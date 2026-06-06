#!/usr/bin/env python3
"""
Slack Fetcher v3 — incremental dump of channel messages to data/raw_messages.json.

Pipeline:
  fetch_slack.py        → data/raw_messages.json   (raw dump: all messages + threads + reactions)
  parse_attendance.py   → data/attendance.json      (classify + merge with seed history)
  build.py              → dist/index.html           (inline JSON into dashboard)

Key design decisions:
  - reactions.get is called for EVERY message that has reactions.
    conversations.history returns reaction names+counts but NOT the users list
    by default (it's omitted to save bandwidth). Without user IDs, +1 reactions
    can't be attributed to individuals. So we always call reactions.get separately.
  - Incremental: only fetches since the last successful run timestamp
    (stored in data/last_fetch.json). First run fetches from 2025-01-01.
  - Thread replies are fetched in full (conversations.replies).
  - Deduplicates by ts so safe to run multiple times.

HOW TO RUN:
  Option A — Claude Code session (no token needed, uses Slack MCP):
    Ask Claude: "Run fetch_slack.py to update raw_messages.json"
    Claude runs this script via its own MCP auth; then runs parse_attendance.py.

  Option B — standalone cron / scheduled task (token required):
    1. Create .env with:  SLACK_BOT_TOKEN=xoxb-your-token-here
       OR export:         export SLACK_BOT_TOKEN=xoxb-...
       OR store:          echo 'xoxb-...' > ~/.slack_token
    2. python3 fetch_slack.py
    3. python3 parse_attendance.py
    4. python3 build.py && git add data/ && git commit -m "data: weekly refresh" && git push

Required OAuth scopes: channels:history  reactions:read
"""

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

CHANNEL_ID = "C043FKMNUNM"
DATA_DIR   = Path(__file__).parent / "data"
RAW_PATH   = DATA_DIR / "raw_messages.json"
META_PATH  = DATA_DIR / "last_fetch.json"
# Fetch from this date on first run (before team started using channel)
HISTORY_START = datetime(2025, 1, 1, tzinfo=timezone.utc).timestamp()


# ── Token resolution ──────────────────────────────────────────────────────────

def get_token() -> str:
    """Resolve Slack bot token from env or file. Precedence: env → .env → ~/.slack_token"""
    # 1. Already exported
    for key in ("SLACK_BOT_TOKEN", "SLACK_TOKEN"):
        t = os.environ.get(key, "").strip()
        if t:
            return t
    # 2. .env file (no python-dotenv required)
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            for key in ("SLACK_BOT_TOKEN=", "SLACK_TOKEN="):
                if line.startswith(key) and not line.startswith("#"):
                    t = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if t:
                        return t
    # 3. ~/.slack_token plain-text file
    home_token = Path.home() / ".slack_token"
    if home_token.exists():
        t = home_token.read_text().strip()
        if t:
            return t
    raise SystemExit(
        "\n❌  No Slack bot token found.\n"
        "    Set environment:  export SLACK_BOT_TOKEN=xoxb-...\n"
        "    Or create .env:   SLACK_BOT_TOKEN=xoxb-...\n"
        "    Or store:         echo 'xoxb-...' > ~/.slack_token\n\n"
        "    Required OAuth scopes: channels:history  reactions:read\n\n"
        "    In Claude Code sessions you may not need a token — Claude's\n"
        "    Slack MCP can fetch messages directly. Ask Claude to run\n"
        "    'fetch_slack.py' and it will handle auth automatically.\n"
    )


# ── API helpers ───────────────────────────────────────────────────────────────

def _api(endpoint: str, params: dict, token: str) -> dict:
    """GET a Slack Web API endpoint with rate-limit retry (3 attempts)."""
    url = f"https://slack.com/api/{endpoint}?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                body = json.loads(r.read())
                if body.get("ok"):
                    return body
                if body.get("error") == "ratelimited":
                    wait = int(r.headers.get("Retry-After", 30))
                    print(f"  ⏳ Rate limited — waiting {wait}s …")
                    time.sleep(wait)
                    continue
                print(f"  ⚠  Slack error [{endpoint}]: {body.get('error')}")
                return body
        except Exception as e:
            print(f"  ⚠  Request error (attempt {attempt+1}): {e}")
            time.sleep(3)
    return {}


def fetch_history(token: str, oldest: float, cursor: str | None = None) -> dict:
    params = {"channel": CHANNEL_ID, "limit": 200, "oldest": str(oldest),
              "inclusive": "false"}
    if cursor:
        params["cursor"] = cursor
    return _api("conversations.history", params, token)


def fetch_replies(token: str, thread_ts: str) -> list:
    """Fetch all thread replies (first message is parent, skip it)."""
    params = {"channel": CHANNEL_ID, "ts": thread_ts, "limit": 100}
    resp = _api("conversations.replies", params, token)
    return resp.get("messages", [])[1:] if resp.get("ok") else []


def fetch_reactions(token: str, ts: str) -> list:
    """
    Fetch full reactions for a message — including user ID lists.

    conversations.history returns reaction NAME + COUNT but NOT the 'users'
    list by default. Without user IDs, +1 reactions can't be attributed to
    individuals. This call is the authoritative source for who reacted.

    Returns: [{"name": "...", "count": N, "users": ["UID1", "UID2", ...]}, ...]
    """
    params = {"channel": CHANNEL_ID, "timestamp": ts, "full": "true"}
    resp = _api("reactions.get", params, token)
    if not resp.get("ok"):
        return []
    msg = resp.get("message", {})
    return [
        {"name": r["name"], "count": r["count"], "users": r.get("users", [])}
        for r in msg.get("reactions", [])
    ]


# ── Record normalisation ──────────────────────────────────────────────────────

def msg_to_record(m: dict, token: str, fetch_rxns: bool = True) -> dict:
    """
    Normalize a Slack message dict to a flat record for raw_messages.json.

    If fetch_rxns=True and the message has reactions, we call reactions.get
    to populate the full 'users' list (not just names+counts from history).
    """
    has_reactions = bool(m.get("reactions"))
    if has_reactions and fetch_rxns:
        reactions = fetch_reactions(token, m["ts"])
        time.sleep(0.2)  # courtesy pause between reactions.get calls
    else:
        # Keep what history gave us (will have name+count but users may be empty)
        reactions = [
            {"name": r["name"], "count": r["count"], "users": r.get("users", [])}
            for r in m.get("reactions", [])
        ]

    return {
        "ts":          m.get("ts", ""),
        "user":        m.get("user", ""),
        "text":        m.get("text", ""),
        "thread_ts":   m.get("thread_ts"),
        "is_reply":    (m.get("thread_ts") is not None
                        and m.get("thread_ts") != m.get("ts")),
        "reply_count": m.get("reply_count", 0),
        "reactions":   reactions,
    }


# ── Main fetch loop ───────────────────────────────────────────────────────────

def main():
    DATA_DIR.mkdir(exist_ok=True)
    token = get_token()

    # Load existing raw dump
    existing: list[dict] = []
    if RAW_PATH.exists():
        try:
            existing = json.loads(RAW_PATH.read_text())
        except json.JSONDecodeError:
            print("⚠  Existing raw_messages.json is corrupt — starting fresh.")

    # Determine start of incremental fetch
    if META_PATH.exists():
        try:
            meta = json.loads(META_PATH.read_text())
            oldest = float(meta.get("last_ts", 0)) + 0.000001
        except Exception:
            oldest = HISTORY_START
    elif existing:
        oldest = max(float(m["ts"]) for m in existing) + 0.000001
    else:
        oldest = HISTORY_START

    start_dt = datetime.fromtimestamp(oldest, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"📥  Fetching #{CHANNEL_ID} since {start_dt}")

    new_records: list[dict] = []
    cursor: str | None = None
    pages = 0
    last_ts = oldest

    while True:
        resp = fetch_history(token, oldest, cursor)
        if not resp.get("ok"):
            print(f"❌  History fetch failed: {resp.get('error', 'unknown')}")
            break

        msgs = resp.get("messages", [])
        for m in msgs:
            rec = msg_to_record(m, token, fetch_rxns=True)
            new_records.append(rec)
            last_ts = max(last_ts, float(m["ts"]))

            # Fetch thread replies
            if m.get("reply_count", 0) > 0:
                replies = fetch_replies(token, m["ts"])
                for r in replies:
                    r_rec = msg_to_record(r, token, fetch_rxns=True)
                    new_records.append(r_rec)
                    last_ts = max(last_ts, float(r["ts"]))
                if replies:
                    print(f"  ↳ {len(replies)} replies for ts={m['ts']}")
                time.sleep(0.3)

        meta_resp = resp.get("response_metadata", {})
        cursor = meta_resp.get("next_cursor")
        pages += 1
        print(f"  page {pages}: {len(msgs)} messages …")
        if not cursor:
            break
        time.sleep(0.5)  # stay well under tier-3 rate limit

    # Deduplicate by ts and merge
    existing_ts = {m["ts"] for m in existing}
    deduped = [r for r in new_records if r["ts"] not in existing_ts]
    all_records = existing + deduped
    # Sort chronologically (oldest first) for human readability
    all_records.sort(key=lambda m: float(m["ts"]))

    if deduped:
        RAW_PATH.write_text(json.dumps(all_records, indent=2))
        META_PATH.write_text(json.dumps({"last_ts": last_ts,
                                         "fetched_at": datetime.now(tz=timezone.utc).isoformat()}))
        print(f"\n✅  Added {len(deduped)} new records (total {len(all_records)}) "
              f"across {pages} page(s)")
        print(f"    Saved → {RAW_PATH}")
        print(f"\n▶   Next: python3 parse_attendance.py && python3 build.py")
    else:
        print("\n✅  No new messages since last fetch.")

    return len(deduped)


if __name__ == "__main__":
    sys.exit(0 if main() >= 0 else 1)

#!/usr/bin/env python3
"""
Slack Fetcher v2 — appends new messages (incl. thread replies) to raw_messages.json.

P0: Thread replies are now fetched for every message with reply_count > 0.
P1: Emoji reactions captured per message (for future analysis; not yet classified).

HOW TO RUN:
  Option A — via Claude Code (no token needed, uses Slack MCP):
    Ask Claude: "Fetch new Slack messages from C043FKMNUNM since [last date]"
    Claude uses its own MCP auth; run parse_attendance.py after.

  Option B — standalone (token required, for cron/scheduled jobs without Claude):
    1. Create .env:  SLACK_TOKEN=xoxb-your-token-here
       OR:          echo 'xoxb-...' > ~/.slack_token
    2. python3 fetch_slack.py
    3. python3 parse_attendance.py

Scopes required for the token: channels:history, groups:history
"""

import json
import os
import time
from datetime import datetime, timezone, date
from pathlib import Path

CHANNEL_ID  = "C043FKMNUNM"
DATA_DIR    = Path(__file__).parent / "data"
RAW_PATH    = DATA_DIR / "raw_messages.json"

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def get_token() -> str:
    """Resolve Slack token from env, .env file, or ~/.slack_token."""
    # 1. Environment variable already exported
    t = os.environ.get("SLACK_TOKEN", "").strip()
    if t:
        return t
    # 2. .env file in project directory
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line.startswith("SLACK_TOKEN=") and not line.startswith("#"):
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
        "\n❌  No Slack token found.\n"
        "    Create .env:  SLACK_TOKEN=xoxb-...\n"
        "    Or export:    export SLACK_TOKEN=xoxb-...\n"
        "    Or store:     echo 'xoxb-...' > ~/.slack_token\n\n"
        "    NOTE: In Claude Code sessions you don't need a token.\n"
        "    Ask Claude to fetch messages directly using its Slack MCP.\n"
    )


def _get(url: str, token: str) -> dict:
    """Simple authenticated GET with rate-limit retry."""
    import urllib.request
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read())
                if data.get("ok"):
                    return data
                if data.get("error") == "ratelimited":
                    wait = int(r.headers.get("Retry-After", 10))
                    print(f"  Rate limited. Waiting {wait}s …")
                    time.sleep(wait)
                    continue
                print(f"  Slack error: {data.get('error')}")
                return data
        except Exception as e:
            print(f"  Request error (attempt {attempt+1}): {e}")
            time.sleep(2)
    return {}


def fetch_history(token: str, oldest: float, cursor: str = None) -> dict:
    import urllib.parse
    params = {"channel": CHANNEL_ID, "limit": 200, "oldest": str(oldest)}
    if cursor:
        params["cursor"] = cursor
    url = "https://slack.com/api/conversations.history?" + urllib.parse.urlencode(params)
    return _get(url, token)


def fetch_replies(token: str, thread_ts: str) -> list:
    """P0: Fetch all replies in a thread."""
    import urllib.parse
    params = {"channel": CHANNEL_ID, "ts": thread_ts, "limit": 100}
    url = "https://slack.com/api/conversations.replies?" + urllib.parse.urlencode(params)
    resp = _get(url, token)
    if not resp.get("ok"):
        return []
    # Skip first message (it's the parent, already in history)
    return resp.get("messages", [])[1:]


def msg_to_record(m: dict) -> dict:
    """Normalize a Slack message to a flat record for raw_messages.json."""
    return {
        "ts":        m.get("ts", ""),
        "user":      m.get("user", ""),
        "text":      m.get("text", ""),
        "thread_ts": m.get("thread_ts"),
        "is_reply":  m.get("thread_ts") != m.get("ts") and m.get("thread_ts") is not None,
        # P1: Capture reactions for future emoji-based status analysis
        "reactions": [
            {"name": r["name"], "count": r["count"], "users": r.get("users", [])}
            for r in m.get("reactions", [])
        ],
        "reply_count": m.get("reply_count", 0),
    }


def main():
    DATA_DIR.mkdir(exist_ok=True)
    token = get_token()

    # Load existing messages; determine oldest seen timestamp
    existing: list = []
    if RAW_PATH.exists():
        existing = json.loads(RAW_PATH.read_text())

    if existing:
        newest_ts = max(float(m["ts"]) for m in existing)
        oldest = newest_ts + 0.000001
    else:
        oldest = datetime(2025, 1, 1, tzinfo=timezone.utc).timestamp()

    print(f"Fetching messages since {datetime.fromtimestamp(oldest).strftime('%Y-%m-%d %H:%M:%S')}")

    new_messages: list = []
    cursor = None
    pages  = 0

    while True:
        resp = fetch_history(token, oldest, cursor)
        if not resp.get("ok"):
            print(f"History fetch failed: {resp.get('error', 'unknown')}")
            break
        msgs = resp.get("messages", [])
        for m in msgs:
            rec = msg_to_record(m)
            new_messages.append(rec)

            # P0: Fetch thread replies for messages with replies
            if m.get("reply_count", 0) > 0:
                replies = fetch_replies(token, m["ts"])
                for r in replies:
                    new_messages.append(msg_to_record(r))
                if replies:
                    print(f"  + {len(replies)} thread replies for {m['ts']}")
                time.sleep(0.3)  # rate-limit courtesy for replies

        meta   = resp.get("response_metadata", {})
        cursor = meta.get("next_cursor")
        pages += 1
        if not cursor:
            break
        time.sleep(0.5)

    if new_messages:
        # Deduplicate by ts (thread replies may appear as both parent and reply)
        seen = {m["ts"] for m in existing}
        deduped = [m for m in new_messages if m["ts"] not in seen]
        all_msgs = existing + deduped
        RAW_PATH.write_text(json.dumps(all_msgs, indent=2))
        print(f"Added {len(deduped)} new records (total {len(all_msgs)}) across {pages} pages")
    else:
        print("No new messages.")


if __name__ == "__main__":
    main()

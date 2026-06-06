#!/usr/bin/env python3
"""
build_raw_messages.py — Build raw_messages.json using Slack Web API directly.

This script uses the Slack bot token to fetch all messages from the channel
and write them to data/raw_messages.json in the format expected by parse_attendance.py.

Run:
  python3 build_raw_messages.py

Requires: SLACK_BOT_TOKEN env var or .env file with SLACK_BOT_TOKEN=xoxb-...
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
DATA_DIR = Path(__file__).parent / "data"
RAW_PATH = DATA_DIR / "raw_messages.json"
HISTORY_START = datetime(2025, 1, 1, tzinfo=timezone.utc).timestamp()

# Bot / system user IDs to skip entirely
SKIP_USERS = {
    "USLACKBOT",
    "U08DY9ATQ4X",  # AsyncMessageReader
    "U093GDFNJ84",  # AskJira
    "U08TFBARPQC",  # FormsCustomerAnalyzer
    "U0B0UCDC72T",  # Team-Reporting
    "U0ACD3LLF5K",  # Intelligent Questions
}


def get_token() -> str:
    for key in ("SLACK_BOT_TOKEN", "SLACK_TOKEN"):
        t = os.environ.get(key, "").strip()
        if t:
            return t
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            for key in ("SLACK_BOT_TOKEN=", "SLACK_TOKEN="):
                if line.startswith(key) and not line.startswith("#"):
                    t = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if t and not t.startswith("xoxb-your"):
                        return t
    home_token = Path.home() / ".slack_token"
    if home_token.exists():
        t = home_token.read_text().strip()
        if t:
            return t
    raise SystemExit(
        "\n❌  No Slack bot token found.\n"
        "    Set environment:  export SLACK_BOT_TOKEN=xoxb-...\n"
        "    Or create .env:   SLACK_BOT_TOKEN=xoxb-...\n"
    )


def api_get(endpoint: str, params: dict, token: str) -> dict:
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
            print(f"  ⚠  Request error (attempt {attempt + 1}): {e}")
            time.sleep(3)
    return {}


def fetch_reactions(token: str, ts: str) -> list:
    params = {"channel": CHANNEL_ID, "timestamp": ts, "full": "true"}
    resp = api_get("reactions.get", params, token)
    if not resp.get("ok"):
        return []
    msg = resp.get("message", {})
    return [
        {"name": r["name"], "count": r["count"], "users": r.get("users", [])}
        for r in msg.get("reactions", [])
    ]


def fetch_replies(token: str, thread_ts: str) -> list:
    params = {"channel": CHANNEL_ID, "ts": thread_ts, "limit": 100}
    resp = api_get("conversations.replies", params, token)
    return resp.get("messages", [])[1:] if resp.get("ok") else []


def msg_to_record(m: dict, token: str) -> dict | None:
    user = m.get("user", m.get("username", ""))
    if user in SKIP_USERS:
        return None
    # Also skip bot_messages with no user or subtype that is a bot join
    subtype = m.get("subtype", "")
    if subtype in ("bot_message", "channel_join") and user in SKIP_USERS:
        return None
    # Skip channel_join messages from bots even if not in SKIP_USERS
    if subtype == "channel_join" and user in SKIP_USERS:
        return None

    has_reactions = bool(m.get("reactions"))
    if has_reactions:
        reactions = fetch_reactions(token, m["ts"])
        time.sleep(0.3)
    else:
        reactions = []

    return {
        "ts": m.get("ts", ""),
        "user": user,
        "text": m.get("text", ""),
        "thread_ts": m.get("thread_ts"),
        "is_reply": (
            m.get("thread_ts") is not None
            and m.get("thread_ts") != m.get("ts")
        ),
        "reply_count": m.get("reply_count", 0),
        "reactions": reactions,
    }


def main():
    DATA_DIR.mkdir(exist_ok=True)
    token = get_token()

    all_records: list[dict] = []
    cursor = None
    pages = 0

    print(f"📥  Fetching #{CHANNEL_ID} since {datetime.fromtimestamp(HISTORY_START, tz=timezone.utc).strftime('%Y-%m-%d')}")

    while True:
        params = {
            "channel": CHANNEL_ID,
            "limit": 200,
            "oldest": str(HISTORY_START),
            "inclusive": "false",
        }
        if cursor:
            params["cursor"] = cursor

        resp = api_get("conversations.history", params, token)
        if not resp.get("ok"):
            print(f"❌  History fetch failed: {resp.get('error', 'unknown')}")
            break

        msgs = resp.get("messages", [])
        pages += 1
        page_count = 0

        for m in msgs:
            user = m.get("user", "")
            if user in SKIP_USERS:
                continue
            # Skip channel_join subtypes for bots
            subtype = m.get("subtype", "")
            if subtype == "channel_join" and user in SKIP_USERS:
                continue

            rec = msg_to_record(m, token)
            if rec:
                all_records.append(rec)
                page_count += 1

            # Fetch thread replies
            if m.get("reply_count", 0) > 0:
                replies = fetch_replies(token, m["ts"])
                for r in replies:
                    r_user = r.get("user", "")
                    if r_user in SKIP_USERS:
                        continue
                    r_rec = msg_to_record(r, token)
                    if r_rec:
                        all_records.append(r_rec)
                if replies:
                    print(f"    ↳ {len(replies)} replies for ts={m['ts']}")
                time.sleep(0.3)

        meta = resp.get("response_metadata", {})
        next_cursor = meta.get("next_cursor", "")
        print(f"  page {pages}: {page_count} records …")

        if not next_cursor:
            break
        cursor = next_cursor
        time.sleep(0.5)

    # Sort chronologically (oldest first)
    all_records.sort(key=lambda m: float(m["ts"]))

    RAW_PATH.write_text(json.dumps(all_records, indent=2, ensure_ascii=False))
    print(f"\n✅  Written {len(all_records)} records to {RAW_PATH}")
    print(f"\n▶   Next: python3 parse_attendance.py && python3 build.py")
    return len(all_records)


if __name__ == "__main__":
    sys.exit(0 if main() >= 0 else 1)

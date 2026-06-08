#!/usr/bin/env python3
"""
refresh_reactions.py — Re-fetch reactions for ALL team-member messages.

WHY THIS EXISTS
───────────────
fetch_slack.py is incremental: it captures reactions at the moment a message
is first fetched. But reactions change — people add or remove +1s days later.
Stale reaction data causes attribution errors (e.g. Utkarsha shows no_info
because her +1 was added after the original fetch).

This script re-fetches reactions.get for every message authored by a team
member (or any message that already has reactions), ensuring raw_messages.json
always reflects the *current* Slack state.

RUN THIS:
  • Weekly alongside fetch_slack.py, OR
  • Any time a team member reports "I was present but showing no_info"

HOW TO RUN (two modes)
──────────────────────
Mode A — via Slack bot token (automated / cron):
    python3 refresh_reactions.py
    Requires:  SLACK_BOT_TOKEN env var  OR  .env  OR  ~/.slack_token

Mode B — via Claude (no token needed, uses Slack MCP):
    Tell Claude: "Run refresh_reactions.py to update all reaction data"
    Claude executes this script through its own Slack MCP auth.

PIPELINE (run in order after this script)
─────────────────────────────────────────
    python3 refresh_reactions.py
    python3 parse_attendance.py
    python3 build.py
    git add data/ dist/ && git commit -m "data: refresh reactions" && git push

WHAT IT DOES
────────────
1. Reads data/raw_messages.json
2. For each message where the author is a known team member, or where the
   message already has any reactions stored, calls reactions.get with full=true
3. Updates the 'reactions' field with the authoritative current list
4. Writes back to data/raw_messages.json (sorted chronologically)

NOTE: Messages from bots or non-team-members with no reactions are skipped
to save API calls (they can't trigger +1 attribution anyway).
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

# Team members whose messages might attract +1 reactions
TEAM_MEMBERS = {
    "W4R4S9FS4",   # Anurag
    "WAM5KDYBZ",   # Khushwant
    "W010NNJV7S8", # Chris
    "U03HRQ036BD", # Ruchita
    "U0900H3NUUT", # Utkarsha
    "U08HVLWG1UM", # Bhumika (former — messages still attract reactions)
}

# Bots to always skip (no reactions worth fetching)
SKIP_USERS = {"USLACKBOT", "U08DY9ATQ4X", "U093GDFNJ84", "U0B0UCDC72T",
              "U0ACD3LLF5K", "U08TFBARPQC"}


# ── Token resolution (same as fetch_slack.py) ────────────────────────────────

def get_token() -> str:
    for key in ("SLACK_BOT_TOKEN", "SLACK_TOKEN"):
        t = os.environ.get(key, "").strip()
        if t:
            return t
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            for key in ("SLACK_BOT_TOKEN=", "SLACK_TOKEN="):
                if line.strip().startswith(key) and not line.strip().startswith("#"):
                    t = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if t:
                        return t
    home_token = Path.home() / ".slack_token"
    if home_token.exists():
        t = home_token.read_text().strip()
        if t:
            return t
    raise SystemExit(
        "\n❌  No Slack bot token found.\n"
        "    Set:  export SLACK_BOT_TOKEN=xoxb-...\n"
        "    Or create .env with:  SLACK_BOT_TOKEN=xoxb-...\n"
        "    Or ask Claude to run this script (uses Slack MCP auth).\n"
    )


def _api(endpoint: str, params: dict, token: str) -> dict:
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
                return body
        except Exception as e:
            print(f"  ⚠  Request error (attempt {attempt+1}): {e}")
            time.sleep(3)
    return {}


def fetch_reactions(token: str, ts: str) -> list:
    """Fetch full reactions including user ID lists for a message."""
    params = {"channel": CHANNEL_ID, "timestamp": ts, "full": "true"}
    resp = _api("reactions.get", params, token)
    if not resp.get("ok"):
        return []
    return [
        {"name": r["name"], "count": r["count"], "users": r.get("users", [])}
        for r in resp.get("message", {}).get("reactions", [])
    ]


def should_refresh(record: dict) -> bool:
    """
    Return True if we should re-fetch reactions for this record.
    Criteria:
      - Author is a known team member (their messages attract +1s), OR
      - The record already has reactions stored (need to keep fresh)
    Skip bots and thread replies from non-team-members with no reactions.
    """
    uid = record.get("user", "")
    if uid in SKIP_USERS:
        return False
    if uid in TEAM_MEMBERS:
        return True                     # always refresh team member posts
    if record.get("reactions"):
        return True                     # refresh anything that already has reactions
    return False


def main():
    if not RAW_PATH.exists():
        print(f"❌  {RAW_PATH} not found. Run fetch_slack.py first.")
        sys.exit(1)

    token = get_token()
    records: list[dict] = json.loads(RAW_PATH.read_text())
    print(f"📂  Loaded {len(records)} records from raw_messages.json")

    to_refresh = [r for r in records if should_refresh(r)]
    print(f"🔄  Will refresh reactions for {len(to_refresh)} messages "
          f"({len(records)-len(to_refresh)} skipped — bots / non-member without reactions)")

    updated = 0
    changed = 0
    errors  = 0

    for i, rec in enumerate(to_refresh, 1):
        ts  = rec["ts"]
        uid = rec.get("user", "?")
        if i % 50 == 0 or i == 1:
            print(f"  [{i}/{len(to_refresh)}] ts={ts} user={uid}")

        new_rxns = fetch_reactions(token, ts)
        old_rxns = rec.get("reactions", [])

        # Compare by name+count+users to detect real changes
        old_key = sorted((r["name"], tuple(sorted(r.get("users",[])))) for r in old_rxns)
        new_key = sorted((r["name"], tuple(sorted(r.get("users",[])))) for r in new_rxns)

        if new_key != old_key:
            rec["reactions"] = new_rxns
            changed += 1
            if old_rxns != new_rxns:
                old_names = [r["name"] for r in old_rxns]
                new_names = [r["name"] for r in new_rxns]
                print(f"    ↻ changed: {old_names} → {new_names}")

        updated += 1
        time.sleep(0.2)  # stay well under rate limit

    # Write back
    records.sort(key=lambda m: float(m["ts"]))
    RAW_PATH.write_text(json.dumps(records, indent=2, ensure_ascii=False))

    print(f"\n✅  Done: {updated} messages checked, {changed} reactions updated")
    print(f"   Errors: {errors}")
    print(f"\n▶   Next:")
    print(f"   python3 parse_attendance.py")
    print(f"   python3 build.py")
    print(f"   git add data/ dist/ && git commit -m 'data: refresh reactions' && git push")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
incremental_fetch.py — helper for the Claude scheduled task pipeline.

Used by the scheduled task agent (not directly by humans) to do
cursor-managed incremental updates to data/raw_messages.json.

Modes:
  python3 incremental_fetch.py --cutoff
      Print the latest message timestamp already in raw_messages.json.
      The scheduled task uses this as the `oldest` param for slack_read_channel.

  python3 incremental_fetch.py --append-file /tmp/new_slack_records.json
      Read JSON records from the given file, deduplicate against raw_messages.json
      by ts, append new ones, sort chronologically, write back.

Record format (matches raw_messages.json schema):
  {
    "ts": "1749702249.268269",
    "user": "W4R4S9FS4",
    "text": "At office",
    "thread_ts": null,
    "is_reply": false,
    "reply_count": 0,
    "reactions": [{"name": "+1moji", "count": 1, "users": ["U03HRQ036BD"]}]
  }
"""

import json
import sys
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
RAW_PATH = DATA_DIR / "raw_messages.json"


def get_cutoff():
    if not RAW_PATH.exists():
        print("0.000000")
        return
    recs = json.loads(RAW_PATH.read_text())
    if not recs:
        print("0.000000")
        return
    latest = max(float(r["ts"]) for r in recs)
    print(f"{latest:.6f}")


def append_file(path: str):
    new_recs = json.loads(Path(path).read_text())
    if not RAW_PATH.exists():
        DATA_DIR.mkdir(exist_ok=True)
        existing = []
    else:
        existing = json.loads(RAW_PATH.read_text())

    existing_ts = {r["ts"] for r in existing}
    added = [r for r in new_recs if r["ts"] not in existing_ts]
    existing.extend(added)
    existing.sort(key=lambda r: float(r["ts"]))
    RAW_PATH.write_text(json.dumps(existing, indent=2, ensure_ascii=False))
    print(f"Added {len(added)} new records (total {len(existing)})")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    if sys.argv[1] == "--cutoff":
        get_cutoff()
    elif sys.argv[1] == "--append-file" and len(sys.argv) == 3:
        append_file(sys.argv[2])
    else:
        print(__doc__)
        sys.exit(1)

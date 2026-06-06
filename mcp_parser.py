#!/usr/bin/env python3
"""
Parse Slack MCP text-format responses into raw_messages.json records.
Usage: python3 mcp_parser.py --append   (reads from PAGE_TEXT list below)
"""
import json, re
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
RAW_PATH = DATA_DIR / "raw_messages.json"

# --- Parse a single MCP page text into list of message dicts ---
def parse_page(text: str) -> list[dict]:
    records = []
    # Split on message headers
    blocks = re.split(r'=== Message from ', text)
    for block in blocks[1:]:
        lines = block.strip().splitlines()
        if not lines:
            continue
        # Header line: "Display Name (USER_ID) at DATETIME IST ==="
        header = lines[0]
        m = re.search(r'\(([A-Z0-9]+)\)', header)
        if not m:
            continue
        user_id = m.group(1)
        # Skip bots
        if user_id in ('USLACKBOT', 'U08DY9ATQ4X'):
            continue

        # Find "Message TS:" line
        ts = None
        text_lines = []
        reaction_raw = None
        reply_count = 0
        thread_ts = None

        for i, line in enumerate(lines[1:], 1):
            if line.startswith('Message TS:'):
                ts = line.split(':', 1)[1].strip()
            elif line.startswith('Reactions:'):
                reaction_raw = line[len('Reactions:'):].strip()
            elif line.startswith('Thread:'):
                m2 = re.search(r'(\d+) repl', line)
                if m2:
                    reply_count = int(m2.group(1))
            elif line.startswith('Files:'):
                pass  # skip
            else:
                # Content lines (skip empty header remainder)
                if i > 1 or (not line.startswith('Message TS')):
                    text_lines.append(line)

        if not ts:
            continue

        # Parse reactions (names+counts only — users filled in later by get_reactions)
        reactions = []
        if reaction_raw:
            for part in reaction_raw.split(','):
                part = part.strip()
                rm = re.match(r'(.+?)\s*\((\d+)\)$', part)
                if rm:
                    reactions.append({
                        "name": rm.group(1).strip(),
                        "count": int(rm.group(2)),
                        "users": []  # filled by slack_get_reactions
                    })

        # Build clean text (skip "Message TS:" and meta lines already captured)
        msg_text = '\n'.join(l for l in text_lines if not l.startswith('Message TS:')).strip()

        records.append({
            "ts": ts,
            "user": user_id,
            "text": msg_text,
            "thread_ts": None,
            "is_reply": False,
            "reply_count": reply_count,
            "reactions": reactions,
            "has_reactions_pending": bool(reactions),  # flag for second pass
        })
    return records


def load_existing() -> dict:
    if RAW_PATH.exists():
        try:
            return {r['ts']: r for r in json.loads(RAW_PATH.read_text())}
        except Exception:
            pass
    return {}


def save(records_by_ts: dict):
    DATA_DIR.mkdir(exist_ok=True)
    sorted_recs = [v for _, v in sorted(records_by_ts.items())]
    RAW_PATH.write_text(json.dumps(sorted_recs, indent=2, ensure_ascii=False))
    print(f"  Saved {len(sorted_recs)} records → {RAW_PATH}")


# Paste each page text here as a string in the list below, then run the script.
PAGE_TEXTS = []  # filled below


if __name__ == '__main__':
    existing = load_existing()
    added = 0
    for page_text in PAGE_TEXTS:
        recs = parse_page(page_text)
        for r in recs:
            if r['ts'] not in existing:
                existing[r['ts']] = r
                added += 1
    print(f"Added {added} new records (total {len(existing)})")
    save(existing)

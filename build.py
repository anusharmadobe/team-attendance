#!/usr/bin/env python3
"""
build.py — Bakes data/attendance.json into dashboard.html → dist/index.html

Replaces the async fetch() call with inline JS data so the dashboard works
on any static host (Azure Static Web Apps, GitHub Pages, SharePoint) without
CORS issues or a separate JSON file.

Run:
  python3 build.py

Output:
  dist/index.html  (single self-contained file, safe to deploy anywhere)
"""

import json
import sys
from pathlib import Path

SRC_HTML  = Path(__file__).parent / "dashboard.html"
DATA_JSON = Path(__file__).parent / "data" / "attendance.json"
DIST_DIR  = Path(__file__).parent / "dist"
OUT_HTML  = DIST_DIR / "index.html"

# ── Exact anchor text to find in dashboard.html ───────────────────────────────
OLD_LOAD = (
    "// ── load ──────────────────────────────────────────────────────────────────\n"
    "async function loadData(){\n"
    "  try{const r=await fetch('data/attendance.json');DATA=await r.json();}\n"
    "  catch(e){DATA={team_members:{},attendance:{},period:{from:TODAY,to:TODAY},generated_at:TODAY};}\n"
    "  init();\n"
    "}"
)


def build():
    if not SRC_HTML.exists():
        print(f"ERROR: {SRC_HTML} not found", file=sys.stderr)
        sys.exit(1)
    if not DATA_JSON.exists():
        print(f"ERROR: {DATA_JSON} not found — run seed_attendance.py first", file=sys.stderr)
        sys.exit(1)

    html = SRC_HTML.read_text(encoding="utf-8")
    data = json.loads(DATA_JSON.read_text(encoding="utf-8"))

    if OLD_LOAD not in html:
        print("ERROR: Could not find loadData() anchor in dashboard.html.\n"
              "The source file may have changed — update OLD_LOAD in build.py.", file=sys.stderr)
        sys.exit(1)

    # Compact JSON (no extra whitespace) to keep file size down
    inline_json = json.dumps(data, separators=(",", ":"), ensure_ascii=False)

    new_load = (
        "// ── load (data inlined by build.py — no fetch needed) ──────────────────────\n"
        f"const __INLINE_DATA__ = {inline_json};\n"
        "function loadData(){\n"
        "  DATA = __INLINE_DATA__;\n"
        "  init();\n"
        "}"
    )

    html = html.replace(OLD_LOAD, new_load)

    DIST_DIR.mkdir(exist_ok=True)
    OUT_HTML.write_text(html, encoding="utf-8")

    days  = len(data.get("attendance", {}))
    kb    = OUT_HTML.stat().st_size // 1024
    print(f"✅  Built → {OUT_HTML}  ({days} days · {kb} KB)")


if __name__ == "__main__":
    build()

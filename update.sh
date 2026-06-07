#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# update.sh — manual one-shot attendance refresh
#
# For scheduled automated runs, use the Claude Scheduled Tasks instead:
#   team-attendance-weekly-refresh   (every Monday 9:30 AM IST)
#   team-attendance-monthly-report   (1st of every month 9:30 AM IST)
#
# Those tasks auto-fetch new Slack messages via MCP, parse, report, and push.
#
# This script only re-parses existing data (no Slack fetch). To do an
# incremental Slack fetch manually, open Claude Code and ask it to run the
# incremental fetch pipeline (see docs/AUTOMATION.md → Manual refresh).
# ─────────────────────────────────────────────────────────────────────────────
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "──────────────────────────────────────────────────────"
echo "  Team Attendance Refresh  $(date '+%Y-%m-%d %H:%M')"
echo "──────────────────────────────────────────────────────"

# Create logs dir
mkdir -p logs

# Re-parse existing raw_messages.json + merge seed data → attendance.json
echo "→ Parsing attendance data (raw_messages.json + seed)..."
python3 parse_attendance.py

# Build the dashboard locally (optional preview)
echo "→ Building dashboard..."
python3 build.py

echo ""
echo "✅  Done. Preview: python3 -m http.server 8899 --directory dist"
echo "    Push:    git add data/attendance.json data/raw_messages.json && git commit -m 'data: manual refresh' && git push origin main"
echo ""

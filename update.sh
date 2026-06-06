#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# update.sh — weekly attendance update script
#
# Run manually:           ./update.sh
# Add to crontab (Mondays 9 AM):
#   crontab -e
#   0 9 * * 1 cd "/Users/anusharm/learn/ClaudeCode/Team attendance" && ./update.sh >> logs/update.log 2>&1
# ─────────────────────────────────────────────────────────────────────────────
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "──────────────────────────────────────────────────────"
echo "  Team Attendance Update  $(date '+%Y-%m-%d %H:%M')"
echo "──────────────────────────────────────────────────────"

# Create logs dir
mkdir -p logs

# Step 1: Fetch new Slack messages
echo "→ Fetching new Slack messages..."
python3 fetch_slack.py

# Step 2: Re-process into attendance.json
echo "→ Processing attendance data..."
python3 parse_attendance.py

echo "✅  Done. Open dashboard.html to view updated data."
echo ""

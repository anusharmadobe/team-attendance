# Team Attendance System

Tracks daily WFH / Office / Sick / PTO / Leave status for the AEM Forms India PM + Content team from Slack channel **#aemforms-india-pm-chl-design** (`C043FKMNUNM`).

## Quick start

```bash
# Open the dashboard (requires a local HTTP server — not file://)
python3 -m http.server 8899
# then open http://localhost:8899/dashboard.html
```

## Weekly update workflow

```bash
# 1. Fetch new Slack messages (needs SLACK_TOKEN env var)
export SLACK_TOKEN=xoxb-your-token-here
python3 fetch_slack.py          # appends to data/raw_messages.json

# 2. Re-process messages → attendance.json
python3 parse_attendance.py     # reads raw_messages.json, writes data/attendance.json

# 3. Refresh dashboard in browser
```

## Files

| File | Purpose |
|------|---------|
| `dashboard.html` | Interactive dashboard (5 views) |
| `data/attendance.json` | Processed attendance records |
| `data/raw_messages.json` | Raw Slack messages (append-only) |
| `seed_attendance.py` | One-time seed from hand-parsed messages |
| `parse_attendance.py` | Reprocesses raw_messages.json → attendance.json |
| `fetch_slack.py` | Fetches new Slack messages and appends to raw_messages.json |

## Dashboard views

| Tab | What it shows |
|-----|--------------|
| **Annual** | KPIs + office% bar per person + status distribution + colour-coded heat calendar |
| **Monthly** | Daily stacked bar + per-person breakdown + full date matrix table |
| **Weekly** | Current week table with prev/next navigation |
| **By Member** | Per-person summary cards (clickable for full history) + period filter |
| **Daily Log** | Full filterable log (member, status, date range) |

## Status codes

| Code | Meaning |
|------|---------|
| `office` | Explicitly said at office |
| `wfh` | Working from home (including WFH while sick) |
| `sick` | Sick leave / unwell and not working |
| `pto` | Planned time off / vacation |
| `leave` | Half-day, personal leave, or other absence |
| `no_info` | No message posted that day (not an assumption of any status) |

## Team members tracked

| Name | Period |
|------|--------|
| Anurag Sharma | Jan 2025 – present |
| Khushwant Singh | Jan 2025 – present |
| Chris J | Jan 2025 – present |
| Ruchita Srivastava | Jan 2025 – present |
| Ajit Sharma | Jan 2025 – Apr 2025 |
| Bhumika Yadav | Apr 2025 – May 2026 |
| Utkarsha Sharma | Jun 2025 – present |
| Tanya Khetrapal | Jul 2025 – present |
| Satyam Jha | Apr 2026 – May 2026 (intern) |

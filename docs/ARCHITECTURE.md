# System Architecture

## Overview

The system is a lightweight, file-based attendance tracker with three layers:

```
┌─────────────────────────────────────────────────────────────────┐
│  DATA INGESTION                                                 │
│  Slack channel messages → classify → attendance.json            │
├─────────────────────────────────────────────────────────────────┤
│  REPORTING                                                      │
│  attendance.json → generate_report.py → formatted Slack message │
├─────────────────────────────────────────────────────────────────┤
│  PRESENTATION                                                   │
│  attendance.json → build.py → dist/index.html → GitHub Pages   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data flow

```
Slack Channel
#aemforms-india-pm-chl-design
        │
        │  (Claude Slack MCP / fetch_slack.py)
        ▼
data/raw_messages.json          ← append-only, raw message objects
        │
        │  parse_attendance.py  (live Slack data path)
        │  OR
        │  seed_attendance.py   (curated EVENTS list — primary path today)
        ▼
data/attendance.json            ← single source of truth for all outputs
        │
        ├──── generate_report.py ──► Slack message (DM or channel post)
        │
        └──── build.py ──────────► dist/index.html ──► GitHub Pages
```

---

## Components

### `seed_attendance.py` *(primary data source)*
A curated Python file containing a hand-reviewed `EVENTS` list — one tuple per attendance record `(date, user_id, status, note)`. This is the authoritative source because:
- Slack message parsing has edge cases (ambiguous messages, emoji-only posts)
- Manual curation catches group messages ("Ruchita and I at office")
- Corrections and overrides are explicit and auditable

The `build()` function in `seed_attendance.py`:
1. Processes EVENTS with priority (`office > wfh > sick > leave > no_info`)
2. Skips weekends and public holidays
3. Fills `no_info` for all active members on all working days with no explicit record
4. Outputs `data/attendance.json`

### `parse_attendance.py` *(live Slack data path)*
Classifies raw Slack messages using regex rules. Used when processing real-time data from `fetch_slack.py`. Handles:
- Multi-person attribution ("Ruchita, Khushwant and I at office")
- Multi-day expansion ("WFH today and tomorrow")
- Personal vs family illness distinction
- Official travel classification

### `fetch_slack.py` *(Slack API client)*
Fetches messages from the Slack channel including thread replies and emoji reactions. Requires a Slack API token when run standalone; uses Claude's Slack MCP when run via scheduled task.

### `generate_report.py` *(Slack report formatter)*
Generates executive-format Slack messages for any time period. Produces:
- Highlights (what's going well)
- Lowlights / Action Needed
- Team Metrics with progress bars
- Individual Office Attendance ranked leaderboard

Supported periods: `last_week`, `week`, `month`, `last_month`, `year`, `last_year`, custom range.

### `build.py` *(static site builder)*
Reads `dashboard.html` + `data/attendance.json` and produces `dist/index.html` with the JSON inlined as a JavaScript constant. This:
- Eliminates CORS issues on static hosts
- Produces a single self-contained file
- Is idempotent — safe to run on every push

### `dashboard.html` *(interactive frontend)*
Single-file HTML/CSS/JS dashboard using Adobe Spectrum 2 design tokens. No build tools, no npm, no dependencies. Tabs:
- **Home** — Executive summary, attendance trend chart, member cards with drill-down
- **Annual** — KPIs, individual + team bar charts, monthly matrix heat-map
- **Monthly** — KPIs, charts, daily table for any month
- **Weekly** — Week-by-week navigation with prev/next, copy-to-clipboard summary
- **Daily Log** — Full filterable log (member × status × date range)

---

## Automation

### Claude Scheduled Tasks (local, runs on this machine)

| Task | Schedule | Actions |
|---|---|---|
| `team-attendance-weekly-refresh` | Mon 9:30 AM IST | seed → 3 Slack reports → git push |
| `team-attendance-monthly-report` | 1st of month 9:30 AM IST | seed → 3 Slack reports → git push |

### GitHub Actions (cloud, triggered by push)

Every `git push origin main` triggers `.github/workflows/deploy.yml`:
1. `python3 build.py` — inlines JSON into HTML → `dist/index.html`
2. `actions/deploy-pages` — deploys `dist/` to GitHub Pages

Total time from push to live: ~2 minutes.

---

## Holiday calendar

Public holidays are defined in `HOLIDAYS` sets in both `seed_attendance.py` and `parse_attendance.py` (kept in sync manually). Sources:
- **2026**: Adobe official Global Holidays PDF (pages 47–49, India / Noida office)
- **2025**: Estimated from 2026 pattern; Independence Day and Gandhi Jayanti confirmed from channel posts

Bangalore-specific holidays (Chris J) are handled as `leave` entries in EVENTS, not removed from the global holiday set, to avoid affecting Noida/Delhi members' working day counts.

---

## Key constraints

| Constraint | Reason |
|---|---|
| No database | Simplicity; JSON file is sufficient for a 5-person team |
| No backend server | Static hosting on GitHub Pages; no auth required |
| Slack as input only | Team already uses Slack; no new tool adoption needed |
| Manual seed approach | Higher accuracy than pure NLP parsing for a small dataset |
| No real-time updates | Weekly batch refresh is sufficient for attendance tracking |

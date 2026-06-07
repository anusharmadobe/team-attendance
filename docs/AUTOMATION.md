# Automation & CI/CD

## Overview

Two types of automation keep everything running — no manual steps required.

| Layer | What | How |
|---|---|---|
| **Local** | Weekly Slack fetch + attendance parse + reports | Claude Scheduled Tasks (runs on your machine) |
| **Cloud** | Dashboard rebuild + deploy to GitHub Pages | GitHub Actions (triggers on every push) |

---

## Local automation — Claude Scheduled Tasks

Both tasks are **fully automated**. They fetch new Slack messages automatically, regenerate attendance data, post reports to Slack, and push to git — no manual input needed.

### Weekly task: `team-attendance-weekly-refresh`

**When:** Every Monday at 9:30 AM IST  
**What it does (in order):**
1. **Fetches new Slack messages** since the last stored timestamp using `slack_read_channel` MCP (incremental — only new messages, with +1moji reaction users populated via `slack_get_reactions`)
2. Appends new records to `data/raw_messages.json` via `incremental_fetch.py`
3. Runs `parse_attendance.py` → merges Slack history + seed data → `data/attendance.json`
4. Generates 3 reports: last week, current month, current year
5. Posts all 3 reports to Slack channel `C08T43UHK9D`
6. Commits `data/attendance.json` + `data/raw_messages.json` and pushes to `main` → triggers live dashboard rebuild

### Monthly task: `team-attendance-monthly-report`

**When:** 1st of every month at 9:30 AM IST  
**What it does:** Identical to the weekly task above — full fetch, parse, report, push.

> **No manual seed updates needed.** The tasks fetch fresh data from Slack automatically every week.

---

## Cloud automation — GitHub Actions

### Workflow: `deploy.yml`

**Trigger:** Every push to `main` branch  
**File:** `.github/workflows/deploy.yml`

**Steps:**
1. Check out the repo
2. Set up Python 3.11
3. Run `python3 build.py` → produces `dist/index.html` (attendance.json inlined)
4. Upload `dist/` as a GitHub Pages artifact
5. Deploy to `https://anusharmadobe.github.io/team-attendance/`

**Time to live:** ~2 minutes from push to updated dashboard

**Required GitHub settings:**
- Repository → Settings → Pages → Source: **GitHub Actions**
- Workflow needs `permissions: pages: write, id-token: write`

---

## Manual refresh (if needed)

```bash
cd "/Users/anusharm/learn/ClaudeCode/Team attendance"

# 1. Get cutoff timestamp and fetch new messages via Claude Code + Slack MCP
#    (run this in a Claude Code session — it uses the Slack MCP directly)
python3 incremental_fetch.py --cutoff
# Then ask Claude to: fetch slack_read_channel C043FKMNUNM oldest=<cutoff> detailed
# and run: python3 incremental_fetch.py --append-file /tmp/new_slack_records.json

# 2. Regenerate attendance
python3 parse_attendance.py

# 3. Build dashboard locally
python3 build.py

# 4. Commit and push
git add data/attendance.json data/raw_messages.json
git commit -m "data: manual refresh $(date +%Y-%m-%d)"
git push origin main
```

### Preview without pushing

```bash
python3 build.py
python3 -m http.server 8899 --directory dist
# Open http://localhost:8899
```

---

## Data pipeline

```
Slack channel #aemforms-india-pm-chl-design
        ↓  (slack_read_channel MCP, incremental)
data/raw_messages.json   ←  incremental_fetch.py --append-file
        ↓
parse_attendance.py  ←  also reads seed_attendance.py via merge_seed()
        ↓
data/attendance.json
        ↓  (git push → GitHub Actions)
dist/index.html  →  https://anusharmadobe.github.io/team-attendance/
```

---

## Authentication

### Git push
Scheduled tasks use `gh auth token --hostname github.com --user anusharmadobe`. If it fails:
```bash
TOKEN=$(gh auth token --hostname github.com --user anusharmadobe)
git remote set-url origin "https://anusharmadobe:$TOKEN@github.com/anusharmadobe/team-attendance.git"
git push origin main
git remote set-url origin "https://github.com/anusharmadobe/team-attendance.git"
```

### Slack
Slack MCP is used directly — no token management needed.

---

## Troubleshooting

| Problem | Check |
|---|---|
| Scheduled task didn't run | Was your machine on and Claude Code running at 9:30 AM IST? |
| Git push failed: auth error | See auth command above |
| GitHub Actions failed | Check Actions tab in the repo; usually a `build.py` import error |
| Dashboard shows stale data | Check if latest commit contains updated `data/attendance.json` |
| Slack message not sent | Verify Slack MCP is connected in Claude Code settings |
| incremental_fetch.py returns 0 records | Check `oldest` param — data may already be current |

---

## Concurrency

GitHub Actions uses `concurrency: group: pages` — overlapping deployments cancel the in-flight job and run the latest. Never two simultaneous deployments.

---

## Adding a new team member

1. Add to `TEAM_MEMBERS` in `parse_attendance.py` and `MEMBER_NAMES` if needed:
   ```python
   "WXXXXXX": {"name": "First Last", "username": "flast", "active_from": "2026-07-01", "active_to": None, "role": "PM"}
   ```
2. Add to `README.md` → Active team members table
3. Run `python3 parse_attendance.py` — they'll have `no_info` from `active_from` onward for any unrecorded days
4. Commit and push

## Removing a team member (departure)

1. Set `active_to` to their last working day in `TEAM_MEMBERS` (do NOT delete — historical data must stay)
2. Run `python3 parse_attendance.py`, commit, and push

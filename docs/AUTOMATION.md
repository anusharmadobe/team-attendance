# Automation & CI/CD

## Overview

Two types of automation are active:

| Layer | What | How |
|---|---|---|
| **Local** | Weekly data refresh + Slack reports | Claude Scheduled Tasks (runs on your machine) |
| **Cloud** | Dashboard rebuild + deploy | GitHub Actions (runs on push) |

---

## Local automation — Claude Scheduled Tasks

### Weekly task: `team-attendance-weekly-refresh`

**When:** Every Monday at 9:30 AM IST (assumes machine is on)  
**What it does:**
1. Runs `seed_attendance.py` to rebuild `attendance.json` from the curated EVENTS list
2. Generates 3 reports: last week, current month, current year
3. Posts all 3 reports to Slack channel `C08T43UHK9D`
4. Commits `data/attendance.json` and pushes to `main` — triggering a live dashboard rebuild

**Skill file:** `~/.claude/scheduled-tasks/team-attendance-weekly-refresh/SKILL.md`

### Monthly task: `team-attendance-monthly-report`

**When:** 1st of every month at 9:30 AM IST  
**What it does:** Same as weekly task — runs seed, generates 3 reports, posts to Slack, pushes to git

**Skill file:** `~/.claude/scheduled-tasks/team-attendance-monthly-report/SKILL.md`

> **Note:** Before this runs, you must have updated `seed_attendance.py` with the latest attendance data for the period. The scheduled task re-runs the seed script but does not fetch live Slack data automatically — it works from what's in EVENTS.

---

## Cloud automation — GitHub Actions

### Workflow: `deploy.yml`

**Trigger:** Every push to `main` branch  
**File:** `.github/workflows/deploy.yml`

**Steps:**
1. Check out the repo
2. Set up Python 3.11
3. Run `python3 build.py` → produces `dist/index.html` (JSON inlined)
4. Upload `dist/` as a GitHub Pages artifact
5. Deploy artifact to `https://anusharmadobe.github.io/team-attendance/`

**Time to live:** ~2 minutes from push to updated dashboard

**Required GitHub settings:**
- Repository → Settings → Pages → Source: **GitHub Actions**
- Workflow needs `permissions: pages: write, id-token: write`

---

## Manual triggers

### Refresh data and reports right now

```bash
cd "/Users/anusharm/learn/ClaudeCode/Team attendance"

# 1. Update attendance data
python3 seed_attendance.py

# 2. Generate reports (optional — just prints to stdout)
python3 generate_report.py last_week
python3 generate_report.py month
python3 generate_report.py year

# 3. Build the dashboard
python3 build.py

# 4. Commit and deploy
git add data/attendance.json
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

## Authentication

### Git push
The scheduled task uses `gh auth token --hostname github.com --user anusharmadobe` to embed an auth token in the remote URL temporarily, then resets the remote to the clean HTTPS URL. If this fails:

```bash
gh auth login        # authenticate with GitHub
gh auth setup-git    # configure git credential helper
```

### Slack
The Slack MCP is used directly by the scheduled task. No token management needed — it uses your existing Claude Code Slack integration.

---

## Troubleshooting

| Problem | Check |
|---|---|
| Scheduled task didn't run | Was your machine on and Claude Code running at 9:30 AM IST? |
| Git push failed: auth error | Run `gh auth setup-git` then retry manually |
| GitHub Actions failed | Check Actions tab in the repo; usually a `build.py` import error |
| Dashboard shows stale data | Check if latest commit contains updated `data/attendance.json` |
| Slack message not sent | Verify Slack MCP is connected in Claude Code settings |
| Wrong date range in report | Check the `last_week` date math — `today.weekday() + 3` gives days back to last Friday |

---

## Concurrency

GitHub Actions uses `concurrency: group: pages` so overlapping deployments (e.g. rapid pushes) cancel the in-flight job and run the latest. There will never be two simultaneous deployments.

---

## Adding a new team member

1. Add them to the `MEMBERS` dict in `seed_attendance.py` and `parse_attendance.py`:
   ```python
   "WXXXXXX": {
       "name": "First Last",
       "username": "flast",
       "active_from": "2026-07-01",
       "active_to": None,
       "role": "PM"
   }
   ```
2. Add them to `README.md` → Active team members table
3. Re-run `seed_attendance.py` — their days prior to `active_from` won't appear; from `active_from` onward they get `no_info` for any day not explicitly listed in EVENTS
4. Add historical EVENTS entries if you have Slack data for their past days
5. Commit and push

## Removing a team member (departure)

1. Set `active_to` to their last working day in `MEMBERS` (do NOT delete the entry — historical data must stay)
2. The dashboard will stop showing them in new periods; historical periods still show them correctly
3. Re-run `seed_attendance.py`, commit, and push

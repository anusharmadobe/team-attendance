# Adding Attendance Data

## Two-track data strategy

The system combines two sources. `parse_attendance.py` is always the command that produces `attendance.json` — it reads both sources and merges them automatically (higher priority status wins).

| Track | File | Role |
|---|---|---|
| **Slack history** | `data/raw_messages.json` | Full channel history Jan 2025–present, fetched via Slack MCP. Re-run `populate_raw.py` for a full backfill. |
| **Manual seed** | `seed_attendance.py` EVENTS | Your weekly additions. `parse_attendance.py` merges this automatically via `merge_seed()`. |

**Normal weekly flow:** Add entries to `seed_attendance.py` → run `parse_attendance.py` → done. No need to run `seed_attendance.py` directly.

**Periodic backfill** (every few months, or when a new member joins): Run `populate_raw.py` to re-fetch the full Slack channel history via MCP, then `parse_attendance.py`.

---

## Weekly workflow — adding new data

Every week, add recent Slack posts to `seed_attendance.py` EVENTS. The scheduled task (every Monday 9:30 AM IST) will pick them up automatically.

---

## Step 1 — Read the Slack channel (weekly)

Open **#aemforms-india-pm-chl-design** on Slack and scroll back to the dates you need to add.

For each working day, note what each person posted. You're looking for:

| Signal | Classify as |
|---|---|
| "At office", "WF-Sec25A", "N132", at customer site | `office` |
| "WFH today", "working remotely", "joining from home" | `wfh` |
| "Sick", "not feeling well, taking leave", "under the weather" | `sick` |
| "On leave", "PTO", "day off", "OOO" | `leave` |
| No message | `no_info` (filled automatically) |

---

## Step 2 — Add entries to `EVENTS` in `seed_attendance.py`

Open `seed_attendance.py` and find the `EVENTS` list. Append your new records at the bottom in chronological order.

### Format

```python
("YYYY-MM-DD", "SLACK_USER_ID", "status", "brief note"),
```

### Example — adding a whole week

```python
# --- 2026-06-01 (Mon) ---
("2026-06-01", "W4R4S9FS4",   "office", "At office"),
("2026-06-01", "WAM5KDYBZ",   "wfh",    "WFH today"),
("2026-06-01", "W010NNJV7S8", "leave",  "OOO"),
# Ruchita and Utkarsha had no post — no_info filled automatically

# --- 2026-06-02 (Tue) ---
("2026-06-02", "W4R4S9FS4",   "office", "Office"),
("2026-06-02", "WAM5KDYBZ",   "office", "In office"),
("2026-06-02", "W010NNJV7S8", "wfh",    "WFH"),
("2026-06-02", "U03HRQ036BD", "office", "At office"),
("2026-06-02", "U0900H3NUUT", "wfh",    "WFH today"),
# ... and so on for Wed, Thu, Fri
```

### Slack User IDs

| Name | Slack ID |
|---|---|
| Anurag Sharma | `W4R4S9FS4` |
| Khushwant Singh | `WAM5KDYBZ` |
| Chris J | `W010NNJV7S8` |
| Ruchita Srivastava | `U03HRQ036BD` |
| Utkarsha Sharma | `U0900H3NUUT` |

---

## Step 3 — Handle edge cases

### Group message ("Ruchita and I at office")
Add an `office` entry for the sender AND for Ruchita:
```python
("2026-06-03", "W4R4S9FS4",   "office", "At office"),
("2026-06-03", "U03HRQ036BD", "office", "With Anurag at office"),
```

### Multi-day message ("WFH today and tomorrow")
Add entries for both days:
```python
("2026-06-03", "WAM5KDYBZ", "wfh", "WFH"),
("2026-06-04", "WAM5KDYBZ", "wfh", "WFH (carried from prev day)"),
```

### Official travel (customer site, other Adobe building)
Classify as `office`:
```python
("2026-06-04", "W010NNJV7S8", "office", "At customer site (Bangalore)"),
```

### Contradictory posts in same day (e.g. "WFH" in morning, "heading to office" later)
Add only the higher-priority status:
```python
("2026-06-05", "W4R4S9FS4", "office", "Initially WFH, came to office"),
# Do NOT add a wfh entry — office wins (priority 5 > 4)
```

### Public holiday
Do **not** add any entries for that date. The seed script skips public holidays automatically using the `HOLIDAYS` set. The date won't appear in `attendance.json` at all.

---

## Step 4 — Regenerate attendance.json

```bash
cd "/Users/anusharm/learn/ClaudeCode/Team attendance"
python3 parse_attendance.py
```

Expected output (numbers grow over time):
```
Loaded 816 messages from raw_messages.json
Merged seed data: XX additional records resolved
Written 354 days, 1638 records → data/attendance.json
```

`parse_attendance.py` reads `data/raw_messages.json` (full Slack history) **and** automatically merges your new `seed_attendance.py` entries — you do not need to run `seed_attendance.py` directly.

---

## Step 5 — Verify in the dashboard

```bash
python3 build.py
python3 -m http.server 8899 --directory dist
# Open http://localhost:8899
```

Check the **Daily Log** tab — your new entries should appear for the dates you added.

---

## Step 6 — Commit and push

```bash
git add data/attendance.json seed_attendance.py
git commit -m "data: add attendance for week of YYYY-MM-DD"
git push origin main
```

> **Auth note:** If push fails, use:
> `TOKEN=$(gh auth token --hostname github.com --user anusharmadobe) && git remote set-url origin "https://anusharmadobe:$TOKEN@github.com/anusharmadobe/team-attendance.git" && git push origin main`

GitHub Actions will rebuild and redeploy the live dashboard within ~2 minutes.

---

## Tips

- Always add entries in **date order** — it keeps EVENTS readable.
- The seed script deduplicates by priority, so duplicate entries (e.g. from multiple Slack messages) are safe — the higher-priority one wins.
- If you're unsure whether a message counts as `office` vs `wfh`, default to `wfh` unless it explicitly mentions being at a physical office or travel.
- `no_info` entries do NOT need to be added manually — the script fills them for every active member on every working day with no explicit record.

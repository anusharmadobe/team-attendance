#!/usr/bin/env python3
"""
Team Attendance Parser — v2
Processes raw Slack messages into daily attendance records.
Run weekly after fetch_slack.py to update data/attendance.json.

Improvements in v2:
  P0: Multi-person attribution, official travel = office, correction priority
  P1: Multi-day expansion, Indian holidays, context-sensitive stepping-out
  P2: Reporting rate confidence, location-aware holidays, future dates
"""

import json
import re
from datetime import date, timedelta
from pathlib import Path

# ── Active team roster ────────────────────────────────────────────────────────
TEAM_MEMBERS = {
    "W4R4S9FS4":  {"name": "Anurag Sharma",     "username": "anusharm",  "active_from": "2025-01-01", "active_to": None,         "role": "Manager"},
    "WAM5KDYBZ":  {"name": "Khushwant Singh",   "username": "khsingh",   "active_from": "2025-01-01", "active_to": None,         "role": "Senior PM"},
    "W010NNJV7S8":{"name": "Chris J",           "username": "macman",    "active_from": "2025-01-01", "active_to": None,         "role": "PM"},
    "U03HRQ036BD":{"name": "Ruchita Srivastava","username": "ruchitas",  "active_from": "2025-01-01", "active_to": None,         "role": "Technical Writer"},
    "U0900H3NUUT":{"name": "Utkarsha Sharma",   "username": "utkarshas", "active_from": "2025-06-16", "active_to": None,         "role": "Designer"},
    # Former members — kept so their messages are classified and +1 reactions
    # to their posts correctly attribute to current team members.
    "U08HVLWG1UM":{"name": "Bhumika Yadav",     "username": "bhumikay",  "active_from": "2025-04-01", "active_to": "2026-05-31", "role": "PM"},
    # Removed (no messages / observer only): Ajit Sharma (left Apr 2025),
    #   Ashish Alex (left Jul 2025), Tanya Khetrapal (observer, 0 records),
    #   Satyam Jha (intern, left May 2026)
}

# ── Name → member ID for multi-person attribution ─────────────────────────────
# e.g. "Ruchita, Khushwant and I at office" → attribute office to all three
MEMBER_NAMES = {
    "anurag":    "W4R4S9FS4",
    "khushwant": "WAM5KDYBZ",
    "chris":     "W010NNJV7S8",
    "ruchita":   "U03HRQ036BD",
    "utkarsha":  "U0900H3NUUT",
}

SKIP_USERS = {"USLACKBOT", "U08DY9ATQ4X", "U093GDFNJ84", "U0B0UCDC72T",
              "U0ACD3LLF5K", "U08TFBARPQC"}  # bots / integrations

# ── Confirmed Indian public holidays → maps date to holiday name ─────────────
# 2025: national holidays confirmed; Adobe Wellbeing Days estimated from 2026 pattern.
# 2026: from official Adobe Global Holidays PDF (pages 47–49).
# Bangalore-specific holidays (e.g. Chris) are seeded individually; not here.
# Republic Day 2025 (Jan 26) falls on a Sunday → already a weekend, not listed.
HOLIDAYS: dict[str, str] = {
    # ── 2025 ──────────────────────────────────────────────────────────────────
    "2025-01-01": "New Year's Day",
    "2025-03-14": "Holi",
    "2025-03-21": "Adobe Wellbeing Day",
    "2025-04-14": "Dr. Ambedkar Jayanti",
    "2025-04-18": "Good Friday",
    "2025-05-01": "Labour Day",
    "2025-06-27": "Adobe Wellbeing Day",
    "2025-08-15": "Independence Day",
    "2025-08-22": "Adobe Wellbeing Day",
    "2025-08-27": "Ganesh Chaturthi",
    "2025-10-02": "Gandhi Jayanti",
    "2025-10-20": "Diwali",
    "2025-10-31": "Adobe Wellbeing Day",
    "2025-11-05": "Guru Nanak Jayanti",
    "2025-12-24": "Winter Shutdown",
    "2025-12-25": "Winter Shutdown",
    "2025-12-26": "Winter Shutdown",
    "2025-12-29": "Winter Shutdown",
    "2025-12-30": "Winter Shutdown",
    "2025-12-31": "Winter Shutdown",
    # ── 2026 — from official Adobe Global Holidays PDF ──────────────────────
    "2026-01-01": "New Year's Day",
    "2026-01-26": "Republic Day",
    "2026-03-04": "Holi",
    "2026-03-20": "Adobe Wellbeing Day",
    "2026-04-03": "Good Friday",
    "2026-05-01": "Labour Day",
    "2026-05-27": "Eid al-Adha",
    "2026-06-29": "Adobe Wellbeing Day",
    "2026-08-21": "Adobe Wellbeing Day",
    "2026-09-14": "Ganesh Chaturthi",
    "2026-10-02": "Gandhi Jayanti",
    "2026-10-20": "Dussehra",
    "2026-10-30": "Adobe Wellbeing Day",
    "2026-11-09": "Diwali",
    "2026-11-24": "Guru Nanak Jayanti",
    "2026-12-24": "Winter Shutdown",
    "2026-12-25": "Winter Shutdown",
    "2026-12-28": "Winter Shutdown",
    "2026-12-29": "Winter Shutdown",
    "2026-12-30": "Winter Shutdown",
    "2026-12-31": "Winter Shutdown",
}

# ── Status correction priority ─────────────────────────────────────────────────
# If multiple messages exist for same person/day, higher priority wins.
# e.g. "WFH at 9am" then "At office at 2pm" → office wins.
STATUS_PRIORITY = {"office": 5, "wfh": 4, "sick": 3, "leave": 2, "holiday": 1, "no_info": 0}

# ── Emoji reactions treated as "me too, same status" ──────────────────────────
# When a team member reacts with one of these to a classified message,
# they are recorded with the same status as the message sender.
# Applies to office and wfh only — sick/leave reactions are too ambiguous.
PLUS_ONE_EMOJIS = {"+1moji", "+1_sign", "plus_one", "thumbsup", "+1"}
PLUS_ONE_STATUSES = {"office", "wfh"}

# ── Illness keywords ───────────────────────────────────────────────────────────
# Match PERSONAL illness (not family member illness, which stays WFH).
ILLNESS_KW = re.compile(
    r"(?:not feeling well|feeling unwell|feel(?:ing)? sick|body ache|"
    r"fever|viral|stomach (?:ache|infection)|migraine|throat infection|"
    r"cough\b|cervical pain|headache|suffering from|under the weather)",
    re.I,
)

# Family illness keywords — these keep status as WFH (not sick)
FAMILY_ILLNESS_KW = re.compile(
    r"(?:wife|daughter|son|kid|child|baby|mother|father|parent).*(?:not well|ill|sick|fever|hospital)",
    re.I,
)

# ── Classification rules ──────────────────────────────────────────────────────
# Checked in order; first match wins (after illness upgrades applied).
RULES = [
    # ── Sick leave: personal illness causing a full day off ───────────────────
    ("sick", [
        r"sick leave",
        r"on sick leave",
        r"taking sick leave",
        r"taking.*day off.*sick",
        r"sick.*taking.*off",
    ]),
    # ── Leave / PTO ───────────────────────────────────────────────────────────
    ("leave", [
        r"\bpto\b(?!.*(?:at office|in office|wfh|work from home))",
        r"\bon leave\b",
        r"taking leave",
        r"taking.*day off",
        r"day off\b",
        r"will be on leave",
        r"\bleave today\b",
        r"\bleave for today\b",
    ]),
    # ── WFH ───────────────────────────────────────────────────────────────────
    ("wfh", [
        r"\bwfh\b",
        r"work(?:ing)? from home",
        r"working remotely",
        r"attend(?:ing)? (?:\w+ )?meetings? from home",
        r"logging(?: in)? from home",
        r"connect(?:ing)? from home",
        r"available from home",
        r"online from home",
        r"wf-home",
    ]),
    # ── Office (explicit + official travel + leaving-office context) ──────────
    ("office", [
        # Standard "at office" variants
        r"\bwfo\b",             # WFO = working from office
        r"at (?:the )?office",
        r"in (?:the )?office",
        r"working from office",
        r"working at office",
        # Official travel / other Adobe buildings (P0: official travel = office)
        r"at sec-?25",          # Adobe Sec-25A Noida
        r"at n-?132",           # Adobe N132 Noida
        r"wf-sec",              # "WF-Sec25A" shorthand
        r"at hdfc",             # customer site
        r"at maruti",           # customer site
        r"workshop at",         # attending any workshop
        r"offsite\b",           # official offsite
        r"customer site",
        r"client site",
        # "Coming to office" / "heading to office" variants
        r"coming to office",
        r"heading (?:to|into) (?:the )?office",
        r"going (?:to|into) (?:the )?office",
        r"will (?:be )?(?:reach|arrive|be) (?:at )?office",
        r"reaching office",
        r"reach (?:the )?office",
        # "Leaving for home" implies was at office (P1: context-sensitive)
        r"leaving (?:the )?office",      # unambiguous: was in office
        r"leaving for home",             # implies left an office/work location
        r"heading home from",            # implies was somewhere (likely office)
    ]),
    # ── Leave (second pass — half-day signals) ────────────────────────────────
    ("leave", [
        r"\bon leave\b",
        r"(?:first|second|1st|2nd) half.*(?:leave|off)",
        r"(?:leave|off).*(?:first|second|1st|2nd) half",
        r"filing.*leave",
        r"filling.*leave",
    ]),
]


def classify(text: str):
    """
    Returns (status, extra_days) where:
      status     = 'office'|'wfh'|'sick'|'leave'|None
      extra_days = number of additional consecutive days with same status (0 = just today)
    """
    tl = text.lower()
    personal_ill = bool(ILLNESS_KW.search(text))
    family_ill   = bool(FAMILY_ILLNESS_KW.search(text))

    # Check multi-day expansion patterns (P1)
    extra = _count_extra_days(tl)

    for status, patterns in RULES:
        for pat in patterns:
            if re.search(pat, tl):
                # ── Illness upgrades ──────────────────────────────────────
                if status == "wfh" and personal_ill and not family_ill:
                    # Personal illness + WFH = still WFH (they're working)
                    return ("wfh", extra)
                if status in ("leave", "pto") and personal_ill and not family_ill:
                    # Leave specifically because person is ill = sick
                    return ("sick", extra)
                return (status, extra)

    # Illness mentioned without explicit status → sick if taking day off
    if personal_ill and not family_ill:
        if re.search(r"tak(?:e|ing) (?:the )?(?:day|leave|rest|first half)", tl):
            return ("sick", extra)

    return (None, 0)


def _count_extra_days(tl: str) -> int:
    """Detect multi-day announcements and return how many extra days to fill."""
    if re.search(r"today and tomorrow", tl):
        return 1
    if re.search(r"(?:for )?(?:rest of|remaining) (?:the )?week", tl):
        # Fill to end of current work week (up to 4 more days)
        return 4  # will be clamped to same-week days in process()
    if re.search(r"this week", tl) and not re.search(r"last|next|past", tl):
        return 4
    if re.search(r"today and (?:the )?next (?:two|2) days", tl):
        return 2
    return 0


def _next_working_days(d: date, n: int):
    """Yield up to n working days after d (same week only for 'rest of week')."""
    cur = d + timedelta(days=1)
    count = 0
    week_cutoff = d + timedelta(days=(4 - d.weekday()))  # Friday
    while count < n and cur <= week_cutoff:
        if cur.weekday() < 5 and cur.isoformat() not in HOLIDAYS:
            yield cur
            count += 1
        cur += timedelta(days=1)


def _mentioned_members(text: str, sender_id: str) -> list:
    """
    P0: Extract other team members mentioned in a group message.
    e.g. "Ruchita, Khushwant and I at office" → [ruchita_id, khushwant_id]
    The sender is already captured separately, so we return only OTHERS.
    """
    tl = text.lower()
    mentioned = []
    for name, uid in MEMBER_NAMES.items():
        if uid == sender_id:
            continue  # skip sender
        # Match first name with word boundary
        if re.search(rf"\b{re.escape(name)}\b", tl):
            mentioned.append(uid)
    return mentioned


def ts_to_date(ts: str) -> date:
    from datetime import datetime, timezone
    return datetime.fromtimestamp(float(ts), tz=timezone.utc).date()


def is_member_active(member_id: str, d: date) -> bool:
    m = TEAM_MEMBERS.get(member_id, {})
    af = date.fromisoformat(m["active_from"])
    at = date.fromisoformat(m["active_to"]) if m.get("active_to") else date(2099, 12, 31)
    return af <= d <= at


def working_days(start: date, end: date):
    cur = start
    while cur <= end:
        if cur.weekday() < 5 and cur.isoformat() not in HOLIDAYS:
            yield cur
        cur += timedelta(days=1)


def _apply_status(attendance, ds, uid, status, note):
    """Apply status with correction priority — higher priority wins."""
    attendance.setdefault(ds, {})
    existing_pri = STATUS_PRIORITY.get(attendance[ds].get(uid, {}).get("status", ""), 0)
    new_pri      = STATUS_PRIORITY.get(status, 0)
    if new_pri > existing_pri:
        attendance[ds][uid] = {"status": status, "note": note[:180].strip()}


# ── Main processing ───────────────────────────────────────────────────────────

def process(messages: list, start: date, end: date) -> tuple:
    """
    Returns (attendance_dict, unclassified_list).

    unclassified_list contains records for team-member messages that had text
    but no classification matched — these may need manual review / seed entry.
    Thread replies are excluded (they're rarely status posts).
    """
    attendance: dict[str, dict] = {}
    unclassified: list = []

    for msg in messages:
        uid = msg.get("user", "")
        if uid in SKIP_USERS or uid not in TEAM_MEMBERS:
            continue
        ts = msg.get("ts", "")
        if not ts:
            continue
        d = ts_to_date(ts)
        if not (start <= d <= end):
            continue
        text = msg.get("text", "").strip()
        if not text:
            continue

        result = classify(text)
        if not result[0]:
            # Track unclassified messages (top-level posts only, min 5 chars)
            if not msg.get("is_reply", False) and len(text) >= 5:
                unclassified.append({
                    "date": d.isoformat(),
                    "user_id": uid,
                    "name": TEAM_MEMBERS[uid]["name"],
                    "text": text[:300],
                    "ts": ts,
                })
            continue
        status, extra_days = result

        # P0: Apply to sender
        _apply_status(attendance, d.isoformat(), uid, status, text)

        # P1: Multi-day expansion — fill extra consecutive working days same week
        if extra_days > 0:
            for xd in _next_working_days(d, extra_days):
                if start <= xd <= end:
                    _apply_status(attendance, xd.isoformat(), uid, status,
                                  f"[multi-day] {text[:120]}")

        # P0: Multi-person attribution — attribute to other named team members
        if status == "office":
            for other_uid in _mentioned_members(text, uid):
                if is_member_active(other_uid, d):
                    _apply_status(attendance, d.isoformat(), other_uid, "office",
                                  f"[group mention] {text[:120]}")

        # P0: +1 reactions — "me too, same status" for office and wfh messages
        # e.g. Utkarsha posts "at office", Chris +1s → Chris also marked office
        if status in PLUS_ONE_STATUSES:
            sender_name = TEAM_MEMBERS.get(uid, {}).get("name", uid)
            for reaction in msg.get("reactions", []):
                if reaction.get("name") in PLUS_ONE_EMOJIS:
                    for reactor_uid in reaction.get("users", []):
                        if reactor_uid in TEAM_MEMBERS and reactor_uid != uid:
                            if is_member_active(reactor_uid, d):
                                _apply_status(
                                    attendance, d.isoformat(), reactor_uid, status,
                                    f"[+1 to {sender_name}] {text[:120]}"
                                )

    # Fill holiday / no_info for all active members on all weekdays with no record.
    # Holidays get their proper name in the note; working days get no_info.
    cur = start
    while cur <= end:
        if cur.weekday() < 5:  # Monday–Friday only
            ds = cur.isoformat()
            attendance.setdefault(ds, {})
            holiday_name = HOLIDAYS.get(ds)  # None if not a holiday
            for mid in TEAM_MEMBERS:
                if is_member_active(mid, cur) and mid not in attendance[ds]:
                    if holiday_name:
                        attendance[ds][mid] = {"status": "holiday", "note": holiday_name}
                    else:
                        attendance[ds][mid] = {"status": "no_info", "note": None}
        cur += timedelta(days=1)

    return dict(sorted(attendance.items())), unclassified


def merge_seed(att_parsed: dict, seed_path: Path) -> dict:
    """
    Merge seed_attendance.py output into the parsed attendance dict.

    Strategy:
      - seed_attendance.py is the authoritative source for historical data
        (Jan 2025 → the date when live fetch_slack.py pipeline went active).
      - parse_attendance.py is authoritative for recent live data from Slack.
      - For days where BOTH have a record, STATUS_PRIORITY decides — the
        higher-priority status wins (office > wfh > sick > leave > no_info).
      - This means a manually curated seed entry always beats a no_info,
        and a Slack-parsed "office" beats a seeded "wfh" if someone corrected
        via Slack after the seed was written.

    Seed is only re-read if seed_attendance.py exists alongside this file.
    If absent, parsed data is used as-is.
    """
    if not seed_path.exists():
        return att_parsed

    import importlib.util
    spec = importlib.util.spec_from_file_location("seed_attendance", seed_path)
    seed_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(seed_mod)
    att_seed = seed_mod.build()  # returns {date_str: {uid: {status, note}}}

    # Merge: for each day/member in seed, apply to parsed dict with priority
    merged = {k: dict(v) for k, v in att_parsed.items()}
    for ds, day in att_seed.items():
        merged.setdefault(ds, {})
        for uid, rec in day.items():
            existing_pri = STATUS_PRIORITY.get(
                merged[ds].get(uid, {}).get("status", ""), 0)
            new_pri = STATUS_PRIORITY.get(rec.get("status", ""), 0)
            if new_pri > existing_pri:
                merged[ds][uid] = rec

    return dict(sorted(merged.items()))


def run():
    data_dir  = Path(__file__).parent / "data"
    raw_path  = data_dir / "raw_messages.json"
    seed_path = Path(__file__).parent / "seed_attendance.py"
    out_path  = data_dir / "attendance.json"

    if not raw_path.exists():
        print(f"ERROR: {raw_path} not found.\n"
              f"  Run fetch_slack.py first, or use seed_attendance.py for\n"
              f"  fully manual data entry.")
        return

    messages = json.loads(raw_path.read_text())
    print(f"Loaded {len(messages)} messages from raw_messages.json")

    start = date(2025, 1, 1)
    end   = date.today()

    att, unclassified = process(messages, start, end)

    # Merge seed data — seed fills historical gaps; parse data wins for recent
    if seed_path.exists():
        before = sum(
            1 for day in att.values()
            for rec in day.values() if rec["status"] != "no_info"
        )
        att = merge_seed(att, seed_path)
        after = sum(
            1 for day in att.values()
            for rec in day.values() if rec["status"] != "no_info"
        )
        print(f"Merged seed data: {after - before} additional records resolved")

    output = {
        "generated_at": end.isoformat(),
        "period": {"from": start.isoformat(), "to": end.isoformat()},
        "team_members": TEAM_MEMBERS,
        "holidays": HOLIDAYS,  # date → holiday name; used by dashboard today-strip
        "attendance": att,
    }

    out_path.write_text(json.dumps(output, indent=2, default=str))
    days = len(att)
    records = sum(len(v) for v in att.values())
    print(f"Written {days} days, {records} records → {out_path}")

    # Write unclassified.json — messages from team members the parser couldn't classify
    unclassified_path = data_dir / "unclassified.json"
    unclassified_path.write_text(json.dumps(unclassified, indent=2, ensure_ascii=False))
    cutoff_14d = (end - timedelta(days=14)).isoformat()
    recent_unclassified = [u for u in unclassified if u["date"] >= cutoff_14d]
    if recent_unclassified:
        print(f"⚠️  {len(recent_unclassified)} unclassified message(s) in last 14 days "
              f"({len(unclassified)} total) — see data/unclassified.json")
    elif unclassified:
        print(f"ℹ️  {len(unclassified)} historical unclassified messages (none in last 14 days)")
    else:
        print("✅  No unclassified messages")


if __name__ == "__main__":
    run()

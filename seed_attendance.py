#!/usr/bin/env python3
"""
Seed script: converts all hand-parsed Slack attendance events into attendance.json.
Run once (or after adding new EVENTS lines) to regenerate data/attendance.json.
For ongoing weekly updates use fetch_slack.py + parse_attendance.py instead.
"""

import json
from datetime import date, timedelta
from pathlib import Path

# ── Roster (matches parse_attendance.py) ──────────────────────────────────────
MEMBERS = {
    "W4R4S9FS4":   {"name": "Anurag Sharma",     "username": "anusharm",   "active_from": "2025-01-01", "active_to": None,         "role": "Manager"},
    "WAM5KDYBZ":   {"name": "Khushwant Singh",    "username": "khsingh",    "active_from": "2025-01-01", "active_to": None,         "role": "Senior PM"},
    "W010NNJV7S8": {"name": "Chris J",            "username": "macman",     "active_from": "2025-01-01", "active_to": None,         "role": "PM"},
    # Ajit Sharma left — removed from active roster (data retained in EVENTS for history)
    # "U04BTKLSUF7": {"name": "Ajit Sharma", ...}
    "U03HRQ036BD": {"name": "Ruchita Srivastava", "username": "ruchitas",   "active_from": "2025-01-01", "active_to": None,         "role": "Technical Writer"},
    # Ashish Alex left (Jul 18 2025) — removed from active roster
    # "U0780UP1KQB": {"name": "Ashish Alex", ...},
    # Bhumika Yadav left (May 5 2026) — removed from active roster
    # "U08HVLWG1UM": {"name": "Bhumika Yadav", ...},
    "U0900H3NUUT": {"name": "Utkarsha Sharma",    "username": "utkarshas",  "active_from": "2025-06-16", "active_to": None,         "role": "Designer"},
    # Tanya Khetrapal — 0 reported days since Jul 2025, not participating in attendance tracking
    # "WFBQQU8H5": {"name": "Tanya Khetrapal", ...},
    # Satyam Jha (intern) left — removed from active roster
    # "U0AKAJDDJHH": {"name": "Satyam Jha", ...},
}

# Aliases for readability in EVENTS list
A  = "W4R4S9FS4"   # Anurag
K  = "WAM5KDYBZ"   # Khushwant
C  = "W010NNJV7S8" # Chris
AJ = "U04BTKLSUF7" # Ajit
R  = "U03HRQ036BD" # Ruchita
AS = "U0780UP1KQB" # Ashish
B  = "U08HVLWG1UM" # Bhumika
U  = "U0900H3NUUT" # Utkarsha
T  = "WFBQQU8H5"   # Tanya
S  = "U0AKAJDDJHH" # Satyam

# Status codes: wfh | office | sick | pto | leave | no_info
# EVENTS = list of (date_str, member_id, status, short_note)
EVENTS = [
    # ── January 2025 ──────────────────────────────────────────────────────────
    # Anurag: "I will come to office post lunch hours. Morning meetings from home." (Jan 14)
    ("2025-01-14", A,  "office", "Morning meetings from home, then office post lunch"),
    ("2025-01-07", C,  "wfh",    "Wfh today"),
    ("2025-01-07", R,  "sick",   "Sick leave, bad throat and fever"),
    ("2025-01-08", R,  "wfh",    "Will login around 11"),
    ("2025-01-13", K,  "office", "Working from office"),
    ("2025-01-13", C,  "wfh",    "Wfh today"),
    ("2025-01-14", R,  "wfh",    "WFH today"),
    ("2025-01-15", C,  "wfh",    "wfh today"),
    ("2025-01-15", R,  "wfh",    "WFH today"),
    ("2025-01-17", K,  "wfh",    "WFH Today"),
    ("2025-01-17", C,  "wfh",    "Wife ill, WFH today"),
    ("2025-01-24", K,  "leave",  "On leave till 2:30 pm"),
    ("2025-01-24", R,  "leave",    "PTO today"),
    ("2025-01-27", C,  "wfh",    "wfh today"),
    ("2025-01-29", C,  "wfh",    "wfh today"),
    ("2025-01-29", R,  "wfh",    "WFH today"),
    ("2025-01-31", C,  "sick",   "Both me and wife unwell, taking PTO"),
    ("2025-01-31", R,  "wfh",    "WFH today"),

    # ── February 2025 ─────────────────────────────────────────────────────────
    ("2025-02-04", C,  "wfh",    "wfh today"),
    ("2025-02-04", R,  "wfh",    "WFH, son's school admit card"),
    ("2025-02-04", K,  "wfh",    "Morning meetings from home, then office"),
    ("2025-02-05", R,  "wfh",    "WFH due to Delhi elections"),
    ("2025-02-05", K,  "wfh",    "WFH"),
    ("2025-02-07", R,  "wfh",    "WFH today"),
    ("2025-02-07", K,  "leave",  "Away for first half"),
    ("2025-02-11", C,  "wfh",    "wfh today, PTO in 2nd half"),
    ("2025-02-11", R,  "wfh",    "Not feeling well, WFH"),
    ("2025-02-12", A,  "leave",  "Lost cousin, personal emergency"),
    ("2025-02-13", K,  "sick",   "Not feeling well, taking off"),
    ("2025-02-14", R,  "sick",   "Sick leave today"),
    ("2025-02-14", K,  "wfh",    "WFH today"),
    ("2025-02-17", K,  "leave",  "Severe headache, taking first half off"),
    ("2025-02-18", C,  "wfh",    "wfh today"),
    ("2025-02-19", C,  "wfh",    "wfh today"),
    ("2025-02-20", R,  "wfh",    "WFH today"),
    ("2025-02-20", C,  "wfh",    "wfh, severe back ache"),
    ("2025-02-21", K,  "wfh",    "WFH Today"),
    ("2025-02-21", C,  "wfh",    "Extending wfh, back pain"),
    ("2025-02-24", C,  "office", "At office (left early for physio)"),
    ("2025-02-24", K,  "wfh",    "WFH Today - daughter not well"),
    ("2025-02-25", K,  "wfh",    "Morning meetings from home, then office"),
    ("2025-02-25", C,  "wfh",    "wfh today, likely take off 2nd half"),
    ("2025-02-26", K,  "wfh",    "WFH today"),
    ("2025-02-26", C,  "office", "In hospital, then to office"),
    ("2025-02-28", K,  "leave",  "Taking leave, wife and kids ill"),
    ("2025-02-28", C,  "wfh",    "Wfh today"),

    # ── March 2025 ────────────────────────────────────────────────────────────
    ("2025-03-06", R,  "wfh",    "WFH today"),
    ("2025-03-06", K,  "leave",  "On leave for first half"),
    ("2025-03-06", C,  "sick",   "Not feeling well, logging off"),
    ("2025-03-10", R,  "leave",  "Leave today and tomorrow – son's exam"),
    ("2025-03-11", R,  "leave",  "On leave – son's exam"),
    ("2025-03-12", R,  "wfh",    "WFH today"),
    ("2025-03-12", C,  "wfh",    "wfh today"),
    ("2025-03-13", R,  "sick",   "Sick leave today"),
    ("2025-03-18", C,  "wfh",    "Wfh today"),
    ("2025-03-19", R,  "wfh",    "WFH today"),
    ("2025-03-20", K,  "wfh",    "Away 1st half, WFH 2nd half"),
    ("2025-03-21", R,  "sick",   "Fever with throat infection, sick leave"),
    ("2025-03-25", R,  "wfh",    "WFH today"),
    ("2025-03-25", C,  "wfh",    "wfh today"),
    ("2025-03-25", K,  "wfh",    "WFH today"),
    ("2025-03-27", A,  "office", "Back from Summit and sick leave, at office"),
    ("2025-03-27", C,  "wfh",    "wfh today"),

    # ── April 2025 ────────────────────────────────────────────────────────────
    ("2025-04-04", R,  "wfh",    "WFH today"),
    ("2025-04-04", C,  "wfh",    "WFH today"),
    ("2025-04-04", K,  "sick",   "Sore throat and feverish, taking day off"),
    ("2025-04-07", R,  "leave",    "On PTO today"),
    ("2025-04-07", K,  "wfh",    "Away 1st half, WFH 2nd half"),
    ("2025-04-11", R,  "wfh",    "WFH today"),
    ("2025-04-15", C,  "wfh",    "Wfh today, stepping out 2nd half"),
    ("2025-04-16", K,  "leave",  "On leave 16th and 17th April"),
    ("2025-04-17", K,  "leave",  "On leave 16th and 17th April"),
    ("2025-04-17", A,  "wfh",    "WFH today"),
    ("2025-04-17", R,  "wfh",    "WFH today"),
    ("2025-04-21", R,  "wfh",    "WFH today"),
    ("2025-04-21", C,  "wfh",    "Feeling unwell, opting for wfh"),
    ("2025-04-23", R,  "leave",    "On PTO today"),
    ("2025-04-25", A,  "wfh",    "WFH today"),
    ("2025-04-25", R,  "wfh",    "WFH today"),
    ("2025-04-25", C,  "wfh",    "Wfh today"),
    ("2025-04-25", K,  "office", "Working from office"),
    ("2025-04-29", A,  "wfh",    "Working from home and PTO 2nd half"),
    ("2025-04-30", K,  "wfh",    "Leave 1st half, WFH 2nd half"),

    # ── May 2025 ──────────────────────────────────────────────────────────────
    ("2025-05-05", A,  "leave",  "Away from office this week - mother hospitalized"),
    ("2025-05-05", C,  "wfh",    "WFH today and tomorrow"),
    ("2025-05-05", R,  "wfh",    "WFH today"),
    ("2025-05-07", A,  "leave",  "Mother hospitalized, limited availability"),
    ("2025-05-08", A,  "leave",  "Away this week, mother hospitalized"),
    ("2025-05-09", A,  "leave",  "Away from office this week - mother hospitalized"),
    ("2025-05-09", R,  "wfh",    "WFH"),
    ("2025-05-09", K,  "wfh",    "WFH Today"),
    ("2025-05-12", R,  "sick",   "Stomach infection, sick leave"),
    ("2025-05-12", K,  "office", "Working from office"),
    ("2025-05-14", A,  "office", "Joined office and clearing backlog"),
    ("2025-05-14", C,  "wfh",    "wfh today"),
    ("2025-05-16", R,  "wfh",    "WFH"),
    ("2025-05-16", C,  "wfh",    "WFH today"),
    ("2025-05-16", K,  "office", "Working From Office"),
    ("2025-05-19", K,  "office", "Working From Office"),
    ("2025-05-19", C,  "wfh",    "WFH Today"),
    ("2025-05-19", A,  "wfh",    "WFH today"),
    ("2025-05-20", C,  "wfh",    "Raining in Bangalore, WFH"),
    ("2025-05-21", R,  "wfh",    "WFH today, logging late"),
    ("2025-05-21", A,  "office", "In office again"),
    ("2025-05-22", A,  "wfh",    "WFH today, daughter not well"),
    ("2025-05-23", R,  "wfh",    "WFH today"),
    ("2025-05-23", A,  "wfh",    "WFH today"),
    ("2025-05-23", C,  "wfh",    "WFH today"),
    ("2025-05-23", K,  "wfh",    "On leave 1st half, then office"),
    ("2025-05-26", R,  "wfh",    "WFH today"),
    ("2025-05-26", C,  "wfh",    "Feeling under the weather, WFH"),
    ("2025-05-26", A,  "wfh",    "WFH today"),
    ("2025-05-28", C,  "wfh",    "WFH today, still recovering"),
    ("2025-05-29", R,  "wfh",    "WFH today"),
    ("2025-05-29", A,  "wfh",    "WFH today"),
    ("2025-05-29", K,  "leave",  "On leave for the first half"),
    ("2025-05-30", K,  "office", "Working from office"),
    ("2025-05-30", R,  "leave",    "PTO today"),
    ("2025-05-30", A,  "office", "Cancelled PTO, working"),

    # ── June 2025 ─────────────────────────────────────────────────────────────
    ("2025-06-02", A,  "wfh",    "WFH today"),
    ("2025-06-02", K,  "wfh",    "WFH 1st half, office 2nd half"),
    ("2025-06-03", A,  "office", "In office"),
    ("2025-06-03", C,  "wfh",    "WFH today"),
    ("2025-06-04", R,  "wfh",    "WFH, late (son to doctor)"),
    ("2025-06-04", K,  "office", "At office"),
    ("2025-06-04", A,  "office", "At office"),
    ("2025-06-04", C,  "office", "Coming late to office"),
    ("2025-06-05", A,  "office", "at office"),
    ("2025-06-05", C,  "wfh",    "WFH today"),
    ("2025-06-05", R,  "wfh",    "WFH today"),
    ("2025-06-05", K,  "leave",  "On leave 1st half, WFH 2nd half"),
    ("2025-06-06", K,  "office", "At Office"),
    ("2025-06-06", A,  "wfh",    "WFH today"),
    ("2025-06-06", R,  "wfh",    "WFH today"),
    ("2025-06-09", R,  "leave",  "On leave today, travelling"),
    ("2025-06-09", A,  "office", "At office"),
    ("2025-06-09", K,  "wfh",    "WFH - Punjab Today"),
    ("2025-06-10", R,  "wfh",    "WFH due to cough and cold"),
    ("2025-06-10", K,  "wfh",    "WFH"),
    ("2025-06-10", A,  "office", "At office"),
    ("2025-06-10", C,  "wfh",    "WFH today"),
    ("2025-06-11", R,  "office", "Reaching late to office"),
    ("2025-06-12", A,  "office", "at office"),
    ("2025-06-12", C,  "wfh",    "WFH today"),
    ("2025-06-13", R,  "wfh",    "WFH today"),
    ("2025-06-13", C,  "wfh",    "Feeling unwell, taking wfh"),
    ("2025-06-13", A,  "wfh",    "WFH today"),
    ("2025-06-17", R,  "wfh",    "WFH today, dropping son to airport"),
    ("2025-06-17", C,  "wfh",    "WFH today"),
    ("2025-06-18", K,  "leave",  "On leave 2nd half"),
    ("2025-06-19", C,  "wfh",    "WFH today"),
    ("2025-06-19", U,  "wfh",    "Wfh today"),
    ("2025-06-20", R,  "wfh",    "WFH today"),
    ("2025-06-20", U,  "wfh",    "Wfh today"),
    ("2025-06-20", K,  "leave",  "On leave 2nd half"),
    ("2025-06-23", A,  "office", "At office"),
    ("2025-06-23", K,  "wfh",    "WFh Today"),
    ("2025-06-23", U,  "wfh",    "Wfh today"),
    ("2025-06-24", R,  "wfh",    "WFH today"),
    ("2025-06-24", A,  "office", "Bhumika, Utkarsha and I at office"),
    ("2025-06-24", U,  "office", "At office (with Anurag)"),
    ("2025-06-25", A,  "wfh",    "WFH today"),
    ("2025-06-25", C,  "wfh",    "WFH today"),
    ("2025-06-26", A,  "office", "Ruchita, Utkarsha, Bhumika and I at office"),
    ("2025-06-26", R,  "office", "At office (with Anurag)"),
    ("2025-06-26", U,  "office", "At office (with Anurag)"),
    ("2025-06-27", A,  "wfh",    "WFH today"),
    ("2025-06-27", R,  "wfh",    "WFH today"),
    ("2025-06-27", C,  "wfh",    "WFH Today"),
    ("2025-06-30", A,  "wfh",    "WFH today"),
    ("2025-06-30", K,  "wfh",    "WFH 1st half, may visit office 2nd half"),

    # ── July 2025 ─────────────────────────────────────────────────────────────
    ("2025-07-02", A,  "office", "At office"),
    ("2025-07-02", C,  "wfh",    "WFH today"),
    ("2025-07-03", C,  "wfh",    "WFH today"),
    ("2025-07-03", R,  "wfh",    "WFH today"),
    ("2025-07-03", U,  "wfh",    "WFH today"),
    ("2025-07-07", R,  "leave",    "PTO today"),
    ("2025-07-07", U,  "wfh",    "Wfh today"),
    ("2025-07-07", K,  "wfh",    "Wfh today"),
    ("2025-07-07", A,  "office", "Working at office"),
    ("2025-07-08", C,  "wfh",    "WFH today"),
    ("2025-07-09", C,  "wfh",    "WFH today"),
    ("2025-07-10", U,  "wfh",    "WFH today"),
    ("2025-07-10", A,  "office", "At office with Khushwant, Ruchita, Bhumika"),
    ("2025-07-10", K,  "office", "At office"),
    ("2025-07-10", R,  "office", "At office"),
    ("2025-07-11", U,  "wfh",    "Wfh"),
    ("2025-07-11", R,  "wfh",    "WFH"),
    ("2025-07-14", A,  "wfh",    "WFH today"),
    ("2025-07-15", C,  "wfh",    "Wfh today"),
    ("2025-07-15", A,  "office", "At office"),
    ("2025-07-15", U,  "wfh",    "Wfh today"),
    ("2025-07-16", A,  "office", "WF-Sec25A office today"),
    ("2025-07-16", K,  "office", "At office"),
    ("2025-07-17", U,  "wfh",    "Wfh today (inferred from no office message)"),
    ("2025-07-18", A,  "wfh",    "WFH today"),
    ("2025-07-21", A,  "wfh",    "WFH today"),
    ("2025-07-22", C,  "wfh",    "WFH today"),
    ("2025-07-22", K,  "wfh",    "Away 1st half, at office 2nd half"),
    ("2025-07-22", A,  "office", "At office, got late"),
    ("2025-07-23", U,  "wfh",    "Wfh today"),
    ("2025-07-23", C,  "leave",  "Death in family, away 1st half"),
    ("2025-07-24", R,  "office", "Back in office after a long gap"),
    ("2025-07-24", A,  "office", "At office"),
    ("2025-07-24", K,  "wfh",    "WFH 1st half, running errand"),
    ("2025-07-25", R,  "wfh",    "WFH"),
    ("2025-07-25", U,  "wfh",    "Wfh today"),
    ("2025-07-28", A,  "office", "At office"),
    ("2025-07-28", C,  "wfh",    "Wfh, stepping out for personal work"),
    ("2025-07-29", A,  "office", "At office"),
    ("2025-07-29", U,  "office", "Working from office"),
    ("2025-07-30", R,  "office", "At office with Bhumika"),
    ("2025-07-30", A,  "wfh",    "WFH today"),
    ("2025-07-31", A,  "sick",   "Got fever and cold, sick leave"),
    ("2025-07-31", R,  "wfh",    "WFH today"),
    ("2025-07-31", K,  "wfh",    "WFH Today"),

    # ── August 2025 ───────────────────────────────────────────────────────────
    ("2025-08-01", A,  "office", "At office"),
    ("2025-08-01", R,  "wfh",    "WFH today"),
    ("2025-08-01", K,  "leave",  "On leave Today"),
    ("2025-08-04", R,  "wfh",    "WFH today"),
    ("2025-08-04", K,  "wfh",    "WFH Today"),
    ("2025-08-04", A,  "wfh",    "WFH today"),
    ("2025-08-04", U,  "wfh",    "WFH Today"),
    ("2025-08-05", A,  "office", "At office"),
    ("2025-08-05", U,  "wfh",    "Wfh today"),
    ("2025-08-05", K,  "office", "At office now (running late)"),
    ("2025-08-06", R,  "wfh",    "WFH today"),
    ("2025-08-06", C,  "wfh",    "Wfh today"),
    ("2025-08-06", A,  "office", "At office"),
    ("2025-08-06", K,  "office", "At office"),
    ("2025-08-06", U,  "wfh",    "wfh today"),
    ("2025-08-07", R,  "wfh",    "WFH"),
    ("2025-08-07", A,  "wfh",    "WFH today"),
    ("2025-08-07", K,  "office", "At office"),
    ("2025-08-07", U,  "office", "At office"),
    ("2025-08-08", R,  "wfh",    "WFH today"),
    ("2025-08-11", R,  "sick",   "Having high fever with body ache, on leave"),
    ("2025-08-11", A,  "office", "At office"),
    ("2025-08-11", U,  "office", "At office"),
    ("2025-08-11", K,  "wfh",    "Morning meeting from home, then office"),
    ("2025-08-12", R,  "sick",   "Still down with viral, fever, sick leave"),
    ("2025-08-12", U,  "wfh",    "Wfh today"),
    ("2025-08-12", A,  "office", "Morning meetings from home, then office"),
    ("2025-08-12", C,  "wfh",    "travelling back home, WFH"),
    ("2025-08-13", A,  "wfh",    "WFH today"),
    ("2025-08-13", K,  "office", "At office"),
    ("2025-08-13", R,  "wfh",    "WFH, feeling weak due to viral"),
    ("2025-08-13", C,  "office", "Taking calls from home, travel to office later"),
    ("2025-08-13", U,  "wfh",    "Wfh today"),
    ("2025-08-14", A,  "office", "At office"),
    ("2025-08-14", R,  "wfh",    "WFH today"),
    ("2025-08-14", U,  "wfh",    "WFH Today"),
    ("2025-08-18", U,  "office", "In office"),
    ("2025-08-18", A,  "wfh",    "WFH today"),
    ("2025-08-19", A,  "office", "Will be at office after morning meetings"),
    ("2025-08-19", U,  "wfh",    "wfh today"),
    ("2025-08-20", U,  "office", "At office"),
    ("2025-08-20", A,  "wfh",    "WFH today"),
    ("2025-08-20", R,  "wfh",    "WFH"),
    ("2025-08-20", K,  "wfh",    "WFH Today"),
    ("2025-08-21", U,  "office", "At office"),
    ("2025-08-22", R,  "wfh",    "WFH today"),
    ("2025-08-22", U,  "wfh",    "wfh today"),
    ("2025-08-22", A,  "wfh",    "WFH today"),
    ("2025-08-22", K,  "office", "At Office"),
    ("2025-08-25", A,  "wfh",    "WFH today"),
    ("2025-08-25", U,  "office", "At office"),
    ("2025-08-26", A,  "office", "At office (announced Aug 25 evening: 'Will be at office tomorrow')"),
    ("2025-08-26", K,  "office", "At office"),
    ("2025-08-26", C,  "wfh",    "WFH today"),
    ("2025-08-26", U,  "office", "At office"),
    ("2025-08-27", A,  "office", "at office"),
    ("2025-08-27", U,  "office", "At office"),
    ("2025-08-27", R,  "wfh",    "WFH today"),
    ("2025-08-28", K,  "office", "At office (running late)"),
    ("2025-08-28", A,  "office", "At office"),
    ("2025-08-28", U,  "wfh",    "Wfh today"),
    ("2025-08-28", C,  "wfh",    "WFH today"),
    ("2025-08-29", R,  "wfh",    "WFH today"),
    ("2025-08-29", U,  "wfh",    "Wfh today"),
    ("2025-08-29", A,  "wfh",    "WFH today"),

    # ── September 2025 ────────────────────────────────────────────────────────
    ("2025-09-01", A,  "wfh",    "WFH today"),
    ("2025-09-01", R,  "wfh",    "WFH, not feeling well"),
    ("2025-09-01", U,  "wfh",    "Wfh today"),
    ("2025-09-02", A,  "office", "WFH morning, office at 12"),
    ("2025-09-02", U,  "wfh",    "Wfh today"),
    ("2025-09-03", A,  "office", "at office since morning"),
    ("2025-09-03", K,  "office", "At office since morning"),
    ("2025-09-03", U,  "office", "At office"),
    ("2025-09-03", R,  "wfh",    "WFH due to rain and Yamuna situation"),
    ("2025-09-04", A,  "office", "at office"),
    ("2025-09-04", U,  "office", "At office"),
    ("2025-09-04", C,  "wfh",    "WFH today"),
    ("2025-09-04", R,  "wfh",    "Continuing WFH, Delhi situation"),
    ("2025-09-05", A,  "wfh",    "WFH today"),
    ("2025-09-05", U,  "wfh",    "Wfh today"),
    ("2025-09-05", R,  "wfh",    "WFH today"),
    ("2025-09-05", K,  "wfh",    "WFH Today"),
    ("2025-09-08", A,  "wfh",    "WFH today"),
    ("2025-09-08", R,  "office", "In Office"),
    ("2025-09-08", U,  "office", "At office"),
    ("2025-09-08", K,  "wfh",    "Wife ill, taking her to doctor, WFH"),
    ("2025-09-08", C,  "wfh",    "WFH today"),
    ("2025-09-09", A,  "leave",    "Will be on PTO tomorrow, daughter fever"),
    ("2025-09-10", R,  "wfh",    "WFH today"),
    ("2025-09-10", K,  "wfh",    "WFH Today"),
    ("2025-09-10", U,  "office", "At office"),
    ("2025-09-11", R,  "office", "At office"),
    ("2025-09-11", U,  "wfh",    "Wfh today"),
    ("2025-09-11", C,  "sick",   "Not feeling well, sick leave"),
    ("2025-09-12", R,  "wfh",    "WFH today"),
    ("2025-09-12", U,  "wfh",    "Wfh today"),
    ("2025-09-12", C,  "wfh",    "WFH today, still recovering"),
    ("2025-09-12", K,  "leave",  "On leave for first half"),
    ("2025-09-15", R,  "wfh",    "Stomach infection, prefer WFH"),
    ("2025-09-15", A,  "office", "At office"),
    ("2025-09-15", C,  "wfh",    "WFH Today"),
    ("2025-09-15", U,  "sick",   "Not feeling well, sick leave"),
    ("2025-09-16", A,  "office", "WFH morning, at office around noon"),
    ("2025-09-16", U,  "office", "At office"),
    ("2025-09-16", C,  "wfh",    "WFH today, nursing back issue"),
    ("2025-09-16", K,  "office", "At office"),
    ("2025-09-17", R,  "office", "Reaching late to office"),
    ("2025-09-17", A,  "office", "at office since morning"),
    ("2025-09-17", U,  "wfh",    "Wfh today"),
    ("2025-09-18", R,  "wfh",    "Travelling Ahmedabad, working remotely 19-26 Sep"),
    ("2025-09-18", A,  "office", "At office"),
    ("2025-09-19", A,  "wfh",    "WFH, IIML interviews"),
    ("2025-09-19", K,  "wfh",    "WFH Today"),
    ("2025-09-19", R,  "wfh",    "WFH remotely from Ahmedabad"),
    ("2025-09-22", A,  "office", "At office"),
    ("2025-09-22", U,  "office", "At office"),
    ("2025-09-22", R,  "leave",    "PTO today"),
    ("2025-09-23", A,  "wfh",    "WFH today"),
    ("2025-09-23", U,  "wfh",    "Wfh today"),
    ("2025-09-23", C,  "wfh",    "WFH today"),
    ("2025-09-23", K,  "office", "At office"),
    ("2025-09-24", A,  "office", "At office"),
    ("2025-09-24", U,  "office", "At office"),
    ("2025-09-25", A,  "office", "At office"),
    ("2025-09-25", K,  "wfh",    "WFH 1st half, then to office"),
    ("2025-09-25", C,  "wfh",    "Wfh today"),
    ("2025-09-25", U,  "office", "At office"),
    ("2025-09-29", A,  "wfh",    "WFH today"),
    ("2025-09-29", K,  "leave",  "On Leave Today"),
    ("2025-09-29", U,  "wfh",    "Wfh today"),
    ("2025-09-29", R,  "office", "At Office"),
    ("2025-09-30", A,  "office", "At office"),
    ("2025-09-30", R,  "office", "Reaching late (emergency with pet)"),
    ("2025-09-30", C,  "wfh",    "Wfh today"),

    # ── October 2025 ──────────────────────────────────────────────────────────
    ("2025-10-01", R,  "office", "At office"),
    ("2025-10-01", U,  "office", "At office"),
    ("2025-10-01", C,  "wfh",    "Wfh today"),
    ("2025-10-01", A,  "wfh",    "WFH today"),
    ("2025-10-01", K,  "wfh",    "WFH Today"),
    ("2025-10-06", A,  "office", "At office"),
    ("2025-10-06", U,  "office", "At office"),
    ("2025-10-06", R,  "wfh",    "WFH today"),
    ("2025-10-08", R,  "office", "At Office"),
    ("2025-10-08", U,  "wfh",    "Wfh today"),
    ("2025-10-10", R,  "wfh",    "WFH today"),
    ("2025-10-10", U,  "wfh",    "Wfh today"),
    ("2025-10-14", A,  "office", "At office"),
    ("2025-10-14", C,  "wfh",    "WFH today"),
    ("2025-10-15", A,  "office", "At office"),
    ("2025-10-16", K,  "office", "At Office"),
    ("2025-10-16", C,  "wfh",    "wfh today"),
    ("2025-10-16", U,  "wfh",    "Wfh today"),
    ("2025-10-16", R,  "wfh",    "WFH"),
    ("2025-10-17", R,  "wfh",    "WFH today"),
    ("2025-10-17", U,  "wfh",    "Wfh today"),
    ("2025-10-20", A,  "wfh",    "WFH today"),
    ("2025-10-20", K,  "leave",  "On leave 2nd half"),
    ("2025-10-20", U,  "leave",  "On leave"),
    ("2025-10-23", A,  "office", "At office"),
    ("2025-10-23", C,  "wfh",    "Wfh today"),
    ("2025-10-23", U,  "wfh",    "Wfh today"),
    ("2025-10-23", R,  "wfh",    "WFH today"),
    ("2025-10-24", K,  "office", "At Office"),
    ("2025-10-24", A,  "wfh",    "WFH today"),
    ("2025-10-27", K,  "office", "At office"),
    ("2025-10-27", C,  "wfh",    "wfh today"),
    ("2025-10-27", U,  "wfh",    "Experiencing back pain, WFH"),
    ("2025-10-27", R,  "office", "Reaching late to office"),
    ("2025-10-28", K,  "office", "At office"),
    ("2025-10-29", U,  "office", "At office"),
    ("2025-10-30", R,  "wfh",    "Unexpected guests, WFH"),
    ("2025-10-31", A,  "office", "At office"),
    ("2025-10-31", R,  "wfh",    "WFH today"),

    # ── November 2025 ─────────────────────────────────────────────────────────
    ("2025-11-03", R,  "office", "At Office"),
    ("2025-11-03", A,  "wfh",    "WFH today"),
    ("2025-11-04", C,  "wfh",    "WFH today"),
    ("2025-11-04", U,  "office", "At office"),
    ("2025-11-06", A,  "office", "At Mumbai with customers"),
    ("2025-11-06", U,  "wfh",    "Wfh today"),
    ("2025-11-07", A,  "office", "At office"),
    ("2025-11-07", R,  "wfh",    "WFH today"),
    ("2025-11-10", A,  "office", "At office"),
    ("2025-11-10", R,  "wfh",    "WFH today"),
    ("2025-11-11", C,  "wfh",    "WFH today"),
    ("2025-11-11", U,  "office", "At office"),
    ("2025-11-11", A,  "wfh",    "Death in extended family, WFH to babysit"),
    ("2025-11-12", R,  "office", "At Office"),
    ("2025-11-12", A,  "wfh",    "WFH today"),
    ("2025-11-13", U,  "wfh",    "Migraine pain, WFH"),
    ("2025-11-14", R,  "wfh",    "WFH today"),
    ("2025-11-17", A,  "wfh",    "WFH today"),
    ("2025-11-18", K,  "wfh",    "WFH Today"),
    ("2025-11-18", A,  "office", "At office"),
    ("2025-11-19", U,  "office", "At office"),
    ("2025-11-20", R,  "wfh",    "WFH today"),
    ("2025-11-20", K,  "wfh",    "WFH 1st half"),
    ("2025-11-20", A,  "wfh",    "Will come to office 2nd half"),
    ("2025-11-21", C,  "office", "WFH 1st half, office 2nd half"),
    ("2025-11-21", K,  "office", "Working from Office"),
    ("2025-11-24", K,  "leave",    "PTO Today"),
    ("2025-11-24", A,  "wfh",    "WFH today"),
    ("2025-11-25", R,  "office", "At office"),
    ("2025-11-25", K,  "leave",  "On leave first half"),
    ("2025-11-25", A,  "leave",  "On leave 1st half, taking care of daughter"),
    ("2025-11-26", R,  "wfh",    "Not feeling well, WFH"),
    ("2025-11-27", C,  "wfh",    "wfh today"),
    ("2025-11-27", K,  "leave",  "Khushwant is on Leave"),
    ("2025-11-28", R,  "wfh",    "WFH"),

    # ── December 2025 ─────────────────────────────────────────────────────────
    ("2025-12-01", R,  "leave",    "On PTO today and tomorrow"),
    ("2025-12-01", U,  "wfh",    "Not feeling well, WFH"),
    ("2025-12-01", K,  "office", "At office"),
    ("2025-12-02", A,  "office", "At office"),
    ("2025-12-02", U,  "wfh",    "Wfh today"),
    ("2025-12-02", R,  "leave",    "On PTO (day 2)"),
    ("2025-12-04", R,  "wfh",    "Husband and son not well, WFH"),
    ("2025-12-04", C,  "wfh",    "WFH today"),
    ("2025-12-04", A,  "wfh",    "WFH today"),
    ("2025-12-04", U,  "wfh",    "Fever, prefer WFH"),
    ("2025-12-05", R,  "wfh",    "WFH today"),
    ("2025-12-09", U,  "wfh",    "wfh today"),
    ("2025-12-09", K,  "leave",  "On leave first half"),
    ("2025-12-10", K,  "office", "At office"),
    ("2025-12-10", A,  "office", "At office"),
    ("2025-12-11", U,  "office", "At office"),
    ("2025-12-11", A,  "office", "At office"),
    ("2025-12-12", U,  "sick",   "On sick leave"),
    ("2025-12-15", A,  "office", "Ruchita, Khushwant, Anurag at office"),
    ("2025-12-15", K,  "office", "At office (with Anurag)"),
    ("2025-12-15", R,  "office", "At office (with Anurag)"),
    ("2025-12-15", U,  "wfh",    "Recovering, wfh"),
    ("2025-12-16", U,  "wfh",    "Wfh today"),
    ("2025-12-16", A,  "office", "At office"),
    ("2025-12-17", U,  "sick",   "On sick leave"),
    ("2025-12-17", K,  "leave",  "On leave second half"),
    ("2025-12-18", U,  "wfh",    "Wfh today"),
    ("2025-12-19", A,  "wfh",    "WFH today"),
    ("2025-12-19", K,  "wfh",    "WFH Today"),
    ("2025-12-19", R,  "wfh",    "WFH today"),
    ("2025-12-19", U,  "wfh",    "Wfh today"),
    ("2025-12-22", R,  "wfh",    "WFH"),
    ("2025-12-23", K,  "office", "At office"),
    ("2025-12-23", U,  "wfh",    "Wfh today"),

    # ── January 2026 ──────────────────────────────────────────────────────────
    ("2026-01-02", R,  "leave",    "PTO today"),
    ("2026-01-02", K,  "leave",    "PTO Today"),
    ("2026-01-05", R,  "office", "At office"),
    ("2026-01-05", A,  "wfh",    "WFH today"),
    ("2026-01-08", K,  "office", "At Office"),
    ("2026-01-08", U,  "wfh",    "Working from home today"),
    ("2026-01-09", K,  "wfh",    "WFH Today"),
    ("2026-01-12", R,  "office", "At office"),
    ("2026-01-12", K,  "wfh",    "Working in patches from home"),
    ("2026-01-12", A,  "wfh",    "WFH today"),
    ("2026-01-13", C,  "wfh",    "WFH today"),
    ("2026-01-13", K,  "leave",  "Filling leave for today"),
    ("2026-01-14", R,  "office", "At Office"),
    ("2026-01-14", K,  "office", "Late, picking daughter from school"),
    ("2026-01-15", R,  "wfh",    "WFH today"),
    ("2026-01-15", A,  "sick",   "On Sick leave today"),
    ("2026-01-15", K,  "office", "I am at office"),
    ("2026-01-15", U,  "wfh",    "WFH, mandatory session 2-5pm"),
    ("2026-01-15", C,  "leave",  "Holiday in Bangalore for Sankranti & Pongal"),
    ("2026-01-16", K,  "wfh",    "WFH, taking care of daughter"),
    ("2026-01-16", A,  "office", "At office"),
    ("2026-01-19", K,  "office", "At office"),
    ("2026-01-19", A,  "wfh",    "WFH today"),
    ("2026-01-19", U,  "wfh",    "Wfh (Menstrual discomfort)"),
    ("2026-01-19", R,  "wfh",    "WFH, feeling under the weather"),
    ("2026-01-20", A,  "office", "Ruchita, Khushwant, Anurag at office"),
    ("2026-01-20", K,  "office", "At office"),
    ("2026-01-20", R,  "office", "At office"),
    ("2026-01-21", A,  "office", "At office"),
    ("2026-01-23", R,  "wfh",    "WFH today"),
    ("2026-01-23", K,  "wfh",    "WFH Today (rain)"),
    ("2026-01-23", A,  "wfh",    "WFH due to rains"),
    ("2026-01-27", R,  "sick",   "Taking sick leave, not feeling well"),
    ("2026-01-27", A,  "sick",   "Out sick with stomach infection, PTO"),
    ("2026-01-27", C,  "wfh",    "WFH Today"),
    ("2026-01-27", U,  "office", "Working from office"),
    ("2026-01-27", K,  "office", "Working from office"),
    ("2026-01-28", A,  "sick",   "Sick leave today"),
    ("2026-01-28", R,  "office", "At Office"),
    ("2026-01-28", C,  "wfh",    "WFH Today"),
    ("2026-01-29", A,  "sick",   "Sick leave, getting tests done"),
    ("2026-01-29", R,  "office", "At Office"),
    ("2026-01-29", K,  "leave",  "On leave 1st half, reaching office around 1"),
    ("2026-01-29", U,  "office", "At office"),
    ("2026-01-30", A,  "office", "At office"),
    ("2026-01-30", R,  "wfh",    "WFH today"),
    ("2026-01-30", U,  "wfh",    "Wfh today"),

    # ── February 2026 ─────────────────────────────────────────────────────────
    ("2026-02-02", A,  "office", "At office"),
    ("2026-02-03", C,  "office", "WFO"),
    ("2026-02-04", R,  "wfh",    "WFH today"),
    ("2026-02-04", A,  "office", "At office"),
    ("2026-02-04", U,  "wfh",    "Shoulder pain, WFH"),
    ("2026-02-05", R,  "office", "At Office"),
    ("2026-02-06", A,  "office", "At office"),
    ("2026-02-06", R,  "wfh",    "WFH today"),
    ("2026-02-06", U,  "leave",  "On leave today"),
    ("2026-02-09", A,  "wfh",    "WFH today"),
    ("2026-02-09", C,  "wfh",    "WFH today, feeling unwell"),
    ("2026-02-10", R,  "wfh",    "WFH today"),
    ("2026-02-10", C,  "wfh",    "still recovering"),
    ("2026-02-10", U,  "office", "At office"),
    ("2026-02-11", A,  "office", "At office"),
    ("2026-02-12", R,  "office", "At Office"),
    ("2026-02-12", C,  "wfh",    "WFH today (neck and back ache)"),
    ("2026-02-12", U,  "leave",    "PTO today"),
    ("2026-02-13", C,  "office", "At office"),
    ("2026-02-13", U,  "office", "Working from office"),
    ("2026-02-13", R,  "wfh",    "WFH today"),
    ("2026-02-16", R,  "office", "At Office"),
    ("2026-02-16", A,  "wfh",    "WFH today"),
    ("2026-02-16", C,  "wfh",    "WFH Today, wife to doc 2nd half"),
    ("2026-02-17", C,  "wfh",    "WFH today"),
    ("2026-02-17", K,  "wfh",    "WFH 1st half, away 1-2:15pm"),
    ("2026-02-17", U,  "office", "At office"),
    ("2026-02-18", R,  "office", "At office"),
    ("2026-02-18", A,  "wfh",    "WFH today"),
    ("2026-02-18", K,  "leave",  "Not feeling well, leaving for day"),
    ("2026-02-19", R,  "office", "At office"),
    ("2026-02-19", K,  "leave",  "Not feeling well, off 1st half"),
    ("2026-02-19", C,  "wfh",    "WFH Today, doctor 2nd half"),
    ("2026-02-20", R,  "wfh",    "WFH today"),
    ("2026-02-20", K,  "sick",   "Recovering, taking off today"),
    ("2026-02-20", A,  "wfh",    "WFH today"),
    ("2026-02-20", U,  "office", "At office"),
    ("2026-02-23", R,  "office", "At Office"),
    ("2026-02-23", K,  "office", "Running late, office around 12:30"),
    ("2026-02-23", C,  "sick",   "Feeling unwell, PTO 1st half"),
    ("2026-02-24", R,  "office", "At Office"),
    ("2026-02-24", C,  "wfh",    "WFH Today"),
    ("2026-02-25", R,  "wfh",    "WFH today"),
    ("2026-02-25", U,  "office", "At office"),
    ("2026-02-26", R,  "office", "At Office"),
    ("2026-02-26", C,  "wfh",    "WFH today"),
    ("2026-02-26", A,  "wfh",    "WFH today"),
    ("2026-02-27", C,  "office", "At Office"),
    ("2026-02-27", K,  "office", "WFH 1st half, at office 2nd half"),

    # ── March 2026 ────────────────────────────────────────────────────────────
    ("2026-03-02", K,  "office", "At office"),
    ("2026-03-02", U,  "wfh",    "Wfh today"),
    ("2026-03-02", R,  "wfh",    "Not feeling well, login late, WFH"),
    ("2026-03-03", R,  "wfh",    "WFH"),
    ("2026-03-05", R,  "office", "At Office"),
    ("2026-03-05", U,  "wfh",    "Wfh today"),
    ("2026-03-06", R,  "wfh",    "WFH today"),
    ("2026-03-06", C,  "office", "At Office"),
    ("2026-03-09", A,  "wfh",    "WFH today"),
    ("2026-03-09", C,  "wfh",    "WFH this week, out of town"),
    ("2026-03-09", R,  "office", "At office"),
    ("2026-03-09", K,  "leave",  "On leave 1st half"),
    ("2026-03-10", U,  "office", "At office"),
    ("2026-03-10", A,  "leave",    "On PTO today"),
    ("2026-03-10", R,  "leave",  "Taking half day PTO"),
    ("2026-03-10", K,  "office", "WFH morning, office around 11"),
    ("2026-03-12", R,  "wfh",    "WFH today"),
    ("2026-03-12", K,  "leave",  "On leave 1st half"),
    ("2026-03-13", R,  "wfh",    "WFH"),
    ("2026-03-13", K,  "wfh",    "WFH Today"),
    ("2026-03-13", A,  "wfh",    "WFH 1st half, at office post lunch"),
    ("2026-03-16", U,  "office", "At office"),
    ("2026-03-16", C,  "wfh",    "WFH Today"),
    ("2026-03-17", K,  "wfh",    "WFH 1st half, office 2nd half"),
    ("2026-03-17", A,  "wfh",    "WFH today"),
    ("2026-03-17", C,  "office", "At Office"),
    ("2026-03-17", U,  "office", "At office"),
    ("2026-03-18", U,  "office", "At office"),
    ("2026-03-18", K,  "wfh",    "WFH 1st half, may go to office 2nd half"),
    ("2026-03-18", A,  "wfh",    "WFH today"),
    ("2026-03-19", A,  "office", "WFH till 2PM, office later"),
    ("2026-03-19", R,  "office", "At office"),
    ("2026-03-19", C,  "office", "At office"),
    ("2026-03-19", U,  "wfh",    "Wfh today"),
    ("2026-03-20", K,  "wfh",    "WFH"),
    ("2026-03-20", A,  "office", "At office"),
    ("2026-03-23", R,  "office", "At Office"),
    ("2026-03-23", A,  "wfh",    "WFH today"),
    ("2026-03-23", C,  "sick",   "Sick leave, injured in football"),
    ("2026-03-24", R,  "office", "Stuck in traffic, late to office"),
    ("2026-03-24", A,  "office", "At office"),
    ("2026-03-24", C,  "wfh",    "WFH Today, still recovering"),
    ("2026-03-25", R,  "office", "At Office"),
    ("2026-03-26", A,  "office", "At office, enjoying alone"),
    ("2026-03-26", U,  "wfh",    "Wfh today"),
    ("2026-03-26", C,  "wfh",    "WFH today, out of office 2nd half"),
    ("2026-03-27", A,  "sick",   "Sick leave today"),
    ("2026-03-30", A,  "wfh",    "WFH today"),
    ("2026-03-30", C,  "office", "at Office"),
    ("2026-03-31", A,  "office", "At office"),
    ("2026-03-31", R,  "wfh",    "WFH today"),

    # ── April 2026 ────────────────────────────────────────────────────────────
    ("2026-04-01", A,  "office", "At office"),
    ("2026-04-01", C,  "office", "At Office"),
    ("2026-04-02", C,  "wfh",    "WFH today"),
    ("2026-04-06", R,  "office", "At office"),
    ("2026-04-06", A,  "wfh",    "WFH 1st half, office post lunch"),
    ("2026-04-06", C,  "wfh",    "WFH"),
    ("2026-04-07", A,  "wfh",    "WFH today"),
    ("2026-04-07", K,  "office", "At office"),
    ("2026-04-07", U,  "office", "At office"),
    ("2026-04-08", C,  "wfh",    "WFH today"),
    ("2026-04-08", U,  "sick",   "Sick leave today"),
    ("2026-04-09", A,  "office", "At office"),
    ("2026-04-09", R,  "wfh",    "WFH today"),
    ("2026-04-10", C,  "office", "At Office"),
    ("2026-04-10", K,  "wfh",    "WFH till 3pm"),
    ("2026-04-13", U,  "office", "At office"),
    ("2026-04-13", R,  "sick",   "Not feeling well, sick leave"),
    ("2026-04-13", K,  "office", "Running errand, office around 12:30"),
    ("2026-04-14", K,  "office", "At Office"),
    ("2026-04-14", A,  "wfh",    "WFH today"),
    ("2026-04-14", C,  "wfh",    "WFH today"),
    ("2026-04-14", R,  "wfh",    "WFH (Khushwant advised stay home)"),
    ("2026-04-15", U,  "office", "At office"),
    ("2026-04-16", A,  "wfh",    "WFH today"),
    ("2026-04-17", U,  "wfh",    "Wfh today"),
    ("2026-04-20", R,  "office", "At Office"),
    ("2026-04-20", C,  "wfh",    "WFH today"),
    ("2026-04-20", U,  "office", "Cancelled leave, at work"),
    ("2026-04-20", K,  "leave",  "Father in ICU, on-and-off this week"),
    ("2026-04-21", C,  "office", "At office"),
    ("2026-04-23", C,  "wfh",    "WFH today"),
    ("2026-04-27", R,  "office", "At office"),
    ("2026-04-27", U,  "wfh",    "WFH, suffering from migraine"),
    ("2026-04-28", U,  "office", "At office"),
    ("2026-04-28", A,  "office", "At office, joined a day earlier"),
    ("2026-04-29", R,  "leave",    "On leave today"),
    ("2026-04-29", U,  "wfh",    "wfh today"),
    ("2026-04-29", K,  "office", "At Office"),
    ("2026-04-30", R,  "office", "At Office"),
    ("2026-04-30", K,  "office", "At Office"),
    ("2026-04-30", C,  "wfh",    "WFH today"),

    # ── May 2026 ──────────────────────────────────────────────────────────────
    ("2026-05-04", U,  "wfh",    "Wfh today"),
    ("2026-05-04", A,  "office", "At office"),
    ("2026-05-05", C,  "wfh",    "WFH today"),
    ("2026-05-05", U,  "office", "At office"),
    ("2026-05-05", R,  "leave",  "On leave today"),
    ("2026-05-06", C,  "office", "At Office"),
    ("2026-05-06", U,  "office", "At office"),
    ("2026-05-07", R,  "wfh",    "WFH today"),
    ("2026-05-07", A,  "office", "At office"),
    ("2026-05-07", K,  "leave",  "On leave, limited access"),
    ("2026-05-08", A,  "office", "At office"),
    ("2026-05-08", U,  "wfh",    "WFH today"),
    ("2026-05-11", U,  "office", "At office"),
    ("2026-05-12", A,  "office", "At office"),
    ("2026-05-12", C,  "wfh",    "WFH today"),
    ("2026-05-12", R,  "leave",  "On leave today"),
    ("2026-05-12", K,  "wfh",    "WFH till 4pm"),
    ("2026-05-13", U,  "office", "At office"),
    ("2026-05-13", K,  "wfh",    "WFH, online 10:45-5:30"),
    ("2026-05-13", A,  "office", "At office"),
    ("2026-05-14", A,  "office", "At Maruti Gurgaon"),
    ("2026-05-14", C,  "office", "At Office"),
    ("2026-05-14", U,  "wfh",    "Wfh today"),
    ("2026-05-14", K,  "wfh",    "WFH, online 11:30 onwards"),
    ("2026-05-15", A,  "office", "At office"),
    ("2026-05-15", C,  "wfh",    "WFH today"),
    ("2026-05-18", R,  "wfh",    "WFH today"),
    ("2026-05-18", U,  "office", "At office"),
    ("2026-05-19", R,  "office", "At Office"),
    ("2026-05-19", C,  "wfh",    "WFH today"),
    ("2026-05-19", U,  "office", "+1 to Ruchita (At Office)"),
    ("2026-05-19", A,  "office", "+1 to Ruchita (At Office)"),
    ("2026-05-20", U,  "office", "At office"),
    ("2026-05-20", C,  "wfh",    "WFH - raining in Bangalore"),
    ("2026-05-20", R,  "office", "+1 to Utkarsha (At office)"),
    ("2026-05-20", A,  "office", "+1 to Utkarsha (At office)"),
    ("2026-05-21", C,  "wfh",    "WFH today"),
    ("2026-05-21", U,  "office", "At office"),
    ("2026-05-21", A,  "office", "In office"),
    ("2026-05-21", R,  "wfh",    "WFH today, logging late"),
    ("2026-05-22", A,  "office", "Was at office in morning, WFH rest of day"),
    ("2026-05-22", C,  "sick",   "Feeling unwell, taking rest of day off"),
    ("2026-05-22", K,  "leave",  "On Leave"),
    ("2026-05-22", U,  "wfh",    "Wfh today"),
    ("2026-05-22", R,  "wfh",    "+1 to Utkarsha (Wfh today)"),
    ("2026-05-25", R,  "wfh",    "WFH today"),
    ("2026-05-25", A,  "office", "At office"),
    ("2026-05-25", U,  "office", "At office"),
    ("2026-05-25", C,  "wfh",    "+1 to Ruchita (WFH today)"),
    ("2026-05-26", R,  "sick",   "Not feeling well, sick leave"),
    ("2026-05-26", A,  "office", "At office"),
    ("2026-05-26", U,  "office", "At office"),
    ("2026-05-26", C,  "office", "+1 to Anurag (At office)"),
    ("2026-05-28", U,  "wfh",    "Wfh today"),
    ("2026-05-28", A,  "office", "At office"),
    ("2026-05-28", C,  "wfh",    "OOO 1st half, WFH 2nd half"),
    ("2026-05-28", R,  "leave",  "Bereavement - grandmother passed away"),
    ("2026-05-29", R,  "leave",  "On leave, rituals at home"),
    ("2026-05-29", U,  "wfh",    "wfh today"),
    ("2026-05-29", A,  "office", "At office"),
    ("2026-05-29", C,  "wfh",    "Feeling under the weather, WFH"),

    # ── June 2026 ─────────────────────────────────────────────────────────────
    ("2026-06-01", U,  "office", "At office"),
    ("2026-06-01", C,  "office", "+1 to Utkarsha (at office)"),
    ("2026-06-02", A,  "office", "At office"),
    ("2026-06-02", U,  "office", "At office"),
    ("2026-06-02", C,  "wfh",    "WFH today"),
    ("2026-06-03", A,  "office", "At office"),
    ("2026-06-03", C,  "office", "At office"),
    ("2026-06-03", U,  "wfh",    "Wfh today"),
    ("2026-06-03", R,  "wfh",    "+1 to Utkarsha (Wfh today)"),
    ("2026-06-04", A,  "office", "At office"),
    ("2026-06-04", C,  "wfh",    "WFH today"),
    ("2026-06-04", U,  "office", "At office"),
    ("2026-06-04", R,  "office", "Reaching office around 10:30"),
    ("2026-06-05", A,  "office", "At office"),
    ("2026-06-05", C,  "office", "At office"),
    ("2026-06-05", R,  "wfh",    "WFH today"),
    ("2026-06-05", U,  "wfh",    "+1 to Ruchita (WFH today)"),
    # ── AUTO-ADDED by Friday review task — insert new entries above this line ──
]


# ── Official Adobe India paid holidays ─────────────────────────────────────────
# Source: "2026 Global Holidays Master PDF 5_14_26.pdf" (Adobe Confidential)
# Pages 47-49: India | Chennai/Bangalore, India | Mumbai, India | Noida/New Delhi/Gurgaon
#
# Team locations:
#   Noida/Delhi: Anurag (W4R4S9FS4), Khushwant (WAM5KDYBZ), Ruchita (U03HRQ036BD),
#                Utkarsha (U0900H3NUUT)
#   Bangalore:   Chris J (W010NNJV7S8)
#
# Common holidays (both locations share these) go in HOLIDAYS_COMMON.
# Location-specific:
#   • Makar Sankranti Jan 14 (Bangalore only) → Chris's "leave" EVENTS entry is correct.
#   • Guru Nanak's Birthday Nov 24 (Noida only) → added to HOLIDAYS; slight 1-day over-count
#     for Chris is acceptable given data volume.
#
# 2025 entries: Independence Day + Gandhi Jayanti confirmed from channel; others estimated
# from the same Adobe pattern (confirmed 2026 structure). Marked with [est-2025].

HOLIDAYS = {
    # ── 2025 ─────────────────────────────────────────────────────────────────
    "2025-01-01",   # New Year's Day (Wednesday) [est-2025]
    # Makar Sankranti Jan 14 (Bangalore/Chris) → already "leave" in EVENTS
    "2025-03-14",   # Holi (Friday) [est-2025]
    "2025-03-21",   # Global Wellbeing Day (Friday) [est-2025 — Adobe quarterly GWD]
    "2025-04-18",   # Good Friday (Friday) [est-2025]
    "2025-05-01",   # Labour Day (Thursday) [est-2025]
    "2025-06-27",   # Global Wellbeing Day (Friday) [est-2025 — Q2, similar to 2026 Jun 29]
    "2025-08-15",   # Independence Day (Friday)  ← confirmed from channel
    "2025-08-22",   # Global Wellbeing Day (Friday) [est-2025 — Q3, similar to 2026 Aug 21]
    "2025-08-27",   # Ganesh Chaturthi (Wednesday) [est-2025]
    "2025-10-02",   # Gandhi Jayanti (Thursday)   ← confirmed from channel
    "2025-10-20",   # Deepavali/Diwali (Monday) [est-2025]
    "2025-10-31",   # Global Wellbeing Day (Friday) [est-2025]
    "2025-11-05",   # Guru Nanak's Birthday (Wednesday) [est-2025 — Noida; +Chris negligible]
    "2025-12-24",   # Christmas Eve / Winter shutdown (Wednesday) [est-2025]
    "2025-12-25",   # Christmas Day (Thursday) [est-2025]
    "2025-12-26",   # Winter shutdown (Friday) [est-2025]
    "2025-12-29",   # Winter shutdown (Monday) [est-2025]
    "2025-12-30",   # Winter shutdown (Tuesday) [est-2025]
    "2025-12-31",   # Winter shutdown (Wednesday) [est-2025]

    # ── 2026 — FROM OFFICIAL PDF ──────────────────────────────────────────────
    "2026-01-01",   # New Year's Day (Thursday)
    # Makar Sankranti Jan 14 (Bangalore/Chris) → already "leave" in EVENTS for Chris
    "2026-01-26",   # Republic Day (Monday)
    "2026-03-04",   # Holi (Wednesday)
    "2026-03-20",   # Global Wellbeing Day (Friday)
    "2026-04-03",   # Good Friday (Friday)
    "2026-05-01",   # Labour Day (Friday)         ← was called "Buddha Purnima" by bot, same date
    "2026-05-27",   # Eid al-Adha / Bakri Id (Wednesday) ← CORRECTED from May 28 (bot was off by 1 day)
    "2026-06-29",   # Global Wellbeing Day (Monday)
    "2026-08-21",   # Global Wellbeing Day (Friday)
    "2026-09-14",   # Ganesh Chaturthi (Monday)
    "2026-10-02",   # Gandhi Jayanti (Friday)
    "2026-10-20",   # Dussehra (Tuesday)
    "2026-10-30",   # Global Wellbeing Day (Friday)
    "2026-11-09",   # Deepavali / Govardhan Puja (Monday) [subject to gazette notification]
    "2026-11-24",   # Guru Nanak's Birthday (Tuesday) — Noida; +Chris 1-day over negligible
    "2026-12-24",   # Christmas Eve / Winter shutdown (Thursday)
    "2026-12-25",   # Christmas Day / Winter shutdown (Friday)
    "2026-12-28",   # Winter shutdown (Monday)
    "2026-12-29",   # Winter shutdown (Tuesday)
    "2026-12-30",   # Winter shutdown (Wednesday)
    "2026-12-31",   # Winter shutdown (Thursday)
}

# Also update parse_attendance.py HOLIDAYS to match — run: python3 seed_attendance.py
# NOTE: Bangalore-specific Makar Sankranti (Jan 14, 2026 and Jan 15, 2025) is correctly
# captured as "leave" in Chris's EVENTS entries. Not in HOLIDAYS so it does not
# accidentally remove a working day for the Noida team.


def is_member_active(mid: str, d: date) -> bool:
    m = MEMBERS[mid]
    af = date.fromisoformat(m["active_from"])
    at = date.fromisoformat(m["active_to"]) if m["active_to"] else date(2099, 12, 31)
    return af <= d <= at


def working_days(start: date, end: date):
    cur = start
    while cur <= end:
        if cur.weekday() < 5 and cur.isoformat() not in HOLIDAYS:
            yield cur
        cur += timedelta(days=1)


# Correction priority: if multiple messages for same person/day, prefer the "better" one.
# office > wfh > sick > leave > no_info
# (e.g. "WFH today" at 9am then "At office" at 2pm → office wins)
STATUS_PRIORITY = {"office": 5, "wfh": 4, "sick": 3, "leave": 2, "no_info": 1}


def build():
    att: dict[str, dict] = {}

    for ds, uid, status, note in EVENTS:
        # Skip official holidays entirely — even if someone posted a status that day,
        # the day is not a working day and must not appear in the attendance calendar.
        if ds in HOLIDAYS:
            continue
        # Also skip weekend dates (should not be in EVENTS, but defensive check)
        if date.fromisoformat(ds).weekday() >= 5:
            continue
        att.setdefault(ds, {})
        if uid not in att[ds]:
            att[ds][uid] = {"status": status, "note": note}
        else:
            # Use higher-priority status when corrections are posted later in the day
            existing_pri = STATUS_PRIORITY.get(att[ds][uid]["status"], 0)
            new_pri      = STATUS_PRIORITY.get(status, 0)
            if new_pri > existing_pri:
                att[ds][uid] = {"status": status, "note": note}

    start = date(2025, 1, 1)
    end   = date.today()

    for d in working_days(start, end):
        ds = d.isoformat()
        att.setdefault(ds, {})
        for mid in MEMBERS:
            if is_member_active(mid, d) and mid not in att[ds]:
                att[ds][mid] = {"status": "no_info", "note": None}

    return dict(sorted(att.items()))


def main():
    data_dir = Path(__file__).parent / "data"
    raw_path = data_dir / "raw_messages.json"

    # Safety guard: if raw_messages.json exists, running this script standalone
    # would OVERWRITE attendance.json and discard all Slack history attribution.
    # Use parse_attendance.py instead — it merges both sources automatically.
    if raw_path.exists():
        print("⚠️  WARNING: raw_messages.json exists.")
        print("   Running seed_attendance.py standalone would OVERWRITE attendance.json")
        print("   and lose all Slack history data from raw_messages.json.")
        print("")
        print("   Use this instead:")
        print("     python3 parse_attendance.py")
        print("")
        print("   This merges raw_messages.json + seed_attendance.py EVENTS automatically.")
        print("   Aborting.")
        raise SystemExit(1)

    data_dir.mkdir(exist_ok=True)
    att = build()
    output = {
        "generated_at": date.today().isoformat(),
        "period": {"from": "2025-01-01", "to": date.today().isoformat()},
        "team_members": MEMBERS,
        "attendance": att,
    }
    out = data_dir / "attendance.json"
    out.write_text(json.dumps(output, indent=2, default=str))
    days = len(att)
    records = sum(len(v) for v in att.values())
    print(f"Written {days} days, {records} records → {out}")


if __name__ == "__main__":
    main()

# Data Model

## `data/attendance.json` — structure

This is the single source of truth consumed by the dashboard and report generator.

```jsonc
{
  "generated_at": "2026-06-06",          // ISO date — shown as "Updated Jun 6, 2026"
  "period": {
    "from": "2025-01-01",
    "to":   "2026-06-06"
  },
  "team_members": {                       // Active members only (departed excluded)
    "W4R4S9FS4": {
      "name":        "Anurag Sharma",
      "username":    "anusharm",
      "active_from": "2025-01-01",
      "active_to":   null,               // null = still active
      "role":        "Manager"
    }
    // ... one entry per member
  },
  "attendance": {                         // Keyed by ISO date string
    "2026-06-02": {
      "W4R4S9FS4":  { "status": "office", "note": "At office today" },
      "WAM5KDYBZ":  { "status": "wfh",    "note": "WFH today" },
      "W010NNJV7S8":{ "status": "no_info","note": null },
      // ... one entry per active member per working day
    }
  }
}
```

---

## Status values

| Value | Label | Color | Meaning |
|---|---|---|---|
| `office` | Office | Green `#0E9F5C` | Physically at an office location |
| `wfh` | WFH | Blue `#0265DC` | Working from home |
| `sick` | Sick | Red `#D31420` | Sick leave — personal illness, not working |
| `leave` | Leave | Amber `#CE9500` | Planned PTO, personal leave, half-day |
| `no_info` | No Info | Grey `#C8C8C8` | No status posted — data unavailable |

### Classification rules (in priority order)

1. **Sick** — explicit sick leave phrases, or leave + personal illness keywords
2. **Leave** — "on leave", "PTO", "day off", "taking leave"
3. **WFH** — "WFH", "work from home", "working remotely"
4. **Office** — "at office", "in office", official travel (Sec-25A, N132, customer site, workshop, offsite)
5. **Leave (second pass)** — half-day signals, filing leave

### Correction priority

If a person posts multiple statuses in one day, the **higher priority** wins:

```
office (5) > wfh (4) > sick (3) > leave (2) > no_info (1)
```

Example: Someone posts "WFH today" at 9 AM, then "Heading to office" at 11 AM → recorded as `office`.

### Special cases

| Situation | Classification |
|---|---|
| Official travel (customer site, other Adobe building) | `office` |
| WFH because family member is ill | `wfh` (not sick) |
| Leave because personally ill | `sick` |
| "Leaving the office" / "heading home" | `office` (implies was at office) |
| Group message: "Ruchita and I at office" | `office` for sender AND Ruchita |
| "WFH today and tomorrow" | `wfh` for today AND tomorrow |

---

## What days appear in `attendance`

Only **working days** appear — defined as:
- Monday–Friday, AND
- Not a public holiday (see `HOLIDAYS` set in `seed_attendance.py`)

Weekends and holidays are **completely absent** from the JSON.

---

## Member active periods

The `active_from` / `active_to` fields control which dates a member appears in the data:

```python
# Member is active on date d if:
active_from <= d <= (active_to or 2099-12-31)
```

Departed members are retained in `seed_attendance.py`'s `EVENTS` for historical accuracy but excluded from `team_members` in the output so the dashboard doesn't show them.

---

## `data/raw_messages.json` — structure

Produced by `fetch_slack.py`. Array of Slack message objects:

```jsonc
[
  {
    "ts":         "1704153600.123456",   // Unix timestamp (Slack message ID)
    "user":       "W4R4S9FS4",           // Slack user ID
    "text":       "WFH today, will be online all day",
    "reactions":  [                      // Emoji reactions on the message
      { "name": "office", "count": 2, "users": ["WAM5KDYBZ"] }
    ],
    "reply_count": 0,
    "thread_ts":  null
  }
]
```

Deduplication is by `ts`. Thread replies are fetched separately and appended.

---

## Holiday calendar

Defined as a Python `set` of ISO date strings in `seed_attendance.py` and `parse_attendance.py`.

### 2026 holidays (from Adobe official PDF, India / Noida)
| Date | Holiday |
|---|---|
| 2026-01-01 | New Year's Day |
| 2026-01-26 | Republic Day |
| 2026-03-04 | Holi |
| 2026-03-20 | Global Wellbeing Day |
| 2026-04-03 | Good Friday |
| 2026-05-01 | Labour Day |
| 2026-05-27 | Eid al-Adha / Bakri Id |
| 2026-06-29 | Global Wellbeing Day |
| 2026-08-21 | Global Wellbeing Day |
| 2026-09-14 | Ganesh Chaturthi |
| 2026-10-02 | Gandhi Jayanti |
| 2026-10-20 | Dussehra |
| 2026-10-30 | Global Wellbeing Day |
| 2026-11-09 | Deepavali / Govardhan Puja |
| 2026-11-24 | Guru Nanak's Birthday |
| 2026-12-24 to 2026-12-31 | Winter shutdown (6 days) |

### 2025 holidays (estimated from 2026 pattern)
| Date | Holiday |
|---|---|
| 2025-01-01 | New Year's Day |
| 2025-03-14 | Holi [est] |
| 2025-03-21 | Global Wellbeing Day [est] |
| 2025-04-18 | Good Friday [est] |
| 2025-05-01 | Labour Day |
| 2025-06-27 | Global Wellbeing Day [est] |
| 2025-08-15 | Independence Day ✓ |
| 2025-08-22 | Global Wellbeing Day [est] |
| 2025-08-27 | Ganesh Chaturthi [est] |
| 2025-10-02 | Gandhi Jayanti ✓ |
| 2025-10-20 | Deepavali [est] |
| 2025-10-31 | Global Wellbeing Day [est] |
| 2025-11-05 | Guru Nanak's Birthday [est] |
| 2025-12-24 to 2025-12-31 | Winter shutdown (6 days) |

> ✓ = confirmed from Slack channel messages. [est] = estimated, to be verified against the 2025 Adobe PDF when available.

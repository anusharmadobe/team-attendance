#!/usr/bin/env python3
"""
Attendance Report Generator
Produces formatted Slack messages for any time period.

Usage:
  python3 generate_report.py week          # current working week
  python3 generate_report.py month         # current month
  python3 generate_report.py last_month    # previous calendar month
  python3 generate_report.py year          # current year to date
  python3 generate_report.py last_year     # previous full year
  python3 generate_report.py 2026-05-01 2026-05-31   # custom range

To send the output to Slack DM, pipe to send_slack.py:
  python3 generate_report.py month | python3 send_slack.py U_ID
"""

import json
import sys
from datetime import date, timedelta
from pathlib import Path

DATA_PATH = Path(__file__).parent / "data" / "attendance.json"
OFFICE_TARGET = 60  # 3 days/week mandate

# ── Load data ──────────────────────────────────────────────────────────────
def load():
    return json.loads(DATA_PATH.read_text())

# ── Period helpers ─────────────────────────────────────────────────────────
def parse_period(args):
    today = date.today()
    if not args or args[0] == "week":
        dow = (today.weekday())
        mon = today - timedelta(days=dow)
        fri = mon + timedelta(days=4)
        return mon.isoformat(), min(fri, today).isoformat(), f"Week of {mon.strftime('%b %d')}–{fri.strftime('%b %d, %Y')}"
    elif args[0] == "month":
        first = date(today.year, today.month, 1)
        return first.isoformat(), today.isoformat(), f"{today.strftime('%B %Y')}"
    elif args[0] == "last_week":
        # Previous Mon–Fri (the week that just finished)
        dow      = today.weekday()          # 0=Mon … 6=Sun
        last_fri = today - timedelta(days=dow + 3)
        last_mon = last_fri - timedelta(days=4)
        return last_mon.isoformat(), last_fri.isoformat(), \
               f"Week of {last_mon.strftime('%b %d')}–{last_fri.strftime('%b %d, %Y')}"
    elif args[0] == "last_month":
        if today.month == 1:
            ym, yy = 12, today.year - 1
        else:
            ym, yy = today.month - 1, today.year
        first = date(yy, ym, 1)
        import calendar
        last = date(yy, ym, calendar.monthrange(yy, ym)[1])
        return first.isoformat(), last.isoformat(), f"{first.strftime('%B %Y')}"
    elif args[0] == "year":
        return f"{today.year}-01-01", today.isoformat(), f"{today.year} (YTD)"
    elif args[0] == "last_year":
        y = today.year - 1
        return f"{y}-01-01", f"{y}-12-31", f"{y} (Full Year)"
    elif len(args) >= 2:
        return args[0], args[1], f"{args[0]} to {args[1]}"
    else:
        raise ValueError(f"Unknown period: {args[0]}")

# ── Stats computation ──────────────────────────────────────────────────────
def compute_stats(att, members, from_date, to_date):
    days = sorted(d for d in att if from_date <= d <= to_date)
    totals = {"office": 0, "wfh": 0, "sick": 0, "leave": 0, "no_info": 0}
    by_person = {}

    for d in days:
        day_data = att.get(d, {})
        for uid, m in members.items():
            rec = day_data.get(uid)
            if not rec:
                continue
            s = rec["status"]
            totals[s] = totals.get(s, 0) + 1
            if uid not in by_person:
                by_person[uid] = {"office": 0, "wfh": 0, "sick": 0,
                                  "leave": 0, "no_info": 0, "days": 0}
            by_person[uid][s] += 1
            by_person[uid]["days"] += 1

    total_pd = sum(totals.values())
    rep = total_pd - totals["no_info"]
    off_pct = round(totals["office"] / rep * 100) if rep else 0

    return {
        "cal_days": len(days),
        "total_pd": total_pd,
        "rep": rep,
        "totals": totals,
        "off_pct": off_pct,
        "by_person": by_person,
    }

# ── Helpers ────────────────────────────────────────────────────────────────
def bar(pct, width=10):
    """Unicode filled/empty block bar (0-100)."""
    filled = round(min(pct, 100) / 100 * width)
    return "█" * filled + "░" * (width - filled)

def status_dot(pct, target=OFFICE_TARGET):
    if pct >= target:          return "🟢"
    elif pct >= target * 0.5:  return "🟡"
    else:                       return "🔴"

# ── Executive-format Slack message ─────────────────────────────────────────
def format_slack(label, stats, members):
    t      = stats["totals"]
    rep    = stats["rep"] or 1
    total  = stats["total_pd"] or 1
    off_p  = stats["off_pct"]
    wfh_p  = round(t["wfh"] / rep * 100)
    away_p = round((t["sick"] + t["leave"]) / rep * 100)
    ni_p   = round(t["no_info"] / total * 100)

    # Build ranked per-person list
    ranked = []
    for uid, m in members.items():
        bp    = stats["by_person"].get(uid, {})
        rep_p = bp.get("office",0)+bp.get("wfh",0)+bp.get("sick",0)+bp.get("leave",0)
        days_p = bp.get("days", 0)
        op    = round(bp.get("office", 0) / rep_p * 100) if rep_p else 0
        pr    = round(rep_p / days_p * 100)               if days_p else 0
        ranked.append(dict(name=m["name"].split()[0], uid=uid, bp=bp,
                           rep=rep_p, days=days_p, op=op, pr=pr))
    ranked.sort(key=lambda x: x["op"], reverse=True)

    best  = ranked[0]  if ranked else None
    worst = ranked[-1] if ranked else None

    # ── Highlights & Lowlights  (no *bold* markers — rendered inside code block) ──
    hi, lo = [], []
    if off_p >= OFFICE_TARGET:
        hi.append(f"Team office attendance  {off_p}%  —  above 60% mandate 🎯")
    else:
        lo.append(f"Team office attendance  {off_p}%  —  {OFFICE_TARGET - off_p} pts below 60% mandate")

    if best and best["rep"] > 2:
        tag = "on target ✅" if best["op"] >= OFFICE_TARGET else "highest on team"
        hi.append(f"{best['name']}  {best['op']}%  —  {tag} in office attendance")

    if worst and worst["rep"] > 2 and worst["op"] < OFFICE_TARGET * 0.6:
        lo.append(f"{worst['name']}  {worst['op']}%  —  lowest on team, needs attention")

    if ni_p >= 50:
        lo.append(f"No status  {ni_p}%  —  data confidence is low")
    elif ni_p >= 30:
        lo.append(f"No status  {ni_p}%  —  encourage daily updates")

    # ── Compose ────────────────────────────────────────────────────────────
    SEP  = "━" * 34
    RULE = "─" * 44
    lines = [
        f"**AEM Forms India PM & Content Team Attendance  |  {label}  ·  {stats['cal_days']} working days**  |  Generated {date.today().strftime('%B %d %Y')}",
        SEP,
    ]

    # Highlights — own bold title + code block (icons small, like metrics)
    if hi:
        lines += ["🔷  **Highlights**", "```"]
        for h in hi:
            lines.append(f"  ✅  {h}")
        lines += ["```", SEP]

    # Lowlights — own bold title + code block
    if lo:
        lines += ["🔻  **Lowlights / Action Needed**", "```"]
        for l in lo:
            lines.append(f"  🔴  {l}")
        lines += ["```", SEP]

    # Team Metrics block
    lines += [
        "📈  **Team Metrics**",
        "```",
        f"  🏢 Office     {off_p:>3}%  {bar(off_p)}  {t['office']} person-days",
        f"  🏠 WFH        {wfh_p:>3}%  {bar(wfh_p)}  {t['wfh']} person-days",
        f"  🏥 Sick/PTO   {away_p:>3}%  {bar(away_p)}  {t['sick'] + t['leave']} person-days",
        f"  ❓ No status  {ni_p:>3}%  {bar(ni_p)}  {t['no_info']} person-days",
        "```",
        SEP,
    ]

    # Individual Office Attendance — legend tucked inside code block
    nw = max((len(r["name"]) for r in ranked), default=8)
    lines += ["👥  **Individual Office Attendance**", "```"]
    for r in ranked:
        dot  = status_dot(r["op"])
        b    = bar(r["op"])
        flag = " 🎯" if r["op"] >= OFFICE_TARGET else ""
        cov  = f"  [{r['pr']}% posted]" if r["pr"] < 70 else ""
        lines.append(f"  {dot}  {r['name']:<{nw}}  {r['op']:>3}%  {b}{flag}{cov}")
    tgt_indent = " " * (nw + 11)
    lines += [
        f"  {tgt_indent}{'─' * round(OFFICE_TARGET / 10)}┤ 60% target",
        f"  {RULE}",
        f"  🟢 At/above target   🟡 Near target   🔴 Needs attention",
        "```",
        SEP,
    ]
    return "\n".join(lines)


def main():
    args = sys.argv[1:]
    data = load()
    att = data["attendance"]
    members = data["team_members"]

    from_date, to_date, label = parse_period(args)
    stats = compute_stats(att, members, from_date, to_date)
    print(format_slack(label, stats, members))


if __name__ == "__main__":
    main()

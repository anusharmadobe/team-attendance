# Team Attendance Tool — Comprehensive Critique

**Reviewed:** 2026-06-06  
**Scope:** Dashboard (all 5 tabs), automated Slack reports, automation pipeline  
**Perspectives:** Individual contributor, Direct manager, Skip-level manager, UX/Design

---

## 1. Individual Team Member Perspective

### What they see and experience

A team member opens the dashboard (linked from the Slack channel or bookmarked directly). They can:
- See their own office % compared to everyone else (Annual, Monthly, Weekly bars)
- See a public ranking in the Slack report ("Anurag 55% — leads team in office attendance")
- Drill into any week via the Weekly tab to see day-by-day status for the whole team
- Check the Daily Log filtered to their own name

### What's good

- **Transparency is fair:** Everyone's data is visible to everyone. There are no hidden tiers. A team member knows exactly what their manager sees.
- **No Assumptions principle is respected:** "No Info" is surfaced as a data gap, not as an absence. This is meaningful — someone who forgot to post on a day they were in office isn't penalised.
- **Easy to understand:** The color legend (green = office, blue = WFH, red = sick, amber = leave, grey = no info) is consistent throughout.

### Pain points

**1. No self-view / privacy mode**  
There is no way to see only your own data without seeing everyone else's. If a team member wants to check "did my status get recorded correctly last Tuesday?" they have to look at the full team view. More significantly, a new joiner or someone going through a difficult personal period (reflected in their sick/leave patterns) has no ability to review just their own history privately.

**Recommendation:** Add a "My view" toggle or a Member dropdown on the Home tab that collapses the view to just the logged-in person. (For now, the Member dropdown on Monthly/Weekly is a partial workaround — but it's not discoverable.)

**2. No ability to self-correct**  
If a team member was at the office on a day that shows "No Info" (because they forgot to post), they have no way to flag this. Only the manager (who has access to `seed_attendance.py`) can correct it. This creates a power asymmetry where data errors always need manager intervention.

**Recommendation:** A lightweight "flag a correction" mechanism — even just a pinned Slack message format like "Correction: I was at office on 2026-06-01" that the manager processes weekly.

**3. Public ranking in Slack reports can be demoralising**  
The Individual Office Attendance section in the weekly/monthly Slack report ranks people from highest to lowest office %. The person at the bottom of that list (currently Chris at 29% YTD) sees their name at the bottom, in a channel that may be visible to others. For people with legitimate reasons for lower office attendance (Bangalore location, travel, family obligations), this public ranking can feel like a scarlet letter without context.

**Recommendation:** Remove the ranked order from the public Slack report (or show alphabetical order). Keep ranking in a private manager-only report. Alternatively, add a brief contextual note if a person has a structural reason for lower office % (e.g. remote worker).

**4. Historical data going back 18 months without notice**  
The Daily Log defaults to showing data from 2025-01-01. A team member who joined in mid-2025 might be surprised to see how much historical data about them exists. There is no explanation of data retention policy anywhere in the UI.

**Recommendation:** Add a short "About this data" tooltip or footer: "Data collected from Slack posts since January 2025. Only the team manager can correct entries."

---

## 2. Direct Manager Perspective (Anurag Sharma)

### What the manager gets

- Weekly automated Slack reports (no manual effort)
- Trend chart showing office % month-by-month for 2026
- Monthly matrix to spot patterns (e.g. "Khushwant has no data for May–Jun")
- Individual bars ranked by office % in Annual view
- Day-by-day breakdown in Weekly view for any week

### What's good

- **Automation removes the toil:** Before this tool, generating a weekly attendance summary required manually reading the Slack channel, counting days, and formatting a message. That's now fully automated.
- **The monthly matrix is the standout feature:** Seeing each person's office % per month in a grid (color-coded green/amber/grey) is the most actionable view for a manager. It immediately shows who has been consistently low and whether it's improving.
- **Trend line on Home tab:** Seeing Jan → Jun 2026 in one view, with the 60% target dashed line, makes the management conversation concrete. "We're below target — here's the trend."
- **Highlights / Lowlights in Slack report:** The auto-generated insight narrative saves writing time and keeps the report from being just raw numbers.

### Pain points

**1. No alert when someone hasn't posted in N days**  
The tool tracks `no_info` but never escalates it. If Khushwant hasn't posted anything for 3 weeks straight, the tool will show grey cells — but there is no proactive notification to the manager. The manager has to log in and notice the grey pattern.

**Recommendation:** Add a rule to the weekly Slack report: "⚠️ The following members have not posted status for 5+ consecutive working days: Khushwant Singh." This makes it actionable rather than just visible.

**2. Data is only as fresh as the last seed run**  
The `seed_attendance.py` script requires the manager to manually add EVENTS entries. If the manager is busy or travelling, the data can lag by weeks. There's no indicator in the dashboard showing "this data is 14 days stale." The header shows "Updated Jun 6, 2026" — but that's when the JSON was last built, not necessarily when new data was added.

**Recommendation:** Add a "last data entry" date to the dashboard header, separate from the build date. Something like: "Data through Jun 5 · Built Jun 6." This makes staleness explicit.

**3. No export / download**  
There is no way to download the attendance data as a CSV or Excel file. If a manager needs to share attendance numbers with HR, put them into a performance review, or do ad-hoc analysis, they have to manually copy data from the dashboard.

**Recommendation:** Add a "Download CSV" button on the Daily Log tab (easiest to implement — it's already a flat table). A full data export button on Annual tab would also be valuable.

**4. No projection / forecast**  
The dashboard shows where the team is (45% YTD office) but not where it's headed. "At the current May–June rate of ~50%, the team will end the year at approximately 48% — still below the 60% target." That kind of projection would give the manager a sense of urgency (or confidence).

**Recommendation:** Add a simple projection to the Annual KPI area: "Projected year-end: X% (based on last 90 days)." A linear extrapolation is sufficient.

**5. The 53% No Status KPI demands investigation but provides no path**  
Annual tab shows "NO STATUS 53%" in grey. This is the dominant signal in the data — more than half of all person-days have no status. But clicking it does nothing. A manager who sees this wants to immediately know: *who* is driving this? Is it one person or all five? Which months were worst?

**Recommendation:** Make the "NO STATUS" KPI card clickable. Clicking it should filter the dashboard (or jump to the Daily Log with Status=No Info) to show the breakdown.

---

## 3. Skip-Level Manager Perspective

### Context

The skip-level manager (Anurag's manager) sees the team from an organisational compliance and performance angle. They are not in the daily Slack channel. They receive whatever is shared with them — at present, nothing automatically, unless they are in `C08T43UHK9D`.

### What they need

- A simple answer: "Is this team meeting the 60% return-to-office mandate?"
- Trend: improving or declining?
- Outliers: anyone at risk of being below threshold long-term?
- Data confidence: how reliable are these numbers?
- Comparison: how does this team compare to others?

### What they get today

- The live dashboard (if linked): moderate — it has the numbers, but requires interpretation
- The Slack report (if in the channel): good — the narrative highlights / lowlights do the interpretation work
- Nothing proactively: the skip-level has to know to look for this tool

### Pain points

**1. No compliance verdict**  
The dashboard shows 45% YTD office attendance against a 60% target — but never says "BELOW TARGET" in clear terms. The KPI card shows "45%" in a green-ish color. The trend chart has a dashed 60% line. A skip-level manager who glances at this for 30 seconds might not register that the team is 15 points below target.

**Recommendation:** Add an explicit compliance badge to the Annual KPI area:
```
Office 45%  🔴 Below 60% target  (-15 pts)
```
Color the number red when below 60%, amber when 50–59%, green when ≥ 60%. This is the single most important data point for a compliance conversation.

**2. No rollup view across teams**  
The tool tracks one team only. A skip-level manager with 3–4 teams reporting to them cannot use this tool to compare attendance across their portfolio. They'd need to look at 3–4 separate dashboards.

**Recommendation (medium-term):** Add a "multi-team" mode or at minimum allow the dashboard to be parameterised by a JSON URL, so different team instances can be deployed and compared.

**3. Data confidence is hidden, not front-and-center**  
The 53% "No Status" figure is tucked into a KPI card. For a skip-level manager trusting these numbers in a compliance conversation, the appropriate response is: "If 53% of days have unknown status, how confident are we that the 45% office figure is real?" This question is not answered anywhere in the UI.

**Recommendation:** Add a data confidence indicator to the Annual view:
```
📊 Data confidence: Moderate (47% of person-days have reported status)
Tip: Low no-status months (e.g. May 2026) give more reliable office %)
```

**4. No audit trail or governance statement**  
For any compliance use, the skip-level manager needs to know: who built this? Is this official? Is it sourced from HR systems? The dashboard has no "About" or governance statement.

**Recommendation:** Add a footer or "About" modal: "Built by Anurag Sharma. Data sourced from Slack channel posts by team members. Not an official Adobe HR system. For discrepancies, contact anusharm@adobe.com."

**5. Report delivery is passive**  
The Slack report goes to `C08T43UHK9D` — a channel the skip-level may not be in. There is no email summary, no Outlook calendar block, no SharePoint page. The tool only reaches people who are in that specific channel.

**Recommendation (near-term):** Share the dashboard link (`https://anusharmadobe.github.io/team-attendance/`) proactively with your skip-level manager. Consider adding them to `C08T43UHK9D` or forwarding the monthly Slack report via DM.

---

## 4. Design / UX Perspective

### Overall impression

The dashboard is clean, functional, and loads fast. The single-file architecture (no dependencies, no build tools) is a smart choice for a small team tool. The Slack reports are well-formatted and readable. However, several design decisions reduce effectiveness — particularly around communicating target compliance, handling data gaps, and mobile usability.

---

### 4.1 Annual Tab — KPI Grid Layout

**Issue:** 5 KPI cards render as 3 + 2 across two rows on a standard desktop viewport. The orphaned row of 2 cards (SICK/PTO and NO STATUS) looks unfinished. The layout implies equal weight to all 5 metrics, but NO STATUS at 53% is arguably the most important signal.

**Recommendation:**
- Use a consistent 3-column or 4-column grid, or group KPIs semantically:
  ```
  [AT OFFICE 45%]  [WFH 41%]  [SICK/PTO 13%]  [LEAVE 4%]
  [NO STATUS 53%  ⚠ data confidence gap]
  ```
- Or: make NO STATUS full-width with a warning treatment, so it reads as a footnote on data quality rather than a peer metric.

---

### 4.2 Color Encoding Does Not Communicate Target

**Issue:** All individual office attendance bars (Annual, Monthly, Weekly) are rendered in the same flat green — whether the person is at 29% (Chris) or 100% (Anurag in June). Green communicates "good," but 29% is not good relative to a 60% target.

**Current state:**
```
Anurag    ████████████████████████████  55%  (green)
Chris     █████████████                29%  (green)
```

**Recommendation:** Apply target-aware coloring:
- ≥ 60%: green (at/above target)
- 50–59%: amber (near target)
- < 50%: red (needs attention)

This is the most impactful single design change. It would make the "Individual office attendance" chart immediately actionable without reading any numbers.

---

### 4.3 "No Status" KPI Shown Without Urgency

**Issue:** "NO STATUS 53%" is displayed in grey — the same visual weight and color as any other metric. There is no warning, no tooltip, no explanation of what 53% no-status means for data reliability.

**Recommendation:** Apply a warning treatment:
```
NO STATUS ⚠  53%
276 person-days — data may be understated
```
Add a tooltip: "53% of person-days have no status posted. Office % is calculated only from days with reported status, so actual office attendance may differ."

---

### 4.4 Home Tab — Target Line Clipped

**Issue:** The trend chart's 60% target dashed line label ("60'") is clipped at the right edge of the chart. The label is partially visible but looks like a rendering error.

**Recommendation:** Move the target line label to the left side of the chart, or to a legend below the chart axis. Ensure it reads "60% target" not just "60'."

---

### 4.5 Monday No-Show Pattern — Not Surfaced

**Issue:** Looking at the Weekly tab for 2026-06-01 → 06-05, Monday June 1st shows "No Info" for all 5 team members. This is a visible behavioral pattern — the team appears to post status less frequently on Mondays. The dashboard does not call this out or trend it.

**Recommendation (medium-term):** On the Home tab Key Insights, add a pattern detection note: "📌 Monday no-status rate is 3× higher than other weekdays — consider a Monday check-in reminder."

---

### 4.6 Monthly Tab — Missing Member Not Displayed

**Issue:** Khushwant Singh has no attendance data for June 2026 (all No Info) and is not shown in the Monthly tab's "Individual office attendance" bar chart. The four visible bars are Anurag, Utkarsha, Chris, and Ruchita. Khushwant is absent from the chart, giving the impression they're not on the team — not that they have no data.

**Recommendation:** Show all active team members in all bar charts, even if their value is 0% or they have only No Info entries. A grey bar with "0%" would communicate "no data" without hiding the person.

---

### 4.7 Weekly Tab — "Copy Summary" Button Has No Tooltip

**Issue:** The "↓ Copy Summary" button on the Weekly tab has no tooltip, no placeholder for what gets copied, and no feedback after clicking. A first-time user doesn't know if it copies Markdown, plain text, or a table.

**Recommendation:**
- Add a tooltip: "Copies a plain-text summary of this week's attendance to your clipboard"
- Add a transient confirmation: "✓ Copied to clipboard" (disappears after 2 seconds)

---

### 4.8 Home Tab — Scrolling Length and Information Architecture

**Issue:** The Home tab is very long:
1. Today banner
2. Executive Summary (KPIs + warnings)
3. Trend chart (large)
4. Team Members section (often below the fold)

The Team Members section (individual member cards with drill-down) is rarely seen because users scroll to the chart and stop. It's the richest feature on the Home tab but has the lowest visibility.

**Recommendation:**
- Move the Team Members section above the trend chart, or collapse the trend chart to half-height by default with an "Expand" option.
- Alternatively, make the team member cards the primary hero of the Home tab and move the trend chart to the Annual tab.

---

### 4.9 Slack Report — Khushwant's Missing Data Not Called Out

**Issue:** The current year Slack report shows Khushwant at 39% — below target. However, the no_info data for May–June suggests the number is understated (his actual office % may be higher if he attended but didn't post). The Lowlights section flags "Khushwant 39% — needs attention" but gives no context that this may be a data quality issue.

**Recommendation:** When a person has >40% no_info for the period being reported, add a qualification: "⚠ Note: Khushwant has 65% no-status days — office % may be understated."

---

### 4.10 Mobile Responsiveness

**Issue:** The Weekly tab's 5-column day table (MEMBER | MON | TUE | WED | THU | FRI) will overflow or compress to illegibility on a phone screen. Given the tool is sent via Slack (primarily a mobile app), team members who tap the dashboard link on their phone will see a broken table.

**Recommendation:**
- For mobile viewports, collapse the weekly table to a card-per-person layout showing all 5 days vertically.
- Or add a `meta viewport` tag and simple responsive CSS to at minimum allow horizontal scrolling with `overflow-x: auto` on the table container.

---

## 5. Summary Scorecard

| Dimension | Rating | Key Issue |
|---|---|---|
| **Data accuracy** | ★★★★☆ | Manual curation is thorough; no-info is handled correctly |
| **Manager utility** | ★★★★☆ | Monthly matrix + trend chart are excellent; missing alerts and export |
| **Individual UX** | ★★★☆☆ | No self-view, no correction path, public ranking is potentially demoralising |
| **Skip-level utility** | ★★★☆☆ | Good narrative but no compliance verdict, no rollup |
| **Visual design** | ★★★☆☆ | Clean but color encoding misses target communication |
| **Mobile** | ★★☆☆☆ | Weekly table breaks; no responsive layout |
| **Data governance** | ★★☆☆☆ | No retention policy, no About section, no correction path |
| **Automation** | ★★★★★ | Zero-touch weekly refresh + deploy is excellent |

---

## 6. Priority Fixes (Quick Wins)

| # | Fix | Effort | Impact |
|---|---|---|---|
| 1 | Color individual bars red/amber/green based on 60% target | Low | High — immediate visual compliance read |
| 2 | Color the office % KPI red when below target | Low | High — skip-level can read compliance at a glance |
| 3 | Add "↓ N days since last data entry" staleness indicator to header | Low | Medium — manager trust in data currency |
| 4 | Show Khushwant (and any no-data member) as grey bar rather than hiding them | Low | Medium — completeness impression |
| 5 | Add post-copy confirmation toast to "Copy Summary" button | Low | Low — polish |
| 6 | Fix the 60% target label clipping on the trend chart | Low | Low — polish |
| 7 | Add no-status qualification to Slack report when >40% no_info | Medium | High — trust in numbers |
| 8 | Make NO STATUS KPI card clickable → filter to no-info days | Medium | High — makes the metric actionable |
| 9 | Responsive CSS for the weekly table | Medium | High — mobile viewers |
| 10 | Add "About this data" footer or modal | Low | Medium — governance / trust |

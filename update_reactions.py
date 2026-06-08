#!/usr/bin/env python3
"""
update_reactions.py — ONE-TIME PATCH SCRIPT (DO NOT RE-RUN)
============================================================
This script was used once (Jun 2026 data audit) to backfill reaction data
for messages from Aug 2025 – Jun 2026. It contains HARDCODED reactions
captured at a point in time and will OVERWRITE current live reactions with
stale data if run again.

Reaction data is now kept current by the weekly scheduled task (Step 0b),
which calls slack_get_reactions via MCP for every team-member message and
every message with stored reactions. There is NO need to run this script.

If you genuinely need to re-patch a specific message, edit the REACTIONS dict
carefully and test on a copy of raw_messages.json first.

DANGER: Running this will silently corrupt reaction attribution for all 18 months.
"""
import sys
# Hard guard — abort unless the user explicitly passes --force
if "--force" not in sys.argv:
    print("❌  ABORTED: update_reactions.py is a one-time legacy patch script.")
    print("   Reactions are managed by the weekly scheduled task (Step 0b).")
    print("   Re-running this will OVERWRITE live reactions with stale hardcoded data.")
    print("   If you really need to run it, pass --force.")
    sys.exit(1)

import json, os

DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "raw_messages.json")

# Authoritative reaction data: {int_ts_str: [{name, count, users}]}
# Collected via slack_get_reactions for every +1moji / +1_sign status message.
REACTIONS = {
    # ── Aug 2025 ─────────────────────────────────────────────────────────────
    "1754283500": [{"name": "+1moji", "count": 1, "users": ["U03HRQ036BD"]}],
    "1755490740": [{"name": "+1moji", "count": 2, "users": ["U03HRQ036BD", "W010NNJV7S8"]}],
    "1755572298": [{"name": "+1moji", "count": 1, "users": ["W010NNJV7S8"]}],

    # ── Sep 2025 ─────────────────────────────────────────────────────────────
    "1757391266": [{"name": "+1moji", "count": 2, "users": ["U03HRQ036BD", "W4R4S9FS4"]}],
    "1758515094": [{"name": "+1moji", "count": 1, "users": ["W010NNJV7S8"]}],
    "1758689172": [{"name": "+1moji", "count": 2, "users": ["WAM5KDYBZ", "W010NNJV7S8"]}],

    # ── Oct 2025 ─────────────────────────────────────────────────────────────
    "1759729963": [{"name": "+1moji", "count": 2, "users": ["W010NNJV7S8", "WAM5KDYBZ"]}],
    "1759812549": [{"name": "+1moji", "count": 4, "users": ["W010NNJV7S8", "U03HRQ036BD", "U0900H3NUUT", "W4R4S9FS4"]}],
    "1759895872": [{"name": "+1moji", "count": 3, "users": ["W010NNJV7S8", "U08HVLWG1UM", "W4R4S9FS4"]}],
    "1759979031": [{"name": "+1moji", "count": 3, "users": ["U08HVLWG1UM", "U0900H3NUUT", "W4R4S9FS4"]}],
    "1760509577": [{"name": "+1moji", "count": 2, "users": ["W010NNJV7S8", "WAM5KDYBZ"]}],
    "1760940292": [{"name": "+1moji", "count": 4, "users": ["W010NNJV7S8", "U03HRQ036BD", "WAM5KDYBZ", "U08HVLWG1UM"]}],
    "1761198819": [{"name": "+1moji", "count": 1, "users": ["WAM5KDYBZ"]}],
    "1761275240": [{"name": "+1moji", "count": 2, "users": ["U03HRQ036BD", "U0900H3NUUT"]}],
    "1761539840": [{"name": "+1moji", "count": 2, "users": ["U08HVLWG1UM", "W4R4S9FS4"]}],
    "1761625297": [{"name": "+1moji", "count": 2, "users": ["U08HVLWG1UM", "U0900H3NUUT"]}],
    "1761711587": [{"name": "+1moji", "count": 4, "users": ["U08HVLWG1UM", "U03HRQ036BD", "WAM5KDYBZ", "W4R4S9FS4"]}],
    "1761799135": [{"name": "+1moji", "count": 2, "users": ["U0900H3NUUT", "W4R4S9FS4"]}],
    "1761881915": [{"name": "+1moji", "count": 2, "users": ["U0900H3NUUT", "WAM5KDYBZ"]}],
    "1761898063": [{"name": "+1moji", "count": 1, "users": ["W010NNJV7S8"]}],

    # ── Nov 2025 ─────────────────────────────────────────────────────────────
    "1762142565": [{"name": "+1moji", "count": 2, "users": ["U0900H3NUUT", "W010NNJV7S8"]}],
    "1762231743": [{"name": "+1moji", "count": 3, "users": ["U08HVLWG1UM", "W4R4S9FS4", "U03HRQ036BD"]}],
    "1762400075": [{"name": "+1moji", "count": 1, "users": ["W010NNJV7S8"]}],
    "1762486139": [{"name": "+1moji", "count": 2, "users": ["U0900H3NUUT", "WAM5KDYBZ"]}],
    "1762739575": [{"name": "+1moji", "count": 1, "users": ["U0900H3NUUT"]}],
    "1762750041": [{"name": "+1moji", "count": 2, "users": ["W010NNJV7S8", "WAM5KDYBZ"]}],
    "1762835383": [{"name": "+1moji", "count": 3, "users": ["U08HVLWG1UM", "U03HRQ036BD", "WAM5KDYBZ"]}],
    "1762915586": [{"name": "+1moji", "count": 4, "users": ["WAM5KDYBZ", "U08HVLWG1UM", "W010NNJV7S8", "U0900H3NUUT"]}],
    "1763009064": [{"name": "+1moji", "count": 3, "users": ["U03HRQ036BD", "W4R4S9FS4", "WAM5KDYBZ"]}],
    "1763085192": [{"name": "+1moji", "count": 2, "users": ["U0900H3NUUT", "W4R4S9FS4"]}],
    "1763439694": [{"name": "+1moji", "count": 2, "users": ["U08HVLWG1UM", "U0900H3NUUT"]}],
    "1763522636": [{"name": "+1moji", "count": 1, "users": ["W4R4S9FS4"]}],
    "1763606758": [{"name": "+1moji", "count": 3, "users": ["U08HVLWG1UM", "U0900H3NUUT", "U03HRQ036BD"]}],
    "1763696467": [{"name": "+1moji", "count": 2, "users": ["U0900H3NUUT", "U03HRQ036BD"]}],
    "1763956958": [{"name": "+1moji", "count": 2, "users": ["U0900H3NUUT", "U03HRQ036BD"]}],
    "1764043749": [{"name": "+1moji", "count": 3, "users": ["U08HVLWG1UM", "U0900H3NUUT", "WAM5KDYBZ"]}],
    "1764131307": [{"name": "+1moji", "count": 3, "users": ["WAM5KDYBZ", "U0900H3NUUT", "W4R4S9FS4"]}],
    "1764219520": [{"name": "+1moji", "count": 3, "users": ["W4R4S9FS4", "U03HRQ036BD", "U0900H3NUUT"]}],
    "1764300158": [{"name": "+1moji", "count": 2, "users": ["U0900H3NUUT", "U08HVLWG1UM"]}],

    # ── Dec 2025 ─────────────────────────────────────────────────────────────
    "1764559292": [{"name": "+1moji", "count": 1, "users": ["W010NNJV7S8"]}],
    "1764655650": [{"name": "+1moji", "count": 1, "users": ["W010NNJV7S8"]}],
    "1764735998": [{"name": "+1moji", "count": 5, "users": ["U0900H3NUUT", "W4R4S9FS4", "WAM5KDYBZ", "U03HRQ036BD", "W010NNJV7S8"]}],
    "1764901144": [{"name": "+1moji", "count": 2, "users": ["U0900H3NUUT", "W4R4S9FS4"]}],
    "1765168540": [{"name": "+1moji", "count": 3, "users": ["U03HRQ036BD", "WAM5KDYBZ", "W010NNJV7S8"]}],
    "1765255664": [{"name": "+1moji", "count": 1, "users": ["W010NNJV7S8"]}],
    "1765256100": [{"name": "+1moji", "count": 1, "users": ["U03HRQ036BD"]}],
    "1765343837": [{"name": "+1moji", "count": 1, "users": ["U0900H3NUUT"]}],
    "1765427864": [{"name": "+1moji", "count": 1, "users": ["W4R4S9FS4"]}],
    "1765512843": [{"name": "+1moji", "count": 1, "users": ["U03HRQ036BD"]}],
    "1765863445": [{"name": "+1moji", "count": 2, "users": ["U03HRQ036BD", "WAM5KDYBZ"]}],
    "1765944493": [{"name": "+1moji", "count": 1, "users": ["U03HRQ036BD"]}],
    "1766377715": [{"name": "+1moji", "count": 2, "users": ["U0900H3NUUT", "W4R4S9FS4"]}],
    "1766379599": [{"name": "+1moji", "count": 1, "users": ["W010NNJV7S8"]}],
    "1766457636": [{"name": "+1moji", "count": 3, "users": ["U03HRQ036BD", "U08HVLWG1UM", "W010NNJV7S8"]}],
    "1766469023": [{"name": "+1moji", "count": 1, "users": ["W4R4S9FS4"]}],

    # ── Jan 2026 (Jan 5–13, from prior session) ───────────────────────────────
    "1767586314": [{"name": "+1moji", "count": 4, "users": ["W010NNJV7S8", "U0900H3NUUT", "U08HVLWG1UM", "WAM5KDYBZ"]}],
    "1767679231": [{"name": "+1moji", "count": 2, "users": ["W4R4S9FS4", "U0900H3NUUT"]}],
    "1767852899": [{"name": "+1moji", "count": 1, "users": ["W4R4S9FS4"]}],
    "1767853421": [{"name": "+1_sign", "count": 1, "users": ["W010NNJV7S8"]}],
    "1767928813": [{"name": "+1moji", "count": 4, "users": ["U0900H3NUUT", "U03HRQ036BD", "W4R4S9FS4", "W010NNJV7S8"]}],
    "1768190976": [{"name": "+1moji", "count": 2, "users": ["U08HVLWG1UM", "W010NNJV7S8"]}],
    "1768198151": [{"name": "+1moji", "count": 2, "users": ["U0900H3NUUT", "WAM5KDYBZ"]}],
    "1768277696": [{"name": "+1moji", "count": 2, "users": ["U0900H3NUUT", "W4R4S9FS4"]}],

    # ── Jan 2026 (Jan 14–30, freshly fetched) ────────────────────────────────
    "1768364273": [{"name": "+1moji", "count": 4, "users": ["U08HVLWG1UM", "U0900H3NUUT", "W4R4S9FS4", "W010NNJV7S8"]}],
    "1768444461": [{"name": "+1moji", "count": 1, "users": ["U08HVLWG1UM"]}],
    "1768534460": [{"name": "+1moji", "count": 2, "users": ["U0900H3NUUT", "W010NNJV7S8"]}],
    "1768878543": [{"name": "+1moji", "count": 1, "users": ["U0900H3NUUT"]}],
    "1768971998": [{"name": "+1moji", "count": 3, "users": ["WAM5KDYBZ", "U0900H3NUUT", "U03HRQ036BD"]}],
    "1769057716": [{"name": "+1moji", "count": 3, "users": ["W4R4S9FS4", "U0900H3NUUT", "WAM5KDYBZ"]}],
    "1769134571": [{"name": "+1moji", "count": 1, "users": ["U08HVLWG1UM"]}],
    "1769144136": [{"name": "+1moji", "count": 1, "users": ["U0900H3NUUT"]}],
    "1769571488": [{"name": "+1_sign", "count": 2, "users": ["WAM5KDYBZ", "U0900H3NUUT"]}],
    "1769663575": [{"name": "+1_sign", "count": 3, "users": ["W010NNJV7S8", "WAM5KDYBZ", "U03HRQ036BD"]}],
    "1769742875": [{"name": "+1moji", "count": 1, "users": ["U08HVLWG1UM"]}],
    "1769749201": [{"name": "+1_sign", "count": 1, "users": ["W010NNJV7S8"]}],

    # ── Feb 2026 ──────────────────────────────────────────────────────────────
    "1770003268": [{"name": "+1_sign", "count": 2, "users": ["W010NNJV7S8", "U0900H3NUUT"]}],
    "1770088537": [{"name": "+1moji", "count": 3, "users": ["U03HRQ036BD", "U0900H3NUUT", "W4R4S9FS4"]}],
    "1770175618": [{"name": "+1_sign", "count": 1, "users": ["W010NNJV7S8"]}],
    "1770182162": [{"name": "+1_sign", "count": 1, "users": ["WAM5KDYBZ"]}],
    "1770264056": [{"name": "+1moji", "count": 3, "users": ["W4R4S9FS4", "WAM5KDYBZ", "W010NNJV7S8"]}],
    "1770347906": [{"name": "+1moji", "count": 1, "users": ["U08HVLWG1UM"]}],
    "1770351843": [{"name": "+1_sign", "count": 2, "users": ["W010NNJV7S8", "WAM5KDYBZ"]}],
    "1770612560": [{"name": "+1moji", "count": 3, "users": ["U0900H3NUUT", "U03HRQ036BD", "WAM5KDYBZ"]}],
    "1770689759": [{"name": "+1_sign", "count": 1, "users": ["W010NNJV7S8"]}],
    "1770692971": [{"name": "+1moji", "count": 2, "users": ["U08HVLWG1UM", "W4R4S9FS4"]}],
    "1770786194": [{"name": "+1_sign", "count": 3, "users": ["W010NNJV7S8", "U03HRQ036BD", "U0900H3NUUT"]}],
    "1770869750": [{"name": "+1moji", "count": 3, "users": ["U08HVLWG1UM", "W4R4S9FS4", "WAM5KDYBZ"]}],
    "1770957482": [{"name": "+1moji", "count": 2, "users": ["U08HVLWG1UM", "WAM5KDYBZ"]}],
    "1771213199": [{"name": "+1moji", "count": 3, "users": ["U08HVLWG1UM", "U0900H3NUUT", "WAM5KDYBZ"]}],
    "1771300919": [{"name": "+1moji", "count": 2, "users": ["U03HRQ036BD", "W4R4S9FS4"]}],
    "1771388038": [{"name": "+1moji", "count": 2, "users": ["U08HVLWG1UM", "W010NNJV7S8"]}],
    "1771470323": [{"name": "+1moji", "count": 3, "users": ["U08HVLWG1UM", "W4R4S9FS4", "U0900H3NUUT"]}],
    "1771565500": [{"name": "+1_sign", "count": 2, "users": ["W010NNJV7S8", "W4R4S9FS4"]}],
    "1771817857": [{"name": "+1moji", "count": 4, "users": ["U08HVLWG1UM", "W4R4S9FS4", "U0900H3NUUT", "WAM5KDYBZ"]}],
    "1771903005": [{"name": "+1moji", "count": 3, "users": ["U0900H3NUUT", "U08HVLWG1UM", "W4R4S9FS4"]}],
    "1771985955": [{"name": "+1moji", "count": 1, "users": ["U08HVLWG1UM"]}],
    "1771991303": [{"name": "+1_sign", "count": 2, "users": ["W010NNJV7S8", "W4R4S9FS4"]}],
    "1772078955": [{"name": "+1moji", "count": 1, "users": ["U0900H3NUUT"]}],
    "1772165297": [{"name": "+1moji", "count": 3, "users": ["U03HRQ036BD", "U0900H3NUUT", "W4R4S9FS4"]}],

    # ── Mar 2026 ──────────────────────────────────────────────────────────────
    "1772422864": [{"name": "+1moji", "count": 1, "users": ["U08HVLWG1UM"]}],
    "1772426603": [{"name": "+1moji", "count": 1, "users": ["U08HVLWG1UM"]}],
    "1772508533": [{"name": "+1_sign", "count": 2, "users": ["W010NNJV7S8", "W4R4S9FS4"]}],
    "1772680081": [{"name": "+1_sign", "count": 2, "users": ["W010NNJV7S8", "W4R4S9FS4"]}],
    "1772770737": [{"name": "+1_sign", "count": 2, "users": ["W010NNJV7S8", "W4R4S9FS4"]}],
    "1773026053": [{"name": "+1moji", "count": 1, "users": ["U0900H3NUUT"]}],
    "1773116657": [{"name": "+1moji", "count": 2, "users": ["U0900H3NUUT", "U08HVLWG1UM"]}],
    "1773197386": [{"name": "+1moji", "count": 3, "users": ["U03HRQ036BD", "U08HVLWG1UM", "WAM5KDYBZ"]}],
    "1773283522": [{"name": "+1moji", "count": 2, "users": ["U0900H3NUUT", "W4R4S9FS4"]}],
    "1773376997": [{"name": "+1moji", "count": 1, "users": ["U0900H3NUUT"]}],
    "1773637234": [{"name": "+1moji", "count": 3, "users": ["U08HVLWG1UM", "WAM5KDYBZ", "W4R4S9FS4"]}],
    "1773809619": [{"name": "+1_sign", "count": 1, "users": ["W010NNJV7S8"]}],
    "1774239428": [{"name": "+1moji", "count": 3, "users": ["U0900H3NUUT", "U08HVLWG1UM", "WAM5KDYBZ"]}],
    "1774324061": [{"name": "+1moji", "count": 2, "users": ["U0900H3NUUT", "U08HVLWG1UM"]}],
    "1774331618": [{"name": "+1_sign", "count": 1, "users": ["WAM5KDYBZ"]}],
    "1774410001": [{"name": "+1_sign", "count": 4, "users": ["U0900H3NUUT", "U08HVLWG1UM", "W010NNJV7S8", "W4R4S9FS4"]}],
    "1774493402": [{"name": "+1moji", "count": 2, "users": ["U03HRQ036BD", "U0900H3NUUT"]}],
    "1774581875": [{"name": "+1moji", "count": 2, "users": ["U0900H3NUUT", "W010NNJV7S8"]}],
    "1774846735": [{"name": "+1moji", "count": 1, "users": ["U0900H3NUUT"]}],
    "1774918562": [{"name": "+1_sign", "count": 2, "users": ["W010NNJV7S8", "U0900H3NUUT"]}],

    # ── Apr 2026 ──────────────────────────────────────────────────────────────
    "1775014557": [{"name": "+1moji", "count": 2, "users": ["U03HRQ036BD", "U0900H3NUUT"]}],
    "1775103551": [{"name": "+1moji", "count": 2, "users": ["U0900H3NUUT", "U03HRQ036BD"]}],
    "1775446722": [{"name": "+1moji", "count": 3, "users": ["U0900H3NUUT", "U08HVLWG1UM", "WAM5KDYBZ"]}],
    "1775532770": [{"name": "+1moji", "count": 1, "users": ["U03HRQ036BD"]}],
    "1775534842": [{"name": "+1moji", "count": 1, "users": ["U0900H3NUUT"]}],
    "1775542589": [{"name": "+1_sign", "count": 1, "users": ["W010NNJV7S8"]}],
    "1775705655": [{"name": "+1moji", "count": 2, "users": ["U0900H3NUUT", "W010NNJV7S8"]}],
    "1775795822": [{"name": "+1moji", "count": 2, "users": ["U03HRQ036BD", "U0900H3NUUT"]}],
    "1776051771": [{"name": "+1_sign", "count": 1, "users": ["W010NNJV7S8"]}],
    "1776140201": [{"name": "+1moji", "count": 3, "users": ["U08HVLWG1UM", "U03HRQ036BD", "U0900H3NUUT"]}],
    "1776224856": [{"name": "+1moji", "count": 5, "users": ["U03HRQ036BD", "W010NNJV7S8", "W4R4S9FS4", "U08HVLWG1UM", "WAM5KDYBZ"]}],
    "1776312753": [{"name": "+1_sign", "count": 1, "users": ["W010NNJV7S8"]}],
    "1776398888": [{"name": "+1moji", "count": 3, "users": ["U08HVLWG1UM", "U03HRQ036BD", "U0AKAJDDJHH"]}],
    "1776661768": [{"name": "+1moji", "count": 2, "users": ["U08HVLWG1UM", "U0900H3NUUT"]}],
    "1776743793": [{"name": "+1_sign", "count": 2, "users": ["U03HRQ036BD", "U0900H3NUUT"]}],
    "1776831026": [{"name": "+1moji", "count": 2, "users": ["U0900H3NUUT", "U03HRQ036BD"]}],
    "1776914151": [{"name": "+1moji", "count": 3, "users": ["U08HVLWG1UM", "U03HRQ036BD", "U0900H3NUUT"]}],
    "1777263621": [{"name": "+1moji", "count": 1, "users": ["U0AKAJDDJHH"]}],
    "1777347939": [{"name": "+1moji", "count": 1, "users": ["U03HRQ036BD"]}],
    "1777435628": [{"name": "+1moji", "count": 2, "users": ["U08HVLWG1UM", "W010NNJV7S8"]}],
    "1777437735": [{"name": "+1moji", "count": 1, "users": ["W4R4S9FS4"]}],
    "1777521954": [{"name": "+1moji", "count": 3, "users": ["W4R4S9FS4", "U0900H3NUUT", "U08HVLWG1UM"]}],

    # ── May 2026 ──────────────────────────────────────────────────────────────
    "1777951208": [{"name": "+1moji", "count": 1, "users": ["W4R4S9FS4"]}],
    "1778038825": [{"name": "+1_sign", "count": 2, "users": ["U03HRQ036BD", "W4R4S9FS4"]}],
    "1778124160": [{"name": "+1moji", "count": 1, "users": ["U03HRQ036BD"]}],
    "1778129623": [{"name": "+1_sign", "count": 1, "users": ["W010NNJV7S8"]}],
    "1778214994": [{"name": "+1_sign", "count": 1, "users": ["W010NNJV7S8"]}],
    "1778216726": [{"name": "+1moji", "count": 1, "users": ["U03HRQ036BD"]}],
    "1778471796": [{"name": "+1_sign", "count": 1, "users": ["W010NNJV7S8"]}],
    "1778558578": [{"name": "+1moji", "count": 2, "users": ["U03HRQ036BD", "W010NNJV7S8"]}],
    "1778644122": [{"name": "+1moji", "count": 1, "users": ["U0900H3NUUT"]}],
    "1778648348": [{"name": "+1_sign", "count": 1, "users": ["W010NNJV7S8"]}],
    "1778724428": [{"name": "+1moji", "count": 1, "users": ["U03HRQ036BD"]}],
    "1778815218": [{"name": "+1moji", "count": 3, "users": ["U03HRQ036BD", "U0900H3NUUT", "U0AKAJDDJHH"]}],
    "1779076970": [{"name": "+1moji", "count": 2, "users": ["W4R4S9FS4", "WAM5KDYBZ"]}],
    "1779160786": [{"name": "+1moji", "count": 2, "users": ["U0900H3NUUT", "W4R4S9FS4"]}],
    "1779165405": [{"name": "+1moji", "count": 1, "users": ["U0AKAJDDJHH"]}],
    "1779251307": [{"name": "+1moji", "count": 3, "users": ["U03HRQ036BD", "W010NNJV7S8", "W4R4S9FS4"]}],
    "1779337414": [{"name": "+1moji", "count": 2, "users": ["U0AKAJDDJHH", "W4R4S9FS4"]}],
    "1779421587": [{"name": "+1moji", "count": 1, "users": ["U03HRQ036BD"]}],
    "1779677013": [{"name": "+1_sign", "count": 1, "users": ["W010NNJV7S8"]}],
    "1779772851": [{"name": "+1_sign", "count": 1, "users": ["W010NNJV7S8"]}],

    # ── Jun 2026 ──────────────────────────────────────────────────────────────
    "1780288410": [{"name": "+1_sign", "count": 1, "users": ["W010NNJV7S8"]}],
    "1780458416": [{"name": "+1moji", "count": 1, "users": ["U03HRQ036BD"]}],
    "1780631614": [{"name": "+1moji", "count": 1, "users": ["U0900H3NUUT"]}],
}


def main():
    with open(DATA_FILE) as f:
        records = json.load(f)

    ts_index = {r["ts"]: i for i, r in enumerate(records)}

    updated = 0
    not_found = []
    for ts_str, rxs in REACTIONS.items():
        if ts_str in ts_index:
            records[ts_index[ts_str]]["reactions"] = rxs
            updated += 1
        else:
            not_found.append(ts_str)

    print(f"Updated {updated} records.")
    if not_found:
        print(f"WARNING: {len(not_found)} timestamps not found in file:")
        for ts in not_found:
            print(f"  {ts}")

    with open(DATA_FILE, "w") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(records)} records to {DATA_FILE}")


if __name__ == "__main__":
    main()

"""Frozen cricket scoring conventions (Phase 1 audit + row-level extras review).

Cricket rationale
-----------------
`runs` is off-the-bat scoring (boundary flags match on non-extra balls).
Team innings total = runs + extras1_runs + extras_2_runs.
Wides/byes/leg-byes store extras in extras1_runs with runs = 0.
Overstep is a no-ball: extras1_runs is always 1; runs is batter scoring.

`other` extras: 264 rows. delivery_style is dominated by Beamer / Full Toss /
Slow Bouncer — height or waist-high no-balls, not byes. extras1_runs is always 1
and the runs distribution matches Overstep. Treating them as legal balls produces
impossible 121–124 ball completed 20-over innings. Classification: no-ball.

`extras_2_runs` > 0 only on Overstep/`other` and only when runs = 0 (35 balls).
That pattern is additional extras not off the bat (byes/leg-byes off a no-ball).
Team total includes them; they are not charged to the bowler.
"""

from __future__ import annotations

EXTRAS_WIDE = {"wide"}
EXTRAS_NO_BALL = {"Overstep", "other"}
EXTRAS_BYE = {"byes"}
EXTRAS_LEG_BYE = {"legbyes"}
EXTRAS_PENALTY = {"Penalty"}

BOWLER_CREDITED_DISMISSAL_TYPES = {
    "Caught",
    "Bowled",
    "LBW",
    "Stump",
    "Hit Wicket",
}

NON_BOWLER_DISMISSAL_TYPES = {
    "RunOut",
    "Retire Out",
    "Obstructing the field",
    "Obstracting the field",
}

REVISED_OVERS_UNIT = "legal_balls"
SUPER_OVER_INNINGS = {3, 4}
REGULATION_INNINGS = {1, 2}

UNMERGED_IDENTITY_IDS = {
    8638,  # Basil Hameed (UAE, BBB present)
    39444,  # Basil Hameed (UAE, BBB present) — not merged
}


def extras_family(value) -> str:
    if value is None or (isinstance(value, float) and value != value):
        return "none"
    text = str(value).strip()
    if text in ("", "nan", "None"):
        return "none"
    if text in EXTRAS_WIDE:
        return "wide"
    if text in EXTRAS_NO_BALL:
        return "no_ball"
    if text in EXTRAS_BYE:
        return "bye"
    if text in EXTRAS_LEG_BYE:
        return "leg_bye"
    if text in EXTRAS_PENALTY:
        return "penalty"
    return "other_unknown"


def is_legal_delivery(family: str) -> bool:
    return family not in {"wide", "no_ball"}


def is_batter_ball_faced(family: str) -> bool:
    """Standard cricket: wides are not balls faced; no-balls are faced."""
    return family != "wide"


def batter_runs_from_row(runs: float, family: str) -> float:
    if family in {"wide", "bye", "leg_bye", "penalty"}:
        return 0.0
    return float(runs or 0)


def team_runs_from_row(runs: float, extras1: float, extras2: float) -> float:
    return float(runs or 0) + float(extras1 or 0) + float(extras2 or 0)


def bowler_conceded_from_row(runs: float, extras1: float, extras2: float, family: str) -> float:
    """Wides and no-ball extras (extras1) charged to bowler; byes/leg-byes/penalty not.

    extras2 on no-balls is treated as bye/leg-bye: not bowler-conceded.
    """
    batter = batter_runs_from_row(runs, family)
    if family == "wide":
        return float(extras1 or 0)
    if family == "no_ball":
        return batter + float(extras1 or 0)
    if family in {"bye", "leg_bye", "penalty"}:
        return 0.0
    return batter


def bowler_credited_wicket(is_wicket: bool, dismissal_type) -> bool:
    if not is_wicket:
        return False
    return str(dismissal_type) in BOWLER_CREDITED_DISMISSAL_TYPES

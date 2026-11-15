"""Run the full player-level stack for one scenario.

A scenario fixes: which PI columns define pressure, the frozen thresholds,
which levels count as "pressure", eligibility and z. Baselines are re-fitted
per scenario because the pressure level is one of the context strata.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from config.settings import RANK_Z
from src.baselines.expected_performance import (add_batting_expectations, add_bowling_expectations,
                                                batting_rows, bowling_rows)
from src.batting.batting_metrics import batting_match_table, batting_summary
from src.bowling.bowling_metrics import bowling_match_table, bowling_summary
from src.pressure.pressure_engine import classify
from src.ranking.rankings import build_rankings


@dataclass
class Scenario:
    name: str
    elevated: float
    high: float
    pi_bat: str = "pi_bat"
    pi_bowl: str = "pi_bowl"
    levels: tuple = ("Elevated", "High")
    z: float = RANK_Z
    bat_elig: tuple | None = None
    bowl_elig: tuple | None = None
    subset: dict = field(default_factory=dict)  # e.g. {"format_group": "IPL"}


def run_scenario(d: pd.DataFrame, sc: Scenario, keep_detail: bool = False) -> dict:
    d = d.copy()
    for col, val in sc.subset.items():
        d = d[d[col] == val]
    d["pressure_level_bat"] = classify(d[sc.pi_bat], sc.elevated, sc.high)
    d["pressure_level_bowl"] = classify(d[sc.pi_bowl], sc.elevated, sc.high)
    b = add_batting_expectations(batting_rows(d))
    w = add_bowling_expectations(bowling_rows(d))
    bmt = batting_match_table(b, pressure_levels=sc.levels)
    wmt = bowling_match_table(w, pressure_levels=sc.levels)
    bs, ws = batting_summary(bmt), bowling_summary(wmt)
    be = sc.bat_elig or (None, None)
    we = sc.bowl_elig or (None, None)
    br, bmeta = build_rankings(bmt, bs, "batting", z=sc.z, min_matches=be[0], min_balls=be[1])
    wr, wmeta = build_rankings(wmt, ws, "bowling", z=sc.z, min_matches=we[0], min_balls=we[1])
    out = {"bat_rank": br, "bowl_rank": wr, "bat_meta": bmeta, "bowl_meta": wmeta}
    if keep_detail:
        out.update({"bat_rows": b, "bowl_rows": w, "bat_mt": bmt, "bowl_mt": wmt, "deliveries": d})
    return out

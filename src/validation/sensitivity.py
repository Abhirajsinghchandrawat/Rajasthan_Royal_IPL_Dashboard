"""Sensitivity analysis: how much do the official rankings move under
reasonable alternative assumptions?

Scenarios
- Pressure thresholds shifted by -10, -5, +5, +10 PI points
- High-only pressure deliveries
- Alternative pressure definitions: difficulty-only; geometric mean of ranks
- Eligibility grid
- Ranking z: 0 (posterior mean) and 1.645

Metrics per scenario: top-10 overlap with official, Spearman rank correlation
on players eligible in both, and each official top-10 player's rank.
"""

from __future__ import annotations

import pandas as pd
from scipy.stats import spearmanr

from config.settings import ELIGIBILITY_GRID, RANK_Z_SENSITIVITY, THRESHOLD_SENSITIVITY_SHIFTS
from src.ranking.player_models import Scenario, run_scenario


def scenarios(th: dict) -> list[Scenario]:
    e, h = th["elevated"], th["high"]
    sc = [Scenario(f"Thresholds {s:+d}", e + s, h + s) for s in THRESHOLD_SENSITIVITY_SHIFTS]
    sc.append(Scenario("High-only pressure", e, h, levels=("High",)))
    sc.append(Scenario("Difficulty-only PI", e, h, pi_bat="pi_bat_difficulty_only", pi_bowl="pi_bowl_difficulty_only"))
    sc.append(Scenario("Geometric-rank PI", e, h, pi_bat="pi_bat_geo_rank", pi_bowl="pi_bowl_geo_rank"))
    for z in RANK_Z_SENSITIVITY:
        sc.append(Scenario(f"Ranking z={z}", e, h, z=z))
    return sc


def compare(official: pd.DataFrame, alt: pd.DataFrame, name: str, kind: str) -> tuple[dict, pd.DataFrame]:
    o = official.dropna(subset=["rank"]).set_index("player_id")["rank"]
    a = alt.dropna(subset=["rank"]).set_index("player_id")["rank"]
    top_o = set(o[o <= 10].index)
    top_a = set(a[a <= 10].index)
    both = o.index.intersection(a.index)
    rho = float(spearmanr(o[both], a[both]).statistic) if len(both) > 3 else float("nan")
    summary = {"scenario": name, "kind": kind, "top10_overlap": len(top_o & top_a),
               "spearman": rho, "n_common_eligible": len(both), "n_eligible": int(a.notna().sum())}
    moves = pd.DataFrame({"player_id": sorted(top_o), "scenario": name, "kind": kind})
    moves["official_rank"] = moves["player_id"].map(o)
    moves["scenario_rank"] = moves["player_id"].map(a)
    return summary, moves


def run_sensitivity(d: pd.DataFrame, th: dict, official: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows, moves = [], []
    for sc in scenarios(th):
        res = run_scenario(d, sc)
        for kind, key in (("batting", "bat_rank"), ("bowling", "bowl_rank")):
            s, m = compare(official[key], res[key], sc.name, kind)
            rows.append(s)
            moves.append(m)
    # eligibility grid: re-rank from the official scenario (no refit needed)
    from src.ranking.rankings import build_rankings
    for mm, mb in ELIGIBILITY_GRID:
        for kind, key, mt, sm in (("batting", "bat_rank", official["bat_mt"], official["bat_summary"]),
                                  ("bowling", "bowl_rank", official["bowl_mt"], official["bowl_summary"])):
            mb_k = mb if kind == "batting" else int(mb * 1.2)
            alt, _ = build_rankings(mt, sm, kind, min_matches=mm, min_balls=mb_k)
            s, m = compare(official[key], alt, f"Eligibility >= {mm} matches / {mb_k} balls", kind)
            rows.append(s)
            moves.append(m)
    return pd.DataFrame(rows), pd.concat(moves, ignore_index=True)

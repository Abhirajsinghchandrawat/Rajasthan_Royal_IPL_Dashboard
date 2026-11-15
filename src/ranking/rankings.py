"""Official ranking estimand and leaderboard construction.

Ranking estimand (defined before any leaderboard was produced)
--------------------------------------------------------------
Reliable Pressure Rating (RPR) = posterior lower bound of the player's true
context-adjusted contribution per pressure ball:

    RPR = post_mean - z * post_sd,  z = 1.2816 (one-sided 90%)

Reading: "with 90% confidence, this player's true pressure contribution is at
least RPR." It is one statistical quantity, not a weighted composite:
- high contribution raises post_mean;
- inconsistency across matches widens the cluster-bootstrap SE -> lowers RPR;
- small samples are shrunk towards the population -> lowers RPR.
Units: batting = runs above expectation per 100 pressure balls faced;
bowling = runs prevented per 24 pressure deliveries (a 4-over spell).

Shown alongside but NOT mixed into the rank: posterior mean (Adjusted
Pressure Rating), PRD (improvement vs own normal), consistency, sample
volume, 90% CI.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from config.settings import (BATTER_MIN_PRESSURE_BALLS, BATTER_MIN_PRESSURE_MATCHES,
                             BOWLER_MIN_PRESSURE_LEGAL_BALLS, BOWLER_MIN_PRESSURE_MATCHES, RANK_Z)
from src.reliability.consistency import consistency_metrics
from src.reliability.shrinkage import estimate_prior, shrink
from src.reliability.uncertainty import cluster_bootstrap

SCALE = {"batting": 100.0, "bowling": 24.0}


def eligibility(summary: pd.DataFrame, kind: str, min_matches=None, min_balls=None) -> pd.Series:
    if kind == "batting":
        mm = BATTER_MIN_PRESSURE_MATCHES if min_matches is None else min_matches
        mb = BATTER_MIN_PRESSURE_BALLS if min_balls is None else min_balls
        return (summary["p_matches"].fillna(0) >= mm) & (summary["p_balls"].fillna(0) >= mb)
    mm = BOWLER_MIN_PRESSURE_MATCHES if min_matches is None else min_matches
    mb = BOWLER_MIN_PRESSURE_LEGAL_BALLS if min_balls is None else min_balls
    return (summary["p_matches"].fillna(0) >= mm) & (summary["p_legal"].fillna(0) >= mb)


def _shrunk(mt: pd.DataFrame, elig_ids: set, prefix: str) -> pd.DataFrame:
    bt = cluster_bootstrap(mt)
    balls = mt.groupby("player_id")["balls"].sum()
    bt["balls_w"] = bt["player_id"].map(balls)
    pop = bt[bt["player_id"].isin(elig_ids)]
    mu, tau2 = estimate_prior(pop["rate"], pop["se"], pop["balls_w"])
    pm, psd, B = shrink(bt["rate"], bt["se"], mu, tau2)
    bt["post_mean"], bt["post_sd"], bt["shrink_weight"] = pm, psd, B
    bt.attrs["prior"] = {"mu": mu, "tau2": tau2}
    keep = ["player_id", "n_matches", "rate", "se", "boot_lo", "boot_hi", "post_mean", "post_sd", "shrink_weight"]
    out = bt[keep].set_index("player_id").add_prefix(prefix)
    out.attrs["prior"] = bt.attrs["prior"]
    return out


def build_rankings(mt: pd.DataFrame, summary: pd.DataFrame, kind: str, z: float = RANK_Z,
                   min_matches=None, min_balls=None) -> tuple[pd.DataFrame, dict]:
    sc = SCALE[kind]
    summary = summary.set_index("player_id")
    elig = eligibility(summary.reset_index(), kind, min_matches, min_balls)
    elig.index = summary.index
    elig_ids = set(elig[elig].index)

    pm = mt[mt["context"] == "pressure"]
    nm = mt[mt["context"] == "normal"]
    P = _shrunk(pm, elig_ids, "pr_")
    N = _shrunk(nm[nm["player_id"].isin(pm["player_id"].unique())], elig_ids, "nr_")
    t = summary.join(P, how="left").join(N, how="left")
    t["eligible"] = elig
    for c in ["pr_rate", "pr_se", "pr_boot_lo", "pr_boot_hi", "pr_post_mean", "pr_post_sd",
              "nr_rate", "nr_se", "nr_post_mean", "nr_post_sd"]:
        t[c] = t[c] * sc
    t["rating_mean"] = t["pr_post_mean"]
    t["ci_lo"] = t["pr_post_mean"] - 1.645 * t["pr_post_sd"]
    t["ci_hi"] = t["pr_post_mean"] + 1.645 * t["pr_post_sd"]
    t["rpr"] = t["pr_post_mean"] - z * t["pr_post_sd"]
    t["prd"] = t["pr_post_mean"] - t["nr_post_mean"]
    t["prd_sd"] = np.sqrt(t["pr_post_sd"] ** 2 + t["nr_post_sd"] ** 2)
    t["prd_lo"] = t["prd"] - 1.645 * t["prd_sd"]
    t["prd_hi"] = t["prd"] + 1.645 * t["prd_sd"]
    t = t.join(consistency_metrics(pm, sc).set_index("player_id"), how="left")

    t["eligibility_status"] = np.where(t["eligible"], "Eligible",
                                       np.where(t["pr_n_matches"].fillna(0) >= 2, "Insufficient sample",
                                                "No pressure exposure"))
    t["rpr"] = t["rpr"].where(t["pr_post_sd"].notna())
    e = t[t["eligible"] & t["rpr"].notna()].reset_index().sort_values(
        ["rpr", "rating_mean", "player_id"], ascending=[False, False, True])
    e["rank"] = np.arange(1, len(e) + 1)
    t = t.join(e.set_index("player_id")["rank"], how="left")

    # Quadrants (eligible only): thresholds = eligible-population medians (documented).
    perf_med = float(e["rating_mean"].median()) if len(e) else np.nan
    rel_med = float(e["success_rate"].median()) if len(e) else np.nan
    hp = t["rating_mean"] >= perf_med
    hr = t["success_rate"] >= rel_med
    t["quadrant"] = np.where(~t["eligible"], "Not eligible",
                             np.where(hp & hr, "High performance / High reliability",
                                      np.where(hp, "High performance / Low reliability",
                                               np.where(hr, "Low performance / High reliability",
                                                        "Low performance / Low reliability"))))
    meta = {"kind": kind, "z": z, "scale": sc, "prior_pressure": P.attrs.get("prior"),
            "prior_normal": N.attrs.get("prior"), "n_eligible": int(len(e)),
            "quadrant_perf_threshold": perf_med, "quadrant_reliability_threshold": rel_med}
    return t.reset_index().sort_values(["rank", "player_id"], na_position="last"), meta


def attach_context(r: pd.DataFrame, mt: pd.DataFrame, names: pd.DataFrame, teams: pd.DataFrame) -> pd.DataFrame:
    """Display name + main team(s) + formats from the player's pressure matches (display only)."""
    tn = teams.drop_duplicates("team_id").set_index("team_id")["team_name"]
    pm = mt[mt["context"] == "pressure"].copy()
    pm["team_name"] = pm["team_id"].map(tn)
    teams_str = pm.groupby("player_id")["team_name"].agg(
        lambda s: ", ".join(s.value_counts().index[:2].astype(str)))
    fmts = pm.groupby("player_id")["format_group"].agg(lambda s: " + ".join(sorted(s.unique())))
    r = r.merge(names, on="player_id", how="left")
    r["teams"] = r["player_id"].map(teams_str)
    r["formats"] = r["player_id"].map(fmts)
    return r

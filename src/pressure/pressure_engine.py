"""Pressure Index (0-100), from both the batting and the bowling perspective.

Definition (frozen)
-------------------
    Difficulty_bat  = 1 - WP_bat          (calibrated chance the batting side loses)
    Difficulty_bowl = WP_bat              (calibrated chance the fielding side loses)
    LiveGate        = min(1, L / median(L | innings))
    PI_side         = 100 * Difficulty_side * LiveGate

Cricket rationale
-----------------
Pressure = "we are losing" while "the game is still live".
- Difficulty is a cross-fitted, out-of-sample-validated probability, so a
  PI of 70 literally means "~70% chance of losing from here, in a live game".
- The leverage gate removes dead situations (lost causes and cruises), where
  the next ball cannot change the match. It is a gate, not a weight:
  raw leverage grows mechanically as balls run out, so weighting by it would
  just re-label death overs as pressure (rejected candidate, see below).
- Bowling pressure uses the fielding side's difficulty, so defending 140 is
  correctly harder than defending 220 (spec 5.4).
- First innings and chase use separate WP models (spec 5.1 / guardrail 3).

Candidates evaluated before freezing (data/analytical/pressure_candidates):
  A  100*sqrt(rank(D)*rank(L)): chase middle overs almost never High (0.06%),
     and the first ball of a match sits at the 74th percentile. Rejected.
  B  100*rank(D)*gate: tight finishes (12 off 6) only ~50. Rejected.
  C  (frozen) raw D * gate: balanced across phases (pressure share 25-43% in
     every innings x phase cell), lost causes ~6, collapses ~60, 30-off-12 ~76.
Alternatives A and difficulty-only are retained as sensitivity scenarios.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from config.settings import LEVERAGE_GATE_QUANTILE
from src.pressure.resource_model import ResourceModel
from src.pressure.win_probability import fit_predict_innings, outcome_probabilities


def compute_pressure(d: pd.DataFrame) -> tuple[pd.DataFrame, ResourceModel, dict]:
    d = d.copy()
    d["row_id"] = np.arange(len(d))
    rm = ResourceModel().fit(ResourceModel.training_rows(d))
    probs = outcome_probabilities(d)
    parts = [fit_predict_innings(d, inn, rm, probs) for inn in (1, 2)]
    pr = pd.concat(parts, ignore_index=True)
    d = d.merge(pr, on="row_id", how="left")

    lev_ref = {}
    d["live_gate"] = np.nan
    d["lev_rank"] = np.nan
    for inn in (1, 2):
        m = (d["innings"] == inn) & d["leverage"].notna()
        ref = float(d.loc[m, "leverage"].quantile(LEVERAGE_GATE_QUANTILE))
        lev_ref[inn] = ref
        d.loc[m, "live_gate"] = np.clip(d.loc[m, "leverage"] / ref, 0, 1)
        d.loc[m, "lev_rank"] = d.loc[m, "leverage"].rank(pct=True)

    d["difficulty_bat"] = 1 - d["wp_bat"]
    d["difficulty_bowl"] = d["wp_bat"]
    d["pi_bat"] = 100 * d["difficulty_bat"] * d["live_gate"]
    d["pi_bowl"] = 100 * d["difficulty_bowl"] * d["live_gate"]
    # alternative definitions (sensitivity only)
    d["pi_bat_difficulty_only"] = 100 * d["difficulty_bat"]
    d["pi_bowl_difficulty_only"] = 100 * d["difficulty_bowl"]
    for side in ("bat", "bowl"):
        dr = d.groupby("innings")[f"difficulty_{side}"].rank(pct=True)
        d[f"pi_{side}_geo_rank"] = 100 * np.sqrt(dr * d["lev_rank"])

    # interpretable state descriptors
    d["exp_remaining_runs"] = np.where(d["pressure_eligible"],
                                       rm.predict(d["balls_remaining"], d["wickets_remaining"], d["format_group"]), np.nan)
    par = rm.predict(d["allocated_balls"], np.full(len(d), 10), d["format_group"])
    d["par_total"] = np.where((d["innings"] == 1) & d["pressure_eligible"], par, np.nan)
    d["par_deviation"] = np.where(d["innings"] == 1, d["pre_team_runs"] + d["exp_remaining_runs"] - d["par_total"], np.nan)
    d["resource_ratio"] = np.where(d["innings"] == 2, d["runs_needed"] / np.maximum(d["exp_remaining_runs"], 0.5), np.nan)
    d["wicket_value"] = np.where(d["pressure_eligible"],
                                 rm.wicket_value(d["balls_remaining"], d["wickets_remaining"], d["format_group"]), np.nan)
    meta = {"leverage_reference": lev_ref, "resource_params": rm.params, "format_multiplier": rm.format_mult}
    return d, rm, meta


def classify(pi: pd.Series, elevated: float, high: float) -> pd.Series:
    out = pd.Series(np.where(pi >= high, "High", np.where(pi >= elevated, "Elevated", "Low")), index=pi.index)
    return out.where(pi.notna(), None)

"""Tests for batting metrics, balls faced, dismissals, and context-adjusted baselines."""

from __future__ import annotations

import pandas as pd

from config.settings import DATA_ANALYTICAL, DATA_PROCESSED


def test_batting_denominators_and_dismissals():
    d = pd.read_parquet(DATA_PROCESSED / "deliveries_with_pressure.parquet")
    wides = d[d["extras_family"] == "wide"]
    assert (wides["batter_faced"] == False).all()
    assert (wides["batter_runs"] == 0).all()
    # False wicket rows (12 rows with dismissed_player_id but is_wicket=False) are not striker_out
    false_w = d[d["dismissed_player_id"].notna() & (~d["is_dismissal"])]
    assert len(false_w) == 12
    assert (false_w["striker_out"] == False).all()


def test_batting_summary_and_baseline_skill():
    bs = pd.read_parquet(DATA_ANALYTICAL / "batting_summary.parquet")
    bv = pd.read_parquet(DATA_ANALYTICAL / "baseline_validation.parquet")
    assert len(bs) > 500
    assert (bs["p_sr"].dropna() >= 0).all()
    bat_bv = bv[bv["target"] == "Batter Runs per Ball"].iloc[0]
    assert bat_bv["mse_context"] < bat_bv["mse_global"]

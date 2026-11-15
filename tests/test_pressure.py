"""Unit and integration tests for the Pre-Delivery Pressure Engine."""

from __future__ import annotations

import pandas as pd

from config.settings import DATA_ANALYTICAL, DATA_PROCESSED


def test_pre_delivery_state_no_leakage():
    d = pd.read_parquet(DATA_PROCESSED / "deliveries_with_pressure.parquet")
    sample = d[(d["match_id"] == 13511) & (d["innings"] == 1)].sort_values("innings_ball_num")
    # First ball of innings must have 0 pre_team_runs, 0 pre_wickets, 0 pre_legal_balls
    first = sample.iloc[0]
    assert first["pre_team_runs"] == 0
    assert first["pre_wickets"] == 0
    assert first["pre_legal_balls"] == 0
    # Cumulative pre_team_runs + current team_runs on row i equals pre_team_runs on row i+1
    assert (sample["pre_team_runs"].iloc[1:].to_numpy() == (sample["pre_team_runs"] + sample["team_runs"]).iloc[:-1].to_numpy()).all()


def test_pressure_index_bounds_and_exclusions():
    d = pd.read_parquet(DATA_PROCESSED / "deliveries_with_pressure.parquet")
    pe = d[d["pressure_eligible"]]
    assert pe["pi_bat"].notna().all()
    assert pe["pi_bowl"].notna().all()
    assert pe["pi_bat"].between(0.0, 100.0).all()
    assert pe["pi_bowl"].between(0.0, 100.0).all()
    # Out-of-scope or super over deliveries must not have pressure_eligible
    assert not d[d["is_super_over"]]["pressure_eligible"].any()
    assert not d[~d["in_official_scope"]]["pressure_eligible"].any()


def test_first_innings_par_vs_run_rate_safeguard():
    fv = pd.read_parquet(DATA_ANALYTICAL / "face_validity.parquet")
    d = pd.read_parquet(DATA_PROCESSED / "deliveries_with_pressure.parquet")
    i1 = d[(d["pressure_eligible"]) & (d["innings"] == 1) & (d["pre_legal_balls"] >= 30)]
    corr_rr = i1["pi_bat"].corr(i1["current_rr"])
    assert corr_rr < 0.0, "High first-innings run rate must not automatically imply high pressure"
    assert fv["pressure_share"].between(0.05, 0.85).all()

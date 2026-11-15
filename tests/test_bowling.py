"""Tests for bowling metrics, legal deliveries, conceded runs, and economy."""

from __future__ import annotations

import numpy as np
import pandas as pd

from config.settings import DATA_ANALYTICAL, DATA_PROCESSED


def test_bowling_conceded_and_legal_balls():
    d = pd.read_parquet(DATA_PROCESSED / "deliveries_with_pressure.parquet")
    byes_lb = d[d["extras_family"].isin(["bye", "leg_bye", "penalty"])]
    assert (byes_lb["bowler_conceded"] == 0).all()
    illegal = d[d["extras_family"].isin(["wide", "no_ball"])]
    assert (illegal["is_legal"] == False).all()


def test_bowling_economy_and_baseline_skill():
    ws = pd.read_parquet(DATA_ANALYTICAL / "bowling_summary.parquet")
    bv = pd.read_parquet(DATA_ANALYTICAL / "baseline_validation.parquet")
    sub = ws[ws["p_legal"] > 0]
    calc_econ = 6.0 * sub["p_conceded"] / sub["p_legal"]
    assert np.allclose(calc_econ, sub["p_economy"])
    bowl_bv = bv[bv["target"] == "Bowler Runs Conceded per Ball"].iloc[0]
    assert bowl_bv["mse_context"] < bowl_bv["mse_global"]

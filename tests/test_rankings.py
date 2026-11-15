"""Tests for official batting and bowling rankings, eligibility, and export consistency."""

from __future__ import annotations

import numpy as np
import pandas as pd

from config.settings import (
    BATTER_MIN_PRESSURE_BALLS,
    BATTER_MIN_PRESSURE_MATCHES,
    BOWLER_MIN_PRESSURE_LEGAL_BALLS,
    BOWLER_MIN_PRESSURE_MATCHES,
    DATA_ANALYTICAL,
    EXPORTS,
)


def test_batting_rankings_integrity():
    br = pd.read_parquet(DATA_ANALYTICAL / "batting_rankings.parquet")
    csv = pd.read_csv(EXPORTS / "official_top10_batters.csv")
    top10 = br[br["rank"] <= 10].sort_values("rank")
    assert len(top10) == 10
    assert top10["player_id"].is_unique
    assert top10["eligible"].all()
    assert (top10["p_matches"] >= BATTER_MIN_PRESSURE_MATCHES).all()
    assert (top10["p_balls"] >= BATTER_MIN_PRESSURE_BALLS).all()
    assert top10["rpr"].is_monotonic_decreasing
    assert np.allclose(top10["rpr"].to_numpy(), csv["rpr"].to_numpy())
    assert list(top10["player_id"]) == list(csv["player_id"])


def test_bowling_rankings_integrity():
    wr = pd.read_parquet(DATA_ANALYTICAL / "bowling_rankings.parquet")
    csv = pd.read_csv(EXPORTS / "official_top10_bowlers.csv")
    top10 = wr[wr["rank"] <= 10].sort_values("rank")
    assert len(top10) == 10
    assert top10["player_id"].is_unique
    assert top10["eligible"].all()
    assert (top10["p_matches"] >= BOWLER_MIN_PRESSURE_MATCHES).all()
    assert (top10["p_legal"] >= BOWLER_MIN_PRESSURE_LEGAL_BALLS).all()
    assert top10["rpr"].is_monotonic_decreasing
    assert np.allclose(top10["rpr"].to_numpy(), csv["rpr"].to_numpy())
    assert list(top10["player_id"]) == list(csv["player_id"])

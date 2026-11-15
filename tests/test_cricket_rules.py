"""Unit tests for cricket-scoring rules, extras accounting, dismissals, and revised targets."""

from __future__ import annotations

import pandas as pd

from config.settings import DATA_PROCESSED
from src.quality.cricket_rules import (
    UNMERGED_IDENTITY_IDS,
    batter_runs_from_row,
    bowler_conceded_from_row,
    bowler_credited_wicket,
    extras_family,
    is_batter_ball_faced,
    is_legal_delivery,
    team_runs_from_row,
)


def test_extras_family_and_legality():
    assert extras_family(None) == "none"
    assert extras_family("wide") == "wide"
    assert extras_family("Overstep") == "no_ball"
    assert extras_family("other") == "no_ball"
    assert extras_family("byes") == "bye"
    assert extras_family("legbyes") == "leg_bye"
    assert extras_family("Penalty") == "penalty"

    assert not is_legal_delivery("wide")
    assert not is_legal_delivery("no_ball")
    assert is_legal_delivery("bye")
    assert is_legal_delivery("leg_bye")
    assert is_legal_delivery("none")

    assert not is_batter_ball_faced("wide")
    assert is_batter_ball_faced("no_ball")
    assert is_batter_ball_faced("bye")


def test_runs_accounting_rules():
    # Wide: 0 batter runs, bowler charged extras1
    assert batter_runs_from_row(0, "wide") == 0.0
    assert bowler_conceded_from_row(0, 5, 0, "wide") == 5.0
    # No-ball off bat: batter gets 4, bowler charged 4 + 1 = 5
    assert batter_runs_from_row(4, "no_ball") == 4.0
    assert bowler_conceded_from_row(4, 1, 0, "no_ball") == 5.0
    # No-ball with extras_2_runs (bye/leg-bye off no-ball): team gets 1+4=5, bowler charged only 1
    assert team_runs_from_row(0, 1, 4) == 5.0
    assert bowler_conceded_from_row(0, 1, 4, "no_ball") == 1.0
    # Byes/leg-byes/penalty: 0 bowler runs
    for fam in ("bye", "leg_bye", "penalty"):
        assert batter_runs_from_row(0, fam) == 0.0
        assert bowler_conceded_from_row(0, 4, 0, fam) == 0.0


def test_bowler_wicket_attribution():
    for dt in ("Caught", "Bowled", "LBW", "Stump", "Hit Wicket"):
        assert bowler_credited_wicket(True, dt)
    for dt in ("RunOut", "Retire Out", "Obstructing the field", "Obstracting the field"):
        assert not bowler_credited_wicket(True, dt)
    assert not bowler_credited_wicket(False, "Caught")


def test_super_overs_and_basil_hameed_in_processed():
    d = pd.read_parquet(DATA_PROCESSED / "deliveries_with_pressure.parquet")
    assert (d[d["is_super_over"]]["pressure_eligible"] == False).all()
    assert {8638, 39444} == UNMERGED_IDENTITY_IDS
    assert set(UNMERGED_IDENTITY_IDS).issubset(set(d["striker_id"]).union(set(d["bowler_id"])))

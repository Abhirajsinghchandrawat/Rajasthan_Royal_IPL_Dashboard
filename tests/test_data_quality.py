"""Unit and integration tests for Phase 1 data quality and relational integrity."""

from __future__ import annotations

import pandas as pd

from config.settings import DATA_INTERIM
from src.ingestion.load_data import load_raw_tables


def test_raw_tables_load_and_counts():
    tables = load_raw_tables()
    assert len(tables["competitions"]) == 141
    assert len(tables["teams"]) == 353
    assert len(tables["matches"]) == 883
    assert len(tables["ball_by_ball"]) == 200_999
    assert len(tables["player_mapping"]) == 6_413
    assert len(tables["playing_eleven"]) == 28_381


def test_no_duplicate_delivery_keys():
    tables = load_raw_tables()
    bbb = tables["ball_by_ball"]
    assert not bbb.duplicated(["match_id", "innings", "overid", "over_ball_num"]).any()
    assert not bbb.duplicated(["match_id", "innings", "innings_ball_num"]).any()


def test_relational_integrity_and_valid_ranges():
    tables = load_raw_tables()
    bbb = tables["ball_by_ball"]
    matches = tables["matches"]
    mapping = tables["player_mapping"]

    assert set(bbb["match_id"]).issubset(set(matches["match_id"]))
    all_pids = set(bbb["striker_id"]) | set(bbb["non_striker_id"]) | set(bbb["bowler_id"])
    assert all_pids.issubset(set(mapping["player_id"]))
    assert (bbb["runs"] >= 0).all()
    assert (bbb["extras1_runs"] >= 0).all()
    assert (bbb["extras_2_runs"] >= 0).all()
    assert set(bbb["innings"].unique()) == {1, 2, 3, 4}
    assert bbb["overid"].between(1, 20).all()


def test_exclusions_documented():
    excl = pd.read_csv(DATA_INTERIM / "exclusion_flag_summary.csv")
    flags = set(excl["flag"])
    assert {"OUT_OF_OFFICIAL_SCOPE", "SUPER_OVER", "REVISED_OVERS", "REVISED_TARGET", "MATCH_NO_BBB"}.issubset(flags)

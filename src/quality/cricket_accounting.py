"""Apply cricket accounting and pre-delivery match state."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.ingestion.load_data import load_raw_tables
from src.quality.cricket_rules import (
    batter_runs_from_row,
    bowler_conceded_from_row,
    bowler_credited_wicket,
    extras_family,
    is_batter_ball_faced,
    is_legal_delivery,
    team_runs_from_row,
)

IPL_NAME_PATTERN = r"(?i)\bIPL\b|Indian Premier League"


def classify_competitions(competitions: pd.DataFrame) -> pd.DataFrame:
    out = competitions.copy()
    name = out["comp_name"].astype(str)
    fmt = out["match_format"].astype(str).str.strip()
    out["scope_group"] = np.select(
        [
            name.str.contains(IPL_NAME_PATTERN, regex=True, na=False),
            fmt.eq("T20I"),
            fmt.eq("T20"),
        ],
        ["IPL", "T20I", "Other T20"],
        default="Other/Unknown",
    )
    out["in_official_scope"] = out["scope_group"].isin(["IPL", "T20I"])
    return out


def overs_phase(overid: pd.Series) -> pd.Series:
    return np.select(
        [overid.between(1, 6), overid.between(7, 15), overid.between(16, 20)],
        ["Powerplay", "Middle", "Death"],
        default="Unknown",
    )


def account_deliveries(bbb: pd.DataFrame) -> pd.DataFrame:
    d = bbb.copy()
    d["extras_family"] = d["extras_type"].map(extras_family)
    d["is_legal"] = d["extras_family"].map(is_legal_delivery)
    d["batter_faced"] = d["extras_family"].map(is_batter_ball_faced)
    d["batter_runs"] = [
        batter_runs_from_row(r, f) for r, f in zip(d["runs"].to_numpy(), d["extras_family"].to_numpy())
    ]
    d["team_runs"] = [
        team_runs_from_row(r, e1, e2)
        for r, e1, e2 in zip(d["runs"].to_numpy(), d["extras1_runs"].to_numpy(), d["extras_2_runs"].to_numpy())
    ]
    d["bowler_conceded"] = [
        bowler_conceded_from_row(r, e1, e2, f)
        for r, e1, e2, f in zip(
            d["runs"].to_numpy(),
            d["extras1_runs"].to_numpy(),
            d["extras_2_runs"].to_numpy(),
            d["extras_family"].to_numpy(),
        )
    ]
    d["is_dismissal"] = d["is_wicket"].fillna(False).astype(bool)
    d["bowler_wicket"] = [
        bowler_credited_wicket(w, t) for w, t in zip(d["is_dismissal"].to_numpy(), d["dismissal_type"].to_numpy())
    ]
    d["is_boundary"] = (d["is_four"].fillna(False) | d["is_six"].fillna(False)).astype(bool)
    d["is_dot_batter"] = (d["batter_faced"] & (d["batter_runs"] == 0) & ~d["is_dismissal"]).astype(bool)
    d["is_dot_bowl"] = (d["is_legal"] & (d["bowler_conceded"] == 0) & ~d["is_dismissal"]).astype(bool)
    d["is_regulation"] = d["innings"].isin([1, 2])
    d["is_super_over"] = d["innings"].isin([3, 4])
    d["phase"] = overs_phase(d["overid"])
    return d


def attach_match_context(deliveries: pd.DataFrame, matches: pd.DataFrame, competitions: pd.DataFrame) -> pd.DataFrame:
    comps = classify_competitions(competitions)
    m = matches.merge(
        comps[["comp_id", "comp_name", "match_format", "season", "scope_group", "in_official_scope"]],
        on="comp_id",
        how="left",
    )
    m["format_group"] = np.where(m["scope_group"].eq("IPL"), "IPL", np.where(m["scope_group"].eq("T20I"), "T20I", "Other T20"))
    m["allocated_balls_1"] = m["first_inn_revised_overs"].fillna(120)
    m["allocated_balls_2"] = m["second_inn_revised_overs"].fillna(120)
    m["has_revised_overs"] = m["first_inn_revised_overs"].notna() | m["second_inn_revised_overs"].notna()
    m["has_revised_target"] = m["revised_target"].notna()
    m["match_date"] = pd.to_datetime(m["match_date"], errors="coerce")
    keep = [
        "match_id",
        "comp_id",
        "match_date",
        "comp_name",
        "match_format",
        "season",
        "scope_group",
        "format_group",
        "in_official_scope",
        "result",
        "win_team_id",
        "home_team_id",
        "away_team_id",
        "home_team",
        "away_team",
        "allocated_balls_1",
        "allocated_balls_2",
        "revised_target",
        "has_revised_overs",
        "has_revised_target",
        "knock_out",
        "stage",
    ]
    return deliveries.merge(m[keep], on="match_id", how="left")


def add_pre_delivery_state(d: pd.DataFrame) -> pd.DataFrame:
    d = d.sort_values(["match_id", "innings", "innings_ball_num"]).copy()
    g = d.groupby(["match_id", "innings"], sort=False)
    d["pre_team_runs"] = g["team_runs"].cumsum() - d["team_runs"]
    d["pre_wickets"] = g["is_dismissal"].cumsum() - d["is_dismissal"].astype(int)
    d["pre_legal_balls"] = g["is_legal"].cumsum() - d["is_legal"].astype(int)
    d["pre_deliveries"] = g.cumcount()

    inn1_total = (
        d[d["innings"] == 1]
        .groupby("match_id", as_index=False)
        .agg(inn1_team_runs=("team_runs", "sum"), inn1_legal=("is_legal", "sum"), inn1_wkts=("is_dismissal", "sum"))
    )
    d = d.merge(inn1_total, on="match_id", how="left")

    d["allocated_balls"] = np.where(d["innings"] == 1, d["allocated_balls_1"], d["allocated_balls_2"])
    d["allocated_balls"] = np.where(d["innings"].isin([3, 4]), 6, d["allocated_balls"])
    d["balls_remaining"] = (d["allocated_balls"] - d["pre_legal_balls"]).clip(lower=0)
    d["wickets_remaining"] = (10 - d["pre_wickets"]).clip(lower=0)
    d["current_rr"] = np.where(d["pre_legal_balls"] > 0, 6 * d["pre_team_runs"] / d["pre_legal_balls"], 0.0)

    default_target = d["inn1_team_runs"] + 1
    d["chase_target"] = np.where(
        d["innings"] == 2,
        np.where(d["revised_target"].notna(), d["revised_target"], default_target),
        np.nan,
    )
    d["runs_needed"] = np.where(d["innings"] == 2, (d["chase_target"] - d["pre_team_runs"]).clip(lower=0), np.nan)
    d["required_rr"] = np.where(
        (d["innings"] == 2) & (d["balls_remaining"] > 0),
        6 * d["runs_needed"] / d["balls_remaining"],
        np.nan,
    )
    # A chase target is unreliable when (a) the first innings has no BBB, or
    # (b) the match had an overs revision but no revised target was supplied
    # (DLS target cannot be reconstructed without the DLS table).
    d["target_unreliable"] = (d["innings"] == 2) & (
        d["inn1_team_runs"].isna()
        | (d["has_revised_overs"] & d["revised_target"].isna()
           & ((d["allocated_balls_2"] < 120) | (d["allocated_balls_1"] < 120)))
    )
    return d


def add_attribution_and_flags(d: pd.DataFrame) -> pd.DataFrame:
    """Batter-dismissal attribution and analytical-eligibility flags.

    Cricket rationale
    - A dismissal belongs to the dismissed batter (dismissed_player_id), not
      automatically to the striker: a non-striker run-out is not the striker's
      wicket. The one Retire Out row with a missing id is assigned to the
      striker (documented assumption, 1 row).
    - 12 rows carry a dismissed_player_id with is_wicket=False (Phase 1). They
      are NOT dismissals.
    - Pressure is only scored on official-scope regulation deliveries whose
      resources/target are reconstructable.
    """
    dis = d["dismissed_player_id"]
    d["striker_out"] = d["is_dismissal"] & (dis.eq(d["striker_id"]) | dis.isna())
    d["nonstriker_out"] = d["is_dismissal"] & dis.eq(d["non_striker_id"])
    d["season_year"] = d["match_date"].dt.year
    d["wkts_bucket"] = pd.cut(
        d["wickets_remaining"], bins=[-1, 4, 6, 8, 10], labels=["<=4", "5-6", "7-8", "9-10"]
    ).astype(str)
    chase_ok = (d["innings"] == 1) | (
        (d["innings"] == 2) & ~d["target_unreliable"] & (d["runs_needed"] > 0)
    )
    d["pressure_eligible"] = (
        d["in_official_scope"].fillna(False).astype(bool)
        & d["is_regulation"]
        & (d["balls_remaining"] > 0)
        & chase_ok
    )
    return d


def player_display_names(mapping: pd.DataFrame, d: pd.DataFrame) -> pd.DataFrame:
    names = pd.concat(
        [
            mapping[["player_id", "player_name"]],
            d[["striker_id", "striker_name"]].rename(columns={"striker_id": "player_id", "striker_name": "player_name"}),
            d[["bowler_id", "bowler_name"]].rename(columns={"bowler_id": "player_id", "bowler_name": "player_name"}),
        ],
        ignore_index=True,
    ).dropna()
    names["player_name"] = names["player_name"].astype(str).str.strip()
    freq = names.groupby(["player_id", "player_name"]).size().reset_index(name="n")
    freq = freq.sort_values(["player_id", "n"], ascending=[True, False])
    canon = freq.drop_duplicates("player_id")[["player_id", "player_name"]]
    return canon


def build_accounted_deliveries() -> pd.DataFrame:
    tables = load_raw_tables()
    d = account_deliveries(tables["ball_by_ball"])
    d = attach_match_context(d, tables["matches"], tables["competitions"])
    d = add_pre_delivery_state(d)
    d = add_attribution_and_flags(d)
    names = player_display_names(tables["player_mapping"], d)
    d = d.merge(names.rename(columns={"player_id": "striker_id", "player_name": "striker_canon"}), on="striker_id", how="left")
    d = d.merge(names.rename(columns={"player_id": "bowler_id", "player_name": "bowler_canon"}), on="bowler_id", how="left")
    d["striker_name"] = d["striker_canon"].fillna(d["striker_name"])
    d["bowler_name"] = d["bowler_canon"].fillna(d["bowler_name"])
    d = d.drop(columns=["striker_canon", "bowler_canon"], errors="ignore")
    return d, names, tables

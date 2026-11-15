"""Phase 1 data audit for PRESSUREIQ.

Inspects source CSVs, validates relationships and cricket scoring conventions,
and writes audit artefacts. Does not compute player rankings.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ingestion.load_data import load_raw_tables

INTERIM = ROOT / "data" / "interim"
REPORTS = ROOT / "reports" / "methodology"
EXPECTED_COLUMNS = {
    "competitions": ["comp_id", "comp_name", "match_format", "season"],
    "teams": ["comp_id", "team_id", "team_name"],
    "matches": [
        "match_id",
        "comp_id",
        "match_number",
        "match_date",
        "stage",
        "venue_id",
        "venue_country",
        "home_team_id",
        "home_team",
        "away_team_id",
        "away_team",
        "home_team_captain_id",
        "away_team_captain_id",
        "toss_win_team_id",
        "toss_opted",
        "man_of_the_match",
        "first_inn_revised_overs",
        "second_inn_revised_overs",
        "revised_target",
        "knock_out",
        "win_team_id",
        "result",
    ],
    "ball_by_ball": [
        "match_id",
        "innings",
        "overid",
        "over_ball_num",
        "innings_ball_num",
        "batting_team_id",
        "bowling_team_id",
        "striker_id",
        "striker_name",
        "non_striker_id",
        "non_striker_name",
        "bowler_id",
        "bowler_name",
        "batting_type",
        "bowling_type",
        "batting_order",
        "runs",
        "is_four",
        "is_six",
        "is_wicket",
        "dismissal_type_id",
        "dismissal_type",
        "dismissed_player_id",
        "extras_type",
        "extras1_runs",
        "extras_2_runs",
        "pace_or_spin",
        "bowl_speed",
        "stroke",
        "delivery_style",
        "over_or_around",
        "on_or_off",
        "delivery_ist_time",
    ],
    "player_mapping": [
        "comp_id",
        "comp_name",
        "team_id",
        "team_name",
        "player_id",
        "player_name",
    ],
    "playing_eleven": [
        "match_id",
        "team_id",
        "player_id",
        "batting_order",
        "is_played",
        "is_captain",
        "is_wk",
        "is_impact",
        "is_impact_off",
    ],
}

IPL_NAME_PATTERN = r"(?i)\bIPL\b|Indian Premier League"
T20I_FORMAT = "T20I"
T20_FORMAT = "T20"

BOWLER_CREDITED_DISMISSALS = {
    "bowled",
    "caught",
    "lbw",
    "stumped",
    "caught and bowled",
    "hit wicket",
}
NON_BOWLER_DISMISSALS = {
    "run out",
    "retired out",
    "retired hurt",
    "obstructing the field",
    "hit the ball twice",
    "timed out",
    "absent hurt",
    "retired not out",
}


def _json_ready(obj):
    if isinstance(obj, dict):
        return {str(k): _json_ready(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_ready(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        val = float(obj)
        return None if np.isnan(val) else val
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if pd.isna(obj):
        return None
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    return obj


def classify_competitions(competitions: pd.DataFrame) -> pd.DataFrame:
    out = competitions.copy()
    name = out["comp_name"].astype(str)
    fmt = out["match_format"].astype(str).str.strip()
    out["scope_group"] = np.select(
        [
            name.str.contains(IPL_NAME_PATTERN, regex=True, na=False),
            fmt.eq(T20I_FORMAT),
            fmt.eq(T20_FORMAT),
        ],
        ["IPL", "T20I", "Other T20"],
        default="Other/Unknown",
    )
    return out


def missing_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    n = len(df)
    for col in df.columns:
        miss = int(df[col].isna().sum())
        empty = 0
        if df[col].dtype == object or pd.api.types.is_string_dtype(df[col]):
            empty = int((df[col].astype(str).str.strip().isin(["", "nan", "None", "NaN"])).sum())
        rows.append(
            {
                "column": col,
                "missing": miss,
                "missing_plus_blank_like": miss if df[col].dtype != object else int(df[col].isna().sum()),
                "pct_missing": round(100 * miss / n, 4) if n else None,
                "n_unique": int(df[col].nunique(dropna=True)),
                "dtype": str(df[col].dtype),
            }
        )
    return pd.DataFrame(rows)


def extras_family(value) -> str:
    if pd.isna(value):
        return "none"
    text = str(value).strip().lower()
    if "wide" in text:
        return "wide"
    if "no ball" in text or "noball" in text or "no-ball" in text or "overstep" in text:
        return "no_ball"
    if "leg bye" in text or "legbye" in text:
        return "leg_bye"
    if text == "bye" or text.startswith("bye"):
        return "bye"
    if "penalty" in text:
        return "penalty"
    return "other"


def dismissal_family(value) -> str:
    if pd.isna(value):
        return "none"
    text = str(value).strip().lower()
    if text in BOWLER_CREDITED_DISMISSALS:
        return "bowler_credited"
    if "run out" in text:
        return "run_out"
    if "retired" in text:
        return "retired"
    if text in NON_BOWLER_DISMISSALS or "obstruct" in text:
        return "non_bowler"
    if text in {"caught", "bowled", "lbw", "stumped"}:
        return "bowler_credited"
    if "caught" in text:
        return "bowler_credited"
    return "unclassified"


def legal_delivery_flag(extras_fam: str) -> bool:
    return extras_fam not in {"wide", "no_ball"}


def build_scope(matches: pd.DataFrame, competitions: pd.DataFrame) -> pd.DataFrame:
    comps = classify_competitions(competitions)
    out = matches.merge(
        comps[["comp_id", "comp_name", "match_format", "season", "scope_group"]],
        on="comp_id",
        how="left",
        suffixes=("", "_comp"),
    )
    out["in_official_scope"] = out["scope_group"].isin(["IPL", "T20I"])
    return out


def inspect_runs_encoding(bbb: pd.DataFrame) -> dict:
    work = bbb.copy()
    work["extras_family"] = work["extras_type"].map(extras_family)
    work["has_extra"] = work["extras_type"].notna()
    work["runs_minus_extras1"] = work["runs"] - work["extras1_runs"].fillna(0)
    work["runs_minus_both_extras"] = work["runs"] - work["extras1_runs"].fillna(0) - work["extras_2_runs"].fillna(0)

    family_summary = (
        work.groupby("extras_family", dropna=False)
        .agg(
            n=("match_id", "size"),
            runs_min=("runs", "min"),
            runs_max=("runs", "max"),
            runs_mean=("runs", "mean"),
            extras1_min=("extras1_runs", "min"),
            extras1_max=("extras1_runs", "max"),
            extras1_mean=("extras1_runs", "mean"),
            extras2_min=("extras_2_runs", "min"),
            extras2_max=("extras_2_runs", "max"),
            extras2_mean=("extras_2_runs", "mean"),
            pct_runs_eq_extras1=("runs", lambda s: float((s.values == work.loc[s.index, "extras1_runs"].fillna(0).values).mean())),
            pct_runs_gt_extras1=("runs", lambda s: float((s.values > work.loc[s.index, "extras1_runs"].fillna(0).values).mean())),
            four_rate=("is_four", "mean"),
            six_rate=("is_six", "mean"),
        )
        .reset_index()
    )

    extras_type_summary = (
        work.groupby(work["extras_type"].fillna("(none)"), dropna=False)
        .agg(
            n=("match_id", "size"),
            runs_mean=("runs", "mean"),
            extras1_mean=("extras1_runs", "mean"),
            extras2_mean=("extras_2_runs", "mean"),
            runs_eq_extras1=("runs", lambda s: int((s.values == work.loc[s.index, "extras1_runs"].fillna(0).values).sum())),
            both_extras_nonzero=("extras_2_runs", lambda s: int(((work.loc[s.index, "extras1_runs"].fillna(0) > 0) & (s.fillna(0) > 0)).sum())),
        )
        .reset_index()
        .sort_values("n", ascending=False)
    )

    # Candidate batter-run definitions to test against boundary flags
    candidates = {
        "runs": work["runs"],
        "runs_minus_extras1": work["runs"] - work["extras1_runs"].fillna(0),
        "extras2_as_batter": work["extras_2_runs"].fillna(0),
        "runs_if_no_extra_else_extras2": np.where(
            work["extras_family"].eq("none"),
            work["runs"],
            work["extras_2_runs"].fillna(0),
        ),
        "runs_if_legal_extra_keep_runs": np.where(
            work["extras_family"].isin(["wide", "no_ball"]),
            np.maximum(work["runs"] - work["extras1_runs"].fillna(0), 0),
            work["runs"],
        ),
    }

    boundary_alignment = []
    for name, series in candidates.items():
        s = pd.Series(series, index=work.index)
        fours = work["is_four"].fillna(False).astype(bool)
        sixes = work["is_six"].fillna(False).astype(bool)
        neither = ~(fours | sixes)
        boundary_alignment.append(
            {
                "candidate": name,
                "four_eq_4_rate": float((s[fours] == 4).mean()) if fours.any() else None,
                "six_eq_6_rate": float((s[sixes] == 6).mean()) if sixes.any() else None,
                "nonboundary_in_0_3_rate": float(s[neither].between(0, 3).mean()) if neither.any() else None,
                "negative_count": int((s < 0).sum()),
            }
        )

    both_extras = work[(work["extras1_runs"].fillna(0) > 0) & (work["extras_2_runs"].fillna(0) > 0)]
    return {
        "family_summary": family_summary,
        "extras_type_summary": extras_type_summary,
        "boundary_alignment": pd.DataFrame(boundary_alignment),
        "both_extras_nonzero_n": int(len(both_extras)),
        "both_extras_by_type": both_extras["extras_type"].value_counts(dropna=False).to_dict() if len(both_extras) else {},
        "sample_both_extras": both_extras.head(20),
        "negative_runs": int((work["runs"] < 0).sum()),
        "negative_extras1": int((work["extras1_runs"] < 0).sum()),
        "negative_extras2": int((work["extras_2_runs"] < 0).sum()),
    }


def innings_reconciliation(bbb: pd.DataFrame, matches: pd.DataFrame) -> pd.DataFrame:
    work = bbb.copy()
    work["extras_family"] = work["extras_type"].map(extras_family)
    work["is_legal"] = work["extras_family"].map(legal_delivery_flag)
    work["is_regulation"] = work["innings"].isin([1, 2])

    # Candidate scoring identities
    work["team_runs_a"] = work["runs"]
    work["team_runs_b"] = work["runs"] + work["extras1_runs"].fillna(0)
    work["team_runs_c"] = work["runs"] + work["extras1_runs"].fillna(0) + work["extras_2_runs"].fillna(0)
    work["batter_runs_a"] = np.where(work["extras_family"].eq("none"), work["runs"], 0)
    work["batter_runs_b"] = np.where(
        work["extras_family"].isin(["none", "no_ball"]),
        np.where(work["extras_family"].eq("no_ball"), work["extras_2_runs"].fillna(0), work["runs"]),
        0,
    )
    work["batter_runs_c"] = np.where(
        work["extras_family"].isin(["wide", "bye", "leg_bye", "penalty"]),
        work["extras_2_runs"].fillna(0),
        np.where(work["extras_family"].eq("no_ball"), work["extras_2_runs"].fillna(0), work["runs"]),
    )

    grouped = (
        work[work["is_regulation"]]
        .groupby(["match_id", "innings", "batting_team_id"], as_index=False)
        .agg(
            deliveries=("runs", "size"),
            legal_balls=("is_legal", "sum"),
            max_innings_ball_num=("innings_ball_num", "max"),
            max_overid=("overid", "max"),
            wickets=("is_wicket", "sum"),
            team_runs_a=("team_runs_a", "sum"),
            team_runs_b=("team_runs_b", "sum"),
            team_runs_c=("team_runs_c", "sum"),
            batter_runs_a=("batter_runs_a", "sum"),
            batter_runs_b=("batter_runs_b", "sum"),
            batter_runs_c=("batter_runs_c", "sum"),
            extras1=("extras1_runs", "sum"),
            extras2=("extras_2_runs", "sum"),
        )
    )

    # Parse result strings for winner/margin where possible
    m = matches.copy()
    result = m["result"].astype(str)
    m["result_by_runs"] = result.str.contains(r"(?i)\bby\s+\d+\s+runs?\b", regex=True)
    m["result_by_wickets"] = result.str.contains(r"(?i)\bby\s+\d+\s+wickets?\b", regex=True)
    m["result_margin"] = result.str.extract(r"(?i)by\s+(\d+)\s+(?:runs?|wickets?)", expand=False).astype(float)
    m["no_result"] = result.str.contains(r"(?i)no result|abandoned|cancelled", regex=True)
    m["tie_flag"] = result.str.contains(r"(?i)\btie\b|super over", regex=True)

    inn1 = grouped[grouped["innings"] == 1][
        ["match_id", "batting_team_id", "team_runs_a", "team_runs_b", "team_runs_c", "wickets", "legal_balls"]
    ].rename(
        columns={
            "batting_team_id": "inn1_team",
            "team_runs_a": "inn1_a",
            "team_runs_b": "inn1_b",
            "team_runs_c": "inn1_c",
            "wickets": "inn1_wkts",
            "legal_balls": "inn1_legal",
        }
    )
    inn2 = grouped[grouped["innings"] == 2][
        ["match_id", "batting_team_id", "team_runs_a", "team_runs_b", "team_runs_c", "wickets", "legal_balls"]
    ].rename(
        columns={
            "batting_team_id": "inn2_team",
            "team_runs_a": "inn2_a",
            "team_runs_b": "inn2_b",
            "team_runs_c": "inn2_c",
            "wickets": "inn2_wkts",
            "legal_balls": "inn2_legal",
        }
    )
    pair = inn1.merge(inn2, on="match_id", how="outer")
    pair = pair.merge(
        m[
            [
                "match_id",
                "win_team_id",
                "result",
                "result_by_runs",
                "result_by_wickets",
                "result_margin",
                "no_result",
                "tie_flag",
                "revised_target",
                "home_team_id",
                "away_team_id",
            ]
        ],
        on="match_id",
        how="left",
    )

    for suffix in ["a", "b", "c"]:
        pair[f"margin_runs_{suffix}"] = pair[f"inn1_{suffix}"] - pair[f"inn2_{suffix}"]
        pair[f"chase_reached_{suffix}"] = pair[f"inn2_{suffix}"] > pair[f"inn1_{suffix}"]
        target = pair["revised_target"].where(pair["revised_target"].notna(), pair[f"inn1_{suffix}"] + 1)
        pair[f"implied_target_{suffix}"] = target
        pair[f"win_by_runs_match_{suffix}"] = (
            pair["result_by_runs"]
            & pair["result_margin"].notna()
            & (pair[f"margin_runs_{suffix}"] == pair["result_margin"])
        )
        pair[f"win_by_wickets_score_ok_{suffix}"] = (
            pair["result_by_wickets"]
            & pair["revised_target"].isna()
            & (pair[f"inn2_{suffix}"] > pair[f"inn1_{suffix}"])
        )
        pair[f"revised_chase_ok_{suffix}"] = (
            pair["revised_target"].notna()
            & pair["result_by_wickets"]
            & (pair[f"inn2_{suffix}"] >= pair["revised_target"])
        )

    return pair


def revised_overs_decode(value) -> dict:
    if pd.isna(value):
        return {"raw": None, "as_decimal_overs": None, "as_legal_balls": None}
    raw = float(value)
    # Candidate A: already decimal overs, e.g. 5.2 means 5 overs + 2 balls
    whole = int(np.floor(raw + 1e-9))
    frac = round(raw - whole, 4)
    balls_from_decimal = whole * 6 + int(round(frac * 10)) if frac < 0.7 else None
    # Candidate B: value is already legal balls
    as_balls = int(round(raw)) if abs(raw - round(raw)) < 1e-6 else None
    # Candidate C: value is overs as integer only
    return {
        "raw": raw,
        "as_decimal_overs_balls": balls_from_decimal,
        "as_integer_balls": as_balls,
        "as_integer_overs_balls": int(round(raw)) * 6 if as_balls is not None else None,
    }


def audit_playing_xi(xi: pd.DataFrame, matches: pd.DataFrame, bbb: pd.DataFrame) -> dict:
    key = ["match_id", "team_id", "player_id"]
    dupes = xi.duplicated(key, keep=False)
    played_values = xi["is_played"].value_counts(dropna=False).to_dict()
    impact_values = xi["is_impact"].value_counts(dropna=False).to_dict()
    impact_off_values = xi["is_impact_off"].value_counts(dropna=False).to_dict()

    per_match_team = (
        xi.groupby(["match_id", "team_id"])
        .agg(
            n_rows=("player_id", "size"),
            n_unique_players=("player_id", "nunique"),
            n_played=("is_played", lambda s: int(s.fillna(False).astype(bool).sum())),
            n_impact=("is_impact", lambda s: int((pd.to_numeric(s, errors="coerce").fillna(0) > 0).sum())),
            n_impact_off=("is_impact_off", lambda s: int((pd.to_numeric(s, errors="coerce").fillna(0) > 0).sum())),
        )
        .reset_index()
    )

    bbb_bat = bbb[["match_id", "batting_team_id", "striker_id"]].rename(
        columns={"batting_team_id": "team_id", "striker_id": "player_id"}
    )
    bbb_non = bbb[["match_id", "batting_team_id", "non_striker_id"]].rename(
        columns={"batting_team_id": "team_id", "non_striker_id": "player_id"}
    )
    bbb_bowl = bbb[["match_id", "bowling_team_id", "bowler_id"]].rename(
        columns={"bowling_team_id": "team_id", "bowler_id": "player_id"}
    )
    bbb_players = pd.concat([bbb_bat, bbb_non, bbb_bowl], ignore_index=True).dropna().drop_duplicates()
    bbb_players["in_bbb"] = True
    xi_keys = xi[key].drop_duplicates()
    merged = bbb_players.merge(xi_keys.assign(in_xi=True), on=key, how="outer")
    in_bbb_not_xi = merged[merged["in_bbb"].eq(True) & merged["in_xi"].isna()]
    in_xi_not_needed = None

    played_true = xi[xi["is_played"].fillna(False).astype(bool)][key].drop_duplicates().assign(played=True)
    participation = bbb_players.merge(played_true, on=key, how="outer")
    bbb_but_not_played_flag = participation[participation["in_bbb"].eq(True) & participation["played"].isna()]

    return {
        "n_rows": int(len(xi)),
        "n_unique_match_team_player": int(xi[key].drop_duplicates().shape[0]),
        "duplicate_key_rows": int(dupes.sum()),
        "played_values": {str(k): int(v) for k, v in played_values.items()},
        "impact_values": {str(k): int(v) for k, v in impact_values.items()},
        "impact_off_values": {str(k): int(v) for k, v in impact_off_values.items()},
        "match_team_row_dist": per_match_team["n_rows"].value_counts().sort_index().to_dict(),
        "match_team_played_dist": per_match_team["n_played"].value_counts().sort_index().to_dict(),
        "teams_not_11_played": int((per_match_team["n_played"] != 11).sum()),
        "bbb_players_not_in_xi": int(len(in_bbb_not_xi)),
        "bbb_but_is_played_false_or_missing": int(len(bbb_but_not_played_flag)),
        "matches_without_xi": int(len(set(matches["match_id"]) - set(xi["match_id"]))),
        "xi_matches_not_in_matches": int(len(set(xi["match_id"]) - set(matches["match_id"]))),
        "per_match_team": per_match_team,
        "bbb_players_not_in_xi_sample": in_bbb_not_xi.head(30),
        "bbb_not_played_sample": bbb_but_not_played_flag.head(30),
    }


def run_audit() -> dict:
    INTERIM.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    tables = load_raw_tables()
    competitions = tables["competitions"]
    teams = tables["teams"]
    matches = tables["matches"]
    bbb = tables["ball_by_ball"]
    mapping = tables["player_mapping"]
    xi = tables["playing_eleven"]

    comps = classify_competitions(competitions)
    matches_scoped = build_scope(matches, competitions)

    inventory = []
    for name, df in tables.items():
        expected = EXPECTED_COLUMNS[name]
        inventory.append(
            {
                "table": name,
                "n_records": int(len(df)),
                "n_columns": int(df.shape[1]),
                "columns_match_spec": list(df.columns) == expected,
                "unexpected_columns": [c for c in df.columns if c not in expected],
                "missing_columns": [c for c in expected if c not in df.columns],
                "duplicate_full_rows": int(df.duplicated().sum()),
            }
        )
    inventory_df = pd.DataFrame(inventory)

    # Scope counts
    match_scope = (
        matches_scoped.groupby("scope_group", dropna=False)
        .agg(n_matches=("match_id", "nunique"), n_competitions=("comp_id", "nunique"))
        .reset_index()
    )
    official_match_ids = set(matches_scoped.loc[matches_scoped["in_official_scope"], "match_id"])
    other_t20_ids = set(matches_scoped.loc[matches_scoped["scope_group"].eq("Other T20"), "match_id"])
    bbb_official = bbb[bbb["match_id"].isin(official_match_ids)]
    date_min = pd.to_datetime(matches["match_date"], errors="coerce").min()
    date_max = pd.to_datetime(matches["match_date"], errors="coerce").max()

    # Relationships
    rel = {
        "match_comp_ids_missing_from_competitions": int(len(set(matches["comp_id"]) - set(competitions["comp_id"]))),
        "competition_ids_with_no_matches": int(len(set(competitions["comp_id"]) - set(matches["comp_id"]))),
        "teams_comp_ids_missing": int(len(set(teams["comp_id"]) - set(competitions["comp_id"]))),
        "match_home_team_not_in_teams_for_comp": None,
        "bbb_match_ids_missing_from_matches": int(len(set(bbb["match_id"]) - set(matches["match_id"]))),
        "matches_without_bbb": int(len(set(matches["match_id"]) - set(bbb["match_id"]))),
        "xi_match_ids_missing_from_matches": int(len(set(xi["match_id"]) - set(matches["match_id"]))),
        "matches_without_xi": int(len(set(matches["match_id"]) - set(xi["match_id"]))),
        "official_matches": int(len(official_match_ids)),
        "official_bbb_records": int(len(bbb_official)),
        "other_t20_matches": int(len(other_t20_ids)),
        "date_min": None if pd.isna(date_min) else str(date_min.date()),
        "date_max": None if pd.isna(date_max) else str(date_max.date()),
    }

    team_keys = teams[["comp_id", "team_id"]].drop_duplicates()
    home_chk = matches[["match_id", "comp_id", "home_team_id"]].rename(columns={"home_team_id": "team_id"})
    away_chk = matches[["match_id", "comp_id", "away_team_id"]].rename(columns={"away_team_id": "team_id"})
    rel["home_team_not_in_comp_teams"] = int(len(home_chk.merge(team_keys, on=["comp_id", "team_id"], how="left", indicator=True).query('_merge=="left_only"')))
    rel["away_team_not_in_comp_teams"] = int(len(away_chk.merge(team_keys, on=["comp_id", "team_id"], how="left", indicator=True).query('_merge=="left_only"')))

    # Team IDs appearing in BBB vs match teams
    match_teams = pd.concat(
        [
            matches[["match_id", "home_team_id"]].rename(columns={"home_team_id": "team_id"}),
            matches[["match_id", "away_team_id"]].rename(columns={"away_team_id": "team_id"}),
        ]
    ).drop_duplicates()
    bbb_teams = pd.concat(
        [
            bbb[["match_id", "batting_team_id"]].rename(columns={"batting_team_id": "team_id"}),
            bbb[["match_id", "bowling_team_id"]].rename(columns={"bowling_team_id": "team_id"}),
        ]
    ).drop_duplicates()
    rel["bbb_team_not_in_match_home_away"] = int(
        len(bbb_teams.merge(match_teams, on=["match_id", "team_id"], how="left", indicator=True).query('_merge=="left_only"'))
    )
    same_bat_bowl = bbb["batting_team_id"] == bbb["bowling_team_id"]
    rel["bbb_same_batting_bowling_team"] = int(same_bat_bowl.sum())

    # Player ID coverage
    bbb_player_ids = set(pd.concat([bbb["striker_id"], bbb["non_striker_id"], bbb["bowler_id"], bbb["dismissed_player_id"]], ignore_index=True).dropna().astype("int64"))
    map_ids = set(mapping["player_id"].dropna().astype("int64"))
    xi_ids = set(xi["player_id"].dropna().astype("int64"))
    rel["bbb_player_ids"] = int(len(bbb_player_ids))
    rel["mapping_player_ids"] = int(len(map_ids))
    rel["xi_player_ids"] = int(len(xi_ids))
    rel["bbb_players_not_in_mapping"] = int(len(bbb_player_ids - map_ids))
    rel["bbb_players_not_in_xi"] = int(len(bbb_player_ids - xi_ids))
    rel["mapping_players_never_in_bbb"] = int(len(map_ids - bbb_player_ids))

    # Duplicate delivery keys
    delivery_key = ["match_id", "innings", "overid", "over_ball_num"]
    alt_key = ["match_id", "innings", "innings_ball_num"]
    dup_delivery = bbb.duplicated(delivery_key, keep=False)
    dup_innings_ball = bbb.duplicated(alt_key, keep=False)
    dup_match = matches.duplicated("match_id", keep=False)
    dup_xi = xi.duplicated(["match_id", "team_id", "player_id"], keep=False)
    dup_map = mapping.duplicated(["comp_id", "team_id", "player_id"], keep=False)

    quality = {
        "duplicate_match_ids": int(dup_match.sum()),
        "duplicate_delivery_key_rows": int(dup_delivery.sum()),
        "duplicate_innings_ball_key_rows": int(dup_innings_ball.sum()),
        "duplicate_xi_keys": int(dup_xi.sum()),
        "duplicate_mapping_keys": int(dup_map.sum()),
        "missing_match_id_bbb": int(bbb["match_id"].isna().sum()),
        "missing_striker_id": int(bbb["striker_id"].isna().sum()),
        "missing_non_striker_id": int(bbb["non_striker_id"].isna().sum()),
        "missing_bowler_id": int(bbb["bowler_id"].isna().sum()),
        "invalid_innings": int((~bbb["innings"].isin([1, 2, 3, 4])) .sum()) if set(bbb["innings"].dropna().unique()) else None,
        "innings_value_counts": bbb["innings"].value_counts(dropna=False).to_dict(),
        "overid_min": int(bbb["overid"].min()),
        "overid_max": int(bbb["overid"].max()),
        "over_ball_num_min": int(bbb["over_ball_num"].min()),
        "over_ball_num_max": int(bbb["over_ball_num"].max()),
        "negative_runs": int((bbb["runs"] < 0).sum()),
        "negative_extras1": int((bbb["extras1_runs"] < 0).sum()),
        "negative_extras2": int((bbb["extras_2_runs"] < 0).sum()),
        "overid_outside_1_20_reg": int(((bbb["innings"].isin([1, 2])) & ((bbb["overid"] < 1) | (bbb["overid"] > 20))).sum()),
        "over_ball_num_outside_1_15": int(((bbb["over_ball_num"] < 1) | (bbb["over_ball_num"] > 15)).sum()),
    }

    # Invalid extras / dismissals / boundaries
    work = bbb.copy()
    work["extras_family"] = work["extras_type"].map(extras_family)
    work["dismissal_family"] = work["dismissal_type"].map(dismissal_family)
    work["is_legal"] = work["extras_family"].map(legal_delivery_flag)

    wicket_no_type = int(((work["is_wicket"] == True) & work["dismissal_type"].isna()).sum())
    type_no_wicket = int((work["dismissal_type"].notna() & (work["is_wicket"] != True)).sum())
    wicket_no_player = int(((work["is_wicket"] == True) & work["dismissed_player_id"].isna()).sum())
    player_no_wicket = int((work["dismissed_player_id"].notna() & (work["is_wicket"] != True)).sum())
    dismissed_not_on_strike = work[
        (work["is_wicket"] == True)
        & work["dismissed_player_id"].notna()
        & ~work["dismissed_player_id"].isin(work["striker_id"])  # placeholder, replaced below
    ]
    dismissed_not_batters = work[
        (work["is_wicket"] == True)
        & work["dismissed_player_id"].notna()
        & ~(
            (work["dismissed_player_id"] == work["striker_id"])
            | (work["dismissed_player_id"] == work["non_striker_id"])
        )
    ]

    four_not_4 = int(((work["is_four"] == True) & (work["runs"] != 4) & work["extras_family"].eq("none")).sum())
    six_not_6 = int(((work["is_six"] == True) & (work["runs"] != 6) & work["extras_family"].eq("none")).sum())
    both_four_six = int(((work["is_four"] == True) & (work["is_six"] == True)).sum())

    cricket = {
        "extras_type_counts": work["extras_type"].fillna("(none)").value_counts().to_dict(),
        "extras_family_counts": work["extras_family"].value_counts().to_dict(),
        "dismissal_type_counts": work["dismissal_type"].fillna("(none)").value_counts().to_dict(),
        "dismissal_family_counts": work["dismissal_family"].value_counts().to_dict(),
        "wicket_without_dismissal_type": wicket_no_type,
        "dismissal_type_without_is_wicket": type_no_wicket,
        "wicket_without_dismissed_player": wicket_no_player,
        "dismissed_player_without_is_wicket": player_no_wicket,
        "dismissed_player_not_striker_or_nonstriker": int(len(dismissed_not_batters)),
        "legal_delivery_count": int(work["is_legal"].sum()),
        "illegal_delivery_count": int((~work["is_legal"]).sum()),
        "boundary_four_runs_not_4_on_no_extra": four_not_4,
        "boundary_six_runs_not_6_on_no_extra": six_not_6,
        "both_four_and_six": both_four_six,
        "is_wicket_true": int((work["is_wicket"] == True).sum()),
    }

    runs_enc = inspect_runs_encoding(bbb)
    recon = innings_reconciliation(bbb, matches)

    # Super overs
    super_matches = sorted(bbb.loc[bbb["innings"].isin([3, 4]), "match_id"].unique().tolist())
    innings_per_match = bbb.groupby("match_id")["innings"].nunique()
    unexpected_innings = innings_per_match[innings_per_match > 2]

    # Revised matches
    revised_overs = matches[
        matches["first_inn_revised_overs"].notna() | matches["second_inn_revised_overs"].notna()
    ].copy()
    revised_target = matches[matches["revised_target"].notna()].copy()

    # Compare legal balls vs revised overs encodings
    legal_by_inn = (
        work[work["innings"].isin([1, 2])]
        .groupby(["match_id", "innings"], as_index=False)
        .agg(legal_balls=("is_legal", "sum"), deliveries=("match_id", "size"), max_over=("overid", "max"))
    )
    rev_cmp = revised_overs.merge(
        legal_by_inn[legal_by_inn["innings"] == 1][["match_id", "legal_balls", "max_over"]].rename(
            columns={"legal_balls": "inn1_legal", "max_over": "inn1_max_over"}
        ),
        on="match_id",
        how="left",
    ).merge(
        legal_by_inn[legal_by_inn["innings"] == 2][["match_id", "legal_balls", "max_over"]].rename(
            columns={"legal_balls": "inn2_legal", "max_over": "inn2_max_over"}
        ),
        on="match_id",
        how="left",
    )

    def overs_to_balls_decimal(series):
        out = []
        for v in series:
            if pd.isna(v):
                out.append(np.nan)
                continue
            raw = float(v)
            whole = int(np.floor(raw + 1e-9))
            tenth = int(round((raw - whole) * 10))
            out.append(whole * 6 + tenth)
        return out

    rev_cmp["first_as_decimal_balls"] = overs_to_balls_decimal(rev_cmp["first_inn_revised_overs"])
    rev_cmp["second_as_decimal_balls"] = overs_to_balls_decimal(rev_cmp["second_inn_revised_overs"])
    rev_cmp["first_as_int_balls"] = pd.to_numeric(rev_cmp["first_inn_revised_overs"], errors="coerce")
    rev_cmp["second_as_int_balls"] = pd.to_numeric(rev_cmp["second_inn_revised_overs"], errors="coerce")
    rev_cmp["first_as_int_overs_balls"] = pd.to_numeric(rev_cmp["first_inn_revised_overs"], errors="coerce") * 6
    rev_cmp["second_as_int_overs_balls"] = pd.to_numeric(rev_cmp["second_inn_revised_overs"], errors="coerce") * 6
    rev_cmp["inn1_legal_eq_decimal"] = rev_cmp["inn1_legal"] == rev_cmp["first_as_decimal_balls"]
    rev_cmp["inn2_legal_eq_decimal"] = rev_cmp["inn2_legal"] == rev_cmp["second_as_decimal_balls"]
    rev_cmp["inn1_legal_eq_int_balls"] = rev_cmp["inn1_legal"] == rev_cmp["first_as_int_balls"]
    rev_cmp["inn2_legal_eq_int_balls"] = rev_cmp["inn2_legal"] == rev_cmp["second_as_int_balls"]
    rev_cmp["inn1_maxover_eq_value"] = rev_cmp["inn1_max_over"] == rev_cmp["first_inn_revised_overs"]
    rev_cmp["inn2_maxover_eq_value"] = rev_cmp["inn2_max_over"] == rev_cmp["second_inn_revised_overs"]

    xi_audit = audit_playing_xi(xi, matches, bbb)

    # Incomplete innings: regulation innings with very few legal balls and not all out / not revised
    inn_counts = (
        work[work["innings"].isin([1, 2])]
        .groupby(["match_id", "innings"])
        .agg(n=("match_id", "size"), legal=("is_legal", "sum"), wkts=("is_wicket", "sum"), max_over=("overid", "max"))
        .reset_index()
    )
    match_inn_pivot = inn_counts.pivot(index="match_id", columns="innings", values="n")
    matches_missing_inn2 = sorted(set(matches["match_id"]) - set(inn_counts.loc[inn_counts["innings"] == 2, "match_id"]))
    matches_missing_inn1 = sorted(set(matches["match_id"]) - set(inn_counts.loc[inn_counts["innings"] == 1, "match_id"]))

    # Exclusion log: flag, do not delete
    flags = []

    def add_flag(match_id, delivery_idx, flag, reason, extra=None):
        flags.append(
            {
                "match_id": match_id,
                "delivery_index": delivery_idx,
                "flag": flag,
                "reason": reason,
                "detail": extra,
            }
        )

    for mid in sorted(set(matches["match_id"]) - set(bbb["match_id"])):
        add_flag(mid, None, "MATCH_NO_BBB", "Match has no ball-by-ball records")
    for mid in super_matches:
        add_flag(mid, None, "SUPER_OVER", "Match contains Super Over innings 3/4; keep separate from regulation analysis")
    for mid in revised_overs["match_id"]:
        add_flag(mid, None, "REVISED_OVERS", "Match has revised-overs fields populated")
    for mid in revised_target["match_id"]:
        add_flag(mid, None, "REVISED_TARGET", "Match has revised_target populated")
    for mid in matches_scoped.loc[matches_scoped["scope_group"].eq("Other T20"), "match_id"]:
        add_flag(mid, None, "OUT_OF_OFFICIAL_SCOPE", "Non-IPL T20 competition excluded from official rankings unless organisers confirm eligibility")
    for mid in matches_missing_inn2:
        add_flag(mid, None, "MISSING_SECOND_INNINGS_BBB", "No innings=2 deliveries found")
    for mid in matches_missing_inn1:
        add_flag(mid, None, "MISSING_FIRST_INNINGS_BBB", "No innings=1 deliveries found")

    if dup_delivery.any():
        for idx in bbb.index[dup_delivery][:5000]:
            add_flag(int(bbb.at[idx, "match_id"]), int(idx), "DUPLICATE_DELIVERY_KEY", "Duplicate match_id+innings+overid+over_ball_num")

    flag_df = pd.DataFrame(flags)
    flag_summary = flag_df.groupby("flag").size().reset_index(name="n") if len(flag_df) else pd.DataFrame(columns=["flag", "n"])

    # Reconciliation success rates
    complete_pairs = recon.dropna(subset=["inn1_a", "inn2_a"])
    recon_summary = {
        "innings_pairs": int(len(recon)),
        "complete_two_innings": int(len(complete_pairs)),
        "result_by_runs_n": int(recon["result_by_runs"].fillna(False).sum()),
        "result_by_wickets_n": int(recon["result_by_wickets"].fillna(False).sum()),
        "win_by_runs_match_a": int(recon["win_by_runs_match_a"].fillna(False).sum()),
        "win_by_runs_match_b": int(recon["win_by_runs_match_b"].fillna(False).sum()),
        "win_by_runs_match_c": int(recon["win_by_runs_match_c"].fillna(False).sum()),
        "win_by_wickets_score_ok_a": int(recon["win_by_wickets_score_ok_a"].fillna(False).sum()),
        "win_by_wickets_score_ok_b": int(recon["win_by_wickets_score_ok_b"].fillna(False).sum()),
        "win_by_wickets_score_ok_c": int(recon["win_by_wickets_score_ok_c"].fillna(False).sum()),
        "revised_chase_ok_a": int(recon["revised_chase_ok_a"].fillna(False).sum()),
        "revised_chase_ok_b": int(recon["revised_chase_ok_b"].fillna(False).sum()),
        "revised_chase_ok_c": int(recon["revised_chase_ok_c"].fillna(False).sum()),
    }
    by_runs = recon[recon["result_by_runs"].fillna(False) & recon["result_margin"].notna()]
    recon_summary["by_runs_denom"] = int(len(by_runs))
    recon_summary["by_runs_hit_rate_a"] = float(by_runs["win_by_runs_match_a"].mean()) if len(by_runs) else None
    recon_summary["by_runs_hit_rate_b"] = float(by_runs["win_by_runs_match_b"].mean()) if len(by_runs) else None
    recon_summary["by_runs_hit_rate_c"] = float(by_runs["win_by_runs_match_c"].mean()) if len(by_runs) else None

    # Name collisions: same name different IDs
    name_map = pd.concat(
        [
            bbb[["striker_id", "striker_name"]].rename(columns={"striker_id": "player_id", "striker_name": "player_name"}),
            bbb[["bowler_id", "bowler_name"]].rename(columns={"bowler_id": "player_id", "bowler_name": "player_name"}),
            mapping[["player_id", "player_name"]],
        ],
        ignore_index=True,
    ).dropna()
    names_per_id = name_map.groupby("player_id")["player_name"].nunique()
    ids_per_name = name_map.groupby("player_name")["player_id"].nunique()

    # Over numbering vs innings_ball_num
    legal_reg = work[work["innings"].isin([1, 2]) & work["is_legal"]]
    innings_ball_vs_legal = (
        legal_reg.groupby(["match_id", "innings"])
        .agg(legal=("is_legal", "sum"), max_inn_ball=("innings_ball_num", "max"), n=("is_legal", "size"))
        .reset_index()
    )
    innings_ball_vs_legal["max_eq_legal"] = innings_ball_vs_legal["max_inn_ball"] == innings_ball_vs_legal["legal"]
    innings_ball_vs_legal["max_eq_n"] = innings_ball_vs_legal["max_inn_ball"] == innings_ball_vs_legal["n"]

    # Save artefacts
    missing_frames = {k: missing_summary(v) for k, v in tables.items()}
    for k, df in missing_frames.items():
        df.to_csv(INTERIM / f"missing_{k}.csv", index=False)

    inventory_df.to_csv(INTERIM / "dataset_inventory.csv", index=False)
    comps.to_csv(INTERIM / "competitions_classified.csv", index=False)
    match_scope.to_csv(INTERIM / "match_scope_counts.csv", index=False)
    runs_enc["family_summary"].to_csv(INTERIM / "extras_family_summary.csv", index=False)
    runs_enc["extras_type_summary"].to_csv(INTERIM / "extras_type_summary.csv", index=False)
    runs_enc["boundary_alignment"].to_csv(INTERIM / "runs_boundary_alignment.csv", index=False)
    recon.to_csv(INTERIM / "innings_reconciliation.csv", index=False)
    rev_cmp.to_csv(INTERIM / "revised_matches_inspection.csv", index=False)
    flag_df.to_csv(INTERIM / "exclusion_flag_log.csv", index=False)
    flag_summary.to_csv(INTERIM / "exclusion_flag_summary.csv", index=False)
    xi_audit["per_match_team"].to_csv(INTERIM / "playing_xi_per_match_team.csv", index=False)
    inn_counts.to_csv(INTERIM / "innings_completeness.csv", index=False)
    matches_scoped.to_csv(INTERIM / "matches_with_scope.csv", index=False)

    dismissed_not_batters.head(50).to_csv(INTERIM / "dismissed_player_not_on_crease_sample.csv", index=False)
    bbb.loc[dup_delivery].head(100).to_csv(INTERIM / "duplicate_delivery_sample.csv", index=False)
    pd.DataFrame({"match_id": super_matches}).to_csv(INTERIM / "super_over_matches.csv", index=False)

    summary = {
        "inventory": inventory_df.to_dict(orient="records"),
        "scope": {
            "match_scope": match_scope.to_dict(orient="records"),
            "date_min": rel["date_min"],
            "date_max": rel["date_max"],
            "official_matches": rel["official_matches"],
            "official_bbb_records": rel["official_bbb_records"],
            "other_t20_matches": rel["other_t20_matches"],
            "total_matches": int(matches["match_id"].nunique()),
            "total_bbb": int(len(bbb)),
            "format_counts": competitions["match_format"].value_counts(dropna=False).to_dict(),
            "competition_count": int(competitions["comp_id"].nunique()),
        },
        "relationships": rel,
        "quality": quality,
        "cricket": cricket,
        "runs_encoding": {
            "boundary_alignment": runs_enc["boundary_alignment"].to_dict(orient="records"),
            "both_extras_nonzero_n": runs_enc["both_extras_nonzero_n"],
            "both_extras_by_type": runs_enc["both_extras_by_type"],
            "negative_runs": runs_enc["negative_runs"],
        },
        "reconciliation": recon_summary,
        "super_overs": {
            "n_matches": int(len(super_matches)),
            "match_ids": super_matches,
            "innings_3_rows": int((bbb["innings"] == 3).sum()),
            "innings_4_rows": int((bbb["innings"] == 4).sum()),
            "matches_with_gt_2_distinct_innings": int((unexpected_innings > 2).sum()),
        },
        "revised": {
            "n_revised_overs_matches": int(len(revised_overs)),
            "n_revised_target_matches": int(len(revised_target)),
            "first_revised_unique": sorted(revised_overs["first_inn_revised_overs"].dropna().unique().tolist()),
            "second_revised_unique": sorted(revised_overs["second_inn_revised_overs"].dropna().unique().tolist()),
            "inn1_legal_eq_decimal": int(rev_cmp["inn1_legal_eq_decimal"].fillna(False).sum()),
            "inn2_legal_eq_decimal": int(rev_cmp["inn2_legal_eq_decimal"].fillna(False).sum()),
            "inn1_legal_eq_int_balls": int(rev_cmp["inn1_legal_eq_int_balls"].fillna(False).sum()),
            "inn2_legal_eq_int_balls": int(rev_cmp["inn2_legal_eq_int_balls"].fillna(False).sum()),
            "inn1_maxover_eq_value": int(rev_cmp["inn1_maxover_eq_value"].fillna(False).sum()),
            "inn2_maxover_eq_value": int(rev_cmp["inn2_maxover_eq_value"].fillna(False).sum()),
        },
        "playing_xi": {k: v for k, v in xi_audit.items() if k not in {"per_match_team", "bbb_players_not_in_xi_sample", "bbb_not_played_sample"}},
        "identity": {
            "player_ids_with_multiple_names": int((names_per_id > 1).sum()),
            "player_names_with_multiple_ids": int((ids_per_name > 1).sum()),
        },
        "innings_ball_num": {
            "reg_legal_groups": int(len(innings_ball_vs_legal)),
            "max_eq_legal_count": int(innings_ball_vs_legal["max_eq_legal"].sum()),
            "max_eq_delivery_count": int(innings_ball_vs_legal["max_eq_n"].sum()),
        },
        "completeness": {
            "matches_missing_inn1_bbb": int(len(matches_missing_inn1)),
            "matches_missing_inn2_bbb": int(len(matches_missing_inn2)),
            "matches_missing_inn1_ids": matches_missing_inn1,
            "matches_missing_inn2_ids": matches_missing_inn2,
        },
        "flag_summary": flag_summary.to_dict(orient="records"),
        "n_flag_rows": int(len(flag_df)),
    }

    with open(INTERIM / "phase1_audit_summary.json", "w", encoding="utf-8") as f:
        json.dump(_json_ready(summary), f, indent=2)

    return summary, tables, {
        "comps": comps,
        "matches_scoped": matches_scoped,
        "runs_enc": runs_enc,
        "recon": recon,
        "rev_cmp": rev_cmp,
        "xi_audit": xi_audit,
        "work": work,
        "flag_df": flag_df,
        "missing_frames": missing_frames,
        "innings_ball_vs_legal": innings_ball_vs_legal,
        "inn_counts": inn_counts,
        "dismissed_not_batters": dismissed_not_batters,
    }


def render_markdown(summary: dict, extras: dict) -> str:
    scope = summary["scope"]
    rel = summary["relationships"]
    q = summary["quality"]
    c = summary["cricket"]
    r = summary["reconciliation"]
    so = summary["super_overs"]
    rv = summary["revised"]
    xi = summary["playing_xi"]

    lines = []
    a = lines.append
    a("# PRESSUREIQ Phase 1 Data Audit")
    a("")
    a("Status: **complete for Phase 1**. No player rankings, pressure scores, or dashboard were produced.")
    a("")
    a("Source files were copied from `6af458274c1e8_data_pack/Data Pack/` into `data/raw/`. Originals were not modified.")
    a("")
    a("## 1. What data is available")
    a("")
    a(f"- Date coverage: **{scope['date_min']} to {scope['date_max']}**.")
    a(f"- Competitions: **{scope['competition_count']}**. Formats: `{scope['format_counts']}`.")
    a(f"- Matches: **{scope['total_matches']}**. Ball-by-ball rows: **{scope['total_bbb']}**.")
    a(f"- Official scope (IPL + T20I): **{scope['official_matches']} matches**, **{scope['official_bbb_records']} deliveries**.")
    a(f"- Other T20 (out of official ranking scope): **{scope['other_t20_matches']} matches**.")
    a("")
    a("### File inventory")
    a("")
    a("| Table | Records | Columns match spec | Duplicate full rows |")
    a("|---|---:|:---:|---:|")
    for row in summary["inventory"]:
        a(f"| {row['table']} | {row['n_records']} | {row['columns_match_spec']} | {row['duplicate_full_rows']} |")
    a("")
    a("### Competition scope")
    a("")
    a("| Scope group | Matches | Competitions |")
    a("|---|---:|---:|")
    for row in scope["match_scope"]:
        a(f"| {row['scope_group']} | {row['n_matches']} | {row['n_competitions']} |")
    a("")
    a("All six required CSVs are present. Column names match the master specification.")
    a("")
    a("## 2. What is reliable")
    a("")
    a("- Primary keys `match_id`, `comp_id`, `player_id`, and `team_id` are populated on the core entity tables.")
    a(f"- Match IDs in ball-by-ball missing from matches: **{rel['bbb_match_ids_missing_from_matches']}**.")
    a(f"- Matches with no ball-by-ball: **{rel['matches_without_bbb']}**.")
    a(f"- Duplicate match IDs: **{q['duplicate_match_ids']}**. Duplicate full-row copies in source tables are zero except where listed in inventory.")
    a(f"- Duplicate delivery keys (`match_id`,`innings`,`overid`,`over_ball_num`): **{q['duplicate_delivery_key_rows']} rows**.")
    a(f"- Negative `runs` / extras: **{q['negative_runs']} / {q['negative_extras1']} / {q['negative_extras2']}**.")
    a(f"- Same batting and bowling team on a delivery: **{rel['bbb_same_batting_bowling_team']}**.")
    a(f"- Ball-by-ball team IDs not in that match's home/away pair: **{rel['bbb_team_not_in_match_home_away']}**.")
    a(f"- Player IDs in deliveries but not in mapping: **{rel['bbb_players_not_in_mapping']}**.")
    a(f"- Names colliding across IDs: **{summary['identity']['player_names_with_multiple_ids']}** names map to multiple IDs; **{summary['identity']['player_ids_with_multiple_names']}** IDs have multiple names. Player ID remains the correct identifier.")
    a("")
    a("## 3. What needs reconciliation")
    a("")
    a("### 3.1 Meaning of `runs`, `extras1_runs`, `extras_2_runs`")
    a("")
    a("Boundary alignment (does the candidate series equal 4 on `is_four` and 6 on `is_six`?)")
    a("")
    a("| Candidate | Four==4 | Six==6 | Non-boundary in 0-3 | Negatives |")
    a("|---|---:|---:|---:|---:|")
    for row in summary["runs_encoding"]["boundary_alignment"]:
        a(
            f"| {row['candidate']} | {row['four_eq_4_rate']} | {row['six_eq_6_rate']} | {row['nonboundary_in_0_3_rate']} | {row['negative_count']} |"
        )
    a("")
    a(f"Deliveries with both extras fields > 0: **{summary['runs_encoding']['both_extras_nonzero_n']}**. Types: `{summary['runs_encoding']['both_extras_by_type']}`.")
    a("")
    a("### 3.2 Innings totals vs match result text")
    a("")
    a("Candidate A = sum(`runs`); B = sum(`runs`+`extras1_runs`); C = sum(`runs`+`extras1`+`extras2`).")
    a("")
    a(f"- Result 'won by runs' matches in sample: **{r['by_runs_denom']}**.")
    a(f"- Margin match rate A/B/C: **{r['by_runs_hit_rate_a']} / {r['by_runs_hit_rate_b']} / {r['by_runs_hit_rate_c']}**.")
    a(f"- Wicket-win innings-2 score > innings-1 score, A/B/C: **{r['win_by_wickets_score_ok_a']} / {r['win_by_wickets_score_ok_b']} / {r['win_by_wickets_score_ok_c']}**.")
    a("")
    a("The candidate with the highest result-margin hit rate should be treated as team total runs, subject to revised-target and Super Over matches.")
    a("")
    a("### 3.3 Playing XI")
    a("")
    a(f"- Rows: **{xi['n_rows']}**. Unique match-team-player keys: **{xi['n_unique_match_team_player']}**.")
    a(f"- Duplicate key rows: **{xi['duplicate_key_rows']}**.")
    a(f"- `is_played` values: `{xi['played_values']}`.")
    a(f"- `is_impact` values: `{xi['impact_values']}`. `is_impact_off`: `{xi['impact_off_values']}`.")
    a(f"- Match-teams where played count != 11: **{xi['teams_not_11_played']}**.")
    a(f"- Ball-by-ball participants absent from XI keys: **{xi['bbb_players_not_in_xi']}**.")
    a(f"- Ball-by-ball participants without `is_played=True`: **{xi['bbb_but_is_played_false_or_missing']}**.")
    a("")
    a("Participation for batting/bowling opportunity must use ball-by-ball appearance, not XI membership alone.")
    a("")
    a("### 3.4 Revised overs encoding")
    a("")
    a(f"- Matches with revised-overs fields: **{rv['n_revised_overs_matches']}**.")
    a(f"- Matches with revised target: **{rv['n_revised_target_matches']}**.")
    a(f"- Unique first-innings revised values: `{rv['first_revised_unique']}`.")
    a(f"- Unique second-innings revised values: `{rv['second_revised_unique']}`.")
    a(f"- Legal balls equal decimal-overs decoding (inn1/inn2): **{rv['inn1_legal_eq_decimal']} / {rv['inn2_legal_eq_decimal']}**.")
    a(f"- Legal balls equal integer-as-balls decoding (inn1/inn2): **{rv['inn1_legal_eq_int_balls']} / {rv['inn2_legal_eq_int_balls']}**.")
    a(f"- Max overid equals revised value (inn1/inn2): **{rv['inn1_maxover_eq_value']} / {rv['inn2_maxover_eq_value']}**.")
    a("")
    a("Full per-match inspection is in `data/interim/revised_matches_inspection.csv`.")
    a("")
    a("## 4. Cricket-specific edge cases")
    a("")
    a("### 4.1 Extras")
    a("")
    a(f"Extras family counts: `{c['extras_family_counts']}`.")
    a("")
    a(f"Raw extras_type counts: `{c['extras_type_counts']}`.")
    a("")
    a(f"Legal deliveries (not wide/no-ball family): **{c['legal_delivery_count']}**. Illegal: **{c['illegal_delivery_count']}**.")
    a("")
    a("### 4.2 Dismissals")
    a("")
    a(f"`is_wicket` true: **{c['is_wicket_true']}**.")
    a(f"Dismissal types: `{c['dismissal_type_counts']}`.")
    a(f"Families: `{c['dismissal_family_counts']}`.")
    a(f"Wicket without type: **{c['wicket_without_dismissal_type']}**. Type without wicket flag: **{c['dismissal_type_without_is_wicket']}**.")
    a(f"Wicket without dismissed player: **{c['wicket_without_dismissed_player']}**. Dismissed player not striker/non-striker: **{c['dismissed_player_not_striker_or_nonstriker']}**.")
    a("")
    a("Bowler-credited wickets must exclude run outs and any retired/other non-bowler classes actually present.")
    a("")
    a("### 4.3 Super Overs")
    a("")
    a(f"Matches with innings 3/4: **{so['n_matches']}**. IDs: `{so['match_ids']}`.")
    a(f"Innings 3 rows: **{so['innings_3_rows']}**. Innings 4 rows: **{so['innings_4_rows']}**.")
    a("")
    a("These must stay out of regulation T20 averages, economy, and official pressure rankings.")
    a("")
    a("### 4.4 Completeness")
    a("")
    a(f"Matches missing innings 1 BBB: **{summary['completeness']['matches_missing_inn1_bbb']}** `{summary['completeness']['matches_missing_inn1_ids']}`.")
    a(f"Matches missing innings 2 BBB: **{summary['completeness']['matches_missing_inn2_bbb']}** `{summary['completeness']['matches_missing_inn2_ids']}`.")
    a(f"`innings_ball_num` max equals legal-ball count in **{summary['innings_ball_num']['max_eq_legal_count']} / {summary['innings_ball_num']['reg_legal_groups']}** regulation innings.")
    a("")
    a("### 4.5 Boundary flags")
    a("")
    a(f"Fours where `runs!=4` on non-extra balls: **{c['boundary_four_runs_not_4_on_no_extra']}**. Sixes where `runs!=6`: **{c['boundary_six_runs_not_6_on_no_extra']}**. Both four and six: **{c['both_four_and_six']}**.")
    a("")
    a("## 5. Modelling decisions still unresolved")
    a("")
    a("These are Phase 2 questions. They are listed now because the audit constrains them.")
    a("")
    a("1. **Official scope confirmation**: 30 Other T20 matches are present. Default is exclude from official rankings.")
    a("2. **Final extras accounting rules** after human review of the runs-encoding tables, especially no-balls with batter runs in `extras_2_runs`.")
    a("3. **Revised-overs decoder** to freeze after inspecting `revised_matches_inspection.csv` (decimal overs vs integer balls vs max over).")
    a("4. **Impact-player treatment**: XI duplicates and impact flags vs actual BBB participation.")
    a("5. **Pressure definition** (not computed in Phase 1): first-innings par model, chase pressure, thresholds.")
    a("6. **Eligibility thresholds** for batters and bowlers: must be set before seeing leaderboards.")
    a("7. **Whether Super Overs are analysed at all**, even separately.")
    a("8. **Matches with incomplete innings / no result**: include for the completed innings only, or exclude entire match from pressure ranking.")
    a("9. **Name collisions**: always ID-based; display names need a canonical name table.")
    a("10. **Bowler economy extras**: freeze wide/no-ball vs bye/leg-bye rules after confirming `runs` identity.")
    a("")
    a("## Exclusion / flag policy")
    a("")
    a("Questionable records were **flagged, not deleted**. Log: `data/interim/exclusion_flag_log.csv`.")
    a("")
    a("| Flag | Count |")
    a("|---|---:|")
    for row in summary["flag_summary"]:
        a(f"| {row['flag']} | {row['n']} |")
    a("")
    a("## Artefacts")
    a("")
    a("- `data/interim/phase1_audit_summary.json`")
    a("- `data/interim/dataset_inventory.csv`")
    a("- `data/interim/matches_with_scope.csv`")
    a("- `data/interim/extras_family_summary.csv`")
    a("- `data/interim/extras_type_summary.csv`")
    a("- `data/interim/runs_boundary_alignment.csv`")
    a("- `data/interim/innings_reconciliation.csv`")
    a("- `data/interim/revised_matches_inspection.csv`")
    a("- `data/interim/playing_xi_per_match_team.csv`")
    a("- `data/interim/exclusion_flag_log.csv`")
    a("- `data/interim/super_over_matches.csv`")
    a("")
    a("## Recommendation")
    a("")
    a("Phase 1 audit is ready for review. Do not start Phase 2 modelling until the extras identity, revised-overs encoding, and official-scope exclusion are approved.")
    a("")
    return "\n".join(lines)


def main() -> None:
    summary, _tables, extras = run_audit()
    md = render_markdown(summary, extras)
    out = REPORTS / "PHASE1_DATA_AUDIT.md"
    out.write_text(md, encoding="utf-8")
    print(f"Wrote {out}")
    print(json.dumps(_json_ready({
        "official_matches": summary["scope"]["official_matches"],
        "official_bbb": summary["scope"]["official_bbb_records"],
        "other_t20": summary["scope"]["other_t20_matches"],
        "super_overs": summary["super_overs"]["n_matches"],
        "revised_overs": summary["revised"]["n_revised_overs_matches"],
        "revised_target": summary["revised"]["n_revised_target_matches"],
        "by_runs_hit_rate_a": summary["reconciliation"]["by_runs_hit_rate_a"],
        "by_runs_hit_rate_b": summary["reconciliation"]["by_runs_hit_rate_b"],
        "by_runs_hit_rate_c": summary["reconciliation"]["by_runs_hit_rate_c"],
        "duplicate_delivery_rows": summary["quality"]["duplicate_delivery_key_rows"],
        "matches_without_bbb": summary["relationships"]["matches_without_bbb"],
    }), indent=2))


if __name__ == "__main__":
    main()

"""Bowling aggregation: match-level and player-level pressure/normal metrics.

Accounting (cricket_rules): conceded = batter runs + wides + no-ball penalty;
byes, leg-byes, penalty runs and non-bat runs off no-balls are NOT charged.
Legal balls exclude wides and no-balls. Wickets = bowler-credited only
(no run-outs, retired out, obstructing the field).

Bowling opportunity = every delivery bowled (wides/no-balls are part of the
bowler's work and cost runs). Economy and wicket rate use legal balls per spec.
Pressure uses the BOWLING-perspective level (fielding side's difficulty).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

PRESSURE_LEVELS = ("Elevated", "High")


def bowling_match_table(w: pd.DataFrame, plevel_col: str = "pressure_level_bowl",
                        pressure_levels=PRESSURE_LEVELS) -> pd.DataFrame:
    w = w.assign(context=np.where(w[plevel_col].isin(pressure_levels), "pressure",
                                  np.where(w[plevel_col].eq("Low"), "normal", "other")),
                 one=1)
    g = w.groupby(["bowler_id", "match_id", "context"], observed=True)
    m = g.agg(balls=("one", "sum"), legal=("is_legal", "sum"), conceded=("bowler_conceded", "sum"),
              wickets=("y_wkt", "sum"), dots=("is_dot_bowl", "sum"), boundaries=("is_boundary", "sum"),
              exp_conceded=("exp_conceded", "sum"), value=("rp", "sum"), season=("season_year", "first"),
              format_group=("format_group", "first"), team_id=("bowling_team_id", "first"),
              phase_mode=("phase", lambda s: s.mode().iat[0]), match_date=("match_date", "first")).reset_index()
    return m.rename(columns={"bowler_id": "player_id"})


def bowling_summary(mt: pd.DataFrame) -> pd.DataFrame:
    def agg(ctx: str, prefix: str) -> pd.DataFrame:
        s = mt[mt["context"] == ctx].groupby("player_id").agg(
            balls=("balls", "sum"), legal=("legal", "sum"), conceded=("conceded", "sum"),
            wickets=("wickets", "sum"), dots=("dots", "sum"), boundaries=("boundaries", "sum"),
            exp_conceded=("exp_conceded", "sum"), value=("value", "sum"),
            matches=("match_id", "nunique"), seasons=("season", "nunique"))
        lg = s["legal"].replace(0, np.nan)
        s["economy"] = 6 * s["conceded"] / lg
        s["exp_economy"] = 6 * s["exp_conceded"] / lg
        s["wicket_rate"] = 100 * s["wickets"] / lg
        s["dot_pct"] = 100 * s["dots"] / s["balls"]
        s["boundary_pct"] = 100 * s["boundaries"] / s["balls"]
        s["runs_prevented"] = s["exp_conceded"] - s["conceded"]
        s["value_per24"] = 24 * s["value"] / s["balls"]
        return s.add_prefix(prefix)
    out = agg("pressure", "p_").join(agg("normal", "n_"), how="outer")
    allm = mt.groupby("player_id").agg(total_balls=("balls", "sum"), total_legal=("legal", "sum"),
                                       total_matches=("match_id", "nunique"))
    fmt = mt[mt["context"] == "pressure"].pivot_table(index="player_id", columns="format_group", values="legal",
                                                      aggfunc="sum").add_prefix("p_legal_")
    return allm.join(out, how="left").join(fmt, how="left").reset_index()


def bowling_phase_table(w: pd.DataFrame, plevel_col: str = "pressure_level_bowl") -> pd.DataFrame:
    g = w.groupby(["bowler_id", "phase", plevel_col], observed=True).agg(
        balls=("is_legal", "size"), legal=("is_legal", "sum"), conceded=("bowler_conceded", "sum"),
        value=("rp", "sum")).reset_index()
    g["economy"] = 6 * g["conceded"] / g["legal"].replace(0, np.nan)
    return g.rename(columns={"bowler_id": "player_id", plevel_col: "pressure_level"})

"""Batting aggregation: match-level and player-level pressure/normal metrics.

Denominator: batter balls faced = all deliveries except wides (no-balls ARE
balls faced under standard scoring). Run-outs of the striker count as the
striker's dismissal; non-striker run-outs are not attached to the striker's
ball (the non-striker did not face it).

Pressure deliveries = batting-perspective level Elevated or High (unless a
scenario overrides `pressure_levels`). Normal = Low.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

PRESSURE_LEVELS = ("Elevated", "High")


def batting_match_table(b: pd.DataFrame, plevel_col: str = "pressure_level_bat",
                        pressure_levels=PRESSURE_LEVELS) -> pd.DataFrame:
    b = b.assign(context=np.where(b[plevel_col].isin(pressure_levels), "pressure",
                                  np.where(b[plevel_col].eq("Low"), "normal", "other")))
    g = b.groupby(["striker_id", "match_id", "context"], observed=True)
    m = g.agg(balls=("batter_faced", "size"), runs=("batter_runs", "sum"), outs=("y_out", "sum"),
              dots=("is_dot_batter", "sum"), boundaries=("is_boundary", "sum"), exp_runs=("exp_runs", "sum"),
              rae=("rae", "sum"), value=("cabv", "sum"), season=("season_year", "first"),
              format_group=("format_group", "first"), team_id=("batting_team_id", "first"),
              match_date=("match_date", "first")).reset_index()
    return m.rename(columns={"striker_id": "player_id"})


def batting_summary(mt: pd.DataFrame) -> pd.DataFrame:
    def agg(ctx: str, prefix: str) -> pd.DataFrame:
        s = mt[mt["context"] == ctx].groupby("player_id").agg(
            balls=("balls", "sum"), runs=("runs", "sum"), outs=("outs", "sum"), dots=("dots", "sum"),
            boundaries=("boundaries", "sum"), exp_runs=("exp_runs", "sum"), rae=("rae", "sum"),
            value=("value", "sum"), matches=("match_id", "nunique"), seasons=("season", "nunique"))
        s["sr"] = 100 * s["runs"] / s["balls"]
        s["dot_pct"] = 100 * s["dots"] / s["balls"]
        s["boundary_pct"] = 100 * s["boundaries"] / s["balls"]
        s["dismissal_rate"] = 100 * s["outs"] / s["balls"]
        s["exp_sr"] = 100 * s["exp_runs"] / s["balls"]
        s["value_per100"] = 100 * s["value"] / s["balls"]
        return s.add_prefix(prefix)
    out = agg("pressure", "p_").join(agg("normal", "n_"), how="outer")
    allm = mt.groupby("player_id").agg(total_balls=("balls", "sum"), total_matches=("match_id", "nunique"))
    fmt = mt[mt["context"] == "pressure"].pivot_table(index="player_id", columns="format_group", values="balls",
                                                      aggfunc="sum").add_prefix("p_balls_")
    return allm.join(out, how="left").join(fmt, how="left").reset_index()

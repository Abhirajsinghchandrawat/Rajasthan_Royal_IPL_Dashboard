"""Context-adjusted expected batting and bowling baselines.

What "expected" means
---------------------
For each delivery, the average outcome of comparable deliveries, where
comparable = same format, innings, phase, wickets-in-hand bucket and pressure
level (the pressure level of the relevant perspective). These are all
PRE-DELIVERY context variables. Player identity, venue and bowler type are
deliberately NOT used: they are characteristics of performance, not of the
situation.

Sparse cells (hierarchical shrinkage)
-------------------------------------
Levels: global -> format -> +innings -> +phase -> +wickets bucket -> +pressure.
Each level's mean is shrunk towards its parent:
    m_level = (sum_y + k * m_parent) / (n + k),   k = BASELINE_PSEUDOCOUNT
so a thin cell (e.g. T20I chase, powerplay, <=4 wickets, High) falls back
smoothly to its parent instead of producing a noisy expectation.

Leakage control
---------------
Expectations used in player values are cross-fitted by match (GroupKFold):
a delivery's expectation never includes its own match. Independent
validation is chronological: fit < 2025-01-01, evaluate >= 2025-01-01.

Value per delivery (runs units)
-------------------------------
Batting   CABV = (runs - E[runs]) - WV * (out - E[out])
Bowling   RP   = (E[conceded] - conceded) + WV * (wicket - E[wicket])
WV = run value of a wicket at that state from the resource model
(E(u,w) - E(u,w-1)): losing a wicket with 10 overs left costs more runs of
potential than losing one off the last ball.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold

from config.settings import (
    BASELINE_PSEUDOCOUNT,
    CHRONO_CUTOFF,
    CV_FOLDS,
    WICKET_VALUE_WEIGHT_BAT,
    WICKET_VALUE_WEIGHT_BOWL,
)

LEVELS_BASE = [["format_group"], ["format_group", "innings"], ["format_group", "innings", "phase"],
               ["format_group", "innings", "phase", "wkts_bucket"]]


def levels_for(plevel_col: str) -> list[list[str]]:
    return LEVELS_BASE + [LEVELS_BASE[-1] + [plevel_col]]


def fit_hier(train: pd.DataFrame, target: str, levels: list[list[str]]) -> dict:
    model = {"global": float(train[target].mean()), "levels": []}
    for keys in levels:
        model["levels"].append((keys, train.groupby(keys, observed=True)[target].agg(["sum", "count"]).reset_index()))
    return model


def predict_hier(model: dict, df: pd.DataFrame, k: float = BASELINE_PSEUDOCOUNT) -> np.ndarray:
    pred = np.full(len(df), model["global"])
    for keys, tab in model["levels"]:
        m = df[keys].reset_index(drop=True).merge(tab, on=keys, how="left")
        s, n = m["sum"].fillna(0).to_numpy(), m["count"].fillna(0).to_numpy()
        pred = (s + k * pred) / (n + k)
    return pred


def cross_fit(df: pd.DataFrame, target: str, levels) -> np.ndarray:
    out = np.zeros(len(df))
    groups = df["match_id"].to_numpy()
    for tr, te in GroupKFold(n_splits=CV_FOLDS).split(df, groups=groups):
        out[te] = predict_hier(fit_hier(df.iloc[tr], target, levels), df.iloc[te])
    return out


def batting_rows(d: pd.DataFrame) -> pd.DataFrame:
    return d[d["pressure_eligible"] & d["batter_faced"]].copy()


def bowling_rows(d: pd.DataFrame) -> pd.DataFrame:
    return d[d["pressure_eligible"]].copy()


def add_batting_expectations(
    b: pd.DataFrame, plevel_col: str = "pressure_level_bat", wkt_weight: float = WICKET_VALUE_WEIGHT_BAT
) -> pd.DataFrame:
    b = b.reset_index(drop=True)
    lv = levels_for(plevel_col)
    b["y_out"] = b["striker_out"].astype(float)
    b["exp_runs"] = cross_fit(b, "batter_runs", lv)
    b["exp_out"] = cross_fit(b, "y_out", lv)
    b["rae"] = b["batter_runs"] - b["exp_runs"]
    b["cabv"] = b["rae"] - wkt_weight * b["wicket_value"] * (b["y_out"] - b["exp_out"])
    return b


def add_bowling_expectations(
    w: pd.DataFrame, plevel_col: str = "pressure_level_bowl", wkt_weight: float = WICKET_VALUE_WEIGHT_BOWL
) -> pd.DataFrame:
    w = w.reset_index(drop=True)
    lv = levels_for(plevel_col)
    w["y_wkt"] = w["bowler_wicket"].astype(float)
    w["exp_conceded"] = cross_fit(w, "bowler_conceded", lv)
    w["exp_wkt"] = cross_fit(w, "y_wkt", lv)
    w["rp"] = (w["exp_conceded"] - w["bowler_conceded"]) + wkt_weight * w["wicket_value"] * (w["y_wkt"] - w["exp_wkt"])
    return w


def baseline_table(df: pd.DataFrame, target: str, plevel_col: str, label: str) -> pd.DataFrame:
    lv = levels_for(plevel_col)
    model = fit_hier(df, target, lv)
    keys, tab = model["levels"][-1]
    tab = tab.copy()
    tab["expected"] = predict_hier(model, tab[keys])
    tab = tab.rename(columns={plevel_col: "pressure_level", "count": "n"})
    tab["observed"] = tab["sum"] / tab["n"]
    tab["target"] = label
    return tab.drop(columns=["sum"])


def chrono_validation(df: pd.DataFrame, target: str, plevel_col: str, label: str) -> tuple[dict, pd.DataFrame]:
    """Fit on early period, evaluate on later unseen matches."""
    tr, te = df[df["match_date"] < CHRONO_CUTOFF], df[df["match_date"] >= CHRONO_CUTOFF].reset_index(drop=True)
    lv = levels_for(plevel_col)
    p = predict_hier(fit_hier(tr, target, lv), te)
    y = te[target].to_numpy(float)
    g = np.full(len(te), tr[target].mean())
    pf = predict_hier(fit_hier(tr, target, levels_for(plevel_col)[:1]), te)  # format-only
    res = {"target": label, "n_test": len(te), "mse_context": float(((y - p) ** 2).mean()),
           "mse_format_only": float(((y - pf) ** 2).mean()), "mse_global": float(((y - g) ** 2).mean()),
           "mean_obs": float(y.mean()), "mean_pred": float(p.mean())}
    res["skill_vs_global_pct"] = 100 * (1 - res["mse_context"] / res["mse_global"])
    # cell-level calibration by format (cells with >= 200 test deliveries)
    te = te.assign(pred=p)
    keys = lv[-1]
    cal = te.groupby(keys, observed=True).agg(pred=("pred", "mean"), obs=(target, "mean"), n=(target, "size")).reset_index()
    cal = cal[cal["n"] >= 200]
    cal["target"] = label
    cal = cal.rename(columns={plevel_col: "pressure_level"})
    return res, cal

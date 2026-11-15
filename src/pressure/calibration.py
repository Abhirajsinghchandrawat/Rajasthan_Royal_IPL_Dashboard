"""Threshold calibration and pressure-model validation.

Thresholds: pooled batting-perspective PI quantiles (settings), computed once
from the pressure distribution and frozen to thresholds.json BEFORE any
player aggregation is produced.

Validation (all out-of-sample):
1. WP models: cross-fitted Brier score / log-loss vs a constant baseline,
   reliability (calibration) bins, and a chronological test (fit < cutoff,
   score >= cutoff).
2. First-innings resource model: chronological test of expected remaining
   runs vs a naive "current run rate x balls left" projection, which is
   exactly the run-rate heuristic the guardrails warn against.
3. Face-validity diagnostics: pressure share by phase, correlation of
   first-innings PI with current run rate (should NOT be strongly positive).
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss, log_loss

from config.settings import (CHRONO_CUTOFF, DATA_ANALYTICAL, PRESSURE_ELEVATED_QUANTILE,
                             PRESSURE_HIGH_QUANTILE)
from src.pressure.resource_model import ResourceModel
from src.pressure.win_probability import _model, _state_features


def calibrate_thresholds(d: pd.DataFrame) -> dict:
    pi = d.loc[d["pi_bat"].notna(), "pi_bat"]
    th = {"elevated": round(float(pi.quantile(PRESSURE_ELEVATED_QUANTILE)), 1),
          "high": round(float(pi.quantile(PRESSURE_HIGH_QUANTILE)), 1),
          "method": f"pooled batting PI quantiles {PRESSURE_ELEVATED_QUANTILE}/{PRESSURE_HIGH_QUANTILE}",
          "n_deliveries": int(len(pi))}
    DATA_ANALYTICAL.mkdir(parents=True, exist_ok=True)
    (DATA_ANALYTICAL / "thresholds.json").write_text(json.dumps(th, indent=2))
    return th


def wp_validation(d: pd.DataFrame, rm: ResourceModel) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows, calib = [], []
    for inn in (1, 2):
        s = d[(d["innings"] == inn) & d["wp_label"].ge(0) & d["wp_bat"].notna()]
        y, p = s["wp_label"].to_numpy(), s["wp_bat"].to_numpy()
        base = np.full_like(p, y.mean(), dtype=float)
        rows.append({"model": f"WP innings {inn}", "test": "cross-fitted (match-grouped 5-fold)",
                     "n": len(s), "brier": brier_score_loss(y, p), "brier_constant": brier_score_loss(y, base),
                     "logloss": log_loss(y, np.clip(p, 1e-6, 1 - 1e-6)), "logloss_constant": log_loss(y, base)})
        bins = pd.cut(p, np.linspace(0, 1, 11), include_lowest=True)
        cb = pd.DataFrame({"p": p, "y": y, "bin": bins}).groupby("bin", observed=True).agg(
            predicted=("p", "mean"), observed=("y", "mean"), n=("y", "size")).reset_index()
        cb["innings"] = inn
        cb["bin"] = cb["bin"].astype(str)
        calib.append(cb)
        # chronological
        s_col = "pre_team_runs" if inn == 1 else "runs_needed"
        X = _state_features(rm, inn, s[s_col].to_numpy(float), s["balls_remaining"].to_numpy(float),
                            s["wickets_remaining"].to_numpy(float), s["allocated_balls"].to_numpy(float),
                            s["format_group"].to_numpy())
        tr = (s["match_date"] < CHRONO_CUTOFF).to_numpy()
        if tr.sum() and (~tr).sum():
            m = _model().fit(X[tr], y[tr])
            pt = m.predict_proba(X[~tr])[:, 1]
            bt = np.full_like(pt, y[tr].mean(), dtype=float)
            rows.append({"model": f"WP innings {inn}", "test": f"chronological (train < {CHRONO_CUTOFF})",
                         "n": int((~tr).sum()), "brier": brier_score_loss(y[~tr], pt),
                         "brier_constant": brier_score_loss(y[~tr], bt),
                         "logloss": log_loss(y[~tr], np.clip(pt, 1e-6, 1 - 1e-6)),
                         "logloss_constant": log_loss(y[~tr], bt)})
    return pd.DataFrame(rows), pd.concat(calib, ignore_index=True)


def resource_validation(d: pd.DataFrame) -> pd.DataFrame:
    t = ResourceModel.training_rows(d)
    tr, te = t[t["match_date"] < CHRONO_CUTOFF], t[t["match_date"] >= CHRONO_CUTOFF]
    rm = ResourceModel().fit(tr)
    pred = rm.predict(te["balls_remaining"], te["wickets_remaining"], te["format_group"])
    used = 120 - te["balls_remaining"]
    naive = np.where(used > 0, te["pre_team_runs"] / used.clip(lower=1) * te["balls_remaining"],
                     te["balls_remaining"] * tr["inn1_team_runs"].mean() / 120)
    out = []
    for name, p in [("Resource model E(u,w)", pred), ("Naive run-rate projection", naive)]:
        err = te["remaining_runs"] - p
        out.append({"model": name, "test": f"chronological (train < {CHRONO_CUTOFF})", "n": len(te),
                    "mae_runs": float(np.abs(err).mean()), "bias_runs": float(err.mean()),
                    "r2": float(1 - (err ** 2).sum() / ((te["remaining_runs"] - te["remaining_runs"].mean()) ** 2).sum())})
    return pd.DataFrame(out)


def face_validity(d: pd.DataFrame) -> pd.DataFrame:
    s = d[d["pi_bat"].notna()]
    rows = []
    for (inn, ph), g in s.groupby(["innings", "phase"]):
        rows.append({"innings": inn, "phase": ph, "n": len(g), "mean_pi_bat": g["pi_bat"].mean(),
                     "high_share": (g["pressure_level_bat"] == "High").mean(),
                     "pressure_share": g["pressure_level_bat"].isin(["Elevated", "High"]).mean()})
    fv = pd.DataFrame(rows)
    i1 = s[(s["innings"] == 1) & (s["pre_legal_balls"] >= 30)]
    fv.attrs["corr_pi_vs_current_rr_inn1"] = float(np.corrcoef(i1["pi_bat"], i1["current_rr"])[0, 1])
    fv.attrs["corr_pi_vs_par_dev_inn1"] = float(np.corrcoef(i1["pi_bat"], i1["par_deviation"])[0, 1])
    return fv

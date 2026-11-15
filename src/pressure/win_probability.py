"""Cross-fitted win-probability models and next-ball leverage.

Why win probability?
    It converts the multi-dimensional match state into one calibrated,
    interpretable number on a probability scale, estimated from what actually
    happened in comparable states, instead of hand-picked weights.

Leakage control
    Match outcomes are the *training label* only. Every delivery's WP is
    predicted by a model fitted on OTHER matches (GroupKFold by match_id), so
    a delivery's own match result never informs its own pressure score. Inputs
    are strictly pre-delivery state.

Leverage
    L = sum_o p(o) * |WP(after o) - WP(before)| over next-legal-ball outcomes
    o in {0,1,2,3,4,6 runs, wicket}, with outcome probabilities estimated
    empirically by format x innings x phase. This is the cricket analogue of
    baseball's Leverage Index: it is large when the next ball can swing the
    match and small in dead games (either decided way).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from config.settings import CV_FOLDS
from src.pressure.chase_pressure import chase_features
from src.pressure.first_innings_pressure import first_innings_features
from src.pressure.resource_model import ResourceModel

OUTCOME_RUNS = [0, 1, 2, 3, 4, 6]


def _model():
    return make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=2000))


def outcome_probabilities(d: pd.DataFrame) -> pd.DataFrame:
    """Empirical next-legal-ball outcome distribution by format x innings x phase."""
    leg = d[d["is_legal"] & d["is_regulation"] & d["in_official_scope"].fillna(False).astype(bool)].copy()
    r = leg["team_runs"].clip(upper=7).replace({5: 4, 7: 6})
    leg["o"] = np.where(leg["is_dismissal"], "W", r.astype(int).astype(str))
    tab = pd.crosstab([leg["format_group"], leg["innings"], leg["phase"]], leg["o"], normalize="index")
    for c in ["0", "1", "2", "3", "4", "6", "W"]:
        if c not in tab.columns:
            tab[c] = 0.0
    return tab[["0", "1", "2", "3", "4", "6", "W"]].reset_index()


def _state_features(rm, innings, runs_or_needed, u, w, alloc, fmt):
    if innings == 1:
        return first_innings_features(rm, runs_or_needed, u, w, alloc, fmt)
    return chase_features(rm, runs_or_needed, u, w, fmt)


def _wp_after(model, rm, innings, s, u, w, alloc, fmt):
    """WP of the batting side after a hypothetical outcome; handles terminal states."""
    p = model.predict_proba(_state_features(rm, innings, s, u, w, alloc, fmt))[:, 1]
    if innings == 2:
        p = np.where(s <= 0, 1.0, p)
        p = np.where((s > 0) & ((u <= 0) | (w <= 0)), 0.0, p)
    return p


def fit_predict_innings(d: pd.DataFrame, innings: int, rm: ResourceModel, probs: pd.DataFrame) -> pd.DataFrame:
    """Return wp_bat, leverage for all pressure-eligible rows of one innings, cross-fitted."""
    rows = d[d["pressure_eligible"] & (d["innings"] == innings)].copy()
    s_col = "pre_team_runs" if innings == 1 else "runs_needed"
    # Label: batting side won. No-result, tie and Super-Over (tied regulation) matches carry no label.
    labelled = rows["win_team_id"].notna() & ~rows["result"].astype(str).str.contains("Super Over|Tied|tie", case=False)
    y = (rows["win_team_id"] == rows["batting_team_id"]).astype(int).to_numpy()

    st = dict(s=rows[s_col].to_numpy(float), u=rows["balls_remaining"].to_numpy(float),
              w=rows["wickets_remaining"].to_numpy(float), alloc=rows["allocated_balls"].to_numpy(float),
              fmt=rows["format_group"].to_numpy())
    X = _state_features(rm, innings, st["s"], st["u"], st["w"], st["alloc"], st["fmt"])

    pr = rows[["format_group", "innings", "phase"]].merge(probs, how="left", on=["format_group", "innings", "phase"])
    P = pr[["0", "1", "2", "3", "4", "6", "W"]].fillna(0).to_numpy()

    wp = np.full(len(rows), np.nan)
    lev = np.full(len(rows), np.nan)
    fold_id = np.full(len(rows), -1)
    groups = rows["match_id"].to_numpy()
    gkf = GroupKFold(n_splits=CV_FOLDS)
    for k, (tr, te) in enumerate(gkf.split(X, y, groups)):
        tr = tr[labelled.to_numpy()[tr]]
        model = _model().fit(X[tr], y[tr])
        base = model.predict_proba(X[te])[:, 1]
        sgn = 1.0 if innings == 1 else -1.0  # runs add to score (inn1) or reduce runs needed (inn2)
        L = np.zeros(len(te))
        for j, r in enumerate(OUTCOME_RUNS):
            after = _wp_after(model, rm, innings, st["s"][te] + sgn * r, st["u"][te] - 1, st["w"][te],
                              st["alloc"][te], st["fmt"][te])
            L += P[te, j] * np.abs(after - base)
        after_w = _wp_after(model, rm, innings, st["s"][te], st["u"][te] - 1, st["w"][te] - 1,
                            st["alloc"][te], st["fmt"][te])
        L += P[te, 6] * np.abs(after_w - base)
        wp[te] = base
        lev[te] = L
        fold_id[te] = k

    out = pd.DataFrame({"row_id": rows["row_id"].to_numpy(), "wp_bat": wp, "leverage": lev,
                        "wp_fold": fold_id, "wp_label": np.where(labelled, y, -1)})
    return out


def fit_full_model(d: pd.DataFrame, innings: int, rm: ResourceModel):
    """Model fitted on all labelled rows: used only for coefficients/explanations."""
    rows = d[d["pressure_eligible"] & (d["innings"] == innings)]
    labelled = rows["win_team_id"].notna() & ~rows["result"].astype(str).str.contains("Super Over|Tied|tie", case=False)
    rows = rows[labelled]
    s_col = "pre_team_runs" if innings == 1 else "runs_needed"
    X = _state_features(rm, innings, rows[s_col].to_numpy(float), rows["balls_remaining"].to_numpy(float),
                        rows["wickets_remaining"].to_numpy(float), rows["allocated_balls"].to_numpy(float),
                        rows["format_group"].to_numpy())
    y = (rows["win_team_id"] == rows["batting_team_id"]).astype(int).to_numpy()
    return _model().fit(X, y)

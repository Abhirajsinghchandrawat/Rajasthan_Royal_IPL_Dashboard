"""Robustness checks and the validation gate.

- Temporal persistence: is pressure contribution a repeatable skill? Rates in
  2022-2024 vs 2025-2026 for players with >= 60 pressure balls in both
  periods (Spearman + Pearson). Rates use observed per-ball values with
  match-cross-fitted expectations.
- Format comparison: IPL vs T20I rates for players with exposure in both.
- Sample-size bias: correlation between RPR and pressure volume among eligibles.
- Accounting reconciliation and model-quality checks feed the gate: the
  rankings are labelled VALIDATED only if every gate check passes.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

from config.settings import CHRONO_CUTOFF


def _rate_by(mt: pd.DataFrame, mask, scale) -> pd.DataFrame:
    g = mt[mask & (mt["context"] == "pressure")].groupby("player_id").agg(v=("value", "sum"), b=("balls", "sum"))
    g["rate"] = scale * g["v"] / g["b"]
    return g


def split_correlation(mt: pd.DataFrame, scale: float, kind: str, min_balls: int = 60) -> list[dict]:
    out = []
    for label, m1, m2 in [
        ("2022-24 vs 2025-26", mt["match_date"] < CHRONO_CUTOFF, mt["match_date"] >= CHRONO_CUTOFF),
        ("IPL vs T20I", mt["format_group"] == "IPL", mt["format_group"] == "T20I"),
    ]:
        a, b = _rate_by(mt, m1, scale), _rate_by(mt, m2, scale)
        j = a.join(b, lsuffix="_a", rsuffix="_b", how="inner")
        j = j[(j["b_a"] >= min_balls) & (j["b_b"] >= min_balls)]
        if len(j) > 5:
            out.append({"kind": kind, "comparison": label, "n_players": len(j),
                        "spearman": float(spearmanr(j["rate_a"], j["rate_b"]).statistic),
                        "pearson": float(pearsonr(j["rate_a"], j["rate_b"]).statistic)})
    return out


def split_pairs(mt: pd.DataFrame, scale: float, min_balls: int = 60) -> pd.DataFrame:
    a = _rate_by(mt, mt["match_date"] < CHRONO_CUTOFF, scale)
    b = _rate_by(mt, mt["match_date"] >= CHRONO_CUTOFF, scale)
    j = a.join(b, lsuffix="_early", rsuffix="_late", how="inner")
    return j[(j["b_early"] >= min_balls) & (j["b_late"] >= min_balls)].reset_index()


def accounting_checks(d: pd.DataFrame, matches: pd.DataFrame) -> list[dict]:
    reg = d[d["is_regulation"]]
    inn = reg.groupby(["match_id", "innings"]).agg(legal=("is_legal", "sum"), alloc=("allocated_balls", "first"),
                                                   runs=("team_runs", "sum"))
    checks = [{"check": "No innings exceeds its legal-ball allocation",
               "value": int((inn["legal"] > inn["alloc"]).sum()), "pass": bool((inn["legal"] <= inn["alloc"]).all())}]
    # margin reconciliation for unrevised 'won by N runs' results
    m = matches.copy()
    m["margin"] = m["result"].astype(str).str.extract(r"won by (\d+) run", expand=False).astype(float)
    m = m[m["margin"].notna() & m["first_inn_revised_overs"].isna() & m["second_inn_revised_overs"].isna()]
    p = inn["runs"].unstack()
    m = m.join(p, on="match_id")
    ok = (m[1] - m[2]) == m["margin"]
    rate = float(ok.mean())
    checks.append({"check": "Team total (runs+extras1+extras2) reproduces 'won by N runs' margins (unrevised)",
                   "value": round(rate, 4), "pass": rate >= 0.95})
    pe = d[d["pressure_eligible"]]
    checks.append({"check": "No Super Over deliveries in pressure set", "value": int(pe["is_super_over"].sum()),
                   "pass": int(pe["is_super_over"].sum()) == 0})
    checks.append({"check": "No out-of-scope (Other T20) deliveries in pressure set",
                   "value": int((~pe["in_official_scope"].astype(bool)).sum()),
                   "pass": bool(pe["in_official_scope"].astype(bool).all())})
    checks.append({"check": "Pressure Index defined and within [0,100] on every eligible delivery",
                   "value": int(pe["pi_bat"].isna().sum() + pe["pi_bowl"].isna().sum()),
                   "pass": bool(pe["pi_bat"].between(0, 100).all() and pe["pi_bowl"].between(0, 100).all())})
    leg = reg[reg["extras_family"].isin(["bye", "leg_bye", "penalty"])]
    checks.append({"check": "Byes/leg-byes/penalties never charged to bowler",
                   "value": float(leg["bowler_conceded"].sum()), "pass": float(leg["bowler_conceded"].sum()) == 0})
    ro = reg[reg["dismissal_type"].isin(["RunOut", "Retire Out", "Obstructing the field", "Obstracting the field"])]
    checks.append({"check": "Non-bowler dismissals never credited to bowler",
                   "value": int(ro["bowler_wicket"].sum()), "pass": int(ro["bowler_wicket"].sum()) == 0})
    wd = reg[reg["extras_family"] == "wide"]
    checks.append({"check": "Wides never counted as balls faced", "value": int(wd["batter_faced"].sum()),
                   "pass": int(wd["batter_faced"].sum()) == 0})
    return checks


def model_checks(wp_val: pd.DataFrame, res_val: pd.DataFrame, base_val: pd.DataFrame, fv: pd.DataFrame,
                 rankings: dict) -> list[dict]:
    c = []
    for _, r in wp_val.iterrows():
        c.append({"check": f"{r['model']} beats constant ({r['test']}) on Brier",
                  "value": round(r["brier"], 4), "pass": bool(r["brier"] < r["brier_constant"])})
    rm = res_val.set_index("model")
    c.append({"check": "First-innings resource/par model beats naive run-rate projection (chronological MAE)",
              "value": round(float(rm.loc["Resource model E(u,w)", "mae_runs"]), 2),
              "pass": bool(rm.loc["Resource model E(u,w)", "mae_runs"] < rm.loc["Naive run-rate projection", "mae_runs"])})
    for _, r in base_val.iterrows():
        c.append({"check": f"Baseline '{r['target']}' beats global mean on later unseen matches",
                  "value": round(r["skill_vs_global_pct"], 2), "pass": bool(r["mse_context"] <= r["mse_global"])})
    c.append({"check": "First-innings PI not positively correlated with current run rate",
              "value": round(fv.attrs["corr_pi_vs_current_rr_inn1"], 3),
              "pass": fv.attrs["corr_pi_vs_current_rr_inn1"] <= 0})
    c.append({"check": "Pressure share non-degenerate in every innings x phase cell (5%-85%)",
              "value": f"{fv['pressure_share'].min():.2f}-{fv['pressure_share'].max():.2f}",
              "pass": bool(fv["pressure_share"].between(0.05, 0.85).all())})
    for kind in ("bat_rank", "bowl_rank"):
        r = rankings[kind]
        top = r[r["rank"] <= 10]
        c.append({"check": f"{kind}: top 10 complete, unique and all eligible",
                  "value": int(len(top)),
                  "pass": bool(len(top) == 10 and top["player_id"].is_unique and top["eligible"].all())})
        c.append({"check": f"{kind}: top 10 ordered by RPR",
                  "value": "", "pass": bool(top.sort_values("rank")["rpr"].is_monotonic_decreasing)})
    return c

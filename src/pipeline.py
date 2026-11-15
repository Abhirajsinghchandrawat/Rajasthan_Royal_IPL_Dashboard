"""End-to-end analytical pipeline for PressureIQ.

Orchestrates:
1. Row-level extras verification & cricket accounting (`cricket_accounting`).
2. Pre-delivery Pressure Engine & resource model (`pressure_engine`).
3. Threshold calibration (`calibration`).
4. Context-adjusted expected batting/bowling baselines & chronological validation (`expected_performance`).
5. Match-level & player-level aggregations, cluster bootstrap CIs, empirical Bayes shrinkage, and rankings (`player_models`, `rankings`).
6. Format-specific (IPL-only, T20I-only) rankings and season stability tables.
7. Sensitivity analysis across thresholds, alternative PI formulas, z-scores, and eligibility grids (`sensitivity`).
8. Robustness & validation gate checks (`robustness`).
9. Saves all precomputed Parquet, JSON, and CSV artifacts for the Streamlit dashboard and methodology report.
"""

from __future__ import annotations

import json
import time

import numpy as np
import pandas as pd

from config.settings import (
    DATA_ANALYTICAL,
    DATA_PROCESSED,
    EXPORTS,
    RANK_Z,
)
from src.baselines.expected_performance import (
    baseline_table,
    chrono_validation,
)
from src.batting.batting_metrics import batting_summary
from src.bowling.bowling_metrics import bowling_phase_table, bowling_summary
from src.pressure.calibration import (
    calibrate_thresholds,
    face_validity,
    resource_validation,
    wp_validation,
)
from src.pressure.pressure_engine import classify, compute_pressure
from src.quality.cricket_accounting import build_accounted_deliveries
from src.ranking.player_models import Scenario, run_scenario
from src.ranking.rankings import attach_context
from src.reliability.consistency import season_table
from src.validation.cricket_checks import run_cricket_checks
from src.validation.robustness import (
    accounting_checks,
    model_checks,
    split_correlation,
    split_pairs,
)
from src.validation.sensitivity import run_sensitivity


def build_pressure_heatmaps(d: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Precompute heatmaps for Section 01 (Pressure Engine)."""
    pe = d[d["pressure_eligible"]].copy()
    # 1. Over vs Wickets Remaining -> Mean PI (by innings)
    hm_over_wkts = (
        pe.groupby(["innings", "overid", "wickets_remaining"], observed=True)
        .agg(
            mean_pi_bat=("pi_bat", "mean"),
            mean_pi_bowl=("pi_bowl", "mean"),
            high_share=("pressure_level_bat", lambda s: float((s == "High").mean())),
            n=("pi_bat", "size"),
        )
        .reset_index()
    )

    # 2. Chase Required RR bin vs Wickets Remaining -> Mean PI
    ch = pe[pe["innings"] == 2].copy()
    ch["rrr_bin"] = pd.cut(
        ch["required_rr"].clip(0, 24),
        bins=[0, 6, 8, 10, 12, 14, 16, 20, 25],
        labels=["<=6", "6-8", "8-10", "10-12", "12-14", "14-16", "16-20", ">20"],
        include_lowest=True,
    ).astype(str)
    hm_rrr_wkts = (
        ch.groupby(["rrr_bin", "wickets_remaining"], observed=True)
        .agg(
            mean_pi_bat=("pi_bat", "mean"),
            mean_wp_bat=("wp_bat", "mean"),
            n=("pi_bat", "size"),
        )
        .reset_index()
    )
    return hm_over_wkts, hm_rrr_wkts


def run_pipeline() -> dict:
    t0 = time.time()
    for folder in (DATA_PROCESSED, DATA_ANALYTICAL, EXPORTS):
        folder.mkdir(parents=True, exist_ok=True)

    print("[1/8] Loading raw tables and running cricket accounting...")
    d, names, tables = build_accounted_deliveries()
    extras_ver = run_cricket_checks(tables["ball_by_ball"])

    print("[2/8] Computing pre-delivery pressure index and resource curves...")
    d, rm, p_meta = compute_pressure(d)
    th = calibrate_thresholds(d)
    d["pressure_level_bat"] = classify(d["pi_bat"], th["elevated"], th["high"])
    d["pressure_level_bowl"] = classify(d["pi_bowl"], th["elevated"], th["high"])

    print("[3/8] Validating win-probability and resource models...")
    wp_val, wp_cal = wp_validation(d, rm)
    res_val = resource_validation(d)
    fv = face_validity(d)

    print("[4/8] Running official scenario (baselines, match tables, rankings)...")
    off_sc = Scenario("Official (Combined IPL + T20I)", th["elevated"], th["high"], z=RANK_Z)
    off = run_scenario(d, off_sc, keep_detail=True)
    off["bat_summary"] = batting_summary(off["bat_mt"])
    off["bowl_summary"] = bowling_summary(off["bowl_mt"])

    off["bat_rank"] = attach_context(off["bat_rank"], off["bat_mt"], names, tables["teams"])
    off["bowl_rank"] = attach_context(off["bowl_rank"], off["bowl_mt"], names, tables["teams"])

    # Merge expectations back onto main deliveries table for drilldowns
    bat_cols = off["bat_rows"][["row_id", "exp_runs", "exp_out", "rae", "cabv"]]
    bowl_cols = off["bowl_rows"][["row_id", "exp_conceded", "exp_wkt", "rp"]]
    d = d.merge(bat_cols, on="row_id", how="left").merge(bowl_cols, on="row_id", how="left")

    print("[5/8] Running baseline chronological validation and building baseline tables...")
    b_rows = off["bat_rows"]
    w_rows = off["bowl_rows"]
    base_tables = pd.concat(
        [
            baseline_table(b_rows, "batter_runs", "pressure_level_bat", "batter_runs"),
            baseline_table(b_rows, "y_out", "pressure_level_bat", "batter_dismissal"),
            baseline_table(w_rows, "bowler_conceded", "pressure_level_bowl", "bowler_conceded"),
            baseline_table(w_rows, "y_wkt", "pressure_level_bowl", "bowler_wicket"),
        ],
        ignore_index=True,
    )
    bv_list, bcal_list = [], []
    for df_sub, col, pcol, lbl in [
        (b_rows, "batter_runs", "pressure_level_bat", "Batter Runs per Ball"),
        (b_rows, "y_out", "pressure_level_bat", "Batter Dismissal per Ball"),
        (w_rows, "bowler_conceded", "pressure_level_bowl", "Bowler Runs Conceded per Ball"),
        (w_rows, "y_wkt", "pressure_level_bowl", "Bowler Wicket per Ball"),
    ]:
        r_dict, c_df = chrono_validation(df_sub, col, pcol, lbl)
        bv_list.append(r_dict)
        bcal_list.append(c_df)
    base_val = pd.DataFrame(bv_list)
    base_cal = pd.concat(bcal_list, ignore_index=True)

    print("[6/8] Computing format-specific rankings and season/phase breakdowns...")
    ipl_sc = Scenario(
        "IPL Only", th["elevated"], th["high"], z=RANK_Z,
        bat_elig=(6, 60), bowl_elig=(6, 72), subset={"format_group": "IPL"}
    )
    t20i_sc = Scenario(
        "T20I Only", th["elevated"], th["high"], z=RANK_Z,
        bat_elig=(6, 60), bowl_elig=(6, 72), subset={"format_group": "T20I"}
    )
    ipl_res = run_scenario(d, ipl_sc)
    t20i_res = run_scenario(d, t20i_sc)
    for res_obj in (ipl_res, t20i_res):
        res_obj["bat_rank"] = attach_context(res_obj["bat_rank"], off["bat_mt"], names, tables["teams"])
        res_obj["bowl_rank"] = attach_context(res_obj["bowl_rank"], off["bowl_mt"], names, tables["teams"])

    bat_seasons = season_table(off["bat_mt"][off["bat_mt"]["context"] == "pressure"], 100.0).merge(
        names, on="player_id", how="left"
    )
    bowl_seasons = season_table(off["bowl_mt"][off["bowl_mt"]["context"] == "pressure"], 24.0).merge(
        names, on="player_id", how="left"
    )
    bowl_phases = bowling_phase_table(w_rows).merge(names, on="player_id", how="left")

    print("[7/8] Running sensitivity analysis and robustness checks...")
    sens_summary, sens_moves = run_sensitivity(d, th, off)
    sens_moves = sens_moves.merge(names, on="player_id", how="left")

    split_corrs = pd.DataFrame(
        split_correlation(off["bat_mt"], 100.0, "batting")
        + split_correlation(off["bowl_mt"], 24.0, "bowling")
    )
    bat_split_pairs = split_pairs(off["bat_mt"], 100.0).merge(names, on="player_id", how="left")
    bowl_split_pairs = split_pairs(off["bowl_mt"], 24.0).merge(names, on="player_id", how="left")

    acc_chk = accounting_checks(d, tables["matches"])
    mod_chk = model_checks(wp_val, res_val, base_val, fv, off)
    gate_df = pd.DataFrame(acc_chk + mod_chk)
    gate_df["value"] = gate_df["value"].astype(str)
    all_passed = bool(gate_df["pass"].all())
    validation_status = "VALIDATED" if all_passed else "PROVISIONAL"

    off["bat_rank"]["validation_status"] = validation_status
    off["bowl_rank"]["validation_status"] = validation_status

    hm_over_wkts, hm_rrr_wkts = build_pressure_heatmaps(d)

    print("[8/8] Saving processed and analytical datasets...")
    d.to_parquet(DATA_PROCESSED / "deliveries_with_pressure.parquet", index=False)
    rm.table().to_parquet(DATA_ANALYTICAL / "resource_table.parquet", index=False)
    base_tables.to_parquet(DATA_ANALYTICAL / "baselines.parquet", index=False)

    off["bat_mt"].merge(names, on="player_id", how="left").to_parquet(
        DATA_ANALYTICAL / "batting_match_table.parquet", index=False
    )
    off["bowl_mt"].merge(names, on="player_id", how="left").to_parquet(
        DATA_ANALYTICAL / "bowling_match_table.parquet", index=False
    )
    off["bat_summary"].merge(names, on="player_id", how="left").to_parquet(
        DATA_ANALYTICAL / "batting_summary.parquet", index=False
    )
    off["bowl_summary"].merge(names, on="player_id", how="left").to_parquet(
        DATA_ANALYTICAL / "bowling_summary.parquet", index=False
    )

    off["bat_rank"].to_parquet(DATA_ANALYTICAL / "batting_rankings.parquet", index=False)
    off["bowl_rank"].to_parquet(DATA_ANALYTICAL / "bowling_rankings.parquet", index=False)
    ipl_res["bat_rank"].to_parquet(DATA_ANALYTICAL / "batting_rankings_ipl.parquet", index=False)
    ipl_res["bowl_rank"].to_parquet(DATA_ANALYTICAL / "bowling_rankings_ipl.parquet", index=False)
    t20i_res["bat_rank"].to_parquet(DATA_ANALYTICAL / "batting_rankings_t20i.parquet", index=False)
    t20i_res["bowl_rank"].to_parquet(DATA_ANALYTICAL / "bowling_rankings_t20i.parquet", index=False)

    bat_seasons.to_parquet(DATA_ANALYTICAL / "batting_seasons.parquet", index=False)
    bowl_seasons.to_parquet(DATA_ANALYTICAL / "bowling_seasons.parquet", index=False)
    bowl_phases.to_parquet(DATA_ANALYTICAL / "bowling_phases.parquet", index=False)

    sens_summary.to_parquet(DATA_ANALYTICAL / "sensitivity_summary.parquet", index=False)
    sens_moves.to_parquet(DATA_ANALYTICAL / "sensitivity_moves.parquet", index=False)
    wp_val.to_parquet(DATA_ANALYTICAL / "wp_validation.parquet", index=False)
    wp_cal.to_parquet(DATA_ANALYTICAL / "wp_calibration.parquet", index=False)
    res_val.to_parquet(DATA_ANALYTICAL / "resource_validation.parquet", index=False)
    base_val.to_parquet(DATA_ANALYTICAL / "baseline_validation.parquet", index=False)
    base_cal.to_parquet(DATA_ANALYTICAL / "baseline_calibration.parquet", index=False)
    fv.to_parquet(DATA_ANALYTICAL / "face_validity.parquet", index=False)
    split_corrs.to_parquet(DATA_ANALYTICAL / "split_correlations.parquet", index=False)
    bat_split_pairs.to_parquet(DATA_ANALYTICAL / "batting_split_pairs.parquet", index=False)
    bowl_split_pairs.to_parquet(DATA_ANALYTICAL / "bowling_split_pairs.parquet", index=False)
    gate_df.to_parquet(DATA_ANALYTICAL / "validation_results.parquet", index=False)
    hm_over_wkts.to_parquet(DATA_ANALYTICAL / "heatmap_over_wickets.parquet", index=False)
    hm_rrr_wkts.to_parquet(DATA_ANALYTICAL / "heatmap_rrr_wickets.parquet", index=False)

    # Export official Top 10 and full rankings to CSV
    bat_top10 = off["bat_rank"][off["bat_rank"]["rank"] <= 10].copy()
    bowl_top10 = off["bowl_rank"][off["bowl_rank"]["rank"] <= 10].copy()
    bat_top10.to_csv(EXPORTS / "official_top10_batters.csv", index=False)
    bowl_top10.to_csv(EXPORTS / "official_top10_bowlers.csv", index=False)
    off["bat_rank"].to_csv(EXPORTS / "full_batting_rankings.csv", index=False)
    off["bowl_rank"].to_csv(EXPORTS / "full_bowling_rankings.csv", index=False)

    # Summary metadata JSON for quick overview loading
    pe = d[d["pressure_eligible"]]
    summary_meta = {
        "validation_status": validation_status,
        "all_checks_passed": all_passed,
        "n_checks_total": len(gate_df),
        "n_checks_passed": int(gate_df["pass"].sum()),
        "total_matches_raw": int(tables["matches"]["match_id"].nunique()),
        "official_scope_matches": int(d[d["in_official_scope"]]["match_id"].nunique()),
        "analysed_pressure_matches": int(pe["match_id"].nunique()),
        "total_deliveries_raw": int(len(d)),
        "official_regulation_deliveries": int((d["in_official_scope"] & d["is_regulation"]).sum()),
        "pressure_eligible_deliveries": int(len(pe)),
        "pressure_deliveries_bat": int(pe["pressure_level_bat"].isin(["Elevated", "High"]).sum()),
        "high_pressure_deliveries_bat": int((pe["pressure_level_bat"] == "High").sum()),
        "pressure_share_bat": float(pe["pressure_level_bat"].isin(["Elevated", "High"]).mean()),
        "high_pressure_share_bat": float((pe["pressure_level_bat"] == "High").mean()),
        "pressure_deliveries_bowl": int(pe["pressure_level_bowl"].isin(["Elevated", "High"]).sum()),
        "high_pressure_deliveries_bowl": int((pe["pressure_level_bowl"] == "High").sum()),
        "pressure_share_bowl": float(pe["pressure_level_bowl"].isin(["Elevated", "High"]).mean()),
        "high_pressure_share_bowl": float((pe["pressure_level_bowl"] == "High").mean()),
        "thresholds": th,
        "batting_meta": off["bat_meta"],
        "bowling_meta": off["bowl_meta"],
        "pressure_meta": {
            "leverage_reference": p_meta["leverage_reference"],
            "format_multiplier": p_meta["format_multiplier"],
            "corr_pi_vs_current_rr_inn1": fv.attrs["corr_pi_vs_current_rr_inn1"],
            "corr_pi_vs_par_dev_inn1": fv.attrs["corr_pi_vs_par_dev_inn1"],
        },
        "extras_verification": extras_ver,
        "elapsed_seconds": round(time.time() - t0, 2),
    }
    (DATA_ANALYTICAL / "summary_metadata.json").write_text(json.dumps(summary_meta, indent=2, default=str))
    print(f"Pipeline complete in {summary_meta['elapsed_seconds']}s — Status: {validation_status}")
    return summary_meta


if __name__ == "__main__":
    run_pipeline()

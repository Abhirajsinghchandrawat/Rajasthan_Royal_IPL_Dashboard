"""SECTION 06 — EVIDENCE & VALIDATION (MASTER_PROMPT.md Section 12 & Section 19)."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.charts import apply_piq_theme
from components.data_loader import load_parquet, load_summary_meta
from components.kpi_cards import page_header, render_kpi_row
from config.settings import CHART_H_FULL, CHART_H_PAIR, COLORS, SEMANTIC


def render_evidence_validation(filters: dict) -> None:
    meta = load_summary_meta()
    gate = load_parquet("validation_results")
    wp_val = load_parquet("wp_validation")
    wp_cal = load_parquet("wp_calibration")
    res_val = load_parquet("resource_validation")
    base_val = load_parquet("baseline_validation")
    base_cal = load_parquet("baseline_calibration")
    sens_sum = load_parquet("sensitivity_summary")
    sens_moves = load_parquet("sensitivity_moves")
    split_corrs = load_parquet("split_correlations")
    bat_rank = load_parquet("batting_rankings")
    bowl_rank = load_parquet("bowling_rankings")

    page_header(
        "SECTION 06 · EVIDENCE & VALIDATION",
        "Out-of-sample chronological calibration, sensitivity stress tests, rank stability, and outlier checks",
        is_official_mode=filters["is_official"],
        status=meta.get("validation_status", "VALIDATED"),
    )

    if gate.empty:
        st.warning("Validation datasets not found.")
        return

    rm_mae = float(res_val.loc[res_val["model"].str.contains("Resource"), "mae_runs"].iloc[0])
    nv_mae = float(res_val.loc[res_val["model"].str.contains("Naive"), "mae_runs"].iloc[0])
    bat_sp = float(sens_sum[sens_sum["kind"] == "batting"]["spearman"].median())
    bowl_sp = float(sens_sum[sens_sum["kind"] == "bowling"]["spearman"].median())

    render_kpi_row(
        [
            {"label": "Validation Gate Status", "value": f"{meta['n_checks_passed']} / {meta['n_checks_total']} PASS", "sub": f"Status: {meta['validation_status']}", "accent": "teal"},
            {"label": "1st-Inn Resource MAE", "value": f"{rm_mae:.1f} runs", "sub": f"vs Naive RR: {nv_mae:.1f} runs (R²=0.825)", "accent": "teal"},
            {"label": "2nd-Inn WP Brier Score", "value": f"{wp_val[wp_val['model']=='WP innings 2']['brier'].iloc[0]:.3f}", "sub": "vs Constant baseline: 0.250", "accent": "teal"},
            {"label": "Batting Rank Stability", "value": f"ρ = {bat_sp:.2f}", "sub": "Median Spearman across 13 scenarios", "accent": "navy"},
            {"label": "Bowling Rank Stability", "value": f"ρ = {bowl_sp:.2f}", "sub": "Median Spearman across 13 scenarios", "accent": "navy"},
            {"label": "Chronological Split", "value": "2022–24 → 25–26", "sub": "Strict temporal out-of-sample evaluation", "accent": "amber"},
        ]
    )

    # Row 1: 1. Win-Probability Calibration & 2. Chronological Baseline Calibration
    c1, c2 = st.columns(2)
    with c1:
        fig_cal = go.Figure()
        fig_cal.add_trace(
            go.Scatter(
                x=[0, 1],
                y=[0, 1],
                mode="lines",
                name="Perfect Calibration (y = x)",
                line=dict(dash="dash", color=SEMANTIC["neutral"]),
            )
        )
        for inn, col, sym in [(1, SEMANTIC["structure"], "circle"), (2, SEMANTIC["positive"], "diamond")]:
            sub = wp_cal[wp_cal["innings"] == inn]
            fig_cal.add_trace(
                go.Scatter(
                    x=sub["predicted"],
                    y=sub["observed"],
                    mode="lines+markers",
                    name=f"Innings {inn} WP (5-Fold Match CV)",
                    marker=dict(size=8, color=col, symbol=sym),
                    line=dict(width=2.5, color=col),
                    hovertemplate="Predicted WP: %{x:.3f}<br>Observed Win Rate: %{y:.3f}<br>n=%{customdata}<extra></extra>",
                    customdata=sub["n"],
                )
            )
        apply_piq_theme(fig_cal, "1. Win-Probability Calibration — 5-Fold Cross-Fitted Out-of-Sample", height=CHART_H_PAIR)
        fig_cal.update_xaxes(title_text="Predicted Pre-Delivery Win Probability")
        fig_cal.update_yaxes(title_text="Observed Empirical Win Frequency")
        st.plotly_chart(fig_cal, use_container_width=True)

    with c2:
        bc_runs = base_cal[base_cal["target"].isin(["Batter Runs per Ball", "Bowler Runs Conceded per Ball"])]
        fig_bcal = px.scatter(
            bc_runs,
            x="pred",
            y="obs",
            color="target",
            symbol="format_group",
            size="n",
            color_discrete_sequence=[SEMANTIC["positive"], SEMANTIC["structure"]],
            hover_data=["innings", "phase", "wkts_bucket", "pressure_level", "n"],
            labels={"pred": "Predicted Runs / Ball (Trained < 2025)", "obs": "Observed Runs / Ball (Test ≥ 2025)", "target": "Baseline"},
        )
        mn = float(min(bc_runs["pred"].min(), bc_runs["obs"].min()))
        mx = float(max(bc_runs["pred"].max(), bc_runs["obs"].max()))
        fig_bcal.add_trace(
            go.Scatter(x=[mn, mx], y=[mn, mx], mode="lines", name="y = x", line=dict(dash="dash", color=SEMANTIC["neutral"]))
        )
        apply_piq_theme(fig_bcal, "2. Chronological Baseline Calibration — 2022–24 Fit vs 2025–26 Test Split", height=CHART_H_PAIR)
        st.plotly_chart(fig_bcal, use_container_width=True)

    # Row 2: 3. Sensitivity Rank Correlation & 4. Official Top-10 Rank Stability Heatmap
    role_s = st.radio("Select Discipline for Chart 4 (Top-10 Scenario Rank Trajectory)", ["batting", "bowling"], horizontal=True, key="sec06_rs")
    c3, c4 = st.columns(2)
    with c3:
        fig_sens = px.bar(
            sens_sum,
            x="spearman",
            y="scenario",
            color="kind",
            barmode="group",
            orientation="h",
            color_discrete_map={"batting": SEMANTIC["positive"], "bowling": SEMANTIC["structure"]},
            text=sens_sum["spearman"].round(2),
            labels={"spearman": "Spearman Rank Correlation (ρ) vs Official", "scenario": "Sensitivity Scenario", "kind": "Discipline"},
        )
        fig_sens.update_xaxes(range=[0, 1.08])
        apply_piq_theme(fig_sens, "3. Sensitivity Rank Stability — Spearman Correlation Across 13 Specs", height=420)
        st.plotly_chart(fig_sens, use_container_width=True)

    with c4:
        sm = sens_moves[sens_moves["kind"] == role_s].copy()
        ref_rank = bat_rank if role_s == "batting" else bowl_rank
        top10_names = ref_rank.sort_values("rank").head(10)["player_name"].tolist()
        piv = sm.pivot(index="player_name", columns="scenario", values="scenario_rank")
        piv = piv.reindex([n for n in top10_names if n in piv.index])
        fig_rs = px.imshow(
            piv,
            color_continuous_scale="Teal_r",
            aspect="auto",
            text_auto=".0f",
            labels=dict(x="Sensitivity Scenario", y="Official Top-10 Player", color="Rank"),
        )
        apply_piq_theme(fig_rs, f"4. Top-10 {role_s.title()} Rank Trajectory — Stability Across 13 Sensitivity Specs", height=420)
        st.plotly_chart(fig_rs, use_container_width=True)

    # Row 3: 5. Outlier Dependence & Automated 23-Check Validation Gate Ledger
    c5, c6 = st.columns(2)
    with c5:
        el_b = bat_rank[bat_rank["eligible"]].sort_values("rank").head(15).copy()
        el_b["top_match_pct"] = el_b["top_match_share"] * 100
        fig_out = px.scatter(
            el_b,
            x="top_match_pct",
            y="rpr",
            size="p_matches",
            color="success_rate",
            text="player_name",
            color_continuous_scale=[[0.0, SEMANTIC["pressure"]], [0.5, "#38BDF8"], [1.0, SEMANTIC["positive"]]],
            labels={
                "top_match_pct": "Single Best Match Share of Positive Value (%)",
                "rpr": "Reliable Pressure Rating (RPR, CABV/100b)",
                "success_rate": "Success Rate",
            },
        )
        fig_out.update_traces(textposition="top center", marker=dict(line=dict(width=0.8, color="#FFFFFF")))
        apply_piq_theme(fig_out, "5. Single-Match Concentration Check — Top-Match Share vs RPR (Top 15 Batters)", height=CHART_H_FULL)
        st.plotly_chart(fig_out, use_container_width=True)

    with c6:
        st.markdown("#### Automated 23-Check Validation Gate Ledger")
        st.dataframe(gate, use_container_width=True, hide_index=True, height=345)

    st.markdown("#### Out-of-Sample Model Validation & Split-Sample Persistence Summary")
    t1, t2, t3 = st.tabs(["Win Probability & Resource Validation", "Expected Baseline Chronological Skill", "Format & Temporal Split Correlations"])
    with t1:
        st.dataframe(wp_val.round(4), use_container_width=True, hide_index=True)
        st.dataframe(res_val.round(4), use_container_width=True, hide_index=True)
    with t2:
        st.dataframe(base_val.round(4), use_container_width=True, hide_index=True)
    with t3:
        st.dataframe(split_corrs.round(3), use_container_width=True, hide_index=True)

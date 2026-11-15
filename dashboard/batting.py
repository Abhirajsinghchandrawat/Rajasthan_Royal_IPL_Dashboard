"""SECTION 02 — BATTING INTELLIGENCE (MASTER_PROMPT.md Section 6 & Section 12)."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.charts import (
    apply_piq_theme,
    dumbbell_chart,
    horizontal_leaderboard,
    style_single_box,
)
from components.data_loader import load_parquet, load_summary_meta
from components.kpi_cards import page_header, render_kpi_row
from components.player_profile import render_batter_drilldown, render_two_player_comparison
from config.settings import CHART_H_FULL, CHART_H_PAIR, COLORS, DIVERGING_SCALE, SEMANTIC


def render_batting_intelligence(filters: dict) -> None:
    meta = load_summary_meta()
    bat_rank = load_parquet("batting_rankings")
    bat_mt = load_parquet("batting_match_table")
    bat_seasons = load_parquet("batting_seasons")

    page_header(
        "SECTION 02 · BATTING INTELLIGENCE",
        "Context-adjusted batting contribution (CABV / 100b), strike-rate vs survival trade-offs, and Pressure Response Delta",
        is_official_mode=filters["is_official"],
        status=meta.get("validation_status", "VALIDATED"),
    )

    if bat_rank.empty:
        st.warning("Batting analytical datasets not found.")
        return

    el = bat_rank[bat_rank["eligible"]].copy()
    tot_p_runs = int(el["p_runs"].sum())
    tot_p_balls = int(el["p_balls"].sum())
    mean_p_sr = 100 * tot_p_runs / max(tot_p_balls, 1)
    mean_dot = float(el["p_dot_pct"].mean())
    mean_bnd = float(el["p_boundary_pct"].mean())
    mean_dis = float(el["p_dismissal_rate"].mean())
    top_bat = el.sort_values("rpr", ascending=False).iloc[0]

    render_kpi_row(
        [
            {"label": "Pressure Runs (Eligible)", "value": f"{tot_p_runs:,}", "sub": f"across {tot_p_balls:,} pressure balls faced", "accent": "navy"},
            {"label": "Cohort Pressure SR", "value": f"{mean_p_sr:.1f}", "sub": f"Expected SR: {el['p_exp_sr'].mean():.1f} runs/100b", "accent": "teal"},
            {"label": "Mean Pressure Dot %", "value": f"{mean_dot:.1f}%", "sub": "0-run non-dismissal balls faced", "accent": "navy"},
            {"label": "Mean Boundary %", "value": f"{mean_bnd:.1f}%", "sub": "4s + 6s per 100 pressure balls", "accent": "teal"},
            {"label": "Mean Dismissal Rate", "value": f"{mean_dis:.2f} / 100b", "sub": "Striker outs per 100 pressure balls", "accent": "coral"},
            {"label": "#1 Batter (RPR)", "value": f"{top_bat['player_name']}", "sub": f"RPR: {top_bat['rpr']:+.2f} · APR: {top_bat['rating_mean']:+.2f} · PRD: {top_bat['prd']:+.2f}", "accent": "featured"},
        ]
    )

    # Row 1: 1. Batter Performance Matrix & 2. Context-Adjusted Leaderboard
    c1, c2 = st.columns(2)
    with c1:
        fig_mat = px.scatter(
            el,
            x="p_dismissal_rate",
            y="p_sr",
            size="p_balls",
            color="rating_mean",
            hover_name="player_name",
            hover_data={"p_balls": True, "p_matches": True, "rpr": ":.2f", "prd": ":.2f"},
            color_continuous_scale=DIVERGING_SCALE,
            color_continuous_midpoint=0.0,
            labels={
                "p_dismissal_rate": "Pressure Dismissal Rate (Outs / 100 Balls — Lower is Better)",
                "p_sr": "Pressure Strike Rate (Runs / 100 Balls)",
                "rating_mean": "APR (/100b)",
            },
        )
        fig_mat.update_traces(marker=dict(line=dict(width=0.8, color="#FFFFFF"), opacity=0.9))
        fig_mat.add_hline(y=el["p_sr"].median(), line_dash="dot", line_color=SEMANTIC["neutral"], annotation_text="Median SR")
        fig_mat.add_vline(x=el["p_dismissal_rate"].median(), line_dash="dot", line_color=SEMANTIC["neutral"], annotation_text="Median Dismissal")
        apply_piq_theme(fig_mat, "1. Batter Performance Matrix — Pressure SR vs Dismissal Rate", height=CHART_H_PAIR)
        st.plotly_chart(fig_mat, use_container_width=True)

    with c2:
        top12 = el.sort_values("rank").head(12).copy()
        top12["label"] = "#" + top12["rank"].astype(int).astype(str) + " " + top12["player_name"]
        fig_lb = horizontal_leaderboard(
            top12,
            "rating_mean",
            "label",
            "2. Context-Adjusted Batting Leaderboard — Ordered by RPR Rank (APR + 90% CI)",
            "Shrunk CABV / 100 Pressure Balls (Bars = APR, ◆ = Official RPR)",
            order_col="rank",
            ci_lo="ci_lo",
            ci_hi="ci_hi",
            marker_col="rpr",
            marker_name="RPR (90% Lower Bound)",
            value_name="Shrunk Mean (APR)",
            height=CHART_H_PAIR,
        )
        st.plotly_chart(fig_lb, use_container_width=True)

    # Row 2: 3. Normal vs Pressure Dumbbell & 4. Pressure SR Distribution
    c3, c4 = st.columns(2)
    with c3:
        top12_d = el.sort_values("rank", ascending=True).head(12).sort_values("rank", ascending=False).copy()
        top12_d["rank_label"] = "#" + top12_d["rank"].astype(int).astype(str) + " " + top12_d["player_name"]
        fig_db = dumbbell_chart(
            top12_d,
            "rank_label",
            "nr_post_mean",
            "pr_post_mean",
            "3. Normal vs Pressure Contribution — Top 12 Batters (PRD = APR − Normal)",
            "Shrunk Context-Adjusted Batting Value (CABV / 100 Balls)",
            height=CHART_H_PAIR,
        )
        st.plotly_chart(fig_db, use_container_width=True)

    with c4:
        fig_sr = go.Figure()
        fig_sr.add_trace(
            go.Histogram(
                x=el["n_sr"].dropna(),
                name="Normal State SR (Baseline)",
                marker_color=SEMANTIC["neutral"],
                nbinsx=24,
                opacity=0.60,
            )
        )
        fig_sr.add_trace(
            go.Histogram(
                x=el["p_sr"],
                name="Pressure State SR (Elevated + High)",
                marker_color=SEMANTIC["positive"],
                nbinsx=24,
                opacity=0.82,
            )
        )
        fig_sr.update_layout(barmode="overlay")
        fig_sr.add_vline(x=el["p_sr"].median(), line_dash="dash", line_color=SEMANTIC["positive"], annotation_text="Pressure Median")
        fig_sr.add_vline(x=el["n_sr"].median(), line_dash="dot", line_color=SEMANTIC["neutral_dark"], annotation_text="Normal Median")
        apply_piq_theme(fig_sr, "4. Strike Rate Distribution — Pressure vs Normal States (Eligible Batters)", height=CHART_H_PAIR)
        fig_sr.update_xaxes(title_text="Strike Rate (Runs / 100 Balls)")
        fig_sr.update_yaxes(title_text="Eligible Batters")
        st.plotly_chart(fig_sr, use_container_width=True)

    # Row 3: 5. Match-Level Performance Distribution for Top 10 Batters
    top10_ordered = el.sort_values("rank").head(10)
    top10_ids = top10_ordered["player_id"].tolist()
    top10_names = top10_ordered["player_name"].tolist()
    pm_top10 = bat_mt[(bat_mt["player_id"].isin(top10_ids)) & (bat_mt["context"] == "pressure")].copy()
    fig_box = px.box(
        pm_top10,
        x="player_name",
        y="value",
        points="outliers",
        category_orders={"player_name": top10_names},
        labels={"player_name": "Official Top 10 Batters (Ordered #1 to #10)", "value": "Match Pressure CABV (Runs)"},
    )
    style_single_box(fig_box, SEMANTIC["positive"])
    fig_box.add_hline(y=0, line_dash="dash", line_color=SEMANTIC["neutral"])
    apply_piq_theme(fig_box, "5. Match-Level Pressure Contribution — Official Top 10 Batters (CABV Runs)", height=CHART_H_FULL)
    st.plotly_chart(fig_box, use_container_width=True)

    st.markdown("---")
    tab1, tab2 = st.tabs(["Individual Batter Profile Drill-Down", "Two-Batter Head-to-Head Comparison"])
    with tab1:
        render_batter_drilldown(bat_rank, bat_mt, bat_seasons, key_prefix="sec02_bat")
    with tab2:
        render_two_player_comparison(bat_rank, kind="batting", key_prefix="sec02_cmp")

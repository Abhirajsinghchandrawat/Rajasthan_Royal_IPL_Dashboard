"""SECTION 04 — RELIABILITY LAB (MASTER_PROMPT.md Section 9 & Section 12)."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.charts import apply_piq_theme, forest_plot, style_single_box
from components.data_loader import load_parquet, load_summary_meta
from components.kpi_cards import callout, page_header, render_kpi_row, signed_accent
from config.settings import CHART_H_FULL, CHART_H_PAIR, COLORS, IDENTITY_SEQ, SEMANTIC


def render_reliability_lab(filters: dict) -> None:
    meta = load_summary_meta()
    bat_rank = load_parquet("batting_rankings")
    bowl_rank = load_parquet("bowling_rankings")
    bat_mt = load_parquet("batting_match_table")
    bowl_mt = load_parquet("bowling_match_table")
    bat_seasons = load_parquet("batting_seasons")
    bowl_seasons = load_parquet("bowling_seasons")

    page_header(
        "SECTION 04 · RELIABILITY LAB",
        "Distinguishing repeatable pressure mastery from small-sample volatility via match-cluster bootstrap & Empirical Bayes",
        is_official_mode=filters["is_official"],
        status=meta.get("validation_status", "VALIDATED"),
    )

    role = st.radio("Select Analytical Discipline", ["Batting Reliability", "Bowling Reliability"], horizontal=True)
    is_bat = role == "Batting Reliability"
    df = bat_rank if is_bat else bowl_rank
    mt = bat_mt if is_bat else bowl_mt
    seasons = bat_seasons if is_bat else bowl_seasons
    role_meta = meta.get("batting_meta" if is_bat else "bowling_meta", {})
    unit_lbl = "CABV / 100 Pressure Balls" if is_bat else "Runs Prevented / 24 Pressure Deliveries"
    balls_col = "p_balls" if is_bat else "p_legal"

    el = df[df["eligible"]].copy()
    perf_med = role_meta.get("quadrant_perf_threshold", float(el["rating_mean"].median()))
    rel_med = role_meta.get("quadrant_reliability_threshold", float(el["success_rate"].median()))

    render_kpi_row(
        [
            {"label": "Median PRD (Eligible)", "value": f"{el['prd'].median():+.2f}", "sub": f"Unit: {unit_lbl}", "accent": signed_accent(el["prd"].median())},
            {"label": "Median Match Success %", "value": f"{rel_med*100:.1f}%", "sub": "Share of pressure matches with value > 0", "accent": "teal"},
            {"label": "Median IQR (Match Runs)", "value": f"{el['iqr_match'].median():.2f} runs", "sub": "75th − 25th match contribution spread", "accent": "navy"},
            {"label": "Median Pressure Matches", "value": f"{int(el['p_matches'].median())}", "sub": "Min threshold: 10 unique matches", "accent": "navy"},
            {"label": "Median Shrinkage Weight B", "value": f"{el['pr_shrink_weight'].median():.2f}", "sub": "τ² / (τ² + SE²) signal retention", "accent": "amber"},
            {"label": "Multi-Season Stability", "value": f"{el['season_positive_share'].dropna().mean()*100:.1f}%", "sub": "Qualifying seasons (≥30b) with rate > 0", "accent": "teal"},
        ]
    )

    callout(
        f"<b>Documented Quadrant Thresholds:</b> Quadrants are defined strictly on the eligible population medians: "
        f"Shrunk Performance threshold = <b>{perf_med:+.2f}</b> ({unit_lbl}) and Match Success Rate threshold = <b>{rel_med*100:.1f}%</b>. "
        f"Players in <b>High performance / High reliability</b> exceed both benchmarks."
    )

    # Row 1: 1. Quadrant Plot & 2. Confidence Interval Forest Plot
    c1, c2 = st.columns(2)
    with c1:
        el["success_pct"] = el["success_rate"] * 100
        quad_colors = {
            "High performance / High reliability": SEMANTIC["positive"],
            "High performance / Low reliability": SEMANTIC["pressure"],
            "Low performance / High reliability": SEMANTIC["structure_soft"],
            "Low performance / Low reliability": SEMANTIC["negative"],
        }
        quad_symbols = {
            "High performance / High reliability": "diamond",
            "High performance / Low reliability": "triangle-up",
            "Low performance / High reliability": "circle",
            "Low performance / Low reliability": "x",
        }
        fig_q = px.scatter(
            el,
            x="success_pct",
            y="rating_mean",
            color="quadrant",
            symbol="quadrant",
            size=balls_col,
            hover_name="player_name",
            hover_data={"rpr": ":.2f", "prd": ":.2f", "p_matches": True, "top_match_share": ":.2f"},
            color_discrete_map=quad_colors,
            symbol_map=quad_symbols,
            labels={
                "success_pct": "Match Success Rate (% of Pressure Matches > 0)",
                "rating_mean": f"Shrunk Mean ({unit_lbl})",
                "quadrant": "Quadrant",
            },
        )
        fig_q.update_traces(marker=dict(line=dict(width=0.7, color="#FFFFFF"), opacity=0.9))
        fig_q.add_hline(y=perf_med, line_dash="dash", line_color=SEMANTIC["structure"], annotation_text="Median APR")
        fig_q.add_vline(x=rel_med * 100, line_dash="dash", line_color=SEMANTIC["structure"], annotation_text="Median Success %")
        apply_piq_theme(fig_q, "1. Performance vs Reliability Quadrant — Eligible Cohort (APR vs Success %)", height=CHART_H_PAIR)
        st.plotly_chart(fig_q, use_container_width=True)

    with c2:
        top15 = el.sort_values("rank", ascending=True).head(15).copy()
        top15["label"] = "#" + top15["rank"].astype(int).astype(str) + " " + top15["player_name"]
        fig_fp = forest_plot(
            top15,
            "label",
            "rating_mean",
            "ci_lo",
            "ci_hi",
            "rpr",
            "2. Empirical Bayes 90% CI & RPR — Top 15 Players Forest Plot",
            unit_lbl,
            height=CHART_H_PAIR,
        )
        st.plotly_chart(fig_fp, use_container_width=True)

    # Row 2: 3. Sample Size vs Performance Funnel & 4. Multi-Season Stability Line Chart
    c3, c4 = st.columns(2)
    with c3:
        sub_all = df[df["pr_n_matches"].fillna(0) >= 3].copy()
        fig_sc = go.Figure()
        fig_sc.add_trace(
            go.Scatter(
                x=sub_all[balls_col],
                y=sub_all["pr_rate"],
                mode="markers",
                name="Raw Observed Rate",
                marker=dict(color=SEMANTIC["neutral"], symbol="circle-open", size=7, opacity=0.65, line=dict(width=1.4)),
                text=sub_all["player_name"],
                hovertemplate="<b>%{text}</b><br>Balls: %{x}<br>Raw Rate: %{y:+.2f}<extra></extra>",
            )
        )
        fig_sc.add_trace(
            go.Scatter(
                x=sub_all[balls_col],
                y=sub_all["rating_mean"],
                mode="markers",
                name="Empirical-Bayes Shrunk Rate (APR)",
                marker=dict(color=SEMANTIC["positive"], symbol="diamond", size=7, opacity=0.88),
                text=sub_all["player_name"],
                hovertemplate="<b>%{text}</b><br>Balls: %{x}<br>Shrunk APR: %{y:+.2f}<extra></extra>",
            )
        )
        fig_sc.add_vline(
            x=100 if is_bat else 120,
            line_dash="dash",
            line_color=SEMANTIC["pressure"],
            annotation_text="Min Ball Cutoff",
        )
        fig_sc.add_hline(y=0, line_dash="dot", line_color=SEMANTIC["neutral"])
        apply_piq_theme(fig_sc, "3. Sample Size vs Performance — Empirical Bayes Shrinkage Funnel", height=CHART_H_PAIR)
        fig_sc.update_xaxes(title_text="Pressure Balls Faced" if is_bat else "Pressure Legal Balls Bowled")
        fig_sc.update_yaxes(title_text=unit_lbl)
        st.plotly_chart(fig_sc, use_container_width=True)

    with c4:
        top6_ordered = el.sort_values("rank").head(6)
        top6_ids = top6_ordered["player_id"].tolist()
        top6_names = top6_ordered["player_name"].tolist()
        s_top = seasons[(seasons["player_id"].isin(top6_ids)) & (seasons["qualifying"])].sort_values("season")
        fig_ss = px.line(
            s_top,
            x="season",
            y="rate",
            color="player_name",
            markers=True,
            category_orders={"player_name": top6_names},
            color_discrete_sequence=IDENTITY_SEQ,
            labels={"season": "Season Year", "rate": unit_lbl, "player_name": "Top-6 Player"},
        )
        fig_ss.add_hline(y=0, line_dash="dash", line_color=SEMANTIC["neutral"])
        apply_piq_theme(fig_ss, "4. Multi-Season Stability Trajectory — Top 6 Players (≥ 30b/season)", height=CHART_H_PAIR)
        st.plotly_chart(fig_ss, use_container_width=True)

    # Row 3: 5. Match-Level Contribution Box & Strip Plot
    top10_ordered = el.sort_values("rank").head(10)
    top10_ids = top10_ordered["player_id"].tolist()
    top10_names = top10_ordered["player_name"].tolist()
    pm_10 = mt[(mt["player_id"].isin(top10_ids)) & (mt["context"] == "pressure")].copy()
    fig_bx = px.box(
        pm_10,
        x="player_name",
        y="value",
        points="all",
        category_orders={"player_name": top10_names},
        labels={"player_name": "Official Top 10 Ranked Players (Ordered #1 to #10)", "value": "Single-Match Net Pressure Value (Runs)"},
    )
    style_single_box(fig_bx, SEMANTIC["positive"])
    fig_bx.add_hline(y=0, line_dash="dash", line_color=SEMANTIC["neutral"])
    apply_piq_theme(fig_bx, "5. Match-Level Contribution Box & Strip Plot — Top 10 Players", height=CHART_H_FULL)
    st.plotly_chart(fig_bx, use_container_width=True)

"""SECTION 03 — BOWLING INTELLIGENCE (MASTER_PROMPT.md Section 7 & Section 12)."""

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
from components.kpi_cards import callout, page_header, render_kpi_row
from components.player_profile import render_bowler_drilldown, render_two_player_comparison
from config.settings import CHART_H_FULL, CHART_H_PAIR, COLORS, DIVERGING_SCALE, SEMANTIC


def render_bowling_intelligence(filters: dict) -> None:
    meta = load_summary_meta()
    bowl_rank = load_parquet("bowling_rankings")
    bowl_mt = load_parquet("bowling_match_table")
    bowl_seasons = load_parquet("bowling_seasons")
    bowl_phases = load_parquet("bowling_phases")

    page_header(
        "SECTION 03 · BOWLING INTELLIGENCE",
        "Defensive difficulty context, Context-Adjusted Runs Prevented (RP / 24 deliveries), and phase effectiveness",
        is_official_mode=filters["is_official"],
        status=meta.get("validation_status", "VALIDATED"),
    )

    if bowl_rank.empty:
        st.warning("Bowling analytical datasets not found.")
        return

    el = bowl_rank[bowl_rank["eligible"]].copy()
    tot_legal = int(el["p_legal"].sum())
    tot_conc = float(el["p_conceded"].sum())
    tot_wkts = int(el["p_wickets"].sum())
    cohort_econ = 6 * tot_conc / max(tot_legal, 1)
    cohort_wr = 100 * tot_wkts / max(tot_legal, 1)
    top_bowl = el.sort_values("rpr", ascending=False).iloc[0]

    render_kpi_row(
        [
            {"label": "Cohort Pressure Economy", "value": f"{cohort_econ:.2f} RPO", "sub": f"Expected Econ: {el['p_exp_economy'].mean():.2f} RPO", "accent": "navy"},
            {"label": "Pressure Wicket Rate", "value": f"{cohort_wr:.2f} / 100b", "sub": f"{tot_wkts:,} bowler-credited wkts / 100 legal b", "accent": "teal"},
            {"label": "Mean Pressure Dot %", "value": f"{el['p_dot_pct'].mean():.1f}%", "sub": "Legal 0-run non-wicket balls", "accent": "teal"},
            {"label": "Boundary Conceded %", "value": f"{el['p_boundary_pct'].mean():.1f}%", "sub": "4s + 6s per 100 pressure deliveries", "accent": "coral"},
            {"label": "Pressure Legal Balls", "value": f"{tot_legal:,}", "sub": f"across {len(el)} eligible bowlers", "accent": "navy"},
            {"label": "#1 Bowler (RPR)", "value": f"{top_bowl['player_name']}", "sub": f"RPR: {top_bowl['rpr']:+.2f} · APR: {top_bowl['rating_mean']:+.2f} · PRD: {top_bowl['prd']:+.2f}", "accent": "featured"},
        ]
    )

    with st.expander("Analytical Metric Guide — Reconciling RPR (+1.13), Shrunk APR (+2.65), and PRD (−2.35)", expanded=False):
        st.markdown(
            f"""
            All three bowling value metrics are expressed in **Context-Adjusted Runs Prevented per 24 bowling deliveries** (equivalent to a 4-over spell, including marginal wicket-value credit $0.20 \\times WV \\times (\\text{{wkt}} - E[\\text{{wkt}} \\mid \\text{{ctx}}])$):

            1. **Raw Observed Pressure Rate (`pr_rate` = `{top_bowl['pr_rate']:+.2f}` / 24 deliveries for #1 {top_bowl['player_name']}):** Across `{int(top_bowl['p_balls'])}` pressure deliveries (`{int(top_bowl['p_legal'])}` legal balls in `{int(top_bowl['p_matches'])}` matches), {top_bowl['player_name']} conceded `{int(top_bowl['p_conceded'])}` runs against `{top_bowl['p_exp_conceded']:.1f}` expected (economy `{top_bowl['p_economy']:.2f}` vs `{top_bowl['p_exp_economy']:.2f}` expected), yielding a raw observed rate of **`{top_bowl['pr_rate']:+.2f}` runs prevented / 24 deliveries** with match-cluster bootstrap `SE = {top_bowl['pr_se']:.2f}`.
            2. **Shrunk Pressure Mean (`APR` / `rating_mean` = `{top_bowl['rating_mean']:+.2f}` / 24 deliveries):** Single-spell bowling outcomes carry substantial match-to-match variance. Volume-weighted Empirical Bayes shrinks each bowler's raw rate toward the eligible population prior (`+0.13 / 24b`, signal retention $B_p = {top_bowl['pr_shrink_weight']:.2f}$), giving a posterior mean of **`{top_bowl['rating_mean']:+.2f}` / 24 deliveries** (`90% CI: [{top_bowl['ci_lo']:+.2f}, {top_bowl['ci_hi']:+.2f}]`).
            3. **Reliable Pressure Rating (`RPR` = `{top_bowl['rpr']:+.2f}` / 24 deliveries — Official Ranking Estimand):** The one-sided 90% Empirical-Bayes lower confidence bound ($\\text{{APR}} - 1.2816 \\times \\text{{SD}}_{{\\text{{post}}}}$). With 90% confidence, {top_bowl['player_name']}'s true pressure bowling contribution exceeds **`{top_bowl['rpr']:+.2f}` runs prevented / 24 deliveries** (#1 among all `{len(el)}` eligible bowlers).
            4. **Why Pressure Response Delta (`PRD` = `{top_bowl['prd']:+.2f}` / 24 deliveries) is negative despite #1 pressure ranking:** `PRD = Shrunk_Pressure_Mean (APR) − Shrunk_Normal_Mean`. In normal (low-pressure) states (`{int(top_bowl['n_balls'])}` deliveries, economy `{top_bowl['n_economy']:.2f}` vs `{top_bowl['n_exp_economy']:.2f}` expected), {top_bowl['player_name']}'s baseline is a historic outlier (**`{top_bowl['nr_rate']:+.2f}` raw** and **`{top_bowl['nr_post_mean']:+.2f}` shrunk** per 24 deliveries, because normal states have ~2× larger sample volume and higher population signal retention $B_n = {top_bowl['nr_shrink_weight']:.2f}$). Thus `PRD = +2.65 − 5.00 = −2.35 / 24b` reflects both his extraordinary normal-state ceiling and stronger Empirical-Bayes shrinkage on the smaller pressure sample — **not** poor pressure bowling.
            """
        )

    # Row 1: 1. Bowling Effectiveness Matrix & 2. Context-Adjusted Runs Prevented Leaderboard
    c1, c2 = st.columns(2)
    with c1:
        fig_mat = px.scatter(
            el,
            x="p_economy",
            y="p_wicket_rate",
            size="p_legal",
            color="rating_mean",
            hover_name="player_name",
            hover_data={"p_legal": True, "p_matches": True, "rpr": ":.2f", "prd": ":.2f"},
            color_continuous_scale=DIVERGING_SCALE,
            color_continuous_midpoint=0.0,
            labels={
                "p_economy": "Pressure Economy Rate (Runs / Over — Reversed: Left is Better)",
                "p_wicket_rate": "Pressure Wicket Rate (Wickets / 100 Legal Balls)",
                "rating_mean": "APR (/24b)",
            },
        )
        fig_mat.update_traces(marker=dict(line=dict(width=0.8, color="#FFFFFF"), opacity=0.9))
        fig_mat.update_xaxes(autorange="reversed")
        fig_mat.add_hline(y=el["p_wicket_rate"].median(), line_dash="dot", line_color=SEMANTIC["neutral"], annotation_text="Median Wkt Rate")
        fig_mat.add_vline(x=el["p_economy"].median(), line_dash="dot", line_color=SEMANTIC["neutral"], annotation_text="Median Econ")
        apply_piq_theme(fig_mat, "1. Bowling Effectiveness Matrix — Economy vs Wicket Rate (Reversed X)", height=CHART_H_PAIR)
        st.plotly_chart(fig_mat, use_container_width=True)

    with c2:
        top12 = el.sort_values("rank").head(12).copy()
        top12["label"] = "#" + top12["rank"].astype(int).astype(str) + " " + top12["player_name"]
        fig_lb = horizontal_leaderboard(
            top12,
            "rating_mean",
            "label",
            "2. Context-Adjusted Runs Prevented — Ordered by RPR Rank (APR + 90% CI)",
            "Shrunk Runs Prevented / 24 Pressure Deliveries (Bars = APR, ◆ = Official RPR)",
            order_col="rank",
            ci_lo="ci_lo",
            ci_hi="ci_hi",
            marker_col="rpr",
            marker_name="RPR (90% Lower Bound)",
            value_name="Shrunk Mean (APR)",
            height=CHART_H_PAIR,
        )
        st.plotly_chart(fig_lb, use_container_width=True)

    # Row 2: 3. Bowling Phase Heatmap & 4. Normal vs Pressure Bowling Value
    c3, c4 = st.columns(2)
    top10_ordered = el.sort_values("rank").head(10)
    top10_ids = top10_ordered["player_id"].tolist()
    top10_names = top10_ordered["player_name"].tolist()

    with c3:
        ph_sub = bowl_phases[
            (bowl_phases["player_id"].isin(top10_ids)) & (bowl_phases["pressure_level"].isin(["Elevated", "High"]))
        ].copy()
        ph_agg = (
            ph_sub.groupby(["player_name", "phase"], observed=True)
            .agg(val=("value", "sum"), balls=("balls", "sum"))
            .reset_index()
        )
        ph_agg["rp_per24"] = 24 * ph_agg["val"] / ph_agg["balls"].clip(lower=1)
        piv = ph_agg.pivot(index="player_name", columns="phase", values="rp_per24")
        piv = piv[[c for c in ["Powerplay", "Middle", "Death"] if c in piv.columns]]
        piv = piv.reindex([n for n in top10_names if n in piv.index])
        piv.index = [f"#{i+1} {name}" for i, name in enumerate(piv.index)]
        fig_hm = px.imshow(
            piv,
            color_continuous_scale=DIVERGING_SCALE,
            color_continuous_midpoint=0.0,
            aspect="auto",
            text_auto=".2f",
            labels=dict(x="Innings Phase", y="Official Top-10 Bowler", color="RP / 24b"),
        )
        apply_piq_theme(fig_hm, "3. Bowling Phase Heatmap — Top 10 Bowlers (Observed RP / 24 Deliveries)", height=CHART_H_PAIR)
        st.plotly_chart(fig_hm, use_container_width=True)

    with c4:
        top12_d = el.sort_values("rank", ascending=True).head(12).sort_values("rank", ascending=False).copy()
        top12_d["rank_label"] = "#" + top12_d["rank"].astype(int).astype(str) + " " + top12_d["player_name"]
        fig_db = dumbbell_chart(
            top12_d,
            "rank_label",
            "nr_post_mean",
            "pr_post_mean",
            "4. Normal vs Pressure Bowling Value — Top 12 Bowlers (PRD = APR − Normal)",
            "Shrunk Runs Prevented / 24 Deliveries",
            height=CHART_H_PAIR,
        )
        st.plotly_chart(fig_db, use_container_width=True)

    # Row 3: 5. Match-Level Bowling Distribution
    pm_top10 = bowl_mt[(bowl_mt["player_id"].isin(top10_ids)) & (bowl_mt["context"] == "pressure")].copy()
    fig_box = px.box(
        pm_top10,
        x="player_name",
        y="value",
        points="outliers",
        category_orders={"player_name": top10_names},
        labels={"player_name": "Official Top 10 Bowlers (Ordered #1 to #10)", "value": "Match Pressure RP Value (Runs)"},
    )
    style_single_box(fig_box, SEMANTIC["positive"])
    fig_box.add_hline(y=0, line_dash="dash", line_color=SEMANTIC["neutral"])
    apply_piq_theme(fig_box, "5. Match-Level Pressure Bowling Value — Official Top 10 Bowlers (RP Runs)", height=CHART_H_FULL)
    st.plotly_chart(fig_box, use_container_width=True)

    st.markdown("---")
    tab1, tab2 = st.tabs(["Individual Bowler Profile Drill-Down", "Two-Bowler Head-to-Head Comparison"])
    with tab1:
        render_bowler_drilldown(bowl_rank, bowl_mt, bowl_seasons, key_prefix="sec03_bowl")
    with tab2:
        render_two_player_comparison(bowl_rank, kind="bowling", key_prefix="sec03_cmp")

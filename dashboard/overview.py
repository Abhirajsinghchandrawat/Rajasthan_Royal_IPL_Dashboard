"""SECTION 00 — EXECUTIVE OVERVIEW (MASTER_PROMPT.md Section 12)."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.charts import apply_piq_theme, horizontal_leaderboard
from components.data_loader import load_parquet, load_summary_meta
from components.kpi_cards import callout, page_header, render_kpi_row
from config.settings import COLORS, LEVEL_COLORS, SEMANTIC


def _podium_card_html(r: pd.Series, role_label: str, balls_col: str, unit_short: str) -> str:
    prd_val = float(r["prd"])
    prd_col = "#0F766E" if prd_val >= 0 else "#B91C1C"
    return f"""
    <div class="piq-panel piq-podium" style="border-top:3px solid {SEMANTIC['positive']} !important;">
        <div class="piq-podium-rank">RANK #{int(r['rank'])} {role_label}</div>
        <div class="piq-podium-name" title="{r['player_name']}">{r['player_name']}</div>
        <div class="piq-podium-meta">RPR: <b style="color:#0F766E !important;">{r['rpr']:+.2f}</b> · APR: <b style="color:#14243A !important;">{r['rating_mean']:+.2f}</b> {unit_short}</div>
        <div class="piq-podium-meta">PRD: <b style="color:{prd_col} !important;">{prd_val:+.2f}</b> · {int(r[balls_col])}b ({int(r['p_matches'])}m)</div>
    </div>
    """


def render_overview(filters: dict) -> None:
    meta = load_summary_meta()
    bat_rank = load_parquet("batting_rankings")
    bowl_rank = load_parquet("bowling_rankings")
    fv = load_parquet("face_validity")
    d = load_parquet("deliveries_with_pressure", processed=True)

    status = meta.get("validation_status", "VALIDATED")
    page_header(
        "SECTION 00 · EXECUTIVE OVERVIEW",
        "High-conviction player reliability intelligence across 853 official IPL & T20I matches (2022–2026)",
        is_official_mode=filters["is_official"],
        status=status,
    )

    if not meta or bat_rank.empty:
        st.warning("Analytical pipeline outputs not found. Please run `python -m src.pipeline`.")
        return

    n_elig_bat = int(bat_rank["eligible"].sum())
    n_elig_bowl = int(bowl_rank["eligible"].sum())

    render_kpi_row(
        [
            {
                "label": "Matches Analysed",
                "value": f"{meta['analysed_pressure_matches']:,}",
                "sub": f"of {meta['official_scope_matches']:,} IPL + T20I (16 abandoned excl.)",
                "accent": "navy",
            },
            {
                "label": "Deliveries Analysed",
                "value": f"{meta['pressure_eligible_deliveries']:,}",
                "sub": f"{meta['official_regulation_deliveries']:,} official reg. balls",
                "accent": "navy",
            },
            {
                "label": "Pressure Deliveries",
                "value": f"{meta['pressure_deliveries_bat']:,}",
                "sub": f"High tier: {meta['high_pressure_deliveries_bat']:,} balls",
                "accent": "amber",
            },
            {
                "label": "Pressure Delivery Share",
                "value": f"{meta['pressure_share_bat']*100:.1f}%",
                "sub": f"High share: {meta['high_pressure_share_bat']*100:.1f}% (PI ≥ {meta['thresholds']['high']})",
                "accent": "amber",
            },
            {
                "label": "Eligible Batters",
                "value": f"{n_elig_bat}",
                "sub": "≥ 10 pressure matches & ≥ 100 balls",
                "accent": "teal",
            },
            {
                "label": "Eligible Bowlers",
                "value": f"{n_elig_bowl}",
                "sub": "≥ 10 pressure matches & ≥ 120 legal b",
                "accent": "teal",
            },
        ]
    )

    top3_bat = bat_rank[bat_rank["rank"] <= 3].sort_values("rank")
    top3_bowl = bowl_rank[bowl_rank["rank"] <= 3].sort_values("rank")

    b1 = top3_bat.iloc[0]
    w1 = top3_bowl.iloc[0]
    callout(
        f"<b>Headline Evidence-Backed Discovery:</b> True pressure reliability separates sharply from raw volume. "
        f"In first-innings cricket, raw current run rate correlates negatively with pressure (<b>r = {meta['pressure_meta']['corr_pi_vs_current_rr_inn1']:.2f}</b>), "
        f"proving that late-innings boundary sprees from 160/1 are low-difficulty states rather than crunch moments. "
        f"Once evaluated strictly on pre-delivery deficit and next-ball leverage, <b>{b1['player_name']}</b> leads all eligible batters "
        f"(RPR <b>{b1['rpr']:+.2f}</b> CABV/100b, Shrunk APR <b>{b1['rating_mean']:+.2f}</b> across {int(b1['p_matches'])} matches) and <b>{w1['player_name']}</b> leads all eligible bowlers "
        f"(RPR <b>{w1['rpr']:+.2f}</b>, Shrunk APR <b>{w1['rating_mean']:+.2f}</b> Runs Prevented/24 deliveries across {int(w1['p_matches'])} matches)."
    )

    # Row 1: Top 3 podium cards + Top 10 horizontal leaderboards
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Official Top 3 Batters Under Pressure")
        pcols = st.columns(3)
        for idx, (_, r) in enumerate(top3_bat.iterrows()):
            with pcols[idx]:
                st.markdown(_podium_card_html(r, "BATTER", "p_balls", "/100b"), unsafe_allow_html=True)

        top10_b = bat_rank[bat_rank["rank"] <= 10].sort_values("rank").copy()
        top10_b["label"] = "#" + top10_b["rank"].astype(int).astype(str) + " " + top10_b["player_name"]
        fig_b = horizontal_leaderboard(
            top10_b,
            "rpr",
            "label",
            "1. Top 10 Batters — Reliable Pressure Rating (RPR & Shrunk APR, CABV / 100b)",
            "RPR (90% Lower Bound CABV / 100 Pressure Balls)",
            order_col="rank",
            marker_col="rating_mean",
            marker_name="Shrunk Mean (APR)",
            value_name="RPR (90% Lower Bound)",
            height=385,
        )
        st.plotly_chart(fig_b, use_container_width=True)

    with c2:
        st.markdown("#### Official Top 3 Bowlers Under Pressure")
        pcols = st.columns(3)
        for idx, (_, r) in enumerate(top3_bowl.iterrows()):
            with pcols[idx]:
                st.markdown(_podium_card_html(r, "BOWLER", "p_legal", "/24b"), unsafe_allow_html=True)

        top10_w = bowl_rank[bowl_rank["rank"] <= 10].sort_values("rank").copy()
        top10_w["label"] = "#" + top10_w["rank"].astype(int).astype(str) + " " + top10_w["player_name"]
        fig_w = horizontal_leaderboard(
            top10_w,
            "rpr",
            "label",
            "2. Top 10 Bowlers — Reliable Pressure Rating (RPR & Shrunk APR, RP / 24 Deliveries)",
            "RPR (90% Lower Bound Runs Prevented / 24 Pressure Deliveries)",
            order_col="rank",
            marker_col="rating_mean",
            marker_name="Shrunk Mean (APR)",
            value_name="RPR (90% Lower Bound)",
            height=385,
        )
        st.plotly_chart(fig_w, use_container_width=True)

    # Row 2: Pressure distribution, IPL vs T20I coverage, and Phase breakdown
    pe = d[d["pressure_eligible"]].copy()
    if not filters["is_official"]:
        if filters["competition"] == "IPL Only":
            pe = pe[pe["format_group"] == "IPL"]
        elif filters["competition"] == "T20I Only":
            pe = pe[pe["format_group"] == "T20I"]
        pe = pe[pe["season_year"].isin(filters["seasons"]) & pe["phase"].isin(filters["phases"])]

    c3, c4, c5 = st.columns(3)
    with c3:
        fig_dist = go.Figure()
        for lvl in ["Low", "Elevated", "High"]:
            sub = pe[pe["pressure_level_bat"] == lvl]
            fig_dist.add_trace(
                go.Histogram(
                    x=sub["pi_bat"],
                    name=f"{lvl}",
                    marker_color=LEVEL_COLORS[lvl],
                    nbinsx=35,
                    opacity=0.88,
                )
            )
        fig_dist.update_layout(barmode="stack")
        fig_dist.add_vline(
            x=meta["thresholds"]["elevated"],
            line_dash="dash",
            line_color=SEMANTIC["pressure"],
            annotation_text=f"Elev ({meta['thresholds']['elevated']})",
        )
        fig_dist.add_vline(
            x=meta["thresholds"]["high"],
            line_dash="dash",
            line_color=SEMANTIC["negative"],
            annotation_text=f"High ({meta['thresholds']['high']})",
        )
        apply_piq_theme(fig_dist, "3. Batting Pressure Distribution — Pre-Delivery PI (0–100 Scale)", height=360)
        fig_dist.update_xaxes(title_text="Pressure Index (0–100 Scale)")
        fig_dist.update_yaxes(title_text="Deliveries")
        st.plotly_chart(fig_dist, use_container_width=True)

    with c4:
        fmt_cov = (
            pe.groupby(["format_group", "pressure_level_bat"], observed=True)
            .size()
            .reset_index(name="deliveries")
        )
        fmt_cov["share"] = fmt_cov.groupby("format_group")["deliveries"].transform(lambda s: 100 * s / s.sum())
        fig_fmt = px.bar(
            fmt_cov,
            x="format_group",
            y="share",
            color="pressure_level_bat",
            category_orders={"pressure_level_bat": ["Low", "Elevated", "High"]},
            color_discrete_map=LEVEL_COLORS,
            barmode="group",
            text=fmt_cov["share"].round(1),
            labels={"pressure_level_bat": "Pressure Tier"},
        )
        fig_fmt.update_traces(textposition="outside", cliponaxis=False)
        apply_piq_theme(fig_fmt, "4. IPL vs T20I Pressure Tiers — Share of Format Deliveries (%)", height=360)
        fig_fmt.update_xaxes(title_text="Competition Format")
        fig_fmt.update_yaxes(title_text="Share of Format Deliveries (%)", range=[0, 82])
        st.plotly_chart(fig_fmt, use_container_width=True)

    with c5:
        if not fv.empty:
            fv_plot = fv.copy()
            fv_plot["innings_label"] = fv_plot["innings"].map({1: "1st Innings", 2: "2nd Innings (Chase)"})
            fv_plot["pressure_pct"] = fv_plot["pressure_share"] * 100
            fig_ph = px.bar(
                fv_plot,
                x="phase",
                y="pressure_pct",
                color="innings_label",
                barmode="group",
                category_orders={"phase": ["Powerplay", "Middle", "Death"]},
                color_discrete_sequence=[SEMANTIC["structure"], SEMANTIC["pressure"]],
                text=fv_plot["pressure_pct"].round(1),
                labels={"innings_label": "Innings"},
            )
            fig_ph.update_traces(textposition="outside", cliponaxis=False)
            apply_piq_theme(fig_ph, "5. Pressure Share by Phase — 1st Innings vs 2nd Innings (%)", height=360)
            fig_ph.update_xaxes(title_text="Innings Phase")
            fig_ph.update_yaxes(title_text="Elevated + High Share (%)", range=[0, 58])
            st.plotly_chart(fig_ph, use_container_width=True)

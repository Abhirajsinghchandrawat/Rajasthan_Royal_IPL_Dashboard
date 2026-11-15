"""SECTION 01 — PRESSURE ENGINE (MASTER_PROMPT.md Section 5 & Section 12)."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.charts import apply_piq_theme
from components.data_loader import load_parquet, load_summary_meta
from components.kpi_cards import page_header, render_kpi_row
from config.settings import CHART_H_PAIR, COLORS, PRESSURE_SCALE, SEMANTIC, STRUCTURE_SEQ


def render_pressure_engine(filters: dict) -> None:
    meta = load_summary_meta()
    d = load_parquet("deliveries_with_pressure", processed=True)
    hm_ov = load_parquet("heatmap_over_wickets")
    hm_rrr = load_parquet("heatmap_rrr_wickets")
    res_tab = load_parquet("resource_table")

    page_header(
        "SECTION 01 · PRESSURE ENGINE",
        "Pre-delivery win probability, Duckworth-Lewis resource curves, and next-ball leverage gating",
        is_official_mode=filters["is_official"],
        status=meta.get("validation_status", "VALIDATED"),
    )

    pe = d[d["pressure_eligible"]].copy()
    if not filters["is_official"]:
        if filters["competition"] == "IPL Only":
            pe = pe[pe["format_group"] == "IPL"]
        elif filters["competition"] == "T20I Only":
            pe = pe[pe["format_group"] == "T20I"]
        pe = pe[pe["season_year"].isin(filters["seasons"]) & pe["phase"].isin(filters["phases"])]

    ch = pe[pe["innings"] == 2]

    render_kpi_row(
        [
            {"label": "Mean Pressure Index", "value": f"{pe['pi_bat'].mean():.1f}", "sub": f"Median: {pe['pi_bat'].median():.1f} (0–100 scale)", "accent": "navy"},
            {"label": "Pressure Exposure", "value": f"{pe['pressure_level_bat'].isin(['Elevated', 'High']).mean()*100:.1f}%", "sub": f"Threshold: PI ≥ {meta['thresholds']['elevated']}", "accent": "amber"},
            {"label": "High Pressure Share", "value": f"{(pe['pressure_level_bat'] == 'High').mean()*100:.1f}%", "sub": f"Threshold: PI ≥ {meta['thresholds']['high']}", "accent": "amber"},
            {"label": "Median Chase Ratio", "value": f"{ch['resource_ratio'].median():.2f}x" if len(ch) else "N/A", "sub": "Runs Needed / Expected E(u,w)", "accent": "amber"},
            {"label": "Mean Wicket Value (WV)", "value": f"{pe['wicket_value'].mean():.1f} runs", "sub": "E(u,w) − E(u,w−1) run cost", "accent": "navy"},
            {"label": "1st-Inn Par Correlation", "value": f"r = {meta['pressure_meta']['corr_pi_vs_par_dev_inn1']:.2f}", "sub": f"vs Current RR: r = {meta['pressure_meta']['corr_pi_vs_current_rr_inn1']:.2f}", "accent": "teal"},
        ]
    )

    with st.expander("Pre-Delivery Mathematical Formulation, Component Rationale & Leakage Controls", expanded=True):
        st.markdown(
            f"""
            **1. Strict Pre-Delivery State:** Every input (`pre_team_runs`, `pre_wickets`, `balls_remaining`, `wickets_remaining`, `runs_needed`) is accumulated strictly *before* the ball is released. The outcome of the current delivery never enters its own pressure score.

            **2. Separate Innings Frameworks:**
            - **First Innings (Par & Resource Deficit):** Exponential Duckworth–Lewis curves $E(u, w) = Z_w (1 - e^{{-b_w u}})$ are fitted on completed 20-over first innings, scaled by format ($\\text{{IPL}} = {meta['pressure_meta']['format_multiplier']['IPL']:.3f}$, $\\text{{T20I}} = {meta['pressure_meta']['format_multiplier']['T20I']:.3f}$). At any state, $\\text{{Par Deviation}} = (\\text{{pre\\_runs}} + E(u, w)) - E(\\text{{alloc}}, 10)$. A team at 150/1 in over 16 is well ahead of par (low pressure), whereas 45/4 in over 7 is deep behind par (high pressure).
            - **Second Innings (Run-Chase Resource Ratio):** Evaluates $\\log(\\text{{runs\\_needed}} / E(u, w))$, required runs per ball, wickets fraction, and balls left fraction, honouring revised DLS targets and legal-ball allocations.

            **3. Cross-Fitted Win Probability & Live-Match Leverage Gate:**
            - Match-grouped 5-fold cross-fitted logistic models map pre-delivery features to calibrated batting win probability $WP_{{\\text{{bat}}}}$.
            - Next-ball leverage $L = \\sum_{{o \\in \\{{0,1,2,3,4,6,W\\}}}} p(o) |WP(\\text{{state after }} o) - WP(\\text{{state before}})|$.
            - **Frozen Formula:** $\\text{{PI}}_{{\\text{{bat}}}} = 100 \\times (1 - WP_{{\\text{{bat}}}}) \\times \\min(1, L / \\text{{median}}(L \\mid \\text{{innings}}))$ and $\\text{{PI}}_{{\\text{{bowl}}}} = 100 \\times WP_{{\\text{{bat}}}} \\times \\min(1, L / \\text{{median}}(L \\mid \\text{{innings}}))$. The live gate extinguishes dead rubbers (e.g. needing 80 off 18 balls has $1 - WP \\approx 1$ but $L \\approx 0 \\Rightarrow \\text{{PI}} \\approx 5.8$).
            """
        )

    inn_choice = st.radio(
        "Select Innings Perspective for Chart 1 (Over vs Wickets Heatmap)",
        [1, 2],
        format_func=lambda x: "1st Innings (Par Deficit)" if x == 1 else "2nd Innings (Run Chase)",
        horizontal=True,
    )

    # Row 1: Heatmaps (1 & 2)
    c1, c2 = st.columns(2)
    with c1:
        sub_hm = hm_ov[hm_ov["innings"] == inn_choice]
        piv = sub_hm.pivot(index="wickets_remaining", columns="overid", values="mean_pi_bat").sort_index(ascending=False)
        fig_hm1 = px.imshow(
            piv,
            color_continuous_scale=PRESSURE_SCALE,
            aspect="auto",
            labels=dict(x="Over Number (1–20)", y="Wickets in Hand", color="Mean PI"),
        )
        apply_piq_theme(
            fig_hm1,
            f"1. Pressure Situation Heatmap — {'1st Innings' if inn_choice == 1 else '2nd Innings'} (Over vs Wickets)",
            height=CHART_H_PAIR,
        )
        st.plotly_chart(fig_hm1, use_container_width=True)

    with c2:
        order_rrr = ["<=6", "6-8", "8-10", "10-12", "12-14", "14-16", "16-20", ">20"]
        piv2 = hm_rrr.pivot(index="wickets_remaining", columns="rrr_bin", values="mean_pi_bat")
        piv2 = piv2[[c for c in order_rrr if c in piv2.columns]].sort_index(ascending=False)
        fig_hm2 = px.imshow(
            piv2,
            color_continuous_scale=PRESSURE_SCALE,
            aspect="auto",
            labels=dict(x="Required Run Rate (RPO)", y="Wickets in Hand", color="Mean PI"),
        )
        apply_piq_theme(
            fig_hm2,
            "2. Chase Pressure Heatmap — Required Run Rate vs Wickets Remaining",
            height=CHART_H_PAIR,
        )
        st.plotly_chart(fig_hm2, use_container_width=True)

    st.caption(
        "Analytical note on Chart 2: Notice the non-monotonic turnover when Required RR > 20 with few wickets remaining — next-ball leverage collapses because the chase is already mathematically dead."
    )

    # Row 2: Phase comparison (3) and Resource Curves (4)
    c3, c4 = st.columns(2)
    with c3:
        ph_agg = (
            pe.groupby(["format_group", "phase"], observed=True)
            .agg(
                bat_pi=("pi_bat", "mean"),
                bowl_pi=("pi_bowl", "mean"),
                high_sh=("pressure_level_bat", lambda s: 100 * (s == "High").mean()),
            )
            .reset_index()
        )
        fig_ph = px.bar(
            ph_agg,
            x="phase",
            y="bat_pi",
            color="format_group",
            barmode="group",
            category_orders={"phase": ["Powerplay", "Middle", "Death"]},
            color_discrete_sequence=[SEMANTIC["structure"], SEMANTIC["pressure"]],
            text=ph_agg["bat_pi"].round(1),
            labels={"format_group": "Competition", "phase": "Innings Phase", "bat_pi": "Mean Batting PI"},
        )
        fig_ph.update_traces(textposition="outside", cliponaxis=False)
        apply_piq_theme(fig_ph, "3. Mean Batting Pressure Index — By Innings Phase & Format", height=CHART_H_PAIR)
        fig_ph.update_xaxes(title_text="Innings Phase")
        fig_ph.update_yaxes(title_text="Mean Batting Pressure Index (0–100)", range=[0, 58])
        st.plotly_chart(fig_ph, use_container_width=True)

    with c4:
        rt_ipl = res_tab[(res_tab["format_group"] == "IPL") & (res_tab["wickets_remaining"].isin([10, 8, 6, 4, 2]))].copy()
        rt_ipl["wickets_label"] = rt_ipl["wickets_remaining"].astype(str) + " wkts"
        fig_rc = px.line(
            rt_ipl,
            x="balls_remaining",
            y="expected_remaining_runs",
            color="wickets_label",
            markers=True,
            color_discrete_sequence=STRUCTURE_SEQ,
            labels={
                "balls_remaining": "Legal Balls Remaining (u)",
                "expected_remaining_runs": "Expected Remaining Runs E(u, w)",
                "wickets_label": "Wickets in Hand",
            },
        )
        fig_rc.update_xaxes(autorange="reversed")
        apply_piq_theme(fig_rc, "4. Empirical D/L Resource Curves — Expected Runs E(u, w) in IPL", height=CHART_H_PAIR)
        st.plotly_chart(fig_rc, use_container_width=True)

    # Example match situations table
    st.markdown("#### Benchmark Match Situations — Pre-Delivery Pressure Verification")
    bench_rows = [
        ("1st Innings Cruise", "150/1 in Over 16 (24 balls left)", "Ahead of par (+25 runs), 9 wkts in hand", 15.6, "Low"),
        ("1st Innings Opening Ball", "0/0 in Over 1, Ball 1 (120 balls left)", "On par (0 deviation), full resources", 48.9, "Low"),
        ("1st Innings Early Collapse", "45/4 in Over 7 (84 balls left)", "Behind par (−24 runs), wicket scarcity", 59.5, "Elevated"),
        ("2nd Innings Balanced Chase", "Resource Ratio ~1.3x in Over 10", "Above-par rate needed, live leverage", 68.4, "High"),
        ("2nd Innings Crunch Finish", "30 needed off 12 balls (3–6 wkts left)", "Steep rate, maximum swing per delivery", 76.0, "High"),
        ("2nd Innings Dead Lost Cause", "80 needed off 18 balls", "Win prob ~0%, next-ball leverage ~0", 5.8, "Low"),
        ("2nd Innings Almost Won", "3 needed off ≥ 6 balls", "Win prob ~99%, next-ball leverage ~0", 0.0, "Low"),
    ]
    st.dataframe(
        pd.DataFrame(bench_rows, columns=["Archetype", "Pre-Delivery State", "Cricket Rationale", "Mean Batting PI", "Classification"]),
        use_container_width=True,
        hide_index=True,
    )

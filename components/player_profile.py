"""Player profile drill-down and two-player head-to-head comparison components."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components.charts import apply_piq_theme, sign_colors
from components.kpi_cards import render_kpi_row, signed_accent
from config.settings import COLORS, SEMANTIC


def render_batter_drilldown(
    rank_df: pd.DataFrame,
    mt_df: pd.DataFrame,
    seasons_df: pd.DataFrame,
    key_prefix: str = "bat_dd",
) -> None:
    eligible_first = rank_df.sort_values(["eligible", "rpr"], ascending=[False, False]).copy()
    eligible_first["label"] = (
        eligible_first["player_name"].fillna("Unknown")
        + " (ID: "
        + eligible_first["player_id"].astype(str)
        + " · "
        + eligible_first["eligibility_status"]
        + ")"
    )
    choice = st.selectbox("Select Batter for Profile Drill-Down", eligible_first["label"].tolist(), key=f"{key_prefix}_sel")
    row = eligible_first[eligible_first["label"] == choice].iloc[0]
    pid = int(row["player_id"])

    render_kpi_row(
        [
            {
                "label": "Player & ID",
                "value": f"{row['player_name']}",
                "sub": f"ID: {pid} · {row.get('teams', 'N/A')}",
                "accent": "featured",
            },
            {
                "label": "Reliable Rating (RPR)",
                "value": f"{row['rpr']:+.2f} / 100b" if pd.notna(row["rpr"]) else "N/A",
                "sub": f"Rank: #{int(row['rank'])} (90% Lower Bound)" if pd.notna(row["rank"]) else row["eligibility_status"],
                "accent": signed_accent(row["rpr"]) if pd.notna(row["rpr"]) else "slate",
            },
            {
                "label": "Shrunk Mean (APR)",
                "value": f"{row['rating_mean']:+.2f} / 100b" if pd.notna(row["rating_mean"]) else "N/A",
                "sub": f"Raw: {row.get('pr_rate', 0):+.2f} · 90% CI: [{row['ci_lo']:+.1f}, {row['ci_hi']:+.1f}]" if pd.notna(row["ci_lo"]) else "Insufficient sample",
                "accent": signed_accent(row["rating_mean"]) if pd.notna(row["rating_mean"]) else "slate",
            },
            {
                "label": "Pressure Response (PRD)",
                "value": f"{row['prd']:+.2f} / 100b" if pd.notna(row["prd"]) else "N/A",
                "sub": f"APR ({row['rating_mean']:+.1f}) vs Shrunk Normal ({row.get('nr_post_mean', 0):+.1f})" if pd.notna(row["prd"]) else "vs Own Normal Baseline",
                "accent": signed_accent(row["prd"]) if pd.notna(row["prd"]) else "slate",
            },
            {
                "label": "Pressure Sample",
                "value": f"{int(row.get('p_balls', 0) or 0)} balls",
                "sub": f"{int(row.get('p_matches', 0) or 0)} pressure matches (B={row.get('pr_shrink_weight', 0):.2f})",
                "accent": "amber",
            },
            {
                "label": "Pressure Strike Rate",
                "value": f"{row.get('p_sr', 0):.1f}",
                "sub": f"Exp SR: {row.get('p_exp_sr', 0):.1f} · Dot%: {row.get('p_dot_pct', 0):.1f}%",
                "accent": signed_accent(row.get("p_sr", 0) - row.get("p_exp_sr", 0)),
            },
        ]
    )

    c1, c2 = st.columns(2)
    pm = mt_df[(mt_df["player_id"] == pid) & (mt_df["context"] == "pressure")].sort_values("match_date")
    with c1:
        if len(pm):
            fig = go.Figure()
            fig.add_trace(
                go.Bar(
                    x=pm["match_date"].astype(str) + " (#" + pm["match_id"].astype(str) + ")",
                    y=pm["value"],
                    marker_color=sign_colors(pm["value"]),
                    hovertemplate="Match: %{x}<br>CABV: %{y:+.2f} runs<br>Runs: %{customdata[0]} (%{customdata[1]}b)<extra></extra>",
                    customdata=pm[["runs", "balls"]].to_numpy(),
                )
            )
            fig.add_hline(y=0, line_dash="dash", line_color=SEMANTIC["neutral"])
            apply_piq_theme(fig, f"{row['player_name']} — Match-by-Match Pressure CABV (Runs)", height=340)
            fig.update_xaxes(showticklabels=False, title_text=f"{len(pm)} Pressure Matches (Chronological — Teal ≥ 0, Coral < 0)")
            fig.update_yaxes(title_text="Net CABV (Runs)")
            st.plotly_chart(fig, use_container_width=True)
    with c2:
        ps = seasons_df[seasons_df["player_id"] == pid].sort_values("season")
        if len(ps):
            fig2 = go.Figure()
            fig2.add_trace(
                go.Scatter(
                    x=ps["season"].astype(str),
                    y=ps["rate"],
                    mode="lines+markers+text",
                    text=[f"{v:+.1f}" for v in ps["rate"]],
                    textposition="top center",
                    marker=dict(
                        size=10,
                        color=sign_colors(ps["rate"]),
                        symbol=["diamond" if v >= 0 else "circle" for v in ps["rate"]],
                        line=dict(width=1.5, color="#FFFFFF"),
                    ),
                    line=dict(width=2.4, color=SEMANTIC["structure"]),
                    hovertemplate="Season %{x}<br>Raw CABV/100b: %{y:+.2f}<br>Balls: %{customdata}<extra></extra>",
                    customdata=ps["balls"],
                )
            )
            fig2.add_hline(y=0, line_dash="dash", line_color=SEMANTIC["neutral"])
            apply_piq_theme(fig2, f"{row['player_name']} — Season Trajectory (Observed CABV / 100b)", height=340)
            fig2.update_xaxes(title_text="Season Year")
            fig2.update_yaxes(title_text="CABV / 100 Pressure Balls")
            st.plotly_chart(fig2, use_container_width=True)


def render_bowler_drilldown(
    rank_df: pd.DataFrame,
    mt_df: pd.DataFrame,
    seasons_df: pd.DataFrame,
    key_prefix: str = "bowl_dd",
) -> None:
    eligible_first = rank_df.sort_values(["eligible", "rpr"], ascending=[False, False]).copy()
    eligible_first["label"] = (
        eligible_first["player_name"].fillna("Unknown")
        + " (ID: "
        + eligible_first["player_id"].astype(str)
        + " · "
        + eligible_first["eligibility_status"]
        + ")"
    )
    choice = st.selectbox("Select Bowler for Profile Drill-Down", eligible_first["label"].tolist(), key=f"{key_prefix}_sel")
    row = eligible_first[eligible_first["label"] == choice].iloc[0]
    pid = int(row["player_id"])

    render_kpi_row(
        [
            {
                "label": "Player & ID",
                "value": f"{row['player_name']}",
                "sub": f"ID: {pid} · {row.get('teams', 'N/A')}",
                "accent": "featured",
            },
            {
                "label": "Reliable Rating (RPR)",
                "value": f"{row['rpr']:+.2f} / 24b" if pd.notna(row["rpr"]) else "N/A",
                "sub": f"Rank: #{int(row['rank'])} (90% Lower Bound)" if pd.notna(row["rank"]) else row["eligibility_status"],
                "accent": signed_accent(row["rpr"]) if pd.notna(row["rpr"]) else "slate",
            },
            {
                "label": "Shrunk Mean (APR)",
                "value": f"{row['rating_mean']:+.2f} / 24b" if pd.notna(row["rating_mean"]) else "N/A",
                "sub": f"Raw: {row.get('pr_rate', 0):+.2f} · 90% CI: [{row['ci_lo']:+.1f}, {row['ci_hi']:+.1f}]" if pd.notna(row["ci_lo"]) else "Insufficient sample",
                "accent": signed_accent(row["rating_mean"]) if pd.notna(row["rating_mean"]) else "slate",
            },
            {
                "label": "Pressure Response (PRD)",
                "value": f"{row['prd']:+.2f} / 24b" if pd.notna(row["prd"]) else "N/A",
                "sub": f"APR ({row['rating_mean']:+.2f}) vs Shrunk Normal ({row.get('nr_post_mean', 0):+.2f})" if pd.notna(row["prd"]) else "vs Own Normal Baseline",
                "accent": signed_accent(row["prd"]) if pd.notna(row["prd"]) else "slate",
            },
            {
                "label": "Pressure Sample",
                "value": f"{int(row.get('p_legal', 0) or 0)} legal b",
                "sub": f"{int(row.get('p_balls', 0) or 0)} total deliv · {int(row.get('p_matches', 0) or 0)}m (B={row.get('pr_shrink_weight', 0):.2f})",
                "accent": "amber",
            },
            {
                "label": "Pressure Economy & Wkts",
                "value": f"{row.get('p_economy', 0):.2f} RPO",
                "sub": f"Exp: {row.get('p_exp_economy', 0):.2f} · Wkts: {int(row.get('p_wickets', 0) or 0)}",
                "accent": signed_accent(row.get("p_exp_economy", 0) - row.get("p_economy", 0)),
            },
        ]
    )

    c1, c2 = st.columns(2)
    pm = mt_df[(mt_df["player_id"] == pid) & (mt_df["context"] == "pressure")].sort_values("match_date")
    with c1:
        if len(pm):
            fig = go.Figure()
            fig.add_trace(
                go.Bar(
                    x=pm["match_date"].astype(str) + " (#" + pm["match_id"].astype(str) + ")",
                    y=pm["value"],
                    marker_color=sign_colors(pm["value"]),
                    hovertemplate="Match: %{x}<br>RP Value: %{y:+.2f} runs<br>Conceded: %{customdata[0]} (%{customdata[1]} legal b)<extra></extra>",
                    customdata=pm[["conceded", "legal"]].to_numpy(),
                )
            )
            fig.add_hline(y=0, line_dash="dash", line_color=SEMANTIC["neutral"])
            apply_piq_theme(fig, f"{row['player_name']} — Match-by-Match Pressure Value (Runs)", height=340)
            fig.update_xaxes(showticklabels=False, title_text=f"{len(pm)} Pressure Matches (Chronological — Teal ≥ 0, Coral < 0)")
            fig.update_yaxes(title_text="Net Runs Prevented + Wkt Value")
            st.plotly_chart(fig, use_container_width=True)
    with c2:
        ps = seasons_df[seasons_df["player_id"] == pid].sort_values("season")
        if len(ps):
            fig2 = go.Figure()
            fig2.add_trace(
                go.Scatter(
                    x=ps["season"].astype(str),
                    y=ps["rate"],
                    mode="lines+markers+text",
                    text=[f"{v:+.1f}" for v in ps["rate"]],
                    textposition="top center",
                    marker=dict(
                        size=10,
                        color=sign_colors(ps["rate"]),
                        symbol=["diamond" if v >= 0 else "circle" for v in ps["rate"]],
                        line=dict(width=1.5, color="#FFFFFF"),
                    ),
                    line=dict(width=2.4, color=SEMANTIC["structure"]),
                    hovertemplate="Season %{x}<br>Raw RP/24b: %{y:+.2f}<br>Deliveries: %{customdata}<extra></extra>",
                    customdata=ps["balls"],
                )
            )
            fig2.add_hline(y=0, line_dash="dash", line_color=SEMANTIC["neutral"])
            apply_piq_theme(fig2, f"{row['player_name']} — Season Trajectory (Observed RP / 24 Deliveries)", height=340)
            fig2.update_xaxes(title_text="Season Year")
            fig2.update_yaxes(title_text="Runs Prevented / 24 Deliveries")
            st.plotly_chart(fig2, use_container_width=True)


def render_two_player_comparison(rank_df: pd.DataFrame, kind: str = "batting", key_prefix: str = "cmp") -> None:
    el = rank_df[rank_df["eligible"]].sort_values("rank").copy()
    el["label"] = "#" + el["rank"].astype(int).astype(str) + " " + el["player_name"] + " (ID: " + el["player_id"].astype(str) + ")"
    labels = el["label"].tolist()
    if len(labels) < 2:
        st.info("Need at least two eligible players for head-to-head comparison.")
        return

    c1, c2 = st.columns(2)
    with c1:
        p1_lbl = st.selectbox("Player A", labels, index=0, key=f"{key_prefix}_p1")
    with c2:
        p2_lbl = st.selectbox("Player B", labels, index=min(1, len(labels) - 1), key=f"{key_prefix}_p2")

    r1 = el[el["label"] == p1_lbl].iloc[0]
    r2 = el[el["label"] == p2_lbl].iloc[0]

    if kind == "batting":
        metrics = [
            ("Official Rank (by RPR)", f"#{int(r1['rank'])}", f"#{int(r2['rank'])}"),
            ("Reliable Pressure Rating (RPR, CABV / 100b)", f"{r1['rpr']:+.2f}", f"{r2['rpr']:+.2f}"),
            ("Shrunk Pressure Mean (APR, CABV / 100b)", f"{r1['rating_mean']:+.2f}", f"{r2['rating_mean']:+.2f}"),
            ("Raw Observed Pressure Rate (CABV / 100b)", f"{r1['pr_rate']:+.2f}", f"{r2['pr_rate']:+.2f}"),
            ("90% Empirical-Bayes Credible Interval", f"[{r1['ci_lo']:+.2f}, {r1['ci_hi']:+.2f}]", f"[{r2['ci_lo']:+.2f}, {r2['ci_hi']:+.2f}]"),
            ("Shrunk Normal Baseline (CABV / 100b)", f"{r1['nr_post_mean']:+.2f}", f"{r2['nr_post_mean']:+.2f}"),
            ("Raw Observed Normal Rate (CABV / 100b)", f"{r1['nr_rate']:+.2f}", f"{r2['nr_rate']:+.2f}"),
            ("Pressure Response Delta (PRD = APR − Normal)", f"{r1['prd']:+.2f}", f"{r2['prd']:+.2f}"),
            ("Pressure Balls Faced (Normal Balls)", f"{int(r1['p_balls'])} ({int(r1.get('n_balls', 0) or 0)})", f"{int(r2['p_balls'])} ({int(r2.get('n_balls', 0) or 0)})"),
            ("Unique Pressure Matches", f"{int(r1['p_matches'])}", f"{int(r2['p_matches'])}"),
            ("Pressure Strike Rate (Expected SR)", f"{r1['p_sr']:.1f} ({r1['p_exp_sr']:.1f})", f"{r2['p_sr']:.1f} ({r2['p_exp_sr']:.1f})"),
            ("Pressure Dot Ball %", f"{r1['p_dot_pct']:.1f}%", f"{r2['p_dot_pct']:.1f}%"),
            ("Pressure Boundary %", f"{r1['p_boundary_pct']:.1f}%", f"{r2['p_boundary_pct']:.1f}%"),
            ("Pressure Dismissal Rate (/100b)", f"{r1['p_dismissal_rate']:.2f}", f"{r2['p_dismissal_rate']:.2f}"),
            ("Match Success Rate (% > 0)", f"{r1['success_rate']*100:.1f}%", f"{r2['success_rate']*100:.1f}%"),
        ]
    else:
        metrics = [
            ("Official Rank (by RPR)", f"#{int(r1['rank'])}", f"#{int(r2['rank'])}"),
            ("Reliable Pressure Rating (RPR, RP / 24 deliv.)", f"{r1['rpr']:+.2f}", f"{r2['rpr']:+.2f}"),
            ("Shrunk Pressure Mean (APR, RP / 24 deliv.)", f"{r1['rating_mean']:+.2f}", f"{r2['rating_mean']:+.2f}"),
            ("Raw Observed Pressure Rate (RP / 24 deliv.)", f"{r1['pr_rate']:+.2f}", f"{r2['pr_rate']:+.2f}"),
            ("90% Empirical-Bayes Credible Interval", f"[{r1['ci_lo']:+.2f}, {r1['ci_hi']:+.2f}]", f"[{r2['ci_lo']:+.2f}, {r2['ci_hi']:+.2f}]"),
            ("Shrunk Normal Baseline (RP / 24 deliv.)", f"{r1['nr_post_mean']:+.2f}", f"{r2['nr_post_mean']:+.2f}"),
            ("Raw Observed Normal Rate (RP / 24 deliv.)", f"{r1['nr_rate']:+.2f}", f"{r2['nr_rate']:+.2f}"),
            ("Pressure Response Delta (PRD = APR − Normal)", f"{r1['prd']:+.2f}", f"{r2['prd']:+.2f}"),
            ("Pressure Legal Balls (Total Deliveries)", f"{int(r1['p_legal'])} ({int(r1['p_balls'])})", f"{int(r2['p_legal'])} ({int(r2['p_balls'])})"),
            ("Unique Pressure Matches", f"{int(r1['p_matches'])}", f"{int(r2['p_matches'])}"),
            ("Pressure Economy (Expected Economy)", f"{r1['p_economy']:.2f} ({r1['p_exp_economy']:.2f})", f"{r2['p_economy']:.2f} ({r2['p_exp_economy']:.2f})"),
            ("Pressure Wicket Rate (/100 legal b)", f"{r1['p_wicket_rate']:.2f}", f"{r2['p_wicket_rate']:.2f}"),
            ("Pressure Dot Ball %", f"{r1['p_dot_pct']:.1f}%", f"{r2['p_dot_pct']:.1f}%"),
            ("Boundary Conceded %", f"{r1['p_boundary_pct']:.1f}%", f"{r2['p_boundary_pct']:.1f}%"),
            ("Match Success Rate (% > 0)", f"{r1['success_rate']*100:.1f}%", f"{r2['success_rate']*100:.1f}%"),
        ]

    cmp_df = pd.DataFrame(metrics, columns=["Metric", r1["player_name"], r2["player_name"]])
    st.dataframe(cmp_df, use_container_width=True, hide_index=True)

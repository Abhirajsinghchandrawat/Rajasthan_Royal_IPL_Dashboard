"""SECTION 05 — PLAYER RANKINGS (MASTER_PROMPT.md Section 10 & Section 12)."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.data_loader import load_parquet, load_summary_meta
from components.kpi_cards import callout, page_header
from components.player_profile import (
    render_batter_drilldown,
    render_bowler_drilldown,
    render_two_player_comparison,
)


def _format_leaderboard(df: pd.DataFrame, kind: str) -> pd.DataFrame:
    d = df.copy()
    d["CI_90"] = d.apply(
        lambda r: f"[{r['ci_lo']:+.2f}, {r['ci_hi']:+.2f}]" if pd.notna(r["ci_lo"]) else "N/A",
        axis=1,
    )
    if kind == "batting":
        cols = {
            "rank": "Rank",
            "player_id": "Player ID",
            "player_name": "Player",
            "teams": "Teams",
            "formats": "Format Scope",
            "rpr": "RPR (/100b)",
            "rating_mean": "Shrunk APR (/100b)",
            "pr_rate": "Raw Pressure Rate (/100b)",
            "nr_post_mean": "Shrunk Normal (/100b)",
            "prd": "PRD (APR − Normal)",
            "p_balls": "Pressure Balls",
            "p_matches": "Unique Matches",
            "p_sr": "Pressure SR",
            "p_exp_sr": "Expected SR",
            "success_rate": "Match Success %",
            "CI_90": "90% CI",
            "eligibility_status": "Eligibility Status",
        }
    else:
        cols = {
            "rank": "Rank",
            "player_id": "Player ID",
            "player_name": "Player",
            "teams": "Teams",
            "formats": "Format Scope",
            "rpr": "RPR (/24b)",
            "rating_mean": "Shrunk APR (/24b)",
            "pr_rate": "Raw Pressure Rate (/24b)",
            "nr_post_mean": "Shrunk Normal (/24b)",
            "prd": "PRD (APR − Normal)",
            "p_legal": "Pressure Legal Balls",
            "p_matches": "Unique Matches",
            "p_economy": "Pressure Econ",
            "p_exp_economy": "Expected Econ",
            "p_wickets": "Pressure Wkts",
            "success_rate": "Match Success %",
            "CI_90": "90% CI",
            "eligibility_status": "Eligibility Status",
        }
    out = d[[c for c in cols if c in d.columns]].rename(columns=cols).copy()
    if "Match Success %" in out.columns:
        out["Match Success %"] = (out["Match Success %"] * 100).round(1)
    for num_c in [
        "RPR (/100b)",
        "Shrunk APR (/100b)",
        "Raw Pressure Rate (/100b)",
        "Shrunk Normal (/100b)",
        "RPR (/24b)",
        "Shrunk APR (/24b)",
        "Raw Pressure Rate (/24b)",
        "Shrunk Normal (/24b)",
        "PRD (APR − Normal)",
        "Pressure SR",
        "Expected SR",
        "Pressure Econ",
        "Expected Econ",
    ]:
        if num_c in out.columns:
            out[num_c] = out[num_c].round(2)
    return out


def render_rankings(filters: dict) -> None:
    meta = load_summary_meta()
    bat_off = load_parquet("batting_rankings")
    bowl_off = load_parquet("bowling_rankings")
    bat_ipl = load_parquet("batting_rankings_ipl")
    bowl_ipl = load_parquet("bowling_rankings_ipl")
    bat_t20i = load_parquet("batting_rankings_t20i")
    bowl_t20i = load_parquet("bowling_rankings_t20i")
    bat_mt = load_parquet("batting_match_table")
    bowl_mt = load_parquet("bowling_match_table")
    bat_seasons = load_parquet("batting_seasons")
    bowl_seasons = load_parquet("bowling_seasons")

    page_header(
        "SECTION 05 · PLAYER RANKINGS",
        "Official Top-10 Batters and Top-10 Bowlers under pressure, plus exploratory format & cohort search",
        is_official_mode=filters["is_official"],
        status=meta.get("validation_status", "VALIDATED"),
    )

    callout(
        "<b>Official Ranking Estimand & Metric Guide:</b> "
        "Players are ordered strictly by <b>Reliable Pressure Rating (RPR) = APR − 1.2816 × post_sd</b>, the one-sided 90% Empirical-Bayes lower bound on context-adjusted contribution "
        "(<b>CABV / 100 balls</b> for batters; <b>Runs Prevented / 24 deliveries</b> for bowlers). "
        "<b>Shrunk APR</b> is the Empirical-Bayes posterior mean, <b>Raw Pressure Rate</b> is the unshrunk observed rate, and <b>PRD = Shrunk APR − Shrunk Normal</b> measures elevation vs the player's own normal baseline. "
        "Official rankings always use the complete 853-match IPL + T20I regulation scope."
    )

    # Official Top 10 Side-by-Side
    st.markdown("### Official Top 10 Leaderboards (Combined IPL + T20I, 2022–2026)")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### A. Official Top 10 Batters Under Pressure")
        b10 = bat_off[bat_off["rank"] <= 10].sort_values("rank")
        b10_disp = _format_leaderboard(b10, "batting")
        st.dataframe(b10_disp, use_container_width=True, hide_index=True)
        st.download_button(
            "Download Official Top 10 Batters (CSV)",
            b10.to_csv(index=False).encode("utf-8"),
            file_name="official_top10_batters.csv",
            mime="text/csv",
        )

    with c2:
        st.markdown("#### B. Official Top 10 Bowlers Under Pressure")
        w10 = bowl_off[bowl_off["rank"] <= 10].sort_values("rank")
        w10_disp = _format_leaderboard(w10, "bowling")
        st.dataframe(w10_disp, use_container_width=True, hide_index=True)
        st.download_button(
            "Download Official Top 10 Bowlers (CSV)",
            w10.to_csv(index=False).encode("utf-8"),
            file_name="official_top10_bowlers.csv",
            mime="text/csv",
        )

    st.markdown("---")
    st.markdown("### Interactive Leaderboard Explorer (Search, Sort, Format Slice & Export)")

    sort_labels = {
        "rpr": "Official Reliable Pressure Rating (RPR)",
        "rating_mean": "Shrunk Posterior Mean (APR)",
        "pr_rate": "Raw Observed Pressure Rate",
        "prd": "Pressure Response Delta (PRD)",
        "p_matches": "Unique Pressure Matches",
        "success_rate": "Match Success Rate (%)",
    }

    ec1, ec2, ec3, ec4 = st.columns([1.3, 1.3, 1.3, 1.3])
    with ec1:
        scope_sel = st.selectbox(
            "Ranking Dataset Scope",
            ["Official Combined (IPL + T20I)", "Exploratory: IPL Only", "Exploratory: T20I Only"],
        )
    with ec2:
        elig_filter = st.selectbox("Eligibility Filter", ["Eligible Only", "All Players (incl. Insufficient Sample)"])
    with ec3:
        sort_by = st.selectbox("Sort Table By", list(sort_labels.keys()), format_func=lambda k: sort_labels[k])
    with ec4:
        search_q = st.text_input("Search Player or Team Name", "")

    if scope_sel == "Exploratory: IPL Only":
        b_src, w_src = bat_ipl, bowl_ipl
        callout("<b>Exploratory Mode Active (IPL Only):</b> Displaying format-isolated IPL rankings. Official combined rankings remain above.", tone="amber")
    elif scope_sel == "Exploratory: T20I Only":
        b_src, w_src = bat_t20i, bowl_t20i
        callout("<b>Exploratory Mode Active (T20I Only):</b> Displaying format-isolated T20I rankings. Official combined rankings remain above.", tone="amber")
    else:
        b_src, w_src = bat_off, bowl_off

    if sort_by != "rpr":
        st.caption(f"Note: Table is currently sorted by **{sort_labels[sort_by]}**. The `Rank` column always displays each player's official RPR rank.")

    tab_b, tab_w, tab_cmp = st.tabs(["Batters Explorer & Drill-Down", "Bowlers Explorer & Drill-Down", "Two-Player Head-to-Head"])
    with tab_b:
        bf = b_src.copy()
        if elig_filter == "Eligible Only":
            bf = bf[bf["eligible"]]
        if search_q.strip():
            q = search_q.strip().lower()
            bf = bf[
                bf["player_name"].fillna("").str.lower().str.contains(q)
                | bf["teams"].fillna("").str.lower().str.contains(q)
            ]
        bf = bf.sort_values(sort_by, ascending=False)
        st.dataframe(_format_leaderboard(bf, "batting"), use_container_width=True, hide_index=True)
        st.download_button(
            "Export Filtered Batting Table (CSV)",
            bf.to_csv(index=False).encode("utf-8"),
            file_name="filtered_batting_rankings.csv",
            mime="text/csv",
            key="dl_bat_filt",
        )
        st.markdown("#### Batter Profile Drill-Down")
        render_batter_drilldown(bat_off, bat_mt, bat_seasons, key_prefix="sec05_bat")

    with tab_w:
        wf = w_src.copy()
        if elig_filter == "Eligible Only":
            wf = wf[wf["eligible"]]
        if search_q.strip():
            q = search_q.strip().lower()
            wf = wf[
                wf["player_name"].fillna("").str.lower().str.contains(q)
                | wf["teams"].fillna("").str.lower().str.contains(q)
            ]
        wf = wf.sort_values(sort_by, ascending=False)
        st.dataframe(_format_leaderboard(wf, "bowling"), use_container_width=True, hide_index=True)
        st.download_button(
            "Export Filtered Bowling Table (CSV)",
            wf.to_csv(index=False).encode("utf-8"),
            file_name="filtered_bowling_rankings.csv",
            mime="text/csv",
            key="dl_bowl_filt",
        )
        st.markdown("#### Bowler Profile Drill-Down")
        render_bowler_drilldown(bowl_off, bowl_mt, bowl_seasons, key_prefix="sec05_bowl")

    with tab_cmp:
        role_cmp = st.radio("Comparison Category", ["batting", "bowling"], horizontal=True, key="sec05_role_cmp")
        render_two_player_comparison(bat_off if role_cmp == "batting" else bowl_off, kind=role_cmp, key_prefix="sec05_cmp")

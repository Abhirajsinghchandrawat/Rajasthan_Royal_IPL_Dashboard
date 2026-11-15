"""SECTION 07 — METHODOLOGY & DATA AUDIT (MASTER_PROMPT.md Section 12 & Section 20)."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.data_loader import load_interim_csv, load_interim_json, load_summary_meta
from components.kpi_cards import page_header, render_kpi_row
from config.metric_definitions import KPI_CATALOG
from config.settings import METHODOLOGY_DIR, REPORTS


def render_methodology_audit(filters: dict) -> None:
    meta = load_summary_meta()
    page_header(
        "SECTION 07 · METHODOLOGY & DATA AUDIT",
        "Complete Phase 1 source audit, row-level extras reconciliation, mathematical specifications, and KPI catalog",
        is_official_mode=filters["is_official"],
        status=meta.get("validation_status", "VALIDATED"),
    )

    tab_audit, tab_meth, tab_kpi = st.tabs(
        ["TAB 1 · PHASE 1 DATA AUDIT & RECONCILIATION", "TAB 2 · MATHEMATICAL METHODOLOGY & ASSUMPTIONS", "TAB 3 · FULL KPI CATALOG & DOWNLOADS"]
    )

    with tab_audit:
        inv = load_interim_csv("dataset_inventory")
        excl = load_interim_csv("exclusion_flag_summary")
        ext_fam = load_interim_csv("extras_family_summary")
        rev_m = load_interim_csv("revised_matches_inspection")
        so_m = load_interim_csv("super_over_matches")
        ext_ver = meta.get("extras_verification", load_interim_json("extras_verification"))

        render_kpi_row(
            [
                {"label": "Raw CSV Tables", "value": "6 Files", "sub": "0 duplicate full rows across all tables", "accent": "navy"},
                {"label": "Total Matches (Raw)", "value": "883", "sub": "371 IPL + 482 T20I + 30 Other T20", "accent": "navy"},
                {"label": "Official Scope Matches", "value": "853", "sub": "837 with BBB (16 abandoned 0-ball matches)", "accent": "teal"},
                {"label": "'other' Extras Verified", "value": "264 Rows", "sub": "100% extras1=1 (Beamer/Full Toss no-balls)", "accent": "amber"},
                {"label": "extras_2_runs Verified", "value": "36 Rows", "sub": "35 no-ball byes/leg-byes + 1 untagged extra", "accent": "amber"},
                {"label": "Margin Hit Rate", "value": "97.6% (100% unrev.)", "sub": "Team total = runs + extras1 + extras2", "accent": "teal"},
            ]
        )

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 1. Source File Inventory & Schema Verification")
            if not inv.empty:
                st.dataframe(inv, use_container_width=True, hide_index=True)
            st.markdown("#### 2. Explicit Exclusion & Audit Flags (No Silent Deletes)")
            if not excl.empty:
                st.dataframe(excl, use_container_width=True, hide_index=True)

        with c2:
            st.markdown("#### 3. Extras Family Accounting & Row-Level Verification")
            if not ext_fam.empty:
                st.dataframe(ext_fam, use_container_width=True, hide_index=True)
            if ext_ver:
                st.json(ext_ver, expanded=False)

        c3, c4 = st.columns(2)
        with c3:
            st.markdown("#### 4. Revised Overs & DLS Targets (34 Matches, Legal-Ball Units)")
            if not rev_m.empty:
                st.dataframe(rev_m.head(20), use_container_width=True, hide_index=True)
        with c4:
            st.markdown("#### 5. Super Over Matches (6 Matches, Innings 3 & 4 Excluded)")
            if not so_m.empty:
                st.dataframe(so_m, use_container_width=True, hide_index=True)

        audit_md_path = METHODOLOGY_DIR / "PHASE1_DATA_AUDIT.md"
        if audit_md_path.exists():
            with st.expander("Read Full Verbatim Phase 1 Data Audit Report (`PHASE1_DATA_AUDIT.md`)"):
                st.markdown(audit_md_path.read_text(encoding="utf-8"))

    with tab_meth:
        st.markdown(
            r"""
            ### End-to-End Mathematical & Statistical Specification

            #### 1. Official Scope & Cricket Accounting (`src/quality/cricket_rules.py`, `cricket_accounting.py`)
            - **Competition Scope:** 371 IPL + 482 T20I matches (853 matches, 194,014 deliveries). The 30 Other-T20 matches (Emerging Teams Asia Cup 2024 & Rising Stars 2025) and 38 Super Over deliveries (`innings in {3, 4}`) are flagged and excluded from official regulation rankings.
            - **Runs & Extras Decomposition:**
              - `batter_runs = runs` on legal, Overstep, and `other` (height no-ball) deliveries; `0` on wides, byes, leg-byes, and penalty.
              - `team_runs = runs + extras1_runs + extras_2_runs` (reconciles 100% of unrevised 'won by N runs' margins).
              - `bowler_conceded = batter_runs + extras1_runs` on wides and no-balls (`Overstep` / `other`); byes, leg-byes, penalty, and `extras_2_runs` (bye/leg-bye off no-ball) are **not** debited to the bowler.
              - `is_legal = extras_family not in {'wide', 'no_ball'}`; `batter_faced = extras_family != 'wide'`.
            - **Dismissal Attribution:** Only `Caught`, `Bowled`, `LBW`, `Stump`, and `Hit Wicket` credit `bowler_wicket`. `RunOut` (600), `Retire Out` (6), and `Obstructing/Obstracting the field` (3) count as team wickets (`pre_wickets`) and batter dismissals (`striker_out` when `dismissed_player_id == striker_id`), never bowler wickets.
            - **Identity Hygiene:** Player aggregation uses `player_id`. Basil Hameed's two IDs (`8638` and `39444`) are kept unmerged per safeguard rules.

            #### 2. Pre-Delivery Pressure Engine (`src/pressure/`)
            - **Resource Curve $E(u, w)$:** Exponential Duckworth–Lewis curves $Z_w(1 - e^{-b_w u})$ fitted per wickets-in-hand $w \in \{1..10\}$ on unrevised completed first innings, scaled by format multiplier ($\text{IPL} = 1.035$, $\text{T20I} = 0.972$).
            - **First-Innings Pressure Model:** Uses pre-delivery Par Deviation $(\text{pre\_runs} + E(u,w) - E(\text{alloc}, 10))/20$, progress interaction, wickets fraction, and format in a 5-fold match-grouped cross-fitted logistic model for $WP_{\text{bat}}$.
            - **Run-Chase Pressure Model:** Uses $\log(\text{runs\_needed} / E(u,w))$, progress interaction, required runs per ball, wickets fraction, and balls left fraction in a separate 5-fold match-grouped cross-fitted logistic model.
            - **Next-Ball Leverage & Live Gate:** $L = \sum_{o \in \{0,1,2,3,4,6,W\}} p(o) |WP(\text{after } o) - WP(\text{before})|$.
              $$\text{PI}_{\text{bat}} = 100 \cdot (1 - WP_{\text{bat}}) \cdot \min\!\left(1, \frac{L}{\text{median}(L \mid \text{innings})}\right), \qquad \text{PI}_{\text{bowl}} = 100 \cdot WP_{\text{bat}} \cdot \min\!\left(1, \frac{L}{\text{median}(L \mid \text{innings})}\right)$$
            - **Frozen Thresholds:** Pooled batting PI quantiles: **Elevated $\ge 52.0$** (65th percentile), **High $\ge 66.1$** (88th percentile).

            #### 3. Context-Adjusted Baselines, PRD, Shrinkage & Ranking Estimand
            - **Hierarchical Context Baselines (`src/baselines/expected_performance.py`):** 5-fold match-cross-fitted expectations stratified by `format_group × innings × phase × wkts_bucket × pressure_level` with hierarchical empirical-Bayes smoothing ($k = 100$ balls) toward parent strata.
            - **Per-Delivery Value:**
              - Batting: $\text{CABV} = (r - E[r \mid \text{ctx}]) - 0.30 \cdot WV \cdot (\text{out} - E[\text{out} \mid \text{ctx}])$, scaled per 100 balls faced.
              - Bowling: $\text{RP} = (E[c \mid \text{ctx}] - c) + 0.20 \cdot WV \cdot (\text{wkt} - E[\text{wkt} \mid \text{ctx}])$, scaled per 24 bowling deliveries.
            - **Match-Cluster Bootstrap & Volume-Weighted Empirical Bayes (`src/reliability/`):** 250 match-cluster resamples (`seed=42`) yield standard error $SE_i$. Prior $(\mu, \tau^2)$ is estimated on the eligible population via ball-weighted method of moments. Posterior mean (`APR` / `rating_mean`): $\hat{\theta}_i = \mu + B_i(\bar{y}_i - \mu)$, $B_i = \tau^2/(\tau^2 + SE_i^2)$, $SD_i = \sqrt{\tau^2 SE_i^2 / (\tau^2 + SE_i^2)}$.
            - **Pressure Response Delta (PRD):** $\text{PRD}_i = \hat{\theta}_{i,\text{pressure}} - \hat{\theta}_{i,\text{normal}}$. Because normal states typically have ~2× more deliveries and higher between-player variance $\tau^2_{\text{normal}}$, players with extraordinary normal-state baselines (e.g., Jasprit Bumrah in bowling or Suryakumar Yadav in batting) can exhibit negative `PRD` while still holding top-3 absolute pressure ratings (`APR` and `RPR`).
            - **Official Ranking Estimand (RPR):** $\text{RPR}_i = \hat{\theta}_{i,\text{pressure}} - 1.2816 \cdot SD_{i,\text{pressure}}$ (one-sided 90% lower confidence bound).
            """
        )

    with tab_kpi:
        st.markdown("#### Complete KPI Hierarchy & Definitions (Section 13 Compliance)")
        kpi_df = pd.DataFrame(KPI_CATALOG)
        st.dataframe(kpi_df, use_container_width=True, hide_index=True)

        st.markdown("#### Downloadable Reports & Reproducibility Artefacts")
        dc1, dc2 = st.columns(2)
        pdf_path = REPORTS / "methodology" / "PRESSUREIQ_METHODOLOGY_REPORT.pdf"
        md_path = REPORTS / "methodology" / "PRESSUREIQ_METHODOLOGY_REPORT.md"
        with dc1:
            if pdf_path.exists():
                st.download_button(
                    "Download Official Methodology Report (PDF)",
                    pdf_path.read_bytes(),
                    file_name="PRESSUREIQ_METHODOLOGY_REPORT.pdf",
                    mime="application/pdf",
                )
        with dc2:
            if md_path.exists():
                st.download_button(
                    "Download Official Methodology Report (Markdown)",
                    md_path.read_bytes(),
                    file_name="PRESSUREIQ_METHODOLOGY_REPORT.md",
                    mime="text/markdown",
                )

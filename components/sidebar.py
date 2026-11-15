"""Persistent left sidebar navigation and global exploratory filters (Section 15)."""

from __future__ import annotations

import streamlit as st

SECTIONS = [
    "00 · Executive Overview",
    "01 · Pressure Engine",
    "02 · Batting Intelligence",
    "03 · Bowling Intelligence",
    "04 · Reliability Lab",
    "05 · Player Rankings",
    "06 · Evidence & Validation",
    "07 · Methodology & Data Audit",
]

ALL_SEASONS = [2022, 2023, 2024, 2025, 2026]
ALL_PHASES = ["Powerplay", "Middle", "Death"]
DEFAULTS = {
    "f_comp": "Combined (IPL + T20I)",
    "f_seasons": ALL_SEASONS,
    "f_tier": "Elevated + High (Official)",
    "f_phases": ALL_PHASES,
}


def _reset_filters() -> None:
    for k, v in DEFAULTS.items():
        st.session_state[k] = list(v) if isinstance(v, list) else v


def render_sidebar() -> dict:
    for k, v in DEFAULTS.items():
        st.session_state.setdefault(k, list(v) if isinstance(v, list) else v)

    with st.sidebar:
        st.markdown(
            """
            <div style="padding: 0 0 0.75rem 0; border-bottom: 1px solid rgba(255,255,255,0.14); margin-bottom: 0.8rem;">
                <div style="font-size: 1.3rem; font-weight: 800; letter-spacing: 0.03em; color: #FFFFFF;">PRESSURE<span style="color:#2DD4BF;">IQ</span></div>
                <div style="font-size: 0.75rem; color: #94A3B8; margin-top: 0.15rem;">The science of performing when it matters</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        section = st.radio("Navigation", SECTIONS, index=0, key="nav")

        st.markdown("<hr style='border-color:rgba(255,255,255,0.14); margin: 0.8rem 0 0.6rem 0;'>", unsafe_allow_html=True)
        st.markdown(
            "<div style='font-size:0.74rem; font-weight:700; letter-spacing:0.05em; color:#94A3B8; margin-bottom:0.35rem;'>ANALYSIS MODE & GLOBAL FILTERS</div>",
            unsafe_allow_html=True,
        )

        comp = st.selectbox("Competition Scope", ["Combined (IPL + T20I)", "IPL Only", "T20I Only"], key="f_comp")
        seasons = st.multiselect("Seasons", ALL_SEASONS, key="f_seasons")
        pressure_tier = st.selectbox("Pressure Intensity", ["Elevated + High (Official)", "High Pressure Only"], key="f_tier")
        phases = st.multiselect("Innings Phase", ALL_PHASES, key="f_phases")

        is_official = (
            comp == DEFAULTS["f_comp"]
            and set(seasons) == set(ALL_SEASONS)
            and pressure_tier == DEFAULTS["f_tier"]
            and set(phases) == set(ALL_PHASES)
        )

        st.button("Reset to Official Scope", use_container_width=True, on_click=_reset_filters, disabled=is_official)

        if is_official:
            st.markdown(
                "<div style='background:rgba(13,148,136,0.2); border:1px solid #14B8A6; padding:0.55rem 0.7rem; border-radius:6px; font-size:0.75rem; margin-top:0.5rem; line-height:1.4;'>"
                "<b>Mode: Official Scope</b><br>853 IPL + T20I matches (2022–2026). Official Top-10 rankings are locked to this scope.</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div style='background:rgba(217,119,6,0.22); border:1px solid #F59E0B; padding:0.55rem 0.7rem; border-radius:6px; font-size:0.75rem; margin-top:0.5rem; line-height:1.4;'>"
                "<b>Mode: Exploratory View</b><br>Custom filters apply to descriptive charts. Official rankings are never recomputed from filters.</div>",
                unsafe_allow_html=True,
            )

    return {
        "section": section,
        "competition": comp,
        "seasons": seasons or ALL_SEASONS,
        "pressure_tier": pressure_tier,
        "phases": phases or ALL_PHASES,
        "is_official": is_official,
    }

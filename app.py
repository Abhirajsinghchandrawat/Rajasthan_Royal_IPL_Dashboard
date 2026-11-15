"""PRESSUREIQ — Main Streamlit Application Entry Point.

Run locally with:
    streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

from components.kpi_cards import inject_custom_css
from components.sidebar import render_sidebar
from dashboard.batting import render_batting_intelligence
from dashboard.bowling import render_bowling_intelligence
from dashboard.evidence import render_evidence_validation
from dashboard.methodology import render_methodology_audit
from dashboard.overview import render_overview
from dashboard.pressure_engine import render_pressure_engine
from dashboard.rankings import render_rankings
from dashboard.reliability import render_reliability_lab

st.set_page_config(
    page_title="PRESSUREIQ · Cricket Pressure Performance Intelligence",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_custom_css()
filters = render_sidebar()

sec = filters["section"]
if sec.startswith("00"):
    render_overview(filters)
elif sec.startswith("01"):
    render_pressure_engine(filters)
elif sec.startswith("02"):
    render_batting_intelligence(filters)
elif sec.startswith("03"):
    render_bowling_intelligence(filters)
elif sec.startswith("04"):
    render_reliability_lab(filters)
elif sec.startswith("05"):
    render_rankings(filters)
elif sec.startswith("06"):
    render_evidence_validation(filters)
elif sec.startswith("07"):
    render_methodology_audit(filters)

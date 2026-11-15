"""Enterprise sports analytics UI components: high-contrast CSS theme, KPI cards, and banners."""

from __future__ import annotations

import streamlit as st

from config.settings import COLORS


def inject_custom_css() -> None:
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        /* Force high-contrast enterprise light surface & dark slate typography globally */
        :root {{
            color-scheme: light !important;
        }}
        html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
            background-color: {COLORS['bg']} !important;
            color: {COLORS['text']} !important;
        }}
        [data-testid="stHeader"] {{
            background-color: rgba(244, 247, 250, 0.88) !important;
        }}

        /* Main content typography — explicit dark navy/slate so dark-mode browsers never wash out text */
        .main .block-container,
        [data-testid="stMainBlockContainer"] {{
            padding-top: 1.35rem !important;
            padding-bottom: 2.5rem !important;
            max-width: 1440px !important;
            color: {COLORS['text']} !important;
        }}
        [data-testid="stMain"] h1,
        [data-testid="stMain"] h2,
        [data-testid="stMain"] h3,
        [data-testid="stMain"] h4,
        [data-testid="stMain"] h5,
        [data-testid="stMain"] h6 {{
            color: {COLORS['navy']} !important;
            font-weight: 700 !important;
            letter-spacing: -0.015em;
        }}
        [data-testid="stMain"] p,
        [data-testid="stMain"] li,
        [data-testid="stMain"] span,
        [data-testid="stMain"] label,
        [data-testid="stMain"] div[data-testid="stMarkdownContainer"],
        [data-testid="stMain"] div[data-testid="stCaptionContainer"] {{
            color: {COLORS['text']} !important;
        }}
        [data-testid="stMain"] div[data-testid="stCaptionContainer"] p {{
            color: #475569 !important;
            font-size: 0.82rem !important;
        }}

        /* Main area inputs, selectboxes, radios, tabs, expanders, and buttons */
        [data-testid="stMain"] div[data-baseweb="select"] > div,
        [data-testid="stMain"] div[data-baseweb="input"] > div {{
            background-color: #FFFFFF !important;
            border: 1px solid #CBD5E1 !important;
            color: {COLORS['text']} !important;
        }}
        [data-testid="stMain"] div[data-baseweb="select"] span,
        [data-testid="stMain"] input {{
            color: {COLORS['text']} !important;
        }}
        [data-testid="stMain"] [data-testid="stExpander"] {{
            background-color: #FFFFFF !important;
            border: 1px solid #CBD5E1 !important;
            border-radius: 10px !important;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
        }}
        [data-testid="stMain"] [data-testid="stExpander"] summary,
        [data-testid="stMain"] [data-testid="stExpander"] summary span,
        [data-testid="stMain"] [data-testid="stExpander"] summary p {{
            color: {COLORS['navy']} !important;
            font-weight: 700 !important;
        }}
        [data-testid="stMain"] [data-testid="stExpanderDetails"] p,
        [data-testid="stMain"] [data-testid="stExpanderDetails"] li,
        [data-testid="stMain"] [data-testid="stExpanderDetails"] span {{
            color: {COLORS['text']} !important;
        }}
        [data-testid="stMain"] button[data-baseweb="tab"] {{
            color: #475569 !important;
            font-weight: 600 !important;
        }}
        [data-testid="stMain"] button[data-baseweb="tab"][aria-selected="true"] {{
            color: {COLORS['teal']} !important;
            border-bottom-color: {COLORS['teal']} !important;
            font-weight: 700 !important;
        }}
        [data-testid="stMain"] .stDownloadButton button,
        [data-testid="stMain"] .stButton button {{
            background-color: {COLORS['navy']} !important;
            color: #FFFFFF !important;
            border: 1px solid {COLORS['navy2']} !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
        }}
        [data-testid="stMain"] .stDownloadButton button *,
        [data-testid="stMain"] .stButton button * {{
            color: #FFFFFF !important;
        }}
        [data-testid="stMain"] .stDownloadButton button:hover,
        [data-testid="stMain"] .stButton button:hover {{
            background-color: {COLORS['teal']} !important;
            border-color: {COLORS['teal']} !important;
        }}

        /* Persistent Left Sidebar — Deep Navy Executive Theme */
        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, {COLORS['navy']} 0%, {COLORS['navy2']} 100%) !important;
            border-right: 1px solid #1E324A !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {{
            padding-top: 1.1rem !important;
        }}
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] div {{
            color: #F1F5F9 !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {{
            font-size: 0.74rem !important;
            font-weight: 700 !important;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            color: #94A3B8 !important;
        }}
        section[data-testid="stSidebar"] .stSelectbox,
        section[data-testid="stSidebar"] .stMultiSelect {{
            margin-bottom: 0.15rem !important;
        }}
        /* Navigation: full-width rows with a clear active state */
        section[data-testid="stSidebar"] div[role="radiogroup"] {{
            gap: 2px !important;
        }}
        section[data-testid="stSidebar"] div[role="radiogroup"] label {{
            width: 100%;
            margin: 0 !important;
            padding: 0.42rem 0.6rem !important;
            border-radius: 6px;
            border-left: 3px solid transparent;
            transition: background 0.15s ease;
        }}
        section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {{
            background: rgba(255, 255, 255, 0.06);
        }}
        section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {{
            background: rgba(13, 148, 136, 0.24);
            border-left-color: #2DD4BF;
        }}
        section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p {{
            font-weight: 700 !important;
            color: #FFFFFF !important;
        }}
        section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div,
        section[data-testid="stSidebar"] .stMultiSelect div[data-baseweb="select"] > div {{
            background-color: rgba(15, 23, 42, 0.55) !important;
            border: 1px solid rgba(148, 163, 184, 0.35) !important;
            color: #FFFFFF !important;
        }}
        section[data-testid="stSidebar"] span[data-baseweb="tag"] {{
            background-color: rgba(13, 148, 136, 0.55) !important;
        }}
        section[data-testid="stSidebar"] .stButton button {{
            background-color: {COLORS['teal']} !important;
            color: #FFFFFF !important;
            border: none !important;
            font-weight: 700 !important;
            margin-top: 0.35rem;
        }}

        /* Top Banner Header (compact) */
        .piq-header {{
            background: linear-gradient(135deg, {COLORS['navy']} 0%, {COLORS['navy2']} 100%) !important;
            color: #FFFFFF !important;
            padding: 0.85rem 1.35rem;
            border-radius: 10px;
            margin-bottom: 1rem;
            display: flex;
            flex-wrap: wrap;
            gap: 0.6rem 1.2rem;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 4px 14px rgba(20, 36, 58, 0.14);
            border-bottom: 3px solid {COLORS['teal']};
        }}
        .piq-header-text {{ min-width: 0; flex: 1 1 420px; }}
        .piq-header h1, .piq-header h1 * {{
            margin: 0 !important;
            padding: 0 !important;
            font-size: 1.24rem !important;
            line-height: 1.25 !important;
            font-weight: 800 !important;
            letter-spacing: -0.015em;
            color: #FFFFFF !important;
        }}
        .piq-header p, .piq-header p * {{
            margin: 0.2rem 0 0 0 !important;
            font-size: 0.84rem !important;
            line-height: 1.35 !important;
            color: #CBD5E1 !important;
        }}
        .piq-badge {{
            display: inline-flex;
            align-items: center;
            white-space: nowrap;
            padding: 0.34rem 0.8rem;
            border-radius: 999px;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }}
        .piq-badge-official {{
            background-color: rgba(13, 148, 136, 0.28) !important;
            border: 1px solid #2DD4BF !important;
            color: #99F6E4 !important;
        }}
        .piq-badge-exploratory {{
            background-color: rgba(217, 119, 6, 0.30) !important;
            border: 1px solid #FBBF24 !important;
            color: #FEF08A !important;
        }}

        /* KPI Cards — fixed, equal geometry in every row */
        .piq-card {{
            box-sizing: border-box;
            height: 122px;
            display: flex;
            flex-direction: column;
            background: #FFFFFF !important;
            border: 1px solid #CBD5E1 !important;
            border-top: 4px solid {COLORS['navy']} !important;
            border-radius: 10px;
            padding: 0.8rem 1rem 0.75rem 1rem;
            box-shadow: 0 2px 5px rgba(15, 23, 42, 0.05);
            overflow: hidden;
        }}
        .piq-card.teal {{ border-top-color: {COLORS['teal']} !important; }}
        .piq-card.amber {{ border-top-color: {COLORS['amber']} !important; }}
        .piq-card.coral {{ border-top-color: {COLORS['coral']} !important; }}
        .piq-card.grey {{ border-top-color: #94A3B8 !important; }}
        .piq-card.featured {{
            border-top-color: {COLORS['teal']} !important;
            background: linear-gradient(180deg, #F0FDFA 0%, #FFFFFF 75%) !important;
            box-shadow: 0 0 0 1px rgba(13, 148, 136, 0.28), 0 2px 6px rgba(15, 23, 42, 0.06);
        }}
        .piq-card-label {{
            font-size: 0.71rem !important;
            font-weight: 700 !important;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #475569 !important;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            line-height: 1.2;
            min-height: 1.2em;
        }}
        .piq-card-value {{
            margin-top: 0.3rem;
            font-size: clamp(1.15rem, 1.5vw, 1.6rem) !important;
            font-weight: 800 !important;
            color: {COLORS['navy']} !important;
            line-height: 1.2;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .piq-card.featured .piq-card-value {{
            font-size: clamp(1.0rem, 1.2vw, 1.3rem) !important;
            padding-top: 0.12rem;
        }}
        .piq-card-sub {{
            margin-top: 0.3rem;
            font-size: 0.75rem !important;
            font-weight: 500 !important;
            color: #475569 !important;
            line-height: 1.3;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }}
        @media (max-width: 1280px) {{
            .piq-card {{ height: 128px; padding: 0.7rem 0.8rem; }}
            .piq-card-sub {{ font-size: 0.72rem !important; }}
        }}

        /* Podium panels — equal height */
        .piq-panel {{
            background: #FFFFFF !important;
            border: 1px solid #CBD5E1 !important;
            border-radius: 10px;
            padding: 0.85rem 1rem;
            margin-bottom: 0.9rem;
            box-shadow: 0 2px 5px rgba(15, 23, 42, 0.04);
            color: {COLORS['text']} !important;
        }}
        .piq-panel * {{
            color: {COLORS['text']};
        }}
        .piq-podium {{
            box-sizing: border-box;
            height: 112px;
            overflow: hidden;
            border-top: 4px solid {COLORS['teal']} !important;
        }}
        .piq-podium .pd-rank {{ font-size: 0.71rem; font-weight: 800; letter-spacing: 0.05em; color: #0F766E !important; }}
        .piq-podium .pd-name {{ font-size: 1.02rem; font-weight: 800; color: {COLORS['navy']} !important; margin: 0.2rem 0;
                                white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .piq-podium .pd-line {{ font-size: 0.76rem; color: #334155 !important; white-space: nowrap; overflow: hidden;
                                text-overflow: ellipsis; }}
        .piq-podium .pd-line b {{ color: #0F766E !important; }}

        /* Chart section heading used between rows */
        .piq-row-label {{
            font-size: 0.72rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase;
            color: #64748B !important; margin: 0.4rem 0 0.2rem 0;
        }}

        /* Callout Banners — Explicit Dark Slate Text on Tinted Surface */
        .piq-callout {{
            background-color: #F0FDFA !important;
            border-left: 5px solid {COLORS['teal']} !important;
            border-top: 1px solid #99F6E4 !important;
            border-right: 1px solid #99F6E4 !important;
            border-bottom: 1px solid #99F6E4 !important;
            padding: 0.95rem 1.2rem;
            border-radius: 8px;
            margin: 0.65rem 0 1.1rem 0;
            font-size: 0.9rem !important;
            line-height: 1.55 !important;
            color: #0F172A !important;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
        }}
        .piq-callout,
        .piq-callout p,
        .piq-callout span {{
            color: #1E293B !important;
        }}
        .piq-callout b,
        .piq-callout strong {{
            color: #0F766E !important;
            font-weight: 700 !important;
        }}
        .piq-callout.amber {{
            background-color: #FFFBEB !important;
            border-left-color: {COLORS['amber']} !important;
            border-top-color: #FDE68A !important;
            border-right-color: #FDE68A !important;
            border-bottom-color: #FDE68A !important;
            color: #1E293B !important;
        }}
        .piq-callout.amber b,
        .piq-callout.amber strong {{
            color: #B45309 !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str, is_official_mode: bool = True, status: str = "VALIDATED") -> None:
    mode_cls = "piq-badge-official" if is_official_mode else "piq-badge-exploratory"
    mode_txt = f"OFFICIAL SCOPE · {status}" if is_official_mode else "EXPLORATORY FILTERED VIEW"
    st.markdown(
        f"""
        <div class="piq-header">
            <div class="piq-header-text">
                <h1>{title}</h1>
                <p>{subtitle}</p>
            </div>
            <span class="piq-badge {mode_cls}">{mode_txt}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


_ACCENT_ALIAS = {"green": "teal", "navy": "navy"}


def _esc(s: str) -> str:
    return str(s).replace('"', "&quot;")


def kpi_card(label: str, value: str, subtitle: str = "", accent: str = "navy") -> str:
    accent = _ACCENT_ALIAS.get(accent, accent)
    return f"""
    <div class="piq-card {accent}">
        <div class="piq-card-label" title="{_esc(label)}">{label}</div>
        <div class="piq-card-value" title="{_esc(value)}">{value}</div>
        <div class="piq-card-sub" title="{_esc(subtitle)}">{subtitle}</div>
    </div>
    """


def signed_accent(v) -> str:
    """Teal for >= 0, coral for < 0, grey when unavailable."""
    try:
        if v is None or v != v:
            return "grey"
        return "teal" if float(v) >= 0 else "coral"
    except (TypeError, ValueError):
        return "grey"


def render_kpi_row(items: list[dict]) -> None:
    cols = st.columns(len(items), gap="small")
    for col, item in zip(cols, items):
        with col:
            st.markdown(
                kpi_card(
                    item["label"],
                    item["value"],
                    item.get("sub", ""),
                    item.get("accent", "navy"),
                ),
                unsafe_allow_html=True,
            )
    st.markdown("<div style='height:0.65rem'></div>", unsafe_allow_html=True)


def callout(text: str, tone: str = "teal") -> None:
    cls = "piq-callout amber" if tone == "amber" else "piq-callout"
    st.markdown(f'<div class="{cls}">{text}</div>', unsafe_allow_html=True)

"""Cached data loader for the PressureIQ Streamlit application."""

from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from config.settings import DATA_ANALYTICAL, DATA_INTERIM, DATA_PROCESSED


@st.cache_data(show_spinner=False)
def load_summary_meta() -> dict:
    p = DATA_ANALYTICAL / "summary_metadata.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text())


@st.cache_data(show_spinner=False)
def load_parquet(name: str, processed: bool = False) -> pd.DataFrame:
    folder = DATA_PROCESSED if processed else DATA_ANALYTICAL
    p = folder / f"{name}.parquet"
    if not p.exists():
        return pd.DataFrame()
    return pd.read_parquet(p)


@st.cache_data(show_spinner=False)
def load_interim_csv(name: str) -> pd.DataFrame:
    p = DATA_INTERIM / f"{name}.csv"
    if not p.exists():
        return pd.DataFrame()
    return pd.read_csv(p)


@st.cache_data(show_spinner=False)
def load_interim_json(name: str) -> dict:
    p = DATA_INTERIM / f"{name}.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text())

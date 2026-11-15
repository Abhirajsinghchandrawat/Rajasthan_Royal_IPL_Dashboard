"""Tests for match-cluster bootstrap reproducibility, Empirical Bayes shrinkage, and sample counts."""

from __future__ import annotations

import numpy as np
import pandas as pd

from config.settings import DATA_ANALYTICAL
from src.reliability.shrinkage import estimate_prior, shrink
from src.reliability.uncertainty import cluster_bootstrap


def test_bootstrap_reproducibility():
    bmt = pd.read_parquet(DATA_ANALYTICAL / "batting_match_table.parquet")
    pm = bmt[bmt["context"] == "pressure"]
    sub = pm[pm["player_id"].isin(pm["player_id"].unique()[:15])]
    r1 = cluster_bootstrap(sub, n_boot=50, seed=42)
    r2 = cluster_bootstrap(sub, n_boot=50, seed=42)
    assert np.allclose(r1["se"].dropna(), r2["se"].dropna())
    assert np.allclose(r1["boot_lo"].dropna(), r2["boot_lo"].dropna())


def test_shrinkage_pulls_toward_prior():
    rates = pd.Series([-0.20, 0.0, 0.25, 0.40])
    ses = pd.Series([0.25, 0.05, 0.05, 0.30])
    weights = pd.Series([50, 500, 500, 40])
    mu, tau2 = estimate_prior(rates, ses, weights)
    pm, psd, B = shrink(rates, ses, mu, tau2)
    # Small-sample noisy observations (indices 0 and 3) have smaller B than large-sample (1 and 2)
    assert B.iloc[0] < B.iloc[1]
    assert B.iloc[3] < B.iloc[2]
    # Shrunk mean is always between observed rate and prior mean mu
    for r_obs, r_post in zip(rates, pm):
        assert abs(r_post - mu) <= abs(r_obs - mu) + 1e-9
    assert (psd <= ses).all()

"""Empirical-Bayes (normal-normal) shrinkage of per-ball contribution rates.

Model
-----
    observed_i ~ N(theta_i, se_i^2)        se_i = match-cluster bootstrap SE
    theta_i    ~ N(mu, tau^2)              population of eligible players

    mu    = ball-weighted mean rate of the eligible population
    tau^2 = max(var(observed) - mean(se^2), floor)   (method of moments)
    post_mean_i = mu + B_i (observed_i - mu),  B_i = tau^2 / (tau^2 + se_i^2)
    post_sd_i   = sqrt(tau^2 se_i^2 / (tau^2 + se_i^2))

Why: a player whose rate rests on few, volatile matches has a large se_i and
is pulled strongly towards mu; a player with many consistent matches keeps
most of their observed rate. The shrinkage strength is learned from the data
(tau^2), not chosen by hand, and post_sd_i never claims more certainty than
the bootstrap supports (post_sd_i <= se_i).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def estimate_prior(rate: pd.Series, se: pd.Series, weights: pd.Series) -> tuple[float, float]:
    ok = rate.notna() & se.notna() & (weights > 0)
    w = weights[ok].to_numpy(float)
    w = w / w.sum()
    r = rate[ok].to_numpy(float)
    s2 = (se[ok].to_numpy(float)) ** 2
    mu = float((w * r).sum())
    var_obs = float((w * (r - mu) ** 2).sum())
    mean_se2 = float((w * s2).sum())
    tau2 = float(var_obs - mean_se2)
    floor = 0.15 * var_obs
    return mu, max(tau2, floor)


def shrink(rate: pd.Series, se: pd.Series, mu: float, tau2: float) -> tuple[pd.Series, pd.Series, pd.Series]:
    se2 = se ** 2
    B = tau2 / (tau2 + se2)
    post_mean = mu + B * (rate - mu)
    post_sd = np.sqrt(tau2 * se2 / (tau2 + se2))
    return post_mean, post_sd, B

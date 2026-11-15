"""Match-cluster bootstrap for per-ball contribution rates.

Resampling unit: the MATCH. Deliveries within one innings share conditions,
opposition and the batter's form, so treating them as independent would
understate uncertainty. For a player with match-level (value_m, balls_m),
each replicate resamples the player's matches with replacement and computes
sum(value)/sum(balls). B = 250 replicates, seed = 42 (settings), 90% CI
(percentile). A player with few matches automatically gets a wide interval.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from config.settings import BOOTSTRAP_ITERATIONS, CONFIDENCE_LEVEL, RANDOM_SEED


def cluster_bootstrap(mt: pd.DataFrame, value_col: str = "value", balls_col: str = "balls",
                      n_boot: int = BOOTSTRAP_ITERATIONS, seed: int = RANDOM_SEED,
                      level: float = CONFIDENCE_LEVEL) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    lo_q, hi_q = (1 - level) / 2, 1 - (1 - level) / 2
    rows = []
    for pid, g in mt.groupby("player_id", sort=True):
        v = g[value_col].to_numpy(float)
        b = g[balls_col].to_numpy(float)
        n = len(v)
        obs = v.sum() / b.sum() if b.sum() > 0 else np.nan
        if n < 2:
            rows.append((pid, n, obs, np.nan, np.nan, np.nan))
            continue
        idx = rng.integers(0, n, size=(n_boot, n))
        bs = v[idx].sum(1) / np.maximum(b[idx].sum(1), 1e-9)
        rows.append((pid, n, obs, bs.std(ddof=1), np.quantile(bs, lo_q), np.quantile(bs, hi_q)))
    return pd.DataFrame(rows, columns=["player_id", "n_matches", "rate", "se", "boot_lo", "boot_hi"])

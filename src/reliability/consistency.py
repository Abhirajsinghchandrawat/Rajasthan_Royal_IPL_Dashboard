"""Match-to-match consistency and season stability.

Benchmark: a match is a "pressure success" when the player's context-adjusted
value in that match's pressure deliveries is > 0, i.e. they beat the
expectation for those exact situations. This avoids raw SD, which is not
comparable across players with different volumes and means (spec 9.4).

- success_rate  share of pressure matches with value > 0
- median_match  median match pressure value (runs)
- iqr_match     IQR of match pressure value (runs)
- top_match_share share of the player's total positive value coming from their
                single best match (outlier dependence)
- season_positive_share share of qualifying seasons (>= SEASON_MIN_BALLS pressure
                balls) with a positive rate
- season_sd     SD of qualifying season rates (per-ball x scale)
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from config.settings import SEASON_MIN_BALLS


def consistency_metrics(pm: pd.DataFrame, scale: float) -> pd.DataFrame:
    g = pm.groupby("player_id")["value"]
    out = pd.DataFrame({
        "success_rate": g.apply(lambda s: float((s > 0).mean())),
        "median_match": g.median(),
        "iqr_match": g.quantile(0.75) - g.quantile(0.25),
        "top_match_share": g.apply(lambda s: float(s.max() / s[s > 0].sum()) if (s > 0).any() else np.nan),
    })
    se = pm.groupby(["player_id", "season"]).agg(v=("value", "sum"), b=("balls", "sum")).reset_index()
    se = se[se["b"] >= SEASON_MIN_BALLS]
    se["rate"] = scale * se["v"] / se["b"]
    st = se.groupby("player_id").agg(qual_seasons=("season", "nunique"),
                                     season_positive_share=("rate", lambda s: float((s > 0).mean())),
                                     season_sd=("rate", lambda s: float(s.std(ddof=1)) if len(s) > 1 else np.nan))
    return out.join(st, how="left").reset_index()


def season_table(pm: pd.DataFrame, scale: float) -> pd.DataFrame:
    se = pm.groupby(["player_id", "season"]).agg(value=("value", "sum"), balls=("balls", "sum"),
                                                  matches=("match_id", "nunique")).reset_index()
    se["rate"] = scale * se["value"] / se["balls"]
    se["qualifying"] = se["balls"] >= SEASON_MIN_BALLS
    return se

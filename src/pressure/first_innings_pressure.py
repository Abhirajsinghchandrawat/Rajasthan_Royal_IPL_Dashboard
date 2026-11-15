"""First-innings pressure features (batting first, no target exists).

Cricket rationale
-----------------
With no target, the batting side's real question is "are we on course for a
competitive total given what we have left?". That is answered by comparing
the *projected* total with *par*:

    projected = runs so far + E(balls left, wickets in hand)
    par       = E(allocated balls, 10 wickets)     (revised allocations honoured)
    deviation = projected - par

Note what this deliberately does NOT do:
- A fast run rate with wickets in hand gives a positive deviation, i.e. LOW
  batting difficulty, not high pressure.
- Death overs are not pressure by construction: 160/2 after 16 overs is
  well ahead of par.
- Losing wickets cuts E(u, w) sharply, so a collapse raises difficulty even
  when the run rate looks healthy.

How much a given deviation matters grows as the innings runs out of time to
recover (progress interaction). Those features feed a win-probability model
whose label is the batting-first side winning.
"""

from __future__ import annotations

import numpy as np

from src.pressure.resource_model import ResourceModel


def first_innings_features(rm: ResourceModel, runs, u, w, alloc, fmt) -> np.ndarray:
    runs = np.asarray(runs, float)
    u = np.asarray(u, float)
    w = np.asarray(w, float)
    alloc = np.asarray(alloc, float)
    exp_rem = rm.predict(u, w, fmt)
    par = rm.predict(alloc, np.full_like(alloc, 10), fmt)
    dev = (runs + exp_rem - par) / 20.0
    progress = np.clip(1 - u / np.maximum(alloc, 1), 0, 1)
    is_t20i = (np.asarray(fmt) == "T20I").astype(float)
    return np.column_stack([dev, dev * progress, w / 10.0, progress, (w / 10.0) * progress, is_t20i])


FIRST_INNINGS_FEATURE_NAMES = ["par_dev_20", "par_dev_x_progress", "wkts_frac", "progress",
                               "wkts_x_progress", "is_t20i"]

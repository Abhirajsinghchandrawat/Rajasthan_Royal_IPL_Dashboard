"""Run-chase pressure features.

Cricket rationale
-----------------
A chase is defined by runs needed (r), legal balls left (u) and wickets in
hand (w). Required run rate alone is misleading: needing 10 an over with
9 wickets in hand is very different from needing 10 an over with 3. The
key quantity is the *resource ratio*

    ratio = r / E(u, w)

i.e. runs needed as a share of what a typical side would be expected to score
from this exact resource state (Duckworth–Lewis logic). ratio ~ 1 is a
balanced chase; > 1 means the chase needs above-average output from the
remaining resources; < 1 means the chase is ahead of the game.

Revised (DLS) targets and revised legal-ball allocations are applied before
this point (cricket_accounting). Chases whose target cannot be reconstructed
are flagged `target_unreliable` and never scored.
"""

from __future__ import annotations

import numpy as np

from src.pressure.resource_model import ResourceModel


def chase_features(rm: ResourceModel, runs_needed, u, w, fmt) -> np.ndarray:
    r = np.asarray(runs_needed, float)
    u = np.asarray(u, float)
    w = np.asarray(w, float)
    exp_rem = np.maximum(rm.predict(u, w, fmt), 0.5)
    log_ratio = np.log(np.clip(r, 0.5, None) / exp_rem)
    rrr_ball = np.clip(r / np.maximum(u, 1), 0, 4)
    time_frac = u / 120.0
    is_t20i = (np.asarray(fmt) == "T20I").astype(float)
    return np.column_stack([log_ratio, log_ratio * (1 - time_frac), rrr_ball, w / 10.0, time_frac, is_t20i])


CHASE_FEATURE_NAMES = ["log_resource_ratio", "log_ratio_x_progress", "req_runs_per_ball", "wkts_frac",
                       "balls_left_frac", "is_t20i"]

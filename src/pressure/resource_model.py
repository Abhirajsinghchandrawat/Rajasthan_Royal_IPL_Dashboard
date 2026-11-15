"""Expected remaining runs E(u, w): the batting-resource table.

Cricket rationale
-----------------
In T20 the two scarce batting resources are legal balls remaining (u) and
wickets in hand (w). Duckworth–Lewis showed remaining scoring potential follows
Z(u, w) = Z_w * (1 - exp(-b_w * u)): runs flatten as wickets fall because
batters must protect their wicket. We fit exactly that functional form per
wickets-in-hand from *first innings* that were allowed to run their full
20-over course (unrevised, completed by 120 legal balls or all out), so the
target variable (runs still to come) is not truncated by rain or a chase win.

A format multiplier (IPL vs T20I) rescales the pooled shape: IPL scoring is
materially higher, and T20I includes associate nations.

The table gives:
- first-innings par at any state:   projected = runs + E(u, w)
- chase resource ratio:             runs_needed / E(u, w)
- the run value of a wicket:        E(u, w) - E(u, w - 1)
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit


def _dl(u, z, b):
    return z * (1.0 - np.exp(-b * u))


class ResourceModel:
    def __init__(self) -> None:
        self.params: dict[int, tuple[float, float]] = {}
        self.format_mult: dict[str, float] = {}

    @staticmethod
    def training_rows(d: pd.DataFrame) -> pd.DataFrame:
        m = (
            (d["innings"] == 1)
            & d["in_official_scope"].fillna(False).astype(bool)
            & (d["allocated_balls_1"] == 120)
            & ((d["inn1_legal"] >= 120) | (d["inn1_wkts"] >= 10))
        )
        t = d.loc[m, ["match_id", "match_date", "format_group", "balls_remaining", "wickets_remaining",
                      "pre_team_runs", "inn1_team_runs"]].copy()
        t["remaining_runs"] = t["inn1_team_runs"] - t["pre_team_runs"]
        return t

    def fit(self, t: pd.DataFrame) -> "ResourceModel":
        for w in range(1, 11):
            s = t[t["wickets_remaining"] == w]
            if len(s) < 200:  # sparse (1-2 wickets in hand): borrow from w+1 later
                continue
            agg = s.groupby("balls_remaining")["remaining_runs"].mean()
            p, _ = curve_fit(_dl, agg.index.values.astype(float), agg.values, p0=[150, 0.01],
                             bounds=([1, 1e-4], [600, 1]), maxfev=20000)
            self.params[w] = (float(p[0]), float(p[1]))
        # sparse low-wicket states: scale the nearest fitted curve downwards
        for w in range(10, 0, -1):
            if w not in self.params:
                nxt = min(k for k in self.params if k > w)
                z, b = self.params[nxt]
                self.params[w] = (z * w / nxt, b * 1.15)
        # enforce monotonicity in w (more wickets in hand can never be worth less)
        base = self._pooled(t["balls_remaining"].values, t["wickets_remaining"].values)
        for f, g in t.assign(pred=base).groupby("format_group"):
            self.format_mult[f] = float(g["remaining_runs"].sum() / max(g["pred"].sum(), 1e-9))
        return self

    def _pooled(self, u, w) -> np.ndarray:
        u = np.asarray(u, dtype=float)
        w = np.asarray(w, dtype=int)
        out = np.zeros_like(u)
        prev = np.zeros_like(u)
        curves = {}
        for k in range(1, 11):
            z, b = self.params[k]
            cur = np.maximum(_dl(u, z, b), prev)
            curves[k] = cur
            prev = cur
        for k in range(1, 11):
            mk = w == k
            out[mk] = curves[k][mk]
        out[w <= 0] = 0.0
        out[u <= 0] = 0.0
        return out

    def predict(self, u, w, fmt) -> np.ndarray:
        mult = pd.Series(np.asarray(fmt)).map(self.format_mult).fillna(1.0).to_numpy()
        return self._pooled(u, w) * mult

    def wicket_value(self, u, w, fmt) -> np.ndarray:
        """Run value of losing one wicket at state (u, w)."""
        w = np.asarray(w)
        return np.maximum(self.predict(u, w, fmt) - self.predict(u, w - 1, fmt), 0.0)

    def table(self) -> pd.DataFrame:
        rows = []
        for fmt in self.format_mult:
            for w in range(1, 11):
                for u in range(0, 121, 6):
                    rows.append({"format_group": fmt, "wickets_remaining": w, "balls_remaining": u,
                                 "expected_remaining_runs": float(self.predict([u], [w], [fmt])[0])})
        return pd.DataFrame(rows)

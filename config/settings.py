"""PRESSUREIQ configuration. Modelling constants are frozen here.

Every constant is set from cricket reasoning or data coverage, never from
which players a value favours. Sensitivity analysis varies each of them.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_INTERIM = ROOT / "data" / "interim"
DATA_PROCESSED = ROOT / "data" / "processed"
DATA_ANALYTICAL = ROOT / "data" / "analytical"
REPORTS = ROOT / "reports"
EXPORTS = REPORTS / "exports"
FIGURES = REPORTS / "figures"
METHODOLOGY_DIR = REPORTS / "methodology"

RANDOM_SEED = 42
BOOTSTRAP_ITERATIONS = 250
CONFIDENCE_LEVEL = 0.90
CV_FOLDS = 5  # match-grouped cross-fitting folds (WP model + baselines)

# Pressure classification. Thresholds are the pooled batting-perspective
# Pressure Index quantiles below (computed once from the pressure
# distribution, independent of any player result) and then frozen in
# data/analytical/thresholds.json. Elevated+High = top 35% of deliveries,
# High = top 12%.
PRESSURE_ELEVATED_QUANTILE = 0.65
PRESSURE_HIGH_QUANTILE = 0.88
# "Pressure deliveries" used for ranking = Elevated or High.
# High-only is reported as a sensitivity scenario.
THRESHOLD_SENSITIVITY_SHIFTS = (-10, -5, 5, 10)

# Live-match gate: leverage relative to the per-innings median leverage.
LEVERAGE_GATE_QUANTILE = 0.50

# Eligibility (set from coverage before leaderboards were produced):
# ~10 independent pressure matches and ~16-20 overs of pressure exposure.
BATTER_MIN_PRESSURE_MATCHES = 10
BATTER_MIN_PRESSURE_BALLS = 100
BOWLER_MIN_PRESSURE_MATCHES = 10
BOWLER_MIN_PRESSURE_LEGAL_BALLS = 120
ELIGIBILITY_GRID = [(6, 42), (8, 60), (10, 100), (12, 150), (15, 200)]

# Marginal wicket value share: E(u,w) - E(u,w-1) is the full resource drop if no
# further batters existed (~15-20 runs). Because the incoming batter still scores
# at replacement level, the marginal run cost/value of one wicket above replacement
# is ~25-30% of the raw resource drop (~4-6 runs), preventing single-ball binary
# wicket variance from swamping run-scoring/run-saving signal.
BASELINE_PSEUDOCOUNT = 100.0
WICKET_VALUE_WEIGHT_BAT = 0.30
WICKET_VALUE_WEIGHT_BOWL = 0.20

# Ranking estimand: posterior lower bound with z for a one-sided 90% bound.
RANK_Z = 1.2816
RANK_Z_SENSITIVITY = (0.0, 1.645)

# Minimum pressure balls in a season for season-stability calculations.
SEASON_MIN_BALLS = 30

CHRONO_CUTOFF = "2025-01-01"

PHASE_BINS = {
    "Powerplay": (1, 6),
    "Middle": (7, 15),
    "Death": (16, 20),
}

COLORS = {
    "navy": "#14243A",
    "navy2": "#223750",
    "teal": "#0D9488",
    "green": "#16856A",
    "amber": "#D97706",
    "coral": "#DC6262",
    "bg": "#F4F7FA",
    "card": "#FFFFFF",
    "border": "#E5EAF0",
    "text": "#182536",
    "muted": "#68778A",
    "grey": "#A0AEC0",
}
LEVEL_COLORS = {"Low": "#94A3B8", "Elevated": "#F59E0B", "High": "#B45309"}

# Semantic design tokens (colour by metric meaning, never decoratively)
SEMANTIC = {
    "positive": "#0D9488",   # teal  - positive contribution / improvement
    "negative": "#DC6262",   # coral - negative contribution / deterioration
    "pressure": "#D97706",   # amber - pressure, caution, uncertainty
    "pressure_dark": "#B45309",
    "structure": "#14243A",  # navy  - headers, structural series
    "structure_soft": "#334155",
    "baseline": "#94A3B8",   # grey  - baselines, references, unavailable
    "baseline_dark": "#64748B",
    "neutral": "#94A3B8",
    "neutral_dark": "#64748B",
}
DIVERGING_SCALE = [[0.0, "#DC6262"], [0.5, "#F1F5F9"], [1.0, "#0D9488"]]
PRESSURE_SCALE = [[0.0, "#F8FAFC"], [0.35, "#FDE68A"], [0.7, "#F59E0B"], [1.0, "#B45309"]]
STRUCTURE_SEQ = ["#14243A", "#2B4466", "#4A6488", "#64748B", "#94A3B8"]
IDENTITY_SEQ = ["#14243A", "#0369A1", "#64748B", "#7C3AED", "#0F766E", "#9F1239"]

UNITS = {
    "bat": "CABV runs per 100 pressure balls faced",
    "bat_short": "runs / 100 balls",
    "bowl": "Runs prevented per 24 pressure deliveries (incl. wicket credit)",
    "bowl_short": "runs / 24 deliveries",
}

CHART_H_PAIR = 410   # paired charts in a 2-column row
CHART_H_FULL = 360   # full-width charts

# PRESSUREIQ — Cricket Pressure Performance Intelligence Platform

> *"The science of performing when it matters."*

**PRESSUREIQ** is an end-to-end cricket performance intelligence and decision-support platform engineered to identify the **Top 10 most reliable batters** and **Top 10 most reliable bowlers** under pressure across **853 official IPL and T20 International matches (2022–2026)**.

---

## Key Analytical Highlights

1. **Official Scope & Zero Silent Deletions:**
   - **853 official matches** (371 IPL + 482 T20I; 194,014 deliveries).
   - 30 Other-T20 matches (`Mens T20 Emerging Teams Asia Cup 2024`, `Asia Cup Rising Stars 2025`) and 38 Super Over deliveries (`innings in {3, 4}`) are preserved in raw/interim data with explicit flags (`OUT_OF_OFFICIAL_SCOPE`, `SUPER_OVER`) and excluded from official regulation rankings.
   - Row-level verification of all 264 `extras_type == "other"` deliveries confirms `extras1_runs == 1` on 100% of rows (Beamer/Full Toss height no-balls) and reduces >120-legal-ball regulation innings from 150 to **0**.
   - Row-level verification of the 35 no-ball rows with `extras_2_runs > 0` (`runs == 0`) confirms they are byes/leg-byes off no-balls (counted in team runs, not debited to the bowler).

2. **Pre-Delivery Pressure Engine (Separate 1st-Innings & Chase Frameworks):**
   - **First Innings (Par & Resource Deficit):** Exponential Duckworth–Lewis curves $E(u, w) = Z_w(1 - e^{-b_w u})$ fitted on completed first innings achieve a chronological out-of-sample MAE of **17.11 runs ($R^2 = 0.825$)** vs **27.17 runs ($R^2 = 0.408$)** for naive run-rate projection. First-innings Pressure Index correlates negatively with current run rate ($r = -0.679$), confirming that aggressive boundary sprees from strong positions are not conflated with pressure.
   - **Run Chase (Resource Ratio):** Evaluates $\log(\text{runs\_needed} / E(u, w))$, required runs per ball, wickets fraction, and remaining balls fraction, honouring revised DLS targets and legal-ball allocations.
   - **Live-Match Leverage Gate:**
     $$\text{PI}_{\text{side}} = 100 \times \text{Difficulty}_{\text{side}} \times \min\!\left(1, \frac{\text{Leverage}}{\text{median}(\text{Leverage} \mid \text{innings})}\right)$$
   - **Frozen Thresholds:** Pooled batting PI quantiles: **Elevated $\ge 52.0$** (65th percentile), **High $\ge 66.1$** (88th percentile).

3. **Context-Adjusted Baselines, PRD, Empirical Bayes Shrinkage & RPR:**
   - **5-Fold Match-Cross-Fitted Hierarchical Baselines:** Stratified by `format_group × innings × phase × wkts_bucket × pressure_level` with hierarchical empirical-Bayes smoothing ($k = 100$).
   - **Context-Adjusted Batting Value (CABV):** $(r - E[r \mid \text{ctx}]) - 0.30 \cdot WV \cdot (\text{out} - E[\text{out} \mid \text{ctx}])$, scaled per 100 pressure balls faced.
   - **Context-Adjusted Runs Prevented (RP):** $(E[c \mid \text{ctx}] - c) + 0.20 \cdot WV \cdot (\text{wkt} - E[\text{wkt} \mid \text{ctx}])$, scaled per 24 pressure deliveries.
   - **Pressure Response Delta (PRD):** $\hat{\theta}_{i,\text{pressure}} - \hat{\theta}_{i,\text{normal}}$.
   - **Official Ranking Estimand — Reliable Pressure Rating (RPR):**
     $$\text{RPR}_i = \hat{\theta}_{i,\text{pressure}} - 1.2816 \cdot SD_{i,\text{pressure}}$$
     (one-sided 90% Empirical-Bayes lower confidence bound using match-cluster bootstrap standard errors, $B=250$, `seed=42`).

---

## Quick Start & Reproducibility

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Full Analytical & Validation Pipeline
```bash
python -m src.pipeline
```
This regenerates all Parquet datasets in `data/processed/` and `data/analytical/`, CSV exports in `reports/exports/`, and executes the 23-check validation gate.

### 3. Generate the Official Methodology PDF & Markdown Reports
```bash
python -m src.reporting.generate_methodology_report
```

### 4. Run the Automated Test Suite
```bash
python -m pytest tests/ -v
```

### 5. Launch the Interactive Streamlit Dashboard
```bash
streamlit run app.py
```

---

## Project Architecture

```text
Cricket_performance_System/
├── app.py                              # Main Streamlit entry point (8 sections)
├── config/
│   ├── settings.py                     # Frozen constants, thresholds & colour palette
│   └── metric_definitions.py           # Full Section-13 KPI catalog
├── data/
│   ├── raw/                            # Immutable original CSVs
│   ├── interim/                        # Phase 1 audit & extras verification artefacts
│   ├── processed/                      # Delivery-level Parquet with pre-delivery pressure
│   └── analytical/                     # Precomputed rankings, match tables & validation Parquets
├── src/
│   ├── ingestion/load_data.py          # Source loader
│   ├── quality/                        # Phase 1 audit, cricket_rules.py, cricket_accounting.py
│   ├── pressure/                       # resource_model.py, first_innings_pressure.py, chase_pressure.py, win_probability.py, pressure_engine.py, calibration.py
│   ├── baselines/                      # expected_performance.py (5-fold match-grouped hierarchical EB)
│   ├── batting/batting_metrics.py      # Match & player batting aggregations
│   ├── bowling/bowling_metrics.py      # Match, player & phase bowling aggregations
│   ├── reliability/                    # uncertainty.py (cluster bootstrap), shrinkage.py, consistency.py
│   ├── ranking/                        # rankings.py, player_models.py
│   ├── validation/                     # cricket_checks.py, sensitivity.py, robustness.py
│   ├── reporting/                      # generate_methodology_report.py (PDF + Markdown + figures)
│   └── pipeline.py                     # Master pipeline orchestrator
├── components/                         # Reusable Streamlit UI components, cards, charts, drilldowns
├── dashboard/                          # 8 dashboard views (overview, pressure_engine, batting, bowling, reliability, rankings, evidence, methodology)
├── reports/
│   ├── methodology/                    # PHASE1_DATA_AUDIT.md, PRESSUREIQ_METHODOLOGY_REPORT.pdf/.md
│   ├── exports/                        # official_top10_batters.csv, official_top10_bowlers.csv, full_*.csv
│   └── figures/                        # High-resolution static evidence plots
└── tests/                              # 19 pytest unit & integration tests across 7 test modules
```

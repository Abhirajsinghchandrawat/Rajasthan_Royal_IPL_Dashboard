# PRESSUREIQ — Official Methodology & Validation Report

**Validation Status:** `VALIDATED` (23/23 automated gate checks passed)  
**Official Scope:** 837 IPL + T20I matches (837 active with ball-by-ball; 193,842 pressure-eligible deliveries)

## 1. Executive Summary
PRESSUREIQ is an end-to-end cricket pressure intelligence platform built to identify the most reliable batters and bowlers under genuine match pressure across IPL and T20 International cricket (2022–2026). Rather than equating death overs or high required run rates with pressure, PRESSUREIQ estimates pre-delivery difficulty and next-ball leverage from separate first-innings and run-chase models, evaluates players against 5-way cross-fitted context expectations, and ranks eligible players by their **Reliable Pressure Rating (RPR)** — the one-sided 90% Empirical-Bayes lower confidence bound on true context-adjusted contribution.

## 2. Problem Statement
Conventional leaderboards reward raw run volume or unadjusted bowling economy, conflating easy match states with crunch situations and allowing small-sample outliers to top rankings. The central analytical question solved here is: *Which players consistently deliver the greatest context-adjusted contribution when the pre-delivery match situation is difficult and the contest is still live?*

## 3. Dataset and Scope
- **Source Inventory:** `competitions.csv` (141), `teams.csv` (353), `matches.csv` (883), `ball_by_ball.csv` (200,999), `competition_team_player_mapping.csv` (6,413), `playing_eleven.csv` (28,381).
- **Official Competition Scope:** 371 IPL matches + 482 T20I matches = **853 matches** (194,014 deliveries). The 30 Other-T20 matches (Emerging Teams Asia Cup 2024 & Asia Cup Rising Stars 2025) are preserved in raw data and flagged `OUT_OF_OFFICIAL_SCOPE`.

## 4. Data Quality Audit
- Zero duplicate delivery keys `(match_id, innings, overid, over_ball_num)` and zero missing player/match IDs.
- 16 matches are `Match Abandoned` without ball-by-ball; 22 further matches lack second-innings deliveries (`No Result` / rain). None are silently deleted; all carry explicit audit flags in `data/interim/exclusion_flag_log.csv`.
- `playing_eleven.csv` contains 75 duplicate-key rows and IPL Impact Player substitutions (12+ `is_played=True`). Actual ball-by-ball appearance is used as the ground-truth participation table.

## 5. Cricket-Specific Data Processing
- **Runs & Extras (`src/quality/cricket_rules.py`):** `runs` is verified as off-the-bat batter runs. Team runs = `runs + extras1_runs + extras_2_runs` (reconciling 100% of unrevised 'won by N runs' margins).
- **`other` Extras Verification:** Row-level audit of all 264 `extras_type == 'other'` rows confirms `extras1_runs == 1` on 100% of rows, dominated by Beamer (116) and Full Toss (72) height no-balls. Treating `other` as legal creates 150 innings with >120 legal balls; classifying `other` as a no-ball reduces over-120-ball innings to **0**.
- **`extras_2_runs` Verification:** 35 rows occur on `Overstep`/`other` no-balls when `runs == 0` (plus 1 untagged row in match 17555), representing byes/leg-byes run off a no-ball. Credited to team runs, not debited to the bowler.
- **Dismissals:** `Caught`, `Bowled`, `LBW`, `Stump`, `Hit Wicket` credit the bowler. `RunOut` (600), `Retire Out` (6), and `Obstructing/Obstracting the field` (3) count as batting dismissals only. 12 rows with `dismissed_player_id` but `is_wicket=False` are tagging artefacts and not treated as wickets.
- **Super Overs & Revised Overs:** 38 Super Over deliveries (`innings in {3, 4}`) are excluded from regulation statistics. Revised-overs integers (`30..114`, all multiples of 6) are verified as legal-ball allocations.
- **Identity Collisions:** Basil Hameed's two IDs (`8638` and `39444`) remain unmerged per safeguard rules.

## 6. Pressure Definition & 7. Pressure Index Construction
- **Resource Model $E(u, w)$:** Exponential Duckworth–Lewis curves $Z_w(1 - e^{-b_w u})$ fitted on unrevised completed first innings, scaled by format ($\text{IPL}=1.035$, $\text{T20I}=0.972$). Out-of-sample chronological MAE is **17.11 runs** ($R^2 = 0.825$) vs **27.17 runs** ($R^2 = 0.408$) for naive current-run-rate projection.
- **Separate First-Innings & Chase WP Models:** 5-fold match-grouped cross-fitted logistic models predict $WP_{\text{bat}}$ from pre-delivery Par Deviation (Innings 1) or log Resource Ratio $\log(\text{runs\_needed}/E(u,w))$ (Innings 2). First-innings PI correlates negatively with current run rate ($r = -0.679$), proving high run rates are not conflated with pressure.
- **Frozen Pressure Index:** $\text{PI}_{\text{side}} = 100 \cdot \text{Difficulty}_{\text{side}} \cdot \min(1, L / \text{median}(L \mid \text{innings}))$.
- **Calibrated Thresholds:** Pooled batting PI quantiles (65th / 88th): **Elevated >= 52.0**, **High >= 66.1**.

## 8. Batting Performance Model & 9. Bowling Performance Model
- **Hierarchical Context Baselines:** 5-fold match-cross-fitted expectations over `format_group × innings × phase × wkts_bucket × pressure_level` with hierarchical empirical-Bayes smoothing ($k=100$).
- **Batting Value (CABV):** $(r - E[r \mid \text{ctx}]) - 0.30 \cdot WV \cdot (\text{out} - E[\text{out} \mid \text{ctx}])$, expressed per 100 pressure balls faced.
- **Bowling Value (RP):** $(E[c \mid \text{ctx}] - c) + 0.20 \cdot WV \cdot (\text{wkt} - E[\text{wkt} \mid \text{ctx}])$, expressed per 24 pressure deliveries.

## 10. Pressure Response Delta (PRD)
- $\text{PRD}_i = \hat{\theta}_{i,\text{pressure}} - \hat{\theta}_{i,\text{normal}}$ measures how a player's shrunk context-adjusted contribution changes under pressure relative to their own shrunk normal baseline. Reported independently from absolute pressure rating.

## 11. Reliability Framework, 12. Statistical Shrinkage & 13. Confidence Intervals
- **Match-Cluster Bootstrap:** 250 resamples of whole matches per player (`seed=42`) yield cluster-robust standard errors $SE_i$.
- **Volume-Weighted Empirical Bayes:** Population prior $(\mu, \tau^2)$ is estimated on the eligible cohort via ball-weighted method of moments. Posterior mean $\hat{\theta}_i = \mu + B_i(\bar{y}_i - \mu)$ with $B_i = \tau^2/(\tau^2 + SE_i^2)$ and posterior SD $SD_i = \sqrt{\tau^2 SE_i^2/(\tau^2 + SE_i^2)}$.
- **Ranking Estimand (RPR):** $\text{RPR}_i = \hat{\theta}_i - 1.2816 \cdot SD_i$ (one-sided 90% lower confidence bound).

## 14. Eligibility Rules
- **Batters:** $\ge 10$ unique pressure matches and $\ge 100$ pressure balls faced (**177 eligible batters**).
- **Bowlers:** $\ge 10$ unique pressure matches and $\ge 120$ pressure legal balls bowled (**162 eligible bowlers**).

## 15. Final Batting Top 10 (Official IPL + T20I Scope)

|   rank |   player_id | player_name      | teams                              | formats    |   rpr |   rating_mean |    prd |   p_balls |   p_matches |   p_sr |   p_exp_sr |   success_rate |
|-------:|------------:|:-----------------|:-----------------------------------|:-----------|------:|--------------:|-------:|----------:|------------:|-------:|-----------:|---------------:|
|      1 |        6819 | Yashasvi Jaiswal | Rajasthan Royals, India            | IPL + T20I | 15.73 |         24.65 |  20.56 |       397 |          55 | 179.6  |     139.19 |           0.67 |
|      2 |        6396 | Tim David        | Mumbai Indians, Australia          | IPL + T20I | 13.48 |         23.22 |   0.71 |       455 |          46 | 180.88 |     137.18 |           0.57 |
|      3 |        1699 | Suryakumar Yadav | Mumbai Indians, India              | IPL + T20I | 11.55 |         19.11 |  -7.57 |       857 |          69 | 156.83 |     132.99 |           0.65 |
|      4 |        6281 | Abhishek Sharma  | Sunrisers Hyderabad, India         | IPL + T20I |  8.94 |         18.06 | -18.62 |       630 |          76 | 171.27 |     136.32 |           0.55 |
|      5 |        4260 | Heinrich Klaasen | Sunrisers Hyderabad, South Africa  | IPL + T20I |  8.91 |         16.98 |  -4.23 |       452 |          38 | 154.42 |     135.93 |           0.61 |
|      6 |        5039 | Rajat Patidar    | Royal Challengers Bengaluru        | IPL        |  8.86 |         17.95 |   0.01 |       326 |          23 | 155.21 |     131.07 |           0.65 |
|      7 |        1318 | Andre Russell    | Kolkata Knight Riders, West Indies | IPL + T20I |  8.07 |         17.94 |   0.03 |       318 |          32 | 172.01 |     138.14 |           0.59 |
|      8 |        6931 | Pathum Nissanka  | Sri Lanka, Delhi Capitals          | IPL + T20I |  6.57 |         15.69 |  18.75 |       406 |          34 | 153.2  |     132.84 |           0.59 |
|      9 |        6423 | Riyan Parag      | Rajasthan Royals, India            | IPL + T20I |  6.43 |         14.51 |  16.14 |       483 |          38 | 154.24 |     137.78 |           0.61 |
|     10 |        4736 | Josh Inglis      | Australia, Punjab Kings            | IPL + T20I |  5.78 |         15.87 |   3.17 |       241 |          26 | 163.49 |     130.5  |           0.65 |

## 16. Final Bowling Top 10 (Official IPL + T20I Scope)

|   rank |   player_id | player_name         | teams                                 | formats    |   rpr |   rating_mean |   prd |   p_legal |   p_matches |   p_economy |   p_exp_economy |   p_wickets |   success_rate |
|-------:|------------:|:--------------------|:--------------------------------------|:-----------|------:|--------------:|------:|----------:|------------:|------------:|----------------:|------------:|---------------:|
|      1 |        2933 | Jasprit Bumrah      | Mumbai Indians, India                 | IPL + T20I |  1.13 |          2.65 | -2.35 |       641 |          52 |        7.82 |            9.57 |          20 |           0.77 |
|      2 |         781 | Sunil Narine        | Kolkata Knight Riders                 | IPL        |  0.82 |          2.43 | -2.83 |       503 |          41 |        7.31 |            9.06 |          18 |           0.68 |
|      3 |         305 | Ravichandran Ashwin | Rajasthan Royals, Chennai Super Kings | IPL + T20I |  0.62 |          2.07 |  0.15 |       478 |          36 |        7.91 |            9.08 |          16 |           0.69 |
|      4 |        4373 | Mustafizur Rahman   | Bangladesh, Delhi Capitals            | IPL + T20I |  0.5  |          1.84 | -1.21 |       555 |          48 |        8.45 |            9.45 |          18 |           0.6  |
|      5 |        2876 | Axar Patel          | India, Delhi Capitals                 | IPL + T20I |  0.46 |          1.86 |  1.55 |       823 |          75 |        7.84 |            8.74 |          38 |           0.65 |
|      6 |        4874 | Richard Ngarava     | Zimbabwe                              | T20I       |  0.27 |          1.77 |  1.62 |       422 |          33 |        7.72 |            8.77 |          22 |           0.61 |
|      7 |         278 | Tim Southee         | New Zealand, Kolkata Knight Riders    | IPL + T20I |  0.23 |          1.9  |  2.31 |       312 |          25 |        7.44 |            8.76 |          21 |           0.72 |
|      8 |       19316 | Maheesh Theekshana  | Sri Lanka, Chennai Super Kings        | IPL + T20I |  0.23 |          1.58 | -0.53 |       826 |          70 |        7.99 |            8.81 |          34 |           0.63 |
|      9 |        4722 | Rashid Khan         | Gujarat Titans, Afghanistan           | IPL + T20I |  0.21 |          1.7  | -1.84 |       718 |          61 |        7.96 |            8.85 |          34 |           0.67 |
|     10 |        7364 | Haris Rauf          | Pakistan                              | T20I       |  0.13 |          1.66 |  3.41 |       459 |          39 |        8.37 |            9.2  |          32 |           0.72 |

## 17. Evidence & Player Comparisons, 18. Sensitivity Analysis & 19. Model Validation
### Out-of-Sample Win-Probability Validation
| model        | test                                |     n |   brier |   brier_constant |   logloss |   logloss_constant |
|:-------------|:------------------------------------|------:|--------:|-----------------:|----------:|-------------------:|
| WP innings 1 | cross-fitted (match-grouped 5-fold) | 99445 |  0.2219 |           0.25   |    0.6341 |             0.6931 |
| WP innings 1 | chronological (train < 2025-01-01)  | 39575 |  0.2293 |           0.2517 |    0.6528 |             0.6965 |
| WP innings 2 | cross-fitted (match-grouped 5-fold) | 90948 |  0.1271 |           0.2496 |    0.3926 |             0.6924 |
| WP innings 2 | chronological (train < 2025-01-01)  | 35830 |  0.1224 |           0.2524 |    0.3786 |             0.6979 |

### Chronological First-Innings Resource Model Validation
| model                     | test                               |     n |   mae_runs |   bias_runs |     r2 |
|:--------------------------|:-----------------------------------|------:|-----------:|------------:|-------:|
| Resource model E(u,w)     | chronological (train < 2025-01-01) | 39673 |    17.1114 |      2.0808 | 0.8249 |
| Naive run-rate projection | chronological (train < 2025-01-01) | 39673 |    27.1738 |      9.4242 | 0.4079 |

### Chronological Expected-Performance Baseline Validation
| target                        |   n_test |   mse_context |   mse_format_only |   mse_global |   mean_obs |   mean_pred |   skill_vs_global_pct |
|:------------------------------|---------:|--------------:|------------------:|-------------:|-----------:|------------:|----------------------:|
| Batter Runs per Ball          |    74200 |        3.1715 |            3.1939 |       3.1998 |     1.4476 |      1.365  |                0.8844 |
| Batter Dismissal per Ball     |    74200 |        0.0519 |            0.0522 |       0.0522 |     0.0553 |      0.0543 |                0.4989 |
| Bowler Runs Conceded per Ball |    77252 |        3.077  |            3.0973 |       3.1026 |     1.4416 |      1.3659 |                0.8239 |
| Bowler Wicket per Ball        |    77252 |        0.0489 |            0.049  |       0.049  |     0.0517 |      0.0508 |                0.3641 |

### Sensitivity Analysis Across 13 Alternative Specifications
| scenario                              | kind    |   top10_overlap |   spearman |   n_common_eligible |   n_eligible |
|:--------------------------------------|:--------|----------------:|-----------:|--------------------:|-------------:|
| Thresholds -10                        | batting |               8 |      0.869 |                 177 |          210 |
| Thresholds -10                        | bowling |               5 |      0.845 |                 162 |          198 |
| Thresholds -5                         | batting |               6 |      0.939 |                 177 |          191 |
| Thresholds -5                         | bowling |               8 |      0.91  |                 162 |          187 |
| Thresholds +5                         | batting |               7 |      0.896 |                 143 |          143 |
| Thresholds +5                         | bowling |               5 |      0.896 |                 126 |          126 |
| Thresholds +10                        | batting |               5 |      0.756 |                 107 |          107 |
| Thresholds +10                        | bowling |               5 |      0.794 |                  88 |           88 |
| High-only pressure                    | batting |               5 |      0.707 |                  67 |           67 |
| High-only pressure                    | bowling |               4 |      0.675 |                  58 |           58 |
| Difficulty-only PI                    | batting |               8 |      0.893 |                 177 |          216 |
| Difficulty-only PI                    | bowling |               5 |      0.89  |                 162 |          187 |
| Geometric-rank PI                     | batting |               7 |      0.842 |                 176 |          194 |
| Geometric-rank PI                     | bowling |               6 |      0.816 |                 161 |          183 |
| Ranking z=0.0                         | batting |               9 |      0.972 |                 177 |          177 |
| Ranking z=0.0                         | bowling |               9 |      0.989 |                 162 |          162 |
| Ranking z=1.645                       | batting |               9 |      0.998 |                 177 |          177 |
| Ranking z=1.645                       | bowling |              10 |      0.999 |                 162 |          162 |
| Eligibility >= 6 matches / 42 balls   | batting |               8 |      0.998 |                 177 |          264 |
| Eligibility >= 6 matches / 50 balls   | bowling |               9 |      1     |                 162 |          242 |
| Eligibility >= 8 matches / 60 balls   | batting |               9 |      0.999 |                 177 |          213 |
| Eligibility >= 8 matches / 72 balls   | bowling |              10 |      1     |                 162 |          203 |
| Eligibility >= 10 matches / 100 balls | batting |              10 |      1     |                 177 |          177 |
| Eligibility >= 10 matches / 120 balls | bowling |              10 |      1     |                 162 |          162 |
| Eligibility >= 12 matches / 150 balls | batting |              10 |      0.998 |                 135 |          135 |
| Eligibility >= 12 matches / 180 balls | bowling |              10 |      0.999 |                 119 |          119 |
| Eligibility >= 15 matches / 200 balls | batting |              10 |      0.996 |                 111 |          111 |
| Eligibility >= 15 matches / 240 balls | bowling |              10 |      0.997 |                  90 |           90 |

### 23-Check Automated Validation Gate
| check                                                                                | value     | pass   |
|:-------------------------------------------------------------------------------------|:----------|:-------|
| No innings exceeds its legal-ball allocation                                         | 0         | True   |
| Team total (runs+extras1+extras2) reproduces 'won by N runs' margins (unrevised)     | 1.0       | True   |
| No Super Over deliveries in pressure set                                             | 0         | True   |
| No out-of-scope (Other T20) deliveries in pressure set                               | 0         | True   |
| Pressure Index defined and within [0,100] on every eligible delivery                 | 0         | True   |
| Byes/leg-byes/penalties never charged to bowler                                      | 0.0       | True   |
| Non-bowler dismissals never credited to bowler                                       | 0         | True   |
| Wides never counted as balls faced                                                   | 0         | True   |
| WP innings 1 beats constant (cross-fitted (match-grouped 5-fold)) on Brier           | 0.2219    | True   |
| WP innings 1 beats constant (chronological (train < 2025-01-01)) on Brier            | 0.2293    | True   |
| WP innings 2 beats constant (cross-fitted (match-grouped 5-fold)) on Brier           | 0.1271    | True   |
| WP innings 2 beats constant (chronological (train < 2025-01-01)) on Brier            | 0.1224    | True   |
| First-innings resource/par model beats naive run-rate projection (chronological MAE) | 17.11     | True   |
| Baseline 'Batter Runs per Ball' beats global mean on later unseen matches            | 0.88      | True   |
| Baseline 'Batter Dismissal per Ball' beats global mean on later unseen matches       | 0.5       | True   |
| Baseline 'Bowler Runs Conceded per Ball' beats global mean on later unseen matches   | 0.82      | True   |
| Baseline 'Bowler Wicket per Ball' beats global mean on later unseen matches          | 0.36      | True   |
| First-innings PI not positively correlated with current run rate                     | -0.731    | True   |
| Pressure share non-degenerate in every innings x phase cell (5%-85%)                 | 0.25-0.44 | True   |
| bat_rank: top 10 complete, unique and all eligible                                   | 10        | True   |
| bat_rank: top 10 ordered by RPR                                                      |           | True   |
| bowl_rank: top 10 complete, unique and all eligible                                  | 10        | True   |
| bowl_rank: top 10 ordered by RPR                                                     |           | True   |

## 20. Assumptions & 21. Limitations
- Marginal wicket value above replacement is set to $0.30 	imes WV$ for batting and $0.20 	imes WV$ for bowling so binary single-ball dismissal variance does not swamp run-scoring/saving signal; pure run-only ($0.0 	imes WV$) and full resource drop ($1.0 	imes WV$) were verified during diagnostics.
- Two DLS chases without `revised_target` are flagged `target_unreliable` and excluded from chase pressure scoring.
- Basil Hameed's two IDs (`8638` and `39444`) are kept unmerged because no external biographical key is supplied.

## 22. Reproducibility Instructions
```bash
pip install -r requirements.txt
python -m src.pipeline
python -m pytest tests/ -v
streamlit run app.py
```
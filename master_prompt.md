# MASTER PROJECT SPECIFICATION
# PRESSUREIQ — Cricket Pressure Performance Intelligence Platform

## ROLE & EXPECTED LEVEL OF EXECUTION

Act as a multidisciplinary team consisting of:

1. A senior cricket data scientist specialising in T20 and IPL analytics.
2. A top-tier sports performance analyst.
3. A senior data analyst and statistician.
4. A data engineer experienced in ball-by-ball cricket datasets.
5. A senior Python and Streamlit developer.
6. A product manager specialising in analytical products.
7. A senior UI/UX designer specialising in enterprise dashboards.
8. A statistical model validation specialist.

Your task is to design, engineer, validate and deliver a professional cricket analytics platform called PRESSUREIQ.

Do not behave like a generic dashboard generator.

Think like a professional cricket analytics organisation building a decision-support product that must withstand scrutiny from experienced cricket analysts, statisticians, data scientists and product evaluators.

Every analytical decision must have:
- A cricketing justification.
- A statistical justification.
- A clearly documented formula or rule.
- A reproducible implementation.
- A validation mechanism.
- An understandable user-facing explanation.

Do not optimise for visual attractiveness at the expense of analytical correctness.

Do not optimise for complicated mathematics at the expense of interpretability.

The final product must be analytically defensible, visually sophisticated, interactive, explainable and reproducible.

---

# 1. PROJECT OBJECTIVE

Original problem:

Identify the most reliable players under pressure.

The challenge requires two independent ordered rankings:

A. Top 10 batters who perform most reliably under pressure.

B. Top 10 bowlers who perform most reliably under pressure.

The dataset covers historical IPL and T20 International cricket from 2022 onwards.

The platform must identify high-pressure match situations, calculate pressure-adjusted player performance, compare it with normal performance, estimate consistency and uncertainty, and produce defensible player rankings.

The central question is:

"Which players consistently deliver the greatest context-adjusted contribution when the match situation becomes difficult?"

This is NOT a conventional batting-average or bowling-economy leaderboard.

A player with excellent overall statistics should not automatically receive a high pressure rating.

A player with a small number of extraordinary performances should not automatically be considered reliable.

The ranking must emerge from actual supplied data.

---

# 2. PRODUCT VISION

Product name: PRESSUREIQ

Tagline:

"The science of performing when it matters."

Product category:
Interactive cricket performance intelligence and decision-support platform.

Target users:
- Cricket analysts.
- Sports data scientists.
- Coaches and team strategists.
- Cricket enthusiasts.
- Competition evaluators.

The platform should allow a user to:

1. Understand how pressure is defined.
2. Explore the distribution of pressure situations.
3. Examine batting performance under pressure.
4. Examine bowling performance under pressure.
5. Understand the difference between performance and reliability.
6. Explore the final top-10 rankings.
7. Compare individual players.
8. Inspect the evidence behind rankings.
9. Understand statistical uncertainty.
10. Reproduce the analytical methodology.

The product should feel like a professional sports intelligence platform rather than a generic academic dashboard.

---

# 3. DATASET AND SOURCE OF TRUTH

The supplied dataset contains these six primary CSV files:

- competitions.csv
- teams.csv
- matches.csv
- ball_by_ball.csv
- competition_team_player_mapping.csv
- playing_eleven.csv

The ZIP also contains the original problem-statement PDF and operating-system metadata files.

Dataset inventory verified from the supplied files:

| File | Records |
|---|---:|
| competitions.csv | 141 |
| teams.csv | 353 |
| matches.csv | 883 |
| ball_by_ball.csv | 200,999 |
| competition_team_player_mapping.csv | 6,413 |
| playing_eleven.csv | 28,381 |

Observed date coverage:
22 January 2022 – 1 November 2026.

Competition inventory:

- IPL: 371 matches.
- Other T20 competitions: 30 matches.
- T20I: 482 matches.

Official intended analysis scope:

IPL + T20I only.

Expected in-scope match count:
853.

Expected in-scope ball-by-ball record count:
194,014 before delivery-level exclusions and validation.

These are initial inventory figures, not guaranteed final analytical denominators. Recalculate and document all figures from the source data.

The source ZIP may not automatically be accessible to the coding environment. If necessary, place it in:

data/raw/data_pack.zip

Extract the original CSVs into:

data/raw/

Never overwrite or modify original files.

Create processed data separately.

## 3.1 Schema reference

### competitions.csv
- comp_id
- comp_name
- match_format
- season

### teams.csv
- comp_id
- team_id
- team_name

### matches.csv
- match_id
- comp_id
- match_number
- match_date
- stage
- venue_id
- venue_country
- home_team_id
- home_team
- away_team_id
- away_team
- home_team_captain_id
- away_team_captain_id
- toss_win_team_id
- toss_opted
- man_of_the_match
- first_inn_revised_overs
- second_inn_revised_overs
- revised_target
- knock_out
- win_team_id
- result

### ball_by_ball.csv
- match_id
- innings
- overid
- over_ball_num
- innings_ball_num
- batting_team_id
- bowling_team_id
- striker_id
- striker_name
- non_striker_id
- non_striker_name
- bowler_id
- bowler_name
- batting_type
- bowling_type
- batting_order
- runs
- is_four
- is_six
- is_wicket
- dismissal_type_id
- dismissal_type
- dismissed_player_id
- extras_type
- extras1_runs
- extras_2_runs
- pace_or_spin
- bowl_speed
- stroke
- delivery_style
- over_or_around
- on_or_off
- delivery_ist_time

### competition_team_player_mapping.csv
- comp_id
- comp_name
- team_id
- team_name
- player_id
- player_name

### playing_eleven.csv
- match_id
- team_id
- player_id
- batting_order
- is_played
- is_captain
- is_wk
- is_impact
- is_impact_off

Use player IDs as the primary player identifier, not player names.

Use match IDs as the primary match identifier.

Never infer identity from names alone when IDs are available.

---

# 4. MANDATORY DATA ENGINEERING AND VALIDATION

Do not begin player modelling until the data audit is complete.

Build a reproducible data validation pipeline.

## 4.1 Validate relationships

Validate:

- Competition IDs across competitions and matches.
- Team IDs across competitions, teams and matches.
- Match IDs across matches, deliveries and playing XI.
- Player IDs across deliveries, mappings and playing XI.
- Batting team and bowling team relationships.
- Player-team participation consistency.

Create a documented relational model.

## 4.2 Data quality checks

Test:

- Duplicate delivery records.
- Duplicate match records.
- Duplicate player-match-team records in playing XI.
- Missing identifiers.
- Invalid innings numbers.
- Invalid over and ball numbering.
- Negative run values.
- Invalid extras.
- Dismissal inconsistencies.
- Boundary indicator inconsistencies.
- Missing player mappings.
- Matches without ball-by-ball records.
- Matches with incomplete innings.
- Unexpected innings counts.
- Invalid revised-overs values.
- Revised-target inconsistencies.

Produce a data-quality report with:
- Total records.
- Valid records.
- Invalid records.
- Missing values.
- Duplicate records.
- Excluded records.
- Exclusion reasons.

Do not silently delete questionable records.

Create explicit exclusion flags and an audit log.

## 4.3 Cricket-specific data validation

This is critical.

Inspect and establish the actual meanings of:

- runs
- extras1_runs
- extras_2_runs
- extras_type
- is_wicket
- dismissal_type
- dismissed_player_id
- innings_ball_num
- overid
- over_ball_num

Do not assume that runs represents batter runs, total team runs or bowler-conceded runs until reconciled.

Reconcile sample innings totals against match-level information wherever possible.

Build separate variables for:

1. Batter runs.
2. Total team runs.
3. Bowler-conceded runs.
4. Legal deliveries.
5. Batter balls faced.
6. Bowler legal balls.
7. Bowler-credited wickets.
8. Total dismissals.

Check the provider's delivery conventions before implementing these.

## 4.4 Extras handling

Implement explicit rules for:

- Wides.
- No-balls / oversteps.
- Byes.
- Leg-byes.
- Penalty runs.
- Other extras.

Standard cricket accounting must be respected.

In general:
- Wides and no-balls affect bowler-conceded runs.
- Byes and leg-byes do not count against the bowler's economy.
- Wides and no-balls are not legal deliveries.
- Byes and leg-byes are legal deliveries unless the source convention indicates otherwise.
- Batter runs must be separated from extras.
- Verify the exact handling of no-ball batter runs and related extras.

Do not count an illegal delivery as a legal ball.

## 4.5 Dismissal handling

Differentiate:

- Bowler-credited dismissals.
- Run-outs.
- Obstructing the field.
- Retired out.
- Other non-bowler dismissals.

Do not award a wicket to the bowler for a dismissal that is not credited to the bowler under cricket scoring rules.

Retired-out and unusual dismissal categories must be documented separately.

## 4.6 Super Overs

There are six matches containing Super Overs in the supplied data.

Keep Super Over innings separate from regulation innings.

Do not allow Super Over deliveries to distort normal T20 batting averages, bowling economy or pressure rankings.

Analyse them separately only if a defensible and useful treatment is possible.

## 4.7 Revised matches

There are 34 matches with revised-overs information and 23 matches with a revised target in the initial inventory.

Inspect these individually.

Do not assume revised-overs values are decimal overs.

Establish the source encoding and reconstruct the effective match rules.

For revised-target chases:
- Use the applicable target.
- Use the applicable innings allocation.
- Correctly calculate remaining balls.
- Do not use the original target when it has been superseded.

Flag matches where the target or remaining resources cannot be reliably reconstructed.

## 4.8 Playing XI

The playing_eleven file contains duplicate player-match-team keys and non-playing entries.

Resolve participation carefully.

Distinguish:
- Selected players.
- Actual playing players.
- Impact substitutes.
- Non-playing squad members.

Do not assume that inclusion in playing_eleven automatically means the player participated.

Use actual ball-by-ball participation as the primary evidence of batting or bowling opportunities.

Document how impact players are treated.

---

# 5. PRESSURE ENGINE

The pressure engine is the foundation of the entire platform.

Do not define pressure simply as overs 16–20.

Do not define pressure using required run rate alone.

Do not use the outcome of a delivery to determine the pressure of that same delivery.

Pressure must be calculated using information available immediately BEFORE the delivery.

Build a Pressure Index between 0 and 100.

## 5.1 Pressure dimensions

### Second innings: chase pressure

Consider:

- Runs remaining.
- Legal balls remaining.
- Required run rate.
- Wickets remaining.
- Current run rate.
- Required run rate relative to expected scoring conditions.
- Revised target.
- Innings stage.
- Remaining batting resources.

### First innings: scoring and resource pressure

Consider:

- Overs remaining.
- Wickets remaining.
- Current scoring rate.
- Expected par score at the current stage.
- Difference between current score and expected par.
- Expected scoring resources.
- Remaining wickets and overs.

Do not incorrectly assume that a high current run rate means pressure is high.

First-innings pressure needs its own empirical model.

## 5.2 Pressure modelling

Investigate a transparent, data-supported combination of:

- Required scoring difficulty.
- Wicket-resource scarcity.
- Remaining time/resources.
- Expected scoring opportunities.
- Match-state deviation.

Use historical data to estimate expected scoring conditions.

Where appropriate, use:
- Historical phase-level scoring baselines.
- Wicket-state baselines.
- Chase-state baselines.
- Empirical expected runs from comparable situations.

Avoid arbitrary weights.

Prefer a calibrated model whose outputs can be explained.

If a composite formula is used, document:
- Every component.
- Normalisation method.
- Weight selection.
- Calibration.
- Validation.
- Limitations.

Do not present an unvalidated heuristic as a scientifically established pressure probability.

## 5.3 Pressure classifications

Create three classifications:

- Low Pressure.
- Elevated Pressure.
- High Pressure.

Select thresholds using a defensible calibration procedure.

Freeze the thresholds before final ranking analysis.

Run sensitivity checks using reasonable alternative thresholds.

## 5.4 Bowling pressure interpretation

The bowling model must recognise the defensive context.

A bowler defending a small total and a bowler defending a large total do not face equivalent situations.

Use the batting-side match state and the defensive difficulty to contextualise the bowling contribution.

Avoid assuming every high-pressure batting delivery is automatically equally difficult for the bowler.

Where the data cannot support a meaningful distinction, state the limitation.

---

# 6. BATTING PERFORMANCE MODEL

Develop a separate batting performance model.

Evaluate each batter's contribution on qualifying pressure deliveries.

## Core batting KPIs

1. Pressure Runs.
2. Pressure Strike Rate.
3. Pressure Dot Ball Percentage.
4. Pressure Boundary Percentage.
5. Pressure Dismissal Rate.
6. Context-Adjusted Batting Value.
7. Pressure Opportunity Count.
8. Number of Unique Pressure Matches.

### Definitions

Pressure Strike Rate:

(Batter Runs / Batter Balls Faced) × 100.

Pressure Dot Ball Percentage:

(Dot Balls / Batter Balls Faced) × 100.

Pressure Boundary Percentage:

(Boundary-scoring balls / Batter Balls Faced) × 100.

Pressure Dismissal Rate:

(Batter dismissals / Batter Balls Faced) × 100.

Define the denominator consistently and document treatment of deliveries on which the striker does not face a ball under the applicable scoring rules.

## 6.1 Context-adjusted batting value

This is more important than raw strike rate.

Estimate the expected batting contribution using comparable conditions:

- Format.
- Innings phase.
- Wickets remaining.
- Match situation.
- Pressure level.
- Other available pre-delivery context.

Calculate the difference between observed and expected contribution.

A possible implementation is:

Context-Adjusted Batting Value =
Actual Batter Runs - Expected Batter Runs.

However, the expected-run model must be appropriate to the scoring opportunity and must not use future delivery information.

Investigate an empirical baseline or a properly validated predictive model.

Do not compare players using raw runs alone.

## 6.2 Batter baselines

Compare pressure performance with normal performance.

Control for:
- Innings phase.
- Format.
- Wickets remaining.
- Match context.
- Relevant batting opportunities.

Avoid comparing pressure death-over performance directly with normal powerplay performance without adjustment.

---

# 7. BOWLING PERFORMANCE MODEL

Develop a separate bowling performance model.

## Core bowling KPIs

1. Pressure Economy.
2. Pressure Wicket Rate.
3. Pressure Dot Ball Percentage.
4. Boundary Conceded Percentage.
5. Context-Adjusted Runs Prevented.
6. Pressure Legal Balls.
7. Number of Unique Pressure Matches.

### Definitions

Pressure Economy:

(Bowler-Conceded Runs / Legal Balls Bowled) × 6.

Pressure Wicket Rate:

(Bowler-Credited Wickets / Legal Balls Bowled) × 100.

Pressure Dot Ball Percentage:

(Dot Deliveries / Bowling Opportunities) × 100.

Boundary Conceded Percentage:

(Boundaries Conceded / Eligible Bowling Deliveries) × 100.

Validate all delivery and extras conventions before implementation.

## 7.1 Context-adjusted runs prevented

Calculate:

Expected Runs Conceded - Actual Bowler-Conceded Runs.

Positive values represent better-than-expected bowling.

Estimate expected runs based on:
- Innings phase.
- Match format.
- Wickets remaining.
- Scoring environment.
- Match state.
- Relevant pressure context.

Do not reward a bowler merely because their team defended a large total.

## 7.2 Bowler baselines

Compare performance under pressure with normal performance.

Control for:
- Bowling phase.
- Format.
- Match state.
- Expected scoring environment.
- Relevant bowling opportunities.

Account for powerplay, middle-over and death-over role differences.

---

# 8. SIGNATURE METRIC: PRESSURE RESPONSE DELTA

Create a signature metric called:

PRESSURE RESPONSE DELTA (PRD).

It measures how a player's context-adjusted performance changes under pressure compared with their own normal-performance baseline.

Formula:

PRD = Adjusted Pressure Performance - Adjusted Normal Performance.

For batting:
Use context-adjusted batting contribution.

For bowling:
Use context-adjusted runs prevented, with consistent positive-value direction.

Interpretation:

- Positive PRD: player improves under pressure.
- Zero PRD: player maintains their normal performance.
- Negative PRD: player deteriorates under pressure.

This metric must be shown independently from absolute pressure performance.

A player with a high PRD may still have a lower absolute pressure contribution than a player with a slightly negative PRD.

Never confuse:
- Best pressure performer.
- Most improved under pressure.
- Most consistent performer.

These are distinct analytical questions.

---

# 9. RELIABILITY AND STATISTICAL CONFIDENCE

This section is a major differentiator.

Do not rank players using small samples without accounting for uncertainty.

Build a reliability framework containing:

1. Context-adjusted pressure contribution.
2. Match-to-match consistency.
3. Pressure Response Delta.
4. Pressure opportunities.
5. Independent match count.
6. Statistical uncertainty.
7. Season stability.

## 9.1 Sample-size handling

Distinguish:
- Delivery count.
- Batting opportunities.
- Bowling opportunities.
- Unique matches.
- Unique seasons.

Repeated deliveries from one match are not independent match observations.

Use match-level aggregation for consistency and uncertainty estimation where appropriate.

## 9.2 Statistical shrinkage

Investigate an appropriate empirical Bayes or hierarchical shrinkage method.

Players with small samples should be pulled towards an appropriate population baseline.

The shrinkage model must:
- Be appropriate to the metric.
- Have a documented prior or population baseline.
- Be reproducible.
- Be validated.
- Avoid creating artificial certainty.

## 9.3 Confidence intervals

Use a defensible uncertainty-estimation method.

A match-cluster bootstrap is a preferred candidate because deliveries within a match are not independent.

Document:
- Resampling unit.
- Number of bootstrap iterations.
- Confidence level.
- Treatment of small samples.
- Reproducibility seed.

Do not display fabricated confidence values.

## 9.4 Consistency metrics

Investigate:
- Match-level adjusted performance variance.
- Median match contribution.
- Interquartile range.
- Percentage of matches above the defined benchmark.
- Season-to-season stability.

Do not use raw standard deviation alone because players with different opportunity volumes and means are not directly comparable.

## 9.5 Eligibility

Set minimum eligibility requirements for batters and bowlers.

The thresholds must be determined using data coverage, cricketing relevance and sensitivity testing.

Do not choose thresholds after looking at which players they help.

Report excluded players and reasons.

A player without sufficient evidence should be labelled insufficient sample rather than poor performer.

---

# 10. FINAL RANKING FRAMEWORK

Produce two independent ordered top-10 lists.

A. Batters.

B. Bowlers.

Ranking must be based on a predefined, transparent, reliability-adjusted and context-adjusted performance estimator.

Do not use reputation, popularity, career achievements or subjective opinions.

Do not manually promote famous players.

Do not simply average strike rate, economy, wickets and confidence into an arbitrary composite.

Use statistical shrinkage and uncertainty-aware estimates to distinguish observed performance from estimated true contribution.

Keep these metrics separately visible:
- Estimated pressure contribution.
- PRD.
- Consistency.
- Sample volume.
- Confidence interval.

Define the final ranking estimand before generating the leaderboard.

If there are insufficient eligible players for a complete top 10 in either category, report the limitation instead of inventing entries.

Official rankings must use the complete IPL + T20I scope.

Exploratory filtered rankings must be clearly distinguished from official rankings.

The two official lists must not contain repeated players within their own category.

---

# 11. FORMAT AND COMPETITION FAIRNESS

The official scope is:

- IPL.
- T20I.
- 2022 onwards.

Other T20 competitions are excluded from official rankings unless the competition rules explicitly permit them.

Build:
- IPL-only comparison.
- T20I-only comparison.
- Combined IPL + T20I ranking.

Investigate format effects and player performance differences across formats.

Do not assume IPL and T20I scoring environments are identical.

Use appropriate format-aware baselines.

A player appearing in both competitions should be identifiable through one player ID.

Do not duplicate the same player because they appear for different teams or competitions.

---

# 12. DASHBOARD ARCHITECTURE

Build one interactive Streamlit application with:

ONE EXECUTIVE OVERVIEW + SEVEN ANALYTICAL SECTIONS.

Navigation should be persistent and easy to understand.

## SECTION 00 — EXECUTIVE OVERVIEW

Purpose:
Explain the project and communicate the most important findings immediately.

Top KPI cards:

1. Matches Analysed.
2. Deliveries Analysed.
3. Pressure Deliveries.
4. Pressure Delivery Share.
5. Eligible Batters.
6. Eligible Bowlers.

Include:

- Top three batters.
- Top three bowlers.
- Pressure distribution.
- IPL vs T20I coverage.
- Pressure intensity distribution.
- Most important evidence-backed discovery.
- Model coverage and data completeness.

Charts:
- KPI cards.
- Horizontal leaderboard.
- Pressure distribution.
- IPL/T20I comparison.
- Small-multiple phase charts.

Do not show unpopulated or invented results.

## SECTION 01 — PRESSURE ENGINE

Purpose:
Explain what pressure means and how it is measured.

KPIs:
- Pressure Index.
- Pressure Exposure.
- High Pressure Share.
- Chase Difficulty.
- Wicket Resource Pressure.
- Innings Resource Pressure.

Visualisations:
1. Pressure Situation Heatmap.
2. Required Run Rate vs Wickets Remaining Heatmap.
3. Pressure Score Distribution.
4. Pressure by Innings Phase.
5. IPL vs T20I pressure comparison.

Include:
- Pressure formula.
- Component explanations.
- Classification thresholds.
- Example match situations.
- Pre-delivery calculation explanation.
- Sensitivity analysis.

## SECTION 02 — BATTING INTELLIGENCE

KPIs:
- Pressure Runs.
- Pressure Strike Rate.
- Pressure Dot Ball %.
- Pressure Boundary %.
- Pressure Dismissal Rate.
- Context-Adjusted Batting Value.
- Pressure Response Delta.

Visualisations:
1. Batter Performance Matrix.
2. Normal vs Pressure Dumbbell Chart.
3. Pressure Strike Rate Distribution.
4. Context-Adjusted Contribution Leaderboard.
5. Batter Match-Level Performance Distribution.

Player-level drill-down:
- Name and ID.
- Matches played.
- Pressure opportunities.
- Pressure runs.
- Pressure strike rate.
- Dot ball rate.
- Dismissal rate.
- Expected contribution.
- Adjusted contribution.
- PRD.
- Confidence interval.
- Season performance.
- IPL/T20I breakdown.

## SECTION 03 — BOWLING INTELLIGENCE

KPIs:
- Pressure Economy.
- Pressure Wicket Rate.
- Pressure Dot Ball %.
- Boundary Conceded %.
- Context-Adjusted Runs Prevented.
- Pressure Response Delta.

Visualisations:
1. Bowling Effectiveness Matrix.
2. Bowling Phase Heatmap.
3. Runs Prevented Leaderboard.
4. Normal vs Pressure Comparison.
5. Match-Level Bowling Distribution.

Player drill-down:
- Matches bowled.
- Legal balls.
- Pressure legal balls.
- Pressure economy.
- Pressure wickets.
- Wicket rate.
- Dot ball rate.
- Boundary conceded rate.
- Expected runs.
- Actual runs.
- Runs prevented.
- PRD.
- Confidence interval.
- Season and format breakdown.

## SECTION 04 — RELIABILITY LAB

Purpose:
Distinguish exceptional performances from repeatable performance.

KPIs:
- Pressure Response Delta.
- Match-to-Match Consistency.
- Pressure Success Rate.
- Unique Pressure Matches.
- Pressure Opportunities.
- Confidence Interval.
- Season Stability.

Visualisations:
1. Performance vs Reliability Quadrant.
2. Confidence Interval Forest Plot.
3. Match-Level Box Plots.
4. Season Stability Line Chart.
5. Sample Size vs Performance Scatter Plot.

Player classifications:
- High performance / high reliability.
- High performance / low reliability.
- Low performance / high reliability.
- Low performance / low reliability.

Do not create misleading quadrants without documenting their thresholds.

## SECTION 05 — PLAYER RANKINGS

Display two separate leaderboards.

Batting Top 10.

Bowling Top 10.

Columns:
- Rank.
- Player.
- Team / competition context.
- Adjusted Pressure Rating.
- PRD.
- Pressure Opportunities.
- Unique Matches.
- Confidence Interval.
- Eligibility Status.

Include:
- Search.
- Sorting.
- Format filter.
- Season filter.
- Pressure filter.
- Player comparison.
- Player profile drill-down.
- CSV export.

Clearly distinguish the official overall ranking from exploratory filtered rankings.

## SECTION 06 — EVIDENCE & VALIDATION

Purpose:
Demonstrate that the rankings are robust.

Include:
- IPL vs T20I comparisons.
- Season-wise consistency.
- Pressure threshold sensitivity.
- Eligibility threshold sensitivity.
- Sample-size analysis.
- Player ranking stability.
- Outlier analysis.
- Model calibration, where applicable.
- Prediction vs observation, where applicable.
- Confidence interval comparisons.

Charts:
- Dumbbell comparisons.
- Sensitivity line charts.
- Rank stability plots.
- Histograms.
- Calibration plots.
- Forest plots.

Every chart must have a clear analytical purpose.

## SECTION 07 — METHODOLOGY & DATA AUDIT

Provide two internal tabs.

DATA AUDIT:
- Original file inventory.
- Schema.
- Data relationships.
- Missing values.
- Duplicate checks.
- Invalid records.
- Extras handling.
- Dismissal handling.
- Super Overs.
- Revised targets.
- Exclusions.
- Data completeness.

METHODOLOGY:
- Pressure formula.
- Batting model.
- Bowling model.
- Baselines.
- PRD.
- Reliability model.
- Shrinkage.
- Confidence intervals.
- Eligibility.
- Ranking logic.
- Validation.
- Assumptions.
- Limitations.

Include an explanation of every KPI.

Provide a downloadable methodology report.

---

# 13. FINAL KPI HIERARCHY

Do not overload the overview with every metric.

Overview:
- Matches Analysed.
- Deliveries Analysed.
- Pressure Deliveries.
- Pressure Delivery Share.
- Eligible Batters.
- Eligible Bowlers.

Pressure:
- Pressure Index.
- Pressure Exposure.
- High Pressure Share.
- Chase Difficulty.
- Wicket Resource Pressure.
- Innings Resource Pressure.

Batting:
- Pressure Runs.
- Pressure Strike Rate.
- Pressure Dot Ball %.
- Pressure Boundary %.
- Pressure Dismissal Rate.
- Context-Adjusted Batting Value.
- PRD.

Bowling:
- Pressure Economy.
- Pressure Wicket Rate.
- Pressure Dot Ball %.
- Boundary Conceded %.
- Context-Adjusted Runs Prevented.
- PRD.

Reliability:
- Match-to-Match Consistency.
- Pressure Success Rate.
- Unique Matches.
- Pressure Opportunities.
- Confidence Interval.
- Season Stability.

All KPIs must have:
- Name.
- Definition.
- Formula.
- Unit.
- Denominator.
- Interpretation.
- Data availability.
- Known limitations.

---

# 14. VISUAL DESIGN SYSTEM

Design the product as a premium enterprise sports analytics platform.

Avoid generic Streamlit styling.

The visual identity should feel sophisticated, clean, professional and data-dense without becoming cluttered.

## Colour palette

Primary navy: #14243A

Secondary navy: #223750

Primary teal: #0D9488

Positive green: #16856A

Pressure amber: #D97706

Negative coral: #DC6262

Background: #F4F7FA

Cards: #FFFFFF

Border: #E5EAF0

Text: #182536

Secondary text: #68778A

Use:
- Teal for positive analytical contribution.
- Green for positive reliability.
- Amber for elevated pressure.
- Coral for negative contribution.
- Neutral grey for unavailable or unclassified values.

Do not use colour alone to convey meaning.

Provide accessible contrast and consistent visual semantics.

## Layout

Use:
- Persistent left sidebar.
- Compact top header.
- Main page title.
- Short explanatory subtitle.
- Global filters.
- KPI cards.
- Primary chart area.
- Secondary evidence area.
- Expandable methodology notes.

Avoid excessive whitespace.

Avoid cramming too many charts into one row.

Use a consistent grid system and spacing scale.

## Typography

Use a clean sans-serif font.

Suggested:
- Inter or equivalent.
- Clear hierarchy.
- Compact but readable table typography.
- Large numerical KPI values.
- Consistent chart labels.

## Chart rules

Use Plotly.

Recommended charts:

| Analytical purpose | Chart |
|---|---|
| Main KPIs | Metric cards |
| Pressure distribution | Histogram |
| Match-state pressure | Heatmap |
| Performance comparison | Dumbbell |
| Player comparison | Scatter / bubble |
| Rankings | Horizontal bars |
| Statistical uncertainty | Forest plot |
| Consistency | Box plot |
| Season comparison | Small-multiple line charts |
| Sensitivity | Line charts |
| Ranking movement | Slope chart |

Avoid:
- 3D charts.
- Unnecessary pie charts.
- Decorative gauges.
- Radar charts as the primary player-comparison method.
- Excessive dual-axis charts.
- Unnecessary animations.

## Chart interaction

Every relevant chart should support:
- Hover tooltips.
- Clear labels.
- Units.
- Sample counts.
- Meaningful legends.
- Responsive rendering.

Tooltips should explain what the metric means, not simply repeat the number.

---

# 15. INTERACTION AND PRODUCT EXPERIENCE

Global filters:
- Competition: IPL / T20I / Combined.
- Season: 2022–2026.
- Pressure intensity.
- Innings phase.
- Player.

Interactions:
- Clickable navigation.
- Player drill-down.
- Two-player comparison.
- Sortable rankings.
- Searchable tables.
- Reset filters.
- CSV download.
- Methodology explanations.
- Expandable chart insights.

Critical requirement:

Filtering must not silently alter the official ranking.

Display two clearly distinguished modes:

1. Official Overall Rankings.
2. Exploratory Filtered Analysis.

The user must always understand which mode is active.

Maintain consistent filtering across related charts.

If a filter creates an insufficient sample, display an informative warning instead of a misleading value.

Do not display NaN, Infinity, undefined or raw Python exceptions to the user.

---

# 16. TECHNICAL ARCHITECTURE

Use:

Python.
Pandas.
NumPy.
SciPy where appropriate.
Statsmodels or scikit-learn where justified.
DuckDB.
Parquet.
Streamlit.
Plotly.

Do not introduce unnecessary dependencies.

Suggested project structure:

pressureiq/
│
├── app.py
├── config/
│   ├── settings.py
│   └── metric_definitions.py
│
├── data/
│   ├── raw/
│   ├── interim/
│   ├── processed/
│   └── analytical/
│
├── src/
│   ├── ingestion/
│   │   ├── load_data.py
│   │   └── schema_validation.py
│   │
│   ├── quality/
│   │   ├── data_audit.py
│   │   ├── cricket_rules.py
│   │   └── reconciliation.py
│   │
│   ├── pressure/
│   │   ├── pressure_engine.py
│   │   ├── chase_pressure.py
│   │   ├── first_innings_pressure.py
│   │   └── calibration.py
│   │
│   ├── batting/
│   │   ├── batting_metrics.py
│   │   └── batting_model.py
│   │
│   ├── bowling/
│   │   ├── bowling_metrics.py
│   │   └── bowling_model.py
│   │
│   ├── reliability/
│   │   ├── shrinkage.py
│   │   ├── uncertainty.py
│   │   └── consistency.py
│   │
│   ├── ranking/
│   │   ├── batter_rankings.py
│   │   └── bowler_rankings.py
│   │
│   └── validation/
│       ├── sensitivity.py
│       ├── robustness.py
│       └── model_tests.py
│
├── dashboard/
│   ├── overview.py
│   ├── pressure_engine.py
│   ├── batting.py
│   ├── bowling.py
│   ├── reliability.py
│   ├── rankings.py
│   ├── evidence.py
│   └── methodology.py
│
├── components/
│   ├── sidebar.py
│   ├── filters.py
│   ├── kpi_cards.py
│   ├── charts.py
│   ├── player_profile.py
│   └── comparison.py
│
├── reports/
│   ├── methodology/
│   ├── exports/
│   └── figures/
│
├── tests/
│   ├── test_data_quality.py
│   ├── test_cricket_rules.py
│   ├── test_pressure.py
│   ├── test_batting.py
│   ├── test_bowling.py
│   ├── test_reliability.py
│   └── test_rankings.py
│
├── requirements.txt
├── README.md
└── .gitignore

Adjust the architecture when necessary, but maintain separation between:
- Data processing.
- Statistical modelling.
- Business logic.
- Presentation.
- Validation.

Do not place all calculations inside app.py.

---

# 17. PERFORMANCE AND ENGINEERING QUALITY

The dataset contains approximately 201K delivery records.

The dashboard must load efficiently.

Requirements:
- Process data once.
- Store validated intermediate data.
- Use Parquet.
- Use DuckDB for efficient querying where beneficial.
- Cache expensive calculations.
- Avoid unnecessary full-dataframe copies.
- Separate analytical computation from UI rendering.
- Use deterministic calculations.
- Avoid repeated model training on every interaction.
- Use appropriate pre-aggregations.

The dashboard must run locally using a documented command.

Example:

streamlit run app.py

Provide installation instructions.

Do not require paid APIs or external services for the core analytical functionality.

---

# 18. TESTING REQUIREMENTS

Build unit tests and integration tests.

## Data tests
- No unexpected duplicate delivery keys.
- All relevant match IDs resolve.
- Player mappings are consistent.
- Exclusions are documented.

## Cricket-rule tests
- Wide handling.
- No-ball handling.
- Byes.
- Leg-byes.
- Bowler wicket attribution.
- Legal delivery counting.
- Super Overs.
- Revised targets.

## Pressure tests
- Pressure uses pre-delivery state.
- No future delivery leakage.
- Remaining balls are correct.
- Wickets remaining are correct.
- Revised targets are applied.
- Regulation innings are separated from Super Overs.

## Batting tests
- Batter runs are correct.
- Batter balls faced are correct.
- Dismissals are attributed correctly.
- Expected contribution is reproducible.

## Bowling tests
- Bowler runs conceded are correct.
- Legal balls are correct.
- Credited wickets are correct.
- Economy calculations are correct.

## Reliability tests
- Small samples do not receive unjustified certainty.
- Bootstrap is reproducible.
- Shrinkage behaves correctly.
- Unique match counts are correct.

## Ranking tests
- Rankings are deterministic.
- No duplicate player within a list.
- Eligibility is enforced.
- Top 10 is correctly ordered.
- Rankings agree with exported results.

---

# 19. VALIDATION AND ROBUSTNESS

The final model must undergo:

1. Data reconciliation.
2. Cricket-rule validation.
3. Pressure-threshold sensitivity.
4. Eligibility-threshold sensitivity.
5. Format comparison.
6. Season comparison.
7. Match-level consistency validation.
8. Sample-size bias investigation.
9. Ranking stability analysis.
10. Outlier investigation.

If the model uses predicted expected performance, evaluate it using a chronological or match-separated validation procedure.

Never train an expected-performance model on an observation and then claim the same observation demonstrates out-of-sample predictive accuracy.

Avoid leakage between training and evaluation data.

Do not use the final match outcome to calculate pre-delivery pressure.

Document all assumptions.

---

# 20. METHODOLOGY REPORT

Create a separate professional PDF.

The report must contain:

1. Executive Summary.
2. Problem Statement.
3. Dataset and Scope.
4. Data Quality Audit.
5. Cricket-Specific Data Processing.
6. Pressure Definition.
7. Pressure Index Construction.
8. Batting Performance Model.
9. Bowling Performance Model.
10. Pressure Response Delta.
11. Reliability Framework.
12. Statistical Shrinkage.
13. Confidence Intervals.
14. Eligibility Rules.
15. Final Batting Top 10.
16. Final Bowling Top 10.
17. Evidence and Player Comparisons.
18. Sensitivity Analysis.
19. Model Validation.
20. Assumptions.
21. Limitations.
22. Reproducibility Instructions.

The report and dashboard must use identical formulas, thresholds, player IDs and ranking results.

Include evidence tables and useful charts.

Do not use unsupported claims.

---

# 21. FINAL DELIVERABLES

The finished project must contain:

A. Interactive Streamlit dashboard.

B. Final top-10 batting rankings.

C. Final top-10 bowling rankings.

D. Methodology PDF.

E. Data audit report.

F. Processed analytical datasets.

G. Reproducible Python source code.

H. Unit and integration tests.

I. README with setup and execution instructions.

J. CSV exports of final rankings.

K. Evidence charts and player comparison tables.

L. Clear explanation of the signature metrics.

---

# 22. NON-NEGOTIABLE RULES

1. Never fabricate a statistic, player result or sample count.
2. Never invent missing data.
3. Never rank players by reputation.
4. Never hardcode player rankings.
5. Never use arbitrary weights without validation.
6. Never silently discard data.
7. Never mix Super Overs into normal T20 statistics.
8. Never charge byes or leg-byes to the bowler.
9. Never credit non-bowler dismissals to the bowler.
10. Never use future delivery information to calculate pre-delivery pressure.
11. Never confuse raw performance with context-adjusted contribution.
12. Never confuse absolute performance with reliability.
13. Never show a high-confidence rating when the sample is insufficient.
14. Never allow dashboard filters to silently change official rankings.
15. Never sacrifice statistical correctness for attractive visualisations.
16. Never present an unvalidated heuristic as an established cricket metric.
17. Never create placeholder player rankings that look like real results.
18. Never claim a model is validated without running its tests.
19. Never omit assumptions or limitations.
20. Never create a dashboard that cannot be independently reproduced.

---

# 23. IMPLEMENTATION PROTOCOL — FOLLOW THIS SEQUENCE

## INTEGRATED EXECUTION (ACTIVE)

Phase 1 data audit is complete and approved (`reports/methodology/PHASE1_DATA_AUDIT.md`).

Do **not** treat Phase 2 as a documentation-only gate. After Phase 1 approval, implement in one integrated programme:

1. Cricket-accounting and delivery pipeline (parquet).
2. Pressure engine, expected-performance baselines, batting/bowling metrics, reliability, rankings — in modular Python, with each modelling decision documented in code and the methodology report.
3. Streamlit dashboard (all eight sections) built alongside the engine, reading precomputed analytical tables.
4. Automated tests and validation throughout.
5. Official rankings and methodology report only after calculations pass validation.

Preserve original CSVs and the Phase 1 audit. Do not fabricate rankings. Provisional vs validated outputs must be distinguishable.

Credit-saving: no repeated audit, no extra planning documents, no per-decision approval pauses unless correctness cannot be resolved from data.

Assumptions frozen after Phase 1 (see cricket_rules.py):
- Official scope = 371 IPL + 482 T20I; exclude 30 other T20 from official rankings.
- Super Overs excluded from regulation rankings.
- Revised overs = legal-ball allocations.
- `other` extras classified as no-balls after row-level review (beamer/full-toss/height patterns).
- `extras_2_runs` on no-balls treated as additional extras not off the bat (team runs yes, bowler-conceded no).
- Basil Hameed IDs 8638 and 39444 remain unmerged.
- Ball-by-ball appearance is the participation source.

IMPORTANT (historical):

Do not attempt to complete the entire project in one uncontrolled coding operation.

Work in explicit phases. The sequence below remains the logical milestone order; after Phase 1 approval it is executed continuously rather than as separate wait-states.

## PHASE 1 — DATA AUDIT

First inspect the actual source files.

Create:
- Dataset inventory.
- Schema report.
- Relationship report.
- Data-quality report.
- Cricket-rule validation report.
- Data exclusion log.

Identify unresolved issues.

Do not build player rankings.

STOP and present findings.

Wait for approval before moving to modelling.

## PHASE 2 — MODEL DESIGN

Design and document:
- Pressure model.
- Batting metrics.
- Bowling metrics.
- Expected-performance baselines.
- PRD.
- Reliability framework.
- Eligibility criteria.
- Ranking estimand.

Provide formulas and reasoning.

Identify unresolved modelling choices.

STOP and present the proposed methodology.

Wait for approval.

## PHASE 3 — ANALYTICAL IMPLEMENTATION

Build the analytical engine.

Calculate:
- Pressure opportunities.
- Batting contributions.
- Bowling contributions.
- Context-adjusted performance.
- PRD.
- Reliability.
- Statistical uncertainty.

Run tests.

Generate preliminary analytical outputs.

STOP and present validation results before finalising rankings.

## PHASE 4 — RANKING AND EVIDENCE

Generate:
- Official batting top 10.
- Official bowling top 10.
- Supporting player profiles.
- Sensitivity tests.
- Format and season comparisons.

Reconcile ranking outputs against the methodology.

STOP and present the final ranking evidence.

## PHASE 5 — DASHBOARD DEVELOPMENT

Only after analytical outputs have been validated, develop the eight dashboard sections.

Use the final KPI hierarchy.

Implement interactions, filters, charts, navigation, player drill-down and downloads.

## PHASE 6 — QUALITY ASSURANCE

Test:
- All navigation.
- All filters.
- All charts.
- All calculations.
- All exports.
- Responsive layouts.
- Error states.
- Performance.
- Ranking consistency.

Fix issues before declaring completion.

## PHASE 7 — FINAL PACKAGING

Produce the final methodology PDF, rankings, code, tests, audit report and README.

Perform a final consistency audit across every deliverable.

---

# 24. FIRST RESPONSE REQUIRED FROM THE AGENT

When this specification is provided, do NOT immediately start coding the dashboard.

First:

1. Confirm that you understand the project.
2. Inspect the project directory and locate the supplied dataset.
3. Confirm whether all six source CSVs are accessible.
4. Inspect the actual schema and record counts.
5. Produce the Phase 1 data-audit plan.
6. Identify unresolved cricket-scoring and modelling questions.
7. Recommend the next implementation steps.

Do not generate final rankings or populate the dashboard with fabricated data.

Wait for explicit approval before advancing from Phase 1.

The goal is not simply to build a dashboard.

The goal is to build a defensible cricket performance intelligence system that identifies the players who can genuinely be trusted when the match is on the line.

QUALITY STANDARD:

Think like a top-tier cricket analytics team.

Build like a senior software engineering team.

Design like a premium analytical product team.

Validate like a statistician.

Explain like a great product analyst.

The final output must be accurate, transparent, interactive, reproducible and competition-ready.


## CRITICAL METHODOLOGY GUARDRAILS — NON-NEGOTIABLE

### 1. Official competition scope

The dataset contains 401 T20 matches, comprising:
- 371 IPL matches
- 30 other domestic/development T20 matches

It also contains 482 T20I matches.

The default official analytical scope is therefore **853 matches: 371 IPL + 482 T20I**.

Do not include the additional 30 T20 matches in official player rankings unless the competition organisers explicitly confirm their eligibility. Preserve them in the raw dataset and document their exclusion. Do not confuse the 401-match T20 category with the IPL-only scope.

### 2. Pressure scores must represent real cricket pressure

A visually impressive pressure index is not automatically a valid measure of cricket pressure.

Do not create an arbitrary weighted score simply because its output looks intuitive or produces interesting player rankings.

Every pressure variable, threshold, coefficient and classification must have:
- A cricket-specific rationale.
- A clear definition and calculation method.
- No information leakage from the delivery outcome being evaluated.
- Evidence that it captures meaningful match difficulty.
- Sensitivity analysis showing how reasonable alternative assumptions affect results.

### 3. First-innings pressure requires special scrutiny

Do not assume that a high run rate, late innings, or low wickets automatically means high pressure.

Develop a separate first-innings pressure framework based on the difficulty of the scoring situation relative to an expected par score or expected scoring opportunity.

Investigate:
- Score relative to expected par at that exact match state.
- Overs and legal balls remaining.
- Wickets/resources remaining.
- Batting phase and scoring opportunity.
- Match and competition context.
- Revised overs and targets where applicable.

Validate whether the framework identifies genuinely difficult scoring situations rather than merely identifying aggressive batting situations.

### 4. Expected-performance baselines require independent validation

Expected batting and bowling performance must be estimated from comparable cricket situations, not arbitrary averages or convenient assumptions.

Document:
- Which variables define comparable situations.
- How baselines are estimated.
- How sparse situations and small samples are handled.
- Whether the model is evaluated on unseen matches or later periods.
- Whether format, innings phase, wickets, match state and other relevant context are accounted for.
- Whether the baseline is calibrated and performs consistently across IPL and T20I.

Do not present an unvalidated expected-performance model as established truth.

### 5. Approval gate

Before finalising player rankings, produce a methodology validation report covering the pressure model, first-innings framework, expected-performance baselines, sample sizes, sensitivity analysis and alternative definitions.

Flag unresolved assumptions and explain their potential impact. Do not silently proceed to final rankings if a core methodological assumption is unsupported.
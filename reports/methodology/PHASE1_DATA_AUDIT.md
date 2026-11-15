# PRESSUREIQ — Phase 1 Data Audit

**Status:** Phase 1 complete. No pressure model, no player rankings, no dashboard.

**Source of truth:** original CSVs copied from `6af458274c1e8_data_pack/Data Pack/` into `data/raw/`. Originals were not modified.

**Machine artefacts:** `data/interim/` (inventory, flags, extras, revised-match inspection, reconciliation).

---

## 1. What data is available

All six required files are present. Schemas match the master specification exactly.

| File | Records | Columns match spec | Duplicate full rows |
|---|---:|:---:|---:|
| competitions.csv | 141 | yes | 0 |
| teams.csv | 353 | yes | 0 |
| matches.csv | 883 | yes | 0 |
| ball_by_ball.csv | 200,999 | yes | 0 |
| competition_team_player_mapping.csv | 6,413 | yes | 0 |
| playing_eleven.csv | 28,381 | yes | 0 |

Date coverage: **2022-01-22 to 2026-11-01**.

### Competition scope (recalculated from source)

| Scope | Matches | Competitions | Notes |
|---|---:|---:|---|
| IPL | 371 | 5 | IPL 2022–2026 (74, 74, 74, 75, 74) |
| T20I | 482 | 131 | Includes 2022/23-style season labels |
| Other T20 | 30 | 2 | Mens T20 Emerging Teams Asia Cup 2024; Asia Cup Rising Stars 2025 |
| **Official IPL + T20I** | **853** | | Agrees with the specification |
| Official ball-by-ball | **194,014** | | Agrees with the specification, before delivery-level exclusions |

Three competitions have no matches (series listed but empty): Afghanistan v Sri Lanka T20I Series 2026; UAE in Nepal T20I Series 2026; India in Bangladesh T20I Series 2025.

The ZIP also contains the problem-statement PDF and macOS metadata (`.DS_Store`, `__MACOSX`). Those are not analytical inputs.

### Relational model (validated)

```
competitions 1──* teams
competitions 1──* matches
competitions 1──* competition_team_player_mapping
matches 1──* ball_by_ball
matches 1──* playing_eleven
teams  *──* players  (via mapping and playing_eleven; team_id is global, not competition-local)
```

- Every match `comp_id` exists in competitions.
- Every match home/away team exists in `teams` for that competition.
- Every ball-by-ball `match_id` exists in matches.
- Every ball-by-ball batting/bowling team is the match home or away team.
- Batting team never equals bowling team.
- Every player ID observed in deliveries exists in the mapping table.
- Use **player_id** and **match_id** as identifiers. Names are display labels only.

Identifiers in deliveries: 959 distinct player IDs. Mapping has 1,217 IDs (258 never appear in ball-by-ball). Playing XI has 1,082 IDs.

---

## 2. What is reliable

These properties are clean enough to use as foundations.

### Keys and integrity

- No duplicate `match_id`.
- No duplicate delivery key `(match_id, innings, overid, over_ball_num)`.
- No duplicate `(match_id, innings, innings_ball_num)`.
- No duplicate mapping key `(comp_id, team_id, player_id)`.
- No missing `match_id`, `striker_id`, `non_striker_id`, or `bowler_id` on deliveries.
- No negative `runs`, `extras1_runs`, or `extras_2_runs`.
- Innings values are only `{1, 2, 3, 4}`. Overs are 1–20. `over_ball_num` ranges 1–13 (extras extend the over).
- `is_wicket` and `dismissal_type` are perfectly aligned (10,881 wickets; 0 mismatches either way).
- On wicket rows, `dismissed_player_id` is always the striker or non-striker (0 off-crease mismatches), except one Retire Out with a missing dismissed player.
- Non-extra boundaries: every `is_four` has `runs == 4`; every `is_six` has `runs == 6`; never both flags.

### `runs` is batter runs, not team runs

Evidence:

- On non-extra balls, `runs` matches boundary flags exactly.
- Wides: `runs = 0`, extras live in `extras1_runs`.
- Byes: `runs = 0`, extras in `extras1_runs`.
- Leg-byes: `runs = 0` except one dirty row; extras in `extras1_runs`.
- Overstep (no-ball): `extras1_runs = 1` always; `runs` holds off-the-bat scoring (including 81 fours and 47 sixes).

Team innings total is **not** `sum(runs)`.

Against 411 “won by N runs” results, reconstructed innings margin hit rates:

| Team-total candidate | Margin match rate |
|---|---:|
| A = sum(`runs`) | 5.8% |
| B = sum(`runs` + `extras1_runs`) | 91.2% |
| C = sum(`runs` + `extras1_runs` + `extras_2_runs`) | **97.6%** |

The 10 candidate-C misses are DLS/Super Over matches, where the result margin is not innings1 − innings2. That is expected. For unrevised completed matches, C is the team total.

### Delivery numbering

- `overid` is the cricket over number (1–20).
- `over_ball_num` is the ball *within the over including extras*.
- `innings_ball_num` is a sequential counter of **all recorded deliveries** in the innings, including wides and no-balls. It is **not** legal balls faced.
- Legal-ball remaining-resource calculations must count legal deliveries, not `120 - innings_ball_num`.

### Super Overs

Six matches have innings 3/4 (38 deliveries: 25 + 13):

| match_id | Scope | Result |
|---|---|---|
| 34429 | T20I | India won Super Over |
| 40725 | IPL | DC won Super Over |
| 45512 | T20I | India won Super Over |
| 48027 | Other T20 | Bangladesh A won Super Over |
| 48029 | Other T20 | Pakistan A won Super Over |
| 50359 | IPL | KKR won Super Over |

These must stay out of regulation T20 batting/bowling/pressure rankings.

---

## 3. What needs reconciliation

Nothing below was silently dropped. Flags are in `data/interim/exclusion_flag_log.csv`.

### 3.1 Extras accounting (must freeze in Phase 2)

Observed `extras_type`:

| extras_type | n | `runs` | `extras1_runs` | `extras_2_runs` |
|---|---:|---|---|---|
| (none) | 189,167 | batter runs 0–6 | ~0 | ~0 |
| wide | 7,714 | always 0 | 1–5 (mostly 1; 270 fives = wide to boundary) | 0 |
| legbyes | 2,748 | 0 (1 exception) | bye-equivalent 0–5 | 0 |
| Overstep | 576 | batter runs, including boundaries | always 1 (no-ball extra) | >0 in 21 rows, only when `runs = 0` |
| byes | 529 | always 0 | 1–5 | 0 |
| other | 264 | same pattern as Overstep | always 1 | >0 in 14 rows |
| Penalty | 1 | 0 | 5 | 0 |

**Proposed mapping (awaiting approval):**

| Role | Rule |
|---|---|
| Batter runs | `runs` on non-wide, non-bye, non-leg-bye, non-penalty balls. On Overstep/`other`, `runs` is still batter runs. Wides/byes/leg-byes/penalty contribute 0 batter runs. |
| Team runs | `runs + extras1_runs + extras_2_runs` |
| Bowler-conceded | batter runs + wides + no-ball extras (`Overstep` and, if approved, `other`). **Do not** charge byes, leg-byes, or penalty to the bowler. |
| Legal delivery | not wide and not no-ball (`Overstep`/`other`) |
| Batter ball faced | legal deliveries (standard cricket). Confirm free-hit / run-out-off-wide treatment in Phase 2. |

Supporting evidence that `other` is a no-ball family: treating only `wide`+`Overstep` as illegal leaves 20-over innings with 121–124 “legal” balls (impossible). Including `other` as illegal caps completed 20-over innings at 120 legal balls.

`extras_2_runs` is rare (35 deliveries, Overstep/`other` only) and appears to store extra runs when `runs = 0` (likely bye/leg-bye off a no-ball). Phase 2 must decide whether those runs are bowler-conceded.

One leg-bye has `runs = 1` and `extras1_runs = 0` (match 37099). Flag; do not guess.

### 3.2 Dismissal attribution

| dismissal_type | n | Proposed bowler credit |
|---|---:|---|
| Caught | 7,557 | yes |
| Bowled | 1,775 | yes |
| LBW | 709 | yes |
| RunOut | 600 | **no** |
| Stump | 214 | yes (stumped) |
| Hit Wicket | 17 | yes |
| Retire Out | 6 | **no** |
| Obstracting the field | 2 | **no** (typo) |
| Obstructing the field | 1 | **no** |

Issues:

- 1 Retire Out wicket with **no** `dismissed_player_id` (Hardik Pandya, match 40709). Count the wicket against the batting side; do not invent a batter ID beyond the striker if we treat striker as the retired batter.
- 12 rows have `dismissed_player_id` populated with `is_wicket = False` and no dismissal type. These look like tagging errors (including sixes). **Do not treat as dismissals.**
- 40 wickets on wides, all RunOut. Legal-ball and batter-faced rules must handle run-outs off wides.
- No `caught and bowled` label; those are inside `Caught`.
- No `retired hurt` type. Possible retired-hurt events may sit in the 12 false-wicket player-id rows; evidence is insufficient.

### 3.3 Matches without usable innings

| Issue | n | Detail |
|---|---:|---|
| No ball-by-ball | 16 | All `Match Abandoned` (4 IPL, 12 T20I) |
| No innings 1 BBB | 16 | Same 16 abandoned matches |
| No innings 2 BBB | 38 | Abandoned, No Result, or first-innings-only interruptions |
| No playing XI | 3 | Subset of abandoned matches |
| `win_team_id` missing | 41 | 19 Abandoned + 21 No Result + 1 Match Tied |
| `result` populated | 883 | Never null; includes Abandoned / No Result / Super Over text |

These matches can remain in inventory. They should not enter regulation pressure rankings as complete two-innings contests. First-innings-only fragments need an explicit Phase 2 include/exclude rule.

### 3.4 Playing XI

- 28,381 rows, 28,341 unique `(match_id, team_id, player_id)` keys.
- **75 duplicate-key rows** (35 player-match-team groups), mainly conflicting `batting_order` on the same player. Two matches (13613, 21176) plus Super Over match 28962 are the worst clusters.
- `is_played`: 19,714 True / 8,667 False. Inclusion in the file does **not** mean the player participated.
- Impact flags: 558 `is_impact=1` and 558 `is_impact_off=1`.
- Only 1,168 of 1,760 match-teams have exactly 11 `is_played=True`. IPL impact substitutions produce 12+ “played” rows. 23 match-teams have 0 played (abandoned).
- 6 ball-by-ball participant keys are absent from XI; 6 BBB participants lack `is_played=True`.

**Rule to freeze:** batting/bowling opportunity = appearance in ball-by-ball. XI is metadata (captain, keeper, impact, selected squad), not the participation fact table.

### 3.5 Player identity collisions

Seven display names map to two IDs. Most are different people (e.g. Abdul Samad Pakistan vs SRH; Haider Ali Pakistan vs UAE). Two need care:

- **Basil Hameed** IDs 8638 and 39444, both UAE, **both appear in ball-by-ball**. Stats will split unless merged.
- **Rashid Khan** 4722 (Afghanistan / GT, heavy BBB usage) vs 20172 (Nepal, mapping only, 0 BBB). Low ranking risk; do not merge by name.

One ID has two name strings: 4458 = “Aneurin Donald” / “AHT Donald”.

### 3.6 Revised overs and targets

- 34 matches with revised-overs fields.
- 23 matches with `revised_target`.
- Values are **{30, 42, 48, 54, 60, 66, 72, 78, 84, 90, 102, 108, 114}** — all multiples of 6.

This is **legal-ball allocation**, not decimal overs. 114 means 19 overs, not 114.0 overs. Decoding as cricket decimal overs (5.2 → 32 balls) matches **0** innings.

When an innings used its full allocation, observed legal balls equal the stored integer. When rain/DLS cut an innings short, or the chase finished early, observed legal balls are below the allocation. That is consistent.

Per-match table: `data/interim/revised_matches_inspection.csv`.

Several DLS “won by runs” results **cannot** be reproduced as innings1 − innings2, even with `revised_target`. Remaining balls and par must use:

- allocated legal balls from revised-overs fields (integer balls / 6 = overs),
- `revised_target` as the chase target when present,
- actual legal balls already bowled from ball-by-ball.

Matches where second-innings resources or target cannot be reconstructed (abandoned mid-innings, No Result, missing second innings) must be flagged `TARGET_UNRELIABLE` before pressure scoring.

### 3.7 Other data-quality notes (not blockers)

- Captains missing on ~5% of matches; toss missing on 15 matches (abandoned).
- `man_of_the_match = 0` on 119 matches (none awarded / abandoned).
- `bowl_speed = 0` on 38.7% of deliveries: missing speed, not a real 0 kph. Do not use raw 0 in models.
- `stroke` missing 3.1% (often extras).
- Mapping covers 140 of 141 competitions.
- `batting_order` on deliveries goes to 13 (impact / unusual XI).

---

## 4. Cricket-specific edge cases

1. **Wides and no-balls are not legal balls.** `over_ball_num` and `innings_ball_num` still increment.
2. **Wide to the boundary** is stored as `extras1_runs = 5`, not four + wide split. Charge 5 to bowler.
3. **No-ball off the bat** stores the extra in `extras1_runs` and batter scoring in `runs`. Team total adds both. Boundary flags follow `runs`.
4. **No-ball + bye/leg-bye** likely uses `extras_2_runs` when `runs = 0` (35 balls). Bowler charge is unresolved.
5. **`other` extras** behave as no-balls that are not labelled Overstep (height/fielding). Treat as illegal unless a counterexample appears.
6. **Penalty** (1 ball, 5 runs): team runs yes, bowler no, not a legal-ball issue in the usual sense (confirm whether the delivery is legal; here `runs=0`, type=Penalty).
7. **Run-outs off wides** (40): wicket counts for batting resources; bowler does not get a wicket; delivery still illegal.
8. **Retired out** (6): batting wicket, not bowler-credited. One missing dismissed player ID.
9. **Obstructing the field** including the typo spelling: not bowler-credited.
10. **Super Overs** in innings 3–4, including two Other-T20 matches that are already out of official scope.
11. **DLS/rain**: 34 revised allocations, 23 revised targets. First-innings par and chase pressure must use allocated balls and revised target, not a blanket 120 balls / innings1+1.
12. **Incomplete matches**: 16 no BBB; 22 additional missing second innings; 21 No Result; 19 Abandoned (some overlap).
13. **Impact players**: XI duplicates and 12+ played flags. BBB is the participation source.
14. **Free-hit** is not a column. Inferring from previous no-ball is possible but error-prone; dismissals on the subsequent ball need a Phase 2 rule.
15. **Tied match with no Super Over innings in BBB** exists (`Match Tied`, `win_team_id` null). Do not invent a winner.

---

## 5. Modelling decisions still unresolved

Phase 1 does not choose these. They need approval before Phase 2 design.

1. **Official scope:** default exclude the 30 Other T20 matches (Emerging Teams Asia Cup 2024, Asia Cup Rising Stars 2025). Confirm.
2. **Freeze extras rules**, especially:
   - `other` = no-ball,
   - bowler charge for `extras_2_runs` on no-balls,
   - whether a penalty delivery is legal,
   - batter balls faced on wides (0 except maybe run-out? Standard is 0).
3. **Freeze revised-overs unit as legal balls** and the reconstruction rule when observed balls ≠ allocation.
4. **Incomplete innings:** use completed first innings for first-innings pressure, or drop the whole match.
5. **Super Overs:** exclude from official rankings (recommended). Separate analysis only if useful.
6. **Basil Hameed dual IDs:** merge, keep split, or mark insufficient identity.
7. **Impact substitute overs:** no effect on delivery metrics if BBB is source; needed only if we weight “opportunity” by selection.
8. **Pressure definition** (not started): first-innings par, chase difficulty, pre-delivery leakage, thresholds.
9. **Eligibility thresholds** for batters and bowlers: set from coverage **before** seeing leaderboards.
10. **Free-hit inference.**
11. **Expected-performance strata:** format (IPL vs T20I), phase, wickets, venue — design in Phase 2, not here.

---

## Flag summary (no silent deletes)

| Flag | Count |
|---|---:|
| MATCH_NO_BBB | 16 |
| MISSING_FIRST_INNINGS_BBB | 16 |
| MISSING_SECOND_INNINGS_BBB | 38 |
| OUT_OF_OFFICIAL_SCOPE | 30 |
| REVISED_OVERS | 34 |
| REVISED_TARGET | 23 |
| SUPER_OVER | 6 |

---

## Recommended Phase 2 inputs (not yet built)

If approved, Phase 2 should start from:

- Official match set = IPL + T20I, minus abandoned matches with no BBB.
- Regulation deliveries = innings ∈ {1, 2}.
- Derived columns: batter runs, team runs, bowler-conceded, legal ball, batter faced, bowler-credited wicket — using the extras/dismissal tables above.
- Revised allocation in balls; revised target when present.
- Player key = `player_id` with an identity exception list.

---

**Waiting for approval before Phase 2 (model design).**

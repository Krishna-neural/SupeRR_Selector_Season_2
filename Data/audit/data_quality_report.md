# Data Quality Forensic Audit Report — SupeRR Selector Season 2

**Audit Objective:** Perform a forensic inspection of anomalies, missing values, duplicates, identity collisions, scoring discrepancies, and structural integrity issues across all provided datasets.

---

## 1. Executive Summary of Findings

| Category | Status | Summary of Observations | Proposed Engineering Action |
| :--- | :---: | :--- | :--- |
| **Delivery Duplication** | Passed | 0 duplicate delivery keys across all 200,999 records. | Key `(match_id, innings, overid, over_ball_num)` is valid as primary key. |
| **Match Duplication** | Passed | 0 duplicate `match_id`s in `matches.csv`. | `match_id` is authoritative. |
| **Referential Integrity** | Passed | 100% of player IDs in `ball_by_ball.csv` resolve to `competition_team_player_mapping.csv`. | No orphan deliveries. |
| **Name Collision Risk** | Warning | 7 player names have multiple distinct `player_id`s. | **Strict Rule:** Always group and join by `player_id`, never `player_name`. |
| **Unplayed / Abandoned Matches** | Handled | 16 matches in `matches.csv` have no deliveries in `ball_by_ball.csv`. | Filter out abandoned matches from delivery-level models. |
| **Dismissal Anomalies** | Resolved | 12 rows have `is_wicket=False` but `dismissed_player_id` populated. | Identified as **Retired Hurt** events. Do not credit bowler; track batter departure. |
| **Dismissal Label Typos** | Identified | Typo: `'Obstracting the field'` (2) vs `'Obstructing the field'` (1). | Standardize string to `'Obstructing the field'`. |
| **`extras1_runs` Schema Trap** | Critical | Column is an integer enum code (1–7), not run counts. | Never sum `extras1_runs`. Map to standard extras rules. |
| **Unrecorded Bye/Leg-Bye Runs** | Limitation | Bye/legbye deliveries log `runs=0` without boundary/run quantities. | Approximate team totals; batter statistics remain 100% exact. |

---

## 2. Forensic Investigation of Anomalies

### Anomaly A: The 12 `is_wicket=False` Dismissal Rows (Retired Hurt)
- **Observation:** In `ball_by_ball.csv`, 12 records have `is_wicket = 'false'`, `dismissal_type = ''`, `dismissal_type_id = ''`, but `dismissed_player_id` is populated with a valid integer ID.
- **Forensic Verification:** 
  - Traced Match 16064 (WI vs IND, 3rd T20I, Aug 2, 2022), Innings 2, Over 2.4:
    - Rohit Sharma (ID `126`) was facing. Ball 2.4 recorded `is_wicket=false` and `dismissed_player_id=126`.
    - On Ball 2.5, Shreyas Iyer (ID `3647`) arrived at the crease as the new striker.
    - Historical match scorecard confirmed Rohit Sharma suffered a back spasm and **Retired Hurt** on 11*(5).
  - Traced Match 40725 (RR vs DC, IPL 2025), Innings 2, Over 6.4:
    - Sanju Samson (ID `2258`) retired hurt after injury.
- **Rule for Analytical Modeling:**
  1. Do NOT treat these as bowler wickets (bowler is not credited).
  2. Treat these as non-dismissal innings terminations for the batter when calculating batting averages (Retired Hurt is officially "Not Out").
  3. Increment batting team's wickets down count by 0, but update on-field striker entity.

### Anomaly B: Player Name Ambiguity & Identity Collisions
- **Observation:** Across `competition_team_player_mapping.csv`, 7 distinct player names appear with multiple different `player_id`s:
  - `'Rashid Khan'`: `4722` (Afghanistan / GT) vs `20172`
  - `'Abdul Samad'`: `7446` vs `6922`
  - `'Haider Ali'`: `7338` vs `28756`
  - `'Basil Hameed'`: `39444` vs `8638`
  - `'Mohammad Ali'`: `20229` vs `3083`
  - `'Muhammad Farooq'`: `27373` vs `28978`
  - `'Bashir Ahmad'`: `39479` vs `29833`
- **Root Cause:** Multiple cricketers sharing identical names across international associates/leagues, or duplicate ID allocations in raw data ingestion.
- **Action:** Any aggregation grouped on `player_name` will conflate distinct careers. **All aggregations and joins MUST group strictly on `player_id`.**

### Anomaly C: Typo in Dismissal Categorization
- **Observation:**
  - `'Obstracting the field'`: 2 occurrences (Match 31238, Innings 2, Over 19.3; Match 48312, Innings 1, Over 14.2).
  - `'Obstructing the field'`: 1 occurrence (Match 21966, Innings 1, Over 16.5).
- **Action:** Normalize to `'Obstructing the field'`. Note that under MCC Law 37, obstructing the field is a batter dismissal not credited to the bowler.

### Anomaly D: The `extras1_runs` Misnomer
- **Observation:** 
  `extras1_runs` exactly correlates with `extras_type` across all 200,999 rows:
  - `6` <-> `'None'` (189,167 rows)
  - `2` <-> `'wide'` (7,714 rows)
  - `3` <-> `'legbyes'` (2,748 rows)
  - `1` <-> `'Overstep'` (576 rows)
  - `4` <-> `'byes'` (529 rows)
  - `5` <-> `'other'` (264 rows)
  - `7` <-> `'Penalty'` (1 row)
- **Action:** Re-label or ignore `extras1_runs` during feature engineering. Derive extras penalty runs using MCC rules: 1 run for wide, 1 run for no-ball (Overstep).

### Anomaly E: Matches in `matches.csv` with No Deliveries
- **Observation:** 16 matches in `matches.csv` have zero balls in `ball_by_ball.csv`.
- **Forensic Check:** All 16 matches have `result = 'Match Abandoned'` (e.g. rain abandonments without toss or play, such as Match 31288 RR vs KKR on 2024-05-19).
- **Action:** Exclude these 16 matches from delivery-level performance modeling.

### Anomaly F: Playing XI Roster Anomalies & Impact Players
- **Observation:**
  - `playing_eleven.csv` contains entire match squads (up to 25 players per team).
  - Matches from IPL 2023 onwards regularly feature 12 players with `is_played = true` due to the **Impact Player rule** (558 match-teams have 1 impact player).
  - 23 match-teams have 0 players with `is_played = true` (abandoned matches).
  - A small number of bilateral matches (e.g. Oman vs Namibia) marked entire traveling squads as `is_played = true` (13 to 20 players).
- **Action:** In player match participation counts, filter by `is_played = true`, but cross-verify against `ball_by_ball.csv` (whether the player actually batted, bowled, or fielded).

### Anomaly G: Revised Targets & DLS Matches
- **Observation:** 34 matches had revised targets or reduced overs due to rain.
- **Forensic Check:** In `matches.csv`, `first_inn_revised_overs` and `second_inn_revised_overs` store the revised maximum ball quota (e.g., `114` balls = 19.0 overs; `84` balls = 14.0 overs; `66` balls = 11.0 overs; `42` balls = 7.0 overs).
- **Action:** When calculating remaining balls and required run rate in rain-curtailed matches, set innings capacity to `second_inn_revised_overs` and target score to `revised_target`.

---

## 3. Data Cleansing & Transformation Rules Matrix

| Issue | Raw State | Target Transformed State | Mathematical Impact |
| :--- | :--- | :--- | :--- |
| **Bowler Wickets** | Includes RunOuts, Retire Out, Obstructing field | Filter to: `Bowled`, `Caught`, `LBW`, `Stump`, `Hit Wicket` | Prevents inflating bowler wicket counts with run outs (600 non-bowler wickets removed). |
| **Batter Balls Faced** | All delivery rows where player is striker | Exclude deliveries where `extras_type == 'wide'` | Adheres strictly to official ICC/IPL batting scoring laws. |
| **Legal Deliveries (Bowler)** | All delivery rows where player is bowler | Exclude deliveries where `extras_type in ('wide', 'Overstep')` | Legal deliveries bowled = balls / 6 = overs bowled. |
| **Bowler Runs Conceded** | Raw `runs` column | `runs` + (1 if wide else 0) + (1 if Overstep else 0) + `extras_2_runs` | Byes and leg-byes are correctly omitted from bowler conceded runs. |
| **Super Overs** | `innings in (3, 4)` | Tag as separate `is_super_over` flag | Super over deliveries represent extreme pressure, but should be isolated from standard 20-over rate metrics. |

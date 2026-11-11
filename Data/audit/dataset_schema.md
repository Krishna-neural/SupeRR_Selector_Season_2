# Comprehensive CSV Schema Analysis — SupeRR Selector Season 2

**Scope:** Exhaustive audit of all 6 CSV files, 77 distinct columns, data types, null profiles, uniqueness, key roles, domain-specific analytical utility, and Phase 1.5 empirical patches.

---

## 1. `competitions.csv`
- **Total Records:** 141 rows
- **Total Columns:** 4
- **Natural Primary Key:** `comp_id` (Unique: 141 / 141, Nulls: 0)

| Column Name | Stored / Logical Type | Example Values | Missing Values (%) | Unique Count | Key Classification | Analytical Utility |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `comp_id` | `INTEGER` | `1358`, `1715`, `3395` | 0 (0.0%) | 141 | Primary Key | Join key to `matches`, `teams`, `competition_team_player_mapping`. |
| `comp_name` | `STRING` | `'IPL 2022'`, `'ICC Men's T20 World Cup 2024'` | 0 (0.0%) | 141 | Alternate Key | Tournament classification; separates IPL franchise matches from T20 Internationals and Emerging Cups. |
| `match_format` | `STRING` | `'T20'`, `'T20I'` | 0 (0.0%) | 2 | Attribute | Segmenting domestic league/associate (`T20`) vs international (`T20I`) contexts. |
| `season` | `STRING` | `'2022'`, `'2023'`, `'2024'`, `'2025'`, `'2026'` | 0 (0.0%) | 8 | Attribute | Longitudinal temporal weighting, career baselines, and cross-season consistency checks. |

### Competition Stratification Tiers (Phase 1.5 Update)
- **Tier 1 (`IPL`):** `comp_id in [1358, 1715, 2193, 2725, 3298]` (371 matches).
- **Tier 2 (`T20I_FullMember`):** T20I matches between ICC Full Members (`India, Australia, England, South Africa, New Zealand, West Indies, Pakistan, Sri Lanka, Bangladesh, Afghanistan, Ireland, Zimbabwe`).
- **Tier 3 (`T20_Associate_Emerging`):** T20I matches involving Associate members and emerging team tournaments (`comp_id in [2670, 3289]`).

---

## 2. `teams.csv`
- **Total Records:** 353 rows
- **Total Columns:** 3
- **Composite Primary Key:** `(comp_id, team_id)` (Unique: 353 / 353, Nulls: 0)

| Column Name | Stored / Logical Type | Example Values | Missing Values (%) | Unique Count | Key Classification | Analytical Utility |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `comp_id` | `INTEGER` | `1331`, `1358`, `3298` | 0 (0.0%) | 141 | Foreign Key -> `competitions.comp_id` | Identifies competition context of the team. |
| `team_id` | `INTEGER` | `22`, `28`, `18`, `256` | 0 (0.0%) | 38 | Foreign Key -> `teams.team_id` | Standard team entity identifier. |
| `team_name` | `STRING` | `'India'`, `'Rajasthan Royals'`, `'England'` | 0 (0.0%) | 38 | Attribute | Human-readable team identification; franchise vs country. |

---

## 3. `matches.csv`
- **Total Records:** 883 rows
- **Total Columns:** 22
- **Natural Primary Key:** `match_id` (Unique: 883 / 883, Nulls: 0)

| Column Name | Stored / Logical Type | Example Values | Missing Values (%) | Unique Count | Key Classification | Analytical Utility |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `match_id` | `INTEGER` | `13511`, `14112`, `40725` | 0 (0.0%) | 883 | Primary Key | Transactional join key connecting deliveries and playing XIs. |
| `comp_id` | `INTEGER` | `1331`, `1358`, `2193` | 0 (0.0%) | 138 | Foreign Key -> `competitions.comp_id` | Links match to competition format and season. |
| `match_number` | `INTEGER` | `1`, `2`, `74` | 0 (0.0%) | 75 | Attribute | Schedule order within competition. |
| `match_date` | `DATE (YYYY-MM-DD)` | `'2022-01-22'`, `'2024-05-26'` | 0 (0.0%) | 686 | Attribute | Chronological ordering, recency weighting, and dynamic Elo progression. |
| `stage` | `STRING` | `'League'`, `'Qualifier'`, `'Eliminator'`, `'Final'` | 0 (0.0%) | 7 | Attribute | **Crucial Pressure Variable:** Knockout/Playoff matches carry elevated macro-pressure ($\kappa_{\text{stage}} = 1.25$). |
| `venue_id` | `INTEGER` | `54`, `8`, `44` | 0 (0.0%) | 98 | Attribute | Pitch condition and par score grouping. |
| `venue_country` | `STRING` | `'India'`, `'Australia'`, `'West Indies'` | 0 (0.0%) | 17 | Attribute | Geographic condition context (subcontinent vs pace/bounce). |
| `home_team_id` | `INTEGER` | `28`, `18`, `20` | 0 (0.0%) | 36 | Foreign Key -> `teams.team_id` | Identifies home side. |
| `home_team` | `STRING` | `'West Indies'`, `'India'` | 0 (0.0%) | 36 | Attribute | Team label. |
| `away_team_id` | `INTEGER` | `22`, `28`, `27` | 0 (0.0%) | 36 | Foreign Key -> `teams.team_id` | Identifies away side. |
| `away_team` | `STRING` | `'England'`, `'Sri Lanka'` | 0 (0.0%) | 36 | Attribute | Team label. |
| `home_team_captain_id`| `INTEGER` | `494`, `126`, `250` | 44 (5.0%) | 89 | Foreign Key -> `players.player_id` | Leadership analysis (null in unplayed matches). |
| `away_team_captain_id`| `INTEGER` | `478`, `1596`, `494` | 45 (5.1%) | 98 | Foreign Key -> `players.player_id` | Leadership analysis. |
| `toss_win_team_id` | `INTEGER` | `28`, `22`, `18` | 15 (1.7%) | 37 | Foreign Key -> `teams.team_id` | Toss outcome. |
| `toss_opted` | `STRING` | `'Fielding'`, `'Batting'` | 15 (1.7%) | 2 | Attribute | Tactical match context (chase vs defend strategy). |
| `man_of_the_match` | `INTEGER` | `0`, `4986`, `1699` | 0 (0.0%) | 293 | Foreign Key -> `players.player_id` | High-impact clutch match performances (0 = no award). |
| `first_inn_revised_overs`| `INTEGER` | `114`, `84`, `66` | 858 (97.2%) | 13 | Attribute | **Rain / DLS context:** Stored as total balls allocated (e.g. 114 balls = 19.0 overs). |
| `second_inn_revised_overs`| `INTEGER` | `114`, `42`, `48` | 858 (97.2%) | 12 | Attribute | **Rain / DLS context:** Balls allocated for run chase. |
| `revised_target` | `INTEGER` | `143`, `56`, `91` | 860 (97.4%) | 23 | Attribute | **Crucial Pressure Variable:** DLS target required for 2nd innings pressure calculations. |
| `knock_out` | `BOOLEAN / INT` | `0`, `1` | 0 (0.0%) | 2 | Attribute | **Binary macro-pressure flag:** 1 indicates sudden-death knockout match. |
| `win_team_id` | `INTEGER` | `28`, `22`, `18` | 41 (4.6%) | 36 | Foreign Key -> `teams.team_id` | Match outcome (null in 41 abandoned/no-result/tied matches). |
| `result` | `STRING` | `'England Won by 1 Run'`, `'Match Abandoned'` | 0 (0.0%) | 670 | Attribute | Victory margin, chase success, and match finality. Used for Match-Margin Anchoring. |

---

## 4. `competition_team_player_mapping.csv`
- **Total Records:** 6,413 rows
- **Total Columns:** 6
- **Composite Primary Key:** `(comp_id, team_id, player_id)` (Unique: 6,413 / 6,413, Nulls: 0)

| Column Name | Stored / Logical Type | Example Values | Missing Values (%) | Unique Count | Key Classification | Analytical Utility |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `comp_id` | `INTEGER` | `1331`, `1358` | 0 (0.0%) | 140 | Foreign Key -> `competitions.comp_id` | Tourney roster link. |
| `comp_name` | `STRING` | `'IPL 2022'` | 0 (0.0%) | 140 | Attribute | Tourney label. |
| `team_id` | `INTEGER` | `22`, `28`, `18` | 0 (0.0%) | 38 | Foreign Key -> `teams.team_id` | Team entity. |
| `team_name` | `STRING` | `'India'`, `'England'` | 0 (0.0%) | 38 | Attribute | Team label. |
| `player_id` | `INTEGER` | `478`, `1699`, `4722` | 0 (0.0%) | 1217 | Foreign Key -> Player entity | **Canonical Player Identity Key:** Must be used for all player joins. |
| `player_name` | `STRING` | `'Eoin Morgan'`, `'Rashid Khan'` | 0 (0.0%) | 1210 | Attribute | Player label. *Warning:* 7 names have multiple distinct IDs; do not join on name. |

---

## 5. `playing_eleven.csv`
- **Total Records:** 28,381 rows
- **Total Columns:** 9
- **Composite Primary Key:** `(match_id, team_id, player_id)` (Unique: 28,381 / 28,381, Nulls: 0)

| Column Name | Stored / Logical Type | Example Values | Missing Values (%) | Unique Count | Key Classification | Analytical Utility |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `match_id` | `INTEGER` | `13511`, `13512` | 0 (0.0%) | 880 | Foreign Key -> `matches.match_id` | Match linkage. |
| `team_id` | `INTEGER` | `22`, `28` | 0 (0.0%) | 38 | Foreign Key -> `teams.team_id` | Team representation. |
| `player_id` | `INTEGER` | `1187`, `6273` | 0 (0.0%) | 1082 | Foreign Key -> `mapping.player_id` | Player entity. |
| `batting_order` | `INTEGER` | `1`, `2`, `11` | 8678 (30.6%) | 13 | Attribute | Lineup position (1-11); null for bench reserves (`is_played=false`). |
| `is_played` | `BOOLEAN` | `true`, `false` | 0 (0.0%) | 2 | Attribute | **Critical Filter:** Filters active on-field players from bench reserves. |
| `is_captain` | `BOOLEAN` | `false`, `true` | 8667 (30.5%) | 2 | Attribute | On-field captaincy flag. |
| `is_wk` | `BOOLEAN` | `false`, `true` | 8667 (30.5%) | 2 | Attribute | Designated wicketkeeper flag. |
| `is_impact` | `INTEGER` | `0`, `1` | 0 (0.0%) | 2 | Attribute | **IPL Tactical Feature:** 1 indicates player entered as an Impact Player substitution. |
| `is_impact_off` | `INTEGER` | `0`, `1` | 0 (0.0%) | 2 | Attribute | 1 indicates player was subbed out via Impact Player rule. |

---

## 6. `ball_by_ball.csv`
- **Total Records:** 200,999 rows
- **Total Columns:** 33
- **Composite Primary Key:** `(match_id, innings, overid, over_ball_num)` (Unique: 200,999 / 200,999, Nulls: 0)
- **Alternate Primary Key:** `(match_id, innings, innings_ball_num)` (Unique: 200,999 / 200,999, Nulls: 0)

| Column Name | Stored / Logical Type | Example Values | Missing Values (%) | Unique Count | Key Classification | Analytical Utility |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `match_id` | `INTEGER` | `13511`, `14112` | 0 (0.0%) | 867 | Foreign Key -> `matches.match_id` | Core match event link. |
| `innings` | `INTEGER` | `1`, `2`, `3`, `4` | 0 (0.0%) | 4 | Attribute | 1=First innings, 2=Chase innings, 3/4=Super Over ($\kappa_{\text{stage}} = 1.35$). |
| `overid` | `INTEGER` | `1`, `2`, `20` | 0 (0.0%) | 20 | Attribute | Over index (1-indexed: 1 = 1st over, 20 = 20th over). |
| `over_ball_num` | `INTEGER` | `1`, `2`, `6`, `13` | 0 (0.0%) | 13 | Attribute | Delivery count within over (exceeds 6 on wides/no-balls). |
| `innings_ball_num` | `INTEGER` | `1`, `2`, `120`, `136` | 0 (0.0%) | 136 | Attribute | Sequential delivery counter across entire innings. |
| `batting_team_id` | `INTEGER` | `22`, `28` | 0 (0.0%) | 38 | Foreign Key -> `teams.team_id` | Batting team entity. |
| `bowling_team_id` | `INTEGER` | `28`, `22` | 0 (0.0%) | 38 | Foreign Key -> `teams.team_id` | Bowling team entity. |
| `striker_id` | `INTEGER` | `1187`, `1699` | 0 (0.0%) | 888 | Foreign Key -> Player entity | Batter facing delivery. |
| `striker_name` | `STRING` | `'Jason Roy'`, `'Jos Buttler'` | 0 (0.0%) | 885 | Attribute | Batter label. |
| `non_striker_id` | `INTEGER` | `6273`, `1210` | 0 (0.0%) | 867 | Foreign Key -> Player entity | Batter at bowler's end. |
| `non_striker_name` | `STRING` | `'Tom Banton'` | 0 (0.0%) | 864 | Attribute | Non-striker label. |
| `bowler_id` | `INTEGER` | `1772`, `4722` | 0 (0.0%) | 647 | Foreign Key -> Player entity | Active bowler delivering ball. |
| `bowler_name` | `STRING` | `'Sheldon Cottrell'`, `'Rashid Khan'`| 0 (0.0%) | 646 | Attribute | Bowler label. |
| `batting_type` | `STRING` | `'RHB'`, `'LHB'` | 0 (0.0%) | 2 | Attribute | Right/Left hand batter match-up context. |
| `bowling_type` | `STRING` | `'Right-arm Fast'`, `'Slow left-arm orthodox'`| 0 (0.0%) | 12 | Attribute | Specific bowling style match-up. |
| `batting_order` | `INTEGER` | `1`, `2`, `11` | 0 (0.0%) | 13 | Attribute | Batter position in batting card. |
| `runs` | `INTEGER` | `0`, `1`, `2`, `4`, `6` | 0 (0.0%) | 7 | Attribute | **Runs scored by batter off the bat.** (0 on wides). |
| `is_four` | `BOOLEAN` | `false`, `true` | 0 (0.0%) | 2 | Attribute | Boundary 4 flag. |
| `is_six` | `BOOLEAN` | `false`, `true` | 0 (0.0%) | 2 | Attribute | Boundary 6 flag. |
| `is_wicket` | `BOOLEAN` | `false`, `true` | 0 (0.0%) | 2 | Attribute | Wicket fall indicator (10,881 true). |
| `dismissal_type_id` | `INTEGER` | `1`, `2`, `5` | 190,118 (94.6%) | 8 | Attribute | Numeric dismissal category code. |
| `dismissal_type` | `STRING` | `'Bowled'`, `'Caught'`, `'RunOut'` | 190,118 (94.6%) | 9 | Attribute | **Wicket classification:** Used to credit bowler vs fielding. (Bowler credited only on Bowled, Caught, LBW, Stump, Hit Wicket). |
| `dismissed_player_id`| `INTEGER` | `1187`, `6273` | 190,107 (94.6%) | 814 | Foreign Key -> Player entity | Player dismissed. *(Note: 12 rows have ID populated but is_wicket=false indicating Retired Hurt).* |
| `extras_type` | `STRING` | `'None'`, `'wide'`, `'legbyes'`, `'Overstep'`, `'other'`, `'byes'`, `'Penalty'`| 0 (0.0%) | 7 | Attribute | Extra category. **Crucial:** `'other'` (264 rows) = Non-Overstep No-Balls. `'Penalty'` (1 row) = +5 team runs under MCC Law 41/42. |
| `extras1_runs` | `INTEGER` | `1`, `2`, `3`, `4`, `5`, `6`, `7` | 0 (0.0%) | 7 | Attribute | **CATEGORICAL ENUM CODE for `extras_type`, NOT runs!** (1=Overstep, 2=wide, 3=legbyes, 4=byes, 5=other, 6=None, 7=Penalty). |
| `extras_2_runs` | `INTEGER` | `0`, `1`, `4` | 0 (0.0%) | 3 | Attribute | Additional extra runs recorded in rare no-ball instances (36 rows non-zero). |
| `pace_or_spin` | `STRING` | `'Pace'`, `'Spin'` | 0 (0.0%) | 2 | Attribute | Macro bowling classification. |
| `bowl_speed` | `FLOAT` | `0.0`, `138.4`, `145.2` | 0 (0.0%) | 1033 | Attribute | Ball speed in km/h (0 when unmeasured or spin). |
| `stroke` | `STRING` | `'Cover Drive'`, `'Pull'`, `'Flick'` | 12 (0.0%) | 31 | Attribute | Batter shot selection (biomechanical/tactical profiling). |
| `delivery_style` | `STRING` | `'Inswing'`, `'Yorker'`, `'Bouncer'` | 7 (0.0%) | 35 | Attribute | Bowler delivery trajectory/style (Yorker, Bouncer, Slower ball, Inswing/Outswing). |
| `over_or_around` | `STRING` | `'Over'`, `'Around'` | 407 (0.2%) | 2 | Attribute | Bowler angle around the wicket. |
| `on_or_off` | `STRING` | `'Off-side'`, `'On-side'` | 0 (0.0%) | 2 | Attribute | Direction of delivery / shot. |
| `delivery_ist_time` | `TIMESTAMP` | `'2022-01-22 20:15:32 UTC'` | 0 (0.0%) | >10000 | Attribute | Exact delivery timestamp. |

---

## 7. Engineered Pre-Delivery State Columns Specification (Phase 2)
In `clean_deliveries.csv`, each delivery is augmented with pre-delivery state variables strictly preventing temporal leakage:
- `pre_team_score`: Score before delivery $t$.
- `post_team_score`: `pre_team_score + team_runs_on_ball`.
- `pre_wickets_lost`: Wickets lost before delivery $t$.
- `pre_wickets_in_hand`: $10 - \text{pre\_wickets\_lost}$.
- `pre_legal_balls_bowled`: Legal deliveries completed prior to delivery $t$.
- `pre_balls_remaining`: $\max(1, \text{max\_legal\_balls} - \text{pre\_legal\_balls\_bowled})$.
- `pre_partnership_runs`, `pre_partnership_balls`: Cumulative active partnership stats.
- `pre_consecutive_dots`: Active streak of consecutive dot balls immediately preceding delivery $t$.
- `pre_striker_runs`, `pre_striker_balls`: Cumulative innings performance of the current striker prior to delivery $t$.
- `target_score`: Fixed target (Innings 2 only).
- `pre_runs_needed`: $\max(0, \text{target\_score} - \text{pre\_team\_score})$.
- `pre_crr`: Current run rate prior to ball $t$.
- `pre_rrr`: Required run rate prior to ball $t$.
- `comp_tier`: Tier 1 (`IPL`), Tier 2 (`T20I_FullMember`), Tier 3 (`T20_Associate_Emerging`).
- `opposition_quality_weight`: Pre-match Elo-derived quality weight $\omega_t \in [0.60, 1.35]$.

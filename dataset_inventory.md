# Dataset Forensic Inventory — SupeRR Selector Season 2

**Audit Date:** November 2026 (Updated Phase 1.5)  
**Auditor:** Principal Cricket Data Engineer & Quantitative Researcher  
**Dataset Scope:** Historical IPL and T20 International (T20I) matches from 2022 to 2026.  
**Integrity Status:** 100% Parsed without corruption. Zero encoding failures. Original raw CSV files remain untouched.

---

## 1. Complete File Inventory

| Filename | File Format | File Size (Bytes) | File Size (MB) | Row Count | Column Count | Integrity / Status | Primary Purpose | Inter-File Relationships |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- | :--- | :--- |
| **`competitions.csv`** | CSV | 7,624 | 0.01 MB | 141 | 4 | Clean / OK | Metadata for all covered tournaments, leagues, and bilateral series | Parent table for `matches.csv`, `teams.csv`, and `competition_team_player_mapping.csv` via `comp_id`. |
| **`teams.csv`** | CSV | 6,922 | 0.01 MB | 353 | 3 | Clean / OK | Maps teams to the specific competitions they participated in | Child of `competitions.csv` (`comp_id`); parent to `matches.csv` (`home_team_id`, `away_team_id`) and `playing_eleven.csv` (`team_id`). |
| **`matches.csv`** | CSV | 123,864 | 0.12 MB | 883 | 22 | Clean / OK | Match-level metadata (dates, venues, toss, revised overs/targets, winner, result text) | Child of `competitions.csv` (`comp_id`); parent of `ball_by_ball.csv` and `playing_eleven.csv` via `match_id`. |
| **`competition_team_player_mapping.csv`** | CSV | 462,969 | 0.44 MB | 6,413 | 6 | Clean / OK | Official rosters linking registered players to teams within specific competitions | Bridge table connecting `competitions.csv`, `teams.csv`, and player entities referenced in `playing_eleven.csv` and `ball_by_ball.csv`. |
| **`playing_eleven.csv`** | CSV | 966,287 | 0.92 MB | 28,381 | 9 | Clean / OK | Matchday squads, batting orders, active participation flags, captaincy, wicketkeepers, and impact players | Child of `matches.csv` (`match_id`) and `teams.csv` (`team_id`); maps to players in `ball_by_ball.csv` via `player_id`. |
| **`ball_by_ball.csv`** | CSV | 41,071,609 | 39.17 MB | 200,999 | 33 | Clean / OK | Granular delivery-level event records (runs, extras, wickets, ball speed, stroke, angles, timestamps) | Core transactional fact table. Child of `matches.csv` (`match_id`); references teams (`batting_team_id`, `bowling_team_id`) and players (`striker_id`, `non_striker_id`, `bowler_id`, `dismissed_player_id`). |
| **`Round 1 Problem Statement...pdf`** | PDF | 254,082 | 0.24 MB | N/A | N/A | Clean / OK | Official tournament competition brief and evaluation guidelines | Defines problem boundaries, evaluation criteria, and submission specifications. |

---

## 2. High-Level Dataset Volumes & Summary Metrics

- **Total Matches Recorded:** 883 matches across 141 competitions.
- **Total Deliveries Logged:** 200,999 deliveries across 867 playable matches.
  - *Note:* 16 matches in `matches.csv` have zero deliveries in `ball_by_ball.csv` because they were abandoned without a ball bowled.
- **3-Tier Competition Stratification:**
  - *Critical Discovery:* `match_format == 'T20'` is **not 100% IPL**. Out of 401 matches with format `'T20'`, 371 are IPL, while 30 matches belong to Associate/Emerging tournaments:
    - **Tier 1 (`IPL`):** `comp_id in [1358, 1715, 2193, 2725, 3298]` (371 matches).
    - **Tier 2 (`T20I_FullMember`):** T20I matches where both competing teams are Top-12 ICC Full Members (`India, Australia, England, South Africa, New Zealand, West Indies, Pakistan, Sri Lanka, Bangladesh, Afghanistan, Ireland, Zimbabwe`).
    - **Tier 3 (`T20_Associate_Emerging`):** T20I matches involving Associate nations and `comp_id in [2670, 3289]` (`Mens T20 Emerging Teams Asia Cup 2024` with 15 matches, and `Asia Cup Rising Stars 2025` with 15 matches).
- **Player Universe:**
  - **1,217** unique `player_id`s registered across all competition rosters.
  - **1,082** unique `player_id`s named in matchday squads (`playing_eleven.csv`).
  - **958** unique active players engaged in ball-by-ball events (888 batters faced ≥ 1 ball; 647 bowlers bowled ≥ 1 legal ball).
  - **100% referential integrity:** Every player appearing in `ball_by_ball.csv` exists in `competition_team_player_mapping.csv`.

---

## 3. Structural File Interdependency Graph

```text
                  +-------------------+
                  |  competitions.csv |
                  +---------+---------+
                            |
           +----------------+----------------+
           |                                 |
           v                                 v
    +---------------+             +-----------------------+
    |   teams.csv   |             |      matches.csv      |
    +-------+-------+             +-----------+-----------+
            |                                 |
            +----------------+----------------+
                             |
                             v
                  +---------------------+
                  |  playing_eleven.csv |
                  +----------+----------+
                             |
                             v
           +------------------------------------+
           | competition_team_player_mapping.csv|
           +-----------------+------------------+
                             |
                             v
                  +---------------------+
                  |  ball_by_ball.csv   |
                  +---------------------+
```

---

## 4. Empirical Discovery Patches (Phase 1.5)

1. **The Hidden No-Ball Trap (`extras_type == 'other'`):**  
   All 264 rows where `extras_type == 'other'` (`extras1_runs == 5`) are **Non-Overstep No-Balls** (e.g., waist-high full tosses, fielding restriction breaches). In 130 of 132 complete overs containing a single `'other'` delivery and no wides/oversteps, the over required 7 balls (`over_ball_num` reaches 7), batters scored up to 6 runs off the bat (42 boundaries of 4, 26 sixes), and 3 run outs occurred.  
   *Engineering Rule:* Both `'Overstep'` (576 rows) and `'other'` (264 rows) = **840 total No-Balls**. Both add `+1` penalty run to team score and bowler runs conceded, are excluded from bowler legal balls, and count as batter balls faced.

2. **The `'Penalty'` Delivery (`extras_type == 'Penalty'`):**  
   The single delivery in Match `16753` (Innings 2, Over 6.4, `extras1_runs == 7`) represents `+5` penalty runs awarded under MCC Law 41/42. Concedes 0 bowler runs, 0 legal balls, and 0 batter balls faced.

3. **Deterministic Striker-Rotation Parity & Match-Margin Anchoring:**  
   Next-ball striker parity deterministically identifies whether batters physically crossed (odd vs even runs) on byes, leg-byes, and wides, enabling exact reconciliation against `matches.result` margins.

---

## 5. Integrity Verdict
All files are intact, non-empty, and structurally sound. Original CSV files remain untouched and immutable throughout all pipeline stages.

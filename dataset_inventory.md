# Dataset Forensic Inventory — SupeRR Selector Season 2

**Audit Date:** November 2026  
**Auditor:** Automated Data Forensic System  
**Dataset Scope:** Historical IPL and T20 International (T20I) matches from 2022 to 2026.  
**Integrity Status:** 100% Parsed without corruption. Zero encoding failures. Original CSV files remain untouched.

---

## 1. Complete File Inventory

| Filename | File Format | File Size (Bytes) | File Size (MB) | Row Count | Column Count | Integrity / Status | Primary Purpose | Inter-File Relationships |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
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
- **Competitions & Formats:**
  - **T20 Internationals (T20I):** 482 matches across 136 series/tournaments.
  - **Domestic T20 (IPL):** 401 matches across 5 IPL seasons (IPL 2022, 2023, 2024, 2025, 2026).
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

## 4. Integrity Verdict
All files are intact, non-empty, and structurally sound. CSV parsing yields zero syntax exceptions or misaligned delimiters.

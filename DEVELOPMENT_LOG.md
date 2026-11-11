# Development Log

## Project Status
In Progress — Phase 1 (Dataset Forensic Audit) Completed. Ready for Approval Gate 1.

## Current Phase
Phase 1 — Dataset Forensic Audit.

## Completed Work
- Completed full file inventory of all raw CSV files, schemas, and problem statement documentation.
- Formally audited schemas, null profiles, distinct counts, and candidate primary/foreign keys across all 6 CSV tables (77 total columns).
- Mapped all entity relationships, join paths, and cardinalities between Competitions, Teams, Matches, Playing XIs, Rosters, and Deliveries.
- Uncovered critical domain-specific findings:
  - `extras1_runs` is a categorical code (1–7) corresponding to `extras_type`, NOT actual run counts.
  - 12 deliveries with `is_wicket=False` and blank dismissal types have populated `dismissed_player_id` representing **Retired Hurt** events (e.g., Rohit Sharma back spasm, Sanju Samson).
  - 7 player names have multiple distinct player IDs (e.g. Rashid Khan, Abdul Samad, Haider Ali), mandating strict grouping by `player_id`.
  - 16 matches in `matches.csv` were abandoned without play and have 0 deliveries in `ball_by_ball.csv`.
- Evaluated feasibility of all cricket metrics and pressure variables for 1st innings (target setting) and 2nd innings (chasing).
- Defined mathematical requirements for Bayesian shrinkage, context adjustment, bootstrap confidence intervals, and separate batting/bowling indices.
- Generated the 6 required audit deliverables in `data/audit/` and repository root.

## Decisions Made
- Never group, filter, or join on `player_name`; always use canonical `player_id`.
- Never sum `extras1_runs` as run values; derive extras penalty runs using ICC rules.
- Do not credit bowlers for RunOuts (600), Retired Out (6), Obstructing the field (3), or Retired Hurt (12).
- Exclude 16 rain-abandoned matches from delivery-level feature engineering.
- Measure sample size thresholds for eligibility: $\ge 75$ pressure balls faced for batters; $\ge 60$ pressure balls bowled for bowlers.

## Known Issues & Limitations
- Multi-run byes/leg-byes are not broken down in `ball_by_ball.csv` (recorded as 0 runs off the bat with byes/legbyes flag). This creates a minor (<1.5%) difference in total cumulative team scores, but has zero impact on individual batter runs or bowler wickets.
- No raw 3D trajectory tracking or field-placement coordinates exist in the dataset; all pressure modeling will rely on match situation state (RRR, phase, wickets in hand, balls remaining, tournament leverage).

## Pending Tasks
- Await Phase 1 approval gate sign-off before commencing Phase 2 (Data Engineering & Feature Extraction).

## Next Approval Gate
Phase 1 Sign-Off -> Approval to proceed to Phase 2 (Data Engineering).


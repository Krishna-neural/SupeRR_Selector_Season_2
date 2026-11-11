# Development Log

## Project Status
In Progress — Phase 1, Phase 1.5, and Phase 2 Completed. Reached Phase 2 Checkpoint.

## Current Phase
Phase 2 Checkpoint — Data Engineering & Pre-Delivery State Engine Complete (Awaiting Sign-Off before Phase 3).

## Completed Work
- **Phase 1:** Complete forensic dataset audit and inventory across all 6 raw CSV files and documentation PDF.
- **Phase 1.5:**
  - Upgraded all 5 audit documents (`data_quality_report.md`, `dataset_schema.md`, `dataset_inventory.md`, `pressure_variable_feasibility.md`, `recommended_analytical_methodology.md`).
  - Added empirical finding: All 264 `'other'` rows are Non-Overstep No-Balls (`extras1_runs == 5`), combined with `'Overstep'` (576) to form 840 total No-Balls.
  - Added empirical finding: Exactly 1 `'Penalty'` row (Match 16753, Inn 2 Over 6.4) adding +5 team runs under MCC Law 41/42.
  - Implemented next-ball Striker-Rotation Parity ($\mathcal{C}_t$) and Match-Margin Anchoring.
  - Stratified competitions into 3 tiers: Tier 1 (IPL), Tier 2 (T20I Full Member), Tier 3 (Associate/Emerging).
  - Wrote the complete mathematical blueprint for Phases 3–6 into `recommended_analytical_methodology.md` (Quantum/Shannon Entropy, DTMC Leverage, Gaussian RRR Knife-Edge factor, Context-Adjusted VAOE/xRWA, Empirical Bayes Shrinkage, Sortino Downside Semi-Deviation, and Match-Level Block Bootstrap).
- **Phase 2:**
  - Developed and executed high-performance pipeline `src/phase2_pipeline.py`.
  - Generated all 4 processed datasets: `clean_deliveries.csv` (200,999 rows, 71 cols), `match_context.csv` (883 rows, 39 cols), `player_match_batting.csv` (13,754 rows, 23 cols), `player_match_bowling.csv` (10,106 rows, 30 cols).
  - Implemented automated `pytest` test suite `tests/test_phase2_validation.py` with 9 comprehensive tests (100% passed in 4.13s).
  - Authored `data_validation_report.md` with complete manual scorecard reconciliations for Match 16064 (Rohit Sharma Retired Hurt), Match 13513 ('other' no-balls), and Match 13612 (DLS chase).

## Decisions Made
- `extras_type in ('Overstep', 'other')` are combined as No-Balls (`is_noball = True`, 840 rows).
- 12 deliveries with `is_wicket=False` and populated `dismissed_player_id` are flagged `is_retired_hurt=True` (treated as Not Out, 0 bowler wickets, 0 team wickets lost).
- Bowler wickets strictly filtered to Bowled, Caught, LBW, Stump, Hit Wicket (exactly 10,272 bowler wickets).
- Strict Pre-Delivery Anti-Leakage enforced across all 200,999 rows.
- Dynamic Team Elo initialized across 3 tiers (1550 IPL, 1500 Full Member, 1300 Associate) and updated chronologically ($K = 24$).

## Known Issues & Limitations
- All known schema and domain anomalies have been identified, handled, and verified against official match results.
- No further unaddressed discrepancies remain in the Phase 2 feature sets.

## Pending Tasks
- User review of Phase 2 checkpoint scorecards and validation report.
- Upon approval, proceed to Phase 3 (Pressure Index Modeling).

## Next Approval Gate
Phase 2 Checkpoint Sign-Off -> Approval to unlock Phase 3 (Pressure Modeling).



# Development Log

## Project Status
In Progress — Phase 1, Phase 1.5, Phase 2, and Phase 3 Completed. Reached Phase 3 Approval Checkpoint.

## Current Phase
Phase 3 Checkpoint — Pressure Index Research & Development Complete (Awaiting Sign-Off before Phase 4).

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
- **Phase 3:**
  - Researched, implemented, and compared three candidate pre-delivery pressure models (`pressure_model_a_rule`, `pressure_model_b_percentile`, and `pressure_model_c_quantum_leverage`) in `src/pressure_index.py`.
  - Validated Win Probability surfaces using 5-fold cross-validation: Innings 2 ROC AUC = `0.9021 ± 0.0010` (Brier: `0.1271`), Innings 1 ROC AUC = `0.7192 ± 0.0032`.
  - Selected Model C (Win Probability Shannon Entropy $H_t$ + DTMC Counterfactual Leverage $\mathcal{L}_t$) as Champion Model.
  - Formulated asymmetric role indices (`batting_pressure_index` and `bowling_pressure_index`) accounting for micro-situational stressors (dot-ball entrapment, new-batter-in-middle/death, set-batter defense).
  - Formulated four stratified pressure tiers: Low ($< P_{40}$, 39.99%), Moderate ($P_{40} \le P < P_{70}$, 30.00%), High ($P_{70} \le P < P_{90}$, 20.00%), Extreme ($\ge P_{90}$ + Super Overs, 10.00%).
  - Confirmed 100% Extreme classification for Super Overs ($P = 98.00$) with a 34.21% wicket rate.
  - Confirmed mathematical dead-chase immunity (dead chase mean pressure = 14.82 vs knife-edge = 66.45).
  - Confirmed Powerplay collapse sensitivity (collapse PP mean pressure = 67.22 vs normal PP = 58.11).
  - Executed automated `pytest` suite `tests/test_phase3_pressure.py` and full regression suite: 17/17 tests passed (100% in 9.30s).
  - Generated `pressure_distribution.csv` (13 stratum metrics across categories, innings, phases, tiers).
  - Updated `clean_deliveries.csv` (now 200,999 rows, 86 columns).
  - Authored comprehensive documentation: `pressure_model_research.md` and `pressure_validation_report.md`.

## Decisions Made
- **Primary Champion Model:** Candidate Model C (Win Probability Shannon Entropy $H_t$ + DTMC Counterfactual Leverage $\tilde{\mathcal{L}}_t$) is adopted for all downstream player evaluations.
- **High-Pressure Threshold:** Set to empirical $P_{70} = 65.57$ (`is_high_pressure = True` for top 30.01% deliveries, providing 172 qualified batters and 170 qualified bowlers with $\ge 100$ balls).
- **Continuous Weighting:** Quadratic weight $\omega_t = (P_C / 100.0)^2$ used for Phase 4 residual evaluation to suppress routine balls and magnify crucible moments.
- **Super Overs:** Unconditionally pinned to Extreme tier ($P = 98.00$, $\omega = 0.9604$).

## Known Issues & Limitations
- All 17 automated tests pass with zero failures and zero NaNs.
- No remaining unaddressed issues in Phase 3.

## Pending Tasks
- User review of Phase 3 deliverables, threshold sensitivity, and situational walkthroughs.
- Upon approval, proceed to Phase 4 (Player Value Added Above Expected & Residual Modelling).

## Next Approval Gate
Phase 3 Checkpoint Sign-Off -> Approval to unlock Phase 4 (Residual Performance Modelling).




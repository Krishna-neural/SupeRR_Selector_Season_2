# Pressure Variable Feasibility & Cricket Data Understanding — SupeRR Selector Season 2

**Objective:** Audit the availability, derivability, and mathematical feasibility of match context variables for constructing a scientifically defensible pressure index.

---

## 1. Cricket Metric Feasibility Matrix

| Cricket Metric | Feasible from Raw Data? | Source Columns Used | Derivation Methodology / Limitations |
| :--- | :---: | :--- | :--- |
| **Batter Runs** | **Yes (100% Exact)** | `striker_id`, `runs` | Cumulative sum of `runs` per batter. Wides are excluded. |
| **Batter Balls Faced** | **Yes (100% Exact)** | `striker_id`, `extras_type` | Count of deliveries faced where `extras_type != 'wide'`. No-balls (Overstep) count as balls faced under ICC laws. |
| **Legal Deliveries** | **Yes (100% Exact)** | `extras_type` | Count of deliveries where `extras_type not in ('wide', 'Overstep')`. Exactly 6 legal deliveries per standard over. |
| **Bowler Runs Conceded**| **Yes (~99.5% Exact)**| `bowler_id`, `runs`, `extras_type`, `extras_2_runs` | `runs` off the bat + 1 for wide + 1 for Overstep + `extras_2_runs`. Legbyes and byes are correctly excluded from bowler charges. Minor unrecorded runs on multi-run wides. |
| **Bowler Wickets** | **Yes (100% Exact)** | `is_wicket`, `dismissal_type` | `is_wicket == True` AND `dismissal_type in ('Bowled', 'Caught', 'LBW', 'Stump', 'Hit Wicket')`. Run outs (600), Retire Out (6), and Obstructing field (3) are excluded. |
| **Dismissal Types** | **Yes (100% Exact)** | `dismissal_type` | 9 categories available in raw data. |
| **Overs & Balls** | **Yes (100% Exact)** | `overid`, `over_ball_num`, `innings_ball_num` | `overid` (1 to 20), `over_ball_num` (1 to 13), `innings_ball_num` (1 to 136). |
| **Innings** | **Yes (100% Exact)** | `innings` | 1 (1st innings), 2 (2nd innings chase), 3/4 (Super Over). |
| **Cumulative Score** | **Yes (~99.0% Exact)**| `runs`, `extras_type`, `extras_2_runs` | Cumulative sum of batter runs + standard extras penalty (1 for wide/no-ball) + `extras_2_runs`. Minor unrecorded bye/legbye multi-runs. |
| **Wickets Lost** | **Yes (100% Exact)** | Cumulative sum of `is_wicket` | Exactly tracks batting team wickets down (0 to 10). |
| **Balls Remaining** | **Yes (100% Exact)** | `overid`, `over_ball_num`, `extras_type`, `revised_overs` | Calculated via legal deliveries remaining: $120 - \text{cumulative\_legal\_balls}$ (or revised ball quota for rain matches). |
| **Target Score** | **Yes (100% Exact)** | Innings 1 total OR `matches.revised_target` | For regular matches: $\text{Innings 1 Total} + 1$. For DLS matches: `matches.revised_target`. |
| **Required Run Rate** | **Yes (100% Exact)** | `runs_needed`, `legal_balls_remaining` | $\text{RRR} = \frac{\text{Runs Needed}}{\text{Legal Balls Remaining} / 6}$. Feasible for every ball in Innings 2. |
| **Innings Phase** | **Yes (100% Exact)** | `overid` | Powerplay: Overs 1–6 (64,046 balls); Middle: Overs 7–15 (92,499 balls); Death: Overs 16–20 (44,454 balls). |
| **Match Outcome** | **Yes (100% Exact)** | `matches.win_team_id`, `result` | Victory margin, chase success, defending team win, super over result. |

---

## 2. Pressure Feasibility by Game Context

```
                         PRESSURE CONTEXT MATRIX
┌───────────────────────────────────────┬───────────────────────────────────────┐
│           FIRST INNINGS               │            SECOND INNINGS             │
├───────────────────────────────────────┼───────────────────────────────────────┤
│ Context: Target setting under         │ Context: Chasing a known target       │
│ uncertainty.                          │ under finite ball constraints.        │
│                                       │                                       │
│ Available Pressure Signals:           │ Available Pressure Signals:           │
│ 1. Collapse Pressure: Wickets down    │ 1. Required Run Rate (RRR):           │
│    early (e.g. >= 3 down in PP).      │    Escalating run rate demands.       │
│ 2. Phase Pressure: Death overs        │ 2. Wickets in Hand vs Runs Needed.    │
│    (overs 16-20) acceleration.        │ 3. Phase Pressure: Death overs        │
│ 3. Dot-ball Pressure: consecutive dots│    (overs 16-20) in a tight chase.    │
│ 4. Tournament Stakes: Knockout /      │ 4. Match Closeness: Balls where       │
│    Playoff matches (knock_out=1).     │    win/loss is separated by < 10 runs │
│                                       │    or final over finishes.            │
└───────────────────────────────────────┴───────────────────────────────────────┘
```

### A. Batting Situations Under Pressure
- **Innings 2 (Chasing):**
  - High RRR ($\text{RRR} \ge 10.0$ or $\text{RRR} > \text{Baseline RRR} + 2.5$).
  - High leverage situations: $\le 3$ wickets in hand, requiring $> 8.0$ runs/over.
  - Final overs ($\text{Over} \ge 16$) where runs required is within reach of victory.
- **Innings 1 (Target Setting):**
  - Top-order collapse recovery: Batting when $\ge 3$ wickets have fallen within the Powerplay (Overs 1–6).
  - Death overs acceleration: Maximizing strike rate in Overs 16–20 while protecting wickets.
  - Playoff / Knockout stage: High tournament leverage (`knock_out == 1`).

### B. Bowling Situations Under Pressure
- **Innings 2 (Defending):**
  - Defending tight totals in the Death Overs (Overs 16–20) where the chasing team requires $\le 10$ runs per over.
  - Breaking threatening partnerships (bowling to top batters who have high scoring momentum).
  - High leverage death-over boundary containment (dot balls and boundary prevention).
- **Innings 1 (Restriction):**
  - Powerplay restriction: bowling against attacking openers.
  - Death over containment: bowling overs 18, 19, 20 against designated finishers.
  - Playoff / Knockout stage.

---

## 3. Explicit Inventory of Unavailable Variables

To maintain scientific integrity, the following variables are **not available** in the raw datasets and cannot be fabricated:
1. **Field Placements:** No data on fielder coordinates, boundary riders, or slip cordons.
2. **Pitch / Trajectory Coordinates:** No Hawk-Eye 3D tracking coordinates (only textual `stroke`, `delivery_style`, `pace_or_spin`, and `on_or_off`).
3. **Pre-Calculated Win Probability:** There is no vendor win-probability column; win probability or leverage must be derived from empirical cricket formulas (e.g., Duckworth-Lewis-Stern curves, empirical chase completion tables, or RRR/wickets-in-hand leverage indices).
4. **Exact Bye / Leg-Bye Magnitudes:** As noted in the audit, multi-run byes/leg-byes are not broken down; however, this affects only ~1.6% of team totals and has 0.0% impact on individual batter runs or bowler wickets.

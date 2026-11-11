# Recommended Analytical & Mathematical Methodology — SupeRR Selector Season 2

**Scope:** Feasibility analysis and mathematical specification of recommended statistical methodologies for pressure modeling, reliability estimation, and player ranking.

---

## 1. Evaluation of Statistical Methodologies

| Methodology | Feasible with Available Data? | Mathematical Justification & Input Requirements |
| :--- | :---: | :--- |
| **Multi-Factor Pressure Index (MPI)** | **Fully Feasible** | Inputs: `innings`, `overid`, `runs_needed`, `balls_remaining`, `wickets_in_hand`, `knock_out`. Allows every delivery to be assigned a continuous pressure score $P \in [0, 100]$ or categorized into High/Medium/Low pressure tiers. |
| **Context-Adjusted Performance** | **Fully Feasible** | Inputs: Phase (PP, Middle, Death), Venue country, Pace vs Spin, Batting order. Normalizes batter strike rates and bowler economy rates relative to match-phase and opposition baselines. |
| **Bayesian Shrinkage (Empirical Bayes)** | **Fully Feasible & Strongly Recommended** | Inputs: Sample sizes ($N_{\text{balls}}$), player raw performance, cohort prior distribution. Solves the small sample size problem (e.g. a batter who faced only 15 balls hitting 3 sixes will be shrunk toward the cohort mean, preventing spurious high rankings). |
| **Bootstrap Confidence Intervals** | **Fully Feasible** | Inputs: Delivery-level event vectors per player. By resampling deliveries with replacement ($B = 1000$ iterations), we compute empirical 95% confidence intervals for pressure rating and rank stability. |
| **Pressure Differential (Delta Metric)** | **Fully Feasible** | Inputs: $\text{Performance}_{\text{Pressure}} - \text{Performance}_{\text{Baseline}}$. Measures whether a player's performance escalates or declines under pressure relative to their own standard baseline. |
| **Consistency / Variance Analysis** | **Fully Feasible** | Inputs: Match-level aggregated performance. Measures inter-match variance $\sigma^2$ to distinguish consistent clutch performers from volatile one-hit wonders. |
| **Tournament / Format Weighting** | **Fully Feasible** | Inputs: `match_format` (`T20` vs `T20I`) and `comp_name` (IPL vs Bilateral vs World Cup). Allows adjusting for strength of competition. |

---

## 2. Mathematical Framework Specification

### A. Pressure Index Formulation ($P_{\text{ball}}$)
For any delivery $i$, pressure is a function of situational state variables:

#### Second Innings (Run Chase):
$$P_{\text{chase}} = w_1 \cdot \left(\frac{\text{RRR}}{\text{Target RRR}_0}\right) + w_2 \cdot \left(1 - \frac{\text{Wickets in Hand}}{10}\right) + w_3 \cdot \left(\frac{120 - \text{Balls Rem}}{120}\right) + w_4 \cdot \text{KnockoutFlag}$$

Where:
- $\text{RRR} = \frac{\text{Runs Needed}}{\text{Legal Balls Remaining} / 6}$
- $\text{Target RRR}_0 = \frac{\text{Target}}{20}$
- Weights $w_1, w_2, w_3, w_4$ are calibrated via game-leverage curves.

#### First Innings (Target Setting):
$$P_{\text{first}} = w_1 \cdot \text{CollapseFactor} + w_2 \cdot \text{DeathOversFactor} + w_3 \cdot \text{KnockoutFlag}$$
Where:
- $\text{CollapseFactor} = \max\left(0, \frac{3 - \text{Wickets in Hand at Over 6}}{3}\right)$
- $\text{DeathOversFactor} = \frac{\max(0, \text{Over} - 15)}{5}$

Deliveries with $P \ge P_{\text{threshold}}$ (e.g., top 30th percentile of match pressure) are classified as **High Pressure Deliveries**.

---

### B. Batting Reliability Under Pressure
Batting under pressure requires balancing **Scoring Speed (Strike Rate)**, **Boundary Ability**, and **Wicket Preservation (Average/Survival)**:

1. **Pressure Strike Rate Index ($\text{PSRI}$):**
   $$\text{PSRI}_i = \frac{\text{Runs}_{\text{pressure}, i}}{\text{Balls Faced}_{\text{pressure}, i}} \times 100$$
2. **Pressure Average / Dismissal Cost ($\text{PA}_i$):**
   $$\text{PA}_i = \frac{\text{Runs}_{\text{pressure}, i}}{\max(1, \text{Dismissals}_{\text{pressure}, i})}$$
3. **Bayesian Shrinkage Formulation:**
   $$\theta_{\text{shrunk}, i} = \frac{N_i}{N_i + K} \cdot \bar{X}_i + \frac{K}{N_i + K} \cdot \mu_{\text{prior}}$$
   Where $N_i$ is balls faced under pressure, and $K$ is the empirical shrinkage constant determined by cohort variance.
4. **Reliability Index ($\text{BRI}$):**
   $$\text{BRI}_i = \alpha \cdot \text{Performance}_{\text{Pressure, shrunk}} + \beta \cdot (\text{Performance}_{\text{Pressure}} - \text{Performance}_{\text{Baseline}}) - \gamma \cdot \sigma_{\text{match-to-match}}$$

---

### C. Bowling Reliability Under Pressure
Bowling under pressure requires **Run Containment (Economy)**, **Dot Ball Creation**, and **Clutch Wickets**:

1. **Pressure Economy Delta ($\Delta \text{Econ}_j$):**
   $$\Delta \text{Econ}_j = \text{Econ}_{\text{baseline}, j} - \text{Econ}_{\text{pressure}, j}$$
   *(Positive value indicates bowler constricts scoring rate under pressure compared to normal overs).*
2. **Pressure Dot Ball Ratio ($\text{DotRatio}_j$):**
   $$\text{DotRatio}_j = \frac{\text{Dot Balls}_{\text{pressure}, j}}{\text{Legal Deliveries}_{\text{pressure}, j}}$$
3. **Clutch Wicket Strike Rate ($\text{CWSR}_j$):**
   $$\text{CWSR}_j = \frac{\text{Legal Deliveries}_{\text{pressure}, j}}{\max(1, \text{Clutch Wickets}_j)}$$
4. **Bayesian Shrunk Bowling Rating ($\text{BWI}_j$):**
   $$\text{BWI}_j = \frac{N_j}{N_j + K_b} \cdot \text{Metric}_j + \frac{K_b}{N_j + K_b} \cdot \mu_{\text{prior, bowl}}$$

---

## 3. Sample Size Eligibility Criteria

Based on our empirical analysis of player ball volumes:
- **Batters:**
  - Full dataset has 888 batters; 326 faced $\ge 100$ balls; 189 faced $\ge 250$ balls.
  - Under pressure (~30% of deliveries), a minimum threshold of **$\ge 75$ pressure balls faced** ensures a robust, defensible candidate pool of ~100-120 proven international and IPL batters.
- **Bowlers:**
  - Full dataset has 647 bowlers; 309 bowled $\ge 120$ balls (20 overs); 183 bowled $\ge 300$ balls (50 overs).
  - Under pressure, a minimum threshold of **$\ge 60$ pressure balls bowled (10 pressure overs)** ensures a defensible candidate pool of ~80-100 elite bowlers.
- **Cross-Competition Representation:**
  - Must have participated in at least 5 matches across IPL or recognized T20 Internationals to ensure consistency across tournaments.

---

## 4. Next Phase Gate Alignment
This methodology directly fulfills all requirements of Phase 1. It bridges seamlessly into **Phase 2 (Data Engineering & Feature Extraction)** and **Phase 3 (Pressure Modeling)** without modifying original data or introducing untestable assumptions.

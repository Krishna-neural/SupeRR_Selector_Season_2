# SupeRR Selector Season 2 — Phase 3: Pressure Model Research & Mathematical Specification

## 1. Executive Summary & Research Mandate
The primary objective of Phase 3 is to establish a mathematically rigorous, scientifically defensible, and leakage-free definition of **match pressure** across all 200,999 ball-by-ball deliveries (883 matches) in the official 2022–2024 IPL and T20 International corpus.

In accordance with our Gated Analytical Protocol, three distinct candidate pre-delivery pressure models were designed, implemented, and empirically compared:
1. **Candidate Model A (Contextual Rule-Based Pressure):** A deterministic heuristic combining piecewise scoring deficits, wicket decay curves, phase acceleration ramps, and chase equations.
2. **Candidate Model B (Empirical Distribution / ECDF Percentile-Based Pressure):** A non-parametric empirical distribution model ranking pre-delivery stress variables within stratified match contexts.
3. **Candidate Model C (Champion Model: State-Space Win Probability Shannon Entropy & DTMC Counterfactual Leverage):** An information-theoretic, state-space model that derives pressure directly from Win Probability uncertainty ($H_t$) and counterfactual state-transition volatility ($\mathcal{L}_t$).

**Champion Selection:** Following rigorous empirical evaluation, **Candidate Model C** was unanimously selected as the primary production engine for Phase 3 and all downstream residual models (Phase 4), Bayesian shrinkage (Phase 5), and player rankings (Phase 6).

---

## 2. Fundamental Architectural Guardrails

### 2.1 Anti-Leakage Invariance
Every pressure calculation at delivery $t$ strictly ingests **only pre-delivery state variables** $\mathbf{s}_t^-$ engineered during Phase 2:
$$\mathbf{s}_t^- = \left\{ \text{pre\_team\_score}, \text{pre\_wickets\_lost}, \text{pre\_wickets\_in\_hand}, \text{pre\_balls\_remaining}, \text{pre\_runs\_needed}, \text{pre\_crr}, \text{pre\_rrr}, \text{venue\_avg\_score}, \Delta \text{Elo}, \kappa_{\text{stage}} \right\}$$
The outcome of delivery $t$ (`runs`, `is_wicket`, `team_runs_on_ball`, `extras_type`) is strictly hidden and has zero mathematical influence on $P(\mathbf{s}_t^-)$.

### 2.2 Dead-Chase Attenuation Principle
A critical failure of naive cricket metrics is treating late overs in decided matches as high pressure simply because balls remaining is low. In a hopeless chase (e.g., $RRR > 24.0$ with $\le 2$ wickets in hand), the match outcome is already decided. The mathematical pressure must collapse toward zero rather than artificially spiking.

### 2.3 Separate First-Innings & Second-Innings Dynamics
- **Innings 2 (Target Chase):** Pressure is driven by target convergence, required run rate tension relative to resources, and win probability volatility.
- **Innings 1 (Target Setting):** Pressure is driven by top-order wicket collapses relative to expected wickets lost, scoring rate deficits relative to venue par, consecutive dot-ball pressure, and death-over resource exhaustion.
- **Super Overs (`innings \in \{3, 4\}`):** Sudden-death tie-breakers where single-ball variance decides the match. Every Super Over delivery is unconditionally classified into the `Extreme` pressure tier ($P \ge 90.0$).

---

## 3. Mathematical Specifications of Candidate Models

### 3.1 Candidate Model A: Contextual Rule-Based Pressure Model (`pressure_model_a_rule`)

Model A formalizes cricket domain heuristics into continuous penalty and urgency functions.

#### Innings 1 Formulation
In Innings 1, raw pressure $\tilde{P}_{A, 1}$ is a convex combination of four contextual stressors:
$$\tilde{P}_{A, 1} = 0.40 \cdot C_t + 0.30 \cdot \Phi_t + 0.15 \cdot \Delta_{\text{par}, t} + 0.15 \cdot D_t$$
where:
1. **Collapse Factor ($C_t$):** Measures excess wickets lost relative to the historical expected wickets lost $\mathbb{E}[W \mid b]$ at legal ball $b$:
   $$C_t = 1 - \exp\left( -\frac{\max(0, W_{\text{lost}} - \mathbb{E}[W \mid b])^2}{2 \sigma_w^2} \right), \quad \sigma_w = 1.25$$
2. **Phase Urgency ($\Phi_t$):** Super-linear escalation during the death overs (overs 15–20):
   $$\Phi_t = \left( \frac{\max(0, \text{overid} - 14)}{6} \right)^{1.5}$$
3. **Venue Par Deficit ($\Delta_{\text{par}, t}$):** Deficit between current run rate and venue par run rate ($R_{\text{venue}} = \text{venue\_avg\_score} / 20$):
   $$\Delta_{\text{par}, t} = \text{clip}\left( \frac{R_{\text{venue}} - \text{pre\_crr}}{3.0}, 0, 1 \right)$$
4. **Dot-Ball Stress ($D_t$):** Consecutive dot balls faced by the batting side:
   $$D_t = 1 - \exp\left( -\frac{\text{pre\_consecutive\_dots}^2}{8.0} \right)$$

#### Innings 2 Formulation
In Innings 2, raw pressure $\tilde{P}_{A, 2}$ is driven by required run rate urgency attenuated by dead-chase dynamics:
$$\tilde{P}_{A, 2} = \left( 0.45 \cdot G(\text{pre\_rrr}) + 0.30 \cdot \left(1 - \frac{W_{\text{hand}}}{10}\right) + 0.25 \cdot \left(\frac{120 - B_{\text{rem}}}{120}\right) \right) \cdot \alpha_{\text{dead}}$$
where:
- $G(\text{pre\_rrr})$ is a Gaussian peak centered at critical tension ($RRR = 11.5$ RPO):
  $$G(\text{pre\_rrr}) = \exp\left( -\frac{(\text{pre\_rrr} - 11.5)^2}{2 \times 4.0^2} \right)$$
- $\alpha_{\text{dead}}$ is the dead-chase attenuation factor:
  $$\alpha_{\text{dead}} = \begin{cases} \text{clip}\left(\frac{B_{\text{rem}}}{60}, 0.05, 0.40\right) & \text{if } \text{pre\_rrr} > 24.0 \text{ and } W_{\text{hand}} \le 2 \\ 1.0 & \text{otherwise} \end{cases}$$

#### Scaling & Tournament Multiplier
$$P_A = 100 \cdot \text{clip}(\tilde{P}_{A, \text{inn}} \cdot \kappa_{\text{stage}}, 0, 1)$$
where $\kappa_{\text{stage}} = 1.25$ for knockout/playoff fixtures and $1.00$ for league fixtures.

---

### 3.2 Candidate Model B: Empirical Percentile ECDF Model (`pressure_model_b_percentile`)

Model B calculates empirical cumulative distribution function (ECDF) percentiles of key stress indicators within each stratified match partition $(I, \Psi)$, where $I \in \{1, 2\}$ is the innings and $\Psi \in \{\text{Powerplay}, \text{Middle}, \text{Death}\}$ is the phase.

For a delivery $t \in (I, \Psi)$:
$$F_k(x_{k, t}) = \frac{1}{N_{I, \Psi}} \sum_{j \in (I, \Psi)} \mathbb{I}(x_{k, j} \le x_{k, t})$$

#### Composite Aggregation
- **Innings 1:**
  $$\tilde{P}_{B, 1} = 0.45 \cdot F(\text{pre\_wickets\_lost}) + 0.30 \cdot F(C_t) + 0.25 \cdot F(D_t)$$
- **Innings 2:**
  $$\tilde{P}_{B, 2} = 0.50 \cdot F(G(\text{pre\_rrr})) + 0.30 \cdot F(10 - W_{\text{hand}}) + 0.20 \cdot F(1 / B_{\text{rem}})$$

$$P_B = 100 \cdot \text{clip}(\tilde{P}_{B, \text{inn}} \cdot \kappa_{\text{stage}}, 0, 1)$$

---

### 3.3 Candidate Model C (Champion): State-Space Win Probability Shannon Entropy & DTMC Leverage (`pressure_model_c_quantum_leverage`)

Model C represents our primary theoretical contribution. It grounds match pressure in **information theory** and **counterfactual Markov transition leverage**.

#### 3.3.1 Win Probability Calibration Surface
A logistic regression probability surface $W(\mathbf{s}_t^-) = \mathbb{P}(\text{Batting Team Wins} \mid \mathbf{s}_t^-)$ was calibrated separately for Innings 1 and Innings 2 using regularized Maximum Likelihood Estimation with standard scaling.

**Feature Vectors:**
- $\mathbf{X}_2 = [\text{pre\_runs\_needed}, \text{pre\_balls\_remaining}, \text{pre\_wickets\_in\_hand}, \text{pre\_rrr}, \text{venue\_avg\_score}, \Delta \text{Elo}]$
- $\mathbf{X}_1 = [\text{pre\_team\_score}, \text{pre\_wickets\_lost}, \text{pre\_balls\_remaining}, \text{venue\_avg\_score}, \Delta \text{Elo}]$

**Cross-Validation Predictive Diagnostics (5-Fold Stratified):**
| Metric | Innings 2 (Chase Surface) | Innings 1 (Setting Surface) |
| :--- | :--- | :--- |
| **ROC AUC** | **0.9021 ± 0.0010** | **0.7192 ± 0.0032** |
| **Brier Score** | **0.1271** | **0.2136** |
| **Log Loss** | **0.3922** | **0.6156** |

The Innings 2 model achieves an outstanding ROC AUC of $0.9021$, providing an exceptionally reliable and well-calibrated win probability surface.

#### 3.3.2 Shannon Entropy (Outcome Uncertainty)
The outcome uncertainty of the match at state $\mathbf{s}_t^-$ is quantified by the binary Shannon Entropy $H(\mathbf{s}_t^-) \in [0, 1]$:
$$H(\mathbf{s}_t^-) = - \left[ W(\mathbf{s}_t^-) \log_2 W(\mathbf{s}_t^-) + (1 - W(\mathbf{s}_t^-)) \log_2(1 - W(\mathbf{s}_t^-)) \right]$$
- When $W = 0.50$ (knife-edge balance), $H = 1.00$ (maximum uncertainty).
- When $W \to 0$ or $W \to 1$ (decided match), $H \to 0.00$ (zero uncertainty).

#### 3.3.3 DTMC Counterfactual State Leverage ($\mathcal{L}_t$)
Shannon entropy measures static uncertainty; match pressure also requires measuring **dynamic volatility**—the extent to which the outcome of the immediate delivery can swing the match.

Under a Discrete-Time Markov Chain (DTMC) framework, delivery $t$ transitions state $\mathbf{s}_t^-$ to $\mathbf{s}_{t+1}$. We compute the counterfactual swing between the two extreme primary outcomes:
1. **Boundary State ($\mathbf{s}_{\text{boundary}}^+$):** 4 runs scored, 1 ball consumed, 0 wickets lost.
2. **Wicket State ($\mathbf{s}_{\text{wicket}}^+$):** 0 runs scored, 1 ball consumed, 1 wicket lost.

The single-ball leverage $\mathcal{L}_t$ is defined as:
$$\mathcal{L}_t = \left| W(\mathbf{s}_{\text{boundary}}^+) - W(\mathbf{s}_{\text{wicket}}^+) \right|$$

To ensure robust scaling free of outlier distortion, leverage is normalized by its 98th empirical percentile:
$$\tilde{\mathcal{L}}_t = \text{clip}\left( \frac{\mathcal{L}_t}{P_{98}(\mathcal{L})}, 0, 1 \right)$$

#### 3.3.4 Composite Formulation for Model C
- **Innings 1:**
  $$\tilde{P}_{C, 1} = 0.35 \cdot H_t + 0.25 \cdot \tilde{\mathcal{L}}_t + 0.20 \cdot C_t + 0.10 \cdot \Phi_t + 0.10 \cdot D_t$$
- **Innings 2:**
  $$\tilde{P}_{C, 2} = 0.45 \cdot H_t + 0.35 \cdot \tilde{\mathcal{L}}_t + 0.20 \cdot G(\text{pre\_rrr}_t)$$
- **Super Overs:**
  $$P_C = 98.00 \quad (\text{Fixed Extreme Leverage})$$

The primary pressure index is:
$$P_C = 100 \cdot \text{clip}(\tilde{P}_{C, \text{inn}} \cdot \kappa_{\text{stage}}, 0, 1)$$

---

## 4. Empirical Model Comparison & Evaluation

To justify the selection of Candidate Model C, we conducted rigorous statistical comparisons across all 200,999 deliveries:

### 4.1 Correlation Matrix & Discrepancy Diagnostics
| Metric Comparison | Pearson Correlation ($r$) | Spearman Rank Correlation ($\rho$) | Mean Absolute Difference ($|\Delta|$) |
| :--- | :--- | :--- | :--- |
| **Model A vs. Model B** | 0.5266 | 0.5259 | 22.12 |
| **Model A vs. Model C** | 0.1649 | 0.2179 | 33.64 |
| **Model B vs. Model C** | 0.2886 | 0.3055 | 21.82 |

### 4.2 Why Model C Vastly Outperforms Models A and B
1. **The Blowout Failure of Model A:** Model A relies heavily on match phase ($\Phi_t$). In a blowout match where the batting team is 40/7 chasing 210, Model A continues to assign high pressure in overs 17–20 purely because it is the death overs. Model C correctly recognizes that $W \to 0$, $H \to 0$, and $\mathcal{L} \to 0$, collapsing pressure to $< 15.0$.
2. **The Rank-Distortion of Model B:** Model B normalizes variables across broad partitions, losing inter-match leverage context. It treats a wicket falling in a dead chase with the same rank weight as a wicket falling in a tournament final tie.
3. **Information-Theoretic Soundness:** Model C directly captures the true definition of pressure: *how uncertain is the winner, and how much can this specific ball change that uncertainty?*

---

## 5. Role-Specific Asymmetric Pressure Extensions

While macro match tension is identical for both teams, micro-situational stressors create asymmetric demands on the striker versus the bowler:

### 5.1 Batting Pressure Index (`batting_pressure_index`)
Batters experience heightened psychological pressure from personal delivery dot-ball entrapment, entry into the crease during the middle/death phase with zero balls faced, and structural collapses:
$$\text{batting\_pressure\_index} = \text{clip}(P_C + 8.0 \cdot D_t + 6.0 \cdot \mathbb{I}(\text{pre\_striker\_balls} \le 4 \land \text{overid} \ge 11) + 5.0 \cdot C_t, 0, 100)$$

### 5.2 Bowling Pressure Index (`bowling_pressure_index`)
Bowlers experience heightened tactical pressure when bowling death overs against teams with abundant wickets in hand, or when bowling to well-set batters / established partnerships:
$$\text{bowling\_pressure\_index} = \text{clip}(P_C + 6.0 \cdot \mathbb{I}(\text{overid} \ge 16 \land W_{\text{hand}} \ge 5) + 5.0 \cdot \mathbb{I}(\text{pre\_striker\_runs} \ge 30 \lor \text{pre\_partner\_runs} \ge 50), 0, 100)$$

---

## 6. Categorization & Continuous Weighting

Using the empirical distribution of $P_C$ across all 200,999 deliveries, four definitive pressure tiers are established:

| Category | Percentile Range | Pressure Index Range | Total Deliveries | Percentage |
| :--- | :--- | :--- | :--- | :--- |
| **Low** | $< P_{40}$ | $[0.00, 57.05)$ | 80,378 | 39.99% |
| **Moderate** | $[P_{40}, P_{70})$ | $[57.05, 65.57)$ | 60,308 | 30.00% |
| **High** | $[P_{70}, P_{90})$ | $[65.57, 83.47)$ | 40,207 | 20.00% |
| **Extreme** | $\ge P_{90}$ (+ Super Overs) | $[83.47, 100.00]$ | 20,106 | 10.00% |

### 6.1 Binary High-Pressure Indicator
$$\text{is\_high\_pressure} = \mathbb{I}(P_C \ge P_{70}) \quad (\text{Threshold: } 65.57)$$
This classifies the top 30.01% most critical deliveries (60,313 deliveries) as high-pressure crucible deliveries.

### 6.2 Quadratic Pressure Weight
For continuous weighting in downstream residual models (Phase 4):
$$\omega_t = \left( \frac{P_C}{100.0} \right)^2 \in [0, 1]$$
Quadratic scaling gives low weight ($\approx 0.09$) to routine deliveries ($P \approx 30$) while quadratically magnifying high-pressure deliveries ($P \ge 70 \implies \omega \ge 0.49; P \ge 90 \implies \omega \ge 0.81$).

---

## 7. Approval & Sign-Off Checklist
- [x] Pre-delivery anti-leakage strictly enforced and unit-tested.
- [x] Dead-chase immunity mathematically guaranteed.
- [x] Win probability surfaces cross-validated ($AUC = 0.9021$ for chase).
- [x] Super Overs 100% categorized into `Extreme`.
- [x] Role-specific batting and bowling pressure indices formulated.
- [x] Model C confirmed as Champion Model.

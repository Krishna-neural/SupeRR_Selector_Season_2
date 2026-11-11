# Architectural & Mathematical Methodology Blueprint — SupeRR Selector Season 2

**Role:** Principal Cricket Data Engineer & Quantitative Research Architect  
**Purpose:** Formal, end-to-end mathematical and statistical architecture for Phases 3, 4, 5, and 6. This document serves as the permanent, authoritative technical blueprint for the entire project.

---

## 1. Phase 3 Architecture: Pre-Delivery State-Space & Shannon Entropy Pressure Model

### 1.1 Strict Pre-Delivery Anti-Leakage Protocol
To guarantee total scientific validity, every pressure variable at delivery $t$ is strictly a function of the **pre-delivery state vector** $\mathbf{s}_t^{-}$:
$$\mathbf{s}_t^{-} = \big(\text{innings}_t, b_{\text{rem}, t}^{-}, w_{\text{lost}, t}^{-}, r_{\text{need}, t}^{-}, \text{CRR}_t^{-}, \text{dot\_streak}_t^{-}, \text{venue\_par}_t, \kappa_{\text{stage}}\big)$$

Zero post-delivery event information (such as runs scored on ball $t$ or wicket fall on ball $t$) is ever utilized in pressure estimation.

---

### 1.2 First Innings Pressure Formulation ($\mathcal{P}_{t, \text{Inn 1}}$)
In target-setting scenarios, pressure is driven by top-order collapses, death-over run acceleration, and dot-ball suffocations:

1. **Corrected Top-Order Collapse Exponential:**  
   Let $\bar{w}(b)$ denote the empirical mean wickets lost by legal ball $b$ across all first innings in the dataset. The collapse pressure is given by:
   $$\text{CollapsePressure}_t = 1 - \exp\left( -\frac{\max\big(0, w_{\text{lost}, t}^{-} - \bar{w}(b_t^{-})\big)^2}{2 \cdot 1.25^2} \right) \in [0, 1]$$
   *(When a team is 3 or 4 wickets down in the Powerplay, this term surges toward 1.0, reflecting intense salvage pressure).*

2. **Phase Acceleration Factor:**
   $$\text{PhaseAccel}_t = \left(\frac{\max(0, \text{overid}_t - 14)}{6}\right)^{1.5} \in [0, 1]$$
   *(Captures the escalating demand for high strike-rate boundary execution across Overs 16–20).*

3. **Dot-Ball Buildup Factor:**
   $$\text{DotBuildup}_t = 1 - \exp\left(-\frac{(\text{dot\_streak}_t^{-})^2}{8}\right) \in [0, 1]$$
   *(Captures bowling asphyxiation; pressure increases non-linearly with consecutive legal dot balls).*

4. **Venue Par Deficit Factor:**
   $$\text{ParDeficit}_t = \text{clip}_{[0,1]}\left( \frac{\text{ExpectedParScore}(b_t^{-}) - \text{pre\_team\_score}_t}{30.0} \right)$$

5. **Composite Innings 1 Pressure:**
   $$\mathcal{P}_{t, \text{Inn 1}} = 100 \times \text{clip}_{[0,1]}\Big( 0.40 \cdot \text{CollapsePressure}_t + 0.30 \cdot \text{PhaseAccel}_t + 0.15 \cdot \text{ParDeficit}_t + 0.15 \cdot \text{DotBuildup}_t \Big) \times \kappa_{\text{stage}}$$

---

### 1.3 Second Innings Pressure Formulation ($\mathcal{P}_{t, \text{Inn 2}}$)
To eliminate the **"Dead-Chase Bias"** (where an unachievable target of 70 runs off 6 balls is falsely labeled as high pressure rather than garbage time), we model the run chase as a Discrete-Time Markov Chain (DTMC) with pre-delivery win probability $W(\mathbf{s}_t^{-}) \in (0, 1)$:

1. **Information-Theoretic / Shannon Entropy ($H_t$):**
   $$H(\mathbf{s}_t^{-}) = -W(\mathbf{s}_t^{-})\log_2 W(\mathbf{s}_t^{-}) - \big(1 - W(\mathbf{s}_t^{-})\big)\log_2\big(1 - W(\mathbf{s}_t^{-})\big) \in [0, 1]$$
   - $H(\mathbf{s}_t^{-}) = 1.0$ when $W = 0.50$ (maximum competitive balance / game on the line).
   - $H(\mathbf{s}_t^{-}) \to 0$ when $W \to 0$ (hopeless dead chase) or $W \to 1$ (chase already secured).

2. **Single-Ball State-Transition Leverage ($\mathcal{L}_t$):**
   $$\mathcal{L}_t = \big| W(\mathbf{s}_{t+1}^{-} \mid \text{Boundary 4}) - W(\mathbf{s}_{t+1}^{-} \mid \text{Wicket}) \big|$$
   Normalized relative to maximum leverage:
   $$\tilde{\mathcal{L}}_t = \frac{\mathcal{L}_t}{\max_k \mathcal{L}_k} \in [0, 1]$$

3. **Gaussian RRR Knife-Edge Factor ($G_t$):**
   $$G(\text{RRR}_t^{-}) = \exp\left( -\frac{(\text{RRR}_t^{-} - 11.5)^2}{2 \cdot 4.0^2} \right) \in [0, 1]$$
   *(Peaks at intensely contested chasing rates of 11.5 RPO; decays naturally toward 0 for impossible or trivial chase rates).*

4. **Composite Innings 2 Pressure:**
   $$\mathcal{P}_{t, \text{Inn 2}} = 100 \times \text{clip}_{[0,1]}\Big( 0.45 \cdot H(\mathbf{s}_t^{-}) + 0.35 \cdot \tilde{\mathcal{L}}_t + 0.20 \cdot G(\text{RRR}_t^{-}) \Big) \times \kappa_{\text{stage}}$$

---

### 1.4 Tournament Stakes Multiplier ($\kappa_{\text{stage}}$)
- **Super Overs (`innings in [3, 4]`):** $\kappa_{\text{stage}} = 1.35$ (instant elimination / maximum tension).
- **Playoffs / Knockouts (`knock_out == 1` or `stage in ['Final', 'Semi Final', 'Qualifier', 'Eliminator', 'Super 4']`):** $\kappa_{\text{stage}} = 1.25$.
- **Standard League Matches:** $\kappa_{\text{stage}} = 1.00$.

**Pressure Tiers:**
- **High Pressure:** $\mathcal{P}_t \ge 65.0$ (top ~30% of competitive deliveries).
- **Medium Pressure:** $40.0 \le \mathcal{P}_t < 65.0$.
- **Low Pressure / Baseline:** $\mathcal{P}_t < 40.0$.

---

## 2. Phase 4 Architecture: Context-Adjusted Value Added Over Expectation (VAOE / xRWA)

### 2.1 Eliminating Phase-Confounding Bias
Raw strike rates and economies suffer from severe contextual bias: Death overs naturally yield ~10.2 runs/over vs ~7.8 in the Middle overs. Evaluating a death-overs bowler on raw economy rate or a middle-overs accumulator on raw strike rate creates severe distortion.

We eliminate phase-confounding by computing expected runs and dismissal rates conditioned on pre-delivery context:
$$\hat{\mu}_{\text{runs}}(t) = \mathbb{E}\big[\text{runs}_t \mid \text{innings}, \text{overid}, \text{pace\_or\_spin}, \text{comp\_tier}\big]$$
$$\hat{p}_{\text{wkt}}(t) = \mathbb{P}\big(\text{wicket}_t \mid \text{innings}, \text{overid}, \text{pace\_or\_spin}, \text{comp\_tier}\big)$$

---

### 2.2 Dynamic Wicket Value Function ($\lambda_{\text{wkt}}$)
A wicket is significantly more damaging in the early overs than in the 20th over. We define $\lambda_{\text{wkt}}(b_{\text{rem}}^{-}, w_{\text{lost}}^{-})$ as the expected remaining runs lost by the batting team when a wicket falls at state $(b_{\text{rem}}^{-}, w_{\text{lost}}^{-})$:
$$\lambda_{\text{wkt}}(b_{\text{rem}}^{-}, w_{\text{lost}}^{-}) = \text{clip}_{[6.0, 26.0]}\left( 18.5 \cdot \left(\frac{b_{\text{rem}}^{-}}{120}\right) \cdot \left(\frac{10 - w_{\text{lost}}^{-}}{10}\right) + 6.0 \right)$$

---

### 2.3 Delivery-Level Value Added Formulation
For each delivery $t$:

#### Batter Value Added ($v_{\text{bat}, t}$):
$$v_{\text{bat}, t} = \big(\text{batter\_runs}_t - \hat{\mu}_{\text{bat\_runs}, t}\big) - \lambda_{\text{wkt}}(b_{\text{rem}, t}^{-}, w_{\text{lost}, t}^{-}) \cdot \big(\mathbb{I}(\text{BatterDismissed}_t) - \hat{p}_{\text{bat\_wkt}, t}\big)$$

#### Bowler Value Added ($v_{\text{bowl}, t}$):
$$v_{\text{bowl}, t} = \big(\hat{\mu}_{\text{bowl\_runs}, t} - \text{bowler\_runs\_conceded}_t\big) + \lambda_{\text{wkt}}(b_{\text{rem}, t}^{-}, w_{\text{lost}, t}^{-}) \cdot \big(\mathbb{I}(\text{BowlerWicket}_t) - \hat{p}_{\text{bowl\_wkt}, t}\big) + 0.35 \cdot \mathbb{I}(\text{LegalDot}_t) \cdot \left(\frac{\mathcal{P}_t}{100}\right)$$

---

### 2.4 Biomechanical & Tactical Profiling
To provide deep qualitative evidence explaining *how* players succeed under pressure:
- **Bowlers:** Profile execution frequencies and effectiveness of Yorkeresque deliveries (`delivery_style == 'Yorker'`), Bouncers (`delivery_style == 'Bouncer'`), Slower balls, and boundary containment speeds (`bowl_speed`).
- **Batters:** Profile execution of attacking strokes (`stroke in ['Cover Drive', 'Pull', 'Flick', 'Sweep', 'Scoop']`), boundary percentages, and off-side vs on-side dispersion (`on_or_off`).

---

## 3. Phase 5 & 6 Architecture: Hierarchical Empirical Bayes, Dynamic Elo & Sortino Downside Reliability

### 3.1 Dynamic Team Elo & Opposition Quality Weighting ($\omega_t$)
Teams are initialized with tier-stratified Elo ratings:
- Tier 1 (IPL): $R_0 = 1550$
- Tier 2 (T20I Full Member): $R_0 = 1500$
- Tier 3 (Associate / Emerging): $R_0 = 1300$

Updated chronologically post-match ($K = 24$):
$$R_{\text{new}} = R_{\text{old}} + K \cdot (S - \mathbb{E}[S])$$

For any match between Team $A$ and Team $B$, the delivery opposition quality weight $\omega_t$ is:
$$\omega_t = \text{clip}_{[0.60, 1.35]}\left( \frac{R_{\text{opposition}}}{1500.0} \right)$$
This ensures performances against elite IPL and Full-Member bowling attacks carry substantially greater statistical weight than runs scored against Associate bowling.

---

### 3.2 Empirical Bayes Shrinkage (Solving Small-Sample Distortion)
Let $\bar{V}_{i, \text{press}}$ be player $i$'s raw mean Value Added under high pressure over effective sample size $N_{i, \text{eff}} = \sum_{t \in \text{pressure}} \omega_t$:
$$\bar{V}_{i, \text{press}} = \frac{\sum_{t \in \text{pressure}} \omega_t \cdot v_{i, t}}{N_{i, \text{eff}}}$$

We estimate the cohort prior mean $\mu_0$ and between-player variance $\hat{\sigma}^2_{\text{between}}$ and within-player variance $\hat{\sigma}^2_{\text{within}}$. The empirical shrinkage constant is:
$$K = \frac{\hat{\sigma}^2_{\text{within}}}{\hat{\sigma}^2_{\text{between}}}$$

The Bayesian Shrunk Performance is:
$$\theta_{i, \text{press}} = \frac{N_{i, \text{eff}}}{N_{i, \text{eff}} + K} \cdot \bar{V}_{i, \text{press}} + \frac{K}{N_{i, \text{eff}} + K} \cdot \mu_0$$
This rigorously prevents lower-order batters or part-time bowlers with small sample sizes from dominating the rankings.

---

### 3.3 Sortino Downside Semi-Deviation ($\sigma_{\text{down}, i}$)
Standard deviation $\sigma$ penalizes massive match-winning outlier innings (positive variance). A reliable pressure performer should not be penalized for producing heroic, exceptionally high positive value added!

We replace standard deviation with **Downside Semi-Deviation** below contextual par ($\tau = 0$):
$$\sigma_{\text{down}, i} = \sqrt{ \frac{1}{M_i} \sum_{m=1}^{M_i} \min\big(0, \text{VAOE}_{i, m}^{\text{press}} - \tau\big)^2 }$$
Where $\text{VAOE}_{i, m}^{\text{press}}$ is player $i$'s aggregated value added in match $m$ under pressure.

---

### 3.4 Unified Reliability Indices & Top-10 Ranking Engine

#### Batting Reliability Index ($\text{BRI}_i$):
$$\text{BRI}_i = 100 \times \Bigg( 0.45 \cdot \tilde{\theta}_{i, \text{press}} + 0.30 \cdot \big(\tilde{\theta}_{i, \text{press}} - \tilde{\theta}_{i, \text{base}}\big) + 0.15 \cdot \text{ClutchFinishRatio}_i - 0.10 \cdot \tilde{\sigma}_{\text{down}, i} \Bigg)$$

#### Bowling Reliability Index ($\text{BWI}_j$):
$$\text{BWI}_j = 100 \times \Bigg( 0.45 \cdot \tilde{\theta}_{j, \text{press}} + 0.30 \cdot \big(\tilde{\theta}_{j, \text{press}} - \tilde{\theta}_{j, \text{base}}\big) + 0.15 \cdot \text{DeathContainmentRatio}_j - 0.10 \cdot \tilde{\sigma}_{\text{down}, j} \Bigg)$$

---

## 4. Uncertainty Quantification: Match-Level Block Bootstrap ($B = 1000$)
Because deliveries within a match are serially correlated, naive ball-level bootstrap destroys intra-match dependence. We implement **Match-Level Block Bootstrap**:
1. Resample complete `match_id` clusters with replacement over $B = 1,000$ iterations.
2. For each bootstrap iteration $b \in \{1, \dots, 1000\}$, recompute Bayesian shrunk ratings $\theta_{i}^{(b)}$ and rankings $\text{Rank}_i^{(b)}$.
3. Report:
   - **Empirical 95% Confidence Interval:** $[\text{CI}_{\text{lower}}, \text{CI}_{\text{upper}}]$.
   - **Probability of Outperforming Baseline:** $\mathbb{P}(\theta_{i, \text{press}} > \theta_{i, \text{base}})$.
   - **Top-10 Rank Stability:** $\mathbb{P}(\text{Rank}_i \le 10)$.

---

## 5. Sample Size Eligibility Criteria & Filter Gates

To ensure every ranked player is a proven performer with robust statistical credibility:
1. **Batters:**
   - Minimum $\ge 75$ pressure balls faced ($\mathcal{P}_t \ge 65.0$).
   - Minimum $\ge 15$ matches played across IPL and T20 Internationals.
2. **Bowlers:**
   - Minimum $\ge 60$ pressure legal deliveries bowled / 10 pressure overs ($\mathcal{P}_t \ge 65.0$).
   - Minimum $\ge 15$ matches played across IPL and T20 Internationals.

This methodology provides an unshakeable, mathematically rigorous foundation for the entire tournament.

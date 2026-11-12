# Bayesian Methodology & Statistical Reliability Specification
## SupeRR Selector Season 2 — Phase 5 Mathematical Blueprint

### 1. The Small-Sample Dilemma in Cricket Pressure Analytics
In Phase 4, we engineered context-adjusted Value Added Over Expected ($\text{VAOE}$) residuals for 888 batters and 647 bowlers. However, evaluating players strictly on raw sample averages creates severe distortions:
1. **The Short-Sample Cameo Spike:** A player facing 10 high-pressure deliveries who hits two sixes achieves an unregularized raw rate of $+120.0$ runs per 100 balls, outranking a world-class anchor who maintained $+30.0$ runs per 100 balls across 800 deliveries.
2. **The Associate-Bilateral Inflation:** High-pressure deliveries in Associate-nation bilateral fixtures feature lower opposition bowling/batting skill levels than high-pressure deliveries in the IPL or ICC T20 World Cup knockouts.
3. **Escalation Delta Instability:** Subtracting a player's normal-baseline VAOE from their high-pressure VAOE yields extreme deltas (e.g. $+168.0$) when the normal-situation sample size is small (e.g., a finisher who faced only 15 normal-pressure balls).

To resolve these distortions without discarding data, Phase 5 implements a **Hierarchical Empirical Bayes (EB) Shrinkage Model** augmented by **Effective Sample Size ($N_{\text{eff}}$) Weighting**, **Contextual Empirical Priors**, and **Match-Level Block Bootstrapping ($B = 1,000$)**.

---

### 2. Effective Sample Size ($N_{\text{eff}}$) & Delivery Evidence Weighting

Rather than treating every delivery as an identical unit of information, each high-pressure delivery $t$ (`is_high_pressure == True`) is weighted by its statistical information density:

$$w_{i, t} = \tau_{\text{tier}}(t) \cdot \omega_{\text{elo}}(t) \cdot \left(\frac{\mathcal{P}_{\text{role}, t}}{P_{70}}\right)$$

where:
1. **Competition Tier Weight ($\tau_{\text{tier}}(t)$):**
   $$\tau_{\text{tier}}(t) = \begin{cases} 1.00 & \text{for Tier 1 (IPL) and Tier 2 (T20I Full Member)} \\ 0.50 & \text{for Tier 3 (T20 Associate / Emerging)} \end{cases}$$
   *Rationale:* Dampens bilateral Associate mismatches while weighting elite franchise and international cricket at full scale.
2. **Pre-Match Opposition Elo Factor ($\omega_{\text{elo}}(t)$):**
   Derived in Phase 2 from dynamic Elo ratings, scaling delivery credit up for world-class attacks and down for weaker opposition.
3. **Situational Leverage Scaling ($\frac{\mathcal{P}_{\text{role}, t}}{P_{70}}$):**
   Where $P_{70} = 65.57$ is the 70th percentile of the corpus pressure index. A delivery at $P = 98.0$ (Super Over or extreme death chase) carries $1.49\times$ the evidence weight of an entry-level high-pressure ball ($P = 65.57$).

The player's **Effective Sample Size ($N_{i, \text{eff}}$)** is the sum of evidence weights:
$$N_{i, \text{eff}} = \sum_{t \in \text{HighPressure}_i} w_{i, t}$$

---

### 3. Hierarchical Empirical Bayes Shrinkage Formulation

In the Empirical Bayes framework, a player's observed weighted average performance $\bar{V}_i$ is assumed to arise from a true latent talent $\theta_i$ perturbed by sampling noise:
$$\bar{V}_i \mid \theta_i \sim \mathcal{N}\left(\theta_i, \frac{\sigma_{i, \text{within}}^2}{N_{i, \text{eff}}}\right)$$
$$\theta_i \sim \mathcal{N}\left(\mu_{0, \text{role}}, \tau_{\text{between}}^2\right)$$

Under conjugate normal-normal updating, the posterior distribution of $\theta_i$ is normal with mean:
$$\tilde{\theta}_i = B_i \bar{V}_i + (1 - B_i) \mu_{0, \text{role}}$$
where the **Credibility Factor ($B_i \in [0, 1)$)** is given by:
$$B_i = \frac{N_{i, \text{eff}}}{N_{i, \text{eff}} + K}$$
with shrinkage constant $K = \frac{\sigma_{\text{within}}^2}{\tau_{\text{between}}^2}$.

#### 3.1 Variance-Ratio Derivation & Crucible Stabilization Floors
Using random-effects ANOVA / DerSimonian-Laird estimation across qualified Tier 1 and Tier 2 players:
- **Batting Residuals:** $\hat{\sigma}_{\text{within}}^2 = 132,255.2$, $\hat{\tau}_{\text{between}}^2 = 867.8 \implies K_{\text{raw}} = 152.4$ balls.
- **Bowling Residuals:** $\hat{\sigma}_{\text{within}}^2 = 7,181.4$, $\hat{\tau}_{\text{between}}^2 = 30.7 \implies K_{\text{raw}} = 234.3$ legal balls.

To guarantee that small-sample cameos cannot dominate the elite rankings, we enforce a **Crucible Stabilization Floor**:
$$K_{\text{bat}} = \max(K_{\text{raw, bat}}, 200.0) = \mathbf{200.0 \text{ effective balls}}$$
$$K_{\text{bowl}} = \max(K_{\text{raw, bowl}}, 150.0) = \mathbf{234.3 \text{ effective legal balls}}$$

**Practical Interpretation of $B_i$:**
- At $N_{\text{eff}} = 20$ balls: $B_{\text{bat}} = \frac{20}{220} = 0.091$ (91% regression toward prior mean).
- At $N_{\text{eff}} = 100$ balls: $B_{\text{bat}} = \frac{100}{300} = 0.333$ (33% self-weight).
- At $N_{\text{eff}} = 200$ balls: $B_{\text{bat}} = \frac{200}{400} = 0.500$ (50% self-weight).
- At $N_{\text{eff}} = 800$ balls (e.g. Suryakumar Yadav): $B_{\text{bat}} = \frac{800}{1000} = 0.800$ (80% self-weight backed by massive sample).

---

### 4. Contextual Role-Specific Priors & Exact Component Additivity

Rather than shrinking all players toward an indiscriminate global average of 0.0, we establish empirical priors conditioned on the player's primary role in the team:

#### 4.1 Batting Role Priors (per 100 balls)
Calibrated from weighted high-pressure deliveries across the corpus:
- **Top Order (Positions 1–3):** $\mu_{\text{VAOE}} = -0.63$ (Runs Added: $\mu_{\text{RAE}} = +0.63$, Wicket Cost: $\mu_{\text{WPV}} = -1.25$).
- **Middle Order (Positions 4–5):** $\mu_{\text{VAOE}} = +2.92$ (Runs Added: $\mu_{\text{RAE}} = -2.32$, Wicket Cost: $\mu_{\text{WPV}} = +5.23$).
- **Lower-Middle / Finisher (Positions 6+):** $\mu_{\text{VAOE}} = -4.47$ (Runs Added: $\mu_{\text{RAE}} = -4.63$, Wicket Cost: $\mu_{\text{WPV}} = +0.15$).

#### 4.2 Bowling Style Priors (per 24 legal balls)
- **Pace Bowlers:** $\mu_{\text{VAOE}} = -0.14$ (Runs Saved: $\mu_{\text{RSAE}} = +0.18$, Wickets: $\mu_{\text{WVA}} = -0.32$).
- **Spin Bowlers:** $\mu_{\text{VAOE}} = -0.24$ (Runs Saved: $\mu_{\text{RSAE}} = +0.17$, Wickets: $\mu_{\text{WVA}} = -0.41$).

#### 4.3 Exact Additive Component Identity
To maintain perfect interpretability, component residuals are shrunk alongside total VAOE:
$$\tilde{\text{RAE}}_i = B_i \cdot \bar{\text{RAE}}_i + (1 - B_i) \cdot \mu_{\text{RAE}, \text{role}}$$
$$\tilde{\text{WPV}}_i = B_i \cdot \bar{\text{WPV}}_i + (1 - B_i) \cdot \mu_{\text{WPV}, \text{role}}$$
$$\tilde{\theta}_i = \tilde{\text{RAE}}_i + \tilde{\text{WPV}}_i$$

Because $\mu_{\text{RAE}, \text{role}} + \mu_{\text{WPV}, \text{role}} \equiv \mu_{\text{VAOE}, \text{role}}$, the sum of shrunk components is **identically equal to shrunk total VAOE** across all players.

---

### 5. Escalation Delta Shrinkage ($\tilde{\Delta}_i$)

A player's escalation under pressure is measured by their performance differential:
$$\Delta_i = \text{VAOE}_{i, \text{press}} - \text{VAOE}_{i, \text{normal}}$$

Because $\Delta_i$ is the difference between two noisy estimates, its variance is the sum of their variances:
$$\text{Var}(\Delta_i) \propto \frac{1}{N_{i, \text{press}}} + \frac{1}{N_{i, \text{normal}}}$$

We define the **Harmonic Sample Size ($N_{i, \text{harm}}$)**:
$$N_{i, \text{harm}} = \left(\frac{1}{N_{i, \text{press}}} + \frac{1}{N_{i, \text{normal}}}\right)^{-1}$$

The shrunk escalation delta $\tilde{\Delta}_i$ is computed with stabilization constant $K_{\Delta} = 150.0$:
$$\tilde{\Delta}_i = \frac{N_{i, \text{harm}}}{N_{i, \text{harm}} + K_{\Delta}} \cdot \left(\bar{V}_{i, \text{press}} - \bar{V}_{i, \text{normal}}\right)$$

This rigorously prevents noisy single-match swings from inflating a player's "clutch escalation" rating.

---

### 6. Analytical Uncertainty & Confidence Bounds

For every player $i$, we compute analytical posterior uncertainty metrics:
1. **Posterior Standard Error ($\text{SE}(\tilde{\theta}_i)$):**
   $$\text{SE}(\tilde{\theta}_i) = \sqrt{\frac{S^2 \cdot \hat{\sigma}_{i, \text{within}}^2}{N_{i, \text{eff}} + K}}$$
   where $S = 100$ for batters and $S = 24$ for bowlers. $\hat{\sigma}_{i, \text{within}}^2$ is regularized toward pooled variance:
   $$\hat{\sigma}_{i, \text{within}}^2 = \frac{N_i}{N_i + 20} s_i^2 + \frac{20}{N_i + 20} \sigma_{\text{pool}}^2$$
2. **95% Bayesian Credible Interval:**
   $$\left[\text{CI}_{\text{low}, 95\%}, \text{CI}_{\text{high}, 95\%}\right] = \left[\tilde{\theta}_i - 1.96 \cdot \text{SE}(\tilde{\theta}_i), \; \tilde{\theta}_i + 1.96 \cdot \text{SE}(\tilde{\theta}_i)\right]$$
3. **Posterior Lower Confidence Bound ($\text{LCB}_{80}$):**
   $$\text{LCB}_{i, 80\%} = \tilde{\theta}_i - 0.8416 \cdot \text{SE}(\tilde{\theta}_i)$$
   *Rationale:* Represents the performance level that the player exceeds with 80% posterior probability, heavily rewarding high-volume players whose conservative floor is elite.
4. **Probability of Outperforming Contextual Baseline ($P(\theta_i > 0)$):**
   $$P(\theta_i > 0) = \Phi\left(\frac{\tilde{\theta}_i}{\text{SE}(\tilde{\theta}_i)}\right)$$

---

### 7. Vectorized Match-Level Block Bootstrap ($B = 1,000$)

Deliveries within the same match share unmodeled pitch conditions, weather, and psychological match context. To produce non-parametric empirical error distributions that fully respect match-level clustering:
1. Resample the $M = 867$ match clusters with replacement $B = 1,000$ times.
2. Formulate the resampling as a multinomial matrix multiplication $\mathbf{C} \in \mathbb{R}^{B \times M}$ against pre-aggregated match-player matrices $\mathbf{W} \in \mathbb{R}^{P \times M}$ and $\mathbf{V} \in \mathbb{R}^{P \times M}$:
   $$\mathbf{W}_{\text{boot}} = \mathbf{W} \mathbf{C}^T, \quad \mathbf{V}_{\text{boot}} = \mathbf{V} \mathbf{C}^T$$
3. Across all 1,000 bootstrap iterations, compute:
   - `bootstrap_mean` & `bootstrap_se`
   - Empirical 95% interval: `bootstrap_ci_95_low` (2.5th percentile) and `bootstrap_ci_95_high` (97.5th percentile)
   - `bootstrap_prob_positive`: % of resamples where shrunk VAOE $> 0$
   - `bootstrap_median_rank` & `bootstrap_rank_iqr` ($P_{75} - P_{25}$)
   - `bootstrap_top10_prob`: % of iterations where the candidate ranks in the Top 10.

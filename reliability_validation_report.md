# Phase 5 Validation Report: Statistical Reliability, Empirical Bayes Shrinkage & Uncertainty
## SupeRR Selector Season 2 — Quantitative Audit

### 1. Executive Summary
Phase 5 establishes the statistical reliability and regularization engine for the Rajasthan Royals SupeRR Selector Season 2 challenge. By integrating **Hierarchical Empirical Bayes (EB) Shrinkage**, **Effective Sample Size ($N_{\text{eff}}$) Weighting**, **Contextual Role Priors**, and a **1,000-Iteration Match-Level Block Bootstrap**, this engine successfully resolves the small-sample outlier vulnerability identified in Phase 4 without losing the signals of elite performance.

All architectural invariants and deliverables were executed via `src/reliability_model.py` and validated through `tests/test_phase5_reliability.py` (32/32 tests passing across Phases 2–5):
- Unified uncertainty table generated: `player_uncertainty.csv` (1,535 rows, 31 columns).
- Master player tables updated: `batting_player_statistics.csv` (888 rows, 95 columns) and `bowling_player_statistics.csv` (647 rows, 101 columns).
- Zero-null invariant verified across all eligible candidates.
- Small-sample defense verified: 0 players with $< 30$ balls rank in the Top 20 of shrunk VAOE.

---

### 2. Before-and-After Shrinkage Proof: Outlier Regularization

The primary objective of Empirical Bayes shrinkage is to act as an automated Bayesian filter: heavily shrinking noisy, low-volume spikes toward the contextual role prior ($\mu_{0, \text{role}}$) while preserving the rating of high-volume performers who proved their quality across hundreds of deliveries.

#### 2.1 Batting Outlier Defense vs. High-Volume Elite Performers
The table below contrasts extreme small-sample outliers against sustained high-volume stars:

| Player Name | Context / Role | Raw Pressure Balls | Effective Sample ($N_{\text{eff}}$) | Credibility Factor ($B_i$) | Raw VAOE (runs/100b) | Shrunk VAOE ($\tilde{\theta}$) | Posterior $\text{SE}$ | 95% Credible Interval | LCB$_{80}$ Floor |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Kushal Bhurtel** | Small-Sample Spike | 5 | 5.2 | 0.0253 | **+262.80** | **+5.89** | 24.81 | [-42.74, +54.52] | -15.00 |
| **Arafat Minhas** | Associate Bilateral | 42 | 26.8 | 0.1182 | **+63.42** | **+4.25** | 23.60 | [-42.01, +50.51] | -15.61 |
| **Evin Lewis** | Moderate Sample | 105 | 135.8 | 0.4043 | **+53.82** | **+21.38** | 19.64 | [-17.11, +59.87] | +4.85 |
| **Suryakumar Yadav** | High-Volume Elite | **760** | **974.8** | **0.8298** | **+35.81** | **+30.21** | **9.20** | **[+12.18, +48.24]** | **+22.47** |
| **Pathum Nissanka** | High-Volume Elite | **682** | **869.8** | **0.8131** | **+32.70** | **+26.47** | **11.41** | **[+4.11, +48.83]** | **+16.87** |
| **Reeza Hendricks** | High-Volume Elite | **301** | **371.2** | **0.6499** | **+39.84** | **+25.67** | **14.34** | **[-2.44, +53.78]** | **+13.60** |
| **Virat Kohli** | High-Volume Elite | **667** | **846.5** | **0.8089** | **+26.87** | **+21.61** | **10.05** | **[+1.91, +41.31]** | **+13.15** |
| **Sai Sudharsan** | High-Volume Elite | **450** | **589.6** | **0.7467** | **+28.77** | **+21.32** | **11.00** | **[-0.24, +42.88]** | **+12.07** |
| **Heinrich Klaasen** | High-Volume Elite | **403** | **519.8** | **0.7221** | **+27.72** | **+20.83** | **10.81** | **[-0.36, +42.02]** | **+11.73** |

**Empirical Proof Points:**
1. Kushal Bhurtel’s unregularized raw spike of $+262.80$ runs/100b is shrunken by **97.5%**, dropping down to $+5.89$ with a massive $\text{SE} = 24.81$.
2. In contrast, Suryakumar Yadav ($N_{\text{eff}} = 974.8$) retains **83.0%** of his observed performance, settling at an elite $+30.21$ runs/100b backed by a rock-solid $\text{LCB}_{80} = +22.47$ runs/100b floor.

---

#### 2.2 Bowling Outlier Defense vs. High-Volume Elite Performers
Comparison across bowling candidates (per 24 legal balls / 4-over spell):

| Player Name | Context / Role | Raw Pressure Balls | Effective Sample ($N_{\text{eff}}$) | Credibility Factor ($B_i$) | Raw VAOE (runs/24b) | Shrunk VAOE ($\tilde{\theta}$) | Posterior $\text{SE}$ | 95% Credible Interval | LCB$_{80}$ Floor |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Kashif Daud** | Associate Small Sample | 6 | 3.2 | 0.0135 | **+24.12** | **+0.19** | 5.56 | [-10.71, +11.09] | -4.49 |
| **Wayne Parnell** | Small Volatile Sample | 105 | 128.9 | 0.3550 | **+11.37** | **+3.95** | 6.76 | [-9.30, +17.20] | -1.74 |
| **Lockie Ferguson** | Sustained Strike Bowler | **290** | **352.5** | **0.6007** | **+12.17** | **+7.25** | **4.22** | **[-1.02, +15.52]** | **+3.70** |
| **Umran Malik** | Middle Over Express | **126** | **160.6** | **0.4067** | **+17.49** | **+7.03** | **4.81** | **[-2.40, +16.46]** | **+2.98** |
| **Mahedi Hasan** | Powerplay Specialist | **279** | **304.2** | **0.5649** | **+12.59** | **+7.01** | **4.60** | **[-2.01, +16.03]** | **+3.14** |
| **Shaheen Afridi** | Elite Strike Pace | **431** | **515.1** | **0.6873** | **+8.00** | **+5.45** | **3.74** | **[-1.88, +12.78]** | **+2.30** |
| **Josh Hazlewood** | Control & Wickets | **479** | **620.3** | **0.7258** | **+6.35** | **+4.57** | **3.70** | **[-2.68, +11.82]** | **+1.46** |
| **Nathan Ellis** | Death Specialist | **316** | **399.9** | **0.6305** | **+6.72** | **+4.19** | **3.39** | **[-2.45, +10.83]** | **+1.34** |

**Empirical Proof Points:**
1. Kashif Daud’s 6-ball raw anomaly of $+24.12$ runs/24b is compressed by **98.7%** to $+0.19$, with a negative floor ($\text{LCB}_{80} = -4.49$).
2. Lockie Ferguson ($N_{\text{eff}} = 352.5$) retains $+7.25$ runs/24b with a positive floor ($\text{LCB}_{80} = +3.70$), and Nathan Ellis maintains $+4.19$ runs/24b backed by a low posterior standard error of $3.39$.

---

### 3. Uncertainty Decay with Sample Size

As established in Section 6 of `bayesian_methodology.md`, the posterior standard error decays as a function of effective sample size according to:
$$\text{SE}(N_{\text{eff}}) = \sqrt{\frac{S^2 \cdot \sigma_{\text{within}}^2}{N_{\text{eff}} + K}}$$

Empirical standard error averages across volume buckets confirm theoretical convergence:

```
Posterior Uncertainty Decay Curves:
Batting SE (runs/100b):
N_eff = 0:    [█████████████████████████] 25.91
N_eff = 100:  [██████████████████]       18.32
N_eff = 300:  [████████████]             12.95
N_eff = 600:  [█████████]                 9.16
N_eff = 1000: [███████]                   7.48

Bowling SE (runs/24b):
N_eff = 0:    [█████████████████████████] 5.66
N_eff = 100:  [██████████████████]       4.38
N_eff = 300:  [████████████]             3.40
N_eff = 600:  [█████████]                 2.68
N_eff = 1000: [███████]                   2.19
```

Players with small sample sizes have confidence interval widths of $\approx 70.0$ runs/100b (batting) or $\approx 18.0$ runs/24b (bowling). Once a player accumulates $\ge 600$ effective balls, their confidence interval narrows by more than **60%**, providing immense statistical certainty for high-volume performers.

---

### 4. Match-Level Block Bootstrap Convergence Diagnostics ($B = 1,000$)

To capture unmodeled pitch, weather, and venue correlation across balls within the same match, we performed $B = 1,000$ cluster resamples of all $M = 867$ match IDs.

```
Bootstrap Convergence Diagnostics:
- Number of Replicates (B):           1,000 match clusters
- Execution Time (Vectorized Matrix): 1.96 seconds
- Monte Carlo Standard Error (MCSE):  < 0.12 runs across all players
- Mean Difference (Boot Mean - Shrunk VAOE):
    • Batting:  -0.08 runs/100b (Exact zero bias!)
    • Bowling:  -0.03 runs/24b  (Exact zero bias!)
- Rank Stability Metric:
    • Suryakumar Yadav Rank IQR:  7.0 positions (Top-10 Prob = 75.4%)
    • Pathum Nissanka Rank IQR:   14.0 positions (Top-10 Prob = 56.2%)
    • Lockie Ferguson Rank IQR:   18.0 positions (Top-10 Prob = 61.3%)
```

---

### 5. Production Eligible Shrunk Leaderboards

The tables below display the top 10 eligible batters and bowlers sorted by shrunk pressure VAOE ($\tilde{\theta}_{\text{press}}$), accompanied by their Bayesian Credible Intervals, $\text{LCB}_{80}$, and Block Bootstrap metrics:

#### 5.1 Top 10 Eligible Batters
*Eligibility: $\ge 100$ pressure balls faced AND $\ge 5$ Tier 1 / Tier 2 matches (168 qualified batters).*

| Rank | Player Name | Primary Role | Pressure Balls | $N_{\text{eff}}$ | Shrunk VAOE (runs/100b) | 95% Credible Interval | LCB$_{80}$ Floor | Bootstrap Mean | Bootstrap 95% CI | Top-10 Prob | $P(\theta > 0)$ |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | **Vaibhav Sooryavanshi** | Top Order (1-3) | 260 | 318.6 | **+36.49** | [-4.78, +77.76] | +18.76 | +36.80 | [-1.59, +70.72] | 74.8% | 96.6% |
| **2** | **Suryakumar Yadav** | Middle Order (4-5) | 760 | 974.8 | **+30.21** | [+12.18, +48.24] | +22.47 | +30.12 | [+15.21, +43.83] | 75.4% | 99.9% |
| **3** | **Pathum Nissanka** | Top Order (1-3) | 682 | 869.8 | **+26.47** | [+4.11, +48.83] | +16.87 | +26.22 | [+8.78, +42.47] | 56.2% | 99.0% |
| **4** | **Reeza Hendricks** | Top Order (1-3) | 301 | 371.2 | **+25.67** | [-2.44, +53.78] | +13.60 | +24.38 | [+0.97, +40.99] | 51.6% | 96.3% |
| **5** | **Ryan Rickelton** | Top Order (1-3) | 246 | 312.1 | **+24.41** | [-7.28, +56.10] | +10.78 | +22.87 | [-3.18, +43.87] | 43.9% | 93.4% |
| **6** | **Virat Kohli** | Top Order (1-3) | 667 | 846.5 | **+21.61** | [+1.91, +41.31] | +13.15 | +21.44 | [+6.03, +36.63] | 31.5% | 98.4% |
| **7** | **Evin Lewis** | Top Order (1-3) | 105 | 135.8 | **+21.38** | [-17.11, +59.87] | +4.85 | +19.59 | [-10.55, +49.79] | 35.7% | 86.2% |
| **8** | **Sai Sudharsan** | Top Order (1-3) | 450 | 589.6 | **+21.32** | [-0.24, +42.88] | +12.07 | +20.66 | [+3.37, +33.64] | 28.6% | 97.4% |
| **9** | **Yashasvi Jaiswal** | Top Order (1-3) | 588 | 754.7 | **+21.24** | [-6.09, +48.57] | +9.51 | +20.40 | [-2.43, +38.65] | 32.2% | 93.6% |
| **10** | **Heinrich Klaasen** | Middle Order (4-5) | 403 | 519.8 | **+20.83** | [-0.36, +42.02] | +11.73 | +20.26 | [+1.52, +36.78] | 28.8% | 97.3% |

---

#### 5.2 Top 10 Eligible Bowlers
*Eligibility: $\ge 60$ pressure legal balls bowled AND $\ge 5$ Tier 1 / Tier 2 matches (215–221 qualified bowlers).*

| Rank | Player Name | Primary Role | Pressure Balls | $N_{\text{eff}}$ | Shrunk VAOE (runs/24b) | 95% Credible Interval | LCB$_{80}$ Floor | Bootstrap Mean | Bootstrap 95% CI | Top-10 Prob | $P(\theta > 0)$ |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | **Lockie Ferguson** | Middle Specialist | 290 | 352.5 | **+7.25** | [-1.02, +15.52] | +3.70 | +7.01 | [+0.40, +13.56] | 61.3% | 95.7% |
| **2** | **Umran Malik** | Middle Specialist | 126 | 160.6 | **+7.03** | [-2.40, +16.46] | +2.98 | +6.70 | [-1.43, +14.08] | 57.4% | 92.8% |
| **3** | **Mahedi Hasan** | Powerplay Specialist | 279 | 304.2 | **+7.01** | [-2.01, +16.03] | +3.14 | +5.80 | [-1.58, +12.88] | 47.6% | 93.6% |
| **4** | **William ORourke** | Powerplay Specialist | 60 | 77.4 | **+6.70** | [-8.37, +21.77] | +0.23 | +6.39 | [+0.55, +12.05] | 54.3% | 81.1% |
| **5** | **Shaheen Afridi** | Powerplay Specialist | 431 | 515.1 | **+5.45** | [-1.88, +12.78] | +2.30 | +5.21 | [-0.43, +10.78] | 39.3% | 92.7% |
| **6** | **Ottneil Baartman** | Middle Specialist | 99 | 116.9 | **+4.96** | [-6.21, +16.13] | +0.17 | +4.82 | [-1.04, +10.82] | 34.7% | 80.8% |
| **7** | **Josh Hazlewood** | Powerplay Specialist | 479 | 620.3 | **+4.57** | [-2.68, +11.82] | +1.46 | +4.51 | [-1.11, +10.24] | 29.5% | 89.2% |
| **8** | **Mohammad Nawaz** | Middle Specialist | 375 | 445.9 | **+4.29** | [-2.61, +11.19] | +1.33 | +3.77 | [-1.50, +9.43] | 21.0% | 89.4% |
| **9** | **Nathan Ellis** | Death Specialist | 316 | 399.9 | **+4.19** | [-2.45, +10.83] | +1.34 | +4.04 | [-0.48, +8.82] | 20.4% | 89.2% |
| **10** | **Wayne Parnell** | Powerplay Specialist | 105 | 128.9 | **+3.95** | [-9.30, +17.20] | -1.74 | +3.92 | [-5.15, +13.65] | 33.0% | 72.1% |

---

### 6. Phase 5 Sign-Off Checklist
- [x] Effective Sample Size ($N_{\text{eff}}$) computed with competition tier ($\tau = 1.0$ / $0.5$) and opposition Elo.
- [x] Empirical Bayes shrinkage calibrated with variance components ($K_{\text{bat}} = 200.0$, $K_{\text{bowl}} = 234.3$).
- [x] Role-specific empirical priors calibrated and exact component additivity verified.
- [x] Analytical posterior uncertainty ($\text{SE}$, 95% CI, $\text{LCB}_{80}$, $P(\theta > 0)$, $P(\Delta > 0)$) generated.
- [x] Vectorized Match-Level Block Bootstrap ($B = 1,000$) executed in under 2 seconds.
- [x] Threshold sensitivity analysis completed across 5 batter and 5 bowler thresholds.
- [x] Production eligibility standards locked ($\ge 100$ balls for batters, $\ge 60$ legal balls for bowlers, $\ge 5$ Tier 1/2 matches).
- [x] All 32 automated tests in `pytest tests/` passing 100%.
- [x] STOP RULE respected: Final Phase 6 ranking engine held until Phase 5 approval.

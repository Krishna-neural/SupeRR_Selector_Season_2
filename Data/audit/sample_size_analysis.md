# Sample Size and Eligibility Sensitivity Analysis
## SupeRR Selector Season 2 — Phase 5 Research Report

### 1. Executive Summary & Problem Formulation
In Phase 4, we constructed context-adjusted Value Added Over Expected ($\text{VAOE}$) models across 888 batters and 647 bowlers. While the zero-mean residual invariant was mathematically verified across all 200,999 balls ($\sum \text{RAE} = +0.07$, $\sum \text{RSAE} = -0.05$), raw unregularized averages suffer from extreme sample size vulnerability. Players facing or bowling small samples in high-pressure situations exhibited extreme outlier ratings (e.g., Kushal Bhurtel at $+262.8$ runs/100b in 5 balls, Arafat Minhas at $+63.4$ runs/100b in Associate matches, or Evin Lewis at $+53.8$ runs/100b in 105 balls).

To solve this, Phase 5 establishes an empirical sample size framework that:
1. Converts raw delivery counts into **Effective Sample Size ($N_{\text{eff}}$)** by weighting deliveries by competition tier ($\tau = 1.0$ for IPL and Full-Member T20Is; $0.5$ for Associate matches), opposition Elo quality ($\omega_{\text{elo}}$), and situational pressure intensity ($\mathcal{P} / P_{70}$).
2. Conducts a rigorous **5-point threshold sensitivity analysis** across candidate eligibility cutoffs to identify the optimal boundary balancing statistical power, uncertainty bounds, and fair representation across IPL and T20I competitions.

---

### 2. High-Pressure Sample Size Distributions

Across the corpus of 883 matches (200,999 balls), 60,313 deliveries (30.01%) meet the High-Pressure threshold ($\mathcal{P} \ge P_{70} = 65.57$ or Super Overs):
- **Tier 1 (IPL):** 27,441 balls (45.50%)
- **Tier 2 (T20I Full Member):** 26,818 balls (44.46%)
- **Tier 3 (T20 Associate / Emerging):** 6,054 balls (10.04%)

#### 2.1 Batting High-Pressure Sample Distribution
- Total Batters in Corpus: 888
- Batters facing $\ge 1$ High-Pressure Ball: 731
- Batters facing $\ge 50$ High-Pressure Balls: 237 (32.4%)
- Batters facing $\ge 100$ High-Pressure Balls: 168 (23.0%)
- Batters facing $\ge 200$ High-Pressure Balls: 104 (14.2%)
- Batters facing $\ge 500$ High-Pressure Balls: 26 (3.6%)
- Maximum Pressure Balls Faced: Namboori Tilak Varma (787 balls, $N_{\text{eff}} = 1024.77$), Shubman Gill (767 balls, $N_{\text{eff}} = 989.49$), Suryakumar Yadav (760 balls, $N_{\text{eff}} = 974.81$).

#### 2.2 Bowling High-Pressure Sample Distribution
- Total Bowlers in Corpus: 647
- Bowlers bowling $\ge 1$ High-Pressure Legal Ball: 554
- Bowlers bowling $\ge 48$ Legal Balls (8 overs): 244 (44.0%)
- Bowlers bowling $\ge 60$ Legal Balls (10 overs): 221 (39.9%)
- Bowlers bowling $\ge 120$ Legal Balls (20 overs): 146 (26.4%)
- Bowlers bowling $\ge 300$ Legal Balls (50 overs): 47 (8.5%)
- Maximum Pressure Legal Balls Bowled: Arshdeep Singh (914 balls, $N_{\text{eff}} = 1139.70$), Yuzvendra Chahal (791 balls, $N_{\text{eff}} = 1018.37$), Ravi Bishnoi (778 balls, $N_{\text{eff}} = 1002.20$), Rashid Khan (759 balls, $N_{\text{eff}} = 947.86$).

---

### 3. Threshold Sensitivity Grid Analysis

To prevent arbitrary cutoff selection, we evaluated candidate thresholds across five dimensions:
1. **Candidate Pool Size ($N$):** Viable depth of candidates for elite selection.
2. **Mean Effective Sample Size ($\bar{N}_{\text{eff}}$):** Average information content per player.
3. **Mean Posterior Standard Error ($\overline{\text{SE}}$) & 95% Credible Interval Width:** Precision of player estimates.
4. **Rank Stability:** Spearman rank correlation ($\rho$) and Top-10 Jaccard overlap relative to the locked production baseline.
5. **Competition Representation:** Percentage of candidate pool originating primarily from IPL, T20I Full Member, and Associate competitions.

#### 3.1 Batting Threshold Grid Evaluation
All cutoffs require $\ge 5$ matches in Tier 1 (IPL) or Tier 2 (T20I Full Member) to ensure multi-tournament validation.

| Threshold | Eligible Batters | Mean $N_{\text{eff}}$ | Mean $\text{SE}$ (runs/100b) | 95% CI Width | Spearman $\rho$ | Top-10 Jaccard | % IPL | % T20I Full Member | % Associate |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$\ge 50$ balls** | 237 | 259.0 | 17.57 | 68.89 | 1.000 | 1.00 | 45.6% | 51.9% | 2.5% |
| **$\ge 75$ balls** | 190 | 305.4 | 16.67 | 65.36 | 1.000 | 1.00 | 49.5% | 49.5% | 1.1% |
| **$\ge 100$ balls (Recommended)** | **168** | **332.2** | **16.38** | **64.21** | **1.000** | **1.00** | **52.4%** | **47.6%** | **0.0%** |
| **$\ge 125$ balls** | 140 | 371.7 | 15.47 | 60.63 | 1.000 | 0.82 | 53.6% | 46.4% | 0.0% |
| **$\ge 150$ balls** | 125 | 396.7 | 15.00 | 58.80 | 1.000 | 0.82 | 55.2% | 44.8% | 0.0% |

**Observations on Batting Cutoff:**
- At $\ge 50$ balls, the pool includes small-sample cameos (e.g. 50–70 balls) with wide confidence intervals ($\pm 34.4$ runs/100b) and lingering Associate bilateral noise (2.5%).
- Moving from 75 to 100 balls completely purges non-elite Associate distortions ($0.0\%$), achieving a near-perfect balance between IPL (52.4%) and T20I Full Member (47.6%) specialists.
- The Top-10 Jaccard overlap between 50b, 75b, and 100b is exactly **1.00** (identical Top-10 set), demonstrating that Empirical Bayes shrinkage already protects the upper echelon from small-sample intrusion.
- At $\ge 125$ or $\ge 150$ balls, the pool narrows excessively (dropping to 125 batters), unnecessarily eliminating clutch performers with 105–118 balls (such as Evin Lewis).
- **Locked Batting Standard:** $\ge 100$ high-pressure balls faced AND $\ge 5$ Tier 1 / Tier 2 matches (168 qualified batters).

---

#### 3.2 Bowling Threshold Grid Evaluation
All cutoffs require $\ge 5$ matches in Tier 1 (IPL) or Tier 2 (T20I Full Member).

| Threshold | Eligible Bowlers | Mean $N_{\text{eff}}$ | Mean $\text{SE}$ (runs/24b) | 95% CI Width | Spearman $\rho$ | Top-10 Jaccard | % IPL | % T20I Full Member | % Associate |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$\ge 48$ balls (8 overs)** | 244 | 255.5 | 4.06 | 15.90 | 1.000 | 1.00 | 40.6% | 57.0% | 2.5% |
| **$\ge 60$ balls (10 overs) (Recommended)** | **221** | **275.7** | **3.98** | **15.60** | **1.000** | **1.00** | **41.6%** | **56.1%** | **2.3%** |
| **$\ge 90$ balls (15 overs)** | 175 | 325.5 | 3.79 | 14.87 | 1.000 | 0.82 | 44.0% | 54.9% | 1.1% |
| **$\ge 120$ balls (20 overs)** | 146 | 365.6 | 3.66 | 14.36 | 1.000 | 0.54 | 48.6% | 50.7% | 0.7% |
| **$\ge 150$ balls (25 overs)** | 117 | 416.7 | 3.52 | 13.79 | 1.000 | 0.43 | 49.6% | 50.4% | 0.0% |

**Observations on Bowling Cutoff:**
- In T20 cricket, a complete spell is 24 legal balls (4 overs). A threshold of 60 legal balls represents **2.5 complete 4-over spells bowled under high pressure**, requiring multi-match consistency.
- Moving from 48 balls to 60 balls preserves 100% Top-10 stability (Jaccard = 1.00) while tightening mean standard error below 4.0 runs/24b.
- Raising the cutoff to 120 or 150 balls degrades Top-10 Jaccard overlap significantly (dropping to 0.54 and 0.43) by arbitrarily penalizing specialized high-leverage death and powerplay strike bowlers (such as Ottneil Baartman with 99 balls or William O'Rourke with 60 balls).
- **Locked Bowling Standard:** $\ge 60$ high-pressure legal balls bowled AND $\ge 5$ Tier 1 / Tier 2 matches (215–221 qualified bowlers).

---

### 4. Competition Tier & Representation Synthesis

The official Rajasthan Royals challenge rubric explicitly demands fair evaluation across both IPL and International T20 contexts without systemic competition bias:

```
Eligible Pool Composition at Locked Thresholds:
┌──────────────────────────────────────────────────────────┐
│ Batters (N = 168):                                       │
│   • Tier 1 (IPL):                     88 batters (52.4%) │
│   • Tier 2 (T20I Full Member):        80 batters (47.6%) │
│   • Tier 3 (Associate / Emerging):     0 batters  (0.0%) │
├──────────────────────────────────────────────────────────┤
│ Bowlers (N = 221):                                       │
│   • Tier 1 (IPL):                     92 bowlers (41.6%) │
│   • Tier 2 (T20I Full Member):       124 bowlers (56.1%) │
│   • Tier 3 (Associate / Emerging):     5 bowlers  (2.3%) │
└──────────────────────────────────────────────────────────┘
```

By coupling the volume floor with the dual-match requirement ($\ge 5$ Tier 1/2 matches) and evidence weight discounting ($\tau_{\text{tier}} = 0.50$ for Associate matches), the pipeline guarantees that:
1. Pure Associate mismatches cannot exploit short-sample spikes to displace elite tournament players.
2. Full Member international stars (e.g., Pathum Nissanka, Reeza Hendricks, Shaheen Shah Afridi, Mohammad Nawaz) receive equal, rigorous standing alongside IPL mainstays (Suryakumar Yadav, Virat Kohli, Josh Hazlewood, Lockie Ferguson).
3. Both the batting and bowling candidate pools possess substantial statistical depth (168 batters, 221 bowlers) for final ranking construction in Phase 6.

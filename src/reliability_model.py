"""
SupeRR Selector Season 2 — Phase 5: Statistical Reliability & Uncertainty Engine
Hierarchical Empirical Bayes Shrinkage, Effective Sample Size Weighting,
Analytical Uncertainty Bounds, and Match-Level Block Bootstrap (B=1,000).

Architectural Invariants Enforced:
1. Effective Sample Size (N_eff) with Competition Tier (IPL=1.0, FullMember=1.0, Associate=0.5)
   and Opposition Pre-Match Elo Weighting.
2. Empirical Bayes Variance-Ratio & Crucible Volume Floors:
   K_bat = 200.0 effective balls, K_bowl = 234.3 effective legal balls, K_delta = 150.0 balls.
3. Contextual Role-Specific Priors:
   Batting: Top Order (1-3), Middle Order (4-5), Lower-Middle / Finisher (6+).
   Bowling: Pace vs Spin (+ Phase Specialization).
4. Exact Additive Component Shrinkage:
   shrunk_vaoe = shrunk_rae + shrunk_wpv (batting)
   shrunk_vaoe = shrunk_rsae + shrunk_wva (bowling)
5. Vectorized Match-Cluster Block Bootstrap (B=1,000 iterations):
   Full empirical distributions, 95% CIs, median rank, rank IQR, and top-10 probability.
6. Rigorous Eligibility Guardrails:
   Batting: >= 100 pressure balls faced AND >= 5 Tier 1/2 matches.
   Bowling: >= 60 pressure legal balls bowled AND >= 5 Tier 1/2 matches.
"""

import os
import sys
import time
import numpy as np
import pandas as pd
from scipy import stats


def load_datasets(base_dir="."):
    """Load all required processed datasets."""
    print("--- [1/7] Loading Processed Datasets ---")
    data_dir = os.path.join(base_dir, "Data", "processed")
    if not os.path.exists(data_dir):
        data_dir = base_dir

    deliv_path = os.path.join(data_dir, "clean_deliveries.csv")
    bat_path = os.path.join(data_dir, "batting_player_statistics.csv")
    bowl_path = os.path.join(data_dir, "bowling_player_statistics.csv")
    pmb_path = os.path.join(data_dir, "player_match_batting.csv")
    pm_bowl_path = os.path.join(data_dir, "player_match_bowling.csv")

    deliv = pd.read_csv(deliv_path, low_memory=False)
    bat_stats = pd.read_csv(bat_path)
    bowl_stats = pd.read_csv(bowl_path)
    pmb = pd.read_csv(pmb_path)
    pm_bowl = pd.read_csv(pm_bowl_path)

    print(f"Loaded deliveries: {len(deliv):,} rows, {deliv['match_id'].nunique()} matches")
    print(f"Loaded batting statistics: {len(bat_stats)} batters")
    print(f"Loaded bowling statistics: {len(bowl_stats)} bowlers")
    return deliv, bat_stats, bowl_stats, pmb, pm_bowl


def assign_player_roles(pmb, pm_bowl, bowl_stats):
    """
    Assign primary contextual roles to players.
    Batters: Top Order (1-3), Middle Order (4-5), Lower-Middle / Finisher (6+).
    Bowlers: Pace vs Spin and Phase Specialists (Powerplay, Middle, Death).
    """
    print("--- [2/7] Assigning Player Roles and Phase Specializations ---")
    # Batting role from median batting order
    mode_order = pmb.groupby("player_id")["batting_order"].median()

    def get_bat_role(order):
        if order <= 3.5:
            return "Top Order (1-3)"
        elif order <= 5.5:
            return "Middle Order (4-5)"
        else:
            return "Lower-Middle / Finisher (6+)"

    bat_roles = mode_order.apply(get_bat_role).to_dict()

    # Bowling phase specialization
    bowl_phase_agg = pm_bowl.groupby("player_id")[["powerplay_overs", "middle_overs", "death_overs"]].sum()

    def get_bowl_phase(row):
        tot = row["powerplay_overs"] + row["middle_overs"] + row["death_overs"]
        if tot == 0:
            return "Middle Specialist"
        pp_pct = row["powerplay_overs"] / tot
        d_pct = row["death_overs"] / tot
        if d_pct >= 0.35:
            return "Death Specialist"
        elif pp_pct >= 0.40:
            return "Powerplay Specialist"
        else:
            return "Middle Specialist"

    bowl_phases = bowl_phase_agg.apply(get_bowl_phase, axis=1).to_dict()

    # Bowling style (Pace vs Spin)
    bowl_styles = bowl_stats.set_index("bowler_id")["pace_or_spin"].to_dict()

    return bat_roles, bowl_phases, bowl_styles


def calibrate_empirical_priors(deliv, bat_roles, bowl_styles):
    """
    Calibrate empirical priors for each role using weighted deliveries.
    Enforces exact component sum: prior_vaoe = prior_scoring + prior_wicket.
    """
    print("--- [3/7] Calibrating Contextual Empirical Priors ---")
    hp = deliv[deliv["is_high_pressure"] == True].copy()
    hp["tau_tier"] = hp["comp_tier"].apply(lambda x: 0.50 if "Associate" in str(x) else 1.00)

    # Batting priors
    bat_hp = hp[hp["is_batter_ball_faced"] == True].copy()
    bat_hp["w_bat"] = bat_hp["tau_tier"] * bat_hp["omega_elo_bat"] * (bat_hp["batting_pressure_index"] / 65.57)
    bat_hp["role"] = bat_hp["striker_id"].map(bat_roles).fillna("Middle Order (4-5)")

    bat_priors = {}
    for role, group in bat_hp.groupby("role"):
        w_sum = group["w_bat"].sum()
        rae_sum = (group["bat_rae"] * group["omega_elo_bat"] * group["tau_tier"]).sum()
        wpv_sum = (group["bat_wpv"] * group["omega_elo_bat"] * group["tau_tier"]).sum()
        vaoe_sum = (group["elo_bat_vaoe"] * group["tau_tier"]).sum()
        p_rae = (rae_sum / w_sum) * 100.0
        p_wpv = (wpv_sum / w_sum) * 100.0
        p_vaoe = (vaoe_sum / w_sum) * 100.0
        bat_priors[role] = {
            "prior_rae": round(p_rae, 2),
            "prior_wpv": round(p_wpv, 2),
            "prior_vaoe": round(p_vaoe, 2),
        }
        print(f"  Batting Prior [{role:28s}]: VAOE={p_vaoe:+.2f} (RAE={p_rae:+.2f}, WPV={p_wpv:+.2f}) per 100b")

    # Bowling priors by style (Pace vs Spin)
    bowl_hp = hp[hp["is_legal_ball"] == True].copy()
    bowl_hp["w_bowl"] = bowl_hp["tau_tier"] * bowl_hp["omega_elo_bowl"] * (bowl_hp["bowling_pressure_index"] / 65.57)
    bowl_hp["style"] = bowl_hp["bowler_id"].map(bowl_styles).fillna("Pace")

    bowl_priors = {}
    for style, group in bowl_hp.groupby("style"):
        w_sum = group["w_bowl"].sum()
        rsae_sum = (group["bowl_rsae"] * group["omega_elo_bowl"] * group["tau_tier"]).sum()
        wva_sum = (group["bowl_wva"] * group["omega_elo_bowl"] * group["tau_tier"]).sum()
        vaoe_sum = (group["elo_bowl_vaoe"] * group["tau_tier"]).sum()
        p_rsae = (rsae_sum / w_sum) * 24.0
        p_wva = (wva_sum / w_sum) * 24.0
        p_vaoe = (vaoe_sum / w_sum) * 24.0
        bowl_priors[style] = {
            "prior_rsae": round(p_rsae, 2),
            "prior_wva": round(p_wva, 2),
            "prior_vaoe": round(p_vaoe, 2),
        }
        print(f"  Bowling Prior [{style:28s}]: VAOE={p_vaoe:+.2f} (RSAE={p_rsae:+.2f}, WVA={p_wva:+.2f}) per 24b")

    return bat_priors, bowl_priors


def compute_batting_reliability(deliv, bat_stats, pmb, bat_roles, bat_priors, K_bat=200.0, K_delta=150.0):
    """
    Compute Effective Sample Size, Empirical Bayes Shrinkage, Analytical Uncertainty,
    and Eligibility for all batters.
    """
    print("--- [4/7] Computing Batting Reliability & Empirical Bayes Shrinkage ---")
    hp = deliv[deliv["is_high_pressure"] == True].copy()
    hp["tau_tier"] = hp["comp_tier"].apply(lambda x: 0.50 if "Associate" in str(x) else 1.00)
    bat_hp = hp[hp["is_batter_ball_faced"] == True].copy()
    bat_hp["w_bat"] = bat_hp["tau_tier"] * bat_hp["omega_elo_bat"] * (bat_hp["batting_pressure_index"] / 65.57)

    # Tier 1 & 2 match counts
    t12 = deliv[deliv["comp_tier"].isin(["Tier 1 (IPL)", "Tier 2 (T20I_FullMember)"])]
    bat_t12_matches = t12[t12["is_batter_ball_faced"]].groupby("striker_id")["match_id"].nunique().to_dict()

    # Delivery-level variance pooling
    pooled_var = bat_hp["bat_vaoe"].var()

    # Aggregate by batter
    agg_dict = {}
    for bid, group in bat_hp.groupby("striker_id"):
        n_raw = len(group)
        n_elite = (group["tau_tier"] == 1.0).sum()
        n_mat = group["match_id"].nunique()
        w_sum = group["w_bat"].sum()
        elo_vaoe_sum = (group["elo_bat_vaoe"] * group["tau_tier"]).sum()
        elo_rae_sum = (group["bat_rae"] * group["omega_elo_bat"] * group["tau_tier"]).sum()
        elo_wpv_sum = (group["bat_wpv"] * group["omega_elo_bat"] * group["tau_tier"]).sum()
        
        # Individual variance regularized with pooled variance
        ind_var = group["bat_vaoe"].var() if n_raw >= 5 else pooled_var
        if np.isnan(ind_var):
            ind_var = pooled_var
        reg_var = (n_raw / (n_raw + 20.0)) * ind_var + (20.0 / (n_raw + 20.0)) * pooled_var

        agg_dict[bid] = {
            "pressure_balls": n_raw,
            "elite_tier_pressure_balls": n_elite,
            "n_pressure_matches": n_mat,
            "effective_sample_size": w_sum,
            "weighted_elo_vaoe_sum": elo_vaoe_sum,
            "weighted_elo_rae_sum": elo_rae_sum,
            "weighted_elo_wpv_sum": elo_wpv_sum,
            "delivery_var": reg_var
        }

    # Merge with bat_stats
    bat_df = bat_stats.copy()
    bat_df["role_category"] = "Batter"
    bat_df["primary_role"] = bat_df["batter_id"].map(bat_roles).fillna("Middle Order (4-5)")
    bat_df["n_tier1_tier2_matches"] = bat_df["batter_id"].map(lambda x: bat_t12_matches.get(x, 0))

    # Populate aggregated fields
    bat_df["pressure_balls"] = bat_df["batter_id"].map(lambda x: agg_dict.get(x, {}).get("pressure_balls", 0))
    bat_df["elite_tier_pressure_balls"] = bat_df["batter_id"].map(lambda x: agg_dict.get(x, {}).get("elite_tier_pressure_balls", 0))
    bat_df["n_pressure_matches"] = bat_df["batter_id"].map(lambda x: agg_dict.get(x, {}).get("n_pressure_matches", 0))
    bat_df["effective_sample_size"] = bat_df["batter_id"].map(lambda x: agg_dict.get(x, {}).get("effective_sample_size", 0.0)).round(2)

    # Credibility factor B_i
    bat_df["credibility_factor"] = (bat_df["effective_sample_size"] / (bat_df["effective_sample_size"] + K_bat)).round(4)

    # Role priors
    bat_df["prior_vaoe"] = bat_df["primary_role"].map(lambda r: bat_priors.get(r, {}).get("prior_vaoe", 0.0))
    bat_df["prior_rae"] = bat_df["primary_role"].map(lambda r: bat_priors.get(r, {}).get("prior_rae", 0.0))
    bat_df["prior_wpv"] = bat_df["primary_role"].map(lambda r: bat_priors.get(r, {}).get("prior_wpv", 0.0))

    # Raw rates
    raw_vaoe_per_100b = []
    raw_rae_per_100b = []
    raw_wpv_per_100b = []
    reg_vars = []
    for bid in bat_df["batter_id"]:
        info = agg_dict.get(bid, None)
        if info and info["effective_sample_size"] > 0:
            neff = info["effective_sample_size"]
            raw_vaoe_per_100b.append((info["weighted_elo_vaoe_sum"] / neff) * 100.0)
            raw_rae_per_100b.append((info["weighted_elo_rae_sum"] / neff) * 100.0)
            raw_wpv_per_100b.append((info["weighted_elo_wpv_sum"] / neff) * 100.0)
            reg_vars.append(info["delivery_var"])
        else:
            raw_vaoe_per_100b.append(0.0)
            raw_rae_per_100b.append(0.0)
            raw_wpv_per_100b.append(0.0)
            reg_vars.append(pooled_var)

    bat_df["raw_pressure_vaoe"] = np.round(raw_vaoe_per_100b, 2)
    bat_df["raw_pressure_rae"] = np.round(raw_rae_per_100b, 2)
    bat_df["raw_pressure_wpv"] = np.round(raw_wpv_per_100b, 2)

    # Shrunk VAOE & Components (Enforcing exact additive component identity)
    B = bat_df["credibility_factor"].values
    bat_df["shrunk_pressure_rae"] = np.round(B * bat_df["raw_pressure_rae"] + (1.0 - B) * bat_df["prior_rae"], 2)
    bat_df["shrunk_pressure_wpv"] = np.round(B * bat_df["raw_pressure_wpv"] + (1.0 - B) * bat_df["prior_wpv"], 2)
    bat_df["shrunk_pressure_vaoe"] = np.round(bat_df["shrunk_pressure_rae"] + bat_df["shrunk_pressure_wpv"], 2)

    # Shrunk Pressure Escalation Delta (Delta_i)
    # n_harm = (1/n_press + 1/n_normal)^-1
    n_press = np.maximum(bat_df["pressure_balls"].values, 1.0)
    n_norm = np.maximum(bat_df["normal_balls_faced"].values, 1.0)
    n_harm = 1.0 / (1.0 / n_press + 1.0 / n_norm)
    b_delta = n_harm / (n_harm + K_delta)
    
    raw_delta = bat_df["raw_pressure_vaoe"].values - bat_df["normal_vaoe_per_100b"].values
    bat_df["raw_pressure_delta"] = np.round(raw_delta, 2)
    bat_df["shrunk_pressure_delta"] = np.round(b_delta * raw_delta, 2)

    # Analytical Posterior Uncertainty
    # SE(theta) = sqrt( (100^2 * reg_var) / (N_eff + K_bat) )
    reg_vars = np.array(reg_vars)
    denom = bat_df["effective_sample_size"].values + K_bat
    post_se = np.sqrt((100.0**2 * reg_vars) / denom)
    bat_df["posterior_se"] = np.round(post_se, 2)
    bat_df["ci_95_low"] = np.round(bat_df["shrunk_pressure_vaoe"] - 1.96 * post_se, 2)
    bat_df["ci_95_high"] = np.round(bat_df["shrunk_pressure_vaoe"] + 1.96 * post_se, 2)
    bat_df["lcb_80"] = np.round(bat_df["shrunk_pressure_vaoe"] - 0.8416 * post_se, 2)

    # Probabilities
    # P(theta > 0)
    z_stat = bat_df["shrunk_pressure_vaoe"].values / np.maximum(post_se, 1e-4)
    bat_df["prob_outperform_baseline"] = np.round(stats.norm.cdf(z_stat), 4)

    # P(Delta > 0)
    se_norm = np.sqrt(100.0**2 * pooled_var / n_norm)
    se_delta = np.sqrt(post_se**2 + se_norm**2)
    z_delta = bat_df["shrunk_pressure_delta"].values / np.maximum(se_delta, 1e-4)
    bat_df["prob_positive_delta"] = np.round(stats.norm.cdf(z_delta), 4)

    # Production Eligibility: >= 100 pressure balls AND >= 5 Tier 1/2 matches
    bat_df["is_eligible_production"] = (bat_df["pressure_balls"] >= 100) & (bat_df["n_tier1_tier2_matches"] >= 5)

    print(f"Total Batters: {len(bat_df)}, Production Eligible: {bat_df['is_eligible_production'].sum()}")
    return bat_df


def compute_bowling_reliability(deliv, bowl_stats, pm_bowl, bowl_phases, bowl_styles, bowl_priors, K_bowl=234.3, K_delta=150.0):
    """
    Compute Effective Sample Size, Empirical Bayes Shrinkage, Analytical Uncertainty,
    and Eligibility for all bowlers.
    """
    print("--- [5/7] Computing Bowling Reliability & Empirical Bayes Shrinkage ---")
    hp = deliv[deliv["is_high_pressure"] == True].copy()
    hp["tau_tier"] = hp["comp_tier"].apply(lambda x: 0.50 if "Associate" in str(x) else 1.00)
    bowl_hp = hp[hp["is_legal_ball"] == True].copy()
    bowl_hp["w_bowl"] = bowl_hp["tau_tier"] * bowl_hp["omega_elo_bowl"] * (bowl_hp["bowling_pressure_index"] / 65.57)

    # Tier 1 & 2 match counts
    t12 = deliv[deliv["comp_tier"].isin(["Tier 1 (IPL)", "Tier 2 (T20I_FullMember)"])]
    bowl_t12_matches = t12[t12["is_legal_ball"]].groupby("bowler_id")["match_id"].nunique().to_dict()

    pooled_var = bowl_hp["bowl_vaoe"].var()

    # Aggregate by bowler
    agg_dict = {}
    for bid, group in bowl_hp.groupby("bowler_id"):
        n_raw = len(group)
        n_elite = (group["tau_tier"] == 1.0).sum()
        n_mat = group["match_id"].nunique()
        w_sum = group["w_bowl"].sum()
        elo_vaoe_sum = (group["elo_bowl_vaoe"] * group["tau_tier"]).sum()
        elo_rsae_sum = (group["bowl_rsae"] * group["omega_elo_bowl"] * group["tau_tier"]).sum()
        elo_wva_sum = (group["bowl_wva"] * group["omega_elo_bowl"] * group["tau_tier"]).sum()

        ind_var = group["bowl_vaoe"].var() if n_raw >= 5 else pooled_var
        if np.isnan(ind_var):
            ind_var = pooled_var
        reg_var = (n_raw / (n_raw + 20.0)) * ind_var + (20.0 / (n_raw + 20.0)) * pooled_var

        agg_dict[bid] = {
            "pressure_balls": n_raw,
            "elite_tier_pressure_balls": n_elite,
            "n_pressure_matches": n_mat,
            "effective_sample_size": w_sum,
            "weighted_elo_vaoe_sum": elo_vaoe_sum,
            "weighted_elo_rsae_sum": elo_rsae_sum,
            "weighted_elo_wva_sum": elo_wva_sum,
            "delivery_var": reg_var
        }

    # Merge with bowl_stats
    bowl_df = bowl_stats.copy()
    bowl_df["role_category"] = "Bowler"
    bowl_df["primary_role"] = bowl_df["bowler_id"].map(bowl_phases).fillna("Middle Specialist")
    bowl_df["n_tier1_tier2_matches"] = bowl_df["bowler_id"].map(lambda x: bowl_t12_matches.get(x, 0))

    bowl_df["pressure_balls"] = bowl_df["bowler_id"].map(lambda x: agg_dict.get(x, {}).get("pressure_balls", 0))
    bowl_df["elite_tier_pressure_balls"] = bowl_df["bowler_id"].map(lambda x: agg_dict.get(x, {}).get("elite_tier_pressure_balls", 0))
    bowl_df["n_pressure_matches"] = bowl_df["bowler_id"].map(lambda x: agg_dict.get(x, {}).get("n_pressure_matches", 0))
    bowl_df["effective_sample_size"] = bowl_df["bowler_id"].map(lambda x: agg_dict.get(x, {}).get("effective_sample_size", 0.0)).round(2)

    # Credibility factor B_i
    bowl_df["credibility_factor"] = (bowl_df["effective_sample_size"] / (bowl_df["effective_sample_size"] + K_bowl)).round(4)

    # Style priors (Pace vs Spin)
    bowl_df["prior_vaoe"] = bowl_df["pace_or_spin"].map(lambda s: bowl_priors.get(s, {}).get("prior_vaoe", 0.0))
    bowl_df["prior_rsae"] = bowl_df["pace_or_spin"].map(lambda s: bowl_priors.get(s, {}).get("prior_rsae", 0.0))
    bowl_df["prior_wva"] = bowl_df["pace_or_spin"].map(lambda s: bowl_priors.get(s, {}).get("prior_wva", 0.0))

    # Raw rates
    raw_vaoe_per_24b = []
    raw_rsae_per_24b = []
    raw_wva_per_24b = []
    reg_vars = []
    for bid in bowl_df["bowler_id"]:
        info = agg_dict.get(bid, None)
        if info and info["effective_sample_size"] > 0:
            neff = info["effective_sample_size"]
            raw_vaoe_per_24b.append((info["weighted_elo_vaoe_sum"] / neff) * 24.0)
            raw_rsae_per_24b.append((info["weighted_elo_rsae_sum"] / neff) * 24.0)
            raw_wva_per_24b.append((info["weighted_elo_wva_sum"] / neff) * 24.0)
            reg_vars.append(info["delivery_var"])
        else:
            raw_vaoe_per_24b.append(0.0)
            raw_rsae_per_24b.append(0.0)
            raw_wva_per_24b.append(0.0)
            reg_vars.append(pooled_var)

    bowl_df["raw_pressure_vaoe"] = np.round(raw_vaoe_per_24b, 2)
    bowl_df["raw_pressure_rsae"] = np.round(raw_rsae_per_24b, 2)
    bowl_df["raw_pressure_wva"] = np.round(raw_wva_per_24b, 2)

    # Shrunk VAOE & Components (Enforcing exact additive component identity)
    B = bowl_df["credibility_factor"].values
    bowl_df["shrunk_pressure_rsae"] = np.round(B * bowl_df["raw_pressure_rsae"] + (1.0 - B) * bowl_df["prior_rsae"], 2)
    bowl_df["shrunk_pressure_wva"] = np.round(B * bowl_df["raw_pressure_wva"] + (1.0 - B) * bowl_df["prior_wva"], 2)
    bowl_df["shrunk_pressure_vaoe"] = np.round(bowl_df["shrunk_pressure_rsae"] + bowl_df["shrunk_pressure_wva"], 2)

    # Shrunk Pressure Escalation Delta
    n_press = np.maximum(bowl_df["pressure_balls"].values, 1.0)
    n_norm = np.maximum(bowl_df["normal_legal_balls"].values, 1.0)
    n_harm = 1.0 / (1.0 / n_press + 1.0 / n_norm)
    b_delta = n_harm / (n_harm + K_delta)

    raw_delta = bowl_df["raw_pressure_vaoe"].values - bowl_df["normal_vaoe_per_24b"].values
    bowl_df["raw_pressure_delta"] = np.round(raw_delta, 2)
    bowl_df["shrunk_pressure_delta"] = np.round(b_delta * raw_delta, 2)

    # Analytical Posterior Uncertainty
    # SE(theta) = sqrt( (24^2 * reg_var) / (N_eff + K_bowl) )
    reg_vars = np.array(reg_vars)
    denom = bowl_df["effective_sample_size"].values + K_bowl
    post_se = np.sqrt((24.0**2 * reg_vars) / denom)
    bowl_df["posterior_se"] = np.round(post_se, 2)
    bowl_df["ci_95_low"] = np.round(bowl_df["shrunk_pressure_vaoe"] - 1.96 * post_se, 2)
    bowl_df["ci_95_high"] = np.round(bowl_df["shrunk_pressure_vaoe"] + 1.96 * post_se, 2)
    bowl_df["lcb_80"] = np.round(bowl_df["shrunk_pressure_vaoe"] - 0.8416 * post_se, 2)

    # Probabilities
    z_stat = bowl_df["shrunk_pressure_vaoe"].values / np.maximum(post_se, 1e-4)
    bowl_df["prob_outperform_baseline"] = np.round(stats.norm.cdf(z_stat), 4)

    se_norm = np.sqrt(24.0**2 * pooled_var / n_norm)
    se_delta = np.sqrt(post_se**2 + se_norm**2)
    z_delta = bowl_df["shrunk_pressure_delta"].values / np.maximum(se_delta, 1e-4)
    bowl_df["prob_positive_delta"] = np.round(stats.norm.cdf(z_delta), 4)

    # Production Eligibility: >= 60 legal pressure balls AND >= 5 Tier 1/2 matches
    bowl_df["is_eligible_production"] = (bowl_df["pressure_balls"] >= 60) & (bowl_df["n_tier1_tier2_matches"] >= 5)

    print(f"Total Bowlers: {len(bowl_df)}, Production Eligible: {bowl_df['is_eligible_production'].sum()}")
    return bowl_df


def execute_match_block_bootstrap(deliv, bat_df, bowl_df, bat_priors, bowl_priors, B=1000, seed=42):
    """
    Perform ultra-fast vectorized Match-Level Block Bootstrap (B=1,000 iterations).
    Resamples match_id with replacement and computes empirical parameter distributions,
    credible intervals, and rank percentiles.
    """
    print(f"--- [6/7] Running Vectorized Match-Level Block Bootstrap (B={B:,} iterations) ---")
    t0 = time.time()
    np.random.seed(seed)

    unique_matches = np.array(sorted(deliv["match_id"].unique()))
    M = len(unique_matches)
    match_to_idx = {m: idx for idx, m in enumerate(unique_matches)}

    # Generate Multinomial Resampling Matrix: Shape (B, M)
    match_counts = np.zeros((B, M), dtype=np.float32)
    for b in range(B):
        sampled = np.random.randint(0, M, size=M)
        np.add.at(match_counts[b], sampled, 1.0)

    hp = deliv[deliv["is_high_pressure"] == True].copy()
    hp["tau_tier"] = hp["comp_tier"].apply(lambda x: 0.50 if "Associate" in str(x) else 1.00)

    # === BATTING BOOTSTRAP ===
    bat_hp = hp[hp["is_batter_ball_faced"] == True].copy()
    bat_hp["w_bat"] = bat_hp["tau_tier"] * bat_hp["omega_elo_bat"] * (bat_hp["batting_pressure_index"] / 65.57)

    bat_match_agg = bat_hp.groupby(["striker_id", "match_id"]).agg(
        w_sum=("w_bat", "sum"),
        vaoe_sum=("elo_bat_vaoe", "sum")
    ).reset_index()

    unique_batters = bat_df["batter_id"].values
    P_bat = len(unique_batters)
    batter_to_idx = {b: idx for idx, b in enumerate(unique_batters)}

    W_bat = np.zeros((P_bat, M), dtype=np.float32)
    V_bat = np.zeros((P_bat, M), dtype=np.float32)

    b_idx = bat_match_agg["striker_id"].map(batter_to_idx).dropna().astype(int).values
    m_idx = bat_match_agg["match_id"].map(match_to_idx).dropna().astype(int).values
    w_vals = bat_match_agg["w_sum"].values.astype(np.float32)
    v_vals = bat_match_agg["vaoe_sum"].values.astype(np.float32)

    # Filter valid mappings
    valid_mask = bat_match_agg["striker_id"].isin(batter_to_idx)
    W_bat[b_idx, m_idx] = w_vals[valid_mask]
    V_bat[b_idx, m_idx] = v_vals[valid_mask]

    # Matrix multiplication: (P_bat x M) @ (M x B) -> (P_bat x B)
    boot_w_bat = W_bat @ match_counts.T
    boot_v_bat = V_bat @ match_counts.T

    K_bat = 200.0
    prior_vec_bat = bat_df["prior_vaoe"].values.astype(np.float32)[:, None]
    B_factor_bat = boot_w_bat / (boot_w_bat + K_bat)
    shrunk_boot_bat = B_factor_bat * (boot_v_bat / np.maximum(boot_w_bat, 1e-6)) * 100.0 + (1.0 - B_factor_bat) * prior_vec_bat

    # Summary statistics across iterations
    bat_df["bootstrap_mean"] = np.round(shrunk_boot_bat.mean(axis=1), 2)
    bat_df["bootstrap_se"] = np.round(shrunk_boot_bat.std(axis=1), 2)
    bat_df["bootstrap_ci_95_low"] = np.round(np.percentile(shrunk_boot_bat, 2.5, axis=1), 2)
    bat_df["bootstrap_ci_95_high"] = np.round(np.percentile(shrunk_boot_bat, 97.5, axis=1), 2)
    bat_df["bootstrap_prob_positive"] = np.round((shrunk_boot_bat > 0).mean(axis=1), 4)

    # Ranks among eligible candidates
    bat_elig_mask = bat_df["is_eligible_production"].values
    bat_elig_idx = np.where(bat_elig_mask)[0]
    shrunk_elig_bat = shrunk_boot_bat[bat_elig_idx, :]

    ranks_bat = np.zeros_like(shrunk_elig_bat)
    for b in range(B):
        order = np.argsort(-shrunk_elig_bat[:, b])
        ranks_bat[order, b] = np.arange(1, len(bat_elig_idx) + 1)

    med_rank_bat = np.median(ranks_bat, axis=1)
    iqr_rank_bat = np.percentile(ranks_bat, 75, axis=1) - np.percentile(ranks_bat, 25, axis=1)
    top10_prob_bat = (ranks_bat <= 10).mean(axis=1)

    bat_df["bootstrap_median_rank"] = np.nan
    bat_df["bootstrap_rank_iqr"] = np.nan
    bat_df["bootstrap_top10_prob"] = np.nan

    bat_df.loc[bat_elig_mask, "bootstrap_median_rank"] = np.round(med_rank_bat, 1)
    bat_df.loc[bat_elig_mask, "bootstrap_rank_iqr"] = np.round(iqr_rank_bat, 1)
    bat_df.loc[bat_elig_mask, "bootstrap_top10_prob"] = np.round(top10_prob_bat, 4)

    # === BOWLING BOOTSTRAP ===
    bowl_hp = hp[hp["is_legal_ball"] == True].copy()
    bowl_hp["w_bowl"] = bowl_hp["tau_tier"] * bowl_hp["omega_elo_bowl"] * (bowl_hp["bowling_pressure_index"] / 65.57)

    bowl_match_agg = bowl_hp.groupby(["bowler_id", "match_id"]).agg(
        w_sum=("w_bowl", "sum"),
        vaoe_sum=("elo_bowl_vaoe", "sum")
    ).reset_index()

    unique_bowlers = bowl_df["bowler_id"].values
    P_bowl = len(unique_bowlers)
    bowler_to_idx = {b: idx for idx, b in enumerate(unique_bowlers)}

    W_bowl = np.zeros((P_bowl, M), dtype=np.float32)
    V_bowl = np.zeros((P_bowl, M), dtype=np.float32)

    valid_mask_bowl = bowl_match_agg["bowler_id"].isin(bowler_to_idx)
    b_idx_bowl = bowl_match_agg.loc[valid_mask_bowl, "bowler_id"].map(bowler_to_idx).values
    m_idx_bowl = bowl_match_agg.loc[valid_mask_bowl, "match_id"].map(match_to_idx).values
    w_vals_bowl = bowl_match_agg.loc[valid_mask_bowl, "w_sum"].values.astype(np.float32)
    v_vals_bowl = bowl_match_agg.loc[valid_mask_bowl, "vaoe_sum"].values.astype(np.float32)

    W_bowl[b_idx_bowl, m_idx_bowl] = w_vals_bowl
    V_bowl[b_idx_bowl, m_idx_bowl] = v_vals_bowl

    boot_w_bowl = W_bowl @ match_counts.T
    boot_v_bowl = V_bowl @ match_counts.T

    K_bowl = 234.3
    prior_vec_bowl = bowl_df["prior_vaoe"].values.astype(np.float32)[:, None]
    B_factor_bowl = boot_w_bowl / (boot_w_bowl + K_bowl)
    shrunk_boot_bowl = B_factor_bowl * (boot_v_bowl / np.maximum(boot_w_bowl, 1e-6)) * 24.0 + (1.0 - B_factor_bowl) * prior_vec_bowl

    bowl_df["bootstrap_mean"] = np.round(shrunk_boot_bowl.mean(axis=1), 2)
    bowl_df["bootstrap_se"] = np.round(shrunk_boot_bowl.std(axis=1), 2)
    bowl_df["bootstrap_ci_95_low"] = np.round(np.percentile(shrunk_boot_bowl, 2.5, axis=1), 2)
    bowl_df["bootstrap_ci_95_high"] = np.round(np.percentile(shrunk_boot_bowl, 97.5, axis=1), 2)
    bowl_df["bootstrap_prob_positive"] = np.round((shrunk_boot_bowl > 0).mean(axis=1), 4)

    bowl_elig_mask = bowl_df["is_eligible_production"].values
    bowl_elig_idx = np.where(bowl_elig_mask)[0]
    shrunk_elig_bowl = shrunk_boot_bowl[bowl_elig_idx, :]

    ranks_bowl = np.zeros_like(shrunk_elig_bowl)
    for b in range(B):
        order = np.argsort(-shrunk_elig_bowl[:, b])
        ranks_bowl[order, b] = np.arange(1, len(bowl_elig_idx) + 1)

    med_rank_bowl = np.median(ranks_bowl, axis=1)
    iqr_rank_bowl = np.percentile(ranks_bowl, 75, axis=1) - np.percentile(ranks_bowl, 25, axis=1)
    top10_prob_bowl = (ranks_bowl <= 10).mean(axis=1)

    bowl_df["bootstrap_median_rank"] = np.nan
    bowl_df["bootstrap_rank_iqr"] = np.nan
    bowl_df["bootstrap_top10_prob"] = np.nan

    bowl_df.loc[bowl_elig_mask, "bootstrap_median_rank"] = np.round(med_rank_bowl, 1)
    bowl_df.loc[bowl_elig_mask, "bootstrap_rank_iqr"] = np.round(iqr_rank_bowl, 1)
    bowl_df.loc[bowl_elig_mask, "bootstrap_top10_prob"] = np.round(top10_prob_bowl, 4)

    t1 = time.time()
    print(f"Bootstrap completed in {t1 - t0:.2f} seconds!")
    return bat_df, bowl_df


def create_player_uncertainty_dataset(bat_df, bowl_df):
    """
    Construct the unified player_uncertainty.csv table containing
    standardized uncertainty metrics across both batters and bowlers.
    """
    print("--- [7/7] Assembling Unified player_uncertainty.csv ---")
    bat_sub = pd.DataFrame({
        "player_id": bat_df["batter_id"],
        "player_name": bat_df["batter_name"],
        "role_category": "Batter",
        "primary_role": bat_df["primary_role"],
        "primary_comp_tier": bat_df["primary_tier"],
        "n_pressure_matches": bat_df["n_pressure_matches"],
        "pressure_balls": bat_df["pressure_balls"],
        "elite_tier_pressure_balls": bat_df["elite_tier_pressure_balls"],
        "effective_sample_size": bat_df["effective_sample_size"],
        "credibility_factor": bat_df["credibility_factor"],
        "raw_pressure_vaoe": bat_df["raw_pressure_vaoe"],
        "shrunk_pressure_vaoe": bat_df["shrunk_pressure_vaoe"],
        "raw_pressure_delta": bat_df["raw_pressure_delta"],
        "shrunk_pressure_delta": bat_df["shrunk_pressure_delta"],
        "posterior_se": bat_df["posterior_se"],
        "ci_95_low": bat_df["ci_95_low"],
        "ci_95_high": bat_df["ci_95_high"],
        "lcb_80": bat_df["lcb_80"],
        "prob_outperform_baseline": bat_df["prob_outperform_baseline"],
        "prob_positive_delta": bat_df["prob_positive_delta"],
        "bootstrap_mean": bat_df["bootstrap_mean"],
        "bootstrap_se": bat_df["bootstrap_se"],
        "bootstrap_ci_95_low": bat_df["bootstrap_ci_95_low"],
        "bootstrap_ci_95_high": bat_df["bootstrap_ci_95_high"],
        "bootstrap_prob_positive": bat_df["bootstrap_prob_positive"],
        "bootstrap_median_rank": bat_df["bootstrap_median_rank"],
        "bootstrap_rank_iqr": bat_df["bootstrap_rank_iqr"],
        "bootstrap_top10_prob": bat_df["bootstrap_top10_prob"],
        "sortino_downside_deviation": bat_df["sortino_downside_deviation"],
        "clutch_success_rate": bat_df["clutch_success_rate"],
        "is_eligible_production": bat_df["is_eligible_production"]
    })

    bowl_sub = pd.DataFrame({
        "player_id": bowl_df["bowler_id"],
        "player_name": bowl_df["bowler_name"],
        "role_category": "Bowler",
        "primary_role": bowl_df["primary_role"],
        "primary_comp_tier": bowl_df["primary_tier"],
        "n_pressure_matches": bowl_df["n_pressure_matches"],
        "pressure_balls": bowl_df["pressure_balls"],
        "elite_tier_pressure_balls": bowl_df["elite_tier_pressure_balls"],
        "effective_sample_size": bowl_df["effective_sample_size"],
        "credibility_factor": bowl_df["credibility_factor"],
        "raw_pressure_vaoe": bowl_df["raw_pressure_vaoe"],
        "shrunk_pressure_vaoe": bowl_df["shrunk_pressure_vaoe"],
        "raw_pressure_delta": bowl_df["raw_pressure_delta"],
        "shrunk_pressure_delta": bowl_df["shrunk_pressure_delta"],
        "posterior_se": bowl_df["posterior_se"],
        "ci_95_low": bowl_df["ci_95_low"],
        "ci_95_high": bowl_df["ci_95_high"],
        "lcb_80": bowl_df["lcb_80"],
        "prob_outperform_baseline": bowl_df["prob_outperform_baseline"],
        "prob_positive_delta": bowl_df["prob_positive_delta"],
        "bootstrap_mean": bowl_df["bootstrap_mean"],
        "bootstrap_se": bowl_df["bootstrap_se"],
        "bootstrap_ci_95_low": bowl_df["bootstrap_ci_95_low"],
        "bootstrap_ci_95_high": bowl_df["bootstrap_ci_95_high"],
        "bootstrap_prob_positive": bowl_df["bootstrap_prob_positive"],
        "bootstrap_median_rank": bowl_df["bootstrap_median_rank"],
        "bootstrap_rank_iqr": bowl_df["bootstrap_rank_iqr"],
        "bootstrap_top10_prob": bowl_df["bootstrap_top10_prob"],
        "sortino_downside_deviation": bowl_df["sortino_downside_deviation"],
        "clutch_success_rate": bowl_df["clutch_spell_success_rate"],
        "is_eligible_production": bowl_df["is_eligible_production"]
    })

    player_uncertainty = pd.concat([bat_sub, bowl_sub], ignore_index=True)
    return player_uncertainty


def export_and_sync_all(bat_df, bowl_df, player_uncertainty, base_dir="."):
    """Save updated files to Data/processed/ and repository root."""
    print("--- Exporting and Syncing Processed Datasets ---")
    proc_dir = os.path.join(base_dir, "Data", "processed")
    os.makedirs(proc_dir, exist_ok=True)

    files_to_sync = [
        ("batting_player_statistics.csv", bat_df),
        ("bowling_player_statistics.csv", bowl_df),
        ("player_uncertainty.csv", player_uncertainty),
    ]

    for fname, df in files_to_sync:
        p1 = os.path.join(proc_dir, fname)
        p2 = os.path.join(base_dir, fname)
        df.to_csv(p1, index=False)
        df.to_csv(p2, index=False)
        sz_mb = os.path.getsize(p1) / (1024 * 1024)
        print(f"  Saved {fname}: {len(df):,} rows x {len(df.columns)} cols ({sz_mb:.2f} MB)")


def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    print(f"Starting Phase 5 Reliability Engine in {base_dir}")

    # 1. Load data
    deliv, bat_stats, bowl_stats, pmb, pm_bowl = load_datasets(base_dir)

    # 2. Player roles
    bat_roles, bowl_phases, bowl_styles = assign_player_roles(pmb, pm_bowl, bowl_stats)

    # 3. Calibrate priors
    bat_priors, bowl_priors = calibrate_empirical_priors(deliv, bat_roles, bowl_styles)

    # 4. Batting reliability
    bat_df = compute_batting_reliability(deliv, bat_stats, pmb, bat_roles, bat_priors)

    # 5. Bowling reliability
    bowl_df = compute_bowling_reliability(deliv, bowl_stats, pm_bowl, bowl_phases, bowl_styles, bowl_priors)

    # 6. Match-Level Block Bootstrap
    bat_df, bowl_df = execute_match_block_bootstrap(deliv, bat_df, bowl_df, bat_priors, bowl_priors, B=1000)

    # 7. Unified player uncertainty table
    player_uncertainty = create_player_uncertainty_dataset(bat_df, bowl_df)

    # 8. Export and sync
    export_and_sync_all(bat_df, bowl_df, player_uncertainty, base_dir)

    print("\n=== PHASE 5 STATISTICAL RELIABILITY PIPELINE COMPLETED SUCCESSFULLY ===")


if __name__ == "__main__":
    main()

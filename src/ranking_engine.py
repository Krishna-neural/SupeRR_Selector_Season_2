"""
SupeRR Selector Season 2 — Phase 6: Final Player Ranking Engine & Top-10 Submission Lists
Mathematical Formulation & Comparison of Candidate Ranking Frameworks (Formulations 1, 2, 3),
Risk-Adjusted Certainty & Crucible Reliability Rating (CRR), and Deterministic Output Generation.

Architectural Invariants Enforced:
1. Refined Production Eligibility Criteria:
   - Batters: pressure_balls >= 120, n_pressure_matches >= 10, n_tier1_tier2_matches >= 8,
     primary_comp_tier in ['Tier 1 (IPL)', 'Tier 2 (T20I_FullMember)'].
   - Bowlers: pressure_legal_balls >= 120, n_pressure_matches >= 10, n_tier1_tier2_matches >= 8,
     primary_comp_tier in ['Tier 1 (IPL)', 'Tier 2 (T20I_FullMember)'].
2. Extreme Crucible Stress Testing (theta_extreme):
   - Empirical Bayes shrunk VAOE on deliveries where batting_pressure_index >= 75.0 / bowling_pressure_index >= 75.0.
3. Powerplay-Death Asymmetry Parity for Bowlers:
   - Incorporates role difficulty adjustment for bowlers handling high proportions of death overs (16-20).
4. Multi-Factor Composite Scoring (CRR):
   - Formulation 1: Pure Shrunk VAOE.
   - Formulation 2: Equal-Weighted Linear Composite (20% each).
   - Formulation 3 (Champion): Risk-Adjusted Certainty & Crucible Reliability Rating (CRR).
5. 0 to 100 Championship Index Scaling:
   - Standardized mapping where Rank #1 achieves 100.00 and components are transparently tabulated.
"""

import os
import sys
import numpy as np
import pandas as pd


def load_datasets(base_dir="."):
    """Load processed data and teams mapping."""
    print("--- [1/6] Loading Datasets for Phase 6 Ranking Engine ---")
    data_dir = os.path.join(base_dir, "Data", "processed")
    raw_dir = os.path.join(base_dir, "Data", "raw")
    if not os.path.exists(data_dir):
        data_dir = base_dir
    if not os.path.exists(raw_dir):
        raw_dir = base_dir

    deliv_path = os.path.join(data_dir, "clean_deliveries.csv")
    bat_path = os.path.join(data_dir, "batting_player_statistics.csv")
    bowl_path = os.path.join(data_dir, "bowling_player_statistics.csv")
    pu_path = os.path.join(data_dir, "player_uncertainty.csv")
    teams_path = os.path.join(raw_dir, "teams.csv")

    deliv = pd.read_csv(deliv_path, low_memory=False)
    bat_stats = pd.read_csv(bat_path)
    bowl_stats = pd.read_csv(bowl_path)
    pu = pd.read_csv(pu_path)
    teams_df = pd.read_csv(teams_path).drop_duplicates(subset=["team_id"])
    teams_map = teams_df.set_index("team_id")["team_name"].to_dict()

    print(f"Loaded {len(pu):,} player records across {len(deliv):,} deliveries")
    return deliv, bat_stats, bowl_stats, pu, teams_map


def compute_teams_represented(deliv, teams_map):
    """Map each player to comma-separated list of teams represented in corpus."""
    bat_teams = deliv.groupby("striker_id")["batting_team_id"].unique().to_dict()
    bowl_teams = deliv.groupby("bowler_id")["bowling_team_id"].unique().to_dict()

    def get_team_str(team_ids):
        names = [teams_map.get(tid, f"Team {tid}") for tid in team_ids if tid in teams_map]
        return ", ".join(sorted(set(names))) if names else "Unknown"

    bat_teams_str = {pid: get_team_str(tids) for pid, tids in bat_teams.items()}
    bowl_teams_str = {pid: get_team_str(tids) for pid, tids in bowl_teams.items()}
    return bat_teams_str, bowl_teams_str


def compute_extreme_crucible_vaoe(deliv, K_ext=100.0):
    """
    Compute Empirical Bayes shrunk VAOE on Extreme Crucible deliveries
    (pressure_index >= 75.0).
    """
    print("--- [2/6] Computing Extreme Crucible VAOE (Pressure Index >= 75.0) ---")
    hp = deliv[deliv["is_high_pressure"] == True].copy()
    hp["tau_tier"] = hp["comp_tier"].apply(lambda x: 0.50 if "Associate" in str(x) else 1.00)

    # Batting Extreme
    ext_bat = hp[(hp["is_batter_ball_faced"] == True) & (hp["batting_pressure_index"] >= 75.0)].copy()
    ext_bat["w_bat_ext"] = ext_bat["tau_tier"] * ext_bat["omega_elo_bat"] * (ext_bat["batting_pressure_index"] / 65.57)

    bat_ext_agg = ext_bat.groupby("striker_id").agg(
        ext_balls=("match_id", "count"),
        ext_neff=("w_bat_ext", "sum"),
        ext_elo_vaoe=("elo_bat_vaoe", "sum")
    ).reset_index().rename(columns={"striker_id": "batter_id"})

    bat_ext_agg["b_ext"] = bat_ext_agg["ext_neff"] / (bat_ext_agg["ext_neff"] + K_ext)
    bat_ext_agg["raw_ext_vaoe_per_100b"] = (bat_ext_agg["ext_elo_vaoe"] / bat_ext_agg["ext_neff"]) * 100.0
    bat_ext_agg["shrunk_ext_vaoe_per_100b"] = (
        bat_ext_agg["b_ext"] * bat_ext_agg["raw_ext_vaoe_per_100b"] +
        (1.0 - bat_ext_agg["b_ext"]) * 0.0
    ).round(2)

    # Bowling Extreme
    ext_bowl = hp[(hp["is_legal_ball"] == True) & (hp["bowling_pressure_index"] >= 75.0)].copy()
    ext_bowl["w_bowl_ext"] = ext_bowl["tau_tier"] * ext_bowl["omega_elo_bowl"] * (ext_bowl["bowling_pressure_index"] / 65.57)

    bowl_ext_agg = ext_bowl.groupby("bowler_id").agg(
        ext_balls=("match_id", "count"),
        ext_neff=("w_bowl_ext", "sum"),
        ext_elo_vaoe=("elo_bowl_vaoe", "sum")
    ).reset_index()

    bowl_ext_agg["b_ext"] = bowl_ext_agg["ext_neff"] / (bowl_ext_agg["ext_neff"] + K_ext)
    bowl_ext_agg["raw_ext_vaoe_per_24b"] = (bowl_ext_agg["ext_elo_vaoe"] / bowl_ext_agg["ext_neff"]) * 24.0
    bowl_ext_agg["shrunk_ext_vaoe_per_24b"] = (
        bowl_ext_agg["b_ext"] * bowl_ext_agg["raw_ext_vaoe_per_24b"] +
        (1.0 - bowl_ext_agg["b_ext"]) * (-0.20)
    ).round(2)

    # Compute death pressure balls percentage for bowlers
    hp_bowl = hp[hp["is_legal_ball"] == True].copy()
    death_pct_map = hp_bowl.groupby("bowler_id")["is_death"].mean().to_dict()

    return bat_ext_agg, bowl_ext_agg, death_pct_map


def robust_zscore(series):
    """Compute robust Z-score scaled by IQR/1.349, clipped at [-3.5, +3.5]."""
    med = series.median()
    iqr = series.quantile(0.75) - series.quantile(0.25)
    scale = (iqr / 1.349) if iqr > 1e-4 else series.std()
    if scale <= 1e-4:
        scale = 1.0
    z = (series - med) / scale
    return np.clip(z, -3.5, 3.5)


def build_batter_rankings(bat_stats, pu, bat_ext_agg, bat_teams_str):
    """
    Compute Formulations 1, 2, and 3 for all batters, flag refined eligibility,
    and scale Champion CRR to 0-100 scale.
    """
    print("--- [3/6] Building Comprehensive Batting Leaderboard & Formulations ---")
    bat_pu = pu[pu["role_category"] == "Batter"].copy()
    bat_pu["n_tier1_tier2_matches"] = bat_stats.set_index("batter_id").loc[bat_pu["player_id"], "n_tier1_tier2_matches"].values
    bat_pu = bat_pu.merge(bat_ext_agg[["batter_id", "shrunk_ext_vaoe_per_100b"]], left_on="player_id", right_on="batter_id", how="left")
    bat_pu["shrunk_ext_vaoe_per_100b"] = bat_pu["shrunk_ext_vaoe_per_100b"].fillna(0.0)

    # Refined Eligibility Filter
    bat_pu["is_eligible_final"] = (
        (bat_pu["pressure_balls"] >= 120) &
        (bat_pu["n_pressure_matches"] >= 10) &
        (bat_pu["n_tier1_tier2_matches"] >= 8) &
        (bat_pu["primary_comp_tier"].isin(["Tier 1 (IPL)", "Tier 2 (T20I_FullMember)"]))
    )

    elig = bat_pu[bat_pu["is_eligible_final"] == True].copy()
    print(f"Qualified Final Eligible Batters: {len(elig)} / {len(bat_pu)}")

    # Formulation 1: Pure Shrunk VAOE
    bat_pu["f1_score"] = bat_pu["shrunk_pressure_vaoe"]
    bat_pu["rank_f1"] = np.nan
    bat_pu.loc[bat_pu["is_eligible_final"], "rank_f1"] = elig["shrunk_pressure_vaoe"].rank(ascending=False).astype(int)

    # Formulation 2: Equal-Weighted Linear Composite (20% each)
    z_f2_vaoe = robust_zscore(elig["shrunk_pressure_vaoe"])
    z_f2_delta = robust_zscore(elig["shrunk_pressure_delta"])
    z_f2_clutch = robust_zscore(elig["clutch_success_rate"])
    z_f2_p0 = robust_zscore(elig["prob_outperform_baseline"])
    z_f2_sortino = robust_zscore(-elig["sortino_downside_deviation"])
    f2_comp = 0.20*z_f2_vaoe + 0.20*z_f2_delta + 0.20*z_f2_clutch + 0.20*z_f2_p0 + 0.20*z_f2_sortino
    bat_pu["f2_score"] = np.nan
    bat_pu["rank_f2"] = np.nan
    bat_pu.loc[bat_pu["is_eligible_final"], "f2_score"] = np.round(f2_comp, 4)
    bat_pu.loc[bat_pu["is_eligible_final"], "rank_f2"] = f2_comp.rank(ascending=False).astype(int)

    # Formulation 3 (Champion): Risk-Adjusted Certainty & Crucible Reliability Rating (CRR)
    # Delta clamped between -20 and +30 to prevent over-rewarding poor normal baselines
    delta_clamped = np.clip(elig["shrunk_pressure_delta"], -20.0, 30.0)
    consistency_adj = elig["clutch_success_rate"] - 0.5 * elig["sortino_downside_deviation"]

    z_f3_vaoe = robust_zscore(elig["shrunk_pressure_vaoe"])
    z_f3_lcb = robust_zscore(elig["lcb_80"])
    z_f3_ext = robust_zscore(elig["shrunk_ext_vaoe_per_100b"])
    z_f3_delta = robust_zscore(delta_clamped)
    z_f3_cons = robust_zscore(consistency_adj)

    crr_comp = (
        0.30 * z_f3_vaoe +
        0.25 * z_f3_lcb +
        0.15 * z_f3_ext +
        0.15 * z_f3_delta +
        0.15 * z_f3_cons
    )

    # Scale cleanly to 0-100 Championship Index scale
    z_min = crr_comp.min()
    z_max = crr_comp.max()
    crr_100 = 15.0 + 85.0 * ((crr_comp - z_min) / (z_max - z_min))

    bat_pu["crr_z_composite"] = np.nan
    bat_pu["final_crr_score_100"] = np.nan
    bat_pu["rank_crr"] = np.nan
    bat_pu.loc[bat_pu["is_eligible_final"], "crr_z_composite"] = np.round(crr_comp, 4)
    bat_pu.loc[bat_pu["is_eligible_final"], "final_crr_score_100"] = np.round(crr_100, 2)
    bat_pu.loc[bat_pu["is_eligible_final"], "rank_crr"] = crr_comp.rank(ascending=False).astype(int)

    # Merge auxiliary tactical details from bat_stats
    bat_pu["teams_represented"] = bat_pu["player_id"].map(lambda x: bat_teams_str.get(x, "Unknown"))
    
    stat_cols = [
        "pressure_runs", "pressure_strike_rate", "pressure_expected_strike_rate",
        "pressure_sr_residual", "pressure_batting_avg", "pressure_boundary_pct",
        "pressure_dot_pct", "normal_balls_faced", "normal_strike_rate",
        "normal_vaoe_per_100b", "shrunk_pressure_rae", "shrunk_pressure_wpv",
        "pressure_vaoe_vs_pace", "pressure_vaoe_vs_spin", "top_stroke",
        "off_side_pct", "leg_side_pct"
    ]
    for sc in stat_cols:
        if sc in bat_stats.columns:
            bat_pu[sc] = bat_stats.set_index("batter_id").loc[bat_pu["player_id"], sc].values

    return bat_pu


def build_bowler_rankings(bowl_stats, pu, bowl_ext_agg, death_pct_map, bowl_teams_str):
    """
    Compute Formulations 1, 2, and 3 for all bowlers, apply role difficulty adjustment,
    flag refined eligibility, and scale Champion CRR to 0-100 scale.
    """
    print("--- [4/6] Building Comprehensive Bowling Leaderboard & Formulations ---")
    bowl_pu = pu[pu["role_category"] == "Bowler"].copy()
    bowl_pu["n_tier1_tier2_matches"] = bowl_stats.set_index("bowler_id").loc[bowl_pu["player_id"], "n_tier1_tier2_matches"].values
    bowl_pu = bowl_pu.merge(bowl_ext_agg[["bowler_id", "shrunk_ext_vaoe_per_24b"]], left_on="player_id", right_on="bowler_id", how="left")
    bowl_pu["shrunk_ext_vaoe_per_24b"] = bowl_pu["shrunk_ext_vaoe_per_24b"].fillna(-0.20)
    bowl_pu["death_pressure_balls_pct"] = bowl_pu["player_id"].map(lambda x: round(death_pct_map.get(x, 0.0) * 100.0, 2))

    # Refined Eligibility Filter
    bowl_pu["is_eligible_final"] = (
        (bowl_pu["pressure_balls"] >= 120) &
        (bowl_pu["n_pressure_matches"] >= 10) &
        (bowl_pu["n_tier1_tier2_matches"] >= 8) &
        (bowl_pu["primary_comp_tier"].isin(["Tier 1 (IPL)", "Tier 2 (T20I_FullMember)"]))
    )

    elig = bowl_pu[bowl_pu["is_eligible_final"] == True].copy()
    print(f"Qualified Final Eligible Bowlers: {len(elig)} / {len(bowl_pu)}")

    # Formulation 1: Pure Shrunk VAOE
    bowl_pu["f1_score"] = bowl_pu["shrunk_pressure_vaoe"]
    bowl_pu["rank_f1"] = np.nan
    bowl_pu.loc[bowl_pu["is_eligible_final"], "rank_f1"] = elig["shrunk_pressure_vaoe"].rank(ascending=False).astype(int)

    # Formulation 2: Equal-Weighted Linear Composite (20% each)
    z_f2_vaoe = robust_zscore(elig["shrunk_pressure_vaoe"])
    z_f2_delta = robust_zscore(elig["shrunk_pressure_delta"])
    z_f2_clutch = robust_zscore(elig["clutch_success_rate"])
    z_f2_p0 = robust_zscore(elig["prob_outperform_baseline"])
    z_f2_sortino = robust_zscore(-elig["sortino_downside_deviation"])
    f2_comp = 0.20*z_f2_vaoe + 0.20*z_f2_delta + 0.20*z_f2_clutch + 0.20*z_f2_p0 + 0.20*z_f2_sortino
    bowl_pu["f2_score"] = np.nan
    bowl_pu["rank_f2"] = np.nan
    bowl_pu.loc[bowl_pu["is_eligible_final"], "f2_score"] = np.round(f2_comp, 4)
    bowl_pu.loc[bowl_pu["is_eligible_final"], "rank_f2"] = f2_comp.rank(ascending=False).astype(int)

    # Formulation 3 (Champion): Risk-Adjusted Certainty & Crucible Reliability Rating (CRR)
    # Role Difficulty Adjustment: Death Overs (16-20) carry high expected economy and thin margins
    diff_bonus = 2.0 * (elig["death_pressure_balls_pct"] / 100.0)
    theta_role_adj = elig["shrunk_pressure_vaoe"] + diff_bonus
    lcb_role_adj = elig["lcb_80"] + diff_bonus

    delta_clamped = np.clip(elig["shrunk_pressure_delta"], -10.0, 15.0)
    consistency_adj = elig["clutch_success_rate"] - 0.5 * elig["sortino_downside_deviation"]

    z_f3_vaoe = robust_zscore(theta_role_adj)
    z_f3_lcb = robust_zscore(lcb_role_adj)
    z_f3_ext = robust_zscore(elig["shrunk_ext_vaoe_per_24b"])
    z_f3_delta = robust_zscore(delta_clamped)
    z_f3_cons = robust_zscore(consistency_adj)

    crr_comp = (
        0.30 * z_f3_vaoe +
        0.25 * z_f3_lcb +
        0.20 * z_f3_ext +
        0.10 * z_f3_delta +
        0.15 * z_f3_cons
    )

    z_min = crr_comp.min()
    z_max = crr_comp.max()
    crr_100 = 15.0 + 85.0 * ((crr_comp - z_min) / (z_max - z_min))

    bowl_pu["crr_z_composite"] = np.nan
    bowl_pu["final_crr_score_100"] = np.nan
    bowl_pu["rank_crr"] = np.nan
    bowl_pu.loc[bowl_pu["is_eligible_final"], "crr_z_composite"] = np.round(crr_comp, 4)
    bowl_pu.loc[bowl_pu["is_eligible_final"], "final_crr_score_100"] = np.round(crr_100, 2)
    bowl_pu.loc[bowl_pu["is_eligible_final"], "rank_crr"] = crr_comp.rank(ascending=False).astype(int)

    bowl_pu["teams_represented"] = bowl_pu["player_id"].map(lambda x: bowl_teams_str.get(x, "Unknown"))

    stat_cols = [
        "pace_or_spin", "total_overs", "pressure_overs", "pressure_runs_conceded",
        "pressure_wickets", "pressure_economy", "pressure_expected_economy",
        "pressure_econ_saved", "pressure_dot_pct", "pressure_boundary_pct",
        "normal_legal_balls", "normal_economy", "normal_vaoe_per_24b",
        "shrunk_pressure_rsae", "shrunk_pressure_wva", "yorker_pct",
        "bouncer_pct", "slower_pct", "mean_bowl_speed", "max_bowl_speed"
    ]
    for sc in stat_cols:
        if sc in bowl_stats.columns:
            bowl_pu[sc] = bowl_stats.set_index("bowler_id").loc[bowl_pu["player_id"], sc].values

    return bowl_pu


def extract_official_top10_tables(bat_pu, bowl_pu):
    """Format and generate the official Top 10 Batters and Top 10 Bowlers dataframes."""
    print("--- [5/6] Extracting Official Top 10 Submission Tables ---")
    
    # 1. Top 10 Batters
    top_bat_df = bat_pu[bat_pu["is_eligible_final"] == True].sort_values("rank_crr").head(10).copy()
    top_bat_df["rank"] = np.arange(1, 11)

    # Format pace vs spin and top scoring strokes
    pace_vs_spin = []
    top_strokes_str = []
    for _, r in top_bat_df.iterrows():
        p_pace = r.get("pressure_vaoe_vs_pace", 0.0)
        p_spin = r.get("pressure_vaoe_vs_spin", 0.0)
        pace_vs_spin.append(f"{p_pace:+.1f} vs Pace / {p_spin:+.1f} vs Spin")
        stroke = r.get("top_stroke", "Drive")
        off_p = r.get("off_side_pct", 50.0)
        leg_p = r.get("leg_side_pct", 50.0)
        top_strokes_str.append(f"{stroke} (Off: {off_p:.0f}%, Leg: {leg_p:.0f}%)")

    top_bat_df["pace_vs_spin_vaoe"] = pace_vs_spin
    top_bat_df["top_scoring_strokes"] = top_strokes_str

    final_bat_cols = [
        "rank", "player_id", "player_name", "teams_represented", "primary_comp_tier", "primary_role",
        "n_pressure_matches", "pressure_balls", "effective_sample_size", "credibility_factor",
        "pressure_runs", "pressure_strike_rate", "pressure_expected_strike_rate", "pressure_sr_residual",
        "pressure_batting_avg", "pressure_boundary_pct", "pressure_dot_pct", "normal_balls_faced",
        "normal_strike_rate", "normal_vaoe_per_100b", "raw_pressure_vaoe", "shrunk_pressure_vaoe",
        "shrunk_pressure_rae", "shrunk_pressure_wpv", "lcb_80", "shrunk_ext_vaoe_per_100b",
        "shrunk_pressure_delta", "clutch_success_rate", "sortino_downside_deviation",
        "prob_outperform_baseline", "bootstrap_ci_95_low", "bootstrap_ci_95_high",
        "bootstrap_top10_prob", "crr_z_composite", "final_crr_score_100",
        "pace_vs_spin_vaoe", "top_scoring_strokes"
    ]
    top_10_batters = top_bat_df[final_bat_cols].rename(columns={
        "pressure_strike_rate": "pressure_sr",
        "pressure_expected_strike_rate": "expected_pressure_sr",
        "pressure_batting_avg": "pressure_avg",
        "normal_balls_faced": "normal_balls",
        "normal_strike_rate": "normal_sr",
        "shrunk_pressure_rae": "shrunk_rae",
        "shrunk_pressure_wpv": "shrunk_wpv",
        "lcb_80": "lcb_80_floor",
        "shrunk_ext_vaoe_per_100b": "extreme_crucible_vaoe"
    })

    # 2. Top 10 Bowlers
    top_bowl_df = bowl_pu[bowl_pu["is_eligible_final"] == True].sort_values("rank_crr").head(10).copy()
    top_bowl_df["rank"] = np.arange(1, 11)

    final_bowl_cols = [
        "rank", "player_id", "player_name", "teams_represented", "primary_comp_tier", "pace_or_spin", "primary_role",
        "n_pressure_matches", "pressure_balls", "pressure_overs", "effective_sample_size", "credibility_factor",
        "pressure_wickets", "pressure_economy", "pressure_expected_economy", "pressure_econ_saved",
        "pressure_dot_pct", "pressure_boundary_pct", "death_pressure_balls_pct", "normal_legal_balls",
        "normal_economy", "normal_vaoe_per_24b", "raw_pressure_vaoe", "shrunk_pressure_vaoe",
        "shrunk_pressure_rsae", "shrunk_pressure_wva", "lcb_80", "shrunk_ext_vaoe_per_24b",
        "shrunk_pressure_delta", "clutch_success_rate", "sortino_downside_deviation",
        "prob_outperform_baseline", "bootstrap_ci_95_low", "bootstrap_ci_95_high",
        "bootstrap_top10_prob", "crr_z_composite", "final_crr_score_100",
        "yorker_pct", "slower_pct", "bouncer_pct", "mean_bowl_speed"
    ]
    top_10_bowlers = top_bowl_df[final_bowl_cols].rename(columns={
        "pace_or_spin": "bowling_style",
        "pressure_balls": "pressure_legal_balls",
        "pressure_expected_economy": "expected_pressure_economy",
        "pressure_boundary_pct": "pressure_boundary_conceded_pct",
        "shrunk_pressure_rsae": "shrunk_rsae",
        "shrunk_pressure_wva": "shrunk_wva",
        "lcb_80": "lcb_80_floor",
        "shrunk_ext_vaoe_per_24b": "extreme_crucible_vaoe",
        "clutch_success_rate": "clutch_spell_success_rate",
        "slower_pct": "slower_ball_pct"
    })

    return top_10_batters, top_10_bowlers


def export_and_sync_all(top_10_batters, top_10_bowlers, complete_batters, complete_bowlers, base_dir="."):
    """Save all Phase 6 outputs to Data/processed/ and repository root."""
    print("--- [6/6] Exporting and Syncing Official Deliverables ---")
    proc_dir = os.path.join(base_dir, "Data", "processed")
    os.makedirs(proc_dir, exist_ok=True)

    files_to_sync = [
        ("top_10_batters.csv", top_10_batters),
        ("top_10_bowlers.csv", top_10_bowlers),
        ("complete_batter_rankings.csv", complete_batters),
        ("complete_bowler_rankings.csv", complete_bowlers),
    ]

    for fname, df in files_to_sync:
        p1 = os.path.join(proc_dir, fname)
        p2 = os.path.join(base_dir, fname)
        df.to_csv(p1, index=False)
        df.to_csv(p2, index=False)
        sz_mb = os.path.getsize(p1) / (1024 * 1024)
        print(f"  Saved {fname}: {len(df):,} rows x {len(df.columns)} cols ({sz_mb:.3f} MB)")


def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    print(f"Starting Phase 6 Ranking Engine in {base_dir}")

    # 1. Load data
    deliv, bat_stats, bowl_stats, pu, teams_map = load_datasets(base_dir)

    # 2. Auxiliary mappings
    bat_teams_str, bowl_teams_str = compute_teams_represented(deliv, teams_map)
    bat_ext_agg, bowl_ext_agg, death_pct_map = compute_extreme_crucible_vaoe(deliv)

    # 3. Build leaderboards
    complete_batters = build_batter_rankings(bat_stats, pu, bat_ext_agg, bat_teams_str)
    complete_bowlers = build_bowler_rankings(bowl_stats, pu, bowl_ext_agg, death_pct_map, bowl_teams_str)

    # 4. Extract Top 10
    top_10_batters, top_10_bowlers = extract_official_top10_tables(complete_batters, complete_bowlers)

    # 5. Export and sync
    export_and_sync_all(top_10_batters, top_10_bowlers, complete_batters, complete_bowlers, base_dir)

    print("\n=== TOP 10 BATTERS UNDER PRESSURE (CRUTCH RELIABILITY RATING) ===")
    print(top_10_batters[["rank", "player_name", "primary_role", "pressure_balls", "shrunk_pressure_vaoe", "lcb_80_floor", "final_crr_score_100"]].to_string(index=False))

    print("\n=== TOP 10 BOWLERS UNDER PRESSURE (CRUTCH RELIABILITY RATING) ===")
    print(top_10_bowlers[["rank", "player_name", "bowling_style", "primary_role", "pressure_legal_balls", "death_pressure_balls_pct", "shrunk_pressure_vaoe", "lcb_80_floor", "final_crr_score_100"]].to_string(index=False))

    print("\n=== PHASE 6 PLAYER RANKING ENGINE COMPLETED SUCCESSFULLY ===")


if __name__ == "__main__":
    main()

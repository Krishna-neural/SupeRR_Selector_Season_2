"""
SupeRR Selector Season 2 — Phase 7 Automated Unit Test Suite
Verification of Robustness Invariants, Sensitivity Thresholds, Weight Perturbations,
Temporal Non-Leakage, and Adversarial Edge-Case Immunity.
"""

import os
import pytest
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, pearsonr


@pytest.fixture(scope="module")
def base_dir():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="module")
def stability_data(base_dir):
    path = os.path.join(base_dir, "ranking_stability.csv")
    assert os.path.exists(path), f"ranking_stability.csv not found at {path}"
    df = pd.read_csv(path)
    return df


def test_deliverables_exist_and_populated(base_dir, stability_data):
    """Verify all Phase 7 files exist in processed/audit and root with zero NaNs."""
    required_files = [
        os.path.join(base_dir, "ranking_stability.csv"),
        os.path.join(base_dir, "Data", "processed", "ranking_stability.csv"),
        os.path.join(base_dir, "sensitivity_analysis.md"),
        os.path.join(base_dir, "Data", "audit", "sensitivity_analysis.md"),
        os.path.join(base_dir, "final_model_validation.md"),
        os.path.join(base_dir, "Data", "audit", "final_model_validation.md"),
        os.path.join(base_dir, "src", "robustness_experiments.py"),
    ]
    for fp in required_files:
        assert os.path.exists(fp), f"Required Phase 7 file missing: {fp}"
        assert os.path.getsize(fp) > 0, f"File is empty: {fp}"

    # Verify columns and zero NaNs
    req_cols = [
        "player_id", "player_name", "role_category", "production_rank", "final_crr_score_100",
        "rank_model_a", "rank_model_b", "rank_continuous_pressure",
        "rank_p65", "rank_p75", "rank_p80",
        "rank_formulation_1", "rank_formulation_2",
        "weight_mc_mean_rank", "weight_mc_rank_std", "weight_mc_top10_pct",
        "ipl_only_vaoe", "t20i_only_vaoe", "seasons_active_count", "max_single_season_ball_share",
        "expanding_window_vaoe_diff", "crr_boot_mean", "crr_boot_ci_95_low", "crr_boot_ci_95_high",
        "crr_boot_median_rank", "crr_boot_rank_iqr", "crr_top10_freq_pct", "crr_top15_freq_pct",
        "stability_tier"
    ]
    for c in req_cols:
        assert c in stability_data.columns, f"Missing required column: {c}"
        assert stability_data[c].isnull().sum() == 0, f"Found NaNs in column: {c}"

    assert len(stability_data) == 290, f"Expected 290 eligible players (145 bat + 145 bowl), got {len(stability_data)}"


def test_weight_perturbation_stability_invariant(stability_data):
    """
    Verify that across weight perturbations, the Spearman rank correlation with production
    CRR ranking is rho >= 0.94 for both disciplines, and at least 8 of Top 10 have retention >= 75%.
    """
    bat = stability_data[stability_data["role_category"] == "Batter"].copy()
    bowl = stability_data[stability_data["role_category"] == "Bowler"].copy()

    # Formulations 1 and 2 correlation proxies
    rho_f1_bat, _ = spearmanr(bat["production_rank"], bat["rank_formulation_1"])
    rho_f2_bat, _ = spearmanr(bat["production_rank"], bat["rank_formulation_2"])
    rho_f1_bowl, _ = spearmanr(bowl["production_rank"], bowl["rank_formulation_1"])
    rho_f2_bowl, _ = spearmanr(bowl["production_rank"], bowl["rank_formulation_2"])

    assert rho_f1_bat >= 0.94, f"Batting Formulation 1 rho too low: {rho_f1_bat:.4f}"
    assert rho_f2_bat >= 0.94, f"Batting Formulation 2 rho too low: {rho_f2_bat:.4f}"
    assert rho_f1_bowl >= 0.94, f"Bowling Formulation 1 rho too low: {rho_f1_bowl:.4f}"
    assert rho_f2_bowl >= 0.94, f"Bowling Formulation 2 rho too low: {rho_f2_bowl:.4f}"

    # Top-10 Weight MC retention >= 75% for at least 8/10
    top10_bat = bat[bat["production_rank"] <= 10]
    top10_bowl = bowl[bowl["production_rank"] <= 10]

    retained_bat = (top10_bat["weight_mc_top10_pct"] >= 75.0).sum()
    retained_bowl = (top10_bowl["weight_mc_top10_pct"] >= 75.0).sum()

    assert retained_bat >= 8, f"Only {retained_bat}/10 batters have weight MC retention >= 75%"
    assert retained_bowl >= 8, f"Only {retained_bowl}/10 bowlers have weight MC retention >= 75%"


def test_pressure_threshold_stability_invariant(stability_data):
    """
    Verify Spearman rank correlation between P70 and adjacent thresholds (P65, P75)
    is rho >= 0.90 for both batters and bowlers.
    """
    bat = stability_data[stability_data["role_category"] == "Batter"]
    bowl = stability_data[stability_data["role_category"] == "Bowler"]

    rho_p65_bat, _ = spearmanr(bat["production_rank"], bat["rank_p65"])
    rho_p75_bat, _ = spearmanr(bat["production_rank"], bat["rank_p75"])
    rho_p65_bowl, _ = spearmanr(bowl["production_rank"], bowl["rank_p65"])
    rho_p75_bowl, _ = spearmanr(bowl["production_rank"], bowl["rank_p75"])

    assert rho_p65_bat >= 0.90, f"Batting P65 rho too low: {rho_p65_bat:.4f}"
    assert rho_p75_bat >= 0.90, f"Batting P75 rho too low: {rho_p75_bat:.4f}"
    assert rho_p65_bowl >= 0.90, f"Bowling P65 rho too low: {rho_p65_bowl:.4f}"
    assert rho_p75_bowl >= 0.90, f"Bowling P75 rho too low: {rho_p75_bowl:.4f}"


def test_temporal_non_leakage_invariant(base_dir):
    """
    Verify that out-of-sample expanding-window delivery VAOE residuals correlate
    with production hierarchical VAOE residuals at r >= 0.97.
    """
    deliv_path = os.path.join(base_dir, "Data", "processed", "clean_deliveries.csv")
    match_path = os.path.join(base_dir, "Data", "processed", "match_context.csv")
    deliv = pd.read_csv(deliv_path, low_memory=False)
    mc = pd.read_csv(match_path, low_memory=False)

    deliv["match_id"] = deliv["match_id"].astype(str)
    mc["match_id"] = mc["match_id"].astype(str)
    mc["year"] = pd.to_datetime(mc["parsed_date"]).dt.year
    year_map = mc.set_index("match_id")["year"].to_dict()
    deliv["year"] = deliv["match_id"].map(year_map)

    deliv["wkt_bucket"] = pd.cut(
        deliv["pre_wickets_lost"], [-1, 1, 3, 5, 10], labels=["0-1", "2-3", "4-5", "6+"]
    ).astype(str)
    deliv["inn_group"] = deliv["innings"].apply(lambda x: "SuperOver" if x in [3, 4] else str(int(x)))

    bat_mask = deliv["is_batter_ball_faced"] == True
    bat_df = deliv[bat_mask].copy()

    # Dynamic lambda
    rem_b = bat_df["pre_balls_remaining"].values
    w_lost = bat_df["pre_wickets_lost"].values
    so_mask = bat_df["innings"].isin([3, 4]).values
    base_cost = np.where(so_mask, 6.0, 4.0 + 16.0 * (rem_b / 120.0))
    wkt_mult = 1.0 + 0.5 * (w_lost / 9.0)
    lambda_wkt = np.clip(base_cost * wkt_mult, 4.0, 24.0)

    train_df = bat_df[bat_df["year"] <= 2024]
    test_df = bat_df[bat_df["year"] >= 2025].copy()
    test_lambda = lambda_wkt[bat_df["year"] >= 2025]

    grp_cols = ["inn_group", "overid", "pace_or_spin", "wkt_bucket"]
    cell_runs = train_df.groupby(grp_cols)["runs"].mean()
    cell_wkt = train_df.groupby(grp_cols)["is_batter_dismissal"].mean()

    test_idx = list(zip(test_df["inn_group"], test_df["overid"], test_df["pace_or_spin"], test_df["wkt_bucket"]))
    test_raw_runs = pd.Series(test_idx).map(cell_runs).fillna(train_df["runs"].mean()).values * test_df["venue_run_rate_multiplier"].values
    test_raw_wkt = pd.Series(test_idx).map(cell_wkt).fillna(train_df["is_batter_dismissal"].mean()).values

    test_rae_out = test_df["runs"].values - test_raw_runs
    test_wpv_out = (test_raw_wkt - test_df["is_batter_dismissal"].values) * test_lambda
    test_vaoe_out = test_rae_out + test_wpv_out

    r_temporal, _ = pearsonr(test_vaoe_out, test_df["bat_vaoe"].values)
    assert r_temporal >= 0.97, f"Expanding-window out-of-sample correlation too low: {r_temporal:.4f}"


def test_edge_case_adversarial_immunity(base_dir):
    """Verify that degenerate adversarial inputs produce finite values and zero exceptions."""
    deliv_path = os.path.join(base_dir, "Data", "processed", "clean_deliveries.csv")
    match_path = os.path.join(base_dir, "Data", "processed", "match_context.csv")
    deliv = pd.read_csv(deliv_path, low_memory=False)
    mc = pd.read_csv(match_path, low_memory=False)

    from src.robustness_experiments import run_exp8_edge_cases
    edge_df = run_exp8_edge_cases(deliv, mc)

    assert len(edge_df) == 6, f"Expected 6 edge case tests, got {len(edge_df)}"
    assert (edge_df["Status"] == "PASSED").all(), "Not all edge cases passed."


def test_stability_tier_taxonomy_consistency(stability_data):
    """Verify that every eligible player has a valid stability tier and classification rules hold."""
    valid_tiers = {
        "Tier 1: Ironclad Lock",
        "Tier 2: High-Confidence Core",
        "Tier 3: High-Upside Contender"
    }
    actual_tiers = set(stability_data["stability_tier"])
    assert actual_tiers.issubset(valid_tiers), f"Invalid stability tiers found: {actual_tiers - valid_tiers}"

    # Verify that multi-season anchors with high retention in Top 10 are Tier 1
    tier1_players = stability_data[stability_data["stability_tier"] == "Tier 1: Ironclad Lock"]
    assert len(tier1_players) > 0, "No Tier 1 players identified"
    for _, r in tier1_players.iterrows():
        assert r["seasons_active_count"] >= 3, f"Player {r['player_name']} in Tier 1 but has < 3 seasons"

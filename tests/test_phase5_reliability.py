"""
Unit and regression tests for Phase 5: Statistical Reliability, Empirical Bayes Shrinkage,
and Uncertainty Estimation for the Rajasthan Royals — SupeRR Selector Season 2 challenge.
"""

import os
import pytest
import numpy as np
import pandas as pd

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "Data", "processed")


@pytest.fixture(scope="module")
def load_phase5_data():
    """Load player_uncertainty, batting_player_statistics, and bowling_player_statistics."""
    uncert_path = os.path.join(DATA_DIR, "player_uncertainty.csv")
    bat_path = os.path.join(DATA_DIR, "batting_player_statistics.csv")
    bowl_path = os.path.join(DATA_DIR, "bowling_player_statistics.csv")

    assert os.path.exists(uncert_path), f"Missing {uncert_path}"
    assert os.path.exists(bat_path), f"Missing {bat_path}"
    assert os.path.exists(bowl_path), f"Missing {bowl_path}"

    df_uncert = pd.read_csv(uncert_path)
    df_bat = pd.read_csv(bat_path)
    df_bowl = pd.read_csv(bowl_path)

    return df_uncert, df_bat, df_bowl


def test_phase5_file_existence_and_row_counts(load_phase5_data):
    """Verify that all Phase 5 files exist in Data/processed and root, with exact row counts."""
    df_uncert, df_bat, df_bowl = load_phase5_data

    # Check root sync
    assert os.path.exists(os.path.join(BASE_DIR, "player_uncertainty.csv")), "Root player_uncertainty.csv missing"
    assert os.path.exists(os.path.join(BASE_DIR, "batting_player_statistics.csv")), "Root batting_player_statistics.csv missing"
    assert os.path.exists(os.path.join(BASE_DIR, "bowling_player_statistics.csv")), "Root bowling_player_statistics.csv missing"

    # Row counts
    assert len(df_bat) == 888, f"Expected 888 batters, got {len(df_bat)}"
    assert len(df_bowl) == 647, f"Expected 647 bowlers, got {len(df_bowl)}"
    assert len(df_uncert) == 1535, f"Expected 1,535 rows in player_uncertainty, got {len(df_uncert)}"

    # Role breakdown in player_uncertainty
    role_counts = df_uncert["role_category"].value_counts()
    assert role_counts.get("Batter", 0) == 888, "Expected 888 Batters in player_uncertainty"
    assert role_counts.get("Bowler", 0) == 647, "Expected 647 Bowlers in player_uncertainty"


def test_zero_nulls_on_eligible_players(load_phase5_data):
    """Verify zero NaN values on all eligible players across all uncertainty metrics."""
    df_uncert, _, _ = load_phase5_data
    elig = df_uncert[df_uncert["is_eligible_production"] == True].copy()

    assert len(elig) >= 350, f"Expected at least 350 eligible players, got {len(elig)}"

    required_cols = [
        "player_id", "player_name", "role_category", "primary_role", "primary_comp_tier",
        "n_pressure_matches", "pressure_balls", "elite_tier_pressure_balls", "effective_sample_size",
        "credibility_factor", "raw_pressure_vaoe", "shrunk_pressure_vaoe", "raw_pressure_delta",
        "shrunk_pressure_delta", "posterior_se", "ci_95_low", "ci_95_high", "lcb_80",
        "prob_outperform_baseline", "prob_positive_delta", "bootstrap_mean", "bootstrap_se",
        "bootstrap_ci_95_low", "bootstrap_ci_95_high", "bootstrap_prob_positive",
        "bootstrap_median_rank", "bootstrap_rank_iqr", "bootstrap_top10_prob",
        "sortino_downside_deviation", "clutch_success_rate", "is_eligible_production"
    ]

    for col in required_cols:
        assert col in elig.columns, f"Missing required column {col}"
        null_count = elig[col].isna().sum()
        assert null_count == 0, f"Found {null_count} NaNs in column '{col}' for eligible players"


def test_shrinkage_monotonicity_invariant(load_phase5_data):
    """
    Verify that:
    1. 0 <= B_i < 1 for all players.
    2. B_i strictly increases monotonically with effective_sample_size.
    3. Extreme small-sample outliers (N < 20) are pulled toward their role prior mean.
    """
    df_uncert, df_bat, df_bowl = load_phase5_data

    # B_i bounds
    b_factors = df_uncert["credibility_factor"].values
    assert (b_factors >= 0.0).all() and (b_factors < 1.0).all(), "Credibility factor B_i out of [0, 1) bounds"

    # Monotonicity with N_eff
    for role in ["Batter", "Bowler"]:
        sub = df_uncert[(df_uncert["role_category"] == role) & (df_uncert["effective_sample_size"] > 0)].copy()
        sub = sub.sort_values("effective_sample_size")
        b_vals = sub["credibility_factor"].values
        # Check non-decreasing
        diffs = np.diff(b_vals)
        assert (diffs >= -1e-6).all(), f"Credibility factor is not monotonic for {role}"

    # Extreme small-sample shrinkage
    small_sample_bat = df_bat[(df_bat["pressure_balls"] > 0) & (df_bat["pressure_balls"] < 20)].copy()
    assert len(small_sample_bat) > 0, "No small sample batters found"
    
    # Distance to prior must decrease after shrinkage: |shrunk - prior| < |raw - prior|
    for _, row in small_sample_bat.iterrows():
        raw_dist = abs(row["raw_pressure_vaoe"] - row["prior_vaoe"])
        shrunk_dist = abs(row["shrunk_pressure_vaoe"] - row["prior_vaoe"])
        assert shrunk_dist <= raw_dist + 0.01, f"Player {row['batter_name']} not shrunk toward prior"


def test_small_sample_outlier_defense(load_phase5_data):
    """
    Defense Invariant: No player with < 30 pressure balls may rank in the Top 20
    of shrunk_pressure_vaoe across the entire corpus.
    """
    df_uncert, _, _ = load_phase5_data

    for role in ["Batter", "Bowler"]:
        sub = df_uncert[df_uncert["role_category"] == role].sort_values("shrunk_pressure_vaoe", ascending=False)
        top20 = sub.head(20)
        min_balls = top20["pressure_balls"].min()
        assert min_balls >= 30, f"Top 20 {role} contains player with only {min_balls} pressure balls (< 30)"


def test_credible_and_bootstrap_interval_integrity(load_phase5_data):
    """
    Verify interval integrity:
    1. ci_95_low <= shrunk_pressure_vaoe <= ci_95_high
    2. bootstrap_ci_95_low <= bootstrap_mean <= bootstrap_ci_95_high
    3. lcb_80 <= shrunk_pressure_vaoe
    """
    df_uncert, _, _ = load_phase5_data
    elig = df_uncert[df_uncert["is_eligible_production"] == True].copy()

    # Analytical CIs
    assert (elig["ci_95_low"] <= elig["shrunk_pressure_vaoe"] + 0.01).all(), "ci_95_low > shrunk_pressure_vaoe"
    assert (elig["shrunk_pressure_vaoe"] <= elig["ci_95_high"] + 0.01).all(), "shrunk_pressure_vaoe > ci_95_high"

    # LCB80
    assert (elig["lcb_80"] <= elig["shrunk_pressure_vaoe"] + 0.01).all(), "lcb_80 > shrunk_pressure_vaoe"

    # Bootstrap CIs
    assert (elig["bootstrap_ci_95_low"] <= elig["bootstrap_mean"] + 0.01).all(), "bootstrap_ci_95_low > bootstrap_mean"
    assert (elig["bootstrap_mean"] <= elig["bootstrap_ci_95_high"] + 0.01).all(), "bootstrap_mean > bootstrap_ci_95_high"


def test_probability_bounds_and_sortino(load_phase5_data):
    """Verify that all probability metrics are strictly within [0, 1] and Sortino >= 0."""
    df_uncert, _, _ = load_phase5_data

    prob_cols = [
        "prob_outperform_baseline", "prob_positive_delta",
        "bootstrap_prob_positive"
    ]
    for col in prob_cols:
        vals = df_uncert[col].values
        assert (vals >= 0.0).all() and (vals <= 1.0).all(), f"Column {col} has values outside [0, 1]"

    # Eligible top10 prob
    elig = df_uncert[df_uncert["is_eligible_production"] == True]
    top10_p = elig["bootstrap_top10_prob"].values
    assert (top10_p >= 0.0).all() and (top10_p <= 1.0).all(), "bootstrap_top10_prob outside [0, 1]"

    # Sortino non-negativity
    assert (df_uncert["sortino_downside_deviation"].values >= 0.0).all(), "Sortino downside deviation is negative"


def test_additive_component_shrinkage_batting_and_bowling(load_phase5_data):
    """
    Verify exact component additivity:
    Batting: shrunk_pressure_rae + shrunk_pressure_wpv == shrunk_pressure_vaoe
    Bowling: shrunk_pressure_rsae + shrunk_pressure_wva == shrunk_pressure_vaoe
    """
    _, df_bat, df_bowl = load_phase5_data

    # Batting
    bat_sum = df_bat["shrunk_pressure_rae"] + df_bat["shrunk_pressure_wpv"]
    bat_diff = (bat_sum - df_bat["shrunk_pressure_vaoe"]).abs()
    assert (bat_diff <= 0.05).all(), f"Batting component sum failed: max discrepancy = {bat_diff.max():.4f}"

    # Bowling
    bowl_sum = df_bowl["shrunk_pressure_rsae"] + df_bowl["shrunk_pressure_wva"]
    bowl_diff = (bowl_sum - df_bowl["shrunk_pressure_vaoe"]).abs()
    assert (bowl_diff <= 0.05).all(), f"Bowling component sum failed: max discrepancy = {bowl_diff.max():.4f}"

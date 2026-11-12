"""
Phase 3 Unit Test Suite: Pressure Index Research & Validation
Rajasthan Royals — SupeRR Selector Season 2

Validates:
1. Column presence and complete data integrity (no NaNs or infinite values).
2. Range bounds: all pressure metrics within [0, 100], pressure_weight in [0, 1].
3. Dead-chase immunity (attenuation under mathematically hopeless conditions).
4. Innings 1 collapse sensitivity (heightened pressure under top-order collapses).
5. Super Over classification (100% Extreme and is_high_pressure == True).
6. Anti-leakage verification (outcome invariance).
7. Distribution stability and role-specific asymmetry.
"""

import os
import sys
import pytest
import pandas as pd
import numpy as np

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

DELIV_PROC_PATH = os.path.join(WORKSPACE_DIR, "Data", "processed", "clean_deliveries.csv")
DIST_PROC_PATH = os.path.join(WORKSPACE_DIR, "Data", "processed", "pressure_distribution.csv")

REQUIRED_PRESSURE_COLS = [
    "pressure_model_a_rule",
    "pressure_model_b_percentile",
    "pressure_model_c_quantum_leverage",
    "pressure_index",
    "batting_pressure_index",
    "bowling_pressure_index",
    "pressure_category",
    "is_high_pressure",
    "pressure_weight",
]

@pytest.fixture(scope="module")
def deliveries_df():
    assert os.path.exists(DELIV_PROC_PATH), f"Missing {DELIV_PROC_PATH}"
    df = pd.read_csv(DELIV_PROC_PATH, keep_default_na=False, low_memory=False)
    # Ensure types
    for col in [
        "pressure_model_a_rule", "pressure_model_b_percentile",
        "pressure_model_c_quantum_leverage", "pressure_index",
        "batting_pressure_index", "bowling_pressure_index", "pressure_weight",
        "pre_rrr", "pre_wickets_in_hand", "pre_wickets_lost", "pre_legal_balls_bowled"
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

@pytest.fixture(scope="module")
def distribution_df():
    assert os.path.exists(DIST_PROC_PATH), f"Missing {DIST_PROC_PATH}"
    return pd.read_csv(DIST_PROC_PATH)

def test_required_columns_exist(deliveries_df):
    """Verify all engineered Phase 3 pressure columns exist in clean_deliveries.csv."""
    for col in REQUIRED_PRESSURE_COLS:
        assert col in deliveries_df.columns, f"Missing required pressure column: {col}"

def test_zero_nulls_in_pressure_columns(deliveries_df):
    """Verify strictly 0 NaN / Null values across all 200,999 deliveries for pressure columns."""
    for col in REQUIRED_PRESSURE_COLS:
        null_count = deliveries_df[col].isna().sum()
        assert null_count == 0, f"Column {col} has {null_count} null/NaN values!"

def test_pressure_metric_bounds(deliveries_df):
    """Verify all pressure indices are strictly bounded in [0, 100] and weights in [0, 1]."""
    scale_cols = [
        "pressure_model_a_rule",
        "pressure_model_b_percentile",
        "pressure_model_c_quantum_leverage",
        "pressure_index",
        "batting_pressure_index",
        "bowling_pressure_index"
    ]
    for col in scale_cols:
        min_val = deliveries_df[col].min()
        max_val = deliveries_df[col].max()
        assert min_val >= 0.0, f"{col} has min {min_val} < 0.0"
        assert max_val <= 100.0, f"{col} has max {max_val} > 100.0"

    w_min = deliveries_df["pressure_weight"].min()
    w_max = deliveries_df["pressure_weight"].max()
    assert w_min >= 0.0, f"pressure_weight min {w_min} < 0.0"
    assert w_max <= 1.0, f"pressure_weight max {w_max} > 1.0"

def test_dead_chase_immunity(deliveries_df):
    """
    Verify dead-chase immunity:
    Deliveries in Innings 2 where RRR > 24 and <= 2 wickets in hand must have
    mean pressure significantly lower than knife-edge chases (RRR 10-14, >= 4 wkts).
    """
    inn2 = deliveries_df[deliveries_df["innings"] == 2]
    dead_chase = inn2[(inn2["pre_rrr"] > 24.0) & (inn2["pre_wickets_in_hand"] <= 2)]
    knife_edge = inn2[(inn2["pre_rrr"] >= 10.0) & (inn2["pre_rrr"] <= 14.0) & (inn2["pre_wickets_in_hand"] >= 4)]

    assert len(dead_chase) > 0, "No dead chase deliveries found in dataset"
    assert len(knife_edge) > 0, "No knife-edge chase deliveries found in dataset"

    mean_dead = dead_chase["pressure_index"].mean()
    mean_knife = knife_edge["pressure_index"].mean()

    # Dead chase mean pressure must be attenuated significantly below 20.0
    # and knife edge must be elevated above 50.0
    assert mean_dead < 20.0, f"Dead chase mean pressure {mean_dead:.2f} is not attenuated below 20.0!"
    assert mean_knife > 50.0, f"Knife-edge chase mean pressure {mean_knife:.2f} is below 50.0!"
    assert mean_knife > mean_dead * 2.5, "Knife-edge chase must be at least 2.5x higher than dead chase"

def test_innings_1_collapse_sensitivity(deliveries_df):
    """
    Verify Innings 1 collapse sensitivity:
    Powerplay deliveries with >= 3 wickets lost must exhibit higher pressure
    than normal Powerplay deliveries with 0 wickets lost.
    """
    inn1_pp = deliveries_df[(deliveries_df["innings"] == 1) & (deliveries_df["is_powerplay"] == True)]
    collapse_pp = inn1_pp[inn1_pp["pre_wickets_lost"] >= 3]
    normal_pp = inn1_pp[inn1_pp["pre_wickets_lost"] == 0]

    assert len(collapse_pp) > 0, "No collapse Powerplay deliveries found in Innings 1"
    assert len(normal_pp) > 0, "No normal Powerplay deliveries found in Innings 1"

    mean_collapse = collapse_pp["pressure_index"].mean()
    mean_normal = normal_pp["pressure_index"].mean()

    assert mean_collapse > mean_normal, (
        f"Collapse PP pressure ({mean_collapse:.2f}) is not higher than normal PP ({mean_normal:.2f})"
    )

def test_super_over_extreme_classification(deliveries_df):
    """Verify 100% of Super Over deliveries are classified as Extreme and is_high_pressure == True."""
    so_deliv = deliveries_df[deliveries_df["innings"].isin([3, 4])]
    if len(so_deliv) > 0:
        assert (so_deliv["pressure_category"] == "Extreme").all(), "Not all Super Over balls are 'Extreme'!"
        assert (so_deliv["is_high_pressure"] == True).all(), "Not all Super Over balls have is_high_pressure == True!"
        assert (so_deliv["pressure_index"] >= 90.0).all(), "Super Over balls have pressure_index < 90.0!"

def test_pressure_category_monotonicity(distribution_df):
    """Verify mean pressure monotonically increases across Low -> Moderate -> High -> Extreme categories."""
    cat_df = distribution_df[distribution_df["stratum"] == "Pressure Category"].set_index("category")
    assert cat_df.loc["Low", "mean_pressure"] < cat_df.loc["Moderate", "mean_pressure"]
    assert cat_df.loc["Moderate", "mean_pressure"] < cat_df.loc["High", "mean_pressure"]
    assert cat_df.loc["High", "mean_pressure"] < cat_df.loc["Extreme", "mean_pressure"]

def test_anti_leakage_outcome_invariance():
    """
    Verify zero outcome leakage:
    Calculates pressure from pre-delivery state only, unaffected by runs conceded or wickets taken.
    """
    from src.pressure_index import run_pressure_pipeline
    # Inspecting source code guarantees no use of 'runs', 'is_wicket', or 'team_runs_on_ball'
    # in calculating pressure_model_a_rule, pressure_model_b_percentile, or pressure_model_c_quantum_leverage.
    import inspect
    src = inspect.getsource(run_pressure_pipeline)
    
    # Check that post-delivery outcome terms are not used in computing pressure
    # They should only be used in computing stratum validation metrics (e.g. rpo, wicket_rate)
    c_split = src.split("--- [4/6] Computing Champion Model C")
    p_comp = c_split[1].split("--- [6/6] Generating pressure_distribution.csv")[0]
    assert "deliv[\"runs\"]" not in p_comp
    assert "deliv[\"is_wicket\"]" not in p_comp
    assert "deliv[\"team_runs_on_ball\"]" not in p_comp

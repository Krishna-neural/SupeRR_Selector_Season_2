"""
Unit and regression tests for Phase 6: Player Ranking Engine and Top-10 Submission Lists
for the Rajasthan Royals — SupeRR Selector Season 2 challenge.
"""

import os
import pytest
import numpy as np
import pandas as pd

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "Data", "processed")


@pytest.fixture(scope="module")
def load_phase6_data():
    """Load Top 10 and Complete Rankings datasets from Data/processed/."""
    tb_path = os.path.join(DATA_DIR, "top_10_batters.csv")
    tbw_path = os.path.join(DATA_DIR, "top_10_bowlers.csv")
    cb_path = os.path.join(DATA_DIR, "complete_batter_rankings.csv")
    cbw_path = os.path.join(DATA_DIR, "complete_bowler_rankings.csv")

    assert os.path.exists(tb_path), f"Missing {tb_path}"
    assert os.path.exists(tbw_path), f"Missing {tbw_path}"
    assert os.path.exists(cb_path), f"Missing {cb_path}"
    assert os.path.exists(cbw_path), f"Missing {cbw_path}"

    df_tb = pd.read_csv(tb_path)
    df_tbw = pd.read_csv(tbw_path)
    df_cb = pd.read_csv(cb_path)
    df_cbw = pd.read_csv(cbw_path)

    return df_tb, df_tbw, df_cb, df_cbw


def test_phase6_file_existence_and_row_counts(load_phase6_data):
    """Verify that all Phase 6 files exist in Data/processed/ and root, with exact row counts."""
    df_tb, df_tbw, df_cb, df_cbw = load_phase6_data

    # Check root file sync
    assert os.path.exists(os.path.join(BASE_DIR, "top_10_batters.csv")), "Root top_10_batters.csv missing"
    assert os.path.exists(os.path.join(BASE_DIR, "top_10_bowlers.csv")), "Root top_10_bowlers.csv missing"
    assert os.path.exists(os.path.join(BASE_DIR, "complete_batter_rankings.csv")), "Root complete_batter_rankings.csv missing"
    assert os.path.exists(os.path.join(BASE_DIR, "complete_bowler_rankings.csv")), "Root complete_bowler_rankings.csv missing"

    # Exact row counts
    assert len(df_tb) == 10, f"Expected exactly 10 rows in top_10_batters.csv, got {len(df_tb)}"
    assert len(df_tbw) == 10, f"Expected exactly 10 rows in top_10_bowlers.csv, got {len(df_tbw)}"
    assert len(df_cb) == 888, f"Expected 888 batters in complete_batter_rankings, got {len(df_cb)}"
    assert len(df_cbw) == 647, f"Expected 647 bowlers in complete_bowler_rankings, got {len(df_cbw)}"


def test_top10_unique_players_and_sequential_ranks(load_phase6_data):
    """
    Verify:
    1. Zero duplicate player_ids or player_names.
    2. Ranks are strictly sequential integers 1 through 10.
    3. final_crr_score_100 is strictly non-increasing with rank.
    """
    df_tb, df_tbw, _, _ = load_phase6_data

    for name, df in [("Batters", df_tb), ("Bowlers", df_tbw)]:
        # Sequential rank
        assert df["rank"].tolist() == list(range(1, 11)), f"{name} ranks are not sequential 1 to 10"

        # Unique players
        assert df["player_id"].nunique() == 10, f"{name} list has duplicate player_id values"
        assert df["player_name"].nunique() == 10, f"{name} list has duplicate player_name values"

        # Non-increasing CRR score
        scores = df["final_crr_score_100"].values
        diffs = np.diff(scores)
        assert (diffs <= 1e-6).all(), f"{name} final_crr_score_100 is not monotonic descending"


def test_strict_eligibility_compliance(load_phase6_data):
    """
    Verify that every selected player meets refined production eligibility:
    - pressure_balls >= 120
    - n_pressure_matches >= 10
    - primary_comp_tier in Tier 1 / Tier 2
    """
    df_tb, df_tbw, _, _ = load_phase6_data
    valid_tiers = ["Tier 1 (IPL)", "Tier 2 (T20I_FullMember)"]

    # Batters
    assert (df_tb["pressure_balls"] >= 120).all(), "Batter in Top 10 has < 120 pressure balls"
    assert (df_tb["n_pressure_matches"] >= 10).all(), "Batter in Top 10 has < 10 pressure matches"
    assert df_tb["primary_comp_tier"].isin(valid_tiers).all(), "Batter in Top 10 not from Tier 1/2"

    # Bowlers
    assert (df_tbw["pressure_legal_balls"] >= 120).all(), "Bowler in Top 10 has < 120 pressure legal balls"
    assert (df_tbw["n_pressure_matches"] >= 10).all(), "Bowler in Top 10 has < 10 pressure matches"
    assert df_tbw["primary_comp_tier"].isin(valid_tiers).all(), "Bowler in Top 10 not from Tier 1/2"


def test_positive_certainty_floor_and_probability_invariants(load_phase6_data):
    """
    Verify that all 10 selected batters and all 10 selected bowlers have:
    1. shrunk_pressure_vaoe > 0
    2. lcb_80_floor > 0
    3. prob_outperform_baseline >= 0.85
    """
    df_tb, df_tbw, _, _ = load_phase6_data

    for name, df in [("Batters", df_tb), ("Bowlers", df_tbw)]:
        # Positive shrunk VAOE
        assert (df["shrunk_pressure_vaoe"] > 0).all(), f"{name} Top 10 has non-positive shrunk VAOE"

        # Positive LCB80 floor
        assert (df["lcb_80_floor"] > 0).all(), f"{name} Top 10 has non-positive LCB80 floor"

        # High certainty
        assert (df["prob_outperform_baseline"] >= 0.85).all(), f"{name} Top 10 has prob_outperform_baseline < 0.85"


def test_reproducibility_and_monotonic_score_mapping(load_phase6_data):
    """
    Verify that final_crr_score_100 is strictly monotonic with crr_z_composite,
    reproducing the exact ordering to machine precision.
    """
    df_tb, df_tbw, _, _ = load_phase6_data

    for name, df in [("Batters", df_tb), ("Bowlers", df_tbw)]:
        # Rank by composite Z vs rank by 0-100 score
        rank_by_z = df["crr_z_composite"].rank(ascending=False).astype(int).tolist()
        rank_by_score = df["final_crr_score_100"].rank(ascending=False).astype(int).tolist()
        assert rank_by_z == list(range(1, 11)), f"{name} composite Z ordering does not match ranks 1-10"
        assert rank_by_score == list(range(1, 11)), f"{name} 0-100 score ordering does not match ranks 1-10"


def test_complete_rankings_integrity(load_phase6_data):
    """
    Verify that complete rankings datasets contain valid candidate evaluations:
    1. Exactly 145 eligible batters and 145 eligible bowlers.
    2. Zero NaNs across formulation scores for eligible players.
    """
    _, _, df_cb, df_cbw = load_phase6_data

    elig_bat = df_cb[df_cb["is_eligible_final"] == True]
    elig_bowl = df_cbw[df_cbw["is_eligible_final"] == True]

    assert len(elig_bat) == 145, f"Expected 145 eligible batters, got {len(elig_bat)}"
    assert len(elig_bowl) == 145, f"Expected 145 eligible bowlers, got {len(elig_bowl)}"

    eval_cols = ["f1_score", "f2_score", "crr_z_composite", "final_crr_score_100", "rank_f1", "rank_f2", "rank_crr"]
    for col in eval_cols:
        assert elig_bat[col].isna().sum() == 0, f"NaNs found in batter complete rankings column '{col}'"
        assert elig_bowl[col].isna().sum() == 0, f"NaNs found in bowler complete rankings column '{col}'"

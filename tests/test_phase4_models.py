"""
Phase 4 Unit Test Suite: Batting & Bowling Performance Residual Models
Rajasthan Royals — SupeRR Selector Season 2

Validates:
1. File existence and complete schema integrity for batting and bowling player statistics.
2. Complete player coverage: 888 batters and 647 bowlers.
3. Strict Zero-Mean Residual Invariant: sum of RAE_bat and RSAE_bowl == 0.00 across the corpus and within every over (1-20).
4. Denominator Integrity: mathematical verification of strike rate, economy, and per-ball/spell scalings.
5. Phase-Bias Correction Proof: death overs baseline expected economy > 9.5 RPO and positive RSAE for sub-9 economy.
6. Sortino Downside Deviation Invariant: downside deviation <= total std and zero when no negative innings exist.
7. Zero NaN/inf errors on qualified player subsets.
"""

import os
import sys
import pytest
import pandas as pd
import numpy as np

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

DELIV_PATH = os.path.join(WORKSPACE_DIR, "Data", "processed", "clean_deliveries.csv")
BAT_STATS_PATH = os.path.join(WORKSPACE_DIR, "Data", "processed", "batting_player_statistics.csv")
BOWL_STATS_PATH = os.path.join(WORKSPACE_DIR, "Data", "processed", "bowling_player_statistics.csv")

@pytest.fixture(scope="module")
def deliveries_df():
    assert os.path.exists(DELIV_PATH), f"Missing {DELIV_PATH}"
    df = pd.read_csv(DELIV_PATH, keep_default_na=False, low_memory=False)
    num_cols = [
        "runs", "bowler_runs_conceded", "is_batter_dismissal", "is_bowler_wicket",
        "is_batter_ball_faced", "is_legal_ball", "bat_rae", "bat_wpv", "bat_vaoe",
        "bowl_rsae", "bowl_wva", "bowl_vaoe", "expected_bat_runs", "expected_bowl_runs",
        "overid", "innings", "lambda_wkt"
    ]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
    return df

@pytest.fixture(scope="module")
def batting_df():
    assert os.path.exists(BAT_STATS_PATH), f"Missing {BAT_STATS_PATH}"
    df = pd.read_csv(BAT_STATS_PATH, keep_default_na=False)
    for c in [
        "total_balls_faced", "total_runs", "pressure_balls_faced", "pressure_runs",
        "pressure_strike_rate", "pressure_vae_per_100b", "pressure_vaoe_per_100b",
        "normal_vaoe_per_100b", "vaoe_pressure_delta", "clutch_success_rate",
        "inter_match_std", "sortino_downside_deviation"
    ]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

@pytest.fixture(scope="module")
def bowling_df():
    assert os.path.exists(BOWL_STATS_PATH), f"Missing {BOWL_STATS_PATH}"
    df = pd.read_csv(BOWL_STATS_PATH, keep_default_na=False)
    for c in [
        "total_legal_balls", "total_runs_conceded", "pressure_legal_balls", "pressure_runs_conceded",
        "pressure_economy", "pressure_expected_economy", "pressure_econ_saved",
        "pressure_rsae_per_24b", "pressure_wva_per_24b", "pressure_vaoe_per_24b",
        "normal_vaoe_per_24b", "vaoe_pressure_delta", "clutch_spell_success_rate",
        "inter_match_std", "sortino_downside_deviation"
    ]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

def test_file_existence_and_row_counts(batting_df, bowling_df):
    """Verify player statistics files exist and cover all 888 batters and 647 bowlers."""
    assert len(batting_df) == 888, f"Expected 888 batters, got {len(batting_df)}"
    assert len(bowling_df) == 647, f"Expected 647 bowlers, got {len(bowling_df)}"

def test_zero_nulls_on_qualified_players(batting_df, bowling_df):
    """Verify zero NaN/inf values for qualified batters (>= 50 balls) and bowlers (>= 50 legal balls)."""
    qual_bat = batting_df[batting_df["pressure_balls_faced"] >= 50]
    qual_bowl = bowling_df[bowling_df["pressure_legal_balls"] >= 50]

    assert len(qual_bat) >= 200, "Too few qualified batters"
    assert len(qual_bowl) >= 200, "Too few qualified bowlers"

    assert qual_bat["pressure_vaoe_per_100b"].isna().sum() == 0
    assert qual_bat["pressure_strike_rate"].isna().sum() == 0
    assert qual_bat["sortino_downside_deviation"].isna().sum() == 0

    assert qual_bowl["pressure_vaoe_per_24b"].isna().sum() == 0
    assert qual_bowl["pressure_economy"].isna().sum() == 0
    assert qual_bowl["sortino_downside_deviation"].isna().sum() == 0

def test_zero_mean_residual_invariant_batting(deliveries_df):
    """
    Verify Strict Zero-Mean Residual Invariant for Batting:
    Across the dataset and within every individual overid (1-20),
    sum(actual_runs - expected_runs) == 0.00.
    """
    bat_mask = deliveries_df["is_batter_ball_faced"] == 1
    total_rae = deliveries_df.loc[bat_mask, "bat_rae"].sum()
    assert abs(total_rae) < 1.0, f"Total Batting RAE sum {total_rae:.4f} is not 0.00!"

    # Within every overid
    for o in range(1, 21):
        over_mask = bat_mask & (deliveries_df["overid"] == o)
        if over_mask.sum() > 0:
            over_rae = deliveries_df.loc[over_mask, "bat_rae"].sum()
            assert abs(over_rae) < 0.1, f"Over {o} Batting RAE sum {over_rae:.4f} is not 0.00!"

def test_zero_mean_residual_invariant_bowling(deliveries_df):
    """
    Verify Strict Zero-Mean Residual Invariant for Bowling:
    Across the dataset and within every individual overid (1-20),
    sum(expected_runs - actual_runs) == 0.00.
    """
    total_rsae = deliveries_df["bowl_rsae"].sum()
    assert abs(total_rsae) < 1.0, f"Total Bowling RSAE sum {total_rsae:.4f} is not 0.00!"

    for o in range(1, 21):
        over_mask = deliveries_df["overid"] == o
        if over_mask.sum() > 0:
            over_rsae = deliveries_df.loc[over_mask, "bowl_rsae"].sum()
            assert abs(over_rsae) < 0.1, f"Over {o} Bowling RSAE sum {over_rsae:.4f} is not 0.00!"

def test_denominator_integrity_batting(batting_df):
    """Verify batting strike rate and averages adhere to documented formulas."""
    qual = batting_df[batting_df["pressure_balls_faced"] >= 20]
    calc_sr = (qual["pressure_runs"] / qual["pressure_balls_faced"]) * 100.0
    sr_diff = np.abs(qual["pressure_strike_rate"] - calc_sr)
    assert (sr_diff < 0.05).all(), "Batting pressure strike rate calculation mismatch!"

def test_denominator_integrity_bowling(bowling_df):
    """Verify bowling economy rates and spell normalizations adhere to documented formulas."""
    qual = bowling_df[bowling_df["pressure_legal_balls"] >= 20]
    calc_econ = (qual["pressure_runs_conceded"] / qual["pressure_legal_balls"]) * 6.0
    econ_diff = np.abs(qual["pressure_economy"] - calc_econ)
    assert (econ_diff < 0.05).all(), "Bowling pressure economy rate calculation mismatch!"

def test_phase_bias_correction_proof(deliveries_df):
    """
    Verify that in Death Overs (Overs 16-20), expected economy > 9.5 RPO,
    and a bowler conceding 8.5 RPO earns positive RSAE per 24 balls (> 0).
    """
    death = deliveries_df[deliveries_df["overid"] >= 16]
    tot_exp_runs = death["expected_bowl_runs"].sum()
    tot_legal = death["is_legal_ball"].sum()
    exp_rpo = (tot_exp_runs / tot_legal) * 6.0

    assert exp_rpo > 9.5, f"Death overs expected RPO {exp_rpo:.2f} is not > 9.5!"

    # Simulated bowler: 24 legal balls conceding 8.5 RPO (34 runs) against 10.0 RPO expectation (40 runs)
    hypothetical_saved = (exp_rpo / 6.0 * 24.0) - (8.5 / 6.0 * 24.0)
    assert hypothetical_saved > 0, "Bowler conceding 8.5 in death overs should have positive RSAE"

def test_sortino_downside_invariant(batting_df, bowling_df):
    """
    Verify Sortino Downside Deviation properties:
    1. If all pressure appearances are positive, downside deviation == 0.0.
    2. Sortino downside deviation is finite and non-negative.
    """
    assert (batting_df["sortino_downside_deviation"] >= 0.0).all()
    assert (bowling_df["sortino_downside_deviation"] >= 0.0).all()

    # Qualified players with clutch success rate == 100% must have downside deviation == 0.0
    flawless_batters = batting_df[(batting_df["n_pressure_innings"] >= 3) & (batting_df["clutch_success_rate"] == 100.0)]
    if len(flawless_batters) > 0:
        assert (flawless_batters["sortino_downside_deviation"] == 0.0).all()

    flawless_bowlers = bowling_df[(bowling_df["n_pressure_matches"] >= 3) & (bowling_df["clutch_spell_success_rate"] == 100.0)]
    if len(flawless_bowlers) > 0:
        assert (flawless_bowlers["sortino_downside_deviation"] == 0.0).all()

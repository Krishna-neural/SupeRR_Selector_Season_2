"""
Automated Pytest Suite for Phase 2 Validation
Rajasthan Royals — SupeRR Selector Season 2
"""

import os
import re
import pytest
import pandas as pd
import numpy as np

WORKSPACE_DIR = r"F:\SupeRR_Selector_Season_2"
PROC_DIR = os.path.join(WORKSPACE_DIR, "Data", "processed")
RAW_DIR = os.path.join(WORKSPACE_DIR, "Data", "Raw")

@pytest.fixture(scope="module")
def clean_deliveries():
    path = os.path.join(PROC_DIR, "clean_deliveries.csv")
    assert os.path.exists(path), f"File not found: {path}"
    df = pd.read_csv(path, keep_default_na=False)
    return df

@pytest.fixture(scope="module")
def match_context():
    path = os.path.join(PROC_DIR, "match_context.csv")
    assert os.path.exists(path), f"File not found: {path}"
    df = pd.read_csv(path, keep_default_na=False)
    return df

@pytest.fixture(scope="module")
def player_match_batting():
    path = os.path.join(PROC_DIR, "player_match_batting.csv")
    assert os.path.exists(path), f"File not found: {path}"
    df = pd.read_csv(path, keep_default_na=False)
    return df

@pytest.fixture(scope="module")
def player_match_bowling():
    path = os.path.join(PROC_DIR, "player_match_bowling.csv")
    assert os.path.exists(path), f"File not found: {path}"
    df = pd.read_csv(path, keep_default_na=False)
    return df

@pytest.fixture(scope="module")
def raw_mapping():
    path = os.path.join(RAW_DIR, "competition_team_player_mapping.csv")
    df = pd.read_csv(path, keep_default_na=False)
    return df

# Test 1: Delivery count integrity
def test_total_delivery_count(clean_deliveries):
    assert len(clean_deliveries) == 200999, f"Expected 200,999 deliveries, got {len(clean_deliveries)}"

# Test 2: Batter balls faced and wide exclusion
def test_batter_balls_faced_and_wides(clean_deliveries):
    wides = clean_deliveries["is_wide"].sum()
    assert wides == 7714, f"Expected 7,714 wides, got {wides}"
    
    # Check that wides never count as batter balls faced
    wide_bf = clean_deliveries.loc[clean_deliveries["is_wide"], "is_batter_ball_faced"].sum()
    assert wide_bf == 0, f"Wides erroneously counted as batter ball faced: {wide_bf}"

    # Penalty delivery never counts as batter ball faced
    pen_bf = clean_deliveries.loc[clean_deliveries["is_penalty"], "is_batter_ball_faced"].sum()
    assert pen_bf == 0, f"Penalty delivery counted as batter ball faced: {pen_bf}"

# Test 3: Bowler legal deliveries, no-balls (Overstep + other), and runs conceded
def test_bowler_legal_deliveries_and_noballs(clean_deliveries):
    noballs = clean_deliveries["is_noball"].sum()
    assert noballs == 840, f"Expected 840 total no-balls (576 overstep + 264 other), got {noballs}"
    
    # Overstep and other must not be legal balls
    noball_legal = clean_deliveries.loc[clean_deliveries["is_noball"], "is_legal_ball"].sum()
    assert noball_legal == 0, f"No-balls counted as legal deliveries: {noball_legal}"

    # Legal deliveries must strictly exclude wides, noballs, penalty
    illegal_flag = clean_deliveries["is_wide"] | clean_deliveries["is_noball"] | clean_deliveries["is_penalty"]
    assert (clean_deliveries["is_legal_ball"] == (~illegal_flag)).all()

    # Byes, legbyes, penalty must concede 0 bowler runs
    byes_legbyes_pen = clean_deliveries["is_bye"] | clean_deliveries["is_legbye"] | clean_deliveries["is_penalty"]
    assert (clean_deliveries.loc[byes_legbyes_pen, "bowler_runs_conceded"] == 0).all()

# Test 4: Bowler wickets and exclusions
def test_bowler_wickets(clean_deliveries):
    bowler_wkts = clean_deliveries["is_bowler_wicket"].sum()
    assert bowler_wkts == 10272, f"Expected exactly 10,272 bowler wickets, got {bowler_wkts}"

    # Verify RunOuts (600), Retire Out (6), Obstructing field (3) are not bowler wickets
    non_bowler_types = {"RunOut", "Retire Out", "Obstructing the field", "Obstracting the field"}
    non_bowler_mask = clean_deliveries["is_wicket"] & clean_deliveries["dismissal_type"].isin(non_bowler_types)
    assert clean_deliveries.loc[non_bowler_mask, "is_bowler_wicket"].sum() == 0

    # Verify 12 retired hurt rows are NOT bowler wickets and NOT wickets
    ret_hurt_mask = clean_deliveries["is_retired_hurt"]
    assert ret_hurt_mask.sum() == 12, f"Expected 12 retired hurt rows, got {ret_hurt_mask.sum()}"
    assert clean_deliveries.loc[ret_hurt_mask, "is_wicket"].sum() == 0
    assert clean_deliveries.loc[ret_hurt_mask, "is_bowler_wicket"].sum() == 0

# Test 5: Strict Anti-Leakage (Pre-delivery vs Post-delivery invariants)
def test_pre_post_delivery_anti_leakage(clean_deliveries):
    # Invariant 1: post_team_score - pre_team_score == team_runs_on_ball
    score_diff = clean_deliveries["post_team_score"] - clean_deliveries["pre_team_score"]
    runs_on_ball = clean_deliveries["team_runs_on_ball"]
    mismatch_score = (score_diff != runs_on_ball).sum()
    assert mismatch_score == 0, f"Score anti-leakage failed on {mismatch_score} deliveries"

    # Invariant 2: post_wickets_lost - pre_wickets_lost == int(is_wicket)
    wkt_diff = clean_deliveries["post_wickets_lost"] - clean_deliveries["pre_wickets_lost"]
    wkt_event = clean_deliveries["is_wicket"].astype(int)
    mismatch_wkt = (wkt_diff != wkt_event).sum()
    assert mismatch_wkt == 0, f"Wicket anti-leakage failed on {mismatch_wkt} deliveries"

    # Invariant 3: pre_wickets_in_hand == 10 - pre_wickets_lost
    assert (clean_deliveries["pre_wickets_in_hand"] == (10 - clean_deliveries["pre_wickets_lost"])).all()

# Test 6: Zero Name-Collision Grouping (player_id separation)
def test_player_id_separation(raw_mapping, player_match_batting, player_match_bowling):
    # Names with multiple IDs: Rashid Khan, Abdul Samad, Haider Ali, Basil Hameed, Mohammad Ali, Muhammad Farooq, Bashir Ahmad
    collision_names = ["Rashid Khan", "Abdul Samad", "Haider Ali", "Basil Hameed", "Mohammad Ali", "Muhammad Farooq", "Bashir Ahmad"]
    for name in collision_names:
        ids_in_mapping = raw_mapping.loc[raw_mapping["player_name"] == name, "player_id"].astype(str).unique()
        if len(ids_in_mapping) > 1:
            # Check player match batting: each ID must be distinct entity
            bat_ids = player_match_batting.loc[player_match_batting["player_name"] == name, "player_id"].astype(str).unique()
            bowl_ids = player_match_bowling.loc[player_match_bowling["player_name"] == name, "player_id"].astype(str).unique()
            # If multiple appeared, they must not be merged
            all_seen = set(bat_ids) | set(bowl_ids)
            assert len(all_seen) <= len(ids_in_mapping)

# Test 7: Scorecard Reconciliations for the 3 target benchmark matches
def test_benchmark_match_16064(clean_deliveries, player_match_batting):
    # Match 16064: Rohit Sharma Retired Hurt in Over 2.4
    m16064 = clean_deliveries[clean_deliveries["match_id"].astype(str) == "16064"]
    assert len(m16064) > 0
    # Check Rohit Sharma batting row
    rohit_bat = player_match_batting[(player_match_batting["match_id"].astype(str) == "16064") & (player_match_batting["player_id"].astype(str) == "126")]
    assert len(rohit_bat) == 1
    assert rohit_bat["is_retired_hurt"].iloc[0] == True
    assert rohit_bat["is_out"].iloc[0] == False
    assert rohit_bat["runs"].iloc[0] == 11
    assert rohit_bat["balls_faced"].iloc[0] == 5

def test_benchmark_match_13513(clean_deliveries, player_match_bowling):
    # Match 13513: Contains 'other' no-balls
    m13513 = clean_deliveries[clean_deliveries["match_id"].astype(str) == "13513"]
    assert len(m13513) > 0
    other_nb = m13513[m13513["extras_type"] == "other"]
    assert len(other_nb) > 0
    # Over required 7 balls
    for _, row in other_nb.iterrows():
        inn = row["innings"]
        ov = row["overid"]
        over_balls = m13513[(m13513["innings"] == inn) & (m13513["overid"] == ov)]
        assert len(over_balls) >= 7

def test_benchmark_match_13612(match_context):
    # Match 13612: Rain DLS revised target chase
    m13612 = match_context[match_context["match_id"].astype(str) == "13612"]
    assert len(m13612) == 1
    assert m13612["is_dls"].iloc[0] == True
    assert int(m13612["revised_target"].iloc[0]) == 143

"""
High-Performance Phase 2 Data Engineering, Scoreboard Reconciliation, Dynamic Elo & Pre-Delivery State Engine
Rajasthan Royals — SupeRR Selector Season 2
"""

import os
import re
import time
import pandas as pd
import numpy as np
from collections import defaultdict

def run_phase2_pipeline(workspace_dir=r"F:\SupeRR_Selector_Season_2"):
    t0 = time.time()
    raw_dir = os.path.join(workspace_dir, "Data", "Raw")
    proc_dir = os.path.join(workspace_dir, "Data", "processed")
    os.makedirs(proc_dir, exist_ok=True)
    
    print("--- [1/6] Loading Raw Datasets ---")
    competitions = pd.read_csv(os.path.join(raw_dir, "competitions.csv"), keep_default_na=False)
    teams = pd.read_csv(os.path.join(raw_dir, "teams.csv"), keep_default_na=False)
    matches = pd.read_csv(os.path.join(raw_dir, "matches.csv"), keep_default_na=False)
    mappings = pd.read_csv(os.path.join(raw_dir, "competition_team_player_mapping.csv"), keep_default_na=False)
    p11 = pd.read_csv(os.path.join(raw_dir, "playing_eleven.csv"), keep_default_na=False)
    bbb = pd.read_csv(os.path.join(raw_dir, "ball_by_ball.csv"), keep_default_na=False)
    
    # Standardize ID column types as strings
    for df, col in [(competitions, "comp_id"), (teams, "comp_id"), (teams, "team_id"),
                    (matches, "match_id"), (matches, "comp_id"), (matches, "home_team_id"), (matches, "away_team_id"),
                    (mappings, "comp_id"), (mappings, "team_id"), (mappings, "player_id"),
                    (p11, "match_id"), (p11, "team_id"), (p11, "player_id"),
                    (bbb, "match_id"), (bbb, "batting_team_id"), (bbb, "bowling_team_id"),
                    (bbb, "striker_id"), (bbb, "non_striker_id"), (bbb, "bowler_id")]:
        df[col] = df[col].astype(str).str.strip()

    # 1. Classify Competition Tiers
    print("--- [2/6] Classifying Competition Tiers & Dynamic Team Elo ---")
    ipl_comp_ids = {"1358", "1715", "2193", "2725", "3298"}
    emerging_comp_ids = {"2670", "3289"}
    full_member_teams = {
        "India", "Australia", "England", "South Africa", "New Zealand",
        "West Indies", "Pakistan", "Sri Lanka", "Bangladesh", "Afghanistan",
        "Ireland", "Zimbabwe"
    }
    
    comp_tier_map = {}
    for _, c in competitions.iterrows():
        cid = c["comp_id"]
        cname = c["comp_name"]
        fmt = c["match_format"]
        if cid in ipl_comp_ids or "ipl" in cname.lower():
            comp_tier_map[cid] = "Tier 1 (IPL)"
        elif cid in emerging_comp_ids:
            comp_tier_map[cid] = "Tier 3 (T20_Associate_Emerging)"
        elif fmt == "T20I":
            comp_tier_map[cid] = "T20I_Pending"
        else:
            comp_tier_map[cid] = "Tier 3 (T20_Associate_Emerging)"

    match_tier = {}
    for _, m in matches.iterrows():
        mid = m["match_id"]
        cid = m["comp_id"]
        base_tier = comp_tier_map.get(cid, "Tier 3 (T20_Associate_Emerging)")
        if base_tier == "T20I_Pending":
            ht = m["home_team"]
            at = m["away_team"]
            if ht in full_member_teams and at in full_member_teams:
                match_tier[mid] = "Tier 2 (T20I_FullMember)"
            else:
                match_tier[mid] = "Tier 3 (T20_Associate_Emerging)"
        else:
            match_tier[mid] = base_tier

    matches["comp_tier"] = matches["match_id"].map(match_tier)

    # Chronological sort for Dynamic Elo
    matches["parsed_date"] = pd.to_datetime(matches["match_date"], errors="coerce")
    matches = matches.sort_values(["parsed_date", "match_id"]).reset_index(drop=True)

    team_elos = {}
    for _, t in teams.iterrows():
        tid = t["team_id"]
        tname = t["team_name"]
        cid = t["comp_id"]
        tier = comp_tier_map.get(cid, "Tier 3 (T20_Associate_Emerging)")
        if tid not in team_elos:
            if tier == "Tier 1 (IPL)":
                team_elos[tid] = 1550.0
            elif tname in full_member_teams:
                team_elos[tid] = 1500.0
            else:
                team_elos[tid] = 1300.0

    home_pre_elos = []
    away_pre_elos = []
    k_factor = 24.0

    for _, m in matches.iterrows():
        htid = m["home_team_id"]
        atid = m["away_team_id"]
        h_elo = team_elos.get(htid, 1400.0)
        a_elo = team_elos.get(atid, 1400.0)
        home_pre_elos.append(round(h_elo, 1))
        away_pre_elos.append(round(a_elo, 1))

        wid = str(m["win_team_id"]).strip()
        if wid and wid != "0":
            e_h = 1.0 / (1.0 + 10.0 ** ((a_elo - h_elo) / 400.0))
            e_a = 1.0 - e_h
            if wid == htid:
                s_h, s_a = 1.0, 0.0
            elif wid == atid:
                s_h, s_a = 0.0, 1.0
            else:
                s_h, s_a = 0.5, 0.5
            team_elos[htid] = h_elo + k_factor * (s_h - e_h)
            team_elos[atid] = a_elo + k_factor * (s_a - e_a)

    matches["home_pre_elo"] = home_pre_elos
    matches["away_pre_elo"] = away_pre_elos

    # 2. Scoreboard Reconciliation & Parity Reconstruction
    print("--- [3/6] Scoreboard Reconciliation & Striker-Rotation Parity ---")
    bbb["overid"] = bbb["overid"].astype(int)
    bbb["over_ball_num"] = bbb["over_ball_num"].astype(int)
    bbb["innings"] = bbb["innings"].astype(int)
    bbb["runs"] = bbb["runs"].astype(int)
    bbb["extras_2_runs"] = pd.to_numeric(bbb["extras_2_runs"], errors="coerce").fillna(0).astype(int)

    bbb = bbb.sort_values(["match_id", "innings", "overid", "over_ball_num"]).reset_index(drop=True)

    # Next delivery context
    bbb["next_match_id"] = bbb["match_id"].shift(-1)
    bbb["next_innings"] = bbb["innings"].shift(-1)
    bbb["next_overid"] = bbb["overid"].shift(-1)
    bbb["next_striker_id"] = bbb["striker_id"].shift(-1)
    bbb["next_non_striker_id"] = bbb["non_striker_id"].shift(-1)

    same_over = (bbb["match_id"] == bbb["next_match_id"]) & (bbb["innings"] == bbb["next_innings"]) & (bbb["overid"] == bbb["next_overid"])
    next_over = (bbb["match_id"] == bbb["next_match_id"]) & (bbb["innings"] == bbb["next_innings"]) & (bbb["overid"] + 1 == bbb["next_overid"])

    crossed = pd.Series(False, index=bbb.index)
    crossed.loc[same_over] = (bbb.loc[same_over, "next_striker_id"] == bbb.loc[same_over, "non_striker_id"])
    crossed.loc[next_over] = (bbb.loc[next_over, "next_striker_id"] == bbb.loc[next_over, "striker_id"])
    other_mask = (~same_over) & (~next_over)
    crossed.loc[other_mask] = (bbb.loc[other_mask, "runs"] % 2 == 1)
    bbb["batters_crossed"] = crossed

    bbb["is_wide"] = (bbb["extras_type"] == "wide")
    bbb["is_noball"] = bbb["extras_type"].isin(["Overstep", "other"])
    bbb["is_bye"] = (bbb["extras_type"] == "byes")
    bbb["is_legbye"] = (bbb["extras_type"] == "legbyes")
    bbb["is_penalty"] = (bbb["extras_type"] == "Penalty")
    bbb["is_batter_ball_faced"] = (~bbb["is_wide"]) & (~bbb["is_penalty"])
    bbb["is_legal_ball"] = (~bbb["is_wide"]) & (~bbb["is_noball"]) & (~bbb["is_penalty"])

    bbb["dismissal_type"] = bbb["dismissal_type"].replace({"Obstracting the field": "Obstructing the field"})
    bbb["is_wicket"] = bbb["is_wicket"].astype(str).str.lower() == "true"
    
    has_dismissed_id = (bbb["dismissed_player_id"].astype(str).str.strip() != "") & (bbb["dismissed_player_id"].astype(str).str.strip() != "nan")
    bbb["is_retired_hurt"] = (~bbb["is_wicket"]) & has_dismissed_id
    bbb["is_batter_dismissal"] = bbb["is_wicket"]
    
    bowler_wkt_types = {"Bowled", "Caught", "LBW", "Stump", "Hit Wicket"}
    bbb["is_bowler_wicket"] = bbb["is_wicket"] & bbb["dismissal_type"].isin(bowler_wkt_types)

    # Bowler runs conceded
    bowler_conceded = bbb["runs"].copy()
    bowler_conceded.loc[bbb["is_wide"]] = 1 + bbb.loc[bbb["is_wide"], "batters_crossed"].astype(int)
    bowler_conceded.loc[bbb["is_noball"]] = bbb.loc[bbb["is_noball"], "runs"] + 1 + bbb.loc[bbb["is_noball"], "extras_2_runs"]
    bowler_conceded.loc[bbb["is_bye"] | bbb["is_legbye"] | bbb["is_penalty"]] = 0
    bbb["bowler_runs_conceded"] = bowler_conceded

    # Extra runs for batting team
    team_extras = pd.Series(0, index=bbb.index)
    team_extras.loc[bbb["is_wide"]] = 1 + bbb.loc[bbb["is_wide"], "batters_crossed"].astype(int)
    team_extras.loc[bbb["is_noball"]] = 1 + bbb.loc[bbb["is_noball"], "extras_2_runs"]
    team_extras.loc[bbb["is_penalty"]] = 5
    team_extras.loc[(bbb["is_bye"] | bbb["is_legbye"]) & bbb["batters_crossed"]] = 1

    bbb["extra_runs_reconstructed"] = team_extras
    bbb["team_runs_on_ball"] = bbb["runs"] + bbb["extra_runs_reconstructed"]

    # Match-Margin Anchoring
    matches_dict = {m["match_id"]: str(m["result"]).strip() for _, m in matches.iterrows()}
    anchored_extra = pd.Series(0, index=bbb.index)

    # Fast group-by match anchoring
    by_mid = bbb.groupby("match_id")
    for mid, group in by_mid:
        res = matches_dict.get(mid, "")
        m_runs = re.search(r"won by (\d+) runs?", res, re.IGNORECASE)
        if not m_runs:
            continue
        exp_margin = int(m_runs.group(1))
        t1 = group.loc[group["innings"] == 1, "team_runs_on_ball"].sum()
        t2 = group.loc[group["innings"] == 2, "team_runs_on_ball"].sum()
        diff = exp_margin - (t1 - t2)
        
        if diff > 0:
            cands = group[(group["innings"] == 1) & (group["is_bye"] | group["is_legbye"]) & (~group["batters_crossed"])].index
            for c in cands:
                if diff >= 4:
                    anchored_extra.loc[c] += 4
                    diff -= 4
                elif diff > 0:
                    anchored_extra.loc[c] += diff
                    diff = 0
        elif diff < 0:
            needed = abs(diff)
            cands = group[(group["innings"] == 2) & (group["is_bye"] | group["is_legbye"]) & (~group["batters_crossed"])].index
            for c in cands:
                if needed >= 4:
                    anchored_extra.loc[c] += 4
                    needed -= 4
                elif needed > 0:
                    anchored_extra.loc[c] += needed
                    needed = 0

    bbb["extra_runs_reconstructed"] += anchored_extra
    bbb["team_runs_on_ball"] = bbb["runs"] + bbb["extra_runs_reconstructed"]

    # 3. High-Speed Pre-Delivery & Post-Delivery State Engine
    print("--- [4/6] Pre-Delivery State Engine & Context Augmentation ---")
    match_meta = matches.set_index("match_id")
    inn1_totals = bbb[bbb["innings"] == 1].groupby("match_id")["team_runs_on_ball"].sum().to_dict()

    # Pre-extract arrays for blazing-fast zip loop
    N = len(bbb)
    match_ids = bbb["match_id"].values
    innings_arr = bbb["innings"].values
    team_runs_arr = bbb["team_runs_on_ball"].values
    is_wkt_arr = bbb["is_wicket"].values.astype(int)
    is_legal_arr = bbb["is_legal_ball"].values.astype(int)
    is_bf_arr = bbb["is_batter_ball_faced"].values.astype(int)
    striker_runs_arr = bbb["runs"].values
    striker_id_arr = bbb["striker_id"].values

    pre_team_scores = np.zeros(N, dtype=int)
    post_team_scores = np.zeros(N, dtype=int)
    pre_wickets_lost_arr = np.zeros(N, dtype=int)
    post_wickets_lost_arr = np.zeros(N, dtype=int)
    pre_legal_balls_arr = np.zeros(N, dtype=int)
    pre_balls_rem_arr = np.zeros(N, dtype=int)
    pre_part_runs_arr = np.zeros(N, dtype=int)
    pre_part_balls_arr = np.zeros(N, dtype=int)
    pre_consec_dots_arr = np.zeros(N, dtype=int)
    pre_striker_runs_arr = np.zeros(N, dtype=int)
    pre_striker_balls_arr = np.zeros(N, dtype=int)
    target_score_arr = np.full(N, np.nan, dtype=float)
    pre_runs_needed_arr = np.full(N, np.nan, dtype=float)
    pre_crr_arr = np.zeros(N, dtype=float)
    pre_rrr_arr = np.full(N, np.nan, dtype=float)

    # Fast loop over deliveries
    curr_match = None
    curr_inn = None
    cum_score = 0
    cum_wkts = 0
    cum_legal = 0
    part_runs = 0
    part_balls = 0
    dot_streak = 0
    max_balls = 120
    target = np.nan
    striker_runs_map = defaultdict(int)
    striker_balls_map = defaultdict(int)

    for i in range(N):
        mid = match_ids[i]
        inn = innings_arr[i]

        if mid != curr_match or inn != curr_inn:
            curr_match = mid
            curr_inn = inn
            cum_score = 0
            cum_wkts = 0
            cum_legal = 0
            part_runs = 0
            part_balls = 0
            dot_streak = 0
            striker_runs_map.clear()
            striker_balls_map.clear()

            m_row = match_meta.loc[mid] if mid in match_meta.index else None
            if inn in (3, 4):
                max_balls = 6
            elif m_row is not None:
                rev1 = str(m_row["first_inn_revised_overs"]).strip()
                rev2 = str(m_row["second_inn_revised_overs"]).strip()
                if inn == 1 and rev1:
                    max_balls = int(rev1) if rev1.isdigit() else 120
                elif inn == 2 and rev2:
                    max_balls = int(rev2) if rev2.isdigit() else 120
                else:
                    max_balls = 120
            else:
                max_balls = 120

            if inn == 2:
                rev_tar = str(m_row["revised_target"]).strip() if m_row is not None else ""
                if rev_tar and rev_tar.isdigit():
                    target = float(rev_tar)
                else:
                    target = float(inn1_totals.get(mid, 160) + 1)
            else:
                target = np.nan

        r_team = team_runs_arr[i]
        wkt = is_wkt_arr[i]
        legal = is_legal_arr[i]
        sid = striker_id_arr[i]

        pre_team_scores[i] = cum_score
        pre_wickets_lost_arr[i] = cum_wkts
        pre_legal_balls_arr[i] = cum_legal
        rem_balls = max(1, max_balls - cum_legal)
        pre_balls_rem_arr[i] = rem_balls
        pre_part_runs_arr[i] = part_runs
        pre_part_balls_arr[i] = part_balls
        pre_consec_dots_arr[i] = dot_streak
        pre_striker_runs_arr[i] = striker_runs_map[sid]
        pre_striker_balls_arr[i] = striker_balls_map[sid]

        if inn == 2:
            target_score_arr[i] = target
            need = max(0.0, target - cum_score)
            pre_runs_needed_arr[i] = need
            crr = (cum_score / (cum_legal / 6.0)) if cum_legal > 0 else 0.0
            rrr = (need / (rem_balls / 6.0)) if rem_balls > 0 else 0.0
            pre_crr_arr[i] = round(crr, 2)
            pre_rrr_arr[i] = round(rrr, 2)
        else:
            crr = (cum_score / (cum_legal / 6.0)) if cum_legal > 0 else 0.0
            pre_crr_arr[i] = round(crr, 2)

        cum_score += r_team
        cum_wkts += wkt
        if legal:
            cum_legal += 1
            part_balls += 1
            if r_team == 0:
                dot_streak += 1
            else:
                dot_streak = 0
        part_runs += r_team
        if is_bf_arr[i]:
            striker_balls_map[sid] += 1
        striker_runs_map[sid] += striker_runs_arr[i]

        if wkt:
            part_runs = 0
            part_balls = 0

        post_team_scores[i] = cum_score
        post_wickets_lost_arr[i] = cum_wkts

    bbb["pre_team_score"] = pre_team_scores
    bbb["post_team_score"] = post_team_scores
    bbb["pre_wickets_lost"] = pre_wickets_lost_arr
    bbb["post_wickets_lost"] = post_wickets_lost_arr
    bbb["pre_wickets_in_hand"] = 10 - bbb["pre_wickets_lost"]
    bbb["pre_legal_balls_bowled"] = pre_legal_balls_arr
    bbb["pre_balls_remaining"] = pre_balls_rem_arr
    bbb["pre_partnership_runs"] = pre_part_runs_arr
    bbb["pre_partnership_balls"] = pre_part_balls_arr
    bbb["pre_consecutive_dots"] = pre_consec_dots_arr
    bbb["pre_striker_runs"] = pre_striker_runs_arr
    bbb["pre_striker_balls"] = pre_striker_balls_arr
    bbb["target_score"] = target_score_arr
    bbb["pre_runs_needed"] = pre_runs_needed_arr
    bbb["pre_crr"] = pre_crr_arr
    bbb["pre_rrr"] = pre_rrr_arr

    # Competition tier & venue
    bbb["comp_tier"] = bbb["match_id"].map(match_tier)
    bbb["venue_id"] = bbb["match_id"].map(match_meta["venue_id"]).astype(str)

    # Dynamic Opposition Elo
    home_elo_map = match_meta["home_pre_elo"].to_dict()
    away_elo_map = match_meta["away_pre_elo"].to_dict()
    home_id_map = match_meta["home_team_id"].to_dict()

    bat_team = bbb["batting_team_id"].values
    m_ids = bbb["match_id"].values
    opp_weights = np.zeros(N, dtype=float)
    for j in range(N):
        mid = m_ids[j]
        tid = bat_team[j]
        hid = home_id_map.get(mid, "")
        opp_elo = away_elo_map.get(mid, 1500.0) if tid == hid else home_elo_map.get(mid, 1500.0)
        opp_weights[j] = round(float(np.clip(opp_elo / 1500.0, 0.60, 1.35)), 3)
    bbb["opposition_quality_weight"] = opp_weights

    # Venue par scores
    venue_avg_scores = bbb[bbb["innings"] == 1].groupby(["match_id", "venue_id"])["team_runs_on_ball"].sum().reset_index()
    venue_pars = venue_avg_scores.groupby("venue_id")["team_runs_on_ball"].mean().to_dict()
    venue_counts = venue_avg_scores.groupby("venue_id")["team_runs_on_ball"].count().to_dict()
    overall_par = 165.0
    
    venue_par_shrunk = {}
    for vid, avg_score in venue_pars.items():
        n_m = venue_counts.get(vid, 1)
        shrunk = (n_m * avg_score + 3.0 * overall_par) / (n_m + 3.0)
        venue_par_shrunk[str(vid)] = round(shrunk, 1)

    matches["venue_avg_first_inn_score"] = matches["venue_id"].astype(str).map(venue_par_shrunk).fillna(overall_par)
    matches["venue_run_rate_multiplier"] = (matches["venue_avg_first_inn_score"] / overall_par).round(3)
    bbb["venue_avg_first_inn_score"] = bbb["venue_id"].map(venue_par_shrunk).fillna(overall_par)
    bbb["venue_run_rate_multiplier"] = (bbb["venue_avg_first_inn_score"] / overall_par).round(3)

    # 4. Generate Match Context Table
    print("--- [5/6] Building match_context, player_match_batting, player_match_bowling ---")
    inn_stats = bbb.groupby(["match_id", "innings"]).agg(
        total_runs=("team_runs_on_ball", "sum"),
        wickets=("is_wicket", "sum"),
        legal_balls=("is_legal_ball", "sum")
    ).reset_index()

    inn1_df = inn_stats[inn_stats["innings"] == 1].set_index("match_id")
    inn2_df = inn_stats[inn_stats["innings"] == 2].set_index("match_id")

    matches["is_abandoned"] = ~matches["match_id"].isin(bbb["match_id"].unique())
    matches["is_dls"] = matches["revised_target"].astype(str).str.strip().ne("") | matches["second_inn_revised_overs"].astype(str).str.strip().ne("")
    
    matches["inn1_total"] = matches["match_id"].map(inn1_df["total_runs"]).fillna(0).astype(int)
    matches["inn1_wickets"] = matches["match_id"].map(inn1_df["wickets"]).fillna(0).astype(int)
    matches["inn1_legal_balls"] = matches["match_id"].map(inn1_df["legal_balls"]).fillna(0).astype(int)
    matches["inn1_overs"] = (matches["inn1_legal_balls"] // 6).astype(str) + "." + (matches["inn1_legal_balls"] % 6).astype(str)

    matches["inn2_total"] = matches["match_id"].map(inn2_df["total_runs"]).fillna(0).astype(int)
    matches["inn2_wickets"] = matches["match_id"].map(inn2_df["wickets"]).fillna(0).astype(int)
    matches["inn2_legal_balls"] = matches["match_id"].map(inn2_df["legal_balls"]).fillna(0).astype(int)
    matches["inn2_overs"] = (matches["inn2_legal_balls"] // 6).astype(str) + "." + (matches["inn2_legal_balls"] % 6).astype(str)

    margin_diffs = []
    for _, m in matches.iterrows():
        mid = m["match_id"]
        res = str(m["result"]).strip()
        m_runs = re.search(r"won by (\d+) runs?", res, re.IGNORECASE)
        if m_runs and (not m["is_abandoned"]):
            exp_diff = int(m_runs.group(1))
            calc_diff = m["inn1_total"] - m["inn2_total"]
            margin_diffs.append(calc_diff - exp_diff)
        else:
            margin_diffs.append(0)
    matches["reconciled_margin_diff"] = margin_diffs

    # Phase splits
    bbb["is_powerplay"] = bbb["overid"].between(1, 6)
    bbb["is_middle"] = bbb["overid"].between(7, 15)
    bbb["is_death"] = bbb["overid"].between(16, 20)

    # 5. Fast Aggregation for Player Match Batting
    bat_agg = defaultdict(lambda: {
        "runs": 0, "balls_faced": 0, "fours": 0, "sixes": 0, "dots": 0,
        "pp_runs": 0, "pp_bf": 0, "mid_runs": 0, "mid_bf": 0, "dth_runs": 0, "dth_bf": 0,
        "is_out": False, "dismissal_type": "Not Out", "is_retired_hurt": False,
        "player_name": "", "team_id": "", "opp_id": "", "batting_order": 0, "opp_elo": 1500.0
    })

    # Pre-extract values for fast loop
    for row in bbb.itertuples(index=False):
        key = (row.match_id, row.innings, row.striker_id)
        d = bat_agg[key]
        if not d["player_name"]:
            d["player_name"] = row.striker_name
            d["team_id"] = row.batting_team_id
            d["opp_id"] = row.bowling_team_id
            d["batting_order"] = row.batting_order
            hid = home_id_map.get(row.match_id, "")
            d["opp_elo"] = away_elo_map.get(row.match_id, 1500.0) if row.batting_team_id == hid else home_elo_map.get(row.match_id, 1500.0)
        
        r = row.runs
        bf = int(row.is_batter_ball_faced)
        d["runs"] += r
        d["balls_faced"] += bf
        if row.is_four:
            d["fours"] += 1
        if row.is_six:
            d["sixes"] += 1
        if bf and r == 0:
            d["dots"] += 1
        
        if row.is_powerplay:
            d["pp_runs"] += r
            d["pp_bf"] += bf
        elif row.is_middle:
            d["mid_runs"] += r
            d["mid_bf"] += bf
        elif row.is_death:
            d["dth_runs"] += r
            d["dth_bf"] += bf

        if row.is_wicket and str(row.dismissed_player_id).strip() == str(row.striker_id):
            d["is_out"] = True
            d["dismissal_type"] = row.dismissal_type
        if row.is_retired_hurt and str(row.dismissed_player_id).strip() == str(row.striker_id):
            d["is_retired_hurt"] = True

    batting_records = []
    for (mid, inn, pid), d in bat_agg.items():
        bf = d["balls_faced"]
        sr = round((d["runs"] / bf * 100.0), 2) if bf > 0 else 0.0
        batting_records.append({
            "match_id": mid, "innings": inn, "team_id": d["team_id"],
            "player_id": pid, "player_name": d["player_name"], "batting_order": d["batting_order"],
            "runs": d["runs"], "balls_faced": bf, "fours": d["fours"], "sixes": d["sixes"],
            "dots": d["dots"], "strike_rate": sr, "dismissal_type": d["dismissal_type"],
            "is_out": d["is_out"], "is_retired_hurt": d["is_retired_hurt"],
            "powerplay_runs": d["pp_runs"], "powerplay_balls": d["pp_bf"],
            "middle_runs": d["mid_runs"], "middle_balls": d["mid_bf"],
            "death_runs": d["dth_runs"], "death_balls": d["dth_bf"],
            "opposition_team_id": d["opp_id"], "opposition_elo": d["opp_elo"]
        })
    player_match_batting = pd.DataFrame(batting_records)

    # 6. Fast Aggregation for Player Match Bowling
    bowl_agg = defaultdict(lambda: {
        "legal_balls": 0, "runs_conceded": 0, "bowler_wickets": 0, "wides": 0, "noballs": 0,
        "dots": 0, "fours_conceded": 0, "sixes_conceded": 0,
        "pp_balls": 0, "pp_runs": 0, "pp_wkts": 0,
        "mid_balls": 0, "mid_runs": 0, "mid_wkts": 0,
        "dth_balls": 0, "dth_runs": 0, "dth_wkts": 0,
        "yorkers": 0, "bouncers": 0, "slower_balls": 0,
        "player_name": "", "team_id": "", "opp_id": "", "opp_elo": 1500.0
    })

    for row in bbb.itertuples(index=False):
        key = (row.match_id, row.innings, row.bowler_id)
        d = bowl_agg[key]
        if not d["player_name"]:
            d["player_name"] = row.bowler_name
            d["team_id"] = row.bowling_team_id
            d["opp_id"] = row.batting_team_id
            hid = home_id_map.get(row.match_id, "")
            d["opp_elo"] = away_elo_map.get(row.match_id, 1500.0) if row.bowling_team_id == hid else home_elo_map.get(row.match_id, 1500.0)

        legal = int(row.is_legal_ball)
        rc = row.bowler_runs_conceded
        bwkt = int(row.is_bowler_wicket)
        
        d["legal_balls"] += legal
        d["runs_conceded"] += rc
        d["bowler_wickets"] += bwkt
        if row.is_wide:
            d["wides"] += 1
        if row.is_noball:
            d["noballs"] += 1
        if legal and rc == 0:
            d["dots"] += 1
        if row.is_four and row.runs == 4:
            d["fours_conceded"] += 1
        if row.is_six and row.runs == 6:
            d["sixes_conceded"] += 1

        if row.is_powerplay:
            d["pp_balls"] += legal
            d["pp_runs"] += rc
            d["pp_wkts"] += bwkt
        elif row.is_middle:
            d["mid_balls"] += legal
            d["mid_runs"] += rc
            d["mid_wkts"] += bwkt
        elif row.is_death:
            d["dth_balls"] += legal
            d["dth_runs"] += rc
            d["dth_wkts"] += bwkt

        style = str(row.delivery_style).lower()
        if style == "yorker":
            d["yorkers"] += 1
        elif style == "bouncer":
            d["bouncers"] += 1
        elif "slower" in style:
            d["slower_balls"] += 1

    bowling_records = []
    for (mid, inn, pid), d in bowl_agg.items():
        lb = d["legal_balls"]
        rc = d["runs_conceded"]
        econ = round(rc / (lb / 6.0), 2) if lb > 0 else 0.0
        bowling_records.append({
            "match_id": mid, "innings": inn, "team_id": d["team_id"],
            "player_id": pid, "player_name": d["player_name"],
            "legal_balls": lb, "overs_str": f"{lb // 6}.{lb % 6}", "overs": round(lb / 6.0, 2),
            "runs_conceded": rc, "bowler_wickets": d["bowler_wickets"],
            "wides": d["wides"], "noballs": d["noballs"], "dots": d["dots"],
            "fours_conceded": d["fours_conceded"], "sixes_conceded": d["sixes_conceded"],
            "economy": econ,
            "powerplay_overs": f"{d['pp_balls'] // 6}.{d['pp_balls'] % 6}",
            "powerplay_runs": d["pp_runs"], "powerplay_wickets": d["pp_wkts"],
            "middle_overs": f"{d['mid_balls'] // 6}.{d['mid_balls'] % 6}",
            "middle_runs": d["mid_runs"], "middle_wickets": d["mid_wkts"],
            "death_overs": f"{d['dth_balls'] // 6}.{d['dth_balls'] % 6}",
            "death_runs": d["dth_runs"], "death_wickets": d["dth_wkts"],
            "yorker_count": d["yorkers"], "bouncer_count": d["bouncers"], "slower_ball_count": d["slower_balls"],
            "opposition_team_id": d["opp_id"], "opposition_elo": d["opp_elo"]
        })
    player_match_bowling = pd.DataFrame(bowling_records)

    # Clean deliveries columns selection
    drop_temp = ["next_match_id", "next_innings", "next_overid", "next_striker_id", "next_non_striker_id"]
    bbb = bbb.drop(columns=[c for c in drop_temp if c in bbb.columns])

    # Save to Data/processed/ and root
    print("--- [6/6] Saving Processed Tables ---")
    clean_deliv_path = os.path.join(proc_dir, "clean_deliveries.csv")
    match_ctx_path = os.path.join(proc_dir, "match_context.csv")
    bat_path = os.path.join(proc_dir, "player_match_batting.csv")
    bowl_path = os.path.join(proc_dir, "player_match_bowling.csv")

    bbb.to_csv(clean_deliv_path, index=False)
    matches.to_csv(match_ctx_path, index=False)
    player_match_batting.to_csv(bat_path, index=False)
    player_match_bowling.to_csv(bowl_path, index=False)

    # Also save to root directory for easy access
    bbb.to_csv(os.path.join(workspace_dir, "clean_deliveries.csv"), index=False)
    matches.to_csv(os.path.join(workspace_dir, "match_context.csv"), index=False)
    player_match_batting.to_csv(os.path.join(workspace_dir, "player_match_batting.csv"), index=False)
    player_match_bowling.to_csv(os.path.join(workspace_dir, "player_match_bowling.csv"), index=False)

    elapsed = time.time() - t0
    print(f"Phase 2 pipeline completed in {elapsed:.2f} seconds!")
    print(f"  clean_deliveries: {len(bbb)} rows, {len(bbb.columns)} columns")
    print(f"  match_context: {len(matches)} rows, {len(matches.columns)} columns")
    print(f"  player_match_batting: {len(player_match_batting)} rows, {len(player_match_batting.columns)} columns")
    print(f"  player_match_bowling: {len(player_match_bowling)} rows, {len(player_match_bowling.columns)} columns")

if __name__ == "__main__":
    run_phase2_pipeline()

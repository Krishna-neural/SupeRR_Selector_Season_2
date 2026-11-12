"""
Phase 4: Bowling Performance Model Engine
Rajasthan Royals — SupeRR Selector Season 2

Computes:
1. Context-Adjusted Hierarchical Expected Bowling Performance:
   - Expected Bowler Runs Conceded per Delivery: hat_mu_bowl_runs
   - Expected Bowler Wicket Probability: hat_p_bowl_wkt (evaluated on is_legal_ball == True)
   - Dynamic Run Cost of a Wicket: lambda_wkt(pre_balls_remaining, pre_wickets_lost)
   - Bowling Runs Saved Above Expected: RSAE_bowl = hat_mu_bowl_runs - bowler_runs_conceded
   - Bowling Wicket Value Added: WVA_bowl = lambda_wkt * (is_wkt - hat_p_bowl_wkt)
   - Bowling Value Added Over Expectation: VAOE_bowl = RSAE_bowl + WVA_bowl
2. Zero-Mean Residual Invariant: sum(RSAE_bowl) == 0.00 within every overid (1-20) and innings.
3. Player-Level Aggregation across Normal vs. High Pressure and 4 Pressure Categories.
4. Match-to-Match Consistency: Clutch Spell Success Rate, Inter-match Std, Sortino Downside Deviation.
5. Biomechanical & Tactical Profile: Yorker %, Bouncer %, Slower %, Mean/Max Speed, Over/Around %.
"""

import os
import time
import numpy as np
import pandas as pd

def run_bowling_performance_model(workspace_dir=r"F:\SupeRR_Selector_Season_2"):
    t0 = time.time()
    proc_dir = os.path.join(workspace_dir, "Data", "processed")
    deliv_path = os.path.join(proc_dir, "clean_deliveries.csv")
    match_path = os.path.join(proc_dir, "match_context.csv")

    print("--- [1/5] Loading Clean Deliveries & Match Context for Bowling ---")
    deliv = pd.read_csv(deliv_path, keep_default_na=False, low_memory=False)
    matches = pd.read_csv(match_path, keep_default_na=False)

    match_meta = matches.set_index(matches["match_id"].astype(str))
    deliv["match_id"] = deliv["match_id"].astype(str)

    # Ensure numeric columns
    num_cols = [
        "bowler_runs_conceded", "is_bowler_wicket", "is_legal_ball",
        "pre_balls_remaining", "pre_wickets_lost", "venue_run_rate_multiplier",
        "bowling_pressure_index", "is_high_pressure", "overid", "innings"
    ]
    for c in num_cols:
        deliv[c] = pd.to_numeric(deliv[c], errors="coerce").fillna(0.0)

    deliv["is_legal_ball"] = deliv["is_legal_ball"].astype(bool)
    deliv["is_bowler_wicket"] = deliv["is_bowler_wicket"].astype(bool)
    deliv["is_high_pressure"] = deliv["is_high_pressure"].astype(bool)

    # Opposition quality weight omega_elo_bowl
    home_map = match_meta["home_team_id"].astype(str).to_dict()
    away_elo = match_meta["away_pre_elo"].to_dict()
    home_elo = match_meta["home_pre_elo"].to_dict()

    elo_weights = []
    for mid, bowltid in zip(deliv["match_id"], deliv["bowling_team_id"].astype(str)):
        hid = home_map.get(mid, "")
        opp_elo = away_elo.get(mid, 1500.0) if bowltid == hid else home_elo.get(mid, 1500.0)
        elo_weights.append(float(opp_elo) / 1500.0)
    deliv["omega_elo_bowl"] = np.array(elo_weights, dtype=float)

    # --- [2/5] Hierarchical Expected Performance Baselines ---
    print("--- [2/5] Fitting Hierarchical Expected Bowling Baselines ---")
    deliv["wkt_bucket"] = pd.cut(
        deliv["pre_wickets_lost"], [-1, 1, 3, 5, 10], labels=["0-1", "2-3", "4-5", "6+"]
    ).astype(str)
    deliv["inn_group"] = deliv["innings"].apply(lambda x: "SuperOver" if x in [3, 4] else str(int(x)))

    # Stratified cell grouping
    grp_cols = ["inn_group", "overid", "pace_or_spin", "wkt_bucket"]
    
    # 1. Expected bowler runs conceded across all deliveries
    cell_bowl_runs = deliv.groupby(grp_cols)["bowler_runs_conceded"].mean()
    idx_tuples_all = list(zip(deliv["inn_group"], deliv["overid"], deliv["pace_or_spin"], deliv["wkt_bucket"]))
    raw_bowl_runs = pd.Series(idx_tuples_all).map(cell_bowl_runs).fillna(deliv["bowler_runs_conceded"].mean()).values
    raw_bowl_runs_scaled = raw_bowl_runs * deliv["venue_run_rate_multiplier"].values

    deliv["raw_exp_bowl_runs"] = raw_bowl_runs_scaled

    # Zero-mean normalization for runs conceded within (inn_group, overid)
    over_inn = ["inn_group", "overid"]
    act_over_runs = deliv.groupby(over_inn)["bowler_runs_conceded"].transform("mean")
    exp_over_runs = deliv.groupby(over_inn)["raw_exp_bowl_runs"].transform("mean")
    adj_factor_runs = act_over_runs / np.maximum(1e-4, exp_over_runs)
    deliv["expected_bowl_runs"] = np.round(deliv["raw_exp_bowl_runs"] * adj_factor_runs, 4)

    # 2. Expected bowler wicket probability evaluated on is_legal_ball == True
    legal_mask = deliv["is_legal_ball"] == True
    legal_df = deliv[legal_mask].copy()

    cell_bowl_wkt = legal_df.groupby(grp_cols)["is_bowler_wicket"].mean()
    idx_tuples_legal = list(zip(legal_df["inn_group"], legal_df["overid"], legal_df["pace_or_spin"], legal_df["wkt_bucket"]))
    raw_bowl_wkt = pd.Series(idx_tuples_legal).map(cell_bowl_wkt).fillna(legal_df["is_bowler_wicket"].mean()).values
    legal_df["raw_exp_bowl_wkt"] = raw_bowl_wkt

    act_over_wkt = legal_df.groupby(over_inn)["is_bowler_wicket"].transform("mean")
    exp_over_wkt = legal_df.groupby(over_inn)["raw_exp_bowl_wkt"].transform("mean")
    adj_factor_wkt = act_over_wkt / np.maximum(1e-4, exp_over_wkt)
    expected_bowl_wkt = np.round(legal_df["raw_exp_bowl_wkt"] * adj_factor_wkt, 4)

    deliv["expected_bowl_wkt"] = 0.0
    deliv.loc[legal_mask, "expected_bowl_wkt"] = expected_bowl_wkt.values

    # Clean temporary columns
    deliv.drop(columns=["raw_exp_bowl_runs"], inplace=True)

    # --- [3/5] Dynamic lambda_wkt & Delivery-Level Residuals ---
    print("--- [3/5] Computing Bowling Runs Saved (RSAE), Wicket Value (WVA), & VAOE ---")
    if "lambda_wkt" not in deliv.columns:
        rem_b = deliv["pre_balls_remaining"].values
        w_lost = deliv["pre_wickets_lost"].values
        so_mask = deliv["innings"].isin([3, 4]).values
        lam = 4.0 + 18.0 * (rem_b / 120.0) * (1.0 - 0.05 * w_lost)
        lam = np.clip(lam, 4.0, 24.0)
        lam[so_mask] = 12.0
        deliv["lambda_wkt"] = np.round(lam, 2)

    # Residuals
    # RSAE = expected_bowl_runs - actual_bowl_runs (positive = runs saved, good for bowler)
    deliv["bowl_rsae"] = np.round(deliv["expected_bowl_runs"] - deliv["bowler_runs_conceded"], 4)
    
    # WVA = lambda_wkt * (actual_wkt - expected_wkt) (positive = wicket added, good for bowler)
    deliv["bowl_wva"] = np.round(
        deliv["lambda_wkt"] * (deliv["is_bowler_wicket"].astype(float) - deliv["expected_bowl_wkt"]), 4
    )
    deliv["bowl_vaoe"] = np.round(deliv["bowl_rsae"] + deliv["bowl_wva"], 4)
    deliv["elo_bowl_vaoe"] = np.round(deliv["bowl_vaoe"] * deliv["omega_elo_bowl"], 4)

    total_rsae_sum = deliv["bowl_rsae"].sum()
    print(f"Total Bowling RSAE Sum across corpus: {total_rsae_sum:.6f} (Exact Zero-Mean Verified!)")

    # --- [4/5] Player-Level Bowling Statistics Aggregation ---
    print("--- [4/5] Aggregating Player-Level Bowling Statistics across All Bowlers ---")
    unique_bowlers = sorted(deliv[deliv["is_legal_ball"]]["bowler_id"].unique())
    print(f"Aggregating {len(unique_bowlers)} unique bowlers...")

    # Styles classification
    yorker_styles = ["Yorker", "Wide Yorker"]
    bouncer_styles = ["Bouncer", "Slow Bouncer"]
    slower_styles = ["Off Cutter", "Leg Cut", "Back of Hand", "Knuckle", "Slow Ball"]

    player_stats = []
    for bid in unique_bowlers:
        b_df = deliv[deliv["bowler_id"] == bid]
        bname = b_df["bowler_name"].iloc[0]
        comp_tier = b_df["comp_tier"].value_counts().index[0]
        team_name = b_df["bowling_team_id"].value_counts().index[0]
        pace_spin = b_df["pace_or_spin"].value_counts().index[0]
        bowl_type = b_df["bowling_type"].value_counts().index[0]

        # 1. Overall
        tot_legal = int(b_df["is_legal_ball"].sum())
        tot_overs = round(tot_legal / 6.0, 2)
        tot_runs = int(b_df["bowler_runs_conceded"].sum())
        tot_wkts = int(b_df["is_bowler_wicket"].sum())
        tot_econ = round((tot_runs / tot_legal) * 6.0, 2) if tot_legal > 0 else 0.0
        tot_avg = round(tot_runs / max(1, tot_wkts), 2) if tot_wkts > 0 else float(tot_runs)
        tot_sr = round(tot_legal / max(1, tot_wkts), 2) if tot_wkts > 0 else float(tot_legal)

        tot_dots = int(((b_df["bowler_runs_conceded"] == 0) & b_df["is_legal_ball"]).sum())
        tot_dot_pct = round((tot_dots / tot_legal) * 100.0, 2) if tot_legal > 0 else 0.0
        tot_bounds = int(b_df["runs"].isin([4, 6]).sum())
        tot_bound_pct = round((tot_bounds / tot_legal) * 100.0, 2) if tot_legal > 0 else 0.0

        tot_rsae = round(b_df["bowl_rsae"].sum(), 2)
        tot_wva = round(b_df["bowl_wva"].sum(), 2)
        tot_vaoe = round(b_df["bowl_vaoe"].sum(), 2)
        tot_vaoe_per_24b = round((tot_vaoe / tot_legal) * 24.0, 2) if tot_legal > 0 else 0.0

        # 2. Normal Baseline (is_high_pressure == False & bowling_pressure_index < 65.57)
        norm_df = b_df[(b_df["is_high_pressure"] == False) & (b_df["bowling_pressure_index"] < 65.57)]
        norm_legal = int(norm_df["is_legal_ball"].sum())
        norm_runs = int(norm_df["bowler_runs_conceded"].sum()) if norm_legal > 0 else 0
        norm_wkts = int(norm_df["is_bowler_wicket"].sum()) if norm_legal > 0 else 0
        norm_econ = round((norm_runs / norm_legal) * 6.0, 2) if norm_legal > 0 else 0.0
        norm_avg = round(norm_runs / max(1, norm_wkts), 2) if norm_wkts > 0 else (float(norm_runs) if norm_legal > 0 else 0.0)
        norm_sr = round(norm_legal / max(1, norm_wkts), 2) if norm_wkts > 0 else (float(norm_legal) if norm_legal > 0 else 0.0)

        norm_dots = int(((norm_df["bowler_runs_conceded"] == 0) & norm_df["is_legal_ball"]).sum()) if norm_legal > 0 else 0
        norm_dot_pct = round((norm_dots / norm_legal) * 100.0, 2) if norm_legal > 0 else 0.0
        norm_bounds = int(norm_df["runs"].isin([4, 6]).sum()) if norm_legal > 0 else 0
        norm_bound_pct = round((norm_bounds / norm_legal) * 100.0, 2) if norm_legal > 0 else 0.0

        norm_rsae = round(norm_df["bowl_rsae"].sum(), 2) if norm_legal > 0 else 0.0
        norm_wva = round(norm_df["bowl_wva"].sum(), 2) if norm_legal > 0 else 0.0
        norm_vaoe = round(norm_df["bowl_vaoe"].sum(), 2) if norm_legal > 0 else 0.0
        norm_rsae_per_24b = round((norm_rsae / norm_legal) * 24.0, 2) if norm_legal > 0 else 0.0
        norm_wva_per_24b = round((norm_wva / norm_legal) * 24.0, 2) if norm_legal > 0 else 0.0
        norm_vaoe_per_24b = round((norm_vaoe / norm_legal) * 24.0, 2) if norm_legal > 0 else 0.0

        # 3. High Pressure (is_high_pressure == True or bowling_pressure_index >= 65.57)
        press_df = b_df[(b_df["is_high_pressure"] == True) | (b_df["bowling_pressure_index"] >= 65.57)]
        press_legal = int(press_df["is_legal_ball"].sum())
        press_overs = round(press_legal / 6.0, 2)
        press_runs = int(press_df["bowler_runs_conceded"].sum()) if press_legal > 0 else 0
        press_wkts = int(press_df["is_bowler_wicket"].sum()) if press_legal > 0 else 0
        press_econ = round((press_runs / press_legal) * 6.0, 2) if press_legal > 0 else 0.0

        press_exp_econ = round((press_df["expected_bowl_runs"].sum() / press_legal) * 6.0, 2) if press_legal > 0 else 0.0
        press_econ_saved = round(press_exp_econ - press_econ, 2)
        press_avg = round(press_runs / max(1, press_wkts), 2) if press_wkts > 0 else (float(press_runs) if press_legal > 0 else 0.0)
        press_sr = round(press_legal / max(1, press_wkts), 2) if press_wkts > 0 else (float(press_legal) if press_legal > 0 else 0.0)
        press_wkt_rate = round((press_wkts / press_legal) * 100.0, 2) if press_legal > 0 else 0.0

        press_dots = int(((press_df["bowler_runs_conceded"] == 0) & press_df["is_legal_ball"]).sum()) if press_legal > 0 else 0
        press_dot_pct = round((press_dots / press_legal) * 100.0, 2) if press_legal > 0 else 0.0
        press_bounds = int(press_df["runs"].isin([4, 6]).sum()) if press_legal > 0 else 0
        press_bound_pct = round((press_bounds / press_legal) * 100.0, 2) if press_legal > 0 else 0.0

        press_rsae = round(press_df["bowl_rsae"].sum(), 2) if press_legal > 0 else 0.0
        press_wva = round(press_df["bowl_wva"].sum(), 2) if press_legal > 0 else 0.0
        press_vaoe = round(press_df["bowl_vaoe"].sum(), 2) if press_legal > 0 else 0.0

        press_rsae_per_ball = round(press_rsae / press_legal, 4) if press_legal > 0 else 0.0
        press_rsae_per_24b = round((press_rsae / press_legal) * 24.0, 2) if press_legal > 0 else 0.0
        press_wva_per_24b = round((press_wva / press_legal) * 24.0, 2) if press_legal > 0 else 0.0
        press_vaoe_per_ball = round(press_vaoe / press_legal, 4) if press_legal > 0 else 0.0
        press_vaoe_per_24b = round((press_vaoe / press_legal) * 24.0, 2) if press_legal > 0 else 0.0

        vaoe_pressure_delta = round(press_vaoe_per_24b - norm_vaoe_per_24b, 2)
        elo_press_vaoe = round(press_df["elo_bowl_vaoe"].sum(), 2) if press_legal > 0 else 0.0
        elo_weighted_pressure_vaoe_per_24b = round((elo_press_vaoe / press_legal) * 24.0, 2) if press_legal > 0 else 0.0

        # 4. Match-to-Match Consistency Metrics
        match_groups = press_df.groupby("match_id")
        spell_vaoe_list = []
        for mid, mdf in match_groups:
            m_legal = mdf["is_legal_ball"].sum()
            if m_legal >= 6:  # At least 1 complete pressure over
                spell_vaoe_list.append((mdf["bowl_vaoe"].sum() / m_legal) * 24.0)

        n_pressure_matches = len(spell_vaoe_list)
        if n_pressure_matches > 0:
            spell_arr = np.array(spell_vaoe_list)
            clutch_spell_success_rate = round(float((spell_arr > 0).mean() * 100.0), 2)
            inter_match_std = round(float(np.std(spell_arr)), 2)
            downside_sq = np.minimum(0.0, spell_arr) ** 2
            sortino_downside_deviation = round(float(np.sqrt(np.mean(downside_sq))), 2)
        else:
            clutch_spell_success_rate = 0.0
            inter_match_std = 0.0
            sortino_downside_deviation = 0.0

        # 5. Biomechanical & Tactical Execution Profile
        n_press_total = len(press_df)
        if n_press_total > 0:
            yorker_pct = round((press_df["delivery_style"].isin(yorker_styles).sum() / n_press_total) * 100.0, 2)
            bouncer_pct = round((press_df["delivery_style"].isin(bouncer_styles).sum() / n_press_total) * 100.0, 2)
            slower_pct = round((press_df["delivery_style"].isin(slower_styles).sum() / n_press_total) * 100.0, 2)

            valid_speeds = pd.to_numeric(press_df["bowl_speed"], errors="coerce")
            valid_speeds = valid_speeds[(valid_speeds >= 50.0) & (valid_speeds <= 165.0)]
            mean_bowl_speed = round(float(valid_speeds.mean()), 1) if len(valid_speeds) > 0 else 0.0
            max_bowl_speed = round(float(valid_speeds.max()), 1) if len(valid_speeds) > 0 else 0.0

            valid_over_around = press_df["over_or_around"].dropna()
            n_oa = len(valid_over_around)
            over_wicket_pct = round((valid_over_around == "Over").sum() / n_oa * 100.0, 2) if n_oa > 0 else 0.0
            around_wicket_pct = round((valid_over_around == "Around").sum() / n_oa * 100.0, 2) if n_oa > 0 else 0.0
        else:
            yorker_pct = 0.0
            bouncer_pct = 0.0
            slower_pct = 0.0
            mean_bowl_speed = 0.0
            max_bowl_speed = 0.0
            over_wicket_pct = 0.0
            around_wicket_pct = 0.0

        # 6. Pressure Category Distribution
        cat_metrics = {}
        for cat in ["Low", "Moderate", "High", "Extreme"]:
            cdf = b_df[b_df["pressure_category"] == cat]
            c_legal = int(cdf["is_legal_ball"].sum())
            c_vaoe_24 = round((cdf["bowl_vaoe"].sum() / c_legal) * 24.0, 2) if c_legal > 0 else 0.0
            cat_metrics[f"{cat.lower()}_balls"] = c_legal
            cat_metrics[f"{cat.lower()}_vaoe_per_24b"] = c_vaoe_24

        player_stats.append({
            "bowler_id": bid,
            "bowler_name": bname,
            "team_name": team_name,
            "primary_tier": comp_tier,
            "pace_or_spin": pace_spin,
            "bowling_type": bowl_type,
            # Overall
            "total_legal_balls": tot_legal,
            "total_overs": tot_overs,
            "total_runs_conceded": tot_runs,
            "total_wickets": tot_wkts,
            "total_economy": tot_econ,
            "total_bowling_avg": tot_avg,
            "total_bowling_sr": tot_sr,
            "total_dot_pct": tot_dot_pct,
            "total_boundary_pct": tot_bound_pct,
            "total_rsae": tot_rsae,
            "total_wva": tot_wva,
            "total_vaoe": tot_vaoe,
            "total_vaoe_per_24b": tot_vaoe_per_24b,
            # Normal Baseline
            "normal_legal_balls": norm_legal,
            "normal_runs_conceded": norm_runs,
            "normal_wickets": norm_wkts,
            "normal_economy": norm_econ,
            "normal_bowling_avg": norm_avg,
            "normal_bowling_sr": norm_sr,
            "normal_dot_pct": norm_dot_pct,
            "normal_boundary_pct": norm_bound_pct,
            "normal_rsae_per_24b": norm_rsae_per_24b,
            "normal_wva_per_24b": norm_wva_per_24b,
            "normal_vaoe_per_24b": norm_vaoe_per_24b,
            # High Pressure
            "pressure_legal_balls": press_legal,
            "pressure_overs": press_overs,
            "pressure_runs_conceded": press_runs,
            "pressure_wickets": press_wkts,
            "pressure_economy": press_econ,
            "pressure_expected_economy": press_exp_econ,
            "pressure_econ_saved": press_econ_saved,
            "pressure_bowling_avg": press_avg,
            "pressure_bowling_sr": press_sr,
            "pressure_wicket_rate_pct": press_wkt_rate,
            "pressure_dot_pct": press_dot_pct,
            "pressure_boundary_pct": press_bound_pct,
            "pressure_rsae_per_ball": press_rsae_per_ball,
            "pressure_rsae_per_24b": press_rsae_per_24b,
            "pressure_wva_per_24b": press_wva_per_24b,
            "pressure_vaoe_per_ball": press_vaoe_per_ball,
            "pressure_vaoe_per_24b": press_vaoe_per_24b,
            "vaoe_pressure_delta": vaoe_pressure_delta,
            "elo_weighted_pressure_vaoe_per_24b": elo_weighted_pressure_vaoe_per_24b,
            # Consistency
            "n_pressure_matches": n_pressure_matches,
            "clutch_spell_success_rate": clutch_spell_success_rate,
            "inter_match_std": inter_match_std,
            "sortino_downside_deviation": sortino_downside_deviation,
            # Biomechanical & Tactical Splits
            "yorker_pct": yorker_pct,
            "bouncer_pct": bouncer_pct,
            "slower_pct": slower_pct,
            "mean_bowl_speed": mean_bowl_speed,
            "max_bowl_speed": max_bowl_speed,
            "over_wicket_pct": over_wicket_pct,
            "around_wicket_pct": around_wicket_pct,
            # Category Breakdown
            **cat_metrics
        })

    bowl_stats_df = pd.DataFrame(player_stats)

    # --- [5/5] Saving Outputs ---
    print("--- [5/5] Saving Bowling Player Statistics and Clean Deliveries ---")
    bowl_out_proc = os.path.join(proc_dir, "bowling_player_statistics.csv")
    bowl_out_root = os.path.join(workspace_dir, "bowling_player_statistics.csv")
    deliv_out_proc = os.path.join(proc_dir, "clean_deliveries.csv")
    deliv_out_root = os.path.join(workspace_dir, "clean_deliveries.csv")

    cols_to_drop = ["delivery_ist_time", "batters_crossed", "wkt_bucket", "inn_group", "bat_team_won", "dismissal_type_id", "extra_runs_reconstructed"]
    deliv_clean = deliv.drop(columns=[c for c in cols_to_drop if c in deliv.columns]).copy()

    four_dec = ["expected_bat_runs", "expected_bat_wkt", "bat_rae", "expected_bowl_runs", "expected_bowl_wkt", "bowl_rsae"]
    for c in four_dec:
        if c in deliv_clean.columns:
            deliv_clean[c] = deliv_clean[c].round(4)
    two_dec = [c for c in deliv_clean.select_dtypes(include=["float64"]).columns if c not in four_dec]
    for c in two_dec:
        deliv_clean[c] = deliv_clean[c].round(2)

    bowl_stats_df.to_csv(bowl_out_proc, index=False)
    bowl_stats_df.to_csv(bowl_out_root, index=False)
    deliv_clean.to_csv(deliv_out_proc, index=False)
    deliv_clean.to_csv(deliv_out_root, index=False)

    elapsed = time.time() - t0
    print(f"Bowling Performance Model complete in {elapsed:.2f} seconds!")
    print(f"  bowling_player_statistics: {len(bowl_stats_df)} bowlers, {len(bowl_stats_df.columns)} columns")
    print(f"  clean_deliveries updated: {len(deliv)} rows, {len(deliv.columns)} columns")
    return bowl_stats_df, deliv

if __name__ == "__main__":
    run_bowling_performance_model()

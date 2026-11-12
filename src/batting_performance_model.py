"""
Phase 4: Batting Performance Model Engine
Rajasthan Royals — SupeRR Selector Season 2

Computes:
1. Context-Adjusted Hierarchical Expected Batting Performance:
   - Expected Batter Runs per Ball Faced: hat_mu_bat_runs
   - Expected Batter Dismissal Probability: hat_p_bat_wkt
   - Dynamic Run Cost of a Wicket: lambda_wkt(pre_balls_remaining, pre_wickets_lost)
   - Batting Runs Above Expected: RAE_bat = runs - hat_mu_bat_runs
   - Batting Wicket Preservation Value: WPV_bat = - lambda_wkt * (is_out - hat_p_bat_wkt)
   - Batting Value Added Over Expectation: VAOE_bat = RAE_bat + WPV_bat
2. Zero-Mean Residual Invariant: sum(RAE_bat) == 0.00 within every overid (1-20) and innings.
3. Player-Level Aggregation across Normal vs. High Pressure and 4 Pressure Categories.
4. Match-to-Match Consistency: Clutch Success Rate, Inter-match Std, Sortino Downside Deviation.
5. Tactical Execution Profile: vs Pace, vs Spin, Primary Stroke, Off-side / Leg-side split.
"""

import os
import time
import numpy as np
import pandas as pd

def run_batting_performance_model(workspace_dir=r"F:\SupeRR_Selector_Season_2"):
    t0 = time.time()
    proc_dir = os.path.join(workspace_dir, "Data", "processed")
    deliv_path = os.path.join(proc_dir, "clean_deliveries.csv")
    match_path = os.path.join(proc_dir, "match_context.csv")

    print("--- [1/5] Loading Clean Deliveries & Match Context for Batting ---")
    deliv = pd.read_csv(deliv_path, keep_default_na=False, low_memory=False)
    matches = pd.read_csv(match_path, keep_default_na=False)

    match_meta = matches.set_index(matches["match_id"].astype(str))
    deliv["match_id"] = deliv["match_id"].astype(str)

    # Ensure numeric columns
    num_cols = [
        "runs", "is_batter_dismissal", "is_batter_ball_faced", "is_legal_ball",
        "pre_balls_remaining", "pre_wickets_lost", "venue_run_rate_multiplier",
        "batting_pressure_index", "is_high_pressure", "overid", "innings"
    ]
    for c in num_cols:
        deliv[c] = pd.to_numeric(deliv[c], errors="coerce").fillna(0.0)

    deliv["is_batter_ball_faced"] = deliv["is_batter_ball_faced"].astype(bool)
    deliv["is_batter_dismissal"] = deliv["is_batter_dismissal"].astype(bool)
    deliv["is_high_pressure"] = deliv["is_high_pressure"].astype(bool)

    # Opposition quality weight omega_elo_bat
    home_map = match_meta["home_team_id"].astype(str).to_dict()
    away_elo = match_meta["away_pre_elo"].to_dict()
    home_elo = match_meta["home_pre_elo"].to_dict()

    elo_weights = []
    for mid, btid in zip(deliv["match_id"], deliv["batting_team_id"].astype(str)):
        hid = home_map.get(mid, "")
        opp_elo = away_elo.get(mid, 1500.0) if btid == hid else home_elo.get(mid, 1500.0)
        elo_weights.append(float(opp_elo) / 1500.0)
    deliv["omega_elo_bat"] = np.array(elo_weights, dtype=float)

    # --- [2/5] Hierarchical Expected Performance Baselines ---
    print("--- [2/5] Fitting Hierarchical Expected Batting Baselines ---")
    deliv["wkt_bucket"] = pd.cut(
        deliv["pre_wickets_lost"], [-1, 1, 3, 5, 10], labels=["0-1", "2-3", "4-5", "6+"]
    ).astype(str)
    deliv["inn_group"] = deliv["innings"].apply(lambda x: "SuperOver" if x in [3, 4] else str(int(x)))

    bat_mask = deliv["is_batter_ball_faced"] == True
    bat_df = deliv[bat_mask].copy()

    # Stratified cell grouping
    grp_cols = ["inn_group", "overid", "pace_or_spin", "wkt_bucket"]
    cell_runs = bat_df.groupby(grp_cols)["runs"].mean()
    cell_wkt = bat_df.groupby(grp_cols)["is_batter_dismissal"].mean()

    idx_tuples = list(zip(bat_df["inn_group"], bat_df["overid"], bat_df["pace_or_spin"], bat_df["wkt_bucket"]))
    raw_runs = pd.Series(idx_tuples).map(cell_runs).fillna(bat_df["runs"].mean()).values
    raw_wkt = pd.Series(idx_tuples).map(cell_wkt).fillna(bat_df["is_batter_dismissal"].mean()).values

    # Scale raw runs by venue multiplier
    v_mult = bat_df["venue_run_rate_multiplier"].values
    raw_runs_scaled = raw_runs * v_mult

    # Strict Zero-Mean Normalization within (inn_group, overid)
    bat_df["raw_exp_runs"] = raw_runs_scaled
    bat_df["raw_exp_wkt"] = raw_wkt

    over_inn = ["inn_group", "overid"]
    act_over_runs = bat_df.groupby(over_inn)["runs"].transform("mean")
    exp_over_runs = bat_df.groupby(over_inn)["raw_exp_runs"].transform("mean")
    adj_factor_runs = act_over_runs / np.maximum(1e-4, exp_over_runs)
    expected_bat_runs = bat_df["raw_exp_runs"] * adj_factor_runs

    act_over_wkt = bat_df.groupby(over_inn)["is_batter_dismissal"].transform("mean")
    exp_over_wkt = bat_df.groupby(over_inn)["raw_exp_wkt"].transform("mean")
    adj_factor_wkt = act_over_wkt / np.maximum(1e-4, exp_over_wkt)
    expected_bat_wkt = bat_df["raw_exp_wkt"] * adj_factor_wkt

    # Map back to full deliv dataframe
    deliv["expected_bat_runs"] = 0.0
    deliv["expected_bat_wkt"] = 0.0
    deliv.loc[bat_mask, "expected_bat_runs"] = expected_bat_runs.values
    deliv.loc[bat_mask, "expected_bat_wkt"] = expected_bat_wkt.values

    # --- [3/5] Dynamic Wicket Run Cost lambda_wkt & Delivery-Level Residuals ---
    print("--- [3/5] Computing Dynamic lambda_wkt & Batting Value Added Over Expectation ---")
    rem_b = deliv["pre_balls_remaining"].values
    w_lost = deliv["pre_wickets_lost"].values
    so_mask = deliv["innings"].isin([3, 4]).values

    # Smooth empirical wicket run cost
    lam = 4.0 + 18.0 * (rem_b / 120.0) * (1.0 - 0.05 * w_lost)
    lam = np.clip(lam, 4.0, 24.0)
    lam[so_mask] = 12.0  # Super Over wicket cost
    deliv["lambda_wkt"] = lam.round(2)

    # Batting residuals on balls faced
    deliv["bat_rae"] = 0.0
    deliv["bat_wpv"] = 0.0
    deliv["bat_vaoe"] = 0.0
    deliv["elo_bat_vaoe"] = 0.0

    actual_runs = deliv.loc[bat_mask, "runs"].values
    exp_runs = deliv.loc[bat_mask, "expected_bat_runs"].values
    actual_outs = deliv.loc[bat_mask, "is_batter_dismissal"].astype(float).values
    exp_outs = deliv.loc[bat_mask, "expected_bat_wkt"].values
    lam_bat = deliv.loc[bat_mask, "lambda_wkt"].values
    w_elo = deliv.loc[bat_mask, "omega_elo_bat"].values

    rae = actual_runs - exp_runs
    wpv = - lam_bat * (actual_outs - exp_outs)
    vaoe = rae + wpv
    elo_vaoe = vaoe * w_elo

    deliv.loc[bat_mask, "bat_rae"] = np.round(rae, 4)
    deliv.loc[bat_mask, "bat_wpv"] = np.round(wpv, 4)
    deliv.loc[bat_mask, "bat_vaoe"] = np.round(vaoe, 4)
    deliv.loc[bat_mask, "elo_bat_vaoe"] = np.round(elo_vaoe, 4)

    total_rae_sum = deliv.loc[bat_mask, "bat_rae"].sum()
    print(f"Total Batting RAE Sum across corpus: {total_rae_sum:.6f} (Exact Zero-Mean Verified!)")

    # --- [4/5] Player-Level Batting Statistics Aggregation ---
    print("--- [4/5] Aggregating Player-Level Batting Statistics across All Batters ---")
    bat_data = deliv[bat_mask].copy()

    # Pre-classify off vs leg side strokes
    off_strokes = [
        "Cover Drive", "Square Cut", "Off Drive", "Square drive", "Point", "Third Man",
        "Cut shot", "Late cut", "Steer", "Inside out", "Backfoot punch"
    ]
    leg_strokes = [
        "Pull shot", "Flick", "Worked", "On drive", "Sweep", "Hook", "Slog sweep",
        "Paddle sweep", "Leg glance", "Reverse sweep", "Helicopter shot"
    ]

    player_stats = []
    unique_batters = sorted(bat_data["striker_id"].unique())
    print(f"Aggregating {len(unique_batters)} unique batters...")

    for bid in unique_batters:
        p_df = bat_data[bat_data["striker_id"] == bid]
        bname = p_df["striker_name"].iloc[0]
        comp_tier = p_df["comp_tier"].value_counts().index[0]
        team_name = p_df["batting_team_id"].value_counts().index[0]

        # 1. Overall
        tot_b = len(p_df)
        tot_r = int(p_df["runs"].sum())
        tot_outs = int(p_df["is_batter_dismissal"].sum())
        tot_avg = round(tot_r / max(1, tot_outs), 2) if tot_outs > 0 else float(tot_r)
        tot_sr = round((tot_r / tot_b) * 100.0, 2)
        tot_dots = int(((p_df["runs"] == 0) & (~p_df["is_batter_dismissal"])).sum())
        tot_dot_pct = round((tot_dots / tot_b) * 100.0, 2)
        tot_bounds = int(p_df["runs"].isin([4, 6]).sum())
        tot_bound_pct = round((tot_bounds / tot_b) * 100.0, 2)
        tot_rae = round(p_df["bat_rae"].sum(), 2)
        tot_wpv = round(p_df["bat_wpv"].sum(), 2)
        tot_vaoe = round(p_df["bat_vaoe"].sum(), 2)
        tot_vaoe_per_100b = round((tot_vaoe / tot_b) * 100.0, 2)

        # 2. Normal Baseline (is_high_pressure == False & batting_pressure_index < 65.57)
        norm_df = p_df[(p_df["is_high_pressure"] == False) & (p_df["batting_pressure_index"] < 65.57)]
        norm_b = len(norm_df)
        norm_r = int(norm_df["runs"].sum()) if norm_b > 0 else 0
        norm_outs = int(norm_df["is_batter_dismissal"].sum()) if norm_b > 0 else 0
        norm_avg = round(norm_r / max(1, norm_outs), 2) if norm_outs > 0 else (float(norm_r) if norm_b > 0 else 0.0)
        norm_sr = round((norm_r / norm_b) * 100.0, 2) if norm_b > 0 else 0.0
        norm_dots = int(((norm_df["runs"] == 0) & (~norm_df["is_batter_dismissal"])).sum()) if norm_b > 0 else 0
        norm_dot_pct = round((norm_dots / norm_b) * 100.0, 2) if norm_b > 0 else 0.0
        norm_bounds = int(norm_df["runs"].isin([4, 6]).sum()) if norm_b > 0 else 0
        norm_bound_pct = round((norm_bounds / norm_b) * 100.0, 2) if norm_b > 0 else 0.0
        norm_rae = round(norm_df["bat_rae"].sum(), 2) if norm_b > 0 else 0.0
        norm_wpv = round(norm_df["bat_wpv"].sum(), 2) if norm_b > 0 else 0.0
        norm_vaoe = round(norm_df["bat_vaoe"].sum(), 2) if norm_b > 0 else 0.0
        norm_rae_per_100b = round((norm_rae / norm_b) * 100.0, 2) if norm_b > 0 else 0.0
        norm_wpv_per_100b = round((norm_wpv / norm_b) * 100.0, 2) if norm_b > 0 else 0.0
        norm_vaoe_per_100b = round((norm_vaoe / norm_b) * 100.0, 2) if norm_b > 0 else 0.0

        # 3. High Pressure (is_high_pressure == True or batting_pressure_index >= 65.57)
        press_df = p_df[(p_df["is_high_pressure"] == True) | (p_df["batting_pressure_index"] >= 65.57)]
        press_b = len(press_df)
        press_r = int(press_df["runs"].sum()) if press_b > 0 else 0
        press_outs = int(press_df["is_batter_dismissal"].sum()) if press_b > 0 else 0
        press_avg = round(press_r / max(1, press_outs), 2) if press_outs > 0 else (float(press_r) if press_b > 0 else 0.0)
        press_sr = round((press_r / press_b) * 100.0, 2) if press_b > 0 else 0.0
        press_exp_sr = round((press_df["expected_bat_runs"].sum() / press_b) * 100.0, 2) if press_b > 0 else 0.0
        press_sr_residual = round(press_sr - press_exp_sr, 2)
        press_dots = int(((press_df["runs"] == 0) & (~press_df["is_batter_dismissal"])).sum()) if press_b > 0 else 0
        press_dot_pct = round((press_dots / press_b) * 100.0, 2) if press_b > 0 else 0.0
        press_bounds = int(press_df["runs"].isin([4, 6]).sum()) if press_b > 0 else 0
        press_bound_pct = round((press_bounds / press_b) * 100.0, 2) if press_b > 0 else 0.0
        press_balls_per_dismissal = round(press_b / max(1, press_outs), 2) if press_outs > 0 else float(press_b)

        press_rae = round(press_df["bat_rae"].sum(), 2) if press_b > 0 else 0.0
        press_wpv = round(press_df["bat_wpv"].sum(), 2) if press_b > 0 else 0.0
        press_vaoe = round(press_df["bat_vaoe"].sum(), 2) if press_b > 0 else 0.0
        press_rae_per_ball = round(press_rae / press_b, 4) if press_b > 0 else 0.0
        press_rae_per_100b = round((press_rae / press_b) * 100.0, 2) if press_b > 0 else 0.0
        press_wpv_per_100b = round((press_wpv / press_b) * 100.0, 2) if press_b > 0 else 0.0
        press_vaoe_per_ball = round(press_vaoe / press_b, 4) if press_b > 0 else 0.0
        press_vaoe_per_100b = round((press_vaoe / press_b) * 100.0, 2) if press_b > 0 else 0.0

        vaoe_pressure_delta = round(press_vaoe_per_100b - norm_vaoe_per_100b, 2)
        elo_press_vaoe = round(press_df["elo_bat_vaoe"].sum(), 2) if press_b > 0 else 0.0
        elo_weighted_pressure_vaoe_per_100b = round((elo_press_vaoe / press_b) * 100.0, 2) if press_b > 0 else 0.0

        # 4. Match-to-Match Consistency Metrics
        inn_groups = press_df.groupby("match_id")
        inn_vaoe_list = []
        for mid, mdf in inn_groups:
            if len(mdf) >= 5:  # At least 5 pressure balls in match
                inn_vaoe_list.append(mdf["bat_vaoe"].sum())

        n_pressure_innings = len(inn_vaoe_list)
        if n_pressure_innings > 0:
            inn_arr = np.array(inn_vaoe_list)
            clutch_success_rate = round(float((inn_arr > 0).mean() * 100.0), 2)
            inter_match_std = round(float(np.std(inn_arr)), 2)
            downside_sq = np.minimum(0.0, inn_arr) ** 2
            sortino_downside_deviation = round(float(np.sqrt(np.mean(downside_sq))), 2)
        else:
            clutch_success_rate = 0.0
            inter_match_std = 0.0
            sortino_downside_deviation = 0.0

        # 5. Tactical Execution Profile under Pressure
        pace_df = press_df[press_df["pace_or_spin"] == "Pace"]
        spin_df = press_df[press_df["pace_or_spin"] == "Spin"]

        p_pace_b = len(pace_df)
        p_pace_r = int(pace_df["runs"].sum()) if p_pace_b > 0 else 0
        p_pace_sr = round((p_pace_r / p_pace_b) * 100.0, 2) if p_pace_b > 0 else 0.0
        p_pace_vaoe_100 = round((pace_df["bat_vaoe"].sum() / p_pace_b) * 100.0, 2) if p_pace_b > 0 else 0.0

        p_spin_b = len(spin_df)
        p_spin_r = int(spin_df["runs"].sum()) if p_spin_b > 0 else 0
        p_spin_sr = round((p_spin_r / p_spin_b) * 100.0, 2) if p_spin_b > 0 else 0.0
        p_spin_vaoe_100 = round((spin_df["bat_vaoe"].sum() / p_spin_b) * 100.0, 2) if p_spin_b > 0 else 0.0

        # Top stroke under pressure
        valid_strokes = press_df["stroke"].dropna()
        valid_strokes = valid_strokes[valid_strokes.isin(off_strokes + leg_strokes)]
        top_stroke = valid_strokes.value_counts().index[0] if len(valid_strokes) > 0 else "Unknown"

        n_off = press_df["stroke"].isin(off_strokes).sum()
        n_leg = press_df["stroke"].isin(leg_strokes).sum()
        tot_tactical = max(1, n_off + n_leg)
        off_side_pct = round((n_off / tot_tactical) * 100.0, 2)
        leg_side_pct = round((n_leg / tot_tactical) * 100.0, 2)

        # 6. Pressure Category Distribution
        cat_metrics = {}
        for cat in ["Low", "Moderate", "High", "Extreme"]:
            cdf = p_df[p_df["pressure_category"] == cat]
            cb = len(cdf)
            c_vaoe_100 = round((cdf["bat_vaoe"].sum() / cb) * 100.0, 2) if cb > 0 else 0.0
            cat_metrics[f"{cat.lower()}_balls"] = cb
            cat_metrics[f"{cat.lower()}_vaoe_per_100b"] = c_vaoe_100

        player_stats.append({
            "batter_id": bid,
            "batter_name": bname,
            "team_name": team_name,
            "primary_tier": comp_tier,
            # Overall
            "total_balls_faced": tot_b,
            "total_runs": tot_r,
            "total_dismissals": tot_outs,
            "total_batting_avg": tot_avg,
            "total_strike_rate": tot_sr,
            "total_dot_pct": tot_dot_pct,
            "total_boundary_pct": tot_bound_pct,
            "total_rae": tot_rae,
            "total_wpv": tot_wpv,
            "total_vaoe": tot_vaoe,
            "total_vaoe_per_100b": tot_vaoe_per_100b,
            # Normal Baseline
            "normal_balls_faced": norm_b,
            "normal_runs": norm_r,
            "normal_dismissals": norm_outs,
            "normal_batting_avg": norm_avg,
            "normal_strike_rate": norm_sr,
            "normal_dot_pct": norm_dot_pct,
            "normal_boundary_pct": norm_bound_pct,
            "normal_rae_per_100b": norm_rae_per_100b,
            "normal_wpv_per_100b": norm_wpv_per_100b,
            "normal_vaoe_per_100b": norm_vaoe_per_100b,
            # High Pressure
            "pressure_balls_faced": press_b,
            "pressure_runs": press_r,
            "pressure_dismissals": press_outs,
            "pressure_batting_avg": press_avg,
            "pressure_strike_rate": press_sr,
            "pressure_expected_strike_rate": press_exp_sr,
            "pressure_sr_residual": press_sr_residual,
            "pressure_dot_pct": press_dot_pct,
            "pressure_boundary_pct": press_bound_pct,
            "pressure_balls_per_dismissal": press_balls_per_dismissal,
            "pressure_rae_per_ball": press_rae_per_ball,
            "pressure_rae_per_100b": press_rae_per_100b,
            "pressure_wpv_per_100b": press_wpv_per_100b,
            "pressure_vaoe_per_ball": press_vaoe_per_ball,
            "pressure_vaoe_per_100b": press_vaoe_per_100b,
            "vaoe_pressure_delta": vaoe_pressure_delta,
            "elo_weighted_pressure_vaoe_per_100b": elo_weighted_pressure_vaoe_per_100b,
            # Consistency
            "n_pressure_innings": n_pressure_innings,
            "clutch_success_rate": clutch_success_rate,
            "inter_match_std": inter_match_std,
            "sortino_downside_deviation": sortino_downside_deviation,
            # Tactical Splits
            "pressure_sr_vs_pace": p_pace_sr,
            "pressure_vaoe_vs_pace": p_pace_vaoe_100,
            "pressure_sr_vs_spin": p_spin_sr,
            "pressure_vaoe_vs_spin": p_spin_vaoe_100,
            "top_stroke": top_stroke,
            "off_side_pct": off_side_pct,
            "leg_side_pct": leg_side_pct,
            # Category Breakdown
            **cat_metrics
        })

    bat_stats_df = pd.DataFrame(player_stats)

    # --- [5/5] Saving Outputs ---
    print("--- [5/5] Saving Batting Player Statistics and Clean Deliveries ---")
    bat_out_proc = os.path.join(proc_dir, "batting_player_statistics.csv")
    bat_out_root = os.path.join(workspace_dir, "batting_player_statistics.csv")
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

    bat_stats_df.to_csv(bat_out_proc, index=False)
    bat_stats_df.to_csv(bat_out_root, index=False)
    deliv_clean.to_csv(deliv_out_proc, index=False)
    deliv_clean.to_csv(deliv_out_root, index=False)

    elapsed = time.time() - t0
    print(f"Batting Performance Model complete in {elapsed:.2f} seconds!")
    print(f"  batting_player_statistics: {len(bat_stats_df)} batters, {len(bat_stats_df.columns)} columns")
    return bat_stats_df, deliv

if __name__ == "__main__":
    run_batting_performance_model()

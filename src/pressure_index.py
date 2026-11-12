"""
Phase 3 Pressure Index Research and Development Engine
Rajasthan Royals — SupeRR Selector Season 2

Implements and evaluates three candidate pre-delivery pressure models:
- Candidate Model A: Contextual Rule-Based Pressure Model
- Candidate Model B: Empirical Distribution / Percentile-Based Pressure Model
- Candidate Model C (Champion): State-Space Win-Probability Shannon Entropy & DTMC Leverage
Computes role-specific Batting Pressure Index and Bowling Pressure Index.
"""

import os
import time
import numpy as np
import pandas as pd
from scipy.stats import rankdata
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import KFold

def run_pressure_pipeline(workspace_dir=r"F:\SupeRR_Selector_Season_2"):
    t0 = time.time()
    proc_dir = os.path.join(workspace_dir, "Data", "processed")
    deliv_path = os.path.join(proc_dir, "clean_deliveries.csv")
    match_path = os.path.join(proc_dir, "match_context.csv")

    print("--- [1/6] Loading Clean Deliveries & Match Context ---")
    deliv = pd.read_csv(deliv_path, keep_default_na=False)
    matches = pd.read_csv(match_path, keep_default_na=False)

    deliv["match_id"] = deliv["match_id"].astype(str)
    matches["match_id"] = matches["match_id"].astype(str)
    match_meta = matches.set_index("match_id")

    # Map stage, knock_out, win_team_id
    deliv["stage"] = deliv["match_id"].map(match_meta["stage"]).fillna("League")
    deliv["knock_out"] = pd.to_numeric(deliv["match_id"].map(match_meta["knock_out"]), errors="coerce").fillna(0).astype(int)
    deliv["win_team_id"] = deliv["match_id"].map(match_meta["win_team_id"]).fillna("").astype(str)
    deliv["batting_team_id"] = deliv["batting_team_id"].astype(str)
    deliv["bowling_team_id"] = deliv["bowling_team_id"].astype(str)
    deliv["bat_team_won"] = (deliv["win_team_id"] == deliv["batting_team_id"]).astype(int)

    # Tournament stakes multiplier kappa
    kappa = np.ones(len(deliv))
    is_so = deliv["innings"].isin([3, 4])
    is_ko = (deliv["knock_out"] == 1) | deliv["stage"].isin(["Final", "Semi Final", "Qualifier", "Eliminator", "Super 4"])
    kappa[is_ko] = 1.25
    kappa[is_so] = 1.35
    deliv["kappa_stage"] = kappa

    # Elo diff
    home_map = match_meta["home_team_id"].astype(str).to_dict()
    home_elo = match_meta["home_pre_elo"].to_dict()
    away_elo = match_meta["away_pre_elo"].to_dict()

    elo_diffs = []
    for mid, btid, bowltid in zip(deliv["match_id"], deliv["batting_team_id"], deliv["bowling_team_id"]):
        hid = home_map.get(mid, "")
        b_elo = home_elo.get(mid, 1500.0) if btid == hid else away_elo.get(mid, 1500.0)
        bw_elo = away_elo.get(mid, 1500.0) if btid == hid else home_elo.get(mid, 1500.0)
        elo_diffs.append(b_elo - bw_elo)
    deliv["elo_diff"] = np.array(elo_diffs, dtype=float)

    # Cast numeric pre_* columns
    num_cols = ["pre_team_score", "pre_wickets_lost", "pre_wickets_in_hand", "pre_legal_balls_bowled",
                "pre_balls_remaining", "pre_partnership_runs", "pre_partnership_balls", "pre_consecutive_dots",
                "pre_striker_runs", "pre_striker_balls", "target_score", "pre_runs_needed", "pre_crr",
                "pre_rrr", "venue_avg_first_inn_score"]
    for c in num_cols:
        deliv[c] = pd.to_numeric(deliv[c], errors="coerce").fillna(0.0)

    # --- [2/6] Candidate Model A: Contextual Rule-Based Pressure ---
    print("--- [2/6] Computing Candidate Model A (Contextual Rule-Based) ---")
    p_model_a = np.zeros(len(deliv))

    inn1_mask = (deliv["innings"] == 1)
    inn1_idx = deliv[inn1_mask].index
    expected_wkts = deliv[inn1_mask].groupby("pre_legal_balls_bowled")["pre_wickets_lost"].mean().to_dict()

    w_exp = deliv.loc[inn1_idx, "pre_legal_balls_bowled"].map(expected_wkts).fillna(0.0).values
    w_act = deliv.loc[inn1_idx, "pre_wickets_lost"].values
    collapse_a = 1.0 - np.exp(- (np.maximum(0.0, w_act - w_exp) ** 2) / (2.0 * 1.25 ** 2))
    overid_1 = deliv.loc[inn1_idx, "overid"].values
    phase_a = (np.maximum(0.0, overid_1 - 14.0) / 6.0) ** 1.5
    par_rpo = deliv.loc[inn1_idx, "venue_avg_first_inn_score"].values / 20.0
    crr_1 = deliv.loc[inn1_idx, "pre_crr"].values
    par_def_a = np.clip((par_rpo - crr_1) / 3.0, 0.0, 1.0)
    dots_1 = deliv.loc[inn1_idx, "pre_consecutive_dots"].values
    dot_stress_a = 1.0 - np.exp(- (dots_1 ** 2) / 8.0)

    raw_a_1 = (0.40 * collapse_a + 0.30 * phase_a + 0.15 * par_def_a + 0.15 * dot_stress_a)
    p_model_a[inn1_idx] = 100.0 * np.clip(raw_a_1 * kappa[inn1_idx], 0.0, 1.0)

    inn2_mask = (deliv["innings"] == 2)
    inn2_idx = deliv[inn2_mask].index
    rrr_2 = deliv.loc[inn2_idx, "pre_rrr"].values
    g_rrr = np.exp(- ((rrr_2 - 11.5) ** 2) / (2.0 * 4.0 ** 2))
    w_hand_2 = deliv.loc[inn2_idx, "pre_wickets_in_hand"].values
    wkt_factor_a = 1.0 - (w_hand_2 / 10.0)
    balls_rem_2 = deliv.loc[inn2_idx, "pre_balls_remaining"].values
    ball_urgency_a = (120.0 - balls_rem_2) / 120.0

    dead_mask = (rrr_2 > 24.0) & (w_hand_2 <= 2)
    dead_chase_a = np.ones(len(inn2_idx))
    dead_chase_a[dead_mask] = np.clip(balls_rem_2[dead_mask] / 60.0, 0.05, 0.4)

    raw_a_2 = (0.45 * g_rrr + 0.30 * wkt_factor_a + 0.25 * ball_urgency_a) * dead_chase_a
    p_model_a[inn2_idx] = 100.0 * np.clip(raw_a_2 * kappa[inn2_idx], 0.0, 1.0)
    p_model_a[is_so] = 95.0 * kappa[is_so]
    deliv["pressure_model_a_rule"] = np.clip(p_model_a, 0.0, 100.0).round(2)

    # --- [3/6] Candidate Model B: Empirical Percentile-Based ---
    print("--- [3/6] Computing Candidate Model B (Percentile / ECDF) ---")
    p_model_b = np.zeros(len(deliv))
    for inn in [1, 2]:
        for phase in ["is_powerplay", "is_middle", "is_death"]:
            mask = (deliv["innings"] == inn) & (deliv[phase] == True)
            idx = deliv[mask].index
            if len(idx) == 0:
                continue
            if inn == 1:
                r1 = rankdata(deliv.loc[idx, "pre_wickets_lost"].values, method="average") / len(idx)
                r2 = rankdata(collapse_a[np.isin(inn1_idx, idx)], method="average") / len(idx)
                r3 = rankdata(dot_stress_a[np.isin(inn1_idx, idx)], method="average") / len(idx)
                score_b = (0.45 * r1 + 0.30 * r2 + 0.25 * r3)
            else:
                r1 = rankdata(g_rrr[np.isin(inn2_idx, idx)], method="average") / len(idx)
                r2 = rankdata(wkt_factor_a[np.isin(inn2_idx, idx)], method="average") / len(idx)
                r3 = rankdata(1.0 / np.maximum(1.0, balls_rem_2[np.isin(inn2_idx, idx)]), method="average") / len(idx)
                score_b = (0.50 * r1 + 0.30 * r2 + 0.20 * r3)
            p_model_b[idx] = 100.0 * np.clip(score_b * kappa[idx], 0.0, 1.0)

    p_model_b[is_so] = 95.0 * kappa[is_so]
    deliv["pressure_model_b_percentile"] = np.clip(p_model_b, 0.0, 100.0).round(2)

    # --- [4/6] Candidate Model C: State-Space Win-Probability Shannon Entropy & DTMC Leverage ---
    print("--- [4/6] Computing Champion Model C (Win Probability Shannon Entropy & DTMC Leverage) ---")
    # Innings 2 Win Probability Surface
    df2 = deliv[inn2_mask].copy()
    features_2 = ["pre_runs_needed", "pre_balls_remaining", "pre_wickets_in_hand", "pre_rrr", "venue_avg_first_inn_score", "elo_diff"]
    X2 = df2[features_2].values
    y2 = df2["bat_team_won"].values

    scaler_2 = StandardScaler()
    X2_scaled = scaler_2.fit_transform(X2)
    clf_2 = LogisticRegression(C=1.0, max_iter=500)
    clf_2.fit(X2_scaled, y2)
    w2 = clf_2.predict_proba(X2_scaled)[:, 1]

    # DTMC Leverage for Inn 2
    runs_bound = np.maximum(0.0, X2[:, 0] - 4.0)
    balls_bound = np.maximum(1.0, X2[:, 1] - 1.0)
    rrr_bound = runs_bound / (balls_bound / 6.0)
    X2_bound = np.column_stack([runs_bound, balls_bound, X2[:, 2], rrr_bound, X2[:, 4], X2[:, 5]])
    w2_bound = clf_2.predict_proba(scaler_2.transform(X2_bound))[:, 1]

    runs_wkt = X2[:, 0]
    balls_wkt = np.maximum(1.0, X2[:, 1] - 1.0)
    wkts_wkt = np.maximum(0.0, X2[:, 2] - 1.0)
    rrr_wkt = runs_wkt / (balls_wkt / 6.0)
    X2_wkt = np.column_stack([runs_wkt, balls_wkt, wkts_wkt, rrr_wkt, X2[:, 4], X2[:, 5]])
    w2_wkt = clf_2.predict_proba(scaler_2.transform(X2_wkt))[:, 1]

    lev_2 = np.abs(w2_bound - w2_wkt)
    lev_98_2 = np.percentile(lev_2, 98)
    norm_lev_2 = np.clip(lev_2 / max(1e-4, lev_98_2), 0.0, 1.0)

    w2_clip = np.clip(w2, 1e-6, 1.0 - 1e-6)
    H2 = - (w2_clip * np.log2(w2_clip) + (1.0 - w2_clip) * np.log2(1.0 - w2_clip))

    # Innings 1 Win Probability Surface
    df1 = deliv[inn1_mask].copy()
    features_1 = ["pre_team_score", "pre_wickets_lost", "pre_balls_remaining", "venue_avg_first_inn_score", "elo_diff"]
    X1 = df1[features_1].values
    y1 = df1["bat_team_won"].values

    scaler_1 = StandardScaler()
    X1_scaled = scaler_1.fit_transform(X1)
    clf_1 = LogisticRegression(C=1.0, max_iter=500)
    clf_1.fit(X1_scaled, y1)
    w1 = clf_1.predict_proba(X1_scaled)[:, 1]

    # DTMC Leverage for Inn 1
    score_bound1 = X1[:, 0] + 4.0
    balls_bound1 = np.maximum(1.0, X1[:, 2] - 1.0)
    X1_bound = np.column_stack([score_bound1, X1[:, 1], balls_bound1, X1[:, 3], X1[:, 4]])
    w1_bound = clf_1.predict_proba(scaler_1.transform(X1_bound))[:, 1]

    score_wkt1 = X1[:, 0]
    balls_wkt1 = np.maximum(1.0, X1[:, 2] - 1.0)
    wkts_wkt1 = np.minimum(10.0, X1[:, 1] + 1.0)
    X1_wkt = np.column_stack([score_wkt1, wkts_wkt1, balls_wkt1, X1[:, 3], X1[:, 4]])
    w1_wkt = clf_1.predict_proba(scaler_1.transform(X1_wkt))[:, 1]

    lev_1 = np.abs(w1_bound - w1_wkt)
    lev_98_1 = np.percentile(lev_1, 98)
    norm_lev_1 = np.clip(lev_1 / max(1e-4, lev_98_1), 0.0, 1.0)

    w1_clip = np.clip(w1, 1e-6, 1.0 - 1e-6)
    H1 = - (w1_clip * np.log2(w1_clip) + (1.0 - w1_clip) * np.log2(1.0 - w1_clip))

    # Composite Model C
    p_model_c = np.zeros(len(deliv))
    raw_c_1 = (0.35 * H1 + 0.25 * norm_lev_1 + 0.20 * collapse_a + 0.10 * phase_a + 0.10 * dot_stress_a)
    p_model_c[inn1_idx] = 100.0 * np.clip(raw_c_1 * kappa[inn1_idx], 0.0, 1.0)

    raw_c_2 = (0.45 * H2 + 0.35 * norm_lev_2 + 0.20 * g_rrr)
    p_model_c[inn2_idx] = 100.0 * np.clip(raw_c_2 * kappa[inn2_idx], 0.0, 1.0)
    p_model_c[is_so] = 98.0
    deliv["pressure_model_c_quantum_leverage"] = np.clip(p_model_c, 0.0, 100.0).round(2)

    # Primary Champion Pressure Index
    deliv["pressure_index"] = deliv["pressure_model_c_quantum_leverage"]

    # --- [5/6] Role-Specific Pressure & Stratified Categories ---
    print("--- [5/6] Computing Batting & Bowling Pressure Indices & Categories ---")
    dot_buildup_full = np.zeros(len(deliv))
    dot_buildup_full[inn1_idx] = dot_stress_a
    dot_buildup_full[inn2_idx] = 1.0 - np.exp(- (deliv.loc[inn2_idx, "pre_consecutive_dots"].values ** 2) / 8.0)

    collapse_full = np.zeros(len(deliv))
    collapse_full[inn1_idx] = collapse_a
    collapse_full[inn2_idx] = wkt_factor_a

    is_new_batter_mid_death = (deliv["pre_striker_balls"] <= 4) & (deliv["overid"] >= 11)
    deliv["batting_pressure_index"] = np.clip(
        deliv["pressure_index"] + 8.0 * dot_buildup_full + 6.0 * is_new_batter_mid_death.astype(int) + 5.0 * collapse_full,
        0.0, 100.0
    ).round(2)

    death_wickets_in_hand = (deliv["overid"] >= 16) & (deliv["pre_wickets_in_hand"] >= 5)
    set_batter_or_partner = (deliv["pre_striker_runs"] >= 30) | (deliv["pre_partnership_runs"] >= 50)
    deliv["bowling_pressure_index"] = np.clip(
        deliv["pressure_index"] + 6.0 * death_wickets_in_hand.astype(int) + 5.0 * set_batter_or_partner.astype(int),
        0.0, 100.0
    ).round(2)

    # Categories based on percentiles of pressure_index
    p40 = np.percentile(deliv["pressure_index"], 40)
    p70 = np.percentile(deliv["pressure_index"], 70)
    p90 = np.percentile(deliv["pressure_index"], 90)

    print(f"Calibrated Percentiles: P40 = {p40:.2f}, P70 = {p70:.2f}, P90 = {p90:.2f}")

    categories = np.empty(len(deliv), dtype=object)
    p_vals = deliv["pressure_index"].values

    categories[p_vals < p40] = "Low"
    categories[(p_vals >= p40) & (p_vals < p70)] = "Moderate"
    categories[(p_vals >= p70) & (p_vals < p90)] = "High"
    categories[p_vals >= p90] = "Extreme"
    # Ensure all Super Over deliveries are in Extreme
    categories[is_so] = "Extreme"
    deliv["pressure_category"] = categories

    deliv["is_high_pressure"] = deliv["pressure_index"] >= p70
    deliv["pressure_weight"] = ((deliv["pressure_index"] / 100.0) ** 2).round(4)

    # --- [6/6] Generating Pressure Distribution Table & Saving Deliverables ---
    print("--- [6/6] Generating pressure_distribution.csv & Updating Processed Datasets ---")
    dist_rows = []

    def compute_stratum_metrics(sub_df, stratum_name, category_val):
        n = len(sub_df)
        if n == 0:
            return None
        p = sub_df["pressure_index"]
        p25, p50, p75 = np.percentile(p, [25, 50, 75])
        legal_balls = sub_df["is_legal_ball"].sum()
        rpo = round(sub_df["team_runs_on_ball"].sum() / (legal_balls / 6.0), 2) if legal_balls > 0 else 0.0
        wkt_rate = round(sub_df["is_wicket"].mean() * 100.0, 2)
        dot_rate = round(((sub_df["runs"] == 0) & sub_df["is_batter_ball_faced"]).mean() * 100.0, 2)
        return {
            "stratum": stratum_name,
            "category": category_val,
            "deliveries": n,
            "pct_total": round(n / len(deliv) * 100.0, 2),
            "mean_pressure": round(p.mean(), 2),
            "median_pressure": round(p50, 2),
            "iqr_pressure": round(p75 - p25, 2),
            "rpo": rpo,
            "wicket_rate_pct": wkt_rate,
            "dot_pct": dot_rate
        }

    # Pressure Categories
    for cat in ["Low", "Moderate", "High", "Extreme"]:
        sub = deliv[deliv["pressure_category"] == cat]
        dist_rows.append(compute_stratum_metrics(sub, "Pressure Category", cat))

    # Innings
    dist_rows.append(compute_stratum_metrics(deliv[deliv["innings"] == 1], "Innings", "Innings 1"))
    dist_rows.append(compute_stratum_metrics(deliv[deliv["innings"] == 2], "Innings", "Innings 2"))
    dist_rows.append(compute_stratum_metrics(deliv[deliv["innings"].isin([3, 4])], "Innings", "Super Over"))

    # Phases
    for ph, label in [("is_powerplay", "Powerplay (Overs 1-6)"), ("is_middle", "Middle (Overs 7-15)"), ("is_death", "Death (Overs 16-20)")]:
        sub = deliv[deliv[ph] == True]
        dist_rows.append(compute_stratum_metrics(sub, "Match Phase", label))

    # Tiers
    for tier in ["Tier 1 (IPL)", "Tier 2 (T20I_FullMember)", "Tier 3 (T20_Associate_Emerging)"]:
        sub = deliv[deliv["comp_tier"] == tier]
        dist_rows.append(compute_stratum_metrics(sub, "Competition Tier", tier))

    pressure_dist_df = pd.DataFrame([r for r in dist_rows if r is not None])

    # Save outputs to Data/processed/ and root
    deliv_out_proc = os.path.join(proc_dir, "clean_deliveries.csv")
    dist_out_proc = os.path.join(proc_dir, "pressure_distribution.csv")
    deliv_out_root = os.path.join(workspace_dir, "clean_deliveries.csv")
    dist_out_root = os.path.join(workspace_dir, "pressure_distribution.csv")

    deliv.to_csv(deliv_out_proc, index=False)
    deliv.to_csv(deliv_out_root, index=False)
    pressure_dist_df.to_csv(dist_out_proc, index=False)
    pressure_dist_df.to_csv(dist_out_root, index=False)

    elapsed = time.time() - t0
    print(f"Phase 3 Pressure pipeline complete in {elapsed:.2f} seconds!")
    print(f"  clean_deliveries: {len(deliv)} rows, {len(deliv.columns)} columns")
    print(f"  pressure_distribution: {len(pressure_dist_df)} rows")
    return deliv, pressure_dist_df

if __name__ == "__main__":
    run_pressure_pipeline()

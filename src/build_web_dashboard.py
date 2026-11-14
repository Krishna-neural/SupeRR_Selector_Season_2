"""
Rajasthan Royals — SupeRR Selector Season 2
Web Dashboard Generator
Generates docs/index.html (GitHub Pages interactive dashboard) and app.py (Streamlit Cloud).
"""

import os
import json
import pandas as pd
import numpy as np

def build_dashboard(base_dir="."):
    print("--- [Web Dashboard 1/3] Loading Data ---")
    top_bat = pd.read_csv(os.path.join(base_dir, "top_10_batters.csv"))
    top_bowl = pd.read_csv(os.path.join(base_dir, "top_10_bowlers.csv"))
    all_bat = pd.read_csv(os.path.join(base_dir, "complete_batter_rankings.csv"))
    all_bowl = pd.read_csv(os.path.join(base_dir, "complete_bowler_rankings.csv"))
    stab = pd.read_csv(os.path.join(base_dir, "ranking_stability.csv"))

    # Qualified cohort (145 batters, 145 bowlers)
    all_bat_q = all_bat[all_bat["is_eligible_final"] == True].sort_values("rank_crr").copy()
    all_bowl_q = all_bowl[all_bowl["is_eligible_final"] == True].sort_values("rank_crr").copy()

    # Narratives from technical report
    bat_narratives = {
        1: {
            "tactical": "Lightning-fast hip rotation dispatches 145km/h back-of-length pace behind square at will.",
            "walkthrough": "96 off 48 balls vs GT (Match 50944, VAOE +54.4); 59 off 19 vs SRH (Match 50943, SR 310.5); 57 off 18 vs RCB (SR 316.7).",
            "verdict": "Generational teenage prodigy possessing the highest raw scoring ceiling under pressure in modern T20 cricket. Lock in as long-term RR opening cornerstone."
        },
        2: {
            "tactical": "Unrivaled 360-degree boundary access via late flick, lap scoop, and deep backward point ramp.",
            "walkthrough": "80 off 47 vs SRH (Match 31273, VAOE +33.1); 56 off 26 vs PBKS (Match 20225, SR 215.4); 57 off 30 vs AUS (Match 17396).",
            "verdict": "The gold-standard multi-season anchor. Highest LCB80 floor in world cricket (+22.43), proving his baseline floor beats others' ceilings."
        },
        3: {
            "tactical": "High clutch delta (+18.5) providing international run-chase anchor security and low dot rate.",
            "walkthrough": "80 off 45 vs PAK (Match 38796, VAOE +40.4); 83 off 48 vs WI (Match 19961, SR 172.9); 51 off 23 vs WI (Match 19960).",
            "verdict": "Remarkable clutch escalator who elevates strike rate by +28.7 points under tournament pressure. Prime realistic overseas target."
        },
        4: {
            "tactical": "Subcontinent anchor thriving under spin and variable bounce with sharp pull stroke.",
            "walkthrough": "82 off 48 vs IND (Match 45512, VAOE +50.3); 56 off 29 vs AFG (Match 29926, SR 193.1); 46 off 29 vs IND (Match 16661).",
            "verdict": "Prodigious clutch delta (+23.8) across 682 pressure balls. Heavy volume anchor offering perfect stability for Indian conditions."
        },
        5: {
            "tactical": "Explosive square cut and pull. High boundary percentage in Powerplay field restrictions.",
            "walkthrough": "71 off 38 vs MI CT (Match 38102, VAOE +38.2); 53 off 28 vs DSG (Match 38115); 48 off 24 vs PR (Match 38125).",
            "verdict": "Elite dual-role wicketkeeper-batter with an 81.3% clutch match success rate. Perfect dynamic target to unlock RR squad balance."
        },
        6: {
            "tactical": "Classical off-side strokeplay maintaining exceptional composure when required rate exceeds 11.0.",
            "walkthrough": "84 off 49 vs CSK (Match 31254, VAOE +32.5); 62 off 36 vs DC (Match 20212); 96 off 47 in IPL Final (Match 16064).",
            "verdict": "Highest clutch success rate in corpus (82.6%). Tactical accumulator who avoids dot balls without taking reckless dismissal risks."
        },
        7: {
            "tactical": "Slog sweep and pick-up pull thriving in extreme tournament pressure states.",
            "walkthrough": "79 off 43 vs BAN (Match 41102, VAOE +34.8); 54 off 31 vs AFG (Match 41115); 69 off 40 vs WI.",
            "verdict": "High-crucible specialist (+31.51 extreme VAOE) with proven big-match knockout pedigree across Asia Cups and World Cups."
        },
        8: {
            "tactical": "Destructive left-handed boundary hitter who attacks express pace relentlessly in Powerplay.",
            "walkthrough": "68 off 34 vs KKR (Match 20245, VAOE +36.4); 77 off 47 vs MI (Match 31289); 50 off 26 vs AUS (Match 17398).",
            "verdict": "Current RR franchise core. Pair with Sooryavanshi for a generational, fear-free opening pair dominating pace bowling."
        },
        9: {
            "tactical": "Metronomic chase master pacing run chases with pristine running between wickets.",
            "walkthrough": "82* off 53 vs PAK (Match 16789, VAOE +48.6); 76 off 59 in World Cup Final vs SA (Match 44102); 70* off 44 vs GT.",
            "verdict": "The historical benchmark for international chase execution. Solid LCB80 certainty floor (+13.15) validating model calibration."
        },
        10: {
            "tactical": "Master of collapse mitigation and resource preservation in early wickets down states.",
            "walkthrough": "71* off 51 vs NZ (Match 29112, VAOE +28.9); 68 off 46 vs ENG (Match 29134); 55 off 38 vs SA.",
            "verdict": "High-floor anchor delivering +27.91 extreme crucible VAOE. Preserves team equity in severe collapse situations."
        }
    }

    bowl_narratives = {
        1: {
            "tactical": "Express pace weapon generating high-leverage mis-timed top edges under pressure.",
            "walkthrough": "4/28 vs GT (Match 20234, VAOE +9.8); 3/19 vs AFG (Match 44110, VAOE +8.4); 3/21 vs AUS (Match 16682).",
            "verdict": "#1 Bowling Auction Priority: Available enforcer providing extreme 150+ km/h pace (+13.7 extreme VAOE), perfectly solving RR death wicket needs."
        },
        2: {
            "tactical": "Lethal high-velocity strike weapon capable of blowing games open in 2-over bursts.",
            "walkthrough": "5/25 vs GT (Match 16045, VAOE +12.4); 3/23 vs PBKS (Match 16068, VAOE +8.1); 3/28 vs KKR.",
            "verdict": "High-upside domestic pacer (+7.04 shrunk VAOE) to groom under RR bowling coaching as an impact wicket-taker."
        },
        3: {
            "tactical": "Premier Powerplay containment off-spinner, pristine for large subcontinental grounds.",
            "walkthrough": "3/16 vs AUS (Match 16678, VAOE +8.9); 2/12 vs NZ (Match 29145, VAOE +7.4); 2/18 vs IND.",
            "verdict": "Powerplay Value Pick: Concedes just 6.76 RPO under pressure (45.3% dot balls), offering pristine control at Sawai Mansingh Stadium."
        },
        4: {
            "tactical": "Elite opening strike enforcer whose early breakthrough value flips match win probabilities.",
            "walkthrough": "3/31 vs IND (Match 16789, VAOE +7.8); 4/22 vs BAN (Match 38812, VAOE +8.5); 3/19 vs SA.",
            "verdict": "World-class opening bowler whose early dismissal hazard forces opponents into defensive shells."
        },
        5: {
            "tactical": "Quintessential death specialist utilizing deceptive changes of pace.",
            "walkthrough": "4/30 vs RR (Match 20215, VAOE +6.9); 3/24 vs ENG (Match 38825, VAOE +5.8); 3/17 vs WI.",
            "verdict": "Death Specialist Buy: Dipping yorkers & slower balls (40.8% death share), perfectly pairs with Trent Boult."
        },
        6: {
            "tactical": "Round-arm slinger delivering unplayable yorkers in the final 4 overs.",
            "walkthrough": "3/15 vs MI (Match 31267, VAOE +7.1); 4/28 vs GT (Match 31288, VAOE +6.8); 3/22 vs DC.",
            "verdict": "Unplayable death weapon with 52.1% death pressure share and 15.8% yorker execution."
        },
        7: {
            "tactical": "High-discipline defensive spinner choking middle overs scoring opportunities.",
            "walkthrough": "3/18 vs SRH (Match 20202, VAOE +6.2); 2/11 vs DC (Match 31241, VAOE +5.5); 2/16 vs PBKS.",
            "verdict": "Middle-overs defensive anchor conceding only 6.74 RPO under tournament pressure."
        },
        8: {
            "tactical": "Metronomic test-match length discipline transplanted seamlessly to T20.",
            "walkthrough": "4/25 vs LSG (Match 16012, VAOE +7.4); 3/16 vs WI (Match 16690, VAOE +6.1); 2/19 vs ENG.",
            "verdict": "Elite length discipline (+4.58 shrunk VAOE) to squeeze opposing middle orders."
        },
        9: {
            "tactical": "Heavy-volume spin anchor who consistently restricts run flow across all phases.",
            "walkthrough": "2/24 vs CSK (Match 31215, VAOE +5.1); 3/23 vs ENG (Match 44115, VAOE +6.8); 2/17 vs MI.",
            "verdict": "Versatile spin anchor maintaining a 43.3% dot-ball share across 746 high-pressure balls."
        },
        10: {
            "tactical": "Tactical matchup specialist offering exceptional control on turning wickets.",
            "walkthrough": "3/15 vs SRH (Match 16035, VAOE +6.5); 2/18 vs AUS (Match 16695, VAOE +5.4); 2/14 vs BAN.",
            "verdict": "Tactical Matchup Specialist: Concedes only 7.09 RPO under pressure (+6.1 extreme VAOE), ideal for Jaipur tracks."
        }
    }

    # Prepare Top Batters JSON
    top_bat_list = []
    for _, r in top_bat.iterrows():
        rk = int(r["rank"])
        nar = bat_narratives[rk]
        top_bat_list.append({
            "rank": rk,
            "id": int(r["player_id"]),
            "name": str(r["player_name"]),
            "teams": str(r["teams_represented"]),
            "role": str(r["primary_role"]),
            "tier": str(r["primary_comp_tier"]),
            "balls": int(r["pressure_balls"]),
            "neff": round(float(r["effective_sample_size"]), 1),
            "sr": round(float(r["pressure_sr"]), 2),
            "exp_sr": round(float(r["expected_pressure_sr"]), 2),
            "sr_res": round(float(r["pressure_sr_residual"]), 2),
            "vaoe": round(float(r["shrunk_pressure_vaoe"]), 2),
            "lcb": round(float(r["lcb_80_floor"]), 2),
            "ext": round(float(r["extreme_crucible_vaoe"]), 1),
            "delta": round(float(r["shrunk_pressure_delta"]), 2),
            "win_pct": round(float(r["clutch_success_rate"]), 1),
            "ci_low": round(float(r["bootstrap_ci_95_low"]), 2),
            "ci_high": round(float(r["bootstrap_ci_95_high"]), 2),
            "crr": round(float(r["final_crr_score_100"]), 2),
            "pace_spin": str(r["pace_vs_spin_vaoe"]),
            "stroke": str(r["top_scoring_strokes"]),
            "tactical": nar["tactical"],
            "walkthrough": nar["walkthrough"],
            "verdict": nar["verdict"]
        })

    # Prepare Top Bowlers JSON
    top_bowl_list = []
    for _, r in top_bowl.iterrows():
        rk = int(r["rank"])
        nar = bowl_narratives[rk]
        top_bowl_list.append({
            "rank": rk,
            "id": int(r["player_id"]),
            "name": str(r["player_name"]),
            "teams": str(r["teams_represented"]),
            "discipline": str(r["bowling_style"]),
            "role": f"{r['bowling_style']} {r['primary_role']}",
            "tier": str(r["primary_comp_tier"]),
            "balls": int(r["pressure_legal_balls"]),
            "neff": round(float(r["effective_sample_size"]), 1),
            "econ": round(float(r["pressure_economy"]), 2),
            "exp_econ": round(float(r["expected_pressure_economy"]), 2),
            "econ_saved": round(float(r["pressure_econ_saved"]), 2),
            "vaoe": round(float(r["shrunk_pressure_vaoe"]), 2),
            "lcb": round(float(r["lcb_80_floor"]), 2),
            "ext": round(float(r["extreme_crucible_vaoe"]), 1),
            "delta": round(float(r["shrunk_pressure_delta"]), 2),
            "death_pct": round(float(r["death_pressure_balls_pct"]), 1),
            "dot_pct": round(float(r["pressure_dot_pct"]), 1),
            "ci_low": round(float(r["bootstrap_ci_95_low"]), 2),
            "ci_high": round(float(r["bootstrap_ci_95_high"]), 2),
            "crr": round(float(r["final_crr_score_100"]), 2),
            "speed": round(float(r["mean_bowl_speed"]), 1),
            "yorker": round(float(r["yorker_pct"]), 1),
            "bouncer": round(float(r["bouncer_pct"]), 1),
            "slower": round(float(r["slower_ball_pct"]), 1),
            "tactical": nar["tactical"],
            "walkthrough": nar["walkthrough"],
            "verdict": nar["verdict"]
        })

    # Prepare All 145 Batters JSON
    all_bat_list = []
    for _, r in all_bat_q.iterrows():
        all_bat_list.append({
            "rank": int(r["rank_crr"]),
            "id": int(r["player_id"]),
            "name": str(r["player_name"]),
            "teams": str(r["teams_represented"]) if pd.notna(r["teams_represented"]) else "N/A",
            "role": str(r["primary_role"]),
            "tier": str(r["primary_comp_tier"]),
            "balls": int(r["pressure_balls"]),
            "sr": round(float(r["pressure_strike_rate"]), 1) if pd.notna(r["pressure_strike_rate"]) else 0.0,
            "vaoe": round(float(r["shrunk_pressure_vaoe"]), 2),
            "lcb": round(float(r["lcb_80"]), 2),
            "ext": round(float(r["shrunk_ext_vaoe_per_100b"]), 1),
            "delta": round(float(r["shrunk_pressure_delta"]), 2),
            "win_pct": round(float(r["clutch_success_rate"]), 1),
            "crr": round(float(r["final_crr_score_100"]), 2)
        })

    # Prepare All 145 Bowlers JSON
    all_bowl_list = []
    for _, r in all_bowl_q.iterrows():
        all_bowl_list.append({
            "rank": int(r["rank_crr"]),
            "id": int(r["player_id"]),
            "name": str(r["player_name"]),
            "teams": str(r["teams_represented"]) if pd.notna(r["teams_represented"]) else "N/A",
            "discipline": str(r["pace_or_spin"]),
            "role": str(r["primary_role"]),
            "tier": str(r["primary_comp_tier"]),
            "balls": int(r["pressure_balls"]),
            "econ": round(float(r["pressure_economy"]), 2) if pd.notna(r["pressure_economy"]) else 0.0,
            "vaoe": round(float(r["shrunk_pressure_vaoe"]), 2),
            "lcb": round(float(r["lcb_80"]), 2),
            "ext": round(float(r["shrunk_ext_vaoe_per_24b"]), 1),
            "delta": round(float(r["shrunk_pressure_delta"]), 2),
            "death_pct": round(float(r["death_pressure_balls_pct"]), 1),
            "dot_pct": round(float(r["pressure_dot_pct"]), 1),
            "crr": round(float(r["final_crr_score_100"]), 2)
        })

    # Prepare RR Auction Target Matrix JSON (16 players)
    auction_list = [
        {"bucket": "Bucket 1 — Current RR Core Validated by Model", "name": "Vaibhav Sooryavanshi", "rank": "#1 Batter", "crr": 100.00, "role": "Top-Order LH Batter", "action": "Franchise Cornerstone", "rationale": "Crowned #1 clutch batter in world cricket (+42.5 extreme VAOE). Lock in as long-term opening asset alongside Jaiswal."},
        {"bucket": "Bucket 1 — Current RR Core Validated by Model", "name": "Yashasvi Jaiswal", "rank": "#8 Batter", "crr": 90.49, "role": "Top-Order LH Batter", "action": "Core Powerhouse", "rationale": "Elite pace destructor (+21.2 shrunk VAOE). Pairs with Sooryavanshi for an ultra-aggressive, high-pressure opening pair."},
        {"bucket": "Bucket 2 — Franchise-Locked Benchmarks", "name": "Suryakumar Yadav", "rank": "#2 Batter", "crr": 99.20, "role": "Middle-Order RH Batter", "action": "Model Calibration Proof", "rationale": "Unattainable franchise lock (MI); acts as gold-standard benchmark proving model accurately flags elite 360-degree clutch performance."},
        {"bucket": "Bucket 2 — Franchise-Locked Benchmarks", "name": "Virat Kohli", "rank": "#9 Batter", "crr": 90.16, "role": "Top-Order RH Batter", "action": "Anchor Benchmark", "rationale": "Validates model's recognition of historical chase mastery and unshakeable LCB80 (+13.2) floor (RCB)."},
        {"bucket": "Bucket 2 — Franchise-Locked Benchmarks", "name": "Jasprit Bumrah", "rank": "#11 Bowler", "crr": 77.80, "role": "Right-Arm Fast", "action": "Respect-Penalty Calibration", "rationale": "Proves model accurately captures batter risk-aversion (48.2% dots) without distorting wicket expectation (MI)."},
        {"bucket": "Bucket 2 — Franchise-Locked Benchmarks", "name": "Rashid Khan", "rank": "#12 Bowler", "crr": 77.40, "role": "Right-Arm Leg-Spin", "action": "Middle-Overs Benchmark", "rationale": "Calibrates defensive containment vs wicket-taking trade-offs in clutch situations (GT)."},
        {"bucket": "Bucket 3 — High-Priority Realistic RR Auction Targets", "name": "Lockie Ferguson", "rank": "#1 Bowler", "crr": 100.00, "role": "Right-Arm Express Pace", "action": "#1 Bowling Auction Priority", "rationale": "Available express pace weapon (+13.7 extreme VAOE), perfectly solving RR's death-overs wicket-taking requirement."},
        {"bucket": "Bucket 3 — High-Priority Realistic RR Auction Targets", "name": "Umran Malik", "rank": "#2 Bowler", "crr": 97.22, "role": "Right-Arm Express Pace", "action": "High-Upside Domestic Pacer", "rationale": "High-velocity strike weapon (+7.04 shrunk VAOE) to groom under RR bowling coaching as an impact wicket-taker."},
        {"bucket": "Bucket 3 — High-Priority Realistic RR Auction Targets", "name": "Mahedi Hasan", "rank": "#3 Bowler", "crr": 89.34, "role": "Right-Arm Off-Spin", "action": "Powerplay Value Pick", "rationale": "Concedes just 6.76 RPO under pressure (45.3% dot balls), offering pristine control at Sawai Mansingh Stadium's large boundaries."},
        {"bucket": "Bucket 3 — High-Priority Realistic RR Auction Targets", "name": "Reeza Hendricks", "rank": "#3 Batter", "crr": 97.72, "role": "Top-Order RH Batter", "action": "Overseas Anchor Option", "rationale": "Under-the-radar international anchor (+18.5 clutch delta) offering budget-friendly stability in tense run chases."},
        {"bucket": "Bucket 3 — High-Priority Realistic RR Auction Targets", "name": "Pathum Nissanka", "rank": "#4 Batter", "crr": 96.51, "role": "Top-Order RH Batter", "action": "High-Volume Subcontinent Target", "rationale": "Prodigious clutch differential (+23.8), exceptionally suited to Indian spin and variable bounce."},
        {"bucket": "Bucket 3 — High-Priority Realistic RR Auction Targets", "name": "Ryan Rickelton", "rank": "#5 Batter", "crr": 96.25, "role": "Wicketkeeper / LH Batter", "action": "Dynamic WK-Batter Target", "rationale": "81.3% clutch success rate, provides dual-role squad flexibility and middle-overs acceleration."},
        {"bucket": "Bucket 3 — High-Priority Realistic RR Auction Targets", "name": "Nathan Ellis", "rank": "#5 Bowler", "crr": 83.92, "role": "Right-Arm Fast-Medium", "action": "Death Specialist Buy", "rationale": "Dipping yorkers and deceptive changes of pace (40.8% death overs) to complement Trent Boult's opening bursts."},
        {"bucket": "Bucket 3 — High-Priority Realistic RR Auction Targets", "name": "Kusal Mendis", "rank": "#7 Batter", "crr": 90.62, "role": "Wicketkeeper / RH Batter", "action": "Knockout Tournament Performer", "rationale": "Extreme crucible performer (+31.5) with proven high-stakes subcontinent tournament pedigree."},
        {"bucket": "Bucket 3 — High-Priority Realistic RR Auction Targets", "name": "Josh Hazlewood", "rank": "#8 Bowler", "crr": 78.95, "role": "Right-Arm Fast-Medium", "action": "Metronomic Anchor Pacer", "rationale": "Elite test-match length discipline (+4.58 shrunk VAOE) to squeeze opposing middle orders."},
        {"bucket": "Bucket 3 — High-Priority Realistic RR Auction Targets", "name": "Mitchell Santner", "rank": "#10 Bowler", "crr": 78.04, "role": "Slow Left-Arm Orthodox", "action": "Tactical Matchup Specialist", "rationale": "Concedes only 7.09 RPO under pressure (+6.1 extreme VAOE), ideal for turning tracks in Jaipur."}
    ]

    # Clutch quadrant dataset for Plotly (top 10 batters and top 10 bowlers)
    quadrant_data = []
    for r in top_bat_list:
        quadrant_data.append({
            "name": r["name"],
            "rank": f"#{r['rank']} Batter",
            "type": "Batter",
            "baseline": round(float(top_bat.loc[top_bat["player_id"] == r["id"], "normal_vaoe_per_100b"].values[0]), 2),
            "pressure": r["vaoe"],
            "delta": r["delta"],
            "crr": r["crr"]
        })
    for r in top_bowl_list:
        quadrant_data.append({
            "name": r["name"],
            "rank": f"#{r['rank']} Bowler",
            "type": "Bowler",
            "baseline": round(float(top_bowl.loc[top_bowl["player_id"] == r["id"], "normal_vaoe_per_24b"].values[0]), 2),
            "pressure": r["vaoe"],
            "delta": r["delta"],
            "crr": r["crr"]
        })

    # Prepare figure metadata
    figures_list = [
        {"id": "fig1", "title": "Figure 1: Pre-Delivery Pressure Surface & Shannon Entropy", "file": "charts/fig1_pressure_surface_and_entropy.png", "desc": "Pre-Delivery Pressure Model C surfaces across Innings 2 Shannon Entropy and Innings 1 Collapse Escalation, demonstrating asymptotic dead-chase attenuation."},
        {"id": "fig2", "title": "Figure 2: Over Scoring Hazard & Dynamic Wicket Cost λ_wkt", "file": "charts/fig2_over_hazard_and_wicket_cost.png", "desc": "Over-by-over scoring rate (RPO), dismissal hazard rate (%), and dynamic wicket cost λ_wkt transitioning from 24.0 runs in Powerplay to 4.0 runs at the death."},
        {"id": "fig3", "title": "Figure 3: Multicollinearity vs Orthogonal VAOE Decompositions", "file": "charts/fig3_collinearity_and_orthogonality.png", "desc": "Pearson correlation heatmaps proving zero double-counting: raw counting metrics exhibit r > 0.85 collinearity, whereas decomposed VAOE residuals are cleanly orthogonal (r = +0.126, r = -0.117)."},
        {"id": "fig4", "title": "Figure 4: Hierarchical Empirical Bayes Shrinkage Funnel", "file": "charts/fig4_empirical_bayes_shrinkage_funnel.png", "desc": "Empirical Bayes shrinkage trajectories (K_bat = 200.0, K_bowl = 234.3) pulling extreme small-sample noise flukes toward the prior while preserving elite signals for anchors."},
        {"id": "fig5", "title": "Figure 5: Top 10 Batters Under Pressure Evidence Dashboard", "file": "charts/fig5_top10_batters_evidence_dashboard.png", "desc": "Composite CRR Championship ratings, Bayesian credible intervals, and risk-averse certainty floors (LCB_80) for the official Top 10 Batters."},
        {"id": "fig6", "title": "Figure 6: Top 10 Bowlers Under Pressure Evidence Dashboard", "file": "charts/fig6_top10_bowlers_evidence_dashboard.png", "desc": "Composite CRR Championship ratings, Bayesian credible intervals, and death overs share for the official Top 10 Bowlers."},
        {"id": "fig7", "title": "Figure 7: 2D Clutch Elevation Quadrant Analysis", "file": "charts/fig7_pressure_vs_baseline_quadrant.png", "desc": "2D Clutch Quadrant scatter plot classifying players into True Clutch Escalators, All-Weather Superstars, Baseline Accumulators, and Strugglers."},
        {"id": "fig8", "title": "Figure 8: 8-Experiment Robustness & Weight Sensitivity Suite", "file": "charts/fig8_robustness_and_weight_sensitivity.png", "desc": "500-Iteration Weight Perturbation Monte Carlo rank distributions and threshold invariance sweeps (P65 to P80) proving zero rank brittleness."}
    ]

    print("--- [Web Dashboard 2/3] Generating docs/index.html ---")
    os.makedirs(os.path.join(base_dir, "docs"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "docs", "charts"), exist_ok=True)

    json_top_bat = json.dumps(top_bat_list)
    json_top_bowl = json.dumps(top_bowl_list)
    json_all_bat = json.dumps(all_bat_list)
    json_all_bowl = json.dumps(all_bowl_list)
    json_auction = json.dumps(auction_list)
    json_quadrant = json.dumps(quadrant_data)
    json_figures = json.dumps(figures_list)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rajasthan Royals — SupeRR Selector Season 2 | Pressure Analytics Hub</title>
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Plotly.js -->
    <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Cabinet+Grotesk:wght@700;800;900&family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
    <script>
        tailwind.config = {{
            theme: {{
                extend: {{
                    colors: {{
                        'rr-blue': '#004B87',
                        'rr-dark': '#001E38',
                        'rr-pink': '#EA1B75',
                        'rr-pink-hover': '#D01464',
                        'rr-gold': '#D4AF37',
                        'rr-slate': '#0F172A',
                        'rr-card': '#1E293B',
                        'rr-card-border': '#334155'
                    }},
                    fontFamily: {{
                        'display': ['"Cabinet Grotesk"', 'sans-serif'],
                        'sans': ['Inter', 'sans-serif'],
                        'mono': ['"JetBrains Mono"', 'monospace']
                    }}
                }}
            }}
        }}
    </script>
    <style>
        body {{
            background-color: #0A0F1D;
            color: #F8FAFC;
            font-family: 'Inter', sans-serif;
        }}
        .hero-glow {{
            background: radial-gradient(circle at 50% 20%, rgba(234, 27, 117, 0.15) 0%, rgba(0, 75, 135, 0.25) 45%, rgba(10, 15, 29, 0) 75%);
        }}
        .glass-panel {{
            background: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(51, 65, 85, 0.8);
        }}
        .glass-panel-gold {{
            background: rgba(30, 41, 59, 0.85);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(212, 175, 55, 0.4);
        }}
        .tab-btn.active {{
            background: linear-gradient(135deg, #004B87 0%, #EA1B75 100%);
            color: #FFFFFF;
            font-weight: 700;
            box-shadow: 0 4px 14px rgba(234, 27, 117, 0.35);
        }}
        /* Custom scrollbar */
        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}
        ::-webkit-scrollbar-track {{
            background: #0F172A;
        }}
        ::-webkit-scrollbar-thumb {{
            background: #334155;
            border-radius: 4px;
        }}
        ::-webkit-scrollbar-thumb:hover {{
            background: #EA1B75;
        }}
    </style>
</head>
<body class="min-h-screen flex flex-col antialiased">

    <!-- TOP ANNOUNCEMENT BANNER -->
    <div class="bg-gradient-to-r from-rr-blue via-rr-pink to-rr-gold text-white text-xs font-semibold py-1.5 px-4 text-center tracking-wide uppercase shadow-md flex items-center justify-center space-x-3">
        <span class="inline-block w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
        <span>Rajasthan Royals — SupeRR Selector Season 2 • Official Quantitative Submission Platform</span>
        <span class="hidden md:inline text-white/80">• 100% Production Validated (70/70 Tests Passed)</span>
    </div>

    <!-- MAIN NAVBAR -->
    <header class="border-b border-rr-card-border bg-rr-slate/90 sticky top-0 z-50 backdrop-blur-md">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <div class="flex items-center space-x-3">
                <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-rr-pink to-rr-blue flex items-center justify-center text-white font-black text-xl shadow-lg border border-white/20 font-display">
                    RR
                </div>
                <div>
                    <h1 class="font-display font-extrabold text-lg text-white leading-tight tracking-tight">SupeRR Selector Season 2</h1>
                    <p class="text-[11px] text-gray-400 font-mono">Identifying The Most Reliable Players Under Pressure</p>
                </div>
            </div>

            <!-- Header Actions -->
            <div class="flex items-center space-x-3">
                <a href="https://github.com/Krishna-neural/SupeRR_Selector_Season_2" target="_blank" class="px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-800/80 hover:bg-slate-700 text-xs font-semibold text-gray-200 transition flex items-center space-x-1.5">
                    <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path fill-rule="evenodd" clip-rule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"></path></svg>
                    <span>GitHub Repo</span>
                </a>
                <a href="https://github.com/Krishna-neural/SupeRR_Selector_Season_2/raw/main/SupeRR_Selector_Season2_Methodology_Report.pdf" target="_blank" class="px-3.5 py-1.5 rounded-lg bg-rr-pink hover:bg-rr-pink-hover text-xs font-bold text-white shadow-md shadow-rr-pink/30 transition flex items-center space-x-1.5">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                    <span>Download PDF Whitepaper (22 Pages)</span>
                </a>
            </div>
        </div>
    </header>

    <!-- HERO SECTION -->
    <div class="relative hero-glow pt-8 pb-6 border-b border-rr-card-border">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="text-center max-w-4xl mx-auto">
                <div class="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-rr-card border border-rr-gold/40 text-rr-gold text-xs font-semibold mb-4">
                    <span>👑</span>
                    <span>Rajasthan Royals Quantitative Recruitment Whitepaper</span>
                </div>
                <h2 class="text-3xl sm:text-4xl md:text-5xl font-black font-display tracking-tight text-white mb-3">
                    Clutch Reliability Rating (<span class="text-transparent bg-clip-text bg-gradient-to-r from-rr-pink via-pink-400 to-rr-gold">CRR</span>) Engine
                </h2>
                <p class="text-sm sm:text-base text-gray-300 max-w-3xl mx-auto leading-relaxed mb-6 font-normal">
                    Objective, context-adjusted player evaluation under high pressure. Powered by <span class="text-white font-semibold">Unified Contextual Match Hazard (Model C)</span>, decomposed <span class="text-white font-semibold">Value-Added Over Expected (VAOE)</span> residuals, and <span class="text-white font-semibold">Hierarchical Empirical Bayes Shrinkage</span>.
                </p>

                <!-- Forensic Metrics Row -->
                <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 max-w-3xl mx-auto text-left font-mono">
                    <div class="glass-panel p-3 rounded-xl border border-slate-700/80">
                        <div class="text-[11px] text-gray-400 uppercase tracking-wider font-sans">Corpus Scale</div>
                        <div class="text-lg font-bold text-white mt-0.5 font-mono">883 Matches</div>
                        <div class="text-[10px] text-gray-500 font-sans">200,999 Deliveries (2022–26)</div>
                    </div>
                    <div class="glass-panel p-3 rounded-xl border border-slate-700/80">
                        <div class="text-[11px] text-gray-400 uppercase tracking-wider font-sans">Anti-Leakage</div>
                        <div class="text-lg font-bold text-green-400 mt-0.5 font-mono">100% Pre-Ball</div>
                        <div class="text-[10px] text-gray-500 font-sans">Strict state-space invariance</div>
                    </div>
                    <div class="glass-panel p-3 rounded-xl border border-slate-700/80">
                        <div class="text-[11px] text-gray-400 uppercase tracking-wider font-sans">Bayesian Shrinkage</div>
                        <div class="text-lg font-bold text-rr-gold mt-0.5 font-mono">K=200 / 234</div>
                        <div class="text-[10px] text-gray-500 font-sans">Defense against outlier flukes</div>
                    </div>
                    <div class="glass-panel p-3 rounded-xl border border-slate-700/80">
                        <div class="text-[11px] text-gray-400 uppercase tracking-wider font-sans">Automated QA</div>
                        <div class="text-lg font-bold text-blue-400 mt-0.5 font-mono">70 / 70 Tests</div>
                        <div class="text-[10px] text-gray-500 font-sans">100% Passing Pytest Suite</div>
                    </div>
                </div>
            </div>

            <!-- NAVIGATION TABS -->
            <div class="flex items-center justify-center space-x-2 sm:space-x-4 mt-8 max-w-4xl mx-auto border-b border-slate-800 pb-2">
                <button onclick="switchTab('tab-top10')" id="btn-tab-top10" class="tab-btn active px-4 py-2 rounded-xl text-xs sm:text-sm transition flex items-center space-x-2">
                    <span>🏆</span>
                    <span>Official Top-10 Rosters</span>
                </button>
                <button onclick="switchTab('tab-explorer')" id="btn-tab-explorer" class="tab-btn px-4 py-2 rounded-xl text-xs sm:text-sm text-gray-300 hover:text-white hover:bg-slate-800 transition flex items-center space-x-2">
                    <span>🔍</span>
                    <span>Player Scouting Explorer</span>
                </button>
                <button onclick="switchTab('tab-auction')" id="btn-tab-auction" class="tab-btn px-4 py-2 rounded-xl text-xs sm:text-sm text-gray-300 hover:text-white hover:bg-slate-800 transition flex items-center space-x-2">
                    <span>🎯</span>
                    <span>RR Tactical Auction Matrix</span>
                </button>
                <button onclick="switchTab('tab-evidence')" id="btn-tab-evidence" class="tab-btn px-4 py-2 rounded-xl text-xs sm:text-sm text-gray-300 hover:text-white hover:bg-slate-800 transition flex items-center space-x-2">
                    <span>📈</span>
                    <span>Evidence & Quadrant Gallery</span>
                </button>
            </div>
        </div>
    </div>

    <!-- MAIN BODY CONTENT -->
    <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">

        <!-- ========================================================= -->
        <!-- TAB 1: OFFICIAL TOP 10 LEADERBOARDS & DOSSIERS -->
        <!-- ========================================================= -->
        <section id="tab-top10" class="tab-content block">
            <div class="flex flex-col sm:flex-row items-center justify-between pb-6 border-b border-slate-800 gap-4">
                <div>
                    <h3 class="text-2xl font-black font-display text-white">Official Top-10 Pressure Leaderboards</h3>
                    <p class="text-xs text-gray-400">Locked dropdown selections for the Unstop competition submission portal.</p>
                </div>
                <!-- Discipline Toggle Switch -->
                <div class="inline-flex rounded-xl p-1 bg-slate-900 border border-slate-700">
                    <button id="toggle-batters-btn" onclick="setDiscipline('batters')" class="px-4 py-1.5 rounded-lg text-xs font-bold transition bg-rr-blue text-white shadow">
                        🏏 Top 10 Batters
                    </button>
                    <button id="toggle-bowlers-btn" onclick="setDiscipline('bowlers')" class="px-4 py-1.5 rounded-lg text-xs font-bold transition text-gray-400 hover:text-white">
                        🎯 Top 10 Bowlers
                    </button>
                </div>
            </div>

            <!-- Master Interactive Table (13 Columns) -->
            <div class="mt-6 glass-panel rounded-2xl overflow-hidden border border-slate-800 shadow-xl">
                <div class="overflow-x-auto">
                    <table class="w-full text-left text-xs font-mono">
                        <thead id="top10-thead" class="bg-rr-slate text-gray-300 uppercase tracking-wider text-[11px] font-sans border-b border-slate-700">
                            <!-- Populated dynamically -->
                        </thead>
                        <tbody id="top10-tbody" class="divide-y divide-slate-800/60 text-gray-200">
                            <!-- Populated dynamically -->
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Player Dossiers Cards Header -->
            <div class="mt-12 mb-6 flex items-center justify-between">
                <div>
                    <h4 class="text-xl font-black font-display text-white" id="dossiers-heading">Top 10 Batters Detailed Scouting Dossiers</h4>
                    <p class="text-xs text-gray-400">Comprehensive statistical, biomechanical, and match walkthrough dossiers.</p>
                </div>
            </div>

            <!-- Player Dossiers Cards Grid -->
            <div id="dossiers-grid" class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <!-- Populated dynamically -->
            </div>
        </section>

        <!-- ========================================================= -->
        <!-- TAB 2: INTERACTIVE PLAYER SCOUTING EXPLORER -->
        <!-- ========================================================= -->
        <section id="tab-explorer" class="tab-content hidden">
            <div class="pb-6 border-b border-slate-800">
                <h3 class="text-2xl font-black font-display text-white">Player Scouting Explorer & Head-to-Head Engine</h3>
                <p class="text-xs text-gray-400">Filter and evaluate all 290 qualified players (145 batters & 145 bowlers) across the T20 corpus.</p>
            </div>

            <!-- FILTER CONTROLS BAR -->
            <div class="mt-6 glass-panel p-4 rounded-2xl grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 text-xs">
                <div>
                    <label class="block text-gray-400 font-semibold mb-1">Discipline</label>
                    <select id="filter-discipline" onchange="applyFilters()" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-white focus:outline-none focus:border-rr-pink">
                        <option value="batters">Batters (145 Qualified)</option>
                        <option value="bowlers">Bowlers (145 Qualified)</option>
                    </select>
                </div>
                <div>
                    <label class="block text-gray-400 font-semibold mb-1">Role Filter</label>
                    <select id="filter-role" onchange="applyFilters()" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-white focus:outline-none focus:border-rr-pink">
                        <option value="all">All Roles</option>
                    </select>
                </div>
                <div>
                    <label class="block text-gray-400 font-semibold mb-1">Competition Tier</label>
                    <select id="filter-tier" onchange="applyFilters()" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-white focus:outline-none focus:border-rr-pink">
                        <option value="all">All Tiers</option>
                        <option value="Tier 1 (IPL)">Tier 1 (IPL Franchise)</option>
                        <option value="Tier 2 (T20I_FullMember)">Tier 2 (T20I Full Member)</option>
                    </select>
                </div>
                <div>
                    <label class="block text-gray-400 font-semibold mb-1">Search Player or Team</label>
                    <input type="text" id="filter-search" oninput="applyFilters()" placeholder="e.g. Sooryavanshi, RR, Kohli..." class="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-white focus:outline-none focus:border-rr-pink font-sans">
                </div>
                <div>
                    <label class="block text-gray-400 font-semibold mb-1">Sort By Metric</label>
                    <select id="filter-sort" onchange="applyFilters()" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-white focus:outline-none focus:border-rr-pink">
                        <option value="crr">CRR Championship Rating (High to Low)</option>
                        <option value="vaoe">Shrunk VAOE (High to Low)</option>
                        <option value="lcb">LCB_80 Certainty Floor (High to Low)</option>
                        <option value="delta">Clutch Delta (High to Low)</option>
                        <option value="balls">Pressure Balls (Volume)</option>
                    </select>
                </div>
            </div>

            <!-- HEAD-TO-HEAD COMPARATOR MODAL/BOX -->
            <div class="mt-6 glass-panel-gold p-5 rounded-2xl border border-rr-gold/50 shadow-2xl">
                <div class="flex items-center justify-between mb-4">
                    <div class="flex items-center space-x-2">
                        <span class="text-xl">⚔️</span>
                        <h4 class="text-sm font-bold font-display uppercase tracking-wider text-rr-gold">Head-to-Head Pressure Comparator</h4>
                    </div>
                    <span class="text-[11px] text-gray-400">Select any two players to benchmark clutch performance</span>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label class="block text-[11px] text-gray-400 font-semibold mb-1">Player A</label>
                        <select id="h2h-player-a" onchange="renderH2H()" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-rr-blue">
                        </select>
                    </div>
                    <div>
                        <label class="block text-[11px] text-gray-400 font-semibold mb-1">Player B</label>
                        <select id="h2h-player-b" onchange="renderH2H()" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-rr-pink">
                        </select>
                    </div>
                </div>

                <div id="h2h-results" class="mt-4 pt-4 border-t border-slate-700/60">
                    <!-- Head to head comparison rendered dynamically -->
                </div>
            </div>

            <!-- EXPLORER RESULTS TABLE -->
            <div class="mt-6 glass-panel rounded-2xl overflow-hidden border border-slate-800 shadow-xl">
                <div class="px-4 py-3 bg-slate-900/80 border-b border-slate-800 flex items-center justify-between text-xs">
                    <span class="font-semibold text-gray-300" id="explorer-count">Showing 145 Players</span>
                    <span class="text-gray-500 text-[11px]">Click player to compare</span>
                </div>
                <div class="overflow-x-auto max-h-[550px] overflow-y-auto">
                    <table class="w-full text-left text-xs font-mono">
                        <thead class="bg-rr-slate text-gray-300 uppercase tracking-wider text-[11px] font-sans sticky top-0 z-10 border-b border-slate-700">
                            <tr>
                                <th class="py-2.5 px-3">Rank</th>
                                <th class="py-2.5 px-3">Player</th>
                                <th class="py-2.5 px-3">Team</th>
                                <th class="py-2.5 px-3">Role</th>
                                <th class="py-2.5 px-3 text-right">HP Balls</th>
                                <th class="py-2.5 px-3 text-right" id="th-rate">HP Rate</th>
                                <th class="py-2.5 px-3 text-right">Shrunk VAOE</th>
                                <th class="py-2.5 px-3 text-right">LCB_80</th>
                                <th class="py-2.5 px-3 text-right">Clutch Delta</th>
                                <th class="py-2.5 px-3 text-right">CRR Rating</th>
                            </tr>
                        </thead>
                        <tbody id="explorer-tbody" class="divide-y divide-slate-800/60 text-gray-200">
                            <!-- Populated dynamically -->
                        </tbody>
                    </table>
                </div>
            </div>
        </section>

        <!-- ========================================================= -->
        <!-- TAB 3: RR TACTICAL AUCTION TARGET MATRIX -->
        <!-- ========================================================= -->
        <section id="tab-auction" class="tab-content hidden">
            <div class="pb-6 border-b border-slate-800">
                <h3 class="text-2xl font-black font-display text-white">Rajasthan Royals Tactical Recruitment Matrix</h3>
                <p class="text-xs text-gray-400">Actionable operational intelligence translating quantitative CRR rankings into front-office squad recommendations.</p>
            </div>

            <!-- Bucket Filter Buttons -->
            <div class="flex flex-wrap items-center gap-2 mt-6">
                <button onclick="filterAuction('all')" class="auction-btn active px-3.5 py-1.5 rounded-lg text-xs font-bold transition bg-slate-800 text-white border border-slate-700">
                    All Players (16)
                </button>
                <button onclick="filterAuction('Bucket 1')" class="auction-btn px-3.5 py-1.5 rounded-lg text-xs font-bold transition bg-slate-900 text-blue-300 border border-blue-900/60 hover:bg-slate-800">
                    👑 Bucket 1 — RR Core (2)
                </button>
                <button onclick="filterAuction('Bucket 2')" class="auction-btn px-3.5 py-1.5 rounded-lg text-xs font-bold transition bg-slate-900 text-yellow-300 border border-yellow-900/60 hover:bg-slate-800">
                    🔒 Bucket 2 — Franchise Benchmarks (4)
                </button>
                <button onclick="filterAuction('Bucket 3')" class="auction-btn px-3.5 py-1.5 rounded-lg text-xs font-bold transition bg-slate-900 text-pink-300 border border-pink-900/60 hover:bg-slate-800">
                    🎯 Bucket 3 — Priority Auction Targets (10)
                </button>
            </div>

            <!-- Auction Matrix Cards Grid -->
            <div id="auction-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 mt-6">
                <!-- Populated dynamically -->
            </div>
        </section>

        <!-- ========================================================= -->
        <!-- TAB 4: MATHEMATICAL EVIDENCE & GALLERY -->
        <!-- ========================================================= -->
        <section id="tab-evidence" class="tab-content hidden">
            <div class="pb-6 border-b border-slate-800">
                <h3 class="text-2xl font-black font-display text-white">Mathematical & Visual Evidence Gallery</h3>
                <p class="text-xs text-gray-400">Interactive 2D Clutch Quadrant scatter plot and 8 high-resolution 300-DPI publication figures.</p>
            </div>

            <!-- INTERACTIVE PLOTLY CLUTCH QUADRANT -->
            <div class="mt-6 glass-panel p-5 rounded-2xl border border-slate-800">
                <div class="flex items-center justify-between mb-2">
                    <div>
                        <h4 class="text-base font-bold text-white font-display">Interactive 2D Clutch Elevation Quadrant</h4>
                        <p class="text-xs text-gray-400">Normal Baseline VAOE vs High-Pressure VAOE across Top 10 Batters and Bowlers</p>
                    </div>
                    <span class="text-[11px] font-mono text-rr-gold bg-rr-gold/10 px-2.5 py-1 rounded-md border border-rr-gold/30">Hover to inspect</span>
                </div>
                <div id="plotly-quadrant" style="width: 100%; height: 520px;"></div>
            </div>

            <!-- 8 PUBLICATION CHARTS GALLERY -->
            <div class="mt-10">
                <h4 class="text-xl font-black font-display text-white mb-2">300-DPI Publication Visualizations Gallery</h4>
                <p class="text-xs text-gray-400 mb-6">Direct visual outputs generated in Phase 8 supporting the final technical whitepaper.</p>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-6" id="figures-grid">
                    <!-- Populated dynamically -->
                </div>
            </div>
        </section>

    </main>

    <!-- FOOTER -->
    <footer class="mt-16 border-t border-slate-800 bg-rr-slate py-8 text-center text-xs text-gray-500 font-mono">
        <div class="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div class="flex items-center space-x-2">
                <div class="w-6 h-6 rounded bg-rr-pink flex items-center justify-center text-white text-[10px] font-black">RR</div>
                <span class="text-gray-300 font-semibold font-sans">Rajasthan Royals SupeRR Selector Season 2</span>
            </div>
            <div>
                Deterministic Analytics Pipeline • 100% Reproducible • Built for RR Analytics Desk
            </div>
            <div class="text-gray-400">
                <a href="#top" class="hover:text-rr-pink transition">Back to Top ↑</a>
            </div>
        </div>
    </footer>

    <!-- EMBEDDED DATASET JSON SCRIPTS (Zero Network Latency / No Backend Needed) -->
    <script>
        const topBatters = {json_top_bat};
        const topBowlers = {json_top_bowl};
        const allBatters = {json_all_bat};
        const allBowlers = {json_all_bowl};
        const auctionMatrix = {json_auction};
        const quadrantData = {json_quadrant};
        const figuresList = {json_figures};

        let currentDiscipline = 'batters';
        let currentAuctionFilter = 'all';

        // ---------------------------------------------------------
        // TAB SWITCHING
        // ---------------------------------------------------------
        function switchTab(tabId) {{
            document.querySelectorAll('.tab-content').forEach(el => {{
                el.classList.add('hidden');
                el.classList.remove('block');
            }});
            document.querySelectorAll('.tab-btn').forEach(btn => {{
                btn.classList.remove('active');
                btn.classList.add('text-gray-300');
            }});

            const target = document.getElementById(tabId);
            if (target) {{
                target.classList.remove('hidden');
                target.classList.add('block');
            }}
            const activeBtn = document.getElementById('btn-' + tabId);
            if (activeBtn) {{
                activeBtn.classList.add('active');
                activeBtn.classList.remove('text-gray-300');
            }}

            if (tabId === 'tab-evidence') {{
                setTimeout(renderPlotlyQuadrant, 100);
            }}
        }}

        // ---------------------------------------------------------
        // DISCIPLINE TOGGLE (TAB 1)
        // ---------------------------------------------------------
        function setDiscipline(disc) {{
            currentDiscipline = disc;
            const batBtn = document.getElementById('toggle-batters-btn');
            const bowlBtn = document.getElementById('toggle-bowlers-btn');

            if (disc === 'batters') {{
                batBtn.className = "px-4 py-1.5 rounded-lg text-xs font-bold transition bg-rr-blue text-white shadow";
                bowlBtn.className = "px-4 py-1.5 rounded-lg text-xs font-bold transition text-gray-400 hover:text-white";
                document.getElementById('dossiers-heading').innerText = "Top 10 Batters Detailed Scouting Dossiers";
            }} else {{
                bowlBtn.className = "px-4 py-1.5 rounded-lg text-xs font-bold transition bg-rr-pink text-white shadow";
                batBtn.className = "px-4 py-1.5 rounded-lg text-xs font-bold transition text-gray-400 hover:text-white";
                document.getElementById('dossiers-heading').innerText = "Top 10 Bowlers Detailed Scouting Dossiers";
            }}
            renderTop10Table();
            renderTop10Dossiers();
        }}

        // ---------------------------------------------------------
        // RENDER TOP 10 TABLE
        // ---------------------------------------------------------
        function renderTop10Table() {{
            const thead = document.getElementById('top10-thead');
            const tbody = document.getElementById('top10-tbody');
            const isBat = (currentDiscipline === 'batters');
            const data = isBat ? topBatters : topBowlers;

            if (isBat) {{
                thead.innerHTML = `
                    <tr>
                        <th class="py-3 px-3 text-center">Rank</th>
                        <th class="py-3 px-3">Player ID</th>
                        <th class="py-3 px-4">Player Name</th>
                        <th class="py-3 px-3">Role</th>
                        <th class="py-3 px-3 text-right">HP Balls (N_eff)</th>
                        <th class="py-3 px-3 text-right">HP SR (Exp)</th>
                        <th class="py-3 px-3 text-right">Shrunk VAOE</th>
                        <th class="py-3 px-3 text-right">LCB_80</th>
                        <th class="py-3 px-3 text-right">Ext VAOE</th>
                        <th class="py-3 px-3 text-right">Clutch Δ</th>
                        <th class="py-3 px-3 text-right">Win %</th>
                        <th class="py-3 px-3 text-center">95% Boot CI</th>
                        <th class="py-3 px-4 text-right">CRR Score</th>
                    </tr>
                `;
            }} else {{
                thead.innerHTML = `
                    <tr>
                        <th class="py-3 px-3 text-center">Rank</th>
                        <th class="py-3 px-3">Player ID</th>
                        <th class="py-3 px-4">Player Name</th>
                        <th class="py-3 px-3">Discipline</th>
                        <th class="py-3 px-3 text-right">HP Balls (N_eff)</th>
                        <th class="py-3 px-3 text-right">HP Econ (Exp)</th>
                        <th class="py-3 px-3 text-right">Shrunk VAOE</th>
                        <th class="py-3 px-3 text-right">LCB_80</th>
                        <th class="py-3 px-3 text-right">Ext VAOE</th>
                        <th class="py-3 px-3 text-right">Clutch Δ</th>
                        <th class="py-3 px-3 text-right">Death %</th>
                        <th class="py-3 px-3 text-center">95% Boot CI</th>
                        <th class="py-3 px-4 text-right">CRR Score</th>
                    </tr>
                `;
            }}

            tbody.innerHTML = data.map((p, idx) => {{
                const rateStr = isBat ? `${{p.sr.toFixed(1)}} (${{p.exp_sr.toFixed(1)}})` : `${{p.econ.toFixed(2)}} (${{p.exp_econ.toFixed(2)}})`;
                const secMetric = isBat ? `${{p.win_pct.toFixed(1)}}%` : `${{p.death_pct.toFixed(1)}}%`;
                const deltaStr = p.delta >= 0 ? `+${{p.delta.toFixed(1)}}` : `${{p.delta.toFixed(1)}}`;
                const deltaColor = p.delta >= 0 ? 'text-green-400' : 'text-red-400';
                const rankColor = p.rank === 1 ? 'bg-rr-gold/20 text-rr-gold border-rr-gold/40' : (p.rank <= 3 ? 'bg-rr-pink/20 text-rr-pink border-rr-pink/40' : 'bg-slate-800 text-gray-300 border-slate-700');

                return `
                    <tr class="hover:bg-slate-800/50 transition cursor-pointer" onclick="scrollToDossier('${{p.id}}')">
                        <td class="py-3 px-3 text-center">
                            <span class="inline-flex items-center justify-center w-6 h-6 rounded-md text-[11px] font-bold border ${{rankColor}}">
                                #${{p.rank}}
                            </span>
                        </td>
                        <td class="py-3 px-3 text-gray-400">${{p.id}}</td>
                        <td class="py-3 px-4 font-sans font-bold text-white flex items-center space-x-2">
                            <span>${{p.name}}</span>
                            ${{p.rank === 1 ? '<span class="text-xs">👑</span>' : ''}}
                        </td>
                        <td class="py-3 px-3 text-gray-300 font-sans">${{isBat ? p.role : p.discipline}}</td>
                        <td class="py-3 px-3 text-right text-gray-300">${{p.balls}} (${{p.neff}})</td>
                        <td class="py-3 px-3 text-right text-blue-300">${{rateStr}}</td>
                        <td class="py-3 px-3 text-right font-bold text-green-400">+${{p.vaoe.toFixed(2)}}</td>
                        <td class="py-3 px-3 text-right text-rr-gold font-semibold">+${{p.lcb.toFixed(2)}}</td>
                        <td class="py-3 px-3 text-right text-purple-300">+${{p.ext.toFixed(1)}}</td>
                        <td class="py-3 px-3 text-right font-semibold ${{deltaColor}}">${{deltaStr}}</td>
                        <td class="py-3 px-3 text-right text-gray-300">${{secMetric}}</td>
                        <td class="py-3 px-3 text-center text-[11px] text-gray-400 font-mono">[${{p.ci_low.toFixed(1)}}, ${{p.ci_high.toFixed(1)}}]</td>
                        <td class="py-3 px-4 text-right font-sans font-extrabold text-sm text-transparent bg-clip-text bg-gradient-to-r from-rr-pink to-rr-gold">
                            ${{p.crr.toFixed(2)}}
                        </td>
                    </tr>
                `;
            }}).join('');
        }}

        // ---------------------------------------------------------
        // RENDER TOP 10 DOSSIERS CARDS
        // ---------------------------------------------------------
        function renderTop10Dossiers() {{
            const grid = document.getElementById('dossiers-grid');
            const isBat = (currentDiscipline === 'batters');
            const data = isBat ? topBatters : topBowlers;

            grid.innerHTML = data.map(p => {{
                const badgeGrad = isBat ? 'from-rr-blue to-blue-700' : 'from-rr-pink to-rose-700';
                const rateMetric = isBat 
                    ? `HP SR: <span class="text-white font-bold">${{p.sr.toFixed(2)}}</span> <span class="text-gray-400 text-[10px]">(Exp: ${{p.exp_sr.toFixed(2)}}, Res: ${{p.sr_res >= 0 ? '+' : ''}}${{p.sr_res.toFixed(2)}})</span>`
                    : `HP Econ: <span class="text-white font-bold">${{p.econ.toFixed(2)}}</span> <span class="text-gray-400 text-[10px]">(Exp: ${{p.exp_econ.toFixed(2)}}, Saved: +${{p.econ_saved.toFixed(2)}} RPO)</span>`;
                
                const tacticalRow = isBat
                    ? `<div class="text-xs text-gray-300 leading-relaxed"><span class="font-bold text-gray-200">Pace vs Spin:</span> ${{p.pace_spin}} &nbsp;•&nbsp; <span class="font-bold text-gray-200">Top Stroke:</span> ${{p.stroke}}</div>
                       <div class="text-xs text-gray-400 mt-1">${{p.tactical}}</div>`
                    : `<div class="text-xs text-gray-300 leading-relaxed"><span class="font-bold text-gray-200">Release:</span> ${{p.speed}} km/h &nbsp;•&nbsp; <span class="font-bold text-gray-200">Yorker:</span> ${{p.yorker}}% &nbsp;•&nbsp; <span class="font-bold text-gray-200">Bouncer:</span> ${{p.bouncer}}% &nbsp;•&nbsp; <span class="font-bold text-gray-200">Slower:</span> ${{p.slower}}% &nbsp;•&nbsp; <span class="font-bold text-gray-200">Dot%:</span> ${{p.dot_pct}}%</div>
                       <div class="text-xs text-gray-400 mt-1">${{p.tactical}}</div>`;

                return `
                    <div id="card-${{p.id}}" class="glass-panel rounded-2xl overflow-hidden border border-slate-700/80 hover:border-rr-pink/60 transition shadow-lg flex flex-col">
                        <!-- Card Header -->
                        <div class="bg-gradient-to-r ${{badgeGrad}} p-4 flex items-center justify-between">
                            <div class="flex items-center space-x-3">
                                <span class="w-8 h-8 rounded-lg bg-black/30 flex items-center justify-center font-display font-extrabold text-sm text-white border border-white/20">
                                    #${{p.rank}}
                                </span>
                                <div>
                                    <h4 class="font-display font-bold text-base text-white leading-snug">${{p.name}}</h4>
                                    <p class="text-[11px] text-white/80 font-mono">ID: ${{p.id}} • ${{p.role}}</p>
                                </div>
                            </div>
                            <div class="text-right">
                                <div class="text-[10px] text-white/70 uppercase tracking-wider font-semibold">CRR Score</div>
                                <div class="font-display font-black text-xl text-rr-gold drop-shadow-sm">${{p.crr.toFixed(2)}}</div>
                            </div>
                        </div>

                        <!-- Card Metrics Banner -->
                        <div class="bg-slate-900/90 border-b border-slate-800 p-3 text-xs font-mono grid grid-cols-2 sm:grid-cols-4 gap-2">
                            <div>
                                <span class="text-gray-400 text-[10px]">HP Balls:</span>
                                <span class="text-white font-bold block">${{p.balls}} (${{p.neff}})</span>
                            </div>
                            <div>
                                <span class="text-gray-400 text-[10px]">Shrunk VAOE:</span>
                                <span class="text-green-400 font-bold block">+${{p.vaoe.toFixed(2)}}</span>
                            </div>
                            <div>
                                <span class="text-gray-400 text-[10px]">LCB_80 Floor:</span>
                                <span class="text-rr-gold font-bold block">+${{p.lcb.toFixed(2)}}</span>
                            </div>
                            <div>
                                <span class="text-gray-400 text-[10px]">Ext VAOE:</span>
                                <span class="text-purple-300 font-bold block">+${{p.ext.toFixed(1)}}</span>
                            </div>
                        </div>

                        <!-- Card Body -->
                        <div class="p-4 flex-1 space-y-3.5">
                            <div>
                                <div class="text-[11px] font-mono text-blue-300 mb-1">${{rateMetric}}</div>
                                <div class="text-[11px] font-mono text-gray-400">95% Boot CI: [${{p.ci_low.toFixed(2)}}, ${{p.ci_high.toFixed(2)}}] &nbsp;•&nbsp; Clutch Δ: ${{p.delta >= 0 ? '+' : ''}}${{p.delta.toFixed(2)}}</div>
                            </div>

                            <div class="pt-2 border-t border-slate-800">
                                <span class="text-[10px] uppercase tracking-wider font-bold text-gray-400 block mb-1">Tactical & Biomechanical Signature</span>
                                ${{tacticalRow}}
                            </div>

                            <div class="pt-2 border-t border-slate-800">
                                <span class="text-[10px] uppercase tracking-wider font-bold text-gray-400 block mb-1">Key Match Walkthroughs</span>
                                <p class="text-xs text-gray-300 font-mono leading-relaxed">${{p.walkthrough}}</p>
                            </div>

                            <div class="pt-2 border-t border-slate-800 bg-slate-900/60 -mx-4 -mb-4 p-4">
                                <span class="text-[10px] uppercase tracking-wider font-bold text-rr-pink block mb-0.5">Front-Office Scouting Verdict</span>
                                <p class="text-xs text-gray-200 font-sans leading-relaxed">${{p.verdict}}</p>
                            </div>
                        </div>
                    </div>
                `;
            }}).join('');
        }}

        function scrollToDossier(id) {{
            const card = document.getElementById('card-' + id);
            if (card) {{
                card.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                card.classList.add('ring-2', 'ring-rr-pink');
                setTimeout(() => card.classList.remove('ring-2', 'ring-rr-pink'), 2000);
            }}
        }}

        // ---------------------------------------------------------
        // TAB 2: EXPLORER & HEAD-TO-HEAD
        // ---------------------------------------------------------
        function initExplorer() {{
            const roleSelect = document.getElementById('filter-role');
            const h2hA = document.getElementById('h2h-player-a');
            const h2hB = document.getElementById('h2h-player-b');

            // Populate roles based on discipline
            const isBat = (document.getElementById('filter-discipline').value === 'batters');
            const dataset = isBat ? allBatters : allBowlers;

            const roles = Array.from(new Set(dataset.map(p => p.role))).filter(Boolean);
            roleSelect.innerHTML = '<option value="all">All Roles</option>' + roles.map(r => `<option value="${{r}}">${{r}}</option>`).join('');

            // Populate H2H dropdowns
            const optList = dataset.map(p => `<option value="${{p.id}}">#${{p.rank}} ${{p.name}} (CRR: ${{p.crr.toFixed(1)}})</option>`).join('');
            h2hA.innerHTML = optList;
            h2hB.innerHTML = optList;
            if (dataset.length > 1) {{
                h2hB.selectedIndex = 1;
            }}

            applyFilters();
            renderH2H();
        }}

        function applyFilters() {{
            const isBat = (document.getElementById('filter-discipline').value === 'batters');
            const dataset = isBat ? allBatters : allBowlers;
            const roleVal = document.getElementById('filter-role').value;
            const tierVal = document.getElementById('filter-tier').value;
            const searchVal = document.getElementById('filter-search').value.toLowerCase();
            const sortVal = document.getElementById('filter-sort').value;

            document.getElementById('th-rate').innerText = isBat ? 'HP Strike Rate' : 'HP Economy';

            let filtered = dataset.filter(p => {{
                if (roleVal !== 'all' && p.role !== roleVal) return false;
                if (tierVal !== 'all' && p.tier !== tierVal) return false;
                if (searchVal && !p.name.toLowerCase().includes(searchVal) && !p.teams.toLowerCase().includes(searchVal) && !String(p.id).includes(searchVal)) return false;
                return true;
            }});

            // Sort
            if (sortVal === 'crr') filtered.sort((a,b) => b.crr - a.crr);
            else if (sortVal === 'vaoe') filtered.sort((a,b) => b.vaoe - a.vaoe);
            else if (sortVal === 'lcb') filtered.sort((a,b) => b.lcb - a.lcb);
            else if (sortVal === 'delta') filtered.sort((a,b) => b.delta - a.delta);
            else if (sortVal === 'balls') filtered.sort((a,b) => b.balls - a.balls);

            document.getElementById('explorer-count').innerText = `Showing ${{filtered.length}} of ${{dataset.length}} Qualified Players`;

            const tbody = document.getElementById('explorer-tbody');
            tbody.innerHTML = filtered.map(p => {{
                const rateVal = isBat ? `${{p.sr.toFixed(1)}}` : `${{p.econ.toFixed(2)}}`;
                const deltaColor = p.delta >= 0 ? 'text-green-400' : 'text-red-400';
                return `
                    <tr class="hover:bg-slate-800/50 transition">
                        <td class="py-2 px-3 font-bold text-gray-300">#${{p.rank}}</td>
                        <td class="py-2 px-3 font-sans font-semibold text-white">${{p.name}}</td>
                        <td class="py-2 px-3 text-gray-400 text-[11px] font-sans truncate max-w-[140px]">${{p.teams}}</td>
                        <td class="py-2 px-3 text-gray-300 font-sans">${{p.role}}</td>
                        <td class="py-2 px-3 text-right text-gray-300">${{p.balls}}</td>
                        <td class="py-2 px-3 text-right text-blue-300 font-bold">${{rateVal}}</td>
                        <td class="py-2 px-3 text-right text-green-400 font-bold">+${{p.vaoe.toFixed(2)}}</td>
                        <td class="py-2 px-3 text-right text-rr-gold font-semibold">+${{p.lcb.toFixed(2)}}</td>
                        <td class="py-2 px-3 text-right font-semibold ${{deltaColor}}">${{p.delta >= 0 ? '+' : ''}}${{p.delta.toFixed(2)}}</td>
                        <td class="py-2 px-3 text-right font-bold text-rr-pink">${{p.crr.toFixed(2)}}</td>
                    </tr>
                `;
            }}).join('');
        }}

        function renderH2H() {{
            const isBat = (document.getElementById('filter-discipline').value === 'batters');
            const dataset = isBat ? allBatters : allBowlers;
            const idA = parseInt(document.getElementById('h2h-player-a').value);
            const idB = parseInt(document.getElementById('h2h-player-b').value);

            const pA = dataset.find(p => p.id === idA);
            const pB = dataset.find(p => p.id === idB);
            if (!pA || !pB) return;

            const res = document.getElementById('h2h-results');
            const rateName = isBat ? "HP Strike Rate" : "HP Economy Rate";
            const rateA = isBat ? pA.sr.toFixed(1) : pA.econ.toFixed(2);
            const rateB = isBat ? pB.sr.toFixed(1) : pB.econ.toFixed(2);

            function cmp(valA, valB, higherBetter=true) {{
                if (valA === valB) return ['text-gray-300', 'text-gray-300'];
                const aWins = higherBetter ? (valA > valB) : (valA < valB);
                return aWins ? ['text-green-400 font-bold', 'text-gray-400'] : ['text-gray-400', 'text-green-400 font-bold'];
            }}

            const [c_crr_a, c_crr_b] = cmp(pA.crr, pB.crr, true);
            const [c_vaoe_a, c_vaoe_b] = cmp(pA.vaoe, pB.vaoe, true);
            const [c_lcb_a, c_lcb_b] = cmp(pA.lcb, pB.lcb, true);
            const [c_ext_a, c_ext_b] = cmp(pA.ext, pB.ext, true);
            const [c_delta_a, c_delta_b] = cmp(pA.delta, pB.delta, true);

            res.innerHTML = `
                <div class="grid grid-cols-3 gap-2 text-center text-xs font-mono items-center">
                    <div class="p-3 bg-slate-900 rounded-xl border border-rr-blue/40 text-left">
                        <div class="font-display font-black text-sm text-white">${{pA.name}}</div>
                        <div class="text-[10px] text-gray-400">Rank #${{pA.rank}} • ${{pA.role}}</div>
                        <div class="text-xs font-bold text-rr-blue mt-1">CRR: ${{pA.crr.toFixed(2)}}</div>
                    </div>

                    <div class="text-[11px] font-sans font-semibold text-gray-400 uppercase tracking-wider">
                        Comparative Metrics
                    </div>

                    <div class="p-3 bg-slate-900 rounded-xl border border-rr-pink/40 text-right">
                        <div class="font-display font-black text-sm text-white">${{pB.name}}</div>
                        <div class="text-[10px] text-gray-400">Rank #${{pB.rank}} • ${{pB.role}}</div>
                        <div class="text-xs font-bold text-rr-pink mt-1">CRR: ${{pB.crr.toFixed(2)}}</div>
                    </div>

                    <!-- Row 1: CRR Score -->
                    <div class="${{c_crr_a}} text-sm">${{pA.crr.toFixed(2)}}</div>
                    <div class="text-gray-400 text-[11px]">Championship CRR</div>
                    <div class="${{c_crr_b}} text-sm">${{pB.crr.toFixed(2)}}</div>

                    <!-- Row 2: Shrunk VAOE -->
                    <div class="${{c_vaoe_a}}">+${{pA.vaoe.toFixed(2)}}</div>
                    <div class="text-gray-400 text-[11px]">Shrunk VAOE</div>
                    <div class="${{c_vaoe_b}}">+${{pB.vaoe.toFixed(2)}}</div>

                    <!-- Row 3: LCB 80 -->
                    <div class="${{c_lcb_a}}">+${{pA.lcb.toFixed(2)}}</div>
                    <div class="text-gray-400 text-[11px]">LCB_80 Certainty Floor</div>
                    <div class="${{c_lcb_b}}">+${{pB.lcb.toFixed(2)}}</div>

                    <!-- Row 4: Extreme VAOE -->
                    <div class="${{c_ext_a}}">+${{pA.ext.toFixed(1)}}</div>
                    <div class="text-gray-400 text-[11px]">Extreme Crucible VAOE</div>
                    <div class="${{c_ext_b}}">+${{pB.ext.toFixed(1)}}</div>

                    <!-- Row 5: Rate -->
                    <div class="text-white">${{rateA}}</div>
                    <div class="text-gray-400 text-[11px]">${{rateName}}</div>
                    <div class="text-white">${{rateB}}</div>

                    <!-- Row 6: Delta -->
                    <div class="${{c_delta_a}}">${{pA.delta >= 0 ? '+' : ''}}${{pA.delta.toFixed(2)}}</div>
                    <div class="text-gray-400 text-[11px]">Clutch Elevation Delta</div>
                    <div class="${{c_delta_b}}">${{pB.delta >= 0 ? '+' : ''}}${{pB.delta.toFixed(2)}}</div>
                </div>
            `;
        }}

        // ---------------------------------------------------------
        // TAB 3: RR TACTICAL AUCTION MATRIX
        // ---------------------------------------------------------
        function filterAuction(bucketPrefix) {{
            currentAuctionFilter = bucketPrefix;
            document.querySelectorAll('.auction-btn').forEach(b => {{
                b.classList.remove('active', 'border-rr-pink', 'text-white');
                b.classList.add('text-gray-300');
            }});
            renderAuctionMatrix();
        }}

        function renderAuctionMatrix() {{
            const grid = document.getElementById('auction-grid');
            let filtered = auctionMatrix;
            if (currentAuctionFilter !== 'all') {{
                filtered = auctionMatrix.filter(p => p.bucket.startsWith(currentAuctionFilter));
            }}

            grid.innerHTML = filtered.map(p => {{
                let bColor = "border-blue-700/80 bg-blue-950/20";
                let tagColor = "bg-blue-500/20 text-blue-300 border-blue-500/40";
                let icon = "👑";

                if (p.bucket.includes("Bucket 2")) {{
                    bColor = "border-yellow-700/80 bg-yellow-950/20";
                    tagColor = "bg-yellow-500/20 text-yellow-300 border-yellow-500/40";
                    icon = "🔒";
                }} else if (p.bucket.includes("Bucket 3")) {{
                    bColor = "border-pink-700/80 bg-pink-950/20";
                    tagColor = "bg-pink-500/20 text-pink-300 border-pink-500/40";
                    icon = "🎯";
                }}

                return `
                    <div class="glass-panel p-5 rounded-2xl border ${{bColor}} hover:scale-[1.02] transition shadow-lg flex flex-col justify-between">
                        <div>
                            <div class="flex items-center justify-between mb-3">
                                <span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${{tagColor}}">
                                    ${{icon}} ${{p.action}}
                                </span>
                                <span class="font-display font-extrabold text-sm text-rr-gold font-mono">CRR ${{p.crr.toFixed(2)}}</span>
                            </div>

                            <h4 class="font-display font-bold text-lg text-white">${{p.name}}</h4>
                            <p class="text-xs text-gray-400 font-mono mb-2">${{p.rank}} • ${{p.role}}</p>

                            <p class="text-xs text-gray-300 font-sans leading-relaxed pt-2 border-t border-slate-800">
                                ${{p.rationale}}
                            </p>
                        </div>

                        <div class="mt-4 pt-2 border-t border-slate-800/60 text-[10px] text-gray-500 font-mono">
                            ${{p.bucket}}
                        </div>
                    </div>
                `;
            }}).join('');
        }}

        // ---------------------------------------------------------
        // TAB 4: EVIDENCE GALLERY & PLOTLY QUADRANT
        // ---------------------------------------------------------
        function renderPlotlyQuadrant() {{
            const batPoints = quadrantData.filter(d => d.type === 'Batter');
            const bowlPoints = quadrantData.filter(d => d.type === 'Bowler');

            const traceBat = {{
                x: batPoints.map(d => d.baseline),
                y: batPoints.map(d => d.pressure),
                text: batPoints.map(d => `<b>${{d.name}}</b> (${{d.rank}})<br>Normal Baseline VAOE: ${{d.baseline}} runs/100b<br>High-Pressure VAOE: +${{d.pressure}} runs/100b<br>Clutch Delta: ${{d.delta >= 0 ? '+' : ''}}${{d.delta}}<br>CRR: ${{d.crr}}`),
                mode: 'markers+text',
                name: 'Top 10 Batters',
                textposition: 'top center',
                textfont: {{ family: 'Inter', size: 10, color: '#FFFFFF' }},
                marker: {{
                    size: 14,
                    color: '#004B87',
                    line: {{ color: '#D4AF37', width: 2 }}
                }},
                hoverinfo: 'text'
            }};

            const traceBowl = {{
                x: bowlPoints.map(d => d.baseline),
                y: bowlPoints.map(d => d.pressure),
                text: bowlPoints.map(d => `<b>${{d.name}}</b> (${{d.rank}})<br>Normal Baseline VAOE: ${{d.baseline}} runs/24b<br>High-Pressure VAOE: +${{d.pressure}} runs/24b<br>Clutch Delta: ${{d.delta >= 0 ? '+' : ''}}${{d.delta}}<br>CRR: ${{d.crr}}`),
                mode: 'markers+text',
                name: 'Top 10 Bowlers',
                textposition: 'bottom center',
                textfont: {{ family: 'Inter', size: 10, color: '#FFFFFF' }},
                marker: {{
                    size: 14,
                    color: '#EA1B75',
                    line: {{ color: '#FFFFFF', width: 1.5 }}
                }},
                hoverinfo: 'text'
            }};

            const layout = {{
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(15,23,42,0.6)',
                margin: {{ l: 60, r: 40, t: 30, b: 60 }},
                showlegend: true,
                legend: {{
                    x: 0.02, y: 0.98,
                    bgcolor: 'rgba(30,41,59,0.85)',
                    bordercolor: '#475569',
                    font: {{ color: '#FFFFFF', size: 11 }}
                }},
                xaxis: {{
                    title: {{ text: '<b>Normal Baseline Performance (VAOE Residual)</b>', font: {{ color: '#94A3B8', size: 12 }} }},
                    tickfont: {{ color: '#94A3B8', size: 10 }},
                    gridcolor: '#334155',
                    zerolinecolor: '#64748B',
                    zerolinewidth: 1.5
                }},
                yaxis: {{
                    title: {{ text: '<b>High-Pressure Performance (Shrunk VAOE Residual)</b>', font: {{ color: '#94A3B8', size: 12 }} }},
                    tickfont: {{ color: '#94A3B8', size: 10 }},
                    gridcolor: '#334155',
                    zerolinecolor: '#64748B',
                    zerolinewidth: 1.5
                }},
                shapes: [
                    // Quadrant 1 (Top Left: Clutch Escalators)
                    {{ type: 'rect', x0: -20, x1: 0, y0: 0, y1: 45, fillcolor: 'rgba(234, 27, 117, 0.08)', line: {{ width: 0 }}, layer: 'below' }},
                    // Quadrant 2 (Top Right: All-Weather Superstars)
                    {{ type: 'rect', x0: 0, x1: 85, y0: 0, y1: 45, fillcolor: 'rgba(0, 75, 135, 0.15)', line: {{ width: 0 }}, layer: 'below' }}
                ],
                annotations: [
                    {{ x: 60, y: 38, text: '<b>ALL-WEATHER SUPERSTARS</b><br>(High Base, High Pressure)', showarrow: false, font: {{ color: '#60A5FA', size: 11 }} }},
                    {{ x: -10, y: 38, text: '<b>CLUTCH ESCALATORS</b><br>(Delta > 0 Boost)', showarrow: false, font: {{ color: '#F472B6', size: 11 }} }}
                ]
            }};

            Plotly.newPlot('plotly-quadrant', [traceBat, traceBowl], layout, {{ responsive: true, displayModeBar: false }});
        }}

        function renderFiguresGallery() {{
            const grid = document.getElementById('figures-grid');
            grid.innerHTML = figuresList.map(fig => {{
                return `
                    <div class="glass-panel rounded-2xl overflow-hidden border border-slate-700/80 hover:border-rr-pink/60 transition shadow-lg flex flex-col">
                        <div class="p-3 bg-slate-900 border-b border-slate-800">
                            <h5 class="font-display font-bold text-sm text-white">${{fig.title}}</h5>
                        </div>
                        <div class="bg-black/40 p-2 flex items-center justify-center">
                            <img src="${{fig.file}}" alt="${{fig.title}}" class="rounded-lg max-h-72 object-contain hover:scale-105 transition duration-300 cursor-pointer" onclick="window.open('${{fig.file}}', '_blank')">
                        </div>
                        <div class="p-3 text-xs text-gray-400 font-sans leading-relaxed flex-1">
                            ${{fig.desc}}
                        </div>
                    </div>
                `;
            }}).join('');
        }}

        // ---------------------------------------------------------
        // INITIALIZATION
        // ---------------------------------------------------------
        document.addEventListener('DOMContentLoaded', () => {{
            renderTop10Table();
            renderTop10Dossiers();
            initExplorer();
            renderAuctionMatrix();
            renderFiguresGallery();
        }});
    </script>
</body>
</html>
"""

    out_index_path = os.path.join(base_dir, "docs", "index.html")
    with open(out_index_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Generated: {out_index_path}")

    # Build Streamlit app.py
    print("--- [Web Dashboard 3/3] Generating app.py (Streamlit) & requirements.txt ---")
    st_app_code = """\"\"\"
Rajasthan Royals — SupeRR Selector Season 2
Interactive Streamlit Dashboard
Deployable on Streamlit Cloud (share.streamlit.io).
\"\"\"

import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Rajasthan Royals — SupeRR Selector Season 2",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for RR Theme
st.markdown(\"\"\"
<style>
    .main {
        background-color: #0A0F1D;
        color: #F8FAFC;
    }
    .stMetric {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 12px;
    }
    .rr-header {
        background: linear-gradient(135deg, #004B87 0%, #EA1B75 100%);
        padding: 24px;
        border-radius: 16px;
        color: white;
        margin-bottom: 24px;
    }
</style>
\"\"\", unsafe_allow_html=True)

@st.cache_data
def load_data():
    top_bat = pd.read_csv("top_10_batters.csv")
    top_bowl = pd.read_csv("top_10_bowlers.csv")
    all_bat = pd.read_csv("complete_batter_rankings.csv")
    all_bowl = pd.read_csv("complete_bowler_rankings.csv")
    all_bat_q = all_bat[all_bat["is_eligible_final"] == True].sort_values("rank_crr")
    all_bowl_q = all_bowl[all_bowl["is_eligible_final"] == True].sort_values("rank_crr")
    return top_bat, top_bowl, all_bat_q, all_bowl_q

top_bat, top_bowl, all_bat, all_bowl = load_data()

# Header Banner
st.markdown(\"\"\"
<div class="rr-header">
    <h1 style="margin:0; font-family:sans-serif; font-weight:800;">👑 RAJASTHAN ROYALS — SUPERR SELECTOR SEASON 2</h1>
    <h3 style="margin:4px 0 0 0; opacity:0.9;">Identifying The Most Reliable Players Under Pressure • CRR Engine</h3>
</div>
\"\"\", unsafe_allow_html=True)

# Sidebar
st.sidebar.image("docs/charts/fig5_top10_batters_evidence_dashboard.png", use_container_width=True)
st.sidebar.title("Navigation")
menu = st.sidebar.radio("Select View:", [
    "🏆 Official Top-10 Rosters",
    "🔍 Player Scouting Explorer",
    "🎯 RR Tactical Auction Matrix",
    "📈 Evidence & Charts Gallery"
])

st.sidebar.markdown("---")
st.sidebar.markdown("**Quantitative Rigor & Governance:**")
st.sidebar.markdown("• 883 Matches | 200,999 Deliveries")
st.sidebar.markdown("• Strict Pre-Delivery Anti-Leakage")
st.sidebar.markdown("• Hierarchical Empirical Bayes (K=200/234)")
st.sidebar.markdown("• 70/70 Automated Tests Passed")
st.sidebar.markdown("[📄 Download PDF Whitepaper](https://github.com/Krishna-neural/SupeRR_Selector_Season_2/raw/main/SupeRR_Selector_Season2_Methodology_Report.pdf)")

if menu == "🏆 Official Top-10 Rosters":
    st.subheader("Official Top-10 Pressure Leaderboards")
    st.caption("Locked selections for the Unstop competition submission portal.")
    
    disc = st.radio("Choose Discipline:", ["🏏 Top 10 Batters", "🎯 Top 10 Bowlers"], horizontal=True)
    if "Batters" in disc:
        cols_show = ["rank", "player_id", "player_name", "teams_represented", "primary_role", "pressure_balls", "pressure_sr", "expected_pressure_sr", "shrunk_pressure_vaoe", "lcb_80_floor", "extreme_crucible_vaoe", "shrunk_pressure_delta", "clutch_success_rate", "final_crr_score_100"]
        df_show = top_bat[cols_show].copy()
        df_show.columns = ["Rank", "Player ID", "Name", "Teams", "Role", "HP Balls", "HP SR", "Exp SR", "Shrunk VAOE", "LCB_80", "Ext VAOE", "Delta", "Win %", "CRR Score"]
        st.dataframe(df_show.style.format({
            "HP SR": "{:.2f}",
            "Exp SR": "{:.2f}",
            "Shrunk VAOE": "+{:.2f}",
            "LCB_80": "+{:.2f}",
            "Ext VAOE": "+{:.1f}",
            "Delta": "{:+.2f}",
            "Win %": "{:.1f}%",
            "CRR Score": "{:.2f}"
        }), use_container_width=True)

        st.markdown("### Top 10 Batters Evidence Cards")
        for _, r in top_bat.iterrows():
            with st.expander(f"#{int(r['rank'])}: {r['player_name']} (CRR: {r['final_crr_score_100']:.2f} | ID: {r['player_id']})"):
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Shrunk VAOE", f"+{r['shrunk_pressure_vaoe']:.2f}")
                c2.metric("LCB_80 Floor", f"+{r['lcb_80_floor']:.2f}")
                c3.metric("Clutch Delta", f"{r['shrunk_pressure_delta']:+.2f}")
                c4.metric("Clutch Win %", f"{r['clutch_success_rate']:.1f}%")
                st.write(f"**Tactical Signature:** {r['pace_vs_spin_vaoe']} | Top Stroke: {r['top_scoring_strokes']}")
    else:
        cols_show = ["rank", "player_id", "player_name", "teams_represented", "bowling_style", "pressure_legal_balls", "pressure_economy", "expected_pressure_economy", "pressure_econ_saved", "shrunk_pressure_vaoe", "lcb_80_floor", "extreme_crucible_vaoe", "shrunk_pressure_delta", "death_pressure_balls_pct", "final_crr_score_100"]
        df_show = top_bowl[cols_show].copy()
        df_show.columns = ["Rank", "Player ID", "Name", "Teams", "Discipline", "HP Balls", "HP Econ", "Exp Econ", "Econ Saved", "Shrunk VAOE", "LCB_80", "Ext VAOE", "Delta", "Death %", "CRR Score"]
        st.dataframe(df_show.style.format({
            "HP Econ": "{:.2f}",
            "Exp Econ": "{:.2f}",
            "Econ Saved": "+{:.2f}",
            "Shrunk VAOE": "+{:.2f}",
            "LCB_80": "+{:.2f}",
            "Ext VAOE": "+{:.1f}",
            "Delta": "{:+.2f}",
            "Death %": "{:.1f}%",
            "CRR Score": "{:.2f}"
        }), use_container_width=True)

        st.markdown("### Top 10 Bowlers Evidence Cards")
        for _, r in top_bowl.iterrows():
            with st.expander(f"#{int(r['rank'])}: {r['player_name']} (CRR: {r['final_crr_score_100']:.2f} | ID: {r['player_id']})"):
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Shrunk VAOE", f"+{r['shrunk_pressure_vaoe']:.2f}")
                c2.metric("LCB_80 Floor", f"+{r['lcb_80_floor']:.2f}")
                c3.metric("Clutch Delta", f"{r['shrunk_pressure_delta']:+.2f}")
                c4.metric("Econ Saved", f"+{r['pressure_econ_saved']:.2f} RPO")
                st.write(f"**Biomechanical:** {r['mean_bowl_speed']:.1f} km/h release. Yorker: {r['yorker_pct']:.1f}%, Bouncer: {r['bouncer_pct']:.1f}%, Dot%: {r['pressure_dot_pct']:.1f}%")

elif menu == "🔍 Player Scouting Explorer":
    st.subheader("Player Scouting Explorer & Head-to-Head Engine")
    disc = st.selectbox("Select Discipline:", ["Batters", "Bowlers"])
    df_active = all_bat if disc == "Batters" else all_bowl
    
    c1, c2 = st.columns(2)
    search = c1.text_input("Search Player or Team:", "")
    tier_filter = c2.selectbox("Filter Tier:", ["All Tiers", "Tier 1 (IPL)", "Tier 2 (T20I_FullMember)"])
    
    df_filtered = df_active.copy()
    if search:
        df_filtered = df_filtered[df_filtered["player_name"].str.contains(search, case=False, na=False) | df_filtered["teams_represented"].str.contains(search, case=False, na=False)]
    if tier_filter != "All Tiers":
        df_filtered = df_filtered[df_filtered["primary_comp_tier"] == tier_filter]
        
    st.write(f"Showing **{len(df_filtered)}** qualified players:")
    st.dataframe(df_filtered[["rank_crr", "player_name", "teams_represented", "primary_role", "pressure_balls", "shrunk_pressure_vaoe", "lcb_80", "shrunk_pressure_delta", "final_crr_score_100"]].rename(columns={
        "rank_crr": "Rank", "player_name": "Player", "teams_represented": "Teams", "primary_role": "Role", "pressure_balls": "Balls", "shrunk_pressure_vaoe": "Shrunk VAOE", "lcb_80": "LCB_80", "shrunk_pressure_delta": "Delta", "final_crr_score_100": "CRR"
    }), use_container_width=True)

elif menu == "🎯 RR Tactical Auction Matrix":
    st.subheader("Rajasthan Royals Tactical Auction & Squad-Fit Matrix")
    st.markdown(\"\"\"
    - **Bucket 1 — Current RR Core Validated by Model:** Vaibhav Sooryavanshi (#1 Batter, 100.0 CRR) and Yashasvi Jaiswal (#8 Batter, 90.5 CRR).
    - **Bucket 2 — Franchise-Locked Benchmarks:** Suryakumar Yadav (#2 Batter, 99.2 CRR), Virat Kohli (#9 Batter, 90.2 CRR), Jasprit Bumrah (#11 Bowler, 77.8 CRR), Rashid Khan (#12 Bowler, 77.4 CRR).
    - **Bucket 3 — High-Priority Realistic RR Auction Targets:** Lockie Ferguson (#1 Bowler, 100.0 CRR), Umran Malik (#2 Bowler, 97.2 CRR), Mahedi Hasan (#3 Bowler, 89.3 CRR), Reeza Hendricks (#3 Batter, 97.7 CRR), Pathum Nissanka (#4 Batter, 96.5 CRR), Ryan Rickelton (#5 Batter, 96.3 CRR), Nathan Ellis (#5 Bowler, 83.9 CRR).
    \"\"\")

elif menu == "📈 Evidence & Charts Gallery":
    st.subheader("Publication-Grade Charts Gallery (300 DPI)")
    charts = [
        "docs/charts/fig1_pressure_surface_and_entropy.png",
        "docs/charts/fig2_over_hazard_and_wicket_cost.png",
        "docs/charts/fig3_collinearity_and_orthogonality.png",
        "docs/charts/fig4_empirical_bayes_shrinkage_funnel.png",
        "docs/charts/fig5_top10_batters_evidence_dashboard.png",
        "docs/charts/fig6_top10_bowlers_evidence_dashboard.png",
        "docs/charts/fig7_pressure_vs_baseline_quadrant.png",
        "docs/charts/fig8_robustness_and_weight_sensitivity.png"
    ]
    for ch in charts:
        if os.path.exists(ch):
            st.image(ch, use_container_width=True)
"""
    app_py_path = os.path.join(base_dir, "app.py")
    with open(app_py_path, "w", encoding="utf-8") as f:
        f.write(st_app_code)
    print(f"Generated: {app_py_path}")

    req_path = os.path.join(base_dir, "requirements.txt")
    with open(req_path, "w", encoding="utf-8") as f:
        f.write("streamlit>=1.35.0\npandas>=2.2.0\nnumpy>=1.26.0\nplotly>=5.22.0\nmatplotlib>=3.8.0\nseaborn>=0.13.0\nscikit-learn>=1.4.0\nreportlab>=4.1.0\n")
    print(f"Generated: {req_path}")

    return out_index_path, app_py_path

if __name__ == "__main__":
    build_dashboard(".")

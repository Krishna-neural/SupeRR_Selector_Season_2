"""
Rajasthan Royals — SupeRR Selector Season 2
Interactive Streamlit Dashboard
Deployable on Streamlit Cloud (share.streamlit.io).
"""

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
st.markdown("""
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
""", unsafe_allow_html=True)

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
st.markdown("""
<div class="rr-header">
    <h1 style="margin:0; font-family:sans-serif; font-weight:800;">👑 RAJASTHAN ROYALS — SUPERR SELECTOR SEASON 2</h1>
    <h3 style="margin:4px 0 0 0; opacity:0.9;">Identifying The Most Reliable Players Under Pressure • CRR Engine</h3>
</div>
""", unsafe_allow_html=True)

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
    st.markdown("""
    - **Bucket 1 — Current RR Core Validated by Model:** Vaibhav Sooryavanshi (#1 Batter, 100.0 CRR) and Yashasvi Jaiswal (#8 Batter, 90.5 CRR).
    - **Bucket 2 — Franchise-Locked Benchmarks:** Suryakumar Yadav (#2 Batter, 99.2 CRR), Virat Kohli (#9 Batter, 90.2 CRR), Jasprit Bumrah (#11 Bowler, 77.8 CRR), Rashid Khan (#12 Bowler, 77.4 CRR).
    - **Bucket 3 — High-Priority Realistic RR Auction Targets:** Lockie Ferguson (#1 Bowler, 100.0 CRR), Umran Malik (#2 Bowler, 97.2 CRR), Mahedi Hasan (#3 Bowler, 89.3 CRR), Reeza Hendricks (#3 Batter, 97.7 CRR), Pathum Nissanka (#4 Batter, 96.5 CRR), Ryan Rickelton (#5 Batter, 96.3 CRR), Nathan Ellis (#5 Bowler, 83.9 CRR).
    """)

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

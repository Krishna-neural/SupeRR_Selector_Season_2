"""
SupeRR Selector Season 2 — Phase 8 Final Submission Quality Assurance Test Suite
25-Point Comprehensive Submission Verification covering raw dataset immutability,
300 DPI publication charts, 17-section Markdown report, PDF Whitepaper compilation,
RR Tactical Matrix, and Top-10 leaderboards integrity.
"""

import os
import re
import pytest
import pandas as pd


@pytest.fixture(scope="module")
def project_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class TestPhase8SubmissionQA:
    """25-Point Submission Quality Assurance Checklist."""

    # 1 - 6: Raw Data Integrity & Immutability (All 6 pristine raw files in Data/Raw/)
    def test_01_raw_matches_exists(self, project_root):
        path = os.path.join(project_root, "Data", "Raw", "matches.csv")
        assert os.path.exists(path) and os.path.getsize(path) > 10_000

    def test_02_raw_ball_by_ball_exists(self, project_root):
        path = os.path.join(project_root, "Data", "Raw", "ball_by_ball.csv")
        assert os.path.exists(path) and os.path.getsize(path) > 10_000_000

    def test_03_raw_teams_exists(self, project_root):
        path = os.path.join(project_root, "Data", "Raw", "teams.csv")
        assert os.path.exists(path) and os.path.getsize(path) > 500

    def test_04_raw_competitions_exists(self, project_root):
        path = os.path.join(project_root, "Data", "Raw", "competitions.csv")
        assert os.path.exists(path) and os.path.getsize(path) > 1_000

    def test_05_raw_competition_team_player_mapping_exists(self, project_root):
        path = os.path.join(project_root, "Data", "Raw", "competition_team_player_mapping.csv")
        assert os.path.exists(path) and os.path.getsize(path) > 10_000

    def test_06_raw_playing_eleven_exists(self, project_root):
        path = os.path.join(project_root, "Data", "Raw", "playing_eleven.csv")
        assert os.path.exists(path) and os.path.getsize(path) > 100_000

    def test_07_raw_corpus_row_counts_unmodified(self, project_root):
        m_path = os.path.join(project_root, "Data", "Raw", "matches.csv")
        d_path = os.path.join(project_root, "Data", "Raw", "ball_by_ball.csv")
        df_m = pd.read_csv(m_path)
        assert len(df_m) == 883, f"Expected 883 matches, found {len(df_m)}"
        # Check ball_by_ball row count without high memory overhead
        with open(d_path, "r", encoding="utf-8") as f:
            n_deliv = sum(1 for _ in f) - 1
        assert n_deliv == 200_999, f"Expected 200,999 deliveries, found {n_deliv}"

    # 8 - 15: High-Resolution 300 DPI Publication Charts in outputs/charts/
    def test_08_fig1_pressure_surface_chart(self, project_root):
        p = os.path.join(project_root, "outputs", "charts", "fig1_pressure_surface_and_entropy.png")
        assert os.path.exists(p) and os.path.getsize(p) > 30_000

    def test_09_fig2_over_hazard_chart(self, project_root):
        p = os.path.join(project_root, "outputs", "charts", "fig2_over_hazard_and_wicket_cost.png")
        assert os.path.exists(p) and os.path.getsize(p) > 30_000

    def test_10_fig3_collinearity_orthogonality_chart(self, project_root):
        p = os.path.join(project_root, "outputs", "charts", "fig3_collinearity_and_orthogonality.png")
        assert os.path.exists(p) and os.path.getsize(p) > 30_000

    def test_11_fig4_shrinkage_funnel_chart(self, project_root):
        p = os.path.join(project_root, "outputs", "charts", "fig4_empirical_bayes_shrinkage_funnel.png")
        assert os.path.exists(p) and os.path.getsize(p) > 30_000

    def test_12_fig5_top10_batters_dashboard_chart(self, project_root):
        p = os.path.join(project_root, "outputs", "charts", "fig5_top10_batters_evidence_dashboard.png")
        assert os.path.exists(p) and os.path.getsize(p) > 30_000

    def test_13_fig6_top10_bowlers_dashboard_chart(self, project_root):
        p = os.path.join(project_root, "outputs", "charts", "fig6_top10_bowlers_evidence_dashboard.png")
        assert os.path.exists(p) and os.path.getsize(p) > 30_000

    def test_14_fig7_pressure_baseline_quadrant_chart(self, project_root):
        p = os.path.join(project_root, "outputs", "charts", "fig7_pressure_vs_baseline_quadrant.png")
        assert os.path.exists(p) and os.path.getsize(p) > 30_000

    def test_15_fig8_robustness_sensitivity_chart(self, project_root):
        p = os.path.join(project_root, "outputs", "charts", "fig8_robustness_and_weight_sensitivity.png")
        assert os.path.exists(p) and os.path.getsize(p) > 30_000

    # 16 - 19: Reports Existence & Integrity
    def test_16_outputs_markdown_report_exists(self, project_root):
        p = os.path.join(project_root, "outputs", "reports", "final_methodology_report.md")
        assert os.path.exists(p) and os.path.getsize(p) > 10_000

    def test_17_root_markdown_report_exists(self, project_root):
        p = os.path.join(project_root, "final_methodology_report.md")
        assert os.path.exists(p) and os.path.getsize(p) > 10_000

    def test_18_outputs_pdf_whitepaper_exists(self, project_root):
        p = os.path.join(project_root, "outputs", "reports", "SupeRR_Selector_Season2_Methodology_Report.pdf")
        assert os.path.exists(p) and os.path.getsize(p) > 50_000

    def test_19_root_pdf_whitepaper_exists(self, project_root):
        p = os.path.join(project_root, "SupeRR_Selector_Season2_Methodology_Report.pdf")
        assert os.path.exists(p) and os.path.getsize(p) > 50_000

    # 20 - 21: Markdown Sections & RR Tactical Matrix
    def test_20_all_17_sections_present_in_report(self, project_root):
        p = os.path.join(project_root, "outputs", "reports", "final_methodology_report.md")
        with open(p, "r", encoding="utf-8") as f:
            content = f.read()

        for sec_num in range(1, 18):
            pattern = rf"^##\s+{sec_num}\.\s+"
            match = re.search(pattern, content, flags=re.MULTILINE)
            assert match is not None, f"Section {sec_num} missing from final_methodology_report.md"

    def test_21_rr_tactical_squad_fit_matrix_in_section_14(self, project_root):
        p = os.path.join(project_root, "outputs", "reports", "final_methodology_report.md")
        with open(p, "r", encoding="utf-8") as f:
            content = f.read()

        assert "14.2 Rajasthan Royals Tactical Squad-Fit & Auction Target Matrix" in content
        assert "Bucket 1 — Current RR Core Validated by Model" in content
        assert "Bucket 2 — Franchise-Locked Benchmarks" in content
        assert "Bucket 3 — High-Priority Realistic RR Auction" in content
        assert "Vaibhav Sooryavanshi" in content
        assert "Yashasvi Jaiswal" in content
        assert "Suryakumar Yadav" in content
        assert "Jasprit Bumrah" in content
        assert "Lockie Ferguson" in content
        assert "Umran Malik" in content
        assert "Mahedi Hasan" in content

    # 22 - 23: Top 10 Batters and Bowlers Dataframes Integrity
    def test_22_top_10_batters_compliance(self, project_root):
        p = os.path.join(project_root, "top_10_batters.csv")
        df = pd.read_csv(p)
        assert len(df) == 10
        assert list(df["rank"]) == list(range(1, 11))
        assert df["player_id"].nunique() == 10
        assert (df["pressure_balls"] >= 120).all()
        assert (df["final_crr_score_100"] >= 80.0).all()
        assert (df["lcb_80_floor"] > 0).all()

    def test_23_top_10_bowlers_compliance(self, project_root):
        p = os.path.join(project_root, "top_10_bowlers.csv")
        df = pd.read_csv(p)
        assert len(df) == 10
        assert list(df["rank"]) == list(range(1, 11))
        assert df["player_id"].nunique() == 10
        assert (df["pressure_legal_balls"] >= 120).all()
        assert (df["final_crr_score_100"] >= 75.0).all()
        assert (df["lcb_80_floor"] > 0).all()

    # 24: Rank Order & Player IDs in Report
    def test_24_top_players_rank_order_in_report(self, project_root):
        p_md = os.path.join(project_root, "outputs", "reports", "final_methodology_report.md")
        with open(p_md, "r", encoding="utf-8") as f:
            content = f.read()

        df_bat = pd.read_csv(os.path.join(project_root, "top_10_batters.csv"))
        df_bowl = pd.read_csv(os.path.join(project_root, "top_10_bowlers.csv"))

        # Check all batters appear with correct rank and player_id
        for _, r in df_bat.iterrows():
            assert f"#{int(r['rank'])}" in content
            assert str(r['player_id']) in content
            assert r['player_name'] in content

        # Check all bowlers appear with correct rank and player_id
        for _, r in df_bowl.iterrows():
            assert f"#{int(r['rank'])}" in content
            assert str(r['player_id']) in content
            assert r['player_name'] in content

    # 25: Unstop Dropdown ID Uniqueness Across Batters and Bowlers
    def test_25_zero_contradictory_player_duplicates(self, project_root):
        df_bat = pd.read_csv(os.path.join(project_root, "top_10_batters.csv"))
        df_bowl = pd.read_csv(os.path.join(project_root, "top_10_bowlers.csv"))
        bat_ids = set(df_bat["player_id"])
        bowl_ids = set(df_bowl["player_id"])
        overlap = bat_ids.intersection(bowl_ids)
        # Even if an all-rounder were present in both, verify IDs are distinct individuals
        assert len(overlap) == 0, f"Found overlapping player_ids: {overlap}"

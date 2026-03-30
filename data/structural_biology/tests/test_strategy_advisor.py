"""Tests for strategy_advisor.py — refinement strategy recommendations."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from strategy_advisor import (
    recommend_strategy,
    format_recommendation,
    XRAY_STRATEGIES,
    CRYOEM_STRATEGIES,
)


class TestStaticRecommendations(unittest.TestCase):
    """Test static strategy recommendations (no history)."""

    def test_high_res_xray(self):
        rec = recommend_strategy(1.2, "xray")
        self.assertIn("individual_sites", rec["strategy"])
        self.assertEqual(rec["confidence"], "static")

    def test_medium_res_xray(self):
        rec = recommend_strategy(2.5, "xray")
        self.assertIn("tls", rec["strategy"])

    def test_low_res_xray(self):
        rec = recommend_strategy(4.5, "xray")
        self.assertIn("rigid_body", rec["strategy"])

    def test_high_res_cryoem(self):
        rec = recommend_strategy(2.0, "cryo_em")
        self.assertIn("minimization_global", rec["strategy"])
        self.assertIn("expected_cc_range", rec)

    def test_low_res_cryoem(self):
        rec = recommend_strategy(6.0, "cryo_em")
        self.assertIn("rigid_body", rec["strategy"])

    def test_boundary_resolution(self):
        """Test at exact resolution boundaries."""
        rec_below = recommend_strategy(1.49, "xray")
        rec_above = recommend_strategy(1.50, "xray")
        # Both should return valid strategies
        self.assertIn("strategy", rec_below)
        self.assertIn("strategy", rec_above)

    def test_all_resolution_ranges_covered(self):
        """Every resolution from 0.5 to 10 should get a recommendation."""
        for res in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0, 8.0, 10.0]:
            rec = recommend_strategy(res, "xray")
            self.assertIn("strategy", rec)
            self.assertIsNotNone(rec["strategy"])

            rec_em = recommend_strategy(res, "cryo_em")
            self.assertIn("strategy", rec_em)
            self.assertIsNotNone(rec_em["strategy"])


class TestRecommendationOutput(unittest.TestCase):
    """Test recommendation output format."""

    def test_has_required_fields(self):
        rec = recommend_strategy(2.5, "xray")
        self.assertIn("resolution", rec)
        self.assertIn("method", rec)
        self.assertIn("strategy", rec)
        self.assertIn("notes", rec)
        self.assertIn("confidence", rec)
        self.assertIn("expected_cycles_range", rec)

    def test_xray_has_rfree_range(self):
        rec = recommend_strategy(2.5, "xray")
        self.assertIn("expected_rfree_range", rec)
        lo, hi = rec["expected_rfree_range"]
        self.assertLess(lo, hi)

    def test_cryoem_has_cc_range(self):
        rec = recommend_strategy(3.0, "cryo_em")
        self.assertIn("expected_cc_range", rec)
        lo, hi = rec["expected_cc_range"]
        self.assertLess(lo, hi)

    def test_json_output(self):
        rec = recommend_strategy(2.5, "xray")
        text = format_recommendation(rec, as_json=True)
        parsed = json.loads(text)
        self.assertEqual(parsed["resolution"], 2.5)

    def test_text_output(self):
        rec = recommend_strategy(2.5, "xray")
        text = format_recommendation(rec, as_json=False)
        self.assertIn("Strategy", text)
        self.assertIn("2.5", text)


class TestHistoricalScanning(unittest.TestCase):
    """Test scanning local projects for historical evidence."""

    def test_scan_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rec = recommend_strategy(2.5, "xray", staging_dir=tmpdir)
            self.assertEqual(rec["confidence"], "static")
            self.assertEqual(rec["historical_evidence"], [])

    def test_scan_with_matching_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from refinement_state import ProjectState

            # Create a completed project
            proj_dir = os.path.join(tmpdir, "struct_test")
            os.makedirs(proj_dir)
            state = ProjectState(proj_dir)
            state.method = "xray"
            state.set("resolution", 2.3)
            state.transition("refining")
            state.record_cycle_metrics(1, r_work=0.25, r_free=0.30,
                                       refinement_strategy="individual_sites+individual_adp+tls")
            state.record_cycle_metrics(2, r_work=0.22, r_free=0.27,
                                       refinement_strategy="individual_sites+individual_adp+tls")
            state.transition("converged")
            state.transition("complete")
            state.save()

            rec = recommend_strategy(2.5, "xray", staging_dir=tmpdir)
            self.assertEqual(rec["confidence"], "empirical")
            self.assertEqual(len(rec["historical_evidence"]), 1)
            self.assertEqual(rec["historical_evidence"][0]["project_id"], "struct_test")

    def test_scan_filters_by_method(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from refinement_state import ProjectState

            # Create a cryo-EM project
            proj_dir = os.path.join(tmpdir, "struct_em")
            os.makedirs(proj_dir)
            state = ProjectState(proj_dir)
            state.method = "cryo_em"
            state.set("resolution", 2.5)
            state.transition("refining")
            state.record_cycle_metrics(1, map_model_cc=0.7)
            state.save()

            # Query for X-ray should not find it
            rec = recommend_strategy(2.5, "xray", staging_dir=tmpdir)
            self.assertEqual(rec["historical_evidence"], [])


class TestStrategyTableConsistency(unittest.TestCase):
    """Verify strategy tables are well-formed."""

    def test_xray_ranges_contiguous(self):
        for i in range(len(XRAY_STRATEGIES) - 1):
            self.assertEqual(
                XRAY_STRATEGIES[i]["resolution_max"],
                XRAY_STRATEGIES[i + 1]["resolution_min"],
            )

    def test_cryoem_ranges_contiguous(self):
        for i in range(len(CRYOEM_STRATEGIES) - 1):
            self.assertEqual(
                CRYOEM_STRATEGIES[i]["resolution_max"],
                CRYOEM_STRATEGIES[i + 1]["resolution_min"],
            )

    def test_all_strategies_have_required_keys(self):
        for s in XRAY_STRATEGIES + CRYOEM_STRATEGIES:
            self.assertIn("strategy", s)
            self.assertIn("notes", s)
            self.assertIn("expected_cycles", s)


if __name__ == "__main__":
    unittest.main()

"""Tests for project_dashboard.py — multi-project status summary."""

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from project_dashboard import (
    scan_projects,
    format_table,
    format_json,
    STALE_DAYS,
)
from refinement_state import ProjectState


def _make_project(staging_dir, name, method="xray", resolution=2.0,
                   status="refining", n_cycles=3, **kwargs):
    """Helper to create a mock project."""
    proj_dir = os.path.join(staging_dir, name)
    os.makedirs(proj_dir, exist_ok=True)
    state = ProjectState(proj_dir)
    state.method = method
    state.set("resolution", resolution)

    # Walk through states to reach target
    if status in ("xtriage", "phasing", "building", "refining",
                   "awaiting_inspection", "converged", "complete"):
        if status != "new":
            state.transition("refining")
        if status == "awaiting_inspection":
            state.transition("awaiting_inspection")
        elif status == "converged":
            state.transition("converged")
        elif status == "complete":
            state.transition("converged")
            state.transition("complete")

    for i in range(1, n_cycles + 1):
        state.record_cycle_metrics(
            i,
            r_work=0.30 - i * 0.02,
            r_free=0.35 - i * 0.02,
            molprobity_score=2.5 - i * 0.2,
        )

    state.save()

    # Override last_updated after save (save sets it to now)
    if "last_updated" in kwargs:
        import json as _json
        notes_path = os.path.join(proj_dir, "project_notes.json")
        with open(notes_path) as f:
            data = _json.load(f)
        data["last_updated"] = kwargs["last_updated"]
        with open(notes_path, "w") as f:
            _json.dump(data, f, indent=2)

    return state


class TestScanProjects(unittest.TestCase):
    """Test scanning for projects."""

    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            summaries = scan_projects(tmpdir)
            self.assertEqual(len(summaries), 0)

    def test_nonexistent_directory(self):
        summaries = scan_projects("/nonexistent/path")
        self.assertEqual(len(summaries), 0)

    def test_finds_projects(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _make_project(tmpdir, "struct_a")
            _make_project(tmpdir, "struct_b")
            _make_project(tmpdir, "struct_c")

            summaries = scan_projects(tmpdir)
            self.assertEqual(len(summaries), 3)

    def test_skips_non_projects(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _make_project(tmpdir, "struct_a")
            # Create a non-project directory
            os.makedirs(os.path.join(tmpdir, "not_a_project"))

            summaries = scan_projects(tmpdir)
            self.assertEqual(len(summaries), 1)

    def test_summary_has_required_fields(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _make_project(tmpdir, "struct_test", resolution=1.8)

            summaries = scan_projects(tmpdir)
            s = summaries[0]

            self.assertEqual(s["project_id"], "struct_test")
            self.assertEqual(s["method"], "xray")
            self.assertAlmostEqual(s["resolution"], 1.8)
            self.assertIn("status", s)
            self.assertIn("cycle", s)
            self.assertIn("r_free", s)
            self.assertIn("molprobity", s)

    def test_latest_metrics_included(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _make_project(tmpdir, "struct_test", n_cycles=3)

            summaries = scan_projects(tmpdir)
            s = summaries[0]

            # Should have metrics from cycle 3
            self.assertIsNotNone(s["r_free"])
            self.assertIsNotNone(s["molprobity"])


class TestStaleDetection(unittest.TestCase):
    """Test detection of stalled projects."""

    def test_recent_project_not_stale(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _make_project(tmpdir, "recent", status="awaiting_inspection")

            summaries = scan_projects(tmpdir)
            self.assertFalse(summaries[0]["stale"])

    def test_old_awaiting_is_stale(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            old_date = (datetime.now() - timedelta(days=STALE_DAYS + 1)).isoformat()
            _make_project(tmpdir, "old", status="awaiting_inspection",
                          last_updated=old_date)

            summaries = scan_projects(tmpdir)
            self.assertTrue(summaries[0]["stale"])
            self.assertIn("days", summaries[0]["stale_reason"])

    def test_completed_not_stale(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            old_date = (datetime.now() - timedelta(days=30)).isoformat()
            _make_project(tmpdir, "done", status="complete",
                          last_updated=old_date)

            summaries = scan_projects(tmpdir)
            self.assertFalse(summaries[0]["stale"])


class TestFormatting(unittest.TestCase):
    """Test output formatting."""

    def test_empty_table(self):
        result = format_table([])
        self.assertIn("No projects", result)

    def test_table_has_headers(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _make_project(tmpdir, "test")
            summaries = scan_projects(tmpdir)
            table = format_table(summaries)
            self.assertIn("Project", table)
            self.assertIn("Method", table)
            self.assertIn("Status", table)

    def test_json_output(self):
        summaries = [
            {"project_id": "test", "method": "xray", "status": "refining",
             "resolution": 2.0, "cycle": 3, "r_work": 0.22, "r_free": 0.27,
             "map_model_cc": None, "molprobity": 1.8, "created": "2026-03-14",
             "last_updated": "2026-03-14", "stale": False, "stale_reason": None},
        ]
        text = format_json(summaries)
        parsed = json.loads(text)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["project_id"], "test")


class TestMultipleProjectTypes(unittest.TestCase):
    """Test dashboard with mixed project types."""

    def test_mixed_methods(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _make_project(tmpdir, "xray_proj", method="xray", resolution=1.8)
            _make_project(tmpdir, "em_proj", method="cryo_em", resolution=3.5)

            summaries = scan_projects(tmpdir)
            methods = {s["method"] for s in summaries}
            self.assertEqual(methods, {"xray", "cryo_em"})

    def test_mixed_statuses(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _make_project(tmpdir, "active", status="refining")
            _make_project(tmpdir, "waiting", status="awaiting_inspection")
            _make_project(tmpdir, "done", status="complete")

            summaries = scan_projects(tmpdir)
            statuses = {s["status"] for s in summaries}
            self.assertEqual(statuses, {"refining", "awaiting_inspection", "complete"})


if __name__ == "__main__":
    unittest.main()

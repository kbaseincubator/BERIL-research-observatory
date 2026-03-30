"""Tests for run_pipeline.py — pipeline orchestration logic."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from run_pipeline import (
    ensure_project_dir,
    load_project_state,
    save_project_state,
    log_provenance,
    get_latest_cycle,
)


class TestProjectDirectory(unittest.TestCase):
    """Test project directory creation and structure."""

    def test_create_project_dir(self):
        """Project directory is created with expected subdirectories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = ensure_project_dir("test_project", staging=tmpdir)

            self.assertTrue(os.path.isdir(project_dir))
            for subdir in ["input", "cycles", "scripts", "figures", "final"]:
                self.assertTrue(
                    os.path.isdir(os.path.join(project_dir, subdir)),
                    f"Missing subdirectory: {subdir}",
                )

    def test_idempotent_creation(self):
        """Creating project dir twice doesn't fail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ensure_project_dir("test_project", staging=tmpdir)
            ensure_project_dir("test_project", staging=tmpdir)


class TestProjectState(unittest.TestCase):
    """Test project state persistence."""

    def test_new_project_state(self):
        """New project returns default state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state = load_project_state(tmpdir)
            self.assertEqual(state["status"], "new")
            self.assertEqual(state["current_cycle"], 0)
            self.assertEqual(state["steps_completed"], [])

    def test_save_and_load(self):
        """State persists across save/load cycles."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state = {
                "project_id": "test",
                "status": "in_progress",
                "current_cycle": 3,
                "steps_completed": ["xtriage", "phaser"],
                "method": "xray",
            }
            save_project_state(tmpdir, state)

            loaded = load_project_state(tmpdir)
            self.assertEqual(loaded["status"], "in_progress")
            self.assertEqual(loaded["current_cycle"], 3)
            self.assertEqual(loaded["steps_completed"], ["xtriage", "phaser"])

    def test_state_roundtrip_preserves_all_fields(self):
        """All fields survive save/load."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state = {
                "project_id": "test",
                "status": "completed",
                "current_cycle": 5,
                "steps_completed": ["xtriage", "phaser", "autobuild", "refine"],
                "method": "xray",
                "resolution": 1.8,
                "custom_field": "value",
            }
            save_project_state(tmpdir, state)
            loaded = load_project_state(tmpdir)
            self.assertEqual(loaded, state)


class TestProvenance(unittest.TestCase):
    """Test provenance logging."""

    def test_log_provenance(self):
        """Provenance records are appended as JSONL."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_provenance(tmpdir, "test_action", "test_tool", metrics={"score": 1.5})
            log_provenance(tmpdir, "second_action", "other_tool")

            prov_path = os.path.join(tmpdir, "provenance.jsonl")
            self.assertTrue(os.path.exists(prov_path))

            with open(prov_path) as f:
                lines = f.readlines()
            self.assertEqual(len(lines), 2)

            record1 = json.loads(lines[0])
            self.assertEqual(record1["action"], "test_action")
            self.assertEqual(record1["tool"], "test_tool")
            self.assertEqual(record1["metrics"]["score"], 1.5)
            self.assertIn("timestamp", record1)

            record2 = json.loads(lines[1])
            self.assertEqual(record2["action"], "second_action")

    def test_provenance_with_all_fields(self):
        """All optional provenance fields are recorded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_provenance(
                tmpdir,
                action="refinement",
                tool="phenix.refine",
                parameters={"strategy": "tls"},
                metrics={"r_free": 0.25},
                input_model="model_in.pdb",
                output_model="model_out.pdb",
                notes="Added TLS groups",
            )

            prov_path = os.path.join(tmpdir, "provenance.jsonl")
            with open(prov_path) as f:
                record = json.loads(f.readline())

            self.assertEqual(record["parameters"]["strategy"], "tls")
            self.assertEqual(record["metrics"]["r_free"], 0.25)
            self.assertEqual(record["input_model"], "model_in.pdb")
            self.assertEqual(record["output_model"], "model_out.pdb")
            self.assertEqual(record["decision_rationale"], "Added TLS groups")


class TestCycleTracking(unittest.TestCase):
    """Test refinement cycle number tracking."""

    def test_no_cycles(self):
        """No cycles directory returns 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self.assertEqual(get_latest_cycle(tmpdir), 0)

    def test_empty_cycles_dir(self):
        """Empty cycles directory returns 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, "cycles"))
            self.assertEqual(get_latest_cycle(tmpdir), 0)

    def test_multiple_cycles(self):
        """Returns highest cycle number."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cycles_dir = os.path.join(tmpdir, "cycles")
            for n in [1, 2, 3, 5]:
                os.makedirs(os.path.join(cycles_dir, f"cycle_{n:03d}"))
            self.assertEqual(get_latest_cycle(tmpdir), 5)

    def test_non_sequential_cycles(self):
        """Handles gaps in cycle numbers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cycles_dir = os.path.join(tmpdir, "cycles")
            for n in [1, 3, 7]:
                os.makedirs(os.path.join(cycles_dir, f"cycle_{n:03d}"))
            self.assertEqual(get_latest_cycle(tmpdir), 7)


if __name__ == "__main__":
    unittest.main()

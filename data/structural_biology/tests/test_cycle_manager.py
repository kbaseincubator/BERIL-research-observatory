"""Tests for cycle_manager.py — convergence detection and model management."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from refinement_state import ProjectState
from cycle_manager import check_convergence, accept_rebuilt_model


class TestConvergenceDetection(unittest.TestCase):
    """Test refinement convergence analysis."""

    def _make_state(self, tmpdir, metrics_list):
        """Helper: create a ProjectState with pre-loaded cycle metrics."""
        state = ProjectState(tmpdir)
        state.method = "xray"
        state.transition("refining")
        for m in metrics_list:
            state.record_cycle_metrics(**m)
        return state

    def test_too_few_cycles(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state = self._make_state(tmpdir, [
                {"cycle_num": 1, "r_work": 0.30, "r_free": 0.35},
            ])
            converged, reason, rec = check_convergence(state)
            self.assertFalse(converged)
            self.assertIn("Too few", reason)

    def test_rfree_plateau_converged(self):
        """R-free not changing = converged."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state = self._make_state(tmpdir, [
                {"cycle_num": 1, "r_work": 0.22, "r_free": 0.27},
                {"cycle_num": 2, "r_work": 0.215, "r_free": 0.2695},
                {"cycle_num": 3, "r_work": 0.214, "r_free": 0.2693},
            ])
            converged, reason, rec = check_convergence(state)
            self.assertTrue(converged)
            self.assertIn("plateau", reason.lower())

    def test_still_improving(self):
        """R-free still dropping significantly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state = self._make_state(tmpdir, [
                {"cycle_num": 1, "r_work": 0.30, "r_free": 0.35},
                {"cycle_num": 2, "r_work": 0.25, "r_free": 0.30},
                {"cycle_num": 3, "r_work": 0.22, "r_free": 0.27},
            ])
            converged, reason, rec = check_convergence(state)
            self.assertFalse(converged)

    def test_overfitting_detected(self):
        """R-gap too large = overfitting warning."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state = self._make_state(tmpdir, [
                {"cycle_num": 1, "r_work": 0.18, "r_free": 0.28},
                {"cycle_num": 2, "r_work": 0.15, "r_free": 0.29},
            ])
            converged, reason, rec = check_convergence(state)
            self.assertFalse(converged)
            self.assertIn("R-gap", reason)

    def test_rfree_getting_worse(self):
        """R-free increasing between cycles."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state = self._make_state(tmpdir, [
                {"cycle_num": 1, "r_work": 0.22, "r_free": 0.27},
                {"cycle_num": 2, "r_work": 0.20, "r_free": 0.25},
                {"cycle_num": 3, "r_work": 0.19, "r_free": 0.26},  # R-free went up
            ])
            converged, reason, rec = check_convergence(state)
            self.assertFalse(converged)
            self.assertIn("increased", reason.lower())

    def test_cryoem_cc_convergence(self):
        """Map-model CC plateau for cryo-EM."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state = ProjectState(tmpdir)
            state.method = "cryo_em"
            state.transition("refining")
            state.record_cycle_metrics(1, map_model_cc=0.65)
            state.record_cycle_metrics(2, map_model_cc=0.653)
            state.record_cycle_metrics(3, map_model_cc=0.654)

            converged, reason, rec = check_convergence(state)
            self.assertTrue(converged)
            self.assertIn("CC", reason)


class TestAcceptRebuiltModel(unittest.TestCase):
    """Test accepting a rebuilt model from the user."""

    def test_accept_model(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Set up project
            state = ProjectState(tmpdir)
            state.transition("refining")
            state.record_cycle_metrics(1, r_work=0.25, r_free=0.30)
            state.transition("awaiting_inspection")
            state.save()

            # Create a fake rebuilt model
            fake_model = os.path.join(tmpdir, "rebuilt.pdb")
            with open(fake_model, "w") as f:
                f.write("ATOM      1  N   ALA A   1      10.0  20.0  30.0  1.00 85.0           N\nEND\n")

            # Create cycles dir
            os.makedirs(os.path.join(tmpdir, "cycles"), exist_ok=True)

            next_cycle = accept_rebuilt_model(tmpdir, fake_model, notes="Fixed Leu45")

            self.assertEqual(next_cycle, 2)

            # Check state was updated
            loaded = ProjectState.load(tmpdir)
            self.assertEqual(loaded.status, "refining")

            # Check model was copied
            dest = os.path.join(tmpdir, "cycles", "cycle_002", "model_rebuilt.pdb")
            self.assertTrue(os.path.exists(dest))

    def test_accept_creates_provenance(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state = ProjectState(tmpdir)
            state.transition("refining")
            state.record_cycle_metrics(1, r_work=0.25, r_free=0.30)
            state.transition("awaiting_inspection")
            state.save()

            fake_model = os.path.join(tmpdir, "rebuilt.pdb")
            with open(fake_model, "w") as f:
                f.write("END\n")

            os.makedirs(os.path.join(tmpdir, "cycles"), exist_ok=True)
            accept_rebuilt_model(tmpdir, fake_model)

            prov_path = os.path.join(tmpdir, "provenance.jsonl")
            self.assertTrue(os.path.exists(prov_path))
            with open(prov_path) as f:
                record = json.loads(f.readline())
            self.assertEqual(record["action"], "accept_rebuilt_model")
            self.assertEqual(record["tool"], "human")


if __name__ == "__main__":
    unittest.main()

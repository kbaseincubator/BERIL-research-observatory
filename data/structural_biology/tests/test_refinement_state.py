"""Tests for refinement_state.py — project lifecycle state machine."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from refinement_state import ProjectState, InvalidTransition, STATES, TRANSITIONS


class TestProjectStateCreation(unittest.TestCase):
    """Test creating and loading project state."""

    def test_new_state(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state = ProjectState(tmpdir)
            self.assertEqual(state.status, "new")
            self.assertEqual(state.current_cycle, 0)
            self.assertIsNone(state.method)

    def test_load_nonexistent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state = ProjectState.load(tmpdir)
            self.assertEqual(state.status, "new")

    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state = ProjectState(tmpdir)
            state.method = "xray"
            state.transition("xtriage")
            state.save()

            loaded = ProjectState.load(tmpdir)
            self.assertEqual(loaded.status, "xtriage")
            self.assertEqual(loaded.method, "xray")

    def test_project_id(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state = ProjectState(tmpdir)
            self.assertEqual(state.project_id, os.path.basename(tmpdir))


class TestStateTransitions(unittest.TestCase):
    """Test valid and invalid state transitions."""

    def test_valid_forward_transitions(self):
        """Test a full valid pipeline path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state = ProjectState(tmpdir)
            state.transition("xtriage")
            self.assertEqual(state.status, "xtriage")
            state.transition("phasing")
            self.assertEqual(state.status, "phasing")
            state.transition("building")
            self.assertEqual(state.status, "building")
            state.transition("refining")
            self.assertEqual(state.status, "refining")
            state.transition("awaiting_inspection")
            self.assertEqual(state.status, "awaiting_inspection")
            state.transition("refining")  # another cycle
            self.assertEqual(state.status, "refining")
            state.transition("converged")
            self.assertEqual(state.status, "converged")
            state.transition("complete")
            self.assertEqual(state.status, "complete")

    def test_invalid_transition_raises(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state = ProjectState(tmpdir)
            with self.assertRaises(InvalidTransition):
                state.transition("converged")  # can't go from new to converged

    def test_unknown_state_raises(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state = ProjectState(tmpdir)
            with self.assertRaises(InvalidTransition):
                state.transition("invalid_state")

    def test_complete_is_terminal(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state = ProjectState(tmpdir)
            state.transition("complete")
            with self.assertRaises(InvalidTransition):
                state.transition("refining")

    def test_skip_to_refining(self):
        """Can go directly from new to refining (e.g., AlphaFold-only validation)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state = ProjectState(tmpdir)
            state.transition("refining")
            self.assertEqual(state.status, "refining")

    def test_converged_can_resume(self):
        """Can go from converged back to refining."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state = ProjectState(tmpdir)
            state.transition("refining")
            state.transition("converged")
            state.transition("refining")  # resume
            self.assertEqual(state.status, "refining")

    def test_all_transitions_valid(self):
        """All defined transitions are between valid states."""
        for from_state, to_states in TRANSITIONS.items():
            self.assertIn(from_state, STATES)
            for to_state in to_states:
                self.assertIn(to_state, STATES)


class TestCycleMetrics(unittest.TestCase):
    """Test recording and querying cycle metrics."""

    def test_record_metrics(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state = ProjectState(tmpdir)
            state.record_cycle_metrics(1, r_work=0.25, r_free=0.30)
            state.record_cycle_metrics(2, r_work=0.22, r_free=0.27)

            self.assertEqual(state.current_cycle, 2)
            self.assertEqual(len(state.cycle_metrics), 2)

    def test_get_latest_metrics(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state = ProjectState(tmpdir)
            state.record_cycle_metrics(1, r_work=0.25, r_free=0.30)
            state.record_cycle_metrics(2, r_work=0.22, r_free=0.27)

            latest = state.get_latest_metrics()
            self.assertEqual(latest["cycle"], 2)
            self.assertAlmostEqual(latest["r_work"], 0.22)

    def test_get_latest_no_metrics(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state = ProjectState(tmpdir)
            self.assertIsNone(state.get_latest_metrics())

    def test_get_metrics_history(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state = ProjectState(tmpdir)
            state.record_cycle_metrics(1, r_free=0.30, molprobity_score=2.5)
            state.record_cycle_metrics(2, r_free=0.27, molprobity_score=2.0)
            state.record_cycle_metrics(3, r_free=0.25, molprobity_score=1.8)

            history = state.get_metrics_history("r_free")
            self.assertEqual(len(history), 3)
            self.assertAlmostEqual(history[0][1], 0.30)
            self.assertAlmostEqual(history[2][1], 0.25)

    def test_metrics_persist(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state = ProjectState(tmpdir)
            state.record_cycle_metrics(1, r_work=0.25, r_free=0.30)
            state.save()

            loaded = ProjectState.load(tmpdir)
            self.assertEqual(len(loaded.cycle_metrics), 1)
            self.assertAlmostEqual(loaded.cycle_metrics[0]["r_work"], 0.25)


class TestWaitingState(unittest.TestCase):
    """Test human-in-the-loop state checks."""

    def test_is_waiting(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state = ProjectState(tmpdir)
            self.assertFalse(state.is_waiting_for_human())
            state.transition("refining")
            state.transition("awaiting_inspection")
            self.assertTrue(state.is_waiting_for_human())

    def test_is_terminal(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state = ProjectState(tmpdir)
            self.assertFalse(state.is_terminal())
            state.transition("complete")
            self.assertTrue(state.is_terminal())


class TestAdvance(unittest.TestCase):
    """Test the advance() recommendation method."""

    def test_advance_new(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state = ProjectState(tmpdir)
            action, reason = state.advance()
            self.assertEqual(action, "run_xtriage")

    def test_advance_awaiting(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state = ProjectState(tmpdir)
            state.transition("refining")
            state.transition("awaiting_inspection")
            action, reason = state.advance()
            self.assertEqual(action, "wait_for_human")

    def test_advance_converged(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state = ProjectState(tmpdir)
            state.transition("refining")
            state.transition("converged")
            action, reason = state.advance()
            self.assertEqual(action, "finalize")

    def test_advance_complete(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state = ProjectState(tmpdir)
            state.transition("complete")
            action, reason = state.advance()
            self.assertEqual(action, "done")


class TestSummary(unittest.TestCase):
    """Test summary output."""

    def test_summary_contains_key_info(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state = ProjectState(tmpdir)
            state.method = "xray"
            state.transition("refining")
            state.record_cycle_metrics(1, r_work=0.25, r_free=0.30)

            summary = state.summary()
            self.assertIn("xray", summary)
            self.assertIn("refining", summary)
            self.assertIn("r_work", summary)


if __name__ == "__main__":
    unittest.main()

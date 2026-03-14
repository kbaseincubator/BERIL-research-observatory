"""Tests for generate_figures.py — publication figure generation."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from generate_figures import (
    generate_plddt_heatmap,
    generate_quality_summary,
    generate_batch_histogram,
    generate_strategy_comparison,
    HAS_MATPLOTLIB,
)

# Skip all tests if matplotlib is not available
SKIP_REASON = "matplotlib not available"


def _make_pdb(filepath, n_residues=50):
    """Create a minimal PDB with CA atoms and varying B-factors."""
    with open(filepath, "w") as f:
        for i in range(1, n_residues + 1):
            plddt = 50 + (i / n_residues) * 45  # Range from ~50 to ~95
            f.write(
                f"ATOM  {i:5d}  CA  ALA A{i:4d}    "
                f"{10.0 + i:8.3f}{20.0:8.3f}{30.0:8.3f}"
                f"  1.00{plddt:6.2f}           C\n"
            )
        f.write("END\n")


def _make_project(project_dir, n_cycles=5):
    """Create a mock project with cycle metrics."""
    from refinement_state import ProjectState

    state = ProjectState(project_dir)
    state.method = "xray"
    state.set("resolution", 2.0)
    state.transition("refining")

    for i in range(1, n_cycles + 1):
        state.record_cycle_metrics(
            i,
            r_work=0.30 - i * 0.02,
            r_free=0.35 - i * 0.02,
            molprobity_score=2.5 - i * 0.2,
            clash_score=10 - i * 1.5,
            ramachandran_favored=94 + i * 0.8,
            ramachandran_outliers=1.0 - i * 0.15,
            rotamer_outliers=3.0 - i * 0.4,
        )

    state.save()
    return state


@unittest.skipUnless(HAS_MATPLOTLIB, SKIP_REASON)
class TestPlddtHeatmap(unittest.TestCase):
    """Test pLDDT heatmap generation."""

    def test_generates_png(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pdb_path = os.path.join(tmpdir, "model.pdb")
            _make_pdb(pdb_path, n_residues=30)

            output = os.path.join(tmpdir, "plddt.png")
            result = generate_plddt_heatmap(pdb_path, output)

            self.assertIsNotNone(result)
            self.assertTrue(os.path.exists(output))
            self.assertGreater(os.path.getsize(output), 0)

    def test_empty_pdb_returns_none(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pdb_path = os.path.join(tmpdir, "empty.pdb")
            with open(pdb_path, "w") as f:
                f.write("END\n")

            result = generate_plddt_heatmap(pdb_path, os.path.join(tmpdir, "out.png"))
            self.assertIsNone(result)


@unittest.skipUnless(HAS_MATPLOTLIB, SKIP_REASON)
class TestQualitySummary(unittest.TestCase):
    """Test multi-panel quality summary."""

    def test_generates_png(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _make_project(tmpdir, n_cycles=4)

            output = os.path.join(tmpdir, "summary.png")
            result = generate_quality_summary(tmpdir, output)

            self.assertIsNotNone(result)
            self.assertTrue(os.path.exists(output))

    def test_no_metrics_returns_none(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from refinement_state import ProjectState
            state = ProjectState(tmpdir)
            state.save()

            result = generate_quality_summary(tmpdir, os.path.join(tmpdir, "out.png"))
            self.assertIsNone(result)


@unittest.skipUnless(HAS_MATPLOTLIB, SKIP_REASON)
class TestBatchHistogram(unittest.TestCase):
    """Test batch validation histogram."""

    def test_generates_png(self):
        import csv

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a summary.tsv
            summary_path = os.path.join(tmpdir, "summary.tsv")
            with open(summary_path, "w", newline="") as f:
                writer = csv.writer(f, delimiter="\t")
                writer.writerow(["name", "n_residues", "mean_plddt", "quality",
                                 "plddt_very_high", "plddt_high", "plddt_low", "plddt_very_low"])
                for i in range(20):
                    writer.writerow([f"model_{i}", 100 + i * 10, 70 + i * 1.5, "high",
                                     30, 50, 15, 5])

            output = os.path.join(tmpdir, "histogram.png")
            result = generate_batch_histogram(tmpdir, output)

            self.assertIsNotNone(result)
            self.assertTrue(os.path.exists(output))

    def test_missing_summary_returns_none(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = generate_batch_histogram(tmpdir)
            self.assertIsNone(result)


@unittest.skipUnless(HAS_MATPLOTLIB, SKIP_REASON)
class TestStrategyComparison(unittest.TestCase):
    """Test strategy comparison chart."""

    def test_generates_png(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create two projects with different strategies
            for name, strategy in [("proj_a", "tls"), ("proj_b", "individual_adp")]:
                proj_dir = os.path.join(tmpdir, name)
                os.makedirs(proj_dir)
                from refinement_state import ProjectState
                state = ProjectState(proj_dir)
                state.method = "xray"
                state.transition("refining")
                state.record_cycle_metrics(1, r_work=0.22, r_free=0.27,
                                           refinement_strategy=strategy)
                state.save()

            output = os.path.join(tmpdir, "comparison.png")
            result = generate_strategy_comparison(tmpdir, output)

            self.assertIsNotNone(result)
            self.assertTrue(os.path.exists(output))

    def test_no_projects_returns_none(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = generate_strategy_comparison(tmpdir)
            self.assertIsNone(result)


class TestWithoutMatplotlib(unittest.TestCase):
    """Test graceful handling when matplotlib is not available."""

    def test_module_loads(self):
        """Module should load even if matplotlib is missing."""
        import generate_figures
        self.assertIsNotNone(generate_figures)


if __name__ == "__main__":
    unittest.main()

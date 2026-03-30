"""Tests for batch_validate.py — batch structure validation."""

import csv
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from batch_validate import (
    validate_pdb_file,
    batch_validate_pdbs,
    write_summary_tsv,
    write_batch_stats,
)


def _make_pdb(filepath, n_residues=10, mean_plddt=85.0):
    """Create a minimal PDB file with CA atoms."""
    with open(filepath, "w") as f:
        for i in range(1, n_residues + 1):
            plddt = mean_plddt + (i % 5 - 2) * 5  # vary around mean
            f.write(
                f"ATOM  {i:5d}  CA  ALA A{i:4d}    "
                f"{10.0 + i:8.3f}{20.0:8.3f}{30.0:8.3f}"
                f"  1.00{plddt:6.2f}           C\n"
            )
        # Also write N atoms (not CA) with same pLDDT
        for i in range(1, n_residues + 1):
            plddt = mean_plddt + (i % 5 - 2) * 5
            f.write(
                f"ATOM  {n_residues + i:5d}  N   ALA A{i:4d}    "
                f"{10.0 + i:8.3f}{21.0:8.3f}{30.0:8.3f}"
                f"  1.00{plddt:6.2f}           N\n"
            )
        f.write("END\n")


class TestValidatePdbFile(unittest.TestCase):
    """Test single PDB validation."""

    def test_high_confidence_model(self):
        with tempfile.NamedTemporaryFile(suffix=".pdb", mode="w", delete=False) as f:
            _make_pdb(f.name, n_residues=20, mean_plddt=92.0)
            report = validate_pdb_file(f.name)
        os.unlink(f.name)

        self.assertEqual(report["n_residues"], 20)
        self.assertGreater(report["mean_plddt"], 80)
        self.assertIn("quality", report)
        self.assertIn("plddt_distribution", report)

    def test_low_confidence_model(self):
        with tempfile.NamedTemporaryFile(suffix=".pdb", mode="w", delete=False) as f:
            _make_pdb(f.name, n_residues=10, mean_plddt=35.0)
            report = validate_pdb_file(f.name)
        os.unlink(f.name)

        self.assertEqual(report["quality"], "very_low")

    def test_report_has_required_fields(self):
        with tempfile.NamedTemporaryFile(suffix=".pdb", mode="w", delete=False) as f:
            _make_pdb(f.name)
            report = validate_pdb_file(f.name)
        os.unlink(f.name)

        for field in ["model", "name", "n_residues", "mean_plddt", "quality",
                       "plddt_distribution", "validation_date"]:
            self.assertIn(field, report)


class TestBatchValidation(unittest.TestCase):
    """Test batch PDB validation."""

    def test_batch_multiple_pdbs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create 3 PDB files
            for name, plddt in [("model_a", 92.0), ("model_b", 75.0), ("model_c", 45.0)]:
                _make_pdb(os.path.join(tmpdir, f"{name}.pdb"), n_residues=15, mean_plddt=plddt)

            pdb_files = sorted([
                os.path.join(tmpdir, f) for f in os.listdir(tmpdir) if f.endswith(".pdb")
            ])

            outdir = os.path.join(tmpdir, "results")
            reports = batch_validate_pdbs(pdb_files, outdir)

            self.assertEqual(len(reports), 3)
            # Per-structure JSON reports should exist
            for r in reports:
                name = r["name"]
                self.assertTrue(os.path.exists(
                    os.path.join(outdir, f"{name}_report.json")
                ))


class TestSummaryTsv(unittest.TestCase):
    """Test summary TSV generation."""

    def test_write_summary(self):
        reports = [
            {"name": "model_a", "n_residues": 100, "mean_plddt": 92.0,
             "quality": "very_high", "plddt_distribution": {"very_high": 80, "high": 20, "low": 0, "very_low": 0}},
            {"name": "model_b", "n_residues": 200, "mean_plddt": 75.0,
             "quality": "high", "plddt_distribution": {"very_high": 10, "high": 70, "low": 20, "very_low": 0}},
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "summary.tsv")
            write_summary_tsv(reports, path)

            self.assertTrue(os.path.exists(path))
            with open(path) as f:
                reader = csv.DictReader(f, delimiter="\t")
                rows = list(reader)

            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["name"], "model_a")

    def test_skips_errored_reports(self):
        reports = [
            {"name": "good", "n_residues": 100, "mean_plddt": 92.0,
             "quality": "very_high", "plddt_distribution": {"very_high": 100, "high": 0, "low": 0, "very_low": 0}},
            {"name": "bad", "error": "file not found"},
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "summary.tsv")
            write_summary_tsv(reports, path)

            with open(path) as f:
                reader = csv.DictReader(f, delimiter="\t")
                rows = list(reader)
            self.assertEqual(len(rows), 1)


class TestBatchStats(unittest.TestCase):
    """Test batch statistics generation."""

    def test_write_stats(self):
        reports = [
            {"name": "a", "n_residues": 100, "mean_plddt": 92.0, "quality": "very_high"},
            {"name": "b", "n_residues": 200, "mean_plddt": 75.0, "quality": "high"},
            {"name": "c", "n_residues": 150, "mean_plddt": 45.0, "quality": "very_low"},
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            stats = write_batch_stats(reports, tmpdir)

            self.assertIsNotNone(stats)
            self.assertEqual(stats["total_structures"], 3)
            self.assertEqual(stats["successful"], 3)
            self.assertAlmostEqual(stats["plddt_mean"], (92 + 75 + 45) / 3, places=1)
            self.assertEqual(stats["quality_distribution"]["very_high"], 1)
            self.assertEqual(stats["quality_distribution"]["high"], 1)

            # Check JSON was written
            stats_path = os.path.join(tmpdir, "batch_stats.json")
            self.assertTrue(os.path.exists(stats_path))

    def test_handles_failed_reports(self):
        reports = [
            {"name": "good", "n_residues": 100, "mean_plddt": 80.0, "quality": "high"},
            {"name": "bad", "error": "failed"},
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            stats = write_batch_stats(reports, tmpdir)
            self.assertEqual(stats["successful"], 1)
            self.assertEqual(stats["failed"], 1)


if __name__ == "__main__":
    unittest.main()

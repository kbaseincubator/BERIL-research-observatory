"""Tests for export_tables.py — Delta Lake TSV export."""

import csv
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from export_tables import (
    export_structure_project,
    export_refinement_cycles,
    export_validation_report,
    export_alphafold_structure,
    STRUCTURE_PROJECTS_COLUMNS,
    REFINEMENT_CYCLES_COLUMNS,
    VALIDATION_REPORTS_COLUMNS,
    ALPHAFOLD_STRUCTURES_COLUMNS,
)
from refinement_state import ProjectState


class TestExportStructureProject(unittest.TestCase):
    """Test structure_projects.tsv export."""

    def test_export_project(self):
        with tempfile.TemporaryDirectory() as projdir, \
             tempfile.TemporaryDirectory() as outdir:
            state = ProjectState(projdir)
            state.method = "xray"
            state.set("resolution", 1.8)
            state.set("space_group", "P 21 21 21")
            state.set("uniprot_accession", "P0A6Y8")
            state.transition("complete")
            state.set("completed_date", "2026-03-14")
            state.save()

            n = export_structure_project(projdir, outdir)
            self.assertEqual(n, 1)

            filepath = os.path.join(outdir, "structure_projects.tsv")
            self.assertTrue(os.path.exists(filepath))

            with open(filepath) as f:
                reader = csv.DictReader(f, delimiter="\t")
                rows = list(reader)

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["method"], "xray")
            self.assertEqual(rows[0]["uniprot_accession"], "P0A6Y8")
            self.assertEqual(rows[0]["status"], "complete")

    def test_header_matches_schema(self):
        with tempfile.TemporaryDirectory() as projdir, \
             tempfile.TemporaryDirectory() as outdir:
            state = ProjectState(projdir)
            state.save()
            export_structure_project(projdir, outdir)

            filepath = os.path.join(outdir, "structure_projects.tsv")
            with open(filepath) as f:
                header = f.readline().strip().split("\t")
            self.assertEqual(header, STRUCTURE_PROJECTS_COLUMNS)


class TestExportRefinementCycles(unittest.TestCase):
    """Test refinement_cycles.tsv export."""

    def test_export_cycles(self):
        with tempfile.TemporaryDirectory() as projdir, \
             tempfile.TemporaryDirectory() as outdir:
            state = ProjectState(projdir)
            state.record_cycle_metrics(1, r_work=0.30, r_free=0.35, molprobity_score=2.5)
            state.record_cycle_metrics(2, r_work=0.25, r_free=0.30, molprobity_score=2.0)
            state.record_cycle_metrics(3, r_work=0.22, r_free=0.27, molprobity_score=1.8)
            state.save()

            n = export_refinement_cycles(projdir, outdir)
            self.assertEqual(n, 3)

            filepath = os.path.join(outdir, "refinement_cycles.tsv")
            with open(filepath) as f:
                reader = csv.DictReader(f, delimiter="\t")
                rows = list(reader)

            self.assertEqual(len(rows), 3)
            self.assertEqual(rows[0]["cycle_number"], "1")
            self.assertEqual(rows[2]["cycle_number"], "3")

    def test_rgap_calculated(self):
        with tempfile.TemporaryDirectory() as projdir, \
             tempfile.TemporaryDirectory() as outdir:
            state = ProjectState(projdir)
            state.record_cycle_metrics(1, r_work=0.20, r_free=0.25)
            state.save()

            export_refinement_cycles(projdir, outdir)

            filepath = os.path.join(outdir, "refinement_cycles.tsv")
            with open(filepath) as f:
                reader = csv.DictReader(f, delimiter="\t")
                row = next(reader)

            # R-gap should be 0.05
            self.assertAlmostEqual(float(row["r_gap"]), 0.05, places=3)

    def test_header_matches_schema(self):
        with tempfile.TemporaryDirectory() as projdir, \
             tempfile.TemporaryDirectory() as outdir:
            state = ProjectState(projdir)
            state.record_cycle_metrics(1, r_work=0.25, r_free=0.30)
            state.save()
            export_refinement_cycles(projdir, outdir)

            filepath = os.path.join(outdir, "refinement_cycles.tsv")
            with open(filepath) as f:
                header = f.readline().strip().split("\t")
            self.assertEqual(header, REFINEMENT_CYCLES_COLUMNS)


class TestExportValidationReport(unittest.TestCase):
    """Test validation_reports.tsv export."""

    def test_export_report(self):
        report = {
            "model": "model.pdb",
            "validation_date": "2026-03-14",
            "metrics": {
                "molprobity_score": 1.87,
                "ramachandran_favored": 97.6,
                "ramachandran_outliers": 0.34,
                "clash_score": 4.32,
                "rotamer_outliers": 2.12,
                "cbeta_deviations": 2,
            },
        }

        with tempfile.TemporaryDirectory() as outdir:
            n = export_validation_report(report, "P0A6Y8", "alphafold", outdir)
            self.assertEqual(n, 1)

            filepath = os.path.join(outdir, "validation_reports.tsv")
            with open(filepath) as f:
                reader = csv.DictReader(f, delimiter="\t")
                row = next(reader)

            self.assertEqual(row["uniprot_accession"], "P0A6Y8")
            self.assertEqual(row["source"], "alphafold")
            self.assertAlmostEqual(float(row["molprobity_score"]), 1.87)

    def test_header_matches_schema(self):
        report = {"metrics": {}, "validation_date": "2026-03-14"}
        with tempfile.TemporaryDirectory() as outdir:
            export_validation_report(report, "P0A6Y8", "experimental", outdir)

            filepath = os.path.join(outdir, "validation_reports.tsv")
            with open(filepath) as f:
                header = f.readline().strip().split("\t")
            self.assertEqual(header, VALIDATION_REPORTS_COLUMNS)


class TestExportAlphafoldStructure(unittest.TestCase):
    """Test alphafold_structures.tsv export."""

    def test_export_metadata(self):
        metadata = {
            "uniprot_accession": "P0A6Y8",
            "pdb_path": "s3a://cdm-lake/.../model.pdb",
            "cif_path": "s3a://cdm-lake/.../model.cif",
            "pae_path": "s3a://cdm-lake/.../pae.json",
            "n_residues": 109,
            "n_domains": 0,
            "mean_plddt": 92.5,
            "retrieval_date": "2026-03-14",
        }

        with tempfile.TemporaryDirectory() as outdir:
            n = export_alphafold_structure(metadata, outdir)
            self.assertEqual(n, 1)

            filepath = os.path.join(outdir, "alphafold_structures.tsv")
            with open(filepath) as f:
                reader = csv.DictReader(f, delimiter="\t")
                row = next(reader)

            self.assertEqual(row["uniprot_accession"], "P0A6Y8")
            self.assertEqual(row["n_residues"], "109")

    def test_append_mode(self):
        """Multiple exports append to the same file."""
        with tempfile.TemporaryDirectory() as outdir:
            for acc in ["P0A6Y8", "Q9Y6K9", "P12345"]:
                export_alphafold_structure(
                    {"uniprot_accession": acc, "n_residues": 100,
                     "n_domains": 0, "mean_plddt": 90.0,
                     "retrieval_date": "2026-03-14"},
                    outdir,
                )

            filepath = os.path.join(outdir, "alphafold_structures.tsv")
            with open(filepath) as f:
                lines = f.readlines()
            # 1 header + 3 data rows
            self.assertEqual(len(lines), 4)

    def test_header_matches_schema(self):
        with tempfile.TemporaryDirectory() as outdir:
            export_alphafold_structure({"uniprot_accession": "X"}, outdir)

            filepath = os.path.join(outdir, "alphafold_structures.tsv")
            with open(filepath) as f:
                header = f.readline().strip().split("\t")
            self.assertEqual(header, ALPHAFOLD_STRUCTURES_COLUMNS)


class TestSchemaConsistency(unittest.TestCase):
    """Verify column lists match the ingestion config."""

    def test_columns_match_config(self):
        """Column lists should match structural_biology.json schema_sql."""
        config_path = os.path.join(
            os.path.dirname(__file__), "..", "scripts", "structural_biology.json"
        )
        with open(config_path) as f:
            config = json.load(f)

        for table in config["tables"]:
            schema_sql = table["schema_sql"]
            # Extract column names from schema_sql
            config_cols = [
                part.strip().split()[0]
                for part in schema_sql.split(",")
            ]

            if table["name"] == "structure_projects":
                self.assertEqual(config_cols, STRUCTURE_PROJECTS_COLUMNS)
            elif table["name"] == "refinement_cycles":
                self.assertEqual(config_cols, REFINEMENT_CYCLES_COLUMNS)
            elif table["name"] == "validation_reports":
                self.assertEqual(config_cols, VALIDATION_REPORTS_COLUMNS)
            elif table["name"] == "alphafold_structures":
                self.assertEqual(config_cols, ALPHAFOLD_STRUCTURES_COLUMNS)


if __name__ == "__main__":
    unittest.main()

"""Tests for download_pdb_data.py — RCSB GraphQL + SIFTS download."""

import csv
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from download_pdb_data import (
    parse_entry,
    parse_validation_entry,
    ENTRIES_COLUMNS,
    MAPPING_COLUMNS,
    VALIDATION_COLUMNS,
)


SAMPLE_GRAPHQL_ENTRY = {
    "rcsb_id": "4HHB",
    "struct": {"title": "THE CRYSTAL STRUCTURE OF HUMAN DEOXYHAEMOGLOBIN AT 1.74 ANGSTROMS RESOLUTION"},
    "rcsb_entry_info": {
        "resolution_combined": [1.74],
        "experimental_method": "X-ray",
    },
    "exptl": [{"method": "X-RAY DIFFRACTION"}],
    "refine": [{"ls_R_factor_R_free": None, "ls_R_factor_R_work": 0.135}],
    "rcsb_accession_info": {
        "deposit_date": "1984-03-07T00:00:00Z",
        "initial_release_date": "1984-07-17T00:00:00Z",
    },
    "rcsb_primary_citation": {"pdbx_database_id_DOI": "10.1016/0022-2836(84)90472-8"},
    "polymer_entities": [
        {
            "rcsb_polymer_entity": {"pdbx_description": "HEMOGLOBIN (DEOXY)"},
            "rcsb_entity_source_organism": [
                {"ncbi_scientific_name": "Homo sapiens"}
            ],
        }
    ],
}

SAMPLE_EM_ENTRY = {
    "rcsb_id": "7S6V",
    "struct": {"title": "Cryo-EM structure of a ribosome"},
    "rcsb_entry_info": {
        "resolution_combined": [3.2],
        "experimental_method": "EM",
    },
    "exptl": [{"method": "ELECTRON MICROSCOPY"}],
    "refine": None,
    "rcsb_accession_info": {
        "deposit_date": "2021-06-15T00:00:00Z",
        "initial_release_date": "2022-01-10T00:00:00Z",
    },
    "rcsb_primary_citation": {"pdbx_database_id_DOI": None},
    "polymer_entities": [
        {
            "rcsb_entity_source_organism": [
                {"ncbi_scientific_name": "Escherichia coli"}
            ],
        }
    ],
}


class TestParseEntry(unittest.TestCase):
    """Test parsing GraphQL entry responses."""

    def test_xray_entry(self):
        row = parse_entry(SAMPLE_GRAPHQL_ENTRY)
        self.assertEqual(row["pdb_id"], "4HHB")
        self.assertEqual(row["method"], "X-ray")
        self.assertEqual(row["method_full"], "X-RAY DIFFRACTION")
        self.assertAlmostEqual(row["resolution"], 1.74)
        self.assertAlmostEqual(row["r_work"], 0.135)
        self.assertIsNone(row["r_free"])
        self.assertEqual(row["organism"], "Homo sapiens")
        self.assertEqual(row["deposition_date"], "1984-03-07")
        self.assertIn("DEOXYHAEMOGLOBIN", row["title"])

    def test_em_entry(self):
        row = parse_entry(SAMPLE_EM_ENTRY)
        self.assertEqual(row["pdb_id"], "7S6V")
        self.assertEqual(row["method"], "EM")
        self.assertEqual(row["method_full"], "ELECTRON MICROSCOPY")
        self.assertAlmostEqual(row["resolution"], 3.2)
        self.assertIsNone(row["r_work"])
        self.assertIsNone(row["r_free"])
        self.assertEqual(row["organism"], "Escherichia coli")

    def test_missing_fields_handled(self):
        """Entries with missing fields should not crash."""
        minimal = {"rcsb_id": "1XYZ"}
        row = parse_entry(minimal)
        self.assertEqual(row["pdb_id"], "1XYZ")
        self.assertEqual(row["title"], "")
        self.assertIsNone(row["resolution"])

    def test_all_columns_present(self):
        row = parse_entry(SAMPLE_GRAPHQL_ENTRY)
        for col in ENTRIES_COLUMNS:
            self.assertIn(col, row)

    def test_tabs_in_title_escaped(self):
        entry = dict(SAMPLE_GRAPHQL_ENTRY)
        entry["struct"] = {"title": "Title\twith\ttabs"}
        row = parse_entry(entry)
        self.assertNotIn("\t", row["title"])

    def test_date_truncation(self):
        row = parse_entry(SAMPLE_GRAPHQL_ENTRY)
        self.assertEqual(len(row["deposition_date"]), 10)
        self.assertEqual(len(row["release_date"]), 10)


class TestColumnDefinitions(unittest.TestCase):
    """Test column definitions match ingestion config."""

    def test_entries_columns_match_config(self):
        config_path = os.path.join(
            os.path.dirname(__file__), "..", "scripts", "pdb_collection.json"
        )
        with open(config_path) as f:
            config = json.load(f)

        for table in config["tables"]:
            schema_cols = [p.strip().split()[0] for p in table["schema_sql"].split(",")]
            if table["name"] == "pdb_entries":
                self.assertEqual(schema_cols, ENTRIES_COLUMNS)
            elif table["name"] == "pdb_uniprot_mapping":
                self.assertEqual(schema_cols, MAPPING_COLUMNS)
            elif table["name"] == "pdb_validation":
                self.assertEqual(schema_cols, VALIDATION_COLUMNS)


class TestParseValidationEntry(unittest.TestCase):
    """Test parsing GraphQL validation responses."""

    def test_parse_validation(self):
        entry = {
            "rcsb_id": "4HHB",
            "pdbx_vrpt_summary_geometry": [{
                "clashscore": 141.11,
                "percent_ramachandran_outliers": 1.24,
                "percent_rotamer_outliers": 8.44,
                "angles_RMSZ": 7.11,
                "bonds_RMSZ": 9.69,
            }],
        }
        row = parse_validation_entry(entry)
        self.assertEqual(row["pdb_id"], "4HHB")
        self.assertAlmostEqual(row["clashscore"], 141.11)
        self.assertAlmostEqual(row["percent_ramachandran_outliers"], 1.24)

    def test_missing_validation(self):
        entry = {"rcsb_id": "1XYZ", "pdbx_vrpt_summary_geometry": None}
        row = parse_validation_entry(entry)
        self.assertEqual(row["pdb_id"], "1XYZ")
        self.assertIsNone(row["clashscore"])

    def test_all_validation_columns(self):
        entry = {"rcsb_id": "1ABC", "pdbx_vrpt_summary_geometry": [{}]}
        row = parse_validation_entry(entry)
        for col in VALIDATION_COLUMNS:
            self.assertIn(col, row)


class TestSiftsOutput(unittest.TestCase):
    """Test SIFTS TSV output format."""

    def test_mapping_columns_count(self):
        self.assertEqual(len(MAPPING_COLUMNS), 9)

    def test_mapping_has_uniprot(self):
        self.assertIn("uniprot_accession", MAPPING_COLUMNS)

    def test_mapping_has_pdb_id(self):
        self.assertIn("pdb_id", MAPPING_COLUMNS)


if __name__ == "__main__":
    unittest.main()

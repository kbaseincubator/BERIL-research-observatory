"""Tests for retrieve_alphafold.py — AlphaFold structure retrieval from EBI."""

import json
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from retrieve_alphafold import (
    validate_pdb,
    validate_pae,
    METADATA_HEADER,
)

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


class TestValidatePdb(unittest.TestCase):
    """Test PDB file validation and pLDDT extraction."""

    def test_valid_pdb(self):
        """Parse a minimal PDB with ATOM records."""
        pdb_content = (
            "ATOM      1  N   ALA A   1      10.000  20.000  30.000  1.00 85.50           N\n"
            "ATOM      2  CA  ALA A   1      11.000  21.000  31.000  1.00 90.20           C\n"
            "ATOM      3  N   GLY A   2      12.000  22.000  32.000  1.00 75.00           N\n"
            "ATOM      4  CA  GLY A   2      13.000  23.000  33.000  1.00 80.30           C\n"
            "END\n"
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".pdb", delete=False) as f:
            f.write(pdb_content)
            f.flush()
            n_residues, mean_plddt = validate_pdb(f.name)
        os.unlink(f.name)

        self.assertEqual(n_residues, 2)
        self.assertAlmostEqual(mean_plddt, 82.75, places=1)

    def test_empty_pdb(self):
        """Empty PDB returns zero residues."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".pdb", delete=False) as f:
            f.write("REMARK  empty file\nEND\n")
            f.flush()
            n_residues, mean_plddt = validate_pdb(f.name)
        os.unlink(f.name)

        self.assertEqual(n_residues, 0)
        self.assertEqual(mean_plddt, 0.0)


class TestValidatePae(unittest.TestCase):
    """Test PAE JSON validation."""

    def test_standard_pae_format(self):
        """Parse standard PAE JSON with predicted_aligned_error matrix."""
        pae_data = [{"predicted_aligned_error": [[0.5, 2.1], [2.1, 0.5]]}]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(pae_data, f)
            f.flush()
            result = validate_pae(f.name)
        os.unlink(f.name)
        self.assertTrue(result)

    def test_dict_format_pae(self):
        """Parse dict-format PAE JSON."""
        pae_data = {"predicted_aligned_error": [[1.0, 3.0], [3.0, 1.0]]}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(pae_data, f)
            f.flush()
            result = validate_pae(f.name)
        os.unlink(f.name)
        self.assertTrue(result)


class TestEbiApiResponse(unittest.TestCase):
    """Test parsing of EBI API response fixture."""

    def test_parse_fixture(self):
        """Verify fixture JSON has expected structure."""
        fixture_path = os.path.join(FIXTURES_DIR, "sample_alphafold_response.json")
        with open(fixture_path) as f:
            data = json.load(f)

        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)

        entry = data[0]
        self.assertEqual(entry["uniprotAccession"], "P0A6Y8")
        self.assertEqual(entry["gene"], "trxA")
        self.assertIn("pdbUrl", entry)
        self.assertIn("cifUrl", entry)
        self.assertIn("paeDocUrl", entry)
        self.assertEqual(entry["uniprotStart"], 1)
        self.assertEqual(entry["uniprotEnd"], 109)


class TestMetadataHeader(unittest.TestCase):
    """Test metadata output format."""

    def test_header_fields(self):
        """Verify metadata header matches alphafold_structures schema."""
        expected = [
            "uniprot_accession", "pdb_path", "cif_path", "pae_path",
            "n_residues", "n_domains", "mean_plddt", "retrieval_date",
        ]
        self.assertEqual(METADATA_HEADER, expected)


class TestRetrieveWithMockApi(unittest.TestCase):
    """Test retrieve_structure with mocked HTTP responses."""

    @patch("retrieve_alphafold.requests.Session")
    def test_retrieve_success(self, mock_session_class):
        """Successful retrieval with mocked API and file downloads."""
        from retrieve_alphafold import retrieve_structure

        # Load fixture
        fixture_path = os.path.join(FIXTURES_DIR, "sample_alphafold_response.json")
        with open(fixture_path) as f:
            api_response = json.load(f)

        # Mock session
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Mock API response
        api_resp = MagicMock()
        api_resp.status_code = 200
        api_resp.json.return_value = api_response

        # Mock file download responses
        pdb_content = b"ATOM      1  N   ALA A   1      10.0  20.0  30.0  1.00 85.50           N\nEND\n"
        cif_content = b"_atom_site.id\n1\n"
        pae_content = json.dumps([{"predicted_aligned_error": [[0.5]]}]).encode()

        file_resp = MagicMock()
        file_resp.iter_content.return_value = [pdb_content]

        cif_resp = MagicMock()
        cif_resp.iter_content.return_value = [cif_content]

        pae_resp = MagicMock()
        pae_resp.iter_content.return_value = [pae_content]

        mock_session.get.side_effect = [api_resp, file_resp, cif_resp, pae_resp]

        with tempfile.TemporaryDirectory() as tmpdir:
            metadata = retrieve_structure("P0A6Y8", tmpdir, session=mock_session)

            self.assertIsNotNone(metadata)
            self.assertEqual(metadata["uniprot_accession"], "P0A6Y8")
            self.assertEqual(metadata["n_domains"], 0)
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "P0A6Y8", "metadata.tsv")))

    @patch("retrieve_alphafold.requests.Session")
    def test_retrieve_not_found(self, mock_session_class):
        """404 returns None."""
        from retrieve_alphafold import retrieve_structure

        mock_session = MagicMock()
        resp = MagicMock()
        resp.status_code = 404
        mock_session.get.return_value = resp

        with tempfile.TemporaryDirectory() as tmpdir:
            result = retrieve_structure("INVALID", tmpdir, session=mock_session)
            self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()

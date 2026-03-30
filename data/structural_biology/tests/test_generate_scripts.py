"""Tests for generate_scripts.py — visualization script generation."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from generate_scripts import (
    generate_coot_outlier_script,
    generate_pymol_validation_script,
    generate_chimerax_session,
    generate_rfactor_plot,
    parse_ramalyze_file,
    _parse_residue,
)

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")

SAMPLE_OUTLIERS = [
    {"residue": "A:45:LEU", "type": "ramachandran_outlier"},
    {"residue": "A:78:ARG", "type": "rotamer_outlier"},
    {"residue": "A:123:PHE", "type": "ramachandran_outlier"},
]


class TestParseResidue(unittest.TestCase):
    """Test residue string parsing."""

    def test_colon_format(self):
        chain, resnum, resname = _parse_residue("A:45:LEU")
        self.assertEqual(chain, "A")
        self.assertEqual(resnum, 45)
        self.assertEqual(resname, "LEU")

    def test_space_format(self):
        chain, resnum, resname = _parse_residue("A  78  ARG")
        self.assertEqual(chain, "A")
        self.assertEqual(resnum, 78)
        self.assertEqual(resname, "ARG")

    def test_invalid_returns_defaults(self):
        chain, resnum, resname = _parse_residue("")
        self.assertEqual(resnum, 0)


class TestCootScript(unittest.TestCase):
    """Test Coot script generation."""

    def test_generates_valid_python(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "coot.py")
            generate_coot_outlier_script(SAMPLE_OUTLIERS, "model.pdb", output_path=path)

            self.assertTrue(os.path.exists(path))
            with open(path) as f:
                content = f.read()

            self.assertIn("import coot", content)
            self.assertIn("model.pdb", content)
            self.assertIn("outliers = [", content)
            self.assertIn("ramachandran_outlier", content)
            self.assertIn("45", content)

    def test_with_mtz_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "coot.py")
            generate_coot_outlier_script(
                SAMPLE_OUTLIERS, "model.pdb", data_path="data.mtz", output_path=path
            )
            with open(path) as f:
                content = f.read()
            self.assertIn("data.mtz", content)

    def test_with_map(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "coot.py")
            generate_coot_outlier_script(
                SAMPLE_OUTLIERS, "model.pdb", map_path="map.mrc", output_path=path
            )
            with open(path) as f:
                content = f.read()
            self.assertIn("map.mrc", content)

    def test_no_outliers(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "coot.py")
            generate_coot_outlier_script([], "model.pdb", output_path=path)
            with open(path) as f:
                content = f.read()
            self.assertIn("No outliers found", content)


class TestPymolScript(unittest.TestCase):
    """Test PyMOL script generation."""

    def test_generates_valid_pml(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "validation.pml")
            generate_pymol_validation_script(SAMPLE_OUTLIERS, "model.pdb", output_path=path)

            self.assertTrue(os.path.exists(path))
            with open(path) as f:
                content = f.read()

            self.assertIn("load model.pdb", content)
            self.assertIn("show cartoon", content)
            self.assertIn("rama_outliers", content)
            self.assertIn("rota_outliers", content)
            self.assertIn("color red", content)
            self.assertIn("color orange", content)

    def test_no_outliers(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "validation.pml")
            generate_pymol_validation_script([], "model.pdb", output_path=path)
            with open(path) as f:
                content = f.read()
            self.assertIn("load model.pdb", content)
            self.assertNotIn("rama_outliers", content)


class TestChimeraXScript(unittest.TestCase):
    """Test ChimeraX script generation."""

    def test_model_only(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "session.cxc")
            generate_chimerax_session("model.pdb", output_path=path)

            with open(path) as f:
                content = f.read()
            self.assertIn("open model.pdb", content)
            self.assertIn("cartoon style", content)

    def test_with_map(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "session.cxc")
            generate_chimerax_session("model.pdb", map_path="map.mrc", output_path=path)

            with open(path) as f:
                content = f.read()
            self.assertIn("open map.mrc", content)
            self.assertIn("volume", content)

    def test_with_outliers(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "session.cxc")
            generate_chimerax_session("model.pdb", outliers=SAMPLE_OUTLIERS, output_path=path)

            with open(path) as f:
                content = f.read()
            self.assertIn("color sel red", content)


class TestParseRamalyzeFile(unittest.TestCase):
    """Test parsing phenix.ramalyze output."""

    def test_parse_fixture(self):
        data = parse_ramalyze_file(os.path.join(FIXTURES_DIR, "sample_ramalyze.out"))
        self.assertGreater(len(data), 0)

        # Check we got tuples of (phi, psi, is_outlier)
        for phi, psi, is_outlier in data:
            self.assertIsInstance(phi, float)
            self.assertIsInstance(psi, float)
            self.assertIsInstance(is_outlier, bool)

        # Should have some outliers
        n_outliers = sum(1 for _, _, o in data if o)
        self.assertGreater(n_outliers, 0)


class TestRfactorPlot(unittest.TestCase):
    """Test R-factor convergence plot generation."""

    def test_generates_plot(self):
        """Test plot generation (may skip if matplotlib not available)."""
        try:
            import matplotlib
        except ImportError:
            self.skipTest("matplotlib not available")

        cycles_data = [
            {"cycle": 1, "r_work": 0.30, "r_free": 0.35},
            {"cycle": 2, "r_work": 0.25, "r_free": 0.30},
            {"cycle": 3, "r_work": 0.22, "r_free": 0.27},
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "rfactor.png")
            result = generate_rfactor_plot(cycles_data, output_path=path)
            if result:
                self.assertTrue(os.path.exists(path))
                self.assertGreater(os.path.getsize(path), 0)


if __name__ == "__main__":
    unittest.main()

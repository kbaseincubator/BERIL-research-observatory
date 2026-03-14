"""Tests for parse_validation.py — Phenix output parsing."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from parse_validation import (
    parse_validation_log,
    parse_refine_log,
    parse_xtriage_log,
    parse_ramalyze_output,
    parse_rotalyze_output,
    format_report,
)

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


class TestParseValidationLog(unittest.TestCase):
    """Test parsing of phenix.molprobity / phenix.validation output."""

    def setUp(self):
        with open(os.path.join(FIXTURES_DIR, "sample_validation.log")) as f:
            self.log_text = f.read()

    def test_molprobity_score(self):
        metrics = parse_validation_log(self.log_text)
        self.assertAlmostEqual(metrics["molprobity_score"], 1.87)

    def test_clashscore(self):
        metrics = parse_validation_log(self.log_text)
        self.assertAlmostEqual(metrics["clash_score"], 4.32)

    def test_ramachandran_favored(self):
        metrics = parse_validation_log(self.log_text)
        self.assertAlmostEqual(metrics["ramachandran_favored"], 97.60)

    def test_ramachandran_outliers(self):
        metrics = parse_validation_log(self.log_text)
        self.assertAlmostEqual(metrics["ramachandran_outliers"], 0.34)

    def test_rotamer_outliers(self):
        metrics = parse_validation_log(self.log_text)
        self.assertAlmostEqual(metrics["rotamer_outliers"], 2.12)

    def test_cbeta_deviations(self):
        metrics = parse_validation_log(self.log_text)
        self.assertEqual(metrics["cbeta_deviations"], 2)

    def test_r_factors(self):
        metrics = parse_validation_log(self.log_text)
        self.assertAlmostEqual(metrics["r_work"], 0.1923)
        self.assertAlmostEqual(metrics["r_free"], 0.2345)

    def test_rms_bonds_angles(self):
        metrics = parse_validation_log(self.log_text)
        self.assertAlmostEqual(metrics["rms_bonds"], 0.008)
        self.assertAlmostEqual(metrics["rms_angles"], 1.023)


class TestParseRefineLog(unittest.TestCase):
    """Test parsing of phenix.refine output."""

    def setUp(self):
        with open(os.path.join(FIXTURES_DIR, "sample_refine.log")) as f:
            self.log_text = f.read()

    def test_cycles_parsed(self):
        result = parse_refine_log(self.log_text)
        self.assertEqual(len(result["cycles"]), 3)

    def test_cycle_values(self):
        result = parse_refine_log(self.log_text)
        cycle1 = result["cycles"][0]
        self.assertEqual(cycle1["cycle"], 1)
        self.assertAlmostEqual(cycle1["r_work"], 0.2234)
        self.assertAlmostEqual(cycle1["r_free"], 0.2645)

    def test_final_metrics(self):
        result = parse_refine_log(self.log_text)
        final = result["final"]
        self.assertAlmostEqual(final["r_work"], 0.2098)
        self.assertAlmostEqual(final["r_free"], 0.2489)
        self.assertAlmostEqual(final["molprobity_score"], 1.95)

    def test_refinement_strategy(self):
        result = parse_refine_log(self.log_text)
        self.assertEqual(result["refinement_strategy"], "individual_sites+individual_adp")

    def test_output_model(self):
        result = parse_refine_log(self.log_text)
        self.assertEqual(result["output_model"], "model_out.pdb")

    def test_convergence(self):
        """R-factors should decrease across cycles."""
        result = parse_refine_log(self.log_text)
        r_frees = [c["r_free"] for c in result["cycles"]]
        for i in range(1, len(r_frees)):
            self.assertLess(r_frees[i], r_frees[i - 1])


class TestParseXtriageLog(unittest.TestCase):
    """Test parsing of phenix.xtriage output."""

    def setUp(self):
        with open(os.path.join(FIXTURES_DIR, "sample_xtriage.log")) as f:
            self.log_text = f.read()

    def test_resolution(self):
        metrics = parse_xtriage_log(self.log_text)
        self.assertAlmostEqual(metrics["resolution"], 1.80)

    def test_space_group(self):
        metrics = parse_xtriage_log(self.log_text)
        self.assertEqual(metrics["space_group"], "P 21 21 21")

    def test_completeness(self):
        metrics = parse_xtriage_log(self.log_text)
        self.assertAlmostEqual(metrics["completeness"], 99.2)

    def test_wilson_b(self):
        metrics = parse_xtriage_log(self.log_text)
        self.assertAlmostEqual(metrics["wilson_b"], 22.4)

    def test_no_twinning(self):
        metrics = parse_xtriage_log(self.log_text)
        self.assertFalse(metrics["twinning"])

    def test_reflections(self):
        metrics = parse_xtriage_log(self.log_text)
        self.assertEqual(metrics["n_reflections"], 24531)

    def test_matthews(self):
        metrics = parse_xtriage_log(self.log_text)
        self.assertAlmostEqual(metrics["matthews_coefficient"], 2.34)

    def test_solvent_content(self):
        metrics = parse_xtriage_log(self.log_text)
        self.assertAlmostEqual(metrics["solvent_content"], 47.3)

    def test_molecules_asu(self):
        metrics = parse_xtriage_log(self.log_text)
        self.assertEqual(metrics["n_molecules_asu"], 1)

    def test_unit_cell(self):
        metrics = parse_xtriage_log(self.log_text)
        self.assertEqual(len(metrics["unit_cell"]), 6)
        self.assertAlmostEqual(metrics["unit_cell"][0], 45.23)


class TestParsePerResidueTools(unittest.TestCase):
    """Test parsing of per-residue validation tools."""

    def test_ramalyze_outliers(self):
        output = (
            " A   1  ALA  -60.5  -40.2    Favored\n"
            " A  15  PRO  -75.0   80.0    OUTLIER\n"
            " A  42  GLY   85.0  170.0    OUTLIER\n"
            " A  50  LEU  -65.0  -35.0    Favored\n"
        )
        outliers = parse_ramalyze_output(output)
        self.assertEqual(len(outliers), 2)
        self.assertEqual(outliers[0]["type"], "ramachandran_outlier")

    def test_rotalyze_outliers(self):
        output = (
            " A  10  LEU  mt  t60p   Favored\n"
            " A  25  VAL  m   OUTLIER\n"
            " A  30  ILE  pt  p60m   Favored\n"
        )
        outliers = parse_rotalyze_output(output)
        self.assertEqual(len(outliers), 1)
        self.assertEqual(outliers[0]["type"], "rotamer_outlier")

    def test_no_outliers(self):
        output = " A   1  ALA  Favored\n A   2  GLY  Favored\n"
        self.assertEqual(len(parse_ramalyze_output(output)), 0)
        self.assertEqual(len(parse_rotalyze_output(output)), 0)


class TestFormatReport(unittest.TestCase):
    """Test report formatting."""

    def test_text_format(self):
        report = {
            "model": "test.pdb",
            "data": None,
            "validation_date": "2026-03-14",
            "metrics": {
                "molprobity_score": 1.87,
                "clash_score": 4.32,
                "ramachandran_favored": 97.6,
            },
            "outliers": [],
        }
        text = format_report(report, as_json=False)
        self.assertIn("MolProbity score", text)
        self.assertIn("1.87", text)

    def test_json_format(self):
        report = {
            "model": "test.pdb",
            "metrics": {"molprobity_score": 1.87},
            "outliers": [],
        }
        import json
        output = format_report(report, as_json=True)
        parsed = json.loads(output)
        self.assertEqual(parsed["metrics"]["molprobity_score"], 1.87)


if __name__ == "__main__":
    unittest.main()

"""Tests for SLURM job templates — verify templates exist and have correct structure."""

import os
import unittest

TEMPLATES_DIR = os.path.join(
    os.path.dirname(__file__), "..", "scripts", "slurm_templates"
)

EXPECTED_TEMPLATES = {
    "refine.sh": {
        "tool": "phenix.refine",
        "default_time": "04:00:00",
        "required_vars": ["PHENIX_MODEL", "PHENIX_DATA"],
    },
    "real_space_refine.sh": {
        "tool": "phenix.real_space_refine",
        "default_time": "04:00:00",
        "required_vars": ["PHENIX_MODEL", "PHENIX_MAP", "PHENIX_RESOLUTION"],
    },
    "phaser.sh": {
        "tool": "phenix.phaser",
        "default_time": "04:00:00",
        "required_vars": ["PHENIX_DATA", "PHENIX_MODEL", "PHENIX_SEQ"],
    },
    "autobuild.sh": {
        "tool": "phenix.autobuild",
        "default_time": "08:00:00",
        "required_vars": ["PHENIX_DATA", "PHENIX_MODEL", "PHENIX_SEQ"],
    },
    "map_to_model.sh": {
        "tool": "phenix.map_to_model",
        "default_time": "24:00:00",
        "required_vars": ["PHENIX_MAP", "PHENIX_SEQ", "PHENIX_RESOLUTION"],
    },
    "predict_and_build.sh": {
        "tool": "phenix.predict_and_build",
        "default_time": "48:00:00",
        "required_vars": ["PHENIX_MODEL", "PHENIX_SEQ", "PHENIX_RESOLUTION"],
    },
}


class TestTemplatesExist(unittest.TestCase):
    """Verify all expected SLURM templates exist."""

    def test_all_templates_present(self):
        for name in EXPECTED_TEMPLATES:
            path = os.path.join(TEMPLATES_DIR, name)
            self.assertTrue(os.path.exists(path), f"Missing template: {name}")

    def test_templates_executable(self):
        for name in EXPECTED_TEMPLATES:
            path = os.path.join(TEMPLATES_DIR, name)
            self.assertTrue(os.access(path, os.X_OK), f"Not executable: {name}")


class TestTemplateStructure(unittest.TestCase):
    """Verify SLURM templates have correct SBATCH directives and structure."""

    def _read_template(self, name):
        with open(os.path.join(TEMPLATES_DIR, name)) as f:
            return f.read()

    def test_sbatch_directives(self):
        """All templates must have required SBATCH directives."""
        for name in EXPECTED_TEMPLATES:
            content = self._read_template(name)
            self.assertIn("#SBATCH --qos=regular", content, f"{name}: missing qos")
            self.assertIn("#SBATCH --constraint=cpu", content, f"{name}: missing constraint")
            self.assertIn("#SBATCH --nodes=1", content, f"{name}: missing nodes")

    def test_conda_activation(self):
        """All templates must activate conda and Phenix environment."""
        for name in EXPECTED_TEMPLATES:
            content = self._read_template(name)
            self.assertIn("module load conda", content, f"{name}: missing module load")
            self.assertIn("conda activate phenix", content, f"{name}: missing conda activate")

    def test_phenix_tool_present(self):
        """Each template must call the correct Phenix tool."""
        for name, spec in EXPECTED_TEMPLATES.items():
            content = self._read_template(name)
            self.assertIn(spec["tool"], content,
                          f"{name}: missing tool {spec['tool']}")

    def test_required_env_vars(self):
        """Templates must reference their required environment variables."""
        for name, spec in EXPECTED_TEMPLATES.items():
            content = self._read_template(name)
            for var in spec["required_vars"]:
                self.assertIn(var, content,
                              f"{name}: missing required var {var}")

    def test_set_e(self):
        """All templates must use 'set -e' or 'set -euo pipefail'."""
        for name in EXPECTED_TEMPLATES:
            content = self._read_template(name)
            self.assertTrue(
                "set -e" in content or "set -euo" in content,
                f"{name}: missing error handling (set -e)",
            )

    def test_default_times(self):
        """Templates should reference their default time limits."""
        for name, spec in EXPECTED_TEMPLATES.items():
            content = self._read_template(name)
            self.assertIn(spec["default_time"], content,
                          f"{name}: missing default time {spec['default_time']}")

    def test_shebang(self):
        """All templates must start with bash shebang."""
        for name in EXPECTED_TEMPLATES:
            content = self._read_template(name)
            self.assertTrue(content.startswith("#!/bin/bash"),
                            f"{name}: missing shebang")


class TestTemplateParameterization(unittest.TestCase):
    """Test that templates use environment variable defaults correctly."""

    def test_cpus_default(self):
        """Templates should have CPU defaults via ${PHENIX_CPUS:-N}."""
        for name in EXPECTED_TEMPLATES:
            with open(os.path.join(TEMPLATES_DIR, name)) as f:
                content = f.read()
            self.assertRegex(content, r"PHENIX_CPUS:-\d+",
                             f"{name}: missing PHENIX_CPUS default")

    def test_time_default(self):
        """Templates should have time defaults via ${PHENIX_TIME:-HH:MM:SS}."""
        for name in EXPECTED_TEMPLATES:
            with open(os.path.join(TEMPLATES_DIR, name)) as f:
                content = f.read()
            self.assertRegex(content, r"PHENIX_TIME:-\d+:\d+:\d+",
                             f"{name}: missing PHENIX_TIME default")


if __name__ == "__main__":
    unittest.main()

"""Tests for observatory_context.parsing (formerly scripts/build_registry.py)."""

from __future__ import annotations

import json
from pathlib import Path

from observatory_context.parsing import scan_notebook_deps, parse_readme_deps, PROJECTS_DIR


def test_scan_notebook_deps_supports_digit_project_ids(tmp_path):
    project_dir = tmp_path / "consumer2_proj"
    notebooks_dir = project_dir / "notebooks"
    notebooks_dir.mkdir(parents=True)

    nb_data = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {},
        "cells": [
            {
                "cell_type": "code",
                "metadata": {},
                "outputs": [],
                "source": ["df = pd.read_csv('../../source2_proj/data/results.csv')"],
            }
        ],
    }
    (notebooks_dir / "analysis.ipynb").write_text(json.dumps(nb_data), encoding="utf-8")

    deps = scan_notebook_deps(project_dir)

    assert deps == [{"project": "source2_proj", "files": ["results.csv"]}]


def test_parse_readme_deps_supports_digit_project_ids(tmp_path, monkeypatch):
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir()
    (projects_dir / "source2_proj").mkdir()

    monkeypatch.setattr("observatory_context.parsing.PROJECTS_DIR", projects_dir)

    readme = """## Dependencies
- Uses `source2_proj` data export.
- Also references [source2](../source2_proj/README.md)
## Next Section
"""

    deps = parse_readme_deps(readme)

    assert deps == ["source2_proj"]

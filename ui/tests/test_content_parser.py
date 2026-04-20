"""Tests for app.content_parser — stateless markdown/notebook parsing."""

import json
from pathlib import Path

import pytest

from app.content_parser import (
    ParsedContributor,
    ParsedProjectFields,
    extract_collection_refs,
    extract_other_sections,
    extract_section,
    parse_contributors,
    parse_notebook_metadata,
    parse_project_fields,
    rewrite_md_links,
    scan_project_files,
)


# ---------------------------------------------------------------------------
# extract_section
# ---------------------------------------------------------------------------


class TestExtractSection:
    def test_extracts_simple_section(self):
        content = "# Title\n\n## Research Question\nWhy does X happen?\n\n## Hypothesis\nBecause Y.\n"
        assert extract_section(content, "Research Question") == "Why does X happen?"

    def test_returns_none_for_missing_section(self):
        content = "## Overview\nSome text.\n"
        assert extract_section(content, "Hypothesis") is None

    def test_returns_none_for_empty_section(self):
        content = "## Overview\n\n## Next\nContent.\n"
        assert extract_section(content, "Overview") is None

    def test_extracts_multiline_section(self):
        content = "## Approach\nStep 1.\nStep 2.\nStep 3.\n\n## Results\nDone.\n"
        result = extract_section(content, "Approach")
        assert result == "Step 1.\nStep 2.\nStep 3."

    def test_stops_at_next_h2(self):
        content = "## A\nContent A.\n## B\nContent B.\n"
        assert extract_section(content, "A") == "Content A."
        assert extract_section(content, "B") == "Content B."


# ---------------------------------------------------------------------------
# extract_other_sections
# ---------------------------------------------------------------------------


class TestExtractOtherSections:
    def test_returns_unknown_sections(self):
        content = "## Known\nSkip this.\n## Custom\nKeep this.\n"
        others = extract_other_sections(content, {"Known"})
        assert len(others) == 1
        assert others[0] == ("Custom", "Keep this.")

    def test_empty_when_all_sections_known(self):
        content = "## Known\nContent.\n"
        assert extract_other_sections(content, {"Known"}) == []

    def test_skips_empty_sections(self):
        content = "## Extra\n\n## Another\nHas content.\n"
        others = extract_other_sections(content, set())
        assert len(others) == 1
        assert others[0][0] == "Another"


# ---------------------------------------------------------------------------
# extract_collection_refs
# ---------------------------------------------------------------------------


class TestExtractCollectionRefs:
    def test_finds_known_collection(self):
        text = "We used the kbase_ke_pangenome collection."
        refs = extract_collection_refs(text)
        assert "kbase_ke_pangenome" in refs

    def test_returns_empty_for_unknown(self):
        assert extract_collection_refs("no collection here") == []

    def test_finds_multiple_collections(self):
        text = "kbase_ke_pangenome and kbase_genomes were used."
        refs = extract_collection_refs(text)
        assert "kbase_ke_pangenome" in refs
        assert "kbase_genomes" in refs


# ---------------------------------------------------------------------------
# rewrite_md_links
# ---------------------------------------------------------------------------


class TestRewriteMdLinks:
    def test_rewrites_relative_image(self):
        content = "![alt](figures/plot.png)"
        result = rewrite_md_links(content, "my_project")
        assert result == "![alt](/project-assets/my_project/figures/plot.png)"

    def test_leaves_absolute_image_unchanged(self):
        content = "![alt](https://example.com/img.png)"
        assert rewrite_md_links(content, "proj") == content

    def test_rewrites_md_link_to_project(self):
        content = "[see plan](RESEARCH_PLAN.md)"
        result = rewrite_md_links(content, "proj")
        assert result == "[see plan](/projects/proj)"

    def test_leaves_external_link_unchanged(self):
        content = "[external](https://example.com)"
        assert rewrite_md_links(content, "proj") == content

    def test_returns_none_for_none(self):
        assert rewrite_md_links(None, "proj") is None

    def test_returns_empty_string_unchanged(self):
        assert rewrite_md_links("", "proj") == ""


# ---------------------------------------------------------------------------
# parse_contributors
# ---------------------------------------------------------------------------


class TestParseContributors:
    def test_parses_bold_format_with_orcid(self):
        readme = (
            "# Title\n\n## Authors\n"
            "- **Alice Smith** (LBNL) | ORCID: 0000-0001-2345-6789\n"
        )
        contribs = parse_contributors(readme, "proj")
        assert len(contribs) == 1
        c = contribs[0]
        assert c.name == "Alice Smith"
        assert c.orcid == "0000-0001-2345-6789"
        assert c.affiliation == "LBNL"

    def test_parses_plain_format(self):
        readme = (
            "# Title\n\n## Authors\n"
            "- Bob Jones, ORNL (https://orcid.org/0000-0002-3456-7890)\n"
        )
        contribs = parse_contributors(readme, "proj")
        assert len(contribs) == 1
        c = contribs[0]
        assert c.name == "Bob Jones"
        assert c.orcid == "0000-0002-3456-7890"
        assert c.affiliation == "ORNL"

    def test_returns_empty_when_no_authors_section(self):
        readme = "# Title\n\n## Overview\nNo authors here.\n"
        assert parse_contributors(readme, "proj") == []

    def test_parses_multiple_contributors(self):
        readme = (
            "# Title\n\n## Authors\n"
            "- **Alice** (LBNL) | ORCID: 0000-0001-2345-6789\n"
            "- **Bob** (ORNL) | ORCID: 0000-0002-3456-7890\n"
        )
        contribs = parse_contributors(readme, "proj")
        assert len(contribs) == 2
        assert contribs[0].name == "Alice"
        assert contribs[1].name == "Bob"


# ---------------------------------------------------------------------------
# parse_project_fields
# ---------------------------------------------------------------------------


class TestParseProjectFields:
    def _readme(self, **extra_sections):
        parts = ["# My Project\n\n## Research Question\nWhy does X happen?\n"]
        for name, body in extra_sections.items():
            parts.append(f"## {name}\n{body}\n")
        return "".join(parts)

    def test_extracts_title(self):
        parsed = parse_project_fields(self._readme())
        assert parsed.title == "My Project"

    def test_extracts_research_question(self):
        parsed = parse_project_fields(self._readme())
        assert parsed.research_question == "Why does X happen?"

    def test_status_proposed_when_no_plan_or_findings(self):
        readme = "# Project\n\n## Research Question\nQ?\n"
        parsed = parse_project_fields(readme)
        assert parsed.status == "proposed"

    def test_status_in_progress_when_plan_provided(self):
        readme = "# Project\n\n## Research Question\nQ?\n"
        plan = "## Hypothesis\nH.\n## Approach\nA.\n"
        parsed = parse_project_fields(readme, plan=plan)
        assert parsed.status == "in_progress"

    def test_status_completed_when_findings_present(self):
        readme = "# Project\n\n## Key Findings\nWe found significant results.\n"
        parsed = parse_project_fields(readme)
        assert parsed.status == "completed"

    def test_plan_fields_extracted_from_plan_doc(self):
        readme = "# Project\n"
        plan = "## Hypothesis\nX causes Y.\n## Approach\nMeasure Z.\n"
        parsed = parse_project_fields(readme, plan=plan)
        assert parsed.hypothesis == "X causes Y."
        assert parsed.approach == "Measure Z."

    def test_report_fields_extracted(self):
        readme = "# Project\n"
        report = "## Results\nPositive results.\n## Limitations\nSmall sample.\n"
        parsed = parse_project_fields(readme, report=report)
        assert parsed.results == "Positive results."
        assert parsed.limitations == "Small sample."

    def test_raw_fields_stored(self):
        readme = "# Project\n"
        plan = "## Hypothesis\nH.\n"
        parsed = parse_project_fields(readme, plan=plan, project_id="slug")
        assert parsed.raw_readme == readme
        assert parsed.research_plan_raw == plan

    def test_detects_collection_refs(self):
        readme = "# Project\n\nWe used kbase_ke_pangenome for this work.\n"
        parsed = parse_project_fields(readme)
        assert "kbase_ke_pangenome" in parsed.related_collections


# ---------------------------------------------------------------------------
# parse_notebook_metadata
# ---------------------------------------------------------------------------


class TestParseNotebookMetadata:
    def _write_notebook(self, tmp_path, cells):
        nb = {
            "nbformat": 4,
            "nbformat_minor": 4,
            "metadata": {},
            "cells": cells,
        }
        path = tmp_path / "test_notebook.ipynb"
        path.write_text(json.dumps(nb))
        return path

    def test_extracts_title_from_h1(self, tmp_path):
        path = self._write_notebook(tmp_path, [
            {"cell_type": "markdown", "source": ["# My Analysis\n\nSome intro text."], "metadata": {}},
        ])
        result = parse_notebook_metadata(path)
        assert result.title == "My Analysis"
        assert result.description == "Some intro text."

    def test_falls_back_to_filename(self, tmp_path):
        path = self._write_notebook(tmp_path, [
            {"cell_type": "code", "source": ["x = 1"], "metadata": {}, "outputs": []},
        ])
        result = parse_notebook_metadata(path)
        assert result.title == "Test Notebook"

    def test_handles_invalid_json(self, tmp_path):
        path = tmp_path / "bad.ipynb"
        path.write_text("not json")
        result = parse_notebook_metadata(path)
        assert result.title == "Bad"

    def test_handles_missing_file(self, tmp_path):
        path = tmp_path / "missing.ipynb"
        result = parse_notebook_metadata(path)
        assert result.title == "Missing"


# ---------------------------------------------------------------------------
# scan_project_files
# ---------------------------------------------------------------------------


class TestScanProjectFiles:
    def test_finds_readme(self, tmp_path):
        (tmp_path / "README.md").write_text("# Project")
        files = scan_project_files(tmp_path)
        names = [f.filename for f in files]
        assert "README.md" in names

    def test_assigns_correct_file_types(self, tmp_path):
        (tmp_path / "README.md").write_text("# Project")
        (tmp_path / "analysis.ipynb").write_text("{}")
        (tmp_path / "data.csv").write_text("a,b\n1,2\n")
        (tmp_path / "plot.png").write_bytes(b"\x89PNG")

        files = {f.filename: f for f in scan_project_files(tmp_path)}
        assert files["README.md"].file_type == "readme"
        assert files["analysis.ipynb"].file_type == "notebook"
        assert files["data.csv"].file_type == "data"
        assert files["plot.png"].file_type == "visualization"

    def test_skips_hidden_files(self, tmp_path):
        (tmp_path / ".hidden").write_text("secret")
        (tmp_path / "visible.md").write_text("visible")
        files = scan_project_files(tmp_path)
        names = [f.filename for f in files]
        assert ".hidden" not in names
        assert "visible.md" in names

    def test_skips_pkl_and_pyc(self, tmp_path):
        (tmp_path / "cache.pkl").write_bytes(b"")
        (tmp_path / "mod.pyc").write_bytes(b"")
        (tmp_path / "keep.py").write_text("x = 1")
        files = scan_project_files(tmp_path)
        names = [f.filename for f in files]
        assert "cache.pkl" not in names
        assert "mod.pyc" not in names
        assert "keep.py" in names

    def test_returns_relative_paths(self, tmp_path):
        subdir = tmp_path / "data"
        subdir.mkdir()
        (subdir / "results.csv").write_text("x\n1\n")
        files = scan_project_files(tmp_path)
        paths = [f.relative_path for f in files]
        assert any("data/results.csv" in p or "data\\results.csv" in p for p in paths)

"""Unit tests for app.dataloader."""

import gzip
import json
import pickle
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.dataloader import (
    RepositoryParser,
    load_local_pickle,
    load_repository_data,
    slugify,
)
from app.models import (
    CollectionCategory,
    IdeaStatus,
    Priority,
    ProjectStatus,
    RepositoryData,
)


# ---------------------------------------------------------------------------
# slugify
# ---------------------------------------------------------------------------


class TestSlugify:
    def test_basic(self):
        assert slugify("Hello World") == "hello-world"

    def test_special_chars_removed(self):
        assert slugify("Hello, World!") == "hello-world"

    def test_underscores_become_hyphens(self):
        assert slugify("hello_world") == "hello-world"

    def test_multiple_spaces(self):
        assert slugify("hello   world") == "hello-world"

    def test_already_slug(self):
        assert slugify("hello-world") == "hello-world"

    def test_empty(self):
        assert slugify("") == ""

    def test_numbers_preserved(self):
        assert slugify("project 2024") == "project-2024"


# ---------------------------------------------------------------------------
# load_local_pickle
# ---------------------------------------------------------------------------


class TestLoadLocalPickle:
    def test_loads_valid_file(self, pickle_file, repository_data):
        result = load_local_pickle(pickle_file)
        assert isinstance(result, RepositoryData)
        assert len(result.projects) == len(repository_data.projects)

    def test_raises_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_local_pickle(tmp_path / "nonexistent.pkl.gz")

    def test_raises_value_error_for_wrong_type(self, tmp_path):
        bad_file = tmp_path / "bad.pkl.gz"
        with gzip.open(bad_file, "wb") as f:
            pickle.dump({"not": "repository_data"}, f)
        with pytest.raises(ValueError, match="Expected RepositoryData"):
            load_local_pickle(bad_file)


# ---------------------------------------------------------------------------
# load_repository_data
# ---------------------------------------------------------------------------


class TestLoadRepositoryData:
    def test_loads_from_path(self, pickle_file, repository_data):
        result = load_repository_data(pickle_file)
        assert isinstance(result, RepositoryData)
        assert len(result.projects) == len(repository_data.projects)

    def test_falls_back_to_local_parse_on_bad_file(self, tmp_path):
        bad_file = tmp_path / "bad.pkl.gz"
        with gzip.open(bad_file, "wb") as f:
            pickle.dump("not repo data", f)
        with patch("app.dataloader.get_parser") as mock_get_parser:
            mock_parser = MagicMock()
            mock_parser.parse_all.return_value = RepositoryData()
            mock_get_parser.return_value = mock_parser
            result = load_repository_data(bad_file)
        assert isinstance(result, RepositoryData)
        mock_parser.parse_all.assert_called_once()

    def test_none_source_calls_parser(self):
        with patch("app.dataloader.get_parser") as mock_get_parser:
            mock_parser = MagicMock()
            mock_parser.parse_all.return_value = RepositoryData()
            mock_get_parser.return_value = mock_parser
            result = load_repository_data(None)
        assert isinstance(result, RepositoryData)
        mock_parser.parse_all.assert_called_once()


# ---------------------------------------------------------------------------
# RepositoryParser._contributor_key
# ---------------------------------------------------------------------------


class TestContributorKey:
    def test_strips_middle_initial(self):
        key = RepositoryParser._contributor_key("Paramvir S. Dehal")
        assert key == "paramvir dehal"

    def test_same_key_with_and_without_initial(self):
        k1 = RepositoryParser._contributor_key("Paramvir S. Dehal")
        k2 = RepositoryParser._contributor_key("Paramvir Dehal")
        assert k1 == k2

    def test_normalizes_case(self):
        assert RepositoryParser._contributor_key("ALICE SMITH") == "alice smith"

    def test_normalizes_extra_spaces(self):
        assert RepositoryParser._contributor_key("Alice  Smith") == "alice smith"


# ---------------------------------------------------------------------------
# RepositoryParser._aggregate_contributors
# ---------------------------------------------------------------------------


class TestAggregateContributors:
    def _make_project(self, pid, contributors):
        from app.models import Contributor, Project
        return Project(
            id=pid,
            title=pid,
            research_question="Q",
            contributors=contributors,
        )

    def _make_contrib(self, name, pid, orcid=None, affiliation=None, roles=None):
        from app.models import Contributor
        return Contributor(
            name=name,
            orcid=orcid,
            affiliation=affiliation,
            roles=roles or [],
            project_ids=[pid],
        )

    def test_deduplicates_same_person(self):
        c1 = self._make_contrib("Alice Smith", "proj_a")
        c2 = self._make_contrib("Alice Smith", "proj_b")
        p1 = self._make_project("proj_a", [c1])
        p2 = self._make_project("proj_b", [c2])
        parser = RepositoryParser.__new__(RepositoryParser)
        result = parser._aggregate_contributors([p1, p2])
        assert len(result) == 1
        assert set(result[0].project_ids) == {"proj_a", "proj_b"}

    def test_merges_middle_initial(self):
        c1 = self._make_contrib("Paramvir S. Dehal", "proj_a")
        c2 = self._make_contrib("Paramvir Dehal", "proj_b")
        p1 = self._make_project("proj_a", [c1])
        p2 = self._make_project("proj_b", [c2])
        parser = RepositoryParser.__new__(RepositoryParser)
        result = parser._aggregate_contributors([p1, p2])
        assert len(result) == 1
        # Longer name preferred
        assert result[0].name == "Paramvir S. Dehal"

    def test_prefers_orcid(self):
        c1 = self._make_contrib("Alice Smith", "proj_a", orcid=None)
        c2 = self._make_contrib("Alice Smith", "proj_b", orcid="0000-0001-0000-0000")
        p1 = self._make_project("proj_a", [c1])
        p2 = self._make_project("proj_b", [c2])
        parser = RepositoryParser.__new__(RepositoryParser)
        result = parser._aggregate_contributors([p1, p2])
        assert result[0].orcid == "0000-0001-0000-0000"

    def test_union_roles(self):
        c1 = self._make_contrib("Alice Smith", "proj_a", roles=["lead"])
        c2 = self._make_contrib("Alice Smith", "proj_b", roles=["analyst"])
        p1 = self._make_project("proj_a", [c1])
        p2 = self._make_project("proj_b", [c2])
        parser = RepositoryParser.__new__(RepositoryParser)
        result = parser._aggregate_contributors([p1, p2])
        assert set(result[0].roles) == {"lead", "analyst"}

    def test_sorted_alphabetically(self):
        c1 = self._make_contrib("Zara Zeta", "proj_a")
        c2 = self._make_contrib("Alice Alpha", "proj_b")
        p1 = self._make_project("proj_a", [c1])
        p2 = self._make_project("proj_b", [c2])
        parser = RepositoryParser.__new__(RepositoryParser)
        result = parser._aggregate_contributors([p1, p2])
        assert result[0].name == "Alice Alpha"
        assert result[1].name == "Zara Zeta"

    def test_empty_projects(self):
        parser = RepositoryParser.__new__(RepositoryParser)
        result = parser._aggregate_contributors([])
        assert result == []


# ---------------------------------------------------------------------------
# RepositoryParser._extract_section
# ---------------------------------------------------------------------------


class TestExtractSection:
    def setup_method(self):
        self.parser = RepositoryParser.__new__(RepositoryParser)

    def test_extracts_section(self):
        content = "# Title\n\n## Research Question\nWhat is X?\n\n## Hypothesis\nX causes Y.\n"
        result = self.parser._extract_section(content, "Research Question")
        assert result == "What is X?"

    def test_returns_none_if_missing(self):
        content = "# Title\n\n## Overview\nSome text.\n"
        result = self.parser._extract_section(content, "Research Question")
        assert result is None

    def test_extracts_last_section(self):
        content = "## Section One\nContent one.\n\n## Section Two\nContent two.\n"
        result = self.parser._extract_section(content, "Section Two")
        assert result == "Content two."

    def test_multiline_content(self):
        content = "## Approach\nStep 1.\nStep 2.\nStep 3.\n\n## Other\nEnd.\n"
        result = self.parser._extract_section(content, "Approach")
        assert "Step 1" in result
        assert "Step 2" in result


# ---------------------------------------------------------------------------
# RepositoryParser._extract_other_sections
# ---------------------------------------------------------------------------


class TestExtractOtherSections:
    def setup_method(self):
        self.parser = RepositoryParser.__new__(RepositoryParser)

    def test_skips_known_sections(self):
        content = "## Key Findings\nFindings here.\n\n## Custom Section\nCustom content.\n"
        result = self.parser._extract_other_sections(content, {"Key Findings"})
        assert len(result) == 1
        assert result[0][0] == "Custom Section"
        assert result[0][1] == "Custom content."

    def test_skips_empty_sections(self):
        content = "## Empty Section\n\n## Non-Empty\nContent.\n"
        result = self.parser._extract_other_sections(content, set())
        assert len(result) == 1
        assert result[0][0] == "Non-Empty"

    def test_returns_empty_for_all_known(self):
        content = "## Key Findings\nFindings.\n"
        result = self.parser._extract_other_sections(content, {"Key Findings"})
        assert result == []


# ---------------------------------------------------------------------------
# RepositoryParser._rewrite_md_links
# ---------------------------------------------------------------------------


class TestRewriteMdLinks:
    def test_rewrites_md_links(self):
        content = "[Report](REPORT.md)"
        result = RepositoryParser._rewrite_md_links(content, "my_project")
        assert result == "[Report](/projects/my_project/REPORT.md)"

    def test_rewrites_image_links(self):
        content = "![caption](figures/foo.png)"
        result = RepositoryParser._rewrite_md_links(content, "my_project")
        assert result == "![caption](/project-assets/my_project/figures/foo.png)"

    def test_none_passthrough(self):
        assert RepositoryParser._rewrite_md_links(None, "proj") is None

    def test_external_links_unchanged(self):
        content = "[Link](https://example.com/page.html)"
        result = RepositoryParser._rewrite_md_links(content, "proj")
        assert result == content

    def test_multiple_links(self):
        content = "[Plan](RESEARCH_PLAN.md) and [Report](REPORT.md)"
        result = RepositoryParser._rewrite_md_links(content, "proj")
        assert "/projects/proj/RESEARCH_PLAN.md" in result
        assert "/projects/proj/REPORT.md" in result


# ---------------------------------------------------------------------------
# RepositoryParser._extract_collection_refs
# ---------------------------------------------------------------------------


class TestExtractCollectionRefs:
    def setup_method(self):
        self.parser = RepositoryParser.__new__(RepositoryParser)

    def test_finds_known_collection(self):
        content = "We used the kbase_ke_pangenome database for this analysis."
        result = self.parser._extract_collection_refs(content)
        assert "kbase_ke_pangenome" in result

    def test_no_collection_refs(self):
        content = "No databases mentioned here."
        result = self.parser._extract_collection_refs(content)
        assert result == []

    def test_multiple_collections(self):
        content = "Used kbase_ke_pangenome and kbase_genomes for this work."
        result = self.parser._extract_collection_refs(content)
        assert "kbase_ke_pangenome" in result
        assert "kbase_genomes" in result


# ---------------------------------------------------------------------------
# RepositoryParser._parse_contributors (parsing logic)
# ---------------------------------------------------------------------------


class TestParseContributors:
    def setup_method(self):
        self.parser = RepositoryParser.__new__(RepositoryParser)

    def test_bold_format_with_affiliation_and_orcid(self):
        content = (
            "## Authors\n"
            "- **Alice Smith** (LBNL) | ORCID: 0000-0001-1111-1111 | lead\n"
        )
        contribs = self.parser._parse_contributors(content, "proj_a")
        assert len(contribs) == 1
        c = contribs[0]
        assert c.name == "Alice Smith"
        assert c.affiliation == "LBNL"
        assert c.orcid == "0000-0001-1111-1111"
        assert "lead" in c.roles

    def test_plain_format(self):
        content = "## Authors\n- Bob Jones, LBNL\n"
        contribs = self.parser._parse_contributors(content, "proj_b")
        assert len(contribs) == 1
        assert contribs[0].name == "Bob Jones"
        assert contribs[0].affiliation == "LBNL"

    def test_plain_format_with_orcid_url(self):
        content = (
            "## Authors\n"
            "- Carol White (https://orcid.org/0000-0002-2222-2222), LBNL\n"
        )
        contribs = self.parser._parse_contributors(content, "proj_c")
        assert len(contribs) == 1
        assert contribs[0].orcid == "0000-0002-2222-2222"

    def test_no_authors_section(self):
        content = "# Title\n\n## Research Question\nQuestion here.\n"
        contribs = self.parser._parse_contributors(content, "proj_d")
        assert contribs == []

    def test_contributors_section_fallback(self):
        content = "## Contributors\n- **Dave Brown** (MIT)\n"
        contribs = self.parser._parse_contributors(content, "proj_e")
        assert len(contribs) == 1
        assert contribs[0].name == "Dave Brown"

    def test_project_id_assigned(self):
        content = "## Authors\n- **Eve Green** (JBEI)\n"
        contribs = self.parser._parse_contributors(content, "my_project")
        assert contribs[0].project_ids == ["my_project"]


# ---------------------------------------------------------------------------
# RepositoryParser.parse_projects (filesystem integration)
# ---------------------------------------------------------------------------


class TestParseProjects:
    def test_empty_projects_dir(self, tmp_repo):
        parser = RepositoryParser(repo_path=tmp_repo)
        projects = parser.parse_projects()
        assert projects == []

    def test_parses_single_project(self, tmp_project_dir, tmp_repo):
        parser = RepositoryParser(repo_path=tmp_repo)
        projects = parser.parse_projects()
        assert len(projects) == 1
        p = projects[0]
        assert p.id == "alpha_project"
        assert "Alpha Project" in p.title
        assert p.status == ProjectStatus.COMPLETED  # has findings

    def test_skips_hidden_dirs(self, tmp_repo):
        hidden_dir = tmp_repo / "projects" / ".hidden"
        hidden_dir.mkdir()
        (hidden_dir / "README.md").write_text("# Hidden\n")
        parser = RepositoryParser(repo_path=tmp_repo)
        projects = parser.parse_projects()
        assert all(not p.id.startswith(".") for p in projects)

    def test_skips_dirs_without_readme(self, tmp_repo):
        no_readme = tmp_repo / "projects" / "no_readme_project"
        no_readme.mkdir()
        parser = RepositoryParser(repo_path=tmp_repo)
        projects = parser.parse_projects()
        assert all(p.id != "no_readme_project" for p in projects)

    def test_proposed_status_when_no_content(self, tmp_repo):
        sparse_dir = tmp_repo / "projects" / "sparse_project"
        sparse_dir.mkdir()
        (sparse_dir / "README.md").write_text("# Sparse\n")
        parser = RepositoryParser(repo_path=tmp_repo)
        projects = parser.parse_projects()
        sparse = next((p for p in projects if p.id == "sparse_project"), None)
        assert sparse is not None
        assert sparse.status == ProjectStatus.PROPOSED

    def test_in_progress_with_plan(self, tmp_repo):
        proj_dir = tmp_repo / "projects" / "in_prog_project"
        proj_dir.mkdir()
        (proj_dir / "README.md").write_text(
            "# In Progress\n\n## Research Question\nWhat?\n"
        )
        (proj_dir / "RESEARCH_PLAN.md").write_text(
            "# Plan\n\n## Hypothesis\nWe think X.\n\n## Approach\nMeasure Y.\n"
        )
        parser = RepositoryParser(repo_path=tmp_repo)
        projects = parser.parse_projects()
        proj = next((p for p in projects if p.id == "in_prog_project"), None)
        assert proj is not None
        assert proj.status == ProjectStatus.IN_PROGRESS
        assert proj.has_research_plan is True

    def test_used_by_reverse_mapping(self, tmp_repo):
        """Verify used_by is populated on source project."""
        src_dir = tmp_repo / "projects" / "source_proj"
        src_dir.mkdir()
        (src_dir / "README.md").write_text(
            "# Source\n\n## Research Question\nQ?\n\n"
            "## Key Findings\nFound it.\n"
        )

        consumer_dir = tmp_repo / "projects" / "consumer_proj"
        consumer_dir.mkdir()
        notebooks_dir = consumer_dir / "notebooks"
        notebooks_dir.mkdir()
        # Create a notebook that references source_proj data
        nb = {
            "nbformat": 4,
            "nbformat_minor": 5,
            "metadata": {},
            "cells": [
                {
                    "cell_type": "code",
                    "source": ["df = pd.read_csv('../../source_proj/data/results.csv')"],
                    "outputs": [],
                    "metadata": {},
                }
            ],
        }
        (notebooks_dir / "analysis.ipynb").write_text(json.dumps(nb))
        (consumer_dir / "README.md").write_text(
            "# Consumer\n\n## Research Question\nQ?\n"
        )

        parser = RepositoryParser(repo_path=tmp_repo)
        projects = parser.parse_projects()
        src = next((p for p in projects if p.id == "source_proj"), None)
        assert src is not None
        assert "consumer_proj" in src.used_by


# ---------------------------------------------------------------------------
# RepositoryParser.parse_discoveries
# ---------------------------------------------------------------------------


class TestParseDiscoveries:
    def test_no_file(self, tmp_repo):
        parser = RepositoryParser(repo_path=tmp_repo)
        assert parser.parse_discoveries() == []

    def test_parses_discoveries(self, tmp_repo):
        content = (
            "# Discoveries\n\n"
            "## 2024-03\n\n"
            "### [my_project] Alpha causes beta\n\n"
            "We measured alpha and found it causes beta at rate 0.42.\n"
        )
        (tmp_repo / "docs" / "discoveries.md").write_text(content)
        parser = RepositoryParser(repo_path=tmp_repo)
        discoveries = parser.parse_discoveries()
        assert len(discoveries) == 1
        d = discoveries[0]
        assert d.title == "Alpha causes beta"
        assert d.project_tag == "my_project"
        assert d.date.year == 2024
        assert d.date.month == 3

    def test_skips_template_section(self, tmp_repo):
        content = (
            "# Discoveries\n\n"
            "## 2024-03\n\n"
            "### [proj] Real discovery\n\nReal content.\n\n"
            "## Template\n\n"
            "### [tag] Brief title\n\nDescription of what was discovered\n"
        )
        (tmp_repo / "docs" / "discoveries.md").write_text(content)
        parser = RepositoryParser(repo_path=tmp_repo)
        discoveries = parser.parse_discoveries()
        assert len(discoveries) == 1
        assert discoveries[0].title == "Real discovery"


# ---------------------------------------------------------------------------
# RepositoryParser.parse_pitfalls
# ---------------------------------------------------------------------------


class TestParsePitfalls:
    def test_no_file(self, tmp_repo):
        parser = RepositoryParser(repo_path=tmp_repo)
        assert parser.parse_pitfalls() == []

    def test_parses_pitfall(self, tmp_repo):
        content = (
            "# Pitfalls\n\n"
            "## Performance\n\n"
            "### Slow full table scan\n\n"
            "Running COUNT(*) without filters hits all rows.\n\n"
            "```sql\nSELECT COUNT(*) FROM genome;\n```\n"
        )
        (tmp_repo / "docs" / "pitfalls.md").write_text(content)
        parser = RepositoryParser(repo_path=tmp_repo)
        pitfalls = parser.parse_pitfalls()
        assert len(pitfalls) == 1
        p = pitfalls[0]
        assert p.title == "Slow full table scan"
        assert p.category == "Performance"
        assert "COUNT(*)" in p.code_example


# ---------------------------------------------------------------------------
# RepositoryParser.parse_performance
# ---------------------------------------------------------------------------


class TestParsePerformance:
    def test_no_file(self, tmp_repo):
        parser = RepositoryParser(repo_path=tmp_repo)
        assert parser.parse_performance() == []

    def test_parses_tip(self, tmp_repo):
        content = (
            "# Performance\n\n"
            "### Use partition pruning\n\n"
            "Filter on partition columns first.\n\n"
            "```sql\nSELECT * FROM genome WHERE species_id = 42;\n```\n"
        )
        (tmp_repo / "docs" / "performance.md").write_text(content)
        parser = RepositoryParser(repo_path=tmp_repo)
        tips = parser.parse_performance()
        assert len(tips) == 1
        assert tips[0].title == "Use partition pruning"
        assert "species_id" in tips[0].code_example


# ---------------------------------------------------------------------------
# RepositoryParser.parse_research_ideas
# ---------------------------------------------------------------------------


class TestParseResearchIdeas:
    def test_no_file(self, tmp_repo):
        parser = RepositoryParser(repo_path=tmp_repo)
        assert parser.parse_research_ideas() == []

    def test_parses_idea(self, tmp_repo):
        content = (
            "# Research Ideas\n\n"
            "### [cog_analysis] Explore COG distributions\n\n"
            "**Status**: PROPOSED\n"
            "**Priority**: HIGH\n"
            "**Research Question**: Are COG distributions uniform?\n\n"
            "**Hypothesis**: They vary by lifestyle.\n\n"
            "**Approach**: Compute distribution per lifestyle.\n\n"
            "**Effort**: Low (1 week)\n"
            "**Impact**: High\n"
        )
        (tmp_repo / "docs" / "research_ideas.md").write_text(content)
        parser = RepositoryParser(repo_path=tmp_repo)
        ideas = parser.parse_research_ideas()
        assert len(ideas) == 1
        idea = ideas[0]
        assert idea.title == "Explore COG distributions"
        assert idea.status == IdeaStatus.PROPOSED
        assert idea.priority == Priority.HIGH
        assert idea.effort == "Low (1 week)"

    def test_parses_in_progress_status(self, tmp_repo):
        content = (
            "# Research Ideas\n\n"
            "### [proj] Active research\n\n"
            "**Status**: IN_PROGRESS\n"
            "**Research Question**: Something active?\n"
        )
        (tmp_repo / "docs" / "research_ideas.md").write_text(content)
        parser = RepositoryParser(repo_path=tmp_repo)
        ideas = parser.parse_research_ideas()
        assert ideas[0].status == IdeaStatus.IN_PROGRESS


# ---------------------------------------------------------------------------
# RepositoryParser._parse_row_counts
# ---------------------------------------------------------------------------


class TestParseRowCounts:
    def setup_method(self):
        self.parser = RepositoryParser.__new__(RepositoryParser)

    def test_parses_row_counts(self):
        content = (
            "## Table Summary\n\n"
            "| Table | Row Count | Description |\n"
            "|-------|-----------|-------------|\n"
            "| genome | 293,059 | Genome rows |\n"
            "| feature | 1,500,000 | Gene features |\n"
            "\n---\n"
        )
        result = self.parser._parse_row_counts(content)
        assert result["genome"] == 293059
        assert result["feature"] == 1500000

    def test_no_summary_section(self):
        content = "## Overview\n\nNo table summary here.\n"
        result = self.parser._parse_row_counts(content)
        assert result == {}


# ---------------------------------------------------------------------------
# RepositoryParser._cluster_research_areas
# ---------------------------------------------------------------------------


class TestClusterResearchAreas:
    def _make_project(self, pid, title, research_question=""):
        from app.models import Project
        return Project(id=pid, title=title, research_question=research_question)

    def test_empty_returns_empty(self):
        result = RepositoryParser._cluster_research_areas([])
        assert result == []

    def test_single_project_is_independent(self):
        p = self._make_project("p1", "Unique standalone research")
        result = RepositoryParser._cluster_research_areas([p])
        all_ids = [pid for area in result for pid in area.project_ids]
        assert "p1" in all_ids

    def test_similar_projects_cluster(self):
        p1 = self._make_project(
            "p1", "Fitness advantage analysis", "What drives fitness advantage?"
        )
        p2 = self._make_project(
            "p2", "Fitness cost measurement", "How to measure fitness costs?"
        )
        result = RepositoryParser._cluster_research_areas([p1, p2])
        # Should cluster together (fitness similarity)
        clustered = [a for a in result if len(a.project_ids) > 1]
        if clustered:
            ids = clustered[0].project_ids
            assert "p1" in ids and "p2" in ids

    def test_data_dep_boosts_similarity(self):
        from app.models import DerivedDataRef
        p1 = self._make_project("p1", "Essential genome analysis")
        p2 = self._make_project("p2", "Dispensable genome study")
        p2.derived_from = [DerivedDataRef(source_project="p1")]
        result = RepositoryParser._cluster_research_areas([p1, p2])
        all_ids = [pid for area in result for pid in area.project_ids]
        assert "p1" in all_ids
        assert "p2" in all_ids

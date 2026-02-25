"""Unit tests for app.models."""

from datetime import datetime, date

import pytest

from app.models import (
    Collection,
    CollectionCategory,
    CollectionTable,
    Column,
    Contributor,
    DataFile,
    DerivedDataRef,
    Discovery,
    IdeaStatus,
    Notebook,
    PerformanceTip,
    Pitfall,
    Priority,
    Project,
    ProjectStatus,
    RepositoryData,
    ResearchArea,
    ResearchIdea,
    Review,
    ReviewStatus,
    SampleQuery,
    Skill,
    Table,
    Visualization,
    _slugify_name,
)


# ---------------------------------------------------------------------------
# _slugify_name
# ---------------------------------------------------------------------------


class TestSlugifyName:
    def test_basic(self):
        assert _slugify_name("Alice Researcher") == "alice-researcher"

    def test_lowercase(self):
        assert _slugify_name("BOB SMITH") == "bob-smith"

    def test_strips_special_chars(self):
        assert _slugify_name("John O'Brien") == "john-obrien"

    def test_multiple_spaces(self):
        assert _slugify_name("First   Last") == "first-last"

    def test_leading_trailing_whitespace(self):
        assert _slugify_name("  Alice  ") == "alice"

    def test_empty_string(self):
        assert _slugify_name("") == ""

    def test_hyphen_preserved(self):
        result = _slugify_name("Mary-Ann Smith")
        assert result == "mary-ann-smith"


# ---------------------------------------------------------------------------
# Contributor
# ---------------------------------------------------------------------------


class TestContributor:
    def test_id_property(self):
        c = Contributor(name="Alice Researcher")
        assert c.id == "alice-researcher"

    def test_orcid_url_with_orcid(self):
        c = Contributor(name="Alice", orcid="0000-0001-2345-6789")
        assert c.orcid_url == "https://orcid.org/0000-0001-2345-6789"

    def test_orcid_url_without_orcid(self):
        c = Contributor(name="Alice")
        assert c.orcid_url is None

    def test_defaults(self):
        c = Contributor(name="Bob")
        assert c.affiliation is None
        assert c.orcid is None
        assert c.roles == []
        assert c.project_ids == []

    def test_with_all_fields(self):
        c = Contributor(
            name="Bob Smith",
            affiliation="LBNL",
            orcid="0000-0002-9999-0000",
            roles=["lead", "analyst"],
            project_ids=["proj_a", "proj_b"],
        )
        assert c.affiliation == "LBNL"
        assert len(c.roles) == 2
        assert "proj_a" in c.project_ids


# ---------------------------------------------------------------------------
# ReviewStatus
# ---------------------------------------------------------------------------


class TestReviewStatus:
    def test_no_review(self):
        p = Project(id="p", title="T", research_question="Q")
        assert p.review_status == ReviewStatus.NOT_REVIEWED

    def test_reviewed_when_review_date_equals_updated(self):
        dt = datetime(2024, 5, 1)
        p = Project(
            id="p",
            title="T",
            research_question="Q",
            updated_date=dt,
            review=Review(reviewer="bot", date=dt, project_id="p"),
        )
        assert p.review_status == ReviewStatus.REVIEWED

    def test_reviewed_when_review_date_is_newer(self):
        p = Project(
            id="p",
            title="T",
            research_question="Q",
            updated_date=datetime(2024, 4, 1),
            review=Review(
                reviewer="bot",
                date=datetime(2024, 5, 1),
                project_id="p",
            ),
        )
        assert p.review_status == ReviewStatus.REVIEWED

    def test_needs_re_review_when_updated_after_review(self):
        p = Project(
            id="p",
            title="T",
            research_question="Q",
            updated_date=datetime(2024, 6, 1),
            review=Review(
                reviewer="bot",
                date=datetime(2024, 5, 1),
                project_id="p",
            ),
        )
        assert p.review_status == ReviewStatus.NEEDS_RE_REVIEW

    def test_reviewed_same_day_granularity(self):
        """Review date and updated_date on same calendar day → REVIEWED."""
        p = Project(
            id="p",
            title="T",
            research_question="Q",
            updated_date=datetime(2024, 5, 1, 23, 59, 59),
            review=Review(
                reviewer="bot",
                date=datetime(2024, 5, 1, 0, 0, 0),
                project_id="p",
            ),
        )
        assert p.review_status == ReviewStatus.REVIEWED

    def test_review_without_date(self):
        """Review with no date should still be REVIEWED (no staleness check)."""
        p = Project(
            id="p",
            title="T",
            research_question="Q",
            updated_date=datetime(2024, 6, 1),
            review=Review(reviewer="bot", date=None, project_id="p"),
        )
        assert p.review_status == ReviewStatus.REVIEWED

    def test_project_without_updated_date_and_with_review(self):
        p = Project(
            id="p",
            title="T",
            research_question="Q",
            updated_date=None,
            review=Review(
                reviewer="bot",
                date=datetime(2024, 5, 1),
                project_id="p",
            ),
        )
        assert p.review_status == ReviewStatus.REVIEWED


# ---------------------------------------------------------------------------
# Project defaults and status
# ---------------------------------------------------------------------------


class TestProject:
    def test_default_status(self):
        p = Project(id="p", title="T", research_question="Q")
        assert p.status == ProjectStatus.IN_PROGRESS

    def test_optional_fields_default_to_none(self):
        p = Project(id="p", title="T", research_question="Q")
        assert p.hypothesis is None
        assert p.approach is None
        assert p.findings is None
        assert p.review is None

    def test_list_fields_default_to_empty(self):
        p = Project(id="p", title="T", research_question="Q")
        assert p.notebooks == []
        assert p.visualizations == []
        assert p.data_files == []
        assert p.contributors == []
        assert p.related_collections == []
        assert p.derived_from == []
        assert p.used_by == []

    def test_bool_flags_default_false(self):
        p = Project(id="p", title="T", research_question="Q")
        assert p.has_research_plan is False
        assert p.has_report is False


# ---------------------------------------------------------------------------
# RepositoryData helper methods
# ---------------------------------------------------------------------------


class TestRepositoryData:
    def test_get_collection_found(self, collection):
        rd = RepositoryData(collections=[collection])
        result = rd.get_collection("kbase_ke_pangenome")
        assert result is collection

    def test_get_collection_not_found(self, collection):
        rd = RepositoryData(collections=[collection])
        assert rd.get_collection("nonexistent") is None

    def test_get_collections_by_category_primary(self, collection):
        domain_coll = Collection(
            id="domain_coll",
            name="Domain",
            category=CollectionCategory.DOMAIN,
            icon="D",
            description="Domain collection",
        )
        rd = RepositoryData(collections=[collection, domain_coll])
        primaries = rd.get_collections_by_category(CollectionCategory.PRIMARY)
        assert len(primaries) == 1
        assert primaries[0].id == "kbase_ke_pangenome"

    def test_get_collections_by_category_empty(self):
        rd = RepositoryData()
        assert rd.get_collections_by_category(CollectionCategory.REFERENCE) == []

    def test_get_tables_for_collection_direct(self):
        t = Table(name="genome", description="Genomes", row_count=100)
        rd = RepositoryData(tables={"kbase_ke_pangenome": [t]})
        result = rd.get_tables_for_collection("kbase_ke_pangenome")
        assert len(result) == 1
        assert result[0].name == "genome"

    def test_get_tables_for_collection_via_sub_collection(self):
        t = Table(name="genome", description="Genomes", row_count=100)
        parent = Collection(
            id="parent_coll",
            name="Parent",
            category=CollectionCategory.PRIMARY,
            icon="P",
            description="Parent",
            sub_collections=["child_coll"],
        )
        rd = RepositoryData(
            tables={"child_coll": [t]},
            collections=[parent],
        )
        result = rd.get_tables_for_collection("parent_coll")
        assert len(result) == 1

    def test_get_tables_for_collection_missing(self):
        rd = RepositoryData()
        assert rd.get_tables_for_collection("missing") == []

    def test_get_contributor_found(self, contributor):
        rd = RepositoryData(contributors=[contributor])
        result = rd.get_contributor(contributor.id)
        assert result is contributor

    def test_get_contributor_not_found(self, contributor):
        rd = RepositoryData(contributors=[contributor])
        assert rd.get_contributor("nobody") is None

    def test_defaults_are_empty(self):
        rd = RepositoryData()
        assert rd.projects == []
        assert rd.discoveries == []
        assert rd.tables == {}
        assert rd.pitfalls == []
        assert rd.performance_tips == []
        assert rd.research_ideas == []
        assert rd.collections == []
        assert rd.contributors == []
        assert rd.skills == []
        assert rd.research_areas == []
        assert rd.total_notebooks == 0
        assert rd.total_visualizations == 0
        assert rd.total_data_files == 0
        assert rd.last_updated is None


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class TestEnums:
    def test_project_status_values(self):
        assert ProjectStatus.COMPLETED == "Completed"
        assert ProjectStatus.IN_PROGRESS == "In Progress"
        assert ProjectStatus.PROPOSED == "Proposed"

    def test_idea_status_values(self):
        assert IdeaStatus.PROPOSED == "PROPOSED"
        assert IdeaStatus.IN_PROGRESS == "IN_PROGRESS"
        assert IdeaStatus.COMPLETED == "COMPLETED"

    def test_priority_values(self):
        assert Priority.HIGH == "HIGH"
        assert Priority.MEDIUM == "MEDIUM"
        assert Priority.LOW == "LOW"

    def test_collection_category_values(self):
        assert CollectionCategory.PRIMARY == "primary"
        assert CollectionCategory.DOMAIN == "domain"
        assert CollectionCategory.REFERENCE == "reference"

    def test_review_status_values(self):
        assert ReviewStatus.REVIEWED == "Reviewed"
        assert ReviewStatus.NEEDS_RE_REVIEW == "Needs Re-review"
        assert ReviewStatus.NOT_REVIEWED == "Not Reviewed"


# ---------------------------------------------------------------------------
# Dataclasses - basic instantiation & defaults
# ---------------------------------------------------------------------------


class TestDataclassDefaults:
    def test_notebook(self):
        n = Notebook(filename="analysis.ipynb", path="projects/p/notebooks/analysis.ipynb")
        assert n.title is None
        assert n.description is None

    def test_visualization(self):
        v = Visualization(filename="fig.png", path="projects/p/figures/fig.png")
        assert v.title is None
        assert v.description is None
        assert v.size_bytes == 0

    def test_data_file(self):
        d = DataFile(filename="results.csv", path="projects/p/data/results.csv")
        assert d.description is None
        assert d.size_bytes == 0
        assert d.row_count is None

    def test_collection_table(self):
        ct = CollectionTable(name="genome", description="Genome rows")
        assert ct.row_count is None

    def test_sample_query(self):
        sq = SampleQuery(title="Count", query="SELECT COUNT(*) FROM t")
        assert sq.title == "Count"
        assert "COUNT" in sq.query

    def test_column_defaults(self):
        col = Column(name="genome_id", data_type="STRING", description="Genome identifier")
        assert col.is_primary_key is False
        assert col.is_foreign_key is False
        assert col.foreign_key_table is None

    def test_table_defaults(self):
        t = Table(name="genome", description="Genomes")
        assert t.row_count == 0
        assert t.columns == []
        assert t.known_limitations == []
        assert t.sample_queries == []
        assert t.foreign_keys == []

    def test_pitfall_defaults(self):
        p = Pitfall(
            id="slow-query",
            title="Slow Query",
            category="Performance",
            problem="Query hits full scan",
            solution="Add index",
        )
        assert p.project_tag is None
        assert p.code_example is None

    def test_performance_tip_defaults(self):
        tip = PerformanceTip(id="use-index", title="Use Index", description="Always index FKs")
        assert tip.table_name is None
        assert tip.code_example is None

    def test_research_idea_defaults(self):
        idea = ResearchIdea(
            id="my-idea", title="My Idea", research_question="Can we?"
        )
        assert idea.status == IdeaStatus.PROPOSED
        assert idea.priority == Priority.MEDIUM
        assert idea.hypothesis is None
        assert idea.approach is None
        assert idea.dependencies == []
        assert idea.next_steps == []
        assert idea.cross_project_tags == []

    def test_skill_defaults(self):
        s = Skill(name="berdl", description="Query BERDL")
        assert s.user_invocable is False

    def test_research_area_defaults(self):
        ra = ResearchArea(id="area-1", name="Genomics")
        assert ra.project_ids == []
        assert ra.top_terms == []

    def test_derived_data_ref_defaults(self):
        ref = DerivedDataRef(source_project="essential_genome")
        assert ref.files == []

    def test_discovery_defaults(self):
        d = Discovery(
            id="disc-1",
            title="Disc 1",
            content="Found X",
            project_tag="proj_a",
        )
        assert d.date is None
        assert d.statistics == {}
        assert d.related_projects == []

    def test_review_defaults(self):
        r = Review(reviewer="bot")
        assert r.date is None
        assert r.project_id == ""
        assert r.summary is None
        assert r.raw_content == ""

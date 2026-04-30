"""Shared pytest fixtures for the BERIL Observatory UI test suite."""

import gzip
import pickle
from collections.abc import AsyncGenerator
from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import Base
from app.db.session import get_db

from app.models import (
    Collection,
    CollectionCategory,
    CollectionTable,
    Contributor,
    Discovery,
    IdeaStatus,
    PerformanceTip,
    Pitfall,
    Priority,
    Project,
    ProjectStatus,
    RepositoryData,
    ResearchArea,
    ResearchIdea,
    Review,
    SampleQuery,
    Skill,
    WikiIndex,
    WikiLink,
    WikiPage,
)


# ---------------------------------------------------------------------------
# Basic model fixture helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def contributor():
    return Contributor(
        name="Alice Researcher",
        affiliation="Lawrence Berkeley National Laboratory",
        orcid="0000-0001-2345-6789",
        roles=["lead"],
        project_ids=["project_a"],
    )


@pytest.fixture
def project(contributor):
    return Project(
        id="test_project",
        title="Test Research Project",
        research_question="What is the answer?",
        status=ProjectStatus.IN_PROGRESS,
        hypothesis="We think X causes Y",
        approach="We will measure Z",
        findings=None,
        contributors=[contributor],
        created_date=datetime(2024, 1, 1),
        updated_date=datetime(2024, 6, 1),
        related_collections=["kbase_ke_pangenome"],
    )


@pytest.fixture
def completed_project(contributor):
    return Project(
        id="completed_project",
        title="Completed Research Project",
        research_question="Why does A happen?",
        status=ProjectStatus.COMPLETED,
        findings="A happens because of B and C.",
        contributors=[contributor],
        created_date=datetime(2023, 1, 1),
        updated_date=datetime(2023, 12, 1),
    )


@pytest.fixture
def review():
    return Review(
        reviewer="BERIL Automated Review",
        date=datetime(2024, 5, 1),
        project_id="test_project",
        summary="Good work overall.",
        methodology="Sound methodology.",
        code_quality="Clean code.",
        findings_assessment="Findings are well-supported.",
        suggestions="Consider adding more samples.",
    )


@pytest.fixture
def collection():
    return Collection(
        id="kbase_ke_pangenome",
        name="KBase Pangenome",
        category=CollectionCategory.PRIMARY,
        icon="&#127757;",
        description="Primary pangenome collection.",
        key_tables=[
            CollectionTable(name="genome", description="Genomes", row_count=293059)
        ],
        sample_queries=[
            SampleQuery(title="Count genomes", query="SELECT COUNT(*) FROM genome")
        ],
        related_collections=["kbase_genomes"],
        tenant_id="kbase",
        tenant_name="KBase",
        snapshot_source="test snapshot",
        discovered_at="2026-04-29T00:00:00+00:00",
        schema_status="discovered",
        curation_status="curated",
    )


@pytest.fixture
def repository_data(project, completed_project, collection):
    discovery = Discovery(
        id="test-discovery",
        title="Test Discovery",
        content="We found something interesting.",
        project_tag="test_project",
        date=datetime(2024, 3, 1),
    )
    idea = ResearchIdea(
        id="test-idea",
        title="Test Idea",
        research_question="Can we do X?",
        status=IdeaStatus.PROPOSED,
        priority=Priority.HIGH,
    )
    pitfall = Pitfall(
        id="test-pitfall",
        title="Test Pitfall",
        category="Performance",
        problem="Query is slow",
        solution="Add an index",
    )
    tip = PerformanceTip(
        id="test-tip",
        title="Use indexes",
        description="Always index on foreign keys.",
    )
    skill = Skill(
        name="berdl",
        description="Query BERDL databases.",
        user_invocable=True,
    )
    area = ResearchArea(
        id="test-area",
        name="Test Area",
        project_ids=["test_project", "completed_project"],
        top_terms=["gene", "fitness"],
    )
    atlas_page = WikiPage(
        id="atlas.test",
        title="Test BERIL Atlas",
        type="atlas",
        status="draft",
        summary="Test atlas summary.",
        path="atlas",
        body="# Test BERIL Atlas\n\nAtlas body.",
        source_projects=[],
        source_docs=["docs/discoveries.md"],
        related_collections=[],
        related_pages=["topic.test"],
        confidence="medium",
        generated_by="pytest",
        last_reviewed="2026-04-28",
        section="root",
        order=1,
    )
    section_pages = [
        WikiPage(
            id=f"{section}.index",
            title=title,
            type="meta",
            status="draft",
            summary=f"{title} summary.",
            path=f"{section}/index",
            body=f"# {title}\n\nSection body.",
            source_projects=[],
            source_docs=["docs/discoveries.md"],
            related_collections=[],
            confidence="medium",
            generated_by="pytest",
            last_reviewed="2026-04-28",
            section=section,
            order=1,
        )
        for section, title in [
            ("topics", "Topics"),
            ("data", "Data"),
            ("claims", "Claims"),
            ("conflicts", "Tensions"),
            ("directions", "Directions"),
            ("hypotheses", "Hypotheses"),
        ]
    ]
    topic_page = WikiPage(
        id="topic.test",
        title="Test Atlas Topic",
        type="topic",
        status="draft",
        summary="Test topic summary.",
        path="topics/test",
        body="# Test Atlas Topic\n\n## Synthesis\n\nTopic body.",
        source_projects=["test_project"],
        source_docs=[],
        related_collections=["kbase_ke_pangenome"],
        confidence="medium",
        generated_by="pytest",
        last_reviewed="2026-04-28",
        section="topics",
        order=10,
    )
    reuse_page = WikiPage(
        id="data.reuse",
        title="Derived Data Reuse Graph",
        type="meta",
        status="draft",
        summary="Reuse graph summary.",
        path="data/reuse",
        body="# Derived Data Reuse Graph\n\nReuse body.",
        source_docs=["docs/discoveries.md"],
        related_collections=["kbase_ke_pangenome"],
        confidence="medium",
        generated_by="pytest",
        last_reviewed="2026-04-28",
        section="data",
        order=2,
    )
    derived_page = WikiPage(
        id="data.test-product",
        title="Test Derived Product",
        type="derived_product",
        status="draft",
        summary="Test derived product summary.",
        path="data/derived-products/test-product",
        body="# Test Derived Product\n\nProduct body.",
        source_projects=["test_project"],
        source_docs=["docs/discoveries.md"],
        related_collections=["kbase_ke_pangenome"],
        confidence="medium",
        generated_by="pytest",
        last_reviewed="2026-04-28",
        section="data",
        order=3,
        metadata={
            "product_kind": "score",
            "reuse_status": "promoted",
            "produced_by_projects": ["test_project"],
            "used_by_projects": ["completed_project"],
            "output_artifacts": [{"path": "planned:test"}],
            "review_routes": ["test_project"],
            "evidence": [{"source": "test_project", "support": "Test support."}],
        },
    )
    conflict_page = WikiPage(
        id="conflict.test",
        title="Test Tension",
        type="conflict",
        status="draft",
        summary="Test conflict summary.",
        path="conflicts/test",
        body="# Test Tension\n\nConflict body.",
        source_projects=["test_project", "completed_project"],
        source_docs=["docs/discoveries.md"],
        related_collections=["kbase_ke_pangenome"],
        related_pages=["topic.test"],
        confidence="medium",
        generated_by="pytest",
        last_reviewed="2026-04-28",
        section="conflicts",
        order=10,
        metadata={
            "conflict_status": "unresolved",
            "affected_pages": ["topic.test"],
            "evidence_sides": [
                {"side": "a", "support": "A"},
                {"side": "b", "support": "B"},
            ],
            "resolving_work": ["Test resolution."],
        },
    )
    return RepositoryData(
        projects=[project, completed_project],
        discoveries=[discovery],
        pitfalls=[pitfall],
        performance_tips=[tip],
        research_ideas=[idea],
        collections=[collection],
        contributors=[project.contributors[0]],
        skills=[skill],
        research_areas=[area],
        wiki_index=WikiIndex(
            pages=[
                atlas_page,
                *section_pages,
                topic_page,
                reuse_page,
                derived_page,
                conflict_page,
            ],
            links=[WikiLink(source_id="atlas.test", target_id="topic.test")],
        ),
        total_notebooks=2,
        total_visualizations=3,
        total_data_files=1,
        last_updated=datetime(2024, 6, 15),
    )

@pytest.fixture
def app_data_context(repository_data: RepositoryData):
    return {
        "app_name": "BERIL Test App",
        "total_genomes": "500",
        "total_species": "100",
        "total_genes": 10000,
        "project_count": len(repository_data.projects),
        "discovery_count": len(repository_data.discoveries),
        "idea_count": len(repository_data.research_ideas),
        "collection_count": len(repository_data.collections),
        "contributor_count": len(repository_data.contributors),
        "skill_count": len(repository_data.skills),
        "atlas_count": len(repository_data.wiki_index.pages),
        "last_updated": repository_data.last_updated,
    }

# ---------------------------------------------------------------------------
# File system fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_repo(tmp_path):
    """Create a minimal fake repository directory structure."""
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir()
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "schemas").mkdir()
    return tmp_path


@pytest.fixture
def tmp_project_dir(tmp_repo):
    """Create a single project directory with a README."""
    project_dir = tmp_repo / "projects" / "alpha_project"
    project_dir.mkdir()
    readme = project_dir / "README.md"
    readme.write_text(
        "# Alpha Project\n\n"
        "## Research Question\nDoes alpha cause beta?\n\n"
        "## Hypothesis\nAlpha causes beta via gamma.\n\n"
        "## Approach\nMeasure gamma concentration.\n\n"
        "## Authors\n- **Alice Researcher** (LBNL) | ORCID: 0000-0001-2345-6789\n\n"
        "## Key Findings\nAlpha does cause beta at rate 0.42.\n"
    )
    return project_dir


@pytest.fixture
def pickle_file(tmp_path, repository_data):
    """Write a RepositoryData pickle to a temp file and return the path."""
    pkl_path = tmp_path / "data.pkl.gz"
    with gzip.open(pkl_path, "wb") as f:
        pickle.dump(repository_data, f)
    return pkl_path


# ---------------------------------------------------------------------------
# Database fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """In-memory SQLite session for tests. Creates all tables fresh each test."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


# ---------------------------------------------------------------------------
# FastAPI TestClient fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def test_client(repository_data, db_session):
    """Return a TestClient with app state pre-loaded and DB dependency overridden."""
    from fastapi.testclient import TestClient

    from app.main import app

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=False) as client:
        app.state.repo_data = repository_data
        yield client
    app.dependency_overrides.pop(get_db, None)

"""Shared pytest fixtures for the BERIL Observatory UI test suite."""

import gzip
import json
import pickle
import tempfile
from datetime import datetime
from pathlib import Path

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
        total_notebooks=2,
        total_visualizations=3,
        total_data_files=1,
        last_updated=datetime(2024, 6, 15),
    )


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
# FastAPI TestClient fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def test_client(repository_data):
    """Return a TestClient with app state pre-loaded."""
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app, raise_server_exceptions=False) as client:
        # Inject repository data directly into app state
        app.state.repo_data = repository_data
        yield client

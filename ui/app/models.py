"""Data models for the BERIL Research Observatory."""

import re
from datetime import datetime
from enum import Enum
from typing import Any

from dataclasses import dataclass, field


def _slugify_name(name: str) -> str:
    """Slugify a contributor name for use as an ID."""
    text = name.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text


@dataclass
class Contributor:
    """A project contributor with optional ORCID and affiliation."""

    name: str
    affiliation: str | None = None
    orcid: str | None = None
    roles: list[str] = field(default_factory=list)
    project_ids: list[str] = field(default_factory=list)

    @property
    def id(self) -> str:
        """Slugified name for use as an identifier."""
        return _slugify_name(self.name)

    @property
    def orcid_url(self) -> str | None:
        """Full ORCID URL."""
        if self.orcid:
            return f"https://orcid.org/{self.orcid}"
        return None


class ReviewStatus(str, Enum):
    """Review status values."""

    REVIEWED = "Reviewed"
    NEEDS_RE_REVIEW = "Needs Re-review"
    NOT_REVIEWED = "Not Reviewed"


class ProjectStatus(str, Enum):
    """Project status values."""

    COMPLETED = "Completed"
    IN_PROGRESS = "In Progress"
    PROPOSED = "Proposed"


class IdeaStatus(str, Enum):
    """Research idea status values."""

    PROPOSED = "PROPOSED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class Priority(str, Enum):
    """Priority levels."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class CollectionCategory(str, Enum):
    """Collection category types."""

    PRIMARY = "primary"
    DOMAIN = "domain"
    REFERENCE = "reference"


@dataclass
class SampleQuery:
    """A sample SQL query for a collection."""

    title: str
    query: str


@dataclass
class CollectionTable:
    """A table within a collection."""

    name: str
    description: str
    row_count: int | None = None


@dataclass
class Collection:
    """A BERDL data collection."""

    id: str
    name: str
    category: CollectionCategory
    icon: str
    description: str
    philosophy: str = ""
    data_sources: list[str] = field(default_factory=list)
    scale_stats: dict[str, Any] = field(default_factory=dict)
    key_tables: list[CollectionTable] = field(default_factory=list)
    sample_queries: list[SampleQuery] = field(default_factory=list)
    related_collections: list[str] = field(default_factory=list)
    sub_collections: list[str] = field(default_factory=list)


@dataclass
class Review:
    """An automated review of a project."""

    reviewer: str
    date: datetime | None = None
    project_id: str = ""
    summary: str | None = None
    methodology: str | None = None
    code_quality: str | None = None
    findings_assessment: str | None = None
    suggestions: str | None = None
    raw_content: str = ""


@dataclass
class Notebook:
    """A Jupyter notebook in a project."""

    filename: str
    path: str
    title: str | None = None
    description: str | None = None


@dataclass
class Visualization:
    """A visualization image from a project."""

    filename: str
    path: str
    title: str | None = None
    description: str | None = None
    size_bytes: int = 0


@dataclass
class DataFile:
    """A data file (CSV, etc.) from a project."""

    filename: str
    path: str
    description: str | None = None
    size_bytes: int = 0
    row_count: int | None = None


@dataclass
class Project:
    """A research project."""

    id: str
    title: str
    research_question: str
    status: ProjectStatus = ProjectStatus.IN_PROGRESS
    hypothesis: str | None = None
    approach: str | None = None
    findings: str | None = None
    notebooks: list[Notebook] = field(default_factory=list)
    visualizations: list[Visualization] = field(default_factory=list)
    data_files: list[DataFile] = field(default_factory=list)
    created_date: datetime | None = None
    updated_date: datetime | None = None
    contributors: list[Contributor] = field(default_factory=list)
    related_discoveries: list[str] = field(default_factory=list)
    related_ideas: list[str] = field(default_factory=list)
    related_collections: list[str] = field(default_factory=list)
    raw_readme: str = ""
    review: Review | None = None
    # Three-file structure fields
    has_research_plan: bool = False
    has_report: bool = False
    research_plan_raw: str | None = None
    report_raw: str | None = None
    overview: str | None = None
    results: str | None = None
    interpretation: str | None = None
    limitations: str | None = None
    future_directions: str | None = None
    revision_history: str | None = None

    @property
    def review_status(self) -> ReviewStatus:
        """Determine review status based on review existence and staleness.

        Compares at date granularity (not datetime) because the review
        frontmatter only records YYYY-MM-DD, while updated_date comes from
        filesystem mtime with full timestamp precision. Without this, any
        project modified on the same day as its review shows "Needs Re-review".
        """
        if self.review is None:
            return ReviewStatus.NOT_REVIEWED
        if self.review.date and self.updated_date:
            # Normalize both to date objects for same-day comparison
            r_date = (
                self.review.date.date()
                if isinstance(self.review.date, datetime)
                else self.review.date
            )
            u_date = (
                self.updated_date.date()
                if isinstance(self.updated_date, datetime)
                else self.updated_date
            )
            if u_date > r_date:
                return ReviewStatus.NEEDS_RE_REVIEW
        return ReviewStatus.REVIEWED


@dataclass
class Discovery:
    """A research discovery from docs/discoveries.md."""

    id: str
    title: str
    content: str  # Markdown content
    project_tag: str  # e.g., "cog_analysis"
    date: datetime | None = None
    statistics: dict[str, Any] = field(default_factory=dict)
    related_projects: list[str] = field(default_factory=list)


@dataclass
class Column:
    """A database table column."""

    name: str
    data_type: str
    description: str | None = None
    is_primary_key: bool = False
    is_foreign_key: bool = False
    foreign_key_table: str | None = None


@dataclass
class Table:
    """A database table from docs/schema.md."""

    name: str
    description: str
    row_count: int = 0
    columns: list[Column] = field(default_factory=list)
    known_limitations: list[str] = field(default_factory=list)
    sample_queries: list[str] = field(default_factory=list)
    foreign_keys: list[tuple[str, str]] = field(
        default_factory=list
    )  # (column, target_table)


@dataclass
class Pitfall:
    """A pitfall or gotcha from docs/pitfalls.md."""

    id: str
    title: str
    category: str
    problem: str
    solution: str
    project_tag: str | None = None
    code_example: str | None = None


@dataclass
class PerformanceTip:
    """A performance tip from docs/performance.md."""

    id: str
    title: str
    description: str
    table_name: str | None = None
    code_example: str | None = None


@dataclass
class ResearchIdea:
    """A research idea from docs/research_ideas.md."""

    id: str
    title: str
    research_question: str
    status: IdeaStatus = IdeaStatus.PROPOSED
    priority: Priority = Priority.MEDIUM
    hypothesis: str | None = None
    approach: str | None = None
    effort: str | None = None  # e.g., "Low (1 week)"
    impact: str | None = None  # e.g., "High"
    dependencies: list[str] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)
    cross_project_tags: list[str] = field(default_factory=list)


@dataclass
class RepositoryData:
    """All parsed data from the repository."""

    projects: list[Project] = field(default_factory=list)
    discoveries: list[Discovery] = field(default_factory=list)
    tables: dict[str, list[Table]] = field(default_factory=dict)
    pitfalls: list[Pitfall] = field(default_factory=list)
    performance_tips: list[PerformanceTip] = field(default_factory=list)
    research_ideas: list[ResearchIdea] = field(default_factory=list)
    collections: list[Collection] = field(default_factory=list)
    contributors: list[Contributor] = field(default_factory=list)

    # Computed stats
    total_notebooks: int = 0
    total_visualizations: int = 0
    total_data_files: int = 0
    last_updated: datetime | None = None

    def get_tables_for_collection(self, collection_id: str) -> list[Table]:
        """Get schema tables for a collection by ID, checking sub_collections."""
        if collection_id in self.tables:
            return self.tables[collection_id]
        # Check if any sub_collection has tables
        collection = self.get_collection(collection_id)
        if collection:
            for sub_id in collection.sub_collections:
                if sub_id in self.tables:
                    return self.tables[sub_id]
        return []

    def get_collection(self, collection_id: str) -> Collection | None:
        """Get a collection by ID."""
        return next((c for c in self.collections if c.id == collection_id), None)

    def get_collections_by_category(
        self, category: CollectionCategory
    ) -> list[Collection]:
        """Get all collections in a category."""
        return [c for c in self.collections if c.category == category]

    def get_contributor(self, contributor_id: str) -> Contributor | None:
        """Get a contributor by ID."""
        return next((c for c in self.contributors if c.id == contributor_id), None)

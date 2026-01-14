"""Data models for the Pangenome Research Observatory."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


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
    contributors: list[str] = field(default_factory=list)
    related_discoveries: list[str] = field(default_factory=list)
    related_ideas: list[str] = field(default_factory=list)
    raw_readme: str = ""


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
    foreign_keys: list[tuple[str, str]] = field(default_factory=list)  # (column, target_table)


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
    tables: list[Table] = field(default_factory=list)
    pitfalls: list[Pitfall] = field(default_factory=list)
    performance_tips: list[PerformanceTip] = field(default_factory=list)
    research_ideas: list[ResearchIdea] = field(default_factory=list)

    # Computed stats
    total_notebooks: int = 0
    total_visualizations: int = 0
    total_data_files: int = 0
    last_updated: datetime | None = None

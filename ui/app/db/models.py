"""SQLAlchemy ORM models for BERIL Observatory."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_uuid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class BerilUser(Base):
    """A BERIL Observatory user, identified by ORCiD."""

    __tablename__ = "beril_user"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    orcid_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    display_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    affiliation: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    last_login_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    projects: Mapped[list["UserProject"]] = relationship(
        "UserProject", back_populates="owner", cascade="all, delete-orphan"
    )
    api_tokens: Mapped[list["UserApiToken"]] = relationship(
        "UserApiToken", back_populates="user", cascade="all, delete-orphan"
    )


class UserProject(Base):
    """A research project owned by a BERIL user."""

    __tablename__ = "user_project"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    owner_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("beril_user.id", ondelete="CASCADE"), nullable=False, index=True
    )
    slug: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    research_question: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("proposed", "in_progress", "completed", name="project_status"),
        default="proposed",
        nullable=False,
    )
    hypothesis: Mapped[str | None] = mapped_column(Text, nullable=True)
    approach: Mapped[str | None] = mapped_column(Text, nullable=True)
    findings: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    github_repo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    github_branch: Mapped[str | None] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    owner: Mapped["BerilUser"] = relationship("BerilUser", back_populates="projects")
    contributors: Mapped[list["ProjectContributor"]] = relationship(
        "ProjectContributor", back_populates="project", cascade="all, delete-orphan"
    )
    files: Mapped[list["ProjectFile"]] = relationship(
        "ProjectFile", back_populates="project", cascade="all, delete-orphan"
    )
    reviews: Mapped[list["ProjectReview"]] = relationship(
        "ProjectReview", back_populates="project", cascade="all, delete-orphan"
    )
    related_collections: Mapped[list["ProjectCollection"]] = relationship(
        "ProjectCollection", back_populates="project", cascade="all, delete-orphan"
    )

    @property
    def filesystem_path_parts(self) -> tuple[str, str]:
        """Returns (owner_id, slug) for constructing the filesystem path."""
        return (self.owner_id, self.slug)


class ProjectContributor(Base):
    """A contributor credited on a user project (may or may not be a registered user)."""

    __tablename__ = "project_contributor"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user_project.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Nullable: allows crediting contributors who haven't registered
    user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("beril_user.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    orcid_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    role: Mapped[str] = mapped_column(String(64), default="Author", nullable=False)

    project: Mapped["UserProject"] = relationship("UserProject", back_populates="contributors")


class ProjectFile(Base):
    """A file artifact belonging to a user project, stored on the filesystem."""

    __tablename__ = "project_file"
    __table_args__ = (
        # Prevents duplicate rows when two uploads for the same file race
        UniqueConstraint("project_id", "filename", "source", name="uq_project_file_name_source"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user_project.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_type: Mapped[str] = mapped_column(
        Enum(
            "notebook", "data", "visualization", "readme",
            "research_plan", "report", "other",
            name="file_type",
        ),
        nullable=False,
    )
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    # Path relative to user_projects_root
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    size_bytes: Mapped[int] = mapped_column(default=0)
    content_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # "upload" for manually uploaded files, "github" for files synced from a repo
    source: Mapped[str] = mapped_column(
        Enum("upload", "github", name="file_source"),
        default="upload",
        nullable=False,
    )
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    project: Mapped["UserProject"] = relationship("UserProject", back_populates="files")


class ProjectReview(Base):
    """An automated review run against a user project. Append-only."""

    __tablename__ = "project_review"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user_project.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reviewer: Mapped[str] = mapped_column(Text, nullable=False)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    methodology: Mapped[str | None] = mapped_column(Text, nullable=True)
    code_quality: Mapped[str | None] = mapped_column(Text, nullable=True)
    findings_assessment: Mapped[str | None] = mapped_column(Text, nullable=True)
    suggestions: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_content: Mapped[str] = mapped_column(Text, default="")

    project: Mapped["UserProject"] = relationship("UserProject", back_populates="reviews")


class UserApiToken(Base):
    """A personal API token for a BERIL user. Only the hash is stored."""

    __tablename__ = "user_api_token"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("beril_user.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    token_hash: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["BerilUser"] = relationship("BerilUser", back_populates="api_tokens")


class ProjectCollection(Base):
    """Join table: BERDL collections referenced by a user project."""

    __tablename__ = "project_collection"

    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user_project.id", ondelete="CASCADE"), primary_key=True
    )
    collection_id: Mapped[str] = mapped_column(String(128), primary_key=True)

    project: Mapped["UserProject"] = relationship("UserProject", back_populates="related_collections")

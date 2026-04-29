"""SQLAlchemy ORM models for BERIL Observatory."""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, JSON, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# JSONB on Postgres, JSON fallback elsewhere (used by SQLite-backed tests).
JSONCol = JSON().with_variant(JSONB(), "postgresql")


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
    roles: Mapped[list["UserRole"]] = relationship(
        "UserRole", back_populates="user", cascade="all, delete-orphan"
    )
    chat_sessions: Mapped[list["ChatSession"]] = relationship(
        "ChatSession", back_populates="owner", cascade="all, delete-orphan"
    )


class UserRole(Base):
    """System-level role granted to a user (e.g. admin)."""

    __tablename__ = "user_role"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("beril_user.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[str] = mapped_column(
        Enum("admin", "user", name="role_type"),
        primary_key=True,
    )
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    user: Mapped["BerilUser"] = relationship("BerilUser", back_populates="roles")


class UserProject(Base):
    """A research project owned by a BERIL user."""

    __tablename__ = "user_project"
    __table_args__ = (
        UniqueConstraint("owner_id", "slug", name="uq_user_project_owner_slug"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    owner_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("beril_user.id", ondelete="CASCADE"), nullable=False, index=True
    )
    slug: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    research_question: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum("proposed", "in_progress", "completed", name="project_status"),
        default="proposed",
        nullable=False,
    )
    hypothesis: Mapped[str | None] = mapped_column(Text, nullable=True)
    approach: Mapped[str | None] = mapped_column(Text, nullable=True)
    findings: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Rich parsed content fields
    overview: Mapped[str | None] = mapped_column(Text, nullable=True)
    results: Mapped[str | None] = mapped_column(Text, nullable=True)
    interpretation: Mapped[str | None] = mapped_column(Text, nullable=True)
    limitations: Mapped[str | None] = mapped_column(Text, nullable=True)
    future_directions: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_section: Mapped[str | None] = mapped_column(Text, nullable=True)
    references_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    revision_history: Mapped[str | None] = mapped_column(Text, nullable=True)
    other_sections: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    # Raw source files
    raw_readme: Mapped[str | None] = mapped_column(Text, nullable=True)
    research_plan_raw: Mapped[str | None] = mapped_column(Text, nullable=True)
    report_raw: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Origin tracking
    origin: Mapped[str] = mapped_column(
        Enum("user", "repo", "github", name="project_origin"),
        default="user",
        nullable=False,
    )
    repo_path: Mapped[str | None] = mapped_column(Text, nullable=True)  # e.g. "projects/slug"
    # Visibility and external links
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
    import_record: Mapped["ProjectImportRecord | None"] = relationship(
        "ProjectImportRecord", back_populates="project", uselist=False
    )
    chat_sessions: Mapped[list["ChatSession"]] = relationship(
        "ChatSession", back_populates="project"
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
        Enum("upload", "github", "repo_import", name="file_source"),
        default="upload",
        nullable=False,
    )
    # Tracks the source file's modification time (separate from the DB record's updated_at)
    last_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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


class ProjectImportRecord(Base):
    """Tracks migration state for each repo project directory."""

    __tablename__ = "project_import_record"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    repo_path: Mapped[str] = mapped_column(Text, unique=True, nullable=False, index=True)
    project_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("user_project.id", ondelete="SET NULL"), nullable=True
    )
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(
        Enum("pending", "imported", "failed", "stale", name="import_status"),
        default="pending",
        nullable=False,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    project: Mapped["UserProject | None"] = relationship(
        "UserProject", back_populates="import_record"
    )


class ChatSession(Base):
    """A persistent LLM chat session owned by a BERIL user.

    ``provider_id`` is a free-form string matched against the chat provider
    registry at request time (not an enum). Adding a new provider is a config +
    code change, not a migration.

    ``sdk_session_id`` is null until the first turn completes; subsequent turns
    pass it as the resume handle so the underlying agent rehydrates context.
    """

    __tablename__ = "chat_session"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    owner_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("beril_user.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sdk_session_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider_id: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False, default="New chat")
    project_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("user_project.id", ondelete="SET NULL"), nullable=True
    )
    archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    last_active_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    owner: Mapped["BerilUser"] = relationship("BerilUser", back_populates="chat_sessions")
    project: Mapped["UserProject | None"] = relationship(
        "UserProject", back_populates="chat_sessions"
    )
    messages: Mapped[list["ChatMessage"]] = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )


class ChatMessage(Base):
    """One finalized message in a chat session.

    ``content`` stores structured payloads (text, tool-call dicts, tool-result
    dicts) as JSON so we preserve the full turn structure on replay.
    """

    __tablename__ = "chat_message"
    __table_args__ = (
        Index("ix_chat_message_session_created", "session_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("chat_session.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(
        Enum("user", "assistant", "tool", "tool_result", name="chat_message_role"),
        nullable=False,
    )
    content: Mapped[Any] = mapped_column(JSONCol, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    session: Mapped["ChatSession"] = relationship("ChatSession", back_populates="messages")

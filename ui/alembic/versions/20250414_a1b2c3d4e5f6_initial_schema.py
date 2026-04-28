"""Initial schema — encodes the database as it existed before Alembic was introduced.

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2025-04-14
"""

from alembic import op
import sqlalchemy as sa

revision = "a1b2c3d4e5f6"
down_revision = None
branch_labels = None
depends_on = None


def _table_exists(name: str) -> bool:
    """Check whether a table already exists in the current database."""
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT EXISTS ("
            "  SELECT 1 FROM information_schema.tables"
            "  WHERE table_name = :name"
            ")"
        ),
        {"name": name},
    )
    return result.scalar()


def upgrade() -> None:
    # If the schema already exists (created by the old create_all before Alembic
    # was introduced), skip creation and just let Alembic stamp the revision.
    if _table_exists("beril_user"):
        return

    # beril_user
    op.create_table(
        "beril_user",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("orcid_id", sa.String(64), nullable=False, unique=True),
        sa.Column("display_name", sa.Text, nullable=True),
        sa.Column("affiliation", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_beril_user_orcid_id", "beril_user", ["orcid_id"])

    # user_project
    op.create_table(
        "user_project",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("owner_id", sa.String(36), sa.ForeignKey("beril_user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("slug", sa.String(128), nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("research_question", sa.Text, nullable=True),
        sa.Column("status", sa.Enum("proposed", "in_progress", "completed", name="project_status"), nullable=False, server_default="proposed"),
        sa.Column("hypothesis", sa.Text, nullable=True),
        sa.Column("approach", sa.Text, nullable=True),
        sa.Column("findings", sa.Text, nullable=True),
        sa.Column("is_public", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("github_repo_url", sa.Text, nullable=True),
        sa.Column("github_branch", sa.String(256), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_user_project_owner_id", "user_project", ["owner_id"])

    # project_contributor
    op.create_table(
        "project_contributor",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("user_project.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("beril_user.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("orcid_id", sa.String(64), nullable=True),
        sa.Column("role", sa.String(64), nullable=False, server_default="Author"),
    )
    op.create_index("ix_project_contributor_project_id", "project_contributor", ["project_id"])

    # project_file
    op.create_table(
        "project_file",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("user_project.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_type", sa.Enum("notebook", "data", "visualization", "readme", "research_plan", "report", "other", name="file_type"), nullable=False),
        sa.Column("filename", sa.Text, nullable=False),
        sa.Column("storage_path", sa.Text, nullable=False),
        sa.Column("size_bytes", sa.Integer, nullable=False, server_default="0"),
        sa.Column("content_type", sa.String(128), nullable=True),
        sa.Column("title", sa.Text, nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("is_public", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("source", sa.Enum("upload", "github", name="file_source"), nullable=False, server_default="upload"),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("project_id", "filename", "source", name="uq_project_file_name_source"),
    )
    op.create_index("ix_project_file_project_id", "project_file", ["project_id"])

    # project_review
    op.create_table(
        "project_review",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("user_project.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reviewer", sa.Text, nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("methodology", sa.Text, nullable=True),
        sa.Column("code_quality", sa.Text, nullable=True),
        sa.Column("findings_assessment", sa.Text, nullable=True),
        sa.Column("suggestions", sa.Text, nullable=True),
        sa.Column("raw_content", sa.Text, nullable=False, server_default=""),
    )
    op.create_index("ix_project_review_project_id", "project_review", ["project_id"])

    # user_api_token
    op.create_table(
        "user_api_token",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("beril_user.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("token_hash", sa.Text, nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
    )

    # project_collection
    op.create_table(
        "project_collection",
        sa.Column("project_id", sa.String(36), sa.ForeignKey("user_project.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("collection_id", sa.String(128), primary_key=True),
    )


def downgrade() -> None:
    op.drop_table("project_collection")
    op.drop_table("user_api_token")
    op.drop_table("project_review")
    op.drop_table("project_file")
    op.drop_table("project_contributor")
    op.drop_table("user_project")
    op.drop_table("beril_user")
    # Drop enums explicitly (PostgreSQL keeps them after table drop)
    op.execute("DROP TYPE IF EXISTS project_status")
    op.execute("DROP TYPE IF EXISTS file_type")
    op.execute("DROP TYPE IF EXISTS file_source")

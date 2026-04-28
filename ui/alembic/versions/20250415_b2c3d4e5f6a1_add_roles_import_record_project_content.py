"""Add UserRole, ProjectImportRecord, rich content fields on UserProject, last_updated_at on ProjectFile.

Revision ID: b2c3d4e5f6a1
Revises: a1b2c3d4e5f6
Create Date: 2025-04-15
"""

from alembic import op
import sqlalchemy as sa

revision = "b2c3d4e5f6a1"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def _table_exists(name: str) -> bool:
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


def _column_exists(table: str, column: str) -> bool:
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT EXISTS ("
            "  SELECT 1 FROM information_schema.columns"
            "  WHERE table_name = :table AND column_name = :column"
            ")"
        ),
        {"table": table, "column": column},
    )
    return result.scalar()


def upgrade() -> None:
    # --- user_role table ---
    if not _table_exists("user_role"):
        op.create_table(
            "user_role",
            sa.Column("user_id", sa.String(36), sa.ForeignKey("beril_user.id", ondelete="CASCADE"), primary_key=True),
            sa.Column("role", sa.Enum("admin", "user", name="role_type"), primary_key=True),
            sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False),
        )

    # --- project_import_record table ---
    if not _table_exists("project_import_record"):
        op.create_table(
            "project_import_record",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("repo_path", sa.Text, nullable=False, unique=True),
            sa.Column("project_id", sa.String(36), sa.ForeignKey("user_project.id", ondelete="SET NULL"), nullable=True),
            sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status", sa.Enum("pending", "imported", "failed", "stale", name="import_status"), nullable=False, server_default="pending"),
            sa.Column("error_message", sa.Text, nullable=True),
        )
        op.create_index("ix_project_import_record_repo_path", "project_import_record", ["repo_path"])

    # --- New columns on user_project ---
    for col in (
        "overview",
        "results",
        "interpretation",
        "limitations",
        "future_directions",
        "data_section",
        "references_text",
        "revision_history",
        "other_sections",
        "raw_readme",
        "research_plan_raw",
        "report_raw",
        "repo_path",
    ):
        if not _column_exists("user_project", col):
            op.add_column("user_project", sa.Column(col, sa.Text, nullable=True))

    # github_branch was added to the model after the pre-Alembic schema was
    # frozen, so legacy databases (where the initial migration short-circuits)
    # never received it. The ORM selects it on every UserProject query.
    if not _column_exists("user_project", "github_branch"):
        op.add_column(
            "user_project",
            sa.Column("github_branch", sa.String(256), nullable=True),
        )

    if not _column_exists("user_project", "origin"):
        # The enum type must exist before it can be referenced in ADD COLUMN.
        # create_table auto-creates enums, but add_column does not.
        op.execute("""
            DO $$ BEGIN
                CREATE TYPE project_origin AS ENUM ('user', 'repo', 'github');
            EXCEPTION
                WHEN duplicate_object THEN NULL;
            END $$
        """)
        op.add_column(
            "user_project",
            sa.Column(
                "origin",
                sa.Enum("user", "repo", "github", name="project_origin", create_type=False),
                nullable=False,
                server_default="user",
            ),
        )

    # --- New column on project_file ---
    if not _column_exists("project_file", "last_updated_at"):
        op.add_column(
            "project_file",
            sa.Column("last_updated_at", sa.DateTime(timezone=True), nullable=True),
        )

    # `source` predates Alembic in the model, but databases created via the
    # very first create_all (before `source` was added to ProjectFile) won't
    # have the column or the enum type. Create both conditionally before
    # extending the enum below.
    if not _column_exists("project_file", "source"):
        op.execute("""
            DO $$ BEGIN
                CREATE TYPE file_source AS ENUM ('upload', 'github');
            EXCEPTION
                WHEN duplicate_object THEN NULL;
            END $$
        """)
        op.add_column(
            "project_file",
            sa.Column(
                "source",
                sa.Enum("upload", "github", name="file_source", create_type=False),
                nullable=False,
                server_default="upload",
            ),
        )

    # --- Add repo_import to the file_source enum ---
    # IF NOT EXISTS is safe to run repeatedly.
    op.execute("ALTER TYPE file_source ADD VALUE IF NOT EXISTS 'repo_import'")

    # --- Unique (owner_id, slug) on user_project ---
    # Storage paths are keyed by {owner_id}/{slug}, so duplicates would let
    # two projects share files. Resolve any pre-existing collisions by
    # suffixing later rows, then enforce uniqueness.
    conn = op.get_bind()
    constraint_exists = conn.execute(
        sa.text(
            "SELECT EXISTS ("
            "  SELECT 1 FROM pg_constraint"
            "  WHERE conname = 'uq_user_project_owner_slug'"
            ")"
        )
    ).scalar()
    if not constraint_exists:
        # For each (owner_id, slug) duplicate, leave the earliest row alone
        # and rewrite the others' slug with a short random suffix.
        op.execute("""
            WITH dups AS (
                SELECT id,
                       slug,
                       ROW_NUMBER() OVER (
                           PARTITION BY owner_id, slug ORDER BY created_at, id
                       ) AS rn
                FROM user_project
            )
            UPDATE user_project up
            SET slug = dups.slug || '-' || substr(md5(up.id), 1, 6)
            FROM dups
            WHERE up.id = dups.id AND dups.rn > 1
        """)
        op.create_unique_constraint(
            "uq_user_project_owner_slug",
            "user_project",
            ["owner_id", "slug"],
        )


def downgrade() -> None:
    # Remove repo_import from file_source enum is not directly supported in PG;
    # leave the enum value in place — it's harmless if unused.
    op.drop_constraint("uq_user_project_owner_slug", "user_project", type_="unique")
    op.drop_column("project_file", "last_updated_at")

    op.drop_column("user_project", "origin")
    for col in (
        "repo_path",
        "report_raw",
        "research_plan_raw",
        "raw_readme",
        "other_sections",
        "revision_history",
        "references_text",
        "data_section",
        "future_directions",
        "limitations",
        "interpretation",
        "results",
        "overview",
    ):
        op.drop_column("user_project", col)
    # github_branch is only added by upgrade() on legacy DBs; leaving it in
    # place on downgrade is safe since the initial schema also defines it.

    op.drop_index("ix_project_import_record_repo_path", table_name="project_import_record")
    op.drop_table("project_import_record")
    op.drop_table("user_role")

    op.execute("DROP TYPE IF EXISTS import_status")
    op.execute("DROP TYPE IF EXISTS project_origin")
    op.execute("DROP TYPE IF EXISTS role_type")

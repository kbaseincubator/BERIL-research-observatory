"""Add chat_session and chat_message tables.

Revision ID: c3d4e5f6a1b2
Revises: b2c3d4e5f6a1
Create Date: 2026-04-21
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "c3d4e5f6a1b2"
down_revision = "b2c3d4e5f6a1"
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


def upgrade() -> None:
    if not _table_exists("chat_session"):
        op.create_table(
            "chat_session",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column(
                "owner_id",
                sa.String(36),
                sa.ForeignKey("beril_user.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("sdk_session_id", sa.Text, nullable=True),
            sa.Column("provider_id", sa.String(64), nullable=False),
            sa.Column("model", sa.String(128), nullable=False),
            sa.Column("title", sa.Text, nullable=False, server_default="New chat"),
            sa.Column(
                "project_id",
                sa.String(36),
                sa.ForeignKey("user_project.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("archived", sa.Boolean, nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_chat_session_owner_id", "chat_session", ["owner_id"])

    if not _table_exists("chat_message"):
        op.create_table(
            "chat_message",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column(
                "session_id",
                sa.String(36),
                sa.ForeignKey("chat_session.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "role",
                sa.Enum("user", "assistant", "tool", "tool_result", name="chat_message_role"),
                nullable=False,
            ),
            sa.Column("content", postgresql.JSONB, nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index(
            "ix_chat_message_session_created",
            "chat_message",
            ["session_id", "created_at"],
        )


def downgrade() -> None:
    op.drop_index("ix_chat_message_session_created", table_name="chat_message")
    op.drop_table("chat_message")
    op.drop_index("ix_chat_session_owner_id", table_name="chat_session")
    op.drop_table("chat_session")
    op.execute("DROP TYPE IF EXISTS chat_message_role")

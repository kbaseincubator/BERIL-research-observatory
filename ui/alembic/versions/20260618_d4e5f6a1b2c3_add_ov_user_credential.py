"""Add ov_user_credential table.

Stores each BERIL user's OpenViking credential (the API key) encrypted at rest,
one-to-one with beril_user.

Revision ID: d4e5f6a1b2c3
Revises: c3d4e5f6a1b2
Create Date: 2026-06-18
"""

from alembic import op
import sqlalchemy as sa

revision = "d4e5f6a1b2c3"
down_revision = "c3d4e5f6a1b2"
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
    if not _table_exists("ov_user_credential"):
        op.create_table(
            "ov_user_credential",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column(
                "user_id",
                sa.String(36),
                sa.ForeignKey("beril_user.id", ondelete="CASCADE"),
                nullable=False,
                unique=True,
            ),
            sa.Column("account_id", sa.String(128), nullable=False),
            sa.Column("ov_user_id", sa.String(128), nullable=False),
            sa.Column("encrypted_key", sa.Text, nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )


def downgrade() -> None:
    op.drop_table("ov_user_credential")

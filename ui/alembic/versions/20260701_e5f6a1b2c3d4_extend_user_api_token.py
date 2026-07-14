"""Extend user_api_token: multi-token per user, add name/expires_at/revoked_at.

The initial-schema migration declared ``user_id`` UNIQUE, enforcing one token
per user with rotation-on-create. The new PAT flow needs multiple named,
expiring, revocable tokens per user, so we drop that unique constraint and
add columns for name, expiry, and revocation. All new columns are nullable
so pre-existing rows remain valid: NULL means "unnamed, never expires, not
revoked."

Revision ID: e5f6a1b2c3d4
Revises: d4e5f6a1b2c3
Create Date: 2026-07-01
"""

from alembic import op
import sqlalchemy as sa

revision = "e5f6a1b2c3d4"
down_revision = "d4e5f6a1b2c3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the auto-named UNIQUE constraint on user_id. PostgreSQL default
    # name for an inline column UNIQUE is "<table>_<column>_key".
    op.execute("ALTER TABLE user_api_token DROP CONSTRAINT IF EXISTS user_api_token_user_id_key")

    # Replace with a plain index so lookups by user_id stay fast.
    op.create_index(
        "ix_user_api_token_user_id",
        "user_api_token",
        ["user_id"],
    )

    op.add_column("user_api_token", sa.Column("name", sa.String(128), nullable=True))
    op.add_column("user_api_token", sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("user_api_token", sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("user_api_token", "revoked_at")
    op.drop_column("user_api_token", "expires_at")
    op.drop_column("user_api_token", "name")
    op.drop_index("ix_user_api_token_user_id", table_name="user_api_token")
    # Restore the UNIQUE constraint. Only safe if no user currently owns
    # more than one token — otherwise this migration will fail, which is
    # the correct behavior.
    op.create_unique_constraint(
        "user_api_token_user_id_key", "user_api_token", ["user_id"]
    )

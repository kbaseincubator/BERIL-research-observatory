"""Database CRUD operations for BERIL Observatory."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import BerilUser


async def get_user_by_orcid(db: AsyncSession, orcid_id: str) -> BerilUser | None:
    """Look up a user by their ORCiD ID."""
    result = await db.execute(select(BerilUser).where(BerilUser.orcid_id == orcid_id))
    return result.scalar_one_or_none()


async def get_or_create_user(
    db: AsyncSession,
    orcid_id: str,
    display_name: str | None = None,
) -> tuple[BerilUser, bool]:
    """Get an existing user or create a new one on first login.

    Returns (user, created) where created is True if this is a new account.
    Updates last_login_at and display_name on every login.
    """
    user = await get_user_by_orcid(db, orcid_id)
    created = False

    if user is None:
        user = BerilUser(
            orcid_id=orcid_id,
            display_name=display_name,
        )
        db.add(user)
        created = True
    else:
        user.last_login_at = datetime.now(timezone.utc)
        if display_name and display_name != user.display_name:
            user.display_name = display_name

    await db.commit()
    await db.refresh(user)
    return user, created

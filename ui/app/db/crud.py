"""Database CRUD operations for BERIL Observatory."""

import hashlib
import secrets
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import BerilUser, ProjectFile, UserApiToken, UserProject


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


# ---------------------------------------------------------------------------
# UserProject
# ---------------------------------------------------------------------------


async def get_project_by_id(db: AsyncSession, project_id: str) -> UserProject | None:
    result = await db.execute(select(UserProject).where(UserProject.id == project_id))
    return result.scalar_one_or_none()


async def get_projects_for_user(db: AsyncSession, user_id: str) -> list[UserProject]:
    result = await db.execute(select(UserProject).where(UserProject.owner_id == user_id))
    return list(result.scalars().all())


async def update_project_github_url(
    db: AsyncSession, project_id: str, github_repo_url: str | None
) -> UserProject | None:
    project = await get_project_by_id(db, project_id)
    if project is None:
        return None
    project.github_repo_url = github_repo_url
    await db.commit()
    await db.refresh(project)
    return project


# ---------------------------------------------------------------------------
# ProjectFile
# ---------------------------------------------------------------------------


async def create_project_file(
    db: AsyncSession,
    *,
    project_id: str,
    file_type: str,
    filename: str,
    storage_path: str,
    size_bytes: int = 0,
    content_type: str | None = None,
    title: str | None = None,
    description: str | None = None,
    is_public: bool = False,
) -> ProjectFile:
    f = ProjectFile(
        project_id=project_id,
        file_type=file_type,
        filename=filename,
        storage_path=storage_path,
        size_bytes=size_bytes,
        content_type=content_type,
        title=title,
        description=description,
        is_public=is_public,
    )
    db.add(f)
    await db.commit()
    await db.refresh(f)
    return f


async def get_files_for_project(db: AsyncSession, project_id: str) -> list[ProjectFile]:
    result = await db.execute(
        select(ProjectFile).where(ProjectFile.project_id == project_id)
    )
    return list(result.scalars().all())


async def get_file_by_id(db: AsyncSession, file_id: str) -> ProjectFile | None:
    result = await db.execute(select(ProjectFile).where(ProjectFile.id == file_id))
    return result.scalar_one_or_none()


async def delete_project_file(db: AsyncSession, file_id: str) -> None:
    f = await get_file_by_id(db, file_id)
    if f is not None:
        await db.delete(f)
        await db.commit()


# ---------------------------------------------------------------------------
# UserApiToken
# ---------------------------------------------------------------------------


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


async def get_or_create_api_token(
    db: AsyncSession, user_id: str
) -> tuple[str, UserApiToken]:
    """Generate a new API token for the user, replacing any existing one.

    Returns (raw_token, record). The raw token is returned exactly once and
    never stored — only its SHA-256 hash is persisted.

    The delete and insert run in a single transaction. If a concurrent request
    wins the insert race, we retry once (the unique constraint on user_id
    guarantees at most one active token at all times).
    """
    for attempt in range(2):
        try:
            async with db.begin_nested():
                await db.execute(delete(UserApiToken).where(UserApiToken.user_id == user_id))
                raw_token = secrets.token_hex(32)
                record = UserApiToken(user_id=user_id, token_hash=_hash_token(raw_token))
                db.add(record)
            await db.commit()
            await db.refresh(record)
            return raw_token, record
        except IntegrityError:
            await db.rollback()
            if attempt == 1:
                raise


async def get_user_by_api_token(
    db: AsyncSession, raw_token: str
) -> BerilUser | None:
    """Look up the user owning the given raw API token.

    Updates last_used_at on the token record if found.
    """
    token_hash = _hash_token(raw_token)
    result = await db.execute(
        select(UserApiToken).where(UserApiToken.token_hash == token_hash)
    )
    record = result.scalar_one_or_none()
    if record is None:
        return None

    record.last_used_at = datetime.now(timezone.utc)
    await db.commit()

    user_result = await db.execute(
        select(BerilUser).where(BerilUser.id == record.user_id)
    )
    return user_result.scalar_one_or_none()

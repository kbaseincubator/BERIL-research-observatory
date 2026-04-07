"""Database engine and session management."""

import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import Base

logger = logging.getLogger(__name__)

# Module-level engine and session factory — initialized by init_db()
_engine = None
_async_session_factory = None
_db_url: str | None = None


async def init_db(db_url: str) -> None:
    """Create the async engine, session factory, and all tables."""
    global _engine, _async_session_factory, _db_url

    if _engine is not None:
        if db_url != _db_url:
            logger.warning(
                f"init_db called again with a different URL (ignoring). "
                f"Active: {_db_url!r}, requested: {db_url!r}"
            )
        else:
            logger.debug("init_db called again with same URL — already initialized, skipping")
        return

    _engine = create_async_engine(db_url, echo=False)
    _async_session_factory = async_sessionmaker(_engine, expire_on_commit=False)

    from sqlalchemy import text

    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Add columns introduced after the initial schema on already-initialized databases.
    # Run in a separate connection so a duplicate-column error on transactional-DDL
    # databases (PostgreSQL) does not abort the surrounding transaction.
    async with _engine.connect() as conn:
        await conn.execution_options(isolation_level="AUTOCOMMIT")
        try:
            await conn.execute(text(
                "ALTER TABLE user_project ADD COLUMN github_branch VARCHAR(256)"
            ))
        except Exception:
            pass  # Column already exists — safe to ignore

    async with _engine.begin() as conn:
        # Ensure the upload-upsert uniqueness constraint exists on already-initialized
        # databases (create_all only creates missing tables, not missing constraints).
        # Skip index creation if pre-existing duplicates would violate it; those
        # require manual deduplication rather than silent data loss at startup.
        result = await conn.execute(text(
            "SELECT COUNT(*) FROM ("
            "  SELECT project_id, filename, source FROM project_file"
            "  GROUP BY project_id, filename, source HAVING COUNT(*) > 1"
            ") dups"
        ))
        dup_count = result.scalar()
        if dup_count:
            logger.warning(
                "Skipping uq_project_file_name_source index: %d duplicate "
                "(project_id, filename, source) group(s) found in project_file. "
                "Deduplicate manually before this index can be applied.",
                dup_count,
            )
        else:
            await conn.execute(text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_project_file_name_source "
                "ON project_file (project_id, filename, source)"
            ))

    _db_url = db_url
    logger.info(f"Database initialized: {db_url}")


async def close_db() -> None:
    """Dispose of the engine on shutdown."""
    global _engine, _db_url
    if _engine:
        await _engine.dispose()
        _engine = None
        _db_url = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yields an async database session."""
    if _async_session_factory is None:
        raise RuntimeError("Database not initialized — call init_db() first")
    async with _async_session_factory() as session:
        yield session


async def check_db() -> dict:
    """Check DB connectivity and return basic status info."""
    if _engine is None:
        return {"status": "unavailable", "detail": "engine not initialized"}
    try:
        from sqlalchemy import text
        async with _engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        version = _engine.dialect.server_version_info
        return {"status": "ok", "version": version}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

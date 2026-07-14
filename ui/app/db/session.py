"""Database engine and session management."""

import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

logger = logging.getLogger(__name__)

# Module-level engine and session factory — initialized by init_db()
_engine = None
_async_session_factory = None
_db_url: str | None = None


async def init_db(db_url: str) -> None:
    """Create the async engine and session factory.

    Schema creation and migrations are handled by Alembic.
    Run ``uv run alembic upgrade head`` before starting the application.
    """
    global _engine, _async_session_factory, _db_url

    if _engine is not None:
        if db_url != _db_url:
            logger.warning(
                "init_db called again with a different URL (ignoring). "
                "Active: %r, requested: %r",
                _db_url,
                db_url,
            )
        else:
            logger.debug("init_db called again with same URL — already initialized, skipping")
        return

    _engine = create_async_engine(db_url, echo=False)
    _async_session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    _db_url = db_url
    logger.info("Database initialized: %s", db_url)


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

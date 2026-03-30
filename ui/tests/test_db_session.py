"""Tests for database session management (app.db.session)."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import session as db_session_module
from app.db.session import close_db, get_db, init_db

URL = "sqlite+aiosqlite:///:memory:"


class TestInitDb:
    async def test_creates_tables(self):
        """init_db should create all ORM tables without error."""
        await init_db(URL)
        await close_db()

    async def test_sets_module_globals(self):
        """init_db should populate the module-level engine, factory, and url."""
        db_session_module._engine = None
        db_session_module._async_session_factory = None
        db_session_module._db_url = None

        await init_db(URL)

        assert db_session_module._engine is not None
        assert db_session_module._async_session_factory is not None
        assert db_session_module._db_url == URL
        await close_db()

    async def test_same_url_reinit_is_noop(self):
        """Calling init_db twice with the same URL keeps the original engine."""
        await init_db(URL)
        engine_before = db_session_module._engine

        await init_db(URL)  # should early-return
        assert db_session_module._engine is engine_before
        await close_db()

    async def test_different_url_reinit_logs_warning_and_ignores(self, caplog):
        """Calling init_db with a different URL warns and keeps the original engine."""
        import logging

        await init_db(URL)
        engine_before = db_session_module._engine

        with caplog.at_level(logging.WARNING, logger="app.db.session"):
            await init_db("sqlite+aiosqlite:///other.db")

        assert db_session_module._engine is engine_before
        assert "different URL" in caplog.text
        await close_db()


class TestCloseDb:
    async def test_disposes_engine_and_clears_globals(self):
        await init_db(URL)
        assert db_session_module._engine is not None

        await close_db()
        assert db_session_module._engine is None
        assert db_session_module._db_url is None

    async def test_safe_to_call_when_not_initialized(self):
        """close_db should not raise if called before init_db."""
        db_session_module._engine = None
        await close_db()  # should not raise

    async def test_reinit_works_after_close(self):
        """After close_db, init_db should succeed again."""
        await init_db(URL)
        await close_db()
        await init_db(URL)
        assert db_session_module._engine is not None
        await close_db()


class TestGetDb:
    async def test_raises_when_not_initialized(self):
        """get_db should raise RuntimeError if called before init_db."""
        db_session_module._async_session_factory = None

        gen = get_db()
        with pytest.raises(RuntimeError, match="Database not initialized"):
            await gen.__anext__()

    async def test_yields_async_session(self):
        """get_db should yield an AsyncSession after init."""
        await init_db("sqlite+aiosqlite:///:memory:")

        gen = get_db()
        session = await gen.__anext__()
        assert isinstance(session, AsyncSession)

        # Clean up the generator
        try:
            await gen.aclose()
        except StopAsyncIteration:
            pass

        await close_db()

    async def test_session_is_usable(self):
        """Session from get_db should be able to execute a statement."""
        from sqlalchemy import text

        await init_db("sqlite+aiosqlite:///:memory:")

        gen = get_db()
        session = await gen.__anext__()
        result = await session.execute(text("SELECT 1"))
        assert result.scalar() == 1

        try:
            await gen.aclose()
        except StopAsyncIteration:
            pass

        await close_db()

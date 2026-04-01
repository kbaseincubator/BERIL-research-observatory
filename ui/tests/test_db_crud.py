"""Tests for database CRUD operations (app.db.crud)."""

from datetime import datetime, timezone

import pytest

from app.db.crud import get_or_create_user, get_user_by_orcid
from app.db.models import BerilUser


# ---------------------------------------------------------------------------
# get_user_by_orcid
# ---------------------------------------------------------------------------


class TestGetUserByOrcid:
    async def test_returns_none_when_not_found(self, db_session):
        result = await get_user_by_orcid(db_session, "0000-0000-0000-0000")
        assert result is None

    async def test_returns_user_when_found(self, db_session):
        user = BerilUser(orcid_id="0000-0001-2345-6789", display_name="Alice")
        db_session.add(user)
        await db_session.commit()

        result = await get_user_by_orcid(db_session, "0000-0001-2345-6789")
        assert result is not None
        assert result.orcid_id == "0000-0001-2345-6789"
        assert result.display_name == "Alice"

    async def test_lookup_is_exact_match(self, db_session):
        user = BerilUser(orcid_id="0000-0001-2345-6789")
        db_session.add(user)
        await db_session.commit()

        # Partial or different ID should not match
        assert await get_user_by_orcid(db_session, "0000-0001-2345-678") is None
        assert await get_user_by_orcid(db_session, "0000-0001-2345-6780") is None

    async def test_returns_correct_user_among_many(self, db_session):
        for i in range(5):
            db_session.add(BerilUser(orcid_id=f"0000-0001-0000-000{i}"))
        await db_session.commit()

        result = await get_user_by_orcid(db_session, "0000-0001-0000-0003")
        assert result is not None
        assert result.orcid_id == "0000-0001-0000-0003"


# ---------------------------------------------------------------------------
# get_or_create_user
# ---------------------------------------------------------------------------


class TestGetOrCreateUser:
    async def test_creates_new_user_on_first_login(self, db_session):
        user, created = await get_or_create_user(
            db_session, orcid_id="0000-0001-2345-6789", display_name="Alice"
        )
        assert created is True
        assert user.orcid_id == "0000-0001-2345-6789"
        assert user.display_name == "Alice"
        assert user.id is not None

    async def test_returns_existing_user_on_second_login(self, db_session):
        user1, created1 = await get_or_create_user(
            db_session, orcid_id="0000-0001-2345-6789", display_name="Alice"
        )
        user2, created2 = await get_or_create_user(
            db_session, orcid_id="0000-0001-2345-6789", display_name="Alice"
        )
        assert created1 is True
        assert created2 is False
        assert user1.id == user2.id

    async def test_updates_last_login_at_on_return(self, db_session):
        user, _ = await get_or_create_user(
            db_session, orcid_id="0000-0001-2345-6789"
        )
        original_login = user.last_login_at

        # Simulate a later login
        user2, created = await get_or_create_user(
            db_session, orcid_id="0000-0001-2345-6789"
        )
        assert created is False
        # last_login_at should be >= the original (may be equal if within same second)
        assert user2.last_login_at >= original_login

    async def test_updates_display_name_when_changed(self, db_session):
        await get_or_create_user(
            db_session, orcid_id="0000-0001-2345-6789", display_name="Alice Old"
        )
        user, created = await get_or_create_user(
            db_session, orcid_id="0000-0001-2345-6789", display_name="Alice New"
        )
        assert created is False
        assert user.display_name == "Alice New"

    async def test_does_not_overwrite_name_with_none(self, db_session):
        await get_or_create_user(
            db_session, orcid_id="0000-0001-2345-6789", display_name="Alice"
        )
        user, _ = await get_or_create_user(
            db_session, orcid_id="0000-0001-2345-6789", display_name=None
        )
        # Name should be preserved when None is passed
        assert user.display_name == "Alice"

    async def test_does_not_overwrite_name_with_empty_string(self, db_session):
        await get_or_create_user(
            db_session, orcid_id="0000-0001-2345-6789", display_name="Alice"
        )
        user, _ = await get_or_create_user(
            db_session, orcid_id="0000-0001-2345-6789", display_name=""
        )
        # Empty string is falsy, so name should not be overwritten
        assert user.display_name == "Alice"

    async def test_new_user_is_persisted(self, db_session):
        user, _ = await get_or_create_user(
            db_session, orcid_id="0000-0001-2345-6789", display_name="Alice"
        )
        # Verify it's actually in the DB
        fetched = await get_user_by_orcid(db_session, "0000-0001-2345-6789")
        assert fetched is not None
        assert fetched.id == user.id

    async def test_new_user_defaults(self, db_session):
        user, _ = await get_or_create_user(db_session, orcid_id="0000-0001-2345-6789")
        assert user.is_active is True
        assert user.affiliation is None
        assert user.created_at is not None
        assert user.last_login_at is not None

    async def test_multiple_distinct_users_created_independently(self, db_session):
        user_a, created_a = await get_or_create_user(db_session, orcid_id="0000-0001-0001-0001")
        user_b, created_b = await get_or_create_user(db_session, orcid_id="0000-0001-0002-0002")

        assert created_a is True
        assert created_b is True
        assert user_a.id != user_b.id

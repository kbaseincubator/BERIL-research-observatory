"""Tests for database CRUD operations (app.db.crud)."""

import secrets
import pytest

from app.db.crud import (
    _hash_token,
    create_project_file,
    delete_project_file,
    get_file_by_id,
    get_files_for_project,
    get_or_create_api_token,
    get_or_create_user,
    get_project_by_id,
    get_projects_for_user,
    get_user_by_api_token,
    get_user_by_orcid,
    update_project_github_url,
)
from app.db.models import BerilUser, UserApiToken, UserProject


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


# ---------------------------------------------------------------------------
# Shared fixture helpers
# ---------------------------------------------------------------------------


async def _make_user(db_session, orcid="0000-0001-2345-6789"):
    user = BerilUser(orcid_id=orcid)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def _make_project(db_session, user):
    project = UserProject(
        owner_id=user.id, slug="test-project", title="T", research_question="Q?"
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


# ---------------------------------------------------------------------------
# get_project_by_id / get_projects_for_user
# ---------------------------------------------------------------------------


class TestProjectQueries:
    async def test_get_project_by_id_found(self, db_session):
        user = await _make_user(db_session)
        project = await _make_project(db_session, user)

        result = await get_project_by_id(db_session, project.id)
        assert result is not None
        assert result.id == project.id

    async def test_get_project_by_id_not_found(self, db_session):
        result = await get_project_by_id(db_session, "nonexistent-id")
        assert result is None

    async def test_get_projects_for_user_returns_all(self, db_session):
        user = await _make_user(db_session)
        for i in range(3):
            project = UserProject(
                owner_id=user.id, slug=f"project-{i}", title="T", research_question="Q?"
            )
            db_session.add(project)
        await db_session.commit()

        results = await get_projects_for_user(db_session, user.id)
        assert len(results) == 3

    async def test_get_projects_for_user_empty(self, db_session):
        user = await _make_user(db_session)
        results = await get_projects_for_user(db_session, user.id)
        assert results == []

    async def test_get_projects_for_user_only_own(self, db_session):
        user_a = await _make_user(db_session, orcid="0000-0001-0001-0001")
        user_b = await _make_user(db_session, orcid="0000-0001-0002-0002")
        await _make_project(db_session, user_a)
        await _make_project(db_session, user_b)

        results = await get_projects_for_user(db_session, user_a.id)
        assert len(results) == 1
        assert results[0].owner_id == user_a.id


# ---------------------------------------------------------------------------
# update_project_github_url
# ---------------------------------------------------------------------------


class TestUpdateProjectGithubUrl:
    async def test_sets_github_url(self, db_session):
        user = await _make_user(db_session)
        project = await _make_project(db_session, user)

        result = await update_project_github_url(
            db_session, project.id, "https://github.com/org/repo"
        )
        assert result is not None
        assert result.github_repo_url == "https://github.com/org/repo"

    async def test_clears_github_url(self, db_session):
        user = await _make_user(db_session)
        project = await _make_project(db_session, user)
        await update_project_github_url(db_session, project.id, "https://github.com/org/repo")

        result = await update_project_github_url(db_session, project.id, None)
        assert result.github_repo_url is None

    async def test_returns_none_for_missing_project(self, db_session):
        result = await update_project_github_url(db_session, "no-such-id", "https://github.com/x/y")
        assert result is None


# ---------------------------------------------------------------------------
# create_project_file / get_file_by_id / get_files_for_project / delete_project_file
# ---------------------------------------------------------------------------


class TestProjectFileCrud:
    @pytest.fixture
    async def project(self, db_session):
        user = await _make_user(db_session)
        return await _make_project(db_session, user)

    async def test_create_file_minimal(self, db_session, project):
        f = await create_project_file(
            db_session,
            project_id=project.id,
            file_type="data",
            filename="data.csv",
            storage_path=f"{project.owner_id}/{project.slug}/data.csv",
        )
        assert f.id is not None
        assert f.filename == "data.csv"
        assert f.is_public is False
        assert f.size_bytes == 0

    async def test_create_file_all_fields(self, db_session, project):
        f = await create_project_file(
            db_session,
            project_id=project.id,
            file_type="notebook",
            filename="analysis.ipynb",
            storage_path=f"{project.owner_id}/{project.slug}/analysis.ipynb",
            size_bytes=12_345,
            content_type="application/x-ipynb+json",
            title="My Analysis",
            description="Main analysis notebook",
            is_public=True,
        )
        assert f.size_bytes == 12_345
        assert f.content_type == "application/x-ipynb+json"
        assert f.title == "My Analysis"
        assert f.is_public is True

    async def test_get_file_by_id_found(self, db_session, project):
        f = await create_project_file(
            db_session,
            project_id=project.id,
            file_type="data",
            filename="x.csv",
            storage_path="a/b/x.csv",
        )
        result = await get_file_by_id(db_session, f.id)
        assert result is not None
        assert result.id == f.id

    async def test_get_file_by_id_not_found(self, db_session):
        assert await get_file_by_id(db_session, "no-such-id") is None

    async def test_get_files_for_project(self, db_session, project):
        for i in range(3):
            await create_project_file(
                db_session,
                project_id=project.id,
                file_type="data",
                filename=f"file{i}.csv",
                storage_path=f"a/b/file{i}.csv",
            )
        results = await get_files_for_project(db_session, project.id)
        assert len(results) == 3

    async def test_get_files_for_project_empty(self, db_session, project):
        results = await get_files_for_project(db_session, project.id)
        assert results == []

    async def test_delete_project_file(self, db_session, project):
        f = await create_project_file(
            db_session,
            project_id=project.id,
            file_type="data",
            filename="delete_me.csv",
            storage_path="a/b/delete_me.csv",
        )
        await delete_project_file(db_session, f.id)
        assert await get_file_by_id(db_session, f.id) is None

    async def test_delete_nonexistent_file_is_noop(self, db_session):
        # Should not raise
        await delete_project_file(db_session, "no-such-id")


# ---------------------------------------------------------------------------
# get_or_create_api_token / get_user_by_api_token
# ---------------------------------------------------------------------------


class TestApiToken:
    @pytest.fixture
    async def user(self, db_session):
        return await _make_user(db_session)

    async def test_creates_token_and_returns_raw(self, db_session, user):
        raw_token, record = await get_or_create_api_token(db_session, user.id)
        assert isinstance(raw_token, str)
        assert len(raw_token) == 64  # secrets.token_hex(32) = 64 hex chars
        assert record.user_id == user.id
        assert record.token_hash != raw_token  # hash is stored, not raw

    async def test_lookup_by_raw_token(self, db_session, user):
        raw_token, _ = await get_or_create_api_token(db_session, user.id)
        found = await get_user_by_api_token(db_session, raw_token)
        assert found is not None
        assert found.id == user.id

    async def test_wrong_token_returns_none(self, db_session, user):
        await get_or_create_api_token(db_session, user.id)
        result = await get_user_by_api_token(db_session, "not-a-real-token")
        assert result is None

    async def test_rotating_token_invalidates_old(self, db_session, user):
        raw_old, _ = await get_or_create_api_token(db_session, user.id)
        raw_new, _ = await get_or_create_api_token(db_session, user.id)

        assert await get_user_by_api_token(db_session, raw_old) is None
        assert await get_user_by_api_token(db_session, raw_new) is not None

    async def test_lookup_updates_last_used_at(self, db_session, user):
        from sqlalchemy import select

        raw_token, record = await get_or_create_api_token(db_session, user.id)
        assert record.last_used_at is None

        await get_user_by_api_token(db_session, raw_token)

        result = await db_session.execute(
            select(UserApiToken).where(UserApiToken.id == record.id)
        )
        updated = result.scalar_one()
        assert updated.last_used_at is not None

    async def test_integrity_error_triggers_retry_and_succeeds(self, db_session, user):
        """If the first savepoint raises IntegrityError, the retry succeeds."""
        import contextlib
        from unittest.mock import patch
        from sqlalchemy.exc import IntegrityError

        attempt_count = 0
        fresh_raw = secrets.token_hex(32)
        fresh_hash = _hash_token(fresh_raw)

        original_begin_nested = db_session.begin_nested

        @contextlib.asynccontextmanager
        async def fail_first_then_succeed():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count == 1:
                # Simulate: savepoint exits but the commit races and collides
                yield
                raise IntegrityError("concurrent insert", {}, Exception())
            else:
                # Second attempt: let the real savepoint run
                async with original_begin_nested() as sp:
                    yield sp

        with patch.object(db_session, "begin_nested", fail_first_then_succeed):
            with patch("app.db.crud.secrets.token_hex", return_value=fresh_raw):
                raw_token, record = await get_or_create_api_token(db_session, user.id)

        assert attempt_count == 2
        assert raw_token == fresh_raw
        assert record.token_hash == fresh_hash
        found = await get_user_by_api_token(db_session, raw_token)
        assert found is not None
        assert found.id == user.id

    async def test_integrity_error_reraises_after_two_failures(self, db_session, user):
        """If both attempts fail with IntegrityError, the exception propagates."""
        import contextlib
        from unittest.mock import patch
        from sqlalchemy.exc import IntegrityError

        attempt_count = 0

        @contextlib.asynccontextmanager
        async def always_raises():
            nonlocal attempt_count
            attempt_count += 1
            yield
            raise IntegrityError("concurrent insert", {}, Exception())

        with patch.object(db_session, "begin_nested", always_raises):
            with pytest.raises(IntegrityError):
                await get_or_create_api_token(db_session, user.id)

        assert attempt_count == 2  # both attempts were made before re-raising

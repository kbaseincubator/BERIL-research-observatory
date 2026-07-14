"""Tests for user data routes (app.routes.data)."""

import os
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.db.crud import get_file_by_id, get_files_for_project
from app.db.models import BerilUser, UserProject
from app.db.session import get_db
from app.main import create_app
from app.storage import LocalFileStorage


# ---------------------------------------------------------------------------
# Shared token / oauth helpers (mirrors test_auth.py)
# ---------------------------------------------------------------------------

GOOD_TOKEN = {
    "access_token": "fake-access-token",
    "token_type": "bearer",
    "orcid": "0000-0001-2345-6789",
    "name": "Test Researcher",
}


def make_mock_oauth_client(token: dict | None = None):
    auth_url = (
        "https://sandbox.orcid.org/oauth/authorize"
        "?client_id=APP-TESTCLIENTID&scope=%2Fauthenticate"
        "&response_type=code&redirect_uri=http%3A%2F%2Flocalhost%3A8000"
        "%2Fauth%2Forcid%2Fcallback&state=mock-state"
    )
    mock_instance = MagicMock()
    mock_instance.create_authorization_url = MagicMock(return_value=(auth_url, "mock-state"))
    mock_instance.fetch_token = AsyncMock(return_value=token or {})
    mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
    mock_instance.__aexit__ = AsyncMock(return_value=False)
    return MagicMock(return_value=mock_instance), mock_instance


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_ENV = {
    "BERIL_TEST_SKIP_LIFESPAN": "True",
    "BERIL_ORCID_CLIENT_ID": "APP-TESTCLIENTID",
    "BERIL_ORCID_CLIENT_SECRET": "test-secret",
    "BERIL_ORCID_BASE_URL": "https://sandbox.orcid.org",
    "BERIL_SESSION_SECRET_KEY": "test-session-secret",
}


@pytest.fixture
def client(repository_data, app_data_context, db_session):
    """TestClient backed by in-memory DB, ORCiD credentials set, lifespan skipped."""
    with patch.dict(os.environ, _ENV):
        import app.config as cfg
        cfg._settings = None
        app_instance = create_app()

        async def override_get_db() -> AsyncGenerator:
            yield db_session

        app_instance.dependency_overrides[get_db] = override_get_db
        with TestClient(app_instance, raise_server_exceptions=True) as c:
            app_instance.state.repo_data = repository_data
            app_instance.state.base_context = app_data_context
            yield c
        cfg._settings = None


@pytest.fixture
def storage(tmp_path):
    """LocalFileStorage rooted at a temp directory."""
    return LocalFileStorage(tmp_path)


@pytest.fixture
async def beril_user(db_session):
    """A BerilUser row matching GOOD_TOKEN's ORCiD."""
    u = BerilUser(orcid_id=GOOD_TOKEN["orcid"], display_name=GOOD_TOKEN["name"])
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


@pytest.fixture
async def user_project(db_session, beril_user):
    """A UserProject owned by beril_user."""
    p = UserProject(
        owner_id=beril_user.id,
        slug="test-project",
        title="Test Project",
        research_question="What is X?",
    )
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(p)
    return p


def _login(client):
    """Drive the mock ORCiD callback to set a real session cookie."""
    mock_class, _ = make_mock_oauth_client(token=GOOD_TOKEN)
    with patch("app.routes.auth.AsyncOAuth2Client", mock_class):
        client.get(
            "/auth/orcid/callback",
            params={"code": "fake-code"},
            follow_redirects=False,
        )


# ---------------------------------------------------------------------------
# GET /user/data
# ---------------------------------------------------------------------------


class TestUserDataPage:
    def test_redirects_when_not_logged_in(self, client):
        resp = client.get("/user/data", follow_redirects=False)
        assert resp.status_code == 302
        assert "/auth/login" in resp.headers["location"]

    def test_returns_200_when_logged_in(self, client, beril_user):
        _login(client)
        resp = client.get("/user/data")
        assert resp.status_code == 200

    def test_shows_project_name(self, client, beril_user, user_project):
        _login(client)
        resp = client.get("/user/data")
        assert resp.status_code == 200
        assert user_project.title in resp.text


# ---------------------------------------------------------------------------
# GET /user/data/new
# ---------------------------------------------------------------------------


class TestUserDataNewForm:
    def test_redirects_when_not_logged_in(self, client):
        resp = client.get("/user/data/new", follow_redirects=False)
        assert resp.status_code == 302
        assert "/auth/login" in resp.headers["location"]

    def test_returns_200_when_logged_in(self, client, beril_user):
        _login(client)
        resp = client.get("/user/data/new")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# GET /user/projects/{id}
# ---------------------------------------------------------------------------


class TestUserProjectFilesPage:
    def test_redirects_when_not_logged_in(self, client, user_project):
        resp = client.get(f"/user/projects/{user_project.id}", follow_redirects=False)
        assert resp.status_code == 302
        assert "/auth/login" in resp.headers["location"]

    def test_returns_200_when_logged_in(self, client, beril_user, user_project):
        _login(client)
        resp = client.get(f"/user/projects/{user_project.id}")
        assert resp.status_code == 200

    def test_shows_project_title(self, client, beril_user, user_project):
        _login(client)
        resp = client.get(f"/user/projects/{user_project.id}")
        assert resp.status_code == 200
        assert user_project.title in resp.text

    def test_returns_403_for_wrong_owner(self, client, beril_user, db_session, tmp_path):
        _login(client)
        import asyncio

        async def _other():
            p = UserProject(owner_id="stranger", slug="s", title="T", research_question="Q?")
            db_session.add(p)
            await db_session.commit()
            await db_session.refresh(p)
            return p

        other = asyncio.get_event_loop().run_until_complete(_other())
        resp = client.get(f"/user/projects/{other.id}", follow_redirects=False)
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# POST /user/data/upload-to-project
# ---------------------------------------------------------------------------


class TestUserDataUploadPost:
    def test_upload_creates_project_file(self, client, beril_user, user_project, db_session, tmp_path):
        _login(client)
        with patch("app.routes.data._storage") as mock_storage_fn:
            storage = LocalFileStorage(tmp_path)
            mock_storage_fn.return_value = storage

            resp = client.post(
                "/user/data/upload-to-project",
                data={
                    "project_id": user_project.id,
                    "file_type": "data",
                    "is_public": False,
                },
                files={"files": ("results.csv", b"a,b\n1,2", "text/csv")},
                follow_redirects=False,
            )

        assert resp.status_code == 302
        assert resp.headers["location"] == f"/user/projects/{user_project.id}"

    async def test_upload_stores_file_on_disk(self, client, beril_user, user_project, db_session, tmp_path):
        _login(client)
        with patch("app.routes.data._storage") as mock_storage_fn:
            storage = LocalFileStorage(tmp_path)
            mock_storage_fn.return_value = storage

            client.post(
                "/user/data/upload-to-project",
                data={"project_id": user_project.id, "file_type": "data"},
                files={"files": ("data.csv", b"x,y\n1,2", "text/csv")},
                follow_redirects=False,
            )

        owner_id, slug = user_project.filesystem_path_parts
        assert storage.exists(f"{owner_id}/{slug}/uploads/data.csv")

    async def test_upload_creates_db_record(self, client, beril_user, user_project, db_session, tmp_path):
        _login(client)
        with patch("app.routes.data._storage") as mock_storage_fn:
            mock_storage_fn.return_value = LocalFileStorage(tmp_path)

            client.post(
                "/user/data/upload-to-project",
                data={"project_id": user_project.id, "file_type": "data"},
                files={"files": ("data.csv", b"x,y", "text/csv")},
                follow_redirects=False,
            )

        files = await get_files_for_project(db_session, user_project.id)
        assert len(files) == 1
        assert files[0].filename == "data.csv"
        assert files[0].source == "upload"

    async def test_upload_upserts_existing_file(self, client, beril_user, user_project, db_session, tmp_path):
        _login(client)
        storage = LocalFileStorage(tmp_path)

        with patch("app.routes.data._storage", return_value=storage):
            client.post(
                "/user/data/upload-to-project",
                data={"project_id": user_project.id, "file_type": "data"},
                files={"files": ("data.csv", b"v1", "text/csv")},
                follow_redirects=False,
            )
            client.post(
                "/user/data/upload-to-project",
                data={"project_id": user_project.id, "file_type": "data"},
                files={"files": ("data.csv", b"v2_longer", "text/csv")},
                follow_redirects=False,
            )

        files = await get_files_for_project(db_session, user_project.id)
        assert len(files) == 1  # no duplicate
        assert files[0].size_bytes == len(b"v2_longer")

    def test_upload_rejects_wrong_owner(self, client, db_session, beril_user, user_project, tmp_path):
        """A project owned by a different user should return 403."""
        _login(client)
        # Create a second user and project not owned by the logged-in user
        import asyncio
        other_id = "other-user-id-000"

        async def _create_other_project():
            other_project = UserProject(
                owner_id=other_id,
                slug="other-project",
                title="Other",
                research_question="Q?",
            )
            db_session.add(other_project)
            await db_session.commit()
            await db_session.refresh(other_project)
            return other_project

        other_project = asyncio.get_event_loop().run_until_complete(_create_other_project())

        with patch("app.routes.data._storage", return_value=LocalFileStorage(tmp_path)):
            resp = client.post(
                "/user/data/upload-to-project",
                data={"project_id": other_project.id, "file_type": "data"},
                files={"files": ("x.csv", b"data", "text/csv")},
                follow_redirects=False,
            )
        assert resp.status_code == 403

    def test_upload_strips_directory_from_filename(self, client, beril_user, user_project, tmp_path):
        """Path traversal via filename should be stripped to the basename."""
        _login(client)
        storage = LocalFileStorage(tmp_path)
        with patch("app.routes.data._storage", return_value=storage):
            client.post(
                "/user/data/upload-to-project",
                data={"project_id": user_project.id, "file_type": "data"},
                files={"files": ("../../evil.csv", b"bad", "text/csv")},
                follow_redirects=False,
            )
        owner_id, slug = user_project.filesystem_path_parts
        # Should be stored as "evil.csv", not at a path that escapes the project dir
        assert storage.exists(f"{owner_id}/{slug}/uploads/evil.csv")

    def test_upload_rejects_invalid_file_type(self, client, beril_user, user_project, tmp_path):
        """An unknown file_type must be rejected before writing to storage."""
        _login(client)
        storage = LocalFileStorage(tmp_path)
        with patch("app.routes.data._storage", return_value=storage):
            resp = client.post(
                "/user/data/upload-to-project",
                data={"project_id": user_project.id, "file_type": "evil_type"},
                files={"files": ("x.csv", b"data", "text/csv")},
                follow_redirects=False,
            )
        assert resp.status_code == 422
        # No blob should have been written to storage
        owner_id, slug = user_project.filesystem_path_parts
        assert not storage.exists(f"{owner_id}/{slug}/uploads/x.csv")

    @pytest.mark.parametrize("bad_name", [".", ".."])
    def test_upload_rejects_dot_filenames(self, bad_name, client, beril_user, user_project, tmp_path):
        """Filenames of '.' or '..' must be rejected with 422 before touching storage."""
        _login(client)
        storage = LocalFileStorage(tmp_path)
        with patch("app.routes.data._storage", return_value=storage):
            resp = client.post(
                "/user/data/upload-to-project",
                data={"project_id": user_project.id, "file_type": "data"},
                files={"files": (bad_name, b"data", "text/plain")},
                follow_redirects=False,
            )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# DELETE /user/data/{file_id}
# ---------------------------------------------------------------------------


class TestUserDataDelete:
    async def test_delete_removes_db_record(self, client, beril_user, user_project, db_session, tmp_path):
        from app.db.crud import create_project_file

        _login(client)
        storage = LocalFileStorage(tmp_path)
        owner_id, slug = user_project.filesystem_path_parts
        path = f"{owner_id}/{slug}/uploads/del.csv"
        await storage.save(b"data", path)
        record = await create_project_file(
            db_session,
            project_id=user_project.id,
            file_type="data",
            filename="del.csv",
            storage_path=path,
            source="upload",
        )

        with patch("app.routes.data._storage", return_value=storage):
            resp = client.delete(f"/user/data/{record.id}")

        assert resp.status_code == 204
        assert await get_file_by_id(db_session, record.id) is None

    async def test_delete_removes_storage_blob(self, client, beril_user, user_project, db_session, tmp_path):
        from app.db.crud import create_project_file

        _login(client)
        storage = LocalFileStorage(tmp_path)
        owner_id, slug = user_project.filesystem_path_parts
        path = f"{owner_id}/{slug}/uploads/del.csv"
        await storage.save(b"data", path)
        record = await create_project_file(
            db_session,
            project_id=user_project.id,
            file_type="data",
            filename="del.csv",
            storage_path=path,
            source="upload",
        )

        with patch("app.routes.data._storage", return_value=storage):
            client.delete(f"/user/data/{record.id}")

        assert not storage.exists(path)

    async def test_delete_rejects_wrong_owner(self, client, beril_user, user_project, db_session, tmp_path):
        from app.db.crud import create_project_file

        _login(client)
        # Create a project owned by a different user
        other_project = UserProject(
            owner_id="other-user-00",
            slug="other",
            title="Other",
            research_question="Q?",
        )
        db_session.add(other_project)
        await db_session.commit()
        await db_session.refresh(other_project)

        storage = LocalFileStorage(tmp_path)
        path = "other-user-00/other/uploads/x.csv"
        await storage.save(b"data", path)
        record = await create_project_file(
            db_session,
            project_id=other_project.id,
            file_type="data",
            filename="x.csv",
            storage_path=path,
            source="upload",
        )

        with patch("app.routes.data._storage", return_value=storage):
            resp = client.delete(f"/user/data/{record.id}")

        assert resp.status_code == 403

    def test_delete_returns_401_when_not_logged_in(self, client):
        resp = client.delete("/user/data/nonexistent-id")
        assert resp.status_code == 401

    def test_delete_returns_404_for_missing_file(self, client, beril_user, tmp_path):
        _login(client)
        with patch("app.routes.data._storage", return_value=LocalFileStorage(tmp_path)):
            resp = client.delete("/user/data/no-such-id")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /user/projects/{project_id}/github-sync
# ---------------------------------------------------------------------------


class TestGithubSync:
    def test_sync_redirects_on_success(self, client, beril_user, user_project, tmp_path):
        _login(client)
        storage = LocalFileStorage(tmp_path)

        with (
            patch("app.routes.data._storage", return_value=storage),
            patch("app.routes.data.sync_github_repo", new_callable=AsyncMock) as mock_sync,
        ):
            mock_sync.return_value = ([], "main")
            resp = client.post(
                f"/user/projects/{user_project.id}/github-sync",
                data={"github_repo_url": "https://github.com/org/repo", "branch": "main"},
                follow_redirects=False,
            )

        assert resp.status_code == 302
        assert resp.headers["location"] == f"/user/projects/{user_project.id}"

    async def test_sync_stores_github_repo_url(self, client, beril_user, user_project, db_session, tmp_path):
        from app.db.crud import get_project_by_id

        _login(client)
        with (
            patch("app.routes.data._storage", return_value=LocalFileStorage(tmp_path)),
            patch("app.routes.data.sync_github_repo", new_callable=AsyncMock, return_value=([], "main")),
        ):
            client.post(
                f"/user/projects/{user_project.id}/github-sync",
                data={"github_repo_url": "https://github.com/org/repo"},
                follow_redirects=False,
            )

        project = await get_project_by_id(db_session, user_project.id)
        assert project.github_repo_url == "https://github.com/org/repo"

    def test_sync_rejects_wrong_owner(self, client, beril_user, db_session, tmp_path):
        _login(client)
        import asyncio

        async def _other():
            p = UserProject(owner_id="stranger", slug="s", title="T", research_question="Q?")
            db_session.add(p)
            await db_session.commit()
            await db_session.refresh(p)
            return p

        other = asyncio.get_event_loop().run_until_complete(_other())

        with patch("app.routes.data._storage", return_value=LocalFileStorage(tmp_path)):
            resp = client.post(
                f"/user/projects/{other.id}/github-sync",
                data={"github_repo_url": "https://github.com/org/repo"},
                follow_redirects=False,
            )
        assert resp.status_code == 403

    def test_sync_handles_sync_exception_gracefully(self, client, beril_user, user_project, tmp_path):
        """Sync errors should not propagate — the route catches them and redirects."""
        _login(client)
        with (
            patch("app.routes.data._storage", return_value=LocalFileStorage(tmp_path)),
            patch(
                "app.routes.data.sync_github_repo",
                new_callable=AsyncMock,
                side_effect=Exception("clone failed"),
            ),
        ):
            resp = client.post(
                f"/user/projects/{user_project.id}/github-sync",
                data={"github_repo_url": "https://github.com/org/repo"},
                follow_redirects=False,
            )
        assert resp.status_code == 302

    def test_sync_rejects_non_github_url(self, client, beril_user, user_project, tmp_path):
        """Non-repo GitHub URLs and non-github.com URLs must be rejected."""
        _login(client)
        for bad_url in [
            "file:///etc/passwd",
            "http://github.com/org/repo",           # http not https
            "https://evil.com/org/repo",
            "https://internal-server/repo",
            "ssh://git@github.com/org/repo",
            # Credential-bearing URLs: secret would be persisted and logged
            "https://token:x-oauth-basic@github.com/org/repo",
            "https://user@github.com/org/repo",
            # Bare github.com or org-only pages: not a clonable repo URL
            "https://github.com",
            "https://github.com/org",
            # Sub-pages of a repo: not directly clonable (3+ path segments)
            "https://github.com/org/repo/issues",
            "https://github.com/org/repo/pulls",
            # Browser-copied URLs with query strings or fragments
            "https://github.com/org/repo?tab=readme-ov-file",
            "https://github.com/org/repo#readme",
        ]:
            resp = client.post(
                f"/user/projects/{user_project.id}/github-sync",
                data={"github_repo_url": bad_url},
                follow_redirects=False,
            )
            assert resp.status_code == 422, f"Expected 422 for URL: {bad_url}"


# ---------------------------------------------------------------------------
# GET /api/data/{file_id}
# ---------------------------------------------------------------------------


class TestApiGetFile:
    async def test_returns_file_bytes_for_owner(self, client, beril_user, user_project, db_session, tmp_path):
        from app.db.crud import create_project_file

        _login(client)
        storage = LocalFileStorage(tmp_path)
        owner_id, slug = user_project.filesystem_path_parts
        path = f"{owner_id}/{slug}/uploads/report.csv"
        await storage.save(b"col1,col2\n1,2", path)
        record = await create_project_file(
            db_session,
            project_id=user_project.id,
            file_type="data",
            filename="report.csv",
            storage_path=path,
            content_type="text/csv",
            source="upload",
        )

        with patch("app.routes.data._storage", return_value=storage):
            resp = client.get(f"/api/data/{record.id}")

        assert resp.status_code == 200
        assert resp.content == b"col1,col2\n1,2"
        assert resp.headers["content-type"].startswith("text/csv")

    async def test_returns_public_file_without_auth(self, client, user_project, db_session, tmp_path):
        """Public files should be accessible without authentication."""
        storage = LocalFileStorage(tmp_path)
        owner_id, slug = user_project.filesystem_path_parts
        path = f"{owner_id}/{slug}/uploads/public.csv"
        await storage.save(b"public data", path)

        from app.db.crud import create_project_file
        record = await create_project_file(
            db_session,
            project_id=user_project.id,
            file_type="data",
            filename="public.csv",
            storage_path=path,
            is_public=True,
            source="upload",
        )

        with patch("app.routes.data._storage", return_value=storage):
            resp = client.get(f"/api/data/{record.id}")

        assert resp.status_code == 200
        assert resp.content == b"public data"

    async def test_returns_403_for_private_file_without_auth(self, client, user_project, db_session, tmp_path):
        from app.db.crud import create_project_file

        storage = LocalFileStorage(tmp_path)
        owner_id, slug = user_project.filesystem_path_parts
        path = f"{owner_id}/{slug}/uploads/private.csv"
        await storage.save(b"secret", path)
        record = await create_project_file(
            db_session,
            project_id=user_project.id,
            file_type="data",
            filename="private.csv",
            storage_path=path,
            is_public=False,
            source="upload",
        )

        with patch("app.routes.data._storage", return_value=storage):
            resp = client.get(f"/api/data/{record.id}")

        assert resp.status_code == 403

    async def test_returns_file_via_bearer_token(self, client, beril_user, user_project, db_session, tmp_path):
        from app.db.crud import create_project_file, get_or_create_api_token

        storage = LocalFileStorage(tmp_path)
        owner_id, slug = user_project.filesystem_path_parts
        path = f"{owner_id}/{slug}/uploads/bearer.csv"
        await storage.save(b"bearer data", path)
        record = await create_project_file(
            db_session,
            project_id=user_project.id,
            file_type="data",
            filename="bearer.csv",
            storage_path=path,
            is_public=False,
            source="upload",
        )
        raw_token, _ = await get_or_create_api_token(db_session, beril_user.id)

        with patch("app.routes.data._storage", return_value=storage):
            resp = client.get(
                f"/api/data/{record.id}",
                headers={"Authorization": f"Bearer {raw_token}"},
            )

        assert resp.status_code == 200
        assert resp.content == b"bearer data"

    def test_returns_404_for_missing_file(self, client):
        resp = client.get("/api/data/no-such-id")
        assert resp.status_code == 404

    async def test_returns_404_when_blob_missing_from_storage(
        self, client, beril_user, user_project, db_session, tmp_path
    ):
        """A stale DB record whose storage blob is gone should return 404, not 500."""
        from app.db.crud import create_project_file

        _login(client)
        # Create a DB record but do NOT write the storage blob
        record = await create_project_file(
            db_session,
            project_id=user_project.id,
            file_type="data",
            filename="ghost.csv",
            storage_path="nonexistent/path/ghost.csv",
            is_public=True,
            source="upload",
        )

        storage = LocalFileStorage(tmp_path)
        with patch("app.routes.data._storage", return_value=storage):
            resp = client.get(f"/api/data/{record.id}")

        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/user/token
# ---------------------------------------------------------------------------


class TestApiUserToken:
    def test_returns_401_when_not_logged_in(self, client):
        resp = client.post("/api/user/token")
        assert resp.status_code == 401

    def test_returns_token_when_logged_in(self, client, beril_user):
        _login(client)
        resp = client.post("/api/user/token")
        assert resp.status_code == 200
        data = resp.json()
        assert "token" in data
        assert len(data["token"]) == 64  # 32 bytes hex = 64 chars
        assert "created_at" in data

    def test_returns_new_token_on_rotation(self, client, beril_user):
        _login(client)
        token1 = client.post("/api/user/token").json()["token"]
        token2 = client.post("/api/user/token").json()["token"]
        assert token1 != token2

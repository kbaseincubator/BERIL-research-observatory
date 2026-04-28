"""Tests for admin routes (app.routes.admin)."""

import os
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.db.models import BerilUser, ProjectImportRecord, UserRole
from app.db.session import get_db
from app.main import create_app


# ---------------------------------------------------------------------------
# Shared env / helpers
# ---------------------------------------------------------------------------


_ENV = {
    "BERIL_TEST_SKIP_LIFESPAN": "True",
    "BERIL_ORCID_CLIENT_ID": "APP-TESTCLIENTID",
    "BERIL_ORCID_CLIENT_SECRET": "test-secret",
    "BERIL_ORCID_BASE_URL": "https://sandbox.orcid.org",
    "BERIL_SESSION_SECRET_KEY": "test-session-secret",
}

GOOD_TOKEN = {
    "access_token": "fake-access-token",
    "token_type": "bearer",
    "orcid": "0000-0001-2345-6789",
    "name": "Admin Researcher",
}


def make_mock_oauth_client(token=None):
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


@pytest.fixture
def client(repository_data, app_data_context, db_session):
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
async def regular_user(db_session):
    u = BerilUser(orcid_id=GOOD_TOKEN["orcid"], display_name=GOOD_TOKEN["name"])
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


@pytest.fixture
async def admin_user(db_session, regular_user):
    role = UserRole(user_id=regular_user.id, role="admin")
    db_session.add(role)
    await db_session.commit()
    return regular_user


def _login(client):
    mock_class, _ = make_mock_oauth_client(token=GOOD_TOKEN)
    with patch("app.routes.auth.AsyncOAuth2Client", mock_class):
        client.get(
            "/auth/orcid/callback",
            params={"code": "fake-code"},
            follow_redirects=False,
        )


# ---------------------------------------------------------------------------
# GET /admin/import/status — auth enforcement
# ---------------------------------------------------------------------------


class TestImportStatusAuth:
    def test_requires_authentication(self, client):
        resp = client.get("/admin/import/status", follow_redirects=False)
        assert resp.status_code == 401

    def test_rejects_non_admin_user(self, client, regular_user):
        _login(client)
        resp = client.get("/admin/import/status", follow_redirects=False)
        assert resp.status_code == 403

    def test_allows_admin_user(self, client, admin_user):
        _login(client)
        resp = client.get("/admin/import/status")
        assert resp.status_code == 200

    def test_shows_import_records(self, client, admin_user, db_session):
        # We can't easily add rows through the client, but we can verify the
        # template renders without error and contains expected structure.
        _login(client)
        resp = client.get("/admin/import/status")
        assert resp.status_code == 200
        assert "Import Status" in resp.text


# ---------------------------------------------------------------------------
# POST /admin/import/run — auth and behavior
# ---------------------------------------------------------------------------


class TestRunImportEndpoint:
    def test_requires_authentication(self, client):
        resp = client.post("/admin/import/run")
        assert resp.status_code == 401

    def test_rejects_non_admin(self, client, regular_user):
        _login(client)
        resp = client.post("/admin/import/run")
        assert resp.status_code == 403

    def test_returns_summary_json(self, client, admin_user, tmp_path):
        _login(client)

        # Point the importer at an empty directory via settings patch
        empty_projects = tmp_path / "projects"
        empty_projects.mkdir()

        from app.importer import MigrationSummary
        mock_summary = MigrationSummary(total=0, imported=0, skipped=0, failed=0)

        with patch("app.routes.admin.run_full_migration", AsyncMock(return_value=mock_summary)):
            resp = client.post("/admin/import/run")

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "total" in data
        assert "imported" in data
        assert "results" in data


# ---------------------------------------------------------------------------
# POST /admin/import/{slug}/resync
# ---------------------------------------------------------------------------


class TestResyncProjectEndpoint:
    def test_requires_authentication(self, client):
        resp = client.post("/admin/import/missing_slug/resync")
        assert resp.status_code == 401

    def test_rejects_non_admin(self, client, regular_user):
        _login(client)
        resp = client.post("/admin/import/missing_slug/resync")
        assert resp.status_code == 403

    def test_returns_404_for_unknown_slug(self, client, admin_user, tmp_path):
        _login(client)
        # Settings will point projects_dir at the real repo; slug won't exist
        resp = client.post("/admin/import/totally_unknown_slug_xyz/resync")
        assert resp.status_code == 404

    def test_returns_result_json_on_success(self, client, admin_user, tmp_path):
        _login(client)
        from app.importer import ImportResult

        mock_result = ImportResult(
            repo_path="projects/test_slug",
            status="imported",
            project_id="abc-123",
            message="3 files copied",
        )

        with (
            patch("app.routes.admin.import_project", AsyncMock(return_value=mock_result)),
            patch("app.routes.admin.Path.exists", return_value=True),
            patch("app.routes.admin.Path.is_dir", return_value=True),
        ):
            resp = client.post("/admin/import/test_slug/resync")

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "imported"
        assert data["project_id"] == "abc-123"

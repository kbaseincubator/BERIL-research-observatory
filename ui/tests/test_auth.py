"""Tests for ORCiD OAuth2 auth flow (app.auth)."""

import os
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.db.crud import get_user_by_orcid
from app.db.session import get_db
from app.main import create_app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client(repository_data, app_data_context, db_session):
    """TestClient with ORCiD credentials configured, lifespan skipped."""
    env = {
        "BERIL_TEST_SKIP_LIFESPAN": "True",
        "BERIL_ORCID_CLIENT_ID": "APP-TESTCLIENTID",
        "BERIL_ORCID_CLIENT_SECRET": "test-secret",
        "BERIL_ORCID_BASE_URL": "https://sandbox.orcid.org",
        "BERIL_SESSION_SECRET_KEY": "test-session-secret",
    }
    with patch.dict(os.environ, env):
        # Reset cached settings so the new env vars are picked up
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
def client_no_orcid(repository_data, app_data_context, db_session):
    """TestClient with no ORCiD credentials configured.

    Patches get_settings everywhere it's imported so the .env file on disk
    is never consulted and orcid_client_id stays None.
    """
    import app.config as cfg

    no_orcid_settings = MagicMock()
    no_orcid_settings.test_skip_lifespan = True
    no_orcid_settings.orcid_client_id = None
    no_orcid_settings.session_secret_key = "test-session-secret"
    no_orcid_settings.debug = False
    no_orcid_settings.app_name = "BERIL Test"
    no_orcid_settings.app_description = ""
    no_orcid_settings.static_dir = cfg.Settings().static_dir
    no_orcid_settings.projects_dir = cfg.Settings().projects_dir
    no_orcid_settings.templates_dir = cfg.Settings().templates_dir

    async def override_get_db() -> AsyncGenerator:
        yield db_session

    with patch("app.main.get_settings", return_value=no_orcid_settings):
        with patch("app.routes.auth.get_settings", return_value=no_orcid_settings):
            app_instance = create_app()
            app_instance.dependency_overrides[get_db] = override_get_db
            with TestClient(app_instance, raise_server_exceptions=True) as c:
                app_instance.state.repo_data = repository_data
                app_instance.state.base_context = app_data_context
                yield c


def make_mock_oauth_client(
    auth_url: str = "https://sandbox.orcid.org/oauth/authorize?client_id=APP-TESTCLIENTID&scope=%2Fauthenticate&response_type=code&redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fauth%2Forcid%2Fcallback&state=mock-state",
    state: str = "mock-state",
    token: dict | None = None,
):
    """Build a mock AsyncOAuth2Client context manager."""
    mock_instance = MagicMock()
    mock_instance.create_authorization_url = MagicMock(return_value=(auth_url, state))
    mock_instance.fetch_token = AsyncMock(return_value=token or {})
    mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
    mock_instance.__aexit__ = AsyncMock(return_value=False)
    mock_class = MagicMock(return_value=mock_instance)
    return mock_class, mock_instance


# ---------------------------------------------------------------------------
# /auth/login
# ---------------------------------------------------------------------------


class TestLoginRoute:
    def test_login_redirects_to_orcid(self, client):
        mock_class, _ = make_mock_oauth_client()
        with patch("app.routes.auth.AsyncOAuth2Client", mock_class):
            resp = client.get("/auth/login", follow_redirects=False)
        assert resp.status_code == 302
        assert "sandbox.orcid.org/oauth/authorize" in resp.headers["location"]

    def test_login_without_credentials_redirects_home(self, client_no_orcid):
        resp = client_no_orcid.get("/auth/login", follow_redirects=False)
        assert resp.status_code == 302
        assert resp.headers["location"] == "/"

    def test_login_stores_next_in_session(self, client):
        """The ?next= param should be preserved so we can redirect after login."""
        mock_class, _ = make_mock_oauth_client()
        with patch("app.routes.auth.AsyncOAuth2Client", mock_class):
            # Follow the redirect so the session cookie is set on the client
            client.get("/auth/login?next=/projects", follow_redirects=False)

        # Verify the session cookie is present (session was written)
        assert "beril_session" in client.cookies

    def test_login_stores_state_in_session(self, client):
        mock_class, _ = make_mock_oauth_client(state="unique-state-xyz")
        with patch("app.routes.auth.AsyncOAuth2Client", mock_class):
            client.get("/auth/login", follow_redirects=False)
        assert "beril_session" in client.cookies


# ---------------------------------------------------------------------------
# /auth/orcid/callback
# ---------------------------------------------------------------------------


GOOD_TOKEN = {
    "access_token": "fake-access-token",
    "token_type": "bearer",
    "orcid": "0000-0001-2345-6789",
    "name": "Test Researcher",
}


class TestCallbackRoute:
    def test_callback_success_redirects_home(self, client):
        mock_class, _ = make_mock_oauth_client(token=GOOD_TOKEN)
        with patch("app.routes.auth.AsyncOAuth2Client", mock_class):
            resp = client.get(
                "/auth/orcid/callback",
                params={"code": "fake-code"},
                follow_redirects=False,
            )
        assert resp.status_code == 302
        assert resp.headers["location"] == "/"

    def test_callback_success_sets_session(self, client):
        mock_class, _ = make_mock_oauth_client(token=GOOD_TOKEN)
        with patch("app.routes.auth.AsyncOAuth2Client", mock_class):
            client.get(
                "/auth/orcid/callback",
                params={"code": "fake-code"},
                follow_redirects=False,
            )
        assert "beril_session" in client.cookies

    def test_callback_redirects_to_next_url(self, client):
        """After login, should redirect to the stored login_next URL."""
        mock_class, _ = make_mock_oauth_client()
        # First hit /login?next=/projects to set login_next in session
        with patch("app.routes.auth.AsyncOAuth2Client", mock_class):
            client.get("/auth/login?next=/projects", follow_redirects=False)

        mock_class2, _ = make_mock_oauth_client(token=GOOD_TOKEN)
        with patch("app.routes.auth.AsyncOAuth2Client", mock_class2):
            resp = client.get(
                "/auth/orcid/callback",
                params={"code": "fake-code"},
                follow_redirects=False,
            )
        assert resp.headers["location"] == "/projects"

    def test_callback_with_orcid_error_param_redirects(self, client):
        resp = client.get(
            "/auth/orcid/callback",
            params={"error": "access_denied"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert "auth_error=1" in resp.headers["location"]

    def test_callback_with_no_code_redirects(self, client):
        resp = client.get("/auth/orcid/callback", follow_redirects=False)
        assert resp.status_code == 302
        assert "auth_error=1" in resp.headers["location"]

    def test_callback_token_missing_orcid_field_redirects(self, client):
        """Token response without 'orcid' field should redirect to error."""
        bad_token = {"access_token": "tok", "token_type": "bearer"}  # no 'orcid'
        mock_class, _ = make_mock_oauth_client(token=bad_token)
        with patch("app.routes.auth.AsyncOAuth2Client", mock_class):
            resp = client.get(
                "/auth/orcid/callback",
                params={"code": "fake-code"},
                follow_redirects=False,
            )
        assert resp.status_code == 302
        assert "auth_error=1" in resp.headers["location"]

    def test_callback_fetch_token_exception_redirects(self, client):
        """Network errors during token exchange should redirect to error."""
        mock_class, mock_instance = make_mock_oauth_client()
        mock_instance.fetch_token = AsyncMock(side_effect=Exception("connection refused"))
        with patch("app.routes.auth.AsyncOAuth2Client", mock_class):
            resp = client.get(
                "/auth/orcid/callback",
                params={"code": "fake-code"},
                follow_redirects=False,
            )
        assert resp.status_code == 302
        assert "auth_error=1" in resp.headers["location"]


# ---------------------------------------------------------------------------
# /auth/logout
# ---------------------------------------------------------------------------


class TestLogoutRoute:
    def test_logout_redirects_home(self, client):
        resp = client.get("/auth/logout", follow_redirects=False)
        assert resp.status_code == 302
        assert resp.headers["location"] == "/"

    def test_logout_clears_session(self, client):
        # Establish a session via callback
        mock_class, _ = make_mock_oauth_client(token=GOOD_TOKEN)
        with patch("app.routes.auth.AsyncOAuth2Client", mock_class):
            client.get(
                "/auth/orcid/callback",
                params={"code": "fake-code"},
                follow_redirects=False,
            )
        session_before = client.cookies.get("beril_session")
        assert session_before is not None

        client.get("/auth/logout", follow_redirects=False)

        # After logout the session cookie should be absent or empty
        session_after = client.cookies.get("beril_session")
        assert session_after != session_before


# ---------------------------------------------------------------------------
# get_current_user helper
# ---------------------------------------------------------------------------


class TestGetCurrentUser:
    def test_returns_none_when_not_logged_in(self, client):
        """Pages should render without a current_user when session is empty."""
        resp = client.get("/")
        assert resp.status_code == 200

    def test_user_present_in_context_after_login(self, client):
        """After a successful callback the home page should show the user name."""
        mock_class, _ = make_mock_oauth_client(token=GOOD_TOKEN)
        with patch("app.routes.auth.AsyncOAuth2Client", mock_class):
            client.get(
                "/auth/orcid/callback",
                params={"code": "fake-code"},
                follow_redirects=True,
            )
        resp = client.get("/")
        assert resp.status_code == 200
        assert "Test Researcher" in resp.text


# ---------------------------------------------------------------------------
# Callback DB integration: user record creation
# ---------------------------------------------------------------------------


class TestCallbackDbIntegration:
    async def test_callback_creates_beril_user(self, client, db_session):
        """A successful callback should persist a BerilUser row."""
        mock_class, _ = make_mock_oauth_client(token=GOOD_TOKEN)
        with patch("app.routes.auth.AsyncOAuth2Client", mock_class):
            client.get(
                "/auth/orcid/callback",
                params={"code": "fake-code"},
                follow_redirects=False,
            )

        user = await get_user_by_orcid(db_session, GOOD_TOKEN["orcid"])
        assert user is not None
        assert user.orcid_id == GOOD_TOKEN["orcid"]
        assert user.display_name == GOOD_TOKEN["name"]

    async def test_callback_sets_beril_user_id_in_session(self, client, db_session):
        """The session should contain the BERIL user UUID after login."""
        mock_class, _ = make_mock_oauth_client(token=GOOD_TOKEN)
        with patch("app.routes.auth.AsyncOAuth2Client", mock_class):
            client.get(
                "/auth/orcid/callback",
                params={"code": "fake-code"},
                follow_redirects=False,
            )

        # The session cookie must be present
        assert "beril_session" in client.cookies

        # The BERIL user in the DB has an ID that must have been written to session
        user = await get_user_by_orcid(db_session, GOOD_TOKEN["orcid"])
        assert user is not None
        assert user.id is not None

    async def test_repeated_callback_does_not_duplicate_user(self, client, db_session):
        """Logging in twice with the same ORCiD should produce exactly one user row."""
        from sqlalchemy import func, select
        from app.db.models import BerilUser

        mock_class, _ = make_mock_oauth_client(token=GOOD_TOKEN)
        with patch("app.routes.auth.AsyncOAuth2Client", mock_class):
            client.get("/auth/orcid/callback", params={"code": "c1"}, follow_redirects=False)

        mock_class2, _ = make_mock_oauth_client(token=GOOD_TOKEN)
        with patch("app.routes.auth.AsyncOAuth2Client", mock_class2):
            client.get("/auth/orcid/callback", params={"code": "c2"}, follow_redirects=False)

        result = await db_session.execute(
            select(func.count()).where(BerilUser.orcid_id == GOOD_TOKEN["orcid"])
        )
        assert result.scalar() == 1

    async def test_callback_error_does_not_create_user(self, client, db_session):
        """A failed callback (missing orcid field) should not write any user row."""
        bad_token = {"access_token": "tok", "token_type": "bearer"}
        mock_class, _ = make_mock_oauth_client(token=bad_token)
        with patch("app.routes.auth.AsyncOAuth2Client", mock_class):
            client.get("/auth/orcid/callback", params={"code": "fake-code"}, follow_redirects=False)

        user = await get_user_by_orcid(db_session, "0000-0001-2345-6789")
        assert user is None

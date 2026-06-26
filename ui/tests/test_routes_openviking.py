"""Tests for the OpenViking integration routes.

The OpenViking HTTP client coroutines are monkeypatched so these run against
the in-memory SQLite DB with no live OV instance. A real Fernet key is set in
the environment so encryption/decryption round-trips through the DB.
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.crud import get_ov_credential
from app.db.models import BerilUser, OvUserCredential
from app.db.session import get_db
from app.main import create_app
from app.clients.openviking import OpenVikingError

_ENV = {
    "BERIL_TEST_SKIP_LIFESPAN": "True",
    "BERIL_ORCID_CLIENT_ID": "APP-TESTCLIENTID",
    "BERIL_ORCID_CLIENT_SECRET": "test-secret",
    "BERIL_ORCID_BASE_URL": "https://sandbox.orcid.org",
    "BERIL_SESSION_SECRET_KEY": "test-session-secret",
    "BERIL_OV_URL": "http://ov.test:1933",
    "BERIL_OV_ACCOUNT_ID": "beril",
    "BERIL_OV_ADMIN_KEY": "admin-key",
    "BERIL_OV_CREDENTIAL_KEY": Fernet.generate_key().decode(),
}

USER_TOKEN = {
    "access_token": "fake-access-token",
    "token_type": "bearer",
    "orcid": "0000-0001-2345-6789",
    "name": "Alice Researcher",
}


def _make_mock_oauth_client(token: dict):
    auth_url = "https://sandbox.orcid.org/oauth/authorize?client_id=APP-TESTCLIENTID"
    mock_instance = MagicMock()
    mock_instance.create_authorization_url = MagicMock(return_value=(auth_url, "mock-state"))
    mock_instance.fetch_token = AsyncMock(return_value=token)
    mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
    mock_instance.__aexit__ = AsyncMock(return_value=False)
    return MagicMock(return_value=mock_instance)


def _login(client: TestClient, token: dict = USER_TOKEN) -> None:
    mock_class = _make_mock_oauth_client(token)
    with patch("app.routes.auth.AsyncOAuth2Client", mock_class):
        client.get("/auth/orcid/callback", params={"code": "fake-code"}, follow_redirects=False)


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
async def user(db_session):
    u = BerilUser(orcid_id=USER_TOKEN["orcid"], display_name=USER_TOKEN["name"])
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


def test_create_unauthenticated_returns_401(client):
    assert client.post("/api/ov/user").status_code == 401


def test_credentials_unauthenticated_returns_401(client):
    assert client.get("/api/ov/credentials").status_code == 401


# ---------------------------------------------------------------------------
# POST /api/ov/user
# ---------------------------------------------------------------------------


async def test_create_happy_path_stores_encrypted_key(client, user, db_session):
    _login(client)
    fake_register = AsyncMock(
        return_value={"account_id": "beril", "user_id": user.orcid_id, "user_key": "plain-123"}
    )
    with patch("app.routes.openviking.register_ov_user", fake_register):
        resp = client.post("/api/ov/user")

    assert resp.status_code == 201
    body = resp.json()
    assert body == {
        "account_id": "beril",
        "ov_user_id": user.orcid_id,
        "ov_url": "http://ov.test:1933",
        "created": True,
    }
    fake_register.assert_awaited_once_with(user.orcid_id)

    cred = await get_ov_credential(db_session, user.id)
    assert cred is not None
    assert cred.ov_user_id == user.orcid_id
    # The plaintext key is never stored.
    assert cred.encrypted_key != "plain-123"


async def test_create_is_idempotent_no_ov_call(client, user, db_session):
    _login(client)
    fake_register = AsyncMock(
        return_value={"account_id": "beril", "user_id": user.orcid_id, "user_key": "plain-123"}
    )
    with patch("app.routes.openviking.register_ov_user", fake_register):
        client.post("/api/ov/user")
        # Second call should short-circuit without contacting OV.
        fake_register.reset_mock()
        resp = client.post("/api/ov/user")

    assert resp.status_code == 201
    assert resp.json()["created"] is False
    fake_register.assert_not_awaited()


async def test_create_409_does_not_regenerate_or_store(client, user, db_session):
    _login(client)
    fake_register = AsyncMock(
        side_effect=OpenVikingError("exists", status_code=409, code="ALREADY_EXISTS")
    )
    fake_regen = AsyncMock()
    with patch("app.routes.openviking.register_ov_user", fake_register), patch(
        "app.routes.openviking.regenerate_ov_user_key", fake_regen
    ):
        resp = client.post("/api/ov/user")

    assert resp.status_code == 409
    fake_regen.assert_not_awaited()  # never auto-regenerate
    assert await get_ov_credential(db_session, user.id) is None


# ---------------------------------------------------------------------------
# POST /api/ov/user/regenerate
# ---------------------------------------------------------------------------


async def test_regenerate_stores_new_key(client, user, db_session):
    _login(client)
    fake_regen = AsyncMock(return_value={"user_key": "regen-456"})
    with patch("app.routes.openviking.regenerate_ov_user_key", fake_regen):
        resp = client.post("/api/ov/user/regenerate")

    assert resp.status_code == 200
    assert resp.json()["regenerated"] is True
    fake_regen.assert_awaited_once_with(user.orcid_id)
    cred = await get_ov_credential(db_session, user.id)
    assert cred is not None and cred.encrypted_key != "regen-456"


async def test_regenerate_rotates_existing_key(client, user, db_session):
    _login(client)
    # Seed an existing credential row.
    db_session.add(
        OvUserCredential(
            user_id=user.id,
            account_id="beril",
            ov_user_id=user.orcid_id,
            encrypted_key="old-cipher",
        )
    )
    await db_session.commit()

    fake_regen = AsyncMock(return_value={"user_key": "regen-789"})
    with patch("app.routes.openviking.regenerate_ov_user_key", fake_regen):
        resp = client.post("/api/ov/user/regenerate")

    assert resp.status_code == 200
    result = await db_session.execute(
        select(OvUserCredential).where(OvUserCredential.user_id == user.id)
    )
    rows = result.scalars().all()
    assert len(rows) == 1  # rotated, not duplicated
    assert rows[0].encrypted_key not in ("old-cipher", "regen-789")


# ---------------------------------------------------------------------------
# GET /api/ov/credentials
# ---------------------------------------------------------------------------


async def test_credentials_404_before_create(client, user):
    _login(client)
    assert client.get("/api/ov/credentials").status_code == 404


async def test_credentials_returns_decrypted_key(client, user):
    _login(client)
    fake_register = AsyncMock(
        return_value={"account_id": "beril", "user_id": user.orcid_id, "user_key": "plain-xyz"}
    )
    with patch("app.routes.openviking.register_ov_user", fake_register):
        client.post("/api/ov/user")

    resp = client.get("/api/ov/credentials")
    assert resp.status_code == 200
    body = resp.json()
    assert body["user_key"] == "plain-xyz"
    assert body["account_id"] == "beril"
    assert body["ov_user_id"] == user.orcid_id


# ---------------------------------------------------------------------------
# GET /api/ov/health
# ---------------------------------------------------------------------------


async def test_health_ok(client, user):
    _login(client)
    with patch("app.routes.openviking.ov_health", AsyncMock(return_value={"healthy": True})):
        resp = client.get("/api/ov/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


async def test_health_unreachable(client, user):
    _login(client)
    with patch(
        "app.routes.openviking.ov_health",
        AsyncMock(side_effect=OpenVikingError("boom")),
    ):
        resp = client.get("/api/ov/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "unreachable"

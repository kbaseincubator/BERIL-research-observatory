"""Tests for chat session CRUD and list/session pages."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models import BerilUser, ChatMessage, ChatSession
from app.db.session import get_db
from app.main import create_app


_ENV = {
    "BERIL_TEST_SKIP_LIFESPAN": "True",
    "BERIL_ORCID_CLIENT_ID": "APP-TESTCLIENTID",
    "BERIL_ORCID_CLIENT_SECRET": "test-secret",
    "BERIL_ORCID_BASE_URL": "https://sandbox.orcid.org",
    "BERIL_SESSION_SECRET_KEY": "test-session-secret",
}

USER_TOKEN = {
    "access_token": "fake-access-token",
    "token_type": "bearer",
    "orcid": "0000-0001-2345-6789",
    "name": "Alice Researcher",
}

OTHER_TOKEN = {
    "access_token": "other-access-token",
    "token_type": "bearer",
    "orcid": "0000-0002-9999-9999",
    "name": "Mallory",
}


def _make_mock_oauth_client(token: dict):
    auth_url = (
        "https://sandbox.orcid.org/oauth/authorize"
        "?client_id=APP-TESTCLIENTID&scope=%2Fauthenticate"
        "&response_type=code&redirect_uri=http%3A%2F%2Flocalhost%3A8000"
        "%2Fauth%2Forcid%2Fcallback&state=mock-state"
    )
    mock_instance = MagicMock()
    mock_instance.create_authorization_url = MagicMock(return_value=(auth_url, "mock-state"))
    mock_instance.fetch_token = AsyncMock(return_value=token)
    mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
    mock_instance.__aexit__ = AsyncMock(return_value=False)
    return MagicMock(return_value=mock_instance)


def _login(client: TestClient, token: dict = USER_TOKEN) -> None:
    mock_class = _make_mock_oauth_client(token)
    with patch("app.routes.auth.AsyncOAuth2Client", mock_class):
        client.get(
            "/auth/orcid/callback",
            params={"code": "fake-code"},
            follow_redirects=False,
        )


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


@pytest.fixture
async def other_user(db_session):
    u = BerilUser(orcid_id=OTHER_TOKEN["orcid"], display_name=OTHER_TOKEN["name"])
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


async def _make_session(db, owner, **overrides) -> ChatSession:
    defaults = dict(
        owner_id=owner.id,
        provider_id="anthropic",
        model="claude-opus-4-7",
        title="Test chat",
    )
    defaults.update(overrides)
    s = ChatSession(**defaults)
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return s


# ---------------------------------------------------------------------------
# POST /api/chat — create
# ---------------------------------------------------------------------------


class TestCreateSession:
    def test_unauthenticated_returns_401(self, client):
        resp = client.post(
            "/api/chat",
            json={"provider_id": "anthropic", "model": "claude-opus-4-7"},
        )
        assert resp.status_code == 401

    async def test_happy_path_creates_row(self, client, user, db_session):
        _login(client)
        resp = client.post(
            "/api/chat",
            json={
                "provider_id": "anthropic",
                "model": "claude-opus-4-7",
                "title": "Gene clusters",
            },
        )
        assert resp.status_code == 200
        session_id = resp.json()["session_id"]

        result = await db_session.execute(
            select(ChatSession).where(ChatSession.id == session_id)
        )
        row = result.scalar_one()
        assert row.owner_id == user.id
        assert row.provider_id == "anthropic"
        assert row.model == "claude-opus-4-7"
        assert row.title == "Gene clusters"

    def test_default_title(self, client, user):
        _login(client)
        resp = client.post(
            "/api/chat",
            json={"provider_id": "anthropic", "model": "claude-opus-4-7"},
        )
        assert resp.status_code == 200

    def test_unknown_provider_rejected(self, client, user):
        _login(client)
        resp = client.post(
            "/api/chat",
            json={"provider_id": "bogus", "model": "claude-opus-4-7"},
        )
        assert resp.status_code == 400
        assert "bogus" in resp.json()["error"]

    def test_unknown_model_rejected(self, client, user):
        _login(client)
        resp = client.post(
            "/api/chat",
            json={"provider_id": "anthropic", "model": "not-a-real-model"},
        )
        assert resp.status_code == 400
        assert "not-a-real-model" in resp.json()["error"]


# ---------------------------------------------------------------------------
# PATCH /api/chat/{id} — update (rename, archive)
# ---------------------------------------------------------------------------


class TestUpdateSession:
    def test_unauthenticated_returns_401(self, client):
        resp = client.patch("/api/chat/anything", json={"title": "x"})
        assert resp.status_code == 401

    async def test_missing_session_returns_404(self, client, user):
        _login(client)
        resp = client.patch("/api/chat/does-not-exist", json={"title": "x"})
        assert resp.status_code == 404

    async def test_other_users_session_returns_404(
        self, client, user, other_user, db_session
    ):
        """No information leak: other-user and missing both return 404."""
        foreign = await _make_session(db_session, other_user)
        _login(client)
        resp = client.patch(f"/api/chat/{foreign.id}", json={"title": "x"})
        assert resp.status_code == 404

    async def test_rename(self, client, user, db_session):
        session = await _make_session(db_session, user, title="old")
        _login(client)
        resp = client.patch(f"/api/chat/{session.id}", json={"title": "new title"})
        assert resp.status_code == 200
        assert resp.json()["title"] == "new title"

        await db_session.refresh(session)
        assert session.title == "new title"

    async def test_archive(self, client, user, db_session):
        session = await _make_session(db_session, user)
        _login(client)
        resp = client.patch(f"/api/chat/{session.id}", json={"archived": True})
        assert resp.status_code == 200
        assert resp.json()["archived"] is True

        await db_session.refresh(session)
        assert session.archived is True

    async def test_unarchive(self, client, user, db_session):
        session = await _make_session(db_session, user, archived=True)
        _login(client)
        resp = client.patch(f"/api/chat/{session.id}", json={"archived": False})
        assert resp.status_code == 200
        await db_session.refresh(session)
        assert session.archived is False

    async def test_empty_patch_rejected(self, client, user, db_session):
        session = await _make_session(db_session, user)
        _login(client)
        resp = client.patch(f"/api/chat/{session.id}", json={})
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# DELETE /api/chat/{id}
# ---------------------------------------------------------------------------


class TestDeleteSession:
    def test_unauthenticated_returns_401(self, client):
        resp = client.delete("/api/chat/anything")
        assert resp.status_code == 401

    async def test_missing_session_returns_404(self, client, user):
        _login(client)
        resp = client.delete("/api/chat/does-not-exist")
        assert resp.status_code == 404

    async def test_other_users_session_returns_404(
        self, client, user, other_user, db_session
    ):
        foreign = await _make_session(db_session, other_user)
        _login(client)
        resp = client.delete(f"/api/chat/{foreign.id}")
        assert resp.status_code == 404

    async def test_delete_removes_row_and_messages(self, client, user, db_session):
        session = await _make_session(db_session, user)
        msg = ChatMessage(session_id=session.id, role="user", content={"text": "hi"})
        db_session.add(msg)
        await db_session.commit()

        _login(client)
        resp = client.delete(f"/api/chat/{session.id}")
        assert resp.status_code == 204

        result = await db_session.execute(
            select(ChatSession).where(ChatSession.id == session.id)
        )
        assert result.scalar_one_or_none() is None

        result = await db_session.execute(
            select(ChatMessage).where(ChatMessage.session_id == session.id)
        )
        assert list(result.scalars()) == []


# ---------------------------------------------------------------------------
# GET /chat — list page
# ---------------------------------------------------------------------------


class TestListPage:
    def test_unauthenticated_redirects(self, client):
        resp = client.get("/chat", follow_redirects=False)
        assert resp.status_code == 302
        assert "/auth/login" in resp.headers["location"]

    async def test_shows_active_sessions(self, client, user, db_session):
        await _make_session(db_session, user, title="Project planning chat")
        await _make_session(db_session, user, title="Archived one", archived=True)
        _login(client)

        resp = client.get("/chat")
        assert resp.status_code == 200
        body = resp.text
        assert "Project planning chat" in body
        # Archived session shouldn't be in the main list, but should appear
        # in the Archived details section.
        assert "Archived one" in body
        assert "Archived" in body  # the <summary> label

    async def test_empty_state(self, client, user):
        _login(client)
        resp = client.get("/chat")
        assert resp.status_code == 200
        assert "You have no chats yet" in resp.text

    async def test_provider_catalog_embedded(self, client, user):
        _login(client)
        resp = client.get("/chat")
        assert "chat-providers-data" in resp.text
        # Provider IDs should appear in the JSON island.
        assert "anthropic" in resp.text
        assert "cborg" in resp.text


# ---------------------------------------------------------------------------
# GET /chat/{id} — session page
# ---------------------------------------------------------------------------


class TestSessionPage:
    def test_unauthenticated_redirects(self, client):
        resp = client.get("/chat/some-id", follow_redirects=False)
        assert resp.status_code == 302

    async def test_missing_session_returns_404(self, client, user):
        _login(client)
        resp = client.get("/chat/does-not-exist")
        assert resp.status_code == 404

    async def test_other_users_session_returns_404(
        self, client, user, other_user, db_session
    ):
        foreign = await _make_session(db_session, other_user)
        _login(client)
        resp = client.get(f"/chat/{foreign.id}")
        assert resp.status_code == 404

    async def test_renders_transcript(self, client, user, db_session):
        session = await _make_session(db_session, user, title="Research chat")
        now = datetime.now(timezone.utc)
        user_msg = ChatMessage(
            session_id=session.id,
            role="user",
            content={"text": "What genes matter?"},
            created_at=now,
        )
        assistant_msg = ChatMessage(
            session_id=session.id,
            role="assistant",
            content={"text": "Several candidates.", "tool_activity": [], "error": None},
            created_at=now,
        )
        db_session.add_all([user_msg, assistant_msg])
        await db_session.commit()

        _login(client)
        resp = client.get(f"/chat/{session.id}")
        assert resp.status_code == 200
        assert "Research chat" in resp.text
        assert "What genes matter?" in resp.text
        assert "Several candidates." in resp.text

    async def test_island_root_carries_session_metadata(
        self, client, user, db_session
    ):
        session = await _make_session(db_session, user, model="claude-sonnet-4-6")
        _login(client)
        resp = client.get(f"/chat/{session.id}")
        assert f'data-session-id="{session.id}"' in resp.text
        assert 'data-provider-id="anthropic"' in resp.text
        assert 'data-model="claude-sonnet-4-6"' in resp.text

    async def test_initial_messages_json_block_is_valid(
        self, client, user, db_session
    ):
        """The React island parses JSON out of <script id='chat-initial-messages'>.
        If this JSON is malformed, the page silently breaks client-side, so
        snapshot the structure here."""
        import json
        import re

        session = await _make_session(db_session, user)
        db_session.add_all(
            [
                ChatMessage(
                    session_id=session.id,
                    role="user",
                    content={"text": "hi"},
                ),
                ChatMessage(
                    session_id=session.id,
                    role="assistant",
                    content={
                        "text": "hello",
                        "tool_activity": [],
                        "error": None,
                    },
                ),
            ]
        )
        await db_session.commit()

        _login(client)
        resp = client.get(f"/chat/{session.id}")
        m = re.search(
            r'<script type="application/json" id="chat-initial-messages">(.*?)</script>',
            resp.text,
            re.DOTALL,
        )
        assert m is not None
        parsed = json.loads(m.group(1))
        assert isinstance(parsed, list)
        assert len(parsed) == 2
        assert {row["role"] for row in parsed} == {"user", "assistant"}
        assert all("id" in row and "created_at" in row for row in parsed)

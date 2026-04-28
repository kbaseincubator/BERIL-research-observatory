"""End-to-end tests for both chat turn endpoints (JSON + SSE)."""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncGenerator
from typing import AsyncIterator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.chat.concurrency import reset_concurrency_manager
from app.chat.providers.base import (
    ErrorEvent,
    SessionInitialized,
    TextDelta,
    ToolCall,
    ToolResult,
    TurnComplete,
    TurnEvent,
)
from app.db.models import BerilUser, ChatMessage, ChatSession
from app.db.session import get_db
from app.main import create_app


# ---------------------------------------------------------------------------
# Shared env / fixtures
# ---------------------------------------------------------------------------


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


@pytest.fixture(autouse=True)
def _reset_concurrency():
    reset_concurrency_manager()
    yield
    reset_concurrency_manager()


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
    """The BerilUser matching USER_TOKEN (must be pre-created for session auth)."""
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


@pytest.fixture
async def session_row(db_session, user):
    s = ChatSession(
        owner_id=user.id, provider_id="anthropic", model="claude-opus-4-7"
    )
    db_session.add(s)
    await db_session.commit()
    await db_session.refresh(s)
    return s


# ---------------------------------------------------------------------------
# Provider-turn fakes
# ---------------------------------------------------------------------------


def _events_ok() -> list[TurnEvent]:
    return [
        SessionInitialized(sdk_session_id="sdk-abc"),
        TextDelta(text="Hello "),
        TextDelta(text="world"),
        ToolCall(name="berdl_query", input={"sql": "SELECT 1"}, tool_use_id="tu-1"),
        ToolResult(tool_use_id="tu-1", content="3 rows"),
        TurnComplete(),
    ]


def _patched_provider(events: list[TurnEvent]):
    async def _fake(
        *, db, session, user_message, credentials
    ) -> AsyncIterator[TurnEvent]:
        for e in events:
            yield e

    return _fake


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


class TestAuth:
    def test_unauthenticated_returns_401(self, client, session_row):
        resp = client.post(
            f"/api/chat/{session_row.id}/turn",
            json={"message": "hi", "credentials": {"api_key": "k"}},
        )
        assert resp.status_code == 401

    def test_other_user_gets_403(self, client, session_row, other_user):
        _login(client, OTHER_TOKEN)
        resp = client.post(
            f"/api/chat/{session_row.id}/turn",
            json={"message": "hi", "credentials": {"api_key": "k"}},
        )
        assert resp.status_code == 403

    def test_unknown_session_returns_404(self, client, user):
        _login(client)
        resp = client.post(
            "/api/chat/does-not-exist/turn",
            json={"message": "hi", "credentials": {"api_key": "k"}},
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class TestValidation:
    def test_empty_message_rejected(self, client, session_row, user):
        _login(client)
        resp = client.post(
            f"/api/chat/{session_row.id}/turn",
            json={"message": "", "credentials": {"api_key": "k"}},
        )
        assert resp.status_code == 422

    def test_missing_credential_returns_400(self, client, session_row, user):
        _login(client)
        resp = client.post(
            f"/api/chat/{session_row.id}/turn",
            json={"message": "hi", "credentials": {}},
        )
        assert resp.status_code == 400
        assert "api_key" in resp.json()["error"]


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


class TestSuccessfulTurn:
    def test_returns_assistant_text(self, client, session_row, user):
        _login(client)
        with patch(
            "app.chat.service.run_provider_turn", _patched_provider(_events_ok())
        ):
            resp = client.post(
                f"/api/chat/{session_row.id}/turn",
                json={"message": "hi there", "credentials": {"api_key": "k"}},
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["assistant_text"] == "Hello world"
        assert body["session_id"] == session_row.id
        kinds = [t["type"] for t in body["tool_activity"]]
        assert kinds == ["tool_call", "tool_result"]

    async def test_persists_user_and_assistant_messages(
        self, client, session_row, user, db_session
    ):
        _login(client)
        with patch(
            "app.chat.service.run_provider_turn", _patched_provider(_events_ok())
        ):
            resp = client.post(
                f"/api/chat/{session_row.id}/turn",
                json={"message": "hi there", "credentials": {"api_key": "k"}},
            )
        assert resp.status_code == 200

        result = await db_session.execute(
            select(ChatMessage).where(ChatMessage.session_id == session_row.id)
        )
        msgs = list(result.scalars())
        roles = [m.role for m in msgs]
        assert roles == ["user", "assistant"]
        assert msgs[0].content == {"text": "hi there"}
        assert msgs[1].content["text"] == "Hello world"
        assert msgs[1].content["error"] is None

    async def test_sdk_session_id_captured_on_first_turn(
        self, client, session_row, user, db_session
    ):
        assert session_row.sdk_session_id is None
        _login(client)
        with patch(
            "app.chat.service.run_provider_turn", _patched_provider(_events_ok())
        ):
            resp = client.post(
                f"/api/chat/{session_row.id}/turn",
                json={"message": "hi", "credentials": {"api_key": "k"}},
            )
        assert resp.status_code == 200
        await db_session.refresh(session_row)
        assert session_row.sdk_session_id == "sdk-abc"

    async def test_subsequent_turn_preserves_original_sdk_session_id(
        self, client, session_row, user, db_session
    ):
        session_row.sdk_session_id = "already-set"
        await db_session.commit()

        events: list[TurnEvent] = [
            SessionInitialized(sdk_session_id="different-one"),
            TextDelta(text="ok"),
            TurnComplete(),
        ]
        _login(client)
        with patch("app.chat.service.run_provider_turn", _patched_provider(events)):
            resp = client.post(
                f"/api/chat/{session_row.id}/turn",
                json={"message": "follow-up", "credentials": {"api_key": "k"}},
            )
        assert resp.status_code == 200
        await db_session.refresh(session_row)
        assert session_row.sdk_session_id == "already-set"

    async def test_last_active_at_updated(
        self, client, session_row, user, db_session
    ):
        original = session_row.last_active_at
        await asyncio.sleep(0.01)

        _login(client)
        with patch(
            "app.chat.service.run_provider_turn", _patched_provider(_events_ok())
        ):
            client.post(
                f"/api/chat/{session_row.id}/turn",
                json={"message": "hi", "credentials": {"api_key": "k"}},
            )
        await db_session.refresh(session_row)
        assert session_row.last_active_at > original


# ---------------------------------------------------------------------------
# Error path
# ---------------------------------------------------------------------------


class TestProviderError:
    def test_error_returned_in_body(self, client, session_row, user):
        events: list[TurnEvent] = [
            SessionInitialized(sdk_session_id="sdk-x"),
            ErrorEvent(message="upstream 500"),
        ]
        _login(client)
        with patch("app.chat.service.run_provider_turn", _patched_provider(events)):
            resp = client.post(
                f"/api/chat/{session_row.id}/turn",
                json={"message": "hi", "credentials": {"api_key": "k"}},
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["error"] == "upstream 500"
        assert body["assistant_text"] == ""

    async def test_assistant_message_records_error(
        self, client, session_row, user, db_session
    ):
        events: list[TurnEvent] = [ErrorEvent(message="timeout")]
        _login(client)
        with patch("app.chat.service.run_provider_turn", _patched_provider(events)):
            client.post(
                f"/api/chat/{session_row.id}/turn",
                json={"message": "hi", "credentials": {"api_key": "k"}},
            )

        result = await db_session.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_row.id)
            .where(ChatMessage.role == "assistant")
        )
        msg = result.scalar_one()
        assert msg.content["error"] == "timeout"


# ---------------------------------------------------------------------------
# Concurrency
# ---------------------------------------------------------------------------


class TestConcurrency:
    def test_cap_exceeded_returns_429(
        self, client, session_row, user, db_session
    ):
        """With cap=1, two concurrent turns across two sessions → one 429."""
        # Override the singleton manager with cap=1.
        from app.chat import concurrency as c
        from app.chat.concurrency import ChatConcurrencyManager

        c._manager = ChatConcurrencyManager(per_user_cap=1)

        # Pre-reserve the user's single slot by poking the manager directly.
        # This is equivalent to "a turn is already in flight" without needing
        # two concurrent sync requests through TestClient.
        asyncio.get_event_loop().run_until_complete(
            c._manager._try_reserve_user_slot(user.id)
        )
        assert c._manager.active_turns_for(user.id) == 1

        _login(client)
        with patch(
            "app.chat.service.run_provider_turn", _patched_provider(_events_ok())
        ):
            resp = client.post(
                f"/api/chat/{session_row.id}/turn",
                json={"message": "hi", "credentials": {"api_key": "k"}},
            )
        assert resp.status_code == 429
        assert "cap" in resp.json()["error"]

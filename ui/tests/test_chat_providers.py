"""Tests for the chat provider abstraction and Anthropic-compatible impl."""

from __future__ import annotations

from typing import Any, AsyncIterator
from unittest.mock import patch

import pytest

from claude_agent_sdk import AssistantMessage, ResultMessage, SystemMessage

from app.chat.config import ProviderConfig
from app.chat.providers import (
    get_provider,
    get_providers,
    reset_providers_cache,
)
from app.chat.providers.anthropic_compatible import AnthropicCompatibleProvider
from app.chat.providers.base import (
    ChatProvider,
    Credentials,
    ErrorEvent,
    SessionInitialized,
    TextDelta,
    ToolCall,
    ToolResult,
    TurnComplete,
)


# ---------------------------------------------------------------------------
# Helpers: use real SDK message classes so isinstance() checks in the
# translator match. Blocks remain duck-typed because the translator reads
# them via getattr().
# ---------------------------------------------------------------------------


def _sys_init(session_id: str) -> SystemMessage:
    return SystemMessage(subtype="init", data={"session_id": session_id})


def _assistant(blocks: list) -> AssistantMessage:
    return AssistantMessage(content=blocks, model="m1")


def _result(subtype: str = "end_turn") -> ResultMessage:
    return ResultMessage(
        subtype=subtype,
        duration_ms=0,
        duration_api_ms=0,
        is_error=False,
        num_turns=1,
        session_id="s",
    )


class _FakeTextBlock:
    def __init__(self, text: str):
        self.text = text


class _FakeToolUseBlock:
    def __init__(self, name: str, input_: dict, id_: str = "tu-1"):
        self.name = name
        self.input = input_
        self.id = id_


class _FakeToolResultBlock:
    def __init__(self, tool_use_id: str, content: Any, is_error: bool = False):
        self.tool_use_id = tool_use_id
        self.content = content
        self.is_error = is_error


def _make_provider(auth_style: str = "api_key") -> AnthropicCompatibleProvider:
    cfg = ProviderConfig(
        display_name="Test",
        wire_protocol="anthropic",
        base_url="https://example.com",
        auth_style=auth_style,
        credential_fields=[
            {"id": "api_key", "display_name": "API Key", "secret": True}
        ],
        models=[{"id": "m1", "display_name": "Model One"}],
    )
    return AnthropicCompatibleProvider(provider_id="test", config=cfg)


def _fake_query(messages: list):
    """Return a mock query() that yields the given message list."""

    async def _fake(prompt: str, options):  # noqa: ARG001
        for m in messages:
            yield m

    return _fake


async def _collect(agen: AsyncIterator) -> list:
    return [e async for e in agen]


# ---------------------------------------------------------------------------
# Translation
# ---------------------------------------------------------------------------


class TestTurnTranslation:
    async def test_system_init_yields_session_initialized(self):
        provider = _make_provider()
        messages = [
            _sys_init("sdk-session-123"),
            _result(),
        ]
        with patch("app.chat.providers.anthropic_compatible.query", _fake_query(messages)):
            events = await _collect(
                provider.run_turn(
                    user_message="hi",
                    credentials=Credentials({"api_key": "k"}),
                    model="m1",
                    cwd="/tmp",
                    sdk_session_id=None,
                )
            )
        kinds = [e.kind for e in events]
        assert kinds == ["session_initialized", "turn_complete"]
        assert events[0].sdk_session_id == "sdk-session-123"

    async def test_assistant_text_yields_text_delta(self):
        provider = _make_provider()
        messages = [
            _assistant([_FakeTextBlock("hello ")]),
            _assistant([_FakeTextBlock("world")]),
            _result(),
        ]
        with patch("app.chat.providers.anthropic_compatible.query", _fake_query(messages)):
            events = await _collect(
                provider.run_turn(
                    user_message="hi",
                    credentials=Credentials({"api_key": "k"}),
                    model="m1",
                    cwd="/tmp",
                    sdk_session_id=None,
                )
            )
        text_events = [e for e in events if isinstance(e, TextDelta)]
        assert [e.text for e in text_events] == ["hello ", "world"]

    async def test_tool_call_translated(self):
        provider = _make_provider()
        messages = [
            _assistant(
                [_FakeToolUseBlock("berdl_query", {"sql": "SELECT 1"}, "tu-7")]
            ),
            _result(),
        ]
        with patch("app.chat.providers.anthropic_compatible.query", _fake_query(messages)):
            events = await _collect(
                provider.run_turn(
                    user_message="run a query",
                    credentials=Credentials({"api_key": "k"}),
                    model="m1",
                    cwd="/tmp",
                    sdk_session_id=None,
                )
            )
        calls = [e for e in events if isinstance(e, ToolCall)]
        assert len(calls) == 1
        assert calls[0].name == "berdl_query"
        assert calls[0].input == {"sql": "SELECT 1"}
        assert calls[0].tool_use_id == "tu-7"

    async def test_tool_result_string_content_passes_through(self):
        provider = _make_provider()
        messages = [
            _assistant([_FakeToolResultBlock("tu-7", "3 rows returned")]),
            _result(),
        ]
        with patch("app.chat.providers.anthropic_compatible.query", _fake_query(messages)):
            events = await _collect(
                provider.run_turn(
                    user_message="x",
                    credentials=Credentials({"api_key": "k"}),
                    model="m1",
                    cwd="/tmp",
                    sdk_session_id=None,
                )
            )
        results = [e for e in events if isinstance(e, ToolResult)]
        assert len(results) == 1
        assert results[0].content == "3 rows returned"
        assert results[0].is_error is False

    async def test_tool_result_list_of_text_blocks_joined(self):
        provider = _make_provider()
        content = [{"type": "text", "text": "part-a "}, {"type": "text", "text": "part-b"}]
        messages = [
            _assistant([_FakeToolResultBlock("tu-7", content)]),
            _result(),
        ]
        with patch("app.chat.providers.anthropic_compatible.query", _fake_query(messages)):
            events = await _collect(
                provider.run_turn(
                    user_message="x",
                    credentials=Credentials({"api_key": "k"}),
                    model="m1",
                    cwd="/tmp",
                    sdk_session_id=None,
                )
            )
        results = [e for e in events if isinstance(e, ToolResult)]
        assert results[0].content == "part-a part-b"

    async def test_result_message_yields_turn_complete(self):
        provider = _make_provider()
        messages = [_result(subtype="end_turn")]
        with patch("app.chat.providers.anthropic_compatible.query", _fake_query(messages)):
            events = await _collect(
                provider.run_turn(
                    user_message="x",
                    credentials=Credentials({"api_key": "k"}),
                    model="m1",
                    cwd="/tmp",
                    sdk_session_id=None,
                )
            )
        terminal = events[-1]
        assert isinstance(terminal, TurnComplete)
        assert terminal.result_subtype == "end_turn"

    async def test_exception_surfaces_as_error_event(self):
        provider = _make_provider()

        async def _bad_query(prompt, options):  # noqa: ARG001
            yield _sys_init("sess-x")
            raise RuntimeError("upstream 500")

        with patch("app.chat.providers.anthropic_compatible.query", _bad_query):
            events = await _collect(
                provider.run_turn(
                    user_message="x",
                    credentials=Credentials({"api_key": "k"}),
                    model="m1",
                    cwd="/tmp",
                    sdk_session_id=None,
                )
            )
        assert isinstance(events[-1], ErrorEvent)
        assert "upstream 500" in events[-1].message

    async def test_turn_complete_synthesized_if_missing(self):
        """If the SDK stream ends without a ResultMessage, we still emit a
        terminal event so callers don't hang."""
        provider = _make_provider()
        messages = [_assistant([_FakeTextBlock("hi")])]
        with patch("app.chat.providers.anthropic_compatible.query", _fake_query(messages)):
            events = await _collect(
                provider.run_turn(
                    user_message="x",
                    credentials=Credentials({"api_key": "k"}),
                    model="m1",
                    cwd="/tmp",
                    sdk_session_id=None,
                )
            )
        assert isinstance(events[-1], TurnComplete)


# ---------------------------------------------------------------------------
# Options wiring: env, resume, cwd, skills
# ---------------------------------------------------------------------------


class TestOptionsWiring:
    async def _capture_options(self, provider, **turn_kwargs):
        captured: dict[str, Any] = {}

        async def _spy_query(prompt, options):
            captured["prompt"] = prompt
            captured["options"] = options
            yield _result()

        with patch("app.chat.providers.anthropic_compatible.query", _spy_query):
            await _collect(provider.run_turn(**turn_kwargs))
        return captured

    async def test_api_key_auth_uses_x_api_key_env(self):
        """auth_style=api_key → key in ANTHROPIC_API_KEY (x-api-key header)."""
        provider = _make_provider(auth_style="api_key")
        captured = await self._capture_options(
            provider,
            user_message="hi",
            credentials=Credentials({"api_key": "user-secret"}),
            model="m1",
            cwd="/tmp/repo",
            sdk_session_id=None,
        )
        env = captured["options"].env
        assert env["ANTHROPIC_BASE_URL"] == "https://example.com"
        assert env["ANTHROPIC_API_KEY"] == "user-secret"
        # The bearer env var is blanked so a stale server-level default
        # can't win and produce "invalid bearer token".
        assert env["ANTHROPIC_AUTH_TOKEN"] == ""

    async def test_bearer_auth_uses_auth_token_env(self):
        """auth_style=bearer → key in ANTHROPIC_AUTH_TOKEN (Bearer header).

        This is what CBORG and similar OAuth-style proxies need.
        """
        provider = _make_provider(auth_style="bearer")
        captured = await self._capture_options(
            provider,
            user_message="hi",
            credentials=Credentials({"api_key": "user-secret"}),
            model="m1",
            cwd="/tmp/repo",
            sdk_session_id=None,
        )
        env = captured["options"].env
        assert env["ANTHROPIC_AUTH_TOKEN"] == "user-secret"
        assert env["ANTHROPIC_API_KEY"] == ""

    async def test_default_auth_style_is_api_key(self):
        """No auth_style in YAML should default to api_key (direct Anthropic)."""
        cfg = ProviderConfig(
            display_name="Default",
            wire_protocol="anthropic",
            base_url="https://example.com",
            credential_fields=[{"id": "api_key", "display_name": "K", "secret": True}],
            models=[{"id": "m1", "display_name": "Model One"}],
        )
        assert cfg.auth_style == "api_key"

    async def test_resume_passed_through(self):
        provider = _make_provider()
        captured = await self._capture_options(
            provider,
            user_message="hi",
            credentials=Credentials({"api_key": "k"}),
            model="m1",
            cwd="/tmp",
            sdk_session_id="prior-session",
        )
        assert captured["options"].resume == "prior-session"

    async def test_resume_none_when_fresh(self):
        provider = _make_provider()
        captured = await self._capture_options(
            provider,
            user_message="hi",
            credentials=Credentials({"api_key": "k"}),
            model="m1",
            cwd="/tmp",
            sdk_session_id=None,
        )
        assert captured["options"].resume is None

    async def test_model_and_cwd_passed(self):
        provider = _make_provider()
        captured = await self._capture_options(
            provider,
            user_message="hi",
            credentials=Credentials({"api_key": "k"}),
            model="claude-opus-4-7",
            cwd="/repo",
            sdk_session_id=None,
        )
        assert captured["options"].model == "claude-opus-4-7"
        assert str(captured["options"].cwd) == "/repo"

    async def test_skills_enabled_all(self):
        provider = _make_provider()
        captured = await self._capture_options(
            provider,
            user_message="hi",
            credentials=Credentials({"api_key": "k"}),
            model="m1",
            cwd="/tmp",
            sdk_session_id=None,
        )
        assert captured["options"].skills == "all"

    async def test_missing_api_key_raises(self):
        provider = _make_provider()
        with pytest.raises(ValueError, match="api_key"):
            async for _ in provider.run_turn(
                user_message="hi",
                credentials=Credentials({}),
                model="m1",
                cwd="/tmp",
                sdk_session_id=None,
            ):
                pass


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


class TestRegistry:
    def setup_method(self):
        reset_providers_cache()

    def teardown_method(self):
        reset_providers_cache()

    def test_registry_built_from_shipped_config(self):
        providers = get_providers()
        assert set(providers.keys()) == {"anthropic", "cborg"}
        assert isinstance(providers["anthropic"], ChatProvider)
        assert isinstance(providers["cborg"], ChatProvider)

    def test_get_provider_returns_same_instance(self):
        p1 = get_provider("anthropic")
        p2 = get_provider("anthropic")
        assert p1 is p2

    def test_get_provider_unknown_raises(self):
        with pytest.raises(KeyError):
            get_provider("does-not-exist")

    def test_registry_caches(self):
        first = get_providers()
        second = get_providers()
        assert first is second

    def test_reset_drops_cache(self):
        first = get_providers()
        reset_providers_cache()
        second = get_providers()
        assert first is not second

"""Provider that talks the Anthropic Messages API.

Covers both Anthropic (``https://api.anthropic.com``) and Anthropic-compatible
endpoints such as CBORG. The distinction between the two is entirely
configuration — ``base_url`` and credentials differ; wire format is
identical — so both are served by this single class.

Per-turn credentials are passed into the spawned SDK subprocess via
``ClaudeAgentOptions.env`` and are never written to logs, files, or the parent
process environment.
"""

from __future__ import annotations

import logging
from typing import Any, AsyncIterator

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    SystemMessage,
    query,
)

from app.chat.config import ProviderConfig
from app.chat.providers.base import (
    Credentials,
    ErrorEvent,
    SessionInitialized,
    TextDelta,
    ToolCall,
    ToolResult,
    TurnComplete,
    TurnEvent,
)

logger = logging.getLogger(__name__)

# Credential field id we expect every Anthropic-compatible provider to
# declare. Config validation doesn't enforce it (providers could evolve to
# need more fields), but this implementation requires it at minimum.
_API_KEY_FIELD = "api_key"


class AnthropicCompatibleProvider:
    """Runs a chat turn through the Claude Agent SDK against any
    Anthropic-format endpoint.
    """

    def __init__(self, *, provider_id: str, config: ProviderConfig) -> None:
        self.provider_id = provider_id
        self.config = config

    async def run_turn(
        self,
        *,
        user_message: str,
        credentials: Credentials,
        model: str,
        cwd: str,
        sdk_session_id: str | None,
    ) -> AsyncIterator[TurnEvent]:
        api_key = credentials.require(_API_KEY_FIELD)

        # Env is merged on top of os.environ in the SDK subprocess. The
        # auth_style dictates which env var carries the key:
        #   * api_key  → ANTHROPIC_API_KEY (sent as x-api-key header;
        #                direct Anthropic endpoints require this).
        #   * bearer   → ANTHROPIC_AUTH_TOKEN (sent as Authorization: Bearer;
        #                OAuth-style proxies like CBORG require this).
        # The unused var is blanked so any server-level default can't shadow
        # the user's key with a stale value.
        turn_env = {"ANTHROPIC_BASE_URL": self.config.base_url}
        if self.config.auth_style == "bearer":
            turn_env["ANTHROPIC_AUTH_TOKEN"] = api_key
            turn_env["ANTHROPIC_API_KEY"] = ""
        else:
            turn_env["ANTHROPIC_API_KEY"] = api_key
            turn_env["ANTHROPIC_AUTH_TOKEN"] = ""

        options = ClaudeAgentOptions(
            model=model,
            cwd=cwd,
            env=turn_env,
            resume=sdk_session_id,
            skills="all",
        )

        try:
            async for event in _stream_turn(user_message, options):
                yield event
        except Exception as exc:  # noqa: BLE001 — top-level stream guard
            logger.exception("chat turn failed for provider=%s", self.provider_id)
            yield ErrorEvent(message=str(exc))


async def _stream_turn(
    user_message: str, options: ClaudeAgentOptions
) -> AsyncIterator[TurnEvent]:
    """Drive the SDK ``query()`` and translate its messages to TurnEvents."""
    emitted_terminal = False
    async for message in query(prompt=user_message, options=options):
        for event in _translate(message):
            if isinstance(event, (TurnComplete, ErrorEvent)):
                emitted_terminal = True
            yield event
    if not emitted_terminal:
        yield TurnComplete()


def _translate(message: Any) -> list[TurnEvent]:
    """Map one SDK message to zero or more TurnEvents."""
    if isinstance(message, SystemMessage):
        if message.subtype == "init":
            sid = (message.data or {}).get("session_id")
            if sid:
                return [SessionInitialized(sdk_session_id=sid)]
        return []

    if isinstance(message, AssistantMessage):
        events: list[TurnEvent] = []
        for block in message.content or []:
            events.extend(_translate_block(block))
        return events

    if isinstance(message, ResultMessage):
        return [TurnComplete(result_subtype=getattr(message, "subtype", None))]

    # UserMessage (tool_result echoes back through the SDK), partial-message
    # events, and anything else we don't recognize: ignore.
    return []


def _translate_block(block: Any) -> list[TurnEvent]:
    """Map one content block inside an AssistantMessage to TurnEvents.

    The SDK's block types are duck-typed in the docs; we match on attributes
    rather than class names so minor SDK revisions don't break us.
    """
    # Text block
    text = getattr(block, "text", None)
    if isinstance(text, str) and text:
        return [TextDelta(text=text)]

    # Tool-use block: has name + input (+ id)
    tool_name = getattr(block, "name", None)
    tool_input = getattr(block, "input", None)
    if tool_name is not None and tool_input is not None:
        return [
            ToolCall(
                name=tool_name,
                input=_as_dict(tool_input),
                tool_use_id=getattr(block, "id", None),
            )
        ]

    # Tool-result block: has tool_use_id + content, optional is_error
    tu_id = getattr(block, "tool_use_id", None)
    tu_content = getattr(block, "content", None)
    if tu_id is not None and tu_content is not None:
        return [
            ToolResult(
                tool_use_id=tu_id,
                content=_coerce_tool_result_content(tu_content),
                is_error=bool(getattr(block, "is_error", False)),
            )
        ]

    return []


def _as_dict(v: Any) -> dict[str, Any]:
    if isinstance(v, dict):
        return v
    return {"value": v}


def _coerce_tool_result_content(v: Any) -> Any:
    """Tool result content can be a string or a list of content blocks;
    unwrap the common case to a plain string so persistence is tidier."""
    if isinstance(v, str):
        return v
    if isinstance(v, list) and all(
        isinstance(item, dict) and item.get("type") == "text" for item in v
    ):
        return "".join(item.get("text", "") for item in v)
    return v

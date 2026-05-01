"""SSE wire-format helpers for chat turn streams.

The provider yields :class:`TurnEvent` dataclasses; the browser consumes
JSON-per-frame SSE. This module is the only place that knows how to map
between them. Keep it boring — the React component parses these shapes
directly, so renaming a field here is a breaking change.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from app.chat.providers.base import (
    ErrorEvent,
    SessionInitialized,
    TextDelta,
    ToolCall,
    ToolResult,
    TurnComplete,
    TurnEvent,
)


def event_to_frame(event: TurnEvent) -> dict[str, str]:
    """Convert one TurnEvent into the dict shape ``EventSourceResponse`` expects.

    ``event`` → ``{ "event": <kind>, "data": <json payload> }``.
    """
    if isinstance(event, SessionInitialized):
        payload: dict[str, Any] = {"sdk_session_id": event.sdk_session_id}
    elif isinstance(event, TextDelta):
        payload = {"text": event.text}
    elif isinstance(event, ToolCall):
        payload = {
            "name": event.name,
            "input": event.input,
            "tool_use_id": event.tool_use_id,
        }
    elif isinstance(event, ToolResult):
        payload = {
            "tool_use_id": event.tool_use_id,
            "content": event.content,
            "is_error": event.is_error,
        }
    elif isinstance(event, ErrorEvent):
        payload = {"message": event.message}
    elif isinstance(event, TurnComplete):
        payload = {"result_subtype": event.result_subtype}
    else:  # pragma: no cover — exhaustive union
        payload = asdict(event)

    return {"event": event.kind, "data": json.dumps(payload)}


def turn_complete_frame(*, assistant_message_id: str) -> dict[str, str]:
    """Emit the final frame with the newly-persisted assistant message id.

    This is distinct from the provider's :class:`TurnComplete` event: that
    one marks the agent's end of turn; this frame is what the browser
    listens for to know the server has finished persisting and is closing
    the stream.
    """
    return {
        "event": "turn_persisted",
        "data": json.dumps({"assistant_message_id": assistant_message_id}),
    }

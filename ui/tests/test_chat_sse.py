"""Unit tests for SSE wire-format helpers."""

from __future__ import annotations

import json

from app.chat.providers.base import (
    ErrorEvent,
    SessionInitialized,
    TextDelta,
    ToolCall,
    ToolResult,
    TurnComplete,
)
from app.chat.sse import event_to_frame, turn_complete_frame


class TestEventToFrame:
    def test_session_initialized(self):
        frame = event_to_frame(SessionInitialized(sdk_session_id="sdk-42"))
        assert frame["event"] == "session_initialized"
        assert json.loads(frame["data"]) == {"sdk_session_id": "sdk-42"}

    def test_text_delta(self):
        frame = event_to_frame(TextDelta(text="hello"))
        assert frame["event"] == "text_delta"
        assert json.loads(frame["data"]) == {"text": "hello"}

    def test_tool_call(self):
        frame = event_to_frame(
            ToolCall(name="berdl_query", input={"sql": "SELECT 1"}, tool_use_id="tu-7")
        )
        assert frame["event"] == "tool_call"
        data = json.loads(frame["data"])
        assert data == {
            "name": "berdl_query",
            "input": {"sql": "SELECT 1"},
            "tool_use_id": "tu-7",
        }

    def test_tool_result_ok(self):
        frame = event_to_frame(
            ToolResult(tool_use_id="tu-7", content="3 rows", is_error=False)
        )
        assert frame["event"] == "tool_result"
        assert json.loads(frame["data"]) == {
            "tool_use_id": "tu-7",
            "content": "3 rows",
            "is_error": False,
        }

    def test_tool_result_error(self):
        frame = event_to_frame(
            ToolResult(tool_use_id="tu-9", content="boom", is_error=True)
        )
        assert json.loads(frame["data"])["is_error"] is True

    def test_error_event(self):
        frame = event_to_frame(ErrorEvent(message="upstream 500"))
        assert frame["event"] == "error"
        assert json.loads(frame["data"]) == {"message": "upstream 500"}

    def test_turn_complete(self):
        frame = event_to_frame(TurnComplete(result_subtype="end_turn"))
        assert frame["event"] == "turn_complete"
        assert json.loads(frame["data"]) == {"result_subtype": "end_turn"}


class TestTurnCompleteFrame:
    def test_payload(self):
        frame = turn_complete_frame(assistant_message_id="msg-abc")
        assert frame["event"] == "turn_persisted"
        assert json.loads(frame["data"]) == {"assistant_message_id": "msg-abc"}

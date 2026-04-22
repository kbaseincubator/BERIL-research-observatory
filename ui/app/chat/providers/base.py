"""Provider abstraction for the chat feature.

Every provider emits a uniform :class:`TurnEvent` stream, regardless of the
underlying wire protocol or SDK. Route handlers consume this stream, persist
message rows, and (later) translate it into SSE frames for the browser.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Literal, Protocol, runtime_checkable

from app.chat.config import ProviderConfig


# ---------------------------------------------------------------------------
# Turn events
# ---------------------------------------------------------------------------


@dataclass
class SessionInitialized:
    """Emitted once per turn, early in the stream.

    Carries the provider-assigned ``sdk_session_id`` so the caller can
    persist it on :class:`ChatSession` for future resumes.
    """

    kind: Literal["session_initialized"] = "session_initialized"
    sdk_session_id: str = ""


@dataclass
class TextDelta:
    """A chunk of assistant text.

    Providers that only deliver complete messages (non-streaming SDKs) emit
    one :class:`TextDelta` per message; streaming providers emit many.
    """

    text: str
    kind: Literal["text_delta"] = "text_delta"


@dataclass
class ToolCall:
    """The model invoked a tool."""

    name: str
    input: dict[str, Any] = field(default_factory=dict)
    tool_use_id: str | None = None
    kind: Literal["tool_call"] = "tool_call"


@dataclass
class ToolResult:
    """The result returned by a tool invocation."""

    tool_use_id: str | None
    content: Any
    is_error: bool = False
    kind: Literal["tool_result"] = "tool_result"


@dataclass
class TurnComplete:
    """Final event of a successful turn."""

    kind: Literal["turn_complete"] = "turn_complete"
    result_subtype: str | None = None


@dataclass
class ErrorEvent:
    """Terminal event for a failed turn."""

    message: str
    kind: Literal["error"] = "error"


TurnEvent = (
    SessionInitialized | TextDelta | ToolCall | ToolResult | TurnComplete | ErrorEvent
)


# ---------------------------------------------------------------------------
# Credentials
# ---------------------------------------------------------------------------


@dataclass
class Credentials:
    """User-supplied credentials for a single turn.

    Keyed by the ``id`` of each :class:`~app.chat.config.CredentialField`
    declared on the provider. Values never leave per-request scope.
    """

    values: dict[str, str]

    def require(self, field_id: str) -> str:
        if field_id not in self.values or not self.values[field_id]:
            raise ValueError(f"missing credential {field_id!r}")
        return self.values[field_id]


# ---------------------------------------------------------------------------
# Provider protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class ChatProvider(Protocol):
    """Async generator of :class:`TurnEvent` for one chat turn."""

    provider_id: str
    config: ProviderConfig

    def run_turn(
        self,
        *,
        user_message: str,
        credentials: Credentials,
        model: str,
        cwd: str,
        sdk_session_id: str | None,
    ) -> AsyncIterator[TurnEvent]:
        """Run a single chat turn and yield events as they happen.

        Implementations must yield a :class:`SessionInitialized` event once
        the provider reports a session id, and a terminal
        :class:`TurnComplete` or :class:`ErrorEvent` exactly once.
        """
        ...

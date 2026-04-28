"""Chat turn service: drives one turn end-to-end.

Responsibilities:
  * Persist the user's message before calling the provider (so it survives a
    crash mid-turn and is visible in the transcript on resume).
  * Run the provider and collect events.
  * Persist a single assistant message (aggregating text deltas + tool calls)
    when the turn finishes.
  * Record the ``sdk_session_id`` on first completion so subsequent turns
    resume correctly.
  * Update ``last_active_at`` so the session list can sort by recency.

This layer is provider-agnostic and streaming-agnostic.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.chat.crud import list_messages_for_session
from app.chat.providers import get_provider
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
from app.chat.sdk_sessions import build_resume_preamble, session_file_exists
from app.config import get_settings
from app.db.models import ChatMessage, ChatSession

logger = logging.getLogger(__name__)


async def persist_user_message(
    db: AsyncSession, *, session: ChatSession, user_message: str
) -> ChatMessage:
    """Write the user's message and commit. Called before provider dispatch."""
    row = ChatMessage(
        session_id=session.id, role="user", content={"text": user_message}
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def persist_assistant_message(
    db: AsyncSession,
    *,
    session: ChatSession,
    result: "TurnResult",
) -> ChatMessage:
    """Write the assistant's message, update session state, commit."""
    row = ChatMessage(
        session_id=session.id,
        role="assistant",
        content={
            "text": result.assistant_text,
            "tool_activity": result.tool_activity,
            "error": result.error,
        },
    )
    db.add(row)
    if result.sdk_session_id and not session.sdk_session_id:
        session.sdk_session_id = result.sdk_session_id
    session.last_active_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(row)
    return row


@dataclass
class TurnResult:
    """Outcome of one completed turn. Callers returning JSON use this."""

    assistant_text: str = ""
    tool_activity: list[dict[str, Any]] = field(default_factory=list)
    sdk_session_id: str | None = None
    error: str | None = None

    @property
    def is_error(self) -> bool:
        return self.error is not None


async def run_turn(
    db: AsyncSession,
    *,
    session: ChatSession,
    user_message: str,
    credentials: Credentials,
) -> TurnResult:
    """Run one chat turn to completion and persist messages.

    The session row is expected to be owned by the caller; auth happens at
    the route layer. This function does not validate ownership.
    """
    await persist_user_message(db, session=session, user_message=user_message)

    result = TurnResult()
    text_parts: list[str] = []

    async for event in run_provider_turn(
        db=db,
        session=session,
        user_message=user_message,
        credentials=credentials,
    ):
        fold_event(event, text_parts, result)

    result.assistant_text = "".join(text_parts)
    await persist_assistant_message(db, session=session, result=result)
    return result


async def run_provider_turn(
    *,
    db: AsyncSession,
    session: ChatSession,
    user_message: str,
    credentials: Credentials,
) -> AsyncIterator[TurnEvent]:
    """Resolve the provider and stream its events. No persistence.

    Exposed separately so the streaming endpoint can consume the event
    stream directly while still sharing provider resolution.

    If ``session.sdk_session_id`` points to a transcript the SDK can no
    longer find on disk (volume wiped, different replica, etc.), we clear
    the stale handle and cold-start the SDK with a reconstructed preamble
    of prior DB-stored messages so the user doesn't lose context.
    """
    provider = get_provider(session.provider_id)
    cwd = str(get_settings().repo_dir)

    resume_id: str | None = session.sdk_session_id
    outbound_message = user_message
    if resume_id and not session_file_exists(cwd, resume_id):
        logger.warning(
            "SDK transcript missing for session %s (sdk_session_id=%s); cold-starting with DB preamble",
            session.id,
            resume_id,
        )
        prior = await list_messages_for_session(db, session.id)
        # Drop the just-persisted user message — it's already in
        # ``user_message`` and will be sent as the live prompt.
        preamble_sources = [m for m in prior if m.content != {"text": user_message}]
        preamble = build_resume_preamble(preamble_sources)
        outbound_message = preamble + user_message
        resume_id = None
        # Clear the stale handle so persist_assistant_message accepts the
        # new session ID emitted by the cold-started SDK run.
        session.sdk_session_id = None

    async for event in provider.run_turn(
        user_message=outbound_message,
        credentials=credentials,
        model=session.model,
        cwd=cwd,
        sdk_session_id=resume_id,
    ):
        yield event


def fold_event(event: TurnEvent, text_parts: list[str], result: TurnResult) -> None:
    """Accumulate a provider event into the in-progress TurnResult."""
    if isinstance(event, SessionInitialized):
        result.sdk_session_id = event.sdk_session_id
    elif isinstance(event, TextDelta):
        text_parts.append(event.text)
    elif isinstance(event, ToolCall):
        result.tool_activity.append(
            {
                "type": "tool_call",
                "name": event.name,
                "input": event.input,
                "tool_use_id": event.tool_use_id,
            }
        )
    elif isinstance(event, ToolResult):
        result.tool_activity.append(
            {
                "type": "tool_result",
                "tool_use_id": event.tool_use_id,
                "content": event.content,
                "is_error": event.is_error,
            }
        )
    elif isinstance(event, ErrorEvent):
        result.error = event.message
    elif isinstance(event, TurnComplete):
        pass  # terminal sentinel; nothing to fold

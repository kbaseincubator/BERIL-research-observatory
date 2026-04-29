"""Database access helpers for chat sessions and messages.

Mirrors the style of :mod:`app.db.crud` but scoped to the chat feature.
Route handlers import from here; the service layer talks to models directly
because it's tightly coupled to the turn lifecycle.

Currently this file holds only the read helper the service layer needs to
reconstruct prior context when an SDK transcript file goes missing. The
session CRUD helpers used by the management UI land in a later PR.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ChatMessage


async def list_messages_for_session(
    db: AsyncSession, session_id: str
) -> list[ChatMessage]:
    """Return all messages for ``session_id`` in chronological order."""
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    return list(result.scalars())

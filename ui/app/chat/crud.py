"""Database access helpers for chat sessions and messages.

Mirrors the style of :mod:`app.db.crud` but scoped to the chat feature.
Route handlers import from here; the service layer talks to models directly
because it's tightly coupled to the turn lifecycle.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import ChatMessage, ChatSession


async def get_session_for_user(
    db: AsyncSession, session_id: str, user_id: str
) -> ChatSession | None:
    """Return the session iff it exists AND belongs to the given user."""
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()
    if session is None or session.owner_id != user_id:
        return None
    return session


async def list_sessions_for_user(
    db: AsyncSession, user_id: str, *, include_archived: bool = False
) -> list[ChatSession]:
    """Return all sessions owned by ``user_id``, newest first."""
    stmt = (
        select(ChatSession)
        .where(ChatSession.owner_id == user_id)
        .order_by(ChatSession.last_active_at.desc())
    )
    if not include_archived:
        stmt = stmt.where(ChatSession.archived.is_(False))
    result = await db.execute(stmt)
    return list(result.scalars())


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


async def create_session(
    db: AsyncSession,
    *,
    owner_id: str,
    provider_id: str,
    model: str,
    title: str = "New chat",
) -> ChatSession:
    session = ChatSession(
        owner_id=owner_id,
        provider_id=provider_id,
        model=model,
        title=title,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def update_session(
    db: AsyncSession,
    session: ChatSession,
    *,
    title: str | None = None,
    archived: bool | None = None,
) -> ChatSession:
    if title is not None:
        session.title = title
    if archived is not None:
        session.archived = archived
    await db.commit()
    await db.refresh(session)
    return session


async def delete_session(db: AsyncSession, session: ChatSession) -> None:
    await db.delete(session)
    await db.commit()


async def get_session_with_messages(
    db: AsyncSession, session_id: str
) -> ChatSession | None:
    """Fetch session + eager-load its messages. Used by the session page."""
    result = await db.execute(
        select(ChatSession)
        .options(selectinload(ChatSession.messages))
        .where(ChatSession.id == session_id)
    )
    return result.scalar_one_or_none()

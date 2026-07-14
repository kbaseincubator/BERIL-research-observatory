"""Tests for ChatSession and ChatMessage ORM models."""

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.db.models import BerilUser, ChatMessage, ChatSession, UserProject


async def _make_user(db_session, orcid="0000-0001-1111-0001"):
    user = BerilUser(orcid_id=orcid, display_name="Test User")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def _make_project(db_session, owner, slug="p"):
    project = UserProject(owner_id=owner.id, slug=slug, title="Test Project")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


class TestChatSessionBasic:
    async def test_create_minimal(self, db_session):
        user = await _make_user(db_session)
        session = ChatSession(
            owner_id=user.id,
            provider_id="anthropic",
            model="claude-opus-4-7",
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        assert session.id is not None
        assert len(session.id) == 36
        assert session.provider_id == "anthropic"
        assert session.model == "claude-opus-4-7"
        assert session.title == "New chat"
        assert session.archived is False
        assert session.sdk_session_id is None
        assert session.project_id is None
        assert session.created_at is not None
        assert session.last_active_at is not None

    async def test_create_with_full_fields(self, db_session):
        user = await _make_user(db_session)
        project = await _make_project(db_session, user)
        session = ChatSession(
            owner_id=user.id,
            provider_id="cborg",
            model="anthropic/claude-opus",
            title="Investigating gene clusters",
            sdk_session_id="sdk-abc-123",
            project_id=project.id,
            archived=False,
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        assert session.title == "Investigating gene clusters"
        assert session.sdk_session_id == "sdk-abc-123"
        assert session.project_id == project.id

    async def test_provider_id_is_free_form_string(self, db_session):
        """Adding a new provider shouldn't require a migration."""
        user = await _make_user(db_session)
        session = ChatSession(
            owner_id=user.id,
            provider_id="a-provider-that-doesnt-exist-yet",
            model="some-model",
        )
        db_session.add(session)
        await db_session.commit()  # no enum constraint; accepted

    async def test_owner_required(self, db_session):
        session = ChatSession(
            provider_id="anthropic",
            model="claude-opus-4-7",
        )
        db_session.add(session)
        with pytest.raises(IntegrityError):
            await db_session.commit()


class TestChatSessionRelations:
    async def test_owner_relationship(self, db_session):
        user = await _make_user(db_session)
        session = ChatSession(
            owner_id=user.id, provider_id="anthropic", model="claude-opus-4-7"
        )
        db_session.add(session)
        await db_session.commit()

        result = await db_session.execute(
            select(BerilUser).options(selectinload(BerilUser.chat_sessions)).where(BerilUser.id == user.id)
        )
        loaded = result.scalar_one()
        assert len(loaded.chat_sessions) == 1
        assert loaded.chat_sessions[0].id == session.id

    async def test_cascade_delete_user_removes_sessions(self, db_session):
        user = await _make_user(db_session)
        session = ChatSession(
            owner_id=user.id, provider_id="anthropic", model="claude-opus-4-7"
        )
        db_session.add(session)
        await db_session.commit()
        session_id = session.id

        await db_session.delete(user)
        await db_session.commit()

        result = await db_session.execute(select(ChatSession).where(ChatSession.id == session_id))
        assert result.scalar_one_or_none() is None

    async def test_project_delete_sets_null(self, db_session):
        user = await _make_user(db_session)
        project = await _make_project(db_session, user)
        session = ChatSession(
            owner_id=user.id,
            provider_id="anthropic",
            model="claude-opus-4-7",
            project_id=project.id,
        )
        db_session.add(session)
        await db_session.commit()

        await db_session.delete(project)
        await db_session.commit()
        await db_session.refresh(session)

        assert session.project_id is None


class TestChatMessage:
    async def _session(self, db_session):
        user = await _make_user(db_session)
        session = ChatSession(
            owner_id=user.id, provider_id="anthropic", model="claude-opus-4-7"
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)
        return session

    async def test_create_user_message(self, db_session):
        session = await self._session(db_session)
        msg = ChatMessage(
            session_id=session.id,
            role="user",
            content={"text": "What is the genome size of E. coli?"},
        )
        db_session.add(msg)
        await db_session.commit()
        await db_session.refresh(msg)

        assert msg.id is not None
        assert msg.role == "user"
        assert msg.content == {"text": "What is the genome size of E. coli?"}

    async def test_create_assistant_message_with_structured_content(self, db_session):
        """Tool calls live inside content as structured JSON."""
        session = await self._session(db_session)
        msg = ChatMessage(
            session_id=session.id,
            role="assistant",
            content={
                "text": "Let me check.",
                "tool_calls": [{"name": "berdl_query", "input": {"sql": "SELECT 1"}}],
            },
        )
        db_session.add(msg)
        await db_session.commit()
        await db_session.refresh(msg)

        assert msg.content["tool_calls"][0]["name"] == "berdl_query"

    async def test_messages_ordered_by_created_at(self, db_session):
        session = await self._session(db_session)
        from datetime import datetime, timedelta, timezone

        base = datetime.now(timezone.utc)
        msgs = [
            ChatMessage(
                session_id=session.id,
                role="user",
                content={"text": f"msg-{i}"},
                created_at=base + timedelta(seconds=i),
            )
            for i in range(3)
        ]
        db_session.add_all(msgs)
        await db_session.commit()

        result = await db_session.execute(
            select(ChatSession)
            .options(selectinload(ChatSession.messages))
            .where(ChatSession.id == session.id)
        )
        loaded = result.scalar_one()
        texts = [m.content["text"] for m in loaded.messages]
        assert texts == ["msg-0", "msg-1", "msg-2"]

    async def test_cascade_delete_session_removes_messages(self, db_session):
        session = await self._session(db_session)
        msg = ChatMessage(session_id=session.id, role="user", content={"text": "hi"})
        db_session.add(msg)
        await db_session.commit()
        msg_id = msg.id

        await db_session.delete(session)
        await db_session.commit()

        result = await db_session.execute(select(ChatMessage).where(ChatMessage.id == msg_id))
        assert result.scalar_one_or_none() is None

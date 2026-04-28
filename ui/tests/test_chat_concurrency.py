"""Tests for the ChatConcurrencyManager."""

from __future__ import annotations

import asyncio

import pytest

from app.chat.concurrency import ChatConcurrencyManager, UserCapExceeded


class TestSessionLock:
    async def test_same_session_serializes(self):
        mgr = ChatConcurrencyManager(per_user_cap=10)
        order: list[str] = []

        async def turn(tag: str, hold: float) -> None:
            async with mgr.acquire(session_id="s1", user_id="u1"):
                order.append(f"enter-{tag}")
                await asyncio.sleep(hold)
                order.append(f"exit-{tag}")

        await asyncio.gather(turn("a", 0.02), turn("b", 0.01))

        # Second entry must wait for the first to exit — no interleaving.
        assert order.index("exit-a") < order.index("enter-b") or order.index(
            "exit-b"
        ) < order.index("enter-a")

    async def test_different_sessions_parallel(self):
        mgr = ChatConcurrencyManager(per_user_cap=10)
        events: list[str] = []

        async def turn(sess: str) -> None:
            async with mgr.acquire(session_id=sess, user_id="u1"):
                events.append(f"enter-{sess}")
                await asyncio.sleep(0.01)
                events.append(f"exit-{sess}")

        await asyncio.gather(turn("s1"), turn("s2"))

        # Both should have entered before either exited.
        entered = [e for e in events if e.startswith("enter-")]
        assert len(entered) == 2
        first_exit = next(i for i, e in enumerate(events) if e.startswith("exit-"))
        assert events[first_exit - 1].startswith("enter-")
        assert events[first_exit - 2].startswith("enter-")


class TestUserCap:
    async def test_cap_blocks_third_turn(self):
        mgr = ChatConcurrencyManager(per_user_cap=2)
        release = asyncio.Event()

        async def held_turn(sess: str) -> None:
            async with mgr.acquire(session_id=sess, user_id="u1"):
                await release.wait()

        t1 = asyncio.create_task(held_turn("s1"))
        t2 = asyncio.create_task(held_turn("s2"))
        # Give the tasks a moment to acquire.
        await asyncio.sleep(0.01)
        assert mgr.active_turns_for("u1") == 2

        with pytest.raises(UserCapExceeded):
            async with mgr.acquire(session_id="s3", user_id="u1"):
                pass

        release.set()
        await asyncio.gather(t1, t2)
        assert mgr.active_turns_for("u1") == 0

    async def test_slot_released_on_exception(self):
        mgr = ChatConcurrencyManager(per_user_cap=1)
        with pytest.raises(RuntimeError):
            async with mgr.acquire(session_id="s1", user_id="u1"):
                raise RuntimeError("boom")
        assert mgr.active_turns_for("u1") == 0

        # Can acquire again immediately afterward.
        async with mgr.acquire(session_id="s1", user_id="u1"):
            pass

    async def test_different_users_independent(self):
        mgr = ChatConcurrencyManager(per_user_cap=1)
        release = asyncio.Event()

        async def held(user: str) -> None:
            async with mgr.acquire(session_id="s", user_id=user):
                await release.wait()

        t1 = asyncio.create_task(held("u1"))
        t2 = asyncio.create_task(held("u2"))
        await asyncio.sleep(0.01)
        assert mgr.active_turns_for("u1") == 1
        assert mgr.active_turns_for("u2") == 1
        release.set()
        await asyncio.gather(t1, t2)

    async def test_invalid_cap_rejected(self):
        with pytest.raises(ValueError):
            ChatConcurrencyManager(per_user_cap=0)

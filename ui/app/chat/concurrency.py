"""Per-session and per-user concurrency control for chat turns.

Two guarantees:

1. **One active turn per session.** The underlying Agent SDK session is
   stateful; two concurrent turns would race on the same ``sdk_session_id``
   and corrupt the conversation. Enforced with a per-session :class:`asyncio.Lock`.

2. **Bounded parallelism per user.** A user running many tabs can still run
   turns in parallel across their sessions, but not unbounded. Enforced with
   a per-user :class:`asyncio.Semaphore` sized from
   ``settings.chat_max_concurrent_turns_per_user``.

The manager is process-local. If this app ever runs multi-worker, these
guarantees collapse to per-worker; upgrade to a Redis lock or move turns
onto a single background worker.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator

from app.config import get_settings


class UserChatConcurrencyExceeded(Exception):
    """Raised when the per-user concurrent-turn cap would be exceeded."""


class ChatConcurrencyManager:
    def __init__(self, *, per_user_cap: int) -> None:
        if per_user_cap < 1:
            raise ValueError("per_user_cap must be >= 1")
        self._per_user_cap = per_user_cap
        self._session_locks: dict[str, asyncio.Lock] = {}
        # user_id -> current count of active turns. Incremented atomically
        # under _registry_lock; decremented after the turn finishes. Using a
        # plain counter (rather than asyncio.Semaphore) lets us fail fast
        # when the cap is exceeded instead of queueing the caller.
        self._user_active: dict[str, int] = {}
        self._registry_lock = asyncio.Lock()

    async def _get_session_lock(self, session_id: str) -> asyncio.Lock:
        async with self._registry_lock:
            lock = self._session_locks.get(session_id)
            if lock is None:
                lock = asyncio.Lock()
                self._session_locks[session_id] = lock
            return lock

    async def _try_reserve_user_slot(self, user_id: str) -> bool:
        async with self._registry_lock:
            active = self._user_active.get(user_id, 0)
            if active >= self._per_user_cap:
                return False
            self._user_active[user_id] = active + 1
            return True

    async def _release_user_slot(self, user_id: str) -> None:
        async with self._registry_lock:
            active = self._user_active.get(user_id, 0)
            if active <= 1:
                self._user_active.pop(user_id, None)
            else:
                self._user_active[user_id] = active - 1

    def active_turns_for(self, user_id: str) -> int:
        """Introspection for tests and debugging."""
        return self._user_active.get(user_id, 0)

    @asynccontextmanager
    async def acquire(self, *, session_id: str, user_id: str) -> AsyncIterator[None]:
        """Acquire both the user-cap and session-lock for one turn.

        Non-blocking on the user cap: if the cap is already exhausted,
        raises :class:`UserChatConcurrencyExceeded` immediately rather than queueing the
        caller. This lets the route return 429 to the browser quickly.

        Blocks on the session lock. Two turns in the same chat will serialize.
        """
        lock = await self._get_session_lock(session_id)
        async with lock:
            reserved = await self._try_reserve_user_slot(user_id)
            if not reserved:
                raise UserChatConcurrencyExceeded(
                    f"user {user_id!r} has reached the concurrent-turn cap"
                )
            try:
                yield
            finally:
                await self._release_user_slot(user_id)


_manager: ChatConcurrencyManager | None = None


def get_concurrency_manager() -> ChatConcurrencyManager:
    global _manager
    if _manager is None:
        cap = get_settings().chat_max_concurrent_turns_per_user
        _manager = ChatConcurrencyManager(per_user_cap=cap)
    return _manager


def reset_concurrency_manager() -> None:
    """Used for tests only."""
    global _manager
    _manager = None

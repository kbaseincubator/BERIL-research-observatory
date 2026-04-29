"""Chat routes.

Exposes non-streaming turn execution. A streaming (SSE) endpoint is
layered on top in a later PR and shares the same service layer.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user_session_or_token
from app.chat.concurrency import UserChatConcurrencyExceeded, get_concurrency_manager
from app.chat.providers import get_provider
from app.chat.providers.base import Credentials
from app.chat.service import run_turn
from app.db.models import ChatSession
from app.db.session import get_db

logger = logging.getLogger(__name__)

ROUTER_CHAT = APIRouter(prefix="/api/chat", tags=["Chat"])


class TurnRequest(BaseModel):
    """JSON body for POST /api/chat/{session_id}/turn."""

    message: str = Field(min_length=1)
    # Credentials: {credential_field_id: value}. Keys must match the provider
    # config's credential_fields[*].id (e.g. "api_key"). Never logged.
    credentials: dict[str, str] = Field(default_factory=dict)


def _validate_credentials(provider_id: str, provided: dict[str, str]) -> Credentials:
    provider = get_provider(provider_id)
    missing = [
        f.id for f in provider.config.credential_fields if not provided.get(f.id)
    ]
    if missing:
        raise ValueError(f"missing credentials: {', '.join(missing)}")
    return Credentials(values=provided)


async def _load_session_for_user(
    db: AsyncSession, session_id: str, user_id: str
) -> tuple[ChatSession | None, int | None]:
    """Return (session, None) on success, or (None, http_status_code) on auth failure."""
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()
    if session is None:
        return None, 404
    if session.owner_id != user_id:
        return None, 403
    return session, None


@ROUTER_CHAT.post("/{session_id}/turn")
async def chat_turn(
    session_id: str,
    body: TurnRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Run one chat turn to completion and return the assistant's response.

    Non-streaming. Returns JSON on both success and provider error. The
    streaming variant (a later PR) will live at ``.../stream``.
    """
    user = await get_current_user_session_or_token(request, db)
    if user is None:
        return Response(status_code=401)

    session, err = await _load_session_for_user(db, session_id, user.id)
    if err is not None or session is None:
        return Response(status_code=err)

    try:
        credentials = _validate_credentials(session.provider_id, body.credentials)
    except (KeyError, ValueError) as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)

    manager = get_concurrency_manager()
    try:
        async with manager.acquire(session_id=session.id, user_id=user.id):
            turn = await run_turn(
                db,
                session=session,
                user_message=body.message,
                credentials=credentials,
            )
    except UserChatConcurrencyExceeded:
        return JSONResponse(
            {"error": "concurrent-turn cap exceeded for this user"},
            status_code=429,
        )

    payload: dict[str, Any] = {
        "session_id": session.id,
        "assistant_text": turn.assistant_text,
        "tool_activity": turn.tool_activity,
    }
    if turn.is_error:
        payload["error"] = turn.error
    return JSONResponse(payload)

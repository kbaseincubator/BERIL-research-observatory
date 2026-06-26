"""ORCiD OAuth2 authentication helpers for the BERIL Research Observatory."""

from dataclasses import dataclass

from app.db.crud import get_user_by_api_token, get_user_by_orcid
from app.db.models import BerilUser
from app.db.session import get_db
from fastapi import Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class OrcidUser:
    """Authenticated user from ORCiD."""

    orcid_id: str
    name: str | None = None
    access_token: str | None = None

    @property
    def orcid_url(self) -> str:
        return f"https://orcid.org/{self.orcid_id}"


def get_current_session_user(request: Request) -> OrcidUser | None:
    """Return the logged-in user from the session, or None if not logged in."""
    orcid_id = request.session.get("orcid_id")
    if not orcid_id:
        return None
    return OrcidUser(
        orcid_id=orcid_id,
        name=request.session.get("orcid_name"),
        access_token=request.session.get("orcid_access_token"),
    )


def get_beril_user_id(request: Request) -> str | None:
    """Return the internal BerilUser UUID from the session, or None."""
    return request.session.get("beril_user_id")


async def get_current_user_session_or_token(
    request: Request, db: AsyncSession
) -> "BerilUser | None":
    """Authenticate via session cookie or Authorization: Bearer token.

    Tries the session first (cheaper, no DB hit). Falls back to the Bearer
    token in the Authorization header, which requires a DB lookup.
    Returns the BerilUser ORM object, or None if neither method succeeds.
    """
    # Session path — only trust it if the orcid_id still resolves in the DB
    orcid_id = request.session.get("orcid_id")
    if orcid_id:
        user = await get_user_by_orcid(db, orcid_id)
        if user is not None:
            return user

    # Bearer token path — scheme is case-insensitive per HTTP spec
    auth_header = request.headers.get("Authorization", "")
    if auth_header.lower().startswith("bearer "):
        raw_token = auth_header[len("bearer "):]
        return await get_user_by_api_token(db, raw_token)

    return None


class _RedirectToLogin(HTTPException):
    """Raised by ``require_user_page`` to bounce anonymous visitors to login.

    Carries no detail body — the registered exception handler turns it into a
    302 redirect to ``/auth/login?next=<original path>``.
    """

    def __init__(self, next_url: str) -> None:
        super().__init__(status_code=status.HTTP_302_FOUND)
        self.next_url = next_url


async def require_user_page(
    request: Request, db: AsyncSession = Depends(get_db)
) -> BerilUser:
    """Dependency for HTML routes: yield the BerilUser or redirect to login.

    On failure raises ``_RedirectToLogin``, which the app's exception handler
    converts into a 302 to ``/auth/login?next=<current path>``. Routes that
    depend on this are guaranteed a non-None ``BerilUser``.
    """
    user = await get_current_user_session_or_token(request, db)
    if user is None:
        raise _RedirectToLogin(next_url=request.url.path)
    return user


async def require_user_api(
    request: Request, db: AsyncSession = Depends(get_db)
) -> BerilUser:
    """Dependency for API routes: yield the BerilUser or raise 401.

    Routes that depend on this are guaranteed a non-None ``BerilUser``.
    """
    user = await get_current_user_session_or_token(request, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return user


def redirect_to_login_handler(request: Request, exc: _RedirectToLogin) -> RedirectResponse:
    """Exception handler that turns ``_RedirectToLogin`` into a 302 redirect."""
    return RedirectResponse(url=f"/auth/login?next={exc.next_url}", status_code=302)

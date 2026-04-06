"""ORCiD OAuth2 authentication helpers for the BERIL Research Observatory."""

from dataclasses import dataclass

from fastapi import Request
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


def get_current_user(request: Request) -> OrcidUser | None:
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


async def get_current_user_or_token(
    request: Request, db: AsyncSession
) -> "BerilUser | None":
    """Authenticate via session cookie or Authorization: Bearer token.

    Tries the session first (cheaper, no DB hit). Falls back to the Bearer
    token in the Authorization header, which requires a DB lookup.
    Returns the BerilUser ORM object, or None if neither method succeeds.
    """
    from app.db.crud import get_user_by_api_token, get_user_by_orcid

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

"""ORCiD OAuth2 authentication helpers for the BERIL Research Observatory."""

from dataclasses import dataclass

from fastapi import Request


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

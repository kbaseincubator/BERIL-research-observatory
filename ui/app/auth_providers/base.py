"""Provider protocols.

Two roles:

- ``IdentityProvider`` runs a login flow and owns the ``BerilUser`` row. Exactly
  one is active (ORCiD).
- ``TokenProvider`` exposes a per-request credential for calling an external
  service. Stateless — re-read on every request so revocation upstream is
  immediate. Zero or more enabled.
"""

from typing import Protocol

from fastapi import FastAPI, Request

from app.auth import OrcidUser


class IdentityProvider(Protocol):
    name: str

    def install_routes(self, app: FastAPI) -> None:
        """Mount the provider's login/callback/logout routes on the app."""
        ...

    def get_session_user(self, request: Request) -> OrcidUser | None:
        """Return the logged-in user from the session, or None."""
        ...


class TokenProvider(Protocol):
    name: str

    def get_token(self, request: Request) -> str | None:
        """Return the credential for this request, or None if unavailable."""
        ...

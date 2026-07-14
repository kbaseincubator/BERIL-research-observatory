"""ORCiD identity provider.

Wraps the existing ORCiD OAuth2 routes (defined in app.routes.auth) under the
provider interface. ORCiD is the sole identity provider: every BerilUser row
keys on an orcid_id.
"""

from fastapi import FastAPI, Request

from app.auth import OrcidUser, get_current_session_user
from app.config import Settings
from app.routes.auth import ROUTER_AUTH


class OrcidProvider:
    name = "orcid"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def install_routes(self, app: FastAPI) -> None:
        app.include_router(ROUTER_AUTH)

    def get_session_user(self, request: Request) -> OrcidUser | None:
        return get_current_session_user(request)

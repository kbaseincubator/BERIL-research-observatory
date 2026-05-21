"""KBase token provider.

Reads the KBase auth token off the incoming request's cookies on every call.
The cookie is set by the KBase auth UI on a parent ``*.kbase.us`` domain and
shared with this app when it's deployed there. The cookie name is configurable
via ``BERIL_KBASE_AUTH_COOKIE``.

This provider does NOT create a BerilUser. KBase identity is intentionally
decoupled from ORCiD identity: the user logs in via ORCiD, and KBase just
supplies a token for downstream service calls (to K-BERDL or other related
services) when the cookie is present.
"""

from fastapi import Request

from app.config import Settings


class KBaseTokenProvider:
    name = "kbase"

    def __init__(self, settings: Settings) -> None:
        self._cookie_name = settings.kbase_auth_cookie

    def get_token(self, request: Request) -> str | None:
        token = request.cookies.get(self._cookie_name)
        return token or None

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
from datetime import datetime
import logging
from app.config import Settings
from kbase.auth import AsyncKBaseAuthClient, InvalidTokenError
from kbase._auth.models import MFAStatus

logger = logging.getLogger(__name__)
class KBaseTokenProvider:
    name = "kbase"

    def __init__(self, settings: Settings) -> None:
        self._cookie_name = settings.kbase_auth_cookie
        self._auth_url = settings.kbase_auth_url
        self._require_mfa = settings.kbase_auth_mfa

    async def get_token(self, request: Request) -> str | None:
        token = request.cookies.get(self._cookie_name)
        if not token:
            return None
        is_valid = await self._validate_token(token)
        if is_valid:
            return token
        return None

    async def _validate_token(self, token: str) -> bool:
        if not token:
            return False
        try:
            async with await AsyncKBaseAuthClient.create(self._auth_url) as cli:
                token_info = await cli.get_token(token)
                if self._require_mfa and token_info.mfa != MFAStatus.USED:
                    logger.warning(f"Attempted login with KBase token without MFA enabled - user {token_info.user}")
                    return False
                if token_info.expires > datetime.now().timestamp() * 1000:
                    logger.info(f"KBase login detected - user {token_info.user}")
                    return True
                return False
        except InvalidTokenError:
            logger.warning("Attempted login with invalid KBase token")
            return False

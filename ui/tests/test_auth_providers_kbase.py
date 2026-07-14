"""Unit tests for the KBase auth token provider.

KBaseTokenProvider is intentionally tiny: read a cookie, validate the token via
the KBase auth service, return it or None. These tests pin down each branch
without standing up a FastAPI app — the provider only needs a request-like
object with a ``cookies`` dict and the KBase auth client mocked at the import
site (``app.auth_providers.kbase``).
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from kbase.auth import InvalidTokenError
from kbase._auth.models import MFAStatus

from app.auth_providers.kbase import KBaseTokenProvider


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@dataclass
class _SettingsStub:
    """Minimal Settings shape KBaseTokenProvider reads."""
    kbase_auth_cookie: str = "kbase_session_backup"
    kbase_auth_url: str = "https://example.invalid/services/auth"
    kbase_auth_mfa: bool = True


def _fake_request(cookies: dict | None = None) -> SimpleNamespace:
    """Build a stand-in for fastapi.Request — only .cookies is read."""
    return SimpleNamespace(cookies=cookies or {})


def _future_ms(seconds: int = 3600) -> float:
    """KBase expires field is milliseconds since epoch."""
    return (datetime.now() + timedelta(seconds=seconds)).timestamp() * 1000


def _past_ms(seconds: int = 3600) -> float:
    return (datetime.now() - timedelta(seconds=seconds)).timestamp() * 1000


def _mock_token_info(mfa: MFAStatus = MFAStatus.USED, expires: float | None = None,
                     user: str = "alice") -> MagicMock:
    info = MagicMock()
    info.mfa = mfa
    info.expires = expires if expires is not None else _future_ms()
    info.user = user
    return info


def _patch_client(token_info: MagicMock | None = None,
                  raise_invalid: bool = False) -> patch:
    """Patch AsyncKBaseAuthClient.create to yield an async-context-managed
    client whose .get_token returns ``token_info`` (or raises InvalidTokenError).
    Mirrors the ``async with await AsyncKBaseAuthClient.create(...) as cli``
    shape the provider uses."""
    cli = MagicMock()
    if raise_invalid:
        cli.get_token = AsyncMock(side_effect=InvalidTokenError("bad token"))
    else:
        cli.get_token = AsyncMock(return_value=token_info)

    # The provider does `async with await Client.create(url) as cli`.
    # create(...) is awaited to get an async context manager, then `async with`
    # awaits __aenter__/__aexit__. So create must be an AsyncMock returning an
    # object with __aenter__/__aexit__.
    ctx_manager = MagicMock()
    ctx_manager.__aenter__ = AsyncMock(return_value=cli)
    ctx_manager.__aexit__ = AsyncMock(return_value=False)

    return patch(
        "app.auth_providers.kbase.AsyncKBaseAuthClient.create",
        new=AsyncMock(return_value=ctx_manager),
    )


# ---------------------------------------------------------------------------
# Cookie-absent path
# ---------------------------------------------------------------------------


class TestNoCookie:
    @pytest.mark.asyncio
    async def test_returns_none_when_cookie_missing(self):
        """No cookie present → no network call, returns None.

        The validator is wrapped in a patch that would explode if invoked, to
        prove we short-circuit before talking to KBase.
        """
        provider = KBaseTokenProvider(_SettingsStub())
        with patch(
            "app.auth_providers.kbase.AsyncKBaseAuthClient.create",
            side_effect=AssertionError("must not call KBase when no cookie"),
        ):
            assert await provider.get_token(_fake_request({})) is None

    @pytest.mark.asyncio
    async def test_returns_none_when_cookie_empty_string(self):
        """Empty-string cookie short-circuits to None without hitting KBase."""
        provider = KBaseTokenProvider(_SettingsStub())
        with patch(
            "app.auth_providers.kbase.AsyncKBaseAuthClient.create",
            side_effect=AssertionError("must not call KBase for empty cookie"),
        ):
            assert await provider.get_token(_fake_request({"kbase_session_backup": ""})) is None


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


class TestValidToken:
    @pytest.mark.asyncio
    async def test_returns_token_when_mfa_used_and_not_expired(self):
        provider = KBaseTokenProvider(_SettingsStub())
        token_info = _mock_token_info(mfa=MFAStatus.USED, expires=_future_ms())
        with _patch_client(token_info=token_info):
            result = await provider.get_token(_fake_request({"kbase_session_backup": "tok-abc"}))
        assert result == "tok-abc"

    @pytest.mark.asyncio
    async def test_validator_called_with_cookie_value(self):
        """The token from the cookie is the one sent to KBase for validation."""
        provider = KBaseTokenProvider(_SettingsStub())
        token_info = _mock_token_info()

        cli = MagicMock()
        cli.get_token = AsyncMock(return_value=token_info)
        ctx_manager = MagicMock()
        ctx_manager.__aenter__ = AsyncMock(return_value=cli)
        ctx_manager.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "app.auth_providers.kbase.AsyncKBaseAuthClient.create",
            new=AsyncMock(return_value=ctx_manager),
        ) as create_mock:
            await provider.get_token(_fake_request({"kbase_session_backup": "exact-token"}))

        create_mock.assert_awaited_once_with("https://example.invalid/services/auth")
        cli.get_token.assert_awaited_once_with("exact-token")


# ---------------------------------------------------------------------------
# Rejection paths
# ---------------------------------------------------------------------------


class TestRejection:
    @pytest.mark.asyncio
    async def test_rejects_when_mfa_required_but_not_used(self):
        provider = KBaseTokenProvider(_SettingsStub(kbase_auth_mfa=True))
        token_info = _mock_token_info(mfa=MFAStatus.NOT_USED)
        with _patch_client(token_info=token_info):
            assert await provider.get_token(_fake_request({"kbase_session_backup": "t"})) is None

    @pytest.mark.asyncio
    async def test_rejects_when_mfa_required_and_status_unknown(self):
        provider = KBaseTokenProvider(_SettingsStub(kbase_auth_mfa=True))
        token_info = _mock_token_info(mfa=MFAStatus.UNKNOWN)
        with _patch_client(token_info=token_info):
            assert await provider.get_token(_fake_request({"kbase_session_backup": "t"})) is None

    @pytest.mark.asyncio
    async def test_rejects_when_token_expired(self):
        provider = KBaseTokenProvider(_SettingsStub())
        token_info = _mock_token_info(mfa=MFAStatus.USED, expires=_past_ms())
        with _patch_client(token_info=token_info):
            assert await provider.get_token(_fake_request({"kbase_session_backup": "t"})) is None

    @pytest.mark.asyncio
    async def test_returns_none_on_invalid_token_error(self):
        provider = KBaseTokenProvider(_SettingsStub())
        with _patch_client(raise_invalid=True):
            assert await provider.get_token(_fake_request({"kbase_session_backup": "bogus"})) is None


# ---------------------------------------------------------------------------
# MFA-optional configuration
# ---------------------------------------------------------------------------


class TestMfaOptional:
    @pytest.mark.asyncio
    async def test_accepts_non_mfa_token_when_mfa_disabled(self):
        """With kbase_auth_mfa=False, a non-MFA token that's otherwise valid
        should be accepted. This is the dev / non-prod configuration."""
        provider = KBaseTokenProvider(_SettingsStub(kbase_auth_mfa=False))
        token_info = _mock_token_info(mfa=MFAStatus.NOT_USED, expires=_future_ms())
        with _patch_client(token_info=token_info):
            result = await provider.get_token(_fake_request({"kbase_session_backup": "t"}))
        assert result == "t"

    @pytest.mark.asyncio
    async def test_still_rejects_expired_token_when_mfa_disabled(self):
        """Expiration check applies regardless of the MFA toggle."""
        provider = KBaseTokenProvider(_SettingsStub(kbase_auth_mfa=False))
        token_info = _mock_token_info(mfa=MFAStatus.NOT_USED, expires=_past_ms())
        with _patch_client(token_info=token_info):
            assert await provider.get_token(_fake_request({"kbase_session_backup": "t"})) is None


# ---------------------------------------------------------------------------
# Configurable cookie name
# ---------------------------------------------------------------------------


class TestCookieName:
    @pytest.mark.asyncio
    async def test_honors_configured_cookie_name(self):
        provider = KBaseTokenProvider(_SettingsStub(kbase_auth_cookie="custom_cookie"))
        token_info = _mock_token_info()
        with _patch_client(token_info=token_info):
            # The default cookie name is set but should be ignored.
            result = await provider.get_token(_fake_request({
                "kbase_session_backup": "wrong",
                "custom_cookie": "right",
            }))
        assert result == "right"

    @pytest.mark.asyncio
    async def test_returns_none_when_configured_cookie_absent(self):
        provider = KBaseTokenProvider(_SettingsStub(kbase_auth_cookie="custom_cookie"))
        with patch(
            "app.auth_providers.kbase.AsyncKBaseAuthClient.create",
            side_effect=AssertionError("must not call KBase when configured cookie missing"),
        ):
            # Default cookie is set but the provider only reads custom_cookie.
            assert await provider.get_token(_fake_request({"kbase_session_backup": "t"})) is None

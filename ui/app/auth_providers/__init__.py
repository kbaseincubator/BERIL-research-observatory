"""Authentication and token providers.

ORCiD is the identity provider — it owns the BerilUser row and runs the login
flow. Other providers (currently just KBase) are token providers: stateless
helpers that read a credential off the incoming request so the app can call an
external service on the user's behalf.

The deployment picks which token providers are enabled via
``BERIL_AUTH_TOKEN_PROVIDERS`` (comma-separated). The registry is built once at
startup and stashed on ``app.state.auth_providers``.
"""

from dataclasses import dataclass, field
from fastapi import Request

from app.config import Settings
from app.auth_providers.base import IdentityProvider, TokenProvider
from app.auth_providers.kbase import KBaseTokenProvider
from app.auth_providers.orcid import OrcidProvider


@dataclass
class ProviderRegistry:
    identity: IdentityProvider
    tokens: dict[str, TokenProvider] = field(default_factory=dict)


def load_providers(settings: Settings) -> ProviderRegistry:
    """Build the provider registry from settings."""
    identity = OrcidProvider(settings)

    tokens: dict[str, TokenProvider] = {}
    for name in settings.auth_token_providers_list:
        if name == "kbase":
            tokens["kbase"] = KBaseTokenProvider(settings)
        else:
            # Unknown provider name in config — fail loud rather than silently
            # dropping it, so a typo doesn't disable a security-relevant feature.
            raise ValueError(f"Unknown auth token provider: {name!r}")

    return ProviderRegistry(identity=identity, tokens=tokens)


async def get_kbase_token(request: Request) -> str | None:
    """Convenience accessor — returns None if the provider is not enabled
    or the user has no KBase session cookie."""
    registry: ProviderRegistry | None = getattr(request.app.state, "auth_providers", None)
    if registry is None:
        return None
    provider = registry.tokens.get("kbase")
    return await provider.get_token(request) if provider else None


__all__ = [
    "ProviderRegistry",
    "load_providers",
    "get_kbase_token",
    "IdentityProvider",
    "TokenProvider",
]

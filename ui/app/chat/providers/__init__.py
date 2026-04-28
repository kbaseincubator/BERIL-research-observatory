"""Chat provider registry.

The registry maps ``provider_id`` strings (as stored on
``ChatSession.provider_id``) to concrete provider instances. Membership is
driven by the chat config YAML: each entry in ``providers`` becomes one
registry entry, selected by its ``wire_protocol``.

Adding a new wire protocol (e.g. OpenAI, Bedrock) is a code change — add the
implementation and extend :func:`_build_provider` — but adding a new provider
that speaks an existing wire protocol is a config edit only.
"""

from __future__ import annotations

from app.chat.config import ProviderConfig, get_chat_config
from app.chat.providers.anthropic_compatible import AnthropicCompatibleProvider
from app.chat.providers.base import ChatProvider

_registry: dict[str, ChatProvider] | None = None


def _build_provider(provider_id: str, cfg: ProviderConfig) -> ChatProvider:
    if cfg.wire_protocol == "anthropic":
        return AnthropicCompatibleProvider(provider_id=provider_id, config=cfg)
    # Unreachable: ChatConfig pydantic validation rejects unknown wire_protocols.
    raise ValueError(f"unknown wire_protocol {cfg.wire_protocol!r}")


def get_providers() -> dict[str, ChatProvider]:
    """Return the cached registry, building it on first access."""
    global _registry
    if _registry is None:
        chat_cfg = get_chat_config()
        _registry = {pid: _build_provider(pid, pc) for pid, pc in chat_cfg.providers.items()}
    return _registry


def get_provider(provider_id: str) -> ChatProvider:
    """Look up a provider by id. Raises KeyError if unknown."""
    reg = get_providers()
    if provider_id not in reg:
        raise KeyError(f"unknown chat provider {provider_id!r}")
    return reg[provider_id]


def reset_providers_cache() -> None:
    """Drop the cached registry. Tests only."""
    global _registry
    _registry = None


__all__ = [
    "ChatProvider",
    "get_provider",
    "get_providers",
    "reset_providers_cache",
]

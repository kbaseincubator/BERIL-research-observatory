"""Chat provider configuration.

Loaded once at process startup from the YAML file at
``settings.chat_config_path``. Validated via pydantic so malformed config
fails fast instead of surfacing at the first chat request.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, field_validator

from app.config import get_settings

WireProtocol = Literal["anthropic"]  # OpenAI, Bedrock to be added later

# How the provider expects the API key to be presented.
#
# - ``api_key``: sent as the ``x-api-key`` header. What api.anthropic.com wants
#   for keys issued from console.anthropic.com.
# - ``bearer``: sent as ``Authorization: Bearer <token>``. What OAuth/proxy
#   layers in front of Anthropic (CBORG, enterprise gateways) typically want.
#
# Under the hood the Agent SDK maps these to its two env vars:
# ``ANTHROPIC_API_KEY`` for the former, ``ANTHROPIC_AUTH_TOKEN`` for the
# latter. Getting the wrong one produces "invalid bearer token" or
# similar auth failures even with a perfectly valid key.
AuthStyle = Literal["api_key", "bearer"]


class CredentialField(BaseModel):
    """One credential input the user must supply for a provider."""

    id: str
    display_name: str
    secret: bool = True


class ModelInfo(BaseModel):
    id: str
    display_name: str


class ProviderConfig(BaseModel):
    display_name: str
    wire_protocol: WireProtocol
    base_url: str
    # Optional. Defaults to "api_key" (x-api-key header) because that's what
    # direct Anthropic endpoints want. CBORG and similar proxies want "bearer".
    auth_style: AuthStyle = "api_key"
    credential_fields: list[CredentialField] = Field(default_factory=list)
    models: list[ModelInfo]

    @field_validator("models")
    @classmethod
    def _models_nonempty(cls, v: list[ModelInfo]) -> list[ModelInfo]:
        if not v:
            raise ValueError("provider must declare at least one model")
        return v

    @field_validator("credential_fields")
    @classmethod
    def _credential_ids_unique(cls, v: list[CredentialField]) -> list[CredentialField]:
        ids = [f.id for f in v]
        if len(ids) != len(set(ids)):
            raise ValueError("credential_fields must have unique ids")
        return v


class ChatConfig(BaseModel):
    providers: dict[str, ProviderConfig]

    @field_validator("providers")
    @classmethod
    def _providers_nonempty(cls, v: dict[str, ProviderConfig]) -> dict[str, ProviderConfig]:
        if not v:
            raise ValueError("chat config must declare at least one provider")
        return v


_chat_config: ChatConfig | None = None


def load_chat_config(path: Path | None = None) -> ChatConfig:
    """Read and validate the chat provider config from disk.

    Callers typically use :func:`get_chat_config` instead; this function exists
    for explicit reload and for tests.
    """
    config_path = path if path is not None else get_settings().chat_config_path
    if not config_path.exists():
        raise FileNotFoundError(f"chat config not found at {config_path}")
    with open(config_path, "r") as f:
        raw = yaml.safe_load(f)
    if not isinstance(raw, dict):
        raise ValueError(f"chat config at {config_path} must be a mapping")
    return ChatConfig.model_validate(raw)


def get_chat_config() -> ChatConfig:
    """Return the cached chat config, loading it on first access."""
    global _chat_config
    if _chat_config is None:
        _chat_config = load_chat_config()
    return _chat_config


def reset_chat_config_cache() -> None:
    """Drop the cached config. Tests only."""
    global _chat_config
    _chat_config = None

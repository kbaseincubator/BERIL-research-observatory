"""Configuration for the observatory OpenViking client."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ObservatoryContextSettings(BaseSettings):
    """Settings for OpenViking integration."""

    openviking_url: str = Field(default="http://127.0.0.1:1933")
    openviking_api_key: str | None = Field(default=None)
    openviking_agent_id: str | None = Field(default="beril-observatory")
    openviking_config: Path | None = Field(default=None)

    model_config = SettingsConfigDict(
        env_prefix="BERIL_",
        env_file=".env",
        extra="ignore",
    )


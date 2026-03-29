"""Configuration for the observatory OpenViking client."""

from __future__ import annotations

from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ObservatoryContextSettings(BaseSettings):
    """Settings for OpenViking integration."""

    openviking_url: str = Field(default="http://127.0.0.1:1933")
    openviking_api_key: str | None = Field(default=None)
    openviking_agent_id: str | None = Field(default="beril-observatory")
    openviking_config: Path | None = Field(default=None)

    cborg_api_url: str = Field(
        default="https://api.cborg.lbl.gov/v1",
        validation_alias=AliasChoices("CBORG_API_URL", "BERIL_CBORG_API_URL"),
    )
    cborg_model: str = Field(
        default="claude-haiku-4-5-20251001",
        validation_alias=AliasChoices("CBORG_MODEL", "BERIL_CBORG_MODEL"),
    )
    cborg_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("CBORG_API_KEY", "BERIL_CBORG_API_KEY"),
    )

    model_config = SettingsConfigDict(
        env_prefix="BERIL_",
        env_file=".env",
        extra="ignore",
    )


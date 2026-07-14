"""Unit tests for the chat provider configuration loader."""

from pathlib import Path

import pytest

from app.chat import config as chat_config


def _write_yaml(path: Path, text: str) -> Path:
    path.write_text(text)
    return path


def test_load_shipped_chat_providers_yaml():
    """The checked-in placeholder YAML loads and validates cleanly."""
    from app.config import get_settings

    cfg = chat_config.load_chat_config(get_settings().chat_config_path)

    assert "anthropic" in cfg.providers
    assert "cborg" in cfg.providers

    anthropic = cfg.providers["anthropic"]
    assert anthropic.display_name == "Anthropic"
    assert anthropic.wire_protocol == "anthropic"
    assert anthropic.base_url == "https://api.anthropic.com"
    assert {m.id for m in anthropic.models} == {"claude-opus-4-7", "claude-sonnet-4-6"}
    assert [f.id for f in anthropic.credential_fields] == ["api_key"]

    cborg = cfg.providers["cborg"]
    assert cborg.base_url == "https://api.cborg.lbl.gov"
    assert len(cborg.models) >= 1


def test_missing_file_raises(tmp_path):
    missing = tmp_path / "does_not_exist.yaml"
    with pytest.raises(FileNotFoundError):
        chat_config.load_chat_config(missing)


def test_non_mapping_root_rejected(tmp_path):
    path = _write_yaml(tmp_path / "c.yaml", "- just\n- a\n- list\n")
    with pytest.raises(ValueError, match="must be a mapping"):
        chat_config.load_chat_config(path)


def test_empty_providers_rejected(tmp_path):
    path = _write_yaml(tmp_path / "c.yaml", "providers: {}\n")
    with pytest.raises(Exception):  # pydantic ValidationError
        chat_config.load_chat_config(path)


def test_provider_with_no_models_rejected(tmp_path):
    path = _write_yaml(
        tmp_path / "c.yaml",
        """
providers:
  p1:
    display_name: P1
    wire_protocol: anthropic
    base_url: https://example.com
    models: []
""",
    )
    with pytest.raises(Exception):
        chat_config.load_chat_config(path)


def test_unknown_wire_protocol_rejected(tmp_path):
    path = _write_yaml(
        tmp_path / "c.yaml",
        """
providers:
  p1:
    display_name: P1
    wire_protocol: gopher
    base_url: https://example.com
    models:
      - id: m1
        display_name: Model One
""",
    )
    with pytest.raises(Exception):
        chat_config.load_chat_config(path)


def test_duplicate_credential_field_ids_rejected(tmp_path):
    path = _write_yaml(
        tmp_path / "c.yaml",
        """
providers:
  p1:
    display_name: P1
    wire_protocol: anthropic
    base_url: https://example.com
    credential_fields:
      - id: api_key
        display_name: Key A
      - id: api_key
        display_name: Key B
    models:
      - id: m1
        display_name: Model One
""",
    )
    with pytest.raises(Exception, match="unique"):
        chat_config.load_chat_config(path)


def test_minimal_valid_config_loads(tmp_path):
    path = _write_yaml(
        tmp_path / "c.yaml",
        """
providers:
  minimal:
    display_name: Minimal
    wire_protocol: anthropic
    base_url: https://example.com
    models:
      - id: only-model
        display_name: Only Model
""",
    )
    cfg = chat_config.load_chat_config(path)
    assert cfg.providers["minimal"].credential_fields == []
    assert cfg.providers["minimal"].models[0].id == "only-model"


def test_get_chat_config_caches(monkeypatch, tmp_path):
    path = _write_yaml(
        tmp_path / "c.yaml",
        """
providers:
  p1:
    display_name: P1
    wire_protocol: anthropic
    base_url: https://example.com
    models:
      - id: m1
        display_name: M1
""",
    )
    chat_config.reset_chat_config_cache()

    from app import config as app_config

    monkeypatch.setattr(app_config.get_settings(), "chat_config_path", path, raising=False)

    first = chat_config.get_chat_config()
    second = chat_config.get_chat_config()
    assert first is second  # cached

    chat_config.reset_chat_config_cache()


def test_settings_defaults_point_to_shipped_yaml():
    from app.config import Settings

    # Use the same sentinel pattern as test_config.py
    s = Settings(_env_file="/dev/null/nonexistent.env")
    assert s.chat_config_path.name == "chat_providers.yaml"
    assert s.chat_config_path.parent.name == "config"
    assert s.chat_max_concurrent_turns_per_user == 3


def test_chat_max_concurrent_turns_env_override(monkeypatch):
    from app.config import Settings

    monkeypatch.setenv("BERIL_CHAT_MAX_CONCURRENT_TURNS_PER_USER", "7")
    s = Settings()
    assert s.chat_max_concurrent_turns_per_user == 7


def test_chat_config_path_env_override(monkeypatch, tmp_path):
    from app.config import Settings

    custom = tmp_path / "custom_chat.yaml"
    monkeypatch.setenv("BERIL_CHAT_CONFIG_PATH", str(custom))
    s = Settings()
    assert s.chat_config_path == custom

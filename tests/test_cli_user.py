"""Tests for `beril user` subcommand."""

from __future__ import annotations

import argparse
import json

import pytest

from beril_cli import config
from beril_cli.user_cmd import run_user


@pytest.fixture()
def tmp_config(tmp_path, monkeypatch):
    """Point config at a temporary directory."""
    cfg_dir = tmp_path / ".config" / "beril"
    cfg_dir.mkdir(parents=True)
    monkeypatch.setattr(config, "CONFIG_DIR", cfg_dir)
    monkeypatch.setattr(config, "CONFIG_PATH", cfg_dir / "config.toml")
    return cfg_dir / "config.toml"


def _ns(json_flag: bool = False) -> argparse.Namespace:
    return argparse.Namespace(json=json_flag)


def test_full_config_pretty(tmp_config, capsys):
    config.save({"user": {"name": "Alice", "affiliation": "LBNL", "orcid": "0000-0001-2345-6789"}})
    rc = run_user(_ns())
    out = capsys.readouterr().out
    assert rc == 0
    assert "Alice" in out
    assert "LBNL" in out
    assert "0000-0001-2345-6789" in out
    assert "(missing)" not in out


def test_full_config_json(tmp_config, capsys):
    config.save({"user": {"name": "Alice", "affiliation": "LBNL", "orcid": "0000-0001-2345-6789"}})
    rc = run_user(_ns(json_flag=True))
    out = capsys.readouterr().out
    assert rc == 0
    assert json.loads(out) == {
        "name": "Alice",
        "affiliation": "LBNL",
        "orcid": "0000-0001-2345-6789",
    }


def test_partial_config_pretty_returns_1(tmp_config, capsys):
    config.save({"user": {"name": "Alice", "affiliation": "LBNL"}})  # missing orcid
    rc = run_user(_ns())
    captured = capsys.readouterr()
    assert rc == 1
    assert "Alice" in captured.out
    assert "(missing)" in captured.out
    assert "orcid" in captured.err
    assert "beril setup" in captured.err


def test_partial_config_json(tmp_config, capsys):
    config.save({"user": {"name": "Alice", "affiliation": "LBNL"}})
    rc = run_user(_ns(json_flag=True))
    captured = capsys.readouterr()
    assert rc == 1
    parsed = json.loads(captured.out)
    assert parsed == {"name": "Alice", "affiliation": "LBNL", "orcid": ""}
    assert "orcid" in captured.err


def test_no_config_file_pretty(tmp_config, capsys):
    rc = run_user(_ns())
    captured = capsys.readouterr()
    assert rc == 1
    assert "No user config" in captured.err
    assert "beril setup" in captured.err


def test_no_user_section_pretty(tmp_config, capsys):
    config.save({"defaults": {"agent": "claude"}})  # no [user]
    rc = run_user(_ns())
    captured = capsys.readouterr()
    assert rc == 1
    assert "beril setup" in captured.err


def test_no_config_json_returns_empty_strings(tmp_config, capsys):
    rc = run_user(_ns(json_flag=True))
    captured = capsys.readouterr()
    assert rc == 1
    assert json.loads(captured.out) == {"name": "", "affiliation": "", "orcid": ""}

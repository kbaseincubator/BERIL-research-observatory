"""Tests for the installed CLI distribution version."""

import importlib.metadata
import runpy
from pathlib import Path

import beril_cli


def test_version_falls_back_without_distribution_metadata(monkeypatch):
    """A source-only checkout still has a meaningful, PEP 440 version."""

    def missing_distribution(_distribution_name):
        raise importlib.metadata.PackageNotFoundError

    monkeypatch.setattr(importlib.metadata, "version", missing_distribution)

    namespace = runpy.run_path(Path(beril_cli.__file__))

    assert namespace["__version__"] == "0+unknown"

"""Deterministic wiki integrity checks (dangling links + orphan citations)."""

from __future__ import annotations

import json
from pathlib import Path

from compendium.check import check_wiki


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_check_passes_clean_wiki(tmp_path: Path) -> None:
    _write(
        tmp_path / "index.md",
        "# Home\n\nSee [topic x](topics/x.md).\n",
    )
    _write(tmp_path / "topics" / "x.md", "# Topic X\n\nBody.\n")

    assert check_wiki(tmp_path) == []


def test_check_flags_broken_wiki_link(tmp_path: Path) -> None:
    _write(
        tmp_path / "index.md",
        "# Home\n\nSee [missing](topics/missing.md).\n",
    )

    problems = check_wiki(tmp_path)

    assert problems
    assert any("topics/missing.md" in p for p in problems)


def test_check_ignores_external_and_anchor_links(tmp_path: Path) -> None:
    _write(
        tmp_path / "index.md",
        "# Home\n\n[ext](https://example.com) [mail](mailto:a@b.c) [anchor](#section).\n",
    )

    assert check_wiki(tmp_path) == []


def test_check_flags_orphan_citation_against_manifest(tmp_path: Path) -> None:
    _write(
        tmp_path / "topics" / "x.md",
        "# Topic X\n\nA finding [stmt:known-id; proj_a] and [stmt:orphan-id; proj_a].\n",
    )
    _write(
        tmp_path / ".manifests" / "topics" / "x.manifest.json",
        json.dumps({"cited_statement_ids": ["stmt:known-id"]}),
    )

    problems = check_wiki(tmp_path)

    assert any("orphan-id" in p for p in problems)
    assert not any("known-id" in p for p in problems)


def test_check_skips_citation_check_when_no_manifest(tmp_path: Path) -> None:
    _write(
        tmp_path / "topics" / "x.md",
        "# Topic X\n\nA finding [stmt:any-id; proj_a].\n",
    )

    # No manifest for this page -> citation check skipped, no crash, no problems.
    assert check_wiki(tmp_path) == []

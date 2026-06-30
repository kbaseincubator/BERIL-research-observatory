"""Deterministic wiki integrity checks (dangling links)."""

from __future__ import annotations

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


def test_check_ignores_non_link_bracket_text(tmp_path: Path) -> None:
    # Bracketed text that is not a Markdown link (no parenthesized target) is not a link.
    _write(
        tmp_path / "topics" / "x.md",
        "# Topic X\n\nA finding [stmt:any-id; proj_a] with no parenthesized target.\n",
    )

    assert check_wiki(tmp_path) == []


def test_check_skips_source_report_links(tmp_path: Path) -> None:
    # A project page links to its source REPORT.md, which lives outside the wiki tree.
    _write(
        tmp_path / "projects" / "p.md",
        "# P\n\n[Open the full report →](../../../projects/p/REPORT.md)\n",
    )

    # The source report is the one deliberately external link; it is not flagged.
    assert check_wiki(tmp_path) == []


def test_check_flags_escaping_non_report_link(tmp_path: Path) -> None:
    # A genuine off-by-one typo that escapes the wiki root is still a dead link, not external.
    _write(tmp_path / "index.md", "# Home\n\nSee [x](../topics/x.md).\n")
    _write(tmp_path / "topics" / "x.md", "# X\n\nBody.\n")

    problems = check_wiki(tmp_path)

    assert any("../topics/x.md" in p for p in problems)

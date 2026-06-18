"""Tests for paragraph reflow (pages/reflow.py)."""

from __future__ import annotations

from compendium.pages.reflow import reflow_paragraphs


def test_reflow_joins_hard_wrapped_paragraph() -> None:
    md = "# Title\n\nA sentence that was\nhard wrapped across\nthree lines.\n\nNext para.\n"
    out = reflow_paragraphs(md)
    assert "A sentence that was hard wrapped across three lines." in out
    assert out.count("\n\n") == 2  # title|para1, para1|para2
    assert "# Title" in out


def test_reflow_preserves_headings_and_reference_list() -> None:
    md = (
        "## References\n\n"
        "1. [Proj One](../projects/proj-one.md) — REPORT.md › \"Findings\".\n"
        "2. [Proj Two](../projects/proj-two.md) — REPORT.md.\n"
    )
    out = reflow_paragraphs(md)
    lines = [l for l in out.splitlines() if l.startswith(("1.", "2."))]
    assert len(lines) == 2  # each reference stays on its own line


def test_reflow_joins_wrapped_list_item_but_keeps_items_separate() -> None:
    md = "- first item that wraps\nonto a second line\n- second item\n"
    out = reflow_paragraphs(md)
    assert "- first item that wraps onto a second line" in out
    assert "- second item" in out


def test_reflow_leaves_code_blocks_untouched() -> None:
    md = "Para one\nwrapped.\n\n```\ncode line 1\ncode line 2\n```\n"
    out = reflow_paragraphs(md)
    assert "Para one wrapped." in out
    assert "code line 1\ncode line 2" in out

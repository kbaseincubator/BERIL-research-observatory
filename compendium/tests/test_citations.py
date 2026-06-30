"""Tests for the publish-time provenance transforms (pages/citations.py)."""

from __future__ import annotations

from compendium.models import EvidenceAnchor, StatementCard, StatementLinks
from compendium.pages.citations import (
    clean_project_lead,
    link_project_mentions,
    normalize_page_links,
    render_inline_citations,
)


def _card(id_: str, project: str, *, section: str | None = "Findings") -> StatementCard:
    return StatementCard(
        id=id_,
        kind="finding",
        text=f"text for {id_}",
        confidence="high",
        topics=[],
        entities=[],
        links=StatementLinks(),
        evidence=[
            EvidenceAnchor(
                source_project=project, source_doc="REPORT.md", source_section=section, quote="q"
            )
        ],
    )


def _by_id(*cards: StatementCard) -> dict[str, StatementCard]:
    return {c.id: c for c in cards}


def test_inline_citations_numbered_deduped_and_referenced() -> None:
    cards = _by_id(_card("stmt:a", "proj_one"), _card("stmt:b", "proj_two"))
    body = (
        "# Topic\n\nA claim [stmt:a; proj_one]. A second claim [stmt:b; proj_two], "
        "and the first again [stmt:a; proj_one].\n"
    )

    out, cited = render_inline_citations(
        body, cards, page_path="topics/x.md", member_ids={"stmt:a", "stmt:b"}
    )

    assert cited == ["stmt:a", "stmt:b"]
    # Same statement -> same number; new statement -> next number.
    assert out.count("[\\[1\\]](#references)") == 2
    assert "[\\[2\\]](#references)" in out
    assert "[stmt:a;" not in out
    assert "## References" in out
    assert "1. [Proj One](../projects/proj-one.md) — REPORT.md › \"Findings\"." in out
    assert "2. [Proj Two](../projects/proj-two.md) — REPORT.md › \"Findings\"." in out


def test_inline_citations_relpath_from_home() -> None:
    cards = _by_id(_card("stmt:a", "proj_one"))
    out, _ = render_inline_citations(
        "# Home\n\nClaim [stmt:a; proj_one].\n",
        cards,
        page_path="index.md",
        member_ids={"stmt:a"},
    )
    assert "[Proj One](projects/proj-one.md)" in out


def test_inline_citations_reject_nonmember_and_missing() -> None:
    cards = _by_id(_card("stmt:a", "proj_one"))
    import pytest

    with pytest.raises(ValueError, match="outside page membership"):
        render_inline_citations(
            "x [stmt:b; proj_two].", cards, page_path="topics/x.md", member_ids={"stmt:a"}
        )
    with pytest.raises(ValueError, match="at least one member"):
        render_inline_citations(
            "no citation here", cards, page_path="topics/x.md", member_ids={"stmt:a"}
        )


def test_strip_leaves_legitimate_sources_heading_intact() -> None:
    # "## Sources of variation" must NOT be treated as the trailing provenance dump.
    cards = _by_id(_card("stmt:a", "proj_one"))
    body = (
        "# Topic\n\n## Overview\n\nA [stmt:a; proj_one].\n\n"
        "## Sources of variation\n\nNoise can come from sampling.\n"
    )
    out, _ = render_inline_citations(
        body, cards, page_path="topics/x.md", member_ids={"stmt:a"}
    )
    assert "## Sources of variation" in out
    assert "Noise can come from sampling." in out
    assert "## References" in out


def test_strip_removes_author_written_references_section_no_duplicate() -> None:
    cards = _by_id(_card("stmt:a", "proj_one"))
    body = (
        "# Topic\n\nA [stmt:a; proj_one].\n\n"
        "## References\n\n- [stmt:a; proj_one]\n"
    )
    out, _ = render_inline_citations(
        body, cards, page_path="topics/x.md", member_ids={"stmt:a"}
    )
    assert out.count("## References") == 1


def test_section_missing_renders_without_section_suffix() -> None:
    cards = _by_id(_card("stmt:a", "proj_one", section=None))
    out, _ = render_inline_citations(
        "x [stmt:a; proj_one].", cards, page_path="topics/x.md", member_ids={"stmt:a"}
    )
    assert "1. [Proj One](../projects/proj-one.md) — REPORT.md." in out


def test_link_project_mentions_only_known_projects() -> None:
    out = link_project_mentions(
        "Uses `proj_one` but not `unknown_proj`.",
        {"proj_one"},
        page_path="topics/x.md",
    )
    assert "[`proj_one`](../projects/proj-one.md)" in out
    assert "`unknown_proj`" in out and "unknown-proj.md" not in out


def test_normalize_page_links_fixes_root_relative_cross_links() -> None:
    known = {"topics/a.md", "topics/b.md", "data/d.md", "index.md"}
    md = (
        "From topic A: [B](topics/b.md), [D](data/d.md#sec), "
        "an already-correct sibling [B2](b.md), and a relative [up](../authors/x.md)."
    )
    out = normalize_page_links(md, page_path="topics/a.md", known_paths=known)
    # root-relative known-page links become page-relative
    assert "[B](b.md)" in out
    assert "[D](../data/d.md#sec)" in out
    # a correct sibling link (not a wiki-root path) is left alone
    assert "[B2](b.md)" in out
    # an explicitly relative link is untouched
    assert "[up](../authors/x.md)" in out


def test_normalize_page_links_leaves_home_root_links_unchanged() -> None:
    known = {"topics/a.md", "index.md"}
    out = normalize_page_links(
        "Home links [A](topics/a.md).", page_path="index.md", known_paths=known
    )
    assert "[A](topics/a.md)" in out


def test_clean_project_lead_strips_tokens_and_leading_heading() -> None:
    lead = "# Proj One\n\nThis project found a gradient [stmt:a; proj_one]. It matters."
    cleaned = clean_project_lead(lead)
    assert not cleaned.startswith("#")
    assert "[stmt:a;" not in cleaned
    assert "found a gradient. It matters." in cleaned

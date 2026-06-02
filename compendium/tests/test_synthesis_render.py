"""Tests for deterministic v4 synthesis-wiki rendering."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from compendium.models import (
    AboutRefs,
    EvidenceAnchor,
    ExtractionManifest,
    PagePlan,
    PageSectionPlan,
    StatementCard,
    StatementLinks,
)
from compendium.pages import plan_pages
from compendium.render.synthesis import render_synthesis_site


def _manifest(timestamp: str = "2026-06-02T00:00:00Z") -> ExtractionManifest:
    return ExtractionManifest(
        agent_type="llm_extractor",
        skill="kg-ingest-project",
        model="test-model",
        prompt_hash="prompt:abc",
        context_pack_hash="context:def",
        repo_commit="abc123",
        timestamp=timestamp,
    )


def _card(
    *,
    id_: str,
    kind: str,
    statement: str,
    project: str,
    topics: list[str],
    entities: list[str],
    confidence: str = "medium",
    links: StatementLinks | None = None,
) -> StatementCard:
    return StatementCard(
        id=id_,
        kind=kind,
        statement=statement,
        scope="cross_project" if kind == "claim" else "project_local",
        tier="grounded",
        confidence=confidence,
        about=AboutRefs(entities=entities, topics=topics),
        links=links or StatementLinks(),
        qualifiers={"organism": "entity:adp1"},
        evidence=EvidenceAnchor(
            source_project=project,
            source_doc="REPORT.md",
            source_section="Key Findings",
            exact=statement,
        ),
        extraction=_manifest(),
    )


def _cards() -> list[StatementCard]:
    topic = "topic:carbon-source-essentiality"
    entity = "entity:adp1"
    return [
        _card(
            id_="stmt:f1",
            kind="finding",
            statement="ADP1 carbon sources define condition-specific essentiality.",
            project="adp1_deletion_phenotypes",
            topics=[topic],
            entities=[entity],
            links=StatementLinks(supports=["stmt:c1"]),
        ),
        _card(
            id_="stmt:c1",
            kind="claim",
            statement="ADP1 has a reusable carbon-source essentiality landscape.",
            project="adp1_deletion_phenotypes",
            topics=[topic],
            entities=[entity],
            confidence="high",
        ),
        _card(
            id_="stmt:o1",
            kind="opportunity",
            statement="Compare ADP1 essential genes across additional carbon sources.",
            project="adp1_followup",
            topics=[topic],
            entities=[entity],
            links=StatementLinks(motivates=["stmt:c1"]),
        ),
    ]


def _hrefs(html_file: Path) -> list[str]:
    return re.findall(r'href="([^"#?]+)"', html_file.read_text(encoding="utf-8"))


def test_render_home_topic_entity_and_claim_pages(tmp_path: Path) -> None:
    cards = _cards()
    render_synthesis_site(cards, plan_pages(cards), tmp_path)

    home = (tmp_path / "index.html").read_text(encoding="utf-8")
    topic = (tmp_path / "topic_carbon-source-essentiality.html").read_text(encoding="utf-8")
    entity = (tmp_path / "entity_adp1.html").read_text(encoding="utf-8")
    claim = (tmp_path / "claim_c1.html").read_text(encoding="utf-8")

    assert "State Of The Science" in home
    assert "home page" in home
    assert "Topic: Carbon Source Essentiality" in topic
    assert "topic page" in topic
    assert "Entity: Adp1" in entity
    assert "entity page" in entity
    assert "ADP1 has a reusable carbon-source essentiality landscape." in claim
    assert "claim page" in claim


def test_render_includes_sections_sources_and_navigation(tmp_path: Path) -> None:
    cards = _cards()
    render_synthesis_site(cards, plan_pages(cards), tmp_path)

    claim = (tmp_path / "claim_c1.html").read_text(encoding="utf-8")

    assert "Supporting Evidence" in claim
    assert "Source Projects" in claim
    assert "adp1_deletion_phenotypes" in claim
    assert "REPORT.md" in claim
    assert "Outgoing Links" in claim
    assert "Backlinks" in claim
    assert "topic_carbon-source-essentiality.html" in claim
    assert "entity_adp1.html" in claim


def test_render_has_no_broken_internal_links(tmp_path: Path) -> None:
    cards = _cards()
    render_synthesis_site(cards, plan_pages(cards), tmp_path)

    for html_file in tmp_path.rglob("*.html"):
        for href in _hrefs(html_file):
            target = (html_file.parent / href).resolve()
            assert target.exists(), f"broken link {href} in {html_file}"


def test_render_output_is_deterministic(tmp_path: Path) -> None:
    cards = _cards()
    plans = plan_pages(cards)
    out_a = tmp_path / "a"
    out_b = tmp_path / "b"

    paths_a = render_synthesis_site(cards, plans, out_a)
    paths_b = render_synthesis_site(list(reversed(cards)), list(reversed(plans)), out_b)

    rel_a = sorted(path.relative_to(out_a).as_posix() for path in paths_a)
    rel_b = sorted(path.relative_to(out_b).as_posix() for path in paths_b)
    assert rel_a == rel_b

    for relative_path in rel_a:
        assert (out_a / relative_path).read_text(encoding="utf-8") == (
            out_b / relative_path
        ).read_text(encoding="utf-8")


def test_render_rejects_page_filename_collisions(tmp_path: Path) -> None:
    plans = [
        PagePlan(
            id="topic:a/b",
            type="topic",
            title="Slash Topic",
            member_statement_ids=[],
            sections=[PageSectionPlan(id="main", heading="Main", member_statement_ids=[])],
            outgoing_links=[],
            backlinks=[],
            member_hash="hash:slash",
        ),
        PagePlan(
            id="topic:a_b",
            type="topic",
            title="Underscore Topic",
            member_statement_ids=[],
            sections=[PageSectionPlan(id="main", heading="Main", member_statement_ids=[])],
            outgoing_links=[],
            backlinks=[],
            member_hash="hash:underscore",
        ),
    ]

    with pytest.raises(ValueError, match="same filename"):
        render_synthesis_site(_cards(), plans, tmp_path)

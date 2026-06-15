"""Tests for deterministic synthesis-wiki page planning (topic/data/author/home model)."""

from __future__ import annotations

from compendium.data_index import CollectionRecord
from compendium.models import (
    AboutRefs,
    EvidenceAnchor,
    ExtractionManifest,
    StatementCard,
    StatementLinks,
)
from compendium.pages import build_page_context, plan_pages, write_page_artifact
from compendium.people import AuthorRecord
from compendium.registry import Registry


def _manifest(timestamp: str = "2026-06-02T00:00:00Z") -> ExtractionManifest:
    return ExtractionManifest(
        agent_type="llm_extractor",
        skill="kg-extract",
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
    tier: str = "grounded",
    links: StatementLinks | None = None,
    timestamp: str = "2026-06-02T00:00:00Z",
) -> StatementCard:
    return StatementCard(
        id=id_,
        kind=kind,
        statement=statement,
        scope="cross_project" if kind == "claim" else "project_local",
        tier=tier,
        confidence=confidence,
        about=AboutRefs(entities=entities, topics=topics),
        links=links or StatementLinks(),
        qualifiers={},
        evidence=EvidenceAnchor(
            source_project=project,
            source_doc="REPORT.md",
            source_section="Key Findings",
            exact=statement,
        ),
        extraction=_manifest(timestamp),
    )


# Two raw topic slugs (`topic:metal-resistance` and `topic:Metal-Resistance`) that the small
# registry's case-folding merges into one canonical key; a second topic (`topic:pangenome`)
# stays distinct.
def _cards() -> list[StatementCard]:
    return [
        _card(
            id_="stmt:m1",
            kind="finding",
            statement="Metal fitness atlas maps cross-metal resistance genes.",
            project="metal_fitness_atlas",
            topics=["topic:metal-resistance"],
            entities=["entity:adp1"],
        ),
        _card(
            id_="stmt:m2",
            kind="claim",
            statement="Metal resistance is largely shared across the tested strains.",
            project="metal_fitness_atlas",
            topics=["topic:Metal-Resistance"],  # case variant -> merges with m1's topic
            entities=["entity:a_baylyi_adp1"],  # entity alias -> adp1
            confidence="high",
        ),
        _card(
            id_="stmt:m3",
            kind="caveat",
            statement="Cross-metal resistance conclusions depend on the metal panel tested.",
            project="metal_cross_resistance",
            topics=["topic:Metal-Resistance"],
            entities=["entity:adp1"],
        ),
        _card(
            id_="stmt:m4",
            kind="opportunity",
            statement="Extend the metal panel to rare-earth elements.",
            project="metal_cross_resistance",
            topics=["topic:metal-resistance"],
            entities=["entity:adp1"],
        ),
        _card(
            id_="stmt:p1",
            kind="finding",
            statement="Pangenome openness varies with accessory-gene turnover.",
            project="pangenome_openness",
            topics=["topic:pangenome"],
            entities=["entity:adp1"],
        ),
    ]


def _registry() -> Registry:
    return Registry(
        {
            "topics": {
                "topic:metal-resistance": {
                    "label": "Metal Resistance & Critical Minerals",
                    "definition": "x",
                    "projects": [],
                },
                "topic:pangenome": {
                    "label": "Pangenome Architecture",
                    "definition": "x",
                    "projects": [],
                },
            },
            "entities": {
                "entity:adp1": {
                    "label": "Acinetobacter baylyi ADP1",
                    "kind": "organism",
                    "aliases": ["entity:a_baylyi_adp1"],
                }
            },
        }
    )


def _authors() -> dict[str, AuthorRecord]:
    return {
        "0000-0001-5810-2497": AuthorRecord(
            name="Paramvir S. Dehal",
            orcid="0000-0001-5810-2497",
            projects=["metal_fitness_atlas", "metal_cross_resistance"],
        ),
        "0009-0007-0287-2979": AuthorRecord(
            name="Beril Admin",
            orcid="0009-0007-0287-2979",
            projects=["pangenome_openness"],
        ),
    }


def _collections() -> dict[str, CollectionRecord]:
    return {
        "kbase_ke_pangenome": CollectionRecord(
            id="kbase_ke_pangenome",
            projects=["metal_fitness_atlas", "pangenome_openness"],
        ),
        "kescience_fitnessbrowser": CollectionRecord(
            id="kescience_fitnessbrowser",
            projects=["metal_fitness_atlas", "metal_cross_resistance"],
        ),
        # A collection no present project cites -> must be omitted.
        "enigma_coral": CollectionRecord(id="enigma_coral", projects=["unrelated_project"]),
    }


def _plans(**overrides):
    kwargs = {
        "registry": _registry(),
        "authors": _authors(),
        "collections": _collections(),
    }
    kwargs.update(overrides)
    return {plan.id: plan for plan in plan_pages(_cards(), **kwargs)}


def test_page_plans_are_deterministic_for_shuffled_cards() -> None:
    cards = _cards()
    inputs = {"registry": _registry(), "authors": _authors(), "collections": _collections()}
    forward = [plan.to_dict() for plan in plan_pages(cards, **inputs)]
    backward = [plan.to_dict() for plan in plan_pages(list(reversed(cards)), **inputs)]
    assert forward == backward


def test_only_home_topic_data_author_page_types_exist() -> None:
    plans = _plans()
    types = {plan.type for plan in plans.values()}
    assert types == {"home", "topic", "data", "author"}
    # No legacy standalone page types.
    assert not any(
        plan.type in {"project", "claim", "conflict", "opportunity", "entity"}
        for plan in plans.values()
    )
    assert not any(pid.startswith(("project:", "claim:", "opportunity:")) for pid in plans)


def test_topic_canonicalization_merges_raw_slugs() -> None:
    plans = _plans()
    # Both raw slugs (metal-resistance / metal_resistance) collapse into one topic page.
    assert "topic:metal-resistance" in plans
    assert "topic:metal_resistance" not in plans
    metal = plans["topic:metal-resistance"]
    assert set(metal.member_statement_ids) == {"stmt:m1", "stmt:m2", "stmt:m3", "stmt:m4"}
    assert [section.heading for section in metal.sections] == [
        "Overview",
        "Key Claims",
        "Conflicts & Caveats",
        "Open Directions",
    ]
    sections = {s.id: s for s in metal.sections}
    assert sections["key_claims"].member_statement_ids == ["stmt:m2"]
    assert sections["conflicts_and_caveats"].member_statement_ids == ["stmt:m3"]
    assert sections["open_directions"].member_statement_ids == ["stmt:m4"]


def test_home_page_has_moc_sections_and_links_every_page() -> None:
    plans = _plans()
    home = plans["home"]
    assert home.type == "home"
    assert [section.heading for section in home.sections] == [
        "Cross-Project Overview",
        "Topic Map",
        "Author Map",
        "Data Map",
    ]
    assert set(home.outgoing_links) == {pid for pid in plans if pid != "home"}


def test_data_and_author_pages_have_expected_ids_types_and_paths() -> None:
    from compendium.pages import wiki_page_path

    plans = _plans()
    # Data pages: only collections with a present project; enigma_coral omitted.
    assert "data:kbase_ke_pangenome" in plans
    assert "data:kescience_fitnessbrowser" in plans
    assert "data:enigma_coral" not in plans
    data = plans["data:kbase_ke_pangenome"]
    assert data.type == "data"
    assert wiki_page_path(data).as_posix() == "data/kbase-ke-pangenome.md"
    assert [s.heading for s in data.sections] == ["Overview", "Projects Using This Collection"]

    # Author pages keyed by ORCID slug.
    author_id = "author:0000-0001-5810-2497"
    assert author_id in plans
    author = plans[author_id]
    assert author.type == "author"
    assert author.title == "Paramvir S. Dehal"
    assert wiki_page_path(author).as_posix() == "authors/0000-0001-5810-2497.md"
    assert [s.heading for s in author.sections] == ["Overview", "Projects", "Topics"]


def test_topic_links_to_its_data_and_author_pages() -> None:
    plans = _plans()
    metal = plans["topic:metal-resistance"]
    # metal projects (metal_fitness_atlas, metal_cross_resistance) cite both collections
    # and are authored by Dehal.
    assert "data:kbase_ke_pangenome" in metal.outgoing_links
    assert "data:kescience_fitnessbrowser" in metal.outgoing_links
    assert "author:0000-0001-5810-2497" in metal.outgoing_links
    # Adjacent topic: pangenome_openness does not share a project with metal topic, so the
    # metal topic should not link the pangenome topic.
    assert "topic:pangenome" not in metal.outgoing_links


def test_author_links_to_its_topics() -> None:
    plans = _plans()
    dehal = plans["author:0000-0001-5810-2497"]
    assert "topic:metal-resistance" in dehal.outgoing_links
    beril = plans["author:0009-0007-0287-2979"]
    assert "topic:pangenome" in beril.outgoing_links


def test_data_page_links_to_topic_and_author_pages() -> None:
    plans = _plans()
    pangenome_coll = plans["data:kbase_ke_pangenome"]
    # Cited by metal_fitness_atlas (metal topic, Dehal) and pangenome_openness (pangenome, Beril).
    assert "topic:metal-resistance" in pangenome_coll.outgoing_links
    assert "topic:pangenome" in pangenome_coll.outgoing_links
    assert "author:0000-0001-5810-2497" in pangenome_coll.outgoing_links
    assert "author:0009-0007-0287-2979" in pangenome_coll.outgoing_links


def test_backlinks_are_exact_reverse_of_outgoing() -> None:
    plans = _plans()
    for plan in plans.values():
        for target in plan.outgoing_links:
            assert plan.id in plans[target].backlinks
        for source in plan.backlinks:
            assert plan.id in plans[source].outgoing_links


def test_identity_passthrough_without_registry() -> None:
    # No registry -> raw topic slugs are not merged (case variants stay distinct).
    plans = {plan.id: plan for plan in plan_pages(_cards())}
    assert "topic:metal-resistance" in plans
    assert "topic:Metal-Resistance" in plans  # distinct without canonicalization
    # No authors/collections -> no data/author pages.
    assert {plan.type for plan in plans.values()} == {"home", "topic"}


def test_plan_then_context_then_authored_page_round_trips(tmp_path) -> None:
    plans = _plans()
    page_plans = list(plans.values())
    topic = plans["topic:metal-resistance"]

    context = build_page_context(topic, _cards(), page_plans=page_plans)
    assert context["page"]["id"] == "topic:metal-resistance"
    assert context["page"]["wiki_path"] == "topics/metal-resistance.md"
    member_ids = {s["id"] for s in context["member_statements"]}
    assert "stmt:m2" in member_ids
    # Cross-links to data + author pages surface in the link map.
    outgoing_ids = {ref["id"] for ref in context["link_map"]["outgoing"]}
    assert "data:kbase_ke_pangenome" in outgoing_ids
    assert "author:0000-0001-5810-2497" in outgoing_ids

    # A hand-authored page citing one member statement validates clean.
    markdown = (
        "# Topic: Metal Resistance\n\n"
        "Metal resistance is largely shared across the tested strains.\n\n"
        "## Sources\n\n"
        "- [stmt:m2; metal_fitness_atlas]\n"
    )
    markdown_path, manifest_path = write_page_artifact(
        topic,
        _cards(),
        tmp_path,
        markdown=markdown,
        model="test-model",
        prompt_hash="prompt:test",
    )
    assert markdown_path == tmp_path / "topics" / "metal-resistance.md"
    assert manifest_path.is_file()

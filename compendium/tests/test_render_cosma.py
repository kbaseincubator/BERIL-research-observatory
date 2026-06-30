"""Tests for the deterministic Cosma export (one node per published page)."""

from __future__ import annotations

from compendium.data_index import CollectionRecord
from compendium.models import EvidenceAnchor, StatementCard, StatementLinks
from compendium.pages import plan_pages
from compendium.people import AuthorRecord
from compendium.render.cosma import build_cosma_records, cosma_config, write_cosma_project


from compendium.cli import main


def _card(project: str, topic: str, *, id_: str) -> StatementCard:
    return StatementCard(
        id=id_,
        kind="finding",
        text=f"{project} finding about {topic}.",
        confidence="high",
        topics=[topic],
        entities=[],
        links=StatementLinks(),
        evidence=[EvidenceAnchor(source_project=project, source_doc="REPORT.md", quote="q")],
    )


def _fixture():
    cards = [_card("metal_fitness_atlas", "topic:metal-resistance", id_="stmt:m1")]
    authors = {
        "0000-0001-0000-0001": AuthorRecord(
            name="Jane Roe", orcid="0000-0001-0000-0001", projects=["metal_fitness_atlas"]
        )
    }
    collections = {"kbase_x": CollectionRecord(id="kbase_x", projects=["metal_fitness_atlas"])}
    page_markdown = {
        "home": "# State of the Science\n\nSee [Metal Resistance](topics/metal-resistance.md).\n",
        "topic:metal-resistance": (
            "# Metal Resistance\n\n## Overview\n\n"
            "Uses [KBase X](../data/kbase-x.md) and authored by "
            "[Jane Roe](../authors/0000-0001-0000-0001.md).\n"
        ),
        "data:kbase_x": "# KBase X\n\nA shared collection.\n",
        "author:0000-0001-0000-0001": "# Jane Roe\n\nA contributor.\n",
        # Project pages are real wiki pages now; their links become graph edges too.
        "project:metal_fitness_atlas": (
            "# Metal Fitness Atlas\n\nMapped cross-metal resistance genes.\n\n"
            "## Topics\n\n- [Metal Resistance](../topics/metal-resistance.md)\n"
        ),
    }
    plans = plan_pages(cards, registry=None, authors=authors, collections=collections)
    return plans, cards, authors, collections, page_markdown


def _by_type(records, type_):
    return [r for r in records if r.type == type_]


def test_page_record_converts_frontmatter_and_rewrites_links():
    plans, _cards, _authors, _collections, page_markdown = _fixture()
    records = build_cosma_records(plans, page_markdown=page_markdown)

    topic = _by_type(records, "topic")[0]
    assert topic.title == "Metal Resistance"
    # H1 stripped; title comes from frontmatter
    assert not topic.body.lstrip().startswith("# Metal Resistance")
    # [Label](../data/kbase-x.md) -> [[KBase X|Label]] (title of the target page)
    assert "[[KBase X|KBase X]]" in topic.body
    assert "[[Jane Roe|Jane Roe]]" in topic.body
    assert "](../data" not in topic.body
    # serialized record carries Cosma frontmatter
    text = topic.to_markdown()
    assert text.startswith("---\ntitle: Metal Resistance\ntype: topic\n---")


def test_project_page_is_a_node_with_converted_links():
    plans, _cards, _authors, _collections, page_markdown = _fixture()
    records = build_cosma_records(plans, page_markdown=page_markdown)

    projects = _by_type(records, "project")
    assert [p.filename for p in projects] == ["projects_metal-fitness-atlas.md"]
    project = projects[0]
    assert project.title == "Metal Fitness Atlas"
    # The project page's link to its topic becomes a graph edge.
    assert "[[Metal Resistance|Metal Resistance]]" in project.body


def test_project_title_colliding_with_topic_is_disambiguated():
    # A project whose title slugs to the same id as a topic must not drop a node.
    cards = [_card("functional_dark_matter", "topic:functional-dark-matter", id_="stmt:f1")]
    plans = plan_pages(cards, registry=None, authors={}, collections={})
    page_markdown = {
        "topic:functional-dark-matter": "# Functional Dark Matter\n\nThe topic.\n",
        "project:functional_dark_matter": (
            "# Functional Dark Matter\n\nLead.\n\n## Topics\n\n"
            "- [Functional Dark Matter](../topics/functional-dark-matter.md)\n"
        ),
    }
    records = build_cosma_records(plans, page_markdown=page_markdown)
    by_type = {r.type: r for r in records if r.type in ("topic", "project")}
    assert by_type["topic"].title == "Functional Dark Matter"
    assert by_type["project"].title == "Functional Dark Matter (project)"
    # the topic's inbound link from the project resolves to the disambiguated node title
    assert "[[Functional Dark Matter|Functional Dark Matter]]" in by_type["project"].body
    # the two nodes no longer share a slug
    titles = {r.title for r in records}
    assert len(titles) == len(records)


def test_export_is_deterministic():
    plans, _cards, _authors, _collections, page_markdown = _fixture()
    first = [r.to_markdown() for r in build_cosma_records(plans, page_markdown=page_markdown)]
    second = [r.to_markdown() for r in build_cosma_records(plans, page_markdown=page_markdown)]
    assert first == second
    assert len(first) == 5  # home + topic + data + author + project


def test_config_has_project_type_and_light_theme():
    config = cosma_config(title="Compendium")
    assert config["graph_background_color"] == "#ffffff"
    assert config["files_origin"] == "./src"
    assert "project" in config["record_types"]
    # Cosma rejects an empty description; the default must be non-empty.
    assert config["description"]


def test_write_cosma_project_reads_wiki_and_writes_src_and_config(tmp_path):
    plans, _cards, _authors, _collections, page_markdown = _fixture()
    wiki = tmp_path / "wiki"
    for plan in plans:
        from compendium.pages.artifact import wiki_page_path

        page = wiki / wiki_page_path(plan)
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text(page_markdown[plan.id], encoding="utf-8")

    out = tmp_path / "cosma"
    written = write_cosma_project(plans, wiki_dir=wiki, out_dir=out, title="Compendium")

    assert (out / "config.yml").is_file()
    topic_src = out / "src" / "topics_metal-resistance.md"
    assert topic_src.is_file()
    assert "type: topic" in topic_src.read_text(encoding="utf-8")
    assert (out / "src" / "projects_metal-fitness-atlas.md").is_file()
    assert any(p.name == "config.yml" for p in written)


def test_export_cosma_cli_writes_project(tmp_path):
    import yaml

    kg = tmp_path / "demo.kg.yaml"
    kg.write_text(
        yaml.safe_dump(
            {
                "project": {"id": "proj_x", "title": "Proj X"},
                "statements": [
                    {
                        "id": "stmt:x1",
                        "kind": "finding",
                        "text": "A demo finding.",
                        "confidence": "high",
                        "topics": ["topic:demo"],
                        "entities": [],
                        "evidence": [
                            {"source_project": "proj_x", "source_doc": "REPORT.md", "quote": "A demo finding."}
                        ],
                    }
                ],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    wiki = tmp_path / "wiki"
    (wiki / "topics").mkdir(parents=True)
    (wiki / "projects").mkdir(parents=True)
    (wiki / "index.md").write_text("# Home\n\nSee [Demo](topics/demo.md).\n", encoding="utf-8")
    (wiki / "topics" / "demo.md").write_text("# Demo Topic\n\n## Overview\n\nText.\n", encoding="utf-8")
    (wiki / "projects" / "proj-x.md").write_text(
        "# Proj X\n\nLead.\n\n## Topics\n\n- [Demo Topic](../topics/demo.md)\n", encoding="utf-8"
    )
    empty_root = tmp_path / "projects"
    empty_root.mkdir()
    out = tmp_path / "cosma"

    code = main(
        [
            "export-cosma",
            str(kg),
            "--source-root",
            str(empty_root),
            "--wiki",
            str(wiki),
            "--out",
            str(out),
        ]
    )

    assert code == 0
    assert (out / "config.yml").is_file()
    assert (out / "src" / "topics_demo.md").is_file()
    project_src = (out / "src" / "projects_proj-x.md").read_text(encoding="utf-8")
    assert "[[Demo Topic|Demo Topic]]" in project_src

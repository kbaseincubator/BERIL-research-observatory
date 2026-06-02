"""Tests for the deterministic static render module."""

from __future__ import annotations

import json
import re
from pathlib import Path

from compendium.models import Edge, Graph, Node
from compendium.render.render import render_site, safe


def _sample_graph() -> Graph:
    org = Node(
        id="n:org1",
        type="Organism",
        label="Escherichia coli",
        curie="NCBITaxon:562",
        tier="grounded",
        x=10.0,
        y=20.0,
        provenance=["p1", "p2"],
    )
    f1 = Node(id="n:find1", type="Finding", label="Finding one", tier="asserted",
              provenance=["p1"])
    f2 = Node(id="n:find2", type="Finding", label="Finding two", tier="asserted",
              provenance=["p2"])
    e1 = Edge(s="n:find1", p="about", o="n:org1", tier="grounded", provenance=["p1"],
              evidence=["a:e1"])
    e2 = Edge(s="n:find2", p="about", o="n:org1", tier="grounded", provenance=["p2"],
              evidence=["a:e2"])
    return Graph(nodes=[org, f1, f2], edges=[e1, e2])


def test_render_organism_page_has_both_projects(tmp_path: Path) -> None:
    graph = _sample_graph()
    render_site(graph, tmp_path)

    org_html = tmp_path / "wiki" / f"{safe('n:org1')}.html"
    assert org_html.exists()
    text = org_html.read_text(encoding="utf-8")
    assert "p1" in text
    assert "p2" in text
    assert "Escherichia coli" in text


def test_graph_json_written_with_organism(tmp_path: Path) -> None:
    graph = _sample_graph()
    render_site(graph, tmp_path)

    gjson = tmp_path / "wiki" / "graph.json"
    assert gjson.exists()
    data = json.loads(gjson.read_text(encoding="utf-8"))
    node_ids = {n["data"]["id"] for n in data["nodes"]}
    assert "n:org1" in node_ids


def test_no_broken_internal_links(tmp_path: Path) -> None:
    graph = _sample_graph()
    render_site(graph, tmp_path)

    href_re = re.compile(r'href="([^"#?]+)"')
    for html_file in tmp_path.rglob("*.html"):
        text = html_file.read_text(encoding="utf-8")
        for href in href_re.findall(text):
            if "://" in href:
                continue
            target = (html_file.parent / href).resolve()
            assert target.exists(), f"broken link {href} in {html_file}"


def test_render_returns_pages(tmp_path: Path) -> None:
    graph = _sample_graph()
    pages = render_site(graph, tmp_path)
    assert pages
    slugs = {p.slug for p in pages}
    assert safe("n:org1") in slugs
    for page in pages:
        assert page.fact_hash


def test_narration_synthesis_section(tmp_path: Path) -> None:
    graph = _sample_graph()
    narration = {"n:org1": "This organism is well studied [p1]."}
    render_site(graph, tmp_path, narration=narration)
    text = (tmp_path / "wiki" / f"{safe('n:org1')}.html").read_text(encoding="utf-8")
    assert "Synthesis" in text
    assert "well studied" in text


def test_deterministic(tmp_path: Path) -> None:
    graph = _sample_graph()
    out_a = tmp_path / "a"
    out_b = tmp_path / "b"
    pages_a = render_site(graph, out_a)
    pages_b = render_site(graph, out_b)
    assert [p.fact_hash for p in pages_a] == [p.fact_hash for p in pages_b]
    a_html = (out_a / "wiki" / f"{safe('n:org1')}.html").read_text(encoding="utf-8")
    b_html = (out_b / "wiki" / f"{safe('n:org1')}.html").read_text(encoding="utf-8")
    assert a_html == b_html

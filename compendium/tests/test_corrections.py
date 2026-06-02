"""Corrections: reground overrides curie (id-stable rebuild) and retract removes the edge."""

import json

from compendium import ids
from compendium.corrections import apply_corrections, load_corrections
from compendium.build import build
from compendium.models import (
    TIER_GROUNDED,
    Assertion,
    Correction,
    Entity,
    ProjectKG,
    ProjectMeta,
)


def _make_pkg() -> ProjectKG:
    org_node = ids.node_id("ADP1", "Organism")
    gene_node = ids.node_id("benA", "Gene")
    return ProjectKG(
        project=ProjectMeta(id="proj_a", title="A"),
        entities=[
            Entity(node=org_node, type="Organism", label="ADP1", tier=TIER_GROUNDED),
            Entity(node=gene_node, type="Gene", label="benA",
                   curie="KBase:benA", tier=TIER_GROUNDED),
        ],
        assertions=[
            Assertion(
                id=ids.assertion_id(s=gene_node, p="in_taxon", o=org_node),
                kind="relation", s=gene_node, p="in_taxon", o=org_node,
                polarity="positive", tier=TIER_GROUNDED,
            ),
        ],
    )


def test_reground_overrides_curie_and_survives_rebuild():
    org_node = ids.node_id("ADP1", "Organism")
    correction = Correction(
        id="cor_1", kind="reground", targets=[org_node],
        value={"curie": "NCBITaxon:62977"},
    )

    # build twice from a fresh constructor: id-stable, correction re-binds both times
    for _ in range(2):
        graph = build([_make_pkg()], [correction])
        org = next(n for n in graph.nodes if n.type == "Organism")
        assert org.curie == "NCBITaxon:62977"


def test_retract_removes_targeted_edge():
    pkg = _make_pkg()
    edge_assertion_id = pkg.assertions[0].id

    before = build([_make_pkg()], [])
    assert any(e.p == "in_taxon" for e in before.edges)

    correction = Correction(id="cor_1", kind="retract", targets=[edge_assertion_id])
    after = build([_make_pkg()], [correction])
    assert not any(e.p == "in_taxon" for e in after.edges)


def test_load_corrections_reads_yaml_and_json_sorted(tmp_path):
    (tmp_path / "b.json").write_text(
        json.dumps([{"id": "cor_2", "kind": "retract", "targets": ["a:zzz"]}])
    )
    (tmp_path / "a.yaml").write_text(
        "- id: cor_1\n  kind: reground\n  targets: [n:abc]\n  value: {curie: 'NCBITaxon:1'}\n"
    )
    corrections = load_corrections(tmp_path)
    assert [c.id for c in corrections] == ["cor_1", "cor_2"]


def test_load_corrections_missing_dir_returns_empty(tmp_path):
    assert load_corrections(tmp_path / "nope") == []


def test_apply_retract_drops_assertion():
    pkg = _make_pkg()
    aid = pkg.assertions[0].id
    pkgs, _ = apply_corrections(
        [pkg], [Correction(id="c", kind="retract", targets=[aid])]
    )
    assert pkgs[0].assertions == []

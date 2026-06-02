"""Corrections: v4 names, id-stable rebuilds, and explicit retraction metadata."""

import json

from compendium import ids
from compendium.corrections import apply_corrections, load_corrections
from compendium.build import build
from compendium.models import (
    TIER_ASSERTED,
    TIER_CONFLICT,
    TIER_GROUNDED,
    TIER_RETRACTED,
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


def _make_pkg_with_finding(statement: str = "benA is essential") -> ProjectKG:
    pkg = _make_pkg()
    gene_node = ids.node_id("benA", "Gene")
    pkg.assertions.append(
        Assertion(
            id=ids.assertion_id(statement=statement, project="proj_a"),
            kind="finding",
            statement=statement,
            entities=[gene_node],
            tier=TIER_GROUNDED,
        )
    )
    return pkg


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


def test_fix_statement_preserves_assertion_id_across_rebuilds():
    finding_id = ids.assertion_id(statement="benA is essential", project="proj_a")
    correction = Correction(
        id="cor_1",
        kind="fix-statement",
        targets=[finding_id],
        value={"statement": "benA is conditionally essential"},
    )

    for _ in range(2):
        graph = build([_make_pkg_with_finding()], [correction])
        finding = next(n for n in graph.nodes if n.id == finding_id)
        assert finding.label == "benA is conditionally essential"


def test_retract_removes_targeted_edge():
    pkg = _make_pkg()
    edge_assertion_id = pkg.assertions[0].id

    before = build([_make_pkg()], [])
    assert any(e.p == "in_taxon" for e in before.edges)

    correction = Correction(id="cor_1", kind="retract", targets=[edge_assertion_id])
    after = build([_make_pkg()], [correction])
    assert not any(e.p == "in_taxon" for e in after.edges)


def test_v4_correction_kinds_apply_to_current_model():
    pkg = _make_pkg_with_finding()
    org_node = ids.node_id("ADP1", "Organism")
    gene_node = ids.node_id("benA", "Gene")
    relation_id = ids.assertion_id(s=gene_node, p="in_taxon", o=org_node)
    finding_id = ids.assertion_id(statement="benA is essential", project="proj_a")

    pkgs, force_merge_pairs = apply_corrections(
        [pkg],
        [
            Correction(
                id="cor_4",
                kind="fix-qualifier",
                targets=[finding_id],
                value={"extractor": {"agent_type": "curator", "confidence": 1.0}},
            ),
            Correction(id="cor_3", kind="resolve-conflict", targets=[finding_id]),
            Correction(id="cor_5", kind="force-merge", targets=[org_node, gene_node]),
            Correction(id="cor_6", kind="force-split", targets=[org_node, gene_node]),
            Correction(id="cor_2", kind="mark-conflict", targets=[relation_id]),
            Correction(
                id="cor_1",
                kind="reground-entity",
                targets=[org_node],
                value={"curie": "NCBITaxon:62977"},
            ),
        ],
    )

    org = next(e for e in pkgs[0].entities if e.node == org_node)
    relation = next(a for a in pkgs[0].assertions if a.id == relation_id)
    finding = next(a for a in pkgs[0].assertions if a.id == finding_id)
    assert org.curie == "NCBITaxon:62977"
    assert relation.tier == TIER_CONFLICT
    assert finding.tier == TIER_GROUNDED
    assert finding.extractor == {"agent_type": "curator", "confidence": 1.0}
    assert force_merge_pairs == [(org_node, gene_node)]


def test_promote_and_demote_default_tiers():
    pkg = _make_pkg_with_finding()
    relation_id = pkg.assertions[0].id
    finding_id = pkg.assertions[1].id

    pkgs, _ = apply_corrections(
        [pkg],
        [
            Correction(id="cor_1", kind="demote", targets=[relation_id]),
            Correction(id="cor_2", kind="promote", targets=[finding_id]),
        ],
    )

    assert pkgs[0].assertions[0].tier == TIER_ASSERTED
    assert pkgs[0].assertions[1].tier == TIER_GROUNDED


def test_load_corrections_reads_yaml_and_json_sorted(tmp_path):
    (tmp_path / "b.json").write_text(
        json.dumps(
            [
                {"id": "cor_3", "kind": "retract", "targets": ["a:zzz"]},
                {"id": "cor_1", "kind": "reground-entity", "targets": ["n:abc"]},
            ]
        )
    )
    (tmp_path / "a.yaml").write_text(
        "- id: cor_2\n  kind: reground\n  targets: [n:abc]\n  value: {curie: 'NCBITaxon:1'}\n"
    )
    corrections = load_corrections(tmp_path)
    assert [c.id for c in corrections] == ["cor_1", "cor_2", "cor_3"]


def test_load_corrections_missing_dir_returns_empty(tmp_path):
    assert load_corrections(tmp_path / "nope") == []


def test_apply_retract_drops_assertion():
    pkg = _make_pkg()
    aid = pkg.assertions[0].id
    pkgs, _ = apply_corrections(
        [pkg], [Correction(id="c", kind="retract", targets=[aid])]
    )
    assert pkgs[0].assertions == []
    correction_metadata = pkgs[0].project.extraction["corrections"]
    assert correction_metadata[0]["target"] == aid
    assert correction_metadata[0]["assertion"]["tier"] == TIER_RETRACTED

"""Idempotency: build + KGX export are byte-stable across input shuffles."""

import copy
import random

from compendium import ids
from compendium.build import build, to_kgx
from compendium.models import (
    TIER_GROUNDED,
    Assertion,
    Correction,
    Entity,
    ProjectKG,
    ProjectMeta,
)


def _fixture_pkgs() -> list[ProjectKG]:
    org_node = ids.node_id("ADP1", "Organism")
    gene_node = ids.node_id("benA", "Gene")
    org2_node = ids.node_id("Acinetobacter baylyi ADP1", "Organism")

    pkg_a = ProjectKG(
        project=ProjectMeta(id="proj_a", title="A"),
        entities=[
            Entity(node=org_node, type="Organism", label="ADP1",
                   curie="NCBITaxon:62977", tier=TIER_GROUNDED),
            Entity(node=gene_node, type="Gene", label="benA",
                   curie="KBase:benA", tier=TIER_GROUNDED),
        ],
        assertions=[
            Assertion(
                id=ids.assertion_id(s=gene_node, p="in_taxon", o=org_node),
                kind="relation", s=gene_node, p="in_taxon", o=org_node,
                polarity="positive", tier=TIER_GROUNDED,
            ),
            Assertion(
                id=ids.assertion_id(statement="benA is essential", project="proj_a"),
                kind="finding", statement="benA is essential",
                entities=[gene_node], tier=TIER_GROUNDED,
            ),
        ],
    )
    pkg_b = ProjectKG(
        project=ProjectMeta(id="proj_b", title="B"),
        entities=[
            Entity(node=org2_node, type="Organism", label="Acinetobacter baylyi ADP1",
                   curie="NCBITaxon:62977", tier=TIER_GROUNDED),
        ],
        assertions=[
            Assertion(
                id=ids.assertion_id(statement="genome is reduced", project="proj_b"),
                kind="finding", statement="genome is reduced",
                entities=[org2_node], tier=TIER_GROUNDED,
            ),
        ],
    )
    return [pkg_a, pkg_b]


def _fixture_corrections() -> list[Correction]:
    return [
        Correction(id="cor_1", kind="demote",
                   targets=[ids.assertion_id(statement="benA is essential", project="proj_a")],
                   value={"tier": "asserted"}),
        Correction(id="cor_2", kind="reground",
                   targets=[ids.node_id("benA", "Gene")],
                   value={"curie": "KEGG:K00001"}),
    ]


def test_build_and_kgx_byte_identical_across_shuffles(tmp_path):
    rng = random.Random(0)
    hashes = []
    node_bytes = []
    edge_bytes = []

    for i in range(5):
        pkgs = copy.deepcopy(_fixture_pkgs())
        rng.shuffle(pkgs)
        for pkg in pkgs:
            rng.shuffle(pkg.entities)
            rng.shuffle(pkg.assertions)
        corrections = copy.deepcopy(_fixture_corrections())

        graph = build(pkgs, corrections)
        hashes.append(ids.graph_hash(graph))

        out = tmp_path / f"run_{i}"
        to_kgx(graph, out)
        node_bytes.append((out / "nodes.tsv").read_bytes())
        edge_bytes.append((out / "edges.tsv").read_bytes())

    assert len(set(hashes)) == 1, hashes
    assert len(set(node_bytes)) == 1
    assert len(set(edge_bytes)) == 1

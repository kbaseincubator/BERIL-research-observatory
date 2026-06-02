"""Assemble per-project KGs into one canonical, laid-out Graph and export to KGX."""

from __future__ import annotations

import pathlib
from typing import Optional

from ..corrections import apply_corrections
from ..models import (
    TIER_CONFLICT,
    Correction,
    Edge,
    Graph,
    Node,
    ProjectKG,
)
from .canonicalize import canonicalize
from .layout import layout

# assertion kinds that become synthesis nodes (kind -> Node.type)
_SYNTHESIS_KINDS = {
    "finding": "Finding",
    "opportunity": "Opportunity",
    "claim": "Claim",
    "hypothesis": "Hypothesis",
    "direction": "Direction",
}


def build(
    pkgs: list[ProjectKG],
    corrections: Optional[list[Correction]] = None,
    layout_seed: int = 0,
) -> Graph:
    """Build the canonical, laid-out graph from project KGs and curator corrections."""
    pkgs, force_merge_pairs = apply_corrections(pkgs, corrections or [])
    cmap, nodes = canonicalize(pkgs, force_merge_pairs)

    nodes_by_id: dict[str, Node] = {n.id: n for n in nodes}

    # (1) relation assertions -> edges, deduped by (s, p, o)
    edge_map: dict[tuple[str, str, str], Edge] = {}
    for pkg in pkgs:
        pid = pkg.project.id
        for a in pkg.assertions:
            if a.kind != "relation":
                continue
            s = cmap.get(a.s, a.s)
            o = cmap.get(a.o, a.o)
            key = (s, a.p, o)
            existing = edge_map.get(key)
            if existing is None:
                edge_map[key] = Edge(
                    s=s,
                    p=a.p,
                    o=o,
                    tier=a.tier,
                    polarity=a.polarity,
                    evidence=[a.id],
                    provenance=[pid],
                )
            else:
                if a.id not in existing.evidence:
                    existing.evidence.append(a.id)
                if pid not in existing.provenance:
                    existing.provenance.append(pid)
    edges = list(edge_map.values())

    # (2) synthesis assertions -> synthesis nodes + 'about' edges to referenced entities
    for pkg in pkgs:
        pid = pkg.project.id
        for a in pkg.assertions:
            ntype = _SYNTHESIS_KINDS.get(a.kind)
            if ntype is None:
                continue
            snode = Node(
                id=a.id,
                type=ntype,
                label=a.statement or "",
                tier=a.tier,
                provenance=[pid],
            )
            nodes.append(snode)
            nodes_by_id[snode.id] = snode
            for ent in a.entities:
                target = cmap.get(ent, ent)
                edges.append(
                    Edge(
                        s=a.id,
                        p="about",
                        o=target,
                        tier=a.tier,
                        evidence=[a.id],
                        provenance=[pid],
                    )
                )

    # (3) conflict detection: same (s, o), same p, opposite polarity
    by_spo: dict[tuple[str, str, str], list[Edge]] = {}
    for e in edges:
        by_spo.setdefault((e.s, e.p, e.o), []).append(e)
    conflict_nodes: list[Node] = []
    seen_conflict_pairs: set[tuple[str, str, str]] = set()
    for (s, p, o), group in by_spo.items():
        polarities = {e.polarity for e in group}
        if "positive" in polarities and "negative" in polarities:
            for e in group:
                e.tier = TIER_CONFLICT
            pair = (s, p, o)
            if pair not in seen_conflict_pairs:
                seen_conflict_pairs.add(pair)
                cid = "c:" + p + ":" + s + ":" + o
                cnode = Node(
                    id=cid,
                    type="Conflict",
                    label=f"Conflict on {p} between {s} and {o}",
                    tier=TIER_CONFLICT,
                    provenance=sorted({pid for e in group for pid in e.provenance}),
                )
                conflict_nodes.append(cnode)
    nodes.extend(conflict_nodes)

    graph = Graph(nodes=nodes, edges=edges)

    # (4) layout
    graph = layout(graph, seed=layout_seed)

    # (5) deterministic sort
    graph.nodes.sort(key=lambda n: n.id)
    graph.edges.sort(key=lambda e: (e.s, e.p, e.o))
    return graph


def to_kgx(graph: Graph, out_dir: pathlib.Path) -> None:
    """Write KGX ``nodes.tsv`` and ``edges.tsv`` (rows sorted, provenance joined with '|')."""
    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    node_rows = sorted(
        "\t".join(
            [
                n.id,
                n.type,
                n.label,
                n.curie or "",
                n.tier,
                "|".join(n.provenance),
            ]
        )
        for n in graph.nodes
    )
    nodes_text = "id\tcategory\tname\tcurie\ttier\tprovenance\n"
    nodes_text += "".join(row + "\n" for row in node_rows)
    (out_dir / "nodes.tsv").write_text(nodes_text, encoding="utf-8")

    edge_rows = sorted(
        "\t".join([e.s, e.p, e.o, e.tier, "|".join(e.provenance)]) for e in graph.edges
    )
    edges_text = "subject\tpredicate\tobject\ttier\tprovenance\n"
    edges_text += "".join(row + "\n" for row in edge_rows)
    (out_dir / "edges.tsv").write_text(edges_text, encoding="utf-8")

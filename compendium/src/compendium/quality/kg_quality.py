"""Deterministic quality metrics for the canonical knowledge graph.

No LLM, no network — pure functions over a :class:`compendium.models.Graph`.
"""

from __future__ import annotations

from collections import Counter

from ..models import BIOLOGY_TYPES, Graph

_BIOLOGY = frozenset(BIOLOGY_TYPES)


def assess_kg(graph: Graph) -> dict:
    """Compute structural / grounding / provenance metrics for the canonical KG.

    Parameters
    ----------
    graph
        The canonical :class:`~compendium.models.Graph`.

    Returns
    -------
    dict
        Metrics keyed by name (see module/design spec).
    """
    node_ids = {n.id for n in graph.nodes}

    nodes_by_type = Counter(n.type for n in graph.nodes)
    edges_by_predicate = Counter(e.p for e in graph.edges)
    node_tier_distribution = Counter(n.tier for n in graph.nodes)
    edge_tier_distribution = Counter(e.tier for e in graph.edges)

    # grounding_rate: fraction of BIOLOGY-type nodes that carry a curie.
    biology_nodes = [n for n in graph.nodes if n.type in _BIOLOGY]
    grounded = sum(1 for n in biology_nodes if n.curie)
    grounding_rate = grounded / len(biology_nodes) if biology_nodes else 0.0

    # provenance_completeness: fraction of edges with >= 1 backing assertion/evidence id.
    with_prov = sum(1 for e in graph.edges if e.evidence)
    provenance_completeness = with_prov / len(graph.edges) if graph.edges else 0.0

    # orphan_nodes: node ids that are not an endpoint of any edge.
    endpoints = set()
    dangling_edges = 0
    for e in graph.edges:
        endpoints.add(e.s)
        endpoints.add(e.o)
        if e.s not in node_ids or e.o not in node_ids:
            dangling_edges += 1
    orphan_nodes = sum(1 for n in graph.nodes if n.id not in endpoints)

    # cross_project_edges: edge spans >= 2 projects, either by its own provenance
    # or because an endpoint node has >= 2 distinct provenance entries.
    node_by_id = {n.id: n for n in graph.nodes}
    cross_project_edges = 0
    for e in graph.edges:
        projects = set(e.provenance)
        for endpoint in (e.s, e.o):
            n = node_by_id.get(endpoint)
            if n:
                projects.update(n.provenance)
        if len(projects) >= 2:
            cross_project_edges += 1

    return {
        "n_nodes": len(graph.nodes),
        "n_edges": len(graph.edges),
        "nodes_by_type": dict(nodes_by_type),
        "edges_by_predicate": dict(edges_by_predicate),
        "node_tier_distribution": dict(node_tier_distribution),
        "edge_tier_distribution": dict(edge_tier_distribution),
        "grounding_rate": grounding_rate,
        "provenance_completeness": provenance_completeness,
        "orphan_nodes": orphan_nodes,
        "dangling_edges": dangling_edges,
        "cross_project_edges": cross_project_edges,
    }

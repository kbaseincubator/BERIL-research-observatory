"""Union-find canonicalization of entities across projects into canonical nodes.

Two entities merge if they share a non-null curie or are an explicit force-merge pair. The cluster's
canonical id prefers a member carrying a curie, else the lexicographically smallest node id.
"""

from __future__ import annotations

from typing import Optional

from ..models import TIER_GROUNDED, Entity, Node, ProjectKG


class _UnionFind:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}

    def find(self, x: str) -> str:
        self.parent.setdefault(x, x)
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[x] != root:
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        # keep the lexicographically smaller root for determinism
        lo, hi = (ra, rb) if ra < rb else (rb, ra)
        self.parent[hi] = lo


def canonicalize(
    pkgs: list[ProjectKG], force_merge_pairs: Optional[list[tuple[str, str]]] = None
) -> tuple[dict[str, str], list[Node]]:
    """Cluster entities and return ``(node_id -> canonical_id, list[Node])``."""
    # gather all entities with their contributing project id
    members: list[tuple[Entity, str]] = []
    for pkg in pkgs:
        for e in pkg.entities:
            members.append((e, pkg.project.id))

    uf = _UnionFind()
    for e, _ in members:
        uf.find(e.node)

    # union entities sharing a non-null curie
    by_curie: dict[str, list[str]] = {}
    for e, _ in members:
        if e.curie:
            by_curie.setdefault(e.curie, []).append(e.node)
    for nodes in by_curie.values():
        for other in nodes[1:]:
            uf.union(nodes[0], other)

    # union explicit force-merge pairs
    for a, b in force_merge_pairs or []:
        uf.find(a)
        uf.find(b)
        uf.union(a, b)

    # cluster members by root
    clusters: dict[str, list[tuple[Entity, str]]] = {}
    for e, pid in members:
        clusters.setdefault(uf.find(e.node), []).append((e, pid))

    cmap: dict[str, str] = {}
    nodes: list[Node] = []
    for cluster in clusters.values():
        ent_nodes = sorted({e.node for e, _ in cluster})
        grounded_nodes = sorted({e.node for e, _ in cluster if e.curie})
        canonical_id = grounded_nodes[0] if grounded_nodes else ent_nodes[0]

        for e, _ in cluster:
            cmap[e.node] = canonical_id

        # representative: the member whose node id == canonical_id
        rep = next(e for e, _ in cluster if e.node == canonical_id)
        tier = TIER_GROUNDED if any(e.tier == TIER_GROUNDED for e, _ in cluster) else "asserted"
        provenance = sorted({pid for _, pid in cluster})
        nodes.append(
            Node(
                id=canonical_id,
                type=rep.type,
                label=rep.label,
                curie=rep.curie,
                tier=tier,
                provenance=provenance,
            )
        )

    nodes.sort(key=lambda n: n.id)
    return cmap, nodes

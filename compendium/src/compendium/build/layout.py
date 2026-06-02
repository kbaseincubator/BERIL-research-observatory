"""Deterministic 2-D layout via a pure-Python seeded spring (Fruchterman-Reingold) algorithm.

We avoid networkx's ``spring_layout`` because it pulls in numpy (not a declared dependency). This
implementation is fully deterministic given a seed: identical inputs and seed yield identical
coordinates, which keeps the build idempotent.
"""

from __future__ import annotations

import math
import random

import networkx as nx

from ..models import Graph

_ITERATIONS = 50


def layout(graph: Graph, seed: int = 0) -> Graph:
    """Assign deterministic ``x``/``y`` to each node (rounded to 4 dp). Empty-safe."""
    if not graph.nodes:
        return graph

    g = nx.Graph()
    for n in graph.nodes:
        g.add_node(n.id)
    for e in graph.edges:
        if e.s in g and e.o in g:
            g.add_edge(e.s, e.o)

    pos = _spring_layout(g, seed=seed)
    for n in graph.nodes:
        x, y = pos[n.id]
        n.x = round(x, 4)
        n.y = round(y, 4)
    return graph


def _spring_layout(g: nx.Graph, seed: int) -> dict[str, tuple[float, float]]:
    """Seeded Fruchterman-Reingold layout in pure Python (deterministic)."""
    nodes = sorted(g.nodes())
    n = len(nodes)
    if n == 1:
        return {nodes[0]: (0.0, 0.0)}

    rng = random.Random(seed)
    pos = {node: (rng.uniform(-1.0, 1.0), rng.uniform(-1.0, 1.0)) for node in nodes}
    k = math.sqrt(1.0 / n)
    t = 0.1  # initial temperature
    dt = t / (_ITERATIONS + 1)

    adj = {node: set(g.neighbors(node)) for node in nodes}

    for _ in range(_ITERATIONS):
        disp = {node: [0.0, 0.0] for node in nodes}
        for i, u in enumerate(nodes):
            ux, uy = pos[u]
            for v in nodes[i + 1:]:
                vx, vy = pos[v]
                dx, dy = ux - vx, uy - vy
                dist = math.hypot(dx, dy) or 1e-9
                # repulsion
                rep = (k * k) / dist
                rx, ry = (dx / dist) * rep, (dy / dist) * rep
                disp[u][0] += rx
                disp[u][1] += ry
                disp[v][0] -= rx
                disp[v][1] -= ry
                # attraction for connected nodes
                if v in adj[u]:
                    att = (dist * dist) / k
                    ax, ay = (dx / dist) * att, (dy / dist) * att
                    disp[u][0] -= ax
                    disp[u][1] -= ay
                    disp[v][0] += ax
                    disp[v][1] += ay
        for node in nodes:
            dnx, dny = disp[node]
            d = math.hypot(dnx, dny) or 1e-9
            limited = min(d, t)
            x, y = pos[node]
            pos[node] = (x + (dnx / d) * limited, y + (dny / d) * limited)
        t -= dt

    return pos

# Compendium

A **deterministic, knowledge-graph-centered scientific aggregation wiki** distilled from the BERIL
Research Observatory `projects/` corpus — distinct from the hand-authored `atlas/`.

Design spec: [`docs/kg-wiki/2026-06-01-kg-wiki-design.md`](../docs/kg-wiki/2026-06-01-kg-wiki-design.md) ·
Plan: [`docs/superpowers/plans/2026-06-01-compendium.md`](../docs/superpowers/plans/2026-06-01-compendium.md)

## What it is

The **deterministic core** (pure Python, no LLM, runs headless) turns project REPORTs into a typed,
content-addressed knowledge graph and renders a static wiki:

```
audit -> extract (Stage-1) -> ground -> verify (tiers) -> canonicalize -> assemble (KGX) -> render -> quality
```

- **Content-addressed identity** (`ids.py`): node id = `n:hash(label|type)`, assertion id =
  `a:hash(s|p|o)` — stable across re-extraction, so the build is idempotent and corrections re-bind.
- **Honest entities-only tiers** (`grounded` / `asserted` / `conflict`) — no tier claims a relation is *true*.
- **Reproducible build**: same inputs → byte-identical KGX (idempotency test shuffles ingest order & merge timing).
- **LLM steps are skills** (`skills/`) that dispatch subagents (subscription tokens), never on the render path.

## Run

```bash
uv run --directory compendium --group test pytest          # 57 tests
uv run --directory compendium compendium all \
    --projects acinetobacter_adp1_explorer adp1_deletion_phenotypes \
    --projects-dir ../projects --out out
open compendium/out/site/index.html                         # the wiki
```

Outputs: `out/nodes.tsv`, `out/edges.tsv` (KGX), `out/site/` (static wiki + `wiki/graph.json`),
`out/quality.json` (KG + wiki quality), `kg/<project>.kg.yaml` (per-project KG).

## Layout

| Path | Responsibility |
|---|---|
| `src/compendium/models.py`, `ids.py` | shared data contracts + identity/canonicalization |
| `audit.py` | Phase-0 corpus-structure audit |
| `extract/structural.py` | Stage-1 deterministic parser → `ProjectKG` |
| `ground/` | dictionary + regex grounder (Gilda/OGER = future swap-in) |
| `verify/` | auto-verification → assertion tiers |
| `build/`, `corrections.py` | canonicalize, assemble (KGX), layout, correction overlay |
| `render/` | deterministic static site (Cytoscape preset + Mermaid) |
| `quality/` | KG + wiki quality metrics |
| `skills/` | LLM steps: `kg-extract`, `kg-synthesize`, `kg-correct`, `kg-narrate` |

## Status (tracer)

Deterministic core complete & tested on 2 ADP1 projects (29 nodes / 29 edges, 0 orphans / dangling /
broken links, shared ADP1 organism hub, 100% provenance). Deferred (clear seams): real Gilda/OGER
grounding, full corpus backfill, FastAPI integration, `/submit` hook, hypothesis overlay.

# Compendium

A **statement-card-centered synthesis wiki** distilled from the BERIL Research Observatory
`projects/` corpus. It replaces the current generated `atlas/` shape with a richer KG-backed
human wiki.

Design spec: [`docs/kg-wiki/2026-06-02-synthesis-wiki-design.md`](../docs/kg-wiki/2026-06-02-synthesis-wiki-design.md) ·
Plan: [`docs/superpowers/plans/2026-06-02-synthesis-wiki.md`](../docs/superpowers/plans/2026-06-02-synthesis-wiki.md)

## What it is

The deterministic Python core never calls an LLM. It builds context packs, validates statement cards,
assembles the graph, plans pages, renders the static site, and reports quality. Skills orchestrate
LLM extraction and prose synthesis on top of those deterministic scripts.

```
audit -> context-pack -> validate cards -> assemble graph -> plan pages -> render -> quality
```

- **Statement cards** are the extraction, correction, graph, and synthesis unit.
- **Synthesis pages** are the primary human reading path: home, topics, claims, conflicts,
  opportunities, directions, hypotheses, projects, and entities.
- **Typed edge classes** separate scientific, provenance, navigation, derivation, and review links.
- **Reproducible build**: same inputs → byte-identical KGX (idempotency test shuffles ingest order & merge timing).
- **LLM steps are skills** (`skills/`) that publish validated extraction/prose artifacts, never live render calls.

## Run

```bash
uv run --directory compendium --group test pytest
uv run --directory compendium compendium page-artifact \
    fixtures/statement_cards/adp1_three_project_ingestion.yaml \
    --page-id home --markdown out/drafts/home.md --out wiki \
    --model <model-id> --prompt-hash <prompt-hash>
# Repeat page-artifact for every changed page context, reusing unchanged wiki pages.
uv run --directory compendium compendium render-markdown \
    fixtures/statement_cards/adp1_three_project_ingestion.yaml --out wiki
open compendium/wiki/index.md                               # linked Markdown wiki

uv run --directory compendium compendium tracer --out out/adp1-tracer
open compendium/out/adp1-tracer/page-contexts/home.prompt.md # deterministic prompt/context bundle

uv run --directory compendium compendium all \
    --projects acinetobacter_adp1_explorer adp1_deletion_phenotypes \
    --projects-dir ../projects --out out
open compendium/out/site/index.html                         # legacy deterministic tracer wiki
```

Current commands still support the earlier deterministic tracer. The v4 plan adds context-pack,
statement-card validation, page planning, and skills-first ingestion commands.

## Layout

| Path | Responsibility |
|---|---|
| `src/compendium/models.py`, `ids.py` | shared data contracts + identity/canonicalization |
| `context_pack.py` | deterministic context packs for ingestion skills |
| `audit.py` | Phase-0 corpus-structure audit |
| `extract/structural.py` | Stage-1 deterministic parser → `ProjectKG` |
| `ground/` | dictionary + regex grounder (Gilda/OGER = future swap-in) |
| `verify/` | auto-verification → assertion tiers |
| `build/`, `corrections.py` | canonicalize, assemble (KGX), layout, correction overlay |
| `render/` | deterministic static site (Cytoscape preset + Mermaid) |
| `quality/` | KG + wiki quality metrics |
| `skills/` | LLM orchestration: ingest, synthesize pages, curate, backfill, review queue |
| `wiki/` | single human-facing Markdown wiki; page manifests live under `wiki/.manifests/` |
| `out/page-contexts/` | ignored deterministic page contexts/prompts for LLM page synthesis |

## Status (tracer)

The older deterministic core is a useful scaffold, but future work follows the v4 statement-card
plan. Initial implementation target: two ADP1 projects with generated home/topic/claim/opportunity/
project/entity pages and a typed graph with no dangling edges or broken links.

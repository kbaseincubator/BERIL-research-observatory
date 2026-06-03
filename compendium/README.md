# Compendium

A **statement-card-centered synthesis wiki** distilled from the BERIL Research Observatory
`projects/` corpus. It replaces the current generated `atlas/` shape with a richer KG-backed
human wiki.

Design spec: [`docs/kg-wiki/2026-06-02-synthesis-wiki-design.md`](../docs/kg-wiki/2026-06-02-synthesis-wiki-design.md)

## What it is

The deterministic Python core never calls an LLM. It builds context packs, validates statement cards,
assembles the statement graph, plans pages, validates and publishes the Markdown wiki, and reports
quality. Skills orchestrate LLM extraction and prose synthesis on top of those deterministic scripts.

```
audit/context-pack -> validate cards -> statement-graph -> plan-pages -> wiki-contexts
  -> page-artifact (LLM-authored, validated) -> render-markdown -> quality-synthesis/review-queue
```

- **Statement cards** are the extraction, correction, graph, and synthesis unit.
- **Synthesis pages** are the primary human reading path: home, topics, claims, conflicts,
  opportunities, directions, hypotheses, projects, and entities.
- **Typed edge classes** separate scientific, provenance, navigation, derivation, and review links.
- **Reproducible build**: deterministic statement graph and page plans — same statement cards → identical graph artifacts, page plans, and published wiki regardless of input order.
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
```

The `kg-generate-wiki` skill orchestrates this workflow end-to-end; `tracer` runs the deterministic
graph/context/quality steps over the committed ADP1 fixture with no LLM.

## Layout

| Path | Responsibility |
|---|---|
| `src/compendium/models.py`, `ids.py` | shared data contracts + identity/canonicalization |
| `context_pack.py` | deterministic context packs for ingestion skills |
| `audit.py` | Phase-0 corpus-structure audit (also feeds `context_pack`) |
| `extract/structural.py` | Stage-1 deterministic parser → `ProjectKG` scaffold for context packs |
| `build/statement_graph.py` | typed statement-card graph + `nodes.tsv`/`edges.tsv`/`graph.json` artifacts |
| `pages/` | deterministic page plans + bounded LLM page contexts + authored-page validation |
| `render/markdown.py` | deterministic Markdown wiki publisher (validates authored pages, writes `graph.md`) |
| `quality/` | statement-card synthesis quality, review queue, and quality dashboard |
| `skills/` | LLM orchestration: ingest, generate/synthesize pages, curate, backfill, review queue |
| `wiki/` | single human-facing Markdown wiki; page manifests live under `wiki/.manifests/` |
| `out/page-contexts/` | ignored deterministic page contexts/prompts for LLM page synthesis |

## Status (tracer)

The tracer target is two ADP1 projects with LLM-authored home/topic/claim/opportunity/project/entity
pages and a typed statement graph with no dangling edges or broken links. The canonical human-facing
output is the connected Markdown wiki at `compendium/wiki/` (entry point `wiki/index.md`); there is no
HTML wiki export.

# Compendium

A **topic-centered synthesis wiki** distilled from the BERIL Research Observatory `projects/` corpus.
It connects projects through cross-cutting **topics** (Maps of Content), plus **author** and **shared-data**
pages — a lightweight link layer, not a formal knowledge graph. The deterministic Python core never calls
an LLM; three LLM steps (extraction, reconciliation, page authoring) run as skills on top of it.

## Pipeline

```
projects/* ─[D] context-pack ─▶ context-packs/   (audit + source excerpts + authors + candidate terms)
                                   │
              ─[LLM] kg-extract ──▶ kg/<project>.kg.yaml      (per-project statement cards; raw slugs)
                                   │
   ALL cards ─[LLM] kg-reconcile ─▶ registry.yaml             (★ global: canonical topics/entities + aliases)
                                   │
   cards + registry ─[D] plan-pages + wiki-contexts ─▶ page contexts   (topic / data / author / home)
                                   │
              ─[LLM] kg-write ────▶ wiki/*.md                 (cited prose; provenance in a Sources section)
                                   │
              ─[D] render-markdown + check ─▶ published wiki + integrity gate
                                   │
              ─[D] export-cosma + cosma modelize ─▶ cosma/cosmoscope.html (graph + wiki viewer)
```

- **Deterministic (no model):** `context-pack`, `validate-kg`, `plan-pages`, `wiki-contexts`,
  `page-context`, `render-markdown`, `check`, `export-cosma`, `validate-card`, `validate-page-plan`. The author and
  shared-data connections are deterministic too (no LLM): authors join on ORCID from README `## Authors`
  blocks; shared data joins on the canonical collection ids in `ui/config/collections.yaml`.
- **LLM steps are skills** under `skills/`: `kg-extract` (per project), `kg-reconcile` (once, global,
  **autonomous** — owns the topic vocabulary, no human gate), `kg-write` (per page), and `kg-wiki` (the
  orchestrator that chains the whole flow). `kg-wiki` is the only skill a user normally invokes.
- **Reproducible:** same statement cards + registry → identical page plans and published wiki.

## Data model

One small YAML contract (`SCHEMA.md`) plus a global `registry.yaml`:

- **Statement card** (`kg/<project>.kg.yaml`): `id`, `kind`, `text`, `confidence`, raw per-project
  `topics`/`entities`, simple `links.{supports,contradicts,refines}`, and evidence anchors with exact
  source quotes.
- **Registry** (`registry.yaml`): canonical `topics` and `entities`, each with `aliases`. The raw
  per-project topic slugs map onto ~12 canonical themes through topic aliases — this is the cross-project
  merge. The registry is **additive**: `plan` resolves slugs via `compendium.registry.Registry`; cards are
  never rewritten.

## Page types (the reader-facing wiki)

`wiki/index.md` (home: topic + author + data maps) · `wiki/topics/*` (the backbone — Overview, Key Claims,
Conflicts & Caveats, Open Directions, with cross-links to adjacent topics, shared data, and authors) ·
`wiki/data/*` (one per BERDL collection: which projects share it) · `wiki/authors/*` (one per ORCID:
projects + topics). Claims/conflicts/opportunities are **sections inside topic pages**, not standalone pages.

## Run

```bash
uv run --directory compendium --group test pytest        # deterministic core (no LLM)

# End-to-end is driven by the kg-wiki skill in Claude Code / Codex. The deterministic steps it shells out to:
cd compendium
uv run compendium context-pack ../projects/<id> --out context-packs/<id>.json     # → kg-extract authors cards
uv run compendium validate-kg fixtures/statement_cards/adp1_tracer.yaml
uv run compendium plan-pages <kg> --source-root ../projects --out out/plans.json   # 4 page types
uv run compendium wiki-contexts <kg> --source-root ../projects --out out/page-contexts
#   → kg-write authors each wiki/<page>.md from its context, published via page-artifact
uv run compendium render-markdown <kg> --source-root ../projects --out wiki        # validate + publish
uv run compendium check --wiki wiki                                                # link + citation integrity gate
open compendium/wiki/index.md

# Graph + wiki viewer (Cosma): deterministic records/config, then a one-shot Node build.
uv run compendium export-cosma <kg> --source-root ../projects --wiki wiki --out cosma  # reader-graph records + config.yml
(cd cosma && npx -y @graphlab-fr/cosma modelize)                                       # → cosma/cosmoscope.html (self-contained)
open compendium/cosma/cosmoscope.html
```

`plan-pages` / `wiki-contexts` / `render-markdown` auto-load `compendium/registry.yaml` when present and
build the author/collection indexes from `--source-root` + `ui/config/collections.yaml`.

## Layout

| Path | Responsibility |
|---|---|
| `src/compendium/models.py` | statement-card + page-plan data contracts |
| `src/compendium/audit.py`, `context_pack.py` | deterministic source audit + bounded context packs for extraction |
| `src/compendium/people.py` | author index (ORCID) from README `## Authors` |
| `src/compendium/data_index.py` | shared-collection index from `ui/config/collections.yaml` |
| `src/compendium/registry.py` | additive canonical topic/entity resolution from `registry.yaml` |
| `src/compendium/pages/` | deterministic page plans (topic/data/author/home) + bounded page contexts + authored-page validation |
| `src/compendium/render/markdown.py` | Markdown wiki publisher (validates authored pages) |
| `src/compendium/render/cosma.py` | Cosma export: reader-graph records (topic/project/data/author) + config for the cosmoscope viewer |
| `src/compendium/check.py` | link + citation integrity check (the final gate) |
| `skills/` | LLM orchestration: `kg-extract`, `kg-reconcile`, `kg-write`, `kg-wiki` |
| `wiki/` | the human-facing Markdown wiki (entry point `wiki/index.md`); manifests under `wiki/.manifests/` |

`tests/test_wiki_readability.py` is a smoke test, not a prose judge. It guards against obvious
regressions: missing introductions, missing sources, missing wiki links, and leaked graph jargon.

This README is the single source of truth for the pipeline. The ideology and methodology (why a topic-MOC
instead of a formal KG, what a topic is, the two-pass reconciliation) live in
`../docs/kg-wiki/methodology.md`; the design decisions and build history live in
`../docs/kg-wiki/2026-06-15-kg-wiki-redesign.md`.

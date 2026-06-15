---
name: kg-extract
description: Extract thin statement cards for ONE BERIL project from its deterministic context pack. Runs the zero-LLM context-pack builder, then the LLM emits validated statement-card YAML to kg/<id>.kg.yaml using only the context pack. Validates by loading the cards with plan-pages.
---

# kg-extract

Extract one project at a time, usually `projects/<project_id>`. The output is a validated
statement-card project KG (`compendium/kg/<project_id>.kg.yaml`), not prose. The `compendium`
commands are deterministic and never call a model; this skill uses an LLM only after the fixed
context pack has been generated, and the LLM may use **only** that context pack as evidence.

## Inputs

- Required: a project directory `projects/<project_id>/` containing at least one source document
  (`REPORT.md`, `RESEARCH_PLAN.md`, `REVIEW.md`, `README.md`, or `beril.yaml`).
- Produced first by this skill: the deterministic context pack
  `compendium/context-packs/<project_id>.json` (the ONLY allowed evidence for extraction).

Stop if the project path does not exist or the context pack has no `source_sections` /
`source_anchors` to ground evidence on.

## Outputs

- `compendium/context-packs/<project_id>.json` — deterministic context pack (`build_context_pack`).
- `compendium/kg/<project_id>.kg.yaml` — `{project: {id, title}, statements: [...]}` with validated
  statement cards, written by the LLM from the context pack only.

## Workflow

1. Build the deterministic context pack (no model):
   ```bash
   cd compendium
   uv run compendium context-pack ../projects/<project_id> --out context-packs/<project_id>.json
   ```
   Note the printed `hash:` line — that `sha256:...` value is the `context_pack_hash` every card's
   manifest must carry.
2. Read `context-packs/<project_id>.json`. Use only its fields as evidence:
   - `project.{id,title,authors}` — card project + manifest context;
   - `source_sections` / `source_anchors` — the source text spans available to quote;
   - `candidate_terms` — soft hints for `about.entities` / `about.topics` slugs;
   - `allowed_vocabularies` — the exact enums each card must use;
   - `asset_hints.{notebooks,figures}` — optional `evidence.notebook` / `evidence.figure`.
3. Emit `kg/<project_id>.kg.yaml` as a mapping `{project: {id, title}, statements: [<card>, ...]}`.
   Each statement card must have:
   - `id`: `stmt:<slug>` (stable human slug, kebab-case; not a content hash);
   - `kind`: from `allowed_vocabularies.statement_kinds` (e.g. `finding`, `claim`, `opportunity`);
   - `statement`: one concise scientific sentence;
   - `scope`: from `allowed_vocabularies.statement_scopes` (e.g. `project_local`, `cross_project`);
   - `tier`: from `allowed_vocabularies.statement_tiers` (use `grounded` only when the span is
     located and entities are clean; otherwise `asserted`);
   - `confidence`: from `allowed_vocabularies.confidence` (`low`/`medium`/`high`);
   - `about.entities` and/or `about.topics`: raw slugs (prefer `candidate_terms`); reconcile maps
     them to canonical keys later — do not invent a canonical vocabulary here;
   - `links`: only `supports` / `contradicts` / `motivates` / `refines` / `requires_validation`,
     each a list of `stmt:` ids within this project;
   - `qualifiers`: optional flat `{key: value}` strings (organism, condition, method, ...);
   - `evidence`: `{source_project: <project_id>, source_doc, source_section, exact, prefix, suffix}`
     where `exact` is a verbatim span copied from the context pack's source text; `notebook` /
     `figure` / `p_value` optional;
   - `extraction`: `{agent_type: llm_extractor, skill: kg-extract, model: <model-id>,
     prompt_hash: <prompt-hash>, context_pack_hash: <hash from step 1>, repo_commit: <git rev-parse
     --short HEAD>, timestamp: <ISO-8601 UTC>}`.
4. Validate by loading the cards through the deterministic planner — it must exit 0:
   ```bash
   cd compendium
   uv run compendium plan-pages kg/<project_id>.kg.yaml --out /tmp/<project_id>.plan.json
   ```
   Spot-check a single card with `uv run compendium validate-card <one-card-file>` if a field is in
   question. The orchestrator (`kg-wiki`) runs the full `plan` over the merged corpus later.
5. On a validation error, fix only the offending card(s) and re-run `plan-pages`. Retry a fragment
   at most twice; if a card cannot be grounded, drop it rather than publish an uncited claim.
6. Summarize card counts by kind, new `about` slugs, and any dropped fragments.

## Prohibitions

- Use ONLY the context pack as evidence. No web search, literature, or files outside the pack.
- Every non-retracted card needs an `evidence` anchor with a verbatim `exact` span from the pack.
- Use the pack's `allowed_vocabularies` enums exactly; never invent kind/scope/tier/confidence/link
  values.
- Extract only this one project; the orchestrator batches projects. Do not write other projects'
  KGs.
- Do not write `registry.yaml`, wiki pages, page plans, or canonical entity/topic keys — those are
  `kg-reconcile` / `kg-write`.
- Do not edit Python code, tests, schema, or docs.

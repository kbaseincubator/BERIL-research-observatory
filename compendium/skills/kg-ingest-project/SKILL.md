---
name: kg-ingest-project
description: Ingest one project into the BERIL synthesis wiki statement-card KG. Builds a deterministic context pack, uses an LLM only for schema-constrained extraction, validates and retries invalid output, then writes the project KG artifact and rebuilds quality outputs.
---

# kg-ingest-project

Use this skill for one project at a time, usually `projects/<project_id>`. The output is a validated
statement-card project KG, not prose. Python commands are deterministic and must never call a model;
this skill may use an LLM/subagent only after the fixed context pack has been generated.

## Inputs

- Required: `projects/<project_id>/`.
- Required source files when present: `REPORT.md`, `RESEARCH_PLAN.md`, `REVIEW.md`, `README.md`,
  `beril.yaml`, notebooks, figures, and data artifacts.
- Optional: prior related cards from neighboring projects, entity/topic hints, BERDL/OpenViking context
  references, and existing corrections.

Stop if the project path does not exist or if no source document can supply evidence spans.

## Outputs

- `compendium/context-packs/<project_id>.json`.
- `compendium/kg/<project_id>.kg.yaml`.
- Extraction manifest embedded in the project KG with skill name, model id, prompt hash, context-pack
  hash, schema hash, repo commit, timestamp, retries, and fragment hashes.
- Rebuilt statement graph, page plans, rendered Markdown wiki, and quality diff, or a recorded
  validation failure if the deterministic checks cannot pass.

## Workflow

1. Resolve `project_id` from the project directory name and record the current repo commit.
2. Run deterministic audit/context-pack generation:
   ```bash
   cd compendium
   uv run compendium audit --projects <project_id> --projects-dir ../projects --out out
   uv run compendium context-pack ../projects/<project_id> --out context-packs/<project_id>.json
   ```
3. Hash the context pack and schema. If `compendium/kg/<project_id>.kg.yaml` already has the same
   context-pack hash, schema hash, skill version, and prompt hash, skip extraction and rebuild only if
   downstream artifacts are missing.
4. Ask the LLM/subagent to emit only structured YAML/JSON matching the statement-card project KG contract:
   statement cards, entities, topic memberships, typed statement links, caveats, conflicts, opportunities,
   and a manifest. Give it only the context pack, allowed vocabularies, schema, and existing corrections.
5. Require each non-retracted statement card to include:
   - `id` as `stmt:<content-hash>`;
   - `kind`, `scope`, `tier`, and `confidence` from the allowed enums;
   - `statement` as a concise scientific assertion;
   - `about.entities` and/or `about.topics`;
   - typed `links` only from the allowed relation sets;
   - `evidence.source_project`, `source_doc`, `exact`, `prefix`, and `suffix`;
   - `extraction.context_pack_hash` equal to the generated context pack hash.
6. Validate the draft:
   ```bash
   cd compendium
   uv run compendium validate-project-kg kg/<project_id>.kg.yaml
   uv run compendium statement-graph kg/<project_id>.kg.yaml --out out/<project_id>-statement-graph.json
   uv run compendium plan-pages kg/<project_id>.kg.yaml --out out/<project_id>-page-plans.json
   uv run compendium render-markdown kg/<project_id>.kg.yaml --out wiki
   uv run compendium quality-synthesis kg/<project_id>.kg.yaml --source-root ../projects --out out/<project_id>-synthesis-quality.json
   ```
7. Retry invalid fragments as described below, then write the final YAML with sorted statement cards and
   stable key ordering.
8. Summarize card counts by kind/tier, new or changed entities, proposed conflicts/opportunities, failed
   fragments, and graph/quality diffs.

## Retry Rules

- Retry only the invalid section or fragment, not the entire project, unless the context pack hash changed.
- Retry at most two times per failed fragment.
- On retry, provide the validator error, the offending fragment, the exact source section, and the schema
  subset needed to fix it.
- Drop a fragment after two failed retries and record it in the extraction manifest as `failed_fragments`;
  do not publish partially valid cards from that fragment unless they pass validation independently.
- If evidence `exact` cannot be found in the cited source document, retry once for regrounding; if it still
  fails, drop the statement.
- If an entity grounding is ambiguous, keep the statement at `asserted` and add `requires_validation`;
  do not invent a CURIE.

## Prohibitions

- Do not write uncited claims. Every published non-retracted statement needs an evidence anchor.
- Do not use free-form relation, tier, kind, scope, confidence, page type, or edge-class names.
- Do not promote statements to `reviewed`; only `kg-curate` with a human action can do that.
- Do not retract, merge, split, or correct existing cards here; write proposed issues for `kg-curate`.
- Do not call external APIs, web search, or literature sources to improve a project card. Extraction must
  come from the project context pack.
- Do not edit Python code, tests, docs, or rendered pages from this skill.
- Do not ingest multiple projects in one run; use `kg-backfill` for batches.

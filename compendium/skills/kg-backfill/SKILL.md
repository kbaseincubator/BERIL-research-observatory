---
name: kg-backfill
description: Batch wrapper for BERIL synthesis wiki ingestion. Iterates project-by-project through kg-ingest-project, records per-project failures, supports limits and resume, and produces a batch quality summary without ingesting the full corpus by default.
---

# kg-backfill

Use this skill for controlled batch ingestion. During tracer work, default to the two ADP1 projects only:
`projects/acinetobacter_adp1_explorer` and `projects/adp1_deletion_phenotypes`.
This wrapper is deterministic except for the delegated `kg-ingest-project` extraction step, which may call
an LLM only after each project's fixed context pack exists.

## Inputs

- Explicit project list, or a tracer preset.
- Optional `--limit <n>` to cap project count.
- Optional `--resume <batch_id>` to continue a previous batch.
- Optional `--force` to re-run projects whose context-pack and prompt hashes are unchanged.

Stop if no explicit project list or tracer preset was provided. Do not infer "all projects" by default.

## Outputs

- Batch manifest under `compendium/out/backfill/<batch_id>.yaml`.
- Per-project status: skipped, succeeded, failed validation, failed extraction, or failed rebuild.
- Links to each written `compendium/kg/<project_id>.kg.yaml`.
- Batch diff and quality summary with statement counts, failure reasons, broken links, dangling edges,
  active conflicts, and pages changed.

## Workflow

1. Build the project queue from the explicit list or tracer preset. Sort it for deterministic order.
2. Apply `--limit` after sorting.
3. If `--resume` is supplied, load the prior batch manifest and skip succeeded projects unless `--force`
   is also supplied.
4. For each project, call `kg-ingest-project` with exactly one project path. Do not combine projects into
   one extraction prompt.
5. After each project, append status to the batch manifest immediately so interrupted runs are resumable.
6. Continue after a failed project unless the failure is a shared schema/validator failure affecting every
   project.
7. After the queue completes, run deterministic graph, page-plan, and quality checks for each written
   project KG:
   ```bash
   cd compendium
   uv run compendium validate-project-kg kg/<project_id>.kg.yaml
   uv run compendium statement-graph kg/<project_id>.kg.yaml --out out/<project_id>-statement-graph.json
   uv run compendium plan-pages kg/<project_id>.kg.yaml --out out/<project_id>-page-plans.json
   uv run compendium quality-synthesis kg/<project_id>.kg.yaml --source-root ../projects --out out/<project_id>-synthesis-quality.json
   ```
8. Run `kg-generate-wiki` once the batch has produced the intended KG set; do not write wiki prose from
   this batch wrapper.
9. Write the batch summary with:
   - project count by status;
   - extracted statement count by kind/tier/source project;
   - failed project reasons and validator messages;
   - changed pages and graph artifacts;
   - quality metrics and remaining review-queue candidates.

## Validation Commands

Run these per project after `kg-ingest-project` writes its KG artifact:

```bash
cd compendium
uv run compendium validate-project-kg kg/<project_id>.kg.yaml
uv run compendium statement-graph kg/<project_id>.kg.yaml --out out/<project_id>-statement-graph.json
uv run compendium plan-pages kg/<project_id>.kg.yaml --out out/<project_id>-page-plans.json
uv run compendium quality-synthesis kg/<project_id>.kg.yaml --source-root ../projects --out out/<project_id>-synthesis-quality.json
```

## Retry Rules

- Retry a failed project at most once in the same batch after preserving the failure log.
- Do not retry projects that failed because source files are missing; record them as source failures.
- If a project fails only because one extraction fragment is invalid, let `kg-ingest-project` apply its
  fragment retry/drop rules, then continue.
- On resume, never re-run succeeded projects unless `--force` is explicit.
- If three consecutive projects fail with the same validator/schema error, stop the batch and record a
  shared blocker.

## Prohibitions

- Do not ingest the full project corpus by default during tracer work.
- Do not let one project's context pack or statement cards bleed into another project's extraction prompt
  except as deterministic related-project hints.
- Do not overwrite previous batch manifests; create a new batch id or resume the specified one.
- Do not hide failed projects from the summary.
- Do not edit Python code, tests, README, design docs, or rendered output by hand.

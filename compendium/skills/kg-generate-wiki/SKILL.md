---
name: kg-generate-wiki
description: Single entry point for generating the human-facing BERIL Markdown wiki from deterministic KG/page contexts and LLM-authored synthesis pages.
---

# kg-generate-wiki

Use this skill as the main wiki-generation workflow in Claude Code/Codex. Python commands are internal
deterministic tools: they validate KGs, build statement graphs, plan pages, create bounded page contexts,
validate authored Markdown, and publish the Markdown wiki. The LLM prose is written by the agent/subagents
running this skill, not by Python scripts.

## Inputs

- Required: one statement-card KG file, usually `compendium/kg/<project_id>.kg.yaml` or a merged fixture.
- Required: source project root, usually `projects/`, so page contexts can include bounded source excerpts.
- Optional: existing authored page directory, usually `compendium/pages/`, for unchanged page reuse.
- Optional: page id filter for regenerating one page.

Stop if the KG fails validation, page planning fails, or source excerpts cannot be built for the intended
scope.

## Outputs

- `compendium/page-contexts/**/*.context.json` and `.prompt.md` for deterministic LLM inputs.
- `compendium/pages/**/*.md` plus `.manifest.json` for LLM-authored and validated page artifacts.
- `compendium/wiki/**/*.md` as the connected human-facing Markdown wiki.
- Quality/review artifacts under `compendium/out/`.

## Workflow

1. Build deterministic graph, page plan, and page contexts:
   ```bash
   cd compendium
   uv run compendium validate-project-kg <kg-path>
   uv run compendium statement-graph <kg-path> --out out/wiki-statement-graph.json --artifacts-dir out/wiki-graph
   uv run compendium plan-pages <kg-path> --out out/wiki-page-plans.json
   uv run compendium wiki-contexts <kg-path> --source-root ../projects --out page-contexts
   ```
2. Determine changed pages by comparing each context page `member_hash` with any existing
   `pages/**/*.manifest.json`. Reuse pages whose member hash and prompt/model contract still match.
3. For each changed page context, write the page with the LLM. Prefer parallel subagents when several
   pages changed. Each subagent gets exactly one `.context.json` and `.prompt.md`.
4. The LLM-authored page must:
   - be actual academic prose, not a deterministic template or list of links;
   - use the context's `member_statements`, `local_graph`, `link_map`, and source excerpts;
   - include Markdown links from the context link map where useful;
   - cite every factual paragraph as `[stmt:id; source_project]`;
   - cite only statement ids present in that page context;
   - include source statements/evidence after the prose, not as the lead.
5. Persist each draft through the validator:
   ```bash
   cd compendium
   uv run compendium page-artifact <kg-path> --page-id <page_id> --markdown <draft.md> --out pages --model <model-id> --prompt-hash <prompt-hash>
   ```
6. If `page-artifact` fails, retry the page at most twice. On retry, provide the validator error and the
   exact allowed statement id list from the context. Do not change page membership to make prose pass.
7. Publish the connected Markdown wiki:
   ```bash
   cd compendium
   uv run compendium render-markdown <kg-path> --pages pages --out wiki
   uv run compendium quality-synthesis <kg-path> --source-root ../projects --out out/wiki-quality.json --dashboard-out out/wiki-quality.html
   uv run compendium review-queue <kg-path> --source-root ../projects --out out/wiki-review-queue.json
   ```
8. Verify:
   ```bash
   cd compendium
   uv run pytest tests/test_page_artifact.py tests/test_cli_commands.py tests/test_tracer.py tests/test_ingested_tracer.py -q
   ```
9. Summarize changed pages, reused pages, failed pages, quality status, and the final wiki entry point
   `compendium/wiki/index.md`.

## Subagent Contract

When dispatching subagents, give each subagent:

- the page id;
- path to one `.context.json`;
- path to the matching `.prompt.md`;
- output path for one draft Markdown file.

Each subagent must return only:

- the draft path;
- cited statement ids;
- any uncertainty or validation concern.

Do not let subagents edit KG files, page plans, manifests, tests, or unrelated wiki pages.

## Prohibitions

- Do not call Python scripts to generate substitute prose.
- Do not use web/literature facts or project files outside the deterministic page context.
- Do not add new statement ids, page links, topics, entities, or page members during wiki generation.
- Do not publish pages without `page-artifact` manifests.
- Do not reintroduce HTML wiki export.

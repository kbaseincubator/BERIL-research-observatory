---
name: kg-synthesize-page
description: Generate one prose-rich synthesis wiki page from a fixed PagePlan and referenced statement cards. Writes cited markdown plus a synthesis manifest, regenerating only when the plan/member hash changes.
---

# kg-synthesize-page

Use this skill after deterministic graph assembly and page planning. The LLM may write prose, but it may
only use the fixed `PagePlan` member set and the referenced statement cards. This skill does not choose
page membership and does not create new scientific claims.

## Inputs

- Required: page id or page-plan path.
- Required: `PagePlan` with `id`, `type`, `title`, `member_statement_ids`, `sections`, `outgoing_links`,
  `backlinks`, and `member_hash`.
- Required: the referenced statement cards and source-project metadata.
- Optional: cached section manifests for unchanged section/member hashes.

Stop if the page plan references missing cards, retracted cards intended for normal synthesis, or cards
outside the allowed member set.

## Outputs

- `compendium/pages/<page_path>.md`, where the path follows the page type:
  `home.md`, `topics/<id>.md`, `claims/<id>.md`, `conflicts/<id>.md`,
  `opportunities/<id>.md`, `directions/<id>.md`, `hypotheses/<id>.md`,
  `projects/<id>.md`, or `entities/<id>.md`.
- `page_plan.yaml` beside the page artifact or in the page-plan output directory, as defined by the
  page planner.
- Synthesis manifest with skill name, model id, prompt hash, page-plan hash, member hash, section hashes,
  repo commit, timestamp, and cited statement ids.

## Workflow

1. Load the deterministic page plan and collect only `member_statement_ids`.
2. Validate the plan before writing:
   ```bash
   cd compendium
   uv run compendium validate-page-plan <page_plan.yaml>
   ```
3. Compute the page-plan hash and each section fact/member hash. Reuse cached prose for unchanged
   section hashes.
4. For changed sections, ask the LLM/subagent to write concise wiki prose from only:
   - the section plan;
   - member statement text;
   - statement kind/tier/confidence;
   - evidence source project and source document;
   - outgoing/backlink targets selected by the plan.
5. Require citations in every factual paragraph using statement ids and source projects, for example
   `[stmt:abc123; acinetobacter_adp1_explorer]`.
6. Write page markdown with:
   - title and page metadata;
   - readable synthesis sections;
   - caveats/conflicts when present in the member set;
   - source statement list;
   - outgoing links and backlinks from the plan;
   - synthesis manifest reference.
7. Validate and rebuild the affected outputs:
   ```bash
   cd compendium
   uv run compendium validate-page-plan <page_plan.yaml>
   uv run compendium render --out out
   uv run compendium quality --out out
   ```
8. Summarize changed sections, reused sections, cited statements, and affected rendered pages.

## Page-Type Requirements

- `home`: state-of-the-science overview, topic map, strongest reusable claims, active conflicts,
  opportunities/directions, reusable products, recent changes, and browse lanes.
- `topic`: cross-project synthesis, key claims, caveats, conflicts, next actions, and project coverage.
- `claim`: claim statement, supporting/refuting cards, scope, caveats, and downstream uses.
- `conflict`: sides, evidence, affected pages, and resolving work.
- `opportunity`/`direction`/`hypothesis`: motivating evidence, required data, target output, and readiness
  or success criteria.
- `project`: extracted statement summary and source trail.
- `entity`: backlink/local graph page grouped by statement kind and topic, not a full narrative hub.

## Retry Rules

- Retry only sections whose prose fails citation, unsupported-claim, or page-template validation.
- Retry at most two times per section.
- On retry, provide the section draft, validator finding, and the exact allowed statement list.
- If a section still fails after two retries, leave the previous cached section if its hash matches;
  otherwise write a stub section that lists member statements without LLM prose and record the failure.
- Never regenerate unchanged sections just to improve style.

## Prohibitions

- Do not add statements, entities, links, topics, or page members.
- Do not cite a project without citing a statement id.
- Do not use source documents directly except for the evidence snippets already attached to member cards.
- Do not hide `asserted`, `low` confidence, conflict, or caveat status.
- Do not include unsupported background knowledge, literature claims, or web-sourced facts.
- Do not change tiers, corrections, graph artifacts, Python code, tests, README, or design docs.

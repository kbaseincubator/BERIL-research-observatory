---
name: kg-review-queue
description: Generate and act on a prioritized human review queue for high-value weak points in the BERIL synthesis wiki statement-card KG, routing accepted actions through kg-curate.
---

# kg-review-queue

Use this skill after graph assembly and quality checks. It identifies statements where limited human review
has the most leverage: central asserted statements, low-confidence statements used in synthesis, conflicts,
and cards with evidence or grounding concerns. Python commands are deterministic; this skill should not
call an LLM unless it is summarizing a fixed queue item from generated graph, page-plan, and quality
artifacts.

## Inputs

- Committed project KG files and graph artifacts.
- Quality report metrics.
- Optional scope: page id, project id, topic id, entity id, statement kind, or maximum item count.

Stop if graph, page-plan, or quality artifacts are missing; run the deterministic commands first.

## Outputs

- Review queue artifact under `compendium/out/review-queue.yaml` or the configured quality output path.
- Review briefs with statement text, evidence anchor, source project, confidence/tier, why it was ranked,
  affected pages, linked conflicts, and suggested `kg-curate` actions.
- Optional curation records only when the reviewer explicitly chooses an action.

## Ranking Signals

Rank higher when a statement has one or more of these properties:

- high graph centrality or many synthesis-page memberships;
- tier is `asserted` and not manually reviewed;
- confidence is `low`;
- kind is `conflict`, `caveat`, `opportunity`, or a claim used by multiple pages;
- involved in `contradicts`, `requires_validation`, `needs_review`, or unresolved conflict edges;
- evidence anchor is weak, missing context, or near a validator warning;
- affects tracer pages such as home, ADP1 topic, ADP1 organism, claim, or opportunity pages.

## Workflow

1. Rebuild the graph, page-plan, Markdown wiki, and quality artifacts for the scoped project KG:
   ```bash
   cd compendium
   uv run compendium validate-project-kg kg/<project_id>.kg.yaml
   uv run compendium statement-graph kg/<project_id>.kg.yaml --out out/<project_id>-statement-graph.json
   uv run compendium plan-pages kg/<project_id>.kg.yaml --out out/<project_id>-page-plans.json
   uv run compendium render-markdown kg/<project_id>.kg.yaml --out wiki
   uv run compendium quality-synthesis kg/<project_id>.kg.yaml --source-root ../projects --out out/<project_id>-synthesis-quality.json
   ```
2. Generate the review queue from the project KG and deterministic artifacts:
   ```bash
   cd compendium
   uv run compendium review-queue kg/<project_id>.kg.yaml --source-root ../projects --out out/<project_id>-review-queue.json
   ```
3. For each queued item, write a brief containing:
   - statement id and text;
   - kind, tier, confidence, scope;
   - source project, source document, source section, exact evidence, prefix, suffix;
   - ranking reasons and score components;
   - affected pages and linked statements;
   - suggested action: accept/promote, demote, retract, fix-statement, reground-entity, mark-conflict,
     resolve-conflict, or defer.
4. If the reviewer chooses an action, call `kg-curate` to write the append-only correction. Do not write
   corrections directly from the review queue.
5. Rebuild and rerun quality after accepted curation actions:
   ```bash
   cd compendium
   uv run compendium validate-project-kg kg/<project_id>.kg.yaml
   uv run compendium statement-graph kg/<project_id>.kg.yaml --out out/<project_id>-statement-graph.json
   uv run compendium plan-pages kg/<project_id>.kg.yaml --out out/<project_id>-page-plans.json
   uv run compendium quality-synthesis kg/<project_id>.kg.yaml --source-root ../projects --out out/<project_id>-synthesis-quality.json
   ```
6. Summarize queue size, top reasons, actions taken, and remaining high-priority items.

## Retry Rules

- If queue generation fails because graph or quality artifacts are stale, rebuild once and retry.
- If an item lacks enough evidence for a review brief, rank it high as an evidence issue and suggest
  `retract` or `fix-statement`; do not fill gaps with inference.
- If a suggested action has an ambiguous target, pass the ambiguity to `kg-curate` and wait for a reviewer
  decision.
- Do not repeatedly surface an item already reviewed in the same run unless it remains unresolved after
  curation.

## Prohibitions

- Do not make curation changes without an explicit reviewer action.
- Do not promote statements just because they are central.
- Do not lower priority for conflicts merely because they are hard to resolve.
- Do not use external literature or web search to decide truth during queue generation.
- Do not edit extracted project KG files, Python code, tests, README, design docs, or unrelated skills.

---
name: kg-curate
description: Create append-only curation records for statement-card corrections, retractions, entity merge/split decisions, tier changes, and conflict handling. Corrections are deterministic build inputs and regression fixtures.
---

# kg-curate

Use this skill when a human reviewer or review queue identifies a concrete issue in the statement-card KG.
The skill writes correction records; it does not edit extracted project cards in place.

## Inputs

- Natural-language reviewer request or a structured review-queue action.
- Target statement id, graph node id, entity id, page id, or enough text to resolve candidates.
- Required rationale and reviewer identity when changing tier, retracting, merging, splitting, or resolving
  a conflict.

Stop and ask for clarification if the target resolves to multiple plausible statements or if the requested
change would affect a class of records but only one example was identified.

## Outputs

- Append-only correction record in `compendium/kg/corrections/<scope>.yaml`.
- Regression fixture entry that can be used to prove the correction survives re-extraction.
- Rebuilt graph/page/quality diff for affected statements/pages.

## Correction Kinds

Allowed `kind` values:

- `retract`
- `fix-statement`
- `fix-qualifier`
- `reground-entity`
- `force-merge`
- `force-split`
- `promote`
- `demote`
- `mark-conflict`
- `resolve-conflict`

No other correction kind is valid.

## Workflow

1. Resolve targets from committed artifacts:
   ```bash
   cd compendium
   uv run compendium build --out out
   ```
   Inspect `kg/projects/*.yaml`, `kg/graph/graph.json`, `out/nodes.tsv`, `out/edges.tsv`, and rendered
   pages as needed.
2. Present ambiguous target candidates before writing anything. Include statement id, statement text,
   source project, tier, confidence, and affected pages.
3. Write one append-only correction record with:
   ```yaml
   id: corr:<stable-id>
   kind: <allowed-kind>
   targets: [stmt:<id>]
   value: {}
   rationale: "<human-readable reason>"
   reviewer: "<name-or-id>"
   timestamp: "<iso8601>"
   source: "kg-curate"
   creates_regression_fixture: true
   ```
4. For `retract`, keep the original statement for provenance but exclude it from normal synthesis.
5. For `fix-statement`, preserve the original evidence anchor and state the corrected text. If the evidence
   no longer supports the text, use `retract` instead.
6. For `reground-entity`, `force-merge`, and `force-split`, record the old and new ids and the exact scope
   of the override.
7. For `promote` or `demote`, require reviewer rationale. Only promote to `reviewed` when the reviewer
   explicitly accepted the statement or generated synthesis section.
8. For `mark-conflict` or `resolve-conflict`, record both sides and affected pages.
9. Validate and rebuild:
   ```bash
   cd compendium
   uv run compendium validate-project-kg kg/projects/<project_id>.yaml
   uv run compendium build --out out
   uv run compendium quality --out out
   ```
10. Summarize the correction id, targets, affected pages, and regression fixture created.

## Retry Rules

- If target resolution is ambiguous, do not guess; ask for the intended target or scope.
- If validation fails because the correction shape is invalid, fix the record once and rerun validation.
- If validation fails because the requested correction contradicts another correction, surface both records
  and ask for a reviewer decision.
- If re-extraction changes a corrected statement id, use the stable content/evidence fields to relink the
  correction once; record the relink in the correction manifest.

## Prohibitions

- Do not edit extracted cards directly to make a correction.
- Do not delete retracted statements; preserve provenance.
- Do not invent correction kinds or relation types.
- Do not silently apply broad entity merges/splits from a single ambiguous example.
- Do not promote automatically extracted statements to `reviewed` without an explicit human decision.
- Do not change Python code, tests, README, design docs, or unrelated skill files.

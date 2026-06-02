---
name: kg-extract
description: Enrich a project's deterministic kg.yaml with typed, sourced relation assertions using subagents (schema-constrained, validate-retry, provenance-stamped, content-hash cached). Use after Stage-1 extraction when a project's prose contains relations the rule parser cannot capture.
---

# kg-extract

Stage-2 **candidate authoring** for one project. The deterministic Stage-1 parser
(`compendium.extract.structural`) already produced entities, findings, datasets, and the
`Project–studies→Organism` scaffold. This skill adds the **prose-bound typed relations** an LLM can
read but regex cannot (e.g. `Gene –has_phenotype→ Phenotype`, `Gene –participates_in→ Pathway`),
**always with a source span**. Output is *candidates* — tiers are assigned deterministically by
`compendium.verify`, never by this skill.

## When to run
At `/submit` (per project, incremental) or during backfill. Runs **offline**; never on the render path.

## Procedure
1. **Cache check.** Compute `content_hash(report_text) + skill_version + prompt_hash + schema_hash`.
   If `kg/<project>.kg.yaml` already carries that `extraction` manifest, skip (no re-extraction).
2. **Dispatch subagents** (Claude Code `Agent`/Task or Codex subagents — `subagent_type=general-purpose`,
   one per REPORT section chunk). Give each the LinkML schema (`compendium/schema/compendium.yaml`),
   the section text, and the existing entity node ids. Instruct: emit ONLY JSON matching the `Assertion`
   shape (`s`,`p`,`o` from the predicate enum, `polarity`, `evidence.span` with `file`+`char`+verbatim
   `quote`, `extractor.confidence`). Node ids must be `ids.node_id(label, type)`; do not invent CURIEs.
3. **Validate + retry.** Load each fragment; drop assertions that fail schema, use an off-enum predicate,
   or whose `quote` is not found verbatim in the cited file. Retry a failed chunk once.
4. **Merge into `kg/<project>.kg.yaml`** (assertions deduped by content-addressed `assertion_id`) and
   write the `project.extraction` provenance manifest (skill/model/prompt/tool/commit/retry/candidate hashes).
5. **Rebuild** the affected blast radius: `compendium all --projects <project> ...` (deterministic).

## Guarantees
- Reproducible **build**, not reproducible extraction: candidates are frozen + provenance-stamped, then
  the deterministic core takes over.
- No tier is set here. `verify` decides `grounded`/`asserted`; conflicts surface at build.
- Tokens come from the agent runtime (subscription); an API path is an optional drop-in for unattended backfill.

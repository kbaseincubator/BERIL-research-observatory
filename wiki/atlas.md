---
id: atlas.beril
title: BERIL Atlas
type: atlas
status: draft
summary: Entry point for the BERIL Atlas over projects, data, claims, directions, hypotheses, methods, and contributor provenance.
source_projects: []
source_docs:
  - docs/discoveries.md
  - docs/research_ideas.md
  - docs/pitfalls.md
  - docs/performance.md
  - ui/config/collections.yaml
related_collections:
  - kbase_ke_pangenome
  - kescience_fitnessbrowser
  - enigma_coral
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-04-30
related_pages:
  - topics.index
  - topic.critical-minerals
  - topic.amr-resistance-ecology
  - data.index
  - data.reuse
  - conflicts.index
  - claims.index
  - directions.index
  - hypotheses.index
  - method.progressive-disclosure
  - method.reuse-and-tension-workflow
order: 1
---

# BERIL Atlas

The BERIL Atlas is a curated semantic layer over the observatory. It does not replace project reports, notebooks, BERDL collections, or memory docs. It gives humans and agents a progressive path through the landscape those sources create together.

## What The Atlas Connects

The Atlas is organized around several kinds of maps:

- [Topics](/atlas/topics) synthesize science and application areas across projects.
- [Data](/atlas/data) explains tenants, collections, data types, derived products, joins, and gaps.
- [Reuse](/atlas/data/reuse) shows how project outputs become reusable products and downstream inputs.
- [Claims](/atlas/claims) preserve reusable evidence-backed statements.
- [Tensions](/atlas/conflicts) preserve conflicts, caveats, and resolving analyses.
- [Directions](/atlas/directions) identify high-value research programs.
- [Hypotheses](/atlas/hypotheses) turn synthesis into testable units.
- [People](/atlas/people) routes review by contributor context and ownership.
- [Methods](/atlas/methods) define the maintenance and evidence rules.

## How To Read It

Start with [topics](/atlas/topics) when you want narrative synthesis. Start with [data](/atlas/data) when you want reusable collections, joins, and derived products. Start with [claims](/atlas/claims/metal-specific-genes-core-enriched) or [hypotheses](/atlas/hypotheses/h-metal-amr-co-selection) when you want agent-sized reasoning units.

## Maintenance Boundary

The Atlas is still static checked-in markdown. Agents can build, lint, inventory, and revise it, but the production UI reads the checked-in corpus and BERDL collection snapshot rather than calling a live LLM at request time.

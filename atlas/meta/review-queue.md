---
id: meta.review-queue
title: Atlas Review Queue
type: meta
status: draft
summary: Maintainer queue for deepening flagship topics, promoting reusable products, and resolving Atlas tensions.
source_projects: []
source_docs:
  - docs/discoveries.md
  - docs/research_ideas.md
  - atlas/meta/metrics-to-watch.md
  - atlas/methods/reuse-and-tension-workflow.md
  - projects/bacillota_b_subsurface_accessory/REPORT.md
related_collections:
  - kbase_ke_pangenome
  - kescience_fitnessbrowser
  - enigma_coral
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-05-01
related_pages:
  - meta.metrics-to-watch
  - method.agent-maintenance
  - method.reuse-and-tension-workflow
  - topic.critical-minerals
  - topic.amr-resistance-ecology
  - topic.fitness-validated-function
  - topic.pangenome-architecture
  - data.cf-formulation-scores
  - data.functional-innovation-ko-atlas
  - conflict.lab-fitness-field-generalization
  - conflict.metal-amr-co-selection-readiness
order: 3
---

# Atlas Review Queue

## Why This Page Exists

The Atlas now has enough structure that maintenance should be driven by review queues, not by whichever page is easiest to edit. This page converts inventory signals into concrete update packets that agents and human reviewers can work through without adding an always-on LLM service.

## Current Maintenance Signals

- **Low-confidence pages** should be treated as review targets, not defects. The useful question is whether they need better provenance, narrower claims, or a reviewer route.
- **Unresolved conflicts** are productive tension records. They should stay visible until a resolving analysis or experiment changes the claim status.
- **Derived products without consumers** need a promotion decision: connect them to downstream projects, keep them candidate, or deprecate them.
- **Flagship topics** should read as synthesis pages. If a topic only lists projects, it is not carrying enough Atlas value.
- **New completed projects** should be checked against existing claims before they become isolated project summaries.

## Priority Update Packets

### Packet 1 - Flagship Topic Depth

Target pages:

- [Critical Minerals and Metal Biology](/atlas/topics/critical-minerals)
- [AMR, Resistance Ecology, and Co-selection](/atlas/topics/amr-resistance-ecology)
- [Pangenome Architecture and Gene-Content Evolution](/atlas/topics/pangenome-architecture)
- [Fitness-Validated Gene Function](/atlas/topics/fitness-validated-function)

Review task: each page should have a synthesis takeaway, learned layers, reusable claims, linked directions or opportunities, data dependencies, caveats, open tensions, and a clear drill-down path. The reviewer should check whether the page explains what BERIL has learned rather than only reciting project names.

### Packet 2 - Derived Product Promotion

Target products:

- [CF Formulation Scores](/atlas/data/derived-products/cf-formulation-scores)
- [Functional Innovation KO Atlas](/atlas/data/derived-products/functional-innovation-ko-atlas)
- [Pangenome Openness Metrics](/atlas/data/derived-products/pangenome-openness-metrics)
- [Dark Gene Prioritization](/atlas/data/derived-products/dark-gene-prioritization)

Review task: decide whether each product has a real downstream consumer, a named owner route, artifact provenance, caveats, and an obvious next use. Products without consumers should be connected to an opportunity or kept explicitly as candidates.

### Packet 3 - Tension Resolution

Target conflicts:

- [Lab fitness signals versus field ecology](/atlas/conflicts/lab-fitness-field-generalization)
- [Metal-AMR co-selection readiness](/atlas/conflicts/metal-amr-co-selection-readiness)
- [Metal specificity versus general stress](/atlas/conflicts/metal-specificity-vs-general-stress)
- [Ecotype translation leakage](/atlas/conflicts/ecotype-translation-leakage)

Review task: confirm that each conflict has evidence on multiple sides, likely explanations, affected claims, and a resolving analysis. If a new project narrows the uncertainty, update the conflict before updating the topic.

### Packet 4 - New Project Integration

Trigger: a completed project adds a report, review, or derived output.

Review task:

1. Add the project to the relevant topic page only if it changes the synthesis.
2. Add or update a claim when the project creates reusable evidence.
3. Add or update a conflict when the project corrects, weakens, or complicates an existing story.
4. Add a derived product only when the output has artifact paths and likely reuse.

Recent example: `bacillota_b_subsurface_accessory` strengthens the pangenome topic by showing subsurface Bacillota_B gene-content expansion and by documenting a marker-correction lesson for redox interpretation.

## Review Routes

Use project authorship and derived-product producers first. For pages that join multiple domains, route review to at least two contexts: one person close to the source project and one person close to the downstream use. Do not infer personal expertise beyond explicit repository context.

## Exit Criteria

A review packet is done when:

- Atlas lint passes.
- Inventory does not introduce new orphaned pages or unresolved ID problems.
- The updated page has a clear "what we learned" statement.
- Caveats say what analysis or experiment would change the claim.
- Links point to the next useful drill-down, not just adjacent pages.

## How Agents Should Use This Page

Before starting Atlas maintenance, run inventory and compare the output to these packets. Prefer completing one packet well over making shallow edits across many pages.

---
id: method.new-project-integration
title: New Project Integration Pattern
type: method
status: draft
summary: Procedure for integrating newly completed projects into the BERIL Atlas without turning topic pages into project-summary dumps.
source_projects:
  - lanthanide_methylotrophy_atlas
  - prophage_amr_comobilization
  - harvard_forest_warming
  - microbeatlas_metal_ecology
  - metal_resistance_global_biogeography
  - soil_metal_functional_genomics
  - soil_frontier_genomics
  - t4ss_cazy_environmental_hgt
source_docs:
  - projects/lanthanide_methylotrophy_atlas/REPORT.md
  - projects/prophage_amr_comobilization/REPORT.md
  - projects/harvard_forest_warming/REPORT.md
  - projects/microbeatlas_metal_ecology/REPORT.md
  - projects/metal_resistance_global_biogeography/REPORT.md
  - projects/soil_metal_functional_genomics/REPORT.md
  - projects/soil_frontier_genomics/REPORT.md
  - projects/t4ss_cazy_environmental_hgt/REPORT.md
related_collections:
  - kbase_ke_pangenome
  - kescience_fitnessbrowser
  - arkinlab_microbeatlas
  - kescience_mgnify
  - nmdc_metadata
  - nmdc_results
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-05-08
related_pages:
  - meta.review-queue
  - method.agent-maintenance
  - topic.critical-minerals
  - topic.amr-resistance-ecology
  - topic.mobile-elements-phage
  - topic.microbial-ecotypes-environment
order: 60
---

# New Project Integration Pattern

## Purpose

New completed projects should change the Atlas only where they improve synthesis, evidence, reuse, or review routing. The goal is not to mention every project everywhere; it is to decide which existing Atlas statements the project strengthens, weakens, redirects, or makes newly testable.

## Intake Steps

1. Read the project report, review, and generated-data tables before editing Atlas pages.
2. Classify each project as one or more of: topic deepener, claim creator, claim modifier, conflict resolver, conflict creator, opportunity source, derived-product candidate, or data-gap evidence.
3. Update existing topic pages before creating new pages.
4. Create a claim only when the result is reusable outside the source project.
5. Update or create a conflict when the project complicates an existing story or exposes a necessary control.
6. Add project IDs to frontmatter only on pages where the project changes the synthesis.

## Integration Map From This Pass

- `lanthanide_methylotrophy_atlas`: creates a reusable rare-earth biology claim and changes the critical-minerals synthesis from "REE data absent" to "direct REE fitness absent, but pangenome marker evidence is now substantial."
- `prophage_amr_comobilization`: creates a mobile-context AMR claim and strengthens AMR and mobile-element topics.
- `microbeatlas_metal_ecology`: creates a field-ecology claim that metal type diversity predicts niche breadth after phylogenetic control.
- `metal_resistance_global_biogeography`: supports global metal-resistance mapping but stays caveat-heavy because spatial validation and sampling-effort correction remain pending.
- `soil_metal_functional_genomics`: strengthens metal-environment association synthesis while adding confounds around co-contamination, conditional R2, and proximity joins.
- `harvard_forest_warming`: strengthens the field-validation topic by showing how DNA and RNA functional pools can converge after long-term warming and how design confounds can reverse apparent omics-layer conclusions.
- `t4ss_cazy_environmental_hgt`: strengthens the mobile-element topic by connecting T4SS, CAZy HGT, and metal-resistance enrichment.
- `soil_frontier_genomics`: contributes mainly as a data-gap and validation-method signal, not as a settled biological claim.

## Exit Criteria

An integration pass is complete when Atlas lint passes, inventory shows no new orphaned pages, every new claim has evidence metadata, and every touched topic has a clear "what changed" statement rather than a project list.

## How Agents Should Use This Page

Use this method after any merged project batch. Treat it as a checklist for deciding whether the Atlas needs a topic edit, a claim, a conflict, an opportunity, or no change.

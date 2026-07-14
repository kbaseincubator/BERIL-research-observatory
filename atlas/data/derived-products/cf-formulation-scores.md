---
id: data.cf-formulation-scores
title: CF Formulation Scores
type: derived_product
status: draft
summary: Reusable formulation scoring outputs for CF airway community design and Pseudomonas competition analysis.
source_projects:
  - cf_formulation_design
  - pseudomonas_carbon_ecology
  - webofmicrobes_explorer
source_docs:
  - projects/cf_formulation_design/REPORT.md
  - projects/cf_formulation_design/data/DATA_DICTIONARY.md
related_collections:
  - protect_genomedepot
  - protect_integration
  - protect_mind
  - kescience_webofmicrobes
  - kbase_ke_pangenome
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-05-08
related_pages:
  - topic.host-microbiome-translation
  - topic.metabolic-capability-community-design
product_kind: ranking
reuse_status: candidate
produced_by_projects:
  - cf_formulation_design
used_by_projects: []
output_artifacts:
  - path: projects/cf_formulation_design/figures/05_formulation_scores_by_size.png
    description: Formulation score comparison by community size.
    status: figure
  - path: projects/cf_formulation_design/data/DATA_DICTIONARY.md
    description: Data dictionary for formulation scoring tables and derived facts.
    status: documentation
review_routes:
  - cf_formulation_design
evidence:
  - source: cf_formulation_design
    support: Produces ranked formulations, strict-safety filters, and validation figures for airway community design.
  - source: webofmicrobes_explorer
    support: Provides metabolite production/consumption context that can inform formulation reuse.
order: 101
---

# CF Formulation Scores

## Reusable Object

This product captures ranked candidate microbial formulations and supporting score components for CF airway community design.

## Review Brief

What changed: this candidate product now needs a clearer human decision about whether the formulation score changes downstream design or remains an internal project output.

Why review matters: CF formulation is translationally sensitive. Reviewers should confirm that safety filters, cohort provenance, validation limits, and ecological-cost assumptions are explicit before reuse.

Evidence to inspect:

- `cf_formulation_design` for score components and strict safety filtering.
- `pseudomonas_carbon_ecology` for Pseudomonas competition context.
- `webofmicrobes_explorer` for metabolic interaction evidence.
- [CF Formulation Score Reuse Test](/atlas/opportunities/cf-formulation-reuse) for the downstream consumer question.

Questions for reviewers:

- Does the score change a concrete formulation decision?
- Are strict-safety filters visible enough for translational review?
- Should this remain candidate until an independent validation or consumer exists?
- Which score components are generalizable beyond the source cohort?

## Why It Is High Value

The scoring framework links inhibition, engraftability, metabolic niche coverage, safety filters, and Pseudomonas genomic context. Even if the exact formulation changes, the score structure is reusable.

## High-Value Joins

- Join formulation candidates to PROTECT isolate/genome metadata.
- Join metabolic compatibility to Web of Microbes and GapMind pathway evidence.
- Join Pseudomonas genomic context to host-associated adaptation and target robustness.

## Caveats

This is translationally sensitive. Reuse should preserve strict-safety filtering, cohort provenance, and experimental validation status.

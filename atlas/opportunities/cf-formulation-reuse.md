---
id: opportunity.cf-formulation-reuse
title: CF Formulation Score Reuse Test
type: opportunity
status: draft
summary: Find a first downstream consumer for CF formulation scores by testing whether ranked carbon contexts improve strain or community design decisions.
source_projects:
  - cf_formulation_design
  - pseudomonas_carbon_ecology
  - webofmicrobes_explorer
source_docs:
  - docs/discoveries.md
  - docs/research_ideas.md
related_collections:
  - kescience_webofmicrobes
  - kbase_phenotype
  - kbase_msd_biochemistry
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-04-30
related_pages:
  - topic.metabolic-capability-community-design
  - topic.host-microbiome-translation
  - data.cf-formulation-scores
  - data.metabolism-biochemistry-pathways
opportunity_status: candidate
opportunity_kind: analysis
impact: medium
feasibility: high
readiness: high
evidence_strength: medium
linked_conflicts: []
linked_products:
  - data.cf-formulation-scores
target_outputs:
  - First downstream reuse analysis for CF formulation scores.
  - Reuse decision: promote, revise, or deprecate the score product.
  - Candidate strains or carbon contexts for follow-up validation.
review_routes:
  - cf_formulation_design
  - pseudomonas_carbon_ecology
  - webofmicrobes_explorer
evidence:
  - source: data.cf-formulation-scores
    support: The product is tracked but currently has no declared downstream consumer.
  - source: pseudomonas_carbon_ecology
    support: Carbon ecology provides a natural reuse context for formulation ranking.
order: 50
---

# CF Formulation Score Reuse Test

## Why It Matters

The Atlas already tracks CF formulation scores, but inventory marks the product as needing downstream reuse. A first consumer would show whether the score is a reusable asset or only a project-local artifact.

## Evidence Base

The product connects formulation design, Pseudomonas carbon ecology, Web of Microbes context, phenotype data, and metabolism collections. That makes it a practical test case for derived-product promotion.

## Work Package

Choose one reuse question: strain ranking, carbon-source prioritization, or community design constraints. Apply the existing formulation score to that question and record whether the score changes a decision relative to simpler baselines.

## Decision Use

If the score improves a downstream decision, [CF Formulation Scores](/atlas/data/derived-products/cf-formulation-scores) can move toward promoted reuse. If not, the Atlas should record the failed reuse path and revise the product caveats.

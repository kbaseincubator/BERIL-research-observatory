---
id: opportunity.derived-product-readiness-burn-down
title: Derived Product Readiness Burn-Down
type: opportunity
status: draft
summary: Review candidate and promoted derived products to close missing consumers, artifacts, caveats, and review routes before they become default inputs.
source_projects:
  - metal_fitness_atlas
  - ecotype_analysis
  - cf_formulation_design
  - pangenome_pathway_ecology
source_docs:
  - docs/discoveries.md
  - docs/performance.md
  - docs/pitfalls.md
related_collections:
  - kbase_ke_pangenome
  - kescience_fitnessbrowser
  - kbase_msd_biochemistry
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-05-08
related_pages:
  - data.reuse
  - method.reuse-and-tension-workflow
  - direction.derived-data-product-catalog
  - hypothesis.derived-product-reuse-predicts-value
opportunity_status: candidate
opportunity_kind: productization
impact: medium
feasibility: high
readiness: high
evidence_strength: high
linked_conflicts: []
linked_products:
  - data.cf-formulation-scores
  - data.functional-innovation-ko-atlas
  - data.pangenome-openness-metrics
target_outputs:
  - Readiness table for all derived products with consumer, owner, artifact, and caveat status.
  - Specific promotion or revision actions for candidate products.
  - Updated Atlas metrics for derived-product reuse and readiness.
review_routes:
  - cf_formulation_design
  - pangenome_pathway_ecology
  - metal_fitness_atlas
evidence:
  - source: data.reuse
    support: The reuse graph already exposes products without consumers and products needing stronger review.
  - source: hypothesis.derived-product-reuse-predicts-value
    support: The Atlas treats reuse as a measurable signal of observatory value.
order: 110
---

# Derived Product Readiness Burn-Down

## Why It Matters

Derived products are where BERIL outputs compound. The Atlas now tracks them, but product readiness needs active burn-down: consumers, artifacts, caveats, and review routes should be explicit before a product becomes a default input.

## Review Brief

What changed: many derived-product pages now include review briefs, making this burn-down opportunity more actionable.

Why review matters: reviewers should decide which products are promoted assets, which are candidates, which lack consumers, and which need deprecation or narrower scope.

Evidence to inspect:

- [Reuse Graph](/atlas/data/reuse) for producer, consumer, and source edges.
- Candidate products such as [CF Formulation Scores](/atlas/data/derived-products/cf-formulation-scores) and [Functional Innovation KO Atlas](/atlas/data/derived-products/functional-innovation-ko-atlas).
- [Review Briefs](/atlas/methods/review-briefs) for expected human-feedback structure.

Questions for reviewers:

- Which products have a real consumer versus only a plausible future use?
- Which products need table artifacts rather than figures or diagnostics?
- Which products have no clear owner route?
- What product should be promoted, narrowed, or deprecated first?

## Evidence Base

The reuse graph identifies products with and without downstream consumers. Current examples include strong reused products and candidate products that need a first consumer or clearer promotion criteria.

## Work Package

Review every derived product against a standard checklist: producer, consumer, artifact, caveat, review route, linked tension, and next reuse path. Update page metadata and summaries where the product is promoted, narrowed, or deprecated.

## Decision Use

This opportunity improves the Atlas itself. It should reduce ambiguous reuse and make future project planning faster because product readiness is visible before a notebook is opened.

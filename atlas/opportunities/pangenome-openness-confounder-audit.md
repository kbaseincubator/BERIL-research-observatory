---
id: opportunity.pangenome-openness-confounder-audit
title: Pangenome Openness Confounder Audit
type: opportunity
status: draft
summary: Audit whether openness-function relationships remain after controlling for taxonomy, genome quality, sampling density, and annotation completeness.
source_projects:
  - pangenome_openness
  - openness_functional_composition
  - conservation_vs_fitness
  - core_gene_tradeoffs
source_docs:
  - docs/discoveries.md
  - docs/pitfalls.md
related_collections:
  - kbase_ke_pangenome
  - kbase_genomes
  - pangenome_bakta
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-05-08
related_pages:
  - topic.pangenome-architecture
  - claim.pangenome-openness-shapes-function
  - hypothesis.pangenome-openness-pathway-diversity
  - data.pangenome-openness-metrics
  - data.genomes-and-pangenomes
opportunity_status: candidate
opportunity_kind: analysis
impact: medium
feasibility: high
readiness: high
evidence_strength: medium
linked_conflicts: []
linked_products:
  - data.pangenome-openness-metrics
target_outputs:
  - Confounder-adjusted openness-function association table.
  - List of taxa where openness claims are robust or fragile.
  - Revised caveat labels for pangenome architecture claims.
review_routes:
  - pangenome_openness
  - openness_functional_composition
  - conservation_vs_fitness
evidence:
  - source: claim.pangenome-openness-shapes-function
    support: The Atlas already treats openness as a reusable functional architecture claim.
  - source: data.pangenome-openness-metrics
    support: Openness metrics are tracked as a derived product ready for reuse.
order: 80
---

# Pangenome Openness Confounder Audit

## Why It Matters

Pangenome openness is a useful organizing concept, but it can be confounded by taxonomy, sampling depth, genome quality, and annotation completeness. A clear audit makes the claim stronger where it survives and narrower where it does not.

## Review Brief

What changed: openness now appears in more claims, topics, and derived products, making a confounder audit more urgent.

Why review matters: reviewers should define the minimum controls required before openness can be reused as an explanatory variable.

Evidence to inspect:

- [Pangenome openness shapes functional opportunity](/atlas/claims/pangenome-openness-shapes-function) for the core claim.
- [Pangenome Openness Metrics](/atlas/data/derived-products/pangenome-openness-metrics) for reusable inputs.
- `pangenome_openness`, `openness_functional_composition`, and `conservation_vs_fitness` for source evidence.

Questions for reviewers:

- Which confounder is most likely to change current conclusions: genome count, taxonomy, quality, or annotation density?
- Should the audit produce revised caveat labels or revised metrics?
- What effect size is large enough to preserve after controls?
- Which downstream pages should be updated if openness weakens after adjustment?

## Evidence Base

The relevant projects already connect openness, conservation, fitness, core-gene tradeoffs, and functional composition. The opportunity is to standardize the caveat analysis so future Atlas pages reuse the metric responsibly.

## Work Package

Model openness-function associations with explicit controls for clade, genome count, assembly quality, annotation density, and collection source. Compare raw and adjusted effects and record which conclusions are robust.

## Decision Use

The result should update [Pangenome Openness Metrics](/atlas/data/derived-products/pangenome-openness-metrics), the pangenome topic page, and any future opportunity that treats openness as a predictor.

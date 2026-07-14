---
id: claim.metal-type-diversity-predicts-niche-breadth
title: Metal type diversity predicts ecological niche breadth
type: claim
status: draft
summary: Genus-level metal resistance type diversity predicts broader ecological niche breadth after phylogenetic control, while total AMR burden is less informative.
source_projects:
  - microbeatlas_metal_ecology
source_docs:
  - projects/microbeatlas_metal_ecology/REPORT.md
related_collections:
  - kbase_ke_pangenome
  - arkinlab_microbeatlas
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-05-08
related_pages:
  - topic.critical-minerals
  - topic.microbial-ecotypes-environment
  - conflict.metal-amr-co-selection-readiness
evidence:
  - source: microbeatlas_metal_ecology
    support: PGLS models report that metal type diversity predicts genus-level Levins niche breadth after phylogenetic correction.
  - source: microbeatlas_metal_ecology
    support: Total AMR cluster burden and core AMR fraction are not the strongest predictors, pointing to breadth across metal types rather than raw gene count.
order: 60
---

# Metal type diversity predicts ecological niche breadth

## Claim

The breadth of a genus' metal-resistance repertoire is associated with broader ecological niche breadth after phylogenetic correction. The useful signal is metal type diversity, not simply total AMR gene burden.

## Review Brief

What changed: metal resistance breadth now has a field-ecology claim that connects pangenome-derived resistance summaries to MicrobeAtlas niche breadth.

Why review matters: the claim could influence contaminated-site and bioprospecting proposals, but it is genus-level and observational. Reviewers should decide how much weight it can carry.

Evidence to inspect:

- PGLS model linking metal type diversity to Levins niche breadth.
- Comparison with total AMR burden and core AMR fraction.
- Genus-level aggregation and GTDB phylogenetic matching.
- Sensitivity to prevalence filtering and MicrobeAtlas environment coverage.

Questions for reviewers:

- Is metal type diversity biologically interpretable enough to use as a proposal feature?
- Should the claim stay genus-level, or can it be safely projected to species or site-level analyses?
- What sensitivity check would make this claim more reusable: stricter AMR filters, environment rarefaction, or alternate niche-breadth metrics?
- Should this claim link to a new derived product for metal-resistance breadth features?

## Evidence

`microbeatlas_metal_ecology` links pangenome-derived metal AMR summaries to MicrobeAtlas niche breadth across 1,264 genera and reports that metal type diversity remains a significant PGLS predictor in the bacterial subset with AMR data.

## Why It Matters

This gives critical-mineral and field-ecology pages a stronger bridge from gene repertoires to ecological behavior. It also sharpens co-selection proposals: a site model should ask whether exposure broadens the spectrum of metal types tolerated, not only whether resistance genes are present.

## Caveats

The claim is genus-level and observational. It depends on MicrobeAtlas environment coverage, GTDB phylogenetic matching, and AMR marker definitions. Strict prevalence filtering reduces power, so niche breadth estimates should travel with sensitivity checks.

## Promotion Criteria

Promote this claim after a reviewer confirms that the PGLS result is robust enough for synthesis use and that all downstream pages preserve the genus-level, observational scope.

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

## Evidence

`microbeatlas_metal_ecology` links pangenome-derived metal AMR summaries to MicrobeAtlas niche breadth across 1,264 genera and reports that metal type diversity remains a significant PGLS predictor in the bacterial subset with AMR data.

## Why It Matters

This gives critical-mineral and field-ecology pages a stronger bridge from gene repertoires to ecological behavior. It also sharpens co-selection proposals: a site model should ask whether exposure broadens the spectrum of metal types tolerated, not only whether resistance genes are present.

## Caveats

The claim is genus-level and observational. It depends on MicrobeAtlas environment coverage, GTDB phylogenetic matching, and AMR marker definitions. Strict prevalence filtering reduces power, so niche breadth estimates should travel with sensitivity checks.

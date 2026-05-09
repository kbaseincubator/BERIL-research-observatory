---
id: claim.prophage-density-predicts-amr-breadth
title: Prophage density predicts AMR repertoire breadth
type: claim
status: draft
summary: Pangenome-scale prophage marker density is a strong species-level predictor of AMR breadth, while gene-level AMR-prophage proximity is weaker and threshold-sensitive.
source_projects:
  - prophage_amr_comobilization
source_docs:
  - projects/prophage_amr_comobilization/REPORT.md
related_collections:
  - kbase_ke_pangenome
  - kescience_fitnessbrowser
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-05-08
related_pages:
  - topic.amr-resistance-ecology
  - topic.mobile-elements-phage
  - conflict.metal-amr-co-selection-readiness
evidence:
  - source: prophage_amr_comobilization
    support: Across 4,770 species, prophage marker density correlates strongly with AMR repertoire breadth, including after genome-count control.
  - source: prophage_amr_comobilization
    support: AMR-prophage gene proximity is statistically significant but modest and threshold-sensitive, so the strongest reusable claim is species-level breadth rather than direct cargo transfer.
order: 50
---

# Prophage density predicts AMR repertoire breadth

## Claim

Species with higher prophage marker density tend to carry broader AMR repertoires. This makes prophage context a first-class covariate for AMR ecology, even when direct phage-mediated transfer is not proven.

## Evidence

`prophage_amr_comobilization` reports that prophage density explains a substantial share of AMR breadth across thousands of species and remains associated after controlling for genome count. Gene-level proximity between AMR genes and prophage markers exists but is smaller, heterogeneous, and sensitive to the distance threshold.

## Why It Matters

AMR topic pages should no longer treat "mobile context" as a generic caveat. Prophage burden is now a concrete explanatory variable and a likely confound for metal-AMR co-selection analyses.

## Caveats

The project uses keyword and Pfam prophage markers rather than a dedicated prophage caller, and gene distances are ordinal gene positions rather than base-pair distances. The result supports ecological association and prioritization, not proof of transfer mechanism.

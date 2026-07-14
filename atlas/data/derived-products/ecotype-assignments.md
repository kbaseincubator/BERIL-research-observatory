---
id: data.ecotype-assignments
title: Ecotype Assignments
type: derived_product
status: draft
summary: Reusable within-species or community ecotype labels that support environmental validation, microbiome stratification, and downstream hypothesis tests.
source_projects:
  - ecotype_analysis
  - ecotype_env_reanalysis
  - ibd_phage_targeting
  - plant_microbiome_ecotypes
source_docs:
  - docs/discoveries.md
related_collections:
  - kbase_ke_pangenome
  - nmdc_arkin
  - phagefoundry_paeruginosa_genome_browser
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-05-08
related_pages:
  - topic.microbial-ecotypes-environment
  - topic.host-microbiome-translation
  - conflict.ecotype-translation-leakage
product_kind: label_set
reuse_status: promoted
produced_by_projects:
  - ecotype_analysis
  - ecotype_env_reanalysis
used_by_projects:
  - ibd_phage_targeting
  - plant_microbiome_ecotypes
output_artifacts:
  - path: projects/ecotype_analysis/data/ecotype_correlation_results.csv
    description: Ecotype-environment correlation results used as the reusable label/evidence substrate.
    status: table
  - path: projects/ecotype_env_reanalysis/data/species_env_classification.csv
    description: Environmental reanalysis classifies species context for safer label reuse.
    status: table
review_routes:
  - ecotype_analysis
  - ecotype_env_reanalysis
evidence:
  - source: ecotype_analysis
    support: Ecotype projects generate reusable labels that compress population or community structure for downstream tests.
  - source: ibd_phage_targeting
    support: Translational use cases show why ecotype labels need provenance, caveats, and review gates.
order: 90
---

# Ecotype Assignments

## Reusable Object

Ecotype assignments are labels that compress high-dimensional compositional or genomic structure into cohorts for downstream comparison.

## Review Brief

What changed: ecotype assignments are now used across environment, host, and plant pages, so their validation status needs to be visible to reviewers.

Why review matters: these labels are useful for stratification but risky for translational claims. Reviewers should decide which labels are exploratory, domain-reusable, or safe for downstream hypothesis tests.

Evidence to inspect:

- `ecotype_analysis` and `ecotype_env_reanalysis` for label construction and environmental checks.
- `ibd_phage_targeting` for a translational failure mode.
- `plant_microbiome_ecotypes` for cross-domain reuse.
- [Ecotype labels versus translational leakage](/atlas/conflicts/ecotype-translation-leakage) for the main guardrail.

Questions for reviewers:

- Do the artifacts identify label version, training features, and intended reuse scope?
- Which labels have held-out validation and which are exploratory?
- Should every downstream use carry a leakage-risk or validation-tier field?
- Is this product ready for broad reuse outside the original ecotype projects?

## Why It Is High Value

They can stratify field ecology, clinical microbiome analysis, plant compartment function, and genotype-to-phenotype links.

## High-Value Joins

- Join ecotype labels to environmental metadata to test niche structure.
- Join ecotype labels to pathways, metabolites, or fitness dependencies to test mechanism.
- Join ecotype labels to phage-host or intervention candidates only after independent validation.

## Reuse Signals

Ecotype assignments are useful when they become stable labels shared by multiple projects. They are especially valuable when later work can reuse the same labels without recomputing clusters or leaking outcome features.

## Missing Complementary Data

Independent cohorts, consistent environment labels, batch-corrected metabolomics, and held-out validation data would make these labels safer for translational use.

## Caveats

Ecotype labels become dangerous when the same features define the ecotype and test the outcome. Agents should require leakage checks, nulls, and independent evidence gates.

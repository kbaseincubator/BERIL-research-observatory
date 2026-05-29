---
id: conflict.ecotype-translation-leakage
title: Ecotype labels versus translational leakage
type: conflict
status: draft
summary: Ecotype labels are reusable stratification products, but translational target lists can collapse when labels and outcomes share leaked or confounded features.
source_projects:
  - ecotype_analysis
  - ecotype_env_reanalysis
  - ibd_phage_targeting
  - plant_microbiome_ecotypes
source_docs:
  - projects/ibd_phage_targeting/FAILURE_ANALYSIS.md
  - docs/discoveries.md
related_collections:
  - kbase_ke_pangenome
  - phagefoundry_paeruginosa_genome_browser
  - nmdc_arkin
confidence: medium
generated_by: Codex GPT-5
last_reviewed: 2026-05-08
related_pages:
  - topic.microbial-ecotypes-environment
  - topic.host-microbiome-translation
  - claim.ecotype-analysis-needs-rigor-gates
  - data.ecotype-assignments
conflict_status: partially_resolved
affected_pages:
  - topic.microbial-ecotypes-environment
  - topic.host-microbiome-translation
  - claim.ecotype-analysis-needs-rigor-gates
  - data.ecotype-assignments
evidence_sides:
  - side: useful_stratification
    sources:
      - ecotype_analysis
      - plant_microbiome_ecotypes
    support: Ecotype labels compress high-dimensional structure and can reveal ecological or compartment patterns.
  - side: translational_risk
    sources:
      - ibd_phage_targeting
    support: Target-list collapse under stricter review showed that outcome leakage, missing nulls, and confounds can make ecotype-derived target claims unsafe.
resolving_work:
  - Separate label-training features from outcome-testing features.
  - Require held-out cohort, leave-one-study-out, or independent environment validation before translational reuse.
  - Attach leakage, null-model, and confound labels to every ecotype-derived target list.
order: 20
---

# Ecotype Labels Versus Translational Leakage

## Tension

Ecotype labels are valuable because they simplify complex biological structure. The same compression becomes risky when the label is trained on information too close to the claimed outcome.

## Review Brief

What changed: Atlas review is now using ecotype pages as both reusable data products and cautionary examples for downstream translation.

Why review matters: ecotype labels can help organize biology, but target or intervention claims need stronger validation than stratification claims. Reviewers should make sure those use cases stay separated.

Evidence to inspect:

- `ecotype_analysis` and `ecotype_env_reanalysis` for label construction and environment structure.
- `plant_microbiome_ecotypes` for ecological stratification use.
- `ibd_phage_targeting` failure analysis for leakage, null models, and target-list collapse.
- [Ecotype Assignments](/atlas/data/derived-products/ecotype-assignments) for derived-product reuse.

Questions for reviewers:

- Are label-training features separated from outcome-testing features?
- Which Atlas pages are using ecotypes only for stratification, and which imply translational action?
- What validation ladder should be mandatory before ecotype-derived target claims are allowed?
- Should each ecotype-derived product carry an explicit leakage-risk label?

## Current Interpretation

Ecotype labels should be reusable for stratification and hypothesis generation. They should not be reused for intervention, target, or clinical claims unless independent validation and leakage checks are present.

## Resolving Analysis

The resolving work is a validation ladder: locked labels, held-out outcomes, null models, confound checks, and independent cohort replication.

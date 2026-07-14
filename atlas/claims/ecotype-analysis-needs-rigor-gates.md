---
id: claim.ecotype-analysis-needs-rigor-gates
title: Ecotype analyses need rigor gates before translation
type: claim
status: draft
summary: Ecotype-derived target lists can collapse under leakage, confound, and independent-evidence checks, so translation requires explicit gates.
source_projects:
  - ibd_phage_targeting
  - ecotype_analysis
  - ecotype_env_reanalysis
source_docs:
  - docs/discoveries.md
  - docs/pitfalls.md
related_collections:
  - phagefoundry_paeruginosa_genome_browser
  - kbase_ke_pangenome
confidence: high
generated_by: Codex GPT-5
last_reviewed: 2026-05-08
related_pages:
  - topic.host-microbiome-translation
  - hypothesis.ecotype-batch-correction
  - conflict.ecotype-translation-leakage
evidence:
  - source: ibd_phage_targeting
    support: Target-list collapse under review showed that ecotype-derived translational claims need leakage, null, and confound checks.
  - source: docs/pitfalls.md
    support: Recorded pitfalls document modality and cohort effects that can reverse naive ecotype interpretation.
order: 40
---

# Ecotype analyses need rigor gates before translation

## Claim

Ecotype analyses are useful for stratification, but target-selection claims need leakage checks, null distributions, confound adjustment, and independent evidence gates.

## Review Brief

What changed: this claim is now a general review rule for host, plant, and environment pages that use ecotype labels.

Why review matters: reviewers should enforce the distinction between exploratory stratification and downstream intervention or target claims.

Evidence to inspect:

- `ibd_phage_targeting` failure analysis for target-list collapse.
- `ecotype_analysis` and `ecotype_env_reanalysis` for label construction.
- `docs/pitfalls.md` for modality and cohort caveats.
- [Ecotype Label Validation Benchmark](/atlas/opportunities/ecotype-validation-benchmark) for the next validation path.

Questions for reviewers:

- Which downstream pages use ecotypes for stratification versus action?
- Are null models and held-out validations required before every translational claim?
- Should ecotype-derived products carry a validation-tier field?
- What evidence would let a specific ecotype claim move from cautionary to reviewed?

## Evidence

The IBD phage-targeting memory entries document target-list collapse and plan-review issues caused by feature leakage, missing nulls, and confound mismatch.

## Why It Matters

This claim protects downstream clinical, phage, FMT, antibiotic, and formulation design work from plausible but fragile narratives.

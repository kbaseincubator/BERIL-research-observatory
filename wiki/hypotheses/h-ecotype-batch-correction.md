---
id: hypothesis.ecotype-batch-correction
title: Cross-cohort metabolite ecotypes require batch correction
type: hypothesis
status: draft
summary: Absolute-intensity metabolite ecotypes are dominated by cohort batch effects unless corrected before clustering.
source_projects:
  - ibd_phage_targeting
  - ecotype_analysis
  - webofmicrobes_explorer
source_docs:
  - docs/discoveries.md
  - docs/pitfalls.md
related_collections:
  - phagefoundry_paeruginosa_genome_browser
  - kbase_msd_biochemistry
confidence: high
generated_by: Codex GPT-5
last_reviewed: 2026-04-28
related_pages:
  - claim.ecotype-analysis-needs-rigor-gates
order: 50
---

# Cross-cohort metabolite ecotypes require batch correction

## Hypothesis

Pooled absolute-intensity metabolomics clusters separate by cohort before biology unless batch correction is applied.

## Testable With

Cross-cohort metabolomics, PCA or clustering diagnostics, cohort labels, and corrected versus uncorrected comparisons.

## Agent Rule

Do not treat taxonomy-relative and metabolite-absolute feature spaces as equally portable across cohorts.

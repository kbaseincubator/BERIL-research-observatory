---
reviewer: BERIL Automated Review
date: 2026-02-16
project: enigma_contamination_functional_potential
---

# Review: Contamination Gradient vs Functional Potential in ENIGMA Communities

## Summary
This project is well-structured and reproducible, with a clear hypothesis, complete notebook-to-artifact flow, and a report that is generally consistent with generated outputs. The strongest aspects are explicit confirmatory-vs-exploratory labeling, global BH-FDR reporting across p-values, and robustness checks for mapping coverage and community fractions. The main remaining limitations are biological resolution (genus-level ENIGMA taxonomy), substantial unmapped taxa, and reliance on coarse functional proxies, which appropriately constrain causal interpretation.

## Methodology
The research question is specific and testable in `README.md` and `RESEARCH_PLAN.md`, and the notebook sequence is logical: extraction/QC (`notebooks/01_enigma_extraction_qc.ipynb`), taxonomy bridge + feature engineering (`notebooks/02_taxonomy_bridge_functional_features.ipynb`), then modeling and diagnostics (`notebooks/03_contamination_functional_models.ipynb`).

Reproducibility is strong:
- `README.md` includes a clear `## Reproduction` section with Spark/local separation, execution order, expected runtimes, and expected outputs.
- `requirements.txt` is present.
- All substantive code cells in all 3 notebooks have saved outputs; the two no-output cells in NB03 are comment placeholders only.
- Expected artifacts are present: 7 data TSVs and 3 figure PNGs.

Data-source clarity is good and consistent with schema references (`docs/schemas/enigma.md`, `docs/schemas/pangenome.md`). The analysis explicitly handles known constraints from `docs/pitfalls.md` (string-to-numeric casting, Spark-first aggregation, correct `gene_cluster` to `eggnog_mapper_annotations` join key pattern).

## Code Quality
Notebook code quality is solid overall:
- NB01 keeps heavy aggregation in Spark before collecting to pandas, reducing driver-memory risk.
- NB01 explicitly casts concentration/count fields to numeric types before analysis.
- NB02 uses a defensible strict vs relaxed vs species-proxy bridge design and propagates mode labels through downstream modeling.
- NB03 includes status handling for `insufficient_samples`/`constant_feature`, permutation testing, adjusted models, fraction-aware robustness, and global BH-FDR q-values.

No clear executable bug was found in the current run-synced artifacts. Remaining technical risks are mainly methodological rather than coding errors:
- Genus normalization/matching (`genus_norm`) is pragmatic but can mis-handle edge taxonomic naming variants.
- Species-proxy mode is coverage-limited, so null/weak results there are partly power/coverage constrained.
- Sensitivity model families are broad; although FDR is now present, interpretation should continue to emphasize the predeclared confirmatory endpoint.

## Findings Assessment
The conclusions in `REPORT.md` are supported by the generated tables and figures:
- Confirmatory defense tests are null after global FDR (`model_results.tsv`).
- Exploratory positive defense associations appear in coverage-aware adjusted models and are attenuated after global FDR in stricter settings.
- Community-fraction robustness checks do not show strong within-fraction monotonic defense signals.
- Species-proxy mode has much lower mapped abundance coverage, limiting inferential strength.

The write-up is appropriately cautious, acknowledges limitations clearly, and avoids over-claiming causality.

## Suggestions
1. [High] Keep a strict separation between confirmatory and exploratory claims in `REPORT.md` by presenting confirmatory results first in a dedicated subsection/table and moving all exploratory families to a secondary section with explicit caveats.
2. [High] Add uncertainty intervals (for example bootstrap CIs) for key effect sizes (`spearman_rho`, contamination coefficients), not just p-values/q-values, to improve interpretability of null and borderline signals.
3. [Medium] Add a small sensitivity analysis for contamination-index construction (for example uranium-only, top-k metals, PCA-based index) to show whether conclusions are robust to index definition.
4. [Medium] Quantify bridge uncertainty further by reporting per-sample influence diagnostics versus `mapped_abundance_fraction` (for example decile-stratified effects), beyond the current threshold-based high-coverage subset.
5. [Medium] Add one concise notebook/report table that enumerates sample counts per modeling family (base, adjusted, fraction-aware, high-coverage) to make effective sample-size differences immediately visible.
6. [Nice-to-have] If future ENIGMA releases provide species/strain annotations, prioritize re-running the same pipeline at higher taxonomic resolution before adding more model complexity.

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-02-16
- **Scope**: README.md, 3 notebooks, 7 data files, 3 figures
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.

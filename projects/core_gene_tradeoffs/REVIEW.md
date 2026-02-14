---
reviewer: BERIL Automated Review
date: 2026-02-14
project: core_gene_tradeoffs
---

# Review: Core Gene Paradox — Why Are Core Genes More Burdensome?

## Summary

This is a well-motivated follow-up project that dissects a surprising finding from the upstream `fitness_effects_conservation` analysis: core genome genes are 1.3× more likely to show positive fitness effects (burdens) when deleted than accessory genes. The single notebook (`01_burden_anatomy.ipynb`) delivers a logically structured six-section analysis — function-specific burden rates, condition-type decomposition, trade-off gene enrichment, condition-specific paradox, a motility case study, and a selection-signature matrix — all supported by clear figures with saved outputs. The framing around lab conditions as an impoverished proxy for natural environments is compelling and scientifically grounded. The main areas for improvement are the absence of a `data/` directory or `requirements.txt`, a potential performance issue in the motility analysis, and limited statistical testing in some sections.

## Methodology

**Research question**: Clearly stated and testable — "Why are core genome genes MORE likely to show positive fitness effects when deleted?" The question builds directly on quantified results from the upstream project (OR=0.77, p=5.5e-48), making it a well-scoped follow-up.

**Approach**: The six-section decomposition is sound:
1. Breaking the paradox down by functional category identifies which gene classes drive the effect, rather than treating all genes uniformly.
2. The condition-type analysis tests whether specific experimental conditions create the burden signal.
3. Trade-off gene analysis (sick in some conditions, beneficial in others) provides the mechanistic explanation for why core genes appear burdensome.
4. The selection-signature 2×2 matrix (costly/neutral × conserved/dispensable) is an elegant synthesis that reframes the paradox as evidence for natural selection.

**Data sources**: Well-identified — the project reuses cached data from `fitness_effects_conservation` and `conservation_vs_fitness`, clearly documented in the README and notebook setup cell. The Dyella79 exclusion (known locus tag mismatch, per `docs/pitfalls.md`) is correctly applied (cell `setup`, line `link = link[link['orgId'] != 'Dyella79']`).

**Reproducibility of reasoning**: The notebook is self-contained and the logic chain from upstream findings to new analysis is traceable.

## Code Quality

**Notebook organization**: Excellent. The notebook follows a clean setup → analysis × 6 → summary structure, with markdown headers separating each section. Each section produces both printed statistics and a saved figure.

**Notebook outputs**: All code cells have saved outputs (text and images confirmed across all 8 code cells). This is a significant strength — a reader can follow the entire analysis without re-execution.

**Figures**: All 6 figures listed in the README exist in the `figures/` directory with reasonable file sizes (56–122 KB). Each corresponds to a major analysis section.

**Statistical methods**:
- Fisher's exact test for trade-off gene enrichment in core (OR=1.29, p=1.2e-44) is appropriate for the 2×2 contingency table.
- However, several other comparisons lack formal statistical tests. The burden rate differences by functional category (Section A) are presented as raw percentage-point differences without confidence intervals or significance tests. Given the large sample sizes, most differences would be significant, but a few categories with smaller gene counts (near the `min_genes >= 50` threshold) could be noise.

**Potential performance issue**: In cell `motility`, the line `by_cond.apply(lambda r: (r['orgId'], r['locusId']) in mot_loci, axis=1)` iterates row-by-row over the full `by_cond` DataFrame using a Python lambda. Since `fitness_stats_by_condition.tsv` is 77 MB, this could be slow. A merge-based approach would be more efficient:
```python
mot_keys = motility[['orgId','locusId']].drop_duplicates()
mot_cond = by_cond.merge(mot_keys, on=['orgId','locusId'], how='inner')
```

**Pitfall awareness**:
- The Dyella79 exclusion (documented in `docs/pitfalls.md` under "FB Locus Tag Mismatch") is correctly handled.
- Essential genes are not explicitly included in this analysis — the focus is on burden (positive fitness), so essential genes (no fitness data) are naturally excluded from burden classification. This is acceptable for the research question but could be noted.
- The project correctly uses cached local data rather than making Spark queries, avoiding API timeout issues.

**Minor code issues**:
- In cell `burden-by-condition`, the `n_beneficial` column from `by_cond` is used to define burden, but `by_cond` comes from `fitness_stats_by_condition.tsv` which has per-condition-type statistics. The column semantics should be verified — if `n_beneficial` counts experiments within a condition type where fit > 1, this is correct; if it's the overall count, the per-condition breakdown may be mixing levels.

## Findings Assessment

**Conclusions supported by data**:
- The function-specific burden pattern (Section A) is well-supported, showing that the paradox is not uniform — Protein Metabolism, Motility, and RNA Metabolism drive the effect while Cell Wall reverses it.
- The trade-off gene enrichment (OR=1.29, p=1.2e-44, Section C) is robustly significant.
- The selection-signature matrix (Section F) provides a compelling synthesis: 28,017 genes that are both costly in the lab and conserved in pangenomes represent the strongest evidence for natural selection maintaining genes despite their lab-measured cost.
- The motility case study (Section E) is an effective illustration of condition-dependent trade-offs.

**Limitations acknowledged**: The README lists four concrete limitations including lab condition bias, the ambiguity of "burden," DIAMOND identity thresholds, and condition-type bias. These are appropriate and honest.

**Completeness**: The analysis is complete — no placeholder cells, no "TODO" markers, and the summary cell successfully prints all key results.

**Visualization quality**: Figures are properly titled and labeled. The paired bar charts (Sections A, B) effectively show core vs non-core comparisons. The 2×2 quadrant figure (Section F) is informative though somewhat dense.

## Suggestions

1. **Add statistical tests to Section A (burden by function)**: The burden rate differences by functional category are presented without significance tests. Add chi-squared tests or Fisher's exact tests for each category, with multiple-testing correction (e.g., Bonferroni or FDR). This would distinguish real functional differences from noise, especially for categories near the 50-gene minimum threshold.

2. **Replace row-wise `apply` with merge in motility analysis**: The `by_cond.apply(lambda r: (r['orgId'], r['locusId']) in mot_loci, axis=1)` pattern in cell `motility` is O(n) with a large constant. Replace with a merge join for better performance:
   ```python
   mot_keys = motility[['orgId','locusId']].drop_duplicates()
   mot_cond = by_cond.merge(mot_keys, on=['orgId','locusId'], how='inner')
   ```

3. **Add a `requirements.txt`**: The project has no dependency specification. While the dependencies are standard (pandas, numpy, matplotlib, scipy), a `requirements.txt` would complete the reproducibility story. The upstream project's README lists `Python 3.10+, pandas, numpy, matplotlib, scipy` — this project should do the same or provide a file.

4. **Document the empty `data/` directory or remove it**: The `data/` directory exists but is empty. Either populate it with intermediate outputs (e.g., the merged DataFrame `m` as a TSV for downstream use) or remove it and update the project structure in the README, which currently does not list it.

5. **Clarify `n_beneficial` column semantics in condition analysis**: In Section B, `n_beneficial` from `fitness_stats_by_condition.tsv` is used to define burden within each condition type. Add a brief comment or markdown note confirming that this column counts within-condition-type experiments where the gene showed positive fitness, not the overall count across all experiments.

6. **Consider adding a combined summary figure**: The project has 6 individual figures but no single summary visualization that ties together the main narrative (function-specific paradox → trade-offs → selection signature). A small multi-panel figure in the README or a final notebook cell could strengthen the presentation. *(Nice-to-have)*

7. **Note essential gene treatment**: The analysis focuses on burden (positive fitness when deleted), so essential genes (no fitness data) are naturally excluded from the burden definition. Adding a brief note in the notebook acknowledging that the 27,693 essential genes are not classified as burdens or non-burdens would prevent reader confusion. *(Nice-to-have)*

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-02-14
- **Scope**: README.md, 1 notebook (01_burden_anatomy.ipynb, 15 cells with saved outputs), 0 data files, 6 figures
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.

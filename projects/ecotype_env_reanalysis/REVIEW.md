---
reviewer: BERIL Automated Review
date: 2026-02-17
project: ecotype_env_reanalysis
---

# Review: Ecotype Reanalysis — Environmental-Only Samples

## Summary

This is a well-motivated, tightly scoped reanalysis that asks whether the weak environment–gene content signal found in the original ecotype analysis was an artifact of clinical sampling bias. The research question is clearly derived from two prior projects, the hypothesis is testable, and the statistical approach (Mann-Whitney U on partial correlations stratified by genome-level environment classification) is appropriate. The REPORT.md is unusually thorough, with honest treatment of a null result and thoughtful interpretation. The main weaknesses are: (1) the notebook has **zero saved outputs** and the figures directory is empty, making it impossible to verify any claims without re-running the analysis; (2) the data files show that many species have NaN partial correlations (empty `r_partial_emb_jaccard` in `ecotype_corr_with_env_group.csv`), suggesting possible data extraction issues that are acknowledged but not fully investigated; and (3) the 27x discrepancy in overall median partial correlations compared to the original analysis is flagged but unresolved, which somewhat undermines confidence in the exact numerical findings.

## Methodology

**Research question**: Clearly stated and testable — "Does the environment effect on gene content become stronger when analysis is restricted to genuinely environmental samples?" The null and alternative hypotheses are well-formulated in RESEARCH_PLAN.md.

**Approach**: Sound. Classifying species by majority genome-level `env_category` (from keyword-harmonized isolation_source) is a meaningful improvement over the original manual species-level categorization. The Mann-Whitney U test with a one-sided alternative is the right choice for comparing medians between groups with different sample sizes and non-normal distributions.

**Data sources**: Clearly identified. The project reuses data from two parent projects (`ecotype_analysis` and `env_embedding_explorer`) with no new BERDL queries. The dependency chain is well-documented in both the README and the notebook markdown header.

**Reproducibility**: Mixed. The README includes a Reproduction section with prerequisites and steps. There is a `requirements.txt` with pinned kaleido version (correctly following the pitfall about kaleido v1 on headless pods). The notebook runs locally without Spark, which is a strength. However, reproduction depends on parent project data files existing at relative paths — this is documented but fragile.

## Code Quality

**Notebook organization**: Logical flow — setup → data loading → species classification → statistical test → visualization → interpretation. Markdown cells provide clear section headers and explanations of each step.

**Code correctness**: The classification logic (cells 7 and 10) is straightforward and correct. The species name matching has a reasonable fallback strategy (cell 10) for handling potential format differences between datasets. The statistical test (cell 13) correctly uses `alternative='greater'` for the one-sided hypothesis.

**Robustness**: The notebook handles missing data gracefully — `FileNotFoundError` with helpful messages (cell 3), fallback column name detection (cells 9, 12, 17), and `dropna()` before statistical tests. However, examining `ecotype_corr_with_env_group.csv`, several large species (e.g., *A. baumannii* with 3,505 genomes, *M. tuberculosis* with 2,556 genomes) have empty `r_partial_emb_jaccard` and `p_partial_emb` values — these NaN species are acknowledged in the report (Finding #4) but their prevalence in the human-associated group could bias the comparison.

**Pitfall awareness**: The project follows relevant pitfalls from `docs/pitfalls.md`:
- Correctly pins `kaleido==0.2.1` (env_embedding_explorer kaleido pitfall)
- Documents the Spark `maxResultSize` issue for K. pneumoniae (ecotype_env_reanalysis pitfall)
- The project itself contributed two pitfalls back to the repository (maxResultSize and broken symlinks), which is good practice

**Minor issues**:
- Cell 7: `species_env['n_env'] = species_env[env_cols].sum(axis=1) if env_cols else 0` — the `if env_cols else 0` check operates on the truthiness of the list, not element-wise. This works because an empty list is falsy, but `if len(env_cols) > 0` would be clearer.
- The `save_fig` function (cell 1) writes both PNG and HTML, which is good practice for interactive Plotly figures.

## Findings Assessment

**Conclusions supported by data**: The null result (p=0.83) is clearly supported, and the report correctly notes that the effect is in the **opposite** direction from the hypothesis (human-associated species have slightly higher partial correlations). The interpretation section (REPORT.md) provides three plausible explanations for why the hypothesis was wrong, demonstrating good scientific reasoning.

**Limitations acknowledged**: Yes, thoroughly. The REPORT.md lists five specific limitations: no downsampling, NaN species exclusion, no saved notebook outputs, K. pneumoniae exclusion, and the majority-vote classification threshold. This is commendably honest.

**Incomplete analysis**: The 27x discrepancy between this reanalysis's median partial correlation (0.081) and the original analysis (0.003) is flagged as the first Future Direction but not resolved. This is a significant methodological concern — if the partial correlations are 27x higher due to methodological differences (no downsampling), then the group comparison might also be affected by these same methodological differences. The report acknowledges this but does not test it (e.g., by repeating the comparison on the original 172-species results with the new classifications).

**Visualizations**: Three visualizations are defined in the notebook (box plot, histogram overlay, scatter plot) — all well-designed with appropriate labels, reference lines, and color coding. However, the `figures/` directory is **completely empty** (no PNG or HTML files), so none of these visualizations actually exist as reviewable artifacts.

## Suggestions

1. **Critical — Execute the notebook and save outputs**: All 14 code cells have empty output arrays, and the figures directory is empty. This is the single most important improvement. Run `jupyter nbconvert --to notebook --execute --inplace notebooks/01_environmental_only_reanalysis.ipynb` to populate outputs. Without this, the notebook is code-only documentation rather than a reproducible analysis record. The REPORT.md itself acknowledges this gap ("notebook pending execution").

2. **Critical — Investigate the 27x partial correlation discrepancy**: The report notes that the median partial correlation is 0.081 in this reanalysis vs 0.003 in the original. Before concluding that clinical bias doesn't matter, verify that the group comparison holds when applied to the original (downsampled) partial correlations. If the original `ecotype_correlation_results.csv` contains the 172-species results with downsampling, re-run the Mann-Whitney U test on those values with the new genome-level classifications. This would control for the methodological difference.

3. **Important — Examine NaN species composition**: 30 of 213 species produced NaN partial correlations and were excluded. From `ecotype_corr_with_env_group.csv`, several of the largest human-associated species (A. baumannii, M. tuberculosis) are among the NaN species. Report the NaN breakdown by group (how many Environmental vs Human-associated species were excluded?) to confirm the exclusion doesn't differentially affect one group.

4. **Important — Consider a continuous analysis**: The report notes (Limitation #5) that majority-vote classification is arbitrary at the 50% threshold. A Spearman correlation between `frac_env` (continuous) and the partial correlation value would be a more powerful test of the same hypothesis with no threshold needed. The data for this is already in `species_env_classification.csv`.

5. **Minor — Add species_env_classification.csv generation to the notebook**: The `species_env_classification.csv` file exists in `data/` with 224 rows, but the notebook code (cell 7) doesn't explicitly save this file. Either the file was generated by a separate script, or the notebook was run in a different form. Add a `species_env.to_csv()` call to the notebook for completeness.

6. **Minor — Fix the README Quick Links**: The REPORT.md link says "(TBD)" but the report is complete. Update to reflect the current status.

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-02-17
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, references.md, requirements.txt, 1 notebook, 2 data files, 0 figures
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.

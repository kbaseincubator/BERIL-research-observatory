---
reviewer: BERIL Automated Review
date: 2026-02-17
project: ecotype_env_reanalysis
---

# Review: Ecotype Reanalysis — Environmental-Only Samples

## Summary

This is a well-executed, tightly scoped reanalysis project that honestly reports a null result. The research question — whether clinical sampling bias in AlphaEarth explains the weak environment–gene content signal — is clearly motivated by two parent projects. The single notebook is well-organized with saved outputs, appropriate statistical tests (Mann-Whitney U and Spearman), and four informative visualizations. The documentation is strong: README, RESEARCH_PLAN, and REPORT all follow the observatory's three-file convention, with thorough interpretation of why the hypothesis was wrong. The project also contributed two pitfalls back to `docs/pitfalls.md`. The main issues are minor: (1) `species_env_classification.csv` is listed in REPORT.md as a generated data file but is not produced by the notebook, creating a reproducibility gap; (2) the 27x discrepancy in median partial correlations versus the original ecotype analysis is documented but not validated; and (3) the environment classification is computed from a downsampled genome subset (~250 per species) while the correlations use the full genome set, which is defensible but undocumented.

## Methodology

**Research question**: Clearly stated, testable, with explicit null and alternative hypotheses in RESEARCH_PLAN.md. The expected outcomes section specifies what each result would mean, which is good scientific practice.

**Approach**: Sound. The improvement over the original ecotype analysis's manual classification (which left 56% of species as "Unknown") is well-motivated. The majority-vote classification by genome-level `isolation_source` is reasonable, and the continuous Spearman analysis using `frac_env` avoids the arbitrary 50% threshold — a valuable robustness check. Using both binary and continuous approaches strengthens the null finding.

**Data sources**: Clearly documented in README, RESEARCH_PLAN, and the notebook header. The project cleanly reuses data from two parent projects with no new BERDL queries, isolating the analytical question from data extraction. Dependencies on parent project files at relative paths (`../../ecotype_analysis/data/`, `../../env_embedding_explorer/data/`) are documented in the README prerequisites.

**Statistical methods**: The Mann-Whitney U test with `alternative='greater'` (one-sided) is appropriate for the directional hypothesis. The Spearman correlation on continuous fraction-environmental is a well-chosen complement. The NaN analysis (cells 10, 21) properly assesses whether differential dropout biases the comparison.

## Reproducibility

**Notebook outputs**: All 16 code cells have saved outputs with text, tables, and figures. The notebook reads as a complete narrative without needing re-execution.

**Figures**: All four key visualizations exist in both PNG and interactive HTML formats (8 files total), covering species classification, box plots, distributions, and the continuous scatter analysis.

**Dependencies**: `requirements.txt` is present with pinned `kaleido==0.2.1`, correctly following the kaleido v1 pitfall from `docs/pitfalls.md`.

**Reproduction guide**: The README includes a clear Reproduction section: prerequisites (Python 3.10+, requirements.txt, parent project data), a single step to run, and correctly notes the notebook runs locally (no Spark needed).

**Data file gap**: The REPORT.md (line 114) lists `data/species_env_classification.csv` (224 rows) as a generated data file. This file exists on disk but is **not produced by the notebook** — the notebook only saves `ecotype_corr_with_env_group.csv` (cell 26). A reader running the notebook from scratch would not regenerate this file. The file appears to have been created separately (timestamp differs: Feb 16 04:02 vs notebook outputs at Feb 17 00:20).

## Code Quality

**Notebook organization**: Excellent logical flow: setup → data loading → species classification → join with correlations → statistical tests → visualizations → NaN analysis → methodological comparison → summary → data export. Markdown cells provide context at each stage.

**Code correctness**: The classification logic (cell 7), statistical tests (cells 12, 14), and NaN analysis (cells 10, 21) are all correct. The one-sided Mann-Whitney U test is properly specified. The `harmonize()` function re-implements keyword-based categorization rather than importing the pre-computed `env_category` column — this is a reasonable choice for self-containment, though a brief note explaining why would help readers verify consistency with the parent project.

**Pitfall awareness**: The project follows relevant pitfalls:
- Pins `kaleido==0.2.1` per the headless pod pitfall
- Documents the Spark `maxResultSize` issue for K. pneumoniae (contributed as a new pitfall)
- Documents broken symlinks to Mac paths (contributed as a new pitfall)
- Follows the three-file structure (README/RESEARCH_PLAN/REPORT)

**Subtle data scope issue**: The `frac_env` and `frac_human` values in the merged CSV are computed from `target_genomes_expanded.csv`, which caps at ~250 genomes per species (the downsampled set). Meanwhile, `n_genomes` reports the full genome count with embeddings (up to 3,505). So the classification uses a subset while the correlations use the full set. This is defensible — the 250-genome sample should be representative — but the discrepancy is not documented in the notebook or report. For example, *A. baumannii* has `n_genomes=3505` but `n_total=250` in the output CSV.

**Minor code style**: In cell 7, `species_env['n_env'] = species_env[env_cols].sum(axis=1) if env_cols else 0` relies on list truthiness. While correct, `if len(env_cols) > 0` would be more explicit.

## Findings Assessment

**Conclusions supported by data**: Yes. The null result (U=1536, p=0.83; Spearman rho=-0.085, p=0.25) is clearly supported by the notebook outputs. The report correctly highlights that the effect is in the *opposite* direction from the hypothesis — human-associated species have slightly higher median partial correlations (0.084 vs 0.051).

**Numerical consistency**: The values in REPORT.md (Table at line 11–15) match the notebook outputs after rounding: Environmental median 0.051 (notebook: 0.0511), range [-0.50, 0.78] (notebook: [-0.4971, 0.7822]), etc. No factual discrepancies found.

**Interpretation quality**: The REPORT.md provides three plausible explanations for the null result: (1) embedding similarity ≠ ecological relevance, (2) clinical pathogens have real geographic structure, (3) genome sampling matters. These are thoughtful and well-reasoned.

**27x discrepancy**: The median partial correlation (0.081) is 27x higher than the original ecotype analysis (0.003). Cell 23 documents the methodological differences (no downsampling, more genomes, different genome sets) and correctly argues this doesn't invalidate the group comparison. However, the discrepancy is only *documented*, not *validated*. Running the Mann-Whitney U test on the original 172-species downsampled partial correlations (which should be available from the parent project) with the new genome-level classifications would confirm robustness. This is listed as Future Direction #1 but would strengthen the current analysis.

**Limitations**: Thoroughly acknowledged — NaN exclusion bias, K. pneumoniae exclusion, majority-vote threshold, no downsampling. The NaN analysis (Environmental: 21% NaN vs Human-associated: 7%) correctly notes this would bias *toward* finding a stronger environmental signal, strengthening the null conclusion.

**Visualizations**: Four figures are clear, properly labeled, and well-chosen for the analysis. The box plot (with individual data points overlaid) is particularly effective at showing the overlapping distributions. Interactive HTML versions are a nice addition.

## Suggestions

1. **Moderate — Save `species_env_classification.csv` from the notebook**: Add a `species_env[['n_env', 'n_human', 'n_total', 'group']].to_csv(...)` call after cell 7. Currently this file exists but is not reproducible from the notebook, yet REPORT.md lists it as a generated output.

2. **Moderate — Validate the null result against the original downsampled correlations**: The original ecotype analysis's 172-species partial correlations (median 0.003) were computed with diversity-maximizing downsampling. Re-running the Mann-Whitney U test on those original values with the new genome-level classifications would confirm the null result is not an artifact of the methodological change. This could be added as a few cells at the end of the notebook.

3. **Minor — Document the genome subset used for classification**: The classification uses `target_genomes_expanded.csv` (up to ~250 genomes per species), while the correlations in `ecotype_correlation_results.csv` use the full genome set (up to 3,505). A brief markdown note explaining this difference and why it's acceptable would help readers.

4. **Minor — Add effect size to complement p-values**: The rank-biserial correlation r = 1 − 2U/(n₁ × n₂) can be computed from the existing U statistic (cell 12) to quantify how trivially small the group difference is. This would strengthen the null interpretation beyond p-values alone.

5. **Minor — Document the re-harmonization choice**: Cell 5 re-implements `harmonize()` rather than importing the pre-computed `env_category` column from the parent project's CSV (which already has it). A brief markdown note explaining why (self-containment, reproducibility) would help readers verify consistency.

6. **Nice-to-have — Multiple testing note**: Two statistical tests are conducted (Mann-Whitney and Spearman). While both support the null and no correction is strictly needed for two tests at p > 0.25, a brief note that no multiple testing correction was applied (and why it's unnecessary given the large p-values) would preempt reviewer questions.

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-02-17
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, references.md, requirements.txt, 1 notebook (16 code cells, all with saved outputs), 2 data files, 4 figures (8 files: PNG + HTML)
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.

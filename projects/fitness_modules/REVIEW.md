---
reviewer: BERIL Automated Review
date: 2026-02-13
project: fitness_modules
---

# Review: Pan-bacterial Fitness Modules via Independent Component Analysis

## Summary

This is a mature, well-executed project that applies robust ICA to decompose RB-TnSeq fitness compendia from 32 organisms into 1,116 stable functional modules, aligns them across species via ortholog fingerprints into 156 cross-organism families, and generates 878 function predictions for hypothetical proteins. The full pipeline — from data exploration through formal benchmarking — is complete, with a standalone benchmark script (`src/run_benchmark.py`) that evaluates four prediction methods across all 32 organisms. The project demonstrates exceptional scientific honesty: the near-zero KO-level precision of module-ICA predictions is clearly explained as a granularity mismatch (modules capture process-level co-regulation, not gene-level molecular function), and the appropriate validation metrics (94.2% cofitness enrichment, 22.7× genomic adjacency enrichment) are used instead. The main areas for improvement are documenting the hyperparameter split between pilot and scale-up organisms, resolving the remaining TIGRFam ID-to-description mapping, and adding a few missing figures.

## Methodology

**Research question**: Clearly stated and testable — "Can we decompose RB-TnSeq fitness compendia into latent functional modules via robust ICA, align them across organisms using orthology, and use module context to predict gene function?" The three sub-goals (decomposition, alignment, prediction) map directly to notebooks 03-06, with NB07 providing formal evaluation.

**Approach**: The methodology is sound and well-grounded in published literature (Borchert et al. 2019). The pipeline follows a rigorous sequence: Marchenko-Pastur eigenvalue thresholding for dimensionality → 30-50× FastICA restarts with DBSCAN stability filtering → Fisher exact enrichment with BH FDR correction → ortholog-group fingerprinting via connected components → hierarchical clustering into families → confidence-scored predictions. Each step is well-motivated with documented parameter choices.

**Data sources**: Clearly identified in the README with a table mapping each `kescience_fitnessbrowser` table to its analytical purpose. The SQL queries use the correct join paths throughout (e.g., `besthitkegg → keggmember → kgroupdesc` for KEGG annotations), correctly applying lessons from documented pitfalls.

**Reproducibility**: Strong overall. The `src/ica_pipeline.py` module and `src/run_benchmark.py` script are self-contained and runnable from the command line. All 32 organisms have corresponding JSON parameter files recording exact hyperparameters. Notebooks use file-existence caching for re-execution. One gap: the `pilot_organisms.csv` was expanded from 5 to 32 organisms during the project, but the notebooks still reference `pilot_ids` as a variable name. The scale-up process itself is not documented in the notebooks — a reader would need to infer that `pilot_organisms.csv` was updated between runs.

## Code Quality

**SQL correctness**: All queries are correct and address known pitfalls:
- String-to-numeric casting is consistently applied (`CAST(fit AS FLOAT)`, `CAST(cor12 AS FLOAT)`) per the pitfall about all fitness browser columns being strings (NB01 cell-9, NB02 cells 4, 6, 8).
- The KEGG join path in NB04 cell-4 correctly goes through `besthitkegg` with the proper join keys (`bk.keggOrg = km.keggOrg AND bk.keggId = km.keggId`), matching the documented pitfall about `keggmember` lacking `orgId`/`locusId`.
- SEED annotations use `seedannotation.seed_desc` directly (NB04 cell-4), correctly avoiding the `seedclass` table which only has EC numbers.
- The `ecnum` column name is correctly used for `kgroupec` (NB04 cell-4).

**Statistical methods**: Appropriate throughout:
- Fisher exact test with BH FDR correction for module enrichment (NB04 cell-6) — standard and correct.
- Mann-Whitney U test for within-module cofitness validation (`run_benchmark.py` lines 613-623) — appropriate non-parametric test for comparing correlation distributions.
- The confidence score in NB06 (`|gene_weight| × -log10(FDR) × (1 + cross_org_bonus)`) is reasonable as a ranking heuristic, though it remains uncalibrated.

**ICA pipeline (`src/ica_pipeline.py`)**: Clean, well-documented, and technically correct:
- Cosine distance clipping (`np.clip(cos_dist, 0, 1, out=cos_dist)`, line 146) correctly addresses the floating-point pitfall documented in `docs/pitfalls.md`.
- Component sign alignment within DBSCAN clusters (lines 159-161) is properly handled via dot-product with a reference vector before averaging.
- Zero-variance genes are handled in `standardize_matrix` (`stds[stds == 0] = 1`).
- The `threshold_membership` function correctly implements the adaptive approach: keep all genes above `min_weight`, cap at `max_members` by taking highest `|weight|`.

**Benchmark script (`src/run_benchmark.py`)**: Comprehensive and well-structured:
- Proper train/test separation (20% holdout, `random_state=42`) prevents data leakage.
- Four methods evaluated at two levels (strict KO match and neighborhood set overlap).
- Vectorized correlation matrix computation is efficient.
- Both cofitness validation (Section 2) and genomic adjacency validation (Section 3) are included.
- Output files (`benchmark_results.csv`, `cofitness_validation.csv`, `adjacency_validation.csv`) are saved for reproducibility.

**Potential issues**:
1. **NB03 cell-8** displays a summary table referencing column `n_components`, but the saved JSON params use key `n_components_used`. This would raise a `KeyError` on re-execution. Minor, since the summary is for display only.
2. **NB02 cell-8**: The `extract_fitness_matrix_fitbyexp` function treats `fitbyexp_*` tables as pre-pivoted wide format, but the documented pitfall notes these tables are actually long format (`expName, locusId, fit, t`). The function would likely fail or return incorrect results, causing the fallback to `extract_fitness_matrix_genefitness` to execute — which is correct. The dead code path is misleading but harmless.
3. **Cofitness validation**: The per-module Mann-Whitney U test uses p < 0.05 without multiple-testing correction across ~1,116 modules. Given that 94.2% pass, FDR correction would likely not change the conclusion materially, but it would be methodologically cleaner.

**Notebook organization**: Excellent. The 7-notebook sequence follows a clear analytical progression. Each notebook has markdown section headers, prints progress summaries, and uses file-existence caching. The Part 1 (Spark) / Part 2 (local) separation in NB04 and NB05 is practical for the cluster environment.

**Pitfall awareness**: Outstanding. The project has contributed 7 fitness-browser-specific pitfalls to `docs/pitfalls.md` (all marked `[fitness_modules]`), including the `fitbyexp_*` long-format discovery, the KEGG join path, the `seedclass` schema issue, the cosine distance clipping fix, the D'Agostino K² thresholding failure, the ortholog scope requirement, and the ICA component ratio cap.

## Findings Assessment

**Conclusions well-supported by data**:
- **1,116 stable modules** across 32 organisms — verified by data files (192 module files across 32 organisms, corresponding JSON params).
- **94.2% cofitness enrichment** — validated by `cofitness_validation.csv` and `cofitness_validation_summary.csv` with per-module Mann-Whitney U statistics.
- **22.7× genomic adjacency enrichment** — validated by `adjacency_validation.csv` with per-organism enrichment calculations.
- **878 function predictions** across 29 organisms — verified by 29 per-organism prediction files and `all_predictions_summary.csv` (493 family-backed, 385 module-only).
- **156 cross-organism families** (28 spanning 5+ organisms, 7 spanning 10+, 1 spanning 21) — verified by `module_families.csv` and `family_annotations.csv`.
- **Ortholog transfer at 95.8% precision** — produced by `run_benchmark.py` and saved in `benchmark_results.csv`.
- **Module-ICA at <1% strict KO precision** — correctly explained as a granularity mismatch, not a pipeline failure.

**Limitations well-acknowledged**:
- The KO-level precision limitation is explicitly discussed (README, NB07 cell-6 markdown) with a clear explanation of why modules capture process-level co-regulation rather than specific molecular function.
- The D'Agostino K² thresholding failure and its resolution are documented (README Key Findings #1).
- The complementary nature of module-ICA vs. sequence-based methods is stated as a conclusion.
- TIGRFam ID resolution is listed as remaining work.

**Limitations not discussed**:
- The NaN imputation with 0.0 for missing fitness values (NB02 cell-9, up to 50% missing allowed) could bias ICA toward weaker modules for genes with sparse fitness data. No sensitivity analysis is provided.
- About 30% of modules hit the `max_members=50` cap (visible from the JSON params files), meaning their effective threshold was raised above 0.3. This design trade-off is not discussed.
- The two hyperparameter regimes (50 runs/25 min_samples for initial organisms vs. 30 runs/15 min_samples for later organisms) are not documented or justified.

**Visualizations**: Three benchmark figures exist (`benchmark_strict.png`, `benchmark_neighborhood.png`, `benchmark_comparison.png`) — properly labeled with error bars. The PCA eigenvalue plot and module size distribution referenced in NB03 are not present in `figures/`, likely lost during the scale-up to 32 organisms.

## Suggestions

1. **[Important] Document the ICA hyperparameter split.** Some organisms were run with `n_runs=50, min_samples=25` while others used `n_runs=30, min_samples=15`. Add a note in the README or NB03 explaining whether this reflects a pilot-vs-production split or was tuned per organism, and whether the different settings affect module quality comparably.

2. **[Important] Complete TIGRFam ID resolution.** The `genedomain` extraction in NB04 already captures `domainName` and `definition` columns, and KEGG queries capture `kgroup_desc`. Propagating these human-readable descriptions through NB06 to `all_predictions_summary.csv` would substantially improve prediction usability. This is listed as remaining work in the README.

3. **[Moderate] Fix the NB03 cell-8 params key.** The summary display references `n_components` but the JSON uses `n_components_used`. Change the display column to match the actual key to avoid a `KeyError` on re-execution.

4. **[Moderate] Re-generate missing NB03 figures.** The `pca_eigenvalues.png` and `module_size_distribution.png` files referenced in NB03 cells 4 and 9 are not present in `figures/`. These are useful for understanding dimensionality selection and module size distributions across all 32 organisms.

5. **[Moderate] Apply FDR correction to cofitness validation.** The 94.2% enrichment uses per-module p < 0.05 across ~1,116 modules. Applying BH correction (as already done for Fisher enrichments in NB04) would be methodologically consistent. The result is likely robust given the high pass rate, but correction would preempt reviewer concerns.

6. **[Nice-to-have] Rename `pilot_organisms.csv` to `selected_organisms.csv`.** Now that the file contains all 32 organisms, the "pilot" naming is misleading. Similarly, renaming `pilot_ids` to `org_ids` in notebook code would reduce cognitive overhead.

7. **[Nice-to-have] Add a `requirements.txt` or `environment.yml`.** The project depends on `scikit-learn`, `scipy`, `statsmodels`, `networkx`, `matplotlib`, and `pandas`. The inline `pip install` in NB03 cell-1 is fragile. A declarative dependency file would improve reproducibility.

8. **[Nice-to-have] Discuss the `max_members=50` cap saturation.** Since roughly 30% of modules hit this cap, acknowledging this as a design trade-off (focused modules vs. potential information loss) would strengthen the methods section. Consider whether an organism-scaled cap (e.g., 1-2% of genes) might be more appropriate for larger genomes.

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-02-13
- **Scope**: README.md, 7 notebooks, 2 source files (`src/ica_pipeline.py`, `src/run_benchmark.py`), ~485 data files across 6 subdirectories (`matrices/`, `modules/`, `annotations/`, `orthologs/`, `module_families/`, `predictions/`), 3 figures
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.

---
reviewer: BERIL Automated Review
date: 2026-02-13
project: fitness_modules
---

# Review: Pan-bacterial Fitness Modules via Independent Component Analysis

## Summary

This is a well-executed project that applies robust ICA to decompose RB-TnSeq fitness compendia from 32 organisms into 1,116 stable functional modules, aligns them across species via ortholog fingerprints into 156 cross-organism families, and generates 878 function predictions for hypothetical proteins. The pipeline spans 7 notebooks and 2 standalone scripts, with strong reproducibility: NB03-07 have saved outputs, data files are cached for re-execution, and a standalone benchmark script enables independent validation. The project demonstrates commendable scientific honesty — the near-zero KO-level precision of module-ICA is clearly explained as a granularity mismatch, and appropriate validation metrics (94.2% cofitness enrichment, 22.7× adjacency enrichment) are presented instead. The main areas for improvement are the very sparse functional annotation of modules (only 9% have significant enrichments, driven by the `min_annotated=3` threshold vs. KEGG's 1-gene-per-KO granularity), the undocumented split between two ICA hyperparameter regimes (50 vs. 30 runs), and the TIGRFam IDs remaining unresolved to human-readable descriptions in predictions.

## Methodology

**Research question**: Clearly stated and testable — "Can we decompose RB-TnSeq fitness compendia into latent functional modules via robust ICA, align them across organisms using orthology, and use module context to predict gene function?" The three sub-goals (decomposition, alignment, prediction) map directly to notebooks 03-06, with NB07 providing formal evaluation.

**Approach**: The methodology is sound and well-grounded in published literature (Borchert et al. 2019). The pipeline follows a rigorous sequence: Marchenko-Pastur eigenvalue thresholding for dimensionality → 30-50× FastICA restarts with DBSCAN stability filtering → Fisher exact enrichment with BH FDR correction → ortholog-group fingerprinting via connected components → hierarchical clustering into module families → confidence-scored predictions. Each step is well-motivated.

**Data sources**: Clearly identified in the README with a table mapping each `kescience_fitnessbrowser` table to its use. The SQL queries use the correct join paths throughout (e.g., `besthitkegg → keggmember → kgroupdesc` for KEGG annotations), correctly applying lessons from documented pitfalls.

**Reproducibility strengths**:
- The README includes a thorough `## Reproduction` section separating JupyterHub-dependent steps (NB01-02) from locally-runnable steps (NB03-07), with exact `nbconvert` commands and estimated runtimes.
- A `requirements.txt` is present with 7 pinned dependencies (scikit-learn, scipy, statsmodels, networkx, matplotlib, pandas, numpy).
- NB03-07 all have saved outputs (tables, figures, text summaries). NB01-02 intentionally lack outputs (noted in their headers) since they require Spark, but their cached data files are present.
- All 32 organisms have JSON parameter files recording exact ICA hyperparameters, enabling reproducibility verification.
- `src/run_benchmark.py` can be run standalone: `python src/run_benchmark.py`.

**Reproducibility gaps**:
- NB01-02 have zero saved outputs across 18 code cells. While this is noted as intentional (JupyterHub dependency), it means a reader cannot see the organism selection rationale or matrix extraction summaries without re-running on the cluster.
- The `pilot_organisms.csv` was expanded from 5 to 32 organisms during the project, but the expansion process is not documented. The file and variable names still use "pilot" throughout, which is misleading.
- Two different ICA hyperparameter regimes were used (50 runs / 25 min_samples for 12 organisms; 30 runs / 15 min_samples for 20 organisms), but this is not documented anywhere. The NB03 code hardcodes `N_RUNS = 30`, suggesting the 50-run organisms were processed in an earlier iteration.

## Code Quality

**SQL correctness**: All queries are correct and address known pitfalls:
- String-to-numeric casting is consistently applied (`CAST(fit AS FLOAT)`, `CAST(cor12 AS FLOAT)`) per the pitfall about all fitness browser columns being strings (NB01 cell-9, NB02 cells 4, 6, 8).
- The KEGG join path in NB04 cell-4 correctly goes through `besthitkegg` with proper join keys (`bk.keggOrg = km.keggOrg AND bk.keggId = km.keggId`), matching the documented pitfall about `keggmember` lacking `orgId`/`locusId`.
- SEED annotations use `seedannotation.seed_desc` directly (NB04 cell-4), correctly avoiding the `seedclass` table.
- The `ecnum` column name is correctly used for `kgroupec` (NB04 cell-4).

**Statistical methods**: Appropriate throughout:
- Fisher exact test with BH FDR correction for module enrichment (NB04 cell-6).
- Mann-Whitney U test for within-module cofitness validation (`run_benchmark.py` lines 613-623).
- Marchenko-Pastur eigenvalue thresholding for dimensionality selection (well-implemented in `ica_pipeline.py` lines 27-74).
- The confidence score in NB06 (`|gene_weight| × -log10(FDR) × (1 + cross_org_bonus)`) is reasonable as a ranking heuristic, though it remains uncalibrated.

**ICA pipeline (`src/ica_pipeline.py`)**: Clean, well-documented, and technically correct:
- Cosine distance clipping (`np.clip(cos_dist, 0, 1, out=cos_dist)`, line 146) correctly addresses the floating-point pitfall documented in `docs/pitfalls.md`.
- Component sign alignment within DBSCAN clusters (lines 159-163) is properly handled via dot-product with a reference vector before averaging.
- Zero-variance genes handled in `standardize_matrix` (line 292: `stds[stds == 0] = 1`).
- The `threshold_membership` function correctly implements the adaptive approach: keep all genes above `min_weight`, cap at `max_members` by taking highest `|weight|`.

**Benchmark script (`src/run_benchmark.py`)**: Comprehensive and well-structured:
- Proper train/test separation (20% holdout, `random_state=42`) prevents data leakage.
- Four methods evaluated at two levels (strict KO match and neighborhood set overlap).
- Vectorized correlation matrix computation is efficient.
- Both cofitness validation (Section 2) and genomic adjacency validation (Section 3) are included.
- All outputs saved to CSV for reproducibility.

**Potential issues**:
1. **NB02 cell-8**: The `extract_fitness_matrix_fitbyexp` function treats `fitbyexp_*` tables as pre-pivoted wide format, but the documented pitfall notes these are actually long format (`expName, locusId, fit, t`). The function would fail, triggering the correct fallback to `extract_fitness_matrix_genefitness`. The dead code path is misleading but harmless.
2. **Cofitness validation**: The per-module Mann-Whitney U test uses p < 0.05 without multiple-testing correction across ~1,116 modules. Given the 94.2% pass rate, FDR correction would likely not change the conclusion, but it would be methodologically consistent with the BH correction used in NB04.
3. **NaN imputation**: Missing fitness values are filled with 0.0 (NB02 cell-9), with up to 50% missing allowed per gene. This could bias ICA toward weaker signals for genes with sparse data. No sensitivity analysis is provided.

**Notebook organization**: Excellent. The 7-notebook sequence follows a clear analytical progression (explore → extract → decompose → annotate → align → predict → benchmark). Each notebook has markdown section headers, prints progress summaries, and uses file-existence caching for idempotent re-execution. The Part 1 (Spark) / Part 2 (local) separation in NB04 and NB05 is practical.

**Pitfall awareness**: Outstanding. The project has contributed 7 fitness-browser-specific pitfalls to `docs/pitfalls.md` (all marked `[fitness_modules]`), including the `fitbyexp_*` long-format discovery, the KEGG join path, the `seedclass` schema issue, the cosine distance clipping fix, the D'Agostino K² thresholding failure, the ortholog scope requirement, and the ICA component ratio cap.

## Findings Assessment

**Conclusions well-supported by data**:
- **1,116 stable modules** across 32 organisms — verified by 192 module data files and 32 JSON parameter files. NB03 cell-8 output confirms 1,117 stable modules with 1,116 having members.
- **94.2% cofitness enrichment** — validated by `cofitness_validation.csv` (1,049/1,114 modules enriched) with per-module Mann-Whitney U statistics. Mean within-module |r| = 0.34 vs. background |r| = 0.12 (2.8× enrichment).
- **22.7× genomic adjacency enrichment** — validated by `adjacency_validation.csv` with per-organism fold-enrichment ranging from 4.1× to 66.8×.
- **878 function predictions** across 29 organisms — verified by 29 per-organism prediction files and `all_predictions_summary.csv` (493 family-backed, 385 module-only).
- **156 cross-organism families** (28 spanning 5+, 7 spanning 10+, 1 spanning 21) — verified by `module_families.csv` and `family_annotations.csv`.
- **Ortholog transfer at 95.8% precision** — confirmed in NB07 cell-3 output and `benchmark_results.csv`.

**Limitations well-acknowledged**:
- The KO-level precision limitation is explicitly discussed (README, NB07 cell-6 markdown) with a clear explanation of the granularity mismatch.
- The D'Agostino K² thresholding failure is documented (README Key Findings #1).
- The complementary nature of module-ICA vs. sequence-based methods is clearly stated.
- TIGRFam ID resolution is listed as remaining work.

**Limitations not discussed**:
- **Low functional annotation rate**: Only 92/1,020 modules (9.0%) have at least one significant functional enrichment (confirmed by NB04 cell-9 output: "Mean annotation rate: 8.8%"). This is driven by the `min_annotated=3` threshold in the Fisher exact test (NB04 cell-6): KEGG groups have a median of 1 gene per KO (only 48/1,256 KO groups in DvH have 3+ genes), and most TIGRFam terms also have fewer than 3 genes per organism. While the `min_annotated=3` requirement is statistically sound (needed for meaningful enrichment), its interaction with the fine-grained annotation databases means 91% of modules remain unlabeled. This severely limits the function prediction pipeline — NB06 can only generate predictions for genes in the 9% of annotated modules, and 3 organisms (Methanococcus_S2, Caulo, Korea) had zero enrichments, producing no predictions at all. The README does not discuss this limitation.
- **Two ICA hyperparameter regimes**: 12 organisms were run with 50 ICA restarts / 25 min_samples, while 20 used 30 / 15. This is visible in the JSON params but undocumented in any notebook or the README. The first 12 correspond to organisms processed before NB03's hardcoded parameters were changed, suggesting a pipeline evolution that was not documented.
- **NaN imputation at 0.0**: Up to 50% missing fitness values are filled with 0.0 (NB02 cell-9). Since 0 means "no fitness effect," this artificially inflates the number of neutral conditions for sparse genes, potentially weakening their ICA weights.
- **~30% of modules hit the `max_members=50` cap** (visible from JSON params), meaning their effective threshold was raised above 0.3. This design trade-off is not discussed.

**Visualizations**: 8 figures are present in `figures/`: `pca_eigenvalues.png`, `module_size_distribution.png`, `enrichment_summary.png`, `module_families.png`, `prediction_summary.png`, `benchmark_strict.png`, `benchmark_neighborhood.png`, and `validation_summary.png`. These cover the major analysis stages well. All figures referenced in NB03-07 are generated and saved.

## Suggestions

1. **[Critical] Address the low module annotation rate.** Only 9% of modules have functional enrichments, which fundamentally limits the prediction pipeline. Consider: (a) lowering `min_annotated` to 2 (trading statistical power for coverage), (b) using broader annotation categories (e.g., KEGG pathway or module level rather than individual KOs), (c) adding COG category enrichment (coarser granularity, better coverage), or (d) at minimum, documenting this limitation prominently in the README alongside the 878 predictions figure to contextualize how many modules were eligible for prediction.

2. **[Important] Document the ICA hyperparameter split.** The first 12 organisms used `n_runs=50, min_samples=25` while the remaining 20 used `n_runs=30, min_samples=15`. Add a note in the README or NB03 explaining this split (pilot iteration vs. scale-up optimization) and whether the different settings produce comparable module quality. Consider whether re-running the first 12 with the final parameters would improve consistency.

3. **[Important] Complete TIGRFam ID resolution.** The current top predictions (e.g., `TIGR00254`, `TIGR03506`) are opaque identifiers. The `genedomain` extraction in NB04 already captures `domainName` and `definition` columns. Propagating these human-readable descriptions through NB06 to `all_predictions_summary.csv` would substantially improve prediction usability and is listed as remaining work.

4. **[Moderate] Apply FDR correction to cofitness validation.** The 94.2% enrichment uses per-module p < 0.05 across ~1,114 modules without multiple-testing correction. Applying BH correction (as already done for Fisher enrichments in NB04) would be methodologically consistent. The result is likely robust given the high pass rate, but correction would preempt reviewer concerns.

5. **[Moderate] Add outputs to NB01-02 or provide summary tables.** These notebooks have zero saved outputs across 18 code cells. While the Spark dependency is noted, including the key summary outputs (organism ranking table, matrix dimensions, QC filtering statistics) would let readers understand the selection rationale without cluster access. Even screenshot-style markdown summaries would help.

6. **[Moderate] Rename `pilot_organisms.csv` and variable names.** The file contains all 32 organisms, not a pilot subset. Renaming to `selected_organisms.csv` (or `organisms.csv`) and updating the `pilot_ids` variable in notebooks to `org_ids` would reduce confusion. NB07 already uses `org_ids`.

7. **[Nice-to-have] Discuss the `max_members=50` cap saturation.** Since roughly 30% of modules hit this cap, acknowledging this as a design trade-off (focused modules vs. potential information loss) would strengthen the methods section. An organism-scaled cap (e.g., 1-2% of genes) might be more appropriate for genomes ranging from 1,244 to 6,384 genes.

8. **[Nice-to-have] Add sensitivity analysis for NaN imputation.** The 0.0 fill for missing fitness values (up to 50% missing per gene) could bias results. A brief comparison of module composition with vs. without high-missingness genes (e.g., genes with >25% missing) would validate robustness.

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-02-13
- **Scope**: README.md, 7 notebooks (NB01-07), 2 source files (`src/ica_pipeline.py`, `src/run_benchmark.py`), `requirements.txt`, ~487 data files across 6 subdirectories, 8 figures
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.

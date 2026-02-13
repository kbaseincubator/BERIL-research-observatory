---
reviewer: BERIL Automated Review
date: 2026-02-13
project: fitness_modules
---

# Review: Pan-bacterial Fitness Modules via Independent Component Analysis

## Summary

This project applies robust ICA (Independent Component Analysis) to decompose RB-TnSeq fitness compendia from the Fitness Browser into latent functional modules, align them across organisms via ortholog fingerprints, and predict gene function for unannotated genes. The work is ambitious and well-structured, with clear progression from exploration (NB01) through ICA decomposition (NB03), functional annotation (NB04), cross-organism alignment (NB05), function prediction (NB06), and benchmarking (NB07). The project successfully scaled from a planned 5-organism pilot to 32 organisms, producing 1,077 stable modules and 878 function predictions. However, the analysis has several notable gaps: the formal benchmarking notebook (NB07) appears not to have been fully executed, there are stale documentation artifacts referencing superseded methodology, and the KEGG and SEED annotation SQL queries in NB04 reference table schemas that are documented as incorrect in `docs/pitfalls.md`.

## Methodology

**Approach**: The Borchert et al. (2019) robust ICA approach is sound and well-implemented. The pipeline (`src/ica_pipeline.py`) correctly normalizes component vectors, uses absolute cosine similarity (to handle ICA sign ambiguity), aligns signs within DBSCAN clusters before computing centroids, and clips floating-point artifacts from the distance matrix. The Marchenko-Pastur eigenvalue threshold for component selection is a principled choice over simpler heuristics.

**Reproducibility**: The project is reasonably reproducible. All notebooks use checkpointing (file existence checks before re-running steps), which is good practice documented in `docs/pitfalls.md`. The 32 JSON parameter files in `data/modules/` record exact ICA hyperparameters per organism. However, there are inconsistencies:

- NB03 hardcodes `N_RUNS = 100`, but actual runs used 30 or 50 (visible in the JSON params files). The code was clearly modified between the notebook source and actual execution, but the notebook source was not updated to reflect what was actually run.
- Some organisms used `n_runs=50, min_samples=25` (DvH, Btheta, Putida, Caulo, psRCH2, Methanococcus_S2, Phaeo, Marino, pseudo3_N2E3, Koxy, Cola, WCS417) while others used `n_runs=30, min_samples=15` (Keio, SB2B, and many others). The rationale for this split is not documented.
- The JSON params files contain fields not in the NB03 code (`n_components_mp`, `n_components_used`, `min_weight`, `max_members`, `elapsed_seconds`), suggesting the actual execution used a more mature version of the pipeline than what is in the committed notebook.

**Data source clarity**: Good. The README clearly lists all tables used from `kescience_fitnessbrowser`, and the SQL queries in NB01-NB02 are readable and well-commented. The data flow from Spark extraction (JupyterHub) to local analysis is cleanly separated.

## Code Quality

**SQL correctness -- known issues in NB04**:

1. **KEGG query uses incorrect schema**: NB04 cell 4 queries `keggmember` with `km.locusId` and `km.orgId`, but `docs/pitfalls.md` (lines 397-412) explicitly documents that `keggmember` does NOT have `orgId` or `locusId` columns. The correct join path is through `besthitkegg`. The fact that predictions were successfully generated suggests either: (a) the cached data files were produced by a corrected query not reflected in the notebook, or (b) the pitfalls documentation was added after the query was run and the schema was subsequently changed. Either way, the notebook code as committed will fail if re-run.

2. **SEED annotation query uses incorrect schema**: NB04 cell 4 joins `seedannotation` to `seedclass` on `sa.seed_desc = sc.seed_desc` and selects `sc.subsystem, sc.category1, sc.category2, sc.category3`. But `docs/pitfalls.md` (lines 416-418) states that `seedclass` has columns `orgId, locusId, type, num` (EC numbers), not subsystem categories. The LEFT JOIN would silently produce NULL values for all `seedclass` columns, and the downstream code in NB04 cell 7 checks `if 'subsystem' in seed.columns` -- which guards against a crash but would silently skip SEED-based enrichment if the schema mismatch is real.

3. **kgroupec column name**: NB04 references `ke.ec` but `docs/pitfalls.md` (line 414) states the column is `ecnum`, not `ec`.

**Statistical methods**: Generally solid.

- Fisher exact test with BH FDR correction for enrichment analysis is appropriate (NB04).
- The confidence score formula in NB06 (`gene_weight * -log10(FDR) * (1 + cross_org_bonus)`) is reasonable but ad hoc. The multiplicative combination of weight and significance can produce extreme values, and there is no calibration or validation of whether the confidence score correlates with prediction accuracy.
- The benchmarking in NB07 correctly holds out 20% of annotated genes and evaluates at the KEGG group level. However, the benchmark file (`data/predictions/benchmark_results.csv`) contains within-module cofitness enrichment data (columns: `orgId, module, mean_within, overall_median, enriched`), not the NB07 benchmark output (which should have columns: `orgId, method, n_test, n_predicted, n_correct, precision, coverage`). This indicates NB07 was not fully executed, or its output was overwritten.

**Pitfall awareness**: The code correctly handles several documented pitfalls:
- Casts string-typed fitness columns to numeric (`CAST(cor12 AS FLOAT)` in NB01/NB02).
- Clips cosine distance matrix to [0,1] before DBSCAN (documented pitfall, implemented in `ica_pipeline.py` line 146).
- Caps `n_components` at 40% of experiments (documented pitfall, although this is done manually per-organism rather than enforced in code -- visible in JSON params where `n_components_used` is sometimes less than `n_components_mp`).

**Notebook organization**: Clean and logical. The 7-notebook sequence follows a clear analytical progression. Each notebook has clear section headers, prints summaries, and saves intermediate outputs. The separation of Spark-dependent code (Parts 1) from local code (Parts 2) in NB04/NB05 is practical.

**Stale documentation in `src/ica_pipeline.py`**: The module docstring (line 9) and NB03 header still reference "D'Agostino K-squared normality test" for membership thresholding, but the actual implementation (`threshold_membership`) uses absolute weight thresholds. The README correctly documents this methodological change and its impact (from 59% to 93% enriched modules), but the code docstring was not updated.

## Findings Assessment

**Supported conclusions**:
- The claim of 1,077 stable modules across 32 organisms is supported by the 32 JSON params files, which sum to 1,077 stable modules (verified).
- The 93.2% within-module cofitness enrichment claim is supported by `benchmark_results.csv`, which contains per-module enrichment data.
- The 878 function predictions across 29 organisms are supported by the 29 per-organism prediction files and `all_predictions_summary.csv`.

**Partially supported conclusions**:
- The README claims "27 module families spanning 2+ organisms" which is supported by `family_annotations.csv` (27 rows). However, only 3 of 27 families have any functional annotation (F043: TIGR02532, F067: CorC efflux, F105: TIGR03506), with the remaining 24 labeled "unannotated". The cross-organism alignment is statistically thin -- using only BBH orthologs from 5 pilot organisms (not all 32), and the hierarchical clustering threshold (t=0.7) is not justified.
- The benchmarking claims in the README ("module-based predictions outperform cofitness voting alone") are NOT supported by the data. The `benchmark_results.csv` file contains cofitness enrichment data, not the comparative benchmark output expected from NB07. No precision/recall/F1 comparison between Module-ICA, Cofitness, Ortholog, and Domain baselines exists in the data outputs.

**Limitations not acknowledged**:
- The cross-organism alignment (NB05) was only run on the original 5 pilot organisms, not all 32. The README's "Results" section does not make this scope limitation clear.
- The NB07 cofitness voting baseline (`cofit_predict`) computes pairwise correlations on-the-fly for each test gene against all training genes, which is O(n^2) and very slow. This likely explains why NB07 was not fully executed.
- Predictions use TIGRFam domain IDs as functional labels (e.g., "TIGR02532") rather than human-readable function descriptions. This limits interpretability.
- The `max_members=50` cap is applied uniformly. For large organisms like Cup4G11 (6,384 genes), this cap may be too restrictive; for small ones like Methanococcus_S2 (1,244 genes), it may be too permissive.
- NaN imputation with 0.0 for missing fitness values (NB02 cell 9) assumes no phenotype, which may bias ICA decomposition for genes with partial data.

## Suggestions

1. **Fix the KEGG annotation SQL in NB04** to use the correct join path through `besthitkegg` as documented in `docs/pitfalls.md` (lines 399-411). Verify whether the cached annotation CSV files were produced by the incorrect query or a corrected one, and re-run enrichment analysis if needed.

2. **Update the `ica_pipeline.py` module docstring** (line 9) and NB03 markdown header to reflect the actual methodology (absolute weight thresholding, not D'Agostino K-squared). The README correctly documents the change, but the code-level documentation is stale.

3. **Complete and run NB07 (benchmarking)** to produce the actual precision/coverage comparison between Module-ICA, Cofitness, Ortholog, and Domain methods. Until this is done, remove the claim from the README that "module-based predictions outperform cofitness voting alone" (Expected Outcomes point 4). Consider pre-computing the correlation matrix once per organism to make the cofitness baseline tractable.

4. **Document the ICA hyperparameter variation** across organisms (n_runs=30 vs. 50, min_samples=15 vs. 25). Either standardize to a single configuration or add a paragraph in the README explaining the rationale for organism-specific tuning.

5. **Extend cross-organism alignment to all 32 organisms**. Currently NB05 only uses BBH pairs among the original 5 pilots, but ICA decomposition was completed for 32 organisms. This is the most impactful next step for the project's "pan-bacterial" framing.

6. **Replace TIGRFam IDs with human-readable function descriptions** in predictions. The `genedomain` table includes `domainName` and `definition` columns that are already extracted in NB04 but not propagated to the prediction output.

7. **Add a `requirements.txt` or `environment.yml`** to the project directory. The notebooks import `scikit-learn`, `scipy`, `statsmodels`, `networkx`, and `matplotlib`, but dependencies are not declared anywhere. The inline pip install in NB03 cell 1 is fragile.

8. **Validate NaN imputation strategy**. The current approach of filling missing fitness values with 0.0 (NB02 cell 9) assumes neutrality for untested gene-condition pairs. Consider comparing results with alternative imputation methods (e.g., row-mean imputation, or simply excluding genes with >20% missing data) as a sensitivity analysis.

9. **Address the SEED annotation schema mismatch** in NB04. Verify whether `seedclass` actually has `subsystem` columns in the current database, or if the query silently produces NULLs. If SEED subsystem enrichment is not functional, remove it from the annotation sources or fix the query.

10. **Reconcile NB03 source code with actual execution**. The committed NB03 shows `N_RUNS = 100` but all JSON params show 30 or 50 runs. Update the notebook source to reflect the actual parameters used, or add a note explaining that the notebook source represents the initial configuration while the JSON params record what was actually run.

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-02-13
- **Scope**: README.md, 7 notebooks, 32 data files (ICA params JSON), 1 source module, 1 pitfalls doc, 32 fitness matrices, 29 prediction files, 2 module family files
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.

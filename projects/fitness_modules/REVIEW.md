---
reviewer: BERIL Automated Review
date: 2026-02-13
project: fitness_modules
---

# Review: Pan-bacterial Fitness Modules via Independent Component Analysis

## Summary

This project applies robust ICA to decompose RB-TnSeq fitness data from 32 organisms in the Fitness Browser into 1,117 stable functional modules, aligns them across organisms via ortholog fingerprints into 156 cross-organism families, and generates 878 function predictions for unannotated genes. Since the prior review, the authors have addressed the most critical issues: the NB04 KEGG SQL was corrected to use the proper join path through `besthitkegg`, the stale D'Agostino K-squared references in `src/ica_pipeline.py` were removed, the SEED annotation query was simplified to avoid the broken `seedclass` join, and the cross-organism alignment was expanded from 5 to all 32 organisms. The project is now substantially more complete, with consistent data artifacts across all 32 organisms (matrices, modules, annotations, predictions, and families). The main remaining gaps are the unexecuted formal benchmark (NB07) and a minor module count discrepancy in the README.

## Methodology

**Approach**: The Borchert et al. (2019) robust ICA methodology remains sound and well-implemented. The pipeline in `src/ica_pipeline.py` correctly handles ICA sign ambiguity via absolute cosine similarity, aligns component signs within DBSCAN clusters before averaging centroids, and clips the distance matrix to avoid floating-point artifacts. The Marchenko-Pastur eigenvalue threshold for component selection is appropriate. The module docstring (line 5) now correctly describes the actual methodology: "Threshold membership via absolute weight cutoff (|r| >= 0.3, max 50 genes)."

**Reproducibility**: Improved since the prior review. All 32 JSON parameter files in `data/modules/` record exact hyperparameters per organism, providing a reproducibility record. The NB03 source code now shows `N_RUNS = 30` and `MIN_SAMPLES = 15`, which matches the parameters actually used for the second batch of organisms. There is still an acknowledged split in hyperparameters: 12 organisms used `n_runs=50, min_samples=25` (DvH, Btheta, Caulo, psRCH2, Methanococcus_S2, Putida, Phaeo, Marino, pseudo3_N2E3, Koxy, Cola, WCS417) while the remaining 20 used `n_runs=30, min_samples=15`. The NB03 source code reflects the second configuration. The rationale is still not documented, though it plausibly represents the initial pilot configuration (50 runs) vs. the scaled-up configuration (30 runs for efficiency). All runs achieved 100% convergence.

**Data source clarity**: Good. The README clearly lists all BERDL tables, the SQL in NB01-NB04 is readable, and the Spark/local separation in NB04 and NB05 is cleanly handled. The `pilot_organisms.csv` file was expanded from the original 5 to 32 organisms, though the variable name `pilot_ids` persists throughout the notebook code -- a cosmetic issue that does not affect correctness.

## Code Quality

**SQL correctness -- prior issues resolved**:
1. The NB04 KEGG query (cell 4) now correctly joins through `besthitkegg` (`bk.keggOrg = km.keggOrg AND bk.keggId = km.keggId`) rather than the previously incorrect `km.locusId`/`km.orgId` path. The column name `ke.ecnum` is also correct per the schema.
2. The NB04 SEED query (cell 4) now directly selects `locusId, seed_desc` from `seedannotation` without the broken `seedclass` join.
3. The NB04 enrichment code (cell 7) correctly groups SEED annotations by `seed_desc` to build the annotation map.

**Statistical methods**: Generally solid.
- Fisher exact test with BH FDR correction for enrichment analysis is appropriate (NB04 cell 6).
- The within-module cofitness validation (NB07 cell 19) uses gene-pair correlation distributions, which is the right validation metric.
- The genomic adjacency validation (NB07 cell 21) checks operon proximity, a biologically motivated validation.
- The confidence score in NB06 (`gene_weight * -log10(FDR) * (1 + cross_org_bonus)`) is reasonable but remains ad hoc and uncalibrated. There is no evaluation of whether higher confidence scores actually correlate with prediction accuracy.

**Pipeline code (`src/ica_pipeline.py`)**: Well-structured with clean separation of concerns across five functions: `standardize_matrix`, `select_n_components`, `robust_ica`, `compute_gene_weights`, and `threshold_membership`. The Pearson correlation computation in `compute_gene_weights` (lines 200-215) is implemented efficiently via normalized dot products. The `threshold_membership` function (line 220) correctly implements the adaptive threshold: keep all genes above `min_weight` unless more than `max_members` pass, in which case take the top `max_members`.

**Module cap saturation**: 336 out of 1,116 modules with members (30.1%) hit the `max_members=50` cap. For organisms like Keio, 22 of 38 modules are capped. This suggests the cap is binding frequently, and the effective threshold is being raised well above 0.3 for many modules (e.g., Keio M006 has effective threshold 0.42, Putida M011 has 0.51). This is not necessarily wrong -- it is working as designed to keep modules focused -- but the high cap rate merits discussion. Module membership is being truncated for nearly a third of modules.

**Notebook organization**: Clean and logical. The 7-notebook sequence follows a clear analytical progression. Each notebook has section headers, prints summaries, and uses file-existence caching. The Part 1 (Spark) / Part 2 (local) separation in NB04 and NB05 is practical.

## Findings Assessment

**Supported conclusions**:
- The README claims "1,077 stable modules" but the 32 JSON params files sum to 1,117 (`n_stable_modules`) with 1,116 having members. This is a data/README mismatch that should be corrected.
- The 156 cross-organism module families spanning 2+ organisms is verified by `family_annotations.csv` (156 data rows). The breakdown (28 spanning 5+ organisms, 7 spanning 10+, 1 spanning 21) matches the data.
- The 878 function predictions across 29 organisms is verified by `all_predictions_summary.csv` (878 data rows, 29 unique orgIds). The split of 493 family-backed and 385 module-only also matches.
- The 32 annotated families with consensus functional labels is verified (32 rows in `family_annotations.csv` with `consensus_term != 'unannotated'`).
- The cross-organism alignment now uses all 32 organisms (1,148,966 BBH pairs, 13,402 ortholog groups), resolving the prior review's finding that it was limited to 5 pilots.

**Partially supported conclusions**:
- The 93.2% within-module cofitness enrichment claim appears in the README but no `benchmark_results.csv` file exists in the data directory. The NB07 validation code (cells 19-21) would generate this data when executed, but there is no output file to verify the exact number. The claim may be from a prior execution whose output was not persisted.

**Remaining gaps**:
- NB07 (benchmarking) has not been fully executed. No `benchmark_results.csv` file exists. The held-out precision/coverage comparison between Module-ICA, Cofitness, Ortholog, and Domain baselines has not been produced. The README correctly lists this as a remaining step ("Formal benchmarking: precision/recall comparison").
- Predictions use raw TIGRFam IDs (e.g., "TIGR02532", "TIGR03506") and KEGG group IDs (e.g., "K01952") as functional labels. The `genedomain` table's `domainName` and `definition` columns are extracted in NB04 but not propagated to prediction outputs. The README lists TIGRFam ID resolution as a remaining step.

**Limitations acknowledged in README**:
- The benchmarking gap is clearly stated in the "Remaining" section.
- The TIGRFam ID resolution issue is listed.

**Limitations not acknowledged**:
- The 30.1% module cap saturation rate is not discussed. For organisms with many small-genome / high-experiment-count ratios, the fixed cap may be too aggressive.
- The NaN imputation with 0.0 for missing fitness values (NB02 cell 9) is not discussed as a potential bias source.
- No `requirements.txt` or `environment.yml` is provided.

## Suggestions

1. **Correct the module count in the README** from 1,077 to 1,117 (or 1,116 if counting only modules with members). The 32 JSON params files sum to 1,117 `n_stable_modules`, not 1,077.

2. **Execute NB07 (benchmarking)** to produce the held-out precision/coverage comparison. The notebook code is well-structured and ready to run. Consider pre-computing per-organism correlation matrices once (and caching to disk) to make the cofitness baseline tractable, since the current on-the-fly computation in `cofit_predict` is O(n * m) per test gene.

3. **Document the ICA hyperparameter split** between `n_runs=50, min_samples=25` (12 organisms) and `n_runs=30, min_samples=15` (20 organisms). A brief note in the README explaining whether this was pilot-vs-production or tuned per organism would improve transparency.

4. **Add a `requirements.txt`** to the project directory. The notebooks depend on `scikit-learn`, `scipy`, `statsmodels`, `networkx`, `matplotlib`, and `pandas`. The inline `pip install` in NB03 cell 1 is fragile and non-declarative.

5. **Discuss the 30.1% module cap saturation**. Nearly a third of modules hit the `max_members=50` ceiling, meaning their effective membership threshold was raised above 0.3. Consider whether an organism-scaled cap (e.g., 1-2% of total genes) would be more appropriate, or simply acknowledge this as a known trade-off.

6. **Resolve TIGRFam/KEGG IDs to human-readable labels** in the prediction output. The NB04 domain extraction already captures `domainName` and `definition` columns, and the KEGG query captures `kgroup_desc`. Propagating these through NB06 to `all_predictions_summary.csv` would substantially improve interpretability.

7. **Rename `pilot_organisms.csv`** to `selected_organisms.csv` (or similar) now that it contains all 32 organisms. The variable names `pilot_ids` in the notebook code are misleading since the project has moved well past the pilot phase. This is a cosmetic issue but reduces cognitive overhead for new readers.

8. **Persist the within-module cofitness validation output** from NB07 cells 19-21. The 93.2% enrichment claim in the README has no backing data file. Even if the notebook was previously run interactively, saving the validation statistics to a CSV (e.g., `data/predictions/cofitness_validation.csv`) would make the claim verifiable.

9. **Add a `docs/` directory** with the pitfalls, discoveries, and performance documentation. The README references these types of insights (e.g., the D'Agostino vs. absolute threshold methodology change, the SEED schema issues) but they are currently only captured in the README itself and the prior REVIEW.md. Structured documentation would help future contributors.

10. **Consider sensitivity analysis for NaN imputation**. The current approach fills missing fitness values with 0.0 (NB02 cell 9), which assumes phenotypic neutrality for untested conditions. For genes with high missing-data fractions (up to 50% is allowed), this could bias ICA decomposition toward weaker, noisier modules. A brief comparison with row-mean imputation or a stricter missing-data cutoff (e.g., 20%) would strengthen confidence in the decomposition quality.

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-02-13
- **Scope**: README.md, 7 notebooks, 32 ICA params JSON files, 1 source module (`ica_pipeline.py`), 32 fitness matrices, 32 module profile/weight/membership file sets, 32 annotation file sets, 29 prediction files, 2 module family files, 1 prior REVIEW.md
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.

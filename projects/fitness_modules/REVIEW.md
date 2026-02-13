---
reviewer: BERIL Automated Review
date: 2026-02-13
project: fitness_modules
---

# Review: Pan-bacterial Fitness Modules via Independent Component Analysis

## Summary

This is a substantial, well-executed computational biology project that decomposes RB-TnSeq fitness data from 32 bacterial organisms into 1,116 stable ICA modules, aligns them across organisms via ortholog fingerprints into 156 cross-organism families, and generates 6,691 function predictions for hypothetical proteins. The project demonstrates strong scientific methodology: the research question is clearly stated, the 7-notebook pipeline is logically structured from exploration through benchmarking, and the analysis is self-aware about the limitations of module-based approaches vs. sequence-based methods. The honest treatment of the KO-level benchmark results — where module-ICA shows <1% strict precision, correctly attributed to a granularity mismatch rather than method failure — is a notable strength. Validation is compelling: 94.2% of modules show significantly elevated within-module cofitness and 22.7× genomic adjacency enrichment. The main areas for improvement are: the absence of saved outputs in the two Spark-dependent notebooks (NB01–02), predicted functions reported as raw PFam/TIGRFam accession IDs rather than human-readable descriptions (acknowledged as remaining work), and no guidance on confidence thresholds for filtering the 6,691 predictions.

## Methodology

**Research question**: Clearly stated, testable, and well-motivated. The three-part question — decompose fitness data into modules, align across organisms, predict function — maps directly to notebooks 03–06, with NB07 providing formal evaluation.

**Approach**: Sound and methodologically rigorous. The pipeline follows the Borchert et al. (2019) framework with meaningful extensions: Marchenko-Pastur eigenvalue thresholding for component selection, 30–50× FastICA restarts with DBSCAN stability filtering, Fisher exact enrichment with BH FDR correction across four annotation databases (KEGG, SEED, TIGRFam, PFam), ortholog-group fingerprinting via connected components, and hierarchical clustering into module families. The extension from a single organism to a 32-organism pan-bacterial framework with cross-organism alignment is a genuine advance over the original method.

**Data sources**: Clearly identified in the README with a table mapping each `kescience_fitnessbrowser` table to its use. The SQL queries throughout correctly apply documented pitfalls — proper KEGG join paths (through `besthitkegg`), `CAST(... AS FLOAT)` for string-typed columns, and `seedannotation` instead of `seedclass`.

**Reproducibility**:
- *Reproduction guide*: The README includes a thorough `## Reproduction` section with prerequisites, step-by-step `nbconvert` commands, clear Spark/local separation, runtime estimates, and a standalone benchmark command (`python src/run_benchmark.py`).
- *Notebook outputs*: NB03–07 all have saved outputs across all code cells — text tables, progress logs, and embedded figures. **NB01–02 have zero saved outputs** across all 18 code cells. This is documented with a header note ("outputs are not saved in git"), but means a reader cannot see the organism selection rationale, matrix shapes, or QC summaries without JupyterHub access.
- *Figures*: 8 substantive PNG files in `figures/` cover all major analysis stages: PCA eigenvalues, module size distributions, enrichment summary, module families, prediction summary, validation summary, and both benchmark charts (strict and neighborhood). This is comprehensive.
- *Dependencies*: A `requirements.txt` with 7 packages and minimum version constraints is present and adequate.
- *Caching*: All notebooks implement file-existence checks for idempotent re-execution. All 32 organisms have ICA parameter JSON files recording exact hyperparameters.
- *Spark/local separation*: Well handled. NB01–02 extract data to CSV caches, NB03–07 operate entirely on cached files. NB04 and NB05 even separate Spark (Part 1) and local (Part 2) sections within a single notebook.

## Code Quality

**SQL correctness**: All queries are correct and demonstrate awareness of documented pitfalls:
- String-to-numeric casting consistently applied (`CAST(cor12 AS FLOAT)`, `CAST(fit AS FLOAT)`).
- The KEGG join path in NB04 correctly routes through `besthitkegg` with composite keys (`bk.keggOrg = km.keggOrg AND bk.keggId = km.keggId`), matching the `docs/pitfalls.md` warning.
- SEED annotations use `seedannotation.seed_desc`, correctly avoiding the misleading `seedclass` table.
- Experiment quality filtering (`cor12 >= 0.1`) and gene missingness filtering (`≤50% missing`) in NB02 are reasonable QC controls.

**Statistical methods**: Appropriate throughout:
- Fisher exact test with BH FDR correction for module enrichment — contingency table correctly constructed with `alternative='greater'`.
- Mann-Whitney U test for within-module cofitness validation — appropriate non-parametric comparison.
- Marchenko-Pastur eigenvalue thresholding for component selection, with sensible caps (40% of experiments, maximum 80).
- DBSCAN for component clustering with `eps=0.15` and cosine distance — good choice for finding stable components without pre-specifying k.

**ICA pipeline (`src/ica_pipeline.py`)**: Clean, well-documented (295 lines), and technically correct:
- Cosine distance clipping (`np.clip(cos_dist, 0, 1, out=cos_dist)`) correctly addresses the documented floating-point pitfall.
- Component sign alignment within DBSCAN clusters is properly handled via dot-product with a reference vector.
- Zero-variance genes handled (`stds[stds == 0] = 1`).
- The `threshold_membership` function implements the correct adaptive approach: all genes above `min_weight`, capped at `max_members`.

**Benchmark script (`src/run_benchmark.py`)**: Comprehensive (749 lines) with proper structure:
- 20% holdout with `random_state=42` prevents data leakage between train and test.
- Four methods evaluated at two granularity levels (strict KO match and neighborhood set overlap).
- Vectorized Pearson correlation matrix computation for cofitness.
- Cofitness and adjacency validation sections produce verifiable CSV outputs.

**Pitfall awareness**: Outstanding. The project contributed 7 fitness-browser-specific pitfalls to `docs/pitfalls.md` (all tagged `[fitness_modules]`), covering: `fitbyexp_*` long-format discovery, KEGG join path, `seedclass` schema correction, cosine distance clipping, D'Agostino K² thresholding failure, ortholog scope requirements, enrichment `min_annotated` threshold, and ICA component ratio cap.

**Minor issues identified**:
1. In `run_benchmark.py`, `ortholog_predict` takes the first BBH hit with a KEGG annotation (`break` at line 196), meaning prediction quality depends on arbitrary row ordering. The `ratio` column is available but unused for sorting by ortholog quality.
2. Within-module pairwise correlations in the cofitness validation (lines 604–607) use nested Python loops rather than vectorized numpy indexing (`corr[np.ix_(idx, idx)]`). This is tolerable for module sizes ≤50 but stylistically inconsistent with the vectorized approach used elsewhere.
3. NB02's `extract_fitness_matrix_fitbyexp` function attempts to use `fitbyexp_*` tables as pre-pivoted wide format, but the documented pitfall notes these are long format. The function would fail silently, triggering the correct `genefitness` fallback — harmless dead code.

**Notebook organization**: Excellent. Consistent pattern across all notebooks: markdown header → imports/setup → numbered analysis sections → visualization → summary. Progress messages are informative and caching status is always reported.

## Findings Assessment

**Conclusions well-supported by data**:
- **1,116 stable modules** across 32 organisms — verified by NB03 cell 8 output (1,117 stable, 1,116 with members) and 32 JSON parameter files.
- **94.2% cofitness enrichment** — backed by per-organism validation (1,049/1,114 modules enriched, Mann-Whitney p < 0.05), with 17 organisms at 100% and all but 3 above 75%.
- **22.7× genomic adjacency enrichment** — per-organism values from 4.1× (SynE) to 66.8× (Btheta), mean 22.7×.
- **156 cross-organism families** (28 spanning 5+, 7 spanning 10+, 1 spanning 21) — verified in NB05 output and `module_families.csv`.
- **6,691 function predictions** (2,455 family-backed, 4,236 module-only) — verified in NB06 output and `all_predictions_summary.csv`.
- **Benchmark results** (95.8% ortholog precision, 29.1% domain, <1% module-ICA strict) — confirmed in NB07 with standard deviations across 32 organisms.

**Limitations well-acknowledged**: The KO-level precision limitation is explicitly discussed with quantitative evidence (DvH: 1,256 unique KOs for 1,549 annotated genes = ~1.2 genes/KO). The D'Agostino K² thresholding failure is documented with before/after metrics. Module-ICA is characterized as "complementary" to sequence-based methods, not a replacement.

**Incomplete analysis**:
- TIGRFam/PFam ID resolution to human-readable descriptions is listed as remaining work. The top-10 highest-confidence predictions display raw PFam IDs (e.g., "PF00460", "PF00356"), limiting biological interpretability.
- No guidance on confidence thresholds for downstream users. The 6,691 predictions span 0.41–14.77 (median 1.32), but there is no calibration of confidence against known annotations.

**Visualizations**: All 8 figures are well-constructed with proper axes, titles, legends, and color-coding. The validation summary (NB07) showing within-module vs. background cofitness alongside adjacency enrichment per organism is particularly effective.

## Suggestions

1. **[High] Resolve TIGRFam/PFam IDs to human-readable descriptions.** Already acknowledged as remaining work. The `genedomain` extraction in NB04 already captures `domainName` and `definition` columns — a join in NB06 from `domainId` to these columns would transform opaque predictions (e.g., "PF00460") into interpretable ones (e.g., "Disulfide oxidoreductase").

2. **[High] Add outputs or summaries to NB01–02.** These 18 code cells have zero saved outputs. Options: (a) re-run with `nbconvert --execute --inplace` to capture outputs, (b) add markdown cells with key summary tables (organisms surveyed, selection criteria results), or (c) include a static `data/exploration_summary.md`. This would let readers understand the data landscape without JupyterHub access.

3. **[Medium] Add confidence threshold guidance for predictions.** The 6,691 predictions span a 36× range in confidence. A brief analysis of precision vs. confidence threshold on the held-out benchmark set — or even a simple statement like "predictions with confidence > 2.0 represent the top quartile" — would help downstream users filter predictions appropriately.

4. **[Medium] Apply FDR correction to cofitness validation.** The 94.2% enrichment rate uses per-module p < 0.05 across ~1,114 tests without multiple-testing correction. Applying BH correction (already used in NB04) would be methodologically consistent and strengthen the claim. Given the strong effect sizes (mean 3.0× enrichment), the result is almost certainly robust.

5. **[Low] Sort ortholog BBH hits by ratio before selection.** In `run_benchmark.py`, `ortholog_predict` takes the first available hit. Adding `.sort_values('ratio', ascending=False)` to the ortholog lookup would ensure the highest-quality ortholog is used for prediction.

6. **[Low] Rename `pilot_organisms.csv` to `selected_organisms.csv`.** The file contains all 32 organisms, not the "~5 pilots" described in NB01. The variable `pilot_ids` in NB03–06 vs. `org_ids` in NB07 creates a minor naming inconsistency. Unifying to `selected_organisms` would be clearer.

7. **[Low] Vectorize within-module correlation extraction.** Replace the nested loop in `run_benchmark.py` (lines 604–607) with `corr_sub = corr[np.ix_(mod_idx_arr, mod_idx_arr)]; within_corrs = corr_sub[np.triu_indices(len(mod_idx_arr), k=1)]` for consistency with the vectorized style used elsewhere in the script.

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-02-13
- **Scope**: README.md, 7 notebooks (NB01–07), 2 source files (`src/ica_pipeline.py`, `src/run_benchmark.py`), `requirements.txt`, ~498 data files across 6 subdirectories, 8 figures
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.

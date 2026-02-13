---
reviewer: BERIL Automated Review
date: 2026-02-13
project: fitness_modules
---

# Review: Pan-bacterial Fitness Modules via Independent Component Analysis

## Summary

This is an impressive, well-executed computational biology project that decomposes RB-TnSeq fitness compendia from 32 bacterial organisms into 1,116 stable ICA modules, aligns them across organisms via ortholog fingerprints into 156 module families, and generates 6,691 function predictions for hypothetical proteins. The project demonstrates strong software engineering and scientific practices: a clean 7-notebook pipeline with consistent structure, reusable source modules (`ica_pipeline.py`, `run_benchmark.py`), idempotent caching at every stage, four annotation databases, a formal 4-method benchmark with dual-granularity evaluation, and honest reporting of method limitations. The README is exemplary — complete reproduction guide, clear Spark/local separation, data source table, and well-contextualized results. Validation is compelling: 94.2% of modules show significantly elevated within-module cofitness and 22.7× genomic adjacency enrichment. The main areas for improvement are: (1) NB01–02 lack saved cell outputs, making the early pipeline opaque to readers without Spark access; (2) the cofitness validation could be strengthened with multiple-testing correction across 1,114 modules; and (3) predicted functions are often domain-family labels (e.g., "DEAD", "ABC_tran") rather than biological process descriptions, creating a semantic gap with the stated goal of process-level prediction.

## Methodology

**Research question**: Clearly stated, testable, and well-motivated — "Can we decompose RB-TnSeq fitness compendia into latent functional modules via robust ICA, align them across organisms using orthology, and use module context to predict gene function?" The three-part question maps directly to notebooks 03–06, with NB07 providing formal evaluation.

**Approach**: Sound and methodologically rigorous. The pipeline follows Borchert et al. (2019) with meaningful extensions to a pan-bacterial framework:
- Marchenko-Pastur eigenvalue thresholding for component selection (capped at 40% of experiments, max 80)
- 30–50× FastICA restarts with DBSCAN stability filtering (eps=0.15)
- Fisher exact enrichment with BH FDR correction across four annotation databases
- Ortholog-group fingerprinting via connected components on 1.15M BBH pairs
- Hierarchical clustering into module families (cosine distance, average linkage, t=0.7)
- Dual-level benchmarking (strict KO match + neighborhood set overlap) on 20% held-out genes

The key methodological insight — that absolute weight thresholds (|r| ≥ 0.3, max 50 genes) dramatically outperform D'Agostino K² thresholding for ICA membership — is well-documented and represents a valuable contribution.

**Data sources**: Clearly identified in the README with a table mapping 10 `kescience_fitnessbrowser` tables to their use. SQL queries throughout correctly follow the documented join paths and type-casting requirements.

**Reproducibility**:
- *Reproduction guide*: The README includes a thorough `## Reproduction` section with prerequisites, step-by-step `nbconvert` commands, clear Spark/local separation, runtime estimates (30–80 min per organism for ICA, ~1 min from cache), and a standalone benchmark command.
- *Notebook outputs*: **NB03–07 all have saved outputs** (text tables, progress logs, embedded figures). **NB01–02 have zero saved outputs** across all code cells. This is documented with a header note, but means readers cannot see organism selection rationale or matrix shapes without JupyterHub access. The "Execution Summary" markdown cells partially mitigate this.
- *Figures*: 8 substantive PNG files covering all major stages: PCA eigenvalues, module size distributions, enrichment summary, module families, prediction summary, validation summary, and both benchmark charts.
- *Dependencies*: `requirements.txt` with 7 packages and minimum version constraints.
- *Caching*: All notebooks implement file-existence checks. All 32 organisms have ICA parameter JSON files recording exact hyperparameters.

## Code Quality

**SQL correctness**: All queries are correct and demonstrate awareness of documented pitfalls:
- String-to-numeric casting applied consistently (`CAST(cor12 AS FLOAT)`, `CAST(fit AS FLOAT)`, `CAST(begin AS INT)`)
- KEGG join path in NB04 correctly routes through `besthitkegg` with composite keys (`bk.keggOrg = km.keggOrg AND bk.keggId = km.keggId`)
- SEED annotations correctly use `seedannotation.seed_desc`, avoiding the misleading `seedclass` table
- Experiment QC filtering (`cor12 >= 0.1`) and gene missingness filtering (`≤50% missing`) are reasonable

**Pitfall awareness**: Outstanding — the project contributed 7 fitness-browser-specific pitfalls to `docs/pitfalls.md` (all tagged `[fitness_modules]`):
- ✅ Cosine distance floating-point fix (`np.clip`, `ica_pipeline.py` line 146)
- ✅ KEGG join path through `besthitkegg`
- ✅ `seedclass` vs `seedannotation` correction
- ✅ D'Agostino K² thresholding failure documented
- ✅ Ortholog scope must match analysis scope
- ✅ ICA component ratio capped at 40%
- ✅ Enrichment `min_annotated` granularity mismatch

**Statistical methods**: Appropriate throughout:
- Fisher exact test with BH FDR for enrichment — contingency table correctly constructed with `alternative='greater'`
- Mann-Whitney U for cofitness validation — appropriate non-parametric test
- DBSCAN for component clustering — good choice for unknown cluster count
- One concern: cofitness validation tests 1,114 modules at p < 0.05 without multiple-testing correction. At 5% FDR, ~56 modules could be falsely enriched. The 94.2% rate is robust enough that this doesn't change the conclusion, but the omission is methodologically inconsistent with the careful FDR correction applied in NB04.

**`ica_pipeline.py`** (295 lines): Clean, well-documented module with proper docstrings, edge-case handling (zero-norm vectors, empty arrays), and correct sign-alignment via dot-product reference.

**`run_benchmark.py`** (749 lines): Comprehensive standalone script with vectorized correlation, proper train/test separation, and CSV output for all validation results. Good use of `matplotlib.use("Agg")` for headless execution.

**Minor issues**:
1. `ortholog_predict` in `run_benchmark.py` (line 196) takes the first BBH hit with a `break`, ignoring the `ratio` column. Sorting by `ratio` descending first would use the highest-quality ortholog.
2. The `fitbyexp_*` extraction function in NB02 attempts to parse these tables as wide format, but the documented pitfall notes they are long format. The function fails silently and the correct `genefitness` fallback triggers — harmless but dead code.
3. Within-module correlation extraction in `run_benchmark.py` (lines 604–607) uses nested Python loops rather than vectorized numpy indexing, inconsistent with the vectorized style elsewhere.

**Notebook organization**: Consistent pattern across all 7 notebooks: markdown header → imports/setup → numbered sections → visualization → summary. Caching status always reported. Spark/local separation clearly marked.

## Findings Assessment

**Conclusions well-supported by data**:
- **1,116 stable modules** — verified by NB03 cell 8 (1,117 stable, 1,116 with members) and 32 JSON parameter files
- **94.2% cofitness enrichment** — 1,049/1,114 modules, with 17/32 organisms at 100% and all but 3 above 75%
- **22.7× genomic adjacency enrichment** — per-organism range 4.1× (SynE) to 66.8× (Btheta)
- **156 module families** (28 spanning 5+, 7 spanning 10+, 1 spanning 21) — verified in NB05 output
- **6,691 predictions** (2,455 family-backed, 4,236 module-only) — verified with per-organism files
- **Benchmark** (95.8% ortholog, 29.1% domain, <1% module-ICA strict) — confirmed across 32 organisms with standard deviations

**Limitations well-acknowledged**: The KO-level precision limitation is explicitly discussed with quantitative evidence (DvH: 1.2 genes per unique KO). Module-ICA is characterized as "complementary" to sequence-based methods. The D'Agostino K² failure is documented with before/after metrics.

**Areas for improvement**:
1. **Prediction granularity gap**: The README states predictions should be interpreted as "process-level context," but many top predictions are domain-family labels (e.g., "DEAD helicase", "LacI", "Response_reg", "ABC_tran", "Flg_bb_rod") inherited from PFam enrichment. These are closer to molecular function than biological process. The 84% ID-to-description resolution (NB06 cell 6) helps readability but doesn't change the semantic level.

2. **No confidence threshold guidance**: Predictions span confidence 0.41–14.77 (median 1.32) with no calibration against known annotations or recommended filtering threshold.

3. **Low-quality organism modules**: Methanococcus_JJ (52.9% enriched, 9/17 modules) and ANA3 (60.5%, 23/38) show markedly lower validation rates. These organisms' predictions may be less reliable, but no quality flag distinguishes them.

## Suggestions

1. **[High] Add outputs or summaries to NB01–02.** These 18 code cells have zero saved outputs. Options: (a) re-run with `nbconvert --execute --inplace` to capture outputs, (b) add markdown summary tables of key results. This would let readers understand the data landscape without JupyterHub access.

2. **[High] Add confidence threshold guidance.** A brief analysis of prediction precision vs. confidence threshold on the held-out set — or even a simple statement like "predictions with confidence > X represent the top quartile" — would help downstream users filter predictions.

3. **[Medium] Distinguish domain-level from process-level predictions.** Consider post-processing predictions into two tiers: (a) process-level from SEED/KEGG enrichment, and (b) domain-level from PFam/TIGRFam. This would make the output more useful and honest about granularity.

4. **[Medium] Apply FDR correction to cofitness validation.** Apply BH correction (already used in NB04) to the 1,114 Mann-Whitney p-values for methodological consistency. Given the strong effect sizes (mean 3.0× enrichment ratio), the result should be robust.

5. **[Low] Sort ortholog BBH hits by ratio before selection.** In `run_benchmark.py`, add `.sort_values('ratio', ascending=False)` to the ortholog lookup to ensure the highest-quality ortholog is used.

6. **[Low] Flag organisms with weak module quality.** Consider adding a quality flag for organisms below a minimum enrichment threshold (e.g., <70% modules enriched) so downstream users can weight predictions accordingly.

7. **[Low] Rename `pilot_organisms.csv` to `selected_organisms.csv`.** The file contains all 32 selected organisms, not the initial "~5 pilots" described in NB01. The variable naming (`pilot_ids` in NB03–06 vs. `org_ids` in NB07) creates a minor inconsistency.

8. **[Nice-to-have] Include a summary table of largest module families.** The README mentions families spanning 10+ and 21 organisms but doesn't name them. A supplementary table of the top families with consensus annotations would be valuable for biologists.

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-02-13
- **Scope**: README.md, 7 notebooks (NB01–07), 2 source files (`ica_pipeline.py`, `run_benchmark.py`), `requirements.txt`, ~498 data files across 6 subdirectories, 8 figures
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.

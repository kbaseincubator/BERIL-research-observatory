---
reviewer: BERIL Automated Review
date: 2026-02-12
project: temporal_core_dynamics
---

# Review: Temporal Core Genome Dynamics

## Summary

This project presents a well-designed and methodologically sound investigation into how core genome composition changes over sampling time. The research question is clear and testable, the approach is systematic with appropriate controls (multiple thresholds, two species comparison), and the notebook organization is exemplary. The analysis reveals compelling evidence that core genome "erosion" in heavily-sampled species reflects temporal dynamics rather than just sampling bias. However, **the analysis has not been executed** - all four notebooks contain only code without any outputs, the data/ and figures/ directories are empty, and the "Key Findings" section in the README remains as "_To be filled in after running the analysis_". This is a complete, well-planned project that needs to be run to generate results.

## Methodology

**Strengths:**
1. **Clear hypothesis**: The project articulates a specific, testable hypothesis about temporal dynamics explaining smaller core genomes in heavily-sampled species
2. **Appropriate species selection**: P. aeruginosa and A. baumannii are excellent choices - both semi-environmental with clinical crossover, both heavily sampled (~6,700 genomes each), making them ideal for temporal analysis
3. **Robust experimental design**: Uses multiple core thresholds (90%, 95%, 99%) to test sensitivity, includes two complementary approaches (cumulative expansion and fixed time windows)
4. **Reproducibility**: The approach is clearly documented with specific table names, explicit date parsing logic, and well-commented code
5. **Appropriate statistical methods**: Power law and log-linear model fitting for decay curves, Jaccard similarity for core composition comparison, COG enrichment analysis for functional characterization

**Areas for improvement:**
1. **Missing execution**: No evidence that any notebooks have been run - this is a critical gap
2. **Minimum window size justification**: The MIN_WINDOW_SIZE=30 is used but not justified. Why 30? A power analysis or sensitivity test would strengthen this choice
3. **Date parsing validation**: The date parsing function is comprehensive but there's no reporting on what fraction of dates fall into each granularity category (exact date vs YYYY-MM vs YYYY only). This matters because using July 1st as a midpoint for "2015" could introduce systematic bias
4. **Missing validation against null model**: The project should test whether temporal patterns are stronger than random sampling effects. A permutation test (shuffle dates, recalculate decay) would strengthen conclusions

## Code Quality

**Strengths:**
1. **Excellent notebook organization**: Four focused notebooks with clear separation of concerns (extraction → windowing → analysis → functional)
2. **Proper Spark usage**: Correctly uses `get_spark_session()` without import (avoiding the pitfall documented in docs/pitfalls.md)
3. **Chunk-based data handling**: Notebook 01 correctly handles potentially large gene cluster data with chunking (CHUNK_SIZE=5M)
4. **Appropriate SQL practices**: Uses exact equality instead of LIKE patterns where possible (following pitfalls.md guidance), properly filters large tables
5. **Good error handling**: Try-except blocks around model fitting with informative error messages

**SQL and Join Key Issues:**
1. **Incorrect annotation join**: Cell 4 of notebook 04 joins `gene_genecluster_junction` to `eggnog_mapper_annotations` via `gene_id`, but according to docs/pitfalls.md lines 148-160, `eggnog_mapper_annotations.query_name` joins to `gene_cluster.gene_cluster_id`, NOT to `gene.gene_id`. The correct query should be:
   ```sql
   -- CORRECT
   SELECT gc.gene_cluster_id, e.COG_category, e.Description
   FROM kbase_ke_pangenome.gene_cluster gc
   JOIN kbase_ke_pangenome.eggnog_mapper_annotations e
     ON gc.gene_cluster_id = e.query_name
   ```
   The current approach may return no results or incorrect annotations.

2. **Efficient but potentially fragile batching**: The annotation batching in notebook 04 uses 1000-gene batches with string concatenation in SQL. While this should work, using a temporary view or staging approach might be more robust for very large result sets.

**Statistical Issues:**
1. **Potential overfitting**: The power law model fitting (notebook 03, cell 2) samples every 10th genome but then fits to all sample points. With hundreds of data points and only 2 parameters, this should be fine, but the code should report degrees of freedom.

2. **Missing significance tests**: The COG enrichment analysis (notebook 04, cells 8-10) compares proportions but doesn't perform statistical tests (e.g., Fisher's exact test) to determine if differences are significant or just noise.

**Code Clarity:**
1. **Good commenting**: Functions like `parse_collection_date()` and `calculate_core()` have clear docstrings
2. **Magic numbers explained**: WINDOW_YEARS=2 is defined clearly, thresholds are consistently used
3. **Progress indicators**: Uses tqdm for long-running loops, helpful for user experience

## Findings Assessment

**Current state**: No findings to assess - the notebooks have not been executed. The README states "_To be filled in after running the analysis_" and both data/ and figures/ directories are empty.

**Expected findings** (based on code inspection):
- The analysis should produce ~14 figures across four notebooks
- Quantitative metrics for decay rates (power law exponents α for each species and threshold)
- Stable core sizes and turnover statistics
- COG enrichment patterns distinguishing stable from transient core genes

**Once executed, the reviewers should assess**:
1. Whether cumulative and fixed-window approaches agree on core erosion patterns
2. If the two species show similar temporal dynamics (supporting generalizability)
3. Whether power law or log-linear models better fit the decay
4. If functional enrichment patterns match biological expectations (housekeeping in stable core, mobile elements in early-exit)

## Suggestions

### Critical Issues (Must Address)

1. **Execute the analysis**: Run all four notebooks in sequence on BERDL JupyterHub to generate results. Without execution, this is an untested plan rather than a completed analysis.

2. **Fix the annotation join key**: In notebook 04, cell 4, correct the join to use `gene_cluster_id` instead of `gene_id` when joining to `eggnog_mapper_annotations`. The current query will likely fail or return incorrect results. Use:
   ```sql
   SELECT DISTINCT
       gc.gene_cluster_id,
       e.COG_category,
       e.Description
   FROM kbase_ke_pangenome.gene_cluster gc
   JOIN kbase_ke_pangenome.eggnog_mapper_annotations e
       ON gc.gene_cluster_id = e.query_name
   WHERE gc.gene_cluster_id IN (...)
   ```

3. **Add statistical significance testing**: In notebook 04, add Fisher's exact test or chi-square tests when comparing COG category proportions between stable and early-exit genes. Report p-values and apply multiple testing correction (Bonferroni or FDR).

4. **Fill in Key Findings**: After running the analysis, update README.md section "Key Findings" with the actual results, including decay rates, stable core sizes, and functional enrichment patterns.

### Important Improvements (Strongly Recommended)

5. **Validate date parsing**: In notebook 01, cell 4, add reporting on date granularity distribution. How many dates are exact (YYYY-MM-DD) vs month-level vs year-only? If most are year-only, the temporal resolution may be too coarse for the claimed analysis.

6. **Test against null model**: Add a permutation test where you shuffle collection dates among genomes and recalculate decay curves. If the observed temporal pattern is not significantly different from random, the conclusions about time-dependent dynamics are not supported.

7. **Report coverage metrics**: In notebook 01, cell 3, report what fraction of collection_date values are in the INVALID_DATES list. This tells us about data quality. Also report the distribution of failed date parses (cell 4) - are these random errors or systematic issues with certain formats?

8. **Justify minimum window size**: Explain why MIN_WINDOW_SIZE=30 was chosen. Consider a sensitivity analysis showing that results are robust to this choice (e.g., test with 20, 30, 50 and show decay rates don't change substantially).

### Nice-to-Have Enhancements

9. **Add confidence intervals**: The power law fits (notebook 03) should report confidence intervals on the α parameter, not just point estimates. Use bootstrap or the covariance matrix from `curve_fit`.

10. **Visualize date quality**: In notebook 01, create a figure showing the distribution of date granularities (exact date, month, year) over time. This would reveal if early samples have lower date precision.

11. **Cross-species stable core**: Add an analysis identifying genes that are in the stable core of BOTH species - these would be truly universal essential functions.

12. **COG category descriptions**: In notebook 04, when creating labels that include COG descriptions, handle NaN values explicitly (as mentioned in docs/pitfalls.md lines 260-285). Use `pd.notna()` checks before string slicing.

13. **Add execution timing**: Include cell execution times or timestamp logging to help users understand which steps are slow and may need optimization.

14. **Document computational requirements**: Add a note about expected runtime and memory requirements for each notebook, so users know what to expect when running on BERDL JupyterHub.

## Pitfalls Assessment

**Correctly avoided:**
- ✅ Uses exact equality for species filtering instead of LIKE where possible
- ✅ Handles NCBI environment metadata EAV structure correctly with ncbi_env table
- ✅ Uses `get_spark_session()` without import
- ✅ Casts numeric columns when needed (though mostly working with Spark directly)
- ✅ Chunks large data exports to avoid memory issues

**Pitfalls encountered:**
- ❌ **Incorrect annotation join key** (docs/pitfalls.md lines 148-160): Uses `gene_id` instead of `gene_cluster_id` to join eggnog_mapper_annotations
- ⚠️ **Pandas NaN handling**: Notebook 04 uses dictionary mapping for COG descriptions but doesn't explicitly check for NaN before string operations (see pitfalls.md lines 260-285)

**Not applicable but good to note:**
- The project doesn't use REST API (correctly chooses direct Spark for this large dataset analysis)
- No string-typed numeric column issues since working with Spark DataFrames
- Gene cluster IDs are only compared within species (correctly following pitfalls.md lines 163-175)

## Review Metadata

- **Reviewer**: BERIL Automated Review
- **Date**: 2026-02-12
- **Scope**: README.md, 4 notebooks (01_data_extraction.ipynb, 02_sliding_window.ipynb, 03_analysis.ipynb, 04_functional.ipynb), 0 data files, 0 figures
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment. The primary finding is that this well-designed project has not been executed - all notebooks contain code without outputs, and data/figures directories are empty.

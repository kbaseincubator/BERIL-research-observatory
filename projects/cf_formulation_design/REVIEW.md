---
reviewer: BERIL Automated Review
date: 2026-03-21
project: cf_formulation_design
---

# Review: CF Protective Microbiome Formulation Design

## Summary

This is an exceptionally thorough translational bioinformatics project that integrates six experimental data modalities — planktonic inhibition assays (220 isolates), carbon source utilization (430 isolates × 21 substrates), growth kinetics (32 isolates), patient metagenomics (175 samples), pairwise interaction assays, and pangenome analysis (499+ genomes across 6 species) — to rationally design commensal formulations for competitive exclusion of *P. aeruginosa* in CF airways. Across 13 executed notebooks, 39 figures, and 22 output data files, the project progresses from exploratory data analysis through mechanistic hypothesis testing to a concrete, ranked set of FDA-safe formulations validated by exhaustive combinatorial enumeration, bootstrap confidence intervals, and pangenome conservation analysis. The REPORT.md reads as a near-publication-quality manuscript with a clear narrative arc, honest treatment of limitations (including the R² = 0.274 training vs 0.145 CV gap), and a well-prioritized experimental roadmap. The project's main strengths are: (1) the transparent, quantitative assessment of what metabolic competition can and cannot explain, (2) the staged safety filtering that shows the cost of clinical viability, (3) the pangenome robustness validation across 1,796 lung PA genomes, and (4) the mature *M. luteus* engraftment discussion with a concrete k=2 vs k=3 recommendation. Areas for improvement are minor: a missing data dictionary entry for the most recently added data file, the use of f-string SQL interpolation in Spark notebooks, and an opportunity to strengthen the cohort representativeness discussion.

## Methodology

**Research question and hypotheses**: The central question — "Can we design optimal 1–5 organism commensal formulations for competitive exclusion in CF lungs?" — is clearly stated, testable, and decomposed into six sub-hypotheses (H0–H6) that build logically from individual mechanism validation to community-level design to pangenome robustness. Each hypothesis is paired with a specific notebook and explicit expected outputs. The null hypothesis (H0: inhibition is driven entirely by direct antagonism) is properly framed and the partial rejection is quantitatively supported.

**Approach soundness**: The multi-criterion optimization framework (niche coverage, complementarity, inhibition, engraftability, safety) captures the essential dimensions of a translatable formulation. Several design choices demonstrate methodological maturity: (a) the permissive-then-strict safety filtering (NB05 → NB05b) transparently shows what is lost at each stage; (b) exhaustive enumeration of all 147,440 k=3 triples confirms the greedy optimum is globally optimal; (c) bootstrap confidence intervals (1,000 resamples) reveal k=2–5 are statistically indistinguishable, supporting the minimalist k=2 recommendation; (d) the *N. mucosa* clade sensitivity check in NB07 tests whether results depend on clade assignment.

**Data sources**: Clearly documented across README.md, RESEARCH_PLAN.md, and REPORT.md §5 with table-level row counts and roles. BERDL databases (pangenome, GapMind, BacDive, PhageFoundry) are used appropriately for validation and extension, not as primary evidence. The bridge from experimental isolates to pangenome genomes via reference genome accessions is carefully managed.

**Reproducibility**:
- **Notebook outputs**: All 13 notebooks have been executed with saved outputs — 100% of code cells (148 total) contain outputs. This fully meets the hard requirement.
- **Figures**: 39 figures in `figures/` cover every analysis stage comprehensively, from EDA (10 from NB01) through formulation optimization (NB05/05b), pangenome conservation (NB07), PA adaptation (NB10), to virulence system distribution (NB13). Each figure uses a numbered prefix tracing it to its source notebook.
- **Dependencies**: `requirements.txt` lists 10 packages with minimum versions. PySpark and `berdl_notebook_utils` are noted as BERDL-provided prerequisites.
- **Reproduction guide**: README includes prerequisites, a notebook dependency DAG with parallel branches clearly marked, identification of Spark-dependent notebooks (NB07, NB09, NB10, NB13), and runtime estimates (< 2 min local, 5–10 min Spark).
- **Spark/local separation**: Clean. Nine notebooks run locally from cached parquet/TSV outputs. Four require BERDL Spark for pangenome/GapMind queries. Downstream notebooks can run locally from cached data.
- **Data dictionary**: `data/DATA_DICTIONARY.md` provides per-file documentation with source notebook, row counts, and column-level metadata — a significant reproducibility aid.

## Code Quality

**Notebook organization**: All 13 notebooks follow a consistent pattern: imports/setup → data loading → analysis → visualization → output saving → summary. Markdown cells provide section headers, goal statements, and inline interpretation. Variable names are descriptive. The code uses pandas, scipy, sklearn, and statsmodels idiomatically.

**Statistical methods**: Appropriate and carefully applied:
- NB03: OLS regression with honest 5-fold cross-validation. The training R² (0.274) vs CV R² (0.145 ± 0.142) gap is transparently reported with the conclusion that out-of-sample predictive power is ~15%. Kruskal-Wallis is appropriate for the non-normal inhibition distributions.
- NB05b: Exhaustive combinatorial enumeration with species-uniqueness constraint. Bootstrap CIs (1,000 resamples) on composite scores.
- NB10: Mann-Whitney U tests with Benjamini-Hochberg FDR correction for pathway differential analysis. PCA with KMeans clustering (k=2, silhouette = 0.95) for PA subpopulation identification.
- NB13: Gene presence/absence frequency analysis across environmental categories with appropriate FDR correction.
- Effect sizes are consistently reported alongside p-values — a commendable practice.

**SQL queries**: NB07, NB09, NB10, and NB13 use Spark SQL for pangenome queries. Queries use proper `GROUP BY` (avoiding the `DISTINCT` + aggregate pitfall from docs/pitfalls.md), appropriate `CAST(... AS DOUBLE)` for Spark DECIMAL columns, and filtering by `gtdb_species_clade_id` with exact equality rather than LIKE patterns. The GapMind `clade_name` format and `ncbi_env` EAV format pitfalls are handled correctly.

**Pitfall awareness**: The project addresses multiple documented pitfalls from docs/pitfalls.md: GapMind genome ID prefix stripping, Spark DECIMAL column casting, `ncbi_env` EAV format pivot, and `clade_name` = `gtdb_species_clade_id` format. The discovery that `fact_pairwise_interaction` is identical to `fact_carbon_utilization` (correlation = 1.0, NB08) is properly documented as a limitation.

**Issues identified**:
- Spark SQL queries in NB07, NB09, NB10, and NB13 use Python f-string interpolation for `WHERE` clause values (e.g., `f"WHERE clade_name LIKE '{prefix}%'"`). While these are research notebooks querying read-only databases with researcher-controlled inputs (not user-facing), parameterized queries or Spark DataFrame API filtering would be more robust. This is a low-severity concern in this context.
- Several Spark notebooks call `.toPandas()` on query results without explicit `LIMIT` safeguards. The queries are filtered by species clade (returning hundreds to low thousands of rows), so this works in practice, but a defensive `LIMIT` or row-count check before collection would prevent unexpected memory issues if clade sizes change.
- Hardcoded absolute paths (e.g., `/home/aparkin/...`) appear in some notebooks for loading PROTECT Gold parquet files. These are appropriate for the on-cluster research context but would need adjustment for other users.

## Findings Assessment

**Conclusions well-supported by data**:
- The metabolic overlap–inhibition correlation (r = 0.384, p = 2.3×10⁻⁶) is statistically robust. The conservative CV R² reporting (0.145) prevents overclaiming. The identification of dual-mechanism species (metabolic + direct antagonism) through residual analysis is a genuine insight, not an artifact.
- The five-species formulation achieving 100% PA niche coverage at k=3 is directly verifiable from the carbon utilization data. The explanation of the coverage jump (18% at k=2 to 100% at k=3) via *M. luteus*'s uniquely broad carbon utilization profile is clearly articulated in §2.6.
- PA amino acid pathway conservation (97.4% across 1,796 lung genomes) and the finding that CF vs non-CF lung PA show zero amino acid pathway differences are compelling for translational generalizability.
- The sugar alcohol prebiotic discovery (6 pathways complete in commensals, absent in PA) is well-supported by both GapMind predictions and patient metatranscriptomics, and the xylitol connection to existing CF clinical evidence is a strong translational bridge.
- The PA14 virulence representativeness analysis (NB13) is an important addition: the finding that CF PA is 94% ExoS+ while PA14 is ExoU+ correctly motivates Proposed Experiment 4.6.

**Limitations honestly acknowledged**: Section 3.7 is thorough, covering: planktonic assay limitations, 22-substrate constraint, 142-isolate core cohort, sparse pairwise data (8 comparisons across 5 pairs), PA14 reference strain bias, inferred engraftability, sparse lung metadata, the `fact_pairwise_interaction` data quality issue, and the *N. mucosa* clade selection. The CUB/GC confound (NB12) is presented as a negative result rather than hidden. The PA14 representativeness limitation is appropriately elevated to its own report section (§2.14) given its significance.

**REPORT narrative quality**: The REPORT is written at a high standard. Each Results subsection opens with a "Rationale" explaining *why* the analysis was done, creating a logical flow. The Discussion synthesizes findings into a multi-mechanism model (§3.1), directly confronts the *M. luteus* engraftment tension (§3.2), and places results in literature context with 20+ relevant citations including recent work (2025–2026). The Proposed Experiments (§4) are ordered by priority with clear rationale — this reads as a genuine experimental roadmap.

**Internal consistency**: The README claims "13 notebooks executed, 39 figures generated, 22 data files produced" — all three counts match the actual file system contents exactly. Notebook numbering has a gap (no NB11) which is explained by the consolidation of NB10 + NB11. The REPORT §5 data table row counts match actual file sizes for all files checked.

**One gap**: The `pa_virulence_systems.tsv` data file (6,760 rows, from NB13) is referenced in REPORT §5 but does not have an entry in `data/DATA_DICTIONARY.md`. This appears to be an oversight from the recent addition of NB13.

## Suggestions

### Important (documentation completeness)

1. **Add `pa_virulence_systems.tsv` to DATA_DICTIONARY.md**: This file (6,760 rows from NB13) is listed in REPORT §5 but has no entry in the data dictionary. It should include column descriptions for `genome_id`, virulence gene presence columns (`exoS`, `exoU`, `pelA`, `pslA`, `ladS`, etc.), `t3ss_type`, `biofilm_type`, and `category`/environment fields.

2. **Note selection bias in the 142-isolate core cohort**: The overlap between inhibition and carbon utilization data yields 142 of 4,949 isolates. While §3.7 mentions this sample size limitation, a brief quantitative statement about whether this subset is taxonomically representative of the broader collection (e.g., comparing genus frequency distributions) would strengthen the methodology. NB01's data overlap figure addresses this visually, but a sentence or two in the Limitations would help readers who do not re-run the notebook.

### Minor (code robustness)

3. **Consider parameterized Spark queries**: The f-string SQL interpolation in NB07, NB09, NB10, and NB13 works correctly with researcher-controlled inputs but is fragile. Using Spark DataFrame API filtering (e.g., `.filter(col("clade_name").like(...))`) or temp view joins would be more robust and easier to maintain. This is low priority given the research context.

4. **Add defensive row-count checks before `.toPandas()`**: In Spark-dependent notebooks, adding a `.count()` check or explicit `LIMIT` before collecting large query results to pandas would guard against unexpected memory issues if pangenome sizes grow. Example: `assert result_spark.count() < 100000, "Unexpectedly large result"`.

### Nice-to-Have

5. **Consider a graphical abstract**: A single pipeline overview figure — from data integration through formulation design to pangenome validation — as the first figure in the REPORT would help readers quickly grasp the project's scope before diving into the 13-notebook, 39-figure detail.

6. **Add NB13 to the README notebook DAG**: NB13 appears in the DAG (correctly, as a Spark-dependent leaf off NB01), but it is not listed in the "Steps" section's runtime estimates. Adding "NB13 requires BERDL Spark access (5–10 min)" to step 3 would complete the reproduction guide.

7. **Clarify the absence of NB11 in the notebook numbering**: The gap (NB10, NB12, NB13 — no NB11) is explained in RESEARCH_PLAN.md §v6, but a reader browsing only the `notebooks/` directory might be confused. A brief comment in the README (e.g., "NB11 was consolidated into NB10") would preempt this.

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-03-21
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, requirements.txt, DATA_DICTIONARY.md, 13 notebooks, 22 data files, 39 figures, docs/pitfalls.md
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.

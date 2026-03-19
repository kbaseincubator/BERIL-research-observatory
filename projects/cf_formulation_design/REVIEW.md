---
reviewer: BERIL Automated Review
date: 2026-03-19
project: cf_formulation_design
---

# Review: CF Protective Microbiome Formulation Design

## Summary

This is an exceptionally well-executed project that integrates 23 experimental tables (30.5M rows) from the PROTECT CF study with BERDL pangenome resources to design rationally optimized probiotic formulations for competitive exclusion of *P. aeruginosa* in CF airways. The project follows a clear logical arc from data integration through hypothesis testing to actionable formulation design, supported by 10 notebooks with saved outputs, 29 figures, 16 data files, and a thorough REPORT.md. The research question is well-motivated, the methodology is sound, and the findings — particularly the identification of dual-mechanism species and sugar alcohol prebiotics — are scientifically compelling. The main areas for improvement are: (1) the cross-validation results in NB03 reveal meaningful overfitting (CV R² = 0.145 vs training R² = 0.274) that should be discussed more prominently in the report, (2) the *N. mucosa* clade selection inconsistency between NB07 and the reference genome mapping deserves more attention, and (3) the pairwise interaction data is extremely sparse (only 8 pair comparisons) relative to the claims made about formulation additivity.

## Methodology

### Research Question & Hypotheses
The research question is clearly stated, testable, and well-scoped. The six hypotheses (H0–H6) are well-formulated with specific, falsifiable predictions and clear criteria for support. The staged design — from individual mechanisms (H1: metabolic competition) through community optimization (H2) to genomic validation (H5/H6) — is logically compelling. The null hypothesis (H0: inhibition is driven by direct antagonism, not metabolism) is appropriately framed and honestly evaluated.

### Approach
The multi-criterion optimization framework is appropriate for the problem. The decision to separate permissive (NB05) and strict (NB05b) safety filters is a smart design choice that reveals the clinical viability tradeoff transparently. The sensitivity analysis in NB05b (cell-13), which shows the same 5-species core emerging across all weight sets, is particularly effective. The staged approach — EDA → mechanism identification → optimization → genomic validation → interaction testing → extension — follows best scientific practice.

### Data Sources
Data sources are thoroughly documented in RESEARCH_PLAN.md with row counts, column descriptions, and roles in the analysis. The project clearly identifies which data comes from local experimental files (`~/protect/gold/`) and which from BERDL. Known pitfalls from `docs/pitfalls.md` are addressed: GapMind genome ID prefix stripping (NB07 cell-4), the `gapmind_pathways` multi-row-per-genome-pathway issue (correct `MAX(score_val)` pattern used throughout NB07 and NB09), and Spark `DECIMAL` casting (explicit `CAST(... AS DOUBLE)` in NB07/NB09).

### Reproducibility
- **Notebook outputs**: All 10 notebooks are committed with saved outputs (text, tables, and figures). This is exemplary and meets the hard requirement. Figures are rendered inline alongside numeric summaries.
- **Figures**: 29 figures in the `figures/` directory covering every analysis stage — well above the minimum. Each major notebook contributes 2–4 figures.
- **Dependencies**: `requirements.txt` is present with pinned minimum versions. However, it is missing `pyspark` (required for NB07, NB09) and the `berdl_notebook_utils` package (imported in NB07/NB09 for `get_spark_session`). These are available on the BERDL JupyterHub but should be noted as cluster-only prerequisites.
- **Reproduction guide**: The README includes a clear `## Reproduction` section with prerequisites, ordered steps, and which notebooks require Spark vs run locally. Runtime estimates are provided for local notebooks (< 2 min each) and Spark notebooks (5–10 min each).
- **Spark/local separation**: Well-handled. NB01–NB06 and NB08 run locally from cached parquet files. NB07 and NB09 require Spark and are clearly documented as such. Intermediate data files (TSV) enable downstream notebooks to run without re-executing Spark queries.

## Code Quality

### SQL Correctness
The GapMind queries in NB07 and NB09 correctly implement the multi-row aggregation pattern (`MAX(score_val)` per genome-pathway pair via CTE), properly cast `AVG(CASE WHEN ...)` to `DOUBLE` (avoiding the Spark DECIMAL pitfall from `docs/pitfalls.md`), and use exact equality filters on `clade_name` for performance. The species clade lookup (NB07 cell-4) tries both `RS_` and `GB_` prefixed accessions with a fallback to name-based search — good defensive coding that addresses the documented GapMind ID prefix mismatch.

### Statistical Methods
- **NB03 regression**: The OLS model progression (overlap-only R²=0.141 → all metabolic R²=0.274 → metabolic+genus R²=0.360) is appropriate. However, the 5-fold cross-validation (cell-14) reveals substantial overfitting: **CV R² = 0.145 ± 0.142** vs training R² = 0.274, with one fold producing negative R² (−0.049). The gap of 0.129 is acknowledged as "some overfitting" in the notebook but the REPORT (Section 2.3) cites R² = 0.274 without the CV caveat. This is the most significant methodological concern — the true out-of-sample predictive power of metabolic features may be closer to 15%.
- **Engraftability score** (NB04): The formula `prevalence × log1p(activity_ratio)` is reasonable but ad hoc. The choice of `log1p` vs `log` vs linear scaling affects species rankings but is not justified or sensitivity-tested.
- **Formulation scoring** (NB05/05b): The multi-criterion composite score uses fixed weights. The sensitivity analysis in NB05b (cell-13) is excellent — the same 5 species emerge across all 5 tested weight configurations — providing strong evidence the solution is robust to scoring assumptions.
- **Synergy classification** (NB08): Using ±10% thresholds for synergistic/additive/antagonistic classification on only 8 data points is underpowered. The mean synergy score of −5.8% should be interpreted cautiously given n=8.

### Notebook Organization
All notebooks follow a consistent and logical structure: markdown header with goal/inputs/outputs → imports/setup → data loading → analysis → visualization → summary → file save. Section numbering is consistent. Each notebook summary prints key statistics for quick reference.

### Pitfall Awareness
The project correctly addresses several `docs/pitfalls.md` entries:
- GapMind genome ID prefix mismatch (`RS_`/`GB_` — NB07 cell-4)
- GapMind multi-row-per-pathway aggregation (correct `MAX` pattern used in all GapMind queries)
- Spark `DECIMAL` → `DOUBLE` casting (explicit `CAST(... AS DOUBLE)` in NB07/NB09)
- GapMind `score_category` values (`complete`/`likely_complete`/etc., not a simple `present` flag)
- GapMind `metabolic_category` values (`'aa'`/`'carbon'` — used correctly)
- `fact_pairwise_interaction` identity with `fact_carbon_utilization` — discovered and documented in NB08

### Code Issues

1. **NB01 cell-27**: The metabolic overlap computation has a dangling `for/continue` loop that iterates over `carbon_sources` but only checks for `no_carbon` — the actual overlap computation is in a separate loop below. The dead code is harmless but confusing.

2. **NB03 cell-11**: The `model_data_full` merge is immediately overridden by `.loc` indexing to attach `asma_id` and `species`. The merge is dead code and should be removed for clarity.

3. **NB05 scoring weights vs NB05b**: NB05 uses weights (30% coverage, 15% complementarity, 35% inhibition, 20% engraftability); NB05b uses (25%, 10%, 35%, 30%). The weight change is motivated (more engraftability for clinical viability) but the lack of a bridging comment makes it easy to miss.

4. **NB08 cell-3/5**: The `id_species.get()` call for ASMA-2260 returns a full Series rather than a scalar because the isolates table has duplicate rows for that ID. This produces garbled output in the interaction summary table where the species column shows the raw Series repr. Fix with `.iloc[0]` or `.drop_duplicates()`.

5. **NaN species isolates**: APA20015, ASMA-1309, ASMA-2475, and ASMA-765 propagate through the pipeline with NaN species. APA20015 appears in the top 5 single-isolate strict-safe candidates at k=1 with 59% inhibition, labeled "Unknown." These should be resolved or explicitly excluded.

## Findings Assessment

### Conclusions
- **H1 (metabolic competition)**: Supported. The r = 0.384 correlation is statistically significant (p = 2.3×10⁻⁶). The honest reporting that metabolism explains only 27% of variance is a strength, though the CV results suggest the true figure is closer to 15%.
- **H2 (complementary coverage)**: Supported. The k=3 formulation achieves 100% niche coverage. The sensitivity analysis confirms the 5-species core is robust across weight variations. Note: complementarity scores are uniformly low (0.04–0.13), meaning coverage comes from members hitting different *subsets* of PA14's substrates, not from overall metabolic dissimilarity.
- **H3 (engraftability)**: Partially supported. *N. mucosa*'s top engraftability (1.595) is data-driven. The caveat that engraftability is inferred from prevalence, not directly measured, is appropriately noted.
- **H4 (prebiotic)**: Amino acid prebiotics rejected (NB06); sugar alcohol candidates identified genomically (NB09). The pivot from a negative result to a novel prebiotic strategy is the project's most creative contribution.
- **H5 (conservation)**: Strongly supported for 4/5 species. *G. sanguinis* (7 genomes, 39% AA pathway conservation) is correctly flagged as the weakest link.
- **H6 (lung adaptation)**: Weakly supported. 21 lung genomes across 5 species with modest metabolic differences. The *R. dentocariosa* (38%) and *N. mucosa* (33%) lung enrichment is interesting but statistically underpowered.

### Limitations
The REPORT §3.5 is thorough and honest, covering: planktonic-only assays, 22 tested substrates, 142-isolate core cohort, sparse pairwise data (only 8 pair comparisons), inferred engraftability, sparse lung metadata (21 genomes), the `fact_pairwise_interaction` data identity issue, and the *N. mucosa* clade selection question. This is an exemplary limitations section.

### Incomplete Analysis
- BacDive cross-validation and ModelSEED biochemistry analysis mentioned in RESEARCH_PLAN.md (NB08 goals) were not performed — NB08 pivoted to pairwise interaction analysis instead. This is acceptable given the "if time permits" qualifier but should be noted as future work.
- The REPORT mentions "eight stages" but the pipeline has 10 notebooks (including NB05b and NB09). Minor numbering discrepancy.

### Visualizations
29 figures are well-labeled and informative. The heatmaps (carbon utilization clustermap, pathway conservation, rate advantage, pathway selectivity) are particularly effective. The prebiotic selectivity plot (NB06) clearly communicates the negative result. One gap: there is no visualization of the final recommended formulation's niche coverage — a figure showing which of the 5 species covers which PA14 substrates would strengthen the community-level competitive exclusion narrative.

## Suggestions

### Critical

1. **Discuss cross-validation results in REPORT.md**: The 5-fold CV R² (0.145 ± 0.142) is substantially lower than the training R² (0.274) reported as the headline number in Section 2.3. Add a sentence acknowledging the CV results and noting that the true predictive power of metabolic features may be closer to 15% than 27%. This does not invalidate the qualitative conclusion (metabolic overlap is a real predictor) but affects quantitative interpretation.

2. **Acknowledge *N. mucosa* clade mismatch more prominently**: NB07 uses `s__Neisseria_mucosa_A` (15 genomes) for all pangenome analyses, but the PROTECT isolate reference genome (`GCA_003028315.1`) maps to the 8-genome `s__Neisseria_mucosa` clade via `GB_GCA_003028315.1`. This is noted in REPORT §3.5 but could affect conservation and lung adaptation findings for this key anchor species. Consider running the GapMind query for the 8-genome clade as a sensitivity check.

3. **Add `pyspark` and cluster-only dependencies to `requirements.txt` or Reproduction section**: Users attempting to run NB07/NB09 need `pyspark` and `berdl_notebook_utils`, neither of which is listed. A note that these are pre-installed on BERDL JupyterHub would suffice.

### Important

4. **Resolve or exclude NaN-species isolates**: APA20015 ranks in the top 5 strict-safe candidates with 59% inhibition, labeled "Unknown." Either resolve its taxonomy against the isolate catalog or exclude it with a documented reason. Three other NaN-species isolates (ASMA-1309, ASMA-2475, ASMA-765) also propagate through the pipeline.

5. **Add a formulation niche coverage visualization**: A figure showing which of the 5 core species covers which PA14-preferred substrates would clearly communicate the community-level competitive exclusion mechanism. Currently, niche coverage is reported only as a percentage.

6. **Fix NB08 ASMA-2260 species lookup** (cell-3/5): The duplicate isolate entries for ASMA-2260 cause garbled Series output in the interaction summary. Use `.iloc[0]` or `.drop_duplicates()` on the species lookup.

7. **Caveat the pairwise interaction conclusions**: The claim that pairs are "near-additive" is based on only 8 comparisons across 5 unique pairs. Add a sample-size caveat to REPORT §2.10 and note that the complete 10-pair matrix (Section 4.2) is a critical gap, not just a nice-to-have follow-up.

### Nice-to-Have

8. **Justify the engraftability score formula**: The `prevalence × log1p(activity_ratio)` formula is reasonable but ad hoc. A brief justification (e.g., diminishing returns of very high activity ratios) or a check that top species are consistent with alternative formulations would strengthen NB04.

9. **Document BacDive/ModelSEED omissions**: Add a note in RESEARCH_PLAN.md or REPORT.md explaining that BacDive cross-validation and ModelSEED biochemistry were deferred due to the pivot toward pairwise interaction analysis.

10. **Clean up dead code**: Remove the dangling `for/continue` block in NB01 cell-27 and the dead `model_data_full` merge in NB03 cell-11. Minor, but improves readability.

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-03-19
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, requirements.txt, 10 notebooks, 16 data files, 29 figures
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.

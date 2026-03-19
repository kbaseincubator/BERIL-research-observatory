---
reviewer: BERIL Automated Review
date: 2026-03-19
project: cf_formulation_design
---

# Review: CF Protective Microbiome Formulation Design

## Summary

This is an ambitious and well-executed project that integrates experimental data (4,949 isolates, 23 tables) with BERDL pangenome resources to rationally design probiotic formulations for competitive exclusion of *P. aeruginosa* in CF airways. The scientific narrative is compelling — moving from EDA through mechanistic hypothesis testing to a concrete 5-organism formulation backed by pangenome validation and a novel sugar-alcohol prebiotic strategy. The project excels in documentation (thorough REPORT.md with literature context, limitations, and proposed experiments), statistical rigor (appropriate regression, variance decomposition, and effect sizes), and creative use of BERDL resources (GapMind pathway conservation, NCBI environmental metadata for lung tropism). The main areas for improvement are: two notebooks (NB05, NB06) lack saved outputs, the scoring function weights change between NB05 and NB05b without formal sensitivity analysis, and several minor code quality issues (duplicated cell, unhandled NaN species, identical pairwise/monoculture tables discovered late). Overall, this is one of the strongest projects in the observatory — the findings are well-supported, limitations are honestly acknowledged, and the proposed experimental follow-ups are specific and actionable.

## Methodology

**Research question**: Clearly stated, testable, and multi-faceted. The six hypotheses (H0–H6) provide a structured framework with pre-specified expected outcomes and confounders. The null hypothesis (H0: direct antagonism dominates) is explicitly stated and tested against.

**Approach**: The multi-criterion optimization framework is sound. The staged analysis (EDA → mechanism → ecology → optimization → validation → extension) builds logically. The decision to run permissive and strict safety filters as separate notebooks (NB05 vs NB05b) is a good design choice — it shows the reader what safety costs and why the strict filter is necessary.

**Data sources**: Thoroughly documented in both README.md and RESEARCH_PLAN.md. The 23-table PROTECT Gold dataset is loaded and profiled in NB01. BERDL sources are clearly identified with specific table names, row counts, and filter strategies in the query plan.

**Reproducibility concerns**:
- **NB05 (Formulation Optimization) has zero saved outputs** across all 8 code cells. This is the central optimization notebook — the reader cannot see any formulation results, scores, or the scores-by-size visualization without re-running it. The `formulations_ranked.tsv` output file exists (5.1 MB, 22,389 rows), confirming the notebook was run, but outputs were not preserved.
- **NB06 (Prebiotic Pairing) also has zero saved outputs** across all 6 code cells. Again, output files exist but notebook outputs are missing.
- The remaining 8 notebooks all have complete outputs (100% of code cells).
- The README Reproduction section lists NB01→NB07 but omits NB08 and NB09, which are also needed for the complete analysis.
- NB07 and NB09 require BERDL Spark access, which is correctly documented, but expected runtimes are not provided.
- `requirements.txt` is present and complete.

## Code Quality

**Notebook organization**: All notebooks follow a clean setup → analysis → visualization → save → summary pattern. Markdown headers provide clear section breaks. Each notebook begins with a description of its goal, inputs, and outputs.

**SQL queries (NB07, NB09)**: GapMind queries correctly use the `MAX(score_val)` per genome-pathway pair pattern documented in `docs/pitfalls.md`, avoiding the multiple-rows-per-pair trap. The `CAST(... AS DOUBLE)` pattern is used for AVG aggregates, following the documented Spark DECIMAL pitfall. Species clade lookup uses both `RS_` and `GB_` prefixed accessions with a fallback to name-based search — good defensive coding.

**Statistical methods**: Appropriate throughout. Pearson/Spearman correlations for continuous/ordinal relationships, OLS regression with variance decomposition for H1 testing, Kruskal-Wallis for genus effects, geometric mean for engraftability aggregation. The R² = 0.274 for the metabolic model is honestly reported rather than inflated.

**Issues identified**:

1. **Duplicated scoring function in NB05**: Cell-4 is a markdown cell containing Python code (the `score_formulation` function), and cell-5 is a code cell with an identical copy. This appears to be an editing artifact. The markdown cell will not execute, so the code cell is the operative one, but it is confusing.

2. **NB05b formulation deduplication**: The k=5 #2 formulation lists "*Streptococcus salivarius*" twice (two different S. salivarius isolates: ASMA-737 and one of ASMA-1064/ASMA-3933/etc.). The scoring function operates on isolate IDs, not species, so this is valid but means the "5-species" formulation is actually a 4-species formulation with two S. salivarius strains. This should be flagged or filtered.

3. **NaN species values**: Several isolates (APA20015, ASMA-1309, ASMA-2475, ASMA-765) have NaN species throughout the pipeline. APA20015 appears in the top 20 strict-safe candidates (#5 at k=1 with 59% inhibition) as "Unknown." These should either be resolved against `dim_isolate` or explicitly excluded with a note.

4. **`fact_pairwise_interaction` is identical to `fact_carbon_utilization`**: NB08 discovers this (correlation = 1.0, mean_diff = 0.0 for all substrates). This is an important data quality finding that should be documented earlier — it means the "pairwise interaction" table does not contain co-culture data and the metabolic facilitation/competition analysis in Section 2 of NB08 is a dead end. The notebook handles this gracefully with a note, but this should propagate to the REPORT.

5. **Scoring weight sensitivity not implemented**: RESEARCH_PLAN.md §NB05 specifies "Sensitivity analysis: vary criterion weights, check stability of top formulations." The scoring weights change between NB05 (coverage=30%, complementarity=15%, inhibition=35%, engraftability=20%) and NB05b (25%, 10%, 35%, 30%) but there is no systematic sensitivity analysis showing how results change across a range of weights. The consistency of the 5-species core across formulation sizes is noted as evidence of robustness, which is good but not a formal sensitivity test.

6. **NB03 residual merge**: Lines creating `model_data_full` via a merge are immediately overridden by direct `.loc` indexing to attach `asma_id` and `species`. The merge is dead code.

**Pitfall awareness**: The project correctly addresses several `docs/pitfalls.md` entries: GapMind genome ID prefix stripping (`RS_`/`GB_`), `CAST(... AS DOUBLE)` for Spark decimal columns, GapMind `score_category` values (`complete`/`likely_complete` not `present`), and the multiple-rows-per-genome-pathway issue. The `metabolic_category` values (`'aa'`/`'carbon'`) are used correctly. The BacDive utilization values pitfall is not relevant since BacDive is not queried.

## Findings Assessment

**Are conclusions supported?**
- **H1 (metabolic competition)**: r = 0.384, R² = 0.274 — well-supported by the data. The honest reporting of 27% explained variance, with 73% residual, is a strength. The identification of "dual-mechanism species" with high positive residuals is an insightful analysis.
- **H2 (complementary coverage)**: The finding that k=3 achieves 100% niche coverage is supported by NB05b output tables. However, complementarity scores are uniformly low (0.04–0.13) — the formulation members are metabolically similar, not complementary. The niche coverage comes from each species covering a different *subset* of PA14's substrates, not from internal metabolic dissimilarity. This nuance could be discussed more explicitly.
- **H3 (engraftability)**: *N. mucosa*'s top engraftability (1.595) is supported. The engraftability metric (prevalence × log1p(activity_ratio)) is reasonable but the REPORT says "prevalence × log(activity ratio)" — minor inconsistency.
- **H4 (prebiotic)**: The negative result (no amino acid prebiotic) is well-supported. The pivot to sugar alcohols via GapMind (NB09) is the project's most novel finding and is strongly supported by the genomic evidence (100% vs 0% pathway completeness).
- **H5 (pangenome conservation)**: Strongly supported for 4/5 species. The caveat about *G. sanguinis* (7 genomes, 39% AA pathway conservation) is appropriately flagged.
- **H6 (lung adaptation)**: Supported qualitatively (21 lung genomes, enrichment in *R. dentocariosa* and *N. mucosa*). The small sample sizes (5–10 lung genomes) are acknowledged as a limitation.

**Limitations acknowledged**: Yes, comprehensively — planktonic-only assays, 22 tested substrates, 142-isolate core cohort, sparse pairwise data, inferred engraftability, sparse lung metadata. The REPORT §3.5 is thorough.

**Incomplete analysis**: The RESEARCH_PLAN mentions an NB08 for "Genomic Extension & BacDive Validation (if time permits)" — this was partially implemented as NB09 (genomic extension) but BacDive cross-validation and ModelSEED biochemistry analysis were not performed. This is acceptable given the "if time permits" qualifier and should be noted as future work.

**Literature context**: The REPORT §3.3 provides substantive literature integration with specific citations. The RESEARCH_PLAN literature section says "To be populated by /literature-review" but the REPORT itself has a complete references section — this is fine for the REPORT but the PLAN should be updated.

## Suggestions

### Critical (should fix)

1. **Re-execute NB05 and NB06 with saved outputs.** These are core notebooks (formulation optimization and prebiotic analysis) with zero saved outputs. Run `jupyter nbconvert --to notebook --execute --inplace` on both, or Kernel → Restart & Run All. The data files exist confirming they ran successfully — outputs just weren't saved. This is a hard requirement per the observatory standard.

2. **Update README Reproduction section** to include NB05b, NB08, and NB09, which are needed for the complete analysis pipeline. Currently only NB01–NB07 are listed.

### Important (should address)

3. **Filter or flag duplicate-species formulations in NB05b.** Several top-ranked k=5 formulations include two isolates of the same species (e.g., two *S. salivarius* strains). Either add a species-uniqueness constraint to the scoring function, or add a post-hoc column flagging these and discuss whether intra-species strain diversity provides meaningful benefit.

4. **Resolve NaN species isolates.** APA20015, ASMA-1309, ASMA-2475, and ASMA-765 propagate through the pipeline with NaN species. Either resolve them against the isolate catalog or filter them with a documented reason. APA20015 ranks in the top 5 single-isolate candidates under strict safety — its identity matters.

5. **Add scoring weight sensitivity analysis.** Even a simple grid (vary each weight ±10%, check if the top-5 formulations change) would satisfy the RESEARCH_PLAN commitment and strengthen the claim that the 5-species core is robust.

6. **Remove the duplicated cell in NB05.** Cell-4 (markdown) contains the `score_formulation` function source code as markdown text; cell-5 contains it as executable code. Delete cell-4 or convert it to a proper markdown description of the scoring approach.

### Nice-to-have

7. **Document the `fact_pairwise_interaction` = `fact_carbon_utilization` identity** in a project-level note or in the REPORT limitations. This data quality finding in NB08 is important for anyone extending the analysis — they should know this table does not contain co-culture data.

8. **Add expected runtimes** to the Reproduction section. NB07 and NB09 require Spark and may take several minutes per GapMind query across 6,760 PA genomes. Users benefit from knowing what to expect.

9. **Update RESEARCH_PLAN.md Literature Context** section to replace "To be populated by /literature-review" with actual content (which is already present in REPORT.md §3.3). The RESEARCH_PLAN should not have placeholder text in a completed project.

10. **Consider a cross-validation or hold-out test** for the metabolic overlap → inhibition regression. The R² = 0.274 is based on the full 142-isolate cohort. A leave-one-out or 5-fold CV R² would strengthen the predictive claim and could be added to NB03 with minimal effort.

11. **Clarify the NB07 *Neisseria mucosa* clade selection.** The query finds two clades: `s__Neisseria_mucosa_A` (15 genomes) and `s__Neisseria_mucosa` (8 genomes). Only the first is used (`clades[:1]`). Document which clade corresponds to the PROTECT isolate's reference genome (`GCA_003028315.1` maps to `s__Neisseria_mucosa`, the 8-genome clade, but the code uses the 15-genome clade). This may not affect conclusions but should be noted.

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-03-19
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, requirements.txt, 10 notebooks, 16 data files, 26 figures
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.

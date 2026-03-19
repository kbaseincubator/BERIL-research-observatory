---
reviewer: BERIL Automated Review
date: 2026-03-19
project: cf_formulation_design
---

# Review: CF Protective Microbiome Formulation Design

## Summary

This is an exceptionally ambitious and well-executed project that integrates experimental data from the PROTECT CF study (4,949 isolates, 30M+ rows across 23 tables) with BERDL pangenome resources to rationally design commensal formulations for competitive exclusion of *P. aeruginosa* in CF airways. The project excels in its systematic multi-criterion framework, clear narrative structure, honest reporting of limitations (including the negative prebiotic result and modest R² values), and thorough pangenome validation of formulation robustness. All 13 notebooks are committed with saved outputs (100% coverage), 35 figures are generated, and 21 data files are produced. The REPORT.md is publication-quality, with a clear progression from data characterization through hypothesis testing to formulation design and proposed experiments. The main areas for improvement are: (1) a potential safety gap where *Mycobacterium abscessus* may pass through the engraftability filter undetected, (2) the codon usage bias analysis (NB12) has a GC-content confound that undermines its conclusions, (3) the pairwise interaction data (NB08) turned out to be duplicated from the carbon utilization table, limiting interaction modeling, and (4) the formulation scoring function has a structural bias favoring monocultures (k=1) due to the complementarity term.

## Methodology

**Research question**: Clearly stated, multi-part, and testable. The six hypotheses (H0–H6) are well-formulated with explicit predictions and identified confounders.

**Approach**: The multi-criterion optimization framework (niche coverage, complementarity, inhibition, engraftability, safety) is well-motivated and systematic. The staged safety filter approach (permissive → strict) is a smart design that reveals how clinical constraints reshape the candidate pool. The progression from single-organism characterization through community-level optimization to pangenome validation is logically sound.

**Data sources**: Clearly identified in both README.md and RESEARCH_PLAN.md, with specific table names, row counts, and roles in analysis. The separation between local parquet data (NB01–06, NB08) and BERDL Spark queries (NB07, NB09–12) is well-documented.

**Reproducibility**: Strong. The README includes a clear reproduction section with prerequisites, notebook ordering, and runtime estimates. A `requirements.txt` is present with pinned minimum versions. The Spark vs. local separation is clearly documented (NB07, NB09–12 need BERDL; others run locally). All notebooks have 100% output coverage — every code cell has saved outputs including text, tables, and 34 cells with embedded figures. The `figures/` directory contains 35 visualizations covering all analysis stages.

## Code Quality

**Notebook organization**: All 13 notebooks follow a consistent pattern: imports/setup → data loading → analysis → visualization → summary → data export. Markdown headers provide clear narrative structure throughout. Every notebook saves intermediate results as TSV files for downstream consumption.

**SQL queries**: The Spark SQL queries in NB07, NB09–12 are structurally correct and follow BERDL best practices. The GapMind score encoding (`CASE WHEN score_category = 'hi' THEN 5 ...`) is consistent across notebooks. The project correctly handles the `gapmind_pathways.clade_name` format (using `gtdb_species_clade_id` values, not short species names), avoids the `DISTINCT + aggregate` pitfall documented in `docs/pitfalls.md`, and uses `CAST(... AS DOUBLE)` for numeric operations — all known pitfalls addressed.

**Statistical methods**: Generally appropriate. OLS regression with cross-validation (NB03), Pearson/Spearman correlations, Kruskal-Wallis tests, Mann-Whitney U with BH-FDR correction (NB10–11), PCA, and K-means clustering. The 5-fold cross-validation in NB03 that reveals overfitting (train R²=0.274, CV R²=0.145) is a commendable self-check that many analyses omit.

**Issues identified**:

1. **NB12 GC-content confound**: The codon usage bias (CUB) analysis compares species spanning GC3 content from 16% (*G. sanguinis*) to 91% (*M. luteus*). The simplified chi-squared CUB metric is inherently inflated for organisms with extreme GC composition. The conclusion that "commensals have higher CUB than PA (688 vs 644)" is not biologically meaningful without GC correction. This does not affect the formulation design (CUB is not used as a scoring criterion) but weakens the growth rate interpretation in the Discussion (Section 3.3).

2. **NB11 silhouette interpretation**: The K-means clustering of lung PA genomes yields a high silhouette score (0.952) for k=2, but the summary text says "Low silhouette score — PA variation is a CONTINUUM." The conditional check (`if sil_df.silhouette.max() < 0.3`) correctly identifies this as a high score, but the summary text is misleading. The minor cluster (53 genomes, 3%) may represent incomplete/low-quality assemblies rather than a biologically distinct subpopulation.

3. **NB05 complementarity bias**: Single-organism formulations receive complementarity=1.0 (by definition, no self-competition), which inflates k=1 scores relative to multi-organism formulations. This creates a scoring paradox where monocultures outscore consortia, contradicting the biological rationale. The strict safety notebook (NB05b) mitigates this with rebalanced weights, but the structural issue remains.

4. **NB08 identical tables**: The discovery that `fact_pairwise_interaction` and `fact_carbon_utilization` contain identical data (correlation=1.0) is honestly reported but limits the interaction modeling. The pairwise synergy analysis draws conclusions from only 8 comparisons across 5 pairs — too few for reliable interaction classification.

5. **NB10 sick vs. stable comparison**: The log2FC analysis of PA pathway expression between acute and stable patients reports fold changes without formal statistical testing (no p-values). Given the small sample sizes (~20 total), the dramatic claims (e.g., "PA massively downregulates 170 of 207 pathways") would benefit from significance testing.

## Findings Assessment

**Conclusions supported by data**: The core findings are well-supported: metabolic overlap predicts inhibition (r=0.384, p=2.3×10⁻⁶), the five-species formulation achieves 100% niche coverage, pangenome conservation is strong (>95% for 4/5 species), and sugar alcohols are genomically predicted as selective prebiotics. The identification of "dual-mechanism" species (metabolic + direct antagonism) through residual analysis is a genuine insight.

**Limitations acknowledged**: The report has an unusually thorough limitations section (Section 3.7), covering planktonic-only assays, 22 tested substrates, small cohort sizes, sparse interaction data, inferred engraftability, sparse lung metadata, and the identical CU/PW table issue. The *N. mucosa* clade selection limitation is also noted with a sensitivity check showing the primary analysis is conservative.

**Incomplete analysis**: The prebiotic pairing notebook (NB06) produces `data/prebiotic_pairings.tsv` pairing formulations with substrates where PA14 still dominates (selectivity <1), since no selective amino acid prebiotic exists. This file's utility is limited. The genomic extension (NB09) provides the real prebiotic answer (sugar alcohols) but requires experimental validation.

**Potential safety concern**: The engraftability analysis (NB04) may not adequately filter *Mycobacterium abscessus*, a critical CF pathogen. While the safety filter in NB05/05b uses a strict exclusion list, the engraftability table itself (used as a standalone reference) could mislead if consulted without the downstream safety filter. The species-level safety flags should be applied earlier in the pipeline.

**Visualizations**: The 35 figures are clear, properly labeled, and cover all analysis stages from EDA through results. The clustermap (NB01), rate advantage heatmap (NB02), and pathway conservation heatmaps (NB07) are particularly effective at conveying complex multi-dimensional data.

## Suggestions

### Critical

1. **Fix the NB12 CUB analysis or add a GC-correction caveat**: Either implement a GC-corrected CUB metric (e.g., Effective Number of Codons adjusted for GC3, or the S-value from Vieira-Silva & Rocha 2010) or add an explicit caveat to the REPORT.md Discussion (Section 3.3) that the cross-species CUB comparison is confounded by GC content and should not be interpreted as evidence of comparable growth rates.

2. **Add statistical testing to the sick vs. stable PA comparison (NB10)**: The claim that PA "massively downregulates" pathways during acute episodes should be supported by Mann-Whitney U tests with FDR correction, matching the approach used for lung vs. non-lung comparisons in the same notebook.

3. **Apply safety flags to the engraftability table (NB04)**: Add a `safety_flag` column to `data/species_engraftability.tsv` so that downstream consumers of this file are immediately aware of excluded species like *M. abscessus*, even outside the formulation pipeline context.

### Important

4. **Address the NB05 complementarity scoring paradox**: Consider normalizing the complementarity score by formulation size or using a different formulation: e.g., complementarity = 1 − (mean pairwise overlap / maximum possible overlap for k organisms). This would prevent single organisms from having an artificial scoring advantage.

5. **Add the *N. mucosa* clade sensitivity check to REPORT.md Section 2.8**: The notebook shows that using the 8-genome `s__Neisseria_mucosa` clade (which matches the PROTECT isolate reference genome) gives stronger conservation than the 15-genome `s__Neisseria_mucosa_A` clade used in the primary analysis. This strengthens the main conclusion and should be mentioned in the report body, not just the limitations.

6. **Clarify the NB11 minor cluster interpretation**: Investigate whether the 53-genome minor cluster (3% of lung PA) represents low-quality assemblies (check genome completeness/contamination if available) or a genuinely distinct metabolic subpopulation. Correct the summary text that refers to "low silhouette" when the score is 0.952.

### Nice-to-Have

7. **Add a `requirements.txt` note about PySpark**: The requirements.txt lists standard Python packages but does not mention `pyspark` or `berdl_notebook_utils`, which are required for NB07, NB09–12. Adding a comment like `# NB07, NB09-12 also require pyspark (provided by BERDL JupyterHub)` would help.

8. **Consider targeted prebiotic selectivity analysis (NB06)**: The current analysis computes selectivity using the mean growth across all safe commensals. Recomputing selectivity using only the 5 core formulation species might reveal more favorable ratios for some substrates, since these species were selected partly for high growth on PA-preferred substrates.

9. **Update the REPORT.md figure count**: Section 6 states "25 total" figures but there are 35 PNG files in the `figures/` directory (including figures from NB10–12 added after the initial count).

10. **Document the NB08 data issue more prominently**: The identical CU/PW tables finding is buried in the limitations section. Since this fundamentally limits the interaction modeling, consider adding a brief note in the NB08 section header of the report (Section 2.10) rather than only in Section 3.7.

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-03-19
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, 13 notebooks, 21 data files, 35 figures, requirements.txt, docs/pitfalls.md
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.

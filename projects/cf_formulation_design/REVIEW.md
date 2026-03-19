---
reviewer: BERIL Automated Review
date: 2026-03-19
project: cf_formulation_design
---

# Review: CF Protective Microbiome Formulation Design

## Summary

This is an exceptionally well-executed translational microbiology project that integrates a large experimental dataset (23 tables, 30.5M rows from the PROTECT study) with BERDL pangenome resources to design rationally optimized probiotic formulations for competitive exclusion of *P. aeruginosa* in cystic fibrosis airways. The analysis is rigorous, the narrative arc is compelling (from EDA through hypothesis testing to actionable formulation design), and the documentation is among the most thorough in the observatory. The project correctly identifies limitations (planktonic-only assays, sparse pairwise data, M. luteus engraftment concerns) and proposes specific follow-up experiments. The main areas for improvement are: (1) the `fact_pairwise_interaction` table is identical to `fact_carbon_utilization` (acknowledged in limitations), limiting co-culture metabolic analysis; (2) cross-validation reveals the metabolic model overfits substantially (CV R² = 0.145 vs training R² = 0.274), which the report acknowledges honestly; and (3) the NB05 permissive-filter optimization is dominated by clinically unviable organisms, making NB05b (strict safety) the more scientifically relevant analysis — this staged design is a strength, not a flaw.

## Methodology

### Research Question & Hypotheses
The research question is clearly stated and testable: whether metabolic competition predicts PA14 inhibition and whether multi-criterion optimization can design viable formulations. Six hypotheses (H0–H6) are well-articulated in RESEARCH_PLAN.md with specific testable predictions and defined outcome criteria. The literature context is thorough, citing foundational CF sputum metabolism work (Palmer 2005/2007), commensal protection studies (Rigauts 2022, Stubbendieck 2023), and regulatory precedent (Dreher 2017).

### Approach
The multi-stage pipeline is sound: data integration → feature extraction → univariate/multivariate modeling → optimization → validation → extension. Each notebook has a clear goal and feeds defined outputs into downstream analyses. The staged safety filter (NB05 permissive → NB05b strict) is a particularly thoughtful design choice that transparently shows what clinical safety costs in terms of efficacy.

### Data Sources
Data sources are clearly identified in both README.md and RESEARCH_PLAN.md with row counts, column descriptions, and roles in the analysis. The BERDL tables used (GapMind, ncbi_env, phagefoundry) are well-chosen for the questions asked. The known pitfall about GapMind genome IDs lacking the RS_/GB_ prefix (documented in `docs/pitfalls.md`) is correctly handled in NB07 (cell 4 and cell 14).

### Reproducibility
**Strengths:**
- All 9 notebooks have saved outputs (text, tables, figures) — this is a hard requirement that is fully met.
- The `figures/` directory contains 25 PNG files covering every analysis stage.
- A `requirements.txt` is present with versioned dependencies.
- The README includes a clear Reproduction section: notebook execution order, which notebooks need Spark (NB07, NB09), and approximate runtimes.
- Data files in `data/` (16 TSV files, 12MB total) enable local re-execution of downstream notebooks without Spark access.

**Minor gaps:**
- The input data (`~/protect/gold/*.snappy.parquet`) is not included in the repository and requires PROTECT study access. This is appropriate for a private dataset but limits external reproducibility.
- NB05b reweights the scoring function (engraftability 30% vs 20%) relative to NB05 without formal justification — the sensitivity analysis (cell 13) partially addresses this by showing the 5-species core is stable across weight variations.

## Code Quality

### Notebook Organization
All notebooks follow the setup → load → analyze → visualize → save pattern consistently. Markdown headers provide clear section structure. Summary cells at the end of each notebook print key statistics, making it easy to verify outputs without re-running.

### SQL & Spark Queries
NB07 and NB09 use correct GapMind query patterns: the critical `MAX(score_val)` aggregation per genome-pathway pair (avoiding the multiple-rows-per-pair pitfall from `docs/pitfalls.md`) is correctly implemented with CTEs. The `CAST(... AS DOUBLE)` pattern for `AVG()` aggregates addresses the Spark DECIMAL pitfall. Genome ID prefix handling (RS_/GB_ stripping) is correctly applied in NB07 cell 14.

### Statistical Methods
- The metabolic overlap metric (weighted sum of min(commensal, PA14) OD) is reasonable and clearly defined.
- The OLS regression (NB03) correctly progresses from univariate to multivariate with variance decomposition.
- Cross-validation (5-fold, cell 14) is appropriately applied and the overfitting gap (0.129) is honestly reported — this is a sign of methodological maturity.
- The Kruskal-Wallis test for genus effects is appropriate for non-normal distributions.
- The formulation scoring function uses cosine similarity for complementarity and geometric mean for engraftability — both reasonable choices.

### Pitfall Awareness
The project correctly handles several documented pitfalls:
- GapMind `clade_name` format (uses `gtdb_species_clade_id`, not `GTDB_species`) — NB07 cell 4
- GapMind score categories (`complete`, `likely_complete`, etc., not `present`) — NB07 cell 7
- GapMind genome IDs lack RS_/GB_ prefix — NB07 cell 14
- BacDive metabolite utilization 4-value issue — noted in RESEARCH_PLAN.md performance plan but BacDive was ultimately not queried (NB08 was repurposed for interaction modeling)
- `CAST(... AS DOUBLE)` for Spark AVG — NB07 cell 7, NB09 cell 4

### Potential Issues
1. **NB03 cell 18**: The safety filter in `single_isolate_scores.tsv` uses a manually curated genus list. An APA20015 isolate with `species=NaN` appears in the top 20 (line `APA20015, NaN, NaN, 0.428, 58.771, 0.550`). This Unknown isolate should be excluded or flagged more prominently.
2. **NB05 cell 4**: The `score_formulation` function imports `cosine_similarity` from sklearn inside the function body, which is called ~22,000 times. This works but is inefficient — the import should be at module level.
3. **NB08 cell 3**: The species lookup for ASMA-2260 returns a Series (two duplicate rows) instead of a scalar, producing garbled output in the pair summary. This is a cosmetic display bug, not a calculation error.
4. **NB07 cell 5**: For *Neisseria mucosa*, two clades exist (`s__Neisseria_mucosa_A` with 15 genomes, `s__Neisseria_mucosa` with 8 genomes). The analysis uses the A clade (15 genomes) but the PROTECT isolate reference genome (`GCA_003028315.1`) maps to the non-A clade (8 genomes). The REPORT.md limitations section correctly notes this and reports that the 8-genome clade shows *stronger* conservation, making the primary analysis conservative.

## Findings Assessment

### Are Conclusions Supported?
**Yes, with appropriate caveats.** The key claims are well-supported:

- **H1 (metabolic competition)**: r = 0.384, p = 2.3×10⁻⁶ is statistically robust. The R² = 0.274 (27% variance explained) is honestly characterized as "supported but incomplete." The CV R² = 0.145 is reported transparently.
- **H2 (complementary coverage)**: The k=3 formulation achieving 100% niche coverage is a clear, verifiable result from the optimization. The sensitivity analysis (NB05b cell 13) showing identical top-5 species across all weight variations is convincing.
- **H3 (engraftability)**: The engraftability scoring (prevalence × log(activity ratio)) is a reasonable proxy, with appropriate disclaimers that patient prevalence ≠ colonization persistence.
- **H4 (prebiotic — amino acids)**: Correctly rejected — PA14 outgrows commensals on all tested substrates. This negative result is valuable.
- **H5 (pangenome conservation)**: Strongly supported — 4/5 species show >95% AA pathway conservation. *G. sanguinis* (7 genomes, 39% AA conservation) is appropriately flagged as the exception.
- **Sugar alcohol prebiotic discovery**: The 6 GapMind pathways with 100% selectivity (0% PA, 100% commensal) is a striking finding. The recommendation to validate experimentally is appropriate.

### Limitations Acknowledged
The REPORT.md limitations section (3.6) is unusually thorough: planktonic-only assays, 22-substrate limitation, sparse pairwise data (8 comparisons), engraftability as proxy, sparse lung metadata, `fact_pairwise_interaction` identity issue, and the *N. mucosa* clade ambiguity. The *M. luteus* engraftment question (Section 3.2) is a particularly honest discussion of a design tension that could have been glossed over.

### Incomplete Analysis
- **NB08 pairwise interaction**: The `fact_pairwise_interaction` table proved identical to `fact_carbon_utilization`, making the per-substrate co-culture analysis impossible. This is documented as a limitation.
- **BacDive validation**: Listed in RESEARCH_PLAN.md NB08 but not executed (NB08 was repurposed for competition assay analysis). External validation of carbon utilization predictions is absent.
- **Fitness Browser**: Listed as a data source in RESEARCH_PLAN.md but not used in any notebook. Gene essentiality under defined carbon/nitrogen conditions could strengthen the metabolic competition narrative.

## Suggestions

### Critical
1. **Validate the N. mucosa clade assignment**: NB07 uses `s__Neisseria_mucosa_A` (15 genomes) but the PROTECT isolate maps to `s__Neisseria_mucosa` (8 genomes). While the report notes the 8-genome clade is more conserved, the primary tables (`pangenome_conservation.tsv`, formulation scores) use the 15-genome clade data. Consider adding a sensitivity check column in the conservation table or re-running with the correct clade as the primary analysis.

2. **Address the Unknown isolate (APA20015)**: This isolate with `species=NaN` appears in NB03's top 20 candidates and NB05's formulation rankings. Either identify it or explicitly filter it from all downstream analyses.

### Important
3. **Add BacDive external validation**: The RESEARCH_PLAN.md lists BacDive cross-validation (NB08 scope), but it was not executed. Even a brief check — do BacDive utilization records for *S. salivarius*, *N. mucosa*, *R. dentocariosa* support the carbon profiles measured in the PROTECT assays? — would strengthen the translational argument. The `fw300_metabolic_consistency` pitfall about BacDive's 4-value utilization field should be addressed.

4. **Expand pairwise interaction coverage**: Only 5 unique pairs were tested, and only 2 involve core formulation species (*N. mucosa* pairs). The report correctly identifies this as a critical gap (Proposed Experiment 4.2). Consider adding a "pairwise interaction priority matrix" figure showing which of the 10 possible pairs among the 5-species core have been tested vs. not.

5. **Report effect sizes with confidence intervals**: The key statistics (r = 0.384, R² = 0.274, CV R² = 0.145) are reported as point estimates. Adding 95% confidence intervals (bootstrap or parametric) would strengthen the quantitative claims.

### Nice-to-Have
6. **Move the import inside `score_formulation` (NB05 cell 4) to module level**: `from sklearn.metrics.pairwise import cosine_similarity` is called inside a function executed ~22,000 times. While Python caches imports, this is cleaner at the top of the notebook.

7. **Add a consolidated formulation comparison figure**: The REPORT.md Section 2.6 table is informative but a single figure showing k=1→5 formulations with bars for coverage, inhibition, and engraftability would be more immediately readable than the bar chart in `05_formulation_scores_by_size.png` (which only shows composite score).

8. **Harmonize NB05/NB05b scoring weights**: NB05 uses (30% coverage, 15% complementarity, 35% inhibition, 20% engraftability) while NB05b uses (25%, 10%, 35%, 30%). The weight change is not clearly motivated in the notebook — add a markdown cell explaining the rationale.

9. **Consider Bonferroni or BH correction for the multi-hypothesis framework**: Six hypotheses are tested without formal multiple-testing correction. While each is evaluated qualitatively and the primary result (H1: r = 0.384) has a very small p-value (2.3×10⁻⁶), noting this in the methods section would be more rigorous.

10. **Add a KEGG-to-GapMind pathway name mapping**: NB09 identifies 6 GapMind genomic candidates and 47 KEGG transcriptomic candidates but notes these use different naming conventions. A manual cross-reference table linking the GapMind sugar alcohol pathways to their KEGG equivalents would close this integration gap.

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-03-19
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, 9 notebooks (NB01–NB09), 16 data files, 25 figures, requirements.txt
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.

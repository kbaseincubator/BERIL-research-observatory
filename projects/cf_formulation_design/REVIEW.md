---
reviewer: BERIL Automated Review
date: 2026-03-19
project: cf_formulation_design
---

# Review: CF Protective Microbiome Formulation Design

## Summary

This is an ambitious and well-executed project that integrates experimental data from the PROTECT CF Synbiotic Cocktail Study (4,949 isolates, 23 tables, 30M rows) with BERDL pangenome resources to rationally design probiotic formulations for competitive exclusion of *P. aeruginosa* in CF airways. The work is notable for its rigorous multi-criterion optimization framework, honest treatment of negative results (no amino acid prebiotics exist; metabolic competition explains only ~15–27% of variance), and the productive pivot from amino acid to sugar alcohol prebiotic candidates via genomic extension. All 10 notebooks are executed with saved outputs, 28 figures are generated, and the three-file documentation structure (README, RESEARCH_PLAN, REPORT) is thorough. Key areas for improvement include: the *N. mucosa* pangenome clade mismatch between the isolate and the analysis, *M. luteus*'s zero engraftability and zero lung genomes despite being critical for niche coverage, and the sugar alcohol prebiotic claims needing clarification that only 1–2 of 5 core species carry each pathway.

## Methodology

**Research question**: Clearly stated and testable. The six hypotheses (H0–H6) are well-articulated, with explicit predictions and falsification criteria. The staged analysis (single-isolate → formulation → pangenome → prebiotic) follows a logical narrative arc.

**Data sources**: Thoroughly documented in both the README and RESEARCH_PLAN, with row counts, column descriptions, and roles for all 23 experimental tables and 6 BERDL databases. The query strategy section in RESEARCH_PLAN includes estimated row counts and filter strategies — a strong practice.

**Approach soundness**: The multi-criterion formulation scoring function (niche coverage, complementarity, inhibition, engraftability, safety) is well-motivated and the weights are subjected to sensitivity analysis (NB05b cell-13), which shows the 5-species core is stable across all tested weight configurations. The two-stage safety filter (NB05 permissive → NB05b strict) is a thoughtful design that preserves the full analysis while revealing what FDA viability costs.

**Reproducibility**:
- All 10 notebooks have saved outputs (text, tables, and figures) — a hard requirement that is fully met.
- The `figures/` directory contains 28 visualizations covering all major analysis stages.
- A `requirements.txt` is provided with pinned minimum versions.
- The README includes a clear Reproduction section with prerequisites, step ordering, and runtime estimates.
- Spark vs local separation is documented: NB07 and NB09 require BERDL Spark; all others run locally from cached parquet files.
- NB07 and NB09 correctly use `from berdl_notebook_utils.setup_spark_session import get_spark_session` for the on-cluster environment.

**Known pitfalls addressed**:
- GapMind genome ID prefix stripping (`RS_`/`GB_`) is noted in the RESEARCH_PLAN and handled in NB07 cell-14.
- GapMind score categories (`complete`, `likely_complete`, etc.) are correctly handled with the numeric hierarchy pattern from `docs/pitfalls.md`.
- `CAST(AVG(...) AS DOUBLE)` is used in GapMind queries (NB07 cell-7, NB09 cell-4) to avoid the Spark DECIMAL pitfall.
- BacDive's 4-value utilization field is acknowledged in the RESEARCH_PLAN's "Known pitfalls" section.
- The `fact_pairwise_interaction` = `fact_carbon_utilization` identity is discovered and documented (NB08 cell-8, REPORT Section 3.5).

## Code Quality

**SQL correctness**: GapMind queries use the correct pattern: CTE with score mapping → MAX per genome-pathway → AVG with CAST to DOUBLE. The `clade_name` filter is applied correctly. PA14 clade lookup (NB09 cell-3) uses exact equality as recommended. One minor issue: NB07 cell-4 builds the genome ID filter via string interpolation (`WHERE genome_id IN ('{ref_list}')`), which works but is fragile if accessions contain special characters.

**Statistical methods**: Appropriate throughout. Pearson and Spearman correlations for univariate analysis, OLS regression with variance decomposition, 5-fold cross-validation with honest reporting of the overfitting gap (training R² = 0.274 vs CV R² = 0.145), Kruskal-Wallis for genus effects. The cross-validation result is a strength — many projects would report only the training R².

**Growth parameter extraction** (NB02 cell-5): The Savitzky-Golay smoothing + numerical differentiation approach for μ_max is reasonable, though the lag time definition (10% of max growth rate threshold) could be sensitive to noise in low-growth conditions. The method is clearly documented.

**Formulation optimization** (NB05/NB05b): The combinatorial approach (exhaustive for small k, top-N candidates for larger k) is practical. The `score_formulation_v2` function in NB05b correctly filters duplicate-species formulations. However, the candidate pool sizes differ between NB05 (top 40/20) and NB05b (top 50/30), making the formulation counts not directly comparable (22,389 vs 22,515).

**Notebook organization**: Consistently follows the pattern: markdown introduction → data loading → analysis → visualization → save outputs → summary. Each notebook has a clear purpose statement, input/output specification, and summary cell.

**Minor issues**:
1. NB08 cell-3: `id_species.get('ASMA-2260')` returns a Series rather than a string because the isolates table has duplicate rows for ASMA-2260, causing messy display in the pair summary table.
2. NB03 cell-11: The merge for species names (`model_data_full`) is followed by a direct index-based assignment (`model_data['asma_id'] = cohort.loc[model_data.index, 'asma_id'].values`), which works but is fragile if indices don't align.
3. Several isolates have `NaN` species annotations (e.g., APA20015 appears in the top 20 candidates in NB03 cell-18 and NB05b cell-4 as "Unknown"). These should be resolved or excluded from ranking.

## Findings Assessment

**Conclusions well-supported**:
- H1 (metabolic competition): The r = 0.384 correlation is statistically significant and the effect size is honestly reported with cross-validation.
- H2 (complementary coverage): The k=3 formulation achieving 100% niche coverage is a clear quantitative result.
- H5 (conservation): The >95% pathway conservation across hundreds of genomes is compelling.
- The "dual-mechanism species" concept (metabolic competition + direct antagonism) is well-supported by the residual analysis.

**Limitations acknowledged**: The REPORT Section 3.5 is thorough, covering planktonic-only assays, sparse pairwise data, inferred engraftability, and the `fact_pairwise_interaction` data identity issue.

**Areas needing stronger caveats**:

1. ***M. luteus* engraftability gap** (critical): *M. luteus* has engraftability = 0.000 (not detected in any patient metagenome) and 0 lung/respiratory genomes in the pangenome. Yet it is the essential species for achieving 100% niche coverage at k=3. The REPORT mentions "it may face engraftment challenges despite its metabolic contribution" (Section 2.9), but this deserves more prominent treatment. A formulation whose niche-coverage keystone cannot engraft is a fundamental design risk. The report should explicitly discuss whether the k=2 formulation (*R. dentocariosa* + *N. mucosa*, both lung-adapted) might be preferable despite lower coverage.

2. ***N. mucosa* clade mismatch**: NB07 cell-5 shows two clades: `s__Neisseria_mucosa_A` (15 genomes) and `s__Neisseria_mucosa` (8 genomes). The PROTECT isolate reference genome (`GCA_003028315.1`) maps to the 8-genome clade (`GB_GCA_003028315.1`), but NB07 uses the 15-genome clade for all conservation analysis. The REPORT notes this in limitations (Section 3.5), but the pangenome validation for *N. mucosa* — the formulation's anchor species — is technically for a different clade than the actual isolate. The 8-genome clade should be analyzed as a sensitivity check.

3. **Sugar alcohol prebiotic specificity**: The REPORT Table (Section 2.11) states "Commensal Completeness: 100%" for xylitol, myoinositol, etc. However, NB09 cell-5 shows `n_commensals_complete` is only 1–2 out of 5 species for each pathway. The "100%" refers to `max_commensal` (the best single species), not all 5. The REPORT table and text should clarify that these are single-species capabilities, not consortium-wide, and identify which species carry each pathway.

4. **Mean inhibition interpretation**: The k=5 formulation reports "78% mean inhibition," but individual species inhibitions range from 38% (*M. luteus*) to 98% (*S. salivarius*). The mean is dominated by the high-inhibition members. Whether the low-inhibition members contribute meaningfully to competitive exclusion beyond niche coverage is not tested.

5. **Pairwise interaction extrapolation**: Only 5 unique pairs were tested (none involving *M. luteus*, *S. salivarius*, or *G. sanguinis* from the core formulation). The conclusion that "N. mucosa pairs are near-additive" is based on 2 pairs. The REPORT appropriately flags this as underpowered (Section 2.10), but the k=3–5 formulation recommendations still assume additive interactions for untested pairs.

## Suggestions

1. **(Critical) Analyze the alternate *N. mucosa* clade**: Re-run the GapMind conservation analysis for `s__Neisseria_mucosa` (8 genomes, the clade matching the PROTECT isolate) and compare results with the current `s__Neisseria_mucosa_A` analysis. This validates whether the conservation claims hold for the actual formulation strain's clade.

2. **(Critical) Discuss *M. luteus* engraftment risk prominently**: Add a dedicated subsection in the Discussion addressing the k=3 formulation's dependency on a species with zero patient detection and zero lung genomes. Consider whether an alternative species could provide niche coverage (e.g., the Bacillus species in the permissive analysis, or whether a non-complete-coverage formulation with higher engraftability is preferable).

3. **(Important) Clarify sugar alcohol prebiotic claims**: In REPORT Section 2.11, revise the table to show per-species pathway completeness (not just max). Add a column indicating which specific species carry each pathway, so readers know whether the prebiotic feeds the anchor species or a peripheral member.

4. **(Important) Resolve NaN-species isolates**: APA20015 and other isolates with missing species annotations appear in candidate rankings (NB03 cell-18, NB05b cell-4). Either resolve their taxonomy or exclude them from formulation scoring to avoid recommending organisms of unknown identity.

5. **(Moderate) Add a figure for the amino acid pathway conservation heatmap**: NB07 generates `07_aa_pathway_conservation.png` but the notebook code for this figure appears to be missing from the saved outputs (the carbon pathway heatmap is in cell-10, but no corresponding amino acid heatmap cell is visible). Verify this figure was generated from the conservation data and add the generating code if missing.

6. **(Moderate) Fix ASMA-2260 species display in NB08**: The `id_species.get()` call returns a Series for ASMA-2260 due to duplicate entries in the isolates table. Use `.iloc[0]` or `.drop_duplicates()` to get a clean string.

7. **(Minor) Standardize formulation candidate pool sizes**: NB05 uses top 40/20 candidates while NB05b uses top 50/30, making the total formulation counts (22,389 vs 22,515) not directly comparable. Consider using the same pool sizes or noting the difference.

8. **(Minor) Add *P. aeruginosa* to the conservation heatmap legend**: Figure `07_carbon_pathway_conservation.png` shows 5 commensal species. Adding PA14 to this figure (from NB09 data) would make the prebiotic argument self-contained in a single visualization.

9. **(Minor) Document the growth parameter extraction method**: NB02's `extract_params()` function uses a 10% threshold for lag time detection. Consider noting the sensitivity of this choice in a markdown cell, especially for substrates where growth is marginal.

10. **(Enhancement) Add a consolidated formulation comparison table**: Create a single table in the REPORT that shows the top formulation at each k=1–5 under both permissive and strict filters side-by-side, with all scoring criteria. The current format requires reading across NB05 and NB05b outputs.

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-03-19
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, 10 notebooks, 16 data files, 28 figures
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.

---
reviewer: BERIL Automated Review
date: 2026-02-25
project: fw300_metabolic_consistency
---

# Review: Metabolic Consistency of Pseudomonas FW300-N2E3

## Summary

This is a well-conceived and carefully executed project that asks an original question — whether four independent BERDL metabolic databases (Web of Microbes, Fitness Browser, BacDive, GapMind) paint a coherent metabolic picture for a single organism. The research plan is thorough, the notebooks are logically structured with saved outputs, and the REPORT.md provides strong biological interpretation grounded in literature. The headline finding (94% concordance with tryptophan overflow as the key discordance) is well-supported where data exists. The main weaknesses are the low cross-database overlap (only 21/58 metabolites testable), the incomplete Reproduction section in the README, the absence of the planned Notebook 4 (pathway-level analysis), and the lack of a statistical baseline test for concordance. Overall, this is a strong analysis that demonstrates the value of multi-database integration and identifies a genuinely interesting biological signal.

## Methodology

**Research question**: Clearly stated in both README.md and RESEARCH_PLAN.md — whether exometabolomic, fitness, phenotypic, and computational pathway data are consistent for FW300-N2E3. The null and alternative hypotheses are well-formulated (RESEARCH_PLAN.md lines 9-11), and the five key comparisons (WoM↔FB, WoM↔BacDive, FB↔BacDive, WoM↔GapMind, FB↔GapMind) are clearly laid out.

**Approach soundness**: The three-way triangulation strategy is appropriate for the question. Starting from WoM-produced metabolites and matching outward to other databases is a defensible choice. The manual metabolite name harmonization (NB01, cell `613d8f51`) is transparent — all mappings are explicit Python dictionaries rather than opaque fuzzy matching, which aids reproducibility.

**Data sources**: All four databases are clearly identified with specific table names, strain identifiers, and expected row counts (RESEARCH_PLAN.md, "Data Sources" section). The REPORT.md "Data" section lists all generated files with row counts.

**Reproducibility gaps**:
- The README.md Reproduction section (line 24) says "*TBD — add prerequisites and step-by-step instructions after analysis is complete*" despite the project being marked as complete. This is a significant gap.
- No `requirements.txt` or environment specification. The notebooks use `pandas`, `numpy`, `matplotlib`, and `get_spark_session()` — the first three are standard, but the Spark dependency is critical and undocumented.
- Notebooks 01 and 02 require Spark access; Notebook 03 runs from cached TSV files. This separation is good practice but is not documented.

**Notable methodological strength**: The sample-size-aware BacDive confidence scoring (high/moderate/low based on number of strains tested) is a thoughtful addition that prevents over-interpreting sparse data. This should be standard practice for BacDive analyses.

## Code Quality

**SQL correctness**: All Spark SQL queries are well-formed, correctly filtered, and use appropriate joins. Key pitfalls from `docs/pitfalls.md` are properly addressed:
- GapMind multiple rows per genome-pathway pair: Correctly handled with `MAX(score_value) ... GROUP BY pathway, genome_id` in NB01 cell `6529bbfb`, exactly as recommended in the pitfalls document.
- Fitness Browser string columns: Correctly cast with `CAST(gf.fit AS DOUBLE)` and `CAST(gf.t AS DOUBLE)` in NB02 cell `cell-4`.
- Experiment table naming: Uses correct `experiment` table with `expName`, `expGroup`, `condition_1` column names.

**Genome ID handling**: NB01 cell `6529bbfb` gracefully handles the `RS_` prefix mismatch between the pangenome genome ID (`RS_GCF_001307155.1`) and the actual GapMind data (`GCF_001307155.1`), trying multiple matching strategies. This is robust engineering.

**Metabolite name matching**: The manual crosswalk approach (NB01 cell `613d8f51`) is the right choice for this scale of analysis. Two mappings are acknowledged as imprecise: Cytosine→Cytidine and Uracil→Uridine (base vs. nucleoside). These are noted in comments, which is good, but they could introduce false concordance for 2 of the 28 WoM-FB matches.

**Minor code issues**:
1. In the `normalize_compound_name()` function (NB01 cell `613d8f51`), the regex `^(l-|d-|dl-|d,l-|d/l-)` only strips stereochemistry prefixes at the start of the string. This works for the current data but wouldn't catch mid-string stereochemistry (e.g., "Sodium D,L-Lactate" — though this is handled by the manual crosswalk).
2. In the BacDive query (NB01 cell `2e096ab3`), the `n_positive` and `n_negative` counts include duplicates across strains (the `n_total` for D-glucose is 104 from 51 strains), meaning some strains have multiple test records. The `pct_positive` calculation uses these raw counts rather than per-strain consensus. For this analysis the effect is minor, but it's worth noting.

**Notebook organization**: Each notebook follows a clean setup→query→analysis→visualization→summary pattern. Markdown headers clearly delineate sections. Summary statistics are printed at the end of each notebook.

## Findings Assessment

**Concordance claim**: The "94% mean concordance" headline is accurate for the testable subset but should be interpreted carefully. Only 21/58 (36%) of WoM metabolites could be tested against any other database, and only 3 metabolites achieved four-way coverage (malate, arginine, valine). The 64% of metabolites classified as "wom_only" are excluded from the concordance calculation. The REPORT.md limitations section (lines 117-118) acknowledges this appropriately.

**Tryptophan overflow finding**: This is the strongest and most interesting result. The convergence of evidence from four databases (WoM: produced, FB: 231 significant genes, GapMind: complete pathway, BacDive: 0/52 strains utilize) is compelling. The cross-feeding interpretation is well-supported by cited literature (Fritts et al. 2021, Ramoneda et al. 2023, Yousif et al. 2025). The claim that this is the "first systematic cross-database metabolic consistency analysis" (REPORT.md line 110) appears justified based on the literature review.

**GapMind validation**: The 13/13 perfect concordance between GapMind pathway predictions and experimental data is a meaningful validation finding. However, this is partially circular — the metabolites that could be mapped to GapMind pathways are common amino acids and organic acids with well-characterized pathways. The result confirms GapMind works for easy cases but doesn't test its accuracy for novel or unusual pathways.

**Incomplete analysis**: The planned Notebook 4 (pathway-level analysis mapping fitness genes to specific GapMind pathway steps) was not completed. This is acknowledged in the REPORT.md limitations (line 121) and future directions (line 167). The planned statistical test for "is concordance better than random?" (RESEARCH_PLAN.md line 153) was also not performed. Both would strengthen the analysis.

**Pleiotropic genes finding**: The 231 genes with significant fitness across 3+ metabolites (NB02 cell `cell-16`) is an interesting result. The top pleiotropic genes (e.g., homoserine O-acetyltransferase, dihydroxy-acid dehydratase, ATP phosphoribosyltransferase) are all amino acid biosynthesis enzymes, which makes biological sense — they are essential for growth on any minimal medium. This could be discussed more explicitly in the report as evidence that the fitness signal largely reflects amino acid prototrophy requirements rather than substrate-specific catabolism.

**Limitations**: Well-enumerated in the REPORT.md (lines 116-121). The medium effect (R2A vs. minimal), BacDive species-level aggregation, and name matching limitations are all genuine confounders that are honestly disclosed.

## Suggestions

1. **Complete the Reproduction section** (README.md line 24): Document which notebooks require Spark, which run locally from cached data, expected runtimes, and Python dependencies. This is marked TBD but the project is listed as complete. *(Critical)*

2. **Add a requirements.txt**: At minimum list `pandas`, `numpy`, `matplotlib`, and note the Spark/`get_spark_session()` dependency with version or environment information. *(Critical)*

3. **Add a statistical baseline for concordance**: The research plan (line 153) proposed testing whether concordance is better than random. A simple permutation test (shuffle WoM-FB metabolite assignments and recompute concordance) would establish whether 94% is meaningfully higher than chance given the data structure. *(High impact)*

4. **Revisit the Cytosine→Cytidine and Uracil→Uridine mappings**: These are base-to-nucleoside mappings, not the same metabolite. Consider either flagging these as approximate matches in the crosswalk table or excluding them from concordance scoring. The current code comments note the issue but the downstream analysis treats them as matches. *(Moderate impact)*

5. **Discuss pleiotropic genes as biosynthetic auxotrophy signal**: The 231 genes significant across 3+ metabolites are predominantly amino acid biosynthesis genes (histidine, leucine, methionine pathway enzymes). This means much of the fitness signal reflects growth requirements for amino acid biosynthesis on minimal media, not substrate-specific catabolism. Distinguishing these "housekeeping fitness" genes from truly substrate-specific ones (e.g., genes specific to carnitine catabolism) would sharpen the WoM↔FB integration. *(Moderate impact)*

6. **Implement Notebook 4 or remove from the research plan**: The pathway-level analysis is described in both RESEARCH_PLAN.md (lines 157-162) and REPORT.md future directions but was not completed. Either implement it or clearly mark it as out-of-scope in the research plan. *(Nice-to-have)*

7. **Address the 7 missing FB conditions**: NB02 queried 31 FB conditions but only 24 returned data (cell `cell-4`). The 7 conditions that returned no gene-experiment records could indicate query issues or genuinely sparse fitness data. A brief note on which conditions were lost would improve transparency. *(Nice-to-have)*

8. **Consider per-strain BacDive consensus**: The current `pct_positive` calculation counts raw utilization records rather than taking one vote per strain. For D-glucose, there are 104 records from 51 strains, suggesting some strains contribute multiple records. A per-strain consensus step before computing the species-level summary would be more rigorous. *(Nice-to-have)*

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-02-25
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, 3 notebooks, 8 data files, 3 figures
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.

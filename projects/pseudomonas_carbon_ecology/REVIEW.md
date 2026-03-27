---
reviewer: BERIL Automated Review
date: 2026-03-20
project: pseudomonas_carbon_ecology
---

# Review: Carbon Source Utilization Predicts Ecology and Lifestyle in Pseudomonas

## Summary

This is a well-executed comparative genomics project that asks a clear, two-part question about *Pseudomonas* carbon utilization and delivers convincing answers. The analysis spans 12,732 genomes across 433 species clades, using GapMind pathway predictions to quantify metabolic differences between host-associated and free-living lineages. The strongest result — dramatic loss of plant-derived sugar pathways in *P. aeruginosa* (H1b) — is well-supported, biologically intuitive, and contextualized against prior literature. The ecology prediction result (H1a) is honestly reported as partially supported, with appropriate caveats about sample size and pathway resolution. Documentation is thorough: the three-file structure (README, RESEARCH_PLAN, REPORT) is well-maintained, notebooks have saved outputs, all 7 planned figures are present, and the project is reproducible from cached data. The main areas for improvement are the absence of the planned 5th notebook (synthesis), lack of phylogenetic correction, and some methodological details in the PERMANOVA-like test.

## Methodology

**Research question and hypotheses**: Clearly stated and testable. The two-part structure (H1a: ecology prediction; H1b: lifestyle-associated pathway loss) is well-motivated, and the null hypotheses are explicitly articulated in RESEARCH_PLAN.md. The literature context (6 papers in the plan, 11 in the report) provides strong justification for the gap being addressed.

**Approach**: Sound overall. The pipeline follows a logical sequence: data extraction (NB01) → environment harmonization (NB02) → subgenus-level pathway comparison (NB03) → ecology prediction with PCA/RF (NB04). The use of GTDB subgenera as a phylogenetic framework for the host-associated vs. free-living comparison is well-justified.

**Data sources**: Clearly identified in both README and RESEARCH_PLAN. The SQL queries in RESEARCH_PLAN.md match what is actually executed in NB01. The project correctly handles the known GapMind pitfall (multiple rows per genome-pathway pair requiring MAX aggregation), which is documented in `docs/pitfalls.md` under `[pangenome_pathway_geography]`.

**Reproducibility**: Good. The README includes a clear 4-step reproduction guide with the Spark/local separation documented (NB01 requires BERDL JupyterHub; NB02-04 run locally from cached CSVs). A `requirements.txt` is present with appropriate version pins. All intermediate data files are saved and listed with sizes.

**Missing notebook**: The RESEARCH_PLAN specifies 5 notebooks, but only 4 were implemented. Notebook 05 (`05_synthesis.ipynb`) was planned for "summary figure, core vs variable pathways, within-species ecotypes" but was never created. The planned figures `summary_figure.png` and `core_vs_variable_pathways.png` are absent. This leaves two of the three planned NB05 analyses (core vs variable pathways, within-species ecotypes) incomplete. These are acknowledged in the REPORT's "Future Directions" section, but the gap between the plan and execution should be more explicitly noted.

## Code Quality

**SQL queries (NB01)**: Well-constructed. The GapMind extraction query correctly uses `MAX(score_value)` grouped by `(clade_name, genome_id, pathway)` to handle multi-row pathway entries — consistent with the pitfall documented in `docs/pitfalls.md`. The isolation source query uses multiple LEFT JOINs to the EAV-format `ncbi_env` table to capture `isolation_source`, `host`, `env_broad_scale`, `env_local_scale`, and `env_medium` in a single query, which is efficient. Numeric columns from pangenome are properly CAST to INT/FLOAT, addressing the string-typed columns pitfall.

**Environment classification (NB02)**: The keyword-based classifier (cell 3) is reasonable for a first pass, with clearly defined priority ordering. The regex patterns are well-structured. One concern: the "food" pattern (`\bmilk\b|dairy|...`) includes `raw chicken`, which could overlap with the "animal" category. However, the priority ordering handles this correctly since "animal" comes before "food_dairy." The `other` category captures 29.1% of genomes — noted in the REPORT as a limitation, but some manual spot-checking of what falls into "other" would strengthen confidence.

**Statistical methods (NB03)**: Appropriate. Mann-Whitney U tests with Benjamini-Hochberg FDR correction for 62 comparisons is the right non-parametric approach given unequal group sizes (7 vs 189 species). The threshold of score >= 4 for "complete or likely_complete" is reasonable.

**PERMANOVA implementation (NB04, cell 7)**: The custom permutation test is a functional approximation of PERMANOVA, but has a notable difference from the standard PERMANOVA (Anderson 2001): it compares mean between-group to mean within-group distances (a ratio), rather than partitioning sums of squared distances into explained vs residual variance (an F-ratio). This means the test statistic is not directly comparable to published PERMANOVA results. The p-value (0.006) is likely still valid as a permutation test, but the method should be described more precisely as a "permutation test on the between/within distance ratio" rather than "PERMANOVA." Alternatively, using `skbio.stats.distance.permanova` would provide the standard implementation.

**Random Forest (NB04, cell 9)**: Appropriate use of `class_weight='balanced'` and `StratifiedKFold` to handle unbalanced classes. The minimum fold count is correctly set to `min(5, min_class_size)`, avoiding folds with empty classes. However, with only 51 species across 4 classes (and rhizosphere having only 6), the results should be interpreted cautiously — the high variance (±0.169) reflects this.

**Notebook organization**: All 4 notebooks follow the expected structure (markdown header → setup → query/load → analysis → visualization → summary). Each notebook clearly states whether it requires Spark or runs locally.

**Pitfall awareness**: The project demonstrates awareness of the key pangenome pitfalls:
- GapMind multi-row aggregation (cell 5 of NB01)
- NCBI_env EAV format (cell 8 of NB01)
- String-typed numeric columns (CAST in NB01 cell 3)

## Findings Assessment

**H1b (pathway loss)**: Strongly supported and well-documented. The finding that 43/62 pathways differ significantly between subgenera, with 7 pathways showing >50 percentage-point differences concentrated in plant-derived sugars (xylose, arabinose, myo-inositol), is compelling. The observation that amino acid catabolism remains near-universal (>99%) while plant sugars are lost aligns precisely with prior work by La Rosa et al. (2018) and Palmer et al. (2007). The nuanced observation about rhamnose/fucose being *higher* in *P. aeruginosa* — possibly related to rhamnolipid virulence factors — adds depth.

**H1a (ecology prediction)**: Honestly reported as partially supported. The significant PERMANOVA result (p=0.006) combined with modest RF accuracy (0.41 vs 0.25 chance) appropriately conveys that carbon profiles carry ecological signal but are insufficient for fine-grained prediction. The feature importance results (D-serine, arabinose, rhamnose as top discriminators) are biologically interpretable.

**Limitations**: Thoroughly acknowledged in the REPORT. Five specific limitations are listed, covering sampling bias, isolation source quality, GapMind resolution, phylogenetic confounding, and majority-vote aggregation. The phylogenetic confounding limitation (item 4) is the most significant unaddressed issue — the dominant PCA signal separates subgenera rather than lifestyles, and within-subgenus differences are subtle. The REPORT correctly identifies this but does not attempt phylogenetic correction (e.g., PGLS).

**Incomplete analysis**: The planned NB05 analyses (core vs variable pathways, within-species ecotypes) were not completed. The REPORT acknowledges these as "Future Directions" rather than explicitly noting they were planned but deferred.

**Genome count note**: The NB01 pangenome species-table sum is 12,727 while the genome table contains 12,732 rows; the 5-genome difference reflects genomes not mapped to a species in the pangenome table. All documentation now uses 12,732 (the genome-table count) as the canonical total, with the species-sum discrepancy noted in NB01.

## Suggestions

1. **Add phylogenetic correction (high impact)**: The most significant analytical gap. Within *Pseudomonas_E*, the lifestyle-associated pathway differences are subtle and may be confounded by phylogeny. Use the `phylogenetic_tree` and `phylogenetic_tree_distance_pairs` tables now available in BERDL to compute phylogenetic independent contrasts or PGLS. This would directly address Limitation 4 and strengthen H1a.

2. **Use standard PERMANOVA implementation (medium impact)**: Replace the custom permutation test (NB04 cell 7) with `skbio.stats.distance.permanova` (or `scikit-bio`). This provides a proper pseudo-F statistic and R² value that are directly interpretable and comparable to published results. The current between/within ratio test is valid but non-standard.

3. **Complete the planned NB05 synthesis (medium impact)**: The core-vs-variable pathway analysis and within-species ecotype analysis were part of the original research plan and would add substantial value. Even a simplified version examining pathway conservation patterns across the genus would strengthen the narrative.

4. **Spot-check "other" environment classification (low-medium impact)**: 29.1% of genomes (3,711) fall into the "other" category. Examining the top 50 most common `source_text` values in this category would reveal whether additional keyword rules could rescue a meaningful fraction. This could increase the statistical power of H1a.

5. ~~**Reconcile genome count discrepancy (low impact)**~~: Resolved — all documentation now uses 12,732 (genome table count). NB01 includes a note explaining the 12,727 species-sum vs 12,732 genome-table difference.

6. **Explicitly note NB05 deferral in RESEARCH_PLAN (low impact)**: Add a note to RESEARCH_PLAN.md indicating that NB05 was deferred to future work, so the plan and execution are clearly reconciled. Alternatively, update the README's reproduction steps to note that only NB01-04 are currently implemented.

7. **Consider Bray-Curtis distance for PERMANOVA (nice-to-have)**: The current test uses Euclidean distance on fraction-complete values. Bray-Curtis dissimilarity is more standard for compositional data in ecology and would be more robust to the scale of pathway completeness fractions.

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-03-20
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, references.md, requirements.txt, 4 notebooks, 7 data files, 7 figures
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.

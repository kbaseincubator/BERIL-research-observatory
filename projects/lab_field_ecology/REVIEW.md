---
reviewer: BERIL Automated Review
date: 2026-02-15
project: lab_field_ecology
---

# Review: Lab Fitness Predicts Field Ecology at Oak Ridge

## Summary

This is a well-conceived and thoroughly executed project that bridges two major ENIGMA/KBase data assets — the Fitness Browser lab fitness data and the ENIGMA CORAL field community data — to ask a genuinely interesting ecological question. The three-notebook pipeline is clean, logically organized, and all notebooks have saved outputs with text summaries, tables, and figures. The documentation follows the observatory three-file convention (README, RESEARCH_PLAN, REPORT) with commendable intellectual honesty: the central hypothesis (H1) is clearly not supported, and the report provides a nuanced, literature-grounded interpretation of why. Statistical methodology is sound, with appropriate use of Spearman correlations and BH-FDR correction for multiple testing. The main areas for improvement are a minor inconsistency between the README and REPORT regarding the number of significant genera, the relatively crude aggregate stress tolerance metric (which conflates metal and non-metal stresses), and opportunities for multivariate analysis to control for confounding geochemistry.

## Methodology

**Research question**: Clearly stated and testable. The three-tier hypothesis structure (H1: aggregate tolerance predicts abundance; H2: per-genus correlations with geochemistry; H3: community-level shifts) is well designed and allows for partial support, which is exactly what the data show.

**Approach**: The overall strategy — extract ENIGMA CORAL community + geochemistry data, match to Fitness Browser genera, correlate — is sound and appropriate for the question. The decision to use brick476 (environmental communities with 108 geochemistry overlap) instead of the originally planned brick459 (which had no environmental community overlap) is documented in the notebook and shows good data exploration and adaptation.

**Data sources**: All data sources are clearly documented in README.md with specific table names, row counts, and descriptions. The data model diagram in RESEARCH_PLAN.md is particularly helpful for understanding the join path from samples → communities → ASVs → taxonomy. Cross-project dependencies on `conservation_vs_fitness` and `fitness_effects_conservation` data are listed in the data sources table.

**Statistical methods**: Well-chosen throughout. Spearman rank correlations are appropriate for the non-normally distributed, zero-inflated abundance data. BH-FDR correction for multiple testing is correctly applied using `statsmodels.stats.multitest.multipletests` in NB03. The 10-site detection threshold for including genera in the correlation analysis is a reasonable minimum for rank-based tests.

**Reproducibility**: Strong.
- All three notebooks have saved outputs (text summaries, statistical tables, and embedded figures), so results can be inspected without re-execution.
- Four figures in `figures/` covering each major analysis stage (genus prevalence, abundance vs uranium, metal tolerance correlation, community composition).
- Seven intermediate data files in `data/` provide a complete reproducibility trail.
- A `requirements.txt` with version ranges is provided.
- The README includes a `## Reproduction` section with step-by-step commands.
- NB01 (Spark) vs NB02–NB03 (local) separation is clearly documented; downstream notebooks run from cached TSV files without Spark access.

## Code Quality

**NB01 (Extract ENIGMA)**: Well-structured Spark queries. The extraction correctly pushes filtering to the Spark layer via `createOrReplaceTempView("overlap_comms")` and a JOIN, rather than pulling all of brick476 locally. `CAST(b.count_count_unit AS LONG)` correctly handles the string-typed numeric columns documented in pitfalls.md. The `.toPandas()` calls are applied only after filtering to the 108 overlap samples, keeping data transfer manageable.

**NB02 (Genus Abundance)**: Clean aggregation pipeline. The relative abundance computation in cell 6 uses a vectorized merge-and-divide approach (`merge` with `sample_totals`, then division), which is efficient and follows the pitfalls.md guidance against row-wise apply. The 86.7% genus-level taxonomy coverage is reasonable for 16S data, and unclassified ASVs are appropriately excluded rather than lumped into an "unknown" category.

**NB03 (Fitness vs Field)**: The core analysis is well-implemented. The `reindex(..., fill_value=0)` correctly treats absence as zero abundance. The BH-FDR correction produces 5 significant genera, which the REPORT correctly describes. The community composition comparison (high vs low uranium) effectively reveals *Rhodanobacter* dominance at contaminated sites, consistent with Carlson et al. (2019).

**Pitfalls addressed**:
- Spark Connect used instead of REST API ✓
- `CAST` used for string-typed numeric columns ✓
- Consistent use of a single ASV brick table (476) ✓
- Reasonable `.toPandas()` calls only on filtered results ✓
- Uses `berdl_notebook_utils.setup_spark_session` import for CLI execution ✓

**Minor code notes**:
- NB01 cell 5: The `geochem_sample_list` variable constructs an IN clause via string interpolation. While functional, the temp view approach used for the community join would be more robust if sample names ever contained special characters.
- NB02 cell 3: The cross-project file path `../../conservation_vs_fitness/data/organism_mapping.tsv` is documented in the README data sources table but a brief comment in the notebook cell itself noting this dependency would aid standalone readability.
- NB03 cell 8: The "metal tolerance score" uses `expGroup == 'stress'` which may include non-metal stresses (oxidative, osmotic, antibiotic). A metal-specific filter would more directly test the hypothesis, as noted in the REPORT's limitations.

## Findings Assessment

**Conclusions supported by data**: Yes. The REPORT accurately reflects the notebook outputs. The per-genus correlation table in the REPORT matches NB03 cell 5 exactly. The rejection of H1 (p=0.095, n=12) and partial support for H2 (5/11 genera significant after FDR) and H3 (community composition shifts) are well-justified.

**README–REPORT inconsistency**: The README status line says "Genus abundance correlates with uranium for 6 genera (3 positive, 3 negative, p<0.05)" but the REPORT and NB03 show **5 genera significant after BH-FDR correction** (2 positive: *Herbaspirillum*, *Bacteroides*; 3 negative: *Caulobacter*, *Sphingomonas*, *Pedobacter*). The discrepancy appears to arise from the README using uncorrected p-values (which would include *Azospirillum* at p=0.042, q=0.077). The REPORT's FDR-corrected values are the correct standard; the README should be updated to match.

**Limitations acknowledged**: Thorough. Seven specific limitations are listed in REPORT.md covering taxonomic resolution, sample size, temporal mismatch, crude tolerance metric, community aggregation, statistical power, and confounders. This is commendably honest scientific reporting.

**Literature context**: Strong. Five relevant papers are cited with specific connections to findings. The Carlson et al. (2019) reference explaining *Rhodanobacter* dominance at contaminated wells, and LaSarre et al. (2020) on the unpredictability of single-organism fitness for community outcomes, are particularly well-integrated.

**Incomplete analysis**: The RESEARCH_PLAN lists "Gene-level: metal tolerance genes in core vs accessory genome" as NB03 item 4, but this analysis does not appear in the notebooks. The REPORT references a `costly_dispensable_genes` finding but attributes it to an upstream project. This scope reduction should be explicitly noted in the RESEARCH_PLAN or REPORT.

**Visualizations**: All four figures are clear and properly labeled. The community composition figure effectively highlights *Rhodanobacter*'s dominance at high-uranium sites. The scatter plots show the heavy right skew of uranium concentration, which compresses most points near the origin.

## Suggestions

1. **Fix README–REPORT inconsistency** (critical): Update the README status line from "6 genera (3 positive, 3 negative, p<0.05)" to "5 genera (2 positive, 3 negative, FDR q<0.05)" to match the REPORT and NB03 results.

2. **Use metal-specific fitness scores** (high impact): The current tolerance metric aggregates fitness across all stress conditions. Filtering to metal-related experiments (uranium, chromium, nickel, zinc) would be a more direct test of the hypothesis and could improve the H1 correlation. This is noted as a future direction but is likely achievable with the existing `fitness_stats_by_condition.tsv` data.

3. **Add multivariate controls** (high impact): The genus–uranium correlations don't control for covarying geochemistry (pH, dissolved oxygen, nitrate). A partial Spearman correlation controlling for pH, or a CCA/RDA ordination using the 48-molecule geochemistry matrix, would test whether uranium is independently driving genus abundance or is confounded with other variables.

4. **Log-transform uranium for visualization** (moderate): The uranium distribution spans 5 orders of magnitude (0.0001–188.2 µM). Log-transformed x-axes on the scatter plots would improve readability and spread the data more evenly, making correlations visually apparent.

5. **Acknowledge the dropped gene-level analysis** (moderate): The RESEARCH_PLAN lists a gene-level core/accessory genome analysis that was not performed. Add a note explaining the scope reduction or carry out the analysis.

6. **Highlight Rhodanobacter in findings** (nice-to-have): NB03 reveals *Rhodanobacter* as the 4th most abundant genus at high-uranium sites (6.29%) vs near-absence at low-uranium sites (0.21%). While not in the Fitness Browser, this finding validates Carlson et al. (2019) and could be noted in the REPORT's findings section, not just in Future Directions.

7. **Document cross-project dependencies in notebooks** (nice-to-have): Add brief markdown cells in NB02 and NB03 noting the dependency on files from `conservation_vs_fitness` and `fitness_effects_conservation` projects, with fallback instructions if those files are unavailable.

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-02-15
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, 3 notebooks, 7 data files, 4 figures, requirements.txt
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.

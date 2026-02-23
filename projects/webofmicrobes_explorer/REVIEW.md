---
reviewer: BERIL Automated Review
date: 2026-02-23
project: webofmicrobes_explorer
---

# Review: Web of Microbes Data Explorer

## Summary

This is a well-executed exploratory data characterization project that inventories the `kescience_webofmicrobes` exometabolomics collection and systematically assesses its cross-collection linking potential to the Fitness Browser, ModelSEED biochemistry, GapMind pathways, and the pangenome. The project excels in documentation quality: the three-file structure (README, RESEARCH_PLAN, REPORT) is thorough and internally consistent, with clear hypotheses, honest limitation reporting, and actionable future directions. Both notebooks are executed with saved outputs, produce reproducible intermediate data, and follow good Spark-first data access patterns. The six key findings — particularly the E/I action encoding clarification, the identification of 19 curated metabolite-condition overlaps for pseudo3_N2E3, and the 26.8% definitive ModelSEED coverage — are well-supported by the data shown. The main areas for improvement are the single-figure output (more visualizations would strengthen the narrative), the completely failed GapMind pathway mapping (0/20 amino acids matched), and the absence of the planned third notebook, though this deferral is well-documented and justified.

## Methodology

**Research question**: Clearly stated and testable. The three-part question (what does WoM contain, which organisms overlap with FB, how do metabolite profiles connect to pangenome capabilities?) is well-scoped and decomposed into two focused notebooks.

**Hypothesis**: Well-formulated with explicit H0/H1 and measurable criteria. The REPORT honestly concludes "H1 is partially supported" — a nuanced outcome that acknowledges both the real cross-links discovered and the fundamental limitation of absent consumption data.

**Data sources**: All four BERDL collections (`kescience_webofmicrobes`, `kescience_fitnessbrowser`, `kbase_msd_biochemistry`, `kbase_ke_pangenome`) are clearly identified in the README, RESEARCH_PLAN, and REPORT, with table names, estimated row counts, and filter strategies documented upfront. The query strategy table in RESEARCH_PLAN is a valuable practice.

**Approach soundness**: The overall approach is appropriate — inventory first (NB01), then cross-collection linking (NB02). The Fitness Browser organism matching uses a reasonable two-stage strategy (exact strain ID via regex extraction and normalization, then genus-level fallback for non-ENIGMA organisms). The ModelSEED matching (exact name first, formula for remainder) is methodical and results are clearly separated by confidence level.

**Reproducibility**: Someone with BERDL JupyterHub access could reproduce this analysis. The README includes a reproduction section with a clear dependency diagram (`NB01 → data/*.csv → NB02 → data/modelseed_*.csv`), notes that both notebooks require active Spark sessions, and explains why NB03 was deferred. All intermediate data files are saved as CSVs. A `requirements.txt` with version constraints (`pandas>=1.5,<3.0`, `pyspark>=3.4,<4.0`, `matplotlib>=3.5,<4.0`) is provided. Estimated runtimes are not documented but would be short given the small WoM table sizes.

## Code Quality

**SQL queries**: Correct and well-structured. NB01's organism-observation join uses appropriate LEFT JOIN with aggregation and action-count pivoting. NB02's ModelSEED matching is methodical. The pangenome genus search in NB02 uses `LIKE` patterns (e.g., `LIKE '%Pseudomonas%fluorescens%'`), which `docs/pitfalls.md` advises against for performance — but this is acceptable for these small exploratory queries against the pangenome summary table.

**Metabolite-condition matching (NB02, cell `fb-wom-metabolite-conditions`)**: Uses a well-curated dictionary mapping (`curated_map`) that maps WoM metabolite names to their specific FB condition variants (e.g., "alanine" → ["L-Alanine", "D-Alanine"]). This produces 19 high-confidence matches with clear biological relevance. This is a strength — the curated approach avoids the false-positive inflation that naive substring matching would produce.

**Notebook organization**: Both notebooks follow a clean setup → query → analysis → save structure with numbered markdown section headers. NB01 includes a summary cell at the end recapping key counts. Code is readable with inline comments explaining non-obvious logic (e.g., the `categorize_organism` function, the `classify_metabolite` function). One minor issue: NB01 section numbering jumps from "## 7" to "## 9. Save Outputs," with the heatmap section labeled "## 8" appearing after section 9 in the cell order — apparently the heatmap cell was inserted after the save cell.

**Pitfall awareness**: The RESEARCH_PLAN explicitly notes "FB columns are all strings (CAST needed)" and "GapMind requires MAX aggregation per genome-pathway pair" from `docs/pitfalls.md`. The first is not exercised in the analysis (no numeric comparisons on FB columns), and the second becomes moot because GapMind matching failed at the name-lookup stage before aggregation was needed. The `CAST(no_genomes AS INT)` in NB02's pangenome query correctly handles the string-typed numeric columns. No `.toPandas()` calls are made on large tables — all heavy filtering happens in Spark SQL first, consistent with pitfall guidance about unnecessary `.toPandas()` calls.

**GapMind matching failure (NB02, cells `gapmind-pathways` and `gapmind-carbon`)**: The approach of searching GapMind pathway names for substring matches with amino acid names (e.g., looking for "L-arginine" in pathway names) yields 0/20 matches. This is because GapMind pathway IDs in the `kbase_ke_pangenome.gapmind_pathways` table use internal identifiers that don't contain simple metabolite substrings. The notebook correctly identifies this as a blocking issue ("Needs a pathway-to-metabolite lookup table"), but the approach could have been validated earlier by inspecting sample pathway names before writing the full matching loop. The cell output clearly shows the failure, which is honest reporting.

**Minor code issues**:
- NB01 cell `organisms-detail`: The `display()` call on a string (from `.to_string()`) wraps the output in quotes, producing repr-style output. Using `print()` would be cleaner.
- NB02 cell `integration-test`: This cell describes what *could* be done with the cross-collection links but doesn't execute any actual integration query. It serves as a narrative summary, which is useful documentation, but the section title "Integration test" implies computation that doesn't occur.

## Findings Assessment

**Finding 1 (Action encoding)**: Well-supported. The observation data clearly shows 0 'D' actions for any organism (all 742 'D' belong to the control), and mutual exclusivity of 'E' and 'I'. The biological distinction between "emerged" (de novo production) and "increased" (amplification of existing) is genuinely useful and not prominently documented in the original Kosina et al. (2018) paper. This is the project's most novel contribution.

**Finding 2 (FB matches)**: Accurate. Two direct strain matches (pseudo3_N2E3, pseudo13_GW456_L13) confirmed by strain ID normalization, plus E. coli BW25113/Keio (same strain, thin WoM data) and Synechococcus PCC7002/SynE (genus-level only, different strain). The match table in the REPORT correctly distinguishes "Direct strain" from "Same strain" and "Genus only" match types.

**Finding 3 (19 metabolite-condition overlaps)**: The curated table of 19 matches is biologically meaningful and well-presented. The mix of de novo products (E: lactate, valine, lysine, thymine, carnitine) and amplified metabolites (I: amino acids, nucleotides) is clearly shown. The connection to specific FB experimental conditions (carbon source vs nitrogen source) is actionable for future work.

**Finding 4 (ModelSEED matching — 26.8% name, 68.5% total)**: Solid and clearly presented. The REPORT appropriately distinguishes high-confidence name matches (69 compounds, 1:1 mapping) from ambiguous formula-only matches (107 compounds → 900 ModelSEED molecules, ~8.4:1 expansion). The 31.5% unmatched rate is honestly reported. The REPORT could benefit from explicitly noting that formula matches are candidate sets rather than definitive identifications — this nuance is present but could be more prominent.

**Finding 5 (Metabolic novelty rates)**: An interesting and creative metric. The E/(E+I) ratio varying from 15.2% (Bacillus FW507-8R2A) to 32.4% (Pseudomonas GW456-L13) across ENIGMA isolates in R2A medium is a novel phenotypic characterization. No statistical tests are applied (appropriate given n=10 organisms and single-environment data), and no overinterpretation is attempted.

**Finding 6 (Pangenome coverage)**: Confirmed at genus level for all WoM organisms. The caveat that species-level matching requires strain-to-genome mapping (not attempted) is appropriate.

**Limitations**: Thoroughly and honestly documented. The five limitations in the REPORT are specific and actionable: (1) no consumption data, (2) small organism set, (3) 2018 frozen snapshot, (4) GapMind naming mismatch, (5) minimal E. coli WoM data. The pointer to de Raad et al. (2022) NLDM dataset for newer data is valuable context.

**NB03 deferral**: The RESEARCH_PLAN described 3 notebooks, with NB03 marked "if warranted." The README explicitly documents the deferral with a clear justification: "The absence of consumption data in this 2018 WoM snapshot made organism-comparison heatmaps less informative than planned." This is honest and well-handled.

## Suggestions

1. **[Moderate] Add more visualizations**: The project has a single figure (the ENIGMA metabolite heatmap, which is effective). Additional figures would strengthen the narrative: (a) a bar chart of metabolite categories (amino acids, nucleotides, etc.) showing the category breakdown from NB01; (b) a Venn or UpSet diagram showing cross-collection overlap (how many organisms/metabolites are in WoM only, WoM+FB, WoM+ModelSEED, etc.); (c) a scatter plot of emerged-vs-increased counts per organism showing the metabolic novelty rate variation. The REPORT references these findings textually but visualizations would make them more immediately accessible.

2. **[Moderate] Investigate GapMind pathway naming before writing full matching loop**: The 0/20 failure in NB02 could have been caught earlier by inspecting a few sample pathway names (e.g., `SELECT DISTINCT pathway FROM kbase_ke_pangenome.gapmind_pathways LIMIT 10`). The notebook does show this query but the matching code was written before understanding the naming convention. A brief note in the notebook explaining *what* the pathway names look like and *why* simple substring matching fails (they use internal pathway IDs like compound utilization pathway names, not "L-arginine biosynthesis") would help future researchers avoid the same dead end.

3. **[Moderate] Add estimated runtimes to reproduction section**: Both notebooks appear to run quickly (WoM tables are tiny, and the cross-collection queries are well-filtered), but documenting approximate runtimes (e.g., "NB01: ~2 minutes, NB02: ~3 minutes") would help prospective reproducers plan their sessions.

4. **[Minor] Fix NB01 section numbering**: The heatmap section (labeled "## 8") appears after the save section (labeled "## 9. Save Outputs") in the cell order. Either reorder the cells or renumber the sections for sequential flow.

5. **[Minor] Consider adding seaborn or scipy to requirements.txt**: If additional visualizations are added per suggestion 1, `seaborn` and/or `scipy` would likely be needed and should be pinned in `requirements.txt`. Currently only `pandas`, `pyspark`, and `matplotlib` are listed, which is correct for the current code.

6. **[Minor] Expand the E. coli / Keio analysis**: The REPORT notes that E. coli BW25113 has only 12 WoM observations (sulfur/cysteine focus), making it a weak cross-link. NB02 could briefly quantify this — how many E. coli metabolites overlap with Keio FB conditions? Even a negative result ("only 1-2 overlaps due to sulfur-only focus") would strengthen the claim that the Pseudomonas matches are the primary integration opportunity.

7. **[Nice-to-have] Explore GapMind pathway names more deeply**: The `gapmind_pathways.pathway` column contains 80 distinct pathway names. Printing all 80 in the notebook (rather than just the LIMIT 200 query) and categorizing them by type (amino acid utilization, carbon source utilization, etc.) could reveal which pathways *are* matchable to WoM metabolites, even if the simple substring approach failed. Some GapMind pathways may use metabolite names in non-obvious formats (e.g., "D-glucose utilization" rather than just "glucose").

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-02-23
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, references.md, requirements.txt, 2 notebooks, 7 data files, 1 figure
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.

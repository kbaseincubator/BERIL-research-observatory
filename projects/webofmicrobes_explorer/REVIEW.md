---
reviewer: BERIL Automated Review
date: 2026-02-23
project: webofmicrobes_explorer
---

# Review: Web of Microbes Data Explorer

## Summary

This is a well-structured exploratory data characterization project that inventories the `kescience_webofmicrobes` exometabolomics collection and systematically assesses its cross-collection linking potential to the Fitness Browser, ModelSEED biochemistry, GapMind pathways, and the pangenome. The documentation is exemplary — the three-file structure (README, RESEARCH_PLAN, REPORT) is thorough and internally consistent, with clear hypotheses, honest limitation reporting, and useful future directions. Both notebooks are executed with saved outputs and produce reproducible intermediate data files. The key findings (the E/I action encoding clarification, the absence of consumption data, 68.5% ModelSEED coverage, and the identification of 2-3 actionable FB organism matches) are well-supported by the data shown. The main gaps are the empty `figures/` directory, the omission of the planned third notebook, and a noisy metabolite-condition matching approach that inflates overlap counts in NB02.

## Methodology

**Research question**: Clearly stated and testable. The three-part question (what does WoM contain, which organisms overlap with FB, how do metabolite profiles connect to pangenome capabilities?) is broken into well-scoped sub-analyses across two notebooks.

**Hypothesis**: Well-formulated with explicit H0/H1 and measurable criteria. The REPORT honestly concludes "H1 is partially supported" — a nuanced outcome that acknowledges both the real cross-links and the fundamental limitation (no consumption data).

**Data sources**: All four BERDL collections are clearly identified in both the README and RESEARCH_PLAN, with table names, estimated row counts, and filter strategies documented upfront. The query strategy table in RESEARCH_PLAN is a good practice.

**Approach soundness**: The overall approach is appropriate — inventory first (NB01), then cross-collection linking (NB02). The Fitness Browser organism matching uses a reasonable two-stage strategy (exact strain ID match, then genus-level fallback). The ModelSEED matching (exact name + formula) is sound and clearly reported.

**Reproducibility**: Someone with BERDL JupyterHub access could reproduce this analysis. All intermediate data files are saved as CSVs, and NB02 reads from NB01 outputs. However, the reproduction section in the README could note that NB02 also requires an active Spark session (not just cached data from NB01) since it runs its own Spark queries against FB, ModelSEED, and pangenome tables.

## Code Quality

**SQL queries**: Correct and well-structured. NB01's organism categorization query uses a clean LEFT JOIN from organism to observation with appropriate aggregation. NB02's ModelSEED matching is methodical (exact name first, then formula for unmatched). The pangenome genus search in NB02 uses `LIKE` patterns (e.g., `LIKE '%Pseudomonas%fluorescens%'`), which docs/pitfalls.md advises against for performance — but this is acceptable here since these are small exploratory queries, not production joins.

**Metabolite-condition matching is noisy (NB02, cell `fb-wom-metabolite-conditions`)**: The substring-based fuzzy matching between WoM metabolite names and FB condition names produces many false positives. For example, "maleic acid" matches "parabanic acid", "benzoic acid", "fusidic acid", etc. because the token "acid" (length > 3) appears in both. The reported "109 potential overlaps" is substantially inflated — the true meaningful overlaps are closer to 10-15 (the curated list in the REPORT's Finding #3 table). The notebook should flag this false-positive rate explicitly, rather than presenting 109 as the headline number.

**Notebook organization**: Both notebooks follow a clean setup-query-analysis-save structure with numbered markdown section headers. The NB01 summary cell at the end is a nice touch. Code is readable with inline comments explaining non-obvious logic (e.g., the organism categorization function).

**Pitfall awareness**: The RESEARCH_PLAN explicitly notes "FB columns are all strings (CAST needed)" and "GapMind requires MAX aggregation per genome-pathway pair." The first isn't exercised in the actual analysis (no numeric comparisons on FB columns), and the second isn't implemented because GapMind matching failed at the name-lookup stage. No `.toPandas()` calls are made on large tables — all heavy filtering happens in Spark SQL first, consistent with pitfall guidance.

**Minor issues**:
- NB01 cell `organisms-detail`: The `display()` call wraps the string output in quotes, producing a repr-style output rather than a clean table. Using `print()` would be cleaner.
- NB02 cell `integration-test`: The integration test for pseudo3_N2E3 produces no amino acid pathway connections (because `aa_pathway_map` is empty after 0/20 GapMind matches). The cell prints the header "Integration test" but the result is just a count of produced metabolites with no actual integration. This section could be removed or replaced with a note explaining why the integration is blocked.

## Findings Assessment

**Finding 1 (Action encoding)**: Well-supported. The observation table clearly shows 0 'D' actions for any organism and mutual exclusivity of 'E' and 'I'. The distinction between "emerged" (de novo) and "increased" (amplification) is genuinely useful and not prominently documented elsewhere.

**Finding 2 (FB matches)**: Accurate. Two direct strain matches confirmed by strain ID normalization, plus the Keio and Synechococcus genus-level matches.

**Finding 3 (Metabolite-FB condition overlap)**: The curated table of ~10 key overlaps (alanine, arginine, glycine, lactate, etc.) in the REPORT is well-chosen and biologically meaningful. However, the "109 overlaps" headline number from NB02 is misleading as discussed above. The REPORT should either clarify that 109 is the raw substring-match count (with high false-positive rate) or report only the curated count.

**Finding 4 (ModelSEED matching)**: Solid. The 68.5% match rate is clearly broken down by match type. One note: formula-only matches (107 compounds mapping to 900 ModelSEED molecules) have inherent ambiguity — the same molecular formula can correspond to many different molecules. The REPORT mentions "at least one ModelSEED molecule link" but doesn't discuss the 1:8.4 average expansion ratio for formula matches, which substantially reduces the precision of these links.

**Finding 5 (Metabolic novelty rates)**: Interesting metric. The E/(E+I) ratio is a creative use of the action encoding discovery. The 2-fold variation across ENIGMA isolates is noted but not statistically tested (small sample, no confidence intervals). This is acknowledged implicitly.

**Finding 6 (Pangenome coverage)**: Confirmed at genus level. The caveat that species-level matching was not attempted is appropriate.

**Limitations**: Thoroughly documented. The five limitations in the REPORT are honest and specific. The note about the 2018 frozen snapshot and the pointer to de Raad et al. (2022) for newer data is particularly useful.

**Incomplete analysis**: The RESEARCH_PLAN described 3 notebooks, but NB03 (Metabolite Interaction Profiles — heatmaps, organism comparisons) was not created. This is partially acknowledged by the "if warranted" qualifier in the plan, but the README's reproduction diagram still references `figures/` outputs that don't exist. The `figures/` directory is empty.

## Suggestions

1. **[Critical] Fix the 109-overlap inflation in NB02 and REPORT**: The substring matching approach generates many false positives (e.g., "acid" matching unrelated compounds). Either (a) tighten the matching to require the full metabolite name rather than any 4+ character token, or (b) add a manual curation step in the notebook and report the curated count. The REPORT's Finding #3 table is well-curated — use that count (~10-15) as the headline, not 109.

2. **[Important] Add at least one summary visualization**: The `figures/` directory is empty. Even without NB03, a single heatmap (organism x metabolite action for the 10 ENIGMA isolates in R2A medium, which is a compact 10 x 105 matrix) or a Venn/UpSet diagram showing cross-collection overlap would significantly strengthen the project. This is the most visible gap.

3. **[Important] Discuss formula-match ambiguity for ModelSEED**: Note that 107 formula-only matches expand to 900 ModelSEED molecules (8.4:1 ratio). This means a formula match provides a candidate set, not a definitive identification. The 68.5% "total matched" headline should be qualified: 26.8% are high-confidence (exact name), while 41.6% are ambiguous (formula-only).

4. **[Moderate] Update README reproduction section**: Note that NB02 requires its own Spark session (not just cached CSVs from NB01). Add estimated runtimes (both notebooks appear fast given the small WoM table sizes). Remove the reference to `figures/` in the reproduction diagram since no figures are generated.

5. **[Moderate] Remove or rework the empty integration test in NB02**: Cell `integration-test` produces no meaningful output because GapMind matching failed (0/20). Either remove this cell or replace it with a note explaining why the WoM-GapMind-FB integration path is blocked and what would be needed to unblock it.

6. **[Minor] Pin dependency versions in requirements.txt**: `pandas` and `pyspark` without version numbers may lead to compatibility issues. Add version constraints (e.g., `pandas>=1.5,<3.0`).

7. **[Minor] Consider documenting the NB03 decision**: Either add a brief note to the README/REPORT explaining why NB03 was deferred ("the absence of consumption data made organism-comparison heatmaps less informative than planned") or remove NB03 from the RESEARCH_PLAN. Currently the plan promises 3 notebooks and delivers 2 without comment.

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-02-23
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, references.md, requirements.txt, 2 notebooks, 7 data files, 0 figures
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.

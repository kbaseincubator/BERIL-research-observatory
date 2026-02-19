---
reviewer: BERIL Automated Review
date: 2026-02-19
project: respiratory_chain_wiring
---

# Review: Condition-Specific Respiratory Chain Wiring in ADP1

## Summary

This is a well-structured and scientifically compelling project that systematically maps the condition-dependent respiratory chain wiring in *Acinetobacter baylyi* ADP1 across 8 carbon sources. The central finding — that Complex I's quinate-specificity is explained by NADH flux *rate* rather than total yield — is a genuinely insightful resolution of an apparent paradox. The project follows the observatory's three-file documentation pattern (README, RESEARCH_PLAN, REPORT) cleanly, all four notebooks have saved outputs with figures, and the reproduction guide is clear. The main weaknesses are: (1) the stoichiometry analysis (NB03) is based on manually entered textbook biochemistry rather than computed from the FBA model, making the "rate vs yield" argument qualitative rather than quantitative; (2) the NDH-2 gene identification in the cross-species analysis (NB04) likely has false positives from poorly annotated Complex I subunits, which could affect the compensation test; and (3) one planned analysis (pangenome NDH-2/Complex I co-occurrence via BERDL) was dropped without documentation. Despite these issues, the project presents a coherent biological story supported by multiple lines of evidence and is transparent about its limitations.

## Methodology

**Research question**: Clearly stated, specific, and testable: "which NADH dehydrogenases and terminal oxidases are required for which substrates?" The dual hypothesis (H0 vs H1) in the RESEARCH_PLAN is well-formulated and makes distinct predictions.

**Approach**: The four-notebook structure maps cleanly to the four aims in the RESEARCH_PLAN:
- NB01: Respiratory chain inventory and condition map (Aim 1)
- NB02: NDH-2 indirect characterization (Aim 2)
- NB03: NADH stoichiometry (Aim 3)
- NB04: Cross-species validation (Aim 4)

**Data sources**: Clearly identified in both README and REPORT. The SQLite database (`berdl_tables.db`) is specified with size (136 MB). BERDL Spark is used only for NB04, with clear Spark/local separation documented in the reproduction guide.

**Reproducibility**:
- **Notebook outputs**: All four notebooks have saved outputs including text, tables, and figures. This is excellent — a reader can follow the analysis without re-executing.
- **Figures**: 7 figures in `figures/`, covering exploration (heatmap, clustermap), results (wiring model, wiring matrix, NADH stoichiometry), and cross-species validation (NDH-2 vs Complex I scatter). Good coverage.
- **Dependencies**: `requirements.txt` is present with 5 packages (pandas, numpy, matplotlib, seaborn, scipy). NB01 also uses `sklearn.preprocessing.StandardScaler` which is not listed — `scikit-learn` should be added to requirements.
- **Reproduction guide**: README includes a clear `## Reproduction` section with prerequisites, `pip install`, and `jupyter nbconvert` commands for each notebook. Spark/local separation is explicitly documented.
- **Missing planned analysis**: The RESEARCH_PLAN (Aim 2) specified querying `kbase_ke_pangenome.eggnog_mapper_annotations` for NDH-2/Complex I KO co-occurrence across Acinetobacter species, and the README lists `kbase_ke_pangenome` as a data source. This analysis was not performed. NB02 relies only on the local SQLite `pangenome_is_core` flag, which is much less informative than a cross-species KO co-occurrence analysis. The omission should be documented (either as a limitation or future work).

## Code Quality

**SQL queries**: Queries in NB01-03 against SQLite are straightforward and correct. NB04 Spark queries correctly use `CAST(fit AS FLOAT)` for the fitness browser's all-string columns, following the pitfall documented in `docs/pitfalls.md`. The `orgId` filter is applied before querying `genefitness`, respecting the performance guidance.

**Gene classification (NB01, cell 4)**: The `classify_respiratory()` function uses a reasonable combination of RAST function keywords and KO identifiers. However, the "Other respiratory" category (20 genes) includes several non-respiratory enzymes that inflate the respiratory chain inventory:
- ACIAD3447: "Transcriptional regulator GabR of GABA utilization" — a transcription factor, not a respiratory component
- ACIAD3295: "Modulator of drug activity B" — a drug resistance gene
- ACIAD2549/2551: Sarcosine oxidase subunits — amino acid catabolism, not core respiratory chain
- ACIAD1909/1910: Nitrite reductase — nitrogen metabolism

These were captured by the broad `LIKE '%NADH%oxidoreductase%'` or similar patterns. While they don't affect the core findings (the subsystem profiles for Complex I, Cyt bo3, etc. are correct), the reported "62 respiratory chain genes" is inflated. Consider tightening the search or renaming "Other respiratory" to "Other redox enzymes."

**NDH-2 identification in NB04 (cell 5)**: This is the most significant code quality concern. The NDH-2 search finds genes with descriptions matching `'%nadh dehydrogenase%'` while excluding those containing "subunit", "chain", or "ubiquinone." However, several organisms show suspiciously many hits:
- `pseudo3_N2E3`: 8 hits (AO353_27745–AO353_27780) — consecutive locus tags suggesting an operon, almost certainly Complex I subunits with incomplete annotations
- `pseudo5_N2C3_1`: 8 hits (AO356_22030–AO356_22065) — same pattern
- `Miya`: 6 hits — likely a mix of true NDH-2 and misannotated Complex I

True NDH-2 is a single-subunit enzyme, so any organism showing 6-8 "NDH-2" hits likely has Complex I subunits leaking through the filter. This misclassification inflates the "organisms with NDH-2" count (reported as 10/14) and could bias the compensation test. A stricter approach would be to filter by KO annotation (K03885 for NDH-2) rather than text matching, or to exclude organisms with >2 NDH-2 hits.

**Stoichiometry analysis (NB03)**: The NADH yields are manually entered as a `pd.DataFrame` literal (cell 3) based on textbook biochemistry, not computed from the FBA model's reaction network. While the FBA reaction data *is* queried (cell 6, 1,421 NADH reactions), it's used only descriptively — the actual stoichiometry comparison uses the hardcoded values. This is acknowledged in the REPORT ("uses theoretical pathway biochemistry, not measured flux distributions") but the notebook itself doesn't make the distinction prominent. The manually entered values appear biochemically reasonable but are not independently validated against the model.

**Statistical methods**: The Mann-Whitney U test in NB04 (cell 9) is appropriate for comparing two small groups with non-normal distributions. The test correctly uses `alternative='two-sided'`. The result (p=0.24) is honestly reported as non-significant.

**Notebook organization**: All four notebooks follow a clean structure: markdown header with goal/inputs/outputs, setup cell, numbered sections, and summary cell. Data is saved to `data/` and figures to `figures/` at the end. The NB02 explicitly closes the database connection. Good practice throughout.

**Pitfall awareness**: The project correctly handles the Fitness Browser all-string column pitfall (`CAST AS FLOAT`), uses `orgId` filters on `genefitness`, and separates Spark-dependent (NB04) from local notebooks (NB01-03). The `get_spark_session()` call in NB04 uses the correct JupyterHub pattern (no import). No issues with the pitfalls documented in `docs/pitfalls.md`.

## Findings Assessment

**Condition-specific respiratory wiring (Finding 1)**: Well-supported by the data in NB01. The heatmap and subsystem profiles clearly show distinct respiratory configurations per carbon source. The wiring summary (cell 15) correctly identifies which subsystems are required vs dispensable per condition. The 0.6 threshold for "essential" is reasonable given the growth ratio scale, though somewhat arbitrary — the choice is not discussed.

**NDH-2 compensation model (Finding 2)**: This is the weakest finding because NDH-2 has no growth data, so the central prediction (NDH-2 compensates on glucose) cannot be tested. The indirect evidence is presented honestly: FBA routing, genomic context, pangenome conservation status, and ortholog-transferred fitness. The REPORT correctly lists this as the primary limitation. The ortholog-transferred fitness data (30 conditions, mean fitness -0.136) shows mild NDH-2 defects across conditions, but notably has *no aromatic conditions* — this is mentioned in passing but deserves emphasis as it limits the ability to test the aromatic-specific hypothesis.

**Rate vs yield resolution (Finding 3)**: This is the project's most novel contribution, but it rests on qualitative reasoning rather than quantitative evidence. The argument is: quinate produces fewer NADH (4) than glucose (9) but Complex I is more essential on quinate; therefore, the explanation must be NADH flux *rate* (concentrated TCA burst from ring cleavage) rather than total yield. This logic is sound and the biochemical reasoning is plausible, but:
- There is no measurement or estimate of actual NADH production *rates*
- The FBA model, which could provide flux rate estimates, predicts zero flux through NDH-2 on all conditions, so it cannot distinguish the two scenarios
- The "concentrated TCA burst" is a qualitative assertion about pathway topology, not a computed flux distribution

The REPORT acknowledges this ("uses theoretical pathway biochemistry, not measured flux distributions"), and the Future Directions section appropriately suggests measuring NADH/NAD+ ratios experimentally.

**Cross-species NDH-2 compensation (Finding 4)**: The direction supports the hypothesis (organisms with NDH-2 show smaller Complex I aromatic deficits), but the result is not statistically significant (p=0.24). The sample is small (n=4 without NDH-2). The *P. putida* outlier (large Complex I deficit despite having NDH-2) is noted and plausibly explained, which is good scientific practice. However, the NDH-2 identification concern noted above (likely false positives for pseudo3/pseudo5/Miya) means some organisms classified as "has NDH-2" may actually lack it, which would weaken the compensation signal further.

**Limitations**: Well acknowledged. Five specific limitations are listed in the REPORT, covering the most important caveats (no NDH-2 growth data, theoretical stoichiometry, small cross-species sample, annotation variability, ACIAD3522 function uncertainty). The Future Directions section is excellent — five concrete, testable follow-up experiments.

## Suggestions

1. **[Critical] Fix NDH-2 false positives in NB04**: Organisms like `pseudo3_N2E3` (8 hits) and `pseudo5_N2C3_1` (8 hits) almost certainly have Complex I subunits leaking through the NDH-2 filter. Either use KO-based identification (K03885), apply a maximum hit count filter (true NDH-2 should have 1-2 genes per organism), or manually curate the hits. Re-run the compensation analysis after fixing — the current "10/14 have NDH-2" count is likely inflated.

2. **[Important] Add `scikit-learn` to `requirements.txt`**: NB01 cell 1 imports `from sklearn.preprocessing import StandardScaler`, but `scikit-learn` is not in the requirements file.

3. **[Important] Document the dropped pangenome analysis**: The RESEARCH_PLAN (Aim 2) lists `kbase_ke_pangenome` for NDH-2/Complex I KO co-occurrence analysis, and the README lists it as a data source. This was not performed. Either add it as a noted limitation/future work item in the REPORT, or remove the BERDL pangenome reference from the README's data sources to avoid implying it was used.

4. **[Moderate] Tighten the "Other respiratory" category in NB01**: The current broad keyword search captures non-respiratory enzymes (transcription factors, drug resistance genes, amino acid catabolism enzymes). Consider either tightening the SQL search patterns or renaming the category to "Other redox/NADH-related" to more accurately describe what's included. The headline "62 respiratory chain genes" is somewhat misleading.

5. **[Moderate] Strengthen the rate vs yield argument with FBA flux data**: NB03 queries 1,421 NADH reactions from the FBA model but only uses them descriptively. The model's per-condition flux predictions (available in `gene_phenotypes`) could provide substrate-specific NADH production flux estimates that would give quantitative support to the "concentrated TCA burst" hypothesis, even if the model doesn't distinguish Complex I from NDH-2 routing.

6. **[Minor] Clarify the 0.6 growth ratio threshold**: NB01 cell 15 uses `mean_growth < 0.6` to classify a subsystem as "essential" for a condition. This threshold is not justified or discussed. Consider mentioning the rationale (e.g., corresponds to ~40% growth reduction, or based on the distribution of growth ratios across all genes).

7. **[Minor] Add the nuoA Complex I FBA discrepancy note**: NB02 cell 3 shows nuoA (ACIAD0730) has `reactions: None` and `flux: None` in the FBA model, yet the narrative states "FBA routes all NADH through Complex I." Cell 4 confirms this by noting NDH-2 has near-zero flux while rxn10122 (the NADH:ubiquinone oxidoreductase reaction) carries all the flux. It would be clearer to note that Complex I flux is tracked at the reaction level (rxn10122), not the gene level, to explain the apparent discrepancy.

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-02-19
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, 4 notebooks, 6 data files, 7 figures
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.

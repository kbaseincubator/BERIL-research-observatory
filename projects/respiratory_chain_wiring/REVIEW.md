---
reviewer: BERIL Automated Review
date: 2026-02-19
project: respiratory_chain_wiring
---

# Review: Condition-Specific Respiratory Chain Wiring in ADP1

## Summary

This project systematically maps the condition-dependent respiratory chain wiring in *Acinetobacter baylyi* ADP1 across 8 carbon sources, producing the insight that Complex I's quinate-specificity is explained by NADH flux *rate* (concentrated TCA burst from aromatic ring cleavage) rather than total NADH yield. The project is well-structured: it follows the three-file documentation pattern (README, RESEARCH_PLAN, REPORT) cleanly, all four notebooks have saved outputs with figures, the reproduction guide is clear, and `requirements.txt` is complete. The REPORT is notably transparent about limitations, including the NDH-2 data gap, the text-based gene identification issue in cross-species analysis, and the dropped pangenome co-occurrence analysis. The main weaknesses are: (1) the stoichiometry analysis (NB03) rests on manually entered textbook biochemistry rather than computed FBA model fluxes, making the central "rate vs yield" argument qualitative rather than quantitative; (2) the NDH-2 identification in NB04 likely has false positives from misannotated Complex I subunits, which inflates the "organisms with NDH-2" count and could bias the compensation test; and (3) the "Other respiratory" category in NB01 includes several non-respiratory enzymes that inflate the headline count. Despite these issues, the project presents a coherent biological story supported by multiple independent lines of evidence and is honest about what it can and cannot conclude.

## Methodology

**Research question**: Clearly stated, specific, and testable: "which NADH dehydrogenases and terminal oxidases are required for which substrates?" The dual hypothesis (H0 vs H1) in the RESEARCH_PLAN is well-formulated and makes distinct, falsifiable predictions.

**Approach**: The four-notebook structure maps cleanly to the four aims in the RESEARCH_PLAN:
- NB01: Respiratory chain inventory and condition map (Aim 1)
- NB02: NDH-2 indirect characterization (Aim 2)
- NB03: NADH stoichiometry (Aim 3)
- NB04: Cross-species validation (Aim 4)

Each notebook has a clear header stating goal, inputs, and outputs. The logical progression (inventory → characterization → stoichiometry → cross-species) builds the argument incrementally.

**Data sources**: Clearly identified in both README and REPORT. The SQLite database (`berdl_tables.db`) is specified with size (136 MB). BERDL Spark is used only for NB04, with clear Spark/local separation documented in the reproduction guide. One minor issue: the README's Data Sources section still lists `kbase_ke_pangenome` for "NDH-2/Complex I co-occurrence," but this analysis was not performed. The REPORT correctly notes this omission in its Limitations and Future Directions sections, but the README implies the pangenome data was used.

**Reproducibility**:
- **Notebook outputs**: All four notebooks have saved outputs including text tables, printed summaries, and figures. A reader can follow the entire analysis without re-executing. This is excellent.
- **Figures**: 7 figures in `figures/`, covering exploration (heatmap, clustermap), results (wiring model, wiring matrix, NADH stoichiometry), and cross-species validation (NDH-2 vs Complex I scatter). Good coverage across all analysis stages.
- **Dependencies**: `requirements.txt` lists 6 packages (pandas, numpy, matplotlib, seaborn, scipy, scikit-learn) with version constraints. Complete for NB01–03. NB04 additionally requires a Spark session, which is documented.
- **Reproduction guide**: README includes a clear `## Reproduction` section with prerequisites (Python, SQLite database, BERDL Spark for NB04), `pip install` command, and individual `jupyter nbconvert --execute` commands for each notebook. Spark/local separation is explicitly documented.
- **Dropped analysis**: The RESEARCH_PLAN Aim 2 specified querying `kbase_ke_pangenome.eggnog_mapper_annotations` for NDH-2/Complex I KO co-occurrence across Acinetobacter species. This was not performed. NB02 instead relies on the local SQLite `pangenome_is_core` flag, which confirms NDH-2 is core but doesn't provide the cross-species co-occurrence pattern. The REPORT documents this as a limitation and lists the full pangenome analysis as Future Direction #3.

## Code Quality

**SQL queries**: Queries in NB01–03 against SQLite are straightforward and correct. NB04 Spark queries correctly use `CAST(fit AS FLOAT)` for the fitness browser's all-string columns, following the pitfall documented in `docs/pitfalls.md`. The `orgId` filter is applied before querying `genefitness`, respecting the performance guidance for the 27M-row table. No issues with the known pitfalls.

**Gene classification (NB01, cell 4)**: The `classify_respiratory()` function uses a reasonable combination of RAST function keywords and KO identifiers. However, the "Other respiratory" category (20 genes) includes several enzymes that are not part of the respiratory electron transport chain:
- ACIAD3447: "Transcriptional regulator GabR of GABA utilization" — a transcription factor
- ACIAD3295: "Modulator of drug activity B" — a drug resistance gene
- ACIAD2549/2551: Sarcosine oxidase subunits — amino acid catabolism
- ACIAD1909/1910: Nitrite reductase — nitrogen metabolism
- ACIAD0709, ACIAD2725, ACIAD3496: NADH-flavin oxidoreductases — general redox enzymes

These were captured by broad `LIKE '%NADH%oxidoreductase%'` or similar patterns in cell 3. While they don't affect the core subsystem profiles (Complex I, Cyt bo3, etc. are correctly classified), the headline "62 respiratory chain genes" is inflated. Of the 20 "Other respiratory" genes, perhaps 5–8 are genuinely respiratory (electron transfer flavoprotein, transhydrogenases, malate:quinone oxidoreductase). The remainder are redox enzymes with other metabolic roles.

**NDH-2 identification in NB04 (cell 5)**: This is the most significant code quality concern. The text-based NDH-2 search matches genes with descriptions containing "nadh dehydrogenase" while excluding "subunit", "chain", and "ubiquinone." Several organisms show suspiciously many hits:
- `pseudo3_N2E3`: 8 hits (AO353_27745–AO353_27780) — consecutive locus tags suggesting an operon, almost certainly Complex I subunits with incomplete annotations
- `pseudo5_N2C3_1`: 8 hits (AO356_22030–AO356_22065) — same pattern
- `Miya`: 6 hits — likely a mix of true NDH-2 and misannotated Complex I
- `Cup4G11`: 4 hits (3 with close locus tags RR42_RS05520–RS05540) — possibly Complex I leakage

True NDH-2 is a single-subunit enzyme, so any organism showing >2 "NDH-2" hits likely has Complex I subunits leaking through the filter. This misclassification inflates the "organisms with NDH-2" count (reported as 10/14) and could bias the compensation test. If pseudo3, pseudo5, and Miya are reclassified as lacking NDH-2, the group sizes shift from 10/4 to 7/7, and the mean deficit difference shrinks substantially. The REPORT acknowledges this limitation explicitly (noting pseudo3_N2E3 as likely false positive), which is good scientific practice, but the analysis was not corrected.

**Stoichiometry analysis (NB03, cell 3)**: The NADH yields are manually entered as a `pd.DataFrame` literal based on textbook biochemistry, not computed from the FBA model's reaction network. While the FBA reaction data IS queried (cell 6, 1,421 NADH reactions showing rxn10122 carries ~8.38 flux units), it's used only descriptively — the actual stoichiometry comparison uses the hardcoded values. The REPORT acknowledges this ("uses theoretical pathway biochemistry, not measured flux distributions"). The manually entered values appear biochemically reasonable (quinate → 4 NADH via succinyl-CoA + acetyl-CoA TCA turns; glucose → 9 NADH via Entner-Doudoroff + 2 TCA turns) but are not independently validated against the model's per-condition flux predictions.

**Complex I FBA discrepancy (NB02, cells 3–5)**: nuoA (ACIAD0730) shows `reactions: None` and `minimal_media_flux: None` in the gene-level query, yet the narrative states "FBA routes all NADH through Complex I." NB03 cell 6 resolves this: rxn10122 (NADH:ubiquinone oxidoreductase, the Complex I reaction) carries all NADH oxidation flux (~8.38 units). The discrepancy arises because the FBA model tracks Complex I flux at the reaction level (rxn10122) but doesn't map this reaction back to individual nuo subunit genes. This is understandable but would benefit from explicit explanation in NB02 so readers don't misinterpret the apparent contradiction.

**Statistical methods**: The Mann-Whitney U test in NB04 (cell 9) is appropriate for comparing two small groups with potentially non-normal distributions. The test correctly uses `alternative='two-sided'`. The result (p=0.24) is honestly reported as non-significant.

**Notebook organization**: All four notebooks follow a clean structure: markdown header with goal/inputs/outputs, setup cell, numbered sections, and summary cell. Data is saved to `data/` and figures to `figures/` at the end. NB02 explicitly closes the database connection. Good practice throughout.

**Pitfall awareness**: The project correctly handles the Fitness Browser all-string column pitfall (`CAST AS FLOAT`), uses `orgId` filters on `genefitness`, and separates Spark-dependent (NB04) from local notebooks (NB01–03). The `get_spark_session()` call in NB04 uses the correct JupyterHub pattern (no import needed). No issues with the pitfalls documented in `docs/pitfalls.md`.

## Findings Assessment

**Condition-specific respiratory wiring (Finding 1)**: Well-supported by the data in NB01. The heatmap and subsystem profiles clearly show distinct respiratory configurations per carbon source. The wiring summary correctly identifies which subsystems are required vs dispensable per condition. Two threshold choices are made without justification: cell 11 uses `< 0.8` for "defect" and `> 1.0` for "fine" in the subsystem summary, while cell 15 uses `< 0.6` for "essential" in the wiring model. The different thresholds produce somewhat different pictures (e.g., Complex I shows "defect" on asparagine at 0.59 by cell 11's threshold but is not classified as "essential" for asparagine in the wiring model). The thresholds are reasonable but the rationale is not discussed.

One additional concern: the Complex II (SDH) subsystem profile is based on a single gene with growth data (ACIAD2880/sdhA) out of 5 SDH genes in the inventory (sdhB, sdhC, sdhD, sdhE all lack data). The profile for this subsystem is thus based on n=1, making it less robust than Complex I (n=11) or Cyt bo3 (n=4). The notebook reports the n values in the subsystem table but doesn't flag the n=1 issue for interpretation.

**NDH-2 compensation model (Finding 2)**: This is the weakest finding because NDH-2 has no growth data, so the central prediction (NDH-2 compensates on glucose) cannot be directly tested. The indirect evidence is presented honestly: FBA routing, genomic context, pangenome conservation status, and ortholog-transferred fitness. The REPORT correctly lists this as the primary limitation. The ortholog-transferred fitness data (30 conditions, mean fitness -0.136) shows mild NDH-2 defects across conditions, but notably has *no aromatic conditions* in the transferred data — this limits the ability to test the aromatic-specific hypothesis. NB02 mentions this in passing but the REPORT doesn't emphasize it as a specific gap.

**Rate vs yield resolution (Finding 3)**: This is the project's most novel contribution, but it rests on qualitative reasoning rather than quantitative evidence. The argument is: quinate produces fewer NADH (4) than glucose (9) but Complex I is more essential on quinate; therefore, the explanation must be NADH flux *rate* (concentrated TCA burst from ring cleavage) rather than total yield. The biochemical logic is sound:
- Quinate catabolism funnels all carbon through ring cleavage → succinyl-CoA + acetyl-CoA → 2 near-simultaneous TCA turns
- Glucose catabolism distributes NADH production across multiple Entner-Doudoroff steps + TCA
- The "burst" vs "distributed" distinction is a genuine structural property of the pathways

However, there is no measurement or estimate of actual NADH production *rates*. The FBA model could in principle provide per-condition flux rates, but it predicts zero flux through NDH-2 on all conditions (because FBA optimizes for growth rate and prefers the more ATP-efficient Complex I). The REPORT acknowledges this and suggests measuring NADH/NAD+ ratios experimentally as a future direction.

**Cross-species NDH-2 compensation (Finding 4)**: The direction supports the hypothesis (organisms with NDH-2 show mean aromatic deficit of -0.086 vs -0.505 for those without), but the result is not statistically significant (p=0.24) with only 4 organisms in the "no NDH-2" group. The *P. putida* outlier (large Complex I deficit despite having NDH-2) is noted and plausibly explained as an active aromatic degrader that overwhelms NDH-2 capacity. The NDH-2 false positive concern (see Code Quality above) means the true group sizes may be more balanced than 10/4, which would further weaken any signal. Importantly, the REPORT is transparent about this limitation.

**Limitations**: Well acknowledged. The REPORT lists seven specific limitations covering the most important caveats: no NDH-2 growth data, theoretical stoichiometry, small cross-species sample, annotation variability, ACIAD3522 function uncertainty, NDH-2 false positives, and the dropped pangenome analysis. The Future Directions section proposes five concrete, testable follow-up experiments. The project's transparency about its limitations is a notable strength.

## Suggestions

1. **[Critical] Fix NDH-2 false positives in NB04**: Organisms like `pseudo3_N2E3` (8 hits) and `pseudo5_N2C3_1` (8 hits) almost certainly have Complex I subunits leaking through the text-based NDH-2 filter. Either use KO-based identification (K03885 via the FB `besthitkegg` table), apply a maximum hit count filter (true NDH-2 should have 1–2 genes per organism), or manually curate the hits. Re-run the compensation analysis after fixing — the current 10/4 split may actually be closer to 7/7, which would substantially change the mean deficit comparison.

2. **[Important] Update README Data Sources**: The README lists `kbase_ke_pangenome` under Data Sources for "NDH-2/Complex I co-occurrence," but this analysis was not performed. Either remove this entry or add a note indicating it was planned but not executed (with a pointer to REPORT.md Future Direction #3). The REPORT already documents this gap, so the fix is just aligning the README.

3. **[Moderate] Tighten the "Other respiratory" category in NB01**: The current broad keyword search captures non-respiratory enzymes (transcription factors, drug resistance genes, amino acid catabolism enzymes). Consider either narrowing the SQL search patterns, applying additional KO/EC filtering to the "Other" category, or renaming it to "Other redox/NADH-related enzymes" to more accurately describe what's included. The headline "62 respiratory chain genes" overstates the respiratory inventory by roughly 10–15 genes.

4. **[Moderate] Strengthen the rate vs yield argument with FBA flux data**: NB03 queries 1,421 NADH reactions from the FBA model but only uses them descriptively. The `gene_phenotypes` table contains per-condition flux predictions (230 conditions) that could provide condition-specific NADH production flux estimates. Comparing total NADH flux on glucose vs quinate conditions would give quantitative support to the "concentrated TCA burst" hypothesis, even though the model doesn't distinguish Complex I from NDH-2 routing.

5. **[Moderate] Note the n=1 limitation for Complex II (SDH) profile**: The subsystem profile for Complex II is based on a single gene (sdhA/ACIAD2880) because the other 4 SDH subunits lack growth data. This should be flagged in the notebook or REPORT when interpreting the SDH condition profile. The other core subsystems (Complex I n=11, Cyt bo3 n=4, Cyt bd n=3) have more robust sample sizes.

6. **[Minor] Clarify the growth ratio thresholds**: NB01 uses two different thresholds without justification: `< 0.8` for "defect" (cell 11) and `< 0.6` for "essential" (cell 15). Consider adding a brief rationale (e.g., based on the distribution of growth ratios across all genes, or correspondence to specific fitness loss magnitudes) and using consistent terminology.

7. **[Minor] Explain the nuoA FBA discrepancy in NB02**: Cell 3 shows nuoA (ACIAD0730) has `reactions: None` and `flux: None`, yet the narrative states "FBA routes all NADH through Complex I." A brief note that Complex I flux is tracked at the reaction level (rxn10122, which carries ~8.38 flux units per NB03 cell 6) rather than mapped back to individual nuo subunit genes would prevent reader confusion.

8. **[Minor] Emphasize the lack of aromatic conditions in NDH-2 ortholog fitness**: NB02 cell 9 shows 30 conditions with ortholog-transferred NDH-2 fitness data, but none are aromatic substrates. The REPORT mentions "no aromatic conditions" in passing but doesn't list it as a specific limitation. Since the hypothesis is specifically about aromatic catabolism overwhelming NDH-2 capacity, the absence of aromatic conditions in the transferred data is a notable gap that deserves explicit mention.

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-02-19
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, 4 notebooks, 6 data files, 7 figures, requirements.txt
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.

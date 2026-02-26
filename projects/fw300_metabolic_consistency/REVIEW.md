---
reviewer: BERIL Automated Review
date: 2026-02-26
project: fw300_metabolic_consistency
---

# Review: Metabolic Consistency of Pseudomonas FW300-N2E3

## Summary

This is an exemplary multi-database integration project that asks an original and scientifically worthwhile question: do four independent BERDL metabolic databases (Web of Microbes, Fitness Browser, BacDive, GapMind) produce a coherent metabolic picture for a single organism? The project is well-structured across three notebooks with saved outputs, a thorough research plan with clearly stated hypotheses, and a comprehensive report grounded in relevant literature. The headline finding — 94% mean concordance with tryptophan overflow as the key biologically meaningful discordance — is supported by the data and honestly qualified. The analysis includes several commendable methodological refinements: sample-size-aware BacDive confidence scoring, approximate-match flagging for the Cytosine/Uracil nucleoside mappings, a statistical baseline test (binomial) for concordance, a sensitivity analysis excluding approximate matches, and a clear decomposition of structural vs. informative concordance components. The main remaining weaknesses are the low cross-database overlap (only 21/58 metabolites testable, 3 with four-way coverage), 7 of 31 queried FB conditions silently returning no data without explanation, and the per-strain BacDive consensus issue. Overall this is a strong, reproducible analysis that demonstrates the value of cross-database metabolic triangulation and identifies a genuinely interesting biological signal in tryptophan overflow.

## Methodology

**Research question**: Clearly stated and testable. The null hypothesis (internal consistency across databases) and alternative (discordances revealing strain-vs-species differences, production-vs-utilization distinctions, or prediction gaps) are well-formulated in RESEARCH_PLAN.md. The five explicit comparison axes (WoM↔FB, WoM↔BacDive, FB↔BacDive, WoM↔GapMind, FB↔GapMind) give the analysis structure.

**Approach**: The three-way triangulation design — anchoring on WoM-produced metabolites and matching outward — is appropriate. The manual metabolite name harmonization (NB01, cell `613d8f51`) is transparent: all mappings are explicit Python dictionaries with inline comments flagging imprecise matches (Cytosine→Cytidine, Uracil→Uridine). This is preferable to opaque fuzzy matching at this scale.

**Data sources**: All four databases are clearly identified in both RESEARCH_PLAN.md and REPORT.md, with specific table names, strain identifiers (e.g., `pseudo3_N2E3`, `RS_GCF_001307155.1`), and expected row counts. The REPORT.md "Data" section provides a complete manifest of all 8 generated TSV files with row counts.

**Reproducibility**: The README.md includes a complete Reproduction section with prerequisites (Python 3.10+, BERDL Spark for NB01/NB02, local for NB03), step-by-step instructions with estimated runtimes, and papermill commands. A `requirements.txt` is present listing `pandas>=1.5`, `numpy>=1.23`, `matplotlib>=3.6` with comments explaining the Spark dependency. The Spark/local separation is clearly documented — NB03 reads cached TSV files and requires no Spark.

**Notebook outputs**: All three notebooks contain saved outputs (text, tables, figures) in their cells. This is critical for reviewability — the analysis can be assessed without re-running on the Spark cluster. Figures are saved to the `figures/` directory (3 PNG files).

**Notable methodological strength**: The sample-size-aware BacDive confidence scoring (high ≥10, moderate ≥3, low = 1-2 strains) prevents over-interpreting sparse data. The statistical decomposition in NB03 (cell `m10bwxsku4`) correctly identifies that the 94% concordance is structurally driven by FB (21/21 = 100%) and GapMind (13/13 = 100%), with BacDive (3/7 = 43%) as the only genuinely variable component. The binomial test against the species baseline (p=0.40) is the right test and the right interpretation.

## Code Quality

**SQL correctness**: All Spark SQL queries are well-formed, properly filtered, and use appropriate joins. Key pitfalls from `docs/pitfalls.md` are correctly addressed:
- **GapMind multiple rows per genome-pathway pair** (`pangenome_pathway_geography` pitfall): Correctly handled with `MAX(score_value) ... GROUP BY pathway, genome_id` in NB01 cell `6529bbfb`, exactly matching the documented solution. The code also correctly uses the five GapMind score categories (`complete`, `likely_complete`, `steps_missing_low`, `steps_missing_medium`, `not_present`) rather than looking for a nonexistent `present` flag.
- **Fitness Browser string columns** (`fitnessbrowser_string_columns` pitfall): Correctly cast with `CAST(gf.fit AS DOUBLE)` and `CAST(gf.t AS DOUBLE)` in NB02 cell `cell-4`, with an explicit comment and dtype verification in the output.
- **Experiment table schema** (`pathway_capability_dependency` pitfall): Uses correct table name `experiment` with correct column names `expName`, `expGroup`, `condition_1`.

**Genome ID handling**: NB01 cell `6529bbfb` gracefully handles the `RS_` prefix mismatch between the pangenome identifier (`RS_GCF_001307155.1`) and the actual GapMind data (`GCF_001307155.1`). The code tries the original ID, strips the prefix, and falls back to a partial match on the accession number. This is defensive programming that will survive data format changes.

**Approximate match flagging**: The crosswalk includes an `fb_match_quality` column distinguishing `exact` from `approximate` matches (NB01 cell `1a6c27cb`). The sensitivity analysis in NB03 confirms that excluding the two approximate matches shifts mean concordance from 0.937 to 0.930 — a negligible difference. This is good scientific practice.

**Minor code issues**:

1. **7 missing FB conditions**: NB02 queries 31 FB conditions (cell `cell-3`) but only 24 return fitness data (cell `cell-4` output: "Unique conditions: 24"). The 7 conditions that returned zero gene-experiment records are silently dropped. These may be conditions where no experiments had significant fitness hits meeting the |fit|>1, |t|>4 thresholds, or they may have had no matching experiments for this organism. A brief diagnostic print listing which conditions returned no data would improve transparency. The crosswalk lists 28 WoM metabolites matched to FB, but the met_summary table (NB02 cell `cell-6`) shows only 21 unique `wom_compound` values, meaning the downstream analysis correctly uses only the metabolites with actual fitness data.

2. **BacDive per-strain deduplication**: In NB01 cell `2e096ab3`, the `n_positive` and `n_negative` counts sum raw utilization records rather than computing one consensus per strain. For D-glucose, there are 104 records from 51 strains (visible in the output), meaning some strains contribute multiple records. The `pct_positive` calculation uses these raw counts. While the impact on this analysis is minor (the conclusions are driven by tryptophan at 0/52 and malate at 49/49, where duplication doesn't change the direction), a per-strain consensus step before species-level aggregation would be more rigorous.

3. **`normalize_compound_name()` limitations**: The regex strips stereochemistry prefixes only at the start of the string (`^(l-|d-|dl-|...)`). Compounds like "Sodium D,L-Lactate" require manual mapping, which is correctly handled. The function serves as a secondary matching layer behind the manual crosswalk, so this is not a practical issue for the current analysis.

**Notebook organization**: Each notebook follows a clean structure: setup → data extraction/query → analysis → visualization → summary. Markdown cells delineate sections. Summary statistics are printed at the end of each notebook with clear formatting.

## Findings Assessment

**Concordance claim**: The "94% mean concordance" is accurately computed from the testable subset but appropriately qualified. The statistical decomposition (NB03 cell `m10bwxsku4`) transparently shows that 100% of this comes from FB and GapMind being structurally concordant, with BacDive as the only informative source. The REPORT.md both leads with the 94% headline and immediately provides the decomposition — this is honest reporting. The 64% of metabolites classified as "wom_only" are excluded from concordance, and the limitations section (REPORT.md) correctly notes that the untested majority "may harbor additional discordances."

**Tryptophan overflow finding**: This is the strongest and most interesting result. The convergence of four independent lines of evidence (WoM: produced, FB: 231 significant genes, GapMind: complete pathway, BacDive: 0/52 strains utilize) makes a compelling case. The cross-feeding interpretation is well-supported by cited literature (Fritts et al. 2021, Ramoneda et al. 2023, Yousif et al. 2025, Sibanyoni et al. 2025). The claim that this is the "first systematic cross-database metabolic consistency analysis" (REPORT.md) appears justified.

**GapMind validation**: The 13/13 perfect concordance is a meaningful result, though partly expected — the matched metabolites are common amino acids and organic acids with well-characterized pathways. The REPORT.md correctly contextualizes this against Price et al. (2022, 2024) rather than overstating it as surprising.

**Pleiotropic genes finding**: The REPORT.md now explicitly addresses this (Finding #4), correctly identifying the top 18 genes as amino acid biosynthesis "housekeeping" genes (histidine, methionine, branched-chain, aromatic amino acid pathways) and distinguishing them from the ~370 substrate-specific genes. This is a useful analytical insight for future WoM↔FB integration work.

**Limitations**: Well-enumerated in REPORT.md with six specific items: low overlap, medium effects, BacDive species-level aggregation, name matching, pleiotropic genes, and deferred NB04. All are genuine confounders honestly disclosed. The deferred NB04 is clearly marked as such in RESEARCH_PLAN.md with a rationale for deferral.

**Literature support**: The REPORT.md references section includes 11 papers, all relevant and correctly cited. The interpretation draws appropriately on the cross-feeding literature (Fritts, Giri, Ramoneda, Yousif, Sibanyoni) and the database method papers (Kosina, Price).

## Suggestions

1. **Diagnose the 7 missing FB conditions**: Of 31 queried FB conditions, only 24 returned data in NB02. Add a diagnostic cell listing which 7 conditions returned no gene-experiment records and why (no experiments for that organism-condition pair? no genes meeting the significance threshold? query mismatch?). This would close a minor transparency gap. *(Moderate impact)*

2. **Add per-strain BacDive consensus**: Before computing species-level `pct_positive`, deduplicate by taking one utilization call per strain per compound (e.g., majority vote or "positive if any positive"). For compounds like D-glucose (104 records from 51 strains), this would give a cleaner species-level summary. The impact on conclusions is likely negligible, but it would make the methodology more defensible for future reuse. *(Low impact, methodological hygiene)*

3. **Add a permutation test for concordance**: The binomial test on BacDive is good, but a complementary approach would be to permute the WoM-metabolite↔database assignments and recompute overall concordance 1,000 times to generate a null distribution. This would directly test whether the observed concordance structure is meaningful rather than an artifact of the data topology. *(Low impact — the current binomial test adequately addresses the question, and the structural decomposition already shows why a permutation test would likely show significance: the non-random FB and GapMind matching creates inherent concordance)*

4. **Expand the crosswalk with chemical identifiers**: The REPORT.md future directions mention using InChIKey or CHEBI for matching. The WoM compound table includes `inchi_key`, `pubchem_id`, and `smiles_string` columns, though they appear to be NULL for all FW300-N2E3 observations in the current data. If these identifiers are populated for other organisms, they could significantly increase the WoM↔BacDive overlap beyond the current 8 metabolites. *(Nice-to-have, future work)*

5. **Consider a supplementary table of all 58 metabolites**: The consistency matrix TSV contains all 58 metabolites, but neither the REPORT.md nor the notebooks present a clean summary table showing all 58 WoM compounds with their cross-database status. A compact table or appendix showing compound name, WoM action, and which databases it matched (even if just "—" for unmatched) would give readers a complete picture at a glance. *(Nice-to-have)*

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-02-26
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, 3 notebooks, 8 data files, 3 figures, requirements.txt
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.

---
reviewer: BERIL Automated Review (Claude, claude-sonnet-4-6)
date: 2026-06-29
project: enigma_isolate_mycothiol_isomerase
---

# Review: ENIGMA Isolate Survey: Mycothiol-Dependent Malonylpyruvate Isomerase

## Summary

This is a re-review following REVIEW_1 (dated 2026-06-25). Since then, the REPORT has been substantively revised: the headline now correctly reads "136 Unique ENIGMA Strains Carry Malonylpyruvate Isomerase," the genome-records vs. unique-strains distinction is maintained consistently throughout the text, and the Discoveries section was expanded from two to three entries with the Alphaproteobacteria finding properly elevated as a cross-project discovery. These are real improvements that address the most prominent concern from Review 1. However, the majority of Review 1's actionable suggestions remain open, and two new issues have emerged as a direct consequence of the REPORT revision: (a) NB02 Cell 15 now outputs "Total MAI-positive candidates: 163" while the REPORT says 136 unique strains — a discrepancy created by updating REPORT text without updating the notebook; and (b) a substantial body of specific quantitative claims in the REPORT (the Fisher's exact test OR=204.7/p=2×10⁻⁶⁷, all unique-strain counts, the 62/74 vs. 24/975 taxonomy breakdown, and the genus-level tables) cannot be traced to any committed notebook cell, matching the "commit notebooks alongside their artifacts" pitfall from `docs/pitfalls.md`. Additionally, a small internal numerical inconsistency exists in the REPORT (54 vs. 51 Environmental complete-pathway strains). The science remains sound and the conclusions plausible, but these traceability and consistency issues should be resolved before submission.

## Methodology

**Strengths.** The H0/H1 framing is crisp and directly testable; H1 is supported. The connection to the upstream pangenomic project is well-explained. KO K16163 is the correct primary search key for malonylpyruvate isomerase. The Fisher's exact test framing (Actinobacteria vs. non-Actinobacteria MAI carriers among genomes with resolved taxonomy) is a sound analytical choice. Literature context (Wang 2007 crystal structure, Park & Roe 2008 sigmaR regulatory framework, Passari 2025 metal tolerance genomics) is directly relevant and correctly cited.

**Concerns.**

1. **REPORT numbers not traceable to notebook cells (new in Review 2).** NB01 has exactly 7 code cells. Reading all cell sources and outputs confirms that none computes: the 136/2,075 unique-strain/organism counts (de-duplication on `organism_name`), the 64% Environmental-label fraction (1,876/2,925), the 62/74 Actinobacteria vs. 24/975 non-Actinobacteria breakdown, the Fisher's exact OR=204.7 and p=2×10⁻⁶⁷, the genus-level taxonomy breakdown tables in the Results section, or the per-genus unique-strain counts. NB01 Cell 2 imports `fisher_exact` from `scipy.stats` but this function is never called in any cell. NB02 Cell 5 extracts genus with `str.split().str[0]` and scores without de-duplication; its Cell 15 outputs "Total MAI-positive candidates: 163" — genome records, not unique strains. These analyses appear to have been performed interactively and their results recorded only in the REPORT, precisely matching the "Commit Notebooks Alongside Their Artifacts" pitfall in `docs/pitfalls.md`. The three-cell pattern needed (de-duplication + taxonomy breakdown + Fisher's exact) could be added to NB01 between the current Cell 14 (MAI-positive list export) and Cell 15 (Section 4 markdown header).

2. **≥2 annotation lines of evidence criterion not explicitly disclosed (carried from Review 1 Concern #2).** RESEARCH_PLAN.md Decision Criterion 1 requires "≥2 annotation lines of evidence." NB01 Cell 9 documents that product-name and InterPro fallbacks were unavailable via browser tables, making KO K16163 the sole evidence line. The REPORT's Limitations section mentions "Annotation-only detection" but does not state this represents a deviation from the pre-specified criterion. One sentence in Limitations would close this.

3. **Inconsistent related-project name (carried from Review 1 Concern #3).** README uses `mycothiol_detox_module`; REPORT Interpretation section (Novel Contribution paragraph) uses `metal_detox_genes_with_phylogenetic_bias`; NB01 Cell 1 (introductory markdown) uses `metal_detox_genes_with_phylogenetic_bias`. Whichever name is the live project directory should be used consistently across all three.

## Reproducibility

**Strengths.** The parquet caching pattern in NB01 Cell 4 (`if is_valid_parquet(enigma_path)`) remains well-designed. All four key data files are present: `enigma_all_genomes.parquet` (81 KB), `enigma_mai_hits.csv` (9.3 KB), `enigma_pathway_completeness.csv` (164 KB), `enigma_candidate_shortlist.csv` (1.8 KB). The figure `nb02_candidate_scatter.png` is committed. NB01 has 8 cells with outputs; NB02 has 9 cells with outputs.

**Concerns.**

4. **NB02 summary contradicts REPORT on unique-strain count (new in Review 2).** NB02 Cell 15 prints "Total MAI-positive candidates: 163" (genome records), while the REPORT now consistently says 136 unique strains. This discrepancy was introduced when the REPORT text was updated without updating the notebook code or re-running NB02.

5. **`enigma_genome_qc.parquet` missing (carried from Review 1 Concern #4).** NB02 Cell 15 explicitly lists this path in its saved output: `  - .../data/enigma_genome_qc.parquet`. No such file exists in `data/`. Either remove the reference or add the missing `to_parquet` call.

6. **Stale file references in NB01 Cell 16 (carried from Review 1 Concern #5).** NB01 Cell 16 lists `enigma_mai_ko_hits.parquet` and `enigma_mai_product_hits.parquet` in its saved output. Both paths are confirmed in the cell's text output; neither file exists in `data/`. Remove these two print lines.

7. **No `## Reproduction` section in README (carried from Review 1 Concern #6).** Which notebook requires a live Spark session (NB01, for the initial query) vs. which can run locally from cached data (NB02) is not documented anywhere.

8. **`pyarrow` missing from `requirements.txt` (carried from Review 1 Concern #7).** Both notebooks use `.to_parquet()` and `pd.read_parquet()`. Current `requirements.txt` lists: `pandas>=2.0`, `numpy>=1.24`, `scipy>=1.10`, `matplotlib>=3.7`, `seaborn>=0.12`, `statsmodels>=0.14`, `pyspark>=3.4` — no `pyarrow`. Add `pyarrow>=12.0`.

9. **README Quick Links still points to nonexistent `REVIEW.md` (carried from Review 1 Concern #8).** Now that both REVIEW_1.md and REVIEW_2.md exist, the Quick Links section should be updated to reference the current reviews. The target `REVIEW.md` does not exist.

## Code Quality

**Strengths.** The main Spark query in NB01 Cell 4 is correct and efficient: a single-pass `GROUP BY` with four `MAX(CASE WHEN ko.kegg_id = '...' THEN 1 ELSE 0 END)` flags and LEFT JOINs to preserve zero-annotation genomes. The composite scoring in NB02 is transparent (pathway 0–40 + genus tractability 0–20, max 60) and consistent with REPORT descriptions. `np.random.default_rng(42)` in the scatter plot ensures reproducible jitter.

**Concerns.**

10. **`fisher_exact` imported but never called (new in Review 2).** NB01 Cell 2 imports `fisher_exact` and `norm` from `scipy.stats`, and `fdrcorrection` from `statsmodels`. None of these are called in any committed cell. This confirms that the statistical test cited in the REPORT was not run in a committed notebook. Once Suggestion #1 is implemented, keep `fisher_exact`; remove `norm` and `fdrcorrection` if still unused.

11. **Shortlist tie-breaking is undisclosed genome_id order (carried from Review 1 Concern #9).** NB02 Cell 9: `shortlist = mai_df.head(20).copy()` takes the top 20 after scoring — all 20 score 60/60, so rank reflects database return order (effectively arbitrary). The REPORT does not disclose this.

12. **`Paenarthrobacter`, `Kitasatospora`, and `Leifsonia` may be unscored (carried from Review 1 Concern #10).** `Paenarthrobacter aurescens FW305-123` is the first row in NB01 Cell 14's output and carries the complete 4-gene pathway. If absent from the `tractable_genera` dict in NB02 Cell 7, it receives genus_tractability = 0 and is unduly deprioritized relative to its phylogenetic relationship to *Arthrobacter* (which scores 2). The full dict is truncated in visible source and should be verified.

## Findings Assessment

**Conclusions are well-supported where traceable.** The traceable claims — 2,925 total genomes (NB01 Cell 4), 163 genome records with MAI (NB01 Cells 4, 7, 11, 14), 134 genome records with 4/4 pathway completeness (NB01 Cell 13 output: `1.00     134`), 20-strain shortlist — are directly verifiable from committed notebook outputs. The literature context is appropriate and correctly cited. The Rhizobiaceae observation is flagged with appropriate epistemic caution and two concrete mechanistic hypotheses.

**Internal numerical inconsistency in REPORT (new in Review 2).** The note following the complete-pathway taxonomy table reads: *"The **54** Environmental-unresolved complete-pathway strains span multiple ENIGMA field sites…"* — but the complete-pathway table directly above shows **51** unique Environmental strains, and the preceding paragraph also uses 51 ("Environmental-unresolved strains (51)"). The number 54 comes from the all-MAI-positive taxonomy table (first table in the Results section: "Environmental (unresolved) | 77 | **54**") and appears to have been copied into the note incorrectly. The note should read 51, not 54.

**Summary of REPORT claim traceability:**

| Claim | Traceable to notebook cell? |
|-------|-----------------------------|
| 2,925 total ENIGMA genomes | ✓ NB01 Cell 4 |
| 163 genome records with MAI | ✓ NB01 Cells 4, 7, 11, 14 |
| 134 genome records with 4/4 pathway | ✓ NB01 Cell 13 |
| 2,829/2,099/2,189 mshA/B/C genome counts | ✓ NB01 Cell 7 |
| 136 unique strains with MAI | ✗ No notebook cell |
| 2,075 unique organisms total | ✗ No notebook cell |
| 112 unique strains with complete pathway | ✗ No notebook cell |
| 1,876 "Environmental" genome records (64%) | ✗ No notebook cell |
| 62/74 Actinobacteria vs. 24/975 non-Actinobacteria | ✗ No notebook cell |
| Fisher's exact OR=204.7, p=2×10⁻⁶⁷ | ✗ No notebook cell (`fisher_exact` imported, never called) |
| Genus-level taxonomy breakdown tables | ✗ No notebook cell |

**Limitations honestly stated.** The REPORT correctly identifies: absence of CheckM quality, unresolved Environmental labels, annotation-only detection, no isolation site metadata, Jen's list not integrated. These gaps are not papered over.

## Discoveries

The three Discoveries entries are assessed as follows:

- **Discovery 1** ("136 unique ENIGMA strains / 163 genome records at 5.6% carry K16163, predominantly *Streptomyces* from Oak Ridge contaminated sites") — The genome-record count (163) is traceable; the unique-strain count (136) is not yet backed by a committed cell. Scope is accurate. The claim should be retained but requires Suggestion #1 to become fully verifiable.

- **Discovery 2** ("112 unique strains carry complete 4-gene mycothiol pathway; 30 are *Streptomyces* with genetic tools") — The 112 and 30 counts are not traceable to any committed notebook cell. Same gap as Discovery 1. Scientifically plausible given the data files, but requires the same fix.

- **Discovery 3** ("MAI in ENIGMA Alphaproteobacteria is unexpected; all carry partial pathways; annotation cross-reactivity or HGT warranted") — Partially traceable: total genome record count (163) is confirmed; per-genus Rhizobium/Ensifer breakdown is not in any cell output. The interpretation — flagging the 3/4-gene Rhizobium strains (mshA+mshC+mai) as ambiguous — is scientifically appropriate and the cautionary language is correct. Scope is not overgeneralized.

None of the three discoveries duplicates a known result from prior projects. All are load-bearing for cross-project synthesis. The traceability gap (Concern #1, Suggestion #1) is the primary barrier to treating the precise numbers as fully verified.

## Suggestions

1. **(Critical) Add a de-duplication + taxonomy breakdown + Fisher's exact cell to NB01.** After the current Cell 14 (MAI-positive export), insert a cell that: (a) de-duplicates `enigma_df` on `organism_name` to produce 136/2,075 unique-strain counts; (b) classifies taxa as Actinobacteria vs. non-Actinobacteria vs. Environmental based on genus; (c) tabulates the 62/74 vs. 24/975 contingency; (d) calls `fisher_exact([[62, 12], [24, 951]])` (or equivalent) to produce OR=204.7 and p=2×10⁻⁶⁷; (e) prints the per-genus taxonomy table. This closes the traceability gap for the majority of REPORT numbers and is the single most important fix before submission.

2. **(Critical) Update NB02 to report unique-strain count in summary.** After Suggestion #1 is implemented, update NB02 Cell 15 to print the de-duplicated candidate count ("136 unique MAI-positive strains (163 genome records)") rather than "163." Either load a de-duplicated version of the hits file or add a one-line `drop_duplicates('organism_name')` before the summary.

3. **(Critical) Fix "54 → 51" REPORT inconsistency.** In the note at the bottom of the complete-pathway taxonomy table, change "The 54 Environmental-unresolved complete-pathway strains" to "The 51 Environmental-unresolved complete-pathway strains" to match both the table above and the text in the preceding paragraph.

4. **(Important) Remove or create `enigma_genome_qc.parquet`.** Either add a missing `to_parquet` call in NB02 (if QC data was computed but not saved) or remove the reference from NB02 Cell 15's print statement.

5. **(Important) Remove stale file references from NB01 Cell 16.** Delete the two lines printing `enigma_mai_ko_hits.parquet` and `enigma_mai_product_hits.parquet`. The saved cell output currently lists them as if they exist.

6. **(Important) Add `## Reproduction` section to README.md.** State: NB01 requires a live Spark session on JupyterHub for the initial query; NB02 can run locally from cached CSV/parquet after NB01 has been executed once.

7. **(Important) Acknowledge ≥2-evidence criterion deviation in REPORT.md Limitations.** Add one sentence noting that the RESEARCH_PLAN's requirement for ≥2 independent annotation signals was reduced to a single KO hit because the ENIGMA Genome Depot browser tables do not expose InterPro domains or free-text product name search.

8. **(Important) Reconcile the related-project name.** README, REPORT Interpretation, and NB01 Cell 1 use two different names (`mycothiol_detox_module` and `metal_detox_genes_with_phylogenetic_bias`). Verify the live project directory and update all references consistently.

9. **(Moderate) Add `pyarrow>=12.0` to `requirements.txt`.**

10. **(Moderate) Fix README Quick Links.** Update `[Review](REVIEW.md)` to link to REVIEW_1.md and REVIEW_2.md. The file `REVIEW.md` does not exist.

11. **(Moderate) Disclose shortlist tie-breaking logic.** All 20 shortlisted candidates score 60/60. Add a note in NB02 Cell 9 or REPORT stating that within the tied tier, listing order is arbitrary (database genome_id order) and all 20 entries are equivalent starting points.

12. **(Moderate) Remove unused imports `norm` and `fdrcorrection` from NB01 Cell 2** once `fisher_exact` is actually called in a cell.

13. **(Nice-to-have) Verify `tractable_genera` coverage for `Paenarthrobacter`, `Kitasatospora`, and `Leifsonia`** in NB02 Cell 7. `Paenarthrobacter aurescens FW305-123` (first row of NB01 Cell 14 output) carries the complete 4-gene pathway; scoring it 0 for genus tractability may not reflect its biological tractability relative to *Arthrobacter*.

14. **(Nice-to-have) Add a taxonomy summary bar chart from NB01.** Once the taxonomy breakdown cell exists (Suggestion #1), a genus/phylum bar chart of MAI-positive hits would make the Actinobacteria vs. Alphaproteobacteria vs. Environmental breakdown immediately visible, complementing the NB02 scatter plot.

## Review Metadata
- **Reviewer**: BERIL Automated Review (Claude, claude-sonnet-4-6)
- **Date**: 2026-06-29
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, REVIEW_1.md, references.md, requirements.txt, beril.yaml, 2 notebooks (01_enigma_depot_query.ipynb: 17 cells, 7 code cells — all sources and outputs read; 02_candidate_ranking.ipynb: 16 cells, 8 code cells — all sources and outputs read), 4 data files (no enigma_genome_qc.parquet present), 1 figure, docs/pitfalls.md
- **Prior review**: REVIEW_1.md (2026-06-25) — 11 concerns raised; 1 fully addressed (genome-record vs. unique-strain headline), 1 partially addressed (annotation-only detection note present but deviation not explicit); 9 remain open; 3 new concerns identified in this review
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.

<!-- report_hash: sha256:56722633619f54adde6edc69d7f541816809ba28b9ab33bc443031ac458bd4d4 -->

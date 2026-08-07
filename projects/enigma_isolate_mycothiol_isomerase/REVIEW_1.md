---
reviewer: BERIL Automated Review (Claude, claude-sonnet-4-6)
date: 2026-06-25
project: enigma_isolate_mycothiol_isomerase
---

# Review: ENIGMA Isolate Survey: Mycothiol-Dependent Malonylpyruvate Isomerase

## Summary

This is a focused, well-motivated project that delivers a concrete outcome: a ranked shortlist of 20 *Streptomyces* ENIGMA isolates as experimental candidates for testing MAI's adaptive metal function. The research question is crisp, the hypothesis is testable (and was tested), and the literature context is carefully assembled. The main Spark query in NB01 is efficient and correct, the caching pattern is well implemented, and both notebooks run to completion with meaningful saved outputs. The primary weaknesses are (a) a genome-vs-strain conflation in the headline count that is not disclosed in the REPORT, (b) a missing output file (`enigma_genome_qc.parquet`) and stale file references in the NB01 summary cell, (c) an undisclosed deviation from the research plan's ≥2-evidence criterion, and (d) small reproducibility gaps (no Reproduction section in README, missing `pyarrow` dependency, stale Quick Links target). None of these compromise the scientific conclusions, but they should be corrected before the project is submitted.

## Methodology

**Strengths.** The H0/H1 framing in `RESEARCH_PLAN.md` is precise and directly testable. The decision criteria (gene present, completeness ≥85%, culture availability, ≥2 annotation lines of evidence) are stated in advance, and the REPORT correctly acknowledges which could not be evaluated (genome quality, culture availability). The connection to the upstream pangenomic project is well explained. The choice of KO K16163 as the primary search key is appropriate.

**Concerns.**

1. **Genome records vs. strain count (not disclosed).** The REPORT states "163 ENIGMA Isolates Carry Malonylpyruvate Isomerase" and "163 (5.6%) carry … MAI." `enigma_mai_hits.csv` has 163 rows with 163 unique `genome_id` values, but only 136 unique `organism_name` values — meaning 27 strain names map to multiple genome records (49 total rows across 22 duplicated names). Examples: `Ensifer adhaerens EB106-05-01-XG146` appears at genome_ids 3704, 3791, 61, 62; `Environmental isolate FW305-130` appears at ids 252 and 1232. The ENIGMA Genome Depot contains multiple genome assemblies for some strains. The REPORT should state "163 genome records (≤136 unique strains)" and clarify whether the 2,925 denominator also includes duplicate assemblies.

2. **≥2 annotation lines of evidence criterion not met.** `RESEARCH_PLAN.md` (Decision Criteria, point 1) requires "≥2 annotation lines of evidence" before prioritising a candidate. NB01 Cell 10 documents that the product-name and InterPro fallbacks were unavailable via browser tables, so the implemented analysis uses only KO K16163. The REPORT's Limitations section mentions "Annotation-only detection" but does not flag the deviation from the plan's explicit criterion. A sentence noting that the ≥2-evidence requirement was relaxed to a single KO line would make the discrepancy transparent.

3. **Inconsistent related-project name.** The README (`projects/mycothiol_detox_module`) and the REPORT's Interpretation section (`projects/metal_detox_genes_with_phylogenetic_bias`) use different names for the upstream pangenomic project. Whichever name is current should be used consistently throughout.

## Reproducibility

**Strengths.** Both notebooks have substantial saved outputs (NB01: 8/17 cells; NB02: 9/16 cells). The parquet caching pattern in NB01 Cell 5 (`if is_valid_parquet(enigma_path): pd.read_parquet(...)`) is well-designed — it means NB02 can run entirely locally from cached data without a Spark connection after NB01 has been executed once. The data directory contains all key files: `enigma_all_genomes.parquet`, `enigma_mai_hits.csv`, `enigma_pathway_completeness.csv`, `enigma_candidate_shortlist.csv`, and the figure `nb02_candidate_scatter.png`.

**Concerns.**

4. **`enigma_genome_qc.parquet` missing.** NB02 Cell 16 prints `data/enigma_genome_qc.parquet` as an output file, but no such file exists in `data/`. A corresponding `to_parquet` call is apparently absent from NB02. Readers following the output log will conclude a file exists that does not.

5. **Stale file references in NB01 Cell 17.** The summary cell prints paths for `enigma_mai_ko_hits.parquet` and `enigma_mai_product_hits.parquet`, both of which were never created (the product-name and KO-only intermediate files were consolidated into `enigma_all_genomes.parquet`). These paths should be removed or replaced with files that actually exist.

6. **No `## Reproduction` section in README.** It is unclear which notebooks require a live Spark connection vs. which can run locally from cached data. A brief Reproduction section (two steps: run NB01 on JupyterHub for the initial Spark query; run NB02 locally from cache) would close this gap.

7. **`pyarrow` missing from `requirements.txt`.** Both notebooks read and write Parquet files (NB01 Cell 5: `pd.read_parquet` / `enigma_df.to_parquet`), but `pyarrow` is not listed in `requirements.txt`. Add `pyarrow>=12.0`.

8. **README Quick Links target is wrong.** `REVIEW.md` listed under Quick Links should be `REVIEW_1.md`.

## Code Quality

**Strengths.** The main Spark query (NB01 Cell 5) is correct and efficient: a single pass with four `MAX(CASE WHEN ko.kegg_id = '...' THEN 1 ELSE 0 END)` flags, grouped by genome, avoids multiple round-trips. LEFT JOINs are used correctly to preserve genomes with no KO annotations. The composite scoring formula in NB02 is straightforward and consistent with the weights described in the REPORT (pathway 0–40, genus tractability 0–20, max 60). The `np.random.default_rng(42)` seed for jitter in the scatter plot ensures reproducibility. The `is_valid_parquet()` helper is a clean defensive pattern.

**Concerns.**

9. **Shortlist tie-breaking is genome_id order.** All 20 shortlisted entries score 60/60, so their ranking reflects the order of genome IDs returned by the database — effectively arbitrary. The REPORT implies a meaningful rank-ordering but does not disclose this. A secondary sort criterion (e.g., strain name alphabetical, isolation site designation) would be more principled, or the REPORT should state that the top 20 are unordered within the tied tier.

10. **`Paenarthrobacter`, `Kitasatospora`, and `Leifsonia` are unscored.** These genera are absent from the `tractable_genera` dict in NB02 Cell 8, so they receive `genus_tractability = 0`. `Paenarthrobacter aurescens FW305-123` (genome_ids 243, 1559) carries the complete 4-gene pathway and is closely related to *Arthrobacter* (which scores 2). `Kitasatospora sp. OK780` (genome_id 2776) belongs to Streptomycetaceae. These candidates may be unduly deprioritised. At minimum, the REPORT should note that the tractability rubric does not cover all Actinobacteria genera.

The relevant pitfall from `docs/pitfalls.md` — strain name collisions when linking ENIGMA isolates to external databases — does not apply here because the analysis stays within the ENIGMA Genome Depot. The notebook-output commit pitfall is avoided: both notebooks are committed with outputs.

## Findings Assessment

**Conclusions are well-supported.** The headline findings (163 genome records MAI-positive, 134 with complete 4-gene pathway, top 20 are all *Streptomyces* with score 60/60) are directly verifiable from notebook outputs and saved data files. The literature context (Wang 2007, Park & Roe 2008, Passari 2025) is relevant and correctly cited. The unexpected Rhizobiaceae observation is flagged with appropriate skepticism and two concrete testable hypotheses (annotation cross-reactivity, HGT).

**Limitations are honestly stated.** The REPORT correctly acknowledges missing genome quality metrics, unresolved taxonomic labels for 77 isolates, absent isolation site metadata, annotation-only detection, and the unavailability of Jen's isolate list. These gaps are not papered over.

**One limitation understated.** The genome-vs-strain-record issue (see concern #1) should be added to Limitations. Stating "163 genomes" rather than "163 genome records, of which ~136 correspond to distinct organism names" modestly overstates the breadth of the candidate set and affects how a collaborator would estimate the scale of culture requests.

## Discoveries

Both `## Discoveries` entries in REPORT.md are appropriate for cross-project surfacing:

- **Discovery 1** ("5.6% of ENIGMA Genome Depot isolates carry K16163, predominantly *Streptomyces* from Oak Ridge") is directly supported by NB01 outputs. Scope is accurate (ENIGMA Genome Depot specifically). Minor refinement: qualifying "163 genome records" rather than "isolates" would make the claim more precise given the duplicate assemblies documented above.

- **Discovery 2** ("MAI prevalence in ENIGMA Alphaproteobacteria exceeds <1% genome-scale expectation; annotation cross-reactivity or HGT should be investigated") is supported by the taxonomy table (18 *Rhizobium* + 4 *Ensifer* confirmed in NB01 output). The validation caveat is appropriately built into the claim.

Neither discovery duplicates known results from prior projects. Both are load-bearing across projects.

## Suggestions

1. **(Critical) Disclose genome-vs-strain distinction.** In REPORT.md Key Findings and Results table, change "163 ENIGMA isolates" to "163 ENIGMA genome records (136 unique organism names)" and note that the ENIGMA Genome Depot contains multiple assemblies per strain. Verify whether 2,925 also contains duplicate entries and adjust the denominator or report both.

2. **(Critical) Remove or create `enigma_genome_qc.parquet`.** Either add a missing `to_parquet` call in NB02 (if QC data was computed), or remove the reference from NB02 Cell 16's summary print. Currently the output log claims a file exists that is absent from disk.

3. **(Important) Fix stale file references in NB01 Cell 17.** Remove `enigma_mai_ko_hits.parquet` and `enigma_mai_product_hits.parquet` from the summary print — neither was created. Replace with the files that do exist (`enigma_all_genomes.parquet`, `enigma_mai_hits.csv`, `enigma_pathway_completeness.csv`).

4. **(Important) Acknowledge ≥2-evidence criterion deviation in REPORT.md.** Add a sentence to Limitations noting that the research plan's requirement for ≥2 independent annotation signals was reduced to a single KO hit because the ENIGMA Genome Depot browser tables do not expose InterPro domains or free-text product name search.

5. **(Important) Add `## Reproduction` section to README.md.** Specify: NB01 requires a live Spark session on JupyterHub for the initial query; NB02 can run locally from cached CSV/parquet with no Spark dependency after NB01 has been executed once.

6. **(Important) Fix inconsistent related-project name.** README references `mycothiol_detox_module`; REPORT.md Interpretation references `metal_detox_genes_with_phylogenetic_bias`. Reconcile to the correct current project ID throughout both files.

7. **(Moderate) Add `pyarrow>=12.0` to `requirements.txt`.** Both notebooks use parquet I/O but the dependency is undeclared.

8. **(Moderate) Fix README Quick Links: `REVIEW.md` → `REVIEW_1.md`.**

9. **(Moderate) Note shortlist tie-breaking logic.** Add a sentence in NB02 or REPORT.md explaining that within the top-tier score (60/60), candidates are listed in database genome_id order (arbitrary). Either apply a meaningful secondary sort or state explicitly that all 20 entries are equivalent candidates.

10. **(Nice-to-have) Expand `tractable_genera` or document the gap.** `Paenarthrobacter` (full 4-gene pathway, 2 genome records), `Kitasatospora` (Streptomycetaceae, complete pathway), and `Leifsonia` appear in the MAI hits but score 0 for genus tractability. Either add these to the dict with appropriate scores, or note in the REPORT that the rubric does not cover all Actinobacteria genera.

11. **(Nice-to-have) Add a taxonomy summary figure from NB01.** The project has only 1 figure (NB02 scatter). A bar chart of MAI-positive hits by genus/phylum from NB01 would let readers immediately see the Actinobacteria-vs-Alphaproteobacteria breakdown without reading the table.

## Review Metadata
- **Reviewer**: BERIL Automated Review (Claude, claude-sonnet-4-6)
- **Date**: 2026-06-25
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, references.md, requirements.txt, beril.yaml, 2 notebooks (01_enigma_depot_query.ipynb: 17 cells, 8 with outputs; 02_candidate_ranking.ipynb: 16 cells, 9 with outputs), 4 data files, 1 figure, docs/pitfalls.md
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.

<!-- report_hash: sha256:02ce221ec16b616b4f612e1f09810371cb5d07044d0588f9e919134e5e24b6e3 -->

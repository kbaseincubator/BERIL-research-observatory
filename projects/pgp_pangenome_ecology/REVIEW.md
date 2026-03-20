---
reviewer: BERIL Automated Review
date: 2026-03-20
project: pgp_pangenome_ecology
---

# Review: PGP Gene Distribution Across Environments & Pangenomes

## Summary

This is a high-quality, well-scoped project that tests four clearly stated hypotheses about plant growth-promoting (PGP) bacterial genes across the full BERDL pangenome (293K genomes, 27K species). The three-file structure (README / RESEARCH_PLAN / REPORT) is correctly implemented, the literature grounding is strong, and the downstream analysis notebooks (NB02–NB05) all have saved outputs that faithfully reproduce the numbers reported. The most significant problem is in NB01: two cells fail with `NameError` in the saved state and five further cells have no outputs at all, leaving the data-extraction notebook's audit trail incomplete. This is almost certainly caused by a known SQL pitfall — an unquoted `order` reserved word in the Spark query — that was identified in the RESEARCH_PLAN but not applied in the implemented SQL. Correcting NB01 and re-executing it to capture clean outputs is the priority action; everything downstream is sound.

---

## Methodology

**Research question and hypotheses.** The research question is precise and testable. All four hypotheses (H1 co-occurrence syndrome, H2 soil enrichment, H3 HGT/accessory status, H4 trp→ipdC coupling) are stated in falsifiable form with expected directions and effect sizes. This is exemplary planning.

**Approach.** The analytical pipeline is appropriate for each hypothesis:
- H1: Pairwise Fisher's exact tests on a binary species × focal-gene matrix, BH-FDR corrected, with log2-OR heatmap — standard and correct for presence/absence pangenome data.
- H2: Per-gene Fisher's exact + logistic regression with phylum fixed effects + strict-rhizosphere sensitivity analysis — good choice of confounders.
- H3: Per-gene chi-square vs genome-wide cluster baseline + Spearman openness correlation — sound design; the code correctly handles the singleton-within-auxiliary nesting of flags.
- H4: Fisher's exact + logistic regression + stratified analysis + negative control — a well-structured causal test.

**Data sources.** All tables are from `kbase_ke_pangenome` and are clearly identified with field names and scale in the RESEARCH_PLAN table. The direct `gtdb_metadata.ncbi_isolation_source` column is correctly preferred over the EAV `ncbi_env` table (documented pitfall avoided).

**Reproducibility of approach.** The README contains an explicit `## Reproduction` section with runtime estimates and Spark/local distinctions for each notebook. This is exactly the right information for someone trying to re-run the pipeline.

---

## Code Quality

### NB01 — Data Extraction (Spark): ❌ Execution errors in saved state

**Bug: `NameError: name 'env_df' is not defined` in cells 9 and 11.** The Spark query in cell 8 (environment extraction) has no saved output, indicating the cell did not execute successfully in the run that was committed. Cells 9 and 11, which depend on `env_df`, then fail visibly:

```
NameError: name 'env_df' is not defined
```

**Root cause: unquoted `order` reserved word.** Cell 8 contains:
```sql
SELECT m.accession AS genome_id, m.ncbi_isolation_source,
       t.phylum, t.class, t.order, t.family, t.genus, t.species, ...
```
The `t.order` column is used without backtick quoting. The RESEARCH_PLAN itself explicitly documents this as Pitfall #7: *"`order` column: backtick-quote in SQL (reserved word)."* This known pitfall was not applied in the implemented query, and is the most likely cause of the Spark query failure.

**Cascade of missing outputs.** Because cells 9 and 11 fail, cells 13 (pangenome stats), 15 (GapMind trp), 17 (validation checkpoint), 18 (summary figure), and 19 (final summary) all have no saved outputs. This means the following are unverifiable from the notebook alone:
- That pangenome_stats.csv was produced correctly (genome-wide baseline of 46.8% core)
- That trp_completeness.csv contains the expected 27,690 species
- The validation that nifH cluster count is 2,756 (noted as diverging 43% from the expected ~1,913 — an unexplained discrepancy worth flagging)
- The summary figure `figures/nb01_pgp_prevalence.png` (absent from the figures/ directory)

Despite these execution failures, the output data files (`genome_environment.csv`, `species_environment.csv`, `pangenome_stats.csv`, `trp_completeness.csv`) do exist with the expected row counts — confirming they were produced in a prior successful session. All downstream notebooks (NB02–NB05) load from these CSVs and run cleanly.

### NB02 — PGP Co-occurrence (H1): ✅ Correct and complete

All cells executed with outputs. Fisher's exact tests, BH-FDR correction, and OR heatmap are correctly implemented. The `fisher_pair()` function constructs the 2×2 contingency table correctly (`[[both, a_only], [b_only, neither]]`). Reported numbers (pqqC × acdS OR = 7.24, n = 286, q = 1.2e-83) match the notebook output exactly. Figures saved to disk. ✓

### NB03 — Environmental Selection (H2): ✅ Correct and complete

All cells executed with outputs. Environment enrichment test function is correctly implemented, including correct contingency table orientation (soil+ vs soil-, gene+ vs gene−). Phylum-stratified analysis, logistic regression with family-level fixed effects, and strict-rhizosphere sensitivity analysis all execute. Results in the REPORT match notebook outputs precisely (acdS OR = 7.02, soil sensitivity OR = 10.59). ✓

One noteworthy result: the phylum-controlled logistic regression for ipdC returns OR = 0.558, p = 0.027, flagging a soil *depletion* of ipdC — opposite to the main enrichment direction. This is correctly handled in the sensitivity analysis and discussed in the REPORT as a soil-reversal finding.

### NB04 — Core vs Accessory (H3): ✅ Correct and complete

All cells executed with outputs. The code correctly handles the singleton-within-auxiliary structure of the `gene_cluster` flags using `(is_auxiliary & ~is_singleton)` for true auxiliary and `is_singleton` separately. Chi-square tests and the Spearman openness correlation (ρ = −0.195, p = 2.0e-97) match REPORT values. ✓

### NB05 — Tryptophan → IAA (H4): ✅ Mostly correct, one silent failure unreported

All cells have outputs. Fisher's exact, logistic Model 1 (trp only, OR = 2.808, p = 1.36e-08), and stratified analysis are correct. The negative control (tyr → ipdC, OR = 3.620, p = 2.32e-11) unexpectedly passes significance — the notebook comment correctly flags this as contrary to expectation, and the REPORT provides a mechanistically sound explanation (TyrR aromatic amino acid regulation).

**Unreported Model 3 failure.** Cell 7 shows:
```
Model 3 failed: Singular matrix
```
The phylum + is_soil logistic regression fails due to quasi-complete separation (too many phyla relative to ipdC prevalence). This failure is not mentioned in the REPORT, which refers only to "logit OR = 2.81" (Model 1). The omission is not harmful to the conclusions but should be disclosed.

### SQL and pitfall compliance

| Pitfall | Status |
|---------|--------|
| `ncbi_isolation_source` direct column (not EAV) | ✅ Correctly used |
| `metabolic_category = 'aa'` for GapMind | ✅ Correctly used |
| `sequence_scope = 'core'` for GapMind | ✅ Correctly used |
| `order` reserved word requires backtick quoting | ❌ Missing in NB01 cell 8 |
| JOIN on `genome_id` (not `gtdb_taxonomy_id`) | ✅ Correctly used in cell 8 |
| `gapmind_pathways.clade_name` = `gtdb_species_clade_id` format | ✅ Used as `clade_name AS gtdb_species_clade_id` |
| CAST pangenome numeric columns from Spark | ✅ CASTed in NB01 cell 13 |

---

## Findings Assessment

**H1 (PGP syndrome): SUPPORTED.** The pqqC × acdS co-occurrence (OR = 7.24) is the strongest result in the project and well-supported by both statistics and existing literature (Vejan et al. 2016). The finding that nifH is negatively associated with pqqC and hcnC — forming a distinct ecological guild — is a genuine novel contribution at this scale. The REPORT's nuance (only 157 species carry ≥3 traits, and the "syndrome" is more a pqqC–acdS module than a broad suite) is honestly stated.

**H2 (Soil enrichment): SUPPORTED.** acdS OR = 7.0 in soil is a large and robust effect that survives phylogenetic control (OR = 6.98 in logistic regression). The strict rhizosphere sensitivity (OR = 10.6) strengthens the finding. The unexpected nifH *depletion* in soil is correctly presented and cited against the literature (Wardell et al. 2022). The ipdC non-enrichment in soil is puzzling given H4's finding that soil species show a reversal; the REPORT addresses this but the explanation is necessarily speculative.

**H3 (HGT/accessory): REJECTED.** The REPORT honestly and clearly rejects H3. All 13 PGP genes are significantly MORE core than the 46.8% genome-wide baseline. The REPORT's interpretation (vertical inheritance as the primary mode) is well-supported and appropriately caveated (pqqD as an outlier). The pangenome-openness correlation (ρ = −0.195) is an important independent corroboration.

**H4 (trp → ipdC coupling): PARTIALLY SUPPORTED.** The core Fisher's result (OR = 2.81, p = 6.3e-10) and the soil reversal are both faithfully reported. The REPORT's mechanistic explanation for the failed negative control (TyrR aromatic amino acid regulation; Ryu & Patten 2008, PMID 18757531) is scientifically sound and converts a potential embarrassment into a novel finding. The REPORT correctly recommends controlling for genome-wide pathway completeness as a future direction.

**Minor factual error in REPORT.** The REPORT states: *"ipdC is the rarest focal gene (226 species, 2.0%)."* However, NB01 cell 3 shows 226 **gene clusters** for ipdC, while NB01 cell 6 shows **214 species** carry ipdC (confirmed by NB05: "ipdC present in: 214 species"). The correct figure is 214 species (1.9%), not 226 species. The 2.0% percentage in the same sentence is also slightly inconsistent (214/11272 = 1.9%).

**Limitations.** The Limitations section in the REPORT is specific and honest: environment classification coverage (5.9% soil/rhizosphere), gene-name-only search, no functional validation of truncated genes, low ipdC prevalence limiting stratified power, and the GapMind confound. All are relevant and correctly assessed.

---

## Suggestions

1. **[Critical] Fix `t.order` SQL in NB01 cell 8.** Backtick-quote the reserved word: change `t.order` to `` t.`order` `` in the Spark SQL query. This is documented as Pitfall #7 in the RESEARCH_PLAN but was not applied in the code. After fixing, re-execute NB01 on JupyterHub to regenerate `genome_environment.csv` and capture clean outputs for cells 8–19.

2. **[Critical] Re-execute NB01 to capture saved outputs.** After fixing the SQL bug, run NB01 end-to-end on BERDL JupyterHub and save the notebook with outputs. Cells 13 (pangenome stats), 15 (GapMind trp), 17 (validation checkpoint), 18 (summary figure), and 19 (final summary) currently have no outputs, making them unverifiable. The `figures/nb01_pgp_prevalence.png` file is also missing.

3. **[Moderate] Explain the nifH cluster count discrepancy.** NB01 cell 4 validation notes "nifH clusters = 2,756 (expected ~1,913)" — a 43% excess over the RESEARCH_PLAN estimate — without explanation. Add a comment or markdown cell explaining why the observed count diverges from the prior estimate (e.g., updated database since the plan was written, or the prior estimate assumed a different query scope). The discrepancy is not necessarily a problem, but it should not be flagged as a failed validation without context.

4. **[Moderate] Disclose the Model 3 singular matrix failure in the REPORT.** NB05 cell 7 records "Model 3 failed: Singular matrix" (phylum + is_soil regression for ipdC). The REPORT should note that Model 3 was attempted but failed due to quasi-complete separation, and that conclusions are therefore based on the simpler Model 1 (trp only) and Model 2 (trp + is_soil). Add a sentence to the H4 section and/or Limitations.

5. **[Minor] Correct the ipdC species count in the REPORT.** Change *"ipdC is the rarest focal gene (226 species, 2.0%)"* to *"ipdC is the rarest focal gene (214 species, 1.9%)"*. The number 226 refers to gene clusters, not species; the correct species count (214) is shown in NB01 cell 6 and NB05 cell 1.

6. **[Minor] Address the ipdC soil-enrichment paradox.** The H2 analysis finds ipdC non-enriched in soil (OR = 0.79, ns) while the H4 stratified analysis shows the trp→ipdC positive coupling is present only in *non-soil* species. The REPORT mentions the soil-reversal but does not explicitly reconcile it with H2's null result for ipdC soil enrichment. A brief cross-reference in the H2 or H4 interpretation section would help the reader.

7. **[Nice-to-have] Add `nb01_pgp_prevalence.png` to figures/ or remove its reference.** NB01 cell 18 generates and saves `figures/nb01_pgp_prevalence.png`, but it does not exist in the repository because NB01 never completed that cell. Either include it after re-executing NB01, or remove the `plt.savefig` call if the figure is not needed for the REPORT.

---

## Review Metadata

- **Reviewer**: BERIL Automated Review
- **Date**: 2026-03-20
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, 5 notebooks (NB01–NB05), 11 data files, 6 figures, requirements.txt, docs/pitfalls.md
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.

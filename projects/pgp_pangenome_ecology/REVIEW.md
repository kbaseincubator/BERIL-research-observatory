---
reviewer: BERIL Automated Review
date: 2026-03-20
project: pgp_pangenome_ecology
---

# Review: PGP Gene Distribution Across Environments & Pangenomes

## Summary

This is a well-executed, scientifically rigorous project that tests four clearly stated hypotheses about plant growth-promoting (PGP) bacterial genes across the full BERDL pangenome (293K genomes, 27K species). The three-file structure (README / RESEARCH_PLAN / REPORT) is correctly implemented, the literature grounding is excellent, and all five notebooks have saved outputs — data was retrieved via a cache-check pattern, making NB02–NB05 runnable locally without Spark. All seven expected figures are present. REPORT numbers match notebook outputs exactly for every tested hypothesis. The two most notable issues are: (1) a latent SQL bug in NB01 (`t.order` is an unquoted reserved word that the RESEARCH_PLAN itself flagged as Pitfall #7 — if the cache is cleared and Spark re-queried, the query will fail); and (2) the logistic Model 2 output shows OR_trp = 2.874 while the REPORT text cites logit OR = 2.81 — this appears to conflate Model 1 and Model 2 OR values and should be clarified. Both are correctable. The science is sound and the findings are clearly communicated.

---

## Methodology

**Research question and hypotheses.** The research question is precise and testable. All four hypotheses are stated in falsifiable form with expected directions and effect sizes in RESEARCH_PLAN.md, and REPORT.md addresses each one with a clear verdict (H1 supported, H2 supported, H3 rejected, H4 partially supported). The H3 rejection is presented honestly and the unexpected result (PGP genes MORE core than genome-wide baseline, not less) is well-argued.

**Analytical approach.** Each hypothesis has an appropriate method:
- H1: Pairwise Fisher's exact tests on a binary species × focal-gene matrix, BH-FDR corrected with a log2-OR heatmap — standard and correct for presence/absence pangenome data.
- H2: Per-gene Fisher's exact + logistic regression with phylum fixed effects + strict-rhizosphere sensitivity analysis — well-chosen confounders; the phylum-stratified analysis (18 phyla with ≥50 species) is a genuine check on phylogenetic confounding.
- H3: Per-gene chi-square vs genome-wide cluster baseline + Spearman openness correlation — correct design; the code correctly disentangles auxiliary-but-not-singleton from the raw `is_auxiliary` flag.
- H4: Fisher's exact + three logistic models + stratified analysis + negative control — a thorough causal test. The mechanistic explanation for the failed negative control (TyrR aromatic amino acid regulation) converts a potential weakness into a novel finding.

**Data sources.** All seven tables from `kbase_ke_pangenome` are clearly identified in RESEARCH_PLAN.md with field names and scale. The direct `gtdb_metadata.ncbi_isolation_source` column is correctly preferred over the EAV `ncbi_env` table, consistent with the documented pitfall. The GapMind query correctly uses `MAX(score_simplified) … GROUP BY clade_name, pathway` to aggregate across multiple rows per species-pathway pair.

**Reproducibility.** The README contains an explicit `## Reproduction` section with per-notebook runtime estimates (NB01: ~20 min Spark; NB02–NB05: ~5–10 min local). The Spark/local distinction is clearly marked. The NB01 cache-check pattern (`if os.path.exists(path): load from CSV else run Spark`) means the full pipeline can be reproduced locally after NB01 has been run once on JupyterHub — this is a good design choice.

---

## Code Quality

### NB01 — Data Extraction (Spark): ⚠️ Latent SQL bug; outputs present via cache

All cells executed with outputs. The notebook loaded all six data files from disk cache (`pgp_clusters.csv`, `species_pgp_matrix.csv`, `genome_environment.csv`, `species_environment.csv`, `pangenome_stats.csv`, `trp_completeness.csv`) rather than running live Spark queries, so the analysis chain is unbroken. However, a latent bug will cause failure if the cache is cleared and NB01 is re-run from scratch:

**Latent bug: unquoted `order` reserved word in NB01 cell 8.**
```sql
-- NB01 cell 8 (current code — will FAIL when run live against Spark):
SELECT m.accession AS genome_id, ...,
       t.phylum, t.class, t.order, t.family, ...
```
The column `order` is a SQL reserved word and must be backtick-quoted in Spark SQL: `` t.`order` ``. This is explicitly documented as Pitfall #7 in RESEARCH_PLAN.md: *"`order` column: backtick-quote in SQL (reserved word)."* The fix was planned but not applied to the code. Because `genome_environment.csv` already existed when the notebook was committed, the Spark branch was never taken and the bug was never triggered.

**Additional NB01 observations:**
- The nifH cluster count (2,756) differs from the RESEARCH_PLAN estimate (~1,913). NB01 cell 4 explains this inline as GTDB database growth. This is acceptable and honestly documented.
- Pangenome numeric columns are correctly CAST to `INT`/`DOUBLE` in the Spark query (NB01 cell 13), avoiding the string-typed-numeric pitfall.
- The known PGPB genus sanity check (NB01 cell 17) confirms Azospirillum leads with median 8 PGP genes/species, consistent with its role as the model PGPB genus.

### NB02 — PGP Co-occurrence (H1): ✅ Correct and complete

All cells have saved outputs. The `fisher_pair()` function builds the 2×2 contingency table correctly (`[[both, a_only], [b_only, neither]]`). BH-FDR correction is applied across all 10 pairs. Reported numbers in REPORT (pqqC × acdS OR = 7.24, n = 286, q = 1.2e-83; nifH × hcnC OR = 0.23, q = 5.8e-29) match notebook output exactly.

### NB03 — Environmental Selection (H2): ✅ Correct and complete

All cells have saved outputs. The `enrichment_test()` function correctly orients the contingency table (soil+ vs soil−, gene+ vs gene−). The phylum-stratified analysis runs on 18 qualifying phyla and the strict-rhizosphere sensitivity analysis correctly re-runs within the soil subset. All reported effect sizes (acdS OR = 7.02, q = 5.15e-62; strict rhizosphere OR = 10.59) match notebook outputs.

The phylum-controlled logistic regression for ipdC returns OR = 0.558, p = 0.027, indicating soil *depletion* of ipdC — opposite to the raw Fisher's direction (OR = 0.79, ns). The REPORT discusses the soil reversal in the H4 context but does not explicitly reconcile why the phylum-controlled H2 logit shows soil depletion while the raw H2 Fisher's test is non-significant. See Suggestion 4.

### NB04 — Core vs Accessory (H3): ✅ Correct and complete

All cells have saved outputs. The code correctly partitions `is_auxiliary & ~is_singleton` for true auxiliary clusters and `is_singleton` separately (consistent with pangenome table semantics documented in pitfalls.md: singletons ⊂ auxiliary). Chi-square tests compare observed core/non-core counts against the weighted genome-wide baseline (46.8% core), which is computed correctly from summing across all species in `pangenome_stats`. The Spearman correlation (ρ = −0.195, p = 2.0e-97) matches REPORT.

### NB05 — Tryptophan → IAA (H4): ✅ Mostly correct; one REPORT citation inconsistency

All cells have saved outputs. Fisher's exact test (OR = 2.808, p = 6.31e-10), logistic Model 1 (OR = 2.808, p = 1.36e-08), logistic Model 2 (OR_trp = 2.874), and stratified results (soil: OR = 0.30, p = 0.02; non-soil: OR = 3.56, p = 7.69e-13) are all present and clearly shown.

**REPORT logit OR citation ambiguity.** NB05 cell 7 shows: Model 1 OR = 2.808; Model 2 OR_trp = 2.874. The REPORT H4 section cites: *"logit OR = 2.81, 95% CI 1.97–4.01, p = 1.4e-08."* The OR of 2.81 and CI match Model 1. However, the sentence immediately precedes reference to Model 2 (trp + is_soil). The REPORT should clarify which model's OR is being cited (Model 1 for the OR, or Model 2 if that is preferred). The difference is small (2.808 vs 2.874) but should be explicit.

**Model 3 failure correctly disclosed.** The REPORT states: *"A phylum + soil logistic model (Model 3) was attempted but failed due to quasi-complete separation caused by ipdC's rarity across phyla (214 species, 1.9%)"* — this is accurate and appropriately disclosed.

**Negative control result is interpretable.** The tyr → ipdC association (OR = 3.62) being similar to trp → ipdC (OR = 2.81) is correctly explained via TyrR regulatory circuitry (Ryu & Patten 2008, PMID 18757531). This is a well-handled result.

### SQL and pitfall compliance

| Pitfall from docs/pitfalls.md | Status |
|-------------------------------|--------|
| `ncbi_isolation_source` direct column (not EAV `ncbi_env`) | ✅ Correctly used |
| `metabolic_category = 'aa'` for GapMind amino acid pathways | ✅ Correctly used |
| `sequence_scope = 'core'` for GapMind | ✅ Correctly used |
| GapMind multiple rows per genome-pathway: use `MAX()` + `GROUP BY` | ✅ Correctly handled |
| JOIN taxonomy on `genome_id` (not `gtdb_taxonomy_id`) | ✅ Correctly used |
| CAST pangenome numeric columns from Spark string types | ✅ Applied in NB01 cell 13 |
| `order` reserved word requires backtick quoting in Spark SQL | ❌ Unquoted `t.order` in NB01 cell 8 (latent bug) |

---

## Findings Assessment

**H1 (PGP syndrome): SUPPORTED.** The pqqC × acdS co-occurrence (OR = 7.24, n = 286) is the strongest result and well-supported by literature. The finding that nifH is *negatively* associated with pqqC (OR = 0.57) and hcnC (OR = 0.23) — creating a separate diazotroph guild — is a genuine and novel contribution at this scale. The nuance (only 157 species carry ≥3 traits; the "syndrome" is primarily a pqqC–acdS module) is honestly stated.

**H2 (Soil enrichment): SUPPORTED.** The acdS soil enrichment (OR = 7.02) surviving phylum fixed effects (logit OR = 6.98) and strict-rhizosphere sensitivity (OR = 10.6) is a robust, highly significant result. The unexpected nifH *depletion* in soil is correctly presented with appropriate literature support (Wardell et al. 2022). Acknowledging the NCBI clinical sampling bias (only 5.9% of species classified as soil/rhizosphere-dominant) as a limitation is appropriate and honest.

**H3 (HGT/accessory): REJECTED.** All 13 PGP genes are significantly MORE core than the 46.8% genome-wide baseline. This clear rejection of the HGT hypothesis is honestly presented. The pqqD outlier (55.5% core, highest singleton fraction) is appropriately called out. The pangenome openness correlation (ρ = −0.195) provides independent corroboration. The REPORT's interpretation — stable ecological specialization rather than HGT-driven gene accumulation — is well-argued.

**H4 (trp → ipdC coupling): PARTIALLY SUPPORTED.** The Fisher's result (OR = 2.81, p = 6.3e-10) is solid. The soil-reversal finding (in soil species, trp-complete predicts *lower* ipdC prevalence, OR = 0.30) is a genuinely interesting secondary result. The REPORT's mechanistic interpretation (soil PGPB obtain tryptophan exogenously from root exudates, relaxing biosynthetic pressure while retaining ipdC) is speculative but scientifically plausible and correctly flagged as hypothesis-generating. The Limitations section correctly identifies that controlling for genome-wide pathway completeness would be needed to isolate the specific trp–ipdC signal.

**REPORT accuracy:** Checked key numbers — all match notebook outputs exactly (pqqC × acdS OR, nifH depletion, acdS soil enrichment, chi-square baselines, Spearman ρ, Fisher H4 OR/p, stratified ORs). The REPORT correctly distinguishes ipdC species count (214) from cluster count (226). No unsupported numbers found.

**Limitations section** is specific and honest: environment classification noise, gene-name-only search (misses product-description-annotated genes), no functional validation of truncated/pseudogenized genes, low ipdC prevalence limiting stratified power, and the GapMind pathway-completeness confound. All relevant.

---

## Suggestions

1. **[Critical] Fix the `t.order` reserved word in NB01 cell 8.** Change `t.order` to `` t.`order` `` in the Spark SQL query. This is exactly Pitfall #7 from the RESEARCH_PLAN but was not applied to the implemented code. The bug is currently latent because `genome_environment.csv` is cached; it will surface if the cache is cleared or the query is re-run. After fixing, re-execute NB01 on BERDL JupyterHub and save the notebook with live Spark outputs to replace the cache-only run.

2. **[Moderate] Clarify the logit OR citation in the H4 REPORT section.** The REPORT cites "logit OR = 2.81, 95% CI 1.97–4.01, p = 1.4e-08" — these values match Model 1 (trp only). However, Model 2 (trp + is_soil) gives OR_trp = 2.874. The text should explicitly name the model being cited (e.g., "Model 1: trp only, OR = 2.81") to avoid ambiguity about whether soil adjustment was applied.

3. **[Moderate] Clarify the ipdC soil enrichment paradox between H2 and H4.** H2 finds ipdC non-enriched in soil (raw OR = 0.79, ns; phylum-controlled OR = 0.558, p = 0.027 soil-depleted), while H4's stratified analysis finds the trp→ipdC positive coupling *only* in non-soil species. These two results are related but the REPORT discusses them in separate sections without a cross-reference. A brief sentence in either the H2 or H4 interpretation section explicitly connecting the ipdC soil-depletion pattern across both analyses would help readers follow the logic.

4. **[Minor] Explain the nifH cluster count discrepancy more prominently.** NB01 cell 4 notes "nifH clusters = 2,756 (expected ~1,913 at plan time)" — a 43% excess — in a print statement. The inline explanation ("reflects DB growth since plan was written") is sufficient for a notebook but deserves a brief acknowledgment in the RESEARCH_PLAN's Revision History or the REPORT's Dataset Scale section, since the plan's expected-outcome section (H1: "nifH × pqqC pair co-occurrence supported") was calibrated against the older count.

5. **[Minor] Add a comment explaining why `score_simplified` values are binary (0.0 / 1.0).** NB01 cell 15 extracts GapMind trp completeness via `MAX(score_simplified)` and NB05 cell 3 shows the values are only `[0.0, 1.0]`. The `score_simplified` column's binary nature is not explained. A brief comment noting that GapMind `score_simplified` encodes pathway completeness as 0/1 (from `sequence_scope = 'core'`) would help readers who expect a continuous score.

6. **[Nice-to-have] Consider adding a figure to visualize the nifH ecological guild separation.** The diazotroph-vs-non-diazotroph finding from H1 and H2 (nifH negatively associated with pqqC/hcnC; nifH depleted in soil) is a strong secondary finding described primarily in prose. A simple phylum-stratified bar chart showing nifH vs pqqC/acdS prevalence across the top 8 phyla would make this guild-separation result visually striking and more accessible to readers.

---

## Review Metadata

- **Reviewer**: BERIL Automated Review
- **Date**: 2026-03-20
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, 5 notebooks (NB01–NB05), 11 data files, 7 figures, requirements.txt, docs/pitfalls.md
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.

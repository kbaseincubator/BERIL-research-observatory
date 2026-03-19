---
reviewer: BERIL Automated Review
date: 2026-03-19
project: amr_environmental_resistome
---

# Review: Environmental Resistome at Pangenome Scale

## Summary

This is a well-executed, large-scale analysis testing whether antimicrobial resistance gene profiles differ between ecological niches across ~15,000 bacterial species and 293K genomes. The project excels in its clear hypothesis-driven structure (H1–H4), thorough phylogenetic controls at both phylum and family level, sensitivity analyses across majority-vote thresholds, and honest acknowledgment of limitations and effect sizes. All four notebooks have saved outputs with figures, and the REPORT is comprehensive with proper literature context. The main areas for improvement are: (1) the Reproduction section is unfinished, (2) several analyses promised in the RESEARCH_PLAN were not performed (PCoA, PERMANOVA, environment-specific gene identification, true within-species AMR comparison), (3) a likely pandas column-alignment bug in the mechanism classifier leaves ~19% of AMR clusters with NaN mechanism, and (4) the NB03 "within-species" analysis is actually a between-species comparison of clinical dominance, not a per-genome within-species comparison.

## Methodology

**Strengths:**
- Research question is clearly stated, testable, and well-motivated by prior literature (Gibson et al. 2015, Forsberg et al. 2014, Jiang et al. 2024).
- Four hypotheses (H1–H4) are specific and falsifiable, with expected outcomes documented in advance.
- Data sources are explicitly identified with table names, row counts, and join paths.
- Phylogenetic confounding is addressed with stratified analysis within 6 phyla and 141 families — a rigorous approach that goes beyond most similar studies.
- Sensitivity analysis at 50%/60%/75%/90% majority-vote thresholds demonstrates robustness of H1.
- Effect sizes (η²) are reported alongside p-values throughout, appropriately noting that with 14K species even tiny effects are significant.

**Gaps:**
- **Reproduction section is TBD** (README.md line 31). The README says "TBD — add prerequisites and step-by-step instructions after analysis is complete." The analysis is complete, but this section was never filled in. There is no guidance on which notebooks require Spark vs run locally, expected runtimes, or execution order.
- **Several planned analyses were not performed.** The RESEARCH_PLAN specifies: (a) PCoA ordination of AMR profiles colored by environment (§NB02 item 4), (b) PERMANOVA with family as covariate (§NB02 item 5), (c) environment-specific AMR gene identification via Fisher's exact test per gene with BH-FDR (§NB02 item 6), and (d) within-species Fisher's exact tests and Mantel tests (§NB03 items 3–4). None appear in the notebooks. The stratified Kruskal-Wallis tests are a reasonable substitute for PERMANOVA but should be documented as such.
- **MAG vs isolate assessment was planned but not done.** RESEARCH_PLAN §NB01 item 7 calls for assessing MAG composition and potentially excluding MAGs, but this is absent from NB01.
- **Archaea consideration** was flagged in the research plan (Confounder #9) but not addressed in any notebook.

## Code Quality

**SQL and data extraction (NB01):**
- SQL queries are correct: the `ncbi_env` EAV pivot via `CASE WHEN ... GROUP BY` is properly implemented (cell-8), matching the documented pitfall for this table.
- The `genome.ncbi_biosample_id → ncbi_env.accession` join path is correct per `docs/pitfalls.md`.
- `pd.to_numeric()` is used appropriately for string-typed numerics (NB02 cell-1).
- AlphaEarth NaN filtering is properly implemented with `~df[emb_cols].isna().any(axis=1)` (NB04 cell-3).
- The GTDB taxonomy join uses `genome_id`, correctly avoiding the `gtdb_taxonomy_id` pitfall.

**Potential mechanism classifier bug (NB01 cell-5):**
The fallback product-based classifier may have a pandas column-alignment issue. The assignment:
```python
amr_clusters.loc[mask, ['amr_class', 'amr_mechanism']] = amr_clusters.loc[mask, 'amr_product'].apply(
    lambda p: pd.Series(classify_amr_product(p)))
```
The `.apply()` returns a DataFrame with columns `0` and `1`, but the `.loc` target expects columns `amr_class` and `amr_mechanism`. Pandas performs label-based alignment, so mismatched column names would write NaN instead of the classified values. Evidence: the mechanism `value_counts()` sums to 67,458 but total rows are 83,008 — the missing 15,550 (~19%) may have NaN mechanism. These would propagate silently: `n_other_mech` in cell-14 counts `x.isin(['other', 'unknown'])` which excludes NaN, so ~19% of AMR clusters may be absent from all mechanism-level analyses. The `resistance_type` column (antibiotic vs metal) sums correctly to 83,008 because NaN `amr_class` evaluates to `not in METAL_CLASSES` → 'antibiotic', masking the issue.

**NB02 summary variable overwrite (cell-18):**
The variable `kw_p` is overwritten by the sensitivity analysis loop in cell-16. The final summary (cell-18) prints `kw_p=4.497e-75` (the 90% threshold result), not the original H1 p-value of `9.446e-167` from cell-3. The `eta_sq` variable is correctly from the original test. This mixes results from different analyses in the summary.

**Tetracycline mechanism classification:**
All tetracycline resistance genes (including ribosomal protection proteins like tet(M), tet(O)) are classified as "efflux" via `CLASS_TO_MECHANISM['tetracycline'] = 'efflux'`. Ribosomal protection is a target modification mechanism, not efflux. This misclassification could inflate efflux counts and deflate target modification counts.

**NB04 Mantel test permutations:**
The RESEARCH_PLAN specifies 9,999 permutations for the Mantel test, but NB04 uses only 999. With the observed r=0.098 yielding p=0.001, 999 permutations gives adequate resolution, but the deviation from the plan should be noted.

**Notebook organization:**
All notebooks follow a clean setup → query → analysis → visualization → save flow. Markdown headers separate logical sections. Each notebook prints a summary at the end. This is well-organized and easy to follow.

## Findings Assessment

**H1 (AMR diversity by environment) — well supported:**
Clinical species carry 2.5× more AMR (median 5 vs 2), with η²=0.056. The effect is consistent across majority-vote thresholds. The 13/15 significant pairwise comparisons with rank-biserial effect sizes add granularity. This is convincing.

**H2 (core vs accessory by environment) — well supported:**
The gradient from soil (43% accessory) to clinical (68%) to human gut (80%) is striking and biologically plausible. The connection to Jiang et al. (2024) is appropriate.

**H3 (mechanism by environment) — well supported, with caveats:**
The efflux/metal resistance contrast (η²=0.107–0.127) is the study's strongest finding. However, the potential ~19% NaN mechanism issue (see Code Quality) could bias these fractions. The tetracycline misclassification specifically affects efflux vs target modification counts. Recommend verifying mechanism totals sum to n_amr_clusters.

**H4 (within-species) — partially supported, with framing concerns:**
The REPORT title ("Within species, clinical strain fraction predicts AMR accumulation") and the strong correlation (rho=0.465, p=2.2×10⁻⁴⁵) are for clinical fraction vs *total AMR count*. However, the planned H4 test was whether AMR gene *content* differs between environments *within* the same species. What was actually tested is whether species that happen to have more clinical genomes also have more AMR — this is a between-species comparison, not a within-species one. The true within-species test (per-genome AMR presence/absence comparison between environments via Fisher's exact) was not performed, as acknowledged in the NB03 markdown (cell-6), because it would require billion-row joins. The alternative approach is reasonable but should be more clearly framed as "species-level proxy for within-species variation" rather than "within-species analysis." Additionally, the clinical fraction vs %accessory correlation is borderline non-significant (rho=0.065, p=0.064), yet the REPORT states clinical-dominated species have "higher fraction of accessory AMR (93.6% vs 81.7%, p=0.004)" based on the grouped comparison — these two results should be reconciled.

**Phylogenetic control — thorough:**
The 5/6 phyla with significant within-phylum effects and 20/141 families with within-family effects provide convincing evidence that the environment-AMR association is not purely phylogenetic. Bacteroidota's large within-phylum effect (η²=0.130) is a nice finding.

**Limitations — honestly presented:**
The seven limitations in the REPORT are thorough and self-aware, particularly regarding NCBI sampling bias, effect size interpretation, and causality. The note that η²=0.02–0.13 means environment explains only 2–13% of variance is important context.

## Suggestions

1. **[Critical] Verify and fix the mechanism classifier.** Check whether `amr_clusters['amr_mechanism'].isna().sum()` returns ~15,550. If so, fix the column-alignment bug by renaming the apply output columns: `amr_clusters.loc[mask, 'amr_product'].apply(lambda p: pd.Series(classify_amr_product(p), index=['amr_class', 'amr_mechanism']))`. Re-run NB02 H3 analysis with corrected mechanism fractions.

2. **[Critical] Fill in the Reproduction section of README.md.** Document: (a) NB01 requires Spark on BERDL JupyterHub; NB02–NB04 run locally from cached CSVs (except NB03 cell-4 and NB04 cell-3 which also need Spark), (b) expected runtimes per notebook, (c) `pip install -r requirements.txt` for dependencies.

3. **[Important] Reframe NB03 as a species-level proxy analysis.** The current framing implies per-genome within-species comparison, but the actual analysis compares species-level statistics. Update the REPORT H4 section title and description to clarify this is a "species-level analysis of clinical enrichment and AMR accumulation" rather than a within-species AMR comparison. Acknowledge the borderline non-significance of clinical fraction vs %accessory (p=0.064) alongside the significant grouped comparison (p=0.004).

4. **[Important] Fix NB02 summary variable overwrite.** In cell-3, save the original H1 results to dedicated variables (e.g., `h1_stat, h1_p = kw_stat, kw_p`) so the sensitivity analysis loop doesn't overwrite them. The current summary incorrectly reports p=4.5×10⁻⁷⁵ instead of p=9.4×10⁻¹⁶⁷ for H1.

5. **[Important] Fix tetracycline mechanism classification.** Split tetracycline genes into efflux (tet(A-E), tet(K), tet(L)) vs target modification (tet(M), tet(O), tet(Q), tet(W)) based on gene name patterns. This would improve the accuracy of the mechanism × environment analysis.

6. **[Moderate] Document unperformed planned analyses.** Add a note to the REPORT or RESEARCH_PLAN explaining why PCoA ordination, PERMANOVA, environment-specific gene identification, MAG assessment, and archaea analysis were not performed or were substituted.

7. **[Moderate] Report mechanism classification completeness.** Add a line to NB01 and the REPORT noting what fraction of AMR clusters could be classified by mechanism. If ~19% are unclassified, discuss potential impact on H3 results.

8. **[Minor] Increase Mantel test permutations to match plan.** Change `n_perm = 999` to `n_perm = 9999` in NB04 cell-8 to match the research plan specification, or note the deviation.

9. **[Minor] Add case studies for non-clinical species.** The NB03 case studies are all clinical-dominated. Adding 1–2 environmentally-dominated species with multiple environments (e.g., a soil/aquatic species) would provide useful contrast.

10. **[Nice-to-have] Add a PCoA or NMDS ordination figure.** This was planned and would be a compelling visual showing whether AMR profiles cluster by environment in multivariate space. Even a simple Jaccard-based PCoA on the 6 environment groups would strengthen the narrative.

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-03-19
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, 4 notebooks, 9 data files, 6 figures, requirements.txt
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.

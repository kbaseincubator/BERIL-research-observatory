---
reviewer: BERIL Automated Review
date: 2026-03-19
project: amr_environmental_resistome
---

# Review: Environmental Resistome at Pangenome Scale

## Summary

This is a strong, hypothesis-driven analysis of AMR gene distribution across ecological niches at an unprecedented scale (14,723 species, 293K genomes). The project is well-structured across four notebooks that progress logically from data extraction through species-level tests to within-species proxies and continuous embedding analysis. Key strengths include thorough phylogenetic controls at both phylum and family level, sensitivity analysis across majority-vote thresholds, effect size reporting throughout, a complete Reproduction section, and an honest limitations discussion. All four notebooks have saved outputs with six figures covering each analysis stage. The main issues are: (1) a REPORT/notebook inconsistency where the REPORT's H3 mechanism statistics come from a pre-tetracycline-reclassification run and no longer match the current notebook outputs, (2) a variable-name reuse bug in NB02 that causes the final summary to print an incorrect H1 p-value, (3) a likely pandas column-alignment bug in the mechanism classifier's product-text fallback that may leave ~15,550 clusters unnecessarily unclassified, and (4) several planned analyses (PCoA, PERMANOVA, environment-specific genes, MAG assessment) were dropped without documentation.

## Methodology

**Strengths:**
- Research question is clearly stated, testable, and well-motivated by six literature references with PMIDs (Gibson et al. 2015, Forsberg et al. 2012/2014, Jiang et al. 2024, Surette & Wright 2017, Van Goethem et al. 2018).
- Four hypotheses (H1-H4) are specific and falsifiable, with expected outcomes and gap analysis documented in RESEARCH_PLAN.md.
- Data sources are explicitly identified with table names, row counts, join paths, and a performance plan for handling large tables.
- Phylogenetic confounding is addressed at two levels: stratified Kruskal-Wallis within 6 major phyla (5/6 significant) and within 141 testable families (20 significant after FDR). This is more rigorous than most comparable studies.
- Sensitivity analysis at 50%/60%/75%/90% majority-vote thresholds demonstrates robustness (η² = 0.044-0.056 across all thresholds).
- Effect sizes (η², rank-biserial r) are reported alongside p-values throughout, with appropriate cautioning that with 14K species even tiny effects are significant.
- The Reproduction section in README.md is complete: prerequisites, pipeline steps with execution order, Spark vs local designation, and expected runtimes per notebook.
- The `requirements.txt` lists all Python dependencies with version ranges.

**Gaps:**
- **Several planned analyses were not performed.** The RESEARCH_PLAN specifies: (a) PCoA ordination of AMR profiles colored by environment (§NB02 item 4), (b) PERMANOVA with family as covariate (§NB02 item 5), (c) environment-specific AMR gene identification via Fisher's exact test with BH-FDR (§NB02 item 6), (d) per-genome within-species Fisher's exact tests and Mantel tests (§NB03 items 3-4), (e) MAG vs isolate assessment (§NB01 item 7), and (f) archaea consideration (Confounder #9). None of these appear in the notebooks. The REPORT's Limitations section (item 9) acknowledges this, which is good, but the RESEARCH_PLAN was not updated to note which analyses were substituted or dropped and why.
- **NB03 framing vs content mismatch.** H4 asks whether AMR gene *content* differs between environments *within* the same species. The actual analysis tests whether species with more clinical genomes have more AMR — this is a between-species comparison of clinical enrichment, not a within-species AMR comparison. The markdown in NB03 cell-6 honestly acknowledges this limitation, and the REPORT labels it a "proxy," but the H4 finding header ("Within species, clinical strain fraction predicts AMR accumulation") could mislead readers. Additionally, the clinical fraction vs %accessory correlation is borderline non-significant (rho=0.065, p=0.064), while the grouped comparison is significant (p=0.004) — both are reported but the tension between them deserves more discussion.

## Code Quality

**SQL and data handling (NB01) — correct:**
- The `ncbi_env` EAV pivot via `CASE WHEN ... GROUP BY` is properly implemented (cell-8), correctly using `genome.ncbi_biosample_id → ncbi_env.accession` as the join path, matching the documented pitfall in `docs/pitfalls.md`.
- The GTDB taxonomy join uses `genome_id`, correctly avoiding the `gtdb_taxonomy_id` mismatch pitfall.
- `pd.to_numeric()` is applied to string-typed numeric columns (NB02 cell-1, NB04 cell-3).
- AlphaEarth NaN filtering uses `~df[emb_cols].isna().any(axis=1)` (NB04 cell-3), matching the documented 4.6% NaN issue.
- The taxonomy column `order` is properly backtick-quoted as a reserved word in SQL (NB01 cell-12).
- The data validation checkpoint in NB01 (cell-17) is thorough: verifies AMR cluster counts, environment coverage, per-environment sample sizes, and qualifying species for NB03.

**Tetracycline reclassification — correctly implemented:**
The `reclassify_tet()` function (NB01 cell-5) properly splits tetracycline genes into efflux (tet(A-E,K,L)) and target modification (tet(M,O,Q,W,S) ribosomal protection proteins). This is applied via `.apply()` after the initial classification. The current NB01 output reflects this reclassification: efflux=3,375 and target_modification=12,916.

**Bug: REPORT statistics don't match current notebook outputs (H3):**
The REPORT's mechanism-related numbers come from a run *without* the tetracycline reclassification and no longer match the current notebook outputs:

| Metric | REPORT | Current NB02 Output |
|--------|--------|-------------------|
| Efflux count | 5,224 | 3,375 |
| Target mod count | 11,067 | 12,916 |
| Efflux KW H | 1,775.0 | 768.0 |
| Efflux η² | 0.127 | 0.055 |
| Target mod KW H | 971.7 | 1,394.9 |
| Target mod η² | 0.069 | 0.100 |

The sums are conserved (5,224+11,067 = 3,375+12,916 = 16,291), confirming 1,849 tetracycline ribosomal protection genes were moved from efflux to target modification. Enzymatic inactivation and metal resistance statistics match between REPORT and notebooks because they are unaffected by the reclassification. The REPORT's claim that "efflux is the largest effect in the study (η²=0.127)" is no longer accurate — with corrected classification, metal resistance (η²=0.107) is the largest effect, and efflux drops to η²=0.055.

**Bug: NB02 H1 p-value overwrite in summary (cell-18):**
The variables `kw_stat` and `kw_p` are reused as loop variables in cells 10 (mechanism tests), 13 (phylum stratification), and 14 (family tests). Cell 16 attempts to save the original H1 values with `h1_kw_stat, h1_kw_p, h1_eta_sq = kw_stat, kw_p, eta_sq`, but by that point `kw_stat` and `kw_p` have been overwritten by cell 14's family loop. The cell-18 summary prints `KW p=1.958e-05` (the last family test value) instead of the correct H1 p-value of `9.446e-167`. The `eta_sq` variable is coincidentally correct (0.0556) because cells 10/13/14 used `eta` as their variable name instead of `eta_sq`.

**Potential bug: mechanism classifier product-text fallback (NB01 cell-5):**
The fallback assignment for product-based classification:
```python
amr_clusters.loc[mask, ['amr_class', 'amr_mechanism']] = amr_clusters.loc[mask, 'amr_product'].apply(
    lambda p: pd.Series(classify_amr_product(p)))
```
The `.apply()` returns a DataFrame with integer columns (0, 1), but `.loc` targets columns named `amr_class` and `amr_mechanism`. In pandas 2.0+, `.loc` assignment uses label-based alignment, so mismatched column names would write NaN instead of classified values. The NB01 output shows no 'unknown' mechanism category in `value_counts()` (which excludes NaN by default), and the classified mechanisms sum to 67,458 vs 83,008 total — the 15,550 gap is consistent with NaN from the alignment bug. Some of these 15,550 clusters might be genuinely unclassifiable, but some may have been classifiable from product text. The REPORT acknowledges 18.7% unclassified but attributes it to annotation gaps rather than a code issue.

**NB04 Mantel test permutations:**
The RESEARCH_PLAN specifies 9,999 permutations but NB04 uses 999. With the observed r=0.098 and p=0.001, 999 permutations provides adequate resolution, but the deviation is undocumented.

**Notebook organization:**
All four notebooks follow a clean setup → query → analysis → visualization → save pattern with markdown section headers. Each prints a summary at the end. The flow from NB01 (data extraction) through NB02 (species-level tests) to NB03 (within-species proxy) and NB04 (continuous embeddings) is logical and well-structured.

## Findings Assessment

**H1 (AMR diversity by environment) — well supported:**
Clinical species carry 2.5× more AMR clusters (median 5 vs 2, KW p=9.4×10⁻¹⁶⁷, η²=0.056). The 13/15 significant pairwise comparisons with rank-biserial effect sizes add granularity. Robustness across four majority-vote thresholds is convincing. The NCBI sampling bias caveat (clinical species overrepresented because they have AMR) is appropriately noted.

**H2 (core vs accessory by environment) — well supported:**
The gradient from soil (43% accessory) to clinical (68%) to human gut (80%) is striking and biologically plausible. The connection to Jiang et al. (2024) and the interpretation linking core=intrinsic/ancient vs accessory=acquired/HGT is well-reasoned.

**H3 (mechanism by environment) — well supported, with reproducibility caveat:**
The mechanism × environment pattern is the study's most novel finding. However, the specific statistics and percentages in the REPORT do not match the current notebook outputs due to the tetracycline reclassification discrepancy described above. The qualitative pattern (metal dominates soil/aquatic, efflux/target modification dominate clinical/gut) holds regardless of the reclassification, but the exact effect sizes and composition percentages need to be updated in the REPORT.

**H4 (within-species proxy) — partially supported:**
The clinical fraction vs total AMR correlation (rho=0.465, p=2.2×10⁻⁴⁵) is strong, and the 4.4× AMR difference between clinical-dominated and environmental-dominated species is compelling. The case studies (especially *K. pneumoniae* with 1,115 AMR clusters, only 7 core) are effective illustrations. However, this is a between-species analysis of clinical enrichment, not a within-species comparison as H4 originally proposed. The borderline non-significance of clinical fraction vs %accessory (p=0.064) contrasts with the significant grouped comparison (p=0.004), suggesting the continuous relationship is weak even though the categorical distinction holds.

**Phylogenetic control — thorough:**
5/6 phyla and 20/141 families show significant within-group environment effects after FDR correction. Bacteroidota's large within-phylum effect (η²=0.130) is a useful finding. The approach of using stratified Kruskal-Wallis as a substitute for PERMANOVA is reasonable, though the substitution should be documented.

**Limitations — comprehensively presented:**
Nine limitations are discussed in the REPORT, covering phylogenetic confounding, NCBI sampling bias, environment classification granularity, AMR detection sensitivity, core/accessory precision, causality, effect sizes, mechanism classification completeness, and unperformed analyses. This is unusually thorough and self-aware.

**Literature context — strong:**
The REPORT cites eight papers with PMIDs, clearly positions the work as extending Gibson et al. (2015) by 50× in scale, and identifies five specific novel contributions. The connections to prior BERIL projects (`amr_strain_variation`, `amr_fitness_cost`, `env_embedding_explorer`) are well-articulated.

## Suggestions

1. **[Critical] Update REPORT.md to match current notebook outputs.** The REPORT's H3 statistics (KW H values, η² values, mechanism counts, composition table percentages) are from a pre-reclassification run. Re-derive all mechanism-related numbers from the current NB01/NB02 outputs with tetracycline reclassification applied. In particular: efflux η² drops from 0.127 to 0.055, and the REPORT's claim that efflux is "the largest effect in the study" should be corrected (metal resistance at η²=0.107 is now largest).

2. **[Critical] Fix NB02 variable-name reuse bug.** In cell-3, save H1 results to dedicated variables immediately: `h1_kw_stat, h1_kw_p, h1_eta_sq = kw_stat, kw_p, eta_sq`. Move this save to cell-3 (not cell-16 where it currently is, after cells 10/13/14 have overwritten the values). Also rename loop variables in cells 10, 13, and 14 to avoid shadowing (e.g., `mech_kw_stat, mech_kw_p`).

3. **[Important] Verify and fix the mechanism classifier product-text fallback.** Check `amr_clusters['amr_mechanism'].isna().sum()` — if ~15,550, fix the alignment bug by adding `index=` to the Series constructor: `pd.Series(classify_amr_product(p), index=['amr_class', 'amr_mechanism'])`. Re-run NB02 to see if the unclassified fraction decreases meaningfully.

4. **[Important] Reframe NB03 more precisely.** Rename the REPORT's H4 section from "Within species..." to "Species-level: clinical genome fraction predicts AMR accumulation." In the REPORT text, clearly distinguish this species-level proxy from the originally planned per-genome within-species comparison, and discuss why the continuous correlation (rho=0.065, p=0.064) is borderline while the grouped comparison (p=0.004) is significant (likely because the grouped comparison discards the continuous clinical fraction information in favor of a categorical split that concentrates effect).

5. **[Important] Document unperformed planned analyses in RESEARCH_PLAN.** Add a "Deviations from Plan" section explaining: (a) PCoA and PERMANOVA were substituted with stratified KW within phyla/families, (b) environment-specific gene identification was deferred, (c) MAG assessment and archaea analysis were not performed. This prevents future readers from wondering whether these analyses failed or were intentionally skipped.

6. **[Moderate] Add 1-2 non-clinical case studies to NB03.** All five case study species (cell-10/11) are clinical-dominated. Including environmentally-dominated species with multi-environment representation (e.g., *Listeria monocytogenes* at 1,906 genomes across 5 environments, or *Vibrio parahaemolyticus* at 1,578 genomes) would provide useful contrast and strengthen the H4 proxy narrative.

7. **[Moderate] Increase Mantel test permutations or note deviation.** Change `n_perm = 999` to `n_perm = 9999` in NB04 cell-8 to match the RESEARCH_PLAN specification, or add a note explaining why 999 was sufficient.

8. **[Minor] Report mechanism classification completeness explicitly in NB01.** After cell-5, add a line: `print(f'Unclassified: {amr_clusters["amr_mechanism"].isna().sum()} + {(amr_clusters["amr_mechanism"]=="unknown").sum()}')` to separate genuine unclassified from potential NaN bugs.

9. **[Nice-to-have] Add PCoA ordination figure.** This was planned and would be a compelling multivariate visualization showing whether AMR profiles cluster by environment. A Jaccard-based PCoA on species AMR presence/absence, colored by environment, would complement the univariate KW tests with a single intuitive figure.

10. **[Nice-to-have] Assess MAG contamination risk.** The RESEARCH_PLAN correctly identified MAGs as a potential confounder (chimeric AMR annotations, ambiguous metadata). Even a brief check of MAG vs isolate proportions across environments would strengthen confidence in the findings.

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-03-19
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, 4 notebooks, 9 data files, 6 figures, requirements.txt
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.

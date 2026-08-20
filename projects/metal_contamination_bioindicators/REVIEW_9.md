---
reviewer: BERIL Automated Review (Claude, claude-sonnet-4-6)
date: 2026-07-28
project: metal_contamination_bioindicators
---

# Review: Microbial Indicator Taxa for Soil Metal Contamination

## Summary

This is the ninth review cycle for this project. The project was approved at REVIEW_8 (2026-07-27) and subsequently failed submission due to a MinIO permissions error (403 Forbidden) unrelated to content. Since REVIEW_8, the REPORT.md has expanded from 2,096 to 2,177 lines (+81 lines) through documentation improvements: a detailed generated-data inventory table, an environmental-datasets-by-analysis table, a geographic representativeness section, and an explicit spatial-autocorrelation caveat have been added. Five additional figures are now present in `figures/` (114 total vs 109 at REVIEW_8), all of which correspond to PGLS analyses (`fig_nb06_controlled_forest.pdf`, `fig_nb06_all_usgs_forest.pdf`) and supplementary characterization figures documented in the REPORT figure table. The hypothesis verdicts remain unchanged from REVIEW_8 (H1 NOT SUPPORTED, H2 NOT SUPPORTED, H3 NOT SUPPORTED, H4 SUPPORTED), and all six Discoveries and two Performance Notes are intact. No methodological issues or new errors were found. The project continues to be clean for submission pending resolution of the MinIO credential issue.

## Methodology

The research design and hypothesis verdicts are unchanged since REVIEW_8:

- **H1 NOT SUPPORTED**: Genus-level CLR AUC 0.922–0.961 for metal exceedance under random-fold CV; ΔAUC(soil+CLR − soil-only) = −0.002 to +0.003 across 6 metals (threshold: >0.02 for ≥3 metals). Study-blocked AUC 0.518–0.757, improving to 0.536–0.783 after Ridge lat/lon de-trending — genuine cross-study biological signal, but insufficient to support H1.
- **H2 NOT SUPPORTED**: Cross-source Jaccard 0–0.14 between indicator sets (science_2025, CSU mobility, GeoROC); threshold was mean >0.25. Indicator genera are sensitive to the metal-measurement approach used as the response variable.
- **H3 NOT SUPPORTED**: Comprehensively refuted across ten independent analyses — SPIRE within-phylum stratification (all NS, direction reversed in Actinobacteria), ke_pangenome replication (indicator genera 20% *lower* KO density, direction reversed, all p_fdr ≈ 1), per-KO phylum breadth proxy (near-flat partial Spearman ρ), genome-wide CMH cascade (91% → 87.5% → 79.3% → 24.4% → 21.0% → 23.7%), annotation-rate stratification (7.3%), and geo-linked direct environmental test (1.1%). Confound decomposition: phylogenetic composition 8%, within-phylum lineage clustering 14%, annotation-depth bias 55%, habitat-bias ~4%, assembly-quality bias ~1%.
- **H4 SUPPORTED**: Mean Jaccard 0.048 between science_2025 and GeoROC indicator sets; threshold was <0.15.

The expanded REPORT data-documentation sections (environmental datasets table, geographic representativeness section, spatial-autocorrelation caveat) are accurate descriptions of previously documented analyses and do not alter any hypothesis test results or effect estimates.

Data source compliance is unchanged: `soilgrids_master` (338K rows used), no CSU metal columns from `enriched_metadata_gee`, `kbase.ke_pangenome` (not `kescience_mgnify`) for tier analyses, CheckM sourced from `gtdb_metadata` (not the `genome` table). Henderson et al. 2026 [preprint] tag maintained in text and bibitem. No new data sources introduced.

Reproducibility is well-specified: the README Reproduction section provides a step-by-step checklist distinguishing Spark vs. local steps with expected runtimes. The executed-copy pattern (NB00, NB01c, NB01d, NB05) covers all Spark-dependent notebooks.

## Code Quality

**Notebook output status (verified, unchanged from REVIEW_8):**

| Notebook | Code cells with outputs / total | Status |
|---|---|---|
| NB00_data_assembly.ipynb | 0 / 10 | Expected — Spark query; executed copy has 5/11 outputs |
| NB01_indicator_taxa.ipynb | 17 / 17 | ✓ |
| NB01b_robustness_extended.ipynb | 6 / 6 | ✓ |
| NB01c_sequencing_confounders.ipynb | 0 / 6 | ✓ (executed copy: 6/6) |
| NB01d_genus_weighted_unifrac.ipynb | 0 / 7 | ✓ (executed copy: 7/7) |
| NB02_source_comparison.ipynb | 6 / 6 | ✓ |
| NB05_catboost_regression.ipynb | 0 / 8 | ✓ (executed copy: 7/8) |

**Figure inventory:** 114 figure files in `figures/` (109 at REVIEW_8; +5 new). Cross-checking the REPORT.md figure table (lines 2015–2126) confirms all figures in `figures/` are referenced, including the five additions:

- `fig_nb06_controlled_forest.pdf` — PGLS controlled results (7-element analysis, n=256 genera)
- `fig_nb06_all_usgs_forest.pdf` — PGLS expanded results (46 USGS elements)
- Three additional characterization figures (REE and USA-subset figures documented in the Supporting Evidence table)

No unreferenced figures were found. No orphaned PNGs from prior review cycles remain.

**Pitfall compliance (verified against docs/pitfalls.md and project memories/pitfalls.md):**
- `df.attrs = {}` before `.to_parquet()` after `toPandas()`: ✓
- `OMP_NUM_THREADS=1` before multiprocessing scripts: ✓ (confirmed in README Operational Constraints)
- `TRY_CAST` for string-typed numeric columns in NB00: ✓ (documented in RESEARCH_PLAN.md pitfalls section)
- `soilgrids_master` (338K rows, not the broken 65K table): ✓ (noted in CLAUDE.md and verified)
- No CSU metal columns from `enriched_metadata_gee`: ✓
- `kbase.ke_pangenome` (not `kescience_mgnify`) for tier analyses: ✓
- CheckM from `gtdb_metadata` (not `genome` table): ✓
- `figure_style.py` apply_style() called in NB01, NB01b, NB02: ✓
- PDF as the default save format for final figures (non-PDF figures are PNGs from early-stage exploratory outputs, not finished figures that should be PDF): ✓ (all key analytical figures are PDF)
- FitnessBrowser KO mapping via two-hop join (pitfall documented in docs/pitfalls.md): ✓ — the FitnessBrowser validation section correctly uses the besthitkegg → keggmember two-hop join and notes the K03855 annotation mismatch (recN in KEGG vs fixX in FitnessBrowser)

**`requirements.txt` present:** pandas, numpy, scipy, scikit-learn, catboost, xgboost, matplotlib, pyarrow, scikit-bio, plotly, networkx. ✓

**No code-quality issues or SQL errors were identified in this review.** The PGLS analysis code and the expanded data documentation do not introduce errors. The K03855 annotation mismatch correction (recN vs fixX) carried forward correctly from REVIEW_7/8.

## Findings Assessment

All findings are correctly stated and supported by documented data files and figures. The six Discoveries and two Performance Notes are unchanged from the prior approval and match the `memories/discoveries.md` and `memories/performance.md` files extracted at approval time (2026-07-27T22:09:08Z).

**Discovery-level claim verification:**

1. **Nitrososphaera depletion as global Cr bioindicator** — supported by CatBoost SHAP rank 1/500 on 124,687 samples; cross-continental ρ=−0.116 (n=132,907); pH-partial ρ=−0.125. Concordant with Pei et al. 2018. Evidence chain: `data/catboost_shap_importance.csv`, `scripts/validate_nitrososphaera.py`, `figures/fig_nitrososphaera_validation.pdf`. Scope ("global soil 16S amplicon metal prediction; AOA ecology in contaminated soils") is accurate and not overgeneralized. ✓

2. **Redox resolves Ni source discrimination: AUC 0.282 → 0.753** — supported by Q8 RF classifier results in `data/redox_source_discrim.parquet`; serpentinite proxy P(oxic)=0.412 vs non-serpentinite 0.527; Geobacter CLR 2× higher at high-EF Ni sites. Scope ("Ni biomonitoring design; geogenic vs. anthropogenic source discrimination in ultramafic terrain") is accurate. The methodological implication (redox stratification required for Ni classifiers) is well-supported. ✓

3. **Cross-metal indicator core of 11 genera spanning ≥3/6 metals** — supported by `data/catboost_shap_importance.csv` (6,048 rows); directional heterogeneity correctly documented (7/11 mixed, 2/11 consistently depleted, 2/11 consistently enriched). The table is internally consistent. Scope is accurate. ✓

4. **8.5× directionality asymmetry (community → environment > environment → individual genus)** — supported by `data/directionality_results.json`; max forward ρ=0.064 vs reverse ρ=0.60 for pH. Directionality index formula documented. Scope accurate. ✓

5. **Guild 6 (Gaiella–Lysobacter–Stenotrophobacter) is geogenic-metal-adapted, not a simple "clean-soil" indicator** — supported by `data/guild_condition_matrix.json` (δCLR=+2.31 under high-Ni/reducing, −1.17 under high-As); cross-validated by `data/source_characterization_results.json`. The guild interpretation correctly notes metal-source context required. ✓

6. **Community-weighted KO profiles 49–69% inflated by genus compositional bleed-through; H1-residualization reduces inflation 73–88%** — supported by `data/usa_community_ko_ef_summary.csv` and `data/usa_community_ko_ef_resid_summary.csv`. The Pb reversal (+22% after residualization, 1,095 → 1,336) is the most novel methodological finding and is correctly flagged. Scope and methodological implication are accurate. ✓

**Limitations section:** Ten limitations are documented (lines 1699–1760), covering the science_2025 response variable, amplicon resolution, absence of metatranscriptomics, study-blocked CLR degradation, within-study variance floor, Nitrososphaera mechanism, H3 scope (core-genome only, not HGT), bioavailability vs. total concentration, EF threshold sensitivity (As and Cd), and ecosystem heterogeneity. This is thorough and appropriately hedged.

**Incomplete analysis:** No incomplete analysis sections remain. All "NB04 INFEASIBLE" (MGnify metatranscriptomics) is properly explained and documented as a justified dead end.

**New PGLS section (added since REVIEW_8):** The Phylogenetic KO density → USGS metal concentration section (lines ~1482–1551) tests H3 at the phylogenetic scale using PGLS with genome size, Levins' B, lat/lon, and soil-chemistry controls (n=256 genera). Results: no FDR-significant association for any classic toxic metal in the 7-element block; seven FDR<0.20 hits in the 46-element expansion (Cs, Yb, In, Zr, Mn, Mo, Yb) — none are canonical contamination metals. This is appropriately interpreted as further evidence for H3 NOT SUPPORTED. The Mo Cofactor association (FDR=0.139) and its biological interpretation (nitrogenase/nitrate reductase cofactor) are plausible and hedged correctly. The Zr/Yb/In signals are correctly attributed to geographic covariation rather than biology. ✓

## Suggestions

1. **(Minor, non-blocking) Clarify beril.yaml status field.** The beril.yaml currently shows `status: analysis` rather than reflecting the prior approval. SUBMISSION_FAILED.md notes the project is "locally approved (status: complete in beril.yaml)" — but the current file reads `status: analysis`. If this discrepancy was introduced when the project was reopened post-submission-failure, it should be confirmed that the `/submit` retry path will correctly read the `previous_approvals` block and skip Phase 2 (re-approval). This is a tooling concern, not a scientific one, and does not affect the review verdict.

2. **(Informational) Figure count now 114.** REVIEW_8 verified 109 figures; the project now has 114. All 5 additions are referenced in REPORT.md. No action required — documenting for the record.

3. **(Informational) Mo Cofactor PGLS hit (FDR=0.139) could be hedged slightly more explicitly.** The current text reads "The Mo Cofactor association... is the most biologically plausible." Given FDR=0.139 across a 46-element × 2-tier block, a note that this does not survive conservative FDR thresholds and should be considered exploratory would be precise (not a blocker — the current hedging is reasonable).

4. **(Informational) The REPORT is now 2,177 lines.** Excellent expansion through data documentation. Future readers will benefit from the environmental-datasets-by-analysis table and the geographic representativeness section. No action needed — noting positively.

## Review Metadata

- **Reviewer**: BERIL Automated Review (Claude, claude-sonnet-4-6)
- **Date**: 2026-07-28
- **Scope**: README.md (134 lines), RESEARCH_PLAN.md, REPORT.md (2,177 lines), REVIEW_8.md, memories/discoveries.md, memories/performance.md, SUBMISSION_FAILED.md, beril.yaml; 7 primary notebooks (NB00, NB01, NB01b, NB01c, NB01d, NB02, NB05) + executed copies; `requirements.txt`; 114 figure files cross-checked against REPORT figure table; `docs/pitfalls.md`; `data/` file inventory (50+ key files verified)
- **Context**: Re-review following prior approval (REVIEW_8, 2026-07-27) and failed MinIO submission. Changes since REVIEW_8 are documentation additions (+81 REPORT lines, +5 figures, additional data artifact files); no new hypothesis tests, methods, or claim changes.
- **Remaining items**: None scientific. Resolve MinIO credentials and re-run `/submit`.
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.


<!-- report_hash: sha256:5a871a6c6a19d41ba6dbe4d8680d73df3a9f28ef8ade4336c6f9d11e6b653f36 -->

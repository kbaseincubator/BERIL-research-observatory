# Microbial Indicator Taxa for Soil Metal Contamination

## Status

Reviewed — REVIEW_9.md drafted; awaiting /submit.

## Research Question

Which microbial genera are reliable indicators of soil metal contamination risk, and does
their indicator status reflect elevated metal gene content rather than phylogenetic
co-occurrence with metal-tolerant lineages?

## Authors

Heather MacGregor (Lawrence Berkeley National Laboratory)

## Thesis Chapter

Part 1 — Global Metal Ecology

## Data Collections

- `arkinlab.microbeatlas` — 278K globally distributed 16S amplicon samples with lat/lon
- `arkinlab.envdbs.science_2025_global_soil_toxic_metals` — global gridded soil metal exceedance probabilities (As/Cd/Co/Cr/Cu/Ni/Pb; AT and HHET thresholds; Tóth et al. 2025 *Science*)
- `arkinlab.envdbs.soilgrids_master` — global soil chemistry at 0.25-deg (pH/SOC/clay/CEC/bulk density, 0–5 cm)
- `arkinlab.envdbs.csu_metal_mobility_grid` — modelled most-mobile metal fractions (pf1_as/cd/cr/cu/hg/pb)
- `arkinlab.microbeatlas.enriched_metadata` — pre-joined GeoROC geological background metals
- `refdata.spire` — 1.2M MAGs for functional validation of indicator genera

## Hypotheses

| H | Statement | Test |
|---|-----------|------|
| H1 | Genus-level community composition predicts metal contamination risk beyond soil chemistry | ΔAUC(CLR model − soil-chemistry-only model) > 0 for ≥ 3/7 metals |
| H2 | Indicator genera are consistent across metal sources (science_2025, GeoROC, CSU mobility) | Jaccard overlap of top-50 indicator genera across three metal datasets |
| H3 | Indicator genera carry elevated metal gene density in SPIRE MAGs | Metal KO density in indicator vs. non-indicator genera (Wilcoxon) |
| H4 | Contamination-risk indicators differ from geological-background indicators | Low Jaccard overlap between science_2025 vs. GeoROC indicator sets |

## Notebooks

| NB | Purpose | Status |
|----|---------|--------|
| NB00 | Data assembly: join microbeatlas × science_2025 × soilgrids × GeoROC × CSU mobility | Complete |
| NB01 | Indicator taxa analysis: genus CLR → metal exceedance (per metal, per threshold type) | Complete |
| NB01b | Extended robustness: study blocking, confounding analysis, regression CV | Complete |
| NB01c | Sequencing confounders: primer bias, sample depth (within-study |ρ| ≤ 0.014; depth not a confounder) | Complete |
| NB01d | Genus-level weighted UniFrac PCoA with GTDB r214 branch lengths (444/500 CLR genera matched); 2×3 panels coloured by depth quartile and binary metal exceedance; continuous hexbin biplot with genus loading arrows | Complete |
| NB02 | Metal source comparison: science_2025 vs GeoROC vs CSU mobility indicator overlap | Complete |
| NB03 (implemented as `scripts/run_nb03_functional.py`) | Functional validation: indicator genera × SPIRE metal KO density | Complete |
| NB04 | MGnify metatranscriptomics extension | INFEASIBLE — no public dataset meets requirements |
| NB05 | CatBoost regression (CLR/soil/soil+CLR), algorithm comparison (6 methods), SHAP importance — run headlessly; `NB05_catboost_regression_executed.ipynb` is the executed copy with saved cell outputs | Complete |
| NB06 | PCA(200), RF-PCA ρ comparison, t-SNE + UMAP explorer — **log file** from headless script run (not interactive notebook); outputs: `data/dimred_coords.parquet`, `figures/fig_dimred_explorer.html` | Complete |

## Analysis Scripts

Scripts in `scripts/` perform substantial analyses not run as interactive notebooks:

| Script | Purpose | Status |
|--------|---------|--------|
| `run_nb03_functional.py` | H3 functional validation: Wilcoxon KO density (indicator vs rest) | Complete |
| `run_mwas.py` | Within-study meta-analysis: 500 genera × 6 metals, Stouffer Z | Complete |
| `validate_nitrososphaera.py` | Nitrososphaera global validation: ρ by continent, pH partial corr, quintile response | Complete |
| `run_strata_biomonitoring.py` | Gradient-position dependent indicators: stratified RF (Q1 vs Q2, Q4 vs Q5) | Complete |
| `run_soil_confound_analysis.py` | Metal vs soil-variable cross-Jaccard (pH/SOC/clay as response) | Complete |
| `run_shap_signed.py` | Signed SHAP direction analysis: CatBoost per metal, waterfall + dependency data | Complete |
| `build_sample_covariates.py` | ENA metadata + OTU V-region merge → sample_covariates.parquet | Complete |
| `run_nb01c_depth.py` | Sequencing depth confound: within-study partial ρ, depth η² | Complete |
| `generate_dashboard.py` | Interactive HTML dashboard v1 (6 sections) | Complete |
| `generate_comprehensive_dashboard.py` | Dashboard v2 (current): adds USA map layer, 23-condition co-occurrence networks | Complete |
| `run_resid_blocked_cv.py` | Spatial de-trended CLR: Ridge lat/lon residuals → study-blocked AUC | Complete |
| `run_usgs_within_study.py` | USGS point-metal MWAS validation: confirms null with measured concentrations (USA, 403 studies) | Complete |
| `run_h3_phylum_stratified.py` | H3 within-phylum stratification: Mann-Whitney within Actinobacteria/Proteobacteria/Firmicutes (reveals phylogenetic confound) | Complete |
| `run_redox_integration.py` | Redox integration: 8 sub-questions (Q1–Q8), redox proxy vs metal/genus associations, source discrimination | Complete |
| `run_network_ecology.py` | Co-occurrence network topology across 23 environmental conditions (s25-defined) | Complete |
| `run_network_null_model.py` | Sign-permutation null model for positive-edge fraction (200 permutations × 23 conditions) | Complete |
| `run_network_usgs.py` | USGS-based co-occurrence networks; comparison to s25-based network metrics | Complete |
| `run_guild_characterization.py` | Ward clustering on 40×40 co-occurrence stability matrix → 8 guilds with env profiles | Complete |
| `run_source_characterization.py` | Contamination vs. geogenic background classifiers; Ni redox ecology (AUC 0.282→0.753) | Complete |
| `run_guild_condition_exploration.py` | δCLR heatmap (8 guilds × 23 conditions), Ward condition clustering | Complete |
| `run_generalizability.py` | Cross-study vs within-study signal concordance; phylum and study-property predictors | Complete |
| `run_temporal_audit.py` | ENA date coverage, year–metal Spearman ρ, temporal–geographic co-structure | Complete |
| `run_ni_multioutput.py` | Multi-output RF for Ni exceedance with auxiliary Cr prediction | Complete |
| `run_directionality_test.py` | Forward (env → genus) vs reverse (CLR → env) prediction asymmetry (8.5× ratio) | Complete |
| `run_q6_q8_fixed.py` | Corrected Q6 (no feature leakage) + Q8 source discrimination with/without redox proxy | Complete |
| `run_usa_ef_redox_analysis.py` | USA EF analysis: USGS enrichment factors, within-study Spearman, Ni redox stratification | Complete |
| `run_usa_community_ko_ef.py` | Community-weighted KO × EF associations (7,221 KOs × 124K samples, BLAS matmul) | Complete |
| `run_usa_community_ko_ef_residualized.py` | H1-residualized community-KO EF analysis; confound-robust KO set | Complete |
| H3 annotation-bias pipeline (`run_h3_all_ko_enrichment*.py`, `run_h3_cmh_*.py`, `run_h3_annotation_bias_controls.py`, `run_h3_geo_linked_ko_enrichment.py`, `run_h3_ko_phylo_breadth.py`, `run_h3_per_metal_cmh.py`) | Ten-analysis H3 confound decomposition: naive → phylum/order-CMH → prevalence threshold → soil filter → completeness filter → annotation-rate stratification → geo-linked validation | Complete |

## Reproduction

**Prerequisites**: JupyterHub Spark session (NB00 only), Python env with `berdl_notebook_utils`, `figure_style.py` from `tools/` on `sys.path`.

**Spark vs. local**: NB00 requires a live Spark session to query `arkinlab.*` tables. All subsequent notebooks (NB01–NB06) and all scripts run locally from `data/analysis_matrix.parquet` (795 MB).

### Reproducibility Checklist

- [ ] JupyterHub Spark session available (NB00 only)
- [ ] `berdl_notebook_utils` installed; `tools/figure_style.py` on `sys.path`
- [ ] Run `NB00_data_assembly.ipynb` (~30 min, Spark) → `data/analysis_matrix.parquet` (795 MB)
- [ ] Run `NB01_indicator_taxa.ipynb` (~15 min, local) → H1 AUC results, indicator SHAP
- [ ] Run `NB01b_robustness_extended.ipynb` (~20 min) → study-blocked CV, confounding
- [ ] Run `NB01c_sequencing_confounders.ipynb` (~10 min) → primer bias, depth η²
- [ ] Run `NB01d_genus_weighted_unifrac.ipynb` (~40 min, first run; checkpoint thereafter) → weighted UniFrac PCoA figures
- [ ] Run `scripts/run_nb01c_depth.py` (~5 min) → within-study partial ρ
- [ ] Run `NB02_source_comparison.ipynb` (~10 min) → H2/H4 source Jaccard
- [ ] Run `scripts/run_nb03_functional.py` (~5 min) → H3 Wilcoxon KO density
- [ ] Run `NB05_catboost_regression.ipynb` (~45 min) → algorithm comparison, SHAP
- [ ] Run `scripts/run_shap_signed.py` (~10 min) → signed SHAP direction + dependency data
- [ ] Run `scripts/run_mwas.py` (~15 min) → within-study meta-analysis (0/3,000 sig)
- [ ] Run `scripts/validate_nitrososphaera.py` (~5 min) → cross-continental validation
- [ ] Run `scripts/run_strata_biomonitoring.py` (~10 min) → gradient-position indicators
- [ ] Run `scripts/run_soil_confound_analysis.py` (~10 min) → cross-variable Jaccard
- [ ] Run `NB06` headless script (~25 min) → PCA(200), t-SNE, UMAP
- [ ] Run `scripts/run_usgs_within_study.py` (~15 min) → USGS MWAS validation (0/3,000 sig; confirms null)
- [ ] Run `scripts/generate_dashboard.py` (~5 min) → `figures/fig_comprehensive_dashboard.html`
- [ ] Verify: all CSVs/parquets in `data/` present; all PDFs in `figures/` present

**Expected runtimes** (approximate, on BERDL hub):

| Notebook/Script | Runtime | Notes |
|----------------|---------|-------|
| NB00 | ~30 min | Spark query + Parquet write |
| NB01 | ~15 min | Local sklearn, gradient boosting |
| NB01b | ~20 min | Study-blocked CV, confounding analysis |
| NB01c + depth script | ~15 min | Primer bias + depth η² |
| NB02 | ~10 min | Source comparison, Jaccard |
| NB03 script | ~5 min | Wilcoxon KO density test |
| NB05 | ~45 min | CatBoost CV + algorithm comparison + SHAP |
| run_shap_signed.py | ~10 min | CatBoost × 6 metals, SHAP on 5K samples each |
| run_mwas.py | ~15 min | 500 genera × 6 metals, vectorized within-study Spearman |
| NB06 script | ~25 min | PCA(200) + t-SNE + UMAP on 124K samples |

**Output verification**: NB01, NB01b, NB02 have saved cell outputs in the primary notebooks. NB00, NB01c, NB01d, NB05 use an executed-copy pattern (`_executed.ipynb`). Run `git log -- figures/` to verify figure provenance; run `ls data/*.csv data/*.parquet` to confirm generated data files are present.

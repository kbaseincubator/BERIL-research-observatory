# metagenomic_environment_prediction

**Does per-Mb metal-gene density in environmental MAGs predict local metal mobility at the sampling site?**

This project tests whether the genomic signal documented in `comprehensive_metal_ecology` is recoverable at the individual-MAG level and generalises across geographic space. It is a downstream extension, not a replication — the predictor (MAG-level density) and target (environmental metal conditions at sampling coordinates) are both different from P1.

---

## Hypotheses

| ID | Statement | Test |
|----|-----------|------|
| H1 | Metal-gene density (M1) beats mean baseline (B0) | M1 CV RMSE < B0 CV RMSE on ≥3/5 spatial folds |
| H2 | Metal features alone (M1) beat non-metal env alone (M2) | M1 CV RMSE < M2 CV RMSE on ≥3/5 folds |
| H3 | Adding non-metal features (M3) beats M1 alone | M3 CV RMSE < M1 CV RMSE on ≥3/5 folds |
| H4 | Geographic transfer — Australia holdout | Holdout RMSE ≤ 1.25 × in-distribution CV RMSE |
| H5 | PGLS directional consistency | β(ko_per_mb) at genus level has same sign as P1 (−0.021) |

---

## Data sources

### SPIRE MAGs (primary dataset; complete)

| Source | Used for |
|--------|----------|
| `https://spire.embl.de/download_eggnog/{SAMPLE_ID}` | **Primary:** gzip eggnog TSV for all MAGs in a sample (~36 MB); cached to `data/spire_cache/eggnog/` |
| `https://spire.embl.de/download_file/{MAG_ID}` | **Primary:** gzip FASTA for contig-to-MAG mapping (~422 KB); cached to `data/spire_cache/mag_contigs/` |
| `refdata.spire.mag_coordinates` | MAG lat/lon coordinates and sample IDs (all 1.16M SPIRE MAGs) |
| `refdata.spire.genome_metadata` | Completeness, contamination, genome size, domain, genus |
| `refdata.spire.sample_environment` | Soil features: SoilGrids pH, clay, organic carbon |
| `refdata.spire.sample_microntology` | ENVO environment terms for host/non-host filtering |
| CSU metal mobility fractions (PF1_As/Cd/Cr/Cu/Hg/Pb) | Environmental metal targets (6 metals; Zn/Ni not in grid) |
| 256-KO primary set (`comprehensive_metal_ecology/data/curated_mrg_ko_ids_v2.csv`) | KO selection and subcategory labels (Tier 1, Tier 2, Tier 2-Fitness) |

### MGnify MAGs (second dataset; exploratory)

| Source | Used for |
|--------|----------|
| `final_mags_geospatial_traits.csv` from `microbeatlas_metal_ecology` | Coordinates, taxonomy, biome classification (~N MAGs after filtering to soil/rhizosphere/marine sediment) |
| `kescience_mgnify.genome` Spark table | Genome completeness, contamination, domain, mobile_fraction |
| `kescience_mgnify.gene_eggnog` Spark table | KEGG KO annotations (KEGG_ko column, comma-separated format) |
| CSU metal mobility fractions (same grid as SPIRE) | Environmental metal targets for spatial join |
| Same 730 curated KOs as SPIRE | KO selection and subcategory labels |

---

## Directory structure

```
metagenomic_environment_prediction/
├── data/                        # Generated data (not committed)
│   ├── spire_probe_results.json
│   ├── mag_feature_matrix.parquet              # SPIRE
│   ├── cv_results.csv                          # SPIRE
│   ├── shap_mean_abs.csv                       # SPIRE
│   ├── holdout_results.json                    # SPIRE
│   ├── pgls_validation_results.csv             # SPIRE
│   ├── mgnify_mag_feature_matrix.csv           # MGnify (exploratory)
│   ├── mgnify_mobility_prediction_results.csv  # MGnify (exploratory)
│   ├── mgnify_geographic_holdout.csv           # MGnify (exploratory)
│   ├── mgnify_pgls_validation.csv              # MGnify (exploratory)
│   ├── mgnify_vs_spire_comparison.csv          # Cross-dataset (exploratory)
│   ├── mgnify_mag_metadata_cache.parquet       # Cache
│   └── mgnify_ko_cache.parquet                 # Cache
├── figures/                     # Generated figures (not committed)
├── notebooks/
│   ├── 00_download_spire.ipynb  # Probe data availability; choose data path
│   ├── 01_mag_feature_matrix.ipynb  # Build MAG feature matrix + env join (SPIRE)
│   ├── 02_predict_mobility.ipynb    # H1/H2/H3 spatial block CV + SHAP (SPIRE)
│   ├── 03_geographic_holdout.ipynb  # H4 Australia holdout (SPIRE)
│   ├── 04_pgls_validation.ipynb     # H5 genus-level PGLS consistency (SPIRE)
│   ├── 01b_mgnify_feature_matrix.ipynb         # Build feature matrix (MGnify, exploratory)
│   ├── 02b_mgnify_mobility_prediction.ipynb    # H5/H6/H7 CV (MGnify, exploratory)
│   ├── 03b_mgnify_geographic_holdout.ipynb     # Geographic holdout (MGnify, exploratory)
│   ├── 04b_mgnify_pgls_validation.ipynb        # PGLS validation (MGnify, exploratory)
│   ├── 05_mgnify_vs_spire_comparison.ipynb     # Cross-dataset comparison (exploratory)
│   ├── 06_spire_genome_levins_b_pgls.ipynb     # Genome-derived Levins' B PGLS (confound diagnostic)
│   └── 07_study_design_confound.ipynb          # Study-effort confound analysis (justifies H5 design)
└── scripts/
    ├── mag_utils.py             # per-Mb density computation
    ├── env_utils.py             # CSU + SoilGrids spatial joins
    ├── spire_api.py             # SPIRE REST API client
    ├── modelling.py             # spatial block CV, baselines, XGBoost
    ├── evaluation.py            # SHAP, RMSE/R², holdout comparison
    └── soilgrids_api.py         -> ../../hybrid_metal_prediction/scripts/soilgrids_api.py
```

---

## Execution order

### SPIRE pipeline (primary)
Run in sequence: NB00 → NB01 → NB02 → NB03 → NB04.
NB00 must complete first as it writes `data/spire_probe_results.json` which determines the data path for NB01.

### MGnify pipeline (exploratory, parallel)
Run in sequence: NB01b → NB02b → NB03b → NB04b → NB05 (comparison).
Can be run in parallel with or after SPIRE pipeline. NB05 should run last as it compares outputs from both pipelines.

---

## MAG quality thresholds

- Domain: Bacteria only
- Completeness ≥ 70%
- Contamination ≤ 10%
- Coordinates required (latitude, longitude not null)
- ENVO terms must indicate non-host environment (terrestrial, soil, aquatic, sediment, freshwater, marine)

---

## Relationship to other projects

- **comprehensive_metal_ecology** (P1): Primary genus-level analysis; this project uses the same 140-KO set and `pgls_utils.run_pgls` but operates at MAG/sample resolution, not genus/OTU resolution.
- **hybrid_metal_prediction**: Source of `soilgrids_api.py`; symlinked here.

---

## Status

Reviewed — REVIEW_1.md drafted; awaiting /submit.

### SPIRE pipeline
All notebooks executed (2026-07-09).

| Notebook | Status | Key output |
|----------|--------|------------|
| NB00 | Complete | `data/spire_probe_results.json` — use_spire_downloads=True |
| NB01 | Complete | `data/mag_feature_matrix.parquet` — 15,957 MAGs, 15,368 with CSU, 13,182 with SoilGrids |
| NB02 | Complete | `data/cv_results.csv`, `data/shap_mean_abs.csv` |
| NB03 | Complete | `data/holdout_results.json` |
| NB04 | Complete | `data/pgls_validation_results.csv` |

### MGnify pipeline (exploratory)
All notebooks executed (2026-07-09 to 2026-07-31).

| Notebook | Status | Key output |
|----------|--------|------------|
| NB01b | Complete | `data/mgnify_mag_feature_matrix.csv` — 8,849 MAGs, 7,973 with CSU |
| NB02b | Complete | `data/mgnify_mobility_prediction_results.csv` — B0/M1/M2/M3 CV; M3=0.0163, B0=0.0369 |
| NB03b | Complete | `data/mgnify_geographic_holdout.csv` — ratio=0.655, n=97 Australia MAGs |
| NB04b | Complete | `data/mgnify_pgls_validation.csv` — β=−0.047, p=0.252, n=444 genera |
| NB05 | Complete | `data/mgnify_vs_spire_comparison.csv` — cross-dataset CV RMSE comparison |

### Confound diagnostics (NB06/NB07)
Executed to validate H5 niche-breadth construct.

| Notebook | Status | Key output |
|----------|--------|------------|
| NB06 | Complete | `data/nb06_genome_levins_b_pgls.csv` — genome-sampling Levins' B PGLS: β=−0.056, p=0.41, λ=0.204 |
| NB07 | Complete | `data/nb07_study_controlled_pgls.csv` — study-effort confound: Pearson r=0.80 vs study count; β sign flip after control |

---

## Results (target: PF1_Cu)

### Spatial block CV RMSE (5-fold, NB02)

| Model | Mean RMSE | SD |
|-------|-----------|----|
| B0 (mean baseline) | 0.0501 | 0.0213 |
| B1 (pH + OC) | 0.0547 | 0.0186 |
| B2 / M2 (all SoilGrids) | 0.0439 | 0.0220 |
| M1 (MAG density only) | 0.0527 | 0.0197 |
| M3 (MAG density + SoilGrids) | **0.0400** | 0.0185 |

### Hypothesis outcomes

| ID | Outcome | Notes |
|----|---------|-------|
| H1 | **NOT supported (Cu only)** | M1 RMSE (0.0527) > B0 (0.0501); MAG density alone does not beat the mean; As/Cd/Cr/Hg/Pb untested |
| H2 | **NOT supported (Cu only)** | M1 RMSE (0.0527) > M2 (0.0439); SoilGrids outperforms MAG density features; As/Cd/Cr/Hg/Pb untested |
| H3 | **Supported (Cu only)** | M3 RMSE (0.0400) < M1 (0.0527); combining features improves prediction; As/Cd/Cr/Hg/Pb untested |
| H4 | **Supported** | Australia holdout/CV ratio = 0.52 (< 1.25 threshold); caveat: n=43 MAGs, r²=−0.39 |
| H5 | **Consistent** | Genus-level β = −0.011 (p=0.22, n=254 genera); same sign as P1 β = −0.021 |

### SHAP feature importance (M3, NB02)

SoilGrids dominates: organic_carbon_density (0.0195) > clay_content (0.0120) > ph_h2o (0.0113). MAG density features are ~20× smaller (ko_per_mb_transport: 0.00073, others ≤ 0.0005). MAG density contributes marginally to the combined model.

### Interpretation

The genus-level signal from P1 does not extend to MAG-level prediction of local metal conditions. This is interpretable: individual MAG-level gene content is more variable than genus-level averages, and soil geochemistry is the dominant driver of metal mobility at this spatial resolution. The directional PGLS consistency (H5) and marginal M3 improvement suggest a weak signal is present but insufficient for reliable prediction.

---

## MGnify Extension (Exploratory)

A second data source (MGnify MAGs) has been scaffolded to test whether results replicate across datasets. All analyses in this section are exploratory and pending execution.

### Data

- **Coordinates + taxonomy:** `final_mags_geospatial_traits.csv` from `microbeatlas_metal_ecology` project
- **Mobility metadata:** `kescience_mgnify.genome` Spark table (mobile_fraction = proportion of genome on mobile elements)
- **KO annotations:** `kescience_mgnify.gene_eggnog` Spark table
- **Biome filter:** Soil, Rhizosphere, or Marine Sediment biomes only

### New hypotheses (exploratory)

- **H5:** MGnify M3 (KO + metal) outperforms B0 (baseline RMSE) — positive control check
- **H6:** MGnify M3 outperforms M2 (metal-only) — KO features add explanatory value  
- **H7:** MGnify M3 generalises across geographic hold-out sets (RMSE < B0 + 0.01)
- **H8:** SPIRE and MGnify genus-level PGLS β coefficients are positively correlated (ρ > 0.3)
  - Rationale: same KO set, same biology; expect consistent direction even if different effect sizes

### Notebooks

| Notebook | Goal | Output |
|----------|------|--------|
| `01b_mgnify_feature_matrix.ipynb` | Build feature matrix from MGnify metadata and KO annotations | `mgnify_mag_feature_matrix.csv` |
| `02b_mgnify_mobility_prediction.ipynb` | Test H5, H6, H7 via spatial block CV on mobile_fraction target | `mgnify_mobility_prediction_results.csv` |
| `03b_mgnify_geographic_holdout.ipynb` | Test geographic generalization (Australia holdout) | `mgnify_geographic_holdout.csv` |
| `04b_mgnify_pgls_validation.ipynb` | Genus-level PGLS (if taxonomy available) | `mgnify_pgls_validation.csv` |
| `05_mgnify_vs_spire_comparison.ipynb` | Compare CV RMSE, target distributions, and H8 (coefficient correlation) | `mgnify_vs_spire_comparison.csv` |

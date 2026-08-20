# per_ko_metal_associations

**Are there individual genes — across the full genome, not just curated metal-interacting KOs — whose presence in a MAG correlates with the bioavailable metal concentration at its sampling site?**

This is a genome-wide association study across environmental gradients. Previous projects (P1 `comprehensive_metal_ecology`, P4 `metagenomic_environment_prediction`) tested whether curated metal-interacting KOs predict metal conditions and found weak or null results at both genus and MAG levels. This project asks a broader question: does *any* gene in the functional genome carry an association with local metal bioavailability, including genes outside the curated list?

**Label:** All analyses in this project are **exploratory**. This is a hypothesis-generation screen. Significant results require independent replication before they can be claimed as discoveries.

---

## Status

NB00–NB07 complete and documented in REPORT.md. See INTERPRETATION_TABLE.md for a full hypothesis-outcome table.

---

## Hypotheses

| ID | Statement | Test | Success criterion | Outcome |
|----|-----------|------|-------------------|---------|
| H1 | ≥20 KO-metal pairs reach FDR q<0.05 in MGnify | Per-KO logistic regression | ≥20 pairs | **SUPPORTED** (219 pairs) |
| H2 | KO-metal associations directionally consistent between MGnify and SPIRE | Cross-dataset β comparison | Spearman ρ > 0.2 | **NOT SUPPORTED** (ρ=0.059, n=324) |
| H3 | Curated metal KOs enriched among FDR-sig associations | Fisher's exact test | p < 0.05 | **NOT SUPPORTED** (OR=1.52, p=0.39) |
| H4 | ≥10 H1 pairs survive latitude adjustment | Latitude-adjusted logistic | ≥10 survive | **SUPPORTED** (138/219) |
| H5 | β stability ρ > 0.5 (adjusted vs unadjusted) | Spearman correlation of betas | ρ > 0.5 | **SUPPORTED** (ρ=0.923) |
| H6 | Adjusted cross-dataset β correlation > unadjusted | Compare adj vs unadj ρ | adj ρ > 0.059 | **NOT SUPPORTED** (adj ρ=0.049) |
| H7 | ≥10 H1 pairs survive class-level taxonomic control | Class-level logistic, genome-wide FDR | ≥10 survive | **SUPPORTED** (92/219) |
| H8 | β stability ρ > 0.7 (phylum vs class model) | Spearman correlation | ρ > 0.7 | **SUPPORTED** (ρ=0.925) |
| H9 | ≥5 H1 pairs survive phylo-PC continuous control | Phylo-PC logistic, genome-wide FDR | ≥5 survive | **SUPPORTED** (8/219) |
| H10 | ≥10 H1 pairs survive MAG quality covariate control | Quality-covariate logistic | ≥10 survive | **SUPPORTED** (200/219) |

---

## Data sources

| Source | Content | Used for |
|--------|---------|----------|
| `kescience_mgnify.genome` | MGnify MAG metadata (genome_id, lat, lon, completeness, contamination, biome, genus, phylum) | Primary dataset; MAG quality (Phase 3) |
| `kescience_mgnify.gene_eggnog` | Per-gene eggnog annotations for MGnify MAGs (KEGG_ko) | KO annotations (primary) |
| `microbeatlas_metal_ecology/data/final_mags_geospatial_traits.csv` | MGnify MAG coordinates with full environmental traits | Lat/lon join |
| `refdata.spire.genome_metadata` + `refdata.spire.mag_coordinates` | SPIRE MAG metadata | Secondary dataset |
| `arkinlab.spire.eggnog_annotations_spire` | SPIRE eggnog annotations (~6,270 MAGs) | KO annotations (secondary; limited coverage) |
| `arkinlab.envdbs.csu_metal_mobility_grid` | CSU PF1 metal mobility fractions | Environmental metal targets |
| `comprehensive_metal_ecology/data/curated_mrg_ko_ids_v2.csv` | 730-KO curated metal-interacting list | H3 enrichment baseline; NB06 cross-validation |

**Metal targets (actual):** PF1_As, PF1_Cd, PF1_Cr, PF1_Cu, PF1_Hg, PF1_Pb (six metals). PF1_Zn was pre-specified in the research plan but was absent from the CSU grid join, so results cover six metals only.

**KO inclusion:** ALL KOs present in ≥ max(10, 1% of MAGs) — no pre-filtering to curated list.

---

## Directory structure

```
per_ko_metal_associations/
├── data/
│   ├── mgnify_all_ko_matrix.parquet          # MAG × KO binary presence matrix (12.7M rows)
│   ├── spire_all_ko_matrix.parquet           # SPIRE MAG × KO matrix (3.3M rows)
│   ├── mgnify_all_ko_associations.csv        # 38,706 rows; unadjusted MGnify logistic results
│   ├── spire_all_ko_associations.csv         # 28,554 rows; unadjusted SPIRE results
│   ├── cross_dataset_comparison.csv          # 26,850 shared KO-metal pairs with betas from both datasets
│   ├── functional_enrichment.csv             # H3: enrichment of curated KO categories
│   ├── functional_enrichment_per_metal.csv   # H3: per-metal category enrichment
│   ├── mgnify_adj_ko_associations.csv        # 38,706 rows; latitude-adjusted MGnify results (H4/H5/H6)
│   ├── spire_adj_ko_associations.csv         # 28,554 rows; latitude-adjusted SPIRE results
│   ├── h1_multi_metal_adjusted.csv           # 219 rows; Phase 2 multi-metal robustness
│   ├── h1_robustness_summary.csv             # 219 rows; all-controls survival summary
│   ├── mgnify_class_ko_associations.csv      # 38,706 rows; class-level control (NB05 H7/H8)
│   ├── mgnify_phylopc_ko_associations.csv    # 38,706 rows; phylo-PC control (NB05 H9)
│   ├── mgnify_phylo_pcs.csv                  # 8,585 MAGs × 20 GTDB taxonomy PCs
│   ├── h1_fine_taxonomy_adjusted.csv         # 219 rows; Phase 4 class-level targeted results
│   ├── mgnify_mag_quality.csv                # 8,585 rows; completeness + contamination (H10)
│   ├── h1_mag_quality_adjusted.csv           # 219 rows; Phase 3A quality covariate results
│   ├── h1_mag_quality_sensitivity_95.csv     # 219 rows; Phase 3B (≥95%/≤2%, n=3,520 MAGs)
│   ├── h1_mag_quality_sensitivity_97.csv     # 219 rows; Phase 3C (≥97%/≤1%, n=1,854 MAGs)
│   ├── category_enrichment_per_ko.csv        # 5 rows; NB06 Fisher enrichment by category
│   ├── phylo_survivor_categories.csv         # 8 rows; phylo-PC survivors with curated category
│   ├── firth_spotcheck.csv                   # 20 rows; Firth vs standard logistic direction check
│   └── phase1_investigation.md               # Metal co-occurrence + feasibility report
├── figures/
│   ├── volcano_ko_metal_associations.png     # genome-wide volcano plots per metal
│   ├── top_ko_associations_per_metal.png     # top 12 associations per metal
│   ├── shared_ko_multi_metal.png             # KOs significant in ≥2 metals
│   ├── pvalue_histograms.png                 # unadjusted and adjusted p-value distributions
│   ├── beta_stability_h1_pairs.png           # unadjusted vs adjusted betas for H1-sig pairs
│   ├── beta_cross_dataset.png                # MGnify vs SPIRE beta scatter
│   ├── phylo_pc_scree.png                    # GTDB taxonomy PC variance scree
│   ├── h8_beta_stability_phylum_vs_class.png # phylum vs class beta comparison (H8)
│   ├── h8_genus_vs_mag_betas.png             # MAG vs genus-level beta sensitivity
│   ├── nb05_model_survival.png               # H1-sig pair survival across models
│   ├── project_summary.png                   # overall project summary figure
│   └── cross_project_functional_split.png    # NB06: PGLS betas vs per-KO enrichment
├── notebooks/
│   ├── 00_build_ko_matrix.ipynb              # Spark: build MGnify + SPIRE KO matrices (NB00)
│   ├── 01_per_ko_associations.ipynb          # H1: genome-wide logistic regression (NB01)
│   ├── 02_cross_dataset_comparison.ipynb     # H2: cross-dataset beta comparison (NB02)
│   ├── 03_functional_enrichment.ipynb        # H3: curated KO enrichment (NB03)
│   ├── 04_covariate_adjusted_associations.ipynb # H4/H5/H6: latitude adjustment (NB04)
│   ├── 05_class_phylo_control.ipynb          # H7/H8/H9: class + phylo-PC control (NB05)
│   ├── 06_cross_validation_with_main_project.ipynb # NB06: cross-project validation
│   └── 07_elevation_sensitivity.ipynb        # NB07: elevation covariate for 88 robust pairs; 83/88 survive, ρ=0.959
├── scripts/
│   ├── association_utils.py                  # core logistic engine (checkpoint/resume, FDR)
│   ├── ko_matrix_utils.py                    # build MAG × KO matrix from Spark annotations
│   ├── cross_dataset_utils.py                # merge results, directional comparison
│   ├── run_nb04_associations.py              # standalone NB04 runner (OOM-resistant)
│   ├── run_nb05_associations.py              # standalone NB05 runner
│   ├── run_robustness_controls.py            # Phase 2/4/6 robustness analyses
│   ├── run_phase3_mag_quality.py             # Phase 3 MAG quality sensitivity
│   ├── compute_phylo_pcs.py                  # GTDB taxonomy TruncatedSVD
│   ├── make_project_summary_figure.py        # project summary figure
│   ├── plot_and_analyse_associations.py      # volcano/top-hit figures
│   ├── run_soil_restricted_associations.py   # soil/rhizo-restricted MGnify sensitivity (standalone)
│   ├── run_elevation_sensitivity.py          # elevation sensitivity for 88 pairs (use NB07 from JupyterHub instead)
│   └── join_soilgrids.py                     # (not used; SoilGrids unavailable)
├── docs/
│   └── pitfalls.md                           # project-specific pitfalls log
├── REPORT.md
├── RESEARCH_PLAN.md
├── INTERPRETATION_TABLE.md
└── README.md
```

---

## Execution order

```
NB00 (Spark required) → NB01 (Spark or cached) → NB02 → NB03 → NB04 → NB05 → NB06 → NB07 (Spark required)
```

NB00 must run first; it produces `mgnify_all_ko_matrix.parquet` and `spire_all_ko_matrix.parquet`. NB01 is compute-intensive (~2–4 hours on 128 CPUs with multiprocessing; checkpoint/resume enabled). NB02 requires both NB01 outputs (MGnify + SPIRE CSVs). NB04–NB06 read cached CSVs from prior notebooks and run locally without Spark.

---

## Reproduction

### Requirements

```bash
pip install -r requirements.txt
```

Key dependencies: `statsmodels`, `scipy`, `scikit-learn`, `pandas`, `numpy`, `pyarrow`, `matplotlib`, `seaborn`.

NB00 additionally requires a running Spark session (`pyspark`) connected to the BERDL Lakehouse (JupyterHub environment).

### Execution

1. **NB00** — Run on JupyterHub (requires Spark). Produces both KO matrices.
2. **NB01** — Run on JupyterHub or locally. Compute-intensive: uses `fork`-based multiprocessing across 6,451 KOs × 6 metals. Set `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1` before launch. Checkpoint/resume is enabled — safe to restart.
3. **NB02–NB06** — Run locally from cached parquet/CSV outputs. No Spark required.
4. **NB07** — Run on JupyterHub (requires Spark). Fetches ETOPO1 elevation and runs elevation-adjusted regressions for the 88 robust pairs. ~5–10 min.

Approximate runtimes: NB00 ~15 min (Spark), NB01 ~3 hours (128 CPUs), NB02–NB06 ~5 min each, NB07 ~10 min (Spark).

---

## MAG quality thresholds

- Domain: Bacteria only
- Completeness ≥ 70%
- Contamination ≤ 10%
- Coordinates required (latitude, longitude not null)
- Environmental samples only: exclude host-associated ENVO terms

---

## Relationship to other projects

- **comprehensive_metal_ecology** (P1): Source of curated 730-KO list used for H3 enrichment baseline. NB06 tested whether the functional split from P1 is recapitulated in per-KO associations — result: null.
- **metagenomic_environment_prediction** (P4): MAG-level prediction attempt with curated KOs; null H1/H2 result motivates this genome-wide screen.
- **microbeatlas_metal_ecology**: Source of `final_mags_geospatial_traits.csv` with MGnify MAG coordinates.

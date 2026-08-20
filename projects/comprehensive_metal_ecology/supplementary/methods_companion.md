# Comprehensive Methods Companion: Metal-Gene Ecology in Bacteria

**Version:** 1.0  
**Date:** 2026-07-14  
**Project:** `comprehensive_metal_ecology`  
**Manuscript target:** ISME Journal  

This document describes all analyses reproducibly enough that an independent researcher with BERDL Spark access could replicate from scratch.

---

## 1. Data Sources and Processing

### 1.1 Genus-level pangenome and KO annotation

**Source:** BERDL Spark database `kbase.ke_pangenome`  
**Processing:** Apache Spark 4.0.1 (PySpark 4.0.1) via JupyterHub or `berdl_notebook_utils.setup_spark_session.get_spark_session()`  
**Notebooks:** `00_gene_list_profile.ipynb`, `01_primary_pgls_metal-gene_density.ipynb`

Per-genome KO counts were aggregated to genus level (arithmetic mean across GTDB-assigned genomes), then normalised by mean genome size in Mb to obtain KO density (KOs per Mb). Genera required ≥3 MAGs for inclusion. The primary predictor `ko_per_mb_primary` covers all Tier 1+2 KOs (see §1.2). Z-scores (`predictor_z`, `genome_mb_z`) were computed globally across all 1,574 bacterial (95 archaeal) genera retained after quality filters.

**Output:** `data/01_genus_ko_density_spark.csv`, `data/01_pgls_input_bacteria.csv` (n=1,574 genera; columns: `genus_lower`, `ko_per_mb_primary`, `mean_genome_mb`, `mean_levins_B_std`, `phylum`, `kingdom`, `predictor_z`, `genome_mb_z`)

### 1.2 Curated metal-gene set (five tiers)

**Source:** Manual curation from KEGG, BacMet, and literature; QC-confirmed against Pfam domains  
**File:** `data/supp_table_metal_ko_curation.csv` (153 KOs total)  
**Columns:** `KO`, `gene_name`, `metal`, `evidence_tier`, `source_database`, `biochemical_rationale`

Tier breakdown:

| Tier | n KOs | Description |
|------|-------|-------------|
| Tier 1 | 2 | Highest-confidence; multiple sources, structural evidence |
| Tier 2 | 13 | Strong biochemical evidence; curated databases |
| Tier 2-Fitness | 72 | Fitness-screen confirmed (BacMet + KEGG overlap) |
| Tier 3 | 66 | Good biochemical evidence, single source |

**Primary set** = Tier 1+2 = 15 KOs covering resistance efflux pumps (Tier 1 component) and metal cofactor biosynthesis (Tier 2 component). The `ko_per_mb_primary` predictor sums these 15 KOs.

Metals covered: Cu, Zn, Ni, Co, Fe, Mn, Hg, As, Cd, Pb, Cr. KO–metal assignments were used for per-metal PGLS models (`data/03_metal_pgls_results.csv`).

**Pfam QC:** Notebook `10_pfam_metal_qc.ipynb` checked 153 KOs against Pfam domain evidence. Result: 7.1% of KOs carry metal-binding domain evidence (`data/pfam_qc_results.csv`).

### 1.3 Niche breadth (Levins' B_std)

**Source:** Earth Microbiome Project (EMP) amplicon data; MicrobeAtlas (arkinlab_microbeatlas.otu_counts_long, otu_metadata, enriched_metadata)  
**Notebook:** `08_emp_niche_breadth.ipynb`  
**Spark table:** `refdata.emp_16s`; genus parsed from taxonomy via `REGEXP_EXTRACT(taxonomy, 'g__([^;]+)', 1)` or semicolon split at index 5

Cross-biome Levins' niche breadth B_std was computed across EMPO level-2 habitat categories (or continent-level biomes) for each genus. B_std was standardised to [0,1] range. Genera required presence in ≥10 samples and detection in ≥2 habitat categories.

**Output:** `data/01_pgls_input_bacteria.csv` column `mean_levins_B_std`; range [0.0008, 0.7474]  
**Soil-restricted niche breadth:** computed separately using only soil-labelled samples from MicrobeAtlas (EMPO soil categories); `data/soil_sample_genus_niche.csv`

### 1.4 Phylogenetic tree

**Source:** GTDB r214 genus-level consensus trees  
**Files:**  
- Bacteria: `projects/microbeatlas_metal_ecology/data/gtdb_bac_genus_pruned.tree` (2,283 tips)  
- Archaea: `projects/microbeatlas_metal_ecology/data/gtdb_arc_genus_pruned.tree`

Trees were pruned to the genera in each analysis dataset using `ape::drop.tip()`. Genus names were matched after replacing spaces with underscores.

### 1.5 Environmental covariates

All environmental data joined to MicrobeAtlas samples via latitude/longitude or Spark join keys.

| Variable | Source | Spark table/file | Scale | Notes |
|----------|--------|-----------------|-------|-------|
| Soil pH | SoilGrids (OLM) | `arkinlab_microbeatlas.enriched_metadata_gee.olm_soil_ph_0cm_H2O` | Divide stored value by 10 for pH units | Join via SRS_Join_Key (extract from accession_id) |
| Air temperature | ERA5 | `arkinlab_microbeatlas.enriched_metadata_gee.ERA5_mean_2m_air_temperature_K` | Kelvin | Same join as pH |
| Bedrock metals (Cu,Ni,Zn,Co,Cr,Pb,As,Cd,Hg) | GeoROC | `arkinlab_microbeatlas.enriched_metadata` columns `GeoROC_Rocks_georoc_*_ppm` | ppm | Direct join via accession_id |
| Soil metals (ICP-MS, 8 metals) | NGSA (Australia) | `arkinlab_envdbs.ngsa_geochemistry` | mg/kg | Australia only (lat -45 to -10, lon 110-155); spatial join 200 km threshold; detection-limit strings (`<0.x`) coerced to NaN via `pd.to_numeric(errors='coerce')` |
| Soil metals (MMI_ME, 8 metals) | NGSA (Australia) | Same table, MMI_ME columns | mg/kg | Mobile metal ion extraction; same spatial join |
| Metal mobility fractions (6 metals) | CSU global grid | `/home/hmacgregor/data/envdbs/global_mobility_grid.parquet` | Fraction [0,1] | 7.4M cells at 0.045° resolution; KDTree nearest-neighbour (threshold 0.09°); columns PF1_As, PF1_Cd, PF1_Cr, PF1_Cu, PF1_Hg, PF1_Pb |

**Join key fix:** `enriched_metadata.accession_id` has format `SRR4241976.SRS1690913`; `enriched_metadata_gee.SRS_Join_Key` = `SRS1690913`. Extract SRS part: `F.split(accession_id, "[.]").getItem(1)`.

**OTU taxonomy fix:** `arkinlab_microbeatlas.otu_metadata.Genus` is NULL for all rows. Genus must be parsed from `Tax` column: `F.when(F.size(F.split("Tax", ";")) >= 6, F.split("Tax", ";").getItem(5))`.

---

## 2. Primary PGLS Framework

**Model:** `mean_levins_B_std ~ ko_per_mb_primary_z + genome_mb_z`  
**Software:** R 4.5.3, `nlme` 3.1.169, `ape` 5.8.1  
**Script:** `results/pgls_analysis.R`

Pagel's λ was estimated jointly with regression coefficients via:

```r
gls(mean_levins_B_std ~ predictor_z + genome_mb_z, data=df,
    correlation=corPagel(value=1, phy=tree, fixed=FALSE, form=~genus_tree),
    method="ML", na.action=na.omit)
```

Fallback to λ=0 (OLS) when optimisation fails (rare; logged). λ=1 corresponds to Brownian motion expectation; λ=0 corresponds to phylogenetic independence.

**Primary result (bacteria):** n=1,574, λ=0.757, β(ko_z)=−0.0207 (SE=0.00368, p=2.1×10⁻⁸), β(genome_z)=+0.006 (SE≈0.004)  
**Primary result (archaea):** n=95, λ=0.726, β(ko_z)=−0.0137, p=0.119 (directionally consistent, underpowered)

**File:** `data/01_primary_pgls_results.csv`

**Phylogenetic permutation check:** PIC (phylogenetically independent contrasts) used as a check on PGLS; confirmed same sign and similar magnitude.

**Per-Mb density:** Normalised by mean genome size to avoid spurious correlation between genome size and total KO count. Genome size included as covariate.

---

## 3. Functional Landscape and Split Analyses

**Notebook:** `18_functional_landscape.ipynb`, `03_tier_and_category_analysis.ipynb`  
**Files:** `data/03_category_pgls_results.csv`, `data/03_tier_pgls_results.csv`

### 3.1 19 KEGG functional categories

KO density computed per BKEGG category (19 categories) and PGLS run independently for each. Metal-related categories serve as true-positive contrasts; all others serve as landscape context (genome-streamlining signal).

### 3.2 Resistance vs cofactor subcategories (Tier split)

**Tier 1 (resistance):** efflux pumps, detoxification; `ko_per_mb_tier1`  
**Tier 2 (cofactor):** metal-dependent biosynthesis; `ko_per_mb_tier2`  
Model: `mean_levins_B_std ~ tier1_z + tier2_z + genome_mb_z`

**Finding:** Cofactor biosynthesis (tier2) carries the signal (β<0, p<0.05); resistance genes (tier1) show no association. File: `data/03_tier_pgls_results.csv`.

### 3.3 H5c split (essential biosynthetic set)

An expanded essential biosynthetic set was defined. Joint model including essential vs accessory term tested to address H5c confounding.

### 3.4 H4c cofactor–translation confounding

KO overlap between cofactor set and translation-related functions was audited (NB02 reviewer response). Three-predictor model adds translation proxy. Results in `results/category_conditional_models.csv`.

---

## 4. Cross-biome and Soil-restricted Analyses

**Primary response:** `mean_levins_B_std` (cross-biome Levins' B, EMP habitat categories)  
**Soil response:** `soil_niche_breadth` from soil-only samples (MicrobeAtlas EMPO soil categories)  
**Files:** `data/soil_sample_genus_niche.csv`, `data/01_soil_restricted_pgls_results.csv`

Soil-specialist genera were defined as those with ≥70% of samples in soil EMPO categories. Soil-restricted PGLS run on this subset separately. Result: stronger signal in soil specialists (Finding 10).

Sampling depth (total read count, log-transformed) included as covariate in sensitivity checks.

---

## 5. Two-scale Phylogenetic Signal (phylo-D)

**Notebook:** `05_sensitivity_analyses.ipynb` (phylo-D section)  
**Files:** `data/phylo_d_ko_presence.csv`, `data/phylo_d_all_ko.csv`

Two scales:  
1. **Genus-level λ:** from primary PGLS; measures phylogenetic autocorrelation of B_std across genera  
2. **Genome-level D:** Fritz & Purvis' D statistic applied to binary KO presence/absence across genomes within genera

Sample size filter: ≥5 genomes per genus required for genome-level D. Double-signal criteria: D > 0.2 AND λ < 0.3 (13 KOs identified; all resistance/transport/sensing). Plasmid association enrichment test (script: `scripts/plsdb_resistance_crossref.py`):

**NCBI Entrez (preferred):** For each gene name, queried NCBI nuccore for `"{gene}"[Gene Name] AND plasmid[Filter]` (plasmid hits) and `"{gene}"[Gene Name]` (total hits); plasmid_frac = n_plasmid / n_total. Mann-Whitney U test (one-sided, alternative='greater') on plasmid fraction comparing double-signal resistance KOs vs background resistance KOs, filtered to n_total ≥ 50. Result: U=122, p=0.045 (n_double=3: merD 4.3%, aoxB 0.4%, norB 0.1%; n_background=51).

**BV-BRC validation:** Downloaded 84,446 unique plasmid accessions from BV-BRC `genome_sequence` table (records with "plasmid" in description, PATRIC annotation). Per-gene plasmid fraction computed via `genome_feature` table using RQL syntax. Large-n genes (n_total ≥ 10,000) estimated via 4-page evenly-spaced sampling to avoid excessive API pagination. Mann-Whitney U test same as NCBI. Result: U=83, p=0.044 (n_double=2: merD 7.2%, norB 0.3%; n_background=48 after arsC KO deduplication).

Genes untestable: gesA, gesB (n=1 in both databases); nrsD (n=16, below threshold). golS near-zero in both databases (NCBI frac=1.7×10⁻⁵, BV-BRC frac=3.5×10⁻⁴).

**Cross-category comparison (NCBI Entrez, all 275 KOs; `data/ncbi_plasmid_fraction_allcats.csv`):** Extended queries to all cofactor, metabolism, transport, and sensing KOs with n_total ≥ 50. Resistance > all non-resistance: Mann-Whitney p=0.020 (n=54 vs n=86). Resistance > metal-dependent metabolism: p=0.023 (n=54 vs n=14). Cofactor biosynthesis KOs (hemH ≤ 0.023%, MOCS2B = 0%) near-zero. The median plasmid-fraction gradient (resistance 0.00043 > transport ≈ sensing > metabolism > cofactor 0.00012) mirrors the phylogenetic-λ gradient across categories.

**Cross-category comparison (BV-BRC, all 275 KOs; `data/bvbrc_plasmid_fraction_allcats.csv`):** Same query extended to 88 non-resistance KOs (154 rows total). Resistance > all non-resistance: p=0.118 (NOT significant; n=51 vs n=82). Within-resistance DS vs BG confirmatory test: p=0.047 (n_double=2 vs n_bg=49; consistent with focused test p=0.044). Discordance from NCBI is attributable to the Transport/Homeostasis group in BV-BRC being inflated by resistance-classified metal efflux transporters (czcA, czcB) and the aph outlier (7.1% frac), collapsing the resistance vs transport gap.

Outputs: `data/plsdb_enrichment_test.json`, `data/bvbrc_plasmid_fraction.csv`, `data/ncbi_plasmid_fraction_allcats.csv`, `data/bvbrc_plasmid_fraction_allcats.csv`.

---

## 6. External Validation

**Notebook:** `11_enigma_frc_replication.ipynb`, `12_ngsa_proper_replication.ipynb`, `13_enigma_isolate_validation.ipynb`, `14_enigma_geochem_discovery.ipynb`, `15_ausmicrobiome_density_replication.ipynb`

| Dataset | Reference | n | Result |
|---------|-----------|---|--------|
| NGSA Australia | NGSA (Caritat & Cooper 2011) | 1,315 stations | Bedrock metal SD PGLS; replication of primary signal |
| AusMicrobiome | Bissett et al. 2016 | Variable | Genomic density replication; consistent direction, limited power |
| ENIGMA FRC | Frossard 2017 | 29 MAGs | Spearman ρ=−0.41 (burden proxy), p=0.029; coverage failure limits inference |
| Li 2022 | Li et al. 2022 | — | Literature validation |
| Frossard 2018 | Frossard et al. 2018 | — | Literature validation |
| Goff 2024 | Goff et al. 2024 | — | Literature validation |
| Abdelmageed 2021 | Abdelmageed et al. 2021 | — | Literature validation |

---

## 7. Sensitivity and Confounder Tests

**Notebooks:** `04_confounder_checks.ipynb`, `05_sensitivity_analyses.ipynb`, `06_confounder_discovery.ipynb`, `22_mag_quality_covariates.ipynb`, `24_niche_breadth_sensitivity.ipynb`, `25_split_magnitude_permutation.ipynb`, `26_interaction_test_jackknife.ipynb`

**Files:** `data/04_confounder_results.csv`, `data/05_sensitivity_results.csv`

| Test | Approach | Result |
|------|----------|--------|
| Genome size | Included as covariate in all models | Signal persists; genome_z β positive (larger genomes → broader niche) |
| Count-model offset | log(genome_size) as offset instead of covariate | Consistent |
| Three-predictor model | +translation proxy | Signal remains |
| GC content | Added as covariate | No change |
| Latitude | Added as covariate | No change |
| Mean annual temperature | Added as covariate | No change |
| MAG completeness/contamination | Quality bins as covariates | No change |
| Genus MAG count | log(n_MAGs) covariate | No change |
| OTU mapping discordance | Genus name concordance across databases | Audited |
| Sampling effort | log(n_samples) covariate | No change |
| Abundance weighting | Abundance-weighted KO density | Consistent |
| Continent-stratified PGLS | PGLS within each continent subset | Directionally consistent across 4/5 continents |
| Coreness-matched permutation | Null model matching core/accessory gene structure | Signal exceeds null (NB20) |
| Cofactor jackknife | Remove one KO at a time from cofactor set | Robust; `results/cofactor_jackknife_results.csv` (NB26) |
| Tree topology perturbation | Bootstrap tree variants | Consistent |

---

## 8. Community-Weighted Mean Analysis

**Notebook:** `29_cwm_from_env.ipynb`  
**File:** `data/cwm_from_env_cv_results.csv`

XGBoost trained to predict community-weighted mean (CWM) metal-gene density from environmental variables (pH, temperature, precipitation, elevation, NDVI, clay, lat/lon, log Cu/Zn/Pb/Ni ppm). Spatial 5-fold block cross-validation.

- Trait mean = 12.7 metal KO clusters, SD = 8.2
- Mean CV RMSE = 11.89 (range: 6.20–19.37 across blocks)
- SHAP analysis: metal features (Cu+Zn+Pb+Ni) = 45.9% of mean |SHAP|; top predictor: log_Ni_ppm (mean |SHAP|=2.23)
- Interpretation: metals structure community composition, but poor spatial-block generalization

Also tested: inverse RDA (NB28) — environmental variables predict community composition metrics via redundancy analysis.

---

## 9. Social Niche Breadth Analysis

**Notebook:** `results/social_niche_pgls.R`, data in `data/social_niche_breadth_data.csv`  
**Source:** EMP 16S rRNA surveys, EMPO level-3 habitat categories  
**n:** 700 genera (≥2 habitats); PGLS subset n=550 (tree-matched)

### 9.1 Metrics

1. **Count breadth (standardized):** Number of co-occurring genera / total genera; range [0.51, 1.00]; mean=0.966  
2. **Weighted breadth:** Mean Jaccard similarity (shared habitats / union habitats) with all co-occurring genera; mean=0.649  
3. **Shannon breadth (standardized):** Shannon diversity of co-occurrence distribution normalised to [0,1]; mean=0.983

### 9.2 Null model SES

100 permutations per genus (n=80 genera sampled), shuffling habitat assignments while preserving habitat frequency. SES = (observed − mean(null)) / SD(null).

### 9.3 Statistical models

Linear models (OLS; phylogenetic correction applied where tree overlap available) regressing social niche breadth against:
- Metal-gene KO density per Mb (predictor_z)
- Genome size (genome_mb_z)
- Cross-biome ecological breadth (Levins' B_std)

**Key result:** PGLS of count_breadth_std ~ Levins_B: β=0.00273, p=0.175, λ=0.012 (n=535; no significant association between ecological and social breadth). SES model (n=62): β=−0.380, p=0.004 (negative association when controlling for null expectation).

**Files:** `results/social_niche_breadth_results_full.csv`, `results/social_niche_pgls_results_table.csv`, `results/social_niche_breadth_correlations.csv`

---

## 10. Environmental Niche Breadth Analysis

**Scripts:** `scripts/env_niche_spark_analysis.py` (global), `scripts/env_niche_ngsa_only.py` (Australia NGSA)  
**PGLS script:** `results/env_niche_all_pgls.R`  
**Software:** Python 3.13.9, PySpark 4.0.1, pandas 3.0.3, numpy 2.4.4, scipy 1.17.1; R 4.5.3 / nlme 3.1.169 / ape 5.8.1

### 10.1 Niche breadth computation

For each genus, environmental niche breadth = SD of the environmental variable across all samples where the genus was detected (≥1 count). This measures physiological and geochemical tolerance breadth independent of cross-biome distributional breadth.

**Sample-genus mapping:** From Spark tables `arkinlab_microbeatlas.otu_counts_long` (sample_id IS the accession_id string) × `otu_metadata` (genus parsed from `Tax` column, semicolon-split, index 5). Collected as `groupBy(accession_id).agg(collect_set(genus_lower))` → exploded in Pandas to avoid exceeding Spark maxResultSize (1,024 MB limit).

| Response variable | Source | n_genera | Notes |
|------------------|--------|----------|-------|
| pH_sd | SoilGrids OLM | 3,433 | Spark aggregation; stored value ÷ 10 |
| temp_sd | ERA5 | 3,433 | Kelvin; Spark aggregation |
| georoc_Cu/Ni/Zn/Co/Cr/Pb/As/Cd/Hg_sd | GeoROC | 3,433 | ppm; 9 metals; Spark aggregation |
| PF1_As/Cd/Cr/Cu/Hg/Pb_sd | CSU global mobility grid | 3,429 | KDTree nearest-neighbour (threshold 0.09°); Pandas |
| ICP-MS Cu/Ni/Zn/Pb/As/Co/Cr/Hg_sd | NGSA Australia | 3,227 | KDTree 200 km threshold; detection limits coerced to NaN |
| MMI_ME Cu/Ni/Zn/Pb/As/Co/Cr/Hg_sd | NGSA Australia | 3,227 | Mobile metal ion extraction |

**CSU grid:** 7,376,940 cells at 0.045° resolution; global; columns PF1_As, PF1_Cd, PF1_Cr, PF1_Cu, PF1_Hg, PF1_Pb (mobility fractions [0,1]); threshold 0.09° (2× grid resolution); 236,605/278,952 samples matched.

**NGSA detection limits:** Values like `<0.2` coerced to NaN via `pd.to_numeric(errors='coerce')` before spatial join.

**Output files:**  
- `data/env_niche_global_spark.csv` (3,433 genera; pH_sd + temp_sd + 9 GeoROC metal SDs + counts)  
- `data/env_niche_csu_spark.csv` (3,429 genera; 6 CSU PF1 SDs + counts)  
- `data/env_niche_ngsa_spark.csv` (3,227 genera; 8 ICP-MS + 8 MMI_ME SDs + counts)

### 10.2 PGLS for environmental niche breadth

33 PGLS models run (1 per SD response), all with the same formula:  
`SD_response ~ predictor_z + genome_mb_z`

PGLS joined to primary predictor dataset (`01_pgls_input_bacteria.csv`, n=1,574) for tree overlap. Final n per model: ~1,520–1,574 (varies with non-null SD coverage). Pagel's λ estimated freely; fallback to λ=0 on convergence failure.

**Merged input:** `results/env_niche_all_pgls_input.csv`  
**Results:** `results/env_niche_all_pgls_results.csv`

---

## 11. Reproducibility and Data Availability

### 11.1 Software versions

| Software | Version |
|----------|---------|
| Python | 3.13.9 |
| PySpark | 4.0.1 |
| pandas | 3.0.3 |
| numpy | 2.4.4 |
| scipy | 1.17.1 |
| R | 4.5.3 |
| nlme | 3.1.169 |
| ape | 5.8.1 |

### 11.2 Key parameter decisions

- Genus minimum sample threshold: ≥10 samples for niche breadth computation; ≥3 MAGs for pangenome KO density
- Maximum spatial join distance: 0.09° for CSU grid; 200 km (≈1.8°) for NGSA
- Phylogenetic tree: GTDB r214 genus-level consensus (no polytomy resolution)
- PGLS method: ML (not REML) to allow likelihood-ratio testing between models
- λ starting value: 1.0; bounds [0, 1]; `fixed=FALSE` (estimated)

### 11.3 Key file inventory

| File | Location | Contents |
|------|----------|----------|
| Primary PGLS input | `data/01_pgls_input_bacteria.csv` | 1,574 bacterial genera; ko_per_mb_primary, genome_mb, B_std, predictor_z, genome_mb_z |
| Metal KO curation | `data/supp_table_metal_ko_curation.csv` | 153 KOs; 5 tiers; metal assignments |
| Phylogenetic tree (bacteria) | `../microbeatlas_metal_ecology/data/gtdb_bac_genus_pruned.tree` | GTDB r214, 2,283 tips |
| Primary PGLS results | `data/01_primary_pgls_results.csv` | All primary and sensitivity models |
| Tier PGLS results | `data/03_tier_pgls_results.csv` | Resistance vs cofactor split |
| Category PGLS | `data/03_category_pgls_results.csv` | 19 KEGG categories |
| Env niche (global) | `data/env_niche_global_spark.csv` | 3,433 genera; pH, temp, 9 GeoROC metals |
| Env niche (CSU) | `data/env_niche_csu_spark.csv` | 3,429 genera; 6 mobility fractions |
| Env niche (NGSA) | `data/env_niche_ngsa_spark.csv` | 3,227 genera; 8 ICP-MS + 8 MMI_ME |
| Env niche PGLS | `results/env_niche_all_pgls_results.csv` | 33 SD responses × 2 predictors |
| Social niche | `results/social_niche_pgls_results_table.csv` | Count, weighted, Shannon breadth PGLS |

### 11.4 Notebooks (in order)

| Notebook | Analysis |
|----------|----------|
| 00_gene_list_profile.ipynb | Metal gene set characterisation |
| 01_primary_pgls_metal-gene_density.ipynb | Primary PGLS |
| 02_ngsa_replication.ipynb | NGSA Australia replication |
| 03_tier_and_category_analysis.ipynb | Resistance/cofactor split; 19 KEGG categories |
| 04_confounder_checks.ipynb | Pre-specified confounders |
| 05_sensitivity_analyses.ipynb | Sensitivity and phylo-D |
| 06_confounder_discovery.ipynb | Data-driven confounder screen |
| 07_marine_and_geological_proxies.ipynb | Geological proxy controls |
| 08_emp_niche_breadth.ipynb | EMP EMPO-level B_std |
| 09_bacdive_niche_breadth.ipynb | BacDive strain niche validation |
| 10_pfam_metal_qc.ipynb | Pfam domain QC of KO set |
| 11_enigma_frc_replication.ipynb | ENIGMA FRC replication |
| 12_ngsa_proper_replication.ipynb | NGSA proper replication |
| 13_enigma_isolate_validation.ipynb | ENIGMA isolate validation |
| 14_enigma_geochem_discovery.ipynb | ENIGMA geochem discovery |
| 15_ausmicrobiome_density_replication.ipynb | AusMicrobiome replication |
| 17_negative_controls.ipynb | Null functional category controls |
| 18_functional_landscape.ipynb | 19-category functional landscape |
| 19_internal_structure_comparison.ipynb | Internal substructure |
| 20_coreness_permutation.ipynb | Coreness-matched permutation test |
| 21_aus_beta_comparison.ipynb | Australia β comparison |
| 22_mag_quality_covariates.ipynb | MAG quality sensitivity |
| 23_category_conditional_models.ipynb | Category conditional PGLS |
| 24_niche_breadth_sensitivity.ipynb | Niche breadth metric sensitivity |
| 25_split_magnitude_permutation.ipynb | Split magnitude permutation |
| 26_interaction_test_jackknife.ipynb | Cofactor jackknife |
| 27_inverse_pgls.ipynb | Inverse PGLS (metal → B) |
| 28_inverse_rda.ipynb | Inverse RDA |
| 29_cwm_from_env.ipynb | CWM prediction from environment |

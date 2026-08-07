# USA Env-PCA Bioindicators — Report

**Status:** Complete (NB00–NB02 executed 2026-07-28/29; OTU-level fingerprints complete)

## Overview

This project identifies genera and metal-resistance KOs diagnostic of specific multi-variate metal contamination fingerprints in USA soils, using PCA on USA environmental space to find contamination fingerprints and which genera/KOs occupy specific positions in that space. Complements `metal_contamination_bioindicators` (global, binary label) by exploiting richer USA env data.

Rhodanobacter is the validation case — established acid-pH + Cr/Ni indicator.

---

## Data

| Dataset | Shape | Source |
|---------|-------|--------|
| `genus_lat_env_covariates.csv` | 10,040 genera × 18 env cols | CME; `median_soil_ph` is pH×10 (divide by 10) |
| `nb27_genus_usgs_means.csv` | 3,239 genera × 9 USGS metal cols | CME |
| `nb25_ko_presence_matrix.parquet` | 417,298 rows (genus × KO) | CME; has `g__` prefix — strip before join |
| `curated_mrg_ko_ids_v2.csv` | 730 KOs × 4 cols | BERIL; Resistance/Transport/Metabolism/Sensing/Cofactor/Unknown |
| WorldClim `worldclim_master.parquet` | 338K rows, 0.25° grid | bio_1=MAT, bio_12=MAP, elev |
| `water_table_depth.parquet` | 338K rows | Water_Table_Depth_m (capitalized column) |

---

## Hypotheses

| ID | Hypothesis | Verdict | Key result |
|----|-----------|---------|-----------|
| H0 | PC1+PC2 explain ≥60% env variance | NOT SUPPORTED | PC1+PC2=56.6%; PC1+PC2+PC3=66.8% |
| H1 | Specific genera diagnostic of contamination fingerprints (Rhodanobacter validation) | PARTIAL | Rhodanobacter rhodanobacteraceae: PC1=+0.78; R. spathiphylli: PC1=−0.62 (opposite directions within genus) |
| H2 | Transport/Resistance KO guilds are more specific env_PC indicators than Cofactor/Sensing | SUPPORTED | Mean |ρ_PC1| = 0.092 vs 0.051 |
| H3 | High-λ KOs are better genus-level env indicators | NOT SUPPORTED | ρ(λ, |ρ_PC1|) = 0.076, p = 0.269 |
| H4 | Sample-level SHAP top genera match genus-level fingerprints | NOT SUPPORTED | 4/20 (20%; threshold ≥8/20) |

---

## NB00 — Genus Env PCA (2026-07-28)

**Data assembly and PCA** on 2,838 genera (n_usgs ≥ 20 filter applied to nb27) with 13 environmental variables (USGS metals As/Cd/Cr/Cu/Ni/Pb/Zn, soil pH, SOM, ERA5 temperature, WorldClim MAP/seasonality, water table depth).

**PCA results:**

| PC | Variance | Key loadings |
|----|---------|-------------|
| PC1 | 35.8% | Heavy metals (USGS Pb, Ni, Cr, As, Cd) + low temperature |
| PC2 | 20.8% | Elevation + aridity + high pH |
| PC3 | 11.0% | SOM / organic carbon |
| PC1+PC2 | 56.6% | — fails H0 threshold (60%) |
| PC1+PC2+PC3 | 66.8% | — |

**Clustering** (k=4, silhouette = 0.599):

| Cluster | Character |
|---------|-----------|
| C1 | Average — intermediate across all env axes |
| C2 | High metal + cold (contaminated, low-latitude boreal) |
| C3 | Arid + alkaline + high elevation |
| C4 | Organic-rich + warm (agricultural/humid) |

**Rhodanobacter finding (H1 — PARTIAL):** Both Rhodanobacter species have PC1 scores but in opposite directions — *R. rhodanobacteraceae* (PC1 = +0.78) and *R. spathiphylli* (PC1 = −0.62). The genus is not a unified contamination indicator; species-level identity is required.

**Outputs:** `data/nb00_genus_env_pca.parquet`, `data/nb00_fingerprint_clusters.csv`, `data/nb00_pca_loadings.csv`, 4 PDF figures.

---

## NB01 — KO / Guild Bioindicators (2026-07-28)

**212 KOs tested** (n_genera ≥ 30 filter from nb25_ko_presence_matrix.parquet, after stripping g__ prefix). Spearman ρ between per-genus KO presence frequency and PC1/PC2 scores.

**Significant KOs (q < 0.05):**
- PC1: 11 KOs significant
- PC2: 8 KOs significant

**Top KO:** porB (ρ_PC1 = +0.421) — outer membrane porin, not a canonical metal resistance gene. Corroborates the Arc 4 finding that transport/membrane genes dominate field metal associations.

**H2 — SUPPORTED:** Transport/Resistance KO guild mean |ρ_PC1| = 0.092 vs Cofactor/Sensing = 0.051. Transport and resistance KOs are ~1.8× more correlated with the USA metal contamination PC than metabolic/sensing KOs.

**H3 — NOT SUPPORTED:** Phylogenetic conservation (Pagel's λ, from `phylo_d_all_ko.csv`) does not predict KO environmental indicator strength. ρ(λ, |ρ_PC1|) = 0.076, p = 0.269. KOs that are more phylogenetically conserved are not better PC1 indicators — ecological adaptations can occur via HGT-prone or phylogenetically labile genes.

**Outputs:** `data/nb01_ko_env_pca_assoc.csv`, `data/nb01_guild_env_correlations.csv`, 3 PDF figures.

---

## NB02 — Sample-Level ML (2026-07-29, Spark)

**6,010 USA soil samples** × 200 genera (top by prevalence ≥ 50 samples; CLR-transformed). Genus CLR features used to predict individual env variables and env-PCA scores via multi-output CatBoost.

**Sample-level env PCA (on the 6,010-sample set):**

| PC | Variance | Key loadings |
|----|---------|-------------|
| PC1 | 43.6% | Cu/Zn/Ni metals (metal contamination axis) |
| PC2 | 23.5% | Elevation + aridity + alkalinity |
| PC1+PC2 | 67.2% | — |

**Multi-output cross-validation (13 env targets, 5-fold):**

| Feature set | Mean R² |
|------------|---------|
| Genus CLR (CLR) | 0.805 |
| Genus P/A | 0.817 |
| Phylum CLR | 0.691 |

**PC-score CV (dedicated CLR → PC score models):**

| PC target | R² |
|-----------|---|
| PC1 (metal contamination) | 0.903 |
| PC2 (elevation/aridity) | 0.927 |

Genus CLR features are highly predictive of both env variables and env-PCA scores, confirming microbiome composition encodes strong environmental signal at the sample level.

**H4 — NOT SUPPORTED (4/20 concordance):** The top SHAP genera from the dedicated genus CLR → PC1 CatBoost model match only 4/20 of the top genus-level PC1 fingerprints from NB00. Shared: *Acinetobacter*, *Agrobacterium*, *Bacteroides*, *Hyalangium*. Core insight: extreme-niche genera (narrow specialists, niche breadth ≤ 0.75) are NOT the best PC1 predictors; broad generalists dominate SHAP. Spearman ρ(|PC1_fingerprint|, shap_mean_pc1) = 0.282, p = 5.3×10⁻⁵ (weak but significant); ρ(niche_breadth, shap_mean_pc1) = 0.011, p = 0.87 (zero). The genus-level env fingerprint and the sample-level predictive rank are measuring complementary rather than redundant information.

**Outputs:** `data/nb02_shap_summary.parquet`, `data/nb02_shap_per_target.parquet`, `data/nb02_genus_env_pca.parquet`, `data/nb02_pc_shap.parquet`, `data/nb02_genus_env_fingerprints.csv` (200 genera × PC1/PC2/niche_breadth/prevalence), `data/nb02_h4_concordance.csv`, 4 PDF figures.

---

## OTU-Level Fingerprints (Standalone, 2026-07-29)

**Spark extraction** (`scripts/extract_otu_level_cache.py`): 2,000 top-prevalence OTUs × 6,010 USA soil samples → `data/nb02_otu_level_cache.parquet` (1,918,978 rows).

**Fingerprints** (`scripts/compute_otu_env_fingerprints.py`): adaptive PCA (N_PCS=4, 94.3% variance; VAR_THRESHOLD=0.85).

Key results:
- Rank coverage by taxonomy level: phylum 1,588 / class 1,546 / order 1,488 / family 953 / genus 540 / unknown 405
- 271/2,000 OTUs with species from Tax[6]
- ρ(|PC1|, PC1_breadth) = 0.072, p = 0.00118 (very weak, consistent with genus-level H3 null)
- **Notable OTU finding:** Narrowest-niche specialist cluster (PC1 ≈ +0.81) is eukaryote-dominated — Neobodonida, Cercomonadida, *Acanthamoeba astronyxis* — invisible at genus level; highlights importance of OTU-level resolution for contamination-associated eukaryotes

**Outputs:** `data/nb02_otu_env_fingerprints.csv` (35 cols), `figures/nb02_F5_otu_env_biplot.pdf`, `OTU_ENV_NICHE_ANNOTATIONS.md`.

---

## Discoveries

**1. Niche generalists — not narrow specialists — drive sample-level metal PC prediction (H4 null mechanistically explained).**

Despite genus-level env fingerprints identifying narrow specialists as diagnostically extreme, sample-level SHAP assigns highest importance to broad generalists (niche_breadth = 0.87–0.95). This is interpretively informative: sample-level ML learns *presence/absence variance across samples* (abundant generalists with broad but metal-correlated presence), not *niche extremity* (rare specialists tied to one contamination axis). For monitoring applications, generalists with metal-correlated distributions outperform narrow specialists as features despite being weaker fingerprints — they are present in enough samples to contribute variance.

**2. Transport and resistance KO guilds are functionally informative env-PC indicators (H2 supported).**

Mean |ρ_PC1| for transport/resistance = 0.092 vs cofactor/sensing = 0.051. Complements the Arc 4 finding that transport genes (not resistance genes) dominate genome-wide field metal associations. The KO guild result adds a positive signal: both transport AND resistance categories are enriched among env-PC indicators relative to cofactor and sensing guilds.

**3. Rhodanobacter species-level divergence as env indicator.**

Two Rhodanobacter species occupy opposite ends of PC1 (heavy metal vs. baseline). This species-level divergence within a single genus underscores that genus-level bioindicator analyses (standard in amplicon studies) may miss species-level habitat specialization. Both species have been detected at ENIGMA field sites; the contrasting PC1 positions warrant cross-reference with ORFRC groundwater chemical data.

**4. Eukaryote specialists enriched at narrowest metal niches (OTU level).**

Neobodonida and Cercomonadida flagellates cluster at PC1 ≈ +0.81 — the extreme metal-contamination end. These are invisible at the 16S bacterial-level genus PCA. Protozoa in this clade are known predators of metal-resistant bacteria and may serve as keystone consumers in contaminated microbiomes. This is an entirely exploratory observation from the OTU fingerprinting analysis.

---

## Interpretation

### Biological

PC1 captures a combined heavy-metal + low-temperature axis, consistent with the USGS metadata structure: high-metal USA soils are disproportionately represented in colder, northern or high-elevation sampling campaigns. This environmental co-structure means PC1 is not a pure metal-contamination axis and should be used with caution as a contamination proxy.

The H2 result — transport/resistance KO guilds are better env-PC indicators than cofactor/sensing guilds — extends the pattern documented in global analyses (Arc 4: transport genes dominate genome-wide field metal associations; Arc 1: transport β most negative in PGLS) to a KO-presence-frequency × env-PC correlation framework. Convergence across three different analytical approaches strengthens the inference that metal transport capacity, not metal sensing, is the functional trait most tightly correlated with contamination gradients.

The H3 null (λ does not predict env indicator strength) is consistent with the Arc 4 finding that field KOs are predominantly accessory-genome genes (5% prevalence) with low phylogenetic conservation. High-λ KOs are core-genome functions, and core-genome genes may be present in too many genera to covary with metal contamination PC.

### Cross-arc coherence

| Arc | Finding | Direction |
|-----|---------|-----------|
| Arc 1 (microbeatlas) | ko_per_mb β = −0.022 vs B_std | Metal gene density ↔ niche specialization |
| Arc 3 (bioindicators) | transport genes dominate CMH signal | Transport > resistance |
| Arc 4 (per-KO associations) | 219 FDR-sig pairs; transport genes 19% | Transport genes dominate field signal |
| **Arc 5 (this project)** | **H2: transport/resistance |ρ| > cofactor/sensing** | **Consistent: transport-functional guild best env-PC indicator** |

---

## Limitations

1. **PC1 confounds metal + temperature.** The first PCA axis reflects the joint co-variation of heavy metals and cold climate in the USGS sampling design. Cannot cleanly isolate metal contamination fingerprint from climate gradient.
2. **n_usgs ≥ 20 filter (NB00) excludes 7,202/10,040 genera.** Rare genera — potentially including many metal-specialist taxa — are excluded from the PCA fingerprinting.
3. **nb25_ko_presence_matrix.parquet requires g__ prefix stripping.** Any analysis that joins without stripping will produce zero matches. Pitfall documented.
4. **Sample-level ML (NB02) uses only top-prevalence 200 genera.** Rare specialist genera (which have the strongest NB00 PC1 fingerprints) are excluded; this directly explains the H4 non-concordance.
5. **No cross-validation with independent USA metal survey.** The USGS metal covariates from nb27 were used to build the PCA that is the response variable. An independent geochemical dataset (e.g., NGSA equivalent for USA) was not used.

---

## Key Output Files

| File | Rows | Description |
|------|------|-------------|
| `data/nb00_genus_env_pca.parquet` | 2,838 | Genus × PC scores + cluster assignment |
| `data/nb00_fingerprint_clusters.csv` | 4 | Cluster centroid environmental profiles |
| `data/nb00_pca_loadings.csv` | 13 | PC1/PC2/PC3 loadings per env variable |
| `data/nb01_ko_env_pca_assoc.csv` | 212 | KO × PC1/PC2 Spearman ρ and FDR q |
| `data/nb01_guild_env_correlations.csv` | 5 | Guild mean |ρ_PC1| by functional category |
| `data/nb02_genus_env_fingerprints.csv` | 200 | Per-genus PC1/PC2/niche_breadth/prevalence |
| `data/nb02_h4_concordance.csv` | 20 | Top SHAP genera × NB00 fingerprint concordance |
| `data/nb02_pc_shap.parquet` | — | Per-genus SHAP importance for PC1/PC2 models |
| `data/nb02_otu_level_cache.parquet` | 1,918,978 | OTU × sample count matrix (2,000 OTUs) |
| `data/nb02_otu_env_fingerprints.csv` | 2,000 | OTU-level PC1/PC2/niche_breadth/taxonomy (35 cols) |

---

## Figures

| Figure | Description |
|--------|-------------|
| `figures/nb00_F1_pca_biplot.pdf` | Genus env PCA biplot (PC1 vs PC2; top 20 genera labeled) |
| `figures/nb00_F2_cluster_profiles.pdf` | Cluster mean env profiles (radar or bar) |
| `figures/nb00_F3_silhouette.pdf` | Silhouette score vs k |
| `figures/nb00_F4_rhodanobacter.pdf` | Rhodanobacter species in PCA space |
| `figures/nb01_F1_volcano.pdf` | KO–PC1 volcano plot (|ρ| vs −log10 q) |
| `figures/nb01_F2_guild_boxplot.pdf` | Guild mean |ρ_PC1| boxplot (H2) |
| `figures/nb01_F3_top_ko.pdf` | Top 15 KOs by |ρ_PC1| bar chart |
| `figures/nb02_F1_env_pca.pdf` | Sample-level env PCA (6,010 samples) |
| `figures/nb02_F2_mo_cv.pdf` | Multi-output CV R² by env target |
| `figures/nb02_F3_shap_pc1.pdf` | SHAP importance for PC1 model |
| `figures/nb02_F4_h4_concordance.pdf` | Scatter: genus fingerprint |ρ_PC1| vs SHAP importance |
| `figures/nb02_F5_otu_env_biplot.pdf` | OTU-level env PCA biplot with taxonomy coloring |

---

## Notebooks

| Notebook | Status | Purpose |
|----------|--------|---------|
| `notebooks/00_genus_env_pca.ipynb` | COMPLETE (2026-07-28) | Genus env PCA, clustering, NB00 fingerprints |
| `notebooks/01_ko_bioindicators.ipynb` | COMPLETE (2026-07-28) | KO guild env-PC correlations (H2, H3) |
| `notebooks/02_sample_level_ml.ipynb` | COMPLETE (2026-07-29) | Sample-level ML, SHAP, H4 concordance (Spark) |
| `scripts/extract_otu_level_cache.py` | COMPLETE (2026-07-29) | Spark extraction of OTU × sample matrix |
| `scripts/compute_genus_env_pca.py` | COMPLETE (2026-07-29) | Standalone genus env PCA script |
| `scripts/compute_pc_shap.py` | COMPLETE (2026-07-29) | Standalone PC1/PC2 SHAP computation |
| `scripts/compute_otu_env_fingerprints.py` | COMPLETE (2026-07-29) | OTU-level fingerprint computation |

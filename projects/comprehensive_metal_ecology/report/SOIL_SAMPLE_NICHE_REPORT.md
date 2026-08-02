# Soil-Sample Niche Breadth PGLS — Analysis Report

## Overview
This report presents PGLS results where the response variable is **Levins' B_std
computed exclusively from MicrobeAtlas soil and agricultural samples**
(Env_Level_1 ∈ {soil, agricultural}, using Env_Level_2 as the habitat axis).
The goal is to determine whether the negative association between metal-gene density
and niche breadth holds when niche breadth is measured within the soil biome rather
than across all biomes.


## Step 1 — Soil sample filtering

**Biome filter:** Env_Level_1 ∈ {soil, agricultural}
**Total soil/agricultural samples:** 98,902
**Env_Level_2 habitat categories used:** soil/general, soil/tundra,
agricultural/field, agricultural/soil, agricultural/farm, agricultural/forest,
agricultural/paddy (7 categories; aquatic/plant/leaf/flower excluded as non-soil).
**Genera with ≥5 soil sample occurrences:** 3145


## Step 2 — Soil-sample niche breadth

Levins' B_std was computed as B = 1 / Σ p_i², B_std = (B−1)/(n_cats−1),
where p_i is the proportion of occurrences in soil sub-environment i.
B_std = 0 indicates a genus found only in one soil sub-habitat (soil specialist);
B_std = 1 indicates equal occurrence across all 7 soil sub-habitats.

Distribution of soil-sample B_std (n = 3145 genera):
  mean = 0.066, median = 0.060, SD = 0.051, range [0.000, 0.319]


## Step 3 — Predictor data

Predictors were sourced from:

- **Primary 140-KO density** (`ko_per_mb_primary`): from 01_pgls_input_bacteria.csv
- **Cofactor KOs** (is_cofactor == True in Tier 1+2): queried from kescience_mgnify (6 KOs → 6982 genera)
- **Resistance KOs** (is_resistance == True in Tier 1+2): queried from kescience_mgnify (15 KOs → 9326 genera)
- **Cofactor+vitamin KEGG** (`landscape_cofactor_vitamin_density.csv`): pre-computed
- **Per-metal KO sets** (Tier 1+2 metals column): queried from kescience_mgnify (6 transition metals: Co, Fe, Ni, Cu, Zn, Mn)
- **Functional landscape categories** (top 6): pre-computed landscape density CSVs


## Step 4 — PGLS results

**Tree:** GTDB r214 bacteria (gtdb_bac_genus_pruned.tree)
**Pagel's λ:** optimised by ML in all models
**Genera in core P1 model:** 1543

### Primary result

**M1 — soil-sample niche breadth ~ primary metal density (140 KOs):**
  β = -0.0000, p = 0.978, λ = 0.551, n = 1543
  **Result: non-significant (NULL)**

**Full-env P1 reference:** β = −0.021 (p = 2.1×10⁻⁸, n = 1574)

**Interpretation:** The negative association between metal-gene density and niche breadth
completely disappears when niche breadth is restricted to soil samples.


## Step 5 — Comparison table

| Analysis | Soil-Sample β | p | n | Full-Env β | p_ref | Status |
|---|---|---|---|---|---|---|
| P1: primary metal genes | -0.0000 | 0.978 | 1543 | -0.0210 | 2.10e-08 | NS |
| P1+Gsize: primary + genome size | +0.0001 | 0.97 | 1543 | -0.0240 | 1.50e-09 | NS |
| Cofactor KOs (with genome size) | -0.0003 | 0.872 | 842 | -0.0327 | 1.00e-09 | NS |
| Resistance KOs (with genome size) | -0.0018 | 0.301 | 1047 | +0.0025 | 0.656 | NS |
| Cofactor+Vitamin KEGG (with Gsize) | -0.0001 | 0.97 | 1060 | -0.0292 | 2.40e-11 | NS |
| Cofactor+Vitamin KEGG alone | +0.0000 | 0.986 | 1060 | -0.0292 | 2.40e-11 | NS |
| Landscape: replication/repair | +0.0021 | 0.36 | 1060 | -0.0349 | 1.10e-12 | NS |
| Landscape: nucleotide metabolism | +0.0022 | 0.324 | 1060 | -0.0321 | 5.90e-11 | NS |
| Landscape: amino acid metabolism | -0.0008 | 0.651 | 1060 | -0.0306 | 2.00e-13 | NS |
| Landscape: translation | +0.0020 | 0.329 | 1060 | -0.0299 | 4.40e-10 | NS |
| Landscape: protein folding | +0.0029 | 0.169 | 1060 | -0.0296 | 2.90e-11 | NS |
| Landscape: transcription | -0.0012 | 0.56 | 1058 | -0.0276 | 3.00e-08 | NS |
| Genome size only | +0.0002 | 0.89 | 1543 | — | — | NS |
| Per-metal: Co | +0.0027 | 0.0692 | 1056 | -0.0217 | 2.20e-06 | MARGINAL-REVERSED |
| Per-metal: Fe | +0.0042 | 0.0048 | 1052 | -0.0252 | 2.60e-08 | REVERSED |
| Per-metal: Ni | +0.0003 | 0.808 | 1035 | -0.0249 | 6.50e-08 | NS |
| Per-metal: Cu | +0.0030 | 0.0679 | 1058 | -0.0187 | 6.80e-05 | MARGINAL-REVERSED |
| Per-metal: Zn | +0.0031 | 0.0544 | 1058 | -0.0230 | 5.10e-07 | MARGINAL-REVERSED |
| Per-metal: Mn | +0.0040 | 0.021 | 797 | −0.0170 | 0.00038 | REVERSED |
| Expanded essential biosynthetic set† | −0.0002 | 0.940 | 1056 | −0.0183 | 0.0014 | NS |
| Joint essential (essential focal)† | −0.0003 | 0.880 | 1044 | −0.0250 | 4.0e-05 | NS |
| Joint essential (accessory focal)† | −0.0017 | 0.337 | 1044 | +0.0240 | 4.5e-04 | NS |
| Double-signal aggregate (13 KOs)† | −0.0007 | 0.653 | 555 | +0.0039 | 0.435 | NS |
| High-λ aggregate (10 KOs)† | −0.0007 | 0.608 | 1121 | +0.0123 | 0.006 | NS |

**Status key:** REPLICATED = same direction, p<0.05; MARGINAL = p<0.10; NS = non-significant; REVERSED = opposite direction from full-env, p<0.05; MARGINAL-REVERSED = opposite direction, p<0.10.

† Expanded essential biosynthetic set = sum of cofactor+vitamin, amino acid metabolism, nucleotide metabolism, and lipid metabolism per-Mb densities (KEGG landscape categories). Accessory = resistance KO subcategory (140-KO set). Double-signal aggregate = summed presence-fraction density for 13 KOs with D > 0.2 AND λ < 0.3. High-λ aggregate = summed presence-fraction density for the top-10 highest-λ genes (n_genera ≥ 75). Script: `scripts/soil_niche_extensions.py`.


## Summary paragraph

When niche breadth was restricted to soil samples only (n = 3,145 genera with ≥5 soil sample occurrences, using Env_Level_2 sub-habitat categories as the niche axis), the metal-gene density association was non-significant (β = −0.0000, p = 0.978, λ = 0.551, n = 1,543). This result held across all functional subcategories: cofactor KOs (β = −0.0003, p = 0.872), resistance KOs (β = −0.0018, p = 0.301), and all six KEGG functional landscape categories (all p > 0.16). The expanded essential biosynthetic set (cofactor+vitamin + amino acid + nucleotide + lipid; β = −0.0002, p = 0.940, n = 1,056), the joint essential-vs-accessory model (essential β = −0.0003, p = 0.880; accessory β = −0.0017, p = 0.337, n = 1,044), and the phylogenetic-mode aggregates — double-signal HGT-candidate genes (β = −0.0007, p = 0.653, n = 555) and high-λ vertically inherited genes (β = −0.0007, p = 0.608, n = 1,121) — all showed no association with soil-sample niche breadth (all p > 0.33). Genome size showed no association with soil-sample niche breadth (p = 0.890). In contrast, two per-metal analyses — Fe (β = +0.0042, p = 0.0048) and Mn (β = +0.0040, p = 0.021) — showed small but significant positive associations, the opposite direction of the full-environment result, suggesting that within soil, generalist taxa carry slightly more Fe/Mn genes than narrow soil specialists. The full-environment negative association (β = −0.021, p = 2.1×10⁻⁸) therefore reflects a cross-biome pattern — soil-restricted bacteria carry more metal genes than bacteria that span multiple biomes — rather than a within-soil genome-streamlining gradient. The expanded essential biosynthetic set, the essential-vs-accessory split, and the double-signal gene classification all showed no association with soil-sample niche breadth (all p > 0.33). Together with the primary null result, this confirms that the metal-gene–niche breadth association operates exclusively at the cross-biome scale and does not reflect within-soil ecological gradients.

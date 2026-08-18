# Environmental Prediction by Functional Subset

## Overview

Phylogenetically corrected regression (Pagel's λ PGLS) testing whether metal-gene functional subset densities at genus level predict environmental metal and geochemical conditions. Model: `env_response_z ~ subset_density_z + genome_size_z + intercept`. Tree: `gtdb_bac_genus_pruned.tree` (GTDB genus-level).

---

## Step 1: Subset PGLS (12 × 15 = 180 models)

Total models: 180 | Significant (BH q<0.05): **4/180**

### Functional subsets ranked by mean |β|

| subset             |   mean_abs_beta |   n_sig_env |
|:-------------------|----------------:|------------:|
| Nonmetal_cofactors |       0.0512022 |           1 |
| Core_metabolism    |       0.0494763 |           1 |
| Heme               |       0.0408667 |           0 |
| Metal_dep_metab    |       0.0400793 |           0 |
| Resistance_Tier1   |       0.0377324 |           1 |
| Expanded_KEGG      |       0.0306804 |           0 |
| Primary_140KO      |       0.0288099 |           1 |
| Siroheme           |       0.0287464 |           0 |
| Cobalamin          |       0.0277283 |           0 |
| FeS_assembly       |       0.0258495 |           0 |
| Molybdopterin      |       0.0238234 |           0 |
| Cofactor_Tier2     |       0.0232074 |           0 |

### Significant associations by env response

| env_response   |   n_sig_subsets |
|:---------------|----------------:|
| GEOROC_Co      |               2 |
| GEOROC_Pb      |               1 |
| Soil_pH        |               1 |

Heatmap: `figures/functional_subset_env_heatmap.pdf`

---

## Step 2: Per-KO PGLS

Top 3 env responses (ranked by mean |β| × n_sig): **['GEOROC_Co', 'GEOROC_Pb', 'Soil_pH']**

KOs tested (≥20 genera present): **276**
Significant KO × env pairs (BH q<0.05): **0/828**

**GEOROC_Co** (top 10 by BH q):

| ko     | primary_category           |   n_genera_present |    n |       beta |        SE |        p |        q |   lambda_est |
|:-------|:---------------------------|-------------------:|-----:|-----------:|----------:|---------:|---------:|-------------:|
| K00013 | Metal-dependent Metabolism |               1351 | 1214 |  0.017491  | 0.0267225 | 0.512886 | 0.930087 |     0.130488 |
| K00031 | Metal-dependent Metabolism |               1236 | 1214 |  0.0255236 | 0.0267193 | 0.339643 | 0.930087 |     0.130775 |
| K00108 | Metal-dependent Metabolism |                438 | 1214 |  0.0322215 | 0.0267422 | 0.228479 | 0.930087 |     0.132352 |
| K00169 | Unknown                    |                235 | 1214 | -0.0167505 | 0.0257344 | 0.515237 | 0.930087 |     0.125774 |
| K00174 | Unknown                    |                682 | 1214 | -0.0153232 | 0.0285062 | 0.590994 | 0.930087 |     0.128126 |
| K00177 | Unknown                    |                298 | 1214 | -0.033527  | 0.0308607 | 0.277519 | 0.930087 |     0.124832 |
| K00209 | Unknown                    |                250 | 1214 |  0.0246735 | 0.0248201 | 0.320376 | 0.930087 |     0.133259 |
| K00228 | Unknown                    |                745 | 1214 |  0.0280231 | 0.0280272 | 0.317581 | 0.930087 |     0.129769 |
| K00390 | Unknown                    |               1008 | 1214 |  0.0137448 | 0.0264156 | 0.602929 | 0.930087 |     0.128941 |
| K00425 | Unknown                    |               1139 | 1214 |  0.0148612 | 0.027303  | 0.586329 | 0.930087 |     0.130172 |

**GEOROC_Pb** (top 10 by BH q):

| ko     | primary_category           |   n_genera_present |    n |        beta |        SE |        p |        q |   lambda_est |
|:-------|:---------------------------|-------------------:|-----:|------------:|----------:|---------:|---------:|-------------:|
| K00013 | Metal-dependent Metabolism |               1351 | 1220 |  0.00283815 | 0.026132  | 0.913531 | 0.984632 |     0.221222 |
| K00031 | Metal-dependent Metabolism |               1236 | 1220 |  0.0154468  | 0.0261357 | 0.554616 | 0.984632 |     0.221552 |
| K00108 | Metal-dependent Metabolism |                438 | 1220 |  0.007753   | 0.0261593 | 0.766994 | 0.984632 |     0.221273 |
| K00169 | Unknown                    |                235 | 1220 |  0.0235479  | 0.0253091 | 0.352342 | 0.984632 |     0.224552 |
| K00177 | Unknown                    |                298 | 1220 | -0.015614   | 0.0304658 | 0.608389 | 0.984632 |     0.216677 |
| K00209 | Unknown                    |                250 | 1220 |  0.0251072  | 0.0242376 | 0.300464 | 0.984632 |     0.220894 |
| K00228 | Unknown                    |                745 | 1220 |  0.0396479  | 0.0273973 | 0.148113 | 0.984632 |     0.215572 |
| K00230 | Unknown                    |                398 | 1220 |  0.0189319  | 0.0248956 | 0.447132 | 0.984632 |     0.224508 |
| K00244 | Metal-dependent Metabolism |                151 | 1220 |  0.0192588  | 0.0298122 | 0.518399 | 0.984632 |     0.225371 |
| K00246 | Metal-dependent Metabolism |                176 | 1220 |  0.013117   | 0.0253817 | 0.605398 | 0.984632 |     0.223138 |

**Soil_pH** (top 10 by BH q):

| ko     | primary_category           |   n_genera_present |    n |       beta |        SE |          p |        q |   lambda_est |
|:-------|:---------------------------|-------------------:|-----:|-----------:|----------:|-----------:|---------:|-------------:|
| K00013 | Metal-dependent Metabolism |               1351 | 1222 | -0.0662298 | 0.0258751 | 0.0105992  | 0.297415 |     0.26173  |
| K01012 | Transport/Homeostasis      |               1108 | 1222 | -0.0605376 | 0.0253595 | 0.0171303  | 0.297415 |     0.266678 |
| K03101 | Unknown                    |               1549 | 1222 | -0.0688507 | 0.0261012 | 0.00844978 | 0.297415 |     0.258112 |
| K03501 | Unknown                    |               1518 | 1222 | -0.0681238 | 0.0260975 | 0.00915571 | 0.297415 |     0.255725 |
| K03655 | Unknown                    |               1482 | 1222 | -0.069297  | 0.0261981 | 0.00827135 | 0.297415 |     0.257569 |
| K03701 | Unknown                    |               1540 | 1222 | -0.0625877 | 0.0262446 | 0.0172414  | 0.297415 |     0.256822 |
| K05540 | Unknown                    |               1418 | 1222 | -0.0638944 | 0.0260291 | 0.0142381  | 0.297415 |     0.259143 |
| K06168 | Unknown                    |               1451 | 1222 | -0.0705272 | 0.0263563 | 0.00755239 | 0.297415 |     0.260825 |
| K06941 | Unknown                    |               1444 | 1222 | -0.0674218 | 0.0262199 | 0.0102465  | 0.297415 |     0.257712 |
| K07084 | Unknown                    |                214 | 1222 | -0.0700083 | 0.0252898 | 0.00572127 | 0.297415 |     0.26693  |

---

## Step 3: Abundance-Weighted PGLS

Weight: log₁₀(n_samples + 1), normalized. WLS via √w pre-multiplication on y, X.

- **Spearman ρ**: 0.925 (p = 1.33e-76)
- **Mean |Δβ|**: 0.0138

ρ > 0.9 and mean |Δβ| < 0.05 would indicate that genus-level abundance weighting does not change conclusions.

---

## Step 4: Multivariate PGLS (env_PC1 ~ all subsets)

env_PC1 = PC1 of PCA on GEOROC metals (Cu/Ni/Zn/Co/Cr/Pb) + soil pH + temperature.

n = 841, λ = 0.193, R² = 0.011

| predictor                 |       beta |        SE |    t_stat |        p |        q |
|:--------------------------|-----------:|----------:|----------:|---------:|---------:|
| ko_per_mb_primary_z       | -0.0719545 | 0.0575483 | -1.25033  | 0.211532 | 0.461235 |
| ko_per_mb_tier1_z         |  0.0110475 | 0.0504608 |  0.218933 | 0.826757 | 0.885206 |
| ko_per_mb_tier2_z         | -0.0288559 | 0.15606   | -0.184903 | 0.853351 | 0.885206 |
| expanded_z                |  1.04697   | 0.693144  |  1.51047  | 0.131307 | 0.461235 |
| heme_z                    | -0.307588  | 0.269593  | -1.14093  | 0.254229 | 0.461235 |
| cobalamin_z               | -0.628587  | 0.42277   | -1.48683  | 0.137441 | 0.461235 |
| molybdopterin_z           | -0.247806  | 0.196946  | -1.25825  | 0.208658 | 0.461235 |
| siroheme_z                | -0.012625  | 0.0874198 | -0.144418 | 0.885206 | 0.885206 |
| fes_assembly_z            | -0.183004  | 0.170742  | -1.07181  | 0.284117 | 0.461235 |
| core_metabolism_z         |  0.0205695 | 0.0839582 |  0.244997 | 0.80652  | 0.885206 |
| metal_dep_z               | -0.0593194 | 0.0595299 | -0.996464 | 0.319316 | 0.461235 |
| cofactor_vitamin_per_mb_z | -0.107208  | 0.0756228 | -1.41767  | 0.156665 | 0.461235 |
| genome_size_mb_z          | -0.0666733 | 0.0634275 | -1.05117  | 0.293486 | 0.461235 |

---

## SI Paragraph

**Environmental prediction by functional gene subset.** To identify which metal-gene functional categories are most strongly associated with environmental metal and geochemical gradients, we ran Pagel's λ PGLS regressing 15 environmental variables (GEOROC bedrock metals Cu, Ni, Zn, Co, Cr, Pb; CSU PF1 mobile fractions As, Cd, Cr, Cu, Hg, Pb; soil pH; mean annual temperature; and a multi-metal environment PC1) against each of 12 functional gene-density subsets at genus level, controlling for genome size (180 models total, BH FDR correction within each environmental variable). 4 of 180 models were significant at q < 0.05. The subsets most strongly associated with environmental metal gradients were Nonmetal cofactors (mean |β| = 0.0512, 1 env responses significant) and Core metabolism (mean |β| = 0.0495, 1 significant). Abundance-weighted PGLS (genera weighted by log₁₀(n_MicrobeAtlas_samples + 1)) yielded nearly identical estimates (Spearman ρ = 0.925, p = 1.33e-76, mean |Δβ| = 0.0138), indicating that the pattern is not driven by highly-sampled genera. Per-KO PGLS for all 276 tracked KOs vs. the top three environmental predictors is reported in Supplementary Data File S_env_ko.

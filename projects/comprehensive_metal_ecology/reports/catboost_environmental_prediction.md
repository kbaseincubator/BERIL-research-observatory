# CatBoost Environmental Prediction Analysis

## Overview

CatBoost regressors with Leave-One-Phylum-Out (LOPO) cross-validation test whether metal-gene functional subset densities and individual KO densities at genus level predict environmental conditions. Each fold trains on all phyla except one and evaluates on the held-out phylum (Spearman ρ). 11 phyla qualify (≥10 genera each). This complements the Pagel's λ PGLS framework (Finding 18) by allowing nonlinear relationships and providing model-agnostic SHAP feature importance.

---

## Step 1a: All-KO CatBoost LOPO CV

| env_response   |    avg_rho |   n_folds |
|:---------------|-----------:|----------:|
| GEOROC_Cu      |  0.102226  |        11 |
| GEOROC_Ni      | -0.138977  |        11 |
| GEOROC_Zn      |  0.133775  |        11 |
| GEOROC_Co      |  0.163275  |        11 |
| GEOROC_Cr      |  0.154903  |        11 |
| GEOROC_Pb      |  0.0897625 |        11 |
| CSU_As         |  0.173709  |        11 |
| CSU_Cd         |  0.0591434 |        11 |
| CSU_Cr         |  0.0237639 |        11 |
| CSU_Cu         |  0.0296618 |        11 |
| CSU_Hg         | -0.0564271 |        11 |
| CSU_Pb         |  0.131856  |        11 |
| Soil_pH        |  0.213126  |        11 |
| Temperature    |  0.0139116 |        11 |
| Env_PC1        |  0.0279455 |        11 |

---

## Step 1b: SHAP Feature Importance (top-10 KOs)

**GEOROC_Cu:**
|   rank | ko     | primary_category           |   mean_abs_shap | in_pgls_top10   |
|-------:|:-------|:---------------------------|----------------:|:----------------|
|      1 | K11741 | Resistance/Detoxification  |       0.054758  | False           |
|      2 | K04564 | Metal-dependent Metabolism |       0.0408286 | False           |
|      3 | K07787 | Resistance/Detoxification  |       0.0296226 | False           |
|      4 | K02007 | Transport/Homeostasis      |       0.0256044 | False           |
|      5 | K01935 | Transport/Homeostasis      |       0.0217305 | False           |
|      6 | K17686 | Resistance/Detoxification  |       0.0210784 | False           |
|      7 | K03635 | Cofactor Biosynthesis      |       0.0201412 | False           |
|      8 | K18989 | Resistance/Detoxification  |       0.0194238 | False           |
|      9 | K07552 | Resistance/Detoxification  |       0.0189576 | False           |
|     10 | K09771 | Resistance/Detoxification  |       0.0174492 | False           |

**GEOROC_Zn:**
|   rank | ko     | primary_category           |   mean_abs_shap | in_pgls_top10   |
|-------:|:-------|:---------------------------|----------------:|:----------------|
|      1 | K07263 | Transport/Homeostasis      |       0.0471775 | False           |
|      2 | K21600 | Sensing/Regulation         |       0.0386178 | False           |
|      3 | K07787 | Resistance/Detoxification  |       0.0304176 | False           |
|      4 | K01599 | Transport/Homeostasis      |       0.0258622 | False           |
|      5 | K00031 | Metal-dependent Metabolism |       0.0227515 | False           |
|      6 | K07240 | Resistance/Detoxification  |       0.021518  | False           |
|      7 | K04564 | Metal-dependent Metabolism |       0.0212714 | False           |
|      8 | K18989 | Resistance/Detoxification  |       0.0205213 | False           |
|      9 | K03635 | Cofactor Biosynthesis      |       0.0197694 | False           |
|     10 | K01772 | Cofactor Biosynthesis      |       0.0188631 | False           |

**GEOROC_Co:**
|   rank | ko     | primary_category           |   mean_abs_shap | in_pgls_top10   |
|-------:|:-------|:---------------------------|----------------:|:----------------|
|      1 | K03741 | Resistance/Detoxification  |       0.0675787 | False           |
|      2 | K07787 | Resistance/Detoxification  |       0.0284405 | False           |
|      3 | K08151 | Resistance/Detoxification  |       0.0271793 | False           |
|      4 | K19575 | Sensing/Regulation         |       0.0264024 | False           |
|      5 | K03297 | Resistance/Detoxification  |       0.0263276 | False           |
|      6 | K23242 | Resistance/Detoxification  |       0.0236531 | False           |
|      7 | K07796 | Resistance/Detoxification  |       0.0216934 | False           |
|      8 | K03325 | Resistance/Detoxification  |       0.0198998 | False           |
|      9 | K00013 | Metal-dependent Metabolism |       0.0194604 | False           |
|     10 | K00031 | Metal-dependent Metabolism |       0.0176129 | False           |

**GEOROC_Cr:**
|   rank | ko     | primary_category           |   mean_abs_shap | in_pgls_top10   |
|-------:|:-------|:---------------------------|----------------:|:----------------|
|      1 | K02047 | Transport/Homeostasis      |       0.0769257 | False           |
|      2 | K01551 | Resistance/Detoxification  |       0.0519892 | False           |
|      3 | K18990 | Resistance/Detoxification  |       0.0498994 | False           |
|      4 | K07240 | Resistance/Detoxification  |       0.0346052 | False           |
|      5 | K00537 | Resistance/Detoxification  |       0.034207  | False           |
|      6 | K08225 | Transport/Homeostasis      |       0.0323335 | False           |
|      7 | K07787 | Resistance/Detoxification  |       0.0320263 | False           |
|      8 | K03741 | Resistance/Detoxification  |       0.0295538 | False           |
|      9 | K01012 | Transport/Homeostasis      |       0.0273149 | False           |
|     10 | K00108 | Metal-dependent Metabolism |       0.0244658 | False           |

**GEOROC_Pb:**
|   rank | ko     | primary_category           |   mean_abs_shap | in_pgls_top10   |
|-------:|:-------|:---------------------------|----------------:|:----------------|
|      1 | K09771 | Resistance/Detoxification  |       0.0666119 | False           |
|      2 | K03741 | Resistance/Detoxification  |       0.0593277 | False           |
|      3 | K22552 | Metal-dependent Metabolism |       0.0329141 | False           |
|      4 | K00537 | Resistance/Detoxification  |       0.0322648 | False           |
|      5 | K06201 | Transport/Homeostasis      |       0.0308524 | False           |
|      6 | K02012 | Transport/Homeostasis      |       0.0302998 | False           |
|      7 | K07240 | Resistance/Detoxification  |       0.0293959 | False           |
|      8 | K07787 | Resistance/Detoxification  |       0.0283609 | True            |
|      9 | K07796 | Resistance/Detoxification  |       0.0280743 | True            |
|     10 | K18989 | Resistance/Detoxification  |       0.0250921 | False           |

**CSU_As:**
|   rank | ko     | primary_category           |   mean_abs_shap | in_pgls_top10   |
|-------:|:-------|:---------------------------|----------------:|:----------------|
|      1 | K03543 | Resistance/Detoxification  |       0.0350006 | False           |
|      2 | K22227 | Transport/Homeostasis      |       0.0320028 | False           |
|      3 | K11811 | Resistance/Detoxification  |       0.0282646 | False           |
|      4 | K19784 | Resistance/Detoxification  |       0.0254737 | False           |
|      5 | K03446 | Resistance/Detoxification  |       0.0245925 | False           |
|      6 | K06042 | Transport/Homeostasis      |       0.0228991 | False           |
|      7 | K07787 | Resistance/Detoxification  |       0.0204158 | False           |
|      8 | K11741 | Resistance/Detoxification  |       0.0197379 | False           |
|      9 | K17686 | Resistance/Detoxification  |       0.018717  | False           |
|     10 | K17225 | Metal-dependent Metabolism |       0.0158745 | False           |

**CSU_Cd:**
|   rank | ko     | primary_category           |   mean_abs_shap | in_pgls_top10   |
|-------:|:-------|:---------------------------|----------------:|:----------------|
|      1 | K02007 | Transport/Homeostasis      |       0.0545682 | False           |
|      2 | K00768 | Transport/Homeostasis      |       0.0390293 | False           |
|      3 | K08641 | Transport/Homeostasis      |       0.0291482 | False           |
|      4 | K00013 | Metal-dependent Metabolism |       0.0274449 | False           |
|      5 | K21600 | Sensing/Regulation         |       0.0265633 | False           |
|      6 | K16090 | Transport/Homeostasis      |       0.0243884 | False           |
|      7 | K13283 | Resistance/Detoxification  |       0.0185202 | False           |
|      8 | K08161 | Resistance/Detoxification  |       0.0170649 | False           |
|      9 | K17226 | Sensing/Regulation         |       0.0169778 | False           |
|     10 | K02009 | Transport/Homeostasis      |       0.0166906 | False           |

**CSU_Cr:**
|   rank | ko     | primary_category          |   mean_abs_shap | in_pgls_top10   |
|-------:|:-------|:--------------------------|----------------:|:----------------|
|      1 | K18990 | Resistance/Detoxification |       0.0513327 | False           |
|      2 | K07787 | Resistance/Detoxification |       0.0476216 | False           |
|      3 | K18989 | Resistance/Detoxification |       0.0469223 | False           |
|      4 | K03446 | Resistance/Detoxification |       0.0392409 | False           |
|      5 | K03543 | Resistance/Detoxification |       0.0353648 | False           |
|      6 | K11811 | Resistance/Detoxification |       0.0338562 | False           |
|      7 | K07240 | Resistance/Detoxification |       0.0324841 | False           |
|      8 | K00537 | Resistance/Detoxification |       0.0276992 | False           |
|      9 | K03893 | Resistance/Detoxification |       0.0264445 | False           |
|     10 | K07552 | Resistance/Detoxification |       0.023829  | False           |

**CSU_Cu:**
|   rank | ko     | primary_category           |   mean_abs_shap | in_pgls_top10   |
|-------:|:-------|:---------------------------|----------------:|:----------------|
|      1 | K03523 | Transport/Homeostasis      |       0.0409519 | False           |
|      2 | K03446 | Resistance/Detoxification  |       0.0389163 | False           |
|      3 | K03543 | Resistance/Detoxification  |       0.0387901 | False           |
|      4 | K06042 | Transport/Homeostasis      |       0.0379118 | False           |
|      5 | K18990 | Resistance/Detoxification  |       0.0303067 | False           |
|      6 | K11811 | Resistance/Detoxification  |       0.0242686 | False           |
|      7 | K18989 | Resistance/Detoxification  |       0.0209575 | False           |
|      8 | K17225 | Metal-dependent Metabolism |       0.0197012 | False           |
|      9 | K07796 | Resistance/Detoxification  |       0.0191732 | False           |
|     10 | K07787 | Resistance/Detoxification  |       0.0187136 | False           |

**CSU_Pb:**
|   rank | ko     | primary_category          |   mean_abs_shap | in_pgls_top10   |
|-------:|:-------|:--------------------------|----------------:|:----------------|
|      1 | K01772 | Cofactor Biosynthesis     |       0.041823  | False           |
|      2 | K00537 | Resistance/Detoxification |       0.0345985 | False           |
|      3 | K00768 | Transport/Homeostasis     |       0.0298372 | False           |
|      4 | K09771 | Resistance/Detoxification |       0.0291934 | False           |
|      5 | K05802 | Transport/Homeostasis     |       0.0281009 | False           |
|      6 | K01935 | Transport/Homeostasis     |       0.0252069 | False           |
|      7 | K06042 | Transport/Homeostasis     |       0.0234794 | False           |
|      8 | K08151 | Resistance/Detoxification |       0.0233831 | False           |
|      9 | K07243 | Transport/Homeostasis     |       0.0209392 | False           |
|     10 | K07665 | Resistance/Detoxification |       0.0181678 | False           |

**Soil_pH:**
|   rank | ko     | primary_category          |   mean_abs_shap | in_pgls_top10   |
|-------:|:-------|:--------------------------|----------------:|:----------------|
|      1 | K18989 | Resistance/Detoxification |       0.0763848 | False           |
|      2 | K00537 | Resistance/Detoxification |       0.0532926 | False           |
|      3 | K19575 | Sensing/Regulation        |       0.0322801 | False           |
|      4 | K18990 | Resistance/Detoxification |       0.0302872 | False           |
|      5 | K11708 | Transport/Homeostasis     |       0.0278047 | False           |
|      6 | K00768 | Transport/Homeostasis     |       0.027573  | False           |
|      7 | K15726 | Resistance/Detoxification |       0.0274692 | False           |
|      8 | K03446 | Resistance/Detoxification |       0.0274497 | False           |
|      9 | K08641 | Transport/Homeostasis     |       0.0266654 | False           |
|     10 | K23242 | Resistance/Detoxification |       0.0251665 | True            |

**Temperature:**
|   rank | ko     | primary_category          |   mean_abs_shap | in_pgls_top10   |
|-------:|:-------|:--------------------------|----------------:|:----------------|
|      1 | K02011 | Transport/Homeostasis     |       0.0539821 | False           |
|      2 | K16090 | Transport/Homeostasis     |       0.0400324 | False           |
|      3 | K18367 | Sensing/Regulation        |       0.0246398 | False           |
|      4 | K08225 | Transport/Homeostasis     |       0.0238384 | False           |
|      5 | K13283 | Resistance/Detoxification |       0.0222026 | False           |
|      6 | K03635 | Cofactor Biosynthesis     |       0.0203757 | False           |
|      7 | K07796 | Resistance/Detoxification |       0.0191553 | False           |
|      8 | K07233 | Resistance/Detoxification |       0.0180116 | False           |
|      9 | K01599 | Transport/Homeostasis     |       0.0174806 | False           |
|     10 | K02188 | Transport/Homeostasis     |       0.0141952 | False           |

**Env_PC1:**
|   rank | ko     | primary_category           |   mean_abs_shap | in_pgls_top10   |
|-------:|:-------|:---------------------------|----------------:|:----------------|
|      1 | K01551 | Resistance/Detoxification  |       0.0567009 | False           |
|      2 | K03297 | Resistance/Detoxification  |       0.0535917 | False           |
|      3 | K03741 | Resistance/Detoxification  |       0.0386779 | False           |
|      4 | K02047 | Transport/Homeostasis      |       0.0329914 | False           |
|      5 | K22041 | Sensing/Regulation         |       0.0311163 | False           |
|      6 | K00031 | Metal-dependent Metabolism |       0.0288536 | False           |
|      7 | K08151 | Resistance/Detoxification  |       0.0267151 | False           |
|      8 | K17226 | Sensing/Regulation         |       0.0222393 | False           |
|      9 | K04564 | Metal-dependent Metabolism |       0.0209508 | False           |
|     10 | K23242 | Resistance/Detoxification  |       0.0200152 | False           |

---

## Step 1c: Single-KO CatBoost — Top KOs by Mean Avg ρ

| ko     | primary_category           |   avg_rho |
|:-------|:---------------------------|----------:|
| K19575 | Sensing/Regulation         | 0.0771596 |
| K22552 | Metal-dependent Metabolism | 0.0675166 |
| K00244 | Metal-dependent Metabolism | 0.0656541 |
| K09883 | Transport/Homeostasis      | 0.064616  |
| K11604 | Transport/Homeostasis      | 0.0612767 |
| K03543 | Resistance/Detoxification  | 0.0605562 |
| K07796 | Resistance/Detoxification  | 0.0591982 |
| K07233 | Resistance/Detoxification  | 0.0582429 |
| K07665 | Resistance/Detoxification  | 0.0574301 |
| K15585 | Transport/Homeostasis      | 0.05722   |
| K05802 | Transport/Homeostasis      | 0.0568608 |
| K09823 | Transport/Homeostasis      | 0.0559621 |
| K02302 | Metal-dependent Metabolism | 0.0558204 |
| K15974 | Sensing/Regulation         | 0.055803  |
| K18989 | Resistance/Detoxification  | 0.0556551 |
| K14166 | Transport/Homeostasis      | 0.0551261 |
| K04080 | Transport/Homeostasis      | 0.055075  |
| K11811 | Resistance/Detoxification  | 0.0542959 |
| K18990 | Resistance/Detoxification  | 0.0541243 |
| K02069 | Transport/Homeostasis      | 0.0540328 |

---

## Step 1d: Within-Subset SHAP Decomposition

**Resistance** — top KOs by mean |SHAP|:
| ko               | primary_category          |   mean_abs_shap |
|:-----------------|:--------------------------|----------------:|
| K07787           | Resistance/Detoxification |       0.0329717 |
| K23242           | Resistance/Detoxification |       0.0295616 |
| genome_size_mb_z | genome_size               |       0.029014  |
| K00537           | Resistance/Detoxification |       0.0278741 |
| K07240           | Resistance/Detoxification |       0.0263202 |

**Transport** — top KOs by mean |SHAP|:
| ko               | primary_category      |   mean_abs_shap |
|:-----------------|:----------------------|----------------:|
| genome_size_mb_z | genome_size           |       0.0300363 |
| K03523           | Transport/Homeostasis |       0.0292259 |
| K02047           | Transport/Homeostasis |       0.0270382 |
| K01599           | Transport/Homeostasis |       0.0254641 |
| K07263           | Transport/Homeostasis |       0.0248338 |

**Cofactor** — top KOs by mean |SHAP|:
| ko               | primary_category      |   mean_abs_shap |
|:-----------------|:----------------------|----------------:|
| genome_size_mb_z | genome_size           |       0.0689108 |
| K03635           | Cofactor Biosynthesis |       0.0647607 |
| K01772           | Cofactor Biosynthesis |       0.0577367 |
| K02225           | Cofactor Biosynthesis |       0.032824  |
| K22225           | Cofactor Biosynthesis |       0.026038  |

**Metal_dep** — top KOs by mean |SHAP|:
| ko               | primary_category           |   mean_abs_shap |
|:-----------------|:---------------------------|----------------:|
| genome_size_mb_z | genome_size                |       0.0505114 |
| K04564           | Metal-dependent Metabolism |       0.0435838 |
| K00031           | Metal-dependent Metabolism |       0.0392805 |
| K00013           | Metal-dependent Metabolism |       0.0368856 |
| K22552           | Metal-dependent Metabolism |       0.0317711 |

---

## Step 2: Functional Subset CatBoost LOPO + SHAP

| env_response   |     avg_rho |   n_folds |
|:---------------|------------:|----------:|
| GEOROC_Cu      | -0.0328602  |         7 |
| GEOROC_Ni      |  0.0936409  |         7 |
| GEOROC_Zn      |  0.0590576  |         7 |
| GEOROC_Co      |  0.0213145  |         7 |
| GEOROC_Cr      |  0.0237807  |         7 |
| GEOROC_Pb      |  0.186232   |         7 |
| CSU_As         |  0.00561622 |         7 |
| CSU_Cd         |  0.191417   |         7 |
| CSU_Cr         |  0.0130998  |         7 |
| CSU_Cu         | -0.134579   |         7 |
| CSU_Hg         |  0.0465141  |         7 |
| CSU_Pb         |  0.0195857  |         7 |
| Soil_pH        |  0.12063    |         7 |
| Temperature    |  0.00235641 |         7 |
| Env_PC1        | -0.00478935 |         7 |

Heatmap: `figures/catboost_shap_heatmap.pdf`

---

## Step 3: Abundance-Weighted vs Unweighted SHAP Rankings

| env_response   |   shap_rank_rho |
|:---------------|----------------:|
| GEOROC_Cu      |        0.879121 |
| GEOROC_Ni      |        0.851648 |
| GEOROC_Zn      |        0.78022  |
| GEOROC_Co      |        0.758242 |
| GEOROC_Cr      |        0.89011  |
| GEOROC_Pb      |        0.895604 |
| CSU_As         |        0.862637 |
| CSU_Cd         |        0.972527 |
| CSU_Cr         |        0.950549 |
| CSU_Cu         |        0.950549 |
| CSU_Hg         |        0.93956  |
| CSU_Pb         |        0.813187 |
| Soil_pH        |        0.912088 |
| Temperature    |        0.835165 |
| Env_PC1        |        0.862637 |

Mean Spearman ρ (weighted vs unweighted SHAP rankings): **0.877**

---

## Step 4: Reverse Classifier (Env → KO Presence/Absence)

| ko     | primary_category           |   avg_auc |   std_auc |   n_folds |
|:-------|:---------------------------|----------:|----------:|----------:|
| K11741 | Resistance/Detoxification  |  0.654116 | 0.172715  |         9 |
| K04564 | Metal-dependent Metabolism |  0.65762  | 0.293582  |         8 |
| K07787 | Resistance/Detoxification  |  0.640607 | 0.0998478 |         7 |
| K02007 | Transport/Homeostasis      |  0.504548 | 0.141081  |         8 |
| K01935 | Transport/Homeostasis      |  0.520359 | 0.214542  |         9 |
| K19575 | Sensing/Regulation         |  0.685631 | 0.318198  |         7 |
| K22552 | Metal-dependent Metabolism |  0.625442 | 0.141959  |         7 |
| K00244 | Metal-dependent Metabolism |  0.681215 | 0.146853  |         3 |
| K09883 | Transport/Homeostasis      |  0.429676 | 0.256073  |         4 |
| K11604 | Transport/Homeostasis      |  0.563815 | 0.225557  |         4 |

---

## Synthesis

- **Step 1a (all-KO model)**: 13/15 responses have avg ρ > 0 across LOPO folds.
- **Step 2 (subset model)**: 12/15 responses have avg ρ > 0. Best: CSU_Cd.
- **Step 3 (weighted)**: Mean Spearman ρ between weighted and unweighted SHAP rankings = 0.877.
- **Step 4 (reverse)**: Best avg AUC across KOs = 0.686.

### CatBoost vs PGLS comparison

PGLS multivariate (all 12 subsets → env_PC1): R² = 0.011. CatBoost avg ρ² provides an analogous nonlinear variance-explained estimate. If CatBoost ρ² ≈ PGLS R², the relationship is largely linear; if substantially higher, nonlinear associations exist.

---

## SI Paragraph

**Machine-learning validation of functional subset environmental associations.** To test whether the PGLS results reflect nonlinear or phylogenetically confounded patterns, we applied CatBoost gradient-boosted trees with Leave-One-Phylum-Out (LOPO) cross-validation (11 phyla, ≥10 genera each) to predict the same 15 environmental variables from genus-level metal-gene functional subset densities and individual Tier 1+2 KO densities. SHAP feature importance was extracted for all models with positive held-out Spearman ρ. Abundance-weighted models (weights = log₁₀(n_MicrobeAtlas_samples + 1)) were compared with unweighted models. For top-ranked KOs by SHAP importance and single-KO ρ, we additionally trained binary classifiers predicting KO presence/absence from environmental variables (LOPO AUC). Results are reported in Supplementary Data File S_catboost_env.

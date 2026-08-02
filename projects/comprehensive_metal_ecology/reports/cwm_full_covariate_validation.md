# CWM Validation — Full Environmental Covariate Model

## Overview

Extended the CWM community regression (Analysis 2) by adding environmental covariates beyond soil pH. Compared pH-only vs Tier-1 (pH+temp+|lat|) vs full-covariate models. Variance partitioned R² between CWM predictors and the environmental block.


*Tier-2 covariates (soil_som_pct, clay_pct, precip_mm, elevation_m) included from Spark extraction.*

---

## Covariate availability

### Environmental covariates used

| Covariate | Source | Coverage | Status |
|-----------|--------|----------|--------|
| pH (soil_pH÷10) | h3a_cwm_sample_data.csv | 64,466/83,401 | Tier-1 ✓ |
| temp_C (temp_K−273.15) | h3a_cwm_sample_data.csv (ERA5) | 68,998/83,401 | Tier-1 ✓ |
| abs_lat (\|lat\|) | h3a_cwm_sample_data.csv | 56,235/83,401 | Tier-1 ✓ |
| SOM (%) OLM 0cm | enriched_metadata_gee | 64,466/83,401 | Tier-2 ✓ |
| Clay (%) OLM 0cm | enriched_metadata_gee | 64,466/83,401 | Tier-2 ✓ |
| MAP (mm) ERA5 | enriched_metadata_gee | 68,998/83,401 | Tier-2 ✓ |
| Altitude (m) self-reported | sample_metadata | 4,412/83,401 | Tier-2 — excluded (<20%) |
| Elevation (m) ETOPO1 0.1° | arkinlab.envdbs.etopo1_elevation | 51,126/83,401 | Tier-2 ✓ |

**Rejected sources** (confirmed unusable):
- `arkinlab.envdbs.srtm_elevation`: ALL elevation values NULL (NB06 screen)
- `arkinlab.envdbs.soilgrids`: only bulk density + OCD; very sparse (152/5000 genera matched)
- `arkinlab.envdbs.chelsa_bioclim`: US Great Plains corridor only, not global

---

## Model results


### GEOROC_bedrock

| Metal | Model | Covariates | n | β(res) | p | q | β(cof) | p | q | R² | AIC |
|-------|-------|-----------|---|--------|---|---|--------|---|---|----|-----|
| Cu | pH_only | pH | 14,211 | -0.0472*** | 5.10e-08 | 7.66e-08 | -0.0287*** | 9.74e-04 | 1.46e-03 | 0.0387 | 25123 |
| Cu | tier1_env | pH+temp_C+abs_lat | 14,211 | -0.0470*** | 6.67e-08 | 1.00e-07 | -0.0305*** | 4.46e-04 | 6.69e-04 | 0.0431 | 25062 |
| Cu | full_covariates | pH+temp_C+abs_lat+soil_som_pct+clay_pct+precip_mm+elevation_m | 13,519 | -0.0482*** | 7.17e-08 | 1.07e-07 | -0.0277** | 1.83e-03 | 2.74e-03 | 0.0738 | 23447 |
| Ni | pH_only | pH | 20,625 | -0.0795*** | 4.03e-18 | 2.42e-17 | +0.0151† | 9.96e-02 | 9.96e-02 | 0.0133 | 46958 |
| Ni | tier1_env | pH+temp_C+abs_lat | 20,625 | -0.0750*** | 2.06e-16 | 6.18e-16 | +0.0121 | 1.83e-01 | 1.83e-01 | 0.0263 | 46688 |
| Ni | full_covariates | pH+temp_C+abs_lat+soil_som_pct+clay_pct+precip_mm+elevation_m | 19,515 | -0.0815*** | 9.21e-18 | 2.49e-17 | +0.0190* | 4.37e-02 | 4.37e-02 | 0.0457 | 44258 |
| Zn | pH_only | pH | 14,813 | -0.0247*** | 4.97e-06 | 5.97e-06 | -0.0309*** | 1.06e-08 | 3.17e-08 | 0.0484 | 12334 |
| Zn | tier1_env | pH+temp_C+abs_lat | 14,813 | -0.0202*** | 1.81e-04 | 2.17e-04 | -0.0325*** | 1.61e-09 | 4.83e-09 | 0.0569 | 12204 |
| Zn | full_covariates | pH+temp_C+abs_lat+soil_som_pct+clay_pct+precip_mm+elevation_m | 13,899 | -0.0184*** | 9.86e-04 | 1.18e-03 | -0.0267*** | 1.68e-06 | 3.36e-06 | 0.1074 | 11170 |
| Co | pH_only | pH | 15,965 | -0.0233** | 2.17e-03 | 2.17e-03 | -0.0186* | 1.45e-02 | 1.73e-02 | 0.0138 | 26076 |
| Co | tier1_env | pH+temp_C+abs_lat | 15,965 | -0.0191* | 1.05e-02 | 1.05e-02 | -0.0238** | 1.47e-03 | 1.77e-03 | 0.0474 | 25528 |
| Co | full_covariates | pH+temp_C+abs_lat+soil_som_pct+clay_pct+precip_mm+elevation_m | 15,346 | -0.0172* | 2.20e-02 | 2.20e-02 | -0.0226** | 2.50e-03 | 3.00e-03 | 0.0902 | 23933 |
| Cr | pH_only | pH | 19,856 | -0.0805*** | 8.72e-18 | 2.62e-17 | +0.0325*** | 5.36e-04 | 1.07e-03 | 0.0090 | 46793 |
| Cr | tier1_env | pH+temp_C+abs_lat | 19,856 | -0.0871*** | 1.07e-20 | 6.43e-20 | +0.0357*** | 1.33e-04 | 2.67e-04 | 0.0200 | 46576 |
| Cr | full_covariates | pH+temp_C+abs_lat+soil_som_pct+clay_pct+precip_mm+elevation_m | 18,807 | -0.0963*** | 8.28e-24 | 4.97e-23 | +0.0512*** | 8.24e-08 | 2.47e-07 | 0.0328 | 43803 |
| Pb | pH_only | pH | 16,535 | +0.0473*** | 1.30e-15 | 2.60e-15 | -0.0443*** | 7.00e-14 | 4.20e-13 | 0.0168 | 19264 |
| Pb | tier1_env | pH+temp_C+abs_lat | 16,535 | +0.0457*** | 1.13e-14 | 2.27e-14 | -0.0427*** | 5.06e-13 | 3.04e-12 | 0.0237 | 19152 |
| Pb | full_covariates | pH+temp_C+abs_lat+soil_som_pct+clay_pct+precip_mm+elevation_m | 15,547 | +0.0513*** | 1.24e-17 | 2.49e-17 | -0.0359*** | 1.97e-09 | 1.18e-08 | 0.0545 | 17546 |

### CSU_PF1_mobile

| Metal | Model | Covariates | n | β(res) | p | q | β(cof) | p | q | R² | AIC |
|-------|-------|-----------|---|--------|---|---|--------|---|---|----|-----|
| As | pH_only | pH | 47,774 | -0.0014*** | 9.07e-40 | 2.72e-39 | +0.0010*** | 2.41e-22 | 1.45e-21 | 0.0225 | -275428 |
| As | tier1_env | pH+temp_C+abs_lat | 47,774 | -0.0018*** | 9.71e-68 | 5.83e-67 | +0.0011*** | 8.81e-25 | 5.28e-24 | 0.0823 | -278437 |
| As | full_covariates | pH+temp_C+abs_lat+soil_som_pct+clay_pct+precip_mm+elevation_m | 45,884 | -0.0015*** | 6.36e-52 | 3.81e-51 | +0.0010*** | 6.97e-25 | 4.18e-24 | 0.1591 | -271338 |
| Cd | pH_only | pH | 47,774 | -0.0022*** | 1.55e-40 | 9.28e-40 | +0.0008*** | 2.53e-07 | 7.59e-07 | 0.0355 | -233750 |
| Cd | tier1_env | pH+temp_C+abs_lat | 47,774 | -0.0014*** | 1.69e-18 | 5.07e-18 | +0.0008*** | 8.42e-08 | 2.52e-07 | 0.1436 | -239428 |
| Cd | full_covariates | pH+temp_C+abs_lat+soil_som_pct+clay_pct+precip_mm+elevation_m | 45,884 | -0.0012*** | 5.93e-14 | 1.78e-13 | +0.0009*** | 8.76e-09 | 2.63e-08 | 0.1691 | -232294 |
| Cr | pH_only | pH | 47,774 | -0.0001 | 4.29e-01 | 4.29e-01 | -0.0004** | 1.58e-03 | 3.16e-03 | 0.0009 | -253310 |
| Cr | tier1_env | pH+temp_C+abs_lat | 47,774 | -0.0008*** | 1.68e-10 | 3.36e-10 | -0.0004** | 3.20e-03 | 6.40e-03 | 0.1251 | -259649 |
| Cr | full_covariates | pH+temp_C+abs_lat+soil_som_pct+clay_pct+precip_mm+elevation_m | 45,884 | -0.0003* | 3.05e-02 | 3.66e-02 | -0.0005*** | 5.70e-06 | 1.14e-05 | 0.2060 | -254917 |
| Cu | pH_only | pH | 47,774 | -0.0001 | 1.94e-01 | 2.33e-01 | -0.0002* | 2.95e-02 | 4.43e-02 | 0.0030 | -285389 |
| Cu | tier1_env | pH+temp_C+abs_lat | 47,774 | -0.0004*** | 3.84e-06 | 5.76e-06 | -0.0002* | 4.99e-02 | 5.99e-02 | 0.0512 | -287751 |
| Cu | full_covariates | pH+temp_C+abs_lat+soil_som_pct+clay_pct+precip_mm+elevation_m | 45,884 | -0.0002* | 1.66e-02 | 2.48e-02 | -0.0002** | 7.87e-03 | 1.12e-02 | 0.0994 | -280926 |
| Hg | pH_only | pH | 47,774 | +0.0013*** | 5.60e-17 | 1.12e-16 | +0.0000 | 8.38e-01 | 8.38e-01 | 0.1040 | -240588 |
| Hg | tier1_env | pH+temp_C+abs_lat | 47,774 | +0.0001 | 2.93e-01 | 2.93e-01 | +0.0000 | 7.57e-01 | 7.57e-01 | 0.3295 | -254434 |
| Hg | full_covariates | pH+temp_C+abs_lat+soil_som_pct+clay_pct+precip_mm+elevation_m | 45,884 | +0.0001 | 5.75e-01 | 5.75e-01 | -0.0001 | 6.73e-01 | 6.73e-01 | 0.3743 | -247758 |
| Pb | pH_only | pH | 47,774 | -0.0003** | 1.52e-03 | 2.28e-03 | +0.0001† | 5.86e-02 | 7.03e-02 | 0.0165 | -303295 |
| Pb | tier1_env | pH+temp_C+abs_lat | 47,774 | -0.0003*** | 1.75e-05 | 2.10e-05 | +0.0002* | 4.71e-02 | 5.99e-02 | 0.0222 | -303569 |
| Pb | full_covariates | pH+temp_C+abs_lat+soil_som_pct+clay_pct+precip_mm+elevation_m | 45,884 | -0.0005*** | 6.17e-09 | 1.23e-08 | +0.0002** | 9.32e-03 | 1.12e-02 | 0.0539 | -292833 |

---

## Variance Partitioning

R² partitioned on the full-model complete-case sample:
- **Unique CWM** = R²_full − R²_env_only
- **Unique env** = R²_full − R²_CWM_only
- **Shared** = R²_CWM + R²_env − R²_full


**Variance partitioning — GEOROC_bedrock** (R²_full = R²_CWM + R²_env − shared)

| Metal | n | R²_full | R²_CWM | R²_env | Unique_CWM | Unique_env | Shared |
|-------|---|---------|--------|--------|-----------|-----------|--------|
| Cu | 13,519 | 0.0738 | 0.0158 | 0.0598 | 0.0140 | 0.0580 | 0.0018 |
| Ni | 19,515 | 0.0457 | 0.0080 | 0.0386 | 0.0071 | 0.0378 | 0.0008 |
| Zn | 13,899 | 0.1074 | 0.0215 | 0.0953 | 0.0122 | 0.0859 | 0.0093 |
| Co | 15,346 | 0.0902 | 0.0044 | 0.0858 | 0.0045 | 0.0858 | -0.0001 |
| Cr | 18,807 | 0.0328 | 0.0047 | 0.0266 | 0.0063 | 0.0281 | -0.0015 |
| Pb | 15,547 | 0.0545 | 0.0041 | 0.0498 | 0.0046 | 0.0503 | -0.0005 |

**Variance partitioning — CSU_PF1_mobile** (R²_full = R²_CWM + R²_env − shared)

| Metal | n | R²_full | R²_CWM | R²_env | Unique_CWM | Unique_env | Shared |
|-------|---|---------|--------|--------|-----------|-----------|--------|
| As | 45,884 | 0.1591 | 0.0037 | 0.1547 | 0.0044 | 0.1554 | -0.0007 |
| Cd | 45,884 | 0.1691 | 0.0037 | 0.1680 | 0.0010 | 0.1654 | 0.0026 |
| Cr | 45,884 | 0.2060 | 0.0008 | 0.2039 | 0.0020 | 0.2052 | -0.0012 |
| Cu | 45,884 | 0.0994 | 0.0004 | 0.0981 | 0.0013 | 0.0990 | -0.0009 |
| Hg | 45,884 | 0.3743 | 0.0025 | 0.3743 | 0.0000 | 0.3719 | 0.0025 |
| Pb | 45,884 | 0.0539 | 0.0003 | 0.0530 | 0.0009 | 0.0537 | -0.0007 |

---

## Signal Summary

| Source | Model | β(res) positive (sig) | β(cof) negative (sig) |
|--------|-------|----------------------|----------------------|
| GEOROC_bedrock | pH_only | 1/6 (1 sig) | 4/6 (4 sig) |
| GEOROC_bedrock | full_covariates | 1/6 (1 sig) | 4/6 (4 sig) |
| CSU_PF1_mobile | pH_only | 1/6 (1 sig) | 2/6 (2 sig) |
| CSU_PF1_mobile | full_covariates | 1/6 (0 sig) | 3/6 (2 sig) |

---

## SI Paragraph

> **Community-level CWM validation — extended environmental covariate model.** We extended Analysis 2 by adding temperature (°C), |latitude|, and, where available from OpenLandMap / ERA5 Spark joins (scripts/extract_sample_env_extended.py), soil organic matter (SOM, %), clay content (%), mean annual precipitation (mm), and ETOPO1 elevation (m; arkinlab.envdbs.etopo1_elevation, 0.1° global grid). SRTM elevation was found to have all-NULL values in the BERDL envdbs registry and was excluded; CHELSA bioclim is US Great Plains corridor only and was excluded. Adding temperature and latitude (and SOM, clay, MAP where available) to the pH-only model modestly changed the CWM resistance–cofactor directional split at the community level. For GEOROC bedrock (n=6 metals): pH-only — 1/6 positive resistance (1 p<0.05), 4/6 negative cofactor (4 p<0.05); full model — 1/6 positive resistance (1 p<0.05), 4/6 negative cofactor (4 p<0.05). For CSU PF1 bioavailable (n=6 metals): pH-only — 1/6 positive resistance (1 p<0.05), 2/6 negative cofactor (2 p<0.05); full model — 1/6 positive resistance (0 p<0.05), 3/6 negative cofactor (2 p<0.05). Variance partitioning: GEOROC — env block dominant (mean unique_CWM=0.0081, unique_env=0.0577, shared=0.0016); CSU — env block dominant (mean unique_CWM=0.0016, unique_env=0.1751, shared=0.0003). These results are consistent with the conclusion that the community-level CWM signal does not substantially strengthen with additional environmental controls.
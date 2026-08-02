# Species-Level and Community-Level Robustness Analyses

## Overview

Two supplementary robustness analyses testing whether the genus-level metal-gene density / niche breadth signal holds at finer taxonomic and ecological resolution.

- **Analysis 1 data source**: kbase.ke_pangenome (Spark)
- **Analysis 2 data source**: MicrobeAtlas CWM × GEOROC geochemistry (h3a_cwm_sample_data.csv)

---

## Analysis 1 — Species-level sensitivity

### Rationale

The primary analysis operates at the GTDB genus level (n = 1,574 genera). If the genus-level signal is driven by genus-level aggregation artefacts, it should not replicate when the same relationship is tested within genera at the species level. Conversely, if the underlying biology operates at the species level and is visible through genome-size/density covariation, within-genus OLS should recover it.

### Data availability and fallback decisions

Species-level KO densities were queried from `kbase.ke_pangenome` (980 species across 5 target genera). Species-level niche breadth from MicrobeAtlas is unavailable (MicrobeAtlas provides OTU-to-genus mapping only). **Fallback applied**: (1) genus-level Levins' B used as a within-genus constant for context; (2) number of distinct isolation sources (from GTDB metadata) used as a species ecological breadth proxy where available; (3) within-genus OLS of species per-Mb KO density vs. species mean genome size as the primary result (tests whether genome-streamlining covariation is preserved at species resolution).

**Note on method**: No species-level phylogenetic tree is available for PGLS; OLS was used with the caveat that species within a genus are not phylogenetically independent. Results are descriptive.

### Top 5 genera by species count

| Genus | N species | N genomes |
|-------|-----------|-----------|
| *Pseudomonas_E* | 398 | 5687 |
| *Streptomyces* | 377 | 1920 |
| *Prevotella* | 358 | 2691 |
| *Streptococcus* | 214 | 17263 |
| *Collinsella* | 202 | 811 |

### Within-genus OLS results

**Response**: standardised species per-Mb KO density. **Predictor**: standardised species mean genome size (Mb). Negative β indicates smaller-genome species within a genus have higher per-Mb metal-gene density — consistent with the genus-level P1 finding.

| Genus | N species | β (density ~ genome size) | p | β (Tier1) | β (Tier2) | Genus B_std |
|-------|-----------|--------------------------|---|-----------|-----------|-------------|
| *Streptomyces* | 207 | -0.677 *** | 0.00e+00 | -0.513 | -0.617 | 0.304 |
| *Pseudomonas_E* | 297 | -0.633 *** | 0.00e+00 | -0.473 | -0.657 | NA |
| *Streptococcus* | 142 | -0.033 | 0.6952 | -0.084 | 0.020 | 0.104 |
| *Prevotella* | 242 | -0.301 *** | 0.00e+00 | -0.238 | -0.330 | 0.183 |
| *Collinsella* | 92 | -0.155 | 0.1396 | -0.129 | -0.134 | 0.150 |

*\* p<0.05, \*\* p<0.01, \*\*\* p<0.001, † p<0.10*

### Interpretation

5/5 target genera show a negative β for density vs genome size (consistent with primary P1 direction); 3 are individually significant at p < 0.05. 
The majority-negative direction supports the hypothesis that the genus-level signal reflects a pattern operating at finer taxonomic resolution. 
Because species-level niche breadth (MicrobeAtlas) is unavailable, a direct species-level replication of P1 cannot be completed with current data. The within-genus genome-size analysis provides indirect support for the streamlining mechanism. This limitation is noted in the Limitations section of the manuscript.

---

## Analysis 2 — Community-level CWM validation

### Rationale

The primary P1 analysis tests whether genera with higher per-Mb metal-gene density occupy narrower niches (cross-biome Levins' B). If this signal has ecological meaning, it should manifest at the community level: samples from metal-rich environments should have communities with higher community-weighted mean (CWM) metal-gene density. The resistance/cofactor split predicts that CWM resistance density may positively predict metal concentrations (metal stress selects for resistant taxa), while CWM cofactor density should be null or negative (cofactor genes reflect niche specialisation, not direct metal response).

### Data

- **CWM source**: MicrobeAtlas-derived CWM from the H3a analysis (n = 83,401 unique samples after deduplication).
- **Metal concentrations**: GEOROC geochemical database, spatially joined to sample coordinates.
- **CWM predictors**: cwm_ko (aggregate primary 140-KO density), cwm_resistance (Tier 1 KOs), cwm_cofactor (Tier 2 KOs).
- **CWM niche breadth**: not available per-sample in this dataset; omitted from models.
- **Covariates**: soil pH included where coverage ≥30% of metal-matched samples.
- **Metal threshold**: ≥30 samples with non-missing metal and CWM data required.

### Model A — Aggregate CWM metal-gene density → metal concentration

`log10(metal_concentration + 1) ~ CWM_ko_per_mb (z-scored)`

| Metal | N samples | β(CWM_ko) | p | q (BH) |
|-------|-----------|-----------|---|--------|
| Cu | 15,831 | -0.0418 *** | 2.50e-19 | 7.51e-19 |
| Ni | 22,648 | 0.0023 | 0.6183 | 0.6183 |
| Zn | 16,851 | -0.0326 *** | 5.55e-37 | 3.33e-36 |
| Co | 17,516 | -0.0098 * | 0.0171 | 0.0236 |
| Cr | 22,345 | 0.0119 * | 0.0197 | 0.0236 |
| Pb | 18,939 | -0.0150 *** | 6.86e-07 | 1.37e-06 |

*\* p<0.05, \*\* p<0.01, \*\*\* p<0.001, † p<0.10*

### Model B — Resistance/cofactor split → metal concentration

`log10(metal_concentration + 1) ~ CWM_resistance_z + CWM_cofactor_z [+ soil_pH]`

| Metal | N samples | β(resistance) | p | q | β(cofactor) | p | q |
|-------|-----------|--------------|---|---|-------------|---|---|
| Cu +pH | 13,955 | -0.0542 *** | 7.36e-11 | 8.83e-11 | -0.0293 *** | 4.87e-04 | 6.28e-04 |
| Ni +pH | 19,677 | -0.0682 *** | 6.28e-16 | 1.88e-15 | 0.0297 *** | 5.23e-04 | 6.28e-04 |
| Zn +pH | 14,703 | -0.0366 *** | 5.36e-14 | 1.07e-13 | -0.0252 *** | 2.93e-07 | 5.86e-07 |
| Co +pH | 15,789 | -0.0263 *** | 3.91e-04 | 3.91e-04 | -0.0209 ** | 0.0053 | 0.0053 |
| Cr +pH | 19,454 | -0.0935 *** | 2.56e-25 | 1.54e-24 | 0.0475 *** | 2.24e-07 | 5.86e-07 |
| Pb +pH | 16,220 | 0.0377 *** | 5.39e-11 | 8.08e-11 | -0.0388 *** | 3.38e-11 | 2.03e-10 |

*+pH = soil pH included as covariate; \* p<0.05, \*\* p<0.01, \*\*\* p<0.001, † p<0.10*

### Comparison to primary genus-level findings

- **CWM resistance vs metal concentration**: 1/6 metals show positive β (predicts higher metal → higher resistance gene communities; 6 individually significant at p < 0.05).
- **CWM cofactor vs metal concentration**: 4/6 metals show negative β (6 individually significant at p < 0.05).
- **Directional signal is weak** at the community level: neither resistance nor cofactor CWM shows consistent directional association with metal concentrations across metals. The community-level signal may require within-biome comparisons or contamination categories rather than raw concentration predictors.

### Interpretation

The community-level CWM regression tests the ecological analog of the genus-level P1 signal: whether samples from metal-richer environments assemble communities with higher metal-gene investment. This is a conceptually distinct hypothesis (community assembly vs. evolutionary niche specialisation) but should show correlated patterns if the biology is self-consistent. 

Key caveats: (1) GEOROC metal concentrations reflect geological substrate, not contemporary pore-water bioavailability; (2) CWM niche breadth was not available at the per-sample level and could not be included; (3) OLS was used (no phylogenetic correction at the community level); (4) the relationship between metal concentration and microbial community composition is mediated by many unmeasured variables (redox state, SOM, pH), which are only partially controlled here by soil pH.

---

## Summary

| Analysis | Key result | Consistent with P1? |
|----------|-----------|---------------------|
| 1 (species-level) | 5/5 genera: negative β within genus (density ~ genome size) | Partially (genome-streamlining pattern present within genera) |
| 2 (CWM community) | CWM resistance: positive for 1/6 metals; CWM cofactor: negative for 4/6 metals | Mixed |

**Data files produced**:
- `data/species_level_density.csv` — species-level KO density per genus
- `data/cwm_community_validation_results.csv` — CWM regression results per metal

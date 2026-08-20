# USA Env-PCA Bioindicators

## Status

Active — companion analysis to [metal_contamination_bioindicators](../metal_contamination_bioindicators/). Results will be integrated into the global bioindicators project once complete. See [metal_ecology_thesis](../metal_ecology_thesis/) for the synthesis umbrella.

## Research question

Which genera and metal-resistance KOs are diagnostic of **specific multi-variate metal contamination conditions** in USA soils? We use PCA on the joint env space (USGS metals + soil pH/SOM + climate) to find contamination fingerprints, then identify genera and KOs that occupy extreme positions in that space.

Motivating example: *Rhodanobacter* tracks acid pH + high Cr/Ni + high SOC specifically. We want to discover many such indicator taxa systematically.

## Hypotheses

| ID | Hypothesis |
|---|---|
| H0 | Genera occupy distinct positions in env_PC space (≥60% variance in PC1+PC2) |
| H1 | Specific genera are diagnostic of specific contamination fingerprints (Rhodanobacter validation) |
| H2 | Metal resistance/transport KOs are more specific env_PC indicators than cofactor/sensing KOs |
| H3 | High-λ KOs are better genus-level env indicators (cross-ref with CME project) |
| H4 | Sample-level SHAP top genera (NB02) match genus-level fingerprint bioindicators (NB00) |

## Notebooks

| Notebook | Status | Description |
|---|---|---|
| 00_genus_env_pca.ipynb | Pending | Genus-level env PCA + fingerprint clustering |
| 01_ko_bioindicators.ipynb | Pending | KO/guild-level bioindicators vs env_PCs |
| 02_sample_level_ml.ipynb | Pending | Sample-level CatBoost (Spark) + SHAP validation |

## Differences from `metal_contamination_bioindicators`

- USA-only (vs global) → richer env data
- Continuous multi-variate fingerprinting (vs binary contamination label)
- Asks "what conditions does this taxon indicate?" (vs "can communities predict contamination?")
- No Spark needed for NB00/NB01 (genus-level analysis is fast)

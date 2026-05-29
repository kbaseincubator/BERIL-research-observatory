# Soil Microbial Dark Matter: Genomic Frontiers and the Clay Shield Null Result

## Research Questions

1. **Clay Shield Hypothesis**: Does high clay content buffer the impact of industrial and
   geochemical stressors (mine proximity, nighttime light pollution, uranium contamination)
   on microbial functional potential in global soil metagenomes?

2. **Genomic Discovery Index**: Where on Earth are the largest gaps between observed
   microbial diversity (16S OTU richness) and available genomic reference coverage, and
   which soil types constitute the "dark matter" frontier?

## Status

**Active** — Core analyses complete in exploratory notebooks. Clay Shield: null result
established across three notebook iterations. GDI: biome rankings complete. Manuscript
framing and figures pending.

Initiated: 2026-05-02. Source notebooks: `projects/misc_exploratory/exploratory/`.

## Key Findings (Preliminary)

### Clay Shield Hypothesis — Null Result

- **5,441 soil 16S rRNA amplicon samples** (deterministic 10% global subsample) with
  clay content, mine proximity, nighttime lights, uranium, and functional gene counts.
- **All predictive models have negative out-of-sample R²**:
  - Soil & Climate World: R² = −0.205 ± 0.197
  - Geochemical World: R² = −0.331 ± 0.071
  - Industrial World: R² = −0.221 ± 0.042
- **Shield efficiency test**: low-clay CV R² = −0.268 vs. high-clay CV R² = −0.292;
  difference = 0.024 [95% CI: −0.423, 0.161] — not significant.
- **Conclusion**: Clay content does not detectably buffer industrial or geochemical
  stress effects on microbial functional potential at global scale. All apparent
  interactions are observational and within the noise of batch/sequencing confounding.

### Genomic Discovery Index (GDI)

- **GDI = OTU Richness / (Mean Genome Completeness + 1)** — quantifies the gap between
  observed diversity and genomic reference coverage at 1° spatial bins (~11 km radius).
- **Highest GDI (genomic frontiers)**: Forest (902.36) and Cropland (890.82) soils —
  high observed species richness but sparse genome reference databases.
- **Lower GDI (relatively well-mapped)**: Grassland (503.42) and Wetland (525.13).
- **pH discovery bias**: frontier areas (GDI > 1000) have mean pH = 6.74 vs. mapped
  areas (GDI < 1000) mean pH = 5.94 — a **+0.8 pH unit gap**, indicating genomic
  databases are biased toward acidic soils and alkaline-specialist microbes are
  disproportionately dark matter.

## Notebooks Consolidated

| NB | Source Notebooks | Status | Description |
|---|---|---|---|
| NB01 | `clay_shield_hypothesis.ipynb`, `clay_shield_hypothesis_v2.ipynb`, `clay_shield_hypothesis_v3.ipynb` | ✅ Done | Primary mixed-effects models; shield efficiency test; GroupKFold CV; null result established |
| NB02 | `clay_impact_richness_usgs.ipynb`, `clay_impact_richness_mindat.ipynb` | ✅ Done | Clay-richness relationships using USGS and MinDat mine databases |
| NB03 | `clay_and_pH_industrial_proximity.ipynb` | ✅ Done | Joint pH + clay + industrial proximity model; interaction terms |
| NB04 | `quantifying_microbial_dark_matter_GDI_analysis.ipynb`, `df_soil_genomic_context.ipynb` | ✅ Done | GDI computation; biome rankings (Forest=902, Grassland=503); pH discovery bias (+0.8 units) |
| NB05 | `notebooks/05_validation.ipynb` | 🔲 Todo | Spatial autocorrelation in clay-functional potential residuals (Moran's I); rarefaction-corrected GDI; uncertainty bands on GDI by biome |
| NB06 | `notebooks/06_figures.ipynb` | 🔲 Todo | Manuscript figures |

### NB05 — Validation Analyses

1. **Spatial autocorrelation in clay model residuals**
   — Mixed-effects model residuals may be spatially structured (same-region samples share
   geology). Compute Moran's I on model residuals. If significant, apply SEVM or spatial
   lag correction and re-test the shield efficiency contrast.

2. **Rarefaction-corrected GDI**
   — GDI conflates biological richness with sampling effort. Rarefy 16S OTU tables to a
   uniform depth before computing richness. Re-rank biomes to verify Forest and Cropland
   remain the highest-GDI frontiers after correcting for read count differences.

3. **GDI uncertainty bands**
   — Bootstrap GDI values (1,000 resamples per biome) to report 95% CIs on biome
   rankings. Confirm Forest vs. Grassland GDI difference (902 vs. 503) is statistically
   distinguishable.

4. **Negative R² interpretation**
   — Negative out-of-sample R² in all three predictive worlds means the models predict
   worse than the training mean. Investigate whether this is driven by: (a) train/test
   distributional shift, (b) extreme outlier samples in test folds, or (c) genuine
   unpredictability. Report MSE decomposition (bias² + variance + irreducible error).

## Data Sources

| Database | Tables/Files Used | Access |
|---|---|---|
| BERIL Observatory | 16S OTU counts, soil sample metadata | REST API + local CSVs |
| SoilGrids / OpenLandMap | Clay content at 0 cm depth (`olm_soil_clay_0cm_pct`) | Local CSV |
| MinDat / USGS | Mine locations (distance to nearest mine) | Local CSV |
| ERA5 | Temperature, precipitation | Local CSV |
| GeoROC | Uranium, other geochemical variables | Local CSV |
| `kbase_ke_pangenome` | Genome completeness (for GDI denominator) | JupyterHub Spark |

## Source Data

```
misc_exploratory/exploratory/data/
  soil_samples_clay_functional.csv   # 5,441 samples with clay + stressor + functional gene data
  df_soil_genomic_context.csv        # Soil samples + genome completeness per spatial bin
```

## Relationship to Other Projects

| Project | Relationship |
|---|---|
| `microbeatlas_metal_ecology` | That project tests OTU richness vs. mine proximity; this project tests functional potential vs. clay + industrial stressors — different outcome, overlapping stressors |
| `soil_metal_functional_genomics` | db-RDA (R²=0.799) shows metals explain functional gene variance; this project shows clay does NOT buffer that effect |
| `metal_resistance_global_biogeography` | Spatial data gap quantification (ENA coordinate coverage) is the genome-resolved complement to GDI's 16S-based gap analysis |

## Authors

Heather MacGregor

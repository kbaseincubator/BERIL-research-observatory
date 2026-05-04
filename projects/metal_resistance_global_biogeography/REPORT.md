# Report: Global Biogeography of Environmental Bacterial Metal Resistance

## Status

Preliminary — data extraction and coordinate retrieval complete (NB01). NB02 spatial
analysis and NB03 figures pending.

## Key Findings

- **260,652 environmental MAGs** extracted from MGnify; 30,497 after filtering
  host-associated biomes.
- **22,356 MAGs with usable geospatial coordinates** (73.3% coordinate coverage of
  environmental MAG set).
- **ENA batch API retrieval**: 24,511 sample records; 16,964 (69.2%) have valid lat/lon
  pairs — a **30.8% spatial data gap** in public metagenomic archives.
- Global map code drafted (geopandas + matplotlib) showing distribution of
  metal-resistant (n_metal_types > 0) vs. susceptible MAGs coloured by metal diversity.
- Known issue: NameError on plt import in map cell (missing `import matplotlib.pyplot`
  in that cell); fix required before NB02.

## Interpretation

Roughly one third of publicly archived metagenomic samples lack usable geospatial
coordinates, constituting a systematic gap in the ability to map microbial metal
resistance at global scale. Among the 22,356 MAGs with coordinates, metal-resistant
genomes are not uniformly distributed, but hotspot identification and sampling-effort
correction are required before regional patterns can be interpreted (NB02).

The 30.8% ENA coordinate gap is a data quality finding independent of the biological
question: it implies that any global map of metal resistance distribution based on
public archives is subject to substantial geographic blind spots. Which biomes are most
underrepresented is a key open question.

## NB02 Spatial Analysis Results

**Global metal resistance prevalence:** 2.8% of 22,356 MAGs with coordinates carry
≥1 metal resistance type — substantially lower than implied by reporting on the 30,497
filtered MAG set. Metal resistance is rare in the global environmental MAG pool.

**5° grid hotspot analysis** (289 cells with ≥5 MAGs; Fisher's exact, BH FDR):
- **11 significant hotspots** (OR>2, q<0.05), **3 coldspots** (OR<0.5, q<0.05).
- Top hotspot: Atacama/Andean region, Chile (lat=-25°, lon=-70°): 21.8% prevalence,
  OR=9.83, q=7.6e-12, n=101 MAGs.
- Eastern and central USA clusters (lat=40°, lon=-80° and -90°): OR=7.9 and 6.3.
- East/Southeast Asia cluster (lat=25-30°, lon=105-120°): OR=4.4–5.9.
Figure: `figures/fig_nb02_global_hotspot_map.png`

**Biome-stratified prevalence** (Fisher's exact vs. global baseline, BH FDR):
| Biome | n MAGs | Prevalence | OR | q |
|---|---|---|---|---|
| Soil | 7,939 | 5.8% | 5.05 | 1.8e-82 |
| Rhizosphere | 422 | 1.9% | 0.66 | 0.30 (NS) |
| Marine | 13,995 | 1.2% | 0.20 | 9.2e-80 |

Soil is significantly enriched for metal resistance (5.8%, OR=5.05); Marine is
significantly depleted (1.2%, OR=0.20). Figure: `figures/fig_nb02_biome_prevalence.png`

**ENA coordinate gap:** 0 of 532 MAG grid cells lack ENA coordinate coverage — the
ENA coordinate file already covers all areas represented in the MAG coordinate dataset.
The 30.8% gap (16,964/24,511 valid pairs) is a per-sample gap, not a geographic gap;
it reflects samples without coordinates, not grid cells with no samples at all.

**Key corrections to REPORT:**
- The "22,356 MAGs with coordinates" dataset shows 2.8% global metal resistance
  prevalence, not a higher figure. This is much lower than the 21.8% T4SS prevalence,
  confirming that metal resistance genes (AMRFinderPlus) and HGT machinery (T4SS) are
  distinct features not uniformly co-distributed.
- Expedition-level clustering check pending for the Atacama and USA clusters.

## Pending Analyses

1. Expedition-level clustering: test if Atacama (OR=9.8) and USA clusters are
   single-study artefacts (check distinct sample_accession prefixes per hotspot)
2. Sampling effort correction: confirm hotspots persist after normalising by log(n_MAGs)
3. Fix matplotlib import in NB01 map cell for production figure

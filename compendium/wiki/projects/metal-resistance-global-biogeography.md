# Metal Resistance Global Biogeography

This project mapped the global distribution of metal-resistance genes across environmental bacterial genomes using genome-resolved metagenome-assembled genomes (MAGs) with precise geospatial coordinates from public archives. Metal resistance proved geographically heterogeneous, with 11 significant hotspots identified by Fisher's-exact test on a 5° grid, the strongest being the Atacama/Andean region (21.8% prevalence, OR=9.83); soil environments are significantly enriched (5.8%, OR=5.05) while marine environments are depleted (1.2%, OR=0.20). However, roughly one-third of publicly archived metagenomic samples lack usable coordinates, a systematic data-quality gap that limits the map's geographic completeness and highlights which biomes remain underrepresented in global sequencing efforts.

## Key findings

- Expedition-level clustering validation remains pending, so hotspot signals such as Atacama cannot yet be distinguished from single-study geographic artifacts. *(confidence: high)*
- Hotspot results should be treated as provisional until sampling-effort normalisation is complete, since many apparent hotspots reflect sequencing effort in Europe, the USA, and East Asia. *(confidence: high)*
- The low 2.8% metal-resistance prevalence may reflect a narrow GapMind pathway definition rather than true biological rarity, as the pathway set may not cover all known mechanisms such as efflux pumps, metallothioneins, and metal-sequestering operons. *(confidence: medium)*
- Roughly one third of publicly archived metagenomic samples lack usable geospatial coordinates, a systematic data-quality gap that subjects any global map of microbial metal resistance to substantial geographic blind spots. *(confidence: high)*
- The 2.8% global metal-resistance prevalence is far below the 21.8% T4SS prevalence, confirming that metal resistance genes and HGT machinery are distinct features that are not uniformly co-distributed. *(confidence: medium)*
- Using genome-resolved MAGs with explicit AMRFinderPlus metal-resistance annotations and precise coordinates provides strain-level spatial resolution and direct gene presence/absence, complementing OTU-level 16S surveys rather than duplicating them. *(confidence: medium)*
- A 5° grid Fisher's-exact analysis over 289 cells identified 11 significant metal-resistance hotspots and 3 coldspots, with the Atacama/Andean region of Chile the strongest (21.8% prevalence, OR=9.83, q=7.6e-12). *(confidence: high)*
- Biome-stratified analysis shows soil is significantly enriched for metal resistance (5.8% prevalence, OR=5.05) while marine MAGs are significantly depleted (1.2%, OR=0.20). *(confidence: high)*
- ENA batch API retrieval returned 24,511 sample records of which only 16,964 (69.2%) have valid lat/lon pairs, exposing a 30.8% per-sample spatial data gap in public metagenomic archives. *(confidence: high)*
- Of 260,652 environmental MAGs extracted from MGnify, 22,356 carry usable geospatial coordinates, giving 73.3% coordinate coverage of the environmental MAG set. *(confidence: high)*
- Only 2.8% of the 22,356 coordinate-bearing MAGs carry at least one metal resistance type, indicating that metal resistance is rare in the global environmental MAG pool. *(confidence: high)*
- The 30.8% coordinate gap is a per-sample gap rather than a geographic one, since 0 of 532 MAG grid cells lack ENA coordinate coverage. *(confidence: high)*
- Overlaying spatially blind grid cells (those with under 50% coordinate coverage) with biome type offers a route to identify which ecosystems are most underrepresented in public metagenomic archives. *(confidence: medium)*
- The genome-resolved geospatial map provides a substrate for mapping exemplar metal-generalist MAGs and overlaying spatial GC-content gradients from related projects. *(confidence: low)*

## Topics

- [Topic: Environment Biogeography](../topics/environment-biogeography.md)
- [Topic: Functional Dark Matter](../topics/functional-dark-matter.md)
- [Topic: Metal Resistance](../topics/metal-resistance.md)
- [Topic: Microbial Ecotypes](../topics/microbial-ecotypes.md)
- [Topic: Mobile Genetic Elements](../topics/mobile-genetic-elements.md)

## Authors

- [Heather MacGregor](../authors/heather-macgregor.md)

[Open the full report →](../../../projects/metal_resistance_global_biogeography/REPORT.md)

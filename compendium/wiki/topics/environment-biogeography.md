# Environment Biogeography

Environment biogeography — the study of how microbial communities are shaped by, and in turn adapted to, their physical and chemical surroundings — is one of the organizing lenses of this synthesis wiki. Across dozens of projects spanning groundwater plumes, agricultural soils, forest warming plots, coral-associated field sites, clinical airways, and global metagenomic archives, a consistent theme emerges: where a microorganism lives, and what chemical stresses its habitat imposes, leaves measurable imprints on its genome content, functional repertoire, and ecological range. This page collects and organizes those findings, explaining what the corpus collectively says about the forces that distribute microbial life across environments.

## Overview

Microbial biogeography sits at the intersection of community ecology and functional genomics. The central questions are simple to state: Do microbes from different habitats look different at the genomic level? Do environmental gradients — pH, metal contamination, temperature, substrate availability — predict which organisms are present and what metabolic pathways they carry? And do those patterns reflect genuine ecological adaptation or are they artefacts of sampling bias, phylogenetic history, and the uneven coverage of public genome databases?

The projects contributing to this page address these questions at multiple scales: from meter-scale hydrological structure at a contaminated subsurface field site, through biome-level enrichment of functional genes, to global maps of metal-resistance hotspots and machine-learning embeddings that encode satellite-image-derived environmental context. Taken together, they show that environmental structure is real and pervasive, but that quantifying it cleanly requires careful accounting for confounders including genome database composition, cultivation bias, spatial autocorrelation, and missing metadata.

## What the Corpus Shows

### Environment leaves strong imprints on genome content

Across many independent analyses, isolation environment is among the strongest predictors of microbial functional gene content. Polyhydroxybutyrate (PHB) — a carbon-storage polymer produced by bacteria under feast–famine conditions — follows a more-than-tenfold gradient in prevalence from temporally variable environments (plant-associated 44%, soil 43.6%) to stable host-associated environments (clinical 7.4%, animal 3.3%), supporting the view that environmental selection drives PHB acquisition [\[1\]](#references). This enrichment is robust to genome size [\[2\]](#references) and confirmed by NMDC metagenomic cross-validation [\[3\]](#references).

Prophage burden — the number of integrated viral sequences a bacterium carries — is similarly shaped by environment, which explains substantially more variance in prophage module composition than host phylogeny does (PERMANOVA F = 30.04 for environment vs. F = 6.17 for phylogeny) [\[4\]](#references). Within each genome-size quartile, environment still significantly influences prophage module counts, showing the signal is not simply a proxy for larger genomes [\[5\]](#references). Prophage burden inferred from NMDC samples correlates positively with pH and temperature [\[6\]](#references), a pattern consistent with pH-sensitive stress-induced phage induction and independently validated across 6,365 metagenomic samples [\[7\]](#references).

In soil functional genomics, metal concentrations are strongly associated with community COG (Clusters of Orthologous Groups) profiles: a distance-based redundancy analysis reports R² = 0.799 (p = 0.005), meaning measured soil metals explain roughly 80% of COG variance after conditioning on batch effects [\[8\]](#references). A community-weighted analysis of 51,748 soil samples found 2,355 significant COG–metal associations across nine metals [\[9\]](#references), and biome-stratified analyses show that soil, marine, and wastewater communities have distinct metal–COG relationships rather than a universal resistance programme [\[10\]](#references).

### Ecological niche breadth is linked to functional diversity

One of the most cross-cutting findings in the corpus is that species occupying broader environmental niches tend to carry more diverse functional repertoires. Using AlphaEarth embeddings — compressed representations of satellite imagery associated with genome isolation coordinates — ecological niche breadth was the strongest predictor of mean metabolic pathway completeness (r = 0.392, p = 7.1×10⁻⁷⁰), and embedding variance was an even stronger predictor (r = 0.412, p = 1.8×10⁻⁷⁷) [\[11\]](#references) [\[12\]](#references). Among AMR (antimicrobial resistance) genes specifically, broader niche breadth strongly predicts higher AMR count (Spearman rho = 0.466) [\[13\]](#references).

At the genus level, the number of distinct metal types resisted is the only metal AMR predictor of ecological niche breadth to survive phylogenetic correction (PGLS β = +0.021, p = 1.5×10⁻⁴) [\[14\]](#references). This relationship is independent of species richness and genome size [\[15\]](#references) and is consistent with a metabolic versatility hypothesis: organisms that handle diverse metal stresses are adapted to chemically complex environments more broadly [\[16\]](#references). Independent validation in 1,624 BERDL groundwater samples confirms that genera with broader metal-type resistance repertoires are significantly more prevalent (Spearman ρ = +0.112, p = 0.0019) [\[17\]](#references).

Bacterial ecological niche breadth is also strongly phylogenetically conserved (Pagel's λ = 0.787), as is habitat range (λ = 0.909) [\[18\]](#references), meaning that closely related species tend to occupy similar environmental ranges — a pattern that must be controlled for before attributing gene-content variation to environmental selection.

### Carbon and metabolic axes differentiate ecosystem types

The metabolic machinery of a community reflects its ecosystem type. A principal component analysis of a 220-sample by 80-pathway community completeness matrix captured 49.4% of variance in PC1, with Soil and Freshwater communities occupying nearly non-overlapping regions of metabolic space [\[19\]](#references). Carbon utilization pathways — not amino acid pathways — load almost entirely on PC1, suggesting that carbon substrate availability is the primary axis differentiating ecosystem metabolic type [\[20\]](#references). Of 18 amino acid pathways, 17 show significantly different completeness levels across ecosystem types [\[21\]](#references). Among the *Pseudomonas* pangenome, carbon pathway profiles are significantly associated with isolation environment (permutation p = 0.006) and a Random Forest classifier predicts four environment classes from those profiles with balanced accuracy of 0.408 [\[22\]](#references) [\[23\]](#references).

### Geography encodes environment, but not always cleanly

AlphaEarth embeddings — trained on satellite imagery — do encode real geographic signal. Cosine distance between embeddings increases monotonically with physical distance across 50,000 sampled genome pairs [\[24\]](#references). Environmental samples show 3.4-fold stronger geographic signal than human-associated samples, because hospitals worldwide share similar urban satellite imagery while natural landscapes differentiate strongly [\[25\]](#references). UMAP reduction of the 64-dimensional embeddings reveals 320 DBSCAN clusters (a density-based clustering algorithm), many dominated by a single environment category [\[26\]](#references). Ecological diversity from these embeddings predicts metabolic pathway completeness better than spatial spread alone [\[27\]](#references).

At the community level, 16S amplicon data can map subsurface hydrology at meter scale: the plume flow path at the Oak Ridge SSO field site is visible purely in Bray-Curtis community similarity, with wells forming a diagonal corridor that aligns with the expected contamination-plume flow from the northeast [\[28\]](#references) [\[29\]](#references). Sediment communities show significant distance-decay at meter scale, with community turnover aligned east-to-west rather than along the hillslope [\[30\]](#references).

### Environmental enrichment of specific gene families

Several gene families show consistent environment-specific enrichment across independent analyses. The xoxF methanol dehydrogenase gene is strongly enriched in soil/sediment (OR = 1.92, p = 6×10⁻³⁹) and strongly depleted in host-associated environments (OR = 0.058, p ≈ 0) [\[31\]](#references) [\[32\]](#references). The 1-aminocyclopropane-1-carboxylate deaminase gene acdS is 7-fold more prevalent in soil/rhizosphere than other environments, and pqqC (involved in pyrroloquinoline quinone biosynthesis) is 2.9-fold enriched [\[33\]](#references). Plant-associated compartment identity itself explains only about 6% of microbial functional-profile variance [\[34\]](#references), but type III secretion systems (T3SS) are roughly 2-fold more prevalent in rhizosphere biomes (21.6–24.0%) than bulk soil (12.3%) [\[35\]](#references).

T4SS (type IV secretion system) conjugative machinery — which enables horizontal gene transfer — is present in about 21.8% of high-quality environmental MAGs, and T4SS-CAZy synteny (co-occurrence with carbohydrate-active enzymes) is most strongly enriched in rhizosphere biomes (barley rhizosphere OR = 10.4) [\[36\]](#references) [\[37\]](#references). Within the dark gene literature, 10 accessory dark gene clusters show significant environmental enrichment across 31 species, including stress and nitrogen genes enriched in clinical isolates [\[38\]](#references).

### Clinical versus environmental species differ systematically in AMR

Human/clinical species carry 2.7-fold more AMR per species (10.6 clusters per species) than environmental species, and their AMR is less "core" — carried in a smaller fraction of strains — than the AMR of soil or plant-associated species [\[39\]](#references). Continuous AlphaEarth environmental embeddings independently confirm this, showing that environmental distance predicts AMR profile distance (Mantel r = 0.098, p = 0.001) most strongly for clinical species [\[40\]](#references). Bacteria isolated from heavy metal contamination sites have predicted metal-tolerance scores a full standard deviation above environmental baseline (Cohen's d = +1.00, p = 0.006), in a dose-dependent gradient [\[41\]](#references) [\[42\]](#references).

### Sampling gaps and database biases shape what we can see

Genome databases are not a neutral mirror of natural communities. AlphaEarth covers only 28.4% of genomes in major pangenome databases and is biased toward genomes with valid GPS metadata [\[43\]](#references), with 38% of the embedded set being human-associated [\[44\]](#references). About one-third of publicly archived metagenomic samples lack usable geospatial coordinates [\[45\]](#references). Forest (GDI 902.36) and Cropland (890.82) soils are the highest "genomic discovery index" frontiers — where observed microbial diversity far outstrips genomic reference coverage — while Grassland and Wetland are relatively well-mapped [\[46\]](#references). Genomic databases show a +0.8 pH unit discovery bias toward acidic soils, leaving alkaline-specialist microbes disproportionately as dark matter [\[47\]](#references).

## Projects and Evidence

**ENIGMA SSO ASV Ecology** ([`enigma_sso_asv_ecology`](../projects/enigma-sso-asv-ecology.md)) is the most spatially precise study in the corpus, demonstrating that 16S community structure resolves meter-scale hydrology at the Oak Ridge field site. The plume model — contamination entering from the northeast and flowing southwest through the saturated zone — is confirmed by Bray-Curtis distance, distance-decay, and well-corridor alignment [\[48\]](#references). Groundwater communities sampled nine days apart show remarkable stability (sampling date explains 0.8% of variance versus 49.9% for well identity) [\[49\]](#references), and groundwater is enriched in plume-adapted denitrifiers and iron oxidizers relative to sediment-attached communities [\[50\]](#references).

**Lab Field Ecology** ([`lab_field_ecology`](../projects/lab-field-ecology.md)) bridges Fitness Browser lab phenotypes to field ecology, demonstrating that Caulobacter and Sphingomonas are sensitive indicators of uranium contamination while Herbaspirillum and Bacteroides may be tolerant colonizers [\[51\]](#references). Of 26 Fitness Browser genera, 14 are detected in Oak Ridge groundwater, but lab metal tolerance does not simply translate to field abundance because field niches are multidimensional [\[52\]](#references).

**Metal Resistance Global Biogeography** ([`metal_resistance_global_biogeography`](../projects/metal-resistance-global-biogeography.md)) mapped metal resistance across 22,356 coordinate-bearing MAGs and identified 11 metal-resistance hotspots globally, with the Atacama/Andean region the strongest (OR = 9.83) [\[53\]](#references). Only 2.8% of environmental MAGs carry at least one metal resistance type, indicating metal resistance is rare globally despite local enrichment [\[54\]](#references).

**MicrobeAtlas Metal Ecology** ([`microbeatlas_metal_ecology`](../projects/microbeatlas-metal-ecology.md)) provided the first analysis linking genus-level metal type diversity from pangenome AMR annotations across 6,789 species to ecological niche breadth from a 464K-sample 16S atlas with phylogenetic control [\[55\]](#references).

**Env Embedding Explorer** ([`env_embedding_explorer`](../projects/env-embedding-explorer.md)) characterized the structure and biases of AlphaEarth environmental embeddings, developing a harmonization of 5,774 free-text isolation source values to 12 broad environment categories [\[56\]](#references) and identifying that 36.6% of embedded genomes cluster at institutional addresses rather than true field sites [\[57\]](#references).

**NMDC Community Metabolic Ecology** ([`nmdc_community_metabolic_ecology`](../projects/nmdc-community-metabolic-ecology.md)) performed the first application of GapMind community-weighted pathway completeness scores to predict environmental metabolomics across 220 NMDC samples spanning soil and aquatic habitats [\[58\]](#references).

**Soil Metal Functional Genomics** ([`soil_metal_functional_genomics`](../projects/soil-metal-functional-genomics.md)) and **Soil Frontier Genomics** ([`soil_frontier_genomics`](../projects/soil-frontier-genomics.md)) focus on soils as an incompletely characterized frontier. The former demonstrates that soil metal concentrations explain 80% of COG variance and that biome-specific responses differ for soil, marine, and wastewater communities [\[59\]](#references). The latter developed the Genomic Discovery Index (GDI = OTU Richness / (Mean Genome Completeness + 1)) to quantify genomic sampling gaps and found that the clay-shield hypothesis — the idea that clay mineral content buffers microbial communities from industrial or geochemical stress — is not supported at global scale [\[60\]](#references) [\[61\]](#references).

**Harvard Forest Warming** ([`harvard_forest_warming`](../projects/harvard-forest-warming.md)) examines how 25 years of +5°C warming reshapes a forest soil microbiome, showing a real but modest compositional shift (Actinobacteria up, Acidobacteria down) [\[62\]](#references) and horizon-specific responses [\[63\]](#references).

**PHB Granule Ecology** ([`phb_granule_ecology`](../projects/phb-granule-ecology.md)) demonstrates that PHB prevalence is a powerful environmental indicator, following a >10-fold gradient from variable to stable environments, and that this enrichment is robust to genome size within all four genome-size quartiles [\[1\]](#references).

**Ecotype Env Reanalysis** ([`ecotype_env_reanalysis`](../projects/ecotype-env-reanalysis.md)) directly tested whether AlphaEarth environmental similarity predicts gene content across ecotypes and found a largely null result: the fraction of environmental genomes per species does not predict environment–gene-content correlation strength (Spearman rho = −0.085, p = 0.25) [\[64\]](#references), and restricting to environmental species did not yield stronger correlations [\[65\]](#references).

## Connections

This page is closely linked to [Microbial Ecotypes](../topics/microbial-ecotypes.md) because ecotype classification is one of the primary frameworks for quantifying environment–genome associations; the ecotype reanalysis findings here feed directly into that page's discussion of whether discrete lifestyle classes predict functional divergence.

The [Metal Resistance](../topics/metal-resistance.md) page is adjacent because metal contamination is one of the most clearly documented abiotic drivers of community and genome composition in this corpus, and the metal-type diversity–niche-breadth relationship is among the strongest environment–function links identified.

[AMR Resistome](../topics/amr-resistome.md) connects because the clinical-versus-environmental AMR contrast is fundamentally a biogeographic question: AMR gene accumulation and core-ness differ by habitat, and genome database biases make that comparison technically difficult.

[Metabolic Pathways](../topics/metabolic-pathways.md) is adjacent because pathway completeness varies systematically across ecosystem types, carbon utilization defines the primary metabolic axis of ecosystem differentiation, and GapMind completeness scores connect to both metabolomics and environmental context.

[Gene Fitness](../topics/gene-fitness.md) connects because lab-measured fitness phenotypes are explicitly compared to field environmental distributions, and the core burden paradox — where energetically costly genes are conserved because lab conditions do not capture natural niches — is fundamentally a biogeographic argument about the mismatch between laboratory and field environments.

[Subsurface Genomics](../topics/subsurface-genomics.md) is a narrower slice of environment-biogeography focused on deep subsurface and clay-confined systems, directly downstream of the plume ecology work here.

[Pangenome Architecture](../topics/pangenome-architecture.md) is adjacent because open pangenomes are hypothesized to enable ecological adaptation [\[66\]](#references), and the structural diversity of pangenomes is predicted to correlate with AlphaEarth ecological diversity [\[67\]](#references).

[Functional Dark Matter](../topics/functional-dark-matter.md) connects because biogeographic enrichment analysis is one of the key tools used to infer likely functions for uncharacterized genes.

[Mobile Genetic Elements](../topics/mobile-genetic-elements.md) is adjacent because T4SS conjugative machinery and mobilome burden are environment-enriched in rhizosphere and marine sediment biomes, linking horizontal gene transfer rates to biogeographic structure.

[Microbiome Engineering](../topics/microbiome-engineering.md) connects because engineered community design — for example, selecting lung-adapted anchor species for a CF airway formulation — relies on knowing which organisms are adapted to which environments [\[68\]](#references).

## Caveats and Open Directions

Several caveats run through nearly every analysis on this page. The most pervasive is **database composition bias**: NCBI and public archives over-represent clinical pathogens, AlphaEarth covers only 28.4% of genomes with an additional 38% human-associated bias [\[69\]](#references), and clinical species with well-characterized environmental metadata are the minority. This means that statistical tests of environment–genome relationships are systematically underpowered for environmental microbes and confounded by clinical over-representation [\[70\]](#references) [\[44\]](#references).

A second major caveat is **missing environmental metadata**. Abiotic features (pH, temperature, organic carbon) were entirely absent for many analysis cohorts [\[71\]](#references), and the abiotic_features table was all zeros for Harvard Forest warming samples in the NMDC lakehouse [\[72\]](#references). Roughly 30% of publicly archived metagenomic samples lack valid GPS coordinates [\[45\]](#references), and even the coordinate quality-control used to detect institutional addresses is acknowledged as crude, mislabelling real field sites [\[73\]](#references).

**Confounding and causation** are recurring concerns. Co-contamination by co-varying metals in industrial soils means that COG–metal associations may reflect a generic multi-stress response rather than metal-specific adaptation [\[74\]](#references). Spatial autocorrelation in soil samples has not been corrected in all analyses [\[75\]](#references). The cross-sectional design of metal-niche-breadth analyses means direction cannot be established — broad niches may select for multi-metal resistance, or vice versa [\[76\]](#references). PHB niche-breadth enrichment largely disappears after controlling for genome size (partial rho = −0.047), suggesting it may be a confounded artefact [\[77\]](#references).

**Open directions** identified across projects include: loading SSO geochemistry into CORAL to directly confirm the plume model [\[78\]](#references); extending metabolomics to freshwater NMDC samples to test whether Black Queen dynamics operate in aquatic communities [\[79\]](#references); re-running ecotype analysis restricted to environmental-only samples to test whether a stronger environment–gene-content signal emerges [\[80\]](#references); recruiting larger REE-impacted metagenome collections to convert descriptive enrichment signals into inferential tests [\[81\]](#references); and computing Moran's I on clay-model residuals to test whether the clay-shield null result survives spatial autocorrelation correction [\[82\]](#references).

Metal-resistance hotspot results remain provisional until sampling-effort normalisation is complete, since apparent hotspots may reflect sequencing effort in Europe, the USA, and East Asia rather than true biological enrichment [\[83\]](#references). Similarly, the alkaline-soil sampling gap in public genomic datasets [\[84\]](#references) implies that any study drawing functional inferences from genome reference databases in forest and cropland biomes inherits a systematic pH bias whose magnitude has not yet been fully quantified [\[85\]](#references).

## References

1. [Phb Granule Ecology](../projects/phb-granule-ecology.md) — REPORT.md › "Finding 2: PHB is enriched in environmentally variable habitats (H1a supported)".
2. [Phb Granule Ecology](../projects/phb-granule-ecology.md) — REPORT.md › "Finding 3: PHB-niche breadth association is largely explained by genome size (H1b qualified)".
3. [Phb Granule Ecology](../projects/phb-granule-ecology.md) — REPORT.md › "Finding 6: NMDC metagenomic cross-validation supports pangenome PHB patterns (H1c supported)".
4. [Prophage Ecology](../projects/prophage-ecology.md) — REPORT.md › "2. Environment explains more variance in prophage composition than host phylogeny".
5. [Prophage Ecology](../projects/prophage-ecology.md) — REPORT.md › "2. Environment explains more variance in prophage composition than host phylogeny".
6. [Prophage Ecology](../projects/prophage-ecology.md) — REPORT.md › "NMDC Cross-Validation (NB05)".
7. [Prophage Ecology](../projects/prophage-ecology.md) — REPORT.md › "5. NMDC metagenomic data independently validates module-level environmental signal".
8. [Soil Metal Functional Genomics](../projects/soil-metal-functional-genomics.md) — REPORT.md › "Key Findings".
9. [Soil Metal Functional Genomics](../projects/soil-metal-functional-genomics.md) — REPORT.md › "Key Findings".
10. [Soil Metal Functional Genomics](../projects/soil-metal-functional-genomics.md) — REPORT.md › "Key Findings".
11. [Pangenome Pathway Geography](../projects/pangenome-pathway-geography.md) — REVIEW.md › "Findings Assessment".
12. [Pangenome Pathway Geography](../projects/pangenome-pathway-geography.md) — REVIEW.md › "Findings Assessment".
13. [Amr Pangenome Atlas](../projects/amr-pangenome-atlas.md) — REPORT.md › "5. Clinical Species Carry 2.7x More AMR — and It's More Acquired".
14. [Microbeatlas Metal Ecology](../projects/microbeatlas-metal-ecology.md) — REPORT.md › "Finding 1: Bacterial niche breadth is moderately phylogenetically conserved; metal type diversity predicts it beyond phylogeny".
15. [Microbeatlas Metal Ecology](../projects/microbeatlas-metal-ecology.md) — REPORT.md › "R6. Three-covariate PGLS: metal types independent of both species richness and genome size".
16. [Microbeatlas Metal Ecology](../projects/microbeatlas-metal-ecology.md) — REPORT.md › "Biological meaning of the metal type effect".
17. [Microbeatlas Metal Ecology](../projects/microbeatlas-metal-ecology.md) — REPORT.md › "Results: Track A (BERDL groundwater)".
18. [Microbeatlas Metal Ecology](../projects/microbeatlas-metal-ecology.md) — REPORT.md › "Finding 1: Bacterial niche breadth is moderately phylogenetically conserved; metal type diversity predicts it beyond phylogeny".
19. [Nmdc Community Metabolic Ecology](../projects/nmdc-community-metabolic-ecology.md) — REPORT.md › "Finding 2 — Community metabolic potential separates strongly by ecosystem type".
20. [Nmdc Community Metabolic Ecology](../projects/nmdc-community-metabolic-ecology.md) — REPORT.md › "H2: Ecosystem Metabolic Niche".
21. [Nmdc Community Metabolic Ecology](../projects/nmdc-community-metabolic-ecology.md) — REPORT.md › "Finding 3 — Amino acid pathway completeness differs across ecosystem types for 17 of 18 pathways".
22. [Pseudomonas Carbon Ecology](../projects/pseudomonas-carbon-ecology.md) — REPORT.md › "Finding 2: Carbon Pathway Profiles Distinguish Environment Types Among Free-Living Species".
23. [Pseudomonas Carbon Ecology](../projects/pseudomonas-carbon-ecology.md) — REPORT.md › "Finding 2: Carbon Pathway Profiles Distinguish Environment Types Among Free-Living Species".
24. [Env Embedding Explorer](../projects/env-embedding-explorer.md) — REPORT.md › "2. AlphaEarth embeddings encode real geographic signal — not noise".
25. [Env Embedding Explorer](../projects/env-embedding-explorer.md) — REPORT.md › "1. Environmental samples show 3.4x stronger geographic signal than human-associated samples".
26. [Env Embedding Explorer](../projects/env-embedding-explorer.md) — REPORT.md › "5. UMAP reveals fine-grained embedding structure with environment-correlated clusters".
27. [Pangenome Pathway Geography](../projects/pangenome-pathway-geography.md) — REVIEW.md › "Findings Assessment".
28. [Enigma Sso Asv Ecology](../projects/enigma-sso-asv-ecology.md) — REPORT.md › "Novel Contribution".
29. [Enigma Sso Asv Ecology](../projects/enigma-sso-asv-ecology.md) — REPORT.md › "2. The Column 3 Corridor: A Plume Flow Path".
30. [Enigma Sso Asv Ecology](../projects/enigma-sso-asv-ecology.md) — REPORT.md › "1. Community Similarity Tracks Spatial Arrangement at Meter Scale".
31. [Lanthanide Methylotrophy Atlas](../projects/lanthanide-methylotrophy-atlas.md) — REPORT.md › "4. Soil/sediment is the strongest environmental enrichment; REE-impacted sites are descriptively elevated".
32. [Lanthanide Methylotrophy Atlas](../projects/lanthanide-methylotrophy-atlas.md) — REPORT.md › "4. Soil/sediment is the strongest environmental enrichment; REE-impacted sites are descriptively elevated".
33. [Pgp Pangenome Ecology](../projects/pgp-pangenome-ecology.md) — REPORT.md › "H2 SUPPORTED — Soil/rhizosphere environment strongly selects for acdS and pqqC, but not nifH".
34. [Plant Microbiome Ecotypes](../projects/plant-microbiome-ecotypes.md) — REPORT.md › "1. Plant compartments impose a small but real functional shift on microbial communities (H1, weakly supported)".
35. [Plant Microbiome Ecotypes](../projects/plant-microbiome-ecotypes.md) — REPORT.md › "9. MGnify cross-validation reveals mobilome enrichment but low classification concordance (H4, H6)".
36. [T4Ss Cazy Environmental Hgt](../projects/t4ss-cazy-environmental-hgt.md) — REPORT.md › "Key Findings".
37. [T4Ss Cazy Environmental Hgt](../projects/t4ss-cazy-environmental-hgt.md) — REPORT.md › "Key Findings".
38. [Functional Dark Matter](../projects/functional-dark-matter.md) — REPORT.md › "Finding 6: Within-species biogeographic analysis reveals 10 dark gene clusters with significant environmental enrichment".
39. [Amr Pangenome Atlas](../projects/amr-pangenome-atlas.md) — REPORT.md › "5. Clinical Species Carry 2.7x More AMR — and It's More Acquired".
40. [Amr Environmental Resistome](../projects/amr-environmental-resistome.md) — REPORT.md › "6. AlphaEarth continuous environment embeddings confirm discrete findings (supplementary)".
41. [Bacdive Metal Validation](../projects/bacdive-metal-validation.md) — REPORT.md › "1. Bacteria From Metal-Contaminated Environments Have Significantly Higher Metal Tolerance Scores".
42. [Bacdive Metal Validation](../projects/bacdive-metal-validation.md) — REPORT.md › "1. Bacteria From Metal-Contaminated Environments Have Significantly Higher Metal Tolerance Scores".
43. [Env Embedding Explorer](../projects/env-embedding-explorer.md) — REPORT.md › "Data coverage".
44. [Env Embedding Explorer](../projects/env-embedding-explorer.md) — REPORT.md › "3. Strong clinical/human sampling bias in the AlphaEarth subset".
45. [Metal Resistance Global Biogeography](../projects/metal-resistance-global-biogeography.md) — REPORT.md › "Interpretation".
46. [Soil Frontier Genomics](../projects/soil-frontier-genomics.md) — README.md › "Genomic Discovery Index (GDI)".
47. [Soil Frontier Genomics](../projects/soil-frontier-genomics.md) — README.md › "Genomic Discovery Index (GDI)".
48. [Enigma Sso Asv Ecology](../projects/enigma-sso-asv-ecology.md) — REPORT.md › "The Contamination Plume Model".
49. [Enigma Sso Asv Ecology](../projects/enigma-sso-asv-ecology.md) — REPORT.md › "7. Groundwater Community Stability Over 9 Days".
50. [Enigma Sso Asv Ecology](../projects/enigma-sso-asv-ecology.md) — REPORT.md › "5. Groundwater Carries a Plume-Associated Planktonic Community".
51. [Lab Field Ecology](../projects/lab-field-ecology.md) — REPORT.md › "Novel Contribution".
52. [Lab Field Ecology](../projects/lab-field-ecology.md) — REPORT.md › "Why Lab Fitness Doesn't Simply Predict Field Ecology".
53. [Metal Resistance Global Biogeography](../projects/metal-resistance-global-biogeography.md) — REPORT.md › "NB02 Spatial Analysis Results".
54. [Metal Resistance Global Biogeography](../projects/metal-resistance-global-biogeography.md) — REPORT.md › "NB02 Spatial Analysis Results".
55. [Microbeatlas Metal Ecology](../projects/microbeatlas-metal-ecology.md) — REPORT.md › "Novel contribution".
56. [Env Embedding Explorer](../projects/env-embedding-explorer.md) — REPORT.md › "Environment harmonization".
57. [Env Embedding Explorer](../projects/env-embedding-explorer.md) — REPORT.md › "4. 36% of coordinates flagged as potential institutional addresses".
58. [Nmdc Community Metabolic Ecology](../projects/nmdc-community-metabolic-ecology.md) — REPORT.md › "Novel Contribution".
59. [Soil Metal Functional Genomics](../projects/soil-metal-functional-genomics.md) — REPORT.md › "Interpretation".
60. [Soil Frontier Genomics](../projects/soil-frontier-genomics.md) — README.md › "Clay Shield Hypothesis — Null Result".
61. [Soil Frontier Genomics](../projects/soil-frontier-genomics.md) — REPORT.md › "Key Findings".
62. [Harvard Forest Warming](../projects/harvard-forest-warming.md) — REPORT.md › "Summary".
63. [Harvard Forest Warming](../projects/harvard-forest-warming.md) — REPORT.md › "5. H3 is supported compositionally — most warming responses are horizon-specific".
64. [Ecotype Env Reanalysis](../projects/ecotype-env-reanalysis.md) — REPORT.md › "1. Clinical bias does NOT explain the weak environment signal (H0 not rejected)".
65. [Ecotype Env Reanalysis](../projects/ecotype-env-reanalysis.md) — REPORT.md › "1. Clinical bias does NOT explain the weak environment signal (H0 not rejected)".
66. [Pangenome Pathway Geography](../projects/pangenome-pathway-geography.md) — REVIEW.md › "Findings Assessment".
67. [Pangenome Pathway Ecology](../projects/pangenome-pathway-ecology.md) — RESEARCH_PLAN.md › "Phase 3: Structural Distance Analysis".
68. [Cf Formulation Design](../projects/cf-formulation-design.md) — REPORT.md › "Summary".
69. [Env Embedding Explorer](../projects/env-embedding-explorer.md) — REPORT.md › "Limitations".
70. [Amr Strain Variation](../projects/amr-strain-variation.md) — REPORT.md › "Finding 4: One in five species has distinct AMR ecotypes".
71. [Nmdc Community Metabolic Ecology](../projects/nmdc-community-metabolic-ecology.md) — REPORT.md › "Limitations".
72. [Harvard Forest Warming](../projects/harvard-forest-warming.md) — REPORT.md › "Limitations".
73. [Env Embedding Explorer](../projects/env-embedding-explorer.md) — REPORT.md › "Limitations".
74. [Soil Metal Functional Genomics](../projects/soil-metal-functional-genomics.md) — REPORT.md › "Interpretation".
75. [Soil Metal Functional Genomics](../projects/soil-metal-functional-genomics.md) — README.md › "NB05 — Validation Analyses".
76. [Microbeatlas Metal Ecology](../projects/microbeatlas-metal-ecology.md) — REPORT.md › "Causation and directionality".
77. [Phb Granule Ecology](../projects/phb-granule-ecology.md) — REPORT.md › "Finding 3: PHB-niche breadth association is largely explained by genome size (H1b qualified)".
78. [Enigma Sso Asv Ecology](../projects/enigma-sso-asv-ecology.md) — REPORT.md › "Future Directions".
79. [Nmdc Community Metabolic Ecology](../projects/nmdc-community-metabolic-ecology.md) — REPORT.md › "Future Directions".
80. [Env Embedding Explorer](../projects/env-embedding-explorer.md) — REPORT.md › "Future Directions".
81. [Lanthanide Methylotrophy Atlas](../projects/lanthanide-methylotrophy-atlas.md) — REPORT.md › "Future Directions".
82. [Soil Frontier Genomics](../projects/soil-frontier-genomics.md) — README.md › "NB05 — Validation Analyses".
83. [Metal Resistance Global Biogeography](../projects/metal-resistance-global-biogeography.md) — README.md › "Reproduction".
84. [Soil Frontier Genomics](../projects/soil-frontier-genomics.md) — REPORT.md › "Interpretation".
85. [Soil Frontier Genomics](../projects/soil-frontier-genomics.md) — REPORT.md › "Critical Assessment".

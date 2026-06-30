# Microbial Ecotypes

Microbial ecotypes are genetically distinct subpopulations within a single microbial species that have become adapted to particular ecological niches — different carbon sources, redox regimes, host compartments, or geographic environments. Unlike the classic species concept, ecotypes blur into one another; they are best detected by clustering gene-content or resistome profiles across many genomes rather than by any single phenotype. This page synthesizes evidence from 47 BERIL projects that, collectively, investigated whether and how the environment shapes microbial gene repertoires within species boundaries, which methods detect that signal most reliably, and where the signal breaks down.

## Overview

A microbial ecotype is operationally defined here as a reproducible cluster of conspecific genomes that share a recognizable metabolic or resistance profile that correlates, however weakly, with where those organisms were isolated. The concept spans scales: within *Pseudomonas*, ecotypes correspond to entire subgenera separated by hundreds of metabolic pathway differences [\[1\]](#references); within a single pathogen species such as *Klebsiella* or *Acinetobacter baumannii*, ecotypes can be as subtle as a distinctive resistome cluster [\[2\]](#references); and in the human gut microbiome the same IBD patient's community can shift between ecotypes between clinical visits [\[3\]](#references).

Two complementary forces shape ecotypes. Phylogeny — the evolutionary history of a lineage — explains the bulk of whole-genome gene-content similarity in most bacterial species [\[4\]](#references). Environment adds a secondary signal that is real but modest: metabolic clustering into ecotypes is a widespread, near-universal feature of bacteria with large enough genome collections [\[5\]](#references), yet the environment explains only a fraction of that variation once phylogeny is controlled for [\[6\]](#references).

Pangenome architecture links the two forces. Open pangenomes — species whose accessory gene pool grows with each new sequenced isolate — correlate with broader ecological niche breadth and higher numbers of within-species metabolic ecotypes [\[7\]](#references) [\[8\]](#references). Accessory genes are the substrate on which ecotype-forming selection acts, enabling metabolic heterogeneity across environments [\[9\]](#references). The [Pangenome Architecture](pangenome-architecture.md) page develops the structural side of this story in more detail.

## What the Corpus Shows

### Ecotype structure is real and widespread

Within-species metabolic clustering is detectable in all 10 target species examined with at least 50 genomes and 15 variable pathways, with silhouette scores above 0.2 in every case [\[5\]](#references). A median of four metabolic ecotypes per species is observed, ranging up to eight, and ecotype count correlates with pangenome openness after controlling for genome count (partial Spearman rho = 0.322, p = 8.0e-07) [\[8\]](#references).

In the resistome domain, roughly one in five bacterial species (19.5% of 974 species with sufficient genomes) forms two or more distinct AMR ecotypes by UMAP plus DBSCAN clustering, with good cluster quality (median silhouette 0.620) [\[2\]](#references). AMR profiles are not randomly distributed across phylogeny: 55.6% of species show significant phylogenetic signal in their AMR repertoire by Mantel test [\[10\]](#references), reinforcing the point that ecotype structure and phylogenetic structure overlap considerably. The [AMR Resistome](amr-resistome.md) page covers the resistance gene side of this in depth.

Gene-content ecotypes are functionally structured rather than random: COG (Clusters of Orthologous Groups) categories — a standard functional classification system — differentiate significantly across ecotypes in all sampled species [\[11\]](#references). Adaptive functions differentiate more strongly between ecotypes than housekeeping functions, although both classes can vary [\[12\]](#references). Within accessory dark genes (those with no known function), ten gene clusters show significant environmental enrichment, including *Pseudomonas putida* stress and nitrogen genes enriched in clinical isolates and *P. syringae* genes enriched in plant-associated genomes [\[13\]](#references).

### The environment signal is real but modest

Ecological niche is a strong predictor of resistome size: clinical and human gut species carry roughly 2.5 times more AMR gene clusters (median 5) than soil, aquatic, and other host-associated species (median 2) [\[14\]](#references). Different niches select for fundamentally different resistance strategies — target modification dominates in human gut (44%) and clinical (28%) species but reaches only 6% in aquatic bacteria [\[15\]](#references). Importantly, this environment–AMR relationship survives phylogenetic control: 20 of 141 testable bacterial families show significant within-family environment effects, demonstrating the signal is not simply a proxy for phylogeny [\[16\]](#references).

For metabolic pathways, carbon profiles across 54 free-living and plant-associated *Pseudomonas* species are significantly associated with isolation environment (permutation p = 0.006) [\[17\]](#references), and free-living species maintain higher carbon pathway richness than host-associated species [\[18\]](#references). Within the Pseudomonas genus, host-associated *P. aeruginosa* shows near-complete loss of plant-derived sugar catabolism relative to the environmental *Pseudomonas\_E* subgenus (Pseudomonas fluorescens group), with 43 of 62 GapMind carbon pathways differing significantly [\[19\]](#references). A random forest classifier trained on carbon pathway profiles achieved balanced accuracy of 0.408 above a 0.25 chance baseline, confirming a modest but real predictive signal [\[20\]](#references).

In soil communities warming by +5°C for 25 years, the signal is detectable but modest: Actinobacteria increase while Acidobacteria decrease, with roughly 39% of metabolic genes showing horizon-specific responses [\[21\]](#references) [\[22\]](#references). Metal resistance follows niche even more cleanly: soil biomes are enriched 5-fold for metal resistance genes while marine MAGs are 5-fold depleted [\[23\]](#references), and biome-stratified phylogenetic regression confirms that soil, marine, and wastewater communities have distinct metal-COG relationships [\[24\]](#references). The [Metal Resistance](metal-resistance.md) page explores the biogeography of resistance genes across these biomes.

### Phylogeny dominates gene content, environment adds a secondary layer

Across species with sufficient data, phylogenetic relatedness generally predicts bacterial gene-content similarity more strongly than environmental similarity [\[4\]](#references). A continuous Spearman analysis confirmed that the fraction of environmental genomes per species does not predict partial-correlation strength (rho = -0.085, p = 0.25) [\[25\]](#references). Restricting the ecotype analysis to environmental species did not yield stronger environment–gene-content correlations than human-associated species (Mann-Whitney U p = 0.83) [\[26\]](#references), and a genome-level classification harmonized by isolation source reproduced this null (p = 0.83 vs original p = 0.66) [\[27\]](#references).

Classical phenotypes — such as those captured in the BacDive database for metal tolerance — add no predictive power beyond taxonomy, with a combined taxonomy-plus-phenotype model performing slightly worse than taxonomy alone [\[28\]](#references). Metal tolerance differences between strains are real but are entirely explained by phylogenetic structure, making phenotypes noisier proxies for taxonomy rather than independent predictors [\[29\]](#references).

### Environment-specific niche markers emerge at broader scales

At the biome and sub-species level, niche-specific gene enrichments are detectable. Plant-microbiome analysis identified 50 eggNOG ortholog groups (ortholog groups are families of evolutionarily related genes across species) that are significantly enriched in plant-associated bacteria after phylum-level phylogenetic control, including COG3569 at a phylo-controlled odds ratio of 6.01 [\[30\]](#references). The type III secretion system (T3SS) — a molecular syringe used by bacteria to inject proteins into host cells — is 2x more prevalent in rhizosphere biomes (21.6–24.0%) than bulk soil (12.3%), confirming it as a marker of plant association [\[31\]](#references).

In the subsurface, depth zones override horizontal position: PERMANOVA (a permutational multivariate ANOVA used for community comparisons) shows that hydrogeological depth explains 27.5% of sediment community variance while well identity is not significant [\[32\]](#references). Ten of twelve dominant phyla split into shallow-oxic and deep-anoxic groups mirroring the redox gradient [\[33\]](#references), and deep clay-confined isolates are dominated by sulfate-reduction-only profiles while shallow-clay isolates are dominated by iron-reduction-only profiles [\[34\]](#references). The [Subsurface Genomics](subsurface-genomics.md) page treats this spatial stratification in full.

In the IBD gut microbiome, two independent clustering methods applied to 8,489 metagenomic samples converge on four reproducible ecotypes (E0–E3) [\[35\]](#references). The canonical Crohn's disease (CD) signature — pathobionts enriched, protective commensals depleted — is recoverable with strong sign concordance across four independent cohorts [\[36\]](#references). Clinical covariates can separate healthy from IBD samples but cannot discriminate between transitional (E1) and severe (E3) ecotypes, so metagenomics remains necessary for ecotype assignment [\[37\]](#references). This is adjacent to [Microbiome Engineering](microbiome-engineering.md), which covers therapeutic strategies built on such ecotype definitions.

## Projects and Evidence

The core ecotype work is distributed across several dedicated projects. The **ecotype\_analysis** project established that phylogeny dominates gene-content similarity across species [\[4\]](#references) and that environmental lifestyle separation did not improve the environment signal [\[38\]](#references). The **ecotype\_env\_reanalysis** project then reanalysed this question with genome-level isolation-source classification, reproducing the null and adding findings about clinical sampling bias (47% of genomes in the AlphaEarth subset are majority human-associated, only 21% majority environmental) [\[39\]](#references). It also found that the embedding-based environment variable (AlphaEarth, a foundation model for environment similarity) may capture climate and land use rather than bacterial gene content drivers, limiting its utility here [\[40\]](#references). The **ecotype\_functional\_differentiation** project confirmed that within-species ecotypes are widespread [\[41\]](#references) and that their gene-content differences are functionally structured [\[11\]](#references).

The **metabolic\_capability\_dependency** project contributed the strongest positive evidence: metabolic ecotypes are a general feature across ten sampled species [\[5\]](#references), and they correlate with isolation environment in copiotrophs (nutrient-rich-environment specialists) such as *Salmonella enterica* and *Phenylobacterium* sp. but not in marine oligotrophs such as *Stutzerimonas* and *Alteromonas* [\[42\]](#references).

The **pseudomonas\_carbon\_ecology** project focused specifically on carbon metabolism within *Pseudomonas*, finding that the primary split between *P. aeruginosa* and *Pseudomonas\_E* (the fluorescens group) accounts for the dominant signal — a deep lineage-level difference rather than a lifestyle adaptation [\[1\]](#references). Much of the pathway loss in *P. aeruginosa* reflects ancestral metabolic streamlining of the lineage itself, predating infection, since the sugar-catabolism pathways were already absent across thousands of isolates at the species level [\[43\]](#references).

The **amr\_strain\_variation** and **amr\_environmental\_resistome** projects documented ecotype structure in the resistome: clinical species carry the most AMR clusters, niche selects for mechanism type, and AMR ecotypes are detectable in one in five species [\[14\]](#references) [\[2\]](#references). The [Gene Fitness](gene-fitness.md) page describes fitness-level evidence from pooled transposon screens that complements the genome-level ecotype view.

The **plant\_microbiome\_ecotypes** project characterised which plant-associated genes are genuinely ecotype-specific versus artifacts of genome-rich clades [\[30\]](#references) and showed that the headline PERMANOVA compartment effect (R2 = 0.527) collapsed to R2 = 0.072 after excluding a handful of genome-rich clades [\[44\]](#references), an important cautionary finding for community ecotype studies.

The **ibd\_phage\_targeting** project framed IBD ecotypes as actionable: patient-specific ecotype determines which phage cocktail composition is optimal, and a single patient can shift between E1 and E3 between visits (cocktail Jaccard similarity 0.60) [\[3\]](#references), motivating state-dependent rather than fixed-prescription phage therapy [\[45\]](#references).

## Connections

Several adjacent topics emerge naturally from ecotype biology. [Pangenome Architecture](pangenome-architecture.md) is the structural foundation: high core-genome fraction correlates negatively with ecological niche breadth (r = -0.445, p = 1.4e-91) [\[46\]](#references), and pangenome openness, while not predicting the drivers of gene-content variation, does correlate with niche breadth and ecotype count. Importantly, whether a species has an open or closed pangenome does not predict whether environment or phylogeny dominates its gene-content variation [\[47\]](#references), and pangenome openness shows no significant correlation with either environmental or phylogenetic effect sizes (environment rho = -0.05, p = 0.54; phylogeny rho = 0.03, p = 0.73) [\[48\]](#references).

[Environment Biogeography](environment-biogeography.md) is adjacent because ecotype assignment depends on environmental metadata: AlphaEarth embeddings of isolation environments reveal substantial UMAP cluster structure (320 DBSCAN clusters, many dominated by a single environment type) [\[49\]](#references), and 52.7% of genomes in the ecotype analysis lack a classifiable isolation source, leaving the environment signal underpowered [\[50\]](#references).

[Functional Dark Matter](functional-dark-matter.md) is adjacent because a disproportionate share of the ecotype-specific gene signal falls in unknown-function and mobile-element categories, making the niche-specific component hard to interpret biologically [\[51\]](#references), and dark accessory gene clusters are among the best candidates for habitat-specific function [\[13\]](#references).

[Metabolic Pathways](metabolic-pathways.md) is the direct mechanistic substrate: metabolic ecotypes are defined by binary pathway profiles, and within-species pathway heterogeneity is the phenotype through which environment-specific selection is most clearly expressed [\[5\]](#references).

[Mobile Genetic Elements](mobile-genetic-elements.md) are relevant because horizontal gene transfer (HGT) is a primary mechanism for distributing niche-specific genes across ecotypes, yet the clade restriction of some innovations (e.g., lanmodulin confined to three methylotroph families) shows that HGT is not universal [\[52\]](#references).

AMR resistance ecotypes connect to [AMR Resistome](amr-resistome.md): AMR support networks are organism-specific rather than mechanism-specific, meaning the same resistance mechanism (beta-lactamase, efflux pump) is embedded in different gene-regulatory contexts in different organisms [\[53\]](#references).

## Caveats and Open Directions

Several important caveats limit current conclusions.

**Phylogenetic confounding is pervasive.** The dominant signal in most comparisons separates subgenera or lineages rather than lifestyles. Within *Pseudomonas\_E*, lifestyle-associated differences are subtle, and analyses generally do not apply full phylogenetic independent contrasts [\[54\]](#references). Metabolic ecotype correlations were controlled only for genome count and taxonomic grouping, so metabolic ecotypes may partly reflect intra-species phylogenetic structure [\[55\]](#references). Phylum-level confounding is only partially resolved for metal tolerance: the signal holds within Pseudomonadota and Actinomycetota but is absent in Bacillota and Bacteroidota [\[56\]](#references).

**Sampling biases are severe.** Genome databases are dominated by pathogens and model organisms — the top 100 bacterial organisms capture 44.3% of the literature [\[57\]](#references) — creating a strong clinical sampling bias that dilutes environment-gene-content associations [\[39\]](#references). Niche breadth estimates from sequencing effort are proxies, not confirmed ecological ranges, and genus-level aggregation in 16S surveys can make a genus appear broadly niched because different species occupy different habitats [\[58\]](#references). Taxonomy tables resolved only to genus level make species- or strain-level bridge testing impossible [\[59\]](#references).

**Effect sizes are modest.** Environment explains only 2–13% of variance in AMR composition [\[6\]](#references). Pangenome openness and effects are near-zero correlated [\[48\]](#references). The ecotype-analysis partial correlations in one reanalysis were 27 times higher than the original (0.081 vs 0.003) due to the absence of downsampling, so absolute magnitudes across studies are not directly comparable [\[60\]](#references).

**Key taxa are missing.** *Klebsiella pneumoniae* was excluded from the ecotype reanalysis because it exceeded compute limits [\[61\]](#references). The most phylogenetically diverse *Ralstonia* organisms have no co-fitness data [\[62\]](#references). Only 18 of 65 plant-associated species with sufficient genomes have phylogenetic-tree distance data, leaving major taxa such as *Bradyrhizobium japonicum* absent [\[63\]](#references).

**Open directions.** Environment may act on specific functional gene categories (transport, secondary metabolism) rather than whole-genome Jaccard distance, motivating targeted gene-subset tests [\[64\]](#references). Repeating the ecotype classification with structured ENVO ontology terms from the env\_broad\_scale field may classify environments more accurately than keyword-based harmonization [\[65\]](#references). Re-running ecotype analysis restricted to environmental-only samples could reveal a stronger environment–gene-content signal where embeddings carry more geographic information [\[66\]](#references). AMR ecotypes could be integrated with virulence factor profiles and metabolic pathway variation from other BERIL analyses to connect resistance structure to broader strain phenotypes [\[67\]](#references). Correlating metabolic ecotypes with AlphaEarth environmental niche breadth was planned but not executed, constrained by AlphaEarth covering only 28% of genomes [\[68\]](#references).

## References

1. [Pseudomonas Carbon Ecology](../projects/pseudomonas-carbon-ecology.md) — REPORT.md › "Finding 4: The Aeruginosa-Fluorescens Split Dominates Carbon Pathway Variation".
2. [Amr Strain Variation](../projects/amr-strain-variation.md) — REPORT.md › "Finding 4: One in five species has distinct AMR ecotypes".
3. [Ibd Phage Targeting](../projects/ibd-phage-targeting.md) — REPORT.md › "NB16 — Patient 6967 longitudinal stability + state-dependent dosing strategy".
4. [Ecotype Analysis](../projects/ecotype-analysis.md) — REPORT.md › "Phylogeny Usually Dominates".
5. [Metabolic Capability Dependency](../projects/metabolic-capability-dependency.md) — REPORT.md › "H3 Supported: All Target Species Show Distinct Metabolic Ecotypes".
6. [Amr Environmental Resistome](../projects/amr-environmental-resistome.md) — REPORT.md › "Limitations".
7. [Pangenome Pathway Geography](../projects/pangenome-pathway-geography.md) — REVIEW.md › "Findings Assessment".
8. [Pathway Capability Dependency](../projects/pathway-capability-dependency.md) — REPORT.md › "6. Metabolic Ecotypes Correlate with Pangenome Openness".
9. [Pangenome Pathway Geography](../projects/pangenome-pathway-geography.md) — REVIEW.md › "Findings Assessment".
10. [Amr Strain Variation](../projects/amr-strain-variation.md) — REPORT.md › "Finding 3: AMR variation tracks phylogeny in the majority of species — but acquired genes show stronger signal than intrinsic".
11. [Ecotype Functional Differentiation](../projects/ecotype-functional-differentiation.md) — REPORT.md › "Ecotypes show pervasive COG functional differentiation".
12. [Ecotype Functional Differentiation](../projects/ecotype-functional-differentiation.md) — REPORT.md › "Adaptive COG categories show significantly larger effect sizes than housekeeping".
13. [Functional Dark Matter](../projects/functional-dark-matter.md) — REPORT.md › "Finding 6: Within-species biogeographic analysis reveals 10 dark gene clusters with significant environmental enrichment".
14. [Amr Environmental Resistome](../projects/amr-environmental-resistome.md) — REPORT.md › "1. Clinical species carry 2.5× more AMR gene clusters than environmental species (H1 supported)".
15. [Amr Environmental Resistome](../projects/amr-environmental-resistome.md) — REPORT.md › "3. Resistance mechanism composition is strongly environment-dependent (H3 supported)".
16. [Amr Environmental Resistome](../projects/amr-environmental-resistome.md) — REPORT.md › "5. Phylogenetic control confirms environment effects are real".
17. [Pseudomonas Carbon Ecology](../projects/pseudomonas-carbon-ecology.md) — REPORT.md › "Finding 2: Carbon Pathway Profiles Distinguish Environment Types Among Free-Living Species".
18. [Pseudomonas Carbon Ecology](../projects/pseudomonas-carbon-ecology.md) — REPORT.md › "Finding 3: Free-Living Species Have Greater Pathway Richness Than Host-Associated Species".
19. [Pseudomonas Carbon Ecology](../projects/pseudomonas-carbon-ecology.md) — REPORT.md › "Finding 1: Host-Associated Pseudomonas Show Dramatic Loss of Plant-Derived Sugar Pathways".
20. [Pseudomonas Carbon Ecology](../projects/pseudomonas-carbon-ecology.md) — REPORT.md › "Finding 2: Carbon Pathway Profiles Distinguish Environment Types Among Free-Living Species".
21. [Harvard Forest Warming](../projects/harvard-forest-warming.md) — REPORT.md › "Summary".
22. [Harvard Forest Warming](../projects/harvard-forest-warming.md) — REPORT.md › "5. H3 is supported compositionally — most warming responses are horizon-specific".
23. [Metal Resistance Global Biogeography](../projects/metal-resistance-global-biogeography.md) — REPORT.md › "NB02 Spatial Analysis Results".
24. [Soil Metal Functional Genomics](../projects/soil-metal-functional-genomics.md) — REPORT.md › "Key Findings".
25. [Ecotype Env Reanalysis](../projects/ecotype-env-reanalysis.md) — REPORT.md › "1. Clinical bias does NOT explain the weak environment signal (H0 not rejected)".
26. [Ecotype Env Reanalysis](../projects/ecotype-env-reanalysis.md) — REPORT.md › "1. Clinical bias does NOT explain the weak environment signal (H0 not rejected)".
27. [Ecotype Env Reanalysis](../projects/ecotype-env-reanalysis.md) — REPORT.md › "Literature Context".
28. [Bacdive Phenotype Metal Tolerance](../projects/bacdive-phenotype-metal-tolerance.md) — REPORT.md › "3. Phenotype Features Add Nothing Beyond Taxonomy (Delta R² = -0.009)".
29. [Bacdive Phenotype Metal Tolerance](../projects/bacdive-phenotype-metal-tolerance.md) — REPORT.md › "The Phylogenetic Confounding Wall".
30. [Plant Microbiome Ecotypes](../projects/plant-microbiome-ecotypes.md) — REPORT.md › "5. Fifty novel gene families distinguish plant-associated species (H5)".
31. [Plant Microbiome Ecotypes](../projects/plant-microbiome-ecotypes.md) — REPORT.md › "9. MGnify cross-validation reveals mobilome enrichment but low classification concordance (H4, H6)".
32. [Enigma Sso Asv Ecology](../projects/enigma-sso-asv-ecology.md) — REPORT.md › "3. Depth Dominates Over Horizontal Position".
33. [Enigma Sso Asv Ecology](../projects/enigma-sso-asv-ecology.md) — REPORT.md › "3. Depth Dominates Over Horizontal Position".
34. [Clay Confined Subsurface](../projects/clay-confined-subsurface.md) — REPORT.md › "Finding 1 — Cultured clay-confined genomes carry the Bagnoud Mont Terri porewater signature, not the Mitzscherling rock-attached signature (H3, supported)".
35. [Ibd Phage Targeting](../projects/ibd-phage-targeting.md) — REPORT.md › "Four reproducible IBD ecotypes with clear disease stratification".
36. [Ibd Phage Targeting](../projects/ibd-phage-targeting.md) — REPORT.md › "Within-ecotype × within-substudy meta-analysis defines ecotype-specific Tier-A (rigor-controlled)".
37. [Ibd Phage Targeting](../projects/ibd-phage-targeting.md) — REPORT.md › "Clinical covariates alone are insufficient for within-IBD ecotype assignment".
38. [Ecotype Analysis](../projects/ecotype-analysis.md) — REPORT.md › "No Difference by Lifestyle".
39. [Ecotype Env Reanalysis](../projects/ecotype-env-reanalysis.md) — REPORT.md › "2. 47% of ecotype species are human-associated, only 21% environmental".
40. [Ecotype Env Reanalysis](../projects/ecotype-env-reanalysis.md) — REPORT.md › "Why the hypothesis was wrong".
41. [Ecotype Functional Differentiation](../projects/ecotype-functional-differentiation.md) — REPORT.md › "Gene-content ecotypes are widespread across bacterial species".
42. [Metabolic Capability Dependency](../projects/metabolic-capability-dependency.md) — REPORT.md › "H3 Supported: All Target Species Show Distinct Metabolic Ecotypes".
43. [Pseudomonas Carbon Ecology](../projects/pseudomonas-carbon-ecology.md) — REPORT.md › "Literature Context".
44. [Plant Microbiome Ecotypes](../projects/plant-microbiome-ecotypes.md) — REPORT.md › "1. Plant compartments impose a small but real functional shift on microbial communities (H1, weakly supported)".
45. [Ibd Phage Targeting](../projects/ibd-phage-targeting.md) — REPORT.md › "Executive Summary".
46. [Pangenome Pathway Geography](../projects/pangenome-pathway-geography.md) — REVIEW.md › "Findings Assessment".
47. [Pangenome Openness](../projects/pangenome-openness.md) — REPORT.md › "Interpretation".
48. [Pangenome Openness](../projects/pangenome-openness.md) — REPORT.md › "No Correlation Found".
49. [Env Embedding Explorer](../projects/env-embedding-explorer.md) — REPORT.md › "5. UMAP reveals fine-grained embedding structure with environment-correlated clusters".
50. [Amr Strain Variation](../projects/amr-strain-variation.md) — REPORT.md › "Finding 4: One in five species has distinct AMR ecotypes".
51. [Ecotype Functional Differentiation](../projects/ecotype-functional-differentiation.md) — REPORT.md › "Replication/mobile elements and unknown function drive the largest ecotype differences".
52. [Lanthanide Methylotrophy Atlas](../projects/lanthanide-methylotrophy-atlas.md) — REPORT.md › "3. Lanmodulin clade restriction is total; xoxF co-occurrence falls just short of the 80 % threshold".
53. [Amr Cofitness Networks](../projects/amr-cofitness-networks.md) — REPORT.md › "3. Support networks are organism-specific, not mechanism-specific".
54. [Pseudomonas Carbon Ecology](../projects/pseudomonas-carbon-ecology.md) — REPORT.md › "Limitations".
55. [Pathway Capability Dependency](../projects/pathway-capability-dependency.md) — REPORT.md › "Limitations".
56. [Bacdive Metal Validation](../projects/bacdive-metal-validation.md) — REPORT.md › "2. The Signal Holds Within Major Phyla".
57. [Paperblast Explorer](../projects/paperblast-explorer.md) — REPORT.md › "Finding 4: Bacterial research is concentrated on pathogens".
58. [Microbeatlas Metal Ecology](../projects/microbeatlas-metal-ecology.md) — REPORT.md › "1. Niche breadth is a sequencing-effort proxy, not confirmed ecological range".
59. [Enigma Contamination Functional Potential](../projects/enigma-contamination-functional-potential.md) — REPORT.md › "Limitations".
60. [Ecotype Env Reanalysis](../projects/ecotype-env-reanalysis.md) — REPORT.md › "4. Overall partial correlations are 27x higher than the original analysis".
61. [Ecotype Env Reanalysis](../projects/ecotype-env-reanalysis.md) — REPORT.md › "Limitations".
62. [Cofitness Coinheritance](../projects/cofitness-coinheritance.md) — REPORT.md › "Limitations".
63. [Plant Microbiome Ecotypes](../projects/plant-microbiome-ecotypes.md) — REPORT.md › "10. Within-species subclade analysis shows weak segregation in 5/17 testable species, with two robust pathovar-host specializations (H7 weakly supported, H6 supported)".
64. [Ecotype Env Reanalysis](../projects/ecotype-env-reanalysis.md) — REPORT.md › "Future Directions".
65. [Ecotype Env Reanalysis](../projects/ecotype-env-reanalysis.md) — REPORT.md › "Future Directions".
66. [Env Embedding Explorer](../projects/env-embedding-explorer.md) — REPORT.md › "Future Directions".
67. [Amr Strain Variation](../projects/amr-strain-variation.md) — REPORT.md › "Future Directions".
68. [Pathway Capability Dependency](../projects/pathway-capability-dependency.md) — REPORT.md › "Limitations".

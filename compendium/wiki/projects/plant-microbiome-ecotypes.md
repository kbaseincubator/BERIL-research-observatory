# Plant Microbiome Ecotypes

This project examined how plant-associated bacteria develop specialized functional profiles and genetic architectures to thrive across plant compartments (roots, rhizospheres, shoots). The central finding was that beneficial plant-growth-promoting genes are predominantly core-encoded in plant-associated species while pathogenic genes are accessory, revealing a fundamental genomic strategy that distinguishes ecological roles—a pattern validated by the discovery that 50 novel conserved gene families (especially those for electron transport and iron-sulfur biosynthesis) distinguish plant-associated bacteria across diverse taxa.

## Key findings

- Because 94.2% of tested ortholog groups were significantly plant-associated, the raw enrichment signal mostly reflects genome-wide taxonomic divergence; only the 50 OGs surviving phylogenetic control represent candidate plant-interaction genes. *(confidence: high)*
- Despite frequent transposase association, plant-interaction marker genes as a class are less mobile than the genomic average (singleton enrichment ratio 0.78, Wilcoxon p<1e-300), indicating stronger purifying selection rather than ongoing high mobility. *(confidence: medium)*
- Only 18 of 65 plant-associated species with sufficient genomes have phylogenetic-tree distance data in BERDL, leaving major taxa such as Bradyrhizobium japonicum absent and making the full within-species adaptation effect unestimable. *(confidence: high)*
- The Phase 1 complementarity result of Cohen d=-7.54 was largely a formula error from dividing by the standard deviation of permutation means; the corrected effect size is about -0.4, with the redundancy direction robust under both aggregation methods. *(confidence: high)*
- The dual-nature rate is genome-size-dependent (54% in the smallest genome-size quartile vs 87% in the top three quartiles), so the 78.7% figure masks a real gradient and overstates genuine plant-adapted duality. *(confidence: high)*
- The headline compartment effect (PERMANOVA R2=0.527) was largely a taxonomic-sampling artifact: excluding a handful of genome-rich rhizobial and Pseudomonas clades drops the residual R2 to 0.072. *(confidence: high)*
- Even after KEGG-module gating reduced T3SS false positives by 86% and narrowed the panel to 17 plant-specific markers, the dual-nature rate among plant-associated species rose to 78.7%, indicating genuine co-occurrence of PGP and pathogenic functions. *(confidence: medium)*
- All 14 experimentally confirmed beneficial and pathogenic ground-truth species were assigned to the dual-nature class, so the categorical cohort label cannot discriminate beneficial from pathogenic species; the continuous pathogenicity ratio is the discriminating signal (median 0.50 vs 0.60, p=0.027). *(confidence: medium)*
- All 50 plant-enriched ortholog groups have characterized functions, dominated by electron-transport/energy metabolism (high-affinity cytochrome oxidases, 7/50) and iron-sulfur cluster biosynthesis (iscA, 94.3% plant), with 60.1-83.1% core gene fractions. *(confidence: high)*
- Beneficial plant-growth-promoting gene clusters are predominantly core-encoded (64.6% core fraction) while pathogenic clusters are accessory (45.2% core), a difference far exceeding the genome-wide baseline (Mann-Whitney p=3.38e-125). *(confidence: high)*
- Co-occurring plant-associated genera in soil communities are slightly less metabolically complementary than random genus pairs (Cohen d about -0.4, permutation p<0.001), supporting functional redundancy at a small effect size. *(confidence: medium)*
- Independent MGnify metagenome cross-validation found T3SS prevalence roughly 2x higher in rhizosphere biomes (21.6-24.0%) than bulk soil (12.3%), confirming the type III secretion system as a marker of plant association. *(confidence: medium)*
- Of 5,341 eggNOG ortholog groups significantly associated with plant association, 50 retained significance after phylum-level phylogenetic control, identifying a robust set of plant-enriched gene families led by COG3569 (phylo-controlled OR=6.01). *(confidence: high)*
- Plant compartment identity explains only a small fraction (~6% of variance, db-RDA location-only R2=0.060, p=0.001) of microbial functional-profile variation once location and dispersion effects are separated, far below the original PERMANOVA R2 of 0.527. *(confidence: high)*
- Plant-associated genera carry higher mobilome burden than non-plant genera (median 3.7 vs 2.8 mobile elements per genome, Mann-Whitney p=1.49e-5), a genus-level enrichment that contrasts with genome-level studies reporting fewer mobile elements in plant-associated bacteria. *(confidence: medium)*
- Plant-associated species carrying singleton marker gene clusters are 16x more likely to also carry transposase/integrase singletons (Fisher OR=15.95, p=8.8e-20), a co-occurrence signature consistent with horizontal gene transfer. *(confidence: medium)*
- Under combined cluster-robust GLM and within-genus permutation tests, plant-association markers split three ways: 3 are species-level robust (nitrogen fixation, ACC deaminase, T3SS), 5 are cassette-level (genus-acquired but not species-distinguishing), and 6 are not robust. *(confidence: high)*
- Within-species subclade analysis showed weak segregation in 5/17 testable species, with two canonical pathovar-host specializations confirmed genomically: Xanthomonas campestris segregating to Brassica hosts and X. vasicola to maize. *(confidence: medium)*
- RNAseq under beneficial versus pathogenic conditions on the Tier-1 marker genes (nitrogen fixation, ACC deaminase, T3SS) and core rhizosphere genera would test whether dual-nature gene sets are co-expressed or differentially regulated, since current classification is presence-based. *(confidence: medium)*
- The genus dossiers, core rhizosphere genera, host-specificity matrix (117 tomato-specific, 54 maize-specific, 5 barley-specific genera), and 84 NRP/siderophore-producing genera provide candidates for synthetic-community design and crop-specific biocontrol formulations. *(confidence: medium)*

## Topics

- [Topic: Environment Biogeography](../topics/environment-biogeography.md)
- [Topic: Functional Dark Matter](../topics/functional-dark-matter.md)
- [Topic: Gene Fitness](../topics/gene-fitness.md)
- [Topic: Metabolic Pathways](../topics/metabolic-pathways.md)
- [Topic: Microbial Ecotypes](../topics/microbial-ecotypes.md)
- [Topic: Microbiome Engineering](../topics/microbiome-engineering.md)
- [Topic: Mobile Genetic Elements](../topics/mobile-genetic-elements.md)
- [Topic: Pangenome Architecture](../topics/pangenome-architecture.md)
- [Topic: Subsurface Genomics](../topics/subsurface-genomics.md)

## Data

- [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md)
- [Nmdc Arkin](../data/nmdc-arkin.md)

## Authors

- [Adam P. Arkin](../authors/0000-0002-4999-2931.md)

[Open the full report →](../../../projects/plant_microbiome_ecotypes/REPORT.md)

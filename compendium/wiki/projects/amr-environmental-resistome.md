# Amr Environmental Resistome

This project characterized how bacterial antibiotic resistance genes vary across ecological niches by analyzing 82,908 AMR clusters across 14,723 species (293,000 genomes), examining whether environmental setting predicts resistome composition and diversity. The work revealed that clinical and human gut bacteria carry 2.5× more AMR than soil and aquatic species, with the resistome architecture reflecting acquisition strategy: soil bacteria retain ancient, chromosomally-encoded resistance while clinical bacteria have predominantly acquired resistance through horizontal gene transfer. Most importantly, different ecological niches select for fundamentally different resistance mechanisms—metal resistance dominates soil and aquatic environments (44-45% of AMR) while target modification and efflux pumps dominate clinical settings—suggesting that environment, not just phylogeny, shapes how bacteria evolve and deploy resistance.

## Key findings

- The analysis establishes correlation rather than causation between environment and AMR, and effect sizes are modest, with environment explaining only 2-13% of variance in AMR composition. *(confidence: high)*
- The clinical-carries-more-AMR finding is partly confounded by NCBI sampling bias, because clinical isolates are massively overrepresented and clinical species are the ones sequenced precisely because they have AMR. *(confidence: high)*
- Soil and aquatic species retain ancient, chromosomally encoded (intrinsic) resistance, whereas clinical and human gut species have overwhelmingly acquired their AMR through horizontal gene transfer. *(confidence: medium)*
- The mechanism-conservation pattern (metal resistance accessory, efflux core) is driven by ecology: efflux genes are core because they serve host-associated organisms across conditions, while metal resistance is accessory because it is only needed in metal-rich environments. *(confidence: medium)*
- Across 823 species sampled in multiple environments, the fraction of genomes from clinical sources strongly predicts total AMR cluster count (Spearman rho = 0.465), with clinical-dominated species carrying 4.4x more AMR clusters than environmentally dominated ones. *(confidence: high)*
- Clinical and human gut bacterial species carry roughly 2.5x more AMR gene clusters (median 5) than soil, aquatic, and host-associated species (median 2), establishing ecological niche as a strong predictor of resistome size. *(confidence: high)*
- Continuous AlphaEarth environmental embeddings independently confirm the discrete environment findings, with a Mantel test showing that environmental distance predicts AMR profile distance (r = 0.098, p = 0.001) most strongly for clinical species. *(confidence: medium)*
- Different ecological niches select for fundamentally different resistance strategies, with target modification dominating in human gut (44%) and clinical (28%) species while only reaching 6% in aquatic species. *(confidence: high)*
- Klebsiella pneumoniae exemplifies HGT-driven within-species AMR variation, carrying 1,115 AMR gene clusters of which only 7 are core, so nearly its entire resistome is accessory. *(confidence: high)*
- Metal resistance is the most environment-discriminating AMR mechanism, comprising ~44-45% of AMR in soil and aquatic species but only 6% in human gut species (the largest mechanism effect, eta-squared = 0.107). *(confidence: high)*
- The environment-AMR relationship survives phylogenetic control, with 20 of 141 testable bacterial families showing significant within-family environment effects, demonstrating it is not simply a proxy for phylogeny. *(confidence: medium)*
- The intrinsic/acquired composition of the resistome varies quantitatively along an ecological gradient, from 43% accessory AMR in soil species up to 68% in clinical and 80% in human gut species. *(confidence: high)*
- Combining the environment-AMR profiles with the amr_fitness_cost project could test whether AMR genes enriched in clinical settings are costlier because recently acquired or cheaper because under strong selection. *(confidence: medium)*
- When mobile genetic element annotations become available in BERDL, accessory AMR clusters in clinical species could be tested for preferential association with plasmids, transposons, or integrative elements. *(confidence: medium)*

## Topics

- [Topic: Amr Resistome](../topics/amr-resistome.md)
- [Topic: Environment Biogeography](../topics/environment-biogeography.md)
- [Topic: Gene Fitness](../topics/gene-fitness.md)
- [Topic: Metal Resistance](../topics/metal-resistance.md)
- [Topic: Microbial Ecotypes](../topics/microbial-ecotypes.md)
- [Topic: Mobile Genetic Elements](../topics/mobile-genetic-elements.md)
- [Topic: Pangenome Architecture](../topics/pangenome-architecture.md)

## Data

- [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md)
- [Nmdc Arkin](../data/nmdc-arkin.md)

## Authors

- [Paramvir S. Dehal](../authors/0000-0001-5810-2497.md)

[Open the full report →](../../../projects/amr_environmental_resistome/REPORT.md)

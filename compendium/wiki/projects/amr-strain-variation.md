# Amr Strain Variation

This project set out to systematically quantify how antimicrobial resistance (AMR) genes vary within bacterial species across more than 1,300 species and 180,000 genomes, revealing that the vast majority of AMR genes are rare or variable within species rather than universally fixed. The most striking finding—that acquired resistance genes show stronger phylogenetic signal than intrinsic genes—reveals that once a lineage acquires resistance elements, they are stably maintained and vertically inherited, creating clonal AMR signatures that make tracking lineages more informative for surveillance than tracking individual resistance genes.

## Key findings

- No species showed significant temporal trends in AMR gene accumulation after FDR correction, but this null result likely reflects sparse and noisy NCBI collection-date metadata rather than a true absence of temporal trends. *(confidence: medium)*
- Statistical testing of ecotype-environment association is underpowered because 52.7% of genomes lack a classifiable isolation source, leaving only 2 species with sufficient within-species environmental diversity for chi-squared testing. *(confidence: high)*
- The lower phylogenetic signal for core AMR genes is partly a statistical artifact, because their near-universal prevalence produces near-zero Jaccard distances with little variance that suppress distance-based Mantel correlations independent of biology. *(confidence: medium)*
- Because acquired resistance elements appear to be stably maintained and vertically transmitted within lineages, tracking clonal lineages may be more informative for AMR surveillance than tracking individual resistance genes. *(confidence: medium)*
- This is the first study to systematically quantify within-species AMR variation across more than 1,300 species simultaneously, enabled by the KBase/BERDL pangenome resource. *(confidence: medium)*
- AMR genes are organized into 1,517 tightly co-inherited resistance islands across 54% of analyzed species, with a mean phi coefficient of 0.827 indicating very tight co-occurrence. *(confidence: high)*
- AMR profiles are not randomly distributed across phylogeny, with 55.6% of species showing significant phylogenetic signal in their AMR repertoire by Mantel test (FDR < 0.05). *(confidence: high)*
- Across 1,305 species and 180,025 genomes, over 90% of AMR gene-species occurrences are variable or rare within a species, with only 7.5% fixed and strains sharing less than 60% of their AMR repertoire. *(confidence: high)*
- Counter-intuitively, non-core (acquired) AMR genes show stronger phylogenetic signal (median Mantel r = 0.222) than core (intrinsic) genes (r = 0.117), suggesting acquired resistance is often clonally inherited rather than randomly transferred. *(confidence: high)*
- Cross-species atlas conservation class strongly predicts within-species prevalence, with 77.3% of Core AMR genes fixed within species and 78.7% of Singletons rare, validating the core/accessory distinction at strain resolution. *(confidence: high)*
- Host-associated species consistently carry more AMR genes per genome than terrestrial or aquatic species, with human-clinical isolates showing the highest AMR burden across two independent environment classifiers. *(confidence: high)*
- Most resistance islands (88%) combine genes from multiple resistance mechanisms, dominated by efflux pumps and enzymatic inactivation, suggesting coordinated defense against multiple drug classes. *(confidence: high)*
- Roughly one in five species (19.5% of 974 species with sufficient genomes) form two or more distinct AMR ecotypes by UMAP plus DBSCAN clustering, with good cluster quality (median silhouette 0.620). *(confidence: high)*
- AMR ecotypes could be integrated with virulence factor profiles and metabolic pathway variation from other BERDL analyses to connect resistance structure to broader strain phenotypes. *(confidence: low)*
- The resistance island co-occurrence structure could be used to build predictive models of which AMR genes are likely to be co-acquired in the future. *(confidence: medium)*

## Topics

- [Topic: Amr Resistome](../topics/amr-resistome.md)
- [Topic: Environment Biogeography](../topics/environment-biogeography.md)
- [Topic: Metabolic Pathways](../topics/metabolic-pathways.md)
- [Topic: Microbial Ecotypes](../topics/microbial-ecotypes.md)
- [Topic: Mobile Genetic Elements](../topics/mobile-genetic-elements.md)
- [Topic: Pangenome Architecture](../topics/pangenome-architecture.md)

## Data

- [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md)

## Authors

- [Paramvir S. Dehal](../authors/0000-0001-5810-2497.md)

[Open the full report →](../../../projects/amr_strain_variation/REPORT.md)

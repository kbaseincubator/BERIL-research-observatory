# Phb Granule Ecology

This project investigated how bacteria use polyhydroxybutyrate (PHB), a carbon-storage polymer, across the bacterial tree of life and whether its distribution reflects adaptation to unpredictable, nutrient-variable environments. Across 27,690 bacterial species, PHB pathway genes showed a >10-fold enrichment gradient from temporally variable habitats (soil and plant-associated, 44%) to stable host environments (clinical, 7%), strongly supporting environmental selection for PHB-mediated "feast or famine" survival. The analysis also identified 311 recent horizontal gene transfer events acquiring phaC (PHA synthase), revealing active dispersal of PHB pathways across bacterial lineages despite deep phylogenetic divergence.

## Key findings

- NMDC abiotic correlations with PHB inference scores were statistically significant but modest in size (|rho| < 0.12), likely because abiotic measurements are point-in-time snapshots rather than measures of temporal variability. *(confidence: medium)*
- The PHB regulator phaR (K18080) was absent from eggNOG annotations of all 27K species, indicating an annotation coverage gap or KO misassignment rather than true biological absence. *(confidence: medium)*
- The apparent association between PHB and broader environmental niche breadth largely disappears after controlling for genome size (partial rho = -0.047), making it a confounded artefact rather than independent evidence. *(confidence: high)*
- Discordant phaC-positive species carry phaC as accessory genome at nearly double the baseline rate (60.1% vs 32.3%), consistent with recent horizontal acquisition not yet fixed in the core genome. *(confidence: medium)*
- A chi-squared test of PHB presence against environmental variability category was highly significant (chi2 = 1,656.36, p ~ 0, dof = 2) across 27,690 species. *(confidence: high)*
- Across 27,690 GTDB species, 21.9% carry phaC (PHA synthase) and 21.7% have a complete PHB biosynthesis pathway, the first precise pan-bacterial prevalence estimate. *(confidence: high)*
- Family-level Fisher tests across 248 families revealed heterogeneous selection within phyla, with 41 PHB-enriched families (skewing freshwater/wastewater) and 62 depleted families (skewing marine/host-associated). *(confidence: medium)*
- NMDC metagenomic cross-validation showed PHB-high genera have significantly higher abundance than PHB-low genera (Mann-Whitney p = 8.41e-22), with top genera including known producers like Pseudomonas and Cupriavidus. *(confidence: medium)*
- PHB environmental enrichment is robust to genome size, holding within all four genome size quartiles with 1.4–4.6x fold enrichment in high-variability environments (all p < 1e-11). *(confidence: high)*
- PHB pathway distribution is highly uneven across the bacterial tree, with Pseudomonadota alone accounting for 74.9% of phaC-carrying species and several major phyla entirely lacking PHB. *(confidence: high)*
- PHB prevalence follows a >10-fold gradient from temporally variable environments (plant 44%, soil 43.6%) to stable host-associated environments (clinical 7.4%, animal 3.3%), supporting environmental selection for PHB. *(confidence: high)*
- Phylogenetically discordant phaC distribution revealed 311 potential horizontal acquisition events and 278 potential loss events, evidencing widespread HGT of phaC across the bacterial tree. *(confidence: medium)*
- Mapping eggNOG Pfam domain names (Abhydrolase_1, PhaC_N) to accession IDs (PF00561, PF07167) would enable proper Class I–IV PHA synthase classification across all 11,792 phaC clusters. *(confidence: medium)*
- Querying the BERDL Fitness Browser for phaC mutant fitness phenotypes could test whether phaC confers a measurable fitness advantage under carbon-variable conditions. *(confidence: low)*

## Topics

- [Topic: Environment Biogeography](../topics/environment-biogeography.md)
- [Topic: Functional Dark Matter](../topics/functional-dark-matter.md)
- [Topic: Gene Fitness](../topics/gene-fitness.md)
- [Topic: Metabolic Pathways](../topics/metabolic-pathways.md)
- [Topic: Microbial Ecotypes](../topics/microbial-ecotypes.md)
- [Topic: Mobile Genetic Elements](../topics/mobile-genetic-elements.md)
- [Topic: Pangenome Architecture](../topics/pangenome-architecture.md)

## Data

- [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md)
- [Nmdc Arkin](../data/nmdc-arkin.md)

## Authors

- [Adam P. Arkin](../authors/0000-0002-4999-2931.md)

[Open the full report →](../../../projects/phb_granule_ecology/REPORT.md)

# Pseudomonas Carbon Ecology

This project systematically characterized carbon source utilization across the entire Pseudomonas genus (433 species, 12,732 genomes) to understand how metabolic capabilities reflect ecological lifestyle and environment. The central finding is that host-associated *P. aeruginosa* has lost plant-derived sugar catabolism pathways through ancestral metabolic streamlining, whereas free-living species maintain broader pathway richness; moreover, carbon pathway composition significantly correlates with isolation environment even among free-living species, demonstrating that metabolic niche specialization is a fundamental organizing principle of Pseudomonas ecology.

## Key findings

- P. aeruginosa comprises 53% of all genomes due to clinical importance while many environmental species have fewer than 10 sequenced genomes, an imbalance that limits the power of species-level comparisons. *(confidence: high)*
- The 62 GapMind carbon pathways miss genus-specific catabolic capabilities, particularly aromatic degradation pathways (toluene, naphthalene, benzoate) central to P. putida ecology. *(confidence: high)*
- The dominant signal in the analysis separates subgenera rather than lifestyles, and within Pseudomonas_E lifestyle-associated differences are subtle, with the analyses not explicitly controlling for phylogenetic non-independence among species. *(confidence: high)*
- Much of the metabolic versatility loss in P. aeruginosa reflects ancestral metabolic streamlining of the lineage itself rather than loss acquired during chronic infection, since these pathways were already absent at the species level across thousands of isolates. *(confidence: medium)*
- This is the first study to systematically quantify carbon pathway profiles across the full breadth of Pseudomonas (433 species, 12,732 genomes) using standardized GapMind pathway predictions. *(confidence: medium)*
- A Random Forest classifier predicting four environment classes from carbon pathway profiles achieved balanced accuracy of 0.408 +/- 0.169, above the 0.250 chance level but only modestly predictive. *(confidence: medium)*
- Amino acid and core organic acid catabolism (arginine, histidine, serine, glutamate, citrate, succinate, pyruvate) remain near-universal (>99%) in both subgenera, consistent with P. aeruginosa retaining amino acid catabolism for growth in host environments such as CF sputum. *(confidence: high)*
- Among 54 free-living and plant-associated species, carbon pathway profiles are significantly associated with isolation environment, with a permutation test yielding p = 0.006. *(confidence: medium)*
- Free-living and plant-associated species maintain higher carbon pathway richness (median 57 pathways) than host-associated species (median 55), a trend that persists within the Pseudomonas_E subgenus alone. *(confidence: medium)*
- Host-associated Pseudomonas sensu stricto (the P. aeruginosa group) show near-complete loss of plant-derived sugar catabolism relative to Pseudomonas_E, with 43 of 62 GapMind carbon pathways differing significantly between the two subgenera. *(confidence: high)*
- The pathways most strongly lost in the P. aeruginosa group are plant-derived sugars and sugar alcohols such as xylose, arabinose, and myo-inositol (0% complete versus 59-74% in the P. fluorescens group). *(confidence: high)*
- The primary axis of carbon pathway variation across Pseudomonas separates P. aeruginosa (Pseudomonas s.s.) from Pseudomonas_E, driven by the dramatic sugar pathway loss, while within-subgenus lifestyle categories overlap substantially. *(confidence: high)*
- The study extracted GapMind carbon pathway predictions for 12,732 genomes across 433 Pseudomonas species clades (GTDB r214) from the BERDL kbase_ke_pangenome collection. *(confidence: high)*
- Analyzing within-species carbon pathway variation in species isolated from multiple environments (e.g., P. fluorescens, P. putida) could reveal metabolic ecotypes adapted to different niches. *(confidence: medium)*
- Cross-referencing carbon pathway predictions with RB-TnSeq fitness data from the kescience_fitnessbrowser could experimentally validate which pathways are functionally important in specific carbon sources. *(confidence: medium)*

## Topics

- [Topic: Environment Biogeography](../topics/environment-biogeography.md)
- [Topic: Functional Dark Matter](../topics/functional-dark-matter.md)
- [Topic: Gene Fitness](../topics/gene-fitness.md)
- [Topic: Metabolic Pathways](../topics/metabolic-pathways.md)
- [Topic: Microbial Ecotypes](../topics/microbial-ecotypes.md)
- [Topic: Microbiome Engineering](../topics/microbiome-engineering.md)
- [Topic: Pangenome Architecture](../topics/pangenome-architecture.md)

## Data

- [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md)
- [Kescience Fitnessbrowser](../data/kescience-fitnessbrowser.md)

## Authors

- [Mark Andrew Miller](../authors/0000-0001-9076-6066.md)

[Open the full report →](../../../projects/pseudomonas_carbon_ecology/REPORT.md)

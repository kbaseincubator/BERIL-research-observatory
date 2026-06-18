# Pathway Capability Dependency

This project mapped metabolic pathway dependencies across bacteria by integrating genomic pathway completeness (GapMind annotations) with experimental fitness data (RB-TnSeq), revealing that genome content alone is insufficient to predict metabolic necessity. The key result: among 161 organism-pathway pairs across 7 model bacteria, only 35% showed fitness importance despite being genomically complete, while 41% were complete yet fitness-neutral under standard conditions; however, condition-type stratification demonstrated that all latent pathways become fitness-critical under specific environmental triggers like nitrogen limitation, stress, or carbon limitation, reframing pathway "completeness" as context-dependent metabolic potential rather than evidence of function.

## Key findings

- Correlations were controlled only for genome count and taxonomic grouping rather than full phylogenetic independent contrasts, so metabolic ecotypes may partly reflect intra-species phylogenetic structure given that phylogeny dominates gene content in most species. *(confidence: medium)*
- The median-based importance threshold splits pathways roughly 50/50 by construction, so the claim that all Latent Capabilities become important under some condition is partly an artifact and would need an independent validation set for a defensible threshold. *(confidence: medium)*
- Tier 1 classification rests on only 7 of 48 Fitness Browser organisms that have GapMind data, all well-annotated model organisms whose near-complete core genomes compress the conservation validation signal. *(confidence: high)*
- A composite importance score integrating essentiality (40%), fitness breadth (30%), and fitness magnitude (30%) is used to classify each organism-pathway pair from RB-TnSeq data. *(confidence: high)*
- Pathway variation supplies a mechanistically interpretable correlate of pangenome openness that broader ecological and phylogenetic variables, which showed no openness correlation in a prior project, failed to capture. *(confidence: medium)*
- Roughly 14% of species-level completeness for the top accessory-dependent pathways comes from accessory genes, so different strains carry different biosynthetic capabilities, a precondition for Black Queen public-good metabolism. *(confidence: medium)*
- Across 2,810 species with at least 10 genomes, the number of variable pathways correlates with pangenome openness, strengthening to partial Spearman rho=0.530 (p=2.83e-203) after controlling for genome count. *(confidence: high)*
- Active Dependencies have higher mean core gene completeness (0.986) than Latent Capabilities (0.975), a small but consistent enrichment aligned with fitness-important genes being concentrated in the core genome. *(confidence: medium)*
- All 66 Latent Capability pathway-organism pairs become fitness-important under at least one condition type, most often nitrogen limitation, stress, or carbon limitation, reframing latency as context-dependence rather than genomic baggage. *(confidence: medium)*
- Amino acid biosynthesis pathways (leucine, valine, arginine, lysine, threonine) show the strongest dependence on accessory genes, with core-vs-all completeness gaps of about 0.14, direct evidence for Black Queen distribution of biosynthetic capacity across strains. *(confidence: high)*
- Of 161 organism-pathway pairs across 7 model bacteria, only 35.4% are Active Dependencies while 41.0% are genomically complete but fitness-neutral Latent Capabilities, showing pathway completeness does not predict metabolic dependency. *(confidence: high)*
- Within-species clustering of binary pathway profiles defines a median of 4 (up to 8) metabolic ecotypes per species, and ecotype count correlates with pangenome openness (partial rho=0.322, p=8.0e-07) after controlling for genome count. *(confidence: medium)*
- Correlating metabolic ecotypes with AlphaEarth environmental niche breadth was planned but not executed and remains a future direction, constrained by AlphaEarth covering only 28% of genomes. *(confidence: medium)*
- The 14.9% of pairs scored incomplete by GapMind yet fitness-important point to annotation gaps or salvage routes that GapMind misses, an opportunity to improve pathway annotation. *(confidence: medium)*

## Topics

- [Topic: Environment Biogeography](../topics/environment-biogeography.md)
- [Topic: Functional Dark Matter](../topics/functional-dark-matter.md)
- [Topic: Gene Fitness](../topics/gene-fitness.md)
- [Topic: Metabolic Pathways](../topics/metabolic-pathways.md)
- [Topic: Microbial Ecotypes](../topics/microbial-ecotypes.md)
- [Topic: Pangenome Architecture](../topics/pangenome-architecture.md)

## Data

- [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md)
- [Kescience Fitnessbrowser](../data/kescience-fitnessbrowser.md)

## Authors

- [Dileep Kishore](../authors/dileep-kishore.md)
- [Paramvir S. Dehal](../authors/0000-0001-5810-2497.md)

[Open the full report →](../../../projects/pathway_capability_dependency/REPORT.md)

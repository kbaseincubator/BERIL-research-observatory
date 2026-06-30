# T4Ss Cazy Environmental Hgt

This project investigated whether type IV secretion system (T4SS) conjugative machinery drives horizontal gene transfer of carbohydrate-active enzymes (CAZy) across phylogenetically distant environmental bacteria. By analyzing 30,497 environmental metagenome-assembled genomes, the team detected 32 high-confidence cross-phylum HGT events in a GT2 glycosyltransferase gene tree, with the strongest signal spanning eight distinct bacterial phyla at phylogenetic divergence 4.843, consistent with conjugative transfer rather than plasmid-mediated mobilisation. These findings suggest T4SS is a major driver of metabolic diversity dissemination in environmental ecosystems, distinct from the classical polysaccharide utilization locus paradigm.

## Key findings

- All reported associations are observational and the central claim is explicitly associative, so mechanistic confirmation of T4SS-mediated CAZy transfer requires experimental validation. *(confidence: high)*
- The 10 kb synteny threshold and the cross-phylum incongruence rate remain unvalidated because the permutation test and housekeeping-gene null baseline have not yet been run. *(confidence: high)*
- The headline Node_4915 result of 8 phyla at divergence 4.843 still needs sequence-level verification by BLAST against NCBI to rule out chimeric or misclassified sequences. *(confidence: medium)*
- Cross-phylum clustering of syntenic T4SS-GT2 loci in 32 verified cases is inconsistent with vertical inheritance and consistent with conjugative horizontal transfer of CAZy cassettes in environmental bacteria. *(confidence: medium)*
- The T4SS-CAZy HGT signal occurs across non-Bacteroidetes lineages via conjugation and is mechanistically and taxonomically distinct from the TonB-dependent PUL paradigm. *(confidence: medium)*
- 92 CAZy families show elevated co-occurrence with T4SS loci within 10 kb, with GT2 glycosyltransferases the top hit across 767 genomes. *(confidence: medium)*
- A negative binomial GLM estimates that each additional CAZy family increases the expected enriched KEGG pathway count by about 35%. *(confidence: medium)*
- About 21.8% of 30,497 high-quality environmental MAGs carry T4SS conjugative machinery defined by a multi-marker gene set. *(confidence: high)*
- CAZy genes are not located on plasmids while T4SS-positive genomes show 10x higher MGE density, consistent with chromosomal or integrative transfer rather than plasmid mobilisation. *(confidence: medium)*
- GT2-neighbourhood MAGs carry roughly 11x more metal resistance genes than non-GT2 MAGs, linking CAZy-T4SS synteny hubs to the metal resistance niche. *(confidence: medium)*
- More phylogenetically distant HGT events have lower syntenic percentage (Spearman rho = -0.615), consistent with sequence divergence accumulating after transfer. *(confidence: medium)*
- Node_4915 was confirmed as a 35-gene, 82.9% syntenic cluster spanning eight distinct bacterial phyla. *(confidence: medium)*
- Phylogenetic analysis of the GT2 gene tree detected 77 HGT events including 32 high-confidence cross-phylum events, with Node_4915 spanning 8 phyla at maximum divergence 4.843. *(confidence: medium)*
- T4SS-CAZy synteny is enriched in marine sediment and rhizosphere biomes, most strongly in barley rhizosphere (OR=10.4). *(confidence: medium)*
- A biome enrichment factorisation comparing joint to independent odds ratios would test whether the striking rhizosphere co-enrichment exceeds independent T4SS and CAZy prevalence effects. *(confidence: medium)*
- Building gene trees for five conserved single-copy housekeeping genes from the same genomes would establish a null incongruence baseline showing whether GT2 syntenic incongruence exceeds background. *(confidence: medium)*

## Topics

- [Topic: Environment Biogeography](../topics/environment-biogeography.md)
- [Topic: Metabolic Pathways](../topics/metabolic-pathways.md)
- [Topic: Metal Resistance](../topics/metal-resistance.md)
- [Topic: Mobile Genetic Elements](../topics/mobile-genetic-elements.md)
- [Topic: Pangenome Architecture](../topics/pangenome-architecture.md)

## Data

- [Kescience Fitnessbrowser](../data/kescience-fitnessbrowser.md)

## Authors

- [Heather MacGregor](../authors/heather-macgregor.md)

[Open the full report →](../../../projects/t4ss_cazy_environmental_hgt/REPORT.md)

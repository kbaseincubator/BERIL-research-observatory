# Conservation Vs Fitness

This project linked Fitness Browser gene essentiality data across 33 bacterial species to KBase pangenome clusters, asking whether genes required for viability are conserved across strains. Essential genes proved modestly but significantly enriched in core pangenome clusters (median odds ratio 1.56), yet the relationship is context-dependent: essential-core genes are enzyme-rich and enriched in housekeeping functions, while poorly-characterized essential-auxiliary genes suggest strain-specific compensatory mechanisms and recently-acquired variants.

## Key findings

- Essentiality here reflects a single set of RB-TnSeq library construction conditions, so genes essential only under stress conditions are not captured. *(confidence: high)*
- The essential-in-core enrichment is modest (OR=1.56) because most genes in well-characterized bacteria are core regardless of essentiality, limiting the discriminative power of the core/auxiliary classification. *(confidence: high)*
- The transposon-based essential gene set is an upper bound because short genes, low-complexity regions, or scaffold edges can lack insertions for non-essentiality reasons, and essential genes are slightly shorter on average, indicating insertion bias. *(confidence: high)*
- Clade-size and lifestyle stratification show that the essential-core enrichment is robust across diverse genomic contexts rather than an artifact of pangenome structure. *(confidence: medium)*
- Essential-core genes are depleted in Carbohydrates, Amino Acids, and Membrane Transport functions that tend to be conditionally important rather than universally essential. *(confidence: medium)*
- Across the linked genes, 145,821 (82.0%) were core and 32,042 (18.0%) auxiliary, with 7,574 singletons forming a subset of the auxiliary fraction. *(confidence: high)*
- Defining essentiality as the absence of viable transposon mutants identified 27,693 putative essential genes, 18.6% of 148,826 protein-coding genes across 33 organisms, with 86.1% of essential genes core versus 81.2% for non-essential genes. *(confidence: high)*
- Essential-auxiliary genes (3,683 genes essential for viability but not present in all strains) are poorly characterized (38.2% hypothetical) and less enzyme-rich (13.4%), with top subsystems spanning ribosomes, DNA replication, type 4 secretion, and plasmid replication. *(confidence: high)*
- Essential-core genes are the most enzyme-rich (41.9%) and best-annotated category (only 13.0% hypothetical), enriched in Protein Metabolism, Cofactors/Vitamins, Cell Wall, and Fatty Acid biosynthesis. *(confidence: high)*
- Essential-unmapped genes (1,259 strain-specific essentials with no pangenome cluster match) are the least characterized category (44.7% hypothetical), dominated by divergent ribosomal proteins, translation factors, transposases, and DNA-binding proteins. *(confidence: medium)*
- Mapping Fitness Browser genes to KBase pangenome clusters by DIAMOND blastp produced 177,863 gene-to-cluster links for 44 of 48 FB organisms at near-perfect identity, of which 82.0% fell in core clusters and 18.0% in auxiliary. *(confidence: high)*
- Putative essential genes are modestly but significantly enriched in core pangenome clusters, with a median odds ratio of 1.56 and significant enrichment in 18 of 33 organisms after BH-FDR correction. *(confidence: high)*
- Deeper characterization of the 3,683 essential-auxiliary genes could test whether they compensate for missing core functions in particular strains. *(confidence: medium)*
- Extending the analysis beyond binary essentiality to condition-specific fitness effects could reveal whether genes important under specific stress conditions show different conservation patterns. *(confidence: medium)*

## Topics

- [Topic: Functional Dark Matter](../topics/functional-dark-matter.md)
- [Topic: Gene Fitness](../topics/gene-fitness.md)
- [Topic: Metabolic Pathways](../topics/metabolic-pathways.md)
- [Topic: Pangenome Architecture](../topics/pangenome-architecture.md)

## Authors

- [Paramvir S. Dehal](../authors/0000-0001-5810-2497.md)

[Open the full report →](../../../projects/conservation_vs_fitness/REPORT.md)

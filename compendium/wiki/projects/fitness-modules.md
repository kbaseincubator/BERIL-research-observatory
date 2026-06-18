# Fitness Modules

This project applied robust Independent Component Analysis to RB-TnSeq gene-fitness matrices from 32 bacterial organisms to discover co-regulated functional modules—genes that vary together across thousands of experimental conditions. Across all organisms, 1,116 stable modules were identified and validated by strong within-module cofitness enrichment (94.2% of modules show significant correlation; 2.8x mean correlation above background) and 22.7x genomic adjacency enrichment, demonstrating that these computational modules recapitulate genuine biological co-regulation programs conserved across diverse bacterial phyla. The project generated 6,691 function predictions for hypothetical proteins using module membership, establishing that fitness modules capture process-level gene regulation rather than specific molecular functions and filling a niche ortholog-based methods cannot reach.

## Key findings

- Module-ICA has near-zero precision for predicting specific KEGG KO assignments because KO groups are gene-level (about 1.2 genes per unique KO); modules capture process-level co-regulation, not specific molecular function. *(confidence: high)*
- Organisms with fewer than about 100 experiments produce weaker modules, exemplified by Caulobacter with 198 experiments showing only 2.9x correlation enrichment. *(confidence: medium)*
- Robust Independent Component Analysis applied to RB-TnSeq gene-fitness matrices from the Fitness Browser decomposes them into latent functional modules of co-regulated genes, complementing sequence-based annotation by capturing process-level co-regulation. *(confidence: high)*
- The largest module family spans 21 organisms, providing evidence for a deeply conserved, pan-bacterial co-regulation program. *(confidence: medium)*
- 94.2% of fitness modules show significantly elevated within-module cofitness (Mann-Whitney U, p < 0.05), with within-module mean |r| of 0.34 versus a background of 0.12 (a 2.8x enrichment). *(confidence: high)*
- Adding PFam domains and lowering the enrichment overlap threshold from 3 to 2 raised the module annotation rate from 8% to 80% (92 to 890 modules) and unlocked 7.6x more function predictions. *(confidence: high)*
- Module enrichment generated 6,691 function predictions for hypothetical proteins across all 32 organisms, of which 2,455 (37%) are family-backed by cross-organism conservation. *(confidence: high)*
- Module genes show 22.7x genomic adjacency enrichment, indicating they are co-located in operons. *(confidence: high)*
- Ortholog transfer remains the gold standard for gene-level function prediction at 95.8% precision, while Module-ICA fills a different niche by identifying which biological processes an uncharacterized gene participates in. *(confidence: high)*
- Ortholog-fingerprint alignment across 32 organisms produced 156 module families spanning two or more organisms (28 spanning 5+, 7 spanning 10+, 1 spanning 21), revealing conserved fitness regulons across diverse bacterial phyla. *(confidence: high)*
- Robust ICA across 32 bacterial organisms, each with at least 100 experiments, yielded 1,116 stable fitness modules. *(confidence: high)*
- Switching from a D'Agostino K-squared module definition to strict absolute weight thresholds (|weight| >= 0.3, max 50 genes) made modules biologically coherent, raising enrichment to 94% and cofitness correlation enrichment to 2.8x. *(confidence: high)*
- A web interface for browsing module families and function predictions would make the conserved fitness regulons and predictions broadly accessible. *(confidence: low)*
- Integrating module predictions with pangenome gene classifications (core/auxiliary/singleton) could reveal which fitness modules are enriched in accessory genes. *(confidence: medium)*

## Topics

- [Topic: Functional Dark Matter](../topics/functional-dark-matter.md)
- [Topic: Gene Fitness](../topics/gene-fitness.md)
- [Topic: Metabolic Pathways](../topics/metabolic-pathways.md)
- [Topic: Pangenome Architecture](../topics/pangenome-architecture.md)

## Data

- [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md)
- [Kescience Fitnessbrowser](../data/kescience-fitnessbrowser.md)

## Authors

- [Paramvir S. Dehal](../authors/0000-0001-5810-2497.md)

[Open the full report →](../../../projects/fitness_modules/REPORT.md)

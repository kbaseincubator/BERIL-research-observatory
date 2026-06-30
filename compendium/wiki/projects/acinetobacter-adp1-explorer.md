# Acinetobacter Adp1 Explorer

This project assembled a unified multi-omics database for *Acinetobacter baylyi* ADP1 and 13 related genomes, integrating TnSeq gene essentiality, metabolic flux predictions, mutant fitness across 8 carbon sources, proteomics, and pangenome context into a 15-table SQLite database (135 MB, 461k rows). The data is deeply connected to BERDL—matching 91-100% of genome IDs, reactions, and compounds—with a key distinction: ADP1 condition-specific fitness measurements are absent from the public Fitness Browser, making this the sole source of such data in the lakehouse and enabling model-experiment concordance analysis for metabolic predictions across diverse growth conditions.

## Key findings

- 87% of the 121,519 growth phenotype predictions rely on at least one gapfilled reaction, tightly coupling prediction accuracy to gapfilling quality. *(confidence: high)*
- No gene in the database carries data across all six modalities, and the sparse FBA flux coverage (15%) limits model-experiment concordance analysis to just 866 genes. *(confidence: high)*
- Because A. baylyi ADP1 is absent from the Fitness Browser, the condition-specific mutant growth data in this database is a unique fitness resource not available elsewhere in BERDL. *(confidence: high)*
- Essential genes are more likely to reside in the core pangenome, consistent with the pattern that conserved genes tend to be essential. *(confidence: medium)*
- A gene junction table provided a complete bridge between the ADP1 database's mmseqs2-style cluster IDs and BERDL centroid gene IDs, mapping all 4,891 BERDL clusters to 4,081 unique ADP1 clusters despite 0% direct string match. *(confidence: high)*
- Core metabolism is highly conserved across the 14 Acinetobacter genomes, with 1,248 of 1,330 unique reactions (94%) shared by all genomes and only 20 genome-unique. *(confidence: high)*
- Essential genes are far more annotation-rich than dispensable ones, with 33% versus 5% carrying COG assignments and 92% versus 53% carrying KEGG KO assignments. *(confidence: high)*
- FBA flux predictions and TnSeq essentiality calls agreed for 73.8% of the 866 genes with both measurements, with the discordant 26% flagged as candidates for model refinement or regulatory effects. *(confidence: high)*
- Four of five connection types between the ADP1 database and BERDL collections matched at over 90%, including 100% of genome IDs and compounds and 91% of reactions, demonstrating deep integration with the lakehouse. *(confidence: high)*
- Gene essentiality in ADP1 is media-dependent, with 499 genes essential on minimal media versus 346 on LB, reflecting the additional biosynthetic burden of minimal media. *(confidence: high)*
- Mutant growth fitness across 8 carbon sources was only moderately correlated (mean pairwise r = 0.44), with urea catabolism standing apart as nearly independent of quinate and other conditions. *(confidence: medium)*
- Protein abundance measured across 7 engineered strains for 2,383 genes shows high cross-strain correlation, indicating the engineered modifications have targeted rather than global proteome effects. *(confidence: medium)*
- The Acinetobacter baylyi ADP1 explorer integrates a user-provided SQLite database of 15 tables (461,522 rows, 135 MB) whose central genome_features table holds 5,852 genes with 51 annotation columns spanning six data modalities. *(confidence: high)*
- The roughly 8% of essential genes lacking KEGG KO assignments are promising candidates for discovering novel essential functions. *(confidence: medium)*

## Topics

- [Topic: Adp1 Model System](../topics/adp1-model-system.md)
- [Topic: Functional Dark Matter](../topics/functional-dark-matter.md)
- [Topic: Gene Fitness](../topics/gene-fitness.md)
- [Topic: Metabolic Pathways](../topics/metabolic-pathways.md)
- [Topic: Pangenome Architecture](../topics/pangenome-architecture.md)

## Data

- [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md)
- [Kbase Msd Biochemistry](../data/kbase-msd-biochemistry.md)
- [Kbase Uniref](../data/kbase-uniref.md)
- [Kescience Fitnessbrowser](../data/kescience-fitnessbrowser.md)
- [Phagefoundry](../data/phagefoundry.md)

## Authors

- [Beril Admin](../authors/0009-0007-0287-2979.md)
- [Paramvir S. Dehal](../authors/0000-0001-5810-2497.md)

[Open the full report →](../../../projects/acinetobacter_adp1_explorer/REPORT.md)

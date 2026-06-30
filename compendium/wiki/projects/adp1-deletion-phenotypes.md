# Adp1 Deletion Phenotypes

This project systematically mapped gene fitness across 8 carbon sources in *Acinetobacter baylyi* ADP1 using a complete deletion collection, asking which genes are essential and how their importance varies by growth condition. The analysis revealed that the fitness landscape is largely a continuum rather than discrete functional modules—with the key insight that genes dispensable in the lab are significantly less conserved across wild Acinetobacter species, linking gene dispensability to pangenome evolution. Condition-specific gene sets recovered the known metabolic architecture of ADP1 and showed that each carbon source imposes largely independent fitness requirements, providing a foundation for predicting metabolic genes from phenotype alone.

## Key findings

- Growth ratios are single-timepoint measurements with unknown technical noise, so the condition-specificity analysis assumes cross-condition variation reflects biology rather than measurement error. *(confidence: high)*
- The complete 2,034-gene matrix excludes 499 essential genes and 316 genes with incomplete data, biasing the analysis toward dispensable genes with successful deletion mutants. *(confidence: high)*
- Cross-referencing with BERDL pangenome data links gene dispensability to pangenome status, suggesting the least-conserved Acinetobacter genes are tied to dispensability through evolutionary retention pressure. *(confidence: medium)*
- Each carbon source imposes a largely independent set of gene requirements in ADP1, reflecting the diverse metabolic entry points of the conditions tested. *(confidence: medium)*
- The top condition-specific genes for each carbon source correspond precisely to the expected metabolic pathways (e.g., urease subunits for urea, protocatechuate/quinate degradation for quinate), recovering ADP1's metabolic architecture from phenotype alone. *(confidence: high)*
- 625 genes (31% of the complete matrix) have a condition-specificity score >= 1.0, concentrating their growth importance on a single carbon source. *(confidence: high)*
- Across the 8 carbon sources tested on the ADP1 deletion collection, conditions partition into demanding, moderate, and robust tiers, with urea most demanding (97.9% of genes defective) and quinate most robust (only 1.6% defective). *(confidence: high)*
- Hierarchical clustering of ADP1 genes by their 8-condition growth profiles yields only a weak K=3 structure (silhouette 0.24) with no FDR-surviving functional enrichment, indicating gene essentiality varies continuously rather than falling into discrete functional modules. *(confidence: high)*
- Hypothetical and unannotated proteins are massively enriched among the dispensable genes missing from the deletion collection, with 25 completely unannotated (q=2.4x10^-25) and 48 annotated as hypothetical protein (q=3.0x10^-4). *(confidence: high)*
- Of 2,593 TnSeq-dispensable ADP1 genes, the 272 (10.5%) lacking deletion-collection growth data are systematically shorter, less annotated, and less conserved (76.5% pangenome core vs 93.3%, p=1.4x10^-20) than genes with coverage. *(confidence: high)*
- PCA of the 2,034x8 ADP1 growth matrix shows that 5 principal components capture 82% of the variance, so the 8 carbon sources provide roughly 5 independent dimensions of phenotypic information. *(confidence: high)*
- The sole discrete phenotypic module in the ADP1 dataset is a set of 24 aromatic-degradation-pathway genes with extreme quinate-specific growth defects (mean z-score -7.28 on quinate). *(confidence: high)*
- ADP1 condition-specificity profiles could be compared with RB-TnSeq data from the Fitness Browser for other organisms grown on overlapping carbon sources to test whether the same pathways are condition-specific across species. *(confidence: medium)*
- Condition-specific gene sets could be used to infer regulatory relationships, since genes that are co-specific for a condition may share transcriptional regulators. *(confidence: low)*

## Topics

- [Topic: Adp1 Model System](../topics/adp1-model-system.md)
- [Topic: Functional Dark Matter](../topics/functional-dark-matter.md)
- [Topic: Gene Fitness](../topics/gene-fitness.md)
- [Topic: Metabolic Pathways](../topics/metabolic-pathways.md)
- [Topic: Pangenome Architecture](../topics/pangenome-architecture.md)

## Data

- [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md)

## Authors

- [Paramvir S. Dehal](../authors/0000-0001-5810-2497.md)

[Open the full report →](../../../projects/adp1_deletion_phenotypes/REPORT.md)

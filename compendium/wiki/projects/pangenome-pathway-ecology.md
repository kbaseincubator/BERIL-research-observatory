# Pangenome Pathway Ecology

This project investigates whether microbial pangenome structure—specifically how "open" or "closed" a pangenome is—correlates with metabolic pathway diversity and reflects ecological strategy. The core hypothesis is that generalist species maintain open pangenomes (high rates of gene acquisition) and metabolic flexibility, while specialist species have closed pangenomes and conserved core metabolic capabilities. Analysis across 27,690 microbial species uses pangenome metrics, GapMind pathway completeness, AlphaFold-predicted structural variation, and phylogenetic distances to test whether these associations hold independent of evolutionary history.

## Key findings

- AlphaEarth structural embeddings cover only about 28% of genomes, so structural-distance analyses must filter to species with sufficient coverage and may be biased by underrepresented isolate types. *(confidence: high)*
- GapMind pathway predictions vary in confidence and are probabilistic rather than experimental, limiting the certainty of metabolic-completeness inferences. *(confidence: high)*
- The project is at the proposal stage with only the Phase 1 notebook implemented and no data files or figures generated, so no empirical findings can yet be assessed. *(confidence: high)*
- A planned test asks whether open pangenomes show greater within-species structural diversity by correlating AlphaEarth embedding distances with pangenome openness. *(confidence: medium)*
- Closed pangenomes (low auxiliary/singleton ratios) are hypothesized to reflect specialist species with reduced gene acquisition rates and core metabolic pathway conservation. *(confidence: medium)*
- Open pangenomes (high auxiliary/singleton gene ratios) are hypothesized to reflect generalist species with greater horizontal gene transfer within ecological niches and increased metabolic pathway flexibility. *(confidence: medium)*
- The central hypothesis tests whether open pangenomes indicate generalist species with broader niche adaptation and greater metabolic pathway diversity, while closed pangenomes indicate specialists with conserved core pathways. *(confidence: medium)*
- Pangenome openness is operationalized as the ratio of variable genes to total genes, openness = (aux_genes + singleton_genes) / total_genes, a standard measure judged sound in independent review. *(confidence: high)*
- The analysis draws on BERDL pangenome, GapMind pathway, AlphaEarth structural embedding, and phylogenetic-tree-distance tables from the kbase_ke_pangenome database. *(confidence: high)*
- The design controls for phylogenetic signal by relating openness to evolutionary distances using phylogenetic independent contrasts (PIC) or PGLS so that associations are independent of phylogeny. *(confidence: medium)*
- The framework is designed to compute pangenome openness distributions and GapMind pathway coverage across all 27,690 microbial species in the pangenome resource. *(confidence: medium)*
- Adding multiple-testing correction (Bonferroni or FDR) when testing many openness-pathway correlations would strengthen the statistical rigor of the correlation analysis. *(confidence: medium)*
- Executing the Phase 1 notebook on BERDL JupyterHub would generate baseline data, reveal bugs, and provide the foundation for the remaining analysis phases. *(confidence: medium)*

## Topics

- [Topic: Environment Biogeography](../topics/environment-biogeography.md)
- [Topic: Functional Dark Matter](../topics/functional-dark-matter.md)
- [Topic: Metabolic Pathways](../topics/metabolic-pathways.md)
- [Topic: Microbial Ecotypes](../topics/microbial-ecotypes.md)
- [Topic: Mobile Genetic Elements](../topics/mobile-genetic-elements.md)
- [Topic: Pangenome Architecture](../topics/pangenome-architecture.md)

## Authors

- [William J. Riehl](../authors/0000-0002-3405-2744.md)

[Open the full report →](../../../projects/pangenome_pathway_ecology/REPORT.md)

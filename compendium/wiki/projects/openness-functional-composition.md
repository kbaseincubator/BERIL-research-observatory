# Openness Functional Composition

This project tests whether the functional specialization of accessory genomes scales with pangenome openness: species that acquire more novel genes through horizontal gene transfer show stronger enrichment of mobile elements and defense systems in their accessory genomes compared to species with closed pangenomes. Building on a prior finding of universal "two-speed genome" patterns across 32 diverse species, this work stratifies ~40 species into openness quartiles to ask whether open pangenomes intensify the mobile-element and defense enrichment seen in novel genes.

## Key findings

- Genome count, phylum effects, and genome size are potential confounders that must be controlled when relating openness to COG enrichment. *(confidence: medium)*
- The study is in progress with notebooks created but not yet executed, so no empirical enrichment results are available. *(confidence: high)*
- Hypothesis H1 predicts that open pangenomes show higher mobile-element (L) and defense (V) COG enrichment in novel genes than closed pangenomes. *(confidence: medium)*
- Hypothesis H2 predicts that closed pangenomes show higher metabolic diversity (COG E, C, G categories) concentrated in core genes. *(confidence: medium)*
- Openness metrics and COG annotations are drawn from BERDL pangenome tables, joining pangenome openness metrics, gene-cluster core/auxiliary/singleton classifications, and eggNOG COG categories at billion-row scale. *(confidence: high)*
- The analysis stratifies roughly 40 species (each with at least 50 genomes) into openness quartiles and computes COG enrichment per quartile across core, auxiliary, and singleton gene clusters. *(confidence: medium)*
- The project hypothesizes that species acquiring more novel genes (more open pangenomes) also show stronger mobile-element and defense enrichment, linking genome fluidity to functional specialization of the accessory genome. *(confidence: medium)*
- This project asks whether pangenome openness predicts the magnitude of COG functional enrichment in novel versus core genes. *(confidence: high)*
- A prior cog_analysis project found a universal two-speed genome pattern in which novel genes are enriched in mobile elements (COG L: +10.88%) and defense (COG V: +2.83%). *(confidence: high)*
- A prior pangenome_openness project found no correlation between pangenome openness and eco-phylo dynamics, motivating stratification by gene function as a next step. *(confidence: medium)*
- The prior cog_analysis project established universal L/V enrichment in novel genes across 32 species and 9 phyla but did not test whether this enrichment scales with openness. *(confidence: high)*
- If open pangenomes show stronger L/V enrichment, the result would extend the two-speed genome model to show the pattern is not merely universal but scales with genome fluidity. *(confidence: low)*
- If openness does not modulate enrichment, the two-speed pattern would be confirmed as truly universal and driven by the nature of HGT events rather than their frequency. *(confidence: low)*

## Topics

- [Topic: Functional Dark Matter](../topics/functional-dark-matter.md)
- [Topic: Metabolic Pathways](../topics/metabolic-pathways.md)
- [Topic: Microbial Ecotypes](../topics/microbial-ecotypes.md)
- [Topic: Mobile Genetic Elements](../topics/mobile-genetic-elements.md)
- [Topic: Pangenome Architecture](../topics/pangenome-architecture.md)

## Authors

- [Justin Reese](../authors/0000-0002-2170-2250.md)

[Open the full report →](../../../projects/openness_functional_composition/REPORT.md)

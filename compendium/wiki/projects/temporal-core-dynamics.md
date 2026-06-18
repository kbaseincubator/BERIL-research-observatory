# Temporal Core Dynamics

This project investigates whether a bacterial species' core genome—the set of genes present in nearly all strains—remains stable over time or changes as the species is sampled across decades. Using Pseudomonas aeruginosa and Acinetobacter baumannii as model organisms, the project applies temporal analysis to thousands of sequenced genomes with collection dates to test whether genes "come and go" from core status and whether apparent reductions in core genome size among heavily-sampled species reflect genuine evolutionary dynamics rather than sampling bias. While the methodological approach is rigorous, the analysis has not yet been executed, leaving the key question unresolved: does the core genome truly erode over evolutionary and ecological time?

## Key findings

- A pitfall was flagged in the functional notebook: eggnog_mapper_annotations was joined on gene_id instead of the correct gene_cluster_id, which may return no results or incorrect annotations. *(confidence: high)*
- No conclusions can yet be drawn because the analysis has not been executed: all four notebooks contain code without outputs and the data and figures directories are empty. *(confidence: high)*
- Variable date granularity may bias temporal inferences, since using July 1st as a midpoint for a year-only date like "2015" could introduce systematic bias. *(confidence: medium)*
- By tracking core erosion, turnover, and functional enrichment, the project seeks to distinguish genuine population dynamics from sampling bias effects. *(confidence: medium)*
- Species sampled over longer time periods are hypothesized to show smaller cores, potentially explaining why heavily-sampled species exhibit reduced core genomes. *(confidence: medium)*
- The analysis aims to functionally characterize early-leaving core genes, expecting mobile elements among early-exit genes and housekeeping functions in the stable core. *(confidence: medium)*
- The central hypothesis is that the core genome is not static and that genes transition in and out of core status over ecological and evolutionary time. *(confidence: medium)*
- Core membership is tested at multiple presence thresholds (90% relaxed, 95% standard, 99% strict) to assess the robustness of temporal core erosion to definition choice. *(confidence: high)*
- P. aeruginosa and A. baumannii were chosen as model species because both are semi-environmental with clinical crossover, making them ideal for temporal dynamics analysis. *(confidence: high)*
- Roughly three-quarters of genomes carry collection dates (P. aeruginosa 73.4% of 6,760; A. baumannii 75.5% of 6,647), providing the dated genome sets for temporal analysis. *(confidence: high)*
- The project asks how core genome composition changes over sampling time and whether genes transition in and out of core status. *(confidence: high)*
- Two complementary approaches are used: cumulative expansion sorting genomes chronologically and fixed 2-year time windows with a minimum of 30 genomes per window. *(confidence: high)*
- A permutation test that shuffles collection dates and recalculates decay curves could establish whether observed temporal patterns exceed random sampling effects. *(confidence: medium)*
- Identifying genes in the stable core of both species could reveal truly universal essential functions across the two semi-environmental pathogens. *(confidence: low)*

## Topics

- [Topic: Environment Biogeography](../topics/environment-biogeography.md)
- [Topic: Functional Dark Matter](../topics/functional-dark-matter.md)
- [Topic: Gene Fitness](../topics/gene-fitness.md)
- [Topic: Microbial Ecotypes](../topics/microbial-ecotypes.md)
- [Topic: Mobile Genetic Elements](../topics/mobile-genetic-elements.md)
- [Topic: Pangenome Architecture](../topics/pangenome-architecture.md)

## Authors

- [Paramvir S. Dehal](../authors/0000-0001-5810-2497.md)

[Open the full report →](../../../projects/temporal_core_dynamics/REPORT.md)

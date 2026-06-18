# Conservation Fitness Synthesis

This synthesis connected transposon mutant fitness data from the Fitness Browser (~194,000 genes across 43 bacteria) to the KBase pangenome (27,690 microbial species) to ask whether a gene's importance for survival relates to its evolutionary conservation. The core finding inverts a naive model: the conserved genome is the most functionally active part of the genome, not the most inert — core genes are 1.2× more likely to be metabolic burdens and show strong condition-specific effects, suggesting that laboratory conditions are an impoverished proxy for natural selection, where trade-off genes remain conserved because they are essential in soil, biofilm, or host-associated environments that the lab does not capture.

## Key findings

- The reported 16pp fitness-conservation gradient is undermined by a discrepancy: Figure 1 shows essential genes at 86% and always-neutral at 78% (an ~8pp gradient) rather than the 82% and 66% stated in the prose, because the notebook computed percentages only over successfully mapped genes. *(confidence: high)*
- The synthesis reports two essential-gene core rates without reconciling them: 82% (from fitness_effects_conservation across 43 organisms, counting unmapped essential genes as non-core) versus 86% (from conservation_vs_fitness across 33 organisms with high mapping coverage). *(confidence: medium)*
- Throughout the synthesis, percent core is computed as the fraction of all protein-coding genes (including unmapped genes of unknown conservation) that are core, which treats unmapped genes as not confirmed core and can shift reported gradients. *(confidence: medium)*
- Connecting the Fitness Browser (RB-TnSeq fitness for ~194,000 genes across 43 bacteria) to the KBase pangenome (gene cluster conservation across 27,690 microbial species) shows that the conserved genome is the most functionally active part of the genome rather than the most inert. *(confidence: high)*
- Laboratory conditions are an impoverished proxy for natural selection because a gene that appears costly in rich media may be essential in soil, biofilm, host tissue, or other natural conditions, so the lab captures the cost of maintaining genes while the pangenome captures the evolutionary pressure to keep them. *(confidence: medium)*
- A quantitative fitness-conservation gradient runs from essential genes (82% core) to always-neutral genes (66% core) across 194,216 protein-coding genes in 43 bacteria, so more important genes are more conserved but the effect is modest. *(confidence: high)*
- A selection-signature matrix identifies 28,017 genes that are simultaneously costly in the lab and conserved in the pangenome as the strongest evidence for purifying selection in natural environments, while 5,526 costly-and-dispensable genes are candidates for ongoing gene loss. *(confidence: high)*
- Contrary to a housekeeping model, core genes are MORE likely to be burdens, with 24.4% showing positive fitness when deleted versus 19.9% for accessory genes, making the conserved genome the most functionally active part of the genome rather than the most inert. *(confidence: high)*
- Contrary to the streamlining hypothesis, accessory genes are LESS costly than core genes rather than systematically burdensome, and module families spanning more organisms do not have higher core fractions (rho=-0.01, p=0.91). *(confidence: high)*
- Core genes are 1.78x more likely to have strong condition-specific phenotypes and 1.29x more likely to be trade-offs that are both important and burdensome depending on conditions. *(confidence: high)*
- ICA decomposition identified 1,116 co-regulated fitness modules across 32 organisms that are significantly enriched in core genes (86% core vs 81.5% baseline, OR=1.46, p=1.6e-87), with 59% of modules being more than 90% core genes. *(confidence: high)*
- The burden paradox is function-specific: motility and chemotaxis (+7.8pp), RNA metabolism (+12.9pp), and protein metabolism (+6.2pp) genes drive the core-burden excess, while cell wall genes reverse it because non-core cell wall genes are more burdensome. *(confidence: high)*
- Connecting lab fitness to AlphaEarth environmental data could test whether organisms from more variable environments carry more trade-off genes in their core, bridging lab phenotypes to natural niche context. *(confidence: medium)*
- The 5,526 costly-and-dispensable genes are candidates for ongoing gene loss and an open opportunity to characterize whether they are mobile elements or recently acquired genes on the way out. *(confidence: medium)*

## Topics

- [Topic: Environment Biogeography](../topics/environment-biogeography.md)
- [Topic: Gene Fitness](../topics/gene-fitness.md)
- [Topic: Metabolic Pathways](../topics/metabolic-pathways.md)
- [Topic: Mobile Genetic Elements](../topics/mobile-genetic-elements.md)
- [Topic: Pangenome Architecture](../topics/pangenome-architecture.md)

## Authors

- [Paramvir S. Dehal](../authors/0000-0001-5810-2497.md)

[Open the full report →](../../../projects/conservation_fitness_synthesis/REPORT.md)

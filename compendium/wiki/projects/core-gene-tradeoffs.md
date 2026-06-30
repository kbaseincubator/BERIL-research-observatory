# Core Gene Tradeoffs

This project investigated why core genes in bacterial pangenomes are more likely to impose fitness costs when deleted compared to accessory genes, seemingly contradicting the model that accessory genes are metabolic burdens. The key finding resolves this paradox: core genes encode energetically expensive functions like motility, ribosomal machinery, and RNA metabolism that are essential for survival in natural environments, even though they appear costly under lab conditions. The project identified 28,017 genes that are simultaneously costly in the lab and conserved across strains, providing direct evidence that natural selection maintains them despite their measured metabolic burden.

## Key findings

- Lab conditions capture only a fraction of the environmental conditions bacteria face in nature, and Fitness Browser condition types are biased toward what is experimentally convenient rather than ecologically relevant. *(confidence: high)*
- The operational definition of burden (fit > 1) may reflect trade-offs rather than true dispensability, and the 90% identity threshold for DIAMOND matching may miss rapidly evolving genes. *(confidence: medium)*
- Core genes accumulate more condition-dependent trade-offs because they participate in more pathways carrying both costs and benefits across environments. *(confidence: medium)*
- Core genome genes are more likely than accessory genes to show positive fitness effects when deleted (lab burden), contradicting the streamlining model that frames accessory genes as the metabolic burden. *(confidence: high)*
- The 28,017 costly-but-conserved genes constitute the strongest evidence that purifying selection maintains genes despite their metabolic cost because they are essential in natural environments not captured by lab experiments. *(confidence: medium)*
- The burden paradox resolves once lab conditions are recognized as an impoverished proxy for nature, since core genes encode energetically expensive functions like motility, ribosomal components, and RNA metabolism that are essential in natural environments. *(confidence: medium)*
- A class of 5,526 costly-and-dispensable genes that are burdensome and not universally conserved are candidates for ongoing gene loss. *(confidence: medium)*
- A selection-signature matrix crossing lab fitness cost with pangenome conservation identifies 28,017 costly-but-conserved genes that natural selection maintains despite their lab-measured cost. *(confidence: high)*
- Genes with strong condition-specific fitness effects are more likely to be core, reinforcing that the conserved genome is functionally active rather than inert. *(confidence: medium)*
- Motility exemplifies the burden paradox: energetically expensive flagellar machinery is conserved because it is essential for chemotaxis in natural environments despite being costly under lab conditions. *(confidence: high)*
- The core-gene burden paradox is function-specific, driven by Protein Metabolism (+6.2pp), Motility (+7.8pp), and RNA Metabolism (+12.9pp), while Cell Wall reverses with non-core genes being more burdensome (-14.1pp). *(confidence: high)*
- True trade-off genes, important in some conditions and burdensome in others, number 25,271 (17.8%) and are 1.29x more likely to be core (OR=1.29, p=1.2e-44). *(confidence: high)*
- Strain-dependent gene essentiality across pangenomes suggests conservation reflects selection across diverse environments rather than universal essentiality, opening a path to interpret core-gene burden through pan-genome-aware essentiality. *(confidence: low)*
- Validating the costly-but-conserved gene set against fitness measurements in natural conditions such as soil or biofilm would test whether lab burden is offset by environmental essentiality. *(confidence: low)*

## Topics

- [Topic: Environment Biogeography](../topics/environment-biogeography.md)
- [Topic: Gene Fitness](../topics/gene-fitness.md)
- [Topic: Metabolic Pathways](../topics/metabolic-pathways.md)
- [Topic: Pangenome Architecture](../topics/pangenome-architecture.md)

## Authors

- [Paramvir S. Dehal](../authors/0000-0001-5810-2497.md)

[Open the full report →](../../../projects/core_gene_tradeoffs/REPORT.md)

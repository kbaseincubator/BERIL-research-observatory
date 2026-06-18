# Prophage Ecology

This project mapped prophage gene modules across 27,702 bacterial species in the BERDL pangenome to understand how prophage composition varies with environment and host phylogeny. The central finding is that environment explains substantially more variance in prophage module composition than host phylogeny, with evidence for a two-tier prophage organization: universal core modules (packaging, lysis, lysogenic regulation) that function as tightly linked units, and variable accessory modules (head, tail, anti-defense) that show strong environmental enrichment, particularly in human-associated niches.

## Key findings

- Because genome size is the dominant predictor of prophage burden, residual confounding cannot be fully excluded despite stratification and partial correlations, since larger genomes carry more genes of all types. *(confidence: medium)*
- Prophages were identified from eggNOG functional annotations rather than dedicated prophage detection tools, likely inflating prevalence by including domesticated remnants and bacterial homologs with an uncharacterized false positive rate. *(confidence: high)*
- The NMDC validation is indirect because taxonomy-based prophage burden inference assumes genus-level conservation of prophage content, which may not hold for recently acquired or lost prophages. *(confidence: medium)*
- Anti-defense module depletion in freshwater and animal-associated environments alongside enrichment in human-associated niches suggests host-phage coevolutionary arms races are most intense where bacterial immune systems are under stronger selection. *(confidence: medium)*
- Module-level and lineage-level prophage ecology are decoupled, with modules showing environment effects beyond phylogeny while lineages do not, supporting modular exchange rather than whole-phage adaptation to environments. *(confidence: medium)*
- Prophage burden inferred from NMDC samples correlates positively with pH and temperature, with the alkaline-pH association consistent with pH-sensitive stress-induced prophage induction. *(confidence: medium)*
- The near-universal packaging, lysis, and regulatory modules likely include many domesticated prophage remnants under purifying selection, so the structurally variable modules are more informative for prophage ecology. *(confidence: medium)*
- All 27,702 bacterial species in the BERDL pangenome carry prophage-associated gene clusters, with packaging, lysis, and lysogenic-regulation modules near-universal while head, tail, and anti-defense modules are structurally variable. *(confidence: high)*
- Co-occurrence testing across 15 phylogenetically stratified species confirms that core packaging, lysis, and lysogenic-regulation modules cluster on the same contigs as physically linked functional units, whereas integration genes explicitly do not co-occur. *(confidence: high)*
- Constrained permutation null models identify eight significant module-by-environment enrichments, with tail, head morphogenesis, and anti-defense modules enriched in human-associated bacteria beyond phylogenetic expectation. *(confidence: high)*
- Environment explains substantially more variance in prophage module composition than host phylogeny, with PERMANOVA effect sizes of F=30.04 for environment versus F=6.17 for phylogeny. *(confidence: high)*
- Genome size is the single dominant predictor of prophage burden, yet environment still significantly affects prophage module count within each genome size quartile, showing the environmental signal is not a genome size artifact. *(confidence: high)*
- Taxonomy-based inference of prophage burden across 6,365 NMDC metagenomic samples reveals 57 significant module-abiotic correlations, with head morphogenesis, tail, and anti-defense modules concordant between pangenome enrichment and metagenomic signal. *(confidence: high)*
- TerL terminase clustering yields 10,991 lineages whose ecology largely mirrors host ecology, with no individual lineage showing environment-specific enrichment beyond phylogenetic expectation but a mix of 325 specialist and 499 generalist lineages. *(confidence: high)*
- Cross-referencing environment-enriched modules with known prophage induction triggers such as the SOS response, pH stress, and temperature shifts could mechanistically explain the pH and temperature correlations observed in NMDC data. *(confidence: medium)*
- Running geNomad or VIBRANT on representative genomes would estimate false positive and negative rates of the annotation-based approach and calibrate the module prevalence estimates. *(confidence: medium)*

## Topics

- [Topic: Environment Biogeography](../topics/environment-biogeography.md)
- [Topic: Functional Dark Matter](../topics/functional-dark-matter.md)
- [Topic: Microbiome Engineering](../topics/microbiome-engineering.md)
- [Topic: Mobile Genetic Elements](../topics/mobile-genetic-elements.md)
- [Topic: Pangenome Architecture](../topics/pangenome-architecture.md)

## Data

- [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md)
- [Nmdc Arkin](../data/nmdc-arkin.md)

## Authors

- [Adam P. Arkin](../authors/0000-0002-4999-2931.md)

[Open the full report →](../../../projects/prophage_ecology/REPORT.md)

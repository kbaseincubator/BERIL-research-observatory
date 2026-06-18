# Gene Function Ecological Agora

This project generalized the Alm 2006 methodology for detecting gene-family expansion signatures to the full bacterial domain, building a horizontal gene transfer and innovation atlas of 13.7 million producer/participation scores and 17 million ranked acquisition events across 18,989 GTDB species. The atlas revealed that specific bacterial clades innovate particular gene functions through distinct evolutionary strategies: Cyanobacteria actively innovate photosystem II through exchange with other clades, while Mycobacteriaceae isolate mycolic-acid innovations within their family, and that the recent-to-ancient ratio of acquired genes itself serves as a signature of HGT activity by function class.

## Key findings

- Recent between-species gain attribution and within-species pangenome openness are uncorrelated (Spearman r=-0.011 across 894 genera), so pangenome openness is not a valid cross-substrate validation of the acquisition-depth signal. *(confidence: high)*
- The Alm 2006 r~0.74 correlation between histidine-kinase count and lineage-specific expansion is NOT reproduced at full GTDB scale, recovering only modest correlations (r=0.10-0.29) across 18,989 genomes. *(confidence: high)*
- The PSII Innovator verdict is strongly rank-dependent (STABLE at genus, Innovator-Exchange at class, Innovator-Isolated at phylum), so the class rank must be chosen on biological grounds rather than read off any single resolution. *(confidence: medium)*
- Atlas-level innovation findings are made robust by convergence across three independent measurement substrates: Sankoff-parsimony effect size, sample-biome ecology metadata, and per-strain phenotype tables. *(confidence: high)*
- The Producer × Participation framework provides a direction-agnostic per-clade categorization (Innovator-Isolated / Innovator-Exchange / Sink-Broker-Exchange / Stable) usable at deep ranks where full DTL reconciliation is intractable. *(confidence: high)*
- All three pre-registered hypothesis KO sets (PSII, mycolic-acid, PUL) show near-zero MGE-machinery rates against a 1.37% atlas baseline, meaning these gene families are not themselves phage, transposase, integrase, or plasmid genes. *(confidence: high)*
- Architectural promiscuity correlates with HGT propensity: mixed-category KOs carry a median of 46 Pfam architectures per KO versus 1 for PSII, mirroring the 'modular systems exchange more' pattern. *(confidence: medium)*
- Cyanobacteria are confirmed as Innovator-Exchange on photosystem II at the Cyanobacteriia class rank (producer d=+1.50, consumer d=+0.70), the appropriate rank since PSII predates Cyanobacteria diversification. *(confidence: high)*
- Mycobacteriaceae are confirmed as Innovator-Isolated on the mycolic-acid pathway at family and order ranks (producer d=+0.31, consumer d=-0.19), indicating high paralog expansion with low cross-clade exchange. *(confidence: high)*
- Pre-registered atlas clades are significantly enriched in their expected biomes, including Mycobacteriaceae host-pathogen (7.88x, p<10^-45), Cyanobacteriia photic aquatic (2.77x, p<10^-52), and Bacteroidota gut/rumen (1.40x, p<10^-35). *(confidence: high)*
- The mycolic-acid Innovator-Isolated signature is concentrated in host-pathogen-niche mycobacteria rather than soil mycobacteria, refining the original family-level finding. *(confidence: medium)*
- The project built a bacterial-domain HGT/innovation atlas of 13.7M producer/participation scores and 17M Sankoff gain events with recipient-rank acquisition attribution across 18,989 GTDB r214 species representatives. *(confidence: high)*
- The ratio of recent-to-ancient gain events is itself a function-class signature, with CRISPR-Cas highly recent-skewed (24.5x ratio, HGT-active) and strict housekeeping genes ancient-skewed (~1x, vertical inheritance). *(confidence: high)*
- Composition-based donor inference at deep ranks remains a future direction, blocked because per-CDS sequence is not in BERDL queryable schemas; tree-based donor inference shipped only as an exploratory layer. *(confidence: medium)*
- Testing whether high-exchange KOs are mobile-element-mediated by flagging phage, plasmid, and integron context per gain event is an identified next step toward a mechanistic explanation of cross-clade gene flow. *(confidence: medium)*

## Topics

- [Topic: Environment Biogeography](../topics/environment-biogeography.md)
- [Topic: Functional Dark Matter](../topics/functional-dark-matter.md)
- [Topic: Gene Fitness](../topics/gene-fitness.md)
- [Topic: Metabolic Pathways](../topics/metabolic-pathways.md)
- [Topic: Microbial Ecotypes](../topics/microbial-ecotypes.md)
- [Topic: Mobile Genetic Elements](../topics/mobile-genetic-elements.md)
- [Topic: Pangenome Architecture](../topics/pangenome-architecture.md)

## Data

- [Kbase Genomes](../data/kbase-genomes.md)
- [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md)
- [Kbase Uniref](../data/kbase-uniref.md)
- [Kescience Fitnessbrowser](../data/kescience-fitnessbrowser.md)
- [Nmdc Arkin](../data/nmdc-arkin.md)

## Authors

- [Adam P. Arkin](../authors/0000-0002-4999-2931.md)

[Open the full report →](../../../projects/gene_function_ecological_agora/REPORT.md)

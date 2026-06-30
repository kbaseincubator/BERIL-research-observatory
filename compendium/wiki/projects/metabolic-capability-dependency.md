# Metabolic Capability Dependency

This project tested whether complete metabolic pathways encoded in bacterial genomes can be functionally neutral under laboratory conditions, and whether fitness-neutral "latent capability" pathways follow patterns predicted by the Black Queen hypothesis. Across 1,695 pathway-organism pairs from 48 bacteria, the researchers found that 15.8% of genomically complete pathways showed no detectable fitness importance, with carbon utilization pathways 3.7-fold more likely to be latent than amino acid biosynthesis pathways. Pangenome openness correlated strongly with per-clade latent capability rates, supporting the Black Queen hypothesis at the community level while revealing that metabolic dependencies vary predictably by pathway type and that within-species metabolic diversity is widespread.

## Key findings

- Linking Fitness Browser organisms to GapMind species clades via NCBI taxonomy IDs returned zero matches because the gtdb_metadata taxid column contained boolean strings rather than numeric taxids, so analyses relied on organism-level aggregates without explicit clade linkage. *(confidence: high)*
- The H2b openness-latency correlation has a non-independence problem because multiple Fitness Browser organisms map to the same GapMind species clade and share an identical pangenome openness value. *(confidence: medium)*
- The contrast between supported clade-level openness and unsupported pathway-level conservation suggests the Black Queen signal operates at the level of genome dynamics and community context rather than in per-pathway cross-genome conservation ratios. *(confidence: medium)*
- The latent fraction is moderately sensitive to classification thresholds, ranging from 4.7% to 21.1% across 16 threshold combinations, but the qualitative conclusion that a non-trivial fraction of complete pathways are fitness-neutral holds across the full range tested. *(confidence: medium)*
- This work provides a systematic quantification of the latent capability fraction across diverse bacteria, yielding the testable prediction that carbon source utilization pathways are 3.7-fold more likely to be latent than amino acid biosynthesis pathways (24.3% vs 6.5%). *(confidence: medium)*
- Across 1,695 pathway-organism pairs from 48 organisms, 15.8% of genomically complete pathways were classified as latent capabilities, encoded by the genome but showing no detectable fitness importance under tested conditions. *(confidence: high)*
- After aggregating 41 organisms to 22 unique species clades, the per-clade fraction of latent capabilities correlated positively with pangenome openness (Spearman rho = 0.69, p = 0.0004), supporting the Black Queen framework at the species level (H2b). *(confidence: high)*
- All 10 target species with at least 50 genomes and at least 15 variable pathways showed meaningful metabolic clustering (all silhouette scores > 0.2), demonstrating that within-species metabolic pathway heterogeneity is a general feature. *(confidence: high)*
- Metabolic clusters correlated significantly with isolation environment in the copiotrophs Salmonella enterica and Phenylobacterium sp., but not in marine oligotrophs such as Stutzerimonas and Alteromonas. *(confidence: medium)*
- Pathway category strongly predicted dependency class, with carbon source utilization pathways most likely to be latent (24.3%) while amino acid biosynthesis pathways were predominantly active (63.5% active, 6.5% latent). *(confidence: high)*
- Pathway-level conservation rates did not differ between latent capabilities and active dependencies, so the Black Queen Hypothesis was not supported at the per-pathway conservation level (H2a). *(confidence: high)*
- Identifying lineages with recent gene loss events in pathways classified as latent and verifying that these represent actual deletion events in the phylogeny could provide longitudinal validation of the latent capability framework. *(confidence: medium)*
- Replacing pathway-level conservation with per-gene dN/dS or gene presence/absence across a phylogeny could directly test the Black Queen prediction of progressive gene loss. *(confidence: medium)*

## Topics

- [Topic: Environment Biogeography](../topics/environment-biogeography.md)
- [Topic: Gene Fitness](../topics/gene-fitness.md)
- [Topic: Metabolic Pathways](../topics/metabolic-pathways.md)
- [Topic: Microbial Ecotypes](../topics/microbial-ecotypes.md)
- [Topic: Pangenome Architecture](../topics/pangenome-architecture.md)

## Data

- [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md)
- [Kescience Fitnessbrowser](../data/kescience-fitnessbrowser.md)

## Authors

- [Christopher Neely](../authors/0000-0002-2620-8948.md)
- [Sierra Moxon](../authors/0000-0002-8719-7760.md)

[Open the full report →](../../../projects/metabolic_capability_dependency/REPORT.md)

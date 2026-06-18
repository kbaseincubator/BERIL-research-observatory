# Cofitness Coinheritance

This project tested whether laboratory-measured functional coupling (co-fitness from the Fitness Browser) predicts which genes co-occur across genomes in 9 natural bacterial populations. While pairwise co-fitness weakly but consistently predicts co-occurrence across species, coordinated multi-gene modules show a much stronger co-inheritance signal—revealing that shared regulation of gene sets, not just pairwise functional similarity, is what most strongly constrains bacterial pangenome structure.

## Key findings

- A prevalence ceiling limits the analysis because most Fitness Browser genes map to core clusters above 95% prevalence, where phi approaches zero for both cofit and random pairs due to negligible presence/absence variance. *(confidence: high)*
- Phylogenetic distance stratification is limited to near and medium strata because most species lack genomes in the far stratum, constraining the ability to fully disentangle functional coupling from shared-ancestry signal. *(confidence: medium)*
- The two most phylogenetically diverse Ralstonia organisms have zero co-fitness data in the Fitness Browser, excluding the species that would likely be most informative. *(confidence: high)*
- Coordinated regulation across multiple genes, rather than pairwise functional similarity alone, is what most strongly constrains co-inheritance in bacterial pangenomes. *(confidence: medium)*
- Accessory modules show the strongest co-inheritance signal, with a mean delta phi of +0.108 and 73% significant at p<0.05, exceeding core and mixed modules. *(confidence: medium)*
- Across 9 organisms, co-fit gene pairs show a weak but consistent positive co-occurrence signal, with 7 of 9 organisms showing a positive delta phi and the aggregate signal highly significant. *(confidence: high)*
- Among high-phi and high-cofit gene pairs, the most common SEED functional categories are metabolism, transport, and regulation. *(confidence: medium)*
- Genomic adjacency (operons) does not confound the co-occurrence signal, since only 0.7% of cofit pairs are adjacent and excluding them does not change the result pattern. *(confidence: high)*
- ICA-derived multi-gene modules show a substantially stronger within-module co-inheritance signal than pairwise co-fitness, with 195 modules across 6 organisms exceeding prevalence-matched null expectations. *(confidence: high)*
- Species with more gene-content diversity, such as Ddia6719 and pseudo3_N2E3, show the largest positive co-inheritance deltas, consistent with the prevalence-ceiling explanation. *(confidence: medium)*
- Stronger co-fitness scores weakly predict lower co-occurrence phi, likely because the strongest co-fitness pairs are near-universal core genes with little variance for co-occurrence detection. *(confidence: medium)*
- The pairwise co-fitness to co-occurrence effect is small in magnitude, indicating lab-measured functional coupling explains only a tiny fraction of co-inheritance patterns. *(confidence: high)*
- Building networks of which modules co-occur across species would allow testing whether co-fitness predicts cross-module co-inheritance. *(confidence: low)*
- Restricting the analysis to auxiliary-only gene pairs where both clusters are below 95% prevalence could maximize presence/absence variance and improve sensitivity to co-inheritance. *(confidence: medium)*

## Topics

- [Topic: Environment Biogeography](../topics/environment-biogeography.md)
- [Topic: Gene Fitness](../topics/gene-fitness.md)
- [Topic: Metabolic Pathways](../topics/metabolic-pathways.md)
- [Topic: Microbial Ecotypes](../topics/microbial-ecotypes.md)
- [Topic: Mobile Genetic Elements](../topics/mobile-genetic-elements.md)
- [Topic: Pangenome Architecture](../topics/pangenome-architecture.md)

## Data

- [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md)
- [Kescience Fitnessbrowser](../data/kescience-fitnessbrowser.md)

## Authors

- [Paramvir S. Dehal](../authors/0000-0001-5810-2497.md)

[Open the full report →](../../../projects/cofitness_coinheritance/REPORT.md)

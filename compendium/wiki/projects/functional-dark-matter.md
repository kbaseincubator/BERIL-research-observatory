# Functional Dark Matter

This project systematically cataloged genes lacking functional annotation but with experimentally measurable phenotypes across 48 bacterial species, identifying 57,011 "dark genes" (24.9% of sequenced bacterial genes) and 17,344 with actionable fitness or essentiality profiles. A comprehensive ranking framework integrating fitness data, pangenome conservation, cross-organism concordance, and biogeographic enrichment prioritized the top 100 candidates and designed a dual-route experimental campaign combining RB-TnSeq screens and CRISPRi knockdowns to characterize this vast reservoir of uncharacterized but functionally important bacterial biology.

## Key findings

- Bakta v1.12.0 reclassifies 83.7% of pangenome-linked dark genes as not hypothetical and assigns all 100 top candidates product descriptions, indicating the 57,011 dark gene count overestimates the truly uncharacterized genes because many are annotated in databases the Fitness Browser vintage did not check. *(confidence: high)*
- The 48 Fitness Browser organisms are 77% Pseudomonadota, with Actinobacteria absent and Firmicutes critically underrepresented, biasing prioritization toward Gammaproteobacteria and leaving major bacterial phyla uncharacterized for dark gene discovery. *(confidence: high)*
- Querying the full 27,690-species GTDB pangenome shows over half of dark gene ortholog groups are pan-bacterial (kingdom-level), demonstrating that functional dark matter is not a minor annotation gap but a fundamental limitation in understanding broadly conserved biology. *(confidence: medium)*
- A darkness spectrum classifies all 57,011 dark genes into 5 tiers from T1 Void (4,273 genes with zero evidence) to T5 Dawn (1,853 nearly-characterized genes), and a weighted set-cover of 42 organisms from 28 genera covers 95% of actionable dark gene priority. *(confidence: high)*
- Across 48 Fitness Browser organisms, 57,011 genes (24.9%) lack functional annotation and 17,344 of these have experimentally measurable phenotypes (strong fitness effects or essentiality), defining the actionable bacterial dark matter. *(confidence: high)*
- Among dark gene ortholog groups present in three or more Fitness Browser organisms, 65 show fitness concordance, meaning orthologs of the same unknown gene produce fitness effects under the same condition classes across different bacterial species. *(confidence: high)*
- Cross-species synteny and co-fitness analysis identifies 10,150 dark gene-operon partner pairs conserved in three or more organisms and 998 double-validated pairs with both conserved synteny and strong co-fitness, the highest-confidence functional predictions in the study. *(confidence: high)*
- Lab fitness phenotypes predict field environmental distribution for 61.7% of testable dark gene clusters, and independent NMDC metagenomic correlations confirmed all 4 pre-registered abiotic predictions (nitrogen, pH and oxygen), supporting a real lab-to-field link. *(confidence: medium)*
- Multi-dimensional scoring across 6 evidence axes ranked 17,344 dark genes and produced 100 top candidates spanning 22 organisms, dominated by Shewanella MR-1, P. putida N2C3 and Marinobacter, with 82% having high-confidence functional hypotheses supported by 3 or more evidence types. *(confidence: high)*
- Of 57,011 dark genes, 39,532 (69.3%) link to the pangenome and 6,142 belong to ICA fitness modules, enabling guilt-by-association function predictions, with 511 being both accessory and strong-fitness prime biogeographic candidates. *(confidence: high)*
- The 9,557 essential dark genes, which make up 55% of the actionable dark matter, were ranked separately using gene-neighbor context and cross-organism conservation, yielding the top 50 CRISPRi-ready candidates since essential genes score poorly in the fitness-centric framework. *(confidence: high)*
- Within-species carrier vs non-carrier comparisons across 31 species identify 10 accessory dark gene clusters with significant environmental enrichment (FDR < 0.05), including Pseudomonas putida stress/nitrogen genes enriched in clinical isolates and P. syringae genes enriched in plant-associated genomes. *(confidence: medium)*
- A dual-route experimental campaign can characterize dark genes efficiently: Route A (evidence-weighted) starts with MR-1 stress/nitrogen RB-TnSeq screens and E. coli CRISPRi for hypothesis testing, while Route B (conservation-weighted) starts with S. meliloti, P. putida and MR-1 broad screens to discover functions of conserved knowledge gaps. *(confidence: medium)*
- AlphaFold2 structure prediction offers a route to confirm functional hypotheses for the top 100 candidates and the 1,853 nearly-characterized T5 Dawn genes, and is the only remaining computational inference strategy for the 4,273 T1 Void genes that lack all other evidence. *(confidence: medium)*

## Topics

- [Topic: Environment Biogeography](../topics/environment-biogeography.md)
- [Topic: Functional Dark Matter](../topics/functional-dark-matter.md)
- [Topic: Gene Fitness](../topics/gene-fitness.md)
- [Topic: Microbial Ecotypes](../topics/microbial-ecotypes.md)
- [Topic: Mobile Genetic Elements](../topics/mobile-genetic-elements.md)
- [Topic: Pangenome Architecture](../topics/pangenome-architecture.md)

## Data

- [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md)
- [Kescience Fitnessbrowser](../data/kescience-fitnessbrowser.md)
- [Nmdc Arkin](../data/nmdc-arkin.md)

## Authors

- [Adam P. Arkin](../authors/0000-0002-4999-2931.md)

[Open the full report →](../../../projects/functional_dark_matter/REPORT.md)

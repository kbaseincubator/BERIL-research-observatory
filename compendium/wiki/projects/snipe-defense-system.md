# Snipe Defense System

This project characterized the SNIPE antiphage defense system by surveying a reference pangenome of 70 bacterial and archaeal species, discovering that SNIPE is far more widespread than previously known (1,696 species across 33 phyla, compared to >500 reported originally). The central finding is that SNIPE resolves a fundamental evolutionary trade-off in phage defense: it enables bacteria to resist phage infection by cleaving injected DNA at the mannose transporter pore while retaining full transporter function, providing defense without the severe metabolic cost of losing the transporter entirely. The work also reveals that SNIPE genes are predominantly accessory and mobile, suggesting they spread horizontally through bacterial populations as defense islands.

## Key findings

- About 20% of DUF4041 clusters have non-defense primary annotations (e.g. histidine kinase, seryl-tRNA aminoacylation) that likely represent annotation noise where DUF4041 is a secondary domain, so a stricter T5orf172/DUF4041 description filter is needed for a high-confidence SNIPE set. *(confidence: medium)*
- eggNOG Pfam annotations may miss divergent SNIPE homologues, since only 54 of 4,572 DUF4041 clusters show Mug113 (PF13455) co-annotation, suggesting many SNIPE nuclease domains go undetected. *(confidence: medium)*
- InterPro has renamed IPR025280 from a domain of unknown function (DUF4041) to the SNIPE associated domain based on the paper's functional characterization, converting a formerly dark domain into a defined antiphage marker. *(confidence: high)*
- The patchy distribution of SNIPE across many phyla and families is consistent with horizontal gene transfer of defense islands rather than vertical inheritance. *(confidence: medium)*
- Fitness Browser data directly contradict UniProt's fructose-transporter annotation, showing ManXYZ mutants grow normally on fructose but are crippled on mannose and glucosamine, confirming ManYZ is a mannose/glucosamine-specific transporter. *(confidence: high)*
- Methanococcus maripaludis JJ carries a full two-domain SNIPE protein (locus MMJJ_RS01635, PF13250 plus PF13455) with 129 experiments of fitness data, the first SNIPE homologue with genome-wide knockout phenotypes. *(confidence: high)*
- RB-TnSeq fitness data from 168 E. coli K-12 experiments show ManXYZ knockouts incur severe substrate-specific defects (worst fitness -3.93 to -4.14) on mannose and glucosamine, quantifying the metabolic cost of losing the phage lambda receptor. *(confidence: high)*
- SNIPE (DUF4041) was detected in the phage therapy target Klebsiella, co-occurring with its mannose PTS transporter in the same genome, which is clinically relevant because SNIPE could affect phage therapy efficacy in this pathogen. *(confidence: medium)*
- SNIPE genes are predominantly accessory, with only 13.3% core and a combined 86.7% accessory-plus-singleton fraction, indicating SNIPE is typically gained or lost rather than vertically inherited. *(confidence: high)*
- SNIPE resolves the phage resistance versus metabolic cost trade-off by cleaving phage DNA at the ManYZ pore while retaining full transporter function, providing the resistance benefit of man knockouts without their metabolic cost. *(confidence: high)*
- SNIPE-bearing species occupy statistically distinct environmental niches, with 22 of 64 AlphaEarth dimensions significantly different (Bonferroni-corrected p < 0.05) at small-to-medium effect sizes, indicating a consistent but modest environmental shift. *(confidence: medium)*
- The SNIPE nuclease domain is PF13455 (Mug113), a distinct Pfam family within the GIY-YIG clan CL0418, not the canonical GIY-YIG family PF01541, so zero DUF4041 plus PF01541 co-occurrences is a genuine biological result rather than an annotation artifact. *(confidence: high)*
- The diagnostic SNIPE domain DUF4041 (PF13250) was detected in 4,572 gene clusters across 1,696 species spanning 33 bacterial and archaeal phyla, far exceeding the more-than-500 homologues reported in the original paper. *(confidence: high)*
- Generating Klebsiella-specific SNIPE or ManYZ fitness data would require new mutant libraries in natural SNIPE-carrying K. pneumoniae strains, a gap a fitness data curation plan has been developed to address. *(confidence: medium)*

## Topics

- [Topic: Environment Biogeography](../topics/environment-biogeography.md)
- [Topic: Functional Dark Matter](../topics/functional-dark-matter.md)
- [Topic: Gene Fitness](../topics/gene-fitness.md)
- [Topic: Metabolic Pathways](../topics/metabolic-pathways.md)
- [Topic: Microbiome Engineering](../topics/microbiome-engineering.md)
- [Topic: Mobile Genetic Elements](../topics/mobile-genetic-elements.md)
- [Topic: Pangenome Architecture](../topics/pangenome-architecture.md)

## Data

- [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md)
- [Kescience Fitnessbrowser](../data/kescience-fitnessbrowser.md)
- [Phagefoundry](../data/phagefoundry.md)

## Authors

- [Chris Mungall](../authors/0000-0002-6601-2165.md)

[Open the full report →](../../../projects/snipe_defense_system/REPORT.md)

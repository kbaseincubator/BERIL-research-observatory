# Prophage Amr Comobilization

This project mapped the association between prophage density and antibiotic resistance across thousands of bacterial species using pangenome-scale analyses of the BERDL genome collection. The central finding is that prophage density emerges as a strong, multi-phylum predictor of AMR breadth, explaining ~30% of variance across 4,770 species—a more robust signal than previously documented at smaller scales. The result suggests prophages either directly mobilize resistance genes via transduction or mark species with higher recombination capacity that independently acquire both prophages and resistance cargo.

## Key findings

- Prophages were identified by keyword/Pfam matching rather than dedicated prediction tools, which may include false positives like phage-defense systems and miss divergent prophages. *(confidence: high)*
- The fitness cost hypothesis could not be tested because the RB-TnSeq fitness browser covers only a few dozen model organisms that do not overlap well with the GTDB pangenome species analyzed. *(confidence: high)*
- The species-level association does not prove phage-mediated AMR transfer, since species with open pangenomes may independently accumulate both prophages and AMR genes. *(confidence: high)*
- The breadth finding extends prior capsule-pangenome work by demonstrating the prophage-AMR correlation at much larger scale and showing it persists after controlling for genome count rather than capsule presence. *(confidence: medium)*
- The prophage density signal is consistent with prophages directly mobilizing resistance genes via transduction or with high-recombination species independently acquiring both prophages and AMR genes. *(confidence: medium)*
- The prophage-AMR breadth association persists after controlling for genome count and is consistent across all five major phyla, arguing against a purely phylogenetic explanation. *(confidence: high)*
- This is the first pangenome-scale analysis of prophage-AMR gene-neighborhood co-localization, spanning 100 species, 1,953 genomes, and 36,041 AMR gene instances. *(confidence: medium)*
- A pangenome-scale census identified 83,008 AMR gene clusters and millions of prophage marker clusters, with 14,669 of 27,702 species carrying both. *(confidence: high)*
- Both prophage markers and AMR genes are predominantly accessory rather than core, with prophage markers more strongly accessory and frequently singleton. *(confidence: high)*
- Over half of AMR gene instances in the most AMR-burdened species reside on contigs that also carry strict prophage markers such as terminase and phage structural proteins. *(confidence: high)*
- Prophage-proximal AMR genes are only slightly more likely to be accessory than distal ones, a statistically significant but modest effect. *(confidence: medium)*
- Species with higher prophage marker density carry significantly broader AMR gene repertoires, with prophage density explaining about 30% of variance in AMR breadth. *(confidence: high)*
- The proximity-accessory association is threshold-dependent and heterogeneous, absent or reversed at very close range and strengthening at broader gene-distance thresholds. *(confidence: medium)*
- Applying dedicated prophage prediction tools such as geNomad or PHASTER and ingesting the results would replace keyword-based detection and reduce false positives. *(confidence: medium)*
- As fitness browser coverage expands, the fitness cost question can be revisited to test whether prophage-proximal AMR genes have distinct fitness costs. *(confidence: medium)*

## Topics

- [Topic: Amr Resistome](../topics/amr-resistome.md)
- [Topic: Functional Dark Matter](../topics/functional-dark-matter.md)
- [Topic: Gene Fitness](../topics/gene-fitness.md)
- [Topic: Mobile Genetic Elements](../topics/mobile-genetic-elements.md)
- [Topic: Pangenome Architecture](../topics/pangenome-architecture.md)

## Data

- [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md)
- [Kescience Fitnessbrowser](../data/kescience-fitnessbrowser.md)

## Authors

- [Claude](../authors/claude.md)
- [Justin Reese](../authors/0000-0002-2170-2250.md)

[Open the full report →](../../../projects/prophage_amr_comobilization/REPORT.md)

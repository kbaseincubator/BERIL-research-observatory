# Aromatic Catabolism Network

This project mapped the genetic architecture of aromatic-compound catabolism in *Acinetobacter baylyi* ADP1, revealing that a seemingly simple metabolic pathway depends on 51 genes organized into four interdependent subsystems: the core aromatic degradation pathway, Complex I for NADH reoxidation, iron acquisition for ring cleavage, and PQQ cofactor biosynthesis. The critical insight is that Complex I, which accounts for 41% of the support network, is required not specifically for aromatic catabolism but for any high-NADH-flux substrate—a dependency invisible to traditional metabolic models despite being the dominant constraint.

## Key findings

- Ortholog-transferred fitness data mixes signals from multiple Fitness Browser organisms with different respiratory chain architectures, so direct Complex I measurements on aromatic substrates in a single organism would be more definitive. *(confidence: medium)*
- The PQQ dependency is not exclusively aromatic because PQQ biosynthesis genes also appear as glucose-specific (PQQ-dependent glucose dehydrogenase), so PQQ requirement is shared with glucose catabolism. *(confidence: high)*
- The co-fitness analysis uses only 8 conditions, limiting the resolution of gene-gene correlations and the sharpness of subsystem boundaries. *(confidence: high)*
- ADP1's apparent quinate-specificity of Complex I likely reflects an alternative NADH dehydrogenase (NDH-2) that compensates on simpler, lower-NADH-flux substrates. *(confidence: low)*
- Three β-ketoadipate-pathway enzyme steps create the support dependencies: a PQQ-dependent quinate dehydrogenase requires PQQ biosynthesis, an Fe²⁺-dependent protocatechuate 3,4-dioxygenase requires iron acquisition, and TCA-cycle oxidation requires Complex I for NADH reoxidation. *(confidence: high)*
- Two DUF-domain proteins (ACIAD3137, ACIAD2176) correlate at r > 0.98 with Complex I genes and are candidate uncharacterized Complex I accessory factors. *(confidence: medium)*
- Aromatic (quinate) catabolism in Acinetobacter baylyi ADP1 requires a 51-gene support network whose genes organize into four functional subsystems beyond the core β-ketoadipate pathway. *(confidence: high)*
- Co-fitness analysis reassigned 16 of 23 previously uncharacterized genes to specific support subsystems, with within-category correlation far exceeding between-category correlation (Complex I mean r = 0.992). *(confidence: high)*
- Complex I (NADH:ubiquinone oxidoreductase) is the dominant support requirement for aromatic catabolism, accounting for 21 of the 51 quinate-specific genes (41%). *(confidence: high)*
- Cross-species ortholog-transferred fitness shows the Complex I dependency is on high-NADH-flux substrates generally, with the largest defects on the non-aromatic substrates acetate and succinate, not on aromatics specifically. *(confidence: high)*
- The FBA model captures higher Complex I flux on aromatic substrates but predicts 0% essentiality, and 30 of the 51 quinate-specific genes have no FBA reaction mappings at all, revealing a systematic metabolic-model blind spot. *(confidence: high)*
- The four support subsystems occupy distinct chromosomal locations with no cross-category operons, so the metabolic dependency is not encoded by genomic co-localization but emerges from the biochemistry of aromatic ring cleavage. *(confidence: high)*
- A cross-species pangenome comparison using KO annotations could test whether Acinetobacter species carrying the pca pathway are more likely to retain Complex I (KOs K00330–K00343) than species without aromatic degradation capability. *(confidence: medium)*
- Searching the ADP1 genome for NDH-2 (type 2 NADH dehydrogenase) genes and testing their deletion phenotype on quinate vs glucose would directly test whether NDH-2 compensates for Complex I on non-aromatic substrates. *(confidence: medium)*

## Topics

- [Topic: Adp1 Model System](../topics/adp1-model-system.md)
- [Topic: Functional Dark Matter](../topics/functional-dark-matter.md)
- [Topic: Gene Fitness](../topics/gene-fitness.md)
- [Topic: Metabolic Pathways](../topics/metabolic-pathways.md)
- [Topic: Pangenome Architecture](../topics/pangenome-architecture.md)

## Data

- [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md)
- [Kescience Fitnessbrowser](../data/kescience-fitnessbrowser.md)

## Authors

- [Paramvir S. Dehal](../authors/0000-0001-5810-2497.md)

[Open the full report →](../../../projects/aromatic_catabolism_network/REPORT.md)

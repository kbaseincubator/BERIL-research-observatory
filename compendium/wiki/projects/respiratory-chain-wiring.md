# Respiratory Chain Wiring

This project mapped how Acinetobacter baylyi ADP1 rewires its respiratory electron transport chain for different carbon sources—switching from Complex I alone on quinate, to a multi-enzyme system on acetate, to full redundancy on glucose. The key finding is that this "wiring" operates at the metabolic level through NADH flux rates, not transcriptional control: all three NADH dehydrogenases are constitutively expressed, and substrate-specific bottlenecks in electron reoxidation determine which enzyme becomes rate-limiting. This flux-rate logic may generalize to any carbon source whose catabolism produces concentrated bursts of reducing equivalents.

## Key findings

- The NADH stoichiometry analysis is built on theoretical pathway biochemistry rather than measured flux distributions, and the cross-species comparison includes only four organisms without NDH-2, too few for statistical significance. *(confidence: high)*
- The central NDH-2 compensation prediction cannot be directly tested because NDH-2 is absent from the deletion collection and has no growth data, making it the weakest finding in the study. *(confidence: high)*
- The cross-species NDH-2 identification relies on text matching of gene descriptions, which likely yields false positives for organisms with incompletely annotated Complex I subunits, so KO-based identification (K03885) would be more reliable. *(confidence: high)*
- The ADP1 NDH-2/Complex I respiratory wiring pattern may be species-specific rather than a general cross-species rule, since the compensation signal is likely ADP1-specific. *(confidence: low)*
- The rate-versus-yield principle—that substrates producing concentrated reducing equivalents demand high-capacity NADH reoxidation regardless of total NADH yield—should generalize to any carbon source whose catabolism concentrates reducing equivalents. *(confidence: medium)*
- ADP1 carries three parallel NADH dehydrogenases (Complex I, NDH-2, and ACIAD3522) with distinct, non-overlapping condition profiles, with ACIAD3522 being specifically lethal on acetate. *(confidence: high)*
- Acinetobacter baylyi ADP1's branched respiratory chain is wired in a condition-dependent manner, using qualitatively different respiratory configurations for each carbon source rather than a quantitative flux gradient. *(confidence: high)*
- Across 14 fitness-browser organisms, those with validated NDH-2 show larger Complex I aromatic fitness deficits than those without (the opposite of the compensation prediction, not statistically significant), so the NDH-2 compensation pattern is not supported across species. *(confidence: medium)*
- All three NADH dehydrogenases are constitutively co-expressed at similar protein levels, so condition-specific respiratory wiring operates as a passive flux-based system at the metabolic level rather than an active transcriptional switch. *(confidence: high)*
- Flux balance analysis predicts zero flux through NDH-2 and ACIAD3522 on all standard media because it optimizes for growth and routes NADH through the more ATP-efficient Complex I, illustrating why FBA fails to capture the capacity constraints that drive condition-specific respiratory requirements. *(confidence: high)*
- NDH-2 (KO K03885) is a standalone core-genome gene that is TnSeq-dispensable, sits outside any respiratory operon, and is absent from the ADP1 deletion collection so it lacks direct growth data. *(confidence: high)*
- The paradox that quinate yields fewer NADH per carbon yet makes Complex I more essential is resolved by NADH flux rate: aromatic ring cleavage via the β-ketoadipate pathway creates a concentrated TCA-cycle NADH burst exceeding NDH-2's reoxidation capacity. *(confidence: high)*
- Constructing an NDH-2 deletion mutant in ADP1 would provide the definitive experimental test of whether NDH-2 loss makes Complex I essential on glucose. *(confidence: medium)*
- Querying the full BERDL pangenome for NDH-2 (K03885) and Complex I (K00330-K00343) KO co-occurrence across 27K species would provide a far larger, better-powered sample to test the compensation hypothesis. *(confidence: medium)*

## Topics

- [Topic: Adp1 Model System](../topics/adp1-model-system.md)
- [Topic: Functional Dark Matter](../topics/functional-dark-matter.md)
- [Topic: Gene Fitness](../topics/gene-fitness.md)
- [Topic: Metabolic Pathways](../topics/metabolic-pathways.md)
- [Topic: Microbial Ecotypes](../topics/microbial-ecotypes.md)
- [Topic: Microbiome Engineering](../topics/microbiome-engineering.md)
- [Topic: Pangenome Architecture](../topics/pangenome-architecture.md)

## Data

- [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md)
- [Kescience Fitnessbrowser](../data/kescience-fitnessbrowser.md)

## Authors

- [Paramvir S. Dehal](../authors/0000-0001-5810-2497.md)

[Open the full report →](../../../projects/respiratory_chain_wiring/REPORT.md)

# Metal Resistance & Critical Minerals

## Overview

This page synthesizes three projects on bacterial metal tolerance. In this wiki,
metal resistance means the genome-wide ability of bacteria to maintain growth or
fitness under exposure to metals such as cobalt, nickel, copper, zinc, aluminum,
chromium, uranium, and related ions. The projects use RB-TnSeq fitness data from
the [KEScience Fitness Browser](../data/kescience-fitnessbrowser.md), pangenome
context from [KBase KE Pangenome](../data/kbase-ke-pangenome.md), and follow-up
specificity analyses to separate general stress response from metal-specific
biology.

The central synthesis is that metal tolerance is not mainly explained by rare,
accessory resistance genes. Across the demo corpus, the dominant signal is core
genome robustness: genes required under metal stress are heavily enriched in the
core genome, cross-resistance between metals is almost always positive, and even
genes filtered as metal-specific remain mostly core. The accessory genome still
matters, but as a smaller and more specialized layer.

## What the Corpus Shows

The metal fitness atlas provides the broadest result. Across 22 organisms and 14
metals, significant metal fitness defects were enriched in core genes, reversing
the initial expectation that toxic metal tolerance would be mostly accessory. The
same atlas found conserved metal-phenotype ortholog groups and novel candidates,
so the result is not only a conservation statistic; it also produces a candidate
set for metal biology.

The cross-resistance project adds a second layer. Gene-level fitness profiles for
metal pairs are overwhelmingly positively correlated, which means that many
metals share a genome-wide stress response. The strongest pairings still carry
chemical structure: divalent cations such as cobalt, nickel, and zinc form
stronger shared responses than more independent metals such as aluminum. That
leads to a two-layer model: a universal stress layer plus a chemistry-specific
magnitude layer.

The specificity project refines the atlas rather than overturning it. More than
half of analyzed metal-important gene records are metal-specific under a strict
non-metal sick-rate filter, and those genes are enriched for metal-resistance
annotations. Yet they remain core-enriched. The best reading is not "all metal
genes are general stress genes" and not "metal resistance is accessory"; it is a
gradient from general stress, through metal-shared defense, to specialized
metal-specific resistance.

## Projects and Evidence

**Pan-Bacterial Metal Fitness Atlas** establishes the core-genome robustness
model. It reports 12,838 metal-important gene records, 1,182 conserved metal gene
families, and a pangenome-scale scoring analysis across 27,702 species.

**Gene-Resolution Metal Cross-Resistance** asks whether metals share genetic
responses. It shows that 98.1% of organism-metal pair correlations are positive
and decomposes metal-important genes into general stress, metal-shared, and
metal-specific tiers.

**Metal-Specific vs General Stress Genes** asks whether the atlas result was only
a general-stress artifact. It finds that 54.9% of analyzed metal-important gene
records are metal-specific, that metal-specific genes are functionally enriched
for resistance annotations, and that the core enrichment still holds after this
filter.

## Connections

The closest conceptual neighbor is [Microbial Ecotypes & Niche Differentiation](microbial-ecotypes.md).
Both topics use pangenomes to separate broad stable background from the more
variable layer where ecological or stress-specific signal appears. The metal
topic does this through core/accessory conservation and fitness specificity; the
ecotype topic does it through whole-genome correlation and COG functional
differentiation.

The main data links are [KEScience Fitness Browser](../data/kescience-fitnessbrowser.md)
for RB-TnSeq metal experiments and [KBase KE Pangenome](../data/kbase-ke-pangenome.md)
for core/accessory and species-scale pangenome context. Author pages for
[Paramvir S. Dehal](../authors/0000-0001-5810-2497.md) and
[Adam Deutschbauer](../authors/0000-0003-2728-7622.md) provide the contributor
view of this topic.

## Caveats and Open Directions

The strongest caveat is validation scale. BacDive validation for multi-metal
scores is underpowered at the Fitness Browser organism scale, so environmental
prediction needs pangenome-scale validation rather than a small matched-species
test. Metal coverage is also uneven, with some metals measured across many
organisms and others only sparsely. The next useful demo extension would add a
project on global metal biogeography or BacDive metal validation so the topic can
connect fitness mechanisms to environmental distribution.

## Sources

- [stmt:metal-atlas-core-robustness-finding; metal_fitness_atlas]
- [stmt:metal-atlas-conserved-families-finding; metal_fitness_atlas]
- [stmt:metal-atlas-pangenome-distribution-claim; metal_fitness_atlas]
- [stmt:metal-cross-universal-positivity-finding; metal_cross_resistance]
- [stmt:metal-cross-two-layer-claim; metal_cross_resistance]
- [stmt:metal-cross-tier-architecture-finding; metal_cross_resistance]
- [stmt:metal-cross-bacdive-caveat; metal_cross_resistance]
- [stmt:metal-specificity-fraction-finding; metal_specificity]
- [stmt:metal-specificity-core-refinement-claim; metal_specificity]
- [stmt:metal-specificity-functional-validation-finding; metal_specificity]

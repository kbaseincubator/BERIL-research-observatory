# KEScience Fitness Browser

## Overview

The KEScience Fitness Browser is the fitness-data backbone for the metal
resistance half of this demo. It contains RB-TnSeq measurements that connect
genes to growth defects across experimental conditions. In the selected projects,
those conditions include hundreds of metal experiments across many bacteria.

The collection matters because the metal pages are not based only on gene
presence. They are based on measured fitness effects: which genes become
important under metal stress, whether the same genes matter for multiple metals,
and whether those genes are metal-specific or broadly sick under many
conditions.

## Projects Using This Collection

The [metal atlas](../topics/metal-resistance.md) uses Fitness Browser data to
classify metal experiments and extract gene-by-metal fitness records. The
cross-resistance project uses those records to compare gene fitness profiles
between metal pairs. The specificity project compares metal-important genes
against thousands of non-metal experiments to ask whether the signal is specific
to metals or reflects general stress.

The collection is therefore the measurement layer under the demo's central metal
claim: metal tolerance is mostly core-genome robustness, with cross-resistance
structure that can be measured directly from gene-level fitness profiles.

## Connections

This page connects most directly to [Metal Resistance & Critical Minerals](../topics/metal-resistance.md).
For evolutionary interpretation, it pairs with [KBase KE Pangenome](kbase-ke-pangenome.md),
which supplies core/accessory context for the genes measured by the Fitness
Browser.

## Sources

- [stmt:metal-atlas-core-robustness-finding; metal_fitness_atlas]
- [stmt:metal-cross-universal-positivity-finding; metal_cross_resistance]
- [stmt:metal-cross-tier-architecture-finding; metal_cross_resistance]

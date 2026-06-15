# Kescience Fitnessbrowser

## Overview

The KEScience Fitness Browser collection anchors functional-genomics work on
*Acinetobacter baylyi* ADP1, a model organism prized for its natural
competence and tractable metabolism. In the BERIL corpus it is exercised
through a single, deeply integrated exploration of an ADP1 multi-omics
resource: a user-provided SQLite database spanning 15 tables, roughly 461,522
rows, and 135 MB of data covering *A. baylyi* ADP1 together with 13 related
genomes. That database is unusually broad for a single organism, with a central
gene-feature table carrying annotation columns across six distinct data
modalities — TnSeq essentiality, FBA metabolic flux, mutant growth fitness on
eight carbon sources, proteomics across seven strains, pangenome
classification, and functional annotations drawn from COG, KO, Pfam, and
UniRef. No single gene is observed across all six modalities at once, but the
pairwise overlaps are substantial, which makes the resource well suited to
cross-modal questions about gene function and metabolic capability.

Work on this collection establishes two complementary stories. The first is one
of connectivity: the ADP1 resource does not sit in isolation but maps cleanly
onto the wider BERDL data lake. Querying BERDL via Spark confirmed strong
linkage through genome identifiers, metabolic reactions, biochemical compounds,
and pangenome clusters, with most connection types matching at high rates. A
gene-junction bridge resolves the otherwise incompatible naming conventions
between the two systems — BERDL centroid gene IDs versus ADP1-style mmseqs2
cluster IDs — and achieves complete gene-level coverage, mapping all 4,891 BERDL
clusters to 4,081 unique ADP1 clusters across 43,754 genes. Together these
results show that a comprehensive, user-provided ADP1 database can act as a
BERDL bridge, supplying a foundation that downstream ADP1 synthesis pages can
build on.

The second story concerns biology and model quality. Mutant growth fitness
across the eight carbon sources is moderately correlated overall, but with clear
structure: urea and quinate stand apart as outlier conditions, and urea fitness
is nearly uncorrelated with the other conditions, pointing to a largely
independent set of urea-catabolism genes. On the modeling side, the ADP1
flux-balance analysis is heavily reliant on gapfilling — of 121,519 growth
phenotype predictions across the 14 genomes, the large majority depend on at
least one gapfilled reaction, so prediction accuracy is tightly coupled to
gapfilling quality. These observations open concrete directions: prioritizing
the genes where FBA and TnSeq disagree on essentiality for metabolic model
refinement, and treating urea-specific fitness genes and their pangenome
conservation as an independent metabolism module worth a dedicated analysis.

## Projects Using This Collection

A single exploration project drives the analyses above. It inventories the
multi-omics database, scans its connectivity to BERDL, constructs the pangenome
cluster bridge, and probes gene essentiality, fitness, and metabolic-model
behavior. Through these notebooks it both validates the collection as an
integration point and surfaces the urea-metabolism and FBA–TnSeq discordance
opportunities that motivate further study. The project's findings feed three
topic areas in this wiki — [Adp1 Data Integration](../topics/adp1-data-integration.md),
which gathers the BERDL connectivity, multi-omics inventory, and pangenome
bridge results; [Adp1 Carbon Fitness](../topics/adp1-carbon-fitness.md), which
covers the condition-specific fitness structure and the urea deep-dive
opportunity; and [Adp1 Model Quality](../topics/adp1-model-quality.md), which
collects the gapfilling caveat and the FBA–TnSeq discordance prioritization.

Authorship and contributors are tracked on the associated author pages,
[0000 0001 5810 2497](../authors/0000-0001-5810-2497.md) and
[0009 0007 0287 2979](../authors/0009-0007-0287-2979.md).

## Sources

- [stmt:adp1-explorer-multiomics-finding; acinetobacter_adp1_explorer]
- [stmt:adp1-explorer-berdl-connectivity-finding; acinetobacter_adp1_explorer]
- [stmt:adp1-explorer-pangenome-bridge-finding; acinetobacter_adp1_explorer]
- [stmt:adp1-explorer-database-bridge-claim; acinetobacter_adp1_explorer]
- [stmt:adp1-explorer-condition-fitness-finding; acinetobacter_adp1_explorer]
- [stmt:adp1-explorer-gapfilling-caveat; acinetobacter_adp1_explorer]
- [stmt:adp1-explorer-urea-deep-dive-opportunity; acinetobacter_adp1_explorer]
- [stmt:adp1-explorer-discordance-opportunity; acinetobacter_adp1_explorer]

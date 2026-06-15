# Kbase Uniref

## Overview

The `kbase_uniref` collection provides UniRef-based functional annotation that
sits alongside COG, KO, and Pfam as one of the sequence-based annotation sources
drawn on by projects working in the BERDL lakehouse. To date it appears in the
compendium through a single exploration of *Acinetobacter baylyi* ADP1, where
UniRef is one of the functional annotation layers carried by a comprehensive,
user-provided multi-omics database for the organism. In that setting UniRef
annotations cover roughly a third to just over half of genes, in the same
34–55% range as the other functional ontologies, and contribute to the gene-level
characterisation that the ADP1 work then connects back to the rest of BERDL.

The value of UniRef annotation in this work is less as a standalone resource and
more as one strand of a richly interconnected dataset. The ADP1 database
integrates six molecular and phenotype modalities — TnSeq essentiality, FBA
metabolic flux, mutant growth fitness, proteomics, pangenome classification, and
functional annotation (COG/KO/Pfam/UniRef) — across thousands of genes, and the
exploration demonstrates that such a user-provided collection can integrate
deeply with the lakehouse rather than remaining an isolated import. UniRef is
therefore best read here as part of the annotation backbone that makes ADP1 genes
addressable and comparable across collections.

## Projects Using This Collection

The [ADP1 data explorer](../authors/0000-0001-5810-2497.md) is the project that
exercises this collection. Its starting point is an inventory of the user-provided
ADP1 database: 15 tables and several hundred thousand rows describing *A. baylyi*
ADP1 together with thirteen related genomes, with a central gene-feature table
whose annotation columns span the six modalities noted above. UniRef sits in the
functional-annotation column group, and the explorer treats the whole assembly as
a multi-omics integration problem — work that is organised under the
[ADP1 data integration](../topics/adp1-data-integration.md) topic.

A central result of that integration is connectivity. Querying BERDL through
Spark, the explorer confirmed that the ADP1 database links strongly to lakehouse
collections through genomes, reactions, compounds, and pangenome clusters, with
most connection types matching at or above 90%. The most technically involved of
these bridges is at the pangenome level: ADP1's mmseqs2-style cluster identifiers
and BERDL's centroid gene identifiers share no direct string overlap, but a
gene-junction mapping recovered complete coverage, with all BERDL clusters mapping
onto unique ADP1 clusters at full gene-level match. That mapping is what lets any
BERDL pangenome annotation be joined onto ADP1 genes, and it is the practical
reason the explorer can serve as a reusable bridge for downstream ADP1 synthesis
work.

The same database also surfaces biology that is specific to ADP1. Across eight
carbon sources, mutant growth fitness shows clear condition-specific structure:
urea and quinate stand apart as outliers, with urea fitness almost uncorrelated
with the other conditions, pointing to a largely independent set of urea
catabolism genes. This fitness analysis belongs to the
[ADP1 carbon fitness](../topics/adp1-carbon-fitness.md) topic and motivates a
proposed follow-up that would treat ADP1's urea-specific fitness genes and their
pangenome conservation as an independent metabolism module.

On the modelling side, the explorer is candid about quality limits, which are
catalogued under the [ADP1 model quality](../topics/adp1-model-quality.md) topic.
The metabolic model leans heavily on gapfilling — the large majority of growth
phenotype predictions depend on at least one gapfilled reaction — so prediction
accuracy is tightly coupled to gapfilling quality. Where flux-balance predictions
and TnSeq essentiality disagree, those discordant genes are flagged as priority
candidates for model refinement. Both observations frame UniRef and the other
annotation layers as supporting evidence for interpreting, and eventually
correcting, the model rather than as finished ground truth.

Related authors and entry points for this work include
[0000-0001-5810-2497](../authors/0000-0001-5810-2497.md) and
[0009-0007-0287-2979](../authors/0009-0007-0287-2979.md).

## Sources

- [stmt:adp1-explorer-multiomics-finding; acinetobacter_adp1_explorer]
- [stmt:adp1-explorer-berdl-connectivity-finding; acinetobacter_adp1_explorer]
- [stmt:adp1-explorer-pangenome-bridge-finding; acinetobacter_adp1_explorer]
- [stmt:adp1-explorer-database-bridge-claim; acinetobacter_adp1_explorer]
- [stmt:adp1-explorer-condition-fitness-finding; acinetobacter_adp1_explorer]
- [stmt:adp1-explorer-urea-deep-dive-opportunity; acinetobacter_adp1_explorer]
- [stmt:adp1-explorer-gapfilling-caveat; acinetobacter_adp1_explorer]
- [stmt:adp1-explorer-discordance-opportunity; acinetobacter_adp1_explorer]

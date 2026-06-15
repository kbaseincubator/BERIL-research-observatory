# Kbase Msd Biochemistry

## Overview

The KBase MSD biochemistry collection is the lakehouse's reference store of
metabolic reactions and compounds — the shared chemical vocabulary against
which genome-scale models and annotation pipelines are reconciled. Its value in
the BERDL knowledge graph comes less from being browsed in isolation than from
being joined: when a project brings its own organism-specific reactions and
compounds, this collection is where those entries are matched, normalized, and
placed in a comparative context. So far the collection is exercised by a single
project, an exploration of an *Acinetobacter baylyi* ADP1 multi-omics database,
which uses the biochemistry tables as one of several anchors that tie a
user-supplied resource into BERDL.

That exploration project assembled a rich multi-omics resource for ADP1: a
SQLite database of fifteen interconnected tables holding roughly 461,522 rows
across 135 MB of data for *A. baylyi* ADP1 and thirteen related genomes,
integrating six molecular and phenotype modalities — TnSeq essentiality, FBA
metabolic flux, mutant growth fitness on eight carbon sources, proteomics across
seven engineered strains, pangenome classification, and functional annotation
via COG, KO, Pfam, and UniRef. The biochemistry collection enters this picture
as the metabolic backbone: the project's reactions and compounds are exactly the
entities that must resolve against MSD biochemistry for the model to mean
anything in a shared setting.

When the ADP1 reactions and compounds were queried against BERDL through Spark,
the match rates were high enough to treat the collection as a dependable anchor.
Of 1,330 ADP1 reactions, 1,210 (91%) matched BERDL biochemistry, and all 230
compounds matched at 100%. Together with genome and pangenome identifiers, these
chemical matches make the ADP1 database connect strongly to BERDL across
genomes, reactions, compounds, and pangenome clusters, covering the major axes
of biological data in the lakehouse — genomics, metabolomics, and comparative
genomics. This is the basis for treating the explorer project as a working
BERDL bridge: a user-provided database that integrates deeply enough with
lakehouse collections, biochemistry among them, to serve as a foundation for
downstream ADP1 synthesis work.

## Projects Using This Collection

The single project drawing on this collection,
[Adp1 Data Integration](../topics/adp1-data-integration.md), demonstrates both
how the biochemistry tables are reached and what they enable once reached. Beyond
the direct reaction and compound matches, the project established a pangenome
cluster bridge that complements the chemical one. ADP1's mmseqs2-style cluster
identifiers share no string overlap with BERDL's centroid gene identifiers, but
routing through BERDL's gene-junction table closed the gap: all 4,891 BERDL
clusters mapped to 4,081 unique ADP1 clusters with complete, 100% gene-level
coverage across 43,754 genes. With reactions, compounds, genomes, and pangenome
clusters all resolved, any BERDL pangenome annotation can be joined onto ADP1
genes, which is what makes the biochemistry collection a productive join target
rather than a standalone lookup.

The same database carries phenotype data the biochemistry layer helps interpret.
Mutant growth fitness across the eight carbon sources shows clear
condition-specific structure rather than a single uniform response, and urea and
quinate stand out as outlier conditions; urea fitness is nearly uncorrelated with
quinate (r = 0.11) and only weakly correlated with the other conditions
(r = 0.12–0.28), pointing to a largely independent set of urea-catabolism genes.
This condition structure is documented under
[Adp1 Carbon Fitness](../topics/adp1-carbon-fitness.md) and gives the metabolic
collection a phenotypic counterpart: reactions and compounds describe what the
organism could do, while the fitness data records what mutants actually do across
substrates.

## Caveats

The metabolic predictions built on this collection should be read with their
gapfilling burden in mind. Across the fourteen genomes, of 121,519 growth
phenotype predictions, 105,376 (87%) depend on at least one gapfilled reaction,
so model-based growth calls for ADP1 are quality-limited by that heavy
dependence — prediction accuracy is tightly coupled to gapfilling quality, and
false-negative predictions carry higher mean gap counts than correct ones. The
biochemistry collection supplies the reference reactions, but where a genome's
draft model is completed by gapfilling rather than by direct evidence, the
resulting phenotype predictions inherit that uncertainty.

## Open Directions

Two follow-up analyses are flagged by the explorer project, both of which would
lean on this collection. First, the FBA–TnSeq discordant genes — those where the
metabolic model and the experimental essentiality calls disagree — should be
prioritized for metabolic-model refinement, since they are the most informative
candidates for correcting reaction content and are tracked under
[Adp1 Model Quality](../topics/adp1-model-quality.md). Second, the urea-specific
fitness genes and their pangenome conservation are worth analyzing as an
independent metabolism module, given how sharply urea separates from the other
carbon sources; this would tie the biochemistry of urea catabolism to its
comparative-genomic footprint.

The contributors to this work are listed at
[0000 0001 5810 2497](../authors/0000-0001-5810-2497.md) and
[0009 0007 0287 2979](../authors/0009-0007-0287-2979.md).

## Sources

- [stmt:adp1-explorer-multiomics-finding; acinetobacter_adp1_explorer]
- [stmt:adp1-explorer-berdl-connectivity-finding; acinetobacter_adp1_explorer]
- [stmt:adp1-explorer-database-bridge-claim; acinetobacter_adp1_explorer]
- [stmt:adp1-explorer-pangenome-bridge-finding; acinetobacter_adp1_explorer]
- [stmt:adp1-explorer-condition-fitness-finding; acinetobacter_adp1_explorer]
- [stmt:adp1-explorer-gapfilling-caveat; acinetobacter_adp1_explorer]
- [stmt:adp1-explorer-discordance-opportunity; acinetobacter_adp1_explorer]
- [stmt:adp1-explorer-urea-deep-dive-opportunity; acinetobacter_adp1_explorer]

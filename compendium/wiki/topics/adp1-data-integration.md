# Topic: ADP1 Data Integration

## Overview

This topic gathers work on stitching a comprehensive, user-provided
*Acinetobacter baylyi* ADP1 dataset into the broader BER Data Lakehouse
(BERDL), so that ADP1 phenotype and annotation data can be queried alongside
the lakehouse's genomic, biochemical, and comparative-genomics collections. The
anchoring effort inventoried a 135 MB SQLite database of 15 tables and 461,522
rows covering ADP1 and 13 related genomes, whose central `genome_features` table
spans six molecular and phenotype modalities — TnSeq essentiality, FBA metabolic
flux, mutant growth fitness across eight carbon sources, proteomics over seven
engineered strains, pangenome classification, and functional annotation via
COG/KO/Pfam/UniRef. No single gene carries all six modalities at once, but the
pairwise overlaps — especially among essentiality, pangenome membership, and
proteomics — are substantial enough to support integrative analysis.

The integration work then validated, by querying BERDL through Spark, that this
local resource connects strongly to the lakehouse: four of five connection
types matched at better than 90%, linking ADP1 genome IDs, reactions, and
compounds directly into BERDL's pangenome and biochemistry collections. The one
gap is that ADP1 is absent from the Fitness Browser, which is precisely what
makes the local fitness data novel. The most technically involved bridge
reconciles two incompatible identifier schemes: ADP1's mmseqs2-style cluster IDs
and BERDL's centroid gene IDs share no direct string overlap, yet a gene-junction
table maps all 4,891 BERDL clusters onto 4,081 unique ADP1 clusters with 100%
gene-level coverage across 43,754 genes. Together these results establish the
ADP1 resource as a reusable BERDL bridge for downstream synthesis, while also
surfacing a concrete refinement target: the genes where flux-balance predictions
and experimental essentiality disagree.

## Projects in this topic

The topic is anchored by the **Acinetobacter ADP1 Explorer**
(`acinetobacter_adp1_explorer`), an exploration project that inventoried the
multi-omics database, scanned its connectivity to BERDL, and constructed the
pangenome cluster-ID mapping. Its work demonstrates that a comprehensive,
user-provided ADP1 database integrates deeply with BERDL collections and can
therefore serve as a bridge for later ADP1 synthesis pages. The authors of this
work are catalogued at
[0000-0001-5810-2497](../authors/0000-0001-5810-2497.md) and
[0009-0007-0287-2979](../authors/0009-0007-0287-2979.md).

## Adjacent topics

Integration is the substrate for two neighbouring lines of inquiry that draw on
the same database. [ADP1 Carbon Fitness](adp1-carbon-fitness.md) builds on the
mutant growth measurements across eight carbon sources — data unique to this
resource within the lakehouse — to characterise condition-specific fitness.
[ADP1 Model Quality](adp1-model-quality.md) takes up the metabolic-model thread,
including the flux-balance versus essentiality comparison that this topic
exposes as an open direction for model refinement.

## Shared data

The validated connections route ADP1 data into several BERDL collections that
are documented elsewhere in the wiki. Genome IDs and the cluster-ID bridge tie
into the [KBase KE pangenome](../data/kbase-ke-pangenome.md), where all 13
ADP1-related genomes resolve to the *Acinetobacter baylyi* clade. Reactions and
compounds map at 91% and 100% respectively into the
[KBase MSD biochemistry](../data/kbase-msd-biochemistry.md) collection, and
functional annotation overlaps with [KBase UniRef](../data/kbase-uniref.md).
The [KEScience Fitness Browser](../data/kescience-fitnessbrowser.md) is notable
by its absence — ADP1 is not present there, which is what gives the local
carbon-source fitness data its singular value. The
[PhageFoundry](../data/phagefoundry.md) Acinetobacter genome browser was
identified during scanning but left for deeper exploration. The full wiki map is
reachable from the [home page](../index.md).

## Open directions

The clearest opportunity to emerge is the disagreement between the metabolic
model and experimental essentiality. Of the genes carrying both FBA flux
predictions and TnSeq essentiality calls, a discordant subset — 227 genes where
the two disagree — stands out as a priority set for model refinement, with the
open question being whether those genes are enriched for particular pathways or
regulatory functions that flux-balance analysis does not capture. The cluster-ID
mapping additionally opens a route to cross-species fitness comparison against
Fitness Browser organisms, and the PhageFoundry browser remains an untapped
avenue for cross-referencing phage susceptibility with this dataset.

## Sources

- [stmt:adp1-explorer-multiomics-finding; acinetobacter_adp1_explorer]
- [stmt:adp1-explorer-berdl-connectivity-finding; acinetobacter_adp1_explorer]
- [stmt:adp1-explorer-pangenome-bridge-finding; acinetobacter_adp1_explorer]
- [stmt:adp1-explorer-database-bridge-claim; acinetobacter_adp1_explorer]
- [stmt:adp1-explorer-discordance-opportunity; acinetobacter_adp1_explorer]

# KBase KE Pangenome

## Overview

The KBase KE pangenome collection holds the BERDL pangenome clusters that group
orthologous genes across related bacterial genomes, exposing gene-family
membership, centroid gene identifiers, and the junction tables that tie clusters
back to individual gene features. Within the *Acinetobacter baylyi* ADP1 work
that draws on it, the collection acts as the evolutionary backbone: it is the
reference against which strain-specific multi-omics measurements, deletion
phenotypes, and metabolic models are placed in a comparative, cross-genome
context.

Two projects anchor their analyses on this collection. The
[Acinetobacter ADP1 explorer](../topics/adp1-data-integration.md) treats the
pangenome clusters as one of the primary connection points between a
user-provided ADP1 database and the wider BERDL lakehouse, while the
[ADP1 deletion phenotypes](../topics/adp1-carbon-fitness.md) study uses pangenome
conservation as the lens through which carbon-source growth requirements are
interpreted across *Acinetobacter* species. Together they show the collection
functioning less as a standalone dataset and more as connective tissue that lets
phenotype, fitness, and metabolic-model layers be compared on a shared,
gene-cluster coordinate system.

The technically load-bearing result for this collection is the cluster-identifier
bridge. The ADP1 explorer established that BERDL pangenome clusters can be mapped
onto ADP1-style cluster identifiers with complete gene-level coverage — every one
of the 4,891 BERDL clusters resolved to an ADP1 cluster, matching all 43,754
genes — despite the two systems using entirely different naming conventions with
no direct string overlap. The mapping was recovered through BERDL's
gene-to-gene-cluster junction table, which links cluster identifiers to member
gene identifiers and, in turn, to the ADP1 feature table. This bridge is what
makes the pangenome collection usable as a join key rather than an isolated
catalog, and it is the foundation on which the explorer's broader claim of strong
BERDL connectivity rests.

## Projects Using This Collection

### Acinetobacter ADP1 explorer

The [ADP1 explorer](../topics/adp1-data-integration.md) demonstrates that a
comprehensive, user-provided multi-omics database for *A. baylyi* ADP1 integrates
deeply with BERDL, and the pangenome collection is central to that integration.
The underlying database brings together six molecular and phenotype modalities —
TnSeq essentiality, FBA metabolic flux, mutant growth fitness across eight carbon
sources, proteomics across multiple strains, pangenome classification, and
functional annotation — spanning ADP1 and thirteen related genomes. Querying
BERDL confirmed that this database connects strongly through genomes, reactions,
compounds, and pangenome clusters, with the pangenome bridge providing the
gene-level join that ties strain measurements to cross-genome gene families.

On the phenotype side, the explorer found that ADP1 mutant growth fitness has a
clear condition-specific structure, with urea and quinate standing apart as
outlier carbon sources whose fitness profiles are largely uncorrelated with the
rest of the panel. That outlier behavior motivates a proposed follow-up in which
urea-specific fitness genes are examined together with their pangenome
conservation as an independent metabolism module — an analysis that depends
directly on the cluster mapping this collection supplies.

The explorer also surfaces a metabolic-model caveat relevant to anyone reusing
its predictions: ADP1 model-based growth predictions are quality-limited by heavy
reliance on gapfilled reactions, with the large majority of growth-phenotype
predictions depending on at least one gapfilled reaction. This grounds a
prioritized direction to single out the genes where flux-balance analysis and
TnSeq essentiality disagree, using those discordances to guide refinement of the
metabolic model rather than trusting the raw predictions. Both of these threads
feed the explorer's framing of the ADP1 database as a reusable
[BERDL bridge](../topics/adp1-model-quality.md) for downstream ADP1 synthesis
work.

### ADP1 deletion phenotypes

The [deletion-phenotypes](../topics/adp1-carbon-fitness.md) study contributes the
phenotypic layer that the pangenome backbone helps interpret. Profiling deletion
mutants across eight carbon sources, it found that the conditions separate into
demanding, moderate, and robust growth-defect tiers according to the fraction of
genes showing defects. Yet the conditions are far from redundant: low pairwise
correlations across the panel indicate that each carbon source imposes a largely
independent set of gene requirements, so the assays together provide several
independent phenotypic dimensions rather than one shared growth-sensitivity axis.

Pushing further, the study found that gene essentiality varies continuously
across conditions rather than falling into clean functional modules, with one
sharp exception: a small group of genes shows extreme, quinate-specific defects
and forms the only genuinely discrete module in the landscape. From this the
project advances the interpretive claim that ADP1 condition-dependent
essentiality is best modeled as a continuous phenotype landscape, with quinate
degradation treated as the lone discrete exception. Because only eight carbon
sources were assayed, the study also flags an opportunity to expand the panel and
test whether the number of independent phenotypic dimensions grows with broader
condition coverage.

## Adjacent Topics

The projects drawing on this collection thread through three connected topics:
[ADP1 data integration](../topics/adp1-data-integration.md), which covers the
BERDL bridge and multi-omics assembly; [ADP1 carbon fitness](../topics/adp1-carbon-fitness.md),
which covers the carbon-source tier structure, condition independence, and the
quinate exception; and [ADP1 model quality](../topics/adp1-model-quality.md),
which covers the gapfilling caveat and the FBA–TnSeq discordance work. The
authors behind these projects are catalogued at
[0000-0001-5810-2497](../authors/0000-0001-5810-2497.md) and
[0009-0007-0287-2979](../authors/0009-0007-0287-2979.md).

## Open Directions

Several near-term opportunities build directly on this collection. The urea
outlier invites a dedicated module analysis pairing urea-specific fitness genes
with their pangenome conservation. The metabolic model can be sharpened by
prioritizing FBA–TnSeq discordant genes for refinement, given how heavily current
growth predictions lean on gapfilled reactions. And the carbon-fitness map can be
stress-tested by expanding deletion phenotyping beyond the original eight carbon
sources to see whether additional independent dimensions emerge. Each of these
leans on the pangenome cluster mapping to carry strain-level signal into a
comparative, cross-genome frame.

## Sources

- [stmt:adp1-explorer-multiomics-finding; acinetobacter_adp1_explorer]
- [stmt:adp1-explorer-berdl-connectivity-finding; acinetobacter_adp1_explorer]
- [stmt:adp1-explorer-pangenome-bridge-finding; acinetobacter_adp1_explorer]
- [stmt:adp1-explorer-database-bridge-claim; acinetobacter_adp1_explorer]
- [stmt:adp1-explorer-condition-fitness-finding; acinetobacter_adp1_explorer]
- [stmt:adp1-explorer-urea-deep-dive-opportunity; acinetobacter_adp1_explorer]
- [stmt:adp1-explorer-gapfilling-caveat; acinetobacter_adp1_explorer]
- [stmt:adp1-explorer-discordance-opportunity; acinetobacter_adp1_explorer]
- [stmt:adp1-deletion-carbon-tier-finding; adp1_deletion_phenotypes]
- [stmt:adp1-deletion-condition-independence-finding; adp1_deletion_phenotypes]
- [stmt:adp1-deletion-quinate-module-finding; adp1_deletion_phenotypes]
- [stmt:adp1-deletion-continuum-claim; adp1_deletion_phenotypes]
- [stmt:adp1-deletion-expand-carbon-panel-opportunity; adp1_deletion_phenotypes]

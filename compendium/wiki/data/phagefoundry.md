# Phagefoundry

## Overview

Phagefoundry is one of the BERDL data collections surveyed during the
*Acinetobacter baylyi* ADP1 data integration effort, where it surfaced as a
37-table *Acinetobacter* genome browser. To date it has been touched by a single
project, the ADP1 data explorer, which catalogued it as a candidate resource for
cross-referencing phage susceptibility against the strain's genome and fitness
data, but did not yet explore it in depth. The collection therefore sits at the
edge of an actively integrated ADP1 knowledge base whose center of gravity is a
rich, user-provided multi-omics SQLite database for ADP1 and its close relatives.

That neighboring database integrates six molecular and phenotype data modalities
for *Acinetobacter baylyi* ADP1, spanning 15 tables, roughly 461,000 rows, and a
central gene-feature table whose columns cover TnSeq essentiality, FBA metabolic
flux, mutant growth fitness on eight carbon sources, proteomics across multiple
strains, pangenome classification, and functional annotations. Validation against
BERDL confirmed that this ADP1 resource connects strongly to the lakehouse through
genomes, reactions, compounds, and pangenome clusters, four of five tested
connection types matching at greater than 90 percent. On that basis the project
positioned the ADP1 explorer as a reusable bridge into BERDL for downstream ADP1
synthesis work, with Phagefoundry named as one of the still-unexplored resources
on the far side of that bridge.

The integration work also produced concrete analytical results that frame how this
collection might be used. A gene-junction mapping reconciled BERDL pangenome
clusters with the ADP1 database's own cluster identifiers at complete gene-level
coverage, making it possible to carry any BERDL pangenome annotation onto ADP1
genes. Mutant growth fitness across the eight carbon sources showed condition-
specific structure, with urea and quinate standing apart as outlier conditions and
urea behaving as a largely independent metabolism module. Two methodological
caveats and follow-up directions accompany these findings: model-based growth
predictions are heavily dependent on gapfilled reactions and so are quality-limited,
and the genes where FBA and TnSeq disagree on essentiality stand out as priorities
for metabolic model refinement.

## Projects Using This Collection

The [ADP1 Data Integration](../topics/adp1-data-integration.md) topic is the home
for the single project that has so far engaged this collection. That project
inventoried the ADP1 multi-omics database, scanned its connectivity to BERDL, and
built the pangenome cluster bridge that ties the two together. Its results extend
into two adjacent topics. [ADP1 Carbon Fitness](../topics/adp1-carbon-fitness.md)
covers the condition-specific growth fitness analysis, including the urea and
quinate outliers and the proposal to study urea-specific genes and their pangenome
conservation as an independent module. [ADP1 Model Quality](../topics/adp1-model-quality.md)
covers the gapfilling-dependence caveat and the prioritization of FBA-TnSeq
discordant genes for model refinement.

Phagefoundry itself was flagged within this work as an unexplored opportunity:
cross-referencing its *Acinetobacter* genome browser with the phage susceptibility
data it holds against the integrated ADP1 fitness and annotation layers could be a
valuable next step, but that integration has not yet been carried out.

The project's authors are catalogued under
[0000-0001-5810-2497](../authors/0000-0001-5810-2497.md) and
[0009-0007-0287-2979](../authors/0009-0007-0287-2979.md).

## Sources

- [stmt:adp1-explorer-multiomics-finding; acinetobacter_adp1_explorer]
- [stmt:adp1-explorer-berdl-connectivity-finding; acinetobacter_adp1_explorer]
- [stmt:adp1-explorer-database-bridge-claim; acinetobacter_adp1_explorer]
- [stmt:adp1-explorer-pangenome-bridge-finding; acinetobacter_adp1_explorer]
- [stmt:adp1-explorer-condition-fitness-finding; acinetobacter_adp1_explorer]
- [stmt:adp1-explorer-urea-deep-dive-opportunity; acinetobacter_adp1_explorer]
- [stmt:adp1-explorer-gapfilling-caveat; acinetobacter_adp1_explorer]
- [stmt:adp1-explorer-discordance-opportunity; acinetobacter_adp1_explorer]

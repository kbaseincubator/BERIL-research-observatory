# State of the Science

## Overview

This compendium synthesizes a cluster of analyses centered on the soil bacterium
*Acinetobacter baylyi* ADP1, a naturally competent organism that has become a workhorse
for studies of metabolism, gene essentiality, and aromatic-compound degradation. Three
projects anchor the current state of the science. The first, an exploratory data project,
inventories a user-provided multi-omics database for ADP1 and establishes how it connects
to the broader BER Data Lakehouse (BERDL). That database integrates six molecular and
phenotype data modalities — TnSeq essentiality, FBA metabolic flux, mutant growth fitness
across eight carbon sources, proteomics across engineered strains, pangenome classification,
and functional annotation — for ADP1 and thirteen related genomes, providing the substrate
on which the downstream analyses draw. The second project dissects deletion-collection growth
phenotypes across carbon sources, and the third reconciles four independent essentiality
methods (FBA, knockouts, RB-TnSeq, and proteomics) into a single integrated picture.

Read together, these projects converge on a coherent message about how ADP1 phenotypes are
organized and how confidently they can be predicted. Carbon-source dependence is best
understood as a near-continuous landscape rather than a set of discrete functional modules:
across eight carbon sources the conditions separate into demanding, moderate, and robust
growth-defect tiers, and the assays supply several largely independent dimensions of
phenotypic information rather than one shared sensitivity axis. The quinate degradation
pathway is the one prominent exception, behaving as a discrete, condition-specific module
against this otherwise gradient backdrop, while urea emerges as a similarly idiosyncratic
condition whose fitness profile is nearly uncorrelated with the others. On the predictive
side, the work is consistent in cautioning against over-reliance on the metabolic model:
flux-balance class fails to predict which dispensable genes carry measurable growth defects,
and continuous fitness measurements and proteomic abundance both outperform binary
essentiality fractions as essentiality signals.

A connecting thread across all three projects is data integration. The ADP1 explorer
demonstrates that the multi-omics database connects strongly to BERDL through genome
identifiers, biochemistry reactions and compounds, and pangenome clusters, and that a
gene-junction bridge resolves the otherwise incompatible cluster-ID naming schemes with
complete gene-level coverage. This connectivity is what allows the carbon-fitness and
model-quality findings to be placed in comparative-genomic and biochemical context rather
than read in isolation.

## Topic Map

The compendium organizes its findings under three topics, each collecting the statements
that bear on a shared question.

[Adp1 Carbon Fitness](topics/adp1-carbon-fitness.md) covers how ADP1 growth requirements
vary across carbon sources. The deletion-phenotype analysis shows that the eight tested
sources partition into demanding, moderate, and robust tiers and that, with low pairwise
correlations and roughly five independent dimensions, they probe largely separate sets of
gene requirements. Within this continuum, quinate degradation stands out as the single
discrete phenotypic module, and the explorer's correlation analysis flags urea and quinate
as the conditions that behave most independently of the rest.

[Adp1 Model Quality](topics/adp1-model-quality.md) addresses how far the metabolic model can
be trusted. The explorer finds that the large majority of model-based growth predictions
depend on gapfilled reactions, tying predictive accuracy to gapfilling quality, and the
essentiality-reconciliation project shows that FBA class does not predict growth defects
among dispensable genes. The latter project also identifies a clear failure mode: aromatic
degradation genes are strongly enriched among FBA-discordant genes, pointing to systematic
gaps in the model rather than random noise.

[Adp1 Data Integration](topics/adp1-data-integration.md) gathers the connectivity results
that make cross-project synthesis possible — the multi-modal database inventory, the strong
match between ADP1 entities and BERDL collections, and the cluster-ID bridge that joins
BERDL pangenome annotations to ADP1 genes.

## Author Map

The work in this compendium is attributed to two contributors, identified by ORCID:
[0000-0001-5810-2497](authors/0000-0001-5810-2497.md) and
[0009-0007-0287-2979](authors/0009-0007-0287-2979.md). Their individual pages collect the
projects and topics each is associated with.

## Data Map

The analyses draw on, and connect to, several shared data collections in the lakehouse.
The pangenome and comparative-genomic context comes from
[Kbase Ke Pangenome](data/kbase-ke-pangenome.md), to which ADP1 genomes and gene clusters
map completely; reaction and compound grounding comes from
[Kbase Msd Biochemistry](data/kbase-msd-biochemistry.md); and protein-family annotations are
supplied through [Kbase Uniref](data/kbase-uniref.md). Two further collections,
[Kescience Fitnessbrowser](data/kescience-fitnessbrowser.md) and
[Phagefoundry](data/phagefoundry.md), sit adjacent to this work: notably, ADP1 is absent
from the Fitness Browser, which is part of why the project-supplied mutant-growth fitness data
is a distinctive contribution rather than a duplication of existing lakehouse resources.

## Open Directions

Several concrete next steps follow directly from the current findings. Because the
carbon-fitness landscape resolves into roughly five independent dimensions from only eight
conditions, expanding the deletion-phenotyping panel beyond those eight carbon sources would
test whether the number of independent phenotypic dimensions continues to grow with broader
condition coverage. The condition-specific behavior of urea motivates a focused study of its
nearly independent fitness gene set together with the pangenome conservation of those genes,
treating urea catabolism as a self-contained metabolism module. On the modeling side, the set
of genes where FBA and TnSeq disagree is a natural priority list for metabolic-model
refinement, and the specific enrichment of aromatic degradation genes among discordant calls
suggests a targeted fix: adding trace aromatic compounds to the FBA media definition and
retesting whether the discordance resolves. Across all of this, the synthesis recommends
prioritizing continuous fitness values and orthogonal evidence over binary essentiality
thresholds when deciding which genes matter.

## Sources

- [stmt:adp1-explorer-multiomics-finding; acinetobacter_adp1_explorer]
- [stmt:adp1-explorer-database-bridge-claim; acinetobacter_adp1_explorer]
- [stmt:adp1-explorer-berdl-connectivity-finding; acinetobacter_adp1_explorer]
- [stmt:adp1-explorer-pangenome-bridge-finding; acinetobacter_adp1_explorer]
- [stmt:adp1-explorer-condition-fitness-finding; acinetobacter_adp1_explorer]
- [stmt:adp1-explorer-gapfilling-caveat; acinetobacter_adp1_explorer]
- [stmt:adp1-explorer-discordance-opportunity; acinetobacter_adp1_explorer]
- [stmt:adp1-explorer-urea-deep-dive-opportunity; acinetobacter_adp1_explorer]
- [stmt:adp1-deletion-carbon-tier-finding; adp1_deletion_phenotypes]
- [stmt:adp1-deletion-condition-independence-finding; adp1_deletion_phenotypes]
- [stmt:adp1-deletion-continuum-claim; adp1_deletion_phenotypes]
- [stmt:adp1-deletion-quinate-module-finding; adp1_deletion_phenotypes]
- [stmt:adp1-deletion-expand-carbon-panel-opportunity; adp1_deletion_phenotypes]
- [stmt:adp1-triple-fba-growth-caveat; adp1_triple_essentiality]
- [stmt:adp1-triple-continuous-fitness-claim; adp1_triple_essentiality]
- [stmt:adp1-triple-fitness-predictor-finding; adp1_triple_essentiality]
- [stmt:adp1-triple-proteomics-finding; adp1_triple_essentiality]
- [stmt:adp1-triple-aromatic-discordance-finding; adp1_triple_essentiality]
- [stmt:adp1-triple-aromatic-media-opportunity; adp1_triple_essentiality]

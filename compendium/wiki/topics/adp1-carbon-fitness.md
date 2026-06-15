# Topic: ADP1 Carbon Fitness

## Overview

This topic gathers what three projects have learned about how the soil bacterium
*Acinetobacter baylyi* ADP1 allocates gene fitness across different carbon
sources. The central picture that emerges is that carbon-source dependence in
ADP1 is not a single "easy versus hard" axis but a high-dimensional landscape.
Deletion-mutant growth ratios measured across eight carbon sources separate the
conditions into demanding, moderate, and robust tiers, with urea the most
demanding and quinate the most robust. Yet the conditions are only loosely
related to one another: pairwise correlations are low (median Pearson
r = 0.25, maximum r = 0.58), and principal component analysis needs roughly five
components to capture most of the variance. In other words, each carbon source
imposes a largely independent set of gene requirements, so the assays supply
multiple independent phenotypic dimensions rather than one shared
growth-sensitivity axis.

Because the landscape lacks natural cluster boundaries — clustering yields a low
silhouette score and no functional enrichments survive correction — the most
faithful way to describe ADP1 condition-dependent essentiality is as a
continuous phenotype gradient. The one clear exception is a small, discrete
module of quinate-specific genes (the aromatic-degradation pathway), which
stands apart from the otherwise smooth continuum. A complementary multi-omics
analysis reaches the same conclusion from a different direction: across the eight
carbon sources, mutant growth fitness shows condition-specific structure in which
urea and quinate behave as outliers, urea being nearly uncorrelated with the
other conditions.

This continuous, multi-dimensional view also has methodological consequences.
When ADP1 essentiality is benchmarked, continuous TnSeq fitness values are better
predictors than binary essentiality fractions, which argues for prioritizing
continuous fitness and orthogonal evidence over fixed essentiality thresholds
when synthesizing the organism's gene-function map. The same continuity that
makes the carbon-fitness landscape hard to partition is what makes
magnitude-aware fitness measures more informative than hard cutoffs.

## Projects in this topic

Three projects contribute the statements collected here, each approaching ADP1
carbon fitness from a different angle:

- **adp1_deletion_phenotypes** characterizes the eight-carbon-source deletion
  matrix directly. It establishes the demanding/moderate/robust tier structure,
  the low inter-condition correlation and PCA dimensionality, the
  gradient-versus-module architecture of the landscape, and the quinate module
  as its sole discrete exception.
- **acinetobacter_adp1_explorer** examines mutant growth fitness across the same
  carbon sources and identifies urea and quinate as outlier conditions, with urea
  catabolism appearing to draw on a largely independent gene set.
- **adp1_triple_essentiality** compares essentiality signals (FBA, knockouts,
  RB-TnSeq, proteomics, and growth assays) and shows that continuous fitness
  values outperform binary essentiality fractions, motivating a synthesis built
  on continuous fitness rather than thresholds alone.

The authors associated with these projects can be reached via the wiki author
pages: [0000-0001-5810-2497](../authors/0000-0001-5810-2497.md) and
[0009-0007-0287-2979](../authors/0009-0007-0287-2979.md).

## Adjacent topics

Carbon fitness sits next to questions about how well models reproduce these
phenotypes. The closest neighbor is [ADP1 Model Quality](adp1-model-quality.md),
which shares the continuous-fitness claim and the aromatic-media refinement
direction, and where the FBA-discordance findings live. The
[ADP1 Data Integration](adp1-data-integration.md) topic links the underlying
collections and cross-references that make these comparisons possible. The wiki
[home page](../index.md) provides the full topic and data map.

## Shared data

The findings here draw on deletion-phenotype and multi-omics collections for
ADP1 and connect outward to several shared BERDL resources. Pangenome
conservation context — used to ask whether condition-specific or dispensable
gene sets are evolutionarily retained — comes from the
[KBase KE Pangenome](../data/kbase-ke-pangenome.md). Related reference and
comparative collections that the projects touch or could extend into include the
[KBase MSD Biochemistry](../data/kbase-msd-biochemistry.md),
[KBase UniRef](../data/kbase-uniref.md),
[KEScience Fitness Browser](../data/kescience-fitnessbrowser.md), and
[PhageFoundry](../data/phagefoundry.md) collections.

## Open directions

Several concrete follow-ups extend the continuous-landscape picture:

- **Expand the carbon-source panel.** Only eight carbon sources were tested, and
  the roughly five independent phenotypic dimensions observed may grow as more
  conditions are added; profiling deletion mutants on a wider panel would test
  whether dimensionality keeps increasing with condition coverage.
- **Dissect urea metabolism.** Urea's near-zero correlation with the other carbon
  sources points to a largely independent gene set, making ADP1 urea-specific
  fitness genes and their pangenome conservation a natural target for analysis as
  a standalone metabolism module.
- **Refine FBA media for aromatics.** Because aromatic-degradation genes surface
  as a discrete, model-relevant signal, adding trace aromatic compounds to the
  ADP1 FBA media definition and retesting against aromatic-degradation
  discordance is a promising way to close systematic model gaps — a direction
  shared with [ADP1 Model Quality](adp1-model-quality.md).

## Sources

- [stmt:adp1-deletion-carbon-tier-finding; adp1_deletion_phenotypes]
- [stmt:adp1-deletion-condition-independence-finding; adp1_deletion_phenotypes]
- [stmt:adp1-deletion-continuum-claim; adp1_deletion_phenotypes]
- [stmt:adp1-deletion-quinate-module-finding; adp1_deletion_phenotypes]
- [stmt:adp1-deletion-expand-carbon-panel-opportunity; adp1_deletion_phenotypes]
- [stmt:adp1-explorer-condition-fitness-finding; acinetobacter_adp1_explorer]
- [stmt:adp1-explorer-urea-deep-dive-opportunity; acinetobacter_adp1_explorer]
- [stmt:adp1-triple-fitness-predictor-finding; adp1_triple_essentiality]
- [stmt:adp1-triple-continuous-fitness-claim; adp1_triple_essentiality]
- [stmt:adp1-triple-aromatic-media-opportunity; adp1_triple_essentiality]

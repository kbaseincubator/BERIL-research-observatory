# Topic: ADP1 Model Quality

## Overview

This topic gathers work that interrogates how well computational and high-throughput
methods describe gene essentiality and growth in *Acinetobacter baylyi* ADP1. The
central question is one of model quality: when a flux-balance analysis (FBA) model, a
transposon-sequencing (TnSeq) fitness screen, a knockout panel, and proteomics are all
applied to the same organism, where do they agree, where do they diverge, and which
signals best track the underlying biology. The picture that emerges is that no single
method is ground truth and that the most reliable conclusions come from treating
essentiality as a continuous, multi-evidence property rather than a binary label.

Several limits of the ADP1 metabolic model surface clearly. Model-based growth
predictions are heavily dependent on gapfilled reactions, which couples prediction
accuracy directly to gapfilling quality. Within the set of genes that TnSeq calls
dispensable, the FBA essential/variable/blocked classification fails to predict which
genes actually show measured growth defects, the central negative result of the
essentiality work. At the same time, the discordance between methods is itself
informative: aromatic-degradation genes are strongly enriched among the FBA-discordant
genes, pointing at a systematic and explainable gap in the model rather than random
noise. On the positive side, continuous TnSeq fitness values and proteomic expression
both turn out to be strong, complementary predictors of essentiality, each clearly
outperforming a binary essentiality fraction.

## Projects in this topic

Two projects contribute the statements collected here. The
[ADP1 multi-omics data explorer](../data/kbase-msd-biochemistry.md) builds a
comprehensive user-provided database for ADP1 and connects it into the wider data
lakehouse; its model-quality contribution is an audit of where FBA growth predictions
come from and a catalogue of the genes where FBA and TnSeq disagree. The triple
essentiality study runs the head-to-head comparison of FBA, knockouts, RB-TnSeq,
proteomics, and growth assays, and supplies the ROC analyses, concordance tests, and
functional enrichment that anchor most of the quantitative claims on this page. The
two projects are complementary: the explorer frames the model-quality problem and the
data it rests on, while the essentiality study resolves which evidence types are
trustworthy and why the model falls short.

## Adjacent topics

The model-quality discussion overlaps strongly with two neighbouring topics.
[ADP1 Carbon Fitness](./adp1-carbon-fitness.md) shares the continuous-fitness and
aromatic-media threads, because the questions of which fitness signal to trust and
which carbon-source media to simulate are inseparable from how growth is scored.
[ADP1 Data Integration](./adp1-data-integration.md) shares the database-bridge work,
since the assessment of model quality depends on the integrated multi-omics resource
that makes cross-method comparison possible in the first place.

## Shared data

The work draws on several lakehouse collections. The ADP1 explorer demonstrates that a
user-provided ADP1 database integrates deeply with existing collections spanning
[biochemistry and metabolic models](../data/kbase-msd-biochemistry.md),
the [Acinetobacter pangenome](../data/kbase-ke-pangenome.md), and
[UniRef protein families](../data/kbase-uniref.md). Because ADP1 is absent from the
[Fitness Browser](../data/kescience-fitnessbrowser.md), the database's mutant growth
fitness data on multiple carbon sources is a genuinely novel contribution rather than a
duplication. An Acinetobacter genome browser in [PhageFoundry](../data/phagefoundry.md)
was also identified as an unexplored avenue for cross-referencing.

## Open directions

Two refinement opportunities follow directly from the discordance findings. First, the
FBA–TnSeq discordant genes should be prioritized for metabolic model refinement, asking
whether the disagreeing genes are enriched for specific pathways or regulatory
functions. Second, because aromatic-degradation genes drive much of the FBA
discordance and ADP1's experimental media may carry trace aromatics, the FBA media
definition should be refined to include trace aromatic compounds and then retested to
see whether the aromatic-degradation discordance resolves. Both are framed as model
improvements grounded in the observed gaps rather than new biological claims, and both
remain flagged for validation against the underlying continuous-fitness and
database-bridge evidence.

## Sources

- [stmt:adp1-explorer-gapfilling-caveat; acinetobacter_adp1_explorer]
- [stmt:adp1-triple-fba-growth-caveat; adp1_triple_essentiality]
- [stmt:adp1-explorer-database-bridge-claim; acinetobacter_adp1_explorer]
- [stmt:adp1-triple-continuous-fitness-claim; adp1_triple_essentiality]
- [stmt:adp1-triple-aromatic-discordance-finding; adp1_triple_essentiality]
- [stmt:adp1-triple-fitness-predictor-finding; adp1_triple_essentiality]
- [stmt:adp1-triple-proteomics-finding; adp1_triple_essentiality]
- [stmt:adp1-explorer-discordance-opportunity; acinetobacter_adp1_explorer]
- [stmt:adp1-triple-aromatic-media-opportunity; adp1_triple_essentiality]

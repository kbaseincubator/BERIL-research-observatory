# ADP1 essentiality synthesis should prioritize continuous fitness and orthogonal evidence over binary essentiality thresholds alone.

## Introduction

This claim states the triple-essentiality project's measurement rule for ADP1 synthesis: continuous fitness and orthogonal evidence should carry more weight than binary essentiality thresholds alone [stmt:adp1-triple-continuous-fitness-claim; adp1_triple_essentiality].

## Synthesis

The claim is supported directly by the finding that continuous fitness values outperform binary essentiality fractions for predicting ADP1 essentiality. Proteomics also performs as a strong signal and is comparable to continuous fitness in ROC analysis, reinforcing the need for orthogonal evidence [stmt:adp1-triple-fitness-predictor-finding; adp1_triple_essentiality] [stmt:adp1-triple-proteomics-finding; adp1_triple_essentiality].

The model-quality boundary is important. FBA class does not predict which TnSeq-dispensable genes have measured growth defects, and aromatic degradation genes are enriched among FBA-discordant genes, so model class should be interpreted alongside measured fitness and proteomics [stmt:adp1-triple-fba-growth-caveat; adp1_triple_essentiality] [stmt:adp1-triple-aromatic-discordance-finding; adp1_triple_essentiality].

The downstream action is media refinement: trace aromatic compounds should be added to ADP1 FBA media definitions and retested against aromatic-degradation discordance [stmt:adp1-triple-aromatic-media-opportunity; adp1_triple_essentiality].

## Navigation Context

Use [Topic: Adp1 Model Quality](../topics/adp1-model-quality.md) for caveats, [Entity: Fba Model](../entities/fba-model.md) for model context, and [ADP1 FBA media definitions should be refined with trace aromatic compounds and retested against aromatic-degradation discordance.](../opportunities/adp1-triple-aromatic-media-opportunity.md) for the follow-up test [stmt:adp1-triple-aromatic-media-opportunity; adp1_triple_essentiality].

## Source Statements

- `stmt:adp1-triple-continuous-fitness-claim`, `stmt:adp1-triple-fitness-predictor-finding`, and `stmt:adp1-triple-proteomics-finding` define the positive evidence [stmt:adp1-triple-continuous-fitness-claim; adp1_triple_essentiality].
- `stmt:adp1-triple-fba-growth-caveat`, `stmt:adp1-triple-aromatic-discordance-finding`, and `stmt:adp1-triple-aromatic-media-opportunity` define the model-quality implications [stmt:adp1-triple-fba-growth-caveat; adp1_triple_essentiality].
- `stmt:adp1-explorer-gapfilling-caveat` is a cross-project caveat for the same model-quality theme [stmt:adp1-explorer-gapfilling-caveat; acinetobacter_adp1_explorer].

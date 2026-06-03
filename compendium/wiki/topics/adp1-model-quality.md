# Topic: Adp1 Model Quality

## Introduction

ADP1 model quality gathers the caveats and refinement opportunities that limit direct interpretation of FBA and essentiality comparisons. The page is anchored by gapfilling dependence, weak FBA-class prediction of growth defects, and aromatic-degradation discordance [stmt:adp1-explorer-gapfilling-caveat; acinetobacter_adp1_explorer] [stmt:adp1-triple-fba-growth-caveat; adp1_triple_essentiality] [stmt:adp1-triple-aromatic-discordance-finding; adp1_triple_essentiality].

## Synthesis

The explorer caveat says ADP1 model-based growth predictions are quality-limited by heavy dependence on gapfilled reactions. This means model predictions need evidence-aware interpretation before they are used as biological claims [stmt:adp1-explorer-gapfilling-caveat; acinetobacter_adp1_explorer].

The triple-essentiality caveat points in the same direction from a different assay comparison: FBA class does not predict which TnSeq-dispensable ADP1 genes have measured growth defects. That narrows what the model can explain without further refinement [stmt:adp1-triple-fba-growth-caveat; adp1_triple_essentiality].

The constructive path is to prioritize discordant genes and retest media assumptions. Aromatic degradation genes are enriched among FBA-discordant genes, so trace aromatic compounds in media definitions are a concrete hypothesis for model improvement [stmt:adp1-explorer-discordance-opportunity; acinetobacter_adp1_explorer] [stmt:adp1-triple-aromatic-discordance-finding; adp1_triple_essentiality] [stmt:adp1-triple-aromatic-media-opportunity; adp1_triple_essentiality].

Continuous fitness and proteomics should remain visible in this topic because they provide orthogonal evidence against over-reliance on binary thresholds or FBA class alone [stmt:adp1-triple-continuous-fitness-claim; adp1_triple_essentiality] [stmt:adp1-triple-fitness-predictor-finding; adp1_triple_essentiality] [stmt:adp1-triple-proteomics-finding; adp1_triple_essentiality].

## Navigation Context

Use [Entity: Fba Model](../entities/fba-model.md) for the model-centered view, [ADP1 essentiality synthesis should prioritize continuous fitness and orthogonal evidence over binary essentiality thresholds alone.](../claims/adp1-triple-continuous-fitness-claim.md) for measurement guidance, and [ADP1 FBA media definitions should be refined with trace aromatic compounds and retested against aromatic-degradation discordance.](../opportunities/adp1-triple-aromatic-media-opportunity.md) for the main model-improvement action [stmt:adp1-triple-aromatic-media-opportunity; adp1_triple_essentiality].

## Source Statements

- Caveats: `stmt:adp1-explorer-gapfilling-caveat` and `stmt:adp1-triple-fba-growth-caveat` [stmt:adp1-explorer-gapfilling-caveat; acinetobacter_adp1_explorer] [stmt:adp1-triple-fba-growth-caveat; adp1_triple_essentiality].
- Evidence and claims: `stmt:adp1-triple-continuous-fitness-claim`, `stmt:adp1-triple-fitness-predictor-finding`, `stmt:adp1-triple-proteomics-finding`, and `stmt:adp1-triple-aromatic-discordance-finding` [stmt:adp1-triple-continuous-fitness-claim; adp1_triple_essentiality].
- Opportunities: `stmt:adp1-explorer-discordance-opportunity` and `stmt:adp1-triple-aromatic-media-opportunity` [stmt:adp1-explorer-discordance-opportunity; acinetobacter_adp1_explorer].

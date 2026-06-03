# Project: Acinetobacter Adp1 Explorer

## Introduction

The Acinetobacter ADP1 explorer contributes the integration layer for the wiki. It connects ADP1 multiomics, BERDL/pangenome bridging, condition-specific fitness, and model-refinement opportunities [stmt:adp1-explorer-multiomics-finding; acinetobacter_adp1_explorer] [stmt:adp1-explorer-database-bridge-claim; acinetobacter_adp1_explorer].

## Synthesis

The project integrates six molecular and phenotype data modalities and connects strongly to BERDL through genomes, reactions, compounds, and pangenome clusters. A gene-junction bridge maps BERDL pangenome clusters to ADP1-style cluster IDs with complete gene-level coverage [stmt:adp1-explorer-multiomics-finding; acinetobacter_adp1_explorer] [stmt:adp1-explorer-berdl-connectivity-finding; acinetobacter_adp1_explorer] [stmt:adp1-explorer-pangenome-bridge-finding; acinetobacter_adp1_explorer].

Scientifically, the explorer adds condition-specific fitness structure. Urea and quinate behave as outlier conditions, making the project important for both carbon-fitness interpretation and follow-up module analysis [stmt:adp1-explorer-condition-fitness-finding; acinetobacter_adp1_explorer] [stmt:adp1-explorer-urea-deep-dive-opportunity; acinetobacter_adp1_explorer].

The project also exposes model-quality limits. Heavy gapfilling dependence constrains growth predictions, so FBA-TnSeq discordant genes should be prioritized for refinement rather than accepted as settled model outputs [stmt:adp1-explorer-gapfilling-caveat; acinetobacter_adp1_explorer] [stmt:adp1-explorer-discordance-opportunity; acinetobacter_adp1_explorer].

## Navigation Context

Use [Topic: Adp1 Data Integration](../topics/adp1-data-integration.md) for the bridge role, [Topic: Adp1 Model Quality](../topics/adp1-model-quality.md) for caveats, and [Entity: Berdl](../entities/berdl.md) for the external data connection [stmt:adp1-explorer-database-bridge-claim; acinetobacter_adp1_explorer].

## Source Statements

- Integration: `stmt:adp1-explorer-database-bridge-claim`, `stmt:adp1-explorer-multiomics-finding`, `stmt:adp1-explorer-pangenome-bridge-finding`, and `stmt:adp1-explorer-berdl-connectivity-finding` [stmt:adp1-explorer-database-bridge-claim; acinetobacter_adp1_explorer].
- Fitness and model follow-up: `stmt:adp1-explorer-condition-fitness-finding`, `stmt:adp1-explorer-urea-deep-dive-opportunity`, `stmt:adp1-explorer-gapfilling-caveat`, and `stmt:adp1-explorer-discordance-opportunity` [stmt:adp1-explorer-condition-fitness-finding; acinetobacter_adp1_explorer].

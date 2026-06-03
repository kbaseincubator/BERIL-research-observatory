# Topic: Adp1 Data Integration

## Introduction

ADP1 data integration is the topic for understanding how the explorer turns project-local outputs into reusable synthesis infrastructure. Its central claim is that the ADP1 data explorer can serve as a BERDL bridge for downstream ADP1 synthesis pages [stmt:adp1-explorer-database-bridge-claim; acinetobacter_adp1_explorer].

## Synthesis

The explorer's value starts with breadth: it integrates six molecular and phenotype data modalities for Acinetobacter baylyi ADP1. That multiomics base gives synthesis pages a common place to connect fitness, pangenome, reaction, and phenotype evidence [stmt:adp1-explorer-multiomics-finding; acinetobacter_adp1_explorer].

The bridge to BERDL is more than a label. The explorer maps BERDL pangenome clusters to ADP1-style cluster IDs with complete gene-level coverage and connects strongly to BERDL through genomes, reactions, compounds, and pangenome clusters [stmt:adp1-explorer-pangenome-bridge-finding; acinetobacter_adp1_explorer] [stmt:adp1-explorer-berdl-connectivity-finding; acinetobacter_adp1_explorer].

This topic also exposes where integration should drive model work. If FBA-TnSeq discordant genes are prioritized for metabolic model refinement, the explorer becomes a triage surface rather than only a static database [stmt:adp1-explorer-discordance-opportunity; acinetobacter_adp1_explorer].

## Navigation Context

Use [The ADP1 data explorer can serve as a BERDL bridge for downstream ADP1 synthesis pages.](../claims/adp1-explorer-database-bridge-claim.md) for the claim-level view, [Entity: Berdl](../entities/berdl.md) for the external integration target, and [Entity: Adp1 Multiomics Database](../entities/adp1-multiomics-database.md) for the collection-level anchor [stmt:adp1-explorer-database-bridge-claim; acinetobacter_adp1_explorer].

## Source Statements

- `stmt:adp1-explorer-database-bridge-claim`: the explorer is a BERDL bridge for downstream synthesis pages [stmt:adp1-explorer-database-bridge-claim; acinetobacter_adp1_explorer].
- `stmt:adp1-explorer-multiomics-finding`, `stmt:adp1-explorer-pangenome-bridge-finding`, and `stmt:adp1-explorer-berdl-connectivity-finding`: the evidence base for integration [stmt:adp1-explorer-multiomics-finding; acinetobacter_adp1_explorer].
- `stmt:adp1-explorer-discordance-opportunity`: the model-refinement use case [stmt:adp1-explorer-discordance-opportunity; acinetobacter_adp1_explorer].

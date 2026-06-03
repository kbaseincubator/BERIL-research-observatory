# The ADP1 data explorer can serve as a BERDL bridge for downstream ADP1 synthesis pages.

## Introduction

This claim explains why the explorer is part of the wiki's synthesis layer. It positions the ADP1 data explorer as a bridge from project-local ADP1 data into BERDL-connected downstream synthesis [stmt:adp1-explorer-database-bridge-claim; acinetobacter_adp1_explorer].

## Synthesis

The bridge rests on three pieces of evidence. The explorer integrates six molecular and phenotype data modalities, maps BERDL pangenome clusters to ADP1-style cluster IDs with complete gene-level coverage, and connects strongly to BERDL through genomes, reactions, compounds, and pangenome clusters [stmt:adp1-explorer-multiomics-finding; acinetobacter_adp1_explorer] [stmt:adp1-explorer-pangenome-bridge-finding; acinetobacter_adp1_explorer] [stmt:adp1-explorer-berdl-connectivity-finding; acinetobacter_adp1_explorer].

The claim is useful because it links data integration to model work. FBA-TnSeq discordant genes can be prioritized for metabolic model refinement, but the model-quality caveats mean those priorities should be checked rather than treated as resolved [stmt:adp1-explorer-discordance-opportunity; acinetobacter_adp1_explorer] [stmt:adp1-explorer-gapfilling-caveat; acinetobacter_adp1_explorer] [stmt:adp1-triple-fba-growth-caveat; adp1_triple_essentiality].

## Navigation Context

Use [Topic: Adp1 Data Integration](../topics/adp1-data-integration.md) for the topic view, [Entity: Berdl](../entities/berdl.md) for the external bridge, and [Entity: Adp1 Multiomics Database](../entities/adp1-multiomics-database.md) for the collection anchor [stmt:adp1-explorer-database-bridge-claim; acinetobacter_adp1_explorer].

## Source Statements

- `stmt:adp1-explorer-database-bridge-claim`: bridge claim [stmt:adp1-explorer-database-bridge-claim; acinetobacter_adp1_explorer].
- `stmt:adp1-explorer-multiomics-finding`, `stmt:adp1-explorer-pangenome-bridge-finding`, and `stmt:adp1-explorer-berdl-connectivity-finding`: bridge evidence [stmt:adp1-explorer-pangenome-bridge-finding; acinetobacter_adp1_explorer].
- `stmt:adp1-explorer-discordance-opportunity`, `stmt:adp1-explorer-gapfilling-caveat`, and `stmt:adp1-triple-fba-growth-caveat`: model-quality implications [stmt:adp1-explorer-discordance-opportunity; acinetobacter_adp1_explorer].

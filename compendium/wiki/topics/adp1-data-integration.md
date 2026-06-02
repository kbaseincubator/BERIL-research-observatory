---
page_id: topic:adp1-data-integration
page_type: topic
member_hash: hash:a1d3cb530bff6c02
---

# Topic: Adp1 Data Integration

- Page type: `topic`
- Member hash: `hash:a1d3cb530bff6c02`
- Graph: [Graph](../graph.md)

## Outgoing Links

- [Adp1 Explorer Database Bridge Claim](../claims/adp1-explorer-database-bridge-claim.md)
- [Adp1 Multiomics Database](../entities/adp1-multiomics-database.md)
- [Adp1](../entities/adp1.md)
- [Berdl](../entities/berdl.md)
- [Fba Model](../entities/fba-model.md)
- [Adp1 Explorer Discordance Opportunity](../opportunities/adp1-explorer-discordance-opportunity.md)
- [Acinetobacter Adp1 Explorer](../projects/acinetobacter-adp1-explorer.md)
- [Adp1 Model Quality](../topics/adp1-model-quality.md)

## Backlinks

- [Adp1 Explorer Database Bridge Claim](../claims/adp1-explorer-database-bridge-claim.md)
- [Adp1 Multiomics Database](../entities/adp1-multiomics-database.md)
- [Adp1](../entities/adp1.md)
- [Berdl](../entities/berdl.md)
- [Home](../index.md)
- [Adp1 Deletion Expand Carbon Panel Opportunity](../opportunities/adp1-deletion-expand-carbon-panel-opportunity.md)
- [Adp1 Explorer Discordance Opportunity](../opportunities/adp1-explorer-discordance-opportunity.md)
- [Adp1 Explorer Urea Deep Dive Opportunity](../opportunities/adp1-explorer-urea-deep-dive-opportunity.md)
- [Adp1 Triple Aromatic Media Opportunity](../opportunities/adp1-triple-aromatic-media-opportunity.md)
- [Acinetobacter Adp1 Explorer](../projects/acinetobacter-adp1-explorer.md)
- [Adp1 Model Quality](../topics/adp1-model-quality.md)

## Conflicts And Caveats

No statements selected for this section.

## Findings

- `stmt:adp1-explorer-berdl-connectivity-finding`: The ADP1 database connects strongly to BERDL through genomes, reactions, compounds, and pangenome clusters. `finding` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)
- `stmt:adp1-explorer-multiomics-finding`: The ADP1 database integrates six molecular and phenotype data modalities for Acinetobacter baylyi ADP1. `finding` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)
- `stmt:adp1-explorer-pangenome-bridge-finding`: A gene-junction bridge maps BERDL pangenome clusters to ADP1-style cluster IDs with complete gene-level coverage. `finding` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)

## Key Claims

- [stmt:adp1-explorer-database-bridge-claim](../claims/adp1-explorer-database-bridge-claim.md): The ADP1 data explorer can serve as a BERDL bridge for downstream ADP1 synthesis pages. `claim` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)

## Opportunities And Directions

- [stmt:adp1-explorer-discordance-opportunity](../opportunities/adp1-explorer-discordance-opportunity.md): FBA-TnSeq discordant genes in ADP1 should be prioritized for metabolic model refinement. `opportunity` `grounded` `medium` (acinetobacter_adp1_explorer/REPORT.md)

## Overview

- `stmt:adp1-explorer-berdl-connectivity-finding`: The ADP1 database connects strongly to BERDL through genomes, reactions, compounds, and pangenome clusters. `finding` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)
- [stmt:adp1-explorer-database-bridge-claim](../claims/adp1-explorer-database-bridge-claim.md): The ADP1 data explorer can serve as a BERDL bridge for downstream ADP1 synthesis pages. `claim` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)
- [stmt:adp1-explorer-discordance-opportunity](../opportunities/adp1-explorer-discordance-opportunity.md): FBA-TnSeq discordant genes in ADP1 should be prioritized for metabolic model refinement. `opportunity` `grounded` `medium` (acinetobacter_adp1_explorer/REPORT.md)
- `stmt:adp1-explorer-multiomics-finding`: The ADP1 database integrates six molecular and phenotype data modalities for Acinetobacter baylyi ADP1. `finding` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)
- `stmt:adp1-explorer-pangenome-bridge-finding`: A gene-junction bridge maps BERDL pangenome clusters to ADP1-style cluster IDs with complete gene-level coverage. `finding` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)

## Reusable Products And Methods

No statements selected for this section.

## Source Statements

### stmt:adp1-explorer-berdl-connectivity-finding

The ADP1 database connects strongly to BERDL through genomes, reactions, compounds, and pangenome clusters.

- Kind/tier/confidence: `finding` / `grounded` / `high`
- Scope: `project_local`
- Source: `acinetobacter_adp1_explorer/REPORT.md`
- Section: `Key Findings`
- Evidence: Querying BERDL via Spark validated that the ADP1 database connects strongly to BERDL collections
- Notebook: `02_berdl_connection_scan.ipynb`
- Topics: [Adp1 Data Integration](../topics/adp1-data-integration.md)
- Entities: [Adp1](../entities/adp1.md), [Berdl](../entities/berdl.md)
- Supports: [stmt:adp1-explorer-database-bridge-claim](../claims/adp1-explorer-database-bridge-claim.md)

### stmt:adp1-explorer-database-bridge-claim

The ADP1 data explorer can serve as a BERDL bridge for downstream ADP1 synthesis pages.

- Kind/tier/confidence: `claim` / `grounded` / `high`
- Scope: `project_local`
- Source: `acinetobacter_adp1_explorer/REPORT.md`
- Section: `Interpretation`
- Evidence: This exploration project demonstrates that a comprehensive user-provided database for *A. baylyi* ADP1 integrates deeply with BERDL collections.
- Topics: [Adp1 Data Integration](../topics/adp1-data-integration.md)
- Entities: [Adp1](../entities/adp1.md), [Berdl](../entities/berdl.md)
- Motivates: [stmt:adp1-explorer-discordance-opportunity](../opportunities/adp1-explorer-discordance-opportunity.md)

### stmt:adp1-explorer-discordance-opportunity

FBA-TnSeq discordant genes in ADP1 should be prioritized for metabolic model refinement.

- Kind/tier/confidence: `opportunity` / `grounded` / `medium`
- Scope: `project_local`
- Source: `acinetobacter_adp1_explorer/REPORT.md`
- Section: `Research Questions Answered`
- Evidence: The 227 genes where FBA and TnSeq disagree on essentiality could guide metabolic model refinement
- Topics: [Adp1 Model Quality](../topics/adp1-model-quality.md)
- Entities: [Adp1](../entities/adp1.md), [Fba Model](../entities/fba-model.md)
- Requires Validation: [stmt:adp1-explorer-database-bridge-claim](../claims/adp1-explorer-database-bridge-claim.md)

### stmt:adp1-explorer-multiomics-finding

The ADP1 database integrates six molecular and phenotype data modalities for Acinetobacter baylyi ADP1.

- Kind/tier/confidence: `finding` / `grounded` / `high`
- Scope: `project_local`
- Source: `acinetobacter_adp1_explorer/REPORT.md`
- Section: `Key Findings`
- Evidence: The user-provided SQLite database contains 15 tables with 461,522 total rows and 135 MB of data for *Acinetobacter baylyi* ADP1 and 13 related genomes.
- Figure: `figures/data_coverage_by_modality.png`
- Notebook: `01_database_exploration.ipynb`
- Topics: [Adp1 Data Integration](../topics/adp1-data-integration.md)
- Entities: [Adp1 Multiomics Database](../entities/adp1-multiomics-database.md), [Adp1](../entities/adp1.md)
- Supports: [stmt:adp1-explorer-database-bridge-claim](../claims/adp1-explorer-database-bridge-claim.md)

### stmt:adp1-explorer-pangenome-bridge-finding

A gene-junction bridge maps BERDL pangenome clusters to ADP1-style cluster IDs with complete gene-level coverage.

- Kind/tier/confidence: `finding` / `grounded` / `high`
- Scope: `project_local`
- Source: `acinetobacter_adp1_explorer/REPORT.md`
- Section: `Key Findings`
- Evidence: All 4,891 BERDL clusters mapped successfully to 4,081 unique ADP1 clusters (100% gene-level match across 43,754 genes).
- Notebook: `03_cluster_id_mapping.ipynb`
- Topics: [Adp1 Data Integration](../topics/adp1-data-integration.md)
- Entities: [Adp1](../entities/adp1.md), [Berdl](../entities/berdl.md)
- Supports: [stmt:adp1-explorer-database-bridge-claim](../claims/adp1-explorer-database-bridge-claim.md)

## Local Graph

- `navigation_edge` `about_entity`: `stmt:adp1-explorer-berdl-connectivity-finding` -> `entity:adp1`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-berdl-connectivity-finding` -> `entity:berdl`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-berdl-connectivity-finding` -> `entity:collection:adp1_multiomics_database`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-database-bridge-claim` -> `entity:adp1`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-database-bridge-claim` -> `entity:berdl`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-database-bridge-claim` -> `entity:collection:adp1_multiomics_database`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-discordance-opportunity` -> `entity:adp1`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-discordance-opportunity` -> `entity:dataset:adp1-fba-tnseq-discordance-prioritization`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-discordance-opportunity` -> `entity:fba_model`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-multiomics-finding` -> `entity:adp1`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-multiomics-finding` -> `entity:collection:adp1_multiomics_database`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-pangenome-bridge-finding` -> `entity:adp1`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-pangenome-bridge-finding` -> `entity:berdl`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-pangenome-bridge-finding` -> `entity:collection:adp1_multiomics_database`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-pangenome-bridge-finding` -> `entity:dataset:cluster_id_mapping`
- `navigation_edge` `member_of_topic`: `stmt:adp1-explorer-berdl-connectivity-finding` -> `topic:adp1-data-integration`
- `navigation_edge` `member_of_topic`: `stmt:adp1-explorer-database-bridge-claim` -> `topic:adp1-data-integration`
- `navigation_edge` `member_of_topic`: `stmt:adp1-explorer-discordance-opportunity` -> `topic:adp1-model-quality`
- `navigation_edge` `member_of_topic`: `stmt:adp1-explorer-multiomics-finding` -> `topic:adp1-data-integration`
- `navigation_edge` `member_of_topic`: `stmt:adp1-explorer-pangenome-bridge-finding` -> `topic:adp1-data-integration`
- `provenance_edge` `cites`: `evidence:c3459b3f8a925fd2` -> `figure:acinetobacter_adp1_explorer:figures/data_coverage_by_modality.png`
- `provenance_edge` `extracted_from`: `evidence:28856b6abc9a30ad` -> `project:acinetobacter_adp1_explorer`
- `provenance_edge` `extracted_from`: `evidence:28856b6abc9a30ad` -> `source_doc:acinetobacter_adp1_explorer:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:28856b6abc9a30ad` -> `source_section:acinetobacter_adp1_explorer:REPORT.md:Key Findings`
- `provenance_edge` `extracted_from`: `evidence:3b0ff3cf4b39cb89` -> `project:acinetobacter_adp1_explorer`
- `provenance_edge` `extracted_from`: `evidence:3b0ff3cf4b39cb89` -> `source_doc:acinetobacter_adp1_explorer:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:3b0ff3cf4b39cb89` -> `source_section:acinetobacter_adp1_explorer:REPORT.md:Research Questions Answered`
- `provenance_edge` `extracted_from`: `evidence:935d82e583994f8c` -> `project:acinetobacter_adp1_explorer`
- `provenance_edge` `extracted_from`: `evidence:935d82e583994f8c` -> `source_doc:acinetobacter_adp1_explorer:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:935d82e583994f8c` -> `source_section:acinetobacter_adp1_explorer:REPORT.md:Key Findings`
- `provenance_edge` `extracted_from`: `evidence:c3459b3f8a925fd2` -> `project:acinetobacter_adp1_explorer`
- `provenance_edge` `extracted_from`: `evidence:c3459b3f8a925fd2` -> `source_doc:acinetobacter_adp1_explorer:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:c3459b3f8a925fd2` -> `source_section:acinetobacter_adp1_explorer:REPORT.md:Key Findings`
- `provenance_edge` `extracted_from`: `evidence:c9ca6ed0aa39959b` -> `project:acinetobacter_adp1_explorer`
- `provenance_edge` `extracted_from`: `evidence:c9ca6ed0aa39959b` -> `source_doc:acinetobacter_adp1_explorer:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:c9ca6ed0aa39959b` -> `source_section:acinetobacter_adp1_explorer:REPORT.md:Interpretation`
- `provenance_edge` `has_evidence`: `stmt:adp1-explorer-berdl-connectivity-finding` -> `evidence:28856b6abc9a30ad`
- `provenance_edge` `has_evidence`: `stmt:adp1-explorer-database-bridge-claim` -> `evidence:c9ca6ed0aa39959b`
- `provenance_edge` `has_evidence`: `stmt:adp1-explorer-discordance-opportunity` -> `evidence:3b0ff3cf4b39cb89`
- `provenance_edge` `has_evidence`: `stmt:adp1-explorer-multiomics-finding` -> `evidence:c3459b3f8a925fd2`
- `provenance_edge` `has_evidence`: `stmt:adp1-explorer-pangenome-bridge-finding` -> `evidence:935d82e583994f8c`
- `provenance_edge` `uses_notebook`: `evidence:28856b6abc9a30ad` -> `notebook:acinetobacter_adp1_explorer:02_berdl_connection_scan.ipynb`
- `provenance_edge` `uses_notebook`: `evidence:935d82e583994f8c` -> `notebook:acinetobacter_adp1_explorer:03_cluster_id_mapping.ipynb`
- `provenance_edge` `uses_notebook`: `evidence:c3459b3f8a925fd2` -> `notebook:acinetobacter_adp1_explorer:01_database_exploration.ipynb`
- `review_edge` `needs_review`: `stmt:adp1-explorer-discordance-opportunity` -> `stmt:adp1-explorer-database-bridge-claim`
- `scientific_edge` `motivates`: `stmt:adp1-explorer-database-bridge-claim` -> `stmt:adp1-explorer-discordance-opportunity`
- `scientific_edge` `motivates`: `stmt:adp1-explorer-gapfilling-caveat` -> `stmt:adp1-explorer-discordance-opportunity`
- `scientific_edge` `supports`: `stmt:adp1-explorer-berdl-connectivity-finding` -> `stmt:adp1-explorer-database-bridge-claim`
- `scientific_edge` `supports`: `stmt:adp1-explorer-multiomics-finding` -> `stmt:adp1-explorer-database-bridge-claim`
- `scientific_edge` `supports`: `stmt:adp1-explorer-pangenome-bridge-finding` -> `stmt:adp1-explorer-database-bridge-claim`

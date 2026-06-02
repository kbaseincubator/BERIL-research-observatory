---
page_id: entity:berdl
page_type: entity
member_hash: hash:66f97432d561c869
---

# Entity: Berdl

- Page type: `entity`
- Member hash: `hash:66f97432d561c869`
- Graph: [Graph](../graph.md)

## Introduction

This entity page is a backlink hub for Entity: Berdl. It gathers 3 statements from `acinetobacter_adp1_explorer` and shows how the entity participates in findings, claims, caveats, and opportunities across the wiki.

## Synthesis

A central reusable claim frames this page. [stmt:adp1-explorer-database-bridge-claim](../claims/adp1-explorer-database-bridge-claim.md) states that The ADP1 data explorer can serve as a BERDL bridge for downstream ADP1 synthesis pages. [stmt:adp1-explorer-database-bridge-claim; acinetobacter_adp1_explorer].
The evidence base is anchored by several findings. `stmt:adp1-explorer-berdl-connectivity-finding` states that The ADP1 database connects strongly to BERDL through genomes, reactions, compounds, and pangenome clusters. [stmt:adp1-explorer-berdl-connectivity-finding; acinetobacter_adp1_explorer]. `stmt:adp1-explorer-pangenome-bridge-finding` states that A gene-junction bridge maps BERDL pangenome clusters to ADP1-style cluster IDs with complete gene-level coverage. [stmt:adp1-explorer-pangenome-bridge-finding; acinetobacter_adp1_explorer].

## Navigation Context

This page links out to 5 related pages and has 10 backlinks. Use those links to move between the prose note, the underlying evidence, and the graph neighborhood.

## Structured Evidence Summary

### Backlinks

- `stmt:adp1-explorer-berdl-connectivity-finding`: The ADP1 database connects strongly to BERDL through genomes, reactions, compounds, and pangenome clusters. `finding` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)
- [stmt:adp1-explorer-database-bridge-claim](../claims/adp1-explorer-database-bridge-claim.md): The ADP1 data explorer can serve as a BERDL bridge for downstream ADP1 synthesis pages. `claim` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)
- `stmt:adp1-explorer-pangenome-bridge-finding`: A gene-junction bridge maps BERDL pangenome clusters to ADP1-style cluster IDs with complete gene-level coverage. `finding` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)

### Claims

- [stmt:adp1-explorer-database-bridge-claim](../claims/adp1-explorer-database-bridge-claim.md): The ADP1 data explorer can serve as a BERDL bridge for downstream ADP1 synthesis pages. `claim` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)

### Conflicts And Caveats

No statements selected for this section.

### Findings

- `stmt:adp1-explorer-berdl-connectivity-finding`: The ADP1 database connects strongly to BERDL through genomes, reactions, compounds, and pangenome clusters. `finding` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)
- `stmt:adp1-explorer-pangenome-bridge-finding`: A gene-junction bridge maps BERDL pangenome clusters to ADP1-style cluster IDs with complete gene-level coverage. `finding` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)

### Opportunities And Directions

No statements selected for this section.

### Topic: Adp1 Data Integration

- `stmt:adp1-explorer-berdl-connectivity-finding`: The ADP1 database connects strongly to BERDL through genomes, reactions, compounds, and pangenome clusters. `finding` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)
- [stmt:adp1-explorer-database-bridge-claim](../claims/adp1-explorer-database-bridge-claim.md): The ADP1 data explorer can serve as a BERDL bridge for downstream ADP1 synthesis pages. `claim` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)
- `stmt:adp1-explorer-pangenome-bridge-finding`: A gene-junction bridge maps BERDL pangenome clusters to ADP1-style cluster IDs with complete gene-level coverage. `finding` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)

## Outgoing Links

- [Adp1 Explorer Database Bridge Claim](../claims/adp1-explorer-database-bridge-claim.md)
- [Adp1](../entities/adp1.md)
- [Adp1 Explorer Discordance Opportunity](../opportunities/adp1-explorer-discordance-opportunity.md)
- [Acinetobacter Adp1 Explorer](../projects/acinetobacter-adp1-explorer.md)
- [Adp1 Data Integration](../topics/adp1-data-integration.md)

## Backlinks

- [Adp1 Explorer Database Bridge Claim](../claims/adp1-explorer-database-bridge-claim.md)
- [Adp1](../entities/adp1.md)
- [Home](../index.md)
- [Adp1 Deletion Expand Carbon Panel Opportunity](../opportunities/adp1-deletion-expand-carbon-panel-opportunity.md)
- [Adp1 Explorer Discordance Opportunity](../opportunities/adp1-explorer-discordance-opportunity.md)
- [Adp1 Explorer Urea Deep Dive Opportunity](../opportunities/adp1-explorer-urea-deep-dive-opportunity.md)
- [Adp1 Triple Aromatic Media Opportunity](../opportunities/adp1-triple-aromatic-media-opportunity.md)
- [Acinetobacter Adp1 Explorer](../projects/acinetobacter-adp1-explorer.md)
- [Adp1 Data Integration](../topics/adp1-data-integration.md)
- [Adp1 Model Quality](../topics/adp1-model-quality.md)

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
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-pangenome-bridge-finding` -> `entity:adp1`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-pangenome-bridge-finding` -> `entity:berdl`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-pangenome-bridge-finding` -> `entity:collection:adp1_multiomics_database`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-pangenome-bridge-finding` -> `entity:dataset:cluster_id_mapping`
- `navigation_edge` `member_of_topic`: `stmt:adp1-explorer-berdl-connectivity-finding` -> `topic:adp1-data-integration`
- `navigation_edge` `member_of_topic`: `stmt:adp1-explorer-database-bridge-claim` -> `topic:adp1-data-integration`
- `navigation_edge` `member_of_topic`: `stmt:adp1-explorer-pangenome-bridge-finding` -> `topic:adp1-data-integration`
- `provenance_edge` `extracted_from`: `evidence:28856b6abc9a30ad` -> `project:acinetobacter_adp1_explorer`
- `provenance_edge` `extracted_from`: `evidence:28856b6abc9a30ad` -> `source_doc:acinetobacter_adp1_explorer:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:28856b6abc9a30ad` -> `source_section:acinetobacter_adp1_explorer:REPORT.md:Key Findings`
- `provenance_edge` `extracted_from`: `evidence:935d82e583994f8c` -> `project:acinetobacter_adp1_explorer`
- `provenance_edge` `extracted_from`: `evidence:935d82e583994f8c` -> `source_doc:acinetobacter_adp1_explorer:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:935d82e583994f8c` -> `source_section:acinetobacter_adp1_explorer:REPORT.md:Key Findings`
- `provenance_edge` `extracted_from`: `evidence:c9ca6ed0aa39959b` -> `project:acinetobacter_adp1_explorer`
- `provenance_edge` `extracted_from`: `evidence:c9ca6ed0aa39959b` -> `source_doc:acinetobacter_adp1_explorer:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:c9ca6ed0aa39959b` -> `source_section:acinetobacter_adp1_explorer:REPORT.md:Interpretation`
- `provenance_edge` `has_evidence`: `stmt:adp1-explorer-berdl-connectivity-finding` -> `evidence:28856b6abc9a30ad`
- `provenance_edge` `has_evidence`: `stmt:adp1-explorer-database-bridge-claim` -> `evidence:c9ca6ed0aa39959b`
- `provenance_edge` `has_evidence`: `stmt:adp1-explorer-pangenome-bridge-finding` -> `evidence:935d82e583994f8c`
- `provenance_edge` `uses_notebook`: `evidence:28856b6abc9a30ad` -> `notebook:acinetobacter_adp1_explorer:02_berdl_connection_scan.ipynb`
- `provenance_edge` `uses_notebook`: `evidence:935d82e583994f8c` -> `notebook:acinetobacter_adp1_explorer:03_cluster_id_mapping.ipynb`
- `review_edge` `needs_review`: `stmt:adp1-explorer-discordance-opportunity` -> `stmt:adp1-explorer-database-bridge-claim`
- `scientific_edge` `motivates`: `stmt:adp1-explorer-database-bridge-claim` -> `stmt:adp1-explorer-discordance-opportunity`
- `scientific_edge` `supports`: `stmt:adp1-explorer-berdl-connectivity-finding` -> `stmt:adp1-explorer-database-bridge-claim`
- `scientific_edge` `supports`: `stmt:adp1-explorer-multiomics-finding` -> `stmt:adp1-explorer-database-bridge-claim`
- `scientific_edge` `supports`: `stmt:adp1-explorer-pangenome-bridge-finding` -> `stmt:adp1-explorer-database-bridge-claim`

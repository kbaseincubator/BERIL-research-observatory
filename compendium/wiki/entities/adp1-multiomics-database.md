---
page_id: collection:adp1_multiomics_database
page_type: entity
member_hash: hash:240fdf71c40f0a84
---

# Entity: Adp1 Multiomics Database

- Page type: `entity`
- Member hash: `hash:240fdf71c40f0a84`
- Graph: [Graph](../graph.md)

## Introduction

This entity page is a backlink hub for Entity: Adp1 Multiomics Database. It gathers 1 statements from `acinetobacter_adp1_explorer` and shows how the entity participates in findings, claims, caveats, and opportunities across the wiki.

## Synthesis

The evidence base is anchored by one finding. `stmt:adp1-explorer-multiomics-finding` states that The ADP1 database integrates six molecular and phenotype data modalities for Acinetobacter baylyi ADP1. [stmt:adp1-explorer-multiomics-finding; acinetobacter_adp1_explorer].

## Navigation Context

This page links out to 4 related pages and has 5 backlinks. Use those links to move between the prose note, the underlying evidence, and the graph neighborhood.

## Structured Evidence Summary

### Backlinks

- `stmt:adp1-explorer-multiomics-finding`: The ADP1 database integrates six molecular and phenotype data modalities for Acinetobacter baylyi ADP1. `finding` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)

### Claims

No statements selected for this section.

### Conflicts And Caveats

No statements selected for this section.

### Findings

- `stmt:adp1-explorer-multiomics-finding`: The ADP1 database integrates six molecular and phenotype data modalities for Acinetobacter baylyi ADP1. `finding` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)

### Opportunities And Directions

No statements selected for this section.

### Topic: Adp1 Data Integration

- `stmt:adp1-explorer-multiomics-finding`: The ADP1 database integrates six molecular and phenotype data modalities for Acinetobacter baylyi ADP1. `finding` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)

## Outgoing Links

- [Adp1 Explorer Database Bridge Claim](../claims/adp1-explorer-database-bridge-claim.md)
- [Adp1](../entities/adp1.md)
- [Acinetobacter Adp1 Explorer](../projects/acinetobacter-adp1-explorer.md)
- [Adp1 Data Integration](../topics/adp1-data-integration.md)

## Backlinks

- [Adp1 Explorer Database Bridge Claim](../claims/adp1-explorer-database-bridge-claim.md)
- [Adp1](../entities/adp1.md)
- [Home](../index.md)
- [Acinetobacter Adp1 Explorer](../projects/acinetobacter-adp1-explorer.md)
- [Adp1 Data Integration](../topics/adp1-data-integration.md)

## Source Statements

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

## Local Graph

- `navigation_edge` `about_entity`: `stmt:adp1-explorer-multiomics-finding` -> `entity:adp1`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-multiomics-finding` -> `entity:collection:adp1_multiomics_database`
- `navigation_edge` `member_of_topic`: `stmt:adp1-explorer-multiomics-finding` -> `topic:adp1-data-integration`
- `provenance_edge` `cites`: `evidence:c3459b3f8a925fd2` -> `figure:acinetobacter_adp1_explorer:figures/data_coverage_by_modality.png`
- `provenance_edge` `extracted_from`: `evidence:c3459b3f8a925fd2` -> `project:acinetobacter_adp1_explorer`
- `provenance_edge` `extracted_from`: `evidence:c3459b3f8a925fd2` -> `source_doc:acinetobacter_adp1_explorer:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:c3459b3f8a925fd2` -> `source_section:acinetobacter_adp1_explorer:REPORT.md:Key Findings`
- `provenance_edge` `has_evidence`: `stmt:adp1-explorer-multiomics-finding` -> `evidence:c3459b3f8a925fd2`
- `provenance_edge` `uses_notebook`: `evidence:c3459b3f8a925fd2` -> `notebook:acinetobacter_adp1_explorer:01_database_exploration.ipynb`
- `scientific_edge` `supports`: `stmt:adp1-explorer-multiomics-finding` -> `stmt:adp1-explorer-database-bridge-claim`

---
page_id: claim:adp1-explorer-database-bridge-claim
page_type: claim
member_hash: hash:36d3d99b69e8f5e9
---

# The ADP1 data explorer can serve as a BERDL bridge for downstream ADP1 synthesis pages.

- Page type: `claim`
- Member hash: `hash:36d3d99b69e8f5e9`
- Graph: [Graph](../graph.md)

## Introduction

This claim page evaluates the statement: The ADP1 data explorer can serve as a BERDL bridge for downstream ADP1 synthesis pages. [stmt:adp1-explorer-database-bridge-claim; acinetobacter_adp1_explorer]. It collects supporting findings, caveats, and downstream uses selected by the deterministic page plan.

## Synthesis

A central reusable claim frames this page. [stmt:adp1-explorer-database-bridge-claim](../claims/adp1-explorer-database-bridge-claim.md) states that The ADP1 data explorer can serve as a BERDL bridge for downstream ADP1 synthesis pages. [stmt:adp1-explorer-database-bridge-claim; acinetobacter_adp1_explorer].
The evidence base is anchored by several findings. `stmt:adp1-explorer-berdl-connectivity-finding` states that The ADP1 database connects strongly to BERDL through genomes, reactions, compounds, and pangenome clusters. [stmt:adp1-explorer-berdl-connectivity-finding; acinetobacter_adp1_explorer]. `stmt:adp1-explorer-multiomics-finding` states that The ADP1 database integrates six molecular and phenotype data modalities for Acinetobacter baylyi ADP1. [stmt:adp1-explorer-multiomics-finding; acinetobacter_adp1_explorer]. `stmt:adp1-explorer-pangenome-bridge-finding` states that A gene-junction bridge maps BERDL pangenome clusters to ADP1-style cluster IDs with complete gene-level coverage. [stmt:adp1-explorer-pangenome-bridge-finding; acinetobacter_adp1_explorer].
The synthesis should be read with several caveats. `stmt:adp1-explorer-gapfilling-caveat` states that ADP1 model-based growth predictions are quality-limited by heavy dependence on gapfilled reactions. [stmt:adp1-explorer-gapfilling-caveat; acinetobacter_adp1_explorer]. `stmt:adp1-triple-fba-growth-caveat` states that FBA class does not predict which TnSeq-dispensable ADP1 genes have measured growth defects. [stmt:adp1-triple-fba-growth-caveat; adp1_triple_essentiality].
The most direct follow-up work is a concrete opportunity. [stmt:adp1-explorer-discordance-opportunity](../opportunities/adp1-explorer-discordance-opportunity.md) states that FBA-TnSeq discordant genes in ADP1 should be prioritized for metabolic model refinement. [stmt:adp1-explorer-discordance-opportunity; acinetobacter_adp1_explorer].

## Navigation Context

This page links out to 11 related pages and has 12 backlinks. Use those links to move between the prose note, the underlying evidence, and the graph neighborhood.

## Structured Evidence Summary

### Caveats

- [stmt:adp1-explorer-discordance-opportunity](../opportunities/adp1-explorer-discordance-opportunity.md): FBA-TnSeq discordant genes in ADP1 should be prioritized for metabolic model refinement. `opportunity` `grounded` `medium` (acinetobacter_adp1_explorer/REPORT.md)
- `stmt:adp1-explorer-gapfilling-caveat`: ADP1 model-based growth predictions are quality-limited by heavy dependence on gapfilled reactions. `caveat` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)
- `stmt:adp1-triple-fba-growth-caveat`: FBA class does not predict which TnSeq-dispensable ADP1 genes have measured growth defects. `caveat` `grounded` `high` (adp1_triple_essentiality/REPORT.md)

### Claim

- [stmt:adp1-explorer-database-bridge-claim](../claims/adp1-explorer-database-bridge-claim.md): The ADP1 data explorer can serve as a BERDL bridge for downstream ADP1 synthesis pages. `claim` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)

### Downstream Uses

- [stmt:adp1-explorer-discordance-opportunity](../opportunities/adp1-explorer-discordance-opportunity.md): FBA-TnSeq discordant genes in ADP1 should be prioritized for metabolic model refinement. `opportunity` `grounded` `medium` (acinetobacter_adp1_explorer/REPORT.md)

### Refutations

No statements selected for this section.

### Supporting Evidence

- `stmt:adp1-explorer-berdl-connectivity-finding`: The ADP1 database connects strongly to BERDL through genomes, reactions, compounds, and pangenome clusters. `finding` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)
- `stmt:adp1-explorer-multiomics-finding`: The ADP1 database integrates six molecular and phenotype data modalities for Acinetobacter baylyi ADP1. `finding` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)
- `stmt:adp1-explorer-pangenome-bridge-finding`: A gene-junction bridge maps BERDL pangenome clusters to ADP1-style cluster IDs with complete gene-level coverage. `finding` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)

## Outgoing Links

- [Adp1 Triple Continuous Fitness Claim](../claims/adp1-triple-continuous-fitness-claim.md)
- [Adp1 Multiomics Database](../entities/adp1-multiomics-database.md)
- [Adp1](../entities/adp1.md)
- [Berdl](../entities/berdl.md)
- [Fba Model](../entities/fba-model.md)
- [Adp1 Explorer Discordance Opportunity](../opportunities/adp1-explorer-discordance-opportunity.md)
- [Adp1 Triple Aromatic Media Opportunity](../opportunities/adp1-triple-aromatic-media-opportunity.md)
- [Acinetobacter Adp1 Explorer](../projects/acinetobacter-adp1-explorer.md)
- [Adp1 Triple Essentiality](../projects/adp1-triple-essentiality.md)
- [Adp1 Data Integration](../topics/adp1-data-integration.md)
- [Adp1 Model Quality](../topics/adp1-model-quality.md)

## Backlinks

- [Adp1 Multiomics Database](../entities/adp1-multiomics-database.md)
- [Adp1](../entities/adp1.md)
- [Berdl](../entities/berdl.md)
- [Fba Model](../entities/fba-model.md)
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

### stmt:adp1-explorer-gapfilling-caveat

ADP1 model-based growth predictions are quality-limited by heavy dependence on gapfilled reactions.

- Kind/tier/confidence: `caveat` / `grounded` / `high`
- Scope: `project_local`
- Source: `acinetobacter_adp1_explorer/REPORT.md`
- Section: `Key Findings`
- Evidence: Of 121,519 growth phenotype predictions across 14 genomes, 105,376 (87%) require at least one gapfilled reaction.
- Figure: `figures/gapfilling_impact.png`
- Notebook: `05_metabolic_model_and_phenotypes.ipynb`
- Topics: [Adp1 Model Quality](../topics/adp1-model-quality.md)
- Entities: [Adp1](../entities/adp1.md), [Fba Model](../entities/fba-model.md)
- Motivates: [stmt:adp1-explorer-discordance-opportunity](../opportunities/adp1-explorer-discordance-opportunity.md)

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

### stmt:adp1-triple-fba-growth-caveat

FBA class does not predict which TnSeq-dispensable ADP1 genes have measured growth defects.

- Kind/tier/confidence: `caveat` / `grounded` / `high`
- Scope: `project_local`
- Source: `adp1_triple_essentiality/REPORT.md`
- Section: `Key Findings`
- Evidence: FBA's binary classification of genes as essential, variable, or blocked does not predict which TnSeq-dispensable genes have measurable growth defects.
- Figure: `figures/fba_growth_concordance.png`
- Topics: [Adp1 Model Quality](../topics/adp1-model-quality.md)
- Entities: [Adp1](../entities/adp1.md), [Fba Model](../entities/fba-model.md)
- Motivates: [stmt:adp1-triple-aromatic-media-opportunity](../opportunities/adp1-triple-aromatic-media-opportunity.md)
- Refines: [stmt:adp1-triple-continuous-fitness-claim](../claims/adp1-triple-continuous-fitness-claim.md)

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
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-gapfilling-caveat` -> `entity:adp1`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-gapfilling-caveat` -> `entity:collection:adp1_multiomics_database`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-gapfilling-caveat` -> `entity:fba_model`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-multiomics-finding` -> `entity:adp1`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-multiomics-finding` -> `entity:collection:adp1_multiomics_database`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-pangenome-bridge-finding` -> `entity:adp1`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-pangenome-bridge-finding` -> `entity:berdl`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-pangenome-bridge-finding` -> `entity:collection:adp1_multiomics_database`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-pangenome-bridge-finding` -> `entity:dataset:cluster_id_mapping`
- `navigation_edge` `about_entity`: `stmt:adp1-triple-fba-growth-caveat` -> `entity:adp1`
- `navigation_edge` `about_entity`: `stmt:adp1-triple-fba-growth-caveat` -> `entity:collection:adp1_triple_essentiality`
- `navigation_edge` `about_entity`: `stmt:adp1-triple-fba-growth-caveat` -> `entity:fba_model`
- `navigation_edge` `member_of_topic`: `stmt:adp1-explorer-berdl-connectivity-finding` -> `topic:adp1-data-integration`
- `navigation_edge` `member_of_topic`: `stmt:adp1-explorer-database-bridge-claim` -> `topic:adp1-data-integration`
- `navigation_edge` `member_of_topic`: `stmt:adp1-explorer-discordance-opportunity` -> `topic:adp1-model-quality`
- `navigation_edge` `member_of_topic`: `stmt:adp1-explorer-gapfilling-caveat` -> `topic:adp1-model-quality`
- `navigation_edge` `member_of_topic`: `stmt:adp1-explorer-multiomics-finding` -> `topic:adp1-data-integration`
- `navigation_edge` `member_of_topic`: `stmt:adp1-explorer-pangenome-bridge-finding` -> `topic:adp1-data-integration`
- `navigation_edge` `member_of_topic`: `stmt:adp1-triple-fba-growth-caveat` -> `topic:adp1-model-quality`
- `provenance_edge` `cites`: `evidence:4c893fc47311557c` -> `figure:acinetobacter_adp1_explorer:figures/gapfilling_impact.png`
- `provenance_edge` `cites`: `evidence:c3459b3f8a925fd2` -> `figure:acinetobacter_adp1_explorer:figures/data_coverage_by_modality.png`
- `provenance_edge` `cites`: `evidence:c42579f962551574` -> `figure:adp1_triple_essentiality:figures/fba_growth_concordance.png`
- `provenance_edge` `extracted_from`: `evidence:28856b6abc9a30ad` -> `project:acinetobacter_adp1_explorer`
- `provenance_edge` `extracted_from`: `evidence:28856b6abc9a30ad` -> `source_doc:acinetobacter_adp1_explorer:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:28856b6abc9a30ad` -> `source_section:acinetobacter_adp1_explorer:REPORT.md:Key Findings`
- `provenance_edge` `extracted_from`: `evidence:3b0ff3cf4b39cb89` -> `project:acinetobacter_adp1_explorer`
- `provenance_edge` `extracted_from`: `evidence:3b0ff3cf4b39cb89` -> `source_doc:acinetobacter_adp1_explorer:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:3b0ff3cf4b39cb89` -> `source_section:acinetobacter_adp1_explorer:REPORT.md:Research Questions Answered`
- `provenance_edge` `extracted_from`: `evidence:4c893fc47311557c` -> `project:acinetobacter_adp1_explorer`
- `provenance_edge` `extracted_from`: `evidence:4c893fc47311557c` -> `source_doc:acinetobacter_adp1_explorer:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:4c893fc47311557c` -> `source_section:acinetobacter_adp1_explorer:REPORT.md:Key Findings`
- `provenance_edge` `extracted_from`: `evidence:935d82e583994f8c` -> `project:acinetobacter_adp1_explorer`
- `provenance_edge` `extracted_from`: `evidence:935d82e583994f8c` -> `source_doc:acinetobacter_adp1_explorer:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:935d82e583994f8c` -> `source_section:acinetobacter_adp1_explorer:REPORT.md:Key Findings`
- `provenance_edge` `extracted_from`: `evidence:c3459b3f8a925fd2` -> `project:acinetobacter_adp1_explorer`
- `provenance_edge` `extracted_from`: `evidence:c3459b3f8a925fd2` -> `source_doc:acinetobacter_adp1_explorer:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:c3459b3f8a925fd2` -> `source_section:acinetobacter_adp1_explorer:REPORT.md:Key Findings`
- `provenance_edge` `extracted_from`: `evidence:c42579f962551574` -> `project:adp1_triple_essentiality`
- `provenance_edge` `extracted_from`: `evidence:c42579f962551574` -> `source_doc:adp1_triple_essentiality:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:c42579f962551574` -> `source_section:adp1_triple_essentiality:REPORT.md:Key Findings`
- `provenance_edge` `extracted_from`: `evidence:c9ca6ed0aa39959b` -> `project:acinetobacter_adp1_explorer`
- `provenance_edge` `extracted_from`: `evidence:c9ca6ed0aa39959b` -> `source_doc:acinetobacter_adp1_explorer:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:c9ca6ed0aa39959b` -> `source_section:acinetobacter_adp1_explorer:REPORT.md:Interpretation`
- `provenance_edge` `has_evidence`: `stmt:adp1-explorer-berdl-connectivity-finding` -> `evidence:28856b6abc9a30ad`
- `provenance_edge` `has_evidence`: `stmt:adp1-explorer-database-bridge-claim` -> `evidence:c9ca6ed0aa39959b`
- `provenance_edge` `has_evidence`: `stmt:adp1-explorer-discordance-opportunity` -> `evidence:3b0ff3cf4b39cb89`
- `provenance_edge` `has_evidence`: `stmt:adp1-explorer-gapfilling-caveat` -> `evidence:4c893fc47311557c`
- `provenance_edge` `has_evidence`: `stmt:adp1-explorer-multiomics-finding` -> `evidence:c3459b3f8a925fd2`
- `provenance_edge` `has_evidence`: `stmt:adp1-explorer-pangenome-bridge-finding` -> `evidence:935d82e583994f8c`
- `provenance_edge` `has_evidence`: `stmt:adp1-triple-fba-growth-caveat` -> `evidence:c42579f962551574`
- `provenance_edge` `uses_notebook`: `evidence:28856b6abc9a30ad` -> `notebook:acinetobacter_adp1_explorer:02_berdl_connection_scan.ipynb`
- `provenance_edge` `uses_notebook`: `evidence:4c893fc47311557c` -> `notebook:acinetobacter_adp1_explorer:05_metabolic_model_and_phenotypes.ipynb`
- `provenance_edge` `uses_notebook`: `evidence:935d82e583994f8c` -> `notebook:acinetobacter_adp1_explorer:03_cluster_id_mapping.ipynb`
- `provenance_edge` `uses_notebook`: `evidence:c3459b3f8a925fd2` -> `notebook:acinetobacter_adp1_explorer:01_database_exploration.ipynb`
- `review_edge` `needs_review`: `stmt:adp1-explorer-discordance-opportunity` -> `stmt:adp1-explorer-database-bridge-claim`
- `scientific_edge` `motivates`: `stmt:adp1-explorer-database-bridge-claim` -> `stmt:adp1-explorer-discordance-opportunity`
- `scientific_edge` `motivates`: `stmt:adp1-explorer-gapfilling-caveat` -> `stmt:adp1-explorer-discordance-opportunity`
- `scientific_edge` `motivates`: `stmt:adp1-triple-fba-growth-caveat` -> `stmt:adp1-triple-aromatic-media-opportunity`
- `scientific_edge` `refines`: `stmt:adp1-triple-fba-growth-caveat` -> `stmt:adp1-triple-continuous-fitness-claim`
- `scientific_edge` `supports`: `stmt:adp1-explorer-berdl-connectivity-finding` -> `stmt:adp1-explorer-database-bridge-claim`
- `scientific_edge` `supports`: `stmt:adp1-explorer-multiomics-finding` -> `stmt:adp1-explorer-database-bridge-claim`
- `scientific_edge` `supports`: `stmt:adp1-explorer-pangenome-bridge-finding` -> `stmt:adp1-explorer-database-bridge-claim`

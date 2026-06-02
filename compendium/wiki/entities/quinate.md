---
page_id: entity:quinate
page_type: entity
member_hash: hash:810fc059ecbda754
---

# Entity: Quinate

- Page type: `entity`
- Member hash: `hash:810fc059ecbda754`
- Graph: [Graph](../graph.md)

## Introduction

This entity page is a backlink hub for Entity: Quinate. It gathers 2 statements from `acinetobacter_adp1_explorer` and `adp1_deletion_phenotypes` and shows how the entity participates in findings, claims, caveats, and opportunities across the wiki.

## Synthesis

The evidence base is anchored by several findings. `stmt:adp1-deletion-quinate-module-finding` states that Quinate degradation is the main discrete exception to the otherwise continuous ADP1 carbon-fitness landscape. [stmt:adp1-deletion-quinate-module-finding; adp1_deletion_phenotypes]. `stmt:adp1-explorer-condition-fitness-finding` states that ADP1 mutant growth fitness shows condition-specific structure, with urea and quinate behaving as outlier conditions. [stmt:adp1-explorer-condition-fitness-finding; acinetobacter_adp1_explorer].

## Navigation Context

This page links out to 8 related pages and has 9 backlinks. Use those links to move between the prose note, the underlying evidence, and the graph neighborhood.

## Structured Evidence Summary

### Backlinks

- `stmt:adp1-deletion-quinate-module-finding`: Quinate degradation is the main discrete exception to the otherwise continuous ADP1 carbon-fitness landscape. `finding` `grounded` `high` (adp1_deletion_phenotypes/REPORT.md)
- `stmt:adp1-explorer-condition-fitness-finding`: ADP1 mutant growth fitness shows condition-specific structure, with urea and quinate behaving as outlier conditions. `finding` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)

### Claims

No statements selected for this section.

### Conflicts And Caveats

No statements selected for this section.

### Findings

- `stmt:adp1-deletion-quinate-module-finding`: Quinate degradation is the main discrete exception to the otherwise continuous ADP1 carbon-fitness landscape. `finding` `grounded` `high` (adp1_deletion_phenotypes/REPORT.md)
- `stmt:adp1-explorer-condition-fitness-finding`: ADP1 mutant growth fitness shows condition-specific structure, with urea and quinate behaving as outlier conditions. `finding` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)

### Opportunities And Directions

No statements selected for this section.

### Topic: Adp1 Carbon Fitness

- `stmt:adp1-deletion-quinate-module-finding`: Quinate degradation is the main discrete exception to the otherwise continuous ADP1 carbon-fitness landscape. `finding` `grounded` `high` (adp1_deletion_phenotypes/REPORT.md)
- `stmt:adp1-explorer-condition-fitness-finding`: ADP1 mutant growth fitness shows condition-specific structure, with urea and quinate behaving as outlier conditions. `finding` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)

## Outgoing Links

- [Adp1 Deletion Continuum Claim](../claims/adp1-deletion-continuum-claim.md)
- [Adp1](../entities/adp1.md)
- [Urea](../entities/urea.md)
- [Adp1 Deletion Expand Carbon Panel Opportunity](../opportunities/adp1-deletion-expand-carbon-panel-opportunity.md)
- [Adp1 Explorer Urea Deep Dive Opportunity](../opportunities/adp1-explorer-urea-deep-dive-opportunity.md)
- [Acinetobacter Adp1 Explorer](../projects/acinetobacter-adp1-explorer.md)
- [Adp1 Deletion Phenotypes](../projects/adp1-deletion-phenotypes.md)
- [Adp1 Carbon Fitness](../topics/adp1-carbon-fitness.md)

## Backlinks

- [Adp1 Deletion Continuum Claim](../claims/adp1-deletion-continuum-claim.md)
- [Adp1](../entities/adp1.md)
- [Urea](../entities/urea.md)
- [Home](../index.md)
- [Adp1 Deletion Expand Carbon Panel Opportunity](../opportunities/adp1-deletion-expand-carbon-panel-opportunity.md)
- [Adp1 Explorer Urea Deep Dive Opportunity](../opportunities/adp1-explorer-urea-deep-dive-opportunity.md)
- [Acinetobacter Adp1 Explorer](../projects/acinetobacter-adp1-explorer.md)
- [Adp1 Deletion Phenotypes](../projects/adp1-deletion-phenotypes.md)
- [Adp1 Carbon Fitness](../topics/adp1-carbon-fitness.md)

## Source Statements

### stmt:adp1-deletion-quinate-module-finding

Quinate degradation is the main discrete exception to the otherwise continuous ADP1 carbon-fitness landscape.

- Kind/tier/confidence: `finding` / `grounded` / `high`
- Scope: `project_local`
- Source: `adp1_deletion_phenotypes/REPORT.md`
- Section: `Key Findings`
- Evidence: The one exception is a small module of 24 genes with extreme quinate-specific defects (mean z-score = -7.28 on quinate, near-zero on other conditions).
- Figure: `figures/module_profiles.png`
- Notebook: `03_gene_modules.ipynb`
- Topics: [Adp1 Carbon Fitness](../topics/adp1-carbon-fitness.md)
- Entities: [Adp1](../entities/adp1.md), [Quinate](../entities/quinate.md)
- Supports: [stmt:adp1-deletion-continuum-claim](../claims/adp1-deletion-continuum-claim.md)
- Motivates: [stmt:adp1-deletion-expand-carbon-panel-opportunity](../opportunities/adp1-deletion-expand-carbon-panel-opportunity.md)

### stmt:adp1-explorer-condition-fitness-finding

ADP1 mutant growth fitness shows condition-specific structure, with urea and quinate behaving as outlier conditions.

- Kind/tier/confidence: `finding` / `grounded` / `high`
- Scope: `project_local`
- Source: `acinetobacter_adp1_explorer/REPORT.md`
- Section: `Key Findings`
- Evidence: Urea fitness is nearly uncorrelated with quinate (r = 0.11) and weakly correlated with all other conditions (r = 0.12-0.28), suggesting that urea catabolism involves a largely independent set of genes.
- Figure: `figures/growth_condition_correlation.png`
- Notebook: `04_gene_essentiality_and_fitness.ipynb`
- Topics: [Adp1 Carbon Fitness](../topics/adp1-carbon-fitness.md)
- Entities: [Adp1](../entities/adp1.md), [Quinate](../entities/quinate.md), [Urea](../entities/urea.md)
- Motivates: [stmt:adp1-explorer-urea-deep-dive-opportunity](../opportunities/adp1-explorer-urea-deep-dive-opportunity.md)

## Local Graph

- `navigation_edge` `about_entity`: `stmt:adp1-deletion-quinate-module-finding` -> `entity:adp1`
- `navigation_edge` `about_entity`: `stmt:adp1-deletion-quinate-module-finding` -> `entity:collection:adp1_deletion_phenotypes`
- `navigation_edge` `about_entity`: `stmt:adp1-deletion-quinate-module-finding` -> `entity:quinate`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-condition-fitness-finding` -> `entity:adp1`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-condition-fitness-finding` -> `entity:collection:adp1_multiomics_database`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-condition-fitness-finding` -> `entity:eight-carbon-sources`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-condition-fitness-finding` -> `entity:quinate`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-condition-fitness-finding` -> `entity:urea`
- `navigation_edge` `member_of_topic`: `stmt:adp1-deletion-quinate-module-finding` -> `topic:adp1-carbon-fitness`
- `navigation_edge` `member_of_topic`: `stmt:adp1-explorer-condition-fitness-finding` -> `topic:adp1-carbon-fitness`
- `provenance_edge` `cites`: `evidence:42cbced2d6495de4` -> `figure:acinetobacter_adp1_explorer:figures/growth_condition_correlation.png`
- `provenance_edge` `cites`: `evidence:cadf3bedb4bb73e8` -> `figure:adp1_deletion_phenotypes:figures/module_profiles.png`
- `provenance_edge` `extracted_from`: `evidence:42cbced2d6495de4` -> `project:acinetobacter_adp1_explorer`
- `provenance_edge` `extracted_from`: `evidence:42cbced2d6495de4` -> `source_doc:acinetobacter_adp1_explorer:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:42cbced2d6495de4` -> `source_section:acinetobacter_adp1_explorer:REPORT.md:Key Findings`
- `provenance_edge` `extracted_from`: `evidence:cadf3bedb4bb73e8` -> `project:adp1_deletion_phenotypes`
- `provenance_edge` `extracted_from`: `evidence:cadf3bedb4bb73e8` -> `source_doc:adp1_deletion_phenotypes:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:cadf3bedb4bb73e8` -> `source_section:adp1_deletion_phenotypes:REPORT.md:Key Findings`
- `provenance_edge` `has_evidence`: `stmt:adp1-deletion-quinate-module-finding` -> `evidence:cadf3bedb4bb73e8`
- `provenance_edge` `has_evidence`: `stmt:adp1-explorer-condition-fitness-finding` -> `evidence:42cbced2d6495de4`
- `provenance_edge` `uses_notebook`: `evidence:42cbced2d6495de4` -> `notebook:acinetobacter_adp1_explorer:04_gene_essentiality_and_fitness.ipynb`
- `provenance_edge` `uses_notebook`: `evidence:cadf3bedb4bb73e8` -> `notebook:adp1_deletion_phenotypes:03_gene_modules.ipynb`
- `review_edge` `needs_review`: `stmt:adp1-explorer-urea-deep-dive-opportunity` -> `stmt:adp1-explorer-condition-fitness-finding`
- `scientific_edge` `motivates`: `stmt:adp1-deletion-quinate-module-finding` -> `stmt:adp1-deletion-expand-carbon-panel-opportunity`
- `scientific_edge` `motivates`: `stmt:adp1-explorer-condition-fitness-finding` -> `stmt:adp1-explorer-urea-deep-dive-opportunity`
- `scientific_edge` `supports`: `stmt:adp1-deletion-quinate-module-finding` -> `stmt:adp1-deletion-continuum-claim`

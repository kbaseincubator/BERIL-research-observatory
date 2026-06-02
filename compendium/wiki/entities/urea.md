---
page_id: entity:urea
page_type: entity
member_hash: hash:6a967c2ad7d3bc8d
---

# Entity: Urea

- Page type: `entity`
- Member hash: `hash:6a967c2ad7d3bc8d`
- Graph: [Graph](../graph.md)

## Introduction

This entity page is a backlink hub for Entity: Urea. It gathers 2 statements from `acinetobacter_adp1_explorer` and shows how the entity participates in findings, claims, caveats, and opportunities across the wiki.

## Synthesis

The evidence base is anchored by one finding. `stmt:adp1-explorer-condition-fitness-finding` states that ADP1 mutant growth fitness shows condition-specific structure, with urea and quinate behaving as outlier conditions. [stmt:adp1-explorer-condition-fitness-finding; acinetobacter_adp1_explorer].
The most direct follow-up work is a concrete opportunity. [stmt:adp1-explorer-urea-deep-dive-opportunity](../opportunities/adp1-explorer-urea-deep-dive-opportunity.md) states that ADP1 urea-specific fitness genes and their pangenome conservation should be analyzed as an independent metabolism module. [stmt:adp1-explorer-urea-deep-dive-opportunity; acinetobacter_adp1_explorer].

## Navigation Context

This page links out to 5 related pages and has 6 backlinks. Use those links to move between the prose note, the underlying evidence, and the graph neighborhood.

## Structured Evidence Summary

### Backlinks

- `stmt:adp1-explorer-condition-fitness-finding`: ADP1 mutant growth fitness shows condition-specific structure, with urea and quinate behaving as outlier conditions. `finding` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)
- [stmt:adp1-explorer-urea-deep-dive-opportunity](../opportunities/adp1-explorer-urea-deep-dive-opportunity.md): ADP1 urea-specific fitness genes and their pangenome conservation should be analyzed as an independent metabolism module. `opportunity` `grounded` `medium` (acinetobacter_adp1_explorer/REPORT.md)

### Claims

No statements selected for this section.

### Conflicts And Caveats

No statements selected for this section.

### Findings

- `stmt:adp1-explorer-condition-fitness-finding`: ADP1 mutant growth fitness shows condition-specific structure, with urea and quinate behaving as outlier conditions. `finding` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)

### Opportunities And Directions

- [stmt:adp1-explorer-urea-deep-dive-opportunity](../opportunities/adp1-explorer-urea-deep-dive-opportunity.md): ADP1 urea-specific fitness genes and their pangenome conservation should be analyzed as an independent metabolism module. `opportunity` `grounded` `medium` (acinetobacter_adp1_explorer/REPORT.md)

### Topic: Adp1 Carbon Fitness

- `stmt:adp1-explorer-condition-fitness-finding`: ADP1 mutant growth fitness shows condition-specific structure, with urea and quinate behaving as outlier conditions. `finding` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)
- [stmt:adp1-explorer-urea-deep-dive-opportunity](../opportunities/adp1-explorer-urea-deep-dive-opportunity.md): ADP1 urea-specific fitness genes and their pangenome conservation should be analyzed as an independent metabolism module. `opportunity` `grounded` `medium` (acinetobacter_adp1_explorer/REPORT.md)

## Outgoing Links

- [Adp1](../entities/adp1.md)
- [Quinate](../entities/quinate.md)
- [Adp1 Explorer Urea Deep Dive Opportunity](../opportunities/adp1-explorer-urea-deep-dive-opportunity.md)
- [Acinetobacter Adp1 Explorer](../projects/acinetobacter-adp1-explorer.md)
- [Adp1 Carbon Fitness](../topics/adp1-carbon-fitness.md)

## Backlinks

- [Adp1](../entities/adp1.md)
- [Quinate](../entities/quinate.md)
- [Home](../index.md)
- [Adp1 Explorer Urea Deep Dive Opportunity](../opportunities/adp1-explorer-urea-deep-dive-opportunity.md)
- [Acinetobacter Adp1 Explorer](../projects/acinetobacter-adp1-explorer.md)
- [Adp1 Carbon Fitness](../topics/adp1-carbon-fitness.md)

## Source Statements

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

### stmt:adp1-explorer-urea-deep-dive-opportunity

ADP1 urea-specific fitness genes and their pangenome conservation should be analyzed as an independent metabolism module.

- Kind/tier/confidence: `opportunity` / `grounded` / `medium`
- Scope: `project_local`
- Source: `acinetobacter_adp1_explorer/REPORT.md`
- Section: `Research Questions Answered`
- Evidence: The near-zero correlation between urea fitness and other carbon sources (r = 0.11-0.28) suggests a largely independent gene set.
- Topics: [Adp1 Carbon Fitness](../topics/adp1-carbon-fitness.md)
- Entities: [Adp1](../entities/adp1.md), [Urea](../entities/urea.md)
- Requires Validation: `stmt:adp1-explorer-condition-fitness-finding`

## Local Graph

- `navigation_edge` `about_entity`: `stmt:adp1-explorer-condition-fitness-finding` -> `entity:adp1`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-condition-fitness-finding` -> `entity:collection:adp1_multiomics_database`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-condition-fitness-finding` -> `entity:eight-carbon-sources`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-condition-fitness-finding` -> `entity:quinate`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-condition-fitness-finding` -> `entity:urea`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-urea-deep-dive-opportunity` -> `entity:adp1`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-urea-deep-dive-opportunity` -> `entity:dataset:adp1-urea-specific-gene-conservation`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-urea-deep-dive-opportunity` -> `entity:urea`
- `navigation_edge` `member_of_topic`: `stmt:adp1-explorer-condition-fitness-finding` -> `topic:adp1-carbon-fitness`
- `navigation_edge` `member_of_topic`: `stmt:adp1-explorer-urea-deep-dive-opportunity` -> `topic:adp1-carbon-fitness`
- `provenance_edge` `cites`: `evidence:42cbced2d6495de4` -> `figure:acinetobacter_adp1_explorer:figures/growth_condition_correlation.png`
- `provenance_edge` `extracted_from`: `evidence:42cbced2d6495de4` -> `project:acinetobacter_adp1_explorer`
- `provenance_edge` `extracted_from`: `evidence:42cbced2d6495de4` -> `source_doc:acinetobacter_adp1_explorer:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:42cbced2d6495de4` -> `source_section:acinetobacter_adp1_explorer:REPORT.md:Key Findings`
- `provenance_edge` `extracted_from`: `evidence:6f38bdb5d36bbfa7` -> `project:acinetobacter_adp1_explorer`
- `provenance_edge` `extracted_from`: `evidence:6f38bdb5d36bbfa7` -> `source_doc:acinetobacter_adp1_explorer:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:6f38bdb5d36bbfa7` -> `source_section:acinetobacter_adp1_explorer:REPORT.md:Research Questions Answered`
- `provenance_edge` `has_evidence`: `stmt:adp1-explorer-condition-fitness-finding` -> `evidence:42cbced2d6495de4`
- `provenance_edge` `has_evidence`: `stmt:adp1-explorer-urea-deep-dive-opportunity` -> `evidence:6f38bdb5d36bbfa7`
- `provenance_edge` `uses_notebook`: `evidence:42cbced2d6495de4` -> `notebook:acinetobacter_adp1_explorer:04_gene_essentiality_and_fitness.ipynb`
- `review_edge` `needs_review`: `stmt:adp1-explorer-urea-deep-dive-opportunity` -> `stmt:adp1-explorer-condition-fitness-finding`
- `scientific_edge` `motivates`: `stmt:adp1-explorer-condition-fitness-finding` -> `stmt:adp1-explorer-urea-deep-dive-opportunity`

# Condition-Specific Respiratory Chain Wiring in ADP1

## Research Question
How is *Acinetobacter baylyi* ADP1's branched respiratory chain wired across carbon sources — which NADH dehydrogenases and terminal oxidases are required for which substrates?

## Status
In Progress — research plan created, awaiting analysis.

## Overview
ADP1 has a branched respiratory chain with multiple NADH dehydrogenases (Complex I, NDH-2, ACIAD3522) and terminal oxidases (cytochrome bo, cytochrome bd). The prior project (`aromatic_catabolism_network`) showed that Complex I is specifically essential for aromatic catabolism but dispensable on glucose, while ACIAD3522 is acetate-lethal but quinate-fine. This project systematically maps the condition-dependent wiring of the entire respiratory chain using the 8-condition growth matrix, FBA stoichiometry, and cross-species Fitness Browser data. The central hypothesis: Complex I's quinate-specificity reflects the high NADH flux from aromatic catabolism exceeding NDH-2's reoxidation capacity.

## Data Sources
- **User-provided**: `user_data/berdl_tables.db` — SQLite database with ADP1 genome features, FBA predictions (230 conditions), gene-reaction mappings
- **Prior projects**: `projects/aromatic_catabolism_network/` (Complex I support network), `projects/adp1_deletion_phenotypes/` (condition-specific growth data)
- **BERDL**: `kescience_fitnessbrowser` for cross-species respiratory chain fitness data; `kbase_ke_pangenome` for NDH-2/Complex I co-occurrence

## Quick Links
- [Research Plan](RESEARCH_PLAN.md) — hypothesis, approach, query strategy
- [Report](REPORT.md) — findings, interpretation, supporting evidence

## Reproduction
*TBD — add prerequisites and step-by-step instructions after analysis is complete.*

## Authors
- Paramvir Dehal (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)), Lawrence Berkeley National Laboratory

# ADP1 Deletion Collection Phenotype Analysis

## Research Question
What is the condition-dependent structure of gene essentiality in *Acinetobacter baylyi* ADP1, as revealed by the de Berardinis single-gene deletion collection grown on 8 carbon sources?

## Status
In Progress — research plan created, awaiting analysis.

## Overview
The de Berardinis et al. (2008) complete deletion collection for ADP1 provides growth ratio measurements for ~2,350 single-gene deletion mutants across 8 carbon sources (acetate, asparagine, butanediol, glucarate, glucose, lactate, quinate, urea). This project performs a phenotype-first analysis of the 2,034×8 complete growth matrix to discover: (1) which carbon sources produce redundant vs independent essentiality profiles, (2) functionally coherent gene modules with correlated growth defects, (3) genes with condition-specific importance, and (4) patterns in TnSeq-classified genes that lack deletion mutant data. No FBA — the prior project (adp1_triple_essentiality) showed FBA class adds no predictive value for growth defects among dispensable genes (p=0.63).

## Data Sources
- **User-provided**: `user_data/berdl_tables.db` — SQLite database (136 MB) with ADP1 genome features, growth data, TnSeq essentiality, and annotations (symlinked from `projects/acinetobacter_adp1_explorer/user_data/`)
- **Prior project**: `projects/adp1_triple_essentiality/` — FBA-TnSeq-growth concordance analysis

## Quick Links
- [Research Plan](RESEARCH_PLAN.md) — hypothesis, approach, query strategy
- [Report](REPORT.md) — findings, interpretation, supporting evidence

## Reproduction
*TBD — add prerequisites and step-by-step instructions after analysis is complete.*

## Authors
- Paramvir Dehal (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)), Lawrence Berkeley National Laboratory

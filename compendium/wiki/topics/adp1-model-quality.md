---
page_id: topic:adp1-model-quality
page_type: topic
member_hash: hash:58c83104bd799e05
---

# Topic: Adp1 Model Quality

- Page type: `topic`
- Member hash: `hash:58c83104bd799e05`
- Graph: [Graph](../graph.md)

## Outgoing Links

- [Adp1 Explorer Database Bridge Claim](../claims/adp1-explorer-database-bridge-claim.md)
- [Adp1 Triple Continuous Fitness Claim](../claims/adp1-triple-continuous-fitness-claim.md)
- [Adp1](../entities/adp1.md)
- [Aromatic Degradation](../entities/aromatic-degradation.md)
- [Berdl](../entities/berdl.md)
- [Fba Model](../entities/fba-model.md)
- [Adp1 Explorer Discordance Opportunity](../opportunities/adp1-explorer-discordance-opportunity.md)
- [Adp1 Triple Aromatic Media Opportunity](../opportunities/adp1-triple-aromatic-media-opportunity.md)
- [Acinetobacter Adp1 Explorer](../projects/acinetobacter-adp1-explorer.md)
- [Adp1 Triple Essentiality](../projects/adp1-triple-essentiality.md)
- [Adp1 Carbon Fitness](../topics/adp1-carbon-fitness.md)
- [Adp1 Data Integration](../topics/adp1-data-integration.md)

## Backlinks

- [Adp1 Deletion Continuum Claim](../claims/adp1-deletion-continuum-claim.md)
- [Adp1 Explorer Database Bridge Claim](../claims/adp1-explorer-database-bridge-claim.md)
- [Adp1 Triple Continuous Fitness Claim](../claims/adp1-triple-continuous-fitness-claim.md)
- [Adp1](../entities/adp1.md)
- [Aromatic Degradation](../entities/aromatic-degradation.md)
- [Fba Model](../entities/fba-model.md)
- [Home](../index.md)
- [Adp1 Deletion Expand Carbon Panel Opportunity](../opportunities/adp1-deletion-expand-carbon-panel-opportunity.md)
- [Adp1 Explorer Discordance Opportunity](../opportunities/adp1-explorer-discordance-opportunity.md)
- [Adp1 Explorer Urea Deep Dive Opportunity](../opportunities/adp1-explorer-urea-deep-dive-opportunity.md)
- [Adp1 Triple Aromatic Media Opportunity](../opportunities/adp1-triple-aromatic-media-opportunity.md)
- [Acinetobacter Adp1 Explorer](../projects/acinetobacter-adp1-explorer.md)
- [Adp1 Triple Essentiality](../projects/adp1-triple-essentiality.md)
- [Adp1 Carbon Fitness](../topics/adp1-carbon-fitness.md)
- [Adp1 Data Integration](../topics/adp1-data-integration.md)

## Conflicts And Caveats

- `stmt:adp1-explorer-gapfilling-caveat`: ADP1 model-based growth predictions are quality-limited by heavy dependence on gapfilled reactions. `caveat` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)
- `stmt:adp1-triple-fba-growth-caveat`: FBA class does not predict which TnSeq-dispensable ADP1 genes have measured growth defects. `caveat` `grounded` `high` (adp1_triple_essentiality/REPORT.md)

## Findings

- `stmt:adp1-triple-aromatic-discordance-finding`: Aromatic degradation genes are enriched among ADP1 FBA-discordant genes, indicating systematic model gaps. `finding` `grounded` `high` (adp1_triple_essentiality/REPORT.md)
- `stmt:adp1-triple-fitness-predictor-finding`: Continuous fitness values outperform binary essentiality fractions for predicting ADP1 essentiality. `finding` `grounded` `high` (adp1_triple_essentiality/REPORT.md)
- `stmt:adp1-triple-proteomics-finding`: Proteomics is a strong ADP1 essentiality signal and performs comparably to continuous fitness in ROC analysis. `finding` `grounded` `high` (adp1_triple_essentiality/REPORT.md)

## Key Claims

- [stmt:adp1-explorer-database-bridge-claim](../claims/adp1-explorer-database-bridge-claim.md): The ADP1 data explorer can serve as a BERDL bridge for downstream ADP1 synthesis pages. `claim` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)
- [stmt:adp1-triple-continuous-fitness-claim](../claims/adp1-triple-continuous-fitness-claim.md): ADP1 essentiality synthesis should prioritize continuous fitness and orthogonal evidence over binary essentiality thresholds alone. `claim` `grounded` `high` (adp1_triple_essentiality/REPORT.md)

## Opportunities And Directions

- [stmt:adp1-explorer-discordance-opportunity](../opportunities/adp1-explorer-discordance-opportunity.md): FBA-TnSeq discordant genes in ADP1 should be prioritized for metabolic model refinement. `opportunity` `grounded` `medium` (acinetobacter_adp1_explorer/REPORT.md)
- [stmt:adp1-triple-aromatic-media-opportunity](../opportunities/adp1-triple-aromatic-media-opportunity.md): ADP1 FBA media definitions should be refined with trace aromatic compounds and retested against aromatic-degradation discordance. `opportunity` `grounded` `medium` (adp1_triple_essentiality/REPORT.md)

## Overview

- [stmt:adp1-explorer-database-bridge-claim](../claims/adp1-explorer-database-bridge-claim.md): The ADP1 data explorer can serve as a BERDL bridge for downstream ADP1 synthesis pages. `claim` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)
- [stmt:adp1-explorer-discordance-opportunity](../opportunities/adp1-explorer-discordance-opportunity.md): FBA-TnSeq discordant genes in ADP1 should be prioritized for metabolic model refinement. `opportunity` `grounded` `medium` (acinetobacter_adp1_explorer/REPORT.md)
- `stmt:adp1-explorer-gapfilling-caveat`: ADP1 model-based growth predictions are quality-limited by heavy dependence on gapfilled reactions. `caveat` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)
- `stmt:adp1-triple-aromatic-discordance-finding`: Aromatic degradation genes are enriched among ADP1 FBA-discordant genes, indicating systematic model gaps. `finding` `grounded` `high` (adp1_triple_essentiality/REPORT.md)
- [stmt:adp1-triple-aromatic-media-opportunity](../opportunities/adp1-triple-aromatic-media-opportunity.md): ADP1 FBA media definitions should be refined with trace aromatic compounds and retested against aromatic-degradation discordance. `opportunity` `grounded` `medium` (adp1_triple_essentiality/REPORT.md)
- [stmt:adp1-triple-continuous-fitness-claim](../claims/adp1-triple-continuous-fitness-claim.md): ADP1 essentiality synthesis should prioritize continuous fitness and orthogonal evidence over binary essentiality thresholds alone. `claim` `grounded` `high` (adp1_triple_essentiality/REPORT.md)
- `stmt:adp1-triple-fba-growth-caveat`: FBA class does not predict which TnSeq-dispensable ADP1 genes have measured growth defects. `caveat` `grounded` `high` (adp1_triple_essentiality/REPORT.md)
- `stmt:adp1-triple-fitness-predictor-finding`: Continuous fitness values outperform binary essentiality fractions for predicting ADP1 essentiality. `finding` `grounded` `high` (adp1_triple_essentiality/REPORT.md)
- `stmt:adp1-triple-proteomics-finding`: Proteomics is a strong ADP1 essentiality signal and performs comparably to continuous fitness in ROC analysis. `finding` `grounded` `high` (adp1_triple_essentiality/REPORT.md)

## Reusable Products And Methods

No statements selected for this section.

## Source Statements

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

### stmt:adp1-triple-aromatic-discordance-finding

Aromatic degradation genes are enriched among ADP1 FBA-discordant genes, indicating systematic model gaps.

- Kind/tier/confidence: `finding` / `grounded` / `high`
- Scope: `project_local`
- Source: `adp1_triple_essentiality/REPORT.md`
- Section: `Key Findings`
- Evidence: **Aromatic degradation genes** are enriched among FBA-discordant genes (OR=9.7), revealing systematic model gaps
- Figure: `figures/rast_enrichment_discordant.png`
- Topics: [Adp1 Model Quality](../topics/adp1-model-quality.md)
- Entities: [Adp1](../entities/adp1.md), [Aromatic Degradation](../entities/aromatic-degradation.md), [Fba Model](../entities/fba-model.md)
- Supports: [stmt:adp1-triple-continuous-fitness-claim](../claims/adp1-triple-continuous-fitness-claim.md)
- Motivates: [stmt:adp1-triple-aromatic-media-opportunity](../opportunities/adp1-triple-aromatic-media-opportunity.md)

### stmt:adp1-triple-aromatic-media-opportunity

ADP1 FBA media definitions should be refined with trace aromatic compounds and retested against aromatic-degradation discordance.

- Kind/tier/confidence: `opportunity` / `grounded` / `medium`
- Scope: `project_local`
- Source: `adp1_triple_essentiality/REPORT.md`
- Section: `Recommendations`
- Evidence: Model refinement should add trace aromatic compounds to media definition
- Topics: [Adp1 Carbon Fitness](../topics/adp1-carbon-fitness.md), [Adp1 Model Quality](../topics/adp1-model-quality.md)
- Entities: [Adp1](../entities/adp1.md), [Aromatic Degradation](../entities/aromatic-degradation.md), [Fba Model](../entities/fba-model.md)
- Requires Validation: [stmt:adp1-triple-continuous-fitness-claim](../claims/adp1-triple-continuous-fitness-claim.md)

### stmt:adp1-triple-continuous-fitness-claim

ADP1 essentiality synthesis should prioritize continuous fitness and orthogonal evidence over binary essentiality thresholds alone.

- Kind/tier/confidence: `claim` / `grounded` / `high`
- Scope: `project_local`
- Source: `adp1_triple_essentiality/REPORT.md`
- Section: `Recommendations`
- Evidence: **Use continuous fitness values** from TnSeq rather than binary essentiality_fraction
- Topics: [Adp1 Carbon Fitness](../topics/adp1-carbon-fitness.md), [Adp1 Model Quality](../topics/adp1-model-quality.md)
- Entities: [Adp1](../entities/adp1.md)
- Motivates: [stmt:adp1-triple-aromatic-media-opportunity](../opportunities/adp1-triple-aromatic-media-opportunity.md)

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

### stmt:adp1-triple-fitness-predictor-finding

Continuous fitness values outperform binary essentiality fractions for predicting ADP1 essentiality.

- Kind/tier/confidence: `finding` / `grounded` / `high`
- Scope: `project_local`
- Source: `adp1_triple_essentiality/REPORT.md`
- Section: `Integrated Discussion`
- Evidence: Continuous fitness values (AUC=0.70-0.73) outperform binary essentiality_fraction (AUC=0.34-0.40).
- Figure: `figures/roc_comprehensive.png`
- Notebook: `04_roc_analysis.ipynb`
- Topics: [Adp1 Carbon Fitness](../topics/adp1-carbon-fitness.md), [Adp1 Model Quality](../topics/adp1-model-quality.md)
- Entities: [Adp1](../entities/adp1.md)
- Supports: [stmt:adp1-triple-continuous-fitness-claim](../claims/adp1-triple-continuous-fitness-claim.md)

### stmt:adp1-triple-proteomics-finding

Proteomics is a strong ADP1 essentiality signal and performs comparably to continuous fitness in ROC analysis.

- Kind/tier/confidence: `finding` / `grounded` / `high`
- Scope: `project_local`
- Source: `adp1_triple_essentiality/REPORT.md`
- Section: `Integrated Conclusions`
- Evidence: Proteomics validates essentiality (AUC=0.74)
- Topics: [Adp1 Model Quality](../topics/adp1-model-quality.md)
- Entities: [Adp1](../entities/adp1.md)
- Supports: [stmt:adp1-triple-continuous-fitness-claim](../claims/adp1-triple-continuous-fitness-claim.md)

## Local Graph

- `navigation_edge` `about_entity`: `stmt:adp1-explorer-database-bridge-claim` -> `entity:adp1`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-database-bridge-claim` -> `entity:berdl`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-database-bridge-claim` -> `entity:collection:adp1_multiomics_database`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-discordance-opportunity` -> `entity:adp1`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-discordance-opportunity` -> `entity:dataset:adp1-fba-tnseq-discordance-prioritization`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-discordance-opportunity` -> `entity:fba_model`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-gapfilling-caveat` -> `entity:adp1`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-gapfilling-caveat` -> `entity:collection:adp1_multiomics_database`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-gapfilling-caveat` -> `entity:fba_model`
- `navigation_edge` `about_entity`: `stmt:adp1-triple-aromatic-discordance-finding` -> `entity:adp1`
- `navigation_edge` `about_entity`: `stmt:adp1-triple-aromatic-discordance-finding` -> `entity:aromatic_degradation`
- `navigation_edge` `about_entity`: `stmt:adp1-triple-aromatic-discordance-finding` -> `entity:collection:adp1_triple_essentiality`
- `navigation_edge` `about_entity`: `stmt:adp1-triple-aromatic-discordance-finding` -> `entity:fba_model`
- `navigation_edge` `about_entity`: `stmt:adp1-triple-aromatic-media-opportunity` -> `entity:adp1`
- `navigation_edge` `about_entity`: `stmt:adp1-triple-aromatic-media-opportunity` -> `entity:aromatic_degradation`
- `navigation_edge` `about_entity`: `stmt:adp1-triple-aromatic-media-opportunity` -> `entity:dataset:adp1-aromatic-media-validation-matrix`
- `navigation_edge` `about_entity`: `stmt:adp1-triple-aromatic-media-opportunity` -> `entity:fba_model`
- `navigation_edge` `about_entity`: `stmt:adp1-triple-aromatic-media-opportunity` -> `entity:minimal-media`
- `navigation_edge` `about_entity`: `stmt:adp1-triple-continuous-fitness-claim` -> `entity:adp1`
- `navigation_edge` `about_entity`: `stmt:adp1-triple-continuous-fitness-claim` -> `entity:collection:adp1_triple_essentiality`
- `navigation_edge` `about_entity`: `stmt:adp1-triple-fba-growth-caveat` -> `entity:adp1`
- `navigation_edge` `about_entity`: `stmt:adp1-triple-fba-growth-caveat` -> `entity:collection:adp1_triple_essentiality`
- `navigation_edge` `about_entity`: `stmt:adp1-triple-fba-growth-caveat` -> `entity:fba_model`
- `navigation_edge` `about_entity`: `stmt:adp1-triple-fitness-predictor-finding` -> `entity:adp1`
- `navigation_edge` `about_entity`: `stmt:adp1-triple-fitness-predictor-finding` -> `entity:collection:adp1_triple_essentiality`
- `navigation_edge` `about_entity`: `stmt:adp1-triple-proteomics-finding` -> `entity:adp1`
- `navigation_edge` `about_entity`: `stmt:adp1-triple-proteomics-finding` -> `entity:collection:adp1_triple_essentiality`
- `navigation_edge` `member_of_topic`: `stmt:adp1-explorer-database-bridge-claim` -> `topic:adp1-data-integration`
- `navigation_edge` `member_of_topic`: `stmt:adp1-explorer-discordance-opportunity` -> `topic:adp1-model-quality`
- `navigation_edge` `member_of_topic`: `stmt:adp1-explorer-gapfilling-caveat` -> `topic:adp1-model-quality`
- `navigation_edge` `member_of_topic`: `stmt:adp1-triple-aromatic-discordance-finding` -> `topic:adp1-model-quality`
- `navigation_edge` `member_of_topic`: `stmt:adp1-triple-aromatic-media-opportunity` -> `topic:adp1-carbon-fitness`
- `navigation_edge` `member_of_topic`: `stmt:adp1-triple-aromatic-media-opportunity` -> `topic:adp1-model-quality`
- `navigation_edge` `member_of_topic`: `stmt:adp1-triple-continuous-fitness-claim` -> `topic:adp1-carbon-fitness`
- `navigation_edge` `member_of_topic`: `stmt:adp1-triple-continuous-fitness-claim` -> `topic:adp1-model-quality`
- `navigation_edge` `member_of_topic`: `stmt:adp1-triple-fba-growth-caveat` -> `topic:adp1-model-quality`
- `navigation_edge` `member_of_topic`: `stmt:adp1-triple-fitness-predictor-finding` -> `topic:adp1-carbon-fitness`
- `navigation_edge` `member_of_topic`: `stmt:adp1-triple-fitness-predictor-finding` -> `topic:adp1-model-quality`
- `navigation_edge` `member_of_topic`: `stmt:adp1-triple-proteomics-finding` -> `topic:adp1-model-quality`
- `provenance_edge` `cites`: `evidence:3d4a1b8cec14598d` -> `figure:adp1_triple_essentiality:figures/rast_enrichment_discordant.png`
- `provenance_edge` `cites`: `evidence:4c893fc47311557c` -> `figure:acinetobacter_adp1_explorer:figures/gapfilling_impact.png`
- `provenance_edge` `cites`: `evidence:c42579f962551574` -> `figure:adp1_triple_essentiality:figures/fba_growth_concordance.png`
- `provenance_edge` `cites`: `evidence:db383272ca8f0ceb` -> `figure:adp1_triple_essentiality:figures/roc_comprehensive.png`
- `provenance_edge` `extracted_from`: `evidence:154e2d833f5c98a7` -> `project:adp1_triple_essentiality`
- `provenance_edge` `extracted_from`: `evidence:154e2d833f5c98a7` -> `source_doc:adp1_triple_essentiality:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:154e2d833f5c98a7` -> `source_section:adp1_triple_essentiality:REPORT.md:Integrated Conclusions`
- `provenance_edge` `extracted_from`: `evidence:3b0ff3cf4b39cb89` -> `project:acinetobacter_adp1_explorer`
- `provenance_edge` `extracted_from`: `evidence:3b0ff3cf4b39cb89` -> `source_doc:acinetobacter_adp1_explorer:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:3b0ff3cf4b39cb89` -> `source_section:acinetobacter_adp1_explorer:REPORT.md:Research Questions Answered`
- `provenance_edge` `extracted_from`: `evidence:3d4a1b8cec14598d` -> `project:adp1_triple_essentiality`
- `provenance_edge` `extracted_from`: `evidence:3d4a1b8cec14598d` -> `source_doc:adp1_triple_essentiality:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:3d4a1b8cec14598d` -> `source_section:adp1_triple_essentiality:REPORT.md:Key Findings`
- `provenance_edge` `extracted_from`: `evidence:4c893fc47311557c` -> `project:acinetobacter_adp1_explorer`
- `provenance_edge` `extracted_from`: `evidence:4c893fc47311557c` -> `source_doc:acinetobacter_adp1_explorer:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:4c893fc47311557c` -> `source_section:acinetobacter_adp1_explorer:REPORT.md:Key Findings`
- `provenance_edge` `extracted_from`: `evidence:62105260d6569ebc` -> `project:adp1_triple_essentiality`
- `provenance_edge` `extracted_from`: `evidence:62105260d6569ebc` -> `source_doc:adp1_triple_essentiality:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:62105260d6569ebc` -> `source_section:adp1_triple_essentiality:REPORT.md:Recommendations`
- `provenance_edge` `extracted_from`: `evidence:c42579f962551574` -> `project:adp1_triple_essentiality`
- `provenance_edge` `extracted_from`: `evidence:c42579f962551574` -> `source_doc:adp1_triple_essentiality:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:c42579f962551574` -> `source_section:adp1_triple_essentiality:REPORT.md:Key Findings`
- `provenance_edge` `extracted_from`: `evidence:c9ca6ed0aa39959b` -> `project:acinetobacter_adp1_explorer`
- `provenance_edge` `extracted_from`: `evidence:c9ca6ed0aa39959b` -> `source_doc:acinetobacter_adp1_explorer:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:c9ca6ed0aa39959b` -> `source_section:acinetobacter_adp1_explorer:REPORT.md:Interpretation`
- `provenance_edge` `extracted_from`: `evidence:d48ec4e4f428af68` -> `project:adp1_triple_essentiality`
- `provenance_edge` `extracted_from`: `evidence:d48ec4e4f428af68` -> `source_doc:adp1_triple_essentiality:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:d48ec4e4f428af68` -> `source_section:adp1_triple_essentiality:REPORT.md:Recommendations`
- `provenance_edge` `extracted_from`: `evidence:db383272ca8f0ceb` -> `project:adp1_triple_essentiality`
- `provenance_edge` `extracted_from`: `evidence:db383272ca8f0ceb` -> `source_doc:adp1_triple_essentiality:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:db383272ca8f0ceb` -> `source_section:adp1_triple_essentiality:REPORT.md:Integrated Discussion`
- `provenance_edge` `has_evidence`: `stmt:adp1-explorer-database-bridge-claim` -> `evidence:c9ca6ed0aa39959b`
- `provenance_edge` `has_evidence`: `stmt:adp1-explorer-discordance-opportunity` -> `evidence:3b0ff3cf4b39cb89`
- `provenance_edge` `has_evidence`: `stmt:adp1-explorer-gapfilling-caveat` -> `evidence:4c893fc47311557c`
- `provenance_edge` `has_evidence`: `stmt:adp1-triple-aromatic-discordance-finding` -> `evidence:3d4a1b8cec14598d`
- `provenance_edge` `has_evidence`: `stmt:adp1-triple-aromatic-media-opportunity` -> `evidence:d48ec4e4f428af68`
- `provenance_edge` `has_evidence`: `stmt:adp1-triple-continuous-fitness-claim` -> `evidence:62105260d6569ebc`
- `provenance_edge` `has_evidence`: `stmt:adp1-triple-fba-growth-caveat` -> `evidence:c42579f962551574`
- `provenance_edge` `has_evidence`: `stmt:adp1-triple-fitness-predictor-finding` -> `evidence:db383272ca8f0ceb`
- `provenance_edge` `has_evidence`: `stmt:adp1-triple-proteomics-finding` -> `evidence:154e2d833f5c98a7`
- `provenance_edge` `uses_notebook`: `evidence:4c893fc47311557c` -> `notebook:acinetobacter_adp1_explorer:05_metabolic_model_and_phenotypes.ipynb`
- `provenance_edge` `uses_notebook`: `evidence:db383272ca8f0ceb` -> `notebook:adp1_triple_essentiality:04_roc_analysis.ipynb`
- `review_edge` `needs_review`: `stmt:adp1-explorer-discordance-opportunity` -> `stmt:adp1-explorer-database-bridge-claim`
- `review_edge` `needs_review`: `stmt:adp1-triple-aromatic-media-opportunity` -> `stmt:adp1-triple-continuous-fitness-claim`
- `scientific_edge` `motivates`: `stmt:adp1-explorer-database-bridge-claim` -> `stmt:adp1-explorer-discordance-opportunity`
- `scientific_edge` `motivates`: `stmt:adp1-explorer-gapfilling-caveat` -> `stmt:adp1-explorer-discordance-opportunity`
- `scientific_edge` `motivates`: `stmt:adp1-triple-aromatic-discordance-finding` -> `stmt:adp1-triple-aromatic-media-opportunity`
- `scientific_edge` `motivates`: `stmt:adp1-triple-continuous-fitness-claim` -> `stmt:adp1-triple-aromatic-media-opportunity`
- `scientific_edge` `motivates`: `stmt:adp1-triple-fba-growth-caveat` -> `stmt:adp1-triple-aromatic-media-opportunity`
- `scientific_edge` `refines`: `stmt:adp1-triple-fba-growth-caveat` -> `stmt:adp1-triple-continuous-fitness-claim`
- `scientific_edge` `supports`: `stmt:adp1-explorer-berdl-connectivity-finding` -> `stmt:adp1-explorer-database-bridge-claim`
- `scientific_edge` `supports`: `stmt:adp1-explorer-multiomics-finding` -> `stmt:adp1-explorer-database-bridge-claim`
- `scientific_edge` `supports`: `stmt:adp1-explorer-pangenome-bridge-finding` -> `stmt:adp1-explorer-database-bridge-claim`
- `scientific_edge` `supports`: `stmt:adp1-triple-aromatic-discordance-finding` -> `stmt:adp1-triple-continuous-fitness-claim`
- `scientific_edge` `supports`: `stmt:adp1-triple-fitness-predictor-finding` -> `stmt:adp1-triple-continuous-fitness-claim`
- `scientific_edge` `supports`: `stmt:adp1-triple-proteomics-finding` -> `stmt:adp1-triple-continuous-fitness-claim`

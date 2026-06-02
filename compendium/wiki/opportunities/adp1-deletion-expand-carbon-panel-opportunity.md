---
page_id: opportunity:adp1-deletion-expand-carbon-panel-opportunity
page_type: opportunity
member_hash: hash:a89bffc675e3bf8a
---

# Expanding ADP1 deletion phenotyping beyond eight carbon sources could test whether the observed independent dimensions increase with condition coverage.

- Page type: `opportunity`
- Member hash: `hash:a89bffc675e3bf8a`
- Graph: [Graph](../graph.md)

## Outgoing Links

- [Adp1 Deletion Continuum Claim](../claims/adp1-deletion-continuum-claim.md)
- [Adp1 Explorer Database Bridge Claim](../claims/adp1-explorer-database-bridge-claim.md)
- [Adp1 Triple Continuous Fitness Claim](../claims/adp1-triple-continuous-fitness-claim.md)
- [Adp1](../entities/adp1.md)
- [Berdl](../entities/berdl.md)
- [Quinate](../entities/quinate.md)
- [Adp1 Explorer Discordance Opportunity](../opportunities/adp1-explorer-discordance-opportunity.md)
- [Adp1 Triple Aromatic Media Opportunity](../opportunities/adp1-triple-aromatic-media-opportunity.md)
- [Acinetobacter Adp1 Explorer](../projects/acinetobacter-adp1-explorer.md)
- [Adp1 Deletion Phenotypes](../projects/adp1-deletion-phenotypes.md)
- [Adp1 Triple Essentiality](../projects/adp1-triple-essentiality.md)
- [Adp1 Carbon Fitness](../topics/adp1-carbon-fitness.md)
- [Adp1 Data Integration](../topics/adp1-data-integration.md)
- [Adp1 Model Quality](../topics/adp1-model-quality.md)

## Backlinks

- [Adp1 Deletion Continuum Claim](../claims/adp1-deletion-continuum-claim.md)
- [Adp1](../entities/adp1.md)
- [Quinate](../entities/quinate.md)
- [Home](../index.md)
- [Adp1 Explorer Discordance Opportunity](../opportunities/adp1-explorer-discordance-opportunity.md)
- [Adp1 Explorer Urea Deep Dive Opportunity](../opportunities/adp1-explorer-urea-deep-dive-opportunity.md)
- [Adp1 Triple Aromatic Media Opportunity](../opportunities/adp1-triple-aromatic-media-opportunity.md)
- [Adp1 Deletion Phenotypes](../projects/adp1-deletion-phenotypes.md)
- [Adp1 Carbon Fitness](../topics/adp1-carbon-fitness.md)

## Motivating Evidence

- `stmt:adp1-deletion-condition-independence-finding`: ADP1 carbon-source assays provide multiple independent phenotypic dimensions rather than one shared growth-sensitivity axis. `finding` `grounded` `high` (adp1_deletion_phenotypes/REPORT.md)
- [stmt:adp1-deletion-continuum-claim](../claims/adp1-deletion-continuum-claim.md): ADP1 condition-dependent essentiality should be modeled as a continuous phenotype landscape with quinate degradation as a discrete exception. `claim` `grounded` `high` (adp1_deletion_phenotypes/REPORT.md)
- `stmt:adp1-deletion-quinate-module-finding`: Quinate degradation is the main discrete exception to the otherwise continuous ADP1 carbon-fitness landscape. `finding` `grounded` `high` (adp1_deletion_phenotypes/REPORT.md)

## Opportunity

- [stmt:adp1-deletion-expand-carbon-panel-opportunity](../opportunities/adp1-deletion-expand-carbon-panel-opportunity.md): Expanding ADP1 deletion phenotyping beyond eight carbon sources could test whether the observed independent dimensions increase with condition coverage. `opportunity` `grounded` `medium` (adp1_deletion_phenotypes/REPORT.md)

## Related Claims

- [stmt:adp1-deletion-continuum-claim](../claims/adp1-deletion-continuum-claim.md): ADP1 condition-dependent essentiality should be modeled as a continuous phenotype landscape with quinate degradation as a discrete exception. `claim` `grounded` `high` (adp1_deletion_phenotypes/REPORT.md)
- [stmt:adp1-explorer-database-bridge-claim](../claims/adp1-explorer-database-bridge-claim.md): The ADP1 data explorer can serve as a BERDL bridge for downstream ADP1 synthesis pages. `claim` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)
- [stmt:adp1-triple-continuous-fitness-claim](../claims/adp1-triple-continuous-fitness-claim.md): ADP1 essentiality synthesis should prioritize continuous fitness and orthogonal evidence over binary essentiality thresholds alone. `claim` `grounded` `high` (adp1_triple_essentiality/REPORT.md)

## Required Validation

- [stmt:adp1-deletion-continuum-claim](../claims/adp1-deletion-continuum-claim.md): ADP1 condition-dependent essentiality should be modeled as a continuous phenotype landscape with quinate degradation as a discrete exception. `claim` `grounded` `high` (adp1_deletion_phenotypes/REPORT.md)

## Source Statements

### stmt:adp1-deletion-condition-independence-finding

ADP1 carbon-source assays provide multiple independent phenotypic dimensions rather than one shared growth-sensitivity axis.

- Kind/tier/confidence: `finding` / `grounded` / `high`
- Scope: `project_local`
- Source: `adp1_deletion_phenotypes/REPORT.md`
- Section: `Results`
- Evidence: The low pairwise correlations (median Pearson r = 0.25, maximum r = 0.58) demonstrate that each carbon source imposes a largely independent set of gene requirements.
- Figure: `figures/condition_clustermap.png`
- Notebook: `02_condition_structure.ipynb`
- Topics: [Adp1 Carbon Fitness](../topics/adp1-carbon-fitness.md)
- Entities: [Adp1](../entities/adp1.md)
- Supports: [stmt:adp1-deletion-continuum-claim](../claims/adp1-deletion-continuum-claim.md)
- Motivates: [stmt:adp1-deletion-expand-carbon-panel-opportunity](../opportunities/adp1-deletion-expand-carbon-panel-opportunity.md)

### stmt:adp1-deletion-continuum-claim

ADP1 condition-dependent essentiality should be modeled as a continuous phenotype landscape with quinate degradation as a discrete exception.

- Kind/tier/confidence: `claim` / `grounded` / `high`
- Scope: `project_local`
- Source: `adp1_deletion_phenotypes/REPORT.md`
- Section: `Novel Contribution`
- Evidence: The quinate degradation pathway is the sole exception, forming the only discrete phenotypic module.
- Figure: `figures/gene_heatmap.png`
- Notebook: `03_gene_modules.ipynb`
- Topics: [Adp1 Carbon Fitness](../topics/adp1-carbon-fitness.md)
- Entities: [Adp1](../entities/adp1.md)
- Motivates: [stmt:adp1-deletion-expand-carbon-panel-opportunity](../opportunities/adp1-deletion-expand-carbon-panel-opportunity.md)

### stmt:adp1-deletion-expand-carbon-panel-opportunity

Expanding ADP1 deletion phenotyping beyond eight carbon sources could test whether the observed independent dimensions increase with condition coverage.

- Kind/tier/confidence: `opportunity` / `grounded` / `medium`
- Scope: `project_local`
- Source: `adp1_deletion_phenotypes/REPORT.md`
- Section: `Limitations`
- Evidence: Only 8 carbon sources were tested. The ~5 independent dimensions may increase with more conditions.
- Topics: [Adp1 Carbon Fitness](../topics/adp1-carbon-fitness.md)
- Entities: [Adp1](../entities/adp1.md)
- Requires Validation: [stmt:adp1-deletion-continuum-claim](../claims/adp1-deletion-continuum-claim.md)

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

## Local Graph

- `navigation_edge` `about_entity`: `stmt:adp1-deletion-condition-independence-finding` -> `entity:adp1`
- `navigation_edge` `about_entity`: `stmt:adp1-deletion-condition-independence-finding` -> `entity:collection:adp1_deletion_phenotypes`
- `navigation_edge` `about_entity`: `stmt:adp1-deletion-condition-independence-finding` -> `entity:eight-carbon-sources`
- `navigation_edge` `about_entity`: `stmt:adp1-deletion-continuum-claim` -> `entity:adp1`
- `navigation_edge` `about_entity`: `stmt:adp1-deletion-continuum-claim` -> `entity:collection:adp1_deletion_phenotypes`
- `navigation_edge` `about_entity`: `stmt:adp1-deletion-continuum-claim` -> `entity:eight-carbon-sources`
- `navigation_edge` `about_entity`: `stmt:adp1-deletion-expand-carbon-panel-opportunity` -> `entity:adp1`
- `navigation_edge` `about_entity`: `stmt:adp1-deletion-expand-carbon-panel-opportunity` -> `entity:dataset:adp1-expanded-carbon-source-growth-matrix`
- `navigation_edge` `about_entity`: `stmt:adp1-deletion-expand-carbon-panel-opportunity` -> `entity:expanded-carbon-source-panel`
- `navigation_edge` `about_entity`: `stmt:adp1-deletion-quinate-module-finding` -> `entity:adp1`
- `navigation_edge` `about_entity`: `stmt:adp1-deletion-quinate-module-finding` -> `entity:collection:adp1_deletion_phenotypes`
- `navigation_edge` `about_entity`: `stmt:adp1-deletion-quinate-module-finding` -> `entity:quinate`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-database-bridge-claim` -> `entity:adp1`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-database-bridge-claim` -> `entity:berdl`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-database-bridge-claim` -> `entity:collection:adp1_multiomics_database`
- `navigation_edge` `about_entity`: `stmt:adp1-triple-continuous-fitness-claim` -> `entity:adp1`
- `navigation_edge` `about_entity`: `stmt:adp1-triple-continuous-fitness-claim` -> `entity:collection:adp1_triple_essentiality`
- `navigation_edge` `member_of_topic`: `stmt:adp1-deletion-condition-independence-finding` -> `topic:adp1-carbon-fitness`
- `navigation_edge` `member_of_topic`: `stmt:adp1-deletion-continuum-claim` -> `topic:adp1-carbon-fitness`
- `navigation_edge` `member_of_topic`: `stmt:adp1-deletion-expand-carbon-panel-opportunity` -> `topic:adp1-carbon-fitness`
- `navigation_edge` `member_of_topic`: `stmt:adp1-deletion-quinate-module-finding` -> `topic:adp1-carbon-fitness`
- `navigation_edge` `member_of_topic`: `stmt:adp1-explorer-database-bridge-claim` -> `topic:adp1-data-integration`
- `navigation_edge` `member_of_topic`: `stmt:adp1-triple-continuous-fitness-claim` -> `topic:adp1-carbon-fitness`
- `navigation_edge` `member_of_topic`: `stmt:adp1-triple-continuous-fitness-claim` -> `topic:adp1-model-quality`
- `provenance_edge` `cites`: `evidence:2e4026ebef8a4f47` -> `figure:adp1_deletion_phenotypes:figures/gene_heatmap.png`
- `provenance_edge` `cites`: `evidence:cadf3bedb4bb73e8` -> `figure:adp1_deletion_phenotypes:figures/module_profiles.png`
- `provenance_edge` `cites`: `evidence:fe2c4a25cd8076da` -> `figure:adp1_deletion_phenotypes:figures/condition_clustermap.png`
- `provenance_edge` `extracted_from`: `evidence:2e4026ebef8a4f47` -> `project:adp1_deletion_phenotypes`
- `provenance_edge` `extracted_from`: `evidence:2e4026ebef8a4f47` -> `source_doc:adp1_deletion_phenotypes:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:2e4026ebef8a4f47` -> `source_section:adp1_deletion_phenotypes:REPORT.md:Novel Contribution`
- `provenance_edge` `extracted_from`: `evidence:62105260d6569ebc` -> `project:adp1_triple_essentiality`
- `provenance_edge` `extracted_from`: `evidence:62105260d6569ebc` -> `source_doc:adp1_triple_essentiality:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:62105260d6569ebc` -> `source_section:adp1_triple_essentiality:REPORT.md:Recommendations`
- `provenance_edge` `extracted_from`: `evidence:c9ca6ed0aa39959b` -> `project:acinetobacter_adp1_explorer`
- `provenance_edge` `extracted_from`: `evidence:c9ca6ed0aa39959b` -> `source_doc:acinetobacter_adp1_explorer:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:c9ca6ed0aa39959b` -> `source_section:acinetobacter_adp1_explorer:REPORT.md:Interpretation`
- `provenance_edge` `extracted_from`: `evidence:cadf3bedb4bb73e8` -> `project:adp1_deletion_phenotypes`
- `provenance_edge` `extracted_from`: `evidence:cadf3bedb4bb73e8` -> `source_doc:adp1_deletion_phenotypes:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:cadf3bedb4bb73e8` -> `source_section:adp1_deletion_phenotypes:REPORT.md:Key Findings`
- `provenance_edge` `extracted_from`: `evidence:d44ad77070799add` -> `project:adp1_deletion_phenotypes`
- `provenance_edge` `extracted_from`: `evidence:d44ad77070799add` -> `source_doc:adp1_deletion_phenotypes:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:d44ad77070799add` -> `source_section:adp1_deletion_phenotypes:REPORT.md:Limitations`
- `provenance_edge` `extracted_from`: `evidence:fe2c4a25cd8076da` -> `project:adp1_deletion_phenotypes`
- `provenance_edge` `extracted_from`: `evidence:fe2c4a25cd8076da` -> `source_doc:adp1_deletion_phenotypes:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:fe2c4a25cd8076da` -> `source_section:adp1_deletion_phenotypes:REPORT.md:Results`
- `provenance_edge` `has_evidence`: `stmt:adp1-deletion-condition-independence-finding` -> `evidence:fe2c4a25cd8076da`
- `provenance_edge` `has_evidence`: `stmt:adp1-deletion-continuum-claim` -> `evidence:2e4026ebef8a4f47`
- `provenance_edge` `has_evidence`: `stmt:adp1-deletion-expand-carbon-panel-opportunity` -> `evidence:d44ad77070799add`
- `provenance_edge` `has_evidence`: `stmt:adp1-deletion-quinate-module-finding` -> `evidence:cadf3bedb4bb73e8`
- `provenance_edge` `has_evidence`: `stmt:adp1-explorer-database-bridge-claim` -> `evidence:c9ca6ed0aa39959b`
- `provenance_edge` `has_evidence`: `stmt:adp1-triple-continuous-fitness-claim` -> `evidence:62105260d6569ebc`
- `provenance_edge` `uses_notebook`: `evidence:2e4026ebef8a4f47` -> `notebook:adp1_deletion_phenotypes:03_gene_modules.ipynb`
- `provenance_edge` `uses_notebook`: `evidence:cadf3bedb4bb73e8` -> `notebook:adp1_deletion_phenotypes:03_gene_modules.ipynb`
- `provenance_edge` `uses_notebook`: `evidence:fe2c4a25cd8076da` -> `notebook:adp1_deletion_phenotypes:02_condition_structure.ipynb`
- `review_edge` `needs_review`: `stmt:adp1-deletion-expand-carbon-panel-opportunity` -> `stmt:adp1-deletion-continuum-claim`
- `review_edge` `needs_review`: `stmt:adp1-explorer-discordance-opportunity` -> `stmt:adp1-explorer-database-bridge-claim`
- `review_edge` `needs_review`: `stmt:adp1-triple-aromatic-media-opportunity` -> `stmt:adp1-triple-continuous-fitness-claim`
- `scientific_edge` `motivates`: `stmt:adp1-deletion-condition-independence-finding` -> `stmt:adp1-deletion-expand-carbon-panel-opportunity`
- `scientific_edge` `motivates`: `stmt:adp1-deletion-continuum-claim` -> `stmt:adp1-deletion-expand-carbon-panel-opportunity`
- `scientific_edge` `motivates`: `stmt:adp1-deletion-quinate-module-finding` -> `stmt:adp1-deletion-expand-carbon-panel-opportunity`
- `scientific_edge` `motivates`: `stmt:adp1-explorer-database-bridge-claim` -> `stmt:adp1-explorer-discordance-opportunity`
- `scientific_edge` `motivates`: `stmt:adp1-triple-continuous-fitness-claim` -> `stmt:adp1-triple-aromatic-media-opportunity`
- `scientific_edge` `refines`: `stmt:adp1-triple-fba-growth-caveat` -> `stmt:adp1-triple-continuous-fitness-claim`
- `scientific_edge` `supports`: `stmt:adp1-deletion-carbon-tier-finding` -> `stmt:adp1-deletion-continuum-claim`
- `scientific_edge` `supports`: `stmt:adp1-deletion-condition-independence-finding` -> `stmt:adp1-deletion-continuum-claim`
- `scientific_edge` `supports`: `stmt:adp1-deletion-quinate-module-finding` -> `stmt:adp1-deletion-continuum-claim`
- `scientific_edge` `supports`: `stmt:adp1-explorer-berdl-connectivity-finding` -> `stmt:adp1-explorer-database-bridge-claim`
- `scientific_edge` `supports`: `stmt:adp1-explorer-multiomics-finding` -> `stmt:adp1-explorer-database-bridge-claim`
- `scientific_edge` `supports`: `stmt:adp1-explorer-pangenome-bridge-finding` -> `stmt:adp1-explorer-database-bridge-claim`
- `scientific_edge` `supports`: `stmt:adp1-triple-aromatic-discordance-finding` -> `stmt:adp1-triple-continuous-fitness-claim`
- `scientific_edge` `supports`: `stmt:adp1-triple-fitness-predictor-finding` -> `stmt:adp1-triple-continuous-fitness-claim`
- `scientific_edge` `supports`: `stmt:adp1-triple-proteomics-finding` -> `stmt:adp1-triple-continuous-fitness-claim`

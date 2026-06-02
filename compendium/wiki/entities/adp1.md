---
page_id: entity:adp1
page_type: entity
member_hash: hash:054b7e08bfb16c51
---

# Entity: Adp1

- Page type: `entity`
- Member hash: `hash:054b7e08bfb16c51`
- Graph: [Graph](../graph.md)

## Introduction

This entity page is a backlink hub for Entity: Adp1. It gathers 19 statements from `acinetobacter_adp1_explorer`, `adp1_deletion_phenotypes`, and `adp1_triple_essentiality` and shows how the entity participates in findings, claims, caveats, and opportunities across the wiki.

## Synthesis

Reusable claims frame this page. [stmt:adp1-deletion-continuum-claim](../claims/adp1-deletion-continuum-claim.md) states that ADP1 condition-dependent essentiality should be modeled as a continuous phenotype landscape with quinate degradation as a discrete exception. [stmt:adp1-deletion-continuum-claim; adp1_deletion_phenotypes]. [stmt:adp1-explorer-database-bridge-claim](../claims/adp1-explorer-database-bridge-claim.md) states that The ADP1 data explorer can serve as a BERDL bridge for downstream ADP1 synthesis pages. [stmt:adp1-explorer-database-bridge-claim; acinetobacter_adp1_explorer]. [stmt:adp1-triple-continuous-fitness-claim](../claims/adp1-triple-continuous-fitness-claim.md) states that ADP1 essentiality synthesis should prioritize continuous fitness and orthogonal evidence over binary essentiality thresholds alone. [stmt:adp1-triple-continuous-fitness-claim; adp1_triple_essentiality].
The evidence base is anchored by several findings. `stmt:adp1-deletion-carbon-tier-finding` states that ADP1 deletion phenotypes across eight carbon sources separate into demanding, moderate, and robust growth-defect tiers. [stmt:adp1-deletion-carbon-tier-finding; adp1_deletion_phenotypes]. `stmt:adp1-deletion-condition-independence-finding` states that ADP1 carbon-source assays provide multiple independent phenotypic dimensions rather than one shared growth-sensitivity axis. [stmt:adp1-deletion-condition-independence-finding; adp1_deletion_phenotypes]. `stmt:adp1-deletion-quinate-module-finding` states that Quinate degradation is the main discrete exception to the otherwise continuous ADP1 carbon-fitness landscape. [stmt:adp1-deletion-quinate-module-finding; adp1_deletion_phenotypes]. 7 additional statements support this reading.
The synthesis should be read with several caveats. `stmt:adp1-explorer-gapfilling-caveat` states that ADP1 model-based growth predictions are quality-limited by heavy dependence on gapfilled reactions. [stmt:adp1-explorer-gapfilling-caveat; acinetobacter_adp1_explorer]. `stmt:adp1-triple-fba-growth-caveat` states that FBA class does not predict which TnSeq-dispensable ADP1 genes have measured growth defects. [stmt:adp1-triple-fba-growth-caveat; adp1_triple_essentiality].
The most direct follow-up work spans several opportunities. [stmt:adp1-deletion-expand-carbon-panel-opportunity](../opportunities/adp1-deletion-expand-carbon-panel-opportunity.md) states that Expanding ADP1 deletion phenotyping beyond eight carbon sources could test whether the observed independent dimensions increase with condition coverage. [stmt:adp1-deletion-expand-carbon-panel-opportunity; adp1_deletion_phenotypes]. [stmt:adp1-explorer-discordance-opportunity](../opportunities/adp1-explorer-discordance-opportunity.md) states that FBA-TnSeq discordant genes in ADP1 should be prioritized for metabolic model refinement. [stmt:adp1-explorer-discordance-opportunity; acinetobacter_adp1_explorer]. [stmt:adp1-explorer-urea-deep-dive-opportunity](../opportunities/adp1-explorer-urea-deep-dive-opportunity.md) states that ADP1 urea-specific fitness genes and their pangenome conservation should be analyzed as an independent metabolism module. [stmt:adp1-explorer-urea-deep-dive-opportunity; acinetobacter_adp1_explorer]. 1 additional statements support this reading.

## Navigation Context

This page links out to 19 related pages and has 20 backlinks. Use those links to move between the prose note, the underlying evidence, and the graph neighborhood.

## Structured Evidence Summary

### Backlinks

- `stmt:adp1-deletion-carbon-tier-finding`: ADP1 deletion phenotypes across eight carbon sources separate into demanding, moderate, and robust growth-defect tiers. `finding` `grounded` `high` (adp1_deletion_phenotypes/REPORT.md)
- `stmt:adp1-deletion-condition-independence-finding`: ADP1 carbon-source assays provide multiple independent phenotypic dimensions rather than one shared growth-sensitivity axis. `finding` `grounded` `high` (adp1_deletion_phenotypes/REPORT.md)
- [stmt:adp1-deletion-continuum-claim](../claims/adp1-deletion-continuum-claim.md): ADP1 condition-dependent essentiality should be modeled as a continuous phenotype landscape with quinate degradation as a discrete exception. `claim` `grounded` `high` (adp1_deletion_phenotypes/REPORT.md)
- [stmt:adp1-deletion-expand-carbon-panel-opportunity](../opportunities/adp1-deletion-expand-carbon-panel-opportunity.md): Expanding ADP1 deletion phenotyping beyond eight carbon sources could test whether the observed independent dimensions increase with condition coverage. `opportunity` `grounded` `medium` (adp1_deletion_phenotypes/REPORT.md)
- `stmt:adp1-deletion-quinate-module-finding`: Quinate degradation is the main discrete exception to the otherwise continuous ADP1 carbon-fitness landscape. `finding` `grounded` `high` (adp1_deletion_phenotypes/REPORT.md)
- `stmt:adp1-explorer-berdl-connectivity-finding`: The ADP1 database connects strongly to BERDL through genomes, reactions, compounds, and pangenome clusters. `finding` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)
- `stmt:adp1-explorer-condition-fitness-finding`: ADP1 mutant growth fitness shows condition-specific structure, with urea and quinate behaving as outlier conditions. `finding` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)
- [stmt:adp1-explorer-database-bridge-claim](../claims/adp1-explorer-database-bridge-claim.md): The ADP1 data explorer can serve as a BERDL bridge for downstream ADP1 synthesis pages. `claim` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)
- [stmt:adp1-explorer-discordance-opportunity](../opportunities/adp1-explorer-discordance-opportunity.md): FBA-TnSeq discordant genes in ADP1 should be prioritized for metabolic model refinement. `opportunity` `grounded` `medium` (acinetobacter_adp1_explorer/REPORT.md)
- `stmt:adp1-explorer-gapfilling-caveat`: ADP1 model-based growth predictions are quality-limited by heavy dependence on gapfilled reactions. `caveat` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)
- `stmt:adp1-explorer-multiomics-finding`: The ADP1 database integrates six molecular and phenotype data modalities for Acinetobacter baylyi ADP1. `finding` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)
- `stmt:adp1-explorer-pangenome-bridge-finding`: A gene-junction bridge maps BERDL pangenome clusters to ADP1-style cluster IDs with complete gene-level coverage. `finding` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)
- [stmt:adp1-explorer-urea-deep-dive-opportunity](../opportunities/adp1-explorer-urea-deep-dive-opportunity.md): ADP1 urea-specific fitness genes and their pangenome conservation should be analyzed as an independent metabolism module. `opportunity` `grounded` `medium` (acinetobacter_adp1_explorer/REPORT.md)
- `stmt:adp1-triple-aromatic-discordance-finding`: Aromatic degradation genes are enriched among ADP1 FBA-discordant genes, indicating systematic model gaps. `finding` `grounded` `high` (adp1_triple_essentiality/REPORT.md)
- [stmt:adp1-triple-aromatic-media-opportunity](../opportunities/adp1-triple-aromatic-media-opportunity.md): ADP1 FBA media definitions should be refined with trace aromatic compounds and retested against aromatic-degradation discordance. `opportunity` `grounded` `medium` (adp1_triple_essentiality/REPORT.md)
- [stmt:adp1-triple-continuous-fitness-claim](../claims/adp1-triple-continuous-fitness-claim.md): ADP1 essentiality synthesis should prioritize continuous fitness and orthogonal evidence over binary essentiality thresholds alone. `claim` `grounded` `high` (adp1_triple_essentiality/REPORT.md)
- `stmt:adp1-triple-fba-growth-caveat`: FBA class does not predict which TnSeq-dispensable ADP1 genes have measured growth defects. `caveat` `grounded` `high` (adp1_triple_essentiality/REPORT.md)
- `stmt:adp1-triple-fitness-predictor-finding`: Continuous fitness values outperform binary essentiality fractions for predicting ADP1 essentiality. `finding` `grounded` `high` (adp1_triple_essentiality/REPORT.md)
- `stmt:adp1-triple-proteomics-finding`: Proteomics is a strong ADP1 essentiality signal and performs comparably to continuous fitness in ROC analysis. `finding` `grounded` `high` (adp1_triple_essentiality/REPORT.md)

### Claims

- [stmt:adp1-deletion-continuum-claim](../claims/adp1-deletion-continuum-claim.md): ADP1 condition-dependent essentiality should be modeled as a continuous phenotype landscape with quinate degradation as a discrete exception. `claim` `grounded` `high` (adp1_deletion_phenotypes/REPORT.md)
- [stmt:adp1-explorer-database-bridge-claim](../claims/adp1-explorer-database-bridge-claim.md): The ADP1 data explorer can serve as a BERDL bridge for downstream ADP1 synthesis pages. `claim` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)
- [stmt:adp1-triple-continuous-fitness-claim](../claims/adp1-triple-continuous-fitness-claim.md): ADP1 essentiality synthesis should prioritize continuous fitness and orthogonal evidence over binary essentiality thresholds alone. `claim` `grounded` `high` (adp1_triple_essentiality/REPORT.md)

### Conflicts And Caveats

- `stmt:adp1-explorer-gapfilling-caveat`: ADP1 model-based growth predictions are quality-limited by heavy dependence on gapfilled reactions. `caveat` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)
- `stmt:adp1-triple-fba-growth-caveat`: FBA class does not predict which TnSeq-dispensable ADP1 genes have measured growth defects. `caveat` `grounded` `high` (adp1_triple_essentiality/REPORT.md)

### Findings

- `stmt:adp1-deletion-carbon-tier-finding`: ADP1 deletion phenotypes across eight carbon sources separate into demanding, moderate, and robust growth-defect tiers. `finding` `grounded` `high` (adp1_deletion_phenotypes/REPORT.md)
- `stmt:adp1-deletion-condition-independence-finding`: ADP1 carbon-source assays provide multiple independent phenotypic dimensions rather than one shared growth-sensitivity axis. `finding` `grounded` `high` (adp1_deletion_phenotypes/REPORT.md)
- `stmt:adp1-deletion-quinate-module-finding`: Quinate degradation is the main discrete exception to the otherwise continuous ADP1 carbon-fitness landscape. `finding` `grounded` `high` (adp1_deletion_phenotypes/REPORT.md)
- `stmt:adp1-explorer-berdl-connectivity-finding`: The ADP1 database connects strongly to BERDL through genomes, reactions, compounds, and pangenome clusters. `finding` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)
- `stmt:adp1-explorer-condition-fitness-finding`: ADP1 mutant growth fitness shows condition-specific structure, with urea and quinate behaving as outlier conditions. `finding` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)
- `stmt:adp1-explorer-multiomics-finding`: The ADP1 database integrates six molecular and phenotype data modalities for Acinetobacter baylyi ADP1. `finding` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)
- `stmt:adp1-explorer-pangenome-bridge-finding`: A gene-junction bridge maps BERDL pangenome clusters to ADP1-style cluster IDs with complete gene-level coverage. `finding` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)
- `stmt:adp1-triple-aromatic-discordance-finding`: Aromatic degradation genes are enriched among ADP1 FBA-discordant genes, indicating systematic model gaps. `finding` `grounded` `high` (adp1_triple_essentiality/REPORT.md)
- `stmt:adp1-triple-fitness-predictor-finding`: Continuous fitness values outperform binary essentiality fractions for predicting ADP1 essentiality. `finding` `grounded` `high` (adp1_triple_essentiality/REPORT.md)
- `stmt:adp1-triple-proteomics-finding`: Proteomics is a strong ADP1 essentiality signal and performs comparably to continuous fitness in ROC analysis. `finding` `grounded` `high` (adp1_triple_essentiality/REPORT.md)

### Opportunities And Directions

- [stmt:adp1-deletion-expand-carbon-panel-opportunity](../opportunities/adp1-deletion-expand-carbon-panel-opportunity.md): Expanding ADP1 deletion phenotyping beyond eight carbon sources could test whether the observed independent dimensions increase with condition coverage. `opportunity` `grounded` `medium` (adp1_deletion_phenotypes/REPORT.md)
- [stmt:adp1-explorer-discordance-opportunity](../opportunities/adp1-explorer-discordance-opportunity.md): FBA-TnSeq discordant genes in ADP1 should be prioritized for metabolic model refinement. `opportunity` `grounded` `medium` (acinetobacter_adp1_explorer/REPORT.md)
- [stmt:adp1-explorer-urea-deep-dive-opportunity](../opportunities/adp1-explorer-urea-deep-dive-opportunity.md): ADP1 urea-specific fitness genes and their pangenome conservation should be analyzed as an independent metabolism module. `opportunity` `grounded` `medium` (acinetobacter_adp1_explorer/REPORT.md)
- [stmt:adp1-triple-aromatic-media-opportunity](../opportunities/adp1-triple-aromatic-media-opportunity.md): ADP1 FBA media definitions should be refined with trace aromatic compounds and retested against aromatic-degradation discordance. `opportunity` `grounded` `medium` (adp1_triple_essentiality/REPORT.md)

### Topic: Adp1 Carbon Fitness

- `stmt:adp1-deletion-carbon-tier-finding`: ADP1 deletion phenotypes across eight carbon sources separate into demanding, moderate, and robust growth-defect tiers. `finding` `grounded` `high` (adp1_deletion_phenotypes/REPORT.md)
- `stmt:adp1-deletion-condition-independence-finding`: ADP1 carbon-source assays provide multiple independent phenotypic dimensions rather than one shared growth-sensitivity axis. `finding` `grounded` `high` (adp1_deletion_phenotypes/REPORT.md)
- [stmt:adp1-deletion-continuum-claim](../claims/adp1-deletion-continuum-claim.md): ADP1 condition-dependent essentiality should be modeled as a continuous phenotype landscape with quinate degradation as a discrete exception. `claim` `grounded` `high` (adp1_deletion_phenotypes/REPORT.md)
- [stmt:adp1-deletion-expand-carbon-panel-opportunity](../opportunities/adp1-deletion-expand-carbon-panel-opportunity.md): Expanding ADP1 deletion phenotyping beyond eight carbon sources could test whether the observed independent dimensions increase with condition coverage. `opportunity` `grounded` `medium` (adp1_deletion_phenotypes/REPORT.md)
- `stmt:adp1-deletion-quinate-module-finding`: Quinate degradation is the main discrete exception to the otherwise continuous ADP1 carbon-fitness landscape. `finding` `grounded` `high` (adp1_deletion_phenotypes/REPORT.md)
- `stmt:adp1-explorer-condition-fitness-finding`: ADP1 mutant growth fitness shows condition-specific structure, with urea and quinate behaving as outlier conditions. `finding` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)
- [stmt:adp1-explorer-urea-deep-dive-opportunity](../opportunities/adp1-explorer-urea-deep-dive-opportunity.md): ADP1 urea-specific fitness genes and their pangenome conservation should be analyzed as an independent metabolism module. `opportunity` `grounded` `medium` (acinetobacter_adp1_explorer/REPORT.md)
- [stmt:adp1-triple-aromatic-media-opportunity](../opportunities/adp1-triple-aromatic-media-opportunity.md): ADP1 FBA media definitions should be refined with trace aromatic compounds and retested against aromatic-degradation discordance. `opportunity` `grounded` `medium` (adp1_triple_essentiality/REPORT.md)
- [stmt:adp1-triple-continuous-fitness-claim](../claims/adp1-triple-continuous-fitness-claim.md): ADP1 essentiality synthesis should prioritize continuous fitness and orthogonal evidence over binary essentiality thresholds alone. `claim` `grounded` `high` (adp1_triple_essentiality/REPORT.md)
- `stmt:adp1-triple-fitness-predictor-finding`: Continuous fitness values outperform binary essentiality fractions for predicting ADP1 essentiality. `finding` `grounded` `high` (adp1_triple_essentiality/REPORT.md)

### Topic: Adp1 Data Integration

- `stmt:adp1-explorer-berdl-connectivity-finding`: The ADP1 database connects strongly to BERDL through genomes, reactions, compounds, and pangenome clusters. `finding` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)
- [stmt:adp1-explorer-database-bridge-claim](../claims/adp1-explorer-database-bridge-claim.md): The ADP1 data explorer can serve as a BERDL bridge for downstream ADP1 synthesis pages. `claim` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)
- `stmt:adp1-explorer-multiomics-finding`: The ADP1 database integrates six molecular and phenotype data modalities for Acinetobacter baylyi ADP1. `finding` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)
- `stmt:adp1-explorer-pangenome-bridge-finding`: A gene-junction bridge maps BERDL pangenome clusters to ADP1-style cluster IDs with complete gene-level coverage. `finding` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)

### Topic: Adp1 Model Quality

- [stmt:adp1-explorer-discordance-opportunity](../opportunities/adp1-explorer-discordance-opportunity.md): FBA-TnSeq discordant genes in ADP1 should be prioritized for metabolic model refinement. `opportunity` `grounded` `medium` (acinetobacter_adp1_explorer/REPORT.md)
- `stmt:adp1-explorer-gapfilling-caveat`: ADP1 model-based growth predictions are quality-limited by heavy dependence on gapfilled reactions. `caveat` `grounded` `high` (acinetobacter_adp1_explorer/REPORT.md)
- `stmt:adp1-triple-aromatic-discordance-finding`: Aromatic degradation genes are enriched among ADP1 FBA-discordant genes, indicating systematic model gaps. `finding` `grounded` `high` (adp1_triple_essentiality/REPORT.md)
- [stmt:adp1-triple-aromatic-media-opportunity](../opportunities/adp1-triple-aromatic-media-opportunity.md): ADP1 FBA media definitions should be refined with trace aromatic compounds and retested against aromatic-degradation discordance. `opportunity` `grounded` `medium` (adp1_triple_essentiality/REPORT.md)
- [stmt:adp1-triple-continuous-fitness-claim](../claims/adp1-triple-continuous-fitness-claim.md): ADP1 essentiality synthesis should prioritize continuous fitness and orthogonal evidence over binary essentiality thresholds alone. `claim` `grounded` `high` (adp1_triple_essentiality/REPORT.md)
- `stmt:adp1-triple-fba-growth-caveat`: FBA class does not predict which TnSeq-dispensable ADP1 genes have measured growth defects. `caveat` `grounded` `high` (adp1_triple_essentiality/REPORT.md)
- `stmt:adp1-triple-fitness-predictor-finding`: Continuous fitness values outperform binary essentiality fractions for predicting ADP1 essentiality. `finding` `grounded` `high` (adp1_triple_essentiality/REPORT.md)
- `stmt:adp1-triple-proteomics-finding`: Proteomics is a strong ADP1 essentiality signal and performs comparably to continuous fitness in ROC analysis. `finding` `grounded` `high` (adp1_triple_essentiality/REPORT.md)

## Outgoing Links

- [Adp1 Deletion Continuum Claim](../claims/adp1-deletion-continuum-claim.md)
- [Adp1 Explorer Database Bridge Claim](../claims/adp1-explorer-database-bridge-claim.md)
- [Adp1 Triple Continuous Fitness Claim](../claims/adp1-triple-continuous-fitness-claim.md)
- [Adp1 Multiomics Database](../entities/adp1-multiomics-database.md)
- [Aromatic Degradation](../entities/aromatic-degradation.md)
- [Berdl](../entities/berdl.md)
- [Fba Model](../entities/fba-model.md)
- [Quinate](../entities/quinate.md)
- [Urea](../entities/urea.md)
- [Adp1 Deletion Expand Carbon Panel Opportunity](../opportunities/adp1-deletion-expand-carbon-panel-opportunity.md)
- [Adp1 Explorer Discordance Opportunity](../opportunities/adp1-explorer-discordance-opportunity.md)
- [Adp1 Explorer Urea Deep Dive Opportunity](../opportunities/adp1-explorer-urea-deep-dive-opportunity.md)
- [Adp1 Triple Aromatic Media Opportunity](../opportunities/adp1-triple-aromatic-media-opportunity.md)
- [Acinetobacter Adp1 Explorer](../projects/acinetobacter-adp1-explorer.md)
- [Adp1 Deletion Phenotypes](../projects/adp1-deletion-phenotypes.md)
- [Adp1 Triple Essentiality](../projects/adp1-triple-essentiality.md)
- [Adp1 Carbon Fitness](../topics/adp1-carbon-fitness.md)
- [Adp1 Data Integration](../topics/adp1-data-integration.md)
- [Adp1 Model Quality](../topics/adp1-model-quality.md)

## Backlinks

- [Adp1 Deletion Continuum Claim](../claims/adp1-deletion-continuum-claim.md)
- [Adp1 Explorer Database Bridge Claim](../claims/adp1-explorer-database-bridge-claim.md)
- [Adp1 Triple Continuous Fitness Claim](../claims/adp1-triple-continuous-fitness-claim.md)
- [Adp1 Multiomics Database](../entities/adp1-multiomics-database.md)
- [Aromatic Degradation](../entities/aromatic-degradation.md)
- [Berdl](../entities/berdl.md)
- [Fba Model](../entities/fba-model.md)
- [Quinate](../entities/quinate.md)
- [Urea](../entities/urea.md)
- [Home](../index.md)
- [Adp1 Deletion Expand Carbon Panel Opportunity](../opportunities/adp1-deletion-expand-carbon-panel-opportunity.md)
- [Adp1 Explorer Discordance Opportunity](../opportunities/adp1-explorer-discordance-opportunity.md)
- [Adp1 Explorer Urea Deep Dive Opportunity](../opportunities/adp1-explorer-urea-deep-dive-opportunity.md)
- [Adp1 Triple Aromatic Media Opportunity](../opportunities/adp1-triple-aromatic-media-opportunity.md)
- [Acinetobacter Adp1 Explorer](../projects/acinetobacter-adp1-explorer.md)
- [Adp1 Deletion Phenotypes](../projects/adp1-deletion-phenotypes.md)
- [Adp1 Triple Essentiality](../projects/adp1-triple-essentiality.md)
- [Adp1 Carbon Fitness](../topics/adp1-carbon-fitness.md)
- [Adp1 Data Integration](../topics/adp1-data-integration.md)
- [Adp1 Model Quality](../topics/adp1-model-quality.md)

## Source Statements

### stmt:adp1-deletion-carbon-tier-finding

ADP1 deletion phenotypes across eight carbon sources separate into demanding, moderate, and robust growth-defect tiers.

- Kind/tier/confidence: `finding` / `grounded` / `high`
- Scope: `project_local`
- Source: `adp1_deletion_phenotypes/REPORT.md`
- Section: `Key Findings`
- Evidence: The 8 carbon sources partition into demanding, moderate, and robust tiers based on the fraction of genes showing growth defects.
- Figure: `figures/condition_boxplots.png`
- Notebook: `01_data_extraction.ipynb`
- Topics: [Adp1 Carbon Fitness](../topics/adp1-carbon-fitness.md)
- Entities: [Adp1](../entities/adp1.md)
- Supports: [stmt:adp1-deletion-continuum-claim](../claims/adp1-deletion-continuum-claim.md)

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

- `navigation_edge` `about_entity`: `stmt:adp1-deletion-carbon-tier-finding` -> `entity:adp1`
- `navigation_edge` `about_entity`: `stmt:adp1-deletion-carbon-tier-finding` -> `entity:collection:adp1_deletion_phenotypes`
- `navigation_edge` `about_entity`: `stmt:adp1-deletion-carbon-tier-finding` -> `entity:eight-carbon-sources`
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
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-berdl-connectivity-finding` -> `entity:adp1`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-berdl-connectivity-finding` -> `entity:berdl`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-berdl-connectivity-finding` -> `entity:collection:adp1_multiomics_database`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-condition-fitness-finding` -> `entity:adp1`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-condition-fitness-finding` -> `entity:collection:adp1_multiomics_database`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-condition-fitness-finding` -> `entity:eight-carbon-sources`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-condition-fitness-finding` -> `entity:quinate`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-condition-fitness-finding` -> `entity:urea`
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
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-urea-deep-dive-opportunity` -> `entity:adp1`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-urea-deep-dive-opportunity` -> `entity:dataset:adp1-urea-specific-gene-conservation`
- `navigation_edge` `about_entity`: `stmt:adp1-explorer-urea-deep-dive-opportunity` -> `entity:urea`
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
- `navigation_edge` `member_of_topic`: `stmt:adp1-deletion-carbon-tier-finding` -> `topic:adp1-carbon-fitness`
- `navigation_edge` `member_of_topic`: `stmt:adp1-deletion-condition-independence-finding` -> `topic:adp1-carbon-fitness`
- `navigation_edge` `member_of_topic`: `stmt:adp1-deletion-continuum-claim` -> `topic:adp1-carbon-fitness`
- `navigation_edge` `member_of_topic`: `stmt:adp1-deletion-expand-carbon-panel-opportunity` -> `topic:adp1-carbon-fitness`
- `navigation_edge` `member_of_topic`: `stmt:adp1-deletion-quinate-module-finding` -> `topic:adp1-carbon-fitness`
- `navigation_edge` `member_of_topic`: `stmt:adp1-explorer-berdl-connectivity-finding` -> `topic:adp1-data-integration`
- `navigation_edge` `member_of_topic`: `stmt:adp1-explorer-condition-fitness-finding` -> `topic:adp1-carbon-fitness`
- `navigation_edge` `member_of_topic`: `stmt:adp1-explorer-database-bridge-claim` -> `topic:adp1-data-integration`
- `navigation_edge` `member_of_topic`: `stmt:adp1-explorer-discordance-opportunity` -> `topic:adp1-model-quality`
- `navigation_edge` `member_of_topic`: `stmt:adp1-explorer-gapfilling-caveat` -> `topic:adp1-model-quality`
- `navigation_edge` `member_of_topic`: `stmt:adp1-explorer-multiomics-finding` -> `topic:adp1-data-integration`
- `navigation_edge` `member_of_topic`: `stmt:adp1-explorer-pangenome-bridge-finding` -> `topic:adp1-data-integration`
- `navigation_edge` `member_of_topic`: `stmt:adp1-explorer-urea-deep-dive-opportunity` -> `topic:adp1-carbon-fitness`
- `navigation_edge` `member_of_topic`: `stmt:adp1-triple-aromatic-discordance-finding` -> `topic:adp1-model-quality`
- `navigation_edge` `member_of_topic`: `stmt:adp1-triple-aromatic-media-opportunity` -> `topic:adp1-carbon-fitness`
- `navigation_edge` `member_of_topic`: `stmt:adp1-triple-aromatic-media-opportunity` -> `topic:adp1-model-quality`
- `navigation_edge` `member_of_topic`: `stmt:adp1-triple-continuous-fitness-claim` -> `topic:adp1-carbon-fitness`
- `navigation_edge` `member_of_topic`: `stmt:adp1-triple-continuous-fitness-claim` -> `topic:adp1-model-quality`
- `navigation_edge` `member_of_topic`: `stmt:adp1-triple-fba-growth-caveat` -> `topic:adp1-model-quality`
- `navigation_edge` `member_of_topic`: `stmt:adp1-triple-fitness-predictor-finding` -> `topic:adp1-carbon-fitness`
- `navigation_edge` `member_of_topic`: `stmt:adp1-triple-fitness-predictor-finding` -> `topic:adp1-model-quality`
- `navigation_edge` `member_of_topic`: `stmt:adp1-triple-proteomics-finding` -> `topic:adp1-model-quality`
- `provenance_edge` `cites`: `evidence:2e4026ebef8a4f47` -> `figure:adp1_deletion_phenotypes:figures/gene_heatmap.png`
- `provenance_edge` `cites`: `evidence:3a118ea8c0f0e2af` -> `figure:adp1_deletion_phenotypes:figures/condition_boxplots.png`
- `provenance_edge` `cites`: `evidence:3d4a1b8cec14598d` -> `figure:adp1_triple_essentiality:figures/rast_enrichment_discordant.png`
- `provenance_edge` `cites`: `evidence:42cbced2d6495de4` -> `figure:acinetobacter_adp1_explorer:figures/growth_condition_correlation.png`
- `provenance_edge` `cites`: `evidence:4c893fc47311557c` -> `figure:acinetobacter_adp1_explorer:figures/gapfilling_impact.png`
- `provenance_edge` `cites`: `evidence:c3459b3f8a925fd2` -> `figure:acinetobacter_adp1_explorer:figures/data_coverage_by_modality.png`
- `provenance_edge` `cites`: `evidence:c42579f962551574` -> `figure:adp1_triple_essentiality:figures/fba_growth_concordance.png`
- `provenance_edge` `cites`: `evidence:cadf3bedb4bb73e8` -> `figure:adp1_deletion_phenotypes:figures/module_profiles.png`
- `provenance_edge` `cites`: `evidence:db383272ca8f0ceb` -> `figure:adp1_triple_essentiality:figures/roc_comprehensive.png`
- `provenance_edge` `cites`: `evidence:fe2c4a25cd8076da` -> `figure:adp1_deletion_phenotypes:figures/condition_clustermap.png`
- `provenance_edge` `extracted_from`: `evidence:154e2d833f5c98a7` -> `project:adp1_triple_essentiality`
- `provenance_edge` `extracted_from`: `evidence:154e2d833f5c98a7` -> `source_doc:adp1_triple_essentiality:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:154e2d833f5c98a7` -> `source_section:adp1_triple_essentiality:REPORT.md:Integrated Conclusions`
- `provenance_edge` `extracted_from`: `evidence:28856b6abc9a30ad` -> `project:acinetobacter_adp1_explorer`
- `provenance_edge` `extracted_from`: `evidence:28856b6abc9a30ad` -> `source_doc:acinetobacter_adp1_explorer:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:28856b6abc9a30ad` -> `source_section:acinetobacter_adp1_explorer:REPORT.md:Key Findings`
- `provenance_edge` `extracted_from`: `evidence:2e4026ebef8a4f47` -> `project:adp1_deletion_phenotypes`
- `provenance_edge` `extracted_from`: `evidence:2e4026ebef8a4f47` -> `source_doc:adp1_deletion_phenotypes:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:2e4026ebef8a4f47` -> `source_section:adp1_deletion_phenotypes:REPORT.md:Novel Contribution`
- `provenance_edge` `extracted_from`: `evidence:3a118ea8c0f0e2af` -> `project:adp1_deletion_phenotypes`
- `provenance_edge` `extracted_from`: `evidence:3a118ea8c0f0e2af` -> `source_doc:adp1_deletion_phenotypes:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:3a118ea8c0f0e2af` -> `source_section:adp1_deletion_phenotypes:REPORT.md:Key Findings`
- `provenance_edge` `extracted_from`: `evidence:3b0ff3cf4b39cb89` -> `project:acinetobacter_adp1_explorer`
- `provenance_edge` `extracted_from`: `evidence:3b0ff3cf4b39cb89` -> `source_doc:acinetobacter_adp1_explorer:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:3b0ff3cf4b39cb89` -> `source_section:acinetobacter_adp1_explorer:REPORT.md:Research Questions Answered`
- `provenance_edge` `extracted_from`: `evidence:3d4a1b8cec14598d` -> `project:adp1_triple_essentiality`
- `provenance_edge` `extracted_from`: `evidence:3d4a1b8cec14598d` -> `source_doc:adp1_triple_essentiality:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:3d4a1b8cec14598d` -> `source_section:adp1_triple_essentiality:REPORT.md:Key Findings`
- `provenance_edge` `extracted_from`: `evidence:42cbced2d6495de4` -> `project:acinetobacter_adp1_explorer`
- `provenance_edge` `extracted_from`: `evidence:42cbced2d6495de4` -> `source_doc:acinetobacter_adp1_explorer:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:42cbced2d6495de4` -> `source_section:acinetobacter_adp1_explorer:REPORT.md:Key Findings`
- `provenance_edge` `extracted_from`: `evidence:4c893fc47311557c` -> `project:acinetobacter_adp1_explorer`
- `provenance_edge` `extracted_from`: `evidence:4c893fc47311557c` -> `source_doc:acinetobacter_adp1_explorer:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:4c893fc47311557c` -> `source_section:acinetobacter_adp1_explorer:REPORT.md:Key Findings`
- `provenance_edge` `extracted_from`: `evidence:62105260d6569ebc` -> `project:adp1_triple_essentiality`
- `provenance_edge` `extracted_from`: `evidence:62105260d6569ebc` -> `source_doc:adp1_triple_essentiality:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:62105260d6569ebc` -> `source_section:adp1_triple_essentiality:REPORT.md:Recommendations`
- `provenance_edge` `extracted_from`: `evidence:6f38bdb5d36bbfa7` -> `project:acinetobacter_adp1_explorer`
- `provenance_edge` `extracted_from`: `evidence:6f38bdb5d36bbfa7` -> `source_doc:acinetobacter_adp1_explorer:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:6f38bdb5d36bbfa7` -> `source_section:acinetobacter_adp1_explorer:REPORT.md:Research Questions Answered`
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
- `provenance_edge` `extracted_from`: `evidence:cadf3bedb4bb73e8` -> `project:adp1_deletion_phenotypes`
- `provenance_edge` `extracted_from`: `evidence:cadf3bedb4bb73e8` -> `source_doc:adp1_deletion_phenotypes:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:cadf3bedb4bb73e8` -> `source_section:adp1_deletion_phenotypes:REPORT.md:Key Findings`
- `provenance_edge` `extracted_from`: `evidence:d44ad77070799add` -> `project:adp1_deletion_phenotypes`
- `provenance_edge` `extracted_from`: `evidence:d44ad77070799add` -> `source_doc:adp1_deletion_phenotypes:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:d44ad77070799add` -> `source_section:adp1_deletion_phenotypes:REPORT.md:Limitations`
- `provenance_edge` `extracted_from`: `evidence:d48ec4e4f428af68` -> `project:adp1_triple_essentiality`
- `provenance_edge` `extracted_from`: `evidence:d48ec4e4f428af68` -> `source_doc:adp1_triple_essentiality:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:d48ec4e4f428af68` -> `source_section:adp1_triple_essentiality:REPORT.md:Recommendations`
- `provenance_edge` `extracted_from`: `evidence:db383272ca8f0ceb` -> `project:adp1_triple_essentiality`
- `provenance_edge` `extracted_from`: `evidence:db383272ca8f0ceb` -> `source_doc:adp1_triple_essentiality:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:db383272ca8f0ceb` -> `source_section:adp1_triple_essentiality:REPORT.md:Integrated Discussion`
- `provenance_edge` `extracted_from`: `evidence:fe2c4a25cd8076da` -> `project:adp1_deletion_phenotypes`
- `provenance_edge` `extracted_from`: `evidence:fe2c4a25cd8076da` -> `source_doc:adp1_deletion_phenotypes:REPORT.md`
- `provenance_edge` `extracted_from`: `evidence:fe2c4a25cd8076da` -> `source_section:adp1_deletion_phenotypes:REPORT.md:Results`
- `provenance_edge` `has_evidence`: `stmt:adp1-deletion-carbon-tier-finding` -> `evidence:3a118ea8c0f0e2af`
- `provenance_edge` `has_evidence`: `stmt:adp1-deletion-condition-independence-finding` -> `evidence:fe2c4a25cd8076da`
- `provenance_edge` `has_evidence`: `stmt:adp1-deletion-continuum-claim` -> `evidence:2e4026ebef8a4f47`
- `provenance_edge` `has_evidence`: `stmt:adp1-deletion-expand-carbon-panel-opportunity` -> `evidence:d44ad77070799add`
- `provenance_edge` `has_evidence`: `stmt:adp1-deletion-quinate-module-finding` -> `evidence:cadf3bedb4bb73e8`
- `provenance_edge` `has_evidence`: `stmt:adp1-explorer-berdl-connectivity-finding` -> `evidence:28856b6abc9a30ad`
- `provenance_edge` `has_evidence`: `stmt:adp1-explorer-condition-fitness-finding` -> `evidence:42cbced2d6495de4`
- `provenance_edge` `has_evidence`: `stmt:adp1-explorer-database-bridge-claim` -> `evidence:c9ca6ed0aa39959b`
- `provenance_edge` `has_evidence`: `stmt:adp1-explorer-discordance-opportunity` -> `evidence:3b0ff3cf4b39cb89`
- `provenance_edge` `has_evidence`: `stmt:adp1-explorer-gapfilling-caveat` -> `evidence:4c893fc47311557c`
- `provenance_edge` `has_evidence`: `stmt:adp1-explorer-multiomics-finding` -> `evidence:c3459b3f8a925fd2`
- `provenance_edge` `has_evidence`: `stmt:adp1-explorer-pangenome-bridge-finding` -> `evidence:935d82e583994f8c`
- `provenance_edge` `has_evidence`: `stmt:adp1-explorer-urea-deep-dive-opportunity` -> `evidence:6f38bdb5d36bbfa7`
- `provenance_edge` `has_evidence`: `stmt:adp1-triple-aromatic-discordance-finding` -> `evidence:3d4a1b8cec14598d`
- `provenance_edge` `has_evidence`: `stmt:adp1-triple-aromatic-media-opportunity` -> `evidence:d48ec4e4f428af68`
- `provenance_edge` `has_evidence`: `stmt:adp1-triple-continuous-fitness-claim` -> `evidence:62105260d6569ebc`
- `provenance_edge` `has_evidence`: `stmt:adp1-triple-fba-growth-caveat` -> `evidence:c42579f962551574`
- `provenance_edge` `has_evidence`: `stmt:adp1-triple-fitness-predictor-finding` -> `evidence:db383272ca8f0ceb`
- `provenance_edge` `has_evidence`: `stmt:adp1-triple-proteomics-finding` -> `evidence:154e2d833f5c98a7`
- `provenance_edge` `uses_notebook`: `evidence:28856b6abc9a30ad` -> `notebook:acinetobacter_adp1_explorer:02_berdl_connection_scan.ipynb`
- `provenance_edge` `uses_notebook`: `evidence:2e4026ebef8a4f47` -> `notebook:adp1_deletion_phenotypes:03_gene_modules.ipynb`
- `provenance_edge` `uses_notebook`: `evidence:3a118ea8c0f0e2af` -> `notebook:adp1_deletion_phenotypes:01_data_extraction.ipynb`
- `provenance_edge` `uses_notebook`: `evidence:42cbced2d6495de4` -> `notebook:acinetobacter_adp1_explorer:04_gene_essentiality_and_fitness.ipynb`
- `provenance_edge` `uses_notebook`: `evidence:4c893fc47311557c` -> `notebook:acinetobacter_adp1_explorer:05_metabolic_model_and_phenotypes.ipynb`
- `provenance_edge` `uses_notebook`: `evidence:935d82e583994f8c` -> `notebook:acinetobacter_adp1_explorer:03_cluster_id_mapping.ipynb`
- `provenance_edge` `uses_notebook`: `evidence:c3459b3f8a925fd2` -> `notebook:acinetobacter_adp1_explorer:01_database_exploration.ipynb`
- `provenance_edge` `uses_notebook`: `evidence:cadf3bedb4bb73e8` -> `notebook:adp1_deletion_phenotypes:03_gene_modules.ipynb`
- `provenance_edge` `uses_notebook`: `evidence:db383272ca8f0ceb` -> `notebook:adp1_triple_essentiality:04_roc_analysis.ipynb`
- `provenance_edge` `uses_notebook`: `evidence:fe2c4a25cd8076da` -> `notebook:adp1_deletion_phenotypes:02_condition_structure.ipynb`
- `review_edge` `needs_review`: `stmt:adp1-deletion-expand-carbon-panel-opportunity` -> `stmt:adp1-deletion-continuum-claim`
- `review_edge` `needs_review`: `stmt:adp1-explorer-discordance-opportunity` -> `stmt:adp1-explorer-database-bridge-claim`
- `review_edge` `needs_review`: `stmt:adp1-explorer-urea-deep-dive-opportunity` -> `stmt:adp1-explorer-condition-fitness-finding`
- `review_edge` `needs_review`: `stmt:adp1-triple-aromatic-media-opportunity` -> `stmt:adp1-triple-continuous-fitness-claim`
- `scientific_edge` `motivates`: `stmt:adp1-deletion-condition-independence-finding` -> `stmt:adp1-deletion-expand-carbon-panel-opportunity`
- `scientific_edge` `motivates`: `stmt:adp1-deletion-continuum-claim` -> `stmt:adp1-deletion-expand-carbon-panel-opportunity`
- `scientific_edge` `motivates`: `stmt:adp1-deletion-quinate-module-finding` -> `stmt:adp1-deletion-expand-carbon-panel-opportunity`
- `scientific_edge` `motivates`: `stmt:adp1-explorer-condition-fitness-finding` -> `stmt:adp1-explorer-urea-deep-dive-opportunity`
- `scientific_edge` `motivates`: `stmt:adp1-explorer-database-bridge-claim` -> `stmt:adp1-explorer-discordance-opportunity`
- `scientific_edge` `motivates`: `stmt:adp1-explorer-gapfilling-caveat` -> `stmt:adp1-explorer-discordance-opportunity`
- `scientific_edge` `motivates`: `stmt:adp1-triple-aromatic-discordance-finding` -> `stmt:adp1-triple-aromatic-media-opportunity`
- `scientific_edge` `motivates`: `stmt:adp1-triple-continuous-fitness-claim` -> `stmt:adp1-triple-aromatic-media-opportunity`
- `scientific_edge` `motivates`: `stmt:adp1-triple-fba-growth-caveat` -> `stmt:adp1-triple-aromatic-media-opportunity`
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

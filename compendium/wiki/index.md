# State Of The Science

## Introduction

The ADP1 wiki now connects three projects: deletion phenotyping, the ADP1 data explorer, and triple-essentiality analysis. Together they describe a condition-dependent fitness landscape, the data infrastructure needed to navigate it, and model-quality limits that should guide follow-up work [stmt:adp1-deletion-continuum-claim; adp1_deletion_phenotypes] [stmt:adp1-explorer-database-bridge-claim; acinetobacter_adp1_explorer] [stmt:adp1-triple-continuous-fitness-claim; adp1_triple_essentiality].

The central synthesis is that ADP1 essentiality should be treated as quantitative and context-sensitive. Deletion phenotypes across eight carbon sources indicate multiple independent dimensions with quinate as a discrete exception, while triple-essentiality evidence argues for continuous fitness and orthogonal evidence over binary thresholds alone [stmt:adp1-deletion-condition-independence-finding; adp1_deletion_phenotypes] [stmt:adp1-deletion-quinate-module-finding; adp1_deletion_phenotypes] [stmt:adp1-triple-continuous-fitness-claim; adp1_triple_essentiality].

## Synthesis

[Topic: Adp1 Carbon Fitness](topics/adp1-carbon-fitness.md) is the scientific spine of the wiki. The deletion project contributes the carbon-tier and quinate-exception evidence, the explorer adds condition-specific fitness structure with urea and quinate as outliers, and the triple-essentiality project adds evidence that continuous fitness values outperform binary essentiality fractions [stmt:adp1-deletion-carbon-tier-finding; adp1_deletion_phenotypes] [stmt:adp1-explorer-condition-fitness-finding; acinetobacter_adp1_explorer] [stmt:adp1-triple-fitness-predictor-finding; adp1_triple_essentiality].

[Topic: Adp1 Data Integration](topics/adp1-data-integration.md) explains why the explorer matters beyond one project. It integrates six data modalities, maps BERDL pangenome clusters to ADP1-style cluster IDs, and connects strongly to BERDL through genomes, reactions, compounds, and pangenome clusters [stmt:adp1-explorer-multiomics-finding; acinetobacter_adp1_explorer] [stmt:adp1-explorer-pangenome-bridge-finding; acinetobacter_adp1_explorer] [stmt:adp1-explorer-berdl-connectivity-finding; acinetobacter_adp1_explorer].

[Topic: Adp1 Model Quality](topics/adp1-model-quality.md) carries the main caution. Heavy dependence on gapfilled reactions and weak FBA class prediction of TnSeq-dispensable growth defects mean model outputs should be used as refinement targets, not as final ground truth [stmt:adp1-explorer-gapfilling-caveat; acinetobacter_adp1_explorer] [stmt:adp1-triple-fba-growth-caveat; adp1_triple_essentiality].

The follow-up agenda is concrete: expand carbon-source phenotyping, prioritize FBA-TnSeq discordant genes, analyze urea-specific fitness genes as an independent module, and retest aromatic degradation after refining media definitions with trace aromatic compounds [stmt:adp1-deletion-expand-carbon-panel-opportunity; adp1_deletion_phenotypes] [stmt:adp1-explorer-discordance-opportunity; acinetobacter_adp1_explorer] [stmt:adp1-explorer-urea-deep-dive-opportunity; acinetobacter_adp1_explorer] [stmt:adp1-triple-aromatic-media-opportunity; adp1_triple_essentiality].

## Navigation Context

Start with the three topic pages, then use the project pages to inspect provenance: [Project: Adp1 Deletion Phenotypes](projects/adp1-deletion-phenotypes.md), [Project: Acinetobacter Adp1 Explorer](projects/acinetobacter-adp1-explorer.md), and [Project: Adp1 Triple Essentiality](projects/adp1-triple-essentiality.md). Use [Entity: Adp1](entities/adp1.md) for the organism-level view and entity pages for BERDL, FBA, quinate, urea, and aromatic degradation [stmt:adp1-explorer-database-bridge-claim; acinetobacter_adp1_explorer].

## Source Statements

- Carbon-fitness synthesis: `stmt:adp1-deletion-continuum-claim`, `stmt:adp1-triple-continuous-fitness-claim`, and condition-specific findings from deletion, explorer, and triple-essentiality projects [stmt:adp1-deletion-continuum-claim; adp1_deletion_phenotypes] [stmt:adp1-triple-continuous-fitness-claim; adp1_triple_essentiality] [stmt:adp1-explorer-condition-fitness-finding; acinetobacter_adp1_explorer].
- Data-integration synthesis: `stmt:adp1-explorer-database-bridge-claim`, `stmt:adp1-explorer-multiomics-finding`, `stmt:adp1-explorer-pangenome-bridge-finding`, and `stmt:adp1-explorer-berdl-connectivity-finding` [stmt:adp1-explorer-database-bridge-claim; acinetobacter_adp1_explorer] [stmt:adp1-explorer-multiomics-finding; acinetobacter_adp1_explorer].
- Model-quality synthesis: `stmt:adp1-explorer-gapfilling-caveat`, `stmt:adp1-triple-fba-growth-caveat`, `stmt:adp1-triple-aromatic-discordance-finding`, and related opportunities [stmt:adp1-explorer-gapfilling-caveat; acinetobacter_adp1_explorer] [stmt:adp1-triple-fba-growth-caveat; adp1_triple_essentiality] [stmt:adp1-triple-aromatic-media-opportunity; adp1_triple_essentiality].

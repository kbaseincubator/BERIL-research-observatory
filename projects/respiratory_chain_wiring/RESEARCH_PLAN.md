# Research Plan: Condition-Specific Respiratory Chain Wiring in ADP1

## Research Question
How is *Acinetobacter baylyi* ADP1's branched respiratory chain wired across carbon sources — which NADH dehydrogenases and terminal oxidases are required for which substrates, and does this explain why Complex I is specifically essential for aromatic catabolism?

## Hypothesis
- **H0**: Respiratory chain components are uniformly important across carbon sources — the apparent quinate-specificity of Complex I reflects assay artifacts or general respiratory stress, not substrate-specific wiring.
- **H1**: ADP1's respiratory chain is wired in a condition-dependent manner, with distinct NADH dehydrogenase and terminal oxidase configurations for different substrate classes. Complex I is specifically required for aromatic catabolism because the high NADH flux from the β-ketoadipate pathway exceeds the capacity of alternative NADH dehydrogenases (NDH-2).

## Literature Context
- **Melo & Teixeira (2016)** reviewed bacterial respiratory chain supramolecular organization, noting that most bacteria have branched respiratory chains with multiple NADH dehydrogenases (Complex I, NDH-2) and terminal oxidases (cytochrome bo, bd, cbb3, aa3).
- **Lencina et al. (2018)** showed that in *Streptococcus agalactiae*, NDH-2 is the only respiratory NADH dehydrogenase — organisms vary in which complexes they rely on.
- **Sena et al. (2024)** demonstrated that *Staphylococcus aureus* has two NDH-2 isoforms with distinct cellular roles, suggesting fine-tuned respiratory chain regulation.
- **Prior project (aromatic_catabolism_network)**: Identified 21 Complex I-associated genes as quinate-specific and showed via cross-species data that the dependency is on high-NADH-flux substrates (acetate, succinate show larger Complex I defects than some aromatics). Proposed NDH-2 compensation hypothesis.
- **Prior project (adp1_deletion_phenotypes)**: Growth data for 2,034 genes across 8 carbon sources provides the phenotypic matrix for this analysis.

### ADP1 Respiratory Chain Components (from genome_features)
| Component | Genes | Quinate growth | Glucose growth | Acetate growth |
|-----------|-------|---------------|----------------|----------------|
| Complex I (nuo) | 13 (ACIAD0730–0743) | ~0.25 (severe defect) | ~1.45 (no defect) | ~0.48 (defect) |
| NDH-2 | 1 (ACIAD_RS16420) | No data | No data | No data |
| ACIAD3522 (NADH-FMN OR) | 1 | 1.39 (fine) | 1.39 (fine) | 0.013 (lethal) |
| Cytochrome bo (cyo) | 4 (ACIAD2425–2428) | ~1.25 (fine) | ~0.94 (mild) | ~0.41 (defect) |
| Cytochrome bd (cyd-1) | 2 (ACIAD1749–1750) | ~1.49 (fine) | ~1.40 (fine) | ~0.71 (mild) |
| Cytochrome bd (cyd-2) | 1 (ACIAD2291) | 1.49 (fine) | 1.32 (fine) | 0.45 (defect) |

## Approach

### Aim 1: Complete Respiratory Chain Condition Map
**Goal**: Systematically extract all respiratory chain components and map their condition-dependent importance.

**Methods**:
- Query genome_features for all genes annotated as NADH dehydrogenases, quinone reductases, cytochrome oxidases, electron transport chain components, ATP synthase subunits
- Build a growth-ratio heatmap: respiratory component × 8 carbon sources
- Z-score normalize to identify condition-specific components
- Cluster respiratory components by their condition profiles — do they group by substrate class?

### Aim 2: NDH-2 Indirect Analysis
**Goal**: Characterize NDH-2 (ACIAD_RS16420) despite missing growth data.

**Methods**:
- **FBA predictions**: Query gene_phenotypes for NDH-2 across all 230 conditions. FBA predicts zero flux — why? Check if the model routes all NADH through Complex I.
- **Genomic context**: Map NDH-2's chromosomal neighborhood. Is it in an operon? Near any regulators?
- **Pangenome conservation**: NDH-2 is core (pangenome_is_core=1). Check whether it co-occurs with Complex I across Acinetobacter species using KO annotations (K03885 for NDH-2, K00330–K00343 for Complex I) via BERDL eggnog_mapper_annotations.
- **Ortholog-transferred fitness**: Query gene_phenotypes for NDH-2's fitness_match entries — do any FB organisms have NDH-2 fitness data on aromatic vs non-aromatic conditions?

### Aim 3: NADH/ATP Stoichiometry by Carbon Source
**Goal**: Test whether quinate produces more NADH per unit biomass than glucose, making Complex I's high-capacity NADH oxidation essential.

**Methods**:
- Extract FBA flux predictions for NADH-producing and NADH-consuming reactions across carbon sources from genome_reactions
- Calculate net NADH production per mole of carbon source entering the TCA cycle
- Compare Complex I flux (proton-pumping, 4 H⁺/NADH) vs NDH-2 flux (non-pumping) across conditions
- Key biochemistry: Complex I pumps 4 H⁺ per NADH oxidized, contributing to the proton motive force. NDH-2 oxidizes NADH without pumping protons — faster but energetically wasteful. The hypothesis: on quinate, the NADH load is so high that only Complex I's capacity suffices; on glucose, NDH-2's capacity is adequate.

### Aim 4: Cross-Species Respiratory Architecture
**Goal**: Test whether the Complex I/aromatic dependency correlates with respiratory chain architecture across FB organisms.

**Methods**:
- Query FB `experiment` table for experiments with aromatic substrates (benzoate, 4-HBA, protocatechuate, vanillin, quinate) across all 48 organisms. Identify which organisms have aromatic fitness data.
- For organisms with aromatic data: extract Complex I (nuo) and NDH-2 (ndh) gene fitness scores on aromatic vs non-aromatic conditions
- Classify FB organisms by respiratory chain architecture: does the organism have both Complex I and NDH-2, or only one?
- Test: do organisms with ONLY Complex I (no NDH-2) show Complex I essentiality on ALL carbon sources (no compensation possible)?
- Note: Requires Spark queries on BERDL for FB genefitness and experiment tables. Use `get_spark_session()` on JupyterHub or local Spark Connect.

## Query Strategy

### Tables Required
| Table | Purpose | Estimated Rows | Filter Strategy |
|---|---|---|---|
| `genome_features` (SQLite) | Growth data, respiratory gene annotations | 5,852 | Keyword search on rast_function |
| `gene_phenotypes` (SQLite) | FBA predictions for NDH-2 and respiratory genes | 239,584 | Filter by gene_id |
| `gene_reaction_data` (SQLite) | NADH reaction mappings | varies | Filter by reaction keywords |
| `genome_reactions` (SQLite) | Full reaction equations for stoichiometry | varies | Filter by NADH/NAD in equation |
| `kescience_fitnessbrowser.experiment` (BERDL) | Find aromatic experiments | 7,552 | Filter by condition/expGroup |
| `kescience_fitnessbrowser.genefitness` (BERDL) | nuo/ndh fitness on aromatics | 27M | Filter by orgId + expName |
| `kescience_fitnessbrowser.gene` (BERDL) | Identify nuo/ndh genes per organism | 228K | Filter by orgId + desc |
| `kbase_ke_pangenome.eggnog_mapper_annotations` (BERDL) | NDH-2/Complex I KO co-occurrence | 93M | Filter by KEGG_ko |

### Performance Plan
- **Execution environment**: Local machine for SQLite analysis (NB01–03); BERDL JupyterHub or local Spark Connect for FB and pangenome queries (NB04)
- **Known pitfalls**: FB all-string columns require CAST; gene clusters are species-specific (use KOs for cross-species); genefitness filter by orgId
- **Spark import**: On JupyterHub: `spark = get_spark_session()` (no import). Locally: `from get_spark_session import get_spark_session`

## Analysis Plan

### Notebook 1: Respiratory Chain Condition Map
- **Goal**: Extract all respiratory components, build condition × component heatmap
- **Expected output**: `data/respiratory_chain_genes.csv`, heatmap figure, condition-specificity scores

### Notebook 2: NDH-2 Indirect Analysis
- **Goal**: Characterize NDH-2 via FBA, genomic context, pangenome, and ortholog fitness
- **Expected output**: `data/ndh2_analysis.csv`, genomic context figure

### Notebook 3: NADH/ATP Stoichiometry
- **Goal**: Calculate NADH balance per carbon source from FBA model
- **Expected output**: `data/nadh_stoichiometry.csv`, NADH balance figure

### Notebook 4: Cross-Species Respiratory Architecture (if data available)
- **Goal**: Test Complex I/NDH-2 architecture effects across FB organisms on aromatics
- **Expected output**: `data/cross_species_respiratory.csv`, architecture comparison figure

## Expected Outcomes
- **If H1 supported**: The respiratory chain shows clear condition-dependent wiring: Complex I dominates on quinate/aromatics, cytochrome bo is required for acetate/lactate, and NDH-2 (inferred) provides backup on glucose. The NADH stoichiometry shows quinate produces significantly more NADH per biomass unit, explaining the Complex I bottleneck.
- **If H0 not rejected**: Respiratory components show similar importance across all conditions — the apparent condition-specificity is an artifact of growth ratio normalization or reflects general aerobic fitness rather than substrate-specific wiring.
- **Potential confounders**:
  - Growth ratio differences across conditions may compress or expand the scale of respiratory defects
  - NDH-2 has no growth data — all NDH-2 conclusions are indirect
  - The FBA model may not accurately represent the branching point between Complex I and NDH-2
  - Cytochrome bo defects on acetate may reflect a shared regulatory pathway, not direct respiratory requirement

## Revision History
- **v1** (2026-02-19): Initial plan

## Authors
- Paramvir Dehal (ORCID: 0000-0001-5810-2497), Lawrence Berkeley National Laboratory

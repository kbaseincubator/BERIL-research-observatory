# Research Plan: Microbiome Grammar -- Environmental Rules for Microbial Community Design

## Research Question

What environmental-to-microbe association rules can we extract from linked metagenomic, isolate, and geochemistry data across BERDL, and can those rules power a predictive framework that designs fit-for-purpose microbial assemblages given user-specified environmental constraints (e.g., pH, metals, nutrients)?

## Hypotheses

- **H0**: Environmental parameters (geochemistry, pH, nutrients) are not predictive of microbial community composition or functional potential beyond broad ecosystem type.
- **H1**: Quantitative environmental parameters significantly predict both which microbial taxa are present and what metabolic functions they encode, enabling rule-based community design for target applications.

### Sub-hypotheses

- **H1a**: Co-occurrence of specific taxa with specific geochemical conditions (e.g., rare earth elements, nitrate) is non-random and reproducible across sampling events.
- **H1b**: GapMind pathway completeness profiles of environmentally-associated taxa predict their functional suitability for target applications (metal recovery, denitrification).
- **H1c**: Multi-organism assemblages designed from environmental association rules outperform single-organism selections in predicted pathway coverage for complex tasks.

## Literature Context

*To be updated after literature review completes.*

## Data Sources

### Primary: Environmental Sample-Microbe Linkages

| Database | Linkage Type | Scale | Key Tables |
|----------|-------------|-------|------------|
| `enigma_coral` | Geochemistry -> 16S communities + isolated genomes | 596 locations, 4,346 samples, 213K ASVs, 6,705 genomes | `sdt_location`, `sdt_sample`, `sdt_community`, `ddt_brick0000459` (ASV abundances), `ddt_brick0000454` (taxonomy), `ddt_brick0000010` (geochemistry: 48 chemical species incl. 13 REEs) |
| `nmdc_arkin` | Abiotic parameters -> metagenomics + metabolomics | 48 studies, 3M+ metabolomics records | `abiotic_features` (pH, temp, nutrients, metals), `taxonomy_features`, `metabolomics_gold`, `annotation_terms_unified` |
| `kbase_ke_pangenome` | Environmental metadata -> 293K genomes | 83K genomes with AlphaEarth embeddings, 4.1M NCBI env records | `ncbi_env`, `alphaearth_embeddings_all_years`, `sample` |
| `planetmicrobe_planetmicrobe` | Marine samples -> metagenomics | 2K samples, 6K experiments | Campaign and sample metadata |

### Secondary: Functional Prediction Resources

| Database | What it Provides | Scale |
|----------|-----------------|-------|
| `kbase_ke_pangenome` (GapMind) | Pathway completeness per genome | 305M pathway records for 293K genomes |
| `kbase_ke_pangenome` (eggNOG) | COG/KEGG/EC/Pfam annotations per gene cluster | 93M annotation records |
| `kescience_fitnessbrowser` | Experimentally-validated gene importance under metal/nitrogen stress | 559 metal experiments, 48 organisms |
| `kescience_bacdive` | Growth conditions, metabolite utilization, isolation source | 97K strains, 988K metabolite tests |
| `kescience_webofmicrobes` | Exometabolomics (what organisms consume/produce) | 37 organisms, 589 metabolites |
| `kbase_msd_biochemistry` | Reaction stoichiometry for metabolic modeling | 56K reactions, 46K molecules |

### Previously Generated (Observatory Projects)

| Project | Reusable Asset |
|---------|---------------|
| `metal_fitness_atlas` | 1,182 conserved metal gene families, metal tolerance scores |
| `enigma_contamination_functional_potential` | ENIGMA community-function linkage pipeline |
| `nmdc_community_metabolic_ecology` | NMDC community-weighted pathway completeness scores |
| `env_embedding_explorer` | AlphaEarth embedding structure and environment label mapping |
| `lab_field_ecology` | Lab fitness -> field ecology prediction framework |
| `cf_formulation_design` | Multi-criterion assemblage optimization framework |

## Query Strategy

### Tables Required

| Table | Purpose | Estimated Rows | Filter Strategy |
|-------|---------|----------------|-----------------|
| `enigma_coral.sdt_location` | Field site metadata | 596 | Full scan OK |
| `enigma_coral.sdt_sample` | Sample-location links | 4,346 | Full scan OK |
| `enigma_coral.sdt_community` | Community-sample links | 2,209 | Full scan OK |
| `enigma_coral.ddt_brick0000459` | ASV abundance matrix | 868K | Filter by community |
| `enigma_coral.ddt_brick0000454` | ASV taxonomy | 627K | Filter by ASV + level |
| `enigma_coral.ddt_brick0000010` | Geochemistry | 52,884 | Filter by molecule |
| `enigma_coral.sdt_strain` | Isolate strain info | 3,154 | Full scan OK |
| `enigma_coral.sdt_genome` | Isolate genomes | 6,705 | Full scan OK |
| `nmdc_arkin.abiotic_features` | Environmental parameters | ~5K | Full scan OK |
| `nmdc_arkin.metabolomics_gold` | Community metabolomics | 3M+ | Filter by sample |
| `kbase_ke_pangenome.gapmind_pathways` | Pathway predictions | 305M | Filter by genome_id |
| `kbase_ke_pangenome.ncbi_env` | Environment metadata | 4.1M | Filter by accession |
| `kbase_ke_pangenome.eggnog_mapper_annotations` | Functional annotations | 93M | Filter by gene_cluster_id |
| `kescience_fitnessbrowser.fitness` | Experimental fitness scores | 27M | Filter by organism + condition |
| `kescience_bacdive.culture_medium` | Growth conditions | varies | Full scan OK |

### Performance Plan

- **Tier**: Mixed -- REST API for small tables, JupyterHub Spark for large joins
- **Estimated complexity**: Complex (multi-database, large-scale aggregation)
- **Known pitfalls**: ENIGMA taxonomy only goes to Genus (no species); NMDC abiotic values may be normalized (check units); AlphaEarth covers only 28% of genomes; gene clusters are species-specific

## Analysis Plan

### Phase 1: Data Inventory & Integration (NB01-NB03)

#### Notebook 01: ENIGMA Environmental-Microbe Census
- **Goal**: Build the complete linkage table: Location -> Sample -> Geochemistry + Community -> ASV taxonomy
- **Key questions**: How many samples have BOTH geochemistry AND community profiles? What is the coverage of each chemical species? What taxonomic resolution is available?
- **Expected output**: `data/enigma_sample_geochem_community.parquet`, coverage summary figures

#### Notebook 02: NMDC Environmental-Microbe Census
- **Goal**: Build the NMDC linkage table: Sample -> Abiotic features + Taxonomy + Metabolomics
- **Key questions**: How many samples have environmental parameters AND taxonomic profiles? What ecosystems are represented? What is pH/nutrient coverage?
- **Expected output**: `data/nmdc_sample_abiotic_taxonomy.parquet`, ecosystem distribution figures

#### Notebook 03: Pangenome Environmental Metadata Census
- **Goal**: Characterize NCBI_env coverage, AlphaEarth embedding coverage, and BacDive isolation source coverage across 293K genomes
- **Key questions**: What fraction of genomes have usable environmental metadata? What environments are most/least represented?
- **Expected output**: `data/pangenome_env_coverage.parquet`, metadata completeness figures

### Phase 2: Association Rule Mining (NB04-NB06)

#### Notebook 04: ENIGMA Geochemistry-Taxon Associations
- **Goal**: Test whether specific taxa associate with specific geochemical conditions (metals, nitrate, etc.)
- **Method**: For each chemical species x taxonomic group combination, compute enrichment statistics (Fisher's exact, Spearman correlation with concentration)
- **Expected output**: `data/enigma_geochem_taxon_associations.csv`, heatmaps

#### Notebook 05: Cross-Database Environmental Rules
- **Goal**: Synthesize environmental association rules across ENIGMA + NMDC + pangenome metadata
- **Method**: Train random forest / gradient boosting models predicting taxon presence from environmental parameters; extract feature importances
- **Expected output**: `data/environmental_association_rules.csv`, feature importance plots

#### Notebook 06: Functional Capability Mapping
- **Goal**: For taxa with environmental associations, map their functional capabilities using GapMind + eggNOG + Fitness Browser
- **Method**: Join associated taxa -> pangenome species -> GapMind pathways + functional annotations. Focus on: (a) nitrogen cycling pathways, (b) metal tolerance/metabolism, (c) carbon utilization
- **Expected output**: `data/taxon_functional_capabilities.csv`, pathway completeness matrices

### Phase 3: Assemblage Design Framework (NB07-NB09)

#### Notebook 07: Assemblage Optimization Engine
- **Goal**: Build the core optimization framework that designs multi-organism assemblages for target conditions
- **Method**: Adapt the CF formulation design optimization approach: given target environmental conditions + desired functions, score candidate organisms on (a) environmental fitness, (b) functional coverage, (c) complementarity, (d) compatibility
- **Expected output**: `src/assemblage_optimizer.py`, validation against known communities

#### Notebook 08: Use Case 1 -- Rare Earth Metal Recovery
- **Goal**: Design assemblages for REE biorecovery at pH 6.5 with 5 mM nitrate
- **Method**: Query ENIGMA samples with REE presence + similar conditions, identify associated taxa, predict functional capabilities, optimize assemblage
- **Expected output**: Ranked assemblage recommendations with predicted performance

#### Notebook 09: Use Case 2 -- Complete Denitrification
- **Goal**: Given a metagenome composition, identify which organisms contribute denitrification steps and predict N2 loss
- **Method**: Map metagenome taxa to denitrification pathway genes (narG, napA, nirS, nirK, norB, nosZ), identify pathway hand-offs between organisms, flag incomplete communities
- **Expected output**: Denitrification pathway coverage analysis, interaction predictions

### Phase 4: Validation & Synthesis (NB10)

#### Notebook 10: Validation Against Known Communities
- **Goal**: Validate predictions against held-out data and known community behaviors
- **Method**: Leave-one-out cross-validation on ENIGMA communities; compare predicted vs observed taxa at held-out sites; benchmark against Fitness Browser experimental data
- **Expected output**: Validation metrics, comparison figures

## Expected Outcomes

- **If H1 supported**: Environmental parameters predict community composition beyond chance, and the assemblage design framework produces biologically plausible recommendations. This creates a queryable "microbiome grammar" linking conditions to organisms to functions.
- **If H0 not rejected**: Environmental parameters alone are insufficient -- stochastic processes, historical contingency, or unmeasured variables dominate. The project still delivers a comprehensive inventory of environmental-microbe linkage data in BERDL.
- **Potential confounders**: Spatial autocorrelation in ENIGMA data (nearby wells are not independent); taxonomic resolution limited to genus in ENIGMA 16S; survivorship bias in cultured isolates vs metagenome-detected taxa.

## Revision History

- **v1** (2026-03-30): Initial plan based on BERDL data exploration

## Authors

- Adam Arkin (ORCID: [0000-0002-4999-2931](https://orcid.org/0000-0002-4999-2931)) -- U.C. Berkeley / Lawrence Berkeley National Laboratory

# Research Plan: BacDive Phenotype Signatures of Metal Tolerance

## Research Question
Can BacDive-measured bacterial phenotypes (Gram stain, oxygen tolerance, metabolite utilization profiles, enzyme activities) predict metal tolerance as measured by Fitness Browser RB-TnSeq experiments and the Metal Fitness Atlas genome-based predictions?

## Hypothesis
- **H0**: BacDive phenotypic traits do not predict metal tolerance beyond what is expected from phylogenetic relatedness alone.
- **H1**: Specific BacDive phenotypes — particularly oxygen tolerance, Gram stain, metabolite utilization breadth, and redox enzyme activities — are significant predictors of metal tolerance, even after controlling for phylogeny.

### Sub-hypotheses
- **H1a**: Gram-negative bacteria show higher metal tolerance scores than Gram-positive bacteria (outer membrane acts as permeability barrier; Giovanella et al. 2017).
- **H1b**: Anaerobes and facultative anaerobes show higher tolerance to redox-active metals (Cu, Cr, U, Fe) due to dissimilatory metal reduction (Lovley 1993; Wang et al. 2018).
- **H1c**: Metabolite utilization breadth (number of positive BacDive metabolite tests) positively correlates with metal tolerance score (metabolic versatility co-occurs with metal resistance gene clusters; Martin-Moldes et al. 2015).
- **H1d**: Catalase-positive organisms show higher tolerance to redox-cycling metals (Cu, Cr, Fe) via ROS detoxification.
- **H1e**: Urease-positive organisms show higher nickel tolerance (urease is a nickel-dependent enzyme; urease-positive organisms have nickel import/handling machinery).
- **H1f**: H₂S-producing organisms (sulfate/thiosulfate reducers) show higher tolerance to chalcophilic metals (Zn, Cu, Cd, Pb) via metal sulfide precipitation.

## Literature Context
- **Cell wall architecture determines metal binding**: Gram-positive bacteria accumulate higher metal concentrations on their thicker peptidoglycan layer (Biswas et al. 2021), but Gram-negative outer membranes provide a permeability barrier and distinct efflux mechanisms (Giovanella et al. 2017; Abou-Shanab 2007).
- **Redox metabolism links to metal fate**: Anaerobes can use metals as terminal electron acceptors (Fe³⁺, Mn⁴⁺, U⁶⁺, Cr⁶⁺), precipitate metals as sulfides, and transform metal redox states (Lovley 1993; Wang et al. 2018; Meng et al. 2019).
- **Metabolic versatility predicts resistance gene repertoire**: Bacteria with broader metabolic capabilities harbor more metal resistance gene clusters (Martin-Moldes et al. 2015; Nnaji et al. 2024).
- **BacDive ML precedent**: Koblitz et al. (2025) demonstrated ML prediction of 8 physiological traits from Pfam profiles using BacDive data (Communications Biology). Same framework applicable to metal tolerance.
- **Gap**: No study has used a comprehensive suite of phenotypic traits (Gram + oxygen + metabolites + enzymes) to predict metal tolerance across diverse bacteria. This project fills that gap using BacDive × Fitness Browser/Metal Fitness Atlas integration.

## Approach

### Two-scale design
1. **Direct validation (n=12)**: 12 Fitness Browser organisms match BacDive strains by NCBI taxonomy ID. Compare BacDive phenotypes against actual per-metal fitness profiles.
2. **Pangenome-scale prediction (n≈3,000-5,000)**: Link BacDive strains to pangenome species via genome accessions (27,502 GCA accessions). Test phenotype → metal tolerance score (from Metal Fitness Atlas) associations across thousands of species.

### Phenotype feature matrix
| Feature | Source | Coverage | Type |
|---------|--------|----------|------|
| Gram stain | `physiology.gram_stain` | 15,296 strains | Binary (neg/pos) |
| Oxygen tolerance | `physiology.oxygen_tolerance` | 23,252 strains | Categorical (5 levels) |
| Cell shape | `physiology.cell_shape` | 14,990 strains | Categorical |
| Motility | `physiology.motility` | 13,759 strains | Binary |
| Catalase activity | `enzyme` (catalase) | 16,907 tests | Binary (+/-) |
| Oxidase activity | `enzyme` (oxidase) | 17,723 tests | Binary (+/-) |
| Urease activity | `enzyme` (urease) | 30,875 tests | Binary (+/-) |
| Nitrate reduction | `metabolite_utilization` (nitrate) | 27,388 tests | Binary (+/-) |
| H₂S production | `metabolite_utilization` (H₂S) | 5,322 tests | Binary (produced/not) |
| Acetate utilization | `metabolite_utilization` (acetate) | 2,199 tests | Binary (+/-) |
| Metabolite breadth | `metabolite_utilization` | 988K tests | Continuous (count of + results) |
| Enzyme breadth | `enzyme` | 643K tests | Continuous (count of + results) |
| Isolation source | `isolation.cat1` | 57,935 strains | Categorical (#Host/#Environmental/#Engineered) |

### Metal tolerance metrics
- **Composite**: Metal Fitness Atlas `metal_score_norm` (27,702 pangenome species)
- **Per-metal**: Fitness scores from 14 metals across 12 FB-BacDive matched organisms

## Query Strategy

### Tables Required
| Table | Purpose | Estimated Rows | Filter Strategy |
|---|---|---|---|
| `kescience_bacdive.strain` | Core strain metadata + taxid | 97K | Full scan OK |
| `kescience_bacdive.physiology` | Gram, oxygen, motility | 97K | Full scan OK |
| `kescience_bacdive.metabolite_utilization` | Anion metabolism, breadth | 988K | Full scan OK |
| `kescience_bacdive.enzyme` | Catalase, oxidase, urease | 643K | Full scan OK |
| `kescience_bacdive.isolation` | Isolation source categories | 58K | Full scan OK |
| `kescience_bacdive.sequence_info` | Genome accessions for pangenome link | 81K | Filter accession_type='genome' |
| `kescience_bacdive.taxonomy` | Taxonomic classification for phylo control | 97K | Full scan OK |

All BacDive data is already ingested locally in `data/bacdive_ingest/`. No Spark queries needed for BacDive tables.

The Metal Fitness Atlas species scores are cached at `projects/metal_fitness_atlas/data/species_metal_scores.csv` (27,702 rows).

### Performance Plan
- **Tier**: Local analysis (all data cached)
- **Estimated complexity**: Moderate (feature engineering + statistical modeling)
- **Known pitfalls**:
  - BacDive genome accessions (GCA_*) need prefix matching to pangenome IDs (GB_GCA_* or RS_GCF_*)
  - Phenotype coverage is sparse — need to handle missing data carefully
  - Phylogenetic confounding: many phenotypes are phylogenetically conserved → must control for taxonomy

## Analysis Plan

### Notebook 1: BacDive-Pangenome Bridge
- **Goal**: Link BacDive strains to pangenome species via genome accessions
- **Method**: Match `sequence_info.accession` (GCA_*) to pangenome `genome.genome_id` using prefix adjustment
- **Expected output**: Bridge table mapping bacdive_id → gtdb_species_clade_id
- **Reuse**: Leverage approach from `projects/bacdive_metal_validation/` (which already solved the GCA matching)

### Notebook 2: Phenotype Feature Engineering
- **Goal**: Build a species-level phenotype feature matrix from BacDive data
- **Method**:
  - Aggregate strain-level phenotypes to species level (majority vote for categorical, fraction positive for continuous)
  - Compute metabolite utilization breadth and enzyme activity breadth
  - Extract key binary features: Gram, catalase, oxidase, urease, nitrate reduction, H₂S production
  - Handle missing data (report coverage per feature, use only complete cases or imputation)
- **Expected output**: Species × phenotype matrix (~3,000-5,000 species with ≥1 phenotype)

### Notebook 3: Univariate Phenotype-Metal Associations
- **Goal**: Test each phenotype feature individually against metal tolerance score
- **Method**:
  - For binary features: Mann-Whitney U or Welch's t-test comparing metal scores between groups
  - For continuous features: Spearman correlation with metal tolerance score
  - Effect sizes (Cohen's d, r) and multiple testing correction (BH-FDR)
  - Stratify by phylum to check for phylogenetic confounding
- **Expected output**: Association table with effect sizes, p-values, and phylum-stratified results

### Notebook 4: Multivariate Prediction Model
- **Goal**: Build a predictive model from multiple phenotype features
- **Method**:
  - Random forest or gradient boosting (XGBoost) predicting metal_score_norm from phenotype features
  - Cross-validation (5-fold) with phylogenetic blocking (no species from same genus in train+test)
  - Feature importance analysis (SHAP values)
  - Compare to phylogeny-only baseline (phylum/class/order as features)
  - Test: does adding phenotype features improve prediction beyond taxonomy alone?
- **Expected output**: Model performance metrics, feature importance ranking, comparison to phylogenetic baseline

### Notebook 5: Direct FB-BacDive Validation
- **Goal**: For the 12 FB organisms matching BacDive, compare BacDive phenotypes to actual per-metal fitness profiles
- **Method**:
  - Extract BacDive phenotypes for the 12 matched organisms
  - For each organism × metal pair: correlate phenotype features with fitness importance (number of metal-important genes, mean fitness effect)
  - Case studies: Does DvH's anaerobic metabolism predict its uranium tolerance? Does urease activity predict nickel fitness?
- **Expected output**: Organism × phenotype × metal concordance table, case study narratives

## Expected Outcomes
- **If H1 supported**: BacDive phenotypes capture real biological predictors of metal tolerance, enabling phenotype-based screening of metal-tolerant organisms from culture collections. Specific mechanisms (Gram-negative barrier, anaerobic metal reduction, sulfide precipitation) validated at genomic scale.
- **If H0 not rejected**: Metal tolerance is primarily determined by specific resistance gene clusters rather than broad physiological phenotypes; phenotypic traits are too phylogenetically confounded to add predictive power beyond taxonomy.
- **Potential confounders**:
  - Phylogenetic autocorrelation (Gram stain, oxygen tolerance, etc. are phylogenetically conserved)
  - BacDive testing bias (well-studied organisms have more phenotype data)
  - Metal Fitness Atlas scores are genome-based predictions, not direct measurements (circular reasoning risk if both use same genomic features)

## Revision History
- **v1** (2026-03-10): Initial plan

## Authors
- Paramvir Dehal (https://orcid.org/0000-0002-3495-1240), Lawrence Berkeley National Laboratory, US Department of Energy

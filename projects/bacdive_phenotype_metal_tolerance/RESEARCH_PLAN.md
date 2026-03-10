# Research Plan: BacDive Phenotype Signatures of Metal Tolerance

## Research Question
Can BacDive-measured bacterial phenotypes (Gram stain, oxygen tolerance, metabolite utilization profiles, enzyme activities) predict metal tolerance as measured by Fitness Browser RB-TnSeq experiments and the Metal Fitness Atlas genome-based predictions?

## Hypothesis
- **H0**: BacDive phenotypic traits do not predict metal tolerance beyond what is expected from phylogenetic relatedness alone.
- **H1**: Specific BacDive phenotypes — particularly oxygen tolerance, Gram stain, metabolite utilization breadth, and redox enzyme activities — are significant predictors of metal tolerance, even after controlling for phylogeny.

### Sub-hypotheses
- **H1a**: Gram-negative bacteria show higher metal tolerance scores than Gram-positive bacteria (outer membrane acts as permeability barrier; Giovanella et al. 2017).
- **H1b**: Anaerobes and facultative anaerobes show higher tolerance to redox-active metals (Cu, Cr, U, Fe) due to dissimilatory metal reduction (Lovley 1993; Wang et al. 2018). Test against **metal-specific** genes (from `counter_ion_effects` corrected scores) to avoid shared-stress confounding.
- **H1c**: Metabolite utilization breadth (number of positive BacDive metabolite tests) positively correlates with metal tolerance score (metabolic versatility co-occurs with metal resistance gene clusters; Martin-Moldes et al. 2015).
- **H1d**: Catalase-positive organisms show higher tolerance to redox-cycling metals (Cu, Cr, Fe) via ROS detoxification. Test against metal-specific genes to separate from general stress response.
- **H1e**: Urease-positive organisms show higher nickel tolerance (urease is a nickel-dependent enzyme; urease-positive organisms have nickel import/handling machinery).
- **H1f**: H₂S-producing organisms (sulfate/thiosulfate reducers) show higher tolerance to chalcophilic metals (Zn, Cu, Cd, Pb) via metal sulfide precipitation.

### Expected effect sizes
The `bacdive_metal_validation` project found Cohen's d = +1.00 for isolation source (heavy metal contamination → metal tolerance score). BacDive phenotypes are less directly related to metal tolerance than isolation from metal-contaminated environments, so we expect moderate effect sizes:
- Gram stain, oxygen tolerance: d = 0.2–0.5 (small to moderate)
- Urease/H₂S (mechanistically specific): d = 0.3–0.7 (moderate)
- Metabolite breadth (indirect proxy): r = 0.1–0.3 (weak to moderate)

## Literature Context
- **Cell wall architecture determines metal binding**: Gram-positive bacteria accumulate higher metal concentrations on their thicker peptidoglycan layer (Biswas et al. 2021), but Gram-negative outer membranes provide a permeability barrier and distinct efflux mechanisms (Giovanella et al. 2017; Abou-Shanab 2007).
- **Redox metabolism links to metal fate**: Anaerobes can use metals as terminal electron acceptors (Fe³⁺, Mn⁴⁺, U⁶⁺, Cr⁶⁺), precipitate metals as sulfides, and transform metal redox states (Lovley 1993; Wang et al. 2018; Meng et al. 2019).
- **Metabolic versatility predicts resistance gene repertoire**: Bacteria with broader metabolic capabilities harbor more metal resistance gene clusters (Martin-Moldes et al. 2015; Nnaji et al. 2024).
- **BacDive ML precedent**: Koblitz et al. (2025) demonstrated ML prediction of 8 physiological traits from Pfam profiles using BacDive data (Communications Biology). Same framework applicable to metal tolerance.
- **Gap**: No study has used a comprehensive suite of phenotypic traits (Gram + oxygen + metabolites + enzymes) to predict metal tolerance across diverse bacteria. This project fills that gap using BacDive × Fitness Browser/Metal Fitness Atlas integration.

## Approach

### Two-scale design
1. **Direct validation (n=12)**: 12 Fitness Browser organisms match BacDive strains by NCBI taxonomy ID (species-level match, not strain-level — see Caveats). Present as **descriptive case studies**, not formal hypothesis tests, given the low n.
2. **Pangenome-scale prediction (n≈TBD)**: Link BacDive strains to pangenome species via genome accessions (27,502 GCA accessions). Test phenotype → metal tolerance score (from Metal Fitness Atlas) associations. **Actual post-matching sample size must be computed in NB01 before proceeding** — estimate 3,000-5,000 species but this is unverified.

### Phenotype feature matrix

**Value encoding rules** (addresses four-value utilization and non-binary enzyme activity):
- `metabolite_utilization.utilization`: Map `+` → positive, `-` → negative, `produced` → positive, `+/-` → exclude (ambiguous). Filter to explicit +/- before computing utilization percentages.
- `enzyme.activity`: Map `+` → positive, `-` → negative, `+/-` → exclude (ambiguous). Other values (e.g., "variable") also excluded.
- `physiology` fields: Use **measured values only** (`gram_stain`, `oxygen_tolerance`, `motility`). Do NOT fill gaps with AI-predicted columns (`predicted_gram`, `predicted_motility`, `predicted_oxygen`). Predicted values could introduce model-dependent bias, especially if the prediction models used genomic features correlated with metal tolerance.

| Feature | Source | Strain Coverage | Type | Encoding |
|---------|--------|-----------------|------|----------|
| Gram stain | `physiology.gram_stain` | 15,296 strains | Binary | negative/positive (exclude "variable") |
| Oxygen tolerance | `physiology.oxygen_tolerance` | 23,252 strains | Categorical (5 levels) | aerobe/anaerobe/microaerophile/facultative/obligate |
| Cell shape | `physiology.cell_shape` | 14,990 strains | Categorical | Top 5 shapes; others → "other" |
| Motility | `physiology.motility` | 13,759 strains | Binary | yes/no |
| Catalase activity | `enzyme` (catalase) | 16,907 tests | Binary | +/- only |
| Oxidase activity | `enzyme` (oxidase) | 17,723 tests | Binary | +/- only |
| Urease activity | `enzyme` (urease) | 30,875 tests | Binary | +/- only |
| Nitrate reduction | `metabolite_utilization` (nitrate) | 27,388 tests | Binary | +/- only (exclude +/-) |
| H₂S production | `metabolite_utilization` (H₂S) | 5,322 tests | Binary | "produced" → positive; else negative |
| Acetate utilization | `metabolite_utilization` (acetate) | 2,199 tests | Binary | +/- only |
| Metabolite breadth | `metabolite_utilization` | 988K tests | Continuous | Count of explicit "+" results per strain |
| Enzyme breadth | `enzyme` | 643K tests | Continuous | Count of explicit "+" results per strain |
| Isolation source | `isolation.cat1` | 57,935 strains | Categorical | #Host/#Environmental/#Engineered |

### Species-level aggregation
- **Categorical features** (Gram, oxygen): Majority vote with **agreement score** (fraction of strains with majority call). Species with agreement < 0.6 flagged as "variable" and analyzed separately.
- **Binary features** (catalase, urease, etc.): Fraction positive across strains. Binarize at species level using 0.5 threshold, but retain continuous fraction for sensitivity analysis.
- **Continuous features** (breadth): Mean across strains within species.

### Metal tolerance metrics
- **Composite**: Metal Fitness Atlas `metal_score_norm` (27,702 pangenome species)
- **Per-metal corrected**: Use metal-specific gene counts from `counter_ion_effects/data/corrected_metal_conservation.csv` where available, to test H1b/H1d against metal-specific (not shared-stress) signal
- **Per-metal direct**: Fitness scores from 14 metals across 12 FB-BacDive matched organisms

### Circular reasoning mitigation
The Metal Fitness Atlas `metal_score_norm` is derived from gene functional signatures (COG/KEGG/SEED/domain annotations in pangenome clusters). If BacDive phenotypes are phylogenetically correlated with the same functional signatures, associations could be indirect. Mitigation strategies:
1. **Control for metal resistance gene count**: Include `n_metal_clusters` from the atlas as a covariate. If phenotypes predict metal tolerance *beyond* what the gene count already explains, the association is biologically meaningful.
2. **Phylogenetic blocking in CV**: Ensure train/test splits don't share genera (prevents phylogenetic leakage).
3. **Partial correlation**: Report both raw and partial correlations (controlling for phylum + n_metal_clusters).

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

FB organism-to-pangenome mapping: `projects/conservation_vs_fitness/data/organism_mapping.tsv` (needed for the 12-organism direct validation in NB05).

### Cross-project data reuse
- **BacDive-pangenome bridge**: Reuse approach from `projects/bacdive_metal_validation/` (NB01). Reference the bridge-building logic but regenerate locally since the original data files are gitignored. If the bridge has been uploaded to the lakehouse (`microbialdiscoveryforge/projects/bacdive_metal_validation/data/`), download via `mc cp` rather than rebuilding.
- **Metal atlas scores**: Reference directly from `projects/metal_fitness_atlas/data/`.
- **Counter ion corrections**: Reference from `projects/counter_ion_effects/data/`.
- **Organism mapping**: Reference from `projects/conservation_vs_fitness/data/`.

### Performance Plan
- **Tier**: Local analysis (all data cached)
- **Estimated complexity**: Moderate (feature engineering + statistical modeling)
- **Known pitfalls**:
  - BacDive genome accessions (GCA_*) need prefix matching to pangenome IDs (GB_GCA_* or RS_GCF_*) — documented in `docs/pitfalls.md`
  - BacDive utilization/enzyme values have four categories (+, -, +/-, produced) — filter to explicit +/- only
  - BacDive species names don't always match GTDB — use GCA accessions, not species names, for joining (only 43.4% species-name match rate)
  - Phenotype coverage is sparse — need to handle missing data carefully
  - Phylogenetic confounding: many phenotypes are phylogenetically conserved → must control for taxonomy
  - FB numeric columns are strings — CAST if querying FB directly

## Analysis Plan

### Notebook 1: BacDive-Pangenome Bridge & Coverage Assessment
- **Goal**: Link BacDive strains to pangenome species; compute post-matching sample sizes for every feature
- **Method**:
  - Reuse GCA → pangenome matching approach from `bacdive_metal_validation` (check lakehouse first)
  - Match `sequence_info.accession` (GCA_*) to pangenome `genome.genome_id` using prefix adjustment (GB_GCA_* / RS_GCF_*)
  - Join bridge to Metal Fitness Atlas scores
  - **Coverage waterfall**: For each phenotype feature, report how many species have both a phenotype value AND a metal score after matching. This determines feasibility before proceeding.
- **Expected output**: Bridge table (bacdive_id → gtdb_species_clade_id), coverage waterfall table and figure
- **Go/no-go gate**: If fewer than 500 species have the key features (Gram, oxygen, catalase) after matching, reconsider the analysis approach (e.g., use taxonomy-based matching as fallback).

### Notebook 2: Phenotype Feature Engineering
- **Goal**: Build a species-level phenotype feature matrix from BacDive data
- **Method**:
  - Filter utilization/enzyme values to explicit +/- only (exclude +/-, variable)
  - Use measured physiology values only (not AI-predicted)
  - Aggregate strain-level phenotypes to species level:
    - Categorical: majority vote + agreement score
    - Binary: fraction positive, binarize at 0.5 threshold
    - Continuous: mean across strains
  - Compute metabolite utilization breadth and enzyme activity breadth
  - Handle missing data: report coverage per feature, retain all species with ≥1 feature (use NaN for missing)
- **Expected output**: Species × phenotype matrix with coverage metadata

### Notebook 3: Univariate Phenotype-Metal Associations
- **Goal**: Test each phenotype feature individually against metal tolerance score
- **Method**:
  - For binary features: Mann-Whitney U comparing metal scores between groups; report Cohen's d
  - For continuous features: Spearman correlation with metal tolerance score
  - Multiple testing correction (BH-FDR across all features)
  - **Phylogenetic stratification at class/order level** (not phylum — too coarse within Pseudomonadota). Report within-class effects to assess phylogenetic confounding.
  - Also test with partial correlation controlling for n_metal_clusters (circular reasoning control)
- **Expected output**: Association table with effect sizes, p-values, FDR q-values, class-stratified results

### Notebook 4: Multivariate Prediction Model
- **Goal**: Build a predictive model from multiple phenotype features
- **Method**:
  - **XGBoost** (handles missing values natively) predicting metal_score_norm from phenotype features
  - Cross-validation (5-fold) with phylogenetic blocking (no species from same genus in train+test)
  - Feature importance analysis (SHAP values)
  - **Baseline comparisons**:
    1. Taxonomy-only baseline (phylum/class/order as features)
    2. Metal gene count only (`n_metal_clusters` from atlas)
    3. Taxonomy + phenotype features
    4. Full model (taxonomy + phenotype + metal gene count)
  - Test: does adding phenotype features improve prediction beyond taxonomy and gene count?
  - Report: R², RMSE, and delta-R² for each model vs baselines
  - **Minimum feature completeness**: Require species to have ≥5 of 13 features non-missing for inclusion. Report how sample size varies with this threshold.
- **Expected output**: Model performance metrics, SHAP feature importance, comparison to baselines

### Notebook 5: Direct FB-BacDive Case Studies
- **Goal**: For the 12 FB organisms matching BacDive, present **descriptive case studies** comparing BacDive phenotypes to actual metal fitness profiles
- **Framing**: n=12 is insufficient for formal hypothesis testing; this notebook provides qualitative illustrations of whether the pangenome-scale associations hold for organisms with direct experimental data.
- **Method**:
  - Extract BacDive phenotypes for the 12 matched organisms (aggregating across all BacDive strains per species, noting strain count and agreement)
  - For each organism: summarize metal fitness profile (which metals tested, how many important genes, overall severity)
  - Narrative case studies:
    - DvH (anaerobe, H₂S producer): uranium and other metal tolerance
    - *E. coli* (catalase+, urease-): contrast metal profile with DvH
    - *P. fluorescens* (103 BacDive strains): phenotype variation within species
  - Concordance table: for each hypothesis (H1a-H1f), does the 12-organism data directionally support or contradict?
- **Expected output**: Case study narratives, concordance summary table

## Expected Outcomes
- **If H1 supported**: BacDive phenotypes capture real biological predictors of metal tolerance, enabling phenotype-based screening of metal-tolerant organisms from culture collections. Specific mechanisms (Gram-negative barrier, anaerobic metal reduction, sulfide precipitation) validated at genomic scale.
- **If H0 not rejected**: Metal tolerance is primarily determined by specific resistance gene clusters rather than broad physiological phenotypes; phenotypic traits are too phylogenetically confounded to add predictive power beyond taxonomy.
- **Potential confounders**:
  - Phylogenetic autocorrelation (Gram stain, oxygen tolerance, etc. are phylogenetically conserved)
  - BacDive testing bias (well-studied organisms have more phenotype data)
  - Metal Fitness Atlas scores are genome-based predictions, not direct measurements (mitigated by controlling for n_metal_clusters and phylogenetic blocking)

## Caveats
- **12-organism validation is species-level, not strain-level**: FB organisms match BacDive strains by NCBI taxonomy ID at the species level. Some species (e.g., *P. fluorescens*, 103 BacDive strains) have substantial strain-level phenotypic variation. NB05 will report strain counts and agreement scores for each match.
- **Post-matching sample size is unverified**: The estimated 3-5K species depends on GCA → pangenome matching success. NB01 includes a go/no-go gate.
- **Sparse features may have low power**: H₂S production (5.3K strain-level tests) and acetate utilization (2.2K) may yield only hundreds of matched species. Per-feature power will be reported in NB03.

## Revision History
- **v1** (2026-03-10): Initial plan
- **v2** (2026-03-10): Addressed plan review — added value encoding rules, coverage waterfall, agreement scores, class-level stratification, circular reasoning mitigation, descriptive framing for n=12 validation, expected effect sizes, cross-project data reuse conventions, go/no-go gate

## Authors
- Paramvir Dehal (https://orcid.org/0000-0002-3495-1240), Lawrence Berkeley National Laboratory, US Department of Energy

# Research Plan: Genotype × Condition → Phenotype Prediction from ENIGMA Growth Curves

## Research Question

Given a bacterial strain's genome and a defined growth condition (carbon source, metal, antibiotic, pH, ...), can we predict its quantitative growth phenotype (growth y/n, lag, µmax, max OD, yield), and do so in a way where the learned predictors are biologically interpretable, mechanistically grounded, and validated against independent fitness data?

Building on the ENIGMA high-throughput growth curve dataset (303 plates, ~26K well-level curves, ~5M timepoint measurements across 88 strains — many with matching Fitness Browser RB-TnSeq data), we aim to:

1. Establish a clean, condition-aligned (strain × condition → phenotype) table usable by multiple predictor families.
2. Compare three predictor paradigms on the same task: **GapMind pathway completeness** (rule-based), **FBA-lite** (mechanistic), and **gradient-boosted trees on genome features** (data-driven).
3. Define what it means for a predictor to be *biologically meaningful* — not just accurate — by cross-validating its learned features against independent Fitness Browser gene fitness data.
4. Identify where coverage is sufficient for reliable prediction vs. where more experiments are needed, and produce a ranked active-learning proposal for ENIGMA's next experimental round.

## Hypotheses

### H1 — Condition-alignable ground truth exists
- **H0**: ENIGMA growth curves and Fitness Browser fitness assays cannot be reliably aligned at the (strain × condition) level, because condition metadata is inconsistent across the two sources.
- **H1**: After canonicalizing media composition + additive molecule + concentration + pH, a substantial fraction (≥25%) of ENIGMA growth conditions can be matched to at least one FB experiment, yielding a dataset where strain genome, measured growth parameters, and measured gene fitness are all simultaneously available.

### H2 — Different predictor paradigms have complementary strengths
- **H0**: A single predictor paradigm (GapMind, FBA, or GBDT) dominates all others across all phenotype targets (growth y/n, lag, µmax, max OD, yield).
- **H1**: The three paradigms partition the prediction space. GapMind is strong on "does this pathway exist?" questions (high-recall binary growth for defined carbon sources). FBA is strong on yield and continuous parameters when models are available. GBDT is strongest for conditions with poor pathway coverage (metals, antibiotics, mixed stress) where predictions require combinations of features GapMind and FBA don't capture.

### H3 — Biological meaningfulness is measurable and separable from accuracy
- **H0**: A predictor's held-out accuracy is the best available indicator of its biological validity. Models with similar accuracy are equally mechanistic.
- **H1**: Accuracy and biological meaningfulness are separable axes. Two models with equal held-out accuracy can differ substantially in the fraction of their top-weighted features whose FB orthologs are fitness-significant under matched conditions. This "FB concordance" score correlates with downstream transferability to unseen strains.

### H4 — Feature resolution matters and interacts with the question
- **H0**: A single best genome feature representation (e.g., KEGG orthologs, or 90% AAI gene clusters) dominates all prediction targets and phenotypes.
- **H1**: Optimal feature granularity depends on the target. Binary growth on defined carbon sources is best predicted by coarse pathway-level features. Continuous growth parameters (lag, µmax, yield) benefit from fine-grained gene-family features. Regulatory and genome-scale scalar features (GC content, sigma factor diversity, ribosomal copy number) add independent signal after controlling for phylogeny for at least one target.

### H5 — Coverage diagnosis can drive rational experimental design
- **H0**: Random sampling of additional (strain, condition) pairs improves model accuracy as well as any principled selection strategy.
- **H1**: Ranking candidates by (model disagreement × genotype-space novelty × FB-concordance weighting) produces an active-learning set that improves model accuracy faster per experiment than random selection, as measured by retrospective subsampling.

## Literature Context

### Genotype–phenotype prediction from bacterial genomes

- **Plata et al. (2015)** pioneered large-scale prediction of bacterial growth media using genome-based FBA on ModelSEED models, establishing FBA as the baseline for carbon source prediction.
- **Kavvas et al. (2018)** and subsequent work from the Palsson group use ML-on-genome-features (SNP / gene presence) to predict antibiotic MIC, showing that GBDT-class models can match or exceed FBA for structured phenotypes when enough training data is available.
- **Weimann et al. (2016)** developed Traitar to predict phenotypes from protein family profiles using Pfam, demonstrating that cross-species transfer works when features are chosen at the right granularity.
- **Price et al. (2020, 2022, 2024)** built GapMind for automated pathway annotation, validated against RB-TnSeq data, and showed that fitness data can fill pathway gaps — setting the precedent for using FB as ground truth for pathway predictions.

### Growth curve parameterization

- **Baranyi & Roberts (1994)** and **Zwietering et al. (1990)** provide the canonical growth curve models (Baranyi, modified Gompertz) from which lag, µmax, and max OD are extracted.
- **Sprouffske & Wagner (2016)** `growthcurver` R package and **Kahm et al. (2010)** `grofit` provide widely used automated curve fitting with QC metrics. Python equivalents include `amiGO` and `croissance`.
- **Midani et al. (2021)** showed that derived growth parameters are reproducible across labs when QC gates are applied (e.g., AIC threshold for model fit, minimum OD range).

### Biological meaningfulness and interpretability

- **Lundberg & Lee (2017)** introduced SHAP values for post-hoc interpretation of tree ensembles; widely applied to genome-based ML but rarely cross-validated against independent functional data.
- **Galardini et al. (2017)** introduced "adversarial validation" in microbial ML: training a classifier to predict phylogeny from features to detect phylogenetic confounding.
- **Kuhnert et al. (2021)** demonstrated that phylogeny-aware mixed-effects models prevent false-positive feature selection in genome-wide association.

### Fitness Browser as ground truth

- **Price et al. (2018)** introduced the ~30K-condition RB-TnSeq fitness dataset across 32 bacteria. Subsequent expansions reach 48 organisms and 27M fitness scores in BERDL.
- **Wetmore et al. (2015)** established the statistical framework (t-like scores) for assessing fitness effect significance per (gene, experiment).

### ENIGMA high-throughput phenotyping

- ENIGMA SFA (Arkin lab and collaborators) has generated growth curves for field isolates from the Oak Ridge Field Research Center across defined media, carbon sources, and contaminant stress. The dataset stored in BERDL `enigma_coral.ddt_brick*` (bricks 928–1230) represents a novel asset not yet integrated with the pangenome / fitness browser at scale.

### Active learning for microbial phenotyping

- **Hie et al. (2020)** used uncertainty-based active learning to guide bacterial growth experiments, showing 5-10x efficiency gains over random sampling.
- **Zampieri et al. (2023)** demonstrated Bayesian active learning for microbial community design but not for single-organism (strain × condition) selection.

### Key References
1. Plata G, Henry CS, Vitkup D (2015). "Long-term phenotypic evolution of bacteria." *Nature* 517:369-372.
2. Kavvas ES et al. (2018). "Machine learning and structural analysis of Mycobacterium tuberculosis pan-genome identifies genetic signatures of antibiotic resistance." *Nature Communications* 9:4306.
3. Weimann A et al. (2016). "From genomes to phenotypes: Traitar, the microbial trait analyzer." *mSystems* 1:e00101-16.
4. Price MN et al. (2018). "Mutant phenotypes for thousands of bacterial genes of unknown function." *Nature* 557:503-509.
5. Price MN et al. (2020). "GapMind: Automated Annotation of Amino Acid Biosynthesis." *mSystems* 5:e00291-20.
6. Price MN et al. (2022). "Filling gaps in bacterial catabolic pathways with computation and high-throughput genetics." *PLOS Genetics* 18:e1010156.
7. Baranyi J, Roberts TA (1994). "A dynamic approach to predicting bacterial growth in food." *Int J Food Microbiol* 23:277-294.
8. Sprouffske K, Wagner A (2016). "Growthcurver: an R package for obtaining interpretable metrics from microbial growth curves." *BMC Bioinformatics* 17:172.
9. Lundberg SM, Lee SI (2017). "A unified approach to interpreting model predictions." *NeurIPS*.
10. Galardini M et al. (2017). "Phenotype inference in an Escherichia coli strain panel." *eLife* 6:e31035.
11. Hie B, Bryson BD, Berger B (2020). "Leveraging uncertainty in machine learning accelerates biological discovery." *Cell Systems* 11:461-477.
12. Wetmore KM et al. (2015). "Rapid quantification of mutant fitness in diverse bacteria by sequencing randomly bar-seq mutant libraries." *mBio* 6:e00306-15.

## Data Sources

### Core — Phenotype (growth curves)

| Table | Purpose | Scale | Filter Strategy |
|-------|---------|-------|-----------------|
| `enigma_coral.ddt_ndarray` | Brick metadata — which bricks are growth curves, shape, dates | 326 rows | Filter `description LIKE '%high throughput growth%'` → 303 growth bricks |
| `enigma_coral.ddt_brick0000928` ... `ddt_brick0001230` | Per-plate long-format curves: `(time, well, strain, media, additive, concentration, pH, OD)` | ~16K-28K rows/brick, ~5M total | Read per-brick, concatenate |
| `enigma_coral.sdt_strain` | Strain metadata, parent strain, genome link | 3,154 rows | Full scan OK |
| `enigma_coral.sdt_genome` | Genome link (n_contigs, link/accession) | small | Full scan OK |
| `enigma_coral.sdt_condition` | Condition IDs (`set1IT001` format suggests FB alignment) | 1,049 rows | Full scan OK |

### Core — Genotype (gene content, pathways, fitness)

| Table | Purpose | Scale | Filter Strategy |
|-------|---------|-------|-----------------|
| `kescience_fitnessbrowser.organism` | FB organism ↔ strain lookup | 48 rows | Full scan |
| `kescience_fitnessbrowser.gene` | Per-gene locus, annotations | millions | Filter by `orgId` |
| `kescience_fitnessbrowser.genefitness` | Gene fitness scores | 27M | Filter by `orgId`; CAST `fit`, `t` to FLOAT |
| `kescience_fitnessbrowser.experiment` | FB experiment metadata (condition, media) | ~10K | Full scan per `orgId` |
| `kescience_fitnessbrowser.seedannotation` | SEED subsystem assignments | millions | Filter by `orgId` |
| `kbase_ke_pangenome.gapmind_pathways` | Per-genome pathway scores (18 AA + 62 C) | 305M | Filter by `genome_id` list |
| `kbase_ke_pangenome.gene_cluster` | 90% AAI gene clusters | 132M | Filter by `gtdb_species_clade_id` |
| `kbase_ke_pangenome.eggnog_mapper_annotations` | COG / KEGG / GO / EC per cluster | 93M | Filter by `query_name` |
| `kbase_ke_pangenome.bakta_annotations` | Per-cluster rich annotations including UniRef100 | 132M | Filter by `gene_cluster_id` |
| `kbase_ke_pangenome.bakta_pfam_domains` | Pfam domains per cluster | 18M | Filter by `gene_cluster_id` |
| `kbase_ke_pangenome.genomad_mobile_elements` | Plasmid / prophage / AMR per gene | large | Filter by `gene_id` |
| `kbase_ke_pangenome.gtdb_metadata` | GC%, genome size, CheckM stats, taxonomy | 293K | Safe to scan |
| `kbase_ke_pangenome.gtdb_taxonomy_r214v1` | Full taxonomy | 293K | Safe to scan |
| `kbase_ke_pangenome.genome_ani` | Pairwise ANI | 421M | Filter per species |
| `kbase_msd_biochemistry.reaction` | ModelSEED reactions for FBA-lite | 56K | Full scan |
| `kbase_msd_biochemistry.compound` | ModelSEED compounds | 46K | Full scan |

### Anchor strain matches (ENIGMA × FB × Pangenome)

| ENIGMA strain | FB orgId | Pangenome link | Notes |
|---|---|---|---|
| `FW300-N1B4` | `pseudo1_N1B4` | via `fb_pangenome_link.tsv` | *Pseudomonas fluorescens* |
| `FW300-N2E2` | `pseudo6_N2E2` | via link table | *P. fluorescens* |
| `FW300-N2E3` | `pseudo3_N2E3` | via link table | *P. fluorescens* — primary test case (see `fw300_metabolic_consistency`) |
| `GW456-L13` | `pseudo13_GW456_L13` | via link table | *P. fluorescens* |
| `GW460-11-11-14-LB5` | `Pedo557` | via link table | *Pedobacter sp.* |

Additional indirect matches exist via species-level GTDB clades (e.g., other FW300 isolates that share a GTDB species with an FB-linked genome).

### Existing assets (reuse, do not re-extract)

| Asset | Source Project | Content |
|---|---|---|
| `conservation_vs_fitness/data/fb_pangenome_link.tsv` | conservation_vs_fitness | FB gene ↔ pangenome cluster (177K pairs, 30 orgs) |
| `conservation_vs_fitness/data/organism_mapping.tsv` | conservation_vs_fitness | FB org ↔ GTDB clade (44 orgs) |
| `conservation_vs_fitness/data/essential_genes.tsv` | conservation_vs_fitness | Gene essentiality classification |
| `fitness_effects_conservation/data/fitness_stats.tsv` | fitness_effects_conservation | Per-gene FB fitness summary |
| `fitness_modules/data/matrices/*.tsv` | fitness_modules | Fitness matrices (32 orgs) and ICA modules |
| `fw300_metabolic_consistency/data/metabolite_crosswalk.tsv` | fw300_metabolic_consistency | WoM ↔ FB ↔ BacDive ↔ GapMind metabolite crosswalk |
| `metabolic_capability_dependency/data/pathway_fitness_metrics.csv` | metabolic_capability_dependency | Pre-computed pathway-level fitness stats |

## Analysis Plan

The plan is organized into four phases. Each notebook produces a standalone deliverable, so the project yields value even if later phases are deferred.

### Phase 1 — Foundation (NB01-NB03)

#### NB01: Growth curve parsing and fitting
- **Goal**: Convert the 303 plate bricks into a single tidy `(strain, well, condition, time, OD, replicate)` table plus a `(strain, well, condition, lag, µmax, max_OD, AUC, carrying_capacity, diauxy_score, cryptic_score, fit_quality)` parameter table.
- **Method**:
  - Read each brick via Spark, concatenate with brick-level metadata (date, plate ID).
  - Fit Gompertz and Baranyi models to every well using `scipy.optimize.curve_fit`, select model per well by AIC.
  - Compute QC metrics: residual RMSE, OD range, curve monotonicity violations, edge-well flag.
  - Derive secondary parameters: diauxy score (number of distinct acceleration phases via smoothed derivative), cryptic growth (slow OD rise after apparent plateau), death-phase slope.
  - Flag curves failing QC gates (minimum OD range, AIC threshold, replicate dispersion).
- **Expected output**:
  - `data/growth_curves_long.parquet` — all (strain, well, time, OD) rows, QC-flagged
  - `data/growth_parameters.parquet` — one row per (strain, well, condition, replicate) with fitted parameters
  - `figures/NB01_curve_fit_examples.png` — 12 representative curves with fits
  - `figures/NB01_qc_summary.png` — QC pass/fail distribution across bricks
- **Runs on**: BERDL JupyterHub (Spark for reads); curve fitting is CPU-bound, parallelized via pandas UDF or driver-side multiprocessing.

#### NB02: Condition canonicalization and FB alignment
- **Goal**: Produce a **canonical condition vector** for every growth well and every FB experiment, so that (strain × condition) keys are comparable across the two sources.
- **Method**:
  - Extract per-well condition from ENIGMA brick columns: `microplate_well_media_name`, `context_media_sdt_condition_name`, `molecule_from_list_*_sys_oterm_name`, `concentration_*`, `microplate_well_ph_ph`.
  - Extract FB experiment conditions from `kescience_fitnessbrowser.experiment`: `expDescLong`, `condition_1`, `concentration_1`, `units_1`, `media`, `pH`.
  - Canonicalize via ontology mapping: (a) molecule ontology term → ChEBI / ModelSEED compound ID; (b) concentration → mM (converting from µg/mL via MW lookup); (c) pH → numeric; (d) media → base media category.
  - Check whether ENIGMA `sdt_condition` names (`set1IT001` format) literally match FB `setname` + `itnum` concatenations — if yes, we have gold-standard alignment; if not, fall back to canonical vector matching.
  - Output (strain × canonical_condition) alignment table with match provenance (exact name / canonical vector / approximate).
- **Expected output**:
  - `data/condition_canonical.parquet` — one row per canonical condition with ChEBI/ModelSEED compound ID, mM concentration, pH, media category
  - `data/enigma_fb_condition_alignment.tsv` — alignment map (ENIGMA condition → FB experiment(s))
  - `figures/NB02_alignment_coverage.png` — Venn / Sankey of condition coverage
- **Runs locally** from cached parquet + Spark reads of `experiment` table.

#### NB03: Coverage atlas
- **Goal**: Build the (strain × canonical_condition) evidence matrix across all data sources, identifying dense regions and data deserts.
- **Method**:
  - For every (strain, canonical_condition) pair, mark which data are available: growth curve? FB fitness vector? BacDive metabolite test? WoM production? GapMind pathway prediction? ModelSEED reaction?
  - Compute per-strain and per-condition coverage scores.
  - Identify the "dense anchor set" — (strain, condition) pairs with ≥3 data types — this is the training / evaluation cohort for Phase 2.
- **Expected output**:
  - `data/coverage_matrix.parquet` — (strain, condition, evidence_flags, count)
  - `data/anchor_set.tsv` — the dense-coverage subset for modeling
  - `figures/NB03_coverage_heatmap.png` — strain × condition evidence heatmap
  - `figures/NB03_coverage_by_source.png` — bar chart of coverage per data source
- **Runs locally**.

### Phase 2 — Baseline predictors (NB04-NB07)

#### NB04: GapMind-based predictor
- **Goal**: Predict growth (y/n), lag, µmax, max_OD using only GapMind pathway completeness as features.
- **Method**:
  - For each anchor (strain, condition) with a defined carbon source or amino acid auxotrophy interpretation, look up GapMind pathway score for the relevant pathway(s).
  - Rule-based prediction: complete pathway → growth predicted; steps_missing → no-growth predicted.
  - For continuous targets, fit a simple model `param ~ pathway_score` (ordinal regression / linear mixed model with strain random effect).
  - Evaluate with leave-one-strain-out CV on the 5 anchor strains.
- **Expected output**:
  - `data/gapmind_predictions.tsv` — per (strain, condition) predicted vs observed
  - `figures/NB04_gapmind_confusion.png`, `figures/NB04_gapmind_scatter.png`
- **Runs locally**.

#### NB05: FBA-lite predictor
- **Goal**: Mechanistic baseline predictor using draft FBA models for anchor strains.
- **Method**:
  - For each of the 5 anchor strains, build (or retrieve) a draft genome-scale metabolic model via ModelSEED reconstruction (from `kbase_genomes` and `kbase_msd_biochemistry`).
  - Run FBA for each canonical condition: set media composition, maximize biomass, record growth feasibility and biomass flux.
  - Map FBA growth rate → µmax via anchor-strain scaling; map FBA biomass yield → max_OD.
  - For conditions where no model exists or the compound isn't in the model, return "no prediction" (not a failure — a diagnostic).
- **Expected output**:
  - `data/fba_predictions.tsv` — per (strain, condition) predicted growth / flux / "no model" flag
  - `figures/NB05_fba_vs_observed.png`
- **Runs on**: BERDL JupyterHub (for model reconstruction) + local (for FBA via `cobrapy`).

#### NB06a: Genome feature engineering
- **Goal**: Construct and document multiple genome feature representations for every strain in the coverage atlas.
- **Method**: Compute all of the following, store each as a (strain × feature) matrix and a feature metadata file:
  - **Gene families (cross-species)**: UniRef50 / UniRef90 / UniRef100 membership counts per strain (via `bakta_annotations.uniref100` → `kbase_uniref50/90/100` cluster IDs). Primary backbone.
  - **Orthogroups**: COG category counts, KEGG ortholog (KO) presence, eggNOG OG presence per strain (via `eggnog_mapper_annotations`).
  - **Protein domains**: Pfam domain counts per strain (via `bakta_pfam_domains`).
  - **Pathway completeness**: GapMind scores per pathway (18 AA + 62 C) as an 80-dim vector.
  - **Reaction presence**: ModelSEED reaction IDs inferred from EC numbers.
  - **Genome-scale scalars**: GC%, genome size (bp), coding density, CheckM completeness/contamination, N50, # contigs.
  - **Ribosomal / translational**: # rRNA operons, # tRNA genes, tRNA species diversity (counts of distinct amino acid targets), codon usage bias (ENC, GC3), ribosomal protein variants.
  - **Regulatory proxies**: # sigma factor homologs by subfamily (σ70/54/32/S/E, via Pfam), # two-component systems (histidine kinase + response regulator counts), # transcription factors by DBD family (HTH, LuxR, AraC, GntR, MarR, ...).
  - **Defense / mobile load**: # CRISPR arrays, # R-M systems, prophage count, plasmid-linked gene count, AMR gene count (via `genomad_mobile_elements`, `bakta_amr`).
  - **Phylogenetic controls**: GTDB taxonomy (family / genus / species as categoricals); ANI to nearest FB-linked anchor; tree distance.
- **Expected output**:
  - `data/features/uniref50.parquet`, `uniref90.parquet`, `uniref100.parquet`, `cog.parquet`, `kegg.parquet`, `pfam.parquet`, `gapmind.parquet`, `modelseed_rxn.parquet`, `scalars.parquet`, `ribotranslation.parquet`, `regulatory.parquet`, `defense.parquet`, `phylogeny.parquet`
  - `data/feature_metadata.tsv` — one row per feature (name, family, description, derivation method, NA rate)
  - `figures/NB06a_feature_family_sizes.png` — dimensionality per family
  - `figures/NB06a_feature_redundancy.png` — cross-family correlation
- **Runs on**: BERDL JupyterHub (Spark-heavy).

#### NB06b: Condition feature engineering
- **Goal**: Convert canonical conditions to a numeric feature vector suitable for model input.
- **Method**:
  - Look up ChEBI → SMILES → RDKit Morgan fingerprint (2048-bit, radius 2).
  - Compute functional group indicators (amine, carboxyl, hydroxyl, phosphate, sulfate, halide, metal-binding, aromatic).
  - Encode concentration (log mM), pH (numeric), condition class (carbon / nitrogen / metal / antibiotic / stress).
  - One-hot media category.
- **Expected output**:
  - `data/condition_features.parquet` — one row per canonical condition
  - `figures/NB06b_condition_embedding.png` — 2D UMAP of condition space colored by class
- **Runs locally**.

#### NB06c: Interaction features
- **Goal**: Assemble the modeling matrix as `(genome × condition → phenotype)` with genome features, condition features, and optional interaction terms.
- **Method**:
  - For each (strain, canonical_condition) pair in the anchor set, concatenate the genome features (chosen family) and condition features.
  - Define interaction terms of interest: GapMind-score-for-this-condition × strain phylogeny; pathway-relevance × condition-class; metal-resistance-gene-count × metal-ion-identity.
  - Produce several modeling tables, one per feature configuration, so downstream notebooks can compare.
- **Expected output**:
  - `data/modeling/X_{feature_set}.parquet` × multiple configurations
  - `data/modeling/y_{target}.parquet` for each phenotype target
- **Runs locally**.

#### NB07: GBDT modeling and cross-paradigm comparison
- **Goal**: Train GBDT models (LightGBM or XGBoost) on each feature configuration × each target, with phylogenetic holdout, and compare to GapMind and FBA baselines on matched train/test splits.
- **Method**:
  - Leave-one-strain-out CV (on the 5 anchor strains) + leave-one-species-out CV (on the 88-strain extrapolation set, using species-level labels).
  - Report per-split RMSE (continuous targets) and AUC (binary growth) for every (feature set, target, model) combination.
  - Adversarial validation: train a taxon classifier on each feature set; features that perfectly predict taxonomy get flagged as phylogeny-confounded.
  - Mixed-effects residual analysis: fit `target ~ features + (1|genus)` and report variance components.
  - Head-to-head comparison table: GapMind vs FBA vs GBDT(coarse) vs GBDT(fine) per target.
- **Expected output**:
  - `data/model_results.tsv` — per (model, feature_set, target, CV_split) metrics
  - `data/model_predictions.tsv` — per (strain, condition, model) predicted vs observed
  - `figures/NB07_paradigm_comparison.png` — bar chart of paradigm × target performance
  - `figures/NB07_adversarial_validation.png` — feature-family phylogenetic leakage scores
- **Runs locally**.

### Phase 3 — Diagnosis and interpretability (NB08-NB10)

#### NB08: Counterfactual and conflict detection
- **Goal**: Identify (strain, condition) pairs where models disagree, where close-ANI strains diverge, or where replicates show unexplained variance — producing a ranked list of "high-information" candidates.
- **Method**:
  - Model disagreement: compute per-pair prediction variance across the three paradigms; rank by disagreement.
  - Near-neighbor divergence: for pairs of strains with ANI > 98% (from `genome_ani`) but divergent measured growth, flag as high-info counterfactuals.
  - Replicate inconsistency: flag (strain, condition) pairs with high within-condition CV and low measurement quality.
  - Propose diagnostic experiments: for the top-ranked counterfactuals, suggest what additional measurement (e.g., single-gene complementation, altered medium) would resolve the divergence.
- **Expected output**:
  - `data/conflict_ranked.tsv` — ranked candidates with scores and proposed diagnostic
  - `figures/NB08_disagreement_histogram.png`
  - `figures/NB08_near_neighbor_divergence.png`
- **Runs locally**.

#### NB09: Feature attribution and per-prediction interpretation
- **Goal**: For each predictor, extract the top-weighted features for every (strain, condition) prediction, producing a local explanation table.
- **Method**:
  - GBDT: SHAP values per prediction.
  - GapMind: which pathway step(s) are determinative.
  - FBA-lite: flux variability analysis on the biomass-producing path; rank reactions by essentiality.
  - Normalize all three to a common "feature → weight" representation so they can be compared.
- **Expected output**:
  - `data/local_attributions.parquet` — per (strain, condition, model, top_feature, weight)
  - `figures/NB09_example_attribution_cases.png` — 6 worked examples across paradigms
- **Runs locally**.

#### NB10: Biological meaningfulness via FB validation
- **Goal**: Score each predictor by the fraction of its top-weighted features whose FB orthologs are fitness-significant under matched conditions — a direct test of mechanistic validity.
- **Method**:
  - For each (strain, condition) in the anchor set where FB fitness data exist:
    1. Pull top-K features from each predictor (K = 10, 50, 100) via NB09 outputs.
    2. Map feature → FB locus via `fb_pangenome_link.tsv` and UniRef/KO cross-references.
    3. For matched FB experiment(s), compute fraction of those loci with |t| > 4 (significant fitness effect).
    4. Report this "FB concordance" as a model-level score, a per-condition score, and a per-feature-family score.
  - Phylogenetic leakage diagnostic: re-fit each model after regressing out GTDB taxonomy; report the accuracy drop and the FB concordance change. Models that drop sharply were leveraging phylogeny; models that don't drop are more mechanistic.
  - Combined score: accuracy × FB concordance × (1 - phylogenetic leakage).
- **Expected output**:
  - `data/meaningfulness_scores.tsv` — per (model, feature_set, target) meaningfulness metrics
  - `data/fb_concordance_per_condition.tsv` — breakdown by condition class
  - `figures/NB10_accuracy_vs_meaningfulness.png` — the key 2D plot
  - `figures/NB10_phylogenetic_leakage.png`
- **Runs locally**.

### Phase 4 — Active learning proposal (NB11, stretch)

#### NB11: Ranked experimental proposal
- **Goal**: Generate a ranked list of proposed next experiments for ENIGMA, targeting (strain, condition) pairs where resolution would most improve the ensemble model.
- **Method**:
  - Candidate pool: all (strain × canonical_condition) pairs NOT currently in the anchor set but where at least one data source has coverage (genome exists, or condition is canonicalized).
  - Scoring: (model disagreement from NB08) × (genotype-space novelty — distance to nearest anchor strain in feature space) × (meaningfulness-weighted coverage gain) × (experimental feasibility — condition class).
  - Retrospective validation: subsample the current anchor set, re-run NB07 with and without proposed points, show that proposed-point inclusion improves accuracy faster than random.
- **Expected output**:
  - `data/proposed_experiments.tsv` — ranked list (top 200), formatted for experimental intake
  - `figures/NB11_retrospective_learning_curve.png`
  - `figures/NB11_proposal_coverage_map.png`
- **Runs locally**.

## Query Strategy

### Performance notes
- Growth curve extraction (NB01): ~303 brick table reads × ~16K-28K rows each. Total ~5M rows. Use `spark.read.parquet` on the table path, or `spark.sql("SELECT * FROM enigma_coral.ddt_brick0000XXX")` in a loop, unioning DataFrames. Keep as Spark DataFrames until curve fitting, then convert to pandas per-strain.
- GapMind extraction (NB04/NB06a): reuse the approach from `metabolic_capability_dependency` — MAX aggregation over score_category, filter by genome_id IN (list).
- Feature matrix construction (NB06a): per-strain scans of `bakta_annotations`, `bakta_pfam_domains`, `eggnog_mapper_annotations`, `genomad_mobile_elements`. Each is a filtered join; aggregate in Spark, collect per-strain summaries.
- FB fitness extraction (NB10): reuse existing cached matrices from `fitness_modules/data/matrices/`. Filter to anchor orgIds, no new queries needed unless conditions are missing.

### Known pitfalls to watch for
- **String-typed numeric columns** in FB — cast `fit`, `t` to FLOAT.
- **Species clade IDs contain `--`** — fine in quoted Spark literals, NOT via REST API.
- **Gene clusters are species-specific** — cannot be used for cross-species features; use UniRef / KO / Pfam instead.
- **Decimal columns** in Spark `.toPandas()` — `CAST AS DOUBLE` in SQL, or `.astype(float)` after collection.
- **AVG over integers** returns decimal — wrap in `CAST(AVG(...) AS DOUBLE)`.
- **Brick table iteration** — 303 reads is acceptable via Spark but slow via REST API. Use Spark.
- **ENIGMA `sdt_condition` names may not match FB experiment names** — verify in NB02 before relying on name-based alignment.
- **Broadcast joins on `kbase_uniprot.uniprot_identifier` fail** — disable auto-broadcast if touching uniprot cross-references.
- **PySpark cannot infer numpy `str_`** — cast to native `str` before `createDataFrame`.

## Expected Outcomes

- **If H1 holds**: We have a clean (strain × condition → phenotype) anchor set of several thousand measurements where all three predictor paradigms can be applied and fairly compared.
- **If H2 holds**: GapMind / FBA / GBDT have complementary strengths, and an ensemble that weights paradigms per target outperforms any single paradigm. This would be a methodological contribution: "paradigm selection depends on phenotype target."
- **If H3 holds**: Two models with equal held-out accuracy can have 2-3× different FB concordance scores, establishing "biological meaningfulness" as a measurable, separable property of a predictor. This would allow principled model selection when held-out accuracy ties.
- **If H4 holds**: We identify a feature family (e.g., KEGG pathway completeness for carbon-source growth; sigma factor diversity for stress; metal-resistance-gene counts for heavy metal conditions) as the natural predictor for each target class, with explicit phylogenetic confounding controls.
- **If H5 holds**: The ranked active-learning proposal outperforms random sampling in retrospective subsampling, producing a credible, short list of next experiments for ENIGMA.
- **If all H0 hold**: The project is a negative result on a substantial scale — a calibration of how far current data and methods can go for condition-specific bacterial phenotype prediction. Still publishable as a benchmark.

### Potential confounders and limitations
- **Only 5 direct-match strains** for the deepest FB-anchored comparison. Extrapolation to the 88-strain set depends on cross-species feature stability.
- **Growth curve QC may reject many wells** — plate effects, condensation, edge-well artifacts. Expect ~20-30% rejection.
- **ENIGMA conditions may not literally match FB conditions** even after canonicalization — ontology gaps, concentration differences, media differences. Alignment quality is the key gating factor for H1.
- **FBA-lite models may not exist** for all 5 anchor strains in usable form; may require reconstruction effort that could blow the scope.
- **Feature engineering burden** — NB06a is the most expensive notebook and may need to be split further.
- **Regulatory signal features** are proxies (Pfam-domain counts), not true network topology; their interpretability is bounded.

## Revision History
- **v1** (2026-04-14): Initial plan. Four-phase design: foundation, baselines, diagnosis, active learning. Multi-feature-family genome representation with phylogenetic controls. Biological meaningfulness defined as FB concordance. Anchor set = 5 direct-match strains; extrapolation set = 88 total ENIGMA strains.

## Authors
- Adam Arkin (ORCID: 0000-0002-4999-2931), U.C. Berkeley / Lawrence Berkeley National Laboratory

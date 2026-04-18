# Research Plan: Genotype × Condition → Phenotype Prediction from ENIGMA Growth Curves

## Research Question

Can we predict bacterial growth phenotype — at multiple resolutions from binary growth/no-growth through continuous parameters (lag, µmax, yield) to complex dynamics (diauxy, death, maintenance) — from genome content and growth condition, in a way where the predictive features are biologically interpretable, mechanistically validated against independent gene fitness data, and actionable for rational experimental design?

## Why this matters

Microbial phenotype prediction from genotype is a central challenge in microbiology, with direct applications in bioremediation design (what substrates will an isolate use at a contamination site?), synthetic community assembly (which organisms produce/consume which metabolites?), and antimicrobial discovery (what genes are condition-essential?). Existing approaches are either high-accuracy but uninterpretable (deep learning on whole genomes) or interpretable but narrow (FBA, GapMind pathway lookups). No existing framework:

1. **Compares rule-based, mechanistic, and data-driven predictors on the same organism × condition matrix** with a formal protocol for choosing between them.
2. **Validates predictor features against independent experimental fitness data** — a measurable "biological meaningfulness" score that separates mechanistically grounded models from phylogeny-riding ones.
3. **Covers the full resolution spectrum** from binary growth through continuous kinetics to complex curve morphology.
4. **Integrates exometabolomic profiles** as a second prediction target — not just "does it grow?" but "what does it produce while growing?"

## What we have

This project sits at a unique convergence of five datasets covering the same Oak Ridge field isolates:

| Dataset | Scale | What it provides |
|---|---|---|
| **ENIGMA growth curves** | 303 plates, 27,632 curves, 7.57M timepoints, 123 strains, 195 molecules (ChEBI-tagged), 21 defined media | Continuous growth phenotype (lag, µmax, max OD, AUC, diauxy, death slope) |
| **ENIGMA Genome Depot** | 3,110 genomes, 6.8M proteins, 3.7M KO annotations, 6.4M COG annotations, 29.4M ortholog groups, 1.9M EC numbers | Pre-computed genome features for all 123 growth strains |
| **Fitness Browser** | 7 matching strains, 27M fitness scores across hundreds of conditions | Independent gene-level validation of predictor features |
| **Web of Microbes** | 6 matching strains, 630 metabolite observations (105 compounds × 6 strains) | Exometabolomic ground truth — what metabolites each strain produces |
| **Carbon source phenotypes** | 795 genomes × 379 conditions = ~53K binary growth labels with KofamScan + BacFormer features | Broad pretraining corpus for transfer to ENIGMA continuous targets |

No other lab system currently offers growth curves, gene fitness, exometabolomics, pre-annotated genomes, and a literature-curated phenotype corpus for the same strains. The overlap of 7 FB-matched and 6 WoM-profiled strains within the 123 growth-curve set creates a densely cross-validated anchor cohort.

## Aims

1. **Multi-resolution phenotype prediction**: Fit growth curves → extract (lag, µmax, max OD, AUC, diauxy, death) → predict each from genome features + condition descriptors. Determine which features matter at which resolution.
2. **Paradigm comparison**: Compare GapMind (rule-based), FBA-lite (mechanistic), and GBDT (data-driven) on matched train/test splits. Report accuracy AND biological meaningfulness for each.
3. **Biological meaningfulness as a measurable property**: Define FB concordance — the fraction of a predictor's top features whose orthologs show significant fitness effects under matched conditions — and show it is separable from held-out accuracy.
4. **Exometabolomic prediction**: For the 6 WoM-profiled strains, predict metabolite production/consumption from genome features. Test whether growth-predictive features also predict exometabolic output.
5. **Active learning**: Rank the next 200 (strain × condition) experiments for ENIGMA by model disagreement × genotype-space novelty × meaningfulness weight.

## Hypotheses

### H1 — Phenotype resolution requires feature resolution
- **H0**: A single genome feature representation (e.g., KO presence/absence) predicts all growth phenotype targets equally well, from binary growth through continuous parameters to complex dynamics.
- **H1**: Optimal feature granularity depends on the target. Binary carbon-source growth is best predicted by coarse pathway-level features (GapMind completeness, KEGG module coverage). Continuous parameters (µmax, lag) require finer-grained gene-family features (individual KOs, ortholog groups). Complex dynamics (diauxy, death phase) require regulatory proxies (sigma factor diversity, operon structure) that pathway-level features miss. Genome-scale scalars (GC%, ribosomal copy number) contribute independently after controlling for phylogeny.

### H2 — Rule-based, mechanistic, and data-driven paradigms are complementary
- **H0**: One predictor paradigm dominates all others across all condition types and phenotype targets.
- **H1**: GapMind wins on defined carbon source growth (high recall, interpretable pathway names). FBA wins on yield prediction when a genome-scale model is available. GBDT wins on conditions with no pathway interpretation (metals, antibiotics, pH stress). An ensemble that selects paradigm per condition-type outperforms any single paradigm overall. The complementarity is condition-class-dependent, not target-dependent — a given paradigm's advantage is about *what kind of biology it encodes*, not how many parameters it fits.

### H3 — Biological meaningfulness is measurable and separable from accuracy
- **H0**: Held-out accuracy is the best indicator of a predictor's mechanistic validity.
- **H1**: FB concordance — the fraction of a predictor's top-K features whose FB orthologs show significant fitness effects under matched conditions — is an independent axis from held-out accuracy. Two models with equal RMSE on growth parameters can have 2-3× different FB concordance scores. Higher FB concordance correlates with better out-of-distribution transfer to Tier 2 strains, because mechanistically grounded features generalize beyond phylogenetic signal.

### H4 — Broad binary data transfers to narrow continuous targets
- **H0**: A model pretrained on the CSP corpus (795 genomes × 379 binary growth labels) performs no better on ENIGMA continuous growth parameters than a model trained from scratch on ENIGMA data alone.
- **H1**: Pretraining on CSP and fine-tuning on ENIGMA continuous targets (µmax, lag, max OD) outperforms ENIGMA-only training, because the CSP corpus provides a prior over which KOs matter for which substrates. The transfer is strongest for carbon-source conditions (high CSP overlap) and weakest for metal/antibiotic stress (no CSP training data — a genuine out-of-domain test).

### H5 — Growth predictors also predict exometabolomic output
- **H0**: Features that predict whether a strain grows on a carbon source are unrelated to features that predict whether it produces/consumes specific metabolites.
- **H1**: For the 6 WoM-profiled strains, GBDT features predictive of growth on carbon source X are enriched among genes associated with production of metabolites derived from X. Growth-predictive KOs overlap with WoM-concordant genes identified in the `fw300_metabolic_consistency` project. This connects the "will it grow?" question to the "what will it produce?" question through shared metabolic pathway features.

### H6 — Active learning outperforms random experimental design
- **H0**: Random sampling of new (strain, condition) experiments improves model accuracy as efficiently as any principled strategy.
- **H1**: Ranking candidates by (model disagreement × genotype-space novelty × FB-concordance weight) produces a set that improves accuracy faster per experiment than random, verified by retrospective subsampling on the existing corpus.

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

### Core — Genotype (ENIGMA Genome Depot — primary feature source)

| Table | Purpose | Scale | Filter Strategy |
|-------|---------|-------|-----------------|
| `enigma_genome_depot_enigma.browser_genome` | ENIGMA genomes (contigs, size, genes, NCBI links) | 3,110 | Full scan OK |
| `enigma_genome_depot_enigma.browser_strain` | Strain ↔ genome ↔ taxon mapping | 2,098 | Full scan OK |
| `enigma_genome_depot_enigma.browser_gene` | Gene coordinates, locus tags, operons | 16.6M | Filter by `genome_id` |
| `enigma_genome_depot_enigma.browser_protein` | Protein sequences + eggNOG descriptions | 6.8M | Filter by protein_id via gene |
| `enigma_genome_depot_enigma.browser_protein_kegg_orthologs` | KO assignments per protein | 3.7M | Join via `protein_id` |
| `enigma_genome_depot_enigma.browser_protein_cog_classes` | COG class per protein | 6.4M | Join via `protein_id` |
| `enigma_genome_depot_enigma.browser_protein_ec_numbers` | EC numbers per protein | 1.9M | Join via `protein_id` |
| `enigma_genome_depot_enigma.browser_protein_go_terms` | GO terms per protein | 25.3M | Join via `protein_id` |
| `enigma_genome_depot_enigma.browser_protein_ortholog_groups` | Ortholog group membership | 29.4M | Join via `protein_id` |
| `enigma_genome_depot_enigma.browser_operon` | Operon predictions | 3.4M | Filter by genome |
| `enigma_genome_depot_enigma.browser_taxon` | Taxonomy per genome | 3,597 | Full scan OK |

### Core — Fitness Browser (mechanistic validation)

| Table | Purpose | Scale | Filter Strategy |
|-------|---------|-------|-----------------|
| `kescience_fitnessbrowser.organism` | FB organism ↔ strain lookup | 48 rows | Full scan |
| `kescience_fitnessbrowser.gene` | Per-gene locus, annotations | millions | Filter by `orgId` |
| `kescience_fitnessbrowser.genefitness` | Gene fitness scores | 27M | Filter by `orgId`; CAST `fit`, `t` to FLOAT |
| `kescience_fitnessbrowser.experiment` | FB experiment metadata (condition, media) | ~10K | Full scan per `orgId` |
| `kescience_fitnessbrowser.seedannotation` | SEED subsystem assignments | millions | Filter by `orgId` |

### Core — Web of Microbes (exometabolomic validation)

| Table | Purpose | Scale | Filter Strategy |
|-------|---------|-------|-----------------|
| `kescience_webofmicrobes.organism` | WoM organism lookup | 37 organisms | Full scan |
| `kescience_webofmicrobes.observation` | Metabolite production/consumption | ~10K | Filter by `organism_id` for matched strains |
| `kescience_webofmicrobes.compound` | Identified metabolite names and formulas | 589 | Full scan |

6 growth-curve strains matched: FW300-N2E3, GW456-L13, FW300-N2A2, GW456-L15, FW507-14TSA, FW300-N2F2. Each has 105 metabolite observations (Emerged / Increased / No Change).

### Core — Carbon Source Phenotype Corpus (pretraining)

| Table | Purpose | Scale | Filter Strategy |
|-------|---------|-------|-----------------|
| `globalusers_carbon_source_phenotypes.genome_table` | 1,097 genomes (795 with phenotype data) | 1,097 | Full scan |
| `globalusers_carbon_source_phenotypes.phenotype_data_table` | Binary growth (0/1) per (genome, phenotype) | 57,302 | Full scan |
| `globalusers_carbon_source_phenotypes.phenotype_description_table` | Phenotype names and media context | 379 | Full scan |
| `globalusers_carbon_source_phenotypes.kofam_annotation_table` | KofamScan KO per gene | 5.2M | Filter by `genomeid` |
| `globalusers_carbon_source_phenotypes.bacformer_annotation_table` | BacFormer protein-LM embeddings (~480 dim) | 526K | Filter by `genomeid` |
| `globalusers_carbon_source_phenotypes.taxonomy_table` | GTDB taxonomy | 1,097 | Full scan |

Joint KBase/BERDL project, preprint in preparation by Dileep et al. Usable for pretraining.

### Supplementary — Pangenome (for Tier 2 pangenome-linked strains only)

| Table | Purpose | Scale | Filter Strategy |
|-------|---------|-------|-----------------|
| `kbase_ke_pangenome.gapmind_pathways` | Per-genome pathway scores (18 AA + 62 C) | 305M | Filter by `genome_id` list |
| `kbase_ke_pangenome.gene_cluster` | 90% AAI gene clusters | 132M | Filter by `gtdb_species_clade_id` |
| `kbase_ke_pangenome.eggnog_mapper_annotations` | COG / KEGG / GO / EC per cluster | 93M | Filter by `query_name` |
| `kbase_ke_pangenome.bakta_pfam_domains` | Pfam domains per cluster | 18M | Filter by `gene_cluster_id` |
| `kbase_ke_pangenome.genomad_mobile_elements` | Plasmid / prophage / AMR per gene | large | Filter by `gene_id` |
| `kbase_ke_pangenome.gtdb_metadata` | GC%, genome size, CheckM, taxonomy | 293K | Safe to scan |
| `kbase_msd_biochemistry.reaction` | ModelSEED reactions for FBA-lite | 56K | Full scan |
| `kbase_msd_biochemistry.compound` | ModelSEED compounds | 46K | Full scan |

### Strain tiering (v3 — post Genome Depot)

With the arrival of `enigma_genome_depot_enigma` (3,110 ENIGMA genomes with pre-computed KO, COG, OG, EC, GO annotations), the old 3-tier structure collapses to two. Every growth-curve strain now has rich pre-computed genome features. The differentiation is whether the strain additionally has independent Fitness Browser and/or Web of Microbes data for mechanistic validation.

Linkage tables: `data/eda/strain_linkage_master.tsv`, `data/eda/genome_depot_matches.tsv`, `data/eda/wom_strain_matches.tsv`.

#### Tier 1 — Dense anchor strains (growth + genome depot + FB fitness ± WoM): 7 strains

The gold cohort for model training, FB-concordance validation, and WoM exometabolomic prediction. Leave-one-strain-out CV on this cohort tests within-distribution generalization.

| ENIGMA strain | FB orgId | WoM? | Curves | FB conditions | Notes |
|---|---|---|---|---|---|
| `FW300-N2E3` | `pseudo3_N2E3` | Yes (105 metabolites) | 454 | 43 (19 overlap ENIGMA) | Primary anchor; characterized in `fw300_metabolic_consistency` |
| `FW300-N2E2` | `pseudo6_N2E2` | — | 456 | 26 | *P. fluorescens* |
| `FW300-N1B4` | `pseudo1_N1B4` | — | 360 | 19 | *P. fluorescens* |
| `GW456-L13` | `pseudo13_GW456_L13` | Yes (105 metabolites) | 360 | 9 | *P. fluorescens* |
| `GW460-11-11-14-LB5` | `Pedo557` | — | 362 | 19 | *Pedobacter sp.* |
| `GW101-3H11` | `acidovorax_3H11` | — | 192 | (to verify) | *Acidovorax sp.* |
| `FW507-4G11` | `Cup4G11` | — | 192 | (to verify) | *Cupriavidus basilensis* |

#### Tier 2 — Full feature strains (growth + genome depot, no FB): 116 strains

All remaining growth-curve strains. Each has KO (~2,000 per genome), COG (21/23 classes), ortholog groups (~16K), EC numbers, GO terms, and operon predictions from the genome depot. Usable for genome-feature-based training (GBDT, transfer from CSP), held-out evaluation, and phylogenetic-leakage diagnostics. Not usable for FB-concordance validation (no independent fitness data).

Substructure by additional data availability:
- **WoM-profiled** (4 strains): FW300-N2A2, GW456-L15, FW507-14TSA, FW300-N2F2 — each has 105-metabolite exometabolomic profiles. These enable WoM prediction evaluation without FB data.
- **BERDL pangenome-linked** (25 additional strains beyond Tier 1): also have GapMind pathway predictions, UniRef/Pfam/bakta annotations, and ANI matrices from the main pangenome. These have the richest feature set.
- **Genome depot only** (91 strains): KO/COG/OG/EC/GO features from the depot. No pangenome features (GapMind, UniRef, ANI). Still fully usable for KO-based and OG-based modeling.

#### Feature-availability summary

| Feature family | Tier 1 (7) | Tier 2 WoM (4) | Tier 2 pangenome (25) | Tier 2 depot-only (91) | CSP (795) |
|---|---|---|---|---|---|
| Growth curves (fitted) | yes | yes | yes | yes | — |
| FB fitness (per-gene) | yes | — | — | — | — |
| WoM exometabolomics | 2 of 7 | yes | — | — | — |
| Genome depot KO/COG/OG/EC/GO | yes | yes | yes | yes | — |
| Pangenome (GapMind, UniRef, Pfam, ANI) | yes* | some | yes | — | — |
| CSP binary phenotype | — | — | — | — | yes |
| CSP KofamScan KO | — | — | — | — | yes |
| CSP BacFormer embeddings | — | — | — | — | yes |

*Tier 1 strains linked via `gtdb_metadata.ncbi_strain_identifiers` (5 of 7 confirmed; Pedo557 and Cup4G11 pending).

#### Implication for modeling

- **Training**: Pretrain on CSP (795 genomes, binary targets, KofamScan KO features). The genome depot's KO annotations are comparable to CSP's KofamScan, enabling direct feature-space alignment.
- **Fine-tuning / evaluation**: Apply to all 123 ENIGMA strains (continuous targets from NB01). Tier 1 gets FB-concordance evaluation; Tier 2 WoM-profiled get exometabolomic evaluation.
- **Active learning**: Rank candidates from the full 123 × condition grid.

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

## Execution Environment

| Notebook | Environment | Rationale |
|---|---|---|
| NB00 (data survey) | JupyterHub (Spark reads) | Queries across 303 bricks + FB + CSP |
| NB01 (curve fitting) | JupyterHub (Spark reads) + local (scipy fits) | Brick reads require Spark; fitting is CPU-only |
| NB02 (condition canon.) | JupyterHub (FB/WoM queries) + local (ChEBI lookup) | One-time extraction of condition metadata |
| NB03 (coverage atlas) | Local | Joins cached TSVs, no Spark needed |
| NB04 (GapMind baseline) | Local | Small cached data |
| NB05 (FBA-lite) | Local (cobrapy) | Runs on local machine or CTS |
| NB06a (genome features) | JupyterHub (Spark) | Depot + pangenome queries for 123 strains |
| NB06b-c (condition/interaction features) | Local | ChEBI/RDKit, small data |
| NB07 (GBDT modeling) | Local (LightGBM) | Training on ~10K-100K rows, minutes |
| NB08-NB10 (diagnosis) | Local | Post-hoc analysis of model outputs |
| NB11 (active learning) | Local | Scoring + ranking |

## Condition-Alignment Fallback Strategy

Condition alignment (NB02) is the gating factor for the project. Four fallback levels:

- **Plan A — Exact ID match**: ENIGMA `sdt_condition` names (`set1IT001`) literally match FB `setname + itnum`. If confirmed, this is gold-standard alignment (no ambiguity). NB00 identified 1,049 condition IDs but didn't verify FB format match — NB02 priority 1.
- **Plan B — ChEBI ID match**: ENIGMA bricks carry ChEBI CURIEs per molecule (e.g., `CHEBI:17234` = glucose). Map FB condition names to ChEBI via PubChem/ChEBI API. Match on (ChEBI ID, concentration bin, media category). Expected to cover all named carbon sources and amino acids.
- **Plan C — Fuzzy string + concentration tolerance**: For conditions without ChEBI resolution, normalize strings (lowercase, strip punctuation) and match within ±50% concentration. NB00 already showed 73 ENIGMA∩FB matches by naive normalization.
- **Plan D — Condition-class pooling**: If per-condition alignment fails for metals/antibiotics (which have no ChEBI in FB), pool FB experiments by condition class (e.g., "all zinc experiments" → one zinc condition class). This loses concentration specificity but preserves strain × condition-class structure.

## Growth Curve QC Contingency

NB01 found 35.7% of curves pass fit_ok (R²>0.8, RMSE<10% OD range). If this proves insufficient for downstream modeling:
- **Relax fit_ok**: Lower R² threshold to 0.7 (expect ~45% pass rate) — acceptable if RMSE remains bounded.
- **Add no-growth as a valid label**: No-growth wells carry information (the strain can't use that substrate). Recode as binary growth=0 rather than discarding. This is biologically correct and dramatically expands the modeling dataset.
- **Smooth QC**: Replace hard pass/fail with a continuous quality weight in the loss function (low-R² curves get down-weighted, not excluded).

## Revision History

- **v3** (2026-04-18): Post-Genome-Depot revision.
  - **ENIGMA Genome Depot arrived**: `enigma_genome_depot_enigma` — 3,110 genomes, 6.8M proteins, 3.7M KO, 6.4M COG, 29.4M OG, 1.9M EC, 25.3M GO annotations. All 123 growth-curve strains matched. Collapses old 3-tier structure to 2 tiers (Tier 1: 7 FB anchors; Tier 2: all 123 with genome depot features). Eliminates "Tier 3 no-features" category entirely.
  - **Web of Microbes integration**: 6 of 123 growth strains have full 105-metabolite exometabolomic profiles (FW300-N2E3, GW456-L13, FW300-N2A2, GW456-L15, FW507-14TSA, FW300-N2F2). Adds metabolite production/consumption as a second prediction target (H5 added).
  - **Hypotheses sharpened**: Collapsed from 8 hypotheses (H1-H8) to 6 focused ones (H1-H6). Merged old H1 (condition alignment — now a validated prerequisite rather than a hypothesis) into the methodology. Promoted feature-resolution dependence (old H4) to H1. Added H5 (exometabolomic prediction via WoM). Kept active learning as H6.
  - **Data sources restructured**: Genome depot is now the primary genotype feature source (replaces pangenome-only). Pangenome tables moved to "supplementary" for the 32 pangenome-linked strains. CSP corpus and WoM added as formal data source tables.
  - **Review items addressed**: Added execution environment table, condition-alignment fallback strategy (Plans A-D), and growth curve QC contingency.
  - **Research framing sharpened**: New "Why this matters" section positions the project at the intersection of interpretable ML, multi-resolution phenotyping, and rational experimental design. "What we have" section makes the unique five-dataset convergence explicit.

- **v2** (2026-04-14): Post-EDA revision informed by NB00 data survey. Key corrections to v1 assumptions, with implications for the predictor architecture:
  - **Strain count**: 123 distinct strains in the brick data (not 88 — v1 parsed brick filenames, which misses bricks whose naming doesn't match the canonical pattern).
  - **Tier 1 anchor size**: **7 strains** with direct Fitness Browser matches (not 5). Additions: `GW101-3H11 ↔ acidovorax_3H11` and `FW507-4G11 ↔ Cup4G11`.
  - **Tier 2 (BERDL pangenome + growth curves)**: **32 strains** (Tier 1 ⊂ Tier 2).
  - **Tier 3 (CORAL narrative genome + growth curves)**: **all 123**. Every growth-curve strain has a KBase narrative genome in `enigma_coral.sdt_genome` (dataview workspace 41372). The "missing genome" problem from v1 was an artifact of joining from the wrong side of the FK.
  - **Primary training corpus added**: `globalusers_carbon_source_phenotypes` — 795 genomes × ~53K binary phenotype measurements with pre-computed KofamScan KO and BacFormer embeddings. This is joint KBase/BERDL data led by team member Dileep (preprint in prep, usable in this project). It expands the effective training cohort from ~5 strains to ~800 genomes for binary-growth prediction. The ENIGMA growth curves now serve as a **continuous-target out-of-distribution test set** rather than the primary training data, with FB fitness as the mechanistic validation cohort for Tier 1 anchors.
  - **Cross-dataset condition overlap (naive string match)**: 195 ENIGMA molecules × 379 CSP phenotypes × 350 FB conditions → 19 triple-overlap, 82 pairwise, 566 unique. ENIGMA∩FB alone is 73 conditions (~21% of FB's condition catalogue). Proper ChEBI-ID canonicalization in NB02 is expected to grow these numbers substantially.
  - **FB anchor coverage is uneven**: pseudo3_N2E3 (FW300-N2E3) has 43 FB conditions (19 overlap ENIGMA); pseudo13_GW456_L13 has only 9 (2 overlap). Per-anchor statistics must be weighted.
  - **New Hypotheses**: Adding H6 (broad-to-narrow transfer learning: pretraining on CSP binary phenotypes and fine-tuning on ENIGMA continuous targets outperforms training from scratch on ENIGMA alone); H7 (BacFormer embeddings are competitive with explicit KO/pathway features on the CSP target — data-driven vs. knowledge-driven comparison); H8 (condition breadth extrapolation: predictors trained on carbon-source data fail on metal/antibiotic stress, providing a genuine out-of-domain test).
  - **Remaining review items (not yet addressed)**: condition-alignment fallback (Plans A/B/C/D), execution-environment table, NB06a split, QC contingency, bootstrap CV, FBA feasibility gate. Deferred to v3 pending the ENIGMA GenomeDepot upload from Alexey (which will add Tier 2 features for all 123 strains instead of just 32).
  - **Outstanding access**: `u_janakakbase__growthphenos` (7 tables with experiment/measurement/condition_set/protocol schema) returns `AccessDeniedException` on the personal warehouse path. Needs access grant from Janaka; may replace the CORAL ddt_brick parsing pipeline if it's a cleaner canonicalization of the same underlying data.

- **v1** (2026-04-14): Initial plan. Four-phase design: foundation, baselines, diagnosis, active learning. Multi-feature-family genome representation with phylogenetic controls. Biological meaningfulness defined as FB concordance. Anchor set = 5 direct-match strains; extrapolation set = 88 total ENIGMA strains.

## Authors
- Adam Arkin (ORCID: 0000-0002-4999-2931), U.C. Berkeley / Lawrence Berkeley National Laboratory

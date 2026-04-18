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

## Scientific Context: ENIGMA SFA and the Oak Ridge Field Site

This project sits within the ENIGMA Scientific Focus Area (Ecosystems and Networks Integrated with Genes and Molecular Assemblies), which aims to understand how microbial communities mechanistically assemble in the terrestrial subsurface, grow, and transform their environment.

**The field site**: The Oak Ridge Y-12 National Security Complex has localized contamination plumes from Manhattan Project-era uranium extraction. These plumes are high in uranium and other heavy metals, with nitrate (used in the extraction process) that lowers pH and interacts with the surrounding geology. The geology is dominated by southeast-dipping, fractured shale (Nolichucky, Rogersville, Pumpkin Valley Shales of the Conasauga Group) interbedded with carbonate units, overlaid by 0-80 feet of weathered regolith/saprolite. Adjacent Maynardville Limestone and Copper Ridge Dolomite contribute karst features that interact with the shale aquifers. Contaminants (uranium, metals) concentrate in the water table fluctuation zone where amorphous basaluminite precipitates form.

**Carbon dynamics**: Carbon and other nutrient availability in the subsurface is generally low. Simple carbon compounds (e.g., acetate, lactate from necromass decomposition) are consumed quickly by fast-growing organisms, leaving slower-to-consume, more complex carbon for extended use by specialists. This creates a selective landscape where carbon source breadth, utilization kinetics, and metabolic efficiency are ecologically determinative.

**Why growth prediction matters here**: Understanding which strains grow on which substrates, how quickly, and what they produce while growing is directly relevant to predicting field-scale community dynamics in contaminated subsurface environments. The growth curves in this project are not abstract phenotypes — they represent the physiological capabilities that determine which organisms thrive in plume vs. background conditions at Oak Ridge.

## Literature Context

### Genotype–phenotype prediction from bacterial genomes

- **Xu, Zakem & Weissman (2025)** developed Phydon, which predicts maximum growth rate from codon usage bias (gRodon) combined with phylogenetic nearest-neighbor interpolation. Their central contribution is **phylogenetically blocked cross-validation**: cutting the GTDB tree at varying depths to create train/test splits with controlled phylogenetic distance. They show that phylogeny beats genomic features at short distances but genomic features (CUB) are more stable at long distances. We adopt their blocked-CV strategy and add CUB as a baseline predictor.
- **Weimann et al. (2016)** developed Traitar to predict phenotypes from Pfam protein family profiles, demonstrating that cross-species transfer works when features are chosen at the right granularity. Our approach extends this with multi-resolution features and independent fitness validation.
- **Kavvas et al. (2018)** showed GBDT-class models on genome features can match or exceed FBA for structured phenotypes (antibiotic MIC) when training data is sufficient.
- **Plata et al. (2015)** used genome-scale FBA (ModelSEED) to predict bacterial growth media, establishing the mechanistic baseline for carbon source prediction.
- **Price et al. (2020, 2022, 2024)** built GapMind for automated pathway annotation, validated against RB-TnSeq fitness data, showing that fitness data can fill pathway gaps.

### Growth curve parameterization

- **Baranyi & Roberts (1994)** and **Zwietering et al. (1990)** provide the canonical growth curve models from which lag, µmax, and max OD are extracted.
- **Sprouffske & Wagner (2016)** and **Kahm et al. (2010)** provide automated fitting tools with QC metrics.
- **Midani et al. (2021)** showed derived growth parameters are reproducible across labs when QC gates are applied.

### Biological meaningfulness and interpretability

- **Lundberg & Lee (2017)** introduced SHAP values; widely applied to genome-based ML but rarely cross-validated against independent functional data (our FB concordance metric addresses this gap).
- **Galardini et al. (2017)** introduced adversarial validation for phylogenetic confounding detection.
- **Kuhnert et al. (2021)** showed phylogeny-aware mixed-effects models prevent false-positive feature selection.

### Microbial biogeography and co-occurrence

- **Friedman & Alm (2012)** introduced SparCC for inferring microbial correlations from compositional data (16S amplicon), addressing the compositionality artifact that distorts standard Pearson/Spearman correlations. We use SparCC or a modern variant for co-occurrence analysis of ENIGMA genera.
- **Thompson et al. (2017)** compiled the Earth Microbiome Project, establishing global patterns of microbial biogeography linked to environmental metadata — the kind of analysis we perform with the microbeatlas database.

### Fitness Browser and exometabolomics

- **Price et al. (2018)** introduced the RB-TnSeq fitness dataset (now 48 organisms, 27M scores in BERDL).
- **Wetmore et al. (2015)** established the statistical framework for per-gene fitness assessment.
- **Kosina et al. (2018)** curated the Web of Microbes exometabolomics database — our source for metabolite production/consumption ground truth.

### ENIGMA high-throughput phenotyping

- ENIGMA SFA has generated high-throughput growth curves for 123 Oak Ridge field isolates across defined media, carbon sources, metals, and antibiotics. This dataset (303 plates, 27,632 curves, 7.57M timepoints) stored in BERDL represents a novel asset for understanding strain physiology in the context of subsurface contamination biology.

### Key References
1. Xu L, Zakem EJ, Weissman JL (2025). "Improved maximum growth rate prediction from microbial genomes by integrating phylogenetic information." *Nature Communications* 16:4256.
2. Weimann A et al. (2016). "From genomes to phenotypes: Traitar, the microbial trait analyzer." *mSystems* 1:e00101-16.
3. Kavvas ES et al. (2018). "Machine learning and structural analysis of Mycobacterium tuberculosis pan-genome." *Nature Communications* 9:4306.
4. Plata G, Henry CS, Vitkup D (2015). "Long-term phenotypic evolution of bacteria." *Nature* 517:369-372.
5. Price MN et al. (2018). "Mutant phenotypes for thousands of bacterial genes of unknown function." *Nature* 557:503-509.
6. Price MN et al. (2020). "GapMind: Automated Annotation of Amino Acid Biosynthesis." *mSystems* 5:e00291-20.
7. Price MN et al. (2022). "Filling gaps in bacterial catabolic pathways." *PLOS Genetics* 18:e1010156.
8. Baranyi J, Roberts TA (1994). "A dynamic approach to predicting bacterial growth in food." *Int J Food Microbiol* 23:277-294.
9. Lundberg SM, Lee SI (2017). "A unified approach to interpreting model predictions." *NeurIPS*.
10. Galardini M et al. (2017). "Phenotype inference in an Escherichia coli strain panel." *eLife* 6:e31035.
11. Friedman J, Alm EJ (2012). "Inferring correlation networks from genomic survey data." *PLOS Computational Biology* 8:e1002687.
12. Thompson LR et al. (2017). "A communal catalogue reveals Earth's multiscale microbial diversity." *Nature* 551:457-463.
13. Kosina SM et al. (2018). "Web of microbes (WoM): a curated microbial exometabolomics database." *BMC Microbiology* 18:139.
14. Wetmore KM et al. (2015). "Rapid quantification of mutant fitness." *mBio* 6:e00306-15.
15. Hie B, Bryson BD, Berger B (2020). "Leveraging uncertainty in machine learning accelerates biological discovery." *Cell Systems* 11:461-477.

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

The project is organized into three acts. Each notebook produces a standalone deliverable; the project yields value even if later acts are deferred.

### Act I — Know the Collection (NB01-NB04)

#### NB01: Growth curve parsing and fitting [DONE]
- **Status**: Complete (27,632 curves fit, 9,861 fit_ok, 15,227 no_growth).
- See `src/curve_fitting.py` (Gompertz model), `src/batch_fit.py` (resumable batch driver).
- Output: `data/growth_parameters_all.parquet`, 4 figures.

#### NB02: Condition canonicalization and cross-dataset alignment
- **Goal**: Produce a canonical condition key for every ENIGMA well, FB experiment, and CSP phenotype, so (strain × condition) tuples are comparable across all datasets. Also align WoM metabolite identifiers.
- **Method**:
  - ENIGMA → ChEBI ID (already in brick columns) + concentration (mM) + media category + pH.
  - FB → ChEBI via PubChem/ChEBI API lookup on `condition_1` names + concentration + media.
  - CSP → ChEBI via phenotype name → compound name mapping.
  - WoM → ChEBI via compound table.
  - Fallback strategy: Plan A (exact sdt_condition/FB ID match), Plan B (ChEBI), Plan C (fuzzy string), Plan D (condition-class pooling). See Condition-Alignment Fallback Strategy section.
- **Output**: `data/condition_canonical.parquet`, `data/cross_dataset_alignment.tsv`, alignment coverage figures.

#### NB03: Functional diversity census
- **Goal**: Characterize the phylogenetic breadth, metabolic diversity, and ecological functional repertoire of the 123-strain collection. Identify metabolically distinct classes expected to have different growth phenotypes.
- **Method**:
  - **Phylogenetic placement**: Build a genus/family tree from genome depot taxonomy. Map strains to GTDB clades. Compute phylogenetic diversity metrics (Faith's PD, mean pairwise distance).
  - **Metabolic guild clustering**: Build (123 strains × ~2,000 KO) presence/absence matrix from genome depot. Cluster by Jaccard distance (hierarchical + UMAP). Label guilds by enriched KEGG pathways/modules. For the 32 pangenome-linked strains, overlay GapMind pathway completeness profiles.
  - **Functional repertoire inventory**: Per strain, count resistance genes (AMR from bakta_amr where available, or by KO annotation), motility genes (flagellar assembly KOs), secretion systems, mobile element markers, two-component systems, sigma factors.
  - **Pangenome outlier detection**: For strains in BERDL pangenome, compare their KO profile to the species clade average. Flag strains with significant deviations (>2σ in KO count or unique KOs absent from >90% of the clade).
- **Output**: `data/functional_census.parquet` (123 × features), `data/metabolic_guilds.tsv`, figures (phylo tree, UMAP of metabolic profiles, guild bar charts, outlier scatter).

#### NB04: Environmental context and biogeography
- **Goal**: Map the 123 isolates and their relatives to local and global environmental distributions. Identify co-occurring taxa and correlations with geochemical features. Contextualize growth predictions in terms of where these organisms live and what conditions they face.
- **Method — four panels**:

  **Panel A — Pangenome species-level biogeography** (32 pangenome-linked strains):
  - For each strain's GTDB species clade, query `kbase_ke_pangenome.ncbi_env` for all genomes in the clade. Extract isolation source, geographic coordinates, ENVO/GOLD ecosystem terms.
  - Aggregate: per-clade environmental distribution (% host-associated, % soil, % freshwater, % engineered). Map global occurrence.
  - Output: species-level environment profiles for each pangenome-linked strain.

  **Panel B — Microbeatlas global 16S biogeography** (all 123 strains at genus level):
  - Query `arkinlab_microbeatlas.otu_counts_long` for OTUs classified to ENIGMA genera (Pseudomonas, Acidovorax, Rhodanobacter, Pedobacter, Cupriavidus, Sphingobium, etc.).
  - Join to `enriched_metadata_gee` for environmental predictors: soil pH (6 depths), temperature, precipitation, soil metals (Co, Cr, Cu, Ni, Zn, Pb, U, As), EPA Superfund proximity, land cover, NDVI.
  - Build genus × environment association models (logistic regression of genus presence/absence on environmental features; random forest variable importance for each genus).
  - Output: global distribution maps per genus, genus-environment association tables.
  - Scale: ~464K samples, 389K geolocated, all 6+ ENIGMA genera detected in 12K-91K samples each.

  **Panel C — CORAL local Oak Ridge spatial analysis** (123 strains):
  - Link strains to isolation wells via `enigma_coral.ddt_brick0000510` (3,150 strains → 58 wells).
  - Overlay with geochemistry from `ddt_brick0000080` (1,888 samples, ~50 elements at ppb) and `ddt_brick0000010` (micromolar U, NO₃, metals).
  - Join to 100 Well Survey ASV community profiles (`ddt_brick0000476`, 587 communities × 111K ASVs) via sample location.
  - Map which strains come from contaminated vs. background wells; correlate strain metabolic guild (from NB03) with local geochemistry.
  - Output: strain × well × geochemistry linkage table, spatial distribution figures.

  **Panel D — Co-occurrence network** (SparCC):
  - Build co-occurrence network from 100WS ASV community data (587 communities). Use SparCC (Friedman & Alm 2012) or FlashWeave to infer genus-genus correlations robust to compositionality.
  - Focus on ENIGMA growth-curve genera: which taxa co-occur, which are mutually exclusive?
  - For co-occurring genus pairs, test whether they have complementary metabolic capabilities (from NB03 guild clustering): e.g., a fermenter + a respirer, or a metal reducer + a metal oxidizer.
  - Optionally validate global co-occurrence patterns in microbeatlas.
  - Output: co-occurrence network (edge list + significance), complementarity analysis for top pairs.

### Act II — Predict and Explain (NB05-NB08)

#### NB05: Feature engineering [DONE]
- **Status**: Complete. Modeling tables assembled.
- **Feature selection**: Prevalence-based filtering on all 123 strains: remove 456 core KOs (p > 0.95) and 2,406 rare KOs (p < 0.05), retain **4,305 informative KOs** (0.05 ≤ p ≤ 0.95) plus 23 COG class counts. This is a principled, target-independent filter with clear biological rationale: core KOs have no discriminative power; rare KOs are too sparse for statistical learning.
- **No PCA**: KO identity is preserved throughout — every selected feature is a named KEGG ortholog with functional annotation. GBDT handles the 4,305-dimensional feature space via internal regularization (tree splits, feature subsampling, leaf constraints). Interpretability comes from SHAP on named KOs, not from opaque principal components.
- **Four feature levels**:
  - **L0 — Phylogeny** (28 features): GTDB order + metabolic guild (one-hot encoded)
  - **L1 — Bulk scalars** (8 features): genome size, gene count, contigs, unique KOs, coding density, operons, rRNA copies, tRNA copies
  - **L2 — Specific features** (4,328 features): 4,305 prevalence-filtered KO presence/absence + 23 COG class counts
  - **L3 — Condition** (7 features): condition class (carbon/amino acid/metal/antibiotic/nitrogen/nucleoside/other) + log(concentration)
- **Two modeling tables**:
  - `anchor_gbdt_table.parquet`: 486 pairs × 4,371 features (for GBDT — all KOs)
  - `anchor_linear_table.parquet`: 486 pairs × 116 features (for baseline comparisons if needed)
- **CV structure**: 7 leave-one-strain-out folds (4 Pseudomonas_E, 1 Cupriavidus, 1 Acidovorax, 1 Pedobacter)
- **Output**: `data/features/`, `data/modeling/`

#### NB06: GBDT variance partitioning + SHAP + FB concordance
- **Goal**: The central analytical notebook. Decompose growth phenotype variance using GBDT at each feature level, extract interpretable feature attributions via SHAP, and validate biological meaningfulness against independent Fitness Browser gene fitness data.
- **Why GBDT throughout** (not linear models): Growth phenotype depends on non-linear gene interactions (epistasis, threshold effects, condition-dependent gene importance). Linear models underestimate L2 contributions because they can't capture these effects. Using the same non-linear model (LightGBM) at every level ensures fair comparison — the only thing that changes between M0 and M3 is which features the model sees.
- **Method — Variance partitioning via nested GBDT**:
  For each phenotype target (binary growth, µmax, lag, max_A, AUC):
  - **M0**: LightGBM on L0 features only (28 phylogeny) → leave-one-strain-out CV → R² (or AUC for binary)
  - **M1**: LightGBM on L0 + L1 (36 features) → CV R²
  - **M2**: LightGBM on L0 + L1 + L2 (4,364 features) → CV R²
  - **M3**: LightGBM on L0 + L1 + L2 + L3 (4,371 features) → CV R²
  - **Incremental contribution** of each level = R²(Mi) - R²(Mi-1). This answers: "how much predictive power does adding KO-level features provide after phylogeny and bulk scalars are already in the model?"
  - LightGBM hyperparameters: `num_leaves=31, min_data_in_leaf=10, feature_fraction=0.5, learning_rate=0.05, n_estimators=200, reg_alpha=0.1, reg_lambda=1.0`. These provide regularization that prevents overfitting on the 486-pair dataset despite 4,000+ features.
- **Method — SHAP feature attribution**:
  - On the full M3 model, compute SHAP values for every prediction.
  - Report global feature importance (mean |SHAP|) and per-condition-class importance.
  - Each important feature is a named KO — directly mappable to KEGG pathway/module annotations.
  - Recursive feature importance: after identifying top-50 SHAP features, refit M3 with only those features and report CV R² to assess whether a compact mechanistic model captures most of the signal.
- **Method — FB concordance (biological meaningfulness)**:
  - For each (strain, condition) in the anchor set with FB fitness data:
    1. Extract top-K SHAP features (K = 10, 50, 100) from M3.
    2. Map KO → FB locus via genome depot gene → `fb_pangenome_link.tsv`.
    3. Compute FB concordance = fraction of mapped loci with |t| > 4 in matched FB experiment.
  - Compare concordance across models M0-M3: does adding KO features (M2) increase FB concordance relative to phylogeny-only (M0)?
  - Scatter plot: held-out accuracy vs. FB concordance — are they correlated or independent axes?
- **Method — Baseline comparisons**:
  - **GapMind baseline**: For carbon-source conditions with pangenome-linked strains, predict growth from pathway completeness score. Rule-based for binary.
  - **Taxonomy-only baseline**: Predict from GTDB genus alone (majority vote by genus). This is the "phylogeny explains everything" null.
- **Output**: `data/variance_partition.tsv`, `data/shap_importance.tsv`, `data/fb_concordance.tsv`, `data/model_predictions.tsv`, figures (stacked bar of incremental R², SHAP beeswarm, accuracy-vs-concordance scatter, per-condition-class feature importance).

#### NB07: Condition-specific prediction via GapMind baseline + CSP pretraining + interaction features
- **Goal**: Build the predictor that works for NEW genomes on SPECIFIC conditions — the core project deliverable. NB06 showed that genome-scale features dominate with n=7; NB07 overcomes this by adding condition-aware features and expanding training data.
- **Method — GapMind baseline** (amino acid + carbon source conditions only):
  - For each (genome, condition) pair where GapMind has a relevant pathway, predict growth from pathway completeness score. This asks "does this genome have the pathway for this condition?" — mechanistic, interpretable, condition-specific.
  - For the ~32 pangenome-linked strains with GapMind data, evaluate against the measured growth curves.
  - Expected: high precision (pathway complete → usually grows), moderate recall (missing pathway ≠ always no-growth due to alternative pathways), zero coverage for metals/antibiotics.
- **Method — CSP-pretrained GBDT with condition-aware features**:
  - Train LightGBM on the 795-genome CSP corpus (53K binary labels, KofamScan KO features).
  - Key innovation: **KO × condition interaction features** — for each (genome, condition), compute "number of KOs in the KEGG module relevant to this condition" using KEGG module → KO mappings. This transforms generic KO presence into condition-specific predictions.
  - Apply to ENIGMA strains by mapping depot KO annotations to KofamScan KO space.
  - Compare: CSP-pretrained vs. ENIGMA-only vs. GapMind baseline.
- **Method — Continuous parameter prediction**:
  - After validating binary growth with CSP pretraining, train regression models for µmax/lag/yield.
  - Two approaches: (a) CSP binary → fine-tune on ENIGMA continuous, (b) train directly on ENIGMA continuous with CSP-derived KO importance as feature weights.
- **Method — FB concordance validation**:
  - For the best-performing model, compute FB concordance on the 7 anchor strains.
  - Map top-SHAP KOs to FB loci via `fb_pangenome_link.tsv`.
  - Test: do condition-specific predictive KOs show significant fitness effects under matched FB conditions?
- **Output**: `data/gapmind_predictions.tsv`, `data/csp_transfer_results.tsv`, `data/fb_concordance.tsv`, comparison figures, per-condition confidence scores.

#### NB08: WoM exometabolomic prediction (pilot)
- **Goal**: For the 6 WoM-profiled strains, test whether growth-predictive KOs also predict metabolite production.
- **Method**:
  - Use the same GBDT architecture and KO features as NB06 M3.
  - Predict: which of 105 WoM metabolites are Emerged / Increased / No Change?
  - Test SHAP feature overlap between growth and metabolite production.
  - Cross-reference with `fw300_metabolic_consistency` tryptophan overflow finding.
- **Output**: `data/wom_predictions.tsv`, feature overlap analysis, figures.

### Act III — Diagnose and Propose (NB10-NB11)

#### NB10: Conflict detection and counterfactuals
- **Goal**: Identify (strain, condition) pairs where models disagree or where close relatives diverge, for active learning prioritization.
- **Method**:
  - Model disagreement: prediction variance across GapMind / CUB / GBDT variants.
  - Near-neighbor divergence: strains sharing a genus or OG cluster but with divergent growth outcomes.
  - Replicate inconsistency: high within-condition CV in growth parameters.
  - Diagnose likely causes: conflicting data (measurement error?), insufficient features (regulatory gap?), genuine biological variation (strain-specific regulation?).
- **Output**: `data/conflict_ranked.tsv`, diagnostic figures.

#### NB11: Active learning proposal
- **Goal**: Rank the next 200 (strain × condition) experiments for ENIGMA.
- **Method**:
  - Score = (model disagreement) × (genotype-space novelty) × (FB-concordance weight) × (experimental feasibility).
  - Retrospective validation: subsample current data, show proposed points improve accuracy faster than random.
  - Consider field relevance: prioritize conditions relevant to Oak Ridge (metals, nitrate, low pH, complex carbon) informed by NB04 environmental context.
- **Output**: `data/proposed_experiments.tsv` (top 200), retrospective learning curve figure.

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

- **If H1 holds** (feature resolution × phenotype resolution): We identify which genomic feature level (pathway → KO → regulatory) is the natural predictor for each phenotype target class. This would be a practical guide: "use GapMind for carbon source growth prediction, use KO profiles for kinetic parameters, use regulatory proxies for complex dynamics."
- **If H2 holds** (paradigm complementarity): GapMind, CUB/gRodon, and GBDT have complementary strengths by condition class. An ensemble that selects paradigm per condition type outperforms any single paradigm. Methodological contribution: paradigm selection depends on condition class, not just dataset size.
- **If H3 holds** (biological meaningfulness): FB concordance is independently measurable and separable from accuracy. This establishes a new evaluation axis for genotype-phenotype predictors beyond held-out error.
- **If H4 holds** (CSP transfer): Pretraining on 795-genome binary corpus improves continuous target prediction on ENIGMA strains. Practical contribution: literature-curated phenotype databases are useful as transfer learning priors for lab-specific growth data.
- **If H5 holds** (exometabolomic prediction): Growth-predictive KOs overlap with metabolite-production-predictive KOs. Conceptual contribution: "will it grow?" and "what will it produce?" share a common genomic basis.
- **If H6 holds** (active learning): The proposed experimental set outperforms random sampling. Practical deliverable for ENIGMA's next experimental round.
- **If all H0 hold**: A calibrated negative result on a substantial scale — published as a benchmark showing where current methods fail and what data are needed.

### Potential confounders and limitations
- **7 FB-anchor strains** for the deepest validation. Small n for per-strain leave-one-out. Mitigated by CSP pretraining (795 genomes) and phylogenetically blocked CV.
- **Growth curve QC**: 35.7% fit_ok. Mitigated by recoding no-growth as a valid binary label (biologically correct) and by continuous quality weights in the loss function.
- **Condition alignment**: Depends on ChEBI ID coverage. Fallback strategy (Plans A-D) covers the spectrum from gold-standard to class-pooled.
- **Phylogenetic confounding**: The dominant confounder. Addressed by Phydon-style blocked CV, adversarial validation, and explicit variance partitioning (NB06).
- **Regulatory features are proxies**: Pfam-domain counts for sigma factors and TCS are not true network topology. Interpretability is bounded.
- **WoM pilot is thin**: Only 6 strains. H5 is a proof-of-concept, not a definitive test.
- **Biogeography is genus-level** for 16S data (microbeatlas). Species-level resolution available only for 32 pangenome-linked strains via `ncbi_env`.

## Execution Environment

| Notebook | Environment | Rationale |
|---|---|---|
| NB00 (data survey) | JupyterHub (Spark) | Queries across 303 bricks + FB + CSP + depot |
| NB01 (curve fitting) | JupyterHub (Spark reads) + local (scipy fits) | Brick reads require Spark; fitting is CPU-only |
| NB02 (condition canon.) | JupyterHub (Spark) + local (ChEBI lookup) | One-time extraction from FB/WoM/CSP |
| NB03 (functional census) | JupyterHub (Spark) | Genome depot KO/COG/OG queries for 123 strains |
| NB04 (env context) | JupyterHub (Spark) | microbeatlas (464K samples), CORAL bricks, pangenome ncbi_env |
| NB05 (features) [done] | JupyterHub (Spark) | Depot + pangenome queries for feature matrices |
| NB06 (GBDT + SHAP + FB) | Local (LightGBM) | Nested GBDT M0-M3, SHAP, FB concordance |
| NB07 (CSP transfer) | Local (LightGBM) | Pretraining on 795 CSP genomes |
| NB08 (WoM prediction) | Local | 6 strains × 105 metabolites |
| NB09-NB10 (diagnosis + AL) | Local | Scoring + ranking |

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

- **v5** (2026-04-18): Act II methodology revision — GBDT-throughout, no PCA.
  - **Merged NB06+NB07+NB08 into NB06**: Variance partitioning, SHAP, and FB concordance are now one notebook. All use GBDT (LightGBM) — no linear models, no PCA. The incremental R² from nested GBDT models (M0→M3) replaces the planned linear variance decomposition. Non-linear effects (gene interactions, threshold responses) are captured at every level.
  - **Principled KO selection**: Replaced arbitrary "top-100 by variance" with prevalence-based filtering: remove 456 core KOs (p > 0.95) and 2,406 rare KOs (p < 0.05), retain 4,305 informative KOs. Rationale: core KOs have no discriminative power; rare KOs are too sparse for statistical learning. GBDT handles the 4,305-dimensional space via internal regularization — no need for pre-selection.
  - **No PCA**: KO identity preserved throughout for interpretability. Every SHAP-important feature is a named KEGG ortholog, not an opaque principal component. GBDT handles dimensionality via tree splits + feature subsampling.
  - **Act II simplified**: 5 notebooks → 4 (NB05 features [done], NB06 variance partition + SHAP + FB concordance, NB07 CSP transfer, NB08 WoM prediction).
  - **CSP transfer moved to NB07**: Separate notebook for pretraining comparison (CSP binary → ENIGMA continuous fine-tuning).

- **v4** (2026-04-18): Three-act restructure with ENIGMA SFA context, biogeography, functional census, and variance partitioning.
  - **ENIGMA SFA context added**: New section describing Oak Ridge field site geology (fractured shale, contamination plumes, uranium/metals/nitrate/low-pH), carbon dynamics (simple C consumed rapidly, complex C persists), and how growth predictions relate to field community dynamics.
  - **Analysis plan restructured to three acts**: Act I (Know the Collection: NB01-NB04), Act II (Predict and Explain: NB05-NB09), Act III (Diagnose and Propose: NB10-NB11).
  - **NB03 added — Functional diversity census**: Phylogenetic breadth, metabolic guild clustering from KO profiles, resistance/motility/mobile element inventory, pangenome outlier detection. Produces the *a priori* classification of metabolically distinct types.
  - **NB04 added — Environmental context and biogeography (four panels)**: Panel A: pangenome species-level biogeography via `ncbi_env` for 32 strains. Panel B: microbeatlas global 16S (464K samples, genus-level, with soil pH/metals/temperature metadata). Panel C: CORAL local Oak Ridge spatial analysis (100WS communities + geochemistry + strain isolation wells). Panel D: SparCC co-occurrence network from 100WS ASV data (587 communities × 111K ASVs) + metabolic complementarity test.
  - **NB06 added — Variance partitioning as central framework**: Nested models at four feature levels (phylogeny → bulk scalars → specific KOs → condition interactions). Phylogenetically blocked CV (Xu et al. 2025). This replaces the old "compare paradigms" framing with a principled decomposition of what genomic information matters at what level.
  - **FBA cut**: GapMind pathway completeness and KO presence already capture the mechanistic signal. FBA reconstruction cost not justified for marginal gain.
  - **CUB/gRodon baseline added**: Codon usage bias prediction of µmax per Xu et al. 2025. Cheap to compute, provides Phydon comparison.
  - **Phylogenetically blocked CV adopted**: Tree-cutting strategy from Xu et al. as primary evaluation in NB06/NB07.
  - **Literature updated**: Added Phydon (Xu et al. 2025), SparCC (Friedman & Alm 2012), EMP (Thompson et al. 2017), WoM (Kosina et al. 2018).
  - **Biogeography data sources mapped**: `arkinlab_microbeatlas` (464K samples, all 6+ ENIGMA genera detected in 12K-91K samples), `enigma_coral` CORAL bricks (100WS 587 communities, geochemistry bricks 80/10/72/73, isolation mapping brick 510), `kbase_ke_pangenome.ncbi_env` (4.1M records for pangenome-linked strains).

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

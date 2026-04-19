# Report: Genotype x Condition to Phenotype Prediction from ENIGMA Growth Curves

## Act I — Know the Collection

### Key Findings

#### 1. A dense multi-dataset anchor set enables genotype-phenotype modeling

![Condition overlap across 4 datasets](figures/NB02_condition_overlap_4way.png)

The ENIGMA growth curve corpus (27,632 curves across 123 strains and 195 molecules) aligns with Fitness Browser RB-TnSeq data through **486 (strain x condition) anchor pairs** — 7 strains x 72 conditions where growth curves, gene fitness, and genome annotations all coexist. Media names (RCH2_defined_noCarbon, LB, R2A, M9) match exactly between ENIGMA and FB, and 42 molecules align by normalized compound name. Of the 486 anchor pairs, 275 (56.6%) show measurable growth — providing balanced positive and negative labels for binary prediction. Five conditions (cytidine, glycine, inosine, thymidine, uridine) are present in all four datasets (ENIGMA, FB, carbon source phenotype corpus, Web of Microbes), with 30 in three.

![Anchor strain growth heatmap](figures/NB02_anchor_growth_heatmap.png)

An additional 795-genome carbon source phenotype corpus (`globalusers_carbon_source_phenotypes`, 379 binary phenotypes, pre-computed KofamScan KO and BacFormer embeddings; Dileep et al., preprint in preparation) is available for pretraining. The full coverage matrix spans 13,632 (strain x condition) pairs across all 123 strains x 194 conditions.

*(Notebooks: NB00_data_survey.ipynb, NB02_condition_canonicalization.ipynb)*

#### 2. Growth curves reveal a 55% no-growth majority with structured kinetic variation

![Growth corpus statistics](figures/NB01_parameter_distributions.png)

Of 27,632 wells across 303 plates, 15,227 (55.1%) show no detectable growth — a biological signal reflecting substrate incompatibility or stress lethality, not a measurement failure. Among the 9,861 fit-ok curves (35.7%), modified Gompertz fitting achieves median R^2 = 0.98 with the following parameter distributions: median mumax = 0.028 h^-1 (doubling time ~24.5 h), median lag = 11.4 h, median asymptotic OD increase (A) = 0.315. Diauxy is common: 40% of fit-ok curves show >=2 growth phases in their smoothed derivative, suggesting sequential substrate utilization is widespread among Oak Ridge isolates.

![Example curve fits](figures/NB01_curve_fit_examples.png)

Pseudomonas anchor strains show 43-61% growth across conditions (metabolic generalists); Pedobacter (23.5%) and Acidovorax (22.4%) show much lower rates, consistent with more specialized metabolic repertoires. The no-growth fraction is itself a prediction target — these are conditions where the genome predicts growth should not occur.

![QC summary across all plates](figures/NB01_qc_summary.png)

*(Notebook: NB01_curve_fitting.ipynb)*

#### 3. Eight metabolic guilds partition the 123-strain collection

![KO profile PCA colored by guild and taxonomy](figures/NB03_ko_pca_guilds.png)

Hierarchical clustering on KO presence/absence (Jaccard distance, 7,167 unique KOs across 123 strains) identifies 8 metabolic guilds spanning 20 taxonomic orders. Guilds align with but are not identical to taxonomy — they are defined by functional gene content, not phylogeny. The Pseudomonas_E guild (27 strains, avg 2,658 KOs) contains 5 of 7 FB-anchor strains, making it the best-sampled for modeling. Genome sizes range from 2.6 to 11.4 Mb with strong correlation to KO diversity (1,256-3,014 unique KOs per strain, median 2,121).

![COG functional profiles by guild](figures/NB03_cog_by_guild.png)

The Flavobacteriales guild (6 strains, avg 1,372 KOs) has the fewest functional genes and represents the hardest out-of-distribution prediction target. COG class profiles show guild-specific functional enrichment, with the largest differences in categories L (replication/repair/recombination) and M (cell wall/membrane biogenesis).

![Genome size vs KO diversity](figures/NB03_genome_vs_ko.png)

*(Notebook: NB03_functional_census.ipynb)*

#### 4. ENIGMA strains are ecological outliers within their genera

![Genus environment heatmap](figures/NB04_genus_env_heatmap.png)

Genus-level environmental profiling across all GTDB genomes reveals that Pseudomonas globally is 37.8% clinical (driven by P. aeruginosa), 12.9% soil/plant, and 9.4% aquatic. However, all ENIGMA Pseudomonas belong to Pseudomonas_E (the fluorescens/protegens clade) — environmental, not clinical. Rhodanobacter is purely aquatic/contaminated (55% aquatic, 10% contaminated, 0% clinical). This means ENIGMA's subsurface field isolates occupy environmental niches underrepresented in the NCBI genome collection. Transfer learning from clinical phenotype databases may be biased.

![Pangenome species environment profiles](figures/NB04_pangenome_env_profiles.png)

All 14 ENIGMA genera are globally ubiquitous — detected in 4,086-288,686 of 464,000 samples in the Microbial Atlas 16S database. Caulobacter is the most widespread (289K samples), followed by Rhodanobacter (228K) and Pseudomonas (206K). These are ecologically significant genera, not rare specialists.

![Global genus occurrence](figures/NB04_global_genus_occurrence.png)

*(Notebook: NB04_environmental_context.ipynb)*

#### 5. A global pH-driven niche partition explains local co-occurrence at Oak Ridge

![Oak Ridge co-occurrence matrix](figures/NB04_oakridge_cooccurrence.png)

Spearman correlation across 587 100-Well-Survey communities identifies two anti-correlated genus clusters with 47 significant pairs (|rho| > 0.2, p < 0.01). Cluster A (Brevundimonas-Caulobacter-Sphingomonas-Variovorax-Sphingobium; strongest pair rho = +0.56) and Cluster B (Rhodanobacter-Ralstonia-Dyella-Serratia-Comamonas; rho = +0.40) are negatively correlated with each other (Brevundimonas-Rhodanobacter rho = -0.34).

![Global co-occurrence matrix](figures/NB04_global_cooccurrence.png)

Environmental characterization of these clusters across 464K global 16S samples reveals a striking pH gradient: Cluster B environments average pH 5.4 (1.35 units more acidic than Cluster A's 6.8) and are 6.9 degrees C warmer. This mirrors the Oak Ridge contamination gradient where nitric acid leachate lowers pH in plume wells. The co-occurrence pattern is **not site-specific but reflects a global pH-driven niche partition**. Cluster B organisms are acid-tolerant generalists enriched wherever pH drops — contamination sites, peatlands, and acidic soils. Cluster A organisms prefer neutral, cooler conditions typical of uncontaminated groundwater.

![Cluster environment comparison](figures/NB04_cluster_env_comparison.png)

This has direct implications for growth phenotype prediction: strains from Cluster B (acid-tolerant) should show different pH-dependent growth profiles than Cluster A strains, and the genomic features distinguishing the clusters should be predictive of pH tolerance.

![Well guild distribution](figures/NB04_well_guild_distribution.png)

![Strain isolation map](figures/NB04_oak_ridge_strain_map.png)

*(Notebook: NB04_environmental_context.ipynb)*

#### 6. A strain-name collision pitfall was discovered and documented

Matching ENIGMA strains to the BERDL pangenome via `ncbi_strain_identifiers` caused 12 of 32 genus-level mismatches. Short names like MT20 (ENIGMA: *Rhodanobacter glycinis*) matched unrelated NCBI organisms (*Streptococcus pneumoniae*), injecting 1,751 spurious clinical genomes into environmental profiles. The fix — using CORAL brick 522 (GTDB-Tk assignments) for authoritative taxonomy and cross-checking genus consistency — reduced verified linkages from 32 to 20 but eliminated all false matches. This pitfall is documented in `docs/pitfalls.md` and affects any project linking ENIGMA strains to the pangenome by name.

*(Notebooks: NB04_environmental_context.ipynb)*

### Act II — Predict and Explain (preliminary results)

**Status note**: Act II produced useful diagnostic results and initial models but the modeling work is preliminary. Key planned analyses — KO x condition interaction features, per-condition prediction quality, cross-genus holdout validation, continuous parameter prediction, and FB concordance — remain to be done. The findings below represent first-pass explorations that frame the right questions, not definitive answers.

#### 7. Feature engineering: 4,305 prevalence-filtered KOs preserve interpretability

![Feature summary](figures/NB05_feature_summary.png)

The modeling table comprises 486 anchor pairs (7 strains x 72 conditions) with features organized into four hierarchical levels: L0 Phylogeny (28), L1 Bulk scalars (8), L2 Specific features (4,305 prevalence-filtered KOs + 23 COG classes), and L3 Condition class + concentration (7). KO selection uses a principled prevalence filter: remove 456 core KOs (p > 0.95, no discriminative power) and 2,406 rare KOs (p < 0.05, too sparse), retaining 4,305 informative KOs as named KEGG orthologs for SHAP interpretability. No PCA — every feature is a named KO.

![KO prevalence filter](figures/NB05_ko_prevalence_filter.png)

![Target distributions](figures/NB05_target_distributions.png)

*(Notebook: NB05_feature_engineering.ipynb)*

#### 8. Initial variance partitioning: genome scale + condition class dominate with n=7

![Variance partitioning](figures/NB06_variance_partition.png)

Nested GBDT models (LightGBM, leave-one-strain-out CV, 486 pairs) achieve AUC 0.633 (binary growth) with the full feature set. SHAP analysis with correlation grouping (|r| > 0.8 connected components) reveals the signal is dominated by a **63-feature genome-scale axis** (25.3% of total SHAP: genome size, gene count, operons, rRNA/tRNA, and co-inherited KOs/COGs) and **condition class** (45.9%: amino acid, carbon source, metal, etc.). Specific KO gene blocks — membrane adaptation, tRNA modification, aromatic catabolism, flagellar motility — contribute ~2% each but are biologically coherent.

![Group-level SHAP importance](figures/NB06_group_shap.png)

![Top 20 SHAP features](figures/NB06_shap_top20.png)

![Feature correlation matrix](figures/NB06_feature_correlation.png)

Continuous targets (mumax, lag, max_A) show negative R^2 — not predictable cross-strain with n=7.

**Limitation**: This analysis uses leave-one-strain-out on 7 strains (4 Pseudomonas_E, 1 each Cupriavidus, Acidovorax, Pedobacter). It does NOT test cross-genus generalization (e.g., train on Pseudomonas, predict Pedobacter), does NOT analyze per-condition prediction quality, and does NOT use condition-specific features. The model effectively learns "big genomes grow on amino acids" — biologically real but not the condition-specific prediction needed for practical use.

*(Notebook: NB06_variance_partition.ipynb)*

#### 9. Preliminary condition-specific models: GapMind and CSP transfer show promise on matched conditions

![Model comparison](figures/NB07_model_comparison.png)

Three approaches were compared for binary growth prediction:

| Model | AUC | Accuracy | Coverage | What it tests |
|---|---|---|---|---|
| ENIGMA-only GBDT (NB06) | 0.633 | — | 100% | Generic KO features, n=7 |
| GapMind baseline | 0.646 | 78.8% | 24.3% | Pathway completeness for AA/carbon |
| CSP transfer (matched) | 0.800 | 76.8% | 23% | CSP-trained KOs on matched conditions |
| CSP internal (5-fold) | 0.858 | — | CSP | Achievable ceiling with sufficient data |

GapMind achieves 96.5% recall and 79% precision on 118 testable pairs — it almost never misses a grower but sometimes predicts growth when the pathway is present but unused. CSP transfer reaches AUC 0.800 on the 23% of conditions that match the CSP training set.

![Coverage gap](figures/NB07_coverage_gap.png)

**The coverage gap**: ~76% of ENIGMA conditions (metals, antibiotics, nitrogen, stress) have neither GapMind pathway coverage nor CSP training data. Prediction on these conditions falls to AUC ~0.63 (no better than generic KO features).

**What this analysis does NOT include** (planned but not yet executed):
- KO x condition interaction features (the key innovation that would make predictions condition-specific)
- Cross-genus holdout (train on Pseudomonas, test on Pedobacter/Acidovorax/Cupriavidus)
- Per-condition accuracy breakdown (which specific conditions are predictable?)
- SHAP analysis on CSP model (which KOs matter for which conditions?)
- Continuous growth parameter prediction (mumax, lag, yield)
- FB concordance validation (do predictive KOs have significant fitness effects?)
- Combined ENIGMA+CSP model with shared feature space

*(Notebook: NB07_condition_specific_prediction.ipynb)*

## Results

### Data scale summary

| Dataset | Scale | Key metric |
|---|---|---|
| ENIGMA growth curves | 303 plates, 27,632 curves, 7.57M timepoints | 123 strains x 195 molecules |
| ENIGMA Genome Depot | 3,110 genomes, 6.8M proteins | 3.7M KO, 6.4M COG annotations |
| Fitness Browser | 7 anchor strains, 27M fitness scores | 486 anchor (strain x condition) pairs |
| Web of Microbes | 6 strains, 630 metabolite observations | 105 compounds per strain |
| Carbon Source Phenotypes | 795 genomes x 379 conditions | ~53K binary growth labels |
| Microbial Atlas (16S) | 464K samples, 260M OTU counts | 14 ENIGMA genera in 4K-289K samples each |
| CORAL (local) | 596 locations, 587 ASV communities | 123 strains mapped to 24 wells |

### Growth curve parameter distributions (fit-ok subset, n=9,861)

| Parameter | Median | IQR | Range |
|---|---|---|---|
| mumax (h^-1) | 0.028 | 0.017-0.048 | 0.001-0.50 |
| Lag (h) | 11.4 | 5.2-18.5 | 0-48 |
| Asymptotic A (OD) | 0.315 | 0.14-0.66 | 0.05-2.77 |
| R^2 | 0.980 | 0.96-0.99 | 0.80-1.00 |
| AUC (OD*h) | 15.8 | 5.5-31.5 | 0.3-98 |

### Condition alignment

| Overlap | Count | Examples |
|---|---|---|
| All 4 datasets | 5 | cytidine, glycine, inosine, thymidine, uridine |
| 3 datasets | 30 | acetate, citrate, ethanol, glycerol, pyruvate, succinate... |
| 2 datasets | 107 | Various carbon sources, amino acids, metals, antibiotics |
| Dense anchor set | 486 pairs | 7 FB-anchor strains x 72 conditions |

### Co-occurrence cluster environmental niche comparison

| Feature | Cluster A (neutral pH) | Cluster B (acidic) | Delta |
|---|---|---|---|
| Mean pH | 6.78 | 5.43 | -1.35 |
| Mean temperature | 15.7 C | 22.6 C | +6.9 C |
| Exclusive samples (global) | 179,023 | 3,720 | 48x rarer |
| Dominant environments | aquatic 33%, plant 23%, soil 22% | aquatic 39%, soil 23%, plant 18% |

## Interpretation

### What we have learned

Act I established an unprecedented multi-dataset foundation: 486 anchor pairs where growth curves, gene fitness, and genome annotations coexist, 8 metabolic guilds across 123 strains, and a global pH-driven niche partition connecting Oak Ridge co-occurrence to 464K global 16S samples.

Act II's variance partitioning (NB06) provides a sobering but instructive diagnostic: **with only 7 anchor strains, binary growth is weakly predictable (AUC 0.633) and continuous kinetics are not predictable (negative R^2)**. The dominant predictors are genome scale (25.3%) and condition class (45.9%), not specific gene-condition interactions. This reveals the fundamental bottleneck: the model learns "big genomes grow on most substrates" — biologically real but not the condition-specific prediction we need for practical applications.

### The path forward

The Act II preliminary results reveal a fundamental framing error: we treated 7 FB-anchor strains as the training set, creating an artificial n=7 bottleneck. In reality, we have **13,632 ENIGMA (strain x condition) pairs** (123 strains, all with growth curves + genome depot KOs) plus **53K CSP pairs** (795 genomes with binary phenotypes). The 7 FB-anchor strains should serve as the VALIDATION set for biological meaningfulness (FB concordance), not as the primary training data.

The revised modeling approach:

1. **Full-corpus training**: Pool all 123 ENIGMA strains (13,632 pairs with binary growth + continuous parameters) and 795 CSP genomes (53K binary growth pairs) into a shared KO feature space (6,360 KOs shared between genome depot and KofamScan). Train on ~67K total pairs.

2. **Genus-level blocked holdout**: Train on all but one genus, predict that genus. With 20+ genera across ENIGMA + CSP, this provides robust generalization estimates and tests whether KO features truly predict growth beyond phylogenetic signal.

3. **Per-condition analysis**: For each of the 194 ENIGMA conditions and 379 CSP conditions, report prediction accuracy separately. Identify which conditions are well-predicted (likely those with condition-specific KO associations) vs. poorly predicted (likely metals, antibiotics, stress).

4. **KO x condition interaction features**: For each (genome, condition) pair, compute condition-specific features: "does this genome have the KOs in the KEGG module relevant to this condition?" This transforms generic KO presence into condition-aware prediction.

5. **Continuous parameter prediction**: With 123 strains providing µmax/lag/yield data (9,861 fit-ok curves), the regression task has much more power than n=7.

6. **FB concordance on the 7-strain validation set**: After training on the full corpus, check whether the model's top SHAP features for the 7 FB-anchor strains correspond to genes with significant fitness effects — the biological meaningfulness check.

7. **SHAP per condition class**: Which KOs matter for growth on amino acids vs. carbon sources vs. metals? This is the mechanistic insight the project should deliver.

8. **Confidence estimation**: Model disagreement between GapMind (pathway-based, high-confidence for AA/carbon) and full-corpus GBDT (data-driven, broader coverage) naturally defines when predictions should be trusted.

### The pH finding in context

The global pH-driven niche partition (Finding 5) is the most unexpected result. Green et al. (2012) showed Rhodanobacter dominates acidic Oak Ridge wells, and Smith et al. (2015) showed community composition predicts geochemistry — but neither connected this to a global ecological pattern across 464K samples. Our finding that the Rhodanobacter-Ralstonia-Dyella cluster occupies environments 1.35 pH units more acidic worldwide means this is not site-specific adaptation but a fundamental microbial niche axis. This has direct implications for growth prediction: pH tolerance is a first-order phenotype that any genotype-to-phenotype model must capture.

### Novel Contribution

1. **First integration of ENIGMA growth curves with Fitness Browser gene fitness at condition-matched scale** (486 pairs). Previous work used these datasets separately.
2. **Global environmental validation of local co-occurrence**: the Oak Ridge contamination-gradient co-occurrence pattern is recapitulated across 464K global samples as a pH-driven niche partition, connecting subsurface microbial ecology to global biogeography.
3. **Strain-name collision pitfall**: documented a systematic data integration hazard that affects any project linking field isolates to reference databases by short strain identifiers.

### Limitations

- **Condition alignment is string-based**: 42 molecular matches via normalized names; ChEBI-ID-based canonicalization would likely expand this to 60-80 matches.
- **Growth curve QC**: 35.7% pass rate for Gompertz fitting. The 55% no-growth fraction is biological, but ~9% of curves fail fitting for technical reasons (monotone violations, short duration, edge-well effects).
- **Genus-level biogeography**: Microbial Atlas analysis is at genus level (16S resolution). Species-level biogeography is available for only 20 pangenome-linked strains with verified GTDB matches.
- **Co-occurrence is correlation, not causation**: Spearman co-occurrence suggests shared/exclusive niches but does not prove direct interaction. SparCC analysis (compositionally aware) on the full 100WS ASV matrix would strengthen these findings.
- **No geochemistry linkage yet**: Uranium, nitrate, and metal concentrations per well are available in CORAL bricks 10/80 but sample-to-location name resolution is incomplete.

## Data

### Sources

| Collection | Tables Used | Purpose |
|---|---|---|
| `enigma_coral` | `ddt_brick0000928`-`ddt_brick0001230`, `sdt_strain`, `sdt_genome`, `sdt_condition`, `ddt_brick0000510`, `ddt_brick0000476`, `ddt_brick0000454`, `ddt_brick0000522` | Growth curves, strain metadata, isolation locations, ASV community data, GTDB-Tk taxonomy |
| `enigma_genome_depot_enigma` | `browser_genome`, `browser_strain`, `browser_gene`, `browser_protein`, `browser_protein_kegg_orthologs`, `browser_protein_cog_classes`, `browser_taxon` | Genome annotations (KO, COG, OG, EC, GO) for all 123 strains |
| `kescience_fitnessbrowser` | `organism`, `experiment`, `genefitness`, `gene` | RB-TnSeq fitness data for 7 anchor strains |
| `kescience_webofmicrobes` | `organism`, `observation`, `compound` | Exometabolomics for 6 strains |
| `globalusers_carbon_source_phenotypes` | `genome_table`, `phenotype_data_table`, `phenotype_description_table`, `kofam_annotation_table`, `bacformer_annotation_table` | Binary growth phenotype pretraining corpus |
| `kbase_ke_pangenome` | `genome`, `gtdb_taxonomy_r214v1`, `ncbi_env`, `gtdb_metadata` | Species-level biogeography, pangenome context |
| `arkinlab_microbeatlas` | `otu_counts_long`, `otu_metadata`, `sample_metadata`, `enriched_metadata_gee` | Global 16S biogeography, co-occurrence, environmental metadata |

### Generated Data

| File | Rows | Description |
|---|---|---|
| `data/growth_parameters_all.parquet` | 27,632 | Gompertz-fitted growth parameters per well |
| `data/condition_canonical.tsv` | 1,192 | Cross-dataset condition alignment (4 datasets) |
| `data/anchor_set.tsv` | 486 | Dense anchor (strain x condition) pairs |
| `data/coverage_matrix.tsv` | 13,632 | Full (strain x condition) coverage matrix |
| `data/ko_matrix.parquet` | 123 x 7,167 | KO presence/absence per strain |
| `data/cog_matrix.tsv` | 123 x 23 | COG class gene counts per strain |
| `data/strain_scalars.tsv` | 123 | Genome scalars + guild + GTDB taxonomy |
| `data/genus_env_profiles.tsv` | 52 | Genus-wide environment profiles from GTDB |
| `data/oakridge_genus_cooccurrence.tsv` | 15 x 15 | Spearman co-occurrence matrix (100WS) |
| `data/global_genus_cooccurrence_jaccard.tsv` | 18 x 18 | Jaccard co-occurrence (464K samples) |
| `data/coral_strain_locations.tsv` | 123 | Strain to well to coordinates mapping |
| `data/modeling/anchor_modeling_table.parquet` | 486 x 173 | Full modeling table (features + targets) |
| `data/modeling/cv_folds.tsv` | 7 | Leave-one-strain-out CV fold assignments |
| `data/features/L0_phylogeny.parquet` | 123 x 28 | GTDB order + guild one-hot |
| `data/features/L1_scalars.parquet` | 123 x 8 | Genome size, genes, operons, rRNA, tRNA |
| `data/features/L2_ko_binary.parquet` | 123 x 7167 | Full KO presence/absence matrix |
| `data/features/L2_cog_counts.parquet` | 123 x 23 | COG class gene counts |
| `data/features/L3_condition.parquet` | 72 x 7 | Condition class + concentration features |

## Supporting Evidence

### Notebooks

| Notebook | Purpose |
|---|---|
| `NB00_data_survey.ipynb` | Five-dataset convergence mapping, data availability audit |
| `NB01_curve_fitting.ipynb` | Modified Gompertz fitting of 27,632 growth curves |
| `NB02_condition_canonicalization.ipynb` | Cross-dataset condition alignment, anchor set identification |
| `NB03_functional_census.ipynb` | KO/COG profiling, metabolic guild clustering |
| `NB04_environmental_context.ipynb` | Biogeography (3 scales), co-occurrence, niche characterization |
| `NB05_feature_engineering.ipynb` | 4-level feature hierarchy, modeling table assembly, CV fold structure |
| `NB06_variance_partition.ipynb` | Nested GBDT M0-M3, SHAP, correlation grouping, variance decomposition |

### Figures

| Figure | Description |
|---|---|
| `NB00_condition_overlap.png` | Initial condition overlap assessment |
| `NB00_growth_corpus_stats.png` | Growth corpus scale summary |
| `NB00_per_strain_curves.png` | Per-strain curve counts |
| `NB00_strain_tiers.png` | Strain data availability tiers |
| `NB01_curve_fit_examples.png` | 12 representative Gompertz fits |
| `NB01_parameter_distributions.png` | mu, lag, A, R^2, AUC distributions |
| `NB01_qc_summary.png` | Per-plate QC pass rates |
| `NB01_single_brick_qc.png` | Single-brick validation |
| `NB02_anchor_growth_heatmap.png` | 7 anchor strains x conditions growth matrix |
| `NB02_condition_overlap_4way.png` | 4-dataset condition overlap |
| `NB02_coverage_summary.png` | Coverage matrix distributions |
| `NB03_ko_pca_guilds.png` | KO PCA by guild and taxonomy |
| `NB03_cog_by_guild.png` | COG profiles by metabolic guild |
| `NB03_genome_vs_ko.png` | Genome size vs KO diversity |
| `NB04_genus_env_heatmap.png` | Genus x environment (GTDB-wide) |
| `NB04_pangenome_env_profiles.png` | Species-clade environment profiles |
| `NB04_global_genus_occurrence.png` | Global 16S genus occurrence |
| `NB04_oak_ridge_strain_map.png` | Oak Ridge well locations |
| `NB04_well_guild_distribution.png` | Guild composition per well |
| `NB04_oakridge_cooccurrence.png` | Local Spearman co-occurrence |
| `NB04_global_cooccurrence.png` | Global Jaccard co-occurrence |
| `NB04_cluster_env_comparison.png` | pH/temperature niche comparison |
| `NB05_feature_summary.png` | Feature dimensionality per level + condition class distribution |
| `NB05_target_distributions.png` | Binary growth and continuous target distributions in anchor set |
| `NB06_variance_partition.png` | Cumulative AUC + incremental + SHAP by feature level |
| `NB06_shap_top20.png` | Top 20 SHAP features with KEGG annotations |
| `NB06_feature_correlation.png` | Correlation matrix of top-50 features showing correlated blocks |
| `NB06_group_shap.png` | Group-level SHAP after correlation grouping |

## Future Directions

### NB07 (revised): Full-corpus modeling with proper validation

The current NB07 is preliminary. A proper version requires:

1. **Full-corpus training**: Pool 123 ENIGMA strains (13,632 pairs) + 795 CSP genomes (53K pairs) in a shared KO feature space (6,360 shared KOs). Total ~67K training pairs — sufficient to learn condition-specific KO effects.

2. **Genus-level blocked holdout**: Train on all genera except one, predict the held-out genus. Report AUC/accuracy per held-out genus and per condition class. This tests genuine cross-genus generalization — can the model predict Pedobacter growth from Pseudomonas/Acidovorax/Burkholderia training data?

3. **KO x condition interaction features**: For each (genome, condition) pair, compute "does this genome have KOs in the KEGG module for this condition?" This is the critical feature engineering step that transforms generic KO presence into condition-specific prediction.

4. **Per-condition analysis**: For each of the 72 ENIGMA conditions, report prediction accuracy separately. Which conditions are predictable from KO content? Which require additional feature engineering?

5. **SHAP per condition class**: Which KOs matter for amino acids vs. carbon sources vs. metals? Report top-10 SHAP features per condition class with KEGG annotations.

6. **Continuous parameter prediction**: With 123 ENIGMA strains providing 9,861 fit-ok curves with µmax/lag/max_A, train regression models on the full feature set. Use leave-one-genus-out holdout.

7. **GapMind comparison**: On the subset of conditions with GapMind pathway matches, compare pathway completeness vs. data-driven GBDT — does GapMind outperform, match, or underperform the full model?

8. **FB concordance validation**: On the 7 FB-anchor strains (used as validation only, not training), map top SHAP KOs to FB fitness loci and compute concordance.

### NB08: WoM exometabolomic prediction (deferred)

For 6 WoM-profiled strains, test whether growth-predictive KOs predict metabolite production.

### Act III: Active learning (deferred)

Rank next experiments by model disagreement x genotype-space novelty x field relevance.

## References

1. Green SJ, Prakash O, Jasrotia P, et al. (2012). "Denitrifying bacteria from the genus Rhodanobacter dominate bacterial communities in the highly contaminated subsurface of a nuclear legacy waste site." *Applied and Environmental Microbiology* 78(4):1039-47. DOI: 10.1128/AEM.06435-11
2. Smith MB, Rocha AM, Smillie CS, et al. (2015). "Natural bacterial communities serve as quantitative geochemical biosensors." *mBio* 6(3):e00326-15. DOI: 10.1128/mBio.00326-15
3. He Z, Zhang P, Wu L, et al. (2018). "Microbial Functional Gene Diversity Predicts Groundwater Contamination and Ecosystem Functioning." *mBio* 9(1):e02435-17. DOI: 10.1128/mBio.02435-17
4. Hemme CL, Green SJ, Rishishwar L, et al. (2016). "Lateral Gene Transfer in a Heavy Metal-Contaminated-Groundwater Microbial Community." *mBio* 7(2):e02234-15. DOI: 10.1128/mBio.02234-15
5. Weimann A, Mooren K, Frank J, et al. (2016). "From Genomes to Phenotypes: Traitar, the Microbial Trait Analyzer." *mSystems* 1(6):e00101-16. DOI: 10.1128/mSystems.00101-16
6. Xu L, Zakem E, Weissman JL (2025). "Improved maximum growth rate prediction from microbial genomes by integrating phylogenetic information." *Nature Communications* 16:4256. DOI: 10.1038/s41467-025-59558-9
7. Reynolds R, Hyun S, Tully B, Bien J, Levine NM (2023). "Identification of microbial metabolic functional guilds from large genomic datasets." *Frontiers in Microbiology* 14:1197329. DOI: 10.3389/fmicb.2023.1197329
8. Borglin S, Joyner D, DeAngelis KM, et al. (2012). "Application of phenotypic microarrays to environmental microbiology." *Current Opinion in Biotechnology* 23(1):41-48. DOI: 10.1016/j.copbio.2011.12.006
9. Bochner BR (2009). "Global phenotypic characterization of bacteria." *FEMS Microbiology Reviews* 33(1):191-205. DOI: 10.1111/j.1574-6976.2008.00149.x
10. Zhou Z, Tran PQ, Breister AM, et al. (2022). "METABOLIC: high-throughput profiling of microbial genomes for functional traits." *Microbiome* 10:33. DOI: 10.1186/s40168-021-01213-8

## Authors

- Adam Arkin (ORCID: 0000-0002-4999-2931), U.C. Berkeley / Lawrence Berkeley National Laboratory

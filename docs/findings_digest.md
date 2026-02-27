# Findings Digest
**Last updated**: 2026-02-27 | **Projects**: 35 | **Findings**: ~153

## acinetobacter_adp1_explorer (2026-02, complete)
**Q**: What is the scope and structure of a comprehensive ADP1 database, and how do its annotations, metabolic models, and phenotype data intersect with BERDL collections (pangenome, biochemistry, fitness, PhageFoundry)?
1. **Rich Multi-Omics Database with 6 Data Modalities** — [REPORT](../projects/acinetobacter_adp1_explorer/REPORT.md)
2. **Strong BERDL Connectivity: 4 of 5 Connection Types at >90% Match** — [REPORT](../projects/acinetobacter_adp1_explorer/REPORT.md)
3. **Pangenome Cluster ID Bridge: 100% Mapping via Gene Junction Table** — [REPORT](../projects/acinetobacter_adp1_explorer/REPORT.md)
4. **FBA and TnSeq Essentiality Agree 74% of the Time** — [REPORT](../projects/acinetobacter_adp1_explorer/REPORT.md)
5. **Condition-Specific Fitness: Urea and Quinate Stand Apart** — [REPORT](../projects/acinetobacter_adp1_explorer/REPORT.md)
6. **Essential Genes Are 6x More Likely to Have COG Annotations** — [REPORT](../projects/acinetobacter_adp1_explorer/REPORT.md)
7. **Highly Conserved Core Metabolism Across 14 Genomes** — [REPORT](../projects/acinetobacter_adp1_explorer/REPORT.md)
8. **87% of Growth Predictions Depend on Gapfilled Reactions** — [REPORT](../projects/acinetobacter_adp1_explorer/REPORT.md)

## adp1_deletion_phenotypes (2026-02, complete)
**Q**: What is the condition-dependent structure of gene essentiality in *Acinetobacter baylyi* ADP1, as revealed by the de Berardinis single-gene deletion collection grown on 8 carbon sources?
1. **Carbon sources define a three-tier essentiality landscape** — [REPORT](../projects/adp1_deletion_phenotypes/REPORT.md)
2. **Conditions are largely independent — 5 PCs capture 82% of variance** — [REPORT](../projects/adp1_deletion_phenotypes/REPORT.md)
3. **The phenotype landscape is a continuum, not discrete modules** — [REPORT](../projects/adp1_deletion_phenotypes/REPORT.md)
4. **Condition-specific genes reveal the metabolic architecture of ADP1** — [REPORT](../projects/adp1_deletion_phenotypes/REPORT.md)
5. **Missing dispensable genes are shorter, less conserved, and enriched for hypotheticals** — [REPORT](../projects/adp1_deletion_phenotypes/REPORT.md)

## adp1_triple_essentiality (2026-02, complete)
**Q**: Among genes that TnSeq says are dispensable in *Acinetobacter baylyi* ADP1, does FBA correctly predict which ones have growth defects? Can direct mutant growth rate measurements serve as an independent axis to evaluate where computational (FBA) and genetic (TnSeq) methods agree or disagree?
1. **FBA Essentiality Class Does Not Predict Growth Defects Among Dispensable Genes** — [REPORT](../projects/adp1_triple_essentiality/REPORT.md)
2. **The Null Result Is Robust Across Growth Defect Thresholds** — [REPORT](../projects/adp1_triple_essentiality/REPORT.md)
3. **Growth Measurements Cannot Break FBA-TnSeq Ties** — [REPORT](../projects/adp1_triple_essentiality/REPORT.md)
4. **Condition-Specific FBA Flux Shows Weak, Mixed Correlations with Growth** — [REPORT](../projects/adp1_triple_essentiality/REPORT.md)
5. **Growth Defects Are Partially Condition-Specific** — [REPORT](../projects/adp1_triple_essentiality/REPORT.md)
6. **Aromatic Degradation Genes Are Enriched Among FBA-Discordant Genes** — [REPORT](../projects/adp1_triple_essentiality/REPORT.md)

## aromatic_catabolism_network (2026-02, complete)
**Q**: Why does aromatic catabolism in *Acinetobacter baylyi* ADP1 require Complex I (NADH dehydrogenase), iron acquisition, and PQQ biosynthesis when growth on other carbon sources does not?
1. **Aromatic catabolism requires a 51-gene support network spanning 4 metabolic subsystems** — [REPORT](../projects/aromatic_catabolism_network/REPORT.md)
2. **Complex I is the largest support subsystem — and invisible to FBA** — [REPORT](../projects/aromatic_catabolism_network/REPORT.md)
3. **Support subsystems are genomically independent but metabolically coupled** — [REPORT](../projects/aromatic_catabolism_network/REPORT.md)
4. **Co-fitness assigns 16 unknown genes to specific subsystems** — [REPORT](../projects/aromatic_catabolism_network/REPORT.md)
5. **Cross-species: Complex I dependency is on high-NADH substrates, not aromatics specifically** — [REPORT](../projects/aromatic_catabolism_network/REPORT.md)

## cofitness_coinheritance (2026-02, complete)
**Q**: Do genes with correlated fitness profiles (co-fit) tend to co-occur in the same genomes across a species' pangenome? Does functional coupling constrain which genes are gained and lost together?
1. **Pairwise Co-fitness Weakly Predicts Co-occurrence** — [REPORT](../projects/cofitness_coinheritance/REPORT.md)
2. **Operons Are Not a Confound** — [REPORT](../projects/cofitness_coinheritance/REPORT.md)
3. **ICA Modules Show Co-inheritance, Especially Accessory Modules** — [REPORT](../projects/cofitness_coinheritance/REPORT.md)
4. **Co-fitness Strength Weakly Anti-correlates with Co-occurrence** — [REPORT](../projects/cofitness_coinheritance/REPORT.md)
5. **Phylogenetic Distance Stratification** — [REPORT](../projects/cofitness_coinheritance/REPORT.md)

## cog_analysis (2026-02, complete)
**Q**: How do COG functional category distributions differ across core, auxiliary, and novel genes in bacterial pangenomes?
1. **Universal Functional Partitioning in Bacterial Pangenomes** — [REPORT](../projects/cog_analysis/REPORT.md)
2. **Composite COG Categories Are Biologically Meaningful** — [REPORT](../projects/cog_analysis/REPORT.md)

## conservation_fitness_synthesis (2026-02, complete)
**Q**: How does a gene's importance for bacterial survival relate to its evolutionary conservation, and what does the conserved genome actually look like?
1. **The Gradient** — [REPORT](../projects/conservation_fitness_synthesis/REPORT.md)
2. **The Paradox** — [REPORT](../projects/conservation_fitness_synthesis/REPORT.md)
3. **The Resolution** — [REPORT](../projects/conservation_fitness_synthesis/REPORT.md)
4. **The Architecture** — [REPORT](../projects/conservation_fitness_synthesis/REPORT.md)

## conservation_vs_fitness (2026-02, complete)
**Q**: Are essential genes preferentially conserved in the core genome, and what functional categories distinguish essential-core from essential-auxiliary genes?
1. **Link Table (Phase 1)** — [REPORT](../projects/conservation_vs_fitness/REPORT.md)
2. **Essential Genes Are Enriched in Core Clusters (Phase 2)** — [REPORT](../projects/conservation_vs_fitness/REPORT.md)
3. **Functional Profiles Differ by Conservation Category** — [REPORT](../projects/conservation_vs_fitness/REPORT.md)
4. **Validation** — [REPORT](../projects/conservation_vs_fitness/REPORT.md)

## core_gene_tradeoffs (2026-02, complete)
**Q**: Why are core genome genes MORE likely to show positive fitness effects when deleted, and what functions and conditions drive this burden paradox?
1. **The Burden Paradox Is Function-Specific** — [REPORT](../projects/core_gene_tradeoffs/REPORT.md)
2. **Trade-Off Genes Are Enriched in Core** — [REPORT](../projects/core_gene_tradeoffs/REPORT.md)
3. **The Selection Signature Matrix** — [REPORT](../projects/core_gene_tradeoffs/REPORT.md)
4. **Case Studies** — [REPORT](../projects/core_gene_tradeoffs/REPORT.md)

## costly_dispensable_genes (2026-02, complete)
**Q**: What characterizes genes that are simultaneously burdensome (fitness improves when deleted) and not conserved in the pangenome? Are they mobile elements, recent acquisitions, degraded pathways, or something else?
1. **Costly+Dispensable Genes Are Mobile Genetic Elements** — [REPORT](../projects/costly_dispensable_genes/REPORT.md)
2. **They Are Poorly Characterized Recent Acquisitions** — [REPORT](../projects/costly_dispensable_genes/REPORT.md)
3. **Core Metabolism Is Depleted** — [REPORT](../projects/costly_dispensable_genes/REPORT.md)
4. ***Pseudomonas stutzeri* RCH2 Is an Outlier** — [REPORT](../projects/costly_dispensable_genes/REPORT.md)
5. **Costly+Dispensable Genes Still Have Condition-Specific Effects** — [REPORT](../projects/costly_dispensable_genes/REPORT.md)

## counter_ion_effects (2026-02, complete)
**Q**: When bacteria are exposed to metal salts (CoCl₂, NiCl₂, CuCl₂), how much of the observed fitness effect is caused by the metal cation versus the counter anion (chloride)? Does correcting for chloride confounding change the conclusions of the Pan-Bacterial Metal Fitness Atlas?
1. **39.8% of Metal-Important Genes Are Also NaCl-Important** — [REPORT](../projects/counter_ion_effects/REPORT.md)
2. **Counter Ions Are NOT the Primary Driver of the Overlap** — [REPORT](../projects/counter_ion_effects/REPORT.md)
3. **DvH Metal-NaCl Correlation Follows Toxicity Mechanism, Not Chloride Dose** — [REPORT](../projects/counter_ion_effects/REPORT.md)
4. **Metal Fitness Atlas Core Enrichment Is Robust After Correction** — [REPORT](../projects/counter_ion_effects/REPORT.md)
5. **Gene Classification: 60% of Metal Fitness Genes Are Metal-Specific** — [REPORT](../projects/counter_ion_effects/REPORT.md)
6. **psRCH2: The Only Within-Metal Counter Ion Comparison** — [REPORT](../projects/counter_ion_effects/REPORT.md)

## ecotype_analysis (2026-02, complete)
**Q**: What drives gene content similarity between bacterial genomes: environmental similarity or phylogenetic relatedness?
1. **Analysis of **172 species** with sufficient environmental and phylogenetic data reveals:** — [REPORT](../projects/ecotype_analysis/REPORT.md)
2. **Phylogeny Usually Dominates** — [REPORT](../projects/ecotype_analysis/REPORT.md)
3. **No Difference by Lifestyle** — [REPORT](../projects/ecotype_analysis/REPORT.md)
4. **Statistical Summary** — [REPORT](../projects/ecotype_analysis/REPORT.md)
5. **Category Breakdown** — [REPORT](../projects/ecotype_analysis/REPORT.md)
6. **Embedding Diversity** — [REPORT](../projects/ecotype_analysis/REPORT.md)

## ecotype_env_reanalysis (2026-02, complete)
**Q**: Does the environment effect on gene content become stronger when analysis is restricted to genuinely environmental samples, excluding human-associated genomes whose AlphaEarth embeddings reflect hospital satellite imagery rather than ecological habitat?
1. **Clinical bias does NOT explain the weak environment signal (H0 not rejected)** — [REPORT](../projects/ecotype_env_reanalysis/REPORT.md)
2. **47% of ecotype species are human-associated, only 21% environmental** — [REPORT](../projects/ecotype_env_reanalysis/REPORT.md)
3. **NaN species are disproportionately environmental, not human-associated** — [REPORT](../projects/ecotype_env_reanalysis/REPORT.md)
4. **Overall partial correlations are 27x higher than the original analysis** — [REPORT](../projects/ecotype_env_reanalysis/REPORT.md)

## enigma_contamination_functional_potential (2026-02, complete)
**Q**: Do high-contamination Oak Ridge groundwater communities show enrichment for taxa with higher inferred stress-related functional potential compared with low-contamination communities?
1. **Multiplicity and sample-size context (primary panel)** — [REPORT](../projects/enigma_contamination_functional_potential/REPORT.md)
2. **Confirmatory Spearman tests remain null with confidence intervals and global FDR** — [REPORT](../projects/enigma_contamination_functional_potential/REPORT.md)
3. **Exploratory defense signal remains strongest in coverage-aware models** — [REPORT](../projects/enigma_contamination_functional_potential/REPORT.md)
4. **Community-fraction robustness does not show strong within-fraction monotonic signal** — [REPORT](../projects/enigma_contamination_functional_potential/REPORT.md)
5. **Contamination-index sensitivity does not change confirmatory outcome** — [REPORT](../projects/enigma_contamination_functional_potential/REPORT.md)
6. **Species-proxy resolution sensitivity is limited by mapped coverage** — [REPORT](../projects/enigma_contamination_functional_potential/REPORT.md)
7. **Contamination index was broad but right-skewed** — [REPORT](../projects/enigma_contamination_functional_potential/REPORT.md)

## env_embedding_explorer (2026-02, complete)
**Q**: What do AlphaEarth environmental embeddings capture, and how do they relate to geographic coordinates and NCBI environment labels?
1. **Environmental samples show 3.4x stronger geographic signal than human-associated samples** — [REPORT](../projects/env_embedding_explorer/REPORT.md)
2. **AlphaEarth embeddings encode real geographic signal — not noise** — [REPORT](../projects/env_embedding_explorer/REPORT.md)
3. **Strong clinical/human sampling bias in the AlphaEarth subset** — [REPORT](../projects/env_embedding_explorer/REPORT.md)
4. **36% of coordinates flagged as potential institutional addresses** — [REPORT](../projects/env_embedding_explorer/REPORT.md)
5. **UMAP reveals fine-grained embedding structure with environment-correlated clusters** — [REPORT](../projects/env_embedding_explorer/REPORT.md)
6. **Embedding space also shows taxonomic structure** — [REPORT](../projects/env_embedding_explorer/REPORT.md)

## essential_genome (2026-02, complete)
**Q**: Which essential genes are conserved across bacteria, which are context-dependent, and can we predict function for uncharacterized essential genes using module context from non-essential orthologs?
1. **15 Gene Families Are Essential in All 48 Bacteria** — [REPORT](../projects/essential_genome/REPORT.md)
2. **Only 5% of Ortholog Families Are Universally Essential** — [REPORT](../projects/essential_genome/REPORT.md)
3. **Orphan Essential Genes Are 58.7% Hypothetical** — [REPORT](../projects/essential_genome/REPORT.md)
4. **1,382 Function Predictions for Hypothetical Essentials** — [REPORT](../projects/essential_genome/REPORT.md)
5. **Universally Essential Families Are Overwhelmingly Core** — [REPORT](../projects/essential_genome/REPORT.md)

## essential_metabolome (2026-02, complete)
**Q**: Which biochemical reactions are universally essential across bacteria, and what does the essential metabolome reveal about the minimal core metabolism required for microbial life?
1. **High Conservation of Amino Acid Biosynthesis Pathways** — [REPORT](../projects/essential_metabolome/REPORT.md)
2. ***Desulfovibrio vulgaris* Serine Auxotrophy** — [REPORT](../projects/essential_metabolome/REPORT.md)
3. **Conserved Carbon Source Utilization** — [REPORT](../projects/essential_metabolome/REPORT.md)
4. **GapMind Coverage Limitation Discovered** — [REPORT](../projects/essential_metabolome/REPORT.md)

## field_vs_lab_fitness (2026-02, complete)
**Q**: Which genes matter for survival under environmentally-realistic conditions but appear dispensable in the lab, and vice versa? Do field-relevant fitness effects predict pangenome conservation better than lab-only effects?
1. **ENIGMA CORAL Contains No DvH Fitness Data (NB01)** — [REPORT](../projects/field_vs_lab_fitness/REPORT.md)
2. **Condition Classification (NB02)** — [REPORT](../projects/field_vs_lab_fitness/REPORT.md)
3. **Genes Important for Field Conditions Are Significantly More Conserved (NB03)** — [REPORT](../projects/field_vs_lab_fitness/REPORT.md)
4. **Specificity Analysis: Lab-Specific Genes Are Surprisingly More Core** — [REPORT](../projects/field_vs_lab_fitness/REPORT.md)
5. **Fitness Effects Are Weak Predictors of Core Status** — [REPORT](../projects/field_vs_lab_fitness/REPORT.md)
6. **Threshold Sensitivity Analysis** — [REPORT](../projects/field_vs_lab_fitness/REPORT.md)
7. **Module-Level Conservation Shows No Field-Lab Difference (NB04)** — [REPORT](../projects/field_vs_lab_fitness/REPORT.md)

## fitness_effects_conservation (2026-02, complete)
**Q**: Is there a continuous gradient from essential genes (core) to dispensable genes (accessory) across the full fitness spectrum, and what does the fitness landscape of novel genes look like?
1. **Conservation Increases with Fitness Importance** — [REPORT](../projects/fitness_effects_conservation/REPORT.md)
2. **Breadth of Fitness Effects Predicts Conservation** — [REPORT](../projects/fitness_effects_conservation/REPORT.md)
3. **Core Genes Are Not Burdens -- They're More Likely Beneficial** — [REPORT](../projects/fitness_effects_conservation/REPORT.md)
4. **Specific-Phenotype Genes Are More Likely Core** — [REPORT](../projects/fitness_effects_conservation/REPORT.md)
5. **Ephemeral Niche Genes** — [REPORT](../projects/fitness_effects_conservation/REPORT.md)
6. **Fitness Distributions by Conservation** — [REPORT](../projects/fitness_effects_conservation/REPORT.md)
7. **Novel Gene Landscape** — [REPORT](../projects/fitness_effects_conservation/REPORT.md)

## fitness_modules (2026-02, complete)
**Q**: Can we decompose RB-TnSeq fitness compendia into latent functional modules via robust ICA, align them across organisms using orthology, and use module context to predict gene function?
1. **1. The strict membership threshold (|weight| >= 0.3, max 50 genes) was critical. The initial D'Agostino K-squared approach gave 100-280 genes per module with weak cofitness signal (59% enriched, 1-17x correlation). After switching to absolute weight thresholds, modules became biologically coherent (94% enriched, 2.8x correlation enrichment)** — [REPORT](../projects/fitness_modules/REPORT.md)

## lab_field_ecology (2026-02, complete)
**Q**: Do lab-measured fitness effects under contaminant stress predict the field abundance of Fitness Browser organisms across Oak Ridge groundwater sites with varying geochemistry?
1. **14 of 26 Fitness Browser Genera Detected at Oak Ridge** — [REPORT](../projects/lab_field_ecology/REPORT.md)
2. **Genus Abundance Correlates with Uranium -- in Both Directions** — [REPORT](../projects/lab_field_ecology/REPORT.md)
3. **Lab Metal Tolerance Does Not Significantly Predict Field Abundance Ratio** — [REPORT](../projects/lab_field_ecology/REPORT.md)
4. **Community Composition Shifts with Contamination** — [REPORT](../projects/lab_field_ecology/REPORT.md)

## metabolic_capability_dependency (in-progress)
**Q**: Can we distinguish metabolic *capability* (genome predicts a complete pathway) from metabolic *dependency* (fitness data shows the pathway genes actually matter)? Do "latent capabilities" — pathways that are genomically present but experimentally dispensable — predict pangenome openness and evolutionary gene loss?
1. **H1 Supported: A Substantial Fraction of Complete Pathways Are Functionally Neutral** — [REPORT](../projects/metabolic_capability_dependency/REPORT.md)
2. **H2 Mixed: Pathway-Level Conservation Undifferentiated; Pangenome Openness Correlated with Latent Rate** — [REPORT](../projects/metabolic_capability_dependency/REPORT.md)
3. **H3 Supported: All Target Species Show Distinct Metabolic Ecotypes** — [REPORT](../projects/metabolic_capability_dependency/REPORT.md)

## metal_fitness_atlas (2026-02, complete)
**Q**: Across diverse bacteria subjected to genome-wide fitness profiling under metal stress, what is the genetic architecture of metal tolerance — is it encoded in the core or accessory genome, is it conserved across species, and can fitness-validated metal tolerance genes predict capabilities across the broader pangenome?
1. **Metal-Important Genes Are Enriched in the Core Genome** — [REPORT](../projects/metal_fitness_atlas/REPORT.md)
2. **Essential Metals Show Stronger Core Enrichment Than Toxic Metals** — [REPORT](../projects/metal_fitness_atlas/REPORT.md)
3. **559 Metal Experiments Across 31 Organisms and 16 Metals** — [REPORT](../projects/metal_fitness_atlas/REPORT.md)
4. **12,838 Metal-Important Gene Records Across 24 Organisms** — [REPORT](../projects/metal_fitness_atlas/REPORT.md)
5. **1,182 Conserved Metal Gene Families Identified** — [REPORT](../projects/metal_fitness_atlas/REPORT.md)
6. **Metal-Responsive ICA Modules Have High Core Fraction** — [REPORT](../projects/metal_fitness_atlas/REPORT.md)
7. **Pangenome-Scale Prediction Validates Metal Gene Signature** — [REPORT](../projects/metal_fitness_atlas/REPORT.md)

## module_conservation (2026-02, complete)
**Q**: Are ICA fitness modules enriched in core pangenome genes, and do cross-organism module families map to the core genome?
1. **Module Genes Are More Core Than Average** — [REPORT](../projects/module_conservation/REPORT.md)
2. **Most Modules Are Core** — [REPORT](../projects/module_conservation/REPORT.md)
3. **Family Breadth Does NOT Predict Conservation** — [REPORT](../projects/module_conservation/REPORT.md)
4. **Accessory Module Families Exist** — [REPORT](../projects/module_conservation/REPORT.md)
5. **Essential Genes Are Absent from Modules** — [REPORT](../projects/module_conservation/REPORT.md)

## pangenome_openness (2026-02, complete)
**Q**: Do open pangenomes show different patterns of environmental vs phylogenetic effects compared to closed pangenomes?
1. **No Correlation Found** — [REPORT](../projects/pangenome_openness/REPORT.md)
2. **Interpretation** — [REPORT](../projects/pangenome_openness/REPORT.md)
3. **Literature Context** — [REPORT](../projects/pangenome_openness/REPORT.md)
4. **Limitations** — [REPORT](../projects/pangenome_openness/REPORT.md)

## paperblast_explorer (2026-02, complete)
**Q**: What does the `kescience_paperblast` collection contain, how current is it, and what are its coverage patterns across organisms, domains of life, and functional databases?
1. **Finding 1: One organism dominates nearly half of all literature** — [REPORT](../projects/paperblast_explorer/REPORT.md)
2. **Finding 2: 65.6% of genes have exactly one paper** — [REPORT](../projects/paperblast_explorer/REPORT.md)
3. **Finding 3: Literature inequality is extreme — Lorenz curves** — [REPORT](../projects/paperblast_explorer/REPORT.md)
4. **Finding 4: Bacterial research is concentrated on pathogens** — [REPORT](../projects/paperblast_explorer/REPORT.md)
5. **Finding 5: 345K protein families from 816K sequences** — [REPORT](../projects/paperblast_explorer/REPORT.md)
6. **Finding 6: 55% of protein families are dark or dim** — [REPORT](../projects/paperblast_explorer/REPORT.md)

## pathway_capability_dependency (2026-02, complete)
**Q**: When a bacterium's genome encodes a complete biosynthetic or catabolic pathway, does the organism actually depend on it? Can we use fitness data to distinguish **active dependencies** from **latent capabilities** — and predict which pathways are candidates for evolutionary gene loss?
1. **Pathway Completeness Alone Is Insufficient to Predict Metabolic Dependency** — [REPORT](../projects/pathway_capability_dependency/REPORT.md)
2. **All "Latent Capabilities" Become Important Under Specific Conditions** — [REPORT](../projects/pathway_capability_dependency/REPORT.md)
3. **Conservation Validation: Active Dependencies Have Near-Complete Core Genomes** — [REPORT](../projects/pathway_capability_dependency/REPORT.md)
4. **Variable Pathways Strongly Correlate with Pangenome Openness** — [REPORT](../projects/pathway_capability_dependency/REPORT.md)
5. **Amino Acid Biosynthesis Pathways Show the Strongest Accessory Dependence** — [REPORT](../projects/pathway_capability_dependency/REPORT.md)
6. **Metabolic Ecotypes Correlate with Pangenome Openness** — [REPORT](../projects/pathway_capability_dependency/REPORT.md)

## phb_granule_ecology (2026-02, complete)
**Q**: How are polyhydroxybutyrate (PHB) granule-forming pathways distributed across bacterial clades and environments, and does this distribution support the hypothesis that carbon storage granules are most beneficial in temporally variable feast/famine environments?
1. **Finding 1: PHB pathways are widespread but phylogenetically concentrated** — [REPORT](../projects/phb_granule_ecology/REPORT.md)
2. **Finding 2: PHB is enriched in environmentally variable habitats (H1a supported)** — [REPORT](../projects/phb_granule_ecology/REPORT.md)
3. **Finding 3: PHB-niche breadth association is largely explained by genome size (H1b qualified)** — [REPORT](../projects/phb_granule_ecology/REPORT.md)
4. **Finding 4: Subclade enrichment reveals heterogeneous selection within phyla (H1d partially supported)** — [REPORT](../projects/phb_granule_ecology/REPORT.md)
5. **Finding 5: Strong signal of horizontal gene transfer in phaC distribution** — [REPORT](../projects/phb_granule_ecology/REPORT.md)
6. **Finding 6: NMDC metagenomic cross-validation supports pangenome PHB patterns (H1c supported)** — [REPORT](../projects/phb_granule_ecology/REPORT.md)

## respiratory_chain_wiring (2026-02, complete)
**Q**: How is *Acinetobacter baylyi* ADP1's branched respiratory chain wired across carbon sources — which NADH dehydrogenases and terminal oxidases are required for which substrates?
1. **Each carbon source uses a distinct respiratory chain configuration** — [REPORT](../projects/respiratory_chain_wiring/REPORT.md)
2. **ADP1 has three parallel NADH dehydrogenases with distinct condition profiles** — [REPORT](../projects/respiratory_chain_wiring/REPORT.md)
3. **The quinate-Complex I paradox is resolved by NADH flux rate, not total yield** — [REPORT](../projects/respiratory_chain_wiring/REPORT.md)
4. **Cross-species: NDH-2 presence does NOT predict reduced Complex I aromatic dependency** — [REPORT](../projects/respiratory_chain_wiring/REPORT.md)
5. **Proteomics: respiratory wiring is metabolic, not transcriptional** — [REPORT](../projects/respiratory_chain_wiring/REPORT.md)

## webofmicrobes_explorer (2026-02, complete)
**Q**: What does the `kescience_webofmicrobes` exometabolomics collection contain, which organisms overlap with the Fitness Browser, and how well do metabolite uptake/release profiles connect to pangenome-predicted metabolic capabilities?
1. **WoM Action Encoding Uses Four Distinct Semantics, Not Three** — [REPORT](../projects/webofmicrobes_explorer/REPORT.md)
2. **Two Direct Fitness Browser Strain Matches Plus Two Genus-Level Matches** — [REPORT](../projects/webofmicrobes_explorer/REPORT.md)
3. **19 WoM-Produced Metabolites Are Tested as FB Carbon/Nitrogen Sources** — [REPORT](../projects/webofmicrobes_explorer/REPORT.md)
4. **26.8% of WoM Metabolites Have Definitive ModelSEED Links (68.5% with Ambiguous Formula Matches)** — [REPORT](../projects/webofmicrobes_explorer/REPORT.md)
5. **ENIGMA Isolates Show Distinct "Metabolic Novelty Rates"** — [REPORT](../projects/webofmicrobes_explorer/REPORT.md)
6. **All WoM Genera Have Pangenome Species Clades** — [REPORT](../projects/webofmicrobes_explorer/REPORT.md)

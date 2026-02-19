# Research Ideas & Future Directions

**Purpose**: Track potential research projects, extensions, and interesting questions that emerge from ongoing work. This serves as a "research backlog" to prioritize future investigations.

**How to use**:
- Add ideas as they come up during analysis
- Tag with source project (e.g., `[cog_analysis]`, `[ecotype_analysis]`)
- Mark priority: HIGH, MEDIUM, LOW
- Update status: PROPOSED → IN_PROGRESS → COMPLETED
- Link to related projects or dependencies

---

## High Priority Ideas

### [pangenome_pathway_geography] Pangenome Openness, Metabolic Pathways, and Biogeography
**Status**: IN_PROGRESS
**Priority**: HIGH
**Effort**: Medium (3-4 weeks)

**Research Question**: Do pangenome characteristics (open vs. closed) correlate with metabolic pathway diversity and biogeographic distribution patterns?

**Approach**:
- Extract pangenome stats (27,690 species from `pangenome` table)
- Aggregate gapmind pathway data to species level (305M rows → species summaries)
- Calculate biogeographic metrics from AlphaEarth embeddings (83K genomes, 28% coverage)
- Test three hypotheses:
  1. Open pangenomes → greater pathway diversity
  2. Wider geographic distribution → more diverse metabolic capabilities
  3. Open pangenomes → broader biogeographic ranges

**Hypotheses**:
- Species with high accessory/core gene ratios have more metabolic pathways (ecological generalists)
- Species with larger AlphaEarth embedding distances have more pathways (niche breadth)
- Pangenome openness enables geographic dispersal through metabolic flexibility

**Impact**: High - integrates genomic, functional, and ecological dimensions of microbial diversity

**Dependencies**:
- AlphaEarth embeddings coverage (only 28% of genomes)
- Gapmind pathway data quality and completeness
- Need to control for genome count as covariate

**Progress**:
- ✅ Project structure created: `projects/pangenome_pathway_geography/`
- ✅ Data extraction notebook: `01_data_extraction.ipynb`
- ✅ Analysis notebook: `02_comparative_analysis.ipynb`
- ⏳ Next: Run notebooks on BERDL JupyterHub to extract data
- ⏳ Next: Perform correlation and regression analyses
- ⏳ Next: Generate visualizations and interpret patterns

**Location**: `projects/pangenome_pathway_geography/`

---

### [cog_analysis] Ecotype Functional Differentiation
**Status**: PROPOSED
**Priority**: HIGH
**Effort**: Medium (2-3 weeks)

**Research Question**: Do ecotypes within a species differ in their COG functional profiles?

**Approach**:
- Use `data/ecotypes_expanded/target_genomes_expanded.csv` (224 species)
- For species with multiple ecotype clusters, compare COG enrichment between ecotypes
- Test if ecotypes differ in:
  - Defense (V) - different phage exposure?
  - Transport (P, G, E) - different nutrient availability?
  - Secondary metabolites (Q) - niche differentiation?

**Hypothesis**:
- Ecotypes represent ecological specialization
- Within-species ecotypes should differ in adaptive gene content (V, M, Q, K) but NOT core metabolism (J, F, H, C)
- Would show that functional differentiation drives ecotype formation

**Impact**: Nature/Science-level finding connecting genome content to ecological adaptation

**Dependencies**:
- Existing: `projects/ecotype_analysis/` with clustering data
- Existing: `projects/cog_analysis/` with functional annotation approach
- New: Need to join ecotype clusters with COG annotations at genome level

**Next Steps**:
1. Prototype analysis on 5-10 well-clustered species
2. Develop statistical framework for within-species comparison
3. Scale to all 224 species

---

### [cog_analysis] Lifestyle-Based COG Stratification
**Status**: PROPOSED
**Priority**: HIGH
**Effort**: Low (1 week)

**Research Question**: How does lifestyle (free-living vs host-associated) affect pangenome functional composition?

**Approach**:
- Join `genome` → `sample` → `ncbi_env` to get environment metadata
- Stratify species by lifestyle: free-living, host-associated, pathogen
- Compare COG enrichment patterns across lifestyles

**Hypotheses**:
- Host-associated bacteria:
  - Higher V (defense) enrichment for immune evasion
  - Lower M (cell wall) enrichment (less environmental stress)
  - Different metabolic profiles (E, G, I) due to nutrient availability
- Free-living bacteria:
  - Higher metabolic diversity
  - More environmental sensing (T, K)

**Impact**: Moderate - extends universal pattern to show ecological context matters

**Dependencies**:
- Need to explore `ncbi_env` table coverage
- May need manual curation of lifestyle categories

**Next Steps**:
1. Query `ncbi_env` to assess data availability
2. Define lifestyle categories (free-living, host-associated, pathogen, environmental)
3. Run COG analysis stratified by lifestyle

---

### [fitness_modules] Pan-bacterial Fitness Modules via ICA
**Status**: IN_PROGRESS
**Priority**: HIGH
**Effort**: Medium (3-4 weeks)

**Research Question**: Can robust ICA decomposition of RB-TnSeq fitness compendia reveal conserved functional modules across bacteria, and can module context predict gene function better than cofitness alone?

**Approach**:
- Decompose gene-fitness matrices into independent components (modules) via robust ICA (100× FastICA + DBSCAN clustering)
- Annotate modules with KEGG, SEED, and domain enrichments
- Align modules across organisms using BBH ortholog fingerprints → module families
- Predict function for hypothetical proteins using module and family context
- Benchmark against cofitness voting, ortholog transfer, and domain-only baselines

**Hypotheses**:
- ICA modules capture biologically coherent gene groups (operons, regulons, pathways)
- Conserved module families exist across phylogenetically diverse bacteria
- Module-based predictions outperform single-method baselines for unannotated genes

**Impact**: High — upgrades Fitness Browser from edge-based to module-based analysis; creates pan-bacterial regulon catalog

**Progress**:
- ✅ Project structure created: `projects/fitness_modules/`
- ✅ 7 analysis notebooks (01-07) scaffolded
- ✅ Reusable ICA pipeline: `src/ica_pipeline.py`
- ⏳ Next: Run NB 01-02 on JupyterHub to select pilots and extract matrices
- ⏳ Next: Run NB 03 locally for ICA decomposition
- ⏳ Next: Run NB 04-07 for annotation, alignment, prediction, benchmarking

**Location**: `projects/fitness_modules/`

---

### [NEW] Metabolic Capability vs Metabolic Dependency
**Status**: PROPOSED
**Priority**: HIGH
**Effort**: Medium (requires GapMind data extraction from JupyterHub)

**Research Question**: Just because a bacterium's genome encodes a complete amino acid biosynthesis or carbon utilization pathway, does the organism actually depend on it? Can we distinguish metabolic *capability* (genome predicts pathway present) from metabolic *dependency* (fitness data shows pathway genes matter)?

**Approach**:
- For the ~30 FB organisms with pangenome links, map GapMind pathway predictions to FB genes via the link table
- For each predicted-complete pathway, aggregate fitness effects of the pathway genes
- Classify pathways as: **active dependencies** (complete + fitness-important), **latent capabilities** (complete + fitness-neutral), or **missing** (incomplete)
- Scale to all 27K species: study within-species pathway heterogeneity at the step level — which pathways are "core complete" vs "accessory"?
- Identify "metabolic ecotypes" — within-species clusters defined by metabolic capability profiles

**Hypotheses**:
- Amino acid biosynthesis pathways that are "latent capabilities" (present but neutral) are candidates for future gene loss (Black Queen Hypothesis)
- Species with more "latent capabilities" will have more open pangenomes (ongoing streamlining)
- Within-species pathway variation defines metabolic ecotypes that correlate with environmental niche

**Impact**: High — bridges the gap between genome-level metabolic prediction and experimental fitness validation. Relevant to synthetic biology (minimal media design), microbiome ecology (cross-feeding dependencies), and drug target discovery (active dependencies are targets).

**Dependencies**:
- GapMind data extraction (305M rows in `kbase_ke_pangenome.gapmind_pathways`)
- Existing FB-pangenome link table from `conservation_vs_fitness`
- Existing fitness data from `fitness_effects_conservation`

---

### [pangenome_openness + cog_analysis] Openness vs Functional Composition
**Status**: PROPOSED
**Priority**: HIGH
**Effort**: Low (1 week)

**Research Question**: Do "open" vs "closed" pangenomes show different COG enrichment patterns?

**Approach**:
- Calculate openness: `no_singleton_gene_clusters / no_gene_clusters`
- Split species into quartiles (Q1 = most closed, Q4 = most open)
- Compare COG enrichment between closed vs open pangenomes

**Hypotheses**:
- Open pangenomes → HIGHER L enrichment (more HGT, more mobile elements)
- Closed pangenomes → HIGHER metabolic diversity in core (E, C, G)
- Open pangenomes → HIGHER V enrichment (more defense systems from HGT)

**Impact**: Moderate-High - connects pangenome structure to functional composition

**Dependencies**:
- Existing: `projects/pangenome_openness/data/pangenome_stats.csv`
- Can reuse COG analysis pipeline

**Next Steps**:
1. Merge pangenome stats with COG analysis results
2. Stratify by openness quartile
3. Statistical test for trend with openness

---

## Medium Priority Ideas

### [cog_analysis] Scale to 100-200 Species
**Status**: PROPOSED
**Priority**: MEDIUM
**Effort**: Low (computational time, minimal analyst time)

**Research Question**: Do COG enrichment patterns hold at larger scale? Are there phylum-specific deviations?

**Approach**:
- Expand from 32 → 100-200 species
- Ensure phylogenetic balance across all major GTDB phyla
- Stratify by genome count bins (50-100, 100-200, 200-500)

**Rationale**:
- Current signals (L: +10.88%, J: -4.65%) are very strong and will hold
- Weaker signals (M, Q, K) might become significant with more power
- Allows detection of phylum-specific patterns

**Impact**: Low-Medium - strengthens existing findings, enables publication

**Dependencies**:
- Spark cluster access for larger query
- Species selection strategy (phylogenetically balanced)

**Next Steps**:
1. Design sampling strategy (stratified by phylum, genome count)
2. Test query performance on 100 species
3. Run full analysis pipeline

---

### [cog_analysis] Gene Copy Number Variation
**Status**: PROPOSED
**Priority**: MEDIUM
**Effort**: Medium (new analysis type)

**Research Question**: Beyond presence/absence, do adaptive vs housekeeping genes show different copy number patterns?

**Approach**:
- For core genes with COG annotations, count paralogs (gene cluster multiplicity)
- Compare copy number distributions between COG categories
- Test: Do housekeeping genes (J, F, H) have fixed copy numbers while adaptive genes (V, L, M) show variation?

**Hypothesis**:
- Core housekeeping genes exist in fixed copy numbers (dosage constraint)
- Adaptive genes show copy number variation even in core (dosage flexibility)

**Impact**: Medium - adds mechanistic depth to functional partitioning

**Dependencies**:
- Need to count `gene_cluster_id` per genome per COG category
- Requires understanding gene cluster membership vs paralogy

**Next Steps**:
1. Prototype on single species (N. gonorrhoeae)
2. Define copy number metric (mean, variance, coefficient of variation)
3. Scale to multi-species analysis

---

### [cog_analysis] Phylum-Specific Patterns Deep Dive
**Status**: PROPOSED
**Priority**: MEDIUM
**Effort**: Medium

**Research Question**: Which phyla deviate from universal COG enrichment patterns and why?

**Specific Questions**:
- Is M (cell wall) enrichment Gram+ vs Gram- specific?
- Do Actinomycetota show different Q (secondary metabolites) patterns?
- Do Spirochaetota show different M patterns (unique cell wall)?

**Approach**:
- Statistical test for phylum × COG category interactions
- Focus on phyla with known biological differences
- Literature review to interpret deviations

**Impact**: Medium - biological context for universal patterns

**Next Steps**:
1. Fit mixed-effects model: `enrichment ~ COG + (COG | phylum)`
2. Identify significant phylum-specific deviations
3. Biological interpretation with literature

---

### [ecotype_analysis] ANI Distance vs Ecotype Divergence
**Status**: PROPOSED
**Priority**: MEDIUM
**Effort**: Medium

**Research Question**: How does genomic distance (ANI) relate to functional divergence between ecotypes?

**Approach**:
- Use `data/ecotypes_expanded/ani_expanded/` for within-species ANI
- Correlate ANI distance with functional distance (Bray-Curtis on COG profiles)
- Test if functional divergence outpaces genomic divergence (adaptation >> drift)

**Hypothesis**:
- Ecotypes with low ANI distance but high functional distance = rapid ecological adaptation
- Identifies "hotspot" species for studying adaptive evolution

**Impact**: Medium-High - mechanistic understanding of ecotype formation

**Dependencies**:
- Need COG profiles at genome level (not species level)
- ANI matrix analysis

---

## Low Priority / Exploratory Ideas

### [cog_analysis] Temporal Evolution via ANI
**Status**: PROPOSED
**Priority**: LOW
**Effort**: High (complex analysis)

**Research Question**: Does COG enrichment pattern change with evolutionary distance?

**Approach**:
- Use mean intra-species ANI as proxy for clade age
- Compare "young" species (high ANI) vs "old" species (low ANI)
- Test if recently diverged species show different COG patterns

**Hypothesis**: Recently diverged species might show MORE novel genes in niche-specific categories

**Challenge**: ANI as "age proxy" is confounded by mutation rate, selection, recombination

---

### [cog_analysis] Composite COG Function Networks
**Status**: PROPOSED
**Priority**: LOW
**Effort**: High

**Research Question**: Do multi-functional genes (composite COGs like "LV", "EGP") represent functional modules?

**Approach**:
- Analyze co-occurrence of COG categories in same genes
- Build COG co-occurrence network
- Identify functional modules (e.g., L+V = "mobile defense islands")

**Hypothesis**: Composite COGs aren't noise - they're biologically meaningful multi-function genes

**Impact**: Low-Medium - interesting but exploratory

---

### [conservation_vs_fitness] Cross-Organism Essential Gene Families
**Status**: COMPLETED
**Priority**: MEDIUM
**Results**: 859 universally essential families (5%), 15 families essential in all 48 organisms. 1,382 function predictions for hypothetical essentials via module transfer. Universally essential families are 91.7% core. See `projects/essential_genome/`.

**Research Question**: Using FB's `ortholog` table, identify essential gene families conserved across multiple species. Are there universally essential families? Species-unique essentials?

**Approach**: Link essential genes across organisms via BBH orthologs, cluster into families, compare to pangenome conservation. Universally essential families should be universally core.

### [fitness_effects_conservation] The 5,526 "Costly + Dispensable" Genes
**Status**: COMPLETED
**Results**: Costly+dispensable genes are mobile genetic element debris (7.45x keyword enrichment, 11.7x Phage/Transposon SEED enrichment). Poorly annotated (51% vs 75% SEED), taxonomically restricted (OG breadth 15 vs 31), shorter (615 vs 765 bp). psRCH2 is an outlier (21.5% costly+dispensable). See `projects/costly_dispensable_genes/`.

### [core_gene_tradeoffs] Environmental Context of Core Gene Trade-offs
**Status**: PROPOSED
**Priority**: MEDIUM

**Research Question**: Can we connect the lab-measured trade-offs to natural environment data? Do organisms from more variable environments have more trade-off genes in their core genome?

**Approach**: Link to AlphaEarth embedding diversity (from ecotype_analysis) — do species with broader environmental niches show more core gene trade-offs?

### [module_conservation] The 48 Accessory Modules
**Status**: PROPOSED
**Priority**: LOW

**Research Question**: What are the 48 co-regulated gene modules that are <50% core? Are they mobile elements, niche-specific operons, or recently acquired functional units?

**Approach**: Characterize the 48 accessory modules by function (SEED/KEGG), genomic context (near mobile elements?), and organism distribution.

### [NEW] Plasmid vs Chromosomal Gene Functional Profiles
**Status**: PROPOSED
**Priority**: LOW
**Effort**: High (need plasmid annotation)

**Research Question**: Do plasmid-borne genes show different COG profiles than chromosomal genes?

**Challenge**: Need plasmid annotations - not clear if available in BERDL

**Hypothesis**: Plasmids enriched in V (defense), L (mobile elements), potentially M (host interaction)

---

## Completed Ideas

### [lab_field_ecology] Lab Fitness Predicts Field Ecology at Oak Ridge
**Status**: COMPLETED
**Results**: 14 of 26 FB genera detected at Oak Ridge (108 sites). 5 of 11 tested genera correlate with uranium after FDR correction: *Herbaspirillum* and *Bacteroides* increase at contaminated sites, *Caulobacter*, *Sphingomonas*, and *Pedobacter* decrease. Lab metal tolerance suggestive but not significant (rho=0.50, p=0.095). First study linking Fitness Browser data with ENIGMA CORAL field ecology. See `projects/lab_field_ecology/`.

### [field_vs_lab_fitness] Field vs Lab Gene Importance in DvH
**Status**: COMPLETED
**Results**: Field-stress genes are significantly enriched in core genome (83.6% core, OR=1.58, FDR q=0.026) vs 76.3% baseline. Antibiotic and heavy-metal resistance genes are least conserved (73%, 71%). Fitness magnitude matters more than condition type for predicting conservation (CV-AUC 0.52-0.55). Module analysis: 21 ecological modules (0.98 core) vs 9 lab modules (0.52 core). ENIGMA CORAL contains no DvH data. See `projects/field_vs_lab_fitness/`.

### [conservation_vs_fitness] Essential Gene Conservation Analysis
**Status**: COMPLETED
**Results**: Essential genes are 86.1% core vs 81.2% for non-essential (OR=1.56, 18/33 significant after BH-FDR). Essential-core genes are 41.9% enzymes; essential-unmapped are 44.7% hypothetical. See `projects/conservation_vs_fitness/`.

### [fitness_effects_conservation] Quantitative Fitness Effects vs Conservation
**Status**: COMPLETED
**Results**: 16pp gradient from essential (82% core) to neutral (66%). Core genes are MORE likely to be burdens (OR=0.77). Condition-specific genes are more core (OR=1.78). See `projects/fitness_effects_conservation/`.

### [module_conservation] Fitness Modules × Pangenome Conservation
**Status**: COMPLETED
**Results**: Module genes are 86% core vs 81.5% baseline (OR=1.46, p=1.6e-87). 59% of modules are >90% core. Family breadth doesn't predict conservation (ceiling effect). See `projects/module_conservation/`.

### [core_gene_tradeoffs] Core Gene Paradox — Why Are Core Genes More Burdensome?
**Status**: COMPLETED
**Results**: Trade-off genes (both sick AND beneficial) are 1.29x more likely core. 28,017 genes are "costly + conserved" = natural selection signature. Lab reveals cost; pangenome reveals selection pressure. See `projects/core_gene_tradeoffs/`.

### [cofitness_coinheritance] Co-fitness Predicts Co-inheritance
**Status**: COMPLETED
**Results**: Pairwise co-fitness weakly but consistently predicts co-occurrence (delta=+0.003, 7/9 organisms positive, p=1.66e-29). ICA modules show stronger co-inheritance (delta=+0.053, 21/195 significant after FDR), with accessory modules strongest (36% significant after FDR). Prevalence ceiling limits pairwise signal. See `projects/cofitness_coinheritance/`.

### [conservation_fitness_synthesis] Cross-Project Synthesis
**Status**: COMPLETED
**Results**: Narrative synthesis across 4 projects with 3 new summary figures. Story: fitness-conservation gradient (82% → 66%), core genes are paradoxically more burdensome, lab reveals cost while pangenome reveals selection. See `projects/conservation_fitness_synthesis/`.

### [env_embedding_explorer] AlphaEarth Embeddings, Geography & Environment
**Status**: COMPLETED
**Results**: Environmental samples show 3.4x stronger geographic signal in AlphaEarth embeddings (cosine distance 0.27 nearby vs 0.90 far) compared to 2.0x for human-associated samples (0.37 vs 0.75). 38% of the 83K genomes with embeddings are human-associated (clinical bias). 5,774 isolation_source values harmonized to 12 categories. 36% of coordinates flagged as potential institutional addresses (some are legitimate field sites like Rifle, CO). 320 UMAP clusters partially correspond to environment types. See `projects/env_embedding_explorer/`.

### [ecotype_env_reanalysis] Ecotype Reanalysis — Environmental-Only Samples
**Status**: COMPLETED
**Results**: H0 not rejected (p=0.83). Environmental species (n=37, median partial corr 0.051) do NOT show stronger env-gene content correlations than human-associated species (n=93, median 0.084). 47% of ecotype species are human-associated by genome-level classification. The clinical bias does not explain the weak environment signal — phylogeny dominates regardless of sample environment. See `projects/ecotype_env_reanalysis/`.

### [acinetobacter_adp1_explorer] ADP1 Triple Essentiality Concordance
**Status**: COMPLETED
**Results**: FBA essentiality class does not predict growth defects among TnSeq-dispensable genes (chi-squared p=0.63, robust across Q10–Q35 thresholds, Kruskal-Wallis p=0.43). Aromatic degradation genes are the primary source of FBA-growth discordance (OR=9.7, q=0.012), pointing to FBA model environmental assumptions as the main error source. 70% of genes show condition-specific growth defects, supporting the "adaptive flexibility" framework. See `projects/adp1_triple_essentiality/`.

### [adp1_deletion_phenotypes] ADP1 Deletion Collection Phenotype Analysis
**Status**: COMPLETED
**Results**: The 2,034×8 growth matrix reveals a phenotypic continuum (~5 independent dimensions by PCA), not discrete modules (silhouette=0.24). 625 genes (31%) are condition-specific, mapping precisely to expected metabolic pathways: urease for urea, protocatechuate degradation for quinate, Entner-Doudoroff for glucose, glyoxylate shunt for acetate. The 272 missing dispensable genes are shorter, less annotated, and less conserved (76.5% core vs 93.3%, p=1.4e-20). See `projects/adp1_deletion_phenotypes/`.

### [aromatic_catabolism_network] Aromatic Catabolism Support Network in ADP1
**Status**: COMPLETED
**Results**: Aromatic catabolism requires a 51-gene support network organized into 4 subsystems: Complex I/NADH reoxidation (21 genes, 41%), aromatic pathway (8), iron acquisition (7), PQQ biosynthesis (2), plus regulation (6). FBA captures 1.76× higher Complex I flux on aromatics but misses the bottleneck (0% essentiality); 30/51 genes lack FBA reaction mappings. Co-fitness analysis assigns 16/23 unknown genes to subsystems, identifying two DUF proteins as candidate Complex I accessory factors (r>0.98). Cross-species data shows the dependency is on high-NADH-flux substrates generally (acetate, succinate show larger Complex I defects than aromatics), not aromatic catabolism exclusively. See `projects/aromatic_catabolism_network/`.

### [respiratory_chain_wiring] Condition-Specific Respiratory Chain Wiring in ADP1
**Status**: COMPLETED
**Results**: ADP1's branched respiratory chain (62 genes, 8 subsystems) uses qualitatively different configurations per carbon source: quinate requires only Complex I, acetate requires everything, glucose requires nothing. The paradox (quinate has lower NADH yield but higher Complex I dependency) is resolved by NADH flux rate — concentrated TCA burst from ring cleavage vs distributed production. ADP1 has 3 parallel NADH dehydrogenases (Complex I, NDH-2, ACIAD3522) with non-overlapping condition requirements. Cross-species: after correcting NDH-2 false positives (filtering to 1-2 hits/organism), NDH-2 presence does NOT predict reduced Complex I aromatic deficits (p=0.52), suggesting ADP1's wiring is species-specific. See `projects/respiratory_chain_wiring/`.

---

## Ideas to Discuss / Refine

_Capture half-baked ideas here for future refinement_

### Metagenome-Assembled Genomes (MAGs) Analysis
- Do incomplete genomes (MAGs) show different COG patterns?
- Could be artifact (missing core genes) or real (streamlined genomes)
- Would need quality metrics (CheckM completeness)

### Functional Redundancy Analysis
- Do species with larger pangenomes have more functional redundancy?
- Multiple gene clusters mapping to same COG category
- Trade-off between genetic diversity and functional diversity

### Horizontal Gene Transfer Directionality
- Can we infer donor vs recipient species based on COG composition?
- Species that gain L+V might be recipients
- Species that lose core genes might be specialists

---

## Cross-Project Integration Opportunities

### cog_analysis × ecotype_analysis
- **Ecotype functional differentiation** (HIGH PRIORITY)
- ANI distance vs functional distance
- Within-species functional diversity

### cog_analysis × pangenome_openness
- **Openness vs functional composition** (HIGH PRIORITY)
- Open pangenomes = more HGT = more L enrichment?

### conservation_vs_fitness × fitness_modules
- **Module-level conservation analysis** (COMPLETED in `module_conservation`)
- Module genes are 86% core; modules are functional units of the core genome
- Next: characterize the 48 accessory modules

### fitness_effects_conservation × ecotype_analysis
- **Trade-off genes × environmental niche breadth**
- Do species from variable environments have more trade-off genes in their core?
- Connect lab-measured costs to natural selection pressures

### ecotype_analysis × pangenome_openness
- Do open pangenomes have more ecotypes?
- Is functional diversity driver of ecotype formation?

---

## Notes

- Keep this document updated as ideas emerge during analysis
- Tag ideas with source project in brackets: `[project_name]`
- Link to relevant notebooks, data files, or papers when adding ideas
- When an idea moves to IN_PROGRESS, create a project directory or notebook
- Archive completed ideas with links to results

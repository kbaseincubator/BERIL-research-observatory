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

### [truly_dark_genes] Truly Dark Genes — What Remains Unknown After Modern Annotation?
**Status**: IN_PROGRESS
**Priority**: HIGH
**Effort**: Medium (2-3 weeks)

**Research Question**: Among the ~6,400 FB genes that remain hypothetical even after bakta v1.12.0 reannotation, what distinguishes them from annotation-lag dark matter, and can fitness phenotypes + sparse annotations prioritize them for experimental characterization?

**Approach**:
- Fork from `functional_dark_matter` NB12 insight: 83.7% of "dark" genes are annotation-lag, not truly unknown
- Characterize the residual ~6,400 truly dark genes (shorter? more divergent? species-specific?)
- Mine sparse annotations (UniRef50, Pfam HMMER, ICA modules, db_xrefs) as partial clues
- Test cross-organism fitness concordance for truly dark orthologs
- Produce prioritized ~50-100 candidates with experimental protocols

**Hypotheses**:
- Truly dark genes are structurally distinct (shorter, less conserved, taxonomically restricted)
- They are enriched in stress conditions and accessory genomes
- Partial annotations (UniRef50 + Pfam + module context) can narrow functional hypotheses

**Impact**: High — reduces the "dark matter" problem from 57,011 genes to ~6,400 genuinely unknown ones and provides a tractable experimental target list

**Dependencies**:
- Existing: `functional_dark_matter` data (NB12 bakta enrichment)
- Existing: `bakta_reannotation` Delta Lake tables
- Existing: FB-pangenome link table from `conservation_vs_fitness`

**Progress**:
- ✅ Project structure created: `projects/truly_dark_genes/`
- ✅ Research plan written
- ⏳ Next: NB01 census and characterization
- ⏳ Next: NB02 Spark data enrichment

**Location**: `projects/truly_dark_genes/`

---

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

### [metabolic_capability_dependency] Metabolic Capability vs Metabolic Dependency
**Status**: IN_PROGRESS
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

**Progress**:
- ✅ Project structure created: `projects/metabolic_capability_dependency/`
- ✅ Research plan written with detailed hypotheses and approach
- ✅ Five analysis notebooks scaffolded (NB01-05)
- ✅ Utility module created: `src/pathway_utils.py`
- ⏳ Next: Run NB01 on JupyterHub to extract GapMind pathway data
- ⏳ Next: Extend NB01 to include gene-level mappings
- ⏳ Next: Complete NB02-03 for pathway classification
- ⏳ Next: Run NB04-05 for Black Queen test and ecotype analysis

**Location**: `projects/metabolic_capability_dependency/`

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

### [ibd_phage_targeting] Metagenome-Prioritized Phage Cocktails for Crohn's Disease and IBD
**Status**: COMPLETED
**Results**: All 5 pillars closed across 32 notebooks. **Pillar 1**: 4 reproducible IBD ecotypes (E0/E1/E2/E3) on 8,489 cMD MetaPhlAn3 samples; HMP2 external replication χ² p=0.016; UC Davis distributes E0 27 % / E1 42 % / E3 31 % (χ² p=0.019). **Pillar 2**: rigor-controlled within-ecotype × within-substudy meta yields 51 E1 + 40 E3 Tier-A candidates; 6 actionable Tier-A core (*H. hathewayi* 4.0, *M. gnavus* 3.8, *E. coli* 3.6, *E. lenta* 3.3, *F. plautii* 3.3, *E. bolteae* 2.8); HMP2 88.2 % E1 sign-concordance external replication. **Pillar 3**: all 8 H3 sub-hypotheses tested (5 SUPPORTED + 1 PARTIALLY + 2 PARTIAL + 1 NOT); 2 cross-corroborated 6-line mechanism narratives (iron-acquisition centred on *E. coli* AIEC; bile-acid 7α-dehydroxylation centred on *F. plautii* / *E. lenta* / *E. bolteae*); NB07d CC1 r=0.96 collapses all narratives into single joint axis. **Pillar 4**: 3-layer phage-evidence stack (literature + PhageFoundry experimental 17,672 pairs + HMP2 in-vivo); concrete 5-phage *E. coli* AIEC cocktail (DIJ07_P2 + LF73_P1 + AL505_Ev3 + 55989_P2 + LF110_P2) at 95 % strain coverage; *H. hathewayi* + *F. plautii* GAP confirmed across all 3 layers. **Pillar 5**: per-patient cocktail drafts for 14 of 23 UC Davis patients (61 %); pure phage cocktail structurally infeasible for E1 ecotype — 3-strategy hybrid required (Novel Contribution #23); patient 6967 longitudinal E1→E3 drift validated with M. gnavus 14× expansion + cocktail Jaccard 0.60; state-dependent dosing rule established with M. gnavus qPCR proposed as cheap clinical proxy (Novel Contribution #24); NB17 cross-cutting synthesis delivers per-patient master table + target decision matrix + 4-phase clinical-translation roadmap. 24 numbered Novel Contributions including: cMD substudy×diagnosis nesting unidentifiability (#6), feature leakage in cluster-stratified DA (#7), within-ecotype × within-substudy meta-analysis as confound-free design (#8), adversarial review as required complement to /berdl-review (#9), pool ≠ flux methodology lesson (#15), bile-acid coupling cost as primary Pillar-4 ecological annotation (#16), species-abundance- vs strain-content-mediated CD-association as distinguishable mechanism axis (#18), cohort batch effects in m/z metabolomics clustering (#19), multi-pillar narratives collapse to single multi-omics joint factor (#21), 3-layer phage-evidence convergence as Pillar-4 rigor pattern (#22). See `projects/ibd_phage_targeting/`.

### [plant_microbiome_ecotypes] Plant Microbiome Ecotype Functional Classification
**Status**: COMPLETED (Phase 2b finalized 2026-04-25)
**Results**: 15 notebooks + 4 follow-up scripts on 293K genomes / 25,660 species. Headline post-Phase-2b verdicts: **H2 supported** — beneficial (PGP) genes are core 64.6% vs pathogenic 45.2%, p=3.4×10⁻¹²⁵. **H5 supported** — 48/50 plant-enriched eggNOG OGs survive real per-species phylum + log₁₀(genome_size) regression at q<0.05; cytochrome oxidase (COG1845) and Fe-S cluster biogenesis (COG0316) lead. **H6 supported in 2 species** — *Xanthomonas campestris* × Brassica (46/47 in best subclade, p=3.3×10⁻¹¹) and *X. vasicola* × *Zea mays* (47/52, p=1.7×10⁻¹⁰), confirming canonical pathovar-host specializations at the genomic level. **H1 weakly supported** — db-RDA location-only R²=0.060 + significant PERMDISP; the original PERMANOVA R²=0.527 was a panel + sampling artifact (86% loss after excluding top-3 species per compartment). **H3 not supported** — small redundancy |d|≈0.4 (NB06's reported −7.54 was a Cohen's d formula error). **H7 weakly supported** — 5/17 testable species pass Bonferroni-Fisher (47/65 candidates lack phylogenetic-tree coverage, a BERDL database limitation). **H0 partially rejected** — three-tier marker framing: 3 species-level (N-fix, ACC deaminase, T3SS), 5 cassette-level (phenazine, CWDEs, phosphate-sol, effector), 6 not robust. Methodological contributions: paired adversarial-review pattern (caught 5 critical issues the standard reviewer missed; documented in `docs/adversarial_review_2026-04-24.md`); bakta-vs-IPS Pfam audit (12/22 marker Pfams silently missing from `bakta_pfam_domains`, project-independent BERDL pitfall in `docs/pitfalls.md`); cluster-robust GLM at genus level as a tractable PGLMM analogue. See `projects/plant_microbiome_ecotypes/`.

### [pgp_pangenome_ecology] PGP Gene Distribution Across Environments & Pangenomes
**Status**: COMPLETED
**Results**: H1 SUPPORTED — pqqC × acdS co-occur at OR = 7.24 (strongest pair), forming a vertically inherited rhizosphere module; nifH forms a separate ecological guild (negatively associated with pqqC, depleted in soil). H2 SUPPORTED — acdS (OR = 7.0) and pqqC (OR = 2.9) strongly enriched in soil/rhizosphere, surviving phylum fixed effects. H3 REJECTED — PGP genes are predominantly core (mean 29.7% accessory vs 53.2% genome-wide baseline), contra the HGT hypothesis. H4 PARTIALLY SUPPORTED — trp completeness predicts ipdC (OR = 2.81) but tyrosine "negative control" also significant (OR = 3.62) due to TyrR co-regulation; soil species show reversal (OR = 0.30). First pangenome-scale analysis across 293K genomes, 27K species. See `projects/pgp_pangenome_ecology/`.

### [bacdive_phenotype_metal_tolerance] BacDive Phenotype Signatures of Metal Tolerance
**Status**: COMPLETED
**Results**: BacDive phenotypes (Gram stain, oxygen tolerance, enzyme activities, metabolite utilization) capture real metal tolerance signal (R²=0.16 alone, 7/10 features significant after FDR) but are entirely phylogenetically confounded — adding phenotype features to a taxonomy-based model provides zero improvement (delta R²=-0.009). Genome-encoded metal resistance gene count is the true predictor (full model R²=0.63). Gram stain is the strongest univariate predictor (d=-0.61) but indistinguishable from phylogeny. Urease effect reversed (d=-0.18, driven by Actinomycetes). Catalase shows Simpson's paradox (positive overall, negative within every major class). First large-scale test of BacDive phenotypes as metal tolerance predictors across 5,647 species. See `projects/bacdive_phenotype_metal_tolerance/`.

### [nmdc_community_metabolic_ecology] Community Metabolic Ecology via NMDC × Pangenome Integration
**Status**: COMPLETED
**Results**: Weak but consistent Black Queen signal detected in community metabolomics: 11/13 (85%) amino acid biosynthesis pathways trend in BQH-predicted direction (binomial p=0.011). Leucine (r=−0.390, q=0.022, n=62) and arginine (r=−0.297, q=0.049, n=80) biosynthesis are FDR-significant. Community metabolic potential separates strongly by ecosystem type (PC1=49.4% variance; Soil vs. Freshwater Mann-Whitney p<0.0001); 17/18 aa pathways significantly differentiated across ecosystem types. First BERDL integration of NMDC multi-omics with GapMind pangenome pathway completeness across 220 samples. See `projects/nmdc_community_metabolic_ecology/`.

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

### [counter_ion_effects] Counter Ion Effects on Metal Fitness Measurements
**Status**: COMPLETED
**Results**: Counter ions (chloride, sulfate, acetate) are NOT the primary confound in Fitness Browser metal experiments. 39.8% of metal-important genes overlap with NaCl stress across 19 organisms and 14 metals, but this reflects shared stress biology, not counter ion contamination. Key evidence: ZnSO₄ (0 mM Cl⁻) shows 44.6% NaCl overlap — higher than most chloride metals. The Metal Fitness Atlas core enrichment is fully robust after removing shared-stress genes (7/14 metals show stronger enrichment). DvH metal-NaCl correlation hierarchy (Zn r=0.72 → Fe r=0.09) follows toxicity mechanism, not Cl⁻ dose. See `projects/counter_ion_effects/`.

### [fw300_metabolic_consistency] Metabolic Consistency of Pseudomonas FW300-N2E3
**Status**: COMPLETED
**Results**: Four BERDL databases (Web of Microbes, Fitness Browser, BacDive, GapMind) show 94% mean concordance for FW300-N2E3 metabolites, but this is structurally driven by FB (21/21=100%) and GapMind (13/13=100%). BacDive is the only informative variable (3/7=43%, binomial p=0.40 vs baseline). The key biological finding is tryptophan overflow: FW300-N2E3 produces tryptophan (WoM), has 231 fitness genes (FB), a complete pathway (GapMind), yet 0/50 *P. fluorescens* strains utilize it (BacDive) — consistent with cross-feeding. Per-strain BacDive consensus, approximate-match flagging, and concordance decomposition are methodological contributions. See `projects/fw300_metabolic_consistency/`.

### [genotype_to_phenotype_enigma] Genotype × Condition → Phenotype Prediction from ENIGMA Growth Curves
**Status**: COMPLETED
**Results**: Integrated five datasets (ENIGMA growth curves 27,632 wells; ENIGMA Genome Depot 3.7M KO annotations; Fitness Browser RB-TnSeq for 7 anchors; Web of Microbes exometabolomics for 6 anchors; Carbon Source Phenotypes 795 genomes × 379 conditions) into a 46,389-pair training corpus across 727 genomes and 135 genera. **Binary growth is genuinely predictable on amino acids (AUC 0.775) and nucleosides (0.780) from KO content** under genus-blocked holdout across 106 genera; moderately on carbon sources (0.695); NOT on metals, antibiotics, or nitrogen. **Continuous kinetics (µmax, lag, yield) are fundamentally not predictable from KO presence** under cross-genus holdout — a biological limit (gene presence encodes capability, not rate), not a data problem. SHAP identifies condition-specific catabolic genes (proP transporter → proline growth, rbsB/C/A ribose transporter → ribose growth, pcaB → aromatic catabolism), but FB concordance is weak (1.19× enrichment) because gene-presence-across-genera and gene-essentiality-within-strain are different biological questions. **The n=7 → n=46K comparison quantifies the corpus size required to shift from genome-scale to gene-specific prediction.** WoM exometabolomics (n=6, 105 metabolites) fails under multivariate GBDT (AUC 0.500) but per-metabolite univariate correlation recovers **940 mechanistic gene-metabolite associations** across all 62/62 variable metabolites (454 production + 486 consumption), illustrating that method must match sample size. A global pH-driven niche partition (464K MicrobeAtlas samples) explains local Oak Ridge co-occurrence: Rhodanobacter-Ralstonia-Dyella occupies environments 1.35 pH units more acidic than Brevundimonas-Caulobacter-Sphingomonas worldwide. Act III converts 42,771 held-out predictions into a **50-experiment active-learning proposal** ranked by `error × (1 − confidence) × field_weight`, prioritizing fumaric acid, melibionic acid, nitrate, and low-pH-compatible substrates on Prescottella and Microbacterium (the two genera the current model predicts least reliably). New pitfalls contributed to `docs/pitfalls.md`: interactive-session artifacts without committed notebooks, WoM action-code interpretation (I/E vs N), FB locusId→KO two-hop mapping. See `projects/genotype_to_phenotype_enigma/`.

### [enigma_sso_asv_ecology] SSO Subsurface Community Ecology — Contamination Plume Model
**Status**: COMPLETED
**Results**: H1a SUPPORTED — significant distance-decay across the 9 SSO wells (~6 m span; Mantel ρ=0.323, p=0.029), but driven by east-west axis (ρ=0.227), not hillslope (ρ=−0.049). The U3-M6-L7 diagonal corridor is more similar than expected (BC 0.56–0.65) — these wells trace the NE→SW contamination plume flow path. H1c SUPPORTED — depth (zone) explains 27.5% of variance (p=0.0001) vs well 19.2% (NS), consistent with the plume in the saturated zone. Genus-level functional inference (65 genera, 12 biogeochemical processes) maps the thermodynamic redox ladder onto the grid: denitrification peaks at M5 (*Rhodanobacter* 7.7%), iron oxidation at U3 (*Sideroxydans* 2.8%), fermentation at L9 (5.3%). M6 is the anaerobic dead zone (lowest for all oxidative processes). GW enriched in plume taxa (*Rhodanobacter* 2.9×, *Gallionella* 8.9×, *Sideroxydans* 7.0× vs sediment). GW communities temporally stable (well R²=49.9%, date R²=0.8% over 9 days; Mantel ρ=0.867). Guild co-occurrence reveals coupled nitrifier×iron oxidizer (ρ=+0.95) and mutually exclusive denitrifier×syntroph (ρ=−0.67) across the redox gradient. First spatially explicit mapping of biogeochemical processes at meter scale on a contamination plume. See `projects/enigma_sso_asv_ecology/`.

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

---


---

### [oak_ridge_cultivation_gap] What Metabolic Functions Does the Cultured Collection Miss at Oak Ridge?
**Status**: PROPOSED
**Priority**: HIGH
**Effort**: Medium (3–4 weeks)

**Research Question**: At Oak Ridge ENIGMA SFA, what metabolic functions does BERDL's cultured-isolate genome collection systematically under-represent compared to MAGs recovered from metagenomes of the same site? In plain terms: if a researcher only used the cultured genomes to characterize the metabolic potential of the Oak Ridge subsurface, what would they get wrong?

**Approach**:
- Inventory paired data in `enigma_coral`: 6,705 cultured `sdt_genome` rows + 623 `sdt_bin` MAG rows from the same site, plus newly released metagenomes (Lui 2025).
- For each metabolic function in a curated marker dictionary (Wood–Ljungdahl, [NiFe]/[FeFe]-hydrogenases, dsr-apr-sat, mtrA-mtrC-omcS, narGHI/napAB, mcrA, glycine-betaine osmoprotectants, MGE/conjugation markers, CPR/DPANN-signature genes), compute the per-function presence rate in the cultured cohort vs the MAG cohort.
- Report a per-function "cultivation-coverage" table with effect sizes, BH-FDR-adjusted p-values, and a one-line interpretation per row.
- Validate against published ORFRC findings: Tian 2020 (Patescibacteria streamlining), Goff 2024 (HMR-laden MGEs in MAGs), Wu 2023 (depth-stratified C/N cycling).
- Generalize: extend the methodology into a reusable module that future BERDL projects can call to flag whether their cohort is cultivation-biased before drawing conclusions.

**Hypotheses**:
- **H1**: Specific metabolic functions are significantly depleted in the cultured cohort relative to the MAG cohort at Oak Ridge — most prominently CPR/DPANN-signature genes (per Tian 2020), iron-reduction surface-electron-transfer genes (per Mitzscherling-style rock-attached pattern), and mobile-element/MGE-resident heavy metal resistance genes (per Goff 2024).
- **H2**: A subset of functions is *enriched* in the cultured cohort (sulfate reduction, broad anaerobic respiration markers from cultivable Bacillota_B) — recapitulating the Mont Terri porewater-bias signature in a different subsurface system.
- **H0**: Cultured and MAG gene-content distributions at Oak Ridge are statistically equivalent across the marker dictionary.

**Impact**: Produces a per-function "cultivation-coverage" reference table that ORFRC researchers can use to decide which cultured-genome claims to caveat. Provides BERDL/KBase data team with a prioritized list of clades worth additional cultivation effort. Generalizes the H3 methodology from a single binary marker pair to a multi-function diagnostic, validated against an independent system with published ground truth. No quantitative cultivation-bias index currently exists in the literature (per Escudeiro 2022 review).

**Dependencies**:
- Existing: `clay_confined_subsurface` H3 framework (NB02/NB05/NB06 templates, marker dictionary)
- Existing: ENIGMA `sdt_bin` / `sdt_genome` / `sdt_assembly` data in `enigma_coral`
- New: MAG contig sequences in MinIO; bakta annotation of MAGs that lack eggNOG annotations (re-uses `bakta_reannotation` patterns documented in `docs/pitfalls.md`)
- New: Cross-link MAGs to GTDB taxonomy (sourmash or single-copy-marker approach)

**Location**: `projects/oak_ridge_cultivation_gap/` (to be created via /berdl_start)


---

### [bacillota_b_subsurface_accessory] What Accessory Gene Content Distinguishes Deep-Clay Bacillota_B from Soil Congeners?
**Status**: PROPOSED
**Priority**: HIGH
**Effort**: Medium (3-4 weeks)

**Research Question**: Within Bacillota_B (Desulfosporosinus, BRH-c8a Peptococcaceae, BRH-c4a Desulfotomaculales, etc.), what gene clusters are enriched in deep-clay-isolated genomes vs phylum-matched soil-baseline genomes — beyond the curated marker dictionary used in clay_confined_subsurface? Includes a Phase 1 correction to the clay project's IR-side analysis (which used KOs K07811/K17324/K17323 that turn out to be TMAO reductase / glycerol ABC / glycerol permease, not iron reduction).

**Approach**:
- NB01: pull all ~6700 Bacillota_B genomes from BERDL pangenome with isolation_source metadata; assemble deep-clay anchor (~15-25 from clay project + BacDive expansion) and phylum-matched soil-baseline (~100-200).
- NB02: per-genome eggNOG-OG presence vector for the cohort (use OG IDs as cross-species orthology surrogate).
- NB03: per-OG Fisher's exact (anchor vs baseline) with BH-FDR; retain OGs with q<0.05 AND fold≥3 AND ≥3 anchor genomes.
- NB04: functional annotation of enriched OGs (eggNOG + bakta) — group into pre-registered categories (sporulation revival, anaerobic respiration accessories, mineral attachment EPS, osmoadaptation, anaerobic-niche regulators).
- NB05: H2 genome-compactness test (anchor vs baseline genome size + gene count, CheckM-controlled).
- NB06: Phase 1 correction — re-run clay H3 IR analysis using PFAM PF14537 multi-heme cytochrome + CXXCH heme-motif counting; commit corrected REPORT addendum to clay project.
- NB07: synthesis.

**Hypotheses**:
- H1: ≥10 OGs are enriched in deep-clay Bacillota_B (Fisher BH-FDR q<0.05, fold≥3) and fall into pre-registered functional categories (sporulation, anaerobic respiration accessories, mineral attachment, osmoadaptation, regulators).
- H2: Deep-clay Bacillota_B have smaller mean genome size + gene count than soil baseline (CheckM-controlled).
- H3 (corrected): Deep-clay Bacillota_B carry PFAM PF14537 multi-heme cytochrome content at higher rates than soil baseline (this is the clay project's H3 IR-side, redone with correct markers).

**Impact**: Gene-cluster-level (not curated-marker) characterization of subsurface Bacillota_B specialization. Provides target list for future biochemistry / fitness-screen work. Closes a real bug in clay_confined_subsurface's IR analysis (PR #231 already merged; correction needed).

**Dependencies**:
- Existing: clay_confined_subsurface (cohort tagging + within-Bacillota_B SR finding); oak_ridge_cultivation_gap (pyrodigal+pyhmmer KOfam annotation pipeline).
- New: BacDive Bacillota_B clay-strain expansion via GCA→GTDB linkage.

**Location**: `projects/bacillota_b_subsurface_accessory/`


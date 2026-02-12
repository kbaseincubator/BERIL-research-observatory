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

### [NEW] Plasmid vs Chromosomal Gene Functional Profiles
**Status**: PROPOSED
**Priority**: LOW
**Effort**: High (need plasmid annotation)

**Research Question**: Do plasmid-borne genes show different COG profiles than chromosomal genes?

**Challenge**: Need plasmid annotations - not clear if available in BERDL

**Hypothesis**: Plasmids enriched in V (defense), L (mobile elements), potentially M (host interaction)

---

## Completed Ideas

_Move completed projects here with links to results_

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

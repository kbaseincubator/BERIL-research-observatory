# Research Plan: Metabolic Capability vs Dependency

## Research Question

When a bacterium's genome encodes a complete biosynthetic or utilization pathway, does the organism actually depend on it? Can we distinguish metabolic **capability** (genome predicts pathway present) from metabolic **dependency** (fitness data shows pathway genes matter), and does this distinction predict which pathways are candidates for evolutionary gene loss?

## Hypothesis

- **H0**: Pathway completeness (GapMind) is sufficient to predict metabolic importance — complete pathways are uniformly important and incomplete pathways are uniformly unimportant.
- **H1a**: Pathways classified as "latent capabilities" (complete but fitness-neutral) are more likely to be accessory in the pangenome — candidates for future gene loss (Black Queen Hypothesis).
- **H1b**: Species with more latent capabilities have more open pangenomes (ongoing genome streamlining).
- **H1c**: "Incomplete but important" pathways represent annotation gaps or salvage routes that GapMind misses.
- **H2**: Within-species binary pathway profiles define metabolic ecotypes that correlate with pangenome conservation patterns and environment metadata.

## Pathway Classification Framework

Four categories classify each organism × pathway combination:

| Category | Pathway Complete? | Fitness-Important? | Interpretation |
|---|---|---|---|
| **Active Dependency** | Yes | Yes | Organism needs this pathway |
| **Latent Capability** | Yes | No | Genomic baggage / Black Queen candidate |
| **Incomplete but Important** | No | Yes | Salvage/partial dependency, or annotation gap |
| **Missing** | No | No | Pathway absent and unneeded |

## Related Projects

This project builds on an extensive analytical pipeline from prior BERIL projects. Understanding these relationships avoids redundant work and ensures we leverage proven methodology.

### Direct Data Dependencies

| Project | What we reuse | Status |
|---|---|---|
| `essential_metabolome` | FB→genome mapping (`fb_genome_mapping_manual.tsv`), GapMind pilot data for 7 organisms, identification of GapMind coverage gaps (E. coli absent) | Data on disk |
| `essential_genome` | Cross-organism ortholog families (`all_ortholog_groups.csv`), universal vs variable essentiality classification | Data on disk |
| `conservation_vs_fitness` | FB-pangenome link table methodology (177K links, 44 organisms), essential gene classification, SEED annotations | Methodology; data must be regenerated via NB01 or copied from JupyterHub |
| `fitness_effects_conservation` | Per-gene fitness statistics methodology, fitness breadth approach | Methodology; data must be regenerated via NB01 |

### Methodological Template

| Project | What we adopt |
|---|---|
| `metal_fitness_atlas` | **Primary template**. Uses the same framework (fitness × conservation × BQH) applied to metal tolerance. Found 87.4% of metal-fitness genes are core (OR=2.08). We adopt its cross-species conservation pipeline and pangenome-scale scoring methodology. |
| `fitness_effects_conservation` | Demonstrated that **fitness breadth** (# conditions where gene is important) predicts conservation better than median fitness (16pp gradient). We incorporate breadth into our importance score. |
| `core_gene_tradeoffs` | Demonstrated that lab fitness ≠ natural selection — 28,017 genes are "costly in lab but conserved in nature." We must account for condition-type effects when classifying pathways as "latent." |
| `field_vs_lab_fitness` | Showed field-important genes are 83.6% core vs 76.3% baseline. **Condition-type stratification** (stress/carbon/nitrogen/antibiotic) reveals distinct conservation patterns. We adopt this stratification for fitness aggregation. |

### Contextual Findings That Inform Interpretation

| Project | Key finding |
|---|---|
| `conservation_fitness_synthesis` | The conserved genome is functionally active, not inert. 16pp fitness-conservation gradient establishes the evolutionary landscape for our pathway categories. |
| `cog_analysis` | Universal "two-speed genome" — core enriched in translation and metabolism, novel enriched in mobile elements. Establishes baseline expectations for metabolic gene conservation. |
| `ecotype_analysis` | Phylogeny dominates gene content similarity (60.5% of species). **Our NB04 ecotype analysis must control for phylogenetic distance**, or ecotypes may simply reflect phylogenetic structure. |
| `cofitness_coinheritance` | Pathway genes that co-occur in pangenomes tend to be co-fit (73% of accessory modules show significant co-inheritance). Validates using pathway-level aggregation of fitness. |
| `pangenome_pathway_ecology/geography` | Both designed but unexecuted. Overlap with our Tier 2 analysis (GapMind × pangenome openness). We subsume their core analyses and will reference them in findings. |
| `pangenome_openness` | **Null result**: pangenome openness does not correlate with environment/phylogeny effect sizes. Tempers expectations for H1b. |
| `module_conservation` | Module family breadth does NOT predict conservation (null result). Conservation of functional groups isn't simply proportional to how widespread they are. |

## Literature Context

- **Black Queen Hypothesis** (Morris, Lenski & Zinser, 2012, mBio): Gene loss can be adaptive when a gene function is "leaky" — available as a public good. Extended by the Constructive BQH (Takeuchi et al. 2024, ISME J) showing new functions can arise under gene loss pressure, and community-scale BQH dynamics in the human gut (Madi et al. 2023, eLife).
- **GapMind**: Price, Deutschbauer & Arkin built GapMind for amino acid biosynthesis (2020, mSystems) and carbon source catabolism (2022, PLOS Genetics). Finds complete paths for 63% of utilized carbon sources; 85% when validated with genetic data.
- **RB-TnSeq & Functional Modules**: ICA of fitness compendia reveals functional gene modules (Thompson et al. 2024, mSystems). The Fitness Browser is the same lab group's experimental resource (Wetmore et al. 2015).
- **Key gap**: No study has systematically compared GapMind pathway predictions against fitness data to classify pathways as "active dependencies" vs "latent capabilities," or tested the BQH prediction at pangenome scale.

## Approach: Two Tiers

### Tier 1 — Fitness-Validated Classification (~34 FB organisms)

For FB organisms with high-quality pangenome links (>=90% DIAMOND coverage):

1. Extract GapMind pathway completeness per genome (best score across sequence scopes and pathway routes)
2. Verify GapMind-FB organism coverage (essential_metabolome found only 7/45 had coverage; we must check the full 48)
3. Map genes to metabolic pathways using eggNOG KEGG orthologs (KOs) — more precise than KEGG pathway map IDs used previously
4. Map annotated gene clusters to FB genes via the FB-pangenome link table
5. For each pathway × organism, aggregate fitness effects using **multiple metrics**:
   - Median fitness (magnitude of effect)
   - **Fitness breadth** (fraction of conditions with |fitness| > 1) — stronger conservation predictor per fitness_effects_conservation
   - **Condition-type stratification** (carbon source / nitrogen source / stress / other) — per core_gene_tradeoffs and field_vs_lab_fitness findings
   - Fraction essential (putative essentials with no transposon insertions)
6. Classify into four categories using data-driven thresholds calibrated against the known fitness-conservation gradient
7. Validate: Active Dependencies should be enriched in core gene clusters; Latent Capabilities enriched in accessory (following metal_fitness_atlas OR methodology)

### Tier 2 — Pan-Bacterial Pathway Conservation (27K species)

1. For each species, extract per-genome pathway completion status from GapMind (using best score per genome × pathway, `sequence_scope = 'all'`)
2. Compute species-level pathway metrics: fraction of genomes with complete pathway, variation in completeness
3. Compare `sequence_scope = 'core'` vs `'all'` — pathways where core-only is incomplete but all-genes is complete indicate accessory pathway genes (direct BQH evidence)
4. Correlate pathway conservation with pangenome openness (`no_aux_genome / no_gene_clusters`)
5. **Add phylogenetic controls**: stratify by phylum/class or use phylogenetic independent contrasts to ensure correlations aren't driven by shared ancestry (per ecotype_analysis finding that phylogeny dominates)
6. Contextualize against pangenome_openness null result and pangenome_pathway_ecology/geography designs

### Tier 3 — Metabolic Ecotypes (within-species variation)

1. For species with sufficient genome diversity (>=50 genomes), build binary pathway profiles
2. Cluster genomes by pathway profiles (hierarchical clustering, Jaccard distance)
3. Count distinct metabolic ecotypes per species
4. Correlate ecotype count with pangenome openness and niche breadth (AlphaEarth, 28% coverage)
5. **Control for phylogenetic structure**: use genome ANI to verify ecotypes aren't simply reflecting intra-species phylogenetic clades (ecotype_analysis showed phylogeny dominates gene content)

## Query Strategy

### Tables Required

| Table | Purpose | Estimated Rows | Filter Strategy |
|---|---|---|---|
| `kbase_ke_pangenome.gapmind_pathways` | Pathway completeness per genome | 305M | Filter by `clade_name` or aggregate by `pathway` |
| `kbase_ke_pangenome.gene_cluster` | Core/accessory status | 132M | Filter by `gtdb_species_clade_id` |
| `kbase_ke_pangenome.eggnog_mapper_annotations` | KEGG KO and EC annotations | 93M | Filter by `query_name` (gene_cluster_id) |
| `kbase_ke_pangenome.pangenome` | Pangenome stats (openness) | 27K | Safe to scan |
| `kbase_ke_pangenome.genome` | Genome metadata | 293K | Safe to scan |
| `kescience_fitnessbrowser.genefitness` | Fitness values | 27M | Filter by `orgId` |
| `kescience_fitnessbrowser.gene` | Gene metadata | ~200K | Filter by `orgId` |
| `kescience_fitnessbrowser.exps` | Experiment metadata (condition types) | ~7.5K | Safe to scan |

### Key Data Properties Discovered

1. **GapMind row multiplicity**: Each genome × pathway has multiple rows — one per `sequence_scope` (all, core, aux) and one per alternative pathway route. Must aggregate with `MAX(score)` grouped by `genome_id, pathway`.
2. **GapMind genome_id format**: Uses bare accessions (`GCF_...`) NOT GTDB-prefixed IDs (`RS_GCF_...`). Must strip `RS_`/`GB_` prefix when joining to pangenome tables.
3. **80 pathways**: 18 amino acid biosynthesis + 62 carbon source utilization
4. **Three sequence scopes**: `all` (all genes), `core` (core pangenome genes only), `aux` (accessory genes only) — the `core` vs `aux` split is itself informative for our analysis
5. **Score categories**: complete, likely_complete, steps_missing_low, steps_missing_medium, not_present
6. **FB-pangenome link**: 34 organisms with >=90% DIAMOND coverage, link table has `orgId`, `locusId`, `gene_cluster_id`, `is_core`
7. **GapMind FB coverage gap**: essential_metabolome found E. coli absent from GapMind dataset and only 7/45 FB organisms covered. Must verify coverage for all 48 FB organisms before analysis design.
8. **Upstream data availability**: essential_metabolome has `fb_genome_mapping_manual.tsv` (8 organisms); essential_genome has `all_ortholog_groups.csv`. conservation_vs_fitness and fitness_effects_conservation data files exist on JupyterHub but not cached locally — NB01 must regenerate the link table and fitness stats.

### Performance Plan

- **Tier**: JupyterHub for all heavy Spark queries (GapMind aggregation, eggNOG joins)
- **REST API**: Only for small exploratory queries during development
- **Estimated complexity**: Moderate (largest operation is aggregating gapmind_pathways by species)
- **Known pitfalls**: GapMind genome_id prefix mismatch, string-typed fitness columns, annotation NULLs
- **Performance fix**: Use Spark `.write.csv()` for large extracts (>1M rows) instead of `.toPandas()` to avoid OOM — the species pathway summary (~23M rows) must NOT be collected to driver

## Analysis Plan

### Notebook 1: Data Extraction (Spark, JupyterHub)

- **Goal**: Extract and cache all required data, verify data availability
- **Steps**:
  1. **Verify upstream data**: Check for `essential_metabolome/data/fb_genome_mapping_manual.tsv` and `essential_genome/data/all_ortholog_groups.csv`; load what's available
  2. **GapMind-FB coverage check**: For all 48 FB organisms, verify which have GapMind pathway data; report coverage gap
  3. Extract per-genome pathway status: aggregate `gapmind_pathways` with `MAX(score)` grouped by genome_id, pathway (scope=all and scope=core separately)
  4. Compute species-level pathway summary (use Spark `.write.csv()`, NOT `.toPandas()`)
  5. Extract pangenome stats
  6. Build/load FB-pangenome link table (regenerate from DIAMOND if not cached, or load from conservation_vs_fitness)
  7. Extract per-gene fitness summary with breadth metrics (n_conditions, n_sick, n_strong_phenotype)
  8. **NEW: Extract condition-type metadata** from `exps` table and compute per-gene fitness by condition type
  9. Extract putative essential genes (FB genes with no fitness data)
  10. Extract eggNOG annotations using **KEGG_ko** (not just KEGG_Pathway maps) for more precise pathway assignment
- **Expected output**: `data/gapmind_genome_pathway_status.csv`, `data/gapmind_core_pathway_status.csv`, `data/species_pathway_summary/` (partitioned), `data/pangenome_stats.csv`, `data/fb_fitness_summary.csv`, `data/fb_fitness_by_condition_type.csv`, `data/fb_kegg_annotations.csv`, `data/fb_essential_genes.csv`, `data/gapmind_fb_coverage.csv`

### Notebook 2: Tier 1 — Pathway Classification (local after data extraction)

- **Goal**: Classify pathways in FB organisms using fitness data
- **Steps**:
  1. Map eggNOG KEGG orthologs (KOs) to GapMind pathways via curated KO→pathway mapping
  2. Join: FB gene → gene_cluster → KO annotation → GapMind pathway
  3. For each pathway × organism, aggregate fitness effects using **three dimensions**:
     - **Magnitude**: median fitness, min fitness, fraction essential
     - **Breadth**: fraction of conditions with |fitness| > 1 (per fitness_effects_conservation)
     - **Condition type**: separate fitness for carbon/nitrogen/stress conditions (per field_vs_lab_fitness)
  4. Compute composite importance score incorporating all three dimensions
  5. Cross-reference with GapMind pathway completeness
  6. Classify into 4 categories using data-driven thresholds
  7. **Validation**: test enrichment of Active Dependencies in core gene clusters using odds ratios (per metal_fitness_atlas methodology)
  8. **Condition-type analysis**: identify pathways that appear "latent" under rich media but important under stress — these may be false negatives for dependency (per core_gene_tradeoffs)
- **Expected output**: `data/tier1_pathway_classification.csv`, `data/tier1_condition_type_analysis.csv`, figures showing category distributions, conservation validation, condition-type patterns

### Notebook 3: Tier 2 — Pan-Bacterial Pathway Conservation (local)

- **Goal**: Pathway conservation patterns across 27K species, with phylogenetic controls
- **Steps**:
  1. Compute species-level pathway completion: fraction of genomes with complete pathway (from NB01 cache)
  2. Compare `sequence_scope = 'core'` vs `'all'` — pathways depending on accessory genes indicate BQH dynamics
  3. Join with pangenome stats (openness)
  4. Test H1b: species with more variable/latent pathways have more open pangenomes
  5. **Phylogenetic controls**: stratify correlations by GTDB phylum/class; compute partial correlations controlling for taxonomy; note ecotype_analysis finding that phylogeny dominates
  6. Contextualize: compare results against pangenome_openness null result and pangenome_pathway_ecology/geography designs
- **Expected output**: `data/species_pathway_metrics.csv`, `data/core_vs_all_pathway_completeness.csv`, correlation figures with and without phylogenetic controls

### Notebook 4: Metabolic Ecotypes (local)

- **Goal**: Define metabolic ecotypes from within-species pathway variation, with phylogenetic controls
- **Steps**:
  1. For species with sufficient genome diversity (>=50 genomes), build binary pathway profiles
  2. Cluster genomes by pathway profiles (hierarchical clustering, Jaccard distance)
  3. **Phylogenetic validation**: compare pathway-based ecotypes against ANI-based phylogenetic clusters to determine if ecotypes reflect phylogeny or independent metabolic variation (per ecotype_analysis finding that phylogeny dominates gene content)
  4. Count distinct metabolic ecotypes per species
  5. Correlate ecotype count with pangenome openness and niche breadth (AlphaEarth, 28% coverage)
  6. Control correlation for genome count (sampling bias) and phylogenetic depth
- **Expected output**: `data/metabolic_ecotypes.csv`, `data/ecotype_summary.csv`, clustering heatmaps, ecotype-openness correlation with controls

### Notebook 5: Synthesis & Visualization (local)

- **Goal**: Key figures and summary statistics for the report
- **Steps**:
  1. Summary figure: 4-category classification across organisms and pathways
  2. Conservation validation: core enrichment by category with OR statistics (metal_fitness_atlas style)
  3. **Condition-type pattern**: which pathways shift category under stress vs rich media
  4. Pangenome openness correlation (with and without phylogenetic controls)
  5. Core vs all pathway completeness (BQH evidence)
  6. Metabolic ecotype examples (2-3 well-characterized species)
  7. **Cross-project comparison**: how do metabolic pathway conservation patterns compare to metal tolerance (metal_fitness_atlas) and overall fitness-conservation gradient (conservation_fitness_synthesis)?
- **Expected output**: Publication-quality figures in `figures/`, summary statistics text file

## Expected Outcomes

- **If H1a supported**: Latent capabilities are enriched in accessory genes — fitness data adds predictive value beyond GapMind alone for identifying evolutionary trends.
- **If H1b supported**: Species with many latent capabilities have open pangenomes — ongoing streamlining leaves genomic "fossils" of past metabolic capability. However, pangenome_openness null result suggests this may not hold.
- **If H0 not rejected**: Pathway completeness is a reliable proxy for dependency — simpler models suffice.
- **Potential confounders**:
  - Lab fitness may not reflect natural selection (core_gene_tradeoffs: 28,017 costly-but-conserved genes)
  - GapMind coverage limited to amino acid and carbon pathways (80 total)
  - GapMind FB organism coverage may be limited (essential_metabolome: only 7/45)
  - Link table coverage varies by organism (34 with >=90% DIAMOND)
  - Phylogeny dominates gene content similarity (ecotype_analysis: 60.5% of species)
  - AlphaEarth embeddings cover only 28% of genomes

## Revision History

- **v1** (2026-02-17): Initial plan based on design review and data exploration
- **v2** (2026-02-19): Major revision incorporating findings from 25 related projects. Added Related Projects section documenting data dependencies and methodological templates. Key improvements: (1) fitness breadth metrics per fitness_effects_conservation, (2) condition-type stratification per field_vs_lab_fitness and core_gene_tradeoffs, (3) phylogenetic controls per ecotype_analysis, (4) improved KEGG KO-based pathway mapping instead of KEGG map IDs, (5) performance fix for large Spark extracts, (6) explicit GapMind-FB coverage verification per essential_metabolome finding.
- **v3** (2026-02-19): Analysis complete. Key methodological change: NB02 uses FB-native KEGG annotations (besthitkegg → keggmember → EC → KEGG map) instead of the pangenome link table + eggnog_mapper_annotations. This avoids the DIAMOND alignment pipeline dependency while providing direct gene-to-pathway mapping for all 48 FB organisms. Results: 35.4% Active Dependencies, condition-type analysis validates the core_gene_tradeoffs finding, pan-bacterial correlation (rho=0.530) is strong and phylogenetically robust.

## Authors

Dileep Kishore, Paramvir Dehal

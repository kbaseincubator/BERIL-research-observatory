# Research Plan: Genomic Signatures of Clay-Confined Deep-Subsurface Life

## Research Question

Do cultured bacterial isolates from clay-confined deep-subsurface environments share a distinguishable, recurrent genomic signature relative to surface soil/sediment microbes, and is "depth/confinement" (anoxia, oligotrophy, mineral confinement) the dominant axis rather than soil texture per se?

## Hypotheses

### H1 — Anaerobic-niche enrichment
- **H0**: The distribution of dissimilatory anaerobic respiration genes (sulfate reduction `dsrAB`/`aprAB`, dissimilatory nitrate reduction `napAB`/`narGHI`, dissimilatory iron reduction *Geobacter*/*Shewanella*-type cytochromes), [NiFe]/[FeFe] hydrogenases, and CO₂-fixation pathways (Wood–Ljungdahl, rTCA) in the clay-confined cohort matches the soil/sediment baseline.
- **H1**: The clay-confined cohort is significantly enriched for these anaerobic-niche markers (Fisher's exact, BH-FDR q<0.05), reflecting selection for anoxic, low-carbon, mineral-bound metabolism.

### H2 — Depth/confinement, not texture, drives the genomic profile
- **H0**: A PCA on COG-category proportions and GapMind pathway-completeness vectors separates samples primarily by "clay vs non-clay" texture; depth has no additional explanatory power.
- **H1**: PC1 separates "deep clay-confined" (Opalinus, bentonite, ENIGMA saturated-zone clays) from "shallow agricultural clay" (Coalvale silty clay, Cerrado clay soils), with surface soil baseline overlapping the shallow clay cluster — i.e., depth/confinement is the dominant axis. PERMANOVA with `depth_class` and `texture_class` as factors will yield a larger pseudo-F for `depth_class`.

### H3 — A clay-confined core
- **H0**: After controlling for phylogeny (per-phylum stratification), no orthogroup is preferentially present in the clay-confined cohort relative to a phylogenetically matched soil baseline.
- **H1**: ≥10 cross-organism orthogroups (BBH-derived) are present in ≥70% of the clay-confined cohort but <20% of a phylum-matched soil-baseline subsample. Functional enrichment of these hits will be reported.

## Literature Context

To be expanded via `/literature-review` (next step). Anchors to cover:
- Subsurface microbiology of Opalinus Clay nuclear repository host rock (Bagnoud, Leupin, Stroes-Gascoyne reviews)
- Bentonite microbial ecology (Pedersen, Stone *et al.*)
- Oak Ridge ENIGMA subsurface plume biogeochemistry (Smith, Carlson, Hazen)
- Black Queen / streamlining theory in oligotrophic environments (Morris, Lenski)
- Cross-environment pangenome studies for comparative power benchmarks (Mende *et al.*, Lapierre & Gogarten)

The literature review will be run before NB02 and added as `references.md`.

## Cohort Definition

### Anchor cohort: clay-confined deep-subsurface (target n ≈ 30–60)
Sources, in priority order:

| Source | Subset | Expected n |
|---|---|---|
| `kbase_ke_pangenome.ncbi_env` | `isolation_source` LIKE '%Opalinus%' OR '%bentonite%' OR '%deep clay%' | ~12 |
| `kbase_ke_pangenome.ncbi_env` | `env_feature` / `env_local_scale` matching deep clay/sediment formation | ~10–15 |
| `kescience_bacdive.isolation` → pangenome (via 27K linkable BacDive→GTDB accessions) | clay-isolated BacDive strains classified Environmental→Terrestrial→Soil with depth or geological context | ~10–25 |
| `enigma_coral` SSO sediment-cultured strains | only if `sdt_strain` rows resolve to pangenome genome_ids | ?  |

### Shallow-clay contrast cohort (n ≈ 15–25)
Surface agricultural / pedogenic clay isolates: Coalvale silty clay, Cerrado clay soils, "clay soil with X" agricultural BacDive entries.

### Soil/sediment baseline (n ≈ 1,000–2,000 species, stratified)
Random per-phylum stratified sample from the 5,151 species linked to soil/sediment biosamples in `ncbi_env`. Used as the reference distribution for H1/H3 enrichment tests.

## Query Strategy

### Tables Required
| Table | Purpose | Rows | Filter |
|---|---|---|---|
| `kbase_ke_pangenome.ncbi_env` | Cohort assembly via isolation_source/env_* keywords | 4.1M | `attribute_name IN (...)` + LIKE on content |
| `kbase_ke_pangenome.genome` | biosample_id ↔ genome_id ↔ species clade | 293K | join from cohort accession list |
| `kbase_ke_pangenome.gene_cluster` | Pangenome cluster IDs + core/aux flags per species | 132M | filter by `gtdb_species_clade_id IN (cohort)` |
| `kbase_ke_pangenome.gene_genecluster_junction` | Genome → cluster membership | 1B | filter by `genome_id IN (cohort)` |
| `kbase_ke_pangenome.eggnog_mapper_annotations` | COG/KEGG/EC/PFAM by cluster representative | 94M | filter by `query_name IN (cohort_clusters)` |
| `kbase_ke_pangenome.gapmind_pathways` | Pathway completeness per genome | 305M | filter by `genome_id IN (cohort)` |
| `kbase_ke_pangenome.genomad_mobile_elements` | Plasmid/phage/AMR flags | varies | filter by `gene_id IN (cohort_genes)` |
| `kbase_ke_pangenome.gtdb_metadata` | GC%, genome size, completeness, lineage | 293K | join on accession |
| `kescience_bacdive.isolation` + `taxonomy` | Map clay-tagged BacDive strains to pangenome | 58K + 97K | LIKE filter on sample_type, then GCA→GTDB |

### Anti-pitfall checklist (from `docs/pitfalls.md` & `docs/performance.md`)
- `--` in species IDs: use exact equality, not LIKE patterns
- Never full-scan `gene` (1B) or `gene_genecluster_junction` (1B) — always filter by `genome_id` or `gene_cluster_id`
- Cast string columns to numeric where used (CheckM completeness, GC%)
- Avoid `.toPandas()` on intermediate Spark results
- Disable `autoBroadcastJoinThreshold` if hitting `maxResultSize` on multi-way joins involving `kbase_uniprot.uniprot_identifier`
- Gene clusters are species-specific; cross-species comparisons require BBH or COG/KEGG aggregation
- AlphaEarth embeddings cover only 28% of genomes — do not require for cohort inclusion

### Performance Plan
- **Tier**: Direct Spark on JupyterHub (current environment)
- **Estimated complexity**: Moderate. Cohort genome list is small (≤200), so per-genome filters perform well on `gene` and `gene_genecluster_junction`. The 305M-row `gapmind_pathways` query restricted to cohort `genome_id IN (...)` is fast.
- **Largest job**: BBH ortholog assembly across cohort (NB05). For ~50 cohort genomes + 200 baseline genomes, all-vs-all DIAMOND on cluster-rep proteomes is ~3–6 hours; we can batch by phylum.

## Analysis Plan

### NB01 — Cohort assembly (Spark)
- **Goal**: Identify clay-confined / shallow-clay / soil-baseline cohorts and link to pangenome `genome_id`.
- **Inputs**: `ncbi_env`, `bacdive.isolation`, `bacdive.taxonomy`, `genome`, `gtdb_metadata`.
- **Outputs**: `data/cohort_assignments.tsv` (genome_id, species_clade_id, cohort_class, source, depth_class, texture_class, raw_isolation_source).

### NB02 — Genome feature extraction (Spark)
- **Goal**: For each cohort genome, extract per-genome COG-category counts, KEGG/EC presence, GapMind pathway completeness, mobile-element gene fractions, and per-genome QC metrics (size, GC%, CheckM completeness).
- **Outputs**: `data/genome_features.parquet`.

### NB03 — Phylogeny-controlled baseline (Spark + local)
- **Goal**: Build a phylum-stratified random soil-baseline (target 4× cohort size per phylum) so H1/H3 tests have a comparable reference distribution.
- **Outputs**: `data/baseline_features.parquet`.

### NB04 — H1: Anaerobic-niche enrichment (local)
- **Goal**: Test enrichment of curated anaerobic respiration / hydrogenase / CO₂-fixation gene markers in clay-confined vs baseline.
- **Method**: Per-marker Fisher's exact (presence/absence per genome) with BH-FDR; effect-size = log-odds. Stratified version with phylum as covariate (Cochran–Mantel–Haenszel) as sensitivity check.
- **Outputs**: `data/h1_marker_enrichment.tsv`, `figures/h1_marker_forest.png`.

### NB05 — H2: Depth vs texture decomposition (local)
- **Goal**: Decompose genomic feature space and quantify depth_class vs texture_class explanatory power.
- **Method**: PCA on standardized COG-proportion + GapMind-completeness vectors. PERMANOVA(`features ~ depth_class + texture_class + phylum`) on Bray–Curtis distance. NMDS for visualization.
- **Outputs**: `data/h2_permanova.tsv`, `figures/h2_pca_depth_vs_texture.png`, `figures/h2_nmds.png`.

### NB06 — H3: Clay-confined core ortholog set (local + Spark for BBH)
- **Goal**: Identify orthogroups recurrently present in clay-confined cohort but rare in matched soil baseline.
- **Method**: All-vs-all DIAMOND on cluster-representative proteomes → BBH graph → connected-component orthogroups. Per-OG presence rate in each cohort. Filter: present ≥70% clay-confined, ≤20% baseline. Annotate with eggNOG / COG.
- **Outputs**: `data/h3_clay_core_orthogroups.tsv`, `figures/h3_presence_heatmap.png`.

### NB07 — Synthesis (local)
- **Goal**: Integrate H1/H2/H3 results, contextualize with literature (`references.md`), produce summary figure.
- **Outputs**: `figures/summary_figure.png`, draft text for REPORT.md.

## Expected Outcomes

- **If H1 supported**: Clay-confined isolates encode an anaerobic-respiration-shifted genomic profile beyond what soil baseline predicts, consistent with deep-subsurface electron-acceptor selection.
- **If H1 not supported**: Either (a) cohort is dominated by aerobic surface contaminants in cultured collections (cultivation bias), (b) clay-confinement does not select strongly at the gene-presence level (rate-of-use selection only), or (c) effect sizes are within noise for this sample size — in which case H3 may still surface a usable signal.
- **If H2 supported**: Soil texture is *not* the primary axis — depth/confinement is. This argues against texture-based microbiome classification and for environmental-context (redox, depth) classification.
- **If H3 supported**: Even ~10 recurrent orthogroups present across phylogenetically diverse clay-confined isolates would be a candidate "deep-clay core" — testable experimentally and a useful biomarker set for future MAG screening.

### Potential confounders
- **Cultivation bias**: BacDive / NCBI deep-subsurface isolates skew toward cultivable (likely facultative) lineages; obligate anaerobes underrepresented.
- **Phylogenetic confounding**: Opalinus and bentonite cohorts are *Desulfosporosinus*-heavy; H1/H3 signals must be controlled for phylum.
- **Sample size**: n=30–60 for the anchor cohort is small; Fisher tests have power for moderate-large effects only. We will report effect sizes alongside p-values and treat marginal findings as descriptive.
- **Annotation gaps**: GapMind covers amino acid + small carbon pathways but not core dissimilatory respiration — H1 markers will be drawn from KEGG modules and curated PFAM lists, not GapMind.

## Revision History

- **v1** (2026-04-30): Initial plan.

## Authors

David Lyon (ORCID: [0000-0002-1927-3565](https://orcid.org/0000-0002-1927-3565)) — KBase

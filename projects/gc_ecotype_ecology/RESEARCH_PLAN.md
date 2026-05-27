# Research Plan: GC Content as an Ecological Signal Across Bacterial Ecotypes

## Research Question
Does within-species GC content vary systematically with environmental niche after controlling for phylogenetic distance? That is, beyond the well-known across-species GC variation, do genomes of the same species from different habitats show subtle but reproducible compositional shifts that track ecology?

## Hypothesis
- **H0**: Within a bacterial species, GC content variation across genomes is explained by phylogenetic structure (intra-species clade / ANI cluster) and shows no residual association with environmental niche.
- **H1**: After controlling for intra-species phylogenetic distance, GC content carries a residual ecological signal — genomes from distinct niches (e.g., host-associated vs free-living, soil vs marine, low-carbon vs high-carbon) show systematic GC offsets.

## Literature Context

Across-species GC patterns are well-studied: GC correlates with genome size, lifestyle (free-living > intracellular obligates), and is shaped by biased gene conversion (Lassalle et al. 2015, PLoS Genetics) and ancient environmental adaptation (Teng et al. 2023, Microbiology Spectrum). At the community level, soil studies show:

- **Chuckran et al. (2023)** — community-weighted GC tracks soil carbon availability in NEON sites.
- **Goodall et al. (2025)** ([DOI](https://doi.org/10.1093/femsmc/xtaf008)) — soil pH drives community GC content traits in agricultural systems.
- **Gralka et al. (2023)** ([DOI](https://doi.org/10.1038/s41564-023-01458-z)) — genomic GC content covaries with sugar-vs-acid carbon catabolism preference, connecting GC to metabolic niche.

**Gap**: The above work is mostly cross-species (metabarcoding or comparative). Whether **within-species** genome-to-genome GC variation tracks environmental niche is rarely tested, because it requires (a) many genomes per species, (b) good ecological metadata per genome, and (c) a way to control for phylogeny. BERDL has all three.

**Related internal work**: `ecotype_analysis` already showed phylogeny dominates *gene content* similarity within species (60.5% of 172 species). This project asks the parallel question for *nucleotide composition* — a much finer-grained trait that could behave differently.

## Query Strategy

### Tables Required

| Table | Purpose | Estimated Rows | Filter Strategy |
|---|---|---|---|
| `kbase_ke_pangenome.gtdb_metadata` | Per-genome GC %, genome size, completeness | 293K | Safe to scan; CAST gc_percentage to DOUBLE |
| `kbase_ke_pangenome.genome` | Maps genome_id → species clade → biosample | 293K | Safe to scan; bridges to ncbi_env |
| `kbase_ke_pangenome.genome_ani` | Pairwise ANI within species (phylogenetic proxy) | 421M | **Always filter to a single species before joining** |
| `kbase_ke_pangenome.alphaearth_embeddings_all_years` | Continuous environmental signature (64 dims) | 83K | LEFT JOIN; only ~28% coverage |
| `kbase_ke_pangenome.ncbi_env` | Isolation source / host / env_broad_scale (EAV) | 4.1M | Filter by harmonized_name; pivot per biosample |
| `kbase_ke_pangenome.sample` | Biosample → genome bridge | 293K | Safe to scan |

### Pitfall checks (from docs/pitfalls.md and live exploration)
- `gc_percentage` is **string-typed** — always `CAST(gc_percentage AS DOUBLE)`.
- `ncbi_env` is EAV — pivot or filter by `harmonized_name`, never assume one row per sample.
- Species clade IDs contain `--` (parses as SQL comment in `IN (...)`); use exact equality or `LIKE 's__...%'`.
- `genome_ani` is within-species only.
- `alphaearth_embeddings_all_years` covers only ~28% of genomes — use LEFT JOIN and report coverage.

### Performance Plan
- **Tier**: JupyterHub Spark SQL (on-cluster, no proxy).
- **Strategy**: Pre-aggregate to one row per genome with GC + environmental features, then iterate species-by-species for ANI-controlled analyses.
- **Estimated complexity**: Moderate. The expensive table is `genome_ani` (421M rows); we'll filter it to one species at a time. Everything else is small-table joins.

### Key Queries

1. **Build the master genome-level GC + environment table** (one row per genome):
```sql
SELECT
  g.genome_id,
  g.gtdb_species_clade_id,
  CAST(m.gc_percentage AS DOUBLE) AS gc_pct,
  CAST(m.genome_size AS BIGINT)   AS genome_size,
  g.ncbi_biosample_id
FROM kbase_ke_pangenome.genome g
LEFT JOIN kbase_ke_pangenome.gtdb_metadata m
  ON m.accession = g.genome_id
WHERE m.gc_percentage IS NOT NULL
```

2. **Pivot ncbi_env to harmonized columns per biosample** (`isolation_source`, `host`, `env_broad_scale`, `env_medium`, `lat_lon`).

3. **Per-species GC vs environment ANOVA / regression**:
   - For each species with ≥ N genomes (start with N=50) and ≥ 2 environmental categories with sufficient sample size, test whether GC varies by category.
   - Control for phylogeny using ANI-based clusters (cluster genomes at e.g. 99.5% ANI; use cluster as random effect or PERMANOVA stratum).

4. **AlphaEarth-based continuous test**:
   - For genomes with embeddings, partial-correlate GC vs AlphaEarth principal components after regressing out an ANI-cluster mean.

## Analysis Plan

### Notebook 01: Master Table Construction
- **Goal**: Build `genome_gc_env.parquet` — one row per genome with `genome_id`, `species`, `gc_pct`, `genome_size`, environment fields, and AlphaEarth presence flag.
- **Expected output**: Parquet table; summary plots of GC distribution overall and by species; coverage report for each environmental field.

### Notebook 02: Across-Species GC Patterns (Sanity Check)
- **Goal**: Reproduce the established literature finding that GC tracks environment at the cross-species level. Use community-level isolation source categories.
- **Expected output**: Boxplots of GC by isolation source / env_broad_scale across all species; basic OLS coefficients. Functions as a positive control for the dataset.

### Notebook 03: Within-Species GC vs Environment (Core Analysis)
- **Goal**: For each species with adequate sample size and environmental diversity, test whether within-species GC varies by environment after controlling for ANI clustering.
- **Steps**:
  1. Select candidate species (≥50 genomes, ≥2 env categories with ≥10 genomes each).
  2. Within each species, cluster genomes at 99.5% ANI; record cluster membership.
  3. Fit mixed model: `gc_pct ~ env_category + (1 | ANI_cluster)`; record coefficient, p-value, residual variance explained.
  4. Multiple-testing correction (Benjamini-Hochberg).
- **Expected output**: Per-species effect-size table; volcano plot; list of species where environment significantly predicts GC after phylogenetic control.

### Notebook 04: AlphaEarth Continuous Signal
- **Goal**: Test the same question using continuous environmental embeddings rather than categorical labels.
- **Steps**:
  1. For genomes with AlphaEarth, compute residual GC after subtracting per-ANI-cluster mean.
  2. Partial correlation of residual GC against each of the 64 AlphaEarth dimensions, and against PC1–PC5 of the embedding.
  3. Identify environmental axes most predictive of within-species GC.
- **Expected output**: Correlation table; scatter plots of residual GC vs top environmental PCs.

### Notebook 05: Visualization & Summary Figures
- **Goal**: Pull together the figures that go into REPORT.md.
- **Expected output**: 4–6 final PNGs saved to `figures/`.

## Expected Outcomes

- **If H1 supported**: We'll find a set of species where within-species GC tracks environment beyond what phylogeny explains. Most likely candidates are species spanning host-associated and free-living niches (e.g., *E. coli*, *Klebsiella*, *Salmonella*, *Pseudomonas aeruginosa*). Effect sizes are likely small (<1% GC shift) but should be detectable with N≥1000 genomes per species.
- **If H0 not rejected**: Within-species GC is essentially determined by ANI cluster. Environmental signal exists only across species. This would be a meaningful negative result complementing `ecotype_analysis` — both gene content and nucleotide composition would then appear to be phylogeny-bound within species.
- **Potential confounders**:
  - **Sampling bias**: Clinical isolate species (Staph, Klebsiella) are over-sampled from hospital settings — limited environmental range within species.
  - **Metadata sparsity**: Many genomes have no `isolation_source` or only generic labels like "human" or "soil".
  - **ANI cluster ≠ ecology**: ANI clusters could themselves track ecology, partially confounding the phylogenetic control. Worth examining and reporting.
  - **Genome size / completeness**: Incomplete genomes can have biased GC estimates. Will filter to CheckM completeness ≥ 90%, contamination ≤ 5%.

## Revision History
- **v1** (2026-05-27): Initial plan.

## Authors
- Justin Reese (ORCID 0000-0002-2170-2250), Lawrence Berkeley National Laboratory

# Research Plan: Prophage-AMR Co-mobilization Atlas

## Research Question

At pangenome scale (293K genomes, 27K species), are antibiotic resistance genes preferentially located within or adjacent to prophage regions, and does this co-localization predict AMR gene mobility and accessory-genome status?

## Hypotheses

- **H1 (Prophage proximity predicts mobility)**: AMR genes within prophage neighborhoods (within 10 genes on the same contig) are more likely to be accessory than AMR genes in prophage-free regions.
- **H0**: Prophage proximity has no effect on AMR gene conservation status (core vs accessory).
- **H2 (Prophage burden predicts AMR breadth)**: Species with more prophage markers per genome have broader AMR repertoires, after controlling for genome size and phylogeny.
- **H3 (Fitness cost differs by context)**: Among Fitness Browser organisms, prophage-proximal AMR genes impose different fitness costs than prophage-distant AMR genes.

## Literature Context

Rendueles et al. 2018 (DOI: 10.1371/journal.pgen.1007862) showed capsule-encoding bacteria have more prophages AND more ARGs across >100 pangenomes, but did not test direct gene-level co-localization. Chen et al. 2018 (DOI: 10.1016/j.envpol.2018.11.024) found ARG-MGE co-occurrence in river metagenomes at the contig level. No pangenome-scale study of prophage-ARG genomic co-occurrence at gene-neighborhood resolution exists. The amr_strain_variation project found 1,517 resistance islands and 51% of AMR genes are rare within species — but did not test whether these mobile AMR genes are prophage-associated.

## Data Sources

### Primary BERDL Tables

| Table | Purpose | Estimated Rows | Filter Strategy |
|---|---|---|---|
| `kbase_ke_pangenome.bakta_amr` | AMR gene identification | 83K | Safe to full-scan |
| `kbase_ke_pangenome.bakta_annotations` | Prophage marker identification via product keywords | 132M | Filter by product keyword or gene_cluster_id |
| `kbase_ke_pangenome.gene_cluster` | Core/accessory status | 132M | Filter by species |
| `kbase_ke_pangenome.gene` | Gene coordinates (contig, start, stop, strand) | 1B | Filter by genome_id |
| `kbase_ke_pangenome.gene_genecluster_junction` | Gene-to-cluster mapping | 1B | Filter by gene_cluster_id |
| `kbase_ke_pangenome.genome` | Genome-to-species mapping | 293K | Safe to full-scan |
| `kbase_ke_pangenome.pangenome` | Species summary (genome counts, cluster counts) | 27K | Safe to full-scan |
| `kbase_ke_pangenome.eggnog_annotation` | COG/KEGG functional annotation | 93M | Filter by query_name |
| `kescience_fitnessbrowser.genefitness` | Gene fitness scores | 27M | Filter by orgId |

### Completed Project Data (MinIO reuse)

| Project | Data Product | What it provides |
|---|---|---|
| `amr_pangenome_atlas` | AMR gene cluster inventory | Pre-computed AMR landscape across 27K species |
| `amr_strain_variation` | Resistance islands, AMR ecotypes | Within-species AMR variation patterns |
| `prophage_ecology` | Prophage distribution atlas | Prophage markers across phylogeny and environments |

### Important: `genomad_mobile_elements` is NOT in BERDL

The overview.md mentions a `genomad_mobile_elements` table but it was never ingested (documented in pitfalls.md and confirmed by gene_function_ecological_agora P4-D2). Prophage detection must use:

1. **bakta_annotations.product** — keyword matching for phage-associated terms (terminase, integrase, phage portal, holin, phage tail, etc.)
2. **bakta_pfam_domains** — Pfam domain-based detection (Terminase_1, Phage_portal, Phage_integrase, etc.)

This approach was validated in gene_function_ecological_agora NB26 (26_p4d2_mge_context.py), which identified ~9,000 MGE-flagged clusters using 23+ keywords.

## Query Strategy

### Performance Plan

- **Tier**: Direct Spark (JupyterHub) — required for billion-row joins
- **Estimated complexity**: Moderate-high (gene-level coordinate analysis across many species)
- **Key pitfalls**: Gene clusters are species-specific; gene table requires genome_id filter; avoid .toPandas() on large intermediates

### Key Queries

**Q1: Prophage marker census**
```sql
-- Identify prophage-associated gene clusters via product keywords
SELECT gene_cluster_id, product, gene
FROM kbase_ke_pangenome.bakta_annotations
WHERE LOWER(product) RLIKE 'phage|prophage|terminase|integrase|holin|endolysin|phage_portal|phage_tail|phage_capsid|excisionase'
   OR LOWER(gene) RLIKE '^ter[ls]$|^int$|^hol$'
```

**Q2: AMR gene inventory**
```sql
-- All AMR gene clusters
SELECT gene_cluster_id, amr_gene, amr_product, method, identity
FROM kbase_ke_pangenome.bakta_amr
```

**Q3: Gene coordinates for neighborhood analysis** (per-species)
```sql
-- Get gene coordinates for a target species
SELECT g.gene_id, g.genome_id, g.contig_id, g.start, g.stop, g.strand,
       j.gene_cluster_id
FROM kbase_ke_pangenome.gene g
JOIN kbase_ke_pangenome.gene_genecluster_junction j ON g.gene_id = j.gene_id
JOIN kbase_ke_pangenome.genome gm ON g.genome_id = gm.genome_id
WHERE gm.gtdb_species_clade_id = '{species_id}'
```

## Analysis Plan

### Notebook 01: AMR and Prophage Marker Census

- **Goal**: Build the complete inventory of AMR genes and prophage markers across BERDL
- **Method**:
  - Extract all 83K bakta_amr entries
  - Extract prophage markers from bakta_annotations (keyword matching on product field)
  - Complement with Pfam-domain-based prophage detection (bakta_pfam_domains)
  - Cross-reference with amr_pangenome_atlas and prophage_ecology data products
  - Map both to gene_cluster -> species -> core/accessory status
- **Output**: `data/amr_clusters.csv`, `data/prophage_marker_clusters.csv`, `data/census_summary.json`
- **Figures**: Distribution of AMR and prophage markers across phyla; overlap Venn/upset plot

### Notebook 02: Gene Neighborhood Co-localization

- **Goal**: For each AMR gene, measure proximity to nearest prophage marker on the same contig
- **Method**:
  - For species with both AMR and prophage markers, extract gene coordinates
  - For each AMR gene instance, find nearest prophage marker on the same contig
  - Define neighborhoods: +/-5, +/-10, +/-20 genes
  - Classify each AMR gene as prophage-proximal vs prophage-distant
  - Sample strategy: start with top-50 species by AMR gene count, then scale
- **Output**: `data/amr_prophage_distances.csv`, `data/coloc_summary.json`
- **Figures**: Distribution of AMR-to-prophage distances; proportion proximal by neighborhood threshold

### Notebook 03: Conservation Test (H1)

- **Goal**: Test whether prophage-proximal AMR genes are more likely accessory
- **Method**:
  - Join co-localization results with gene_cluster core/accessory status
  - Fisher's exact test: prophage-proximal x accessory (per-species, then meta-analysis)
  - Control for species identity and AMR gene type
  - Sensitivity analysis across neighborhood thresholds (+/-5, +/-10, +/-20)
- **Output**: `data/h1_conservation_test.csv`, `data/h1_meta_analysis.json`
- **Figures**: Forest plot of per-species odds ratios; overall effect size by threshold

### Notebook 04: Species-Level Breadth Test (H2)

- **Goal**: Test whether prophage-rich species have broader AMR repertoires
- **Method**:
  - Per-species: count prophage markers per genome, count unique AMR genes
  - Regression: AMR breadth ~ prophage density + genome size + phylum
  - Partial correlation controlling for genome size
  - Phylogenetic comparison (GTDB phylum as fixed effect)
- **Output**: `data/h2_species_regression.csv`, `data/h2_model_summary.json`
- **Figures**: Scatter plot (prophage density vs AMR breadth); partial regression plots

### Notebook 05: Fitness Cost Comparison (H3) and Synthesis

- **Goal**: Compare fitness costs of prophage-proximal vs distant AMR genes; synthesize findings
- **Method**:
  - For FB organisms with pangenome links, map AMR genes to fitness scores
  - Compare median fitness effect: prophage-proximal vs distant
  - Wilcoxon rank-sum test, Cohen's d effect size
  - Environmental stratification: clinical vs environmental species (ncbi_env)
  - Synthesis: combine H1-H3 results, assess overall conclusion
- **Output**: `data/h3_fitness_comparison.csv`, `data/synthesis_summary.json`
- **Figures**: Fitness cost comparison violin plot; summary panel figure

## Expected Outcomes

- **If H1 supported**: Prophage proximity is a marker of AMR gene mobility — these genes are in the accessory genome because they move via phage transduction. Quantifies the fraction of AMR mobilized by phages vs other mechanisms.
- **If H0 not rejected**: AMR mobility is driven by other mechanisms (plasmids, ICEs, transposons) rather than prophages. Still informative — narrows the mechanism space.
- **If H2 supported**: Prophage burden is a species-level predictor of AMR risk. Species with many prophages are "resistance amplifiers."
- **If H3 shows differential cost**: Prophage-proximal AMR genes may be costlier (carrying phage baggage) or cheaper (under positive selection for spread) — both are mechanistically interesting.

## Potential Confounders

- **Genome size**: Larger genomes have more of everything (genes, prophages, AMR). Must control.
- **Phylogeny**: Some clades are inherently prophage-rich AND AMR-rich. Need phylogenetic correction.
- **Contig fragmentation**: Short contigs may split prophage regions from nearby AMR genes, creating false negatives for co-localization. Filter to contigs >20 genes.
- **Annotation sensitivity**: bakta_annotations keyword matching is imperfect for prophage detection. Validate with Pfam domain approach as orthogonal method.
- **Core/accessory definition**: motupan calls depend on sampling. Large species (many genomes) have different core/accessory thresholds than small species.

## Revision History

- **v1** (2026-04-30): Initial plan based on suggest-research recommendation

## Authors

- Justin Reese, Lawrence Berkeley National Laboratory (ORCID: 0000-0002-2170-2250)
- Claude (AI co-scientist, Anthropic)

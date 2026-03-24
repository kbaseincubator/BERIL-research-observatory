# Research Plan: Environmental Resistome at Pangenome Scale

## Research Question

Do antimicrobial resistance gene profiles differ between ecological niches across 27,000 bacterial species? Using 83K AMR gene clusters mapped to 293K genomes with environmental metadata, we test whether the resistome is structured by ecology — and whether intrinsic (core) and acquired (accessory) resistance show different environmental signatures.

## Hypotheses

- **H0**: AMR gene content does not differ between ecological niches after controlling for phylogeny
- **H1**: Species from antibiotic-rich environments (soil, host-associated) carry more diverse AMR gene repertoires than species from low-antibiotic environments (aquatic, pristine). Note: `amr_strain_variation` already showed host-associated > environmental at species level; we replicate at 27K-species scale and decompose by mechanism and core/accessory status.
- **H2**: Intrinsic (core) AMR genes are ecology-structured (reflecting long-term niche adaptation), while acquired (accessory) AMR genes are more uniformly distributed across niches (reflecting recent HGT)
- **H3**: Clinical/host-associated species are enriched for efflux and enzymatic inactivation mechanisms, while soil species are enriched for target modification and metal resistance. The `amr_fitness_cost` project found mechanism predicts conservation (metal 44% accessory vs efflux 13%); we test whether mechanism also predicts environment.
- **H4**: Within species that span multiple environments, AMR gene content differs between niches — strains from hospitals carry different accessory AMR genes than strains from soil

## Literature Context

### Ecology structures the resistome
- **Gibson, Forsberg & Dantas (2015, ISME J)** analyzed ~6,000 genomes and found resistance functions significantly differ between ecologies (soil vs human gut vs cultured isolates). Beta-lactam and tetracycline resistance most discriminated environments. This is the closest published precedent — we extend it by 50× in genome count. PMID: 25003965
- **Forsberg et al. (2014, Nature)** showed soil resistomes are structured by phylogeny and habitat type, with mobility elements rare compared to pathogens. Nitrogen fertilizer strongly influenced soil ARG content. PMID: 24847883

### The ancient environmental resistome
- **Surette & Wright (2017, Annu Rev Microbiol)** established that the environment is the largest resistance reservoir, with soil resistance diversity reflecting millions of years of natural antibiotic production. PMID: 28657887
- **Van Goethem et al. (2018, Microbiome)** found diverse ARGs in pristine Antarctic soils with no antibiotic exposure history — the ancestral resistome. PMID: 29471872

### Soil-clinical exchange
- **Forsberg et al. (2012, Science)** found soil ARGs with perfect nucleotide identity to clinical pathogen genes, providing evidence of recent lateral exchange. PMID: 22936781
- **Finley et al. (2013, Clin Infect Dis)** reviewed evidence that most clinical resistance genes originated in environmental bacteria. PMID: 23723195

### Core vs accessory framing
- **Jiang et al. (2024, Water Research)** found the core resistome is chromosomally encoded (intrinsic) while the rare resistome is plasmid-associated (acquired) — our pangenome framework naturally captures this distinction. PMID: 38039820

### Prior BERIL projects
- **`amr_strain_variation`**: Within-species AMR variation across 180K genomes — 51% of AMR gene occurrences are rare, 20% of species have AMR ecotypes, host-associated species carry more AMR. Species-level environment classification with 91% coverage. **Key overlap**: H1 partially answered; our novelty is mechanism decomposition (H3) and core/accessory (H2).
- **`amr_fitness_cost`**: Universal +0.086 fitness cost, mechanism-independent but mechanism predicts conservation (metal 44% accessory vs efflux 13%). **Key link**: we test whether mechanism-conservation also tracks environment.
- **`env_embedding_explorer`**: AlphaEarth embeddings cover 28% of genomes; 38% are human-associated; environmental samples show 3.4× stronger geographic signal. 4.6% of embeddings have NaN values — filter before use.
- **`resistance_hotspots`**: Proposed but never executed — our project supersedes its Phase 3

**Gap**: No study has mapped AMR profiles vs environment across 27K species with 293K genomes. Gibson (2015) used ~6K genomes; Martiny (2024) used metagenomes. Our pangenome dataset is 2 orders of magnitude larger and uses gene clusters with core/accessory classification — a significant advance. The primary novelty over `amr_strain_variation` is the mechanism × environment decomposition (H3), core vs accessory environmental signatures (H2), and continuous embedding analysis (NB04).

## Data Sources

### Primary Data Assets

| Source | Table/File | Scale | Purpose |
|--------|-----------|-------|---------|
| `bakta_amr` | `kbase_ke_pangenome.bakta_amr` | 83K AMR clusters | AMR gene identification per gene cluster |
| `gene_cluster` | `kbase_ke_pangenome.gene_cluster` | 132M clusters | Core/accessory classification, species assignment |
| `pangenome` | `kbase_ke_pangenome.pangenome` | 27.7K species | Species-level stats (genome count, core/aux counts) |
| `ncbi_env` | `kbase_ke_pangenome.ncbi_env` | 4.1M rows (EAV) | Per-genome isolation source, host, geography |
| `genome` | `kbase_ke_pangenome.genome` | 293K genomes | genome_id → species mapping, ncbi_biosample_id for ncbi_env join |
| `gtdb_taxonomy_r214v1` | `kbase_ke_pangenome.gtdb_taxonomy_r214v1` | 293K genomes | Phylogenetic classification (phylum → genus) |
| AlphaEarth | `kbase_ke_pangenome.alphaearth_embeddings_all_years` | 83K genomes | Environmental embeddings (continuous) |

### Cached Data from Prior Projects

| Source | File | Purpose |
|--------|------|---------|
| `amr_strain_variation` | `data/genome_metadata.csv` | Species-level environment classification (91% coverage) |
| `env_embedding_explorer` | `data/alphaearth_with_env.csv` | Per-genome environment categories + embeddings |

## Query Strategy

### Key Queries (all via Spark on-cluster)

1. **Species-level AMR profile** (~10 min):
```sql
SELECT a.gene_cluster_id, gc.gtdb_species_clade_id, gc.is_core, gc.is_auxiliary,
       a.amr_gene, a.amr_product
FROM kbase_ke_pangenome.bakta_amr a
JOIN kbase_ke_pangenome.gene_cluster gc ON a.gene_cluster_id = gc.gene_cluster_id
```
Note: `bakta_amr.method` is the detection method (BLAST/HMM), NOT the resistance mechanism. Mechanism classification must be inferred from `amr_gene` and `amr_product` text using the classifier developed in `amr_fitness_cost` NB01.

2. **Per-genome environment from ncbi_env** (EAV pivot):
```sql
-- Join through genome.ncbi_biosample_id -> ncbi_env.accession
SELECT g.genome_id, g.gtdb_species_clade_id,
       MAX(CASE WHEN n.harmonized_name = 'isolation_source' THEN n.content END) AS isolation_source,
       MAX(CASE WHEN n.harmonized_name = 'host' THEN n.content END) AS host,
       MAX(CASE WHEN n.harmonized_name = 'geo_loc_name' THEN n.content END) AS geo_loc_name
FROM kbase_ke_pangenome.genome g
JOIN kbase_ke_pangenome.ncbi_env n ON g.ncbi_biosample_id = n.accession
WHERE n.harmonized_name IN ('isolation_source', 'host', 'geo_loc_name')
GROUP BY g.genome_id, g.gtdb_species_clade_id
```

3. **Phylogenetic context** (use family/order for adequate phylogenetic control):
```sql
SELECT genome_id, phylum, class, `order`, family, genus
FROM kbase_ke_pangenome.gtdb_taxonomy_r214v1
```
Note: column is `order` (backtick-quoted, reserved word), not `order_name`.

### AMR Mechanism Classification

`bakta_amr` does not provide resistance mechanism directly. Classify from `amr_gene` and `amr_product` using the regex-based classifier from `amr_fitness_cost` NB01 (cell-7), extended with product-based fallback classification. Categories: efflux, enzymatic_inactivation, target_modification, metal_resistance, other/unknown.

### Performance Plan

- **Tier**: Spark on-cluster for initial data extraction; local pandas for analysis
- **bakta_amr** is small (83K rows) — safe to full-scan
- **gene_cluster** is large (132M rows) — JOIN with bakta_amr filters effectively
- **ncbi_env** is EAV (4.1M rows) — pivot via CASE/GROUP BY after joining through `genome.ncbi_biosample_id`
- **Re-register temp views** before JOINs if a long-running cell precedes them (Spark Connect temp view loss pitfall)
- **Known pitfalls**: ncbi_env EAV format (must join via genome.ncbi_biosample_id), species IDs with `--` (fine in quoted strings), string-typed numerics (`pd.to_numeric()` after `.toPandas()`), AlphaEarth 28% coverage with 4.6% NaN

## Analysis Plan

### Notebook 1: Data Extraction and Environment Classification (~30 min)

- **Goal**: Build species-level AMR profiles + environment labels + data validation
- **Method**:
  1. Extract bakta_amr × gene_cluster join to get AMR clusters with species and core/aux labels
  2. Classify AMR mechanism from `amr_gene`/`amr_product` using `amr_fitness_cost` classifier (regex + product keywords)
  3. Reuse `amr_strain_variation` species-level environment classification where available; extend to remaining species via ncbi_env majority-vote
  4. Get phylogenetic context (phylum through genus) from GTDB taxonomy; use **family** level as primary phylogenetic covariate (finer than phylum, coarser than genus)
  5. Compute species-level AMR summary: total AMR clusters, core vs accessory AMR, mechanism breakdown
  6. **Data validation checkpoint**: (a) species with ≥1 AMR cluster, (b) distribution matches 83K total, (c) environment labels join correctly, (d) sample sizes per environment, (e) count qualifying species for NB03 (≥5 genomes in each of ≥2 environments)
  7. Assess MAG vs isolate composition (via `gtdb_metadata.ncbi_genome_category` if available) and report; exclude MAGs if contamination risk is substantial
- **Expected output**: `data/species_amr_profiles.csv`, `data/species_environment.csv`, `data/genome_environment.csv`
- **Key figures**: AMR gene count distribution by environment, environment coverage bar chart, validation summary

### Notebook 2: Resistome vs Environment (Species-Level) (~15 min)

- **Goal**: Test H1, H2, H3 — do AMR profiles differ between environments?
- **Method**:
  1. Compare total AMR gene count across environments (Kruskal-Wallis). Report effect size (eta-squared) alongside p-value — with 27K species, even tiny effects will be significant.
  2. **H3**: Compare AMR mechanism composition (efflux, enzymatic, metal, target modification) across environments (chi-square per mechanism, BH-FDR across mechanisms)
  3. **H2**: Compare core vs accessory AMR fraction across environments. Test whether core AMR is more environment-structured than accessory AMR.
  4. Ordination: Jaccard distance of AMR profiles → PCoA, colored by environment
  5. **Phylogenetic control**: PERMANOVA with **family** as a covariate (not phylum — too coarse). Also report stratified analysis within major phyla (Pseudomonadota, Bacillota, Actinomycetota, Bacteroidota) as a robustness check.
  6. Identify environment-specific AMR genes: which AMR clusters are found predominantly in one environment? (Fisher's exact per gene, BH-FDR)
  7. **Sensitivity analysis**: Report environment classification at multiple majority thresholds (60%, 75%, 90%) to test robustness to classification uncertainty
- **Expected output**: `data/environment_amr_comparison.csv`, figures
- **Key figures**: AMR count by environment boxplot with effect size, mechanism × environment heatmap, PCoA ordination, phylogeny-controlled analysis, environment-specific gene volcano plot
- **Multiple testing**: BH-FDR (q < 0.05) within each test family (mechanism tests, gene-level tests, stratified analyses)

### Notebook 3: Within-Species AMR × Environment (~20 min)

- **Goal**: Test H4 — within species that span multiple environments, does AMR vary by niche?
- **Method**:
  1. Identify species with genomes in ≥2 environments, requiring **≥5 genomes per environment** (not just ≥20 total) using per-genome ncbi_env classification
  2. NB01 validation will report how many species qualify — if too few (<20), simplify to case studies only
  3. For each qualifying species, compare AMR gene presence/absence between environment groups (Fisher's exact per AMR gene, BH-FDR)
  4. Test whether within-species AMR Jaccard distance correlates with environment difference (Mantel test where applicable)
  5. Case studies: deeply-sampled species (*K. pneumoniae*, *E. coli*, *P. aeruginosa*, *S. aureus*) where clinical vs environmental strains can be compared
- **Expected output**: `data/within_species_amr_environment.csv`, figures
- **Note**: Limited by ncbi_env coverage (53% unknown at per-genome level).

### Notebook 4: AlphaEarth Continuous Environment Analysis (~10 min)

- **Goal**: Use continuous environmental embeddings instead of discrete categories
- **Method**:
  1. For the ~79K genomes with valid AlphaEarth embeddings (filter NaN rows), compute AMR diversity
  2. Correlate embedding dimensions with AMR diversity (Spearman)
  3. Cluster genomes by embedding similarity and compare AMR profiles between clusters
  4. Test whether embedding distance predicts AMR profile distance (Mantel test, 9,999 permutations). Consider db-RDA as a more powerful alternative if sample sizes permit.
  5. Stratify by human-associated vs environmental (per `env_embedding_explorer` findings)
- **Note**: Only 28% genome coverage; biased toward environmental samples. Results must be interpreted cautiously. Filter with `~df[EMB_COLS].isna().any(axis=1)` to remove 4.6% NaN embeddings.

## Expected Outcomes

- **If H1 supported**: Soil species have more diverse intrinsic AMR (from natural antibiotic production), clinical species have more acquired AMR (from antibiotic selection). This would be the largest-scale confirmation of Gibson et al. (2015).
- **If H2 supported**: Core AMR genes partition cleanly by environment (ancient niche adaptation) while accessory AMR genes are more cosmopolitan (recent HGT). This would extend Jiang et al. (2024) from metagenomes to pangenomes.
- **If H3 supported**: Mechanism enrichment by environment would identify which resistance strategies are favored in each niche — actionable for environmental surveillance.
- **If H4 supported**: Within-species AMR variation tracks environment, confirming that AMR ecotypes reflect ecological adaptation, not just random drift.

## Potential Confounders

1. **Phylogenetic confound (critical)**: Environment and phylogeny are correlated (e.g., Enterobacteriaceae overrepresented in clinical samples). All comparisons use PERMANOVA with **family** as covariate, plus stratified analysis within major phyla.
2. **Sampling bias**: NCBI is heavily biased toward clinical isolates and model organisms. Soil and aquatic species are underrepresented. Environment labels reflect sampling location, not the organism's true niche.
3. **ncbi_env metadata quality**: 53% of genomes lack usable isolation source. Species-level majority-vote (91% coverage) is the workaround, but collapses within-species variation. Sensitivity analysis at multiple majority thresholds (60%, 75%, 90%).
4. **MAGs vs isolates**: The pangenome includes metagenome-assembled genomes (MAGs) which may have chimeric AMR annotations and whose metadata refers to the metagenome sample, not a specific organism. Assess and potentially exclude in NB01.
5. **AlphaEarth coverage**: Only 28% of genomes, biased toward environmental samples with valid coordinates, 4.6% NaN in embedding dimensions. Filter NaN; stratify human-associated vs environmental.
6. **bakta_amr detection sensitivity**: AMRFinderPlus focuses on known resistance genes. Novel or cryptic resistance mechanisms in environmental bacteria may be missed, potentially underestimating environmental resistome diversity.
7. **Core/accessory threshold**: The 95% prevalence threshold for "core" depends on species sampling depth. Species with few genomes have imprecise labels.
8. **Effect size vs statistical significance**: With 27K species, even trivially small effects will be significant. Report and interpret effect sizes (eta-squared, Cohen's d, odds ratios) throughout.
9. **Archaea**: The pangenome includes archaea which carry some AMR genes (especially metal resistance). Include with domain as a covariate, or exclude with rationale if they confound bacterial comparisons.

## Revision History

- **v2** (2026-03-19): Incorporated Opus plan review — fixed ncbi_env join path (via genome.ncbi_biosample_id), corrected taxonomy column name (`order` not `order_name`), added AMR mechanism classification step (bakta_amr.method is detection method, not resistance mechanism), upgraded phylogenetic control from phylum to family, added NB03 minimum genomes-per-environment requirement (≥5), added environment classification sensitivity analysis, added MAG/isolate assessment, added data validation checkpoint, added effect size reporting requirement, added archaea consideration, specified BH-FDR throughout, specified Mantel permutation count, added NaN filtering for AlphaEarth
- **v1** (2026-03-19): Initial plan

## Authors

- **Paramvir S. Dehal** (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)) — Lawrence Berkeley National Laboratory

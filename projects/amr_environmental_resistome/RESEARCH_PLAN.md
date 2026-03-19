# Research Plan: Environmental Resistome at Pangenome Scale

## Research Question

Do antimicrobial resistance gene profiles differ between ecological niches across 27,000 bacterial species? Using 83K AMR gene clusters mapped to 293K genomes with environmental metadata, we test whether the resistome is structured by ecology — and whether intrinsic (core) and acquired (accessory) resistance show different environmental signatures.

## Hypotheses

- **H0**: AMR gene content does not differ between ecological niches after controlling for phylogeny
- **H1**: Species from antibiotic-rich environments (soil, host-associated) carry more diverse AMR gene repertoires than species from low-antibiotic environments (aquatic, pristine)
- **H2**: Intrinsic (core) AMR genes are ecology-structured (reflecting long-term niche adaptation), while acquired (accessory) AMR genes are more uniformly distributed across niches (reflecting recent HGT)
- **H3**: Clinical/host-associated species are enriched for efflux and enzymatic inactivation mechanisms, while soil species are enriched for target modification and metal resistance
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
- **`amr_strain_variation`**: Within-species AMR variation across 180K genomes — 51% of AMR gene occurrences are rare, 20% of species have AMR ecotypes, host-associated species carry more AMR. Species-level environment classification with 91% coverage.
- **`amr_fitness_cost`**: Universal +0.086 fitness cost, mechanism-independent but mechanism predicts conservation (metal 44% accessory vs efflux 13%)
- **`env_embedding_explorer`**: AlphaEarth embeddings cover 28% of genomes; 38% are human-associated; environmental samples show 3.4× stronger geographic signal
- **`resistance_hotspots`**: Proposed but never executed — our project supersedes its Phase 3

**Gap**: No study has mapped AMR profiles vs environment across 27K species with 293K genomes. Gibson (2015) used ~6K genomes; Martiny (2024) used metagenomes. Our pangenome dataset is 2 orders of magnitude larger and uses gene clusters with core/accessory classification — a significant advance.

## Data Sources

### Primary Data Assets

| Source | Table/File | Scale | Purpose |
|--------|-----------|-------|---------|
| `bakta_amr` | `kbase_ke_pangenome.bakta_amr` | 83K AMR clusters | AMR gene identification per gene cluster |
| `gene_cluster` | `kbase_ke_pangenome.gene_cluster` | 132M clusters | Core/accessory classification, species assignment |
| `pangenome` | `kbase_ke_pangenome.pangenome` | 27.7K species | Species-level stats (genome count, core/aux counts) |
| `ncbi_env` | `kbase_ke_pangenome.ncbi_env` | 4.1M rows (EAV) | Per-genome isolation source, host, geography |
| `genome` | `kbase_ke_pangenome.genome` | 293K genomes | genome_id → species mapping |
| `gtdb_taxonomy_r214v1` | `kbase_ke_pangenome.gtdb_taxonomy_r214v1` | 293K genomes | Phylogenetic classification (phylum → species) |
| AlphaEarth | `kbase_ke_pangenome.alphaearth_embeddings_all_years` | 83K genomes | Environmental embeddings (continuous) |
| InterProScan | `kbase_ke_pangenome.interproscan_go` | 266M rows | GO annotations for functional characterization |

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
       a.amr_gene, a.amr_product, a.method
FROM kbase_ke_pangenome.bakta_amr a
JOIN kbase_ke_pangenome.gene_cluster gc ON a.gene_cluster_id = gc.gene_cluster_id
```

2. **Species environment classification** — reuse from `amr_strain_variation` cached data or re-derive from `ncbi_env` using majority-vote at species level (91% coverage per prior project's approach).

3. **Phylogenetic context** for controlling phylogeny:
```sql
SELECT genome_id, phylum, class, order_name, family, genus
FROM kbase_ke_pangenome.gtdb_taxonomy_r214v1
```

### Performance Plan

- **Tier**: Spark on-cluster for initial data extraction; local pandas for analysis
- **bakta_amr** is small (83K rows) — safe to full-scan
- **gene_cluster** is large (132M rows) — JOIN with bakta_amr filters effectively
- **ncbi_env** is EAV (4.1M rows) — pivot to wide format after filtering
- **Known pitfalls**: ncbi_env EAV format, species IDs with `--`, string-typed numerics, AlphaEarth 28% coverage

## Analysis Plan

### Notebook 1: Data Extraction and Environment Classification (~30 min)

- **Goal**: Build species-level AMR profiles + environment labels
- **Method**:
  1. Extract bakta_amr × gene_cluster join to get AMR clusters with species and core/aux labels
  2. Classify species into environment categories: clinical, host-associated, soil, aquatic, other environmental, unknown
  3. Reuse `amr_strain_variation` species-level classification where available; extend to remaining species via `ncbi_env` majority-vote
  4. Get phylogenetic context (phylum, class, order) for each species from GTDB taxonomy
  5. Compute species-level AMR summary: total AMR clusters, core vs accessory AMR, AMR mechanism breakdown
- **Expected output**: `data/species_amr_profiles.csv`, `data/species_environment.csv`
- **Key figures**: AMR gene count distribution by environment, environment coverage bar chart

### Notebook 2: Resistome vs Environment (Species-Level) (~15 min)

- **Goal**: Test H1 and H3 — do AMR profiles differ between environments?
- **Method**:
  1. Compare total AMR gene count across environments (Kruskal-Wallis)
  2. Compare AMR mechanism composition (efflux, enzymatic, metal, target modification) across environments (chi-square per mechanism)
  3. Compare core vs accessory AMR fraction across environments (H2)
  4. Ordination: Jaccard distance of AMR profiles → PCoA, colored by environment
  5. Control for phylogeny: PERMANOVA with phylum as a covariate, or stratified analysis within major phyla
  6. Identify environment-specific AMR genes: which AMR clusters are found predominantly in one environment?
- **Expected output**: `data/environment_amr_comparison.csv`, figures
- **Key figures**: AMR count by environment boxplot, mechanism × environment heatmap, PCoA ordination, phylogeny-controlled forest plot

### Notebook 3: Within-Species AMR × Environment (~20 min)

- **Goal**: Test H4 — within species that span multiple environments, does AMR vary by niche?
- **Method**:
  1. Identify species with genomes in ≥2 environments (using per-genome ncbi_env classification)
  2. For each qualifying species, compare AMR gene presence/absence between environment groups
  3. Test whether within-species AMR Jaccard distance correlates with environment difference
  4. Case studies: deeply-sampled species (*K. pneumoniae*, *E. coli*, *P. aeruginosa*) where clinical vs environmental strains can be compared
- **Expected output**: `data/within_species_amr_environment.csv`, figures
- **Note**: Limited by ncbi_env coverage (53% unknown at per-genome level). Focus on species with ≥20 classified genomes.

### Notebook 4: AlphaEarth Continuous Environment Analysis (~10 min)

- **Goal**: Use continuous environmental embeddings instead of discrete categories
- **Method**:
  1. For the 83K genomes with AlphaEarth embeddings, compute AMR diversity (number of AMR clusters)
  2. Correlate embedding dimensions with AMR diversity (Spearman)
  3. Cluster genomes by embedding similarity and compare AMR profiles between clusters
  4. Test whether embedding distance predicts AMR profile distance (Mantel test)
- **Note**: Only 28% genome coverage; biased toward environmental samples. Results must be interpreted cautiously.

## Expected Outcomes

- **If H1 supported**: Soil species have more diverse intrinsic AMR (from natural antibiotic production), clinical species have more acquired AMR (from antibiotic selection). This would be the largest-scale confirmation of Gibson et al. (2015).
- **If H2 supported**: Core AMR genes partition cleanly by environment (ancient niche adaptation) while accessory AMR genes are more cosmopolitan (recent HGT). This would extend Jiang et al. (2024) from metagenomes to pangenomes.
- **If H3 supported**: Mechanism enrichment by environment would identify which resistance strategies are favored in each niche — actionable for environmental surveillance.
- **If H4 supported**: Within-species AMR variation tracks environment, confirming that AMR ecotypes reflect ecological adaptation, not just random drift.

## Potential Confounders

1. **Phylogenetic confound (critical)**: Environment and phylogeny are correlated (e.g., Enterobacteriaceae are overrepresented in clinical samples). All comparisons must control for phylogeny via PERMANOVA, stratification, or phylogenetic regression.
2. **Sampling bias**: NCBI is heavily biased toward clinical isolates and model organisms. Soil and aquatic species are underrepresented. Environment labels reflect sampling location, not the organism's true niche.
3. **ncbi_env metadata quality**: 53% of genomes lack usable isolation source. Species-level majority-vote (91% coverage) is the workaround, but this collapses within-species environmental variation.
4. **AlphaEarth coverage**: Only 28% of genomes, biased toward environmental samples with valid coordinates. Results from NB04 must be interpreted cautiously.
5. **bakta_amr detection sensitivity**: bakta_amr uses AMRFinderPlus which focuses on known resistance genes. Novel or cryptic resistance mechanisms in environmental bacteria may be missed.
6. **Core/accessory threshold**: The 95% prevalence threshold for "core" depends on species sampling depth. Species with few genomes have imprecise labels (median 9 genomes per FB species per `amr_fitness_cost`).

## Revision History

- **v1** (2026-03-19): Initial plan

## Authors

- **Paramvir S. Dehal** (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)) — Lawrence Berkeley National Laboratory

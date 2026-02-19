# Report: Gene-Environment Association Across Pangenome Species

## Key Findings

### 1. Environmental Metadata Coverage

- 292,913 genomes in the BERDL pangenome database have environment metadata from the `ncbi_env` EAV table
- Environment categories (after free-text pivot): human_clinical (104,932), other (81,829), host_associated (51,868), aquatic (33,834), soil (7,620), food (3,998), sediment (3,353), engineered (3,324), plant_associated (1,507), air (648)
- **212 species** meet the statistical testing threshold (>=2 environment categories with >=10 genomes each)
- Top species by qualifying genome count: *S. aureus* (12,906), *K. pneumoniae* (12,888), *S. pneumoniae* (7,933), *S. enterica* (6,838)

### 2. S. aureus Gene-Environment Associations (Proof of Concept)

13,351 of 133,007 accessory gene clusters (10.0%) show significant differential prevalence across 5 environment categories (q < 0.05, chi-squared with BH FDR correction):

| Environment | Enriched clusters |
|---|---|
| food | 4,681 |
| host_associated | 4,068 |
| aquatic | 1,678 |
| air | 1,549 |
| human_clinical | 1,375 |

**Food enrichment dominates** — unexpected for a primarily clinical/commensal pathogen. May reflect accessory genes supporting persistence in food-processing environments (biofilm, stress tolerance, AMR).

### 3. COG Enrichment in Environment-Associated Genes

5,134 of 13,351 significant S. aureus clusters have COG annotations. Top categories:

| COG | Function | Count |
|---|---|---|
| S | Unknown function | 1,698 |
| L | Replication/repair | 813 |
| M | Cell wall | 505 |
| K | Transcription | 348 |
| E | Amino acid metabolism | 295 |

**Mobilome (X) is enriched** in environment-associated vs background accessory genes, consistent with horizontal gene transfer driving niche adaptation.

### 4. Methylobacterium Descriptive Analysis (209 genomes)

**MDH profile x environment** (EC/KEGG-based classification):

| MDH Profile | Count |
|---|---|
| BOTH (xoxF + mxaF) | 176 |
| xoxF_only | 31 |
| mxaF_only | 0 |
| no_MDH | 2 |

Zero mxaF-only genomes reinforces the finding from `mextorquens_pangenome_case` that lanthanide-dependent xoxF is ubiquitous. xoxF_only genomes are distributed across host_associated (16), other (6), aquatic (4), air (2), soil (2), plant_associated (1) — no environment-specific pattern.

**B vitamin pathway completeness is remarkably uniform across environments:**

| Pathway | Range across environments |
|---|---|
| B9 (folate) | 94-100% |
| B1 (thiamine) | 75-88% |
| B12 (cobalamin) | 78-83% |
| B2 (riboflavin) | 65-70% |

Auxotrophy signals (B2, B1) are consistent regardless of isolation source. BOTH and xoxF_only genomes show similar B vitamin profiles (~45 total genes, 81% B12).

## Interpretation

### Literature Context

- **S. aureus food enrichment** aligns with Richardson et al. (2018), who found that gene exchange via mobile genetic elements enables *S. aureus* to colonize diverse host species and environments. Weinert et al. (2012) showed multiple host-switching events throughout *S. aureus* evolution.
- **Mobilome enrichment** is consistent with Ochman et al. (2000) establishing HGT as a primary driver of bacterial niche adaptation, and Brockhurst et al. (2019) reviewing how environmental context shapes accessory genome content.
- **Environment shapes pangenomes**: Maistrenko et al. (2020) showed environmental preferences explain up to 49% of prokaryotic within-species diversity — stronger than phylogenetic inertia. This validates our framework of linking gene cluster presence/absence to environmental metadata.
- **Pan-GWAS methods** (Brynildsrud et al., 2016; Lees et al., 2018) provide more sophisticated alternatives to our Fisher's exact approach by controlling for population structure — a natural next step.
- **Methylobacterium xoxF ubiquity** is consistent with Chistoserdova & Kalyuzhnaya (2018) noting XoxF genes are more widespread than MxaF. Our genome-level environmental analysis extends this to show no environment-specific MDH pattern across 209 genomes.

### Novel Contributions

1. Reusable EAV-to-category pivot of `ncbi_env` metadata covering 292,913 genomes across 9 environment categories
2. Gene-environment association framework tested at scale (133,007 clusters x 12,913 genomes for S. aureus)
3. Identification of 212 species qualifying for gene-environment association testing in BERDL
4. First genome-level MDH x environment analysis for *Methylobacterium* (209 genomes)

### Limitations

- Environment categorization from free-text `isolation_source` is heuristic and lossy (e.g., "leaves" maps to "other" not "plant_associated")
- `ncbi_env` coverage is incomplete; many genomes lack metadata
- Only one species (S. aureus) completed as proof of concept due to Spark Connect auth timeout (~40 min)
- No correction for population structure (phylogenetic non-independence) in the current Fisher's exact/chi-squared approach
- COG enrichment uses a sampled background (5,000 clusters) rather than all accessory clusters
- Methylobacterium analysis is descriptive only — sample sizes too small for formal testing (82 host_associated, 14 aquatic, 10 soil, 5 plant_associated, 4 air, 1 clinical)

## Methods

### Environment Metadata (Notebook 02)
- Pivoted `ncbi_env` EAV table to per-genome environment categories using keyword matching on `isolation_source`
- Cross-tenant join with `nmdc_ncbi_biosamples` for NMDC harmonized ontology labels
- Output: `genome_env_metadata.csv` (292,913 genomes)

### Gene-Environment Association (Notebook 03)
- Species selection: >=2 environment categories with >=10 genomes each (212 species qualify)
- Built presence/absence matrix of accessory gene clusters per genome via `gene_genecluster_junction`
- Per-cluster test: chi-squared (>2 categories) or Fisher's exact (2 categories)
- Multiple testing correction: Benjamini-Hochberg FDR, q < 0.05
- COG enrichment: compared significant vs background (sampled) clusters

### Methylobacterium Descriptive Analysis (Notebook 03, Section 10)
- MDH classification: EC/KEGG priority (same as notebook 01 in `mextorquens_pangenome_case`)
- B vitamin pathway completeness: gene name matching against curated pathway definitions
- Genome-level crosstabs of MDH profile and B vitamin completeness by environment category

# BERIL Research Observatory - Data Documentation Index

**Last Updated:** April 25, 2026 (Phase 2b refresh)
**Maintainer:** Adam Arkin (aparkin@berkeley.edu)

---

## Overview

This directory contains reusable datasets across BERIL research projects. The **plant_microbiome_ecotypes** project has generated the primary dataset (73 CSV files, 873 MB, 7.8M rows after Phase 2b), with complementary validation data available from cross-project analyses. Phase 2b (April 25, 2026) closed all five issues raised in the paired adversarial review and added quantitative controls (db-RDA for H1, cluster-robust GLM for C1, real per-species genome-size control for C4, full 65→18 species subclade scan for H7, bakta-vs-IPS Pfam audit). The canonical post-Phase-2b state is in `projects/plant_microbiome_ecotypes/REPORT.md` §11 and `projects/plant_microbiome_ecotypes/data/hypothesis_verdicts_final.csv`.

## Documentation Files

### 1. **DATA_INVENTORY.md** (Start Here)
Comprehensive reference documenting all available datasets:
- 73 files in plant_microbiome_ecotypes (detailed descriptions, sizes, row counts)
- Phase 1 / Phase 2 / Phase 2b layering with explicit "preferred" tags where files supersede each other
- Column specifications and data types
- Reusability notes for each dataset
- Cross-project validation resources
- **NEW (Phase 2b):** Cross-project pitfalls section — gotchas worth knowing for any future BERDL work

**Use when:** You need detailed information about a specific dataset or want to understand data relationships.

### 2. **DATA_QUICK_REFERENCE.txt**
Visual quick-lookup guide with:
- File sizes and row counts
- Dataset organization by category, including a dedicated Phase 2b Statistical Controls block
- Key joining columns
- Phase 2b headline verdicts inline
- Quick access patterns
- Cross-project data locations

**Use when:** You want to quickly find a file or remember column names.

### 3. **DATA_ACCESS_EXAMPLES.py**
Executable Python code examples demonstrating:
1. Loading core reference datasets (Phase 1 + Phase 2 cohorts side-by-side)
2. Filtering by plant association
3. Creating integrated feature matrices
4. Joining environmental context
5. Validating predictions with NMDC abundance
6. Finding metabolically complementary consortia (using the corrected `complementarity_v2.csv`)
7. Plant enrichment analysis (GWAS-style)
8. Cross-validating with fitness browser
9. Pangenome HGT analysis
10. **NEW:** Reading canonical Phase 2b hypothesis verdicts
11. **NEW:** Cross-checking bakta vs InterProScan for Pfam queries (the pitfall)

**Use when:** You want working code to start an analysis.

---

## Plant Microbiome Ecotypes Dataset

**Location:** `/home/aparkin/BERIL-research-observatory/projects/plant_microbiome_ecotypes/data/`

**Scope:**
- 73 CSV files (873 MB total)
- 25,660 bacterial species
- 293,059 bacterial genomes
- 7.8 million rows across all files

### Essential Files

**Core Reference (Start with these):**
1. **species_cohort_refined.csv** (2.5 MB) — *Phase 2 (preferred over `cohort_assignments.csv`)*
   - Refined Phase 2 cohort labels: beneficial / pathogenic / dual-nature / neutral
   - Built from 17 plant-specific markers + KEGG-module gating
   - Key columns: `gtdb_species_clade_id`, `cohort_refined`, `n_pgp_refined`, `n_pathogen_refined`, `dominant_host`
   - **Validation caveat (Phase 2b)**: the categorical label is uninformative at species level — use the continuous `n_pathogen_refined / (n_pgp_refined + n_pathogen_refined)` ratio for discrimination

2. **hypothesis_verdicts_final.csv** (5.3 KB)
   - Canonical post-Phase-2b verdicts for all 8 hypotheses (H0–H7)
   - Read this rather than parsing chronological notebook outputs

3. **genome_environment.csv** (65.9 MB)
   - Genome-to-environment mapping
   - Plant-association classification, taxonomic context
   - Key columns: `genome_id`, `gtdb_species_clade_id`, `compartment`, `is_plant_associated`

4. **gapmind_plant_species.csv** (137.3 MB)
   - Metabolic pathway completeness per species
   - 4 metabolic categories: carbon, amino acid, nucleotide, cofactor
   - **Note:** Filter before loading to RAM (~137 MB unfiltered)

### Functional Annotation Files
- `bakta_marker_hits.csv` — *Phase 1 marker panel*: PGP genes (nifH, acdS, pqqA-E, ipdC, hcnA-C) + 50 pathogenic markers
- `interproscan_marker_hits.csv` — *Phase 2 InterProScan recovery* (preferred for T3SS/T4SS/T6SS)
- `pfam_recovery_hits.csv` — *Phase 2b Pfam LIKE recovery*
- `pfam_bakta_ips_audit.csv` — *Phase 2b: documents that 12/22 marker Pfams are silently missing from `bakta_pfam_domains` despite being abundant in InterProScan — important cross-project gotcha*
- `marker_gene_clusters.csv` — Full pangenome-level gene cluster membership
- `species_marker_matrix.csv` — *Phase 1*: 25 binary traits per species
- `species_marker_matrix_v2.csv` — *Phase 2 refined*: 17 plant-specific traits + KEGG gating (preferred)
- `kegg_marker_hits.csv` — KEGG orthology mapping
- `kegg_module_completeness.csv` — *Phase 2*: KEGG module gene counts (used for T3SS/T4SS/N-fix gating)
- `genome_host_species.csv` — *Phase 2*: per-genome plant host assignments

### Novel-OG Annotation (NB09)
- `novel_og_annotations.csv` — Aggregate per-OG annotations
- `novel_og_eggnog_annotations.csv` (276 MB) — Per-cluster eggNOG annotations
- `novel_og_bakta.csv`, `novel_og_interproscan.csv`, `novel_og_domains.csv`, `novel_og_go_terms.csv`, `novel_og_pathways.csv` — Per-source detailed annotations
- `top50_og_species.csv` — Species × 50 novel OGs presence/absence matrix
- `enrichment_results.csv` — Genome-wide eggNOG OG enrichment (GWAS-style)
- `novel_plant_markers.csv` — The 50 plant-enriched OGs surviving phylum control

### Phase 2b Statistical Controls (April 24–25, 2026)
- `c1_cluster_robust.csv` — Cluster-robust GLM (cluster=genus); 8/14 markers significant at q<0.05 BH-FDR
- `regularized_phylo_control.csv` — L1-regularized logit (Phase 2b draft, kept for comparison)
- `sensitivity_shuffle.csv` — Within-genus label shuffling: 3/15 markers survive (N-fix, ACC deaminase, T3SS)
- `genome_size_control.csv` — Real per-species genome-size + phylum control: 48/50 OGs survive at q<0.05
- `h1_dbrda_results.csv`, `h1_compartment_dispersions.csv` — db-RDA + PERMDISP: location-only R²=0.060 (84% of total)
- `complementarity_v2.csv` — Prevalence-weighted complementarity (use this, not `complementarity_network.csv` — the original had a Cohen's d formula error)
- `species_validation.csv` — 18-species ground-truth panel; Mann-Whitney p=0.027 on continuous pathogen ratio
- `subclade_full_scan.csv`, `species_subclade_definitions_full.csv` — Full 65→18 species subclade × plant scan; 5/17 testable significant
- `h6_host_subclade_full.csv` — Subclade × plant-host scan; 2/9 species pass both Bonferroni corrections (X. campestris × Brassica, X. vasicola × maize)

### Validation & Summary Files
- `pangenome_stats.csv` — Pangenome openness (HGT burden indicator)
- `complementarity_v2.csv` — Genus-pair metabolic complementarity (Phase 2b corrected — use this, not the older `complementarity_network.csv`)
- `nmdc_genus_abundance.csv` — Real-world abundance in soil metagenomes
- `species_compartment.csv` — Dominant ecological niche per species
- `genus_dossiers.csv` — Summarized genus phenotypes + marker lists

### MGnify Cross-Validation (NB11)
- `mgnify_pangenome_bridge.csv` — MGnify species → GTDB taxonomy bridge
- `mgnify_host_specificity.csv` — Genus × rhizosphere biome presence
- `mgnify_mobilome.csv` — Mobile element annotations (supports H4: 3.7 vs 2.8 MEs/genome, p=1.5e-5)
- `mgnify_bgc_profiles.csv` — Biosynthetic gene cluster profiles (84 plant-associated genera with NRP/siderophore BGCs)
- `mgnify_kegg_biome_profiles.csv`, `mgnify_rhizo_vs_soil_cog.csv`, `mgnify_soil_bgc_summary.csv` — Cross-biome summaries

### Full File Listing
See `DATA_INVENTORY.md` for complete descriptions of all 73 files.

---

## Key Joining Columns

Use these columns to link datasets:

| Column | Tables | Usage |
|--------|--------|-------|
| `gtdb_species_clade_id` | Most species-level files | Universal species identifier |
| `genome_id` | genome_environment.csv, genome_host_species.csv | Genome-level linkage |
| `genus` | cohort_assignments.csv, abundance files | Genus-level aggregation |
| `file_id` | nmdc_soil_file_ids.csv, nmdc_genus_abundance.csv | NMDC metagenome linkage |
| `og_id` | novel_og_*, top50_og_species, genome_size_control | eggNOG OG / COG identifier |

---

## Cross-Project Validation Data

High-value datasets from other BERIL projects for validation:

| Project | File | Size | Purpose |
|---------|------|------|---------|
| conservation_vs_fitness | fb_pangenome_link.tsv | 22 MB | Cross-validate predicted phenotypes against measured fitness (~30 organisms) |
| functional_dark_matter | carrier_genome_map.tsv | 145 MB | Identify uncharacterized ortholog biogeography |
| prophage_ecology | enriched_lineages.tsv | 1.4 GB | Overlay defense systems with plant-associated traits |
| phb_granule_ecology | nmdc_phb_prevalence.tsv | 38 MB | Stress tolerance marker integration |
| cf_formulation_design | asma_pa_virulence_profiles.tsv | 35 MB | Pseudomonas virulence validation |

See `DATA_INVENTORY.md` for full paths and details.

---

## Cross-Project Pitfalls (Phase 2b additions)

These were captured during plant_microbiome_ecotypes Phase 2b and are worth knowing for any future BERDL work. Full descriptions in `projects/plant_microbiome_ecotypes/docs/pitfalls.md`.

1. **`bakta_pfam_domains` silently omits ~half of marker Pfams** (especially T3SS/T4SS/T6SS components — 12 of 22 marker Pfams in this project, abundant in `interproscan_domains` but absent from bakta). Always cross-check `interproscan_domains.signature_acc` before drawing conclusions about absent functions.
2. **Versioned Pfam IDs**: `bakta_pfam_domains.pfam_id` stores versioned accessions (`PF00771.22`). Use `LIKE 'PF00771%'`, not `IN ('PF00771')`.
3. **`phylogenetic_tree_distance_pairs` is sparse** — only ~28% of plant-associated species with ≥20 genomes have tree data. Pre-check coverage before any subclade analysis.
4. **Genome-ID prefix mismatch**: `phylogenetic_tree_distance_pairs.genome*_id` uses bare NCBI accessions (`GCA_*`, `GCF_*`), while the `genome` and `ncbi_env` tables use GTDB-prefixed IDs (`GB_GCA_*`, `RS_GCF_*`). Prepend the right prefix before joining.
5. **`species_compartment.csv` column is `dominant_compartment`, not `compartment`** — but the per-genome `genome_environment.csv` does have `compartment`.
6. **Cohen's d formula sensitivity**: dividing the mean difference by the SD of permutation means (instead of the raw pair-level SD) inflates apparent effect sizes by 10–20×. Use the raw pair-level SD for cross-study comparability.

---

## Quick Start Guide

### 1. Load Minimal Dataset (Fast)
```python
import pandas as pd
PME = '/home/aparkin/BERIL-research-observatory/projects/plant_microbiome_ecotypes/data'

# Phase 2 refined cohorts (preferred over cohort_assignments.csv for new analyses)
cohorts = pd.read_csv(f'{PME}/species_cohort_refined.csv')
print(cohorts.shape)  # (25660, 11)
print(cohorts['cohort_refined'].value_counts())

# Canonical Phase 2b verdicts
verdicts = pd.read_csv(f'{PME}/hypothesis_verdicts_final.csv')
print(verdicts[['id', 'final_verdict']])
```

### 2. Add Environmental Context
```python
# Load genome-to-environment mapping (~66 MB, 1-2 sec)
genome_env = pd.read_csv(f'{PME}/genome_environment.csv')

# Filter to plant-associated only
plant_genomes = genome_env[genome_env['is_plant_associated'] == True]

# Link species phenotypes
species_env = plant_genomes.merge(
    cohorts[['gtdb_species_clade_id', 'cohort_refined', 'n_pgp_refined', 'n_pathogen_refined']],
    on='gtdb_species_clade_id'
)
```

### 3. Add Traits for Machine Learning
```python
# Load 17-trait Phase 2 refined matrix
traits = pd.read_csv(f'{PME}/species_marker_matrix_v2.csv')

# Merge with refined cohort labels
full_matrix = cohorts.merge(traits, on='gtdb_species_clade_id')

# Per Phase 2b validation, prefer the continuous discriminator over the categorical label:
import numpy as np
full_matrix['pathogen_ratio'] = full_matrix['n_pathogen_refined'] / (
    full_matrix['n_pgp_refined'] + full_matrix['n_pathogen_refined']
).replace(0, np.nan)
```

### 4. Validate with Real-World Data
```python
# Load NMDC soil abundance (~2 MB)
nmdc = pd.read_csv(f'{PME}/nmdc_genus_abundance.csv')
# (see DATA_ACCESS_EXAMPLES.py for the full validation pattern)
```

### 5. Check Pfam Coverage Before Querying (Phase 2b lesson)
```python
# If you're about to query bakta_pfam_domains, always cross-check IPS first
audit = pd.read_csv(f'{PME}/pfam_bakta_ips_audit.csv')
silent_gaps = audit[audit['silent_gap']]
print('Pfams missing from bakta but in InterProScan:')
print(silent_gaps[['pfam_id', 'ips_hits', 'bakta_hits']])
```

---

## Data Access Patterns

### Pattern 1: Filter by Plant Association
```python
# Method 1: Use genome-level flag
plant_genomes = genome_env[genome_env['is_plant_associated'] == True]

# Method 2: Use plant compartments
plant_comp = genome_env[genome_env['compartment'].isin(
    ['rhizosphere', 'phyllosphere', 'endosphere']
)]

# Method 3: Use refined species-level classification (Phase 2 preferred)
plant_species = cohorts[cohorts['is_plant_associated'] == 1.0]
```

### Pattern 2: Load Large Files Efficiently
```python
# GapMind is 137 MB; filter first
species_ids = cohorts['gtdb_species_clade_id'].unique()
gapmind = pd.read_csv(f'{PME}/gapmind_plant_species.csv')
gapmind_filt = gapmind[gapmind['gtdb_species_clade_id'].isin(species_ids)]

# novel_og_eggnog_annotations.csv is 276 MB — use chunked read for production code
```

### Pattern 3: Create Analysis-Ready Matrices
```python
df = pd.read_csv(f'{PME}/species_cohort_refined.csv')
df = df.merge(pd.read_csv(f'{PME}/species_marker_matrix_v2.csv'), on='gtdb_species_clade_id')
df = df.merge(pd.read_csv(f'{PME}/species_compartment.csv'), on='gtdb_species_clade_id')
# Ready for analysis/ML
```

### Pattern 4: Use Phase 2b corrected complementarity (not the original)
```python
# DO use complementarity_v2.csv (prevalence-weighted, formula-corrected)
comp = pd.read_csv(f'{PME}/complementarity_v2.csv')

# DO NOT use complementarity_network.csv as the headline result
# (its reported Cohen's d = -7.54 was a formula error; real magnitude is |d|≈0.4)
```

---

## Data Quality & Notes

### File Formats
- **Format:** CSV (UTF-8, comma-delimited)
- **No preprocessing needed** — data ready for direct loading
- **Index columns:** Most files use `gtdb_species_clade_id` as key

### Size Considerations
- **Total active data:** 873 MB (plant_microbiome_ecotypes)
- **Largest files:** novel_og_eggnog_annotations (276 MB), gapmind_plant_species (137 MB), transposase_singletons (104 MB), marker_gene_clusters (67 MB), genome_environment (66 MB)
- **Typical analysis:** 3–30 MB subset

### Missing Data
- Minimal NaN values except in computed fields (e.g., `avg_complementarity`, `pathogen_ratio` when both PGP and pathogen counts are zero)
- Use `.fillna(0)` for ML models on trait matrices

---

## Definitions

**Phase 2 cohorts** (from `species_cohort_refined.csv['cohort_refined']`):
- `beneficial`: Carries one or more PGP markers but no pathogenic markers
- `pathogenic`: Carries one or more pathogenic markers but no PGP markers
- `dual-nature`: Carries both PGP and pathogenic markers (78.7% of plant-associated species)
- `neutral`: No markers in either category

> **Phase 2b validation note**: All 14 known beneficial + pathogenic model organisms in the species-validation panel were assigned to `dual-nature`. The categorical label cannot discriminate beneficial from pathogenic; use the continuous `pathogen_ratio` as the discriminator. (Mann-Whitney p=0.027 between known-beneficial and known-pathogenic species, N=7+7.)

**Phase 1 cohorts** (from `cohort_assignments.csv['cohort']`, kept for legacy comparison):
- `beneficial` / `neutral` / `pathogenic` from NB07 composite scoring (no `dual-nature` class)

**Compartments** (plant-associated):
- `rhizosphere`: Root-associated soil
- `phyllosphere`: Leaf surface
- `endosphere`: Inside plant tissues
- `root`: Root surface (distinct from rhizosphere proper)
- `host_clinical`: Human/animal host (non-plant)
- `soil`: Soil (non-plant-associated)
- `plant_other`: Ambiguous plant-associated isolation
- `other`: Miscellaneous

**PGP Functions Detected (Phase 2 refined panel, 9 of 17 markers):**
- Nitrogen fixation (nifH/D/K) with M00175 module gating ≥2 genes
- ACC deaminase (acdS) — ethylene pathway modulation
- Phosphate solubilization (pqqA–E)
- IAA biosynthesis (ipdC)
- DAPG biocontrol
- Phenazine
- Hydrogen cyanide (hcnA–C)
- Acetoin/butanediol
- Siderophore

**Pathogenic Markers (Phase 2 refined panel, 8 of 17 markers):**
- T3SS (with M00332 module gating ≥3 structural genes)
- T4SS (with M00333 module gating ≥3 genes)
- Effector
- Phytotoxin
- Coronatine toxin
- CWDE cellulase, CWDE pectinase
- Other pathogenic

**HGT Burden (Openness):**
- Computed as: (singleton genes) / (total genes in pangenome)
- High openness (>0.5) indicates recent horizontal gene transfer
- Cross-validated by Phase 2 NB11 mobilome (median 3.7 ME/genome in plant genera vs 2.8 in non-plant, Mann-Whitney p=1.5×10⁻⁵)

---

## For More Information

1. **Detailed dataset descriptions:** `DATA_INVENTORY.md`
2. **Quick lookups:** `DATA_QUICK_REFERENCE.txt`
3. **Working code examples:** `DATA_ACCESS_EXAMPLES.py`
4. **Project synthesis:** `projects/plant_microbiome_ecotypes/REPORT.md` (esp. §11 Phase 2b)
5. **Pitfalls captured:** `projects/plant_microbiome_ecotypes/docs/pitfalls.md`
6. **Paired adversarial review:** `projects/plant_microbiome_ecotypes/docs/adversarial_review_2026-04-24.md`
7. **Canonical reviewer report:** `projects/plant_microbiome_ecotypes/REVIEW.md`

---

## Citation

If using this data in publications, please cite the plant_microbiome_ecotypes project:

> Arkin, A., et al. (2026). Plant Microbiome Ecotypes: Compartment-Specific Functional Guilds and Their Genetic Architecture. BERIL Research Observatory. Preprint/Publication details TBD.

---

**Questions or Issues?** Contact Adam Arkin (aparkin@berkeley.edu)

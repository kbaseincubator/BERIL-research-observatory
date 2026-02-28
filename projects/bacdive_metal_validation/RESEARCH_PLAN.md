# Research Plan: BacDive Isolation Environment × Metal Tolerance Prediction

## Research Question

Do bacteria isolated from metal-contaminated environments have higher predicted metal tolerance scores than bacteria from uncontaminated environments? This tests whether the Metal Fitness Atlas's genome-based metal tolerance prediction method correlates with real-world isolation ecology.

## Hypothesis

- **H0**: Metal tolerance scores are independent of isolation environment — organisms from metal-contaminated sites have the same score distribution as organisms from other environments.
- **H1**: Organisms isolated from metal-contaminated environments have significantly higher metal tolerance scores than organisms from uncontaminated environments, validating the atlas prediction method against ecological data.

### Sub-hypotheses

- **H1a**: Heavy metal contamination isolates (BacDive cat3=#Heavy metal, n=31) have higher metal_score_norm than the environmental baseline.
- **H1b**: Broader contamination isolates (cat2=#Contamination, n=427) show elevated metal scores.
- **H1c**: Industrial and waste/sludge isolates (often metal-rich environments) show intermediate elevation.
- **H1d**: Host-associated bacteria (cat1=#Host) have lower metal scores than free-living environmental bacteria, reflecting reduced metal exposure in host niches.
- **H1e** (exploratory): Organisms with positive BacDive metal utilization tests (iron, manganese, arsenate, chromate) have higher metal tolerance scores than those testing negative.

## Literature Context

- The Metal Fitness Atlas scored 27,702 pangenome species using a 1,286-term KEGG functional signature derived from cross-species RB-TnSeq fitness data. It validated the scoring against known bioleaching organisms (Leptospirillum 91st percentile, Acidithiobacillus 77th).
- BacDive (Reimer et al. 2022, *Nucleic Acids Research*) is the largest standardized bacterial phenotype database (97K strains). Its hierarchical isolation source categories include #Heavy metal contamination.
- No prior study has validated genome-based metal tolerance predictions against isolation environment metadata at this scale.
- Carlson et al. 2019 (*ISME J*) used Fitness Browser data to predict which organisms survive at Oak Ridge metal-contaminated sites, but used organism-level fitness, not genome-based scoring.
- The lab_field_ecology project (this observatory) found a suggestive but non-significant correlation between lab metal tolerance and field abundance at Oak Ridge (rho=0.50, p=0.095, n=11 genera), providing context for expected effect sizes.

## Data Sources

All data available locally — no Spark required for primary analysis.

### Primary Data

| Source | File | Content |
|--------|------|---------|
| BacDive | `data/bacdive_ingest/sequence_info.tsv` | 27,502 GCA genome accessions for 19,592 strains |
| BacDive | `data/bacdive_ingest/isolation.tsv` | 57,935 isolation records with cat1/cat2/cat3 hierarchy |
| BacDive | `data/bacdive_ingest/taxonomy.tsv` | 97,334 strains with full LPSN taxonomy |
| BacDive | `data/bacdive_ingest/metabolite_utilization.tsv` | 988,259 utilization tests (98 metal-related) |
| Metal Atlas | `projects/metal_fitness_atlas/data/species_metal_scores.csv` | 27,702 species with metal_score_norm |

### Bridge Data (to be generated)

| Source | Table | Purpose |
|--------|-------|---------|
| BERDL | `kbase_ke_pangenome.genome` | Map GCA accessions → gtdb_species_clade_id |

## Query Strategy

### Tables Required

| Table | Purpose | Estimated Rows | Filter Strategy |
|-------|---------|----------------|-----------------|
| `kbase_ke_pangenome.genome` | GCA → species mapping | 293K total | Filter by `genome_id LIKE 'GB_GCA_%'` |

### Key Query

```sql
SELECT genome_id, gtdb_species_clade_id
FROM kbase_ke_pangenome.genome
WHERE genome_id LIKE 'GB_GCA_%'
```

This returns ~100-150K rows (GenBank genomes only). The join to BacDive is done locally by matching `GB_{accession}%` patterns.

### Performance Plan
- **Tier**: REST API for genome table query (single query, moderate result set)
- **Estimated complexity**: Simple — one query, rest is local joins
- **Known pitfalls**:
  - BacDive accessions lack version suffix (GCA_000193495 vs GB_GCA_000193495.1)
  - gtdb_species_clade_id contains `--` (fine in quoted strings)
  - Many BacDive strains won't match pangenome (different assemblies, missing from GTDB r214)

## Analysis Plan

### Notebook 1: Build the BacDive → Pangenome Bridge
- **Goal**: Link BacDive strains to pangenome species and metal tolerance scores
- **Method**:
  1. Load BacDive sequence_info, isolation, taxonomy
  2. Query pangenome genome table for GCA→species mapping (REST API or local extract)
  3. Join BacDive GCA accessions to pangenome genome_id (prefix match: `GB_{accession}%`)
  4. Join to species_metal_scores.csv via gtdb_species_clade_id
  5. Report match rates at each step
- **Expected output**: `data/bacdive_pangenome_bridge.csv`

### Notebook 2: Metal Score × Isolation Environment
- **Goal**: Test H1a-H1d — do metal-contaminated isolates have higher metal scores?
- **Method**:
  1. Join bridge table with isolation categories
  2. Power analysis: compute minimum detectable effect size at 80% power for the heavy-metal group (n=31 vs baseline), so a null result is interpretable
  3. Mann-Whitney U test for each environment comparison
  4. Effect sizes (Cohen's d) and bootstrap confidence intervals
  5. Phylogenetic confounding check: genus/phylum distribution in contamination vs baseline
  6. Phylum-stratified permutation test: within Proteobacteria, Firmicutes, Actinobacteriota separately to control for phylogenetic bias in culture collections
- **Expected output**: `data/environment_metal_scores.csv`, `figures/metal_score_by_environment.png`

### Notebook 3: Metal Utilization Phenotypes (Exploratory)
- **Goal**: Test H1e — do organisms with positive metal utilization tests have higher metal scores?
- **Method**:
  1. Filter BacDive metabolite_utilization for metal compounds (98 records)
  2. Join with bridge table for metal scores
  3. Compare positive vs negative utilization by metal compound
- **Expected output**: `data/metal_utilization_validation.csv`, `figures/utilization_vs_score.png`
- **Note**: Small sample sizes (n=98 total) — exploratory only

## Expected Outcomes

- **If H1 supported**: Heavy metal contamination isolates score significantly higher than baseline, validating the atlas prediction method against real-world ecology. This would demonstrate that genome content predicts environmental metal tolerance.

- **If H0 not rejected**: Metal tolerance scores do not predict isolation environment, suggesting that genome-encoded metal tolerance genes are broadly distributed (consistent with the 88% core enrichment finding from metal_specificity) and cannot discriminate metal-adapted from non-adapted organisms by gene content alone.

- **Potential confounders**:
  - Phylogenetic confounding: contamination isolates may be dominated by a few genera (Pseudomonas, Cupriavidus)
  - BacDive sampling bias: culture collection strains are not representative of environmental diversity
  - Low match rate between BacDive GCA accessions and pangenome genomes
  - Small sample sizes for heavy metal category (n=31)

## Revision History
- **v1** (2026-02-28): Initial plan
- **v2** (2026-02-28): Plan review feedback: added power analysis for n=31 group, phylum-stratified permutation test, lab_field_ecology cross-reference. Verified BacDive accessions have no version suffix (0/27,502). Confirmed species_metal_scores.csv exists locally.

## Authors
- Paramvir Dehal, Lawrence Berkeley National Laboratory, US Department of Energy

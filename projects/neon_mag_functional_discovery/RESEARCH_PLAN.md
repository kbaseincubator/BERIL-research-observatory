# Research Plan: NEON Metagenome Lineage Novelty and Functional Ecology

## Research Question

Across the three NEON metagenome studies in NMDC (soil, surface water, benthic sediment): where does microbial lineage novelty concentrate, what KO/Pfam content discriminates habitats and tracks soil chemistry, and where do environmental MAGs carry accessory genes that cultured pangenome representatives of the same genus do not?

## Hypotheses

### H1 — Lineage novelty is driven by soil pH
- **H0**: Per-MAG probability of having no GTDB genus assignment does not depend on soil pH.
- **H1**: Per-MAG probability of no-genus-call scales monotonically with soil pH (direction not pre-specified).
- **Falsification**: Logistic regression (or OLS as a sign-check) of per-MAG novelty on raw soil pH yields slope p ≥ 0.05, **or** the novel-fraction varies by less than 5 percentage points across the observed soil pH range (≈ 3.5–8).
- **Statistical-method note**: An earlier draft of this plan called for a Mann–Kendall / Kendall-τ trend test on novel-fraction aggregated into 4 pH bins. With only 4 (bin, fraction) points the test's smallest achievable two-sided exact p is **2/4! = 1/12 ≈ 0.083**, so even a perfect τ = 1.0 cannot clear α = 0.05 — the test is structurally underpowered against that binning. We therefore evaluate H1 on the raw per-record data, where n is in the thousands. The aggregated table and Kendall τ are still reported in NB02 as a descriptive monotonicity check.

  **Kendall-τ power floor by bin count** (smallest achievable two-sided exact p for monotone trend; computed in `data/kendall_power_floor.tsv`):

  | n bins | min two-sided p | Clears α = 0.05? | Clears α = 0.01? |
  |---|---|---|---|
  | 3 | 0.333 | no | no |
  | 4 | 0.083 | no | no |
  | 5 | 0.017 | **yes** | no |
  | 6 | 0.0028 | yes | **yes** |
  | 7 | 4.0 × 10⁻⁴ | yes | yes |
  | 8 | 5.0 × 10⁻⁵ | yes | yes |
  | 10 | 5.5 × 10⁻⁷ | yes | yes |

  Rule of thumb: **use ≥ 5 bins for Kendall-style aggregated trend tests** with α = 0.05. NEON soil n = 3,161 records over pH 3.23–9.13 would support 5–8 bins comfortably (~400–600 records per bin). The 4-bin choice was a pre-registration mistake; either use 5+ bins or apply the per-record OLS / logistic regression as the primary test (what NB02 does). This pitfall is generic to any "aggregate-then-rank-test" workflow.

### H2 — Habitat-discriminating KOs are enriched in expected biogeochemistry
- **H0**: KOs differentially abundant between habitats are a random sample of KEGG.
- **H1**: Habitat-discriminating KOs are enriched (Fisher exact, FDR < 0.05) for:
  - Soil-enriched: glycoside hydrolase / peptidase / nitrogen-fixation / urease modules (C and N cycling in plant-litter soils)
  - Water-enriched: photosynthesis / oxygenic phototrophy / aerobic CO oxidation / photoheterotrophy
  - Benthic-enriched: methanogenesis / sulfate reduction / dissimilatory nitrate reduction (anaerobic respiration)
- **Falsification**: None of the three habitats show enrichment for any KEGG module above FDR threshold.

### H3 — Soil chemistry tracks functional composition
- **H0**: Soil sample × KO PCoA shows no association with pH, C:N, or horizon (PERMANOVA p > 0.05).
- **H1**: pH and horizon each explain ≥ 5% of variance in KO composition (PERMANOVA R² ≥ 0.05, p < 0.001).

### H4 — Environmental MAGs carry KOs absent from cultured pangenome reps of the same genus
- For each of the ~249 genera with ≥1 NEON MAG (MQ+HQ) and ≥1 KE pangenome species representative:
- **H0**: NEON-MAG accessory KO sets are a strict subset of the cultured-pangenome KO sets for that genus.
- **H1**: NEON-MAG accessory KO sets include KOs not seen in any cultured pangenome member of the same genus, and those KOs are enriched for environmental-process functions (metal homeostasis, secondary metabolism, anaerobic respiration).
- **Falsification**: Fewer than 10% of overlapping-genus comparisons show any NEON-only KO above per-gene-cluster occurrence threshold.

### Bonus — Soil archaeal pH niche (small panel)
- 40 archaeal MAGs from soil; 4 HQ. Descriptive only: do they appear at pH extremes, and do their KO profiles include known archaeal-marker functions (ammonia oxidation, methanogenesis)? Reported as supplementary, not load-bearing.

## Literature Context

NMDC's NEON re-hosting was announced as part of the NMDC–NEON collaboration (https://microbiomedata.github.io/nmdc_notebooks/neon_python.html provides an entry point that queries study `nmdc:sty-11-34xj1150` via the NMDC API and produces an interactive site map of soil pH and water content). The NMDC notebook does not perform downstream lineage or functional analysis — it stops at biosample metadata. This project picks up where that notebook stops.

Relevant background:
- NEON's terrestrial soil sampling design (~73 sites, multiple horizons, repeat sampling) is well-documented in NEON Technical Working Group materials. Coverage in NMDC: 6,489 biosamples from this study alone.
- KBase KE pangenome catalog (27,690 GTDB species) provides cultured-genome accessory-gene baselines. Pangenome species representatives are GTDB-typed, enabling genus-level joins with environmental MAGs.
- Soil pH as a primary driver of microbial community structure is established (Fierer & Jackson 2006; Lauber et al. 2009 and follow-ups); NEON's pH range (3.5–8 across sites) is well-suited to revisit this with MAG-level resolution.

A focused literature search will be performed in NB02 once habitat-discriminating KOs are identified, to ground the functional enrichment interpretation.

## Data Sources

All data lives in the BERDL Lakehouse (`nmdc` and `kbase` tenants).

| Database | Table | Use |
|----------|-------|-----|
| `nmdc_metadata` | `study_set` | Study records (3 NEON studies) |
| `nmdc_metadata` | `biosample_set` | 7,459 NEON biosamples; pH, soil_horizon, depth, lat/lon, env-scale terms |
| `nmdc_metadata` | `biosample_set_associated_studies` | Biosample ↔ study (join on `parent_id` = biosample id; `associated_studies` = study id) |
| `nmdc_metadata` | `data_generation_set` | Per-sample metagenome sequencing records |
| `nmdc_metadata` | `data_generation_set_associated_studies` | Data generation ↔ study link |
| `nmdc_metadata` | `workflow_execution_set` | MetagenomeAnnotation / MetagenomeAssembly / MagsAnalysis runs; `was_informed_by` (array) → data_generation id |
| `nmdc_metadata` | `workflow_execution_set_mags_list` | Per-MAG GTDB-Tk taxonomy at all ranks, completeness, contamination, bin_quality, eukaryotic_evaluation_* |
| `nmdc_metadata` | `functional_annotation_agg` | Workflow-level KO/COG/Pfam counts (~27M rows for NEON); prefixes: `KEGG.ORTHOLOGY:Kxxxxx`, `COG:COGxxxx`, `PFAM:PFxxxxx` |
| `nmdc_results` | `gtdbtk_bacterial_summary` | Bacterial MAG GTDB-Tk detail (1,562 NEON rows); use mags_list for cross-domain |
| `nmdc_results` | `annotation_kegg_orthology` | Per-gene KO (1.8B rows — only for targeted hunts after Hypothesis 2/4 narrows candidates) |
| `nmdc_results` | `pfam_annotation_gff` | Per-gene Pfam (2.7B rows — same caveat) |
| `kbase_ke_pangenome` | `gtdb_species_clade` | 27,690 pangenome species; format `s__Genus_species` — must split on first underscore to extract genus for joining |
| `kbase_ke_pangenome` | `gene_cluster` | Pangenome gene cluster table with `is_core` flag |
| `kbase_ke_pangenome` | `eggnog_mapper_annotations` | Pangenome accessory KO/EC/COG assignments; join on `query_name` = `gene_cluster_id` |

### Sample design

| Habitat | Study | n biosamples | n MQ+HQ MAGs | n bacteria MAGs | n archaea MAGs |
|---|---|---|---|---|---|
| Soil | sty-11-34xj1150 | 6,489 | 1,177 | 1,137 | 40 |
| Surface water | sty-11-hht5sb92 | 234 | 110 | 110 | 0 |
| Benthic sediment | sty-11-pzmd0x14 | 736 | 322 | 322 | 0 |

Sample-level chemistry coverage (% of biosamples with non-null value):

| Variable | Soil | Water | Benthic |
|---|---|---|---|
| pH | 97% | 0% | 0% |
| Temp | 97% | 95% | 0% |
| Water content | 84% | 0% | 0% |
| Soil horizon | 100% | 0% | 0% |
| Organic carbon | 32% | 0% | 0% |
| Total nitrogen | 29% | 0% | 0% |
| C:N | 21% | 0% | 0% |
| Conductivity | 0% | 77% | 0% |
| Dissolved oxygen | 0% | 75% | 0% |

## Query Strategy

### Performance plan

- **Tier**: BERDL JupyterHub Spark SQL for all heavy joins. `functional_annotation_agg` (54M total rows; ~27M NEON-linked) needs `was_generated_by IN (...)` filter against the NEON workflow id list.
- **Hard limits to enforce**:
  - Never full-scan `annotation_kegg_orthology`, `pfam_annotation_gff` — both > 1B rows. Use only after Hypothesis 2 narrows to candidate KOs.
  - Always filter `workflow_execution_set` by `was_informed_by` against the NEON data_generation id list (a few thousand IDs).
  - `biosample_set` has 1,398 columns — always project explicit column list, never `SELECT *`.

### Step 1: Build the canonical NEON sample × workflow inventory (NB01)
- Resolve the 3 study IDs → biosamples (`biosample_set_associated_studies`) → data_generations (`data_generation_set_associated_studies`) → workflows (`workflow_execution_set` via `was_informed_by`).
- Emit `data/sample_inventory.tsv`: one row per biosample with habitat, sample-level chemistry columns, lat/lon, depth, collection_date.
- Emit `data/workflow_inventory.tsv`: one row per workflow with workflow_id, type, data_generation_id, biosample_id, habitat.
- Emit `data/mag_inventory.tsv`: one row per MAG with workflow_id, biosample_id, habitat, GTDB ranks, completeness, contamination, bin_quality.

### Step 2: Lineage novelty map (NB02)
- For MQ+HQ MAGs only: classify each MAG by lowest-defined GTDB rank (species / genus / family / order / class / phylum / domain / unclassified).
- Cross-tabulate by habitat and (for soil) by pH bin (e.g., < 4.5, 4.5–5.5, 5.5–6.5, > 6.5).
- Output: novelty heatmap (rank × habitat × pH bin), fraction-novel-vs-pH plot.

### Step 3: Sample-level functional profile (NB03)
- Build sample × KO count matrix from `functional_annotation_agg` (filter to `was_generated_by` IN NEON MetagenomeAnnotation workflow IDs).
- CLR-transform per sample. PCoA + PERMANOVA on habitat, then on pH/horizon within soil.
- Habitat-discriminating KOs via Welch t-test on CLR values, Benjamini–Hochberg FDR control.
- Enrichment of discriminating KOs against KEGG modules (KEGG pathway/module hierarchy is in `nmdc_arkin.kegg_ko_module` and `kegg_ko_pathway` — these are KEGG reference tables, not NEON sample data, so they're fair game).

### Step 4: Pangenome accessory contrast (NB04)
- Build NEON-MAG genus list (MQ+HQ only).
- Resolve overlapping genera via genus-level join to `kbase_ke_pangenome.gtdb_species_clade` (split `s__Genus_species` → genus).
- For each overlapping genus: get accessory KO set from pangenome (`eggnog_mapper_annotations` joined on `gene_cluster.gene_cluster_id`; `is_core = false`).
- Get the per-NEON-MAG KO content from the corresponding workflow's annotation (this is per-workflow, not per-MAG — need to either (a) restrict to samples where only one MAG of that genus is present, or (b) acknowledge the limitation and use sample-level signal as a proxy).
- Output: per-genus tally of KOs present in NEON, absent from cultured pangenome accessory; enrichment of those "field-only" KOs for environmental-process modules.

### Step 5: Synthesis (NB05)
- Combine into a single figure: 4-panel layout (novelty map, habitat KO PCoA, soil chemistry PERMANOVA, pangenome accessory contrast).
- Discovery candidate table: novel-lineage MAGs with field-only accessory KO content, ranked by combined novelty score.

### Known pitfalls

From earlier BERDL work and this session's probes:

1. **`workflow_execution_set.was_informed_by` is an array**, not a scalar — join with `array_contains(we.was_informed_by, dga.parent_id)`, not `=`.
2. **`biosample_set` has 1,398 columns** — always project explicit columns. Naive `SELECT *` is expensive and breaks downstream parsing.
3. **GTDB species format differs**: `mags_list.gtdbtk_species` is `Genus species`, KE pangenome `GTDB_species` is `s__Genus_species` (underscore separator). For genus extraction from pangenome: `split(replace(GTDB_species, 's__', ''), '_')[0]`.
4. **LQ MAGs dominate counts** (4,032 of 5,209 soil MAGs are LQ with avg completeness 37% / contamination 36%) — always filter to `bin_quality IN ('MQ','HQ')` before any analysis.
5. **77% of NEON soil MAGs have no genus assignment** — null-genus is the modal category. The "novelty" signal lives here; do not filter it out.
6. **`gtdbtk_bacterial_summary` is bacterial-only**: for cross-domain or archaeal counts, use `workflow_execution_set_mags_list.gtdbtk_domain`.
7. **No NEON coverage in `nmdc_arkin` _gold tables** (metaT/metaP/metabolomics/lipidomics/NOM all empty for these studies). Do not attempt multi-omics joins.
8. **Per-gene tables (`annotation_kegg_orthology`, `pfam_annotation_gff`) are billion-row** — only use after a candidate KO/Pfam list is established at the aggregate level.

## Success Criteria

1. Reproducible NB01 inventory: counts match the discovery probe (6,489 / 234 / 736 biosamples; 1,177 / 110 / 322 MQ+HQ MAGs).
2. A habitat × novelty-rank cross-tabulation with at least one statistically supported claim (Fisher exact or chi-square).
3. At least one significantly-enriched KEGG module per habitat (FDR < 0.05) for Hypothesis 2.
4. PERMANOVA result for soil pH effect on KO composition, with reported R² and p.
5. A pangenome-accessory comparison table with ≥ 10 overlapping genera and at least one quantitative claim about field-only KO content.

## Out of Scope

- External NEON portal data (climate stations, vegetation surveys, eddy covariance) — beyond NMDC re-host.
- AlphaEarth or other satellite/derived environmental layers.
- Per-MAG KO content (would require bin assignment, not available in `functional_annotation_agg`). Sample-level proxies used instead.
- Metatranscriptomics / metaproteomics / metabolomics — not in NMDC for these studies.
- Cross-domain (eukaryotic) MAG analysis — only 14 credible eukaryotic MAGs across all habitats, too sparse.

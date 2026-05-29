# Research Plan: DNA vs RNA Functional Response to Long-Term Soil Warming at Harvard Forest

## Research Question

After ~25 years of +5°C experimental soil warming at the Harvard Forest Barre Woods plot, does the functional **transcript pool** (metatranscriptome KO/Pfam composition) diverge from the **genome pool** (metagenome KO/Pfam composition) more strongly than expected from neutral community turnover, and which functional categories drive any divergence?

## Hypotheses

### H1 — Transcript-pool divergence > genome-pool divergence
- **H0**: Heated and control soils differ similarly in metagenome and metatranscriptome KO composition (β-diversity Heated-vs-Control roughly equal across DNA and RNA pools).
- **H1**: Metatranscriptome KO composition shows greater Heated-vs-Control β-diversity than metagenome KO composition (regulatory response precedes / outpaces community turnover).

### H2 — Carbon-degradation KOs are enriched in heated transcript pools
- **H0**: Carbon-degradation KOs (CAZymes, glycoside hydrolases, peptidases, TCA cycle, β-oxidation) are not preferentially enriched in heated metatranscriptomes vs controls.
- **H1**: Carbon-degradation KOs are enriched in heated metatranscriptomes (consistent with the Blanchard lab's published 5°C → accelerated respiration → soil-C loss finding).

### H3 — Horizon × warming interaction
- **H0**: Organic and mineral horizons respond identically to warming in their functional shifts.
- **H1**: Organic horizon shifts disproportionately in C-cycling KOs; mineral horizon shifts in N-cycling and mineral-associated metabolism KOs.

### Bonus — Metabolite class composition
- Categorical comparison of identified metabolites (ChEBI IDs) between heated and control. No quantification, just presence/identification frequency.

## Literature Context

The Harvard Forest Barre Woods experiment is one of the longest-running soil-warming manipulations in the world (DOE funded, started 2003). Published work by Blanchard and colleagues (Pold et al. 2017; Pold et al. 2020 and subsequent multi-omics analyses) shows:

- Sustained +5°C warming reduces total soil C (~30% loss in O horizon over a decade)
- Microbial respiration acclimates but does not fully compensate
- CAZyme expression and decomposition gene transcription respond to warming on shorter timescales than community turnover

Open questions to be addressed by this project:
- Does the DNA-level functional repertoire change at all, or is it stable?
- Which specific KO families drive any RNA-level divergence?
- Do organic and mineral horizons share the same response or are they decoupled?

A focused literature search will be performed in NB01.

## Data Sources

All data lives in the **`nmdc` tenant** of the BERDL Lakehouse (no `nmdc_arkin`).

| Database | Table | Use |
|----------|-------|-----|
| `nmdc_metadata` | `study_set` | Study description (Blanchard, Harvard Forest, sty-11-8ws97026) |
| `nmdc_metadata` | `biosample_set` | 42 biosamples; treatment labels via `name` (BW-C-* vs BW-H-*), `env_medium_has_raw_value` ("forest soil" vs "heat stressed soil"), `env_local_scale_has_raw_value` (organic vs mineral horizon) |
| `nmdc_metadata` | `biosample_set_associated_studies` | Sample ↔ study link; join on `parent_id` (= biosample id), filter `associated_studies = 'nmdc:sty-11-8ws97026'` |
| `nmdc_metadata` | `biosample_to_workflow_run` | Sample ↔ workflow run link |
| `nmdc_metadata` | `workflow_execution_set` | Workflow type (`nmdc:MetagenomeAnnotation`, `nmdc:MetatranscriptomeAnnotation`, etc.) |
| `nmdc_metadata` | `workflow_execution_set_has_metabolite_identifications` | 4,367 ChEBI metabolite IDs across 22 workflow runs |
| `nmdc_results` | `kraken2_classification_report` | Read-based community taxonomy (~278K rows for HF) |
| `nmdc_results` | `gtdbtk_bacterial_summary` | MAG taxonomy (298 MAGs for HF) |
| `nmdc_results` | `annotation_kegg_orthology` | KEGG KO calls — metagenome (~77M) and metatranscriptome (~15M) annotations distinguished by `workflow_run_id` → workflow type |
| `nmdc_results` | `pfam_annotation_gff` | Pfam domain hits on metagenome contigs (~113M rows) |
| `nmdc_results` | `annotation_statistics` | Per-assembly QC stats |

### Sample design (factorial)

| Factor | Levels | Encoded by |
|--------|--------|-----------|
| Treatment | Control / Heated | `name` prefix `BW-C-` / `BW-H-`; also `env_medium_has_raw_value` |
| Horizon | Organic (0–0.02 m) / Mineral (0.02–0.10 m) | `name` suffix `-O` / `-M`; also `env_local_scale_has_raw_value` |
| Incubation | Direct / Lab-incubated | `name` prefix `Inc-` |

- 14 control direct + 14 heated direct + 14 incubated (organic horizon only, 7 control + 7 heated)
- All samples collected 2017-05-24 from Petersham, MA
- Coordinates: 42.481016 °N, −72.178343 °W; elev. 302 m

## Query Strategy

### Performance plan
- **Tier**: BERDL JupyterHub Spark SQL (large `annotation_kegg_orthology` and `pfam_annotation_gff` tables)
- **Estimated complexity**: moderate — joins across 5 tables, 100M-row scans filtered by ~80 workflow_run_ids
- **Known pitfalls** (from `docs/pitfalls.md`):
  - `biosample_set_associated_studies` join key is `parent_id`, not `id`.
  - Avoid alias `n` against tables with column `n` (use longer aliases)
  - Cast string-typed numeric columns before comparison; abiotic features for HF are all zeros (skip).
  - All annotation tables must be filtered by `workflow_run_id` IN (...) — do not full-scan.

### Key queries

1. **Sample → workflow → workflow_type table**:
```sql
SELECT bw.biosample_id, bw.workflow_run_id, w.type as workflow_type
FROM nmdc_metadata.biosample_to_workflow_run bw
JOIN nmdc_metadata.workflow_execution_set w ON bw.workflow_run_id = w.id
WHERE bw.biosample_id IN (
    SELECT parent_id FROM nmdc_metadata.biosample_set_associated_studies
    WHERE associated_studies = 'nmdc:sty-11-8ws97026'
);
```

2. **KO counts per (sample, KO, source) — DNA**:
```sql
SELECT bs.biosample_id, ko.annotation_id as ko, COUNT(*) as gene_count
FROM nmdc_results.annotation_kegg_orthology ko
JOIN sample_workflow bs ON ko.workflow_run_id = bs.workflow_run_id
WHERE bs.workflow_type = 'nmdc:MetagenomeAnnotation'
GROUP BY bs.biosample_id, ko.annotation_id;
```

3. **KO counts per (sample, KO, source) — RNA**: same as #2 with `workflow_type = 'nmdc:MetatranscriptomeAnnotation'`.

4. **Pfam counts per (sample, Pfam, source)**: analogous on `pfam_annotation_gff`.

5. **Kraken2 read-taxonomy abundances per sample**: filter on `workflow_type = 'nmdc:ReadBasedTaxonomyAnalysis'`.

6. **Metabolite IDs per (sample, ChEBI)**: join `workflow_execution_set_has_metabolite_identifications.parent_id` ↔ `biosample_to_workflow_run.workflow_run_id`.

## Analysis Plan

### NB01 — Sample metadata, design, and literature
- Build the `samples × (treatment, horizon, incubation, plot, replicate)` design table from `biosample_set` parsing.
- Confirm one biosample per (treatment × horizon × plot) cell.
- Pull workflow-run IDs per sample per omics layer.
- **Brief literature recap** of Pold et al. and downstream Blanchard-lab papers on Barre Woods.
- **Outputs**: `data/sample_design.tsv`, `figures/01_design.png` (sample × omics-layer matrix).

### NB02 — Spark extraction (JupyterHub Spark)
- Pull DNA KO counts, RNA KO counts, DNA Pfam counts per sample.
- Pull kraken2 phylum/genus abundances per sample.
- Pull MAG GTDB taxonomy per sample.
- Pull metabolite ChEBI IDs per sample.
- **Outputs**: `data/ko_dna.tsv.gz`, `data/ko_rna.tsv.gz`, `data/pfam_dna.tsv.gz`, `data/kraken2_taxa.tsv.gz`, `data/gtdb_mags.tsv.gz`, `data/metabolite_ids.tsv.gz`.

### NB03 — Community composition (taxonomy)
- Phylum-level relative abundance per sample.
- PERMANOVA: Bray-Curtis ~ treatment × horizon (+ block as random).
- PCoA visualization.
- **Outputs**: `figures/03_taxa_pcoa.png`, `figures/03_phylum_heatmap.png`, statistics tables.

### NB04 — DNA vs RNA functional divergence (H1)
- Build per-sample KO and Pfam relative-abundance vectors for DNA and RNA pools.
- Compute Bray-Curtis Heated-vs-Control distance per pool.
- PERMANOVA on each pool; compare R² and pseudo-F.
- Procrustes test of DNA vs RNA configurations.
- **Outputs**: `figures/04_dna_vs_rna_pcoa.png`, `figures/04_betadiv_comparison.png`, statistics table.

### NB05 — Carbon-degradation enrichment (H2)
- Curated KO list for CAZymes, glycoside hydrolases, peptidases, TCA, β-oxidation, methanogenesis (build from KEGG BRITE — committed list in `data/c_cycling_kos.tsv`).
- Differential abundance Heated-vs-Control per pool (ALDEx2-style or DESeq2 on raw counts).
- Compare effect sizes between DNA and RNA.
- **Outputs**: `figures/05_c_cycling_volcano.png`, `data/c_cycling_da_results.tsv`.

### NB06 — Horizon × warming interaction (H3)
- Two-way design: Treatment × Horizon (direct samples only).
- KO/Pfam-level Treatment×Horizon interaction tests (FDR-controlled).
- Categorize interaction hits by KEGG module → C, N, S cycling.
- **Outputs**: `figures/06_interaction_heatmap.png`, `data/interaction_results.tsv`.

### NB07 — Metabolite categorical view (Bonus)
- Per-sample ChEBI sets; map ChEBI → ChEBI roles (compound classes) via OLS or local mapping.
- Frequency table of compound classes by treatment × horizon.
- **Outputs**: `figures/07_metabolite_classes.png`, `data/metabolite_class_summary.tsv`.

### NB08 — Synthesis figure
- Multi-panel summary: design + community β-diversity + DNA-vs-RNA divergence + C-cycling enrichment.
- **Output**: `figures/08_summary.png`.

## Expected Outcomes

- **If H1 supported**: identifies metatranscriptome as the more sensitive layer for detecting warming responses — guides future sampling design.
- **If H1 not supported**: argues that DNA-level community turnover is keeping pace with regulatory response after 25 years of warming.
- **If H2 supported**: confirms the published respiration-acceleration finding at the gene-expression level for the first multi-replicate dataset.
- **If H3 supported**: motivates separate horizon-aware warming-response models in C-cycling community models.

### Potential confounders
- **Assembly bias**: rarer organisms may not assemble; their KOs/Pfams will be missed in the contig-level annotation.
- **Compositional bias**: relative abundances are not absolute — interpret community shifts with care (use centred log-ratio when possible).
- **Replication imbalance**: only 28 samples have metagenome data (vs 39 metatranscriptome) — sample size limits power for H1 cross-pool comparison.
- **Single timepoint**: 2017-05-24 only — cannot detect seasonal effects.
- **Heated soil ENVO term `[ENVO:00005781]`** is "heat stressed soil" — applies treatment label uniformly; not a measurement.

## Revision History

- **v1** (2026-05-07): Initial plan. Constraint: nmdc tenant tables only (no nmdc_arkin). Trades quantitative chemistry/proteomics for fully-tabular DNA/RNA functional comparison.

## Authors

- Chris Mungall, LBNL, ORCID 0000-0002-6601-2165

# Research Plan: Metabolic Self-Sufficiency Index — Predicting Cultivability from Pangenome Pathway Completeness

## Research Question

Can per-genome metabolic self-sufficiency, measured as the completeness of GapMind-annotated amino acid biosynthesis and carbon utilization pathways, distinguish cultured isolates from MAGs at pangenome scale — and can the resulting model identify uncultured MAGs that are *isolate-like* (and therefore plausible cultivation targets) above and beyond what taxonomy and genome quality already predict?

## Hypothesis

- **H1 (primary)**: At matched CheckM quality (≥95% complete, ≤5% contamination), MAGs have significantly lower mean GapMind pathway completeness than isolates within the same GTDB family, on both amino acid biosynthesis and carbon utilization pathway sets. Effect size is large for carbon utilization and modest for amino acid biosynthesis. (Pre-registered direction; supported by Phase A feasibility: 28pp carbon gap, 9pp aa gap across 217K HQ genomes.)
- **H2**: A logistic / gradient-boosted model trained on the 80-pathway binary completeness vector + genome-quality covariates can predict isolate vs MAG with cross-family held-out AUC ≥ 0.75, materially exceeding a taxonomy-only or CheckM-only baseline.
- **H3**: Within the held-out uncultured (MAG) population, the model assigns isolate-like scores to a subset of genomes whose family membership and environmental provenance suggest tractable cultivation — e.g., overrepresented in soil/subsurface niches and underrepresented in known auxotroph-rich lineages (CPR, DPANN, *Ca.* Patescibacteria).
- **H0**: Pathway completeness adds no predictive value beyond `checkm_completeness`, `genome_size`, and family-level taxonomic identity.

## Literature Context

- **Lewis (2020), Lewis & Ettema (2021)** — the cultivation gap is the dominant constraint on functional microbiology of environmental samples. Targeted cultivation campaigns (e.g., Mukherjee 2022 *Patescibacteria*, Cross 2019) rely on hand-curated metabolic predictions.
- **Beaver & Neufeld (2024)** — self-sufficiency framework for explaining cultivability differences; arguments are qualitative and per-lineage.
- **Mitzscherling (2023), Bagnoud (2016)** — subsurface cultivation bias examples; cultured Bacillota_B in clay have the *opposite* redox-marker signature from the dominant native community (sulfate-reducing vs iron-reducing).
- **BERIL `clay_confined_subsurface`** — established that cultured genomes in deep clay are 35% larger and metabolically distinct from soil baseline (CheckM-controlled). Anchors the within-BERDL ground truth.
- **BERIL `oak_ridge_cultivation_gap`** — first quantitative cohort-level cultured-vs-MAG gene-content comparison at a single site.
- **GapMind (Price 2022)** — the underlying pathway scoring tool; binary-thresholded completeness has been used qualitatively but never as a feature set in a cultivability classifier.

What's open: **no pangenome-scale cultivability classifier exists**. Existing predictions are per-organism, lineage-specific, or qualitative. BERDL's 293K-genome GapMind table makes a generalized prediction possible for the first time.

## Query Strategy

### Tables Required

| Table | Purpose | Estimated rows | Filter strategy |
|---|---|---:|---|
| `kbase_ke_pangenome.gapmind_pathways` | 80-pathway binary completeness per genome | 305M | `sequence_scope='all'`, `MAX(score_simplified) GROUP BY genome_id, pathway` |
| `kbase_ke_pangenome.gtdb_metadata` | Cultivation label + CheckM + genome stats | 293K | `checkm_completeness ≥ 95 AND checkm_contamination ≤ 5`; strip `RS_`/`GB_` prefix |
| `kbase_ke_pangenome.gtdb_taxonomy_r214v1` | Family / phylum for stratified holdout | 293K | join on `genome_id` (not `gtdb_taxonomy_id`) |
| `kbase_ke_pangenome.ncbi_env` | Environmental provenance for H3 candidate ranking | sparse | species-level majority vote |

### Key Queries

1. **Per-genome pathway-completeness matrix** (~250K rows × 80 columns):

```sql
WITH gp AS (
  SELECT genome_id, pathway,
         MAX(CAST(score_simplified AS DOUBLE)) AS complete
  FROM kbase_ke_pangenome.gapmind_pathways
  WHERE sequence_scope = 'all'
  GROUP BY genome_id, pathway
)
SELECT genome_id, pathway, complete FROM gp
```
Pivot to wide form per genome (80 pathway columns) in Pandas after import.

2. **Labeled cohort** (apply CheckM quality gate, strip prefix, attach family):

```sql
SELECT
  REGEXP_REPLACE(m.accession, '^(RS_|GB_)', '') AS genome_id,
  CASE WHEN m.ncbi_genome_category = 'none' THEN 1 ELSE 0 END AS is_isolate,
  CAST(m.checkm_completeness AS DOUBLE) AS checkm_comp,
  CAST(m.checkm_contamination AS DOUBLE) AS checkm_contam,
  CAST(m.genome_size AS DOUBLE) AS genome_size,
  CAST(m.gc_percentage AS DOUBLE) AS gc_pct,
  CAST(m.contig_count AS INT) AS contig_count,
  CAST(m.n50_contigs AS INT) AS n50,
  t.family, t.phylum
FROM kbase_ke_pangenome.gtdb_metadata m
JOIN kbase_ke_pangenome.gtdb_taxonomy_r214v1 t
  ON REGEXP_REPLACE(m.accession, '^(RS_|GB_)', '') = REGEXP_REPLACE(t.genome_id, '^(RS_|GB_)', '')
WHERE CAST(m.checkm_completeness AS DOUBLE) >= 95
  AND CAST(m.checkm_contamination AS DOUBLE) <= 5
  AND m.ncbi_genome_category IN ('none', 'derived from metagenome', 'derived from environmental sample', 'derived from single cell')
```

3. **Family-stratified holdout assignment** — for each of the 203 families with ≥5 of both labels, assign 80% to train / 20% to held-out test. Drop families with only one label from the training set used to fit family-fixed-effect logistic baselines.

### Performance Plan

- **Tier**: JupyterHub Spark SQL on-cluster for the GapMind aggregation (305M-row scan, must run in Spark — `toPandas` only the pivoted ~250K × 81 matrix).
- **Estimated complexity**: moderate. The single expensive operation is the 305M-row groupby; the rest is in-memory (sklearn / xgboost) at the 250K-row scale.
- **Known pitfalls** (already verified in `00_label_feasibility.ipynb`):
  - ID format fracture: `gtdb_metadata.accession` has `RS_`/`GB_` prefix, `gapmind_pathways.genome_id` does not — strip via `REGEXP_REPLACE`.
  - GapMind multi-row per (genome, pathway): `MAX(score_simplified)` per `[pgp_pangenome_ecology]` pitfall.
  - `--` in species clade IDs: not a problem in direct Spark, but if any REST API fallback is needed, filter locally.
  - Taxonomy join must be on `genome_id`, NOT `gtdb_taxonomy_id` (different depths).

## Analysis Plan

### Notebook 01: Feature Matrix Construction
- **Goal**: produce `data/features.parquet` = (~250K HQ genomes × 80 pathway-completeness binaries + 5 genome-quality covariates + family/phylum labels + is_isolate target).
- **Expected output**: parquet table, plus `data/cohort_summary.tsv` (n by label × phylum) and `data/family_overlap.tsv` (n iso / n mag per family).

### Notebook 02: Univariate & Family-Stratified Signal
- **Goal**: test H1. For each of the 80 pathways, compare isolate-vs-MAG completeness with (a) pooled OR + Fisher's exact and (b) within-family conditional logistic regression. Apply BH-FDR.
- **Expected output**: `data/per_pathway_or.tsv`, figure `figures/per_pathway_forest.png` (top 20 most-discriminative pathways), `figures/aa_vs_carbon_summary.png` (pooled and family-stratified completeness rates).

### Notebook 03: Predictive Model
- **Goal**: test H2. Train (a) logistic regression with L1 and (b) gradient-boosted decision trees (XGBoost / LightGBM) on the 80-pathway matrix + 5 covariates. Cross-validate with **leave-one-family-out** over the 203 families that have both labels. Compare against three baselines:
  1. Family-only (categorical fixed effect).
  2. CheckM-only.
  3. CheckM + genome_size + gc.
- **Expected output**: `data/cv_predictions.tsv` (per-genome predicted P(isolate)), `figures/roc_curves.png`, `figures/feature_importance.png`. Report held-out AUC, average precision, calibration (Brier).

### Notebook 04: H3 Candidate Ranking
- **Goal**: apply the trained model to all HQ MAGs (~41K), then **filter** to:
  - Family has any isolate representation (so the model has seen the family's typical isolate signature).
  - Predicted P(isolate) ≥ 0.5 (configurable; sensitivity analysis at 0.3, 0.7).
  - Phylum not in known auxotroph-heavy set (CPR, DPANN, Patescibacteria) unless an isolate from that lineage exists.
- **Expected output**: `data/cultivability_candidates.tsv` (ranked, with family, phylum, environmental provenance, predicted probability, top-3 pathway-feature contributions per LIME or SHAP), `figures/candidate_phyla.png` (phylum distribution of top 500 candidates).

### Notebook 05: Anchored Validation
- **Goal**: validate against two completed BERDL projects.
  - `clay_confined_subsurface`: do the 8 Mont Terri cultured deep-clay Bacillota_B genomes score higher on the cultivability index than the published Bagnoud Mont Terri MAGs of the same family?
  - `oak_ridge_cultivation_gap`: do model scores recapitulate the cultured-vs-MAG per-marker gap that project documented?
- **Expected output**: `figures/clay_validation.png`, `figures/oak_ridge_validation.png`, narrative text in REPORT.md.

## Expected Outcomes

- **If H1 + H2 supported**: a generalizable cultivability predictor with held-out AUC ≥ 0.75; first quantitative cultivability index from pangenome-scale GapMind data; mechanistic interpretation through pathway-level feature importance (which biosynthesis / utilization capabilities most distinguish cultured organisms).
- **If H1 supported but H2 fails**: the signal is real but not generalizable across families — likely because cultivability is strongly lineage-specific. We report effect sizes and present the family-conditional version of the index.
- **If H0 not rejected**: pathway completeness is just a proxy for assembly completeness / taxonomy. Result is informative null; methodology contributes the CheckM-controlled cohort design and the family-stratified training protocol.
- **Confounders to control or report**: (i) `checkm_completeness` residual signal beyond the 95% threshold; (ii) phylum imbalance (Pseudomonadota dominate isolates, Bacteroidota dominate MAGs); (iii) MAG-completeness misestimation by CheckM on lineages with reduced single-copy marker sets (CPR/DPANN); (iv) GapMind annotation gaps for non-canonical pathways (e.g., novel carbon utilization in extremophiles).

## Revision History

- **v1** (2026-05-26): Initial plan after Phase A feasibility (`00_label_feasibility.ipynb`). Pivot from the superseded `pangenome_selective_landscape` framing — see `docs/research_ideas.md` entry note.

## Authors

- Justin Reese — LBL — ORCID: 0000-0002-2170-2250

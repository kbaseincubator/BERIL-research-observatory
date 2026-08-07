# Research Plan — metagenomic_environment_prediction

**Question:** Does per-Mb metal-gene KO density in individual bacterial MAGs predict the metal bioavailability conditions at the MAG's sampling location?

**Status:** NB00 and NB01 redesigned to use SPIRE download endpoints for all env bacterial MAGs. NB01 pending re-execution with download path. NB02–NB04 pending.

---

## Motivation

The primary result (P1, `comprehensive_metal_ecology`) establishes a genus-level PGLS association between metal-gene density and niche breadth. That analysis averages over all sequences assigned to a genus. This project tests whether the same signal exists at the level of individual assembled genomes sampled from real environments, and whether the metal conditions at each genome's sampling site can be predicted from its gene content.

This is a harder test: within-genus genome-level variance is large, and environmental metal conditions are only indirectly related to Levins' B. A positive result would substantially strengthen the ecological interpretation.

---

## Hypotheses

### H1 — Predictive signal exists
**MAG genomic metal-gene density (M1: `ko_per_mb_primary`) beats a mean-predictor baseline (B0) when predicting local CSU metal mobility fractions, on at least 3 of 5 spatial folds for ≥2 of the 6 available targets (Cu, As, Cd, Cr, Hg, Pb).**

Rationale: If no predictive signal exists at this resolution, the P1 association may reflect genus-level phylogenetic patterning without ecological predictive power.

### H2 — Metal features outperform non-metal features
**M1 (metal density features) achieves lower mean CV RMSE than M2 (SoilGrids + climate features) for ≥2 of 5 metal targets.**

Rationale: Non-metal env features (pH, climate) co-vary with metal availability and could drive apparent metal prediction without any metal-gene signal.

### H3 — Non-metal features do not consistently add value
**M3 (all features) does not outperform M1 on ≥3/5 folds for any target (or if it does, SHAP shows <25% of importance from metal features).**

This is intentionally falsifiable — we expect metal features to dominate if H1 and H2 hold.

### H4 — Geographic transfer
**The M1 model trained on non-Australian MAGs achieves holdout RMSE ≤ 1.25 × the in-distribution block CV RMSE on Australian MAGs.**

The 1.25 threshold is pre-specified. A ratio >1.25 is evidence of geographic overfitting.

### H5 — PGLS directional consistency
**Genus-aggregated MAG density shows a directionally consistent PGLS β when regressed against Levins' B (same sign as P1 β = −0.021).**

A sign flip would be evidence that MAG-level and genus-level signals are discordant.

---

## MGnify Extension (Exploratory)

All analyses in this section are exploratory. MGnify MAGs provide a second dataset for testing replicability.

### New hypotheses (H5–H8, exploratory)

- **H5 (exploratory):** MGnify M3 (KO + metal) outperforms B0 (baseline RMSE) — positive control check
- **H6 (exploratory):** MGnify M3 outperforms M2 (metal-only) — KO features add explanatory value
- **H7 (exploratory):** MGnify M3 generalises across geographic hold-out sets (RMSE < B0 + 0.01)
- **H8 (exploratory):** SPIRE and MGnify genus-level PGLS β coefficients are positively correlated (Spearman ρ > 0.3)
  - Rationale: same biology (metal-gene associations); expect consistent direction even if different effect sizes

### MGnify pipeline timeline

- **Scaffolded 2026-07-09:** NB01b–NB05 created with full documentation
- **Pending execution:** all notebooks awaiting runtime environment with Spark access
- **Data sources:**
  - Coordinates/taxonomy: `final_mags_geospatial_traits.csv` (from `microbeatlas_metal_ecology/data/`)
  - Mobility metadata: `kescience_mgnify.genome` Spark table (completeness ≥70%, contamination ≤10%, domain='Bacteria')
  - KO annotations: `kescience_mgnify.gene_eggnog` Spark table (extract K##### patterns from KEGG_ko column)
  - Biome filter: "Soil", "Rhizosphere", or "Marine Sediment" in `biome_name`

---

## Pre-specified decisions

### Data path selection (NB00 / NB01)
- **Primary path (implemented 2026-07-08):** SPIRE download endpoints for ALL env bacterial MAGs:
  - `GET https://spire.embl.de/download_eggnog/{SAMPLE_ID}` — gzip eggnog TSV per sample (~36 MB)
  - `GET https://spire.embl.de/download_file/{MAG_ID}` — gzip FASTA per MAG (contig names, ~422 KB)
  - Scope: all MAGs in `refdata.spire.mag_coordinates` passing env/quality filters (NOT filtered to the 6,270 in the internal table)
  - Files cached to `data/spire_cache/eggnog/` and `data/spire_cache/mag_contigs/`; re-runs are fast
- The internal `arkinlab.spire.eggnog_annotations_spire` table (6,270 MAGs) was the initial path but is now superseded by the download approach which covers all ~1.16M SPIRE MAGs.

### MAG quality filter
Completeness ≥70%, contamination ≤10%, Bacteria domain, non-host ENVO. No adjustment after seeing density distributions.

### Spatial fold assignment
k-means k=5 on lat/lon. Same algorithm and seed (`RANDOM_STATE=42`) across all models.

### Primary target
`PF1_Cu` (copper mobility fraction). Secondary: As, Cd, Cr, Hg, Pb (6 targets total; Zn and Ni not in the CSU grid). H1/H2/H3 require support for ≥2 of 6 targets.

### Geographic holdout region
Australia: lat (−45°, −10°), lon (110°, 155°). Not adjusted after seeing MAG coverage.

### H4 pass threshold
1.25 × CV RMSE. Pre-specified; not adjusted if near-miss.

### PGLS model (NB04)
`levins_b_z ~ ko_per_mb_primary_z + log_PF1_Cu_z`. Exactly two predictors; same PGLS implementation as P1.

---

## Negative results

A negative result on H1 (M1 does not beat B0) is interpretable: it would indicate that the genus-level P1 signal does not extend to MAG-level prediction, which is scientifically informative. All hypotheses will be reported as tested regardless of outcome.

---

## Scope boundaries

This project does **not**:
- Update or revise P1 results.
- Replace the primary genus-level PGLS with MAG-level analyses.
- Extend to eukaryotic MAGs.
- Attempt causal inference beyond the correlational framework of P1.

---

## Timeline

- **2026-07-09:** SPIRE pipeline complete (NB00–NB04 executed).
- **2026-07-09:** MGnify extension scaffolded (NB01b–NB05 created; exploratory hypotheses H5–H8 defined; pending execution).

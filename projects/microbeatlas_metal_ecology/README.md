# Metal Resistance Ecology: Phylogenetic Conservation vs. Environmental Selection

## Research Question

Do metal-resistance functions in the global microbiome reflect phylogenetic constraint (conserved
in lineages) or environmental selection (enriched in metal-contaminated habitats)? We test this
using Pagel's λ to quantify phylogenetic signal, characterise whether metal-resistant lineages are
ecological generalists or specialists in a 464K-sample atlas, and use nitrification as a
metabolic-specialist positive control.

## Status

Analysis — report drafted, awaiting `/berdl-review` and `/submit`. All Priority 0 items resolved (2026-07-02). **Central finding:** Metal homeostasis gene density (Tier 2 per Mb: β=−0.009, p=0.011) predicts ecological specialization; resistance gene density (Tier 1 per Mb: p=0.256) does not. Total 94-KO per Mb: β=−0.022, p=4×10⁻⁷ (n=997). Replicates within Gammaproteobacteria (p=0.0008), Bacilli (p=0.004), Alphaproteobacteria (p=0.016). OTU–GeoROC Tier 1 complete: 3,050 samples, 2,773 Bonferroni-significant OTU–metal pairs. Literature context updated with genome streamlining theory (Giovannoni 2014), Burkholderiales metal ecology (Li et al. 2025), and OTU-metal soil associations (Dai et al. 2023).

**Completed (2026-07-01 sessions 1–3):**
- ✅ NB01 re-run with 94-KO list (`mrg_ko_final.csv`); PGLS on n=1,000 genera
- ✅ Robustness R1–R4 and sensitivity S1–S4 re-run with 94-KO data
- ✅ S1 leave-one-metal-out: 11/12 metals positive (p<0.05); cadmium exception (p=0.316) — genomic island interpretation added
- ✅ AMRFinderPlus discrepancy traced and resolved (see REPORT.md Finding 3)
- ✅ TCDB cross-reference: 94-KO list covers ~52% of metal transporter TCDB families (12/23)
- ✅ RB-TnSeq FitnessBrowser validation: 94-KO genes more depleted under metal stress (Keio p=0.013, Shewanella MR-1 p=0.031)
- ✅ Annotation-quality discriminant controls: Pfam (p=0.906) → AMRFinderPlus (p=0.540) → InterPro (p=0.010) → 94-KO (p=0.013)
- ✅ Tier-stratified PGLS (94-KO, n=1,000): Tier 1 resistance p=0.016; Tier 2 homeostasis p=0.050
- ✅ **Metabolism discriminant PGLS (19-KO, Spark):** β=+0.0164 p=0.0012 on n=1,000 — signal not resistance-specific; 7,976 genera covered
- ✅ **Genome-size controlled discriminant PGLS (2026-07-01):** Both signals attenuate on n=523 — stale p=3.5×10⁻⁴ entry corrected in REPORT.md
- ✅ **Normalized PGLS — GTDB genome size (2026-07-01):** 997/1,000 genera covered via gtdb_metadata; per-Mb + per-1k-gene predictors negative (β=−0.022, p=4×10⁻⁷); finding reversed from raw; data: `data/pgls_results_normalized.csv`, `data/genus_genome_size_gtdb.csv`
- ✅ Figure 5 (robustness panel) regenerated
- ✅ GapMind carbon λ added to REPORT.md Finding 2
- ✅ Metal × carbon interaction PGLS: null interaction (p=0.414); additive effects only
- ✅ MCMCglmm Poisson model (nitt=50,000 complete): ESS=147.8, posterior mean=+0.039, pMCMC=0.013
- ✅ **Tier asymmetry** (2026-07-02): Tier 2 homeostasis per Mb p=0.011 (negative); Tier 1 resistance per Mb p=0.256 (null)
- ✅ **Taxonomic replication** (2026-07-02): per-Mb negative replicates within Gammaproteobacteria/Bacilli/Alphaproteobacteria; Burkholderiales strongest order (p=0.0002)
- ✅ **Narrative reframe** (2026-07-02): REPORT Key Findings, Biological Interpretation, Novel Contribution updated to lead with homeostasis density finding
- ✅ Antibiotic resistance λ negative control: λ=0.121 (n=799) vs. metal type diversity λ=0.943
- ✅ Pagel's λ updated with 94-KO values: metal type diversity λ=0.943; clusters λ=0.497; core fraction λ=0.291
- ✅ ENIGMA Track B read coverage: 32.2% mean (10/133 samples <10%)
- ✅ Aquatic sub-type PGLS: marine fraction β=−0.068 (p=0.004)
- ✅ Finding 3 title reframed: "metal-interacting gene diversity, not specific to resistance function"
- ✅ 19-KO count corrected (was 18); K04569 CCS added to REPORT enzyme list
- ✅ Post-hoc/exploratory labels audited throughout REPORT.md

**Open before submission:**
- ✅ OTU–GeoROC MNAR Tier 1 complete (2026-07-02): 3,050 samples, 2,000 OTUs, 2,773 Bonferroni-sig OTU–metal pairs (`data/otu_georoc_tier1_6metal.csv`); Tier 2–3 deferred to revision
- NB08d (db-RDA) excluded — circular predictor bug requires Spark re-execution
- Soil microcosm experimental design drafted (Future Direction 10 in REPORT.md)

**Completed (2026-07-02 session 4 — MGnify MAG validation):**
- ✅ **NB12 MGnify MAG PGLS** (576 genera, biome_H × 94-KO/Mb): β=+0.051, p=5.9×10⁻¹⁹ — sign opposite to primary; confirms positive cross-biome cosmopolitanism vs. negative within-habitat specialization
- ✅ **Diagnostic tests A/B/C** — confirmed discordance driven by niche metric (Levins' B vs. biome_H), not annotation source; Test B null (Levins' B × MGnify KO = p=0.404)
- ✅ **Expanded MGnify biome subsets**: ENV_all β=+0.077 p=1.3×10⁻¹³; MARINE β=+0.118 p=2.7×10⁻¹⁰; GUT_ctrl β=+0.049 p=3.6×10⁻⁵ (biome_H universally positive)
- ✅ **NEON validation attempted** (kbase.nmdc_neon) — abandoned: 80% placeholder GTDB genus names, only 34–37 genera after tree pruning
- ✅ **Amplicon dataset scan** across all ~150 accessible Spark namespaces — no suitable dataset; `netl_pw_dna` access-restricted (NETL tenant pending access request)
- ✅ **REPORT.md updated** with MGnify validation subsection, diagnostic tests, biome subsets, and null validation attempts

**Completed (2026-07-02 session 5 — Soil replication + notebook reorganization):**
- ✅ **NB14 Soil-restricted PGLS** (603 genera): Total 94-KO/Mb β=−0.023, p=0.0002 — signal replicates within soil alone; not driven by soil vs. non-soil contrasts; Tier 2 specificity does not replicate in soil-only subset
- ✅ **NB13 Australian Microbiome** (482 genera): Levins' B × 94-KO/Mb — null result (β=−0.0023, p=0.667); likely underpowered (narrow geographic range, fewer ecological zones)
- ✅ **NB15 NETL replication stub** created — Spark schema exploration for `netl_pw_dna.*` tables; pending JupyterHub execution
- ✅ **replication.ipynb** rewritten as clean hub with status table for all replication attempts
- ✅ **REPORT.md** updated with soil-only PGLS results, AusMicrobiome null, NETL status, new data/notebook table entries

## Overview

Uses `arkinlab_microbeatlas` (98,919 OTUs, 464K samples) linked to `kbase_ke_pangenome`
(bakta_amr, GTDB taxonomy) via genus-level taxonomy matching. Analytical modules:

**Core (Ch.01–06)**
1. **Metal AMR extraction** (NB01, JupyterHub) — species-level metal resistance gene counts from AMRFinderPlus
2. **Niche breadth** (NB02, JupyterHub) — Levins' B from 260M OTU × sample observations
3. **Taxonomy bridge** (NB03, local) — OTU genus → GTDB species → metal AMR proxy
4. **Pagel's λ** (NB04, local) — phylogenetic signal of metal AMR per metal type
5. **Environmental selection test** (NB05, local) — niche breadth vs metal AMR, PGLS
6. **Figures** (NB06, local) — summary visualisations

**Extensions (Ch.07–11; consolidated 2026-06-30)**
7. **Environmental metadata PGLS** (NB07, local) — pH, temperature, organic carbon as PGLS covariates
8. **COG-metal functional genomics** (NB08a–d) — Spearman, BH-FDR, copper-specific, db-RDA across ~51K soil samples
9. **OTU-level GeoROC associations** (NB09a–b) — partial Spearman (CLR, 9,999 perms) between OTU abundance and measured soil metal concentrations
10. **Global MAG biogeography** (NB10a–c) — 260K MGnify MAGs; hotspot identification (Fisher's exact, 11 significant grid cells); biome stratification
11. **Biome-stratified Pagel's λ** (NB10d) — within-biome phylogenetic signal; all biomes λ=0.83–0.90
12. **Gene × biome enrichment** (NB10e) — seven focal genes (merA, arsC, silA, …) × five biomes; Fisher's exact + BH-FDR
13. **AlphaEarth embedding synthesis** (NB11c) — PERMANOVA of NCBI reference genome embeddings by hotspot label; PC12 dose-response

## Quick Links

- [Research Plan](RESEARCH_PLAN.md)
- [Report](REPORT.md)

**Core notebooks**
- [NB01 — Metal AMR extraction](notebooks/01_metal_amr_species.ipynb) *(JupyterHub)*
- [NB02 — Niche breadth](notebooks/02_niche_breadth.ipynb) *(JupyterHub)*
- [NB03 — Taxonomy bridge](notebooks/03_taxonomy_bridge.ipynb)
- [NB04 — Pagel's λ](notebooks/04_pagel_lambda.ipynb)
- [NB05 — PGLS regression](notebooks/05_pgls_regression.ipynb)
- [NB06 — Synthesis figures](notebooks/06_synthesis_figures.ipynb)
- [Supplementary — Clade-specific sensitivity](notebooks/clade_specific_sensitivity.ipynb) *(standalone; run after NB04)*

**Extension notebooks**
- [NB07 — Environmental metadata PGLS](notebooks/07_env_metadata_pgls.ipynb)
- [NB08a — COG-metal Spearman](notebooks/08a_spearman_cog_metal.ipynb)
- [NB08b — BH-FDR associations](notebooks/08b_fdr_associations.ipynb)
- [NB08c — Copper-specific analysis](notebooks/08c_copper_specific.ipynb)
- [NB08d — db-RDA PGLS](notebooks/08d_dbrda_pgls.ipynb) *(PENDING re-execution on Spark)*
- [NB09a — OTU × GeoROC associations](notebooks/09a_otu_georoc_associations.ipynb)
- [NB09b — OTU sensitivity](notebooks/09b_otu_sensitivity.ipynb)
- [NB10a — Global MAG distribution](notebooks/10a_global_mag_distribution.ipynb)
- [NB10b — Spatial hotspot analysis](notebooks/10b_spatial_analysis.ipynb)
- [NB10c — MAG figures](notebooks/10c_mag_figures.ipynb)
- [NB10d — Pagel's λ by biome](notebooks/10d_pagels_biome.ipynb)
- [NB10e — Gene × biome enrichment](notebooks/10e_gene_level_biome.ipynb)
- [NB11c — AlphaEarth embedding synthesis](notebooks/11c_alphaearth_metal_synthesis.ipynb)

**Replication notebooks**
- [Replication hub](notebooks/replication.ipynb) — status table for all replication attempts
- [NB12 — MGnify MAG validation](notebooks/12_mgnify_mag_validation.ipynb) *(complete; biome_H positive)*
- [NB13 — Australian Microbiome](notebooks/13_australian_microbiome_replication.ipynb) *(null result)*
- [NB14 — Soil-restricted primary](notebooks/14_soil_primary_replication.ipynb) *(replicates; β=−0.023, p=0.0002)*
- [NB15 — NETL produced waters](notebooks/15_netl_replication.ipynb) *(pending JupyterHub)*

**Reference**
- [R session info](sessionInfo_r.txt)
- [ENIGMA predictions](ENIGMA_PREDICTIONS.md)
- [Metal resistance table](METAL_RESISTANCE_TABLE.md)
- [Analysis notes](notes/)

## Data Sources

| Database | Tables | Access |
|---|---|---|
| `arkinlab_microbeatlas` | `otu_metadata`, `otu_counts_long`, `sample_metadata` | REST API + CLI Spark |
| `kbase_ke_pangenome` | `bakta_amr`, `gene_cluster`, `gtdb_species_clade` | JupyterHub Spark only |

## Reproduction

**Prerequisites**: JupyterHub Spark access for NB01–NB02; R 4.5.2 with `ape` and `phytools`
for NB04–NB05 (see `sessionInfo_r.txt`); Python ≥ 3.10 with packages in `requirements.txt`.

Run steps in this order:

**Core pipeline (Ch.01–06)**

| Step | Where | Command / Action | Output |
|---|---|---|---|
| 1. Metal AMR extraction | JupyterHub | Open and run `notebooks/01_metal_amr_species.ipynb` (uses `data/mrg_ko_final.csv` — 94-KO tiered list) | `data/species_metal_amr.csv`, `data/gtdb_genus_taxonomy.csv` |
| 2. Niche breadth | JupyterHub | Open and run `notebooks/02_niche_breadth.ipynb` | `data/genus_niche_breadth.csv` |
| 3. Taxonomy bridge | Local | `jupyter nbconvert --to notebook --execute notebooks/03_taxonomy_bridge.ipynb` | `data/species_traits_for_pgls.csv` |
| 4. Pagel's λ | Local (R) | `Rscript scripts/h1_pagel_lambda_survivor.R` | `data/pagel_lambda_results.csv` |
| 5. PGLS regression | Local | `jupyter nbconvert --to notebook --execute notebooks/05_pgls_regression.ipynb` | `data/pgls_results.csv` |
| 6. Synthesis figures | Local | `jupyter nbconvert --to notebook --execute notebooks/06_synthesis_figures.ipynb` | `figures/fig_*` |
| 7. ENIGMA validation | Local | `python scripts/enigma_validation.py` | `figures/fig_enigma_validation_3panel.png` |

**Extension notebooks (Ch.07–11; all local unless noted)**

| Step | Notebook | Command / Action | Output |
|---|---|---|---|
| 8. Env metadata PGLS | NB07 | `jupyter nbconvert --execute notebooks/07_env_metadata_pgls.ipynb` | `data/env_pgls_results.csv` |
| 9. COG-metal Spearman | NB08a–c | `jupyter nbconvert --execute notebooks/08a_spearman_cog_metal.ipynb` etc. | `data/cog_metal_spearman.csv`, figures |
| 10. db-RDA (PENDING) | NB08d | Requires Spark cluster; fix `project_accession` SELECT + `sample_limit≥2000` | `data/dbrda_results.csv` |
| 11. OTU-GeoROC | NB09a–b | `jupyter nbconvert --execute notebooks/09a_otu_georoc_associations.ipynb` | `data/otu_georoc_*.csv`, figures |
| 12. MAG distribution | NB10a | `jupyter nbconvert --execute notebooks/10a_global_mag_distribution.ipynb` | `figures/nb10a_global_mag_distribution.png` |
| 13. Spatial hotspots | NB10b | `jupyter nbconvert --execute notebooks/10b_spatial_analysis.ipynb` | `data/hotspots_5grid.csv`, figures |
| 14. MAG figures | NB10c | `jupyter nbconvert --execute notebooks/10c_mag_figures.ipynb` | `figures/nb10c_*.png` |
| 15. Pagel by biome | NB10d | `jupyter nbconvert --execute notebooks/10d_pagels_biome.ipynb` (calls R via subprocess) | `data/pagel_lambda_by_biome.csv`, `figures/nb04d_*.png` |
| 16. Gene × biome | NB10e | `jupyter nbconvert --execute notebooks/10e_gene_level_biome.ipynb` | `data/gene_biome_enrichment.csv`, `figures/nb04e_*.png` |
| 17. AlphaEarth synthesis | NB11c | `jupyter nbconvert --execute notebooks/11c_alphaearth_metal_synthesis.ipynb` | `data/alphaearth_hotspot_comparison.csv`, `figures/nb11c_*.png` |

**Notes**:
- NB01–02 require `kbase_ke_pangenome` / `arkinlab_microbeatlas` access (JupyterHub only). Pre-computed outputs in `data/` allow local re-running from step 3 onward.
- NB04 calls R via `subprocess`; the notebook handles pre/post-processing.
- NB08d is PENDING: the circular-predictor bug (random project IDs) has been fixed in Cell 9 but the corrected version requires Spark cluster re-execution.
- NB10d calls `scripts/pagel_lambda_by_biome.R` (new wrapper, distinct from NB04's R script).
- Large files (`dir6_georoc_global_pca.csv` at 594 MB, some figures >100 MB) are excluded from git tracking. Zenodo DOI pending.
- `clade_specific_sensitivity.ipynb` is a standalone supplementary analysis (clade-specific Pagel's λ); run independently after step 4.

**Large files**: `data/dir6_georoc_global_pca.csv` (594 MB) and several figures exceed practical git file size limits. These are not tracked in the repository. A Zenodo deposit (DOI pending) will host derived data artifacts for long-term sharing. In the interim, regenerate them by re-running the relevant scripts in `scripts/dir6_*.py`.

## Authors

Heather MacGregor

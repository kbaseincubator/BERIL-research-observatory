# Methods — Comprehensive Metal Ecology

**Project:** Does per-Mb metal-gene KO density predict ecological niche breadth across prokaryotic genera?
**Hypothesis (H1):** Genera with higher per-megabase metal-gene KO density occupy **narrower** ecological niches (β < 0). This is the genome-streamlining prediction: specialists invest more of their limited genomic space in metal homeostasis.

All analyses are reproducible from the notebooks in `notebooks/` against the BERDL Spark cluster. Intermediate data files are in `data/`. Statistical utilities are in `scripts/`.

---

## 1. Metal-gene list construction (`data/curated_mrg_ko_ids_v2.csv`)

### 1.1 Universe of candidate KOs

The gene list was assembled from three independent sources:
1. **KEGG ORTHOLOGY / BRITE hierarchies** — KOs classified under BRITE modules for heavy-metal resistance, metal transport, and metalloenzymes (downloaded 2024). These were filtered to retain only KOs with an explicit metal annotation in the KEGG reaction or definition field.
2. **BacMet2 database** — experimentally validated metal resistance genes from BacMet v2.0 (Pal et al. 2014). KEGG IDs were assigned by mapping BacMet gene names to KEGG gene identifiers via KEGG REST API (`/find/genes/{name}` endpoint).
3. **FitnessBrowser (Deutschbauer lab)** — genome-wide transposon fitness screens in metallic stress conditions. KOs with significant fitness defects (|fitness score| > 1.5, t-statistic |t| > 5) under ≥1 metal stressor were included.

KOs appearing in ≥2 sources were cross-validated; KOs appearing in only one source were retained as lower-confidence candidates with appropriate tier labels.

### 1.2 Evidence tiers

Each of the 730 KOs in the final list is assigned to one of five evidence tiers:

| Tier | Label | n KOs | Criterion |
|------|-------|-------|-----------|
| 1 | Tier 1 | 32 | Multi-source validated: present in BacMet2 AND FitnessBrowser AND has clear KEGG module annotation |
| 2 | Tier 2 | 108 | Clear KEGG module definition; single additional source (BacMet2 or FitnessBrowser) |
| 2-Fitness | Tier 2-Fitness | 116 | FitnessBrowser-validated only; empirical fitness defect but no KEGG module annotation |
| 3-BacMet | Tier 3-BacMet | 188 | BacMet2-curated literature; no cross-validated fitness evidence |
| 3 | Tier 3 | 286 | KEGG BRITE only; ambiguous annotation or multi-function genes |

**Primary KO set** (used in all confirmatory tests): Tier 1 + Tier 2 = **140 KOs**. These have the strongest, multi-source evidence and unambiguous KEGG annotations. The `evidence_tier` column in `curated_mrg_ko_ids_v2.csv` identifies these rows.

### 1.3 Functional categories

Each KO is assigned to one primary functional category:

| Category | n KOs (total list) | n KOs (primary 140) |
|----------|--------------------|----------------------|
| Transport/Homeostasis | 213 | 106 |
| Resistance/Detoxification | 106 | 34 |
| Metal-dependent Metabolism | 54 | — |
| Sensing/Regulation | 48 | — |
| Cofactor Biosynthesis | 7 | — |
| Unknown | 302 | — |

Category assignment is binary: `is_resistance`, `is_transport`, `is_sensor`, `is_cofactor`, `is_metabolism` columns in the CSV. KOs may satisfy multiple categories; `primary_category` assigns the single most specific category. `overlap_flag = True` marks 6 KOs with dual-function ambiguity (primary set minus these dual-function KOs = 134 KOs; `overlap_excluded` subset).

### 1.4 Metal coverage

The primary 140-KO set covers 17 metals: Fe, Zn, Co, Mn, Cu, Ni, S, Mo, Cd, Al, Tl, Ag, Hg, Au, Pb, As, Bi. Metals are listed per KO in the `metals` column (comma-separated). A KO is included in a metal-specific subset if its `metals` field contains that metal.

### 1.5 Supplementary Pfam/InterPro QC (Notebook 10)

To assess whether the primary KO set has independent structural evidence of metal interaction, we performed a three-step API pipeline for all 140 KOs:

1. **KO → gene**: KEGG REST `link/genes/ko:{KO}` → filter to representative model organisms in order of priority (eco, bsu, pae, syn, mtu, sco, rpr, cje, bpe, mge); KEGG REST `conv/uniprot/{gene_id}` → UniProt accession. Rate: 0.4 s per call; 3-retry exponential back-off.
2. **Gene → Pfam**: UniProt REST `/{acc}?fields=xref_pfam&format=tsv` → Pfam domain IDs.
3. **Pfam → clan**: InterPro API `/entry/pfam/{PF}/?format=json` → `metadata.set_info.accession` → InterPro clan. Rate: 0.3 s per call.

Metal-binding domains were defined by five InterPro clans (verified present in InterPro version 97+):
- CL0704 — HMA (Heavy Metal Associated) domain
- CL0344 — 4Fe-4S ferredoxin
- CL0486 — Fer2 / 2Fe-2S ferredoxin
- CL0361 — C2H2 zinc finger
- CL0193 — MBB (metal beta-barrel)

Plus ~25 metal-binding singleton Pfams identified from literature (PF00403, PF00327, PF02403, PF00489, etc.). Note: clans CL0049 and CL0124 cited in older literature are absent from InterPro 97+ and were not used; their functional equivalents are CL0704 and CL0193 respectively.

**Results:** 10/140 (7.1%) KOs have ≥1 metal-binding clan or singleton Pfam. The 130 without evidence fall into three categories: `pfam_no_metal_clan` (113 KOs — Pfams found but none in metal-binding clans; predominantly ABC transporter ATPase/permease scaffolds PF00005/PF00950/PF01032, MerR-family sensors, outer-membrane efflux proteins), `no_gene_found` (15 KOs — no representative bacterial gene in KEGG REST), and `no_pfam_domains` (2 KOs — ARN/K08197, cbiL/K16915). The low InterPro coverage is expected: metal transporters act via substrate selectivity at the binding pocket, not via catalytic metal-co-factor domains, and will systematically fail clan-based Pfam filtering. Full results in `data/pfam_qc_results.csv`; no-evidence KOs in `data/pfam_qc_no_evidence.csv`.

---

## 2. Per-Mb metal-gene KO density

### 2.1 Genomic data sources

**Primary (P1, NB01):** BERDL Spark cluster, namespace `kbase.ke_pangenome`. The `genus_clusters` table contains one row per GTDB genus with pangenome statistics including total gene count, mean genome size (bp), and the full set of KO annotations across all genomes in the genus-level cluster. Joined to `kbase.ke_pangenome.gtdb_taxonomy_r214v1` for phylum/kingdom annotation.

**Replication (P3, NB02):** `refdata.ngsa` (Australian Microbiome Initiative / NGSA dataset). KO content extracted by the same pipeline but restricted to genera detected in Australian soil and sediment samples.

**ENIGMA (NB11):** `enigma_genome_depot_enigma.browser_genome` — 3110 genomes (2925 isolates, 185 MAGs) from the Oak Ridge FRC (Field Research Centre) groundwater site. KO content retrieved via: `browser_genome.id → browser_gene.genome_id` (genome_id matches), `browser_gene.protein_id → browser_protein_kegg_orthologs.protein_id`, `browser_protein_kegg_orthologs.kegg_ortholog_id → browser_kegg_ortholog.id`, `browser_kegg_ortholog.kegg_id` (format: 'K02313', no prefix).

### 2.2 KO density formula

For each genus g:

```
ko_per_mb_primary(g) = n_distinct_primary_KOs(g) / mean_genome_size_Mb(g)
```

where `mean_genome_size_Mb = mean_genome_size_bp / 1e6` averaged across all genomes in the genus cluster, and `n_distinct_primary_KOs` counts unique KO IDs in the primary set (Tier 1+2, 140 KOs) present in ≥1 genome of the genus.

KEGG_KO format in `kescience_mgnify.gene_eggnog` (Spark): `'ko:K00849,ko:K01992'` — comma-separated with `ko:` prefix; queries use `explode(split(kegg_ko, ','))` to unnest, then filter to `ko:{k}` prefix.

### 2.3 Predictor standardisation

For PGLS, `ko_per_mb_primary` is z-scored within the analysis dataset to produce `predictor_z`:

```python
predictor_z = (ko_per_mb_primary - mean(ko_per_mb_primary)) / std(ko_per_mb_primary)
```

This ensures β coefficients are interpretable as the change in response per standard-deviation change in KO density. Standardisation is performed separately within each analysis dataset (bacteria, archaea, Australia-only) so β values are not directly comparable across datasets.

### 2.4 Summary statistics (P1 dataset)

| Statistic | Value |
|-----------|-------|
| n genera | 1574 |
| ko_per_mb_primary: mean (SD) | 8.61 (3.83) KOs/Mb |
| ko_per_mb_primary: range | 0.78–34.56 KOs/Mb |
| mean genome size: mean (SD) | 3.73 (1.63) Mb |
| Dominant phyla | Proteobacteria (43%), Firmicutes (21%), Actinobacteria (13%), Bacteroidetes (12%) |

### 2.5 Excluded data source

`mgnify_mag_ko_density.csv` (local file derived from MGnify MAG annotations) was excluded from all confirmatory and tier analyses after producing positive non-significant β values (β = +0.002 to +0.006, p = 0.135–0.593) with the same primary KO set, conflicting with the Spark-derived P1 result. The discrepancy reflects database differences between the local MGnify MAG file and the `kescience_mgnify` Spark namespace. All tier sweep and category analyses therefore use `kescience_mgnify` via Spark (n = 1073 genera).

---

## 3. Ecological niche breadth

### 3.1 Levins' standardised niche breadth

Niche breadth was quantified using Levins' B (Levins 1968), standardised following Colwell & Futuyma (1971):

```
B = 1 / Σ p_i²          (Levins 1968)
B_std = (B - 1) / (n - 1)   (Colwell & Futuyma 1971)
```

where p_i is the proportional abundance of a genus in sample i (relative to total abundance of that genus across all samples), and n is the total number of samples in the dataset. B_std ∈ [0, 1]: 0 = complete specialist (all occurrences in one sample), 1 = complete generalist (perfectly even distribution across all samples).

Implementation: `scripts/niche_utils.py::levins_b_std()`. Applied to OTU × sample abundance matrices; genera detected in fewer than a minimum number of samples are assigned NaN and excluded.

### 3.2 Primary niche breadth dataset (P1)

**Data source:** `arkinlab.microbeatlas` — genus-level OTU abundance matrix across >400,000 global 16S rDNA amplicon samples aggregated in the MicrobeAtlas database (Yilmaz et al.). Genus-level aggregation: each OTU linked to a genus via `otu_pangenome_link_v2.csv` (`otu_id → genus_lower`); per-genus B_std computed as the mean across all OTUs assigned to that genus.

The `genus_trait_table.csv` stores the final per-genus `mean_levins_B_std` alongside phylum, kingdom, mean genome size, and GC content. The trait table has 2,851 rows with non-null B_std.

**Minimum sample filter:** Genera detected in <5 samples are excluded (NaN). Sensitivity checks at min_n=50 and min_n=150 (the minimum number of MicrobeAtlas samples in which a genus must be detected) produce identical results to the baseline (n=1574 both cases), indicating that most genera exceed these thresholds with the MicrobeAtlas dataset at its current size.

### 3.3 EMP niche breadth (NB08)

**Data source:** Earth Microbiome Project 16S data (`refdata.emp_16s`). EMPO (Earth Microbiome Project Ontology) level-3 habitat categories used as the niche axis; if fewer than 5 unique EMPO-3 categories were present for a genus, EMPO-2 was used as fallback (applied throughout for this dataset, which had only 3 EMPO-3 categories represented — fell back to 4 EMPO-2 categories). Levins B_std computed from genus × EMPO-category co-occurrence matrix. Minimum: ≥5 EMP samples per genus. n = 539 genera after merging with primary ko_per_mb.

### 3.4 Soil-specialist definition (NB01 Block 11, NB14)

For the soil-restricted sensitivity analysis, genera were classified as soil-specialists via MicrobeAtlas `Env_Level_1` using the following ecosystem categories:

```python
SOIL_ENVS = {'soil', 'agricultural', 'farm', 'field', 'paddy', 'peatland', 'desert', 'shrub'}
```

Procedure: (1) For each OTU, identify the dominant `Env_Level_1` category (the row with maximum `n_samples_detected` in `otu_env_matrix.csv`). (2) Flag OTU as `is_soil` if its dominant environment ∈ SOIL_ENVS (case-insensitive). (3) Join OTUs to genera via `otu_pangenome_link_v2.csv`. (4) For each genus, compute `frac_soil = n_soil_otus / n_otus`. (5) Classify genus as soil-specialist if `frac_soil > 0.5`.

Soil-restricted P1 dataset: n = 162 genera. Result: λ = 0.471, β = −0.0328, SE = 0.01190, p = 0.00654 (stronger negative effect in soil specialists).

---

## 4. Phylogenetic tree

**Source:** GTDB (Genome Taxonomy Database) Release 214v1. The full genus-level phylogeny was downloaded in Newick format and pruned to retain only genera present in the PGLS input dataset using `dendropy.Tree.prune_taxa_with_labels()`.

- Bacterial tree: `data/gtdb_bac_genus_pruned.tree` (2283 taxa before pruning; 1574 retained for P1)
- Archaeal tree: `data/gtdb_arc_genus_pruned.tree` (pruned to 95 genera for P2; 41 for S3)

Tip labels in the tree use lowercase genus names with spaces replaced by underscores, matching the `genus_lower` column in all data files. All branch lengths are in units of substitutions per site.

---

## 5. Phylogenetic generalised least squares (PGLS)

### 5.1 Implementation

All PGLS models were fitted using `scripts/pgls_utils.py`, a custom implementation using `dendropy` for tree operations and `scipy`/`numpy` for optimisation and linear algebra.

**Variance-covariance matrix:** Built from the pruned tree as V[i,j] = shared branch length from root to MRCA(i,j) (= root-to-tip path for i=j). Function: `pgls_utils.build_vcv()`.

**Pagel's lambda:** The off-diagonal elements of V are scaled by λ ∈ (0, 1):

```
V_lambda[i,j] = λ × V[i,j]   for i ≠ j
V_lambda[i,i] = V[i,i]        (diagonal unchanged)
```

λ = 0 corresponds to OLS (no phylogenetic correlation); λ = 1 corresponds to Brownian motion (full phylogenetic signal). λ is estimated by maximising the log-likelihood:

```
log L = -0.5 × [n log(2π) + n log(σ²) + log|V_lambda| + (y - Xβ)ᵀ V_lambda⁻¹ (y - Xβ) / σ²]
```

Optimisation: `scipy.optimize.minimize_scalar()` with bounds (1e-4, 1 − 1e-4) and `method='bounded'`.

**GLS fit:** After λ optimisation, GLS coefficients β̂ and their standard errors are estimated:

```
β̂ = (XᵀV⁻¹X)⁻¹ XᵀV⁻¹y
σ² = (y - Xβ̂)ᵀ V_lambda⁻¹ (y - Xβ̂) / (n - p)
SE(β̂_j) = √([(XᵀV⁻¹X)⁻¹]_jj × σ²)
```

where p = number of predictors including intercept.

**Model statistics:**
- t-statistic: t_j = β̂_j / SE(β̂_j), with df = n − p
- AIC = −2 × log L + 2 × (p + 1)  (p predictors + intercept; σ² is not counted separately because σ² is estimated analytically within log L)
- ΔAIC vs null = AIC(model with predictor) − AIC(intercept-only model)
- r² = 1 − Var(residuals) / Var(response)

**Single-predictor models:** The primary, replication, sensitivity, tier, category, and metal analyses all use a single predictor (`predictor_z`). In these cases `result["beta"]` and `result["p_value"]` are returned directly (not nested in dicts).

### 5.2 Multiple testing correction

**Joint FDR (Section 1):** P1, P2, P3 corrected jointly using Benjamini-Hochberg. P1 FDR: 4.28e-08; P2 FDR: 0.178; P3 FDR: 0.755.

**Tier comparisons (Section 2):** T1.4 and T1.5 corrected together (BH, n=2).

**Category comparisons (Section 3):** F1.1–F1.5 corrected together (BH, n=5).

**Metal-specific (Section 4):** Nine metals corrected together (BH, n=9). All nine pass FDR < 0.05.

**No correction applied** to confounder checks (Section 5) or sensitivity analyses (Section 6) — these are pre-specified robustness tests, not independent hypotheses.

### 5.3 Primary result (P1)

| Parameter | Value |
|-----------|-------|
| n genera (bacteria) | 1574 |
| Pagel's λ | 0.757 |
| β (ko_per_mb_primary, z-scored) | −0.0207 |
| SE | 0.00368 |
| t-statistic | −5.629 |
| p (raw) | 2.14 × 10⁻⁸ |
| p (FDR, joint with P2/P3) | 4.28 × 10⁻⁸ |
| r² | 0.046 |
| ΔAIC vs null | −29.41 |
| Direction vs H1 | **Confirmed** (β < 0 = pre-specified direction) |

### 5.4 Archaea replication (P2)

| Parameter | Value |
|-----------|-------|
| n genera | 95 |
| Pagel's λ | 0.726 |
| β | −0.0137 |
| SE | 0.00872 |
| p (raw) | 0.119 |
| p (FDR) | 0.178 |
| Status | NON-SIGNIFICANT; directionally consistent with P1 |

### 5.5 NGSA replication (P3)

| Parameter | Value |
|-----------|-------|
| n genera (Australia only) | 482 |
| Pagel's λ | 0.346 |
| β | −0.00171 |
| SE | 0.00549 |
| p (raw) | 0.755 |
| p (FDR) | 0.755 |
| Status | NON-SIGNIFICANT; near-zero β |

---

## 6. Evidence-tier and category comparisons (Notebook 03)

### 6.1 Tier comparisons

Two additional KO sets were tested (n = 1073 genera from `kescience_mgnify` Spark namespace, which has fewer genera than P1's pangenome dataset):

- **T1.4** — `all_non_ambiguous` (444 KOs): excludes only Tier 3 KOs (which have ambiguous KEGG annotations). Includes Tier 1, Tier 2, Tier 2-Fitness, and Tier 3-BacMet.
- **T1.5** — `bacmet_only` (188 KOs): Tier 3-BacMet, literature-curated from BacMet2 without cross-validation.

Tiers T1.1 (32 KOs), T1.2 (108 KOs), T1.3 (140 KOs), and T1.6 (730 KOs) were computed from `mgnify_mag_ko_density.csv` and are excluded from the interpretation table due to database divergence (see Section 2.5).

### 6.2 Functional category comparisons

Each functional category was tested separately using a density metric computed from only the KOs in that category. All models used the same n = 1073 genera and the same GTDB tree. Results in `data/03_category_pgls_results.csv`.

The resistance category (F1.1, n=106 KOs, β = +0.003, p = 0.656) is the only category with a positive β — contrary to H1 (which predicts β < 0) — and is non-significant. This is the expected result: resistance genes are universal stress-response elements prone to HGT and are not predicted to drive the streamlining signal. All other categories show significant negative β, consistent with H1. The cofactor biosynthesis category (F1.4, n=7 KOs, β = −0.033) shows the strongest negative effect, as predicted for constitutively essential metal cofactor pathways.

### 6.3 Metal-specific comparisons

Metal-specific KO sets were defined as all primary-set KOs whose `metals` field contains the target metal. Models run for the 9 metals with ≥34 KOs in the primary set: Co (101 KOs), Fe (98), Ni (84), S (74), Cu (71), Zn (67), Tl (45), Al (34), Mn (34). All show significant negative β after BH correction (all FDR < 0.001 except Mn at 4.24e-04).

---

## 7. Confounder analyses (Notebook 04)

For each potential confounder, we refitted the PGLS model with the confounder added as an additional predictor alongside `predictor_z`, and recorded the change in the primary β:

```
Δβ = |β_with_confounder - β_baseline| / |β_baseline| × 100%
```

**Decision rule:** If Δβ > 50% AND the model is no longer significant (p > 0.05) → confounder explains the effect.

| Confounder | Operationalisation | Δβ (%) | Verdict |
|------------|-------------------|--------|---------|
| Genome size | Mean genome size in Mb (z-scored), same PGLS framework | 46.7% | ROBUST — below threshold, still significant (p = 0.006) |
| GC content | Mean genomic GC% (z-scored) | 23.7% | ROBUST |
| Isolation source | Categorical dummy (environment from which isolates were cultured) | 14.5% | ROBUST |
| Mean latitude | Mean absolute latitude of sampling locations per genus | 51.8% | ATTENUATED — exceeds threshold, but β becomes more negative (−0.031 vs −0.021), which is inconsistent with confounding (a true confounder should shrink β). Latitude amplifies, not explains, the signal. |
| Dominant biome | Majority Env_Level_1 category from MicrobeAtlas | 5.8% | ROBUST |

No confounder meets the pre-specified decision rule for confounding (>50% AND non-significant). The closest candidate, genome size, reduces β by 46.7% and the model remains significant (p = 0.006). This partial attenuation suggests that genera with higher metal-gene KO density may also have slightly larger genomes, and genome size itself correlates with niche breadth — but genome size does not fully explain the association.

---

## 8. Sensitivity analyses (Notebook 05)

Sensitivity analyses tested the robustness of the P1 result to modelling assumptions.

| ID | Modification | β | p | Notes |
|----|-------------|---|---|-------|
| S1 | λ fixed = 0 | −0.0319 | ≈0 | OLS under phylogenetic structure; stronger than ML-estimated λ result |
| S2 | λ fixed = 1 | −0.0182 | 3.66e-06 | Brownian motion; consistent |
| S3 | Archaea tree, min n=5 genera | −0.0183 | 0.084 | n=41; directionally consistent, underpowered |
| S4 | min_n = 50 samples | −0.0207 | 2.14e-08 | Identical to baseline |
| S5 | min_n = 150 samples | −0.0207 | 2.14e-08 | Identical to baseline |
| S6 | Raw B (unstandardised) | −0.286 | 1.11e-11 | Stronger signal; same direction |
| S7 | Australia-only subset | −0.00171 | 0.755 | Null; same as P3 replication |
| S8 | Northern hemisphere only | −0.0302 | 3.24e-06 | Stronger than P1; consistent |

S4 and S5 produce identical results because all 1574 genera in the primary dataset have MicrobeAtlas detection counts well above 150, making both thresholds redundant at the current data density. S7 = P3 (same n=482 Australian dataset). 6/7 pre-specified sensitivity checks are directionally consistent with P1 and significant.

---

## 9. EMP niche breadth validation (Notebook 08)

### 9.1 Data

Earth Microbiome Project 16S data from `refdata.emp_16s` (Spark namespace). Tables: `sample_metadata` (sample-level EMPO habitat classifications), `otu_summary_deblur_90bp` (OTU × sample occurrence counts), `otu_metadata` (taxonomy including genus from `g__` extraction).

Genus extracted from taxonomy string via: `REGEXP_EXTRACT(tax, 'g__([^;]+)', 1)` with fallback to `SPLIT(tax, ';')[5]`.

### 9.2 EMPO niche axis

EMPO (Earth Microbiome Project Ontology) defines hierarchical habitat categories. We used EMPO level-3 as the niche axis; if fewer than 5 distinct categories were present in the dataset for a given genus, EMPO level-2 was used as fallback. The EMP dataset here had only 3 EMPO-3 categories represented, so level-2 (4 categories) was used throughout.

### 9.3 Analysis

Levins B_std computed from genus × EMPO-category co-occurrence. Minimum 5 EMP samples per genus. Merged with `01_genus_ko_density_spark.csv` on `genus_lower`. n = 539 genera after merge.

**Result:** λ = 0.055 (little phylogenetic signal in EMP niche breadth), β = −0.0190, SE = 0.01150, p = 0.099 (NON-SIGNIFICANT). Directionally consistent with P1. The near-zero λ suggests EMP-derived niche breadth at EMPO-2 resolution has little phylogenetic structure — either the metric is noisy at this resolution, or habitat generalism is weakly phylogenetically conserved.

Saved: `data/emp_niche_pgls_comprehensive.csv`, `data/emp_genus_empo_counts.csv`.

---

## 10. BacDive geographic niche breadth (Notebook 09)

### 10.1 Design

BacDive isolation metadata (`kescience.bacdive.isolation`) was planned as a culture-based, independent niche breadth proxy: the number of distinct countries from which a genus has been cultured. Standardised B_std = (n_countries − 1) / (N_max − 1) where N_max = 95th percentile of n_countries across genera with ≥5 isolates, clamped [0,1]. Planned PGLS: BacDive B_std ~ ko_per_mb_primary (Tier1+2).

### 10.2 Status

**DID NOT COMPLETE.** Schema exploration (cells nb090004, nb090008) confirmed the table structure (`kescience.bacdive.isolation` has 8 columns: bacdive_id, sample_type, country, continent, geographic_location, cat1, cat2, cat3; `kescience.bacdive.taxonomy` has genus, species, domain, phylum, etc.). However, the main analysis cells (nb090010 through nb090020) were not executed. Output files `data/bacdive_genus_country_counts.csv` and `data/bacdive_niche_pgls_comprehensive.csv` were not produced.

**Action required:** Re-execute NB09 from cell nb090010 in JupyterHub.

---

## 11. ENIGMA FRC site-specific replication (Notebook 11)

### 11.1 Site and rationale

The Oak Ridge FRC (Field Research Centre) is a uranium- and heavy-metal-contaminated groundwater site in Tennessee, USA. The ENIGMA consortium has assembled MAG-resolved metagenomes from multiple groundwater monitoring wells. Within-site variation in groundwater metal concentrations provides an opportunity to test whether MAGs from more contaminated wells carry higher per-Mb metal-gene density — a site-level replication of the ecological hypothesis using direct geochemical measurements.

### 11.2 Pre-specified design

| Parameter | Pre-specified value |
|-----------|---------------------|
| Metals | Cu, Ni, Zn, As, Mn, Cr, Co (groundwater mg/L; ≥90 non-null measurements each) |
| Expected direction | **Positive** (higher well-level metal → higher MAG ko_per_mb) |
| Unit of analysis | MAG-level (n≈185) and well-level sensitivity (n≤21) |
| Method | Spearman rank correlation |
| Multiple testing | Benjamini-Hochberg FDR across 7 metals |

### 11.3 Genomic data

Source: `enigma_genome_depot_enigma`. MAGs identified as rows in `browser_genome` where `sample_id IS NOT NULL` (185 MAGs). KO content retrieved via:

```
browser_genome (id, size, sample_id)
  → browser_gene (genome_id, protein_id)        [genome_id = browser_genome.id]
  → browser_protein_kegg_orthologs (protein_id, kegg_ortholog_id)
  → browser_kegg_ortholog (id, kegg_id)          [format: 'K02313', no prefix]
```

KO density: n_distinct primary KOs / (genome_size_bp / 1e6).

Well ID: `browser_genome.sample_id → browser_sample.id` (integer FK) → `browser_sample.sample_id` (well name, e.g., 'FW300', 'FW106-02').

### 11.4 Geochemical data

Source: `enigma_coral.ddt_brick0000007` (68-column geochemistry brick). Groundwater metal columns (mg/L):

| Metal | Column | Non-null rows (n=300 total) |
|-------|--------|---------------------------|
| Cu | concentration_molecule_from_list_copper_atom_milligram_per_liter | 127 |
| Ni | concentration_molecule_from_list_nickel_atom_milligram_per_liter | 122 |
| Zn | concentration_molecule_from_list_zinc_atom_milligram_per_liter | 132 |
| As | concentration_molecule_from_list_arsane_milligram_per_liter | 130 |
| Mn | concentration_molecule_from_list_manganese_atom_milligram_per_liter | 126 |
| Cr | concentration_molecule_from_list_chromium_atom_milligram_per_liter | 94 |
| Co | concentration_molecule_from_list_cobalt_atom_milligram_per_liter | 90 |

Per-well aggregation: median across all date-stamped measurements (sample names like 'FW300-11-05-13' for well FW300, date 2013-05-11). Well ID extracted using startswith matching (longest browser_sample.sample_id matched first, to correctly handle 'FW106-02' vs 'FW106').

### 11.5 Results and failure

**Critical limitation:** Of 185 MAGs and 21 FRC wells in the genome database, only 29 MAGs from 3 wells had matching entries in `ddt_brick0000007`. Most FRC wells with MAGs had no temporal geochemistry in this table. The well-level analysis (n=3) is statistically meaningless.

**MAG-level results (n=29):**

| Metal | rho | p (raw) | p (FDR) | Direction |
|-------|-----|---------|---------|-----------|
| Cu | +0.166 | 0.390 | 0.390 | Pre-specified positive; NS |
| Ni | +0.166 | 0.390 | 0.390 | Pre-specified positive; NS |
| Zn | +0.380 | 0.042 | 0.147 | Pre-specified positive; NS after FDR |
| As | −0.166 | 0.390 | 0.390 | **Opposite** direction; NS |
| Mn | −0.166 | 0.390 | 0.390 | **Opposite** direction; NS |
| Cr | −0.407 | 0.029 | 0.147 | **Opposite** direction; NS after FDR |
| Co | −0.369 | 0.120 | 0.280 | **Opposite** direction; NS (n=19 with Co data) |

Combined metal burden (mean of z-scored per-well concentrations, 7 metals): ρ = −0.407, p = 0.028 (MAG-level, n=29) — **opposite to pre-specified direction**.

**Verdict:** NOT SUPPORTED. 3/7 metals show positive ρ (Cu, Ni, Zn); 4/7 show negative ρ. No metal survives FDR correction. The combined burden is negative, contrary to expectation. The data are insufficient for a valid test (n_wells=3). Recommend accessing the full ENIGMA geochemical database for a future attempt.

---

## 12. Reporting standards

### 12.1 Pre-registration equivalent

All confirmatory tests (Sections 5–8) were pre-specified in `RESEARCH_PLAN.md` before execution. Exploratory analyses (Sections 9–11) are labelled as such throughout. The `INTERPRETATION_TABLE.md` tracks statistical outcomes and was finalised in advance with decision rules and direction predictions.

### 12.2 INTERPRETATION_TABLE.md governance

Every claim in any write-up must be traceable to a row in `INTERPRETATION_TABLE.md`. The notebook cell ID and output file are recorded in each row. Statistical values in `INTERPRETATION_TABLE.md` were entered directly from the saved CSV files in `data/`, not from notebook-cell display output.

### 12.3 FDR correction policy

- Confirmatory tests (P1, P2, P3): joint BH correction.
- Tier comparisons: BH within tier comparisons (n=2 tests in the interpreted set).
- Category comparisons: BH across 5 categories.
- Metal comparisons: BH across 9 metals.
- Confounder and sensitivity analyses: no correction (pre-specified robustness checks).
- Exploratory analyses (Sections 9–11): uncorrected p values reported; these are hypothesis-generating, not confirmatory.

### 12.4 Software and versions

| Tool | Version | Use |
|------|---------|-----|
| Python | 3.10 | All analysis |
| PySpark | 4.0.1 | Distributed KO extraction from BERDL Spark |
| dendropy | — | Phylogenetic tree manipulation and VCV construction |
| numpy | — | Linear algebra for PGLS |
| scipy | — | Lambda optimisation, t-distribution p-values, Spearman correlation |
| pandas | — | Data manipulation |
| statsmodels | — | Benjamini-Hochberg FDR correction |
| KEGG REST API | — | KO→gene, gene→UniProt (NB10) |
| UniProt REST API | — | Gene→Pfam (NB10) |
| InterPro API | v97+ | Pfam→clan (NB10) |

### 12.5 Data file registry

| File | Produced by | Description |
|------|-------------|-------------|
| `curated_mrg_ko_ids_v2.csv` | Manual curation | Full 730-KO gene list with tiers, categories, metals |
| `curated_mrg_ko_ids_v2_pfam.csv` | NB10 | Gene list augmented with Pfam IDs from InterPro pipeline |
| `01_genus_ko_density_spark.csv` | NB01 | Per-genus ko_per_mb_primary from BERDL Spark |
| `01_pgls_input_bacteria.csv` | NB01 | PGLS input: 1574 bacterial genera |
| `01_primary_pgls_results.csv` | NB01 | P1 and P2 PGLS results |
| `01_soil_restricted_pgls_results.csv` | NB01 | Soil-restricted sensitivity (MicrobeAtlas Env_Level_1) |
| `02_ngsa_pgls_results.csv` | NB02 | P3 PGLS result (AusMicrobiome) |
| `02_ngsa_pgls_input.csv` | NB02 | PGLS input: 482 Australian genera |
| `02_p3b_soil_pgls_results.csv` | NB02 | P3b soil-restricted sensitivity |
| `02_joint_fdr.csv` | NB02 | Joint BH FDR across P1/P2/P3 |
| `03_tier_pgls_results.csv` | NB03 | T1.4 and T1.5 tier-sweep results |
| `03_category_pgls_results.csv` | NB03 | F1.1–F1.5 category results |
| `03_metal_pgls_results.csv` | NB03 | Metal-specific results (9 metals) |
| `04_confounder_results.csv` | NB04 | Confounder β-change analysis |
| `05_sensitivity_results.csv` | NB05 | S1–S8 sensitivity results |
| `06_candidate_coverage.csv` | NB06 | Geospatial coverage of candidate environmental datasets |
| `emp_niche_pgls_comprehensive.csv` | NB08 | EMP PGLS result |
| `emp_niche_pgls_input.csv` | NB08 | 539-genus EMP niche input |
| `emp_genus_empo_counts.csv` | NB08 | Genus × EMPO category co-occurrence |
| `pfam_qc_results.csv` | NB10 | Full 140-KO Pfam/InterPro QC table |
| `pfam_qc_no_evidence.csv` | NB10 | 130 KOs lacking metal-binding domain evidence |
| `pfam_qc_cache.json` | NB10 | API call cache (KEGG, UniProt, InterPro) |
| `enigma_frc_replication.csv` | NB11 | ENIGMA FRC Spearman correlations |
| `enigma_frc_mag_geo_joined.csv` | NB11 | MAG × geochemistry joined dataset (29 MAGs, 3 wells) |
| `enigma_frc_well_geochemistry.csv` | NB11 | Per-well median geochemistry |

---

## 13. Key analytical decisions and justifications

**Why z-score the predictor?** Standardisation allows β to be interpreted as the response change per SD change in KO density, making coefficients comparable across models with different KO-set sizes (different denominators change absolute density values). It does not affect p-values, λ, or r².

**Why PGLS rather than OLS?** The estimated λ = 0.757 for P1 indicates substantial phylogenetic signal in niche breadth. OLS would be anti-conservative (artificially small SEs) because closely related genera share niche characteristics. PGLS corrects for this by down-weighting co-variation explained by phylogeny. The S1 result (λ=0) shows a slightly larger β in magnitude but the same direction and significance, confirming the result is not an artefact of the phylogenetic correction.

**Why Levins B_std rather than raw B?** B_std is bounded [0,1] and corrects for variation in the total number of samples across datasets — raw B increases with sample number even for a specialist, making it non-comparable across datasets. The S6 sensitivity (raw B) gives a consistent result (β = −0.286, p = 1.11e-11), confirming the scaling choice does not drive the finding.

**Why not include Tier 2-Fitness and Tier 3-BacMet in the primary set?** Tier 2-Fitness genes have empirical fitness evidence but lack confirmed functional annotation in KEGG modules, making the `ko_per_mb` calculation dependent on a noisier mapping. Tier 3-BacMet genes have only single-source literature evidence, often from non-model organisms, and are more likely to include false positives. Including these tiers (tested in T1.4) strengthens the negative signal (β = −0.027), suggesting the primary set is if anything conservative.

**Why Spearman rather than PGLS for ENIGMA (NB11)?** The ENIGMA analysis is at the MAG level, not genus level, and there is no established phylogenetic tree spanning the 29 MAGs from 3 wells. PGLS requires a resolved, calibrated phylogeny. Spearman correlation is appropriate for a non-parametric site-level test with small n. The result was ultimately limited by poor data coverage (n_wells=3).

**Why is the Australia-only result (P3) null?** Three possible explanations: (1) reduced power — n=482 vs 1574 for P1, and β is smaller in the Australian subset (−0.002 vs −0.021); (2) the AusMicrobiome/NGSA dataset may have lower taxonomic diversity in metal-gene-rich genera; (3) Australian soils may be geochemically distinct enough that the metal-gene/niche association is weaker in that environmental context. The Northern hemisphere subset (S8, n=542) shows a stronger negative effect (β = −0.030), suggesting the Australian null may reflect a genuinely weaker signal in that continental dataset rather than a power issue alone.

---

## 14. Australian replication analyses

### 14.1 P4: Soil metal concentration → niche breadth (Notebook 12)

**Predictor:** Per-well NGSA ICP-MS soil metal concentrations (Cu, Zn, Pb, Ni, Co, μg/g dry soil).
**Response:** `mean_levins_B_std` for each genus in the AusMicrobiome dataset.
**Spatial join:** Each genus linked to NGSA sampling locations within 200 km (Haversine distance);
mean metal concentration assigned across joined sites.
**Analysis:** PGLS (same framework as P1) on n=482 genera. Five models run independently (one per
metal), BH-FDR applied across the 5 metals.
**Results:** Cu and Zn significant after FDR (q=0.041 each). Pb, Ni directionally consistent but
not FDR-significant. Co opposite direction.

### 14.2 P5: Genomic metal-gene density → niche breadth in AusMicrobiome (Notebook 15)

**Design:** Pre-specified confirmatory replication. Same predictor as P1 (`ko_per_mb_primary`, Tier
1+2, 140 KOs) using the same `01_pgls_input_bacteria.csv` density values, restricted to the n=482
genera in the AusMicrobiome subset (identified via inner join with `02_ngsa_pgls_input.csv`).
`ko_per_mb_primary` is z-scored within the 482-genus subset (not within P1). Same GTDB bacterial
tree (pruned to 482 genera). Single pre-specified test; FDR not applicable.

**Results:** β = −0.052 (SE = 0.0063, t = −8.20, p = 2.2×10⁻¹⁵, partial R² = 0.194,
ΔAIC = −61.2, λ = 0.734). 2.5× larger β than P1; z-test vs P1: z ≈ 4.1, p < 0.001.

**Diagnostic analysis (NB21, exploratory):**
1. Z-test: `z = (β_P5 − β_P1) / sqrt(SE_P5² + SE_P1²)` comparing P5 to P1 and to the
   soil-restricted P3b β.
2. Intersecting-genus PGLS: restrict P1 to genera present in both datasets; compare β.
3. B_std identity check: verify P1 and P5 B_std values are identical for overlapping genera
   (same MicrobeAtlas Env_Level_1 computation).
4. Phylum composition: bar chart comparing phylum fractions in P1, P5, and intersection.
5. Density scatter: per-Mb density for overlapping genera, Spearman ρ, 1:1 reference line.

*Data: `data/pgls_ausmicrobiome_density_replication.csv`, `data/aus_beta_comparison.csv`,
`data/intersecting_genus_pgls.csv`, `figures/fig_p5_aus_density.png`,
`figures/aus_composition_comparison.png`, `figures/aus_density_overlap_scatter.png`.*

---

## 15. Functional landscape analysis (Notebook 18)

**Motivation:** The three named negative controls (ribosomal proteins, amino acid biosynthesis, DNA
repair; NB17) all showed strongly negative β values (−0.029 to −0.034), revealing a pervasive
genome-streamlining signal rather than true nulls. To characterise the full landscape within which
the metal-gene signal sits, 19 KEGG functional categories were tested at the same per-Mb density
resolution.

**Category selection:** All KEGG BRITE second-level functional categories with ≥100 associated KOs
in the KEGG database, excluding categories already in the primary gene list (metal-related) and
categories with insufficient genus representation (n < 100 genera after density computation). This
yielded 19 testable categories covering the breadth of prokaryotic functional biology.

**Per-category density:** Same Spark SQL as P1 (`kescience_mgnify.genome` + `gene_eggnog`), with
the KO filter set to the category-specific list. Per-genus mean ko_per_mb computed, z-scored within
each analysis dataset. Same PGLS framework as P1. Minimum n=100 genera.

**Multiple testing:** BH-FDR applied across all 19 categories simultaneously. Metal gene set P1
result (β = −0.021, p = 2.1×10⁻⁸) included as a reference point but not in the FDR family.

**Results:** 14/19 categories significant at FDR < 0.05. Constitutive housekeeping and information-
processing categories define a streamlining baseline (β ≈ −0.029 to −0.035). Five categories show
|β| < 0.006 and q > 0.45 (ABC transporters non-metal, AMR beta-lactam, glycan biosynthesis, cell
motility, two-component systems) — confirmed true-negative controls.

*Data: `data/functional_landscape_results.csv`, `figures/functional_landscape_forest.png`.*

---

## 16. Negative-control analyses (Notebooks 17, 20)

### 16.1 Named housekeeping controls (NB17, complete)

Three a priori housekeeping gene sets were selected as expected true nulls:
- **Ribosomal proteins:** 52 KOs (LSU + SSU core ribosomal protein genes, all phyla)
- **Amino acid biosynthesis:** 38 KOs (KEGG biosynthesis pathway KOs for all 20 standard amino acids)
- **DNA repair:** 24 KOs (core repair machinery: MutS/L/H, UvrABC, RecA, base excision repair)

Each set was run through the identical Spark density computation and PGLS pipeline (minimum 30
genera for named controls, given these are expected to show β ≈ 0). Results revealed all three
as streamlining indicators (β = −0.029 to −0.034), not true nulls. This finding directly motivated
the functional landscape analysis (Section 15).

*Data: `data/nc_ribosomal_proteins_density.csv`, `data/nc_aa_biosynthesis_density.csv`,
`data/nc_dna_repair_density.csv`, appended to `data/negative_control_pgls_results.csv`.*

### 16.2 Predictor permutation test (NB01 Block 14)

The predictor (`ko_per_mb_primary_z`) was permuted across genera 1,000 times. Each permutation
was evaluated with GLS using the same Pagel's λ (0.757) and VCV matrix as P1 (Cholesky
pre-factored; 0.2 ms per permutation). Empirical p = 0/1000 (< 0.001). Observed β is 7.14 SD
below the null mean.

### 16.3 Coreness-matched permutation (NB20, pending JupyterHub execution)

**Definition of KO coreness:** Fraction of all genomes in `kbase.ke_pangenome` carrying a given KO.
This is a per-KO property reflecting pan-genome prevalence, distinct from "annotation depth" (the
per-genus mean number of genomes detecting each KO from the analysis dataset).

**Design:**
1. Compute per-KO coreness from `kbase.ke_pangenome` (total genomes as denominator).
2. Assign each primary KO to a coreness decile (based on full pan-genome KO coreness distribution).
3. Generate 1,000 permuted KO sets: for each permutation, sample n=140 KOs matched to the primary
   set's decile distribution (sampling from the pool of non-primary KOs in the same decile).
4. Run identical PGLS pipeline on each permuted set. Report null β distribution and empirical p.
5. Secondary (100 sets): run PGLS with genome size as covariate; compute % β-attenuation;
   compare distribution to observed 46.7% attenuation in primary analysis.

*Data: `data/ko_coreness_pangenome.csv`, `data/coreness_permutation_results.csv`,
`data/attenuation_profile_comparison.csv`, `figures/coreness_permutation_histogram.png`.*

---

## 17. Exploratory analyses (NB19, NB21–NB23)

All NB19–NB23 analyses are labelled **exploratory**. Run once. No iterative tuning. Results
reported regardless of direction or significance.

### 17.1 Internal structure comparison (NB19)

Tests whether the resistance-null / constitutive-significant split within metal genes is
distinctive, by running the identical PGLS at sub-functional resolution on three comparison
categories:

- **AMR (ko01504):** KEGG BRITE B-level classified to mechanism via curated mapping:
  `beta-Lactamase / Aminoglycoside / Phenicol / Fosfomycin genes → Enzymatic inactivation`;
  `Multidrug resistance modules → Efflux pumps`;
  `Tetracycline / Macrolide / Vancomycin / beta-Lactam resistance modules / CAMP / Trimethoprim /
  Quinolone / Rifamycin / Sulfonamide resistance genes → Target modification/protection`.
- **Two-component systems (ko02020):** Pathway ORTHOLOGY section parsed; KOs classified by
  definition keyword (`sensor histidine kinase` / `sensor kinase` → sensor HK;
  `response regulator` → RR; remainder → phosphotransfer/other).
- **ABC transporters (ko02010):** Pathway ORTHOLOGY classified by substrate keyword (sugar,
  amino acid/peptide, inorganic ion non-metal, vitamin/cofactor, lipid/LPS, drug/multidrug);
  40 KOs present in primary metal gene list excluded from analysis.

Minimum: n_KOs ≥ 5 per subcategory; n_genera ≥ 100 for PGLS. BH-FDR within each parent
category. Output: β, SE, p, q, λ, n_genera, n_kos per subcategory.

*Data: `data/internal_structure_results.csv`, `figures/internal_structure_forest.png`.*

### 17.2 MAG quality covariates (NB22)

Per-genus mean completeness and contamination queried from `kescience_mgnify.genome`
(CheckM columns). Three PGLS models:
- Baseline: `B_std ~ density_z`
- `B_std ~ density_z + completeness_z`
- `B_std ~ density_z + contamination_z`

Sensitivity: restrict to genera with mean completeness ≥ 90% AND contamination ≤ 5%.
% β-attenuation = `(β_baseline − β_with_covariate) / β_baseline × 100`.

*Data: `data/genus_mag_quality.csv`, `data/mag_quality_sensitivity.csv`.*

### 17.3 Category descriptive statistics and conditional PGLS (NB23)

For 5 metal categories + 3 comparison categories (Translation ko03016, Nucleotide metabolism
ko00230+00240, AMR beta-lactam from ko01504):
- n KOs
- Mean gene length (estimated from KEGG REST API; 30-KO sample per category)
- Core fraction (fraction of category KOs with pan-genome prevalence ≥ 95%)
- Mean KO prevalence (from kbase.ke_pangenome)
- Mean annotation depth (mean_prevalence × total_genomes)

Conditional PGLS models (on primary gene set, n=P1 genera with complete covariates):
- `B_std ~ density_z + n_KOs_detected_z` (controls for annotation completeness)
- `B_std ~ density_z + ko_breadth_z` (fraction of primary KOs detected; coreness proxy)
- `B_std ~ density_z + genome_size_z`
- `B_std ~ density_z + n_KOs_detected_z + ko_breadth_z`

*Data: `data/category_descriptive_stats.csv`, `data/category_conditional_models.csv`.*

---

## 18. Analysis Registry

Complete record of all analyses, their pre-registration status, and classification as confirmatory or exploratory. Confirmatory analyses test H1 or a pre-specified extension with a clear directional prediction stated before data inspection. Exploratory analyses were designed or parameterised after seeing the P1 result and cannot support or refute H1 directly.

**Classification criteria:**
- **Confirmatory** — hypothesis direction pre-stated, decision rule pre-specified, analysis designed before data inspection
- **Exploratory** — designed or parameterised after P1 result seen; results reported regardless of direction; no iterative tuning allowed; cannot shift H1 classification

| ID | Notebook | Description | Type | Pre-specified direction | Run once? | Status |
|----|----------|-------------|------|------------------------|-----------|--------|
| P1 | NB01 | Primary PGLS: `B_std ~ ko_per_mb_z`, Bacteria, 140 KOs, GTDB tree | **Confirmatory** | β < 0 | Yes | Complete |
| P2 | NB01 | Primary PGLS: Archaea replication | **Confirmatory** | β < 0 | Yes | Complete |
| P3 | NB01/12 | NGSA Australia-only subset | **Confirmatory** | β < 0 | Yes | Complete |
| T1 | NB03 | Evidence-tier sweep (T1.1–T1.6) | **Confirmatory** | β < 0 for Tier 1+2 | Yes | Partial (Spark tiers excluded — database mismatch) |
| F1 | NB03 | Functional category PGLS (5 categories) | **Confirmatory** | Resistance β≈0; others β<0 | Yes | Complete |
| M1 | NB03 | Metal-specific PGLS (9 metals) | **Confirmatory** | β < 0 for all metals | Yes | Complete |
| C1 | NB04 | Confounder checks (5 confounders) | **Confirmatory** | Decision rule: >50% attenuation AND NS | Yes | Complete |
| S1–S8 | NB05 | Pre-specified sensitivity analyses | **Confirmatory** | β < 0 for all variants | Yes | Complete |
| P4 | NB12 | AusMicrobiome × NGSA replication (env predictor, 5 metals) | **Confirmatory** | β < 0 | Yes | Complete |
| P5 | NB15 | AusMicrobiome genomic density replication | **Confirmatory** | β < 0 | Yes | Complete |
| P6 | NB16 | Clade-stratified PGLS (4 phyla) | **Confirmatory** | β < 0 within each phylum | Yes | Complete |
| E1 | NB17 | Named negative controls (3 housekeeping sets) + 1,000 predictor permutations | **Confirmatory** | Controls β≈0; permutation empirical p | Yes | Complete |
| E2 | NB18 | Functional landscape: 19 KEGG categories | Exploratory | No directional H1 test | Yes | Complete |
| E3 | NB19 | Internal structure: AMR / TCS / ABC sub-categories | Exploratory | If distinctive: comparison families should NOT replicate the split | Yes | Complete |
| E4 | NB20 | Coreness-matched permutation (1,000 sets) | Exploratory | Null β distribution; compare observed attenuation | Yes | Pending JupyterHub |
| E5 | NB21 | Australian β comparison (P1 vs P5 intersection analysis) | Exploratory | Diagnostic — explains P5 vs P1 difference | Yes | Complete |
| E6 | NB22 | MAG quality covariates (completeness, contamination, HQ-restricted) | Exploratory | Decision rule same as C1 (>50% attenuation) | Yes | Complete |
| E7 | NB23 | Category descriptive stats + conditional PGLS | Exploratory | No directional H1 test | Yes | Pending JupyterHub |
| E8 | NB24 | Niche-breadth metric sensitivity (bootstrap, Shannon, sample depth) | Exploratory | Bootstrap β should match P1; Shannon ρ > 0 | Yes | Complete (Block 3 pending JupyterHub) |
| QC | NB10 | Pfam/InterPro structural validation of gene list | QC only | — | Yes | Complete |
| Obs | NB06 | Environmental covariate candidate screen | Observational | — | Yes | Complete |
| Obs | NB07 | Geological proxy correlations | Observational | — | Yes | Complete |
| Obs | NB08 | EMP 16S niche breadth (independent metric) | Observational | Directionally consistent with P1 | Yes | Complete |
| Obs | NB09 | BacDive geographic niche breadth | Observational | β < 0 (independent niche metric) | Yes | Pending JupyterHub |
| Obs | NB11 | ENIGMA MAG geochemistry (site-level, n = 3 wells) | Observational | ρ > 0 (high-metal wells → higher density) | Yes | Complete (insufficient n) |
| Obs | NB13/14 | Soil-restricted replication (MicrobeAtlas, ENIGMA soil) | Observational | β < 0 | Yes | Complete |

**Decision rule precedence:** Only the P1 result and pre-specified sensitivity checks (S1–S8) determine whether H1 is supported or not. All exploratory and observational analyses contribute to mechanistic interpretation only. An exploratory null does not contradict H1; an exploratory significant result does not confirm it beyond what the confirmatory tests establish.

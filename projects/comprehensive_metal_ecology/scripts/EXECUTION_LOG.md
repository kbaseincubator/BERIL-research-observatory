# Script Execution Log — comprehensive_metal_ecology

Scripts that produced REPORT.md Findings 12–17 and Q1–Q4 were executed in JupyterHub
(Spark available, Python 3.13, PySpark 4.0.1, kbase.ke_pangenome + kescience_mgnify BERDL tables).
Key numerical outputs are recorded here for independent verification.

## Finding 12 — Two-scale phylogenetic signal (fritz_purvis_D_genome.py)

**Script:** `scripts/fritz_purvis_D_genome.py`  
**Inputs:** `data/curated_mrg_ko_ids_v2.csv`, GTDB r214 18,961-tip genus tree, kbase.ke_pangenome genome/gene tables  
**Output:** `data/fritz_purvis_D_genome.csv` (309 rows), `data/phylo_d_all_ko.csv` (276 rows, Pagel's λ)

Key results:
- Fritz & Purvis D mean (DS double-signal KOs, n=13): 0.78 (SD=0.29)
- Fritz & Purvis D mean (control KOs): 0.61 (SD=0.31)
- MWU D DS vs control: p = 1.81×10⁻⁴
- D vs λ Spearman ρ = −0.041, p = 0.49 (near-orthogonal — two-scale independence confirmed)
- Double-signal KOs (D > 0.2 AND λ < 0.3): 13 KOs; all resistance/transport/sensing, no cofactor

## Finding 13 — Environmental niche breadth (env_niche_spark_analysis.py, 02_env_niche_pgls.R)

**Scripts:** `scripts/env_niche_spark_analysis.py` (Spark: per-genus env data), `results/02_env_niche_pgls.R` (PGLS)  
**Inputs:** kescience_mgnify genus MAG data, MicrobeAtlas site pH/temperature data  
**Output:** `results/env_niche_pgls_coefficients.csv`

Key results (PGLS `env_niche ~ ko_per_mb_z + genome_mb_z`, n=1,195 genera):
- Temperature range: β = +0.079, SE = 0.886, p = 0.929 (NS)
- Soil pH niche width (pH units, max–min across sites): β = −0.760, SE = 0.233, p = 0.001, λ = 0.11
- Composite environmental gradient (PC1 of pH/temp/precip): β = −0.064, SE = 0.017, p < 0.001

## Finding 14 — Per-KO environmental drivers (per_ko_driver_analysis.py)

**Script:** `scripts/per_ko_driver_analysis.py`  
**Inputs:** `data/01_pgls_input_bacteria.csv`, kescience NGSA/GeoROC metal data per genus  
**Output:** `results/per_ko_pgls_results.csv`

Key results (9 Tier1 KOs × 22 env responses, PGLS):
- emrB (K03446): 11/22 significant responses; strongest Ni (GeoROC) β = 8.45, t = 5.01, p = 6.0×10⁻⁷
- Metal-match test (Mann-Whitney, genus-level): p = 0.035 (KOs significantly associated with their annotated metal)

## Findings 15–16 — Co-occurrence networks (run_cooccurrence_analysis.py, partner_characterisation.py)

**Scripts:** `scripts/run_cooccurrence_analysis.py`, `scripts/partner_characterisation.py`  
**Inputs:** MicrobeAtlas OTU × sample presence-absence matrices (3 strata), `data/01_pgls_input_bacteria.csv`  
**Output:** `results/cooccurrence_pgls_results.csv`, `results/partner_characterisation_results.csv`

Key results:
- ALL stratum (n=1,572 genera): β_sig_pos_partners = 138.4, SE = 13.7, p = 3.4×10⁻²³
- SOIL stratum (n=1,547): β_sig_pos_partners = 210.5, SE = 15.3, p = 8.2×10⁻⁴¹
- Phi-degree (all strata): β = 15.2–16.5, p = 3.5×10⁻³²–9.9×10⁻³²
- Niche breadth correlation with partner count: Spearman ρ = 0.33–0.37 (partial analyses needed)
- Top-50 focal genus partners (soil): Firmicutes bias (39% of focal partners in top quartile vs 21% of control partners; note: REPORT Finding 16 reports Firmicutes as 40.4% of partner phylum composition vs Proteobacteria 39.9% — these are different statistics: 39%/21% = top-quartile membership fraction; 40.4% = Firmicutes share of all phylum assignments); φ > 0.3 threshold passed by 0.91% pairs

## Finding 17 — HGT direct evidence (hgt_direct_evidence.py)

**Script:** `scripts/hgt_direct_evidence.py`  
**Inputs:** `data/fritz_purvis_D_genome.csv`, NCBI GenBank plasmid/mobile-element annotations  
**Output:** `results/hgt_gene_tree_discordance.pdf`, `results/hgt_transposase_proximity.pdf`

Key results:
- MWU D: double-signal vs control KOs, p = 1.81×10⁻⁴ (main evidence line)
- Plasmid fraction (DS KOs): elevated (marginal p; publication-bias caveat noted in REPORT)
- Mobile-element proximity (DS KOs): marginal signal

## Q1 — Null category PGLS (null_category_pgls.py)

**Script:** `scripts/null_category_pgls.py` (or within `five_analyses.py`)  
**Inputs:** `data/01_pgls_input_bacteria.csv`, kbase.ke_pangenome KO density for 5 null KEGG categories  
**Output:** confirms NB18 results for ABC transporters, AMR, glycan, cell motility, TCS

Key results (all β ≈ 0, all q > 0.45):
- ABC transporters (non-metal): β = −0.0055, q = 0.457 (NS)
- AMR (beta-lactam): β = −0.0039, q = 0.505 (NS)
- Two-component systems: β = +0.0059, q = 0.457 (NS)

## Q2 — Cofactor overlap audit (cofactor_overlap_audit.py)

**Script:** `scripts/cofactor_overlap_audit.py`  
**Inputs:** `data/curated_mrg_ko_ids_v2.csv`, KEGG cofactor-related KO lists  
**Output:** cofactor overlap quantification

Key results:
- Metal KOs (140) overlapping cofactor category (382 KOs): 83/382 (21.7%)
- PGLS with 382-KO set (cofactors + vitamins): β = −0.029, same as cofactor-only result
- PGLS with 382 − 83 = 299 reduced set: β ≈ −0.029 (unchanged)

## Q3 — Carbohydrate metabolism reconciliation (kegg_category_ranking.py)

**Script:** `scripts/kegg_category_ranking.py`  
**Output:** geometric explanation (per-Mb density vs GapMind pathway completeness); labelled exploratory

## Q4 — Latitude mechanism tests (latitude_mechanism_tests.py, per_metal_bedrock_models.py)

**Scripts:** `scripts/latitude_mechanism_tests.py`, `scripts/per_metal_bedrock_models.py`  
**Inputs:** `data/genus_lat_env_covariates.csv`, GeoROC per-genus metal data  
**Output:** `data/latitude_mechanism_results.csv` (28 rows, Models A–N), `data/per_metal_pgls.csv`

Key results:
- Models A–I (9 mechanism tests): GeoROC composite β = +0.012, p = 2.2×10⁻⁴ (Cr and Co drive)
- J–M per-metal: Cr BH p = 6.7×10⁻⁹; Co BH p = 0.0084; all VIF < 2
- N series (redox proxy): Cr and Co unattenuated by soil moisture; SOM independently negative (β = −0.016, p = 6.8×10⁻⁵)
- Mafic score (ecotapestry, Model H): β = +0.009, p = 0.013 (corroborates GeoROC Cr)

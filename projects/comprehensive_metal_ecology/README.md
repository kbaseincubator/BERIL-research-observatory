# Comprehensive Metal Ecology

A rigorously pre-specified successor to `microbeatlas_metal_ecology`, using the
comprehensive evidence-tiered metal-gene list (730 KOs, 24 metals, 5 tiers) as
the primary gene set.

## Research Question

Does metal-gene density (KOs per Mb, Tier 1+2 evidence, 140 genes) negatively predict ecological niche breadth (Levins' standardised B) across bacterial genera, after controlling for genome size and phylogenetic non-independence (PGLS with Pagel's λ, GTDB r214 genus tree, n = 1,574 genera)?

Secondary questions: (P2) Does the pattern replicate in archaea? (P3) Does niche breadth predict soil metal concentration directly? Do individual functional categories (resistance, transport, cofactor) contribute equally?

## Authors

- **Heather MacGregor** — Lawrence Berkeley National Laboratory (ORCID: 0000-0003-1112-3009)

## Key differences from microbeatlas_metal_ecology

| Aspect | microbeatlas | comprehensive |
|--------|-------------|---------------|
| Gene set | ~200 KEGG-module KOs | 730 KOs (5 evidence tiers) |
| Evidence grading | None | Tier 1–3; BacMet2; FitnessBrowser |
| Pre-registration | Post-hoc framing | All tests locked before execution |
| Confounder discovery | Ad-hoc | Systematic BERDL namespace scan |
| Sensitivity analyses | Partial | Fully pre-specified subset comparisons |
| Interpretation table | None | INTERPRETATION_TABLE.md (confirmatory vs. exploratory) |

## Gene list

`data/curated_mrg_ko_ids_v2.csv` — 730 KOs, 24 metals, 5 evidence tiers.

Evidence tiers:
- **Tier 1** (32 KOs): Multi-source validated (BacMet2 + FitnessBrowser + clear KEGG)
- **Tier 2** (108 KOs): Clear KEGG definition, single source
- **Tier 2-Fitness** (116 KOs): FitnessBrowser validated, no KEGG module
- **Tier 3** (286 KOs): Ambiguous KEGG definitions — ambiguous assignments
- **Tier 3-BacMet** (188 KOs): BacMet2 curated, no cross-validation

The **primary analysis** uses the **Tier 1 + Tier 2** subset (140 KOs).

## Notebooks

| Notebook | Status | Purpose |
|----------|--------|---------|
| 00_gene_list_profile | Confirmatory | Profile 730-KO list; produce gene_list_summary.csv |
| 01_primary_pgls | **Confirmatory** | PGLS: metal-gene density → niche breadth (primary set) |
| 02_ngsa_replication | **Confirmatory** | Replicate primary PGLS in NGSA soil geochemistry |
| 03_tier_category_analysis | **Confirmatory** | Per-tier and per-category PGLS comparisons |
| 04_confound_checks | **Confirmatory** | Test pre-specified confounders |
| 05_sensitivity_analyses | **Confirmatory** | Gene-subset, tree, and threshold sensitivity |
| 06_confounder_discovery | Exploratory | BERDL namespace scan for new confounders |
| 07_marine_geol_proxies | Exploratory | Geological proxies and marine signal |
| 08_emp_niche_breadth | Exploratory | EMP 16S niche breadth PGLS (n=539, β=−0.019, p=0.099) |
| 09_bacdive_niche_breadth | Exploratory | BacDive geographic niche breadth PGLS (complete): β=+0.100, p≈0, n=752 — positive direction (geographic range ≠ habitat breadth) |
| 10_pfam_metal_qc | QC | Pfam/InterPro metal-binding domain validation (10/140 KOs) |
| 11_enigma_frc_replication | Exploratory | ENIGMA MAG-level site replication (n_wells=3; underpowered) |
| 12_ngsa_proper_replication | **Confirmatory** | P4 proper NGSA replication: niche breadth ~ NGSA metal conc (140-KO list) |
| 13_enigma_isolate_validation | Exploratory | ENIGMA isolate genomes: infeasible — no sample_id on isolates |
| 14_enigma_geochem_discovery | Exploratory | ENIGMA MAG geochemistry discovery + Spearman correlation (all available tables) |
| 25_split_magnitude_permutation | Exploratory | Split magnitude permutation: Δβ resistance/cofactor = 0.035259, emp_p = 0.0 (0/1000) |
| 26_interaction_test_jackknife | Exploratory | Interaction test (resistance vs cofactor split) and cofactor KO jackknife: all 4 KOs stable (β −0.016 to −0.029, all p < 0.001, no sign changes) |

## Scripts

All scripts are importable modules with full type hints and docstrings.

| Script | Purpose |
|--------|---------|
| `gene_list_utils.py` | Load + filter 730-KO gene list; named subsets |
| `pgls_utils.py` | dendropy PGLS with Pagel's lambda |
| `spatial_utils.py` | Haversine join, raster extraction, bbox filter |
| `niche_utils.py` | Levins' standardised niche breadth |
| `berdl_utils.py` | Spark session + BERDL table queries |
| `confounder_discovery.py` | BERDL namespace scan + coverage evaluation |

## Pre-registration

All confirmatory analyses are fully pre-specified in `RESEARCH_PLAN.md` before
any results were observed.  See `INTERPRETATION_TABLE.md` for the decision rules
that will govern interpretation.

## Confirmatory Test Labels

The pre-registered confirmatory tests are labelled P1–P3 in RESEARCH_PLAN.md:
- **P1**: Primary PGLS (bacteria, 140 KOs, kbase.ke_pangenome)
- **P2**: Replication in archaea
- **P3**: Australia-only NGSA soil-concentration replication (n=482; near-zero)

**P4** and **P5** are extended analyses developed after seeing P3 results — they are exploratory despite recovering the signal:
- **P4** (NB12): NGSA soil metal concentration predictor × AusMicrobiome genus panel
- **P5** (NB15): AusMicrobiome genomic KO density predictor (same DB as P1)

P4/P5 differ from the pre-registered P3 in predictor source and genus panel; both are labelled exploratory in REPORT.md and INTERPRETATION_TABLE.md.

## Reproduction

| Notebook category | Spark required? | Run locally from cached data? |
|-------------------|----------------|-------------------------------|
| NB01, NB02, NB05, NB08–NB10, NB16, NB18–NB26 | No | Yes — reads `data/*.csv` |
| NB03, NB04, NB17 | Yes (kbase.ke_pangenome / kescience_mgnify) | Cached results in `data/`; notebooks display cached outputs |
| NB06, NB07, NB11–NB15 | Yes | Not available without JupyterHub Spark session |

To run locally (no Spark): `jupyter-nbconvert --to notebook --execute --inplace <notebook.ipynb>`

Minimum Python dependencies: `pandas`, `numpy`, `scipy`, `statsmodels`, `dendropy`, `matplotlib`, `scikit-learn`

## Status

Analysis — report drafted (Findings 1–19), awaiting `/berdl-review` and `/submit`.

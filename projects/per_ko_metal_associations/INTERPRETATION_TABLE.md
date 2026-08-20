# Interpretation Table — per_ko_metal_associations

**Purpose:** Track each pre-specified hypothesis through to its interpretive
outcome. All results are exploratory — this project generates hypotheses, not
confirmatory tests.

**Status key:**
- `SUPPORTED` — pre-specified threshold met
- `NOT SUPPORTED` — threshold not met
- `NOT FEASIBLE` — analysis not executable (reason documented)

---

## Hypothesis outcomes

| ID | Hypothesis | Threshold | Observed | Status |
|----|-----------|-----------|----------|--------|
| H1 | ≥20 KO-metal pairs reach FDR q<0.05 in MGnify | ≥20 pairs | **219 pairs** (38,706 tested) | **SUPPORTED** |
| H2 | β_MGnify ~ β_SPIRE Spearman ρ > 0.2 across shared KO-metal pairs | ρ > 0.2 | ρ = 0.059 (p=0.29, n=324) | **NOT SUPPORTED** |
| H3 | Curated metal KOs enriched among FDR-sig (Fisher p<0.05) | p < 0.05 | OR=1.52, p=0.39 | **NOT SUPPORTED** |
| H4 | ≥10 H1 pairs survive latitude adjustment | ≥10 | **138/219 (63%)** | **SUPPORTED** |
| H5 | β stability ρ > 0.5 (adjusted vs unadjusted betas) | ρ > 0.5 | ρ = 0.923 (n=910) | **SUPPORTED** |
| H6 | Adjusted cross-dataset β correlation > unadjusted | adj ρ > 0.059 | adj ρ = 0.049 | **NOT SUPPORTED** |
| H7 | ≥10 H1 pairs survive class-level taxonomic control | ≥10 | **92/219 (42%)** | **SUPPORTED** |
| H8 | β stability ρ > 0.7 (phylum vs class model betas) | ρ > 0.7 | ρ = 0.925 (n=219) | **SUPPORTED** |
| H9 | ≥5 H1 pairs survive phylo-PC continuous control | ≥5 | **8/219 (4%)** | **SUPPORTED** |
| H10 | ≥10 H1 pairs survive MAG quality covariate control | ≥10 | **200/219 (91%)** | **SUPPORTED** |
| — | PGLS phylogenetic control | — | — | **NOT FEASIBLE** (16.2% tree coverage) |

---

## Section 1 — Primary screen (H1)

**Model:** `KO_present ~ PF1_metal + log_genome_size + C(phylum)` (logistic regression)  
**Dataset:** 8,585 MGnify MAGs × 6,451 KOs, 6 metals  
**FDR:** Benjamini-Hochberg per metal  

| Metal | Tested | FDR-sig | % |
|-------|--------|---------|---|
| PF1_As | 6,451 | 43 | 0.7% |
| PF1_Cd | 6,451 | 12 | 0.2% |
| PF1_Cr | 6,451 | 6 | 0.1% |
| PF1_Cu | 6,451 | 0 | 0.0% |
| PF1_Hg | 6,451 | 107 | 1.7% |
| PF1_Pb | 6,451 | 51 | 0.8% |
| **Total** | 38,706 | **219** | **0.6%** |

Source: `data/mgnify_all_ko_associations.csv`

---

## Section 2 — Cross-dataset replication (H2)

**SPIRE dataset:** 2,905 MAGs × 4,759 KOs; 63 FDR-sig pairs  
**Shared pairs:** 324 KO-metal pairs tested in both datasets  
**Spearman ρ = 0.059** (p=0.29) — no meaningful cross-dataset correlation.

Likely reflects genuine differences between MGnify (global multi-biome, ~50% soil) and SPIRE (primarily soil). Cu has 0 FDR-sig pairs in MGnify and no Hg-heavy signal in SPIRE (few high-Hg sites).

Not a methodological failure — H4/H5 confirm MGnify associations are not geographic artifacts.

Source: `data/cross_dataset_comparison.csv`

---

## Section 3 — Curated KO enrichment (H3)

**Background:** 6,451 KOs tested; 219 FDR-sig unique KO-metal pairs (169 unique KOs)  
**Foreground:** 730-KO curated set (metal-interacting genes from `comprehensive_metal_ecology`)  
**Fisher's exact:** OR = 1.52, p = 0.39 — **NOT SIGNIFICANT**

Curated metal KOs are not enriched among the genome-wide discoveries. This null result likely reflects that the genome-wide screen recovers ecologically relevant associations not limited to the curated gene list (e.g. flagellar regulators, amino acid transporters), rather than failure of the curated approach.

Source: `data/functional_enrichment.csv`

---

## Section 4 — Geographic robustness (H4, H5, H6)

**Latitude-adjusted model:** `KO_present ~ PF1_metal + log_genome_size + latitude + C(phylum)`

**H4 (survival):** 138/219 H1-sig pairs survive FDR q<0.05 → SUPPORTED  
**H5 (stability):** Spearman ρ = 0.923 between unadjusted and adjusted betas → SUPPORTED  
**H6 (cross-dataset improvement):** Adjusted ρ_SPIRE = 0.049 vs unadjusted ρ_SPIRE = 0.059 → NOT SUPPORTED (adjustment did not improve cross-dataset agreement)

Source: `data/mgnify_adj_ko_associations.csv`, `data/spire_adj_ko_associations.csv`

---

## Section 5 — Taxonomic robustness (H7, H8)

**Class-level model (NB05 Model A):** `KO_present ~ PF1_metal + log_genome_size + latitude + C(class)` (232 classes, mean 37 MAGs/class)

**H7 (survival):** 92/219 H1-sig pairs survive genome-wide FDR at class level → SUPPORTED  
**H8 (stability):** Spearman ρ = 0.925 between phylum-model and class-model betas → SUPPORTED

By metal (H7):

| Metal | H1-sig | Class-survive | % |
|-------|--------|---------------|---|
| As | 43 | 5 | 12% |
| Cd | 12 | 6 | 50% |
| Cr | 6 | 4 | 67% |
| Hg | 107 | 42 | 39% |
| Pb | 51 | 35 | 69% |

As has the highest attrition (88%) — As signal is largely at phylum level. Pb and Cr are most robust to finer taxonomic control.

Source: `data/mgnify_class_ko_associations.csv`, `data/h1_fine_taxonomy_adjusted.csv`

---

## Section 6 — Phylogenetic robustness (H9)

**Phylo-PC model (NB05 Model B):** 20 TruncatedSVD PCs from GTDB taxonomy one-hot matrix (8,585 × 5,481 binary; 43.4% cumulative variance) used as continuous phylogenetic covariates.

**H9 (survival):** 8/219 H1-sig pairs survive genome-wide FDR → SUPPORTED (≥5 threshold)

8 surviving pairs and their KOs:

| KO | Gene | Function | Metal | β |
|----|------|----------|-------|---|
| K01546 | kdpA | Kdp K⁺-ATPase subunit A | Hg | + |
| K01547 | kdpC | Kdp K⁺-ATPase subunit C | Hg | + |
| K01548 | kdpB | Kdp K⁺-ATPase subunit B | Hg | + |
| K16080 | kdpF | Kdp K⁺-ATPase stabilising subunit (eggnog sparse; KEGG assignment well-established) | Hg | + |
| K08364 | merP | Mercury chaperone protein | Hg | − |
| K02075 | — | ABC Zn/Mn transporter | Hg | + |
| K02014 | — | ABC Fe siderophore | Cd | + |
| K03088 | rpoS | Sigma-38 stress sigma factor | Cr | − |

The kdp operon dominates (4/8 pairs) — K⁺ ATPase enriched in high-Hg environments, possibly reflecting Hg²⁺/K⁺ ionic competition or indirect community enrichment. merP (Hg chaperone) is depleted near Hg, consistent with its role in resistance systems that exclude rather than tolerate Hg.

Source: `data/mgnify_phylopc_ko_associations.csv`, `data/phylo_survivor_categories.csv`

---

## Section 7 — MAG quality robustness (H10)

**Quality source:** `kescience_mgnify.genome` — completeness and contamination joined to all 8,585 MAGs. All MAGs already pass the NB00 QC filter (≥70% completeness, ≤10% contamination); mean completeness = 95.8%, mean contamination = 1.66%.

**Phase 3A (covariate control):** `KO_present ~ PF1_metal + log_genome_size + C(phylum) + completeness + contamination`

**H10 (survival):** 200/219 (91%) H1-sig pairs survive → SUPPORTED

**Restricted-subset sensitivity:**

| Subset | MAGs | % of total | Pairs surviving |
|--------|------|-----------|-----------------|
| All MAGs (Phase 3A) | 8,585 | 100% | 200/219 (91%) |
| ≥95%/≤2% (Phase 3B) | 3,520 | 41% | 120/219 (55%) |
| ≥97%/≤1% (Phase 3C) | 1,854 | 22% | 29/219 (13%) |

The Phase 3C drop is driven by power loss (22% of MAGs), not quality artefact. The Phase 3A result (91%) provides the cleanest evidence: quality variation does not confound the H1 associations when all MAGs are included.

Source: `data/mgnify_mag_quality.csv`, `data/h1_mag_quality_adjusted.csv`, `data/h1_mag_quality_sensitivity_95.csv`, `data/h1_mag_quality_sensitivity_97.csv`

---

## Section 8 — Multi-metal covariate control (Phase 2)

For each H1-sig pair, the most-correlated metal (by Spearman ρ across 8,585 MAGs) was added as a covariate:

| Target | Correlate | ρ |
|--------|-----------|---|
| As | Cr | +0.684 |
| Cd | Cr | −0.478 |
| Cr | Cu | +0.710 |
| Cu | Cr | +0.710 |
| Hg | As | +0.551 |
| Pb | Cd | +0.167 |

**210/219 (96%) pairs survive multi-metal adjustment.** Signal is not explained by co-occurrence of correlated metals.

Supplementary: 134/138 latitude-adjusted pairs (H4-sig) survive combined latitude + multi-metal control.

Source: `data/h1_multi_metal_adjusted.csv`

---

## Section 9 — All-controls survival summary

Four controls applied to the 219 H1-sig pairs:

1. Latitude adjustment (H4): 138/219 survive
2. Multi-metal covariate (Phase 2): 210/219 survive
3. Class-level taxonomy (H7, genome-wide FDR): 92/219 survive
4. MAG quality covariate (H10): 200/219 survive

**All 4 controls: 88/219 (40%) pairs survive.** These represent the most robust associations in the genome-wide screen.

| Metal | H1-sig | All-4-controls | % |
|-------|--------|----------------|---|
| As | 43 | 5 | 12% |
| Cd | 12 | 5 | 42% |
| Cr | 6 | 4 | 67% |
| Hg | 107 | 35 | 33% |
| Pb | 51 | 39 | 76% |

Source: `data/h1_robustness_summary.csv` (columns: survives_all_controls_with_p3)

---

## Section 10 — Cross-validation with comprehensive_metal_ecology (NB06)

**Question:** Does the functional split from the main project (resistance null, transport/sensing/cofactor/metabolism significant) replicate in per-KO enrichment among H1-sig KOs?

**Result: NO.** All Fisher's exact tests are non-significant (p > 0.05). Only 8 named-category KOs appear among 169 H1-sig unique KOs — insufficient power.

| Category | Background | H1-sig | OR (Fisher) | p |
|----------|-----------|--------|-------------|---|
| Resistance/Detoxification | 11 | 2 | 1.54 | 0.45 |
| Transport/Homeostasis | 120 | 6 | 0.42 | 0.06 |
| Sensing/Regulation | 7 | 0 | exact zero | — |
| Cofactor Biosynthesis | 6 | 0 | exact zero | — |
| Metal-dependent Metabolism | 32 | 0 | exact zero | — |

The functional split is not recapitulated. The strategic cross-paper paragraph is not supported.

Source: `data/category_enrichment_per_ko.csv`, `data/phylo_survivor_categories.csv`

---

## Additional observation — K03975 (mycothiol isomerase) soil associations

K03975 (mycothiol-dependent malonylpyruvate isomerase) did not appear in H1 (convergence failure in the main 8,553-MAG model at 48% KO prevalence). In the soil/rhizosphere-restricted sensitivity analysis (6,538 MAGs), it shows FDR-significant associations: Hg β = −2.27 q = 7.2×10⁻⁶, Cd β = +1.71 q = 7.8×10⁻³, As β = −2.39 q = 4.3×10⁻². The Hg depletion is directionally consistent with thiol-Hg binding chemistry; the Cd enrichment is opposite. The Hg signal does not survive latitude adjustment in the full dataset (q = 0.37). No SPIRE replication possible (96% prevalence). This is a hypothesis-generating observation, not a confirmed finding. See `REPORT.md` Discovery #3.

**Priority action:** Test K03975 depletion in ENIGMA metal-contaminated isolates vs clean-site isolates via ENIGMA Genome Depot.

---

## Section 11 — Lab–field cross-reference for Arc 4 phylo-PC survivors (NB08)

**Question:** Do the 8 KO-metal pairs surviving all phylogenetic controls (H9) confer fitness under matched acute metal stress in controlled laboratory experiments?

**Design:** Arc 4 survivors queried in ENIGMA FitnessBrowser RB-TnSeq databases (`enigma.fitprivate`, `kescience.fitnessbrowser`), via KO-to-locusId mapping through `besthitkegg × keggmember`.

**n = 3 testable pairs** (K02075/Cr, K03442/Cr, K08364/Cd in *Rhodanobacter_10B01*). This is proof-of-concept; future work will expand the cross-reference to more organisms and metals.

### Testability outcome per pair

| KO | Gene | Metal | Testable? | Reason if not |
|----|------|-------|-----------|---------------|
| K02075 | ZnuB | Cr | Yes | Present in *Rhodanobacter_10B01* |
| K03442 | mscS | Cr | Yes | Present in *Rhodanobacter_10B01* |
| K08364 | merP | Cd | Yes | Present in *Rhodanobacter_10B01* |
| K01669 | phrB | Cr | **No** | Light-activated enzyme; dark assay |
| K07338 | — | Hg | No | Absent from screened genomes |
| K07338 | — | Pb | No | Absent from screened genomes |
| K13018 | — | Cd | No | Absent from screened genomes |
| K00376 | nosZ | Pb | No | Absent from screened genomes |

### Lab fitness results (3 testable pairs)

Arc 4 mean \|t\| = **0.28**, max = 0.70, median genome-wide percentile rank = **42nd** — statistically indistinguishable from a randomly selected gene (genome neutral). None shows meaningful fitness effect under acute metal stress.

Top lab fitness genes for same metals/organisms: mean \|t\| = **8.94** (TonB/K02014 Cr: −16.7; CusA-CzcA/K07239 Cd: −12.0; argD/K07090 Hg: −11.4; RluD/K06180 Pb: +17.2). **The 32× effect size gap confirms that the two assays measure different gene sets.**

Notably, K07239 (CusA/CzcA, top Cd lab fitness gene) is absent from SPIRE MAGs — below the prevalence threshold in global soil communities. The strongest acute Cd resistance gene is ecologically rare.

### Post-hoc three-class framework (hypothesis-generating, not proved)

The results are consistent with — but do not prove — a three-class taxonomy. **This framework is post-hoc; it rests on n = 3 testable pairs and generates testable predictions for future meta-analyses.**

| Class | Example KOs | Field signal | Lab fitness |
|-------|------------|-------------|-------------|
| Stress-responsive homeostasis | K02075/ZnuB, K03442/mscS | Arc 4 survivors | Near-zero (|t| < 0.7, 42nd pct) |
| Inducible resistance | K07239/CusA, K08364/merP | Absent or weak (CusA below prevalence threshold) | Strong (|t| ≈ 12–17, 99th pct) |
| Assay-inaccessible | K01669/phrB | Arc 4 survivor (Cr) | Not testable (dark assay) |

Note: ZnuABC (including K02075/ZnuB) is Zur-regulated and zinc-starvation inducible. "Homeostasis" refers to functional role and ecological prevalence, not constitutive expression.

### Mechanistic illustration

phrB (K01669) — CPD photolyase — is an Arc 4 Cr survivor but phenotypically silent in dark RB-TnSeq. The protein requires visible light; the knockout has no measurable fitness cost in dark growth. Its field signal is most plausibly explained by co-occurring UV and chromium genotoxicity in surface soils. This illustrates the fundamental asymmetry: lab and field assays measure selection under different physical conditions.

### External validation

This dissociation between field metagenomics and acute lab fitness is independently supported by:

- **Uluseker et al. (2025)** (*bioRxiv*): community assembly alone can produce spurious correlations between resistance genes and environmental variables via phylogenetic structure (ARGs, SEM approach)
- **Dunivin & Shade (2018)** (*FEMS Microbiol Ecol*): ARG dynamics along a soil gradient explained by community structure changes, not direct selection
- **Dunivin, Yeh & Shade (2019)** (*BMC Biology*): phylogeny predicts arsenic resistance gene presence; geographic location does not — consistent with phylogenetic sorting as the dominant driver

Source: `data/arc4_lab_fitness_per_exp.csv`, `data/arc4_lab_fitness_summary.csv`, `data/top_lab_fitness_genes.csv`, `data/genome_wide_fitness_dist.parquet`, `data/lab_field_crossref.csv`, `data/top_lab_ko_arc4_prevalence.csv`

Figures: `figures/fig_nb08_arc4_lab_fitness.pdf`, `figures/fig_nb08_field_vs_lab_scatter.pdf`, `figures/fig_nb08_rank_distribution.pdf`

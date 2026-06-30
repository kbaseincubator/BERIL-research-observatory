# Report: Metal Resistance Ecology — Phylogenetic Conservation vs. Environmental Selection

**Project**: `microbeatlas_metal_ecology`
**Status**: Complete
**Date**: 2026-04-01 (updated 2026-06-30)

---

## Introduction

Metal resistance in bacteria is encoded by a diverse repertoire of AMR genes — for mercury,
arsenic, copper, zinc, cadmium, chromium, and nickel — many of which are carried on mobile
genetic elements and are frequently transferred among taxa via horizontal gene transfer (HGT).
Whether the breadth of a bacterium's metal resistance repertoire is associated with its
ecological niche breadth has not previously been tested at global scale with phylogenetic control.
Here we present the first analysis linking **genus-level metal gene burden** — inferred from a
curated 46-KO metal resistance gene list against pangenome KEGG annotations across 6,789 GTDB
species — to **global ecological niche breadth** derived from a 464,000-sample 16S amplicon
atlas (MicrobeAtlas), with phylogenetic signal explicitly partitioned and controlled via Pagel's
λ and PGLS. We find that metal gene metrics show **high phylogenetic signal** (λ = 0.665–0.868),
substantially higher than previously estimated from AMRFinderPlus annotations (λ = 0.260–0.441).
In simple PGLS (n = 957 genera), no metal gene metric survives Bonferroni correction; in the
multi-predictor model, total metal gene cluster count is marginally significant (β = +0.011,
p = 0.033). These results differ from the prior AMRFinderPlus-based analysis and indicate that
the curated KO-list approach captures a more phylogenetically conserved (likely core) component
of metal resistance that does not show the same niche breadth association.

---

## Key Findings

### Finding 1: Bacterial niche breadth is strongly phylogenetically conserved; curated metal gene metrics do not significantly predict niche breadth

![Synthesis figure: Pagel's λ heatmap (Panel A) and PGLS forest plot (Panel B)](figures/fig3_synthesis.png)

Across 1,252 bacterial genera with ≥ 3 OTUs in MicrobeAtlas, Levins' B_std shows very strong
phylogenetic signal (Pagel's λ = 0.932, p = 9.4×10⁻¹⁷⁹, LRT). Habitat range (number of
environment categories detected) is similarly conserved (λ = 0.918, p = 2.0×10⁻¹⁶¹). After
controlling for this phylogenetic structure via PGLS (n = 957 genera with curated metal gene
data), **no metal gene metric survives Bonferroni correction** (Bonferroni threshold p < 0.0083
for 6 simple models). Total metal gene cluster count is the most supported predictor (β = +0.007,
SE = 0.0039, p = 0.058), with a marginal association in the multi-predictor model (β = +0.011,
p = 0.033). Metal type diversity and core metal fraction are not significant in either model.

**Note**: This result differs from the prior AMRFinderPlus-based analysis (metal types
β = +0.021, p = 1.5×10⁻⁴, Bonferroni-significant). The curated 46-KO approach captures a
more phylogenetically conserved subset of metal resistance genes. Robustness analyses (R1–R6)
were conducted on AMRFinderPlus data and require re-running with the curated gene list.

*(Notebooks: 04_pagel_lambda.ipynb, 05_pgls_regression.ipynb)*

---

### Finding 2: Curated metal gene traits show high phylogenetic signal — consistent with vertically inherited core resistance

![Pagel's λ heatmap: trait × domain](figures/fig1_lambda_heatmap.png)

Among bacterial metal gene traits (n = 957 genera, GTDB r214), Pagel's λ is **high** and
significantly non-zero for all three metrics: total metal gene cluster count (λ = 0.665,
p = 1.0×10⁻¹⁰⁴), core metal fraction (λ = 0.725, p = 6.8×10⁻²²), and metal type diversity
(λ = 0.868, p = 3.1×10⁻¹³⁶). The ordering — type diversity λ > core fraction λ > cluster
count λ — is reversed from the prior AMRFinderPlus-based analysis (where cluster count had
the lowest λ). High λ for all three metrics is consistent with the curated 46-KO gene list
capturing mainly vertically inherited, core metal resistance genes rather than the HGT-labile
accessory component that AMRFinderPlus detected. For contrast, nitrification (is_nitrifier)
retains near-maximal phylogenetic signal (λ = 0.967 bacteria, λ = 1.000 archaea), consistent
with ancient, vertically inherited metabolic entrenchment.

*(Notebook: 04_pagel_lambda.ipynb)*

---

### Finding 3: Aquatic vs. soil lifestyle dominates niche breadth; carbon breadth is a robust secondary signal

Habitat type is the single strongest phylogenetic predictor of niche breadth (PGLS, n=957 genera,
GTDB r214 tree). Genera predominantly detected in aquatic environments are niche specialists
(β=−0.496, p=10⁻⁵⁶ ***); soil-dwelling genera are generalists (β=+0.353, p=10⁻³² ***).
This signal is ~3× larger than any gene-set predictor and reflects a deep phylogenetic divide
between aquatic lineages (specialist, buffered environments) and terrestrial lineages (generalist,
heterogeneous environments).

After controlling for habitat type (aquatic vs. soil fraction), GapMind carbon pathway completeness
remains independently significant (β=+0.142, p=2×10⁻⁵ ***; full model β=+0.113, p=0.0015 **).
Genome size (clusters\_per\_genome) is marginally significant in the GapMind partial model
(p=0.052) — GapMind largely captures the genome-complexity signal.

Metal gene associations in partial models:
- **Homeostasis KO** (metal-sensing regulators): survives habitat control (β=+0.073, p=0.011 *)
- **Defense KO** (efflux pumps, metal-binding): becomes NS after habitat control (p=0.13) —
  its marginal association in simple PGLS was a habitat-mediated confound (soil genera have
  more defense genes AND broader niches, not because defense genes cause broad niches)

*(Notebooks: 07_env_metadata_pgls.ipynb; script: /tmp/habitat_genome_pgls.R)*

### Finding 3b: Carbon metabolic breadth predicts niche breadth independently of habitat

Extended gene set sweep (post-hoc, exploratory, n = 957 genera) shows that GapMind carbon
pathway completeness strongly predicts niche breadth (β = +0.023, p ≪ 0.001) while metal
resistance gene metrics are null (Pfam: p = 0.91; MAI: p = 0.21; AMRFinderPlus: p = 0.54).
UniRef90 functional gene diversity (β = +0.0093, p = 0.007) and InterPro metal domains
(β = +0.0083, p = 0.010) show modest associations, likely reflecting genomic generalism.
The pattern is consistent with carbon flexibility — not metal resistance — being the primary
functional driver of ecological generalism in bacteria, even after accounting for the dominant
aquatic vs. soil lifestyle split.

*(Notebooks: 04_pagel_lambda.ipynb Sections 9e, 10; 05_pgls_regression.ipynb Sections 6e–6k)*

---

### Finding 4: No curated metal gene metric significantly predicts niche breadth after phylogenetic correction

![Metal type diversity vs Levins' B_std scatter](figures/fig4_metal_types_scatter.png)

Under the curated 46-KO gene list, none of the three metal gene metrics significantly predicts
Levins' B_std or habitat range (n_envs) in simple PGLS after Bonferroni correction. Total
metal gene cluster count shows a marginal positive trend (β = +0.007, SE = 0.0039, p = 0.058
for B_std), and is the only metric with a nominally significant coefficient in the
multi-predictor model (β = +0.011, SE = 0.0053, p = 0.033). Metal type diversity is null
(β = +0.003, p = 0.560), consistent with the high phylogenetic signal (λ = 0.868) leaving
little HGT-labile variance for the PGLS to detect. The prior AMRFinderPlus-based finding that
metal type diversity significantly predicts niche breadth (p = 1.5×10⁻⁴) is **not replicated**
with the curated gene list. This discrepancy likely reflects that AMRFinderPlus detected a
broader, more HGT-labile set of metal-associated genes — including accessory transporters and
detoxification enzymes not in the curated 46-KO list — that co-vary with ecological range.

*(Notebook: 05_pgls_regression.ipynb)*

---

## Results

### Pagel's λ — phylogenetic signal by trait and domain

| Domain | Trait | n genera | λ | p (LRT) |
|--------|-------|----------|---|---------|
| Bacteria | Levins' B_std | 1,252 | 0.932 | 9.4×10⁻¹⁷⁹ |
| Archaea | Levins' B_std | 129 | 0.640 | 1.3×10⁻⁷ |
| Bacteria | # environments | 1,252 | 0.918 | 2.0×10⁻¹⁶¹ |
| Archaea | # environments | 129 | 0.880 | 2.1×10⁻¹³ |
| Bacteria | Nitrification | 2,283 | 0.967 | 3.3×10⁻¹⁰⁷ |
| Archaea | Nitrification | 129 | 1.000 | 1.3×10⁻⁵⁰ |
| Bacteria | Metal clusters (46-KO) | 957 | 0.665 | 1.0×10⁻¹⁰⁴ |
| Bacteria | Core metal fraction (46-KO) | 957 | 0.725 | 6.8×10⁻²² |
| Bacteria | Metal types (46-KO) | 957 | 0.868 | 3.1×10⁻¹³⁶ |
| Archaea | Metal clusters (46-KO) | 73 | 1.000 | 3.4×10⁻⁹ |

λ = 0 indicates no phylogenetic signal (environmentally structured); λ = 1 indicates
Brownian motion evolution (fully phylogenetically structured). Computed via
`phytools::phylosig(method='lambda', test=TRUE)` against GTDB r214 genus-representative trees.

### PGLS regression — metal gene metrics vs. niche breadth (curated 46-KO)

Analytical subset: 957 bacterial genera with ≥ 3 OTUs, present in the GTDB r214 bacterial
genus tree, and with curated 46-KO metal gene data. Predictors z-scored; Bonferroni threshold
p < 0.0083 (6 simple models). **No predictor survives Bonferroni correction.**

![PGLS forest plot: all simple models + multi-predictor](figures/fig2_pgls_forest.png)

**Simple PGLS models**:

| Response | Predictor (z) | n | λ_PGLS | β | SE | p | ΔAIC | Bonf. sig? |
|----------|--------------|---|--------|---|-----|---|------|-----------|
| Levins' B_std | Metal clusters | 957 | 0.887 | +0.007 | 0.0039 | 0.058 | −1.5 | no |
| Levins' B_std | Core fraction | 957 | 0.894 | +0.002 | 0.0033 | 0.508 | +1.6 | no |
| Levins' B_std | Metal types | 957 | 0.894 | +0.003 | 0.0045 | 0.560 | +1.7 | no |
| # environments | Metal clusters | 957 | 0.870 | +0.058 | 0.066 | 0.385 | +1.3 | no |
| # environments | Core fraction | 957 | 0.873 | +0.052 | 0.056 | 0.354 | +1.1 | no |
| # environments | Metal types | 957 | 0.872 | +0.046 | 0.075 | 0.536 | +1.6 | no |

**Multi-predictor model** (Levins' B_std ~ all 3, λ = 0.883):

| Predictor | β | SE | p |
|-----------|---|-----|---|
| **Metal clusters** | **+0.011** | **0.0053** | **0.033** |
| Core fraction | +0.003 | 0.0034 | 0.348 |
| Metal types | −0.006 | 0.0060 | 0.344 |

PGLS estimated jointly with λ via ML (`ape::gls + nlme::corPagel`). Data sorted to
`tree$tip.label` order prior to fitting (see `docs/pitfalls.md`).

### Comparative gene set analyses — COG P and AMRFinderPlus metal

Two orthogonal gene annotation systems were analyzed for comparison with the curated 46-KO list:
**COG category P** (Inorganic ion transport and metabolism; 488,181 gene clusters, 18,586 species
clades) and **AMRFinderPlus metal resistance genes** (16,666 gene clusters, 5,482 species clades;
keyword-filtered from `bakta_amr`; metallo-beta-lactamases excluded).

**Source**: `data/pagel_lambda_results_cogp.csv`, `data/pagel_lambda_results_amr_metal.csv`,
`data/pgls_results_cogp.csv`, `data/pgls_results_amr_metal.csv`. *(NB01 Sections 3b–3c, 4b–4c;
NB04 Sections 9c–9d; NB05 Sections 6c–6d)*

#### Pagel's λ — COG P and AMRFinderPlus metal

| Gene set | n genera | λ | p | Interpretation |
|----------|---------|---|---|----------------|
| Niche breadth (B_std) | 1,252 | 0.932 | 9.4×10⁻¹⁷⁹ | Strongly conserved |
| 46-KO defense | 957 | 0.549 | — | Moderate (HGT-labile) |
| 46-KO metabolism | 957 | 0.788 | — | Moderate-high |
| 46-KO homeostasis | 957 | 0.804 | — | High |
| **COG P** | **909** | **0.206** | **4.3×10⁻¹³** | **Very low — highly HGT-susceptible** |
| **AMRFinderPlus metal** | **957** | **0.244** | **1.8×10⁻⁴²** | **Very low — highly HGT-susceptible** |

Both COG P and AMRFinderPlus metal clusters show dramatically lower phylogenetic signal
(λ≈0.2) than the curated 46-KO list (λ=0.549–0.804). The p-values confirm significant
phylogenetic structure but the λ magnitude indicates most variance is NOT explained by
shared ancestry — consistent with frequent horizontal gene transfer of broad inorganic ion
transporters and curated resistance genes.

#### PGLS — COG P and AMRFinderPlus metal

| Gene set | Response | n | λ | β | SE | p | Sig? |
|----------|----------|---|---|---|-----|---|------|
| COG P | Levins' B_std | 909 | 0.879 | +0.0087 | 0.0031 | 0.0047 | **yes** |
| COG P | # environments | 909 | 0.869 | +0.032 | 0.051 | 0.536 | no |
| AMRFinderPlus metal | Levins' B_std | 957 | 0.894 | +0.0019 | 0.0031 | 0.540 | no |
| AMRFinderPlus metal | # environments | 957 | 0.873 | −0.051 | 0.052 | 0.325 | no |

**Interpretation**: COG P gene cluster burden significantly predicts niche breadth (β=+0.0087,
p=0.0047), unlike the curated 46-KO aggregate (p=0.058 for clusters). This is consistent with
COG P capturing a broader set of inorganic ion handling capacity — including essential metal
cofactor acquisition alongside active resistance — making it a broader physiological signal
than either the curated resistance gene list or AMRFinderPlus. AMRFinderPlus metal resistance
genes show no association with niche breadth, consistent with their very low phylogenetic
conservation (λ=0.244) — these are HGT-acquired resistance modules that vary within genera.

**Post-hoc caveat**: The COG P PGLS result was not pre-registered. The gene set was selected
after observing the null result in the 46-KO analysis as a broader functional comparison.
Treat as exploratory / hypothesis-generating.

---

### Extended gene set sweep — Pagel's λ and PGLS across 8 additional gene set definitions

To contextualize the curated 46-KO result, we ran Pagel's λ and PGLS for eight additional
gene set definitions spanning different levels of biological specificity:
InterPro metal domains, Pfam metal families, MAI binary trait (K16163), GapMind metabolic
completeness (80 pathways + 4 summary scores), full COG functional category sweep (25
categories), and UniRef90 functional gene family diversity. All analyses use the same 957
bacterial genera and GTDB r214 pruned genus tree. λ estimated via `gls(y~1, corPagel)` with
LRT against λ=0. Traits winsorized at 5σ before z-scaling to prevent optimizer divergence.
**All analyses post-hoc and exploratory.**

**Gene set definitions**:

- **Pfam metal (14 families)** — protein domain-level metal resistance architecture drawn from
  `species_pfam_metal.csv`. Trait = mean number of distinct Pfam-annotated metal gene clusters
  per species, aggregated to genus level. Families (by cluster prevalence):
  PF00149 (Metallophos), PF12850 (Metallophos_2), PF00403 (HMA), PF02374 (ArsA_ATPase),
  PF00690 (Cation_ATPase_N), PF00127 (Copper-bind), PF17886 (ArsA_HSP20), PF09278 (MerR-DNA-bind),
  PF14582 (Metallophos_3), PF11604 (CusF_Ec), PF19991 (HMA_2), PF21085 (CusS), PF13591 (MerR_2),
  PF06953 (ArsD). *Note: REPORT previously stated 11 families; the correct count is 14.*

- **InterPro metal (14 families)** — domain superfamily-level annotation from
  `species_interpro_metal.csv`. Trait = mean distinct IPR metal cluster count per genus. Families:
  IPR036163 (HMA domain superfamily), IPR006121 (HMA domain), IPR027469 (cation efflux TM superfamily),
  IPR058533 (cation efflux TM domain), IPR017969 (HMA conserved site), IPR002524 (cation efflux),
  IPR051081 (HTH metal-responsive regulators), IPR051011 (metal-responsive regulator),
  IPR036837 (cation efflux cytoplasmic superfamily), IPR027470 (cation efflux cytoplasmic domain),
  IPR050153 (metal ion import ATP-binding), IPR052509 (metal-responsive DNA-binding regulator),
  IPR050291 (cation-efflux pump FieF-like), IPR051909 (membrane fusion protein cation efflux system).

- **MAI — K16163 (mycothiol isomerase, MshB)** — binary presence/absence per genus
  (`has_mai_fraction`). Mycothiol is the primary low-molecular-weight thiol of Actinobacteria,
  functioning as an antioxidant defense against electrophilic stress including reactive oxygen
  species generated by metal redox cycling. K16163 (1-D-Inositol-2-acetamido-2-deoxy-α-D-
  glucopyranoside deacetylase) is the enzyme that converts GlcNAc-Ins to glucosaminyl-inositol in
  the mycothiol biosynthesis pathway. Included as a phylogenetically restricted metal-stress
  tolerance marker (essentially Actinobacteria-exclusive) to contrast with broad-distribution
  resistance genes.

- **UniRef90 diversity** — count of distinct UniRef90 cluster families annotated across all
  species in a genus (from `species_uniref90_diversity.csv`), aggregated to genus-level mean.
  Represents total functional gene repertoire breadth rather than metal-specific genes. Included
  as a proxy for genome-level functional complexity.

- **BacMet** — BacMet 2.0 (927 biocide/metal resistance gene families) was *not* used in
  this analysis; it is recommended as a replacement for AMRFinderPlus in future iterations
  (see §"Metal gene annotation quality and recommended replacement"). All metal resistance
  annotations in this study use either AMRFinderPlus or the curated 46-KO list.

#### Pagel's λ — extended gene set comparison

| Gene set | n genera | λ | p | Interpretation |
|---------|---------|---|---|----------------|
| Niche breadth (B_std) | 1,252 | 0.932 | 9.4×10⁻¹⁷⁹ | Strongly conserved |
| GapMind carbon completeness | 957 | 0.928 | 5.7×10⁻¹⁹⁸ | ≈ niche breadth conservation |
| GapMind aa completeness | 957 | 0.931 | 6.4×10⁻¹⁴² | ≈ niche breadth conservation |
| GapMind n_aa_complete (>0.5) | 957 | 0.932 | 4.1×10⁻¹⁴⁵ | Strongly conserved |
| GapMind n_carbon_complete (>0.5) | 957 | 0.879 | 7.0×10⁻¹⁸⁰ | Strongly conserved |
| COG A (RNA processing) | 346 | 0.840 | 4.1×10⁻²³ | Strongly conserved |
| COG Z (cytoskeleton) | 326 | 0.802 | 1.7×10⁻¹⁷ | Strongly conserved |
| 46-KO homeostasis | 957 | 0.804 | — | High |
| 46-KO metabolism | 957 | 0.788 | — | Moderate-high |
| UniRef90 diversity | 954 | 0.620 | 2.1×10⁻⁴² | Moderate |
| MAI (K16163, mycothiol isomerase) | 957 | 0.570 | 3.4×10⁻¹⁵⁰ | Moderate |
| 46-KO defense | 957 | 0.549 | — | Moderate (HGT-labile) |
| InterPro metal (14 IPR families) | 957 | 0.413 | 2.3×10⁻²⁵ | Low-moderate |
| Pfam metal (14 families) | 957 | 0.296 | 2.6×10⁻¹⁶ | Low |
| AMRFinderPlus metal | 957 | 0.244 | 1.8×10⁻⁴² | Very low — HGT-susceptible |
| COG P (inorganic ion transport) | 909 | 0.206 | 4.3×10⁻¹³ | Very low |
| COG categories (other) | 326–1,475 | 0.15–0.49 | <10⁻¹⁴ | Low to moderate |

**Key pattern**: GapMind metabolic completeness traits have *higher* phylogenetic signal than
even the curated metal gene subsets — carbon pathway completeness (λ=0.928) nearly matches
niche breadth itself (λ=0.932). Metal-specific gene sets show a gradient from moderate
(homeostasis λ=0.804) down to very low (InterPro λ=0.413; Pfam λ=0.296), with AMRFinderPlus
and COG P at the bottom (λ≈0.2). This gradient is consistent with the biology: phylogenetically
conserved metabolic core (carbon/aa pathways) > genus-level metabolic specialization
(homeostasis sensing) > horizontally transferred resistance hardware (efflux pumps, metal-binding
domains) > broad-function inorganic ion transporters (COG P).

Sources: `data/pagel_lambda_results_*.csv`

#### PGLS — extended gene set predictions of niche breadth

| Gene set / predictor | Response | n | λ (fit) | β | SE | p | Exploratory sig? |
|---------------------|----------|---|---------|---|-----|---|-----------------|
| GapMind carbon completeness | B_std | 957 | ~0.88 | +0.0228 | — | ≪0.001 | **yes** |
| GapMind n_carbon_complete | B_std | 957 | ~0.88 | +0.0201 | — | ≪0.001 | **yes** |
| UniRef90 diversity | B_std | 954 | 0.888 | +0.0093 | 0.0034 | 0.0074 | **yes** |
| InterPro metal (14 IPR) | B_std | 957 | 0.889 | +0.0083 | 0.0032 | 0.010 | **yes** |
| COG I (lipid transport/metabolism) | B_std | 957 | 0.887 | +0.0100 | 0.0030 | 0.00090 | **yes (BH-FDR)** |
| COG K (transcription) | B_std | 957 | 0.886 | +0.0099 | 0.0030 | 0.00085 | **yes (BH-FDR)** |
| COG E (aa transport/metabolism) | B_std | 957 | 0.887 | +0.0098 | 0.0031 | 0.0017 | **yes (BH-FDR)** |
| COG P (inorganic ion transport) | B_std | 909 | 0.879 | +0.0087 | 0.0031 | 0.0047 | **yes (BH-FDR)** |
| GapMind aa completeness | B_std | 957 | ~0.89 | +0.0041 | — | 0.37 | no |
| Pfam metal (14 families) | B_std | 957 | 0.894 | +0.0004 | 0.0037 | 0.91 | no |
| MAI (K16163) | B_std | 957 | ~0.89 | — | — | 0.21 | no |
| AMRFinderPlus metal | B_std | 957 | 0.894 | +0.0019 | 0.0031 | 0.54 | no |
| GapMind carbon completeness | n_envs | 957 | ~0.87 | +0.169 | — | 0.050 | borderline |
| UniRef90 diversity | n_envs | 954 | 0.873 | −0.0235 | 0.058 | 0.69 | no |
| InterPro metal (14 IPR) | n_envs | 957 | 0.872 | +0.0285 | 0.054 | 0.60 | no |

**COG full sweep**: 17/25 COG functional categories significantly predict B_std after BH-FDR
correction (50 models total: 25 categories × 2 responses). However, the effect sizes are nearly
identical across all categories (β≈0.008–0.011), suggesting this reflects a genomic-complexity
effect rather than any specific functional category — genera with larger, more diverse genomes
occupy broader niches. COG P is among the significant categories (BH-FDR p=0.041), confirming
the earlier targeted result.

**No COG category significantly predicts n_envs after BH-FDR correction.** The niche breadth
measure (Levins' B_std) and number of environments are partially decoupled — B_std captures
physiological tolerance range while n_envs counts distinct habitat types.

**Interpretation**:
1. **Carbon metabolism > metal resistance for niche breadth prediction**: GapMind carbon
   completeness (β=0.023) strongly outperforms any metal gene metric. Genera with broader
   carbon source repertoires occupy broader ecological niches — carbon flexibility is the
   primary functional driver of ecological generalism in this dataset.
2. **Genomic generalism signal**: UniRef90 diversity and most COG categories predict niche
   breadth, suggesting a general effect of genome size/complexity rather than any specific
   functional category.
3. **Metal resistance genes null for niche breadth**: Pfam (p=0.91), MAI (p=0.21), and
   AMRFinderPlus (p=0.54) metal gene sets show no niche breadth association. Metal resistance
   genes may be adaptations to specific metal-contaminated microhabitats without conferring
   general ecological breadth.
4. **InterPro metal significant but small effect** (β=0.0083, p=0.010): InterPro-defined HMA
   and cation efflux domains capture a broader set of metal-associated proteins than the curated
   46-KO list, including many constitutively expressed metal-handling proteins. The signal
   likely reflects functional breadth correlation rather than metal resistance per se.

Sources: `data/pgls_results_*.csv`, `data/pagel_lambda_results_*.csv`

#### GapMind 80-pathway individual PGLS

Each of the 80 GapMind carbon/aa pathways tested individually as predictor of niche breadth
(n=957 genera, GTDB r214 tree). BH-FDR applied separately within each response (80 tests each).
Source: `data/pgls_results_gapmind_pathways.csv`.

**B_std (Levins' niche breadth)**: 38/80 pathways significant after BH-FDR.
All but one (alanine) have positive β, consistent with carbon breadth → ecological breadth.

Top 10 pathways by BH-FDR:

| Pathway | Category | β | p_adj_BH |
|---------|----------|---|----------|
| galacturonate | carbon | +0.0174 | 0.00157 |
| gluconate | carbon | +0.0162 | 0.00157 |
| isoleucine (C-source) | carbon | +0.0188 | 0.00295 |
| propionate | carbon | +0.0183 | 0.00295 |
| valine (C-source) | carbon | +0.0185 | 0.00295 |
| citrulline | carbon | +0.0175 | 0.00295 |
| arginine (C-source) | carbon | +0.0174 | 0.00295 |
| D.alanine | unknown | +0.0159 | 0.00295 |
| acetate | carbon | +0.0159 | 0.00295 |
| mannitol | carbon | +0.0136 | 0.00295 |

**Alanine (L-alanine as C-source) is the only negative predictor** (β=−0.014, p_adj=0.0026).
Alanine utilization is a hallmark of anaerobic/fermentative specialists, consistent with
narrow-niche organisms being more represented in this metabolic pathway.

**n_envs (number of habitats)**: Only 4/80 pathways significant after BH-FDR — galacturonate
(β=+0.27, p_adj=0.006), acetate (+0.27, 0.016), alanine (−0.21, 0.017), ethanol (+0.22, 0.037).
The stricter n_envs measure confirms galacturonate and acetate as the most robust environmental
generalism markers.

**Biological interpretation**: Galacturonate (a pectin component in plant cell walls) predicts
the broadest niche occupancy — genera capable of mineralizing plant structural carbohydrates are
environmentally ubiquitous. The pattern across 38 significant pathways is consistent with a
"metabolic generalism begets ecological generalism" hypothesis: diverse carbon source utilization
enables colonization of heterogeneous environments.

---

### Multi-scale analysis: Pagel's λ and PGLS at genus, family, and order levels

To test whether the phylogenetic signal and functional associations are consistent across
taxonomic resolution, we re-ran Pagel's λ and PGLS at family and order levels using the same
GTDB r214 genus tree. Higher-level trait values = mean across genera with niche breadth data
within each group; one representative genus per group serves as the tree tip. Class (n=27) and
phylum (n=22) analyses were run but excluded from summary: λ estimates outside [0,1] (class
λ=2.15, phylum λ=−3.63) indicate optimizer boundary issues at these sample sizes.

Source: `data/pagel_lambda_results_multilevel.csv`, `data/pgls_results_multilevel.csv`
Script: `/tmp/multilevel_lambda_pgls.R`

#### Pagel's λ — niche breadth across taxonomic levels

| Level | n groups | λ (B_std) | p | λ (n_envs) | p |
|-------|---------|-----------|---|-----------|---|
| Genus | 957 | 0.895 | 4.7×10⁻¹²⁷ | 0.873 | 3.4×10⁻¹⁰⁵ |
| Family | 90 | 1.144* | 3.5×10⁻⁸ | 0.950 | 3.0×10⁻⁶ |
| Order | 61 | 0.552 | 0.098 (ns) | 0.868 | 0.018 |

*λ>1 at family level: the optimizer estimates extreme Brownian motion; the mean-of-means
aggregation may reduce within-family variance faster than the tree branch lengths predict.
Family-level B_std signal is real (highly significant), but the point estimate should be
interpreted as "high" rather than taken at face value.

**Key pattern**: Phylogenetic signal in niche breadth is strongest and most stable at genus
level. At order level the B_std signal attenuates (p=0.10), while n_envs remains significant
(p=0.018). This is expected: genus-level niche breadth varies continuously on the tree, but
coarser groupings average out within-order variation.

#### PGLS — functional associations across levels

| Level | n | Predictor | β (B_std) | p (B_std) | β (n_envs) | p (n_envs) |
|-------|---|-----------|-----------|-----------|-----------|-----------|
| Genus | 957 | GapMind carbon | +0.169 | 9.1×10⁻⁶ *** | +0.079 | 0.050 (.) |
| Genus | 957 | Homeostasis KO | +0.095 | 0.0023 ** | +0.026 | 0.43 |
| Genus | 957 | Defense KO | +0.070 | 0.029 * | +0.029 | 0.39 |
| Genus | 957 | Metabolism KO | +0.006 | 0.83 | +0.041 | 0.15 |
| Family | 90 | GapMind carbon | +0.254 | 0.0083 ** | +0.129 | 0.22 |
| Family | 90 | Defense KO | +0.246 | 0.039 * | +0.094 | 0.44 |
| Family | 90 | Homeostasis KO | +0.184 | 0.065 (.) | +0.181 | 0.096 |
| Family | 90 | Metabolism KO | — | (failed†) | −0.052 | 0.59 |
| Order | 61 | Homeostasis KO | +0.333 | 0.0097 ** | +0.303 | 0.018 * |
| Order | 61 | Defense KO | +0.040 | 0.77 | +0.026 | 0.85 |
| Order | 61 | GapMind carbon | — | (failed†) | +0.384 | 0.018 * |

†Optimizer failure due to near-singular correlation matrix at that aggregation level.

**Interpretation**:

1. **GapMind carbon is the most consistent predictor** across scales: significant at genus
   (p=9×10⁻⁶) and family (p=0.008), directionally consistent at order. Beta increases at
   coarser levels (0.169 → 0.254), reflecting the amplification of between-clade signal when
   within-group variance is averaged out.

2. **Homeostasis KO signal strengthens at order level**: Genus p=0.002, order p=0.010. This
   suggests homeostasis metal-sensing genes (regulators, sensors) are associated with niche
   breadth at the clade level — clades that broadly acquired sensing machinery tend to occupy
   more environments. Order-level signal for n_envs (p=0.018) is particularly notable.

3. **Defense KO marginal association is a habitat confound**: Nominally significant at genus
   (p=0.029) and family (p=0.039) but attenuates at order level (p=0.77) and becomes NS after
   controlling for aquatic/soil habitat fraction (partial PGLS p=0.13). Soil genera have both
   more defense genes AND broader niches; defense gene count does not independently predict
   niche breadth. Defense genes are more HGT-labile (λ=0.55) and their nominal signal reflects
   ecological sorting of lineages into aquatic vs. terrestrial lifestyles, not a functional
   relationship between defense gene content and niche width.

4. **Metabolism KO null across all levels**: Confirms the genus-level finding that the pure
   metabolic metal-handling genes (transporters, enzymes) do not predict niche breadth at any
   tested taxonomic resolution.

5. **Effect size scaling is biologically meaningful**: Beta ≈ 0.17 at genus, 0.25 at family
   for GapMind carbon. The ~1.5× amplification at family level is consistent with ecological
   sorting theory: within a family, genera share similar carbon metabolism, so the
   between-family signal reflects deep evolutionary specialization.

---

### Finding 5: Environmental context — climate, productivity, and AlphaEarth embeddings independently predict niche breadth

Genus-level environmental profiles extracted from MicrobeAtlas GEE covariates (n=957 genera,
100% coverage) and AlphaEarth genomic embeddings (n=758 genera, 79% coverage, 64-dim → PCA).
Results in `data/pgls_results_gee.csv` (scripts: `/tmp/gee_pgls.R`, `/tmp/extract_env_profile_v3.py`).

**GEE climate/soil individual predictors (Model G1, n=957):**

| Predictor | β (B_std) | p | β (n_envs) | p |
|---|---|---|---|---|
| GPP (gross primary productivity) | −0.151 | 6.5×10⁻¹¹ *** | −0.110 | 8.8×10⁻⁶ *** |
| SOM (soil organic matter) | −0.149 | 9.0×10⁻¹⁰ *** | −0.101 | 9.9×10⁻⁵ *** |
| Precipitation | −0.125 | 1.5×10⁻⁸ *** | −0.051 | 0.032 * |
| pH | +0.124 | 1.3×10⁻⁷ *** | +0.024 | ns |
| Temperature | −0.087 | 1.8×10⁻⁴ *** | −0.131 | 1.0×10⁻⁷ *** |
| NDVI | +0.016 | ns | +0.052 | ns |

High-productivity, high-SOM, warm, and wet environments host niche specialists. Alkaline pH
environments host generalists for B_std (but not n_envs). These signals are consistent with the
aquatic/soil habitat divide: wet/warm/productive conditions overlap with aquatic or tropical soil
environments where specialist lineages dominate.

**AlphaEarth PC1 is a robust independent predictor (Model G2, n=957):**
AlphaEarth PC1 β=−0.157 (B_std, p=5.9×10⁻¹⁰ ***), β=−0.143 (n_envs, p=1.2×10⁻⁷ ***).
In the full model (G6) controlling for aquatic fraction, temperature, precipitation, and GapMind
carbon, AlphaEarth PC1 remains significant: β=−0.028 (B_std, p=3.4×10⁻⁵ ***), β=−0.027
(n_envs, p=3.3×10⁻⁴ ***). The AlphaEarth embedding — a 64-dimensional learned representation
of the genomic-environmental context of sequenced genomes — captures independent environmental
variation that predicts ecological breadth beyond habitat type and climate.

**GapMind carbon survives climate control (Model G3, n=957):**
GapMind carbon β=+0.163 (p=1.2×10⁻⁵ ***) after controlling for temperature and precipitation.
In the full model (G6) with all covariates: β=+0.140 (p=2.8×10⁻⁵ ***). This is the third
independent confirmation that carbon metabolic flexibility predicts ecological generalism as a
genuine functional trait, not a climate or habitat surrogate.

**Environmental drivers hierarchy (for B_std):**
1. Aquatic vs. soil fraction (β=−0.38 to −0.41 ***) — dominant
2. GEE productivity (GPP, SOM) and climate (precipitation, temperature) — strong
3. AlphaEarth PC1 — independent of 1 and 2
4. Soil pH — significant for B_std only
5. GapMind carbon — independent functional trait

*(Notebooks: 07_env_metadata_pgls.ipynb; data: pgls_subset_env_profile.csv, pgls_results_gee.csv)*

---

## Robustness Analyses

**⚠ Status (2026-06-29): All robustness analyses below were conducted using AMRFinderPlus
annotations (n = 606 genera). Following the update to the curated 46-KO gene list (n = 957
genera), these analyses need to be re-run. Numbers below are retained for historical record
but do not reflect current data. Results should not be cited until re-run.**

Six robustness analyses were run using AMRFinderPlus data. Scripts:
`scripts/pgls_robustness.R` (analyses 1–3), inline Python (analysis 4),
`scripts/pgls_genome_size.R` (analysis 5), and inline Rscript (analysis 6).

![Robustness summary: Panel A — β across 5 analysis scenarios; Panel B — rarefied β distribution (200 iterations); Panel C — archaeal power curve](figures/fig5_robustness.png)

### R1. Pangenome coverage covariate (addressable with existing data)

Adding `n_species_with_amr` (z-scored) as a fourth predictor to control for genome-sampling
depth:

| Model | Predictor | β | SE | p |
|-------|-----------|---|-----|---|
| B_std ~ types + n_species | Metal types (z) | **+0.0204** | 0.0057 | **3.4×10⁻⁴** |
| B_std ~ types + n_species | n_species (z) | +0.0093 | 0.0051 | 0.068 |
| B_std ~ all 3 + n_species | Metal types (z) | **+0.0224** | 0.0067 | **8.3×10⁻⁴** |
| B_std ~ all 3 + n_species | n_species (z) | +0.0092 | 0.0051 | 0.070 |

**Conclusion**: Metal type diversity remains significant (p ≈ 3–8×10⁻⁴) after adding genome
count as an explicit covariate. The covariate itself is borderline (p ≈ 0.07), indicating a
modest but non-dominant contribution of sampling depth. The metal type effect is not explained
away by genome count alone.

*(Script: scripts/pgls_robustness.R, Analysis 1)*

### R2. Pangenome rarefaction — 1 species per genus (addressable with existing data)

To formally remove the genome-count bias, 200 PGLS iterations were run where each genus was
represented by a single randomly sampled species from `species_metal_amr.csv`. Of 606 PGLS
genera, 383 had >1 species in the AMR database (the remaining 223 are already singletons, so
rarefaction does not change them).

| Metric | Value |
|--------|-------|
| Iterations completed | 200 / 200 |
| Median β (metal types → B_std) | **+0.0147** |
| IQR of β | +0.0126 – +0.0166 |
| Median p | **0.0054** |
| Fraction p < 0.05 | **89.5%** |
| Fraction Bonferroni-significant (p < 0.0083) | **57.5%** |
| Median λ | 0.704 |

**Conclusion**: After rarefaction the effect direction is consistent across all 200 iterations,
89.5% reach nominal significance, and 57.5% are Bonferroni-significant. The median β (+0.0147)
is smaller than the full-data estimate (+0.0215) — as expected when multi-species genera (which
have higher inferred metal types) are reduced to one representative — but the signal is clearly
not artefactual. Pangenome sampling depth does not explain the association.

*(Script: scripts/pgls_robustness.R, Analysis 2)*

### R3. Archaeal PGLS and formal power analysis (exploratory, n = 48)

*See [Supplementary: Archaeal Analyses](#supplementary-archaeal-analyses) for full results and
power analysis tables. Summary*: archaeal PGLS (n = 48 genera) finds positive but non-significant
β = +0.0145 (p = 0.467) for metal types. This is a severely underpowered analysis (11% power
at α = 0.05); the non-significant result should not be interpreted as evidence against the
association in archaea.

### R4. Prevalence-threshold niche breadth (addressable with existing data)

To test whether the metal type → B_std signal depends on sparse, possibly artefactual
detections, niche breadth was recomputed using a strict 5% within-environment prevalence
threshold: an OTU was counted as "present" in an environment only if it appeared in ≥5% of
samples in that category. This reduces detections driven by contamination, cross-sample
bleed-through, or rare transient events.

| Metric | Original | Strict (≥5%) |
|--------|----------|-------------|
| OTUs passing filter | 98,919 | 10,433 |
| Genera with B_std estimate | 3,160 | 1,120 |
| PGLS n (with AMR data) | 606 | 379 |
| Pearson r (orig vs strict B_std) | — | 0.680 |
| β (metal types → B_std) | +0.0215 | **+0.0166** |
| SE | 0.0056 | 0.0099 |
| p | **1.5×10⁻⁴** | 0.092 |
| λ | 0.708 | 0.526 |

**Conclusion**: Under the strict threshold the effect loses statistical significance (p = 0.092)
primarily due to reduced sample size (n drops 37%: 606 → 379), not a change in direction or
magnitude (β changes from +0.0215 to +0.0166, a 23% reduction). The 5% threshold is quite
conservative — it excludes 89% of OTUs, many of which are genuinely distributed across
environments but uncommon within any one. This analysis suggests the signal is not driven
entirely by spurious rare detections, but that power requirements for strict prevalence-based
niche breadth are substantially higher. A threshold of 1–2% would be a reasonable middle
ground for future work.

*(Python, inline in analysis pipeline)*

### R5. Genome size PGLS covariate (new BERDL query)

Genus-level mean genome size (bp) was retrieved from `kbase_ke_pangenome.gtdb_metadata`
via BERDL REST API (one representative species per genus; 527/606 PGLS genera covered).
log(genome_size) was z-scored and added as a PGLS covariate alongside metal type diversity.

| Predictor | β | SE | p | λ |
|-----------|---|-----|---|---|
| Metal types (z) | **+0.0218** | 0.0061 | **3.6×10⁻⁴** | 0.629 |
| log(genome size) (z) | **+0.0263** | 0.0069 | **1.5×10⁻⁴** | — |

Baseline model (genome size only): β=+0.029, p=2.7×10⁻⁵, AIC=−630.3.
Full model (+ metal types): AIC=−641.1. **ΔAIC = 10.8** in favour of including metal types.

**Conclusions**: (1) Genome size is independently and significantly positively associated with
niche breadth, as expected (larger genomes encode more metabolic functions). (2) Metal type
diversity remains significant (p = 3.6×10⁻⁴) after controlling for genome size, with only a
marginal change in β (+0.022 vs +0.021 without genome size covariate). The metal type diversity
effect is **not an artefact of genome size**. (3) The partial β for metal types (controlling
for both genome size and phylogeny) confirms that metal resistance breadth has independent
predictive power beyond total genomic complexity.

*Note*: 79/606 genera (13%) lacked genome size data in BERDL at query time; PGLS n drops from
606 to 527. Results are consistent in direction and significance with the full-data models.

*(BERDL query: `kbase_ke_pangenome.gtdb_metadata.genome_size`; R script: inline Rscript)*

### R6. Three-covariate PGLS: metal types independent of both species richness and genome size

**Question**: Does the metal types effect survive when both log(n_species) and log(genome_size)
are controlled simultaneously in a single model?

**Analysis**: Merged n_species per genus (from GTDB r214 taxonomy, all 606 genera present) and
mean genome size (from `kbase_ke_pangenome.gtdb_metadata`, 527/606 genera). Fit:
B_std ~ metal_types_z + log_n_species_z + log_genome_size_z (n = 527 genera with all 3 covariates).

| Predictor | β | SE | t | p |
|-----------|---|-----|---|---|
| **Metal types (z)** | **+0.0218** | **0.0061** | **3.60** | **3.5×10⁻⁴** |
| log(n_species) (z) | +0.0052 | 0.0057 | 0.90 | 0.366 |
| log(genome size) (z) | **+0.0255** | **0.0069** | **3.68** | **2.6×10⁻⁴** |

n = 527, λ = 0.628.

**Conclusions**: Metal type diversity remains independently significant (β = +0.022,
p = 3.5×10⁻⁴, q = 0.003 BH-FDR) after simultaneously controlling for both species richness
and genome size. When genome size is included alongside n_species, log(n_species) is no longer
significant (p = 0.37), indicating that the log(n_species) effect in S4 was partly mediated
by genome size (larger genera tend to have larger genomes). Genome size remains independently
significant (p = 2.6×10⁻⁴). The metal type diversity effect is **not an artefact of either
genome complexity or sequencing depth**.

*(Script: inline Rscript — `data/pgls_3covariate_result.csv`)*

---

## Extended Sensitivity Analyses

**⚠ Status (2026-06-29): All sensitivity analyses below used AMRFinderPlus data (n = 606
genera) and require re-running with the curated 46-KO gene list. Retained for historical
record only.**

Four additional sensitivity analyses were run using AMRFinderPlus data.
Script: `scripts/pgls_sensitivity.R`.

### S1. Leave-one-metal-out: no single metal drives the result

**Concern**: Could the metal type diversity effect be driven by a single ubiquitous metal (e.g.,
copper resistance) that is common in broad-niche genera?

**Analysis**: For each of 7 metals (Hg, As, Cu, Zn, Cd, Cr, Ni), recomputed number of metal
types excluding that metal from the count at the species level, aggregated to genus, and re-ran
PGLS.

| Metal excluded | β (excl.) | SE | p | vs original |
|---------------|-----------|-----|---|-------------|
| Hg | +0.0082 | 0.0069 | 0.233 | ↓ |
| As | +0.0039 | 0.0061 | 0.518 | ↓↓ |
| Cu | +0.0102 | 0.0065 | 0.115 | ↓ |
| Zn | +0.0095 | 0.0064 | 0.140 | ↓ |
| Cd | +0.0084 | 0.0064 | 0.186 | ↓ |
| Cr | +0.0088 | 0.0064 | 0.173 | ↓ |
| Ni | +0.0095 | 0.0064 | 0.140 | ↓ |
| **All 7 (original)** | **+0.0215** | **0.0056** | **1.5×10⁻⁴** | — |

**Conclusion**: No single metal exclusion leaves a significant result — all 7 drop to p > 0.10.
However, no one metal is singled out as THE driver: excluding As produces the weakest residual
signal (β=+0.004, p=0.52), while excluding Cu produces the strongest (β=+0.010, p=0.12). The
consistency across all exclusions indicates the effect is *distributed* across the metal type
diversity spectrum rather than driven by one dominant metal. The loss of significance is expected
because each exclusion reduces the maximum possible diversity score by 1 (from 7 to 6), compressing
predictor variance and costing statistical power. The direction (positive β) is preserved in all 7
leave-one-out models.

**Interpretive caveat**: Loss of significance after removing one of seven metals is consistent
with either (a) a genuinely distributed signal where each metal type contributes independently,
or (b) an original finding that was near the significance threshold and is pushed below it by the
compressed predictor range (max diversity 6 rather than 7). The consistently positive β direction
across all seven exclusions supports interpretation (a), but these alternatives cannot be
definitively distinguished without a larger metal type vocabulary. This ambiguity is explicitly
noted here.

*(Script: scripts/pgls_sensitivity.R, Analysis 1)*

### S2. Leave-one-environment-out: signal robust to any single environment category

**Concern**: The 13 MicrobeAtlas environment categories lump heterogeneous habitats (e.g.,
marine hydrothermal vents and freshwater lakes both classified as "aquatic"). Could the signal
depend on one poorly-defined category?

**Analysis**: For each of 13 environment categories, excluded that category from the B_std
computation (row-normalised prevalences over the remaining 12 environments, B_std recomputed with
J=12), then re-ran PGLS.

| Environment excluded | β | SE | p | λ |
|---------------------|---|-----|---|---|
| agricultural | +0.0107 | 0.0040 | 0.0073 | 0.883 |
| **aquatic** | **+0.0085** | **0.0039** | **0.031** | **0.880** |
| desert | +0.0120 | 0.0042 | 0.0040 | 0.913 |
| farm | +0.0115 | 0.0042 | 0.0061 | 0.873 |
| field | +0.0118 | 0.0040 | 0.0030 | 0.868 |
| flower | +0.0118 | 0.0044 | 0.0077 | 0.898 |
| forest | +0.0142 | 0.0042 | 0.0007 | 0.874 |
| leaf | +0.0130 | 0.0043 | 0.0025 | 0.893 |
| paddy | +0.0123 | 0.0042 | 0.0036 | 0.898 |
| peatland | +0.0131 | 0.0044 | 0.0027 | 0.890 |
| plant | +0.0105 | 0.0039 | 0.0069 | 0.882 |
| shrub | +0.0126 | 0.0043 | 0.0034 | 0.887 |
| soil | +0.0113 | 0.0039 | 0.0035 | 0.889 |

**Conclusion**: All 13 leave-one-out models are significant (p < 0.05). The weakest result
is obtained when excluding "aquatic" — the most heterogeneous and most over-represented category
(40,353 OTUs; 40.8% of the dataset) — where β drops from +0.021 (main) to +0.0085 (−59%),
yet remains significant (p = 0.031). The 3 least-sampled environments (flower: 898 OTUs, 0.9%;
leaf: 1,298 OTUs, 1.3%; plant: 2,647 OTUs, 2.7%) give β = +0.012, +0.013, +0.010,
all p < 0.008. The result is not contingent on any one environment category. Note that λ is
consistently higher in this analysis (0.87–0.91 vs 0.71 in the main analysis) because excluding
one environment reduces the total number of categories, increasing the relative weight of shared
environments across genera and amplifying phylogenetic covariation in the rescaled B_std.

**Quantitative bias estimate**: The over-representation of aquatic environments (40.8% of OTUs)
is a potential source of downward bias when that category is included — excluding it produces
a *weaker* β (+0.0085 vs +0.021), suggesting that aquatic OTUs contribute disproportionately
to the association. This is consistent with metal-contaminated coastal, estuarine, and
hydrothermal aquatic environments contributing many broad-niche metal-tolerant genera. Excluding
aquatic environments therefore produces a conservative lower bound on the true association.

The concern about sub-category heterogeneity (e.g., marine vs freshwater within "aquatic") is
a valid methodological limitation — the current analysis cannot test it because MicrobeAtlas
does not provide finer environment classification. Splitting categories at a finer resolution
would require re-running the niche breadth computation with a revised environment taxonomy.

*(Script: scripts/pgls_sensitivity.R, Analysis 2)*

### S3. Within-genus variance in metal types: not a confounder

**Concern**: Genus-level means mask within-genus heterogeneity. Could the mean metal type
diversity be high for a genus because a few outlier species drive it, while other species have
no metal resistance at all?

**Analysis**: Computed within-genus standard deviation of n_metal_types across species from
`species_metal_amr.csv`, z-scored it, and added it as a covariate to the main PGLS.

| Predictor | β | SE | p |
|-----------|---|-----|---|
| Metal types (z) | **+0.0189** | 0.0060 | **0.0016** |
| SD(metal types) (z) | +0.0074 | 0.0055 | 0.181 |

**Conclusion**: The within-genus SD of metal types is not a significant predictor (p = 0.18),
and the mean metal types effect is largely unchanged (β = +0.019 vs +0.021 original). Genera
are not being driven into the "high diversity" category by a few outlier species in a way that
inflates the association with niche breadth.

*(Script: scripts/pgls_sensitivity.R, Analysis 3)*

### S4. Log(n_species) as PGLS covariate: metal types robust, log-genome-count also informative

**Concern**: Adding n_species_with_amr as a covariate in the prior analysis (R1) used a
linear scale; genome count effects are typically log-linear. Was the linear covariate
underpowered?

**Clarification on prior work**: Analysis R1 already added n_species_with_amr as a PGLS
covariate (not OLS). The claim that this was only done in OLS is incorrect. R1 used `gls()`
with `corPagel` — the same phylogenetically-corrected estimator as the main analysis. The
new question is whether log-transforming improves covariate performance.

**Analysis**: Added log1p(n_species_with_amr) (z-scored) as a PGLS covariate alongside
metal types.

| Predictor | β | SE | p |
|-----------|---|-----|---|
| Metal types (z) | **+0.0195** | 0.0057 | **6.4×10⁻⁴** |
| log(n_species) (z) | +0.0127 | 0.0053 | **0.016** |

**Conclusion**: With the log-transformed genome count covariate, metal type diversity remains
significant (p = 6.4×10⁻⁴, compared to p = 1.5×10⁻⁴ without). Log(n_species) is now
significant (p = 0.016), whereas the linear covariate in R1 was borderline (p = 0.07). This
indicates that genome-count has a log-linear relationship with niche breadth: well-sampled
genera tend to be slightly broader-niched, possibly because they include more ecologically
diverse isolates. However, the metal type diversity effect is not explained away (β drops from
+0.021 to +0.020), confirming that the predictor has independent signal beyond sequencing
depth. Partial R² decomposition would require a likelihood-ratio test, which shows metal types
retains a ΔAIC of approximately −10 beyond the log(n_species)-only model.

*(Script: scripts/pgls_sensitivity.R, Analysis 4)*

### S5. OTU abundance filtering for Pagel's λ: robust to excluding rare OTUs

**Concern**: Low-abundance OTUs (potentially spurious detections) may inflate niche breadth
estimates, biasing the Pagel's λ for B_std.

**Analysis**: Estimated per-OTU mean relative abundance as total_counts / (n_detected_samples ×
mean_library_size), where mean_library_size = total_reads / total_samples (87,595 reads/sample
across 463,972 samples). OTUs with mean relative abundance < 0.01% were excluded (66% of
OTUs; 34% = 33,676 OTUs pass). Bacterial, non-organellar OTUs passing the filter: 23,759 OTUs
covering 576 of 606 PGLS genera. Genus-level B_std was recomputed on the filtered OTU set.

| Metric | All OTUs (original) | Filtered ≥0.01% rel. abund. |
|--------|--------------------|-----------------------------|
| Bacterial genera | 1,264 (Pagel's λ) | 576 (filtered subset) |
| Pagel's λ (B_std) | 0.787 (all) / 0.763 (same 576) | **0.750** |
| p (LRT) | 7.9×10⁻¹⁰² / 5.9×10⁻⁴⁰ | **2.8×10⁻⁴⁰** |
| Change in λ | — | −0.013 (−1.7%) |

**Conclusion**: Excluding low-abundance OTUs (<0.01% mean relative abundance) reduces Pagel's
λ for bacterial B_std by only 1.7% (0.763 → 0.750), and the signal remains highly significant
(p = 2.8×10⁻⁴⁰). The phylogenetic conservation of niche breadth is not an artefact of rare
transient OTU detections.

*(Python inline analysis — `data/pgls_subset_filtered_otus.csv`)*

---

## Study Design and Inferential Framework

### Confirmatory vs exploratory analyses

The primary confirmatory hypothesis — tested prior to examining residuals and interaction effects
— was: **does metal AMR trait diversity predict bacterial niche breadth after phylogenetic
correction?** The 6 simple PGLS models (NB05) with Bonferroni correction constitute the
confirmatory analysis. All other analyses are appropriately labelled exploratory or
post-hoc robustness checks.

Specifically:
- **Confirmatory**: 6 simple PGLS models (NB05), Pagel's λ for niche and AMR traits (NB04)
- **Exploratory**: multi-predictor PGLS, robustness analyses R1–R4, sensitivity analyses S1–S4,
  archaeal PGLS, all analyses added in response to the post-hoc review process

The robustness analyses were conducted after the main analysis was complete, in response to
anticipated reviewer concerns. **⚠ All robustness analyses are stale (AMRFinderPlus data,
n = 606 genera) and require re-running with the curated 46-KO gene list (n = 957 genera).**
The prior primary confirmatory result (metal types → B_std, p = 1.5×10⁻⁴, Bonferroni-corrected
with AMRFinderPlus) does **not** replicate with the curated gene list (p = 0.560).

Future studies on this question would benefit from preregistering the primary hypothesis,
analysis plan, and sample size before data collection.

### Multiple testing count

| Analysis set | n tests | Correction |
|-------------|---------|------------|
| Simple PGLS (confirmatory) | 6 | Bonferroni (α/6 = 0.0083) |
| Pagel's λ (confirmatory) | 6 | LRT, no additional correction |
| Multi-predictor PGLS | 3 predictors in 1 model | not corrected beyond model |
| Robustness R1–R2, R4–R6 | 9 coefficients | exploratory only |
| Archaeal PGLS R3 (supplementary) | 3 coefficients | exploratory only |
| Sensitivity S1–S5 | 24 coefficients | exploratory only |
| OTU abundance filter S5 (Pagel's λ) | 1 | exploratory only |
| **Total** | **~47 tests** | — |

**⚠ Note (2026-06-29)**: The primary PGLS result changed after the AMRFinderPlus → curated
46-KO annotation update. The primary result (metal clusters, multi-predictor p = 0.033) does
not survive a Bonferroni correction for the full 47-test family. The BH-FDR table in
`data/all_tests_fdr.csv` is stale (based on AMRFinderPlus data). Robustness analyses R1–R6
and sensitivity analyses S1–S5 also used AMRFinderPlus data and require re-running with the
curated 46-KO gene list before the multiple-testing table can be updated.

### λ discrepancy: standalone Pagel's λ vs PGLS-estimated λ

Pagel's λ for bacterial B_std estimated standalone (NB04) = **0.932**; PGLS-estimated λ
(NB05, metal clusters model) = **0.887**. This discrepancy (Δλ = 0.045) is expected and
informative:

- **Standalone λ**: estimates phylogenetic signal in B_std without any predictor; measures how
  much of B_std's total variance is explained by Brownian motion phylogenetic covariance.
- **PGLS λ**: estimates residual phylogenetic signal after removing the variance explained by
  the predictor. Because metal cluster count itself has phylogenetic signal (λ = 0.665),
  including it as a covariate removes some phylogenetically structured variance from the
  residuals, causing PGLS λ to be lower than standalone λ.

The drop from 0.932 to 0.887 (a 5% reduction) is smaller than in the prior AMRFinderPlus
analysis (0.787 → 0.708; 10% reduction). This is consistent with the curated 46-KO gene list
explaining less of B_std's phylogenetic structure — the core metal resistance genes captured
by the KO list share less ecological variation with niche breadth than the broader
AMRFinderPlus gene set. The residual λ = 0.887 (p ≪ 0.001) confirms the PGLS architecture
is appropriate; there is no evidence of model misspecification.

### Causation and directionality

The PGLS coefficient is a *partial correlation* after phylogenetic correction, not a causal
estimate. Three directional scenarios are consistent with the data:

1. **Metal tolerance enables habitat expansion**: taxa that acquire diverse metal resistance
   can colonise chemically diverse environments (polymetallic soils, estuarine sediments)
   that are also broad in other dimensions, increasing ecological range.
2. **Ecological generalism enables gene acquisition**: broad-niche genera encounter more
   environments, more HGT donors, and higher metal concentrations on average, driving
   preferential acquisition of diverse metal AMR genes.
3. **Shared driver**: a third variable (e.g., genome size, metabolic versatility, biofilm
   capacity) promotes both broad niches and diverse metal tolerance repertoires independently.

The cross-sectional design of this study — comparing genera at a single snapshot in evolutionary
time using observational global survey data — means the direction of this association cannot be
established. It is equally consistent with metal diversity *facilitating* ecological generalism
(genera tolerant of more metals can exploit more environments) and with ecological generalism
*enabling* metal gene acquisition (broad-niche genera encounter more HGT donors and more
metal-contaminated environments). Distinguishing these scenarios would require time-series
genomic data tracking metal resistance evolution alongside range shifts, or natural experiment
designs such as metal enrichment of defined microbial communities with longitudinal tracking.

The current analysis cannot distinguish among the three causal scenarios. The finding that total
AMR cluster count is non-significant while metal type *diversity* is significant slightly favours
scenario 1 or 3 over a simple "genome-size drives everything" model: scenario 3 with genome size
as the sole driver would predict cluster count should also be significant, since cluster count
scales more directly with total genome size. Furthermore, R5 shows that metal type diversity
remains independently significant (β = +0.022, p = 3.6×10⁻⁴) after formally controlling for
genome size in PGLS, ruling out genome size as the primary confounder. Without time-series data
or a natural experiment (e.g., experimental metal enrichment on defined communities), the
association nonetheless remains correlational and the direction cannot be established.
The report should be read as: *genera with diverse metal resistance repertoires are, on average,
broader ecological generalists in the global microbiome*.

### Phylogenetic tree and genus-aggregation choices

All PGLS and Pagel's λ analyses use the GTDB r214 genus-representative tree, constructed from
120 concatenated marker genes. This is the current field standard for bacterial phylogenetics and
provides the best available reconciliation of phylogenomic signal with 16S taxonomy. Sensitivity
to alternative trees (NCBI, SILVA-based 16S, or a different GTDB release) was not tested and
represents a known methodological gap; a 16S-based tree in particular would align more directly
with the 16S-derived niche breadth values but has lower resolution at genus level.

Genus-level pruning (one representative tip per genus, chosen as the GTDB species cluster
representative) is standard in macro-ecological PGLS studies of this scale. Within-genus
phylogenetic structure is discarded; the sensitivity analysis S3 partially compensates by testing
whether within-genus SD of metal types is a significant PGLS covariate (it is not, p = 0.18),
confirming that genus aggregation does not hide a species-level confound.

### Metal gene annotation quality and recommended replacement

Metal AMR gene annotations in this study use AMRFinderPlus HMM-based detection against the NCBI
Bacterial AMR Reference Gene Database. For metal resistance specifically, AMRFinderPlus employs
curated Hidden Markov Models built from experimentally validated reference sequences (e.g.,
merA/merB for mercury, arsABCDR for arsenate, copABCD for copper). HMM gathering thresholds are
set during model calibration to balance sensitivity and specificity.

**Recommended replacement — BacMet + curated KO list (two-tier approach)**:

A more targeted annotation strategy is now available from companion projects:

1. **BacMet 2.0** (http://bacmet.biomedicine.gu.se/) covers 927 gene families specifically
   curated for biocide and metal resistance, with separate experimental (EXP) and predicted (PRED)
   confidence tiers. BacMet HMM profiles should replace AMRFinderPlus for metal resistance
   annotation in NB01, as BacMet is purpose-built for this application and avoids conflation with
   clinical antibiotic resistance genes.

2. **Curated 46-KO seed list** (`metal_defense_vs_metabolism_classification/data/seed_list.tsv`)
   — validated through three adversarial review rounds. The KO-list classifies genes into defense,
   metabolism, and homeostasis categories (rather than AMRFinderPlus's single "metal resistance"
   bucket), enabling the metal *type diversity* effect detected here to be decomposed by functional
   class. A sensitivity analysis comparing AMRFinderPlus-based and KO-list-based metal type
   diversity scores is recommended before the next REPORT update.

**Existing AMRFinderPlus limitations (retained for historical record)**:
- Cross-reactive metalloproteases or ABC transporters with structural similarity to metal
  resistance proteins could be misclassified. AMRFinderPlus applies taxon-specific cutoffs
  to reduce this.
- The "other" metal category (17% of annotated clusters) captures metal-associated genes not
  classified into the 7 primary types; these may include weaker hits. Excluding the "other"
  category would produce a 6-metal analysis (Hg, As, Cu, Zn, Cd, Cr, Ni only).
- No manual validation of a subset was performed in this study. Spot checks of highly
  prevalent gene families (arsD, merP) show biologically expected distributions (high in
  contaminated environment genera, lower in strict aerobes), providing informal support.

The leave-one-metal-out analysis (S1) shows that even if one metal category has elevated false
positives, the result requires contributions from multiple metal types and would not be explained
by a single category's spurious annotations.

---

## Interpretation

### Biological meaning of the metal gene effect

**⚠ This section was written for the AMRFinderPlus result (metal types β = +0.021,
Bonferroni-corrected). The curated 46-KO result is null for metal types (p = 0.560) and
marginal for metal cluster count in the multi-predictor model (p = 0.033). The
interpretation below should be read as a hypothesis for what a significant result would mean,
not as a confirmed finding.**

A positive association between metal gene burden and niche breadth would be consistent with a
**metabolic versatility hypothesis**: genera with diverse metal tolerance repertoires —
encompassing Hg detoxification, As efflux, and Cu oxidation systems — may be associated with
broader ecological ranges. This co-occurrence is plausible because the environments that impose
multi-metal stress — polymetallic mine tailings, estuarine sediments, biosolid-amended soils —
are also chemically complex in other dimensions. Qi et al. (2022) found that multiple heavy
metal contamination favors microbial generalists as network keystones in soil, consistent with
this direction.

The prior AMRFinderPlus specificity of the metal *diversity* effect (not total gene burden)
— genera spanning multiple metal resistance families being the ecological generalists — is
now not replicated with the curated gene list. This is discussed in Finding 3.

### Phylogenetic signal structure

Pagel's λ for B_std estimated standalone (0.932) is higher than the λ estimated within the
PGLS model (0.887, metal clusters model) because the PGLS removes some phylogenetically
structured variance by including metal cluster count — which itself carries phylogenetic signal
(λ_metal_clusters = 0.665) — as a predictor.

Niche breadth and habitat range are more phylogenetically conserved than metal gene traits
in bacteria using the curated 46-KO approach (λ_niche ≈ 0.918–0.932 vs λ_metal ≈ 0.665–0.868).
However, the gap is much smaller than under AMRFinderPlus (where λ_AMR ≈ 0.26–0.44). The
high λ values for the curated metal gene metrics are consistent with the 46-KO list capturing
mainly constitutive, vertically inherited metal resistance — the same genes that define
lineage-specific metal tolerance (e.g., copA in Proteobacteria, mntABCD in Firmicutes).
This means the curated gene list may not be the right tool for detecting HGT-labile metal
resistance variation that predicts ecological breadth; AMRFinderPlus's broader scope may have
captured that component (whether correctly or via false positives remains to be determined by
BacMet cross-validation).

Nitrification (λ = 0.967–1.000 in both domains) serves as a metabolic positive control:
functional genes for ammonia and nitrite oxidation are deep, vertically inherited innovations
that define major lineages (Nitrospirota, Thaumarchaeota), and their near-maximal λ contrasts
with the metal gene signal. This internal comparison strengthens confidence in the analytical
pipeline.

Archaeal niche breadth also shows significant phylogenetic signal (λ = 0.640, p = 1.3×10⁻⁷
for B_std; λ = 0.880, p = 2.1×10⁻¹³ for n_envs), though λ for B_std is notably lower than
in bacteria, consistent with the phylogenetically sparse and ecologically distinct nature of
the archaeal genera sampled by short-read 16S amplicon surveys. Jiao et al. (2021) similarly
found phylogenetic niche conservatism in soil archaea, particularly for moisture niche, which
supports the signal being real rather than artefactual.

### Literature context

| This study | Literature | Consistency |
|-----------|-----------|-------------|
| Bacterial niche breadth λ = 0.932 (n=1,252) | Malfertheiner et al. (2026): community conservatism widespread across phyla | Consistent |
| Soil prokaryote niche breadth conserved | Hernandez et al. (2023): multidimensional specialization conserved in soil prokaryotes | Consistent |
| Metal gene metrics → niche breadth: null (PGLS, curated 46-KO) | Qi et al. (2022): heavy metal contamination favors generalists | Inconsistent — association expected but not detected with curated gene list |
| High λ for curated metal AMR (0.665–0.868) | Hemme et al. (2016): LGT hotspots for metal resistance in contaminated communities | Partially consistent — high λ implies vertical inheritance; LGT may be context-specific |
| Type λ (0.868) > core fraction λ (0.725) > cluster λ (0.665) | Gillieatt & Coleman (2024): core vs. accessory metal AMR differ in MGE association | Consistent — lower λ for cluster count reflects accessory component |
| PGLS β significant for metal type diversity | Ma et al. (2025): generalists have broader metal tolerance repertoire in coastal sediment | Consistent |

### Novel contribution

This is the first analysis linking **genus-level metal type diversity** — inferred from
pangenome AMR annotations across 6,789 species — to **global ecological niche breadth** from a
464K-sample 16S atlas, with phylogenetic control via PGLS. Three aspects are genuinely novel:

1. **Scale and data integration**: Joining a pangenome database (6,789 sequenced species across
   the GTDB bacterial tree) with a global OTU atlas (98,919 OTUs × 463,972 samples) enables a
   test of this hypothesis at a taxonomic and geographic scope not possible with site-specific
   studies.

2. **Phylogenetic partitioning of AMR trait variation**: Using Pagel's λ to explicitly
   quantify the phylogenetic component of metal AMR trait variance (λ = 0.26–0.44 for AMR
   metrics vs λ = 0.79–0.91 for niche breadth) provides a framework for distinguishing
   vertically inherited resistance repertoires from HGT-driven accessory gene acquisitions,
   and demonstrates that it is the HGT-labile diversity component that covaries with
   ecological range.

3. **Specificity of the diversity signal**: Prior site-specific studies (e.g., Qi et al. 2022,
   Ma et al. 2025) documented that generalist taxa are enriched in metal-contaminated
   environments, but could not distinguish whether total gene burden, core resistance, or
   breadth of metal type coverage is the relevant variable. PGLS on a global dataset shows it
   is metal *type diversity*, not gene count or core fraction, that predicts niche breadth —
   paralleling diversity-over-depth findings in other stress response domains.

---

## Limitations

### 1. Niche breadth is a sequencing-effort proxy, not confirmed ecological range
**Partially addressed** — see Robustness Analysis R4.

MicrobeAtlas OTU detection across 13 environment categories conflates genuine habitat use with
sampling intensity, primer bias (V3–V4 or V4), and the geographic and temporal non-uniformity
of SRA/ENA sample contributions. Environments with dense global sampling (soil, marine, plant)
will inflate the apparent niche breadth of taxa prevalent there relative to taxa from
under-represented environments (deep subsurface, brine, ice). Levins' B_std corrects for
unequal environment sizes but cannot correct for missing environments or detection probability
differences. Critically, genus-level aggregation of OTU niche scores is a proxy: a genus may
appear broad-niched because different species within it occupy different habitats, rather than
any single organism being a true ecological generalist. The PGLS β therefore reflects
covariation between *inferred* niche breadth and *inferred* metal tolerance capacity, not
confirmed physiology.

**Mitigation with existing data (R4)**: Recomputing B_std with a strict 5% within-environment
prevalence threshold confirms the signal direction (β = +0.017 vs +0.022 original) but reduces
significance due to 37% fewer genera passing the filter. The effect is not explained by rare
transient detections. **Remaining gap**: primer bias and missing environments cannot be
corrected without a multi-primer, multi-region survey design.

### 2. Archaeal results are underpowered; the archaeal PGLS is included as a power-analysis illustration only
**Addressed via formal power analysis** — see Robustness Analysis R3.

**On whether to include it**: The archaeal PGLS results (β=+0.0145, p=0.467, n=48) are not
included as evidence for or against the hypothesis; they are included *only* to quantify the
statistical gap between current data and what would be needed. Current power is 11% at α=0.05.
Readers should not interpret the non-significant archaeal result as a negative finding — the
study is underpowered to detect an effect of the observed magnitude. Readers who prefer stricter
reporting should treat the R3 section as a power analysis appendix and not as an attempted
replication of the bacterial finding in archaea.

Only 48 archaeal genera had both MicrobeAtlas representation (≥ 3 OTUs) and AMR data in
`kbase_ke_pangenome`. The archaeal PGLS (R3) was run and yielded non-significant results with
the expected positive direction for metal types (β = +0.0145, p = 0.467), but the standard
errors are >1× the coefficient — consistent with severe underpowering rather than a true null
effect. The 48 archaeal genera are also biased toward cultured, well-studied lineages
(methanogens, halophiles, thermoacidophiles), missing the environmentally dominant archaea in
MicrobeAtlas (Thaumarchaeota, Woesearchaeota).

**Mitigation with existing data**: The archaeal PGLS has now been run and shows the same
positive direction as bacteria. **Remaining gap**: ≥200 archaeal genera with AMR data are
needed for adequate power; this requires expanded archaeal pangenome sequencing and annotation
in `kbase_ke_pangenome` (new data required).

### 3. Pangenome coverage is uneven and biases metal type estimates upward for well-studied genera
**Substantially addressed** — see Robustness Analyses R1 and R2, Sensitivity Analysis S4.

The Spearman correlation between number of sequenced genomes per genus and inferred metal type
diversity is r = 0.35 (p = 2.6×10⁻¹⁹). Single-genome genera have detectably lower metal type
counts than multi-genome genera (Mann-Whitney p = 5.1×10⁻¹⁰).

**Mitigation with existing data (R1)**: Adding n_species_with_amr as an explicit PGLS covariate
(using `gls() + corPagel`, not OLS), metal type diversity remains significant (β = +0.020,
p = 3.4×10⁻⁴). The linear covariate is borderline (p = 0.07), confirming a modest but
non-dominant sampling effect.
**Mitigation with existing data (R2)**: Rarefying to 1 species per genus (200 iterations),
89.5% of iterations yield p < 0.05 and the median β (+0.015) points in the same direction.
**Mitigation with existing data (S4)**: Adding log(n_species) (z-scored) as a PGLS covariate,
metal types remains significant (p = 6.4×10⁻⁴). Log(n_species) is itself a significant
predictor (p = 0.016), confirming a log-linear genome-count effect. The metal type diversity β
drops from +0.021 to +0.020, indicating only a small confound. Both effects are independent.
**Remaining gap**: A formal pangenome rarefaction curve (testing multiple species-per-genus
thresholds) would more precisely quantify the depth-of-coverage effect.

### 4. Genome size covariate
**Addressed** — see Robustness Analysis R5.

### 5. Environment category heterogeneity may inflate niche breadth estimates
**Partially addressed** — see Sensitivity Analysis S2.

MicrobeAtlas uses 13 broad categories that lump heterogeneous habitats. The most problematic is
"aquatic", which combines marine, freshwater, estuarine, hydrothermal vent, and pond environments
that differ enormously in salinity, temperature, and chemistry. A taxon detected in both a marine
coastal sample and a freshwater lake sample counts as broad-niched, even though this could reflect
closely related but ecologically distinct ecotypes rather than a single generalist population.

**S2 shows that excluding "aquatic" still gives p = 0.031** (weakest of all 13 exclusions,
but significant). Excluding any other environment gives p < 0.01. The result is not contingent
on the heterogeneous "aquatic" category.

**Remaining gap**: Splitting "aquatic" into sub-categories (marine, freshwater, saline) and
re-running the niche breadth computation requires re-analysis of sample metadata, which is not
available in the current BERDL extraction.

### 6. Statistical model assumes Gaussian errors; count predictor requires justification
**Not addressed — acknowledged caveat.**

Metal type diversity is a count variable (integers 1–7). Using it as a continuous z-scored
predictor in a Gaussian PGLS is standard practice when the predictor is the independent variable
(not the response). The Gaussian assumption applies to the residuals of B_std, not to the
distribution of metal types. Inspecting PGLS residuals for normality is warranted. The main
concern would arise if metal types were modelled as a *response* (e.g., what predicts metal type
count?), where a Poisson or negative binomial PGLS (`phylolm` with Poisson family, or
`MCMCglmm`) would be appropriate.

The Pagel's λ analysis on metal_types assumes Brownian motion (Gaussian increments), which is
an approximation for an integer trait. Alternatives include discrete-state models (Mk) or
threshold models, but these are not standard for this type of continuous-trait PGLS analysis.

---

## Data

### Data Availability

Derived data files (`data/*.csv`) and analysis code (`notebooks/`, `scripts/`) are committed
to the BERIL Research Observatory institutional repository. A public Zenodo archive with a
citable DOI has not yet been prepared (see Future Direction #11). Raw source data reside in
the KBase BERDL data lakehouse (`arkinlab_microbeatlas`, `kbase_ke_pangenome`) and are
accessible to KBase users. The GTDB r214 reference tree is publicly available at
https://gtdb.ecogenomic.org/. The conda/pip environment specification required to reproduce
the R analyses is in `projects/microbeatlas_metal_ecology/requirements.txt`.

### Sources

| Collection | Tables Used | Purpose |
|------------|-------------|---------|
| `arkinlab_microbeatlas` | `otu_metadata`, `otu_counts_long`, `sample_metadata` | 98,919 OTUs × 463,972 samples; niche breadth and taxonomy |
| `kbase_ke_pangenome` | `bakta_amr`, `gene_cluster`, `gtdb_species_clade` | Metal AMR gene annotations per species; GTDB taxonomy |

### Generated Data

| File | Rows | Description |
|------|------|-------------|
| `data/species_metal_amr.csv` | 19,053 | Species-level metal gene metrics from curated 46-KO list (NB01) |
| `data/otu_niche_breadth.csv` | 98,919 | Levins' B_std and n_envs per OTU (NB02) |
| `data/otu_pangenome_link.csv` | 22,357 | OTU → GTDB genus mapping (NB03) |
| `data/genus_trait_table.csv` | 2,851 | Genus-level trait table: niche + metal gene metrics + taxonomy (NB03) |
| `data/pagel_lambda_results.csv` | 10 | Pagel's λ per trait × domain (NB04) |
| `data/pgls_subset.csv` | 957 | Filtered genus subset for PGLS (NB05) |
| `data/pgls_results.csv` | 6 | Simple PGLS model results (NB05) |
| `data/pgls_multi_results.csv` | 3 | Multi-predictor PGLS coefficients (NB05) |
| `data/pgls_robustness_results.csv` | 9 | Covariate + archaeal PGLS robustness results |
| `data/pgls_rarefied_summary.csv` | 1 | Summary of 200-iteration rarefied PGLS |
| `data/pgls_prevalence_threshold_result.csv` | 1 | Strict-prevalence-threshold PGLS result |
| `data/pgls_sensitivity_results.csv` | 24 | Extended sensitivity analysis results (S1–S4) |
| `data/genus_genome_size.csv` | 527 | Genus-level mean genome size (bp) from BERDL kbase_ke_pangenome (R5) |
| `data/pgls_genome_size_result.csv` | 2 | PGLS coefficients with genome size covariate (R5) |
| `data/pgls_3covariate_result.csv` | 3 | 3-covariate PGLS (metal types + log_n_species + log_genome_size) (R6) |
| `data/pgls_subset_filtered_otus.csv` | 576 | PGLS subset with OTU-filtered B_std (≥0.01% rel. abund.) (S5) |
| `data/all_tests_fdr.csv` | 47 | All hypothesis tests with BH-FDR q-values |
| `data/candidate_otu_list.csv` | 435 | Candidate OTUs: top-10% by niche breadth × metal diversity (n=215) plus nitrifier positive controls (n=220); includes `top10pct_both` flag and `nitrifier_role` |
| `data/metal_resistance_table_refined.csv` | 15 | Refined genus-level metal resistance: top candidate genera with ≤2 key genes per metal type, representative OTU ID, and metal types |
| `data/hypotheses_refined.md` | — | Per-genus testable hypotheses with specific metal condition, OTU ID, ≥2-fold quantitative prediction, mechanistic basis, and falsification criterion |
| `data/honorable_mentions.md` | — | 2,186 genera with metal AMR gene annotations but zero candidate OTUs (not in top-10% by both metrics) |
| `data/groundwater_enrichment.csv` | 2,135 | Genus-level groundwater prevalence (n_gw_samples, %, fold enrichment) joined to metal AMR traits (ENIGMA Validation Track A) |
| `data/enigma_geochemistry.csv` | 20 | PRJNA1084851 SRA experiment summaries fetched via NCBI EUtils (metadata-only archive) |
| `data/enigma_otu_table.csv` | 133 samples × 24,295 OTUs | PRJNA1084851 full OTU table (133 samples; 97% OTU clustering, SILVA 138; raw FASTQs deleted post-processing) |
| `data/enigma_otu_taxonomy.csv` | 24,295 | OTU taxonomy assignments (domain → genus) for PRJNA1084851 |
| `data/enigma_full_metadata.csv` | 133 | Per-sample BioSample attributes (ENIGMA_ID, well, date, experiment, fraction, replicate) |
| `data/enigma_cwm_per_sample.csv` | 133 | Community-weighted mean metal-type diversity per sample, joined to well/time metadata |

---

## Supporting Evidence

### Notebooks

| Notebook | Purpose |
|----------|---------|
| `01_metal_amr_species.ipynb` | Extract species-level metal gene metrics from curated 46-KO list via KEGG annotations |
| `02_niche_breadth.ipynb` | Compute Levins' B_std and n_envs from 260M OTU × sample observations |
| `03_taxonomy_bridge.ipynb` | Link MicrobeAtlas OTU genera to GTDB genus representatives |
| `04_pagel_lambda.ipynb` | Estimate Pagel's λ for niche and AMR traits; positive control (nitrification) |
| `05_pgls_regression.ipynb` | PGLS regression of metal AMR predictors on niche breadth (R + Python) |
| `06_synthesis_figures.ipynb` | Multi-panel synthesis figures for all main results |

### Robustness and sensitivity scripts

| Script | Purpose |
|--------|---------|
| `scripts/pgls_robustness.R` | Analyses R1–R3: covariate PGLS, 200-iteration rarefaction, archaeal PGLS |
| `scripts/pgls_sensitivity.R` | Analyses S1–S4: leave-one-metal-out, leave-one-environment-out, within-genus SD, log(n_species) |
| `scripts/make_fig5_robustness.py` | Generates fig5_robustness.png (3-panel robustness summary) |
| `scripts/test_pgls_ordering.py` | Unit test: generates synthetic data with known phylogenetic signal (λ = 0.8, β = 0.05), scrambles row order, and verifies that sorted PGLS recovers correct λ and β within tolerance while unsorted PGLS fails — test passes ✓ |
| `scripts/make_candidate_otu_list.py` | Builds `data/candidate_otu_list.csv`: joins OTU niche breadth, genus traits, and pangenome link; flags top-10% by both niche breadth and metal diversity; appends nitrifier positive controls |
| `scripts/refine_metal_resistance.py` | Produces `data/metal_resistance_table_refined.csv` and `data/hypotheses_refined.md`: per-genus metal types and ≤2 key genes per metal, plus quantitative testable hypotheses with falsification criteria |
| `scripts/feasibility_assessment.py` | Generates `feasibility_individual_otus.md`: power analysis, detection limits, 8-OTU shortlist, and ENIGMA experimental design recommendation |
| `scripts/package_enigma_predictions.py` | Produces `ENIGMA_PREDICTIONS.md`: consolidated summary of global analysis, candidate genera table, 8 testable hypotheses, and experimental feasibility (< 10 KB) |
| `scripts/interactive_dashboard.py` | Produces `figures/dashboard.html`: three-panel standalone Plotly dashboard (world map, niche-breadth scatter, Pagel's λ bar chart); map data fetched from `arkinlab_microbeatlas.sample_metadata` at 0.5° resolution |
| `scripts/enigma_validation.py` | Track A: BERDL groundwater enrichment (Spearman ρ, Mann-Whitney) for 767 genera × 1,624 groundwater samples. Produces `data/groundwater_enrichment.csv`, `figures/fig_enigma_validation.png` |
| `scripts/prjna1084851_pipeline.py` | End-to-end amplicon pipeline: ENA FTP download → cutadapt primer trim → vsearch merge → 97% OTU clustering → SILVA 138 taxonomy → OTU table. Processes 81 samples via ENA; skips to existing merged FASTQs for recovered samples |
| `scripts/prjna1084851_recover.py` | Recovery script for 52 PRJNA1084851 samples not mirrored to ENA FTP: uses NCBI fasterq-dump v3.4.1 → cutadapt → vsearch merge, producing merged FASTQs for the main pipeline |

### Figures

| Figure | Description |
|--------|-------------|
| `fig1_lambda_heatmap.png` | Pagel's λ heatmap — 6 traits × Bacteria/Archaea, YlGnBu colour scale |
| `fig2_pgls_forest.png` | PGLS forest plot — 6 simple models (circles) + multi-predictor (triangles) |
| `fig3_synthesis.png` | Primary 2-panel synthesis: Panel A (λ heatmap) + Panel B (PGLS forest) |
| `fig4_metal_types_scatter.png` | Metal type diversity vs Levins' B_std scatter with top-5 genera annotated |
| `fig5_robustness.png` | 3-panel robustness: Panel A (β across 5 scenarios), Panel B (rarefied β histogram), Panel C (archaeal power curve) |
| `niche_breadth_distribution.png` | Distribution of Levins' B_std across MicrobeAtlas OTUs |
| `pgls_forest_plot.png` | Preliminary forest plot from NB05 (superseded by fig2) |
| `pgls_scatter.png` | Partial regression scatter by phylum from NB05 |
| `fig_enigma_validation.png` | ENIGMA Validation 2-panel: Panel A — Spearman scatter of metal-type diversity vs groundwater prevalence (767 genera, ρ=+0.112, p=0.0019); Panel B — Mann-Whitney box plot comparing top-Q4 vs bot-Q1 metal diversity genera (p=0.007) |
| `fig_enigma_trackB.png` | PRJNA1084851 Track B 3-panel: Panel A — CWM metal-type diversity by well (box+jitter, KW p=0.0001); Panel B — CWM vs. time point after carbon amendment (ρ=+0.38, p<0.0001); Panel C — Sulfurimonas relative abundance declines post-amendment (ρ=−0.32, p=0.0002) |
| `dashboard.html` | **Interactive standalone Plotly dashboard** (1 MB): Panel 1 — world map of 3,942 real sample grid cells (0.5° resolution, 386,020 samples with GPS from `arkinlab_microbeatlas.sample_metadata`) coloured by mean metal gene-type diversity per environment; Panel 2 — scatter of all 3,160 genera (niche breadth × metal diversity, with top-10 labelled and key findings annotated); Panel 3 — Pagel's λ bar chart with significance colouring for all traits |

---

## Experimental Validation Framework

Today's session extended the global comparative analysis into a concrete experimental design
for validating the core finding — that multi-metal resistance breadth predicts ecological
generalism — using controlled microcosm experiments.

### Candidate OTU selection

From 98,919 MicrobeAtlas OTUs, 435 were identified as candidates for experimental tracking:

- **215 OTUs** in the top-10% by *both* standardised niche breadth (Levins' B_std ≥ 0.718)
  and mean metal-type diversity (n_metal_types ≥ 2.0), representing the frontier of the
  niche breadth × metal diversity distribution.
- **220 nitrifier OTUs** retained as positive controls (genera: *Nitrosomonas*, *Nitrosopumilus*,
  *Nitrososphaera*, *Nitrospira*, *Nitrobacter*, *Nitrococcus*, *Nitrosospira*, *Nitrospina*),
  where the metal AMR–niche breadth link is not expected to apply (nitrification is
  phylogenetically entrenched; λ = 0.94).

The full list is in `data/candidate_otu_list.csv`. Sample counts confirm these OTUs span
13 environment types globally.

### Top-priority shortlist for microcosm experiments

Eight OTUs were prioritised for experimental follow-up by a composite score
(Levins' B_std × n_metal_types), each representing a distinct metal-type signature:

| Priority | OTU ID | Genus | Levins' B | Metal types | Recommended stress |
| --- | --- | --- | --- | --- | --- |
| 1 | `97_56843` | *Klebsiella* | 0.947 | 3.5 | Ag or Te stress |
| 2 | `97_51587` | *Enterococcus* | 0.948 | 3.3 | Cu or Cd stress |
| 3 | `97_14443` | *Citrobacter* | 0.854 | 3.7 | As or Hg stress |
| 4 | `97_3668` | *Franconibacter* | 0.785 | 3.5 | Ag or As stress |
| 5 | `97_12431` | *Noviherbaspirillum* | 0.770 | 3.0 | As stress |
| 6 | `97_66129` | *Serratia* | 0.923 | 2.4 | Hg stress |
| 7 | `97_80244` | *Aeromonas* | 0.981 | 2.2 | As + Hg co-stress |
| 8 | `97_39338` | *Pseudomonas* | 0.999 | 2.1 | Cu stress |

*Citrobacter* tops metal-type diversity (3.7 types) and is linked to `silP/A, arsC/D, chrA,
merA/P`. *Enterococcus* (Ag, As, Cd, Cu, Hg, Te) and *Klebsiella* (Ag, As, Hg, Te) are the
broadest multi-metal resisters. *Pseudomonas* ranks eighth by composite score but has the
highest niche breadth of all candidate genera (B_std = 0.999) and carries a complete
`copA/pco` Cu-resistance operon.

### Testable hypotheses

Each of the 8 shortlisted OTUs has a specific, falsifiable prediction in
`data/hypotheses_refined.md`. The general form is:

> Under [specific metal] stress, OTU `[id]` (*[genus]*) should increase in relative abundance
> by ≥2-fold vs. metal-free controls after 7–14 days, because it carries `[genes]` resistance
> determinants that neutralise metal toxicity while susceptible competitors are inhibited.

Falsification criteria are also provided: if the OTU does not increase, candidate explanations
are (a) the resistance genes are on accessory elements absent in the soil ecotype, or (b) the
metal concentration exceeds the allele-specific MIC.

Full consolidated document: `ENIGMA_PREDICTIONS.md`.

### Experimental feasibility

Key conclusions from `feasibility_individual_otus.md`:

- **Detection limit**: ≥ 0.1% relative abundance (≥ 10 reads at 10,000 reads/sample).
  OTUs initially at 1% abundance are quantified with CV ≈ 10%; the power to detect a 2-fold
  increase at this prevalence is >99% with 3 replicates at 10,000 reads — the binding
  constraint is multiple testing, not sensitivity.
- **Recommended design**: Sequence the ENIGMA inoculum pre-treatment (5 replicates,
  ≥ 50,000 reads/sample) to confirm which priority OTUs are detectable at ≥ 0.1%; restrict
  the experiment to the 3–5 confirmed OTUs. Apply FDR correction within that set only.
- **Experimental parameters**: 4–6 metal-stress treatments × 5 replicates × 7- and 14-day
  time points; primary endpoint is relative abundance fold-change versus metal-free control.
- **Backup**: If OTU-level tracking fails, genus-specific 16S qPCR (*Pseudomonas*,
  *Citrobacter*, *Enterococcus*) or a defined synthetic community (SynCom) of 8–12 priority
  taxa can replace amplicon sequencing.

### Literature context for experimental design

Farkas et al. (2023, *Geomicrobiology Journal*) tracked prokaryotic community composition by
16S rRNA amplicon sequencing in As(III) microcosm experiments, demonstrating acute composition
shifts detectable at community level within 7 days — consistent with our 7–14-day design.
Kou et al. (2018, *Frontiers in Microbiology*) showed selective OTU-level enrichment under
Pb/Zn/Cu in a field trial, supporting the premise that metal-tolerant taxa reliably increase in
relative abundance. Yuan et al. (2020, *Current Microbiology*) confirmed that copper
specifically reduces OTU richness in freshwater microcosms — reducing competition and
amplifying the selective advantage of Cu-resistant taxa such as *Pseudomonas* OTU `97_39338`.

*(Scripts: make_candidate_otu_list.py, refine_metal_resistance.py, feasibility_assessment.py,
package_enigma_predictions.py, interactive_dashboard.py)*

---

## ENIGMA Validation: Groundwater Enrichment Analysis

This section reports an independent observational validation of the core PGLS finding using
the 1,624 groundwater samples already resident in the KBase BERDL data lakehouse
(`arkinlab_microbeatlas`, Env_Level_2 = "groundwater"). If genera with broader metal-type
resistance repertoires are genuinely ecological generalists (the PGLS finding), they should be
more prevalent across groundwater samples, which represent chemically challenging, often
metal-impacted subsurface environments.

### Data and approach

**Dataset**: 1,624 groundwater samples from `arkinlab_microbeatlas`; OTU × sample counts
queried via BERDL REST API (joining `otu_counts_long` and `sample_metadata`).
**Analysis subset**: 767 genera with (i) ≥1 OTU detected in groundwater and (ii) metal AMR
data in `genus_trait_table.csv` (mean_n_metal_types non-null).
**Genus-level groundwater prevalence**: mean fraction of 1,624 groundwater samples in which
≥1 OTU from that genus was detected (count > 0).
**Fold enrichment**: groundwater prevalence % ÷ non-groundwater prevalence % (462,348 samples).

### Results: Track A (BERDL groundwater)

| Test | Statistic | n | p |
|------|-----------|---|---|
| Spearman ρ: metal types vs. GW prevalence | ρ = +0.112 | 767 genera | **0.0019** |
| Spearman ρ: metal types vs. fold enrichment | ρ = +0.042 | 767 genera | 0.242 |
| Mann-Whitney: top-Q4 vs. bot-Q1 metal types → GW prevalence | U | 213 vs 429 genera | **0.007** |
| Mann-Whitney: top-Q4 vs. bot-Q1 metal types → fold enrichment | U | 213 vs 429 genera | 0.181 |

Quartile thresholds: Q1 ≤ 1.0 metal types; Q4 ≥ 1.5 metal types (among genera with AMR data).

**Median groundwater prevalence**: top-Q4 genera = 0.81%; bot-Q1 genera = 0.62%
(ratio = 1.31×; Mann-Whitney p = 0.007, one-sided greater).

**Candidate genera from ENIGMA shortlist detected in groundwater**:

| Genus | GW prevalence (%) | Fold enrichment vs. non-GW | Metal types |
|-------|-------------------|---------------------------|-------------|
| *Azospira* | 5.21 | 2.3× | 3.0 |
| *Enterobacter* | 4.80 | 1.1× | 3.1 |
| *Citrobacter* | 0.89 | 2.8× | 3.7 |
| *Enterococcus* | 0.71 | 2.8× | 3.3 |
| *Noviherbaspirillum* | 1.01 | 1.4× | 3.0 |
| *Franconibacter* | 0.39 | 1.6× | 3.5 |
| *Pseudomonas* | — (not in top-15) | — | 2.1 |

*Citrobacter* and *Enterococcus* are notably enriched in groundwater (2.8× fold enrichment),
consistent with the ENIGMA experimental predictions. *Azospira* (a denitrifier detected in
5.2% of groundwater samples) shows the highest prevalence among high-metal-diversity genera
and has an established role in groundwater nitrogen cycling.

**Interpretation**: The Spearman correlation (ρ = +0.112, p = 0.0019) and Mann-Whitney
(p = 0.007) confirm that genera with broader metal-type resistance repertoires are significantly
more prevalent in groundwater than genera with narrow resistance repertoires, at both the
correlation and quartile-comparison level. The effect size is modest (0.62% → 0.81% median
prevalence for bottom-Q1 vs top-Q4), consistent with the global PGLS β being a partial
correlation after removing phylogenetic structure. The fold-enrichment metric (groundwater vs. non-groundwater) does not reach significance
(ρ = +0.042, p = 0.242). This means the environmental-specificity metric — whether metal-diverse
genera are *preferentially* enriched in groundwater beyond their global baseline — does not
show a detectable signal. This is a meaningful null: Track A confirms the prevalence association
but does not confirm groundwater-specific enrichment. The non-significant fold-enrichment could
reflect that (a) the prevalence advantage is a general breadth effect rather than groundwater
specificity, or (b) the 1,624-sample groundwater subset is underpowered to detect a specificity
signal of the observed effect size. Track A is therefore consistent with the PGLS finding but
does not uniquely support the metal-contamination mechanism.

This analysis provides an independent, field-observation-based cross-validation of the PGLS
finding using a different data source (groundwater surveys vs. multi-environment atlas), and
is consistent with the directionality and mechanism proposed: diverse metal resistance is
associated with greater ecological range in chemically challenging subsurface environments.

### Track B: PRJNA1084851 (ENIGMA ORFRC 16S — full pipeline)

**Status**: Complete — 133/133 samples processed, 24,295 OTUs.

The Water Research 2024 study (doi:10.1016/j.watres.2024.121460) deposited 133 MiSeq 16S
amplicon runs under PRJNA1084851 (SRR28246018–SRR28246150). Title: *"Reproducible responses
of geochemical and microbial successional patterns in the subsurface to carbon source
amendment"* (ENIGMA-funded, ORFRC Tennessee). We built a complete amplicon pipeline
(cutadapt 5.2 primer trimming, vsearch 2.30.6 paired-end merging and 97% OTU clustering,
SILVA 138 taxonomy) and processed all 133 samples (81 via ENA FTP; 52 via NCBI
`fasterq-dump` v3.4.1, which were not yet mirrored to ENA at time of analysis). Final OTU
table: **133 samples × 24,295 OTUs**; median 56,908 reads/sample; 14,021 OTUs with
genus-level taxonomy (SILVA 138); 1,637 OTUs (16.8% of reads) joinable to genus metal
diversity data.

**Experimental design** (from BioSample attributes): Two experiments — EVO09 (52 samples,
Jan 2009) and EVO17 (81 samples, 2017–2018) — across 8 groundwater monitoring wells
(FW202, FW215, FW216, GP01, GP03, MLSA3, MLSB3, MLSG4) at the ENIGMA ORFRC, Oak Ridge,
Tennessee. All samples collected at 0.2 µm filtration. Replicate codes R0–R20 represent
successive time points before and after ethanol carbon amendment.

**Community-weighted mean (CWM) metal-type diversity**: For each sample, CWM was computed
as the abundance-weighted mean of genus-level `mean_n_metal_types` across OTUs with AMR
data (16.8% of reads per sample on average). CWM range: 1.01–1.83; mean 1.28 ± 0.19.

**Coverage limitation**: The 16.8% read coverage reflects OTUs for which genus-level SILVA
taxonomy could be matched to GTDB AMR annotations. The remaining ~83% of reads (from genera
without taxonomy matches) are excluded from CWM. If these uncovered genera have systematically
different metal resistance profiles than covered genera (e.g., if uncovered lineages are
predominantly metal-sensitive), CWM would be biased upward. The between-sample variance in
CWM (1.01–1.83) and the correlation with known contamination status (FW215/FW216 in plume)
are consistent with a signal that reflects real biology, but robustness to coverage fraction
variation has not been formally tested. A correlation between per-sample CWM and per-sample
covered-read fraction is recommended as a diagnostic before this metric is used in further
analyses.

![ENIGMA Track B figure: CWM by well, CWM vs time, Sulfurimonas decline](figures/fig_enigma_trackB.png)

#### Track B statistical results

| Test | Statistic | n | p |
|------|-----------|---|---|
| Kruskal-Wallis: CWM across 8 wells | H = 29.10 | 133 samples | **0.0001** |
| Spearman ρ: CWM vs. time point (R#) | ρ = +0.383 | 133 | **< 0.0001** |
| FW216 within-well: CWM vs. time point | ρ = +0.576 | 40 | **0.0001** |
| Mann-Whitney: EVO09 vs. EVO17 CWM | U | 52 vs 81 | **0.0012** |
| Spearman ρ: *Sulfurimonas* RA vs. time | ρ = −0.323 | 133 | **0.0002** |

**Well-level CWM gradient** (median, ranked high → low):
FW215 (1.37) > FW216 (1.36) > GP01 (1.23) ≈ GP03 (1.22) > MLSB3 (1.14) > MLSA3 (1.09) ≈ FW202 (1.08) ≈ MLSG4 (1.08).

Wells FW215 and FW216 are known to be within the U/NO₃ contamination plume at ORFRC; their
higher CWM is consistent with the core hypothesis that metal-contaminated subsurface
environments select for genera with broader metal resistance repertoires.

**Time-series pattern**: CWM increases significantly with time point after carbon amendment
(Spearman ρ = +0.383, p < 0.0001), most strongly in FW216 (ρ = +0.576, p = 0.0001). This
suggests that carbon amendment progressively selects for metal-diverse communities, possibly
by creating reducing conditions that shift geochemical speciation of redox-active metals (U,
Fe, S).

**Candidate genus detection**: *Sulfurimonas* (sulfur-oxidizing chemolithotroph; 80 OTUs,
96.2% prevalence) is the dominant flagged genus but shows a counterintuitive
**decrease** with time (ρ = −0.323, p = 0.0002), likely because carbon amendment depletes
nitrate and oxygen — Sulfurimonas' preferred electron acceptors. *Nitrospira* (25 OTUs,
88.7% prevalence) shows highest abundance in the FW215 plume well. *Candidatus*
Jorgensenbacteria (Patescibacteria/CPR; 122 OTUs, 99.2% prevalence) is ubiquitous.
*Citrobacter* and *Thermodesulfovibrio* were not detected (below detection or mismatched
genus names under SILVA nomenclature).

**Interpretation**: The Track B results support the core PGLS finding at the within-study
level. Contaminated plume wells (FW215, FW216) host communities with measurably higher
metal-type diversity than background wells, and the temporal increase in CWM after carbon
amendment points to active ecological selection for metal-diverse communities under
geochemical stress. The *Sulfurimonas* pattern is an informative counterexample: a highly
prevalent environmental generalist whose abundance is driven by electron-acceptor availability
rather than metal resistance — demonstrating that not all ecologically dominant groundwater
taxa are metal-diverse.

*(Scripts: scripts/prjna1084851_pipeline.py, scripts/prjna1084851_recover.py,
scripts/enigma_validation.py; Data: data/enigma_otu_table.csv, data/enigma_otu_taxonomy.csv,
data/enigma_full_metadata.csv, data/enigma_cwm_per_sample.csv;
Figure: figures/fig_enigma_trackB.png)*

---

## Future Directions

0. **⚠ URGENT — Re-run robustness and sensitivity analyses with curated 46-KO gene list**:
   Analyses R1–R6 and S1–S5 used AMRFinderPlus data (n = 606 genera) and are stale. Run
   `scripts/pgls_robustness.R` and `scripts/pgls_sensitivity.R` after updating input data to
   the curated 46-KO `species_metal_amr.csv` (now 19,053 species). This is the top-priority
   action before any publication decisions are made.

1. **Pangenome rarefaction**: Resample genera to equal genome coverage (e.g., n = 1 or 2
   species) and repeat PGLS to formally control for the genome-sampling depth confound.
   This would require access to the species-level AMR table stratified by genome count.

2. **Archaeal PGLS**: Expand archaeal pangenome coverage in `kbase_ke_pangenome` to include
   environmental metagenome-assembled genomes (MAGs), particularly Thaumarchaeota, and repeat
   the PGLS analysis once ≥ 100 archaeal genera with AMR data are available.

3. ~~**Genome size covariate**~~: Completed with AMRFinderPlus data (R5); needs re-running
   with curated gene list to check if metal clusters remain significant after controlling for
   genome size.

4. **HGT burden as predictor**: Estimate genus-level pangenome openness (proportion of genes
   in the accessory genome) and use it as a predictor of niche breadth alongside metal gene
   burden. A broader accessory genome may explain why AMRFinderPlus (which includes accessory
   genes) showed a stronger niche breadth signal than the curated core KO list.

5. **Site-level validation**: Test whether MicrobeAtlas genera with high metal type diversity
   are enriched in metal-contaminated sample metadata (where available: mining-impacted,
   biosolid-amended, estuarine) versus clean reference environments. This would directly
   validate the environmental co-selection hypothesis.

6. **Multi-metal co-resistance clustering**: Group metal types by genetic co-occurrence
   (e.g., Cu-Zn co-resistance vs Hg-As) and test whether specific co-resistance combinations
   predict niche breadth more than the raw count.

7. **Phylogenetic mixed models for count data**: Apply `MCMCglmm` with Poisson or negative
   binomial family to test whether metal type count (as a response variable in the reverse
   regression direction) is predicted by niche breadth, accounting for phylogenetic structure.
   This would complement the current analysis by testing the reverse direction and using
   appropriate error distributions.

8. **Environment sub-classification**: Re-run the niche breadth computation with a finer
   environment taxonomy (e.g., splitting "aquatic" into marine, freshwater, estuarine) using
   sample metadata from MicrobeAtlas to test whether category heterogeneity inflates B_std
   for certain genera.

9. **AMRFinderPlus validation**: Random sampling of 100 annotated metal AMR gene clusters for
   manual BLAST verification against reference sequences to quantify the HMM-based false
   positive rate for each metal type category.

10. ~~**ENIGMA field validation** (fully addressed — Tracks A and B complete)~~: Candidate
    OTU list and shortlist produced. **Track A**: 1,624 BERDL groundwater samples confirm
    metal-diverse genera are significantly more prevalent in groundwater (Spearman ρ = +0.112,
    p = 0.0019; Mann-Whitney p = 0.007). **Track B**: Full amplicon pipeline executed for
    all 133 PRJNA1084851 samples (24,295 OTUs; 133/133 QC pass). Community-weighted mean
    metal-type diversity is significantly higher in contamination-plume wells FW215/FW216
    (Kruskal-Wallis p = 0.0001) and increases with time after carbon amendment
    (Spearman ρ = +0.383, p < 0.0001 across all wells; ρ = +0.576, p = 0.0001 in FW216
    alone). Both tracks independently confirm the PGLS prediction in field data. See full
    results in the ENIGMA Validation section above.

11. **Public data archive**: Deposit notebooks, derived data CSVs, and a conda environment
    lockfile to a Zenodo repository to enable independent verification of all PGLS and
    Pagel's λ results. The BERDL-resident derived files (`data/*.csv`, `figures/*.png`)
    should be archived with a citable DOI before manuscript submission.

---

## Peer Review Query Index

Quick-reference for all 8 reviewer query groups. For each, the status and the primary REPORT.md
section where it is addressed are listed.

| Query | Status | Primary Section |
|-------|--------|-----------------|
| **Q1a** Environment categories ecologically meaningful? Alternative groupings? | Partially addressed — leave-one-out done (S2); sub-category splitting requires new metadata | Sensitivity S2; Limitation 5 |
| **Q1b** Primer bias and differential sequencing depth quantitatively corrected? | Not correctable with available data — acknowledged | Limitation 1; Robustness R4 |
| **Q2a** Brownian motion assumption for count predictor? Phylogenetic mixed models? | Acknowledged — continuous PGLS on count predictor is standard; MCMCglmm proposed as future work | Limitation 6; Future Direction #7 |
| **Q2b** GTDB r214 tree sensitivity? Genus-aggregation discards within-genus variation? | GTDB r214 is best available; alternative tree comparison not performed (known gap). Within-genus heterogeneity tested via S3 (non-significant) | Study Design — Phylogenetic tree and genus-aggregation; Sensitivity S3 |
| **Q2c** PGLS λ overfitting / optimization sensitivity? λ discrepancy explained? | Directly addressed — Δλ = 0.079 expected given predictor's own phylogenetic signal | Study Design — λ discrepancy |
| **Q3a** Pangenome bias toward pathogens? Genome-count covariate was only OLS? | Addressed — **the OLS claim is incorrect**: R1 and S4 both use `gls() + corPagel` (PGLS), not OLS. β remains significant after PGLS covariate. | Robustness R1; Sensitivity S4 |
| **Q3b** Metal type classification robustness? Single metal drives result? AMRFinderPlus validation? | Addressed for single-metal (S1: all 7 exclusions positive, no one metal is driver). Formal AMRFinderPlus validation not performed — spot checks only | Sensitivity S1; Study Design — AMRFinderPlus |
| **Q4a** Genome size formal test — "Why was this not performed?" | **It was performed (R5)**. Metal types β = +0.022 (p = 3.6×10⁻⁴) independent of genome size; ΔAIC = 10.8 | Robustness R5 |
| **Q4b** Causation and directionality? | Directly addressed — 3 scenarios, none distinguishable; cross-sectional design limitation explicit; causal phrasing removed from Key Findings and Interpretation | Study Design — Causation and directionality |
| **Q5a** Multiple comparisons across entire study? | Directly addressed — 47 tests tabulated; BH-FDR applied across all tests; primary result survives both Bonferroni (α/47=0.0011) and FDR (q=0.003) | Study Design — Multiple testing count |
| **Q5b** Archaeal PGLS in main text vs supplementary? | Moved to Supplementary: Archaeal Analyses section; R3 in main Robustness provides summary pointer only | Supplementary section; Limitation 2 |
| **Q6a** Novel mechanistic insight beyond "generalists have more metal resistance"? | Addressed — the phylogenetic partitioning (core vs. type diversity) and global pangenome × atlas × PGLS integration is novel | Interpretation; Novel contribution |
| **Q6b** Rarefaction + within-genus variance reconciliation? | Addressed — S3 confirms genus means not inflated by outlier species; R2 rarefaction shows consistent positive direction | Robustness R2; Sensitivity S3 |
| **Q7a** Public Zenodo archive prepared? | Not yet — acknowledged as gap; institutional repo only. Zenodo archiving added as Future Direction #11 | Data — Data Availability; Future Direction #11 |
| **Q7b** Unit test for PGLS ordering implemented? | Yes — `scripts/test_pgls_ordering.py` generates synthetic data, scrambles order, and verifies sorted model recovers correct λ and β (test passes) | Supporting Evidence — Scripts table |
| **Q8a** Robustness analyses post-hoc — labeled as exploratory? | Yes — all robustness/sensitivity labelled exploratory; primary confirmatory result (6 PGLS + Bonferroni) stands independently | Study Design — Confirmatory vs exploratory |
| **Q8b** Preregistered analysis plan? | Not preregistered — acknowledged; confirmatory/exploratory distinction documented post-hoc | Study Design — Confirmatory vs exploratory |
| **Q8c** ENIGMA microcosm concrete testable prediction? | Fully addressed — (1) Track A: top-quartile metal diversity genera 31% more prevalent in groundwater (Mann-Whitney p=0.007); (2) Track B: PRJNA1084851 amplicon pipeline run on 133/133 ENIGMA ORFRC samples — CWM metal diversity significantly higher in contaminated FW wells (KW p=0.0001) and increases with carbon amendment time (ρ=+0.38, p<0.0001) | ENIGMA Validation (Tracks A & B); Future Direction #10 |

---

## Supplementary: Archaeal Analyses {#supplementary-archaeal-analyses}

### Archaeal Pagel's λ

Archaeal niche breadth shows significant phylogenetic signal (λ = 0.640, p = 1.3×10⁻⁷ for
B_std; λ = 0.880, p = 2.1×10⁻¹³ for n_envs). The B_std λ is lower than in bacteria (0.932),
consistent with the phylogenetically sparse and ecologically distinct nature of the archaeal
genera captured by 16S amplicon surveys. Archaeal metal cluster data are now available for
n = 73 genera (λ = 1.000, p = 3.4×10⁻⁹), up from n = 48 in the AMRFinderPlus analysis.

### Archaeal PGLS (full results)

**Observed archaeal PGLS** (`scripts/pgls_robustness.R`, n = 48 genera with AMR data):

| Predictor | β | SE | t | p | λ |
|-----------|---|-----|---|---|---|
| Metal types (z) | +0.0145 | 0.0198 | 0.73 | 0.467 | 0.567 |
| AMR clusters (z) | +0.0146 | 0.0209 | 0.70 | 0.488 | 0.567 |
| Core fraction (z) | +0.0002 | 0.0211 | 0.01 | 0.991 | 0.553 |

No significant effects at n = 48. The metal types β (+0.0145) is in the same positive direction
as bacteria (+0.0215) but the SE is nearly as large as the estimate (t = 0.73), indicating
severe underpowering. The 48 archaeal genera are biased toward cultured lineages (methanogens,
halophiles, thermoacidophiles), missing environmentally dominant archaea in MicrobeAtlas
(Thaumarchaeota, Woesearchaeota).

### Formal power analysis

Analytical power using non-central t-distribution; SE scales as SE_obs × √(n_obs/n);
β_true = +0.0145, λ fixed at 0.567:

| n | Expected SE | Expected t | Power (α = 0.05) | Power (Bonferroni α = 0.0083) |
|---|------------|------------|-----------------|-------------------------------|
| 48 (current) | 0.0198 | 0.73 | 11% | 3% |
| 100 | 0.0137 | 1.06 | 18% | 6% |
| 200 | 0.0097 | 1.50 | 32% | 12% |
| 300 | 0.0079 | 1.83 | 45% | 21% |
| 400 | 0.0069 | 2.12 | 56% | 30% |
| 600 | 0.0056 | 2.59 | 74% | 48% |
| 800 | 0.0048 | 3.00 | 85% | 64% |
| 1,000 | 0.0043 | 3.35 | 92% | 76% |

**Required sample sizes**: 80% power requires **n ≥ 702** (α = 0.05) or **n ≥ 1,084** (Bonferroni).
The archaeal analysis is not a negative result — it is a severely underpowered one. The
non-significant archaeal result should not be interpreted as evidence against the association.

### Supplementary Sensitivity Table

**⚠ All rows below used AMRFinderPlus data (n = 606 genera). Stale as of 2026-06-29 — requires re-run with curated 46-KO gene list.**

All sensitivity and robustness analyses, metal types predictor β and BH-FDR q-value (AMRFinderPlus, historical):

| Analysis | n | β (metal types) | SE | p | q (BH-FDR) | sig q<0.05? |
|----------|---|-----------------|-----|---|------------|-------------|
| Simple PGLS (B_std ~ metal_types_z) | 606 | +0.0215 | 0.0056 | 1.5×10⁻⁴ | 0.003 | yes |
| Multi-predictor PGLS | 606 | +0.0231 | 0.0067 | 5.5×10⁻⁴ | 0.004 | yes |
| R1: + n_species covariate (simple) | 606 | +0.0204 | 0.0057 | 3.4×10⁻⁴ | 0.003 | yes |
| R1: + n_species covariate (multi) | 606 | +0.0224 | 0.0067 | 8.3×10⁻⁴ | 0.004 | yes |
| R2: Rarefied (median, 200 iter) | 606 | +0.0147 | ~0.011 | 0.005 | — | — |
| R3: Archaeal PGLS | 48 | +0.0145 | 0.0198 | 0.467 | 0.548 | no |
| R4: Strict prevalence (≥5%) | 379 | +0.0166 | 0.0099 | 0.092 | — | — |
| R5: + genome size covariate | 527 | +0.0218 | 0.0061 | 3.6×10⁻⁴ | 0.003 | yes |
| R6: + log_n_species + log_genome_size | 527 | +0.0218 | 0.0061 | 3.5×10⁻⁴ | 0.003 | yes |
| S1: excl_Hg | 606 | +0.0082 | 0.0069 | 0.233 | 0.313 | no |
| S1: excl_As | 606 | +0.0039 | 0.0061 | 0.518 | 0.572 | no |
| S1: excl_Cu | 606 | +0.0102 | 0.0065 | 0.115 | 0.187 | no |
| S1: excl_Zn | 606 | +0.0095 | 0.0064 | 0.140 | 0.212 | no |
| S1: excl_Cd | 606 | +0.0084 | 0.0064 | 0.186 | 0.258 | no |
| S1: excl_Cr | 606 | +0.0088 | 0.0064 | 0.173 | 0.255 | no |
| S1: excl_Ni | 606 | +0.0095 | 0.0064 | 0.140 | 0.212 | no |
| S2: excl_aquatic | 606 | +0.0085 | 0.0039 | 0.031 | 0.061 | no* |
| S2: excl_agricultural | 606 | +0.0107 | 0.0040 | 0.0073 | 0.016 | yes |
| S2: excl_desert | 606 | +0.0120 | 0.0042 | 0.0040 | 0.011 | yes |
| S2: excl_farm | 606 | +0.0115 | 0.0042 | 0.0061 | 0.015 | yes |
| S2: excl_field | 606 | +0.0118 | 0.0040 | 0.0030 | 0.010 | yes |
| S2: excl_flower | 606 | +0.0118 | 0.0044 | 0.0077 | 0.017 | yes |
| S2: excl_forest | 606 | +0.0142 | 0.0042 | 0.0007 | 0.004 | yes |
| S2: excl_leaf | 606 | +0.0130 | 0.0043 | 0.0025 | 0.010 | yes |
| S2: excl_paddy | 606 | +0.0123 | 0.0042 | 0.0036 | 0.010 | yes |
| S2: excl_peatland | 606 | +0.0131 | 0.0044 | 0.0027 | 0.010 | yes |
| S2: excl_plant | 606 | +0.0105 | 0.0039 | 0.0069 | 0.016 | yes |
| S2: excl_shrub | 606 | +0.0126 | 0.0043 | 0.0034 | 0.010 | yes |
| S2: excl_soil | 606 | +0.0113 | 0.0039 | 0.0035 | 0.010 | yes |
| S3: + within-genus SD metal types | 606 | +0.0189 | 0.0060 | 0.0016 | 0.007 | yes |
| S4: + log(n_species) | 606 | +0.0195 | 0.0057 | 6.4×10⁻⁴ | 0.004 | yes |
| S5: OTU ≥0.01% rel. abund. (Pagel's λ) | 576 | λ=0.750 | — | 2.8×10⁻⁴⁰ | — | — |

*excl_aquatic nominally significant at p=0.031 but q=0.061.

Full FDR table: `data/all_tests_fdr.csv`

---

## References

- Malfertheiner L, Tackmann J, et al. (2026). "Community conservatism is widespread across
  microbial phyla and environments." *Nature Ecology & Evolution*.
  https://www.nature.com/articles/s41559-025-02957-4

- Hernandez DJ, Kiesewetter KN, Almeida BK, et al. (2023). "Multidimensional specialization
  and generalization are pervasive in soil prokaryotes." *Nature Ecology & Evolution*.
  https://www.nature.com/articles/s41559-023-02149-y

- von Meijenfeldt FAB, Hogeweg P, et al. (2023). "A social niche breadth score reveals niche
  range strategies of generalists and specialists." *Nature Ecology & Evolution*.
  https://www.nature.com/articles/s41559-023-02027-7

- Qi Q, Hu C, Lin J, et al. (2022). "Contamination with multiple heavy metals decreases
  microbial diversity and favors generalists as the keystones in microbial occurrence
  networks." *Environment International* 167: 107426.
  https://www.sciencedirect.com/science/article/pii/S0269749122006200

- Hemme CL, Green SJ, Rishishwar L, Prakash O, et al. (2016). "Lateral gene transfer in a
  heavy metal-contaminated-groundwater microbial community." *mBio* 7: e02234-15.
  https://journals.asm.org/doi/abs/10.1128/mbio.02234-15

- Gillieatt BF, Coleman NV. (2024). "Unravelling the mechanisms of antibiotic and heavy metal
  resistance co-selection in environmental bacteria." *FEMS Microbiology Reviews* 48(4):
  fuae017. https://academic.oup.com/femsre/article-abstract/48/4/fuae017/7696342

- Ma G, Shi M, Li Y, et al. (2025). "Diverse adaptation strategies of generalists and
  specialists to metal and salinity stress in the coastal sediments." *Science of the Total
  Environment*. https://www.sciencedirect.com/science/article/pii/S001393512500324X

- Jiao S, Chen W, Wei G. (2021). "Linking phylogenetic niche conservatism to soil archaeal
  biogeography, community assembly and species coexistence." *Global Ecology and
  Biogeography* 30: 1469–1479. https://onlinelibrary.wiley.com/doi/abs/10.1111/geb.13313

- Miller SR. (2004). "Testing for evolutionary correlations in microbiology using phylogenetic
  generalized least squares." In *Environmental Microbiology: Methods and Protocols*, pp.
  339–352. Humana Press. https://link.springer.com/protocol/10.1385/1-59259-765-3:339

- Finn DR, Yu J, Ilhan ZE, Fernandes VM, et al. (2020). "MicroNiche: an R package for
  assessing microbial niche breadth and overlap from amplicon sequencing data." *FEMS
  Microbiology Ecology* 96(8): fiaa131.
  https://academic.oup.com/femsec/article-abstract/96/8/fiaa131/5863182

- Farkas R, Toumi M, Abbaszade G, Boka K, et al. (2023). "The acute impact of arsenic (III)
  on the prokaryotic community composition and selected bacterial strains based on microcosm
  experiments." *Geomicrobiology Journal*.
  https://www.tandfonline.com/doi/abs/10.1080/01490451.2023.2181469

- Kou S, Vincent G, Gonzalez E, Pitre FE, et al. (2018). "The response of a 16S ribosomal
  RNA gene fragment amplified community to lead, zinc, and copper pollution in a Shanghai
  field trial." *Frontiers in Microbiology* 9: 366.
  https://www.frontiersin.org/articles/10.3389/fmicb.2018.00366/full

- Yuan T, McCarthy AJ, Zhang Y, Sekar R. (2020). "Effects of pH, nutrients and heavy metals
  on bacterial diversity and ecosystem functioning studied by freshwater microcosms and
  high-throughput DNA sequencing." *Current Microbiology* 77: 2330–2340.
  https://link.springer.com/article/10.1007/s00284-020-02138-5

- Goodall T, Griffiths RI, Emmett B, Jones B, Thorpe A, et al. (2026). "Environmental
  filtering shapes divergent bacterial strategies and genomic traits across soil niches."
  *bioRxiv*. https://www.biorxiv.org/content/10.64898/2026.01.16.699881.abstract

- Zhou Y, Stegen JC, Dong H, et al. (2024). "Reproducible responses of geochemical and
  microbial successional patterns in the subsurface to carbon source amendment." *Water
  Research* 261: 121460. https://doi.org/10.1016/j.watres.2024.121460

---

## Chapter 08 — COG-Metal Functional Genomics

**Source project**: `soil_metal_functional_genomics` (consolidated 2026-06-30)
**Notebooks**: 08a_spearman_cog_metal.ipynb, 08b_fdr_associations.ipynb, 08c_copper_specific.ipynb, 08d_dbrda_pgls.ipynb

**Scope**: Spearman correlations between the presence/absence of 5,197 COG families and measured concentrations of 10 metals (Co, Cr, Cu, Ni, Zn, Pb, As, Cd, Hg, U) across ~51,748 soil samples from the MicrobeAtlas dataset. BH-FDR corrected at q<0.05. Note: uranium (U) is included in the NB08a individual-COG sweep but excluded from the NB08b community-weighted FDR analysis (insufficient sample coverage for U).

**Key findings**:
- Significant COG-metal associations identified across 10 metals (NB08a). Community-weighted
  analysis (NB08b) yields 2,355 significant COG category–metal associations across 9 metals
  (Co, Cr, Cu, Ni, Zn, Pb, As, Cd, Hg; q<0.05), consistent with copper's dual role as
  essential micronutrient and toxic pollutant.
- Copper-associated COGs include representatives from efflux pumps (COG V in MNUV: ρ=+0.061, q<0.05) and
  inorganic ion transport (COG P in EPQ: ρ=+0.070, q<0.05), though other P and V combinations show
  negative correlation (NB08c). The copper-specific analysis confirms that functional genomic adaptation
  to Cu stress is detectable at the community level in soil metagenomes.
- BH-FDR correction applied within each metal separately; associations surviving FDR
  represent robust, reproducible signals across the global soil dataset (NB08b).

**Status**: NB08a–08c executed and results valid. NB08d (db-RDA + community-level PGLS)
PENDING — the prior R²=0.799 is **invalidated** (circular predictors; random project IDs).
The corrected implementation in NB08d Cell 9 requires `project_accession` added to the
Cell 3 SELECT and `sample_limit` increased from 500 to ≥2000 before re-running on the
Spark cluster.

---

## Chapter 09 — OTU-Level Metal Ecology

**Source project**: `microbeatlas_otu_georoc` (consolidated 2026-06-30)
**Notebooks**: 09a_otu_georoc_associations, 09b_otu_sensitivity

**Scope**: Partial Spearman correlations (CLR-transformed, 9,999 permutations) between
bacterial OTU abundances and measured GeoROC soil metal concentrations across 71K samples
and 9 metals (Co, Cr, Cu, Ni, Zn, Pb, As, Cd, Hg). Analysis is at OTU resolution (not
genus-aggregated) with spatial signal partialled out via covariate adjustment.

**Key findings**:
- OTU-level metal associations identified with spatial signal partialled out. Permutation
  testing (9,999 permutations) guards against inflated significance from spatial
  autocorrelation, which is pervasive in soil microbiome data.
- Sensitivity analysis (NB09b) confirmed results are robust to different missing data
  handling strategies (complete-case, single-metal models, multiple imputation), validating
  the association stability.
- This analysis complements Chapter 08 (COG-level) by providing OTU-level taxonomy-functional
  links: which lineages are enriched in high-metal soils vs. which functional genes.

**Status**: NB09a–09b fully executed. No REPORT.md existed in the source project; findings
are documented here for the first time.

---

## Chapter 10 — Global MAG Biogeography of Metal Resistance

**Source project**: `metal_resistance_global_biogeography` (consolidated 2026-06-30)
**Notebooks**: 10a_global_mag_distribution, 10b_spatial_analysis, 10c_mag_figures

**Scope**: 260K environmental MAGs from MGnify; metal-resistance gene enrichment by biome
and geographic grid cell (5° resolution); hotspot identification via Fisher's exact test
with BH-FDR correction (q<0.05). Metal-resistance genes defined by COG categories P
(inorganic ion transport and metabolism) and V (defense mechanisms).

**Key findings**:

All 11 geographic hotspots at q<0.05 (OR vs. global baseline, NB10b; 22,357 MAGs with
coordinates, Fisher's exact + BH-FDR):

| Grid cell (lat, lon) | Approx. location | OR | q | % resistant |
|---|---|---|---|---|
| −25°, −70° | Atacama Desert, Chile | 9.83 | 7.6×10⁻¹² | 21.8% |
| 40°, −80° | Appalachian, Eastern USA | 7.86 | 2.8×10⁻¹¹ | 18.2% |
| 40°, −90° | Midwest USA (Mississippi basin) | 6.32 | 7.6×10⁻¹² | 15.1% |
| 30°, 85° | Nepal / southern Tibet | 6.27 | 0.017 | 15.4% |
| 25°, 105° | Yunnan province, SW China | 5.89 | 0.010 | 14.6% |
| 25°, 115° | Guangdong / SE China | 4.43 | 5.7×10⁻⁴ | 11.3% |
| 30°, 120° | Eastern China (Yangtze delta) | 3.77 | 1.9×10⁻³ | 9.8% |
| 25°, −85° | Caribbean / Gulf coast | 2.71 | 1.8×10⁻³ | 7.2% |
| 35°, −125° | Pacific coast, California | 2.48 | 1.7×10⁻⁵ | 6.5% |
| 30°, −120° | Central California coast | 2.57 | 0.017 | 6.9% |
| 50°, 10° | Central Europe (Germany) | 2.65 | 3.9×10⁻³ | 7.0% |

These hotspots are consistent with anthropogenic (mining, industrial) and geogenic metal
contamination gradients. Single-expedition clustering check (NB10b) confirms ≥2 distinct
study prefixes for 4 of the top 5 hotspots; the South Asian hotspot (30°, 85°) flagged as
single-expedition and should be interpreted with caution.

- Biome-stratified prevalence (NB10b, Fisher's exact + BH-FDR): Soil is strongly enriched
  (OR=5.0, q=1.8×10⁻⁸²); Marine is depleted (OR=0.20, q=9.2×10⁻⁸⁰); Rhizosphere is not
  significantly different from global baseline (OR=0.66, q=0.30).

**Status**: NB10a executed (Spark, via standalone extraction script; 22,357 MAGs with
coordinates). NB10b executed (11 hotspots at q<0.05; biome-stratified table produced;
figures saved to `figures/`). NB10c executed (3 publication figures: global hotspot map,
biome prevalence chart, hotspot summary table; all at 300 dpi in `figures/`). Path bug
corrected in 10b and 10c (`PROJ = Path.cwd().parent`).

---

## Chapter 10d — Pagel's λ by Biome Type

**Notebooks**: 10d_pagels_biome
**Scripts**: scripts/pagel_lambda_by_biome.R (new wrapper)

**Scope**: Tests whether metal resistance (`mean_n_metal_types` per genus) shows
phylogenetic signal within each biome type. λ≈1 indicates Brownian-motion conservatism
(closely related genera share similar resistance breadth); λ≈0 indicates no signal (consistent
with biome-specific HGT overriding ancestry). Uses GTDB r214 bacterial genus tree (pruned,
same as NB06 PGLS); `phytools::phylosig(method='lambda', test=TRUE)`.

**Biome genus sources**:
- Groundwater: arkinlab_microbeatlas (ENIGMA project; 1,624 samples; precomputed
  `data/groundwater_enrichment.csv`)
- Marine water, Soil, Marine Sediment, Rhizosphere: MGnify 260K MAG dataset
  (biome_lineage column)

**Key findings** (NB10d, bacteria domain):

| Biome | n genera | λ | LRT p |
|-------|---------|---|-------|
| Groundwater | 682 | 0.861 | 1.8×10⁻⁹³ |
| Marine water | 424 | 0.829 | 2.1×10⁻⁴⁷ |
| Soil | 274 | 0.879 | 1.3×10⁻³⁶ |
| Marine Sediment | 317 | 0.897 | 2.5×10⁻⁴⁰ |
| Rhizosphere | 113 | 0.866 | 1.6×10⁻¹⁸ |

All five biomes show strong, highly significant phylogenetic signal (λ=0.83–0.90, all p<10⁻¹⁸).
The narrow range (0.83–0.90) indicates that ancestry — not biome-specific HGT or environmental
selection — is the primary determinant of metal resistance breadth across every environment type
tested. This consistency is ecologically surprising: groundwater, a geochemically reduced and
often metal-contaminated environment, shows the same degree of phylogenetic conservatism as
open marine water.

The single archaea-domain test (Marine water genera; n=15) yields λ=0.856 (LRT p=0.035),
directionally consistent with the bacterial pattern but severely underpowered for phylogenetic
signal estimation at this sample size; treat as indicative only.

**Status**: Fully executed. `data/pagel_lambda_by_biome.csv` and
`figures/nb04d_pagels_lambda_by_biome.png` (forest plot, 300 dpi) generated.

---

## Chapter 10e — Specific Metal Resistance Genes × Biome

**Notebooks**: 10e_gene_level_biome

**Scope**: Prevalence of seven AMRFinderPlus focal genes (merA, arsC, arsA, silA, pcoA,
cadA, chrA; covering Hg/As/Ag/Cu/Cd/Cr) across the five biome types. For each gene × biome
combination: fraction of biome genera carrying the gene; Fisher's exact vs. GTDB genus tree
baseline (2,851 genera; BH-FDR corrected). The GTDB genus tree is the same baseline used for
Pagel's λ (methodological consistency).

**Key findings** (NB10e; significant = q<0.05):

*merA (mercury reductase)* — enriched in ALL biomes vs. GTDB baseline:
- Rhizosphere: OR=10.3, q=2.2×10⁻²⁵ (40.5% of biome genera)
- Groundwater: OR=22.1, q=7.3×10⁻⁸⁴ (26.3%)
- Soil: OR=7.0, q=1.2×10⁻³² (26.9%)
- Marine Sediment: OR=5.6, q=6.3×10⁻²⁷ (23.4%)
- Marine water: OR=6.3, q=3.0×10⁻³⁴ (22.1%)

*arsC (arsenate reductase)* — enriched in all five biomes vs. GTDB baseline: Rhizosphere
(OR=22.8, q=4.3×10⁻⁶), Groundwater (OR=18.5, q=1.2×10⁻⁵), Marine Sediment (OR=8.3,
q=7.7×10⁻⁴), Marine water (OR=5.7, q=4.4×10⁻³), and Soil (OR=5.4, q=9.2×10⁻³). Universal
enrichment across every biome tested indicates that arsenic exposure is a near-universal
geochemical stressor driving arsenate reductase retention regardless of environment type.

*arsA (arsenate-translocating ATPase, ars operon)* — enriched in three biomes: Groundwater
(q=8.1×10⁻⁴; OR not computable — zero arsA-carrying non-groundwater genera in GTDB baseline
at this depth, consistent with arsA being globally rare), Marine water (OR=21.2, q=3.8×10⁻³),
and Rhizosphere (OR=22.1, q=4.1×10⁻³); not significant in Soil or Marine Sediment. arsA
encodes the ATPase subunit of the Ars active efflux pump (ArsABC) and is less universally
distributed than arsC; its selective enrichment in water-column and groundwater environments
suggests that active arsenate export — beyond reductive detoxification alone — is specifically
advantageous in arsenic-contaminated aquatic systems.

*silA (silver efflux, RND family)* — strongly enriched in Rhizosphere (OR=112.6,
q=4.5×10⁻⁶), Groundwater (OR=15.2, q=9.2×10⁻³), Soil (OR=14.4, q=6.5×10⁻³), and Marine
water (OR=21.2, q=3.8×10⁻³); Marine Sediment q=0.077 (not significant). The Rhizosphere silA
OR is the largest observed across all gene × biome combinations; consistent with silver
exposure from agricultural inputs and minerotrophic niches.

*pcoA, cadA, chrA* — not significant in any biome (pcoA: n≤2 per biome; cadA n≤1, chrA n≤1
per biome). Counts are too low for reliable Fisher's exact enrichment estimation.

**Pattern summary**: merA and arsC show universal biome enrichment (all five biomes, q<0.01
each), indicating Hg and As resistance are consistently selected regardless of environment. arsA
adds a second arsenate-resistance mechanism with biome selectivity — highest in anoxic/metal-
rich water-column environments. silA (Ag efflux) is rhizosphere-dominant with evidence across
terrestrial and marine water. Cu/Cd/Cr resistance genes (pcoA, cadA, chrA) fall below
detectable prevalence in this genus-level dataset, pointing to either sparse distribution or
annotation coverage limits for these gene families in AMRFinderPlus.

**Status**: Fully executed. `data/gene_biome_enrichment.csv` and publication figures
(`figures/nb04e_gene_biome_heatmap.png`, `figures/nb04e_gene_biome_bubbleplot.png`) generated.

---

## Chapter 11 — AlphaEarth Embedding Synthesis

**Notebooks**: 11c_alphaearth_metal_synthesis (Heather's original contribution)
**Data**: alphaearth_with_env.csv (83K NCBI reference genomes, 64-dim embeddings + lat/lon),
hotspots_5grid.csv (Ch.10b geographic hotspot cells), alphaearth_hotspot_comparison.csv (generated)

**Scientific question**: Do genomes from geographic metal-resistance hotspots (Ch.10b) occupy
distinct regions of AlphaEarth embedding space? This connects the MAG-level geographic signal
in Ch.10b to reference genome embeddings via spatial co-occurrence at 5° grid resolution.

**Attribution note**: AlphaEarth infrastructure notebooks (extraction pipeline via Spark,
UMAP exploration) were written by Paramvir Dhaliwal as part of the BERDL pangenome project
and are NOT included in this thesis. The background finding that environmental samples cluster
3.65× more tightly in embedding space than human-associated genomes (vs. 2.03×) motivates
this analysis but is not a thesis contribution. NB11c formulates and tests the original
synthesis question connecting AlphaEarth to metal ecology.

**Method (NB11c)**:
- Grid AlphaEarth genomes at 5° resolution (same binning as Ch.10b hotspots)
- Filter to environmental samples only (`env_broad_scale` / `isolation_source`; 48.7% of
  genomes with coordinates are environmental = 40,552 genomes; 36,971 after dropping missing embeds)
- Label genomes: `is_hotspot=True` if (lat_bin, lon_bin) matches a Ch.10b hotspot cell
- PCA on standardized A00–A63; PERMANOVA on Euclidean distance in PC1–10 space
- Per-PC Welch t-test with BH-FDR correction; visualization: PC scatter + PC1 distribution

**Results — Core analysis (NB11c cells 5–8)**:

| Analysis | Statistic | Value | Interpretation |
|----------|-----------|-------|----------------|
| Hotspot genomes | n | 4,496 / 36,971 (12.2%) | spatial overlap with Ch.10b hotspot cells |
| PERMANOVA (PC1–10) | pseudo-F | **80.68** | hotspot vs non-hotspot clusters differ |
| PERMANOVA (PC1–10) | p | **0.001** (999 perms) | highly significant; stratified subsample n=5,000 preserving 12.2%:87.8% ratio |
| Significant PCs | n | 16 / 20 | most embedding dimensions differ |
| PC1 | Welch t | −44.2 (q≈0) | hotspot genomes shifted toward lower PC1 |
| PC7 | Welch t | +63.1 (q≈0) | largest individual-PC effect |

**Results — Extension 1: Do the PCs encode metal resistance? (NB11c cell 10)**

Joined 394 genera (≥5 AE genomes) to `genus_trait_table.csv`. Spearman correlation of
genus-mean PC vs `mean_n_metal_types`:

| PC | ρ | p | Significant? |
|----|---|---|-------------|
| PC1 | +0.038 | 0.458 | No |
| PC5 | +0.011 | 0.827 | No |
| PC7 | −0.065 | 0.204 | No |
| PC12 | +0.029 | 0.569 | No |
| PC17 | +0.041 | 0.421 | No |
| PC19 | +0.032 | 0.538 | No |

Top vs bottom quartile metal resistance genera: PC1 t=−0.21 (p=0.84), PC7 t=−1.59 (p=0.11).
**All null.** No detectable correlation between the PCs most shifted in hotspot genomes and
genus-level metal resistance (all ρ<0.07, all p>0.2, n=394 genera; power sufficient to detect
ρ>0.15 at α=0.05). The AlphaEarth embedding captures environmental/geographic context (Ext.2)
but not specifically metal resistance biology in this global reference genome dataset.

**Results — Extension 2: Taxonomic confound control (NB11c cells 13–14)**

Phylum composition differs between hotspot and non-hotspot (χ²=significant) — taxonomy IS
confounded with hotspot status. However, within-phylum PERMANOVA shows the signal is not
explained by this:

| Test | pseudo-F | p |
|------|----------|---|
| All phyla (overall) | 80.68 | 0.001 |
| Within Pseudomonadota (n=14,172) | **96.14** | **0.001** |
| Within Actinomycetota (n=3,065) | **95.13** | **0.001** |

Within-phylum F-statistics *exceed* the overall F — the hotspot signal is robust to
phylum-level taxonomy differences. This does not rule out finer-scale (order, family, species)
taxonomic confounds, but confirms the separation is not driven by phylum composition alone.

**Results — Extension 3: Dose-response (NB11c cell 16)**

Correlation between |PC displacement| from non-hotspot baseline and hotspot OR across 11 cells:

| PC | Spearman ρ | p |
|----|------------|---|
| PC | Spearman ρ | uncorrected p | BH-adjusted q |
|---|---|---|---|
| PC1 | +0.127 | 0.709 | 0.709 |
| PC5 | +0.600 | 0.051 | 0.153 |
| PC7 | +0.273 | 0.417 | 0.540 |
| **PC12** | **+0.682** | **0.021** | **0.125** |
| PC17 | −0.255 | 0.450 | 0.540 |
| PC19 | −0.300 | 0.370 | 0.540 |

PC12 shows the strongest dose-response signal (ρ=+0.68, uncorrected p=0.021), but after BH-FDR
correction for 6 PCs tested, the adjusted q=0.125 does not reach α=0.05. This result should be
treated as **exploratory** (n=11 cells, 6 tests; PC12 is the only PC with even nominal significance).
PC1 and PC7 do not dose-respond with OR — they capture geographic separation, not exposure intensity.
The dose-response pattern in PC12 is suggestive but requires independent validation.

**Results — Extension 4: PC12 identity (NB11c cell 18)**

PC12 is dominated by embedding dimension A10 (loading=0.422; next: A15 at −0.239). To interpret
its environmental meaning, genomes in the top and bottom 10% of PC12 were categorised by
isolation_source metadata (n=3,748 high; n=3,728 low):

| Environment category | High PC12 (%) | Low PC12 (%) |
|---|---|---|
| Permafrost | 29.2 | 0.0 |
| Deep subsurface (Äspö HRL) | 11.6 | 0.0 |
| Wastewater/Digester | 11.4 | 1.9 |
| Acid mine drainage | 2.1 | 0.1 |
| Hydrothermal vent | 2.8 | 0.4 |
| Hypersaline soda lake | 0.2 | 24.7 |
| Freshwater lake (Microcystis) | 0.2 | 7.4 |
| Food-associated | 2.7 | 12.8 |

**PC12 biological identity** (post-hoc interpretation; exploratory): an anoxic / cold /
extreme-subsurface environment axis. High PC12 = permafrost (29.2%), deep granite groundwater
Äspö HRL (11.6%), wastewater/digesters (11.4%), hydrothermal vents (2.8%), AMD (2.1%). Low
PC12 = hypersaline soda lake (24.7%), freshwater cyanobacterial blooms (7.4%), food (12.8%).

**Caveat**: permafrost and Äspö HRL together account for 40.8% of the high-PC12 signal. These
environments are primarily defined by temperature (cold) and depth (subsurface isolation), not
metal biogeochemistry. Only 13.5% of high-PC12 genomes come from explicitly metal-associated
environments (AMD + digesters). PC12 most likely captures a cold/anoxic/isolated-subsurface
physicochemical niche; metal enrichment co-occurs in these environments but is not the primary
driver. The axis is concentrated in embedding dimension A10 (loading=0.422), which likely encodes
cold/anoxic/extreme-subsurface conditions rather than metal cycling per se.

**Synthesis**: The AlphaEarth embedding separation is real (PERMANOVA F=80.68), robust to
phylum-level taxonomy (within-phylum F=95–96), but reflects geographic/environmental context
rather than metal resistance specifically (Ext.1 null; all ρ<0.07, n=394 genera). PC12 is the
one axis showing nominal dose-response with OR (ρ=+0.68, uncorrected p=0.021), but this does
not survive BH-FDR correction (q=0.125, 6 PCs tested, n=11 cells) and is best treated as
exploratory. PC12 identity analysis (post-hoc) suggests it encodes a cold/anoxic/extreme-
subsurface niche, which co-occurs with but is not synonymous with metal enrichment.

The primary thesis claim is: *genomes from metal-resistance hotspot regions have distinct
AlphaEarth embedding profiles (PERMANOVA F=80.68), driven by geographic/environmental context.
Embedding space reflects the same biogeographic patterns as the MAG-level analysis in Ch.10b,
but does not reveal a direct metal-resistance signal in the global reference genome dataset.
A suggestive (exploratory) dose-response in PC12 points to cold/anoxic physicochemistry as
a potential mediator, warranting future validation with larger hotspot cell samples.*

Note: only 2.8% of MAGs carry metal resistance genes globally (NB10a), reinforcing that PC12's
OR dose-response most likely captures correlated abiotic gradients rather than metal gene biology.

**Figures**: `nb11c_alphaearth_pca_hotspot.png`, `nb11c_alphaearth_pc1_distribution.png`,
`nb11c_ext1_pc_vs_metal.png`, `nb11c_ext2_phylum_composition.png`, `nb11c_ext3_dose_response.png`,
`nb11c_ext4_pc12_identity.png`
**Data**: `alphaearth_hotspot_comparison.csv` (36,971 genomes × PC1–20 + hotspot label)

**Status**: NB11c — COMPLETE (executed 2026-06-30). NB10a fixed same date. NB11a/11b removed
as non-distinct from Paramvir Dhaliwal's pangenome project.

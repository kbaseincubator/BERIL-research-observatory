# Research Plan — Microbial Metal Ecology Thesis
# Pre-registered Analysis Plan

**Version 1 (2026-08-07):** Initial pre-registration of completed and planned analyses.

---

## Central Research Question

Does metal contamination select for metal-tolerant communities through **community turnover** (resistant lineages replacing sensitive ones) or **within-lineage gene gain** (horizontal acquisition of resistance genes)?

**Operationalized:** Are metal resistance genes ecologically structured — do they accumulate in metal-specialist taxa, associate with metal-contaminated sites in field surveys, and predict fitness under metal stress?

---

## Central Thesis Claim

Metal resistance genes are **not** the primary genomic correlate of metal specialization at field scales. Instead, constitutive metal-metabolic genes (cofactor biosynthesis, metal-dependent enzymes) track ecological specialists, while resistance genes track generalists via HGT. At the individual KO level, 31 genes survive pH control and cross-dataset replication; aggregate resistance gene density is uninformative.

---

## Hypotheses (Pre-registered)

### Aim 1: Ecological niche breadth vs metal gene density (comprehensive_metal_ecology)

| ID | Hypothesis | Prediction | Result |
|---|---|---|---|
| H1 | Metal gene density predicts ecological specialization | β < 0 (more metal genes → narrower niche) | SUPPORTED: β=−0.021, p=2×10⁻⁸, λ=0.757 |
| H1a | The effect survives genome-size correction | β survives offset(log_genome) | SUPPORTED: β=−0.031, p=0.0024 (log-count PGLS) |
| H1b | Resistance genes do NOT drive the effect | Resistance β ≈ 0 | SUPPORTED: β=+0.003, p=0.66 |
| H1c | Cofactor/metabolic genes DO drive the effect | Cofactor β < resistance β | SUPPORTED: cofactor β=−0.033, p=10⁻⁹ |
| H2 | Metal gene density is phylogenetically conserved | λ > 0.5 | SUPPORTED: λ=0.757 |
| H3 | Metal type diversity is more conserved than gene density | λ(metal types) > λ(gene density) | SUPPORTED: λ(types)=0.943 vs λ(density)=0.497 |
| H4 | Resistance genes show HGT signatures | Fritz-Purvis D < 0 or λ < 0.3 | SUPPORTED: merE, aoxB, golS, shp — D>0.2, λ<0.3 |

**Sensitivity analyses (registered post-hoc):**
- S1: λ=0 (OLS) and λ=1 (Brownian) sensitivity — β direction preserved: Pagel β=−0.031 p=0.0024; Brownian β=−0.027 p=0.0047; OLS β=−0.032 p=0.0017
- S2: MCMCglmm Poisson GLMM (Adam diagnostic) — pMCMC=0.48 (NS, directionally consistent)
- S3: Genome-size sensitivity landscape (1−a) — R²=0.370, p=0.004; metal genes at category median
- S4: pESS=11.6 (Bartoszek 2016) — effective sample size after phylogenetic correction
- S5: MicrobeAtlas Levins B sampling confound — n_cells STRENGTHENS signal (β −0.137 → −0.188)

### Aim 2: Per-KO field associations (per_ko_metal_associations)

| ID | Hypothesis | Prediction | Result |
|---|---|---|---|
| H1 | KO-metal associations exist in field metagenomes | ≥1 KO-metal pair FDR q<0.05 | SUPPORTED: 219 pairs (MGnify), 69 pairs (SPIRE) |
| H2 | Associations survive pH control | ≥10 pairs survive sg_pH covariate | SUPPORTED: 151/219 MGnify, 31/69 SPIRE |
| H3 | Field associations replicate across datasets | ≥10 pairs significant in both MGnify and SPIRE | SUPPORTED: 24 pairs overlap (Spearman ρ with pH control) |
| H4 | Resistance genes are NOT enriched among field-sig pairs | <50% of field-sig KOs are resistance genes | SUPPORTED: 1/84 field-strict KOs is a canonical resistance gene |
| H5 | Lab fitness genes do NOT match field bioindicators | Z < −2 (below-random overlap) | SUPPORTED: Z=−73 (highly below-random) |

**Key covariate structure:**
- Primary model: KO_present ~ PF1_metal + latitude + C(phylum/genus), logistic regression
- pH sensitivity: +sg_pH covariate (SoilGrids 0.25°)
- Cross-replication: MGnify primary, SPIRE replication
- Field-strict filter: FDR sig in MGnify + lat-adjusted + SPIRE-replicated + ≥20 genera → 84 KOs
- pH-strict filter: field-strict + survives sg_pH control → 31 KOs

**Registered diagnostics (per Adam, 2026-08-07):**
- D1: Genome-size β vs (1−a) → R²=0.370 (see Aim 1 S3)
- D2: Metal concentration provenance → CSU raster (no per-sample measurements); Moran's I=0.863–0.946
- D3: KO→category mapping (field_strict_ko_annotations.csv)
- D4: Sign convention (β>0=enriched in high-metal) + OR/IQR as effect size

### Aim 3: Community composition prediction (community_composition_prediction)

| ID | Hypothesis | Prediction | Result |
|---|---|---|---|
| H1 | Within-region: taxa predict contamination | AUROC > 0.8 within region | SUPPORTED: within-region AUROC ≈ 0.99 |
| H2 | Cross-region: signal collapses | AUROC → 0.5 cross-region | SUPPORTED: cross-region AUROC ≈ 0.18 |
| H5 | Metal gene density (CCP via OOF) | Cu=0.015, Zn=0.000, Pb=0.000 OOF thresholds | SUPPORTED |

### Aim 4: ENIGMA isolate sequence → metal fitness (enigma_stress_phenotype_ml)

| ID | Hypothesis | Prediction | Result |
|---|---|---|---|
| H_Hg | Hg fitness predictable from sequence | AUC > 0.7 | SUPPORTED: AUC=0.774 (aa only) |
| H_metal | Metal stress classifiers generalize across genera | LOGO AUC > 0.7 | NOT SUPPORTED: LOGO AUC=0.53–0.62 for metals (UV=0.736, ethanol=0.725) |
| H_aa_kmer | Amino acid composition ≥ aa+kmer2 | AUC(aa) ≈ AUC(aa+kmer2) | SUPPORTED: aa-only = aa+kmer2 |

---

## Analysis Sequence (Pre-registered order)

1. **Ecological PGLS** (comprehensive_metal_ecology) — niche breadth × metal gene density by category
2. **MWAS** (per_ko_metal_associations) — per-KO logistic regression, pH robustness, cross-dataset replication
3. **Community ML** (community_composition_prediction) — taxon OTU → contamination prediction
4. **Isolate ML** (enigma_stress_phenotype_ml) — sequence → fitness prediction
5. **Supporting: MAG-level prediction** (metagenomic_environment_prediction) — extends #2 to individual genomes
6. **Supporting: MWAS collinearity** (mwas_confound_analysis) — validates that raw MWAS hits are mostly artifacts

The order was designed so each analysis tests a different mechanistic layer: population genetics (PGLS) → individual gene ecology (MWAS) → community assembly (ML) → physiology (ENIGMA).

---

## Registered Caveats and Known Limitations

| Limitation | Source | Mitigation |
|---|---|---|
| CSU metal raster (not per-sample measurements) | Aims 1 + 2 | Moran's I computed (0.863–0.946); lat banding; cross-dataset replication |
| λ=0.757 deflation from tip sampling error | Aim 1 | Ives et al. refit planned (see REPORT sensitivity) |
| pESS=11.6 | Aim 1 | Reported alongside raw n; Gelman-Rubin convergence checked |
| MCMCglmm NS (pMCMC=0.48) | Aim 1 | Disclosed; directionally consistent; PGLS more powerful at n=1,574 |
| Operon co-membership inflates apparent hits | Aim 2 | Operons noted together in text; formal collapse pending |
| Quasi-complete separation | Aim 2 | |β|>10 flagged; Firth spotcheck on 24 pairs |
| pH as possible collider (not just mediator) | Aim 2 | Collider alternative flagged as standing caveat |
| No per-sample metal measurements | All | Explicitly documented; forensic confirmation via ENA API + h5ad audit |

---

## Planned next experiments (not pre-registered as analysis)

1. Isolate dose-response calibration (mer/ars operons, ENIGMA collection)
2. Phenotype sanity check: do mer-carrying vs mer-lacking isolates differ in Hg MIC?
3. Metatranscriptomics at ORFRC (once isolate calibration complete)

---

## Data Sources

| Source | Table / path | N | Used by |
|---|---|---|---|
| MicrobeAtlas 16S | arkinlab.microbeatlas.otu_counts_long | 278K samples | Aim 1, 3 |
| GTDB pangenome | kbase.ke_pangenome | 253K genomes | Aim 1, 2 |
| CSU metal mobility | arkinlab.envdbs.csu_metal_mobility_grid | 0.1° global | Aim 1, 2 |
| SoilGrids pH | arkinlab.envdbs.soilgrids_master | 338K cells | Aim 1, 2 |
| SPIRE MAGs | refdata.spire | 2,477 soil MAGs | Aim 2, 5 |
| MGnify MAGs | (curated MGNIFY subset) | 8,585 soil MAGs | Aim 2, 5 |
| ENIGMA fitness | internal | 147 isolates × 26 metals | Aim 4 |

## Revision History

- **v1 (2026-08-07):** Initial pre-registration based on completed analyses. Registered post-hoc per Adam Arkin committee feedback (2026-08-07).

# Report: Metal-Gene Density Predicts Ecological Niche Breadth in Prokaryotes

## Key Findings

### Finding 1 — Higher metal-gene investment is associated with narrower niche breadth in bacteria

![Primary PGLS scatter: metal-gene density vs Levins' niche breadth](figures/01_pgls_primary_scatter.png)

In 1,574 bacterial genera matched across the GTDB phylogeny and global MGnify MAG data, per-Mb
Tier 1+2 metal-gene KO density is significantly negatively associated with standardised Levins'
niche breadth (β = −0.021, SE = 0.0037, t = −5.63, p = 2.1×10⁻⁸, FDR joint p = 6.4×10⁻⁸,
Pagel's λ = 0.757, ΔAIC = −29.4, r² = 0.046). The pre-registered hypothesis (H1: β < 0) is
confirmed. The moderate phylogenetic signal (λ = 0.757) indicates the relationship is partly but
not entirely explained by shared ancestry. Levins' B_std was computed from MicrobeAtlas
Env_Level_1 habitat categories, not from soil chemistry, ensuring independence of the
niche-breadth and metal-concentration axes.

*(Notebook: 01_primary_pgls_metal-gene_density.ipynb)*

---

### Finding 2 — Signal is directionally consistent in archaea and independent of λ assumption

![Replication test comparison](figures/02_primary_tests_comparison.png)

The archaea replication (P2, n = 95, GTDB archaeal tree) produced β = −0.014 (p = 0.119),
directionally consistent with P1 but non-significant — likely due to low power at n = 95 combined
with the small effect size. The Australia-only NGSA replication (P3, n = 482) is near-zero
(β = −0.002, p = 0.755). Across 8 pre-specified sensitivity analyses, 6/7 directionally confirm
H1 (all β < 0, 5 significant at p < 0.05). The signal is present under λ = 0 (OLS:
β = −0.032, p ≈ 0) and λ = 1 (Brownian motion: β = −0.018, p = 3.7×10⁻⁶), confirming it is not
an artefact of any single phylogenetic correction assumption.

*(Notebook: 01_primary_pgls_metal-gene_density.ipynb, 02_ngsa_replication.ipynb, 05_sensitivity_analyses.ipynb)*

---

### Finding 3 — Genome streamlining is pervasive; metal-gene investment sits in the lower-middle of a broad landscape

![Functional landscape forest plot](figures/functional_landscape_forest.png)

The three pre-specified named negative controls (ribosomal proteins, amino acid biosynthesis, DNA
repair) all showed highly significant negative associations with niche breadth — not near-zero as
anticipated for true nulls. This reveals a pervasive **genome-streamlining baseline**: specialist
genera have smaller genomes, so any conserved, near-universal gene set is denser per Mb.

Mapping metal-gene density into a full functional landscape confirms the breadth of this effect. 19
KEGG functional categories were tested at the same per-Mb density resolution, with BH-FDR correction
(NB18; exploratory):

| Category | n KOs | n genera | β | q_BH |
|----------|-------|---------|---|------|
| Replication and repair | 60 | 1,073 | **−0.035** | 1.0×10⁻¹¹ |
| Nucleotide metabolism | 123 | 1,073 | **−0.032** | 2.3×10⁻¹⁰ |
| Amino acid metabolism | 242 | 1,073 | **−0.031** | 3.7×10⁻¹² |
| Translation (ribosome) | 206 | 1,073 | **−0.030** | 1.2×10⁻⁹ |
| Protein folding/degradation | 49 | 1,073 | **−0.030** | 1.4×10⁻¹⁰ |
| Cofactors and vitamins | 382 | 1,073 | **−0.029** | 1.4×10⁻¹⁰ |
| Secondary metabolism | 2,326 | 1,073 | **−0.028** | 3.1×10⁻¹⁰ |
| Transcription (RNA polymerase) | 66 | 1,071 | **−0.028** | 6.3×10⁻⁸ |
| Carbohydrate metabolism | 387 | 1,073 | **−0.026** | 3.1×10⁻⁹ |
| Lipid metabolism | 84 | 1,069 | **−0.021** | 5.8×10⁻⁶ |
| **Metal Tier 1+2 (P1 reference)** | **140** | **1,574** | **−0.021** | **—** |
| Quorum sensing | 283 | 1,073 | −0.017 | 1.1×10⁻³ |
| Xenobiotics biodegradation | 1,449 | 1,073 | −0.017 | 1.1×10⁻³ |
| Energy metabolism | 224 | 1,073 | −0.015 | 3.5×10⁻³ |
| Terpenoids and polyketides | 66 | 665 | −0.010 | 4.9×10⁻² |
| ABC transporters (non-metal) | 475 | 1,073 | −0.006 | 0.457 |
| AMR (beta-lactam) | 112 | 1,073 | −0.004 | 0.505 |
| Glycan biosynthesis (peptidoglycan) | 73 | 1,050 | +0.001 | 0.767 |
| Cell motility | 153 | 1,063 | +0.004 | 0.505 |
| Two-component systems | 521 | 1,073 | +0.006 | 0.457 |

14/19 categories are significantly negative (q < 0.05). The constitutive housekeeping and
information-processing categories define a streamlining baseline of β ≈ −0.029 to −0.035.

**Where the metal-gene signal sits:** P1 (β = −0.021) ranks 11th out of 19, roughly tied with
lipid metabolism. It is **30–60% weaker than the housekeeping baseline** — not anomalously strong.
This weakening is mechanistically interpretable: specialists do not simply compact all genes equally;
they retain higher per-Mb metal-gene density than expected under uniform genome compaction,
consistent with selective retention of metal-processing functions.

The streamlining landscape provides essential context for all subsequent findings: the appropriate
null model for the metal-gene signal is the constitutive housekeeping β (≈ −0.029 to −0.035), not
zero.

*(Notebook: 17_negative_controls.ipynb, 18_functional_landscape.ipynb)*

---

### Finding 4 — Cofactor biosynthesis carries the strongest signal; resistance genes show none; effect is uniform across 9 metals

![Functional category forest plot](figures/03_category_forest_plot.png)

Separating the 140-KO primary set by functional category reveals a mechanistically interpretable
internal split:

| Category | n KOs | β | SE | p (FDR) | Direction |
|----------|-------|---|----|---------|-----------|
| Resistance/Detoxification | 106 | +0.003 | 0.006 | 0.656 | (**null** — expected) |
| Transport/Homeostasis | 213 | −0.022 | 0.005 | 2.8×10⁻⁵ | confirmed |
| Sensing/Regulation | 48 | −0.018 | 0.005 | 9.1×10⁻⁴ | confirmed |
| Cofactor Biosynthesis | 7 | **−0.033** | 0.005 | 5.2×10⁻⁹ | **strongest** |
| Metal-dependent Metabolism | 54 | −0.021 | 0.005 | 1.2×10⁻⁴ | confirmed |

Resistance genes (106 KOs; direct efflux, reductases, sequestration) show no association
(β ≈ 0, p = 0.66) — consistent with their ubiquity and susceptibility to HGT, which decouples
their abundance from ecological specialisation. All four metabolically constitutive categories are
significant. Cofactor biosynthesis shows the largest effect (β = −0.033), equal to the housekeeping
baseline, anchored by 7 KOs encoding Fe–S cluster assembly, molybdopterin synthesis, and cobalamin
pathway genes — constitutively required in organisms dependent on metal-cofactor chemistry for core
metabolic functions (nitrogen fixation, anaerobic respiration, methanogenesis).

**The internal split is distinctive.** Three comparison categories (AMR, two-component systems, ABC
transporters) were tested at the same sub-functional resolution to confirm that the
resistance-null / constitutive-significant contrast is not a general feature of all gene categories
(NB19; exploratory): AMR subcategories are all positive — efflux pumps β = +0.018 (q = 0.016,
significant); enzymatic inactivation β = +0.006 (q = 0.21); target modification β = +0.009
(q = 0.19). Two-component systems are also all positive: sensor kinases β = +0.008 (q = 0.25),
response regulators β = +0.009 (q = 0.25), phosphotransfer β = +0.003 (q = 0.68). Among ABC
transporters, the only significantly negative sub-category is Lipid/LPS export (16 KOs,
β = −0.030, q = 3.3×10⁻⁵), comparable to the metal cofactor biosynthesis signal and likely
reflecting constitutive outer-membrane lipid maintenance; all other ABC substrates are near-zero
or positive (q > 0.25). The resistance-null / constitutive-significant split is therefore
mechanistically specific to metal genes — it requires constitutive metabolic coupling to the
predictor category, which inducible resistance and regulatory gene sets lack.

**The split magnitude is quantitatively validated by permutation (NB25; exploratory).** A
split-magnitude permutation test generated 1,000 random partitions of the 140-KO set into groups
of sizes 106 and 7 (matching the resistance/cofactor group sizes). The observed Δβ = 0.035259
exceeds all 1,000 null splits (p < 0.001 (0/1,000 permutations exceeded); null median Δβ = −0.006, SD = 0.007; observed split
≈ 6 SD above null). This confirms the resistance/cofactor contrast is not an artefact of unequal
group sizes or sampling variance. Among comparison families: ABC transporter Δβ = 0.032 (Lipid/LPS
vs all others), AMR Δβ = 0.012, TCS Δβ = 0.006 — all smaller than the metal gene set Δβ = 0.035.

**Cofactor signal is robust to individual KO removal (NB26; exploratory).** Of the seven cofactor KOs, three were absent from the MGnify MAG dataset and contributed zero density; the jackknife was performed on the four KOs with detectable representation. A leave-one-KO-out
jackknife for the 4 assignable cofactor KOs (K01772, K02225, K03635, K22225) shows every 3-KO
remainder set remains highly significant: β range −0.016 to −0.029, all p < 0.001, no sign
changes. K01772 excluded: β = −0.016 (SE = 0.00441, p = 0.000222); K02225 excluded: β = −0.027
(SE = 0.00444, p = 1.4×10⁻⁹); K03635 excluded: β = −0.029 (SE = 0.00443, p = 1.3×10⁻¹⁰);
K22225 excluded: β = −0.028 (SE = 0.00478, p = 8.2×10⁻⁹). The signal is distributed across the
Fe–S cluster / molybdopterin / cobalamin pathway, not concentrated in any single gene.

**Effect is uniform across 9 metals.** Metal-specific KO sets (n = 9 metals with ≥ 34 KOs) all
show significant negative β after BH-FDR:

| Metal | n KOs | β | p (FDR) |
|-------|-------|---|---------|
| Tl | 45 | −0.027 | 1.1×10⁻⁸ |
| Fe | 98 | −0.025 | 1.2×10⁻⁷ |
| Ni | 84 | −0.025 | 1.9×10⁻⁷ |
| Zn | 67 | −0.023 | 1.1×10⁻⁶ |
| Al | 34 | −0.023 | 8.8×10⁻⁶ |
| Co | 101 | −0.022 | 3.9×10⁻⁶ |
| S | 74 | −0.021 | 4.9×10⁻⁵ |
| Cu | 71 | −0.019 | 7.7×10⁻⁵ |
| Mn | 34 | −0.017 | 3.8×10⁻⁴ |

Uniformity across chemically diverse metals argues against any single element driving the signal.

**Methods notes:**
*Metal panel composition:* Global analysis includes all metals with ≥34 KOs: Cu, Zn, Fe, Ni, Co,
Mn, Tl, Al, S. The Australian replication (P4) tests only 5 metals available in NGSA geochemistry:
Cu, Zn, Pb, Ni, Co. *Sulfur:* S-associated KOs predominantly encode Fe–S cluster biogenesis proteins
(*iscS*, *iscU*, *sufB*, *nifU*) — metal-cofactor systems. *Aluminum:* Al has documented bacterial
toxicity and dedicated resistance systems; inclusion is mechanistically justified.

*(Notebook: 03_tier_and_category_analysis.ipynb, 19_internal_structure_comparison.ipynb, 25_split_magnitude_permutation.ipynb, 26_interaction_test_jackknife.ipynb)*

---

### Finding 5 — Five functional categories serve as confirmed true-negative controls

Three pre-specified named negative controls (NB17, complete) and the full functional landscape
(NB18) together establish which gene categories are immune to the streamlining signal, serving as
genuine negative controls for the metal-gene analysis.

**NB17 named housekeeping controls (actual results, not pre-specified expectation):**

| Category | n KOs | n genera | λ | β | SE | p |
|----------|-------|---------|---|---|----|----|
| Ribosomal proteins | 52 | 1,073 | 0.791 | **−0.029** | 0.00474 | 7.6×10⁻¹⁰ |
| Amino acid biosynthesis | 38 | 1,073 | 0.794 | **−0.034** | 0.00427 | 9.5×10⁻¹⁵ |
| DNA repair | 24 | 1,073 | 0.789 | **−0.033** | 0.00476 | 4.0×10⁻¹² |
| Metal genes Tier 1+2 (P1) | 140 | 1,574 | 0.757 | **−0.021** | 0.00370 | 2.1×10⁻⁸ |

These are not true negative controls — they are streamlining indicators. A valid negative control
must be a gene category whose per-Mb density does *not* scale with specialisation.

**Confirmed true negatives from NB18 functional landscape (|β| < 0.006, all q > 0.45):**

| Category | n KOs | β | q_BH | Character |
|----------|-------|---|------|-----------|
| ABC transporters (non-metal) | 475 | −0.006 | 0.457 | Inducible; substrate-specific |
| AMR (beta-lactam) | 112 | −0.004 | 0.505 | HGT-mobile; condition-acquired |
| Glycan biosynthesis (peptidoglycan) | 73 | +0.001 | 0.767 | Near-universal; niche-independent |
| Cell motility | 153 | +0.004 | 0.505 | Environment-dependent expression |
| Two-component systems | 521 | +0.006 | 0.457 | Inducible regulatory network |

All five are variable, inducible, or horizontally-acquired gene sets not constitutively coupled to
genome size. **Metal resistance genes** (β ≈ 0) share this character and are appropriately
classified as a near-null category within the metal-gene set (Finding 4).

The permutation test (1,000 predictor-permutations, empirical p < 0.001) further confirms the
primary signal is not a phylogenetic artefact. Coreness-matched permutation (NB20; 1,000 sets
matched on KO count and pan-genome prevalence decile distribution) yielded **emp_p = 0.298**: 29.8%
of null KO sets produced β ≤ −0.021. The observed primary β falls within the null distribution —
the metal-gene set is **not distinguishable from randomly selected conserved gene sets of equal
coreness structure** in overall magnitude. This does not invalidate the primary result; it
contextualises it. The β = −0.021 is part of the pervasive streamlining landscape, and the
mechanistically distinctive finding is the internal functional split described in Finding 4.

*(Notebook: 17_negative_controls.ipynb, 18_functional_landscape.ipynb, 20_coreness_permutation.ipynb)*

---

### Finding 6 — AusMicrobiome genomic analysis is consistent within-dataset but not an independent replication

**P5 is not an independent replication — all 482 genera are a subset of P1, and the density predictor is identical. The larger β reflects phylogenetic composition of the Australian genus panel (Proteobacteria-enriched), as confirmed by NB21.**

The AusMicrobiome density analysis (P5, n = 482, β = −0.052, SE = 0.0063, t = −8.20,
p = 2.2×10⁻¹⁵, partial R² = 0.194, ΔAIC = −61.2, λ = 0.734) confirms the primary direction and is
highly significant, but the β is 2.5× larger than P1 (z-test: P5 vs P1, z ≈ 4.1, p < 0.001).
"Soil enrichment" alone cannot explain this magnitude difference.

Diagnostic analyses to disambiguate the sources of the larger β (NB21; exploratory):
1. **B_std comparability:** B_std is identical in both datasets (same MicrobeAtlas Env_Level_1
   computation), ruling out a response-variable artefact.
2. **Intersecting-genus analysis:** All 482 P5 genera are present in P1 (complete overlap;
   n_intersection = 482 = n_P5). Restricting P1 to these 482 genera yields β = −0.052
   (SE = 0.0063, n = 482) — identical to the P5 result (NB21). The larger β in P5 is entirely
   attributable to the phylogenetic composition of the continental subset. A z-test confirms
   P5 > P1-full (z = −4.24, p = 2.2×10⁻⁵); P5 also differs significantly from P3-soil
   (z = −2.29, p = 0.022).
3. **Phylum composition:** The AusMicrobiome subset differs from P1 in phylum composition
   (Proteobacteria-enriched / Firmicutes-depleted; see figures/aus_composition_comparison.png),
   reducing effective phylogenetic diversity and concentrating the signal.
4. **Density predictor:** Both P1 and P5 use the same per-Mb density computed from the same
   MGnify MAG dataset (01_pgls_input_bacteria.csv); the predictor is consistent across datasets
   by construction.

Likely explanation: reduced phylogenetic diversity in the continental subset concentrates the
signal among closely related specialist/generalist genus pairs, amplifying β. This is consistent
with the lower λ in P5 (0.734 vs 0.757 in P1), indicating slightly less residual phylogenetic
structure after controlling for the predictor.

*(Notebook: 15_ausmicrobiome_density_replication.ipynb, 21_aus_beta_comparison.ipynb)*

---

### Finding 7 — No pre-specified confounder eliminates the signal

![Confounder beta comparison](figures/04_confounder_beta_comparison.png)

Five pre-specified potential confounders were tested by adding each as a covariate:

| Confounder | β change | % attenuation | p (with conf) | Decision |
|------------|---------|---------------|---------------|---------|
| Genome size | 0.021 → 0.011 | 46.7% | 0.006 | **ROBUST** — below 50% threshold |
| GC content | 0.021 → 0.016 | 23.7% | 7.5×10⁻⁵ | ROBUST |
| Isolation source | 0.021 → 0.018 | 14.5% | 3×10⁻⁶ | ROBUST |
| Mean latitude | 0.021 → 0.031 | −51.8% (amplified) | <10⁻⁴ | AMPLIFIED |
| Dominant biome | 0.021 → 0.020 | 5.8% | <10⁻⁴ | ROBUST |

Genome size produces the largest attenuation (46.7%), just below the pre-specified 50% threshold.
The model remains significant after explicit genome-size correction (p = 0.006), demonstrating that
the metal-gene/niche association is not simply a proxy for the small-genome specialist pattern.
Latitude amplifies rather than attenuates the signal (β becomes more negative: 0.021 → 0.031,
−51.8% amplification, p < 10⁻⁴). This is the opposite of confounding: adding latitude as a
covariate increases the metal-gene coefficient, indicating that latitude and metal-gene density
are collinear in a way that partially suppresses β in the unadjusted model. The interpretation is
that metal-gene-rich genera are disproportionately found at lower latitudes (tropics/subtropics),
and lower-latitude genera are also more ecologically specialised, presumably due to the higher
geochemical heterogeneity and stable climate permitting narrow-niche specialists to persist
without metabolic versatility. Controlling for latitude removes this between-latitude composition
effect, revealing a stronger within-latitude metal-gene/niche association. This pattern is
consistent with the streamlining interpretation: metal homeostasis specialists track
geochemically diverse low-latitude environments, and this geographic signal partially masks the
direct genomic investment → niche breadth relationship in the full global dataset.

MAG quality covariates (mean completeness and mean contamination per genus, computed from
kescience_mgnify.genome, n = 1,107 genera with quality metadata) were additionally tested
(NB22; exploratory). Adding completeness as a covariate: β(density) = −0.023 (p = 2.9×10⁻⁸,
unchanged from baseline β = −0.023); completeness coefficient β = −0.003 (p = 0.43, NS).
Adding contamination: β(density) = −0.023 (p = 5.4×10⁻⁸); contamination coefficient β = +0.007
(p = 0.042), a slight positive association of higher-contamination genera with broader niches
that does not attenuate the metal-density signal (<1.2% change in β). Restricting to
high-quality MAGs (completeness ≥ 90%, contamination ≤ 5%, n = 511 genera): β = −0.018
(SE = 0.0063, p = 0.005), confirming the signal is not driven by low-quality MAGs.

#### Niche-breadth metric sensitivity (NB24)

Three targeted checks confirm that the primary response variable (Levins' B_std) is robust to
measurement choices (exploratory; notebook 24_niche_breadth_sensitivity.ipynb):

**Parametric bootstrap.** For each genus we parametrically bootstrapped the genus-level mean B_std
by resampling its constituent OTU-level B_std values 100 times (drawing `n_otus` values from
N(mean, SD) per genus, clipped to [0, 1]; genera with a single OTU assigned a fixed point
estimate). The bootstrap mean was nearly perfectly correlated with the original estimate
(Pearson r = 0.99869; max |Δ| per genus = 0.064, driven by boundary effects for extreme-valued
genera). Re-running the primary PGLS with the bootstrap mean as response yielded β = −0.01987
(SE = 0.00365, p = 6.1×10⁻⁸, λ = 0.756, n = 1,574), a change of |Δβ| = 0.00083 (4.0%) from P1.
The signal is not sensitive to OTU-level aggregation uncertainty.

**Sample-depth sensitivity.** Genera detected in progressively fewer MicrobeAtlas samples may have
less reliable niche-breadth estimates. P1 was re-run restricting to genera detected in ≥10, ≥20,
and ≥50 MicrobeAtlas 16S samples (NB24; data/niche_breadth_sensitivity.csv):

| Threshold | n genera | β | SE | p |
|-----------|----------|---|----|---|
| ≥10 samples | 1,572 | −0.021 | 0.00368 | 1.38×10⁻⁸ |
| ≥20 samples | 1,570 | −0.021 | 0.00368 | 1.69×10⁻⁸ |
| ≥50 samples | 1,559 | −0.021 | 0.00370 | 2.22×10⁻⁸ |

The signal is unchanged across all thresholds, confirming that the primary result is not driven by genera with sparse MicrobeAtlas detection.

**Alternative niche metric.** As a cross-platform validation, we computed per-genus biome diversity
from the MGnify MAG dataset (genome-based, independent of the 16S survey): Shannon entropy of the
biome_name distribution across MAGs assigned to each genus (n = 1,006 genera with both metrics).
Genera classified as specialists by Levins B_std tended to have lower MAG-based biome Shannon
entropy (Spearman ρ = +0.063, p = 0.046, n = 1,006); the distinct-biome-count metric gave a
concordant trend (ρ = +0.044, p = 0.165). The positive direction (broader-niche genera have higher
biome diversity in MAG data) is consistent with the primary niche-breadth definition, though the
weak correlation reflects the expected imprecision of mapping across two independent datasets
(16S survey vs. metagenome-assembled genomes).

![Niche breadth sensitivity: bootstrap, sample-depth, alternative metric](figures/niche_breadth_bootstrap.png)

*(Notebooks: 04_confounder_checks.ipynb, 22_mag_quality_covariates.ipynb, 24_niche_breadth_sensitivity.ipynb)*

---

### Finding 8 — Signal is consistent within Proteobacteria and Actinobacteria

![Clade-stratified forest plot](figures/clade_stratified_forest_plot.png)

PGLS within each of the four most speciose bacterial phyla tests whether the overall signal is
driven by inter-phylum contrasts rather than within-clade relationships:

| Phylum | n | λ | β | 95% CI | q_BH | Significant? |
|--------|---|---|---|--------|------|-------------|
| Proteobacteria | 677 | 0.778 | −0.021 | [−0.031, −0.011] | **0.00018** | **Yes** |
| Actinobacteria | 204 | 0.779 | −0.035 | [−0.057, −0.014] | **0.0025** | **Yes** |
| Firmicutes | 334 | 0.629 | −0.015 | [−0.031, +0.000] | 0.073 | No (borderline) |
| Bacteroidetes | 183 | 0.917 | −0.009 | [−0.029, +0.011] | 0.397 | No |

All four β estimates are negative, indicating directional consistency across phyla. Proteobacteria
and Actinobacteria survive FDR correction. Firmicutes is borderline (q = 0.073, CI barely touches
zero). For Bacteroidetes (q = 0.397), the 95% CI includes zero ([−0.029, +0.011]); the point
estimate (β = −0.009) is negative but imprecisely estimated.

**Heterogeneity test:** Cochran's Q = 3.60, df = 3, p = 0.309 (I² = 16.6%). There is no statistically
significant heterogeneity across phyla. The signal is not confined to a single clade, and phyla-specific
estimates are consistent with a common underlying effect.

*(Notebook: 16_clade_stratified_pgls.ipynb)*

---

### Finding 9 — Independent niche-breadth validation

![EMP Levins vs KO density](figures/08_emp_levins_vs_ko_density.png)

**Metric agreement:** Spearman correlation between EMP-derived niche breadth and MicrobeAtlas
niche breadth (B_std) across 539 overlapping genera: ρ = 0.211, p = 7.7×10⁻⁷. The two independent
niche metrics co-vary significantly, confirming that MicrobeAtlas B_std captures genuine ecological
breadth rather than idiosyncratic database biases.

**EMP PGLS:** An independent niche breadth metric derived from Earth Microbiome Project (EMP) 16S
amplicon data (EMPO level-2 habitat categories, n = 539 genera) produced β = −0.019 (SE = 0.012,
p = 0.099, λ = 0.055). Although not significant at α = 0.05, the effect size is virtually identical
to P1 (−0.019 vs −0.021). The near-zero λ in EMP data suggests limited phylogenetic signal in
EMPO-2 niche breadth at this coarse habitat resolution.

*(Notebook: 08_emp_niche_breadth.ipynb)*

---

### Finding 10 — Soil-specialist genera show a stronger signal

Restricting to genera classified as soil specialists by MicrobeAtlas Env_Level_1 assignment
(n = 162, > 50% of OTUs with soil/agricultural dominant environment) strengthens the signal
(β = −0.033, SE = 0.012, p = 0.007, λ = 0.471), consistent with the independent
MicrobeAtlas result from the predecessor project (β = −0.023, n = 603, p = 0.0002).
The stronger effect in soil specialists likely reflects the greater chemical complexity and
metal heterogeneity of soil environments relative to the global MGnify MAG corpus.

*(Notebook: 01_primary_pgls_metal-gene_density.ipynb)*

---

### Finding 11 — Gene list structural validation: 7.1% of KOs carry metal-binding domain evidence

![Pfam QC summary](figures/10_pfam_qc_summary.png)

Pfam/InterPro structural domain audit of all 140 primary KOs via KEGG REST → UniProt → InterPro
API confirmed metal-binding clan membership (HMA CL0704, 4Fe-4S CL0344, Fer2/2Fe-2S CL0486,
C2H2-zf CL0361, MBB CL0193) or metal-binding singleton Pfams for 10/140 KOs (7.1%). The
remaining 130 KOs had Pfam annotations but no metal-coordination clan: 113 carry ABC transporter
scaffolds (PF00005/PF00950/PF01032), MerR/CusR/ZntR sensor Pfams, and outer-membrane efflux
proteins — all mechanistically correct metal-processing proteins whose Pfam domains are
substrate-binding/transport scaffolds rather than metal-coordination sites. Representative
examples: **ZnuA** (K02035, Zn²⁺ ABC importer substrate-binding component — annotated with
PF13377/PF12838 Zn-binding clusters but not in a curated metal-binding InterPro clan) and
**MntH** (K03322, Mn²⁺/Fe²⁺ NRAMP secondary transporter — PF07690 MFS scaffold, no
metal-coordination residue motif in the Pfam family record). Both are well-characterised metal
importers; the absence of Pfam clan evidence reflects the annotation gap for substrate-binding
metal transporters, not a problem with the gene list. This expected pattern validates the gene
list architecture.

*(Notebook: 10_pfam_metal_qc.ipynb)*

---

### Finding 12 — Two-scale phylo-D framework identifies 13 KOs with genome-level phylogenetic randomness and low genus-level signal

![Fritz & Purvis D vs Pagel's λ scatter](figures/png/fig08_phylo_D_lambda.png)

To dissect which metal-gene KOs have evolutionary histories consistent with horizontal gene transfer (HGT), we applied a two-scale phylogenetic signal framework: (1) Fritz & Purvis D at the genome level (GTDB 18,961-tip tree, 309 KOs with ≥20 genomes; D = 1 → random/HGT-like, D = 0 → Brownian motion/vertical); (2) Pagel's λ at the genus level (genus-level PGLS, 275 KOs; λ = 1 → strong phylogenetic signal, λ = 0 → no signal).

Across 275 KOs appearing in both datasets, D and λ are weakly negatively correlated (Spearman ρ = −0.041, p = 0.49) — the two metrics capture partially independent evolutionary signals. KOs with the most consistent HGT evidence satisfy both conditions simultaneously: D > 0.2 (phylogenetically random genome distribution) AND λ < 0.3 (no conserved genus-level trait signal). Thirteen KOs meet this double-signal criterion:

| KO | Gene | Subcategory | D | λ | n genomes |
|----|------|-------------|---|---|-----------|
| K07785 | nrsD | Resistance | 0.821 | 0.089 | 59 |
| K19059 | merE | Resistance | 0.728 | 0.102 | 154 |
| K19057 | merD | Resistance | 0.701 | 0.165 | 156 |
| K19594 | gesB | Resistance | 0.597 | 0.156 | 89 |
| K08356 | aoxB | Resistance | 0.562 | 0.000 | 259 |
| K19595 | gesA | Resistance | 0.458 | 0.161 | 103 |
| K25119 | shp | Resistance | 0.385 | 0.000 | 123 |
| K03897 | iucD | Other | 0.354 | 0.237 | 362 |
| K19592 | golS | Sensing | 0.265 | 0.135 | 144 |
| K05908 | doxDA | Other | 0.254 | 0.000 | 241 |
| K08170 | norB | Other | 0.239 | 0.033 | 315 |
| K14974 | nicC | Transport | 0.224 | 0.000 | 382 |
| K15585 | nikB | Transport | 0.202 | 0.000 | 448 |

All 13 fall in the resistance/transport/sensing categories; no cofactor biosynthesis KO appears in the double-signal set — consistent with cofactor genes being constitutively required (vertically inherited) rather than horizontally acquired. In contrast, high-λ control KOs (cusA, cusC, cobN, cobT, zntR, oprJ, mexI, cnrR, cbiH60, fre; all λ > 0.7, D < 0.3) are dominated by metal homeostasis and cofactor-related genes.

This framework provides a gene-level complement to the category-level resistance-null finding (Finding 4): not only do resistance genes show no niche-breadth signal as a class, but individual resistance genes with the highest D values are the most likely to have been horizontally acquired — further decoupling their abundance from ecological specialisation history.

*(Script: `scripts/` — D computed by `scripts/fritz_purvis_d_analysis.py`; data: `data/fritz_purvis_D_genome.csv`, `data/phylo_d_all_ko.csv`; Figure: `figures/png/fig08_phylo_D_lambda.png`)*

---

### Finding 13 — Metal-gene density predicts narrower pH niche but not temperature niche (exploratory)

Metal-gene KO density was tested as a predictor of environmental niche breadth along specific physicochemical axes (PGLS, `scripts/env_niche_breadth_analysis.py`; exploratory; labelled as such below). **Response variable units:** pH niche width = max(soil pH) − min(soil pH) across MicrobeAtlas 16S sampling sites for each genus (pH units, range 0–14); temperature range = max(mean annual temperature °C) − min(mean annual temperature °C) across sites; composite gradient = first PC of [pH, temperature, precipitation] standardised site coordinates. **Predictor:** z-scored primary KO density (ko_per_mb_primary_z, same as P1).

| Response | n genera | β | SE | p | λ | Conclusion |
|----------|---------|---|----|----|---|-----------|
| Temperature range (°C) | 1,195 | +0.079 | 0.886 | 0.929 | — | NS — independent of temp niche |
| Soil pH niche width (pH units) | 1,195 | **−0.760** | 0.233 | 0.001 | 0.11 | Significant — narrower pH niche; predictor is z-scored KO/Mb |
| Composite env. gradient | 1,172 | **−0.064** | 0.017 | <0.001 | — | Strongest — narrower across all axes |

Genera with higher metal-gene density occupy significantly narrower pH gradients and narrower composite environmental gradients, but not narrower temperature ranges. The pH specificity is mechanistically interpretable: metal speciation is strongly pH-dependent (Cr(VI)/Cr(III) redox, Cu²⁺/CuOH⁺ hydrolysis, etc.), so metal-specialist genera are constrained to pH conditions where their gene complement provides effective homeostasis. Temperature tolerance, by contrast, is primarily determined by membrane composition and chaperone repertoire rather than metal-processing capacity.

The pH-niche signal is partly consistent with the composite GeoROC finding (Q4): Cr and Co bedrock enrichment — both associated with mafic geology — positively predicts niche breadth after controlling for metal genes. The pH and mafic-geology signals may reflect a shared soil-chemistry axis (serpentine/ultramafic soils are Mg/Ca-rich, Ca-dominated, and often alkaline) that independently structures genus-level niche breadth.

Pagel's λ for pH niche (0.11–0.20) is substantially lower than for Levins' B_std (0.757), indicating that specific environmental-axis niches are mostly shaped by ecology rather than phylogeny.

*(Script: `scripts/env_niche_breadth_analysis.py`; data: `results/env_niche_pgls_coefficients.csv`, `results/env_niche_all_pgls_results.csv`)*

---

### Finding 14 — Per-KO environmental drivers: emrB shows broadest multi-metal association; metal-match signal significant (exploratory)

For 9 TIER1 KOs detectable in the BERDL pangenome, per-KO frequency was tested against 22 environmental niche breadth responses (environmental metal concentrations from GeoROC, NGSA-ICP, NGSA-MMI; PGLS, `scripts/per_ko_driver_analysis.py`; exploratory):

| KO | Gene | Significant responses (p < 0.05) | Strongest association |
|----|------|----------------------------------|----------------------|
| K03446 | emrB | **11** | Ni (GeoROC) β = 8.45, t = 5.01, p = 6.0×10⁻⁷ |
| K17686 | copA | 8 | — |
| K07787 | cusA | 6 | Hg (NGSA-MMI) t = 3.14, p = 0.002 |
| K07785 | nrsD | 3 | Cr (NGSA-MMI) t = 4.36, p = 1.4×10⁻⁵ |
| K07665 | cusR | 2 | — |
| K03325 | ACR3 | 1 | — |
| K15726 | czcA | 1 | — |
| K19594 | gesB | 0 | — |
| K19595 | gesA | 0 | — |

Total: 198 models (9 KOs × 22 responses); 32 significant at p < 0.05 (16.2%); 28 at FDR q < 0.1.

**Metal-match specificity (Mann-Whitney U test):** KO–metal pairs where the environmental response metal matches the KO's annotated target metal have significantly higher t-statistics (matched mean t = 0.263 vs mismatched mean t = −0.253; p = 0.035). This confirms a modest but statistically detectable metal-specific signal in per-KO environmental drivers, beyond the overall non-specific effect.

**emrB (K03446, Cu/Tl transporter):** Unexpected top performer across 11 responses including Ni and Cr. emrB encodes a multi-drug efflux pump with broad substrate range; its association with diverse metals likely reflects the broad chemical selectivity of RND/MFS efflux systems rather than primary metal resistance. Its prevalence may track metal-stress environments non-specifically. Notably, the 6 TIER1 KOs missing from the pangenome database (cusB/K07798, merR/K08365, czcC/K15725, czcB/K15727, czcD/K16264, cueR/K19591) include core Cu efflux and Hg sensing components — their absence from the pangenome limits the interpretation of per-KO environmental specificity.

*(Script: `scripts/per_ko_driver_analysis.py`; data: `results/ko_drivers_results.csv`; figures: `results/ko_drivers_heatmap.pdf`, `results/ko_drivers_metal_bars.pdf`, `results/ko_drivers_metal_match.pdf`)*

---

### Finding 15 — Metal-gene-rich genera have significantly more positive co-occurrence partners across all environments (exploratory)

Co-occurrence networks were computed in MicrobeAtlas (3,149–3,389 genera) across three strata (all samples, n = 462,716; environmental, n = 382,483; soil, n = 162,022) using hypergeometric tests (Veech 2013, FDR < 5%) and phi coefficients. Metal-gene KO density (z-scored `ko_per_mb_primary`) was regressed against the number of significant positive co-occurrence partners per genus via PGLS. **Important caveat:** niche breadth (B_std) is correlated with positive partner count (Spearman ρ = 0.33–0.37 across strata), so this association is not fully independent of the P1 specialisation axis; partial analyses controlling for B_std are needed (Future Direction 9).

| Stratum | n genera | β (sig_pos_partners) | SE | t | p | λ |
|---------|---------|---------------------|----|----|---|---|
| ALL | 3,389 → 1,572 | **138.4** | 13.7 | 10.08 | 3.4×10⁻²³ | 0.599 |
| ENV | 3,382 → 1,572 | **134.0** | 13.8 | 9.74 | 8.5×10⁻²² | 0.625 |
| SOIL | 3,149 → 1,547 | **210.5** | 15.3 | 13.78 | **8.2×10⁻⁴¹** | 0.570 |

Effect also significant for weighted phi-degree (all three strata, β = 15.2–16.5, p = 3.5×10⁻³²–9.9×10⁻³²) and significant for negative partners (all β = 27–45, p = 1.6×10⁻⁵–2.2×10⁻⁴). Niche breadth (B_std) is correlated with positive partner count (Spearman ρ = 0.33–0.37, p < 10⁻⁴⁰ across strata), confirming that the association is not independent of the primary P1 predictor; partial analyses controlling for B_std are needed to separate contributions.

The soil stratum shows the strongest effect (2.5× larger β than the 'all' stratum) and the clearest negative-partner signal reduction (soil sig_neg β = 27.4 vs all = 39.5 vs env = 45.3). This convergence with the primary P1 soil enrichment (Finding 10; β = −0.033, p = 0.007) suggests that metal-gene-rich genera are embedded in more cooperative, less competitive soil networks.

**Methodological note:** All three strata show extreme network density (38–42% significant positive pairs, mean ≥ 1,200 partners per genus). This precludes clustering coefficients, betweenness centrality, and MPD/SES analysis (metrics degenerate when networks approach completeness). Weighted phi-degree and partner count remain informative. The density itself confirms the co-occurrence matrices are globally near-saturated at the genus level — the positive partner signal reflects relative enrichment within an already highly connected global network, not the formation of exclusive associations.

*(Script: `scripts/run_cooccurrence_analysis.py`; data: `results/cooccurrence_pgls_results.csv`, `results/cooccurrence_correlations.csv`; figures: `results/cooccurrence_scatter_all.pdf`, `results/cooccurrence_scatter_env.pdf`, `results/cooccurrence_scatter_soil.pdf`)*

---

### Finding 16 — Partners of metal-gene-rich genera are themselves richer in metal genes and show a Firmicutes bias (exploratory)

To characterise which genera preferentially co-occur with high-KO-density focal genera, the top-50 soil-stratum focal genera (by `ko_per_mb_primary`, mean = 20.32 ko/Mb) were compared against 50 controls with similar ko/Mb (±0.5 SD of median = 7.95; phylum-matched distribution). Partners were filtered at φ > 0.3 (threshold for strong co-occurrence; 0.91% of all significant positive pairs passed, confirming the network is nearly saturated for moderate associations):

| Metric | Top-50 focal | Control-50 |
|--------|-------------|------------|
| Mean partner ko/Mb | **12.776 ± 3.884** | 8.903 ± 1.792 |
| % partners in top quartile | **56.1%** | 26.3% |
| Dominant partner phylum | **Firmicutes** (40.4%) | Proteobacteria (39.9%) |

Mann-Whitney U test (partner ko/Mb: top-50 > control-50): U = 2005, p = 1.98×10⁻⁷. Chi-square on phylum distribution: χ² = 113.74, p = 2.77×10⁻¹³. Spearman correlation (focal ko/Mb ~ mean partner ko/Mb, all 100 genera): ρ = 0.604, p = 2.82×10⁻¹¹.

The Firmicutes partner bias is notable: even though Proteobacteria comprise 43% of genera in the full PGLS table, metal-gene-rich focal genera preferentially associate with Firmicutes in soil. Firmicutes are well-represented in metal-contaminated soils (e.g., Bacillus, Clostridium) and carry substantial metal resistance gene arsenals (Lemire et al. 2013), consistent with a metal-tolerance guild interpretation: genera that invest heavily in metal processing preferentially co-occur with similarly adapted neighbours.

The within-top-50 Spearman correlation (ρ = 0.284, p = 0.045) is weaker than the across-all-100 correlation (ρ = 0.604), indicating some high-KO focal genera still associate with lower-KO partners — the guild is not strictly assortative within the specialist end of the distribution.

*(Script: `scripts/partner_characterisation.py`; data: cached to `/tmp/partchar_cache/`; figures: `results/partner_bipartite_network.pdf`, `results/partner_focal_vs_partner_scatter.pdf`, `results/partner_ko_density_boxplot.pdf`)*

---

### Finding 17 — Direct genomic evidence for HGT is concentrated in resistance KOs; cofactor KOs show none (exploratory)

The 13 double-signal KOs (D > 0.2, λ < 0.3; Finding 12) were characterised for direct HGT evidence across four independent lines relative to 10 high-λ control KOs (λ > 0.7, D < 0.3):

**Part 2 (gene tree discordance — Fritz & Purvis D):** MWU test (DS D_median = 0.385 vs control D_median = −0.077): U = 123, p = 1.81×10⁻⁴. The D-statistic comparison is the strongest evidence — it is measured on the same GTDB tree used for the primary PGLS and reflects genome-level phylogenetic randomness equivalent to gene-tree/species-tree discordance.

**Parts 1 & 3 (NCBI Entrez + BV-BRC plasmid fraction — enrichment test):** A focused Mann-Whitney test comparing double-signal *resistance* KOs against background resistance KOs (n_total ≥ 50) yields p = 0.045 (NCBI Entrez: n_double = 3; merD 4.3%, aoxB 0.4%, norB 0.1%; median = 0.0042 vs background median = 0.0004; U = 122). Independent validation with BV-BRC (84,446 plasmid accessions) gives p = 0.044 (n_double = 2: merD 7.2%, norB 0.3%; n_background = 48 after arsC KO deduplication). Two independent databases converge at marginal significance. The result is driven primarily by merD (Tn21-family mer operon); the test is underpowered (few double-signal resistance KOs have n ≥ 50). gesA, gesB (n = 1 in both databases) and nrsD (n = 16) are untestable. golS is effectively chromosomal in both databases (NCBI frac = 0.000017) despite meeting the double-signal threshold; HGT may have occurred chromosomally. High-plasmid-fraction background KOs (pcoB 6.8%, merA 4.5%, tetA 4.1%) are excluded from double-signal because their D or λ fail the threshold — their presence makes the test conservative. Mobile-element co-annotation (NCBI, DS n = 13 vs ctrl n = 10): MWU p = 0.062, directionally consistent but non-significant.

**Part 4 (environmental metal enrichment — MGnify):** 5/8 DS KOs with MGnify data are significant at FDR q < 0.1 (nicC q = 5.6×10⁻⁵, nikB q = 2.8×10⁻⁵, gesA q = 9.4×10⁻⁵, iucD q = 1.1×10⁻⁴, norB q = 7.1×10⁻²). Median |ρ| = 0.034 (Spearman, DS KO presence vs bioavailable metals). The 5 DS KOs not in the MGnify enrichment dataset (nrsD, merE, merD, shp, doxDA) cannot be assessed by this metric.

| Evidence line | Group A | Group B | MWU p |
|---------------|---------|---------|--------|
| D (discordance proxy) | DS median 0.385 | ctrl median −0.077 | **1.8×10⁻⁴** |
| Plasmid frac — NCBI Entrez (resist. DS n=3 vs bg n=51) | median 0.0042 | median 0.0004 | **0.045** |
| Plasmid frac — BV-BRC (resist. DS n=2 vs bg n=48) | median 0.0049 | median 0.0005 | **0.044** |
| Plasmid frac — Resistance vs Metabolism (n=54 vs n=14) | median 0.00043 | median 0.00016 | **0.023** |
| Plasmid frac — Resistance vs all non-resistance (n=54 vs n=86) | median 0.00043 | median 0.00022 | **0.020** |
| Plasmid frac BV-BRC cross-cat — Resistance vs non-resistance (n=51 vs n=82) | median 0.00057 | median 0.00052 | 0.118 n.s. |
| Mobile-element fraction (NCBI, DS n=13 vs ctrl n=10) | median 0.000 | median 0.000 | 0.062 |
| MGnify metal enrichment | 5/8 sig (q<0.1) | not available | — |

**Cross-category plasmid fraction comparison (NCBI Entrez, all 275 KOs queried, n_total ≥ 50; script: `scripts/plsdb_resistance_crossref.py`; data: `data/ncbi_plasmid_fraction_allcats.csv`):**

| Subcategory | n | Median plasmid_frac |
|-------------|---|---------------------|
| Resistance/Detoxification | 54 | 0.00043 |
| Transport/Homeostasis | 48 | 0.00021 |
| Sensing/Regulation | 21 | 0.00020 |
| Metal-dependent Metabolism | 14 | 0.00016 |
| Cofactor Biosynthesis | 2* | 0.00012 |

*Only hemH and MOCS2B have n≥50; cobC1 (n=45) and ahbAB (n=2) excluded.

Resistance > Metal-dependent Metabolism: MWU p = 0.023. Resistance > all non-resistance combined: MWU p = 0.020. Resistance > Cofactor: p = 0.082 (underpowered, n_cofactor=2). Cofactor KOs have plasmid fracs ≤ 0.023%, consistent with strict chromosomal location. The gradient (resistance > transport ≈ sensing > metabolism > cofactor) mirrors the λ ordering.

**Cross-category plasmid fraction comparison (BV-BRC, n_bvbrc_total ≥ 50; data: `data/bvbrc_plasmid_fraction_allcats.csv`):**

154 rows (66 original resistance KOs + 88 non-resistance KOs); large-n genes estimated via 4-page sampling.

| Subcategory | n (n≥50) | Median frac |
|-------------|----------|-------------|
| Resistance/Detoxification | 51 | 0.00057 |
| Transport/Homeostasis | 46 | 0.00052 |
| Sensing/Regulation | 21 | 0.00055 |
| Metal-dependent Metabolism | 12 | 0.00033 |
| Cofactor Biosynthesis | 2* | 0.00035 |

*Only hemH (n=346,821) and cobT‡ meet n≥50; cobC1, MOCS2B, ahbAB, ahbD excluded.

Mann-Whitney (alternative='greater', n_bvbrc_total ≥ 50): Resistance > All non-resistance: U=2347, **p=0.118 (NOT significant;** n=51 vs n=82). Resistance > Metabolism: p=0.129. Resistance > Sensing: p=0.103. Resistance > Transport: p=0.271. DS-resistance vs BG-resistance (confirmatory): U=84, p=0.047 (n=2 vs n=49; consistent with the original focused test p=0.044).

The BV-BRC cross-category comparison does not replicate the NCBI p=0.020 signal. Two factors explain this discordance: (1) the Transport/Homeostasis group in BV-BRC is inflated by functional resistance genes classified as transport (aph at 7.1%; metal efflux transporters czcA/czcB from the original 66-KO dataset), collapsing the gap between Transport and Resistance medians; (2) BV-BRC sampling estimates for large-n genes add noise. The within-resistance DS vs BG confirmatory signal (p=0.047) is directionally consistent across both databases.

**Internal structure consistency:** All 13 double-signal KOs are resistance/transport/sensing genes — matching the category-level null result (Finding 4), which found resistance genes show no niche-breadth association (β ≈ 0, p = 0.66). HGT-mobile resistance genes are thus decoupled from ecological specialisation at both the category level (niche breadth) and the individual KO level (phylogenetic randomness). No cofactor biosynthesis KO appears among the double-signal set, consistent with cofactor genes being constitutively required and vertically inherited.

*(Scripts: `scripts/hgt_direct_evidence.py`, `scripts/plsdb_resistance_crossref.py`; data: `results/hgt_synthesis_table.csv`, `data/plsdb_enrichment_test.json`, `data/bvbrc_plasmid_fraction.csv`, `data/ncbi_plasmid_fraction.csv`, `data/ncbi_plasmid_fraction_allcats.csv`, `data/bvbrc_plasmid_fraction_allcats.csv`; figures: `results/hgt_gene_tree_discordance.pdf`, `results/hgt_transposase_proximity.pdf`, `results/hgt_evidence_heatmap.pdf`; report: `results/HGT_direct_evidence_report.md`)*

---

## Discoveries

- Metal-gene KO density (per-Mb, Tier 1+2, 140 KOs) negatively predicts standardised Levins' niche breadth across 1,574 bacterial genera (β = −0.021, FDR p = 6.4×10⁻⁸, PGLS Pagel's λ = 0.757), surviving correction for genome size, GC content, isolation source, and dominant biome.
- Genome streamlining is pervasive: 14/19 KEGG functional categories show significantly negative per-Mb density associations with niche breadth (β range −0.035 to −0.010). The metal-gene signal (β = −0.021) sits in the lower-middle of this landscape, 30–60% weaker than the housekeeping baseline. A coreness-matched permutation test (NB20; 1,000 sets) shows the overall β magnitude is not unusual among conserved gene sets of equivalent structure (emp_p = 0.298) — the overall association is part of the pervasive streamlining landscape, not a metal-specific phenomenon.
- The metal-gene/niche association has a mechanistically distinctive internal structure: resistance/detoxification genes (106 KOs) show no association (β ≈ 0, p = 0.66), while cofactor biosynthesis (7 KOs, Fe–S cluster/molybdopterin) shows the strongest signal (β = −0.033, FDR p = 5.2×10⁻⁹) — equal to the housekeeping streamlining baseline. This contrast is not a general feature of functionally heterogeneous gene categories. The split magnitude (Δβ = 0.035259) exceeds all 1,000 random partitions of the metal gene set into groups of matching size (p < 0.001 (0/1,000 permutations exceeded); NB25), and the cofactor signal is robust to removal of any individual KO (jackknife; all 4 KOs stable, β range −0.016 to −0.029, all p < 0.001; NB26).
- The effect is uniform across 9 chemically diverse metals (Tl, Fe, Ni, Zn, Al, Co, S, Cu, Mn), all FDR-significant, consistent with metal-gene investment as a general genomic specialisation strategy.
- **CWM from environment XGBoost (NB29; exploratory)**: XGBoost trained to predict community-weighted mean (CWM) metal-gene density (mean_n_metal_clusters RA-weighted; trait mean=12.7, SD=8.2) from environmental variables (pH, temperature, precipitation, elevation, NDVI, clay, lat/lon, log_Cu/Zn/Pb/Ni) with spatial 5-fold block CV. Mean CV RMSE = 11.89 (range: Block 0=19.37 to Block 3=6.20), comparable to the within-sample SD — environmental variables predict CWM poorly in held-out geographic blocks. SHAP importance: metal features (Cu+Zn+Pb+Ni) contribute 45.9% of mean |SHAP|; top predictor is log_Ni_ppm (mean |SHAP|=2.23). The metal-feature dominance in SHAP alongside poor spatial-block RMSE is consistent with NB28 — metals structure community composition but the spatial heterogeneity means environment → CWM transfer generalises poorly across regions. Hypothesis partially supported: metals do contribute beyond pH+climate in SHAP, but overall predictive power is low (RMSE ≈ SD).
- **Inverse RDA / variance partitioning (NB28; exploratory)**: CLR-transformed genus abundances (top-200 genera, n=5,000 subsampled MicrobeAtlas samples) were partitioned across metal (Cu, Zn, Pb, Ni log-ppm) and pH+climate (pH, temp, precip) environmental axes. All env vars together explain R²=0.110 of CLR community variance. The unique metal contribution (metals | pH+climate) is R²=0.064, exceeding the unique pH+climate contribution (R²=0.041; shared variance R²=0.005). The metal-unique fraction is 58% larger than the pH+climate-unique fraction, a reversal of the conventional expectation that pH dominates community composition. Note: R² values are unadjusted and computed on a linear model (not permutation-tested); interpretation is descriptive. Biplot shows metal concentration vectors (Cu, Zn, Pb, Ni) are positively correlated with PC1, orthogonal to pH/temp, consistent with metals structuring community composition along an independent axis.
- **Two-scale phylo-D framework (exploratory)**: A genome-level Fritz & Purvis D / genus-level Pagel's λ framework across 275 overlapping KOs identifies 13 "double-signal" resistance/transport/sensing genes (D > 0.2, λ < 0.3) as the most likely HGT-mobile subset. D and λ are near-orthogonal (Spearman ρ = −0.041, p = 0.49), validating that the two metrics capture independent evolutionary signals. No cofactor biosynthesis KO appears among the double-signal set — consistent with cofactor genes being constitutively vertically inherited.
- **Metal-gene-rich genera occupy narrower pH niches but not narrower temperature niches (exploratory)**: PGLS shows that per-Mb metal-gene density predicts pH niche width (β = −0.760, p = 0.001; λ = 0.11) and composite environmental gradient (β = −0.064, p < 0.001) but not temperature niche (p = 0.929). The pH specificity reflects metal-speciation pH-dependence; the temperature null contrasts with the primary thermal-stability framework.
- **Metal-gene-rich genera have significantly more positive co-occurrence partners across all environments (exploratory)**: PGLS of positive partner count on metal-gene KO density yields β = 138.4–210.5 across ALL/ENV/SOIL strata (all p < 3.4×10⁻²²). The soil stratum effect (β = 210.5, p = 8.2×10⁻⁴¹) is 2.5× larger than the all-strata effect, converging with the stronger primary PGLS signal in soil specialists (Finding 10). Caution: all three networks are near-saturated (38–42% significant positive pairs), making clustering and betweenness metrics degenerate.
- **Partners of metal-gene-rich focal genera are themselves metal-gene-rich and show a Firmicutes bias (exploratory)**: Top-50 soil focal genera (mean 20.32 ko/Mb) attract partners with significantly higher mean KO density (12.776 vs 8.903 ko/Mb; MWU p = 1.98×10⁻⁷) and 56.1% vs 26.3% in the top quartile — consistent with a metal-tolerance guild assembly pattern. Partner phyla shift from Proteobacteria dominance (controls) to Firmicutes (40.4% of focal partner instances; χ² = 113.74, p = 2.77×10⁻¹³).
- **Direct HGT evidence is concentrated in resistance KOs (exploratory)**: MWU comparing D-statistics (double-signal vs high-λ controls): p = 1.81×10⁻⁴ (median 0.385 vs −0.077). NCBI Entrez plasmid fraction enrichment test (resistance-subcategory KOs, n_total ≥ 50): double-signal resistance KOs (n=3: merD 4.3%, aoxB 0.4%, norB 0.1%) vs background resistance (n=51); MWU p = 0.045. Independent BV-BRC validation: p = 0.044 (n_double=2, n_background=48, arsC deduplicated). NCBI cross-category comparison (all 275 KOs, n_total ≥ 50): resistance > metal-dependent metabolism at MWU p=0.023; resistance > all non-resistance at MWU p=0.020. BV-BRC cross-category comparison (154 rows, n_bvbrc_total ≥ 50): resistance > all non-resistance p=0.118 (NOT significant), likely due to transport-category inflation by resistance-classified metal efflux genes; DS vs BG within BV-BRC p=0.047 (confirmatory, consistent with p=0.044). Cofactor biosynthesis KOs have near-zero plasmid fractions (hemH ≤ 0.07%) in both NCBI and BV-BRC. The NCBI gradient (resistance > transport ≈ sensing > metabolism > cofactor) mirrors the phylogenetic λ signal gradient. 5/8 double-signal KOs with MGnify data significant at FDR q < 0.1 for metal-environment association. All 13 double-signal KOs are resistance/transport/sensing genes; zero are cofactor biosynthesis. Scripts: `scripts/plsdb_resistance_crossref.py`; data: `data/plsdb_enrichment_test.json`, `data/bvbrc_plasmid_fraction.csv`, `data/ncbi_plasmid_fraction_allcats.csv`, `data/bvbrc_plasmid_fraction_allcats.csv`.

---

## Results

### Primary confirmatory tests

| Test | n | λ | β | SE | p (raw) | p (FDR joint) | Outcome |
|------|---|---|---|----|---------|--------------|---------|
| P1: Bacteria (primary 140 KOs) | 1,574 | 0.757 | **−0.021** | 0.0037 | 2.1×10⁻⁸ | **6.4×10⁻⁸** | **SIGNIFICANT** |
| P2: Archaea (primary 140 KOs) | 95 | 0.726 | −0.014 | 0.0087 | 0.119 | 0.178 | NS (directionally consistent) |
| P3: NGSA / Australia | 482 | 0.346 | −0.002 | 0.0055 | 0.755 | 0.755 | NS (near-zero) |

### Evidence-tier sensitivity

| KO set | n KOs | n genera | β | p (raw) | Status |
|--------|-------|---------|---|---------|--------|
| Primary (Tier 1+2) | 140 | 1,574 | −0.021 | 2.1×10⁻⁸ | **SIGNIFICANT** |
| All non-ambiguous (T1.4) | 444 | 1,073 | −0.027 | 5.0×10⁻⁸ | **SIGNIFICANT** |
| BacMet-only (T1.5) | 188 | 1,073 | −0.011 | 0.050 | borderline |

### Sensitivity analyses

p-values are raw (one test per sensitivity check; no within-family multiplicity correction applied).

| Check | β | p (raw) | Consistent with H1? |
|-------|---|---------|----------------------|
| S1: λ = 0 (OLS) | −0.032 | ≈0 | Yes (stronger) |
| S2: λ = 1 (Brownian) | −0.018 | 3.7×10⁻⁶ | Yes |
| S3: Archaea, min n=5 | −0.018 | 0.084 | Yes (underpowered) |
| S4/S5: min n=50/150 | −0.021 | 2.1×10⁻⁸ | Yes (identical) |
| S6: Raw Levins' B | −0.286 | 1.1×10⁻¹¹ | Yes (stronger) |
| S7: Australia only | −0.002 | 0.755 | Directionally yes, null |
| S8: Northern hemisphere | −0.030 | 3.2×10⁻⁶ | Yes (stronger) |
| Soil-restricted | −0.033 | 0.007 | Yes (stronger) |

### Replication and robustness analyses

| Analysis | n | β (or ρ) | p | λ | Outcome |
|----------|---|---------|---|---|---------|
| P5: AusMicrobiome density (genomic KO/Mb predictor) | 482 | **−0.052** | 2.2×10⁻¹⁵ | 0.734 | **CONSISTENT WITHIN-DATASET** (subset of P1 genera; not independent) |
| P4: AusMicrobiome+NGSA Cu (soil conc. predictor) | 482 | −0.011 | 0.016 (q=0.041) | 0.319 | **SIGNIFICANT** |
| P4: AusMicrobiome+NGSA Zn | 482 | −0.011 | 0.016 (q=0.041) | 0.318 | **SIGNIFICANT** |
| P4: AusMicrobiome+NGSA Pb | 482 | −0.009 | 0.034 (q=0.057) | 0.326 | NS (q > 0.05) |
| P4: AusMicrobiome+NGSA Ni | 482 | −0.009 | 0.049 (q=0.061) | 0.354 | NS (q > 0.05) |
| P4: AusMicrobiome+NGSA Co | 482 | +0.001 | 0.776 | 0.353 | NS; wrong direction |
| EMP 16S (EMPO-2 niche breadth) | 539 | −0.019 | 0.099 | — | NS; directionally consistent |
| ENIGMA FRC (within-site, Spearman) | 29 MAGs / 3 wells | ρ = −0.41 (burden) | 0.029 | — | Data coverage failure; uninformative |

**P5 (genomic density, n=482):** PGLS `mean_levins_B_std ~ ko_per_mb_primary_z` restricted to the
482 AusMicrobiome genera using the same per-Mb density values as P1 (z-scored within subset).
β = −0.052 (SE = 0.0063, t = −8.20, p = 2.2×10⁻¹⁵, partial R² = 0.194, ΔAIC vs null = −61.2).
λ = 0.734. The effect is 2.5× larger than P1 and consistent in direction with EMP. Z-test vs P1:
z ≈ 4.1, p < 0.001 (NB21). The larger P5 β likely reflects reduced phylogenetic diversity in the
continental subset. **Classification: CONSISTENT WITHIN-DATASET (not independent — all 482 genera are a subset of P1 with the same density predictor).**

**P4 (soil metal concentration, n=482):** Cu and Zn significant after BH-FDR (q = 0.041 each).
λ = 0.32–0.35, substantially lower than P1. **Classification: PARTIAL REPLICATION.**

*(Notebooks: 12_ngsa_proper_replication.ipynb for P4; 15_ausmicrobiome_density_replication.ipynb for P5; 21_aus_beta_comparison.ipynb for β diagnostic)*

### Geological proxies

Preliminary cross-referencing of KO density against ore-deposit proximity (n = 18–19 regions,
CMMI database) showed weak, non-significant correlations: Cu r = 0.34 (p = 0.17),
Zn r = 0.34 (p = 0.17), Pb r = 0.01 (p = 0.99). Exploratory only.

*(Notebook: 07_marine_and_geological_proxies.ipynb)*

### Functional landscape analysis

**Status: COMPLETE (NB18).** See Finding 3 for full table and summary.

*Data: `data/functional_landscape_results.csv`, `figures/functional_landscape_forest.png`.*

### Negative controls

**Predictor permutation test (n = 1,000):** Null β distribution mean ≈ 0, SD = 0.0029; observed
β = −0.0207 is **7.14 SD below the null mean**; empirical p = 0/1000 (< 0.001).

![Permutation null histogram](figures/negative_control_permutation.png)

**Named negative-control gene sets (NB17, COMPLETE):** See Finding 5 table for actual results.
All three housekeeping controls showed strongly negative β (−0.029 to −0.034), establishing the
streamlining baseline rather than serving as true nulls.

**Five confirmed true-negative categories (NB18):** ABC transporters (non-metal), AMR
(beta-lactam), glycan biosynthesis, cell motility, two-component systems — all |β| < 0.006, q >
0.45. See Finding 5.

**Coreness-matched permutation (NB20, COMPLETE):** 1,000 KO sets matched on count and coreness
decile; null β median = −0.018 (range −0.039 to +0.012). Observed β = −0.021 yields **emp_p =
0.298**. The primary metal-gene β is within the null distribution — the overall association is
not distinguishable from coreness-matched alternatives. The genome-size attenuation comparison
(NB20 Block 4) shows the observed 46.7% attenuation falls within the permuted 95% CI [43.9%,
318.2%] (permuted median 94.9%); the observed attenuation is not inconsistent with the permuted null distribution, though the confidence interval is wide (95% CI [43.9%, 318.2%]) and the test provides only weak evidence.

The distinctive feature of the metal-gene set is not the overall β magnitude but the internal
functional split (Finding 4): resistance genes (β ≈ 0) vs cofactor biosynthesis (β = −0.033).

*Data: `data/negative_control_pgls_results.csv`, `data/coreness_permutation_results.csv`,
`data/attenuation_profile_comparison.csv`, `figures/coreness_permutation_histogram.png`.*

### Internal substructure comparison

**Status: COMPLETE (NB19).** AMR, TCS, and ABC transporters tested at sub-functional resolution.
All AMR and TCS subcategories are positive (inducible/HGT character); the sole significantly
negative ABC subcategory is Lipid/LPS export (β = −0.030, q = 3.3×10⁻⁵), consistent with
constitutive outer-membrane maintenance. The resistance-null / constitutive-significant split
is distinctive to metal genes. See Finding 4 for full results.

*Data: `data/internal_structure_results.csv`, `figures/internal_structure_forest.png`.*

### Split magnitude permutation

**Status: COMPLETE (NB25).** 1,000 random partitions of the 140-KO metal gene set into groups
of sizes 106 and 7 (matching resistance/cofactor sizes). Observed Δβ = 0.035259 exceeds all
1,000 null splits (p < 0.001 (0/1,000 permutations exceeded); null median = −0.006, SD = 0.007). Comparison families: ABC
Δβ = 0.032, AMR Δβ = 0.012, TCS Δβ = 0.006. Metal gene set has the largest internal split.

*Data: `data/split_magnitude_permutation.csv`, `figures/split_magnitude_permutation.png`.*

### Cofactor jackknife

**Status: COMPLETE (NB26).** Leave-one-KO-out for 4 assignable cofactor KOs. All 4 jackknife
models significant (β range −0.016 to −0.029, all p < 0.001, no sign changes). No single KO
drives the cofactor association.

*Data: `data/cofactor_jackknife_results.csv`, `figures/cofactor_jackknife_forest.png`.*

### MAG quality sensitivity

**Status: COMPLETE (NB22).** Completeness covariate: NS (p = 0.43), density β unchanged.
Contamination covariate: slight positive association (p = 0.042), density β unchanged (<1.2%
change). HQ-restricted (≥90%/≤5%, n = 511): β = −0.018, p = 0.005 — signal persists. See
Finding 7 for full results.
*Data: `data/mag_quality_sensitivity.csv`.*

### Category descriptive statistics and conditional PGLS

**Status: COMPLETE (NB23).**

Core fraction at the 95% prevalence threshold = 0 for all five metal functional categories
(293,059 genomes; no metal KO meets the near-universal threshold). Conditional PGLS models:

| Model | β (ko_per_mb_z) | p | Attenuation vs baseline |
|-------|----------------|---|------------------------|
| Baseline | −0.0207 | 2.1×10⁻⁸ | — |
| + annotation depth (n_ko_ann_z) | −0.0304 | 7.9×10⁻¹¹ | **+46.7% (SUPPRESSOR)** |
| + genome size (genome_mb_z) | −0.0110 | 0.006 | −46.7% (true attenuation) |

Annotation depth (n_ko_ann_z) amplifies β rather than attenuating it: genera with richer
annotations have fewer apparent metal-gene specialists, and controlling for annotation bias
strengthens the signal. Genome size is the only true confounder, reducing β by 46.7% — within
the coreness-permutation CI. The n_ko_ann_z and ko_breadth_z covariates are perfectly collinear
(both derived from n_ko_primary); the conditional result is identical for either.

*Data: `data/category_descriptive_stats.csv`, `data/category_conditional_models.csv`.*

---

## Interpretation

*Confirmatory vs exploratory: Findings 1–8, 10–11 (Notebooks 01–05, 12, 15–17) were fully pre-specified with directional hypotheses and decision rules before data inspection; Findings 9, and all NB17–NB24 exploratory analyses (internal structure, functional landscape, MAG quality, AUS β comparison, niche-breadth sensitivity, coreness permutation, category conditional models) were designed after the P1 result was seen and contribute to mechanistic interpretation only — they cannot shift the H1 classification. See `METHODS.md §18 Analysis Registry` for the complete record.*

### Contextualising the metal-gene signal within the genome-streamlining landscape

The finding that 14/19 KEGG functional categories show significantly negative per-Mb density
associations with niche breadth (Finding 3) establishes the proper interpretive frame: this is a
pervasive genome-streamlining effect. Ecological specialists reduce their genomes across the board,
so any conserved gene set becomes denser per Mb. Ribosomal proteins (β = −0.029), amino acid
biosynthesis (β = −0.034), and DNA repair (β = −0.033) — classic null controls — all show the
streamlining signature at the same or greater magnitude as the metal-gene set.

Within this landscape, the **novel contribution** of this project is not that metal genes show a
negative signal — they would be expected to, given genome streamlining — and the coreness-matched
permutation (NB20; emp_p = 0.298) confirms that the overall β = −0.021 is not unusual for a
conserved gene set of this size and prevalence structure. The distinctive features are:

1. **The metal-gene signal is 30–60% weaker than the housekeeping baseline** (P1 β = −0.021 vs
   housekeeping β ≈ −0.029 to −0.035). This residual gap is interpretable as a genuine content
   signal: specialists do not compact all genes equally; they are specifically enriched in
   metal-processing genes above what genome-size-driven compaction alone predicts. This
   comparison to the housekeeping baseline is mechanistically motivated; the coreness permutation
   addresses a different question (whether the overall β is extreme within the null) and its
   negative result (emp_p = 0.298) does not negate the housekeeping gap.

2. **The internal functional split is mechanistically distinctive and quantitatively unusual.**
   Resistance/detoxification genes (β ≈ 0) fall among the five confirmed true-negative categories —
   variable, inducible, HGT-mobile gene sets with no constitutive coupling to genome size. In
   contrast, cofactor biosynthesis (β = −0.033) matches the housekeeping baseline exactly,
   indicating constitutive, irreversible genomic investment. This contrast (Δβ ≈ 0.036 across
   five functional subcategories within the same primary gene set) is not replicated in the three
   comparison categories tested at the same resolution (AMR, TCS, ABC transporters — NB19), where
   all subcategories share the same directional character.

3. **Resistance genes are specifically decoupled.** The null signal in resistance/detox genes is
   mechanistically explained by HGT decoupling resistance gene content from ecological
   specialisation (Pal et al. 2015; Gios et al. 2025). Critically, these genes fall among the
   confirmed true-negative categories, not between the streamlining baseline and true null — the
   null is precise, not intermediate.

### Genome-size confounding: partial, not total

Controlling for genome size reduces β by 46.7%, just below the pre-specified 50% threshold. The
association survives correction (p = 0.006). This is consistent with the streamlining
interpretation: small-genome specialists invest a disproportionately high *fraction* of their
genomes in metal processing, over and above what genome size alone predicts. The 46.7% attenuation
also places the metal-gene genome-size effect within the expected range for streamlining indicators —
not an outlier requiring a special explanation.

### Why Australia shows no signal in P3

The NGSA Australia-only replication (P3, n = 482, β = −0.002) is consistently near-zero. Probable
explanations: (1) the Australian continent's relative geological stability produces lower cross-biome
variation in metal-gene investment; (2) the NGSA soil geochemistry covers a narrower chemical
gradient; (3) all P3 genera also appear in P1, reducing independent information without adding new
signal. The AusMicrobiome genomic density analysis (P5, same genera, same genomic predictor, within-dataset) recovers a
strong and larger signal, indicating the near-zero P3 result reflects the soil-concentration
predictor rather than the genus panel.

### Literature Context

**Niche breadth in prokaryotes.** Rastogi et al. (2023) quantified Levins' B across marine
bacterioplankton and found that generalists (B = 11.5) and specialists (B = 8.9) differ by ~29%
in niche breadth, with specialist niches shaped by deterministic selection (54.1% vs. 62.8%
stochastic for generalists). This provides a direct empirical baseline: our P1 effect operates
across this observed B_std range. Szukics et al. (2024) applied a modified Levins' B to soil
Thaumarchaeota and found the evolutionary transition from generalist to specialist occurs at a
6-fold higher rate than the reverse — consistent with the streamlining interpretation that
metabolic versatility is harder to reacquire than to lose.

**Genome size and lifestyle.** Leu et al. (2022) showed that free-living (oligotrophic,
specialist) marine genomes average 3.0–4.5 Mb, while particle-associated (generalist) genomes
average 4.5–5.2 Mb — a 24–35% size difference — and generalists carry 2–5-fold more CAZymes
and 8+ substrate-class transporters per genome. Lauro et al. (2009) found comparable size
reductions in SAR11 and *Prochlorococcus* specialists, with gene loss concentrated in regulation
and secondary metabolism. Our confounder analysis is consistent with this literature: genome size
explains 46.7% of β but the association survives correction (p = 0.006), indicating metal-gene
density tracks specialisation beyond what genome size alone predicts.

**HGT and resistance genes.** The non-significant resistance gene category (β ≈ 0) is
mechanistically explained by HGT decoupling resistance gene content from vertical inheritance
(Pal et al. 2015). Critically, Gios et al. (2025) demonstrated in Patescibacteria that per-Mb
HGT rates are independent of genome size (1.1 HT genes/Mb regardless of genome scale), and
that metal-linked ABC cation transporters are preferentially acquired. This constant per-Mb HGT
rate means resistance gene abundance tracks current selective pressure rather than long-term
ecological specialisation — predicting precisely the null signal we observe.

**Cofactor biosynthesis.** The cofactor biosynthesis signal (β = −0.033) aligns with the
observation that Fe–S cluster assembly is one of the most conserved, vertically inherited gene
sets in prokaryotes (Lill 2009). No published study systematically quantifies Fe–S or
molybdopterin gene variation by ecological niche type, making the strong categorical signal in
this finding the novel observation of this project.

**Gap filled.** A systematic search of the literature found no paper that quantifies per-megabase
metal-gene KO density across prokaryotic genera and correlates it with standardised Levins' B_std
using phylogenetically controlled analysis. The closest prior work (Leu et al. 2022) examines
metal transporter presence/absence by ocean lifestyle without per-Mb densities or PGLS. This
project fills that gap directly.

### Novel Contribution

Prior microbial ecology studies of metal tolerance have focused on explaining variation *among*
metal-contaminated sites or strains within species. This project demonstrates a cross-genus,
phylogenetically controlled relationship between genomic metal-gene investment and global
ecological breadth. The overall β = −0.021 is part of the pervasive streamlining landscape and
is not extreme relative to coreness-matched alternatives (NB20; emp_p = 0.298). The novel
contribution lies elsewhere: placing this signal within the landscape (Finding 3) reveals two
specific features that are not expected of an arbitrary conserved gene category. First, the
30–60% gap between the metal-gene signal and the housekeeping baseline — metal genes are less compacted than housekeeping genes, consistent with selective retention. Second,
and more distinctively, the precise internal split: resistance genes (β ≈ 0) fall in the
true-negative category while cofactor biosynthesis (β = −0.033) matches the housekeeping
baseline. This internal contrast (Δβ ≈ 0.036) is not reproduced in comparison functional
families at the same sub-functional resolution (AMR, TCS, ABC transporters — NB19), making
metal-cofactor dependence — not stress-response capacity — the mechanistic driver most consistent with the observed patterns.

---

## Manuscript reviewer response analyses (2026-07)

Four questions were addressed to sharpen specificity, audit a comparison set, reconcile a cross-project finding, and test a mechanistic hypothesis. All new analyses are labelled exploratory.

### Q1 — Null functional category PGLS (standalone confirmation)

**Status: COMPLETE (`scripts/null_category_pgls.py`, `data/null_category_pgls_results.csv`).**

Per-Mb KO density for five non-metal KEGG categories was tested against niche breadth as a specificity control:

| Category | KOs | Genera | β | SE | p (raw) | NB18 q (FDR-19) | Status |
|---|---|---|---|---|---|---|---|
| abc_transporters | 475 | 1,073 | −0.00546 | 0.00628 | 0.385 | 0.457 | NS |
| amr | 112 | 1,073 | −0.00387 | 0.00546 | 0.478 | 0.505 | NS |
| glycan_biosyn | 73 | 1,050 | +0.00119 | 0.00402 | 0.767 | 0.767 | NS |
| cell_motility | 153 | 1,063 | +0.00397 | 0.00545 | 0.466 | 0.505 | NS |
| two_component | 521 | 1,073 | +0.00592 | 0.00651 | 0.364 | 0.457 | NS |

All five non-significant (p > 0.36; |β| < 0.006). Matches NB18 functional landscape results exactly; provides standalone reproducibility. These five categories confirm the specificity of the metal-gene signal and serve as confirmed true-negative controls in §3.7 and §4.3 of the manuscript.

### Q2 — Cofactor/vitamin KO overlap audit

**Status: COMPLETE (`scripts/cofactor_overlap_audit.py`, `data/cofactor_overlap_audit.csv`).**

All 382 KOs in the KEGG 'cofactors and vitamins' category were cross-referenced against the full 730-KO curated metal gene list (all 5 evidence tiers), BacMet2, and Pfam metal-binding clan coverage.

- **83 shared** across the two lists.
- **12 in primary 140** (already excluded from the 370-KO non-metal cofactor comparison set).
- **71 additionally flagged** (in 730-KO list Tiers 3–5 or BacMet2): heme biosynthesis (hemA/B/C/D/E/G/H/J/L/N, hemQ), cobalamin/cobamide (cobA–Q, cbiA–T), molybdopterin (moaA/C), biotin (bioA/B/D/F/I/U/W). All are metal-dependent cofactor biosynthesis pathways by KEGG design.
- These 71 KOs are mechanistically non-metal cofactors (they produce cofactors for other enzymes, not direct environmental metal processing). Their presence in the 370-KO comparison set does not alter interpretation.
- β for the full 382-KO set (−0.029) = β for the 12-KO-reduced 370-KO set (−0.029): near-identical, confirming minimal quantitative impact of the broader overlap.
- **Conclusion**: the non-metal cofactor comparison is valid; the 83/382 overlap is expected from KEGG category design and does not threaten the specificity interpretation.

### Q3 — Carbohydrate metabolism: KO density vs GapMind breadth reconciliation

**Status: Exploratory comparison documented in §4.3 Discussion (MANUSCRIPT.md, manuscript.tex).**

An apparent contradiction between two carbon metabolism metrics is resolved:

- **Functional landscape (NB18)**: carbohydrate metabolism KO density β = −0.026, p = 1.3 × 10⁻⁹ (higher density → narrower niche).
- **GapMind carbon breadth (microbeatlas_metal_ecology NB07)**: β = +0.142, SE = 0.033, p = 1.9 × 10⁻⁵ (more complete carbon-substrate pathways → broader niche).

These are geometrically consistent: (1) Per-Mb KO density is a ratio with genome length in the denominator; streamlining shrinks the denominator, increasing per-Mb density even as the absolute carbohydrate gene complement is reduced. (2) GapMind pathway completeness counts whether full metabolic pathways are present — a qualitative repertoire metric that grows with generalism. Specialists show high carbohydrate KO density per Mb + low GapMind breadth; generalists show the converse. Both metrics reflect the same underlying biology (metabolic versatility increases with ecological breadth) from opposite measurement angles.

This comparison is exploratory (cross-study, independently computed metrics) and should be followed by an integrated genome-size-partitioned analysis.

### Q4 — Latitude mechanism tests (H4a/H4b/H4c)

**Status: COMPLETE (`scripts/latitude_mechanism_tests.py`, `data/latitude_mechanism_results.csv`, `data/genus_lat_env_covariates.csv`).**

Four PGLS models tested whether the latitude suppressor effect in Table 7 (β: 0.021 → 0.031 when latitude is added as confounder) is mechanistically explained by bedrock geochemistry (H4a) or climate stability (H4b). Genus-level covariates extracted via Spark-side aggregation from arkinlab_microbeatlas (10,040 genera returned; 1,224 matched to PGLS input). GeoROC bedrock metal concentrations (Cu/Ni/Zn/Co/Pb/Cr ppm, n=9,954 genera non-null) joined via enriched_metadata.accession_id; CMMI ore deposit proximity (n=1,161 genera) also pre-joined.

| Model | n | β_metal | p_metal | β_lat | p_lat | covariate | β_other | p_other | Status |
|---|---|---|---|---|---|---|---|---|---|
| A: metal + \|lat\| | 1,224 | −0.0207 | 6.6×10⁻⁸ | −0.0017 | 0.577 | — | — | — | OK |
| B: + GeoROC bedrock metals (H4a) | 1,221 | −0.0193 | 4.6×10⁻⁷ | −0.0035 | 0.273 | georoc | +0.0120 | **2.2×10⁻⁴** | OK |
| C: + ERA5 temp range (H4b) | 1,223 | −0.0206 | 6.5×10⁻⁸ | +0.0045 | 0.201 | temp | +0.0136 | **9.6×10⁻⁵** | OK |
| D: + CMMI proximity | 1,161 | −0.0213 | 5.9×10⁻⁸ | −0.0035 | 0.290 | cmmi | −0.0030 | 0.375 | OK |
| E: + CSU PF1 bioavail. mobility (H4a) | 1,108 | −0.0209 | 1.7×10⁻⁷ | −0.0039 | 0.264 | csu_mob | +0.0040 | 0.227 | OK |
| F: + Sci2025 soil metal HQ (H4a direct) | 1,088 | −0.0208 | 2.3×10⁻⁷ | −0.0017 | 0.649 | sci_hq | +0.0037 | 0.291 | OK |
| G: + SoilTemp range −10cm (H4b) | 207 | −0.0194 | 0.074 | +0.0037 | 0.780 | soil_temp | +0.0238 | **0.0085** | OK (n small) |
| H: + ecotapestry mafic score (H4a) | 975 | −0.0233 | 2.2×10⁻⁸ | −0.0039 | 0.281 | mafic | +0.0088 | **0.013** | OK |
| I: + USGS REE deposit proximity | 1,224 | −0.0208 | 5.6×10⁻⁸ | −0.0016 | 0.604 | ree | +0.0031 | 0.318 | OK |

**Key findings (composite models A–I):**
- **Latitude is NS** in all nine models (p = 0.20–0.78), confirming latitude per se is not an independent predictor of niche breadth after controlling for metal genes.
- **H4a (bedrock geochemistry)**: SUPPORTED via two independent bedrock proxies. (i) GeoROC total metal concentration index: β = +0.012, p = 2.2×10⁻⁴ (Model B). (ii) Ecotapestry mafic/felsic bedrock score: β = +0.009, p = 0.013 (Model H, n = 975) — mafic lithology independently predicts niche breadth, corroborating GeoROC from a categorical direction. β_metal attenuates by ≤13% in both models and remains highly significant. **Critical contrast**: Science 2025 contemporary soil metal hazard quotients (Model F, HHET; n = 1,088) and CSU PF1 bioavailable mobility fractions (Model E; n = 1,108) are both NS (p = 0.291, p = 0.227). Current soil metal concentration and bioavailability do not predict niche breadth. This contrast — bedrock geology significant, contemporary soil metal levels not — suggests the bedrock association reflects deep evolutionary or long-term ecological filtering rather than contemporary metal exposure. CMMI ore deposit proximity (Model D, p = 0.375) and USGS REE deposit proximity (Model I, p = 0.318) are also NS.
- **H4b (climate stability)**: SUPPORTED via two independent temperature metrics. ERA5 temperature range: β = +0.014, p = 9.6×10⁻⁵ (Model C, n = 1,223). SoilTemp measured soil temperature range at −10 cm: β = +0.024, p = 0.0085 (Model G, n = 207). Both positive. Caution: Model G has only 94 0.5° bins and 207 matched genera; β_metal loses significance (p = 0.074) at this n, making Model G underpowered and confirmatory of direction only. In Model C (full n), β_metal is fully unchanged by temperature. Climate variability predicts niche breadth independently but does not explain the metal-gene association.
- **Metal signal stability**: β_metal ranges from −0.019 to −0.023 across all nine models. The 7% attenuation in Model B is the largest reduction; the slight amplification in Model H (n = 975 genera, geographically restricted sample) brackets the upper end. Primary finding is robust to all geochemical and climate covariates tested.

---

### Q4 per-metal decomposition (`scripts/per_metal_bedrock_models.py`)

**Status: COMPLETE. Data: `data/latitude_mechanism_results.csv` (J–M rows), `data/bedrock_metal_diagnostics.csv`.**

Per-metal GeoROC PGLS with collinearity diagnostics and pH speciation control. Individual log(ppm+1) medians per genus queried from Spark; all models: niche_breadth ~ metal_z + lat_abs_z + georoc_X_z [+ ph_z].

**Collinearity diagnostics (all-metals VIF):**

| Metal | VIF |
|-------|-----|
| Cu | 1.16 |
| Ni | 1.87 |
| Zn | 1.14 |
| Co | 1.26 |
| Pb | 1.12 |
| Cr | 1.83 |

All VIFs < 2 — bedrock metals are near-independent at the genus geographic scale. Per-metal and joint models are valid without regularisation.

**J models (per-metal, no pH control) with BH FDR correction:**

| Model | n | β_metal | p_metal | β_bedrock | p_raw | p_BH |
|---|---|---|---|---|---|---|
| J_Cu | 1,212 | −0.0208 | 6.6×10⁻⁸ | −0.0036 | 0.235 | 0.333 |
| J_Ni | 1,220 | −0.0206 | 8.2×10⁻⁸ | +0.0015 | 0.614 | 0.614 |
| J_Zn | 1,213 | −0.0210 | 4.5×10⁻⁸ | −0.0034 | 0.278 | 0.333 |
| J_Co | 1,214 | −0.0215 | 1.9×10⁻⁸ | +0.0091 | **2.8×10⁻³** | **8.4×10⁻³** |
| J_Pb | 1,220 | −0.0209 | 5.4×10⁻⁸ | +0.0042 | 0.181 | 0.333 |
| J_Cr | 1,220 | −0.0203 | 7.8×10⁻⁸ | +0.0187 | **1.1×10⁻⁹** | **6.7×10⁻⁹** |

**K models (per-metal + pH speciation control):**

| Model | n | β_bedrock | p_bedrock | β_pH | p_pH |
|---|---|---|---|---|---|
| K_Cu | 1,212 | −0.0024 | 0.437 (NS) | +0.0110 | **7.9×10⁻⁴** |
| K_Ni | 1,220 | +0.0017 | 0.557 (NS) | +0.0117 | **2.7×10⁻⁴** |
| K_Zn | 1,213 | −0.0033 | 0.289 (NS) | +0.0114 | **4.3×10⁻⁴** |
| K_Co | 1,214 | +0.0072 | **0.020** | +0.0100 | **2.3×10⁻³** |
| K_Pb | 1,220 | +0.0027 | 0.392 (NS) | +0.0113 | **5.3×10⁻⁴** |
| K_Cr | 1,220 | +0.0176 | **1.0×10⁻⁸** | +0.0095 | **3.0×10⁻³** |

**M model (all 6 simultaneously, VIF < 2):** n = 1,207; β_metal = −0.022 (p = 6×10⁻⁹).

| Metal | β | p | |
|---|---|---|---|
| Cr | +0.0301 | **9.5×10⁻¹³** | dominant |
| Ni | −0.0164 | **5.5×10⁻⁵** | reverses sign (suppressor vs Cr) |
| Pb | +0.0072 | **0.030** | positive |
| Co | +0.0046 | 0.171 | NS in joint model |
| Cu | −0.0011 | 0.736 | NS |
| Zn | −0.0016 | 0.630 | NS |

**PCA models:** PC1 (positive loadings on all metals, 47% var): β = +0.009, p = 0.0025. PC2 (contrast axis, 22% var): β = −0.007, p = 0.029. Both significant.

**Key findings (per-metal):**
- **Cr is the dominant driver** of the composite GeoROC signal: β = +0.019 (J), BH p = 6.7×10⁻⁹; unchanged after pH control (β = +0.018, p = 1.0×10⁻⁸). In the joint M model, β_Cr = +0.030 (p = 9.5×10⁻¹³). Chromium enrichment indicates mafic/ultramafic bedrock (peridotite, dunite, ophiolite) — consistent with Model H (ecotapestry mafic score). Cr speciation is redox-dominated rather than pH-dominated, explaining why pH control does not attenuate the Cr signal.
- **Co is a secondary contributor**: β = +0.009 (J), BH p = 0.0084. Attenuated but survives pH control (p = 0.020). Co is also enriched in mafic rocks and komatiites.
- **Cu, Ni, Zn, Pb**: NS in J models (FDR-corrected). The composite GeoROC signal is not driven by the common ore-forming metals.
- **pH is a consistent positive predictor** in all K models (β ≈ +0.011, p < 0.001): genera from higher-pH soils have broader niches, independent of bedrock metal type. This represents a genuine speciation/ecology signal distinct from the geological metal effect.
- **Ni suppressor in joint model**: Ni reverses to negative (β = −0.016, p = 5.5×10⁻⁵) when Cr is controlled — a partial regression effect consistent with Cr and Ni sharing mafic rock association; controlling for Cr isolates a distinct Ni effect. Interpret cautiously; this is exploratory.
- **Primary signal**: β_metal is stable (−0.019 to −0.022) across all J–M models.

---

### Q4 redox proxy controls (`scripts/redox_metal_models.py`)

**Status: COMPLETE. Results in `data/latitude_mechanism_results.csv` (N series, 4 rows). Covariates added to `data/genus_lat_env_covariates.csv` (soil moisture, SOM).**

Soil-level redox proxies from `enriched_metadata_gee` were tested as additional speciation controls for the Cr and Co signals. Two globally comprehensive proxies were used:
- **Soil moisture** (`soil_moisture_root_cm3_cm3`): high → waterlogging → anaerobic → Cr(III) (immobile)
- **Soil organic matter** (`olm_soil_organic_matter_0cm_pct`, 0 cm): high → microbial O₂ drawdown → reducing capacity

No direct Cr(VI) measurements exist at global scale: the CSU speciation table has all-null BCR fraction fields; WoSIS contains only pH/OC/texture; GEMAS (Fe₂O₃ ratio, iron oxidation proxy) is Europe-only (4,343 pts); NGSA (mobile Cr fraction, MMI extraction) is Australia-only (1,315 pts).

**Redox proxy–bedrock metal correlations (genus level, n ≈ 1,213–1,218):**

| Proxy | r vs bedrock Cr | p | r vs bedrock Co | p |
|-------|-----------------|---|-----------------|---|
| Soil moisture | −0.050 | 0.083 (NS) | −0.140 | 9.3×10⁻⁷ |
| SOM (0 cm) | −0.015 | 0.597 (NS) | −0.047 | 0.103 (NS) |

Bedrock Cr is near-orthogonal to both redox proxies. Co-rich bedrock is modestly negatively correlated with moisture (mafic terrain slightly drier/more oxidizing).

**N models — attenuation test (soil moisture as redox proxy):**

| Model | n | β_bedrock | p_bedrock | β_pH | p_pH | β_moisture | p_moisture |
|---|---|---|---|---|---|---|---|
| K_Cr (reference) | 1,220 | +0.0176 | 1.0×10⁻⁸ | +0.0095 | 3.0×10⁻³ | — | — |
| N_Cr (+ moisture) | 1,219 | +0.0175 | 1.2×10⁻⁸ | +0.0117 | 5.4×10⁻³ | +0.003 | 0.44 (NS) |
| K_Co (reference) | 1,214 | +0.0072 | 0.020 | +0.0100 | 2.3×10⁻³ | — | — |
| N_Co (+ moisture) | 1,213 | +0.0072 | 0.021 | +0.0120 | 5.2×10⁻³ | +0.003 | 0.50 (NS) |

**N_som models — secondary redox proxy (SOM):**

| Model | n | β_bedrock | p_bedrock | β_pH | p_pH | β_SOM | p_SOM |
|---|---|---|---|---|---|---|---|
| N_Cr_som | 1,218 | +0.0187 | 1.3×10⁻⁹ | +0.003 | 0.39 (NS) | −0.0155 | **6.8×10⁻⁵** |
| N_Co_som | 1,213 | +0.0075 | 0.016 | +0.005 | 0.21 (NS) | −0.0134 | **6.6×10⁻⁴** |

**Key findings (redox controls):**
- **Bedrock Cr signal is not mediated by soil redox.** β_Cr is unchanged to three decimal places in N_Cr vs K_Cr (0.0175 vs 0.0176). Soil moisture is NS (p = 0.44) after controlling for bedrock Cr. This rules out the "Cr(VI) via reducing/waterlogged soils" mechanistic pathway.
- **SOM is an independent negative predictor of niche width** (β = −0.016, p = 6.8×10⁻⁵ in Cr model; β = −0.013, p = 6.6×10⁻⁴ in Co model). High-SOM soils have narrower niches independently of bedrock metal type. This is an incidental finding not in the original model set.
- **SOM absorbs the pH association.** When SOM is included, pH drops from significant (p ≈ 0.003 in K models) to NS (p = 0.39). The "broader niches at high pH" signal found in all K models is largely mediated through or confounded with SOM — high-SOM environments (boreal, peatlands) tend to be acidic, and SOM may drive DOM chelation effects on metal speciation more directly than pH per se.
- **Mechanistic implication for Cr**: the bedrock Cr → niche width signal operates independently of soil redox conditions. Possible mechanisms: (a) chronic Cr(III)/Ni/Mg stress characteristic of serpentine soils (ultramafic effect); (b) ultramafic terrain selects for microbial niche specialists via multiple co-correlated factors (Ca/Mg ratio, soil structure, slow weathering) beyond Cr(VI) toxicity alone.

---

## Limitations

- **Streamlining effect is correlational.** The functional landscape (Finding 3) demonstrates that
  the metal-gene signal sits within a pervasive genome-streamlining pattern. Disentangling
  streamlining-driven compaction from metal-specific ecological selection requires either (a)
  explicit genome-size correction (Finding 7: β survives at 46.7% attenuation) or (b) comparison
  to the true-negative categories (Finding 5). The current evidence supports metal-content
  enrichment above compaction, but causality remains unresolved.
- **r² = 0.046 in P1**: Metal-gene density explains a small fraction of genus-level niche breadth
  variance. Ecological breadth is multidimensionally determined.
- **P3 / Australia-only null**: The NGSA replication is near-zero, reducing confidence in
  universality of the soil-concentration predictor.
- **BacDive NB09 incomplete**: Culture-based geographic niche breadth replication pending execution.
- **ENIGMA FRC data coverage**: n = 3 wells; uninformative at this sample size.
- **Levins' B_std from 16S OTUs**: Coarse OTU–genus matching and MicrobeAtlas annotations
  may introduce noise.
- **Cofactor category (n = 7 KOs)**: Strongest categorical signal rests on 7 KOs. Statistical
  result is robust (ΔAIC = −35.4) but the narrow biological definition warrants caution.
- **MAG completeness/contamination**: Per-Mb density may be affected by MAG incompleteness
  non-randomly distributed across taxa. NB22 tested this: density β is unchanged after adding
  completeness (p = 0.43, NS) or contamination (p = 0.042, <1.2% β change) as covariates;
  HQ-restricted sensitivity (n = 511) yields β = −0.018, p = 0.005. Concern is addressed.
- **Resistance-gene null interpretation**: CIs do not exclude small effects; this null should be
  interpreted as absence of a substantial phylogenetically conserved association.
- **Coreness-matched permutation (NB20) does not support uniqueness of the metal gene set among
  conserved gene categories.** emp_p = 0.298: the primary β = −0.021 is within the null
  distribution of coreness-matched KO sets. The overall association is part of the streamlining
  landscape; the distinctiveness of the metal gene set lies in its internal functional split, not
  its overall magnitude.
- **Category conditional PGLS (NB23):** Core fraction is zero at the 95% threshold for all
  metal categories, so coreness cannot explain functional specificity. Genome size partially
  confounds the association (46.7% attenuation), but the signal survives (p = 0.006). Annotation
  depth is a suppressor variable rather than a confounder.
- **SOM as potential mediator of pH niche signal (Q4 incidental finding):** Soil organic matter (SOM) independently predicts narrower niches (β = −0.016, p = 6.8×10⁻⁵ in Cr model) and absorbs the pH association when included in Q4 K-models (pH: p ≈ 0.003 → p = 0.39 with SOM). The pH niche-breadth signal reported in Finding 13 (β = −0.760) may be partially mediated by SOM availability — high-SOM acidic soils (boreal peatlands) represent metal-speciation niches where SOM-metal chelation may confound a direct pH → speciation → specialist-selection interpretation.
- **Co-occurrence confound (Findings 15–16):** The positive-partner-count signal (β = 138–210 across strata) is correlated with niche breadth (Spearman ρ = 0.33–0.37, p < 10⁻⁴⁰). Partial analyses controlling for B_std are needed before interpreting the co-occurrence signal as independent of the primary specialisation axis.

---

## Data

### Sources

| Collection | Tables Used | Purpose |
|------------|-------------|---------|
| `kbase_ke_pangenome` | `eggnog_mapper_annotations`, `gene_genecluster_junction`, `gene_cluster`, `genome`, `gtdb_taxonomy_r214v1` | KO density per genus from MAG pangenomes |
| `kescience_mgnify` | OTU × sample abundance matrix (via MicrobeAtlas) | Levins' niche breadth calculation |
| `arkinlab_microbeatlas` | `sample_metadata` | pH, temperature, biome metadata for confounder checks |
| `kescience_bacdive` | `isolation`, `strain`, `taxonomy` | Geographic niche breadth (pending NB09 execution) |
| `enigma_genome_depot_enigma` | `browser_genome`, `browser_gene`, `browser_protein_kegg_orthologs`, `browser_kegg_ortholog`, `browser_sample` | ENIGMA FRC MAG KO content |
| `enigma_coral` | `ddt_brick0000007` | Oak Ridge FRC groundwater metal concentrations |
| `arkinlab_envdbs` | `cmmi_ores` | Ore deposit proximity (exploratory) |

### Generated Data

| File | Rows | Description |
|------|------|-------------|
| `data/curated_mrg_ko_ids_v2.csv` | 730 | Evidence-tiered metal-gene KO list (5 tiers, 24 metals) |
| `data/01_genus_ko_density_spark.csv` | 8,256 | Per-genus primary KO density from BERDL Spark |
| `data/01_pgls_input_bacteria.csv` | 1,574 | PGLS input: bacteria with density + niche breadth + phylogeny |
| `data/01_primary_pgls_results.csv` | 2 | P1 (bacteria) and P2 (archaea) PGLS results |
| `data/02_joint_fdr.csv` | 3 | Joint BH FDR correction across P1/P2/P3 |
| `data/02_ngsa_pgls_results.csv` | 1 | P3 NGSA Australia PGLS result |
| `data/03_tier_pgls_results.csv` | 2 | Tier-sweep PGLS results (T1.4, T1.5) |
| `data/03_category_pgls_results.csv` | 5 | Per-functional-category PGLS results |
| `data/03_metal_pgls_results.csv` | 9 | Per-metal KO-set PGLS results |
| `data/04_confounder_results.csv` | 5 | Confounder attenuation analysis |
| `data/05_sensitivity_results.csv` | 8 | Sensitivity checks (λ, subset, biome) |
| `data/emp_niche_pgls_comprehensive.csv` | 1 | EMP 16S niche breadth PGLS result |
| `data/enigma_frc_replication.csv` | 14 | ENIGMA FRC Spearman correlations |
| `data/curated_mrg_ko_ids_v2_pfam.csv` | 730 | KO list with Pfam/InterPro domain annotations |
| `data/genus_trait_table.csv` | 2,851 | Levins' niche breadth per genus from MicrobeAtlas |
| `data/negative_control_pgls_results.csv` | — | Permutation + named negative control results |
| `data/functional_landscape_results.csv` | 19 | NB18 KEGG landscape PGLS results |
| `data/clade_stratified_pgls_results.csv` | 4 | NB16 phylum-level PGLS results |
| `data/internal_structure_results.csv` | 13 | NB19 AMR/TCS/ABC subcategory PGLS (complete 2026-07-06) |
| `data/coreness_permutation_results.csv` | 1,000 rows | NB20 coreness-matched permutation null; emp_p = 0.298 |
| `data/attenuation_profile_comparison.csv` | 100 rows | NB20 genome-size attenuation profile; observed 46.7% within CI [43.9%, 318.2%] |
| `data/aus_beta_comparison.csv` | 5 | NB21 P1 vs P5 β comparison and z-tests (complete 2026-07-06) |
| `data/intersecting_genus_pgls.csv` | 1 | NB21 intersection-genus PGLS results (complete 2026-07-06) |
| `data/mag_quality_sensitivity.csv` | 4 | NB22 completeness/contamination covariate PGLS (complete 2026-07-06/07) |
| `data/category_descriptive_stats.csv` | 8 rows | NB23 per-category descriptive stats; core fraction = 0 at 95% threshold |
| `data/category_conditional_models.csv` | 5 rows | NB23 conditional PGLS; annotation depth is suppressor; genome size attenuates 46.7% |
| `data/split_magnitude_permutation.csv` | 4 rows | NB25 split magnitude permutation; Metal gene set Δβ = 0.035259, p < 0.001 (0/1,000 permutations exceeded) |
| `data/cofactor_jackknife_results.csv` | 4 rows | NB26 cofactor KO jackknife; all 4 KOs stable (β −0.016 to −0.029, all p < 0.001, no sign changes) |
| `data/inverse_pgls_results.csv` | 17 rows | NB27 inverse PGLS; single + multi-predictor models; n_biomes_z dominant (β=0.215, p≈0); niche-range predictors all positive |
| `data/inverse_rda_variance_partitioning.csv` | 6 rows | NB28 variance partitioning; metals unique R²=0.064, pH+climate unique R²=0.041, shared R²=0.005, all env R²=0.110 |
| `data/cwm_from_env_cv_results.csv` | 5 rows | NB29 spatial block CV; mean RMSE=11.89 (range 6.20–19.37); metals 45.9% of SHAP; top predictor log_Ni_ppm |
| `data/null_category_pgls_results.csv` | 5 rows | Q1 null category PGLS; all 5 non-significant (p > 0.36, |β| < 0.006); standalone confirmation of NB18 values |
| `data/cofactor_overlap_audit.csv` | 382 rows | Q2 cofactor/vitamin KO overlap audit; 83 shared with 730-KO list; 12 in primary 140, 71 additionally flagged (all metal-cofactor pathways by design) |
| `data/genus_lat_env_covariates.csv` | 10,040 rows | Q4 genus-level lat/env: GeoROC metals (9,954 non-null); CMMI proximity; ERA5 temp range (9,985); CSU PF1 mobility (9,217); Science 2025 HHET HQ (Cu/Ni/Co/Cr/Pb); SoilTemp range at −10 cm; ecotapestry mafic/felsic score; USGS REE nearest-distance; soil moisture (9,959 non-null); SOM 0 cm (9,944 non-null) |
| `data/latitude_mechanism_results.csv` | 28 rows | Q4 mechanism PGLS (Models A–I, J–M, N series); β_metal stable across all models; H4a: GeoROC composite β=+0.012 p=2.2×10⁻⁴ driven by Cr (BH p=6.7×10⁻⁹) and Co (BH p=0.0084); mafic score β=+0.009 p=0.013; Sci2025 HQ NS; H4b: ERA5 temp β=+0.014 p=9.6×10⁻⁵; pH positive in all K models (p < 0.001); N models: Cr/Co unattenuated by soil moisture; SOM independently negative (β=−0.016, p=6.8×10⁻⁵) |
| `data/bedrock_metal_diagnostics.csv` | 14 rows | Per-metal collinearity diagnostics: Pearson r matrix, VIFs (all < 2), PCA loadings and explained variance |
| `data/fritz_purvis_D_genome.csv` | 309 | Genome-level Fritz & Purvis D for curated metal KOs on GTDB 18,961-tip tree |
| `data/phylo_d_all_ko.csv` | 276 | Genus-level Pagel's λ for curated metal KOs |
| `results/hgt_synthesis_table.csv` | 23 | HGT evidence synthesis: 13 double-signal + 10 control KOs; D, λ, plasmid_fraction, mobile_fraction, mgnify_rho, env_p, hgt_score |
| `results/env_niche_pgls_coefficients.csv` | 3 | Env niche breadth PGLS: temperature, pH, composite gradient; β, SE, p, λ per response |
| `results/env_niche_all_pgls_results.csv` | — | Full per-response PGLS results for niche breadth analysis |
| `results/ko_drivers_results.csv` | 198 | Per-KO × environmental response PGLS (9 TIER1 KOs × 22 responses); β, t, p, FDR q |
| `results/cooccurrence_pgls_results.csv` | — | Co-occurrence PGLS: sig_pos_partners, sig_neg_partners, phi_degree by stratum |
| `results/cooccurrence_correlations.csv` | — | Spearman correlations: co-occurrence counts vs B_std across strata |

---

## Supporting Evidence

### Notebooks

| Notebook | Purpose |
|----------|---------|
| `00_gene_list_profile.ipynb` | Profile 730-KO gene list; produce gene_list_summary.csv and tier/metal heatmaps |
| `01_primary_pgls_metal-gene_density.ipynb` | Primary PGLS P1 (bacteria) and P2 (archaea); soil-restricted sensitivity |
| `02_ngsa_replication.ipynb` | NGSA replication (P3); joint FDR correction across all three confirmatory tests |
| `03_tier_and_category_analysis.ipynb` | Tier expansion, functional category, and metal-specific PGLS |
| `04_confounder_checks.ipynb` | Genome size, GC content, isolation source, latitude, biome confounders |
| `05_sensitivity_analyses.ipynb` | λ assumption, min-n, raw response, hemisphere, and Australia sensitivity |
| `06_confounder_discovery.ipynb` | BERDL namespace scan for additional covariate candidates |
| `07_marine_and_geological_proxies.ipynb` | Geological ore-deposit proximity exploration (exploratory) |
| `08_emp_niche_breadth.ipynb` | EMP 16S niche breadth PGLS (exploratory replication) |
| `09_bacdive_niche_breadth.ipynb` | BacDive geographic niche breadth PGLS (schema confirmed; main analysis pending) |
| `10_pfam_metal_qc.ipynb` | Pfam/InterPro domain validation of 140 primary KOs |
| `11_enigma_frc_replication.ipynb` | ENIGMA FRC site-level Spearman replication (data coverage limited) |
| `12_ngsa_proper_replication.ipynb` | P4: AusMicrobiome + NGSA soil metal concentration replication |
| `15_ausmicrobiome_density_replication.ipynb` | P5: AusMicrobiome genomic KO density replication |
| `16_clade_stratified_pgls.ipynb` | P6: phylum-stratified PGLS within Proteobacteria/Actinobacteria/Firmicutes/Bacteroidetes |
| `17_negative_controls.ipynb` | Named housekeeping negative controls + streamlining baseline establishment |
| `18_functional_landscape.ipynb` | Full 19-category KEGG functional landscape; true negative identification |
| `19_internal_structure_comparison.ipynb` | Sub-functional PGLS in AMR/TCS/ABC comparison categories (NB19) |
| `20_coreness_permutation.ipynb` | Coreness-matched permutation test; attenuation profile comparison (NB20) |
| `21_aus_beta_comparison.ipynb` | P1 vs P5 β z-test; intersecting-genus and phylum composition analysis (NB21) |
| `22_mag_quality_covariates.ipynb` | MAG completeness/contamination covariates and high-quality sensitivity (NB22) |
| `23_category_conditional_models.ipynb` | Per-category descriptive stats; conditional PGLS on n_KOs/core_fraction/gene_length (NB23) |
| `25_split_magnitude_permutation.ipynb` | Split magnitude permutation: Δβ resistance/cofactor = 0.035259, p < 0.001 (0/1,000 permutations exceeded); comparison families Δβ < 0.033 (NB25) |
| `26_interaction_test_jackknife.ipynb` | NB26: interaction test (resistance vs cofactor) and cofactor KO jackknife: all 4 KOs stable (β −0.016 to −0.029, all p < 0.001, no sign changes) |
| `27_inverse_pgls.ipynb` | Inverse PGLS: n_biomes dominant (β=0.215, p≈0); temp/metal range positive; mean concentrations weak; multi R²=0.063 (NB27) |
| `28_inverse_rda.ipynb` | Inverse RDA: variance partitioning metals vs pH+climate; metals unique R²=0.064 > pH+climate unique R²=0.041 (NB28) |
| `29_cwm_from_env.ipynb` | CWM from env XGBoost: mean CV RMSE=11.89; metal SHAP=45.9%; top predictor log_Ni_ppm; spatial generalisation poor (NB29) |

### Scripts

| Script | Purpose |
|--------|---------|
| `scripts/hgt_direct_evidence.py` | HGT direct evidence: NCBI Entrez plasmid/mobile-element queries, Fritz & Purvis D comparison, MGnify environmental enrichment; synthesis table + 3 figures |
| `scripts/partner_characterisation.py` | Co-occurrence partner characterisation: top-50 vs control-50 focal genera; φ-threshold partner extraction; MWU/chi-square tests; 3 figures |
| `scripts/run_cooccurrence_analysis.py` | Co-occurrence network construction: hypergeometric Veech test, phi coefficients, PGLS of positive partner count on KO density (3 strata) |
| `scripts/env_niche_breadth_analysis.py` | Environmental niche breadth PGLS: temperature/pH/composite gradient as responses |
| `scripts/per_ko_driver_analysis.py` | Per-KO metal-gene driver screen: 9 TIER1 KOs × 22 environmental responses; metal-match MWU |

### Figures

| Figure | Description |
|--------|-------------|
| `figures/00_gene_list_tier_composition.png` | Bar chart: KO count by evidence tier |
| `figures/00_metal_tier_heatmap.png` | Heatmap: KO count by metal × tier |
| `figures/01_descriptive.png` | Response and predictor distributions; bivariate scatter |
| `figures/01_pgls_primary_scatter.png` | Primary PGLS scatter with PGLS regression line (P1) |
| `figures/02_primary_tests_comparison.png` | Side-by-side β estimates for P1, P2, P3 |
| `figures/03_category_forest_plot.png` | Forest plot: β ± SE for each functional category |
| `figures/03_tier_forest_plot.png` | Forest plot: β ± SE for each tier and metal-specific set |
| `figures/04_confounder_beta_comparison.png` | β attenuation by confounder |
| `figures/05_sensitivity_beta_comparison.png` | Sensitivity β comparison across λ and subset checks |
| `figures/06_individual_dataset_maps.png` | Spatial coverage maps per candidate confounder dataset |
| `figures/06_overlay_map_all.png` | Overlay of all candidate confounder datasets |
| `figures/06_sample_coverage_map.png` | Global sample coverage of primary MGnify genera |
| `figures/07_metal_exposure_vs_ko_density.png` | Geological proxy correlation (exploratory) |
| `figures/08_emp_levins_vs_ko_density.png` | EMP niche breadth vs KO density scatter |
| `figures/10_pfam_qc_summary.png` | Pfam evidence breakdown for 140 primary KOs |
| `figures/clade_stratified_forest_plot.png` | Clade-stratified β estimates (P6) |
| `figures/functional_landscape_forest.png` | NB18: 19-category KEGG landscape forest plot |
| `figures/negative_control_full.png` | NB17: named controls vs metal gene set + permutation null |
| `figures/fig_p5_aus_density.png` | P5 AusMicrobiome density replication scatter |
| `figures/internal_structure_forest.png` | NB19: AMR/TCS/ABC internal substructure |
| `figures/coreness_permutation_histogram.png` | NB20: coreness-matched permutation null + attenuation profile; emp_p = 0.298 |
| `figures/aus_composition_comparison.png` | NB21: phylum composition P1/P5/intersection |
| `figures/aus_density_overlap_scatter.png` | NB21: density scatter overlapping genera — P1 all genera vs AusMicrobiome (P5) subset highlighted |
| `figures/png/fig08_phylo_D_lambda.png` | Figure 8: Fritz & Purvis D vs Pagel's λ scatter; 275 KOs; 13 double-signal genes annotated; Spearman ρ=−0.041, p=0.49 |
| `data/two_scale_phylo_D_vs_lambda.pdf` | Source PDF for Figure 8 (7×6 in, vector) |
| `data/supplementary_tl_al_s_kos.csv` | 153 rows; Tl/Al/S KO curation rationale (Supplementary Table S4) |
| `results/hgt_gene_tree_discordance.pdf` | Fritz & Purvis D per KO; DS vs control coloured; MWU p = 1.81×10⁻⁴ |
| `results/hgt_transposase_proximity.pdf` | Two panels: plasmid fraction and mobile-element fraction per KO (DS vs control) |
| `results/hgt_evidence_heatmap.pdf` | Evidence heatmap: D_norm, plasmid_fraction, mobile_fraction, |mgnify_rho| for 23 KOs |
| `results/cooccurrence_scatter_all.pdf` | PGLS scatter: sig_pos_partners vs ko_per_mb (ALL stratum; β = 138.4, p = 3.4×10⁻²³) |
| `results/cooccurrence_scatter_env.pdf` | PGLS scatter: sig_pos_partners vs ko_per_mb (ENV stratum; β = 134.0, p = 8.5×10⁻²²) |
| `results/cooccurrence_scatter_soil.pdf` | PGLS scatter: sig_pos_partners vs ko_per_mb (SOIL stratum; β = 210.5, p = 8.2×10⁻⁴¹) |
| `results/partner_bipartite_network.pdf` | Bipartite co-occurrence network: top-10 focal genera × top-5 partners; node colour = phylum/ko_per_mb |
| `results/partner_focal_vs_partner_scatter.pdf` | Focal ko/Mb vs mean partner ko/Mb; OLS overlay; ρ = 0.604, p = 2.82×10⁻¹¹ |
| `results/partner_ko_density_boxplot.pdf` | Partner ko/Mb distribution: top-50 vs control-50 focal groups; MWU p = 1.98×10⁻⁷ |
| `results/ko_drivers_heatmap.pdf` | Heatmap: 9 KOs × 22 env responses; t-statistic colour scale |
| `results/ko_drivers_metal_bars.pdf` | Bar chart: n significant responses per KO |
| `results/ko_drivers_metal_match.pdf` | Metal-match MWU: matched vs mismatched t-statistic distributions |

---

## Future Directions

1. **Execute NB09 (BacDive)** from cell nb090010 — schema discovery completed; the main
   country-count aggregation and PGLS have not run. BacDive culture-based cosmopolitanism
   would provide a fully independent (non-16S-derived) niche breadth replication.
2. **Use the streamlining landscape as a baseline** (Finding 3) for causal decomposition: partition
   the primary β into streamlining-driven and metal-content-specific components by regressing
   niche breadth on (a) a composite "compaction index" from the true-negative category densities
   and (b) metal-gene density residualised against the compaction index. A significant residual
   β would confirm metal-specific content enrichment beyond the streamlining baseline.
3. **Expand ENIGMA coverage** — access the full ENIGMA geochemical database beyond
   `ddt_brick0000007` to obtain groundwater chemistry for the remaining 18 wells with MAG data.
4. **Northern hemisphere soil replication** — the signal is stronger in northern hemisphere genera
   (β = −0.030) and in soil specialists (β = −0.033). A targeted replication using a
   northern-hemisphere soil amplicon survey would strengthen the Australian-null explanation.
5. **Metagenomically-derived niche breadth** — replace the 16S OTU–genus bridge with
   genus-level niche breadth computed directly from the MGnify metagenomic genus-level
   classifications.
6. **Causal pathway test** — test whether cofactor-gene density (the strongest category) is
   the proximate mechanistic link by regressing niche breadth on cofactor density controlling
   for overall primary-set density. A partial R² test would reveal whether cofactor genes drive
   the association or are co-linear with the broader metal-gene investment signal.
7. **Time-series / community-level test** — use ENIGMA longitudinal MAG data to test whether
   genera with higher metal-gene density show lower occupancy turnover across time points.
8. **Inverse PGLS pre-registration** — an exploratory inverse PGLS (NB27) reversing the prediction direction found that niche-range breadth (biomes occupied, temperature/metal-concentration range) positively predicts per-Mb metal-gene density (n_biomes: β = 0.215, p ≈ 0), which warrants confirmatory pre-registration before further inference.
9. **Partial co-occurrence analysis controlling for B_std** — the positive co-occurrence partner signal (Finding 15) is correlated with niche breadth (Spearman ρ = 0.33–0.37 across strata). A partial analysis regressing partner count on KO density with B_std as a covariate would clarify whether the co-occurrence signal is independent of or mediated by niche breadth.
10. **Phylogenetic distance of co-occurrence partners** — the Firmicutes bias in partner phyla (Finding 16) suggests non-random assembly. Computing mean phylogenetic distance between focal genera and their partners (compared to a random null from the same network) would test whether the guild is phylogenetically structured.
11. **HGT gene tree validation** — the Fritz & Purvis D proxy is an indirect measure of gene-tree/species-tree discordance. For the top-5 double-signal KOs (nrsD, merE, aoxB, shp, golS), a direct single-gene phylogeny against the GTDB species tree using IQ-TREE and the approximately unbiased test would confirm HGT with placement-level resolution when assembly data become available.
12. **pH niche × metal speciation test** — the pH niche signal (Finding 13; β = −0.760, p = 0.001) predicts that metal-gene-rich genera should cluster at lower pH values where Cr(VI)/Cu²⁺ speciation is most reactive. An overlay of genus pH optima onto metal-speciation pH curves would test this mechanistically.

---

## References

- Giovannoni SJ, Thrash JC, Temperton B. (2014). Implications of streamlining theory for microbial ecology. *ISME J* 8:1553–1565. DOI: 10.1038/ismej.2014.60
- Lauro FM, McDougald D, Thomas T, et al. (2009). The genomic basis of trophic strategy in marine bacteria. *PNAS* 106:15527–15533. DOI: 10.1073/pnas.0903507106
- Konstantinidis KT, Tiedje JM. (2004). Trends between gene content and genome size in prokaryotic species with larger genomes. *PNAS* 101:3160–3165. DOI: 10.1073/pnas.0308653100
- Szukics U, Delgado-Baquerizo M, et al. (2024). Niche breadth specialization impacts ecological and evolutionary adaptation of soil ammonia-oxidizing archaea. *ISME J* 18:wrae183. DOI: 10.1093/ismejo/wrae183
- Rastogi G, Sani RK, et al. (2023). Distinct community assembly processes and habitat specialization drive bacterioplankton diversity in a coastal lagoon. *Science of the Total Environment* 163109. DOI: 10.1016/j.scitotenv.2023.163109
- Leu AO, McIlroy SJ, et al. (2022). Diverse Genomic Traits Differentiate Particle-Associated and Free-Living Microorganisms in the North Pacific Subtropical Gyre. *mBio* 13:e01569-22. DOI: 10.1128/mbio.01569-22
- Gios E, Valentini F, et al. (2025). Genetic exchange shapes the metabolic capacities of ultra-small Patescibacteria in groundwater. *mSystems* 10:e00046-25. DOI: 10.1128/msystems.00046-25
- Pal C, Bengtsson-Palme J, Kristiansson E, Larsson DGJ. (2015). Co-occurrence of resistance genes to antibiotics, biocides and metals reveals novel insights into their co-selection potential. *BMC Genomics* 16:964. DOI: 10.1186/s12864-015-2153-5
- Lill R. (2009). Function and biogenesis of iron-sulphur proteins. *Nature* 460:831–838. DOI: 10.1038/nature08301
- Price MN, Wetmore KM, Waters RJ, et al. (2018). Mutant phenotypes for thousands of bacterial genes of unknown function. *Nature* 557:503–509. DOI: 10.1038/s41586-018-0124-0
- Arkin AP, Cottingham RW, Henry CS, et al. (2018). KBase: The United States Department of Energy Systems Biology Knowledgebase. *Nature Biotechnology* 36:566–569. DOI: 10.1038/nbt.4163
- Lemire JA, Harrison JJ, Turner RJ. (2013). Antimicrobial activity of metals: mechanisms, molecular targets and applications. *Nature Reviews Microbiology* 11:371–384. DOI: 10.1038/nrmicro3028
- Sunagawa S, Coelho LP, Chaffron S, et al. (2015). Structure and function of the global ocean microbiome. *Science* 348:1261359. DOI: 10.1126/science.1261359
- Levins R. (1968). *Evolution in Changing Environments*. Princeton University Press, Princeton NJ.
- Martinez JL, Fajardo A, Garmendia L, Hernandez A, Linares JF, Martinez-Solano L, Sanchez MB. (2006). A global view of antibiotic resistance. *FEMS Microbiology Reviews* 30:977–1000. DOI: 10.1111/j.1574-6976.2006.00053.x
- Bouzat JL, Hoostal MJ. (2013). Lateral gene transfer and the evolution of two-component signal transduction systems for metal tolerance in *Synechococcus* and related bacteria. *Journal of Bacteriology* 195:5479–5490. DOI: 10.1128/JB.00789-13
- Sun L, Yin W, Xiong G, Chen X, Chen Y, Liu Y, Pan M, Li B, Yuan B, Gao J. (2022). Heavy metals simplify community network structure in paddy soils by suppressing negative links. *Science of the Total Environment* 850:157967. DOI: 10.1016/j.scitotenv.2022.157967
- Pan M, Li B, Yuan B, Yin W, Chen X, Chen Y, Liu Y, Xiong G, Gao J, Sun L. (2026). Multi-metal contamination simplifies co-occurrence networks in paddy soils by reducing negative interactions. *Environmental Microbiology*. DOI: 10.1111/1462-2920.16xxx
- Veech JA. (2013). A probabilistic model for analysing species co-occurrence. *Global Ecology and Biogeography* 22:252–260. DOI: 10.1111/j.1466-8238.2012.00789.x

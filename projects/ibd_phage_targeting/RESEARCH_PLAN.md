# Research Plan: Metagenome-Prioritized Phage Cocktails for Crohn's Disease and IBD

## Research Question

Which bacterial pathobionts are enriched, ubiquitous, and non-protective in IBD / UC / Crohn's disease patients — considered both across indications and within distinct patient subgroups defined by demographics, severity, native-microbiome structure, and treatment history — and of those, which are tractable phage-therapy targets given available or characterizable phages, target-strain evolutionary escape routes, and ecological consequences of removal?

## Hypothesis Framework

Five coupled pillars. Each pillar's hypotheses are falsifiable, state the statistical test, and specify what "disproved" looks like.

### Pillar 1 — Patient stratification

**H1a**: Unsupervised clustering on baseline microbiome + metabolome + pathway potential of the pooled public-cohort data yields **≥ 3 reproducible IBD ecotypes** that replicate across held-out cohorts. *Test*: Dirichlet Multinomial Mixture (DMM) on taxa, topic modeling on pathways, MOFA+ on the multi-omics join. Ecotype calls retained only if stable under all three methods and under bootstrap resampling (≥ 80 % per-sample consistency). *Disproved if*: no K (number of ecotypes) gives perplexity / BIC stabilization, or inter-method agreement < 50 %, or held-out replication Rand index < 0.4.

**H1b**: UC Davis patients distribute across (not concentrate in) the reference ecotypes. *Test*: project UC Davis taxon profiles onto the reference embedding, count occupancy per ecotype, test against the null of single-ecotype collapse (χ² or exact test). *Disproved if*: ≥ 80 % of UC Davis patients land in one ecotype.

**H1c**: Ecotype membership can be predicted from **clinical covariates alone** (Montreal classification, calprotectin, CRP, medication class, age, sex, smoking) at classification AUC ≥ 0.70. Meaningful because a clinical classifier would allow ecotype assignment before metagenomics is available. *Test*: multinomial logistic regression or gradient-boosted classifier on public-cohort clinical metadata with ecotype label as target; leave-one-cohort-out CV. *Disproved if*: no clinical signature predicts ecotype above chance.

### Pillar 2 — Pathobiont identification (within-ecotype)

**H2a**: A minority of the ~266 CD-enriched species (per the preliminary DA) are actionable pathobionts under a stricter rubric applied within ecotype. *Test*: compositional-aware DA (ANCOM-BC + MaAsLin2 + LinDA, consensus) within each ecotype, then Tier-A scoring (see "Criteria" below). Actionable count defined as those passing ≥ 5 of the 6 Tier-A criteria. *Disproved if*: passing-species lists do not overlap across the three DA methods (< 50 % overlap) or no species passes ≥ 5 criteria.

**H2b**: Target sets differ between UC and CD, and within CD by Montreal-location subtype (ileal L1 vs colonic L2 vs ileocolonic L3). *Test*: Jaccard overlap of top-20 within-ecotype Tier-A candidates between UC and CD, and between L1 / L2 / L3 strata of CD. *Disproved if*: Jaccard > 0.7 (target sets are nearly identical) — which would mean stratification gives no clinical benefit for targeting.

**H2c**: Within-ecotype compositional-aware DA *fails to reproduce protective species as CD-enriched*. Specifically: *C. scindens*, *F. prausnitzii*, *A. muciniphila*, *E. rectale*, *Roseburia intestinalis*, *Lachnospira eligens* should NOT show up as CD-enriched when the analysis is done correctly. *C. scindens* is the motivating example (preliminary report called it log₂FC +2.67 in pooled analysis despite 79 % prevalence in healthy individuals), but the same sanity-check battery applies to the whole protective-species list. *Test*: direct check against the preliminary pooled DA. *Disproved if*: any canonical protective species remains CD-enriched after stratification and compositional correction — which would force us to question the stratification itself.

**H2d**: Pathobiont co-occurrence modules (SparCC / SpiecEasi per ecotype) contain ≥ 2 Tier-A candidates each. This matters because single-target cocktails may fail if the module re-equilibrates around another hub. *Test*: network inference per ecotype + module detection + intersection with Tier-A candidate list. *Disproved if*: modules contain ≤ 1 Tier-A hub on average — suggesting pathobionts are ecologically independent and monovalent cocktails may suffice.

### Pillar 3 — Functional drivers (mechanism)

> **Pillar 3 Scope Refresh (v1.7 — post-adversarial-review).** Revised after the v1.6 plan's adversarial review identified 4 critical + 10 important issues structurally analogous to NB04's failure pattern.
>
> **Confound-free design (per N12).** The primary Pillar 3 contrast is **within-IBD-substudy CD-vs-nonIBD meta-analysis** — never pooled CD-vs-HC. Substudy meta-viability is **modality-specific** and must be re-verified for each new fact table; do NOT inherit NB04e's 4-substudy taxonomic-data viability blindly. NB07a §0 includes an explicit substudy × diagnosis crosstab on `fact_pathway_abundance` that is required before pathway DA is computed. Same rule for `fact_metabolomics`, `fact_serology`, `fact_strain_competition`. Verified pathway-modality substudy viability (already done in adversarial review): HallAB_2017 (CD=88, nonIBD=72), IjazUZ_2017 (56/38), NielsenHB_2014 (21/248), LiJ_2014 (76/10 — boundary, sensitivity-test only), VilaAV_2018 (216/0 — **excluded; CD-only**, has UC-vs-CD signal but no within-substudy CD-vs-nonIBD). Effective pathway-meta is **3 robust + 1 boundary**, not "4 meta-viable" as v1.6 implied.
>
> **Tier-A inputs (pre-registered per test, per I1 fix).** Three explicit input species sets:
>
> - **Tier-A core** = the **6 NB05-actionable** species (`actionable=True` in `data/nb05_tier_a_scored.tsv`): *H. hathewayi*, *M. gnavus*, *E. coli*, *E. lenta*, *F. plautii*, *E. bolteae*. Used for primary H3 tests.
> - **Tier-A extended** = the 6 actionable **plus 9 Tier-B** (NB05 score 2.2–2.4): adds *E. asparagiformis*, *S. salivarius*, *E. citroniae*, *E. clostridioformis*, *B. coccoides*, *V. atypica*, *S. parasanguinis*, *A. oris*, *V. parvula*. Used as sensitivity check, FDR-corrected separately.
> - **NB06 module-anchor commensals** = the top-3-degree non-Tier-A hubs in each pathobiont module (taken from `data/nb06_module_hubs.tsv`; see H3a-new for the actual lists per ecotype × CD/all subnet — note NB07c uses the **E3_CD module hubs** for CD-specific cross-feeding, not E3_all).
>
> **Dual-basis ecotype reporting (per N14, revised — see C2 + C8 in adversarial review).** N14 was structurally broken in v1.6: running pathway-DA stratified by pathway-feature ecotype is the same feature-leakage trap N8 prohibits, so reporting that arm next to the taxon-ecotype arm "for consistency" formalizes a leakage-poisoned defense. **In v1.7, N14 is restricted: when the test feature basis equals the cluster feature basis, the corresponding arm is explicitly LEAKAGE-POISONED and MUST be flagged as such, not reported as supporting evidence.** The within-IBD-substudy CD-vs-nonIBD contrast (N12) is the primary disjoint-axis test. Within-ecotype meta is a *secondary* check stratified only by the disjoint basis (taxonomic ecotype for pathway DA; taxonomic ecotype for metabolite DA). The pathway-feature-ecotype arm and metabolite-feature-ecotype arm are dropped from N14 reporting; they remain available as **internal consistency checks** but cannot serve as evidence for or against H3 claims. Additionally, N14 only applies to ecotypes with viable cross-basis sample size — drop E0 and E2 from N14 reporting given NB04g pathway-ecotype agreement of 0% (E0) and 47% (E2) on tiny n.

**H3a (v1.7)**: Disease-associated pathway enrichment compresses to a **small number of biochemical themes** (bile-acid 7α-dehydroxylation loss, mucin degradation, sulfidogenesis, TMA/TMAO production, AA decarboxylation, ethanolamine utilization, polyamine/urease — full a-priori list in §Expected outcomes), each attributable to a specific Tier-A-core species set (the 6 NB05-actionable species).

*Test*: within-IBD-substudy CD-vs-nonIBD meta-analysis on `fact_pathway_abundance` (CMD_IBD substudies HallAB_2017, IjazUZ_2017, NielsenHB_2014; LiJ_2014 included as sensitivity test only — nonIBD n=10 boundary). Then pathway → pathobiont attribution via per-substudy Spearman ρ between pathway relative abundance and Tier-A-core species abundance, then ρ-meta across substudies. Plus HMP2 single-cohort replication (1,623 pathway samples; within-cohort CD-vs-nonIBD).

*Three falsifiability clauses, each with explicit null distribution (per C7 fix)*:

(a) **Pathway count under permutation null.** ≥ 10 MetaCyc pathways pass FDR < 0.10 with pooled-effect > 0.5. Null: 1000-permutation null on the same dataset, where diagnosis labels are shuffled within each substudy independently. Report observed count, null mean ± SD, and empirical p-value. *Disproved if* observed count is within the null distribution at p > 0.10 (i.e., enrichment is not detectable above chance given multiple testing on ~400 prevalence-filtered MetaCyc pathways).

(b) **Category coherence under random-allocation null.** ≥ 60% of passing pathways concentrate in ≤ 3 of the 7 a-priori MetaCyc categories. Null: random allocation of N passing pathways into the 7-category scheme proportional to per-category pathway counts in the prevalence-filtered MetaCyc corpus; 1000 draws. Report observed concentration, null distribution, and empirical p. *Disproved if* observed concentration is within null at p > 0.10 (would mean any 10 random pathways could meet "≤ 3 categories" by chance).

(c) **Pathway–pathobiont attribution under permutation null.** ≥ 1 pathway × Tier-A-core-species pair has within-substudy-meta |Spearman ρ| > 0.4 with permutation-null empirical p < 0.05. Null: 200-permutation null where pathway-abundance values are permuted across samples within substudy (pathway → pathobiont attribution should not survive sample-permutation). Mirror NB04b §4 protocol.

Sensitivity test on the 9 Tier-B species set (per I1 + I6 fix): repeat (c) with FDR-corrected on Tier-B separately, **flag for review but does NOT influence H3a verdict**. Tier-A-core is the load-bearing test.

Power calibration (per I5 fix): with n_pooled ≈ 165 CD + 320 nonIBD across 3 robust substudies, Spearman |ρ| = 0.4 detection at α = 0.05 (post-FDR) has power ~0.95 per pair tested; Fisher-z effect-size CI: ρ = 0.4 ± 0.07 (95%). Pathway-DA effect > 0.5 CLR detection has power > 0.99 at this n.

**H3a-new (v1.7) — Module-anchor commensal ↔ pathobiont metabolic coupling (NB06 follow-up; renamed per C1 fix).**

The NB06 pathobiont modules in each subnet (E1_all, E1_CD, E3_all, E3_CD) include high-degree non-Tier-A "anchor" commensals that co-occur with the NB05-actionable pathobionts. The anchors have **heterogeneous fermentation modes** — they are not all butyrate producers, contra v1.6:

- **E1_all module 1 hubs** (top-3 by degree): *Firmicutes bacterium CAG 110* (uncharacterized MAG), *Collinsella massiliensis* (Coriobacteriia, bile-acid deconjugation), *Phascolarctobacterium sp CAG 266* (succinate → propionate)
- **E1_CD module 0 hubs**: same three (consistent with E1_all)
- **E3_all module 1 hubs**: *Butyricicoccus pullicaecorum* (butyrate), *Anaerostipes caccae* (butyrate), *Lactococcus lactis* (lactate)
- **E3_CD module 1 hubs**: from `nb06_module_hubs.tsv` row for E3_CD module 1 — pre-register the actual top-3 in NB07c §0 (NOT inheriting E3_all's hubs per X4 fix)

Hypothesis: ≥ 1 anchor commensal × Tier-A-core pathobiont pair shows complementary pathway abundance — i.e., one species' high abundance covaries with the other species' high abundance specifically along a metabolic exchange axis (substrate-producer / consumer). The hypothesis does **NOT** assume butyrate cross-feeding; the metabolic-coupling axis is left open and pre-specified per anchor:

| Anchor | Predicted producer pathway | Predicted consumer pathway | Co-vary |
|---|---|---|---|
| *B. pullicaecorum* (butyrate) | mucin-degradation / fucose / GAG breakdown by *M. gnavus* or *H. hathewayi* | butyrate biosynthesis (BCD operon) | + |
| *A. caccae* (butyrate) | bile-acid deconjugation by *C. massiliensis* (E1) or unconjugated-bile-acid release by *E. lenta* | butyrate biosynthesis | + |
| *L. lactis* (lactate / dairy origin) | lactose / galactose utilization | lactate → propionate / butyrate via cross-species feeding | + |
| *Phascolarctobacterium* (succinate→propionate) | succinate-producing pathways in *E. bolteae* or *M. gnavus* | succinate utilization → propionate | + |
| *C. massiliensis* (bile-acid deconjugation) | bile-acid 7α-dehydroxylation by *C. scindens* / *F. plautii* | bile-salt hydrolase | + |
| *Firmicutes CAG 110* (uncharacterized) | not pre-specified — **null hypothesis only**, no positive prediction | n/a | n/a |

*Test*: per anchor-pathobiont pair, within-IBD-substudy meta of Spearman ρ on (producer-pathway abundance × consumer-pathway abundance) AND (anchor species abundance × pathobiont species abundance) within E1 / E3. *Predicted-pair support*: |ρ| > 0.3 on both axes with permutation-null p < 0.05. *Mechanistic support* requires both axes positive. *Cross-feeding alternative* (vs shared-environmental-preference) distinguished by metabolite-level corroboration in NB09c (bile-acid + SCFA targeted assays — test whether the anchor commensal's fermentation product correlates with the pathobiont's substrate consumption signature in the same samples).

*Disproved if*: no anchor-pathobiont pair (5 with positive predictions) shows |ρ| on both axes > 0.3 at permutation p < 0.05 in ≥ 2 of 3 robust substudies; or all positive pairs lack metabolite-level corroboration in NB09c (rules out cross-feeding interpretation in favor of shared-environmental-preference null).

**H3b (v1.7) — restricted to Kumbhari cohort per C5 fix**:

The v1.6 framing of H3b was structurally broken: the Kumbhari strain-adaptation gene calls live in `ref_kumbhari_s7_gene_strain_inference` (Kumbhari/LSS-PRISM cohort), but cMD samples have only species-level abundance — no per-sample strain-level genotyping. Operationalizing strain-adaptation features as "species has gene X" → species-level proxy collapses the test by construction (AUC(strain+species) − AUC(species) ≈ 0 trivially, not because strain features are uninformative but because they ARE species features in disguise).

**v1.7 H3b is restricted to the Kumbhari cohort itself**: the LSS-PRISM samples in `fact_strain_competition` (15,520 sample × strain rows, with per-sample disease-strain frequencies) are the only data where strain-level resolution is available within this project's data scope. The cross-cohort generalization to cMD is dropped.

*Test*: within Kumbhari/LSS-PRISM samples (n = 15,520 strain × sample observations across `fact_strain_competition`), correlate per-strain disease-frequency-dominance × calprotectin AND per-strain disease-frequency × IBD-adapted-gene-content. Per-species: train GBM predicting `disease_strain_freq > health_strain_freq` from gene-content features in `ref_kumbhari_s7_gene_strain_inference`. Stratify by Kumbhari sub-cohort (PRISM, LSS-PRISM, MUSC) where applicable.

*Disproved if*: gene-content GBM AUC < 0.65 on held-out Kumbhari sub-cohort (i.e., strain-adaptation genes don't discriminate disease-dominant from health-dominant strains within the Kumbhari data itself), OR feature importance is dominated by housekeeping genes (no biologically interpretable adaptation signal).

**Cross-cohort sensitivity test (acknowledged-weak per C5)**: as a sensitivity check only — NOT a load-bearing test — operationalize strain-adaptation as "species has gene X" → species-level binary feature joined to cMD species abundance via prevalence-weighting: `feature_X(sample) = sum over strains s of species: P(s carries X) × abundance(species, sample) / Σ abundance`. Add this feature alongside species abundance in a CD-vs-nonIBD GBM on the within-IBD-substudy 4-cohort set, ROC-compare to species-only baseline. Acknowledge in §Limitations that this is species-resolved, not strain-resolved, and the AUC delta is bounded by (gene-prevalence × abundance-correlation) — small effect size expected even if biology is real.

**H3c (refined)**: BGC-encoded inflammatory mediators (NRPS / RiPP clusters from `ref_bgc_catalog` and the 5,157 CB-ORFs in `ref_cborf_enrichment`) localize to a minority of Tier-A pathobionts and show CD-vs-nonIBD enrichment beyond what species-level abundance captures. *Test*: for each NB05-actionable species, test whether species × BGC-interaction term is significant in the within-IBD-substudy CD-vs-nonIBD regression. *Disproved if*: interaction terms are not significant (FDR < 0.10) for > half of actionable species, OR the BGC-CD-enrichment is fully explained by species abundance (interaction coefficients shrink to < 0.2 after species-abundance adjustment).

**H3d (v1.7) — split into H3d-clust and H3d-DA per X3 fix**:

The v1.6 framing of H3d conflated two distinct tests: (a) clustering on metabolite features and comparing the resulting clusters to taxonomic ecotypes, vs (b) per-metabolite differential abundance within ecotype-stratified samples. v1.7 separates them.

**H3d-clust — Metabolomic-feature stratification stability**: Cluster samples on metabolite-feature space (non-negative matrix factorization on `fact_metabolomics`; HMP2 + FRANZOSA + DAVE = 839 samples, multi-platform — see Limitations §metabolomics platform variation for required normalization). Compute LOSO stability of resulting K=4 clustering using the NB04f protocol — hold out each cohort (HMP2 / FRANZOSA / DAVE) in turn, refit, project held-out, ARI vs full-fit. *Disproved if*: metabolite-clustering LOSO ARI < 0.20 (does not exceed taxonomic-ecotype LOSO ARI 0.113 by a meaningful margin); marginal pass goes in §Limitations. Note: metabolomics-clustering LOSO across **3 cohorts** (HMP2, FRANZOSA, DAVE) tests cross-cohort cross-platform stability — a stronger test than NB04f's within-cMD LOSO.

**H3d-DA — Metabolite × ecotype × diagnosis test**: Within HMP2 only (largest single-cohort metabolomics: 385 samples per the actual mart count; multi-platform CMD metabolomics is bridge-corroboration, not primary). For each metabolite (top ~300 by HMDB-annotated variance), test CD-vs-nonIBD effect within HMP2-projected ecotype (taxonomic ecotype from NB04h projection — 80% projection-confidence threshold; ambiguous-projection samples flagged separately, per I8 fix). *Disproved if*: < 5 metabolites pass FDR < 0.10 with effect > 0.5 CLR per ecotype, AND no metabolite-class coherence (analogous to H3a category-coherence null).

**Important constraint per C8 fix**: H3d-clust is feature-leakage-prone if pursued under N14 dual-basis (metabolite-feature ecotype × metabolite-DA = same axis). N14 is restricted: do NOT report metabolite-DA stratified by metabolite-feature ecotype. Stratify only by taxonomic ecotype (disjoint axis).

**H3e (v1.7) — HMP2 only, n = 67 participants across 3 sites per C6 fix**:

Sample-size reality (verified): `fact_serology` has **67 participants** (32 CD, 14 UC, 21 nonIBD) across 3 sites — CCHMC (Denson lab, n=33 participants at most), Harvard, Emory. Approximately 3 sera per participant on average (NOT the 130-subject HMP2 cohort × 10–12 samples figure that v1.6 implied). 12 assay types in the table; ~6 unique serology axes after deduping EU + Pos. forms (per I9 fix).

*Test*: per Tier-A-core species × per unique serology axis (6 × 6 = 36 tests), partial correlation in HMP2 samples with serology (per-participant mean across longitudinal sera), controlling for **(a) site** (CCHMC vs Harvard vs Emory — batch-effect axis missed in v1.6), **(b) disease status** (CD / UC / nonIBD), **(c) participant taxonomic ecotype** (from NB04h projection). Use per-participant data (n = 67), not per-sample (which is pseudo-replicated).

For longitudinal participants with ≥ 4 serology measurements, sensitivity test via mixed-effects regression with participant random intercept; not the primary test (sample size constrains effective n).

Power calibration (per I5 fix): Fisher-z partial-correlation power at n = 67, α = 0.05/36 (Bonferroni for the 36 tests; FDR also reported): minimum-detectable |r| ~ 0.39 at power 0.80. Pre-registered effect-size threshold |r| > 0.40, not 0.25 (which had power < 0.30 at this n).

*Disproved if*: (a) no Tier-A-core × serology pair has partial |r| > 0.40 with site- + disease- + ecotype-adjusted permutation-null p < 0.05, OR (b) all significant correlations attenuate to |r| < 0.20 after disease-state adjustment alone (no pathobiont-specific signal beyond generic dysbiosis). Tier-B sensitivity-test is exploratory only, not in the primary verdict.

Single-cohort caveat — **no cross-cohort replication path for H3e in current data**; this is a structural limitation, flagged in §Limitations.

### Pillar 4 — Phage targetability

**H4a**: Top-ranked Tier-A pathobionts have **≥ 1 characterized strictly lytic phage** with published host range that together cover ≥ 80 % of the strain diversity in the affected ecotype. *Test*: construct pathobiont-strain × candidate-phage coverage matrix from `phagefoundry_strain_modelling`, PhageFoundry host-specific databases, and external sources (INPHARED / Millard, IMG/VR, NCBI Phage RefSeq, PhagesDB). *Disproved if*: fewer than half of Tier-A targets have qualifying phages, or combined coverage per ecotype < 50 %.

**H4b**: Phage-resistance escape cost varies by receptor class. Receptors in essential transporter / LPS-core / highly-conserved surface-protein systems produce more durable sensitivity than O-antigen-variable receptors. *Test*: where fitness data exists (`kescience_fitnessbrowser` for E. coli, Klebsiella, Acinetobacter etc.), quantify the fitness cost of disrupting the phage receptor or a proxy gene. Classify targets by "escape cost" tier. Cross-check against pangenome essentiality inference (`kbase_ke_pangenome`). *Disproved if*: receptor class does not predict resistance-escape cost (receptor class R² < 0.15 against fitness cost).

**H4c**: Target strains have **CRISPR-Cas content and spacer repertoires** that inform which candidate phages are already immune-targeted. *Test*: CRISPRCasFinder or equivalent on pangenome-linked target strains; spacer-vs-candidate-phage-genome match. Flag target strains with ≥ 1 spacer matching a candidate phage cocktail. *Disproved if*: no target strain shows meaningful spacer content against candidate phages — would simplify cocktail design but is improbable.

**H4d**: Endogenous phageome composition (from `fact_viromics` + `ref_viromics_summary_by_disease`) differs by ecotype and may constrain exogenous phage cocktail deployment via prophage-mediated superinfection exclusion. *Test*: stratified analysis of the 260 viruses in `ref_viromics_summary_by_disease` per ecotype; flag cocktail-candidate-phages whose close relatives are already endemic. *Disproved if*: no ecotype-specific endogenous phageome signature — simplifies but does not block the project.

### Pillar 5 — UC Davis deep dive

**H5a**: UC Davis patients cover a **subset** of reference ecotypes, not all of them. *Test*: projection + occupancy analysis (H1b). *Disproved if*: UC Davis covers all ecotypes equally well (would mean the cohort is representative rather than enriched).

**H5b**: UC Davis severity (fecal calprotectin, CRP, Montreal behavior B2/B3) correlates with pathobiont burden **within ecotype**. *Test*: ecotype-stratified regression of calprotectin against Tier-A-species abundance. *Disproved if*: no ecotype-specific severity signature — pooled correlations may be driven by dysbiosis-score alone.

**H5c**: For each UC Davis patient, a named top-N pathobiont list and a candidate phage cocktail (with Tier-B / C flags) can be produced. Deliverable: patient-level dossier table. *Disproved if*: ≥ 30 % of UC Davis patients have no viable phage-cocktail candidate under the rubric — which would itself be a useful negative result flagging clinical-trial design.

**H5d**: For the two UC Davis patients with longitudinal samples (6967 / 6967-1; 1460 / 1460-1), pathobiont identity is stable within-patient. This informs dosing schedule. *Test*: compare within-patient top-pathobiont ranking at the two timepoints. *Disproved if*: top pathobionts flip between timepoints — implying cocktails may need dynamic adjustment.

## Criteria — the four-tier rubric

### Tier A — Biological target suitability (data-driven from CrohnsPhage + BERDL)

| # | Criterion | Operationalization | Source |
|---|---|---|---|
| A1 | Prevalence within affected ecotype | ≥ 50 % of patients in the ecotype carry the species above detection threshold | `fact_taxon_abundance` / `fact_strain_frequency_wide` stratified by ecotype |
| A2 | Effect size within ecotype | Compositional-aware DA log₂FC > 1.0 AND FDR < 0.05 AND effect size (Cliff's δ or Cohen's h) > 0.2 | ANCOM-BC / MaAsLin2 / LinDA consensus |
| A3 | Mechanistic link to inflammation | ≥ 2 independent literature citations or an explicit mechanism in `ref_phage_biology` / `ref_ibd_indicators` | literature-linked gene evidence via `kescience_paperblast`, `kescience_pubmed`; `ref_ibd_indicators` |
| A4 | Not a protective-analog | Not on curated exclusion list (*C. scindens*, *F. prausnitzii*, *A. muciniphila*, *E. rectale*, *Roseburia spp.*, *Lachnospira spp.*, others per literature) | explicit exclusion list in project data dir |
| A5 | Causal / engraftment evidence | Engrafts in humanized mouse model AND enriches in patients, OR disease-specific strain-level adaptation genes present | engraftment donor-to-P2 tracking; `ref_kumbhari_s7_gene_strain_inference` |
| A6 | BGC-encoded inflammatory mediator | Associated BGC (NRPS / RiPP) in `ref_bgc_catalog` or `ref_cborf_enrichment`, preferably with disease-directional RPKM (`ref_ebf_ecf_prevalence`) | `ref_bgc_catalog`, `ref_cborf_enrichment`, `ref_ebf_ecf_prevalence` |

Scoring: a candidate must pass ≥ 5 of 6 (or equivalent weighted score) to enter Tier-B consideration. Each criterion reports a confidence tag: `observed`, `inherited-from-ref-table`, `inferred-from-literature` — distinguishing "we verified this" from "this came from a pre-computed table we did not re-check."

### Tier B — Phage availability and characterization (phage databases + pangenome)

| # | Criterion | Operationalization |
|---|---|---|
| B1 | ≥ 1 characterized strictly lytic phage | catalog entry with lytic lifestyle, not proven temperate |
| B2 | Host-range coverage | phage cocktail host range covers ≥ 80 % of target strain diversity in the affected ecotype |
| B3 | No transduction / ARG / toxin risk | phage genome annotation confirms no integrase, no transposase, no ARG, no toxin |
| B4 | Receptor identified | receptor gene annotated in the target; ideally a fitness-essential function |

Sources: `phagefoundry_strain_modelling`, `phagefoundry_ecoliphages_genomedepot`, per-genus PhageFoundry databases, INPHARED (Millard), IMG/VR, NCBI Phage Virus RefSeq, PhagesDB.

### Tier C — Ecological durability (BERDL pangenome + fitness + CRISPR + ecology)

| # | Criterion | Operationalization |
|---|---|---|
| C1 | CRISPR-Cas spacer immunity absent | ≤ 1 matching spacer between target strain and cocktail phage genomes |
| C2 | Prophage homoimmunity absent | no close relative of cocktail phage in target strain's prophage complement |
| C3 | Phage-resistance fitness cost high | receptor or proxy gene is essential / has high fitness cost of disruption in `kescience_fitnessbrowser` or pangenome essentiality inference |
| C4 | Removal does not open niche to another pathobiont | ecological modeling from `fact_strain_competition` co-occurrence patterns |
| C5 | Target not a hub with protective dependents | removing the target does not collapse a module containing protective species |

### Tier D — Clinical translation (flagged as experimental follow-up, NOT analyzed in this project)

Gut-transit stability, delivery route (oral / enema / NG / capsule), PK / PD, off-target kills, manufacturability, regulatory pathway. These gate candidates before a clinical trial; the scope of this project is to deliver ranked candidates, not to validate them experimentally.

## Methodological norms

**N1 — Verify where we can.** Pre-computed reference tables are starting points, not ground truth. Where a ref table is load-bearing for a claim, we re-run the underlying computation against the raw fact tables. Specifically:

- `ref_cd_vs_hc_differential` (Mann-Whitney) → verify against ANCOM-BC / MaAsLin2 / LinDA on `fact_taxon_abundance` per ecotype.
- `ref_consensus_severity_indicators` → verify the calprotectin / HBI correlations against `fact_clinical_longitudinal`.
- `ref_viromics_cd_vs_nonibd` / `ref_viromics_summary_by_disease` → verify against `fact_viromics` per ecotype.
- `ref_kumbhari_s7_*` → spot-check 3–5 top gene-level adaptation calls against the Kumbhari supplementary source to confirm the ETL did not drift.

Every Tier-A scored candidate carries one of three provenance tags per criterion: `observed` (re-computed in this project), `inherited-from-ref-table` (used ref table as-is), `inferred-from-literature` (external).

**N2 — Distinguish "CD-enriched" from "CD-associated."** Enrichment requires effect size, not just p-value. For compositional data we insist on log-ratio-based tests (CLR + linear model, ANCOM-BC) before accepting a log₂FC claim.

**N3 — Stratify before you sort.** No Tier-A scoring happens on pooled data. Every DA, regression, and correlation in Pillars 2 / 3 / 5 is run per ecotype (or explicitly noted as cross-ecotype).

**N4 — Power is bounded.** UC Davis n ≤ 21 unique patients. No within-UC-Davis claim is made without effect-size reporting; cross-cohort validation is required for any claim that proposes to generalize.

**N5 — Separate "UC Davis-observed" from "public-reference inherited."** Every UC Davis patient dossier entry makes this distinction explicit, so clinical readers can weigh evidence.

**N6 — BERDL query hygiene.** Every Spark notebook in this project starts with the JupyterHub-native Spark import pattern `spark = get_spark_session()` (no import statement — the session is injected into the BERDL JupyterHub kernel). Every query against a large BERDL table filters before aggregation per `docs/pitfalls.md`. Specifically:

- `kescience_fitnessbrowser.genefitness` (27M rows) — filter by `orgId` before any aggregation; **CAST** `fit` and `t` as DOUBLE before ABS/comparison (string-typed numeric columns).
- `kescience_fitnessbrowser` KO mapping — two-hop join via `besthitkegg` + `keggmember` (no direct `(orgId, locusId) → KO` table).
- `kbase_ke_pangenome.gene_cluster` (132M rows) — filter by `gtdb_species_clade_id` first; never full-scan.
- `kbase_ke_pangenome.genome_ani` (421M rows, O(n²)) — cap large species (K. pneumoniae = 14K genomes) at ≤ 500 genomes via subsampling; prefer species with < 500 genomes.
- `kbase_ke_pangenome.gtdb_taxonomy_r214v1.order` — backtick-quote in SQL (`` `order` ``) — reserved keyword.
- Pangenome taxonomy joins — use `genome_id`, not `gtdb_taxonomy_id` (different depth levels).

A notebook starts with an explicit header cell listing which BERDL databases it will touch and which filter predicates are applied; this is sanity-checked in the reviewer pass.

**N7 — Synonymy layer as taxonomy reconciliation backbone.** Any cross-cohort or cross-classifier analysis over `fact_taxon_abundance` resolves taxa through `data/species_synonymy.tsv` before any pivot / aggregate. The layer maps 2,417 aliases → 1,848 canonical species, grounded in NCBI taxid with GTDB r214+ genus renames. Without this, naive pivots produce log₂FC ≈ 28 artifacts (e.g., *B. vulgatus* / *P. vulgatus* split). Added as a norm in plan v1.2; documented as a pitfall in `docs/pitfalls.md`.

**N8 — Independent-evidence requirement for cluster-stratified DA.** When clusters (ecotypes) and the DA test-feature set share the same axis (e.g., clustering on taxon abundance then testing DA on taxa within cluster), require at least one independent evidence stream from a contrast whose clustering axis and test axis are disjoint. Bootstrap CIs and multi-method DA (CLR-MW + LinDA + ANCOM-BC) on the same within-cluster samples do NOT constitute independent evidence — they share the feature-leakage bias. In cMD specifically, within-IBD-substudy CD-vs-nonIBD is the tested-and-working independent source (see NB04c §3, NB04e). Added in plan v1.4 after NB04 rigor repair. Documented as a pitfall in `docs/pitfalls.md`.

**N9 — Adversarial review for any project whose conclusions inform downstream action.** The standard `/berdl-review` is systematically blind to (a) selection-on-outcome confounding, (b) effect sizes reported without null distributions, (c) hard-coded or post-hoc decision rules, (d) study-design unidentifiability. For any project whose REPORT.md will be cited by downstream notebooks, experimental design, clinical recommendation, or shared external artifacts, pair `bash tools/review.sh <project>` with a separately-spawned adversarial agent (`Agent(subagent_type=general-purpose, prompt=<explicit find-flaws brief>)`) and reconcile the two. Added in plan v1.4 after the NB04 failure case. Documented in `docs/discoveries.md`.

**N10 — LOSO ARI over bootstrap ARI for cluster stability.** For any clustering framework intended for cross-cohort use, report leave-one-substudy-out ARI (hold out each source study, refit, compute agreement on held-out) as the primary stability metric. Bootstrap 80 %-subsample ARI masks per-substudy variation (verified in NB04f: bootstrap 0.13–0.17 vs LOSO 0.00–0.28). The LOSO metric exposes which sub-studies fit the framework well vs poorly and is the honest replication claim.

**N11 — Separate framework-stability tests from operational-claim tests.** A clustering framework can have moderate stability AND strong per-cluster claim replication (or the reverse). Report both. Don't let "framework is marginally stable" imply "the specific Tier-A we derived from it is unreliable" — if Tier-A has independent-cohort validation (NB04h: 88.2 % sign concordance for NB04e E1 Tier-A on HMP2), that's the operational claim strength, which is what matters for downstream NB05 / clinical translation.

**N12 — Pillar 3+ inherits the confound-free within-IBD-substudy CD-vs-nonIBD meta-analysis design.** Every differential-abundance claim across modalities (pathway, metabolite, BGC, strain-adaptation gene, serology) uses the same 4 IBD sub-studies (HallAB_2017, LiJ_2014, IjazUZ_2017, NielsenHB_2014) with within-substudy CLR-Δ or equivalent, inverse-variance weighted meta across studies. Ecotype stratification on top of this is an additional layer; pooled CD-vs-HC is never the primary contrast in Pillar 3+. Added in plan v1.6 after the NB04e design proved to work. The design fails gracefully when (substudy × ecotype × diagnosis) cells are too small and reports explicitly which cells are meta-viable, single-study-only, or not viable — same reporting pattern as NB04e §3.

**N13 — Multi-modal joint-factor analyses (MOFA+, joint NMF, etc.) require per-modality confound-controlled QC before integration.** Running MOFA+ on un-QC'd pathway + metabolite + strain matrices risks joint factors that load on substudy or batch effects rather than biology. Each input modality must pass its own within-substudy DA sanity check (per N12) before contributing to a joint model. Added in plan v1.6 as a prerequisite for H3a and H3d MOFA steps.

**N14 — Dual-basis ecotype reporting for any Pillar 3+ claim that depends on ecotype membership** (v1.7 — restricted per adversarial review C2 + C8). The original v1.6 N14 mandated reporting effects under both taxonomic and alternative-feature-basis ecotypes for "consistency check." This is structurally broken when the alternative basis is the same axis as the test feature: e.g., pathway-DA stratified by pathway-feature ecotype is a feature-leakage trap (N8 violation), so reporting that arm next to the disjoint-axis arm formalizes a leakage-poisoned defense.

**v1.7 N14 (restricted):**
1. **Primary contrast is ALWAYS within-IBD-substudy CD-vs-nonIBD per N12** (disjoint-axis by construction — substudy is the partition; species/pathway/metabolite/serology is the test feature).
2. **Ecotype stratification on top of the primary contrast uses only the disjoint feature basis.** For pathway DA: stratify by taxonomic ecotype (NB01b consensus). For metabolite DA: stratify by taxonomic ecotype. Pathway-feature ecotype (NB04g) and metabolite-feature ecotype refit are NOT used to stratify their own modality's DA — that's leakage.
3. **Same-axis ecotype results (where they would be leakage-poisoned) MUST be reported as such, not used as supporting evidence.** The same-axis arm can serve as an internal-consistency check (does the pattern replicate even under leakage-poisoned conditions?) but cannot rebut a primary-arm null result.
4. **N14 only applies to ecotypes with viable cross-basis sample size.** E0 (n = 43 in NB04g pathway-ecotype) and E2 (n = 19) are dropped from N14 reporting; NB04g pathway-ecotype agreement was 0% (E0) and 47% (E2) — not enough mass for meaningful comparison.

**N15 — Per-modality substudy meta-viability re-verification before any new fact-table DA.** v1.6 had a defect inherited from NB04e: the "4 substudies meta-viable" framing was specific to taxonomic data (`fact_taxon_abundance`), but v1.6 applied it to pathway data (`fact_pathway_abundance`) without verification. Pathway data has only **3 robust + 1 boundary substudy** for within-IBD-substudy CD-vs-nonIBD (LiJ_2014 nonIBD = 10; VilaAV_2018 nonIBD = 0). Same modality-specific verification is required for `fact_metabolomics`, `fact_serology`, `fact_strain_competition`, `fact_viromics`. Each Pillar 3+ notebook MUST include a §0 substudy × diagnosis crosstab on its primary data table, and re-document substudy meta-viability for that modality.

**N16 — Sample-size + power-calibration pre-registration for every quantitative test.** v1.6 Pillar 3 had no power calculations for any H3 test. NB04 had the same gap. Pre-register, per test: minimum-detectable effect at α (post-FDR) and power 0.80 given the actual n; pre-registered effect-size threshold should be at or above this minimum-detectable effect, NOT below it. v1.7 H3a, H3b, H3d, H3e include these calibrations.

**N17 — Prefer ontology / class hierarchy over name-pattern regex for pathway / gene / metabolite categorization.** v1.7 H3a (b) used regex on pathway descriptive names to assign 7 a-priori categories. Two failure modes: (1) regex bugs (e.g., "glycan" matching peptidoglycan / cell-wall), (2) restricted vocabulary missing themes that the curator-validated taxonomy already enumerates (e.g., HEME-SYN, Heme-b-Biosynthesis class membership for PWY-5920, which v1.7 categorized as "0_other"). When a structured ontology / class hierarchy is available — ModelSEEDDatabase MetaCyc_Pathways.tbl for MetaCyc pathway classes; KEGG BRITE for KEGG pathway hierarchy; GO biological-process subontology for enzyme-level mapping — use it as the primary categorization. Regex on names becomes a sensitivity/check step, not the primary test. Added in plan v1.8 after the v1.7 H3a (b) regex approach was found degenerate.

## Query Strategy — tables required by pillar

### Pillar 1 (stratification)

| Table | Purpose | Filter / scope |
|---|---|---|
| `fact_taxon_abundance` | MetaPhlAn3 species profiles for DMM / topic modeling | `classification_method == 'metaphlan3'`; CMD_IBD + HMP2 as training; Kuehl (Kaiju) held out |
| `fact_pathway_abundance` | HUMAnN3 MetaCyc pathways for topic modeling / MOFA | CMD_IBD only (scope 1a) |
| `fact_metabolomics` | HMP2 untargeted (27.3M rows) for MOFA metabolite factor | within-cohort; 35 compounds for cross-cohort bridge |
| `fact_clinical_longitudinal` | severity / medication covariates for H1c classifier | all cohorts with clinical data |
| `dim_participants` + `dim_samples` | subject-level dedup, longitudinal handling | filter to baseline visit per subject for stratification |
| `ref_taxonomy_crosswalk` | reconcile MetaPhlAn3 / Kaiju / GTDB namespaces | 1,951 species bridge |

### Pillar 2 (pathobiont ID)

| Table | Purpose |
|---|---|
| `fact_taxon_abundance` | within-ecotype compositional-aware DA |
| `fact_strain_frequency_wide` + `fact_strain_competition` | strain-level within-species heterogeneity + within-patient severity |
| `ref_consensus_severity_indicators` | starter Tier-A scaffold (verify per N1) |
| `ref_cd_vs_hc_differential` | starter pool of 420 species (verify per N1) |
| `ref_ibd_indicators` | literature ground-truth for sanity check |
| `ref_phage_biology` | starter Tier-1 dossier (12 organisms) — extend |
| `ref_kumbhari_s7_gene_strain_inference` | strain-adaptation genes per species |
| `ref_kumbhari_s7_eggerthella_lenta_predict` | E. lenta exemplar for strain-gene inference pattern |

BERDL joins:
- `kbase_ke_pangenome.bakta_amr` + `kbase_ke_pangenome.bakta_annotations` → virulence / AMR gene burden per target strain
- `kbase_ke_pangenome.gene_cluster` → pangenome gene-content variation within species (for Tier-A A5 strain adaptation)
- `kescience_paperblast.genepaper` + `kescience_pubmed` → literature linkage for Tier-A A3 mechanism

### Pillar 3 (functional drivers)

| Table | Purpose |
|---|---|
| `fact_pathway_abundance` | within-ecotype pathway DA (CMD_IBD only) |
| `fact_metabolomics` | within-cohort untargeted DA; 35-compound cross-cohort bridge via `ref_metabolite_crosswalk` |
| `fact_serology` | Pillar-3 H3e serology-microbiome integration (HMP2 only) |
| `ref_bgc_catalog` (10,060) + `ref_cborf_enrichment` (5,157) | BGC / core-biosynthetic-ORF mechanism |
| `ref_mag_catalog` (76) | BGC → pathobiont MAG linkage (known gap: no R. gnavus, no AIEC) |
| `ref_hmp2_metabolite_annotations` | HMDB-anchored metabolite name resolution for HMP2 |
| `ref_metabolite_crosswalk` | 7,368 compounds; 35 three-way ChEBI |

BERDL joins:
- `kbase_msd_biochemistry.reaction` + `kbase_msd_biochemistry.compound` → pathway ↔ reaction ↔ metabolite mapping for mechanism inference
- `kbase_ke_pangenome.gapmind_pathways` → GapMind metabolic completeness per target species
- `kescience_interpro` → domain-level virulence factor / CRISPR-Cas / adhesin classification

### Pillar 4 (phage targetability)

| Table | Purpose |
|---|---|
| `fact_viromics` (HMP2) + `ref_viromics_summary_by_disease` (780) + `ref_viromics_cd_vs_nonibd` (22) | endogenous phageome per ecotype |
| `ref_phage_biology` | Tier-1 organism phage dossier (12 rows) — extend |

BERDL joins:
- `phagefoundry_strain_modelling` → experimental phage-host interaction matrix (critical for Tier-B B2 host range)
- `phagefoundry_ecoliphages_genomedepot` → E. coli phages (primary AIEC cocktail input)
- `phagefoundry_klebsiella_*` → Klebsiella phages (K. oxytoca cocktail input)
- `phagefoundry_acinetobacter_*` / `phagefoundry_paeruginosa_*` / `phagefoundry_pviridiflava_*` → context / cross-species host-range reference
- `kescience_fitnessbrowser.genefitness` → phage-resistance fitness-cost inference (Tier-C C3)
- `kbase_ke_pangenome` CRISPR-Cas operon annotations → Tier-C C1

External databases (out-of-BERDL):
- Millard lab INPHARED (https://millardlab.org/bacteriophage-genomics/) — comprehensive phage genome catalog
- IMG/VR — viral metagenome reference
- NCBI Phage Virus RefSeq — curated phage genomes
- PhagesDB — additional characterized phages for gram-negative and gram-positive targets

### Pillar 5 (UC Davis deep dive)

| Table | Purpose |
|---|---|
| `~/data/CrohnsPhage/crohns_patient_demographics.xlsx` | UC Davis clinical metadata (21 patients, 23 samples) |
| `fact_taxon_abundance` filtered to Kuehl `study_id == 'KUEHL_WGS'` | UC Davis taxonomic profile (Kaiju; map via `ref_taxonomy_crosswalk` to MetaPhlAn3 reference space) |
| `fact_clinical_longitudinal` (UC Davis rows) | calprotectin / severity (HBI / CDAI pending from Dave lab) |
| `ref_mag_catalog` filtered to Kuehl MAGs (76) | UC Davis strain resolution (acknowledge gap: no R. gnavus, no AIEC) |

Per-patient dossier output columns (per H5c):
`patient_id, ecotype, ecotype_confidence, calprotectin, Montreal, medication_class, top_N_pathobionts (ranked by Tier-A score), per-pathobiont [prevalence_in_patient, strain_adaptation_gene_count, BGC_present, causal_evidence], candidate_phages (per pathobiont, Tier-B/C flags), longitudinal_stability (for patients 6967 and 1460), confidence_notes`.

## Analysis Plan — notebook sketch

| NB | Pillar | Environment | Core output |
|---|---|---|---|
| **NB00** | all | local (no Spark) | Data audit: profile each parquet in `~/data/CrohnsPhage/`, validate column names / dtypes / missingness against the per-table dictionary YAMLs, reconcile the 33 tables against `schema_overview.yaml`, and document each fact / ref table's actual columns in `projects/ibd_phage_targeting/data/table_schemas.md` (since `docs/schemas/` has no coverage for these local-mart tables). Reproduce one slice of the preliminary DA vs compositional-aware DA as a proof-of-concept for norm N1 and the *C. scindens* paradox. Figures: coverage summary, missingness heatmap, sample-count-per-cohort, protective-species sanity check (C. scindens, F. prausnitzii, A. muciniphila). |
| **NB01** | 1 | local | Ecotype training v1: build the systematic synonymy layer (`data/species_synonymy.tsv`, 2,417 aliases → 1,848 canonical species, GTDB r214+ renames included), pivot 8,489 CMD MetaPhlAn3 samples × 1,442 species, fit LDA (DMM-equivalent on pseudo-counts) and GMM (on CLR + PCA) over K=2..8. Initial K=8 result. **Note: HMP2 MetaPhlAn3 not in mart yet** (lineage.yaml `PENDING_HMP2_RAW`); training on CMD only. **Pathway topic model deferred** (CMD_IBD-only per scope 1a); **MOFA+ deferred** (cross-modality is properly scoped after each modality has its own ecotypes). |
| **NB01b** | 1 | local | K-selection refit: held-out perplexity for LDA + cross-method ARI scan (LDA vs GMM) + parsimony rule. Result: **consensus K = 4**, 48.9 % per-sample method agreement, four biologically clean ecotypes (E0 diverse healthy commensal; E1 Bacteroides2 transitional disease/metabolic; E2 Prevotella copri non-Western; E3 severe Bacteroides/fragilis-expanded). `data/ecotype_assignments.tsv` overwritten with K=4 result and `methods_agree` flag. |
| **NB02** | 1 | local | Ecotype projection: project UC Davis Kuehl_WGS (Kaiju namespace → MetaPhlAn3 via synonymy layer) and HMP2 (when ingested) onto the trained K=4 embedding; test H1b occupancy. Figures: UC Davis per-ecotype distribution, held-out cohort occupancy. |
| **NB03** | 1 | local | Clinical-covariate-only ecotype classifier (H1c); report AUC, feature importance. |
| **NB04** | 2 | local | Within-ecotype compositional-aware DA (ANCOM-BC + MaAsLin2 + LinDA consensus); Tier-A A1 / A2 scoring. Figures: ecotype × species enrichment heatmap, C. scindens paradox comparison. |
| **NB05** | 2 | local | Tier-A scoring pipeline: A3 (literature via paperblast), A4 (protective-analog exclusion), A5 (engraftment + strain adaptation), A6 (BGC linkage). Output: scored candidate table. |
| **NB06** | 2 | local | Co-occurrence network per ecotype (SparCC / SpiecEasi); module detection; H2d intersection with Tier-A. Figures: module networks, Tier-A-hub overlap. |
| **NB07a** | 3 | local | Pathway DA within-IBD-substudy CD-vs-nonIBD meta. **§0 substudy × diagnosis crosstab on `fact_pathway_abundance`** (verified: HallAB_2017 / IjazUZ_2017 / NielsenHB_2014 robust; LiJ_2014 boundary-only with nonIBD=10; VilaAV_2018 excluded — CD=216 / nonIBD=0). 10 %-prevalence + UNMAPPED/UNINTEGRATED filter. Per H3a v1.7 falsifiability: 3 permutation nulls (pathway count, category coherence, pathway-pathobiont attribution). **N14 dual-basis is restricted to taxonomic ecotype only** (pathway-feature ecotype dropped per C8 — same-axis leakage). Figures: per-substudy forest plots, MetaCyc-category enrichment with random-allocation null. |
| **NB07b** | 3 | local | Pathway → Tier-A-core attribution: per pathway × Tier-A-core species (6 × ~50 passing pathways), within-substudy Spearman ρ + ρ-meta + 200-perm null. Tier-B (9 species) sensitivity-test FDR-corrected separately, NOT in primary H3a verdict. Figures: pathway × pathobiont heatmap with significance flags. |
| **NB07c** | 3 | local | **H3a-new module-anchor commensal × pathobiont coupling test (renamed per C1; not "butyrate-producer")**. Per anchor (heterogeneous fermentation modes — pre-registered per-anchor producer/consumer expectation; 5 anchors with positive predictions, *Firmicutes CAG 110* null-only): per E1 / E3 / E1_CD / E3_CD subnet, test producer-pathway × consumer-pathway Spearman + species × species Spearman within-IBD-substudy meta. Use **E3_CD module hubs** for CD-specific cross-feeding (per X4 fix), not E3_all. Cross-feeding-vs-shared-environment distinguished by NB09c metabolite-level corroboration. |
| **NB07d** | 3 | local | MOFA+ joint factor — **scoped per C3 fix**: HMP2-only pilot (≤ 383 specimens after sample-key reconciliation via dim_samples crosswalk; ≈ 105 unique participants). Sample-key rule: strip `CMD_IBD:` / `HMP2:` prefixes, join via `dim_samples.sample_id` cross-cohort key. Ecotype-as-covariate (NOT ecotype-as-factor-target — too few samples for E0/E2 to factor independently). N13 prerequisite: each modality passes its own NB07a/NB09a/NB10a QC. |
| **NB08a** | 3 | local | BGC × pathobiont × CD-vs-nonIBD test (H3c) — for each Tier-A-core species, within-IBD-substudy regression with species × BGC interaction term; FDR on interaction at species level. Synonymy-validation count for ref_bgc_catalog × Tier-A-core join (per M7) reported in §0. |
| **NB08b** | 3 | local | UC-Davis-specific CB-ORF / ebf / ecf per-patient annotation: parse per-patient BGC presence/absence from Kuehl_WGS; flag Tier-A-relevant BGCs per UC-Davis patient for Pillar 5. |
| **NB09a** | 3 | local | HMP2 metabolomics × ecotype × CD-vs-nonIBD test (H3d-DA). Features: top 300 metabolites by HMDB-annotated variance from `ref_hmp2_metabolite_annotations`. **§0**: HMP2 → ecotype projection ambiguity (max-posterior < 0.70 → flag as "ambiguous", excluded from primary; sensitivity test includes them, per I8 fix). DA stratified by **taxonomic ecotype only** (disjoint axis per N14 v1.7 + N8). Per-metabolite normalization rule: median-scaling within (study, method) per `fact_metabolomics.method` column (per I4 fix). |
| **NB09b** | 3 | local | Cross-cohort metabolite bridge via `ref_metabolite_crosswalk`. **Includes FRANZOSA_2019** (220 samples, missed in v1.6 per I4) and DAVE (~234 samples). Re-run NB09a signals across all 3 cohorts; 35 three-way-ChEBI anchors as primary, full crosswalk as sensitivity. |
| **NB09c** | 3 | local | Focused bile-acid / SCFA / tryptophan metabolism mechanism test. Anchors: bile-acid 7α-dehydroxylation → *C. scindens* / *F. plautii*; SCFAs → 2 actual butyrate producers (*B. pullicaecorum*, *A. caccae*) + propionate (*Phascolarctobacterium*); tryptophan → AhR ligands. **Provides the metabolite-level corroboration test for NB07c H3a-new** (cross-feeding vs shared-environment distinction). |
| **NB09d** | 3 | local | **H3d-clust LOSO stability test on metabolite-factor clustering** (H3d-clust per H3d split). Hold out HMP2 / FRANZOSA / DAVE in turn; refit metabolite K=4 NMF on remaining; project held-out; ARI vs full-fit. Pre-registered threshold: LOSO ARI > 0.20 to support H3d-clust. |
| **NB10a** | 3 | local | **H3b restricted to Kumbhari cohort (per C5 fix)**: within `fact_strain_competition` (15,520 strain × sample observations + LSS-PRISM + PRISM + MUSC sub-cohorts). Per-species: predict `disease_strain_freq > health_strain_freq` from gene-content features in `ref_kumbhari_s7_gene_strain_inference`; held-out by Kumbhari sub-cohort. Falsifiability per H3b v1.7. |
| **NB10b** | 3 | local | Cross-cohort sensitivity test (acknowledged-weak per H3b v1.7): species-level prevalence-weighted strain-feature on cMD samples; AUC delta vs species-only baseline. Bound delta < 0.05 expected even if biology is real. Sensitivity-only, not load-bearing. |
| **NB11** | 3 | local | Serology × microbiome integration (H3e v1.7, HMP2 only, **n = 67 participants per C6 fix**). Site (CCHMC / Harvard / Emory) as covariate. Per-participant mean serology (not per-sera, which is pseudo-replicated); longitudinal-regression as sensitivity check on participants with ≥ 4 sera. Pre-registered threshold |r| > 0.40 (calibrated to n=67 power; not 0.25 which had power < 0.30). 6 unique serology axes after EU+Pos deduping per I9. |
| **NB12** | 4 | JupyterHub (Spark) + local | Pathobiont × phage coverage matrix (PhageFoundry + external phage DBs). Tier-B B1 / B2 scoring. |
| **NB13** | 4 | local | CRISPR-Cas spacer analysis (Tier-C C1); phage-resistance fitness cost via `kescience_fitnessbrowser` (Tier-C C3). |
| **NB14** | 4 | local | Endogenous phageome stratification per ecotype (H4d); prophage superinfection-exclusion risk annotation. |
| **NB15** | 5 | local | UC Davis medication-class harmonization (parse the Excel into structured `therapy_class`), ecotype projection, per-patient pathobiont ranking. |
| **NB16** | 5 | local | Per-patient phage cocktail drafts (H5c); longitudinal stability check for 6967 and 1460 (H5d). |
| **NB17** | all | local | Synthesis figures + final target ranking per ecotype, cohort-level summary, per-patient dossier. |

Notebook numbers are provisional; NB00 is the audit, NBs 01–03 are Pillar 1, 04–06 Pillar 2, 07–11 Pillar 3, 12–14 Pillar 4, 15–16 Pillar 5, 17 cross-cutting synthesis.

## Reproduce-and-extend — what we carry forward from the preliminary analysis

| From preliminary report | Where it lives in this plan | What we add |
|---|---|---|
| Species-level DA on curatedMetagenomicData (`ref_cd_vs_hc_differential`, 420 species) | Pillar 2 / NB04 | Re-run compositional-aware per ecotype (ANCOM-BC / MaAsLin2 / LinDA) |
| Dysbiosis score (Cohen's d = 1.32) | Pillar 1 feature input | Retain formula; use as one stratification input |
| HUMAnN3 MetaCyc pathway DA | Pillar 3 / NB07 | Re-run within-ecotype; flag HMP2 / UC Davis as known gaps (no raw reads) |
| HMP2 untargeted metabolomics (25,540 features) | Pillar 3 / NB09 | Cohort-specific analysis + 35-compound cross-cohort bridge |
| SAMP/AKR targeted metabolomics (taurocholic acid −3.86; PC 32:2–34:3) | Pillar 3 / NB09 | Cross-check HMP2 bile-acid panel for concordance; small-n caveat |
| Engraftment donor 2708 → P1 → P2 (6 pathobionts transfer) | Pillar 2 Tier-A A5 | Use directly as causal evidence; request NRGS metadata from Dave lab |
| Kumbhari strain-level adaptation (E. lenta *katA*, *rodA*, *ponA*, *acnA*, *rlmN*) | Pillar 3 / NB10 | Extend pattern to all 59 Kumbhari species |
| Elmassry BGC catalog (10,060; 112 pathobiont-linked) | Pillar 3 / NB08 | Per-ecotype BGC DA; ebf / ecf per-patient |
| CB-ORF enrichment (5,157; 115 CD-enriched, 211 CD-depleted) | Pillar 3 / NB08 | CB-ORF × ecotype stratification |
| Calprotectin correlation | Pillar 5 / NB15 + Tier-A A2 | Ecotype-stratified regression |
| GTDB-Tk MAG catalog (76) | Pillar 2 / Pillar 3 | Acknowledge R. gnavus / AIEC gap explicitly |
| Composite Tier-1 / Tier-2 target list (E. bolteae, E. lenta, R. gnavus, H. hathewayi, etc.) | Pillar 2 baseline | Starting hypothesis for rubric validation |

## Known missing-data registry

Tagged via `ref_missing_data_codes` sentinel codes. Does not block analysis but should be reported in every pillar's conclusion.

| Gap | Impact | Mitigation |
|---|---|---|
| Dave lab clinical metadata (HBI / CDAI for ~23 patients) `PENDING_DAVE_LAB` | Pillar 5 H5b severity regression uses calprotectin + CRP only until HBI arrives | Request from Dave lab; flag plan revision when received |
| Dave lab pipeline documentation `PENDING_KUEHL` | Kaiju version, reference DB date unknown | Use available Kaiju output; note provenance gap in figures |
| HMP2 EC enzyme profiles on disk, not in schema `PENDING_HMP2_RAW` | Pillar 3 pathway analysis limited to CMD_IBD | Document as follow-up; no raw reads to run HUMAnN3 ourselves (scope decision 1a) |
| 62 Dave SAMP metabolite IDs unintegrated | Pillar 3 / NB09 within-cohort metabolomics slightly incomplete | Integrate if a targeted mechanism requires them; otherwise accept |
| Kumbhari 5,492 / 6,138 samples lack `dim_samples` entries | Kumbhari-derived analyses rely on `fact_strain_*` joins directly, not through `dim_samples` | Document join pattern in NB00 audit |
| Viral taxonomy in `fact_viromics` 19 / 316 reconciled to `dim_taxa` | Endogenous phageome analysis uses VirMAP lineage strings, not taxon_ids | Build a VirMAP → external-viral-DB crosswalk as Pillar 4 deliverable |
| No raw reads for UC Davis or HMP2 | Cannot re-run MetaPhlAn3 / HUMAnN3 / StrainPhlAn / inStrain | Scope decisions 1a / 3a formally acknowledge this |

## Expected Outcomes — what each H outcome means

- **If H1a–c hold**: reproducible ecotype framework with clinical-covariate projector. Foundational for everything else.
- **If H2a–d hold**: per-ecotype Tier-A target list, each with ≥ 2 hub candidates in co-occurrence modules — proposes consortial cocktail design per ecotype.
- **If H2c fails (C. scindens *still* CD-enriched after stratification)**: the stratification is wrong or the protective annotation needs re-examination. Either is informative.
- **If H3a–d hold**: mechanism-anchored target list with bile-acid / mucin / sulfide / TMAO / BGC themes attributable to specific pathobionts. Concrete a-priori MetaCyc functional-coherence categories (per H3a falsifiability): (1) secondary-bile-acid biosynthesis / 7α-dehydroxylation, (2) mucin-degradation glycoside hydrolase families (GH33, GH84, GH95, GH109, GH110), (3) sulfate / thiosulfate reduction + hydrogen sulfide production, (4) TMA / TMAO / choline metabolism (CutC/D + YeaW/X), (5) ethanolamine / propanediol utilization, (6) polyamine biosynthesis + urease, (7) amino-acid decarboxylation (tryptophanase, arginine/ornithine). H3a is supported if ≥ 10 DA pathways distribute across ≤ 5 of these categories; failed if DA pathways disperse across > 5 categories or show no category coherence.
- **If H3a-new holds**: NB06 butyrate-producer-as-pathobiont-module-anchor finding is metabolically grounded (shared substrates identified); implication is that naive "preserve butyrate producers" is NOT a valid phage-targeting rule.
- **If H3e holds**: serology-confirmed targets with external experimental validation (single-cohort caveat: HMP2 is the only serology-bearing cohort; cross-cohort replication of H3e is not possible within current data).
- **If H4a–d hold**: per-ecotype cocktail designs with strain coverage, resistance-escape risk, and endogenous-phageome compatibility.
- **If H5a–d hold**: per-UC-Davis-patient phage cocktail drafts with per-pillar provenance tags, clinical-ready rubric outputs, longitudinal stability notes.
- **If any pillar's core hypotheses fail**: that failure is a useful negative result for clinical-trial design, not a project failure. The criteria rubric is designed to be falsifiable, not to rubber-stamp hypotheses.

## Potential confounders and limitations

- **Medication confounding**: anti-TNF / anti-IL23 / JAK inhibitors / 5-ASA / corticosteroids modify microbiome composition. UC Davis cohort is heterogeneous on this axis. Ecotype classification and within-ecotype DA must include medication class as a covariate.
- **Biogeography**: stool metagenomics under-samples mucosa-associated communities. AIEC is mucosa-associated. Biopsy samples (where available) treated as separate modality.
- **Smoking**: opposite effects in UC vs CD; UC Davis has heterogeneous smoking history.
- **Age**: pediatric IBD may have different ecotype structure; public-cohort age span (curatedMetagenomicData + HMP2) includes pediatric and adult.
- **Ethnicity / geography**: training on mostly-Western cohorts may not generalize to non-Western IBD patients. Flag but do not attempt to correct.
- **Host genetics (NOD2, IL23R, ATG16L1, etc.)**: UC Davis cohort lacks genotype data. Public cohorts partial. Treat as a *possible* future Pillar-6 extension.
- **Single-donor engraftment evidence (donor 2708)**: N = 1 causal evidence. We treat as strong but irreplicable without additional donors.
- **Pillar 3-specific confounders (v1.6)**:
  - **Metabolomics platform variation**: HMP2 uses LC-MS untargeted (546 samples); CMD metabolomics subset (check — not all CMD studies have it) uses varied platforms. Cross-cohort metabolite abundance comparisons need per-platform standardization (median-batch-scaling or ratio-to-internal-standard). Flag in NB09a/b outputs.
  - **Pathway database version skew**: `fact_pathway_abundance` uses HUMAnN3 MetaCyc (v24.1 per lineage.yaml); any cross-reference to BiGG or KEGG pathway DBs needs explicit mapping (`ref_metabolite_crosswalk` covers compound-level; pathway-level mapping needs verification in NB07a §0).
  - **HMP2 metabolite annotation coverage**: `ref_hmp2_metabolite_annotations` (81K rows) vs `ref_metabolite_crosswalk` (7,368 compounds with 35 three-way ChEBI anchors) — join coverage needs pre-NB09 verification. If < 30 % of HMP2 untargeted features have HMDB annotations usable for cross-cohort bridging, flag as a scope limitation.
  - **Serology single-cohort (HMP2 only)**: H3e has no replication path. Cross-cohort generalization of serology-pathobiont correlations cannot be tested in Pillar 3; flag as a structural limitation.
  - **Kumbhari strain-adaptation scope**: 59 species, 219K gene-strain inferences. NB05 actionable 6 species are the priority; full 59-species scan (NB10b) is extension, not core. Strain-adaptation data is one cohort (Kumbhari / LSS-PRISM) and has its own confounds that don't translate cleanly to within-IBD-substudy meta design. Treat as separate evidence stream, not pooled into N12 meta.

## Revision History

- **v1.8** (2026-04-25): H3a (b) reformulation via MetaCyc class hierarchy after NB07a/b execution exposed the v1.7 regex-on-names approach as both buggy and structurally underpowered. Key changes:
  - **Replace v1.7 regex-on-pathway-names with MetaCyc Class assignments from `/global_share/KBaseUtilities/ModelSEEDDatabase/Biochemistry/Aliases/Provenance/MetaCyc_Pathways.tbl`**. The tbl has **90 % coverage of our 575 HUMAnN3 unstratified pathways** (516/575) with rich multi-membership class hierarchy (e.g., heme biosynthesis maps to `HEME-SYN`, `Cofactor-Biosynthesis`, `Tetrapyrrole-Biosynthesis`, `Heme-b-Biosynthesis`).
  - **Expand from 7 a-priori categories to 12 IBD-relevant themes**, adding what NB07a/b found in the "0_other" bucket: **iron/heme acquisition**, **fat metabolism / β-oxidation / glyoxylate**, **anaerobic respiration / alt electron acceptors**, **purine/pyrimidine recycling**, **aromatic AA / chorismate / indole**. The original 7 themes are retained with bug fixes (peptidoglycan no longer matches mucin/glycan; ornithine is word-bounded; etc.).
  - **Replace H3a (b) "concentrate in ≤3 of 7 categories" framing with per-theme Fisher's exact enrichment** (CD-up × in-theme) with BH-FDR across 12 themes. This is structurally proper — pathways can be multi-membership, and theme-level enrichment is the standard biological interpretation.
  - **Verdict rule (v1.8 H3a (b))**: ≥ 1 IBD theme passes Fisher's exact at FDR < 0.10 with odds ratio > 1.5 = SUPPORTED. Each enriched theme gets reported with the contributing pathway list.
  - **NB07a §6-8 + NB07b §4-5 re-run** with the corrected schema. Original v1.7 output preserved as `nb07a_h3a_v17_*.tsv` for audit; v1.8 outputs are `nb07a_h3a_v18_*.tsv`.
  - **Generalizable observation** (to add to `docs/discoveries.md`): regex-on-pathway-name is a brittle approximation when curator-validated ontology / class hierarchy is available. ModelSEEDDatabase ships a usable MetaCyc class hierarchy (90 %+ coverage of HUMAnN3 outputs) that should be the default for any HUMAnN3-pathway category-enrichment test in BERIL projects. Plan norm N17 added: prefer ontology / class hierarchy over name-pattern regex for pathway / gene / metabolite categorization wherever feasible.
  - **Pillar 3 H3a (b)** now has a defensible test design that handles the structural underpowered-ness identified by NB07a/b execution. v1.7 verdict (FAIL — degenerate) is superseded by v1.8 verdict (TBD — to be reported by re-run).

- **v1.7** (2026-04-24): Pillar 3 plan revised after **adversarial review of v1.6** found 4 critical + 10 important issues structurally analogous to NB04's failure pattern (paraphrased: feature leakage in N14 dual-basis; "4-substudy meta-viable" inherited from NB04e without re-verification for pathway data — actually 3+1; H3a effect-size thresholds without null distributions; H3a-new mislabeled "butyrate-producer ↔ pathobiont" with 4 of 6 named anchors not actually butyrate producers; H3b strain-adaptation operationalization collapses to species-level on cMD by construction; H3e n=67 across 3 sites, not 130-subject HMP2). Same kind of issues that NB04 hit. Adversarial review caught them BEFORE notebook execution; v1.7 fixes them.
  - **Pillar 3 Scope Refresh rewritten**: primary contrast IS within-IBD-substudy CD-vs-nonIBD per N12; substudy meta-viability is **modality-specific** and must be verified per fact-table (per-table viability for pathway data: 3 robust + 1 boundary, NOT 4); Tier-A inputs explicitly pre-registered (Tier-A core = 6 actionable; Tier-A extended = 6 + 9 Tier-B; NB06 anchors = top-3-degree per CD-specific module from `nb06_module_hubs.tsv`).
  - **Plan norm N14 restricted**: same-axis ecotype basis is leakage-poisoned, MUST be flagged as such not used as supporting evidence. Drop E0 / E2 from N14 (insufficient cross-basis sample size). Pathway-feature ecotype is NOT used to stratify pathway DA; metabolite-feature ecotype is NOT used to stratify metabolite DA.
  - **Two new norms**: N15 (per-modality substudy meta-viability re-verification before any new fact-table DA — v1.6 inherited NB04e's taxonomic-data viability blindly), N16 (sample-size + power-calibration pre-registration for every quantitative test — v1.6 had no power calcs for any H3).
  - **H3a v1.7**: 3 falsifiability clauses each with explicit permutation null (pathway count, category coherence, pathway-pathobiont attribution); power-calibrated effect-size thresholds; tightened category-concentration bound (≥ 60% in ≤ 3 of 7 a-priori categories, not "≤ 5").
  - **H3a-new renamed**: "module-anchor commensal ↔ pathobiont metabolic coupling" (drop "butyrate-producer" — only 2 of 6 named anchors actually produce butyrate). Per-anchor producer/consumer expectations pre-registered with heterogeneous fermentation modes; *Firmicutes CAG 110* is null-only (no positive prediction). Cross-feeding-vs-shared-environment distinction requires NB09c metabolite-level corroboration.
  - **H3b restricted to Kumbhari cohort**: cMD has no strain-level genotyping, so cMD-strain-adaptation operationalization collapses to species-level by construction; v1.7 H3b runs strain-level analysis on Kumbhari `fact_strain_competition` data (where strain-level resolution exists). Cross-cohort cMD-extension is sensitivity-test only, not load-bearing.
  - **H3d split**: H3d-clust (metabolite-feature LOSO stability across 3 metabolomics cohorts) + H3d-DA (per-metabolite CD-vs-nonIBD within HMP2 stratified by taxonomic ecotype only). Same-axis arm prohibited per N14 v1.7.
  - **H3e corrected to actual data**: n = **67 participants** across 3 sites (CCHMC / Harvard / Emory), not 130. Site as covariate. Effect-size threshold |r| > 0.40 (calibrated to n=67 power 0.80, not |r| > 0.25 from v1.6 which had power < 0.30). 6 unique serology axes after EU+Pos deduping. Single-cohort caveat structural (no replication path).
  - **Notebook outline revised**: NB07a §0 verifies pathway-modality substudy viability; NB07c uses E3_CD module hubs for CD-specific cross-feeding (not E3_all); NB07d MOFA+ scoped to ≤ 383 HMP2-only specimens with ecotype-as-covariate (not factor target); NB09a normalization rule specified (median-scaling within (study, method)); NB09b adds FRANZOSA_2019 (220 samples, missed in v1.6); NB09d corresponds to H3d-clust split; NB10a Kumbhari-only, NB10b cross-cohort sensitivity-only; NB11 with corrected n=67 + site batch.
  - **Pillar 3 confounders / Limitations** retained from v1.6 + adversarial-review-validated.

- **v1.6** (2026-04-24): Pillar 3 scope refresh after Pillar 2 closure. Incorporates the confound-free design lessons from NB04e, the NB06 butyrate-producer-as-module-anchor finding, and the now-unlocked HMP2 data (via cMD R package). Key changes:
  - **Pillar 3 Scope Refresh** subsection added at top of Pillar 3 — ties Tier-A inputs to NB05 actionable + NB06 module members; mandates within-IBD-substudy meta design.
  - **Three new plan norms**: N12 (Pillar 3+ inherits within-IBD-substudy meta), N13 (multi-modal joint-factor analyses require per-modality confound-controlled QC before integration), N14 (dual-basis ecotype reporting for ecotype-conditioned claims).
  - **H3a refined**: within-IBD-substudy meta design replaces within-ecotype DA as primary contrast; tightened falsifiability (≥10 DA pathways, ≤5 MetaCyc categories). A-priori MetaCyc categories enumerated in Expected outcomes.
  - **H3a-new added**: butyrate-producer ↔ pathobiont metabolic-coupling test following NB06 module-anchor finding.
  - **H3b refined**: predictive-power test operationalized as 5-fold CV AUC difference > 0.03 on held-out substudies.
  - **H3c refined**: species × BGC interaction term in within-substudy regression (FDR on interaction, not main effect).
  - **H3d reframed**: metabolomic signatures should _reproduce_ ecotype stratification with HIGHER LOSO stability than taxonomy, not just "independent of." If metabolite-factor clustering has LOSO ARI > taxonomic-ecotype LOSO ARI (0.113), that's a positive finding.
  - **H3e refined**: longitudinal-regression test with HMP2 subject random effects; single-cohort caveat explicit.
  - **Notebooks split**: NB07 → NB07a/b/c/d (pathway DA / attribution / butyrate-cross-feeding / MOFA), NB08 → NB08a/b, NB09 → NB09a/b/c/d (HMP2 metabolomics / cross-cohort bridge / focused bile-acid / external replication), NB10 → NB10a/b (NB05-subset first, full scan second).
  - **Pillar 3 confounders added** to §Limitations: metabolomics platform variation, pathway DB version skew, HMP2 metabolite annotation coverage, serology single-cohort, Kumbhari strain-adaptation scope.

- **v1.5** (2026-04-24): Pillar 2 strengthening — LOSO stability, pathway-feature refit, HMP2 external replication. After v1.4 committed the rigor-repair pipeline, three additional notebooks tested the framework and Tier-A against three failure modes:
  - **NB04f — LOSO ecotype stability.** Mean ARI 0.113 (range 0.000–0.282) across 8 held-out substudies, more honest than bootstrap ARI 0.160. Some sub-studies (LifeLinesDeep 85 % agreement) fit the framework well, others (AsnicarF 38 %, VilaAV 17 %) poorly. **Retracts the "four reproducible ecotypes" framing** as bit-reproducible across sub-studies; the framework has real cross-study variance.
  - **NB04g — Pathway-feature K=4 refit** on 3,145 CMD_IBD HUMAnN3 samples. ARI 0.113 vs taxon-based consensus; per-ecotype agreement E1 65 %, E3 31 %, E2 47 %, E0 0 % (n=43). Ecotype structure is mixed ecological + taxonomic.
  - **NB04h — HMP_2019_ibdmdb external replication.** Pulled live via `curatedMetagenomicData` v3.18 (1,627 samples, 130 subjects) — HMP_2019_ibdmdb is NOT in our cMD_IBD training set. Ecotype projection: 80 % of samples at max posterior > 0.70; subject-level χ² = 15.61, p = 0.016; **E1 Tier-A 88.2 % sign-concordant (45/51 candidates CD↑ in both cohorts), including every top-10 candidate**. **Pillar 2 operationally externally validated.**
  - **New framing**: framework stability and operational-claim replication are separate properties. This project has a framework with real cross-study variance AND rigorously-replicated Tier-A. Both statements are honest.
  - **New plan norm N10 added**: **LOSO ARI is the preferred stability metric over bootstrap ARI** for any clustering framework intended for cross-cohort use. Bootstrap masks per-substudy variation; LOSO exposes it.
  - **New plan norm N11 added**: **separate framework-stability tests from operational-claim tests**. A project can have moderate framework stability and strong downstream-claim replication, or the reverse. Report both. Don't let "marginal stability" leak into claims about specific targets that have independent-cohort validation.
  - HMP2 raw data ingestion via cMD R package is **no longer a blocker** for external replication; the `PENDING_HMP2_RAW` issue primarily affects ingestion into the mart (for Pillar 3 metabolomics × taxonomy integration), not external ecotype / Tier-A replication.

- **v1.4** (2026-04-24): NB04 rigor-repair arc. **NB04 committed → standard `/berdl-review` ×2 clean → adversarial review found 5 critical + 6 important issues → NB04b (partial repair) → NB04c (completion) → NB04d (formalized stopping rule) → NB04e (confound-free Option A meta) rescued Pillar 2.** Key changes to the plan:
  - **H2c retracted.** The NB04 claim "*C. scindens* paradox resolved by within-ecotype stratification" was a feature-leakage artifact. Under the confound-free within-IBD-substudy CD-vs-nonIBD meta (NB04c §3), *C. scindens* is genuinely CD↑ (+1.18 CLR-Δ, FDR 1e-8, 4/4 sign concord) — there is no paradox. REPORT.md §5 retraction box documents this.
  - **H2b retained under a rigor-controlled statistic.** Permutation null (200 perms) puts observed Jaccard 0.104 at empirical p = 0.000 against a null mean 0.785 ± 0.054. Conclusion (E1 and E3 target sets diverge) survives; the NB04 "Jaccard = 0.14" framing retracted because the observed value was near the random-overlap baseline.
  - **Tier-A rebuilt under a confound-free design** (NB04e): within-ecotype × within-substudy CD-vs-nonIBD meta across the 4 IBD sub-studies that have both CD and nonIBD. E1 is meta-viable across HallAB_2017 + NielsenHB_2014 → **51 candidates**, all 100 % sign-concordant. E3 is single-study-only (HallAB_2017 × E3) → **40 provisional candidates**. Cross-ecotype engraftment-confirmed: 5/6 donor-2708 pathobionts pass under NB04c §3.
  - **Two new pitfalls committed to `docs/pitfalls.md`**: (a) cMD sub-studies are structurally nested within diagnosis (45 HC-studies, 5 CD-studies, zero overlap) → pooled CD-vs-HC LME is unidentifiable; use within-IBD-substudy CD-vs-nonIBD; (b) feature leakage in cluster-stratified DA — clustering on taxa then testing same taxa within cluster is selection-on-outcome confounding.
  - **Plan norm N8 added**: for any within-cluster DA, require an independent evidence stream from a contrast whose clustering axis and test axis are disjoint. Bootstrap + LinDA on the same within-cluster samples do NOT constitute independent evidence (both share the leakage bias). Within-substudy CD-vs-nonIBD is the tested-and-working independent source in cMD.
  - **Plan norm N9 added**: pair standard `/berdl-review` with an adversarial reviewer (general-purpose Agent with explicit "find flaws" framing) for any project whose conclusions inform downstream action. The standard reviewer is systematically blind to selection-on-outcome confounding, missing null distributions, post-hoc decision rules, and study-design unidentifiability. See `docs/discoveries.md` and `FAILURE_ANALYSIS.md`.
  - **Ecotype stability documented as marginal**: bootstrap ARI on 5 × 80 %-subsample refits = median 0.160, range [0.129, 0.169] — below the 0.30 bar. Framework is usable for stratification but not externally replicable without MGnify projection. Flagged as a Pillar 1 limitation.
  - **NB04 artifacts marked superseded, not deleted** (`data/nb04_tier_a_candidates.tsv`, `data/nb04_da_ecotype_{1,3}.tsv`, figures `NB04_h2c_paradox_resolution.png`, `NB04_top_tier_a_per_ecotype.png`). Kept for audit; NB04b/c/d/e + their TSVs + `figures/NB04b_jaccard_null.png` are the authoritative Pillar 2 artifacts.
  - **Pillar 2 verdict revised**: **E1 PROCEED** (51 candidates, 2-substudy meta); **E3 PROCEED WITH CAVEAT** (40 candidates, single-study, flagged provisional); E0 and E2 not analyzable in cMD (no IBD-study nonIBD controls). NB05 (Tier-A scoring with A3–A6) is unblocked on the rigor-controlled input set; HMP2 re-ingestion is the primary unblock for E3 replication.
  - **New project artifact**: `projects/ibd_phage_targeting/FAILURE_ANALYSIS.md` — full failure arc, lessons, methodology recommendations.

- **v1.3** (2026-04-24): NB02 + NB03 execution outcomes — Pillar 1 closed.
  - **NB02**: UC Davis Kuehl_WGS (26 samples, 23 patients) projected onto the K=4 embedding via the synonymy layer. LDA is the primary projection method for Kuehl (feature-sparsity-robust); GMM is advisory (collapses under Kaiju / MetaPhlAn3 classifier mismatch — all Kuehl samples land in E3 at >97 % GMM confidence, an artifact). UC Davis distribution: E0 27 % / E1 42 % / E2 0 % / E3 31 %, χ² p = 0.019 against uniform. **H1b directionally supported.** Patient 6967 shows intra-patient longitudinal disagreement (E1 ↔ E3) — first signal for H5d.
  - **NB03**: clinical-covariate-only ecotype classifier (H1c). Macro OvR AUC 0.799 (minimal) / 0.810 (extended) — both pass the 0.70 threshold. **But UC Davis patient agreement is only 41 % / 36 %.** Minimal classifier predicts E1 for 19/22 UC Davis patients because `is_ibd = 1` is constant and the learned rule collapses to the marginal mode. Extended classifier's training subset is 702 E1 / 959 E3 / 3 E0 / 11 E2 — effectively an E1-vs-E3 binary problem.
  - **H1c revised**: "Passes on pooled-cohort AUC; fails on patient-level translation." Clinical covariates distinguish HC vs IBD trivially (`is_ibd` dominates AUC), but do *not* reliably separate IBD ecotypes (E1 transitional vs E3 severe) without metagenomics. For UC Davis-type cohorts (all active CD), **metagenomics remains the primary ecotype-assignment method**. The per-patient dossier (Pillar 5, NB15–NB16) cites NB02's metagenomic call, not NB03's clinical prediction.
  - **Norm note**: OvR-AUC on a cohort with a strong cohort-axis variable (like `is_ibd`) can overstate per-patient classifier usefulness. Logged as discovery: always validate classifier decisions on an independent cohort before quoting AUC as a clinical-utility metric.
  - **Pillar 1 closed**: H1a, H1b directionally supported; H1c nuanced (paper-pass / patient-fail). Ready for Pillar 2 (NB04 within-ecotype DA — the *C. scindens* paradox resolution).

- **v1.2** (2026-04-24): NB01 + NB01b execution outcomes. Updates:
  - `data/species_synonymy.tsv` (2,417 aliases → 1,848 canonical species) committed as the project-wide taxonomy reconciliation backbone. Norm N7 is now a *deliverable*, not just a methodology note.
  - **Ecotype training** delivered K=8 in NB01 (per-method criteria) but cross-method ARI was weak (0.128). NB01b refit selected **K=4** by maximum cross-method ARI + parsimony, raising agreement to 48.9 %. Four biologically interpretable ecotypes:
    - E0 (n=3,604) — diverse healthy commensal (66.8 % of HC)
    - E1 (n=2,601) — Bacteroides2 transitional / metabolic-disease (48 % CD, 58 % UC, 100 % T1D, 97 % T2D)
    - E2 (n=920) — Prevotella copri enterotype (non-Western healthy comparator)
    - E3 (n=1,364) — severe Bacteroides/fragilis-expanded (50 % CD, 67 % IBD acute, 38 % CDI)
  - **H1a directionally supported**: ≥ 3 reproducible ecotypes confirmed. **H1b directionally supported**: CD/UC distribute across E1 + E3 rather than concentrating in one.
  - **Notebook table**: NB01 split into NB01 (training, K-scan) and NB01b (K-selection refit). HMP2 MetaPhlAn3 confirmed `PENDING_HMP2_RAW`; pathway topic model and MOFA+ explicitly deferred from NB01.
  - **Method note**: LDA on pseudo-counts (sklearn) used as DMM equivalent; GMM on CLR + PCA-20 used as compositional-aware alternative. Both methods reach K=4 as the parsimonious agreement point.

- **v1.1** (2026-04-24): Plan-review follow-up (`PLAN_REVIEW_1.md`, claude-sonnet-4). Added:
  - Norm N6 — explicit BERDL query hygiene (Spark import pattern, `CAST` for string-typed numerics, two-hop KO mapping, large-table filter requirements, `order` keyword backtick-quoting, genome_id join rules, genome_ani subsampling).
  - Extended H2c protective-species validation battery beyond *C. scindens* to *F. prausnitzii*, *A. muciniphila*, *E. rectale*, *R. intestinalis*, *L. eligens*.
  - Expanded NB00 scope to include committing a `data/table_schemas.md` for the CrohnsPhage fact / ref tables (since `docs/schemas/` has no coverage).
- **v1** (2026-04-24): Initial plan — five pillars, four-tier criteria, verify-where-we-can norm, reproduce-and-extend from the 2026-03-28 preliminary report. Scope decisions: (1a) pathway DA on CMD_IBD only, (2a) 35-compound metabolomics cross-cohort bridge, (3a) Kumbhari 432-strain panel as primary. No raw reads available, so options (1b) and (3b) ruled out a priori.

## Authors

- Adam Arkin (ORCID: [0000-0002-4999-2931](https://orcid.org/0000-0002-4999-2931)), U.C. Berkeley / Lawrence Berkeley National Laboratory

Collaborators (data providers, attribution here pending formal authorship):
- UC Davis CD cohort: Kuehl / Dave lab
- Engraftment mouse experiments: Dave lab (NRGS)
- Strain-level reference analyses: Kumbhari et al. 2024 (PMID / source in `dim_studies`)
- BGC meta-analysis: Elmassry et al. 2025 (Cell Host & Microbe)

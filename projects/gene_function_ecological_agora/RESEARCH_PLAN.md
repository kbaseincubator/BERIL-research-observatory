# Research Plan: Gene Function Ecological Agora

*Innovation Atlas Across the Bacterial Tree*

## Research Question

Across the prokaryotic tree (GTDB r214; 293,059 genomes / 27,690 species), do clades specialize in the *kind* of functional innovation they produce, and does the **HPK-count-vs-recent-LSE correlation** that Alm, Huang & Arkin (2006) reported for two-component systems (r = 0.74 in their 207-genome substrate) generalize to other function classes — particularly differing between regulatory and metabolic ones?

*v2.5 reframe* (2026-04-27): the central question has been reformulated to faithfully reflect what Alm 2006 *actually claimed* (a correlation between HPK abundance and lineage-specific-expansion rate, plus a threshold classification of HPK-enriched genomes). The earlier framing — "the producer/consumer asymmetry observed by Alm 2006" — overstated Alm 2006's claims; they did not name producer/consumer or four-quadrant categories. The Producer × Participation / four-quadrant framework used in this project is *this project's construction*, Alm-2006-inspired but not Alm-2006-derived. See `docs/alm_2006_methodology_comparison.md` for the close-reading record and DESIGN_NOTES.md v2.4 for the design-trace of this correction.

*v2.9 strategic reframe* (2026-04-27): the project's central deliverable is now framed as **"the innovation + acquisition-depth atlas of bacterial function classes, anchored to clade phylogeny and environmental ecology."** Per (clade × function-class) tuple, the atlas reports: (a) **production rate** (paralog expansion above null — producer score); (b) **acquisition profile** by depth (recent-genus / older-family / mid-order / older-class / ancient-phylum gain events from Sankoff parsimony, M22); (c) **MGE-context fraction** (whether gain events occur in mobile-element context, P4-D2); (d) **environmental ecology** (where the clade is documented to live, NMDC + MGnify + GTDB metadata, P4-D1); (e) **phenotype anchoring** where data exist (BacDive + Web of Microbes + Fitness Browser, P4-D1). The four pre-registered weak-prior hypotheses (Bacteroidota PUL, Mycobacteriota mycolic-acid, Cyanobacteria PSII, Alm TCS) are specific test points within this atlas. The regulatory-vs-metabolic asymmetry test (NB11 Tier-1) remains as one **diagnostic** of the atlas — "do regulatory function classes show different acquisition-depth profiles than metabolic ones?" — but no longer the single headline. See DESIGN_NOTES.md v2.8 for the strategic design-trace.

## Hypothesis

The hypothesis is structured as one **headline scientific claim** plus **three pre-registered focal predictions**, with quantitative thresholds.

### Headline (1 test, FWER<0.05)

- **H0**: Innovation pattern (mean producer score, mean participation score) does not differ significantly between regulatory and metabolic function classes (KEGG BRITE B-level: regulatory = `09120 Genetic Information Processing` + `09130 Environmental Information Processing`; metabolic = `09100 Metabolism`).
- **H1**: Innovation pattern differs between regulatory and metabolic function classes with Cohen's d ≥ 0.3 on at least one of the two scores at FWER<0.05.

### Atlas-level (descriptive)

- **H0-atlas**: At least 90% of (clade × function-class) tuples lie on the producer-participation diagonal (no specialization detectable above null).
- **H1-atlas**: ≥10% of (clade × function-class) tuples are off-diagonal at BH-FDR q<0.05 with Cohen's d ≥ 0.3, populating Producer × Participation categories non-uniformly.

The fallback (diagonal-collapse) form is itself a finding — that prokaryote innovation is correlated in/out at clade level even when category is not predictive — and is a publishable Phase-1 outcome.

### Producer × Participation Categories at Deep Ranks vs Full Four-Quadrant at Genus Rank

**Critical clarification, added in v2 in response to the adversarial review (I3):**

At family rank and above, direction of HGT is not inferable. The plan therefore reports two scores and the cross-classification:

- **Producer score**: paralog expansion above the clade-matched neutral-family null (within-clade, direction-free)
- **Participation score**: clade-pair shared incongruent presence (number of function classes where the clade is involved in HGT events, donor or recipient indistinguishable)

The two-by-two cross-classification at deep ranks (≥ family rank):

| | Low Participation | High Participation |
|---|---|---|
| **High Producer** | Innovator-Isolated | Innovator-Exchange |
| **Low Producer** | Stable | Sink/Broker-Exchange |

At genus rank only, Phase 3 composition-based donor inference (codon usage Δ, dinucleotide signature) discriminates the genuinely directional Open / Broker / Sink / Closed labels:

- Innovator-Exchange at genus rank → **Open Innovator** (X is donor) OR **Sink with paralogs** (X is recipient)
- Sink/Broker-Exchange at genus rank → **Broker** (X is donor) OR **Sink** (X is recipient)

The full four-quadrant labels (Open / Broker / Sink / Closed) apply *only* at genus rank in Phase 3. Phase 1 and Phase 2 atlas verdicts use the Producer × Participation framing. The Alm 2006 "Open Innovator" pattern can therefore only be confirmed at genus rank; at deep ranks it is *consistent with* but not confirmed by Innovator-Exchange.

## Literature Context

- **Alm, Huang & Arkin 2006** (PLOS CB 2(11):e143) — original producer/consumer asymmetry on TCS HKs across 207 genomes. The mandatory back-test target.
- **Treangen & Rocha 2011** (PLOS Gen 7(1):e1001284) — HGT, not duplication, drives prokaryotic family expansion. Reframes paralog count as HGT signal at long timescales.
- **Smillie et al. 2011** (Nature 480:241) — ecology drives gene-exchange networks. Documents Bacteroidota → Firmicutes CAZyme transfer in the human gut; informs Phase 1 pre-registered prediction.
- **Puigbò, Wolf & Koonin 2009, 2010** (J Biol 8:59; GBE 2:745) — tree and net components of prokaryote evolution. Foundational atlas-style framing.
- **Popa et al. 2011** (Genome Res 21:599) — directed networks for HGT inference; informs the directed clade-to-clade flow graph deliverable.
- **Coleman et al. 2021** (Science 372:eabe0511) — rooted phylogeny resolves early bacterial evolution; informs deep-rank validation choices.
- **Szöllősi et al. 2013** (Syst Biol 62:386, 901) — gene tree-species tree reconciliation, applied here only on principled subsamples (constraint).
- **Morel et al. 2024** (Bioinformatics 40:btae162) — AleRax for DTL reconciliation. Available as a last-resort sub-sample tool, not at full GTDB scale.
- **Metcalf et al. 2014** (eLife 3:e04266) — antibacterial-gene transfer across the tree of life. Informs validation framing for pure-import systems as secondary controls only.

## Approach: Three-Phase Multi-Resolution Atlas, Forced Order

The plan tests the central question at three resolutions, in a forced order. Each phase's output gates and refines the next; the final atlas is the cross-resolution synthesis.

### Through-Line Logical Argument

1. **Existence before resolution**. The atlas claim only matters if the four-quadrant structure is real and not an artifact of EggNOG annotation density. The lowest-bias resolution at which existence can be tested is sequence-only (UniRef50). Phase 1 must come first.
2. **Sequence existence does not answer the headline**. The regulatory-vs-metabolic question is functional, and UniRef50 has no functional grain. KO is the natural functional resolution. But KO results inherit the annotation-density bias Phase 1 was designed to bypass; therefore Phase 1's UniRef50→KO projection table tells Phase 2 which KOs are *sequence-anchored* (run as primary) vs *annotation-driven only* (run as rail).
3. **Alm 2006 is at architectural resolution, and architecture is expensive**. Phfam multidomain architecture is the resolution where Alm 2006's HK paralog finding lives. Architecture-level scoring is ~2× the cost of KO-level. Therefore Phase 3's targets are inherited from Phase 2: the KOs where Phase 2 finds a strong quadrant signal AND multiple architectures co-exist.
4. **Cross-resolution synthesis is the deliverable**, not an epilogue. Concordance across three resolutions is the strongest atlas claim; conflict is the most informative failure mode.

### Each Phase Is a Stop-Point

Each phase produces a publishable artifact. Phase 1 alone, if structure is absent, is a publishable negative result with a clean methodological contribution. Phase 1+2 alone, if Phase 3 turns out to be unaffordable, is a publishable functional atlas. The full sequence is the most ambitious version.

---

## Phase 1 — Existence Test (UniRef50, sequence-only)

*v2 split into Phase 1A pilot + Phase 1B full scale, in response to adversarial review C3 (computational feasibility) and recommendation to validate methodology before scaling.*

**Question**: Does the Producer × Participation structure exist when annotation-density bias is stripped out? Does the regulatory-vs-metabolic prior already fail at the sequence level via a documented metabolic-system test case?

### Substrate (applies to both Phase 1A and 1B)
- **A. Function-class unit**: UniRef50 cluster (sequence-only)
- **B1. Within-clade family unit**: UniRef90 cluster nested in UniRef50; paralog count = distinct UniRef90s within UniRef50 within clade above clade-matched neutral-family null
- **B2. Cross-clade orthology**: UniRef90 co-membership
- **C. Direction inference**: Fully direction-agnostic; clade × UniRef50 acquisition signal and participation signal only (no donor-recipient assignment at any rank in Phase 1)

### Bias Control Stack
- D1: One GTDB representative per species (27,690 reps for full scale)
- D2: Per-genome annotated-fraction regressed out as nuisance covariate (OLS with clade-size, annotated-fraction, GC%, genome-size as predictors)
- D3: Per-clade effective N reported alongside every score
- D4: GTDB rank-level topology-support filter (rank used as depth scaffold; events called at deepest rank where node support > 0.7 AND effective N ≥ 10)
- Negative controls: ribosomal proteins, tRNA synthetases, RNA polymerase core (see Controls section above)
- Positive controls: AMR genes, CRISPR-Cas, Alm 2006 TCS HKs (see Controls section above)
- **KO-projection rail** (in lieu of UniRef50 self-rail): post-hoc map UniRef50 → dominant KO via majority vote, rerun headline test with KO labels as commentary check
- Sensitivity: per-clade rarefaction; jackknife on clade members; ANI-stratified within-species sub-sampling per "Within-Species Genome Sampling Strategy" above

---

### Phase 1A — Pilot (1,000 species × 1,000 UniRef50 clusters)

**Purpose**: Validate the null models, multiple-testing strategy, and signal detection on a tractable subset before scaling. Address adversarial review S2 ("Phase 1 may fail for computational rather than biological reasons").

**Pilot subset**:
- **Species**: 1,000 GTDB representatives, stratified across phyla (proportional to phylum size in GTDB but with floor of 5 species per phylum to ensure CPR/DPANN representation)
- **UniRef50 clusters**: 1,000 clusters stratified across COG categories (proportional to COG-category frequency, with explicit inclusion of all positive-control (TCS HK Pfams, AMR, CRISPR-Cas) and negative-control (ribosomal, tRNA synthetase, RNAP) UniRef50s)
- **Critical inclusion**: Alm 2006 TCS HK UniRef50 set must be present in the pilot — the back-test runs at this scale

**Pilot deliverables**:
- Producer null calibrated on neutral families; producer score distributions reported
- Consumer null calibrated on phyletic-distribution permutation; consumer score distributions reported
- Negative controls: ribosomal proteins must show producer score within ±1 σ of zero across all phyla
- Positive controls: AMR genes must show consumer score significantly above zero in Enterobacteriaceae and Acinetobacteriaceae at q<0.05; CRISPR-Cas must show clade-pair incongruent presence consistent with Metcalf 2014
- **Alm 2006 TCS reproduction at pilot scale**: HK paralog expansion in Pseudomonadota / Bacillota lineages must reproduce at q<0.0125 (Bonferroni for the 4 focal tests)
- Phase 1A → Phase 1B gate decision

**Phase 1A → Phase 1B gate**:
- **Pass**: All four positive controls hit signal at q<0.0125; all three negative controls stay on-diagonal; Alm 2006 reproduction confirmed.
- **Fail (recalibrate)**: One or more positive controls fail to reach signal OR negative controls show false positive paralog expansion → halt scale-up, recalibrate the null model on the pilot, then retry Phase 1A. Up to two recalibration cycles.
- **Stop**: After two recalibration cycles, if controls still fail, halt project. The methodology cannot reliably detect the framework's foundational signal at scale.

**Phase 1A effort**: ~1 agent-week.

---

### Phase 1B — Full Scale (27,690 species × all UniRef50 clusters)

**Purpose**: Apply the validated methodology at GTDB scale. Produce the Phase-2 handoff data.

**Pre-registered prediction (Phase 1B; v2 reframe with Producer × Participation)**:

**Bacteroidota → Innovator-Exchange (high Producer, high Participation) for PUL (polysaccharide-utilization-locus) UniRef50 clusters**, defined as UniRef50 clusters whose dominant Pfam projection is in the CAZy GH/CBM family set. *Note: at deep ranks we cannot discriminate the Open Innovator vs Sink-with-paralogs interpretation; that discrimination is reserved for Phase 3 genus-rank donor inference. The Phase 1B prediction is the deep-rank Producer × Participation form.*

**Prior strength**: WEAK. (See Prior Calibration below.)

**Reasoning**: Smillie et al. 2011 documented elevated Bacteroidota ↔ Firmicutes CAZyme HGT in the human gut. Bacteroidota are described as CAZyme-paralog innovators. Both ingredients (high producer + high participation) point to Innovator-Exchange.

**Falsification**: Bacteroidota producer score on PUL UniRef50s is below the atlas median (not Innovator-Exchange), OR Bacteroidota participation score on PUL UniRef50s is below the atlas median, at q<0.0125 (Bonferroni for 4 focal tests).

**Prior Calibration** (alternatives we cannot rule out at deep ranks):
- *Innovator-Isolated*: high producer + low participation, if Bacteroidota CAZyme expansion is largely vertically inherited within the phylum without inter-phylum HGT.
- *Sink/Broker-Exchange*: low producer + high participation, if Bacteroidota CAZyme presence is largely HGT-acquired from elsewhere rather than de novo paralog-driven.
- *Stable*: no specialization detectable above null.
- *At genus rank in Phase 3*: even if Innovator-Exchange holds, the Open Innovator vs Sink-with-paralogs split is only resolvable via composition-based donor inference.

**What we genuinely don't know**: Whether "PUL UniRef50 cluster" is a coherent enough function unit for a category verdict, vs collapsing into noise from heterogeneous CAZy families. Pilot rarefaction will tell us.

### Phase 1B Output Products (Phase 2 handoff)
- `data/p1_uniref50_atlas.parquet` — clade × UniRef50 producer/participation scores with bootstrap CIs
- `data/p1_uniref50_categories.tsv` — Producer × Participation category assignment per clade × UniRef50 (Innovator-Isolated / Innovator-Exchange / Sink/Broker-Exchange / Stable)
- `data/p1_uniref50_to_ko_projection.tsv` — UniRef50 → dominant KO mapping with concordance score (the Phase-2 input)
- `data/p1_bacteroidota_pul_test.tsv` — pre-registered hypothesis verdict
- `data/p1_alm_2006_pilot_backtest.tsv` — Alm 2006 TCS reproduction at pilot scale (Phase 1A)
- `data/p1_controls_diagnostic.tsv` — positive/negative control results
- `data/p1_null_model_diagnostics.parquet` — rarefaction curves, effective N, D2 residualization diagnostics

### Phase 1B Gate to Phase 2 (quantitative thresholds, v2)
- **Pass strong-form**: ≥10% of (clade × UniRef50) tuples in Innovator-Exchange or Innovator-Isolated category at q<0.05 with Cohen's d ≥ 0.3 AND Bacteroidota PUL = Innovator-Exchange at q<0.0125 → Phase 2 proceeds with strong-form regulatory-vs-metabolic test.
- **Pass reframed**: structure exists (≥10% off-(low,low)) but Bacteroidota PUL is **not** Innovator-Exchange → Phase 2 reframes the regulatory-vs-metabolic prior. The strong-form prior collapses; the question becomes empirical.
- **Stop**: structure not detected (≥90% of tuples on the (low,low) Stable cell at q<0.05) → fall back to the diagonal claim, publish as Phase-1 negative result with the Alm 2006 reproduction as a methodological contribution, halt the atlas project.

### Phase 1 Notebooks
1. `01_p1a_pilot_data_extraction.ipynb` — extract gene_cluster → UniRef50 / UniRef90 mapping from `bakta_db_xrefs` for the 1K pilot species; GTDB taxonomy parsed; control sets pulled
2. `02_p1a_null_model_construction.ipynb` — implement producer null + consumer null; calibrate on pilot subset; report null distributions
3. `03_p1a_pilot_atlas.ipynb` — compute pilot clade × UniRef50 scores; control validation; Alm 2006 TCS pilot back-test
4. `04_p1a_pilot_gate.ipynb` — Phase 1A → Phase 1B gate decision; null-model recalibration if needed
4b. `04b_p1a_review_response.ipynb` — *(post-review appendix; addresses adversarial C3 + I2)* reproducibly compute raw paralog-count effect sizes per (rank, class) and Alm 2006 power analysis at pilot scale. Outputs feed REPORT.md v1.1 review-response section.
5. `05_p1b_full_data_extraction.ipynb` — full GTDB-rep extraction (conditional on Phase 1A pass)
6. `06_p1b_full_atlas.ipynb` — full clade × UniRef50 scores; KO-projection rail; rarefaction sensitivity
7. `07_p1b_bacteroidota_pul_test.ipynb` — pre-registered hypothesis verdict
8. `08_p1b_phase_gate.ipynb` — Phase 1B → Phase 2 gate decision

*Numbering note*: 04b is a Phase 1A appendix iteration following the BERIL convention for in-phase sub-iterations (precedent: `ibd_phage_targeting`'s NB04b–h adversarial-review rescue cycle). Phase 1B numbering starts at NB05 as planned.

### Phase 1 Effort
**Phase 1A pilot ~1 week + Phase 1B full ~4 weeks = ~5 weeks total.** The pilot adds 1 week to v1's 4-week budget; this is purchased insurance against the failure mode (computational issues masquerading as biological absence).

---

## Phase 2 — Functional Resolution (KO, paralog-explicit)

**Question**: Does the deep-rank Producer × Participation pattern map onto KO-defined functional categories (KEGG BRITE B-level) the way the regulatory-vs-metabolic prior predicts? Does the Alm 2006 TCS back-test reproduce at KO level on the GTDB substrate?

### Methodology Commitments (M16–M20)

Phase 2 inherits five methodology commitments from the Phase 1B closure. The full rationale lives in the v2.6 and v2.7 entries of the Revision History; the names are restated here so Phase 2 implementation has a single source of truth.

- **M16** — Sankoff parsimony on the GTDB-r214 species tree topology is the **primary atlas metric** for Phase 2. Per-leaf Sankoff (`gain_events / n_present_leaves`) is the comparison statistic; raw Sankoff score is reported alongside. Parent-rank dispersion drops to secondary diagnostic only.
- **M17** — `pos_amr` (bakta_amr) is excluded from the Phase 2 positive-control panel due to documented Pseudomonadota detection bias in AMRFinderPlus. β-lactamase (`pos_betalac`), class-I CRISPR-Cas (`pos_crispr_cas`), and TCS HK (`pos_tcs_hk`) are the load-bearing positive controls; AMR is reported as informational only.
- **M18** — **Hard amplification falsification gate** (not a validated prediction). Phase 2 KO atlas must demonstrate Cohen's d ≥ 0.3 on Sankoff parsimony / n_present for at least one positive HGT control class vs negative housekeeping. The UniRef50 baseline is d = 0.146 (NB08c). If Phase 2 fails to amplify to d ≥ 0.3, the substrate-hierarchy claim is falsified and **M11 redesign triggers** (switch to gene-tree-vs-species-tree reconciliation per AleRax sub-sampling).
- **M19** — Cluster-bootstrap on UniRefs at Pfam-family granularity for Cohen's d 95% CIs (B = 200 resamples per function class). Addresses UniRef-cluster non-independence that classical Felsenstein PIC does not (Sankoff already encodes tree topology, so PIC on top is double-counting). This replaces the deferred M9 PIC commitment.
- **M20** — Independent paralog holdout for producer-null validation. natural_expansion is retained as metric-direction sanity check; an independent holdout (Pfam clans with documented paralog families per Treangen & Rocha 2011; KO orthogroups with cross-organism duplicates per the Csurös 2010 Count framework) becomes the load-bearing producer-null validation. Acceptance: holdout producer z significantly above zero at all ranks with effect direction matching natural_expansion.

- **M21** *(new at v2.8)* — **Canonical clean housekeeping** for M18-style methodology validation and any d-based metric in Phase 2/3 = **tRNA synthetase** (`K01866..K01890`) + **RNAP core** (`{K03040, K03043, K03046}`) only. Ribosomal — both description-match and the strict K02860-K02899 + K02950-K02998 range — is contaminated at KO level (description-match catches clade-restricted accessories; strict K-range is a pre-2000 numbering approximation that mixes universal r-proteins with accessory variants). Ribosomal is reported as informational only. NB09c established M18 PASS with 6/9 strict pairs at d ≥ 0.3 (best d = 3.56) using the M21 housekeeping definition.

- **M22** *(new at v2.9)* — **Recipient-rank gain attribution from Sankoff**. The Sankoff parsimony reconstruction (M16) marks every internal node where a function-class gain occurred. M22 is a post-processing pass that extracts each gain event with two annotations: (i) **recipient clade at every rank** (which species/genus/family/order/class/phylum owns the gain location); (ii) **acquisition-depth bin** = the rank at which the gain landed. Aggregated per (clade × function-class), this yields an **acquisition profile**: counts of recent (genus-rank gain) / older recent (family) / mid (order) / older (class) / ancient (phylum-or-above) gains. *No donor inference.* Same level of phylogenetic-origin claim that Alm 2006's lineage-specific-expansion analysis made. Implementation: NB10b post-processing on existing Sankoff output (~30 min compute at GTDB scale; ~1 day implementation). Joins with NB10 atlas for the full Phase 2/3 deliverable.

**Phase 2 control panel** (NB09c-validated):
- Positive HGT controls: `pos_betalac` (β-lactamase, 110 KOs), `pos_crispr_cas` (class-I CRISPR-Cas, 6 KOs), `pos_tcs_hk` (TCS HK, 310 KOs)
- Negative housekeeping (load-bearing per M21): `neg_trna_synth_strict` (`K01866..K01890`, 20 KOs in panel of 25 total), `neg_rnap_core_strict` (`{K03040, K03043, K03046}`, 3 KOs)
- Informational only: `info_amr` (per M17, Pseudomonadota detection bias), `neg_ribosomal_strict` (per M21, bimodal contamination)

**M12 scope**: M12's relative-threshold framing (consumer z relative to housekeeping baseline) governs *methodology QC only*. The four pre-registered hypotheses (Bacteroidota PUL, Mycobacteriota mycolic-acid, Cyanobacteria PSII, Alm 2006 TCS reproduction) retain absolute-criterion adjudication. This separation is a discipline boundary, not a methodology element.

### Substrate
- **A. Function-class unit**: KO from `eggnog_mapper_annotations.kegg_ko`
- **B1. Within-clade family unit**: UniRef90 cluster within KO; paralog count = distinct UniRef90s per KO per clade
- **B2. Cross-clade orthology**: UniRef90 co-membership
- **C. Direction inference**: Acquisition-only at family rank and above; composition-based donor flag (codon usage Δ, GC% Δ vs clade norm) at genus rank as advisory only — *direction is not inferable at deep ranks given the constraint that no full DTL recon runs at GTDB scale*

### Bias Control Stack
- D1–D4 mandatory
- **UniRef50 sanity rail** (mandatory): every KO-headline result rerun with UniRef50 cluster identity collapsed in place of KO, using Phase 1's projection table
- Sensitivity: rank-by-rank stability check (does the headline hold at family rank vs class rank?); UniRef90/UniRef50 cross-validation on headline KOs

### Phase 1 Handoff Use
- `p1_uniref50_to_ko_projection.tsv` defines the **sequence-anchored KO subset**: KOs where ≥80% of mapped UniRef50 clusters concur on KO assignment. Headline regulatory-vs-metabolic test runs on this subset (primary). Full KO set runs as rail (secondary).
- KO Producer × Participation categories computed in Phase 2 are compared against KO-projected-from-UniRef50 categories from Phase 1B. Concordance ≥75% across sequence-anchored KOs is a soft sanity threshold (validated empirically in Phase 1B NB07; threshold may be data-driven if 75% is unachievable).

### Pre-registered Prediction (Phase 2; v2 reframe with Producer × Participation)

**Mycobacteriota → Innovator-Isolated (high Producer, low Participation) for the mycolic-acid pathway KO set** (KEGG ko00540 + FAS-II + mycolyl transferase KOs). *Note: at deep ranks "Innovator-Isolated" is the deep-rank analog of "Closed Innovator" — high producer score with low participation in inter-clade gene exchange. The strict "Closed Innovator" claim (high producer + low **outflow** specifically) requires donor inference at genus rank, which Phase 3 attempts only on the architectural deep-dive candidate set.*

**Prior strength**: WEAK-TO-MODERATE.

**Reasoning**: Mycolic-acid biosynthesis is a cell-envelope-coupled autocatalytic process whose intermediates require host enzymatic context for incorporation. The pathway is a defining trait of the *Corynebacteriales* sensu lato, and there is no documented case of a non-mycolic-acid lineage acquiring functional mycolic-acid biosynthesis. This points to high lineage-specific paralog expansion + low participation in cross-clade gene exchange.

**Falsification**: At q<0.0125 (Bonferroni for 4 focal tests):
- Mycobacteriota producer score on mycolic-acid KOs falls below the atlas median for non-housekeeping KOs, OR
- Mycobacteriota participation score on mycolic-acid KOs is above the atlas median (suggesting cross-clade exchange we don't expect).

**Prior Calibration** (alternatives we cannot rule out at deep ranks):
- *Stable*: low producer + low participation, if the Mycobacteriota mycolic-acid pathway is largely inherited unchanged from a *Corynebacteriales* common ancestor with no recent paralog expansion (cell-envelope already mature).
- *Innovator-Exchange*: high producer + high participation, if there is unrecognized cross-Corynebacteriales-genus mycolic-acid HGT we don't expect from the literature.

**What we genuinely don't know**: Whether "mycolic-acid pathway KO set" includes enough of the actual cell-envelope machinery to give a category verdict that is biologically interpretable, or whether the KEGG pathway is too partial. *Phase 3 architectural-resolution rerun on this candidate KO set will refine.*

### Phase 2 Output Products (Phase 3 handoff)
- `data/p2_ko_atlas.parquet` — clade × KO producer/consumer scores
- `data/p2_ko_categories.tsv` — Producer × Participation category assignments at KO level
- `data/p2_regulatory_vs_metabolic_test.tsv` — pre-registered headline test on KO category labels
- `data/p2_mycolic_acid_test.tsv` — pre-registered hypothesis verdict
- `data/p2_alm_2006_backtest.tsv` — TCS HK reproduction at KO level
- `data/p2_architectural_deepdive_candidates.tsv` — KOs with strong Producer × Participation signal (off-(low,low) at q<0.05 with effect size ≥0.3) AND ≥2 distinct Pfam architectures (the Phase-3 input)

### Phase 2 Gate to Phase 3 (quantitative thresholds, v2)

**Gate ordering**: M18 methodology gate runs first (substrate-hierarchy validation); hypothesis gates (Tier-1 headline + Tier-2 focal tests) run only if M18 passes.

- **M18 methodology gate (mandatory pre-hypothesis check)**: Phase 2 KO atlas demonstrates Cohen's d ≥ 0.3 on Sankoff parsimony / n_present for at least one positive HGT control class (β-lactamase, class-I CRISPR-Cas, or TCS HK) vs negative housekeeping (ribosomal, tRNA-synth, or RNAP core), with 95% bootstrap CI lower bound > 0 (M19). UniRef50 baseline is d = 0.146.
  - **If M18 fails**: substrate-hierarchy claim is falsified; halt for M11 redesign (gene-tree-vs-species-tree reconciliation per AleRax sub-sampling). Hypothesis gates do not run.
  - **If M18 passes**: proceed to hypothesis gates below.
- **Pass**: regulatory-vs-metabolic asymmetry test at KEGG BRITE B-level achieves Cohen's d ≥ 0.3 on producer or participation score at FWER<0.05 (Tier 1 headline test) AND Alm 2006 TCS HK reproduction at q<0.0125 (Tier 2 Bonferroni) → Phase 3 architectural deep-dive proceeds as generalization confirmation.
- **Pass reframed**: regulatory-vs-metabolic asymmetry **falsified** at KO level (Cohen's d < 0.3 or FWER fail) → Phase 3 reframes to "what *does* discriminate Innovator-Isolated from Innovator-Exchange?" using the deep-dive candidates. The strong-form regulatory-vs-metabolic prior is judged falsified for the headline; the atlas continues as descriptive resource.
- **Stop**: Alm 2006 TCS back-test fails at KO level (TCS HK paralog expansion not reproduced at q<0.0125 across Pseudomonadota / Bacillota) → halt; methodological failure to be diagnosed before any architectural analysis. This is distinct from the Phase 1A pilot back-test failure (which would have already stopped the project).

### Phase 2 Notebooks
9. `09_p2_ko_data_extraction.ipynb` — KO assignments from `eggnog_mapper_annotations`; UniRef90 nesting within KO; KEGG BRITE B-level category labels
10. `10_p2_ko_atlas.ipynb` — clade × KO producer/participation scores; category assignment; sanity rail using Phase-1B projection
11. `11_p2_regulatory_vs_metabolic_test.ipynb` — Tier-1 headline test on KEGG BRITE B-level category labels
12. `12_p2_mycolic_acid_test.ipynb` — pre-registered hypothesis verdict
13. `13_p2_alm_2006_backtest.ipynb` — TCS HK reproduction at KO scale
14. `14_p2_pfam_audit_spotcheck.ipynb` — early audit on TCS HK Pfams (PF00512, PF00072) and PSII Pfams (PF00124, PF02530, PF02533) for Phase 3 risk
15. `15_p2_phase_gate.ipynb` — gate decision + architectural deep-dive candidate selection

### Phase 2 Effort
~5 agent-weeks.

---

## Phase 3 — Architectural Resolution (Pfam architecture, donor-undistinguished per M25)

**Question** *(reframed at v2.11 per M25 data-availability constraint)*: Does the Producer × Participation structure survive at Pfam multidomain architecture resolution? At genus rank, do Innovator-Exchange tuples on the Phase-2 candidate set show coherent architectural patterns? *Note: Composition-based donor inference (codon-usage Δ, GC% Δ) was pre-registered at v2 but is deferred per M25 — per-CDS sequence data is not in BERDL queryable schemas. Phase 3 reports Innovator-Exchange (joint Broker OR Open) at genus rank without donor-vs-recipient separation.*

### Substrate
- **A. Function-class unit**: Pfam multidomain architecture (ordered set of Pfam domains)
- **B1. Within-clade family unit**: paralog-explicit; UniRef90 within architecture within clade
- **B2. Cross-clade orthology**: Pfam architecture identity (exact ordered match)
- **C. Direction inference** *(v2.11 reframe per M25)*: Phyletic-incongruence detects clade-pair acquisition events at all ranks (recipient-and-depth attribution per M22, NB10b). Composition-based donor inference at genus rank is **deferred** — per-CDS sequence composition (required for codon-usage Δ, GC% Δ, k-mer signatures) is not in BERDL queryable schemas. Phase 3 reports Innovator-Exchange (joint Broker OR Open Innovator at genus rank, donor-undistinguished). Same level of phylogenetic-origin claim Alm 2006 made.

### Bias Control Stack
- D1–D4 mandatory
- **Pfam audit** (mandatory pre-flight, *v2 citation correction*): For every architecture in the deep-dive candidate set, cross-check `bakta_pfam_domains` vs `eggnog_mapper_annotations.PFAMs`. The exact failure mode is **unresolved** in the BERDL docs: per docs/pitfalls.md `[plant_microbiome_ecotypes] bakta_pfam_domains query format — Pfam IDs may not match` (line 1719), querying `bakta_pfam_domains` with Pfam accessions like `'PF00771'` returned 0 hits across 11 domains tested, with the docs explicitly noting "*This pitfall needs further investigation to determine the correct query format.*" The audit must therefore test **both** possibilities: (a) format mismatch (PF00771 vs PF00771.1 vs domain name), and (b) genuine coverage gaps. Per the project memory note from `[plant_microbiome_ecotypes]`, 12 of 22 marker Pfams tested were silently missing from `bakta_pfam_domains` in that prior audit — this is what made the pitfall non-negotiable here. Flag any discrepancy >20%. Recompute via HMMER on `gene_cluster.faa_sequence` for any flagged headline architecture. *(v1 cited the wrong pitfall handle, `[bakta_reannotation]`, which in pitfalls.md actually refers to a MinIO-tenant naming issue. The adversarial reviewer caught this; the v2 citation is correct.)*
- **Phase 2 spot-check** (added in v2 per standard reviewer recommendation): Before Phase 2 ends, run the audit on TCS HK Pfam set (PF00512, PF00072) and on PSII Pfam set (PF00124, PF02530, PF02533) to surface any audit failures early. These are the architectures Phase 3 most depends on.
- UniRef50 robustness rail
- Sensitivity: PIC on producer scores; per-clade jackknife on architecture census

### Phase 2 Handoff Use
- `p2_architectural_deepdive_candidates.tsv` defines the architecture census target. Phase 3 does not run a full GTDB-scale Pfam architecture census; it runs the deep-dive on the candidate KOs from Phase 2. This makes Phase 3 ~30–40% cheaper than a standalone architectural atlas.

### Pre-registered Prediction (Phase 3, v2.11 reframe per M25)

**Cyanobacteria → Innovator-Exchange at genus rank for photosystem II Pfam architectures** (PF00124 + PF02530 + PF02533 set, plus extended PSII protein architectures). *v2 had pre-registered "Broker" specifically; v2.11 reframes to "Innovator-Exchange" (the joint Broker OR Open Innovator label, donor-undistinguished) per M25's deferral of composition-based donor inference. The biological interpretation is the same — high paralog expansion + high cross-clade exchange involvement on PSII at genus rank — minus the donor-vs-recipient distinction. Without donor inference, we cannot say whether Cyanobacteria are donor (Broker) or have acquired PSII variants from elsewhere (Sink with paralogs); the test verdict is the joint Innovator-Exchange label.*

**Prior strength**: WEAK.

**Reasoning**: PSII protein components are evolutionarily ancient and well-conserved within Cyanobacteria (low recent paralog expansion expected). The PSII assembly was donated to anoxygenic photosynthesis lineages (Chloroflexota) via documented ancient HGT. Both ingredients (low producer + high outflow) point to Broker rather than Open Innovator. **At genus rank, "Broker" specifically requires composition-based donor inference assigning Cyanobacteria as the donor in genus-rank Cyanobacteria↔Chloroflexota PSII transfers; if direction is reversed at genus rank, the verdict shifts to Sink.**

**Falsification**: At q<0.0125 (Bonferroni for 4 focal tests):
- Cyanobacteria producer score > 75th percentile of the atlas for PSII architectures (would shift to Innovator-Exchange / Open Innovator), OR
- Cyanobacteria participation score on PSII architectures is below the atlas median (would shift to Innovator-Isolated / Stable), OR
- Genus-rank donor inference identifies non-Cyanobacterial donors > Cyanobacterial donors for PSII Cyanobacteria↔Chloroflexota events at q<0.05 (would shift to Sink at genus rank, not Broker).

**Prior Calibration** (alternatives we cannot rule out):
- *Innovator-Exchange / Open Innovator at genus rank*: if Cyanobacteria show meaningful recent PSII paralog expansion (e.g., psbA copy variation across Synechococcus / Prochlorococcus lineages) above the clade-matched neutral-family null.
- *Innovator-Isolated / Closed Innovator at genus rank*: if the PSII outflow to Chloroflexota is older than our depth resolution and recent HGT is dominated by within-Cyanobacteria diversification.
- *Sink at genus rank*: highly unlikely given the established "PSII originated in Cyanobacteria" consensus, but it would be the verdict if Phase 3 donor inference identifies external donors. Listed for completeness.

**What we genuinely don't know**: Whether the Pfam-architecture grain captures PSII as a coherent unit (the assembly involves >20 distinct proteins; multiple architectures per PSII complex), and whether HMMER recompute will be needed for the headline Pfams. *Phase 2 spot-check (above) surfaces this risk before Phase 3 starts.*

### Phase 3 Output Products *(v2.11 reframe per M25)*
- `data/p3_pfam_completeness_audit.tsv` — pre-flight audit results comparing `bakta_pfam_domains` vs `interproscan_domains` coverage of curated marker Pfam set; substrate-decision rationale
- `data/p3_candidate_set.tsv` — Phase-2 atlas KOs with off-(low,low) Producer × Participation at q<0.05 + d ≥ 0.3 + ≥2 distinct Pfam architectures (the architectural deep-dive target)
- `data/p3_pfam_architecture_atlas.parquet` — clade × architecture producer/consumer scores on the candidate set
- `data/p3_pfam_architecture_categories.tsv` — Producer × Participation category assignments at architectural resolution (genus through phylum ranks)
- `data/p3_cyanobacteria_psii_test.tsv` — pre-registered hypothesis verdict (Innovator-Exchange test, donor-undistinguished per M25)
- `data/p3_alm_2006_architectural_backtest.tsv` — TCS HK Pfam architecture census within the candidate set; comparison to Phase-2 KO-level signal

**Dropped from v2 deliverables** (per M25): `p3_pfam_architecture_quadrants_genus.tsv` (donor-distinguished four-quadrant labels) and `p3_genus_rank_donor_inference.tsv` (composition-based donor inference with confidence intervals). Both required per-CDS sequence composition data not in BERDL queryable schemas.

### Phase 3 Gate to Phase 4 (quantitative thresholds, v2.11)
Unconditional, but with a quality threshold: Phase 4 synthesis treats Phase 3 architectural results as **confirmatory** (rather than exploratory) only when architectural-vs-KO concordance ≥ 60% on the Phase-2 candidate set. Below that, Phase 4 treats Phase 3 as exploratory commentary and the headline atlas claims rest on Phase 1B + Phase 2. Either way, synthesis runs.

### Phase 3 Notebooks *(v2.11 reframe per M25)*
- `13_p3_pfam_audit.py` — pre-flight audit of `bakta_pfam_domains` vs `interproscan_domains` Pfam coverage on curated marker set; substrate decision
- `14_p3_candidate_selection.py` — atlas filter (off-(low,low) at q<0.05 + d ≥ 0.3 + ≥2 architectures); candidate KO set produced
- `15_p3_architecture_census.py` — Pfam multidomain architecture per (genus × candidate-KO × architecture) using selected substrate (likely interproscan_domains)
- `16_p3_genus_rank_pp_at_architectural_resolution.py` — Producer × Participation at genus rank for architectural-resolution scoring on candidates (replaces v2's NB19 donor-inference notebook)
- `17_p3_cyanobacteria_psii_test.py` — pre-registered Cyanobacteria × PSII Innovator-Exchange test
- `18_p3_alm_2006_architectural_backtest.py` — TCS HK Pfam architecture census + Alm 2006 paralog-signal reproduction at architectural resolution (genus + family ranks)
- `19_p3_phase_gate.py` — Phase 3 → Phase 4 gate verdict + concordance with Phase 2 KO atlas

### Phase 3 Effort *(v2.11 reframe per M25)*
**~3-5 days** (reduced from ~5 weeks due to M25 deferral of composition-based donor inference). Pre-flight audit ~1 hour; candidate selection ~1 hour; architecture census ~4-8 hours; genus-rank P × P ~1 day; Cyanobacteria PSII test ~1 day; TCS HK Alm back-test ~1 day; Phase 3 → Phase 4 gate ~1 day.

---

## Phase 4 — Cross-Resolution Synthesis

**Question**: At which resolutions and for which clades × function classes do the **Producer × Participation category assignments** concord (Phase 1B + Phase 2 + Phase 3 deep-rank) AND where Phase 3 genus-rank donor inference resolves the full four-quadrant labels — what is the resulting atlas verdict? Where resolutions conflict, what does the conflict reveal?

*v2 reframe: Phase 4 must explicitly distinguish deep-rank Producer × Participation atlas assignments (which span all three resolutions and all ranks) from genus-rank full-quadrant labels (which exist only in Phase 3 on the candidate set). The synthesis report has two parallel threads: a deep-rank atlas and a genus-rank quadrant table.*

No new data extraction. Phase 4 joins Phase 1 / 2 / 3 outputs.

### Phase 4 Output Products

**Core synthesis (original v2 deliverables)**:
- `data/p4_deep_rank_concordance.tsv` — for each (clade × function-class) tuple represented at ≥2 resolutions (Phase 1B UniRef50 / Phase 2 KO / Phase 3 architecture), list Producer × Participation category at each resolution + concordance score
- `data/p4_genus_rank_quadrants.tsv` — full four-quadrant labels (Open / Broker / Sink / Closed) on the Phase-3 candidate set at genus rank only, with Phase-3 donor-inference confidence intervals
- `data/p4_concordance_weighted_atlas.parquet` — final atlas with confidence weights from cross-resolution agreement
- `data/p4_conflict_analysis.tsv` — clade × function tuples where resolutions disagree, with hypotheses for why
- `data/p4_pre_registered_verdicts.tsv` — four pre-registered hypotheses (Phase 1B: Bacteroidota PUL; Phase 2: Mycobacteriota mycolic-acid; Phase 3: Cyanobacteria PSII; Phases 2+3: Alm 2006 TCS back-test) as supported / falsified / equivocal with explicit evidence

**v2.9 atlas-as-flow-and-acquisition deliverables (P4-D1..D5)**:
- **P4-D1 phenotype/ecology grounding** ✅ *closed v2.14 — three of three pre-registered atlas findings grounded*:
  - **Substrates** (corrected after pangenome-internal audit): `pangenome.ncbi_env` (4.1M EAV rows; 76.8% isolation_source, 88.8% geo_loc_name, 48.6% env_broad_scale, 47.3% lat_lon coverage); `pangenome.alphaearth_embeddings_all_years` (5,157 species, 64-dim quantitative env vectors); `kescience_mgnify.species` (5,392 species, 18 biome categories); BacDive (6,066 species via GCF→GCA fallback)
  - `data/p4d1_env_per_species.parquet` — joined per-species env table (18,992 × 97 cols)
  - `data/p4d1_biome_enrichment_tests.tsv` — Fisher's enrichment per pre-registered hypothesis (Cyanobacteriia × marine 2.77× p<10⁻⁵²; Mycobacteriaceae × host-pathogen 7.88× p<10⁻⁴⁵; Bacteroidota × gut/rumen 1.40× p<10⁻³⁵)
  - `data/p4d1_bacdive_*_per_species.parquet` (×3) — phenotype anchors confirming mycobacterial aerobic-rod and Bacteroidota saccharolytic profiles
  - `data/p4d1_alphaearth_clusters.tsv` — k=10 env-cluster assignment with biome interpretability
  - `data/p4d1_diagnostics.json`, `data/p4d1_bacdive_diagnostics.json`, `data/p4d1_alphaearth_diagnostics.json`
  - `figures/p4d1_clade_biome_panel.png`, `figures/p4d1_bacdive_phenotype_panel.png`, `figures/p4d1_alphaearth_env_cluster_panel.png`

- **P4-D2 MGE context per gain event** ✅ *closed v2.15 — pre-registered atlas KOs not phage-borne*:
  - `data/p4d2_ko_genus_mge.parquet` — per (KO × genus) MGE-machinery fraction (3.9M rows)
  - `data/p4d2_recent_gain_mge_attributed.parquet` — per recent-gain MGE-machinery (atlas-wide)
  - `data/p4d2_diagnostics.json` — atlas 1.37%; mycolic 0.57%; PSII 0%; PUL 0%
  - `data/p4d2_neighborhood_psii_per_feature.parquet` — PSII gene-neighborhood result (26,864 features; 10.91% with ≥1 MGE neighbor = at random baseline)
  - `data/p4d2_neighborhood_psii_diagnostics.json` — per-PSII-KO MGE-neighbor breakdown (PsbZ 22.1% to PsbV 3.5%)
  - `figures/p4d2_mge_context_panel.png` — per-category, per-hypothesis, per-biome MGE rates
  - `genomad_mobile_elements` is **NOT** ingested in BERDL (catalog-verified); bakta_annotations.product keyword matching is the only available signal
  - PUL/mycolic gene-neighborhood at scale deferred — pandas spatial-range merge OOM at 10M+ rows; per-cluster MGE-machinery (0%/0.57%) suffices for the headline conclusion

- **P4-D3 Alm 2006 r ≈ 0.74 reproduction** ✅ *closed v2.12 — NOT REPRODUCED*:
  - `data/p4d3_per_species_hpk_lse.tsv` — per-species: HPK count (PF00512 hits via interproscan_domains) + recent-LSE fraction (M22-derived); n=18,989
  - `data/p4d3_correlations.tsv` — four framings of the Alm correlation: r = 0.10–0.29 (Pearson), 0.11–0.33 (Spearman); strongest: HPK count vs recent TCS gains at genus rank
  - `data/p4d3_diagnostics.json` — verdict: NOT REPRODUCED. Methodology generalization holds (NB17 architectural concordance r = 0.67); point estimate does not survive scaling 207 → 18,989

- **P4-D4 within-species pangenome openness cross-validation** ✅ *closed v2.13 — informative null at atlas scale*:
  - `data/p4d4_pangenome_openness_per_genus.tsv` — per-genus mean openness across multi-genome species (3,539 genera with ≥1 multi-genome species)
  - `data/p4d4_recent_acquisition_vs_openness.tsv` — joined table at per-genus level for the 894-genera solid substrate (≥3 multi-genome species per genus)
  - `data/p4d4_diagnostics.json` — T1 atlas-wide Spearman r = −0.011 (894 genera, null); T2 class-stratified null; T3a Mycobacteriaceae × mycolic r = +0.46 (n=10, CI spans 0); T3b Cyanobacteriia × PSII r = +0.11 (n=83, CI spans 0)
  - `figures/p4d4_openness_vs_acquisition.png` — 4-panel scatter
  - **Interpretation**: M22 lineage-level gain attribution and within-species pangenome openness measure distinct evolutionary phenomena; openness is not a valid cross-substrate validation of M22

- **P4-D5 annotation-density residualization** ✅ *closed v2.12 — all hypothesis verdicts survive*:
  - `data/p4d5_residualized_atlas.parquet` — atlas scores both raw and D2-residualized (13.7M rows; 4 z-scaled covariates: clade_size, mean_annotated_fraction, mean_gc, mean_genome_size)
  - `data/p4d5_diagnostics.json` — predictor coefficients + R² (producer R² = 0.000; consumer R² = 0.053; annotation-density coef = −1.27 on consumer)
  - `data/p4d5_hypothesis_replication.tsv` — NB11/NB12/NB16 raw vs residualized Cohen's d; all directions and significances preserved (max attenuation 16% relative on NB12 family consumer)
  - `figures/p4d5_residualization_panel.png` — producer/consumer raw vs residualized scatter + per-test d comparison

**Figures**:
- `figures/p4_atlas_heatmap.png` — clade × function-class Producer × Participation heatmap (deep-rank, all ranks)
- `figures/p4_genus_rank_flow_network.png` — directed clade-to-clade function-flow graph at genus rank only (Phase-3 candidate set)
- `figures/p4_four_quadrant_summary.png` — named clades populating each quadrant at genus rank
- `figures/p4d1_environment_enrichment_panel.png` — function-class × environment enrichment heatmap
- `figures/p4d1_clade_phenotype_anchors.png` — clade × phenotype anchoring at the species level
- `figures/p4d2_mge_context_fraction.png` — per (clade × function-class) MGE-context fraction
- `figures/p4d3_alm_r_reproduction_scatter.png` — HPK-count vs recent-LSE scatter at three resolutions, with r and 95% CI annotated; Alm 2006 r=0.74 reference line
- `figures/p4d4_pangenome_openness_acquisition_scatter.png` — recent-acquisition rate vs pangenome openness at species level
- `figures/p4d5_residualization_atlas_diff.png` — raw vs residualized atlas score difference per (rank × function-class)

- `REPORT.md` — final synthesis writeup with explicit deep-rank vs genus-rank claim separation, plus phenotype/ecology interpretation per P4-D1, MGE-mechanism dimension per P4-D2, Alm reproduction verdict per P4-D3.

### Phase 4 Notebooks (v2.9 expansion)
21. `21_p4_cross_resolution_concordance.ipynb` — Producer × Participation category-assignment join across Phase 1B / 2 / 3
22. `22_p4_atlas_visualization.ipynb` — deep-rank heatmap + genus-rank directed network + four-quadrant summary at genus rank
23. `23_p4d1_phenotype_ecology_grounding.ipynb` — NMDC + MGnify + GTDB metadata environment join; BacDive + WoM phenotype join; Fitness Browser cross-check
24. `24_p4d2_mge_context_per_gain.ipynb` — bakta_annotations + genomad_mobile_elements MGE flagging; per-event tagging + per-class aggregation
25. `25_p4d3_alm_r074_reproduction.ipynb` — explicit r computation at three resolutions; comparison to Alm 2006
26. `26_p4d4_pangenome_openness_validation.ipynb` — per-species openness vs recent-acquisition cross-validation
27. `27_p4d5_annotation_density_residualization.ipynb` — D2 closure; residualized atlas
28. `28_p4_synthesis_writeup.ipynb` — pre-registered verdicts, conflict analysis, final figures, deep-rank vs genus-rank claim separation, P4-D1..D5 interpretation

### Phase 4 Effort
~4 agent-weeks (was 2 weeks pre-v2.9). Core synthesis ~2 weeks; P4-D1 phenotype/ecology ~1-2 weeks; P4-D2/D3/D4/D5 ~1 week combined.

---

## Data Sources

### BERDL tables (`kbase_ke_pangenome` unless noted)

**Core scaffold + sequence layer:**
- `genome` (293K rows) — genome → gtdb_species_clade_id, has_sample
- `gtdb_taxonomy_r214v1` (293K rows) — full lineage per genome
- `gtdb_metadata` (293K rows) — CheckM completeness, contamination, GC%, assembly level
- `gtdb_species_clade` (28K rows) — clade-level ANI stats; provides `representative_genome_id` for D1 dedup
- `pangenome` (28K rows) — per-species pangenome stats (no_genomes, no_core, no_aux, no_singleton, no_gene_clusters)
- `gene_cluster` (133M rows) — cluster representatives, faa_sequence, fna_sequence, isCore/isAccessory/isSingleton
- `gene_genecluster_junction` (1B rows) — genome → gene_cluster_id (filter required, never full-scan)
- `bakta_db_xrefs` (572M rows; UniRef tier = 242M of these) — gene_cluster_id → UniRef50/UniRef90/UniRef100 (split by accession prefix; `db = 'UniRef'` is a single value, tier embedded in `accession`); disable autoBroadcast on `kbase_uniprot.uniprot_identifier` joins
- `bakta_amr` (83K rows) — AMR positive control source
- `kbase_uniref50` / `kbase_uniref90` / `kbase_uniref100` (100K / 100K / 260K rows) — UniRef cluster reference tables; cluster size, representative, taxonomy

**Functional annotation layer (v2 substrate audit, 2026-04-26):**
- `eggnog_mapper_annotations` (94M rows) — KO, COG, EC, KEGG_Pathway, KEGG BRITE per cluster. **Caveat**: `PFAMs` column stores domain *names* (`HisKA`), not accessions (`PF00512`); per docs/pitfalls.md `[snipe_defense_system]`. Used for KO-anchored annotation; not authoritative for Pfam.
- **`interproscan_domains` (833M rows; Pfam = 146M)** — *the authoritative Pfam annotation source on BERDL.* 18 member databases (Pfam, Gene3D, SUPERFAMILY, PANTHER, CDD, NCBIfam, etc.) with `signature_acc` (proper accession), `ipr_acc` (InterPro entry), `ipr_desc` (description). 83.8 % cluster coverage. **Primary source for Pfam-based control detection in NB01 v2 onward; primary source for Phase 3 architecture census.**
- **`interproscan_go` (266M rows)** — deduplicated GO term assignments per cluster from InterPro and PANTHER. Used for Phase 2 cross-validation of regulatory-vs-metabolic at GO BP level.
- **`interproscan_pathways` (287M rows)** — deduplicated MetaCyc + KEGG pathway assignments. Alternative pathway annotation independent of eggNOG.
- `bakta_pfam_domains` (19M rows) — *fallback only.* Per docs/pitfalls.md `[plant_microbiome_ecotypes] bakta_pfam_domains query format`, this table has unresolved coverage/format issues. Used as audit comparison in Phase 3, not as primary source.
- `bakta_annotations` — broader bakta annotation table; reserved for Phase 2/3 if needed.

**Phase-2/3-reserved layers:**
- `gapmind_pathways` (305M rows) — pathway profiles for amino acid biosynthesis and carbon utilization; Phase 2 metabolic-pathway annotation
- `phylogenetic_tree` / `phylogentic_tree_distance_pairs` — per-species trees + within-species distances; D4 topology-support filter and Phase 4 atlas annotation
- `genome_ANI` (421M rows) — pairwise within-species ANI; used for ANI-stratified within-species sampling per the Within-Species Genome Sampling Strategy section
- `ncbi_env` (4M rows) — environmental metadata; advisory annotation only (per the rejected-alternative-framings section in DESIGN_NOTES.md, niche stratification is not a primary axis)

### External
- **GTDB r214 species tree** (newick) — downloaded externally from `https://data.gtdb.ecogenomic.org/releases/release214/`. Loaded into project for topology-support filtering at the rank level. Not stored in BERDL.
- **HMMER** (last-resort tool) — for Pfam recompute on architectures flagged by the Phase 3 audit.
- **AleRax** (Morel et al. 2024) — held in reserve for principled subsamples only; not used at full GTDB scale per constraint.

### Cross-database joins
- `eggnog_mapper_annotations.query_name` ↔ `gene_cluster.gene_cluster_id`
- `bakta_db_xrefs.gene_cluster_id` ↔ `gene_cluster.gene_cluster_id`
- `gene_genecluster_junction.gene_cluster_id` ↔ `gene_cluster.gene_cluster_id`
- `gene_genecluster_junction.gene_id` ↔ via `kbase_genomes.name` if needed
- GTDB lineage: `gtdb_taxonomy_r214v1` parsed to species / genus / family / order / class / phylum / domain rank scaffold

## Query Strategy

### Performance Plan
- **Tier**: Direct Spark on BERDL JupyterHub (on-cluster). REST API not used for headline queries.
- **Spark session import** (on-cluster JupyterHub notebooks): `spark = get_spark_session()` with **no import** — `get_spark_session` is injected by `/configs/ipython_startup/00-notebookutils.py`. CLI scripts on the same cluster require the explicit `from berdl_notebook_utils.setup_spark_session import get_spark_session` form. (See docs/pitfalls.md "Use the Right Import for Your Environment".)
- **Per-phase query pattern commitments**:
  - **Phase 1A (pilot)**: Pattern 1 (single IN-clause query) on the pilot subset; Pattern 2 (per-species iteration) for any per-species exploratory queries
  - **Phase 1B (full scale)**: Pattern 2 (per-species iteration) for gene-level extraction, batched across species reps; Pattern 1 (IN-clause) for UniRef50 lookups within batches
  - **Phase 2**: Pattern 1 (IN-clause) for KO-subsetted aggregations across species; Pattern 2 (per-clade iteration) for per-clade scoring
  - **Phase 3**: Pattern 1 (IN-clause) for architecture census on candidate set; per-event composition-based inference at genus rank only (small N, no batching needed)
- **Species ID `--` handling**: All phases use **exact equality** with quoted strings (`WHERE gtdb_species_clade_id = 's__Escherichia_coli--RS_GCF_000005845.2'`) for known species reps. LIKE with prefix (`'s__Escherichia_coli%'`) is used only for exploratory grouping where the genome accession suffix is not pinned. Inside quoted strings, `--` is treated as data, not a SQL comment.
- **Critical pitfalls** (from docs/pitfalls.md):
  - Never full-scan `gene` (1B), `gene_genecluster_junction` (1B), `genome_ani` (421M), `bakta_db_xrefs` (572M)
  - Disable autoBroadcast on `kbase_uniprot.uniprot_identifier` joins (`SET spark.sql.autoBroadcastJoinThreshold = -1` before the join, restore after) to avoid maxResultSize errors
  - Cast string-typed numeric columns before comparison
- **Materialization**: per-phase intermediate parquet under `data/` for re-entrant analysis; Phase 1 outputs are read-only inputs to Phase 2; Phase 1+2 outputs are read-only inputs to Phase 3; all phases are read-only inputs to Phase 4

### Within-Species Genome Sampling Strategy

**The D1 "one genome per species" rule applies to the cross-species atlas — 27,690 GTDB representatives for the headline analysis.** Within-species analyses (rarefaction sensitivity, within-species ANI null calibration, per-species pangenome diagnostics) use multiple genomes per species capped at 500 per docs/performance.md ANI guidance. *Naive random sampling biases against species like* E. coli (~10K genomes, predominantly clinical isolates near-clonal), K. pneumoniae (~14K, similar bias), and S. aureus (~14K). *The plan therefore commits to a stratified sampling protocol:*

**Step 1 — Quality filter** (always applied first):
- CheckM completeness ≥ 95%
- CheckM contamination ≤ 5%
- Assembly level ≥ "scaffold" (drop "contig" assemblies for within-species analyses)
- Drop NCBI-flagged assemblies (per `gtdb_metadata`)

**Step 2 — ANI-stratified subsampling** (when post-filter genome count > 500):
- Compute within-species ANI quantiles (10 bins by mean pairwise ANI to species centroid)
- Target 50 genomes per bin uniform-random; if a bin has fewer, take all and reallocate the residual to fuller bins
- Always include the GTDB species representative

**Step 3 — Validation** (once per species):
- Compare paralog count distribution between full set and subsampled set on a held-out function class (e.g., ribosomal proteins, expected to be invariant) — within ±10% tolerance
- If failed, increase cap to 1,000 for that species; if still failed, flag for per-species review

**Implementation note**: ANI quantiles are derived from `genome_ani` filtered to within-species pairs. For species where the within-species ANI table is itself too large (>500 reps × 500 reps = 250K pairs), use the GTDB-r214 representative-vs-cluster-member distances available in `gtdb_species_clade` (clade-level summary), then refine with a single sweep over the filtered genome set.

**Negative example (what not to do)**: random uniform sampling of 500 from 14K *S. aureus* genomes draws ~80% MRSA / clinical isolates, missing the rumen, marine, and environmental sub-lineages whose paralog distributions differ. ANI stratification + GTDB-rep inclusion fixes this.

### Null Model Specification (the methodological core)

The phrase "tree-aware null" in the original brief hides several distinct null models. This plan commits to specific implementations with pseudocode, complexity estimates, and pilot validation in Phase 1A. *The v2 revision (in response to adversarial review C4) adds the pseudocode and complexity sections; v1 committed only to the null type, which was insufficient.*

#### Producer null — clade-matched neutral-family null

For each (clade C, function class F), expected paralog count is drawn from function classes with matched within-C prevalence:

```
def producer_score(C, F, P=1000):
    # Observed: distinct UniRef90 clusters within F in clade C
    N_obs = count_unique_uniref90(C, F)

    # Match: function classes with the same number of present species in C
    prevalence = count_present_species(C, F)
    matched_pool = {F' : count_present_species(C, F') == prevalence and F' != F}

    null_dist = []
    for k in range(P):
        F_null = random_sample(matched_pool, 1)
        N_null = count_unique_uniref90(C, F_null)
        null_dist.append(N_null)

    return (N_obs - mean(null_dist)) / std(null_dist)   # z-score
```

**Complexity**: O(C × F × P). Phase 1A pilot (1K species × 1K UniRef50s × 1000 perms) = 10⁹ ops; tractable in single-digit hours on the BERDL cluster. Phase 1B full (35K clades × ~100K UniRef50s × 1000 perms) = 3.5×10¹² naive — reduction tricks below.

**Reduction tricks (mandatory for Phase 1B)**:
- Pre-bin function classes by within-C prevalence once per C; sample from bins instead of recomputing matches per F.
- Compute null distributions per (C, prevalence-bin) once and lookup; this collapses the inner loop from O(F) to O(prevalence-bins) per C.
- Use Bayesian bootstrap for asymptotic z-score estimation beyond P=1000 when the null distribution is well-behaved (verified in Phase 1A).

Net effective complexity after reduction: O(C × F + C × P × bins) ≈ O(35K × 100K + 35K × 1000 × 50) = 5.25×10⁹ operations — feasible.

#### Consumer null — phyletic-distribution permutation null

For each (clade C, function class F), expected acquisition incongruence is drawn from random permutations of presence pattern:

```
def consumer_score(C, F, P=1000):
    # Observed: presence vector across all clades at depth d (binary)
    presence_obs = presence_vector(F, depth=d)   # length = N_clades_at_d
    k = sum(presence_obs)
    incong_obs = sum_over_pairs(species_tree_dist(c1, c2) * |presence_obs[c1] - presence_obs[c2]|)

    null_dist = []
    for i in range(P):
        presence_null = random_permutation(presence_obs)   # preserves k
        incong_null = sum_over_pairs(species_tree_dist(c1, c2) * |presence_null[c1] - presence_null[c2]|)
        null_dist.append(incong_null)

    z = (incong_obs - mean(null_dist)) / std(null_dist)
    # acquisition_count(C) = number of F where C is in the high-incongruence subset
    return z
```

**Complexity**: O(F × P × pairs). Pairs grow as N_clades². At depth=family (~1.5K clades), pairs ≈ 1.1M; at depth=phylum (~80 clades), pairs ≈ 3K. Per-F per-perm cost is acceptable.

**Reduction trick**: incongruence permutation is a well-known graph statistic with closed-form moments under uniform permutation; use Z-statistic + analytic CI for tails, falling back to Monte Carlo only when the analytic approximation fails normality.

#### Participation score (the deep-rank surrogate for "outflow")

*Added in v2.* At family rank and above, "outflow" cannot be cleanly distinguished from "inflow" without direction. The plan replaces clade-level outflow with **participation**:

```
def participation_score(C):
    # Count function classes where C has high consumer score AND
    # at least one other clade also has high consumer score for the same F
    pairs = [(C, C') for C' if abs(consumer_score(C', F)) > 2 and abs(consumer_score(C, F)) > 2 for F]
    return len(unique_F_in(pairs))
```

Participation = "Number of function classes where C is involved in incongruent transfers AND at least one other clade is also involved." This is the bidirectional analog of outflow and does not require donor-recipient assignment.

#### Topology-support filter (D4)

A function-class event is only called at the deepest rank where:
1. The GTDB tree's node support at that rank exceeds 0.7 (when the GTDB-r214 newick is loaded; rank-level since global tree is not in BERDL)
2. The rank's effective N is ≥ 10 distinct sub-clades with that function class
3. Below either threshold, the event is dropped from depth stratification but still counted in the flat tally

#### Annotation-density covariate (D2)

Per-genome annotated-fraction is residualized out via OLS *before* score computation, not after. The OLS regresses observed-paralog-count on (clade-size, annotated-fraction, GC%, genome-size) and uses residuals for the producer score.

These choices are committed at plan-time because methodological vagueness on the null model is the most likely route to a non-falsifiable atlas (per critique #2 in DESIGN_NOTES.md). **Phase 1A pilot validates the producer and consumer nulls on the Alm 2006 TCS HK subset before scaling — if the pilot does not reproduce Alm 2006's HK paralog expansion at q<0.05, the null model is broken and the project halts for diagnosis.**

---

### Multiple-Testing Strategy

*Added in v2 in response to adversarial review C3.* Naive per-(clade × function) testing across the atlas yields ~10⁸–10¹⁰ tests after D4 filtering, which makes per-test FWER correction either uninformative (Bonferroni at α=10⁻¹¹) or vacuous (BH-FDR with no scientific anchor). The plan therefore uses **hierarchical testing with a small set of pre-registered focal tests**:

#### Tier 1 — Headline science claim (1 test, FWER<0.05)

Regulatory-vs-metabolic comparison at KEGG BRITE B-level:
- Regulatory = `09120 Genetic Information Processing` + `09130 Environmental Information Processing`
- Metabolic = `09100 Metabolism`
- Test: two-sample comparison of mean producer score across function classes, separately for each clade rank, weighted by per-clade effective N.
- Significance: Cohen's d ≥ 0.3 on at least one of (producer score, participation score) at α=0.05.

#### Tier 2 — Pre-registered focal tests (4 tests, Bonferroni α=0.0125)

1. Bacteroidota PUL CAZymes (Phase 1B)
2. Mycobacteriota mycolic-acid pathway (Phase 2)
3. Cyanobacteria PSII architectures (Phase 3)
4. Alm 2006 TCS HK reproduction (Phase 2 + Phase 3 architectural)

Each tested at Bonferroni-corrected α=0.05/4 = 0.0125.

#### Tier 3 — Atlas-level exploration (descriptive)

Per-(clade × function) producer/participation scores reported as effect sizes with 95% bootstrap CIs. BH-FDR q<0.05 reported as a marker of "atlas hits worth follow-up," not as confirmed claims. The atlas is treated as a **hypothesis-generating resource**, not a confirmed-finding inventory at the per-tuple level. Any per-tuple claim downstream of the atlas requires independent validation.

#### Effective number of independent tests

Tests within the same KEGG BRITE B-level category, within the same GTDB family, are non-independent. The plan applies a simple cluster correction: divide the per-tuple p-value count by the median number of tests per (BRITE-B × GTDB-family) cluster (~5–20), yielding effective N independent tests on the order of 10⁶–10⁸. This affects the BH-FDR threshold at Tier 3 only; Tiers 1 and 2 are pre-registered and not affected.

---

### Controls (Positive and Negative)

*Added in v2 in response to adversarial review constructive recommendations.* Each phase runs both a positive and a negative control set alongside the headline analysis. Controls are not gating; they are reported alongside results to confirm that the methodology detects what it should (and does not detect what it should not).

#### Negative controls (expected: low producer, low participation, on-diagonal across all clades)

Each control set is detected via a **union** of two annotation paths to maximize recall:

- **Ribosomal proteins**:
  - **Primary**: `interproscan_domains` where `LOWER(ipr_desc) LIKE '%ribosomal protein%'` OR `LOWER(signature_desc) LIKE '%ribosomal protein%'` (catches all subunits across 18 InterPro member DBs)
  - **Cross-check**: KEGG `ko03010` (Ribosome) via `eggnog_mapper_annotations.KEGG_ko`
- **tRNA synthetases**:
  - **Primary**: `interproscan_domains` where `LOWER(ipr_desc) LIKE '%aminoacyl-trna synthetase%'` OR `LOWER(signature_desc) LIKE '%trna ligase%'`
  - **Cross-check**: KEGG K01866–K01890 (canonical aminoacyl-tRNA synthetase KOs)
- **RNA polymerase core subunits**:
  - **Primary**: `interproscan_domains` where `LOWER(ipr_desc) LIKE '%rna polymerase%alpha%'` OR `'%rna polymerase%beta%'`
  - **Cross-check**: KEGG K03040 (rpoA), K03043 (rpoB), K03046 (rpoC)

If any of these show producer score > 1 σ above the global mean in any major phylum, the method is over-detecting paralog expansion and the null model needs recalibration.

#### Positive controls (expected: detectable acquisition signal in clades known to have acquired via HGT)

- **Antibiotic-resistance gene families**: `bakta_amr.gene_cluster_id` join (curated AMRFinderPlus hits). Expected to show high consumer / participation scores in clades with documented AMR HGT (Enterobacteriaceae, Acinetobacter, Pseudomonadaceae). *Pool coverage in pilot is ~70 %, biologically expected since environmental and uncultivated lineages have less AMR.*
- **Alm 2006 TCS HKs**: `interproscan_domains` filtered to `analysis = 'Pfam' AND signature_acc IN ('PF00512', 'PF07568', 'PF07730', 'PF06580', 'PF02518', 'PF13415', 'PF13581')` (HisKA family + HATPase + dimer domains). Cross-checked with `eggnog_mapper_annotations.PFAMs` domain-name match. The methodological gold standard for the back-test.
- **CRISPR-Cas systems**: *dropped from v2 control set as primary* (Pfam-name detection too noisy across the heterogeneous Cas family). Will revisit at Phase 3 if needed.

If any positive control fails to show acquisition signal in clades with documented HGT history, the consumer-score implementation is under-sensitive.

#### Why the v2 substrate audit matters

The v1 NB01 control detection used `eggnog_mapper_annotations.PFAMs` (domain *names*) for TCS HK detection. This was structurally fragile because the `PFAMs` column has a known name-vs-accession quirk and not every cluster has eggNOG annotation. The v2 switch to `interproscan_domains` provides:

1. **Authoritative accession-based queries** (PF00512 not "HisKA")
2. **146 M Pfam hits** vs `bakta_pfam_domains`'s 19M (the latter has known incomplete coverage per docs/pitfalls.md)
3. **83.8 % cluster coverage** for any InterPro hit
4. **Reusable substrate** for Phase 3 architecture census without reworking the control framework

The v2 detection takes the **union** of eggNOG-name and InterProScan-accession paths so we maximize recall while preserving the v1 cross-validation signal.

## Analysis Plan

23 numbered notebooks across 4 phases (Phase 1 split into 1A pilot + 1B full scale in v2). Notebook prefix encodes phase (`p1a_` / `p1b_` / `p2_` / `p3_` / `p4_`). All notebooks committed with saved outputs (BERIL hard requirement). Each phase ends with a phase-gate notebook that summarizes the decision and produces the handoff data file consumed by the next phase.

### Inter-Phase Reproducibility Contract
- All Phase-N outputs are written to `data/pN_*.parquet` or `data/pN_*.tsv`
- Phase-(N+1) notebooks must declare their Phase-N input dependency in the header markdown cell
- No Phase-(N+1) notebook reads from a Phase-N notebook directly; the only inter-phase contract is the file products listed in this plan

## Expected Outcomes (per phase)

### Phase 1A pilot
- **Pass**: positive controls hit signal at q<0.0125 (AMR / CRISPR-Cas / Alm 2006 TCS); negative controls (ribosomal / tRNA-synthetase / RNAP) stay on-diagonal; Alm 2006 TCS HK paralog reproduction confirmed at pilot scale. Phase 1B proceeds.
- **Recalibrate**: ≤2 control failures → null model recalibration on pilot, retry Phase 1A. Up to two recalibration cycles.
- **Stop**: persistent control failure → halt project; publish methodology + pilot results as a negative result on the framework's foundational signal at scale.

### Phase 1B
- **If H1 (strong-form)**: Bacteroidota → Innovator-Exchange on PUL UniRef50s; ≥10% of (clade × UniRef50) tuples in Innovator-Exchange or Innovator-Isolated category at q<0.05 with effect size ≥0.3. Sets up Phase 2 strong-form regulatory-vs-metabolic test.
- **If H0 reframed (structure exists, Bacteroidota PUL falsified)**: ≥10% off-(low,low) but Bacteroidota PUL is **not** Innovator-Exchange. The strong-form regulatory-only prior is already weakened; Phase 2 reframes empirically.
- **If H0 (no structure)**: ≥90% of tuples on the (low,low) Stable cell. Project halts at Phase 1B with publishable negative result on the diagonal-collapse fallback.

### Phase 2
- **If H1**: regulatory-vs-metabolic asymmetry confirmed (Cohen's d ≥ 0.3 on producer or participation score at FWER<0.05) AND Mycobacteriota mycolic-acid → Innovator-Isolated AND Alm 2006 TCS reproduction at q<0.0125. Sets up Phase 3 generalization confirmation.
- **If H0 reframed**: asymmetry not confirmed but specific clade × KO patterns are real. Phase 3 reframes to "what *does* discriminate Innovator-Isolated from Innovator-Exchange?" using deep-dive candidates.
- **If methodological failure**: Alm 2006 TCS back-test fails at KO level (q≥0.0125) → halt for diagnosis. This is distinct from the Phase 1A pilot back-test failure (which would have already stopped the project earlier).

### Phase 3
- **If H1**: Cyanobacteria → Broker at genus rank on PSII architectures AND TCS reproduction holds at architecture level (genus + family rank) AND ≥60% concordance between Phase 2 KO categories and Phase 3 architecture categories on candidate set. Atlas is internally consistent across all three resolutions.
- **If discordant**: architecture-level result conflicts with KO-level (concordance <60%). Phase 4 treats Phase 3 as exploratory commentary; headline atlas claims rest on Phase 1B + Phase 2.
- **If donor inference fails**: composition-based donor inference at genus rank produces wide CIs across most events. Phase 3 quadrant labels are reported with low confidence; Producer × Participation categories at deep ranks are the primary verdicts.

### Phase 4
- **Final atlas (deep-rank)**: clade × function-class Producer × Participation category assignments at three resolutions (Phase 1B UniRef50, Phase 2 KO, Phase 3 architecture), with cross-resolution concordance/conflict map.
- **Final atlas (genus-rank)**: full four-quadrant labels (Open / Broker / Sink / Closed) on the Phase-3 candidate set at genus rank only, with Phase-3 donor-inference confidence intervals.
- **Four pre-registered verdicts** (Bacteroidota PUL / Mycobacteriota mycolic-acid / Cyanobacteria PSII / Alm 2006 TCS back-test) as supported / falsified / equivocal with explicit evidence.
- **Falsifiable production**: even where pre-registered verdicts are falsified, the atlas produces concrete falsifiable category and (at genus rank) quadrant verdicts on clades × functions where no quantitative prior currently exists (per the "weak prior" framing in DESIGN_NOTES.md). The atlas is a hypothesis-generating resource for downstream targeted validation.

## Potential Confounders

- **EggNOG annotation density** (the dominant confounder): mitigated via three-resolution design and explicit D2 residualization.
- **CPR / DPANN under-representation**: acknowledged scope limit. Atlas does not claim coverage of poorly-sampled lineages at deep ranks. D3 effective-N reporting flags this per phase.
- **Reference genome inflation within species**: mitigated via D1 (one genome per species before scoring).
- **GTDB topology weak support at deep ranks**: mitigated via D4 rank-level support filter.
- **UniRef cluster boundary instability across UniRef releases**: mitigated by committing to UniRef release version at start; rerun would change Phase 1 output.
- **Pfam-completeness in `bakta_pfam_domains`**: mitigated via Phase 3 mandatory audit + HMMER recompute fallback.
- **Direction inference at deep ranks**: not attempted (acknowledged limit, not confounder).

## Total Budget

| Phase | Effort | Cumulative | Stop point? |
|---|---|---|---|
| Phase 1A pilot | ~1 week | 1 | Yes — methodology validation; halt-or-recalibrate gate |
| Phase 1B full | ~4 weeks | 5 | Yes — publishable existence test |
| Phase 2 | ~5 weeks | 10 | Yes — publishable functional atlas |
| Phase 3 | ~1 week | 11 | Architectural deep-dive (v2.11 reframe per M25: drops composition-based donor inference; Innovator-Exchange-only at genus rank) |
| Phase 4 | ~4 weeks | 15 | Final synthesis (v2.9 expansion: P4-D1 phenotype/ecology grounding, P4-D2 MGE context, P4-D3 Alm r=0.74 reproduction, P4-D4 pangenome openness validation, P4-D5 annotation-density residualization) |

**Total ~15 agent-weeks** (v1 = 16 weeks; v2 added 1-week pilot = 17 weeks; v2.9 added 2 weeks Phase 4 expansion = 19 weeks; v2.11 reduced Phase 3 from 5 weeks to ~1 week per M25 = 15 weeks). Four natural commit points; Phase 1A was the most consequential gate — passed. Phase 1B passed (qualified). Phase 2 entry M18 gate passed. Phase 2 NB11 H1 REFRAMED (direction-consistent with Jain 1999 complexity hypothesis at small effect size); Phase 2 NB12 H1 SUPPORTED (Mycobacteriaceae × mycolic-acid Innovator-Isolated). Remaining gates: Phase 3 architectural concordance; Phase 4 cross-resolution synthesis with phenotype/ecology grounding.

## Revision History

- **v1** (2026-04-26): Initial plan. Three-phase forced-order atlas; pre-registered hypotheses with weak-prior calibration; design reasoning captured separately in DESIGN_NOTES.md.

- **v2.16** (2026-04-29, NB28 Final Synthesis — scope expanded with tree-based donor inference + cross-resolution concordance):
  - **Synthesis pass scope (NB28)**: 6 data deliverables + 8 figures, with one new methodology element (tree-based donor inference at genus rank, distinct from the M25-deferred composition-based donor inference).
  - **Data deliverables**:
    - `data/p4_pre_registered_verdicts.tsv` — 4 hypotheses formalized as TSV (atlas effect / ecology grounding / phenotype anchor / MGE verdict / final disposition); currently REPORT prose only.
    - `data/p4_deep_rank_pp_atlas.parquet` — explicit 4-category P×P assignment {Innovator-Isolated / Innovator-Exchange / Sink-Broker-Exchange / Stable / Insufficient-Data} per (rank × clade × KO) tuple. Currently producer_z + consumer_z scalars without categorical column.
    - `data/p4_genus_rank_quadrants_tree_proxy.tsv` — full Open/Broker/Sink/Closed labels at genus rank on Phase 3 candidate set, via tree-based parsimony donor inference (NEW exploratory layer; M25 still defers composition-based confirmation).
    - `data/p4_concordance_weighted_atlas.parquet` — KO-level atlas with Pfam-architecture agreement column on Phase 3 candidate set; concordance flag + final-category column.
    - `data/p4_conflict_analysis.tsv` — discordant tuples (KO category ≠ architecture category) with hypothesis classification.
    - `data/p4_per_event_uncertainty.parquet` — extends `p2_m22_gains_attributed.parquet` with `n_leaves_under` (already there) + `leaf_consistency` (fraction of leaves under recipient_clade carrying the KO; per-event uncertainty proxy). Bootstrap-based per-event uncertainty deferred (~50hrs compute).
  - **Figures**: Hero 1 Atlas Innovation Tree (GTDB tree + per-clade overlays), Hero 2 Three-Substrate Convergence Card, Hero 3 Acquisition-Depth Function Spectrum, Supporting 4 PSII rank-dependence ladder (REVIEW_8 C9 response), Supporting 5 Hypothesis verdict card, Supporting 6 Function × Environment Sankey (the user's "interactions diagram"), NB22 atlas heatmap, NB22 four-quadrant summary.
  - **M26** *(new methodology element)* — **Tree-based parsimony donor inference at genus rank**. For each recent-rank gain event, walk the GTDB species tree to identify candidate donor clades (sister/cousin clades with the KO present prior to the gain, per Sankoff reconstruction). Aggregate to (genus × KO) and classify {Open Innovator, Broker, Sink, Closed/Stable, Ambiguous} with confidence based on (a) gain count per genus × KO, (b) number of alternative donor candidates per gain. **Distinct from M25-deferred composition-based donor inference** (codon usage / k-mer signatures requiring per-CDS sequence not in BERDL). Tree-based gives most-parsimonious-donor with explicit ambiguity; composition would give empirically-supported donor. Reportable as exploratory layer; agrees-with or refines deep-rank Innovator-Exchange labels where applicable.
  - **What remains deferred**: per-family DTL reconciliation at GTDB scale (Liu 2021 DTLOR / Bansal 2013 SPR-based methods); composition-based donor inference (M25); bootstrap-based per-event uncertainty (~50hrs).
  - **Time estimate**: ~22-24 hours of work in 5 stages (verdicts + 4-category atlas; tree-based donor inference; concordance + conflict + uncertainty; 8 figures; final REPORT/README/DESIGN updates).

- **v2.15** (2026-04-29, Phase 4 P4-D2 closure — MGE context per gain event):
  - **P4-D2 closed — pre-registered atlas KOs are not phage-borne, by both per-cluster MGE-machinery and PSII gene-neighborhood**.
  - **Per-cluster MGE-machinery (NB26b/c, atlas-wide via Spark + MinIO)**: bakta_annotations.product keyword matching for phage/transposase/integrase/plasmid/IS-element/recombinase/conjugation across 132M gene_clusters. Atlas baseline 1.37% (248,908 of 18.2M KO-bearing clusters). Pre-registered hypotheses: Mycobacteriaceae × mycolic 0.57%; Cyanobacteriia × PSII 0%; Bacteroidota × PUL 0%. Regulatory KOs show ~10× elevated MGE-machinery rate (4.13%) vs metabolic (0.37%) — consistent with regulatory products including transposon-bound and phage-bound regulators.
  - **PSII gene-neighborhood (NB26f/g, ±5kb on contig)**: cross-walk pangenome gene_id → kbase_genomes feature_id → contig + position (uses `kbase_genomes.feature` 1B rows + `contig_x_feature` 1B rows, broadcast-filtered through MinIO staging). 27,148 PSII focal features in Cyanobacteriia, 218,321 neighbor pairs. Mean MGE-neighbor fraction: 1.65%. **% of focal features with ≥1 MGE neighbor: 10.91%**. Poisson baseline expected with atlas MGE rate p=0.014 and mean neighbors n≈8: P(≥1 MGE neighbor) ≈ 10.6%. **PSII at-baseline — no MGE-cargo enrichment**, definitively ruling out phage-borne PSII transfer hypothesis. Per-KO breakdown (3.5% to 22.1%) shows differential mobility within PSII complex.
  - **Bacteroidota PUL + Mycobacteriaceae mycolic gene-neighborhood: scale-bounded**. Bacteroidota has 2,581 species (8.4× Cyanobacteriia); even canonical SusC/SusD-only (2 KOs) yields 723K focal features × 210K contigs → blows Spark-Connect driver.maxResultSize on toPandas. Sampled to 309 Bacteroidota species: still OOMs the pandas spatial-range merge (~24M-row × 9-col DataFrame). Would require batched processing or full-Spark Stage 6 — 1-2 days additional engineering, deferred.
  - **Combined verdict stands**: per-cluster MGE-machinery gives the answer for PUL/mycolic (0%/0.57% MGE-machinery rates); PSII gene-neighborhood directly demonstrates the at-baseline cargo result; literature (Sonnenburg 2010 ICEs for PUL, Marrakchi 2014 chromosomal mycolic) supports the non-phage transfer mechanism for the unmeasured deferred targets.
  - **Methodology contribution**: BERDL pangenome → genome-context cross-walk pipeline (`pangenome.gene_genecluster_junction` → `pangenome.gene` → `kbase_genomes.name` → `kbase_genomes.feature` + `contig_x_feature`) for cargo-on-MGE measurement at gene-neighborhood scale. Bottlenecks identified: Spark-Connect toPandas driver result-size cap at 1GB; pandas spatial-range merge OOM at ~10M+ rows. Future projects should default to full-Spark spatial filters + collect-only-aggregate pattern, or batched MinIO-staged processing.
  - **Phase 4 status: ALL deliverables closed (P4-D1, P4-D2, P4-D3, P4-D4, P4-D5)**. Final cross-resolution synthesis NB28 closes Phase 4.

- **v2.14** (2026-04-28, Phase 4 P4-D1 closure — phenotype/ecology grounding succeeds with corrected substrate audit):
  - **P4-D1 closed — all three pre-registered atlas findings ecologically grounded**. The user prompted re-audit of pangenome-internal env tables that v2.9 plan didn't list. Two pangenome-internal substrates (`kbase_ke_pangenome.ncbi_env` 4.1M EAV rows; `alphaearth_embeddings_all_years` 64-dim quantitative env vectors) plus `kescience_mgnify.species` (28.4% biome coverage, 18 categories) yielded richer environmental annotation than the v2.9 plan's external-substrate list (NMDC + MGnify + GTDB metadata + BacDive + Web of Microbes + Fitness Browser) suggested.
  - **NB23 biome enrichment**: Fisher's exact tests of clade × expected biome — Cyanobacteriia 2.77× photic aquatic (p<10⁻⁵²); Mycobacteriaceae 7.88× host-pathogen (p<10⁻⁴⁵, soil enrichment null); Bacteroidota 1.40× gut/rumen (p<10⁻³⁵). All three pre-registered atlas findings confirmed at expected biomes. NB12 finding refined: mycolic-acid Innovator-Isolated concentrates in **host-pathogen mycobacteria**, not soil mycobacteria, in our species set.
  - **NB24 BacDive phenotype anchoring** (32% species coverage): Mycobacteriaceae phenotype matches mycobacterial biology (Gram-positive, rod-shaped, non-motile, 89.4% aerobic-leaning, catalase-positive); Bacteroidota phenotype matches PUL biology (Gram-negative, rod-shaped, saccharolytic on maltose/raffinose/cellobiose, 1.5× anaerobe enriched, glycoside-hydrolase-rich). Cyanobacteriia BacDive coverage too thin (n=4) — anchor load carried by NB23+NB25.
  - **NB25 AlphaEarth env-clustering** (5,157 species, k=10): clusters recover ecological structure (cluster 0 = marine+sponge; cluster 4 = sheep-rumen; cluster 6 = hypersaline+Microcystis; cluster 9 = soil+grassland). Focal clades concentrate in expected clusters: Cyanobacteriia 35.6% in marine cluster 0; Mycobacteriaceae 34% in gut+sludge cluster 1. Mixed-biome generalist clusters 5/8 carry highest recent-gain density (consistent with Innovator-Exchange dominance).
  - **Substrate audit lesson**: v2.9 plan didn't anchor to `kbase_ke_pangenome.ncbi_env` or `alphaearth_embeddings_all_years` despite these being on BERDL. Future BERIL projects working with `kbase_ke_pangenome` should default to pangenome-internal env tables before reaching for external NMDC/MGnify/BacDive queries.
  - **Phase 4 status**: 4 of 5 deliverables closed (P4-D1, P4-D3, P4-D4, P4-D5). P4-D2 MGE context per gain event remains optional (biological texture, not closing a defensibility gap). Final cross-resolution synthesis NB28 next.

- **v2.13** (2026-04-28, Phase 4 P4-D4 closure — informative null):
  - **P4-D4 closed — pangenome openness vs M22 recent-acquisition is null at atlas scale, but informatively so.** `21_p4d4_pangenome_openness_validation.py` cross-correlates per-species pangenome openness (`1 − no_core/no_gene_clusters` from `kbase_ke_pangenome.pangenome` motupan output) with M22 recent-rank gain attribution at per-genus level, restricted to genera with ≥3 multi-genome species (n=894). Atlas-wide Spearman r = −0.011, 95% CI (−0.08, +0.06), p = 0.74. Class-stratified (regulatory n=1,554 KOs vs metabolic n=4,974 KOs) likewise null. Hypothesis-targeted T3a Mycobacteriaceae × mycolic (n_genera=10) Pearson r=+0.46 (CI −0.43, +0.86, underpowered); T3b Cyanobacteriia × PSII (n_genera=83) Pearson r=+0.11 (CI −0.10, +0.34, underpowered).
  - **Interpretation — distinct evolutionary phenomena.** The null is methodologically informative: M22 recent-rank gains measure between-species KO turnover on the GTDB species tree (Sankoff parsimony across species reps); pangenome openness measures within-species genome-set diversity (strain-level accessory gene fraction across multi-genome assemblies of one species). A genus can have many M22-recent gains but compact per-species pangenomes; a species can have an open pangenome but few M22-recent gains. **Pangenome openness is not a valid cross-substrate validation of M22**, contrary to the working assumption at plan time.
  - **Implications**: (a) no headline verdict changes — NB11/NB12/NB16 results stand; (b) P4-D4 was designed under the assumption that openness should correlate with M22; the empirical answer (no, they measure distinct things) is itself a methodology contribution to the final report; (c) cross-substrate validation of M22 remains an open commitment, achievable only via P4-D1 phenotype/ecology grounding (do high-recent-acquisition function classes correlate with their expected biomes / phenotypes?).
  - **Phase 4 remaining**: P4-D1 (phenotype/ecology grounding — feasibility audit first), P4-D2 (MGE context per gain event — biological texture, optional). Final cross-resolution synthesis NB28.

- **v2.12** (2026-04-28, Phase 4 P4-D3 + P4-D5 closure):
  - **P4-D3 closed — Alm 2006 r ≈ 0.74 NOT REPRODUCED at GTDB scale.** `19_p4d3_alm_2006_reproduction.py` per-genome HPK count (PF00512 hits) vs per-genome recent-LSE fraction (M22-derived) across n=18,989 species reps. Four framings: r = 0.10–0.29 (Pearson), 0.11–0.33 (Spearman). Strongest: HPK count vs recent TCS gains at genus rank (r = 0.29). All p < 10⁻⁴³. The qualitative result (TCS HK recent-skew) holds; the quantitative point estimate (r ≈ 0.74 from n=207) does not survive scaling. Three identified mechanisms: substrate scale (full GTDB tree heterogeneity vs Alm 2006's 207 cultivated isolates), tree-aware vs paralog-count operationalization (M22 misses within-species expansions), tree-rank granularity. NB17 architectural concordance (r = 0.67 consumer-side) is the project's strongest connection to Alm 2006.
  - **P4-D5 closed — D2 annotation-density residualization preserves all hypothesis verdicts.** `20_p4d5_d2_residualization.py` per-clade aggregate covariates (clade_size, mean annotated_fraction, mean GC%, mean genome_size) z-scaled and regressed against producer_z and consumer_z separately. Producer R² = 0.000 (the within-rank null absorbs all D2 variance — producer_z is bias-immune). Consumer R² = 0.053 (annotation-density coefficient = −1.27 on z-scale; small but non-zero). Hypothesis-test replication on residualized scores: NB11 reg-vs-met consumer d −0.21 → −0.21; NB12 Mycobacteriaceae × mycolic family producer d +0.31 → +0.31, consumer d −0.19 → −0.16; NB12 Mycobacteriales × mycolic order producer d +0.29 → +0.29, consumer d −0.29 → −0.28; NB16 Cyanobacteriia × PSII class producer d +1.50 → +1.50, consumer d +0.70 → +0.63. All directions and significances preserved; largest attenuation NB12 family consumer-side (~16% relative). Closes a long-standing pre-registration debt (D2 specified in plan v1/v2; deferred multiple times; pressed by adversarial reviews 4–7).
  - **Implication**: project's pre-registered hypothesis verdicts are not driven by per-genome annotation-density bias. The Alm 2006 framing is honest: methodology generalization works, point-estimate reproduction does not. Both are reportable and informative.
  - **Phase 4 remaining**: P4-D1 (phenotype/ecology grounding), P4-D2 (MGE context per gain event), P4-D4 (within-species pangenome openness validation). Final cross-resolution synthesis NB closes Phase 4.

- **v2.11** (2026-04-27, Phase 3 entry — feasibility-grounded reframe): Phase 3 entry conversation surfaced a data-availability constraint that scopes down the Phase 3 deliverable set substantially. Composition-based donor inference at genus rank (codon-usage Δ, GC% Δ, k-mer signatures vs clade norm) — pre-registered in plan v2 as the Phase 3 mechanism for distinguishing Open Innovator from Broker labels — requires per-CDS nucleotide composition data that is **not indexed on BERDL**: there are no per-gene codon counts, per-gene GC%, or per-gene k-mer signatures in any `kbase_ke_pangenome` table. Per-genome GC% exists in `kbase_ke_pangenome.gtdb_metadata` but is too coarse for per-gain-event inference.

  Getting per-CDS composition would require: (a) downloading FASTA files for ~18,989 representative genomes from external sources, (b) running codon counting per CDS externally, (c) building the donor-inference framework on the resulting profiles. ~1-2 weeks of additional infrastructure work that breaks the Phase 3 budget envelope and doesn't deliver atlas-aligned value (the v2.9 reframe already moved away from donor identification at deep ranks; M22 recipient-and-depth attribution is the deliverable).

  - **M25** *(new methodology element)* — **Composition-based donor inference at genus rank is deferred** due to a data-availability constraint. Per-CDS nucleotide composition (required for codon-usage Δ, GC% Δ, k-mer signature methods) is not in BERDL queryable schemas; obtaining it would require external FASTA downloads + per-CDS codon profiling that breaks the Phase 3 budget. Phase 3 reframes to *Innovator-Exchange-at-genus-rank* tests (the donor-undistinguished joint label) instead of separated Broker-vs-Open verdicts. Same level of phylogenetic-origin claim Alm 2006 made; same level the v2.9 reframe explicitly endorsed. Future work could revisit donor inference if BERDL adds per-CDS sequence indexing or if the project scope expands to include external sequence data.

  - **Cyanobacteria × PSII hypothesis reframed** — Pre-registered in plan v2 as *"Cyanobacteria → Broker at genus rank on PSII architectures"* (high producer + high outflow specifically; Broker requires donor inference to distinguish from Open Innovator). Reframed at v2.11 to *"Cyanobacteria genera show Innovator-Exchange at genus rank on PSII architectures (Broker OR Open Innovator, donor-undistinguished)"*. Same biological interpretation: high paralog expansion + high cross-clade exchange involvement on PSII at genus rank. The donor-vs-recipient distinction is acknowledged as not testable with current data; reported as a limitation, not as project failure.

  - **Phase 3 deliverables updated** — drops NB15 composition-based donor inference; revised NB15 becomes "Producer × Participation at genus rank on candidate KOs at architectural resolution" (joining the Phase 2 atlas with the architectural census from NB14). Phase 3 now: pre-flight audit + NB13 (candidate selection) + NB14 (architecture census) + NB15 (genus-rank P × P at architectural resolution) + NB16 (Cyanobacteria × PSII Innovator-Exchange test) + NB17 (TCS HK architectural Alm 2006 back-test) + NB18 (Phase 3 → Phase 4 gate).

  - **Phase 3 budget revised** — 5 weeks → ~1 week. Per-stage estimates: pre-flight Pfam audit (1 hour); NB13 candidate selection (1 hour); NB14 architecture census (4-8 hours); NB15 genus-rank P × P at architectural resolution (1 day); NB16 Cyanobacteria × PSII Innovator-Exchange test (1 day); NB17 TCS HK architectural Alm 2006 back-test (1 day); NB18 Phase 3 → Phase 4 gate (1 day). Total ~3-5 days work.

  - **Total project budget revised** — 19 weeks → ~15 weeks (Phase 3 budget reduction more than offsets v2.9's Phase 4 expansion). Phase 4 (P4-D1 phenotype/ecology, P4-D2 MGE context, P4-D3 Alm r=0.74 reproduction, P4-D4 pangenome openness, P4-D5 D2 residualization) remains 4 weeks.

  - **Phase 4 P4-D2 (MGE context per gain event) gains weight** — without composition-based donor inference, the MGE-context-per-gain tag is the strongest available "mechanism dimension" for the flow map. P4-D2 was already in plan v2.9 but becomes more central given M25's deferral.

  **Generalizable lesson**: pre-registered methodology should be feasibility-checked against the actual data substrate at plan time, not at phase entry. Plan v2 specified composition-based donor inference at Phase 3 without confirming per-CDS sequence data was available on BERDL. The constraint was discovered three phases later. *Future BERIL projects should include a Phase-0 substrate audit that maps each pre-registered methodology element to a specific BERDL table or external data source, with feasibility verified before plan freeze.* Plan v2.11 documents this as a project-discipline lesson alongside the M2 (dosage biology), M12 (absolute-zero criterion), and M14 (Alm 2006 misreading) pre-registration omissions.

- **v2.10** (2026-04-27, ADVERSARIAL_REVIEW_5 response): REVIEW_5 raised 4 critical + 6 important + 3 suggested issues against the v1.8 milestone. One important finding (I1) cited a fabricated paper (Mendoza 2020 *Microbiome* 8:1) verified via PubMed as not existing — see REPORT.md v1.9 Adversarial Review 5 Response section. Three critical findings (C3, I3, I4) restate concerns already addressed in plan v2.7-v2.9. Two findings (C1, I5) misframe defensible methodology. Two genuine new concerns drove plan-level commitments: M23 (minimum sample size for primary hypothesis tests) and M24 (canonical effect-size reporting format).

  - **M23** *(new methodology element)* — **Primary hypothesis tests pre-register a minimum sample size of `n_neg ≥ 20` per negative-control group**. REVIEW_5 C2 correctly flagged that the M21 strict-housekeeping panel includes pairs with very small n_neg (RNAP core strict at n=3; ribosomal_strict at n=83 but M21-excluded). For primary hypothesis-test pairs, n_neg ≥ 20 ensures bootstrap CIs have stable upper bounds. Under M23, the load-bearing housekeeping for primary tests is `neg_trna_synth_strict` (n=20). Pairs against `neg_rnap_core_strict` (n=3) are reported as informational only. The 3 PASS pairs against tRNA-synth (d=0.65, 0.79, 2.50, all CI lower bounds > 0) survive M23 with sample sizes that pass the C2 objection.

  - **M24** *(new methodology element)* — **Canonical effect-size reporting format**: every primary statistical comparison reports Cohen's d + 95% bootstrap CI (B = 200 minimum) + Mann-Whitney p-value (one-sided where direction is pre-registered). Median difference and percent-above-cohort are reported as supplementary effect-size metrics where biologically meaningful but are not load-bearing. Standardizes inconsistencies REVIEW_5 S3 flagged across REPORT v1.5-v1.8.

  - **C1/I5 misframing rebuttal documented in REPORT v1.9** — Cohen 1988 conventions (d = 0.2 small, 0.5 medium, 0.8 large) place the Phase 2 KO d values (0.665 medium-large to 3.558 very large) **above** biological-significance thresholds, contrary to REVIEW_5's claim. M18 PASS at full atlas scale (NB10) reproduces NB09c results within d ≤ 0.04 — methodology is robust at scale.

  - **I1 fabrication documented for the audit trail.** REVIEW_5 I1's "Mendoza 2020 50-fold lower regulatory HGT rates" claim is built on a fabricated citation (PMID 32160912 actually points to a Persian-language quality-of-life questionnaire study, not HGT). The "50-fold" quantitative anchor doesn't exist in the published literature. No project change required.

  - **I6 (M22 lacks biological validation anchors) deferred to Phase 4 as planned.** P4-D1 phenotype/ecology grounding (NMDC + MGnify + GTDB metadata + BacDive + Web of Microbes + Fitness Browser) and P4-D3 (explicit Alm r ≈ 0.74 reproduction) are designed to provide exactly these validation anchors. Already in plan v2.9.

  Pattern observation across REVIEW_4 and REVIEW_5: two consecutive adversarial reviews each contained one fabrication carrying a load-bearing quantitative claim. The verify-paper-citations protocol is now in `feedback_adversarial_verify_before_acting.md` (memory) for future BERIL projects.

- **v2.9** (2026-04-27, strategic reframe → "innovation + acquisition-depth atlas with phenotype/ecology grounding"): Triggered by user strategic review of the planned research arc. The original framing centralized the regulatory-vs-metabolic asymmetry test as the headline; the user's actual interest is broader: *where* function classes are produced, *where* and *when* (recent vs ancient) they are acquired, anchored to the clades and environments that host them. The v2.9 reframe makes this the central deliverable; regulatory-vs-metabolic asymmetry remains as one diagnostic within it. Six additions:

  - **M22** *(new methodology element)* — **Recipient-rank gain attribution from Sankoff parsimony**. The Sankoff reconstruction (M16) already marks every internal node where a function-class gain occurred. M22 extracts each gain event with two annotations: (i) **recipient clade at every rank** (which species/genus/family/order/class/phylum owns the gain location); (ii) **acquisition-depth bin** = the rank at which the gain landed (genus = recent, family = older recent, order = mid, class = older, phylum-or-above = ancient). Per (clade × function-class) tuple, this yields an **acquisition profile**: counts of recent / older / mid / older-still / ancient gains. *No donor inference attempted*; this is recipient-and-depth only — the same level of phylogenetic origin claim that Alm 2006's lineage-specific-expansion (LSE) analysis made. Implementation: post-processing pass on existing Sankoff output (~30 min compute at GTDB scale; ~1 day implementation). NB10b (gain-attribution) writes per-(clade × function-class × depth-bin) tables alongside the producer/participation atlas. Output joins with NB10 atlas for the full deliverable.

  - **P4-D1** *(Phase 4 deliverable, new)* — **Phenotype / ecology grounding of the atlas**. Triangulate clade × environment using three independent BERDL substrates: **NMDC** (sample → multi-omics + biome metadata; per `docs/schemas/nmdc.md`), **kescience_mgnify** (MGnify metagenomics study → taxa linkage; collection exists per `docs/discoveries.md` though no dedicated schema doc — Phase 4 mid-audit task), **kbase_ke_pangenome.gtdb_metadata** (per-genome isolation-source / environment fields from GenBank metadata flowing through GTDB). Cross-reference against three phenotype substrates: **BacDive** (per-species metabolic phenotypes — oxygen tolerance, carbon utilization, salt range, growth temp; `docs/schemas/bacdive.md`), **Web of Microbes** (interaction data; co-culture observations), **Fitness Browser** (gene-level fitness for ~30 organisms via `fb_pangenome_link.tsv`). Phase 4 deliverable: per-(clade × function-class) tuples annotated with environmental enrichment, phenotype association, and (where Fitness Browser overlap exists) gene-level fitness validation. Turns the atlas from descriptive to interpretive.

  - **P4-D2** *(new)* — **MGE context per gain event**. Each Sankoff gain event is mechanism-agnostic in the parsimony reconstruction (a phage-mediated transfer, plasmid-borne resistance gene, and chromosomal recombination all look identical). M22 extracts gain locations; P4-D2 tags each gain event "MGE-context: yes/no" using `kbase_ke_pangenome.bakta_annotations` (product/feature flags for phage proteins, integrases, transposases, plasmid replication proteins) and `genomad_mobile_elements` (if ingested — Phase 4 audit task per `docs/pitfalls.md` ingestion-status pattern). Distinguishes flow via mobile elements from flow via other mechanisms (transformation, prophage). Adds mechanism dimension to the flow / acquisition map.

  - **P4-D3** *(new)* — **Explicit Alm 2006 r ≈ 0.74 reproduction at GTDB scale**. Plan v2.5 (M14) reformulated the Alm back-test to "reproduce the r ≈ 0.74 correlation between HPK count per genome and recent-LSE fraction at full GTDB scale, using a tree-aware metric." All ingredients exist after M22: HPK count per genome (already computed in NB04b power analysis at pilot scale; rerun at full scale); recent-LSE fraction = recent-rank gain events per genome / total gene count (M22-derived). P4-D3 dedicates a Phase 4 notebook to the explicit r computation across the 18,989 species and reports r with 95% CI. The faithful reproduction lands at architectural resolution (Phase 3); the KO-level reproduction is a Phase 2 commitment per the original v2 plan. *This commits the project's "Alm-2006-inspired" framing to a quantitative anchor.*

  - **P4-D4** *(new)* — **Within-species pangenome openness as cross-validation of recent-HGT signal**. D1 collapses to one rep per species before producer/consumer scoring. But species pangenome openness (aux/core ratio, or Heaps' law alpha) is itself a documented signal of recent HGT activity (Tettelin 2005; McInerney 2017). P4-D4 computes per-species openness from existing `kbase_ke_pangenome.pangenome` columns (`no_aux_genome / no_core`) and asks: do species in clades flagged "high-recent-acquisition" by Sankoff (M22) also show open pangenomes? Resolves a question reviewers will press; ~1 day work.

  - **P4-D5** *(new, closes a long-standing pre-registration debt)* — **Annotation-density bias residualization fully implemented**. Plan v1 / v2 pre-registered D2 = "per-genome annotated-fraction regressed out as nuisance covariate." Currently `annotated_fraction` is computed and reported in `p1b_full_species.tsv`, but is not used as a pre-regression on producer/participation scores. P4-D5 implements the residualization (OLS with annotated-fraction, GC%, genome-size, clade-size as predictors) and reports atlas scores both raw and residualized. Closes a defensibility gap reviewers will press; ~1 day work.

  **Methodological threads explicitly deferred** (not P4 deliverables, may be Phase 5 / future work):
  - Network-based HGT detection (Popa 2011 bipartite gene-genome occurrence networks) — independent methodology cross-validation. Defer unless reviewers request.
  - Time calibration of the GTDB rank scaffold (using Battistuzzi 2009 / Marin 2017 prokaryote divergence dates) — converts ordinal rank-depth to interval time. Substantial methodology addition; defer.
  - Sensitivity analyses (per-clade rarefaction, jackknife, ANI-stratified within-species sub-sampling) — should be one consolidated Phase 4 robustness NB before final synthesis. Add if budget allows.

  **Budget impact**: 17 weeks → ~19 weeks. M22 (~1 day), P4-D1 (~1-2 weeks), P4-D2 (~2 days), P4-D3 (~1-2 days), P4-D4 (~1 day), P4-D5 (~1 day). Phase 4 budget bumps from 2 weeks to ~4 weeks.

  **Strategic reframe**: The project's central deliverable is now framed as **"the innovation + acquisition-depth atlas of bacterial function classes, anchored to clade phylogeny and environmental ecology."** The four pre-registered weak-prior hypotheses (Bacteroidota PUL, Mycobacteriota mycolic-acid, Cyanobacteria PSII, Alm TCS) become specific test points within this atlas. The regulatory-vs-metabolic asymmetry test (NB11) becomes a query against the atlas: "do regulatory function classes show different acquisition-depth profiles than metabolic ones across the GTDB tree?" If yes → headline asymmetry confirmed at the depth-resolved level; if no → the H0-atlas fallback is the deliverable, but with substantially richer interpretation than originally planned because of P4-D1 phenotype/ecology grounding.

  This reframe is faithful to the original brief's "directed clade-to-clade flow graph" deliverable (DESIGN_NOTES item 4). The project gives up *donor identification at deep ranks* (constraint: not tractable at full GTDB scale per AleRax/ALE limits and codon-amelioration timescales) but recovers *recipient-and-depth attribution* via M22, which is the same level of phylogenetic-origin claim Alm 2006 made — and combines it with environmental and phenotype anchoring that goes beyond Alm 2006's scope.

- **v2.8** (2026-04-27, Phase 2 entry M18 gate + strict-class diagnostic): Phase 2 began with NB09 (KO data extraction) + NB09b (M18 amplification gate) + NB09c (strict-class re-test). NB09b's first-pass M18 verdict was **MARGINAL** (best d = 0.21, 95% CI crossed 0) with the signed direction reversed against expectation: pos HGT controls had lower Sankoff/n_present than neg housekeeping for ribosomal/RNAP comparisons. Diagnostic NB09c reused NB09b's per-KO Sankoff scores and re-classified housekeeping by strict KEGG-KO ranges; M18 verdict swung to **PASS** (6/9 strict pairs at d ≥ 0.3 with 95% CI lower bound > 0; best pair d = 3.56). The MARGINAL → PASS swing diagnosed control-class contamination in the description-match approach.

  - **M21** *(new commitment)* — **Canonical clean housekeeping** for M18-style methodology validation and any d-based metric in Phase 2/3 = **tRNA synthetase** (KEGG-KO `K01866..K01890`, 25 KOs, median n_present_leaves = 18,917 / 18,989) + **RNAP core** (`{K03040, K03043, K03046}`, 3 KOs, median n_present_leaves = 18,758 / 18,989). Ribosomal — both description-match (`LOWER(ipr_desc) LIKE '%ribosomal protein%'`) AND the strict K02860-K02899 + K02950-K02998 range — is too contaminated at KO level: the description-match catches clade-restricted accessory r-proteins (RimM, RbfA, processing factors); the strict K-range is a pre-2000 KEGG-numbering approximation and is itself bimodal between universal r-proteins and accessory variants. Ribosomal is **dropped as load-bearing housekeeping** for Phase 2/3 metric validation; reported as informational only. The Phase 2 control panel is therefore: positive HGT = β-lactamase + class-I CRISPR-Cas + TCS HK (per M17, AMR excluded for Pseudomonadota bias); negative housekeeping = tRNA-synth + RNAP core only.

  - **Methodology freeze breach acknowledged** — Plan v2.7 froze methodology at M18 + M19 + M20 with the explicit caveat that "further revisions during Phase 2 require explicit milestone-revision call-outs with NB-diagnostic rationale." NB09c is exactly that call-out: a one-hour cheap diagnostic that reused existing Sankoff scores, surfaced contamination in the negative-housekeeping pool, and produced a decisive verdict swing. M21 is the resulting commitment. The freeze is broken honestly, not silently.

  - **Generalizable lesson** — Class detection that worked at UniRef50 resolution (description-match → mostly clean because UniRef50 clusters preserve description-level signal) does **not** survive KO aggregation. The 50% majority-vote threshold for "KO is class X" admits class-accessory members (e.g., a KO with 51% of constituent gene_clusters described as "ribosomal protein" might be a clade-specific accessory). For housekeeping at KO resolution, use **KEGG-curated K-ID ranges**, and verify that the chosen range captures only universal members (median n_present ≈ all leaves) before treating as clean. The Phase 2 control panel should always include a `n_present_leaves` sanity check on negative-housekeeping classes.

  - **Phase 2 NB10 atlas commitments updated** — The full KO atlas (NB10) uses M21 housekeeping. The M18-style metric validation in NB10 (sanity rail) compares positive HGT classes to tRNA-synth + RNAP core only.

  Phase 2 NB09/NB09b/NB09c artifacts: `data/p2_ko_assignments.parquet` (28M rows on MinIO), `data/p2_ko_assignments_panel.parquet` (2.69M rows local panel), `data/p2_uniref50_to_ko_projection.tsv` (3.59M projections), `data/p2_ko_control_classes.tsv` (13,062 KOs), `data/p2_ko_pathway_brite.tsv` (13,062), `data/p2_m18*.tsv|.json`, `data/p2_m18c_*.tsv|.json`, `figures/p2_m18_amplification_panel.png`, `figures/p2_m18c_strict_class_panel.png`. Sankoff parsimony on 748 panel KOs ran in 11s; bootstrap (B=200) on 9 pairs in <1s. Wall time NB09 ≈ 7 min, NB09b ≈ 1 min, NB09c ≈ 5 s.

- **v2.7** (2026-04-27, ADVERSARIAL_REVIEW_4 response): Synthesized REVIEW_4 (5 critical + 7 important + 4 suggested). Two critical findings (C1 "no Alm 2006 citation"; I8 "natural-expansion 64.5% vs 39.4% recompute") are reviewer-side errors documented in REPORT.md v1.5 "Phase 1B Adversarial Review 4 Response". The substantive concerns drive three commitments — **M19** (cluster-bootstrap CIs), **M20** (independent paralog holdout), and the retirement of **M9** (PIC, double-counting on Sankoff) — plus an M12 scope clarification.

  - **M19** *(Phase 2 inference)* — Cluster-bootstrap on UniRefs at Pfam-family granularity for Cohen's d confidence intervals. The Phase 1B Mann-Whitney test treats UniRef50s as iid; multiple UniRef50s within a Pfam family inherit related phylogenetic distributions, so the effective N is inflated. Implementation: resample UniRef-clusters within each function class with replacement at Pfam-family granularity (B = 200 bootstraps), recompute per-leaf Sankoff parsimony Cohen's d under each bootstrap, report 95% bootstrap CI alongside the point estimate. Tractable at Phase 2 scale because function-class-level inference reduces effective N by ≈ 10× vs UniRef-level. M19 is the proper fix for the residual non-independence concern that ADVERSARIAL_REVIEW_4 I5 (and prior reviews via M9) flagged.

  - **M20** *(Phase 2 producer-null validation)* — Independent paralog holdout for producer-null validation. The natural_expansion v2.0 control is selected for paralog count ≥ 3 and tested against a null designed to detect paralog expansion — circular. Phase 2 adds an independent paralog control: a holdout set of KOs with documented paralog signal sourced from a curation independent of the natural_expansion construction (Pfam clans with documented paralog families per Treangen & Rocha 2011; KO orthogroups with cross-organism duplicates per the Csurös 2010 Count framework). natural_expansion remains as a metric-direction sanity check; the holdout becomes the load-bearing producer-null validation. Acceptance criterion: producer z on the holdout is significantly above zero at all ranks, with effect direction matching natural_expansion.

  - **M9 retired** — Plan v2.4 promoted PIC (phylogenetic independent contrasts) to Phase 2 mandatory. Plan v2.6 (M16 Sankoff promotion) made classical Felsenstein PIC redundant: per-leaf Sankoff parsimony (`gain_events / n_present_leaves`) is intrinsically tree-aware and already encodes tree topology. Stacking classical PIC on top of Sankoff is double-counting. The legitimate residual non-independence concern is at the UniRef-cluster level (M19), not the species level. M9 is retired with this rationale; M19 is the right fix for the actual residual concern.

  - **M12 scope clarification** — Plan v2.4's M12 ("relative-threshold consumer-z framing") applies only to *methodology QC* (does the methodology distinguish HGT-active classes from housekeeping baselines?), not to hypothesis adjudication. The four pre-registered hypotheses (Bacteroidota PUL, Mycobacteriota mycolic-acid, Cyanobacteria PSII, Alm 2006 TCS reproduction) retain absolute-criterion adjudication. M12 is a control-class metric, not a hypothesis-test threshold. Plan v2.7 separates the two uses to prevent backsliding from absolute-criterion falsification to relative-criterion rescue.

  - **Phase 2 framing sharpened** — M18's amplification gate (Cohen's d ≥ 0.3 on Sankoff for ≥ 1 positive HGT control vs housekeeping) is a *falsification gate*, not a validated prediction. Plan v2.7 reinforces this in the Phase 2 substrate-and-method section header to address ADVERSARIAL_REVIEW_4 C2/C3/C4 framing concerns.

  - **Methodology freeze** — M18 + M19 + M20 close out plan v2.7. Further methodology revisions during Phase 2 require explicit milestone-revision call-outs with NB-diagnostic rationale, per the project's "run cheap diagnostics first" lesson (REPORT.md "Lessons captured").

  Concerns already addressed in plan v2.6 (restated): S2 alm_2006_methodology_comparison.md integration (done in plan v2.5 / REPORT v1.3); S4 promote Sankoff to primary metric (done in plan v2.6 M16); I1 Bacteroidota CAZyme literature substrate-resolution mismatch (Finding 1B.6 + REPORT v1.5 sharpening). Reviewer-side errors C1 (Alm 2006 citation) and I8 (natural-expansion 64.5%/39.4% phase-mixing) documented in REPORT.md v1.5 response section; no project change required.

- **v2.6** (2026-04-27, NB08c diagnostic resolution): Sankoff parsimony on the GTDB-r214 tree (NB08c) confirmed M15: tree-aware metric recovers the expected direction (positive HGT > negative housekeeping at p = 2.1×10⁻⁵), where the parent-rank dispersion metric had produced the order-rank anomaly. **Methodology framework is not broken; the metric was wrong.**

  But effect size at UniRef50 remains small (Cohen's d = 0.146, short of the d ≥ 0.3 threshold). The substrate-hierarchy softening (Phase 1B v1.2) holds: HGT signal is real but small at UniRef50; aggregation may amplify it at Phase 2. We proceed to Phase 2 *banking on amplification*. Three additional revisions baked in:

  - **M16** *(Phase 2 primary metric)* — Sankoff parsimony on the GTDB-r214 tree topology is the **primary atlas metric** for Phase 2 onward. Parent-rank dispersion drops to secondary/diagnostic only. NB08c demonstrated parent-rank dispersion produces the order-rank anomaly that Sankoff resolves. Per-leaf Sankoff (gain events / n_present_leaves) is the comparison statistic; raw Sankoff score is reported alongside. PIC correction (M9, deferred again) is no longer needed in this form because Sankoff is intrinsically tree-aware.

  - **M17** *(Phase 2 control panel)* — `pos_amr` (bakta_amr) is **excluded** from the Phase 2 positive-control panel. NB08c Diagnostic D demonstrated AMR has median 50 % Pseudomonadota fraction (vs ≤4 % for all other classes except natural_expansion). The AMRFinderPlus reference is documented Pseudomonadota-biased; AMR detection at scale is a substrate-bias confound, not a clean HGT-positive control. β-lactamase (`pos_betalac`), class-I CRISPR-Cas (`pos_crispr_cas`), and TCS HK (`pos_tcs_hk`) remain as positive controls. AMR is reported as informational.

  - **M18** *(Phase 2 amplification gate)* — Phase 2 KO atlas must demonstrate **Cohen's d ≥ 0.3 on Sankoff parsimony / n_present** for at least one positive HGT control class vs negative housekeeping. NB08c established the UniRef50 baseline at d = 0.15. If Phase 2 KO does not amplify to d ≥ 0.3, the substrate-hierarchy claim is falsified and **M11 redesign triggers**: switch from Sankoff parsimony to a fundamentally different methodology (e.g., gene-tree-vs-species-tree reconciliation per AleRax sub-sampling, per the original v2 plan's Phase 3 reservation). The amplification gate is a hard test — if it fails, the project halts at Phase 2 for redesign.

  Diagnostic B (within-Pseudomonadota dispersion) **dropped from the methodology**. NB08c showed it's biased by class coverage (housekeeping is pan-Pseudomonadota; HGT-active classes are clade-specific within phylum), not by HGT activity. The right within-phylum analog is per-phylum Sankoff parsimony on a phylum-pruned tree.

  **NB08c also confirmed natural_expansion as a valid metric-direction sanity check**: it has the lowest per-leaf parsimony score (4.5 vs 14-25 for other classes), correctly reflecting that broadly-conserved UniRefs require few gain events to explain their presence pattern.

  **Updated effect-size baseline**: Cohen's d = 0.15 at UniRef50 (Sankoff parsimony, pos HGT vs neg housekeeping) is the lower bound. The +0.6 to +1.2 σ "less clumped than housekeeping" framing in REPORT.md v1.2 used parent-rank dispersion z-scores and overstated effect magnitude on a Cohen's d basis. Plan v2.6 standardizes on Cohen's d as primary effect-size metric.

- **v2.5** (2026-04-27, Alm 2006 close-reading + methodology correction): Triggered by adversarial review effect-size critique + user prompt to revisit the Alm 2006 paper. Close-reading the Alm 2006 paper (memo'd at `docs/alm_2006_methodology_comparison.md`) revealed three load-bearing misreadings of Alm 2006 that had structural consequences for the project:

  1. The four-quadrant framework (Open Innovator / Broker / Sink / Closed Innovator) is **our construction**, not Alm 2006's. Alm 2006 reported a correlation (r = 0.74) between HPK count and LSE fraction per genome, plus a threshold classification ("HPK-enriched" = ≥ 1.5 %). They never named "producer / consumer" / "pioneer / sapper" / four-quadrant categories.
  2. Alm 2006 worked at the **single-domain level** (IPR005467) — directly comparable to our UniRef50 / Pfam-architecture detection. The M3 substrate-hierarchy claim ("UniRef50 too narrow because Alm 2006 worked at family level") was wrong. They got clean signal at the equivalent granularity to ours.
  3. Alm 2006 used **phylogenetic-tree-aware reconciliation** to assign LSE vs HGT events. Our parent-rank dispersion permutation null does not measure the same thing.

  Three corrections (M13–M15) baked into Phase 2 design:

  - **M13** *(reframe)* — Project's relationship to Alm 2006 is "Alm-2006-inspired", not "Alm-2006-generalizing". The central research question's claim that "the producer/consumer asymmetry observed by Alm-Huang-Arkin 2006" generalizes overstates Alm 2006's actual finding (which is a correlation, not a four-quadrant taxonomy). The four-quadrant framework gets explicit ownership as this project's construction. The Alm 2006 back-test deliverable is reformulated to *"reproduce the r ≈ 0.74 correlation between HPK count per genome and recent-LSE fraction at full GTDB scale, using a tree-aware metric"* — a specific, falsifiable, faithful-to-the-original test.

  - **M14** *(replace M3)* — The substrate-hierarchy claim from Phase 1A M3 (and reaffirmed at Phase 1B M6) collapses. Phase 1B's failure at UniRef50 is *not* explained by Alm 2006 working at family level (they didn't). The failure is a *metric* mismatch: parent-rank dispersion is a permutation-null proxy that does not measure tree-aware HGT signal. **Phase 2 KO aggregation is no longer the expected fix. The tree-aware metric (M15) is.** Phase 2 KO atlas remains useful for the regulatory-vs-metabolic comparison but is not required by the substrate-hierarchy logic anymore.

  - **M15** *(promote Diagnostic C)* — Phyletic incongruence as **mandatory** for Phase 2 (and for the Phase 1B post-gate diagnostic NB08c). The lightweight tractable form at GTDB scale is **Sankoff parsimony score** (binary gain/loss) on the GTDB-r214 species tree topology — *not* full DTL reconciliation (out of scope at full scale per the original constraint, but tractable for hundreds-to-thousands of UniRefs). For each UniRef50: minimum number of gain events to explain its presence pattern given the GTDB tree. UniRefs with high parsimony scores indicate HGT; low scores indicate vertical inheritance. This is the closest faithful analog of Alm 2006's tree-reconciliation methodology at GTDB scale.

  **Phase 1B post-gate diagnostic (NB08c)** plan revised. Instead of A + B + D (per-class K, per-phylum decomposition, annotation density), NB08c now includes **A + B + C + D** with C as the headline:

  - **A** Per-class K (n_clades_with) distribution at order rank — checks whether positive HGT controls have systematically smaller K
  - **B** Per-phylum decomposition — restrict each class to its dominant phylum, re-test consumer z within phylum
  - **C** Sankoff parsimony score on the GTDB-r214 tree topology for a sampled subset (~500 UniRefs per class) — the canonical Alm-2006-style metric. **If the order-rank anomaly disappears under Sankoff parsimony, the parent-rank dispersion was the source of the anomaly. If the anomaly persists, the methodology has a deeper problem.**
  - **D** Annotation density check — fraction of UniRefs in each class whose dominant phylum is Pseudomonadota (AMRFinderPlus reference bias)

  **Lesson captured**: anchor papers cited as foundational must be close-read for *exact* methodology before building atlas infrastructure on extrapolations. Three pre-registration omissions in this project (M2, M12, M14) all share this pattern. Future BERIL projects building on canonical papers should treat "actually read the methods section in detail" as a Phase-0 deliverable.

- **v2.4** (2026-04-27, Phase 1B complete + post-gate diagnostic): Phase 1B → Phase 2 gate verdict `PASS_REFRAMED`. Methodology validates at full GTDB scale; pre-registered Bacteroidota PUL Innovator-Exchange hypothesis is falsified at the absolute-zero criterion across all 4 deep ranks. Six methodology revisions (M6–M11) baked into Phase 2 from this point forward. **Plus a critical 7th revision (M12)** raised by a post-gate diagnostic that the user's concern triggered:

  - **M6** Phase 2 substrate is KO not UniRef50 (substrate-hierarchy held in softened form: UniRef50 produces small-magnitude HGT signal; KO aggregation expected to amplify substantially)
  - **M7** Carry M1 rank-stratified parents forward to Phase 2
  - **M8** Carry M2 negative-control criterion forward (CI upper ≤ 0.5)
  - **M9** PIC (HIGH 3) re-promoted to Phase 2 mandatory; deferred from Phase 1B
  - **M10** Per-class cap pattern at KO scale (functional categories may have far fewer KOs than 10K)
  - **M11** *(revised at v2.4)* If KO-level relative-threshold discrimination doesn't amplify substantially over UniRef50's +0.6–1.2 σ at family rank, switch from parent-rank dispersion to direct phyletic-incongruence on KO presence/absence
  - **M12** *(new at v2.4)* **Atlas-level "Innovator-Exchange" definition is reformulated**. Phase 1B revealed the absolute-zero consumer-z threshold was over-stringent: HGT-active classes at UniRef50 sit at consumer z ≈ −6 (clumped relative to permutation null) but at ≈ +0.6–1.2 σ less clumped than housekeeping baselines (Mann-Whitney U one-sided p << 10⁻⁷ for β-lactamase and class-I CRISPR-Cas vs ribosomal at family rank). **For Phase 2 onward, "Innovator-Exchange" is operationalised as "≥ X σ less clumped than housekeeping baseline at the rank's parent" rather than "absolute consumer z > 0".** X is to be calibrated empirically against Phase 2 KO data; Phase 1B numbers (+0.6–1.2 σ at UniRef50 for known-HGT classes) provide a lower bound.

  Plus an **order-rank anomaly** flagged for Phase 2 investigation: at family→order parent (Phase 1B order rank), positive HGT controls are *more* clumped than housekeeping (median Δ = −0.83 σ, opposite of expectation). Possible: small parent-class count inflates null variance, or intra-phylum HGT-active genes cluster within few orders. Phase 2 KO atlas should reproduce this diagnostic.

  The reframe was triggered by a user concern after the original Phase 1B verdict that we might not be confronting a methodology error. The diagnostic in NB08b confirmed: methodology IS detecting HGT signal (just below the absolute threshold). The original NB07/NB08 narrative was over-pessimistic; v2.4 corrects this with M12 + the relative-threshold framing.

  Phase 1B headline numbers:
  - 18,989 bacterial GTDB representatives (post-CheckM)
  - 100,192 UniRef50 target set (10K-per-class cap from a 15.4M unique-UniRef pool)
  - 1.54 M (species, UniRef50) presence rows
  - 1.29 M (rank, clade, UniRef) producer scores
  - Wall time ≈ 1 hour (NB05 7.5 min + NB06 45 min + NB07 5 min + NB08 5 min)

- **v2.3** (2026-04-26, post-Phase-1A review synthesis): synthesized `REVIEW_1.md` (claude standard) and `ADVERSARIAL_REVIEW_1.md` (claude adversarial). Standard reviewer was uniformly positive (0 critical, 0 important, 6 forward-looking suggestions); adversarial reviewer flagged 3 critical + 4 important gaps. Five HIGH revisions baked into Phase 1B from this point forward, plus four MEDIUM items deferred with explicit roadmap:

  - **HIGH 1: Known-HGT positive control set for consumer null** (addresses adversarial C2). The producer null is validated by `natural_expansion`. The consumer null lacks an analogous positive control: AMR was supposed to be it but the parent-phylum anchor masks intra-phylum HGT (M1 acknowledges). **Phase 1B adds** a known-cross-phylum-HGT positive control set:
    - **β-lactamase families with documented cross-phylum spread** — `bla_TEM`, `bla_CTX-M`, `bla_NDM`, `bla_OXA-48` family Pfams (e.g., PF00144, PF13354), known to spread Pseudomonadota ↔ Bacillota via plasmids (literature: Forsberg 2012; Bonomo 2017).
    - **Class-I CRISPR-Cas systems** — Cas3 family (PF18557), Cas7 family (PF09704), Cas8a (PF09827) — Metcalf et al 2014 documented cross-tree-of-life HGT for these.
    Phase 1B's NB02 equivalent validates the consumer null can detect positive z (cross-phylum dispersion above null) for these classes at the appropriate ranks.

  - **HIGH 2: Raw paralog-count effect sizes alongside z-scores** (addresses adversarial C3). All Phase 1B atlas tables in REPORT.md must include raw paralog count means, cohort means, raw differences, and percent-above-cohort alongside z-scores. Phase 1A REPORT v1.1 retroactively adds these; Phase 1B uses them as standard.

  - **HIGH 3: PIC (phylogenetic independent contrasts) mandatory at Phase 1B** (addresses adversarial I1). Plan v2 listed PIC as a Phase 2 optional sensitivity test. **Plan v2.3 promotes PIC to Phase 1B mandatory** for both producer and consumer score reporting. Without PIC, species within clades are pseudo-replicated, and family/order/class/phylum-level statistics conflate genuine functional signal with shared evolutionary history. Implementation: per-(rank, function-class) producer-z and consumer-z reported with PIC-corrected variance estimates using GTDB rank scaffold as the contrast tree.

  - **HIGH 4: Alm 2006 power analysis confirms substrate-hierarchy claim** (addresses adversarial I2). Phase 1A pilot has 81–99% power to detect a medium Alm 2006 effect (d=0.3) at all ranks except genus (where n=73 gives 81% power). At UniRef50, observed TCS HK z is *negative* (mean −0.20) — opposite of Alm 2006's positive paralog expansion. **The negative result is genuine substrate-hierarchy, not underpowering.** This empirically validates the v2 plan's Phase 2 (KO) / Phase 3 (Pfam architecture) substrate-hierarchy for Alm 2006 reproduction.

  - **HIGH 5: M2 sharpening** (addresses adversarial I3). The pre-registered v2 negative-control criterion ("mean producer z within ±1σ of 0") was a pre-registration omission, not a target redefinition. The biological prior (dosage-constrained genes have *fewer* paralogs than typical genes at matched prevalence; Andersson 2009; Bratlie 2010) was correctly anticipated; its quantitative consequence (negative producer z, not zero) was not encoded into the criterion. **Phase 1B pre-registers the corrected expectation**: ribosomal / tRNA-synth / RNAP core controls show producer z significantly below 0 *and* CI not crossing strongly-positive territory.

  Plus four MEDIUM revisions deferred to Phase 1B / 2 plan documents:

  - **MEDIUM 6: Hierarchical multiple-testing implementation details** — BH-FDR variant + effective-N within KEGG BRITE × GTDB family clusters (addresses standard suggestion #4 + adversarial C1).
  - **MEDIUM 7: Compute resource specification per phase** — memory + runtime + storage (addresses standard suggestion #2 + adversarial S2).
  - **MEDIUM 8: Phase 2 mid-pilot KO-level validation step** before Phase 3 architectural deep-dive (addresses standard suggestion #3).
  - **MEDIUM 9: Uncertainty propagation strategy for Phase 4 cross-resolution synthesis, documented in advance** (addresses standard suggestion #4).
  - **MEDIUM 10: Cite Sichert & Cordero (2021) in references.md** for Phase 1B Bacteroidota PUL literature context.

  Three adversarial critiques are not adopted as written, with reasoning documented in `REPORT.md` "Pushbacks":
  - **C1 framing as "rendering meaningful discoveries impossible"** — overcalled given the hierarchical strategy in plan v2.1.
  - **I4 "Substrate switching invalidates v1"** — v1 was iterated, not shipped. v2 IS the milestone.
  - **H2 "Central project hypothesis unsupported"** — DESIGN_NOTES.md v1's weak-prior framing addresses this; reviewer didn't credit it.

  Full review-synthesis narrative in `DESIGN_NOTES.md` v2.2 update.

- **v2.2** (2026-04-26, post-Phase-1A staging alignment): Phase 1A completed with verdict `PASS_WITH_REVISION`. Four methodology revisions (M1–M4) baked into Phase 1B from this point forward:

  - **M1 — Rank-stratified parent ranks for consumer null**: Phase 1A NB02/NB03 used `parent_rank = phylum` for all child ranks. AMR consumer z was strongly negative (−4.4 to −4.8) at parent-phylum dispersion across genus / family / order — reflecting intra-phylum HGT (Enterobacteriaceae, Acinetobacter) being clumped at phylum level, not absence of HGT (literature: Smillie 2011 for gut, Forsberg 2012 for soil). **Phase 1B uses rank-stratified parents**: genus → family parent, family → order parent, order → class parent, class → phylum parent. This makes the consumer null sensitive to HGT events at the rank where they occur.
  - **M2 — Negative-control criterion: CI upper ≤ 0.5, not "near zero"**: pre-registered v2 criterion ("mean producer z within ±1 σ of 0") was biologically wrong. Ribosomal proteins, tRNA synthetases, and RNAP core subunits are dosage-constrained — they have *fewer* paralogs than typical genes at matched prevalence. Negative producer z is the biologically correct outcome (literature: Andersson 2009 for dosage cost). **Phase 1B gate criteria use "producer CI upper bound ≤ 0.5" as the negative-control pass.**
  - **M3 — Alm 2006 reproduction at Phase 1 (UniRef50) is empirically out of scope**: Phase 1A pilot tested TCS HK paralog expansion at UniRef50 resolution and found mean z ≈ −0.2 across all ranks (only 4–11 % of TCS HK UniRefs above zero). This is consistent with Alm 2006's measurement at the HK *family* level (number of distinct HK genes per genome). UniRef50 is a sequence-cluster unit and cannot aggregate to family — confirming the v2 plan's substrate hierarchy. **Alm 2006 reproduction is reserved for Phase 2 (KO) and Phase 3 (Pfam architecture) per the existing pre-registered hypothesis structure.** Phase 1B does not test Alm 2006.
  - **M4 — Paralog fallback (option a) acceptable with sensitivity check**: 21.5 % of (species, UniRef50) presence rows in the pilot use `n_gene_clusters` as paralog proxy when `n_uniref90_present = 0`. Producer null behaves consistently across this fraction; no obvious bias detected. **Phase 1B reports producer scores both with and without fallback as a robustness check.**

  Phase 1A budget actuals: 1 day pilot extraction + null model + atlas + gate (vs 1-week estimate). Faster than expected because pilot scale (1K species × 1.2K UniRefs) ran in single-digit minutes per notebook.

  Phase 1A artifacts in commit history: `8197218` (NB01 v1) → `68b5aad` (NB01 v2 + plan v2.1 substrate audit) → `4629c55` (NB01 v3 natural_expansion + NB02 v2 multi-rank) → `15deb2f` (NB03 + NB04 + Phase 1A complete).

- **v2.1** (2026-04-26, post-NB01 substrate audit): Audit of BERDL substrate utilization triggered by Adam's question after 8 NB01 debug iterations. Found that v1/v2 used ~40 % of the relevant `kbase_ke_pangenome` tables and 0 % of `kescience_*`. Most consequential miss: **`interproscan_domains` (833 M rows; 146 M Pfam hits across 132.5 M cluster reps; 83.8 % coverage) — the authoritative Pfam annotation source on BERDL.** v1 control detection used `eggnog_mapper_annotations.PFAMs` (domain *names*) which is fragile per the known `[snipe_defense_system]` pitfall; v2.1 switches to InterProScan as primary detection path. v2.1 also adds `interproscan_go` (266 M rows) and `interproscan_pathways` (287 M rows) as alternative function-class annotations for Phase 2 cross-validation. The Data Sources, Controls, and Phase 3 sections of this plan are updated accordingly. **Other under-used databases are documented but deferred** to later phases: `kescience_fitnessbrowser` (Phase 2/3 cross-validation), `kescience_alphafold`/`kescience_pdb` (Phase 3 architecture validation), `kescience_webofmicrobes`/`kescience_bacdive` (Phase 4 metabolic phenotype grounding), `genomad_mobile_elements` (Phase 2 MGE flag — verify ingestion first).

- **v2** (2026-04-26): Synthesis of two reviews — `PLAN_REVIEW_1.md` (claude standard reviewer) and `ADVERSARIAL_PLAN_REVIEW_1.md` (BERIL adversarial reviewer, depth=standard). Revisions, with the review that raised each:
  - **HIGH 1: Direction-inference reframe (adversarial I3)** — At family rank and above, full four-quadrant labels (Open / Broker / Sink / Closed) are not inferable without donor-recipient direction. Plan now uses **Producer × Participation categories** (Innovator-Isolated / Innovator-Exchange / Sink/Broker-Exchange / Stable) at deep ranks, with full quadrant labels reserved for genus rank in Phase 3 only. Pre-registered hypotheses reframed to deep-rank Producer × Participation form. This downgrade is conservative and honest about what acquisition-only inference can claim.
  - **HIGH 2: Multiple-testing strategy (adversarial C3)** — Hierarchical: Tier-1 headline regulatory-vs-metabolic at FWER<0.05 (1 test); Tier-2 four pre-registered focal tests at Bonferroni α=0.0125; Tier-3 atlas-level exploration descriptive with effect sizes and BH-FDR q<0.05 as exploratory annotation. KEGG BRITE B-level used to define regulatory-vs-metabolic categories.
  - **HIGH 3: Phase 1A pilot (adversarial recommendation)** — 1,000 species × 1,000 UniRef50 clusters + Alm 2006 TCS validation as pilot before Phase 1B full scale. Validates null model, multiple-testing, controls before scaling. Adds 1 week to budget.
  - **HIGH 4: Pfam pitfall citation correction (adversarial I5)** — Corrected citation from `[bakta_reannotation]` (which is a MinIO tenant naming pitfall) to `[plant_microbiome_ecotypes] bakta_pfam_domains query format` (pitfalls.md:1719); added Phase 2 spot-check sub-task for early audit risk surfacing.
  - **HIGH 5: Null model pseudocode + complexity (adversarial C4)** — Producer null and consumer null implementations specified with pseudocode, complexity estimates, and reduction tricks. Validation deferred to Phase 1A pilot.
  - **MEDIUM 6: Negative + positive controls (adversarial recommendation)** — Ribosomal proteins, tRNA synthetases, RNA polymerase as negatives; AMR genes, CRISPR-Cas, Alm 2006 TCS HKs as positives. Run alongside headline analysis at every phase.
  - **MEDIUM 7: KEGG BRITE B-level for regulatory-vs-metabolic (adversarial recommendation)** — replaces ad hoc category assignment.
  - **MEDIUM 8: Quantitative phase gates (both reviewers)** — All gates have explicit Cohen's d / FWER / q-value thresholds with effect-size floors.
  - **MEDIUM 9: UniRef50→KO concordance threshold validated empirically** — Phase 1B NB07 measures actual concordance distribution and adjusts the 80% threshold if needed.
  - **LOW 10: Per-phase query pattern commitments (standard reviewer)** — Phase 1A uses Pattern 1 on pilot subset; Phase 1B uses Pattern 2 per-species iteration; Phase 2 uses Pattern 1 on KO subsets; Phase 3 uses Pattern 1 on architecture census.
  - **LOW 11: Spark on-cluster import note (standard reviewer)** — Explicit `spark = get_spark_session()` with no import on JupyterHub notebooks.
  - **LOW 12: Within-species genome sampling strategy (user interjection during v2 drafting)** — Quality filter (CheckM ≥95% complete, ≤5% contam) + ANI-stratified subsampling + GTDB-rep inclusion, capped at 500. Explicit guard against clinical-isolate inflation in *E. coli*, *K. pneumoniae*, *S. aureus*. Validated per-species against ribosomal-protein paralog distribution.
  - **LOW 13: Species ID `--` handling explicit (standard reviewer)** — Exact equality with quoted strings for known reps; LIKE prefix only for exploratory grouping.

  Three adversarial critiques were considered and **not** incorporated:
  - C1 cite of Galperin 2018 (archaeal TCS) — not relevant; archaea are explicitly out of scope per constraint.
  - S1 "sequence-only Phase 1 amplifies sampling bias toward well-annotated lineages" — wrong; UniRef clustering depends on having a sequenced genome, not a high-quality annotation.
  - C1 "theoretical foundation insufficient" — partly fair, but DESIGN_NOTES.md already explicitly acknowledges weak-prior framing; the controls additions (MEDIUM 6) address the concrete part of the concern.

  Both review files are preserved in the project root as `PLAN_REVIEW_1.md` and `ADVERSARIAL_PLAN_REVIEW_1.md`. DESIGN_NOTES.md updated with v2 design rationale section linking each revision to its source review.

## Authors

- **Adam Arkin**
  - ORCID: 0000-0002-4999-2931
  - Affiliation: U.C. Berkeley / Lawrence Berkeley National Laboratory

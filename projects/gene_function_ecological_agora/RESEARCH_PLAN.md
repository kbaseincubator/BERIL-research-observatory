# Research Plan: Gene Function Ecological Agora

*Innovation Atlas Across the Bacterial Tree*

## Research Question

Across the prokaryotic tree (GTDB r214; 293,059 genomes / 27,690 species), do clades specialize in the *kind* of functional innovation they produce, and is the producer/consumer asymmetry observed by Alm, Huang & Arkin (2006) for two-component systems a general feature of regulatory function classes but not metabolic ones?

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
5. `05_p1b_full_data_extraction.ipynb` — full GTDB-rep extraction (conditional on Phase 1A pass)
6. `06_p1b_full_atlas.ipynb` — full clade × UniRef50 scores; KO-projection rail; rarefaction sensitivity
7. `07_p1b_bacteroidota_pul_test.ipynb` — pre-registered hypothesis verdict
8. `08_p1b_phase_gate.ipynb` — Phase 1B → Phase 2 gate decision

### Phase 1 Effort
**Phase 1A pilot ~1 week + Phase 1B full ~4 weeks = ~5 weeks total.** The pilot adds 1 week to v1's 4-week budget; this is purchased insurance against the failure mode (computational issues masquerading as biological absence).

---

## Phase 2 — Functional Resolution (KO, paralog-explicit)

**Question**: Does the deep-rank Producer × Participation pattern map onto KO-defined functional categories (KEGG BRITE B-level) the way the regulatory-vs-metabolic prior predicts? Does the Alm 2006 TCS back-test reproduce at KO level on the GTDB substrate?

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

## Phase 3 — Architectural Resolution & Direction (Pfam architecture, hybrid direction)

**Question**: Does the Producer × Participation structure survive at Pfam multidomain architecture resolution? Can the full four-quadrant labels (Open / Broker / Sink / Closed) be assigned at genus rank via composition-based donor inference on the candidate set, discriminating Innovator-Exchange into Open Innovator vs Sink-with-paralogs and discriminating Sink/Broker-Exchange into Broker vs Sink?

### Substrate
- **A. Function-class unit**: Pfam multidomain architecture (ordered set of Pfam domains)
- **B1. Within-clade family unit**: paralog-explicit; UniRef90 within architecture within clade
- **B2. Cross-clade orthology**: Pfam architecture identity (exact ordered match)
- **C. Direction inference**: Hybrid two-level. Phyletic-incongruence detects clade-pair acquisition events. Composition-based donor inference (codon usage Δ, dinucleotide signature) attempted **only for events called at genus rank**, with explicit confidence intervals. Genus-rank events are <10% of total; donor identity beyond genus is not reported.

### Bias Control Stack
- D1–D4 mandatory
- **Pfam audit** (mandatory pre-flight, *v2 citation correction*): For every architecture in the deep-dive candidate set, cross-check `bakta_pfam_domains` vs `eggnog_mapper_annotations.PFAMs`. The exact failure mode is **unresolved** in the BERDL docs: per docs/pitfalls.md `[plant_microbiome_ecotypes] bakta_pfam_domains query format — Pfam IDs may not match` (line 1719), querying `bakta_pfam_domains` with Pfam accessions like `'PF00771'` returned 0 hits across 11 domains tested, with the docs explicitly noting "*This pitfall needs further investigation to determine the correct query format.*" The audit must therefore test **both** possibilities: (a) format mismatch (PF00771 vs PF00771.1 vs domain name), and (b) genuine coverage gaps. Per the project memory note from `[plant_microbiome_ecotypes]`, 12 of 22 marker Pfams tested were silently missing from `bakta_pfam_domains` in that prior audit — this is what made the pitfall non-negotiable here. Flag any discrepancy >20%. Recompute via HMMER on `gene_cluster.faa_sequence` for any flagged headline architecture. *(v1 cited the wrong pitfall handle, `[bakta_reannotation]`, which in pitfalls.md actually refers to a MinIO-tenant naming issue. The adversarial reviewer caught this; the v2 citation is correct.)*
- **Phase 2 spot-check** (added in v2 per standard reviewer recommendation): Before Phase 2 ends, run the audit on TCS HK Pfam set (PF00512, PF00072) and on PSII Pfam set (PF00124, PF02530, PF02533) to surface any audit failures early. These are the architectures Phase 3 most depends on.
- UniRef50 robustness rail
- Sensitivity: PIC on producer scores; per-clade jackknife on architecture census

### Phase 2 Handoff Use
- `p2_architectural_deepdive_candidates.tsv` defines the architecture census target. Phase 3 does not run a full GTDB-scale Pfam architecture census; it runs the deep-dive on the candidate KOs from Phase 2. This makes Phase 3 ~30–40% cheaper than a standalone architectural atlas.

### Pre-registered Prediction (Phase 3)

**Cyanobacteria → Broker quadrant for photosystem II Pfam architectures** (PF00124 + PF02530 + PF02533 set, plus extended PSII protein architectures). *Note: Phase 3 is the **only** phase where the full four-quadrant labels (Open / Broker / Sink / Closed) apply, because Phase 3 runs composition-based donor inference at genus rank for clade-pair events on the candidate set. At family rank and above, the prediction reduces to "Sink/Broker-Exchange" (low producer + high participation) per the Producer × Participation framing.*

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

### Phase 3 Output Products
- `data/p3_pfam_architecture_atlas.parquet` — clade × architecture producer/consumer scores on the candidate set
- `data/p3_pfam_architecture_categories.tsv` — Producer × Participation category assignments at deep ranks (architecture level)
- `data/p3_pfam_architecture_quadrants_genus.tsv` — full four-quadrant labels at genus rank only (after donor inference)
- `data/p3_cyanobacteria_psii_test.tsv` — pre-registered hypothesis verdict
- `data/p3_genus_rank_donor_inference.tsv` — composition-based donor inference at genus rank with confidence intervals
- `data/p3_alm_2006_architectural_backtest.tsv` — full HK Pfam architecture census within the candidate set; comparison to Phase-2 KO-level back-test
- `data/p3_pfam_completeness_audit.tsv` — audit results, recompute decisions

### Phase 3 Gate to Phase 4 (quantitative thresholds, v2)
Unconditional, but with a quality threshold: Phase 4 synthesis treats Phase 3 architectural results as **confirmatory** (rather than exploratory) only when architectural-vs-KO concordance ≥ 60% on the Phase-2 candidate set. Below that, Phase 4 treats Phase 3 as exploratory commentary and the headline atlas claims rest on Phase 1B + Phase 2. Either way, synthesis runs.

### Phase 3 Notebooks
16. `16_p3_pfam_completeness_audit.ipynb` — full audit of `bakta_pfam_domains` for all candidate-set architectures; HMMER recompute decision
17. `17_p3_architecture_atlas.ipynb` — clade × architecture producer/participation scores on candidate set
18. `18_p3_cyanobacteria_psii_test.ipynb` — pre-registered hypothesis verdict
19. `19_p3_genus_rank_donor_inference.ipynb` — composition-based donor inference + confidence intervals; full four-quadrant labels at genus rank
20. `20_p3_alm_2006_architectural_backtest.ipynb` — TCS HK reproduction at architecture level (genus + family rank)

### Phase 3 Effort
~5 agent-weeks (reduced from a standalone ~7–8 due to Phase-2 candidate targeting).

---

## Phase 4 — Cross-Resolution Synthesis

**Question**: At which resolutions and for which clades × function classes do the **Producer × Participation category assignments** concord (Phase 1B + Phase 2 + Phase 3 deep-rank) AND where Phase 3 genus-rank donor inference resolves the full four-quadrant labels — what is the resulting atlas verdict? Where resolutions conflict, what does the conflict reveal?

*v2 reframe: Phase 4 must explicitly distinguish deep-rank Producer × Participation atlas assignments (which span all three resolutions and all ranks) from genus-rank full-quadrant labels (which exist only in Phase 3 on the candidate set). The synthesis report has two parallel threads: a deep-rank atlas and a genus-rank quadrant table.*

No new data extraction. Phase 4 joins Phase 1 / 2 / 3 outputs.

### Phase 4 Output Products
- `data/p4_deep_rank_concordance.tsv` — for each (clade × function-class) tuple represented at ≥2 resolutions (Phase 1B UniRef50 / Phase 2 KO / Phase 3 architecture), list Producer × Participation category at each resolution + concordance score
- `data/p4_genus_rank_quadrants.tsv` — full four-quadrant labels (Open / Broker / Sink / Closed) on the Phase-3 candidate set at genus rank only, with Phase-3 donor-inference confidence intervals
- `data/p4_concordance_weighted_atlas.parquet` — final atlas with confidence weights from cross-resolution agreement
- `data/p4_conflict_analysis.tsv` — clade × function tuples where resolutions disagree, with hypotheses for why
- `data/p4_pre_registered_verdicts.tsv` — four pre-registered hypotheses (Phase 1B: Bacteroidota PUL; Phase 2: Mycobacteriota mycolic-acid; Phase 3: Cyanobacteria PSII; Phases 2+3: Alm 2006 TCS back-test) as supported / falsified / equivocal with explicit evidence
- `figures/p4_atlas_heatmap.png` — clade × function-class Producer × Participation heatmap (deep-rank, all ranks)
- `figures/p4_genus_rank_flow_network.png` — directed clade-to-clade function-flow graph at genus rank only (Phase-3 candidate set)
- `figures/p4_four_quadrant_summary.png` — named clades populating each quadrant at genus rank per Deliverable 4
- `REPORT.md` — final synthesis writeup with explicit deep-rank vs genus-rank claim separation

### Phase 4 Notebooks
21. `21_p4_cross_resolution_concordance.ipynb` — Producer × Participation category-assignment join across Phase 1B / 2 / 3
22. `22_p4_atlas_visualization.ipynb` — deep-rank heatmap + genus-rank directed network + four-quadrant summary at genus rank
23. `23_p4_synthesis_writeup.ipynb` — pre-registered verdicts, conflict analysis, final figures, deep-rank vs genus-rank claim separation

### Phase 4 Effort
~2 agent-weeks (synthesis writing, comparative analysis, figures).

---

## Data Sources

### BERDL tables (`kbase_ke_pangenome` unless noted)
- `genome` (293K rows) — genome → gtdb_species_clade_id, has_sample
- `gtdb_taxonomy_r214v1` (293K rows) — full lineage per genome
- `gtdb_metadata` (293K rows) — CheckM completeness, contamination, GC%, assembly level
- `gtdb_species_clade` (28K rows) — clade-level ANI stats
- `gene_genecluster_junction` (1B rows) — genome → gene_cluster_id (filter required, never full-scan)
- `gene_cluster` (133M rows) — cluster representatives, faa_sequence, fna_sequence, isCore/isAccessory/isSingleton flags
- `eggnog_mapper_annotations` (94M rows) — KO, COG, EC, KEGG, PFAM per cluster
- `bakta_db_xrefs` (572M rows) — gene_cluster_id → UniRef50/UniRef90/UniRef100 (filter required, disable autoBroadcast on `kbase_uniprot.uniprot_identifier` joins)
- `bakta_pfam_domains` (19M rows) — Pfam domains per gene_cluster_id (subject to completeness audit)
- `kbase_uniref50` (100K rows) — UniRef50 cluster table
- `kbase_uniref90` (100K rows) — UniRef90 cluster table
- `genome_ANI` (421M rows) — pairwise within-species ANI (used for D4 within-species genome ranking)
- `ncbi_env` (4M rows) — environmental metadata where genome.has_sample = true (advisory only)

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

- **Ribosomal proteins**: Pfam clan CL0623 (small subunit), CL0626 (large subunit); KEGG ko03010 (`Ribosome`)
- **tRNA synthetases**: KEGG `09183 Translation factors` aminoacyl-tRNA synthetase set
- **RNA polymerase core subunits**: KEGG K03040 (rpoA), K03043 (rpoB), K03046 (rpoC)

If any of these show producer score > 1 σ above the global mean in any major phylum, the method is over-detecting paralog expansion and the null model needs recalibration.

#### Positive controls (expected: detectable acquisition signal in clades known to have acquired via HGT)

- **Antibiotic-resistance gene families**: CARD-mapped UniRef50 clusters (via eggNOG annotation), expected to show high consumer / participation scores in clades with documented AMR HGT (Enterobacteriaceae, Acinetobacter, Pseudomonadaceae)
- **CRISPR-Cas systems**: Pfam clan CL0114 (Cas family), expected to show clade-pair incongruent presence consistent with HGT (Metcalf et al. 2014)
- **Alm 2006 TCS HKs**: Pfam PF00512 (HisKA) + PF00072 (Response_reg); the methodological gold standard

If any positive control fails to show acquisition signal in clades with documented HGT history, the consumer-score implementation is under-sensitive.

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
| Phase 3 | ~5 weeks | 15 | Yes — publishable architectural validation + genus-rank quadrant labels |
| Phase 4 | ~2 weeks | 17 | Final synthesis |

**Total ~17 agent-weeks** (v2 added the 1-week Phase 1A pilot to the v1 16-week budget). Four natural commit points; Phase 1A is the most consequential — it can stop the project before any heavy compute starts if the null model fails to reproduce Alm 2006 at pilot scale or controls fail.

## Revision History

- **v1** (2026-04-26): Initial plan. Three-phase forced-order atlas; pre-registered hypotheses with weak-prior calibration; design reasoning captured separately in DESIGN_NOTES.md.

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

# Design Notes: Gene Function Ecological Agora

This document captures the *reasoning behind* the research plan — the critique of the original brief, the through-line logical argument, the rejected alternatives, the explicit acknowledgement that the pre-registered hypotheses are weak priors, and (added in v2) the trace of how each subsequent revision was raised and resolved. It is written for future readers (human or agent) who need to understand *why* the plan is shaped this way.

`RESEARCH_PLAN.md` is the operational plan. This document is the design record. Read both.

> **v2 (2026-04-26)**: Plan revised in response to two parallel reviews — `PLAN_REVIEW_1.md` (claude standard reviewer) and `ADVERSARIAL_PLAN_REVIEW_1.md` (BERIL adversarial reviewer). The most consequential revision is the **Producer × Participation reframe**: at family rank and above, full four-quadrant labels (Open / Broker / Sink / Closed) are not inferable without donor-recipient direction, so the atlas reports two scores (Producer, Participation) and a 2×2 cross-classification at deep ranks; the full quadrant labels apply only at genus rank in Phase 3. This downgrade is conservative and honest about what acquisition-only inference can claim. Other v2 revisions added a Phase 1A pilot, a hierarchical multiple-testing strategy with 4 pre-registered focal tests, positive/negative controls, KEGG BRITE B-level for category definitions, and corrected a misattributed Pfam pitfall citation. See "v2 Revision Trace" section below for the full decision record.

---

## Original Brief (summary)

The user proposed a multi-resolution stratified tensor:

> *(clade × function-class × phylogenetic-depth) → (producer, consumer)*

with two derived outputs (a clade × function-class heatmap and a directed clade-to-clade flow network), an interpretive engine of four quadrants (Closed Innovator / Broker / Sink / Open Innovator), and a mandatory back-test against Alm, Huang & Arkin (2006).

The brief specified seven mandatory deliverables, six methodological axes (A: function-class unit; B1: within-clade family unit; B2: cross-clade orthology; C: HGT direction inference; D: bias-control stack; E: validation systems beyond the back-test), and asked for three distinct research plans differing on ≥3 axes with ≥1 difference in A/B1/C.

Three plans were drafted (Plan 1: KO-Pangenome; Plan 2: Pfam-Architecture; Plan 3: UniRef50 Sequence-Cluster) and the user committed to running all three in sequence with explicit gates between phases.

---

## Critique of the Original Brief

The brief's strengths are real and were preserved: phylogenetic depth as a *structural* axis (not a covariate), the mandatory Alm 2006 back-test, the four-quadrant model with an explicit fallback to "innovation in/out are correlated", and the per-clade × function × quadrant prediction requirement (Deliverable 6).

The substantive pushback that shaped the plan:

1. **D2 alone does not bound EggNOG annotation-density bias.** Annotation density is *systematically* lower in CPR/DPANN/poorly-cultivated lineages, which means patchy distribution will look like *acquisition* into well-annotated clades and *de novo invention* by them. Linear residualization does not fix non-additive bias. Mitigation: a sequence-only resolution (UniRef50) is mandatory as a robustness rail under any KO/COG-based headline. This pushed Plan 3 to the front of the sequence and made the UniRef50 rail mandatory in all phases.

2. **"Producer score above a tree-aware null" is the methodological core, and "tree-aware null" hides several distinct nulls.** Each phase must commit to a specific null model. The plan commits to a clade-matched neutral-family null for the producer score and a phyletic-distribution permutation null for the consumer score, both implementable in Spark.

3. **The four quadrants are not symmetrically detectable.** Open Innovator and Broker both have high outflow; the discriminator is the producer score, which is exactly the score most exposed to bias #1. The most distinctive prediction of the framework is also its least bias-robust component. The plan acknowledges this in writing and stages the Open-vs-Broker discrimination at Phase 3 (Pfam architecture, with paralog-explicit clustering) where the producer score has its highest grain.

4. **Direction inference at GTDB-r214 scale is mostly impossible.** Composition-based donor inference (codon usage, GC, k-mers) is unreliable for any event older than ~10–100 Myr (post-amelioration). Phyletic-incongruence aggregation gives clade-pair *acquisition* signal but no direction. Per-family DTL reconciliation is explicitly out of scope at full scale. The plan is therefore acquisition-only at family rank and above; composition-based donor inference is attempted only at genus rank, with explicit confidence intervals and only for the Phase 3 candidate subset.

5. **Phylogenetic depth in BERDL is not a free variable.** BERDL has GTDB taxonomy and within-species ANI, but the global GTDB-r214 species tree is not in the lakehouse. The global tree is loaded externally from `data.gtdb.ecogenomic.org`. The depth axis becomes the GTDB rank scaffold (species / genus / family / order / class / phylum / domain), with the global tree only used for D4 rank-level topology-support filtering.

6. **Cross-clade orthology via the pangenome's `gene_cluster_id` is impossible by construction.** The pangenome's clusters are species-specific (a documented BERDL pitfall). All three phases use UniRef-tier cluster co-membership or Pfam-architecture matching as the cross-clade ortholog proxy. No phase uses `gene_cluster_id` for cross-species joins.

7. **Bakta Pfam domains are systematically incomplete.** Per `docs/pitfalls.md` [bakta_reannotation], 12 of 22 marker Pfams were silently missing from `bakta_pfam_domains` in a prior project. Phase 3 — which puts headline weight on Pfam architecture — has a mandatory pre-flight audit with HMMER recompute fallback. This is non-negotiable.

8. **Validation set E demands ≥1 metabolic system with internal heterogeneity.** Pure-import systems (AMR, CRISPR-Cas) are explicitly secondary controls in the brief; they validate detection of acquisition but not the four-quadrant interpretation. The plan picks Bacteroidota CAZymes (Phase 1), Mycobacteriota mycolic-acid (Phase 2), and Cyanobacteria PSII (Phase 3) — three systems with documented internal heterogeneity, spanning the regulatory-vs-metabolic divide deliberately so the user's central prior can fail informatively at Phase 1.

9. **Effort budget in the original brief was hidden.** The plan costs ~16 agent-weeks total with three natural commit points (Phase 1, 2, and 3 each have publishable artifacts). Phase 1's stop-point is the most consequential — it can definitively kill the four-quadrant claim before any heavy compute starts.

10. **The framing decision.** The user asked for the multi-resolution stratified tensor to remain open to alternative framings (flat atlas with depth as covariate; genomic-context-stratified; ecological-niche-stratified). The plan keeps the multi-resolution stratified tensor *only because* Deliverable 6 (named-clade × function × quadrant predictions explained from priors) is enforced. Without that enforcement, the framework slides into a flat-atlas with a depth decoration.

---

## Why Three Phases, In This Order

The forced-order argument:

1. **Existence before resolution**. The atlas claim depends on the four-quadrant structure being real, not an artifact of bias. Phase 1 (UniRef50, sequence-only) is the only resolution that can falsify the bias-artifact alternative cleanly. Therefore Phase 1 must come first.

2. **Sequence existence does not answer the headline**. The headline regulatory-vs-metabolic claim requires functional categorization, which UniRef50 does not provide. Phase 2 (KO) is the natural resolution for the headline test. But Phase 2's KO-defined results are vulnerable to the very bias Phase 1 ruled out at the sequence level. Phase 1's UniRef50→KO projection table tells Phase 2 which KOs are sequence-anchored vs annotation-driven only — Phase 2 can weight or filter accordingly. Therefore Phase 2 follows Phase 1 with a specific data-handoff, not just chronologically.

3. **Alm 2006 is at architectural resolution, and architecture is expensive**. Generalizing or refuting Alm 2006 requires reproducing the analysis at Pfam architecture grain. But architecture-level analysis is ~2× the cost of KO-level and most informative when targeted — and Phase 2 produces the targeting (which KOs warrant architectural deep-dive). Therefore Phase 3 follows Phase 2 with a candidate-list handoff.

4. **The synthesis is the deliverable, not an epilogue**. The three-resolution design is forced by the bias argument; cross-resolution concordance is the strongest claim the atlas can make; cross-resolution conflict is the most informative failure mode. Phase 4 is mandatory.

This is a *forced* order. Reordering loses the bias-protection logic of Phase 1 first; skipping the handoffs makes each phase a standalone atlas that does not benefit from the others.

---

## Why The Pre-Registered Hypotheses Are Weak Priors

The pre-registered hypotheses are:
- **Phase 1**: Bacteroidota → Open Innovator on PUL CAZymes
- **Phase 2**: Mycobacteriota → Closed Innovator on mycolic-acid pathway
- **Phase 3**: Cyanobacteria → Broker on PSII architectures

**None of these are confidently held.** They are best-guess pre-registrations chosen to make each phase's test concrete and to span the regulatory-vs-metabolic divide. Each has *some* literature support, but the *quadrant assignment* specifically is more guess than prior:

- **Bacteroidota PUL**: Smillie 2011 supports outflow; documented CAZyme paralog expansion supports producer score. But whether this combination places Bacteroidota in Open Innovator vs Broker (if outflow is HGT-driven inwards) vs Closed Innovator (if outflow is gut-resident-only) vs on-diagonal — this we do not know.

- **Mycobacteriota mycolic-acid**: cell-envelope coupling supports low outflow; lineage definition supports producer score. But whether the recent paralog expansion in *M. tuberculosis* lineage is detectable above the null vs the older *Corynebacteriales* common-ancestor inheritance dominating — this we do not know.

- **Cyanobacteria PSII**: ancient HGT to Chloroflexota supports outflow; PSII protein conservation suggests low recent paralog expansion. But whether Synechococcus/Prochlorococcus psbA copy variation crosses the producer threshold — this we do not know.

**The atlas's value is therefore partly in producing such verdicts and feeding them back into prior-formation.** Falsification of any pre-registered prediction is a finding, not a project failure. The post-hoc analysis ("the alternative quadrant we found is consistent with X") becomes part of the contribution, not a save.

This framing is non-trivial: it changes how the writeup treats failure modes. The standard "we predicted X, we found X, therefore the framework works" structure is replaced with "we made falsifiable verdicts on systems where the field's quantitative priors are weak; here are the verdicts; here is how the verdicts update the priors." The framework's value is in making the verdicts *concrete enough to be falsifiable*, not in being right about the verdicts.

---

## Rejected Alternative Framings

The original brief left these open. The plan rejects them, with reasons:

### Flat (clade × function-class) atlas with phylogenetic depth as a covariate
**Rejected because**: depth is the timescale axis. Treating it as a covariate collapses ancient and recent events into one number per clade × function. The mandatory Alm 2006 back-test specifically tests a *recent paralog expansion* signal — collapsing depth makes the back-test impossible to reproduce. Kept depth as a structural axis.

### Genomic-context-stratified instead of phylogenetically-stratified
**Rejected because**: genomic context (chromosome vs plasmid vs phage) is informative but is not the user's primary axis of interest. The research question is about *clades* specializing, which requires phylogeny as the primary scaffold. Genomic context is reserved as a possible Phase 3 advisory annotation (e.g., "Bacteroidota PUL UniRef50 acquisitions in Firmicutes are predominantly chromosomal vs predominantly plasmid-borne").

### Ecological-niche-stratified using NCBI environmental metadata
**Rejected because**: per `docs/overview.md`, NCBI environmental metadata is sparsely populated, especially for non-host samples. Per `docs/pitfalls.md`, ENIGMA SFA genus-level taxonomy is too coarse for species-level inference. Building the headline atlas on a sparsely-populated covariate would compromise the headline. Niche stratification is reserved as a Phase 4 advisory annotation: for clades where Phase 1–3 produce a quadrant verdict, the niche metadata is reported as commentary on plausible ecological interpretation.

---

## Known Scope Limits

What this atlas explicitly will not cover:

- **Direction at deep ranks**: no DTL recon at full GTDB scale (constraint). Direction is reported only at genus rank, with confidence intervals, in Phase 3.
- **CPR / DPANN under-representation**: acknowledged scope limit. The atlas does not claim coverage of poorly-sampled lineages at deep ranks. D3 effective-N reporting flags this per phase.
- **Eukaryotic / archaeal-bacterial inter-domain transfer**: out of scope (constraint).
- **Absolute molecular-clock dating**: out of scope (constraint). Depth is GTDB-rank-relative only.
- **Wet-lab or fitness/phenotype integration**: out of scope (constraint). Available in BERDL but not used for the atlas claim.
- **Building new orthogroups from scratch at full GTDB scale**: out of scope (constraint). Cross-clade orthology uses UniRef cluster co-membership or Pfam architecture matching, both pre-computed.

---

## What This Atlas Will NOT Settle (even if all phases succeed)

- **Why** clades fall in their assigned quadrants (mechanism). The atlas describes the pattern; mechanism requires per-clade, per-system biological investigation. Phase 4 advisory commentary will speculate but the atlas does not claim mechanism.
- **Whether the producer signal is paralog expansion vs ortholog displacement**. Alm 2006 distinguished these via gene-tree shape; this plan can only do so at the architectural-resolution Phase 3 step on the candidate subset, and only with ortholog-displacement detection limited by the no-DTL-recon constraint.
- **The relative timing of HGT events at deep ranks**. Depth is rank-level, not absolute time.
- **Whether the atlas patterns hold in the next GTDB release**. UniRef cluster boundaries and GTDB taxonomy both shift between releases; the atlas is keyed to GTDB r214 and one specific UniRef release.
- **Whether annotation-density bias is fully removed**. The three-resolution design *bounds* the bias rather than removing it. Concordance across resolutions is the strongest defense; it is not a proof.

---

## Stop-Point Decisions

The plan has three natural stop-points where the project can be paused or terminated with a publishable artifact:

| Stop point | Trigger | Publishable as |
|---|---|---|
| After Phase 1 | No four-quadrant structure detectable at sequence level | Negative result on diagonal-collapse fallback; methodological contribution on three-resolution design |
| After Phase 2 | Strong-form regulatory-vs-metabolic asymmetry confirmed and Alm 2006 back-test holds | Functional atlas at KO resolution with mycolic-acid case study |
| After Phase 3 | Architectural resolution confirms Phase 2; Cyanobacteria PSII verdict produced | Three-resolution atlas without final synthesis (Phase 4 deferrable) |
| After Phase 4 | Cross-resolution synthesis complete | Full atlas paper |

The Phase-1 stop-point is the most consequential. It can definitively kill the four-quadrant claim before the heavy compute (Phases 2 and 3) starts. This is a feature of the design, not a risk.

---

## Open Methodological Choices Committed Vs Deferred

### Committed at plan time
- Function-class unit per phase: UniRef50 / KO / Pfam architecture
- Cross-clade orthology proxy per phase: UniRef90 co-membership / Pfam architecture identity
- Direction inference policy per rank: acquisition-only ≥ family rank; hybrid at genus rank only
- Bias control mandatory stack: D1 (species dedup) + D2 (annotation-density residualization) + D3 (effective N reporting) + D4 (rank-level topology-support filter)
- Null model for producer: clade-matched neutral-family null
- Null model for consumer: phyletic-distribution permutation null
- Pre-registered hypothesis per phase (with weak-prior calibration)

### Deferred to phase entry
- **Specific KO list defining "regulatory" vs "metabolic" categories** (Phase 2). KEGG pathway-membership is the starting point; will be refined at Phase 2 NB06 entry against the actual KO frequency distribution in the corpus.
- **Specific UniRef50 set defining "PUL CAZymes"** (Phase 1). CAZy GH/CBM Pfam projection is the starting point; will be refined at Phase 1 NB04 entry.
- **Whether Phase 3 requires HMMER recompute on >25% of headline architectures** (Phase 3). If yes, costs are revisited and Phase 3 may extend by ~1–2 weeks.
- **Whether to run Phase 4 immediately after Phase 3 or defer** (Phase 3 exit). Decided at Phase 3 phase-gate notebook based on result quality.

---

## v2 Revision Trace (2026-04-26)

This section documents how each v2 revision was raised, what it changed, and what alternative framings were considered and rejected. The trace is the key audit artifact — it lets a future reviewer ask "*why* does the plan have a Phase 1A pilot?" and find both the source of the concern (which review raised it) and the reasoning for the chosen response.

### v2 Revision 1 (HIGH): Producer × Participation reframe at deep ranks

**Raised by**: Adversarial review I3 — *"If outflow direction cannot be reliably determined, this discrimination [Open Innovator vs Broker, and Open Innovator vs Sink-with-paralogs] cannot be made."*

**The concrete issue**: Without donor-recipient direction at deep ranks, "outflow from clade C" is not separable from "shared incongruent presence between C and other clades." Two distinct biological scenarios — "C donated to D" (Open Innovator) and "C and D both received from Z" (both Sink) — produce the same observable signal. Per the project's hard constraint that no per-family DTL reconciliation runs at full GTDB scale, direction at family rank and above is genuinely uninferable.

**v1 was wrong about this**: v1 named "Open Innovator (high producer + high outflow)" and "Sink (high inflow)" as distinguishable quadrants at all ranks. v1 acknowledged the Open-vs-Broker confusion (via critique #3 in v1 DESIGN_NOTES) but missed the symmetrical Open-vs-Sink confusion. The adversarial reviewer caught it.

**v2 response**: At family rank and above, the atlas reports **Producer × Participation categories** (Innovator-Isolated / Innovator-Exchange / Sink-Broker-Exchange / Stable). Full four-quadrant labels (Open / Broker / Sink / Closed) apply *only* at genus rank in Phase 3 where composition-based donor inference is run on the candidate set. Pre-registered hypotheses reframed:
- Phase 1B: Bacteroidota → **Innovator-Exchange** (was Open Innovator at deep ranks; Open Innovator interpretation reserved for Phase 3 genus-rank confirmation)
- Phase 2: Mycobacteriota → **Innovator-Isolated** (was Closed Innovator at deep ranks; Closed Innovator labeling reserved for Phase 3 genus-rank confirmation)
- Phase 3: Cyanobacteria → **Sink/Broker-Exchange at deep ranks; Broker at genus rank** (the only phase where the full label applies, since Phase 3 runs the donor inference)

**Alternatives considered and rejected**:
- *Reject the adversarial critique and keep v1 framing*: rejected. The critique is structurally sound and v1's framing claimed a discrimination it could not make.
- *Run per-family DTL reconciliation*: rejected. Out of scope per the original hard constraint; AleRax on principled subsamples is reserved for follow-up work.
- *Restrict the entire atlas to genus rank*: rejected. Loses the deep-rank specialization claim entirely; the Producer × Participation framing is more honest *and* preserves the deep-rank atlas.

**Cost of the revision**: Pre-registered hypotheses lose some sharpness (we cannot confirm "Open Innovator" at deep ranks, only "Innovator-Exchange"). This is the right cost; honesty matters more than the sharper-but-unsupportable claim.

### v2 Revision 2 (HIGH): Hierarchical multiple-testing strategy

**Raised by**: Adversarial review C3 — *"3.46+ billion statistical tests requiring FDR correction (Bonferroni-equivalent threshold: 1.44×10⁻¹¹)."*

**The concrete issue**: Naive per-(clade × function × rank) testing across the atlas yields 10⁸–10¹⁰ tests after D4 filtering. Either Bonferroni correction at α=10⁻¹¹ (which gives the headline regulatory-vs-metabolic test no statistical power) or BH-FDR with no scientific anchor (which inflates false positives in atlas exploration).

**v2 response**: Three-tier hierarchy. **Tier 1**: 1 headline test (regulatory-vs-metabolic at KEGG BRITE B-level) at FWER<0.05. **Tier 2**: 4 pre-registered focal tests (3 phase predictions + Alm 2006 back-test) at Bonferroni α=0.0125. **Tier 3**: per-tuple atlas exploration as **descriptive** effect-size + 95% CI; BH-FDR q<0.05 reported as exploratory annotation, not as confirmed claims. The atlas is a hypothesis-generating resource at the per-tuple level; per-tuple claims require independent validation.

**Alternatives considered and rejected**:
- *Per-test BH-FDR with effective-N cluster correction only*: rejected. Conflates atlas exploration with confirmation. The hierarchy enforces the distinction.
- *Drop the per-tuple atlas reporting entirely*: rejected. The atlas is the deliverable; we want it generative.

### v2 Revision 3 (HIGH): Phase 1A pilot

**Raised by**: Adversarial review constructive recommendations — *"Phase 1 pilot on representative subset… reduce Phase 1 scope to 1,000 representative species and 1,000 UniRef50 clusters to validate methodology before full-scale execution."*

**The concrete issue**: v1's Phase 1 went straight to GTDB-scale. If the null model fails, or the multiple-testing strategy is mis-specified, or the controls reveal calibration issues, the failure mode would only surface after weeks of compute on the full 27.7K-species substrate. The adversarial reviewer's S2 ("Phase 1 may fail for computational rather than biological reasons, terminating the entire project despite valid higher-resolution signals") makes this concrete.

**v2 response**: Phase 1 split into Phase 1A (pilot, 1K species × 1K UniRef50s + Alm 2006 TCS validation) and Phase 1B (full scale). Phase 1A includes positive/negative controls and the Alm 2006 reproduction; Phase 1A → Phase 1B gate has explicit pass/recalibrate/stop criteria. Adds 1 week to the budget; buys insurance against the failure mode.

**Alternatives considered and rejected**:
- *Skip pilot, accept the risk*: rejected. The 1-week pilot cost is dwarfed by the 4-week full-scale cost, and a pilot failure that catches a null-model bug saves the project.

### v2 Revision 4 (HIGH): Pfam pitfall citation correction

**Raised by**: Adversarial review I5 — *"This pitfall does not exist in the current pitfalls documentation."*

**The concrete issue**: v1 cited `docs/pitfalls.md [bakta_reannotation]` as the source for the "12/22 marker Pfams silently missing from `bakta_pfam_domains`" claim. The `[bakta_reannotation]` handle in pitfalls.md is in fact a MinIO tenant-naming pitfall, not a Pfam-completeness pitfall. The 12/22 claim came from project memory (`MEMORY.md → plant_microbiome_ecotypes`), and the closest matching pitfall is `[plant_microbiome_ecotypes] bakta_pfam_domains query format — Pfam IDs may not match` (pitfalls.md:1719), which the docs explicitly mark as "*This pitfall needs further investigation to determine the correct query format.*"

**v2 response**: Citation corrected to `[plant_microbiome_ecotypes] bakta_pfam_domains query format`. Added Phase 2 spot-check sub-task on TCS HK Pfams + PSII Pfams to surface audit risk before Phase 3. The Phase 3 audit becomes *more* important because the cause (format mismatch vs true coverage gap) is unresolved.

**This was a genuine error in v1**: the misattributed citation would have been confusing or misleading to anyone trying to chase the prior. The adversarial reviewer's catch is exactly what an external reviewer is for.

### v2 Revision 5 (HIGH): Null model pseudocode + complexity

**Raised by**: Adversarial review C4 — *"The plan commits to 'clade-matched neutral-family null' and 'phyletic-distribution permutation null' but provides no implementation details, no complexity estimates, and no validation against known systems."*

**The concrete issue**: v1 named the null types but left implementation as TBD. The methodological core is precisely what cannot be vague.

**v2 response**: Pseudocode for both nulls (producer score and consumer score), complexity estimates with reduction tricks for full-scale tractability, validation deferred to Phase 1A pilot (the pilot's gate criteria *include* whether the null model reproduces Alm 2006 at pilot scale). Added Participation score formal definition (the deep-rank surrogate for outflow per Revision 1).

### v2 Revisions 6 & 7 (MEDIUM): Negative controls + KEGG BRITE categorization

**Raised by**: Adversarial review constructive recommendations.

**The concrete issue**: v1 had no negative controls. Without ribosomal-protein-style negatives, a positive headline result cannot be distinguished from a method that produces apparent specialization for everything. v1 also used "regulatory" and "metabolic" as ad hoc category labels; this was a poorly-defined baseline for the headline test.

**v2 response**: Negative controls (ribosomal proteins, tRNA synthetases, RNAP core) and positive controls (AMR, CRISPR-Cas, Alm 2006 TCS HKs) added to every phase's bias-control stack. KEGG BRITE B-level (`09100 Metabolism`, `09120 Genetic Information Processing`, `09130 Environmental Information Processing`) replaces ad hoc category assignment.

### v2 Revision 8 (MEDIUM): Quantitative phase gates

**Raised by**: Both reviewers — *"≥30% off-diagonal needs effect-size threshold" (standard); "specialization operationally vague" (adversarial)*.

**v2 response**: All phase gates have explicit Cohen's d / FWER / q-value thresholds with effect-size floors. Phase 1A gate (controls), Phase 1B gate (≥10% off-(low,low) at q<0.05 with d≥0.3), Phase 2 gate (Tier-1 FWER<0.05 + Tier-2 Bonferroni α=0.0125), Phase 3 gate (architectural-vs-KO concordance ≥60%).

### v2 Revision 9 (MEDIUM): UniRef50→KO concordance threshold validated empirically

**Raised by**: Adversarial review I6 — *"plan provides no assessment of whether the 80% threshold is achievable."*

**v2 response**: Phase 1B NB07 measures the actual concordance distribution and adjusts the 80% threshold if needed. Threshold may be data-driven (e.g., the threshold at which 70% of UniRef50s pass).

### v2 Revisions 10–13 (LOW): Operational sharpening

**Raised by**: Standard reviewer mostly; Revision 12 raised by user during v2 drafting.

- **Per-phase query pattern commitments** — Phase 1A → Pattern 1; Phase 1B → Pattern 2 per-species; Phase 2/3 → Pattern 1 IN-clause.
- **Spark on-cluster import** — `spark = get_spark_session()` no import.
- **Within-species genome sampling** — Quality filter (CheckM ≥95% complete, ≤5% contam) + ANI-stratified subsampling + GTDB-rep inclusion, capped at 500. Guards against clinical-isolate inflation in *E. coli* / *K. pneumoniae* / *S. aureus*.
- **Species ID `--` handling** — Exact equality with quoted strings for known reps; LIKE prefix only for exploratory grouping.

### Adversarial critiques considered and *not* incorporated

- **C1 cite of Galperin 2018 (archaeal TCS differs)** — not relevant. Archaeal-bacterial inter-domain transfer is explicitly out of scope per the original hard constraint. The atlas is bacteria-only.
- **S1 "sequence-only Phase 1 amplifies sampling bias toward well-annotated lineages"** — wrong. UniRef clustering depends on having a sequenced genome (which all GTDB genomes have by definition), not on having a high-quality annotation. Sequence-only is *less* sensitive to annotation quality, not more.
- **C1 "theoretical foundation insufficient" (the broad form)** — partly fair, but DESIGN_NOTES.md v1 already explicitly acknowledged weak-prior framing, which the adversarial reviewer did not fully credit. The concrete sub-concerns (positive/negative controls) are addressed via Revision 6.

---

## Authors

- **Adam Arkin**
  - ORCID: 0000-0002-4999-2931
  - Affiliation: U.C. Berkeley / Lawrence Berkeley National Laboratory

## Document History

- **2026-04-26 (v1)**: Initial design notes captured at project creation. Reflects the conversation reasoning leading to the three-phase plan, the weak-prior framing of pre-registered hypotheses, and the rejection of alternative atlas framings.
- **2026-04-26 (v2)**: Added v2 Revision Trace section documenting the changes prompted by `PLAN_REVIEW_1.md` and `ADVERSARIAL_PLAN_REVIEW_1.md`. Most consequential change: Producer × Participation reframe at deep ranks. Within-species genome sampling strategy added in response to a user interjection during v2 drafting.

- **2026-04-27 (v2.4 — Alm 2006 close-reading discovery)**: Triggered by adversarial review flagging Cohen's d mismatch + the user asking "should we review the Alm paper?" Close read of the Alm 2006 paper (now memo'd at `docs/alm_2006_methodology_comparison.md`) revealed three load-bearing claims about Alm 2006 that this project had been getting *wrong*:

  **1. Alm 2006 does NOT use producer/consumer or four-quadrant categories.** Their actual finding is a correlation: r = 0.74 (p < 10⁻¹⁵, OLS) between HPK fraction in a genome and recent-LSE fraction; plus a threshold classification ("HPK-enriched" = ≥ 1.5 % of genes). The "Open Innovator / Broker / Sink / Closed" four-quadrant framework is *this project's construction*, not "Alm 2006's generalization". The central research question's framing — "is the producer/consumer asymmetry observed by Alm-Huang-Arkin 2006 a general feature of regulatory function classes?" — overstates the relationship to Alm 2006.

  **2. Alm 2006 worked at the SAME granularity as our UniRef50 detection, not at family level.** They detected HPKs by InterPro IPR005467 / COG4582 — single domain. Their methodology produced clean signal at this granularity. The M3 substrate-hierarchy claim ("UniRef50 is too narrow because Alm 2006 worked at family level") was a *misreading*. Alm 2006's substrate is comparable to ours; the question of why we don't reproduce their signal is a *metric* question, not a substrate question.

  **3. Alm 2006 was tree-aware; our methodology is not.** They used ML phylogenetic trees and reconciliation to assign LSE vs HGT events per gene, then validated with upstream-domain conservation. Our parent-rank dispersion is a permutation-null proxy that doesn't measure the same thing. **Diagnostic C (phyletic incongruence on the GTDB tree topology) is now strongly indicated as the right metric, not deferred. Sankoff parsimony on the GTDB-r214 newick is the lightweight equivalent of Alm 2006's reconciliation at GTDB scale.**

  **Corrections this triggers** (captured in plan v2.5 as M13–M15):
  - **M13** Reframe project's relationship to Alm 2006: Alm-2006-*inspired*, not Alm-2006-*generalizing*. The four-quadrant framework gets explicit ownership as our construction.
  - **M14** Replace M3 substrate-hierarchy claim. Phase 1B's failure to detect HGT-style signal at UniRef50 is a *metric* failure (parent-rank dispersion ≠ tree-aware reconciliation), not a substrate-aggregation failure. Phase 2 KO atlas may still be useful but is not *required* by the substrate-hierarchy logic. The required move is the tree-aware metric.
  - **M15** Diagnostic C (Sankoff parsimony on GTDB tree) promoted from optional sensitivity to **mandatory** before Phase 2 KO atlas implementation. Phase 1B post-gate diagnostics (NB08c) include Sankoff parsimony on the Phase 1B substrate to test whether the order-rank anomaly disappears under tree-aware metric.

  **Generalisable lesson for BERIL projects**: anchor papers cited as foundational (Alm 2006 in our case) should be close-read for *exact* methodology before building infrastructure on top of them. We've now had three pre-registration omissions in this project (M2 dosage-constraint biology, M12 absolute-zero criterion, and M14 misreading-of-Alm-2006). The pattern is clear: *check what the anchor paper actually claims and how, before extrapolating it*. The memo at `docs/alm_2006_methodology_comparison.md` is the project-level deliverable for future BERIL projects building on Alm 2006.

- **2026-04-27 (v2.3 — Phase 1B complete + post-gate diagnostic correction)**: Phase 1B → Phase 2 gate verdict `PASS_REFRAMED`. Pre-registered Bacteroidota PUL Innovator-Exchange hypothesis falsified at absolute-zero criterion across all 4 deep ranks. Then a critical post-gate correction: a user-triggered concern (*"I am also anxious we may not be confronting a methodological error"*) prompted a Mann-Whitney U diagnostic (NB08b) that reframed the Phase 1B finding from over-pessimistic to nuanced. The methodology IS detecting HGT signal at UniRef50 — CAZymes, β-lactamases, class-I CRISPR-Cas all +0.6 to +1.2 σ less clumped than housekeeping at family rank, with p << 10⁻⁷. The pre-registered absolute-zero criterion was over-stringent; a relative threshold (HGT-class vs housekeeping baseline) reveals the graded signal that the absolute threshold misses.

  This is the second pre-registration omission of the project (after M2 in Phase 1A): the "Innovator-Exchange" criterion specified an absolute consumer-z threshold without anchoring to the empirical baseline at the relevant substrate. M12 corrects this for Phase 2 by promoting the relative-threshold metric to primary atlas-level statistic.

  **Lesson generalisable to other BERIL projects**: atlas-level criteria (or any cross-substrate criterion) should be calibrated against an empirical baseline (negative controls / housekeeping classes) rather than absolute zero, especially at substrate resolutions where the null distribution is itself shifted away from zero. The pattern *adversarial-style self-doubt → diagnostic check → reframed finding* is the right discipline for atlas-style projects with weak priors.

  Order-rank anomaly flagged for Phase 2 investigation: positive HGT controls *more* clumped than housekeeping at family→order parent (median Δ = −0.83 σ). Possibly small parent-class count or intra-phylum clustering; not a methodology failure per se but a calibration question Phase 2 KO atlas must address.

  Phase 1B NB04b-equivalent (NB08b) created to keep the diagnostic computation in the audit trail, following BERIL convention.

- **2026-04-26 (v2.2 — Phase 1A staging alignment + post-review synthesis)**: Two related sub-revisions in this round.

  **Sub-revision a — Phase 1A staging alignment** (after Phase 1A NB01–04 complete, gate verdict `PASS_WITH_REVISION`): RESEARCH_PLAN.md v2.2 captures the four methodology revisions (M1: rank-stratified parent ranks; M2: revised negative-control criterion; M3: Alm 2006 reproduction confirmed deferred; M4: paralog fallback acceptable) baked into Phase 1B. README.md status updates to "Phase 1A complete." REPORT.md v1.0 written as a Phase 1A milestone — *not* the full project synthesis (Phases 1B–4 still in planning). references.md created.

  **Sub-revision b — Post-review synthesis** (after `REVIEW_1.md` + `ADVERSARIAL_REVIEW_1.md` landed): synthesized two reviews that diverged sharply on the project's quality. Standard claude reviewer was uniformly positive ("exceptionally well-designed"; 0 critical, 0 important, 6 forward-looking suggestions). Adversarial reviewer flagged 3 critical + 4 important gaps. The divergence is the canonical pattern documented in this BERIL install's memory: "standard reviewer is over-optimistic on structural issues; adversarial catches what standard misses."

  **What the adversarial review caught that the standard missed**:
  - **C2: Consumer null lacks a positive control.** The producer null is validated by `natural_expansion`. The consumer null has no equivalent. AMR was meant to be it but parent-phylum anchor masks intra-phylum HGT. *Real gap; addressed by Phase 1B HIGH 1: known-cross-phylum-HGT positive control set (β-lactamase families with documented cross-phylum spread + class-I CRISPR-Cas).*
  - **C3: Effect sizes on biologically meaningful scales absent.** Z-scores reported; raw paralog count differences not. *Real gap; addressed by retroactively adding raw paralog count effect sizes to REPORT.md v1.1 (NB04b reproducibly computes them: natural_expansion at phylum is +39.5% above cohort; negative controls 11–16% below cohort; TCS HK 18% below — opposite direction from Alm 2006).*
  - **I1: Pseudoreplication / phylogenetic correlation.** Species within clades not independent. *Real gap; addressed by Phase 1B HIGH 3: PIC mandatory at Phase 1B (was Phase 2 optional sensitivity).*
  - **I2: Power analysis for the Alm 2006 negative result.** Adversarial asked if "deferred to Phases 2/3" hides underpowering. *Computed in NB04b: at pilot scale, 81–99% power to detect medium effect (d=0.3) at all ranks except genus. Observed mean z is negative across all ranks. Conclusion: the substrate-hierarchy claim holds; not underpowering. Caveat: small Alm 2006 effect at UniRef50 (d ≤ 0.1) could still be missed at genus rank.*
  - **I3: Post-hoc revision of negative-control criterion (M2).** Pre-registration discipline concern. *Honest fix in REPORT.md v1.1: the M2 revision corrects a pre-registration omission, not redefines a target. The biological prior (dosage constraint → fewer paralogs) was correctly anticipated during plan v2 design but its quantitative consequence (negative producer z, not zero) was not encoded. Phase 1B pre-registers the corrected expectation.*

  **Adversarial critiques not adopted as written** (with reasoning logged in REPORT.md "Pushbacks"):
  - **C1 framing as "rendering meaningful discoveries impossible"** — overcalled. The hierarchical Tier-1 / Tier-2 / Tier-3 multiple-testing strategy is in plan v2.1; the reviewer didn't fully credit it. Implementation details (BH-FDR variant, effective-N for clusters) are TBD; that's a real Phase 1B gap captured as MEDIUM 6.
  - **I4 "Substrate switching invalidates v1"** — overcalled. v1 was iterated, not shipped. v2 IS the milestone result. No v1 results were used in scientific claims.
  - **H2 "Central project hypothesis unsupported"** — same as the earlier plan-adversarial review. DESIGN_NOTES v1's weak-prior framing addresses this; the framework is *testing* the regulatory-vs-metabolic asymmetry empirically, not assuming it. Reviewer conflates the project's null hypothesis with its starting hypothesis.

  **Lessons captured for future BERIL projects**:
  - *Run both standard AND adversarial review at each milestone* — they catch different things. Standard reviewer's over-optimism on structural issues is a documented BERIL pattern (memory note `feedback_review_pairing.md`); paired adversarial is the right counterweight.
  - *Out-of-band quantitative analyses must be wrapped in a notebook for the audit trail* — addressed in this round by creating NB04b (the BERIL convention for in-phase appendix iterations, precedent: `ibd_phage_targeting`'s NB04b–h rescue cycle).
  - *Pre-registration discipline requires biologically grounded criteria* — the M2 revision is a lesson: a pre-registered "near zero" criterion was wrong because the biological prior (dosage constraint) was not encoded into the criterion. Future phases pre-register criteria with explicit biological rationale.

  **Phase 1B HIGH commitments from this synthesis**:
  - **HIGH 1**: known-HGT positive control set for consumer null (β-lactamase families + class-I CRISPR-Cas)
  - **HIGH 2**: raw paralog count effect sizes alongside z-scores in all atlas tables
  - **HIGH 3**: PIC (phylogenetic independent contrasts) mandatory
  - **HIGH 4**: Alm 2006 power-analysis scope verified empirically; substrate-hierarchy claim defensible
  - **HIGH 5**: M2 sharpening — pre-register corrected expectation, not original

  **Phase 1B MEDIUM (deferred to Phase 1B plan documents)**:
  - **MEDIUM 6**: hierarchical multiple-testing implementation details (BH-FDR variant, effective-N within KEGG BRITE × GTDB family)
  - **MEDIUM 7**: compute-resource specification per phase
  - **MEDIUM 8**: Phase 2 mid-pilot KO-level validation step (pre-Phase-3 architectural deep-dive insurance)
  - **MEDIUM 9**: uncertainty propagation strategy for Phase 4 cross-resolution synthesis, documented in advance
  - **MEDIUM 10**: Sichert & Cordero (2021) added to references.md for Phase 1B Bacteroidota PUL literature context

- **2026-04-26 (v2.1)**: Substrate-audit revision triggered by user question after 8 NB01 debug iterations. The user asked: *"are we sure we are getting all we can out of the KBase tenant and pangenome and kescience_iterpro?"* This was a load-bearing question because the iterations had been a mix of bug-fixes and structural fragility (Pfam-name string-matching for control detection had only caught 38K UniRef50 TCS HKs from the eggNOG `PFAMs` field, with no way to know what fraction was missed). Audit found we were using ~40 % of relevant `kbase_ke_pangenome` tables and 0 % of `kescience_*`. The most consequential miss was **`interproscan_domains`** (833 M rows; 146 M Pfam hits; 83.8 % cluster coverage) — the authoritative Pfam annotation source on BERDL. NB01 v2 control detection now uses InterProScan as primary (accession-based, reliable) with eggNOG `PFAMs` as cross-validation. Two new InterProScan tables (`interproscan_go`, `interproscan_pathways`) added as Phase 2 cross-validation substrate. Other under-used databases (`kescience_fitnessbrowser`, `kescience_alphafold`, `kescience_webofmicrobes`, `kescience_bacdive`, `genomad_mobile_elements` if ingested) are documented in the plan but deferred to specific later phases with explicit roadmap entries. **The audit demonstrated that NB01 fragility was structural (wrong substrate) not just operational (bugs); future phases should audit substrate before implementing rather than after debugging.**

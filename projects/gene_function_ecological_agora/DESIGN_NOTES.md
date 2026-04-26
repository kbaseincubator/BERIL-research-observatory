# Design Notes: Gene Function Ecological Agora

This document captures the *reasoning behind* the research plan — the critique of the original brief, the through-line logical argument, the rejected alternatives, and the explicit acknowledgement that the pre-registered hypotheses are weak priors. It is written for future readers (human or agent) who need to understand *why* the plan is shaped this way.

`RESEARCH_PLAN.md` is the operational plan. This document is the design record. Read both.

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

## Authors

- **Adam Arkin**
  - ORCID: 0000-0002-4999-2931
  - Affiliation: U.C. Berkeley / Lawrence Berkeley National Laboratory

## Document History

- **2026-04-26**: Initial design notes captured at project creation. Reflects the conversation reasoning leading to the three-phase plan, the weak-prior framing of pre-registered hypotheses, and the rejection of alternative atlas framings.

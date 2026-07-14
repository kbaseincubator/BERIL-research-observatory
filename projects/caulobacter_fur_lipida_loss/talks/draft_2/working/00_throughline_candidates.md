# Throughline candidates — `caulobacter_fur_lipida_loss` (talk-30)

**Generated:** 2026-06-08
**Mode:** talk-30 (peer audience) · **Tier:** STRONG (inherited from plan)
**Paper-writer reconciliation:** `papers/draft_2/00_throughline.md` selected the
integrative mechanism-atlas arc. Reuse was NOT set to `auto-from-paper`, so all
three seeded arcs are surfaced for the user; the paper's chosen arc is carried
here as **TL2** (architecture/atlas) so the user can keep the talk aligned with
the paper or deliberately diverge. Not picking — presenting.

Every candidate's evidence map covers all 27 critical analyses (A1–A27) from the
plan inventory; only the *framing* (and therefore the strength glyph) changes
between candidates. Strength glyphs: `✓ direct` · `⚠ partial` · `✗ contradicts`
(→ goes in a limitations slide) · `◇ orthogonal` (context, doesn't bear on the
claim either way).

---

## Candidate TL1: Δ*fur* derepression is the demonstrable driver of the lipid A-loss-permissive envelope state, and everything downstream is the supporting (and still-open) mechanism it sets in motion.

**Evidence map:**

| Sub-claim | Source | Strength |
|---|---|---|
| A1 — Δ*fur* derepression is a major driver (Spearman ρ=0.315, p=2.08e-03, 71% sign concordance over 93 Leaden DEGs) | REPORT §"Finding 1"; nb 01_leaden2018_fur_signature.ipynb cell 5 | ✓ direct |
| A2 — signal is constitutive Δ*fur* derepression, not an iron-limitation response | REPORT §"Finding 1"; nb 01 cell 7 | ⚠ partial — single growth condition (PYE rich) |
| A3 — cbb3/*fix* respiratory operon is the Fur-released listing buffered by Δ*sspB* | REPORT §"Finding 1"; nb 01 cell 9 | ◇ orthogonal — concerns the SspB arm, not the Fur-driver claim |
| A4 — Path A (32 Fur-released genes) enriched for envelope-stress fitness (17/32=53.1%, fold 1.60×, p=0.016) | REPORT §"Finding 2"; nb 02b_h2_hypergeometric_verdict.ipynb cell 2 | ⚠ partial — marginal enrichment above 33.25% background |
| A5 — genome-background calibration (K=1311/N=3943=33.25%) underpinning the test | REPORT §"Finding 2"; nb 02b cell 1 | ✓ direct |
| A6 — ≥10% threshold miscalibration lesson | REPORT §Results scorecard; RESEARCH_PLAN §thresholds | ◇ orthogonal — methodological, not biology |
| A7 — SspB-buffered respiratory arm (Path B) is mechanistically critical | REPORT §"Finding 2"; nb 02b cell 2 | ✗ contradicts — 9/26=34.6%, fold 1.04×, p=0.515 (background); narrows the driver to Fur alone |
| A8 — ChvI two-phase partition (20 early / 10 both / 49 late) | REPORT §"Finding 3"; nb 03_chvi_phase_partition_sigU.ipynb cell 7 | ⚠ partial — downstream consequence of the Fur-set envelope state |
| A9 — ChvI autoregulation (CCNA_00237 +1.45) | REPORT §"Finding 3"; nb 03 cell 7 | ◇ orthogonal — downstream regulatory detail |
| A10 — SigU drives the late ChvI cohort | REPORT §"Finding 3"; nb 03 cell 10 | ✗ contradicts — 24.5% coherence, Fisher p=0.243 |
| A11 — ChvR sRNA post-transcriptional confound | ADVERSARIAL_REVIEW_2 N3 | ◇ orthogonal — confound to acknowledge |
| A12 — sphingolipid biosynthesis constitutive, not induced | REPORT §"Finding 4"; nb 04_sphingolipid_lpt_panel.ipynb cell 4 | ◇ orthogonal — context for the rescued state, not the Fur-driver claim |
| A13 — CtpA as LpxF-equivalent processing step | REPORT §"Finding 4"; nb 04 cell 5 | ✗ contradicts — REJECTED at pre-registered bar |
| A14 — Lpt apparatus repurposed for sphingolipid transport | REPORT §"Finding 4"; nb 04 cells 4 & 6 | ⚠ partial — transcript-protein discordance |
| A15 — OM proteome direction-only (single replicate) | REPORT §"Finding 4"; nb 04 cell 6 | ⚠ partial |
| A16 — *lptC2* single-replicate protein increase | REPORT §"Finding 4"; nb 04 cell 6 | ◇ orthogonal — pilot, appendix |
| A17 — *sphk* present in *A. baumannii* (scope note) | ADVERSARIAL_REVIEW_2 N1 | ◇ orthogonal |
| A18 — PG specific lytic engagement (SdpA +4.8; Pal +2.08/+2.84) | REPORT §"Finding 5"; nb 05_pg_remodeling.ipynb cell 5 | ◇ orthogonal — downstream envelope response |
| A19 — PG broad basal shutdown (28 loci, 20 DOWN) | REPORT §"Finding 5"; nb 05 cell 5 | ◇ orthogonal |
| A20 — PG protein-level statistics caveat | REPORT §"Finding 5"; nb 05 cell 6 | ⚠ partial |
| A21 — sphingolipid pathway *Caulobacter*-unique | REPORT §"Finding 6"; nb 06b_ncbi_annotation_presence.ipynb cell 5 | ◇ orthogonal — explains scope, not the driver |
| A22 — ChvG-ChvI *Caulobacter*-restricted | REPORT §"Finding 6"; nb 06b cell 5 | ◇ orthogonal |
| A23 — NCBI annotation-presence method scope | REPORT §"Finding 6"; nb 06b cell 3 | ⚠ partial |
| A24 — strain 4580/4584/4599 design contrast | REPORT §Methods; RESEARCH_PLAN §design | ✓ direct — the contrast that isolates the Fur signal |
| A25 — Zik 2022 baseline-mechanism anchoring (Δ*fur* required for rescue) | REPORT §Interpretation; RESEARCH_PLAN §background | ✓ direct — establishes Fur as the precondition this arc characterizes |
| A26 — mechanistic synthesis integration (9-point graded) | REPORT §Interpretation §1–9 | ⚠ partial — only the Fur-layer components are `direct` |
| A27 — pre-registered hypothesis scorecard | REPORT §Results; RESEARCH_PLAN §hypotheses | ✓ direct — discipline that grades the driver claim |

**Slide-count estimate:**

- talk-30: 26 slides
- talk-15: 14
- talk-45: 38
- lightning-5: 6

**Visual coherence cost:**

- Existing figures supporting this arc: 3 (NB01_fur_signature_scatter.png, NB01_leaden_iron_vs_fur.png, NB07_synthesis_master.png 4-panel)
- Procedural diagrams the slide-compose prompt will need to add: 3 (strain-design contrast schematic 4580→4584→4599; Δ*fur* derepression → envelope-state cartoon; Path A vs Path B triage funnel)
- AI-image-gen suggestions (Tier 3, opt-in): 0 (AI image-gen is off per plan; no suggestions emitted)

**What this talk would NOT cover if this is chosen:**

- The peptidoglycan-remodeling enzyme catalog (A18/A19) — compressed to a single "downstream consequence" slide; the SdpA/Pal-Tol detail and the Tan & Chng 2025 retrograde-PL reinterpretation are dropped.
- The cross-species restriction atlas (A21/A22) — named as scope, not narrated; the four-species comparison and the PaperBLAST-vs-NCBI method story (A23) are out of scope.
- The methodological threshold-miscalibration lesson (A6) — orthogonal to the driver claim; → appendix at most.
- *Contradicts → limitations slide:* the SspB respiratory arm (A7), CtpA processing (A13), and SigU-as-driver (A10) all appear only as honest "not supported" caveats, not as part of the spine.

**Substory clusters preview** (substory_design will refine):

- S1: "Δ*fur* is the driver" — Leaden concordance + the isolating strain contrast (A1, A2, A24, A25)
- S2: "Which Fur targets matter" — Path A enrichment over a calibrated background, Path B falls out (A4, A5, A7)
- S3: "What the driver sets in motion" — ChvI / sphingolipid / PG as compressed downstream consequences (A8, A12, A18)

**Tier-evidence:** `STRONG`

---

## Candidate TL2: A coordinated multi-layer envelope-remodeling program enables Δ*fur*-permitted lipid A loss — Fur-derepressed transport, ChvI two-phase engagement, constitutive sphingolipid substitution, peptidoglycan reorganization, and species-restricted machinery — each layer narrated at its true evidence grade, demotions included.

_(This is REPORT.md's own integrative framing and the arc the paper-writer selected for `papers/draft_2`. Choosing TL2 keeps the talk aligned with the manuscript.)_

**Evidence map:**

| Sub-claim | Source | Strength |
|---|---|---|
| A1 — Layer 1: Δ*fur* derepression drives the signal (ρ=0.315, p=2.08e-03, 71% concordance) | REPORT §"Finding 1"; nb 01 cell 5 | ✓ direct |
| A2 — Layer 1 scope: constitutive derepression, not iron-limitation | REPORT §"Finding 1"; nb 01 cell 7 | ⚠ partial — single condition |
| A3 — Layer 1: cbb3/*fix* operon buffered by Δ*sspB* (transcript-level) | REPORT §"Finding 1"; nb 01 cell 9 | ✓ direct — clean transcriptomic observation |
| A4 — Layer 1: Path A envelope-stress enrichment (17/32=53.1%, fold 1.60×, p=0.016) | REPORT §"Finding 2"; nb 02b cell 2 | ⚠ partial — marginal |
| A5 — genome-background calibration (33.25%) | REPORT §"Finding 2"; nb 02b cell 1 | ✓ direct |
| A6 — ≥10% threshold miscalibration lesson | REPORT §Results scorecard; RESEARCH_PLAN §thresholds | ◇ orthogonal — methodological aside |
| A7 — Layer 1 demotion: SspB respiratory arm NOT enriched | REPORT §"Finding 2"; nb 02b cell 2 | ✗ contradicts — narrated as an honest demotion of the "dual-release switch" |
| A8 — Layer 2: ChvI two-phase partition (20/10/49) | REPORT §"Finding 3"; nb 03 cell 7 | ✓ direct |
| A9 — Layer 2: ChvI autoregulation (+1.45) | REPORT §"Finding 3"; nb 03 cell 7 | ✓ direct |
| A10 — Layer 2 demotion: SigU drives late cohort | REPORT §"Finding 3"; nb 03 cell 10 | ✗ contradicts — 24.5%, Fisher p=0.243 |
| A11 — ChvR sRNA confound | ADVERSARIAL_REVIEW_2 N3 | ◇ orthogonal — acknowledged confound |
| A12 — Layer 3: sphingolipid biosynthesis constitutive, not induced | REPORT §"Finding 4"; nb 04 cell 4 | ✓ direct |
| A13 — Layer 3 demotion: CtpA LpxF-equivalent step | REPORT §"Finding 4"; nb 04 cell 5 | ✗ contradicts — REJECTED at pre-registered bar |
| A14 — Layer 3: Lpt apparatus repurposed (transcript up, protein discordant) | REPORT §"Finding 4"; nb 04 cells 4 & 6 | ⚠ partial — MIXED grade |
| A15 — Layer 3: OM proteome direction-only | REPORT §"Finding 4"; nb 04 cell 6 | ⚠ partial |
| A16 — Layer 3 pilot: *lptC2* protein increase | REPORT §"Finding 4"; nb 04 cell 6 | ◇ orthogonal — PILOT, appendix |
| A17 — *sphk* scope note (A. baumannii) | ADVERSARIAL_REVIEW_2 N1 | ◇ orthogonal |
| A18 — Layer 4: PG specific lytic engagement (SdpA +4.8; Pal +2.08/+2.84) | REPORT §"Finding 5"; nb 05 cell 5 | ✓ direct |
| A19 — Layer 4: PG broad basal shutdown (28 loci, 20 DOWN) | REPORT §"Finding 5"; nb 05 cell 5 | ✓ direct |
| A20 — Layer 4: PG protein-stat caveat | REPORT §"Finding 5"; nb 05 cell 6 | ⚠ partial |
| A21 — Layer 5: sphingolipid pathway *Caulobacter*-unique | REPORT §"Finding 6"; nb 06b cell 5 | ✓ direct |
| A22 — Layer 5: ChvG-ChvI *Caulobacter*-restricted | REPORT §"Finding 6"; nb 06b cell 5 | ✓ direct |
| A23 — Layer 5: NCBI annotation-presence scope | REPORT §"Finding 6"; nb 06b cell 3 | ⚠ partial |
| A24 — strain 4580/4584/4599 design contrast | REPORT §Methods; RESEARCH_PLAN §design | ✓ direct |
| A25 — Zik 2022 baseline anchoring | REPORT §Interpretation; RESEARCH_PLAN §background | ✓ direct |
| A26 — mechanistic synthesis integration (the atlas itself) | REPORT §Interpretation §1–9 | ⚠ partial — narrative over heterogeneous evidence |
| A27 — pre-registered hypothesis scorecard | REPORT §Results; RESEARCH_PLAN §hypotheses | ✓ direct |

**Slide-count estimate:**

- talk-30: 30 slides (near the 32 ceiling — see budget flag below)
- talk-15: 17 (at the ceiling; atlas compresses poorly — see flag)
- talk-45: 44
- lightning-5: 7

**Visual coherence cost:**

- Existing figures supporting this arc: 7 (NB07_synthesis_master.png, NB01_fur_signature_scatter.png, NB04_sphingolipid_locus_heatmap.png, NB04_lpt_apparatus_heatmap.png, NB05_pg_remodeling_heatmap.png, NB06_comparative_heatmap.png, 00_sphingolipid_locus_heatmap.png) — this arc is the best-served by existing figures
- Procedural diagrams the slide-compose prompt will need to add: 2 (five-layer envelope schematic threading all layers; evidence-grade legend so each layer's SUPPORTED/HYPOTHESIS/MIXED/PILOT badge is consistent across slides)
- AI-image-gen suggestions (Tier 3, opt-in): 0 (AI image-gen off per plan)

**What this talk would NOT cover if this is chosen:**

- The threshold-miscalibration methodological lesson (A6) — folded to an aside; not a layer.
- The cross-species engineering / Tol-Pal retrograde-transport future predictions — Future Directions only.
- The Leaden iron-vs-Δ*fur* internal validation (NB01_leaden_iron_vs_fur figure) and gene-by-gene cbb3/*fix* listing — appendix.
- CCNA_01217 single-replicate protein increase — appendix with the *lptC2* pilot.
- **Mode-budget flag:** at 30 (talk-30) and 17 (talk-15) this arc is at the upper bound. To fit talk-30 safely, hold each of the 5 layers to ≤3 content slides, or fold Layer 5 (species restriction, A21/A22) into the cross-tenant integration slide. To fit talk-15 this arc would have to drop Layer 4 (PG, A18/A19) or Layer 5 to one summary slide.
- *Contradicts → handled in-line at grade:* A7, A10, A13 are narrated as the demotions that make the atlas honest, not hidden.

**Substory clusters preview** (substory_design will refine):

- S1: "Fur opens the gate" — derepression + transport triage (A1, A3, A4, A7)
- S2: "The envelope responds" — ChvI two-phase + PG reorganization (A8, A9, A18, A19)
- S3: "Substitution, not induction" — constitutive sphingolipid + Lpt repurposing (A12, A14)
- S4: "Why only *Caulobacter*" — species-restricted machinery (A21, A22)

**Tier-evidence:** `STRONG`

---

## Candidate TL3: A pre-registered scorecard plus a genome-background calibration is what converts an enthusiastic rescue-mechanism hypothesis into an honestly-graded result — the ≥10%-threshold miscalibration and the Path B / CtpA / SigU demotions are the worked illustration.

**Evidence map:**

| Sub-claim | Source | Strength |
|---|---|---|
| A1 — clean direct positive (Leaden concordance) illustrates a SUPPORTED grade | REPORT §"Finding 1"; nb 01 cell 5 | ◇ orthogonal — vehicle, a result the discipline grades |
| A2 — scope-limiting reasoning (constitutive, not iron) | REPORT §"Finding 1"; nb 01 cell 7 | ⚠ partial — illustrates honest scoping |
| A3 — cbb3/*fix* buffering observation | REPORT §"Finding 1"; nb 01 cell 9 | ◇ orthogonal |
| A4 — Path A SURVIVES recalibration (fold 1.60×, p=0.016) | REPORT §"Finding 2"; nb 02b cell 2 | ✓ direct — central: what passes a *calibrated* test |
| A5 — genome-background calibration (33.25%) | REPORT §"Finding 2"; nb 02b cell 1 | ✓ direct — the calibration is the method |
| A6 — ≥10% threshold miscalibration lesson (10% < 33.25% background) | REPORT §Results scorecard; RESEARCH_PLAN §thresholds | ✓ direct — the headline methodological lesson |
| A7 — Path B DEMOTED on recalibration (1.04×, p=0.515) | REPORT §"Finding 2"; nb 02b cell 2 | ✓ direct — central worked demotion |
| A8 — ChvI two-phase partition passes its pre-registered ≥10-gene bar | REPORT §"Finding 3"; nb 03 cell 7 | ◇ orthogonal — illustration of a PASS |
| A9 — ChvI autoregulation detail | REPORT §"Finding 3"; nb 03 cell 7 | ◇ orthogonal |
| A10 — SigU-as-driver REFRAMED then fails relaxed bar | REPORT §"Finding 3"; nb 03 cell 10 | ✓ direct — central worked demotion |
| A11 — ChvR sRNA confound acknowledged | ADVERSARIAL_REVIEW_2 N3 | ⚠ partial — illustrates confound-honesty |
| A12 — sphingolipid constitutive (a clean PASS) | REPORT §"Finding 4"; nb 04 cell 4 | ◇ orthogonal — illustration |
| A13 — CtpA REJECTED at pre-registered bar (pvalue 0.048, FDR 0.109, protein n.d.) | REPORT §"Finding 4"; nb 04 cell 5 | ✓ direct — central worked rejection |
| A14 — Lpt transcript-protein discordance → MIXED grade | REPORT §"Finding 4"; nb 04 cells 4 & 6 | ⚠ partial — illustrates MIXED grading |
| A15 — single-replicate OM proteome → direction-only | REPORT §"Finding 4"; nb 04 cell 6 | ⚠ partial — illustrates evidence-grade honesty |
| A16 — *lptC2* labeled PILOT, not claimed | REPORT §"Finding 4"; nb 04 cell 6 | ⚠ partial — illustrates PILOT labeling |
| A17 — *sphk* scope-tempering (NCBI 287 outside *Caulobacter*) | ADVERSARIAL_REVIEW_2 N1 | ⚠ partial — illustrates scope-tempering |
| A18 — PG specific lytic engagement (PASS) | REPORT §"Finding 5"; nb 05 cell 5 | ◇ orthogonal — illustration |
| A19 — PG broad shutdown | REPORT §"Finding 5"; nb 05 cell 5 | ◇ orthogonal |
| A20 — PG protein-stat caveat (direction-only) | REPORT §"Finding 5"; nb 05 cell 6 | ⚠ partial — illustrates the caveat discipline |
| A21 — sphingolipid uniqueness (a confirmed claim) | REPORT §"Finding 6"; nb 06b cell 5 | ◇ orthogonal |
| A22 — ChvG-ChvI uniqueness (confirmed) | REPORT §"Finding 6"; nb 06b cell 5 | ◇ orthogonal |
| A23 — PaperBLAST ~80% false-negative diagnosis + NCBI re-test (NB06b) | REPORT §"Finding 6"; nb 06b cell 3 | ✓ direct — central method-rigor illustration |
| A24 — strain 4580/4584/4599 contrast isolates the Δ*lpxc* effect | REPORT §Methods; RESEARCH_PLAN §design | ✓ direct — the pre-registered isolation logic |
| A25 — Zik 2022 baseline (the hypothesis being graded) | REPORT §Interpretation; RESEARCH_PLAN §background | ◇ orthogonal — literature baseline |
| A26 — evidence-graded synthesis (SUPPORTED/HYPOTHESIS/PARTIAL/MIXED/PILOT) | REPORT §Interpretation §1–9 | ⚠ partial — the graded narrative is the method's output |
| A27 — pre-registered hypothesis scorecard (18 rows, H1–H4) | REPORT §Results; RESEARCH_PLAN §hypotheses | ✓ direct — THE central artifact of this arc |

**Slide-count estimate:**

- talk-30: 26 slides
- talk-15: 14
- talk-45: 36
- lightning-5: 6

**Visual coherence cost:**

- Existing figures supporting this arc: 2 (NB07_synthesis_master.png used as the scorecard panel; NB02b hypergeometric verdict is tabular — rendered from data/NB02b_h2_hypergeometric_verdict.csv)
- Procedural diagrams the slide-compose prompt will need to add: 4 (the pre-registration → test → verdict pipeline diagram; a "≥10% vs 33.25% background" calibration bar chart; a before/after demotion table for Path B / CtpA / SigU; the PaperBLAST-vs-NCBI false-negative comparison)
- AI-image-gen suggestions (Tier 3, opt-in): 0 (AI image-gen off per plan)

**What this talk would NOT cover if this is chosen:**

- Most of the biological mechanism detail (sphingolipid biochemistry A12, Lpt shared-component model A14, PG enzymology A18/A19, species restriction A21/A22) becomes *illustration*, not subject — a peer audience expecting the Caulobacter biology as the headline will get the method instead.
- The Uchendu 2026 shared-component nuance and the Tan & Chng 2025 Pal reinterpretation — dropped to keep the focus on inference discipline.
- Future-directions biology (lipidomics, cross-species engineering, iron-axis fitness) — out of scope.
- *Contradicts → these ARE the worked examples:* A7, A10, A13 are the centerpiece of the talk, not limitations to bury.

**Substory clusters preview** (substory_design will refine):

- S1: "Pre-registration before data" — the scorecard + strain contrast set the bars (A27, A24, A6)
- S2: "Calibrate against background" — the 33.25% rate; Path A survives, Path B demoted (A5, A4, A7)
- S3: "Demotions as the product" — CtpA rejected, SigU reframed, PaperBLAST re-tested (A13, A10, A23)

**Tier-evidence:** `STRONG`

---

## Diversity note (for the user)

These are three genuinely different talks, not three wordings of one:

- **TL1** is a *single-driver* story — Fur derepression is the protagonist, the other four layers are supporting cast. Cleanest spine, smallest figure footprint, leaves the most on the cutting-room floor.
- **TL2** is the *whole-system atlas* — all five layers at their honest grade. Richest use of existing figures, matches the paper, but is the tightest fit for talk-30/15 and bundles the demotions into a "coordinated program" claim a sharp reviewer can poke.
- **TL3** is a *methods-as-finding* story — the inference discipline (calibration + scorecard) is the take-home; the biology is the worked example. Most transferable lesson, but a Caulobacter-biology audience may want more mechanism.

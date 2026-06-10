# Substory clusters — `caulobacter_fur_lipida_loss` / talk mode `talk-30`

**Throughline:** Δ*fur* derepression is the demonstrable driver of the lipid A-loss-permissive envelope state, and everything downstream is the supporting (and still-open) mechanism it sets in motion.
**Tier:** STRONG
**Mode budget:** 20-32 slides per SPEC §5

## Mode-capacity check

- **Boilerplate slides:** 9 (title + 5 dividers [1 per substory] + cross_tenant_integration + acknowledgments + references; qa_anticipated not requested)
- **Per-substory content target:** 3 (talk-30)
- **Required slides (uniform target):** 9 + (3 × 5) = 24
- **Required slides (cluster-shaped):** 26 (S4 carries 8 analyses → 5 content slides; all others 3) — matches the throughline's 26-slide estimate
- **Mode max:** 32

**Capacity verdict:** `fits`

The cluster-shaped requirement (26) sits 6 slides under the 32-slide max, with both the uniform (24) and shaped (26) accountings clearing the budget. No overflow; the asymmetry (S4 large, see its rationale) is intentional and budget-affordable, so no drop/escalate/merge is forced.

## Substory clusters

### S1 — Δ*fur* is the driver

**Punchline:** Δ*fur* derepression, not iron limitation, drives the lipid A-loss-permissive envelope state.

**Critical analyses covered:**

- A1: Leaden 2018 Δ*fur* signature concordance (ρ=0.315, p=2.08e-03, 71% sign concordance over 93 DEGs) — REPORT §"Finding 1" / nb 01_leaden2018_fur_signature.ipynb cell 5 — `direct`
- A2: Leaden iron-limitation vs Δ*fur* internal discrimination — REPORT §"Finding 1" / nb 01 cell 7 — `partial` (single PYE-rich growth condition)
- A3: cbb3/*fix* respiratory operon Fur-release listing — REPORT §"Finding 1" / nb 01 cell 9 — `direct`
- A24: strain 4580/4584/4599 design contrast (lipid A-replete vs -deficient) — REPORT §Methods / RESEARCH_PLAN §design — `direct`
- A25: Zik 2022 (PMID 35649364) baseline-mechanism anchoring (Δ*fur* required for rescue) — REPORT §Interpretation / RESEARCH_PLAN §background — `direct`

**Cluster rationale:** This is the load-bearing spine of TL1. A1 (the reproduced Leaden concordance) is the demonstrable driver claim; A2 is the discrimination that rules out the obvious alternative (iron limitation), making the signal *constitutive* Δ*fur* derepression rather than an iron-limitation response; A24 is the experimental contrast that isolates the Fur signal in the first place; A25 anchors Fur as the precondition the whole arc characterizes (Zik shows Δ*fur* is *required* for rescue). A3 is the gene-by-gene Fur-release detail that makes the signature concrete. Confidence shape is clean — four `direct` plus one `partial`, and the lone `partial` (A2) is a scoping caveat (one growth condition) the divider will state plainly rather than hide. **Strain-design contrast (A24) and Zik baseline (A25) lead the talk** because the audience cannot read any downstream slide without first accepting that the comparison isolates a Fur effect.

**Proposed slide budget:** 3 content slides + 1 divider

**Slide kinds anticipated** (slide_compose refines):

- big_idea (substory opener / divider; SPEC §6.2 — non-negotiable)
- workflow_diagram (strain-design contrast schematic 4580→4584→4599; A24)
- data_figure (NB01_fur_signature_scatter.png — Leaden concordance; A1)
- claim_evidence (iron-vs-Δ*fur* discrimination using NB01_leaden_iron_vs_fur.png + Zik anchoring + cbb3/*fix* detail; A2, A25, A3)

---

### S2 — Which Fur targets matter: Path A in, Path B out

**Punchline:** Calibrated against genome background, only the Fur-released Path A enriches for envelope-stress fitness.

**Critical analyses covered:**

- A4: Path A (32-gene Fur-released subset) envelope-stress fitness enrichment (17/32=53.1%, fold 1.60×, p=0.016) — REPORT §"Finding 2" / nb 02b_h2_hypergeometric_verdict.ipynb cell 2 — `partial` (marginal above 33.25% background; independently reproduced by adversarial reviewer)
- A5: genome-background calibration (K=1311/N=3943=33.25%) for the hypergeometric test — REPORT §"Finding 2" / nb 02b cell 1 — `direct`
- A6: pre-registered ≥10% threshold miscalibration lesson — REPORT §Results scorecard / RESEARCH_PLAN §thresholds — `direct` (methodological)
- A7: Path B (SspB-buffered respiratory arm, 26 genes) enrichment test (9/26=34.6%, fold 1.04×, p=0.515) — REPORT §"Finding 2" / nb 02b cell 2 — `preliminary` NEGATIVE (indistinguishable from background)

**Cluster rationale:** This cluster narrows the driver claim from "Fur derepression" to "*which* Fur targets carry the envelope-stress signal." A5 (the genome-background calibration) is the methodological keystone — without it the enrichment is uninterpretable — and A4 is the marginal-but-robustly-reproduced Path A enrichment it underpins. **A7 (the Path B negative) is not a contradiction within the cluster; it IS the second half of the punchline:** the SspB-buffered respiratory arm falls to background (fold 1.04×, p=0.515), which narrows the driver to Fur alone and is honest signal, not a buried caveat. A6 (the ≥10%-threshold miscalibration lesson — 10% sits below the 33.25% background) is the methodological corollary of A5 and rides on the same calibration slide; per the throughline it is otherwise appendix-grade, so it is mentioned, not narrated. **Mixed-confidence note (structural smell, intentional):** this cluster spans `direct` (A5), `partial` (A4), and a `preliminary`/negative (A7). The mix is deliberate — the comparison "Path A enriches, Path B does not" requires both arms at their true grades; collapsing it would either overclaim Path A or hide the Path B demotion.

**Proposed slide budget:** 3 content slides + 1 divider

**Slide kinds anticipated:**

- big_idea (substory opener / divider)
- workflow_diagram (Path A vs Path B triage funnel; A4/A7 partition)
- claim_evidence (Path A hypergeometric enrichment over the calibrated 33.25% background, with A6 threshold lesson as a footnote; A4, A5, A6)
- claim_evidence (Path B negative result — demotion from mechanism to hypothesis; A7)

---

### S3 — The driver triggers a two-phase ChvI response

**Punchline:** The Fur-set envelope state triggers a two-phase ChvI response; its late regulator stays open.

**Critical analyses covered:**

- A8: ChvI envelope-stress two-phase partition (unique-early=20, both-phase=10, late=49) — REPORT §"Finding 3" / nb 03_chvi_phase_partition_sigU.ipynb cell 7 — `partial` (downstream consequence of the Fur-set state)
- A9: ChvI autoregulation (CCNA_00237 +1.45) — REPORT §"Finding 3" / nb 03 cell 7 — `direct`
- A10: SigU drives the late ChvI cohort — REPORT §"Finding 3" / nb 03 cell 10 — `preliminary` NEGATIVE (late-cohort coherence 24.5%, Fisher p=0.243)
- A11: ChvR sRNA alternative post-transcriptional mechanism — ADVERSARIAL_REVIEW_2 N3 (Fröhlich 2018 PMID 30165530) — `preliminary` (review-raised confound)

**Cluster rationale:** This is the first "what the driver sets in motion" layer — the regulatory/signaling response (ChvG-ChvI two-component sensing of the envelope-stress state Fur creates). It is held separate from S4 because ChvI is the *sensor* arm, whereas S4 is the *structural-effector* arm; merging them would force a punchline spanning sensing + remodeling. A8 (the two-phase partition) and A9 (autoregulation) are the descriptive backbone; A10 (SigU-as-late-driver) is a NEGATIVE the punchline names directly ("its late regulator stays open" — coherence 24.5%, p=0.243; note ADVERSARIAL_REVIEW_2 N2 records that SigU *is* characterized [Alvarez-Martinez 2007 PMID 17986185], so the framing is "regulator unidentified," not "no regulator"), and A11 (the ChvR sRNA confound from adversarial review) is the post-transcriptional alternative the talk must acknowledge as the open question. The "still-open" framing is exactly TL1's stance toward downstream mechanism. **Mixed-confidence note:** `direct` (A9) + `partial` (A8) + two `preliminary`/negatives (A10, A11). Intentional — the substory's honesty is precisely that the *partition is robust but the late-cohort regulator is not yet identified.*

**Proposed slide budget:** 3 content slides + 1 divider

**Slide kinds anticipated:**

- big_idea (substory opener / divider)
- data_figure (ChvI two-phase partition counts 20/10/49; A8)
- claim_evidence (ChvI autoregulation; A9)
- claim_evidence (open late-cohort regulator — SigU negative + ChvR sRNA confound; A10, A11)

---

### S4 — Without lipid A, the cell rebuilds the envelope structurally

**Punchline:** Without lipid A, constitutive sphingolipids and reorganized peptidoglycan hold the envelope together.

**Critical analyses covered:**

- A12: sphingolipid biosynthesis constitutive, not induced (0/6 biosynthesis genes UP; *spt* −0.64 FDR 0.002, *sphk* −0.40 FDR 0.02) — REPORT §"Finding 4" / nb 04_sphingolipid_lpt_panel.ipynb cell 4 — `direct`
- A13: CtpA (CCNA_03113) as LpxF-equivalent processing step — REPORT §"Finding 4" / nb 04 cell 5 — `preliminary` REJECTED at pre-registered bar (logFC +0.58, p=0.048, FDR=0.109, protein not detected)
- A14: Lpt apparatus repurposed for sphingolipid transport (Uchendu 2026 shared-component model) — REPORT §"Finding 4" / nb 04 cells 4 & 6 — `partial` (transcript-protein discordance)
- A15: OM proteome direction-only interpretation (single replicate per strain) — REPORT §"Finding 4" / nb 04 cell 6 — `partial`
- A16: *lptC2* (CCNA_01217) single-replicate protein increase — REPORT §"Finding 4" / nb 04 cell 6 — `preliminary` PILOT-grade
- A18: PG remodeling specific lytic engagement (SdpA +4.8 log2 protein; Pal +2.08/+2.84) — REPORT §"Finding 5" / nb 05_pg_remodeling.ipynb cell 5 — `direct`
- A19: PG broad basal shutdown (28 loci, 20 DOWN) — REPORT §"Finding 5" / nb 05 cell 5 — `direct`
- A20: PG remodeling protein-level statistics caveat — REPORT §"Finding 5" / nb 05 cell 6 — `partial` (single-replicate proteome; direction-only)

**Cluster rationale:** This is the structural-effector layer — what the cell physically does to maintain the envelope once lipid A is lost. Sphingolipid substitution (A12: the pathway is *constitutive*, present before the loss and not induced by it — a key mechanistic point) and peptidoglycan reorganization (A18 specific lytic enzymes UP; A19 broad synthesis DOWN) jointly answer one question — "how is the envelope held together structurally?" — and therefore share one punchline. **This is the talk's largest cluster (8 analyses → 5 content slides) by design:** the throughline explicitly compresses the PG enzyme catalog (A18/A19) to a single downstream-consequence treatment and folds the Lpt-repurposing detail (A14) and its honest caveats into this layer rather than spawning separate substories. The cluster carries TL1's "supporting and still-open" downstream framing: A13 (CtpA-as-LpxF) is REJECTED at the pre-registered bar and appears as an honest "not supported," A14/A15 carry transcript-protein discordance, A16 is pilot-grade (appendix candidate), A20 is the PG protein-stats caveat. **Mixed-confidence note (intentional, and the largest in the deck):** `direct` (A12, A18, A19) + `partial` (A14, A15, A20) + `preliminary` (A13, A16). The gradient is the point — the *direction* of structural remodeling is well-supported while the *molecular detail* (which transporter, which processing enzyme) remains open; slide_compose should keep the rejected/pilot items visibly demoted, not promoted into the spine.

**Proposed slide budget:** 5 content slides + 1 divider

**Slide kinds anticipated:**

- big_idea (substory opener / divider)
- claim_evidence (sphingolipid biosynthesis constitutive, not induced; A12)
- claim_evidence (Lpt apparatus repurposed — transcript-protein discordance, with A16 pilot in appendix; A14, A15, A16)
- claim_evidence (CtpA processing step REJECTED at pre-registered bar — honest negative; A13)
- data_figure (PG remodeling — specific lytic engagement vs broad shutdown; A18, A19)
- claim_evidence (PG protein-level statistics caveat — direction-only; A20) *(may merge with the PG data_figure if compose tightens)*

---

### S5 — Honest bounds: Caulobacter-restricted machinery, graded layer by layer

**Punchline:** The machinery is *Caulobacter*-restricted, and every layer carries its pre-registered grade.

**Critical analyses covered:**

- A21: sphingolipid pathway *Caulobacter*-uniqueness (NCBI: *spt* 7/0/0/0, *cerR* 6/0/0/0) — REPORT §"Finding 6" / nb 06b_ncbi_annotation_presence.ipynb cell 5 — `direct`
- A22: ChvG-ChvI two-component *Caulobacter*-uniqueness (NCBI: ChvG 5/0/0/0, ChvI 6/0/0/0) — REPORT §"Finding 6" / nb 06b cell 5 — `direct`
- A23: NCBI annotation-presence method scope (presence/absence over annotation, not structural homology) — REPORT §"Finding 6" / nb 06b cell 3 — `partial` (annotation-scoped; can miss diverged orthologs)
- A17: *sphk* presence in *A. baumannii* (NCBI=287 outside *Caulobacter*) — ADVERSARIAL_REVIEW_2 N1 — `preliminary` (tempers species-uniqueness scope for that one gene)
- A26: mechanistic synthesis integration (9-point, evidence-graded) — REPORT §Interpretation §1-9 — `partial` (strongest only where component layers are `direct`)
- A27: pre-registered hypothesis scorecard (H1-H4 outcomes) — REPORT §Results (18-row table) / RESEARCH_PLAN §hypotheses — `direct`

**Cluster rationale:** This is the closing substory and its single unifying concept is **honest bounds on the claim** — two faces of the same question, "how far does this result reach, and how much should you believe it?" The *reach* face is the comparative-genomics scope (A21/A22: the sphingolipid pathway and the ChvG-ChvI system are annotation-scoped *Caulobacter*-restricted), bounded by its own method caveats (A23: annotation-presence, not structural homology; A17: *sphk* itself is not unique — 287 NCBI hits outside *Caulobacter*, tempering that one gene's uniqueness). The *believe* face is the graded synthesis (A26: the 9-point integration is only as strong as its `direct` components) and the pre-registered scorecard (A27: H1-H4 outcomes, the discipline that grades the driver claim itself). The throughline names A21/A22 as "scope, not narrated" and A27 as "the discipline that grades the driver claim" — both land here as the deck's conclusion. **Compound-punchline note:** the punchline carries two clauses joined by "and" (scope + grade); kept compound because the two faces are the single closing idea ("honest bounds") and splitting them into two two-analysis substories would create thin clusters (see self-review item 6) without adding a distinct argument. NB07_synthesis_master.png (the 4-panel) is the natural closing visual here.

**Proposed slide budget:** 3 content slides + 1 divider

**Slide kinds anticipated:**

- big_idea (substory opener / divider)
- data_figure (species-restriction atlas — NCBI annotation presence/absence; A21, A22)
- claim_evidence (method scope + *sphk* exception — honest bounds on uniqueness; A23, A17)
- data_figure (graded synthesis + pre-registered scorecard — NB07_synthesis_master.png 4-panel; A26, A27)

---

*Mode-capacity verdict is `fits`; the overflow section (SPEC §4.2.1 / D-027) is omitted because no analysis must be dropped, no mode escalation is required, and no merge is forced. All 27 critical analyses from the plan are covered, each in exactly one cluster, none silently dropped (D-002 rev1).*

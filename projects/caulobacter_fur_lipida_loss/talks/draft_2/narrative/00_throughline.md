<!-- chosen: TL1 -->
<!-- punchline: Δ*fur* derepression is the demonstrable driver of the lipid A-loss-permissive envelope state, and everything downstream is the supporting (and still-open) mechanism it sets in motion. -->

# Throughline (chosen: TL1)

_Picked from `00_throughline_candidates.md` by the smoke orchestrator's throughline gate._

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

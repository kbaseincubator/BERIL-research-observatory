# Throughline candidates — `caulobacter_fur_lipida_loss` (talk-45)

**Generated:** 2026-06-07
**Mode:** `talk-45` (budget 35–48 slides; target 40 — SPEC §5)
**Tier:** `STRONG` (inherited from plan)
**Candidates:** 3 (distinct framings, not rephrasings — see diversity note below)

> **Reuse note.** A selected, user-revised throughline exists at
> `papers/draft_1/00_throughline.md` (TL1, revised 2026-06-04). This invocation did
> **not** pass `PAPER_THROUGHLINE_REUSE=auto-from-paper`, so reuse is not auto-applied;
> the full 2–3 candidate slate is presented for the talk. **TL1 below adapts the paper's
> selected throughline** (same central contribution, talk-format slide/visual planning).
> If you want to lock TL1 without reviewing alternatives, that mirrors the paper decision.

> **Diversity (anti-PA-1):** TL1 = focused central contribution (sphingolipid substitution
> is the payload, regulation is context). TL2 = architecture-as-finding (five co-equal
> layers). TL3 = method-as-finding (calibrated inference / how-we-know). These differ in
> *which evidence is load-bearing*, not in wording — the glyph distributions across the
> three evidence maps are deliberately different.

> **No recommendation (anti-PA-2):** the ordering is happy-path / architecture / method,
> not a ranking. The plan flagged a real **diffusion risk** at talk-45 (five layers at five
> evidence levels can read as "doing too much") — that risk bears on TL1 vs TL2 and is
> surfaced in each candidate's trade-offs for you to weigh. You pick.

---

## Candidate TL1: Δ*fur*-permitted lipid A loss in *Caulobacter* is sustained by a *constitutive* anionic-sphingolipid pool with repurposed Lpt machinery — a route structurally unavailable to other lipid-A-loss-tolerant Gram-negatives — with Fur-released transport and two-phase ChvI signaling as supporting mechanistic context.

**Evidence map:**

| Sub-claim | Source | Strength |
|---|---|---|
| Sphingolipid biosynthesis is constitutive, NOT induced (0/6 UP; *spt* −0.64 FDR 0.002; *sphk* −0.40 FDR 0.02) — **central** | REPORT.md §Finding 4; NB 04_sphingolipid_lpt_panel.ipynb cell 3 | ✓ direct |
| Canonical Lpt apparatus maintained/up at transcript (MsbA-like CCNA_00307 +0.89 FDR 0.01; LptC-related CCNA_03716 +0.56 FDR 0.005) — **central** | REPORT.md §Finding 4; NB 04 cell 3 | ✓ direct |
| Lpt protein-level discordance: LptD −0.47, LptE −0.78 log2 (decline opposite to transcript) — **central, notable finding pending replication** | REPORT.md §Finding 4 protein table; NB 04 cell 6 | ⚠ partial |
| *lptC2* (CCNA_01226) pilot: transcript −0.60 FDR 0.034 but protein +1.08 vs intermediate, +0.66 vs WT | REPORT.md §Finding 4 pilot; NB 04 cells 3,6 | ⚠ partial |
| CCNA_01217 protein +0.77/+0.74 (Zik 2022 sphingolipid gene) | REPORT.md §Finding 4; NB 04 cell 6 | ⚠ partial |
| Sphingolipid pathway is *Caulobacter*-unique: NCBI *spt* (7,0,0,0); *cerR* (6,0,0,0) — **central, species-specificity** | REPORT.md §Finding 6; NB 06b_ncbi_annotation_presence.ipynb cell 3 | ✓ direct |
| ChvG-ChvI alphaproteobacterial-restricted: NCBI ChvG (5,0,0,0); ChvI (6,0,0,0) | REPORT.md §Finding 6; NB 06b cell 3 | ✓ direct |
| Comparators use structurally distinct routes (A.b. PBP1A/Ldt; N.m. capsule; M.c. late-acyltransferase) | REPORT.md §Finding 6; NB 06_comparative_species.ipynb cell 3 | ⚠ partial |
| Δ*fur* derepression concordant with Leaden 2018 (ρ=0.315, p=2.08e-03, 71% sign concordance, 93 DEGs) — *supporting context* | REPORT.md §Finding 1; NB 01_leaden2018_fur_signature.ipynb cell 5 | ✓ direct |
| Path A (n=32) marginally enriched for envelope-stress phenotype (17/32=53.1%; fold 1.60×, p=0.016 vs 33.25% bg) — *supporting* | REPORT.md §Finding 2 table; NB 02b_h2_hypergeometric_verdict.ipynb cell 1 | ⚠ partial |
| Path A per-gene fitness (ChvT \|t\|=43.7; TBDTs \|t\| 9–28) | REPORT.md §Finding 2; NB 02_caulo_fitness_ranking.ipynb cell 9 | ✓ direct |
| Genome background phenotype-bearing rate 33.25% (n=3943, K=1311) | REPORT.md §Finding 2; NB 02_caulo_fitness_ranking.ipynb | ◇ orthogonal |
| Path B (SspB-buffered respiratory) NOT enriched (34.6%, fold 1.04×, p=0.515) — respiratory arm demoted to hypothesis | REPORT.md §Finding 2 table; NB 02b cell 1 | ✗ contradicts |
| SspB-buffered cbb3/cyd/*fix*-NOPQ operon (53/93 Leaden DEGs buffered) | REPORT.md §Finding 1; NB 01 cell 5 | ⚠ partial |
| Zero iron-limitation experiments in Caulo FB (0/198); iron arm descoped | REPORT.md §Finding 2 preflight; NB 02 cell 5 | ◇ orthogonal |
| ChvI two-phase disjoint partition (20 early + 10 both + 49 late) — *supporting* | REPORT.md §Finding 3; NB 03_chvi_phase_partition_sigU.ipynb cell 4 | ✓ direct |
| ChvI autoregulation: CCNA_00237 both-phase logFC +1.45 | REPORT.md §Finding 3; NB 03 cell 5 | ✓ direct |
| SigU as late-cohort driver (coherence 24.5%, Fisher p=0.243) | REPORT.md §Finding 3; NB 03 cell 10 | ✗ contradicts |
| Phase theme shift (regulator-rich early 6.7% → envelope-structural late 10.2% OM/12.2% TBDT) | REPORT.md §Finding 3; NB 03 cell 6 | ⚠ partial |
| CtpA (CCNA_03113) +0.58, pvalue 0.048, FDR 0.109; protein not detected — REJECTED at pre-reg bar | REPORT.md §Finding 4 table; NB 04 cell 5 | ✗ contradicts |
| PG remodeling: 28 loci meet H4 (≥3 required) — *supporting* | REPORT.md §Finding 5; NB 05_pg_remodeling.ipynb cell 5 | ✓ direct |
| PG direction: 20 DOWN + specific inductions (SdpA +4.8 protein; Pal +2.08 transcript/+2.84 protein) | REPORT.md §Finding 5; NB 05 cells 5,8 | ⚠ partial |
| Pal-Tol retrograde-PL interpretation (Tan & Chng 2025) | REPORT.md §Interpretation §8; NB 03/NB 05 convergence | ⚠ partial |
| PaperBLAST ~80% false-negative diagnosis for Caulo lipid A genes | REPORT.md §NB06b table; NB 06b cell 3 | ◇ orthogonal |
| NB00 orientation panel (scoping, not standalone claim) | REPORT.md §Phase A; NB 00_orientation.ipynb | ◇ orthogonal |
| 4-panel synthesis master figure + scorecard | REPORT.md §Key Findings; NB 07_synthesis.ipynb | ✓ direct |

**Slide-count estimate:**

- talk-30: 28 slides
- talk-15: 15
- talk-45: 39 (title 1 + 5 substory dividers + ~24 content + synthesis/scorecard 2 + cross-tenant 1 + implications/future 2 + acks 1 + refs 1 + ~3 Q&A appendix)
- lightning-5: 6

**Visual coherence cost:**

- Existing figures supporting this arc: 6 (NB07_synthesis_master; NB04_sphingolipid_locus_heatmap; NB04_lpt_apparatus_heatmap; NB06_comparative_heatmap; NB01_fur_signature_scatter; 00_sphingolipid_locus_heatmap)
- Procedural diagrams slide-compose will need to add: 3 (strain-series design schematic; sphingolipid-substitution-with-shared-LptB cartoon; "structural unavailability" comparator panel)
- AI-image-gen suggestions (Tier 3, opt-in): 0 (`--ai-diagrams off`)

**What this talk would NOT cover if this is chosen:**

- Path B SspB-respiratory mechanistic criticality (A5 ✗ contradicts; appears only on a limitations/hypothesis slide, not on-claim)
- CtpA as the LpxF-substitute step (A12 ✗ REJECTED at pre-registered bar → limitations slide)
- SigU-as-driver of the late ChvI cohort (A10 ✗ failed → noted as open question only)
- The five-layers-as-co-equal architecture — Fur/ChvI deliberately compressed to *supporting context* to mitigate the plan's diffusion risk (this is the explicit TL1-vs-TL2 trade-off)
- NB00 orientation outputs, NB01 iron-limitation 491-DEG set, PaperBLAST false-negative methodology (A24/A25 → backup/methods slides)

**Substory clusters preview** (substory_design will refine):

- S1: The paradox and the rescue (Δ*lpxc* lethality; Δ*fur* + sphingolipid permissive state; strain series)
- S2: Constitutive sphingolipid substitution + Lpt repurposing — the central contribution (A13,A14,A15,A16,A17)
- S3: Why only *Caulobacter* — structural unavailability across comparators (A21,A22,A23,A24)
- S4: Supporting regulatory context — Fur-released transport + ChvI two-phase (A1–A11)
- S5: Envelope remodeling under LPS loss — PG shutdown + Pal-Tol (A18,A19,A20)

**Tier-evidence:** `STRONG`

---

## Candidate TL2: A single envelope catastrophe — lipid A loss — triggers five partially independent adaptive layers (Fur-released transport, ChvI two-phase signaling, constitutive sphingolipid substitution, peptidoglycan remodeling, and cross-species structural unavailability) that together explain how *and why* *Caulobacter* alone tolerates the deletion.

**Evidence map:**

| Sub-claim | Source | Strength |
|---|---|---|
| Layer 1 — Δ*fur* derepression concordant with Leaden 2018 (ρ=0.315, p=2.08e-03, 71% concordance) | REPORT.md §Finding 1; NB 01_leaden2018_fur_signature.ipynb cell 5 | ✓ direct |
| Layer 1 — SspB-buffered cbb3/cyd/*fix*-NOPQ operon (53/93 Leaden DEGs buffered) | REPORT.md §Finding 1; NB 01 cell 5 | ⚠ partial |
| Layer 1 — Path A (n=32) marginal enrichment (53.1%; fold 1.60×, p=0.016) | REPORT.md §Finding 2 table; NB 02b cell 1 | ⚠ partial |
| Layer 1 — Path A per-gene fitness (ChvT \|t\|=43.7; TBDTs \|t\| 9–28) | REPORT.md §Finding 2; NB 02_caulo_fitness_ranking.ipynb cell 9 | ✓ direct |
| Layer 1 — genome background rate 33.25% (calibration baseline) | REPORT.md §Finding 2; NB 02_caulo_fitness_ranking.ipynb | ◇ orthogonal |
| Layer 1 — Path B NOT enriched (fold 1.04×, p=0.515) — weakens the respiratory sub-layer | REPORT.md §Finding 2 table; NB 02b cell 1 | ✗ contradicts |
| Layer 1 — zero iron-limitation experiments (0/198); iron axis untestable | REPORT.md §Finding 2 preflight; NB 02 cell 5 | ◇ orthogonal |
| Layer 2 — ChvI two-phase partition (20 + 10 + 49) | REPORT.md §Finding 3; NB 03_chvi_phase_partition_sigU.ipynb cell 4 | ✓ direct |
| Layer 2 — ChvI autoregulation (CCNA_00237 +1.45 both-phase) | REPORT.md §Finding 3; NB 03 cell 5 | ✓ direct |
| Layer 2 — SigU as late-cohort driver (24.5%, Fisher p=0.243) | REPORT.md §Finding 3; NB 03 cell 10 | ✗ contradicts |
| Layer 2 — phase theme shift (regulator-early → structural-late) | REPORT.md §Finding 3; NB 03 cell 6 | ⚠ partial |
| Layer 3 — sphingolipid biosynthesis constitutive (0/6 UP; *spt* −0.64; *sphk* −0.40) | REPORT.md §Finding 4; NB 04 cell 3 | ✓ direct |
| Layer 3 — Lpt apparatus maintained/up at transcript (MsbA-like +0.89; LptC-related +0.56) | REPORT.md §Finding 4; NB 04 cell 3 | ✓ direct |
| Layer 3 — Lpt protein discordance (LptD −0.47; LptE −0.78) | REPORT.md §Finding 4 protein table; NB 04 cell 6 | ⚠ partial |
| Layer 3 — *lptC2* pilot (transcript −0.60; protein +1.08/+0.66) | REPORT.md §Finding 4 pilot; NB 04 cells 3,6 | ⚠ partial |
| Layer 3 — CCNA_01217 protein +0.77/+0.74 | REPORT.md §Finding 4; NB 04 cell 6 | ⚠ partial |
| Layer 3 — CtpA REJECTED at pre-reg bar (FDR 0.109; protein not detected) | REPORT.md §Finding 4 table; NB 04 cell 5 | ✗ contradicts |
| Layer 4 — PG remodeling: 28 loci meet H4 (≥3) | REPORT.md §Finding 5; NB 05_pg_remodeling.ipynb cell 5 | ✓ direct |
| Layer 4 — PG direction: 20 DOWN + inductions (SdpA +4.8; Pal +2.08/+2.84) | REPORT.md §Finding 5; NB 05 cells 5,8 | ⚠ partial |
| Layer 4 — Pal-Tol retrograde-PL interpretation (Tan & Chng 2025) | REPORT.md §Interpretation §8; NB 03/NB 05 convergence | ⚠ partial |
| Layer 5 — sphingolipid pathway Caulo-unique (NCBI *spt* 7,0,0,0; *cerR* 6,0,0,0) | REPORT.md §Finding 6; NB 06b_ncbi_annotation_presence.ipynb cell 3 | ✓ direct |
| Layer 5 — ChvG-ChvI alphaproteobacterial-restricted (NCBI 5,0,0,0 / 6,0,0,0) | REPORT.md §Finding 6; NB 06b cell 3 | ✓ direct |
| Layer 5 — comparators' alternative routes (A.b./N.m./M.c.) | REPORT.md §Finding 6; NB 06_comparative_species.ipynb cell 3 | ⚠ partial |
| Layer 5 — PaperBLAST ~80% FN diagnosis (method robustness) | REPORT.md §NB06b table; NB 06b cell 3 | ◇ orthogonal |
| Cross-layer orientation panel (NB00 scoping) | REPORT.md §Phase A; NB 00_orientation.ipynb | ◇ orthogonal |
| 4-panel synthesis master figure (maps the five layers) | REPORT.md §Key Findings; NB 07_synthesis.ipynb | ✓ direct |

**Slide-count estimate:**

- talk-30: 30 slides (tight — would compress one layer)
- talk-15: 16 (does NOT fit five co-equal layers cleanly — see NOT-covered flag)
- talk-45: 44 (near the 48 max; five dividers + ~28 content + synthesis 2 + boilerplate 5 + Q&A 3)
- lightning-5: 6 (cannot carry five layers — flag)

**Visual coherence cost:**

- Existing figures supporting this arc: 8–9 (all NB figures used: NB07_synthesis_master; NB01_fur_signature_scatter + NB01_leaden_iron_vs_fur; NB04 sphingolipid + Lpt heatmaps; NB04_ctpA_per_strain; NB05_pg_remodeling_heatmap; NB06_comparative_heatmap; 00_sphingolipid_locus_heatmap)
- Procedural diagrams slide-compose will need to add: 2–3 (five-layer overview master schematic; per-layer transition diagram; envelope cross-section linking layers)
- AI-image-gen suggestions (Tier 3, opt-in): 0 (`--ai-diagrams off`)

**What this talk would NOT cover if this is chosen:**

- The calibrated-inference / "how-we-know" narrative is flattened — the threshold-miscalibration lesson (REPORT Novel Contribution §7) and PaperBLAST FN diagnosis (A24) drop to backup
- Transcript-protein discordance (A15) gets one slide inside Layer 3 rather than the deeper treatment TL1/TL3 give it
- **At talk-15 and lightning-5 this candidate over-runs:** to fit, it would have to drop Layer 4 (PG) or the Layer 5 species arm — i.e., TL2 is the weakest fit for short modes
- At talk-45 the five-layer breadth pushes toward the 48-slide ceiling and carries the plan's named **diffusion risk** ("doing too much" / five co-equal layers at five evidence levels)

**Substory clusters preview** (substory_design will refine):

- S1: Layer 1 — Fur release: amplified derepression + buffered respiratory operon + fitness ranking (A1–A7)
- S2: Layer 2 — ChvI two-phase signaling cascade (A8–A11)
- S3: Layer 3 — constitutive sphingolipid substitution + Lpt repurposing (A12–A17)
- S4: Layer 4 — peptidoglycan shutdown + Pal-Tol engagement (A18–A20)
- S5: Layer 5 — cross-species structural unavailability (A21–A24)

**Tier-evidence:** `STRONG`

---

## Candidate TL3: Reconstructing the Δ*lpxc* rescue mechanism is a case study in calibrated inference — pre-registered thresholds, a rejected hypothesis (CtpA), transcript-protein discordance, and a recalibrated enrichment test demonstrate what STRONG evidence does and does not license about a multi-layer mechanism.

**Evidence map:**

| Sub-claim | Source | Strength |
|---|---|---|
| Pre-registered scorecard with PASS/PARTIAL/REJECTED verdicts is the spine of the analysis | REPORT.md §Results scorecard; NB 07_synthesis.ipynb | ✓ direct |
| CtpA REJECTED at the pre-registered bar (FDR 0.109; protein not detected) — **headline calibration example** | REPORT.md §Finding 4 table; NB 04_sphingolipid_lpt_panel.ipynb cell 5 | ✓ direct |
| Recalibrated H2: genome background 33.25% exposes ≥10% threshold as uninformative — **methods lesson** | REPORT.md §Finding 2; NB 02_caulo_fitness_ranking.ipynb | ✓ direct |
| Recalibrated H2: Path A marginal (fold 1.60×, p=0.016) vs Path B NOT enriched (fold 1.04×, p=0.515) | REPORT.md §Finding 2 table; NB 02b_h2_hypergeometric_verdict.ipynb cell 1 | ✓ direct |
| Negative result honestly reported — SspB-respiratory arm demoted to hypothesis | REPORT.md §Interpretation §2; NB 02b cell 1 | ✓ direct |
| Transcript-protein discordance: Lpt up at transcript, LptD/LptE down at protein — **central example** | REPORT.md §Finding 4 protein table; NB 04 cells 3,6 | ✓ direct |
| *lptC2* labeled pilot (single replicate) rather than claimed | REPORT.md §Finding 4 pilot; NB 04 cells 3,6 | ⚠ partial |
| CCNA_01217 protein direction-only (single replicate) | REPORT.md §Finding 4; NB 04 cell 6 | ⚠ partial |
| SigU-as-driver test failed and was reported as failed (24.5%, Fisher p=0.243) against a literature gap | REPORT.md §Finding 3; NB 03_chvi_phase_partition_sigU.ipynb cell 10 | ✓ direct |
| Descoping decision: zero iron-limitation experiments → H2 iron arm dropped pre-hoc | REPORT.md §Finding 2 preflight; NB 02 cell 5 | ✓ direct |
| PaperBLAST ~80% FN diagnosis → NB06b NCBI re-test as the authoritative comparative measurement | REPORT.md §NB06b table; NB 06b_ncbi_annotation_presence.ipynb cell 3 | ✓ direct |
| Leaden 2018 concordance as an external validation anchor (ρ=0.315, p=2.08e-03) | REPORT.md §Finding 1; NB 01_leaden2018_fur_signature.ipynb cell 5 | ✓ direct |
| SspB-buffered operon identified by contrast to Leaden Δ*fur*-alone | REPORT.md §Finding 1; NB 01 cell 5 | ⚠ partial |
| Path A per-gene fitness (ChvT \|t\|=43.7) — the evidence that survived recalibration | REPORT.md §Finding 2; NB 02 cell 9 | ✓ direct |
| ChvI two-phase partition exceeds pre-reg ≥10/cohort threshold | REPORT.md §Finding 3; NB 03 cell 4 | ✓ direct |
| ChvI autoregulation (CCNA_00237 +1.45) — a clean molecular datum | REPORT.md §Finding 3; NB 03 cell 5 | ✓ direct |
| Phase theme shift suggestive but not statistically discriminated (Fisher p=0.243) — honestly bounded | REPORT.md §Finding 3; NB 03 cell 6 | ⚠ partial |
| Sphingolipid constitutive — a hypothesis that PASSED strongly (the rule, not just the exceptions) | REPORT.md §Finding 4; NB 04 cell 3 | ✓ direct |
| Lpt maintained at transcript (PASS) — example of a clean transcript-level pass | REPORT.md §Finding 4; NB 04 cell 3 | ✓ direct |
| PG remodeling H4 PASSED strongly (28 loci) with framing tightened post-review | REPORT.md §Finding 5; NB 05_pg_remodeling.ipynb cell 5 | ✓ direct |
| PG direction reframed (20 DOWN; "bidirectional" overstatement corrected); 2 regex FPs flagged | REPORT.md §Finding 5; NB 05 cells 5,8 | ⚠ partial |
| Pal-Tol interpretation explicitly flagged as depending on Tan & Chng 2025, not project data | REPORT.md §Interpretation §8; NB 03/NB 05 | ⚠ partial |
| Species-unavailability claim survives because it rests on comparator absences (NCBI-confirmed) | REPORT.md §Finding 6; NB 06b cell 3 | ✓ direct |
| ChvG-ChvI restriction confirmed across two independent methods | REPORT.md §Finding 6; NB 06b cell 3 | ✓ direct |
| Comparator alternative-route assignment inferred from literature, flagged as inference | REPORT.md §Finding 6; NB 06_comparative_species.ipynb cell 3 | ⚠ partial |
| NB00 orientation reframed three priors before formal testing | REPORT.md §Phase A; NB 00_orientation.ipynb | ◇ orthogonal |
| 4-panel synthesis + scorecard as the calibrated-inference artifact | REPORT.md §Key Findings; NB 07_synthesis.ipynb | ✓ direct |

**Slide-count estimate:**

- talk-30: 26 slides
- talk-15: 14
- talk-45: 36 (4 substory dividers + ~20 content + methods-lessons 2 + scorecard 1 + boilerplate 5 + Q&A 2)
- lightning-5: 6

**Visual coherence cost:**

- Existing figures supporting this arc: 5 (NB07_synthesis_master + scorecard; NB04_ctpA_per_strain — the rejected hypothesis; NB04_lpt_apparatus_heatmap — discordance; NB01_fur_signature_scatter — validation; NB06_comparative_heatmap)
- Procedural diagrams slide-compose will need to add: 2 (scorecard rendered as a verdict-table figure; background-vs-threshold calibration schematic showing the 10%-vs-33% miscalibration)
- AI-image-gen suggestions (Tier 3, opt-in): 0 (`--ai-diagrams off`)

**What this talk would NOT cover if this is chosen:**

- The full mechanistic *model* — biology becomes illustrative material for the inference lessons; the constitutive-sphingolipid / Lpt-repurposing payload (A13/A14/A21) is compressed relative to TL1
- PG remodeling enzyme detail (A18/A19 → one worked example) and ChvI cohort detail (A8/A9 → one example)
- The translational "what this means for antibiotic-resistant Gram-negatives" implication is muted in favor of the methodology narrative
- Risk: a domain audience expecting a *Caulobacter* biology talk may find a methods-centered framing under-delivers on mechanism (the explicit TL3-vs-TL1 trade-off)

**Substory clusters preview** (substory_design will refine):

- S1: Pre-registration and the scorecard — what we committed to before looking (scorecard, thresholds)
- S2: When a hypothesis fails honestly — CtpA rejection + the recalibrated enrichment test (A3,A4,A5,A12)
- S3: When transcript and protein disagree — discordance as a finding, not a flaw (A14,A15,A16)
- S4: What survived scrutiny — the robust core (constitutive sphingolipid + species-unavailability) (A13,A21,A22,A24)

**Tier-evidence:** `STRONG`

---

<!-- chosen: TL2 -->
<!-- punchline: A single envelope catastrophe — lipid A loss — triggers five partially independent adaptive layers (Fur-released transport, ChvI two-phase signaling, constitutive sphingolipid substitution, peptidoglycan remodeling, and cross-species structural unavailability) that together explain how *and why* *Caulobacter* alone tolerates the deletion. -->

# Throughline (chosen: TL2)

_Picked from `00_throughline_candidates.md` by the smoke orchestrator's throughline gate._

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

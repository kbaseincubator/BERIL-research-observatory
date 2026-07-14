# Throughline

**Selected:** TL1 (originally surfaced by `plan.v1` on 2026-06-04T05:17:00Z; revised 2026-06-04 per user input).

**Statement:** Δ*fur*-permitted lipid A loss in *Caulobacter crescentus* is sustained by constitutive sphingolipid substitution with repurposed Lpt machinery, a mechanism structurally unavailable to canonical Gram-negative models, characterized through five partially independent lines of evidence — constitutive sphingolipid biosynthesis, Lpt apparatus transcript-protein discordance, cross-species pathway absence, Fur-released envelope-stress transport, and ChvI two-phase signaling — each at its actual evidence level

**User revision applied:**

> Keep TL1 5-layer structure but elevate TL2's sphingolipid substitution + Lpt repurposing + species-specificity as the central scientific contribution. Frame the Lpt transcript-protein discordance (LptD/LptE protein down; MsbA-like/LptC-related transcript up) as a notable finding pending replicated proteomics, not a flaw to gloss. Path B (SspB respiratory) stays hypothesis-only. Do not overclaim CtpA (REJECTED at pre-registered bar) or lptC2 (single-replicate pilot). Comprehensive analysis warranted across all 4 hypotheses + cross-species arm.

→ Revision propagates by: (1) reframing the throughline statement to foreground constitutive sphingolipid biosynthesis (row 6), Lpt apparatus transcript-protein discordance (row 7), and cross-species pathway unavailability (row 9) as the central scientific contribution, with Fur-released transport (row 1) and ChvI signaling (row 4) as supporting mechanistic context; (2) recasting the Lpt transcript-protein discordance from a weakness ("unresolved") to a notable finding awaiting replicated proteomics (evidence map row 7 Source field updated, weakness inventory bullet revised); (3) no glyph changes required (all evidence strengths remain accurate under the revised framing); (4) retaining hypothesis-only status for Path B (SspB respiratory, row 2) and REJECTED status for CtpA (already captured in weakness inventory) and pilot-observation status for lptC2 (to be included with explicit preliminary labeling per exclusions section).

## Evidence map

| Sub-claim | Source | Strength |
|---|---|---|
| Δ*fur* derepresses a TBDT/iron-uptake subset (Path A, n=32) that is marginally enriched for envelope-stress fitness phenotypes (17/32=53.1% vs 33.25% background; fold=1.60×, hypergeometric p=0.016) | REPORT.md §"Finding 2"; NB 02b_h2_hypergeometric_verdict.ipynb cell 1 | ⚠ partial — enrichment is statistically marginal (p=0.016, just under 0.05); fold=1.60× is modest; REPORT itself calls this "marginal but real enrichment" |
| The SspB-buffered respiratory set (Path B, n=26) is indistinguishable from genome background in envelope-stress fitness phenotypes (fold=1.04×, p=0.515) | REPORT.md §"Finding 2"; NB 02b_h2_hypergeometric_verdict.ipynb cell 1 | ✓ direct — the negative result is explicitly established; "respiratory ATP required" framing demoted to hypothesis |
| 53 of 93 Leaden Δ*fur* DEGs are buffered in our Δ*fur* Δ*sspB* data, dominated by the cbb3/cyd/*fix*-NOPQ micro-aerobic respiratory operon | REPORT.md §"Finding 1"; NB 01_leaden2018_fur_signature.ipynb cell 5 | ✓ direct — transcript-level buffering quantitatively established (Spearman ρ=0.315, p=2.08e-03; 71% sign concordance over 93 DEGs) |
| ChvI engages in two phases with cooperative continuation: 20 unique-to-early, 10 both-phase, 49 late-consequence genes | REPORT.md §"Finding 3"; NB 03_chvi_phase_partition_sigU.ipynb cell 4 | ✓ direct — disjoint partition established with counts exceeding the pre-registered ≥10-per-cohort threshold |
| SigU drives the late ChvI cohort | REPORT.md §"Finding 3"; NB 03_chvi_phase_partition_sigU.ipynb cell 10 | ✗ contradicts — SigU regulon uncharacterized in literature (PaperBLAST returned zero substantive snippets); functional coherence check returned 24.5% (below 50% relaxed criterion); Fisher p=0.243 |
| Sphingolipid biosynthesis is constitutive, not induced: 0/6 biosynthesis genes UP; *spt* DOWN −0.64 FDR 0.002; *sphk* DOWN −0.40 FDR 0.02 | REPORT.md §"Finding 4"; NB 04_sphingolipid_lpt_panel.ipynb cell 3 | ✓ direct — all six genes tested, none significantly UP, two mildly DOWN |
| Canonical Lpt apparatus maintained at transcript level (MsbA-like CCNA_00307 +0.89 FDR 0.01; LptC-related CCNA_03716 +0.56 FDR 0.005) but LptD and LptE proteins decline (−0.47, −0.78 log2) | REPORT.md §"Finding 4"; NB 04_sphingolipid_lpt_panel.ipynb cells 3, 6 | ⚠ partial — transcript upregulation significant (FDR < 0.05), protein data (single-replicate) show opposite direction; transcript-protein discordance is a notable finding pending replicated proteomics (revised 2026-06-04) |
| PG remodeling: 28 genes meeting H4 threshold (≥3 required); predominantly downregulation (20 DOWN) with specific lytic engagements (SdpA +4.8 log2 protein; Pal +2.08 transcript, +2.84 protein) | REPORT.md §"Finding 5"; NB 05_pg_remodeling.ipynb cells 5, 8 | ✓ direct for H4 verdict (28 genes, well above ≥3 threshold); ⚠ partial for Pal-Tol mechanistic interpretation (depends on Tan & Chng 2025, not project data alone; protein data single-replicate) |
| Sphingolipid pathway + ChvG-ChvI are Caulobacter-unique; absence in A.b./N.m./M.c. confirmed by NCBI annotation (spt: 7,0,0,0; ChvG: 5,0,0,0; ChvI: 6,0,0,0) | REPORT.md §"Finding 6"; NB 06b_ncbi_annotation_presence.ipynb cell 3 | ✓ direct — NCBI annotation independently confirms PaperBLAST screen; presence pattern robust across two independent methods |

## Weakness inventory

- **Path A enrichment is marginal.** fold=1.60×, p=0.016 is statistically marginal; a reviewer could reasonably argue this does not distinguish "mechanistically critical" from "modestly over-represented." The pre-registered ≥10% threshold was below the genome background (33.25%), a methodological miscalibration (REPORT Limitations §3).
- **SspB-buffered respiratory arm is hypothesis-only.** The transcript-level buffering is real (NB01), but the fitness data provide no independent support for mechanistic criticality of the cbb3/*fix* set (Path B fold=1.04×, p=0.515). A reviewer will note that one of the five claimed "layers" (SspB buffering) is unsupported by functional data.
- **Lpt apparatus transcript-protein discordance awaits replicated proteomics.** The Uchendu 2026 shared-component prediction is supported at transcript level but contradicted at protein level (LptD −0.47, LptE −0.78 log2) from single-replicate OM proteome. This discordance is a notable finding — potentially reflecting post-translational regulation or functional decoupling — but requires replicated protein measurements for mechanistic resolution (revised 2026-06-04).
- **Single-replicate OM proteome underlies all protein-level claims.** SdpA +4.8, Pal +2.84, lptC2 +1.08, LptD/LptE declines — all from n=1 per strain. No per-protein statistics.
- **SigU as late-cohort driver rejected.** The ChvI two-phase structure is real, but the SigU attribution for the late cohort failed (24.5% coherence, Fisher p=0.243). The late cohort lacks a demonstrated transcriptional driver.
- **CtpA rejected at pre-registered bar** (transcript FDR=0.109; protein not detected). The LpxF-substitute hypothesis (Zik 2022) is not supported by this project's data.
- **Central contribution well-established; supporting layers at varying evidence levels.** The central contribution (constitutive sphingolipid substitution + Lpt transcript-protein discordance + species-specificity) is established at ✓ direct or ⚠ partial with clear replication path. Supporting layers (Fur-released transport marginal enrichment, ChvI signaling) provide mechanistic context at lower evidence levels. Focused framing mitigates diffusion risk (revised 2026-06-04).

## Would NOT include if this is the throughline

- NB00 orientation-phase outputs → Methods supplementary (motivated the research plan, not standalone findings)
- NB01 Leaden 2018 iron-limitation DEG set (491 genes) → supplementary data table (used for internal QC, not a central claim)
- NB06 PaperBLAST false-negative characterization (PB ~80% false-negative rate for Caulobacter lipid A genes) → Methods/supplementary methodological note
- Phase A enrichment statistics (Stein fold=4.75, QY fold=3.18) → brief mention in Methods for motivating H1, not foregrounded as findings
- The pre-registered threshold calibration lesson (REPORT Novel Contribution §7) → brief Methods note or dropped (methodological reflection, not a biological finding)
- lptC2 pilot observation → included but explicitly labeled as pilot/preliminary (single replicate, not a headline finding)

## Triage

**Tier:** STRONG
**Recommended mode:** paper
**Rationale:** REPORT has 9 numbered findings with effect sizes and FDR-corrected p-values throughout; pre-registered hypothesis scorecard with 12 testable sub-claims and explicit verdicts (PASS/PARTIAL/REJECTED); 12-item Limitations section with substantive project-specific content (CtpA rejection, single-replicate proteome, Path B background equivalence, SigU literature gap, PaperBLAST false-negative characterization); methods reproducible from 10 committed notebooks. Formal CIs are not tabulated (claim_inventory.tsv shows ci_present=no for all 108 claims), but FDR correction and effect sizes are comprehensive; this is a minor reporting gap addressable at the Methods/Results drafting stage, not a tier-downgrading deficiency.

---

## Candidate TL1: Δ*fur*-permitted lipid A loss in *Caulobacter crescentus* is sustained by five partially independent mechanism layers — Fur-released transport, ChvI two-phase signaling, constitutive sphingolipid substitution, peptidoglycan remodeling, and cross-species structural unavailability — each characterized at its actual evidence level

**Evidence map:**

| Sub-claim | Source | Strength |
|---|---|---|
| Δ*fur* derepresses a TBDT/iron-uptake subset (Path A, n=32) that is marginally enriched for envelope-stress fitness phenotypes (17/32=53.1% vs 33.25% background; fold=1.60×, hypergeometric p=0.016) | REPORT.md §"Finding 2"; NB 02b_h2_hypergeometric_verdict.ipynb cell 1 | ⚠ partial — enrichment is statistically marginal (p=0.016, just under 0.05); fold=1.60× is modest; REPORT itself calls this "marginal but real enrichment" |
| The SspB-buffered respiratory set (Path B, n=26) is indistinguishable from genome background in envelope-stress fitness phenotypes (fold=1.04×, p=0.515) | REPORT.md §"Finding 2"; NB 02b_h2_hypergeometric_verdict.ipynb cell 1 | ✓ direct — the negative result is explicitly established; "respiratory ATP required" framing demoted to hypothesis |
| 53 of 93 Leaden Δ*fur* DEGs are buffered in our Δ*fur* Δ*sspB* data, dominated by the cbb3/cyd/*fix*-NOPQ micro-aerobic respiratory operon | REPORT.md §"Finding 1"; NB 01_leaden2018_fur_signature.ipynb cell 5 | ✓ direct — transcript-level buffering quantitatively established (Spearman ρ=0.315, p=2.08e-03; 71% sign concordance over 93 DEGs) |
| ChvI engages in two phases with cooperative continuation: 20 unique-to-early, 10 both-phase, 49 late-consequence genes | REPORT.md §"Finding 3"; NB 03_chvi_phase_partition_sigU.ipynb cell 4 | ✓ direct — disjoint partition established with counts exceeding the pre-registered ≥10-per-cohort threshold |
| SigU drives the late ChvI cohort | REPORT.md §"Finding 3"; NB 03_chvi_phase_partition_sigU.ipynb cell 10 | ✗ contradicts — SigU regulon uncharacterized in literature (PaperBLAST returned zero substantive snippets); functional coherence check returned 24.5% (below 50% relaxed criterion); Fisher p=0.243 |
| Sphingolipid biosynthesis is constitutive, not induced: 0/6 biosynthesis genes UP; *spt* DOWN −0.64 FDR 0.002; *sphk* DOWN −0.40 FDR 0.02 | REPORT.md §"Finding 4"; NB 04_sphingolipid_lpt_panel.ipynb cell 3 | ✓ direct — all six genes tested, none significantly UP, two mildly DOWN |
| Canonical Lpt apparatus maintained at transcript level (MsbA-like CCNA_00307 +0.89 FDR 0.01; LptC-related CCNA_03716 +0.56 FDR 0.005) but LptD and LptE proteins decline (−0.47, −0.78 log2) | REPORT.md §"Finding 4"; NB 04_sphingolipid_lpt_panel.ipynb cells 3, 6 | ⚠ partial — transcript upregulation is significant (FDR < 0.05), but protein-level data are from single-replicate OM proteome and go in the opposite direction; whether the apparatus is functionally maintained cannot be resolved |
| PG remodeling: 28 genes meeting H4 threshold (≥3 required); predominantly downregulation (20 DOWN) with specific lytic engagements (SdpA +4.8 log2 protein; Pal +2.08 transcript, +2.84 protein) | REPORT.md §"Finding 5"; NB 05_pg_remodeling.ipynb cells 5, 8 | ✓ direct for H4 verdict (28 genes, well above ≥3 threshold); ⚠ partial for Pal-Tol mechanistic interpretation (depends on Tan & Chng 2025, not project data alone; protein data single-replicate) |
| Sphingolipid pathway + ChvG-ChvI are Caulobacter-unique; absence in A.b./N.m./M.c. confirmed by NCBI annotation (spt: 7,0,0,0; ChvG: 5,0,0,0; ChvI: 6,0,0,0) | REPORT.md §"Finding 6"; NB 06b_ncbi_annotation_presence.ipynb cell 3 | ✓ direct — NCBI annotation independently confirms PaperBLAST screen; presence pattern robust across two independent methods |

**Weakness inventory:**

- **Path A enrichment is marginal.** fold=1.60×, p=0.016 is statistically marginal; a reviewer could reasonably argue this does not distinguish "mechanistically critical" from "modestly over-represented." The pre-registered ≥10% threshold was below the genome background (33.25%), a methodological miscalibration (REPORT Limitations §3).
- **SspB-buffered respiratory arm is hypothesis-only.** The transcript-level buffering is real (NB01), but the fitness data provide no independent support for mechanistic criticality of the cbb3/*fix* set (Path B fold=1.04×, p=0.515). A reviewer will note that one of the five claimed "layers" (SspB buffering) is unsupported by functional data.
- **Lpt apparatus transcript-protein discordance unresolved.** The Uchendu 2026 shared-component prediction is supported at transcript level but contradicted at protein level (LptD −0.47, LptE −0.78 log2). Single-replicate OM proteome prevents resolution. A reviewer will question whether the apparatus is "maintained" when the two measured proteins go down.
- **Single-replicate OM proteome underlies all protein-level claims.** SdpA +4.8, Pal +2.84, lptC2 +1.08, LptD/LptE declines — all from n=1 per strain. No per-protein statistics.
- **SigU as late-cohort driver rejected.** The ChvI two-phase structure is real, but the SigU attribution for the late cohort failed (24.5% coherence, Fisher p=0.243). The late cohort lacks a demonstrated transcriptional driver.
- **CtpA rejected at pre-registered bar** (transcript FDR=0.109; protein not detected). The LpxF-substitute hypothesis (Zik 2022) is not supported by this project's data.
- **Five layers at different evidence levels risks a diffuse paper.** A reviewer may argue the paper tries to do too much and no single finding is established at high rigor beyond "constitutive sphingolipid" and "ChvI phase structure."

**What this paper would NOT include if this is chosen:**

- NB00 orientation-phase outputs → Methods supplementary (motivated the research plan, not standalone findings)
- NB01 Leaden 2018 iron-limitation DEG set (491 genes) → supplementary data table (used for internal QC, not a central claim)
- NB06 PaperBLAST false-negative characterization (PB ~80% false-negative rate for Caulobacter lipid A genes) → Methods/supplementary methodological note
- Phase A enrichment statistics (Stein fold=4.75, QY fold=3.18) → brief mention in Methods for motivating H1, not foregrounded as findings
- The pre-registered threshold calibration lesson (REPORT Novel Contribution §7) → brief Methods note or dropped (methodological reflection, not a biological finding)
- lptC2 pilot observation → included but explicitly labeled as pilot/preliminary (single replicate, not a headline finding)

---

## Candidate TL2: In the *Caulobacter crescentus* Δ*lpxc* rescued state, the constitutive anionic sphingolipid pool substitutes for lipid A without biosynthesis upregulation, the canonical Lpt apparatus shows transcript–protein discordance, and the sphingolipid pathway's restriction to Caulobacter explains species specificity among lipid-A-loss-tolerant Gram-negatives

**Evidence map:**

| Sub-claim | Source | Strength |
|---|---|---|
| Sphingolipid biosynthesis is constitutive: 0/6 biosynthesis genes UP; *spt* DOWN −0.64 FDR 0.002; *sphk* DOWN −0.40 FDR 0.02 — rescue does not require transcriptional induction | REPORT.md §"Finding 4" sub-claim table; NB 04_sphingolipid_lpt_panel.ipynb cell 3 | ✓ direct — all six genes tested against pre-registered threshold, none UP, two mildly DOWN |
| Canonical Lpt transcript upregulation: MsbA-like CCNA_00307 +0.89 FDR 0.01; LptC-related CCNA_03716 +0.56 FDR 0.005 — consistent with Uchendu 2026 shared-component model | REPORT.md §"Finding 4"; NB 04_sphingolipid_lpt_panel.ipynb cell 3 | ✓ direct — transcript-level upregulation of two Lpt-related genes is statistically significant |
| Canonical Lpt proteins detected (LptD, LptE) decline in the rescued strain: LptD log2(4672/4659)=−0.47; LptE log2(4672/4659)=−0.78 | REPORT.md §"Finding 4" protein discordance table; NB 04_sphingolipid_lpt_panel.ipynb cell 6 | ⚠ partial — protein-level data are from single-replicate OM proteome (no statistics); direction contradicts transcript-level upregulation of other Lpt components; cannot resolve whether apparatus is maintained, substrate-limited, or downregulated |
| lptC2 (CCNA_01226) shows transcript−protein discordance: transcript −0.60 FDR 0.034, protein log2(4672/4659)=+1.08 (net vs WT +0.66 log2, ≈1.58×) | REPORT.md §"Finding 4" lptC2 pilot; NB 04_sphingolipid_lpt_panel.ipynb cells 3, 6 | ⚠ partial — single-replicate OM proteome; the +1.08 partially recovers a prior −0.42 decline in the intermediate strain; REPORT labels this "suggestive pilot observation requiring replicated proteomics" |
| CtpA (CCNA_03113) provides the LpxF-equivalent processing step (Zik 2022 prediction) | REPORT.md §"Finding 4" sub-claim table; NB 04_sphingolipid_lpt_panel.ipynb cell 5 | ✗ contradicts — CtpA transcript FDR=0.109 in the pre-registered 4599-vs-4584 contrast (fails FDR<0.05 bar); protein NOT detected in OM proteome; REPORT verdict: REJECTED at pre-registered bar |
| CCNA_01217 (Zik 2022 sphingolipid biosynthesis) protein log2=+0.77 in rescued vs intermediate, +0.74 vs WT — consistent with post-transcriptional pathway stabilization | REPORT.md §"Finding 4"; NB 04_sphingolipid_lpt_panel.ipynb cell 6 | ⚠ partial — single-replicate OM proteome; direction consistent but no replication or statistical test |
| Sphingolipid pathway is Caulobacter-unique: spt NCBI (7,0,0,0); cerR NCBI (6,0,0,0); absent from A.b., N.m., M.c. | REPORT.md §"Finding 6"; NB 06b_ncbi_annotation_presence.ipynb cell 3 | ✓ direct — NCBI annotation confirms across all four species; independently supported by Olea-Ozuna 2020/2024 |
| ChvG-ChvI is alphaproteobacterial-restricted: ChvG NCBI (5,0,0,0); ChvI NCBI (6,0,0,0) | REPORT.md §"Finding 6"; NB 06b_ncbi_annotation_presence.ipynb cell 3 | ✓ direct — NCBI annotation confirms; consistent with Greenwich 2023 review |
| Other species use structurally distinct routes: A.b. PBP1A/Ldt (Kang 2021), N.m. capsule (Steeghs 2001), M.c. late acyltransferase (Gao 2008) | REPORT.md §"Finding 6"; NB 06_comparative_species.ipynb cell 3 | ⚠ partial — the project's comparative data (PaperBLAST screen + NCBI annotation) show each species has the appropriate pathway components; however, M.c. is under-annotated in PaperBLAST (162 genes total), and the functional link between gene presence and the published rescue routes is inferred from the cited literature, not directly tested |

**Weakness inventory:**

- **Core mechanistic claim (Lpt repurposing) has unresolved transcript–protein discordance.** The two canonical Lpt proteins actually measured (LptD, LptE) decline at the protein level in the rescued strain, contradicting the transcript-level upregulation of MsbA-like and LptC-related components. Whether the apparatus is functionally maintained, substrate-limited (because LPS precursors are absent), or genuinely downregulated cannot be resolved from single-replicate OM proteome. A reviewer will note this is the central claim's weak point.
- **CtpA is REJECTED at the pre-registered bar.** Zik 2022's prediction that CtpA provides the LpxF-equivalent processing step is untested by this work (FDR=0.109, protein not detected). This is a significant gap for the sphingolipid-substitution narrative because the processing step remains unidentified.
- **lptC2 pilot observation is single-replicate.** The +1.08 log2 protein increase partially recovers a prior −0.42 decline, yielding a net +0.66 vs WT. A reviewer will note: (a) single replicate, (b) partial recovery rather than a clean induction, (c) transcript goes down while protein goes up (post-transcriptional stabilization hypothesis requires independent evidence).
- **Single-replicate OM proteome limits all protein-level claims.** CCNA_01217 +0.77, lptC2 +1.08, LptD −0.47, LptE −0.78 — all direction-only, no per-protein statistical testing.
- **Iron-limitation experiments absent.** The fitness-browser Caulobacter compendium has 0 iron-limitation experiments (REPORT Limitations §8). The Fur-released iron-uptake machinery's role in sphingolipid trafficking (a plausible mechanism link) cannot be assessed under iron-limiting conditions.
- **M. catarrhalis comparative data advisory only** due to PaperBLAST under-annotation (162 total genes; REPORT Limitations §7). The species-specificity argument rests primarily on A.b. and N.m.

**What this paper would NOT include if this is chosen:**

- Full Fur regulon dissection (Finding 1, Finding 2 Path A/B enrichment analysis) → discussed briefly as regulatory context in Introduction/Results, not foregrounded; NB01 Leaden concordance and NB02/02b fitness ranking relegated to supplementary
- ChvI two-phase engagement detail (Finding 3) → one paragraph in Results as "regulatory coordination" context; the 20+10+49 partition and SigU analysis → supplementary
- SspB respiratory-buffering negative result (Finding 1/2 Path B) → brief mention in Discussion as a limitation of the dual-release model; not central
- PG remodeling detail (Finding 5 — 28 genes, SdpA, FtsI, endopeptidases) → discussed as a parallel envelope response but not foregrounded; NB05 heatmap → supplementary
- Pal-Tol upregulation (Finding 5 cross-notebook convergence with NB03) → brief Discussion mention; not central to the sphingolipid narrative unless Pal is reframed as OM lipid homeostasis (Tan & Chng 2025) — could be elevated to a short Results paragraph
- The pre-registered threshold calibration lesson → dropped (methodological, not sphingolipid biology)

---

## Candidate TL3: Dissection of the Δ*fur* regulon in *Caulobacter crescentus* reveals a marginally enriched TBDT/iron-uptake subset under envelope stress and a two-phase ChvI cooperator–consequence engagement across the Δ*fur* → Δ*lpxc* strain series, while the SspB-buffered respiratory set is indistinguishable from genome background

**Evidence map:**

| Sub-claim | Source | Strength |
|---|---|---|
| 4584-vs-4580 signal correlates with Leaden 2018 Δ*fur* at Spearman ρ=0.315, p=2.08e-03 over 93 DEGs with 71% sign concordance — confirming Fur derepression as a major driver | REPORT.md §"Finding 1"; NB 01_leaden2018_fur_signature.ipynb cell 5 | ✓ direct — concordance quantitatively established with specific source (Leaden 2018 Table 2) |
| SspB buffering of cbb3/cyd/*fix*-NOPQ respiratory operon: 53 of 93 Leaden Δ*fur* DEGs are buffered in our Δ*fur* Δ*sspB* data | REPORT.md §"Finding 1"; NB 01_leaden2018_fur_signature.ipynb cell 5 | ✓ direct — transcript-level buffering quantitatively established |
| Path A (concordant_strong Fur-released TBDTs, n=32) is marginally enriched for envelope-stress fitness phenotypes vs genome background (17/32=53.1%; fold=1.60×; hypergeometric p=0.016; background=33.25%) | REPORT.md §"Finding 2"; NB 02b_h2_hypergeometric_verdict.ipynb cell 1 | ⚠ partial — enrichment is real but marginal (p=0.016; fold only 1.60×); REPORT itself labels this "marginally enriched"; the pre-registered ≥10% threshold was below background, a methodological miscalibration |
| Path B (SspB-buffered, n=26) is NOT enriched vs genome background (9/26=34.6%; fold=1.04×; p=0.515) — respiratory buffering arm is not supported by fitness data | REPORT.md §"Finding 2"; NB 02b_h2_hypergeometric_verdict.ipynb cell 1 | ✓ direct — the negative result is explicitly established and quantified |
| Top fitness hits in Path A include ChvT (CCNA_03108, \|*t*\|=43.7) and TBDTs CCNA_02910, 00210, 02048, 00028 (\|*t*\| 9–28) under envelope stress | REPORT.md §"Finding 2"; NB 02_caulo_fitness_ranking.ipynb cell 9 | ✓ direct — individual gene fitness t-statistics from kescience_fitnessbrowser |
| ChvI engages in two phases: 20 unique-to-early (4584-vs-4580), 10 both-phase, 49 late-consequence (only 4599-vs-4584); ChvI itself in both-phase at logFC +1.45 (autoregulation evidence) | REPORT.md §"Finding 3"; NB 03_chvi_phase_partition_sigU.ipynb cells 4, 5 | ✓ direct — disjoint partition established; counts exceed ≥10-per-cohort threshold; ChvI autoregulation is a specific molecular datum |
| Regulator-rich early → envelope-structural late theme shift: 6.7% regulator/TCS in early vs 10.2% envelope/OM and 12.2% TBDT in late; 0% lipid/membrane and PG/cell wall in early | REPORT.md §"Finding 3"; NB 03_chvi_phase_partition_sigU.ipynb cell 6 | ⚠ partial — theme proportions descriptive; Fisher exact test for enrichment shift is not significant (p=0.243, odds ratio=1.88); REPORT states "suggestive but not statistically discriminated" |
| SigU (CCNA_02977, +3.13 in 4599-vs-4584) as operational driver of the late cohort | REPORT.md §"Finding 3"; NB 03_chvi_phase_partition_sigU.ipynb cell 10 | ✗ contradicts — Caulobacter SigU is uncharacterized in the literature (PaperBLAST: zero substantive snippets); coherence check returned 24.5% (below 50% relaxed criterion); no gold-standard regulon exists to test against |
| Zero iron-limitation experiments in Caulobacter fitness compendium (0 of 198 experiments); iron axis of H2 descoped | REPORT.md §"Finding 2" preflight; NB 02_caulo_fitness_ranking.ipynb cell 5 | ✓ direct — the absence is directly established from the compendium classification (REPORT: "zero pure iron-limitation experiments") |

**Weakness inventory:**

- **Path A enrichment is marginal (fold=1.60×, p=0.016).** A sharp reviewer will note: (a) the fold enrichment is modest; (b) p=0.016 with n=32 is not robust to multiple testing across gene-set definitions; (c) the original ≥10% threshold was below the genome background (33.25%), requiring post-hoc recalibration to hypergeometric enrichment (NB02b). The "critical subset" framing claims more specificity than the data robustly support.
- **Path B null result weakens the dual-release switch model.** The project cannot distinguish whether SspB buffering of the respiratory chain matters for the rescue. The transcript-level effect is real (NB01) but the fitness data (Path B fold=1.04×, p=0.515) provide no support for mechanistic importance. The "dual-release switch" model is therefore one-armed: only the Fur derepression arm is supported.
- **ChvI theme shift is not statistically significant.** The "regulator-rich early → envelope-structural late" narrative is descriptive (Fisher p=0.243). The phase partition itself is real (20+10+49 counts) but the biological interpretation of what distinguishes the phases is post-hoc.
- **Iron-limitation axis untestable.** The Caulobacter fitness compendium has zero iron-limitation experiments (REPORT Limitations §8). H2 was descoped to envelope-stress-only. The iron-flux arm of the Fur regulon's contribution — arguably the most biologically relevant axis given Zik 2022's "Fur-regulated processes (not iron status per se)" framing — cannot be assessed.
- **SigU attribution failed.** The SigU-as-late-cohort-driver hypothesis is untestable without a Caulobacter SigU regulon (none exists in the literature). This leaves the late cohort's transcriptional driver unidentified.
- **Spearman ρ=0.315 is moderate concordance.** While p=2.08e-03 is significant, ρ=0.315 means ~90% of variance in 4584-vs-4580 logFC is not explained by Leaden's Δ*fur* signal. The Δ*sspB* co-deletion contributes signal that this approach cannot fully disentangle.

**What this paper would NOT include if this is chosen:**

- Sphingolipid constitutive expression detail (Finding 4) → one-paragraph Results context; NB04 heatmaps and sub-claim table → supplementary
- Lpt apparatus transcript-protein discordance (Finding 4) → supplementary; brief Discussion mention as "Uchendu 2026 prediction partially supported at transcript level"
- lptC2 pilot observation (Finding 4) → supplementary or Discussion future-directions paragraph
- CtpA rejection (Finding 4) → brief negative-result note in Discussion
- PG remodeling (Finding 5 — 28 genes, SdpA, Pal-Tol) → one paragraph in Results as a parallel response; NB05 heatmap → supplementary figure
- Cross-species structural unavailability (Finding 6) → Discussion section on species specificity, not a foregrounded finding; NB06/06b comparative data → supplementary table
- Pal-Tol mechanistic interpretation (Tan & Chng 2025 retrograde PL transport) → dropped or brief Discussion note
- CCNA_01217 protein observation → dropped (single replicate, not central)

---

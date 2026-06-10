# Plan — `caulobacter_fur_lipida_loss`

**Generated:** 2026-06-08T17:30:00Z
**Mode requested:** `talk-30` (peer audience)

## Tier verdict

**Tier:** `STRONG`

**Reasoning:**

- REPORT.md presents 6 numbered findings, each with effect sizes and inferential statistics: Leaden Δ*fur* concordance (Spearman ρ = 0.315, p = 2.08e-03, n = 93 DEGs, §"Finding 1"); Path A envelope-stress enrichment (17/32 = 53.1% vs 33.25% background, fold 1.60×, hypergeometric p = 0.016, §"Finding 2"); ChvI two-phase partition (20 early / 10 both / 49 late, §"Finding 3"). This is the numbered-findings-with-statistical-reporting signature of STRONG.
- REPORT.md carries an explicit, pre-registered hypothesis scorecard (§Results, 18 rows with SUPPORTED / HYPOTHESIS / REJECTED verdicts) AND an 11-entry `## Limitations` section (lines 244-256) that names methodological gaps per finding — the hallmark of a project that has self-audited rather than self-promoted.
- Two independent adversarial review rounds exist (ADVERSARIAL_REVIEW_2.md: 0 critical / 3 important / 2 suggested, 8/9 round-1 issues resolved); the reviewer independently reproduced the Path A enrichment (fold 1.598×, p = 0.0156, Bonferroni-robust). External verification of the load-bearing statistic confirms STRONG over THIN.

**Tier classification rule applied:**

- STRONG: clear research question (Δ*fur*-permitted lipid A loss mechanism) + numbered findings with CIs / p-values + explicit limitations. All three present. (Matched.)
- THIN: not applicable — quantitative claims are CI'd / p-valued, not un-supported.
- EXPLORATORY: not applicable — multi-layer validation + comparative-genomics replication present.

## Mode appropriateness

**Requested mode:** `talk-30` — slide-budget ~20-30 per SPEC §5.

**Verdict:** `appropriate`

**Reasoning:**

- STRONG tier fits any talk mode per the mode-tier matrix; talk-30 is squarely within range.
- The prior talk-45 draft (talks/draft_1/working/00_throughline_candidates.md) estimated all three candidate arcs at 26-30 content slides when compressed to talk-30 (TL1=28, TL2=30, TL3=26). The evidence base sustains a 30-minute arc without padding and without starving any layer of real estate.
- STRONG evidence with an honest gradient (3 SUPPORTED layers, 2 demotions, 1 PARTIAL, 1 PILOT) is well-matched to 30 minutes: enough time to present the supported spine AND the caveats without rushing into overclaim.

**Recommended adjustment (if any):**

- none.

The orchestrator surfaces this recommendation to the user but does NOT
auto-change the mode. The user picks.

## Critical-analysis inventory (input to substory_design)

The substory_design agent groups these into substories. Every analysis in
REPORT.md that bears on a finding is listed; negatives and rejected tests
are kept (not filtered). Strength tags honor the `## Limitations` section.

| ID | Analysis | Source | Strength of finding | Notes |
|---|---|---|---|---|
| A1 | Leaden 2018 Δ*fur* signature concordance (ρ=0.315, p=2.08e-03, 71% sign concordance over 93 DEGs) | REPORT.md §"Finding 1"; notebook 01_leaden2018_fur_signature.ipynb cell 5 | `direct` | (no Limitation downgrades the correlation itself) |
| A2 | Leaden iron-limitation vs Δ*fur* internal discrimination | REPORT.md §"Finding 1"; notebook 01_leaden2018_fur_signature.ipynb cell 7 | `partial` | L: transcriptome is single growth condition (PYE rich) — signal is constitutive Δ*fur* derepression, not iron-limitation response |
| A3 | cbb3 / *fix* respiratory operon Fur-release listing | REPORT.md §"Finding 1"; notebook 01_leaden2018_fur_signature.ipynb cell 9 | `direct` | supporting detail; gene-by-gene listing |
| A4 | Path A (32-gene Fur-released subset) envelope-stress fitness enrichment (17/32=53.1%, fold 1.60×, p=0.016) | REPORT.md §"Finding 2"; notebook 02b_h2_hypergeometric_verdict.ipynb cell 2 | `partial` | REPORT labels enrichment "marginal" (1.60× over 33.25% background); independently reproduced by adversarial reviewer but magnitude is modest |
| A5 | Genome-background calibration (K=1311 / N=3943 = 33.25%) for the hypergeometric test | REPORT.md §"Finding 2"; notebook 02b_h2_hypergeometric_verdict.ipynb cell 1 | `direct` | the calibration itself is sound; underpins the threshold-miscalibration lesson |
| A6 | Pre-registered ≥10% threshold miscalibration lesson (10% sits below 33.25% background) | REPORT.md §Results scorecard; RESEARCH_PLAN.md §thresholds | `direct` | methodological lesson; orthogonal to biology |
| A7 | Path B (SspB-buffered respiratory arm, 26 genes) enrichment test (9/26=34.6%, fold 1.04×, p=0.515) | REPORT.md §"Finding 2"; notebook 02b_h2_hypergeometric_verdict.ipynb cell 2 | `preliminary` | NEGATIVE — indistinguishable from background; REPORT demotes SspB arm from mechanism to hypothesis |
| A8 | ChvI envelope-stress two-phase partition (unique-early=20, both-phase=10, late=49) | REPORT.md §"Finding 3"; notebook 03_chvi_phase_partition_sigU.ipynb cell 7 | `direct` | (partition counts are descriptive and robust) |
| A9 | ChvI autoregulation (CCNA_00237 +1.45) | REPORT.md §"Finding 3"; notebook 03_chvi_phase_partition_sigU.ipynb cell 7 | `direct` | |
| A10 | SigU drives the late ChvI cohort | REPORT.md §"Finding 3"; notebook 03_chvi_phase_partition_sigU.ipynb cell 10 | `preliminary` | NEGATIVE — late-cohort coherence 24.5% (below 50% bar), Fisher p=0.243; ADVERSARIAL_REVIEW_2 N2: SigU is in fact characterized (Alvarez-Martinez 2007 PMID 17986185), revisit framing |
| A11 | ChvR sRNA alternative post-transcriptional mechanism (review-raised confound) | ADVERSARIAL_REVIEW_2.md N3 (Fröhlich 2018 PMID 30165530) | `preliminary` | not in REPORT; flagged as a Path A / ChvI confound the talk should acknowledge |
| A12 | Sphingolipid biosynthesis constitutive, not induced (0/6 biosynthesis genes UP; *spt* −0.64 FDR 0.002, *sphk* −0.40 FDR 0.02) | REPORT.md §"Finding 4"; notebook 04_sphingolipid_lpt_panel.ipynb cell 4 | `direct` | |
| A13 | CtpA (CCNA_03113) as LpxF-equivalent processing step (Zik 2022 prediction) | REPORT.md §"Finding 4"; notebook 04_sphingolipid_lpt_panel.ipynb cell 5 | `preliminary` | REJECTED at pre-registered bar — logFC +0.58, p=0.048, FDR=0.109, protein not detected |
| A14 | Lpt apparatus repurposed for sphingolipid transport (Uchendu 2026 shared-component model) | REPORT.md §"Finding 4"; notebook 04_sphingolipid_lpt_panel.ipynb cells 4 & 6 | `partial` | transcript UP (MsbA-like +0.89 FDR 0.01, LptC-related +0.56 FDR 0.005) but detected proteins LptD (−0.47) and LptE (−0.78) DECLINE — transcript-protein discordance |
| A15 | OM proteome direction-only interpretation (single replicate per strain) | REPORT.md §"Finding 4"; notebook 04_sphingolipid_lpt_panel.ipynb cell 6 | `partial` | L: single-replicate OM proteome, no per-protein statistics; only direction interpretable |
| A16 | lptC2 (CCNA_01217) single-replicate protein increase | REPORT.md §"Finding 4"; notebook 04_sphingolipid_lpt_panel.ipynb cell 6 | `preliminary` | PILOT-grade; single-replicate; appendix candidate |
| A17 | *sphk* presence in *A. baumannii* (review note on comparative claim) | ADVERSARIAL_REVIEW_2.md N1 | `preliminary` | NCBI=287 for *sphk* outside *Caulobacter*; tempers the species-uniqueness scope for that gene |
| A18 | PG remodeling specific lytic engagement (SdpA +4.8 log2 protein; Pal +2.08 / +2.84) | REPORT.md §"Finding 5"; notebook 05_pg_remodeling.ipynb cell 5 | `direct` | strong protein-level signal |
| A19 | PG broad basal shutdown (28 loci, 20 DOWN) | REPORT.md §"Finding 5"; notebook 05_pg_remodeling.ipynb cell 5 | `direct` | |
| A20 | PG remodeling protein-level statistics caveat | REPORT.md §"Finding 5"; notebook 05_pg_remodeling.ipynb cell 6 | `partial` | L: single-replicate proteome; direction-only for protein magnitudes |
| A21 | Sphingolipid pathway *Caulobacter*-uniqueness (NCBI: *spt* 7/0/0/0, *cerR* 6/0/0/0) | REPORT.md §"Finding 6"; notebook 06b_ncbi_annotation_presence.ipynb cell 5 | `direct` | |
| A22 | ChvG-ChvI two-component *Caulobacter*-uniqueness (NCBI: ChvG 5/0/0/0, ChvI 6/0/0/0) | REPORT.md §"Finding 6"; notebook 06b_ncbi_annotation_presence.ipynb cell 5 | `direct` | |
| A23 | NCBI annotation-presence method (presence/absence over annotation, not structural homology) | REPORT.md §"Finding 6"; notebook 06b_ncbi_annotation_presence.ipynb cell 3 | `partial` | annotation-based presence can miss diverged orthologs; uniqueness is annotation-scoped |
| A24 | Strain 4580 / 4584 / 4599 design contrast (lipid A-replete vs -deficient) | REPORT.md §Methods; RESEARCH_PLAN.md §design | `direct` | foundational experimental contrast |
| A25 | Zik 2022 (PMID 35649364) baseline-mechanism anchoring | REPORT.md §Interpretation; RESEARCH_PLAN.md §background | `direct` | literature baseline, not a new result |
| A26 | Mechanistic synthesis integration (9-point, evidence-graded SUPPORTED/HYPOTHESIS/PARTIAL/MIXED/PILOT) | REPORT.md §Interpretation §1-9 | `partial` | the integration is a narrative over heterogeneous evidence; strongest only where its component layers are `direct` |
| A27 | Pre-registered hypothesis scorecard (H1-H4 outcomes) | REPORT.md §Results (18-row table); RESEARCH_PLAN.md §hypotheses | `direct` | the scorecard discipline itself is a methodological strength |

**Notes column rule applied:** REPORT's `## Limitations` (single growth
condition; single-replicate OM proteome; annotation-scoped uniqueness;
threshold calibration) downgrade A2, A4, A14, A15, A20, A23, A26 to
`partial`; negatives/rejections (A7, A10, A13, A16) and review-raised
confounds (A11, A17) sit at `preliminary`. Strength distribution: 14
`direct`, 7 `partial`, 6 `preliminary` (48% partial-or-weaker — above the
PA-6 ≥30% floor expected when a Limitations section exists).

## Throughline candidate seeds (input to throughline agent)

Three candidate meta-arcs at one-sentence depth. The throughline agent
expands these into full evidence maps and surfaces them to the user.
Not picking — seeding only.

- TL1 (central-contribution): Δ*fur* derepression is the demonstrable driver of the lipid A-loss-permissive envelope state, anchored by the reproduced Leaden concordance and the marginally-but-robustly enriched Fur-released envelope-stress subset (Path A), with the remaining layers presented as the supporting and still-open mechanism.
- TL2 (architecture / five-layer atlas): a coordinated multi-layer envelope-remodeling program — Fur-derepressed transport, ChvI two-phase engagement, constitutive sphingolipid substitution, PG reorganization, and species-restricted machinery — each layer narrated at its true evidence grade including the demotions.
- TL3 (method / calibrated inference): how a pre-registered scorecard plus a genome-background calibration converts an enthusiastic mechanism hypothesis into an honestly-graded result, using the ≥10%-threshold miscalibration and the Path B / CtpA / SigU demotions as the worked illustration.

## Pipeline state

- **paper-writer reuse available:** `yes` — `papers/draft_2/00_throughline.md`
  exists with a chosen throughline (TL1 integrative mechanism-atlas). Per
  D-009, reuse defaults ON; the throughline agent should reconcile the
  paper's selected arc with the talk's candidate seeds rather than ignore it.
- **atlas runtime data:** `not consumed` (per D-010 — algorithmic borrow only).
- **Cross-tenant integration slide:** required (SPEC §7).
- **AI image generation:** `off` (default; no `--ai-diagrams opt-in` flag).

## Gap-fill (optional)

REPORT.md is complete (6 findings, scorecard, synthesis, 11-entry
Limitations) and two adversarial review rounds are present. No gap-fill
request filed; this plan ran with a full evidence base.

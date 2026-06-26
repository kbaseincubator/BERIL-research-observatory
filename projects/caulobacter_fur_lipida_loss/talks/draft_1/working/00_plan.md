# Plan — `caulobacter_fur_lipida_loss`

**Generated:** 2026-06-07T00:00:00Z
**Mode requested:** `talk-45`

## Tier verdict

**Tier:** `STRONG`

**Reasoning:**

- REPORT.md presents **9 numbered findings** (Findings 1–6 plus an 8-point mechanistic
  synthesis) with effect sizes and FDR-corrected statistics throughout — e.g. Spearman
  ρ=0.315, p=2.08e-03 over 93 DEGs (§Finding 1); hypergeometric Path A fold=1.60×, p=0.016
  vs 33.25% background (§Finding 2 table); *spt* −0.64 FDR 0.002 (§Finding 4 sub-claim table).
- A **pre-registered hypothesis scorecard** (REPORT.md §Results) tabulates 12+ sub-claims
  against thresholds committed in RESEARCH_PLAN.md §"Pre-registered significance thresholds"
  (lines 269–277), with explicit PASS / PARTIAL / REJECTED verdicts — including a finding
  (CtpA) actively *rejected* at the pre-registered bar after adversarial review.
- A substantive **11-item Limitations section** (REPORT.md lines 245–256) with
  project-specific content (single-replicate OM proteome, Path B background equivalence,
  PaperBLAST ~80% false-negative diagnosis), and **10 committed notebooks** (NB00–NB07 +
  NB02b + NB06b) backing each finding.

**Tier classification rule applied:**

- STRONG: clear research question (RESEARCH_PLAN.md §"Refined research question") +
  numbered findings with effect sizes / FDR-corrected p-values + explicit pre-registered
  thresholds and a real Limitations section. Note: formal CIs are not tabulated (paper-draft
  `claim_inventory.tsv` records ci_present=no across claims), but FDR correction + effect
  sizes are comprehensive — a minor reporting gap, not tier-downgrading.

## Mode appropriateness

**Requested mode:** `talk-45` — slide-budget per SPEC §5 (longest talk format).

**Verdict:** `appropriate`

**Reasoning:**

- STRONG-tier projects fit any talk mode per the mode-tier matrix. This project carries
  **six findings across four hypotheses + a cross-species arm**, with enough independent
  evidence lines (five-layer mechanistic model) to sustain a 45-minute narrative arc without
  starving real estate or padding. The depth of the pre-registered scorecard and the
  nuanced evidence-level distinctions (direct vs. partial vs. rejected) reward the longer
  format, which can devote slides to the transcript-protein discordance and the
  evidence-level honesty that a lightning talk would have to flatten.
- A real risk at talk-45 length is **diffusion** — five layers at five evidence levels can
  read as "doing too much." The throughline agent should weight a focused central-contribution
  framing (sphingolipid substitution + Lpt repurposing + species-specificity) with the Fur/ChvI
  layers as supporting mechanistic context, matching the user's paper-draft revision.

**Recommended adjustment (if any):**

- none. talk-45 is appropriate. Surface the diffusion risk to the throughline agent so the
  selected arc foregrounds a load-bearing contribution rather than five co-equal layers.

## Critical-analysis inventory (input to substory_design)

The substory_design agent groups these into substories. Every analysis in REPORT.md that
bears on a finding is listed; no grouping, ranking, or filtering applied here.

| ID | Analysis | Source | Strength of finding | Notes |
|---|---|---|---|---|
| A1 | Leaden 2018 Δ*fur* concordance (ρ=0.315, p=2.08e-03, 71% sign concordance, 93 DEGs) | REPORT.md §Finding 1; NB 01_leaden2018_fur_signature.ipynb cell 5 | `direct` | (transcript-level concordance quantitatively established) |
| A2 | SspB-buffered cbb3/cyd/*fix*-NOPQ operon identified (53/93 Leaden Δ*fur* DEGs buffered) | REPORT.md §Finding 1; NB 01 cell 5 | `partial` | L#3: mechanistic criticality of buffered set unsupported by fitness data (Path B = background) |
| A3 | Genome-background phenotype-bearing rate = 33.25% (n=3943, K=1311) | REPORT.md §Finding 2; NB 02_caulo_fitness_ranking.ipynb | `direct` | (background rate directly computed) |
| A4 | Path A (concordant_strong, n=32) hypergeometric enrichment 17/32=53.1%, fold=1.60×, p=0.016 | REPORT.md §Finding 2 table; NB 02b_h2_hypergeometric_verdict.ipynb cell 1 | `partial` | L#3: marginal enrichment (p just <0.05; fold modest); ≥10% pre-reg threshold sat below 33.25% background — miscalibration |
| A5 | Path B (SspB-buffered, n=26) NOT enriched: 9/26=34.6%, fold=1.04×, p=0.515 | REPORT.md §Finding 2 table; NB 02b cell 1 | `direct` | (negative result explicitly established; "respiratory ATP" arm demoted) |
| A6 | Individual Path A fitness t-stats: ChvT \|t\|=43.7; TBDTs CCNA_02910/00210/02048/00028 \|t\| 9–28 | REPORT.md §Finding 2; NB 02_caulo_fitness_ranking.ipynb cell 9 | `direct` | (per-gene t-statistics from kescience_fitnessbrowser) |
| A7 | Zero iron-limitation experiments in Caulo FB compendium (0 of 198); H2 iron arm descoped | REPORT.md §Finding 2 preflight; NB 02 cell 5 | `direct` | L#9: iron-axis of H2 untestable in this compendium |
| A8 | ChvI two-phase disjoint partition: 20 unique-early + 10 both-phase + 49 late (=79) | REPORT.md §Finding 3; NB 03_chvi_phase_partition_sigU.ipynb cell 4 | `direct` | (counts exceed pre-reg ≥10/cohort threshold) |
| A9 | ChvI autoregulation: ChvI (CCNA_00237) in both-phase set at logFC +1.45 | REPORT.md §Finding 3; NB 03 cell 5 | `direct` | (specific molecular datum) |
| A10 | SigU as late-cohort driver: coherence check 24.5%, Fisher p=0.243 | REPORT.md §Finding 3; NB 03 cell 10 | `preliminary` | L#6: Caulobacter SigU uncharacterized (PaperBLAST zero snippets); no gold standard; failed relaxed criterion |
| A11 | Phase theme shift: regulator-rich early (6.7%) → envelope-structural late (10.2% OM, 12.2% TBDT) | REPORT.md §Finding 3; NB 03 cell 6 | `partial` | L#6: Fisher p=0.243 — suggestive but not statistically discriminated |
| A12 | CtpA (CCNA_03113) +0.58 transcript, pvalue=0.048, FDR=0.109; protein not detected — REJECTED | REPORT.md §Finding 4 table; NB 04_sphingolipid_lpt_panel.ipynb cell 5 | `preliminary` | L#1: REJECTED at pre-registered bar; LpxF-substitute hypothesis (Zik 2022) untested |
| A13 | Sphingolipid biosynthesis constitutive: 0/6 UP; *spt* −0.64 FDR 0.002; *sphk* −0.40 FDR 0.02 | REPORT.md §Finding 4 table; NB 04 cell 3 | `direct` | (all six genes tested; none UP) |
| A14 | Canonical Lpt maintained at transcript: MsbA-like CCNA_00307 +0.89 FDR 0.01; LptC-related CCNA_03716 +0.56 FDR 0.005 | REPORT.md §Finding 4 table; NB 04 cell 3 | `direct` | (transcript upregulation significant; consistent with Uchendu 2026) |
| A15 | Lpt protein discordance: LptD log2(4672/4659)=−0.47; LptE=−0.78 (decline) | REPORT.md §Finding 4 protein table; NB 04 cell 6 | `partial` | L#2: single-replicate OM proteome; direction contradicts transcript; notable finding pending replication |
| A16 | *lptC2* (CCNA_01226) pilot: transcript −0.60 FDR 0.034; protein +1.08 vs intermediate, +0.66 vs WT | REPORT.md §Finding 4 pilot; NB 04 cells 3,6 | `preliminary` | L#2: single replicate; partial recovery of prior −0.42; labeled "suggestive pilot requiring replication" |
| A17 | CCNA_01217 protein log2 +0.77 (vs intermediate), +0.74 (vs WT) | REPORT.md §Finding 4; NB 04 cell 6 | `preliminary` | L#2: single-replicate OM proteome; direction-only |
| A18 | PG remodeling: 28 unique loci meet H4 threshold (≥3 required; 25 transcript + 6 protein) | REPORT.md §Finding 5; NB 05_pg_remodeling.ipynb cell 5 | `direct` | (well above threshold; gene set locked pre-DE) |
| A19 | PG direction: 20 DOWN (FtsI, PbpZ/C, MurD, endopeptidases) + specific inductions (SdpA +4.8 protein; Pal +2.08 transcript/+2.84 protein) | REPORT.md §Finding 5; NB 05 cells 5,8 | `partial` | L#2: protein-level inductions single-replicate; L#11: 2 regex false positives (CCNA_00565, CCNA_01833) flagged |
| A20 | Pal-Tol mechanistic interpretation (retrograde PL transport per Tan & Chng 2025) | REPORT.md §Interpretation §8; NB 03/NB 05 convergence | `partial` | L#5: interpretation grounded in external 2025 paper, not project data alone |
| A21 | Sphingolipid pathway Caulobacter-unique: NCBI *spt* (7,0,0,0); *cerR* (6,0,0,0) | REPORT.md §Finding 6; NB 06b_ncbi_annotation_presence.ipynb cell 3 | `direct` | (NCBI confirms PaperBLAST screen; Olea-Ozuna 2020/2024 independent support) |
| A22 | ChvG-ChvI alphaproteobacterial-restricted: NCBI ChvG (5,0,0,0); ChvI (6,0,0,0) | REPORT.md §Finding 6; NB 06b cell 3 | `direct` | (consistent with Greenwich 2023) |
| A23 | Comparator alternative routes: A.b. PBP1A/Ldt (Kang 2021); N.m. capsule (Steeghs 2001); M.c. late-acyltransferase (Gao 2008) | REPORT.md §Finding 6; NB 06_comparative_species.ipynb cell 3 | `partial` | L#8: M. catarrhalis under-annotated in PaperBLAST (162 genes); gene-presence↔route link inferred from literature |
| A24 | PaperBLAST ~80% false-negative diagnosis for Caulobacter lipid A genes (LpxA/C/D/B/K 0 in PB, 11–18 in NCBI) | REPORT.md §NB06b table; NB 06b cell 3 | `direct` | L#7: methodological; headline claim unaffected (depends on comparator absences, where NCBI confirms) |
| A25 | NB00 orientation panel (sphingolipid/Lpt CPM, ChvI overlap, Zik suppressors, top DEGs, OM proteome shifts) | REPORT.md §"Phase A"; NB 00_orientation.ipynb | `direct` | (motivated the plan; descriptive scoping, not a standalone claim) |
| A26 | 4-panel synthesis master figure + hypothesis scorecard | REPORT.md §Key Findings figure; NB 07_synthesis.ipynb | `direct` | (synthesis artifact; recommended Figure 1) |

**Notes column rule applied:** Limitations numbered from REPORT.md lines 245–256 in document
order — L#1 CtpA rejected; L#2 single-replicate OM proteome; L#3 Path B background
equivalence / threshold miscalibration; L#4 single growth condition (PYE); L#5 Pal
interpretation depends on Tan & Chng 2025; L#6 SigU literature gap; L#7 NB06 PaperBLAST
~80% FN; L#8 M. catarrhalis under-annotated; L#9 iron-limitation experiments absent;
L#10 NB03 cohort double-counting (corrected); L#11 NB05 regex false positives.
12 of 26 analyses (46%) land at `partial`/`preliminary` — consistent with the substantive
Limitations section (anti-PA-6 satisfied).

## Throughline candidate seeds (input to throughline agent)

Three seeds at one-sentence depth. The throughline agent expands these into full evidence
maps and surfaces them to the user. **Not picked here.** Note: a paper-draft throughline
already exists (`papers/draft_1/00_throughline.md`, TL1 selected + user-revised) — the
throughline agent should treat it as the strong reuse default per D-009 (see Pipeline state).

- **TL1 (sphingolipid-centered, matches paper reuse):** Δ*fur*-permitted lipid A loss in
  *Caulobacter* is sustained by a *constitutive* anionic-sphingolipid pool with repurposed
  Lpt machinery — a route structurally unavailable to other lipid-A-loss-tolerant
  Gram-negatives — with Fur-released transport and two-phase ChvI signaling as supporting
  context, each stated at its actual evidence level.
- **TL2 (five-layer mechanism architecture):** A single envelope catastrophe (lipid A loss)
  triggers five partially independent adaptive layers — Fur-released transport, ChvI
  two-phase signaling, constitutive sphingolipid substitution, peptidoglycan remodeling,
  and cross-species structural unavailability — that together explain how and why
  *Caulobacter* alone tolerates the deletion.
- **TL3 (evidence-honesty / how-we-know):** Reconstructing the Δ*lpxc* rescue mechanism is
  a case study in calibrated inference — pre-registered thresholds, a rejected hypothesis
  (CtpA), transcript-protein discordance, and a recalibrated enrichment test show what
  STRONG evidence does and does not license about a multi-layer mechanism.

## Pipeline state

- **paper-writer reuse available:** `yes` — `papers/draft_1/` exists with a selected,
  user-revised throughline (`00_throughline.md`: TL1, revised 2026-06-04) plus full
  evidence map, weakness inventory, and exclusion list. Per D-009, reuse defaults ON;
  the throughline agent should offer the existing throughline as the primary option and
  adapt it to talk format (TL1/TL2/TL3 seeds above mirror the paper's candidate set).
- **atlas runtime data:** `not consumed` (per D-010 — algorithmic borrow only).
- **Cross-tenant integration slide:** required (SPEC §7). Data sources are
  `kescience_fitnessbrowser` and `kescience_paperblast` (+ user-supplied RNA-seq/proteome
  and NCBI annotation) — surface BERDL cross-collection provenance.
- **AI image generation:** `--ai-diagrams off` (default; not passed in this invocation's flags).

## Gap-fill (optional)

REPORT.md is complete (9 findings, scorecard, 11-item Limitations, data/notebook/figure
inventories). No gap-fill request filed; this plan ran with a fully populated REPORT.

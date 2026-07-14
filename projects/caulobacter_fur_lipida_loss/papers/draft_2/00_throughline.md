# Throughline

**Selected:** TL1 (carried verbatim from plan.v1 candidate; no user revision applied).

**Statement:** A coordinated multi-layer envelope-remodeling program enables Δ*fur*-permitted lipid A loss in *Caulobacter crescentus* — Fur-derepressed transport, ChvI two-phase engagement, constitutive sphingolipid substitution, and peptidoglycan reorganization — each layer reported at its actual evidence level.

_This is REPORT.md's own integrative framing: the comprehensive "mechanism atlas" that presents all five mechanistic layers (Mechanistic Synthesis §1–9) with their honest evidence gradings (SUPPORTED / HYPOTHESIS / PARTIAL / MIXED / PILOT)._

**Evidence map:**

| Sub-claim | Source | Strength |
|---|---|---|
| Δ*fur* derepression is a major driver of the 4584-vs-4580 signal (Spearman ρ = 0.315, p = 2.08e-03 over 93 Leaden Δ*fur* DEGs, 71% sign concordance) | notebook 01_leaden2018_fur_signature.ipynb cell 5; REPORT.md §"Finding 1" | ✓ direct |
| A specific Fur-released subset (Path A, 32 genes) is enriched for envelope-stress fitness phenotypes (17/32 = 53.1% vs 33.25% background, fold 1.60×, p=0.016) | notebook 02b_h2_hypergeometric_verdict.ipynb cell 2; REPORT.md §"Finding 2" | ⚠ partial — enrichment is *marginal* (1.60×, p=0.016) above a 33.25% background; REPORT labels it "marginally enriched" |
| The SspB-buffered respiratory arm (Path B) is mechanistically critical to the rescue ("dual-release switch") | notebook 02b_h2_hypergeometric_verdict.ipynb cell 2; REPORT.md §"Finding 2" | ✗ contradicts — Path B 9/26 = 34.6%, fold 1.04×, p=0.515, indistinguishable from background; REPORT demotes the SspB arm to hypothesis |
| ChvI envelope-stress regulon engages in two phases (unique-early=20, both-phase=10, late=49), with ChvI autoregulation (CCNA_00237 +1.45) | notebook 03_chvi_phase_partition_sigU.ipynb cell 7; REPORT.md §"Finding 3" | ✓ direct |
| SigU drives the late ChvI cohort | notebook 03_chvi_phase_partition_sigU.ipynb cell 10; REPORT.md §"Finding 3" | ✗ contradicts — late-cohort coherence 24.5% (below 50% relaxed bar), Fisher p=0.243; SigU is uncharacterized in the literature so the test cannot be validated |
| Sphingolipid biosynthesis is constitutive, not induced (0/6 biosynthesis genes UP; *spt* −0.64 FDR 0.002, *sphk* −0.40 FDR 0.02) | notebook 04_sphingolipid_lpt_panel.ipynb cell 4; REPORT.md §"Finding 4" | ✓ direct |
| CtpA (CCNA_03113) provides the LpxF-equivalent processing step (Zik 2022 prediction) | notebook 04_sphingolipid_lpt_panel.ipynb cell 5; REPORT.md §"Finding 4" | ✗ contradicts — logFC +0.58, pvalue=0.048, FDR=0.109, protein not detected; REJECTED at the pre-registered bar |
| The canonical Lpt apparatus is repurposed for sphingolipid transport (Uchendu 2026 shared-component model) | notebook 04_sphingolipid_lpt_panel.ipynb cells 4 & 6; REPORT.md §"Finding 4" | ⚠ partial — transcript UP (MsbA-like +0.89 FDR 0.01, LptC-related +0.56 FDR 0.005) but the two Lpt proteins detected, LptD (−0.47) and LptE (−0.78), DECLINE; single-replicate proteome |
| PG remodeling participates: specific lytic engagement (SdpA +4.8 log2 protein, Pal +2.08/+2.84) on a backdrop of broad basal shutdown (28 loci, 20 DOWN) | notebook 05_pg_remodeling.ipynb cell 5; REPORT.md §"Finding 5" | ✓ direct |
| The sphingolipid pathway and ChvG-ChvI are *Caulobacter*-unique, explaining species specificity (NCBI pattern 1000 for *spt*, *cerR*, ChvG, ChvI) | notebook 06b_ncbi_annotation_presence.ipynb cell 5; REPORT.md §"Finding 6" | ✓ direct |

**Weakness inventory:**

- Gap: the candidate is a "kitchen-sink" integration that bundles three SUPPORTED layers (Fur derepression, constitutive sphingolipid, PG remodeling), two negatives/demotions (SspB arm, CtpA), one PARTIAL (Lpt repurposing), and one PILOT (lptC2). A single narrative arc that claims all five layers cohere is harder to defend than its strongest component, because the weakest layer drags the headline.
- Rebuttal a sharp reviewer would offer: "Your title says 'coordinated program' but two of your named layers (the SspB respiratory arm, CtpA processing) are explicitly not supported by your own data, and a third (Lpt repurposing) has transcript-protein discordance. What exactly is 'coordinated'?" The integrative claim risks reading as over-assembly of a story from heterogeneous evidence.
- Methodological caveat: the OM proteome is single-replicate per strain (no per-protein statistics; only direction interpretable), and the entire transcriptome is from a single growth condition (PYE rich medium) — the Fur signal is constitutive Δ*fur* derepression, not a real iron-limitation response. The breadth of the claim amplifies exposure to both caveats.

**What this paper would NOT include if this is chosen:**

- The pre-registered threshold-miscalibration methodological lesson (≥10% threshold sits below a 33.25% background) — orthogonal to the biology; → Discussion aside or appendix.
- The cross-species engineering predictions (sphingolipid-engineered *A. baumannii*, Tol-Pal retrograde-transport assay) — out of scope; → next-paper / Future Directions only.
- Detailed Leaden iron-vs-Δ*fur* internal validation and the cbb3/*fix* operon gene-by-gene listing — supporting detail; → appendix.
- The CCNA_01217 single-replicate protein increase — pilot-grade; → appendix with the lptC2 pilot.

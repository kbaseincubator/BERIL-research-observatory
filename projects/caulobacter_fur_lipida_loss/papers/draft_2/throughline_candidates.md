# Throughline Candidates

## Triage

**Tier:** STRONG
**Recommended mode:** paper
**Rationale:** REPORT.md has a refined research question, six numbered findings with effect sizes + FDR-corrected p-values + hypergeometric enrichment tests against an explicit genome background, a pre-registered hypothesis scorecard (H1–H4), a substantive multi-item Limitations section, and an audit trail showing the project already survived an adversarial-review pass (CtpA demoted to REJECTED, Path B demoted to hypothesis, Pal interpretation re-grounded in Tan & Chng 2025) — methods are reproducible from REPORT + 10 notebooks.

---

## Candidate TL1: A coordinated multi-layer envelope-remodeling program enables Δ*fur*-permitted lipid A loss in *Caulobacter crescentus* — Fur-derepressed transport, ChvI two-phase engagement, constitutive sphingolipid substitution, and peptidoglycan reorganization — each layer reported at its actual evidence level.

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

---

## Candidate TL2: The Δ*lpxc* rescue runs on a pre-existing sphingolipid pool and a repurposed LPS-transport apparatus, not on new biosynthesis — providing the first in-strain regulatory and proteomic evidence for the Uchendu 2026 shared-component model, and explaining why only *Caulobacter* can take this route.

_The highest-novelty single-mechanism story: extends Zik 2022 (rescue requires anionic sphingolipid) and Uchendu 2026 (sphingolipid transporters share the canonical LptB ATPase) by showing, in an actual Δ*lpxc* strain, that biosynthesis is constitutive and the canonical Lpt machinery is transcriptionally redirected — with the comparative arm (Finding 6) supplying the "why Caulobacter only" payoff._

**Evidence map:**

| Sub-claim | Source | Strength |
|---|---|---|
| Sphingolipid biosynthesis is NOT transcriptionally induced in the rescue — the constitutive pool suffices (0/6 biosynthesis genes UP; *spt* −0.64 FDR 0.002, *sphk* −0.40 FDR 0.02) | notebook 04_sphingolipid_lpt_panel.ipynb cell 4; REPORT.md §"Finding 4" / §"Novel Contribution 3" | ✓ direct |
| The canonical Lpt apparatus is maintained/upregulated at the transcript level (MsbA-like CCNA_00307 +0.89 FDR 0.01; LptC-related CCNA_03716 +0.56 FDR 0.005; 0 components DOWN) | notebook 04_sphingolipid_lpt_panel.ipynb cell 4; REPORT.md §"Finding 4" | ✓ direct |
| The canonical Lpt apparatus is functionally repurposed for sphingolipid trafficking (the mechanistic claim, per Uchendu 2026) | notebook 04_sphingolipid_lpt_panel.ipynb cell 6; REPORT.md §"Finding 4" / Mechanistic Synthesis §5 | ⚠ partial — the only two Lpt proteins detected, LptD (log2 4672/4659 = −0.47) and LptE (−0.78), DECLINE at protein level; transcript-protein discordance unresolved by single-replicate proteome |
| Sphingolipid-specific transporter lptC2 (CCNA_01226) accumulates post-transcriptionally (protein up despite transcript down) | notebook 04_sphingolipid_lpt_panel.ipynb cells 4 & 6; REPORT.md §"Finding 4" | ⚠ partial — transcript −0.60 FDR 0.034; protein +1.08 vs intermediate but only +0.66 vs WT baseline (was already −0.42 in intermediate); single-replicate PILOT requiring replication |
| The Fur-derepressed OM transport machinery is plausibly available to assist sphingolipid trafficking in the rescued state | notebook 02b_h2_hypergeometric_verdict.ipynb cell 2; REPORT.md Mechanistic Synthesis §1 | ◇ orthogonal — Path A enrichment (1.60×, p=0.016) is for *envelope-stress* phenotypes; the sphingolipid-trafficking participation is an inference, not demonstrated |
| Only *Caulobacter* encodes the sphingolipid biosynthesis pathway (and ChvG-ChvI) among the four lipid-A-loss-tolerant species — structural unavailability explains species specificity (NCBI pattern 1000 for *spt*, *cerR*, ChvG, ChvI) | notebook 06b_ncbi_annotation_presence.ipynb cell 5; REPORT.md §"Finding 6" | ✓ direct |
| CtpA supplies the LpxF-equivalent head-group processing step (Zik 2022) | notebook 04_sphingolipid_lpt_panel.ipynb cell 5; REPORT.md §"Finding 4" | ✗ contradicts — REJECTED at pre-registered bar (pvalue=0.048, FDR=0.109, protein not detected); the processing-step half of the substitution model is untested |

**Weakness inventory:**

- Gap: the most novel and exciting elements of this story — Lpt repurposing and the lptC2 post-transcriptional accumulation — rest on a single-replicate OM proteome and carry a transcript-protein discordance (LptD/LptE proteins go DOWN while transcripts go UP). The headline "repurposed apparatus" is supported at the transcript level but contested at the protein level. The replicated proteomics that would resolve this are not scheduled until summer 2026.
- Rebuttal a sharp reviewer would offer: "You claim the canonical Lpt machinery is repurposed, but the only Lpt proteins you actually measured both decline. Isn't a substrate-limitation interpretation (no LPS → less canonical-Lpt cargo → lower Lpt protein) equally or more parsimonious than 'repurposing'?" The candidate must foreground that the protein-level data are equivocal.
- Methodological caveat: the central mechanistic claim leans on Uchendu 2026 (a 2026 bioRxiv preprint, not yet peer-reviewed) for the shared-component model, and on single-condition transcriptomics. The CtpA processing step — the other half of the Zik 2022 substitution model — is REJECTED, so the substitution mechanism is established for transport-availability but not for head-group processing.

**What this paper would NOT include if this is chosen:**

- The H2 Fur-regulon fitness ranking and the Path A / Path B dual-release-switch dissection — adjacent but not core to the sphingolipid/Lpt mechanism; → brief mention + appendix.
- The PG-remodeling / SdpA / Pal-Tol arm (Finding 5) and its Tan & Chng 2025 reinterpretation — a parallel envelope-remodeling layer; → appendix or a single integrative paragraph.
- The ChvI two-phase partition detail (Finding 3) — context for envelope-stress signaling; → brief mention.
- The threshold-calibration methodological lesson — out of scope; → omit.

---

## Candidate TL3: Not all of the Fur regulon matters — RB-TnSeq fitness data show that only a specific Fur-released transport subset is enriched for envelope-stress phenotypes, while the SspB-buffered respiratory arm is indistinguishable from background, collapsing the "dual-release switch" to a single supported arm.

_The most rigorous, adversarially-hardened, methods-forward story. Centers on the H2 recalibration (hypergeometric enrichment against a measured genome background) plus the ChvI two-phase corroboration, and carries the generalizable methodological lesson about calibrating fitness-phenotype thresholds to background. Headline includes a defensible negative result._

**Evidence map:**

| Sub-claim | Source | Strength |
|---|---|---|
| Δ*fur* derepression is a major, reproducible component of the combined Δ*fur* Δ*sspB* signal (Spearman ρ = 0.315, p = 2.08e-03 vs Leaden 2018, 71% sign concordance) | notebook 01_leaden2018_fur_signature.ipynb cell 5; REPORT.md §"Finding 1" | ✓ direct |
| The genome-background phenotype-bearing rate must be the comparator, and it is high (33.25%; n=3943, K=1311 at \|fitness t\|>4 in ≥2 envelope-stress experiments) — the pre-registered ≥10% threshold is below background and uninformative | notebook 02_caulo_fitness_ranking.ipynb cell 9; REPORT.md §"Finding 2" / §"NB02" | ✓ direct |
| Only the Path A subset (clean Fur signature: TBDTs + iron-uptake) is enriched for envelope-stress phenotypes (17/32 = 53.1%, fold 1.60×, p=0.016), led by ChvT CCNA_03108 \|t\|=43.7 | notebook 02b_h2_hypergeometric_verdict.ipynb cell 2; REPORT.md §"Finding 2" | ⚠ partial — enrichment is statistically real but *marginal* (1.60×); a single fold-1.6 result above a noisy background is suggestive rather than decisive |
| The SspB-buffered respiratory arm (Path B, cbb3/*cyd*/*fix*) is NOT enriched — the "respiratory ATP required" arm of the dual-release switch is unsupported (9/26 = 34.6%, fold 1.04×, p=0.515) | notebook 02b_h2_hypergeometric_verdict.ipynb cell 2; REPORT.md §"Finding 2" / Mechanistic Synthesis §2 | ✓ direct — supported *negative*: Path B is statistically indistinguishable from background |
| The SspB co-deletion nonetheless buffers a real transcript-level program (53 of 93 Leaden Δ*fur* DEGs blunted, dominated by the cbb3/*fix*-NOPQ operon CCNA_01466–01476) | notebook 01_leaden2018_fur_signature.ipynb cell 5; REPORT.md §"Finding 1" / §"Novel Contribution 1" | ✓ direct — the transcript-level buffering is established; only its *mechanistic criticality* is not |
| The ChvI envelope-stress regulon engages in two phases (20/10/49 disjoint partition; ChvI autoregulation +1.45), corroborating staged envelope-stress signaling | notebook 03_chvi_phase_partition_sigU.ipynb cell 7; REPORT.md §"Finding 3" | ✓ direct |
| The "regulator-early → structural-late" theme shift within the ChvI cohorts is a discrete, ordered program | notebook 03_chvi_phase_partition_sigU.ipynb cell 10; REPORT.md §"NB03" | ⚠ partial — direction is suggestive but the Fisher test of the shift is not significant (p=0.243) |
| The iron-limitation arm of H2 can be tested with this compendium | notebook 02_caulo_fitness_ranking.ipynb cell 5; REPORT.md §"Finding 2" / Limitations | ✗ contradicts — zero iron-limitation experiments in the 198-experiment Caulobacter compendium; H2 was descoped to envelope-axis-only |
| Methodological lesson: pre-registered fitness-phenotype thresholds must be calibrated to the genome-wide background, not a fixed percentage | notebook 02b_h2_hypergeometric_verdict.ipynb cell 2; REPORT.md §"Novel Contribution 7" | ✓ direct |

**Weakness inventory:**

- Gap: the headline is partly a recalibration / negative result ("the SspB arm doesn't matter; the threshold was miscalibrated"). This is scientifically honest and defensible, but it is a narrower and less mechanistically satisfying contribution than the sphingolipid biology — it answers "which Fur genes matter" and "what the fitness data can and can't say," not "how the cell survives without LPS."
- Rebuttal a sharp reviewer would offer: "Your one positive result is a fold-1.60×, p=0.016 enrichment of a 32-gene set above a 33% background — and you used envelope stress as a proxy because the iron-limitation experiments you actually wanted don't exist. How much weight can a marginal enrichment under a proxy condition carry?" The candidate must own the marginality and the descoping.
- Methodological caveat: the FB envelope-stress condition class (22 experiments) is a proxy for the in-vivo Δ*lpxc* envelope perturbation, not a direct assay of it; and the central comparison rests on a single fitness compendium with no iron-limitation arm. The supported negative (Path B) is robust precisely because it is a null against a measured background, but the supported positive (Path A) is marginal.

**What this paper would NOT include if this is chosen:**

- The sphingolipid-substitution and Lpt-repurposing molecular detail (Finding 4: constitutive biosynthesis, MsbA-like/LptC-related upregulation, lptC2 pilot) — the cell-biology payoff; → brief mention + appendix, since this story is regulatory/fitness-centered.
- The PG-remodeling and Pal-Tol arm (Finding 5) with the Tan & Chng 2025 reinterpretation — → appendix.
- The comparative species-specificity arm (Finding 6) — relevant context but not load-bearing for a "which Fur genes matter" story; → brief mention.
- The CtpA REJECTED result and the lptC2 pilot — → appendix / Future Directions.

---

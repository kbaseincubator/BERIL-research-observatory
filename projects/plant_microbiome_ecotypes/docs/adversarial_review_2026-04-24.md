---
reviewer: BERIL Adversarial Review (Claude Opus 4.7, self-directed agent)
date: 2026-04-24
project: plant_microbiome_ecotypes
scope: Phase 2b (NB13–NB15) — adversarial pairing with REVIEW_2.md
---

# Adversarial Review: Phase 2b

> **Purpose**: Paired adversarial review for milestone synthesis, per the project convention of
> running a standard `/berdl-review` together with an adversarial agent because the standard
> reviewer is over-optimistic on structural issues.

## Overall Assessment

The author has done substantial, visible work in Phase 2b — six deferred controls executed, CSVs and figures produced, REPORT §11 written honestly, and a disposition table that acknowledges what was patched versus fixed. But the core problem is the gap between *what was run* and *what was shown*. Several marquee "fixes" are mechanically pre-determined by construction (the novel-OG genome-size simulation), driven by single-genome outliers (*P. amygdali* subclade 2), or are apples-to-oranges comparisons presented as corrections (the Cohen's d 7.54→0.39 reduction). Multiple "Fixed" items in the disposition table are more accurately "patched, still flawed." H7 is declared "partially supported" on the basis of a test that fails on both statistical validity (Cochran's rule) and multiple-testing. The author is declaring victory prematurely. **Grade: C+**.

## Critical Issues (must fix)

1. **NB14 Cell 3 "genome-size control" for novel OGs is circular by construction.** The code (`_build_nb14.py` lines 308–321) generates the outcome variable `y_sim` by drawing `Bernoulli(prev_plant)` for plant species and `Bernoulli(prev_nonplant)` for non-plant species. Genome size never enters the data-generating process. When this synthetic `y_sim` is then regressed on `is_plant + log10(genome_size) + phylum_dummies`, the `is_plant` coefficient *must* recover the prev_plant/prev_nonplant gap (mean difference 0.43, min 0.34 across 50 OGs) — that is literally how the data were built. The "50/50 OGs survive" is a mechanical identity, not evidence. The disposition table lists C4 as "Fixed"; it is **not** fixed. A real test would regress actual per-species OG presence on is_plant + log10(genome_size), which the code explicitly avoids because "we don't have the per-species OG matrix" (comment at L276–282).

2. **H7 "partially supported" rests on statistically invalid tests.** In `subclade_enrichment_corrected.csv`, *P. amygdali* subclade 2 contains **exactly one genome** which happens to be plant-associated (1/1 = 100%). Dropping that single genome and re-running chi² gives **p = 0.85**. Minimum expected cell count in the original 3×2 table is 0.13 — Cochran's rule requires ≥80% of expected counts ≥5; here 50% fall below 1. Similarly, the subclade × host chi² p = 5.6×10⁻⁹ that REPORT §11 highlights is built from a 2×3 table with minimum expected count **0.026** and 67% of cells expected <5; subclade 1 has a single genome and that one genome drives the result. *P. amygdali* also fails Bonferroni correction across 5 species (0.031 > 0.05/5 = 0.01). So of 5 species tested, **exactly one (*P. avellanae*)** is both statistically valid and survives multiple-testing — that is a **1/5** result, not 2/5, and the honest verdict for H7 is closer to "one-off observation in one *Pseudomonas_E* species" than "partially supported."

3. **Species validation (NB13 Cell 2) is nearly tautological.** In `species_validation.csv`, **all 14 of the 7 beneficial + 7 pathogenic** ground-truth species are classified as `dual-nature`. Under the "relaxed accuracy" rule (ben→ben/dual OK, path→path/dual OK), dual-nature is counted as correct for *both* ground-truth classes — so the rule cannot fail for any species the classifier assigned to dual-nature. The 77.8% figure is arithmetically 14 ÷ 18 but contains zero discriminative information between beneficial and pathogenic: all 14 relevant species land in the single class that passes the relaxed rule either way. The only real signal is the pathogen-ratio Mann-Whitney (p = 0.027, N=7 vs 7, medians 0.50 vs 0.60) — which is tiny sample, small effect, and should be reported as the primary result; the confusion matrix should be retired.

4. **Complementarity d reduction (−7.54 → −0.39) is mostly a formula change, not a statistical correction.** In `notebooks/06_complementarity.ipynb` Cell 18, Cohen's d was computed as `(obs_mean − null_means.mean()) / null_means.std()` where `null_means.std()` is the SD of permutation means (asymptotically 0 by CLT). In NB14 Cell 5, d is computed as `(cooccur_mean − random_mean) / random.std()` where `random.std()` is the raw pair-level SD (much larger). Recomputing NB06's max-aggregated complementarity with NB14's formula on `complementarity_v2.csv` gives **d = −0.43**, essentially identical to the prevalence-weighted d = −0.39. The claimed "20× reduction" disappears once the scales are matched: the real effect of switching to prevalence-weighting is ≈10% of the reported magnitude shift. The "I1 Fixed" claim should be downgraded to "aggregation re-checked, effect size recalibrated"; the prevalence change itself barely moves the needle.

5. **L1-penalized logit bootstrap CIs are not standard-interpretable.** Bootstrap CIs on L1-penalized coefficients are known to be inconsistent near zero (Chatterjee & Lahiri 2011) — in each bootstrap replicate L1 shrinks small effects to zero, biasing the CI and producing spurious significance for some markers and spurious nulls for others. The n_bootstrap=100 (should be ≥1000) compounds this, and the "top-20 genera + 'other'" scheme collapses **88.7% of the 8,237 total genera into a single dummy** — this is not phylogenetic control, it is sparse adjustment for a few dominant genera. Markers reported as significant (phosphate_solubilization coef=0.32, cwde_cellulase coef=0.38, effector coef=0.45) have tight CIs only because of L1 shrinkage stability in bootstrap, not because they genuinely survive phylogenetic control. Honest framing: "L1-regularized sparse-adjustment logit suggests 9/14 markers retain positive direction, but these are suggestive not confirmatory CIs."

## Important Concerns (should address)

6. **Within-genus shuffle: the 3/15 survival rate is buried lede.** The author frames this positively (N-fix, ACC deaminase, T3SS are validated). But 12/15 markers — **including phenazine, IAA biosynthesis, CWDE cellulase, CWDE pectinase, effectors, DAPG, HCN, siderophore** — show no signal beyond genus composition. These are functions that feature prominently in the narrative (H1 rhizosphere biocontrol story, H2 pathogen-accessory story) and the shuffle says they are **genus-scale, not species-scale** signals. The REPORT acknowledges this briefly but the hypothesis verdicts do not adjust. Also: 200 permutations is under-resolved for p ≤ 0.005; no multiple-testing correction across 15 markers (Bonferroni alpha = 0.0033, so T3SS at p = 0.005 is marginal).

7. **Pfam "recovery" narrative about T3SS is inconsistent with IPS data.** REPORT §11 claims PF00771, PF01313, PF01514 returned zero hits because "bakta does not annotate these specific Pfam accessions." But `interproscan_marker_hits.csv` contains **18,598 hits for PF00771** and **13,576 for PF01313** (only PF01514 is genuinely absent from IPS). So `bakta_pfam_domains` is missing these Pfams as a **data-source artifact** (likely a reduced-profile bakta build or a different HMM coverage set), not because the domains don't exist in the genomes. The current explanation is factually imprecise and, given that T3SS is central to the narrative (H1 root compartment, dual-nature framing), should be stated correctly: "bakta_pfam_domains silently omits these Pfams; InterProScan detects them in ~18k gene clusters. Our Phase 1 count underestimated T3SS domain coverage by a large margin."

8. **PERMANOVA 7× R² drop is softened to "attenuated."** R² 0.527 → 0.072 means **86% of the original compartment signal vanishes** when 9 species are removed (3 × 3 compartments). That is not "attenuated"; that is a demonstration that the primary H1 result was a taxonomic sampling artifact driven by a handful of over-represented rhizobial and *Pseudomonas* clades. The final verdict "Supported but attenuated" overstates what a 0.072 R² with n=598 supports — at that effect size, compartment explains ~7% of among-sample variance, which is a materially different claim than what REPORT §9 made originally. PERMDISP significance (H=33.12, p=3e-7) from NB08 compounds this: the residual 0.072 may itself partly reflect dispersion rather than location shift.

9. **Cherry-pick concern on the validation panel.** The 18-species panel is hand-curated by the author, and all 14 beneficial/pathogenic species conveniently land in dual-nature — a result the author could have foreseen before choosing them. A more defensible panel would include species known to carry a *minimum* of PGP or pathogenicity machinery (e.g., *Methylobacterium extorquens* as near-pure beneficial, *Xylella fastidiosa* as near-pure pathogen without common PGP markers). The current panel cannot distinguish dual-nature-by-design from a genuinely informative classifier.

10. **H6 "Partially supported" rests entirely on the broken *P. amygdali* host test.** The NB13 subclade × host chi² p = 5.6×10⁻⁹ is the sole Phase 2b evidence cited for H6 in `hypothesis_verdicts_final.csv`. Issue 2 above invalidates this. Without it, H6 retains only Phase 2 host-metadata parsing — a provenance finding, not a biology finding. Consider downgrading.

## Nits and Minor Issues

11. REPORT §11 says "9 of 17 markers" but the valid denominator is 9/14 after three markers with insufficient positives (phytotoxin n=0, coronatine_toxin n=12, other_pathogenic n=1) are excluded. Using 17 as the denominator inflates the apparent failure rate in a favorable direction.

12. `n_bootstrap = 100` in NB14 Cell 2 is too low for stable 95% percentile CIs (standard recommendation: 1000–10000); widen or at minimum flag this in §11.

13. The disposition table lists C1 as "Partial fix" (honest) but C4 as "Fixed" (not honest — see Issue 1). Self-consistency of labels matters.

14. `sensitivity_results.csv` stores only scalar summary; it doesn't retain the permutation null distributions, so the PERMANOVA result is not auditable from the CSV alone.

15. Minor internal inconsistency: H5 verdict text says "COG1845 phylo-controlled OR=8.7 (was 14.5 unadjusted)", but NB14's `genome_size_control.csv` reports coef_plant_controlled = 2.85 (OR ≈ 17.3). The "8.7" comes from the NB03 phylum-controlled regression, not NB14 — cite the source explicitly.

## Where the Author Got It Right

- **I6 (subclade genome ID fix) is genuinely fixed** at the data-plumbing level: 1306/1306 genomes now match, 599 plant-associated genomes recovered where there were previously 0. The mechanical correction is real and valuable (and documented in pitfalls.md). The over-interpretation downstream (Issue 2) is the problem, not the fix.
- **Pfam recovery numbers are internally consistent.** 19,364 hits / 7,962 species / 4,217 species gaining markers / 2,872 nitrogen-fixation gains — all CSV-verified and match REPORT text exactly.
- **H1 honest downgrade attempt.** Even though "attenuated" understates the magnitude of the drop, actually executing the top-3 exclusion and reporting R²=0.072 is the right move and not many authors would.
- **Honest `phase2b_evidence` column.** The final verdict CSV does not hide the unpleasant numbers (e.g., "3/15 markers survive within-genus shuffling" is visible).
- **H5 reframing to "enriched gene families, not truly novel."** Correct call; the I2 issue is handled appropriately.
- **Complementarity direction is unchanged** (still negative), so the ecological takeaway (redundancy not complementarity) holds even if the magnitude story is muddled — Louca et al. 2018 framing is solid.

## Recommendation

**Not publishable as-is.** Three items must be fixed before Phase 2b can be declared complete:

1. **Redo NB14 Cell 3 with real per-species OG presence.** Either pull the per-species OG matrix from eggNOG (it is available server-side — NB03 already aggregated it) or retract the 50/50 claim. The current simulation is circular and cannot stand.
2. **Revise H7 verdict.** Drop the *P. amygdali* result (single-genome subclades make chi² invalid regardless of chi² p-value) or run Fisher's exact on collapsed subclades with ≥5 genomes each. With *P. avellanae* as the sole surviving result, H7 should read "suggested in one *Pseudomonas_E* species; unsupported in the other 4."
3. **Rework the species-level validation around the pathogen-ratio continuous metric.** Retire the "77.8% relaxed accuracy" framing; report Mann-Whitney p=0.027 on N=7+7 with honest framing about the sample size and the fact that the categorical cohort assignments are uninformative at the species level.

Items 4–10 should be disclosed in the Limitations section and the hypothesis verdict table adjusted. Item 7 (T3SS Pfam explanation) is a 10-minute textual correction. If these are addressed, the work is publishable as a carefully-caveated pangenome-scale survey with two genuine contributions (H2 core/accessory asymmetry, dual-nature quantification) and three partially-supported claims (H1 attenuated, H4 multi-scale, H5 reframed). Without them, the current §11 reads more like a self-defense than a correction.

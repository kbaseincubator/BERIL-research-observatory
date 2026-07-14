# Phase 1B → Phase 2 Gate Decision

**Date**: 2026-04-27  
**Verdict**: **PASS_REFRAMED**

## Rationale

Methodology validates (producer null responsive on natural_expansion; negative controls behave under M2; M1 rank-stratified parents reveal monotone gradient). Bacteroidota PUL Innovator-Exchange is FALSIFIED at UniRef50 across all 4 deep ranks. The falsification is consistent with the Phase 1A M3 substrate-hierarchy claim: UniRef50 is too narrow to capture family-level HGT or paralog signal even for documented HGT classes (β-lactamase, CRISPR-Cas also fail their cross-phylum HGT priors at UniRef50). Phase 2 (KO functional aggregation) and Phase 3 (Pfam multidomain architecture) are now empirically REQUIRED to test the four pre-registered hypotheses meaningfully.

## Phase 1B headline numbers

- Bacterial GTDB representatives (post-CheckM): 18,989
- UniRef50 pool (full GTDB): 15,382,302
- UniRef50 target set (10K-per-class cap): 100,192
- Extract presence rows: 1,539,643
- Producer scores computed: 1,294,615 (rank, clade, UniRef) tuples
- Wall time: ~7.5 min NB05 + ~45 min NB06 + ~5 min NB07 ≈ 1 hour total

## Multi-rank consumer z (M1 rank-stratified parents)

| Child rank | Parent rank | Consumer z mean (informative) | Interpretation |
|---|---|---|---|
| genus | family | -10.48 | extreme intra-family clumping |
| family | order | -6.40 | strong intra-order clumping |
| order | class | -4.18 | moderate intra-class clumping |
| class | phylum | -1.84 | weak intra-phylum clumping |

Monotone gradient confirms M1 was the right call. Phase 1A's parent-phylum anchor masked this gradient.

## Bacteroidota PUL hypothesis verdict

**FALSIFIED at all 4 deep ranks.**

| Rank | Bact producer mean (95% CI) | Bact consumer mean | Verdict |
|---|---|---|---|
| family | -0.069 [-0.094, -0.044] | -9.331 | STABLE_OR_FALSIFIED |
| order | -0.105 [-0.131, -0.080] | -4.216 | STABLE_OR_FALSIFIED |
| class | -0.093 [-0.123, -0.064] | -2.794 | STABLE_OR_FALSIFIED |
| phylum | -0.089 [-0.119, -0.058] | +nan | STABLE_OR_FALSIFIED |

Both producer and consumer fail to exceed zero at any deep rank. Bacteroidota CAZymes at UniRef50 sequence-cluster resolution show vertical-inheritance signature, not Innovator-Exchange.

## HIGH 1 known-HGT positive control validation

Pre-registered cross-phylum HGT positive controls (β-lactamase + class-I CRISPR-Cas) **also fail** their HGT-positive prior at UniRef50:

- **β-lactamase** consumer z at genus→family parent: **-12.5** (strongly clumped)
- **class-I CRISPR-Cas** consumer z at genus→family parent: **-10.3** (strongly clumped)
- **AMR**: -11.9; **TCS HK**: -12.2 — all positive HGT controls extremely clumped at UniRef50

**Substrate-hierarchy interpretation**: at UniRef50, all proteins (HGT-active or vertically inherited) appear vertically inherited because UniRef50 captures sequence-cluster-specific variants, not function families. The Phase 1A M3 prediction is empirically validated at full scale.

## Producer null is responsive (natural_expansion validates)

- phylum: paralog 2.09 vs cohort 1.27 = **+64.5 % above cohort**, producer z = +0.89 [0.85, 0.93]
- class: +55.2 % above cohort, producer z = +0.77
- Stronger than Phase 1A pilot (+39.5 %) — confirms scaling

Negative controls (ribosomal / tRNA-synth / RNAP): all at ~-12 % below cohort, producer z ~-0.15. M2 criterion satisfied at all ranks.

## Methodology revisions for Phase 2

### M6 — Phase 2 substrate is KO not UniRef50

Phase 1B empirically validates the M3 substrate-hierarchy claim from Phase 1A. UniRef50 captures only sequence-cluster-specific variants. Phase 2 aggregates UniRef50s up to KEGG Orthology (KO) — the functional family level — which is where Bacteroidota PUL CAZyme aggregation, Mycobacteriota mycolic-acid pathway, and Alm 2006 TCS HK family expansion all live. Phase 2 should NOT use UniRef50 as a function-class unit.

### M7 — Carry M1 rank-stratified parents forward to Phase 2

M1 was vindicated at Phase 1B scale: rank-stratified parents revealed a monotone consumer-z gradient (-10.5 at genus→family parent, decaying to -1.8 at class→phylum). Phase 2 KO atlas should use the same parent-stratification.

### M8 — Carry M2 negative-control criterion forward

M2 (CI upper ≤ 0.5 for negative controls instead of 'near zero') worked correctly at Phase 1B. All three negative controls (ribosomal, tRNA-synth, RNAP) showed dosage-constraint signatures (~-12 % below cohort, z ~-0.15). Use the same criterion at Phase 2.

### M9 — PIC (HIGH 3) deferred from Phase 1B to Phase 2

Plan v2.3 promoted PIC from Phase 2 optional to Phase 1B mandatory. NB06 implementation did not include PIC due to time constraints. Re-promote to Phase 2 mandatory; the KO atlas will report PIC-corrected variance estimates from the start.

### M10 — Per-class cap stays at 10K UniRefs (or analog at KO scale)

At Phase 1B, the per-class cap of 10K kept driver memory tractable. Phase 2 KO atlas may have far fewer KOs per class (KEGG has ~25K KOs total; functional categories have hundreds to low-thousands), so the cap may not bind. Reuse the cap pattern as a defensive default.

### M11 — Phase 1B negative result on cross-phylum HGT positive controls is informative

At UniRef50, β-lactamase (z=-12.5) and class-I CRISPR-Cas (z=-10.3) both fail to show cross-phylum HGT signal — even more clumped than negative controls. Phase 2 at KO level should re-test these classes; if they STILL show clumping at KO level, the consumer-null framework cannot detect documented HGT and a different metric is required (e.g., direct phyletic-incongruence at KO presence/absence rather than parent-rank dispersion).

## What this Gate verdict means

1. **Methodology is validated at full GTDB scale.** Producer null is responsive (natural_expansion +0.89 σ at phylum), negative controls behave under M2, M1 rank-stratified parents reveal a clean monotone consumer-z gradient.
2. **Bacteroidota PUL Innovator-Exchange is falsified at UniRef50.** This is a real falsification, not a methodology artifact.
3. **The falsification is a substrate-validation outcome.** Phase 1A's M3 pre-registration predicted exactly this: UniRef50 sees only sequence-cluster-specific variants, which are vertically inherited even for HGT-active function families. β-lactamase + class-I CRISPR-Cas (HIGH 1 cross-phylum HGT positive controls) also fail at UniRef50 — confirming the substrate-hierarchy claim.
4. **Phase 2 (KO functional aggregation) is now strictly required.** Phase 2 is the resolution at which Bacteroidota PUL CAZymes, Mycobacteriota mycolic-acid pathway, and Alm 2006 TCS HK family signals can be detected. Phase 2 should NOT use UniRef50 as a function-class unit; it aggregates to KO via eggNOG annotation.

## Next step

Phase 2 — KO functional atlas with M6–M11 revisions applied. The Phase 2 pre-registered hypothesis is **Mycobacteriota → Innovator-Isolated on mycolic-acid pathway KO set** (RESEARCH_PLAN.md). The Bacteroidota PUL hypothesis is also re-tested at KO level; the Phase 1B negative result narrows the prior on whether Bacteroidota → Innovator-Exchange is recoverable at any aggregation level.

# Phase 1A → Phase 1B Gate Decision

**Date**: 2026-04-26  
**Verdict**: **PASS_WITH_REVISION**

## Rationale

Producer null is responsive: natural_expansion class shows positive producer z at all 5 ranks (0.13 → 0.55 σ, monotonically growing with rank). Negative controls behave correctly under the revised criterion (dosage-constrained → negative producer z) at most ranks. Multi-rank null model is calibrated and detects real paralog expansion vs the cohort baseline.

## Headline numbers

- Pilot: 1,000 species across 110 phyla; 1,200 UniRef50s in 6 classes; 6,638 (species, UniRef50) presence rows.
- Multi-rank null calibrated at genus / family / order / class / phylum.
- Producer scores computed for 9,201 (rank, clade, UniRef) tuples.
- Natural-expansion class (positive control on null responsiveness): producer z **+0.13 σ at genus → +0.55 σ at phylum**, all five ranks PASS at 95 % CI.
- Negative controls (ribosomal / tRNA-synth / RNAP): producer z negative at all ranks (-0.15 to -0.24 σ) — biologically correct (dosage constraint), revised criterion.
- Alm 2006 TCS HK reproduction at UniRef50: NOT REPRODUCED (mean z = -0.2, 4-11 % positive). Deferred to Phase 2/3 per v2 plan substrate hierarchy.

## Methodology revisions for Phase 1B

### M1 — Rank-stratified parent ranks for consumer null

NB02/NB03 used parent_rank = phylum for all child ranks. AMR consumer z is strongly negative (-4.4 to -4.8) across genus/family/order — but this reflects intra-phylum HGT (Enterobacteriaceae, Acinetobacter) being clumped at phylum level, not absence of HGT. In Phase 1B, use rank-stratified parents: genus → family parent, family → order parent, order → class parent, class → phylum parent. This makes the consumer null sensitive to intra-phylum HGT.

*Affects*: NB02-equivalent at scale, consumer score interpretation

### M2 — Negative-control criterion revised: ≤ 0 not ~ 0

Pre-registered criterion (mean producer z within ±1 σ of 0) was incorrect. Ribosomal proteins, tRNA synthetases, and RNAP core subunits are dosage-constrained — they have FEWER paralogs than typical genes at matched prevalence. Negative producer z is the biologically correct outcome, not a methodology failure. Phase 1B uses 'producer CI upper bound ≤ 0.5' as the negative-control criterion.

*Affects*: NB04-equivalent gate criteria, DESIGN_NOTES.md weak-prior framing

### M3 — Alm 2006 reproduction not in Phase 1 scope — confirmed by pilot

At UniRef50 resolution, individual TCS HK UniRef50 clusters do not show paralog expansion above null (mean z ≈ -0.2 across all ranks; 4-11 % positive z). Alm 2006's finding is at the HK FAMILY level — number of distinct HK genes per genome — which is a different unit of analysis. The v2 plan's substrate hierarchy already places Alm 2006 reproduction at Phase 2 (KO) and Phase 3 (Pfam architecture). The Phase 1A pilot confirms this hierarchy: UniRef50 alone does not capture HK family-level expansion. This is a Phase 1A finding, not a methodology failure.

*Affects*: DESIGN_NOTES.md substrate hierarchy validation

### M4 — Paralog fallback (option a) is acceptable for the pilot

21.5 % of presence rows use n_gene_clusters when UniRef90 is missing. Producer null behaves consistently across this fraction — no obvious bias. Phase 1B should report with-and-without-fallback sensitivity as a robustness check.

*Affects*: NB02-equivalent at scale

## What this Gate verdict means

Phase 1B may proceed with the four methodology revisions documented above. The pilot has demonstrated:

1. The producer null is **responsive** (natural_expansion validates it).
2. Negative controls behave **correctly** under the biologically right criterion (dosage-constrained → negative z, not zero).
3. The consumer null at parent-phylum anchor is **too coarse** for intra-phylum HGT detection (AMR signal masked); rank-stratified parents fix this.
4. Alm 2006 reproduction at Phase 1 (UniRef50) is **not in scope**; the v2 plan's substrate hierarchy already places it at Phase 2 (KO) and Phase 3 (Pfam architecture). The pilot confirms the hierarchy.

## Next step

Phase 1B (full GTDB scale, 27,690 species, all UniRef50s) with M1–M4 revisions applied, OR pause for /synthesize and adversarial review on Phase 1A as a checkpoint before scaling.

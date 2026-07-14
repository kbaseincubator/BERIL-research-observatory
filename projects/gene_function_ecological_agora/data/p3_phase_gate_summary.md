# Phase 3 → Phase 4 Gate Decision

**Date**: 2026-04-28
**Concordance verdict**: `PASS_MIXED`

## Phase 3 components

### NB13 — Pfam pre-flight audit
- **Substrate decision**: USE interproscan_domains
- bakta_pfam_domains: 7/33 markers with ZERO clusters (silent gaps including all 4 PSII Pfams)
- interproscan_domains: 1/33 markers with ZERO clusters
- Median bakta/IPS coverage ratio: 0.102
- Phase 3 architectural deep-dive uses **interproscan_domains** as substrate

### NB14 — Candidate selection
- **10,750 candidate KOs** with off-(low,low) Producer × Participation in atlas
- Category breakdown: {'metabolic': 4142, 'unannotated': 2255, 'mixed': 2126, 'regulatory': 1364, 'other': 863}

### NB15 — Architecture census (focused subsets)
- **376 KOs** across PSII (25), TCS HK (292), mycolic-acid (11), mixed-top-50 (50)
- **15,264 (subset, KO, architecture) rows** materialized
- **Key finding**: mixed-category KOs show 46 architectures/KO median (vs 1 for PSII) — architectural promiscuity correlates with NB11's elevated Innovator-Exchange rate at the KO level

### NB16 — Cyanobacteria × PSII Innovator-Exchange test (donor-undistinguished per M25)
- **Class rank verdict**: `INNOVATOR-EXCHANGE (H1 supported, donor-undistinguished per M25)`
- Class-rank producer Cohen's d = **1.496** (very large)
- Class-rank consumer Cohen's d = **0.6958** (moderate-large)
- Both pass at α/4 = 0.0125
- **Acquisition-depth signature**: Cyanobacteria PSII = 32.26% recent / 2.05% ancient (vs all-PSII = 14.9% ancient). The 7× lower ancient fraction is the donor-origin signature: Cyanobacteria *gave* PSII to other phyla, doesn't *receive* ancient cross-phylum PSII transfers.
- **Pre-registered hypothesis SUPPORTED at class rank** (donor-undistinguished joint label per M25)

### NB17 — TCS HK architectural Alm 2006 back-test
- **292 TCS HK KOs across 3,998 distinct Pfam architectures**
- **KO ↔ architectural concordance at family rank**:
  - Producer correlation r = **0.0932** (exploratory)
  - Consumer correlation r = **0.6727** (confirmatory)
- Top architectures: `PF00072_PF00486` (Response_reg + Trans_reg_C, 76K gains), `PF00512_PF02518` (HisKA + HATPase_c, the canonical Alm 2006 architecture, 25K gains)
- All TCS HK architectures show ~45% recent / ~4-5% ancient acquisition profile — consistent class signature

## Concordance verdict

`PASS_MIXED`: Phase 4 synthesis treats Phase 3 architectural results as MIXED-CONCORDANCE; consumer/participation signal is confirmatory (r >= 0.6), producer signal is exploratory (r < 0.6)

## Phase 3 → Phase 4 hand-off

Phase 4 inherits:
- Atlas (NB10) + M22 attribution (NB10b) — primary deliverable
- Phase 2 hypothesis test results (NB11 H1 REFRAMED + complexity-hypothesis-direction, NB12 H1 SUPPORTED Mycobacteriaceae × mycolic-acid)
- Phase 3 candidate set (10,750 KOs) for selective architectural lookups
- Phase 3 architecture census (376 KOs × 15K (KO, architecture) rows) for hypothesis-test refinement
- Phase 3 NB16 Cyanobacteria PSII H1 SUPPORTED at class rank (donor-undistinguished per M25)
- Phase 3 NB17 TCS HK architectural decomposition (consumer concordance confirmatory, producer concordance exploratory)

Phase 4 deliverables (P4-D1..D5 per plan v2.9):
- P4-D1 phenotype/ecology grounding (NMDC + MGnify + GTDB metadata + BacDive + Web of Microbes + Fitness Browser)
- P4-D2 MGE context per gain event (gains stronger weight per M25 deferral of donor inference)
- P4-D3 explicit Alm r ≈ 0.74 reproduction (per-genome HPK count + recent-LSE)
- P4-D4 within-species pangenome openness validation
- P4-D5 annotation-density bias residualization closure

The atlas-as-deliverable framing (per v2.9 strategic reframe) survives Phase 3 with one
additional pre-registered hypothesis empirically supported (Cyanobacteria PSII at class
rank), making **2 of 4 currently-testable pre-registered hypotheses confirmed**:

| Hypothesis | Result |
|---|---|
| Bacteroidota PUL → Innovator-Exchange (Phase 1B) | falsified at UniRef50 absolute-zero |
| Regulatory-vs-metabolic asymmetry (NB11 Tier-1) | H1 REFRAMED — direction supports Jain 1999 complexity hypothesis at small effect size |
| Mycobacteriaceae × mycolic-acid → Innovator-Isolated (NB12) | **H1 SUPPORTED** at family + order |
| **Cyanobacteria × PSII → Broker-or-Open joint (NB16)** | **H1 SUPPORTED** at class rank |
| Alm 2006 r ≈ 0.74 reproduction (P4-D3) | not yet tested |

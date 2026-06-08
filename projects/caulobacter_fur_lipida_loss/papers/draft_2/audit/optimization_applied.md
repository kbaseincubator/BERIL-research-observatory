# Selective Optimizer (M4) — Applied Subtractions

**Draft:** papers/draft_2/manuscript.md
**Source of truth:** REPORT.md
**Review:** audit/adversarial_review.json (10 findings; P0=0, P1=6, P2=3, info=1)
**Mode:** subtraction-only

## Findings processed by class

| Class | Count | Disposition |
|---|---|---|
| central_objection | 1 | SKIPPED-narrative (1) |
| report_drift | 2 | REMOVED (2) |
| abstract_body_mismatch | 1 | TIGHTENED (1) |
| claim_evidence | 3 | RELABELED (1), REMOVED (1), SKIPPED-provenance (1) |
| register_drift | 1 | HEDGED (1) |
| unbacked_quantitative | 1 | CORRECTED-to-REPORT (1) |
| missing_section | 1 | HALT-REQUESTED (1) |

## Per-finding actions

- **F001** (central_objection, info) — **SKIPPED-narrative.** Title/synthesis over-coordination
  framing is a deep narrative issue not subtraction-fixable. Per role rules, not revised.
  The title and L187 synthesis tension is partially addressed by the F005 fix (L187 de-causalized).
  The title itself was left unchanged; flag for Phase 1 throughline mechanism.

- **F002** (report_drift, P1, Results L167) — **REMOVED.** Deleted the FtsH/Langklotz sentence
  ("...may lower the energetic and regulatory barriers to LpxC deletion..."). This causal
  comparative-genomics synthesis appears nowhere in REPORT.md (no occurrence of "Langklotz",
  "FtsH", or "LpxC proteolysis") and reframing_log.md is empty. Surrounding paragraph preserved;
  ends cleanly at "...the only available one." (Langklotz2011 now an orphan reference-list entry.)

- **F003** (abstract_body_mismatch, P1, Results L67) — **TIGHTENED.** Changed
  "the quantitative outputs of all five analytic layers" → "...the four analytic layers" to
  resolve the internal "five-but-lists-four" contradiction, aligning with the four-layer framing
  in Abstract (L13), Introduction (L27), and Fig 1 caption (L71). No new numerics ("four" already
  used throughout). NOTE: REPORT.md itself uses "five mechanism layers"; the four-vs-five reframe
  relative to REPORT remains unlogged in reframing_log.md (upstream handoff).

- **F004** (claim_evidence, P1, Figs 1 & 2 captions) — **RELABELED.** Removed the conflated
  "Path B" token from the n=53 buffered-cohort mentions in both figure captions
  ("ΔsspB-buffered Path B subset (n = 53)" → "ΔsspB-buffered subset (n = 53)"), reserving
  "Path B (n=26)" for the fitness-scorable hypergeometric set in Table 1 / L81. Both REPORT-backed
  numbers (53, 26) retained; no new numerics added.

- **F005** (register_drift, P1, Discussion L187) — **HEDGED.** Replaced the causal phrasing
  "a single regulatory circuit (ChvG–ChvI) drives a specific effector output (Pal-Tol upregulation)"
  with convergence language ("Pal is induced as both a member of the late ChvI consequence cohort
  and a PG-remodeling effector — convergent evidence ... consistent with, but does not establish,
  ChvI regulation of Pal"). Matches REPORT's "convergence"/"cross-notebook convergence" register
  (Finding 5). No numerics or citations added.

- **F006** (unbacked_quantitative, P1, Results L150 + Methods L55) — **CORRECTED-to-REPORT.**
  Manuscript had listed LpxB among genes with "zero PaperBLAST hits"; REPORT.md records LpxB at
  1 hit ("PaperBLAST under-count"), distinct from the true false-negatives. Removed LpxB from the
  zero-hit enumeration in both locations (and its corresponding NCBI count "18" in the L150 list:
  "11, 15, 15, 18, and 18" → "11, 15, 15, and 18"). Headline ~80% false-negative claim (C-061)
  unaffected. No numbers introduced — only the contradicting member removed.

- **F008** (report_drift, P2, Discussion L175) — **REMOVED.** Deleted the ChvT sentence asserting
  "Fur derepression and ChvI engagement ... are interconnected through shared genetic components."
  This layer-interconnection synthesis is not in REPORT.md (which lists ChvT only as a Path A top
  fitness hit / OM iron-transport machinery) and reframing_log.md is empty. Surrounding paragraph
  preserved; ends at "...provides the appropriate reference."

- **F010** (claim_evidence, P2, Abstract L13) — **HEDGED/TIGHTENED.** Changed "three other
  Gram-negative species with documented LPS dispensability" → "three other Gram-negative species
  that tolerate loss or truncation of LPS" to match the body's careful distinction that
  M. catarrhalis truncates rather than loses LPS (Intro L19, Results L167). No numerics/citations.

- **F009** (claim_evidence, P2, low confidence, Methods L47) — **SKIPPED-provenance.** Methods
  names scipy.stats.hypergeom; methods_provenance.md's auto-extracted test list omits it. REPORT.md
  independently corroborates the hypergeometric verdict and p-values (Path A p=0.016, Path B p=0.515;
  NB02b). The test is REPORT-backed, so removing it would be wrong. This is a provenance-extractor
  reconciliation task, not a subtraction. No manuscript edit. Handoff to methods_provenance.md
  population.

## Halt requests (missing infrastructure / unfixable by subtraction)

- **F007** (missing_section, P1) — **HALT-REQUESTED.** The manuscript lacks software version
  information (Python, scipy, R/Bioconductor, edgeR, Biopython) and the Data Availability section
  carries a placeholder repository URL ("[REPOSITORY URL TO BE PROVIDED]"). Version numbers cannot
  be added (forbidden: would be fabricated numerics) and the repository URL cannot be resolved by
  this optimizer. Requires upstream population of methods_provenance.md package-version fields from
  the committed notebook environments (00–07) and a resolvable code/data DOI/URL. No manuscript
  edit made.

## Self-check

Grepped the modified manuscript for newly introduced numerics — none added. The only
number-touching edit (F006) was a *removal* of contradicting values to align with REPORT.md.
No CIs, p-values, n-counts, effect sizes, or inline citation tokens were added.

## Summary

- Total findings: 10
- Subtractions (REMOVED): 2 (F002, F008)
- Corrected-to-REPORT / relabeled / tightened / hedged: 5 (F003, F004, F005, F006, F010)
- Citation markers added ([NEEDS CITATION]): 0
- Skipped (narrative / provenance, not subtraction-fixable): 2 (F001, F009)
- Halt requests: 1 (F007 — missing software versions + repository URL)

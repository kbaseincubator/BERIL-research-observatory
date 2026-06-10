# P0 gate — pause point

## Summary

- **Total P0 findings:** 1
- **By source:** numeric_grounding=1
- **By class:** count_of=1
- **Remediation cycles used:** 0 / 2
- **Telemetry notes:**
  - filter_applied: demoted 1 missing_section finding(s) about Data Availability / Code Availability — compliance_gate autofixes these post-gate. See demoted_findings.

## How to proceed

Three options:

1. **Attempt automated remediation** (re-drafts the manuscript with anti-fabrication discipline; cap defaults to 2 cycles):

   ```
   beril-paper-writer continue /home/aparkin/BERIL-research-observatory/projects/caulobacter_fur_lipida_loss/papers/draft_1 --remediate
   ```

2. **Ship anyway** (advance to optimize despite P0s; the optimizer's subtraction-only invariant still applies, but the P0 findings will land in the audit trail unaddressed):

   ```
   beril-paper-writer continue /home/aparkin/BERIL-research-observatory/projects/caulobacter_fur_lipida_loss/papers/draft_1 --ship-with-p0s
   ```

3. **Edit `manuscript.md` by hand** and re-run (the gate re-runs phase_review on any manuscript edit it detects):

   ```
   # ...edit /home/aparkin/BERIL-research-observatory/projects/caulobacter_fur_lipida_loss/papers/draft_1/manuscript.md...
   beril-paper-writer continue /home/aparkin/BERIL-research-observatory/projects/caulobacter_fur_lipida_loss/papers/draft_1
   ```


## Filtered findings (not counted in P0 total)

These adversarial findings were demoted by the gate's false-positive filter. They are recorded here for audit-trail completeness. Each carries a `filter_reason` documenting why it was demoted.

### F001 — missing_section (adversarial) — filter: pre-compliance-missing-section

- **Location:** (section unspecified)
- **Issue (demoted):** Data Availability section states that RNA-seq raw reads will be deposited to GEO and proteomics spectra to ProteomeXchange/PRIDE 'pr … [trunc] … cannot access the primary data, and the reproducibility claim in the abstract cannot be verified. This is a hard submission blocker.

## Findings

### NG-051842 — count_of (numeric_grounding)

- **Location:** data and code availability para 1
- **Issue:** Numeric value '1101' not found in claim_inventory.tsv (Tier A) or REPORT.md (Tier B). Manuscript section: data and code availability, paragraph 1.
- **Suggested fix:** Remove or revise the numeric '1101/2026': it has no match in claim_inventory.tsv (Tier A) or REPORT.md (Tier B). Do NOT replace with an invented number. If the prose needs a quantity, hedge it qualitatively.
- **Quote:** `2026 preprint identifying the sphingolipid-locus Lpt paralogs is available at bioRxiv 10.1101/2026.04.12.717747.`

# Optimization Log — M4 Selective Optimizer (subtraction-only)

**Draft:** draft_1/manuscript.md
**Review source:** draft_1/audit/adversarial_review.json
**Optimizer run:** 2026-06-04
**Total findings:** 8

## Findings by class

| Class | Count |
|---|---|
| missing_section | 2 |
| citation_reality | 2 |
| claim_evidence | 1 |
| abstract_body_mismatch | 1 |
| section_arc | 1 |
| central_objection | 1 |

## Per-finding actions

### F001 — missing_section (P0): Data Availability accession numbers
**Action: HALT-REQUESTED**
The Data Availability section is present but lacks GEO and ProteomeXchange/PRIDE accession numbers. These require upstream data deposition by the originating laboratory before they can be added to the manuscript. The current manuscript honestly discloses this as planned ("Deposition... is planned prior to journal submission; accession numbers will be added at that time"). No manuscript edit is possible without the actual accession numbers.

**Halt dependency:** RNA-seq raw reads → NCBI GEO; proteomics raw spectra → ProteomeXchange/PRIDE.

### F002 — citation_reality (P1): citation_map.md tracking gaps
**Action: SKIPPED (upstream tracking file)**
The five citations flagged (Olea-Ozuna2021, Olea-Ozuna2024, Hernandez-Ortiz2025, de2016, Dos2024) are all valid — they appear in the manuscript bibliography, in citation_pool.json, and reference real published papers. The issue is with citation_map.md's internal tracking (incomplete first-cited-at fields, "Uncited" mislabeling), not with the manuscript text. No manuscript edit required; citation_map.md needs upstream refresh.

### F003 — claim_evidence (P1): Figure 6 caption falsely claims dual-source confirmation
**Action: REMOVED overclaim from caption**
- **Before:** "assessed by PaperBLAST text mining [Price2017] and confirmed by NCBI annotation"
- **After:** "assessed by PaperBLAST text mining [Price2017]. NCBI annotation confirmation is shown in Table 3."
- **Rationale:** Figure 6 (NB06_comparative_heatmap.png) shows PaperBLAST data only. NCBI annotation confirmation is in Table 3 (from NB06b). The caption attributed two-source confirmation to a figure that shows one source. The fix removes the false attribution and redirects the reader to the correct table.

### F004 — abstract_body_mismatch (P1): Abstract overclaims "striking" for single-replicate observation
**Action: HEDGED — replaced overclaiming adjective with qualified language**
- **Before:** "exhibits a striking transcript-protein discordance"
- **After:** "exhibits an apparent transcript-protein discordance in single-replicate outer membrane proteomics"
- **Rationale:** The body text (Discussion) hedges the same observation: "This transcript-protein discordance represents a notable finding: it may reflect post-translational regulation..." and the Limitations section states the proteome is single-replicate. The word "striking" in the abstract signals a robust, replicated observation to abstract-only readers. "Apparent" + the single-replicate qualifier brings the abstract into register with the body's hedging.

### F005 — missing_section (P1): Limitations missing DE pipeline reproducibility caveat
**Action: HEDGED — added one sentence to existing Limitations paragraph**
- **Added:** "The primary differential expression statistics were produced by an upstream pipeline whose reported tool versions are mutually inconsistent (see Methods); hypothesis verdicts therefore depend on the reported statistics being correct."
- **Inserted after** the single-replicate proteomics limitation sentence and **before** the single growth condition sentence.
- **Rationale:** The Methods section (line 62) already discloses the R 4.0.2 / edgeR 1.14.5 version inconsistency. This sentence surfaces that disclosure in Limitations so reviewers reading both sections do not notice an omission. No new numerics or claims added — the sentence cross-references Methods via "(see Methods)".

### F006 — section_arc (P2): Results opening and Figure 1 caption overclaim scope
**Action: REMOVED overclaim — corrected figure reference and panel count**
- **Results opening (line 66):**
  - Before: "summarized in Figure 1"
  - After: "summarized in Figures 1 and 6"
- **Figure 1 caption (line 70):**
  - Before: "Overview of the five mechanistic layers"
  - After: "Overview of four of the five mechanistic layers supporting lipid A dispensability in *Caulobacter crescentus* (comparative genomics shown in Figure 6)"
- **Rationale:** Figure 1 has four panels (A–D). The fifth line of evidence (comparative genomics) appears in Figure 6. The original text falsely claimed Figure 1 summarized all five layers.

### F007 — citation_reality (P2): references.md mislabels cited references as "Uncited"
**Action: SKIPPED (upstream tracking file)**
Same class of issue as F002. Dhakephalkar2023, Dhakephalkar2025, Olea-Ozuna2021, and Olea-Ozuna2024 are cited in the manuscript body and have valid bibliography entries. The "Uncited" label in references.md is a tracking error in that file, not a manuscript defect. Requires upstream references.md reorganization.

### F008 — central_objection (info): "repurposing" overclaim in title/abstract
**Action: SKIPPED-narrative**
This is a deep narrative finding about the central interpretive framing. The reviewer's objection — that the LptD/LptE protein-level decline is most parsimoniously explained by substrate-limited Lpt disassembly rather than repurposing — is substantive and should be addressed through the Phase 1 throughline-pick mechanism or a Discussion revision by the authors. The title change (from "repurposing" to "potential involvement") is a framing decision that exceeds the scope of subtraction-only optimization.

## Summary statistics

| Metric | Count |
|---|---|
| **Subtractions (REMOVED/HEDGED)** | 4 |
| **Citation markers added ([NEEDS CITATION])** | 0 |
| **Halt requests** | 1 |
| **Skipped — upstream tracking file** | 2 |
| **Skipped — narrative** | 1 |

## Halt requests

1. **F001** — GEO and ProteomeXchange/PRIDE accession numbers. Blocked on upstream data deposition by the originating laboratory. The manuscript cannot pass journal desk review without valid accession numbers.

## Self-check

Scanned the modified manuscript for numerics potentially introduced by the optimizer. The only word-to-number change was "five" → "four" in the Figure 1 caption, which is a correction of a factual count of figure panels (the figure has panels A–D = 4 panels). No statistical values, CIs, p-values, effect sizes, or n-counts were added.

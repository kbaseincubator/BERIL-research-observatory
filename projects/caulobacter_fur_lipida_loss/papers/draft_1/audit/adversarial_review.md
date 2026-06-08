---
reviewer: BERIL Adversarial Review (Paper, claude-sonnet-4-6)
type: paper
date: 2026-06-04
draft_dir: /home/aparkin/BERIL-research-observatory/projects/caulobacter_fur_lipida_loss/papers/draft_1
project_id: caulobacter_fur_lipida_loss
draft_number: 1
prompt_version: adversarial_paper.v3
tier: STRONG
total_findings: 8
severity_counts:
  P0: 1
  P1: 4
  P2: 2
class_counts:
  throughline: 0
  claim_evidence: 1
  unbacked_quantitative: 0
  register_drift: 0
  citation_reality: 2
  report_drift: 0
  abstract_body_mismatch: 1
  missing_section: 2
  section_arc: 1
  central_objection: 1
---

# Adversarial Review — caulobacter_fur_lipida_loss draft_1

**Reviewer:** beril-adversarial --type paper v3 (claude-sonnet-4-6)
**Reviewed at:** 2026-06-04T12:00:00Z
**Total findings:** 8 (1 P0, 4 P1, 2 P2, 1 info)

---

## A. Throughline integrity

No findings. The five-layer structure is delivered. Layer 1 (Fur TBDT enrichment) is correctly hedged as marginal throughout the paper. Layer 3 (SigU driver) is correctly marked rejected. The comparative species layer (Layer 5) is fully supported by NCBI confirmation data. The throughline sub-claims map cleanly to Results sections. No P0 or P1 throughline violations.

---

## B. Claim-evidence support

### P1 — F003: Figure 6 caption claims NCBI confirmation shown in figure; figure is PaperBLAST-only

**Section:** Results, L163-165

**Paper text:** "Presence and absence of focal gene families across the four Gram-negative species capable of lipid A loss, assessed by PaperBLAST text mining [Price2017] and confirmed by NCBI annotation."

**What the figure actually contains:** NB06_comparative_heatmap.png. figures_inventory.md entry reads: "Title: Focal gene presence/absence (1=present, 0=absent in PaperBLAST)." This is PaperBLAST-only.

**What REPORT says:** "The original NB06 used PaperBLAST description-text matching. NB06b (added post-review) re-ran the comparative panel against NCBI's protein database via Biopython Entrez." The NCBI confirmation data is presented as Table 3 (manuscript lines 154-161), not as part of Figure 6.

**The problem:** A reader who examines Figure 6 expecting NCBI-confirmed data sees only PaperBLAST data. The caption attributes two-source confirmation to a figure that shows one source. A reviewer who inspects the figure will find the caption inaccurate.

---

## C. Register drift

No findings. All quantitative claims traced to REPORT. The REPORT's own register is matched in the manuscript with one exception — the word "striking" in the abstract applied to single-replicate protein observations — which is filed under abstract_body_mismatch (F004) because the body itself is appropriately hedged while the abstract is not.

---

## D. Citation reality

### P1 — F002: citation_map.md incomplete and has incorrect "first cited" locations for 9 citations

**Affected citations:** Olea-Ozuna2021, Olea-Ozuna2024, Hernandez-Ortiz2025, de2016, Dos2024 (absent entirely from citation_map.md); Balhesteros2017, Silva2019 (wrong "first cited" location).

**What the manuscript body actually contains:**
- [Olea-Ozuna2021, Olea-Ozuna2024] — cited at Introduction line 20 and Results lines 111, 175
- [Hernandez-Ortiz2025], [de2016], [Dos2024] — cited at Introduction line 22
- [Silva2019], [Balhesteros2017] — cited at Introduction line 22; citation_map.md says "references, paragraph 16/17" (wrong)

**What references.md says:** Olea-Ozuna2021 and Olea-Ozuna2024 are labeled "Uncited (in pool but not yet cited in prose)" — factually wrong; they are cited at line 20.

**No fabrication:** All nine have valid bibliography entries. This is broken citation tracking, not a missing source. But the citation map is the contract between body text and bibliography; a broken contract means a future auditor cannot rely on it.

### P2 — F007: references.md "Uncited" label wrong for Dhakephalkar2023, Dhakephalkar2025, Olea-Ozuna2021, Olea-Ozuna2024

references.md places all four under "Uncited (in pool but not yet cited in prose)." All four are cited inline in the manuscript body (Olea-Ozuna2021/2024 at lines 20, 111, 175; Dhakephalkar2023/2025 at line 111). No bibliography entry is missing, but the "Uncited" label corrupts bibliography organization and will confuse any downstream tooling that reads references.md to identify which sources were actually used.

---

## E. REPORT drift

No findings. All major quantitative claims were traced to REPORT. Key numbers verified:

| Claim | Paper | REPORT |
|---|---|---|
| Spearman rho | 0.315, p=2.08×10⁻³ | 0.315, p=2.08e-03 ✓ |
| Leaden DEGs | 93 | 93 ✓ |
| 71% sign concordance | 71% | 71% ✓ |
| Buffered subset | 53 of 93 | 53 of 93 ✓ |
| Path A fold enrichment | 1.60×, p=0.016 | 1.60×, p=0.016 ✓ |
| Path B fold enrichment | 1.04×, p=0.515 | 1.04×, p=0.515 ✓ |
| Genome background | 33.25% (1311/3943) | 33.25% (n=3943, K=1311) ✓ |
| ChvI union | 488 genes | 488 ✓ |
| Phase partition | 20+10+49=79 | 20+10+49 ✓ |
| spt log2 change | −0.64, FDR 0.002 | −0.64, FDR 0.002 ✓ |
| sphk log2 change | −0.40, FDR 0.02 | −0.40, FDR 0.02 ✓ |
| MsbA-like CCNA_00307 | +0.89, FDR 0.01 | +0.89, FDR 0.01 ✓ |
| LptD rescued/intermediate | −0.47 | −0.47 ✓ |
| LptE rescued/intermediate | −0.78 | −0.78 ✓ |
| PG genes meeting H4 | 28 | 28 ✓ |
| SdpA protein | +4.8 log2 | +4.8 log2 ✓ |
| Pal transcript/protein | +2.08 / +2.84 | +2.08 transcript, +2.84 protein ✓ |
| spt NCBI hits (C/A/N/M) | 7/0/0/0 | 7,0,0,0 ✓ |
| ChvG NCBI hits | 5/0/0/0 | 5,0,0,0 ✓ |
| PaperBLAST false-negative rate | ~80% | ~80% ✓ |

The reframing_log.md covers both substantive changes (F001 figure alt-text correction, F004 additive methods section). No silent drift found.

---

## F. Abstract-body mismatch

### P1 — F004: "Striking" in abstract for single-replicate protein observations; body hedges appropriately

**Abstract (line 12):** "The canonical lipopolysaccharide transport (Lpt) apparatus exhibits a **striking** transcript-protein discordance: an MsbA-like transporter and an LptC-related component are significantly upregulated at the transcript level [C-043, C-044]... while the two Lpt proteins directly measured in the outer membrane proteome decline in the rescued strain [C-045, C-047]."

**Body Discussion (line 132):** "This transcript-protein discordance represents a notable finding: it may reflect post-translational regulation, reduced demand for LPS-specific transport functions in the absence of LPS substrate, or genuinely decreased Lpt apparatus abundance at the protein level. **Resolution requires the replicated outer membrane proteomics planned for the originating laboratory.**"

**Limitations section:** "The outer membrane proteome is single-replicate per strain, precluding formal statistical testing of protein-level claims."

**REPORT:** "DISCORDANT with transcript; single replicate" — calls for "replicated proteomics."

"Striking" signals a robust, replicated observation. The body and REPORT are unambiguously tentative. A reader who reads only the abstract gets a stronger impression of protein-level data quality than the evidence supports. The body is appropriately hedged; the abstract is not.

---

## G. Missing sections / coverage gaps

### P0 — F001: GEO and ProteomeXchange accession numbers absent — hard submission blocker

**Section:** Data and code availability

**Paper text (lines 191-193):** "Deposition of the RNA-seq raw reads to GEO and the proteomics raw spectra to ProteomeXchange/PRIDE is planned prior to journal submission; accession numbers will be added at that time."

This is a standard blocking requirement at Cell Reports, mBio, PLoS Genetics, eLife, and most journals this manuscript would target. Without GEO and PRIDE accession numbers, peer reviewers cannot access the primary data. The paper's reproducibility claim cannot be verified. The data availability statement is accepted for a draft but is not acceptable at submission.

### P1 — F005: edgeR version inconsistency disclosed in Methods but absent from Limitations

**Methods (line 62) discloses:** "the R and edgeR version values reported in the SeqCenter run report (R 4.0.2 and edgeR 1.14.5) are mutually inconsistent — edgeR 1.14.5 dates to circa 2010 and is not installable on R 4.0.2 — so we treat the differential-expression statistics as reported by the upstream pipeline without independently re-running edgeR."

**Consequence:** All primary DE statistics — the logFC, p-values, and FDRs for both contrasts underpinning H1-H4 verdicts — were accepted from a pipeline whose tool versions are internally inconsistent and cannot be independently reproduced. The Limitations section lists eight specific limitations but does not include this one. A reviewer who reads Methods (where the problem is disclosed) and then checks Limitations (where it is absent) will flag the omission.

---

## H. Section arc / hourglass coherence

### P2 — F006: "Five lines of evidence, summarized in Figure 1" — Figure 1 has four panels; fifth line absent from the figure

**Results opening (lines 66-68):** "The integrated analysis yielded findings across five partially independent lines of evidence, **summarized in Figure 1**."

**Figure 1 panels:** A (Fur signature), B (ChvI phase distribution), C (sphingolipid/Lpt expression), D (PG remodeling). Four panels.

**Figure 1 caption:** "Overview of the **five** mechanistic layers supporting lipid A dispensability" — names only four panels A-D.

The fifth line of evidence (comparative genomics, Finding 6) appears as Figure 6, not Figure 1. The opening sentence and the figure caption both say "five" while showing four. Minor inconsistency that a careful reviewer will notice.

---

## I. Central objection (peer-reviewer killshot)

**F008 — Lpt apparatus repurposing is a working hypothesis, not an established function; the protein evidence is directionally contrary to the model**

The paper's title ("Lpt apparatus repurposing") and abstract position Lpt repurposing for sphingolipid trafficking as a central contribution. The evidence offered is transcript upregulation of MsbA-like CCNA_00307 (+0.89 log2, FDR 0.01) and LptC-related CCNA_03716 (+0.56, FDR 0.005), described as "consistent with a recently proposed shared-component model." But the two canonical Lpt components actually measured at the protein level in the same rescued strain — LptD (−0.47 log2, rescued vs. intermediate) and LptE (−0.78 log2) — decline.

LptD and LptE form the outer-membrane-inserting Lpt translocon that deposits lipid A into the outer leaflet. Their protein-level decline in a strain without LPS is the most parsimonious outcome of substrate-limited complex disassembly — not repurposing for a new cargo. A hostile peer reviewer will write:

> "Your own single-replicate proteomics show the outer-membrane-facing Lpt translocon components declining in the strain you claim repurposes Lpt for sphingolipid transport. Transcript upregulation of two inner-membrane-proximal Lpt-like components is consistent with many explanations besides sphingolipid transport function — stress-responsive upregulation, compensatory transcription after protein-level decline, or regulation by the same ChvI-envelope-stress circuit you describe elsewhere. You have characterized a discordance; you have not demonstrated a function. The word 'repurposing' in the title and abstract is not supported by the data you present."

**Does the paper preempt this?** Partially. Discussion paragraph 4 (lines 177-178) offers three non-exclusive hypotheses including substrate limitation: "LptD and LptE may be substrate-limited in the absence of LPS, leading to reduced protein stability despite maintained transcription." But the paper does not acknowledge that this substrate-limitation hypothesis — LptD/LptE decline because there is no LPS to transport — is actually inconsistent with the repurposing claim (a repurposed apparatus would still need its OM-facing components). The Discussion frames three hypotheses as equivalent alternatives without ranking them by parsimony, and the title and abstract continue to assert "repurposing" without hedging.

**Suggested fix:** Revise Discussion to explicitly state that the transcript evidence is consistent with Uchendu 2026 shared-component repurposing AND consistent with substrate-limited Lpt complex disassembly; that single-replicate proteomics cannot distinguish these; and that "repurposing" is a working hypothesis requiring functional validation (e.g., replicated proteomics showing LptD/LptE maintained at protein level, or in vitro sphingolipid transport reconstitution with the canonical Lpt machinery). Weaken the title and abstract from "repurposing" to "potential repurposing" or "evidence for involvement." This is one sentence in the title and one clause in the abstract — a small change with a large effect on reviewer reception.

---

## Suggested fixes (consolidated)

### abstract.v1.md
- **F004** (Abstract, line 12): Replace "exhibits a **striking** transcript-protein discordance" with "exhibits an apparent transcript-protein discordance in single-replicate outer membrane proteomics." Removes register inflation relative to the body's hedging.

### discussion.v1.md
- **F008** (Discussion, paragraph 4 + title): Strengthen to explicitly acknowledge that LptD/LptE protein-level decline is consistent with substrate-limited Lpt disassembly (no LPS to transport) as an alternative to repurposing — and that these cannot be distinguished without replicated proteomics and functional assays. Revise the title and abstract claim from "Lpt apparatus repurposing" to "potential Lpt apparatus repurposing" or "evidence for Lpt apparatus involvement."

### limitations.v1.md
- **F005** (Limitations, missing bullet): Add: "The primary differential expression statistics (logFC, p-value, FDR) were produced by SeqCenter's upstream pipeline. The pipeline's reported tool versions (R 4.0.2 and edgeR 1.14.5) are mutually inconsistent (edgeR 1.14.5 predates R 4.0.2 by a decade) and cannot be independently reproduced from the reported version string. The H1-H4 verdicts therefore depend on the reported statistics being correct; independent re-analysis from deposited raw counts is recommended before final publication."

### results.v1.md
- **F003** (Results, Figure 6 caption, L163-165): Revise Figure 6 caption to accurately state the figure shows PaperBLAST data only and that NCBI annotation confirmation is in Table 3, not the figure.
- **F006** (Results, opening sentence): Revise "summarized in Figure 1" to "summarized in Figures 1 and 6," or add a fifth panel to Figure 1 covering the comparative analysis, or revise Figure 1 caption from "five" to "four" with a pointer to Figure 6 for the fifth.

### references.v1.md
- **F002** (citation_map.md + references.md): Add entries to citation_map.md for Olea-Ozuna2021, Olea-Ozuna2024, Hernandez-Ortiz2025, de2016, Dos2024. Correct "first cited" for Balhesteros2017 and Silva2019 from "references, paragraph 16/17" to "introduction, paragraph 5." Move Olea-Ozuna2021 and Olea-Ozuna2024 from "Uncited" pool in references.md to the numbered bibliography.
- **F007** (references.md): Move Dhakephalkar2023, Dhakephalkar2025, Olea-Ozuna2021, Olea-Ozuna2024 from "Uncited" into the numbered bibliography with citation numbers assigned in order of first body appearance.

### 07_data_availability.md
- **F001** (Data availability, SUBMISSION BLOCKER): Deposit RNA-seq raw reads to NCBI GEO and proteomics spectra to ProteomeXchange/PRIDE before submission. Replace the placeholder sentence with actual accession numbers.

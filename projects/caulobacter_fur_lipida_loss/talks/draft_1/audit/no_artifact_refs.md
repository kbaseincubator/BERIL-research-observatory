# Process-detail bleed check

Scanned 36 slides for internal-artifact references (notebook IDs, file paths, REPORT.md sections, analysis-layer codes). These patterns make the deck unreadable to fresh peer audiences.

- **Total hits:** 114
- **Slides with hits:** 26/36
- **Hits by pattern:**
  - `notebook-id`: 47
  - `analysis-layer-code`: 42
  - `report-md-section`: 21
  - `notebook-file`: 4

## Per-slide hits

### Slide 4 — section_divider (slide_id=5)

- **notebook-id** in `speaker_notes`: `NB00`
  - Context: `...lytical methods, moves to the NB00 orientation finding that refr...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.

### Slide 5 — methods_summary (slide_id=6)

- **analysis-layer-code** in `bullets[3]`: `H2`
  - Context: `...eriments are iron-limitation; H2 reduced to envelope-axis only`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `bullets[5]`: `H2`
  - Context: `...s genome background as formal H2 verdict (pre-registered ≥10% ...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **notebook-id** in `speaker_notes`: `NB00`
  - Context: `... briefly acknowledge that the NB00 orientation finding on the ne...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **analysis-layer-code** in `speaker_notes`: `H2`
  - Context: `...nts — so the iron-axis arm of H2 was descoped to envelope-axis...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `speaker_notes`: `H2`
  - Context: `...nistic importance. The formal H2 verdict therefore uses hyperg...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.

### Slide 6 — data_figure (slide_id=7)

- **notebook-id** in `title`: `NB00`
  - Context: `NB00: sphingolipid biosynthesis is...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **report-md-section** in `data_source`: `REPORT.md §Phase A`
  - Context: `REPORT.md §Phase A; notebooks/00_orientation.ipy...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **notebook-id** in `speaker_notes`: `NB00`
  - Context: `...hypothesis testing began, the NB00 orientation notebook establis...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **notebook-id** in `speaker_notes`: `NB00`
  - Context: `...e uses CPM normalization from NB00 and is descriptive rather tha...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **notebook-id** in `speaker_notes`: `NB04`
  - Context: `...significantly UP — belongs to NB04 in Layer 3. What the speaker ...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **notebook-id** in `speaker_notes`: `NB00`
  - Context: `...er in S3. The delivery note: 'NB00 showed us the sphingolipid po...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.

### Slide 7 — data_table (slide_id=8)

- **report-md-section** in `data_source`: `REPORT.md §Finding 2 table`
  - Context: `REPORT.md §Finding 2 table; notebooks/02b_h2_hypergeomet...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **analysis-layer-code** in `speaker_notes`: `H2`
  - Context: `...his table delivers the formal H2 verdict: hypergeometric enric...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.

### Slide 8 — claim_evidence (slide_id=9)

- **analysis-layer-code** in `speaker_notes`: `A1`
  - Context: `... one partial finding. Direct (A1): Spearman rho=0.315, p=2.08e...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `speaker_notes`: `A5`
  - Context: `...fines both gene sets. Direct (A5): Path B fold enrichment 1.04...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `speaker_notes`: `A4`
  - Context: `...der envelope stress. Partial (A4): Path A fold enrichment 1.60...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.

### Slide 10 — methods_summary (slide_id=11)

- **analysis-layer-code** in `bullets[4]`: `H1`
  - Context: `Pre-registered H1 phase-structure threshold: ≥1...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **report-md-section** in `speaker_notes`: `REPORT`
  - Context: `...ting explicitly: the original REPORT draft described an 'early coh...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.

### Slide 11 — data_table (slide_id=12)

- **report-md-section** in `data_source`: `REPORT.md §Finding 3`
  - Context: `REPORT.md §Finding 3; NB 03_chvi_phase_partition_s...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **notebook-id** in `speaker_notes`: `NB03`
  - Context: `... at +2.08 appears in both the NB03 late ChvI cohort (this slide)...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **notebook-id** in `speaker_notes`: `NB05`
  - Context: `...I cohort (this slide) and the NB05 PG-remodeling set — a cross-n...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **analysis-layer-code** in `speaker_notes`: `A8`
  - Context: `...al. This is a direct finding (A8). Earlier draft's 'early coho...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.

### Slide 12 — claim_evidence (slide_id=13)

- **analysis-layer-code** in `speaker_notes`: `A11`
  - Context: `... statistically discriminated (A11 = partial, per plan inventory...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.

### Slide 14 — methods_summary (slide_id=15)

- **analysis-layer-code** in `title`: `H3`
  - Context: `Methods: H3 sub-claims tested across tran...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `speaker_notes`: `H3`
  - Context: `The H3 evidence comes from two data ...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `speaker_notes`: `H3`
  - Context: `...cript contrast is the primary H3 readout; the proteome is a po...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.

### Slide 15 — data_figure (slide_id=16)

- **notebook-file** in `data_source`: `NB04_sphingolipid_lpt_panel.ipynb`
  - Context: `REPORT.md §Finding 4; NB04_sphingolipid_lpt_panel.ipynb cell 3`
  - Why: Notebook filename (project-internal). Belongs in audit/ logs, not on slides.
  - Fix: Move the path to <draft_dir>/audit/ and replace the slide citation with the underlying paper or cohort reference.
- **report-md-section** in `data_source`: `REPORT.md §Finding 4`
  - Context: `REPORT.md §Finding 4; NB04_sphingolipid_lpt_panel....`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **report-md-section** in `speaker_notes`: `REPORT.md §Finding 4: 0 of 6`
  - Context: `...declining, not induced.  From REPORT.md §Finding 4: 0 of 6 biosynthesis genes UP at FDR ...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.

### Slide 16 — data_table (slide_id=17)

- **notebook-file** in `data_source`: `NB04_sphingolipid_lpt_panel.ipynb`
  - Context: `REPORT.md §Finding 4; NB04_sphingolipid_lpt_panel.ipynb cells 3,5,6`
  - Why: Notebook filename (project-internal). Belongs in audit/ logs, not on slides.
  - Fix: Move the path to <draft_dir>/audit/ and replace the slide citation with the underlying paper or cohort reference.
- **report-md-section** in `data_source`: `REPORT.md §Finding 4`
  - Context: `REPORT.md §Finding 4; NB04_sphingolipid_lpt_panel....`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **report-md-section** in `speaker_notes`: `REPORT.md §Finding 4 pilot`
  - Context: `... directional pilot datum (see REPORT.md §Finding 4 pilot).  CtpA verdict: REJECTED. Tr...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.

### Slide 18 — section_divider (slide_id=19)

- **notebook-id** in `speaker_notes`: `NB03`
  - Context: `...-consequence ChvI cohort from NB03 and the pre-curated PG-remode...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **notebook-id** in `speaker_notes`: `NB05`
  - Context: `...urated PG-remodeling set from NB05. That kind of cross-notebook ...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.

### Slide 19 — methods_summary (slide_id=20)

- **analysis-layer-code** in `title`: `H4`
  - Context: `H4 PG-remodeling test: pre-curat...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `bullets[5]`: `H4`
  - Context: `H4 pre-registered pass criterion...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **notebook-id** in `bullets[6]`: `NB03`
  - Context: `Cross-notebook check: NB03 late-ChvI cohort compared ind...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **notebook-id** in `speaker_notes`: `NB00`
  - Context: `...oc hypothesis added after the NB00 orientation surfaced SdpA at ...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **notebook-id** in `speaker_notes`: `NB03`
  - Context: `... convergence step — comparing NB03's late-ChvI cohort against th...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **notebook-id** in `speaker_notes`: `NB05`
  - Context: `... late-ChvI cohort against the NB05 PG hits — identified Pal as s...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **analysis-layer-code** in `speaker_notes`: `H4`
  - Context: `... DE is critical: it means the H4 threshold test is not circula...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `speaker_notes`: `M23`
  - Context: `... lipid-II flippase MviN/MurJ, M23-family endopeptidases, and an...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `speaker_notes`: `H4`
  - Context: `...lication, 28 unique loci. The H4 pre-registered pass criterion...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `speaker_notes`: `H4`
  - Context: `... inclusion does not alter the H4 verdict. Second, the cross-no...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.

### Slide 20 — data_figure (slide_id=21)

- **analysis-layer-code** in `title`: `H4`
  - Context: `28 PG-remodeling loci meet H4 threshold: broad downshift wi...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `caption`: `H4`
  - Context: `PG-remodeling enzymes meeting H4 threshold (28/53 pre-curated ...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **report-md-section** in `data_source`: `REPORT.md §Finding 5`
  - Context: `REPORT.md §Finding 5; NB 05_pg_remodeling.ipynb ce...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **notebook-id** in `speaker_notes`: `NB03`
  - Context: `...independent appearance in the NB03 late-ChvI cohort, makes Pal t...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **report-md-section** in `speaker_notes`: `REPORT`
  - Context: `... reorganization.' The current REPORT framing is more accurate — pr...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **analysis-layer-code** in `speaker_notes`: `H4`
  - Context: `...-remodeling loci that met the H4 threshold, and the pattern is...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `speaker_notes`: `M23`
  - Context: `...e lipid-II flippase; multiple M23-family endopeptidases includi...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.

### Slide 21 — claim_evidence (slide_id=22)

- **notebook-id** in `bullets[0]`: `NB03`
  - Context: `...4 protein — convergent across NB03 late-ChvI cohort and NB05 H4 ...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **notebook-id** in `bullets[0]`: `NB05`
  - Context: `...oss NB03 late-ChvI cohort and NB05 H4 PG set, the sole gene with...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **analysis-layer-code** in `bullets[0]`: `H4`
  - Context: `...B03 late-ChvI cohort and NB05 H4 PG set, the sole gene with bo...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **notebook-id** in `speaker_notes`: `NB03`
  - Context: `Pal's appearance in both NB03 and NB05 is the key cross-not...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **notebook-id** in `speaker_notes`: `NB05`
  - Context: `...s appearance in both NB03 and NB05 is the key cross-notebook con...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **notebook-id** in `speaker_notes`: `NB03`
  - Context: `...vergence of this substory. In NB03, Pal at CCNA_00784 was a memb...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **notebook-id** in `speaker_notes`: `NB05`
  - Context: `... as a top late-cohort hit. In NB05, the same gene independently ...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.

### Slide 22 — section_divider (slide_id=23)

- **analysis-layer-code** in `speaker_notes`: `A21`
  - Context: `...tion rests on three analyses. A21 and A22 establish the phyloge...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `speaker_notes`: `A22`
  - Context: `...ts on three analyses. A21 and A22 establish the phylogenetic re...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `speaker_notes`: `A23`
  - Context: `...d (NCBI 5,0,0,0 and 6,0,0,0). A23 closes the explanatory loop: ...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `speaker_notes`: `A24`
  - Context: `...in M. catarrhalis (Gao 2008). A24 supplies the method-robustnes...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.

### Slide 23 — methods_summary (slide_id=24)

- **notebook-id** in `bullets[2]`: `NB06`
  - Context: `Initial screen (NB06): PaperBLAST text-mining via ...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **notebook-id** in `bullets[3]`: `NB06b`
  - Context: `Post-review re-test (NB06b): NCBI protein annotation via...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **notebook-id** in `speaker_notes`: `NB06`
  - Context: `...naming, PaperBLAST misses it. NB06 generated the original presen...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **notebook-id** in `speaker_notes`: `NB06b`
  - Context: `... The critical contribution of NB06b was an NCBI annotation re-tes...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.

### Slide 24 — data_figure (slide_id=25)

- **notebook-id** in `caption`: `NB06`
  - Context: `PaperBLAST screen (NB06) across the four-species pane...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **notebook-id** in `caption`: `NB06b`
  - Context: `...ecies panel; NCBI annotation (NB06b) confirms key absences: spt 7...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **notebook-file** in `data_source`: `NB06b_ncbi_annotation_presence.ipynb`
  - Context: `NB06b_ncbi_annotation_presence.ipynb cell 3; Olea-Ozuna 2020/2024;...`
  - Why: Notebook filename (project-internal). Belongs in audit/ logs, not on slides.
  - Fix: Move the path to <draft_dir>/audit/ and replace the slide citation with the underlying paper or cohort reference.
- **notebook-id** in `speaker_notes`: `NB06`
  - Context: `...s the four-species panel from NB06. The NCBI annotation re-test ...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **notebook-id** in `speaker_notes`: `NB06b`
  - Context: `...he NCBI annotation re-test in NB06b confirms the headline biologi...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **notebook-id** in `speaker_notes`: `NB06b`
  - Context: `... respectively — verbatim from NB06b cell 3 and REPORT.md §Finding...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **report-md-section** in `speaker_notes`: `REPORT.md §Finding 6`
  - Context: `...erbatim from NB06b cell 3 and REPORT.md §Finding 6. Note that PaperBLAST showed ...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **analysis-layer-code** in `speaker_notes`: `A23`
  - Context: `...the comparative analysis: the A23 analysis — connecting compara...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `speaker_notes`: `A21`
  - Context: `... The absence data themselves, A21 for sphingolipid and A22 for ...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `speaker_notes`: `A22`
  - Context: `...ves, A21 for sphingolipid and A22 for ChvG-ChvI, are direct evi...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.

### Slide 25 — two_column_compare (slide_id=26)

- **notebook-id** in `speaker_notes`: `NB06`
  - Context: `...tely 9 PaperBLAST hits in our NB06 screen. Caulobacter's surface...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **analysis-layer-code** in `speaker_notes`: `A23`
  - Context: `...without Fur involvement.  The A23 analysis is categorized as pa...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `speaker_notes`: `A21`
  - Context: `...hvI in all three comparators (A21, A22 — both direct evidence) ...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `speaker_notes`: `A22`
  - Context: `...n all three comparators (A21, A22 — both direct evidence) form ...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `speaker_notes`: `A21`
  - Context: `... foundation.  Taken together, A21 through A24 establish that st...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `speaker_notes`: `A24`
  - Context: `...  Taken together, A21 through A24 establish that structural una...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.

### Slide 27 — methods_summary (slide_id=28)

- **analysis-layer-code** in `bullets[0]`: `H1`
  - Context: `Pre-registered hypotheses H1–H4 + comparative arm; thresho...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `bullets[0]`: `H4`
  - Context: `Pre-registered hypotheses H1–H4 + comparative arm; thresholds...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **notebook-id** in `bullets[4]`: `NB06b`
  - Context: `Comparative: NCBI annotation (NB06b) re-confirmed after PaperBLAS...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **notebook-id** in `bullets[6]`: `NB07`
  - Context: `NB07 synthesis notebook integrates...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **notebook-id** in `speaker_notes`: `NB06b`
  - Context: `...notation finds 11 to 18 each. NB06b re-ran the comparative panel ...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **analysis-layer-code** in `speaker_notes`: `H2`
  - Context: `...that background as the formal H2 verdict, using the 198-experi...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.

### Slide 28 — data_table (slide_id=29)

- **notebook-file** in `data_source`: `NB07_synthesis.ipynb`
  - Context: `REPORT.md §Results; NB07_synthesis.ipynb`
  - Why: Notebook filename (project-internal). Belongs in audit/ logs, not on slides.
  - Fix: Move the path to <draft_dir>/audit/ and replace the slide citation with the underlying paper or cohort reference.
- **report-md-section** in `data_source`: `REPORT.md §Results`
  - Context: `REPORT.md §Results; NB07_synthesis.ipynb`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **analysis-layer-code** in `speaker_notes`: `H4`
  - Context: `...ngly: 28 unique loci meet the H4 threshold — 20 down, includin...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.

### Slide 29 — deck_close (slide_id=30)

- **report-md-section** in `data_source`: `REPORT.md §Future directions`
  - Context: `... narrative/00_throughline.md; REPORT.md §Future directions`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **notebook-id** in `speaker_notes`: `NB03`
  - Context: `...and the late ChvI cohort from NB03 gives us a ready candidate ta...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **report-md-section** in `speaker_notes`: `REPORT.md §Future directions`
  - Context: `... narrative/00_throughline.md; REPORT.md §Future directions`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.

### Slide 30 — cross_tenant_integration (slide_id=31)

- **notebook-id** in `speaker_notes`: `NB03`
  - Context: `...nel (Findings 3–6); GO terms (NB03) characterized ChvI phase the...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **notebook-id** in `speaker_notes`: `NB05`
  - Context: `...ized ChvI phase themes, Pfam (NB05) anchored the PG-remodeling g...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **notebook-id** in `speaker_notes`: `NB06b`
  - Context: `...external, NCBI) confirmed the NB06b comparative absence calls tha...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.

### Slide 31 — qa_anticipated (slide_id=32)

- **report-md-section** in `answer_detail`: `REPORT.md §Finding 4 labels this 'suggestive`
  - Context: `... modest and single-replicate. REPORT.md §Finding 4 labels this 'suggestive pilot observation requiring r...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **report-md-section** in `evidence_pointer`: `REPORT.md §Finding 4 protein table (LptD`
  - Context: `REPORT.md §Finding 4 protein table (LptD −0.47, LptE −0.78 log2); §Int...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.

### Slide 32 — qa_anticipated (slide_id=33)

- **notebook-id** in `answer_detail`: `NB02`
  - Context: `...(REPORT §Finding 2 preflight; NB02 cell 5). Testing this axis re...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **report-md-section** in `answer_detail`: `REPORT §Finding 2 preflight`
  - Context: `...experiments are iron-limited (REPORT §Finding 2 preflight; NB02 cell 5). Testing this a...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **analysis-layer-code** in `answer_detail`: `H2`
  - Context: `...ed the iron-limitation arm of H2 explicitly because zero of 19...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **report-md-section** in `evidence_pointer`: `REPORT.md §Limitations L#4 (single growth condition`
  - Context: `REPORT.md §Limitations L#4 (single growth condition, PYE rich-medium routine); §L...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.

### Slide 33 — qa_anticipated (slide_id=34)

- **notebook-id** in `answer_detail`: `NB06`
  - Context: `...ing via kescience_paperblast (NB06, the original screen) and (b)...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **notebook-id** in `answer_detail`: `NB06b`
  - Context: `...otation via Biopython Entrez (NB06b, added post-adversarial-revie...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **notebook-id** in `answer_detail`: `NB06`
  - Context: `...iew correctly identified that NB06 PaperBLAST had ~80% false-neg...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **notebook-id** in `answer_detail`: `NB06b`
  - Context: `...its each for the same genes). NB06b was added to re-confirm compa...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **notebook-id** in `answer_detail`: `NB06b`
  - Context: `...6,0,0,0.  However, REPORT.md §NB06b explicitly documents a second...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **report-md-section** in `answer_detail`: `REPORT.md §NB06b explicitly documents a second-tier`
  - Context: `...,0; ChvI = 6,0,0,0.  However, REPORT.md §NB06b explicitly documents a second-tier caveat: 'NCBI annotation also...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **report-md-section** in `answer_detail`: `REPORT §Future Directions §8: run Pfam`
  - Context: `...definitive closure, stated in REPORT §Future Directions §8: run Pfam HMM searches using profile PF...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **notebook-id** in `evidence_pointer`: `NB06b`
  - Context: `...erR 6,0,0,0 NCBI-confirmed); §NB06b table (PaperBLAST ~80% FN for...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **notebook-id** in `evidence_pointer`: `NB06b`
  - Context: `...A genes; NCBI confirmation); §NB06b naming-convention caveat (Msb...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **report-md-section** in `evidence_pointer`: `REPORT.md §Finding 6 (spt 7`
  - Context: `REPORT.md §Finding 6 (spt 7,0,0,0; cerR 6,0,0,0 NCBI-conf...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.

## Recommended hand-edit pass

Open the .pptx in PowerPoint or LibreOffice. For each hit above, replace the matched text with peer-readable evidence (cohort + sample size + primary author/year for citations; actual claim or method name for analysis-layer codes; nothing for file paths).

This check is **advisory** — the orchestrator does not block on hits. It exists to surface a class of writing failure that consistently slips past the writer prompts.

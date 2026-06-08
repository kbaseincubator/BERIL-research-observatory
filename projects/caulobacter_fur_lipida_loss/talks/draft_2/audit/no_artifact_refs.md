# Process-detail bleed check

Scanned 34 slides for internal-artifact references (notebook IDs, file paths, REPORT.md sections, analysis-layer codes). These patterns make the deck unreadable to fresh peer audiences.

- **Total hits:** 134
- **Slides with hits:** 27/34
- **Hits by pattern:**
  - `report-md-section`: 56
  - `analysis-layer-code`: 52
  - `notebook-id`: 24
  - `notebook-file`: 2

## Per-slide hits

### Slide 4 — section_divider (slide_id=5)

- **notebook-id** in `speaker_notes`: `NB01`
  - Context: `...e Leaden concordance scatter (NB01 cell 5) follows as the direct...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **report-md-section** in `speaker_notes`: `REPORT §Limitations names this single-condition boundary`
  - Context: `...r Fitness Browser compendium. REPORT §Limitations names this single-condition boundary explicitly. It is the key par...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.

### Slide 5 — workflow_diagram (slide_id=6)

- **report-md-section** in `speaker_notes`: `REPORT §Limitations states: "OM proteome is`
  - Context: `... single-replicate per strain. REPORT §Limitations states: "OM proteome is single-replicate per strain —...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.

### Slide 6 — data_figure (slide_id=7)

- **notebook-file** in `data_source`: `NB01_leaden2018_fur_signature.ipynb`
  - Context: `Leaden 2018 (PMID 30210482); NB01_leaden2018_fur_signature.ipynb cell 5`
  - Why: Notebook filename (project-internal). Belongs in audit/ logs, not on slides.
  - Fix: Move the path to <draft_dir>/audit/ and replace the slide citation with the underlying paper or cohort reference.
- **notebook-file** in `speaker_notes`: `NB01_leaden2018_fur_signature.ipynb`
  - Context: `...he same 93 genes, computed in NB01_leaden2018_fur_signature.ipynb cell 5. The Spearman ρ = 0.31...`
  - Why: Notebook filename (project-internal). Belongs in audit/ logs, not on slides.
  - Fix: Move the path to <draft_dir>/audit/ and replace the slide citation with the underlying paper or cohort reference.
- **report-md-section** in `speaker_notes`: `REPORT §Finding 1 frames this as`
  - Context: `...that's a modest correlation." REPORT §Finding 1 frames this as "confirming Fur derepression ...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.

### Slide 7 — claim_evidence (slide_id=8)

- **report-md-section** in `speaker_notes`: `REPORT §Literature Context quotes their language`
  - Context: `...cue requires the Δfur allele. REPORT §Literature Context quotes their language directly: "Alterations in Fur...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **report-md-section** in `speaker_notes`: `REPORT §Limitations names this as a`
  - Context: `...esult must be stated plainly: REPORT §Limitations names this as a single-condition scope bounda...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.

### Slide 8 — section_divider (slide_id=9)

- **report-md-section** in `speaker_notes`: `REPORT §Finding 2 labels it explicitly`
  - Context: `...Path A enrichment is real but REPORT §Finding 2 labels it explicitly "marginally enriched" — the s...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **analysis-layer-code** in `speaker_notes`: `A6`
  - Context: `...s?" That recalibration is the A6 methodological lesson from th...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `speaker_notes`: `H2`
  - Context: `...s; notebook 02b corrected the H2 verdict to use hypergeometric...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.

### Slide 9 — methods_summary (slide_id=10)

- **analysis-layer-code** in `title`: `H2`
  - Context: `...aulobacter genome background (H2 method)`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `bullets[1]`: `H2`
  - Context: `...periments = 0 in compendium — H2 iron arm descoped at prefligh...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `bullets[4]`: `A6`
  - Context: `...ithout background correction (A6: miscalibration lesson)`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **notebook-id** in `bullets[5]`: `NB02b`
  - Context: `H2 verdict recalibrated in NB02b: hypergeometric enrichment vs...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **analysis-layer-code** in `bullets[5]`: `H2`
  - Context: `H2 verdict recalibrated in NB02b...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **report-md-section** in `speaker_notes`: `REPORT §Finding 2 states this explicitly`
  - Context: `... experiments for Caulobacter. REPORT §Finding 2 states this explicitly: "the iron-limitation arm cou...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **report-md-section** in `speaker_notes`: `REPORT §Limitations names this boundary explicitly`
  - Context: `...y to envelope-stress fitness. REPORT §Limitations names this boundary explicitly, and REPORT §Future Direction...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **report-md-section** in `speaker_notes`: `REPORT §Future Directions §6 lists iron-axis`
  - Context: `...this boundary explicitly, and REPORT §Future Directions §6 lists iron-axis RB-TnSeq experiments as a nee...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **analysis-layer-code** in `speaker_notes`: `H2`
  - Context: `... is the step that changed the H2 verdict from a presence check...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `speaker_notes`: `H2`
  - Context: `...e phenotypic axis relevant to H2. Zero experiments are iron-li...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `speaker_notes`: `H2`
  - Context: `...xperiments in the compendium; H2 was descoped to envelope-axis...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `speaker_notes`: `H2`
  - Context: `...ersarial review surfaced. The H2 verdict was recalibrated in n...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.

### Slide 10 — data_table (slide_id=11)

- **report-md-section** in `data_source`: `REPORT.md §Finding 2`
  - Context: `REPORT.md §Finding 2; notebooks/02b_h2_hypergeomet...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **report-md-section** in `speaker_notes`: `REPORT §Finding 2 and notebook 02b_h2_hypergeometric_verdict`
  - Context: `...number in it is verbatim from REPORT §Finding 2 and notebook 02b_h2_hypergeometric_verdict.ipynb cell 2.  The genome bac...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **report-md-section** in `speaker_notes`: `REPORT §Finding 2 describes this as`
  - Context: `...ound, hypergeometric p=0.016. REPORT §Finding 2 describes this as "marginal but real enrichment...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **report-md-section** in `speaker_notes`: `REPORT`
  - Context: `... genes), fold 1.04×, p=0.515. REPORT labels this "indistinguishabl...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **report-md-section** in `speaker_notes`: `REPORT`
  - Context: `...ll the Path A enrichment what REPORT calls it: marginal. Fold 1.60...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **report-md-section** in `speaker_notes`: `REPORT §Finding 2 states: "Path B`
  - Context: `...chment, not a power artifact. REPORT §Finding 2 states: "Path B (the SspB-buffered respirator...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **analysis-layer-code** in `speaker_notes`: `H2`
  - Context: `...his two-row table is the core H2 result. The contrast between ...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.

### Slide 11 — claim_evidence (slide_id=12)

- **notebook-id** in `bullets[1]`: `NB01`
  - Context: `...level SspB buffering is real (NB01: 53/93 Leaden Δfur DEGs blunt...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **report-md-section** in `speaker_notes`: `REPORT §Limitations states: "The fitness data`
  - Context: `... envelope-stress experiments. REPORT §Limitations states: "The fitness data do not selectively support th...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **report-md-section** in `speaker_notes`: `REPORT §Interpretation §2 demotes the respiratory`
  - Context: `...genes under envelope stress." REPORT §Interpretation §2 demotes the respiratory arm explicitly: "The 'respira...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.

### Slide 12 — section_divider (slide_id=13)

- **analysis-layer-code** in `speaker_notes`: `H1`
  - Context: `...s robust and descriptive. The H1 phase-structure verdict is SU...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.

### Slide 13 — methods_summary (slide_id=14)

- **analysis-layer-code** in `bullets[4]`: `H1`
  - Context: `...genes per cohort required for H1 phase-structure verdict (RESE...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `bullets[6]`: `N3`
  - Context: `...lich 2018; adversarial review N3) acknowledged as untested pos...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `speaker_notes`: `H1`
  - Context: `...-registered threshold for the H1 phase-structure verdict was ≥...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `speaker_notes`: `H1`
  - Context: `...rt (RESEARCH_PLAN §hypotheses H1). This prevents a handful of ...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `speaker_notes`: `H1`
  - Context: `...e threshold strongly, and the H1 verdict is SUPPORTED. The Sig...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `speaker_notes`: `H1`
  - Context: `...e test was the pre-registered H1 sub-hypothesis: if SigU is th...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `speaker_notes`: `N3`
  - Context: `...ance. The adversarial review (N3) flagged ChvR sRNA as a post-...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.

### Slide 14 — data_table (slide_id=15)

- **report-md-section** in `data_source`: `REPORT.md §Finding 3`
  - Context: `REPORT.md §Finding 3; nb 03_chvi_phase_partition_s...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **notebook-id** in `speaker_notes`: `NB03`
  - Context: `...im from REPORT §Finding 3 and NB03 cell 7; together they total 7...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **report-md-section** in `speaker_notes`: `REPORT §Finding 3 and NB03 cell`
  - Context: `... All counts are verbatim from REPORT §Finding 3 and NB03 cell 7; together they total 79 Chv...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **analysis-layer-code** in `speaker_notes`: `H1`
  - Context: `...nsequence genes — is the core H1 result. All counts are verbat...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.

### Slide 15 — claim_evidence (slide_id=16)

- **analysis-layer-code** in `bullets[0]`: `H1`
  - Context: `...and statistical significance; H1 SigU sub-hypothesis is not su...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `bullets[2]`: `N3`
  - Context: `...lich 2018, adversarial review N3) is an untested post-transcri...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **notebook-id** in `speaker_notes`: `NB03`
  - Context: `...RESEARCH_PLAN §hypotheses H1, NB03 cell 10) returned 24.5% envel...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **report-md-section** in `speaker_notes`: `REPORT §Finding 3: "The reframed SigU`
  - Context: `...nes with Fisher p=0.243. From REPORT §Finding 3: "The reframed SigU coherence check on the late c...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **report-md-section** in `speaker_notes`: `REPORT §Limitations: "even the relaxed criterion`
  - Context: `... 50% relaxed criterion." From REPORT §Limitations: "even the relaxed criterion did not pass (Fisher p=0.243)...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **report-md-section** in `speaker_notes`: `REPORT`
  - Context: `...A-seq in the 4599 background (REPORT Future Directions §2). That e...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **analysis-layer-code** in `speaker_notes`: `H1`
  - Context: `...st (RESEARCH_PLAN §hypotheses H1, NB03 cell 10) returned 24.5%...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `speaker_notes`: `N2`
  - Context: `...e broadly. Adversarial review N2 corrected an earlier framing ...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `speaker_notes`: `N3`
  - Context: `...flagged by adversarial review N3, adds a second source of late...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.

### Slide 17 — methods_summary (slide_id=18)

- **analysis-layer-code** in `bullets[2]`: `F2`
  - Context: `...6 IM transporter genes (lptG2/F2/C2) tested for induction vs c...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `bullets[2]`: `C2`
  - Context: `...M transporter genes (lptG2/F2/C2) tested for induction vs cons...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `bullets[4]`: `H4`
  - Context: `... hydrolase families); 28 meet H4 threshold (FDR < 0.05 OR |log...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **report-md-section** in `speaker_notes`: `REPORT §Limitations states this directly: "OM`
  - Context: `...nalyzed by mass spectrometry. REPORT §Limitations states this directly: "OM proteome is single-replicate ...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.

### Slide 18 — data_figure (slide_id=19)

- **report-md-section** in `data_source`: `REPORT.md §Finding 4`
  - Context: `REPORT.md §Finding 4; notebooks/04_sphingolipid_lp...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **report-md-section** in `speaker_notes`: `REPORT`
  - Context: `...sted as Future Direction 4 in REPORT.  The biochemical literature ...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.

### Slide 19 — two_column_compare (slide_id=20)

- **analysis-layer-code** in `speaker_notes`: `A14`
  - Context: `...rtial grade on this analysis (A14) is honestly earned. The LptD...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.

### Slide 20 — claim_evidence (slide_id=21)

- **report-md-section** in `speaker_notes`: `REPORT §Finding 4 records it as`
  - Context: `...A-loss-driven CtpA induction. REPORT §Finding 4 records it as a supplemental observation co...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **report-md-section** in `speaker_notes`: `REPORT`
  - Context: `...targeted lipidomics listed in REPORT Future Directions 1 and 4. Ho...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.

### Slide 21 — data_figure (slide_id=22)

- **analysis-layer-code** in `caption`: `H4`
  - Context: `...f 53 pre-curated loci meeting H4 threshold); 20 DOWN (division...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **report-md-section** in `data_source`: `REPORT.md §Finding 5`
  - Context: `REPORT.md §Finding 5; notebooks/05_pg_remodeling.i...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **notebook-id** in `speaker_notes`: `NB05`
  - Context: `...ally, Pal appears in both the NB05 PG remodeling analysis and as...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **notebook-id** in `speaker_notes`: `NB03`
  - Context: `...op late-cohort ChvI gene from NB03, providing strong cross-noteb...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **analysis-layer-code** in `speaker_notes`: `H4`
  - Context: `...20 of the 28 loci meeting the H4 threshold are significantly d...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `speaker_notes`: `M23`
  - Context: `...multiple LdpD, LdpE, and LdpF M23-family endopeptidases; amiC a...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `speaker_notes`: `A20`
  - Context: `...y LPS.  The ⚠ partial caveat (A20) applies at the protein level...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.

### Slide 22 — section_divider (slide_id=23)

- **notebook-id** in `speaker_notes`: `NB06b`
  - Context: `...ble because understanding why NB06b replaced NB06 is prerequisite...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **notebook-id** in `speaker_notes`: `NB06`
  - Context: `...erstanding why NB06b replaced NB06 is prerequisite to reading th...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **analysis-layer-code** in `speaker_notes`: `A21`
  - Context: `...The comparative-genomics arm (A21/A22) is direct evidence, grad...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `speaker_notes`: `A22`
  - Context: `...comparative-genomics arm (A21/A22) is direct evidence, graded b...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `speaker_notes`: `A23`
  - Context: `...nnotation; its method caveat (A23) is partial — annotation-scop...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `speaker_notes`: `A26`
  - Context: `...rified. The graded synthesis (A26) is partial, only as strong a...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `speaker_notes`: `A27`
  - Context: `...The pre-registered scorecard (A27) is direct — the discipline t...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.

### Slide 23 — methods_summary (slide_id=24)

- **notebook-id** in `bullets[1]`: `NB06`
  - Context: `NB06 (screen): PaperBLAST text-mat...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **notebook-id** in `bullets[2]`: `NB06b`
  - Context: `NB06b (authoritative): Biopython En...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **notebook-id** in `speaker_notes`: `NB06`
  - Context: `...e appears, the evolution from NB06 to NB06b requires a brief exp...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **notebook-id** in `speaker_notes`: `NB06b`
  - Context: `...s, the evolution from NB06 to NB06b requires a brief explanation,...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **notebook-id** in `speaker_notes`: `NB06`
  - Context: `...ly 80% false-negative rate in NB06 for Caulobacter's own lipid A...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **notebook-id** in `speaker_notes`: `NB06`
  - Context: `...ynthesis genes.  The original NB06 used PaperBLAST text-matching...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **notebook-id** in `speaker_notes`: `NB06b`
  - Context: `...ion-text matching relies on.  NB06b, added post-review, reran the...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **report-md-section** in `speaker_notes`: `REPORT §Finding 6 (Method check row`
  - Context: `... names and function keywords. REPORT §Finding 6 (Method check row) documents the specific false...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **report-md-section** in `speaker_notes`: `REPORT §Future Directions §8 specifies the`
  - Context: `... than canonical gene symbols. REPORT §Future Directions §8 specifies the full-rigor next step: HMM-bas...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.

### Slide 24 — data_table (slide_id=25)

- **notebook-id** in `caption`: `NB06b`
  - Context: `NCBI annotation hit counts (NB06b); 0 hits in all three compara...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **report-md-section** in `data_source`: `REPORT.md §Finding 6`
  - Context: `REPORT.md §Finding 6; notebooks/06b_ncbi_annotatio...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **notebook-id** in `speaker_notes`: `NB06b`
  - Context: `...terpretation §9, confirmed in NB06b cell 5: spt (serine palmitoyl...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **report-md-section** in `speaker_notes`: `REPORT §Finding 6 and §Interpretation §9`
  - Context: `...tion hits in every row.  From REPORT §Finding 6 and §Interpretation §9, confirmed in NB06b cell 5: s...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.

### Slide 25 — claim_evidence (slide_id=26)

- **report-md-section** in `bullets[0]`: `REPORT`
  - Context: `... is the full-rigor next step (REPORT Future Directions §8)`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **analysis-layer-code** in `bullets[0]`: `A23`
  - Context: `Scope caveat (A23, partial): NCBI annotation us...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **notebook-id** in `bullets[1]`: `NB06b`
  - Context: `... (LpxC: 0 PB hits, 15 NCBI) — NB06b confirms comparator absences ...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **analysis-layer-code** in `bullets[2]`: `N1`
  - Context: `...lobacter* (adversarial review N1) — core biosynthesis entry (s...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **notebook-id** in `speaker_notes`: `NB06b`
  - Context: `... in the plan, graded partial. NB06b reports annotation-based pres...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **report-md-section** in `speaker_notes`: `REPORT §Limitations states explicitly that the`
  - Context: `...onical Gram-negative symbols. REPORT §Limitations states explicitly that the annotation-based search is "c...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **report-md-section** in `speaker_notes`: `REPORT §Future Directions §8`
  - Context: `...urs via the CDM Task Service (REPORT §Future Directions §8). That search has not been ru...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **analysis-layer-code** in `speaker_notes`: `A23`
  - Context: `... at full value.  The first is A23 in the plan, graded partial. ...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `speaker_notes`: `A17`
  - Context: `...verified.  The second flag is A17, the sphk named exception, su...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `speaker_notes`: `N1`
  - Context: `...urfaced by adversarial review N1. Sphingosine kinase (sphk) re...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.

### Slide 26 — data_figure (slide_id=27)

- **report-md-section** in `data_source`: `REPORT.md §Results (Hypothesis scorecard) and §Interpretation`
  - Context: `REPORT.md §Results (Hypothesis scorecard) and §Interpretation §1-9; notebooks/07_synthesis....`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **notebook-id** in `speaker_notes`: `NB07`
  - Context: `The four-panel NB07 synthesis figure closes the t...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **report-md-section** in `speaker_notes`: `REPORT §Results (hypothesis scorecard`
  - Context: `...rs in presentation order from REPORT §Results (hypothesis scorecard, 18-row table) and §Interpret...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **report-md-section** in `speaker_notes`: `REPORT §Finding 4 as a supplemental`
  - Context: `...st at FDR = 0.035 is noted in REPORT §Finding 4 as a supplemental observation consistent with C...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **report-md-section** in `speaker_notes`: `REPORT`
  - Context: `... by the Future Directions the REPORT specifies — replicated proteo...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **analysis-layer-code** in `speaker_notes`: `H1`
  - Context: `...dependently dataset-grounded. H1 phase structure: unique-early...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `speaker_notes`: `H2`
  - Context: `...gistered relaxed bar of ≥50%. H2 Path A: fold 1.60×, hypergeom...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `speaker_notes`: `H3`
  - Context: `...arm is demoted to hypothesis. H3 CtpA: logFC +0.58, pvalue = 0...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `speaker_notes`: `H4`
  - Context: `...DR 0.02 — SUPPORTED strongly. H4 PG remodeling: 28 unique loci...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `speaker_notes`: `A26`
  - Context: `....  The mechanistic synthesis (A26, partial) integrates these he...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `speaker_notes`: `A27`
  - Context: `...The pre-registered scorecard (A27, direct) is the discipline th...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.

### Slide 27 — deck_close (slide_id=28)

- **report-md-section** in `data_source`: `REPORT.md §Future directions`
  - Context: `... narrative/00_throughline.md; REPORT.md §Future directions`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **notebook-id** in `speaker_notes`: `NB03`
  - Context: `...and the late ChvI cohort from NB03 hands us a ready candidate li...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **report-md-section** in `speaker_notes`: `REPORT.md §Future directions`
  - Context: `... narrative/00_throughline.md; REPORT.md §Future directions`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.

### Slide 28 — cross_tenant_integration (slide_id=29)

- **notebook-id** in `speaker_notes`: `NB06b`
  - Context: `... annotation-presence panel in NB06b that confirmed sphingolipid p...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.

### Slide 29 — qa_anticipated (slide_id=30)

- **report-md-section** in `answer_summary`: `REPORT §Limitations`
  - Context: `... our explicit scope boundary (REPORT §Limitations). Constitutivity is anchored ...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **notebook-id** in `answer_detail`: `NB01`
  - Context: `...tutively. Leaden et al. 2018 (NB01 cell 7, figures/NB01_leaden_i...`
  - Why: Notebook ID (project-internal). Peer audiences don't read your notebook inventory.
  - Fix: Replace with the cohort + sample size + primary author/year, e.g. 'NB04h' → 'Lloyd-Price 2019 (HMP2 cohort, n=1,627)'.
- **report-md-section** in `answer_detail`: `REPORT §Limitations states explicitly: 'The transcriptome`
  - Context: `...y under nutrient limitation.  REPORT §Limitations states explicitly: 'The transcriptome is from a single PYE-rich gro...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **report-md-section** in `answer_detail`: `REPORT`
  - Context: `... — is the required next step (REPORT Future Directions §6: iron-ax...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **analysis-layer-code** in `answer_detail`: `A2`
  - Context: `... deck: it applies not just to A2 (the iron-limitation discrimi...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **report-md-section** in `evidence_pointer`: `REPORT.md §Limitations bullet 4 (single growth`
  - Context: `REPORT.md §Limitations bullet 4 (single growth condition, PYE rich); REPORT....`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **report-md-section** in `evidence_pointer`: `REPORT.md §Finding 1 (Leaden concordance and`
  - Context: `... growth condition, PYE rich); REPORT.md §Finding 1 (Leaden concordance and iron-vs-Δfur discrimination);...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.

### Slide 30 — qa_anticipated (slide_id=31)

- **report-md-section** in `answer_summary`: `REPORT §Finding 4`
  - Context: `...al and explicitly unresolved (REPORT §Finding 4, §Limitations). Two interpret...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **report-md-section** in `answer_detail`: `REPORT §Finding 4: LptD (CCNA_01760) log2(4672/4659`
  - Context: `The exact numbers from REPORT §Finding 4: LptD (CCNA_01760) log2(4672/4659) = −0.47, log2(4672/4580) = −...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **report-md-section** in `answer_detail`: `REPORT`
  - Context: `...way. This is labeled PILOT in REPORT (single replicate, summer 202...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **report-md-section** in `answer_detail`: `REPORT §Limitations explicitly states that LptD/LptE`
  - Context: `...roteomics will resolve this.' REPORT §Limitations explicitly states that LptD/LptE protein decline and lptC2 pro...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **analysis-layer-code** in `answer_detail`: `F2`
  - Context: `...-specific Lpt paralogs (lptG2/F2/C2, Uchendu 2026) handle CPG ...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **analysis-layer-code** in `answer_detail`: `C2`
  - Context: `...ecific Lpt paralogs (lptG2/F2/C2, Uchendu 2026) handle CPG tra...`
  - Why: Looks like a project-internal analysis-layer code (A16, H3c, L13). Reads as jargon to peers; the underlying claim is what they need.
  - Fix: Replace with what the code REFERS TO — e.g., 'L13' → 'comparator-choice sensitivity analysis'. If the code is defined elsewhere on the deck, define it inline; if not, state the actual finding.
- **report-md-section** in `evidence_pointer`: `REPORT.md §Finding 4 (Lpt apparatus protein`
  - Context: `REPORT.md §Finding 4 (Lpt apparatus protein table: LptD log2 −0.47/−0.62,...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **report-md-section** in `evidence_pointer`: `REPORT.md §Limitations bullet 2 (single-replicate OM`
  - Context: `...ptC-related +0.56 FDR 0.005); REPORT.md §Limitations bullet 2 (single-replicate OM proteome, direction only); nb...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.

### Slide 31 — qa_anticipated (slide_id=32)

- **report-md-section** in `answer_summary`: `REPORT`
  - Context: `...th A enrichment 'marginal' in REPORT and claim only that it clears...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **report-md-section** in `answer_detail`: `REPORT`
  - Context: `...ypergeometric enrichment from REPORT data and obtained fold = 1.59...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **report-md-section** in `answer_detail`: `REPORT`
  - Context: `...irect lipidomic verification (REPORT Future Directions §4) before ...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.
- **report-md-section** in `evidence_pointer`: `REPORT.md §Finding 2 (enrichment table: Path`
  - Context: `REPORT.md §Finding 2 (enrichment table: Path A fold 1.60×, p=0.016 vs back...`
  - Why: Reference to REPORT.md (project-internal documentation). Peers don't have access to your REPORT.
  - Fix: Replace with the underlying citation (paper + author + year) or, if the result is original to this project, present it directly without the meta-citation.

## Recommended hand-edit pass

Open the .pptx in PowerPoint or LibreOffice. For each hit above, replace the matched text with peer-readable evidence (cohort + sample size + primary author/year for citations; actual claim or method name for analysis-layer codes; nothing for file paths).

This check is **advisory** — the orchestrator does not block on hits. It exists to surface a class of writing failure that consistently slips past the writer prompts.

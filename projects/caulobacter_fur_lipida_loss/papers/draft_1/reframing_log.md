# Reframing Log

## 2026-06-04 — P0 remediation, surgical

### F001 — Figure 5 alt-text correction (post-adversarial)

REPORT v3 corrected the H4 framing from earlier "coordinated bidirectional reorganization" to "predominantly downregulation (20 of 28 significant loci) punctuated by specific lytic inductions including SdpA and Pal." The first draft of `manuscript.md` carried over the earlier framing in the Figure 5 image alt-text on line 140. The alt-text has been updated to match REPORT v3's corrected framing. This is acknowledged drift, not silent drift: REPORT itself had been updated in response to the round-1 adversarial review of the project (see project-level `ADVERSARIAL_REVIEW_1.md`), and the manuscript drafter pulled from an earlier conceptual frame.

### F004 — Methods Software and reproducibility (additive, not reframing)

Added a "Software and reproducibility" subsection at the end of Methods listing version numbers for SeqCenter's edgeR/HISAT2 pipeline (from REPORT.md provenance) and the downstream Python toolchain on JupyterHub (versions retrieved from the live `python -c "import …; print(…__version__)"` introspection in the BERDL kernel at draft time). This addresses an adversarial-review reproducibility-blocker finding; it does not reframe any biological claim from REPORT.md.

---
reviewer: BERIL Automated Review (Claude, claude-sonnet-4-20250514)
date: 2026-05-08
project: harvard_forest_warming
---

# Review: Harvard Forest Long-Term Warming — DNA vs RNA Functional Response

## Summary

This is an exemplary BERDL project that demonstrates rigorous scientific methodology, clear communication, and reproducible analysis. The research addresses a well-defined question about functional responses to long-term soil warming using multi-omics data from Harvard Forest's 25-year warming experiment. While the primary hypothesis (H1) that RNA responses exceed DNA responses was not supported, the project makes several valuable contributions: it reproduces published compositional findings (Actinobacteria up, Acidobacteria down), identifies novel methanotrophy and glyoxylate cycle signals, and provides the first direct DNA-vs-RNA comparison at this important field site. The work is technically sound, thoroughly documented, and honestly interpreted with appropriate acknowledgment of limitations.

## Methodology

**Research Design**: The three linked hypotheses (H1: RNA > DNA functional divergence; H2: C-cycling enrichment; H3: horizon interactions) are clearly stated, testable, and grounded in published literature. The factorial design effectively leverages treatment × horizon × incubation factors across 42 biosamples from NMDC study `nmdc:sty-11-8ws97026`.

**Data Sources**: Excellent use of BERDL's `nmdc` tenant with clear documentation of all tables used. The restriction to `nmdc_metadata` and `nmdc_results` (excluding `nmdc_arkin`) is well-justified and maintains analytical focus. All data lineage is clearly traceable from NMDC study ID through workflow runs to final results.

**Analytical Approach**: The statistical methods are appropriate and well-implemented. The custom PERMANOVA implementation is mathematically correct, the use of Bray-Curtis distances is suitable for compositional data, and permutation tests provide appropriate significance testing. The H1 sensitivity analysis (direct samples only, removing horizon × incubation confound) demonstrates careful consideration of experimental design issues.

**Reproducibility**: Outstanding reproducibility documentation. The README provides clear step-by-step reproduction instructions, runtime estimates (~15-20 minutes), and platform requirements. The `requirements.txt` specifies appropriate dependencies with version bounds.

## Code Quality

**Statistical Rigor**: The statistical implementations are sound. The PERMANOVA function correctly implements Anderson (2001) methodology with proper permutation testing. The Procrustes analysis appropriately tests configuration alignment, and the centroid distance calculations provide meaningful effect size comparisons. Custom implementations are preferred over black-box packages where appropriate.

**Data Handling**: Excellent practices throughout. The KO matrix alignment (union of DNA and RNA KO sets with zero-filling) is handled correctly with proper re-normalization. The biosample design parsing using regex is robust and well-validated. Compositional data is appropriately converted to relative abundances before distance calculations.

**Notebook Organization**: The 8-notebook pipeline follows logical progression from sample design through synthesis. Each notebook has clear goals, proper documentation with markdown cells, and saves intermediate results appropriately. The heavy Spark extraction is properly isolated to NB02, allowing downstream notebooks to run locally.

**NMDC Best Practices**: The project avoids common NMDC pitfalls. It properly uses `biosample_set_associated_studies` with `parent_id` joins, filters annotation tables by `workflow_run_id` to avoid full scans, and handles the workflow type mapping correctly. No evidence of the alias conflicts or data type issues documented in `docs/pitfalls.md`.

## Findings Assessment

**Conclusions Well-Supported**: All major findings are backed by appropriate statistical evidence. The reproduction of published Actinobacteria/Acidobacteria signals (q=0.049 BH-FDR) validates both the data and methods. The H1 non-support is convincingly demonstrated with proper sensitivity analyses removing confounding factors.

**Honest Interpretation**: The project exemplifies scientific integrity. H1's failure is thoroughly analyzed with four plausible mechanistic explanations rather than dismissed. The distinction between FDR-significant results (few, due to sample size) and biologically interpretable nominal signals (methanotrophy, glyoxylate cycle) is clearly communicated.

**Novel Contributions**: The methanotrophy upregulation (pmoA/pmoB, log2 FC +0.7-0.9, p=0.009-0.054) and glyoxylate cycle activation (aceA/aceB in mineral horizon, both p=0.037) represent genuinely new findings at this site. These are biologically coherent and supported by literature from other warming experiments.

**Literature Integration**: Excellent contextualization of findings within the broader Harvard Forest warming literature and forest warming research generally. The connection to substrate depletion models (Domeignoz-Horta et al. 2022) and the metabolite richness reduction provide mechanistic coherence.

**Limitations Acknowledged**: Comprehensive discussion of constraints including single timepoint, sample size limitations precluding FDR significance for many KOs, and the horizon × incubation confound in some comparisons. The authors are appropriately cautious about interpretation scope.

## Suggestions

1. **ChEBI label resolution**: The metabolite analysis identifies significant patterns (heated mineral samples have fewer detectable metabolites, p=0.012) but lacks compound identification. Consider using the OLS MCP server to resolve ChEBI IDs to chemical names and functional classes for the top differential hits (ChEBI:71028, ChEBI:30918, ChEBI:27967).

2. **Cross-study validation**: The methanotrophy signal could be strengthened by checking other NMDC warming studies (SPRUCE peatland `nmdc:sty-11-33fbta56`, Alaskan permafrost `nmdc:sty-11-db67n062`) for pmoA/pmoB patterns to test generalizability across ecosystems.

3. **MAG-level analysis**: The 298 MAGs from this study could provide taxonomic context for the pmoA/pmoB signals. Which specific lineages carry these upregulated methanotrophy genes? This would connect to the Choudoir et al. 2025 pangenome findings.

4. **Effect size reporting**: Consider adding standardized effect sizes (Cohen's d or similar) alongside the log2 fold changes to aid interpretation and comparison with other studies.

5. **Seasonal context**: While acknowledged as a limitation, briefly discussing how the May sampling timepoint (peak spring activity) might affect the transcript-level signals would help interpret the H1 findings.

## Review Metadata

- **Reviewer**: BERIL Automated Review (Claude, claude-sonnet-4-20250514)
- **Date**: 2026-05-08
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, 8 notebooks, 42 data files, 9 figures
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.
---
reviewer: BERIL Automated Review (Claude, claude-sonnet-4-20250514)
date: 2026-04-28
project: metal_cross_resistance
---

# Review: Gene-Resolution Metal Cross-Resistance Across Diverse Bacteria

## Summary

This project provides a compelling gene-resolution analysis of metal cross-resistance across 28 phylogenetically diverse bacterial organisms. The work successfully demonstrates that metal cross-resistance is largely universal and directionally conserved (H1 strongly supported) and that genes decompose into a meaningful three-tier architecture with a clear core enrichment gradient (H2 supported). The analysis represents an unprecedented scale (28 organisms, 13 metals, 119,561 genes) and provides novel insights into the genetic architecture underlying cross-resistance patterns. While the BacDive validation (H3) is underpowered at the current scale, the project establishes a solid foundation for future pangenome-scale validation and delivers significant methodological and scientific advances.

## Methodology

**Research question and approach**: The core research question—whether genetic architecture of metal cross-resistance is conserved across bacteria or rewired species-specifically—is well-formulated and directly testable. The three-hypothesis structure (H1: conservation, H2: core enrichment gradient, H3: BacDive validation) provides clear success criteria.

**Data sources and scale**: The project leverages the Fitness Browser's RB-TnSeq data across 28 organisms and up to 13 metals, representing a 100× increase in resolution over prior MIC-based studies. The data selection criteria (≥3 metals per organism) are appropriate and well-justified.

**Analytical approach**: The methodology is sound throughout: Pearson correlations for cross-resistance matrices, Mantel tests for conservation assessment, and permutation testing for significance. The three-tier gene classification (general stress > metal-shared > metal-specific) based on fitness profiles and sick rates is novel and biologically meaningful. The leave-one-out consensus prediction provides a rigorous test of universal applicability.

**Statistical rigor**: All statistical tests are appropriate for the data types and research questions. The permutation test design correctly addresses the challenge that all correlations are positive—the null hypothesis tests metal-label specificity, not correlation direction. Multiple testing considerations are handled appropriately with false discovery rate corrections where needed.

**Known pitfalls addressed**: The project correctly addresses critical BERDL pitfalls identified in `docs/pitfalls.md`: all Fitness Browser columns are properly cast to FLOAT, locusId types are consistently converted to strings, and organism-level filtering is applied before complex queries. The analysis appropriately excludes organisms with <3 metals from the tier analysis to maintain statistical validity.

## Reproducibility

**Notebook outputs**: Excellent—all five notebooks contain comprehensive outputs including tables, statistics, and visualizations. Each notebook clearly documents its purpose, environment requirements, and expected outputs. The progression from data extraction (NB01) through cross-resistance analysis (NB02-03) to gene architecture (NB04) and validation (NB05) is logical and well-structured.

**Figures**: The `figures/` directory contains all 11 expected visualizations referenced in the notebooks and REPORT.md. Key figures include the DvH cross-resistance heatmap, multi-organism panels, conservation boxplots, hierarchical clustering dendrograms, core enrichment gradient plots, and BacDive validation attempts. Visualizations are publication-quality with appropriate annotations and statistical results.

**Data files**: All expected data files are present in `data/` with 18 main files plus subdirectories for per-organism matrices (30 files) and cross-resistance matrices (28 files). The data structure follows BERIL conventions with clear naming and appropriate formats.

**Dependencies**: The project includes `requirements.txt` and clearly documents environment requirements. Notebooks requiring Spark are properly identified, and the progression from Spark-dependent extraction to local analysis is well-structured.

**Reproduction guide**: The README provides clear step-by-step instructions with expected runtimes and environment requirements. The data dependencies on other projects (`essential_genome`) are properly documented with fallback paths to lakehouse storage.

## Code Quality

**SQL queries**: SQL queries are well-written with appropriate CAST statements for string-typed Fitness Browser columns, proper filtering by `orgId`, and efficient join strategies. The metal experiment classification logic handles inconsistent naming conventions appropriately.

**Statistical methods**: Statistical approaches are appropriate throughout: Pearson correlations for gene-metal relationships, Mantel tests for matrix comparisons, permutation testing with proper null models, and Spearman correlations for non-parametric relationships. The variance decomposition approach quantifies organism-specific vs. chemistry-driven components effectively.

**Notebook organization**: Each notebook follows a logical flow from data loading through analysis to visualization and interpretation. Code cells are appropriately sized, and markdown documentation provides clear explanations of methods and findings.

**Error handling**: The analysis includes appropriate safeguards such as checking for file existence before loading, handling organisms with insufficient data gracefully, and validating matrix dimensions before correlation calculations.

## Findings Assessment

**Conclusions well-supported**: The main conclusions are strongly supported by the data presented:
- H1 (conservation): 98.1% of correlations positive, >90% sign consistency across all metal pairs, significant Mantel correlations
- H2 (core gradient): Clear 92.0% → 91.0% → 89.8% gradient with 11.5 percentage point spread in fully core genes
- H3 (BacDive): Appropriately acknowledged as underpowered (n=20 species) and requiring pangenome-scale analysis

**Novel contributions**: The project makes several significant contributions: first gene-resolution cross-resistance analysis, demonstration of universal positivity in metal-metal correlations, identification of 318 conserved cross-resistance gene families, and quantification of chemistry-specific vs. organism-specific variance components.

**Limitations acknowledged**: The authors appropriately acknowledge key limitations: metal concentration variations across experiments, unequal experiment counts per organism, phylogenetic non-independence, and insufficient power for BacDive validation at current scale.

**Literature context**: The findings are properly contextualized against classical work (Nies 1999, 2003) while highlighting the unprecedented scale and resolution. The connection to the Metal Fitness Atlas and related observatory projects provides appropriate scientific context.

## Suggestions

1. **Expand phylogenetic controls**: Implement phylogenetic generalized least squares (PGLS) or phylogenetic independent contrasts to formally account for evolutionary relationships when testing cross-resistance conservation.

2. **Dose-response normalization**: Consider normalizing fitness effects by metal concentration relative to MIC to control for dose-response confounds across experiments.

3. **Pangenome-scale H3 validation**: Apply the cross-resistance gene signatures to predict multi-metal tolerance across the full 27K pangenome species using KEGG/PFAM mapping, then validate against BacDive at sufficient scale for statistical power.

4. **ICA module decomposition**: Apply independent component analysis (from the fitness_modules project) specifically to metal conditions to identify co-regulated metal-response modules and test whether cross-resistance genes cluster into coherent regulatory units.

5. **Structural biology integration**: Use AlphaFold structures to investigate whether metal-shared proteins have specific structural features (metal binding sites, membrane interfaces) that explain multi-metal sensitivity.

6. **Cross-reference counter-ion effects**: Explicitly compare the cross-resistance hierarchy with the counter_ion_effects project findings to validate that the same mechanistic groupings emerge from metal-metal vs. metal-NaCl correlations.

## Review Metadata

- **Reviewer**: BERIL Automated Review (Claude, claude-sonnet-4-20250514)
- **Date**: 2026-04-28
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, 5 notebooks, 11 figures, 18 data files, requirements.txt
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.
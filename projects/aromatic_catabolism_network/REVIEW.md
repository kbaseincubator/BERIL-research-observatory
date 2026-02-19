---
reviewer: BERIL Automated Review
date: 2026-02-19
project: aromatic_catabolism_network
---

# Review: Aromatic Catabolism Support Network in ADP1

## Summary

This is a strong project that systematically investigates why aromatic catabolism in *Acinetobacter baylyi* ADP1 requires a 51-gene support network spanning Complex I, iron acquisition, and PQQ biosynthesis beyond the 6 core pathway enzymes. The analysis progresses logically through four notebooks: FBA-based metabolic dependency mapping, genomic organization and operon prediction, co-fitness network analysis for functional assignment of unknown genes, and cross-species validation via ortholog-transferred fitness data. The project produces a clear, biologically coherent model with an important nuance from the cross-species work: the Complex I dependency is on high-NADH-flux substrates generally, not aromatics exclusively. Documentation is thorough across README, RESEARCH_PLAN, and REPORT. All notebooks have saved outputs, 9 figures and 7 data files are generated, and a `requirements.txt` is provided. The main areas for improvement are: the `categorize_gene()` function is duplicated across 3 notebooks instead of being imported from the existing `utils.py` (which already contains a corrected version), the interaction test for Complex I aromatic specificity relies on only 5 genes, and the co-fitness assignment confidence scheme deserves clearer justification given the limited 8-condition dimensionality.

## Methodology

**Research question and hypotheses**: The research question is clearly stated and testable. The explicit null (H0: quinate-specific defects are artifacts) vs alternative (H1: coherent metabolic dependency network) hypothesis structure in RESEARCH_PLAN.md provides a rigorous framework. The identification of potential confounders (growth ratio non-linearity, quinate's unusually high mean growth ratio, general Complex I importance for aerobic respiration) is a notable strength.

**Multi-evidence approach**: The four-aim design is well-conceived. Each notebook contributes independently:
- NB01: Establishes biochemical logic via FBA predictions and identifies model blind spots
- NB02: Tests genomic co-localization (finds the subsystems are physically independent)
- NB03: Provides functional grouping via co-fitness and reassigns 16 unknown genes
- NB04: Tests generality across species and reveals that the dependency is NADH-flux-based, not exclusively aromatic

This convergent evidence structure is appropriate for the question.

**Data sources**: Clearly identified in README and RESEARCH_PLAN. The project depends on a local SQLite database (`berdl_tables.db`, 136 MB) from a prior project and on ortholog-transferred fitness scores. The dependency chain (adp1_deletion_phenotypes -> this project) is documented.

**Concern -- keyword categorization is fragile and inconsistently fixed**: The `categorize_gene()` function in NB01 (cell 1), NB02 (cell 1), and NB03 (cell 1) uses keyword matching on RAST function descriptions and misclassifies ACIAD1710 (4-carboxymuconolactone decarboxylase, pcaC) as "Other" because the keyword list includes "muconate" but not "muconolactone." A `utils.py` file exists in the notebooks directory with a corrected version that includes "muconolactone" in the keyword list, but **none of the notebooks import from it** -- they all contain older, incorrect copies. This creates an inconsistency: the shared utility has the fix, but the notebooks that actually run don't use it. The pitfall is documented in `docs/pitfalls.md` (lines 733-737), but the fix hasn't been propagated to the notebook code.

**Scope reduction acknowledged**: The RESEARCH_PLAN's Aim 3 described querying `kbase_ke_pangenome.eggnog_mapper_annotations` for cross-species pangenome comparison of pca pathway and Complex I KO co-occurrence. This was replaced with ortholog-transferred fitness analysis in NB04 and appropriately deferred to Future Direction #4 in REPORT.md.

## Code Quality

**Notebook organization**: All four notebooks follow a consistent setup -> analysis -> visualization -> summary pattern with markdown section headers. Each notebook ends with a summary cell printing key metrics. The markdown annotations explaining the pathway biochemistry (NB01, cell 2) and the ortholog transfer methodology note (NB04, cell 3) are valuable.

**Code duplication (critical)**: The `categorize_gene()` function is copied verbatim into NB01 (cell 1), NB02 (cell 1), and NB03 (cell 1). The `notebooks/utils.py` module already exists with a corrected version (includes "muconolactone" keyword) but is not imported by any notebook. This is a maintenance problem and actively causes the ACIAD1710 misclassification in the first three notebooks. NB04 avoids the issue by loading final categories from `final_network_model.csv` (which incorporates the co-fitness correction from NB03).

**SQL correctness**: The queries against the SQLite database are straightforward and correct. NB04 (cell 4) correctly uses `CAST(fitness_avg AS FLOAT)` for string-typed Fitness Browser columns, consistent with the pitfall documented in `docs/pitfalls.md` (lines 63-69). NB01's FBA queries use parameterized placeholders for gene ID lists, which is good practice.

**Statistical methods**:
- *Pearson correlation for co-fitness (NB03)*: Appropriate for continuous growth profiles. The population-level z-scoring using all 2,034 genes (NB03, cell 2) is good practice -- it avoids inflating correlations that would result from z-scoring only the 51 quinate-specific genes.
- *Mann-Whitney U test (NB04, cell 11)*: Correctly applied as a non-parametric test. However, the interpretation needs care: both Complex I AND background genes show significantly worse fitness on aromatics (both p<0.0001). The interaction test (cell 12) is the biologically meaningful comparison and relies on only n=5 Complex I genes with data on both aromatic and non-aromatic conditions. The p=0.038 is marginally significant and should be interpreted cautiously at this sample size.
- *No multiple testing correction* on the 13 per-condition comparisons (NB04, cell 14). Given the small number of tests, this is tolerable but should be acknowledged.

**Co-fitness confidence thresholds (NB03, cell 11)**: The scheme (High: r>0.7 and gap>0.15; Medium: r>0.5; Low: r>0.3) produces 2 High and 14 Medium assignments. One consequence: ACIAD3137 (r=0.988 with Complex I, the highest correlation of any unknown gene) gets only "Medium" confidence because the gap to Aromatic pathway (r=0.890) is only 0.098, falling below the 0.15 gap threshold. This is arguably too conservative for genes with r>0.98. With only 8 growth conditions, many genes will correlate with multiple subsystems simply because they share the quinate defect -- the gap criterion addresses this but its specific thresholds aren't empirically justified.

**Operon prediction (NB02, cell 6)**: The heuristic (<100 bp intergenic distance, same strand, allowing overlaps to -50 bp) is standard and appropriate. The Complex I operon prediction (13 genes, nuoA-N) and pca/qui operon (12 genes) match published data (Dal et al. 2005).

**Pitfall awareness**: The project correctly handles string-typed FB columns. Since most work is done locally on SQLite, most BERDL-specific pitfalls don't apply. Two project-specific pitfalls were captured in `docs/pitfalls.md`: keyword categorization fragility (line 733) and NotebookEdit cell validation issues (line 739).

## Findings Assessment

**Conclusions well-supported by data**:
- The 4-subsystem model is convincingly supported by convergent evidence: FBA flux ratios, genomic independence (distinct chromosomal loci), and very high within-subsystem co-fitness (Complex I: r=0.992, Aromatic pathway: r=0.961).
- The FBA blind spot finding (30/51 genes with no reaction mappings, 0% predicted essentiality for Complex I despite 1.76x higher flux on aromatics) is clearly demonstrated and is a genuinely useful finding for metabolic modeling.
- Genomic independence of subsystems (NB02) is cleanly shown: the only cross-category operon involves Aromatic pathway + "Other" (ACIAD1710, which is actually a misclassified pathway gene).
- The cross-species finding that Complex I defects are largest on acetate (-1.55 deficit) and succinate (-1.39), not on aromatic substrates, is an important refinement. The NDH-2 compensation hypothesis is plausible and well-reasoned.

**Areas of concern**:
- *Modest overall within/between co-fitness separation*: NB03 cell 5 shows within-category mean r=0.552 vs between-category r=0.518. This is driven by the high correlations within Complex I and Aromatic pathway (operon co-regulation), while Other (r=0.425) and Unknown (r=0.342) categories have low internal correlations. The subsystem assignments for unknown genes should be interpreted with this context.
- *Thin PQQ/Iron cross-species data*: NB04 shows only 4 aromatic fitness entries from 1 gene in the PQQ/Iron category. The REPORT wisely focuses on Complex I, but this gap limits the cross-species validation of the PQQ and iron dependency claims.
- *Small n for interaction test*: The key interaction test (NB04, cell 12) -- whether Complex I's aromatic deficit exceeds background -- uses only n=5 Complex I genes. The p=0.038 is marginal and would not survive conservative multiple testing correction.
- *Count evolution is clear but could be highlighted*: The numbers shift from NB01 (10 Complex I, 4 Iron, 6 Aromatic) to the REPORT (21 Complex I, 7 Iron, 8 Aromatic) after co-fitness reassignment. NB03 cell 13 shows the before/after table, but a reader going notebook-by-notebook needs to track this transition carefully.

**Limitations honestly acknowledged**: The REPORT.md Limitations section identifies four appropriate caveats: limited 8-condition dimensionality, mixed cross-species signals, phenotypic-only evidence for the 11 newly assigned Complex I genes, and PQQ's shared glucose dependency. The PQQ-glucose point is particularly valuable as it moderates the aromatic-exclusivity claim.

**No incomplete or placeholder analysis**: All planned analyses were either completed or explicitly deferred with rationale to Future Directions.

## Suggestions

1. **Import `categorize_gene()` from the existing `utils.py` instead of duplicating it** (high impact, easy fix): The `notebooks/utils.py` module already contains a corrected version with "muconolactone" in the keyword list. Replace the inline function definitions in NB01 (cell 1), NB02 (cell 1), and NB03 (cell 1) with `from utils import categorize_gene`. This fixes the ACIAD1710 misclassification in the initial categorization and eliminates 3 copies of identical code.

2. **Acknowledge the small sample size in the interaction test** (high impact, easy fix): NB04's interaction test (cell 12) uses only n=5 Complex I genes and yields p=0.038. Add a sentence noting this marginal significance and small n. The per-condition analysis (cell 14) provides complementary evidence, but the formal interaction claim should be appropriately hedged. Consider a permutation-based test as a robustness check.

3. **Document the ortholog transfer methodology in NB04** (medium impact): NB04 cell 3 briefly mentions BBH ortholog detection, but the analysis relies entirely on pre-computed `fitness_avg` and `fitness_count` values from the SQLite database. Clarify: how many FB organisms contributed to each `fitness_avg` value? Were scores averaged across all organisms or only the best hit? This is important because aggregating fitness across organisms with different respiratory chain architectures (a limitation the REPORT itself notes) makes the individual values hard to interpret.

4. **Add the "muconolactone" keyword to the notebook-local categorize functions** (medium impact, immediate fix): If refactoring to import from `utils.py` is deferred, at minimum add "muconolactone" to the keyword list in the notebook copies so ACIAD1710 (pcaC) is correctly classified as "Aromatic pathway" from the start. The current misclassification means NB01 and NB02 analyses (FBA comparison, operon analysis) undercount the aromatic pathway by 1 gene.

5. **Provide rationale for co-fitness confidence thresholds** (medium impact): The gap>0.15 requirement for "High" confidence (NB03, cell 11) causes genes with r>0.98 to be classified as only "Medium." Consider whether the gap threshold should scale with the absolute correlation level -- e.g., a gene with r=0.988 to its best match might reasonably be "High" confidence even with a gap of 0.098, since the correlation is so extreme.

6. **Add context for the modest overall within/between co-fitness difference** (low-medium impact): A brief note in NB03 explaining that the overall within vs between difference (0.552 vs 0.518) is small because it aggregates tight subsystems (Complex I, Aromatic pathway) with heterogeneous categories (Other, Unknown) would help readers correctly interpret the co-fitness assignments.

7. **Consider Bonferroni or BH-FDR correction for per-condition comparisons** (low impact, easy fix): NB04 cell 14 makes 13 condition-level comparisons. Even with a lenient BH-FDR threshold, this would strengthen the claim that acetate and succinate show the largest disproportionate Complex I defects.

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-02-19
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, requirements.txt, utils.py, 4 notebooks, 7 data files, 9 figures
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.

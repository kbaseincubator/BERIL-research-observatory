---
reviewer: BERIL Automated Review
date: 2026-02-19
project: gene_environment_association
---

# Review: Gene-Environment Association Across Pangenome Species

## Summary

This project builds a reusable framework for testing whether accessory gene clusters are differentially distributed across isolation environments, using the BERDL pangenome database and `ncbi_env` EAV metadata. The environmental metadata pivot (notebook 02) is well-executed, covering 292,913 genomes across 9 environment categories with a clean cross-tenant NMDC join. The gene-environment association testing (notebook 03) is statistically sound and produces a compelling S. aureus proof of concept (13,351 significant clusters, 10.0%), with an interesting food-enrichment finding supported by literature. A descriptive Methylobacterium analysis connecting MDH profiles and B vitamin pathways to environments adds biological depth. The main limitation is that only one species completed full testing due to Spark Connect auth timeouts, and the environment categorization heuristic has known gaps (e.g., "leaves" falling into "other"). Documentation is thorough, notebooks have saved outputs, and the project is well-positioned for extension to additional species.

## Methodology

**Research question**: Clearly stated and testable -- do accessory gene clusters show differential prevalence across environments? The question is well-scoped, with explicit criteria (>=2 categories, >=10 genomes each) defining which species qualify.

**Statistical approach**: Appropriate use of chi-squared tests (>2 categories) and Fisher's exact tests (2 categories) with Benjamini-Hochberg FDR correction. The choice of q < 0.05 is standard. The limitation of not controlling for population structure (phylogenetic non-independence) is clearly acknowledged, with pan-GWAS tools (Scoary, pyseer) cited as future extensions.

**Data sources**: Well-documented in README. The EAV pivot of `ncbi_env` follows a proven pattern from `temporal_core_dynamics`. The cross-tenant NMDC join (88,754 genome matches, 30%) is a nice demonstration of BERDL's multi-tenant capability, though it appears exploratory -- the NMDC harmonized labels are not ultimately used in the environment categorization logic, which relies on keyword matching on `isolation_source` and `host` fields.

**Reproducibility**: The pipeline is clearly two-stage (notebook 02 produces CSV, notebook 03 consumes it). Both notebooks require Spark Connect. The README includes a Reproduction section. The `refresh_spark()` workaround for auth timeout is documented and implemented.

**Environment categorization concern**: The heuristic keyword matching in notebook 02, cell b6, has a notable gap: `isolation_source` values like "leaves" (17 Methylobacterium genomes) and "tree leaf surface" (10 genomes) fall into "other" rather than "plant_associated", because the LIKE patterns check for `%leaf%` but the host-based classification fires first. Since many of these genomes have host values (e.g., "Arabidopsis thaliana"), they are classified as "host_associated" rather than "plant_associated". The README and notebook acknowledge this gap, but it is worth noting that for Methylobacterium specifically, this conflates true host-associated and plant-associated niches.

## Code Quality

**SQL queries**: Well-constructed, using exact equality for joins (consistent with pitfalls.md advice), appropriate filters, and correct join keys (`gene_cluster_id` to `eggnog_mapper_annotations.query_name` per documented pitfall). The EAV pivot pattern in notebook 02 cell b5 is clean and efficient.

**Notebook organization**: Both notebooks follow a logical progression (setup -> data exploration -> transformation -> analysis -> visualization -> summary). Markdown headers and section descriptions are clear. Each cell has a well-defined purpose.

**Pitfall awareness**:
- Annotation join key: Correctly uses `gene_cluster_id` = `query_name` (pitfalls.md: "Annotation Table Join Key").
- EAV format: Correctly handles `ncbi_env` pivot (pitfalls.md: "NCBI Environment Metadata").
- Spark timeout: Implements `refresh_spark()` workaround and documents the constraint.
- `.toPandas()` usage: Appropriately used only for final results after Spark-side filtering.
- Missing value filtering: The EAV query in cell b5 filters out common null-equivalent strings ('missing', 'not applicable', etc.).

**Potential issues**:
1. In notebook 03 cell b4a, the `test_gene_env_associations` function builds per-cluster genome sets using `presence_df.groupby('gene_cluster_id')['genome_id'].apply(set).to_dict()`. For 133K clusters, this is memory-intensive. It completed successfully for S. aureus (20 min wall time), but may struggle for species with larger accessory genomes.
2. The COG enrichment background sample (cell b6) uses `all_clusters[:5000]` -- a positional slice rather than a random sample. Since the order of clusters in `results` depends on the iteration order of `gene_genomes` (a dict), this is effectively arbitrary but not formally random. Using `np.random.choice` or `.sample()` would be more rigorous.
3. The COG enrichment comparison (cell b8) shows fraction differences but does not perform a formal statistical test (e.g., Fisher's exact test per COG category). The visual comparison is informative but the claim of "Mobilome (X) enriched" in the README/REPORT would be strengthened by a p-value.

## Findings Assessment

**S. aureus gene-environment associations**: The finding that 10% of accessory clusters show significant differential prevalence is plausible and well-supported by the data. The food enrichment dominance (4,681 clusters) is unexpected and appropriately flagged as requiring further investigation. The literature context (Richardson et al. 2018, Weinert et al. 2012) is relevant.

**COG enrichment**: The mobilome (X) enrichment in environment-associated genes is biologically interesting and consistent with HGT-driven niche adaptation. However, as noted above, this lacks formal statistical testing -- it is presented as a visual fraction difference.

**Methylobacterium descriptive analysis**: Appropriately framed as descriptive given small sample sizes. The finding that B vitamin pathway completeness is uniform across environments is interesting and connects well to the related `mextorquens_pangenome_case` project. The zero mxaF-only genomes reinforces cross-project consistency.

**Limitations**: Thoroughly documented in both README and REPORT. The acknowledgment of no population structure correction, the single-species proof of concept, and the heuristic categorization are all appropriate.

**One minor inconsistency**: The README says "Fisher's exact / chi-squared" in the approach, but the code (cell b4a) uses chi-squared for >2 categories and Fisher's for exactly 2. The REPORT correctly states "chi-squared (>2 categories) or Fisher's exact (2 categories)." S. aureus has 5 categories, so all its tests used chi-squared. The README's "Fisher's exact / chi-squared" phrasing could be read as implying Fisher's was used for S. aureus.

## Suggestions

1. **[High impact] Formalize COG enrichment testing**: Add per-COG-category Fisher's exact tests comparing the proportion of each COG in environment-associated vs. background clusters. This would replace the qualitative fraction-difference chart with quantitative evidence for the mobilome enrichment claim.

2. **[High impact] Use random sampling for COG background**: Replace `all_clusters[:5000]` with `results.sample(5000, random_state=42)['gene_cluster_id'].tolist()` to ensure the background sample is statistically representative.

3. **[Medium impact] Extend to mid-size species**: The README identifies Campylobacter, Enterococcus, and Listeria (1,000-2,000 genomes) as feasible within timeout constraints. Running 2-3 additional species would substantially strengthen the framework validation beyond a single proof of concept.

4. **[Medium impact] Improve plant_associated classification**: The keyword matching misses "leaves" and "tree leaf surface" -- values that are particularly relevant for Methylobacterium. Adding `like("%leaves%")` and `like("%phyllosphere%")` (already present) to the plant_associated branch, and reordering the classification so isolation_source-based plant keywords are checked before the host-based catch-all, would improve accuracy for plant-associated organisms.

5. **[Low impact] Clarify NMDC cross-tenant join utility**: Notebook 02 explores the NMDC `env_triads_flattened` join (30% match rate) but the harmonized ENVO ontology labels are not used in the final environment categorization. Either integrate the ENVO labels as an alternative/supplementary categorization scheme, or clarify in the README that the cross-tenant join was exploratory and the final pipeline uses only `ncbi_env` keyword matching.

6. **[Low impact] Add a Methylobacterium-specific figure**: The Methylobacterium MDH x environment crosstab and B vitamin completeness results are reported as text tables in notebook outputs. A heatmap or grouped bar chart of B vitamin completeness by environment would make these results more accessible and add a third figure to the project.

7. **[Low impact] Notebook numbering gap**: Notebooks start at 02, with no 01. The README mentions "same as notebook 01 in `mextorquens_pangenome_case`" for the MDH classification. If notebook 01 was intentionally omitted (because it belongs to the other project), consider adding a note explaining the numbering, or renaming the notebooks to start at 01.

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-02-19
- **Scope**: README.md, REPORT.md, references.md, requirements.txt, 2 notebooks, 3 data files (61 MB total), 3 figures
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.

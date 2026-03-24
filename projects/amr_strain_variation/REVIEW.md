---
reviewer: BERIL Automated Review
date: 2026-03-17
project: amr_strain_variation
---

# Review: Within-Species AMR Strain Variation

## Summary

This is a high-quality, large-scale analysis extending the AMR Pangenome Atlas to within-species resolution across 1,305 bacterial species and 180,025 genomes — a genuinely novel contribution enabled by the KBase/BERDL pangenome resource. The project is well-documented: all seven notebooks have populated outputs, 17 figures are present (including all four publication-quality PNG/PDF pairs), and the README provides an exemplary reproduction guide with Spark/local separation, runtimes, execution order, and headless run scripts. The REPORT.md is thorough, with well-stated limitations and a compelling novel finding — that acquired (non-core) AMR genes show stronger phylogenetic signal than intrinsic (core) genes. Three areas warrant attention: (1) a citation in REPORT.md ("Moradigaravand et al. (2022)") is absent from references.md; (2) NB04's key summary cells lack saved outputs, requiring a 1.6h Spark re-run to verify the headline phylogenetic signal statistics; and (3) the REPORT.md figures inventory is incomplete, listing only 3 of the 15 generated figures, and findings 4–6 lack inline visualizations. These are fixable gaps that do not undermine the core science.

---

## Methodology

**Research questions**: Clearly stated and decomposed into five testable sub-questions (within-species variation, resistance islands, phylogenetic signal, ecotypes, temporal trends), each mapping to a dedicated notebook. The execution DAG (NB01 → NB02–NB06 in parallel → NB07) is clearly documented.

**Analytical approaches are sound throughout**:
- Binary presence/absence matrices + Jaccard distance is the appropriate representation for AMR repertoire comparison.
- Phi coefficients + hierarchical clustering for resistance island detection with a prevalence-matched null model (1,000 replicates) correctly validates that observed co-occurrence exceeds chance.
- Mantel tests (999 permutations) with BH-FDR correction, stratified by core vs. non-core AMR, directly tests the phylogenetic signal hypothesis.
- UMAP + DBSCAN on Jaccard distance for ecotype detection, with eps estimated adaptively at the 25th percentile of pairwise distances and silhouette scoring for quality.
- Kruskal-Wallis for comparing AMR counts across environment categories (appropriate non-parametric test).

**ANI computational cap**: Species with >500 genomes are excluded from phylogenetic signal analysis (NB04). This is well-justified (O(n²) scaling) and explicitly acknowledged in REPORT limitations, but it excludes the two most clinically important species — *E. coli* (15,388 genomes) and *K. pneumoniae* (14,240 genomes). This is the correct engineering decision; it just needs to be prominent.

**Sibling-project dependency**: NB01 and NB02 require `amr_pangenome_atlas/data/amr_census.csv` and `amr_species_summary.csv`. README `## Reproduction` correctly documents this, including the branch name. This is good practice for cross-project data dependencies.

**Reproducibility**: Excellent. The README has a detailed `## Reproduction` section covering Spark/local separation, per-notebook runtimes, execution order, sibling dependency, and headless run scripts. This is above average for a BERDL analysis project.

---

## Code Quality

**SQL queries**: Syntactically correct. NB01's double-filtered join (`genome` chunk × `gene_genecluster_junction` AMR cluster filter) correctly avoids large IN-clause limits via the `chunked_query` utility — this directly addresses a known BERDL pitfall. The validation spot-check in NB01 comparing matrix AMR counts against direct Spark queries is exemplary defensive practice.

**Statistical methods**: Well-chosen throughout, as described in Methodology. No incorrect test applications detected.

**Specific issues**:

1. **NB04: Key summary cells lack saved outputs.** The local post-processing cells — FDR threshold summary, the core vs. non-core paired t-test (the headline finding t=-8.35, p=7e-16), and the NB04 SUMMARY cell — have no saved outputs. Since NB04 requires a live Spark session for ANI extraction (1.6h), a reader cannot verify the most novel quantitative result in the project without re-running the full pipeline. The ANI matrices are cached in `data/ani_matrices/`, so only the local Mantel portion needs re-execution.

2. **NB04 comment describes the prior, not the finding.** A code comment near the core vs. non-core comparison reads (approximately): `"Expectation: core (intrinsic) AMR should track phylogeny more than non-core (acquired)"` — but the observed result is the opposite. The comment accurately describes the prior hypothesis being tested, but it directly contradicts the finding on the lines below it, which will confuse readers.

3. **NaN→0 substitution in phi coefficient not documented in report.** NB03 replaces NaN phi values with 0 (treating gene pairs with no variance as uncorrelated) before hierarchical clustering. This is defensible but affects island detection thresholds and is not disclosed in the REPORT.md methodology or the findings narrative.

4. **`chunked_query` is duplicated verbatim** between NB01 and NB04. These are identical utility functions that could diverge silently if one is edited without updating the other.

5. **NB06 "BacDive" naming does not match actual implementation.** The notebook name (`06_temporal_bacdive.ipynb`), function name (`classify_env_from_name`), and output file (`bacdive_amr_bridge.csv`) all imply BacDive data was queried. In reality, no BacDive API call is made; the function implements a keyword-based approximation of BacDive's cat1 habitat categories. The REPORT.md is accurate ("rule-based keyword classification approximating BacDive categories"), but the notebook artifacts mislead anyone examining the files directly.

**Pitfall compliance**: Chunked IN-clause queries in NB01 correctly address the documented Spark IN-clause size pitfall. No evidence of the `SELECT DISTINCT ... COUNT(*)` anti-pattern or the `gtdb_taxonomy_id` join error (genome_id is used correctly). DECIMAL-to-float casting is not applicable to this project's aggregation patterns.

---

## Findings Assessment

**Findings 1–3 are fully supported** by saved notebook outputs and consistent with the REPORT.md claims.

- **Finding 1** (51% rare, median Jaccard = 0.435, median variability = 0.526): Confirmed by NB02 outputs. The cross-tabulation (Core → 77.3% fixed; Singleton → 78.7% rare) is a clean validation of the atlas conservation class taxonomy.
- **Finding 2** (1,517 resistance islands in 54% of species, mean phi = 0.827, 88% multi-mechanism): Confirmed by NB03 outputs including null-model comparison (observed phi 0.183 vs null 0.001, t=15.44, p=1.8e-20).
- **Finding 3** (55.6% significant phylogenetic signal, non-core r=0.222 > core r=0.117, p=7e-16): The species count is confirmed by NB07 synthesis reading `mantel_results.csv`. The underlying NB04 summary cells that computed the core/non-core comparison lack saved outputs (see Code Quality issue #1), so the specific statistics cannot be verified in-place. Note also that since core genes are nearly universal (≥95% prevalence by construction), Jaccard distances for core genes will have near-zero variance across genome pairs, which may suppress the Mantel r independent of any biological effect. The REPORT explains the result biologically (clonal fixation of acquired elements), but a brief note acknowledging this statistical dynamic would strengthen the interpretation.

**Finding 4** (19.5% of species form distinct ecotypes, median silhouette = 0.620): Confirmed by NB05 outputs. Environment-ecotype association testing is correctly described in the REPORT as limited to 2 species due to metadata sparsity (52.7% of genomes with unknown isolation_source), and the `ecotype_env_tests.csv` file (2 rows) matches this. The five case-study UMAP figures for *K. pneumoniae*, *S. aureus*, *P. aeruginosa*, *S. enterica*, and *A. baumannii* are present in `figures/`. No inline figure for Finding 4 appears in the REPORT.md text (unlike Findings 1–3, which each show a figure); `fig4_ecotypes_temporal.png` exists but is not embedded. The absence of *E. coli* from the case studies (due to the 500-genome cap) is acknowledged in the README but not in the REPORT.md ecotype discussion.

**Finding 5** (no significant temporal trends): Null result correctly stated and confirmed by NB06 outputs (0/513 species significant after BH-FDR). The interpretation attributing this to metadata sparsity rather than biology is plausible and appropriately hedged.

**Finding 6** (host-associated species carry more AMR): Confirmed by NB06 Kruskal-Wallis outputs (BacDive-approx: H=32.2 p=1e-7; NCBI keywords: H=154.3 p=2e-31). Both classifiers agreeing in direction strengthens confidence.

**REPORT.md citation inconsistency**: The Interpretation section cites "Moradigaravand et al. (2022)" by name in the phylogenetic signal discussion. This reference does not appear in `references.md` or in the REPORT.md reference list at the bottom of the document. This must be resolved.

**REPORT.md figures inventory gap**: The "Supporting Evidence → Figures" table lists only 3 figures (`nb02_variation_landscape.png`, `nb03_cooccurrence.png`, `nb04_phylogenetic_signal.png`). The project actually has 15 figures including the four publication-quality `fig1–fig4` pairs and five `nb05_*_ecotypes.png` case studies. These are simply not listed.

**Limitations section**: Excellent. Collection bias, metadata sparsity, AMRFinderPlus database coverage, the 500-genome Mantel cap, approximate environment classifiers, and the co-occurrence ≠ co-selection caveat are all explicitly stated.

---

## Suggestions

1. **(Critical) Add the missing Moradigaravand et al. (2022) reference.** The REPORT.md cites this paper in the phylogenetic signal interpretation but it appears nowhere in `references.md` or the REPORT.md reference list. Add the full bibliographic entry, or remove the citation if the paper cannot be identified.

2. **(High) Re-save NB04 with outputs for the local Mantel summary cells.** Cells computing the FDR-corrected species count, the core vs. non-core paired t-test (the headline novel finding), and the NB04 SUMMARY should have saved text outputs. ANI matrices are already cached, so only the local portion needs re-execution. This allows verifying the p=7e-16 result without relaunching a Spark session.

3. **(High) Complete the REPORT.md figures inventory.** The "Supporting Evidence → Figures" table lists only 3 of 15 figures. Add the four publication figures (`fig1`–`fig4`, PNG and PDF) and the five `nb05_*_ecotypes.png` case-study plots. Consider also embedding `fig4_ecotypes_temporal.png` inline under Finding 4, matching the pattern used for Findings 1–3.

4. **(Medium) Note the low-variance caveat for the core vs. non-core Mantel result.** Since core AMR genes are defined as ≥95% prevalent, pairwise Jaccard distances for core genes are near-zero with little variance, which can suppress the Mantel r coefficient regardless of true biological signal. Add a sentence in the Limitations section (or Finding 3 interpretation) acknowledging this statistical dynamic alongside the biological explanation.

5. **(Medium) Clarify NB04 code comment on core vs. non-core expectation.** The comment describing the prior hypothesis ("core should track phylogeny more") immediately precedes code that shows the opposite result. Revise to something like: "Prior expectation was that core (intrinsic) AMR tracks phylogeny more strongly — the data show the opposite."

6. **(Medium) Acknowledge *E. coli* exclusion in the REPORT.md ecotype discussion.** The README notes the 500-genome cap excludes *E. coli* from case studies, but REPORT.md Finding 4 does not explain the absence of the most-sequenced gram-negative pathogen. Add a parenthetical clarifying this.

7. **(Low) Clarify BacDive naming vs. actual implementation.** Consider renaming `data/bacdive_amr_bridge.csv` to `data/species_env_bridge.csv` and updating internal NB06 function names and section headers to reflect that a keyword approximation is used, not an actual BacDive query. The REPORT.md is already accurate on this point.

8. **(Low) Deduplicate `chunked_query`.** Extract the shared utility function to `scripts/spark_utils.py` and import it in both NB01 and NB04 to prevent silent divergence.

9. **(Low) Document NaN→0 phi substitution in REPORT methodology.** Add a brief note describing this NB03 design choice and its potential impact on island detection thresholds at the boundary of the φ≥0.5 threshold.

10. **(Low) Pin dependency versions.** `requirements.txt` uses minimum-version constraints. For a completed project, add a `requirements-frozen.txt` from `pip freeze` to preserve the environment used for the canonical run.

---

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-03-17
- **Scope**: README.md, REPORT.md, references.md, requirements.txt, 7 notebooks (NB01–NB07, all with populated outputs), 15 figures in `figures/`, 15 data files in `data/`, `docs/pitfalls.md`
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.

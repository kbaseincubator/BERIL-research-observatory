---
reviewer: BERIL Automated Review
date: 2026-02-15
project: cofitness_coinheritance
---

# Review: Co-fitness Predicts Co-inheritance in Bacterial Pangenomes

## Summary

This is a well-executed and thoroughly documented project that tests whether lab-measured functional coupling (co-fitness from RB-TnSeq) predicts genome-level co-inheritance (co-occurrence in pangenomes) across 11 bacterial species. The analysis covers 2.25M co-fit pairs vs 22.5M prevalence-matched random controls, with a secondary module-level analysis across 6 organisms with ICA data. The main pairwise result is a weak but statistically significant positive signal (delta phi = +0.003, p = 1.66e-29, 7/9 organisms positive), while the module-level analysis reveals a substantially stronger effect (delta = +0.053, 73% of accessory modules significant at p<0.05). The project excels in its three well-designed controls (operon adjacency, prevalence matching, phylogenetic stratification), comprehensive three-file documentation (README, RESEARCH_PLAN, REPORT), clear Spark/local separation with caching for reproducibility, complete notebook outputs, and 8 saved figures covering all 6 planned analyses. The honest reporting of negative and null results (Korea, Putida) alongside positive ones strengthens the credibility of the findings. The main areas for improvement are minor: `requirements.txt` is missing `statsmodels` and lacks version pins, a small discrepancy exists in the Putida module significance count between notebook and REPORT, and the phylogenetic control's 2000-pair subsampling is undocumented. Overall, this is among the strongest projects in the observatory for methodological rigor, statistical care, and intellectual honesty.

## Methodology

**Research question**: Clearly stated and testable. The RESEARCH_PLAN.md articulates specific predictions (signal strongest at intermediate prevalences, collapsing at >99%) and pre-registers four verification checks (e.g., "At prevalence >99%, phi should be ~0 for both groups"), which is excellent scientific practice.

**Approach**: The decision to use continuous prevalence rather than binary core/auxiliary classification (documented in RESEARCH_PLAN "Key Design Decisions") is methodologically sound and maximizes statistical power. The phi coefficient is the correct metric for binary co-occurrence. The prevalence-matched random pair generation independently matches each cluster's prevalence (NB02 `generate_random_pairs`), avoiding the bias of mean-prevalence matching. The two-tier analysis (pairwise co-fitness primary, ICA modules secondary) provides complementary evidence at different scales.

**Controls**: Three well-implemented controls:
1. **Operon control**: Only 0.7% of cofit pairs are adjacent (within 5 genes); excluding them preserves the signal (NB04 Fig 2).
2. **Prevalence matching**: 10 random pairs per cofit pair with +/-5% tolerance on individual cluster prevalences.
3. **Phylogenetic stratification**: Correctly handles the GTDB prefix mismatch (documented as a discovered pitfall). Limited by lack of "far" stratum genomes in most species, which is acknowledged.

**Data sources**: All sources clearly identified in README with a table mapping database, table, and use. Dependencies on three prior projects are explicitly documented in the Dependencies section.

**Reproducibility**: The README includes a two-step reproduction guide cleanly separating Spark-dependent extraction from local analysis. A standalone `src/extract_data.py` script duplicates NB01 for batch execution. All notebooks implement caching (skip if output file exists). However, estimated runtimes are not provided (NB01 takes ~210s per organism, ~40 min total based on outputs).

## Code Quality

**SQL correctness**: Spark SQL queries are correct and efficient. BROADCAST hints are properly applied on small filter tables joining against billion-row `gene_genecluster_junction` and `gene` tables (NB01, `src/extract_data.py`). All Fitness Browser numeric columns are properly CAST (`CAST(rank AS INT)`, `CAST(cofit AS FLOAT)`, `CAST(begin AS INT)`), consistent with `docs/pitfalls.md`. The Dyella79 locus tag mismatch is handled by filtering it from the link table in all notebooks.

**Statistical methods**: Appropriate throughout:
- Mann-Whitney U (two-sided) for non-normal phi distributions
- Wilcoxon signed-rank test for cross-organism meta-analysis (correctly reported as non-significant at p=0.13 with N=9)
- Permutation testing (1000 permutations) for module co-inheritance with Benjamini-Hochberg FDR correction via `statsmodels.stats.multitest.multipletests`
- Spearman correlation for co-fitness strength vs phi

**Notebook organization**: Clean four-notebook pipeline (extraction → pairwise analysis → module analysis → synthesis/figures). Each notebook has markdown headers, runtime requirements stated upfront, inline outputs preserved, and summary cells at the end. All notebooks produce saved outputs (text, tables, and figures).

**Pitfall awareness**: Two pitfalls discovered by this project are documented in `docs/pitfalls.md`: (1) GTDB prefix mismatch in phylogenetic distance table IDs, and (2) BROADCAST hints for billion-row table joins. The project also correctly follows the flat `data/` directory pattern and three-file documentation structure per prior pitfall guidance.

**Issues identified**:

1. **Missing `statsmodels` in `requirements.txt`**: NB03 imports `from statsmodels.stats.multitest import multipletests` but the package is absent from `requirements.txt`. Reproduction would fail at NB03 on a fresh install. No version pins for any package.

2. **Putida module significance discrepancy**: NB03 output prints "5 (13%)" significant modules for Putida, but the REPORT table says "6 (16%)". One of these needs correction.

3. **Phylogenetic control subsamples to 2000 pairs**: NB04 Fig 3 cell silently subsamples cofit pairs (`if len(cofit_unique) > 2000: cofit_unique = cofit_unique.sample(2000, random_state=42)`), which is not documented in the REPORT. This affects most organisms and reduces statistical power for the phylogenetic analysis.

4. **`compute_phi` float comparison**: Using `vec.std() == 0` for exact float comparison is safe for binary integer vectors but fragile in general. A tolerance-based check (`< 1e-10`) would be more robust.

## Findings Assessment

**Conclusions supported by data**: Yes, all central claims are well-supported:
- Pairwise delta phi of +0.003 aggregate, 7/9 organisms positive, 8/9 significant. The non-significant Wilcoxon (p=0.13) is correctly disclosed.
- Module-level delta of +0.053 with 51/195 significant (26%) at p<0.05, 21/195 (11%) after FDR. Accessory modules show 73% significance (8/11, 36% after FDR) -- a biologically meaningful contrast.
- The prevalence ceiling interpretation is well-supported by the Ddia6719 case (strongest signal, most accessory variation among near-clonal species).

**Negative results handled honestly**: Korea's negative delta (-0.042) and Putida's null result (delta=-0.000, p=0.41) are reported without suppression or spin, with plausible explanations provided.

**Limitations acknowledged**: Five specific limitations documented in the REPORT covering prevalence ceiling, Ralstonia exclusion, limited phylogenetic strata, pairwise vs multi-gene scale, and near-clonal species behavior.

**Literature context**: Four references with PMIDs cited meaningfully in the REPORT interpretation, connecting to Coinfinder (Whelan et al. 2020), *E. coli* accessory gene co-occurrence (Hall et al. 2021), *P. aeruginosa* phylogroup co-occurrence networks (Choudhury et al. 2025), and the Fitness Browser source data (Price et al. 2018). The `references.md` includes 11 total references with full bibliographic details.

**Visualizations**: All 6 planned figures from RESEARCH_PLAN are produced and saved in `figures/`, plus 2 supplementary figures. Figures have proper axis labels, titles, legends, and panel letters. Color choices are reasonable (viridis colormap in Fig 4 is colorblind-accessible).

**Counter-intuitive result explained**: The weak anti-correlation between cofit strength and phi (Spearman rho=-0.109) is correctly interpreted as a prevalence ceiling effect, though a partial correlation controlling for prevalence would strengthen this interpretation.

## Suggestions

1. **Add `statsmodels` to `requirements.txt` and pin versions** (Critical for reproducibility): NB03 imports `multipletests` from `statsmodels` but the package is absent from `requirements.txt`. Add it and consider pinning at least major versions for reproducibility (e.g., `pandas>=2.0`, `scipy>=1.10`, `statsmodels>=0.14`).

2. **Resolve Putida module significance discrepancy** (Minor): NB03 prints "5 (13%)" for Putida but the REPORT table says "6 (16%)". Check the source data and correct whichever is wrong.

3. **Document the 2000-pair subsampling in phylogenetic control** (Minor): NB04 silently subsamples cofit pairs to 2000 for the phylogenetic stratification analysis. Add a note in the REPORT's phylogenetic control limitation section (e.g., "phylogenetic stratification was computed on a random subsample of 2000 cofit pairs per organism for computational efficiency").

4. **Add expected runtimes to reproduction instructions** (Nice-to-have): The README's Reproduction section would benefit from approximate runtimes: "Step 1: ~45 min on BERDL JupyterHub (Spark); Steps 2-4: ~10 min each locally."

5. **Investigate Korea's random pair distribution** (Nice-to-have): Korea's random pair median phi (0.8597) is dramatically higher than its cofit pair median (0.2584), which is unusual. A diagnostic prevalence histogram for Korea would clarify whether the prevalence matching is selecting near-universal clusters and help explain the negative delta.

6. **Partial correlation for cofit strength vs phi** (Nice-to-have): Computing a partial Spearman correlation controlling for mean prevalence would directly test whether the anti-correlation (rho=-0.109) is indeed a prevalence ceiling artifact, strengthening the interpretation in the REPORT.

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-02-15
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, references.md, 4 notebooks, 1 extraction script (`src/extract_data.py`), requirements.txt, ~56 data files across 4 subdirectories + summary files, 8 figures
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.

---
reviewer: BERIL Automated Review
date: 2026-02-14
project: module_conservation
---

# Review: Fitness Modules × Pangenome Conservation

## Summary

This is a well-executed synthesis project that connects ICA fitness modules (from `fitness_modules`) with pangenome conservation status (from `conservation_vs_fitness`) to ask whether co-regulated gene groups preferentially reside in the core genome. The analysis is clean, the notebooks are well-structured with saved outputs, and the findings are clearly reported. The key result — that module genes are 86% core vs 81.5% baseline, and that family breadth does not predict conservation — is interesting and honestly presented, including the null result. The main areas for improvement are the lack of statistical testing for the core enrichment claim, resolving PFam/TIGRFam IDs to human-readable names in the annotation analysis, and handling the large number of NaN values in the family conservation table.

## Methodology

**Research question**: Clearly stated and testable — "Are ICA fitness modules enriched in core or accessory pangenome genes, and do cross-organism module families map to the core genome?" The question is a natural follow-up from the two upstream projects.

**Approach**: Sound and straightforward. The analysis merges module membership with conservation status, computes per-module composition, classifies modules by core fraction, and tests the breadth-conservation hypothesis. The essential gene check (Step 4 of NB02) is a thoughtful validation — confirming that ICA modules cannot contain essential genes since they lack fitness data.

**Data sources**: Well-identified. The README clearly lists the upstream data dependencies (`fitness_modules/data/modules/`, `conservation_vs_fitness/data/`). The 29-organism overlap (from 32 module organisms and 43 linked organisms) is explicitly documented.

**Reproducibility concerns**:
- The analysis runs entirely locally (no Spark needed), which is a significant advantage.
- The README includes a clear Reproduction section with exact commands.
- However, there is **no `requirements.txt`** file. The notebooks import pandas, numpy, matplotlib, and scipy, which should be documented.
- Notebook outputs are saved for both text and figures — this is good. Readers can review results without re-running.

## Code Quality

**NB01 (Module Conservation Profiles)**:
- Clean, logical flow: load data → build gene-level dataset → compute per-module conservation → classify modules → analyze function vs conservation.
- The merge between module membership and conservation link table is done correctly, with proper string casting of `locusId` on both sides.
- Conservation classification logic is correct: core when `is_core == True`, singleton when `is_singleton == True`, auxiliary otherwise. This aligns with the mutually exclusive flags documented in `docs/pitfalls.md`.
- The `n_mapped >= 3` filter for module classification is a reasonable minimum.
- Minor issue: The `has_mapped` DataFrame is reassigned with `.copy()` after being created from a filter — this correctly avoids the SettingWithCopyWarning, showing good pandas practice.

**NB02 (Family Conservation)**:
- The merge between families and module conservation uses `inner` join, which silently drops families without conservation data. Since 688 of 749 families are retained, ~61 families are lost. This is not discussed.
- The `family_conservation.tsv` output has a column naming issue: `n_modules_x` and `n_modules_y` from the merge with `family_annot`. This indicates a column name collision that should be resolved with explicit suffixes or renaming.
- In the accessory families output, most families show `NaN` for `n_organisms`, `consensus_term`, and `consensus_db`. This means 532 of 688 families (those not in the 156 annotated families from `family_annot`) lack organism counts and annotations. The analysis proceeds with these NaN values in the scatter plot by using `dropna(subset=['n_organisms', 'overall_pct_core'])`, which effectively restricts the breadth-conservation test to only the 156 annotated families. This is reasonable but should be explicitly stated.

**Annotation analysis (NB01 Step 4)**:
- The top annotations in core and accessory modules are reported as raw PFam/TIGRFam/KEGG IDs (e.g., "PF02653", "TIGR01726", "K03657") without human-readable descriptions. This makes the functional comparison between core and accessory modules difficult to interpret. The upstream `fitness_modules` project resolved these IDs to descriptions — this project should do the same or reference them.

**Pitfall awareness**:
- The Dyella79 exclusion (line in NB01 setup: `link = link[link['orgId'] != 'Dyella79']`) correctly follows the documented pitfall about locus tag mismatch.
- The `is_core`/`is_auxiliary`/`is_singleton` flags are used correctly as mutually exclusive categories, consistent with `docs/pitfalls.md`.
- No Spark queries are involved, so REST API and string-typed column pitfalls are not applicable.

## Findings Assessment

**Module genes are more core than average (+4.5 pp)**: This is the central finding, but it lacks a statistical test. The 86.0% vs 81.5% difference is reported as a simple comparison of proportions, with no chi-squared test, Fisher's exact test, or permutation test to assess significance. Given that there are 27,670 unique module genes and ~178K total genes, even small differences could be statistically significant — but the reader cannot tell from the current analysis. A simple chi-squared test on the 2×2 table (module/non-module × core/non-core) would resolve this.

**Module classification (59% core, 36% mixed, 5% accessory)**: Well-presented with both a histogram and bar chart. The thresholds (90% for core, 50% for accessory) are clearly defined. The visualization is effective — the histogram shows the strong right-skew and the baseline comparison line contextualizes the distribution.

**Family breadth does NOT predict conservation (rho=-0.01, p=0.914)**: This null result is honestly reported and well-interpreted. The explanation — that the core genome baseline is so high that there's little room for a gradient — is insightful. The scatter plot and box plot effectively communicate this. The box plot shows that even 2-organism families are ~90% core, leaving no room for wider families to increase.

**Accessory module families**: The 38 families with <50% core genes are identified, but most lack annotations (NaN consensus_term). The interpretation that these "may represent horizontally transferred functional units or niche-specific operons" is reasonable but speculative — the data don't directly support this claim.

**Essential genes absent from modules**: This is a clean validation (0 essential genes in any module). The explanation is correct — ICA requires fitness variation data, which essential genes lack.

**Limitations**: The README does not have a dedicated Limitations section. The ceiling effect on conservation (most genes are core, limiting the possible enrichment signal) is mentioned in the breadth-conservation context but not as a general limitation. Other potential limitations — such as the 29/32 organism subset, the dependence on upstream link table quality, or the arbitrary 90%/50% thresholds for module classification — are not discussed.

## Suggestions

1. **Add a statistical test for the core enrichment claim** (Critical). The central finding (86.0% vs 81.5% core) has no p-value. A chi-squared test or Fisher's exact test on module vs non-module genes × core vs non-core would take 2-3 lines of code and substantially strengthen the main result.

2. **Resolve annotation IDs to human-readable descriptions** (High). In NB01 Step 4, PFam/TIGRFam IDs like "PF02653" are opaque. Map these to domain names (e.g., "PF02653: ABC transporter permease") so readers can interpret the functional differences between core and accessory modules.

3. **Fix the column naming collision in `family_conservation.tsv`** (Medium). The `n_modules_x` / `n_modules_y` columns result from a merge collision. Rename to something meaningful (e.g., `n_modules_obs` vs `n_modules_family`).

4. **Add a `requirements.txt`** (Medium). The project imports pandas, numpy, matplotlib, and scipy. A simple requirements file would complete the reproduction documentation.

5. **Add a Limitations section to the README** (Medium). Discuss: (a) the ceiling effect — 81.5% baseline core rate limits the maximum observable enrichment; (b) the 29/32 organism subset; (c) the arbitrary classification thresholds; (d) the module membership threshold from upstream could affect conservation composition.

6. **Document the 61 families dropped by the inner join in NB02** (Low). The merge from 749 to 688 families loses ~8% of families. A brief note explaining that these families had no modules in the 29 overlapping organisms would be helpful.

7. **Consider a per-organism analysis** (Nice-to-have). The aggregate 86% vs 81.5% comparison pools all organisms. A per-organism paired comparison (module core fraction vs baseline core fraction, across 29 organisms) would control for organism-level variation and provide a more robust test (e.g., paired Wilcoxon signed-rank test).

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-02-14
- **Scope**: README.md, 2 notebooks, 2 data files, 2 figures
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.

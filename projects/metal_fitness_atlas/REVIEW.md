---
reviewer: BERIL Automated Review
date: 2026-02-17
project: metal_fitness_atlas
---

# Review: Pan-Bacterial Metal Fitness Atlas

## Summary

This is an outstanding project that constructs the first cross-species genome-wide fitness atlas for metal tolerance, spanning 383,349 gene-metal fitness records across 24 organisms and 14 metals. The central finding -- that metal-important genes are 87.4% core (OR=2.08, p=4.3e-162), reversing the initial hypothesis of accessory enrichment -- is rigorously supported by per-organism and per-metal Fisher exact tests, a Mann-Whitney comparison of toxic vs essential metals, and a phylogenetic sensitivity analysis that excludes duplicate Pseudomonas strains. Scientifically, the project demonstrates exemplary integrity: when data refuted the accessory-enrichment hypothesis (H1a), the authors reframed their interpretation as a "core genome robustness model" rather than selectively reporting supporting results. The pipeline is well-structured across 7 notebooks with consistent organization, all notebooks have saved outputs, 13 data files and 11 figures are generated with full provenance, and the documentation (README, RESEARCH_PLAN, REPORT) is thorough. Areas for improvement are relatively minor: the pangenome prediction (NB06) reveals that normalized metal scores do not significantly distinguish bioleaching genera from background (p=0.17), an important null result that deserves more discussion; a few statistical refinements could strengthen the cross-species family analysis; and the PFAM component of the metal signature is vestigial (only 1 term).

## Methodology

**Research question and hypothesis**: Exceptionally well-formulated. The RESEARCH_PLAN provides formal null and alternative hypotheses with four testable sub-hypotheses (H1a-H1d), explicit confounders (concentration variation, phylogenetic non-independence, pangenome sampling depth, condition dependence), and a thorough literature context identifying the specific gap this project fills. The 10 key references are well-chosen and span the relevant fields (RB-TnSeq methods, metal resistance genomics, pangenome biology, bioleaching).

**Approach soundness**: The seven-notebook pipeline follows a logical progression from experiment classification through conservation analysis to pangenome-scale prediction. Each notebook clearly documents its inputs, outputs, and runtime environment. The decision to reuse cached data from three prior projects (`fitness_modules`, `conservation_vs_fitness`, `essential_genome`) rather than re-querying BERDL databases is architecturally sound -- it avoids redundant computation and the string-typed-column pitfall documented in `docs/pitfalls.md`.

**Statistical methods**: Appropriate throughout. Fisher exact tests for 2x2 contingency tables (NB03) are correct for testing enrichment with varying sample sizes. The Mann-Whitney U test for comparing toxic vs essential metal deltas (p=0.015) is appropriate given the small sample sizes (9 toxic, 5 essential metals) where parametric assumptions would be questionable. The phylogenetic sensitivity analysis (excluding 4 duplicate *P. fluorescens* FW300 strains; OR=2.065, p=5.9e-141) convincingly addresses the non-independence concern. The RESEARCH_PLAN mentioned Cochran-Mantel-Haenszel and logistic regression with random effects, which were not implemented, but the simpler approach is adequate given the overwhelming signal strength.

**Data source clarity**: Excellent. The README provides a complete table of 9 reused data assets from 3 prior projects with exact file paths and row counts. The RESEARCH_PLAN includes a detailed query strategy table with estimated row counts and filter strategies. The REPORT documents both BERDL collections used and all 13 generated data files with row counts and descriptions.

**Reproducibility**: The README includes a complete Reproduction section with prerequisites, prior project dependencies, sequential `nbconvert` commands, runtime estimate (<5 min), and coverage notes documenting which organisms are excluded at each stage. A `requirements.txt` is present. NB06's Spark dependency is flagged with a comment in the pipeline commands. All notebooks have saved outputs enabling review without re-execution.

## Code Quality

**Notebook organization**: All 7 notebooks follow a consistent pattern: markdown header documenting inputs/outputs/environment, imports cell, numbered analysis sections with markdown separators, and a formatted summary block at the end. This is exemplary and makes each notebook independently understandable.

**Metal classification (NB01)**: The three-tier matching strategy (exact compound name, keyword in condition_1, keyword in expDesc, expGroup fallback) is thorough. The `METAL_COMPOUND_MAP` dictionary with explicit (metal, category, critical_mineral) tuples is clean and auditable. The decision to exclude Platinum/Cisplatin as a DNA-damaging agent rather than a metal stressor is scientifically sound. One potential gap: 148 of 559 experiments (26%) lack parsed concentrations, which limits the dose-response analysis noted in Future Directions.

**Fitness extraction (NB02)**: Correctly applies standard Fitness Browser thresholds (fit < -1, |t| > 4) and provides both broad and strict importance definitions. The approach of reading pre-computed fitness matrices rather than querying the 27M-row `genefitness` table is efficient and sidesteps the string-typed-columns pitfall. The code handles missing matrices gracefully (7 organisms skipped with reporting). The dual output (full 383K-row scores + 12.8K important genes) supports downstream analyses cleanly.

**Conservation analysis (NB03)**: The join with `fb_pangenome_link` correctly deduplicates on (orgId, locusId) before merging. The per-organism analysis properly deduplicates genes appearing under multiple metals. The baseline comparison computes core fraction over all mapped genes for the same set of organisms, not a global baseline, which is methodologically correct. The sensitivity analysis removing 4 duplicate Pseudomonas strains is a valuable robustness check.

**Cross-species families (NB04)**: The 84.7% mapping rate to ortholog groups is reasonable. The novel candidate classification into three tiers (truly_unknown: 89, novel_domain with DUF/UPF: 43, novel_metal_function: 17) is a meaningful improvement over a binary annotated/unannotated split. The top candidates listed (e.g., OG02094: "P-loop ATPase UPF0042" across 8 organisms and 7 metals; OG02716: "DUF3108" across 7 organisms) are credible follow-up targets. One concern: the `classify_novelty` function checks `rep_desc` and `seed_description` for keywords but does not check the eggNOG `Description` field from the annotation query, which could miss informative annotations.

**Module analysis (NB05)**: The z-scoring approach (standardizing each module's activity across all experiments, then extracting metal z-scores) correctly resolves the scale mismatch that produced 0 responsive modules with raw scores -- this is transparently documented in the REPORT. The |z| > 2.0 threshold yields a 3.1% responsiveness rate (600/19,453 records), which is biologically plausible. Conservation analysis of responsive module genes (mean 0.826 core fraction, n=183) provides independent validation of the gene-level core enrichment finding.

**Pangenome prediction (NB06)**: This notebook runs on BERDL JupyterHub with Spark. The code correctly uses PySpark DataFrame API with BROADCAST hints for the KEGG term join against `eggnog_mapper_annotations`. The full 1,286-term KEGG signature is used (no truncation). Two observations:

- The PFAM signature component is vestigial: only 1 PFAM term was extracted (vs 1,286 KEGG KOs). The `metal_functional_signature.csv` reports 1,287 total terms (1,286 KEGG + 1 PFAM), but only KEGG terms are used in the species scoring query. The PFAM extraction loop appears functional but yields minimal output, likely because the `PFAMs` field format in eggnog annotations doesn't consistently use "PF" prefixes.
- Genome-size normalization is implemented (`n_metal_clusters / n_annotated_clusters`), which correctly controls for large pangenome bias. The top species by normalized score are endosymbionts (*Buchnera*, *Kinetoplastibacterium*) with very small genomes where metal-related KEGG terms comprise a large fraction of their total annotation content. This is a known artifact of proportion-based normalization on reduced genomes and could be addressed with a minimum genome size filter.

**Pitfall awareness from `docs/pitfalls.md`**:
- String-typed numeric columns: Avoided by using pre-computed matrices (NB02)
- genefitness 27M row filtering: Avoided by architectural design
- Gene cluster cross-species comparison: NB06 correctly uses KEGG KOs for cross-species functional comparison
- `get_spark_session()` import: NB06 uses the correct CLI import path
- Essential genes invisible in genefitness: Acknowledged in REPORT Limitations section as "Essential genes excluded" -- notes that ~14.3% of protein-coding genes lack transposon insertions, are ~82% core, and that their exclusion makes the observed core enrichment a conservative estimate. This is well handled.

## Findings Assessment

**Core enrichment finding (H1a rejected)**: Strongly supported. The effect (OR=2.08) is large, the p-value (4.3e-162) reflects genuinely overwhelming evidence given the sample size (318,751 mapped records), and the result holds across 21 of 22 organisms and after phylogenetic sensitivity analysis. The reframing as a "core genome robustness model" -- where metal fitness defects primarily reflect core cellular processes vulnerable to metal disruption (cell envelope, DNA repair, central metabolism) rather than specialized resistance mechanisms -- is a genuine conceptual contribution that reconciles this finding with prior literature showing accessory-genome enrichment of annotated metal resistance genes (efflux pumps, czc operons).

**Essential vs toxic metals (H1b supported)**: Essential metals show significantly higher core enrichment (+0.148 vs +0.081; Mann-Whitney p=0.015). This is biologically sensible: iron/molybdenum/tungsten are cofactors for core metabolism, so genes important under their limitation should be fundamental metabolic genes. The individual metal results are granular and well-reported, with appropriate caveats for underpowered metals (Cadmium: 1 organism; Uranium: 2 organisms).

**Conserved metal families (H1c supported)**: 1,182 families across 2+ organisms and 601 across 3+ organisms represent a substantial catalog. The most broadly conserved family (OG00128: 17 organisms, 9 metals) and the positive correlation between organism breadth and core conservation are compelling. The 149 novel candidates are appropriately categorized.

**Pangenome prediction (mixed results)**: This is the most nuanced finding and deserves more prominent discussion. With genome-size normalization, bioleaching genera are NOT significantly enriched over background (Mann-Whitney p=0.17). The REPORT acknowledges this but frames it as "consistent with the core genome robustness model" -- that metal tolerance genes are broadly distributed rather than concentrated in specialists. This is a valid interpretation, but it also means the pangenome scoring approach has limited practical utility for bioprospecting. The per-genus percentile rankings (Leptospirillum at 91st, Acidithiobacillus at 77th) are informative individually, but the lack of statistical significance for the group comparison is an important caveat. The raw (unnormalized) score shows extreme significance (p<1e-300) but conflates genome size with metal biology.

**Limitations**: Comprehensively acknowledged in the REPORT. The six limitations and five future directions are specific and actionable. Particularly notable: the distinction between "metal fitness genes" (what this atlas measures) and "metal resistance genes" (what prior literature focused on) is clearly articulated and represents real scientific nuance.

**Completeness**: No analysis appears incomplete or left as placeholder. All 7 notebooks have full outputs. The NB07 final summary cell confirms all 11 figures and 13 data files are generated and populated.

## Suggestions

1. **[Moderate] Discuss normalized prediction null result more prominently**: The pangenome prediction finding that bioleaching genera are not significantly enriched after normalization (p=0.17) is buried in the REPORT. This deserves explicit discussion as a meaningful negative result: it implies that metal fitness gene repertoires reflect core bacterial biology rather than specialized metal ecology, which is actually a strong confirmation of the core robustness model. Currently the REPORT primarily emphasizes per-genus percentile rankings, which could give an overly optimistic impression of predictive power.

2. **[Moderate] Address endosymbiont artifact in normalized scores**: The top-ranking species by normalized score are all obligate endosymbionts (*Buchnera*, *Kinetoplastibacterium*, *Ruthia*) with highly reduced genomes (500-950 annotated clusters). These rank high because their small genomes are dominated by conserved core functions that happen to overlap with the metal KEGG signature. Consider adding a minimum genome size filter (e.g., >1,500 annotated clusters) or noting this artifact when presenting top-scoring species. The current top-20 list is misleading for bioprospecting applications.

3. **[Moderate] Fix vestigial PFAM component in metal signature**: The metal functional signature contains 1,286 KEGG terms but only 1 PFAM term. The PFAM extraction loop in NB06 appears functional but yields minimal output. Either debug the PFAM extraction (likely a prefix-matching issue in the `PFAMs` field parsing), include PFAMs in species scoring alongside KEGG terms, or remove the PFAM component from `metal_functional_signature.csv` to avoid confusion about the signature's actual composition.

4. **[Minor] Consider multiple-testing correction across metals in NB03**: The per-metal Fisher exact tests (14 tests) are each evaluated at p<0.05 without Bonferroni or FDR correction. With 14 tests, the Bonferroni threshold would be p<0.0036. This would not change the conclusions (12 of 14 metals have p<0.001), but applying correction would be methodologically cleaner. Similarly, the 22 per-organism tests could benefit from FDR correction, though again the conclusions would be unchanged (14 of 22 are significant at p<0.05; most of these have p<0.001).

5. **[Minor] Clarify metal count discrepancy across documents**: The README states "14 metals," RESEARCH_PLAN says "13 metals" in the data sources table, NB01 identifies 16 categories, and the REPORT says "14 metals" in the conservation table but "16 metals" in the experiment summary. A consistent statement would help: "16 metal categories identified; 14 retained for analysis after excluding Platinum/Cisplatin (DNA-damaging agent) and Metal_limitation (unresolved condition)."

6. **[Minor] Strengthen novelty classification in NB04**: The `classify_novelty` function combines `rep_desc` and `seed_description` for keyword matching but does not incorporate the eggNOG `Description` field from the annotation query. Some families classified as "truly_unknown" may have informative eggNOG descriptions not captured by the current filter. A cross-check against the eggNOG annotations retrieved in NB06 would tighten the novel candidate list.

7. **[Nice-to-have] Add condition-specific metal gene analysis**: As noted in the REPORT's Future Directions, the most impactful follow-up would be repeating the conservation analysis using only genes important for metals but NOT for other stresses (osmotic, oxidative, etc.). Even a preliminary version -- e.g., filtering NB02 output to genes where metal fitness defect < -1 but fitness under non-metal stresses is near zero -- would test whether the "Tier 2" accessory enrichment emerges when general stress response is controlled for. This would directly connect to the prior DvH finding (71.2% core for condition-specific heavy-metal genes) and strengthen the two-tier model.

8. **[Nice-to-have] Report effect sizes alongside p-values for the essential vs toxic comparison**: The Mann-Whitney U test (p=0.015) confirms essential metals have higher core enrichment deltas than toxic metals, but with only 5 essential and 9 toxic metals, the effect size (rank-biserial correlation or Cohen's d) would better convey the magnitude of the difference. The mean deltas (+0.148 vs +0.081) are informative but a formal effect size would strengthen the claim.

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-02-17
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, 7 notebooks, 13 data files, 11 figures, requirements.txt, docs/pitfalls.md
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.

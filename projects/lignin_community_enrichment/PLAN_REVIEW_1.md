# Plan Review 1: Lignin Enrichment and Ecological Memory in Microbial Communities

**Reviewer**: Independent AI Reviewer (BERIL Observatory)
**Date**: 2026-05-07
**Plan version reviewed**: v1 (2026-05-07)

---

## Overall Assessment

This is a well-structured research plan with clearly stated hypotheses and a logical analysis progression that exploits a thoughtful experimental design. However, the plan significantly under-addresses the severe statistical power limitations of n=3 per group and omits several critical bioinformatics pre-registration decisions that will strongly influence results.

---

## Strengths

- **Hypotheses are clearly stated with explicit null and alternative forms.** H1-H5 are all testable given the data, and the expected outcomes section usefully pre-registers interpretive frameworks for both positive and null results.
- **The experimental design is genuinely interesting.** The 2x2 factorial nested within a sequential passaging framework is a creative way to test ecological memory with controlled enrichment history. The tree diagram in the README makes the design immediately legible.
- **The ecological memory contrasts (H3) are the most novel aspect.** Groups 4 vs 5 and 6 vs 7 are well-conceived pairwise comparisons that isolate history effects from current-condition effects.
- **The analysis plan follows a logical progression** (QC -> processing -> composition -> alpha -> beta -> differential abundance -> synthesis) that mirrors community standards.
- **Honest listing of potential confounders** (inoculum variation, bottle effects, extraction bias, PCR bias, sequencing depth) shows awareness of common pitfalls.
- **BERDL cross-referencing is appropriately scoped as optional/post-hoc**, not as a load-bearing part of the primary analysis. This is realistic.
- **Dual-marker approach (16S + ITS)** on the same samples is a strength that enables the Procrustes/concordance analysis in H4.

---

## Issues to Address

### 1. CRITICAL: Statistical power is inadequate for most planned tests, and this is not discussed

With n=3 per group, the study has extremely limited statistical power for nearly every planned analysis. This is the single most important limitation and the plan does not acknowledge or mitigate it.

**Specific concerns:**

- **PERMANOVA with 3 replicates per group**: With 7 groups and 21 total samples, a global PERMANOVA is feasible but will have low power to detect moderate effect sizes. The pairwise PERMANOVAs (each comparing n=3 vs n=3) have only 10 unique permutations under an unrestricted model, making it impossible to achieve p < 0.05 by permutation alone. This is a fundamental mathematical constraint, not a soft concern.
- **Kruskal-Wallis with n=3**: For alpha diversity comparisons, the omnibus test across 7 groups has 21 observations total. Pairwise Dunn's tests between groups of n=3 have almost no power. The planned contrasts (base vs all enriched, lignin vs lignin+LC within round, etc.) pool some groups, which helps, but the plan does not specify which contrasts pool and which do not.
- **Multiple testing burden**: With 7 groups, there are 21 pairwise comparisons. After BH-FDR correction across 21 tests with individual tests that have ~10 permutations each, the probability of detecting a true moderate effect is near zero. The plan should explicitly state which contrasts are primary (confirmatory) and which are exploratory.

**Recommended action**: Add a "Statistical Power and Limitations" section that (a) acknowledges the n=3 constraint, (b) specifies a hierarchy of planned contrasts (primary vs secondary vs exploratory), (c) considers effect-size reporting (e.g., PERMANOVA R-squared, Cohen's d equivalents) alongside or instead of p-values, and (d) considers whether the pairwise PERMANOVA permutation issue can be addressed (e.g., by using the pooled residual permutation approach).

### 2. CRITICAL: Pairwise PERMANOVA with n=3 per group cannot yield significant p-values

This is a specific elaboration of issue 1 that warrants its own entry because it affects the core ecological memory test (H3). When comparing two groups of n=3 each (6 total observations), PERMANOVA with unrestricted permutations has at most 6!/(3!*3!) = 20 possible permutations. The smallest achievable p-value is 1/20 = 0.05, which fails a strict alpha=0.05 threshold. For the key contrasts (Groups 4 vs 5, Groups 6 vs 7), this means H3 literally cannot be rejected at p<0.05 using standard pairwise PERMANOVA.

**Recommended action**: Either (a) use a pooled-within-groups residual permutation approach (permuting residuals from a reduced model under a nested/restricted design), (b) report exact permutation p-values with the understanding that p=0.05 is the minimum, (c) supplement PERMANOVA with effect-size measures (R-squared, distance-to-centroid ratios), or (d) frame these contrasts as exploratory/descriptive rather than confirmatory hypothesis tests. The plan should pre-register which approach will be used.

### 3. CRITICAL: No pre-registration of key bioinformatics decisions that will shape results

The plan leaves several high-impact decisions unspecified:

- **Rarefaction depth**: Not mentioned. Whether to rarefy, at what depth, and whether to discard low-depth samples will directly affect alpha and beta diversity. The rarefaction debate (McMurdie & Holmes 2014 vs Weiss et al. 2017) should be acknowledged, and a decision pre-registered.
- **ASV vs OTU**: The plan says "DADA2 or vsearch" but these produce fundamentally different feature units (ASVs vs OTUs). With n=3, ASV-level analyses will have many sparse features; OTU clustering at 97% may be more appropriate for some analyses. This should be decided and justified before data analysis.
- **Filtering thresholds**: No mention of prevalence or abundance filtering for feature tables. With n=3, rare ASVs will dominate the feature table and inflate beta diversity distances. Standard practice is to filter (e.g., present in at least 2 samples, or at least X total reads), but the threshold matters.
- **Chimera removal strategy**: Not mentioned (DADA2 handles this internally, but vsearch requires explicit chimera filtering).

**Recommended action**: Add a "Pre-registered Bioinformatics Decisions" subsection to NB01 specifying: rarefaction strategy, ASV/OTU choice with justification, prevalence/abundance filtering thresholds, and chimera handling.

### 4. IMPORTANT: The plan does not exploit the nested/hierarchical structure of the experimental design

The sequential enrichment creates a hierarchical structure (Base -> Round 1 -> Round 2) that is not exploited in the statistical framework. All analyses treat the 7 groups as independent, but samples in Round 2 groups are biologically derived from Round 1 groups, which are derived from the Base. This non-independence should be modeled.

**Specific issues:**

- **PERMANOVA should use a nested design**: Rather than a flat 7-group PERMANOVA, a nested/hierarchical PERMANOVA (e.g., `adonis2(dist ~ Round + Round1_condition/Round2_condition)`) would be more appropriate and more powerful for testing the effects of interest.
- **Trajectory analysis in NB06 is on the right track** but should be formalized. The Base->R1->R2 trajectories can be analyzed with repeated-measures-aware methods or trajectory-specific contrasts.
- **Shared inoculum structure**: Groups 4 and 6 share a Round 1 parent (Group 2); Groups 5 and 7 share a Round 1 parent (Group 3). This creates a natural pairing that could be exploited for more powerful tests of Round 2 effects.

**Recommended action**: Restructure NB04 to include a nested PERMANOVA design that models Round and condition within Round. Consider whether the shared-inoculum structure can be leveraged (e.g., split-plot or nested ANOVA analogs for distance matrices).

### 5. IMPORTANT: Compositionality of amplicon data is acknowledged in NB05 but not in NB03-NB04

The plan correctly mentions CLR transformation and ALDEx2-style analysis for differential abundance (NB05), showing awareness of the compositionality problem. However, NB03 (alpha diversity) uses raw count-based metrics (Shannon, Simpson, Chao1) and NB04 (beta diversity) uses Bray-Curtis and Jaccard on relative abundances. There is no discussion of whether Aitchison distance (Euclidean distance on CLR-transformed data) should be used alongside or instead of Bray-Curtis.

**Recommended action**: (a) Add Aitchison distance to the beta diversity analysis in NB04 as a compositionally-aware alternative to Bray-Curtis. (b) Acknowledge that alpha diversity metrics are computed on rarefied counts (which partly addresses compositionality) or on raw counts (which does not). (c) Consider whether the conclusions from NB04 and NB05 could conflict due to different compositionality handling.

### 6. IMPORTANT: Procrustes/Mantel test for 16S-ITS concordance (H4) has methodological issues

- **Mantel test**: The Mantel test for correlation between two distance matrices is known to have inflated Type I error rates when spatial/temporal autocorrelation is present. With n=21 samples, the Mantel test has limited power regardless. More importantly, it tests whether two distance matrices are globally correlated, but H4 predicts that bacteria and fungi respond *differently* -- i.e., lack of concordance -- which is the null expectation under Mantel (no correlation). A non-significant Mantel test does not confirm H4; it merely fails to reject H0.
- **Procrustes analysis**: More informative than Mantel but still limited with n=21. Consider reporting the Procrustes M-squared (sum of squared residuals) with its permutation-based significance.

**Recommended action**: Clarify the interpretive framework for H4. If the hypothesis is that bacteria and fungi respond differently, the analysis should be designed to detect *where* they diverge (e.g., per-group concordance measures) rather than just testing global concordance. Consider a co-inertia analysis as a more powerful alternative to Procrustes/Mantel.

### 7. IMPORTANT: Differential abundance with n=3 is unreliable regardless of method

The plan lists ALDEx2-style CLR + Wilcoxon or ANCOM-BC for differential abundance (NB05). Both are compositionally-aware, which is good. However, with n=3 vs n=3, both methods will have essentially zero power after multiple testing correction across hundreds or thousands of ASVs/OTUs. ALDEx2 was designed for this situation (it uses Monte Carlo sampling from a Dirichlet distribution to estimate technical variability), but the authors themselves note that n<4 is problematic.

**Recommended action**: (a) Acknowledge that NB05 is exploratory with n=3 and should focus on effect-size estimation rather than significance testing. (b) Consider a more targeted approach: instead of testing all ASVs, test only ASVs belonging to pre-specified lignolytic genera (from H1's list), which reduces the multiple testing burden. (c) Report effect sizes (CLR difference, fold change) alongside p-values and do not rely solely on statistical significance for biological interpretation.

### 8. IMPORTANT: No mention of batch effects or technical confounders

The plan acknowledges DNA extraction bias and PCR bias as potential confounders but does not discuss how to detect or mitigate them:

- Were all 21 samples extracted in the same batch? If not, extraction batch is a confounder.
- Were 16S and ITS libraries prepared in the same sequencing run? If not, run effects confound the 16S-ITS comparison.
- Were samples randomized across wells/flow cells? If groups were clustered, index hopping or well effects could create false differences.

**Recommended action**: Add a brief section on technical metadata (extraction batch, library prep batch, sequencing run) and how batch effects will be assessed. At minimum, check whether PERMANOVA ordinations show batch clustering rather than group clustering.

### 9. SUGGESTION: Indicator species analysis (NB06) should use a method designed for small sample sizes

The plan mentions indicator species analysis in NB06 to find taxa indicative of enrichment history. The standard method (Dufrene & Legendre 1997, implemented in R's `indicspecies` package) requires reasonable sample sizes for permutation testing. With n=3, the indicator values will be unstable and significance testing unreliable.

**Recommended action**: Consider replacing indicator species analysis with a simpler presence/absence characterization: which ASVs are found in all 3 replicates of one history but 0/3 replicates of the other? This is a more robust signal with n=3 than a quantitative indicator value.

### 10. SUGGESTION: Add a "sanity check" analysis for replicate consistency

Before any between-group analyses, the plan should verify that within-group replicates are more similar to each other than to other groups. With n=3, even one aberrant replicate could dominate a group's centroid. A simple check (PERMDISP within groups, or a dendrogram of all 21 samples colored by group) would reveal outlier replicates before they contaminate downstream analyses.

**Recommended action**: Add a sanity check step after NB02 (or at the start of NB04) that explicitly verifies replicate consistency and identifies any outlier samples.

### 11. SUGGESTION: The literature context section should be populated before analysis

The plan notes "To be expanded with `/literature-review` before analysis begins" -- this is good practice. However, the literature context should specifically cover:

- Expected effect sizes for lignin enrichment experiments (to calibrate power expectations)
- Existing evidence for ecological memory in microbial enrichment cultures
- Methodological recommendations for small-sample amplicon studies

This should be completed before analysis, as the literature may inform decisions about rarefaction depth, filtering, and statistical approaches.

### 12. SUGGESTION: Consider phylogenetic diversity metrics

The plan includes standard alpha diversity metrics (Shannon, Simpson, Chao1, Pielou's) but does not include any phylogenetic diversity measures (e.g., Faith's PD, weighted/unweighted UniFrac for beta diversity). For 16S data, phylogenetic metrics can be more sensitive to community shifts because they weight closely-related ASVs differently from distantly-related ones. UniFrac is particularly standard for 16S-based beta diversity.

**Recommended action**: Add Faith's PD to alpha diversity (NB03) and UniFrac distances to beta diversity (NB04). Note that UniFrac requires a phylogenetic tree of ASVs, which should be generated in NB01.

### 13. SUGGESTION: BERDL cross-referencing scope should be tightened

The potential BERDL cross-references (mapping enriched genera to pangenome data, GapMind pathway completeness, Fitness Browser data) are interesting but could become a scope creep risk. The plan should specify:

- What minimum number of enriched genera would justify the BERDL analysis?
- What constitutes a "match" between an amplicon-derived genus name and a pangenome species?
- Is the taxonomic resolution of 16S/ITS amplicons (often genus-level at best) sufficient for meaningful pangenome-level inference?

**Recommended action**: Add a brief decision criterion for when BERDL cross-referencing will be pursued (e.g., "if 3+ genera are significantly enriched by lignin and have pangenome data available in BERDL") and acknowledge the genus-vs-species resolution mismatch.

---

## Recommended Changes (Summary)

**Must-fix before analysis:**

1. Add a "Statistical Limitations" section acknowledging n=3 power constraints and the pairwise PERMANOVA permutation floor (Issues 1, 2).
2. Pre-register key bioinformatics decisions: rarefaction strategy, ASV vs OTU, filtering thresholds (Issue 3).
3. Restructure the PERMANOVA design to exploit the nested experimental structure (Issue 4).

**Should-fix for methodological rigor:**

4. Add Aitchison distance to beta diversity analysis (Issue 5).
5. Clarify the interpretive framework for 16S-ITS concordance testing (Issue 6).
6. Reframe differential abundance (NB05) as effect-size-focused and consider targeted testing of pre-specified lignolytic genera (Issue 7).
7. Document technical metadata and batch effect assessment (Issue 8).

**Recommended additions:**

8. Add replicate consistency sanity checks (Issue 10).
9. Add phylogenetic diversity metrics (Faith's PD, UniFrac) (Issue 12).
10. Complete the literature review before analysis, with attention to expected effect sizes (Issue 11).
11. Tighten BERDL cross-referencing scope with decision criteria (Issue 13).

---

## Conclusion

The experimental design is strong and the hypotheses are well-formulated. The primary risk is that the plan applies a standard-sample-size statistical toolkit to a small-sample-size experiment without adequately adjusting expectations, methods, or interpretation. With n=3, this study should be framed as hypothesis-generating rather than hypothesis-confirming, with emphasis on effect sizes, descriptive patterns, and biological plausibility rather than p-value thresholds. Making this framing explicit in the plan would strengthen both the analysis and the eventual interpretation.

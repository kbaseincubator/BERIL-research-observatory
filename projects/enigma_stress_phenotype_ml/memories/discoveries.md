# Discoveries — enigma_stress_phenotype_ml

<!-- [enigma_stress_phenotype_ml] 2026-06-29T10:52:00Z  approved-report extraction (REVIEW: REVIEW_5.md) -->

- Mercury resistance genes carry the strongest sequence-composition signature among the 11 metals tested (AUC-from-ranking=0.774), consistent with the high evolutionary conservation of the *mer* operon. This suggests sequence-composition ML is most useful for well-conserved resistance determinants. Note: the regression AUC-from-ranking (0.774) reflects within-test-organism protein ranking on a continuous fitness model; the LOGO binary classifier AUC for Hg is 0.543 (modest; n=2 genera, unreliable estimate), reflecting genus-level binary classification on held-out genera. These are not contradictory — the regression model ranks Hg-sensitive proteins effectively within organisms similar to its training set, while the binary classifier cannot predict presence/absence of Hg sensitivity in a phylogenetically distant genus.
- Amino acid composition alone (20 features) nearly matches the best 420-feature combination (aa+kmer2) for predicting metal fitness across 5 tested stressors (AUC 0.646 vs 0.656), suggesting coarse compositional bias rather than sequence context drives the signal. Caveat: feature evaluation ran on pre-org-filter labels; the 0.002 margin is within potential bias range.

---

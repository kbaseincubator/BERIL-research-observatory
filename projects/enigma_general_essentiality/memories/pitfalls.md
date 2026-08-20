# Pitfalls — enigma_general_essentiality

## ENIGMA strain codes require manual genus mapping for true LOGO

ENIGMA organism names (e.g. "Keio", "pseudo1_N1B4", "RalstoniaBSBF1503") are lab-assigned
codes, not binomial nomenclature. They contain no spaces, so `str.split().str[0]` returns the
full code — every organism gets a unique "genus," making any LOGO equivalent to LOOO.

**Fix**: Build a manual `GENUS_MAP` dict from known strain identities (see NB01). Multi-organism
genera in the 60-organism ENIGMA set: Pseudomonas (12), Ralstonia (4), Dickeya (3),
Rhodanobacter (3), Bacteroides (2), Burkholderia (2), Methanococcus (2).

This pitfall applies to any project using `labeled_pd.parquet` from `enigma_stress_phenotype_ml`
or `enigma.genome_depot_enigma` organism names. The prior `refocus/` LOGO was silently LOOO
for the same reason.

## Feature file positional alignment is implicit and unverifiable at runtime

`features_aa.parquet` and `features_kmer2.parquet` have no `protein_id` column — they are
row-aligned with `labeled_pd.parquet` by construction. NB02 uses `.iloc[train_ids]` positional
slicing where `train_ids` are original row positions from NB01.

**Risk**: If feature files are re-exported with different row ordering, alignment is silently
corrupted — no error is raised. There is no checksum or row-ID column to verify the mapping.

**Mitigation**: Always use feature files from the same `enigma_stress_phenotype_ml` run as
`labeled_pd.parquet`. Document this constraint prominently (README.md Reproduction section).

## Test-set threshold tuning inflates reported MCC

NB03 tunes the classification threshold by maximizing F1 on the held-out test set
(precision_recall_curve on y_test). This is technically test-set leakage for MCC.
AUC-ROC is threshold-independent and unaffected. For future work, tune threshold on a
validation split or use the training LOGO folds.

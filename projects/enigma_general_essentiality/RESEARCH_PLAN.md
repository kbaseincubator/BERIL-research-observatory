# Research Plan: Cross-Stressor Conditional Essentiality Prediction

## Hypotheses

**H1**: Amino acid composition and di-nucleotide k-mer (kmer2) features encode sufficient signal to
predict cross-stressor conditional essentiality (fitness < −2 in any ENIGMA RB-TnSeq condition)
above chance in a held-out test set of unseen organisms (AUC > 0.55).

**H0**: Sequence features carry no cross-stressor essentiality signal beyond organism-level
compositional bias; genus-level LOGO AUC ≈ 0.5.

**H2 (exploratory)**: Cross-stressor conditional essentiality is less phylogenetically structured
than per-stressor fitness effects — the union label averages over metal-specific and
antibiotic-specific mechanisms, potentially yielding more consistent cross-genus signal.

## Data Source

Same as `enigma_stress_phenotype_ml`:
- FitnessBrowser Spark table (`fit.genomics.lbl.gov`): continuous fitness scores per gene per condition
- 60 ENIGMA isolates with ≥1 RB-TnSeq experiment
- Protein sequences from `enigma.genome_depot_enigma`

**Label derivation**: For each protein, compute `essential_union = 1` if fitness score < −2
in ANY tested condition (across metals, antibiotics, abiotic stressors). This creates a single
binary label integrating all available stress conditions, capturing proteins whose disruption causes
fitness defects under at least one condition.

Expected positive rate: ~4–8% (consistent with known essential gene fractions in bacteria).

## Methodology

### 1. Data extraction (NB01, local — no Spark)

Reuse `enigma_stress_phenotype_ml/data/labeled_pd.parquet` (pre-computed from FitnessBrowser;
no live Spark query required). For each gene, take the minimum fitness score across all conditions.
Apply threshold: `min_fitness < −2 → essential`. Apply manual genus mapping (ENIGMA strain codes
contain no spaces, so `str.split().str[0]` returns the full code and creates LOOO, not LOGO —
see `enigma_general_essentiality/memories/pitfalls.md`). Output a single union binary label.

### 2. Feature engineering (NB02)

Reuse the aa + kmer2 feature combination validated in enigma_stress_phenotype_ml NB04
(mean cross-validation AUC = 0.656). ESM-2 embeddings from `projects/refocus/data/esm2_embeddings.parquet`
may be available if protein IDs align; include as optional high-dimensional feature block.

Feature standardization: fit scaler on training set only; apply to test and LOGO splits.

### 3. Organism-stratified train/test split (NB03)

Use `sklearn.model_selection.GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)`
with `groups = organism_id`. This ensures no organism appears in both train and test sets.

**Verification**: After splitting, assert `len(set(train_orgs) & set(test_orgs)) == 0`.

### 4. Class imbalance handling (NB03)

For a ~4–8% positive rate, use `scale_pos_weight = n_negatives / n_positives` in CatBoostClassifier.
Report AUC-ROC (threshold-independent), MCC (threshold-sensitive), and sensitivity at 90% specificity.
Threshold-tune on validation set, not test set.

### 5. True genus-level LOGO (NB03)

Extract genus label from organism name (first word) or NCBI taxonomy lookup.
Use `sklearn.model_selection.LeaveOneGroupOut()` with `groups = genus_labels` on TRAINING SET only.
Each fold trains on all genera except one and tests on all organisms from the held-out genus.

**Key correctness criterion**: Proteins from ALL organisms of the held-out genus are in the test
fold. This differs from LOOO (leave-one-organism-out), which allows same-genus organisms to remain
in training.

### 6. Metrics and reporting (NB03)

Per-fold: AUC-ROC, MCC, sensitivity, specificity, n_positive, n_negative.
Summary: mean ± SD across folds; also report weighted mean (by test set size).
Flag folds with n_positive < 5 as unreliable; exclude from mean but report separately.

## Expected Outcomes

Given that `enigma_stress_phenotype_ml` found per-metal LOGO AUC 0.53–0.62, the union label LOGO AUC
is expected in a similar range (0.52–0.65). Abiotic-dominated signal (Acid, UV, Ethanol) may push
the union slightly higher than pure-metal models.

The comparison to state-of-the-art essentiality predictors (Geptop 2013: AUC 0.57–0.96;
CNN4Essential 2026: LASP AUC 0.73) is valid IF the evaluation setup matches; our genus-level LOGO
is stricter than those benchmarks' organism-level evaluations.

## Connection to Prior Work

- Builds on feature selection result from `enigma_stress_phenotype_ml` NB04 (aa+kmer2 selected)
- Shares data source with `enigma_stress_phenotype_ml` (FitnessBrowser, 60 ENIGMA organisms)
- Provides a complementary "cross-stressor integration" view to the per-stressor regression models
- Does NOT supersede `enigma_stress_phenotype_ml`; asks a different question

## Scope Limitations

With ~60 organisms and ENIGMA's taxonomic composition, the number of distinct genera for LOGO is
approximately 25–35. Folds with <5 positive proteins will be flagged and excluded from summaries.
This is a smaller LOGO than published state-of-the-art benchmarks; comparisons must account for
this difference in scale and evaluation strictness.

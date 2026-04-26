# TODO

## Open

- [ ] **Manual spot-check of 55 positive disagreements**. The 500-gene positive sample had Claude→`already_correctly_named`; on cross-check Codex disagreed on 55 (27 `improvable_correction`, 14 `improvable_new`, 14 `recalcitrant`). These are excluded from `data/training_set/positives.jsonl`. They are candidates to *demote* an existing FB annotation or *promote* Codex's alternative name. Source: every batch in `data/codex_xcheck_positive/batch_P*/output.jsonl` joined against `data/positive_sample_500.jsonl`; rows where `codex_verdict != "already_correctly_named"` in `data/training_positive_xcheck.jsonl`.

- [ ] **Wet-lab follow-up analysis on the 42 strong-phenotype recalcitrants**. `data/negatives_strong_targets.tsv` lists genes with `|fit|≥2 AND |t|≥5` that two LLMs (with full literature read) still could not annotate. These are publishable mysteries — for each, the analysis should: (1) compile the strongest fitness conditions and likely partner pathways from cofitness, (2) identify the most experimentally tractable organism among the candidates, (3) propose a minimal genetic/biochemical assay. Top by |fit|: `Caulo::CCNA_02030` (|fit|=6.98, |t|=23), `Caulo::CCNA_02021` (|fit|=3.69, |t|=16.2), `MR1::202102` (|fit|=3.27, |t|=24.8), `Pedo557::CA265_RS09335` (|fit|=3.23, |t|=16.2), `Btheta::349844` (|fit|=2.87, |t|=15.4).

## Possible follow-ons (not committed to)

- Continue the random walk past 4,600 to grow the training set (~95% of the 137K queue is still untouched).
- Re-run the cross-check after a future PaperBLAST refresh to detect "newly resolvable" negatives.
- **Semantic recall@name analysis** on the calibration set. Token-set Jaccard ≥0.5 misses many semantically-equivalent name pairs (e.g. "Histidinol-phosphatase (EC:3.1.3.15)" vs "histidinol-phosphate phosphatase"). Run an LLM judge or sentence-embedding similarity on the 621 Claude `right_type_wrong_name` rows in `data/reann_calibration.tsv` to estimate the true semantic recall@name; expected to lift the headline 15.5% to >25%.

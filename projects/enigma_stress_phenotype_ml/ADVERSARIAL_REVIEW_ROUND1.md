# ADVERSARIAL REVIEW: enigma_stress_phenotype_ml
**Date**: 2026-06-29  
**Reviewer**: Claude (Haiku) — adversarial mode  
**Project Status**: Analysis complete with org-filter fix; regressions trained for 11/14 metals

---

## CRITICAL ISSUES (Block Scientific Validity)

### 1. **DATA LEAKAGE IN PER-ORGANISM VALIDATION — REPORT CLAIMS NOT CLEARLY DISTINGUISHED FROM TRAIN SET**

**Issue**: REPORT.md line 215 states per-organism ρ values "predominantly positive and significant" but does not explicitly state whether these are **in-sample (training organisms) or out-of-sample test organisms**.

**Evidence**:
- NB05 trains regression models per stressor using GroupShuffleSplit with `test_size=0.2` on **filtered organisms-with-data**
- NB09 then applies these trained models to ALL organisms including training organisms
- Line 214-215 of REPORT states: "Applied to tested organisms, per-organism Spearman ρ is predominantly positive and significant"
- NB09 cell `e0fdbe6c` (per-organism validation) reports ρ values for all organisms with ≥30 tested proteins **without distinguishing train/test membership**

**Why This Matters**: An organism in the training set will naturally show inflated ρ because the model was partially optimized on its data. A Cd model trained on psRCH2 + rhodanobacter_10B01 reporting ρ=0.530 on psRCH2 is in-sample validation, not an independent test. The REPORT's framing ("strong per-organism ρ indicates real signal") conflates in-sample memorization with generalization.

**Specific Examples**:
- Cd ρ=0.530 on 6,184 tested proteins — but Cd only trained on **2 organisms (psRCH2 + rhodanobacter_10B01)**. Is this ρ computed on both training organisms, or a held-out subset?
- Mn ρ=0.439 on 14,370 tested proteins — trained on only **4 organisms**. How many of those organisms' data went into training vs. testing?

**Fix Required**: Explicitly mark which organisms are training vs. test in the per-organism validation table. Report separate ρ values for:
1. Held-out test organisms (true generalization measure)
2. Training organisms (in-sample ρ, expected to be higher)

**Severity**: CRITICAL — the REPORT's interpretation of per-organism performance is potentially misleading if most tested organisms were used during training.

---

### 2. **MANGANESE (Mn) MODEL IS STATISTICALLY UNRELIABLE — REPORT CALLS IT "HIGHLY SIGNIFICANT"**

**Issue**: Mn model has ρ=0.050 with p=0.009 and **only 4 training organisms**. The REPORT (line 74) lists this alongside models with ρ>0.14, implying similar confidence.

**Evidence** (from `data/regression_model_metrics.csv`):
```
Mn    0.050128   0.008979  0.423888  0.623   14370.0   388.0  0.027001  4.0
```

**Why This Is Critical**:
- ρ=0.050 is barely above random chance (ρ=0 null)
- p=0.009 is marginally significant (not "highly significant")
- **Only 4 organisms** means the train/test split is extremely fragile
- With 4 orgs and 80/20 split, test set has ~0.8 organisms (likely just 1), making ρ unstable
- A single outlier protein can flip the sign of ρ with n=~3 test organisms

**REPORT Framing Problem**: Line 9 states "all metal stressor models suffer from severe class imbalance" — but this is presented as a **problem fixed**. The Mn model remains unfixed: it's untrustworthy, yet predictions are still output in `novel_candidates.csv`.

**Recommendation**: Either:
1. Do not train/report Mn model (declare it untrustworthy due to n_orgs=4)
2. Or add explicit caveat in REPORT: "Mn model (ρ=0.050, 4 organisms) is unreliable; novel Mn predictions should be treated with extreme skepticism"

**Severity**: CRITICAL — Mn predictions in novel_candidates.csv are scientifically unfounded.

---

### 3. **Cd MODEL HAS EXTREME OUT-OF-DISTRIBUTION GENERALIZATION ISSUE — NOT MENTIONED IN REPORT**

**Issue**: Cd model trained on 2 organisms with **very different ecology**, tested on organisms that were never experimentally tested. The two training organisms are qualitatively non-overlapping:
- **psRCH2**: anaerobic, industrial/lab strain (PSI07 background), 3,306 proteins with fitness data
- **rhodanobacter_10B01**: aerobic soil isolate, 2,878 proteins with fitness data

No other ENIGMA organisms have Cd experiments. Cd predictions for the other 58 organisms are **extreme out-of-distribution** (different phylogeny, ecology, oxygen availability).

**Evidence** (from labeled_pd analysis):
```
Organisms with Cd positives: psRCH2, rhodanobacter_10B01 (only)
Total organisms: 60
Untested: 58 (96.7%)
```

**Why This Is Critical**:
- Test-set ρ=0.199 is measured on data from the same 2 organisms used for training (no true test set)
- Predictions for 208,867 proteins in 58 untested organisms are extrapolations across:
  - Phylogenetic distance (different bacterial taxa)
  - Metabolic ecology (aerobic vs. anaerobic)
  - Growth conditions (divergent evolutionary pressures on Cd detoxification)
- AUC_from_ranking=0.556 is barely above random chance

**Specific Problem Identified**: The regression training code (NB05 cell `a6715cf2`) creates per-stressor splits:
```python
gss_s = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=SEED)
s_train_idx, s_test_idx = next(gss_s.split(X, y, groups=g))
```

With 2 organisms and 80/20 split, the test set likely contains **1 organism (possibly split within an organism)**. This is not a cross-organism generalization test.

**REPORT Statement to Challenge** (line 66): "Cd | 0.199 | 3.2e-27 | 0.556 | 6,184 | 2"
- The ρ is significant because there are 6,184 proteins tested
- But **all 6,184 proteins come from 2 organisms** with identical ecological history
- This is not evidence that Cd predictions generalize to the other 58 organisms

**Recommendation**: Add explicit disclaimer:
> "Cd regression model: trained on only 2 ENIGMA organisms (psRCH2: anaerobic; rhodanobacter_10B01: aerobic) with no cross-organism validation. Novel predictions for untested organisms should be treated as hypotheses only. Cross-validation not performed due to insufficient organism count."

**Severity**: CRITICAL — Novel Cd candidates (208,867 proteins in 58 untested organisms) lack scientific grounding.

---

### 4. **FEATURE SELECTION BIAS — NB04 MAY HAVE RUN ON CONTAMINATED LABELED_PD**

**Issue**: Feature selection in NB04 (`notebooks/04_Feature_Evaluation.ipynb`) loaded `labeled_pd` with **no organism filtering**, potentially using contaminated labels (fillna(0) false-negatives).

**Evidence**:
- File timestamps: `data/best_feature_combination.json` created June 26, 20:16
- NB01 org-filter fix applied: commit 601a06bd (June 29, 01:56)
- NB04 does not filter to organisms-with-data before ranking feature sets

**Timeline**:
1. June 25: Features computed
2. June 26: NB04 run → selected aa+kmer2 (likely on contaminated data)
3. June 29: Org-filter fix applied in NB05

**Why This Matters**:
- If NB04 ranked features using contaminated labels (39 organisms with zero Zn experiments labeled as negative), it may have selected a feature combination that works on the false-negative pattern, not on true biology
- This would explain why aa+kmer2 (simple feature set) outperformed learned ESM-2 embeddings (ρ>0.3 in NB04) but yields only ρ~0.20 in regression despite the org-filter fix

**Recommendation**: Re-run NB04 on cleaned labeled_pd (or verify that it doesn't use contaminated labels). If feature selection must be repeated, use stratified CV on organisms-with-data.

**Severity**: CRITICAL if feature selection is actually biased; at minimum requires verification.

---

## IMPORTANT ISSUES (Significant But Not Fatal)

### 5. **REGRESSION MODELS HAVE WEAK ABSOLUTE SIGNAL — ρ < 0.25 FOR ALL METALS**

**Evidence** (from regression_model_metrics.csv):
```
Co   0.230
Cu   0.198
Cd   0.199
Zn   0.195
Hg   0.175
Ni   0.159
Se   0.155
Fe   0.148
Cr   0.141
Al   0.105
Mn   0.050
```

**Interpretation**: Even the best model (Co, ρ=0.230) explains <6% of variance in fitness (R²=ρ²=0.053). AUC_from_ranking of 0.688 means the model ranks proteins only 18.8 percentage points better than random (AUC=0.5).

**Why This Matters**:
- REPORT line 76 frames these as "statistically significant" (true, p<0.05) but does not emphasize **weak practical signal**
- A practitioner reading the REPORT might select top-20 candidates assuming strong predictive power; in reality, a random selection might be ~83% as effective
- Hg's high AUC (0.774) is presented as "strong protein-sequence signal" (line 76), but Hg only has 9 training organisms
- Novel candidates ranked by these weak models may have no better-than-random chance of being true Cd/Mn resistance genes

**REPORT Context**: The Executive Summary (line 11) is honest about metal model weakness: "all metal stressor models suffer from severe class imbalance, predicting all-negative regardless of input." But the Regression Results section (line 58) pivots to regression as a solution without explicitly noting that regression signal is also weak.

**Recommendation**: Qualify novel candidate rankings with effect-size disclaimers:
> "Ranking proteins by predicted fitness offers modest improvement over random (AUC 0.556–0.774). Top-ranked candidates should be prioritized for experimental validation, but the absolute predictive power is low."

**Severity**: IMPORTANT — Honest enough in REPORT, but could be clearer.

---

### 6. **MULTI-METAL CANDIDATE OVERCLAIMED — PROTEIN ANNOTATION NOT VERIFIED**

**Issue**: REPORT line 219 highlights `acidovorax_3H11|Ac3H11_638` as "the single protein predicted top-50 for all 11 metals" with "genuine broad stress-essentiality," claiming it is "operon co-essential with metal resistance genes."

**Evidence**:
- Protein: `acidovorax_3H11|Ac3H11_638`
- Annotation: "L(+)-tartrate dehydratase beta subunit"
- Actual fitness values (from all_protein_predictions.parquet):
  - Co_fit: **-2.82** ✓ (below -2 threshold, genuine fitness defect)
  - Zn_fit: -0.55 (not below threshold)
  - Cu_fit: -0.29 (not below threshold)
  - Ni_fit: -0.73 (not below threshold)
  - Al_fit: -1.07 (not below threshold)
  - Fe_fit: -0.70 (not below threshold)

**Why This Is Problematic**:
1. **Annotation Issue**: L(+)-tartrate dehydratase is a **metabolic enzyme in central carbon metabolism**, not a known metal transporter/resistor
2. **Fitness Pattern**: Co_fit=-2.82 is a strong signal, but other metals show weak/no signal. This does not suggest "broad stress-essentiality" — it suggests **Co-specific essentiality**
3. **Speculative Claim**: "operon co-essential with metal resistance genes" is unsupported; if Ac3H11_638 is in an operon with a metal transporter, it would only be essential if the transporter is also essential for that specific metal
4. **Missed Deeper Issue**: Many proteins are predicted top-50 for 10+ metals not due to metal resistance, but due to general growth impairment or metabolic coupling

**Recommendation**: Either:
1. Remove or downgrade this example (it's a single protein, not a validated candidate)
2. Or qualify: "acidovorax_3H11|Ac3H11_638 shows strong Co-specific essentiality (fitness=-2.82); interpretation as a multi-metal resistance regulator is speculative and requires experimental validation"

**Severity**: IMPORTANT — Overstates the biological interpretation of a single protein.

---

### 7. **BINARY CLASSIFICATION F1 SCORES ARE ABYSMAL — "IMPROVED" AFTER FIX BUT STILL UNUSABLE**

**Evidence** (from final_model_performance.csv and best_thresholds.json):
```
After org-filter fix:
Zn:  F1=0.030  (threshold=0.38)
Cu:  F1=0.125
Co:  F1=0.063
Ni:  F1=0.037
Al:  F1=0.075
Cr:  F1=0.000  (no positive predictions at any threshold)
Fe:  F1=0.000
Se:  F1=0.004  (threshold=0.01)
Hg:  F1=0.009  (threshold=0.02)
Mn:  F1=0.000  (threshold=0.01)
```

**Why This Matters**:
- REPORT line 94 states "threshold tuning improves F1 slightly for metals" — this is true but misleading; F1 values remain <0.15 for all metals
- These F1 scores indicate the models are **useless for binary classification** even after fixing the org-filter
- The implicit reasoning: "regression is better" — true, but regression also has weak signal
- Users might assume "after fixing contamination, metal models work better" without realizing that class imbalance (1–2% positives) is **still unsolved**

**Root Cause Not Fixed**: The org-filter fix removes false negatives but does NOT address the underlying issue:
- Even with only organisms-with-data, positive rates remain ~1–2%
- This is a fundamental property of the data: metal resistance genes are rare
- Gradient boosting cannot learn a useful decision boundary at 1–2% positive rate without sacrificing recall (getting all the positives means too many false positives)

**Recommendation**: Acknowledge that binary classification is not viable for metals; prioritize regression/ranking approach. Add to REPORT:
> "Binary classification is not recommended for metal stressors due to extreme class imbalance (1–2% positives after organism filtering). Regression-based ranking is the only viable approach."

**Severity**: IMPORTANT — Honest in REPORT but could be more explicit.

---

### 8. **CDTEST SET SIZE UNDISCLOSED — Cd REGRESSION HAS ONLY ~1 TEST ORGANISM**

**Issue**: With 2 organisms and 80/20 split, Cd's test set has **~0.4 organisms** (likely <150 proteins from a single organism or a fragment of one). This is not enough for reliable Spearman ρ.

**Evidence**:
- Cd has 6,184 total tested proteins across 2 organisms
- psRCH2: 3,306 proteins; rhodanobacter_10B01: 2,878 proteins
- 80/20 split on 6,184 → training: 4,947, test: 1,237
- **But which organism is in the test set?** Likely a 80/20 split within an organism, meaning test set is ~0.2 × 1 organism = <15% of one organism's proteins

**Why This Matters**:
- Spearman ρ computed on 1,237 proteins from potentially 1 organism is unstable
- ρ=0.199 could be an artifact of that specific organism's fitness distribution
- Generalization to the other 58 untested organisms is completely speculative

**Recommendation**: Report test-set composition explicitly:
> "Cd model test set: approximately X proteins from Y organisms (details in regression_predictions.parquet)"

**Severity**: IMPORTANT — Undermines confidence in Cd ρ=0.199.

---

### 9. **"NOVEL CANDIDATES" CLAIM IS MISLEADING — MOST ARE WEAK PREDICTIONS**

**Issue**: REPORT line 225 claims "7,840 rows" of novel candidates. But analysis reveals:

**Evidence** (from novel_candidates.csv):
```
Unique organisms: 59
Unique metals: 11
Predicted fitness distribution (Zn example):
  Mean: -1.159
  Min: -2.610
  Max: -0.842
  <-2 (binary-positive threshold): 11 out of 7,840 (0.14%)
```

**Why This Matters**:
- The 7,840 candidates are the **top-20 per metal per organism** for untested organisms
- But predicted fitness is centered around -1.1, far from the -2.0 threshold used to define true positives
- 99.86% of "novel candidates" have predicted fitness > -2.0, meaning they are predicted to NOT have a fitness defect
- A naive list of "any protein from untested organisms" would be equally valid

**REPORT Statement to Challenge** (line 225):
> "data/predictions/novel_candidates.csv — untested organisms only (7,840 rows)"

This implies these 7,840 are high-priority candidates, but the actual interpretation is: "top-20 ranked proteins per metal per organism, most with weak predicted effects."

**Recommendation**: Clarify in REPORT and data dictionary:
> "Novel candidates are ranked by predicted fitness (most negative = highest priority). However, predicted fitness values are weak (mean -1.16, centered far above the -2.0 binary threshold). These are exploratory candidates for hypothesis generation, not high-confidence predictions."

**Severity**: IMPORTANT — Overclaims the strength of novel candidates.

---

## MINOR ISSUES (Polish)

### 10. **REPORT DOES NOT CLEARLY STATE "Cd MODEL ONLY TRAINED ON 2 ORGANISMS"**

Currently buried in line 181: "Cd model trains with 2 organisms (ρ=0.199, AUC=0.556)." Should be prominently featured in Limitations section.

---

### 11. **FEATURE SELECTION METRIC (AUC=0.656) NOT TRACED TO TEST SET**

NB04 reports "best feature combination was: aa + kmer2 with average AUC = 0.656" but does not clarify: is this train-set AUC, cross-validation AUC, or test-set AUC? If it's cross-validation, using the same labeled_pd for both feature selection and model training risks data leakage.

---

### 12. **MISSING CROSS-VALIDATION FOR REGRESSION MODELS**

NB06 is mentioned as "pending" (REPORT line 234), but regression models in NB05 were trained without LOGO cross-validation. Report should note: "Regression models trained on single 80/20 split; LOGO cross-validation pending in NB06."

---

### 13. **"HIGHLY SIGNIFICANT P-VALUES" CLAIM USES MULTIPLE TESTING WITHOUT ADJUSTMENT**

REPORT line 76 states "all models show statistically significant Spearman rank correlations" — this is 11 independent tests without Bonferroni correction. With α=0.05, expect ~0.55 false positives. Should adjust α→0.0045 or declare multiple-testing correction.

---

### 14. **MISSING DATA PROVENANCE FOR Cd AND Mn**

Where do Cd and Mn fitness data originate? REPORT line 172 mentions "14 organisms downloaded from FitnessBrowser" — are all 14 included in labeled_pd.parquet? Trace explicitly.

---

## SUMMARY TABLE

| Issue | Severity | Category | Fix Required? |
|-------|----------|----------|---------------|
| In-sample vs. test-set leakage in per-org validation | CRITICAL | Methodology | Yes (re-evaluate ρ values) |
| Mn model unreliable (ρ=0.050, 4 orgs) | CRITICAL | Data Quality | Yes (exclude or caveat heavily) |
| Cd extreme OOD generalization (2 orgs, 96.7% untested) | CRITICAL | Methodology | Yes (add disclaimer) |
| Feature selection bias (NB04 on contaminated data?) | CRITICAL | Reproducibility | Yes (verify/re-run) |
| Weak absolute signal (ρ < 0.25 for all models) | IMPORTANT | Interpretation | Caveat |
| Multi-metal protein overclaimed | IMPORTANT | Interpretation | Downgrade example |
| Binary F1 scores abysmal (<0.15) | IMPORTANT | Context | Clarify |
| Cd test set likely <1 organism | IMPORTANT | Methodology | Disclose |
| "Novel candidates" misleading (99.86% weak) | IMPORTANT | Interpretation | Clarify |
| Cd training count not prominent | MINOR | Clarity | Reposition |
| Feature selection AUC metric unclear | MINOR | Clarity | Define |
| Regression models lack cross-validation | MINOR | Completeness | Note pending |
| Multiple testing not corrected | MINOR | Rigor | Adjust α |
| Cd/Mn data provenance missing | MINOR | Reproducibility | Trace |

---

## CONCLUSION

The project has made genuine progress on the binary classification problem (org-filter fix is sound), but regression models remain weak (ρ < 0.25), and critical organisms (Cd: 2, Mn: 4) lack sufficient sample size for reliable generalization. The REPORT is largely honest but undersells weaknesses in the Regression section and overclaims confidence in multi-metal candidates.

**Blocking Issues**: Feature selection bias (NB04), data leakage in per-org validation, Cd and Mn extreme limitations not clearly stated.

**Path Forward**:
1. Verify NB04 was not run on contaminated data
2. Separate train/test organisms in per-org validation table
3. Add explicit disclaimers for Cd (2 orgs) and Mn (4 orgs, ρ=0.050)
4. Downgrade multi-metal example or provide deeper annotation
5. Run NB06 LOGO cross-validation to test true generalization


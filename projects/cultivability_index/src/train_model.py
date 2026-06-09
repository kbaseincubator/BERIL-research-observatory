"""
NB03 predictive model: family-stratified train/test split, logistic + gradient
boosted classifier on the 80-pathway feature matrix, benchmarked against
CheckM-only and taxonomy-only baselines.
"""
from pathlib import Path
import warnings
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss
from sklearn.dummy import DummyClassifier

PROJ = Path(__file__).resolve().parent.parent
DATA = PROJ / "data"

warnings.filterwarnings("ignore")
rng = np.random.default_rng(20260526)

feat = pd.read_parquet(DATA / "features.parquet")
pathway_cols = [c for c in feat.columns if c.startswith(("aa__", "carbon__"))]
print(f"Cohort: {len(feat):,} genomes; {len(pathway_cols)} pathway features")

# ---- restrict to families that have >=5 of each label ----
fam_counts = feat.groupby("family")["is_isolate"].agg(n_iso="sum", n_total="size")
fam_counts["n_mag"] = fam_counts["n_total"] - fam_counts["n_iso"]
balanced_fams = fam_counts[(fam_counts.n_iso >= 5) & (fam_counts.n_mag >= 5)].index.tolist()
df = feat[feat["family"].isin(balanced_fams)].copy().reset_index(drop=True)
print(f"Balanced cohort: {len(df):,} genomes across {len(balanced_fams)} families "
      f"({df.is_isolate.sum():,} isolate, {(1-df.is_isolate).sum():,} MAG)")

# ---- 80/20 family-level train/test split ----
fams = list(balanced_fams)
rng.shuffle(fams)
test_fams = set(fams[: int(0.20 * len(fams))])
train_fams = set(fams) - test_fams
train_mask = df["family"].isin(train_fams)
test_mask = df["family"].isin(test_fams)
print(f"Train: {train_mask.sum():,} genomes / {len(train_fams)} families")
print(f"Test:  {test_mask.sum():,} genomes / {len(test_fams)} families")

X_path = df[pathway_cols].astype(float).values
y = df["is_isolate"].astype(int).values
checkm = df[["checkm_comp", "genome_size", "gc_pct", "contig_count", "n50_contigs"]].astype(float).values

# Standardize covariates
sc = StandardScaler().fit(checkm[train_mask])
checkm_std = sc.transform(checkm)

def fit_eval(X_tr, y_tr, X_te, y_te, name, n_path=None):
    clf = LogisticRegression(
        penalty="l1", solver="saga", C=0.5, max_iter=2000,
        class_weight="balanced", n_jobs=4,
    )
    clf.fit(X_tr, y_tr)
    p = clf.predict_proba(X_te)[:, 1]
    auc = roc_auc_score(y_te, p)
    ap = average_precision_score(y_te, p)
    bs = brier_score_loss(y_te, p)
    nonzero = int((np.abs(clf.coef_[0]) > 1e-8).sum())
    print(f"  {name:30s}  AUC={auc:.4f}  AP={ap:.4f}  Brier={bs:.4f}  "
          f"nonzero_coefs={nonzero}/{X_tr.shape[1]}")
    return clf, p, dict(name=name, auc=auc, ap=ap, brier=bs, n_features=X_tr.shape[1], nonzero=nonzero)

print("\n== Models (held-out-family test set) ==")
results = []
# Baseline 1: CheckM only
r1 = fit_eval(checkm_std[train_mask], y[train_mask], checkm_std[test_mask], y[test_mask],
              "checkm + size + gc + n50")
results.append(r1[2])

# Baseline 2: family-mean only (Bayesian shrinkage)
fam_mean = df[train_mask].groupby("family")["is_isolate"].mean()
fam_default = df[train_mask]["is_isolate"].mean()
p_fam = df.loc[test_mask, "family"].map(fam_mean).fillna(fam_default).values
auc_fam = roc_auc_score(y[test_mask], p_fam)
ap_fam = average_precision_score(y[test_mask], p_fam)
print(f"  {'family-mean only':30s}  AUC={auc_fam:.4f}  AP={ap_fam:.4f}  (held-out families have NO seen-during-training rate, so model returns the global default)")
results.append(dict(name="family-mean only", auc=auc_fam, ap=ap_fam, brier=brier_score_loss(y[test_mask], p_fam), n_features=1, nonzero=1))

# Pathway only
r2 = fit_eval(X_path[train_mask], y[train_mask], X_path[test_mask], y[test_mask],
              "pathway (80 features)")
results.append(r2[2])

# Pathway + checkm
X_full = np.hstack([X_path, checkm_std])
r3 = fit_eval(X_full[train_mask], y[train_mask], X_full[test_mask], y[test_mask],
              "pathway + checkm (85 features)")
results.append(r3[2])

# Constant predictor
const = DummyClassifier(strategy="prior").fit(X_full[train_mask], y[train_mask])
p_const = const.predict_proba(X_full[test_mask])[:, 1]
auc_const = roc_auc_score(y[test_mask], p_const)
print(f"  {'constant predictor':30s}  AUC={auc_const:.4f}  AP={average_precision_score(y[test_mask], p_const):.4f}")

# ---- save results ----
res_df = pd.DataFrame(results)
res_df.to_csv(DATA / "model_metrics.tsv", sep="\t", index=False, float_format="%.4f")
print("\nWrote data/model_metrics.tsv")

# ---- coefficient inspection for the pathway+checkm model ----
clf_full, p_full, _ = r3
coef = pd.DataFrame({
    "feature": pathway_cols + ["checkm_comp", "genome_size", "gc_pct", "contig_count", "n50_contigs"],
    "coef": clf_full.coef_[0],
}).sort_values("coef")
coef.to_csv(DATA / "model_coefficients.tsv", sep="\t", index=False, float_format="%.4f")
print(f"Wrote data/model_coefficients.tsv ({len(coef)} features)")

print("\nTop 10 isolate-predictive features:")
print(coef.tail(10).to_string(index=False))
print("\nTop 10 MAG-predictive features:")
print(coef.head(10).to_string(index=False))

# ---- save predictions for NB04 (applied to all HQ MAGs in the full cohort) ----
# Retrain on the entire balanced cohort, then predict on ALL HQ uncultured genomes
print("\n== Retraining on balanced cohort, applying to all HQ uncultured genomes ==")
clf_final = LogisticRegression(
    penalty="l1", solver="saga", C=0.5, max_iter=2000,
    class_weight="balanced", n_jobs=4,
)
sc_final = StandardScaler().fit(checkm)
checkm_std_full = sc_final.transform(checkm)
X_final = np.hstack([X_path, checkm_std_full])
clf_final.fit(X_final, y)

# Apply to ALL HQ uncultured genomes (including those outside the balanced family subset)
feat["aa_frac"] = feat[[c for c in feat.columns if c.startswith("aa__")]].mean(axis=1)
feat["carbon_frac"] = feat[[c for c in feat.columns if c.startswith("carbon__")]].mean(axis=1)
X_all_path = feat[pathway_cols].astype(float).values
X_all_check = sc_final.transform(feat[["checkm_comp", "genome_size", "gc_pct", "contig_count", "n50_contigs"]].astype(float).values)
X_all = np.hstack([X_all_path, X_all_check])
feat["p_isolate"] = clf_final.predict_proba(X_all)[:, 1]
print(f"  P(isolate) distribution on all {len(feat):,} HQ genomes:")
print(feat["p_isolate"].describe().to_string())

# Save scored cohort (slim columns for NB04)
slim_cols = ["genome_id", "raw_category", "is_isolate", "p_isolate", "checkm_comp",
             "genome_size", "gc_pct", "aa_frac", "carbon_frac", "phylum", "class", "order", "family", "genus", "species"]
feat[slim_cols].to_parquet(DATA / "scored_genomes.parquet", index=False)
print(f"Wrote data/scored_genomes.parquet")

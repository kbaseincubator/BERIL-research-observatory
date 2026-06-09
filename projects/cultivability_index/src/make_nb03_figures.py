"""NB03 figures: ROC curves, feature importance, score distributions."""
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_curve, average_precision_score, roc_auc_score

PROJ = Path(__file__).resolve().parent.parent
DATA = PROJ / "data"
FIGS = PROJ / "figures"

rng = np.random.default_rng(20260526)
feat = pd.read_parquet(DATA / "features.parquet")
pathway_cols = [c for c in feat.columns if c.startswith(("aa__", "carbon__"))]
covariate_cols = ["checkm_comp", "genome_size", "gc_pct", "contig_count", "n50_contigs"]

fam_counts = feat.groupby("family")["is_isolate"].agg(n_iso="sum", n_total="size")
fam_counts["n_mag"] = fam_counts["n_total"] - fam_counts["n_iso"]
balanced_fams = list(fam_counts[(fam_counts.n_iso >= 5) & (fam_counts.n_mag >= 5)].index)
df = feat[feat["family"].isin(balanced_fams)].copy().reset_index(drop=True)

fams = list(balanced_fams); rng.shuffle(fams)
test_fams = set(fams[: int(0.20 * len(fams))])
test_mask = df["family"].isin(test_fams).values
train_mask = ~test_mask

X_path = df[pathway_cols].astype(float).values
X_cov = StandardScaler().fit(df.loc[train_mask, covariate_cols]).transform(df[covariate_cols])
y = df["is_isolate"].astype(int).values

# Refit the three models
import warnings; warnings.filterwarnings("ignore")
LR = lambda **kw: LogisticRegression(penalty="l1", solver="saga", C=0.5, max_iter=2000, class_weight="balanced", n_jobs=4, **kw)

clf_cov = LR().fit(X_cov[train_mask], y[train_mask])
clf_path = LR().fit(X_path[train_mask], y[train_mask])
clf_full = LR().fit(np.hstack([X_path, X_cov])[train_mask], y[train_mask])

p_cov = clf_cov.predict_proba(X_cov[test_mask])[:, 1]
p_path = clf_path.predict_proba(X_path[test_mask])[:, 1]
p_full = clf_full.predict_proba(np.hstack([X_path, X_cov])[test_mask])[:, 1]
y_te = y[test_mask]

# ----- ROC curves -----
fig, ax = plt.subplots(figsize=(6, 5.5))
for p, lbl, color in [
    (p_cov,  f"covariates only  AUC={roc_auc_score(y_te, p_cov):.3f}", "steelblue"),
    (p_path, f"pathway only (80) AUC={roc_auc_score(y_te, p_path):.3f}", "darkorange"),
    (p_full, f"pathway + cov (85) AUC={roc_auc_score(y_te, p_full):.3f}", "seagreen"),
]:
    fpr, tpr, _ = roc_curve(y_te, p)
    ax.plot(fpr, tpr, label=lbl, color=color, lw=2)
ax.plot([0, 1], [0, 1], "k--", lw=0.5)
ax.set_xlabel("False positive rate")
ax.set_ylabel("True positive rate")
ax.set_title(f"Held-out-family ROC ({test_mask.sum():,} genomes from {len(test_fams)} unseen families)")
ax.legend(loc="lower right")
ax.set_xlim(-0.02, 1.02); ax.set_ylim(-0.02, 1.02); ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(FIGS / "roc_curves.png", dpi=150, bbox_inches="tight")
plt.close()
print("Wrote figures/roc_curves.png")

# ----- feature importance (split into aa, carbon, covariate) -----
coef = pd.read_csv(DATA / "model_coefficients.tsv", sep="\t")
def color(name):
    if name.startswith("aa__"): return "#1f77b4"
    if name.startswith("carbon__"): return "#ff7f0e"
    return "#2ca02c"

# Top 20 isolate-predictive + top 20 MAG-predictive
isolate_pred = coef.tail(20).iloc[::-1]
mag_pred = coef.head(20)

fig, axes = plt.subplots(1, 2, figsize=(12, 7), sharex=False)
for ax, sub, title in zip(axes, [isolate_pred, mag_pred], ["Top 20 isolate-predictive", "Top 20 MAG-predictive"]):
    colors = [color(n) for n in sub["feature"]]
    ax.barh(np.arange(len(sub))[::-1], sub["coef"], color=colors)
    ax.set_yticks(np.arange(len(sub))[::-1])
    ax.set_yticklabels(sub["feature"], fontsize=8)
    ax.axvline(0, color="black", lw=0.5)
    ax.set_xlabel("L1-LR coefficient")
    ax.set_title(title)
    ax.grid(axis="x", alpha=0.3)
# legend
for c, lbl in [("#1f77b4", "amino acid biosynthesis"), ("#ff7f0e", "carbon utilization"), ("#2ca02c", "covariate")]:
    axes[0].scatter([], [], c=c, s=80, label=lbl)
axes[0].legend(loc="lower right", fontsize=8)
plt.tight_layout()
plt.savefig(FIGS / "feature_importance.png", dpi=150, bbox_inches="tight")
plt.close()
print("Wrote figures/feature_importance.png")

# ----- score distributions: NB04 preview -----
scored = pd.read_parquet(DATA / "scored_genomes.parquet")
fig, ax = plt.subplots(figsize=(7.5, 4.5))
ax.hist(scored.loc[scored.is_isolate == 1, "p_isolate"], bins=50, alpha=0.55, color="steelblue", density=False,
        label=f"isolates ({int(scored.is_isolate.sum()):,})")
ax.hist(scored.loc[scored.is_isolate == 0, "p_isolate"], bins=50, alpha=0.55, color="indianred", density=False,
        label=f"MAGs ({int((1-scored.is_isolate).sum()):,})")
ax.set_xlabel("P(isolate) — model score")
ax.set_ylabel("count")
ax.set_title("Score distribution across all 235,671 HQ genomes")
ax.legend()
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(FIGS / "score_distribution.png", dpi=150, bbox_inches="tight")
plt.close()
print("Wrote figures/score_distribution.png")

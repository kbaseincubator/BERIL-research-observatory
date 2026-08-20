"""NB02 figures: per-pathway forest plot and category summary."""
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJ = Path(__file__).resolve().parent.parent
DATA = PROJ / "data"
FIGS = PROJ / "figures"
FIGS.mkdir(exist_ok=True)

res = pd.read_csv(DATA / "per_pathway_or.tsv", sep="\t")
sig = res[res.mh_q < 0.05].copy()
print(f"MH q<0.05: {len(sig)} of {len(res)} pathways")

# ----- forest plot of top 30 pathways (largest absolute log MH-OR) -----
top = sig.assign(log_or=np.log2(sig.mh_or)).copy()
top["abs_log_or"] = top["log_or"].abs()
top = top.sort_values("abs_log_or", ascending=False).head(30).sort_values("log_or")

fig, ax = plt.subplots(figsize=(8, 9))
colors = ["#1f77b4" if c == "aa" else "#ff7f0e" for c in top.metabolic_category]
y = np.arange(len(top))
ax.errorbar(
    np.log2(top.mh_or), y,
    xerr=[np.log2(top.mh_or) - np.log2(top.mh_ci_lo), np.log2(top.mh_ci_hi) - np.log2(top.mh_or)],
    fmt="o", color="grey", ecolor="lightgrey", markersize=0, capsize=2, zorder=1,
)
ax.scatter(np.log2(top.mh_or), y, c=colors, s=60, zorder=2)
ax.axvline(0, color="black", lw=0.5)
ax.set_yticks(y)
ax.set_yticklabels([f"{r.metabolic_category}__{r.pathway_name}" for _, r in top.iterrows()], fontsize=9)
ax.set_xlabel("log₂ Mantel-Haenszel OR (isolate vs MAG)\nfamily-controlled, q<0.05")
ax.set_title(f"Top 30 pathways by |log₂ MH-OR|  (n={len(res)} pathways tested)")
ax.grid(axis="x", alpha=0.3)
# legend
for cat, c, lbl in [("aa", "#1f77b4", "amino acid biosynthesis"), ("carbon", "#ff7f0e", "carbon utilization")]:
    ax.scatter([], [], c=c, s=60, label=lbl)
ax.legend(loc="lower right", fontsize=9)
plt.tight_layout()
plt.savefig(FIGS / "per_pathway_forest.png", dpi=150, bbox_inches="tight")
plt.close()
print(f"Wrote figures/per_pathway_forest.png")

# ----- category summary: pooled vs MH effect -----
fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
for ax, cat, title in zip(axes, ["aa", "carbon"], ["Amino acid biosynthesis", "Carbon utilization"]):
    sub = res[res.metabolic_category == cat].copy()
    sub["log_pooled"] = np.log2(sub.pooled_or)
    sub["log_mh"] = np.log2(sub.mh_or)
    sub = sub.sort_values("log_pooled")
    x = np.arange(len(sub))
    ax.bar(x - 0.2, sub.log_pooled, 0.4, label="pooled (phylogeny-confounded)", color="lightcoral", alpha=0.9)
    ax.bar(x + 0.2, sub.log_mh, 0.4, label="Mantel-Haenszel (family-controlled)", color="steelblue", alpha=0.9)
    ax.axhline(0, color="black", lw=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(sub.pathway_name, rotation=90, fontsize=7)
    ax.set_ylabel("log₂ OR (isolate vs MAG)")
    ax.set_title(f"{title}  (n={len(sub)} pathways)")
    ax.legend(loc="lower right", fontsize=8)
plt.tight_layout()
plt.savefig(FIGS / "pooled_vs_mh_or.png", dpi=150, bbox_inches="tight")
plt.close()
print(f"Wrote figures/pooled_vs_mh_or.png")

# ----- aa vs carbon completeness summary -----
feat = pd.read_parquet(DATA / "features.parquet")
aa_cols = [c for c in feat.columns if c.startswith("aa__")]
carbon_cols = [c for c in feat.columns if c.startswith("carbon__")]
feat["aa_frac"] = feat[aa_cols].mean(axis=1)
feat["carbon_frac"] = feat[carbon_cols].mean(axis=1)
labels = feat["is_isolate"].map({1: "isolate", 0: "MAG/uncultured"})

fig, axes = plt.subplots(1, 2, figsize=(10, 4))
for ax, col, title in zip(axes, ["aa_frac", "carbon_frac"], ["Amino acid biosynthesis completeness", "Carbon utilization completeness"]):
    iso = feat.loc[feat.is_isolate == 1, col]
    mag = feat.loc[feat.is_isolate == 0, col]
    ax.hist(iso, bins=40, alpha=0.6, label=f"isolate (n={len(iso):,}, μ={iso.mean():.3f})", color="steelblue", density=True)
    ax.hist(mag, bins=40, alpha=0.6, label=f"MAG (n={len(mag):,}, μ={mag.mean():.3f})", color="indianred", density=True)
    ax.set_xlabel("fraction of pathways complete")
    ax.set_ylabel("density")
    ax.set_title(title)
    ax.legend(loc="upper left", fontsize=8)
plt.tight_layout()
plt.savefig(FIGS / "aa_vs_carbon_summary.png", dpi=150, bbox_inches="tight")
plt.close()
print(f"Wrote figures/aa_vs_carbon_summary.png")

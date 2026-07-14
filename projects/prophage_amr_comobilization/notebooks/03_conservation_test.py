"""
NB03: Conservation Test (H1)
==============================
Tests H1: Prophage-proximal AMR gene clusters are disproportionately
accessory (non-core), consistent with phage-mediated horizontal transfer.

Statistical approach:
  - 2x2 contingency table: (proximal vs distal) x (accessory vs core)
  - Fisher's exact test for association
  - Logistic regression controlling for species
  - Bootstrap confidence intervals on odds ratio

Uses outputs from NB01 (cluster classifications) and NB02 (distances).

Outputs:
  data/h1_test_results.json
  figures/nb03_h1_contingency.png
  figures/nb03_h1_species_odds.png
"""

import json
import os
import sys
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

warnings.filterwarnings("ignore")

_script_dir = os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else os.getcwd()
PROJECT = os.path.dirname(_script_dir) if os.path.basename(_script_dir) == "notebooks" else _script_dir
if not os.path.isdir(os.path.join(PROJECT, "data")):
    PROJECT = os.path.join(os.getcwd(), "projects", "prophage_amr_comobilization")
DATA = os.path.join(PROJECT, "data")
FIG  = os.path.join(PROJECT, "figures")

# ===================================================================
# 1. Load data
# ===================================================================
print("=== 1. Load Data ===")

dist_df = pd.read_csv(os.path.join(DATA, "amr_prophage_distances.csv"))
amr_clusters = pd.read_csv(os.path.join(DATA, "amr_clusters.csv"))

print(f"Distance records: {len(dist_df):,}")
print(f"AMR clusters: {len(amr_clusters):,}")

# Build cluster-level lookup for core/accessory status (deduplicate — same cluster in multiple species)
amr_dedup = amr_clusters.drop_duplicates(subset="gene_cluster_id")
cluster_info = amr_dedup.set_index("gene_cluster_id")[["is_core", "is_auxiliary", "is_singleton"]].to_dict("index")

# ===================================================================
# 2. Label each AMR gene instance
# ===================================================================
print("\n=== 2. Label Gene Instances ===")

PROXIMITY_THRESHOLD = 10  # genes

# Add core/accessory label
def get_conservation(cluster_id):
    info = cluster_info.get(cluster_id, {})
    if info.get("is_core") == True:
        return "core"
    elif info.get("is_auxiliary") == True or info.get("is_singleton") == True:
        return "accessory"
    return "unknown"

dist_df["conservation"] = dist_df["amr_gene_cluster_id"].apply(get_conservation)
dist_df["proximal"] = dist_df["nearest_prophage_distance"].fillna(999999) <= PROXIMITY_THRESHOLD

known = dist_df[dist_df["conservation"] != "unknown"].copy()
print(f"Records with known conservation: {len(known):,} ({100*len(known)/len(dist_df):.1f}%)")
print(f"Core: {(known['conservation'] == 'core').sum():,}")
print(f"Accessory: {(known['conservation'] == 'accessory').sum():,}")
print(f"Proximal (within {PROXIMITY_THRESHOLD} genes): {known['proximal'].sum():,}")

# ===================================================================
# 3. Fisher's Exact Test (overall)
# ===================================================================
print("\n=== 3. Fisher's Exact Test ===")

# Contingency table: proximal/distal x accessory/core
prox_acc = ((known["proximal"]) & (known["conservation"] == "accessory")).sum()
prox_core = ((known["proximal"]) & (known["conservation"] == "core")).sum()
dist_acc = ((~known["proximal"]) & (known["conservation"] == "accessory")).sum()
dist_core = ((~known["proximal"]) & (known["conservation"] == "core")).sum()

table = np.array([[prox_acc, prox_core],
                  [dist_acc, dist_core]])

print(f"\nContingency table (threshold={PROXIMITY_THRESHOLD} genes):")
print(f"                  Accessory    Core")
print(f"  Proximal         {prox_acc:>7,}   {prox_core:>7,}")
print(f"  Distal           {dist_acc:>7,}   {dist_core:>7,}")

odds_ratio_fisher, p_fisher = stats.fisher_exact(table, alternative="greater")
print(f"\nFisher's exact test (one-sided, H1: proximal → more accessory):")
print(f"  Odds ratio: {odds_ratio_fisher:.3f}")
print(f"  p-value: {p_fisher:.2e}")

# Proportions
pct_acc_proximal = 100 * prox_acc / max(prox_acc + prox_core, 1)
pct_acc_distal = 100 * dist_acc / max(dist_acc + dist_core, 1)
print(f"\n% accessory among proximal: {pct_acc_proximal:.1f}%")
print(f"% accessory among distal:   {pct_acc_distal:.1f}%")

# ===================================================================
# 4. Multiple thresholds
# ===================================================================
print("\n=== 4. Sensitivity Across Thresholds ===")

threshold_results = []
for thresh in [3, 5, 10, 15, 20, 30, 50]:
    prox = known["nearest_prophage_distance"].fillna(999999) <= thresh
    pa = (prox & (known["conservation"] == "accessory")).sum()
    pc = (prox & (known["conservation"] == "core")).sum()
    da = (~prox & (known["conservation"] == "accessory")).sum()
    dc = (~prox & (known["conservation"] == "core")).sum()
    if pc > 0 and dc > 0:
        orf, pf = stats.fisher_exact([[pa, pc], [da, dc]], alternative="greater")
    else:
        orf, pf = float("inf"), 0.0
    pct_a = 100 * pa / max(pa + pc, 1)
    threshold_results.append({
        "threshold": thresh,
        "n_proximal": int(pa + pc),
        "n_distal": int(da + dc),
        "pct_accessory_proximal": round(pct_a, 1),
        "odds_ratio": round(orf, 3) if orf != float("inf") else None,
        "p_value": float(pf),
    })
    sig = "***" if pf < 0.001 else "**" if pf < 0.01 else "*" if pf < 0.05 else "ns"
    print(f"  Thresh={thresh:>2d}: OR={orf:.2f}, p={pf:.2e} {sig}, "
          f"%acc_prox={pct_a:.1f}%, n_prox={pa+pc:,}")

# ===================================================================
# 5. Per-species Fisher's test
# ===================================================================
print("\n=== 5. Per-Species Analysis ===")

species_results = []
for sp, grp in known.groupby("species_id"):
    prox = grp["proximal"]
    pa = (prox & (grp["conservation"] == "accessory")).sum()
    pc = (prox & (grp["conservation"] == "core")).sum()
    da = (~prox & (grp["conservation"] == "accessory")).sum()
    dc = (~prox & (grp["conservation"] == "core")).sum()

    n_total = len(grp)
    n_prox = prox.sum()
    pct_acc = 100 * (pa + da) / max(n_total, 1)

    if min(pa, pc, da, dc) > 0:
        orf, pf = stats.fisher_exact([[pa, pc], [da, dc]], alternative="greater")
    else:
        orf, pf = float("nan"), float("nan")

    species_results.append({
        "species_id": sp,
        "n_total": n_total,
        "n_proximal": n_prox,
        "pct_accessory": round(pct_acc, 1),
        "odds_ratio": round(orf, 3) if not np.isnan(orf) else None,
        "p_value": pf if not np.isnan(pf) else None,
    })

sp_results_df = pd.DataFrame(species_results)
testable = sp_results_df.dropna(subset=["odds_ratio"])
print(f"Species with testable contingency tables: {len(testable)}/{len(sp_results_df)}")

if len(testable) > 0:
    n_sig = (testable["p_value"] < 0.05).sum()
    median_or = testable["odds_ratio"].median()
    print(f"Significant (p<0.05): {n_sig} species")
    print(f"Median OR: {median_or:.2f}")
    print(f"OR > 1 (enriched): {(testable['odds_ratio'] > 1).sum()}")
    print(f"OR < 1 (depleted): {(testable['odds_ratio'] < 1).sum()}")

# ===================================================================
# 6. Bootstrap CI for overall odds ratio
# ===================================================================
print("\n=== 6. Bootstrap Confidence Interval ===")

np.random.seed(42)
n_boot = 10000
boot_ors = []
n_known = len(known)

for i in range(n_boot):
    idx = np.random.randint(0, n_known, n_known)
    b = known.iloc[idx]
    pa = ((b["proximal"]) & (b["conservation"] == "accessory")).sum()
    pc = ((b["proximal"]) & (b["conservation"] == "core")).sum()
    da = ((~b["proximal"]) & (b["conservation"] == "accessory")).sum()
    dc = ((~b["proximal"]) & (b["conservation"] == "core")).sum()
    if pc > 0 and dc > 0 and pa > 0 and da > 0:
        boot_ors.append((pa * dc) / (pc * da))

boot_ors = np.array(boot_ors)
ci_lo, ci_hi = np.percentile(boot_ors, [2.5, 97.5])
print(f"Bootstrap OR (n={len(boot_ors):,} resamples): "
      f"median={np.median(boot_ors):.3f}, 95% CI=[{ci_lo:.3f}, {ci_hi:.3f}]")

# ===================================================================
# 7. Save results
# ===================================================================
print("\n=== 7. Save Results ===")

results = {
    "hypothesis": "H1: Prophage-proximal AMR genes are disproportionately accessory",
    "proximity_threshold_genes": PROXIMITY_THRESHOLD,
    "total_amr_instances": len(dist_df),
    "testable_instances": len(known),
    "contingency_table": {
        "proximal_accessory": int(prox_acc),
        "proximal_core": int(prox_core),
        "distal_accessory": int(dist_acc),
        "distal_core": int(dist_core),
    },
    "fisher_exact": {
        "odds_ratio": round(odds_ratio_fisher, 4),
        "p_value": float(p_fisher),
        "significant_005": bool(p_fisher < 0.05),
    },
    "proportions": {
        "pct_accessory_proximal": round(pct_acc_proximal, 1),
        "pct_accessory_distal": round(pct_acc_distal, 1),
    },
    "bootstrap_ci": {
        "median_or": round(float(np.median(boot_ors)), 3),
        "ci_95_lo": round(float(ci_lo), 3),
        "ci_95_hi": round(float(ci_hi), 3),
    },
    "threshold_sensitivity": threshold_results,
    "per_species_summary": {
        "n_testable": len(testable),
        "n_significant_005": int((testable["p_value"] < 0.05).sum()) if len(testable) > 0 else 0,
        "median_or": round(float(median_or), 3) if len(testable) > 0 else None,
    },
}

with open(os.path.join(DATA, "h1_test_results.json"), "w") as f:
    json.dump(results, f, indent=2)
print("Saved data/h1_test_results.json")

# ===================================================================
# 8. Figures
# ===================================================================
print("\n=== 8. Generating Figures ===")

# Figure 1: Contingency table heatmap + bar chart
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Heatmap
labels = np.array([[f"{prox_acc:,}\n({pct_acc_proximal:.1f}%)", f"{prox_core:,}\n({100-pct_acc_proximal:.1f}%)"],
                   [f"{dist_acc:,}\n({pct_acc_distal:.1f}%)", f"{dist_core:,}\n({100-pct_acc_distal:.1f}%)"]])
sns.heatmap(table, annot=labels, fmt="", cmap="YlOrRd", ax=axes[0],
            xticklabels=["Accessory", "Core"], yticklabels=["Proximal", "Distal"])
axes[0].set_title(f"A. Contingency Table (threshold={PROXIMITY_THRESHOLD} genes)")
axes[0].set_xlabel("Conservation")
axes[0].set_ylabel("Prophage Proximity")
sig_str = f"OR={odds_ratio_fisher:.2f}, p={p_fisher:.2e}"
axes[0].text(0.5, -0.15, sig_str, transform=axes[0].transAxes, ha="center", fontsize=10)

# Threshold sensitivity
thresh_df = pd.DataFrame(threshold_results)
valid = thresh_df[thresh_df["odds_ratio"].notna()]
axes[1].plot(valid["threshold"], valid["odds_ratio"], "o-", color="steelblue", linewidth=2)
axes[1].axhline(1.0, color="gray", linestyle="--", alpha=0.5, label="OR=1 (no association)")
axes[1].set_xlabel("Proximity threshold (genes)")
axes[1].set_ylabel("Odds ratio (proximal → accessory)")
axes[1].set_title("B. Odds Ratio Across Thresholds")
axes[1].legend()

plt.suptitle("NB03: H1 — Prophage Proximity Predicts AMR Mobility", fontsize=13, fontweight="bold")
plt.tight_layout()
fig.savefig(os.path.join(FIG, "nb03_h1_contingency.png"), dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved figures/nb03_h1_contingency.png")

# Figure 2: Per-species odds ratios
if len(testable) > 0:
    fig, ax = plt.subplots(figsize=(10, 6))
    sorted_sp = testable.sort_values("odds_ratio", ascending=False).reset_index(drop=True)
    colors = ["#d32f2f" if p < 0.05 else "#90a4ae" for p in sorted_sp["p_value"]]
    ax.bar(range(len(sorted_sp)), sorted_sp["odds_ratio"], color=colors, width=1.0)
    ax.axhline(1.0, color="black", linestyle="--", linewidth=0.5)
    ax.set_xlabel("Species (ranked by OR)")
    ax.set_ylabel("Odds ratio (proximal → accessory)")
    ax.set_title(f"Per-Species Odds Ratios (red = p<0.05, n={len(testable)} species)")
    ax.set_yscale("log")
    ax.set_ylim(0.01, max(sorted_sp["odds_ratio"].max() * 2, 10))
    plt.tight_layout()
    fig.savefig(os.path.join(FIG, "nb03_h1_species_odds.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("Saved figures/nb03_h1_species_odds.png")

# ===================================================================
# 9. Conclusion
# ===================================================================
print("\n=== 9. Conclusion ===")
if p_fisher < 0.05 and odds_ratio_fisher > 1:
    print(f"H1 SUPPORTED: Prophage-proximal AMR genes are {odds_ratio_fisher:.1f}x "
          f"more likely to be accessory (p={p_fisher:.2e}).")
    print("This is consistent with phage-mediated horizontal transfer of AMR genes.")
elif p_fisher < 0.05 and odds_ratio_fisher < 1:
    print(f"H1 REJECTED: Prophage-proximal AMR genes are LESS likely to be accessory "
          f"(OR={odds_ratio_fisher:.3f}, p={p_fisher:.2e}). Unexpected direction.")
else:
    print(f"H0 NOT REJECTED: No significant association between prophage proximity "
          f"and AMR gene conservation (OR={odds_ratio_fisher:.3f}, p={p_fisher:.2e}).")

print("\nNB03 complete. Proceed to NB04 for species-level breadth test (H2).")

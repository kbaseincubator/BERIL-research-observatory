"""
NB04: Species-Level AMR Breadth Test (H2)
==========================================
Tests H2: Species with higher prophage marker density carry broader
AMR gene repertoires, suggesting phage-mediated amplification of
resistance diversity.

Approach:
  - Uses NB01 species summary data (no Spark needed)
  - Spearman correlation of prophage density vs AMR breadth
  - Linear regression (scipy) with log-transformed variables
  - Partial correlation controlling for genome count
  - Phylum-stratified analysis

Outputs:
  data/h2_test_results.json
  figures/nb04_h2_breadth_regression.png
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
# 1. Load species-level data
# ===================================================================
print("=== 1. Load Data ===")

species_df = pd.read_csv(os.path.join(DATA, "amr_prophage_species_summary.csv"))
print(f"Total species: {len(species_df):,}")

# Filter to species with both AMR and prophage
both = species_df[
    (species_df["n_amr_clusters"] > 0) &
    (species_df["n_prophage_clusters"] > 0) &
    (species_df["no_genomes"] >= 5)
].copy()
print(f"Species with AMR + prophage + >=5 genomes: {len(both):,}")

# Define metrics
both["prophage_density"] = both["n_prophage_clusters"] / both["no_gene_clusters"]
both["amr_density"] = both["n_amr_clusters"] / both["no_gene_clusters"]
both["amr_breadth"] = both["unique_amr_genes"]
both["log_genomes"] = np.log10(both["no_genomes"])
both["log_prophage_density"] = np.log10(both["prophage_density"].clip(lower=1e-6))
both["log_amr_breadth"] = np.log10(both["amr_breadth"].clip(lower=1))

print(f"\nProphage density: median={both['prophage_density'].median():.4f}, "
      f"range=[{both['prophage_density'].min():.4f}, {both['prophage_density'].max():.4f}]")
print(f"AMR breadth: median={both['amr_breadth'].median():.0f}, "
      f"range=[{both['amr_breadth'].min():.0f}, {both['amr_breadth'].max():.0f}]")

# ===================================================================
# 2. Spearman correlation
# ===================================================================
print("\n=== 2. Spearman Correlation ===")

rho, p_spearman = stats.spearmanr(both["prophage_density"], both["amr_breadth"])
print(f"Prophage density vs AMR breadth: rho={rho:.4f}, p={p_spearman:.2e}")

rho2, p2 = stats.spearmanr(both["prophage_density"], both["n_amr_clusters"])
print(f"Prophage density vs AMR clusters: rho={rho2:.4f}, p={p2:.2e}")

rho3, p3 = stats.spearmanr(both["prophage_per_genome"], both["amr_per_genome"])
print(f"Prophage/genome vs AMR/genome:    rho={rho3:.4f}, p={p3:.2e}")

# ===================================================================
# 3. Linear regression: log(AMR breadth) ~ log(prophage density)
# ===================================================================
print("\n=== 3. Linear Regression (log-log) ===")

slope, intercept, r_value, p_linreg, se = stats.linregress(
    both["log_prophage_density"], both["log_amr_breadth"]
)
r_sq = r_value ** 2
print(f"log(AMR breadth) ~ log(prophage density):")
print(f"  slope={slope:.4f}, intercept={intercept:.4f}")
print(f"  R²={r_sq:.4f}, p={p_linreg:.2e}, SE={se:.4f}")
ci_lo = slope - 1.96 * se
ci_hi = slope + 1.96 * se
print(f"  95% CI for slope: [{ci_lo:.4f}, {ci_hi:.4f}]")

# ===================================================================
# 4. Partial correlation (controlling for genome count)
# ===================================================================
print("\n=== 4. Partial Correlation ===")

# Residualize both variables against log_genomes using scipy linregress
s1, i1, _, _, _ = stats.linregress(both["log_genomes"], both["log_prophage_density"])
resid_prophage = both["log_prophage_density"] - (s1 * both["log_genomes"] + i1)

s2, i2, _, _, _ = stats.linregress(both["log_genomes"], both["log_amr_breadth"])
resid_amr = both["log_amr_breadth"] - (s2 * both["log_genomes"] + i2)

rho_partial, p_partial = stats.spearmanr(resid_prophage, resid_amr)
print(f"Partial Spearman (controlling for log_genomes): rho={rho_partial:.4f}, p={p_partial:.2e}")

# Also do Pearson on residuals
r_partial_pearson, p_partial_pearson = stats.pearsonr(resid_prophage, resid_amr)
print(f"Partial Pearson:  r={r_partial_pearson:.4f}, p={p_partial_pearson:.2e}")

# ===================================================================
# 5. Phylum-stratified analysis
# ===================================================================
print("\n=== 5. Phylum-Stratified Analysis ===")

phylum_results = []
for phylum, grp in both.groupby("phylum"):
    if len(grp) < 10:
        continue
    r, p = stats.spearmanr(grp["prophage_density"], grp["amr_breadth"])
    phylum_results.append({
        "phylum": phylum,
        "n_species": len(grp),
        "rho": round(r, 4),
        "p_value": float(p),
    })

phylum_df = pd.DataFrame(phylum_results).sort_values("n_species", ascending=False)
for _, row in phylum_df.iterrows():
    sig = "***" if row["p_value"] < 0.001 else "**" if row["p_value"] < 0.01 else "*" if row["p_value"] < 0.05 else "ns"
    print(f"  {row['phylum']:35s} n={row['n_species']:>4d}  rho={row['rho']:.3f}  p={row['p_value']:.2e}  {sig}")

# ===================================================================
# 6. Save results
# ===================================================================
print("\n=== 6. Save Results ===")

results = {
    "hypothesis": "H2: Species with more prophage carry broader AMR repertoires",
    "n_species_analyzed": len(both),
    "spearman_prophage_amr_breadth": {
        "rho": round(float(rho), 4),
        "p_value": float(p_spearman),
    },
    "spearman_prophage_amr_clusters": {
        "rho": round(float(rho2), 4),
        "p_value": float(p2),
    },
    "spearman_per_genome": {
        "rho": round(float(rho3), 4),
        "p_value": float(p3),
    },
    "linear_regression_log_log": {
        "slope": round(float(slope), 4),
        "intercept": round(float(intercept), 4),
        "r_squared": round(float(r_sq), 4),
        "p_value": float(p_linreg),
        "slope_se": round(float(se), 4),
        "slope_ci_95": [round(float(ci_lo), 4), round(float(ci_hi), 4)],
    },
    "partial_spearman_ctrl_genomes": {
        "rho": round(float(rho_partial), 4),
        "p_value": float(p_partial),
    },
    "partial_pearson_ctrl_genomes": {
        "r": round(float(r_partial_pearson), 4),
        "p_value": float(p_partial_pearson),
    },
    "phylum_results": phylum_df.to_dict("records"),
}

with open(os.path.join(DATA, "h2_test_results.json"), "w") as f:
    json.dump(results, f, indent=2)
print("Saved data/h2_test_results.json")

# ===================================================================
# 7. Figures
# ===================================================================
print("\n=== 7. Generating Figures ===")

fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# Panel A: Scatter plot — prophage density vs AMR breadth (log-log)
top_3_phyla = both["phylum"].value_counts().head(3).index
colors = {"p__Pseudomonadota": "#1f77b4", "p__Bacillota": "#ff7f0e", "p__Actinomycetota": "#2ca02c"}
for phylum in top_3_phyla:
    mask = both["phylum"] == phylum
    c = colors.get(phylum, "gray")
    label = phylum.replace("p__", "")
    axes[0].scatter(both.loc[mask, "prophage_density"],
                    both.loc[mask, "amr_breadth"],
                    alpha=0.4, s=15, c=c, label=label)
other = ~both["phylum"].isin(top_3_phyla)
axes[0].scatter(both.loc[other, "prophage_density"],
                both.loc[other, "amr_breadth"],
                alpha=0.2, s=10, c="gray", label="Other")
axes[0].set_xscale("log")
axes[0].set_yscale("log")
axes[0].set_xlabel("Prophage density (clusters/total clusters)")
axes[0].set_ylabel("AMR breadth (unique gene names)")
axes[0].set_title(f"A. Prophage Density vs AMR Breadth\n(Spearman rho={rho:.3f}, p={p_spearman:.2e})")
axes[0].legend(fontsize=8, framealpha=0.7)

# Panel B: Per-genome rates
axes[1].scatter(both["prophage_per_genome"], both["amr_per_genome"],
                alpha=0.3, s=10, c="steelblue")
axes[1].set_xlabel("Prophage markers per genome")
axes[1].set_ylabel("AMR clusters per genome")
axes[1].set_title(f"B. Per-Genome Rates\n(Spearman rho={rho3:.3f}, p={p3:.2e})")

# Panel C: Partial residuals
axes[2].scatter(resid_prophage, resid_amr, alpha=0.3, s=10, c="steelblue")
z = np.polyfit(resid_prophage, resid_amr, 1)
x_line = np.linspace(resid_prophage.min(), resid_prophage.max(), 100)
axes[2].plot(x_line, np.polyval(z, x_line), "r--", linewidth=1.5)
axes[2].set_xlabel("Residual log(prophage density)")
axes[2].set_ylabel("Residual log(AMR breadth)")
axes[2].set_title(f"C. Partial Correlation (ctrl genome count)\n"
                  f"(rho={rho_partial:.3f}, p={p_partial:.2e})")

plt.suptitle("NB04: H2 — Prophage Burden vs AMR Repertoire Breadth",
             fontsize=13, fontweight="bold")
plt.tight_layout()
fig.savefig(os.path.join(FIG, "nb04_h2_breadth_regression.png"), dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved figures/nb04_h2_breadth_regression.png")

# ===================================================================
# 8. Conclusion
# ===================================================================
print("\n=== 8. Conclusion ===")

if p_linreg < 0.05 and slope > 0:
    print(f"H2 SUPPORTED: Prophage density is a significant positive predictor "
          f"of AMR breadth (slope={slope:.3f}, p={p_linreg:.2e}, R²={r_sq:.3f}).")
elif p_linreg < 0.05 and slope < 0:
    print(f"H2 REJECTED (opposite direction): Prophage density is a significant "
          f"NEGATIVE predictor of AMR breadth (slope={slope:.3f}, p={p_linreg:.2e}).")
else:
    print(f"H0 NOT REJECTED: No significant relationship between prophage density "
          f"and AMR breadth (slope={slope:.3f}, p={p_linreg:.2e}).")

if p_partial < 0.05 and rho_partial > 0:
    print(f"Partial correlation confirms positive association after controlling "
          f"for genome count (rho={rho_partial:.3f}, p={p_partial:.2e}).")
elif p_partial >= 0.05:
    print(f"Partial correlation not significant after controlling for genome count "
          f"(rho={rho_partial:.3f}, p={p_partial:.2e}).")

print("\nNB04 complete. Proceed to NB05 for synthesis.")

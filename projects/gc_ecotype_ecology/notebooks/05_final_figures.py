# %%
"""
Notebook 05: Final figures and summary tables for REPORT.md.

Produces:
  - figures/05_summary_panel.png   — 4-panel summary figure for the report
  - figures/05_burkholderia_case_study.png  — within-species ecotype example
  - data/05_final_summary_table.csv  — clean table of significant species
"""

# %%
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# %%
PROJECT_DIR = "/home/justaddcoffee/BERIL-research-observatory/projects/gc_ecotype_ecology"
DATA_DIR = os.path.join(PROJECT_DIR, "data")
FIG_DIR = os.path.join(PROJECT_DIR, "figures")

# %%
df = pd.read_parquet(os.path.join(DATA_DIR, "genome_gc_env_categorized.parquet"))
sig = pd.read_csv(os.path.join(DATA_DIR, "03_significant_species.csv"))
res = pd.read_csv(os.path.join(DATA_DIR, "03_within_species_results.csv"))
ae = pd.read_csv(os.path.join(DATA_DIR, "04_alphaearth_results.csv"))
perm = pd.read_csv(os.path.join(DATA_DIR, "04_permutation_results.csv"))

# %%
# -----------------------------------------------------------------------------
# Final summary table
# -----------------------------------------------------------------------------
summary = sig[["species","n_genomes","n_clusters","categories",
               "mean_gc","partial_r2_iso","effect_range_pct",
               "p_iso_given_ani","q_value_bh"]].copy()
# Annotate with permutation result
summary = summary.merge(perm[["species","emp_p_value"]], on="species", how="left")
# Annotate with AE result
summary = summary.merge(
    ae[["species","best_r","best_p","q_value_bh"]].rename(
        columns={"best_r":"ae_best_r","best_p":"ae_best_p","q_value_bh":"ae_q"}
    ),
    on="species", how="left"
)
summary["species_short"] = summary["species"].str.replace("s__","").str.split("--").str[0]
summary = summary.sort_values("partial_r2_iso", ascending=False)
summary.to_csv(os.path.join(DATA_DIR, "05_final_summary_table.csv"), index=False)
print(f"Saved final summary table ({len(summary)} significant species)")

# %%
# -----------------------------------------------------------------------------
# 4-panel summary figure
# -----------------------------------------------------------------------------
fig = plt.figure(figsize=(15, 11))
gs = fig.add_gridspec(2, 2, hspace=0.4, wspace=0.3)

# %%
# Panel A: cross-species GC vs isolation source (sanity check)
ax = fig.add_subplot(gs[0, 0])
qual = df[df["passes_quality"] & df["gc_pct"].notna() & df["iso_category"].notna()]
qual = qual[qual["iso_category"] != "other"]
order = (qual.groupby("iso_category")["gc_pct"].median()
         .sort_values(ascending=False).index.tolist())
data = [qual.loc[qual["iso_category"]==c, "gc_pct"].values for c in order]
bp = ax.boxplot(data, tick_labels=order, showfliers=False, patch_artist=True)
for p in bp["boxes"]:
    p.set(facecolor="#4c72b0", alpha=0.6)
ax.set_ylabel("GC content (%)")
ax.set_title("A. Cross-species: GC tracks environment (literature replication)")
ax.tick_params(axis="x", rotation=35, labelsize=8)

# %%
# Panel B: Volcano for within-species iso effect
ax = fig.add_subplot(gs[0, 1])
res_p = res[res["p_iso_given_ani"].notna()]
x = res_p["partial_r2_iso"] * 100
y = -np.log10(res_p["p_iso_given_ani"].clip(lower=1e-300))
is_sig = res_p["q_value_bh"] < 0.05
ax.scatter(x[~is_sig], y[~is_sig], s=12, color="grey", alpha=0.4, label="not sig.")
ax.scatter(x[is_sig],  y[is_sig],  s=22, color="#c44e52", alpha=0.85, label="FDR<0.05")
ax.set_xlabel("Partial R² of iso_category | ANI cluster (%)")
ax.set_ylabel("-log10(p) iso_category effect")
ax.set_title(f"B. Within-species: {int(is_sig.sum())} of {len(res_p)} species show\nenv signal after ANI control")
top = res_p.nlargest(6, "partial_r2_iso")
for _, row in top.iterrows():
    nm = row["species"].split("--")[0].replace("s__","")
    nm = nm.replace("_", " ")[:22]
    ax.annotate(nm, xy=(row["partial_r2_iso"]*100,
                        -np.log10(max(row["p_iso_given_ani"], 1e-300))),
                fontsize=7, alpha=0.8)
ax.legend()

# %%
# Panel C: Permutation null robustness
ax = fig.add_subplot(gs[1, 0])
ax.hist(-np.log10(perm["emp_p_value"].clip(lower=1e-3)), bins=18,
        color="#55a868", edgecolor="white")
ax.axvline(-np.log10(0.05), color="red", linestyle="--", label="empirical p = 0.05")
ax.set_xlabel("-log10(empirical p, 200 permutations)")
ax.set_ylabel("Number of significant species")
n_robust = int((perm["emp_p_value"] < 0.05).sum())
ax.set_title(f"C. Robustness: {n_robust}/{len(perm)} species survive label-permutation null")
ax.legend()

# %%
# Panel D: AlphaEarth independent line — |r| distribution
ax = fig.add_subplot(gs[1, 1])
ae_sig = ae[ae["q_value_bh"] < 0.05]
ax.scatter(ae["best_r"].abs(), -np.log10(ae["best_p"].clip(lower=1e-300)),
           s=12, color="grey", alpha=0.4, label="not sig.")
ax.scatter(ae_sig["best_r"].abs(),
           -np.log10(ae_sig["best_p"].clip(lower=1e-300)),
           s=22, color="#8172b3", alpha=0.85, label="FDR<0.05")
ax.set_xlabel("|Pearson r|, residual GC vs best AlphaEarth PC")
ax.set_ylabel("-log10(p)")
ax.set_title(f"D. Independent: {len(ae_sig)}/{len(ae)} species show continuous env\nsignal (AlphaEarth embeddings)")
ax.legend()

# %%
fig.suptitle("Within-species GC content tracks environmental niche after phylogenetic control\n(BERDL pangenome, 293K bacterial genomes)", fontsize=13, y=0.995)
plt.savefig(os.path.join(FIG_DIR, "05_summary_panel.png"), dpi=150, bbox_inches="tight")
plt.close()
print("Saved summary panel")

# %%
# -----------------------------------------------------------------------------
# Case study: Burkholderia vietnamiensis (env + AE both significant)
# -----------------------------------------------------------------------------
sp_case = sig[sig["species"].str.contains("Burkholderia_vietnamiensis")]
if len(sp_case):
    sp_id = sp_case["species"].iloc[0]
    sub = df[(df["gtdb_species_clade_id"] == sp_id) & df["iso_category"].notna() & (df["iso_category"] != "other")]
    cats = sub["iso_category"].value_counts()
    cats = cats[cats >= 10]
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    # left: boxplot
    data = [sub.loc[sub["iso_category"]==c, "gc_pct"].values for c in cats.index]
    bp = axes[0].boxplot(data, tick_labels=cats.index, showfliers=True, patch_artist=True)
    for p in bp["boxes"]:
        p.set(facecolor="#4c72b0", alpha=0.7)
    axes[0].set_ylabel("GC content (%)")
    axes[0].set_title("Burkholderia vietnamiensis — GC by isolation source")
    stats = sp_case.iloc[0]
    axes[0].text(0.02, 0.98,
                 f"n={int(stats['n_genomes'])} genomes\nANI clusters={int(stats['n_clusters'])}\npartial R² = {stats['partial_r2_iso']*100:.1f}%\nq = {stats['q_value_bh']:.2e}\nmax-min mean GC = {stats['effect_range_pct']:.2f}%",
                 transform=axes[0].transAxes, va="top", ha="left",
                 fontsize=10, family="monospace",
                 bbox=dict(boxstyle="round", facecolor="white", alpha=0.85))

    # right: strip plot by ANI cluster colored by category
    # Use the dataset to make a within-cluster comparison plot
    # We'll need to recompute cluster membership; quick approach: show GC vs category for each ani_cluster summary
    sp_means = sub.groupby("iso_category")["gc_pct"].mean()
    axes[1].bar(sp_means.index, sp_means.values, color="#55a868", alpha=0.7)
    axes[1].set_ylabel("Mean GC (%)")
    axes[1].set_title("Mean GC by environment category (zoomed)")
    axes[1].set_ylim(sp_means.min() - 0.5, sp_means.max() + 0.5)
    for i, (c, v) in enumerate(sp_means.items()):
        axes[1].text(i, v + 0.05, f"{v:.2f}", ha="center", fontsize=10)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "05_burkholderia_case_study.png"), dpi=150)
    plt.close()
    print("Saved Burkholderia case study figure")

# %%
print("\nNotebook 05 complete.")
print(f"Top species by effect (R²): {summary.head(10)['species_short'].tolist()}")

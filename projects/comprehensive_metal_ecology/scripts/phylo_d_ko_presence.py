"""
Phylogenetic signal in KO presence fractions — intercept-only Pagel's λ.

For each Tier 1+2 KO in nb25, fit the model:
    presence_fraction ~ 1   (intercept only, no predictors)
and optimise λ via ML over the GTDB phylogeny.

λ ≈ 0: gene presence scattered across tree (HGT / horizontal transfer)
λ ≈ 1: gene presence clusters in related lineages (vertical inheritance)

This is the most direct phylogenetic signal test available without gene sequences.
Reference: unconditional λ of niche breadth on the same tree (~0.76–0.84).
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import mannwhitneyu

warnings.filterwarnings("ignore")

sys.path.insert(0, str(Path(__file__).parent))
# Import internals directly — intercept-only model needs _gls_fit / _optimise_lambda
from pgls_utils import load_tree, build_vcv, _gls_fit, _optimise_lambda

DATA  = Path("data")
TREE  = DATA / "gtdb_bac_genus_pruned.tree"

print("Loading data...")
nb25    = pd.read_parquet(DATA / "nb25_ko_presence_matrix.parquet")
nb25["genus_lower"] = nb25["genus_lower"].str.replace("g__", "", regex=False)
spark   = pd.read_csv(DATA / "01_genus_ko_density_spark.csv")
curated = pd.read_csv(DATA / "curated_mrg_ko_ids_v2.csv")
primary = pd.read_csv(DATA / "01_pgls_input_bacteria.csv")

tier12  = curated[curated["evidence_tier"].isin(["Tier 1", "Tier 2"])].copy()
ko_meta = tier12.set_index("KO")[["gene_name", "primary_category"]].to_dict("index")

# Build per-genus, per-KO presence fraction
ko_df = nb25.merge(spark[["genus_lower","n_genomes"]], on="genus_lower", how="inner")
ko_df["presence_frac"] = ko_df["n_genomes_with_ko"] / ko_df["n_genomes"]

# Restrict to genera in primary PGLS set (1,574 genera — tree pruned to them)
primary_genera = set(primary["genus_lower"])
ko_df = ko_df[ko_df["genus_lower"].isin(primary_genera)]
print(f"Genera in primary set: {ko_df['genus_lower'].nunique()}")

# KOs with at least 20 genera present
ko_counts = ko_df[ko_df["presence_frac"] > 0].groupby("ko")["genus_lower"].nunique()
eligible_kos = ko_counts[ko_counts >= 20].index.tolist()
tier12_kos = set(tier12["KO"])
eligible_kos = [k for k in eligible_kos if k in tier12_kos]
print(f"Eligible Tier1+2 KOs (≥20 genera present): {len(eligible_kos)}")

print("Loading tree (shared across all KOs)...")
tree = load_tree(str(TREE))
tree_labels = {
    t.label.replace(" ", "_").lower()
    for t in tree.taxon_namespace
}

def _fit_intercept_lambda(genus_list, y_vals):
    """Optimise Pagel's λ for an intercept-only model on the given taxa."""
    taxa_norm = [g.replace(" ", "_").lower() for g in genus_list]
    in_tree = [t in tree_labels for t in taxa_norm]
    taxa_norm = [t for t, ok in zip(taxa_norm, in_tree) if ok]
    y_vals   = y_vals[[i for i, ok in enumerate(in_tree) if ok]]
    if len(taxa_norm) < 20:
        return None, len(taxa_norm)
    V = build_vcv(tree, taxa_norm)
    n = len(taxa_norm)
    X = np.ones((n, 1))  # intercept only
    lam, _ = _optimise_lambda(y_vals.astype(float), X, V)
    return float(lam), n

results = []
for ko_id in sorted(eligible_kos):
    sub = ko_df[ko_df["ko"] == ko_id].dropna(subset=["presence_frac"])
    genus_list = sub["genus_lower"].tolist()
    y_vals = sub["presence_frac"].values
    try:
        lam, n = _fit_intercept_lambda(genus_list, y_vals)
        if lam is None:
            print(f"  SKIP {ko_id}: insufficient tree coverage (n={n})")
            continue
        meta = ko_meta.get(ko_id, {})
        results.append({
            "ko_id":       ko_id,
            "gene_name":   meta.get("gene_name", ""),
            "subcategory": meta.get("primary_category", "Unknown"),
            "lambda":      lam,
            "n_genera":    n,
        })
        print(f"  {ko_id} ({meta.get('gene_name',''):<12} "
              f"[{meta.get('primary_category',''):<25}]): λ = {lam:.3f}  n={n}")
    except Exception as e:
        print(f"  ERROR {ko_id}: {e}")

df = pd.DataFrame(results)
df.to_csv(DATA / "phylo_d_ko_presence.csv", index=False)
print(f"\nSaved {len(df)} rows.")

# Reference: unconditional λ of niche breadth (intercept-only)
sub_nb = primary[["genus_lower","mean_levins_B_std"]].dropna().copy()
genus_nb = sub_nb["genus_lower"].tolist()
y_nb = sub_nb["mean_levins_B_std"].values
try:
    lam_nb, n_nb = _fit_intercept_lambda(genus_nb, y_nb)
    print(f"\nUnconditional λ (niche breadth, n={n_nb}): {lam_nb:.3f}  [reference for comparison]")
except Exception as e:
    lam_nb = None
    print(f"\nNiche breadth null λ error: {e}")

# ── Summary ────────────────────────────────────────────────────────────────────
print("\n\n=== PER-SUBCATEGORY SUMMARY ===")
CAT_ORDER = ["Resistance/Detoxification","Cofactor Biosynthesis",
             "Sensing/Regulation","Transport/Homeostasis","Unknown"]

for cat in CAT_ORDER:
    sub = df[df["subcategory"] == cat]
    if len(sub) == 0:
        continue
    lams = sub["lambda"].values
    print(f"  {cat:<30} n={len(lams):2d}  "
          f"median λ={np.median(lams):.3f}  "
          f"IQR={np.percentile(lams,25):.3f}–{np.percentile(lams,75):.3f}  "
          f"mean={np.mean(lams):.3f}")

res_lams   = df[df["subcategory"]=="Resistance/Detoxification"]["lambda"].values
cof_lams   = df[df["subcategory"]=="Cofactor Biosynthesis"]["lambda"].values
other_lams = df[df["subcategory"]!="Resistance/Detoxification"]["lambda"].values

print()
if len(res_lams) >= 2 and len(cof_lams) >= 2:
    stat, p = mannwhitneyu(res_lams, cof_lams, alternative="less")
    print(f"Mann-Whitney U (resistance λ < cofactor): W={stat:.1f}, p={p:.4e}")
if len(res_lams) >= 2 and len(other_lams) >= 2:
    stat, p = mannwhitneyu(res_lams, other_lams, alternative="less")
    print(f"Mann-Whitney U (resistance λ < all others): W={stat:.1f}, p={p:.4e}")

pct_low_res = (res_lams < 0.2).mean()*100 if len(res_lams) > 0 else 0
pct_low_cof = (cof_lams < 0.2).mean()*100 if len(cof_lams) > 0 else 0
print(f"\nResistance KOs with λ < 0.2: {pct_low_res:.0f}%")
print(f"Cofactor   KOs with λ < 0.2: {pct_low_cof:.0f}%")

# ── Violin / jitter plot ───────────────────────────────────────────────────────
CAT_COLORS = {
    "Resistance/Detoxification": "#d62728",
    "Cofactor Biosynthesis":     "#2ca02c",
    "Sensing/Regulation":        "#ff7f0e",
    "Transport/Homeostasis":     "#1f77b4",
    "Unknown":                   "#9467bd",
}
fig, ax = plt.subplots(figsize=(9, 5))
if lam_nb:
    ax.axhline(lam_nb, color="black", lw=1.2, ls="--", alpha=0.8,
               label=f"Unconditional λ (niche breadth) = {lam_nb:.3f}")
ax.axhline(0, color="grey", lw=0.7, ls=":", alpha=0.5)
ax.axhline(1, color="grey", lw=0.7, ls=":", alpha=0.5)
ax.legend(fontsize=9)

positions, labels = [], []
rng = np.random.default_rng(42)
for cat in CAT_ORDER:
    sub = df[df["subcategory"] == cat]
    if len(sub) == 0:
        continue
    lams = sub["lambda"].values
    pos  = len(positions) + 1
    positions.append(pos)
    labels.append(f"{cat}\n(n={len(lams)})")
    color = CAT_COLORS.get(cat, "#7f7f7f")
    if len(lams) >= 3:
        parts = ax.violinplot(lams, positions=[pos], widths=0.6,
                              showmedians=True, showextrema=True)
        for pc in parts["bodies"]:
            pc.set_facecolor(color); pc.set_alpha(0.7)
        for k in ("cmedians","cbars","cmaxes","cmins"):
            parts[k].set_color("black")
    ax.scatter(pos + rng.uniform(-0.12, 0.12, size=len(lams)),
               lams, color=color, s=50, zorder=5, alpha=0.85)

ax.set_xticks(positions)
ax.set_xticklabels(labels, fontsize=9)
ax.set_ylabel("Pagel's λ  (intercept-only null model on gene presence fraction)", fontsize=9)
ax.set_title("Phylogenetic signal of KO presence across genera — direct λ estimate", fontsize=10)
ax.set_ylim(-0.05, 1.15)
plt.tight_layout()
fig.savefig(DATA.parent / "phylo_d_ko_presence.pdf", dpi=150)
plt.close()
print("\nSaved phylo_d_ko_presence.pdf")

# ── Full sorted table ──────────────────────────────────────────────────────────
print("\n=== ALL KOs SORTED BY λ (ascending = most HGT-like first) ===")
for _, row in df.sort_values("lambda").iterrows():
    marker = " ← HGT candidate" if row["lambda"] < 0.2 else (
             " ← vertical"      if row["lambda"] > 0.7 else "")
    print(f"  {row['ko_id']} ({row['gene_name']:<12}) [{row['subcategory']:<30}]: "
          f"λ={row['lambda']:.3f}  n={row['n_genera']}{marker}")

print("\nDone.")

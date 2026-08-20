"""
Phylogenetic signal (intercept-only Pagel's λ) for ALL curated metal-related
KOs in the nb25 presence matrix (Tier 1–3-BacMet, ≥20 genera present).

Extends phylo_d_ko_presence.py (Tier 1+2 only, n=35) to all 301 eligible KOs.
Outputs:
  data/phylo_d_all_ko.csv          — per-KO λ, evidence tier, subcategory
  phylo_d_all_ko_by_tier.pdf       — violin by evidence tier
  phylo_d_all_ko_by_category.pdf   — violin by primary category
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import mannwhitneyu, kruskal

warnings.filterwarnings("ignore")

sys.path.insert(0, str(Path(__file__).parent))
from pgls_utils import load_tree, build_vcv, _optimise_lambda

DATA = Path("data")
TREE = DATA / "gtdb_bac_genus_pruned.tree"

print("Loading data...")
nb25    = pd.read_parquet(DATA / "nb25_ko_presence_matrix.parquet")
nb25["genus_lower"] = nb25["genus_lower"].str.replace("g__", "", regex=False)
spark   = pd.read_csv(DATA / "01_genus_ko_density_spark.csv")
curated = pd.read_csv(DATA / "curated_mrg_ko_ids_v2.csv")
primary = pd.read_csv(DATA / "01_pgls_input_bacteria.csv")

# All tiers
ko_meta = curated.set_index("KO")[
    ["gene_name", "primary_category", "evidence_tier"]
].to_dict("index")

# Per-genus presence fraction
ko_df = nb25.merge(spark[["genus_lower", "n_genomes"]], on="genus_lower", how="inner")
ko_df["presence_frac"] = ko_df["n_genomes_with_ko"] / ko_df["n_genomes"]

# Restrict to primary PGLS genera
primary_genera = set(primary["genus_lower"])
ko_df = ko_df[ko_df["genus_lower"].isin(primary_genera)]

# KOs with ≥20 genera present
ko_counts = (ko_df[ko_df["presence_frac"] > 0]
             .groupby("ko")["genus_lower"].nunique())
eligible_kos = sorted(ko_counts[ko_counts >= 20].index.tolist())
print(f"Eligible KOs (≥20 genera present in primary set): {len(eligible_kos)}")

print("Loading tree...")
tree = load_tree(str(TREE))
tree_labels = {
    t.label.replace(" ", "_").lower()
    for t in tree.taxon_namespace
}

def fit_intercept_lambda(genus_list, y_vals):
    taxa = [g.replace(" ", "_").lower() for g in genus_list]
    mask = [t in tree_labels for t in taxa]
    taxa  = [t for t, ok in zip(taxa, mask) if ok]
    y_arr = y_vals[[i for i, ok in enumerate(mask) if ok]].astype(float)
    if len(taxa) < 20:
        return None, len(taxa)
    V = build_vcv(tree, taxa)
    X = np.ones((len(taxa), 1))
    lam, _ = _optimise_lambda(y_arr, X, V)
    return float(lam), len(taxa)

results = []
n_total = len(eligible_kos)
for i, ko_id in enumerate(eligible_kos, 1):
    sub = ko_df[ko_df["ko"] == ko_id].dropna(subset=["presence_frac"])
    try:
        lam, n = fit_intercept_lambda(
            sub["genus_lower"].tolist(), sub["presence_frac"].values
        )
        if lam is None:
            print(f"  [{i:3d}/{n_total}] SKIP {ko_id}: n_tree={n} < 20")
            continue
        meta = ko_meta.get(ko_id, {})
        results.append({
            "ko_id":          ko_id,
            "gene_name":      meta.get("gene_name", ""),
            "subcategory":    meta.get("primary_category", "Unknown"),
            "evidence_tier":  meta.get("evidence_tier", "Unknown"),
            "lambda":         lam,
            "n_genera":       n,
        })
        print(f"  [{i:3d}/{n_total}] {ko_id} ({meta.get('gene_name',''):<12} "
              f"[{meta.get('primary_category',''):<30} | "
              f"{meta.get('evidence_tier',''):<15}]): λ={lam:.3f}  n={n}")
    except Exception as e:
        print(f"  [{i:3d}/{n_total}] ERROR {ko_id}: {e}")

df = pd.DataFrame(results)
df.to_csv(DATA / "phylo_d_all_ko.csv", index=False)
print(f"\nSaved {len(df)} rows to data/phylo_d_all_ko.csv")

# Reference niche breadth λ (from Tier 1+2 run: 0.766)
LAM_NB = 0.766

# ── Summary by evidence tier ───────────────────────────────────────────────────
print("\n\n=== BY EVIDENCE TIER ===")
TIER_ORDER = ["Tier 1", "Tier 2", "Tier 2-Fitness", "Tier 3", "Tier 3-BacMet"]
tier_lams = {}
for tier in TIER_ORDER:
    sub = df[df["evidence_tier"] == tier]
    if len(sub) == 0:
        continue
    lams = sub["lambda"].values
    tier_lams[tier] = lams
    print(f"  {tier:<18} n={len(lams):3d}  "
          f"median λ={np.median(lams):.3f}  "
          f"IQR={np.percentile(lams,25):.3f}–{np.percentile(lams,75):.3f}  "
          f"mean={np.mean(lams):.3f}  "
          f"λ<0.2: {(lams<0.2).mean()*100:.0f}%")

if len(tier_lams) >= 3:
    stat, p = kruskal(*[v for v in tier_lams.values()])
    print(f"\nKruskal-Wallis across tiers: H={stat:.2f}, p={p:.4e}")

# ── Summary by subcategory ─────────────────────────────────────────────────────
print("\n=== BY SUBCATEGORY ===")
CAT_ORDER = [
    "Resistance/Detoxification", "Cofactor Biosynthesis",
    "Sensing/Regulation", "Transport/Homeostasis",
    "Metal-dependent Metabolism", "Unknown",
]
cat_lams = {}
for cat in CAT_ORDER:
    sub = df[df["subcategory"] == cat]
    if len(sub) == 0:
        continue
    lams = sub["lambda"].values
    cat_lams[cat] = lams
    print(f"  {cat:<30} n={len(lams):3d}  "
          f"median λ={np.median(lams):.3f}  "
          f"IQR={np.percentile(lams,25):.3f}–{np.percentile(lams,75):.3f}  "
          f"mean={np.mean(lams):.3f}  "
          f"λ<0.2: {(lams<0.2).mean()*100:.0f}%")

if len(cat_lams) >= 3:
    stat, p = kruskal(*[v for v in cat_lams.values()])
    print(f"\nKruskal-Wallis across subcategories: H={stat:.2f}, p={p:.4e}")

res_lams   = cat_lams.get("Resistance/Detoxification", np.array([]))
cof_lams   = cat_lams.get("Cofactor Biosynthesis",     np.array([]))
other_lams = df[df["subcategory"] != "Resistance/Detoxification"]["lambda"].values
if len(res_lams) >= 3 and len(cof_lams) >= 3:
    stat, p = mannwhitneyu(res_lams, cof_lams, alternative="less")
    print(f"\nMann-Whitney U (resistance λ < cofactor): W={stat:.1f}, p={p:.4e}")
if len(res_lams) >= 3 and len(other_lams) >= 3:
    stat, p = mannwhitneyu(res_lams, other_lams, alternative="less")
    print(f"Mann-Whitney U (resistance λ < all others): W={stat:.1f}, p={p:.4e}")

# ── HGT candidates (λ < 0.2) ──────────────────────────────────────────────────
print(f"\n=== HGT CANDIDATES (λ < 0.20) — n={( df['lambda'] < 0.20).sum()} ===")
for _, row in df[df["lambda"] < 0.20].sort_values("lambda").iterrows():
    print(f"  {row['ko_id']} ({row['gene_name']:<12}) "
          f"[{row['subcategory']:<30} | {row['evidence_tier']:<15}]: "
          f"λ={row['lambda']:.3f}  n={row['n_genera']}")

# ── Vertically inherited (λ > 0.75) ───────────────────────────────────────────
print(f"\n=== VERTICALLY INHERITED (λ > 0.75) — n={(df['lambda'] > 0.75).sum()} ===")
for _, row in df[df["lambda"] > 0.75].sort_values("lambda", ascending=False).iterrows():
    print(f"  {row['ko_id']} ({row['gene_name']:<12}) "
          f"[{row['subcategory']:<30} | {row['evidence_tier']:<15}]: "
          f"λ={row['lambda']:.3f}  n={row['n_genera']}")

# ── Plots ──────────────────────────────────────────────────────────────────────
CAT_COLORS = {
    "Resistance/Detoxification":  "#d62728",
    "Cofactor Biosynthesis":      "#2ca02c",
    "Sensing/Regulation":         "#ff7f0e",
    "Transport/Homeostasis":      "#1f77b4",
    "Metal-dependent Metabolism": "#8c564b",
    "Unknown":                    "#7f7f7f",
}
TIER_COLORS = {
    "Tier 1":        "#1f77b4",
    "Tier 2":        "#2ca02c",
    "Tier 2-Fitness":"#98df8a",
    "Tier 3":        "#ff7f0e",
    "Tier 3-BacMet": "#ffbb78",
}

def violin_jitter(ax, groups, order, colors, ref_lam=None):
    rng = np.random.default_rng(42)
    positions, labels = [], []
    for grp in order:
        lams = groups.get(grp)
        if lams is None or len(lams) == 0:
            continue
        pos = len(positions) + 1
        positions.append(pos)
        labels.append(f"{grp}\n(n={len(lams)})")
        color = colors.get(grp, "#7f7f7f")
        if len(lams) >= 3:
            parts = ax.violinplot(lams, positions=[pos], widths=0.65,
                                  showmedians=True, showextrema=True)
            for pc in parts["bodies"]:
                pc.set_facecolor(color); pc.set_alpha(0.65)
            for k in ("cmedians","cbars","cmaxes","cmins"):
                parts[k].set_color("black")
        ax.scatter(pos + rng.uniform(-0.15, 0.15, size=len(lams)),
                   lams, color=color, s=20, zorder=5, alpha=0.7)
    ax.set_xticks(positions)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylim(-0.05, 1.15)
    ax.axhline(0, color="grey", lw=0.7, ls=":", alpha=0.5)
    ax.axhline(1, color="grey", lw=0.7, ls=":", alpha=0.5)
    if ref_lam:
        ax.axhline(ref_lam, color="black", lw=1.2, ls="--", alpha=0.8,
                   label=f"Niche breadth λ = {ref_lam:.3f}")
        ax.legend(fontsize=8)

# Plot 1: by subcategory
fig, ax = plt.subplots(figsize=(11, 5))
violin_jitter(ax, cat_lams, CAT_ORDER, CAT_COLORS, ref_lam=LAM_NB)
ax.set_ylabel("Pagel's λ (gene presence fraction, intercept-only)", fontsize=9)
ax.set_title(f"Phylogenetic signal of KO presence — all curated metal KOs (n={len(df)})", fontsize=10)
plt.tight_layout()
fig.savefig(DATA.parent / "phylo_d_all_ko_by_category.pdf", dpi=150)
plt.close()
print("\nSaved phylo_d_all_ko_by_category.pdf")

# Plot 2: by evidence tier
fig, ax = plt.subplots(figsize=(9, 5))
violin_jitter(ax, tier_lams, TIER_ORDER, TIER_COLORS, ref_lam=LAM_NB)
ax.set_ylabel("Pagel's λ (gene presence fraction, intercept-only)", fontsize=9)
ax.set_title(f"Phylogenetic signal by evidence tier — all curated metal KOs (n={len(df)})", fontsize=10)
plt.tight_layout()
fig.savefig(DATA.parent / "phylo_d_all_ko_by_tier.pdf", dpi=150)
plt.close()
print("Saved phylo_d_all_ko_by_tier.pdf")

print("\nDone.")

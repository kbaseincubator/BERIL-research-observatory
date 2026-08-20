"""
Fritz & Purvis D — genus-level binary phylogenetic signal test.

Adam Arkin (2026-08-06) flagged that the existing D analysis uses an 18,961-genome
tree while the primary PGLS uses a 2,283-tip genus tree. This script computes D
at the same genus level and with the same 1,574 PGLS genera used in the primary
analysis, making D directly comparable to the per-KO Pagel's λ.

Data:
  Tree:   data/gtdb_bac_genus_pruned.tree   (2,283 GTDB r214 genera)
  Trait:  data/nb25_ko_presence_matrix.parquet  (genus × KO n_genomes_with_ko)
  Meta:   data/curated_mrg_ko_ids_v2.csv        (KO subcategory / tier)
  PGLS:   data/01_pgls_input_bacteria.csv       (1,574 PGLS genera)

Outputs:
  data/fritz_purvis_D_genus.csv        — per-KO genus-level D
  data/fritz_purvis_D_genus_summary.csv — subcategory means (for REPORT)
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
from pgls_utils import load_tree

sys.path.insert(0, '/home/hmacgregor/BERIL-research-observatory/tools')
from figure_style import apply_style, save, PALETTE, FIGW, ROW_H
apply_style()

DATA = Path("data")
FIGS = Path("figures")
TREE_PATH = DATA / "gtdb_bac_genus_pruned.tree"

N_PERM = 1000
N_BM   = 1000
MIN_N  = 10   # genus-level: lower threshold than genome-level since n_genera << n_genomes

# ── Load PGLS genera (restrict to the 1,574 used in primary PGLS) ────────────
print("Loading PGLS genera...")
primary = pd.read_csv(DATA / "01_pgls_input_bacteria.csv")
pgls_genera = set(primary["genus_lower"])
print(f"PGLS genera: {len(pgls_genera)}")

# ── Load KO metadata ──────────────────────────────────────────────────────────
print("Loading KO metadata...")
curated = pd.read_csv(DATA / "curated_mrg_ko_ids_v2.csv")
ko_meta = curated.drop_duplicates("KO").set_index("KO")[
    ["gene_name", "primary_category", "evidence_tier"]
].to_dict("index")
CURATED_KOS = set(curated["KO"])

# ── Load genus-level presence data ────────────────────────────────────────────
print("Loading genus-level KO presence matrix...")
nb25 = pd.read_parquet(DATA / "nb25_ko_presence_matrix.parquet")
nb25["genus_lower"] = nb25["genus_lower"].str.replace("g__", "", regex=False)

# Restrict to PGLS genera and curated KOs
nb25 = nb25[nb25["genus_lower"].isin(pgls_genera) & nb25["ko"].isin(CURATED_KOS)]
nb25["present"] = (nb25["n_genomes_with_ko"] > 0).astype(int)
print(f"After filtering: {len(nb25):,} rows, {nb25['genus_lower'].nunique()} genera, "
      f"{nb25['ko'].nunique()} KOs")

# Binary presence set per KO
ko_present_sets = (
    nb25[nb25["present"] == 1]
    .groupby("ko")["genus_lower"]
    .apply(set)
    .to_dict()
)

# ── Load genus tree (DendroPy) ────────────────────────────────────────────────
print("Loading genus tree...")
tree = load_tree(str(TREE_PATH))

taxa_list = []
for tx in tree.taxon_namespace:
    lbl = tx.label.replace(" ", "_")
    tx.label = lbl
    taxa_list.append(lbl)

# Restrict taxa to PGLS genera
taxa_list = [g for g in taxa_list if g in pgls_genera]
taxa_set  = set(taxa_list)
n_tips    = len(taxa_list)
taxa_pos  = {lbl: i for i, lbl in enumerate(taxa_list)}
print(f"Tree tips in PGLS genera: {n_tips}")

# ── Pre-compute tree topology ─────────────────────────────────────────────────
print("Pre-computing tree topology...")
postorder_nodes = list(tree.postorder_node_iter())
preorder_nodes  = list(tree.preorder_node_iter())
n_nodes         = len(postorder_nodes)
node_idx        = {nd: i for i, nd in enumerate(postorder_nodes)}

parent_arr  = np.full(n_nodes, -1, dtype=np.int32)
children_of = []
for i, nd in enumerate(postorder_nodes):
    chs = nd.child_nodes()
    children_of.append(
        np.array([node_idx[c] for c in chs], dtype=np.int32) if chs
        else np.array([], dtype=np.int32)
    )
    if nd.parent_node is not None:
        parent_arr[i] = node_idx[nd.parent_node]

# Leaf arrays — only for PGLS genera
is_leaf         = np.array([nd.is_leaf() for nd in postorder_nodes], dtype=bool)
leaf_node_idxs  = np.where(is_leaf)[0]
leaf_labels     = [postorder_nodes[i].taxon.label
                   if postorder_nodes[i].taxon else "" for i in leaf_node_idxs]
# Keep only PGLS-genus leaves
leaf_taxon_pos  = np.array([taxa_pos.get(lbl, -1) for lbl in leaf_labels], dtype=np.int32)
valid_mask      = leaf_taxon_pos >= 0
valid_leaf_nodes  = leaf_node_idxs[valid_mask]
valid_leaf_taxpos = leaf_taxon_pos[valid_mask]

print(f"Valid PGLS leaves in tree: {valid_mask.sum()} / {len(leaf_labels)} tree leaves")

internal_postorder_idx = np.where(~is_leaf)[0]
child_has_parent = np.array([i for i in range(n_nodes) if parent_arr[i] >= 0], dtype=np.int32)
parent_of_each   = parent_arr[child_has_parent]

preorder_idxs = np.array([node_idx[nd] for nd in preorder_nodes], dtype=np.int32)
edge_lengths  = np.zeros(n_nodes, dtype=np.float32)
for nd in preorder_nodes:
    i  = node_idx[nd]
    bl = nd.edge_length if nd.edge_length is not None else 1e-6
    edge_lengths[i] = max(float(bl), 1e-9)
sqrt_el = np.sqrt(edge_lengths)

print(f"Topology: {n_nodes} nodes, {valid_mask.sum()} PGLS leaves, {len(child_has_parent)} edges")


# ── Core D computation (identical to genome-level version) ───────────────────

def _propagate_and_sum(tip_leaf_batch):
    n_batch = tip_leaf_batch.shape[0]
    states  = np.zeros((n_batch, n_nodes), dtype=np.float32)
    states[:, valid_leaf_nodes] = tip_leaf_batch
    for i in internal_postorder_idx:
        chs = children_of[i]
        if len(chs) > 0:
            states[:, i] = states[:, chs].mean(axis=1)
    return np.abs(states[:, child_has_parent] - states[:, parent_of_each]).sum(axis=1)


def _taxa_to_leaf_order(taxa_batch):
    return taxa_batch[:, valid_leaf_taxpos]


def edge_sum_taxa_order(taxa_batch):
    return _propagate_and_sum(_taxa_to_leaf_order(taxa_batch))


def bm_edge_sum_batch(prevalence, n_batch, rng):
    normals = (rng.standard_normal((n_batch, n_nodes)) * sqrt_el[None, :]).astype(np.float32)
    bm      = np.zeros((n_batch, n_nodes), dtype=np.float32)
    for i in preorder_idxs:
        p = parent_arr[i]
        if p >= 0:
            bm[:, i] = bm[:, p] + normals[:, i]
    tip_bm    = bm[:, valid_leaf_nodes]
    threshold = np.quantile(tip_bm, 1.0 - prevalence, axis=1)
    binary    = (tip_bm >= threshold[:, None]).astype(np.float32)
    return _propagate_and_sum(binary)


def compute_D(trait_taxa, rng):
    n_present  = int(trait_taxa.sum())
    prevalence = n_present / n_tips
    trait_leaf = trait_taxa[valid_leaf_taxpos]
    obs_stat   = float(_propagate_and_sum(trait_leaf[None, :])[0])

    perm_matrix = np.array(
        [rng.permutation(trait_leaf) for _ in range(N_PERM)], dtype=np.float32
    )
    perm_stats = _propagate_and_sum(perm_matrix)
    bm_stats   = bm_edge_sum_batch(prevalence, N_BM, rng)

    mean_perm = float(perm_stats.mean())
    mean_bm   = float(bm_stats.mean())
    denom     = mean_perm - mean_bm
    D         = float((obs_stat - mean_bm) / denom) if abs(denom) > 1e-10 else float("nan")
    p_random    = float((perm_stats <= obs_stat).mean())
    p_conserved = float((bm_stats   >= obs_stat).mean())

    return {
        "D": D, "obs_stat": obs_stat, "mean_perm": mean_perm, "mean_bm": mean_bm,
        "p_random": p_random, "p_conserved": p_conserved,
        "n_present": n_present, "prevalence": prevalence,
    }


# ── Eligible KOs ──────────────────────────────────────────────────────────────
eligible = {ko: gs for ko, gs in ko_present_sets.items()
            if len(gs) >= MIN_N and ko in ko_meta}
print(f"\nEligible KOs (n_present ≥ {MIN_N} PGLS genera): {len(eligible)}")

# ── Run D for each eligible KO ────────────────────────────────────────────────
rng     = np.random.default_rng(42)
results = []
n_total = len(eligible)

for i, (ko_id, present_set) in enumerate(sorted(eligible.items()), 1):
    meta = ko_meta.get(ko_id, {})
    # Map present_set to PGLS taxa only (already filtered, but double-check)
    present_pgls = present_set & taxa_set
    trait_taxa = np.array([1.0 if g in present_pgls else 0.0 for g in taxa_list],
                          dtype=np.float32)
    res = compute_D(trait_taxa, rng)
    row = {
        "ko_id":         ko_id,
        "gene_name":     meta.get("gene_name", ""),
        "subcategory":   meta.get("primary_category", "Unknown"),
        "evidence_tier": meta.get("evidence_tier", ""),
        **res,
    }
    results.append(row)
    if i % 25 == 0 or i == n_total:
        print(f"  [{i}/{n_total}] {ko_id} D={res['D']:.3f} p_rand={res['p_random']:.3f}")

results_df = pd.DataFrame(results)
results_df.to_csv(DATA / "fritz_purvis_D_genus.csv", index=False)
print(f"\nSaved {len(results_df)} rows → data/fritz_purvis_D_genus.csv")


# ── Subcategory summary ───────────────────────────────────────────────────────
CAT_ORDER = [
    "Cofactor Biosynthesis", "Metal-dependent Metabolism",
    "Transport/Homeostasis", "Sensing/Regulation",
    "Resistance/Detoxification", "Unknown",
]

# Also load the genus-level lambda for the same KOs
lam = pd.read_csv(DATA / "phylo_d_all_ko.csv")
merged = results_df.merge(lam[["ko_id", "lambda", "n_genera"]], on="ko_id", how="left")

summary = (
    merged.groupby("subcategory")
    .agg(
        n_kos=("ko_id", "nunique"),
        mean_D=("D", "mean"),
        sd_D=("D", "std"),
        mean_lambda=("lambda", "mean"),
        sd_lambda=("lambda", "std"),
    )
    .round(3)
    .reset_index()
)
summary.to_csv(DATA / "fritz_purvis_D_genus_summary.csv", index=False)
print("\nSubcategory summary:")
print(summary.to_string(index=False))


# ── Companion figure (D vs lambda scatter per KO) ─────────────────────────────
cat_colors = {cat: PALETTE[i % len(PALETTE)] for i, cat in enumerate(CAT_ORDER)}

fig, axs = plt.subplots(1, 2, figsize=(FIGW["2col"], ROW_H))

# Left: D by subcategory violin
cats_present = [c for c in CAT_ORDER if c in merged["subcategory"].values]
plot_data = [merged.loc[merged["subcategory"] == c, "D"].dropna().values
             for c in cats_present]
parts = axs[0].violinplot(plot_data, positions=range(len(cats_present)),
                          widths=0.6, showmedians=True)
for i, (pc, cat) in enumerate(zip(parts["bodies"], cats_present)):
    pc.set_facecolor(cat_colors.get(cat, PALETTE[0]))
    pc.set_edgecolor("k")
    pc.set_linewidth(0.5)
    pc.set_alpha(0.75)
axs[0].axhline(0, color="gray", lw=0.8, ls="--")
axs[0].axhline(1, color="gray", lw=0.8, ls=":")
axs[0].set_xticks(range(len(cats_present)))
axs[0].set_xticklabels([c.replace("/", "/\n") for c in cats_present], fontsize=7)
axs[0].set_xlabel("Functional subcategory")
axs[0].set_ylabel("Fritz–Purvis D (genus level)")
axs[0].set_title("D by subcategory (D≈0: conserved; D≈1: random; D>1: overdispersed)")

# Right: D vs lambda scatter
valid = merged.dropna(subset=["D", "lambda"])
for cat in cats_present:
    sub = valid[valid["subcategory"] == cat]
    axs[1].scatter(sub["lambda"], sub["D"], label=cat,
                   color=cat_colors.get(cat, PALETTE[0]),
                   s=20, edgecolor="k", linewidth=0.4, alpha=0.8)
axs[1].axhline(0, color="gray", lw=0.8, ls="--")
axs[1].axhline(1, color="gray", lw=0.8, ls=":")
axs[1].axvline(0.5, color="gray", lw=0.8, ls=":")
axs[1].set_xlabel("Pagel's λ (genus-level density)")
axs[1].set_ylabel("Fritz–Purvis D (genus-level binary presence)")
axs[1].set_title("D vs λ: independent phylogenetic signal metrics")
axs[1].legend(fontsize=6, loc="upper right", framealpha=0.7)

# Annotate Spearman correlation
from scipy.stats import spearmanr
rho, pval = spearmanr(valid["lambda"], valid["D"])
axs[1].annotate(f"Spearman ρ = {rho:.3f}\np = {pval:.3f}",
                xy=(0.05, 0.95), xycoords="axes fraction",
                ha="left", va="top", fontsize=8, color="#808080")

fig.suptitle("Genus-level Fritz–Purvis D vs Pagel's λ for metal-gene KOs (2026-08-06)",
             y=1.02)
plt.tight_layout()
save(fig, FIGS / "fig_nb40_fritz_purvis_D_genus")
print(f"\nFigure saved → {FIGS}/fig_nb40_fritz_purvis_D_genus.pdf")

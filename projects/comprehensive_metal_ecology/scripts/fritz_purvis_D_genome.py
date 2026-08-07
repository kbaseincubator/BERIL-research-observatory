"""
Fritz & Purvis D — genome-level binary phylogenetic signal test.

Data:
  Tree:  ../final_draft/data/pruned_tree_accessions.nwk  (18,961 GTDB genomes)
  Trait: ../final_draft/data/ko_presence_long.tsv         (sparse: only presence=1 stored)
         Columns: genome_id, ko, presence

For each curated metal KO with ≥20 tree genomes having the KO:
  D ≈ 0 → conserved (BM-like phylogenetic clustering)
  D ≈ 1 → random (no phylogenetic signal; HGT-compatible)
  D > 1 → overdispersed

Implementation: batch numpy — propagates N_PERM/N_BM simulations simultaneously
through the tree, one post-order pass per KO rather than N_PERM passes.

Index convention throughout:
  taxa_list   — indexed 0..n_tips-1, taxa_list[k] = genome label
  leaf_nodes  — subset of post-order node indices that are leaves
  valid_leaf_taxpos[j] = index into taxa_list for the j-th valid leaf node
  → always reorder taxa_list-indexed input to leaf-node-order before
    assigning to the state matrix
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

DATA      = Path("data")
FD_DATA   = Path("../final_draft/data")
TREE_PATH = FD_DATA / "pruned_tree_accessions.nwk"
KO_TSV    = FD_DATA / "ko_presence_long.tsv"

N_PERM = 1000
N_BM   = 1000
MIN_N  = 20
CHUNK  = 5_000_000

# ── Load metadata ─────────────────────────────────────────────────────────────
print("Loading curated KO list...")
curated     = pd.read_csv(DATA / "curated_mrg_ko_ids_v2.csv")
ko_meta     = curated.set_index("KO")[["gene_name","primary_category","evidence_tier"]].to_dict("index")
CURATED_KOS = set(curated["KO"])

# ── Load tree and build taxa index ────────────────────────────────────────────
print("Loading tree...")
tree = load_tree(str(TREE_PATH))

taxa_list = []
for tx in tree.taxon_namespace:
    lbl = tx.label.replace(" ", "_")
    tx.label = lbl
    taxa_list.append(lbl)
taxa_set = set(taxa_list)
n_tips   = len(taxa_list)
taxa_pos = {lbl: i for i, lbl in enumerate(taxa_list)}
print(f"Tree tips: {n_tips}")

# ── Pre-compute tree topology (one-time, reused across all KOs) ───────────────
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

# Leaf arrays (post-order leaf indices → taxa_list positions)
is_leaf          = np.array([nd.is_leaf() for nd in postorder_nodes], dtype=bool)
leaf_node_idxs   = np.where(is_leaf)[0]       # shape (n_leaves,)
leaf_labels      = [postorder_nodes[i].taxon.label
                    if postorder_nodes[i].taxon else "" for i in leaf_node_idxs]
leaf_taxon_pos   = np.array([taxa_pos.get(lbl, -1) for lbl in leaf_labels], dtype=np.int32)
valid_mask       = leaf_taxon_pos >= 0
valid_leaf_nodes = leaf_node_idxs[valid_mask]   # post-order indices of leaves in tree
valid_leaf_taxpos= leaf_taxon_pos[valid_mask]   # their positions in taxa_list
assert len(valid_leaf_nodes) == n_tips, \
    f"Leaf/taxa mismatch: {len(valid_leaf_nodes)} leaves vs {n_tips} taxa"

internal_postorder_idx = np.where(~is_leaf)[0]

# All (child, parent) pairs for edge-sum  (all non-root nodes)
child_has_parent = np.array([i for i in range(n_nodes) if parent_arr[i] >= 0], dtype=np.int32)
parent_of_each   = parent_arr[child_has_parent]

# Edge lengths for BM simulation (pre-order)
preorder_idxs = np.array([node_idx[nd] for nd in preorder_nodes], dtype=np.int32)
edge_lengths  = np.zeros(n_nodes, dtype=np.float32)
for nd in preorder_nodes:
    i  = node_idx[nd]
    bl = nd.edge_length if nd.edge_length is not None else 1e-6
    edge_lengths[i] = max(float(bl), 1e-9)
sqrt_el = np.sqrt(edge_lengths)

print(f"Topology ready: {n_nodes} nodes, {len(internal_postorder_idx)} internal, "
      f"{n_tips} leaves, {len(child_has_parent)} edges")


# ── Core batch computation ────────────────────────────────────────────────────

def _propagate_and_sum(tip_leaf_batch):
    """
    tip_leaf_batch: (n_batch, n_tips) float32 — traits in valid_leaf_nodes order
    Propagates states post-order, returns edge_sums (n_batch,).
    """
    n_batch = tip_leaf_batch.shape[0]
    states  = np.zeros((n_batch, n_nodes), dtype=np.float32)
    # Assign tip values: valid_leaf_nodes[j] gets tip_leaf_batch[:, j]
    states[:, valid_leaf_nodes] = tip_leaf_batch
    # Post-order propagation (internal nodes = mean of children)
    for i in internal_postorder_idx:
        chs = children_of[i]
        if len(chs) > 0:
            states[:, i] = states[:, chs].mean(axis=1)
    # Edge sum
    return np.abs(states[:, child_has_parent] - states[:, parent_of_each]).sum(axis=1)


def _taxa_to_leaf_order(taxa_batch):
    """Reorder (n_batch, n_tips) from taxa_list order to valid_leaf_nodes order."""
    return taxa_batch[:, valid_leaf_taxpos]


def edge_sum_taxa_order(taxa_batch):
    """taxa_batch: (n_batch, n_tips) in taxa_list order → edge_sums (n_batch,)."""
    return _propagate_and_sum(_taxa_to_leaf_order(taxa_batch))


def bm_edge_sum_batch(prevalence, n_batch, rng):
    """
    Forward BM on tree → threshold at observed prevalence → edge_sums (n_batch,).
    Pre-generates all normals to minimise per-iteration Python overhead.
    """
    # Pre-generate scaled normals for all nodes
    normals = (rng.standard_normal((n_batch, n_nodes)) * sqrt_el[None, :]).astype(np.float32)
    bm      = np.zeros((n_batch, n_nodes), dtype=np.float32)
    for i in preorder_idxs:
        p = parent_arr[i]
        if p >= 0:
            bm[:, i] = bm[:, p] + normals[:, i]
    # Threshold each simulation at observed prevalence
    tip_bm    = bm[:, valid_leaf_nodes]                              # (n_batch, n_tips) — leaf order
    threshold = np.quantile(tip_bm, 1.0 - prevalence, axis=1)       # (n_batch,)
    binary    = (tip_bm >= threshold[:, None]).astype(np.float32)
    return _propagate_and_sum(binary)


def compute_D(trait_taxa, rng):
    """
    trait_taxa: (n_tips,) float — binary presence in taxa_list order.
    Returns dict with D, p_random, p_conserved, n_present, prevalence.
    """
    n_present  = int(trait_taxa.sum())
    prevalence = n_present / n_tips

    # Reorder to leaf-node order once
    trait_leaf = trait_taxa[valid_leaf_taxpos]  # (n_tips,) in leaf order

    # Observed edge sum
    obs_stat = float(_propagate_and_sum(trait_leaf[None, :])[0])

    # Permutation null: shuffle tip values, keeping tree fixed
    # Shuffle in leaf-order (equivalent to shuffling taxa_list order then reordering)
    perm_matrix = np.array(
        [rng.permutation(trait_leaf) for _ in range(N_PERM)], dtype=np.float32
    )
    perm_stats = _propagate_and_sum(perm_matrix)

    # BM expectation
    bm_stats = bm_edge_sum_batch(prevalence, N_BM, rng)

    mean_perm = float(perm_stats.mean())
    mean_bm   = float(bm_stats.mean())
    denom     = mean_perm - mean_bm
    D         = float((obs_stat - mean_bm) / denom) if abs(denom) > 1e-10 else float("nan")

    # p_random:    fraction of random perms with stat ≤ obs  (low → observed is clustered vs random)
    # p_conserved: fraction of BM sims with stat ≥ obs       (low → observed is more random than BM)
    p_random    = float((perm_stats <= obs_stat).mean())
    p_conserved = float((bm_stats   >= obs_stat).mean())

    return {
        "D": D, "obs_stat": obs_stat, "mean_perm": mean_perm, "mean_bm": mean_bm,
        "p_random": p_random, "p_conserved": p_conserved,
        "n_present": n_present, "prevalence": prevalence,
    }


# ── Load and filter TSV ───────────────────────────────────────────────────────
print(f"\nFiltering {KO_TSV.name} to tree genomes × curated KOs...")
chunks = []
for chunk in pd.read_csv(KO_TSV, sep="\t", chunksize=CHUNK,
                          usecols=["genome_id", "ko"]):
    mask = chunk["genome_id"].isin(taxa_set) & chunk["ko"].isin(CURATED_KOS)
    if mask.any():
        chunks.append(chunk.loc[mask])

pres_df = pd.concat(chunks, ignore_index=True)
print(f"Filtered rows: {len(pres_df):,}  |  unique KOs: {pres_df['ko'].nunique()}")

ko_present_sets = pres_df.groupby("ko")["genome_id"].apply(set).to_dict()
eligible = {ko: gs for ko, gs in ko_present_sets.items()
            if len(gs) >= MIN_N and ko in ko_meta}
print(f"Eligible KOs (n_present ≥ {MIN_N}): {len(eligible)}")


# ── Run Fritz & Purvis D for each eligible KO ─────────────────────────────────
rng     = np.random.default_rng(42)
results = []
n_total = len(eligible)

for i, (ko_id, present_set) in enumerate(sorted(eligible.items()), 1):
    meta = ko_meta.get(ko_id, {})
    trait_taxa = np.array([1.0 if g in present_set else 0.0 for g in taxa_list],
                          dtype=np.float32)
    res = compute_D(trait_taxa, rng)
    row = {
        "ko_id":         ko_id,
        "gene_name":     meta.get("gene_name", ""),
        "subcategory":   meta.get("primary_category", "Unknown"),
        "evidence_tier": meta.get("evidence_tier", "Unknown"),
        **res,
    }
    results.append(row)
    print(f"  [{i:3d}/{n_total}] {ko_id} ({meta.get('gene_name',''):<12}): "
          f"D={res['D']:+.3f}  n={res['n_present']}  prev={res['prevalence']:.3f}  "
          f"p_rand={res['p_random']:.3f}  p_cons={res['p_conserved']:.3f}")

df = pd.DataFrame(results)
df.to_csv(DATA / "fritz_purvis_D_genome.csv", index=False)
print(f"\nSaved {len(df)} rows → data/fritz_purvis_D_genome.csv")


# ── Summary ────────────────────────────────────────────────────────────────────
CAT_ORDER = [
    "Resistance/Detoxification", "Cofactor Biosynthesis",
    "Sensing/Regulation",        "Transport/Homeostasis",
    "Metal-dependent Metabolism","Unknown",
]

print("\n=== BY SUBCATEGORY ===")
cat_D = {}
for cat in CAT_ORDER:
    Dvals = df[df["subcategory"] == cat]["D"].dropna().values
    if len(Dvals) < 2:
        continue
    cat_D[cat] = Dvals
    print(f"  {cat:<30} n={len(Dvals):3d}  "
          f"median D={np.median(Dvals):+.3f}  "
          f"IQR={np.percentile(Dvals,25):+.3f}–{np.percentile(Dvals,75):+.3f}  "
          f"D>0.5: {(Dvals>0.5).mean()*100:.0f}%  D>1: {(Dvals>1).mean()*100:.0f}%")

if len(cat_D) >= 3:
    stat, p = kruskal(*cat_D.values())
    print(f"\nKruskal-Wallis: H={stat:.2f}, p={p:.4e}")

res_D = cat_D.get("Resistance/Detoxification", np.array([]))
cof_D = cat_D.get("Cofactor Biosynthesis",     np.array([]))
oth_D = df[df["subcategory"] != "Resistance/Detoxification"]["D"].dropna().values
if len(res_D) >= 3 and len(cof_D) >= 3:
    stat, p = mannwhitneyu(res_D, cof_D, alternative="greater")
    print(f"MWU resistance D > cofactor: W={stat:.0f}, p={p:.4e}")
if len(res_D) >= 3 and len(oth_D) >= 3:
    stat, p = mannwhitneyu(res_D, oth_D, alternative="greater")
    print(f"MWU resistance D > all others: W={stat:.0f}, p={p:.4e}")

print("\n=== BY EVIDENCE TIER ===")
TIER_ORDER = ["Tier 1","Tier 2","Tier 2-Fitness","Tier 3","Tier 3-BacMet"]
tier_D = {}
for tier in TIER_ORDER:
    Dvals = df[df["evidence_tier"] == tier]["D"].dropna().values
    if len(Dvals) < 2:
        continue
    tier_D[tier] = Dvals
    print(f"  {tier:<18} n={len(Dvals):3d}  median D={np.median(Dvals):+.3f}  "
          f"D>0.5: {(Dvals>0.5).mean()*100:.0f}%  D>1: {(Dvals>1).mean()*100:.0f}%")

if len(tier_D) >= 3:
    stat, p = kruskal(*tier_D.values())
    print(f"\nKruskal-Wallis across tiers: H={stat:.2f}, p={p:.4e}")

print("\n=== HGT CANDIDATES: D > 0.8 ===")
for _, row in df[df["D"] > 0.8].sort_values("D", ascending=False).iterrows():
    print(f"  {row['ko_id']} ({row['gene_name']:<12}) "
          f"[{row['subcategory']:<30}]: "
          f"D={row['D']:+.3f}  n={row['n_present']}")

print("\n=== VERTICALLY CONSERVED: D < 0.2 ===")
for _, row in df[df["D"] < 0.2].sort_values("D").iterrows():
    print(f"  {row['ko_id']} ({row['gene_name']:<12}) "
          f"[{row['subcategory']:<30}]: "
          f"D={row['D']:+.3f}  n={row['n_present']}")


# ── Plot ───────────────────────────────────────────────────────────────────────
CAT_COLORS = {
    "Resistance/Detoxification":  "#d62728",
    "Cofactor Biosynthesis":      "#2ca02c",
    "Sensing/Regulation":         "#ff7f0e",
    "Transport/Homeostasis":      "#1f77b4",
    "Metal-dependent Metabolism": "#8c564b",
    "Unknown":                    "#7f7f7f",
}
plot_rng = np.random.default_rng(42)
fig, ax  = plt.subplots(figsize=(11, 5))
ax.axhline(0, color="grey", lw=1.0, ls="--", alpha=0.7, label="D=0 (BM / conserved)")
ax.axhline(1, color="grey", lw=1.0, ls=":",  alpha=0.7, label="D=1 (random / HGT)")
positions, xlabels = [], []
for cat in CAT_ORDER:
    Dvals = cat_D.get(cat)
    if Dvals is None or len(Dvals) == 0:
        continue
    pos   = len(positions) + 1
    color = CAT_COLORS.get(cat, "#7f7f7f")
    positions.append(pos)
    xlabels.append(f"{cat}\n(n={len(Dvals)})")
    if len(Dvals) >= 3:
        parts = ax.violinplot(Dvals, positions=[pos], widths=0.65,
                              showmedians=True, showextrema=True)
        for pc in parts["bodies"]:
            pc.set_facecolor(color); pc.set_alpha(0.65)
        for k in ("cmedians","cbars","cmaxes","cmins"):
            parts[k].set_color("black")
    ax.scatter(pos + plot_rng.uniform(-0.15, 0.15, size=len(Dvals)),
               Dvals, color=color, s=20, zorder=5, alpha=0.75)
ax.set_xticks(positions)
ax.set_xticklabels(xlabels, fontsize=8)
ax.set_ylabel("Fritz & Purvis D  (genome-level binary phylogenetic signal)", fontsize=9)
ax.set_title(f"Genome-level D — {len(df)} curated metal KOs on 18,961-genome GTDB tree", fontsize=10)
ax.legend(fontsize=8, loc="upper right")
plt.tight_layout()
fig.savefig(DATA.parent / "fritz_purvis_D_genome.pdf", dpi=150)
plt.close()
print("\nSaved fritz_purvis_D_genome.pdf")
print("Done.")

"""
Fritz & Purvis D — genome-level phylogenetic signal for ABC Lipid/LPS KOs.

Runs the same algorithm as fritz_purvis_D_genome.py but targets only the
16 ABC Lipid/LPS subcategory KOs from NB19's internal structure comparison.
These are constitutively required outer-membrane biogenesis genes (Mla, Lpt,
Lol, Tag pathways). Expected result: low D (< 0.2), confirming vertical
inheritance — same pattern as metal cofactor biosynthesis genes.

Purpose: quantify whether the constitutive-vs-conditional split seen in the
metal gene set also appears in an independent non-metal gene family (ABC
Lipid/LPS), supporting or undermining the claim that metal specificity drives
the observed pattern.

Output: data/fritz_purvis_D_abc_lipid_lps.csv
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

sys.path.insert(0, str(Path(__file__).parent))
from pgls_utils import load_tree

DATA      = Path("data")
FD_DATA   = Path("../final_draft/data")
TREE_PATH = FD_DATA / "pruned_tree_accessions.nwk"
KO_TSV    = FD_DATA / "ko_presence_long.tsv"
OUT_CSV   = DATA / "fritz_purvis_D_abc_lipid_lps.csv"

N_PERM = 1000
N_BM   = 1000
MIN_N  = 20
CHUNK  = 5_000_000

# 16 ABC Lipid/LPS KOs from NB19 keyword classification of KEGG ko02010
ABC_LIPID_LPS = {
    "K02065": "mlaF",        # phospholipid/cholesterol transport ATP-binding
    "K02066": "mlaE",        # phospholipid/cholesterol transport permease
    "K02067": "mlaD",        # phospholipid/cholesterol transport substrate-binding
    "K06861": "lptB",        # LPS export system ATP-binding
    "K07091": "lptF",        # LPS export system permease
    "K07122": "mlaB",        # phospholipid transport transporter-binding
    "K07323": "mlaC",        # phospholipid transport substrate-binding
    "K09690": "wzm_rfbA",    # O-antigen transport permease
    "K09691": "wzt_rfbB",    # O-antigen transport ATP-binding
    "K09692": "tagG",        # teichoic acid transport permease
    "K09693": "tagH",        # teichoic acid transport ATP-binding
    "K09808": "lolC_E_F",    # lipoprotein-releasing system permease
    "K09810": "lolD",        # lipoprotein-releasing system ATP-binding
    "K11720": "lptG",        # LPS export system permease
    "K15628": "PXA",         # peroxisomal fatty acid import (eukaryotic ABC)
    "K17324": "glpS",        # glycerol transport ATP-binding
}
TARGET_KOS = set(ABC_LIPID_LPS.keys())

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

# ── Pre-compute tree topology (one-time) ──────────────────────────────────────
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

is_leaf          = np.array([nd.is_leaf() for nd in postorder_nodes], dtype=bool)
leaf_node_idxs   = np.where(is_leaf)[0]
leaf_labels      = [postorder_nodes[i].taxon.label
                    if postorder_nodes[i].taxon else "" for i in leaf_node_idxs]
leaf_taxon_pos   = np.array([taxa_pos.get(lbl, -1) for lbl in leaf_labels], dtype=np.int32)
valid_mask       = leaf_taxon_pos >= 0
valid_leaf_nodes = leaf_node_idxs[valid_mask]
valid_leaf_taxpos= leaf_taxon_pos[valid_mask]
assert len(valid_leaf_nodes) == n_tips, \
    f"Leaf/taxa mismatch: {len(valid_leaf_nodes)} leaves vs {n_tips} taxa"

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

print(f"Topology ready: {n_nodes} nodes, {n_tips} leaves")


# ── Core batch computation (identical to fritz_purvis_D_genome.py) ────────────

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
    perm_stats  = _propagate_and_sum(perm_matrix)
    bm_stats    = bm_edge_sum_batch(prevalence, N_BM, rng)
    mean_perm   = float(perm_stats.mean())
    mean_bm     = float(bm_stats.mean())
    denom       = mean_perm - mean_bm
    D           = float((obs_stat - mean_bm) / denom) if abs(denom) > 1e-10 else float("nan")
    p_random    = float((perm_stats <= obs_stat).mean())
    p_conserved = float((bm_stats   >= obs_stat).mean())
    return {
        "D": D, "obs_stat": obs_stat, "mean_perm": mean_perm, "mean_bm": mean_bm,
        "p_random": p_random, "p_conserved": p_conserved,
        "n_present": n_present, "prevalence": prevalence,
    }


# ── Load and filter TSV to ABC Lipid/LPS KOs ─────────────────────────────────
print(f"\nFiltering {KO_TSV.name} to tree genomes × {len(TARGET_KOS)} ABC Lipid/LPS KOs...")
chunks = []
for chunk in pd.read_csv(KO_TSV, sep="\t", chunksize=CHUNK,
                          usecols=["genome_id", "ko"]):
    mask = chunk["genome_id"].isin(taxa_set) & chunk["ko"].isin(TARGET_KOS)
    if mask.any():
        chunks.append(chunk.loc[mask])

if not chunks:
    print("ERROR: no rows found for ABC Lipid/LPS KOs in TSV. Exiting.")
    sys.exit(1)

pres_df = pd.concat(chunks, ignore_index=True)
print(f"Filtered rows: {len(pres_df):,}  |  unique KOs found: {pres_df['ko'].nunique()}")

ko_present_sets = pres_df.groupby("ko")["genome_id"].apply(set).to_dict()
eligible = {ko: gs for ko, gs in ko_present_sets.items() if len(gs) >= MIN_N}
missing  = TARGET_KOS - set(ko_present_sets.keys())
print(f"Eligible KOs (n_present ≥ {MIN_N}): {len(eligible)}")
if missing:
    print(f"Not found in TSV: {sorted(missing)}")


# ── Run D for each eligible KO ────────────────────────────────────────────────
rng     = np.random.default_rng(42)
results = []
n_total = len(eligible)

for i, (ko_id, present_set) in enumerate(sorted(eligible.items()), 1):
    gene_name = ABC_LIPID_LPS.get(ko_id, "")
    trait_taxa = np.array([1.0 if g in present_set else 0.0 for g in taxa_list],
                          dtype=np.float32)
    res = compute_D(trait_taxa, rng)
    row = {"ko_id": ko_id, "gene_name": gene_name, "subcategory": "ABC_Lipid_LPS", **res}
    results.append(row)
    print(f"  [{i:2d}/{n_total}] {ko_id} ({gene_name:<12}): "
          f"D={res['D']:+.3f}  n={res['n_present']}  prev={res['prevalence']:.3f}  "
          f"p_rand={res['p_random']:.3f}  p_cons={res['p_conserved']:.3f}")

df = pd.DataFrame(results)
df.to_csv(OUT_CSV, index=False)
print(f"\nSaved {len(df)} rows → {OUT_CSV}")


# ── Summary ────────────────────────────────────────────────────────────────────
print("\n=== ABC LIPID/LPS D SUMMARY ===")
D_vals = df["D"].dropna().values
print(f"  n_KOs         : {len(D_vals)}")
print(f"  median D      : {np.median(D_vals):+.3f}")
print(f"  mean D        : {np.mean(D_vals):+.3f}")
print(f"  IQR           : {np.percentile(D_vals,25):+.3f} – {np.percentile(D_vals,75):+.3f}")
print(f"  D < 0.2 (vert.): {(D_vals < 0.2).sum()} / {len(D_vals)}")
print(f"  D > 0.5       : {(D_vals > 0.5).sum()} / {len(D_vals)}")
print(f"  D > 1.0 (HGT) : {(D_vals > 1.0).sum()} / {len(D_vals)}")

# Compare against metal cofactor and resistance D from existing results
try:
    metal_df = pd.read_csv(DATA / "fritz_purvis_D_genome.csv")
    cof_D    = metal_df[metal_df["subcategory"] == "Cofactor Biosynthesis"]["D"].dropna().values
    res_D    = metal_df[metal_df["subcategory"] == "Resistance/Detoxification"]["D"].dropna().values
    print(f"\n=== REFERENCE: Metal subcategories (from fritz_purvis_D_genome.csv) ===")
    print(f"  Cofactor Biosynthesis  n={len(cof_D):3d}  median D={np.median(cof_D):+.3f}")
    print(f"  Resistance/Detox       n={len(res_D):3d}  median D={np.median(res_D):+.3f}")
    print(f"  ABC Lipid/LPS          n={len(D_vals):3d}  median D={np.median(D_vals):+.3f}")
    print(f"\n  Interpretation:")
    if np.median(D_vals) < 0.2:
        print(f"  → ABC Lipid/LPS median D={np.median(D_vals):+.3f} < 0.2: strongly vertically inherited.")
        print(f"  → Constitutive pattern consistent with metal cofactor genes (median D={np.median(cof_D):+.3f}).")
    elif np.median(D_vals) < 0.5:
        print(f"  → ABC Lipid/LPS median D={np.median(D_vals):+.3f}: moderate phylogenetic signal.")
    else:
        print(f"  → ABC Lipid/LPS median D={np.median(D_vals):+.3f}: low phylogenetic signal (HGT-compatible).")
except FileNotFoundError:
    print("\n  (metal D results not found for comparison)")

print("\nDone.")

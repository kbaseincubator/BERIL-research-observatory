"""NB10b finalize — re-run attribution + immediate-save the big parquets."""
import os, json, time, shutil
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path("/home/aparkin/BERIL-research-observatory/projects/gene_function_ecological_agora")
DATA_DIR = PROJECT_ROOT / "data"
USER_DATA = PROJECT_ROOT / "user_data"
FIG_DIR = PROJECT_ROOT / "figures"

t0 = time.time()
print("=== NB10b finalize ===", flush=True)

gains_df = pd.read_parquet(DATA_DIR / "p2_ko_sankoff_gains.parquet")
sankoff_df = pd.read_parquet(DATA_DIR / "p2_ko_sankoff.parquet")
species_df = pd.read_csv(DATA_DIR / "p1b_full_species.tsv", sep="\t")
print(f"Loaded gains ({len(gains_df):,}), sankoff ({len(sankoff_df):,}), species ({len(species_df):,})", flush=True)

# Tree
class Node:
    __slots__ = ("name", "children", "parent", "_id")
    def __init__(self, name="", children=None, parent=None):
        self.name = name; self.children = children or []; self.parent = parent; self._id = id(self)
    def is_leaf(self): return not self.children

def parse_newick(s):
    pos = [0]
    def skip():
        while pos[0] < len(s) and s[pos[0]].isspace(): pos[0] += 1
    def pn(parent=None):
        skip(); ch = []
        if pos[0] < len(s) and s[pos[0]] == "(":
            pos[0] += 1; ch.append(pn()); skip()
            while pos[0] < len(s) and s[pos[0]] == ",":
                pos[0] += 1; ch.append(pn()); skip()
            assert s[pos[0]] == ")"; pos[0] += 1
        skip(); ns = pos[0]
        if pos[0] < len(s) and s[pos[0]] == "'":
            pos[0] += 1
            while pos[0] < len(s) and s[pos[0]] != "'": pos[0] += 1
            if pos[0] < len(s): pos[0] += 1
        while pos[0] < len(s) and s[pos[0]] not in ",();": pos[0] += 1
        tok = s[ns:pos[0]]
        if tok.startswith("'") and "'" in tok[1:]:
            nm = tok[1:tok.find("'", 1)]
        else:
            nm = tok.split(":")[0].strip().strip("'")
        n = Node(name=nm, children=ch, parent=parent)
        for c in ch: c.parent = n
        return n
    return pn()

def prune(n, keep):
    if n.is_leaf(): return n if n.name in keep else None
    kept = [prune(c, keep) for c in n.children]
    kept = [c for c in kept if c is not None]
    if not kept: return None
    if len(kept) == 1: return kept[0]
    n.children = kept
    for c in kept: c.parent = n
    return n

def postorder(root):
    out = []; stack = [(root, False)]
    while stack:
        n, vis = stack.pop()
        if vis: out.append(n)
        else:
            stack.append((n, True))
            for c in n.children: stack.append((c, False))
    return out

rep_ids_set = set(species_df["representative_genome_id"].dropna().tolist())
with open(USER_DATA / "bac120_r214.tree") as f: newick = f.read()
tree = parse_newick(newick); tree = prune(tree, rep_ids_set)
po_list = postorder(tree)
serial_to_node = {}
internal_id = 0
for n in po_list:
    if not n.is_leaf():
        serial_to_node[internal_id] = n
        internal_id += 1
print(f"Tree: {internal_id:,} internal nodes ({time.time()-t0:.1f}s)", flush=True)

# Pre-compute leaves under each internal node
leaves_under = {}
for n in po_list:
    if n.is_leaf():
        leaves_under[n._id] = [n.name]
    else:
        agg = []
        for c in n.children: agg.extend(leaves_under[c._id])
        leaves_under[n._id] = agg

RANKS_DEEP_TO_SHALLOW = ["genus", "family", "order", "class", "phylum"]
DEPTH_BIN_LABELS = {"genus": "recent", "family": "older_recent", "order": "mid", "class": "older",
                    "phylum": "ancient", "phylum_or_above": "ancient"}
tax_cols = ["genus", "family", "order", "class", "phylum"]
rep_to_tax = species_df.set_index("representative_genome_id")[tax_cols].to_dict(orient="index")

def lca_rank(rep_ids):
    for rank in RANKS_DEEP_TO_SHALLOW:
        labels = set()
        for rep in rep_ids:
            tax = rep_to_tax.get(rep)
            if tax is None: continue
            labels.add(tax.get(rank, "unknown"))
            if len(labels) > 1: break
        if len(labels) == 1:
            return rank, next(iter(labels))
    return "phylum_or_above", None

# Attribution — re-run, then save IMMEDIATELY
print(f"Attributing {len(gains_df):,} gains...", flush=True)
ts = time.time()
rows = []
for i, (ko, serial) in enumerate(zip(gains_df["ko"], gains_df["gain_internal_node_serial"])):
    n = serial_to_node[int(serial)]
    leaves = leaves_under[n._id]
    rank, label = lca_rank(leaves)
    rec = {r: None for r in tax_cols}
    if rank != "phylum_or_above":
        any_rep = next((r for r in leaves if r in rep_to_tax), None)
        if any_rep:
            tax = rep_to_tax[any_rep]
            apply_idx = RANKS_DEEP_TO_SHALLOW.index(rank)
            for r in RANKS_DEEP_TO_SHALLOW[apply_idx:]:
                rec[r] = tax.get(r)
    rows.append({"ko": ko, "gain_internal_node_serial": int(serial), "n_leaves_under": len(leaves),
                 "acquisition_depth": rank, "depth_bin": DEPTH_BIN_LABELS.get(rank, "ancient"),
                 "recipient_genus": rec["genus"], "recipient_family": rec["family"],
                 "recipient_order": rec["order"], "recipient_class": rec["class"],
                 "recipient_phylum": rec["phylum"]})
    if (i+1) % 1000000 == 0:
        elapsed = time.time() - ts; rate = (i+1)/elapsed
        print(f"  {i+1}/{len(gains_df)} ({rate:.0f} g/s, ETA {(len(gains_df)-(i+1))/rate:.0f}s)", flush=True)
attributed = pd.DataFrame(rows)
print(f"Attributed in {time.time()-ts:.1f}s", flush=True)

# Join control class
ko_class = sankoff_df[["ko", "control_class_m21"]] if "control_class_m21" in sankoff_df.columns else sankoff_df[["ko", "control_class"]].rename(columns={"control_class": "control_class_m21"})
attributed = attributed.merge(ko_class, on="ko", how="left")

# IMMEDIATE SAVE — biggest file first
print("Writing attributed parquet (this is the big one)...", flush=True)
attributed.to_parquet(DATA_DIR / "p2_m22_gains_attributed.parquet", index=False)
print(f"  wrote {os.path.getsize(DATA_DIR / 'p2_m22_gains_attributed.parquet')/1e6:.1f} MB ({time.time()-t0:.1f}s elapsed)", flush=True)

# Profile aggregation per rank
print("Computing per-rank profile...", flush=True)
profile_rows = []
for rank in RANKS_DEEP_TO_SHALLOW:
    col = f"recipient_{rank}"
    grp = attributed.dropna(subset=[col]).groupby([col, "ko", "control_class_m21", "depth_bin"]).size().reset_index(name="n_gains")
    grp["recipient_rank"] = rank
    grp = grp.rename(columns={col: "recipient_clade"})
    profile_rows.append(grp)
    print(f"  {rank}: {len(grp):,} rows ({time.time()-t0:.1f}s elapsed)", flush=True)
profile = pd.concat(profile_rows, ignore_index=True)
profile.to_parquet(DATA_DIR / "p2_m22_acquisition_profile.parquet", index=False)
print(f"Profile written: {len(profile):,} rows", flush=True)

# Figure
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DEPTH_ORDER = ["recent", "older_recent", "mid", "older", "ancient"]
summary = pd.read_csv(DATA_DIR / "p2_m22_class_depth_summary.tsv", sep="\t", index_col=0)

classes_for_fig = [c for c in ["pos_betalac", "pos_crispr_cas", "pos_tcs_hk",
                                "neg_trna_synth_strict", "neg_rnap_core_strict", "neg_ribosomal_strict"]
                   if c in summary.index]
fig, ax = plt.subplots(figsize=(10, 6))
x = np.arange(len(classes_for_fig))
bottom = np.zeros(len(classes_for_fig))
colors = {"recent": "#d62728", "older_recent": "#ff7f0e", "mid": "#bcbd22",
          "older": "#17becf", "ancient": "#1f77b4"}
for depth in DEPTH_ORDER:
    pct = [summary.loc[c, f"{depth}_pct"] if c in summary.index else 0 for c in classes_for_fig]
    ax.bar(x, pct, bottom=bottom, label=depth, color=colors[depth], alpha=0.85)
    bottom += pct
ax.set_xticks(x); ax.set_xticklabels(classes_for_fig, rotation=30, ha="right")
ax.set_ylabel("% of gain events at depth")
ax.set_title("M22 — acquisition-depth distribution per control class\n(recent/genus → ancient/phylum-or-above)")
ax.legend(loc="upper right")
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig(FIG_DIR / "p2_m22_acquisition_depth_per_class.png", dpi=120, bbox_inches='tight')
print(f"Figure written ({time.time()-t0:.1f}s elapsed)", flush=True)

# Diagnostics
diagnostics = {
    "phase": "2", "notebook": "NB10b", "methodology": "M22",
    "n_gains_attributed": int(len(attributed)),
    "tree_n_internal_nodes": internal_id,
    "n_profile_rows": int(len(profile)),
    "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}
with open(DATA_DIR / "p2_m22_diagnostics.json", "w") as f:
    json.dump(diagnostics, f, indent=2, default=str)
print(f"\n=== DONE in {time.time()-t0:.1f}s ===", flush=True)

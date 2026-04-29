import json, time
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

PROJECT_ROOT = Path("/home/aparkin/BERIL-research-observatory/projects/gene_function_ecological_agora")
DATA_DIR = PROJECT_ROOT / "data"
USER_DATA = PROJECT_ROOT / "user_data"
FIG_DIR = PROJECT_ROOT / "figures"

RANKS_DEEP_TO_SHALLOW = ["genus", "family", "order", "class", "phylum"]
DEPTH_BIN_LABELS = {
    "genus": "recent",
    "family": "older_recent",
    "order": "mid",
    "class": "older",
    "phylum": "ancient",
    "phylum_or_above": "ancient",
}

diagnostics = {
    "phase": "2",
    "notebook": "NB10b",
    "methodology": "M22",
    "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}

gains_df = pd.read_parquet(DATA_DIR / "p2_ko_sankoff_gains.parquet")
sankoff_df = pd.read_parquet(DATA_DIR / "p2_ko_sankoff.parquet")
species_df = pd.read_csv(DATA_DIR / "p1b_full_species.tsv", sep="\t")
print(f"Gains: {len(gains_df):,} events across {gains_df['ko'].nunique()} KOs")
print(f"Sankoff KOs (with class): {len(sankoff_df):,}")
print(f"Species: {len(species_df):,}")

tree_path = USER_DATA / "bac120_r214.tree"
rep_ids_set = set(species_df["representative_genome_id"].dropna().tolist())
rep_to_clade = dict(zip(species_df["representative_genome_id"], species_df["gtdb_species_clade_id"]))

class Node:
    __slots__ = ("name", "children", "parent", "_id")
    def __init__(self, name="", children=None, parent=None):
        self.name = name; self.children = children or []; self.parent = parent; self._id = id(self)
    def is_leaf(self):
        return not self.children

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

def collect(n, out):
    if n.is_leaf(): out.append(n)
    else:
        for c in n.children: collect(c, out)

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

with open(tree_path) as f: newick = f.read()
t0 = time.time()
tree = parse_newick(newick)
tree = prune(tree, rep_ids_set)
po_list = postorder(tree)
internal_id = 0
serial_to_node = {}
for n in po_list:
    if not n.is_leaf():
        serial_to_node[internal_id] = n
        internal_id += 1
print(f"Tree parsed + pruned in {time.time()-t0:.1f}s; {internal_id} internal nodes (serials 0..{internal_id-1})")
diagnostics["tree_n_internal_nodes"] = internal_id

# Leaves-under per internal node, computed in post-order pass
leaves_under = {}
for n in po_list:
    if n.is_leaf():
        leaves_under[n._id] = [n.name]
    else:
        agg = []
        for c in n.children:
            agg.extend(leaves_under[c._id])
        leaves_under[n._id] = agg

# Per-rep taxonomy lookup
tax_cols = ["genus", "family", "order", "class", "phylum"]
rep_to_tax = species_df.set_index("representative_genome_id")[tax_cols].to_dict(orient="index")

def lca_rank(rep_ids):
    """Find deepest rank where all rep_ids share the same taxonomic label. Returns (rank, label).
    If even at phylum they disagree, returns ('phylum_or_above', None)."""
    # Walk from genus (deepest) → phylum (shallowest)
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

diagnostics["n_leaves_total"] = sum(len(v) for v in leaves_under.values() if len(v) == 1)  # leaves only
print(f"Leaves-under cache built. Largest internal subtree: {max(len(v) for v in leaves_under.values()):,} leaves")

t0 = time.time()
rows = []
for i, (ko, serial) in enumerate(zip(gains_df["ko"], gains_df["gain_internal_node_serial"])):
    n = serial_to_node[int(serial)]
    leaves = leaves_under[n._id]
    rank, label = lca_rank(leaves)
    # Recipient labels at every rank (use the most-common label if mixed; for consistent rank, this is the label)
    rec = {r: None for r in tax_cols}
    if rank != "phylum_or_above":
        # Deeper than 'rank' the leaves disagree, so per-rank labels at deeper levels are mixed; use the gain-rank label there
        # At gain-rank and shallower ranks the label is consistent — fill from any leaf
        any_rep = next((r for r in leaves if r in rep_to_tax), None)
        if any_rep:
            tax = rep_to_tax[any_rep]
            # Fill ranks at and shallower than gain rank (they're unambiguous)
            apply_idx = RANKS_DEEP_TO_SHALLOW.index(rank)
            for r in RANKS_DEEP_TO_SHALLOW[apply_idx:]:
                rec[r] = tax.get(r)
    rows.append({
        "ko": ko,
        "gain_internal_node_serial": int(serial),
        "n_leaves_under": len(leaves),
        "acquisition_depth": rank,
        "depth_bin": DEPTH_BIN_LABELS.get(rank, "ancient"),
        "recipient_genus": rec["genus"],
        "recipient_family": rec["family"],
        "recipient_order": rec["order"],
        "recipient_class": rec["class"],
        "recipient_phylum": rec["phylum"],
    })
    if (i+1) % 50000 == 0:
        elapsed = time.time() - t0; rate = (i+1)/elapsed
        print(f"  {i+1}/{len(gains_df)} ({rate:.0f} gains/s, ETA {(len(gains_df)-(i+1))/rate:.0f}s)")

attributed = pd.DataFrame(rows)
diagnostics["n_gains_attributed"] = int(len(attributed))
diagnostics["attribution_elapsed_s"] = round(time.time() - t0, 1)
print(f"\nAttribution complete: {len(attributed):,} gains in {diagnostics['attribution_elapsed_s']}s")
print("Depth-bin distribution:")
print(attributed["depth_bin"].value_counts().to_string())

ko_class = sankoff_df[["ko", "control_class_m21"]] if "control_class_m21" in sankoff_df.columns else sankoff_df[["ko", "control_class"]].rename(columns={"control_class": "control_class_m21"})
attributed = attributed.merge(ko_class, on="ko", how="left")

DEPTH_ORDER = ["recent", "older_recent", "mid", "older", "ancient"]
summary = attributed.groupby(["control_class_m21", "depth_bin"]).size().unstack(fill_value=0)
for c in DEPTH_ORDER:
    if c not in summary.columns: summary[c] = 0
summary = summary[DEPTH_ORDER]
summary["total"] = summary.sum(axis=1)
for c in DEPTH_ORDER:
    summary[f"{c}_pct"] = (summary[c] / summary["total"] * 100).round(1)
print("=== Per-class acquisition-depth distribution ===")
print(summary.to_string())
summary.to_csv(DATA_DIR / "p2_m22_class_depth_summary.tsv", sep="\t")

profile_rows = []
for rank in RANKS_DEEP_TO_SHALLOW:
    col = f"recipient_{rank}"
    grp = attributed.dropna(subset=[col]).groupby([col, "ko", "control_class_m21", "depth_bin"]).size().reset_index(name="n_gains")
    grp["recipient_rank"] = rank
    grp = grp.rename(columns={col: "recipient_clade"})
    profile_rows.append(grp)
profile = pd.concat(profile_rows, ignore_index=True)
profile.to_parquet(DATA_DIR / "p2_m22_acquisition_profile.parquet", index=False)
print(f"Wrote p2_m22_acquisition_profile.parquet: {len(profile):,} (clade × ko × depth × rank) rows")
diagnostics["n_profile_rows"] = int(len(profile))

attributed.to_parquet(DATA_DIR / "p2_m22_gains_attributed.parquet", index=False)
print(f"Wrote p2_m22_gains_attributed.parquet: {len(attributed):,} rows")

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
plt.show()

diagnostics["completed_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
with open(DATA_DIR / "p2_m22_diagnostics.json", "w") as f:
    json.dump(diagnostics, f, indent=2, default=str)
print("Wrote p2_m22_diagnostics.json")

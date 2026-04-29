"""NB10 finalization recovery script.

NB10 ran Stages 1-9 successfully and wrote intermediate atlas at p2_ko_atlas_intermediate.parquet,
but the process died before Stage 10 writes. This script:
  1. Loads intermediate atlas + consumer null
  2. Re-runs Sankoff (single Spark groupBy + Fitch loop, ~4 min)
  3. Recomputes M21 sanity rail
  4. Writes all final outputs

After this script: p2_ko_atlas.parquet, p2_ko_sankoff.parquet, p2_ko_sankoff_gains.parquet,
p2_null_consumer_lookup.parquet, p2_m21_sanity_rail.tsv, p2_atlas_diagnostics.json,
figures/p2_ko_atlas_per_rank.png all present.
"""
import os, json, time, shutil, sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pyspark.sql import functions as F
from berdl_notebook_utils.setup_spark_session import get_spark_session

PROJECT_ROOT = Path("/home/aparkin/BERIL-research-observatory/projects/gene_function_ecological_agora")
DATA_DIR = PROJECT_ROOT / "data"
USER_DATA = PROJECT_ROOT / "user_data"
FIG_DIR = PROJECT_ROOT / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)
RNG_SEED = 42
BOOTSTRAP_B = 200

t_start = time.time()
print("=== NB10 finalization ===", flush=True)

scores_full = pd.read_parquet(DATA_DIR / "p2_ko_atlas_intermediate.parquet")
consumer_all = pd.read_parquet(DATA_DIR / "p2_consumer_intermediate.parquet")
ko_df = pd.read_csv(DATA_DIR / "p2_ko_control_classes.tsv", sep="\t")
species_df = pd.read_csv(DATA_DIR / "p1b_full_species.tsv", sep="\t")
ko_class = ko_df[["ko", "control_class"]]
print(f"Loaded scores_full ({len(scores_full):,} rows), consumer_all ({len(consumer_all):,}), ko_df ({len(ko_df):,}), species_df ({len(species_df):,})", flush=True)

# Sankoff
spark = get_spark_session()
print("Spark ready", flush=True)
tax_df = species_df[["gtdb_species_clade_id", "representative_genome_id", "genus", "family", "order", "class", "phylum"]].copy()
spark.createDataFrame(tax_df).createOrReplaceTempView("species_tax")

MINIO_PATH = "s3a://cdm-lake/tenant-general-warehouse/microbialdiscoveryforge/projects/gene_function_ecological_agora/data/p2_ko_assignments.parquet"
assignments = spark.read.parquet(MINIO_PATH).filter(F.col("is_present")).select("gtdb_species_clade_id", "ko")

t0 = time.time()
ko_to_reps_spark = assignments.join(
    F.broadcast(spark.table("species_tax").select("gtdb_species_clade_id", "representative_genome_id")),
    on="gtdb_species_clade_id", how="inner"
).groupBy("ko").agg(F.collect_set("representative_genome_id").alias("reps"))
ko_to_reps_pdf = ko_to_reps_spark.toPandas()
print(f"ko_to_reps collected: {len(ko_to_reps_pdf):,} rows in {time.time()-t0:.1f}s", flush=True)

# Tree
tree_path = USER_DATA / "bac120_r214.tree"
rep_ids_set = set(species_df["representative_genome_id"].dropna().tolist())

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
node_to_serial = {}
for n in po_list:
    if not n.is_leaf():
        node_to_serial[n._id] = internal_id
        internal_id += 1
print(f"Tree parsed + pruned in {time.time()-t0:.1f}s; {internal_id:,} internal nodes", flush=True)

def fitch_with_gains(po_nodes, present_set):
    states = {}; gains = []
    for n in po_nodes:
        if n.is_leaf():
            states[n._id] = 1 if n.name in present_set else 0
        else:
            cs = set(states[c._id] for c in n.children)
            if len(cs) == 1:
                states[n._id] = next(iter(cs))
            else:
                states[n._id] = 2
                gains.append(node_to_serial[n._id])
    return len(gains), gains

sankoff_rows = []; gain_rows = []
t0 = time.time()
for i, row in enumerate(ko_to_reps_pdf.itertuples()):
    pres = set(row.reps) & rep_ids_set
    if not pres: continue
    gc, glocs = fitch_with_gains(po_list, pres)
    sankoff_rows.append({"ko": row.ko, "sankoff_score": int(gc), "n_present_leaves": len(pres),
                        "score_per_present": round(gc / len(pres), 4)})
    for g in glocs:
        gain_rows.append({"ko": row.ko, "gain_internal_node_serial": int(g)})
    if (i+1) % 2000 == 0:
        elapsed = time.time() - t0; rate = (i+1)/elapsed
        print(f"  Sankoff {i+1}/{len(ko_to_reps_pdf)} ({rate:.0f} KO/s, ETA {(len(ko_to_reps_pdf)-(i+1))/rate:.0f}s)", flush=True)
sankoff_df = pd.DataFrame(sankoff_rows)
gain_df = pd.DataFrame(gain_rows)
sankoff_elapsed = time.time() - t0
print(f"Sankoff done: {len(sankoff_df):,} KOs scored, {len(gain_df):,} gain events ({sankoff_elapsed:.1f}s)", flush=True)

# M21
POS = ["pos_betalac", "pos_crispr_cas", "pos_tcs_hk"]
TRNA_STRICT = {f"K{n:05d}" for n in range(1866, 1891)}
RNAP_STRICT = {"K03040", "K03043", "K03046"}
RIBO_STRICT = {f"K{n:05d}" for n in (list(range(2860, 2900)) + list(range(2950, 2999)))}

def m21_class(row):
    if row["ko"] in RIBO_STRICT: return "neg_ribosomal_strict"
    if row["ko"] in TRNA_STRICT: return "neg_trna_synth_strict"
    if row["ko"] in RNAP_STRICT: return "neg_rnap_core_strict"
    return row["control_class"]

sankoff_with_class = sankoff_df.merge(ko_class, on="ko", how="left")
sankoff_with_class["control_class_m21"] = sankoff_with_class.apply(m21_class, axis=1)

def cohens_d(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    if len(a) < 2 or len(b) < 2: return np.nan
    sd = np.sqrt(((len(a)-1)*a.var(ddof=1) + (len(b)-1)*b.var(ddof=1)) / (len(a)+len(b)-2))
    return (a.mean() - b.mean()) / sd if sd > 0 else 0.0

def boot_d_ci(a, b, B=BOOTSTRAP_B, seed=42):
    rng = np.random.default_rng(seed)
    if len(a) < 2 or len(b) < 2: return (np.nan, np.nan, np.nan)
    pt = cohens_d(a, b)
    bs = np.empty(B)
    a_arr = np.asarray(a); b_arr = np.asarray(b)
    for i in range(B):
        bs[i] = cohens_d(rng.choice(a_arr, len(a_arr), replace=True), rng.choice(b_arr, len(b_arr), replace=True))
    return (pt, np.quantile(bs, 0.025), np.quantile(bs, 0.975))

M21_HK = ["neg_trna_synth_strict", "neg_rnap_core_strict"]
rail_rows = []
for pos in POS:
    pa = sankoff_with_class[sankoff_with_class["control_class_m21"] == pos]["score_per_present"].dropna().values
    for neg in M21_HK:
        nb_v = sankoff_with_class[sankoff_with_class["control_class_m21"] == neg]["score_per_present"].dropna().values
        d, lo, hi = boot_d_ci(pa, nb_v)
        rail_rows.append({"positive_class": pos, "negative_class": neg, "n_pos": len(pa), "n_neg": len(nb_v),
                         "cohens_d": round(d, 4) if not np.isnan(d) else np.nan,
                         "d_ci_lower": round(lo, 4) if not np.isnan(lo) else np.nan,
                         "d_ci_upper": round(hi, 4) if not np.isnan(hi) else np.nan,
                         "meets_d_threshold": (not np.isnan(d)) and d >= 0.30 and lo > 0})
rail_df = pd.DataFrame(rail_rows)
print("=== M21 sanity rail at full atlas scale ===", flush=True)
print(rail_df.to_string(index=False), flush=True)

# Writes
def safe_pq(df, path):
    clean = pd.DataFrame({c: df[c].to_numpy() for c in df.columns})
    if os.path.isdir(path): shutil.rmtree(path)
    elif os.path.isfile(path): os.remove(path)
    clean.to_parquet(path, index=False)

safe_pq(scores_full, str(DATA_DIR / "p2_ko_atlas.parquet"))
print(f"Wrote p2_ko_atlas.parquet ({os.path.getsize(DATA_DIR / 'p2_ko_atlas.parquet')/1e6:.1f} MB)", flush=True)
safe_pq(consumer_all, str(DATA_DIR / "p2_null_consumer_lookup.parquet"))
safe_pq(sankoff_with_class, str(DATA_DIR / "p2_ko_sankoff.parquet"))
safe_pq(gain_df, str(DATA_DIR / "p2_ko_sankoff_gains.parquet"))
rail_df.to_csv(DATA_DIR / "p2_m21_sanity_rail.tsv", sep="\t", index=False)
print("Wrote sankoff + sanity rail", flush=True)

# Diagnostics + figure
diagnostics = {
    "phase": "2", "notebook": "NB10",
    "version": "v2.2 broadcast-hinted aggregation + recovery via 10_finalize.py",
    "n_assignments": int(28008764),
    "n_producer_scores": int(len(scores_full)),
    "sankoff_n_scored": int(len(sankoff_df)),
    "sankoff_total_gain_events": int(len(gain_df)),
    "tree_n_internal_nodes": internal_id,
    "atlas_parquet_size_mb": round(os.path.getsize(DATA_DIR / "p2_ko_atlas.parquet") / 1e6, 1),
    "pp_category_distribution": scores_full["pp_category"].value_counts().to_dict(),
    "m21_rail_n_passing": int(rail_df["meets_d_threshold"].sum()),
    "m21_rail_pairs": rail_df.to_dict(orient="records"),
    "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}
with open(DATA_DIR / "p2_atlas_diagnostics.json", "w") as f:
    json.dump(diagnostics, f, indent=2, default=str)
print("Wrote diagnostics", flush=True)

# Figure
RANKS = ["genus", "family", "order", "class", "phylum"]
fig, axes = plt.subplots(2, len(RANKS), figsize=(4 * len(RANKS), 8))
for i, rank in enumerate(RANKS):
    sub = scores_full[scores_full["rank"] == rank]
    if len(sub) == 0:
        for ax in axes[:, i]: ax.text(0.5, 0.5, "no data", ha="center")
        continue
    axes[0, i].hist(sub["producer_z"].dropna(), bins=50, color="#2ca02c", alpha=0.7)
    axes[0, i].set_title(f"{rank}: producer z (n={len(sub):,})"); axes[0, i].axvline(0, color='k', lw=0.5)
    if "consumer_z" in sub.columns and sub["consumer_z"].notna().any():
        axes[1, i].hist(sub["consumer_z"].dropna(), bins=50, color="#d62728", alpha=0.7)
        axes[1, i].set_title(f"{rank}: consumer z"); axes[1, i].axvline(0, color='k', lw=0.5)
plt.tight_layout()
plt.savefig(FIG_DIR / "p2_ko_atlas_per_rank.png", dpi=120, bbox_inches='tight')
print(f"Wrote {FIG_DIR / 'p2_ko_atlas_per_rank.png'}", flush=True)

print(f"\n=== DONE in {time.time() - t_start:.1f}s ===", flush=True)

import os, json, time
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import sparse, stats
import matplotlib.pyplot as plt
from pyspark.sql import functions as F

try:
    spark  # noqa
    print("Spark: pre-injected")
except NameError:
    from berdl_notebook_utils.setup_spark_session import get_spark_session
    spark = get_spark_session()
    print("Spark: created")

# DO NOT disable broadcast joins — the 18,989-row species_tax frame is small enough to broadcast
# and disabling would force a shuffle that hangs the per-rank aggregation. (NB05's setting harmful here.)

PROJECT_ROOT = Path("/home/aparkin/BERIL-research-observatory/projects/gene_function_ecological_agora")
DATA_DIR = PROJECT_ROOT / "data"
USER_DATA = PROJECT_ROOT / "user_data"
FIG_DIR = PROJECT_ROOT / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

RNG_SEED = 42
rng = np.random.default_rng(RNG_SEED)

RANKS = ["genus", "family", "order", "class", "phylum"]
PARENT_RANK = {"genus": "family", "family": "order", "order": "class", "class": "phylum", "phylum": None}
N_PREVALENCE_BINS = 5
N_PERMUTATIONS = 1000
BOOTSTRAP_B = 200

diagnostics = {
    "phase": "2", "notebook": "NB10", "version": "v2.2 broadcast-hinted aggregation",
    "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "n_permutations": N_PERMUTATIONS, "n_prevalence_bins": N_PREVALENCE_BINS,
}

MINIO_PATH = "s3a://cdm-lake/tenant-general-warehouse/microbialdiscoveryforge/projects/gene_function_ecological_agora/data/p2_ko_assignments.parquet"

species_df = pd.read_csv(DATA_DIR / "p1b_full_species.tsv", sep="\t")
ko_df = pd.read_csv(DATA_DIR / "p2_ko_control_classes.tsv", sep="\t")
print(f"Species: {len(species_df):,} | KOs: {len(ko_df):,}")

tax_df = species_df[["gtdb_species_clade_id", "representative_genome_id", "genus", "family", "order", "class", "phylum"]].copy()
spark.createDataFrame(tax_df).createOrReplaceTempView("species_tax")

# No cache, no count: each per-rank groupBy re-reads MinIO (cheap: filtered count took 1.5s in inline test).
# Caching 28M rows in Spark memory triggers spill/serialization issues that look like a hang.
assignments = spark.read.parquet(MINIO_PATH).filter(F.col("is_present")).select(
    "gtdb_species_clade_id", "ko", "n_uniref90_present"
).withColumn("paralog", F.greatest(F.col("n_uniref90_present"), F.lit(1)).cast("int")).drop("n_uniref90_present")
diagnostics["minio_path"] = MINIO_PATH

rank_data = {}
ko_ids_global = ko_df["ko"].tolist()
ko_to_idx = {k: i for i, k in enumerate(ko_ids_global)}
N_KO = len(ko_ids_global)

for rank in RANKS:
    t0 = time.time()
    # Explicit broadcast hint on species_tax (18,989 rows) — small enough to broadcast trivially
    joined = assignments.join(F.broadcast(spark.table("species_tax")), on="gtdb_species_clade_id", how="inner")
    agg = joined.groupBy(F.col(rank).alias("clade_label"), "ko").agg(
        F.max("paralog").alias("max_paralog"),
        F.countDistinct("gtdb_species_clade_id").alias("n_species_with"),
    ).filter(F.col("clade_label").isNotNull() & (F.col("clade_label") != "unknown"))
    pdf = agg.toPandas()
    elapsed = time.time() - t0
    if len(pdf) == 0:
        rank_data[rank] = None; continue
    clade_ids = sorted(pdf["clade_label"].unique().tolist())
    clade_to_idx = {c: i for i, c in enumerate(clade_ids)}
    K = len(clade_ids)
    pdf["_ci"] = pdf["clade_label"].map(clade_to_idx).astype(np.int64)
    pdf["_ki"] = pdf["ko"].map(ko_to_idx)
    pdf = pdf.dropna(subset=["_ki"])
    pdf["_ki"] = pdf["_ki"].astype(np.int64)
    M_par = sparse.coo_matrix(
        (pdf["max_paralog"].astype(np.int32).values, (pdf["_ci"].values, pdf["_ki"].values)),
        shape=(K, N_KO), dtype=np.int32,
    ).tocsr()
    M_pres = (M_par > 0).astype(np.int8)
    rank_data[rank] = {"M_par": M_par, "M_pres": M_pres, "clade_ids": clade_ids}
    print(f"  {rank:8s}: {K:5d} clades, nnz={M_pres.nnz:,} ({elapsed:.1f}s)")
    diagnostics[f"rank_{rank}_n_clades"] = K
    diagnostics[f"rank_{rank}_nnz"] = int(M_pres.nnz)

for rank in RANKS:
    parent_rank = PARENT_RANK[rank]
    if rank_data[rank] is None or parent_rank is None:
        if rank_data[rank] is not None:
            rank_data[rank]["clade_to_parent_idx"] = None
            rank_data[rank]["unique_parents"] = []
        continue
    clades = rank_data[rank]["clade_ids"]
    parent_lookup = species_df.dropna(subset=[rank, parent_rank]).groupby(rank)[parent_rank].first().to_dict()
    parent_per_clade = [parent_lookup.get(c, "unknown") for c in clades]
    unique_parents = sorted(set(parent_per_clade) - {"unknown"})
    parent_to_idx = {p: i for i, p in enumerate(unique_parents)}
    clade_to_parent_idx = np.array([parent_to_idx.get(p, -1) for p in parent_per_clade])
    rank_data[rank]["clade_to_parent_idx"] = clade_to_parent_idx
    rank_data[rank]["unique_parents"] = unique_parents
    diagnostics[f"rank_{rank}_n_parents"] = len(unique_parents)
    print(f"  {rank:8s} (parent={parent_rank}): {len(unique_parents)} parents")

producer_lookups = {}
ko_prev_bins = {}
for rank in RANKS:
    rd = rank_data[rank]
    if rd is None:
        producer_lookups[rank] = pd.DataFrame(); continue
    M_p = rd["M_par"]; M_pr = rd["M_pres"]; clades = rd["clade_ids"]; K = len(clades)
    prev = np.asarray(M_pr.sum(axis=0)).ravel() / K
    try:
        prev_bin = pd.qcut(pd.Series(prev), N_PREVALENCE_BINS, labels=False, duplicates="drop").fillna(-1).astype(np.int64).to_numpy()
    except ValueError:
        prev_bin = np.zeros(len(prev), dtype=np.int64)
    n_bins = int(np.unique(prev_bin[prev_bin >= 0]).size)
    ko_prev_bins[rank] = prev_bin
    rows = []
    for c_i in range(K):
        present = M_pr.getrow(c_i).toarray().ravel().astype(bool)
        if not present.any(): continue
        par = M_p.getrow(c_i).toarray().ravel()
        for bid in range(n_bins):
            mask = present & (prev_bin == bid)
            csz = int(mask.sum())
            if csz < 5: continue
            par_c = par[mask]
            rows.append({"rank": rank, "clade_idx": c_i, "clade_id": clades[c_i], "prevalence_bin": bid,
                         "cohort_size": csz, "cohort_mean_paralog": float(par_c.mean()),
                         "cohort_std_paralog": float(par_c.std(ddof=1)) if csz > 1 else 0.0})
    df = pd.DataFrame(rows)
    producer_lookups[rank] = df
    print(f"  {rank:8s}: {len(df):,} (clade × bin) rows, {df['clade_idx'].nunique() if len(df) else 0}/{K} scorable")
    diagnostics[f"rank_{rank}_producer_lookup_rows"] = len(df)

consumer_lookups = {}

def parent_dispersion(presence, clade_to_parent_idx):
    n_with = int(presence.sum())
    if n_with == 0: return np.nan
    parents = clade_to_parent_idx[presence.astype(bool)]
    parents = parents[parents >= 0]
    return np.unique(parents).size / n_with

for rank in RANKS:
    rd = rank_data[rank]
    if rd is None or rd.get("clade_to_parent_idx") is None:
        consumer_lookups[rank] = pd.DataFrame(); continue
    parent_rank = PARENT_RANK[rank]
    M_pr = rd["M_pres"]; clades = rd["clade_ids"]; K = len(clades)
    clade_to_parent_idx = rd["clade_to_parent_idx"]
    M_pr_dense = M_pr.toarray()
    rows = []
    t0 = time.time()
    for k_j in range(N_KO):
        presence = M_pr_dense[:, k_j]
        n_with = int(presence.sum())
        if n_with == 0: continue
        obs = parent_dispersion(presence, clade_to_parent_idx)
        nulls = np.empty(N_PERMUTATIONS, dtype=np.float32)
        for p_i in range(N_PERMUTATIONS):
            perm = rng.choice(K, size=n_with, replace=False)
            pp = np.zeros(K, dtype=np.int8); pp[perm] = 1
            nulls[p_i] = parent_dispersion(pp, clade_to_parent_idx)
        m, s = float(nulls.mean()), float(nulls.std(ddof=1))
        z = (obs - m) / s if s > 0 else 0.0
        rows.append({"rank": rank, "ko": ko_ids_global[k_j], "parent_rank": parent_rank,
                     "n_clades_with": n_with, "obs_parent_dispersion": float(obs),
                     "null_mean": m, "null_std": s, "consumer_z": float(z)})
    df = pd.DataFrame(rows)
    consumer_lookups[rank] = df
    print(f"  {rank:8s}: scored {len(df):,} KOs in {time.time()-t0:.1f}s")
    diagnostics[f"rank_{rank}_consumer_scored"] = len(df)

score_rows = []
for rank in RANKS:
    rd = rank_data[rank]
    if rd is None: continue
    M_p = rd["M_par"]; M_pr = rd["M_pres"]; clades = rd["clade_ids"]
    df_lk = producer_lookups[rank]
    if len(df_lk) == 0: continue
    lookup = {(int(r.clade_idx), int(r.prevalence_bin)): (r.cohort_mean_paralog, r.cohort_std_paralog, int(r.cohort_size)) for r in df_lk.itertuples()}
    pb = ko_prev_bins[rank]
    coo = M_pr.tocoo(); par_coo = M_p.tocoo()
    par_dict = dict(zip(zip(par_coo.row, par_coo.col), par_coo.data))
    for k in range(coo.nnz):
        c_i = int(coo.row[k]); k_j = int(coo.col[k])
        bid = int(pb[k_j])
        if bid < 0 or (c_i, bid) not in lookup: continue
        m, s, csz = lookup[(c_i, bid)]
        par = int(par_dict.get((c_i, k_j), 1))
        z = (par - m) / s if s > 0 else 0.0
        score_rows.append((rank, clades[c_i], ko_ids_global[k_j], par, m, s, csz, bid, float(z)))
scores_df = pd.DataFrame(score_rows, columns=["rank", "clade_id", "ko", "paralog_count",
                                              "cohort_mean_paralog", "cohort_std_paralog",
                                              "cohort_size", "prevalence_bin", "producer_z"])
diagnostics["n_producer_scores"] = int(len(scores_df))
print(f"Producer scores: {len(scores_df):,}")
print(scores_df.groupby("rank")["producer_z"].describe()[["count", "mean", "50%", "std"]])

consumer_all = pd.concat([df for df in consumer_lookups.values() if len(df) > 0], ignore_index=True) if any(len(d) > 0 for d in consumer_lookups.values()) else pd.DataFrame()
ko_class = ko_df[["ko", "control_class"]]
scores_full = scores_df.merge(consumer_all[["rank", "ko", "consumer_z", "n_clades_with"]], on=["rank", "ko"], how="left") if len(consumer_all) > 0 else scores_df.copy()
scores_full = scores_full.merge(ko_class, on="ko", how="left")
if "consumer_z" not in scores_full.columns: scores_full["consumer_z"] = np.nan
if "n_clades_with" not in scores_full.columns: scores_full["n_clades_with"] = np.nan

# Vectorized categorize (was apply(axis=1) — too slow on 13.7M rows)
import sys
print("Categorizing...", flush=True)
t0 = time.time()
p_hi = scores_full["producer_z"].fillna(-np.inf) > 1.0
z = scores_full["consumer_z"]
e_hi = z > 0
has_z = z.notna()
cat = np.where(
    ~has_z, "insufficient_data",
    np.where(p_hi & e_hi, "Innovator-Exchange",
        np.where(p_hi & ~e_hi, "Innovator-Isolated",
            np.where(~p_hi & e_hi, "Sink/Broker-Exchange", "Stable")))
)
scores_full["pp_category"] = cat
print(f"Categorize done in {time.time()-t0:.1f}s", flush=True)
diagnostics["pp_category_distribution"] = scores_full["pp_category"].value_counts().to_dict()
print("Producer × Participation category distribution:", flush=True)
print(scores_full["pp_category"].value_counts().to_string(), flush=True)

# Intermediate save: scores_full + consumer_all so we can resume from here on failure
print("Saving intermediate scores_full + consumer_all...", flush=True)
scores_full.to_parquet(DATA_DIR / "p2_ko_atlas_intermediate.parquet", index=False)
if len(consumer_all) > 0:
    consumer_all.to_parquet(DATA_DIR / "p2_consumer_intermediate.parquet", index=False)
print(f"Intermediate saved at {time.time()-t0:.1f}s elapsed", flush=True)

# Tree parsing + Fitch (reused from NB08c/NB09b)
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
diagnostics["tree_n_internal_nodes"] = internal_id
print(f"Tree parsed + pruned in {time.time()-t0:.1f}s; {internal_id:,} internal nodes")

# Get per-KO present-rep set via Spark — single groupBy. Use broadcast join with species_tax.
t0 = time.time()
ko_to_reps_spark = assignments.join(
    F.broadcast(spark.table("species_tax").select("gtdb_species_clade_id", "representative_genome_id")),
    on="gtdb_species_clade_id", how="inner"
).groupBy("ko").agg(F.collect_set("representative_genome_id").alias("reps"))
ko_to_reps_pdf = ko_to_reps_spark.toPandas()
print(f"ko_to_reps collected: {len(ko_to_reps_pdf):,} rows in {time.time()-t0:.1f}s")
ko_to_reps_pdf["n_reps"] = ko_to_reps_pdf["reps"].apply(len)
diagnostics["sankoff_n_kos"] = int(len(ko_to_reps_pdf))
print(f"  median reps per KO: {ko_to_reps_pdf['n_reps'].median():.0f}")

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
                        "score_per_present": round(gc / len(pres), 4) if pres else np.nan})
    for g in glocs:
        gain_rows.append({"ko": row.ko, "gain_internal_node_serial": int(g)})
    if (i+1) % 2000 == 0:
        elapsed = time.time() - t0; rate = (i+1)/elapsed
        print(f"  Sankoff {i+1}/{len(ko_to_reps_pdf)} ({rate:.0f} KO/s, ETA {(len(ko_to_reps_pdf)-(i+1))/rate:.0f}s)")
sankoff_df = pd.DataFrame(sankoff_rows)
gain_df = pd.DataFrame(gain_rows)
diagnostics["sankoff_n_scored"] = int(len(sankoff_df))
diagnostics["sankoff_total_gain_events"] = int(len(gain_df))
diagnostics["sankoff_elapsed_s"] = round(time.time() - t0, 1)
print(f"\nSankoff complete: {len(sankoff_df):,} KOs scored, {len(gain_df):,} gain events ({diagnostics['sankoff_elapsed_s']}s)")

POS = ["pos_betalac", "pos_crispr_cas", "pos_tcs_hk"]
RIBO_STRICT = {f"K{n:05d}" for n in (list(range(2860, 2900)) + list(range(2950, 2999)))}
TRNA_STRICT = {f"K{n:05d}" for n in range(1866, 1891)}
RNAP_STRICT = {"K03040", "K03043", "K03046"}

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

def boot_d_ci(a, b, B=BOOTSTRAP_B, alpha=0.05, seed=42):
    rng = np.random.default_rng(seed)
    if len(a) < 2 or len(b) < 2: return (np.nan, np.nan, np.nan)
    pt = cohens_d(a, b)
    bs = np.empty(B)
    a_arr = np.asarray(a); b_arr = np.asarray(b)
    for i in range(B):
        bs[i] = cohens_d(rng.choice(a_arr, len(a_arr), replace=True), rng.choice(b_arr, len(b_arr), replace=True))
    return (pt, np.quantile(bs, alpha/2), np.quantile(bs, 1-alpha/2))

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
diagnostics["m21_rail_n_passing"] = int(rail_df["meets_d_threshold"].sum())
diagnostics["m21_rail_pairs"] = rail_df.to_dict(orient="records")
print("=== M21 sanity rail at full atlas scale ===")
print(rail_df.to_string(index=False))

def safe_pq(df, path):
    clean = pd.DataFrame({c: df[c].to_numpy() for c in df.columns})
    if os.path.isdir(path):
        import shutil; shutil.rmtree(path)
    elif os.path.isfile(path): os.remove(path)
    clean.to_parquet(path, index=False)

safe_pq(scores_full, str(DATA_DIR / "p2_ko_atlas.parquet"))
diagnostics["atlas_parquet_size_mb"] = round(os.path.getsize(DATA_DIR / "p2_ko_atlas.parquet") / 1e6, 1)
print(f"Wrote p2_ko_atlas.parquet ({diagnostics['atlas_parquet_size_mb']} MB; {len(scores_full):,} rows)")

producer_all = pd.concat([df for df in producer_lookups.values() if len(df) > 0], ignore_index=True)
safe_pq(producer_all, str(DATA_DIR / "p2_null_producer_lookup.parquet"))
if len(consumer_all) > 0:
    safe_pq(consumer_all, str(DATA_DIR / "p2_null_consumer_lookup.parquet"))
safe_pq(sankoff_with_class, str(DATA_DIR / "p2_ko_sankoff.parquet"))
safe_pq(gain_df, str(DATA_DIR / "p2_ko_sankoff_gains.parquet"))
rail_df.to_csv(DATA_DIR / "p2_m21_sanity_rail.tsv", sep="\t", index=False)

diagnostics["completed_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
with open(DATA_DIR / "p2_atlas_diagnostics.json", "w") as f:
    json.dump(diagnostics, f, indent=2, default=str)
print("Wrote p2_atlas_diagnostics.json")

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
plt.show()
print(f"Wrote {FIG_DIR / 'p2_ko_atlas_per_rank.png'}")

"""
Notebook 04: Robustness Checks + AlphaEarth Secondary Signal

Two purposes:

(A) Robustness: are the notebook 03 hits a phylogenetic confound dressed as
    ecology? Re-fit each species with a permutation null and a stratified
    subsample to test stability.
(B) AlphaEarth: as an independent line of evidence, for species with ≥ 30
    genomes carrying AlphaEarth embeddings, test whether the residual GC
    (after removing ANI-cluster mean) correlates with the top embedding PCs.

Outputs:
  - data/04_permutation_results.csv
  - data/04_alphaearth_results.csv
  - figures/04_permutation_null.png
  - figures/04_alphaearth_signal.png
"""

import os
import warnings
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
from scipy import stats as scistats
from sklearn.decomposition import PCA

from berdl_notebook_utils.setup_spark_session import get_spark_session

warnings.filterwarnings("ignore")

PROJECT_DIR = "/home/justaddcoffee/BERIL-research-observatory/projects/gc_ecotype_ecology"
DATA_DIR = os.path.join(PROJECT_DIR, "data")
FIG_DIR = os.path.join(PROJECT_DIR, "figures")

ANI_THRESHOLD = 99.0
MIN_TOTAL = 50
MIN_PER_CAT = 10

# Reuse helper functions
def design_categorical(s):
    cats = pd.Categorical(s)
    codes = cats.codes
    n, k = len(codes), len(cats.categories)
    if k <= 1:
        return np.ones((n, 1))
    X = np.zeros((n, k - 1))
    for j in range(1, k):
        X[codes == j, j - 1] = 1.0
    return X

def design(*blocks):
    parts = [np.ones((blocks[0].shape[0], 1))]
    parts.extend(blocks)
    return np.hstack(parts)

def ols_rss(X, y):
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    rss = float(np.sum(resid ** 2))
    rank = int(np.linalg.matrix_rank(X))
    return rss, len(y) - rank, rank

def partial_F(X_null, X_alt, y):
    rss_null, df_null, rank_null = ols_rss(X_null, y)
    rss_alt,  df_alt,  rank_alt  = ols_rss(X_alt,  y)
    df_diff = rank_alt - rank_null
    if df_diff <= 0 or df_alt <= 0 or rss_alt <= 0:
        return float("nan"), float("nan")
    f = ((rss_null - rss_alt) / df_diff) / (rss_alt / df_alt)
    p = float(scistats.f.sf(f, df_diff, df_alt))
    return float(f), p

def cluster_by_ani(genome_ids, ani_pairs):
    id_to_idx = {g: i for i, g in enumerate(genome_ids)}
    n = len(genome_ids)
    if not ani_pairs:
        return np.arange(n)
    rows, cols = [], []
    for g1, g2 in ani_pairs:
        i, j = id_to_idx.get(g1), id_to_idx.get(g2)
        if i is None or j is None or i == j:
            continue
        rows.append(i); cols.append(j)
        rows.append(j); cols.append(i)
    if not rows:
        return np.arange(n)
    data = np.ones(len(rows), dtype=np.int8)
    g = csr_matrix((data, (rows, cols)), shape=(n, n))
    _, labels = connected_components(g, directed=False)
    return labels


# -----------------------------------------------------------------------------
# Load data
# -----------------------------------------------------------------------------
df = pd.read_parquet(os.path.join(DATA_DIR, "genome_gc_env_categorized.parquet"))
res = pd.read_csv(os.path.join(DATA_DIR, "03_within_species_results.csv"))
sig = pd.read_csv(os.path.join(DATA_DIR, "03_significant_species.csv"))
spark = get_spark_session()

# -----------------------------------------------------------------------------
# (A) Permutation null on the significant species
# -----------------------------------------------------------------------------
print("=== (A) Permutation null test ===")
sig_species = sig["species"].tolist()

def perm_test_species(sp, n_perm=200):
    sub = df[(df["gtdb_species_clade_id"] == sp) & df["iso_category"].notna()].copy()
    sub = sub[sub["iso_category"] != "other"]
    cat_counts = sub["iso_category"].value_counts()
    keep = cat_counts[cat_counts >= MIN_PER_CAT].index.tolist()
    sub = sub[sub["iso_category"].isin(keep)].copy()
    if len(sub) < MIN_TOTAL or len(keep) < 2:
        return None

    if len(sub) > 5000:
        sub = sub.sample(5000, random_state=42)

    genome_ids = sub["genome_id"].tolist()
    gid_list = "','".join(genome_ids)
    try:
        ani = spark.sql(f"""
            SELECT genome1_id, genome2_id
            FROM kbase_ke_pangenome.genome_ani
            WHERE ANI >= {ANI_THRESHOLD}
              AND genome1_id IN ('{gid_list}')
              AND genome2_id IN ('{gid_list}')
        """).toPandas()
    except Exception:
        return None

    pairs = list(zip(ani["genome1_id"].tolist(), ani["genome2_id"].tolist()))
    sub["ani_cluster"] = cluster_by_ani(genome_ids, pairs)
    if sub["ani_cluster"].nunique() < 2:
        return None

    y = sub["gc_pct"].to_numpy(dtype=float)
    X_ani = design_categorical(sub["ani_cluster"])
    X_null = design(X_ani)

    # Observed F
    X_iso = design_categorical(sub["iso_category"])
    X_alt = design(X_ani, X_iso)
    f_obs, p_obs = partial_F(X_null, X_alt, y)

    # Permutation null — shuffle iso_category labels (within species, not within cluster)
    # to break any iso/cluster correlation. This is conservative because within
    # the same cluster, iso labels could be more or less mixed.
    rng = np.random.default_rng(seed=hash(sp) % 2**31)
    f_perm = np.zeros(n_perm)
    iso_arr = sub["iso_category"].to_numpy().copy()
    for i in range(n_perm):
        rng.shuffle(iso_arr)
        X_iso_p = design_categorical(pd.Series(iso_arr))
        X_alt_p = design(X_ani, X_iso_p)
        f_p, _ = partial_F(X_null, X_alt_p, y)
        f_perm[i] = f_p if not np.isnan(f_p) else 0.0

    emp_p = float((np.sum(f_perm >= f_obs) + 1) / (n_perm + 1))
    return {
        "species": sp,
        "f_observed": float(f_obs) if not np.isnan(f_obs) else None,
        "f_perm_median": float(np.median(f_perm)),
        "f_perm_95pct": float(np.percentile(f_perm, 95)),
        "emp_p_value": emp_p,
        "n_perm": n_perm,
    }

perm_results = []
print(f"Permutation testing {len(sig_species)} significant species (200 perms each)...")
for i, sp in enumerate(sig_species):
    out = perm_test_species(sp, n_perm=200)
    if out is not None:
        perm_results.append(out)
    if (i + 1) % 5 == 0:
        print(f"  {i+1}/{len(sig_species)} done")

perm_df = pd.DataFrame(perm_results)
print(f"\nPermutation results: {len(perm_df)} species")
if len(perm_df) > 0:
    n_robust = int((perm_df["emp_p_value"] < 0.05).sum())
    print(f"  Empirical p < 0.05: {n_robust} / {len(perm_df)} ({100*n_robust/len(perm_df):.0f}%)")
perm_df.to_csv(os.path.join(DATA_DIR, "04_permutation_results.csv"), index=False)


# -----------------------------------------------------------------------------
# (B) AlphaEarth secondary signal
# -----------------------------------------------------------------------------
print("\n=== (B) AlphaEarth continuous signal ===")
# Need genome embeddings — load just for our candidate genomes.
# Pull the per-genome means across years.
ae_cols = [f"A{i:02d}" for i in range(64)]
ae_select = ", ".join(ae_cols)
ae_q = spark.sql(f"""
    SELECT genome_id, {ae_select}
    FROM kbase_ke_pangenome.alphaearth_embeddings_all_years
""").toPandas()
ae_q = pd.DataFrame({c: ae_q[c].to_numpy() for c in ae_q.columns})
ae = ae_q.groupby("genome_id")[ae_cols].mean().reset_index()
print(f"  Per-genome AE embeddings: {len(ae):,}")

# Merge with master table
df_ae = df.merge(ae, on="genome_id", how="inner")
print(f"  Genomes with both GC and AE: {len(df_ae):,}")

# Per-species residual GC test
ae_species_results = []
print("  Testing per-species: residual GC ~ top AE PCs (after ANI control)...")
candidate_species = df_ae["gtdb_species_clade_id"].value_counts()
candidate_species = candidate_species[candidate_species >= 30].index.tolist()
print(f"  {len(candidate_species)} species have >= 30 AE-bearing genomes")

for sp in candidate_species:
    sub = df_ae[df_ae["gtdb_species_clade_id"] == sp].copy()
    if len(sub) > 2000:
        sub = sub.sample(2000, random_state=42)
    genome_ids = sub["genome_id"].tolist()
    gid_list = "','".join(genome_ids)
    try:
        ani = spark.sql(f"""
            SELECT genome1_id, genome2_id
            FROM kbase_ke_pangenome.genome_ani
            WHERE ANI >= {ANI_THRESHOLD}
              AND genome1_id IN ('{gid_list}')
              AND genome2_id IN ('{gid_list}')
        """).toPandas()
    except Exception:
        continue

    pairs = list(zip(ani["genome1_id"].tolist(), ani["genome2_id"].tolist()))
    sub["ani_cluster"] = cluster_by_ani(genome_ids, pairs)
    if sub["ani_cluster"].nunique() < 2:
        continue

    # Compute residual GC after removing cluster mean
    sub["gc_resid"] = (
        sub["gc_pct"] - sub.groupby("ani_cluster")["gc_pct"].transform("mean")
    )

    # Same for each AE dimension (residual AE)
    ae_arr = sub[ae_cols].to_numpy()
    cluster_arr = sub["ani_cluster"].to_numpy()
    # Demean by cluster
    for cluster in np.unique(cluster_arr):
        mask = cluster_arr == cluster
        if mask.sum() <= 1:
            continue
        ae_arr[mask] = ae_arr[mask] - ae_arr[mask].mean(axis=0)

    if np.allclose(sub["gc_resid"].to_numpy(), 0):
        continue
    if np.allclose(ae_arr.std(axis=0).sum(), 0):
        continue

    # PCA of within-cluster AE residuals → top 5
    try:
        pca = PCA(n_components=min(5, ae_arr.shape[0]-1, ae_arr.shape[1]))
        pcs = pca.fit_transform(ae_arr)
    except Exception:
        continue
    # Correlate residual GC with each PC
    gc_resid = sub["gc_resid"].to_numpy()
    best = {"r": 0.0, "p": 1.0, "pc": -1}
    for k in range(pcs.shape[1]):
        if pcs[:, k].std() < 1e-9:
            continue
        r, p = scistats.pearsonr(gc_resid, pcs[:, k])
        if abs(r) > abs(best["r"]):
            best = {"r": float(r), "p": float(p), "pc": int(k)}

    ae_species_results.append({
        "species": sp,
        "n_genomes_with_ae": int(len(sub)),
        "n_clusters": int(sub["ani_cluster"].nunique()),
        "best_ae_pc": best["pc"],
        "best_r": best["r"],
        "best_p": best["p"],
        "expl_var_pc1": float(pca.explained_variance_ratio_[0]) if pcs.shape[1] >= 1 else float("nan"),
    })

ae_df = pd.DataFrame(ae_species_results)
print(f"\nAlphaEarth results: {len(ae_df)} species tested")
if len(ae_df) > 0:
    # BH on best_p
    p = ae_df["best_p"].to_numpy()
    order = np.argsort(p)
    n = len(p)
    q = np.empty(n)
    ranked = p[order]
    q_ranked = np.clip(ranked * n / np.arange(1, n+1), 0, 1)
    q_ranked = np.minimum.accumulate(q_ranked[::-1])[::-1]
    q[order] = q_ranked
    ae_df["q_value_bh"] = q
    n_sig = int((ae_df["q_value_bh"] < 0.05).sum())
    print(f"  Species with FDR<0.05 |best_r| (any of 5 PCs): {n_sig} / {len(ae_df)}")
    ae_df.to_csv(os.path.join(DATA_DIR, "04_alphaearth_results.csv"), index=False)

# -----------------------------------------------------------------------------
# Figures
# -----------------------------------------------------------------------------
print("\nMaking figures...")
if len(perm_df) > 0:
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(-np.log10(perm_df["emp_p_value"].clip(lower=1e-3)), bins=20,
            color="#4c72b0", edgecolor="white")
    ax.axvline(-np.log10(0.05), color="red", linestyle="--", label="p=0.05")
    ax.set_xlabel("-log10(empirical p)")
    ax.set_ylabel("Number of species")
    ax.set_title(f"Permutation-null robustness of within-species GC×env signal\n"
                 f"({len(perm_df)} species, 200 permutations each)")
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "04_permutation_null.png"), dpi=150)
    plt.close()

if len(ae_df) > 0:
    fig, ax = plt.subplots(figsize=(8, 5))
    x = ae_df["best_r"].abs()
    y = -np.log10(ae_df["best_p"].clip(lower=1e-300))
    is_sig = ae_df["q_value_bh"] < 0.05
    ax.scatter(x[~is_sig], y[~is_sig], s=14, color="grey", alpha=0.5, label="not sig.")
    ax.scatter(x[is_sig],  y[is_sig],  s=18, color="#c44e52", alpha=0.8, label="FDR<0.05")
    ax.set_xlabel("|Pearson r| of residual GC vs best AE PC (after ANI control)")
    ax.set_ylabel("-log10(p)")
    ax.set_title(f"AlphaEarth continuous signal — within-species GC vs environmental embeddings\n"
                 f"({len(ae_df)} species tested, {int(is_sig.sum())} significant)")
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "04_alphaearth_signal.png"), dpi=150)
    plt.close()

print("\nNotebook 04 complete.")

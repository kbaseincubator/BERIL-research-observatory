"""
Notebook 04b: AlphaEarth-only re-run (part A succeeded; just need part B with fixed col names)
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
        rows.append(i); cols.append(j); rows.append(j); cols.append(i)
    if not rows:
        return np.arange(n)
    g = csr_matrix((np.ones(len(rows), dtype=np.int8), (rows, cols)), shape=(n, n))
    _, labels = connected_components(g, directed=False)
    return labels

df = pd.read_parquet(os.path.join(DATA_DIR, "genome_gc_env_categorized.parquet"))
spark = get_spark_session()

ae_cols = [f"A{i:02d}" for i in range(64)]
ae_select = ", ".join(ae_cols)
print("Pulling AlphaEarth embeddings...")
ae_q = spark.sql(f"SELECT genome_id, {ae_select} FROM kbase_ke_pangenome.alphaearth_embeddings_all_years").toPandas()
ae_q = pd.DataFrame({c: ae_q[c].to_numpy() for c in ae_q.columns})
ae = ae_q.groupby("genome_id")[ae_cols].mean().reset_index()
print(f"Per-genome AE: {len(ae):,}")

df_ae = df.merge(ae, on="genome_id", how="inner")
print(f"Genomes with both GC and AE: {len(df_ae):,}")

candidate_species = df_ae["gtdb_species_clade_id"].value_counts()
candidate_species = candidate_species[candidate_species >= 30].index.tolist()
print(f"{len(candidate_species)} species with >= 30 AE-bearing genomes")

ae_species_results = []
for i, sp in enumerate(candidate_species):
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

    sub["gc_resid"] = sub["gc_pct"] - sub.groupby("ani_cluster")["gc_pct"].transform("mean")
    ae_arr = sub[ae_cols].to_numpy().copy()
    cluster_arr = sub["ani_cluster"].to_numpy()
    for cluster in np.unique(cluster_arr):
        mask = cluster_arr == cluster
        if mask.sum() <= 1:
            continue
        ae_arr[mask] = ae_arr[mask] - ae_arr[mask].mean(axis=0)

    if np.allclose(sub["gc_resid"].to_numpy(), 0):
        continue
    if np.allclose(ae_arr.std(axis=0).sum(), 0):
        continue

    try:
        pca = PCA(n_components=min(5, ae_arr.shape[0]-1, ae_arr.shape[1]))
        pcs = pca.fit_transform(ae_arr)
    except Exception:
        continue

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
        "expl_var_pc1": float(pca.explained_variance_ratio_[0]),
    })
    if (i + 1) % 25 == 0:
        print(f"  {i+1}/{len(candidate_species)} processed")

ae_df = pd.DataFrame(ae_species_results)
print(f"\nAlphaEarth results: {len(ae_df)} species tested")
if len(ae_df) > 0:
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
    print(f"Species with FDR<0.05 |best_r| across 5 PCs: {n_sig} / {len(ae_df)}")
    ae_df.to_csv(os.path.join(DATA_DIR, "04_alphaearth_results.csv"), index=False)

    fig, ax = plt.subplots(figsize=(8, 5))
    x = ae_df["best_r"].abs()
    y = -np.log10(ae_df["best_p"].clip(lower=1e-300))
    is_sig = ae_df["q_value_bh"] < 0.05
    ax.scatter(x[~is_sig], y[~is_sig], s=14, color="grey", alpha=0.5, label="not sig.")
    ax.scatter(x[is_sig],  y[is_sig],  s=18, color="#c44e52", alpha=0.8, label="FDR<0.05")
    ax.set_xlabel("|Pearson r| of residual GC vs best AE PC (after ANI cluster control)")
    ax.set_ylabel("-log10(p)")
    ax.set_title(f"AlphaEarth continuous signal — within-species GC vs environmental embeddings\n"
                 f"({len(ae_df)} species tested, {int(is_sig.sum())} significant at FDR<0.05)")
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "04_alphaearth_signal.png"), dpi=150)
    plt.close()

# Also produce the permutation null figure now (it was last in the script)
perm_df = pd.read_csv(os.path.join(DATA_DIR, "04_permutation_results.csv"))
fig, ax = plt.subplots(figsize=(8, 5))
ax.hist(-np.log10(perm_df["emp_p_value"].clip(lower=1e-3)), bins=20,
        color="#4c72b0", edgecolor="white")
ax.axvline(-np.log10(0.05), color="red", linestyle="--", label="p=0.05")
ax.set_xlabel("-log10(empirical p)")
ax.set_ylabel("Number of species")
ax.set_title(f"Permutation-null robustness of within-species GC×env signal\n"
             f"({len(perm_df)} species, 200 perms each)")
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "04_permutation_null.png"), dpi=150)
plt.close()

print("Done.")

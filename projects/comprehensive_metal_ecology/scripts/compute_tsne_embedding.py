"""
Compute t-SNE embedding of MicrobeAtlas samples for figS1 Panel G.

Steps:
  1. Spark: collect genus-presence lists per sample (same groupBy+collect_set
     as run_snb_benchmarking.py; result is ~50 MB)
  2. Stratified subsample 25,000 samples by biome (pandas)
  3. Build sparse binary genus presence/absence matrix
  4. TruncatedSVD (50 components) → t-SNE (2 components)
  5. Save data/tsne_embedding.csv
"""

import os
os.environ['OMP_NUM_THREADS'] = '1'

import sys, time
import numpy as np
import pandas as pd
import scipy.sparse as sp
from sklearn.decomposition import TruncatedSVD
from sklearn.manifold import TSNE
from pathlib import Path

_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_root))

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'

MIN_SAMPLES  = 10
TSNE_N       = 25_000
RANDOM_STATE = 42

t0 = time.time()
print("=" * 70)
print("t-SNE embedding for MicrobeAtlas samples")
print("=" * 70)

# ── STEP 1: Spark ──────────────────────────────────────────────────────────
print("\nStep 1: Loading genus presence per sample from Spark...", flush=True)

try:
    from berdl_notebook_utils.setup_spark_session import get_spark_session
except ImportError:
    sys.path.insert(0, str(_root / 'scripts'))
    from get_spark_session import get_spark_session

spark = get_spark_session()
from pyspark.sql import functions as F

_tax_parts = F.split(F.col("Tax"), ";")
otu_meta = (
    spark.table("arkinlab_microbeatlas.otu_metadata")
    .select(
        "otu_id",
        F.when(F.size(_tax_parts) >= 6, _tax_parts.getItem(5)).alias("genus"),
    )
    .filter(F.col("genus").isNotNull() & (F.length(F.trim(F.col("genus"))) > 0))
)

otu_counts = (
    spark.table("arkinlab_microbeatlas.otu_counts_long")
    .select(F.col("sample_id").alias("accession_id"), "otu_id", "count")
    .filter(F.col("count") > 0)
)

sg_spark = (
    otu_counts
    .join(otu_meta, on="otu_id", how="inner")
    .select(
        "accession_id",
        F.lower(F.trim(F.col("genus"))).alias("genus_lower"),
    )
    .distinct()
)

# per-genus sample counts (small result)
print("  Computing per-genus sample counts...", flush=True)
genus_counts_pd = sg_spark.groupBy("genus_lower").count().toPandas()
valid_genera_list = (
    genus_counts_pd.loc[genus_counts_pd["count"] >= MIN_SAMPLES, "genus_lower"]
    .tolist()
)
print(
    f"  {len(valid_genera_list)} genera ≥{MIN_SAMPLES} samples "
    f"(of {len(genus_counts_pd)} total) ({time.time()-t0:.0f}s)",
    flush=True,
)

# group per sample — one row per sample, genus list as array
print("  Grouping genera per sample...", flush=True)
sg_grouped_pd = (
    sg_spark
    .filter(F.col("genus_lower").isin(valid_genera_list))
    .groupBy("accession_id")
    .agg(F.collect_set("genus_lower").alias("genera"))
    .toPandas()
)
spark.stop()
print(
    f"  Spark stopped ({time.time()-t0:.0f}s). "
    f"{len(sg_grouped_pd):,} samples",
    flush=True,
)

# ── STEP 2: Stratified subsample by biome ─────────────────────────────────
print("\nStep 2: Stratified subsample by biome...", flush=True)

biome_df = pd.read_csv(
    DATA / 'sample_latlon_env.csv',
    usecols=['sample_id', 'Env_Level_1'],
)
biome_df.columns = ['accession_id', 'biome']
SMALL = {'desert', 'paddy', 'peatland', 'leaf', 'shrub', 'flower'}
biome_df['biome'] = biome_df['biome'].apply(
    lambda x: 'other' if x in SMALL else x
)

sg = sg_grouped_pd.merge(biome_df, on='accession_id', how='left')
sg['biome'] = sg['biome'].fillna('unknown')

rng = np.random.default_rng(RANDOM_STATE)
parts = []
n_total = len(sg)
for biome, grp in sg.groupby('biome'):
    n = max(1, int(TSNE_N * len(grp) / n_total))
    idx = rng.choice(len(grp), min(n, len(grp)), replace=False)
    parts.append(grp.iloc[idx])
subset = pd.concat(parts, ignore_index=True)
print(
    f"  {len(subset):,} samples selected ({time.time()-t0:.0f}s)\n"
    + "\n".join(
        f"    {b}: {n}" for b, n in subset['biome'].value_counts().items()
    ),
    flush=True,
)

# ── STEP 3: Sparse binary presence/absence matrix ─────────────────────────
print("\nStep 3: Building sparse binary matrix...", flush=True)

genera_sorted = sorted(valid_genera_list)
genus_idx = {g: i for i, g in enumerate(genera_sorted)}
G = len(genera_sorted)
N = len(subset)

row_idx, col_idx = [], []
for si, genera_list in enumerate(subset['genera']):
    for g in genera_list:
        ci = genus_idx.get(g)
        if ci is not None:
            row_idx.append(si)
            col_idx.append(ci)

M = sp.csr_matrix(
    (np.ones(len(row_idx), dtype=np.float32), (row_idx, col_idx)),
    shape=(N, G),
)
print(
    f"  {N:,} × {G:,}  |  {len(row_idx):,} non-zeros  "
    f"({time.time()-t0:.0f}s)",
    flush=True,
)

# ── STEP 4: TruncatedSVD → t-SNE ──────────────────────────────────────────
print("\nStep 4: TruncatedSVD (n=50)...", flush=True)
svd = TruncatedSVD(n_components=50, random_state=RANDOM_STATE)
M_svd = svd.fit_transform(M)
print(
    f"  Explained variance (50 PCs): {svd.explained_variance_ratio_.sum():.3f} "
    f"({time.time()-t0:.0f}s)",
    flush=True,
)

print("  t-SNE (perplexity=50, n_iter=1000, init=pca)...", flush=True)
tsne = TSNE(
    n_components=2, perplexity=50, max_iter=1000,
    init='pca', learning_rate='auto',
    random_state=RANDOM_STATE, n_jobs=4,
)
embedding = tsne.fit_transform(M_svd)
print(f"  t-SNE done ({time.time()-t0:.0f}s)", flush=True)

# ── STEP 5: Save ──────────────────────────────────────────────────────────
print("\nStep 5: Saving...", flush=True)
out = subset[['accession_id', 'biome']].copy()
out['tsne_x'] = embedding[:, 0]
out['tsne_y'] = embedding[:, 1]
out.to_csv(DATA / 'tsne_embedding.csv', index=False)
print(f"  Saved {len(out):,} rows → data/tsne_embedding.csv")
print(f"\nTotal: {(time.time()-t0)/60:.1f} min")

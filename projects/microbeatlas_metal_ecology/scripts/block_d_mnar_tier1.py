#!/usr/bin/env python3
"""
Block D: OTU-GeoROC MNAR Tier 1 analysis.
Restricts to 6 non-MNAR metals (Co, Cr, Cu, Ni, Zn, Pb).
All 3,050 GeoROC-matched samples are complete for these 6 metals.
Runs partial Spearman (CLR-transformed OTU abundances vs soil metal concentrations),
controlling for other 5 metals + library size + spatial terms.
Output: data/otu_georoc_tier1_6metal.csv
"""

import sys, os, warnings
import numpy as np
import pandas as pd
from scipy.stats import rankdata
from sklearn.preprocessing import StandardScaler

# ── Spark setup (JupyterHub-compatible) ──────────────────────────────────────
try:
    spark
except NameError:
    sys.path.append('/opt/conda/lib/python3.13/site-packages')
    from berdl_notebook_utils.setup_spark_session import get_spark_session
    spark = get_spark_session()

from pyspark.sql import functions as F
from pyspark.sql.window import Window

# ── Config ───────────────────────────────────────────────────────────────────
DATA_DIR  = 'data'
METALS    = ['Co', 'Cr', 'Cu', 'Ni', 'Zn', 'Pb']
MIN_READS = 1000
PREV_CUT  = 0.05   # 5% prevalence for CLR denominator
MAX_OTUS  = 2000   # top OTUs by CLR variance for testing
N_PERM    = 999    # permutations per metal
DELTA     = 0.65   # multiplicative replacement scalar
SEED      = 42

rng = np.random.default_rng(SEED)

# ── 1. Load GeoROC complete cases ────────────────────────────────────────────
georoc = pd.read_csv(os.path.join(DATA_DIR, 'dir6_georoc_global_pca.csv'))
complete = georoc[georoc[METALS].notna().all(axis=1)].copy()
print(f'Complete cases (6 non-MNAR metals): {len(complete)} / {len(georoc)}')

sample_ids = complete['sample_id'].tolist()
print(f'Querying OTU counts for {len(sample_ids)} sample IDs...')

# ── 2. Spark: fetch OTU counts for GeoROC sample IDs ─────────────────────────
sid_df   = spark.createDataFrame([(s,) for s in sample_ids], ['sample_id'])
otu_raw  = spark.table('arkinlab_microbeatlas.otu_counts_long')
otu_soil = otu_raw.join(sid_df, 'sample_id', 'inner').cache()

# Filter samples by minimum reads
total_per_sample = otu_soil.groupBy('sample_id').agg(F.sum('count').alias('total_reads'))
good_samples     = total_per_sample.filter(F.col('total_reads') >= MIN_READS)
otu_soil         = otu_soil.join(good_samples.select('sample_id'), 'sample_id', 'inner')

n_samples = good_samples.count()
print(f'Samples with >= {MIN_READS} reads: {n_samples}')

# Prevalence filter for CLR denominator (5% of retained samples)
min_prev = max(5, int(n_samples * PREV_CUT))
otu_prev = (otu_soil
    .filter(F.col('count') > 0)
    .groupBy('otu_id')
    .agg(F.countDistinct('sample_id').alias('prevalence'))
    .filter(F.col('prevalence') >= min_prev)
)
otu_filtered = otu_soil.join(otu_prev.select('otu_id'), 'otu_id', 'inner')
n_otus_pre = otu_prev.count()
print(f'OTUs passing prevalence >= {min_prev} samples: {n_otus_pre}')

# ── 3. Relative abundances ────────────────────────────────────────────────────
window_sample = Window.partitionBy('sample_id')
ra_spark = (otu_filtered
    .withColumn('sample_total', F.sum('count').over(window_sample))
    .withColumn('ra', F.col('count') / F.col('sample_total'))
    .select('sample_id', 'otu_id', 'ra')
)

# ── 4. Multiplicative replacement (Martín-Fernández 2003, δ=0.65) ────────────
row_aggs = ra_spark.groupBy('sample_id').agg(
    F.count(F.when(F.col('ra') == 0, 1)).alias('m_zero'),
    F.min(F.when(F.col('ra') > 0, F.col('ra')).otherwise(None)).alias('min_pos'),
    F.sum(F.when(F.col('ra') > 0, F.col('ra')).otherwise(0.0)).alias('sum_nonzero'),
)
delta_lit = F.lit(DELTA)
ra_replaced = (ra_spark
    .join(row_aggs, 'sample_id')
    .withColumn('replace_val', delta_lit * F.col('min_pos'))
    .withColumn('scale_factor',
        (1 - F.col('m_zero') * delta_lit * F.col('min_pos')) / F.col('sum_nonzero'))
    .withColumn('ra_repl',
        F.when(F.col('ra') == 0, F.col('replace_val'))
         .otherwise(F.col('ra') * F.col('scale_factor')))
    .select('sample_id', 'otu_id', 'ra_repl')
)

# ── 5. CLR transform ──────────────────────────────────────────────────────────
log_ra = ra_replaced.withColumn('log_ra', F.log('ra_repl'))
clr_spark = (log_ra
    .withColumn('clr', F.col('log_ra') - F.avg('log_ra').over(window_sample))
    .select('sample_id', 'otu_id', 'clr')
)

# Select top OTUs by CLR variance
otu_var = (clr_spark
    .groupBy('otu_id')
    .agg(F.variance('clr').alias('variance'))
    .orderBy(F.desc('variance'))
    .limit(MAX_OTUS)
)
clr_top = clr_spark.join(otu_var.select('otu_id'), 'otu_id', 'inner')
top_otu_list = otu_var.select('otu_id').toPandas()['otu_id'].tolist()
print(f'Top OTUs selected for testing: {len(top_otu_list)}')

# ── 6. Collect to pandas ──────────────────────────────────────────────────────
print('Collecting CLR matrix to pandas...')
clr_pd = clr_top.toPandas()
clr_pivot = clr_pd.pivot(index='sample_id', columns='otu_id', values='clr')
print(f'CLR matrix shape: {clr_pivot.shape}')

# ── 7. Align samples with GeoROC metal data ───────────────────────────────────
metals_pd = complete.set_index('sample_id')[METALS].copy()
common_idx = metals_pd.index.intersection(clr_pivot.index)
print(f'Samples with both OTU and metal data: {len(common_idx)}')

clr_test  = clr_pivot.loc[common_idx].fillna(0)
metals_cc = metals_pd.loc[common_idx]
geo_sub   = complete.set_index('sample_id').loc[common_idx]

# ── 8. Covariate matrix ───────────────────────────────────────────────────────
# Covariates Z: log_depth + sin/cos lat/lon (no GEE; simpler than NB09a)
lat = geo_sub['lat'].values
lon = geo_sub['lon'].values
cov_base = pd.DataFrame({
    'log_depth': geo_sub['log_depth'].values,
    'sin_lat':   np.sin(np.radians(lat)),
    'cos_lat':   np.cos(np.radians(lat)),
    'sin_lon':   np.sin(np.radians(lon)),
    'cos_lon':   np.cos(np.radians(lon)),
}, index=common_idx)

scaler_cov   = StandardScaler()
cov_scaled   = pd.DataFrame(
    scaler_cov.fit_transform(cov_base),
    index=common_idx, columns=cov_base.columns
)

scaler_metal = StandardScaler()
metals_scaled = pd.DataFrame(
    scaler_metal.fit_transform(metals_cc),
    index=common_idx, columns=METALS
)

# ── 9. Partial Spearman helper ────────────────────────────────────────────────
def residualise_ranks(Y, Z_rank):
    Y_rank   = np.apply_along_axis(rankdata, 0, Y)
    Z_design = np.column_stack([np.ones(Z_rank.shape[0]), Z_rank])
    beta     = np.linalg.lstsq(Z_design, Y_rank, rcond=None)[0]
    return Y_rank - Z_design @ beta

def partial_spearman_matrix(x, Y, Z, n_perm=999, seed=None):
    rng_  = np.random.default_rng(seed)
    n     = len(x)
    Z_rank = np.apply_along_axis(rankdata, 0, Z)
    Z_des  = np.column_stack([np.ones(n), Z_rank])
    Y_res  = residualise_ranks(Y, Z_rank)
    x_rank = rankdata(x)
    bx     = np.linalg.lstsq(Z_des, x_rank, rcond=None)[0]
    x_res  = x_rank - Z_des @ bx
    x_std  = (x_res - x_res.mean()) / (x_res.std(ddof=1) + 1e-300)
    denom  = Y_res.std(axis=0, ddof=1) + 1e-300
    Y_std  = (Y_res - Y_res.mean(axis=0)) / denom
    r_obs  = (x_std @ Y_std) / (n - 1)
    perm_r = np.empty((n_perm, Y.shape[1]))
    for i in range(n_perm):
        px        = rng_.permutation(x_std)
        perm_r[i] = (px @ Y_std) / (n - 1)
    p_perm = (np.abs(perm_r) >= np.abs(r_obs)).mean(axis=0)
    return r_obs, p_perm

# ── 10. Run partial Spearman for each metal ───────────────────────────────────
Y = clr_test.values.astype(float)
results = []
bonferroni_thresh = 0.05 / len(METALS)

for metal in METALS:
    print(f'  Running partial Spearman: {metal} (n={len(common_idx)}, n_perm={N_PERM})...')
    x       = metals_cc[metal].values
    other_m = [m for m in METALS if m != metal]
    Z_metal = metals_scaled[other_m].values
    Z_cov   = cov_scaled.values
    Z       = np.column_stack([Z_cov, Z_metal])

    r_obs, p_perm = partial_spearman_matrix(
        x, Y, Z, n_perm=N_PERM, seed=rng.integers(1_000_000)
    )

    df_metal = pd.DataFrame({
        'otu_id':    top_otu_list[:len(r_obs)],
        'exposure':  metal,
        'partial_r': r_obs,
        'p_perm':    p_perm,
        'n':         len(common_idx),
    })
    results.append(df_metal)
    sig = (p_perm < bonferroni_thresh).sum()
    print(f'    Bonferroni-significant pairs (p<{bonferroni_thresh:.4f}): {sig}')

# ── 11. BH-FDR ───────────────────────────────────────────────────────────────
from scipy.stats import false_discovery_control  # scipy >= 1.7
full_res = pd.concat(results, ignore_index=True)

# Per-metal BH-FDR
full_res['p_adj_metal'] = np.nan
for metal in METALS:
    mask = full_res['exposure'] == metal
    pvals = full_res.loc[mask, 'p_perm'].values
    full_res.loc[mask, 'p_adj_metal'] = false_discovery_control(pvals, method='bh')

# Global BH-FDR
full_res['p_adj_global'] = false_discovery_control(full_res['p_perm'].values, method='bh')

# ── 12. Add OTU taxonomy ──────────────────────────────────────────────────────
print('Fetching OTU taxonomy...')
otu_tax_spark = spark.table('arkinlab_microbeatlas.otu_metadata')
top_otu_df    = spark.createDataFrame([(o,) for o in top_otu_list], ['otu_id'])
tax_pd = (otu_tax_spark
    .join(top_otu_df, 'otu_id', 'inner')
    .select('otu_id', 'Tax')
    .toPandas()
)

def parse_taxonomy(tax_str):
    if not isinstance(tax_str, str):
        return '', ''
    parts = [p.strip() for p in tax_str.split(';')]
    phylum = parts[1] if len(parts) > 1 else ''
    genus  = parts[5] if len(parts) > 5 else ''
    return phylum, genus

tax_pd[['phylum', 'genus']] = pd.DataFrame(
    tax_pd['Tax'].apply(parse_taxonomy).tolist(), index=tax_pd.index
)

full_res = full_res.merge(tax_pd[['otu_id', 'phylum', 'genus']], on='otu_id', how='left')

# ── 13. Save ──────────────────────────────────────────────────────────────────
out_path = os.path.join(DATA_DIR, 'otu_georoc_tier1_6metal.csv')
full_res.sort_values(['exposure', 'p_perm']).to_csv(out_path, index=False)
print(f'\nSaved: {out_path}')
print(f'Rows: {len(full_res):,}  ({len(METALS)} metals × {len(top_otu_list)} OTUs)')

# ── 14. Summary ───────────────────────────────────────────────────────────────
print('\n=== Summary ===')
print(f'n_samples:           {len(common_idx)}')
print(f'n_OTUs_tested:       {len(top_otu_list)}')
print(f'n_tests_total:       {len(full_res):,}')
print(f'Bonferroni thresh:   p < {bonferroni_thresh:.4f}')
print()
for metal in METALS:
    sub = full_res[full_res['exposure'] == metal]
    n_bon = (sub['p_perm'] < bonferroni_thresh).sum()
    n_fdr = (sub['p_adj_metal'] < 0.05).sum()
    top5  = sub.nsmallest(5, 'p_perm')[['otu_id','partial_r','p_perm','genus']].to_string(index=False)
    print(f'{metal}: Bonferroni={n_bon}, FDR(0.05)={n_fdr}')
    print(f'  Top 5:\n{top5}')
    print()

print('Block D complete.')

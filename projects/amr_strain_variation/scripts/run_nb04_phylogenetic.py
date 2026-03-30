#!/usr/bin/env python3
"""NB04: Phylogenetic Signal — ANI extraction + Mantel tests."""
import os, sys, warnings, traceback
import pandas as pd
import numpy as np
from pathlib import Path
from time import time
from scipy import stats
from scipy.spatial.distance import pdist, squareform

warnings.filterwarnings('ignore')

PROJECT_DIR = Path(__file__).resolve().parent.parent
ATLAS_DIR = PROJECT_DIR.parent / 'amr_pangenome_atlas'
DATA_DIR = PROJECT_DIR / 'data'
MATRIX_DIR = DATA_DIR / 'genome_amr_matrices'
ANI_DIR = DATA_DIR / 'ani_matrices'
ANI_DIR.mkdir(exist_ok=True)

LOG_FILE = PROJECT_DIR / 'scripts' / 'nb04_phylogenetic.log'
LOG_FILE.write_text('')

def log(msg):
    ts = pd.Timestamp.now().strftime('%H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

log("NB04: Starting phylogenetic signal analysis")

# ── Spark session ──
sys.path.insert(0, str(PROJECT_DIR.parent.parent / 'scripts'))
from get_spark_session import get_spark_session
spark = get_spark_session()
spark.sql("SELECT 1 AS test").show()
log("Spark session ready")

# ── Utilities ──
def chunked_query(spark, ids, query_template, chunk_size=5000):
    results = []
    for i in range(0, len(ids), chunk_size):
        chunk = ids[i:i+chunk_size]
        id_list = "','".join(str(x) for x in chunk)
        query = query_template.format(id_list=f"'{id_list}'")
        results.append(spark.sql(query).toPandas())
    return pd.concat(results, ignore_index=True) if results else pd.DataFrame()

# ── Phase 1: ANI Extraction ──
log("Phase 1: ANI extraction")

matrix_files = sorted(MATRIX_DIR.glob('*.tsv'))
# Only species with 10-500 genomes (larger ones make ANI queries infeasible)
species_to_extract = []
for mf in matrix_files:
    n_genomes = len(pd.read_csv(mf, sep='\t', usecols=[0]))
    if 10 <= n_genomes <= 500:
        species_to_extract.append((mf.stem, n_genomes))
# Sort smallest first for fast early progress
species_to_extract.sort(key=lambda x: x[1])

log(f"Species eligible for ANI extraction: {len(species_to_extract)}")

t_start = time()
ok_count = 0
cached_count = 0
err_count = 0

for idx, (species_id, n_genomes) in enumerate(species_to_extract):
    ani_path = ANI_DIR / f"{species_id}.tsv"
    if ani_path.exists() and ani_path.stat().st_size > 100:
        cached_count += 1
        if (idx + 1) % 100 == 0:
            log(f"  [{idx+1}/{len(species_to_extract)}] {cached_count} cached, {ok_count} ok, {err_count} err")
        continue

    try:
        matrix = pd.read_csv(MATRIX_DIR / f"{species_id}.tsv", sep='\t', index_col=0)
        genome_ids = matrix.index.tolist()

        # Single query for all genomes (feasible since <= 500)
        g_list = "','".join(str(x) for x in genome_ids)
        ani_combined = spark.sql(f"""
            SELECT genome1_id AS genome_id_1, genome2_id AS genome_id_2, ANI AS ani
            FROM kbase_ke_pangenome.genome_ani
            WHERE genome1_id IN ('{g_list}')
              AND genome2_id IN ('{g_list}')
        """).toPandas()

        if len(ani_combined) == 0:
            err_count += 1
            log(f"  [{idx+1}/{len(species_to_extract)}] {species_id}: no ANI data")
            continue

        # Pivot to square matrix
        ani_pivot = ani_combined.pivot_table(
            index='genome_id_1', columns='genome_id_2',
            values='ani', aggfunc='mean'
        )

        # Make symmetric
        all_ids = sorted(set(ani_pivot.index) | set(ani_pivot.columns))
        ani_square = pd.DataFrame(np.nan, index=all_ids, columns=all_ids)
        for i in all_ids:
            ani_square.loc[i, i] = 100.0
        for i in ani_pivot.index:
            for j in ani_pivot.columns:
                val = ani_pivot.loc[i, j]
                if not np.isnan(val):
                    ani_square.loc[i, j] = val
                    ani_square.loc[j, i] = val

        ani_square.to_csv(ani_path, sep='\t')
        ok_count += 1

        if (idx + 1) % 50 == 0:
            elapsed = time() - t_start
            log(f"  [{idx+1}/{len(species_to_extract)}] {ok_count} ok, {cached_count} cached, {err_count} err, {elapsed/60:.0f}min")

    except Exception as e:
        err_count += 1
        if (idx + 1) % 50 == 0 or 'ERROR' in str(e):
            log(f"  [{idx+1}/{len(species_to_extract)}] {species_id}: ERROR {e}")

elapsed_total = time() - t_start
log(f"ANI extraction done: {ok_count} ok, {cached_count} cached, {err_count} err in {elapsed_total/3600:.1f}h")

spark.stop()
log("Spark stopped")

# ── Phase 2: Mantel Tests ──
log("Phase 2: Mantel tests")

amr_census = pd.read_csv(ATLAS_DIR / 'data' / 'amr_census.csv')
conservation_map = amr_census.set_index('gene_cluster_id')['conservation_class'].to_dict()

def mantel_test(dist_x, dist_y, n_perm=999):
    assert dist_x.shape == dist_y.shape
    n = dist_x.shape[0]
    idx = np.triu_indices(n, k=1)
    x_flat = dist_x[idx]
    y_flat = dist_y[idx]
    valid = ~(np.isnan(x_flat) | np.isnan(y_flat))
    x_flat = x_flat[valid]
    y_flat = y_flat[valid]
    if len(x_flat) < 10:
        return np.nan, np.nan, 0
    r_obs, _ = stats.pearsonr(x_flat, y_flat)
    rng = np.random.default_rng(42)
    n_greater = 0
    for _ in range(n_perm):
        perm = rng.permutation(n)
        dist_y_perm = dist_y[np.ix_(perm, perm)]
        y_perm_flat = dist_y_perm[idx][valid]
        r_perm, _ = stats.pearsonr(x_flat, y_perm_flat)
        if r_perm >= r_obs:
            n_greater += 1
    p_value = (n_greater + 1) / (n_perm + 1)
    return r_obs, p_value, len(x_flat)

ani_files = sorted(ANI_DIR.glob('*.tsv'))
log(f"Running Mantel tests for {len(ani_files)} species...")

mantel_results = []
for idx, ani_path in enumerate(ani_files):
    species_id = ani_path.stem
    amr_path = MATRIX_DIR / f"{species_id}.tsv"
    if not amr_path.exists():
        continue

    try:
        ani_mat = pd.read_csv(ani_path, sep='\t', index_col=0)
        amr_mat = pd.read_csv(amr_path, sep='\t', index_col=0)

        common = sorted(set(ani_mat.index) & set(amr_mat.index))
        if len(common) < 10:
            continue

        ani_aligned = ani_mat.loc[common, common].values.astype(float)
        amr_aligned = amr_mat.loc[common]

        if amr_aligned.shape[1] < 2:
            continue

        ani_dist = 100.0 - ani_aligned
        amr_jaccard = squareform(pdist(amr_aligned.values, metric='jaccard'))

        r_all, p_all, n_pairs = mantel_test(ani_dist, amr_jaccard)

        result = {
            'gtdb_species_clade_id': species_id,
            'n_genomes': len(common),
            'n_amr_genes': amr_aligned.shape[1],
            'n_pairs': n_pairs,
            'mantel_r_all': r_all,
            'mantel_p_all': p_all,
        }

        # Stratified: core vs non-core
        core_genes = [g for g in amr_aligned.columns if conservation_map.get(g) == 'Core']
        noncore_genes = [g for g in amr_aligned.columns if g not in core_genes]

        if len(core_genes) >= 2:
            amr_core_jaccard = squareform(pdist(amr_aligned[core_genes].values, metric='jaccard'))
            r_core, p_core, _ = mantel_test(ani_dist, amr_core_jaccard)
            result['mantel_r_core'] = r_core
            result['mantel_p_core'] = p_core
            result['n_core_genes'] = len(core_genes)

        if len(noncore_genes) >= 2:
            amr_nc_jaccard = squareform(pdist(amr_aligned[noncore_genes].values, metric='jaccard'))
            r_nc, p_nc, _ = mantel_test(ani_dist, amr_nc_jaccard)
            result['mantel_r_noncore'] = r_nc
            result['mantel_p_noncore'] = p_nc
            result['n_noncore_genes'] = len(noncore_genes)

        mantel_results.append(result)

        if (idx + 1) % 50 == 0:
            log(f"  Mantel [{idx+1}/{len(ani_files)}] {len(mantel_results)} results")

    except Exception as e:
        log(f"  Mantel {species_id}: ERROR {e}")

mantel_df = pd.DataFrame(mantel_results)

# BH-FDR correction
if len(mantel_df) > 0:
    from statsmodels.stats.multitest import multipletests

    valid_mask = mantel_df['mantel_p_all'].notna()
    if valid_mask.sum() > 0:
        _, fdr_all, _, _ = multipletests(mantel_df.loc[valid_mask, 'mantel_p_all'], method='fdr_bh')
        mantel_df.loc[valid_mask, 'mantel_fdr_all'] = fdr_all

    valid_core = mantel_df.get('mantel_p_core', pd.Series(dtype=float)).notna()
    if valid_core.sum() > 0:
        _, fdr_core, _, _ = multipletests(mantel_df.loc[valid_core, 'mantel_p_core'], method='fdr_bh')
        mantel_df.loc[valid_core, 'mantel_fdr_core'] = fdr_core

    valid_nc = mantel_df.get('mantel_p_noncore', pd.Series(dtype=float)).notna()
    if valid_nc.sum() > 0:
        _, fdr_nc, _, _ = multipletests(mantel_df.loc[valid_nc, 'mantel_p_noncore'], method='fdr_bh')
        mantel_df.loc[valid_nc, 'mantel_fdr_noncore'] = fdr_nc

mantel_df.to_csv(DATA_DIR / 'mantel_results.csv', index=False)
log(f"Saved mantel_results.csv: {len(mantel_df)} species")

# Summary
if len(mantel_df) > 0:
    sig_all = (mantel_df.get('mantel_fdr_all', pd.Series(dtype=float)) < 0.05).sum()
    log(f"\nNB04 COMPLETE")
    log(f"Species tested: {len(mantel_df)}")
    log(f"Significant phylogenetic signal (FDR<0.05): {sig_all}/{len(mantel_df)}")
    log(f"Median Mantel r (all): {mantel_df['mantel_r_all'].median():.3f}")

    if 'mantel_r_core' in mantel_df:
        both = mantel_df.dropna(subset=['mantel_r_core', 'mantel_r_noncore'])
        if len(both) > 5:
            t_stat, t_pval = stats.ttest_rel(both['mantel_r_core'], both['mantel_r_noncore'])
            log(f"Core vs non-core: {both['mantel_r_core'].mean():.3f} vs {both['mantel_r_noncore'].mean():.3f} (p={t_pval:.1e})")
else:
    log("NB04 COMPLETE — no Mantel results (no ANI data)")

# Re-run NB07 synthesis with updated data
log("Re-running NB07 synthesis...")
os.system(f"cd {PROJECT_DIR} && python3 scripts/run_nb07_synthesis.py")
log("All done!")

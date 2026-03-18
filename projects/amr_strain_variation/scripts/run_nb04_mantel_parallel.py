#!/usr/bin/env python3
"""Run Mantel tests in parallel across multiple CPUs, then inject outputs into NB04."""
import os, sys, warnings, json
import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats
from scipy.spatial.distance import pdist, squareform
from concurrent.futures import ProcessPoolExecutor, as_completed
from statsmodels.stats.multitest import multipletests

warnings.filterwarnings('ignore')

PROJECT_DIR = Path(__file__).resolve().parent.parent
ATLAS_DIR = PROJECT_DIR.parent / 'amr_pangenome_atlas'
DATA_DIR = PROJECT_DIR / 'data'
MATRIX_DIR = DATA_DIR / 'genome_amr_matrices'
ANI_DIR = DATA_DIR / 'ani_matrices'

N_CPUS = min(os.cpu_count(), 16)
print(f"Running Mantel tests with {N_CPUS} CPUs")

# Load AMR metadata
amr_census = pd.read_csv(ATLAS_DIR / 'data' / 'amr_census.csv')
conservation_map = amr_census.set_index('gene_cluster_id')['conservation_class'].to_dict()


def mantel_test(dist_x, dist_y, n_perm=999):
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
    return r_obs, (n_greater + 1) / (n_perm + 1), len(x_flat)


def process_species(ani_path_str):
    """Process one species — returns dict or None."""
    ani_path = Path(ani_path_str)
    species_id = ani_path.stem
    amr_path = MATRIX_DIR / f"{species_id}.tsv"
    if not amr_path.exists():
        return None

    try:
        ani_mat = pd.read_csv(ani_path, sep='\t', index_col=0)
        amr_mat = pd.read_csv(amr_path, sep='\t', index_col=0)

        common = sorted(set(ani_mat.index) & set(amr_mat.index))
        if len(common) < 10:
            return None

        ani_aligned = ani_mat.loc[common, common].values.astype(float)
        amr_aligned = amr_mat.loc[common]
        if amr_aligned.shape[1] < 2:
            return None

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

        return result
    except Exception:
        return None


# Run in parallel
ani_files = sorted(ANI_DIR.glob('*.tsv'))
print(f"Processing {len(ani_files)} species...")

results = []
with ProcessPoolExecutor(max_workers=N_CPUS) as executor:
    futures = {executor.submit(process_species, str(f)): f for f in ani_files}
    done = 0
    for future in as_completed(futures):
        done += 1
        r = future.result()
        if r is not None:
            results.append(r)
        if done % 100 == 0:
            print(f"  [{done}/{len(ani_files)}] {len(results)} results")

mantel_df = pd.DataFrame(results)
print(f"\nMantel tests complete: {len(mantel_df)} species")

# FDR correction
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

# Summary
sig_all = (mantel_df.get('mantel_fdr_all', pd.Series(dtype=float)) < 0.05).sum()
print(f"\nSignificant phylogenetic signal (FDR<0.05): {sig_all}/{len(mantel_df)} ({100*sig_all/len(mantel_df):.1f}%)")
print(f"Median Mantel r (all): {mantel_df['mantel_r_all'].median():.3f}")
print(f"Median Mantel r (core): {mantel_df['mantel_r_core'].dropna().median():.3f}")
print(f"Median Mantel r (noncore): {mantel_df['mantel_r_noncore'].dropna().median():.3f}")

both = mantel_df.dropna(subset=['mantel_r_core', 'mantel_r_noncore'])
if len(both) > 5:
    t_stat, t_pval = stats.ttest_rel(both['mantel_r_core'], both['mantel_r_noncore'])
    print(f"Core vs noncore: t={t_stat:.2f}, p={t_pval:.1e}, n={len(both)}")

print("\nDone!")

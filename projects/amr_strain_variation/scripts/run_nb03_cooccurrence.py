#!/usr/bin/env python3
"""NB03: Co-occurrence & Resistance Islands."""
import os, warnings
import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import squareform

warnings.filterwarnings('ignore')

PROJECT_DIR = Path(__file__).resolve().parent.parent
ATLAS_DIR = PROJECT_DIR.parent / 'amr_pangenome_atlas'
DATA_DIR = PROJECT_DIR / 'data'
MATRIX_DIR = DATA_DIR / 'genome_amr_matrices'

print("NB03: Computing co-occurrence & resistance islands...")

amr_census = pd.read_csv(ATLAS_DIR / 'data' / 'amr_census.csv')
amr_meta = amr_census[['gene_cluster_id', 'amr_gene', 'amr_product', 'mechanism']].drop_duplicates('gene_cluster_id')
amr_meta_dict = amr_meta.set_index('gene_cluster_id').to_dict('index')

def compute_phi(vec_a, vec_b):
    if vec_a.std() == 0 or vec_b.std() == 0:
        return np.nan
    return np.corrcoef(vec_a, vec_b)[0, 1]

def compute_phi_matrix(matrix):
    prevalence = matrix.mean(axis=0)
    variable_genes = prevalence[(prevalence > 0.05) & (prevalence < 0.95)].index.tolist()
    if len(variable_genes) < 2:
        return None, variable_genes
    n = len(variable_genes)
    phi_mat = np.full((n, n), np.nan)
    for i in range(n):
        phi_mat[i, i] = 1.0
        for j in range(i+1, n):
            phi = compute_phi(matrix[variable_genes[i]].values, matrix[variable_genes[j]].values)
            phi_mat[i, j] = phi
            phi_mat[j, i] = phi
    return pd.DataFrame(phi_mat, index=variable_genes, columns=variable_genes), variable_genes

def detect_islands(phi_df, min_size=3, min_phi=0.5):
    if phi_df is None or phi_df.shape[0] < min_size:
        return []
    phi_vals = phi_df.values.copy()
    np.fill_diagonal(phi_vals, 0)
    dist = 1 - phi_vals
    dist = np.clip(dist, 0, 2)
    np.fill_diagonal(dist, 0)
    nan_mask = np.isnan(dist)
    if nan_mask.any():
        dist[nan_mask] = 1.0
    dist = (dist + dist.T) / 2
    np.fill_diagonal(dist, 0)
    try:
        condensed = squareform(dist)
        Z = linkage(condensed, method='average')
        labels = fcluster(Z, t=1 - min_phi, criterion='distance')
    except Exception:
        return []
    genes = phi_df.index.tolist()
    islands = []
    for cluster_id in set(labels):
        members = [genes[i] for i, l in enumerate(labels) if l == cluster_id]
        if len(members) < min_size:
            continue
        member_phi = phi_df.loc[members, members]
        upper_tri = member_phi.values[np.triu_indices(len(members), k=1)]
        mean_phi = np.nanmean(upper_tri)
        if mean_phi >= min_phi:
            islands.append({'genes': members, 'size': len(members), 'mean_phi': mean_phi})
    return islands

# Process all species
matrix_files = sorted(MATRIX_DIR.glob('*.tsv'))
print(f"Processing {len(matrix_files)} species...")

all_islands = []
phi_summaries = []

for idx, mf in enumerate(matrix_files):
    species_id = mf.stem
    matrix = pd.read_csv(mf, sep='\t', index_col=0)
    if matrix.shape[0] < 10 or matrix.shape[1] < 3:
        continue

    phi_df, variable_genes = compute_phi_matrix(matrix)
    if phi_df is None or len(variable_genes) < 3:
        phi_summaries.append({
            'gtdb_species_clade_id': species_id,
            'n_variable_genes': len(variable_genes) if variable_genes else 0,
            'n_pairs': 0, 'mean_phi': np.nan, 'n_islands': 0,
        })
        continue

    n = phi_df.shape[0]
    upper_phis = phi_df.values[np.triu_indices(n, k=1)]
    valid_phis = upper_phis[~np.isnan(upper_phis)]

    islands = detect_islands(phi_df)
    for isl_idx, island in enumerate(islands):
        mechanisms = set()
        gene_names = []
        for g in island['genes']:
            if g in amr_meta_dict:
                mechanisms.add(amr_meta_dict[g].get('mechanism', 'Unknown'))
                gene_names.append(amr_meta_dict[g].get('amr_gene', g))
            else:
                gene_names.append(g)
        all_islands.append({
            'gtdb_species_clade_id': species_id,
            'island_id': f"{species_id}_island{isl_idx}",
            'size': island['size'], 'mean_phi': island['mean_phi'],
            'gene_cluster_ids': '|'.join(island['genes']),
            'gene_names': '|'.join(gene_names),
            'mechanisms': '|'.join(sorted(mechanisms)),
        })

    phi_summaries.append({
        'gtdb_species_clade_id': species_id,
        'n_variable_genes': len(variable_genes),
        'n_pairs': len(valid_phis),
        'mean_phi': np.mean(valid_phis) if len(valid_phis) > 0 else np.nan,
        'median_phi': np.median(valid_phis) if len(valid_phis) > 0 else np.nan,
        'frac_positive_phi': (valid_phis > 0).mean() if len(valid_phis) > 0 else np.nan,
        'frac_strong_phi': (valid_phis > 0.5).mean() if len(valid_phis) > 0 else np.nan,
        'n_islands': len(islands),
    })
    if (idx + 1) % 200 == 0:
        print(f"  [{idx+1}/{len(matrix_files)}] {len(all_islands)} islands so far")

islands_df = pd.DataFrame(all_islands)
phi_summary_df = pd.DataFrame(phi_summaries)

islands_df.to_csv(DATA_DIR / 'resistance_islands.csv', index=False)
phi_summary_df.to_csv(DATA_DIR / 'phi_summary.csv', index=False)

print(f"\nNB03 COMPLETE")
print(f"Species processed: {len(phi_summary_df)}")
print(f"Resistance islands: {len(islands_df)}")
if len(islands_df) > 0:
    print(f"Species with islands: {islands_df['gtdb_species_clade_id'].nunique()}")
    print(f"Mean island size: {islands_df['size'].mean():.1f}")
    print(f"Mean island phi: {islands_df['mean_phi'].mean():.3f}")

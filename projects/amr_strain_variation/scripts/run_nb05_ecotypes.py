#!/usr/bin/env python3
"""NB05: AMR Ecotypes — UMAP + DBSCAN clustering by AMR profile."""
import os, warnings
import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats
from scipy.spatial.distance import pdist, squareform

warnings.filterwarnings('ignore')

try:
    import umap
except ImportError:
    import subprocess
    subprocess.check_call(['pip', 'install', 'umap-learn'])
    import umap

from sklearn.cluster import DBSCAN
from sklearn.metrics import silhouette_score

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / 'data'
MATRIX_DIR = DATA_DIR / 'genome_amr_matrices'

print("NB05: Computing AMR ecotypes...")

genome_meta = pd.read_csv(DATA_DIR / 'genome_metadata.csv')

def classify_environment(row):
    env = str(row.get('isolation_source', '')).lower() if pd.notna(row.get('isolation_source')) else ''
    h = str(row.get('host', '')).lower() if pd.notna(row.get('host')) else ''
    if any(k in env for k in ['blood', 'sputum', 'urine', 'wound', 'clinical', 'hospital', 'patient']):
        return 'Human-Clinical'
    if 'homo sapiens' in h or 'human' in h:
        if any(k in env for k in ['stool', 'feces', 'gut', 'intestin', 'rectal']):
            return 'Human-Gut'
        return 'Human-Other'
    if any(k in env for k in ['chicken', 'poultry', 'swine', 'pig', 'cattle', 'bovine', 'animal']):
        return 'Animal'
    if any(k in h for k in ['gallus', 'sus scrofa', 'bos taurus']):
        return 'Animal'
    if any(k in env for k in ['food', 'meat', 'milk', 'cheese']):
        return 'Food'
    if any(k in env for k in ['water', 'river', 'sewage', 'marine', 'ocean']):
        return 'Water'
    if any(k in env for k in ['soil', 'rhizosphere', 'plant']):
        return 'Soil/Plant'
    return 'Unknown'

genome_meta['environment'] = genome_meta.apply(classify_environment, axis=1)

def detect_ecotypes(matrix, min_cluster_size=5):
    n_genomes = matrix.shape[0]
    if n_genomes < 15:
        return None, None, None
    jaccard_dist = squareform(pdist(matrix.values, metric='jaccard'))
    if np.all(jaccard_dist == 0):
        return None, None, None
    n_neighbors = min(15, n_genomes - 1)
    reducer = umap.UMAP(n_components=2, metric='precomputed', n_neighbors=n_neighbors,
                         min_dist=0.1, random_state=42)
    embedding = reducer.fit_transform(jaccard_dist)
    upper_tri = jaccard_dist[np.triu_indices(n_genomes, k=1)]
    eps = np.percentile(upper_tri[upper_tri > 0], 25) if (upper_tri > 0).any() else 0.3
    eps = max(eps, 0.05)
    clusterer = DBSCAN(eps=eps, min_samples=min_cluster_size, metric='precomputed')
    labels = clusterer.fit_predict(jaccard_dist)
    n_clusters = len(set(labels) - {-1})
    sil = np.nan
    if n_clusters >= 2:
        non_noise = labels != -1
        if non_noise.sum() >= n_clusters + 1:
            sil = silhouette_score(jaccard_dist[non_noise][:, non_noise],
                                   labels[non_noise], metric='precomputed')
    return embedding, labels, sil

matrix_files = sorted(MATRIX_DIR.glob('*.tsv'))
print(f"Processing {len(matrix_files)} species...")

ecotype_rows = []
species_ecotype_summary = []

for idx, mf in enumerate(matrix_files):
    species_id = mf.stem
    matrix = pd.read_csv(mf, sep='\t', index_col=0)
    if matrix.shape[0] < 15 or matrix.shape[1] < 3:
        continue
    try:
        embedding, labels, sil = detect_ecotypes(matrix)
    except Exception as e:
        print(f"  {species_id}: ERROR {e}")
        continue
    if embedding is None:
        continue
    n_clusters = len(set(labels) - {-1})
    for i, genome_id in enumerate(matrix.index):
        ecotype_rows.append({
            'gtdb_species_clade_id': species_id,
            'genome_id': genome_id,
            'ecotype': labels[i],
            'umap_x': embedding[i, 0], 'umap_y': embedding[i, 1],
        })
    species_ecotype_summary.append({
        'gtdb_species_clade_id': species_id,
        'n_genomes': matrix.shape[0], 'n_clusters': n_clusters,
        'silhouette': sil, 'noise_frac': (labels == -1).mean(),
    })
    if (idx + 1) % 200 == 0:
        print(f"  [{idx+1}/{len(matrix_files)}]")

ecotype_df = pd.DataFrame(ecotype_rows)
eco_summary = pd.DataFrame(species_ecotype_summary)

# Env segregation tests
ecotype_meta = ecotype_df.merge(genome_meta[['genome_id', 'environment']], on='genome_id', how='left')
env_tests = []
for species_id, grp in ecotype_meta.groupby('gtdb_species_clade_id'):
    valid = grp[(grp['ecotype'] >= 0) & (grp['environment'] != 'Unknown')]
    if valid['ecotype'].nunique() < 2 or valid['environment'].nunique() < 2:
        continue
    ct = pd.crosstab(valid['ecotype'], valid['environment'])
    if ct.values.sum() < 20:
        continue
    chi2, p, dof, expected = stats.chi2_contingency(ct)
    n = ct.values.sum()
    k = min(ct.shape) - 1
    cramers_v = np.sqrt(chi2 / (n * k)) if k > 0 and n > 0 else 0
    env_tests.append({
        'gtdb_species_clade_id': species_id,
        'n_ecotypes': valid['ecotype'].nunique(),
        'n_environments': valid['environment'].nunique(),
        'n_genomes': len(valid), 'chi2': chi2, 'p_value': p, 'cramers_v': cramers_v,
    })

env_test_df = pd.DataFrame(env_tests)
if len(env_test_df) > 0:
    from statsmodels.stats.multitest import multipletests
    _, fdr, _, _ = multipletests(env_test_df['p_value'], method='fdr_bh')
    env_test_df['fdr'] = fdr

ecotype_df.to_csv(DATA_DIR / 'amr_ecotypes.csv', index=False)
eco_summary.to_csv(DATA_DIR / 'ecotype_summary.csv', index=False)
if len(env_test_df) > 0:
    env_test_df.to_csv(DATA_DIR / 'ecotype_env_tests.csv', index=False)

print(f"\nNB05 COMPLETE")
print(f"Species analyzed: {len(eco_summary)}")
print(f"Species with >= 2 ecotypes: {(eco_summary['n_clusters'] >= 2).sum()}")
if len(env_test_df) > 0:
    print(f"Env-ecotype significant (FDR<0.05): {(env_test_df['fdr'] < 0.05).sum()}/{len(env_test_df)}")

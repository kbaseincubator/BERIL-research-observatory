#!/usr/bin/env python3
"""NB02: Within-Species AMR Variation Metrics."""
import os, sys, warnings
import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats
from scipy.spatial.distance import pdist

warnings.filterwarnings('ignore')

PROJECT_DIR = Path(__file__).resolve().parent.parent
ATLAS_DIR = PROJECT_DIR.parent / 'amr_pangenome_atlas'
DATA_DIR = PROJECT_DIR / 'data'
MATRIX_DIR = DATA_DIR / 'genome_amr_matrices'

print("NB02: Computing variation metrics...")

# Load atlas data
species_summary = pd.read_csv(ATLAS_DIR / 'data' / 'amr_species_summary.csv')
amr_census = pd.read_csv(ATLAS_DIR / 'data' / 'amr_census.csv')
amr_meta = amr_census[['gene_cluster_id', 'amr_gene', 'amr_product', 'mechanism',
                        'conservation_class', 'is_core', 'is_auxiliary', 'is_singleton']].drop_duplicates('gene_cluster_id')

def classify_prevalence(freq):
    if freq >= 0.95: return 'fixed'
    elif freq <= 0.05: return 'rare'
    else: return 'variable'

def compute_species_metrics(matrix):
    n_genomes, n_amr = matrix.shape
    prevalence = matrix.mean(axis=0)
    classes = prevalence.apply(classify_prevalence)
    n_fixed = (classes == 'fixed').sum()
    n_variable = (classes == 'variable').sum()
    n_rare = (classes == 'rare').sum()
    variability_index = n_variable / n_amr if n_amr > 0 else 0

    if n_genomes >= 2:
        jaccard_dists = pdist(matrix.values, metric='jaccard')
        mean_jaccard = np.nanmean(jaccard_dists)
    else:
        mean_jaccard = np.nan

    gene_entropies = []
    for col in matrix.columns:
        p = prevalence[col]
        h = -p * np.log2(p) - (1-p) * np.log2(1-p) if 0 < p < 1 else 0
        gene_entropies.append(h)
    mean_entropy = np.mean(gene_entropies)
    amr_per_genome = matrix.sum(axis=1)

    return {
        'n_genomes': n_genomes, 'n_amr': n_amr,
        'n_fixed': n_fixed, 'n_variable': n_variable, 'n_rare': n_rare,
        'variability_index': variability_index,
        'mean_jaccard': mean_jaccard, 'mean_entropy': mean_entropy,
        'mean_amr_per_genome': amr_per_genome.mean(),
        'std_amr_per_genome': amr_per_genome.std(),
        'min_amr_per_genome': amr_per_genome.min(),
        'max_amr_per_genome': amr_per_genome.max(),
    }, prevalence, classes

# Process all species
species_metrics = []
gene_prevalence_rows = []
matrix_files = sorted(MATRIX_DIR.glob('*.tsv'))
print(f"Processing {len(matrix_files)} species...")

for idx, mf in enumerate(matrix_files):
    species_id = mf.stem
    matrix = pd.read_csv(mf, sep='\t', index_col=0)
    if matrix.shape[0] < 2 or matrix.shape[1] < 1:
        continue
    metrics, prev, classes = compute_species_metrics(matrix)
    metrics['gtdb_species_clade_id'] = species_id
    species_metrics.append(metrics)
    for gene_id in matrix.columns:
        gene_prevalence_rows.append({
            'gtdb_species_clade_id': species_id,
            'gene_cluster_id': gene_id,
            'prevalence': prev[gene_id],
            'prevalence_class': classes[gene_id],
        })
    if (idx + 1) % 200 == 0:
        print(f"  [{idx+1}/{len(matrix_files)}]")

variation_df = pd.DataFrame(species_metrics)
prevalence_df = pd.DataFrame(gene_prevalence_rows)

# Merge atlas metadata
variation_df = variation_df.merge(
    species_summary[['gtdb_species_clade_id', 'phylum', 'class', 'order', 'family',
                      'genus', 'openness', 'amr_density', 'pct_core_amr']],
    on='gtdb_species_clade_id', how='left'
)
prevalence_df = prevalence_df.merge(
    amr_meta[['gene_cluster_id', 'amr_gene', 'mechanism', 'conservation_class']],
    on='gene_cluster_id', how='left'
)

variation_df.to_csv(DATA_DIR / 'amr_variation_by_species.csv', index=False)
prevalence_df.to_csv(DATA_DIR / 'amr_prevalence_by_gene.csv', index=False)

# Summary
r, p = stats.spearmanr(variation_df['openness'].dropna(),
                        variation_df.loc[variation_df['openness'].notna(), 'variability_index'])

print(f"\nNB02 COMPLETE")
print(f"Species: {len(variation_df)}")
print(f"Gene-species records: {len(prevalence_df)}")
print(f"Variability index median: {variation_df['variability_index'].median():.3f}")
print(f"Mean Jaccard median: {variation_df['mean_jaccard'].median():.3f}")
print(f"Variability-openness rho={r:.3f}, p={p:.1e}")
print(f"Prevalence classes: {prevalence_df['prevalence_class'].value_counts().to_dict()}")

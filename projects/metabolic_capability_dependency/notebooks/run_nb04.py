#!/usr/bin/env python3
"""NB04 runner: Metabolic Ecotypes. Runs locally after NB01."""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import pdist
from scipy import stats
from numpy.linalg import lstsq
import os
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
FIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'figures')
os.makedirs(os.path.join(FIG_DIR, 'ecotype_heatmaps'), exist_ok=True)

plt.rcParams.update({'figure.figsize': (12, 8), 'figure.dpi': 150, 'font.size': 11})

print("=" * 60)
print("NB04: Metabolic Ecotypes")
print("=" * 60)

# --- 1. Load Data ---
print("\n[1] Loading per-genome pathway status...")
gapmind = pd.read_csv(os.path.join(DATA_DIR, 'gapmind_genome_pathway_status.csv'),
                       usecols=['genome_id', 'clade_name', 'pathway', 'is_complete'])
gapmind['is_complete'] = pd.to_numeric(gapmind['is_complete'], errors='coerce')
print(f"  Loaded: {len(gapmind):,} rows")

# Pivot to genome x pathway matrix
print("  Pivoting to genome x pathway matrix...")
pathway_matrix = gapmind.pivot_table(
    index=['genome_id', 'clade_name'],
    columns='pathway',
    values='is_complete',
    aggfunc='max'
).fillna(0).astype(int)
print(f"  Matrix: {pathway_matrix.shape[0]:,} genomes x {pathway_matrix.shape[1]} pathways")

pangenome = pd.read_csv(os.path.join(DATA_DIR, 'pangenome_stats.csv'))
for col in ['no_genomes', 'no_gene_clusters', 'no_core', 'no_aux_genome']:
    if col in pangenome.columns:
        pangenome[col] = pd.to_numeric(pangenome[col], errors='coerce')

# --- 2. Identify species with pathway variation ---
print("\n[2] Identifying species with pathway variation...")
pathway_matrix_flat = pathway_matrix.reset_index()
species_counts = pathway_matrix_flat.groupby('clade_name').size()

MIN_GENOMES = 50
target_species = species_counts[species_counts >= MIN_GENOMES].index.tolist()
print(f"  Species with >= {MIN_GENOMES} genomes: {len(target_species):,}")

variable_counts = []
for sp in target_species:
    sp_data = pathway_matrix_flat[pathway_matrix_flat['clade_name'] == sp]
    pathways_only = sp_data.drop(columns=['genome_id', 'clade_name'])
    n_variable = ((pathways_only.mean() > 0.05) & (pathways_only.mean() < 0.95)).sum()
    variable_counts.append({'clade_name': sp, 'n_genomes': len(sp_data), 'n_variable_pathways': n_variable})

var_df = pd.DataFrame(variable_counts)
print(f"\n  Variable pathway distribution:")
print(var_df['n_variable_pathways'].describe().to_string())
print(f"  Species with >5 variable pathways: {(var_df['n_variable_pathways'] > 5).sum()}")

# --- 3. Cluster genomes ---
print("\n[3] Clustering genomes by pathway profile...")
MIN_VARIABLE = 3
cluster_species = var_df[var_df['n_variable_pathways'] >= MIN_VARIABLE]['clade_name'].tolist()
print(f"  Species to cluster: {len(cluster_species):,}")

ecotype_results = []
for i, sp in enumerate(cluster_species):
    sp_data = pathway_matrix_flat[pathway_matrix_flat['clade_name'] == sp]
    genome_ids = sp_data['genome_id'].values
    profiles = sp_data.drop(columns=['genome_id', 'clade_name']).values

    col_var = profiles.std(axis=0) > 0
    profiles_var = profiles[:, col_var]

    if profiles_var.shape[1] < 2:
        continue

    try:
        dist = pdist(profiles_var, metric='jaccard')
        Z = linkage(dist, method='ward')
        max_d = Z[-1, 2]
        clusters = fcluster(Z, t=max_d * 0.5, criterion='distance')
        n_ecotypes = len(set(clusters))
    except Exception:
        n_ecotypes = 1
        clusters = np.ones(len(genome_ids), dtype=int)

    for gid, cl in zip(genome_ids, clusters):
        ecotype_results.append({'genome_id': gid, 'clade_name': sp, 'ecotype': cl})

    if i < 3 or (i % 100 == 0):
        print(f"    [{i+1}/{len(cluster_species)}] {sp[:50]:50s}: {n_ecotypes} ecotypes, {len(genome_ids)} genomes")

ecotype_df = pd.DataFrame(ecotype_results)
print(f"\n  Total ecotype assignments: {len(ecotype_df):,}")

# --- 4. Ecotype summary and correlation ---
print("\n[4] Ecotype summary and correlation with openness...")
ecotype_summary = ecotype_df.groupby('clade_name').agg(
    n_ecotypes=('ecotype', 'nunique'),
    n_genomes=('genome_id', 'nunique'),
).reset_index()

ecotype_merged = ecotype_summary.merge(
    pangenome, left_on='clade_name', right_on='gtdb_species_clade_id', how='inner'
)
ecotype_merged['openness'] = ecotype_merged['no_aux_genome'] / ecotype_merged['no_gene_clusters']

rho, p = stats.spearmanr(ecotype_merged['n_ecotypes'], ecotype_merged['openness'])
print(f"  Spearman(n_ecotypes, openness): rho={rho:.3f}, p={p:.2e}")

rho_ng, p_ng = stats.spearmanr(ecotype_merged['n_ecotypes'], ecotype_merged['n_genomes'])
print(f"  Confound: n_ecotypes vs n_genomes: rho={rho_ng:.3f}")

def partial_spearman(x, y, z):
    from scipy.stats import spearmanr, rankdata
    rx, ry, rz = rankdata(x), rankdata(y), rankdata(z)
    A = np.column_stack([rz, np.ones(len(rz))])
    bx = lstsq(A, rx, rcond=None)[0]
    by = lstsq(A, ry, rcond=None)[0]
    return spearmanr(rx - A @ bx, ry - A @ by)

mask = ecotype_merged[['n_ecotypes', 'openness', 'n_genomes']].dropna().index
if len(mask) > 30:
    rho_p, p_p = partial_spearman(
        ecotype_merged.loc[mask, 'n_ecotypes'],
        ecotype_merged.loc[mask, 'openness'],
        ecotype_merged.loc[mask, 'n_genomes']
    )
    print(f"  Partial Spearman (ctrl n_genomes): rho={rho_p:.3f}, p={p_p:.2e}")

ecotype_merged['ecotypes_per_genome'] = ecotype_merged['n_ecotypes'] / ecotype_merged['n_genomes']
rho_norm, p_norm = stats.spearmanr(ecotype_merged['ecotypes_per_genome'], ecotype_merged['openness'])
print(f"  Spearman(ecotypes/genome, openness): rho={rho_norm:.3f}, p={p_norm:.2e}")

# Plot
fig, axes = plt.subplots(1, 3, figsize=(18, 6))
axes[0].scatter(ecotype_merged['n_ecotypes'], ecotype_merged['openness'], alpha=0.3, s=10)
axes[0].set_xlabel('Number of Metabolic Ecotypes')
axes[0].set_ylabel('Pangenome Openness')
axes[0].set_title(f'Raw: rho={rho:.3f}, p={p:.1e}')

axes[1].scatter(ecotype_merged['n_ecotypes'], ecotype_merged['n_genomes'], alpha=0.3, s=10)
axes[1].set_xlabel('Number of Metabolic Ecotypes')
axes[1].set_ylabel('Number of Genomes')
axes[1].set_title(f'Confound check: rho={rho_ng:.3f}')

axes[2].hist(ecotype_merged['ecotypes_per_genome'], bins=50, edgecolor='black', alpha=0.7)
axes[2].set_xlabel('Ecotypes per Genome')
axes[2].set_ylabel('Count (species)')
axes[2].set_title(f'Normalized vs openness rho={rho_norm:.3f}')

plt.suptitle('Metabolic Ecotypes vs Openness (with controls)\n'
             'ecotype_analysis: phylogeny dominates gene content for 60.5% of species', fontsize=13)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'ecotype_count_vs_openness.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: ecotype_count_vs_openness.png")

# --- 5. Example heatmaps ---
print("\n[5] Generating ecotype heatmaps for top species...")
top_species = ecotype_summary.nlargest(5, 'n_ecotypes')['clade_name'].tolist()

for sp in top_species:
    sp_data = pathway_matrix_flat[pathway_matrix_flat['clade_name'] == sp]
    sp_ecotypes = ecotype_df[ecotype_df['clade_name'] == sp].set_index('genome_id')['ecotype']

    profiles = sp_data.drop(columns=['genome_id', 'clade_name'])
    var_cols = profiles.columns[profiles.std() > 0]

    if len(var_cols) < 3:
        continue

    plot_data = profiles[var_cols].copy()
    plot_data.index = sp_data['genome_id'].values
    plot_data['ecotype'] = plot_data.index.map(sp_ecotypes)
    plot_data = plot_data.sort_values('ecotype')
    ecotype_col = plot_data.pop('ecotype')

    fig, ax = plt.subplots(figsize=(max(10, len(var_cols) * 0.4), max(6, len(plot_data) * 0.05)))
    sns.heatmap(plot_data, cmap='YlOrRd', cbar_kws={'label': 'Pathway Complete'},
                ax=ax, yticklabels=False)
    sp_short = sp.split('--')[0].replace('s__', '')
    n_eco = ecotype_col.nunique()
    ax.set_title(f'{sp_short} ({len(plot_data)} genomes, {n_eco} ecotypes, {len(var_cols)} variable pathways)')
    ax.set_xlabel('GapMind Pathway')
    plt.tight_layout()
    safe_name = sp_short.replace(' ', '_').replace('/', '_')
    plt.savefig(os.path.join(FIG_DIR, 'ecotype_heatmaps', f'{safe_name}.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print(f"    {sp_short}: {n_eco} ecotypes, {len(plot_data)} genomes")

# --- 6. Save ---
print("\n[6] Saving results...")
ecotype_df.to_csv(os.path.join(DATA_DIR, 'metabolic_ecotypes.csv'), index=False)
print(f"  metabolic_ecotypes.csv: {len(ecotype_df):,} genome assignments")

ecotype_summary.to_csv(os.path.join(DATA_DIR, 'ecotype_summary.csv'), index=False)
print(f"  ecotype_summary.csv: {len(ecotype_summary):,} species")

print(f"\n  Median ecotypes per species: {ecotype_summary['n_ecotypes'].median():.0f}")
print(f"  Max ecotypes: {ecotype_summary['n_ecotypes'].max()}")

print("\n" + "=" * 60)
print("NB04 COMPLETE")
print("=" * 60)

#!/usr/bin/env python3
"""NB03 runner: Tier 2 — Pan-Bacterial Pathway Conservation. Runs locally."""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from numpy.linalg import lstsq
import os
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
FIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'figures')
os.makedirs(FIG_DIR, exist_ok=True)

plt.rcParams.update({'figure.figsize': (12, 8), 'figure.dpi': 150, 'font.size': 11})

print("=" * 60)
print("NB03: Tier 2 — Pan-Bacterial Pathway Conservation")
print("=" * 60)

# --- 1. Load Data ---
print("\n[1] Loading data...")
species_pw = pd.read_csv(os.path.join(DATA_DIR, 'species_pathway_summary.csv'))
species_pw['frac_complete'] = pd.to_numeric(species_pw['frac_complete'], errors='coerce')
species_pw['n_genomes'] = pd.to_numeric(species_pw['n_genomes'], errors='coerce')
print(f"  Species pathway summary: {len(species_pw):,} rows, {species_pw['clade_name'].nunique():,} species, {species_pw['pathway'].nunique()} pathways")

pangenome = pd.read_csv(os.path.join(DATA_DIR, 'pangenome_stats.csv'))
for col in ['no_genomes', 'no_gene_clusters', 'no_core', 'no_aux_genome', 'no_singleton_gene_clusters']:
    if col in pangenome.columns:
        pangenome[col] = pd.to_numeric(pangenome[col], errors='coerce')
print(f"  Pangenome stats: {len(pangenome):,} species")

# --- 2. Species-Level Metrics ---
print("\n[2] Computing species-level metabolic capability metrics...")
species_metrics = species_pw.groupby('clade_name').agg(
    n_pathways=('pathway', 'count'),
    n_genomes=('n_genomes', 'first'),
    n_complete_majority=('frac_complete', lambda x: (x >= 0.5).sum()),
    n_universal=('frac_complete', lambda x: (x >= 0.9).sum()),
    n_variable=('frac_complete', lambda x: ((x >= 0.1) & (x < 0.9)).sum()),
    n_absent=('frac_complete', lambda x: (x < 0.1).sum()),
    mean_frac_complete=('frac_complete', 'mean'),
    pathway_diversity=('frac_complete', 'std'),
).reset_index()
print(f"  Species with metrics: {len(species_metrics):,}")
print(f"\n  Metric distributions:")
print(species_metrics[['n_complete_majority', 'n_universal', 'n_variable', 'n_absent']].describe().to_string())

# --- 3. Merge with Pangenome ---
print("\n[3] Merging with pangenome openness...")
merged = species_metrics.merge(pangenome, left_on='clade_name', right_on='gtdb_species_clade_id', how='inner')
merged['openness'] = merged['no_aux_genome'] / merged['no_gene_clusters']
merged_filtered = merged[merged['n_genomes'] >= 10].copy()
print(f"  Merged species: {len(merged):,}")
print(f"  Species with >=10 genomes: {len(merged_filtered):,}")

# --- 4. H1b Test ---
print("\n[4] Testing H1b: variable pathways vs pangenome openness...")
rho, p = stats.spearmanr(merged_filtered['n_variable'], merged_filtered['openness'])
print(f"  Spearman(n_variable, openness): rho={rho:.3f}, p={p:.2e}")

rho2, p2 = stats.spearmanr(merged_filtered['n_complete_majority'], merged_filtered['openness'])
print(f"  Spearman(n_complete, openness): rho={rho2:.3f}, p={p2:.2e}")

rho3, p3 = stats.spearmanr(merged_filtered['pathway_diversity'], merged_filtered['openness'])
print(f"  Spearman(diversity, openness): rho={rho3:.3f}, p={p3:.2e}")

# Confound checks
rho_ng, p_ng = stats.spearmanr(merged_filtered['n_variable'], merged_filtered['n_genomes'])
print(f"\n  Confound: n_variable vs n_genomes: rho={rho_ng:.3f}")

def partial_spearman(x, y, z):
    from scipy.stats import spearmanr, rankdata
    rx, ry, rz = rankdata(x), rankdata(y), rankdata(z)
    A = np.column_stack([rz, np.ones(len(rz))])
    bx = lstsq(A, rx, rcond=None)[0]
    by = lstsq(A, ry, rcond=None)[0]
    return spearmanr(rx - A @ bx, ry - A @ by)

mask = merged_filtered[['n_variable', 'openness', 'n_genomes']].dropna().index
if len(mask) > 30:
    rho_partial, p_partial = partial_spearman(
        merged_filtered.loc[mask, 'n_variable'],
        merged_filtered.loc[mask, 'openness'],
        merged_filtered.loc[mask, 'n_genomes']
    )
    print(f"  Partial Spearman (ctrl n_genomes): rho={rho_partial:.3f}, p={p_partial:.2e}")

# Plot
fig, axes = plt.subplots(1, 3, figsize=(18, 6))
for ax, (x_col, label, r, pv) in zip(axes, [
    ('n_variable', 'Variable Pathways (10-90% complete)', rho, p),
    ('n_complete_majority', 'Complete Pathways (>50%)', rho2, p2),
    ('pathway_diversity', 'Pathway Completeness Std Dev', rho3, p3),
]):
    ax.scatter(merged_filtered[x_col], merged_filtered['openness'], alpha=0.1, s=5)
    ax.set_xlabel(label)
    ax.set_ylabel('Pangenome Openness (frac accessory)')
    ax.set_title(f'rho={r:.3f}, p={pv:.1e}')
plt.suptitle('Metabolic Capability vs Pangenome Openness\n(Context: pangenome_openness found null for env/phylo)', fontsize=14)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'pathway_conservation_vs_openness.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: pathway_conservation_vs_openness.png")

# --- 4b. Phylogenetic stratification (genus-level) ---
print("\n[4b] Phylogenetic stratification by GTDB genus...")
# Extract genus from GTDB species clade name (format: s__Genus_species--accession)
merged_filtered['genus'] = merged_filtered['clade_name'].str.extract(r's__(\w+?)_')[0]

# Filter to genera with enough species for meaningful correlation
genus_counts = merged_filtered['genus'].value_counts()
large_genera = genus_counts[genus_counts >= 20].index.tolist()
print(f"  Genera with >=20 species: {len(large_genera)}")

n_positive = 0
n_tested = 0
print("  Within-genus correlations (n_variable vs openness):")
for gname in sorted(large_genera):
    gdf = merged_filtered[merged_filtered['genus'] == gname]
    r_g, p_g = stats.spearmanr(gdf['n_variable'], gdf['openness'])
    sig = '*' if p_g < 0.05 else ''
    print(f"    {gname:30s}: rho={r_g:.3f}, p={p_g:.2e}, n={len(gdf)} {sig}")
    n_tested += 1
    if r_g > 0 and p_g < 0.05:
        n_positive += 1

print(f"\n  Signal holds in {n_positive} of {n_tested} genera tested (p<0.05, positive rho)")

# Plot top 6 genera by species count
top_genera = genus_counts.head(6).index.tolist()
fig, axes = plt.subplots(2, 3, figsize=(18, 10))
for ax, gname in zip(axes.flat, top_genera):
    gdf = merged_filtered[merged_filtered['genus'] == gname]
    r_g, p_g = stats.spearmanr(gdf['n_variable'], gdf['openness'])
    ax.scatter(gdf['n_variable'], gdf['openness'], alpha=0.3, s=10)
    ax.set_title(f'{gname} (n={len(gdf)}, rho={r_g:.2f}, p={p_g:.1e})')
    ax.set_xlabel('Variable Pathways')
    ax.set_ylabel('Openness')
plt.suptitle('Within-Genus Correlations (GTDB genus-level phylogenetic control)', fontsize=14)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'pathway_conservation_by_genus.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: pathway_conservation_by_genus.png")

# --- 5. Core vs All ---
print("\n[5] Core vs all-genes pathway completeness...")
gapmind_all = pd.read_csv(os.path.join(DATA_DIR, 'gapmind_genome_pathway_status.csv'),
                          usecols=['clade_name', 'pathway', 'is_complete'])
gapmind_core = pd.read_csv(os.path.join(DATA_DIR, 'gapmind_core_pathway_status.csv'),
                           usecols=['clade_name', 'pathway', 'is_complete_core'])

sp_all = gapmind_all.groupby(['clade_name', 'pathway']).agg(
    frac_complete_all=('is_complete', 'mean')
).reset_index()

sp_core = gapmind_core.groupby(['clade_name', 'pathway']).agg(
    frac_complete_core=('is_complete_core', 'mean')
).reset_index()

core_vs_all = sp_all.merge(sp_core, on=['clade_name', 'pathway'], how='inner')
core_vs_all['gap'] = core_vs_all['frac_complete_all'] - core_vs_all['frac_complete_core']
print(f"  Species x pathway pairs: {len(core_vs_all):,}")

accessory_dependent = core_vs_all[core_vs_all['gap'] > 0.1]
print(f"  Accessory-dependent (gap>0.1): {len(accessory_dependent):,}")
print(f"\n  Top pathways by accessory dependence:")
top_pw = accessory_dependent.groupby('pathway')['gap'].mean().sort_values(ascending=False).head(15)
print(top_pw.to_string())

# Plot
aa_pathways = ['arg', 'asn', 'cys', 'gln', 'gly', 'his', 'ile', 'leu', 'lys',
               'met', 'phe', 'pro', 'ser', 'thr', 'trp', 'tyr', 'val', 'chorismate']
aa_data = core_vs_all[core_vs_all['pathway'].isin(aa_pathways)]
aa_summary = aa_data.groupby('pathway').agg(
    mean_all=('frac_complete_all', 'mean'),
    mean_core=('frac_complete_core', 'mean'),
    mean_gap=('gap', 'mean'),
).sort_values('mean_gap', ascending=False)

fig, ax = plt.subplots(figsize=(12, 6))
x = range(len(aa_summary))
ax.bar(x, aa_summary['mean_all'], label='All genes', alpha=0.7, color='steelblue')
ax.bar(x, aa_summary['mean_core'], label='Core genes only', alpha=0.7, color='coral')
ax.set_xticks(x)
ax.set_xticklabels(aa_summary.index, rotation=45, ha='right')
ax.set_ylabel('Mean Fraction Complete Across Species')
ax.set_title('AA Pathway Completeness: Core vs All Genes (gap = accessory dependence)')
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'core_vs_all_pathway_completeness.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: core_vs_all_pathway_completeness.png")

# --- 6. Save Results ---
print("\n[6] Saving results...")
merged_filtered.to_csv(os.path.join(DATA_DIR, 'species_pathway_metrics.csv'), index=False)
print(f"  Saved: species_pathway_metrics.csv ({len(merged_filtered):,} rows)")

core_vs_all.to_csv(os.path.join(DATA_DIR, 'core_vs_all_pathway_completeness.csv'), index=False)
print(f"  Saved: core_vs_all_pathway_completeness.csv ({len(core_vs_all):,} rows)")

print("\n" + "=" * 60)
print("NB03 COMPLETE")
print("=" * 60)

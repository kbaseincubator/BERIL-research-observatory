#!/usr/bin/env python3
"""Generate all figures for the project (headless, no display)."""
import os, warnings
import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns

warnings.filterwarnings('ignore')

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / 'data'
FIG_DIR = PROJECT_DIR / 'figures'
FIG_DIR.mkdir(exist_ok=True)

plt.rcParams.update({'figure.dpi': 150, 'font.size': 9, 'font.family': 'sans-serif',
                      'axes.linewidth': 0.8})

# Load data
variation = pd.read_csv(DATA_DIR / 'amr_variation_by_species.csv')
prevalence = pd.read_csv(DATA_DIR / 'amr_prevalence_by_gene.csv')
islands = pd.read_csv(DATA_DIR / 'resistance_islands.csv')
phi_summary = pd.read_csv(DATA_DIR / 'phi_summary.csv')
mantel = pd.read_csv(DATA_DIR / 'mantel_results.csv')
ecotypes = pd.read_csv(DATA_DIR / 'ecotype_summary.csv')
temporal = pd.read_csv(DATA_DIR / 'temporal_amr_trends.csv')
summary = pd.read_csv(DATA_DIR / 'integrated_summary.csv')

print("Generating figures...")

# ── Figure: NB02 Variation Landscape ──
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

ax = axes[0, 0]
cross = pd.crosstab(prevalence['conservation_class'], prevalence['prevalence_class'], normalize='index')
if all(c in cross.columns for c in ['fixed', 'variable', 'rare']):
    cross = cross[['fixed', 'variable', 'rare']]
cross.plot(kind='bar', stacked=True, ax=ax, color=['#2ecc71', '#f39c12', '#e74c3c'])
ax.set_xlabel('Atlas Conservation Class')
ax.set_ylabel('Fraction of Genes')
ax.set_title('A. Within-Species Prevalence by Atlas Class')
ax.legend(title='Within-species', fontsize=7)
ax.set_xticklabels(ax.get_xticklabels(), rotation=0)

ax = axes[0, 1]
ax.scatter(variation['openness'], variation['variability_index'], alpha=0.2, s=8, c='steelblue')
r, p = stats.spearmanr(variation['openness'].dropna(),
                        variation.loc[variation['openness'].notna(), 'variability_index'])
ax.set_xlabel('Pangenome Openness')
ax.set_ylabel('AMR Variability Index')
ax.set_title(f'B. Variability vs Openness (rho={r:.2f})')

ax = axes[1, 0]
top_phyla = variation['phylum'].value_counts().head(8).index
phylum_data = variation[variation['phylum'].isin(top_phyla)]
order = phylum_data.groupby('phylum')['mean_jaccard'].median().sort_values().index
sns.boxplot(data=phylum_data, x='phylum', y='mean_jaccard', order=order, ax=ax, fliersize=2)
ax.set_xticklabels([p.replace('p__', '') for p in order], rotation=45, ha='right', fontsize=7)
ax.set_xlabel('')
ax.set_ylabel('Mean Pairwise Jaccard Distance')
ax.set_title('C. AMR Diversity by Phylum')

ax = axes[1, 1]
top_mechs = prevalence['mechanism'].value_counts().head(6).index
mech_data = prevalence[prevalence['mechanism'].isin(top_mechs)]
mech_order = mech_data.groupby('mechanism')['prevalence'].median().sort_values().index
sns.violinplot(data=mech_data, x='mechanism', y='prevalence', order=mech_order,
               ax=ax, cut=0, inner='quartile', linewidth=0.8, scale='width')
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right', fontsize=7)
ax.set_xlabel('')
ax.set_ylabel('Within-Species Prevalence')
ax.set_title('D. Prevalence by AMR Mechanism')

plt.tight_layout()
plt.savefig(FIG_DIR / 'nb02_variation_landscape.png', dpi=150, bbox_inches='tight')
plt.close()
print("  nb02_variation_landscape.png")

# ── Figure: NB03 Co-occurrence ──
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

ax = axes[0]
ax.hist(islands['size'], bins=range(3, min(islands['size'].max()+2, 25)),
        edgecolor='black', alpha=0.7, color='coral')
ax.set_xlabel('Island Size (genes)')
ax.set_ylabel('Count')
ax.set_title('A. Resistance Island Sizes')

ax = axes[1]
has_islands = summary.dropna(subset=['n_islands'])
ax.scatter(has_islands['variability_index'], has_islands['n_islands'], alpha=0.3, s=10, c='coral')
ax.set_xlabel('Variability Index')
ax.set_ylabel('Number of Islands')
ax.set_title('B. Islands vs Variability')

ax = axes[2]
mech_counts = islands['mechanisms'].str.split('|').explode().value_counts().head(8)
mech_counts.plot(kind='barh', ax=ax, color='coral', edgecolor='black')
ax.set_xlabel('Number of Islands')
ax.set_title('C. Island Mechanism Composition')

plt.tight_layout()
plt.savefig(FIG_DIR / 'nb03_cooccurrence.png', dpi=150, bbox_inches='tight')
plt.close()
print("  nb03_cooccurrence.png")

# ── Figure: NB04 Phylogenetic Signal ──
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

ax = axes[0]
ax.hist(mantel['mantel_r_all'].dropna(), bins=40, edgecolor='black', alpha=0.7, color='mediumpurple')
ax.axvline(0, color='red', ls='--', linewidth=0.8)
med = mantel['mantel_r_all'].median()
ax.axvline(med, color='darkblue', ls='-', linewidth=1, label=f'median={med:.2f}')
ax.legend(fontsize=7)
ax.set_xlabel('Mantel r (ANI vs AMR distance)')
ax.set_ylabel('Number of Species')
ax.set_title('A. Phylogenetic Signal Distribution')

ax = axes[1]
both = mantel.dropna(subset=['mantel_r_core', 'mantel_r_noncore'])
if len(both) > 0:
    ax.scatter(both['mantel_r_core'], both['mantel_r_noncore'], alpha=0.3, s=10, c='mediumpurple')
    lim = max(both[['mantel_r_core', 'mantel_r_noncore']].max().max(), 0.5)
    ax.plot([-0.3, lim], [-0.3, lim], 'k--', alpha=0.3, linewidth=0.8)
ax.set_xlabel('Mantel r (Core AMR)')
ax.set_ylabel('Mantel r (Non-core AMR)')
ax.set_title('B. Intrinsic vs Acquired Signal')

ax = axes[2]
valid = mantel.dropna(subset=['mantel_r_all', 'mantel_fdr_all'])
colors = ['red' if fdr < 0.05 else 'grey' for fdr in valid['mantel_fdr_all']]
ax.scatter(valid['mantel_r_all'], -np.log10(valid['mantel_fdr_all'].clip(1e-300)),
           c=colors, alpha=0.3, s=10)
ax.axhline(-np.log10(0.05), color='blue', ls='--', label='FDR=0.05')
ax.set_xlabel('Mantel r')
ax.set_ylabel('-log10(FDR)')
ax.set_title('C. Volcano: Phylogenetic Signal')
ax.legend(fontsize=7)

plt.tight_layout()
plt.savefig(FIG_DIR / 'nb04_phylogenetic_signal.png', dpi=150, bbox_inches='tight')
plt.close()
print("  nb04_phylogenetic_signal.png")

print(f"\nAll figures saved to {FIG_DIR}/")

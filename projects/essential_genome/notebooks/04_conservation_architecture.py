#!/usr/bin/env python3
"""
NB04: Connect essential gene families to pangenome conservation.

For organisms with pangenome links, test whether universally essential
families are always core and what predicts variable essentiality.

Runs locally using cached data.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from pathlib import Path

# ============================================================================
# Setup
# ============================================================================
PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / 'data'
FIG_DIR = PROJECT_DIR / 'figures'
CV_DIR = PROJECT_DIR.parent / 'conservation_vs_fitness' / 'data'

print("Loading data...")
essential = pd.read_csv(DATA_DIR / 'all_essential_genes.tsv', sep='\t', low_memory=False)
essential['is_essential'] = essential['is_essential'].astype(str).str.strip().str.lower() == 'true'
essential['locusId'] = essential['locusId'].astype(str)

og_df = pd.read_csv(DATA_DIR / 'all_ortholog_groups.csv')
og_df['locusId'] = og_df['locusId'].astype(str)

families = pd.read_csv(DATA_DIR / 'essential_families.tsv', sep='\t')

# Load pangenome link table
link = pd.read_csv(CV_DIR / 'fb_pangenome_link.tsv', sep='\t')
link['locusId'] = link['locusId'].astype(str)
print(f"Link table: {len(link):,} gene-cluster links, "
      f"{link['orgId'].nunique()} organisms")

# Load pangenome metadata
pg_meta = pd.read_csv(CV_DIR / 'pangenome_metadata.tsv', sep='\t')

# ============================================================================
# 1. Map essential genes to conservation status
# ============================================================================
print("\n=== MAPPING ESSENTIALS TO CONSERVATION ===")

# Merge essential status with link table
ess_conservation = essential.merge(
    link[['orgId', 'locusId', 'is_core', 'is_auxiliary', 'is_singleton']],
    on=['orgId', 'locusId'],
    how='inner'
)

print(f"Essential genes with conservation status: {len(ess_conservation):,}")
print(f"  Organisms: {ess_conservation['orgId'].nunique()}")

# Core fraction by essentiality
ess_core = ess_conservation[ess_conservation['is_essential']]
noness_core = ess_conservation[~ess_conservation['is_essential']]

ess_pct_core = ess_core['is_core'].mean() * 100
noness_pct_core = noness_core['is_core'].mean() * 100
print(f"\nEssential genes: {ess_pct_core:.1f}% core (n={len(ess_core):,})")
print(f"Non-essential genes: {noness_pct_core:.1f}% core (n={len(noness_core):,})")

# ============================================================================
# 2. Conservation by essentiality class
# ============================================================================
print("\n=== CONSERVATION BY ESSENTIALITY CLASS ===")

# Add OG and essentiality class to conservation data
ess_conservation = ess_conservation.merge(
    og_df[['orgId', 'locusId', 'OG_id']], on=['orgId', 'locusId'], how='left'
)
ess_conservation = ess_conservation.merge(
    families[['OG_id', 'essentiality_class']], on='OG_id', how='left'
)

# For genes without OG membership, classify based on essentiality
ess_conservation.loc[
    ess_conservation['essentiality_class'].isna() & ess_conservation['is_essential'],
    'essentiality_class'
] = 'orphan_essential'
ess_conservation.loc[
    ess_conservation['essentiality_class'].isna() & ~ess_conservation['is_essential'],
    'essentiality_class'
] = 'no_og'

print(f"\nCore fraction by essentiality class:")
class_conservation = []
for cls in ['universally_essential', 'variably_essential', 'never_essential',
            'orphan_essential', 'no_og']:
    subset = ess_conservation[ess_conservation['essentiality_class'] == cls]
    if len(subset) == 0:
        continue
    pct_core = subset['is_core'].mean() * 100
    n = len(subset)
    n_ess = subset['is_essential'].sum()
    print(f"  {cls}: {pct_core:.1f}% core (n={n:,}, {n_ess:,} essential)")
    class_conservation.append({
        'class': cls, 'pct_core': pct_core, 'n': n, 'n_essential': n_ess
    })

# ============================================================================
# 3. Per-family conservation analysis
# ============================================================================
print("\n=== PER-FAMILY CONSERVATION ===")

# For each family with pangenome links, calculate % core
family_conservation = []
for og_id, group in ess_conservation[ess_conservation['OG_id'].notna()].groupby('OG_id'):
    fam_info = families[families['OG_id'] == og_id]
    if len(fam_info) == 0:
        continue
    fam = fam_info.iloc[0]

    pct_core = group['is_core'].mean() * 100
    n_genes = len(group)
    n_orgs = group['orgId'].nunique()

    family_conservation.append({
        'OG_id': og_id,
        'essentiality_class': fam['essentiality_class'],
        'pct_core': pct_core,
        'n_genes': n_genes,
        'n_organisms': n_orgs,
        'n_essential_organisms': fam['n_essential_organisms'],
        'frac_essential': fam['frac_essential'],
        'rep_gene': fam['rep_gene'],
        'rep_desc': fam['rep_desc'],
    })

fam_cons = pd.DataFrame(family_conservation)
fam_cons.to_csv(DATA_DIR / 'family_conservation.tsv', sep='\t', index=False)
print(f"Families with conservation data: {len(fam_cons):,}")

# Summary
for cls in ['universally_essential', 'variably_essential', 'never_essential']:
    subset = fam_cons[fam_cons['essentiality_class'] == cls]
    if len(subset) == 0:
        continue
    print(f"  {cls}: median {subset['pct_core'].median():.1f}% core "
          f"(n={len(subset):,} families)")

# Are universally essential families always core?
univ_fams = fam_cons[fam_cons['essentiality_class'] == 'universally_essential']
n_all_core = (univ_fams['pct_core'] == 100).sum()
n_mostly_core = (univ_fams['pct_core'] >= 90).sum()
print(f"\nUniversally essential families:")
print(f"  100% core: {n_all_core} / {len(univ_fams)} ({n_all_core/len(univ_fams)*100:.1f}%)")
print(f"  ≥90% core: {n_mostly_core} / {len(univ_fams)} ({n_mostly_core/len(univ_fams)*100:.1f}%)")

# ============================================================================
# 4. What predicts variable essentiality?
# ============================================================================
print("\n=== PREDICTORS OF VARIABLE ESSENTIALITY ===")

# For variably essential families, compare organisms where essential vs not
var_fams = families[families['essentiality_class'] == 'variably_essential'].copy()

# Merge with pangenome metadata to test if clade size predicts essentiality
org_mapping = pd.read_csv(CV_DIR / 'organism_mapping.tsv', sep='\t')
org_meta = org_mapping.merge(pg_meta, on='gtdb_species_clade_id', how='inner')

# For each organism, get summary essentiality stats
org_ess_stats = essential.groupby('orgId').agg(
    n_genes=('locusId', 'count'),
    n_essential=('is_essential', 'sum'),
).reset_index()
org_ess_stats['pct_essential'] = org_ess_stats['n_essential'] / org_ess_stats['n_genes'] * 100

# Merge with pangenome info
org_ess_stats = org_ess_stats.merge(
    org_meta[['orgId', 'no_genomes', 'no_core', 'no_gene_clusters',
              'mean_intra_species_ANI']],
    on='orgId', how='left'
)
org_ess_stats['core_fraction'] = org_ess_stats['no_core'] / org_ess_stats['no_gene_clusters']
org_ess_stats['openness'] = 1 - org_ess_stats['core_fraction']

# Correlations
has_pg = org_ess_stats.dropna(subset=['no_genomes'])
if len(has_pg) > 5:
    rho_genomes, p_genomes = stats.spearmanr(has_pg['no_genomes'], has_pg['pct_essential'])
    rho_openness, p_openness = stats.spearmanr(has_pg['openness'], has_pg['pct_essential'])
    print(f"Clade size vs % essential: rho={rho_genomes:.3f}, p={p_genomes:.3e}")
    print(f"Openness vs % essential: rho={rho_openness:.3f}, p={p_openness:.3e}")

# ============================================================================
# 5. Visualizations
# ============================================================================
print("\n=== GENERATING FIGURES ===")

fig, axes = plt.subplots(2, 2, figsize=(14, 11))

# Panel A: Core fraction by essentiality class
ax = axes[0, 0]
plot_classes = ['universally_essential', 'variably_essential', 'never_essential', 'orphan_essential']
plot_labels = ['Universally\nessential', 'Variably\nessential', 'Never\nessential', 'Orphan\nessential']
colors = ['#D32F2F', '#FF9800', '#4CAF50', '#9E9E9E']
core_pcts = []
ns = []
for cls in plot_classes:
    s = ess_conservation[ess_conservation['essentiality_class'] == cls]
    core_pcts.append(s['is_core'].mean() * 100 if len(s) > 0 else 0)
    ns.append(len(s))
bars = ax.bar(plot_labels, core_pcts, color=colors, edgecolor='black', linewidth=0.5)
for bar, n in zip(bars, ns):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
            f'n={n:,}', ha='center', va='bottom', fontsize=8)
ax.set_ylabel('% core genome')
ax.set_title('A. Core Genome Fraction by Essentiality Class')
ax.set_ylim(0, 105)
ax.axhline(noness_pct_core, color='gray', linestyle='--', alpha=0.5,
           label=f'Non-essential baseline ({noness_pct_core:.1f}%)')
ax.legend(fontsize=8)

# Panel B: Family-level core fraction distribution
ax = axes[0, 1]
for cls, color, label in zip(
    ['universally_essential', 'variably_essential', 'never_essential'],
    ['#D32F2F', '#FF9800', '#4CAF50'],
    ['Universally essential', 'Variably essential', 'Never essential']
):
    subset = fam_cons[fam_cons['essentiality_class'] == cls]
    if len(subset) > 0:
        ax.hist(subset['pct_core'], bins=20, alpha=0.6, color=color,
                label=f'{label} (n={len(subset):,})', edgecolor='black', linewidth=0.3)
ax.set_xlabel('% core genes in family')
ax.set_ylabel('Number of families')
ax.set_title('B. Family-Level Core Fraction')
ax.legend(fontsize=8)

# Panel C: Essentiality fraction vs core fraction (variably essential)
ax = axes[1, 0]
var_with_core = fam_cons[fam_cons['essentiality_class'] == 'variably_essential']
if len(var_with_core) > 0:
    ax.scatter(var_with_core['frac_essential'], var_with_core['pct_core'],
               alpha=0.3, s=10, color='#FF9800')
    rho, p = stats.spearmanr(var_with_core['frac_essential'], var_with_core['pct_core'])
    print(f"Penetrance vs conservation: rho={rho:.4f}, p={p:.2e}")
    high_pen = var_with_core[var_with_core['frac_essential'] > 0.8]['pct_core'].median()
    low_pen = var_with_core[var_with_core['frac_essential'] < 0.2]['pct_core'].median()
    print(f"  >80% penetrance: {high_pen:.1f}% core; <20% penetrance: {low_pen:.1f}% core")
    ax.set_xlabel('Fraction of organisms where essential')
    ax.set_ylabel('% core genes in family')
    ax.set_title(f'C. Essentiality Penetrance vs Conservation\n'
                 f'(rho={rho:.3f}, p={p:.2e})')

# Panel D: Clade size vs % essential
ax = axes[1, 1]
if len(has_pg) > 0:
    ax.scatter(has_pg['no_genomes'], has_pg['pct_essential'],
               alpha=0.6, s=30, color='#2196F3', edgecolor='black', linewidth=0.3)
    for _, r in has_pg.iterrows():
        if r['no_genomes'] > 1000 or r['pct_essential'] > 25:
            ax.annotate(r['orgId'], (r['no_genomes'], r['pct_essential']),
                        fontsize=6, alpha=0.7)
    ax.set_xlabel('Number of genomes in species clade')
    ax.set_ylabel('% genes called essential')
    ax.set_title(f'D. Clade Size vs Essentiality Rate\n'
                 f'(rho={rho_genomes:.3f}, p={p_genomes:.2e})')
    ax.set_xscale('log')

plt.tight_layout()
plt.savefig(FIG_DIR / 'conservation_architecture.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"Saved: figures/conservation_architecture.png")

# ============================================================================
# Summary
# ============================================================================
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"Essential genes: {ess_pct_core:.1f}% core vs non-essential: {noness_pct_core:.1f}%")
print(f"Universally essential families: {n_all_core}/{len(univ_fams)} are 100% core, "
      f"{n_mostly_core}/{len(univ_fams)} are ≥90% core")
print(f"Conservation by class:")
for row in class_conservation:
    print(f"  {row['class']}: {row['pct_core']:.1f}% core")

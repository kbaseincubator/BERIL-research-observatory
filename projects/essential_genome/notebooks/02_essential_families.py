#!/usr/bin/env python3
"""
NB02: Build and classify essential gene families.

Groups essential genes into ortholog families, classifies them as universally/
variably/never essential, and performs functional characterization.

Runs locally using cached data from extract_data.py.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# ============================================================================
# Setup
# ============================================================================
PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / 'data'
FIG_DIR = PROJECT_DIR / 'figures'
FIG_DIR.mkdir(parents=True, exist_ok=True)

# Load data
print("Loading data...")
essential = pd.read_csv(DATA_DIR / 'all_essential_genes.tsv', sep='\t')
og_df = pd.read_csv(DATA_DIR / 'all_ortholog_groups.csv')
seed_ann = pd.read_csv(DATA_DIR / 'all_seed_annotations.tsv', sep='\t')

# Load SEED hierarchy from conservation_vs_fitness
seed_hier_path = PROJECT_DIR.parent / 'conservation_vs_fitness' / 'data' / 'seed_hierarchy.tsv'
if seed_hier_path.exists():
    seed_hier = pd.read_csv(seed_hier_path, sep='\t')
else:
    seed_hier = None

# Ensure boolean types
essential['is_essential'] = essential['is_essential'].astype(str).str.strip().str.lower() == 'true'

print(f"Essential genes: {len(essential):,} ({essential['is_essential'].sum():,} essential)")
print(f"Ortholog groups: {og_df['OG_id'].nunique():,}")
print(f"SEED annotations: {len(seed_ann):,}")

# ============================================================================
# 1. Merge essential status with ortholog groups
# ============================================================================
print("\n=== MERGING ESSENTIALITY WITH ORTHOLOG GROUPS ===")

# Ensure locusId types match
essential['locusId'] = essential['locusId'].astype(str)
og_df['locusId'] = og_df['locusId'].astype(str)

# Merge
merged = og_df.merge(
    essential[['orgId', 'locusId', 'is_essential', 'gene', 'desc', 'gene_length']],
    on=['orgId', 'locusId'],
    how='left'
)

print(f"Merged: {len(merged):,} gene-OG assignments")
print(f"  With essential status: {merged['is_essential'].notna().sum():,}")
print(f"  Missing essential status: {merged['is_essential'].isna().sum():,}")

# Genes NOT in any OG (no orthologs in other organisms)
# Use merge instead of row-wise apply (performance pitfall)
og_keys = og_df[['orgId', 'locusId']].drop_duplicates()
og_keys['in_og'] = True
essential = essential.merge(og_keys, on=['orgId', 'locusId'], how='left')
essential['in_og'] = essential['in_og'].fillna(False)
n_in_og = essential['in_og'].sum()
n_total = len(essential)
print(f"\nGenes in ortholog groups: {n_in_og:,} / {n_total:,} ({n_in_og/n_total*100:.1f}%)")

ess_in_og = essential[essential['is_essential'] & essential['in_og']]
ess_not_in_og = essential[essential['is_essential'] & ~essential['in_og']]
print(f"Essential genes in OGs: {len(ess_in_og):,} / {essential['is_essential'].sum():,}")
print(f"Essential genes without orthologs (orphans): {len(ess_not_in_og):,}")

# ============================================================================
# 2. Classify ortholog families by essentiality
# ============================================================================
print("\n=== CLASSIFYING ORTHOLOG FAMILIES ===")

family_stats = []
for og_id, group in merged.groupby('OG_id'):
    # Only consider genes with essential status data
    with_status = group[group['is_essential'].notna()].copy()
    if len(with_status) == 0:
        continue

    # Ensure boolean
    with_status['is_essential'] = with_status['is_essential'].astype(bool)

    n_organisms = with_status['orgId'].nunique()
    n_essential = with_status[with_status['is_essential'] == True]['orgId'].nunique()
    n_nonessential = with_status[with_status['is_essential'] == False]['orgId'].nunique()
    n_genes = len(with_status)
    n_ess_genes = (with_status['is_essential'] == True).sum()

    # Get representative gene description
    descs = with_status['desc'].dropna().unique()
    non_hyp_descs = [d for d in descs if 'hypothetical' not in str(d).lower()]
    rep_desc = non_hyp_descs[0] if non_hyp_descs else (descs[0] if len(descs) > 0 else 'unknown')

    # Get representative gene name
    gene_names = with_status['gene'].dropna().unique()
    gene_names = [g for g in gene_names if g and str(g) != 'nan']
    rep_gene = gene_names[0] if gene_names else ''

    # Classify
    if n_essential == n_organisms:
        ess_class = 'universally_essential'
    elif n_essential > 0:
        ess_class = 'variably_essential'
    else:
        ess_class = 'never_essential'

    # Fraction essential
    frac_essential = n_essential / n_organisms if n_organisms > 0 else 0

    # List organisms where essential
    ess_orgs = sorted(with_status[with_status['is_essential'] == True]['orgId'].unique())
    noness_orgs = sorted(with_status[with_status['is_essential'] == False]['orgId'].unique())

    family_stats.append({
        'OG_id': og_id,
        'n_organisms': n_organisms,
        'n_essential_organisms': n_essential,
        'n_nonessential_organisms': n_nonessential,
        'n_genes': n_genes,
        'n_essential_genes': int(n_ess_genes),
        'frac_essential': frac_essential,
        'essentiality_class': ess_class,
        'rep_gene': rep_gene,
        'rep_desc': rep_desc,
        'essential_organisms': ';'.join(ess_orgs),
        'nonessential_organisms': ';'.join(noness_orgs),
    })

families = pd.DataFrame(family_stats)

# Add copy-number ratio to distinguish single-copy from multi-copy families
families['copy_ratio'] = families['n_genes'] / families['n_organisms']
families['is_single_copy'] = (families['copy_ratio'] <= 1.5) & (families['n_nonessential_organisms'] == 0)

families.to_csv(DATA_DIR / 'essential_families.tsv', sep='\t', index=False)
print(f"Total families classified: {len(families):,}")

# Summary by class
class_counts = families['essentiality_class'].value_counts()
print(f"\nFamily classification:")
for cls, count in class_counts.items():
    pct = count / len(families) * 100
    print(f"  {cls}: {count:,} ({pct:.1f}%)")

# Single-copy vs multi-copy universally essential
univ = families[families['essentiality_class'] == 'universally_essential']
n_sc = univ['is_single_copy'].sum()
n_mc = len(univ) - n_sc
print(f"\nUniversally essential families: {len(univ):,}")
print(f"  Single-copy (strict, ratio≤1.5 & no non-ess members): {n_sc:,}")
print(f"  Multi-copy or with paralogs: {n_mc:,}")

# By organism count
print(f"\nFamilies spanning all 48 organisms: "
      f"{(families['n_organisms'] == 48).sum()}")
print(f"Universally essential + all 48 organisms: "
      f"{((families['essentiality_class'] == 'universally_essential') & (families['n_organisms'] == 48)).sum()}")

# ============================================================================
# 3. Functional characterization
# ============================================================================
print("\n=== FUNCTIONAL CHARACTERIZATION ===")

# Merge SEED annotations with essential genes
seed_ann['locusId'] = seed_ann['locusId'].astype(str)
essential_with_seed = essential.merge(
    seed_ann, on=['orgId', 'locusId'], how='left'
)

# Add SEED hierarchy
if seed_hier is not None:
    essential_with_seed = essential_with_seed.merge(
        seed_hier[['seed_desc', 'toplevel']].drop_duplicates(),
        on='seed_desc', how='left'
    )

# Characterize by essentiality class
# First, tag each gene with its family's essentiality class
gene_family_class = merged.merge(
    families[['OG_id', 'essentiality_class']],
    on='OG_id', how='left'
)

# For genes not in any OG, they are "orphan_essential" or "orphan_nonessential"
print("\nFunctional profile by essentiality class:")

# Hypothetical fraction
for cls in ['universally_essential', 'variably_essential', 'never_essential']:
    subset = gene_family_class[gene_family_class['essentiality_class'] == cls]
    if len(subset) == 0:
        continue
    n_hyp = subset['desc'].str.contains('hypothetical', case=False, na=False).sum()
    pct_hyp = n_hyp / len(subset) * 100
    print(f"  {cls}: {len(subset):,} genes, {pct_hyp:.1f}% hypothetical")

# Orphan essential genes
orphan_ess = essential[essential['is_essential'] & ~essential['in_og']]
n_hyp_orphan = orphan_ess['desc'].str.contains('hypothetical', case=False, na=False).sum()
print(f"  orphan_essential (no orthologs): {len(orphan_ess):,} genes, "
      f"{n_hyp_orphan/len(orphan_ess)*100:.1f}% hypothetical")

# ============================================================================
# 4. Top universally essential families
# ============================================================================
print("\n=== TOP UNIVERSALLY ESSENTIAL FAMILIES ===")
univ_ess = families[families['essentiality_class'] == 'universally_essential'].copy()
univ_ess_sorted = univ_ess.sort_values('n_organisms', ascending=False)

print(f"\nTop 30 universally essential families (by organism count):")
print(f"{'OG_id':<12} {'n_orgs':>6} {'gene':<12} {'description':<60}")
print("-" * 92)
for _, row in univ_ess_sorted.head(30).iterrows():
    desc = str(row['rep_desc'])[:58]
    gene = str(row['rep_gene'])[:10] if row['rep_gene'] else ''
    print(f"{row['OG_id']:<12} {row['n_organisms']:>6} {gene:<12} {desc}")

# ============================================================================
# 5. Variably essential: what determines essentiality?
# ============================================================================
print("\n=== VARIABLY ESSENTIAL FAMILIES: PATTERNS ===")
var_ess = families[families['essentiality_class'] == 'variably_essential'].copy()

print(f"\nVariably essential families: {len(var_ess):,}")
print(f"  Spanning 2+ organisms: {(var_ess['n_organisms'] >= 2).sum():,}")
print(f"  Spanning 10+ organisms: {(var_ess['n_organisms'] >= 10).sum():,}")
print(f"  Spanning 20+ organisms: {(var_ess['n_organisms'] >= 20).sum():,}")

# Distribution of frac_essential
print(f"\nFraction of organisms where gene is essential:")
print(f"  Mean: {var_ess['frac_essential'].mean():.3f}")
print(f"  Median: {var_ess['frac_essential'].median():.3f}")
print(f"  >50% essential: {(var_ess['frac_essential'] > 0.5).sum():,}")
print(f"  <10% essential: {(var_ess['frac_essential'] < 0.1).sum():,}")

# ============================================================================
# 6. Visualizations
# ============================================================================
print("\n=== GENERATING FIGURES ===")

fig, axes = plt.subplots(2, 2, figsize=(14, 11))

# Panel A: Family classification
ax = axes[0, 0]
class_order = ['universally_essential', 'variably_essential', 'never_essential']
class_labels = ['Universally\nessential', 'Variably\nessential', 'Never\nessential']
class_colors = ['#D32F2F', '#FF9800', '#4CAF50']
counts = [class_counts.get(c, 0) for c in class_order]
bars = ax.bar(class_labels, counts, color=class_colors, edgecolor='black', linewidth=0.5)
for bar, count in zip(bars, counts):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50,
            f'{count:,}', ha='center', va='bottom', fontsize=10)
ax.set_ylabel('Number of ortholog families')
ax.set_title('A. Essentiality Classification of Ortholog Families')
ax.set_ylim(0, max(counts) * 1.15)

# Panel B: Family size vs essentiality class
ax = axes[0, 1]
for cls, color, label in zip(class_order, class_colors,
                              ['Universally essential', 'Variably essential', 'Never essential']):
    subset = families[families['essentiality_class'] == cls]
    ax.hist(subset['n_organisms'], bins=range(2, 50), alpha=0.6,
            color=color, label=f'{label} (n={len(subset):,})', edgecolor='black', linewidth=0.3)
ax.set_xlabel('Number of organisms in family')
ax.set_ylabel('Number of families')
ax.set_title('B. Family Size Distribution by Essentiality')
ax.legend(fontsize=8)

# Panel C: Fraction essential distribution (variably essential only)
ax = axes[1, 0]
ax.hist(var_ess['frac_essential'], bins=20, color='#FF9800',
        edgecolor='black', linewidth=0.5)
ax.set_xlabel('Fraction of organisms where gene is essential')
ax.set_ylabel('Number of variably essential families')
ax.set_title('C. Essentiality Penetrance (Variably Essential)')
ax.axvline(0.5, color='black', linestyle='--', alpha=0.5, label='50%')
ax.legend()

# Panel D: Hypothetical fraction by class
ax = axes[1, 1]
hyp_data = []
for cls, label in zip(class_order + ['orphan'], class_labels + ['Orphan\nessential']):
    if cls == 'orphan':
        subset = orphan_ess
        n_hyp = subset['desc'].str.contains('hypothetical', case=False, na=False).sum()
    else:
        subset = gene_family_class[gene_family_class['essentiality_class'] == cls]
        n_hyp = subset['desc'].str.contains('hypothetical', case=False, na=False).sum()
    if len(subset) > 0:
        hyp_data.append({'class': label, 'pct_hyp': n_hyp / len(subset) * 100,
                         'n': len(subset)})

hyp_df = pd.DataFrame(hyp_data)
bars = ax.bar(hyp_df['class'], hyp_df['pct_hyp'],
              color=['#D32F2F', '#FF9800', '#4CAF50', '#9E9E9E'],
              edgecolor='black', linewidth=0.5)
for bar, row in zip(bars, hyp_df.itertuples()):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
            f'n={row.n:,}', ha='center', va='bottom', fontsize=8)
ax.set_ylabel('% hypothetical proteins')
ax.set_title('D. Annotation Status by Essentiality Class')
ax.set_ylim(0, hyp_df['pct_hyp'].max() * 1.2)

plt.tight_layout()
plt.savefig(FIG_DIR / 'essential_families_overview.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"Saved: figures/essential_families_overview.png")

# ============================================================================
# Figure 2: Heatmap of top universally essential families
# ============================================================================
# Show essentiality status across organisms for the top 40 universally essential families
top_univ = univ_ess_sorted.head(40)

fig, ax = plt.subplots(figsize=(16, 10))

# Build heatmap matrix: family × organism
all_orgs_sorted = sorted(essential['orgId'].unique())
heatmap_data = np.full((len(top_univ), len(all_orgs_sorted)), np.nan)
family_labels_list = []

for i, (_, fam) in enumerate(top_univ.iterrows()):
    fam_genes = merged[merged['OG_id'] == fam['OG_id']]
    # Use the is_essential already present in merged (from the earlier merge)
    for _, gene in fam_genes.iterrows():
        if gene['orgId'] in all_orgs_sorted:
            j = all_orgs_sorted.index(gene['orgId'])
            ess_val = gene.get('is_essential', None)
            if pd.notna(ess_val):
                heatmap_data[i, j] = 1 if bool(ess_val) else 0

    gene_name = str(fam['rep_gene'])[:8] if fam['rep_gene'] else ''
    desc_short = str(fam['rep_desc'])[:35]
    label = f"{gene_name} - {desc_short}" if gene_name else desc_short
    family_labels_list.append(label)

cmap = plt.cm.colors.ListedColormap(['#4CAF50', '#D32F2F', '#E0E0E0'])
bounds = [-0.5, 0.5, 1.5, 2.5]
norm = plt.cm.colors.BoundaryNorm(bounds, cmap.N)

# Replace NaN with 2 for the colormap
heatmap_display = np.where(np.isnan(heatmap_data), 2, heatmap_data)

im = ax.imshow(heatmap_display, aspect='auto', cmap=cmap, norm=norm, interpolation='none')
ax.set_yticks(range(len(family_labels_list)))
ax.set_yticklabels(family_labels_list, fontsize=7)
ax.set_xticks(range(len(all_orgs_sorted)))
ax.set_xticklabels(all_orgs_sorted, rotation=90, fontsize=6)
ax.set_xlabel('Organism')
ax.set_title(f'Top {len(top_univ)} Universally Essential Gene Families')

# Legend
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor='#D32F2F', label='Essential'),
                   Patch(facecolor='#4CAF50', label='Non-essential'),
                   Patch(facecolor='#E0E0E0', label='Not present')]
ax.legend(handles=legend_elements, loc='lower right', fontsize=8)

plt.tight_layout()
plt.savefig(FIG_DIR / 'essential_families_heatmap.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"Saved: figures/essential_families_heatmap.png")

# ============================================================================
# Summary statistics
# ============================================================================
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"Total genes: {len(essential):,}")
print(f"Essential genes: {essential['is_essential'].sum():,} ({essential['is_essential'].mean()*100:.1f}%)")
print(f"Genes in ortholog groups: {n_in_og:,}")
print(f"Essential genes in OGs: {len(ess_in_og):,}")
print(f"Essential orphans (no orthologs): {len(ess_not_in_og):,}")
print(f"\nOrtholog families: {len(families):,}")
for cls in class_order:
    n = class_counts.get(cls, 0)
    print(f"  {cls}: {n:,}")
print(f"\nUniversally essential spanning all 48 orgs: "
      f"{((families['essentiality_class'] == 'universally_essential') & (families['n_organisms'] == 48)).sum()}")
print(f"\nUniversally essential (single-copy): {univ['is_single_copy'].sum():,}")
print(f"Universally essential (multi-copy/paralog): {len(univ) - univ['is_single_copy'].sum():,}")
print(f"\nVariably essential families: {len(var_ess):,}")
print(f"  Median frac_essential: {var_ess['frac_essential'].median():.3f}")

# Gene length statistics for essentiality
print(f"\nGene length by essentiality:")
ess_len = essential[essential['is_essential']]['gene_length'].median()
noness_len = essential[~essential['is_essential']]['gene_length'].median()
short_ess = (essential['is_essential'] & (essential['gene_length'] < 300)).sum()
print(f"  Essential median length: {ess_len:.0f} bp")
print(f"  Non-essential median length: {noness_len:.0f} bp")
print(f"  Essential genes <300 bp: {short_ess:,} ({short_ess/essential['is_essential'].sum()*100:.1f}%)")

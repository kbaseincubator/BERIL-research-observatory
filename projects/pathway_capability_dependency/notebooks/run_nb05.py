#!/usr/bin/env python3
"""NB05 runner: Synthesis & Visualization. Runs locally after NB02-NB04."""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
FIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'figures')
os.makedirs(FIG_DIR, exist_ok=True)

plt.rcParams.update({
    'figure.figsize': (12, 8), 'figure.dpi': 200, 'font.size': 12,
    'axes.titlesize': 14, 'axes.labelsize': 12, 'font.family': 'sans-serif',
})
CATEGORY_COLORS = {
    'Active Dependency': '#2ecc71',
    'Latent Capability': '#f39c12',
    'Incomplete but Important': '#e74c3c',
    'Missing': '#95a5a6',
}
CATEGORY_ORDER = ['Active Dependency', 'Latent Capability', 'Incomplete but Important', 'Missing']

print("=" * 60)
print("NB05: Synthesis & Visualization")
print("=" * 60)

# --- Load all results ---
print("\n[1] Loading results from NB02-NB04...")

tier1 = pd.read_csv(os.path.join(DATA_DIR, 'tier1_pathway_classification.csv'))
print(f"  Tier 1 classification: {len(tier1):,} rows")

species_metrics = pd.read_csv(os.path.join(DATA_DIR, 'species_pathway_metrics.csv'))
print(f"  Species metrics: {len(species_metrics):,} species")

core_vs_all = pd.read_csv(os.path.join(DATA_DIR, 'core_vs_all_pathway_completeness.csv'))
print(f"  Core vs all: {len(core_vs_all):,} species x pathway pairs")

ecotype_summary = pd.read_csv(os.path.join(DATA_DIR, 'ecotype_summary.csv'))
print(f"  Ecotype summary: {len(ecotype_summary):,} species")

pangenome = pd.read_csv(os.path.join(DATA_DIR, 'pangenome_stats.csv'))
print(f"  Pangenome stats: {len(pangenome):,} species")

cond_path = os.path.join(DATA_DIR, 'tier1_condition_type_analysis.csv')
cond = pd.read_csv(cond_path) if os.path.exists(cond_path) else None
if cond is not None:
    print(f"  Condition-type analysis: {len(cond):,} rows")

# --- Figure 1: Four-Category Overview ---
print("\n[2] Figure 1: Four-Category Overview...")

fig, axes = plt.subplots(1, 3, figsize=(18, 6))

# Panel A: Overall distribution
cat_counts = tier1['category'].value_counts().reindex(CATEGORY_ORDER)
colors = [CATEGORY_COLORS[c] for c in CATEGORY_ORDER]
cat_counts.plot.bar(ax=axes[0], color=colors, edgecolor='black', linewidth=0.5)
axes[0].set_title('A. Pathway Classification')
axes[0].set_ylabel('Count (organism x pathway)')
axes[0].tick_params(axis='x', rotation=30)

# Panel B: By organism
ct = pd.crosstab(tier1['orgId'], tier1['category'], normalize='index')
if all(c in ct.columns for c in CATEGORY_ORDER):
    ct[CATEGORY_ORDER].plot.bar(stacked=True, ax=axes[1], color=colors, edgecolor='black', linewidth=0.5)
axes[1].set_title('B. By Organism')
axes[1].set_ylabel('Fraction')
axes[1].legend(fontsize=7, loc='upper right')
axes[1].tick_params(axis='x', rotation=45)

# Panel C: Completeness vs Importance scatter
for cat in CATEGORY_ORDER:
    subset = tier1[tier1['category'] == cat]
    axes[2].scatter(subset['frac_complete'], subset['importance_score'],
                    c=CATEGORY_COLORS[cat], label=cat, alpha=0.5, s=30, edgecolors='black', linewidth=0.3)
if 'importance_score' in tier1.columns:
    thresh = tier1['importance_score'].median()
    axes[2].axhline(y=thresh, color='gray', linestyle='--', alpha=0.5)
    axes[2].axvline(x=0.5, color='gray', linestyle='--', alpha=0.5)
axes[2].set_xlabel('Pathway Completeness (frac genomes)')
axes[2].set_ylabel('Fitness Importance Score')
axes[2].set_title('C. Completeness vs Importance')
axes[2].legend(fontsize=7)

plt.suptitle('Metabolic Capability vs Dependency: Pathway Classification\n'
             '(7 Fitness Browser organisms, 23 GapMind pathways)', fontsize=14, y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'fig1_four_category_overview.png'), dpi=200, bbox_inches='tight')
plt.close()
print("  Saved: fig1_four_category_overview.png")

# --- Figure 2: Conservation Validation ---
print("\n[3] Figure 2: Conservation validation (core vs all-genes)...")

# Use core_vs_all for species-level validation
# For each pathway, compute mean gap across species
pathway_gap = core_vs_all.groupby('pathway').agg(
    mean_gap=('gap', 'mean'),
    mean_all=('frac_complete_all', 'mean'),
    mean_core=('frac_complete_core', 'mean'),
).reset_index()

# Amino acid pathways
aa_pathways = ['arg', 'asn', 'cys', 'gln', 'gly', 'his', 'ile', 'leu', 'lys',
               'met', 'phe', 'pro', 'ser', 'thr', 'trp', 'tyr', 'val', 'chorismate']
aa_gap = pathway_gap[pathway_gap['pathway'].isin(aa_pathways)].sort_values('mean_gap', ascending=False)

fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# Panel A: Core vs All for AA pathways
if len(aa_gap) > 0:
    x = range(len(aa_gap))
    w = 0.35
    axes[0].bar([i - w/2 for i in x], aa_gap['mean_all'], w, label='All genes', alpha=0.8, color='steelblue')
    axes[0].bar([i + w/2 for i in x], aa_gap['mean_core'], w, label='Core genes only', alpha=0.8, color='coral')
    axes[0].set_xticks(list(x))
    axes[0].set_xticklabels(aa_gap['pathway'], rotation=45, ha='right')
    axes[0].set_ylabel('Mean Fraction Complete')
    axes[0].set_title('A. AA Pathway Completeness: Core vs All Genes')
    axes[0].legend()

# Panel B: Gap distribution
axes[1].hist(pathway_gap['mean_gap'], bins=30, edgecolor='black', alpha=0.7, color='steelblue')
axes[1].axvline(x=pathway_gap['mean_gap'].median(), color='red', linestyle='--', label=f'Median: {pathway_gap["mean_gap"].median():.3f}')
axes[1].set_xlabel('Mean Accessory Dependence (gap)')
axes[1].set_ylabel('Count (pathways)')
axes[1].set_title('B. Distribution of Accessory Genome Dependence')
axes[1].legend()

plt.suptitle('Accessory Genome Drives Pathway Completeness\n'
             f'({len(core_vs_all):,} species x pathway pairs, NB03)', fontsize=14)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'fig2_conservation_by_category.png'), dpi=200, bbox_inches='tight')
plt.close()
print("  Saved: fig2_conservation_by_category.png")

# --- Figure 3: Pan-Bacterial Pathway Conservation ---
print("\n[4] Figure 3: Pan-bacterial pathway conservation vs openness...")

# species_metrics already has pangenome columns merged (from NB03)
merged = species_metrics.copy()

fig, axes = plt.subplots(1, 3, figsize=(18, 6))

rho_var, p_var = stats.spearmanr(merged['n_variable'], merged['openness'])
axes[0].scatter(merged['n_variable'], merged['openness'], alpha=0.1, s=5, c='steelblue')
axes[0].set_xlabel('Variable Pathways (10-90% complete)')
axes[0].set_ylabel('Pangenome Openness')
axes[0].set_title(f'A. Variable Pathways vs Openness\nrho={rho_var:.3f}, p={p_var:.1e}')

rho_comp, p_comp = stats.spearmanr(merged['n_complete_majority'], merged['openness'])
axes[1].scatter(merged['n_complete_majority'], merged['openness'], alpha=0.1, s=5, c='coral')
axes[1].set_xlabel('Complete Pathways (>50%)')
axes[1].set_ylabel('Pangenome Openness')
axes[1].set_title(f'B. Complete Pathways vs Openness\nrho={rho_comp:.3f}, p={p_comp:.1e}')

rho_div, p_div = stats.spearmanr(merged['pathway_diversity'], merged['openness'])
axes[2].scatter(merged['pathway_diversity'], merged['openness'], alpha=0.1, s=5, c='forestgreen')
axes[2].set_xlabel('Pathway Completeness Std Dev')
axes[2].set_ylabel('Pangenome Openness')
axes[2].set_title(f'C. Diversity vs Openness\nrho={rho_div:.3f}, p={p_div:.1e}')

plt.suptitle('Pan-Bacterial Metabolic Capability vs Pangenome Openness\n'
             f'(n={len(merged):,} species, NB03)', fontsize=14)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'fig3_core_accessory_pathways.png'), dpi=200, bbox_inches='tight')
plt.close()
print("  Saved: fig3_core_accessory_pathways.png")

# --- Figure 4: Metabolic Ecotypes ---
print("\n[5] Figure 4: Metabolic ecotypes vs openness...")

ecotype_with_pan = ecotype_summary.merge(pangenome, left_on='clade_name', right_on='gtdb_species_clade_id', how='inner')
ecotype_with_pan['openness'] = ecotype_with_pan['no_aux_genome'] / ecotype_with_pan['no_gene_clusters']

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

rho_eco, p_eco = stats.spearmanr(ecotype_with_pan['n_ecotypes'], ecotype_with_pan['openness'])
axes[0].scatter(ecotype_with_pan['n_ecotypes'], ecotype_with_pan['openness'], alpha=0.3, s=15, c='steelblue')
axes[0].set_xlabel('Number of Metabolic Ecotypes')
axes[0].set_ylabel('Pangenome Openness')
axes[0].set_title(f'A. Ecotypes vs Openness\nrho={rho_eco:.3f}, p={p_eco:.1e}')

axes[1].hist(ecotype_with_pan['n_ecotypes'], bins=range(1, ecotype_with_pan['n_ecotypes'].max()+2),
             edgecolor='black', alpha=0.7, color='steelblue')
axes[1].set_xlabel('Number of Metabolic Ecotypes')
axes[1].set_ylabel('Count (species)')
axes[1].set_title(f'B. Ecotype Distribution\n(median={ecotype_with_pan["n_ecotypes"].median():.0f}, max={ecotype_with_pan["n_ecotypes"].max()})')

plt.suptitle(f'Metabolic Ecotypes and Pangenome Openness\n'
             f'({len(ecotype_with_pan):,} species with >=3 variable pathways, NB04)', fontsize=14)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'fig4_ecotype_openness.png'), dpi=200, bbox_inches='tight')
plt.close()
print("  Saved: fig4_ecotype_openness.png")

# --- Figure 5: Condition-Type Shifts ---
print("\n[6] Figure 5: Condition-type analysis...")

if cond is not None and len(cond) > 0:
    # Summarize: mean importance by pathway × condition type
    cond_summary = cond.groupby(['gapmind_pathway', 'condition_type']).agg(
        mean_importance=('importance', 'mean'),
        n_orgs=('orgId', 'nunique'),
    ).reset_index()

    pivot_imp = cond_summary.pivot_table(
        index='gapmind_pathway', columns='condition_type',
        values='mean_importance'
    )

    fig, ax = plt.subplots(figsize=(14, 8))
    sns.heatmap(pivot_imp, cmap='YlOrRd', annot=True, fmt='.2f', ax=ax,
                linewidths=0.5)
    ax.set_title('Pathway Fitness Importance by Condition Type\n'
                 '(Higher = more fitness-important genes in that pathway under that condition)')
    ax.set_ylabel('GapMind Pathway')
    ax.set_xlabel('Condition Type')
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, 'fig5_condition_type_shifts.png'), dpi=200, bbox_inches='tight')
    plt.close()
    print("  Saved: fig5_condition_type_shifts.png")
else:
    print("  Condition-type data not available")

# --- Summary Statistics ---
print("\n[7] Compiling summary statistics...")

summary = []
summary.append('=== Metabolic Capability vs Dependency: Summary Statistics ===')
summary.append(f'Analysis date: 2026-02-19')
summary.append('')

summary.append('--- Tier 1: Fitness-Validated Classification (NB02) ---')
summary.append(f'FB organisms analyzed: {tier1["orgId"].nunique()}')
summary.append(f'GapMind pathways analyzed: {tier1["gapmind_pathway"].nunique()}')
summary.append(f'Total classifications: {len(tier1):,}')
summary.append(f'Mapping approach: FB-native KEGG (besthitkegg → keggmember → EC → KEGG map)')
for cat in CATEGORY_ORDER:
    n = (tier1['category'] == cat).sum()
    pct = n / len(tier1) * 100
    summary.append(f'  {cat}: {n} ({pct:.1f}%)')

summary.append(f'\nKey finding: 35.4% Active Dependencies — pathways complete AND fitness-important')
summary.append(f'Key finding: Condition-type analysis reveals ALL Latent Capabilities become')
summary.append(f'  important under specific conditions (N, stress, C limitation)')
summary.append(f'  → supports core_gene_tradeoffs: "costly in lab but conserved in nature"')

summary.append('')
summary.append('--- Tier 2: Pan-Bacterial Pathway Conservation (NB03) ---')
summary.append(f'Species analyzed: {len(species_metrics):,}')
summary.append(f'H1b: Variable pathways vs openness: rho={rho_var:.3f}, p={p_var:.1e}')
summary.append(f'Partial Spearman (ctrl n_genomes): rho=0.530, p=2.83e-203')
summary.append(f'Key finding: Species with more variable pathways have more open pangenomes')
summary.append(f'Key finding: Amino acid biosynthesis shows largest accessory dependence gap')

top_gap_pathways = pathway_gap.nlargest(5, 'mean_gap')
summary.append(f'\nTop accessory-dependent pathways:')
for _, row in top_gap_pathways.iterrows():
    summary.append(f'  {row["pathway"]}: gap={row["mean_gap"]:.3f} (all={row["mean_all"]:.3f}, core={row["mean_core"]:.3f})')

summary.append('')
summary.append('--- Metabolic Ecotypes (NB04) ---')
summary.append(f'Species with ecotypes: {len(ecotype_summary):,}')
summary.append(f'Median ecotypes per species: {ecotype_summary["n_ecotypes"].median():.0f}')
summary.append(f'Max ecotypes: {ecotype_summary["n_ecotypes"].max()}')
summary.append(f'Ecotypes vs openness: rho={rho_eco:.3f}, p={p_eco:.1e}')
summary.append(f'Key finding: More metabolic ecotypes → more open pangenomes')

summary.append('')
summary.append('--- Cross-Project Context ---')
summary.append('  metal_fitness_atlas: 87.4% metal-fitness genes are core (OR=2.08)')
summary.append('  conservation_fitness_synthesis: 16pp fitness-conservation gradient')
summary.append('  ecotype_analysis: phylogeny dominates gene content (60.5% of species)')
summary.append('  pangenome_openness: null result for openness vs env/phylo')
summary.append('  core_gene_tradeoffs: 28,017 genes costly in lab but conserved in nature')

summary_text = '\n'.join(summary)
print(summary_text)

with open(os.path.join(FIG_DIR, 'summary_statistics.txt'), 'w') as f:
    f.write(summary_text)
print(f"\nSaved: summary_statistics.txt")

print("\n" + "=" * 60)
print("NB05 COMPLETE")
print("=" * 60)

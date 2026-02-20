#!/usr/bin/env python3
"""NB02 runner: Tier 1 — Pathway Classification Using Fitness Data.

Uses FB-native KEGG/SEED annotations (not pangenome link table) to map
FB genes to GapMind pathways. This avoids the DIAMOND alignment pipeline
dependency while providing direct gene-to-pathway mapping.

Chain: FB gene → KEGG KO → EC number → KEGG map → GapMind pathway
"""
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

plt.rcParams.update({'figure.figsize': (12, 8), 'figure.dpi': 150, 'font.size': 11})

CATEGORY_COLORS = {
    'Active Dependency': '#2ecc71',
    'Latent Capability': '#f39c12',
    'Incomplete but Important': '#e74c3c',
    'Missing': '#95a5a6',
}
CATEGORY_ORDER = ['Active Dependency', 'Latent Capability', 'Incomplete but Important', 'Missing']

print("=" * 60)
print("NB02: Tier 1 — Pathway Classification Using Fitness Data")
print("=" * 60)

# --- 1. Load Data ---
print("\n[1] Loading data...")

# FB-genome mapping (which FB organisms have GapMind data)
fb_coverage = pd.read_csv(os.path.join(DATA_DIR, 'gapmind_fb_coverage.csv'))
fb_orgs_with_gapmind = fb_coverage[fb_coverage['in_gapmind'] == True]['orgId'].tolist()
print(f"  FB organisms with GapMind data: {fb_orgs_with_gapmind}")

# GapMind pathway status for FB organisms
gapmind = pd.read_csv(os.path.join(DATA_DIR, 'gapmind_genome_pathway_status.csv'),
                       usecols=['genome_id', 'clade_name', 'pathway', 'metabolic_category', 'is_complete'])
gapmind['is_complete'] = pd.to_numeric(gapmind['is_complete'], errors='coerce')

# Filter to FB organism genomes
fb_genome_map = fb_coverage[fb_coverage['in_gapmind'] == True][['orgId', 'gapmind_genome_id']].copy()
fb_genome_map.rename(columns={'gapmind_genome_id': 'genome_id'}, inplace=True)

# Get GapMind status for each FB organism by matching genome prefix
# FB genomes are identified by accession (e.g., GCF_000195755.1)
fb_gapmind_rows = []
for _, row in fb_genome_map.iterrows():
    org_id = row['orgId']
    genome_prefix = row['genome_id']
    # GapMind genome_id contains the species-level genome accession
    matches = gapmind[gapmind['genome_id'].str.contains(genome_prefix, na=False)]
    if len(matches) > 0:
        matches = matches.copy()
        matches['orgId'] = org_id
        fb_gapmind_rows.append(matches)
    else:
        print(f"  WARNING: No GapMind match for {org_id} ({genome_prefix})")

if fb_gapmind_rows:
    fb_gapmind = pd.concat(fb_gapmind_rows, ignore_index=True)
else:
    # Try matching via clade_name species lookup
    print("  Direct genome match failed, trying species-level matching...")
    fb_gapmind = pd.DataFrame()

print(f"  GapMind rows for FB organisms: {len(fb_gapmind):,}")

# Species-level pathway completeness (for organisms with many genomes)
fb_org_pathways = fb_gapmind.groupby(['orgId', 'pathway', 'metabolic_category']).agg(
    frac_complete=('is_complete', 'mean'),
).reset_index()
print(f"  Organism × pathway pairs: {len(fb_org_pathways):,}")

# Fitness summary
fitness = pd.read_csv(os.path.join(DATA_DIR, 'fb_fitness_summary.csv'))
fitness_fb = fitness[fitness['orgId'].isin(fb_orgs_with_gapmind)]
print(f"  Fitness rows (FB with GapMind): {len(fitness_fb):,}")

# Condition-type fitness
cond_fitness = pd.read_csv(os.path.join(DATA_DIR, 'fb_fitness_by_condition_type.csv'))
cond_fitness_fb = cond_fitness[cond_fitness['orgId'].isin(fb_orgs_with_gapmind)]
print(f"  Condition-type fitness rows: {len(cond_fitness_fb):,}")

# Essential genes
essentials = pd.read_csv(os.path.join(DATA_DIR, 'fb_essential_genes.csv'))
essential_set = set(zip(essentials['orgId'], essentials['locusId']))
print(f"  Essential genes: {len(essentials):,}")

# FB KEGG KO annotations
fb_kegg_ko = pd.read_csv(os.path.join(DATA_DIR, 'fb_gene_kegg_ko.csv'))
fb_kegg_ko_fb = fb_kegg_ko[fb_kegg_ko['orgId'].isin(fb_orgs_with_gapmind)]
print(f"  FB KEGG KO annotations (FB with GapMind): {len(fb_kegg_ko_fb):,}")

# FB EC annotations
fb_ec = pd.read_csv(os.path.join(DATA_DIR, 'fb_gene_ec.csv'))
fb_ec_fb = fb_ec[fb_ec['orgId'].isin(fb_orgs_with_gapmind)]
print(f"  FB EC annotations: {len(fb_ec_fb):,}")

# KEGG map → EC mapping
kegg_map_ec = pd.read_csv(os.path.join(DATA_DIR, 'kegg_map_ec.csv'))
print(f"  KEGG map-EC pairs: {len(kegg_map_ec):,}")

# SEED annotations
fb_seed = pd.read_csv(os.path.join(DATA_DIR, 'fb_gene_seed.csv'))
fb_seed_fb = fb_seed[fb_seed['orgId'].isin(fb_orgs_with_gapmind)]
print(f"  SEED annotations (FB with GapMind): {len(fb_seed_fb):,}")

# --- 2. Map FB Genes to GapMind Pathways ---
print("\n[2] Mapping FB genes to GapMind pathways...")

# KEGG map → GapMind pathway mapping
KEGG_TO_GAPMIND = {
    # Amino acid biosynthesis
    '00220': 'arg', '00330': 'arg',
    '00260': 'ser', '00270': 'met',
    '00290': 'val', '00300': 'lys',
    '00340': 'his', '00350': 'tyr',
    '00360': 'phe', '00380': 'trp',
    '00400': 'chorismate', '00250': 'asn',
    # Carbon source utilization
    '00010': 'glucose', '00020': 'citrate',
    '00030': 'ribose', '00040': 'glucuronate',
    '00051': 'fructose', '00052': 'galactose',
    '00500': 'sucrose', '00520': 'NAG',
    '00620': 'pyruvate', '00630': 'succinate',
    '00640': 'propionate', '00562': 'myoinositol',
}

# Chain: FB gene → EC → KEGG map → GapMind pathway
# Step 1: FB gene → EC number (via fb_gene_ec.csv)
# Step 2: EC number → KEGG map (via kegg_map_ec.csv)
# Step 3: KEGG map → GapMind pathway

# Join FB EC with KEGG map-EC
gene_to_map = fb_ec_fb.merge(kegg_map_ec, on='ecnum', how='inner')
print(f"  Gene-EC-Map joins: {len(gene_to_map):,}")

# Map KEGG maps to GapMind pathways
gene_to_map['gapmind_pathway'] = gene_to_map['mapId'].map(KEGG_TO_GAPMIND)
gene_to_pathway = gene_to_map.dropna(subset=['gapmind_pathway'])[
    ['orgId', 'locusId', 'kegg_ko', 'ecnum', 'mapId', 'gapmind_pathway']
].drop_duplicates()

print(f"  FB genes mapped to GapMind pathways: {gene_to_pathway[['orgId','locusId']].drop_duplicates().shape[0]:,}")
print(f"  Gene × pathway pairs: {len(gene_to_pathway):,}")
print(f"  GapMind pathways represented: {gene_to_pathway['gapmind_pathway'].nunique()}")
print(f"\n  Pathway distribution:")
print(gene_to_pathway['gapmind_pathway'].value_counts().head(20).to_string())

# Also build SEED-based mapping as validation
SEED_TO_METABOLIC_CATEGORY = {
    'Amino Acids and Derivatives': 'amino_acid',
    'Carbohydrates': 'carbon',
    'Respiration': 'carbon',
    'Fatty Acids, Lipids, and Isoprenoids': 'carbon',
}
fb_seed_fb_mapped = fb_seed_fb[fb_seed_fb['toplevel'].isin(SEED_TO_METABOLIC_CATEGORY)].copy()
fb_seed_fb_mapped['metabolic_broad'] = fb_seed_fb_mapped['toplevel'].map(SEED_TO_METABOLIC_CATEGORY)
print(f"\n  SEED metabolic genes: {fb_seed_fb_mapped[['orgId','locusId']].drop_duplicates().shape[0]:,}")
print(f"  By category: {fb_seed_fb_mapped['metabolic_broad'].value_counts().to_dict()}")

# --- 3. Aggregate Fitness by Pathway × Organism ---
print("\n[3] Computing pathway-level fitness importance...")

# Join pathway genes with fitness data
pathway_fitness = gene_to_pathway.merge(
    fitness_fb[['orgId', 'locusId', 'mean_fitness', 'median_fitness', 'min_fitness',
                'n_conditions', 'n_sick', 'n_strong_phenotype', 'fitness_breadth',
                'sick_breadth']],
    on=['orgId', 'locusId'],
    how='left'
)

# Mark essential genes (merge approach, faster than row-wise apply)
essentials_flag = essentials[['orgId', 'locusId']].drop_duplicates().assign(is_essential=True)
pathway_fitness = pathway_fitness.merge(essentials_flag, on=['orgId', 'locusId'], how='left')
pathway_fitness['is_essential'] = pathway_fitness['is_essential'].fillna(False).astype(bool)

print(f"  Pathway-fitness rows: {len(pathway_fitness):,}")
print(f"  With fitness data: {pathway_fitness['median_fitness'].notna().sum():,}")
print(f"  Essential: {pathway_fitness['is_essential'].sum():,}")

# Aggregate per organism × pathway
pathway_agg = pathway_fitness.groupby(['orgId', 'gapmind_pathway']).agg(
    n_genes=('locusId', 'nunique'),
    n_essential=('is_essential', 'sum'),
    mean_fitness_of_genes=('mean_fitness', 'mean'),
    min_fitness_of_genes=('min_fitness', 'min'),
    frac_sick=('n_sick', lambda x: (x > 0).mean()),
    total_sick_conditions=('n_sick', 'sum'),
    total_strong_phenotype=('n_strong_phenotype', 'sum'),
    mean_fitness_breadth=('fitness_breadth', 'mean'),
    max_fitness_breadth=('fitness_breadth', 'max'),
    mean_sick_breadth=('sick_breadth', 'mean'),
).reset_index()

# Composite importance score: 40% essentiality, 30% breadth, 30% magnitude
pathway_agg['frac_essential'] = pathway_agg['n_essential'] / pathway_agg['n_genes']
breadth_component = pathway_agg['mean_fitness_breadth'].fillna(pathway_agg['frac_sick'])
magnitude_component = (-pathway_agg['min_fitness_of_genes'].clip(upper=0) / 3).clip(upper=1)

pathway_agg['importance_score'] = (
    0.4 * pathway_agg['frac_essential'] +
    0.3 * breadth_component +
    0.3 * magnitude_component
)

print(f"\n  Organism × pathway pairs: {len(pathway_agg):,}")
print(f"  Importance score distribution:")
print(pathway_agg['importance_score'].describe().to_string())

# --- 4. Classify Pathways ---
print("\n[4] Classifying pathways into four categories...")

# Merge with GapMind completeness
classified = pathway_agg.merge(
    fb_org_pathways[['orgId', 'pathway', 'metabolic_category', 'frac_complete']].rename(
        columns={'pathway': 'gapmind_pathway'}
    ),
    on=['orgId', 'gapmind_pathway'],
    how='left'
)

# For pathways not matched in GapMind, try to get from species-level data
n_missing = classified['frac_complete'].isna().sum()
if n_missing > 0:
    print(f"  {n_missing} pathway entries without direct GapMind match")
    # Check what pathways are in GapMind
    gapmind_pathways = set(fb_org_pathways['pathway'].unique())
    classified_pathways = set(classified['gapmind_pathway'].unique())
    missing_pathways = classified_pathways - gapmind_pathways
    if missing_pathways:
        print(f"  Pathways not in GapMind: {missing_pathways}")

# Thresholds
COMPLETENESS_THRESHOLD = 0.5
IMPORTANCE_THRESHOLD = classified['importance_score'].median()
print(f"  Completeness threshold: {COMPLETENESS_THRESHOLD}")
print(f"  Importance threshold (median): {IMPORTANCE_THRESHOLD:.4f}")

def classify_pathway(row):
    complete = row['frac_complete'] >= COMPLETENESS_THRESHOLD if pd.notna(row['frac_complete']) else False
    important = row['importance_score'] >= IMPORTANCE_THRESHOLD if pd.notna(row['importance_score']) else False
    if complete and important:
        return 'Active Dependency'
    elif complete and not important:
        return 'Latent Capability'
    elif not complete and important:
        return 'Incomplete but Important'
    else:
        return 'Missing'

classified['category'] = classified.apply(classify_pathway, axis=1)

print(f"\n  Classification results:")
for cat in CATEGORY_ORDER:
    n = (classified['category'] == cat).sum()
    pct = n / len(classified) * 100
    print(f"    {cat:30s}: {n:5d} ({pct:.1f}%)")

# --- 5. Conservation Validation ---
print("\n[5] Conservation validation using core vs all-genes data...")

# Use NB03's core_vs_all_pathway_completeness.csv as a proxy for core enrichment
core_vs_all = pd.read_csv(os.path.join(DATA_DIR, 'core_vs_all_pathway_completeness.csv'))

# For each FB organism, find its species in core_vs_all
fb_species = fb_gapmind[['orgId', 'clade_name']].drop_duplicates()

# Merge classified pathways with core_vs_all data
classified_with_gap = classified.merge(fb_species, on='orgId', how='left')
classified_with_gap = classified_with_gap.merge(
    core_vs_all[['clade_name', 'pathway', 'frac_complete_all', 'frac_complete_core', 'gap']].rename(
        columns={'pathway': 'gapmind_pathway'}
    ),
    on=['clade_name', 'gapmind_pathway'],
    how='left'
)

# The "gap" (all - core) indicates accessory genome dependence
# Active Dependencies should have SMALLER gap (pathway works with core alone)
# Latent Capabilities and Missing pathways should have LARGER gap
n_with_gap = classified_with_gap['gap'].notna().sum()
print(f"  Pathway entries with conservation data: {n_with_gap}")

if n_with_gap > 10:
    print(f"\n  Accessory dependence (gap = all - core) by category:")
    for cat in CATEGORY_ORDER:
        subset = classified_with_gap[classified_with_gap['category'] == cat]['gap'].dropna()
        if len(subset) > 0:
            print(f"    {cat:30s}: median gap={subset.median():.3f}, mean={subset.mean():.3f} (n={len(subset)})")

    # Statistical test
    ad_gap = classified_with_gap[classified_with_gap['category'] == 'Active Dependency']['gap'].dropna()
    lc_gap = classified_with_gap[classified_with_gap['category'] == 'Latent Capability']['gap'].dropna()
    if len(ad_gap) > 5 and len(lc_gap) > 5:
        u, p = stats.mannwhitneyu(ad_gap, lc_gap, alternative='less')
        print(f"\n  Mann-Whitney (Active Dep gap < Latent Cap gap): U={u:.0f}, p={p:.3e}")

    # Core completeness by category
    print(f"\n  Core-only pathway completeness by category:")
    for cat in CATEGORY_ORDER:
        subset = classified_with_gap[classified_with_gap['category'] == cat]['frac_complete_core'].dropna()
        if len(subset) > 0:
            print(f"    {cat:30s}: core_complete={subset.mean():.3f} (n={len(subset)})")

# --- 6. Condition-Type Analysis ---
print("\n[6] Condition-type fitness analysis...")

# Join pathway genes with condition-type fitness
cond_pathway = gene_to_pathway.merge(
    cond_fitness_fb, on=['orgId', 'locusId'], how='inner'
)

if len(cond_pathway) > 0:
    cond_agg = cond_pathway.groupby(['orgId', 'gapmind_pathway', 'condition_type']).agg(
        n_genes=('locusId', 'nunique'),
        mean_fitness=('mean_fitness', 'mean'),
        min_fitness=('min_fitness', 'min'),
        frac_sick=('n_sick', lambda x: (x > 0).mean()),
    ).reset_index()

    # Importance per condition type
    cond_agg['importance'] = cond_agg['frac_sick'] + (-cond_agg['min_fitness'].clip(upper=0) / 3).clip(upper=1)

    # Find Latent Capability pathways that become important under specific conditions
    latent_pairs = classified[classified['category'] == 'Latent Capability'][['orgId', 'gapmind_pathway']]
    latent_cond = latent_pairs.merge(cond_agg, on=['orgId', 'gapmind_pathway'], how='inner')
    latent_reclassified = latent_cond[latent_cond['importance'] >= IMPORTANCE_THRESHOLD]

    n_latent = len(latent_pairs)
    n_shifted = latent_reclassified[['orgId', 'gapmind_pathway']].drop_duplicates().shape[0]
    print(f"  Latent Capability pathways: {n_latent}")
    print(f"  Shift to Active under specific conditions: {n_shifted}")
    if len(latent_reclassified) > 0:
        print(f"\n  Condition types triggering reclassification:")
        print(latent_reclassified['condition_type'].value_counts().to_string())

    # Save condition analysis
    cond_agg.to_csv(os.path.join(DATA_DIR, 'tier1_condition_type_analysis.csv'), index=False)
    print(f"\n  Saved: tier1_condition_type_analysis.csv ({len(cond_agg):,} rows)")
else:
    print("  No condition-type pathway data available")
    cond_agg = pd.DataFrame()
    latent_reclassified = pd.DataFrame()

# --- 7. Visualizations ---
print("\n[7] Generating figures...")

# Figure A: Classification heatmap
fig, ax = plt.subplots(figsize=(16, 8))
category_map = {'Active Dependency': 3, 'Latent Capability': 2,
                'Incomplete but Important': 1, 'Missing': 0}
classified['cat_num'] = classified['category'].map(category_map)
pivot = classified.pivot_table(index='orgId', columns='gapmind_pathway',
                                values='cat_num', aggfunc='first')
if len(pivot) > 0:
    cmap = plt.cm.colors.ListedColormap(['#95a5a6', '#e74c3c', '#f39c12', '#2ecc71'])
    sns.heatmap(pivot.fillna(-1), cmap=cmap, ax=ax, linewidths=0.5,
                cbar_kws={'ticks': [0, 1, 2, 3]})
    ax.set_title('Pathway Classification: FB Organisms x GapMind Pathways')
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, 'tier1_classification_heatmap.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("  Saved: tier1_classification_heatmap.png")

# Figure B: Category distribution
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

cat_counts = classified['category'].value_counts().reindex(CATEGORY_ORDER)
colors = [CATEGORY_COLORS[c] for c in CATEGORY_ORDER]
cat_counts.plot.bar(ax=axes[0], color=colors, edgecolor='black', linewidth=0.5)
axes[0].set_title('Overall Category Distribution')
axes[0].set_ylabel('Count (organism x pathway)')
axes[0].tick_params(axis='x', rotation=30)

# Per-organism breakdown
ct = pd.crosstab(classified['orgId'], classified['category'], normalize='index')
if all(c in ct.columns for c in CATEGORY_ORDER):
    ct[CATEGORY_ORDER].plot.bar(stacked=True, ax=axes[1], color=colors, edgecolor='black', linewidth=0.5)
axes[1].set_title('Category Breakdown by Organism')
axes[1].set_ylabel('Fraction')
axes[1].legend(fontsize=8, loc='upper right')
axes[1].tick_params(axis='x', rotation=45)

plt.suptitle('Tier 1: Metabolic Capability vs Dependency Classification', fontsize=14)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'tier1_category_distribution.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: tier1_category_distribution.png")

# Figure C: Conservation validation
if n_with_gap > 10:
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Panel A: Core completeness by category
    data_for_box = classified_with_gap[classified_with_gap['frac_complete_core'].notna()]
    if len(data_for_box) > 0:
        sns.boxplot(data=data_for_box, x='category', y='frac_complete_core',
                    order=CATEGORY_ORDER, palette=CATEGORY_COLORS, ax=axes[0])
        axes[0].set_title('Core-Only Pathway Completeness by Category')
        axes[0].set_ylabel('Frac Complete (Core Genes Only)')
        axes[0].tick_params(axis='x', rotation=15)

    # Panel B: Accessory dependence (gap) by category
    data_for_gap = classified_with_gap[classified_with_gap['gap'].notna()]
    if len(data_for_gap) > 0:
        sns.boxplot(data=data_for_gap, x='category', y='gap',
                    order=CATEGORY_ORDER, palette=CATEGORY_COLORS, ax=axes[1])
        axes[1].set_title('Accessory Genome Dependence by Category')
        axes[1].set_ylabel('Gap (All Genes - Core Only)')
        axes[1].tick_params(axis='x', rotation=15)

    plt.suptitle('Validation: Active Dependencies Rely Less on Accessory Genome', fontsize=13)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, 'tier1_conservation_validation.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("  Saved: tier1_conservation_validation.png")

# Figure D: Condition-type shifts
if len(latent_reclassified) > 0:
    fig, ax = plt.subplots(figsize=(12, 6))
    shift_counts = latent_reclassified.groupby(['gapmind_pathway', 'condition_type']).size().unstack(fill_value=0)
    shift_counts.plot.bar(stacked=True, ax=ax, edgecolor='black', linewidth=0.5)
    ax.set_title('Latent Capabilities Becoming Important Under Specific Conditions\n'
                 '(Addresses core_gene_tradeoffs: "costly in lab but conserved in nature")')
    ax.set_ylabel('Count (organism x pathway)')
    ax.legend(title='Condition Type')
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, 'tier1_condition_type_shifts.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("  Saved: tier1_condition_type_shifts.png")

# Figure E: Importance vs Completeness scatter
fig, ax = plt.subplots(figsize=(10, 8))
for cat in CATEGORY_ORDER:
    subset = classified[classified['category'] == cat]
    ax.scatter(subset['frac_complete'], subset['importance_score'],
               c=CATEGORY_COLORS[cat], label=cat, alpha=0.6, s=40, edgecolors='black', linewidth=0.3)
ax.axhline(y=IMPORTANCE_THRESHOLD, color='gray', linestyle='--', alpha=0.5, label=f'Importance threshold ({IMPORTANCE_THRESHOLD:.3f})')
ax.axvline(x=COMPLETENESS_THRESHOLD, color='gray', linestyle='--', alpha=0.5)
ax.set_xlabel('Pathway Completeness (fraction of genomes)')
ax.set_ylabel('Fitness Importance Score')
ax.set_title('Completeness vs Importance: Four-Category Classification')
ax.legend(loc='upper left')
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'tier1_completeness_vs_importance.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: tier1_completeness_vs_importance.png")

# --- 8. Save Results ---
print("\n[8] Saving results...")

# Drop temporary columns
save_cols = [c for c in classified.columns if c != 'cat_num']
classified[save_cols].to_csv(os.path.join(DATA_DIR, 'tier1_pathway_classification.csv'), index=False)
print(f"  tier1_pathway_classification.csv: {len(classified):,} rows")

# Summary
print("\n" + "=" * 60)
print("NB02 SUMMARY")
print("=" * 60)
print(f"  Organisms analyzed: {classified['orgId'].nunique()}")
print(f"  Pathways analyzed: {classified['gapmind_pathway'].nunique()}")
print(f"  Total classifications: {len(classified):,}")
for cat in CATEGORY_ORDER:
    n = (classified['category'] == cat).sum()
    pct = n / len(classified) * 100
    print(f"    {cat:30s}: {n:5d} ({pct:.1f}%)")
print(f"\n  Mapping approach: FB-native KEGG (besthitkegg → keggmember → EC → KEGG map)")
print(f"  Gene-pathway pairs used: {len(gene_to_pathway):,}")
print(f"  Importance threshold: {IMPORTANCE_THRESHOLD:.4f}")
print(f"  Completeness threshold: {COMPLETENESS_THRESHOLD}")

print("\n" + "=" * 60)
print("NB02 COMPLETE")
print("=" * 60)

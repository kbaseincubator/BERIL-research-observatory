#!/usr/bin/env python3
"""NB06: Temporal Trends + BacDive Classification."""
import os, re, warnings
import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats

warnings.filterwarnings('ignore')

PROJECT_DIR = Path(__file__).resolve().parent.parent
ATLAS_DIR = PROJECT_DIR.parent / 'amr_pangenome_atlas'
DATA_DIR = PROJECT_DIR / 'data'
MATRIX_DIR = DATA_DIR / 'genome_amr_matrices'

print("NB06: Temporal trends + BacDive...")

genome_meta = pd.read_csv(DATA_DIR / 'genome_metadata.csv')
eligible = pd.read_csv(DATA_DIR / 'eligible_species.csv')

def parse_year(date_str):
    if pd.isna(date_str): return np.nan
    s = str(date_str).strip()
    m = re.match(r'(\d{4})', s)
    if m:
        year = int(m.group(1))
        if 1900 <= year <= 2026: return year
    m = re.search(r'(\d{4})$', s)
    if m:
        year = int(m.group(1))
        if 1900 <= year <= 2026: return year
    return np.nan

genome_meta['year'] = genome_meta['collection_date'].apply(parse_year)
print(f"Genomes with valid year: {genome_meta['year'].notna().sum()}")

# AMR counts per genome
genome_amr_counts = {}
genome_species = {}
for mf in sorted(MATRIX_DIR.glob('*.tsv')):
    species_id = mf.stem
    matrix = pd.read_csv(mf, sep='\t', index_col=0)
    counts = matrix.sum(axis=1)
    for gid, cnt in counts.items():
        genome_amr_counts[gid] = cnt
        genome_species[gid] = species_id

genome_meta['amr_count'] = genome_meta['genome_id'].map(genome_amr_counts)
genome_meta['species_id'] = genome_meta['genome_id'].map(genome_species)
dated = genome_meta.dropna(subset=['year', 'amr_count', 'species_id'])
print(f"Genomes with year + AMR count: {len(dated)}")

# Temporal regression
temporal_results = []
for species_id, grp in dated.groupby('species_id'):
    if len(grp) < 20 or grp['year'].nunique() < 3: continue
    recent = grp[grp['year'] >= 1990]
    if len(recent) < 20 or recent['year'].nunique() < 3: continue
    slope, intercept, r_value, p_value, std_err = stats.linregress(recent['year'], recent['amr_count'])
    rho, rho_p = stats.spearmanr(recent['year'], recent['amr_count'])
    short_name = species_id.split('--')[0].replace('s__', '')
    temporal_results.append({
        'gtdb_species_clade_id': species_id, 'species_name': short_name,
        'n_genomes': len(recent),
        'year_range': f"{int(recent['year'].min())}-{int(recent['year'].max())}",
        'slope': slope, 'r_squared': r_value**2, 'p_value': p_value,
        'spearman_rho': rho, 'spearman_p': rho_p,
        'mean_amr': recent['amr_count'].mean(),
    })

temporal_df = pd.DataFrame(temporal_results)
if len(temporal_df) > 0:
    from statsmodels.stats.multitest import multipletests
    _, fdr, _, _ = multipletests(temporal_df['p_value'], method='fdr_bh')
    temporal_df['fdr'] = fdr
    temporal_df.to_csv(DATA_DIR / 'temporal_amr_trends.csv', index=False)

# BacDive classification
def classify_bacdive_cat1(species_name):
    name = species_name.lower().replace('_', ' ')
    host = ['staphylococcus', 'streptococcus', 'enterococcus', 'haemophilus',
            'neisseria', 'helicobacter', 'campylobacter', 'clostridioides',
            'klebsiella', 'escherichia', 'salmonella', 'shigella',
            'pseudomonas aeruginosa', 'acinetobacter baumannii',
            'mycobacterium tuberculosis', 'legionella', 'listeria',
            'bacteroides', 'bifidobacterium', 'lactobacillus',
            'enterobacter', 'citrobacter', 'proteus', 'serratia']
    for i in host:
        if i in name: return 'Host-associated'
    aquatic = ['vibrio', 'shewanella', 'alteromonas', 'marinobacter']
    for i in aquatic:
        if i in name: return 'Aquatic'
    soil = ['streptomyces', 'bacillus', 'paenibacillus', 'rhizobium',
            'bradyrhizobium', 'agrobacterium', 'pseudomonas fluorescens',
            'pseudomonas putida', 'pseudomonas syringae']
    for i in soil:
        if i in name: return 'Terrestrial'
    return 'Unknown'

eligible['species_name'] = eligible['gtdb_species_clade_id'].str.split('--').str[0].str.replace('s__', '', regex=False)
eligible['bacdive_cat1'] = eligible['species_name'].apply(classify_bacdive_cat1)

# NCBI env classification
def classify_environment(row):
    env = str(row.get('isolation_source', '')).lower() if pd.notna(row.get('isolation_source')) else ''
    h = str(row.get('host', '')).lower() if pd.notna(row.get('host')) else ''
    if any(k in env for k in ['blood', 'sputum', 'urine', 'wound', 'clinical', 'hospital']):
        return 'Human-Clinical'
    if 'homo sapiens' in h or 'human' in h: return 'Human-Other'
    if any(k in env for k in ['chicken', 'poultry', 'swine', 'pig', 'cattle', 'bovine', 'animal']):
        return 'Animal'
    if any(k in env for k in ['food', 'meat', 'milk']): return 'Food'
    if any(k in env for k in ['water', 'river', 'sewage', 'marine']): return 'Water'
    if any(k in env for k in ['soil', 'rhizosphere', 'plant']): return 'Soil/Plant'
    return 'Unknown'

genome_meta['ncbi_env'] = genome_meta.apply(classify_environment, axis=1)
species_env = (
    genome_meta[genome_meta['ncbi_env'] != 'Unknown']
    .groupby('species_id')['ncbi_env']
    .agg(lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else 'Unknown')
    .to_dict()
)
eligible['ncbi_env'] = eligible['gtdb_species_clade_id'].map(species_env).fillna('Unknown')

# Merge with variation data
variation = pd.read_csv(DATA_DIR / 'amr_variation_by_species.csv')
bridge = eligible.merge(variation[['gtdb_species_clade_id', 'variability_index', 'mean_jaccard',
                                    'mean_amr_per_genome']],
                         on='gtdb_species_clade_id', how='left')

# Kruskal-Wallis tests
bacdive_known = bridge[bridge['bacdive_cat1'] != 'Unknown']
if bacdive_known['bacdive_cat1'].nunique() >= 2:
    groups = [grp['mean_amr_per_genome'].dropna() for _, grp in bacdive_known.groupby('bacdive_cat1')]
    groups = [g for g in groups if len(g) >= 5]
    if len(groups) >= 2:
        h_stat, h_pval = stats.kruskal(*groups)
        print(f"Kruskal-Wallis AMR across BacDive cat1: H={h_stat:.1f}, p={h_pval:.1e}")

bridge.to_csv(DATA_DIR / 'bacdive_amr_bridge.csv', index=False)

print(f"\nNB06 COMPLETE")
print(f"Species with temporal data: {len(temporal_df)}")
if len(temporal_df) > 0:
    sig = temporal_df[temporal_df['fdr'] < 0.05]
    print(f"Significant trends: {len(sig)} ({(sig['slope']>0).sum()} increasing, {(sig['slope']<0).sum()} decreasing)")
print(f"BacDive classified: {(bridge['bacdive_cat1'] != 'Unknown').sum()}/{len(bridge)}")
print(f"NCBI env classified: {(bridge['ncbi_env'] != 'Unknown').sum()}/{len(bridge)}")

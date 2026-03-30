#!/usr/bin/env python3
"""NB07: Synthesis — Summary table + key statistics."""
import os, warnings
import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats

warnings.filterwarnings('ignore')

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / 'data'

print("NB07: Synthesis...")

# Load all results
variation = pd.read_csv(DATA_DIR / 'amr_variation_by_species.csv')
prevalence = pd.read_csv(DATA_DIR / 'amr_prevalence_by_gene.csv')

islands = pd.read_csv(DATA_DIR / 'resistance_islands.csv') if (DATA_DIR / 'resistance_islands.csv').exists() else pd.DataFrame()
phi_summary = pd.read_csv(DATA_DIR / 'phi_summary.csv') if (DATA_DIR / 'phi_summary.csv').exists() else pd.DataFrame()
mantel = pd.read_csv(DATA_DIR / 'mantel_results.csv') if (DATA_DIR / 'mantel_results.csv').exists() else pd.DataFrame()
ecotypes = pd.read_csv(DATA_DIR / 'ecotype_summary.csv') if (DATA_DIR / 'ecotype_summary.csv').exists() else pd.DataFrame()
temporal = pd.read_csv(DATA_DIR / 'temporal_amr_trends.csv') if (DATA_DIR / 'temporal_amr_trends.csv').exists() else pd.DataFrame()
bridge = pd.read_csv(DATA_DIR / 'bacdive_amr_bridge.csv') if (DATA_DIR / 'bacdive_amr_bridge.csv').exists() else pd.DataFrame()

print("Loaded datasets:")
for name, df in [('variation', variation), ('prevalence', prevalence),
                  ('islands', islands), ('phi_summary', phi_summary),
                  ('mantel', mantel), ('ecotypes', ecotypes),
                  ('temporal', temporal), ('bridge', bridge)]:
    print(f"  {name}: {len(df)} rows")

# Build integrated table
summary = variation[['gtdb_species_clade_id', 'n_genomes', 'n_amr',
                      'n_fixed', 'n_variable', 'n_rare',
                      'variability_index', 'mean_jaccard', 'mean_entropy',
                      'mean_amr_per_genome', 'phylum', 'openness']].copy()

if len(phi_summary) > 0:
    summary = summary.merge(
        phi_summary[['gtdb_species_clade_id', 'n_variable_genes', 'mean_phi',
                      'frac_strong_phi', 'n_islands']],
        on='gtdb_species_clade_id', how='left')

if len(mantel) > 0:
    summary = summary.merge(
        mantel[['gtdb_species_clade_id', 'mantel_r_all', 'mantel_fdr_all',
                'mantel_r_core', 'mantel_r_noncore']],
        on='gtdb_species_clade_id', how='left')

if len(ecotypes) > 0:
    summary = summary.merge(
        ecotypes[['gtdb_species_clade_id', 'n_clusters', 'silhouette']],
        on='gtdb_species_clade_id', how='left')

if len(temporal) > 0:
    summary = summary.merge(
        temporal[['gtdb_species_clade_id', 'slope', 'fdr']].rename(
            columns={'slope': 'temporal_slope', 'fdr': 'temporal_fdr'}),
        on='gtdb_species_clade_id', how='left')

summary.to_csv(DATA_DIR / 'integrated_summary.csv', index=False)
print(f"\nIntegrated summary: {len(summary)} species x {summary.shape[1]} columns")

# Key statistics
print("\n" + "="*70)
print("KEY STATISTICS FOR ABSTRACT")
print("="*70)

n_species = len(summary)
total_genomes = summary['n_genomes'].sum()

print(f"\nScale:")
print(f"  {n_species} species, {total_genomes:,} genomes")

print(f"\nVariation (NB02):")
print(f"  Median variability index: {summary['variability_index'].median():.3f}")
print(f"  Median Jaccard diversity: {summary['mean_jaccard'].median():.3f}")
print(f"  Prevalence classes: {prevalence['prevalence_class'].value_counts().to_dict()}")

r, p = stats.spearmanr(summary['openness'].dropna(),
                        summary.loc[summary['openness'].notna(), 'variability_index'])
print(f"  Variability-openness: rho={r:.3f}, p={p:.1e}")

if len(islands) > 0:
    print(f"\nResistance Islands (NB03):")
    print(f"  {len(islands)} islands in {islands['gtdb_species_clade_id'].nunique()} species")
    print(f"  Mean size: {islands['size'].mean():.1f} genes, mean phi: {islands['mean_phi'].mean():.3f}")

if len(mantel) > 0:
    print(f"\nPhylogenetic Signal (NB04):")
    sig_m = (mantel.get('mantel_fdr_all', pd.Series(dtype=float)) < 0.05).sum()
    print(f"  {sig_m}/{len(mantel)} species with significant signal")
    print(f"  Median Mantel r: {mantel['mantel_r_all'].median():.3f}")

if len(ecotypes) > 0:
    print(f"\nEcotypes (NB05):")
    print(f"  {(ecotypes['n_clusters'] >= 2).sum()}/{len(ecotypes)} species with >= 2 ecotypes")
    if 'silhouette' in ecotypes:
        print(f"  Median silhouette: {ecotypes['silhouette'].dropna().median():.3f}")

if len(temporal) > 0:
    sig_t = temporal[temporal['fdr'] < 0.05]
    print(f"\nTemporal (NB06):")
    print(f"  {len(sig_t)} species with significant trend")
    if len(sig_t) > 0:
        print(f"  Increasing: {(sig_t['slope'] > 0).sum()}, Decreasing: {(sig_t['slope'] < 0).sum()}")
        print(f"\n  Top 5 increasing:")
        for _, row in sig_t.nlargest(5, 'slope').iterrows():
            print(f"    {row['species_name']}: +{row['slope']:.3f} AMR/year (n={row['n_genomes']})")

print(f"\n" + "="*70)

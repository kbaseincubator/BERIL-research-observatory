#!/usr/bin/env python3
"""
Prepare genus presence fractions for phylogenetic beta-regression robustness check.

Input:
  - data/phylo_d_all_ko.csv: KO metadata with original lambda estimates
  - data/genus_ko_presence_t12_spark.csv: genus-KO presence counts

Output:
  - results/robustness_beta_lambda_input.csv: wide format for R analysis
    columns: ko_id, gene_name, subcategory, evidence_tier, lambda_original,
             genus, n_genomes_with_ko, genus_genome_total, presence_fraction
"""

import os
import pandas as pd
import numpy as np

os.environ['OMP_NUM_THREADS'] = '1'

# Load data
print("Loading phylo_d_all_ko.csv...")
ko_meta = pd.read_csv(
    "data/phylo_d_all_ko.csv",
    dtype={"ko_id": str, "lambda": float, "n_genera": int}
)

print("Loading genus_ko_presence_t12_spark.csv...")
presence = pd.read_csv(
    "data/genus_ko_presence_t12_spark.csv",
    dtype={"genus_lower": "string", "ko": "string", "n_genomes_with_ko": int}
)

# For each KO, compute the total number of genera and total genomes in the tree
print("Computing genus-wise presence fractions...")

# Aggregate to get total genomes per genus per KO
# (in case there are duplicates)
presence = presence.groupby(['genus_lower', 'ko'], as_index=False, sort=False)['n_genomes_with_ko'].sum()

# For each KO, compute: genus_genome_total = max genus size across all KOs
# This approximates the total genome count in the tree for each genus
# (assumes genus sampling is roughly consistent)
genus_total_size = presence.groupby('genus_lower')['n_genomes_with_ko'].max().reset_index()
genus_total_size.columns = ['genus_lower', 'genus_genome_total']

presence = presence.merge(genus_total_size, on='genus_lower')

# Compute presence fraction
presence['presence_fraction'] = (
    presence['n_genomes_with_ko'] / presence['genus_genome_total']
).clip(0.0001, 0.9999)  # Avoid extreme values for beta regression

# Merge with KO metadata
print("Merging with KO metadata...")
presence.columns = ['genus_lower', 'ko_id', 'n_genomes_with_ko', 'genus_genome_total', 'presence_fraction']

result = presence.merge(
    ko_meta[['ko_id', 'gene_name', 'subcategory', 'evidence_tier', 'lambda']],
    on='ko_id',
    how='left'
)

result.columns = [
    'genus', 'ko_id', 'n_genomes_with_ko', 'genus_genome_total',
    'presence_fraction', 'gene_name', 'subcategory', 'evidence_tier', 'lambda_original'
]

# Add arcsine-sqrt transformation
result['y_transformed'] = np.arcsin(np.sqrt(result['presence_fraction']))

# Reorder columns
result = result[
    ['ko_id', 'gene_name', 'subcategory', 'evidence_tier', 'lambda_original',
     'genus', 'n_genomes_with_ko', 'genus_genome_total', 'presence_fraction', 'y_transformed']
]

print(f"Output shape: {result.shape}")
print(f"N unique KOs: {result['ko_id'].nunique()}")
print(f"N unique genera: {result['genus'].nunique()}")
print(f"\nPresence fraction summary:")
print(result['presence_fraction'].describe())

# Save
os.makedirs("results", exist_ok=True)
result.to_csv("results/robustness_beta_lambda_input.csv", index=False)
print("\nSaved to results/robustness_beta_lambda_input.csv")

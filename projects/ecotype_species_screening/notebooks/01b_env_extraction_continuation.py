"""
NB01 Continuation: Environmental Diversity Extraction (Cells 10-14)

Run this after NB01 cells 1-9 have completed and saved:
  - data/species_tree_list.csv
  - data/species_pangenome_stats.csv
  - data/species_phylo_stats.csv

Usage:
  source .venv-berdl/bin/activate
  python projects/ecotype_species_screening/notebooks/01b_env_extraction_continuation.py

Avoids spark.createDataFrame() -- uses SQL subqueries instead (Spark Connect compatible).
"""

import os
import sys
import numpy as np
import pandas as pd
from pyspark.sql import functions as F

# Local Spark Connect
from get_spark_session import get_spark_session

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "../data")
os.makedirs(OUTPUT_PATH, exist_ok=True)

print("=== NB01 Continuation: Environmental Diversity Extraction ===\n")

spark = get_spark_session()
print(f"Spark version: {spark.version}\n")

# Load previously saved species list
tree_species_pd = pd.read_csv(f"{OUTPUT_PATH}/species_tree_list.csv")
print(f"Loaded {len(tree_species_pd)} tree species from species_tree_list.csv")

# ── Cell 8: Explore NMDC schema ──────────────────────────────────────────────
print("\n--- NMDC BioSamples tables ---")
spark.sql("SHOW TABLES IN nmdc_ncbi_biosamples").show(20, truncate=False)

print("\nenv_triads_flattened schema:")
spark.sql("DESCRIBE nmdc_ncbi_biosamples.env_triads_flattened").show(20, truncate=False)

print("\nSample rows:")
spark.sql("SELECT * FROM nmdc_ncbi_biosamples.env_triads_flattened LIMIT 3").show(truncate=False)

# ── Cell 9: Biosamples_flattened env fields ───────────────────────────────────
print("\n--- biosamples_flattened env fields ---")
spark.sql("""
    SELECT accession, isolation_source, env_broad_scale, env_local_scale, env_medium
    FROM nmdc_ncbi_biosamples.biosamples_flattened
    WHERE env_broad_scale IS NOT NULL
    LIMIT 5
""").show(truncate=False)

# ── Cell 10: Skip — genome_biosample_map.csv already saved ───────────────────
print("\n--- Cell 10: Skipped (genome_biosample_map.csv already exists) ---")
genome_biosample_pd = pd.read_csv(f"{OUTPUT_PATH}/genome_biosample_map.csv")
print(f"Loaded {len(genome_biosample_pd):,} rows from genome_biosample_map.csv")

# ── Cell 11: Env diversity per species ───────────────────────────────────────
# env_triads_flattened is EAV: attribute column contains 'env_broad_scale',
# 'env_local_scale', 'env_medium' as values; label contains ENVO term.
# Use conditional COUNT(DISTINCT ...) to pivot in aggregation.
print("\n--- Cell 11: Env diversity per species ---")
env_diversity_df = spark.sql("""
    SELECT
        g.gtdb_species_clade_id,
        COUNT(DISTINCT g.genome_id)                                                          AS n_genomes_total,
        COUNT(DISTINCT CASE WHEN t.accession IS NOT NULL THEN g.genome_id END)               AS n_genomes_with_env,
        COUNT(DISTINCT CASE WHEN t.attribute = 'env_broad_scale' THEN t.label END)           AS n_distinct_env_broad,
        COUNT(DISTINCT CASE WHEN t.attribute = 'env_local_scale' THEN t.label END)           AS n_distinct_env_local,
        COUNT(DISTINCT CASE WHEN t.attribute = 'env_medium'      THEN t.label END)           AS n_distinct_env_medium
    FROM kbase_ke_pangenome.genome g
    JOIN kbase_ke_pangenome.sample s
        ON g.genome_id = s.genome_id
    LEFT JOIN nmdc_ncbi_biosamples.env_triads_flattened t
        ON s.ncbi_biosample_accession_id = t.accession
    WHERE g.gtdb_species_clade_id IN (
        SELECT gtdb_species_clade_id FROM kbase_ke_pangenome.phylogenetic_tree
    )
    GROUP BY g.gtdb_species_clade_id
""")

env_diversity_pd = env_diversity_df.toPandas()
env_diversity_pd['env_coverage_fraction'] = (
    env_diversity_pd['n_genomes_with_env'] / env_diversity_pd['n_genomes_total']
)

print(f"Species with env diversity computed: {len(env_diversity_pd)}")
print(f"Zero env coverage: {(env_diversity_pd['env_coverage_fraction'] == 0).sum()}")
print(env_diversity_pd['env_coverage_fraction'].describe())
print(env_diversity_pd['n_distinct_env_broad'].describe())

# Top env-diverse species
top_env = env_diversity_pd.merge(
    tree_species_pd[['gtdb_species_clade_id', 'GTDB_species']], on='gtdb_species_clade_id', how='left'
).nlargest(10, 'n_distinct_env_broad')
print("\nTop 10 by env_broad diversity:")
print(top_env[['GTDB_species', 'n_genomes_with_env', 'n_distinct_env_broad', 'env_coverage_fraction']].to_string())

# ── Cell 12: Shannon entropy ──────────────────────────────────────────────────
print("\n--- Cell 12: Shannon entropy ---")
env_counts_df = spark.sql("""
    SELECT
        g.gtdb_species_clade_id,
        t.label AS env_broad_label,
        COUNT(DISTINCT g.genome_id) AS n_genomes_in_env
    FROM kbase_ke_pangenome.genome g
    JOIN kbase_ke_pangenome.sample s
        ON g.genome_id = s.genome_id
    JOIN nmdc_ncbi_biosamples.env_triads_flattened t
        ON s.ncbi_biosample_accession_id = t.accession
    WHERE t.attribute = 'env_broad_scale'
      AND g.gtdb_species_clade_id IN (
          SELECT gtdb_species_clade_id FROM kbase_ke_pangenome.phylogenetic_tree
      )
    GROUP BY g.gtdb_species_clade_id, t.label
""")

env_counts_pd = env_counts_df.toPandas()

def shannon_entropy(counts):
    total = counts.sum()
    if total == 0:
        return 0.0
    probs = counts / total
    return float(-np.sum(probs * np.log2(probs + 1e-12)))

entropy_per_species = (
    env_counts_pd
    .groupby('gtdb_species_clade_id')['n_genomes_in_env']
    .apply(shannon_entropy)
    .reset_index()
    .rename(columns={'n_genomes_in_env': 'env_broad_entropy'})
)

print(f"Entropy computed for {len(entropy_per_species)} species with env annotations")
print(entropy_per_species['env_broad_entropy'].describe())

# Rename for consistency with notebook
env_counts_pd = env_counts_pd.rename(columns={'env_broad_label': 'env_broad_scale'})
env_counts_pd.to_csv(f"{OUTPUT_PATH}/species_env_category_counts.csv", index=False)
print(f"Saved species_env_category_counts.csv ({len(env_counts_pd):,} rows)")

# ── Cell 13: Merge env stats and save ─────────────────────────────────────────
print("\n--- Cell 13: Merge and save env stats ---")
species_env_stats = env_diversity_pd.merge(
    entropy_per_species, on='gtdb_species_clade_id', how='left'
).merge(
    tree_species_pd[['gtdb_species_clade_id', 'GTDB_species']], on='gtdb_species_clade_id', how='left'
)
species_env_stats['env_broad_entropy'] = species_env_stats['env_broad_entropy'].fillna(0.0)

species_env_stats.to_csv(f"{OUTPUT_PATH}/species_env_stats.csv", index=False)
print(f"Saved species_env_stats.csv ({len(species_env_stats)} species)")

# ── Cell 14: Sanity check ─────────────────────────────────────────────────────
print("\n=== Output File Inventory ===")
for f in ['species_tree_list.csv', 'species_pangenome_stats.csv', 'species_phylo_stats.csv',
          'species_env_stats.csv', 'species_env_category_counts.csv', 'genome_biosample_map.csv']:
    fpath = os.path.join(OUTPUT_PATH, f)
    if os.path.exists(fpath):
        df = pd.read_csv(fpath)
        print(f"  {f}: {len(df):,} rows")
    else:
        print(f"  MISSING: {f}")

print("\nAll done. Proceed with NB02 locally.")

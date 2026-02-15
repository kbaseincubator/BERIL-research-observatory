#!/usr/bin/env python3
"""
Extract data for co-fitness co-inheritance analysis via Spark Connect.

For each target species/organism, extracts:
1. Genome x gene_cluster presence matrices (binary)
2. Co-fitness pairs from Fitness Browser
3. Gene coordinates for adjacency control
4. Phylogenetic distances between genomes

Usage: python3 src/extract_data.py

Requires BERDL JupyterHub with get_spark_session() available.
"""

import pandas as pd
import numpy as np
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / 'data'
CONS_DIR = PROJECT_DIR.parent / 'conservation_vs_fitness' / 'data'

# Create output subdirectories
for subdir in ['genome_cluster_matrices', 'cofit', 'gene_coords', 'phylo_distances']:
    (DATA_DIR / subdir).mkdir(parents=True, exist_ok=True)

# Target organisms and their species clades (from organism_mapping.tsv)
# Only include organisms with sufficient genomes and auxiliary genes
TARGET_ORGANISMS = {
    'Koxy': 's__Klebsiella_michiganensis--RS_GCF_002925905.1',
    'Btheta': 's__Bacteroides_thetaiotaomicron--RS_GCF_000011065.1',
    'Smeli': 's__Sinorhizobium_meliloti--RS_GCF_017876815.1',
    'RalstoniaUW163': 's__Ralstonia_solanacearum--RS_GCF_002251695.1',
    'Putida': 's__Pseudomonas_E_alloputida--RS_GCF_021282585.1',
    'SyringaeB728a': 's__Pseudomonas_E_syringae_M--RS_GCF_009176725.1',
    'Korea': 's__Sphingomonas_koreensis--RS_GCF_002797435.1',
    'RalstoniaGMI1000': 's__Ralstonia_pseudosolanacearum--RS_GCF_024925465.1',
    'Phaeo': 's__Phaeobacter_inhibens--RS_GCF_000473105.1',
    'Ddia6719': 's__Dickeya_dianthicola--RS_GCF_000365305.1',
    'pseudo3_N2E3': 's__Pseudomonas_E_fluorescens_E--RS_GCF_001307155.1',
}

# ============================================================================
# Connect to Spark
# ============================================================================
print("Connecting to Spark...")
from berdl_notebook_utils.setup_spark_session import get_spark_session
spark = get_spark_session()
print("Spark ready")

# ============================================================================
# Load FB pangenome link table to identify target clusters per species
# ============================================================================
print("\nLoading FB pangenome link table...")
link = pd.read_csv(CONS_DIR / 'fb_pangenome_link.tsv', sep='\t')
link = link[link['orgId'] != 'Dyella79']
print(f"  {len(link):,} gene-cluster links across {link['orgId'].nunique()} organisms")

# Load organism mapping for reference genome IDs
org_mapping = pd.read_csv(CONS_DIR / 'organism_mapping.tsv', sep='\t')
print(f"  {len(org_mapping)} organism-clade mappings")

# ============================================================================
# 1. Extract Genome x Gene Cluster Presence Matrices
# ============================================================================
print("\n=== EXTRACTING GENOME x CLUSTER PRESENCE MATRICES ===")

for orgId, clade_id in TARGET_ORGANISMS.items():
    outpath = DATA_DIR / 'genome_cluster_matrices' / f'{orgId}_presence.tsv'
    if outpath.exists() and outpath.stat().st_size > 0:
        print(f"  [{orgId}] Already cached: {outpath}")
        continue

    print(f"  [{orgId}] Extracting for clade {clade_id}...", flush=True)

    # Get target cluster IDs (clusters that FB genes map to)
    org_clusters = link[link['gtdb_species_clade_id'] == clade_id]['gene_cluster_id'].unique()
    if len(org_clusters) == 0:
        # Try matching by orgId instead
        org_clusters = link[link['orgId'] == orgId]['gene_cluster_id'].unique()
    print(f"    Target clusters: {len(org_clusters)}")

    if len(org_clusters) == 0:
        print(f"    WARNING: No clusters found for {orgId}, skipping")
        continue

    # Register small filter tables for BROADCAST joins
    cluster_df = spark.createDataFrame(
        [(c,) for c in org_clusters], ['gene_cluster_id']
    )
    cluster_df.createOrReplaceTempView('target_clusters')

    genome_ids = spark.sql(f"""
        SELECT genome_id FROM kbase_ke_pangenome.genome
        WHERE gtdb_species_clade_id = '{clade_id}'
    """).toPandas()['genome_id'].tolist()
    genome_df = spark.createDataFrame([(g,) for g in genome_ids], ['genome_id'])
    genome_df.createOrReplaceTempView('target_genomes')

    # Use BROADCAST hints on small filter tables to avoid shuffle joins
    # against the billion-row gene_genecluster_junction and gene tables
    presence = spark.sql("""
        SELECT /*+ BROADCAST(tc), BROADCAST(tg) */
            DISTINCT g.genome_id, j.gene_cluster_id
        FROM kbase_ke_pangenome.gene_genecluster_junction j
        JOIN target_clusters tc ON j.gene_cluster_id = tc.gene_cluster_id
        JOIN kbase_ke_pangenome.gene g ON j.gene_id = g.gene_id
        JOIN target_genomes tg ON g.genome_id = tg.genome_id
    """)

    # Convert to pandas: each row is (genome_id, gene_cluster_id)
    presence_pd = presence.toPandas()
    print(f"    Raw presence rows: {len(presence_pd):,}")

    if len(presence_pd) == 0:
        print(f"    WARNING: No presence data for {orgId}, skipping")
        continue

    # Pivot to binary matrix: rows=genomes, cols=clusters
    presence_pd['present'] = 1
    matrix = presence_pd.pivot_table(
        index='genome_id', columns='gene_cluster_id',
        values='present', fill_value=0, aggfunc='max'
    )

    print(f"    Matrix shape: {matrix.shape[0]} genomes x {matrix.shape[1]} clusters")
    matrix.to_csv(outpath, sep='\t')
    print(f"    Saved: {outpath}")

# ============================================================================
# 2. Extract Co-fitness Pairs
# ============================================================================
print("\n=== EXTRACTING CO-FITNESS PAIRS ===")

for orgId in TARGET_ORGANISMS:
    outpath = DATA_DIR / 'cofit' / f'{orgId}_cofit.tsv'
    if outpath.exists() and outpath.stat().st_size > 0:
        print(f"  [{orgId}] Already cached: {outpath}")
        continue

    print(f"  [{orgId}] Extracting cofit pairs...", end='', flush=True)
    cofit = spark.sql(f"""
        SELECT orgId, locusId, hitId,
               CAST(rank AS INT) as rank,
               CAST(cofit AS FLOAT) as cofit
        FROM kescience_fitnessbrowser.cofit
        WHERE orgId = '{orgId}'
        ORDER BY locusId, CAST(rank AS INT)
    """).toPandas()
    print(f" {len(cofit):,} pairs")

    cofit.to_csv(outpath, sep='\t', index=False)
    print(f"    Saved: {outpath}")

# ============================================================================
# 3. Extract Gene Coordinates
# ============================================================================
print("\n=== EXTRACTING GENE COORDINATES ===")

for orgId in TARGET_ORGANISMS:
    outpath = DATA_DIR / 'gene_coords' / f'{orgId}_coords.tsv'
    if outpath.exists() and outpath.stat().st_size > 0:
        print(f"  [{orgId}] Already cached: {outpath}")
        continue

    print(f"  [{orgId}] Extracting gene coordinates...", end='', flush=True)
    coords = spark.sql(f"""
        SELECT orgId, locusId, scaffoldId,
               CAST(begin AS INT) as begin,
               CAST(end AS INT) as end,
               strand
        FROM kescience_fitnessbrowser.gene
        WHERE orgId = '{orgId}'
        ORDER BY scaffoldId, CAST(begin AS INT)
    """).toPandas()
    print(f" {len(coords):,} genes")

    coords.to_csv(outpath, sep='\t', index=False)
    print(f"    Saved: {outpath}")

# ============================================================================
# 4. Extract Phylogenetic Distances
# ============================================================================
print("\n=== EXTRACTING PHYLOGENETIC DISTANCES ===")

# First, get phylogenetic tree IDs for our target clades
clade_ids = list(TARGET_ORGANISMS.values())
clade_str = "','".join(clade_ids)

tree_mapping = spark.sql(f"""
    SELECT gtdb_species_clade_id, phylogenetic_tree_id
    FROM kbase_ke_pangenome.phylogenetic_tree
    WHERE gtdb_species_clade_id IN ('{clade_str}')
""").toPandas()

print(f"Species with phylogenetic trees: {len(tree_mapping)}/{len(TARGET_ORGANISMS)}")
if len(tree_mapping) > 0:
    print(tree_mapping.to_string(index=False))

for _, row in tree_mapping.iterrows():
    clade_id = row['gtdb_species_clade_id']
    tree_id = row['phylogenetic_tree_id']

    # Find orgId for this clade
    orgId = None
    for oid, cid in TARGET_ORGANISMS.items():
        if cid == clade_id:
            orgId = oid
            break
    if orgId is None:
        continue

    outpath = DATA_DIR / 'phylo_distances' / f'{orgId}_phylo_distances.tsv'
    if outpath.exists() and outpath.stat().st_size > 0:
        print(f"  [{orgId}] Already cached: {outpath}")
        continue

    print(f"  [{orgId}] Extracting phylogenetic distances for tree {tree_id}...",
          end='', flush=True)
    distances = spark.sql(f"""
        SELECT genome1_id, genome2_id, branch_distance
        FROM kbase_ke_pangenome.phylogenetic_tree_distance_pairs
        WHERE phylogenetic_tree_id = '{tree_id}'
    """).toPandas()
    print(f" {len(distances):,} pairs")

    distances.to_csv(outpath, sep='\t', index=False)
    print(f"    Saved: {outpath}")

# Also save which genome is the FB reference strain for each species
# (needed for distance stratification)
ref_genomes = org_mapping[
    org_mapping['orgId'].isin(TARGET_ORGANISMS.keys())
][['orgId', 'gtdb_species_clade_id', 'pg_genome_id']].drop_duplicates()
ref_genomes.to_csv(DATA_DIR / 'phylo_distances' / 'reference_genomes.tsv',
                   sep='\t', index=False)
print(f"\nSaved reference genome mapping: {len(ref_genomes)} rows")

# ============================================================================
# Summary
# ============================================================================
print("\n=== EXTRACTION COMPLETE ===")
print(f"Genome x cluster matrices: {DATA_DIR / 'genome_cluster_matrices'}")
print(f"Co-fitness pairs: {DATA_DIR / 'cofit'}")
print(f"Gene coordinates: {DATA_DIR / 'gene_coords'}")
print(f"Phylogenetic distances: {DATA_DIR / 'phylo_distances'}")

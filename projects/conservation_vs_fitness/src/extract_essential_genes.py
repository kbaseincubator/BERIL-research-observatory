#!/usr/bin/env python3
"""
Extract essential gene data from the Fitness Browser via Spark Connect.

For each organism, identifies putative essential genes (type=1 CDS with no
entries in genefitness). Also extracts gene metadata (begin, end for length)
and SEED/KEGG annotations for functional analysis.

Usage: python3 src/extract_essential_genes.py
"""

import pandas as pd
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / 'data'

# Connect to Spark
print("Connecting to Spark...")
from berdl_notebook_utils.setup_spark_session import get_spark_session
spark = get_spark_session()
print("Spark ready")

# Load organism mapping to get the 34 high-coverage organisms
link_table = pd.read_csv(DATA_DIR / 'fb_pangenome_link.tsv', sep='\t')
mapping = pd.read_csv(DATA_DIR / 'organism_mapping.tsv', sep='\t')

# Count FB genes per organism from FASTA files
fb_fasta_dir = DATA_DIR / 'fb_fastas'
fb_gene_counts = {}
for f in fb_fasta_dir.glob('*.fasta'):
    orgId = f.stem
    n = sum(1 for line in open(f) if line.startswith('>'))
    fb_gene_counts[orgId] = n

# Identify organisms with >=90% DIAMOND coverage
matched_counts = link_table.groupby('orgId').size().to_dict()
high_cov_orgs = []
for orgId in sorted(mapping['orgId'].unique()):
    n_total = fb_gene_counts.get(orgId, 0)
    n_matched = matched_counts.get(orgId, 0)
    pct = (n_matched / n_total * 100) if n_total > 0 else 0
    if pct >= 90:
        high_cov_orgs.append(orgId)

print(f"High-coverage organisms (>=90%): {len(high_cov_orgs)}")

# ============================================================================
# Extract essential gene data
# ============================================================================
print("\n=== EXTRACTING ESSENTIAL GENE DATA ===")

all_genes = []
all_fitness_genes = []

for i, orgId in enumerate(sorted(high_cov_orgs)):
    print(f"  [{i+1}/{len(high_cov_orgs)}] {orgId}...", end='', flush=True)

    # All type=1 (CDS) genes with coordinates for length calculation
    genes = spark.sql(f"""
        SELECT orgId, locusId, scaffoldId,
               CAST(begin AS INT) as gene_begin,
               CAST(end AS INT) as gene_end,
               gene, desc
        FROM kescience_fitnessbrowser.gene
        WHERE orgId = '{orgId}' AND type = '1'
    """).toPandas()

    # Genes with fitness data
    fitness_genes = spark.sql(f"""
        SELECT DISTINCT orgId, locusId
        FROM kescience_fitnessbrowser.genefitness
        WHERE orgId = '{orgId}'
    """).toPandas()

    genes['has_fitness'] = genes['locusId'].isin(fitness_genes['locusId'].values)
    genes['is_essential'] = ~genes['has_fitness']
    genes['gene_length'] = abs(genes['gene_end'] - genes['gene_begin']) + 1

    n_essential = genes['is_essential'].sum()
    n_total = len(genes)
    print(f" {n_total} genes, {n_essential} essential ({n_essential/n_total*100:.1f}%)")

    all_genes.append(genes)

essential_df = pd.concat(all_genes, ignore_index=True)
output_path = DATA_DIR / 'essential_genes.tsv'
essential_df.to_csv(output_path, sep='\t', index=False)
print(f"\nSaved: {output_path} ({len(essential_df):,} genes)")

# ============================================================================
# Extract SEED annotations for all organisms
# ============================================================================
print("\n=== EXTRACTING SEED ANNOTATIONS ===")

all_seed = []
for i, orgId in enumerate(sorted(high_cov_orgs)):
    print(f"  [{i+1}/{len(high_cov_orgs)}] {orgId}...", end='', flush=True)
    seed = spark.sql(f"""
        SELECT orgId, locusId, seed_desc
        FROM kescience_fitnessbrowser.seedannotation
        WHERE orgId = '{orgId}'
    """).toPandas()
    all_seed.append(seed)
    print(f" {len(seed)} annotations")

seed_df = pd.concat(all_seed, ignore_index=True)
seed_path = DATA_DIR / 'seed_annotations.tsv'
seed_df.to_csv(seed_path, sep='\t', index=False)
print(f"Saved: {seed_path} ({len(seed_df):,} annotations)")

# ============================================================================
# Extract KEGG annotations
# ============================================================================
print("\n=== EXTRACTING KEGG ANNOTATIONS ===")

all_kegg = []
for i, orgId in enumerate(sorted(high_cov_orgs)):
    print(f"  [{i+1}/{len(high_cov_orgs)}] {orgId}...", end='', flush=True)
    kegg = spark.sql(f"""
        SELECT bk.orgId, bk.locusId, km.kgroup, kd.desc as kegg_desc
        FROM kescience_fitnessbrowser.besthitkegg bk
        JOIN kescience_fitnessbrowser.keggmember km
            ON bk.keggOrg = km.keggOrg AND bk.keggId = km.keggId
        JOIN kescience_fitnessbrowser.kgroupdesc kd
            ON km.kgroup = kd.kgroup
        WHERE bk.orgId = '{orgId}'
    """).toPandas()
    all_kegg.append(kegg)
    print(f" {len(kegg)} annotations")

kegg_df = pd.concat(all_kegg, ignore_index=True)
kegg_path = DATA_DIR / 'kegg_annotations.tsv'
kegg_df.to_csv(kegg_path, sep='\t', index=False)
print(f"Saved: {kegg_path} ({len(kegg_df):,} annotations)")

# ============================================================================
# Extract pangenome metadata for stratification
# ============================================================================
print("\n=== EXTRACTING PANGENOME METADATA ===")

# Get unique resolved clades from the link table
resolved_clades = link_table.drop_duplicates('orgId')[['orgId', 'gtdb_species_clade_id']]
resolved_clades = resolved_clades[resolved_clades['orgId'].isin(high_cov_orgs)]
unique_clades = resolved_clades['gtdb_species_clade_id'].unique().tolist()
clade_str = "','".join(unique_clades)

pangenome_meta = spark.sql(f"""
    SELECT p.gtdb_species_clade_id,
           p.no_genomes, p.no_core, p.no_aux_genome,
           p.no_singleton_gene_clusters, p.no_gene_clusters,
           s.GTDB_species, s.GTDB_taxonomy,
           s.mean_intra_species_ANI
    FROM kbase_ke_pangenome.pangenome p
    JOIN kbase_ke_pangenome.gtdb_species_clade s
        ON p.gtdb_species_clade_id = s.gtdb_species_clade_id
    WHERE p.gtdb_species_clade_id IN ('{clade_str}')
""").toPandas()

pangenome_path = DATA_DIR / 'pangenome_metadata.tsv'
pangenome_meta.to_csv(pangenome_path, sep='\t', index=False)
print(f"Saved: {pangenome_path} ({len(pangenome_meta)} clades)")

print("\n=== EXTRACTION COMPLETE ===")
print(f"Essential genes: {output_path}")
print(f"SEED annotations: {seed_path}")
print(f"KEGG annotations: {kegg_path}")
print(f"Pangenome metadata: {pangenome_path}")

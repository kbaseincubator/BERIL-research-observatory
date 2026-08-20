#!/usr/bin/env python3
"""
Build KO presence/absence matrices from all available genome databases,
spatially join PF1 metal scores, and cache as parquet.

Databases:
  1. arkinlab.spire eggnog (6,270 MAGs)
  2. ke_pangenome (83K genomes via gene→cluster→eggnog)
  3. carbon_source_phenotypes (1,097 genomes)
  4. SMAG gene products (38K MAGs, gene-level not KO)
"""
import os
for var in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ.setdefault(var, '1')

import numpy as np
import pandas as pd
from pathlib import Path
from scipy.spatial import cKDTree
import sys

DATA = Path('/home/hmacgregor/BERIL-research-observatory/projects/comprehensive_metal_ecology/data')
OUTDIR = DATA / 'db_ko_matrices'
OUTDIR.mkdir(exist_ok=True)

# PF1 metal scores from MGnify parquet (Science 2025 HQ grid)
sci_grid = pd.read_csv(DATA / 'env_cache' / 'science2025_grid.csv')
sci_grid = sci_grid.dropna(subset=['lat', 'lon'])
sci_tree = cKDTree(sci_grid[['lat', 'lon']].values)

METALS = ['sci_hq_As', 'sci_hq_Cd', 'sci_hq_Co', 'sci_hq_Cr', 'sci_hq_Cu', 'sci_hq_Ni', 'sci_hq_Pb']
# PF1 names to match MGnify/SPIRE convention
PF1_MAP = {
    'sci_hq_As': 'PF1_As', 'sci_hq_Cd': 'PF1_Cd', 'sci_hq_Cr': 'PF1_Cr',
    'sci_hq_Cu': 'PF1_Cu', 'sci_hq_Ni': 'PF1_Ni', 'sci_hq_Pb': 'PF1_Pb',
}

# Env covariates
env_full = pd.read_csv(DATA / 'genome_env_covariates_full.csv')
env_locs = env_full[['latitude', 'longitude']].dropna()
env_tree = cKDTree(env_locs.values)
ENV_COLS = ['ph_h2o', 'organic_carbon_density', 'clay_pct',
            'mean_annual_temp_C', 'mean_annual_precip_mm',
            'elevation_m', 'litho_mafic_score']


def assign_metals_and_env(df, lat_col='latitude', lon_col='longitude'):
    """Assign PF1 metal scores and env covariates via KD-tree."""
    locs = df[[lat_col, lon_col]].values

    # Metals from Science 2025 HQ
    dd, ii = sci_tree.query(locs, k=1)
    for sci_col, pf1_col in PF1_MAP.items():
        df[pf1_col] = sci_grid[sci_col].values[ii]
        df.loc[dd > 0.5, pf1_col] = np.nan

    # We don't have PF1_Hg in sci grid — check MGnify for Hg source
    # For now skip Hg for non-MGnify databases

    # Env covariates from MGnify grid
    dd2, ii2 = env_tree.query(locs, k=1)
    for c in ENV_COLS:
        if c in env_full.columns:
            df[c] = env_full[c].values[ii2]
            df.loc[dd2 > 0.5, c] = np.nan

    return df


from berdl_notebook_utils import get_spark_session
spark = get_spark_session()


# ════════════════════════════════════════════════════════════════════════
# 1. arkinlab.spire eggnog (6,270 MAGs)
# ════════════════════════════════════════════════════════════════════════
print("\n" + "="*80)
print("DATABASE 1: arkinlab.spire eggnog")
print("="*80 + "\n")

spire_ko = spark.sql("""
    SELECT e.mag_id AS genome_id,
           REPLACE(e.KEGG_ko, 'ko:', '') AS ko_id,
           mc.latitude, mc.longitude,
           gm.genome_size, gm.genus, gm.phylum
    FROM arkinlab.spire.eggnog_annotations_spire e
    JOIN refdata.spire.mag_coordinates mc ON e.mag_id = mc.mag_id
    JOIN refdata.spire.genome_metadata gm ON e.mag_id = gm.mag_id
    WHERE e.KEGG_ko IS NOT NULL
      AND e.KEGG_ko != ''
      AND e.KEGG_ko != '-'
      AND mc.latitude IS NOT NULL
""").toPandas()

print(f"  Raw rows: {len(spire_ko):,}")
print(f"  Unique MAGs: {spire_ko.genome_id.nunique():,}")
print(f"  Unique KOs: {spire_ko.ko_id.nunique():,}")

if len(spire_ko) > 0:
    # Deduplicate (genome_id, ko_id) → present=1
    spire_ko = spire_ko.drop_duplicates(subset=['genome_id', 'ko_id'])
    spire_ko['present'] = 1

    # Get genome metadata
    genome_meta = spire_ko.groupby('genome_id').first()[
        ['latitude', 'longitude', 'genome_size', 'genus', 'phylum']
    ].reset_index()
    genome_meta = assign_metals_and_env(genome_meta)

    # Merge metadata back
    spire_out = spire_ko[['genome_id', 'ko_id', 'present']].merge(
        genome_meta, on='genome_id')

    spire_out.to_parquet(OUTDIR / 'arkinlab_spire_ko_matrix.parquet', index=False)
    print(f"  Saved: {len(spire_out):,} rows, {spire_out.genome_id.nunique():,} genomes")
    print(f"  Genera: {genome_meta.genus.nunique()}, usable (≥8): "
          f"{(genome_meta.genus.value_counts() >= 8).sum()}")


# ════════════════════════════════════════════════════════════════════════
# 2. ke_pangenome (83K genomes)
# ════════════════════════════════════════════════════════════════════════
print("\n" + "="*80)
print("DATABASE 2: ke_pangenome (via gene_cluster → eggnog)")
print("="*80 + "\n")

# Strategy: first get all gene_cluster_ids with KEGG_ko annotations,
# then find which genomes have genes in those clusters.
# This avoids joining the full billion-row gene table.

print("  Step 1: Get gene_clusters with KO annotations...")
ko_clusters = spark.sql("""
    SELECT DISTINCT query_name AS gene_cluster_id,
           REPLACE(KEGG_ko, 'ko:', '') AS ko_id
    FROM kbase.ke_pangenome.eggnog_mapper_annotations
    WHERE KEGG_ko IS NOT NULL AND KEGG_ko != '' AND KEGG_ko != '-'
""").toPandas()
print(f"    Gene clusters with KO: {len(ko_clusters):,}")
print(f"    Unique KOs: {ko_clusters.ko_id.nunique():,}")

print("  Step 2: Get spatial genomes...")
spatial_genomes = spark.sql("""
    SELECT genome_id, cleaned_lat AS latitude, cleaned_lon AS longitude,
           genus, phylum
    FROM kbase.ke_pangenome.alphaearth_embeddings_all_years
    WHERE cleaned_lat IS NOT NULL AND cleaned_lon IS NOT NULL
""").toPandas()
print(f"    Spatial genomes: {len(spatial_genomes):,}")

# Get genome_size from gtdb_metadata
print("  Step 2b: Get genome sizes...")
try:
    genome_sizes = spark.sql("""
        SELECT genome_id, TRY_CAST(genome_size AS BIGINT) AS genome_size
        FROM kbase.ke_pangenome.gtdb_metadata
        WHERE genome_size IS NOT NULL
    """).toPandas()
    spatial_genomes = spatial_genomes.merge(genome_sizes, on='genome_id', how='left')
    print(f"    With genome_size: {spatial_genomes.genome_size.notna().sum():,}")
except Exception as e:
    print(f"    genome_size fetch failed: {e}")
    spatial_genomes['genome_size'] = np.nan

spatial_ids = set(spatial_genomes.genome_id)

print("  Step 3: Map genomes → gene_clusters (batched Spark query)...")
# This is the expensive part. We query gene_genecluster_junction
# but only for genes belonging to spatial genomes.
# Since gene table has genome_id, use it as bridge.

# Do this in batches of genome_ids to avoid Spark OOM
batch_size = 5000
genome_list = sorted(spatial_ids)
all_genome_ko = []

for batch_start in range(0, len(genome_list), batch_size):
    batch = genome_list[batch_start:batch_start + batch_size]
    batch_str = "','".join(batch)

    if (batch_start // batch_size) % 5 == 0:
        print(f"    Batch {batch_start//batch_size + 1}/{len(genome_list)//batch_size + 1}...", flush=True)

    try:
        batch_result = spark.sql(f"""
            SELECT DISTINCT g.genome_id, ggc.gene_cluster_id
            FROM kbase.ke_pangenome.gene g
            JOIN kbase.ke_pangenome.gene_genecluster_junction ggc
                ON g.gene_id = ggc.gene_id
            WHERE g.genome_id IN ('{batch_str}')
        """).toPandas()

        # Map to KOs
        batch_ko = batch_result.merge(ko_clusters, on='gene_cluster_id')
        batch_ko = batch_ko[['genome_id', 'ko_id']].drop_duplicates()
        all_genome_ko.append(batch_ko)
    except Exception as e:
        print(f"    Batch error: {str(e)[:100]}")
        continue

if all_genome_ko:
    kp_ko = pd.concat(all_genome_ko, ignore_index=True).drop_duplicates()
    kp_ko['present'] = 1
    print(f"  Total genome-KO pairs: {len(kp_ko):,}")
    print(f"  Genomes with KOs: {kp_ko.genome_id.nunique():,}")

    # Merge metadata
    kp_meta = spatial_genomes.copy()
    kp_meta = assign_metals_and_env(kp_meta)

    kp_out = kp_ko.merge(kp_meta, on='genome_id')
    kp_out.to_parquet(OUTDIR / 'ke_pangenome_ko_matrix.parquet', index=False)
    print(f"  Saved: {len(kp_out):,} rows")
else:
    print("  ERROR: No genome-KO pairs found!")


# ════════════════════════════════════════════════════════════════════════
# 3. Carbon source phenotypes (1,097 genomes)
# ════════════════════════════════════════════════════════════════════════
print("\n" + "="*80)
print("DATABASE 3: carbon_source_phenotypes")
print("="*80 + "\n")

cs_ko = spark.sql("""
    SELECT genomeid AS genome_id, koid AS ko_id
    FROM globalusers.carbon_source_phenotypes.kofam_annotation_table
    WHERE koid IS NOT NULL
""").toPandas()
print(f"  Raw rows: {len(cs_ko):,}")
print(f"  Unique genomes: {cs_ko.genome_id.nunique():,}")
print(f"  Unique KOs: {cs_ko.ko_id.nunique():,}")

# Get taxonomy from genome_table → need to link to ke_pangenome for lat/lon
cs_genomes = spark.sql("""
    SELECT genomeid AS genome_id
    FROM globalusers.carbon_source_phenotypes.genome_table
""").toPandas()

# Try to get taxonomy
try:
    cs_tax = spark.sql("""
        SELECT genomeid AS genome_id, phylum, class, `order`, family, genus, species
        FROM globalusers.carbon_source_phenotypes.taxonomy_table
    """).toPandas()
    cs_genomes = cs_genomes.merge(cs_tax, on='genome_id', how='left')
    print(f"  With taxonomy: {cs_genomes.genus.notna().sum():,}")
except Exception as e:
    print(f"  Taxonomy fetch failed: {e}")

# Link to ke_pangenome for lat/lon
# genome_ids in carbon_source may overlap with ke_pangenome
overlap = set(cs_genomes.genome_id) & spatial_ids
print(f"  Overlap with ke_pangenome spatial: {len(overlap):,}")

if len(overlap) > 10:
    cs_spatial = cs_genomes[cs_genomes.genome_id.isin(overlap)].merge(
        spatial_genomes[['genome_id', 'latitude', 'longitude', 'genome_size']],
        on='genome_id', how='left')
    cs_spatial = assign_metals_and_env(cs_spatial)

    cs_ko_spatial = cs_ko[cs_ko.genome_id.isin(overlap)].drop_duplicates()
    cs_ko_spatial['present'] = 1
    cs_out = cs_ko_spatial.merge(cs_spatial, on='genome_id')
    cs_out.to_parquet(OUTDIR / 'carbon_source_ko_matrix.parquet', index=False)
    print(f"  Saved: {len(cs_out):,} rows, {cs_out.genome_id.nunique():,} genomes")
else:
    print("  Too few overlapping genomes with spatial data")


# ════════════════════════════════════════════════════════════════════════
# 4. SMAG gene products (38K MAGs)
# ════════════════════════════════════════════════════════════════════════
print("\n" + "="*80)
print("DATABASE 4: SMAG (gene-level analysis)")
print("="*80 + "\n")

# SMAG has product names in smag_eggnog, not KO IDs.
# Extract mag_id from the ID field (format: MAG_ID_contig.gene)
# and use Eggnog Desc + Product for gene identification

# First check the ID format more carefully
smag_sample = spark.sql("""
    SELECT ID, Product, Eggnog, Eggnog_Desc
    FROM arkinlab.smag.smag_eggnog
    WHERE Product IS NOT NULL AND Product != 'nan'
    LIMIT 20
""").toPandas()
print("  SMAG eggnog sample:")
for _, r in smag_sample.head(5).iterrows():
    print(f"    ID={r.ID}  Product={r.Product}  Eggnog_Desc={str(r.Eggnog_Desc)[:60]}")

# The ID format is MAG_ID_contig.pos.frame — extract mag_id
# Pattern: everything before the last _contigNNNN part
# Actually: TARA_MED_95_MAG_00519_000000011713.4.3
# mag_id = TARA_MED_95_MAG_00519
# Let's see if we can find these in mag_sample_map

smag_mag_ids = spark.sql("""
    SELECT DISTINCT mag_id FROM refdata.smag.mag_sample_map
    WHERE lat IS NOT NULL LIMIT 10
""").toPandas()
print(f"\n  SMAG mag_id format: {smag_mag_ids.mag_id.tolist()[:5]}")

# The eggnog IDs have the MAG name embedded. We need to extract it.
# For now, count how many products are metal-related
metal_products = spark.sql("""
    SELECT Product, COUNT(*) as n
    FROM arkinlab.smag.smag_eggnog
    WHERE Product IS NOT NULL AND Product != 'nan'
      AND (LOWER(Product) LIKE '%mercury%' OR LOWER(Product) LIKE '%arsenic%'
           OR LOWER(Product) LIKE '%copper%' OR LOWER(Product) LIKE '%zinc%'
           OR LOWER(Product) LIKE '%nickel%' OR LOWER(Product) LIKE '%cadmium%'
           OR LOWER(Product) LIKE '%lead%' OR LOWER(Product) LIKE '%chromat%'
           OR LOWER(Product) LIKE '%merp%' OR LOWER(Product) LIKE '%kdp%'
           OR LOWER(Product) LIKE '%hyp%' OR LOWER(Product) LIKE '%mgt%'
           OR LOWER(Product) LIKE '%aquaporin%' OR LOWER(Product) LIKE '%transposase%')
    GROUP BY Product
    ORDER BY n DESC
    LIMIT 20
""").toPandas()
print(f"\n  Metal-related products in SMAG eggnog:")
for _, r in metal_products.iterrows():
    print(f"    {r.Product[:60]:60s} n={r.n:,}")

total_genes = spark.sql("SELECT COUNT(*) FROM arkinlab.smag.smag_eggnog").collect()[0][0]
print(f"\n  Total SMAG eggnog rows: {total_genes:,}")

# SMAG gene-level analysis requires mapping IDs to MAGs then to lat/lon
# This is complex — save for a separate script
print("  SMAG gene-level build deferred (needs MAG ID extraction from gene IDs)")


spark.stop()
print("\n" + "="*80)
print("DONE — KO matrices built and saved to", OUTDIR)
print("="*80)

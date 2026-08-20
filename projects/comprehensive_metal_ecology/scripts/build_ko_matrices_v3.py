#!/usr/bin/env python3
"""
Build KO matrices v3 — fixed OOM for ke_pangenome by splitting the join:
  1. Pull ko_clusters (gene_cluster_id → ko_id) to Python
  2. Batch genome→gene→junction in Spark (2-table join, not 3)
  3. Join with ko_clusters locally

Also checks carbon_source for independent lat/lon.
"""
import os
for var in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ.setdefault(var, '1')

import numpy as np
import pandas as pd
from pathlib import Path
from scipy.spatial import cKDTree
import gc

DATA = Path('/home/hmacgregor/BERIL-research-observatory/projects/comprehensive_metal_ecology/data')
OUTDIR = DATA / 'db_ko_matrices'
OUTDIR.mkdir(exist_ok=True)
PROJECTS = Path('/home/hmacgregor/BERIL-research-observatory/projects')

# ── Metal grid (CSU) ──────────────────────────────────────────────────
print("Loading CSU metal mobility grid...", flush=True)
csu_grid = pd.read_parquet(PROJECTS / 'microbeatlas_metal_ecology' / 'data' / 'csu_metal_mobility_grid.parquet')
csu_tree = cKDTree(csu_grid[['lat', 'lon']].values)
METAL_COLS = ['PF1_As', 'PF1_Cd', 'PF1_Cr', 'PF1_Cu', 'PF1_Hg', 'PF1_Pb']
print(f"  CSU grid: {len(csu_grid):,} cells")

# ── Env covariates ────────────────────────────────────────────────────
env_full = pd.read_csv(DATA / 'genome_env_covariates_full.csv')
env_locs = env_full[['latitude', 'longitude']].dropna()
env_tree = cKDTree(env_locs.values)
ENV_COLS = ['ph_h2o', 'organic_carbon_density', 'clay_pct',
            'mean_annual_temp_C', 'mean_annual_precip_mm',
            'elevation_m', 'litho_mafic_score']


def assign_metals_and_env(df, lat_col='latitude', lon_col='longitude'):
    for c in METAL_COLS + ENV_COLS:
        df[c] = np.nan
    valid = df[lat_col].notna() & df[lon_col].notna()
    if valid.sum() == 0:
        return df
    locs = df.loc[valid, [lat_col, lon_col]].values
    dd, ii = csu_tree.query(locs, k=1)
    for c in METAL_COLS:
        vals = csu_grid[c].values[ii].copy()
        vals[dd > 0.5] = np.nan
        df.loc[valid, c] = vals
    dd2, ii2 = env_tree.query(locs, k=1)
    for c in ENV_COLS:
        if c in env_full.columns:
            vals2 = env_full[c].values[ii2].copy()
            vals2[dd2 > 0.5] = np.nan
            df.loc[valid, c] = vals2
    return df


from berdl_notebook_utils import get_spark_session
spark = get_spark_session()


# ════════════════════════════════════════════════════════════════════════
# ke_pangenome — split join strategy
# ════════════════════════════════════════════════════════════════════════
if not (OUTDIR / 'ke_pangenome_ko_matrix.parquet').exists():
    print("\n" + "="*80)
    print("DATABASE: ke_pangenome (split-join strategy)")
    print("="*80 + "\n", flush=True)

    # Step 1: Pull all gene_cluster → KO mappings to Python
    print("  Step 1: Getting gene_cluster → KO mappings...", flush=True)
    ko_clusters = spark.sql("""
        SELECT DISTINCT query_name AS gene_cluster_id,
               REPLACE(KEGG_ko, 'ko:', '') AS ko_id
        FROM kbase.ke_pangenome.eggnog_mapper_annotations
        WHERE KEGG_ko IS NOT NULL AND KEGG_ko != '' AND KEGG_ko != '-'
    """).toPandas()
    print(f"    Gene clusters with KO: {len(ko_clusters):,}")
    print(f"    Unique KOs: {ko_clusters.ko_id.nunique():,}")
    gc_set = set(ko_clusters.gene_cluster_id)

    # Step 2: Get spatial genomes
    print("  Step 2: Getting spatial genomes...", flush=True)
    spatial_genomes = spark.sql("""
        SELECT genome_id, cleaned_lat AS latitude, cleaned_lon AS longitude,
               genus, phylum
        FROM kbase.ke_pangenome.alphaearth_embeddings_all_years
        WHERE cleaned_lat IS NOT NULL AND cleaned_lon IS NOT NULL
    """).toPandas()
    print(f"    {len(spatial_genomes):,} genomes with lat/lon")

    # Get genome_size from gtdb_metadata (accession column maps to genome_id)
    try:
        gsizes = spark.sql("""
            SELECT accession AS genome_id,
                   TRY_CAST(genome_size AS BIGINT) AS genome_size
            FROM kbase.ke_pangenome.gtdb_metadata
            WHERE genome_size IS NOT NULL
        """).toPandas()
        spatial_genomes = spatial_genomes.merge(gsizes, on='genome_id', how='left')
        print(f"    With genome_size: {spatial_genomes.genome_size.notna().sum():,}")
    except Exception as e:
        print(f"    genome_size fetch failed: {e}")
        spatial_genomes['genome_size'] = np.nan

    spatial_genomes = assign_metals_and_env(spatial_genomes)
    spatial_ids = set(spatial_genomes.genome_id)

    # Step 3: Batch genome → gene → junction, then join with ko_clusters locally
    print("  Step 3: Batched genome → gene → junction queries...", flush=True)
    genome_list = sorted(spatial_ids)
    batch_size = 2000
    all_genome_ko = []

    for batch_start in range(0, len(genome_list), batch_size):
        batch = genome_list[batch_start:batch_start + batch_size]
        batch_num = batch_start // batch_size + 1
        total_batches = (len(genome_list) + batch_size - 1) // batch_size

        if batch_num % 5 == 1:
            n_so_far = sum(len(x) for x in all_genome_ko)
            print(f"    Batch {batch_num}/{total_batches}, "
                  f"{n_so_far:,} genome-cluster pairs so far...", flush=True)

        batch_str = "','".join(batch)
        try:
            chunk = spark.sql(f"""
                SELECT DISTINCT g.genome_id, ggc.gene_cluster_id
                FROM kbase.ke_pangenome.gene g
                JOIN kbase.ke_pangenome.gene_genecluster_junction ggc
                    ON g.gene_id = ggc.gene_id
                WHERE g.genome_id IN ('{batch_str}')
            """).toPandas()

            # Filter to clusters that have KO annotations
            chunk = chunk[chunk.gene_cluster_id.isin(gc_set)]
            if len(chunk) > 0:
                # Map to KOs
                chunk_ko = chunk.merge(ko_clusters, on='gene_cluster_id')
                chunk_ko = chunk_ko[['genome_id', 'ko_id']].drop_duplicates()
                all_genome_ko.append(chunk_ko)
        except Exception as e:
            print(f"    Batch {batch_num} error: {str(e)[:100]}")
            continue

    if all_genome_ko:
        kp_ko = pd.concat(all_genome_ko, ignore_index=True).drop_duplicates()
        kp_ko['present'] = 1
        print(f"\n  Total genome-KO pairs: {len(kp_ko):,}")
        print(f"  Genomes with KOs: {kp_ko.genome_id.nunique():,}")
        print(f"  Unique KOs: {kp_ko.ko_id.nunique():,}")

        kp_out = kp_ko.merge(spatial_genomes, on='genome_id')
        kp_out.to_parquet(OUTDIR / 'ke_pangenome_ko_matrix.parquet', index=False)
        print(f"  Saved: {kp_out.genome_id.nunique():,} genomes")
        usable = (spatial_genomes[spatial_genomes.genome_id.isin(
            set(kp_ko.genome_id))].genus.value_counts() >= 8).sum()
        print(f"  Usable genera (≥8): {usable}")
    else:
        print("  ERROR: No KO pairs found!")
else:
    print("\nSkipping ke_pangenome (already exists)")
    spatial_genomes = None


# ════════════════════════════════════════════════════════════════════════
# carbon_source_phenotypes — check for independent lat/lon
# ════════════════════════════════════════════════════════════════════════
if not (OUTDIR / 'carbon_source_ko_matrix.parquet').exists():
    print("\n" + "="*80)
    print("DATABASE: carbon_source_phenotypes")
    print("="*80 + "\n", flush=True)

    # Check all tables in carbon_source_phenotypes
    tables = spark.sql("SHOW TABLES IN globalusers.carbon_source_phenotypes").toPandas()
    print(f"  Tables: {tables.tableName.tolist()}")

    # Look for location data
    for t in tables.tableName:
        try:
            cols = spark.sql(f"DESCRIBE globalusers.carbon_source_phenotypes.{t}").toPandas()
            col_names = cols.col_name.tolist()
            loc_cols = [c for c in col_names if c.lower() in
                       ('lat', 'latitude', 'lon', 'longitude', 'lng', 'location')]
            if loc_cols:
                print(f"  Table {t} has location columns: {loc_cols}")
                sample = spark.sql(
                    f"SELECT {', '.join(loc_cols)} FROM globalusers.carbon_source_phenotypes.{t} "
                    f"WHERE {loc_cols[0]} IS NOT NULL LIMIT 5").toPandas()
                print(f"    Sample: {sample.to_dict('records')[:3]}")
        except:
            pass

    # Check genome_table for any linkable IDs
    try:
        gt_cols = spark.sql("DESCRIBE globalusers.carbon_source_phenotypes.genome_table").toPandas()
        print(f"\n  genome_table columns: {gt_cols.col_name.tolist()}")
        gt_sample = spark.sql("""
            SELECT * FROM globalusers.carbon_source_phenotypes.genome_table LIMIT 3
        """).toPandas()
        print(f"  Sample rows:")
        for _, r in gt_sample.iterrows():
            print(f"    {dict(r)}")
    except Exception as e:
        print(f"  genome_table error: {e}")

    # Check if genome_ids match NCBI taxids that we can link to GTDB
    cs_ko = spark.sql("""
        SELECT genomeid AS genome_id, koid AS ko_id
        FROM globalusers.carbon_source_phenotypes.kofam_annotation_table
        WHERE koid IS NOT NULL
    """).toPandas()
    print(f"\n  KO rows: {len(cs_ko):,}, genomes: {cs_ko.genome_id.nunique():,}")
    print(f"  Sample genome_ids: {cs_ko.genome_id.unique()[:10].tolist()}")

    # Try matching via GTDB ncbi_genbank_assembly_accession or ncbi_wgs_master
    # The "242606.24" format looks like IMG genome_id
    # Try to find if these are in ke_pangenome gene table (gene_id references these)
    sample_ids = cs_ko.genome_id.unique()[:20].tolist()
    sample_str = "','".join(str(s) for s in sample_ids)

    print("\n  Checking if genome_ids appear in ke_pangenome gene table...", flush=True)
    try:
        check = spark.sql(f"""
            SELECT DISTINCT genome_id
            FROM kbase.ke_pangenome.gene
            WHERE genome_id IN ('{sample_str}')
            LIMIT 5
        """).toPandas()
        print(f"    Matches in gene table: {len(check)}")
        if len(check) > 0:
            print(f"    Matched: {check.genome_id.tolist()}")
    except Exception as e:
        print(f"    gene table check failed: {str(e)[:100]}")

    # Check alphaearth_embeddings for these IDs
    try:
        check2 = spark.sql(f"""
            SELECT DISTINCT genome_id
            FROM kbase.ke_pangenome.alphaearth_embeddings_all_years
            WHERE genome_id IN ('{sample_str}')
            LIMIT 5
        """).toPandas()
        print(f"    Matches in alphaearth: {len(check2)}")
    except Exception as e:
        print(f"    alphaearth check failed: {str(e)[:100]}")

    print("\n  Carbon source phenotypes: no spatial link found")
else:
    print("\nSkipping carbon_source (already exists)")


spark.stop()
print("\n" + "="*80)
print("DONE")
print("="*80)

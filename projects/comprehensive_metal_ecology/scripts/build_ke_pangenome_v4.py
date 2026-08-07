#!/usr/bin/env python3
"""
Build ke_pangenome KO matrix — v4: very small batches (300 genomes),
full 3-way join in Spark to minimize result size (only genome_id + ko_id).
Checkpoints every 5 batches to allow resume.
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
CHECKPOINT = OUTDIR / 'ke_pangenome_checkpoint.parquet'

# ── Metal grid (CSU) ──────────────────────────────────────────────────
print("Loading CSU metal mobility grid...", flush=True)
csu_grid = pd.read_parquet(PROJECTS / 'microbeatlas_metal_ecology' / 'data' / 'csu_metal_mobility_grid.parquet')
csu_tree = cKDTree(csu_grid[['lat', 'lon']].values)
METAL_COLS = ['PF1_As', 'PF1_Cd', 'PF1_Cr', 'PF1_Cu', 'PF1_Hg', 'PF1_Pb']

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


if (OUTDIR / 'ke_pangenome_ko_matrix.parquet').exists():
    print("ke_pangenome_ko_matrix.parquet already exists — exiting")
    exit(0)

from berdl_notebook_utils import get_spark_session
spark = get_spark_session()

# Step 1: Get spatial genomes
print("\nStep 1: Getting spatial genomes...", flush=True)
spatial_genomes = spark.sql("""
    SELECT genome_id, cleaned_lat AS latitude, cleaned_lon AS longitude,
           genus, phylum
    FROM kbase.ke_pangenome.alphaearth_embeddings_all_years
    WHERE cleaned_lat IS NOT NULL AND cleaned_lon IS NOT NULL
""").toPandas()
print(f"  {len(spatial_genomes):,} genomes with lat/lon")

# Get genome_size
try:
    gsizes = spark.sql("""
        SELECT accession AS genome_id,
               TRY_CAST(genome_size AS BIGINT) AS genome_size
        FROM kbase.ke_pangenome.gtdb_metadata
        WHERE genome_size IS NOT NULL
    """).toPandas()
    spatial_genomes = spatial_genomes.merge(gsizes, on='genome_id', how='left')
    print(f"  With genome_size: {spatial_genomes.genome_size.notna().sum():,}")
except:
    spatial_genomes['genome_size'] = np.nan

spatial_genomes = assign_metals_and_env(spatial_genomes)

# Step 2: Check for checkpoint
genome_list = sorted(spatial_genomes.genome_id.unique())
all_genome_ko = []
start_batch = 0

if CHECKPOINT.exists():
    print("\n  Resuming from checkpoint...", flush=True)
    prev = pd.read_parquet(CHECKPOINT)
    all_genome_ko.append(prev)
    done_ids = set(prev.genome_id)
    genome_list = [g for g in genome_list if g not in done_ids]
    print(f"  Checkpoint: {len(prev):,} pairs, {prev.genome_id.nunique():,} genomes done")
    print(f"  Remaining: {len(genome_list):,} genomes")

# Step 3: Batch queries — full 3-way join, small batches
batch_size = 300
total_batches = (len(genome_list) + batch_size - 1) // batch_size
print(f"\nStep 3: Processing {len(genome_list):,} genomes in {total_batches} batches of {batch_size}...",
      flush=True)

errors = 0
for batch_num in range(total_batches):
    batch_start = batch_num * batch_size
    batch = genome_list[batch_start:batch_start + batch_size]

    if (batch_num + 1) % 10 == 0 or batch_num == 0:
        n_so_far = sum(len(x) for x in all_genome_ko)
        print(f"  Batch {batch_num+1}/{total_batches}, {n_so_far:,} pairs so far...", flush=True)

    batch_str = "','".join(batch)
    try:
        chunk = spark.sql(f"""
            SELECT DISTINCT g.genome_id,
                   REPLACE(e.KEGG_ko, 'ko:', '') AS ko_id
            FROM kbase.ke_pangenome.gene g
            JOIN kbase.ke_pangenome.gene_genecluster_junction ggc
                ON g.gene_id = ggc.gene_id
            JOIN kbase.ke_pangenome.eggnog_mapper_annotations e
                ON ggc.gene_cluster_id = e.query_name
            WHERE g.genome_id IN ('{batch_str}')
              AND e.KEGG_ko IS NOT NULL
              AND e.KEGG_ko != ''
              AND e.KEGG_ko != '-'
        """).toPandas()

        if len(chunk) > 0:
            all_genome_ko.append(chunk)
    except Exception as ex:
        err_msg = str(ex)[:120]
        if 'maxResultSize' in err_msg:
            # Try halving the batch
            half = len(batch) // 2
            for sub_batch in [batch[:half], batch[half:]]:
                if not sub_batch:
                    continue
                sub_str = "','".join(sub_batch)
                try:
                    sub_chunk = spark.sql(f"""
                        SELECT DISTINCT g.genome_id,
                               REPLACE(e.KEGG_ko, 'ko:', '') AS ko_id
                        FROM kbase.ke_pangenome.gene g
                        JOIN kbase.ke_pangenome.gene_genecluster_junction ggc
                            ON g.gene_id = ggc.gene_id
                        JOIN kbase.ke_pangenome.eggnog_mapper_annotations e
                            ON ggc.gene_cluster_id = e.query_name
                        WHERE g.genome_id IN ('{sub_str}')
                          AND e.KEGG_ko IS NOT NULL
                          AND e.KEGG_ko != ''
                          AND e.KEGG_ko != '-'
                    """).toPandas()
                    if len(sub_chunk) > 0:
                        all_genome_ko.append(sub_chunk)
                except:
                    errors += 1
        else:
            errors += 1
            if errors <= 3:
                print(f"    Batch {batch_num+1} error: {err_msg}")
        continue

    # Checkpoint every 50 batches
    if (batch_num + 1) % 50 == 0 and all_genome_ko:
        cp = pd.concat(all_genome_ko, ignore_index=True).drop_duplicates()
        cp.to_parquet(CHECKPOINT, index=False)
        n_genomes_done = cp.genome_id.nunique()
        print(f"  Checkpoint saved: {len(cp):,} pairs, {n_genomes_done:,} genomes", flush=True)

# Step 4: Assemble final output
if all_genome_ko:
    kp_ko = pd.concat(all_genome_ko, ignore_index=True).drop_duplicates()
    kp_ko['present'] = 1
    print(f"\n  Total genome-KO pairs: {len(kp_ko):,}")
    print(f"  Genomes with KOs: {kp_ko.genome_id.nunique():,}")
    print(f"  Unique KOs: {kp_ko.ko_id.nunique():,}")
    print(f"  Errors: {errors}")

    kp_out = kp_ko.merge(spatial_genomes, on='genome_id')
    kp_out.to_parquet(OUTDIR / 'ke_pangenome_ko_matrix.parquet', index=False)
    print(f"  Saved: {kp_out.genome_id.nunique():,} genomes")

    usable = (spatial_genomes[spatial_genomes.genome_id.isin(
        set(kp_ko.genome_id))].genus.value_counts() >= 8).sum()
    print(f"  Usable genera (≥8): {usable}")

    # Clean up checkpoint
    if CHECKPOINT.exists():
        CHECKPOINT.unlink()
else:
    print("  ERROR: No KO pairs found!")

spark.stop()
print("\nDONE")

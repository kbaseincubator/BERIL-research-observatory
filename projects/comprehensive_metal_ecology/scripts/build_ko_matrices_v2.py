#!/usr/bin/env python3
"""
Build KO presence/absence matrices from all genome databases with lat/lon.
Uses CSU metal mobility grid (same source as MGnify/SPIRE PF1 scores) for
consistent metal assignments.

Databases built:
  1. arkinlab.spire eggnog (6K MAGs with direct mag_id + KEGG_ko)
  2. ke_pangenome (83K genomes via gene→cluster→eggnog)
  3. carbon_source_phenotypes (1K genomes with kofam)
"""
import os
for var in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ.setdefault(var, '1')

import numpy as np
import pandas as pd
from pathlib import Path
from scipy.spatial import cKDTree
import sys
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
    """Assign PF1 metals (from CSU grid) and env covariates via KD-tree."""
    # Initialize all output columns
    for c in METAL_COLS + ENV_COLS:
        df[c] = np.nan

    valid = df[lat_col].notna() & df[lon_col].notna()
    if valid.sum() == 0:
        return df
    locs = df.loc[valid, [lat_col, lon_col]].values

    # Metals from CSU grid
    dd, ii = csu_tree.query(locs, k=1)
    for c in METAL_COLS:
        vals = csu_grid[c].values[ii].copy()
        vals[dd > 0.5] = np.nan
        df.loc[valid, c] = vals

    # Env covariates from MGnify grid
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
# 1. arkinlab.spire eggnog
# ════════════════════════════════════════════════════════════════════════
if not (OUTDIR / 'arkinlab_spire_ko_matrix.parquet').exists():
    print("\n" + "="*80)
    print("DATABASE 1: arkinlab.spire eggnog")
    print("="*80 + "\n", flush=True)

    spire_ko = spark.sql("""
        SELECT e.mag_id AS genome_id,
               REPLACE(e.KEGG_ko, 'ko:', '') AS ko_id,
               mc.latitude, mc.longitude,
               TRY_CAST(gm.genome_size AS BIGINT) AS genome_size,
               gm.genus, gm.phylum
        FROM arkinlab.spire.eggnog_annotations_spire e
        JOIN refdata.spire.mag_coordinates mc ON e.mag_id = mc.mag_id
        JOIN refdata.spire.genome_metadata gm ON e.mag_id = gm.genome_id
        WHERE e.KEGG_ko IS NOT NULL
          AND e.KEGG_ko != ''
          AND e.KEGG_ko != '-'
          AND mc.latitude IS NOT NULL
    """).toPandas()

    print(f"  Raw rows: {len(spire_ko):,}, MAGs: {spire_ko.genome_id.nunique():,}")

    if len(spire_ko) > 0:
        spire_ko = spire_ko.drop_duplicates(subset=['genome_id', 'ko_id'])
        spire_ko['present'] = 1

        genome_meta = spire_ko.groupby('genome_id').first()[
            ['latitude', 'longitude', 'genome_size', 'genus', 'phylum']
        ].reset_index()
        genome_meta = assign_metals_and_env(genome_meta)

        spire_out = spire_ko[['genome_id', 'ko_id', 'present']].merge(
            genome_meta, on='genome_id')
        spire_out.to_parquet(OUTDIR / 'arkinlab_spire_ko_matrix.parquet', index=False)
        print(f"  Saved: {spire_out.genome_id.nunique():,} genomes, "
              f"{spire_out.ko_id.nunique():,} KOs, "
              f"usable genera: {(genome_meta.genus.value_counts() >= 8).sum()}")
else:
    print("\nSkipping DB1 (already exists)")


# ════════════════════════════════════════════════════════════════════════
# 2. ke_pangenome — efficient strategy
# ════════════════════════════════════════════════════════════════════════
if not (OUTDIR / 'ke_pangenome_ko_matrix.parquet').exists():
    print("\n" + "="*80)
    print("DATABASE 2: ke_pangenome")
    print("="*80 + "\n", flush=True)

    # Strategy: Use Spark to do the heavy join server-side,
    # only pull genome_id + ko_id pairs to Python.

    print("  Step 1: Get spatial genomes...", flush=True)
    spatial_genomes = spark.sql("""
        SELECT genome_id, cleaned_lat AS latitude, cleaned_lon AS longitude,
               genus, phylum
        FROM kbase.ke_pangenome.alphaearth_embeddings_all_years
        WHERE cleaned_lat IS NOT NULL AND cleaned_lon IS NOT NULL
    """).toPandas()
    print(f"    {len(spatial_genomes):,} genomes with lat/lon")

    # Get genome sizes
    try:
        gsizes = spark.sql("""
            SELECT genome_id, TRY_CAST(genome_size AS BIGINT) AS genome_size
            FROM kbase.ke_pangenome.gtdb_metadata
        """).toPandas()
        spatial_genomes = spatial_genomes.merge(gsizes, on='genome_id', how='left')
    except:
        spatial_genomes['genome_size'] = np.nan

    spatial_genomes = assign_metals_and_env(spatial_genomes)

    print("  Step 2: Running genome→gene→cluster→KO join in Spark...", flush=True)
    print("    (This may take several minutes...)", flush=True)

    # Do in chunks by first letter of genome_id to avoid OOM
    import string
    all_ko_pairs = []

    # Get distinct first-char prefixes
    prefixes = spark.sql("""
        SELECT DISTINCT SUBSTRING(genome_id, 1, 3) AS prefix
        FROM kbase.ke_pangenome.alphaearth_embeddings_all_years
        WHERE cleaned_lat IS NOT NULL
    """).toPandas()['prefix'].tolist()

    print(f"    Processing {len(prefixes)} genome prefixes...", flush=True)

    for i, prefix in enumerate(sorted(prefixes)):
        if (i + 1) % 50 == 0:
            n_so_far = sum(len(x) for x in all_ko_pairs)
            print(f"    Prefix {i+1}/{len(prefixes)} ({prefix}), "
                  f"{n_so_far:,} pairs so far...", flush=True)
        try:
            chunk = spark.sql(f"""
                SELECT DISTINCT g.genome_id,
                       REPLACE(e.KEGG_ko, 'ko:', '') AS ko_id
                FROM kbase.ke_pangenome.gene g
                JOIN kbase.ke_pangenome.gene_genecluster_junction ggc
                    ON g.gene_id = ggc.gene_id
                JOIN kbase.ke_pangenome.eggnog_mapper_annotations e
                    ON ggc.gene_cluster_id = e.query_name
                WHERE g.genome_id LIKE '{prefix}%'
                  AND e.KEGG_ko IS NOT NULL
                  AND e.KEGG_ko != ''
                  AND e.KEGG_ko != '-'
            """).toPandas()
            # Only keep spatial genomes
            chunk = chunk[chunk.genome_id.isin(set(spatial_genomes.genome_id))]
            if len(chunk) > 0:
                all_ko_pairs.append(chunk)
        except Exception as ex:
            print(f"    Prefix {prefix} error: {str(ex)[:80]}")
            continue

    if all_ko_pairs:
        kp_ko = pd.concat(all_ko_pairs, ignore_index=True).drop_duplicates()
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
    print("\nSkipping DB2 (already exists)")


# ════════════════════════════════════════════════════════════════════════
# 3. Carbon source phenotypes
# ════════════════════════════════════════════════════════════════════════
if not (OUTDIR / 'carbon_source_ko_matrix.parquet').exists():
    print("\n" + "="*80)
    print("DATABASE 3: carbon_source_phenotypes")
    print("="*80 + "\n", flush=True)

    # Ensure spatial_genomes is loaded (may have been skipped if DB2 already existed)
    if 'spatial_genomes' not in dir():
        print("  Loading ke_pangenome spatial genomes for cross-ref...", flush=True)
        spatial_genomes = spark.sql("""
            SELECT genome_id, cleaned_lat AS latitude, cleaned_lon AS longitude,
                   genus, phylum
            FROM kbase.ke_pangenome.alphaearth_embeddings_all_years
            WHERE cleaned_lat IS NOT NULL AND cleaned_lon IS NOT NULL
        """).toPandas()
        try:
            gsizes = spark.sql("""
                SELECT genome_id, TRY_CAST(genome_size AS BIGINT) AS genome_size
                FROM kbase.ke_pangenome.gtdb_metadata
            """).toPandas()
            spatial_genomes = spatial_genomes.merge(gsizes, on='genome_id', how='left')
        except:
            spatial_genomes['genome_size'] = np.nan
        spatial_genomes = assign_metals_and_env(spatial_genomes)

    cs_ko = spark.sql("""
        SELECT genomeid AS genome_id, koid AS ko_id
        FROM globalusers.carbon_source_phenotypes.kofam_annotation_table
        WHERE koid IS NOT NULL
    """).toPandas()

    cs_tax = spark.sql("""
        SELECT genomeid AS genome_id, phylum, genus
        FROM globalusers.carbon_source_phenotypes.taxonomy_table
    """).toPandas()

    print(f"  KO rows: {len(cs_ko):,}, genomes: {cs_ko.genome_id.nunique():,}")

    spatial_ids = set(spatial_genomes.genome_id)
    overlap = set(cs_ko.genome_id) & spatial_ids
    print(f"  Overlap with ke_pangenome spatial: {len(overlap):,}")

    if len(overlap) < 10:
        # Try matching via sample→biosample linkage
        print("  Trying alternative spatial linking via ke_pangenome.sample...", flush=True)
        cs_genome_ids = cs_ko.genome_id.unique().tolist()[:100]  # sample
        print(f"  Sample genome_id format: {cs_genome_ids[:5]}")
        print("  No spatial match available — skipping carbon_source")
    else:
        cs_ko = cs_ko[cs_ko.genome_id.isin(overlap)].drop_duplicates()
        cs_ko['present'] = 1
        cs_meta = spatial_genomes[spatial_genomes.genome_id.isin(overlap)].copy()
        cs_meta = cs_meta.merge(cs_tax, on='genome_id', how='left', suffixes=('', '_cs'))
        cs_out = cs_ko.merge(cs_meta, on='genome_id')
        cs_out.to_parquet(OUTDIR / 'carbon_source_ko_matrix.parquet', index=False)
        print(f"  Saved: {cs_out.genome_id.nunique():,} genomes")
else:
    print("\nSkipping DB3 (already exists)")


spark.stop()
print("\n" + "="*80)
print("DONE — All KO matrices built")
print("="*80)

#!/usr/bin/env python3
"""
NB01 runner — remaining steps 8-10 only.
Steps 2-7 already completed.
Fixes: experiment table name, column names (expName, expGroup, condition_1).
"""
import os
import time
import glob
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')

print("=" * 60)
print("NB01: Data Extraction — Remaining Steps (8-10)")
print("=" * 60)

print("\n[init] Initializing Spark session...")
t0 = time.time()
from get_spark_session import get_spark_session
spark = get_spark_session()
print(f"  Ready ({time.time()-t0:.1f}s)")

# Verify previously saved files
print("\nExisting data files:")
for f in sorted(glob.glob(os.path.join(DATA_DIR, '*.csv'))):
    size_mb = os.path.getsize(f) / 1e6
    print(f"  {os.path.basename(f):45s} {size_mb:8.1f} MB")

# --- Step 8: Condition-type fitness ---
output_path = os.path.join(DATA_DIR, 'fb_fitness_by_condition_type.csv')
if os.path.exists(output_path):
    print(f"\n[8/10] Condition-type fitness: already exists, skipping")
else:
    print(f"\n[8/10] Extracting condition-type fitness (v2)...")
    print("  Using experiment table with expGroup for cleaner classification...")
    t0 = time.time()
    # Use expGroup for primary classification (cleaner than pattern matching)
    # Supplement with condition_1 pattern matching for 'other' group
    cond_fitness_pd = spark.sql("""
        WITH exp_types AS (
            SELECT
                expName,
                orgId,
                CASE
                    WHEN LOWER(expGroup) = 'carbon source'
                         THEN 'carbon_source'
                    WHEN LOWER(expGroup) = 'nitrogen source'
                         THEN 'nitrogen_source'
                    WHEN LOWER(expGroup) = 'sulfur source'
                         THEN 'sulfur_source'
                    WHEN LOWER(expGroup) IN ('stress', 'metal limitation', 'pH', 'temperature',
                                              'starvation', 'survival', 'anaerobic')
                         OR LOWER(condition_1) LIKE '%stress%'
                         OR LOWER(condition_1) LIKE '%antibiotic%'
                         OR LOWER(condition_1) LIKE '%oxidative%'
                         OR LOWER(condition_1) LIKE '%osmotic%'
                         THEN 'stress'
                    WHEN LOWER(expGroup) LIKE '%control%'
                         OR LOWER(expGroup) IN ('lb', 'pye', 'r2a', 'kb', 'bhis',
                                                 'rich t1', 'rich t2', 'nutrient',
                                                 'nutrient t1', 'nutrient t2',
                                                 'marine broth', 'bg11')
                         THEN 'rich_media'
                    ELSE 'other'
                END as condition_type
            FROM kescience_fitnessbrowser.experiment
        )
        SELECT
            gf.orgId, gf.locusId, et.condition_type,
            COUNT(*) as n_conditions,
            AVG(CAST(gf.fit AS FLOAT)) as mean_fitness,
            PERCENTILE_APPROX(CAST(gf.fit AS FLOAT), 0.5) as median_fitness,
            MIN(CAST(gf.fit AS FLOAT)) as min_fitness,
            SUM(CASE WHEN CAST(gf.fit AS FLOAT) < -1.0 THEN 1 ELSE 0 END) as n_sick,
            SUM(CASE WHEN ABS(CAST(gf.fit AS FLOAT)) > 1.0 THEN 1 ELSE 0 END) as n_strong
        FROM kescience_fitnessbrowser.genefitness gf
        JOIN exp_types et ON gf.expName = et.expName AND gf.orgId = et.orgId
        GROUP BY gf.orgId, gf.locusId, et.condition_type
    """).toPandas()
    cond_fitness_pd.to_csv(output_path, index=False)
    print(f"  Saved: {len(cond_fitness_pd):,} rows ({time.time()-t0:.1f}s)")
    print(f"  Condition type distribution:")
    print(cond_fitness_pd.groupby('condition_type')['n_conditions'].sum().to_string())
    print(f"  Genes per condition type:")
    print(cond_fitness_pd.groupby('condition_type')['locusId'].nunique().to_string())

# --- Step 9: KEGG annotations ---
output_path = os.path.join(DATA_DIR, 'fb_kegg_annotations.csv')
if os.path.exists(output_path):
    print(f"\n[9/10] KEGG annotations: already exists, skipping")
else:
    print(f"\n[9/10] Extracting KEGG KO + pathway annotations (93M-row table)...")
    t0 = time.time()
    kegg_pd = spark.sql("""
        SELECT
            query_name as gene_cluster_id,
            EC, KEGG_ko, KEGG_Pathway, COG_category, Description
        FROM kbase_ke_pangenome.eggnog_mapper_annotations
        WHERE (
            KEGG_Pathway LIKE '%map00220%'
            OR KEGG_Pathway LIKE '%map00260%'
            OR KEGG_Pathway LIKE '%map00270%'
            OR KEGG_Pathway LIKE '%map00290%'
            OR KEGG_Pathway LIKE '%map00300%'
            OR KEGG_Pathway LIKE '%map00330%'
            OR KEGG_Pathway LIKE '%map00340%'
            OR KEGG_Pathway LIKE '%map00350%'
            OR KEGG_Pathway LIKE '%map00360%'
            OR KEGG_Pathway LIKE '%map00380%'
            OR KEGG_Pathway LIKE '%map00400%'
            OR KEGG_Pathway LIKE '%map00250%'
            OR KEGG_Pathway LIKE '%map00010%'
            OR KEGG_Pathway LIKE '%map00020%'
            OR KEGG_Pathway LIKE '%map00030%'
            OR KEGG_Pathway LIKE '%map00040%'
            OR KEGG_Pathway LIKE '%map00051%'
            OR KEGG_Pathway LIKE '%map00052%'
            OR KEGG_Pathway LIKE '%map00500%'
            OR KEGG_Pathway LIKE '%map00520%'
            OR KEGG_Pathway LIKE '%map00620%'
            OR KEGG_Pathway LIKE '%map00630%'
            OR KEGG_Pathway LIKE '%map00640%'
            OR KEGG_Pathway LIKE '%map00650%'
            OR KEGG_Pathway LIKE '%map00660%'
            OR KEGG_Pathway LIKE '%map00562%'
            OR COG_category LIKE '%E%'
            OR COG_category LIKE '%G%'
            OR COG_category LIKE '%C%'
        )
        AND (KEGG_ko != '-' OR EC != '-' OR KEGG_Pathway != '-')
    """).toPandas()
    kegg_pd.to_csv(output_path, index=False)
    print(f"  Saved: {len(kegg_pd):,} rows ({time.time()-t0:.1f}s)")
    print(f"  Unique gene clusters: {kegg_pd['gene_cluster_id'].nunique():,}")
    print(f"  With KEGG_ko: {(kegg_pd['KEGG_ko'] != '-').sum():,}")
    print(f"  With EC: {(kegg_pd['EC'] != '-').sum():,}")

# --- Step 10: Essential genes ---
output_path = os.path.join(DATA_DIR, 'fb_essential_genes.csv')
if os.path.exists(output_path):
    print(f"\n[10/10] Essential genes: already exists, skipping")
else:
    print(f"\n[10/10] Identifying putative essential genes...")
    t0 = time.time()
    essentials_pd = spark.sql("""
        SELECT g.orgId, g.locusId, g.sysName, g.gene as gene_name, g.desc as gene_desc
        FROM kescience_fitnessbrowser.gene g
        LEFT JOIN (
            SELECT DISTINCT orgId, locusId FROM kescience_fitnessbrowser.genefitness
        ) gf ON g.orgId = gf.orgId AND g.locusId = gf.locusId
        WHERE CAST(g.type AS INT) = 1
          AND gf.locusId IS NULL
    """).toPandas()
    essentials_pd.to_csv(output_path, index=False)
    print(f"  Saved: {len(essentials_pd):,} genes ({time.time()-t0:.1f}s)")
    print(f"  Per organism:")
    print(essentials_pd.groupby('orgId').size().describe().to_string())

# --- Summary ---
print("\n" + "=" * 60)
print("NB01 COMPLETE — All data files:")
print("=" * 60)
for f in sorted(glob.glob(os.path.join(DATA_DIR, '*.csv'))):
    size_mb = os.path.getsize(f) / 1e6
    print(f"  {os.path.basename(f):45s} {size_mb:8.1f} MB")
print("\nReady for NB02 (Tier 1) and NB03 (Tier 2).")

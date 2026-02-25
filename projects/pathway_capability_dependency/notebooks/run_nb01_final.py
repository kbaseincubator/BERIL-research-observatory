#!/usr/bin/env python3
"""
NB01 runner — final steps 9-10 only.
Steps 2-8 already completed.
KEGG query: drop Description column to fit under maxResultSize.
Split into 3 chunks for safety.
"""
import os
import time
import glob
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')

print("=" * 60)
print("NB01: Data Extraction — Final Steps (9-10)")
print("=" * 60)

print("\n[init] Initializing Spark session...")
t0 = time.time()
from get_spark_session import get_spark_session
spark = get_spark_session()
print(f"  Ready ({time.time()-t0:.1f}s)")

# --- Step 9: KEGG annotations (without Description, 3 chunks) ---
output_path = os.path.join(DATA_DIR, 'fb_kegg_annotations.csv')
if os.path.exists(output_path):
    print(f"\n[9/10] KEGG annotations: already exists, skipping")
else:
    print(f"\n[9/10] Extracting KEGG annotations (no Description col) in 3 chunks...")

    # Define pathway groups for chunking
    pathway_groups = {
        'aa_biosynthesis': [
            'map00220', 'map00260', 'map00270', 'map00290',
            'map00300', 'map00330', 'map00340', 'map00350',
        ],
        'aa_metabolism': [
            'map00360', 'map00380', 'map00400', 'map00250',
        ],
        'carbon_energy': [
            'map00010', 'map00020', 'map00030', 'map00040',
            'map00051', 'map00052', 'map00500', 'map00520',
            'map00620', 'map00630', 'map00640', 'map00650',
            'map00660', 'map00562',
        ],
    }

    chunks = []
    for group_name, maps in pathway_groups.items():
        print(f"  Chunk '{group_name}' ({len(maps)} maps)...")
        tc = time.time()
        where_parts = " OR ".join([f"KEGG_Pathway LIKE '%{m}%'" for m in maps])
        chunk = spark.sql(f"""
            SELECT
                query_name as gene_cluster_id,
                EC, KEGG_ko, KEGG_Pathway, COG_category
            FROM kbase_ke_pangenome.eggnog_mapper_annotations
            WHERE ({where_parts})
              AND (KEGG_ko != '-' OR EC != '-' OR KEGG_Pathway != '-')
        """).toPandas()
        chunks.append(chunk)
        print(f"    {len(chunk):,} rows ({time.time()-tc:.1f}s)")

    kegg_pd = pd.concat(chunks, ignore_index=True).drop_duplicates()
    kegg_pd.to_csv(output_path, index=False)
    print(f"  TOTAL: {len(kegg_pd):,} rows (deduplicated)")
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
total_mb = 0
for f in sorted(glob.glob(os.path.join(DATA_DIR, '*.csv'))):
    size_mb = os.path.getsize(f) / 1e6
    total_mb += size_mb
    print(f"  {os.path.basename(f):45s} {size_mb:8.1f} MB")
print(f"  {'TOTAL':45s} {total_mb:8.1f} MB")
print("\nReady for NB02 (Tier 1) and NB03 (Tier 2).")

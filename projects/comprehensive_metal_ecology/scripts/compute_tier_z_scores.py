#!/usr/bin/env python3
"""
Compute tier1 (resistance) and tier2 (cofactor) KO densities per genus
using kbase.ke_pangenome — same database and query pattern as NB01 primary P1.

Tier 1 (resistance/detoxification): 15 KOs (primary_category=Resistance/Detoxification,
    evidence_tier in {Tier 1, Tier 2})
Tier 2 (cofactor biosynthesis): 5 KOs (primary_category=Cofactor Biosynthesis,
    evidence_tier in {Tier 1, Tier 2})

Genome sizes taken from 01_pgls_input_bacteria.csv (mean_genome_mb) to match P1.
Output: data/tier_z_scores_full.csv
"""

import os
os.environ['OMP_NUM_THREADS'] = '1'

import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats

try:
    from berdl_tools.spark import get_spark_session
    spark = get_spark_session()
    SPARK_AVAILABLE = True
    print("Spark session available")
except Exception as e:
    print(f"Spark unavailable: {e}")
    SPARK_AVAILABLE = False

DATA = Path('projects/comprehensive_metal_ecology/data')

# ── KO tier lists ─────────────────────────────────────────────────────────────
TIER1_KOS = [
    'K03325', 'K03446', 'K07665', 'K07785', 'K07787', 'K07798',
    'K08365', 'K15725', 'K15726', 'K15727', 'K16264', 'K17686',
    'K19591', 'K19594', 'K19595'
]
TIER2_KOS = ['K02225', 'K03635', 'K03638', 'K03750', 'K03831']

print(f"Tier 1 KOs (n={len(TIER1_KOS)}): {TIER1_KOS}")
print(f"Tier 2 KOs (n={len(TIER2_KOS)}): {TIER2_KOS}")

# ── Genome sizes from primary PGLS input (n=1,574) ────────────────────────────
pgls_input = pd.read_csv(DATA / '01_pgls_input_bacteria.csv')
print(f"\nPrimary PGLS genera: {len(pgls_input)}")

if not SPARK_AVAILABLE:
    print("\nERROR: Spark not available — run this script in JupyterHub.")
    raise SystemExit(1)

# ── SQL strings ───────────────────────────────────────────────────────────────
tier1_in = ', '.join(f"'{k}'" for k in TIER1_KOS)
tier2_in = ', '.join(f"'{k}'" for k in TIER2_KOS)
all_in   = ', '.join(f"'{k}'" for k in sorted(set(TIER1_KOS + TIER2_KOS)))

# ── Step 1: explode KEGG_ko, filter to tier1+tier2 KOs ───────────────────────
print("\nStep 1: Exploding KEGG_ko annotations...")
spark.sql(f"""
    CREATE OR REPLACE TEMP VIEW ego_tier_exploded AS
    SELECT
        ego.query_name,
        TRIM(REPLACE(TRIM(ko_part), 'ko:', '')) AS kegg_ko_single
    FROM kbase.ke_pangenome.eggnog_mapper_annotations ego
    LATERAL VIEW explode(split(ego.KEGG_ko, '[|,]')) ko AS ko_part
    WHERE TRIM(ko_part) != '-'
      AND TRIM(ko_part) != ''
      AND TRIM(REPLACE(TRIM(ko_part), 'ko:', '')) IN ({all_in})
""")
print("  ego_tier_exploded view created")

# ── Step 2: join to genus taxonomy, count distinct KOs per tier per genus ─────
print("Step 2: Joining to taxonomy and counting KOs per tier per genus...")
spark.sql(f"""
    CREATE OR REPLACE TEMP VIEW genus_tier_ko_counts AS
    SELECT
        LOWER(REGEXP_REPLACE(SPLIT(tax.genus, '__')[1], ' ', '_')) AS genus_lower,
        COUNT(DISTINCT CASE
            WHEN ego_ex.kegg_ko_single IN ({tier1_in})
            THEN ego_ex.kegg_ko_single
        END) AS n_ko_tier1,
        COUNT(DISTINCT CASE
            WHEN ego_ex.kegg_ko_single IN ({tier2_in})
            THEN ego_ex.kegg_ko_single
        END) AS n_ko_tier2
    FROM ego_tier_exploded ego_ex
    JOIN kbase.ke_pangenome.gene_genecluster_junction junc
      ON ego_ex.query_name = junc.gene_id
    JOIN kbase.ke_pangenome.gene_cluster gc
      ON junc.gene_cluster_id = gc.gene_cluster_id
    JOIN kbase.ke_pangenome.genome g
      ON gc.gtdb_species_clade_id = g.gtdb_species_clade_id
    JOIN kbase.ke_pangenome.gtdb_taxonomy_r214v1 tax
      ON g.genome_id = tax.genome_id
    GROUP BY LOWER(REGEXP_REPLACE(SPLIT(tax.genus, '__')[1], ' ', '_'))
""")
print("  genus_tier_ko_counts view created")

# ── Step 3: collect to Pandas ─────────────────────────────────────────────────
print("Step 3: Collecting to Pandas...")
genus_tier_counts = spark.sql("SELECT * FROM genus_tier_ko_counts").toPandas()
print(f"  Genera with any tier1/tier2 KO: {len(genus_tier_counts)}")
print(f"  Tier1 distribution: {genus_tier_counts['n_ko_tier1'].describe()}")
print(f"  Tier2 distribution: {genus_tier_counts['n_ko_tier2'].describe()}")

# Save raw counts before merging
genus_tier_counts.to_csv(DATA / 'tier_ko_counts_spark.csv', index=False)
print("  Saved: tier_ko_counts_spark.csv")

# ── Step 4: merge with primary PGLS genome sizes, compute densities ───────────
print("\nStep 4: Merging with primary PGLS genome sizes...")
merged = pgls_input[['genus_lower', 'mean_genome_mb']].merge(
    genus_tier_counts, on='genus_lower', how='left'
)
# Genera not in Spark results had 0 matching KOs in the database
merged['n_ko_tier1'] = merged['n_ko_tier1'].fillna(0)
merged['n_ko_tier2'] = merged['n_ko_tier2'].fillna(0)

merged['ko_per_mb_tier1'] = merged['n_ko_tier1'] / merged['mean_genome_mb']
merged['ko_per_mb_tier2'] = merged['n_ko_tier2'] / merged['mean_genome_mb']

n_spark_match = merged['n_ko_tier1'].notna().sum()
print(f"  1574 primary genera, {(genus_tier_counts['genus_lower'].isin(pgls_input['genus_lower'])).sum()} matched in Spark")

# ── Step 5: z-score across the full 1574-genus set ───────────────────────────
merged['ko_per_mb_tier1_z'] = stats.zscore(merged['ko_per_mb_tier1'], nan_policy='omit')
merged['ko_per_mb_tier2_z'] = stats.zscore(merged['ko_per_mb_tier2'], nan_policy='omit')

out = merged[['genus_lower', 'ko_per_mb_tier1', 'ko_per_mb_tier1_z',
              'ko_per_mb_tier2', 'ko_per_mb_tier2_z']]
out.to_csv(DATA / 'tier_z_scores_full.csv', index=False)
print(f"\nSaved: data/tier_z_scores_full.csv ({len(out)} genera)")
print("\nSummary stats:")
print(out[['ko_per_mb_tier1', 'ko_per_mb_tier1_z',
           'ko_per_mb_tier2', 'ko_per_mb_tier2_z']].describe().round(4))
print("\nZero counts:")
print(f"  n_ko_tier1 == 0: {(merged['n_ko_tier1'] == 0).sum()}")
print(f"  n_ko_tier2 == 0: {(merged['n_ko_tier2'] == 0).sum()}")

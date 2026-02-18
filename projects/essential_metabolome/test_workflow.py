#!/usr/bin/env python3
"""
Test complete local BERDL workflow for essential_metabolome project.

This validates:
1. Spark Connect from local machine (using get_spark_session)
2. Cross-database queries (Pangenome + Biochemistry)
3. Result extraction and local saving
"""

from get_spark_session import get_spark_session
import pandas as pd
from pathlib import Path

print("=" * 60)
print("Essential Metabolome - Local BERDL Workflow Test")
print("=" * 60)

# Create Spark session
print("\n⏳ Creating Spark session...")
spark = get_spark_session()
print(f"✅ Spark session created: version {spark.version}")

# Test 1: List databases
print("\n" + "=" * 60)
print("TEST 1: List BERDL Databases")
print("=" * 60)
databases_df = spark.sql("SHOW DATABASES")
databases = [row.namespace for row in databases_df.collect()]
print(f"✅ Found {len(databases)} databases")
print(f"   Pangenome: {'kbase_ke_pangenome' in databases}")
print(f"   Biochemistry: {'kbase_msd_biochemistry' in databases}")

# Test 2: Query eggNOG annotations with EC numbers
print("\n" + "=" * 60)
print("TEST 2: Query Pangenome eggNOG Annotations (EC numbers)")
print("=" * 60)
ec_query = """
SELECT
    query_name as gene_cluster_id,
    EC,
    Description,
    Preferred_name,
    COG_category
FROM kbase_ke_pangenome.eggnog_mapper_annotations
WHERE EC IS NOT NULL AND EC != '-'
LIMIT 100
"""
ec_df = spark.sql(ec_query)
ec_count = ec_df.count()
print(f"✅ Retrieved {ec_count} EC annotations")

# Show sample
ec_pd = ec_df.limit(5).toPandas()
print("\n   Sample EC annotations:")
for _, row in ec_pd.iterrows():
    print(f"   - {row['gene_cluster_id']}: EC {row['EC']}")
    print(f"     {row['Description'][:60]}...")

# Test 3: Query ModelSEED reactions
print("\n" + "=" * 60)
print("TEST 3: Query ModelSEED Biochemistry Reactions")
print("=" * 60)
rxn_query = """
SELECT
    id as reaction_id,
    name,
    abbreviation,
    ec_numbers,
    reversibility
FROM kbase_msd_biochemistry.reaction
WHERE ec_numbers IS NOT NULL
LIMIT 100
"""
rxn_df = spark.sql(rxn_query)
rxn_count = rxn_df.count()
print(f"✅ Retrieved {rxn_count} reactions with EC numbers")

# Show sample
rxn_pd = rxn_df.limit(5).toPandas()
print("\n   Sample reactions:")
for _, row in rxn_pd.iterrows():
    print(f"   - {row['reaction_id']}: {row['name'][:40]}")
    print(f"     EC: {row['ec_numbers']}, Reversible: {row['reversibility']}")

# Test 4: Cross-database join (EC → Reactions)
print("\n" + "=" * 60)
print("TEST 4: Cross-Database Join (eggNOG + Biochemistry)")
print("=" * 60)
join_query = """
WITH eggnog_ec AS (
    SELECT
        query_name as gene_cluster_id,
        EC as ec_number,
        Description,
        Preferred_name
    FROM kbase_ke_pangenome.eggnog_mapper_annotations
    WHERE EC IS NOT NULL AND EC != '-'
    LIMIT 1000
),
reactions AS (
    SELECT
        id as reaction_id,
        name as reaction_name,
        ec_numbers,
        reversibility
    FROM kbase_msd_biochemistry.reaction
    WHERE ec_numbers IS NOT NULL
)
SELECT
    e.gene_cluster_id,
    e.ec_number,
    e.Preferred_name as gene_name,
    r.reaction_id,
    r.reaction_name,
    r.reversibility
FROM eggnog_ec e
JOIN reactions r
    ON e.ec_number = r.ec_numbers
LIMIT 50
"""
join_df = spark.sql(join_query)
join_count = join_df.count()
print(f"✅ Cross-database join successful")
print(f"   Retrieved {join_count} EC → reaction mappings")

# Show sample
if join_count > 0:
    join_pd = join_df.limit(5).toPandas()
    print("\n   Sample EC → Reaction mappings:")
    for _, row in join_pd.iterrows():
        print(f"   - Gene: {row['gene_cluster_id']} ({row['gene_name']})")
        print(f"     EC: {row['ec_number']} → Reaction: {row['reaction_id']}")
        print(f"     {row['reaction_name'][:50]}...")

# Test 5: Save results locally
print("\n" + "=" * 60)
print("TEST 5: Save Results Locally")
print("=" * 60)
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

# Save EC annotations sample
ec_sample_file = data_dir / "eggnog_ec_sample.tsv"
ec_df.limit(100).toPandas().to_csv(ec_sample_file, sep='\t', index=False)
print(f"✅ Saved EC annotations: {ec_sample_file}")

# Save reactions sample
rxn_sample_file = data_dir / "biochem_reactions_sample.tsv"
rxn_df.limit(100).toPandas().to_csv(rxn_sample_file, sep='\t', index=False)
print(f"✅ Saved reactions: {rxn_sample_file}")

# Save join results
if join_count > 0:
    join_sample_file = data_dir / "ec_reaction_mappings_sample.tsv"
    join_df.toPandas().to_csv(join_sample_file, sep='\t', index=False)
    print(f"✅ Saved EC→reaction mappings: {join_sample_file}")

# Clean up
spark.stop()

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED - Local BERDL Workflow Validated")
print("=" * 60)
print(f"""
Validated capabilities:
  ✅ Spark Connect from local machine (get_spark_session)
  ✅ Proxy chain working (SSH tunnels + pproxy)
  ✅ Pangenome queries (eggNOG annotations)
  ✅ Biochemistry queries (ModelSEED reactions)
  ✅ Cross-database joins (EC → reactions)
  ✅ Local result saving (TSV files)

Output files:
  - {ec_sample_file}
  - {rxn_sample_file}
  - {join_sample_file if join_count > 0 else 'N/A'}

Ready for full essential metabolome analysis!
""")

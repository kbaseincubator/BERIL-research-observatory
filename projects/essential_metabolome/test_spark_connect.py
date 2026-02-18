#!/usr/bin/env python3
"""
Test Spark Connect from local machine.

This validates the local BERDL workflow:
- Proxy chain (SSH tunnel + pproxy)
- Spark Connect to BERDL cluster
- Cross-database queries
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
project_root = Path(__file__).parent.parent.parent
load_dotenv(project_root / '.env')

# Set proxy for Spark Connect
os.environ['https_proxy'] = 'http://127.0.0.1:8123'
os.environ['http_proxy'] = 'http://127.0.0.1:8123'
os.environ['no_proxy'] = 'localhost,127.0.0.1'

print("=" * 60)
print("Testing Local BERDL Workflow - Spark Connect")
print("=" * 60)

# Verify prerequisites
auth_token = os.getenv('KBASE_AUTH_TOKEN')
if not auth_token:
    print("❌ KBASE_AUTH_TOKEN not found in .env")
    sys.exit(1)

print(f"\n✅ Environment configured")
print(f"   Proxy: {os.environ.get('https_proxy')}")
print(f"   Auth token: {auth_token[:20]}...")

# Import PySpark
try:
    from pyspark.sql import SparkSession
    print(f"✅ PySpark imported")
except ImportError as e:
    print(f"❌ PySpark import failed: {e}")
    sys.exit(1)

# Connect to Spark
print(f"\n⏳ Connecting to Spark Connect at hub.berdl.kbase.us:443...")
try:
    spark = SparkSession.builder \
        .remote("sc://hub.berdl.kbase.us:443") \
        .config("spark.connect.grpc.http.proxy", "http://127.0.0.1:8123") \
        .config("spark.connect.grpc.channelBuilder", "netty") \
        .getOrCreate()

    print(f"✅ Spark session created")
    print(f"   Spark version: {spark.version}")
except Exception as e:
    print(f"❌ Spark Connect failed: {e}")
    sys.exit(1)

# Test 1: List databases
print(f"\n" + "=" * 60)
print("TEST 1: List BERDL Databases")
print("=" * 60)
try:
    databases_df = spark.sql("SHOW DATABASES")
    databases = [row.namespace for row in databases_df.collect()]
    print(f"✅ Found {len(databases)} databases")
    print(f"   Sample: {databases[:5]}")
except Exception as e:
    print(f"❌ Database listing failed: {e}")
    spark.stop()
    sys.exit(1)

# Test 2: Query pangenome eggNOG annotations
print(f"\n" + "=" * 60)
print("TEST 2: Query Pangenome eggNOG Annotations")
print("=" * 60)
try:
    ec_query = """
    SELECT
        query_name as gene_cluster_id,
        EC,
        Description,
        Preferred_name
    FROM kbase_ke_pangenome.eggnog_mapper_annotations
    WHERE EC IS NOT NULL AND EC != '-'
    LIMIT 10
    """
    ec_df = spark.sql(ec_query)
    ec_results = ec_df.collect()
    print(f"✅ Retrieved {len(ec_results)} EC annotations")
    print(f"\n   Sample:")
    for row in ec_results[:3]:
        print(f"   - {row.gene_cluster_id}: {row.EC} ({row.Preferred_name})")
except Exception as e:
    print(f"❌ eggNOG query failed: {e}")
    spark.stop()
    sys.exit(1)

# Test 3: Query biochemistry reactions
print(f"\n" + "=" * 60)
print("TEST 3: Query ModelSEED Biochemistry")
print("=" * 60)
try:
    rxn_query = """
    SELECT
        id as reaction_id,
        name,
        abbreviation,
        ec_numbers
    FROM kbase_msd_biochemistry.reaction
    WHERE ec_numbers IS NOT NULL
    LIMIT 10
    """
    rxn_df = spark.sql(rxn_query)
    rxn_results = rxn_df.collect()
    print(f"✅ Retrieved {len(rxn_results)} reactions")
    print(f"\n   Sample:")
    for row in rxn_results[:3]:
        print(f"   - {row.reaction_id}: {row.name} (EC: {row.ec_numbers})")
except Exception as e:
    print(f"❌ Biochemistry query failed: {e}")
    spark.stop()
    sys.exit(1)

# Test 4: Cross-database join
print(f"\n" + "=" * 60)
print("TEST 4: Cross-Database Join (eggNOG + Biochemistry)")
print("=" * 60)
try:
    join_query = """
    WITH eggnog_ec AS (
        SELECT
            query_name as gene_cluster_id,
            EC as ec_number,
            Preferred_name
        FROM kbase_ke_pangenome.eggnog_mapper_annotations
        WHERE EC IS NOT NULL AND EC != '-'
        LIMIT 100
    ),
    reactions AS (
        SELECT
            id as reaction_id,
            name as reaction_name,
            ec_numbers
        FROM kbase_msd_biochemistry.reaction
        WHERE ec_numbers IS NOT NULL
    )
    SELECT
        e.gene_cluster_id,
        e.ec_number,
        e.Preferred_name,
        r.reaction_id,
        r.reaction_name
    FROM eggnog_ec e
    JOIN reactions r
        ON e.ec_number = r.ec_numbers
    LIMIT 10
    """
    join_df = spark.sql(join_query)
    join_results = join_df.collect()
    print(f"✅ Cross-database join successful")
    print(f"   Retrieved {len(join_results)} EC → reaction mappings")
    if join_results:
        print(f"\n   Sample:")
        for row in join_results[:3]:
            print(f"   - {row.gene_cluster_id} ({row.ec_number})")
            print(f"     → {row.reaction_id}: {row.reaction_name}")
except Exception as e:
    print(f"❌ Cross-database join failed: {e}")
    spark.stop()
    sys.exit(1)

# Clean up
spark.stop()

print(f"\n" + "=" * 60)
print("✅ ALL TESTS PASSED - Local BERDL Workflow Validated")
print("=" * 60)
print(f"""
Validated capabilities:
  ✅ Spark Connect from local machine
  ✅ Proxy chain (SSH + pproxy)
  ✅ Pangenome queries (eggNOG annotations)
  ✅ Biochemistry queries (ModelSEED reactions)
  ✅ Cross-database joins

Ready for full analysis workflow!
""")

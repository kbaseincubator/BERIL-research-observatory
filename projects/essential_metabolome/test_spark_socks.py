#!/usr/bin/env python3
"""
Test Spark Connect using SOCKS5 proxy directly (bypassing pproxy).
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
project_root = Path(__file__).parent.parent.parent
load_dotenv(project_root / '.env')

# Set SOCKS proxy for gRPC
os.environ['grpc_proxy'] = 'socks5://127.0.0.1:1338'
os.environ['no_proxy'] = 'localhost,127.0.0.1'

print("=" * 60)
print("Testing Spark Connect via SOCKS5 Proxy")
print("=" * 60)

# Verify prerequisites
auth_token = os.getenv('KBASE_AUTH_TOKEN')
if not auth_token:
    print("❌ KBASE_AUTH_TOKEN not found in .env")
    sys.exit(1)

print(f"\n✅ Environment configured")
print(f"   SOCKS proxy: {os.environ.get('grpc_proxy')}")
print(f"   Auth token: {auth_token[:20]}...")

# Import PySpark
from pyspark.sql import SparkSession

print(f"✅ PySpark imported")

# Connect to Spark
print(f"\n⏳ Connecting to Spark Connect at hub.berdl.kbase.us:443...")
try:
    spark = SparkSession.builder \
        .remote("sc://hub.berdl.kbase.us:443") \
        .getOrCreate()

    print(f"✅ Spark session created")
    print(f"   Spark version: {spark.version}")
except Exception as e:
    print(f"❌ Spark Connect failed: {e}")
    sys.exit(1)

# Test query
print(f"\n⏳ Testing database query...")
try:
    databases_df = spark.sql("SHOW DATABASES")
    databases = [row.namespace for row in databases_df.collect()]
    print(f"✅ Query successful - found {len(databases)} databases")
    print(f"   Sample: {databases[:5]}")
except Exception as e:
    print(f"❌ Query failed: {e}")
    spark.stop()
    sys.exit(1)

spark.stop()
print(f"\n✅ SUCCESS - Spark Connect working via SOCKS5 proxy")

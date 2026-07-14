#!/usr/bin/env python3
"""Probe microbeatlas schemas + CORAL dim tables for NB04 joins."""
import os
from pyspark.sql import SparkSession
spark_url = f"sc://jupyter-{os.environ['USER']}.jupyterhub-prod:15002/;use_ssl=false;x-kbase-token={os.environ['KBASE_AUTH_TOKEN']}"
spark = SparkSession.builder.remote(spark_url).getOrCreate()

def probe(sql, label, n=2):
    print(f"\n=== {label} ===")
    try:
        df = spark.sql(sql)
        for c, t in df.dtypes[:40]:
            print(f"  {c:35s} {t}")
        if len(df.dtypes) > 40: print(f"  ... {len(df.dtypes)-40} more cols")
        try:
            rows = df.limit(n).collect()
            for r in rows:
                d = r.asDict()
                print("    " + ", ".join(f"{k}={str(v)[:35]!r}" for k,v in list(d.items())[:5]))
        except Exception as e: print(f"    [no rows: {type(e).__name__}]")
    except Exception as e:
        print(f"  ERROR: {e}")

def count(sql, label):
    try:
        n = spark.sql(sql).collect()[0][0]
        print(f"  {label}: {n:,}")
    except Exception as e:
        print(f"  {label}: ERR {type(e).__name__}")

# microbeatlas
for t in ["otu_metadata", "otu_counts_long", "sample_metadata", "enriched_metadata", "enriched_metadata_gee"]:
    probe(f"SELECT * FROM arkinlab_microbeatlas.{t}", f"arkinlab_microbeatlas.{t}")

print("\n=== microbeatlas counts ===")
for t in ["otu_metadata", "otu_counts_long", "sample_metadata", "enriched_metadata_gee"]:
    count(f"SELECT COUNT(*) FROM arkinlab_microbeatlas.{t}", t)

# CORAL dimensions
probe("SELECT * FROM enigma_coral.sdt_asv", "sdt_asv")
probe("SELECT * FROM enigma_coral.sdt_community", "sdt_community")
probe("SELECT * FROM enigma_coral.sdt_sample", "sdt_sample")
probe("SELECT * FROM enigma_coral.sdt_location", "sdt_location")

print("\n=== CORAL counts ===")
for t in ["sdt_asv", "sdt_community", "sdt_sample", "sdt_location", "ddt_brick0000476", "ddt_brick0000080"]:
    count(f"SELECT COUNT(*) FROM enigma_coral.{t}", t)

# Check ncbi_env attribute distribution (what env-related fields are populated?)
print("\n=== ncbi_env top attribute_name values ===")
try:
    rows = spark.sql("""
        SELECT attribute_name, COUNT(DISTINCT accession) AS n_accessions
        FROM kbase_ke_pangenome.ncbi_env
        GROUP BY attribute_name
        ORDER BY n_accessions DESC
        LIMIT 30
    """).collect()
    for r in rows: print(f"  {r[0]:35s} {r[1]:>10,}")
except Exception as e: print(f"  ERR: {e}")

spark.stop()

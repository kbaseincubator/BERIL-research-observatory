#!/usr/bin/env python3
"""Probe schemas for NB04 data sources."""
import os
from pyspark.sql import SparkSession
spark_url = f"sc://jupyter-{os.environ['USER']}.jupyterhub-prod:15002/;use_ssl=false;x-kbase-token={os.environ['KBASE_AUTH_TOKEN']}"
spark = SparkSession.builder.remote(spark_url).getOrCreate()

def probe(sql, label, limit=3):
    print(f"\n===== {label} =====")
    try:
        df = spark.sql(sql)
        for c, t in df.dtypes:
            print(f"  {c:30s} {t}")
        if limit:
            try:
                rows = df.limit(limit).collect()
                if rows:
                    print(f"  [sample rows: {len(rows)}]")
                    for r in rows[:2]:
                        d = r.asDict()
                        print("  " + ", ".join(f"{k}={str(v)[:40]!r}" for k,v in list(d.items())[:6]))
            except Exception as e:
                print(f"  [could not fetch rows: {type(e).__name__}]")
    except Exception as e:
        print(f"  ERROR: {type(e).__name__}: {str(e)[:200]}")

# Panel A: pangenome.ncbi_env
probe("SELECT * FROM kbase_ke_pangenome.ncbi_env", "ncbi_env")
try:
    n = spark.sql("SELECT COUNT(*) FROM kbase_ke_pangenome.ncbi_env").collect()[0][0]
    print(f"  row count: {n:,}")
except Exception as e:
    print(f"  count failed: {e}")

# Panel B: microbeatlas
try:
    rows = spark.sql("SHOW DATABASES LIKE 'arkinlab_microbeatlas*'").collect()
    print("\nDatabases matching arkinlab_microbeatlas*:")
    for r in rows: print(f"  {r[0]}")
except Exception as e: print(f"  err: {e}")

try:
    rows = spark.sql("SHOW TABLES IN arkinlab_microbeatlas").collect()
    print("\nTables in arkinlab_microbeatlas:")
    for r in rows: print(f"  {r[1]}")
except Exception as e:
    print(f"  microbeatlas tables err: {e}")
    # try variants
    for db in ["arkinlab_microbeatlas", "arkinlab_microbe_atlas", "microbeatlas"]:
        try:
            rows = spark.sql(f"SHOW TABLES IN {db}").collect()
            print(f"Tables in {db}:")
            for r in rows: print(f"  {r[1]}")
            break
        except Exception as e2:
            print(f"  {db}: {type(e2).__name__}")

# Panel C + D: enigma_coral bricks
probe("SELECT * FROM enigma_coral.ddt_brick0000510", "ddt_brick0000510 (strain-well)")
probe("SELECT * FROM enigma_coral.ddt_brick0000080", "ddt_brick0000080 (geochem ppb)")
probe("SELECT * FROM enigma_coral.ddt_brick0000010", "ddt_brick0000010 (geochem uM)")
probe("SELECT * FROM enigma_coral.ddt_brick0000476", "ddt_brick0000476 (100WS ASV)")

# CORAL dimension tables (sdt_* and smt_*)
try:
    rows = spark.sql("SHOW TABLES IN enigma_coral").collect()
    dims = [r[1] for r in rows if r[1].startswith(('sdt_', 'smt_'))]
    print(f"\nCORAL dim tables ({len(dims)}):")
    for t in sorted(dims): print(f"  {t}")
except Exception as e: print(f"  err: {e}")

spark.stop()

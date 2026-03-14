#!/usr/bin/env python3
"""
Assess InterPro coverage across BERDL collections via Spark SQL.

After ingestion, this runs JOINs between kescience_interpro.protein2ipr
and other BERDL collections to report coverage statistics.

Usage:
  python data/interpro_lookup/scripts/05_assess_coverage.py
"""

import time

from berdl_notebook_utils.setup_spark_session import get_spark_session

IPR = "kescience_interpro"
PAN = "kbase_ke_pangenome"


def main():
    spark = get_spark_session()

    print("=" * 70)
    print("InterPro Coverage Assessment")
    print("=" * 70)

    # ── InterPro table stats ─────────────────────────────────────────
    print("\n── InterPro Table Stats ──")

    for table, desc in [
        ("protein2ipr", "protein → InterPro mappings"),
        ("entry", "InterPro entry metadata"),
        ("go_mapping", "InterPro → GO mappings"),
    ]:
        t0 = time.time()
        n = spark.sql(f"SELECT COUNT(*) AS n FROM {IPR}.{table}").collect()[0]["n"]
        elapsed = time.time() - t0
        print(f"  {IPR}.{table:15s}: {n:>14,} rows ({elapsed:.1f}s) — {desc}")

    # Unique proteins in protein2ipr
    n_proteins = spark.sql(f"""
        SELECT COUNT(DISTINCT uniprot_acc) AS n FROM {IPR}.protein2ipr
    """).collect()[0]["n"]
    print(f"\n  Unique UniProt proteins with InterPro: {n_proteins:,}")

    # Entry type breakdown
    print("\n── InterPro Entry Types ──")
    types = spark.sql(f"""
        SELECT entry_type, COUNT(*) AS n
        FROM {IPR}.entry
        GROUP BY entry_type
        ORDER BY n DESC
    """).toPandas()
    for _, row in types.iterrows():
        print(f"  {row['entry_type']:20s}: {row['n']:>8,}")

    # Top source databases
    print("\n── Top Source Databases in protein2ipr ──")
    src_dbs = spark.sql(f"""
        SELECT source_db, COUNT(*) AS n
        FROM {IPR}.protein2ipr
        GROUP BY source_db
        ORDER BY n DESC
        LIMIT 15
    """).toPandas()
    for _, row in src_dbs.iterrows():
        print(f"  {row['source_db']:20s}: {row['n']:>14,}")

    # ── Pangenome coverage ───────────────────────────────────────────
    print("\n── Pangenome Gene Cluster Coverage ──")

    total_clusters = spark.sql(f"""
        SELECT COUNT(*) AS n FROM {PAN}.bakta_annotations
    """).collect()[0]["n"]
    print(f"\n  Total gene clusters (bakta_annotations): {total_clusters:,}")

    # UniRef100 exact match
    print("\n  Matching via UniRef100 (exact sequence match)...")
    t0 = time.time()
    uniref100_match = spark.sql(f"""
        SELECT COUNT(DISTINCT ba.gene_cluster_id) AS n
        FROM {PAN}.bakta_annotations ba
        JOIN {IPR}.protein2ipr ip
          ON REPLACE(ba.uniref100, 'UniRef100_', '') = ip.uniprot_acc
        WHERE ba.uniref100 IS NOT NULL AND ba.uniref100 <> ''
    """).collect()[0]["n"]
    elapsed = time.time() - t0
    pct = uniref100_match / total_clusters * 100
    print(f"  UniRef100 → InterPro: {uniref100_match:>12,} clusters ({pct:.1f}%) [{elapsed:.0f}s]")

    # UniRef50 match (adds clusters without UniRef100)
    print("  Matching via UniRef50 (≥50% identity, additional clusters)...")
    t0 = time.time()
    uniref50_match = spark.sql(f"""
        SELECT COUNT(DISTINCT ba.gene_cluster_id) AS n
        FROM {PAN}.bakta_annotations ba
        JOIN {IPR}.protein2ipr ip
          ON REPLACE(ba.uniref50, 'UniRef50_', '') = ip.uniprot_acc
        WHERE ba.uniref50 IS NOT NULL AND ba.uniref50 <> ''
          AND (ba.uniref100 IS NULL OR ba.uniref100 = '')
    """).collect()[0]["n"]
    elapsed = time.time() - t0
    pct50 = uniref50_match / total_clusters * 100
    print(f"  UniRef50 additional: {uniref50_match:>12,} clusters ({pct50:.1f}%) [{elapsed:.0f}s]")

    combined = uniref100_match + uniref50_match
    combined_pct = combined / total_clusters * 100
    gap = total_clusters - combined
    gap_pct = gap / total_clusters * 100

    print(f"\n  ─── Summary ───")
    print(f"  Total clusters:           {total_clusters:>12,}")
    print(f"  With InterPro (exact):    {uniref100_match:>12,} ({uniref100_match/total_clusters*100:.1f}%)")
    print(f"  With InterPro (≥50%):   + {uniref50_match:>12,} ({pct50:.1f}%)")
    print(f"  With InterPro (total):    {combined:>12,} ({combined_pct:.1f}%)")
    print(f"  No InterPro coverage:     {gap:>12,} ({gap_pct:.1f}%)")

    # ── InterPro annotations per cluster (sample) ────────────────────
    print("\n── Annotations per Cluster (sample of matched) ──")
    stats = spark.sql(f"""
        WITH matched AS (
            SELECT ba.gene_cluster_id, COUNT(*) AS n_ipr_entries
            FROM {PAN}.bakta_annotations ba
            JOIN {IPR}.protein2ipr ip
              ON REPLACE(ba.uniref100, 'UniRef100_', '') = ip.uniprot_acc
            WHERE ba.uniref100 IS NOT NULL AND ba.uniref100 <> ''
            GROUP BY ba.gene_cluster_id
        )
        SELECT
            MIN(n_ipr_entries) AS min_entries,
            PERCENTILE_APPROX(n_ipr_entries, 0.25) AS p25,
            PERCENTILE_APPROX(n_ipr_entries, 0.5) AS median,
            PERCENTILE_APPROX(n_ipr_entries, 0.75) AS p75,
            MAX(n_ipr_entries) AS max_entries,
            AVG(n_ipr_entries) AS mean_entries
        FROM matched
    """).collect()[0]
    print(f"  Min: {stats['min_entries']}, P25: {stats['p25']}, "
          f"Median: {stats['median']}, P75: {stats['p75']}, "
          f"Max: {stats['max_entries']}, Mean: {stats['mean_entries']:.1f}")

    # ── GO term coverage ─────────────────────────────────────────────
    print("\n── GO Term Coverage ──")
    go_count = spark.sql(f"""
        SELECT COUNT(DISTINCT gm.go_id) AS n_go_terms
        FROM {PAN}.bakta_annotations ba
        JOIN {IPR}.protein2ipr ip
          ON REPLACE(ba.uniref100, 'UniRef100_', '') = ip.uniprot_acc
        JOIN {IPR}.go_mapping gm
          ON ip.ipr_id = gm.ipr_id
        WHERE ba.uniref100 IS NOT NULL AND ba.uniref100 <> ''
    """).collect()[0]["n_go_terms"]
    print(f"  Unique GO terms reachable via pangenome: {go_count:,}")

    print("\n" + "=" * 70)
    print("Done.")

    spark.stop()


if __name__ == "__main__":
    main()

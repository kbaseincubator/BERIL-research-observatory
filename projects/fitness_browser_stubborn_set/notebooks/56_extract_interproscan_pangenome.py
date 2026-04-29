"""
Extract InterProScan domains for FB training-set genes via MD5-of-sequence
matching against the kbase_ke_pangenome InterProScan run.

Why MD5 matching: kbase_ke_pangenome.interproscan_domains is keyed by
gene_cluster_id, which we cannot directly link to FB locusIds (no xref
table connects them). But the table also carries an `md5` column = MD5 of
the protein sequence. By computing the same MD5 from the FB fasta, we can
match identically-sequenced proteins to their InterProScan results.

This complements the UniProt-based extract (notebook 55, kescience_interpro):
  - 55: FB → uniprot_acc → kescience_interpro (broad UniProt InterPro index)
  - 56: FB → md5 → kbase_ke_pangenome.interproscan_domains (richer, with
         per-domain scores, sites, GO + pathway aggregations)

Output:
  data/training_set/target_gene_interproscan.tsv
    columns: orgId, locusId, md5, signature_acc, signature_desc,
             ipr_acc, ipr_desc, analysis, start, stop, score, go_terms, pathways
"""
from __future__ import annotations

import csv
import hashlib
import sys
import time
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from get_spark_session import get_spark_session  # noqa: E402

MD5_MAP_FILE = Path("/tmp/training_md5.tsv")
OUT_PATH = PROJECT_DATA / "training_set" / "target_gene_interproscan.tsv"


def main() -> None:
    t0 = time.time()
    md5_rows = []
    with open(MD5_MAP_FILE) as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            md5_rows.append(r)
    print(f"FB md5 mappings: {len(md5_rows)}", file=sys.stderr)
    md5_set = sorted(set(r["md5"] for r in md5_rows))
    print(f"unique md5s to query: {len(md5_set)}", file=sys.stderr)

    spark = get_spark_session()
    print(f"[{time.time()-t0:5.1f}s] Spark connected", file=sys.stderr)

    # Batch the md5 IN clause; stream-resets above ~1500 md5s
    BATCH = 500
    df_parts = []
    for i in range(0, len(md5_set), BATCH):
        batch = md5_set[i:i+BATCH]
        md5_in = ",".join(f"'{m}'" for m in batch)
        q = f"""
            SELECT d.md5, d.gene_cluster_id, d.analysis,
                   d.signature_acc, d.signature_desc,
                   d.ipr_acc, d.ipr_desc, d.start, d.stop,
                   try_cast(d.score AS DOUBLE) AS score
            FROM kbase_ke_pangenome.interproscan_domains d
            WHERE d.md5 IN ({md5_in})
        """
        part = spark.sql(q).toPandas()
        df_parts.append(part)
        print(f"  batch {i//BATCH + 1}: {len(part):,} rows", file=sys.stderr)
    df = pd.concat(df_parts, ignore_index=True) if df_parts else pd.DataFrame()
    print(f"[{time.time()-t0:5.1f}s] {len(df):,} IPS rows for {df['md5'].nunique():,} unique md5s, "
          f"{df['ipr_acc'].nunique():,} unique IPR accs", file=sys.stderr)

    # Now pull GO and pathway aggregates for the gene_clusters we hit
    cluster_ids = sorted(df['gene_cluster_id'].dropna().unique())
    print(f"[{time.time()-t0:5.1f}s] {len(cluster_ids):,} gene_cluster_ids; pulling GO + pathway aggregates...", file=sys.stderr)
    go_parts = []
    path_parts = []
    for i in range(0, len(cluster_ids), BATCH):
        batch = cluster_ids[i:i+BATCH]
        in_list = ",".join(f"'{c}'" for c in batch)
        go_parts.append(spark.sql(f"""
            SELECT gene_cluster_id, array_join(collect_set(go_id), ';') AS go_ids
            FROM kbase_ke_pangenome.interproscan_go
            WHERE gene_cluster_id IN ({in_list})
            GROUP BY gene_cluster_id
        """).toPandas())
        path_parts.append(spark.sql(f"""
            SELECT gene_cluster_id, array_join(collect_set(concat(pathway_db,':',pathway_id)), ';') AS pathways
            FROM kbase_ke_pangenome.interproscan_pathways
            WHERE gene_cluster_id IN ({in_list})
            GROUP BY gene_cluster_id
        """).toPandas())
    go_df = pd.concat(go_parts, ignore_index=True) if go_parts else pd.DataFrame(columns=['gene_cluster_id','go_ids'])
    path_df = pd.concat(path_parts, ignore_index=True) if path_parts else pd.DataFrame(columns=['gene_cluster_id','pathways'])
    df = df.merge(go_df, on='gene_cluster_id', how='left').merge(path_df, on='gene_cluster_id', how='left')
    print(f"[{time.time()-t0:5.1f}s] Joined GO + pathways", file=sys.stderr)

    # Join back with training (orgId, locusId) by md5
    md5_df = pd.DataFrame(md5_rows)
    merged = md5_df.merge(df, on="md5", how="inner")
    print(f"[{time.time()-t0:5.1f}s] After merging with FB training keys: {len(merged):,} rows", file=sys.stderr)
    print(f"  unique training genes covered: {len(merged[['orgId','locusId']].drop_duplicates()):,}", file=sys.stderr)

    cols = ["orgId", "locusId", "md5", "gene_cluster_id", "analysis",
            "signature_acc", "signature_desc", "ipr_acc", "ipr_desc",
            "start", "stop", "score", "go_ids", "pathways"]
    merged[cols].to_csv(OUT_PATH, sep="\t", index=False)
    size_mb = OUT_PATH.stat().st_size / 1e6
    print(f"[{time.time()-t0:5.1f}s] Wrote {OUT_PATH} ({size_mb:.1f} MB)", file=sys.stderr)


if __name__ == "__main__":
    main()

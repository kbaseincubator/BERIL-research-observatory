"""
Extract InterProScan annotations for FB training-set genes via the
cluster-mediated bridge:

  FB (orgId, locusId)
    → fb_pangenome_link.tsv (DIAMOND best hit per FB gene to a pangenome
                              cluster representative; from sibling project
                              `conservation_vs_fitness/`)
    → gene_cluster_id
    → kbase_ke_pangenome.interproscan_domains / interproscan_go /
      interproscan_pathways

This is the most complete of the three bridges:
  - target_gene_interpro.tsv         (UniProt-based, 66% coverage)
  - target_gene_interproscan.tsv     (MD5-based, 39% coverage)
  - target_gene_interpro_cluster.tsv (cluster-based, 78% coverage)  ← this file

The cluster route works for any FB gene whose DIAMOND best hit lands on
a pangenome cluster representative (regardless of whether sequences are
identical). That's why it covers more genes than MD5 matching.

Output:
  data/training_set/target_gene_interpro_cluster.tsv
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from get_spark_session import get_spark_session  # noqa: E402

LINK_TSV = PROJECT_DATA / "fb_pangenome_link.tsv"
OUT_PATH = PROJECT_DATA / "training_set" / "target_gene_interpro_cluster.tsv"


def chunk(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i+n]


def main() -> None:
    t0 = time.time()

    # 1. Training keys
    keys = set()
    for fn in ("negatives.jsonl", "positives.jsonl", "human_validated.jsonl"):
        with open(PROJECT_DATA / "training_set" / fn) as fh:
            for line in fh:
                r = json.loads(line)
                keys.add((r["orgId"], r["locusId"]))
    print(f"training keys: {len(keys)}", file=sys.stderr)

    # 2. Link table → cluster_ids for training genes
    link = pd.read_csv(LINK_TSV, sep="\t")
    link["key"] = list(zip(link["orgId"], link["locusId"]))
    sub = link[link["key"].isin(keys)].drop(columns=["key"])
    print(f"training rows in link table: {len(sub):,}", file=sys.stderr)
    cluster_ids = sorted(sub["gene_cluster_id"].dropna().unique())
    print(f"unique cluster_ids: {len(cluster_ids):,}", file=sys.stderr)

    # 3. Pull InterProScan for those cluster_ids (batch the IN clauses)
    spark = get_spark_session()
    print(f"[{time.time()-t0:5.1f}s] Spark connected", file=sys.stderr)

    BATCH = 500
    ips_parts = []
    for i, batch in enumerate(chunk(cluster_ids, BATCH)):
        in_list = ",".join(f"'{c}'" for c in batch)
        q = f"""
            SELECT gene_cluster_id, md5, analysis,
                   signature_acc, signature_desc,
                   ipr_acc, ipr_desc, start, stop,
                   try_cast(score AS DOUBLE) AS score
            FROM kbase_ke_pangenome.interproscan_domains
            WHERE gene_cluster_id IN ({in_list})
        """
        part = spark.sql(q).toPandas()
        ips_parts.append(part)
        if (i+1) % 2 == 0:
            print(f"  IPS batch {i+1}: cum {sum(len(p) for p in ips_parts):,} rows",
                  file=sys.stderr)
    ips = pd.concat(ips_parts, ignore_index=True) if ips_parts else pd.DataFrame()
    print(f"[{time.time()-t0:5.1f}s] IPS rows: {len(ips):,}", file=sys.stderr)

    # 4. GO + pathway aggregates per cluster_id (only for clusters we have)
    hit_clusters = sorted(ips["gene_cluster_id"].dropna().unique())
    print(f"  clusters with IPS hits: {len(hit_clusters):,}", file=sys.stderr)
    go_parts = []
    path_parts = []
    for batch in chunk(hit_clusters, BATCH):
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
    go_df = pd.concat(go_parts, ignore_index=True) if go_parts else pd.DataFrame(columns=["gene_cluster_id","go_ids"])
    path_df = pd.concat(path_parts, ignore_index=True) if path_parts else pd.DataFrame(columns=["gene_cluster_id","pathways"])
    ips = ips.merge(go_df, on="gene_cluster_id", how="left").merge(path_df, on="gene_cluster_id", how="left")

    # 5. Join back to FB (orgId, locusId) keys via the link
    merged = sub[["orgId","locusId","gene_cluster_id","gtdb_species_clade_id",
                  "pident","evalue","bitscore","is_core","is_auxiliary","is_singleton"]] \
        .merge(ips, on="gene_cluster_id", how="inner")
    print(f"[{time.time()-t0:5.1f}s] joined: {len(merged):,} rows  "
          f"({merged[['orgId','locusId']].drop_duplicates().shape[0]:,} unique training genes covered)",
          file=sys.stderr)

    cols = ["orgId","locusId","gene_cluster_id","gtdb_species_clade_id",
            "is_core","is_auxiliary","is_singleton",
            "pident","evalue","bitscore",
            "analysis","signature_acc","signature_desc",
            "ipr_acc","ipr_desc","start","stop","score",
            "go_ids","pathways"]
    merged[cols].to_csv(OUT_PATH, sep="\t", index=False)
    print(f"[{time.time()-t0:5.1f}s] wrote {OUT_PATH} ({OUT_PATH.stat().st_size/1e6:.1f} MB)",
          file=sys.stderr)


if __name__ == "__main__":
    main()

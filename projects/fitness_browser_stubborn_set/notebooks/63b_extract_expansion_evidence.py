"""
Extract InterPro union + ortholog fitness for the 2,000 expansion
candidate genes (data/random_sample_genes_expansion.parquet), using
the same SQL/pandas pipelines as notebooks 57+58+59 but pointed at
the expansion key set.

Outputs (parallel naming to data/training_set/ for symmetry):
  data/expansion/target_gene_interpro_cluster.tsv
  data/expansion/target_gene_interpro_union.tsv     (consolidated)
  data/expansion/target_gene_ortholog_fitness.tsv
  data/expansion/fb_organism_gtdb_lineage.tsv       (same as training)

We skip the UniProt route (notebook 55) and MD5 route (notebook 56)
for the expansion -- those routes need full BERDL passes and the
cluster route already gives 70.8% coverage, which dominates. The
union here is just `cluster` source; if we later want UniProt/MD5
corroboration for the expansion, we re-run those notebooks with
expansion keys.
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
EXPANSION_PARQUET = PROJECT_DATA / "random_sample_genes_expansion.parquet"
LINEAGE_TRAIN = PROJECT_DATA / "training_set" / "fb_organism_gtdb_lineage.tsv"

OUT_DIR = PROJECT_DATA / "expansion"
INTERPRO_OUT = OUT_DIR / "target_gene_interpro_cluster.tsv"
UNION_OUT = OUT_DIR / "target_gene_interpro_union.tsv"
ORTHO_OUT = OUT_DIR / "target_gene_ortholog_fitness.tsv"
LINEAGE_OUT = OUT_DIR / "fb_organism_gtdb_lineage.tsv"

RANKS = ["domain", "phylum", "class", "order", "family", "genus", "species"]


def chunk(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i+n]


def main() -> None:
    t0 = time.time()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    pool = pd.read_parquet(EXPANSION_PARQUET)
    keys = set(zip(pool["orgId"], pool["locusId"]))
    print(f"expansion keys: {len(keys):,}", file=sys.stderr)

    # ---- 1. Cluster-route InterPro (notebook 57 logic) ----
    link = pd.read_csv(LINK_TSV, sep="\t")
    link["key"] = list(zip(link["orgId"], link["locusId"]))
    sub = link[link["key"].isin(keys)].drop(columns=["key"])
    print(f"expansion rows in link table: {len(sub):,}", file=sys.stderr)
    cluster_ids = sorted(sub["gene_cluster_id"].dropna().unique())
    print(f"unique cluster_ids: {len(cluster_ids):,}", file=sys.stderr)

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
        ips_parts.append(spark.sql(q).toPandas())
    ips = pd.concat(ips_parts, ignore_index=True) if ips_parts else pd.DataFrame()
    print(f"[{time.time()-t0:5.1f}s] IPS rows: {len(ips):,}", file=sys.stderr)

    hit_clusters = sorted(ips["gene_cluster_id"].dropna().unique())
    go_parts, path_parts = [], []
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

    merged = sub[["orgId","locusId","gene_cluster_id","gtdb_species_clade_id",
                  "pident","evalue","bitscore","is_core","is_auxiliary","is_singleton"]] \
        .merge(ips, on="gene_cluster_id", how="inner")

    cols_int = ["orgId","locusId","gene_cluster_id","gtdb_species_clade_id",
                "is_core","is_auxiliary","is_singleton",
                "pident","evalue","bitscore",
                "analysis","signature_acc","signature_desc",
                "ipr_acc","ipr_desc","start","stop","score",
                "go_ids","pathways"]
    merged[cols_int].to_csv(INTERPRO_OUT, sep="\t", index=False)
    print(f"[{time.time()-t0:5.1f}s] wrote {INTERPRO_OUT.name} ({len(merged):,} rows)", file=sys.stderr)

    # ---- 2. Union (single-source: cluster) ----
    union = merged[cols_int].copy()
    union["sources"] = "cluster"
    union["n_sources"] = 1
    union["uniprot_acc"] = ""
    union["md5"] = ""
    union_cols = [
        "orgId", "locusId",
        "ipr_acc", "ipr_desc",
        "analysis", "signature_acc", "signature_desc",
        "start", "stop", "score",
        "go_ids", "pathways",
        "sources", "n_sources",
        "gene_cluster_id", "gtdb_species_clade_id",
        "is_core", "is_auxiliary", "is_singleton",
        "pident", "evalue", "bitscore",
        "uniprot_acc", "md5",
    ]
    # Backfill cluster metadata for genes not in IPS join: left-join from link
    full = sub[["orgId","locusId","gene_cluster_id","gtdb_species_clade_id",
                "is_core","is_auxiliary","is_singleton"]].copy()
    full = full.merge(union[union_cols].drop(columns=[
        "gene_cluster_id","gtdb_species_clade_id",
        "is_core","is_auxiliary","is_singleton"
    ]), on=["orgId","locusId"], how="left")
    for c in ["gene_cluster_id","gtdb_species_clade_id","is_core","is_auxiliary","is_singleton"]:
        full[c] = full[c].fillna("unknown").replace("", "unknown")
    full = full[full["ipr_acc"].notna() | full["signature_acc"].notna()][union_cols]
    full.to_csv(UNION_OUT, sep="\t", index=False)
    print(f"[{time.time()-t0:5.1f}s] wrote {UNION_OUT.name} ({len(full):,} rows)", file=sys.stderr)

    # ---- 3. Ortholog fitness (notebook 59 logic, simplified) ----
    expansion_orgs = sorted({k[0] for k in keys})
    org_in = ",".join(f"'{o}'" for o in expansion_orgs)
    ortho_all = spark.sql(f"""
        SELECT orgId1 AS target_orgId, locusId1 AS target_locusId,
               orgId2 AS ortholog_orgId, locusId2 AS ortholog_locusId,
               try_cast(ratio AS DOUBLE) AS bbh_ratio
        FROM kescience_fitnessbrowser.ortholog
        WHERE orgId1 IN ({org_in})
    """).toPandas()
    print(f"[{time.time()-t0:5.1f}s] orthologs from expansion orgs: {len(ortho_all):,}",
          file=sys.stderr)

    mask = list(zip(ortho_all["target_orgId"], ortho_all["target_locusId"]))
    ortho = ortho_all[[k in keys for k in mask]].reset_index(drop=True)
    print(f"  filtered to expansion target side: {len(ortho):,} pairs", file=sys.stderr)
    if len(ortho) == 0:
        print("no orthologs found, skipping ortholog file", file=sys.stderr)
        return

    ortho_keys = (ortho[["ortholog_orgId", "ortholog_locusId"]].drop_duplicates())
    ortho_orgs = sorted(ortho_keys["ortholog_orgId"].unique())
    ortho_set = set(zip(ortho_keys["ortholog_orgId"], ortho_keys["ortholog_locusId"]))
    org_in_o = ",".join(f"'{o}'" for o in ortho_orgs)

    def _filter_to_ortho(df: pd.DataFrame) -> pd.DataFrame:
        ks = list(zip(df["orgId"], df["locusId"]))
        return df[[k in ortho_set for k in ks]].reset_index(drop=True)

    desc = spark.sql(f"""
        SELECT orgId, locusId, desc AS ortholog_gene_desc, gene AS ortholog_symbol
        FROM kescience_fitnessbrowser.gene WHERE orgId IN ({org_in_o})
    """).toPandas(); desc = _filter_to_ortho(desc)
    fit_sum = spark.sql(f"""
        SELECT orgId, locusId,
               MAX(ABS(try_cast(fit AS DOUBLE))) AS ortholog_max_abs_fit,
               MAX(ABS(try_cast(t   AS DOUBLE))) AS ortholog_max_abs_t,
               SUM(CASE WHEN ABS(try_cast(fit AS DOUBLE))>=1 AND ABS(try_cast(t AS DOUBLE))>=4 THEN 1 ELSE 0 END)
                 AS ortholog_n_strong
        FROM kescience_fitnessbrowser.genefitness WHERE orgId IN ({org_in_o})
        GROUP BY orgId, locusId
    """).toPandas(); fit_sum = _filter_to_ortho(fit_sum)
    top_cond = spark.sql(f"""
        WITH ranked AS (
          SELECT f.orgId, f.locusId,
                 try_cast(f.fit AS DOUBLE) AS fit_signed,
                 try_cast(f.t   AS DOUBLE) AS t_val,
                 e.expDescLong AS condition,
                 ROW_NUMBER() OVER (PARTITION BY f.orgId, f.locusId
                   ORDER BY ABS(try_cast(f.fit AS DOUBLE)) DESC NULLS LAST) AS rn
          FROM kescience_fitnessbrowser.genefitness f
          JOIN kescience_fitnessbrowser.experiment e
            ON f.orgId = e.orgId AND f.expName = e.expName
          WHERE f.orgId IN ({org_in_o}) )
        SELECT orgId, locusId,
               array_join(collect_list(concat('fit=', round(fit_signed,2),
                          ' t=', round(t_val,1), ' cond=', condition)), ' | ') AS ortholog_top_conditions
        FROM ranked WHERE rn <= 3 GROUP BY orgId, locusId
    """).toPandas(); top_cond = _filter_to_ortho(top_cond)
    spec = spark.sql(f"""
        SELECT orgId, locusId, COUNT(*) AS ortholog_n_specific_phenotype
        FROM kescience_fitnessbrowser.specificphenotype WHERE orgId IN ({org_in_o})
        GROUP BY orgId, locusId
    """).toPandas(); spec = _filter_to_ortho(spec)

    df = ortho.merge(desc.rename(columns={"orgId":"ortholog_orgId","locusId":"ortholog_locusId"}),
                     on=["ortholog_orgId","ortholog_locusId"], how="left") \
              .merge(fit_sum.rename(columns={"orgId":"ortholog_orgId","locusId":"ortholog_locusId"}),
                     on=["ortholog_orgId","ortholog_locusId"], how="left") \
              .merge(top_cond.rename(columns={"orgId":"ortholog_orgId","locusId":"ortholog_locusId"}),
                     on=["ortholog_orgId","ortholog_locusId"], how="left") \
              .merge(spec.rename(columns={"orgId":"ortholog_orgId","locusId":"ortholog_locusId"}),
                     on=["ortholog_orgId","ortholog_locusId"], how="left")

    # Reuse training-set GTDB lineage file (already covers all 36 orgs)
    if LINEAGE_TRAIN.exists():
        lineage = pd.read_csv(LINEAGE_TRAIN, sep="\t", dtype=str, keep_default_na=False)
        # Carry through to expansion output unchanged
        lineage.to_csv(LINEAGE_OUT, sep="\t", index=False)
        lin_t = lineage.rename(columns={c: f"target_{c}" for c in RANKS} | {"orgId": "target_orgId"})
        lin_o = lineage.rename(columns={c: f"ortholog_{c}" for c in RANKS} | {"orgId": "ortholog_orgId"})
        df = df.merge(lin_t[["target_orgId"]+[f"target_{r}" for r in RANKS]], on="target_orgId", how="left")
        df = df.merge(lin_o[["ortholog_orgId"]+[f"ortholog_{r}" for r in RANKS]], on="ortholog_orgId", how="left")
        a = df[[f"target_{r}" for r in RANKS]].rename(columns=lambda c: c.replace("target_",""))
        b = df[[f"ortholog_{r}" for r in RANKS]].rename(columns=lambda c: c.replace("ortholog_",""))
        n = pd.Series(0, index=a.index); m = pd.Series(True, index=a.index)
        for r in RANKS:
            eq = m & (a[r].fillna("") == b[r].fillna("")) & a[r].fillna("").astype(bool)
            n += eq.astype(int); m = eq
        df["shared_taxonomic_ranks"] = n
        df["target_gtdb_lineage"]   = df[[f"target_{r}"   for r in RANKS]].fillna("").agg(";".join, axis=1)
        df["ortholog_gtdb_lineage"] = df[[f"ortholog_{r}" for r in RANKS]].fillna("").agg(";".join, axis=1)
        df = df.drop(columns=[f"target_{r}" for r in RANKS] + [f"ortholog_{r}" for r in RANKS])
    else:
        df["shared_taxonomic_ranks"] = ""
        df["target_gtdb_lineage"] = ""
        df["ortholog_gtdb_lineage"] = ""

    cols = ["target_orgId","target_locusId","ortholog_orgId","ortholog_locusId",
            "bbh_ratio","shared_taxonomic_ranks",
            "ortholog_symbol","ortholog_gene_desc",
            "ortholog_max_abs_fit","ortholog_max_abs_t","ortholog_n_strong",
            "ortholog_n_specific_phenotype","ortholog_top_conditions",
            "target_gtdb_lineage","ortholog_gtdb_lineage"]
    df[cols].sort_values(["target_orgId","target_locusId","bbh_ratio"],
                         ascending=[True,True,False]).to_csv(ORTHO_OUT, sep="\t", index=False)
    print(f"[{time.time()-t0:5.1f}s] wrote {ORTHO_OUT.name} ({len(df):,} rows, "
          f"{df[['target_orgId','target_locusId']].drop_duplicates().shape[0]:,} expansion genes covered)",
          file=sys.stderr)


if __name__ == "__main__":
    main()

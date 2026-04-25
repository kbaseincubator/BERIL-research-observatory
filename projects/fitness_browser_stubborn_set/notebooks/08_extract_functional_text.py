"""
Pull the actual TEXT of each functional-annotation source for every gene
in the 35 curated organisms. We previously had only binary flags (does this
gene have an informative SEED desc?) — but the dossier needs the prose.

Outputs (all per-gene aggregations, 1 row per (orgId, locusId)):
  - data/swissprot_hits.parquet      sprotAccession, sprotId, identity,
                                     gene_symbol, sprot_desc, sprot_organism
  - data/domain_hits.parquet         arrays of (domainDb, domainId, domainName,
                                     definition, ec, score, evalue) — top 5
                                     by score per gene
  - data/kegg_hits.parquet           best KO + ko_desc + ko_ecnum
  - data/seed_hits.parquet           seed_desc

Run:
    python projects/fitness_browser_stubborn_set/notebooks/08_extract_functional_text.py
"""
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("SPARK_CONNECT_PROGRESS_BAR_ENABLED", "false")

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import pandas as pd  # noqa: E402

from get_spark_session import get_spark_session  # noqa: E402

PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"
FEATURES_PATH = PROJECT_DATA / "gene_evidence_features.parquet"

OUT_SWISS = PROJECT_DATA / "swissprot_hits.parquet"
OUT_DOMAIN = PROJECT_DATA / "domain_hits.parquet"
OUT_KEGG = PROJECT_DATA / "kegg_hits.parquet"
OUT_SEED = PROJECT_DATA / "seed_hits.parquet"


def main() -> None:
    t0 = time.time()
    feats = pd.read_parquet(FEATURES_PATH)
    curated_orgs = sorted(feats.loc[feats.is_reannotated == 1, "orgId"].unique())
    print(f"Curated organisms: {len(curated_orgs)}")

    spark = get_spark_session()
    print(f"[{time.time()-t0:5.1f}s] Spark session OK")
    org_list = "', '".join(curated_orgs)

    # 1. SwissProt hit + curated description
    print(f"[{time.time()-t0:5.1f}s] SwissProt hits...")
    swiss = spark.sql(f"""
        SELECT
          bw.orgId, bw.locusId,
          bw.sprotAccession,
          bw.sprotId,
          CAST(bw.identity AS DOUBLE) AS identity,
          sd.geneName AS sprot_gene,
          sd.desc     AS sprot_desc,
          sd.organism AS sprot_organism
        FROM kescience_fitnessbrowser.besthitswissprot bw
        LEFT JOIN kescience_fitnessbrowser.swissprotdesc sd
          ON bw.sprotId = sd.sprotId
        WHERE bw.orgId IN ('{org_list}')
    """).toPandas()
    swiss.attrs = {}
    print(f"  {len(swiss):,} SwissProt-hit rows")
    swiss.to_parquet(OUT_SWISS, index=False)
    print(f"  Wrote {OUT_SWISS}  ({OUT_SWISS.stat().st_size/1e6:.1f} MB)")

    # 2. Top-5 domain hits per gene (by score). Multiple domains per gene OK.
    print(f"[{time.time()-t0:5.1f}s] Domain hits (top 5 per gene by score)...")
    domains = spark.sql(f"""
        WITH ranked AS (
          SELECT orgId, locusId, domainDb, domainId, domainName,
                 definition, ec, geneSymbol,
                 CAST(score  AS DOUBLE) AS score,
                 CAST(evalue AS DOUBLE) AS evalue,
                 ROW_NUMBER() OVER (PARTITION BY orgId, locusId
                                     ORDER BY CAST(score AS DOUBLE) DESC) AS rk
          FROM kescience_fitnessbrowser.genedomain
          WHERE orgId IN ('{org_list}')
        )
        SELECT orgId, locusId, domainDb, domainId, domainName,
               definition, ec, geneSymbol, score, evalue
        FROM ranked WHERE rk <= 5
    """).toPandas()
    domains.attrs = {}
    print(f"  {len(domains):,} domain-hit rows | "
          f"{domains.groupby(['orgId','locusId']).ngroups:,} distinct genes")
    domains.to_parquet(OUT_DOMAIN, index=False)
    print(f"  Wrote {OUT_DOMAIN}  ({OUT_DOMAIN.stat().st_size/1e6:.1f} MB)")

    # 3. KEGG hit: best KO + description + EC (two-hop join + kgroupdesc + kgroupec)
    print(f"[{time.time()-t0:5.1f}s] KEGG KO hits with descriptions...")
    kegg = spark.sql(f"""
        WITH ranked AS (
          SELECT bhk.orgId, bhk.locusId, km.kgroup,
                 kd.desc       AS ko_desc,
                 ke.ecnum      AS ko_ecnum,
                 CAST(bhk.identity AS DOUBLE) AS identity,
                 ROW_NUMBER() OVER (PARTITION BY bhk.orgId, bhk.locusId
                                     ORDER BY CAST(bhk.identity AS DOUBLE) DESC) AS rk
          FROM kescience_fitnessbrowser.besthitkegg bhk
          JOIN kescience_fitnessbrowser.keggmember km
            ON bhk.keggOrg = km.keggOrg AND bhk.keggId = km.keggId
          LEFT JOIN kescience_fitnessbrowser.kgroupdesc kd
            ON km.kgroup = kd.kgroup
          LEFT JOIN kescience_fitnessbrowser.kgroupec ke
            ON km.kgroup = ke.kgroup
          WHERE bhk.orgId IN ('{org_list}')
        )
        SELECT orgId, locusId, kgroup, ko_desc, ko_ecnum, identity
        FROM ranked WHERE rk = 1
    """).toPandas()
    kegg.attrs = {}
    print(f"  {len(kegg):,} KEGG-hit rows")
    kegg.to_parquet(OUT_KEGG, index=False)
    print(f"  Wrote {OUT_KEGG}  ({OUT_KEGG.stat().st_size/1e6:.1f} MB)")

    # 4. SEED desc (concatenate multiple descriptions per gene)
    print(f"[{time.time()-t0:5.1f}s] SEED descriptions...")
    seed = spark.sql(f"""
        SELECT orgId, locusId, seed_desc
        FROM kescience_fitnessbrowser.seedannotation
        WHERE orgId IN ('{org_list}')
          AND seed_desc IS NOT NULL AND seed_desc != ''
    """).toPandas()
    seed.attrs = {}
    print(f"  {len(seed):,} SEED-hit rows")
    seed.to_parquet(OUT_SEED, index=False)
    print(f"  Wrote {OUT_SEED}  ({OUT_SEED.stat().st_size/1e6:.1f} MB)")


if __name__ == "__main__":
    main()

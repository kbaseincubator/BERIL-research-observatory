"""
Extract secondary evidence flags for every Fitness Browser gene in the 36
curated organisms (those with at least one reannotation). Saves one local
parquet for NB02 to walk through.

Six binary flags per (orgId, locusId):
  - informative_domain      : any genedomain hit with EC or non-DUF definition
  - informative_kegg_ko     : KO with non-"uncharacterized" description
                              (besthitkegg -> keggmember -> kgroupdesc)
  - informative_kegg_ec     : KO with non-null kgroupec.ecnum
  - informative_seed        : seedannotation.seed_desc not hypothetical
  - conserved_spec_phenotype: in specog with nInOG >= 2 (multi-org)
  - conserved_cofit         : has a cofit pair >= 0.6 whose orthologs
                              also have a cofit pair >= 0.6

Run with .venv-berdl active and the BERDL proxy chain up:
    source .venv-berdl/bin/activate
    python projects/fitness_browser_stubborn_set/notebooks/02_extract_secondary_evidence.py
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
OUT_PATH = PROJECT_DATA / "gene_secondary_evidence.parquet"

FEATURES_PATH = PROJECT_DATA / "gene_evidence_features.parquet"
assert FEATURES_PATH.exists(), "Run 00_extract_gene_features.py first"


def main() -> None:
    t0 = time.time()
    feats = pd.read_parquet(FEATURES_PATH)
    curated_orgs = sorted(feats.loc[feats.is_reannotated == 1, "orgId"].unique())
    print(f"Curated organisms: {len(curated_orgs)}")

    spark = get_spark_session()
    print(f"[{time.time()-t0:5.1f}s] Spark session OK")
    org_list = "', '".join(curated_orgs)

    # Base set: every (orgId, locusId) in curated orgs that has fitness data.
    base = spark.sql(f"""
        SELECT DISTINCT orgId, locusId
        FROM kescience_fitnessbrowser.genefitness
        WHERE orgId IN ('{org_list}')
    """)

    # 1. informative_domain: any genedomain hit with EC, OR a non-DUF definition.
    informative_domain = spark.sql(f"""
        SELECT DISTINCT orgId, locusId, 1 AS informative_domain
        FROM kescience_fitnessbrowser.genedomain
        WHERE orgId IN ('{org_list}')
          AND (
            (ec IS NOT NULL AND ec != '' AND ec != '-')
            OR (
              LOWER(COALESCE(definition, '')) NOT LIKE '%domain of unknown function%'
              AND LOWER(COALESCE(definition, '')) NOT LIKE '%uncharacterized%'
              AND LOWER(COALESCE(domainName, '')) NOT LIKE 'duf%'
              AND LOWER(COALESCE(domainName, '')) NOT LIKE 'upf%'
              AND COALESCE(definition, '') != ''
              AND COALESCE(domainName, '') != ''
            )
          )
    """)

    # 2. informative_kegg_ko: two-hop KO mapping; description is informative.
    informative_kegg_ko = spark.sql(f"""
        SELECT DISTINCT bhk.orgId, bhk.locusId, 1 AS informative_kegg_ko
        FROM kescience_fitnessbrowser.besthitkegg bhk
        JOIN kescience_fitnessbrowser.keggmember km
          ON bhk.keggOrg = km.keggOrg AND bhk.keggId = km.keggId
        JOIN kescience_fitnessbrowser.kgroupdesc kd
          ON km.kgroup = kd.kgroup
        WHERE bhk.orgId IN ('{org_list}')
          AND kd.desc IS NOT NULL AND kd.desc != ''
          AND LOWER(kd.desc) NOT LIKE '%uncharacterized%'
          AND LOWER(kd.desc) NOT LIKE '%hypothetical%'
          AND LOWER(kd.desc) NOT LIKE '%unknown function%'
    """)

    # 3. informative_kegg_ec: KO has an EC number via kgroupec.ecnum.
    informative_kegg_ec = spark.sql(f"""
        SELECT DISTINCT bhk.orgId, bhk.locusId, 1 AS informative_kegg_ec
        FROM kescience_fitnessbrowser.besthitkegg bhk
        JOIN kescience_fitnessbrowser.keggmember km
          ON bhk.keggOrg = km.keggOrg AND bhk.keggId = km.keggId
        JOIN kescience_fitnessbrowser.kgroupec ke
          ON km.kgroup = ke.kgroup
        WHERE bhk.orgId IN ('{org_list}')
          AND ke.ecnum IS NOT NULL AND ke.ecnum != ''
    """)

    # 4. informative_seed: seedannotation.seed_desc not hypothetical/uncharacterized.
    informative_seed = spark.sql(f"""
        SELECT DISTINCT orgId, locusId, 1 AS informative_seed
        FROM kescience_fitnessbrowser.seedannotation
        WHERE orgId IN ('{org_list}')
          AND seed_desc IS NOT NULL AND seed_desc != ''
          AND LOWER(seed_desc) NOT LIKE '%hypothetical%'
          AND LOWER(seed_desc) NOT LIKE '%uncharacterized%'
          AND LOWER(seed_desc) NOT LIKE '%unknown function%'
          AND LOWER(seed_desc) NOT LIKE '%putative%'
    """)

    # 5. conserved_spec_phenotype: in specog with nInOG >= 2 (signal is shared
    # across at least 2 orthologous genes in different organisms).
    conserved_spec = spark.sql(f"""
        SELECT DISTINCT orgId, locusId, 1 AS conserved_spec_phenotype
        FROM kescience_fitnessbrowser.specog
        WHERE orgId IN ('{org_list}')
          AND CAST(nInOG AS INT) >= 2
    """)

    # 6. conserved_cofit: this gene has at least one cofit pair (l, h) with
    # cofit >= 0.6 in this org, AND in at least one OTHER organism the
    # orthologs (l', h') of (l, h) also have cofit >= 0.6.
    #
    # Implementation: filter cofit to >= 0.6 first (call it strong),
    # then 4-way self-join via two ortholog hops.
    # This is the most expensive query — uses Spark to join on (orgId, locusId, hitId).
    spark.sql(f"""
        CREATE OR REPLACE TEMP VIEW strong_cofit AS
        SELECT orgId, locusId, hitId, CAST(cofit AS DOUBLE) AS cofit
        FROM kescience_fitnessbrowser.cofit
        WHERE orgId IN ('{org_list}')
          AND CAST(cofit AS DOUBLE) >= 0.6
    """)
    spark.sql(f"""
        CREATE OR REPLACE TEMP VIEW orth AS
        SELECT orgId1, locusId1, orgId2, locusId2
        FROM kescience_fitnessbrowser.ortholog
        WHERE orgId1 IN ('{org_list}') AND orgId2 IN ('{org_list}')
    """)

    conserved_cofit = spark.sql("""
        SELECT DISTINCT a.orgId AS orgId, a.locusId AS locusId, 1 AS conserved_cofit
        FROM strong_cofit a
        JOIN orth o1
          ON a.orgId = o1.orgId1 AND a.locusId = o1.locusId1
        JOIN orth o2
          ON a.orgId = o2.orgId1 AND a.hitId   = o2.locusId1
         AND o1.orgId2 = o2.orgId2
        JOIN strong_cofit b
          ON  b.orgId   = o1.orgId2
          AND b.locusId = o1.locusId2
          AND b.hitId   = o2.locusId2
    """)

    # Combine all flags onto the base set.
    secondary = (
        base
        .join(informative_domain,    on=["orgId", "locusId"], how="left")
        .join(informative_kegg_ko,   on=["orgId", "locusId"], how="left")
        .join(informative_kegg_ec,   on=["orgId", "locusId"], how="left")
        .join(informative_seed,      on=["orgId", "locusId"], how="left")
        .join(conserved_spec,        on=["orgId", "locusId"], how="left")
        .join(conserved_cofit,       on=["orgId", "locusId"], how="left")
        .fillna({
            "informative_domain": 0,
            "informative_kegg_ko": 0,
            "informative_kegg_ec": 0,
            "informative_seed": 0,
            "conserved_spec_phenotype": 0,
            "conserved_cofit": 0,
        })
    )

    print(f"[{time.time()-t0:5.1f}s] Pulling secondary evidence to driver (pandas)...")
    pdf = secondary.toPandas()
    pdf.attrs = {}
    print(f"[{time.time()-t0:5.1f}s] Got {len(pdf):,} rows")
    print(pdf.head().to_string())
    print("\nFlag totals:")
    flag_cols = ["informative_domain", "informative_kegg_ko", "informative_kegg_ec",
                 "informative_seed", "conserved_spec_phenotype", "conserved_cofit"]
    for c in flag_cols:
        n = int(pdf[c].astype(int).sum())
        print(f"  {c:30}: {n:>7,}")

    pdf.to_parquet(OUT_PATH, index=False)
    print(f"[{time.time()-t0:5.1f}s] Wrote {OUT_PATH}  ({OUT_PATH.stat().st_size/1e6:.1f} MB)")


if __name__ == "__main__":
    main()

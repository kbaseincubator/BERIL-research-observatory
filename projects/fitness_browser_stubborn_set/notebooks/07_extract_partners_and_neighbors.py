"""
Two more dossier-content extracts that were initially abstracted away:

1. **Top cofitness partners** per gene (#4 from the evidence inventory): for
   each FB gene, the top 10 cofit partners with their cofit value, the
   partner's gene_symbol, and the partner's existing gene.desc. Curators read
   "this gene cofits with hisG, hisD, hisI" to infer pathway membership.

2. **Gene neighborhood** per gene (#17): the genes within +/- 5 positions on
   the same scaffold (operon context). Curators use this constantly — Price
   2018 reannotation comments often say "in a gene cluster that also includes
   hutD and imidazolonepropionase".

Outputs:
  - data/cofit_partners_top10.parquet
  - data/gene_neighborhood.parquet

Run:
    python projects/fitness_browser_stubborn_set/notebooks/07_extract_partners_and_neighbors.py
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
PARTNERS_OUT = PROJECT_DATA / "cofit_partners_top10.parquet"
NEIGHBORS_OUT = PROJECT_DATA / "gene_neighborhood.parquet"

TOP_COFIT_PARTNERS = 10
NEIGHBOR_RADIUS = 5  # positions either side


def main() -> None:
    t0 = time.time()
    feats = pd.read_parquet(FEATURES_PATH)
    curated_orgs = sorted(feats.loc[feats.is_reannotated == 1, "orgId"].unique())
    print(f"Curated organisms: {len(curated_orgs)}")

    spark = get_spark_session()
    print(f"[{time.time()-t0:5.1f}s] Spark session OK")
    org_list = "', '".join(curated_orgs)

    # 1. Top cofit partners per gene with the partner's existing annotation
    # cofit table is large — filter early to >= 0.5 cofit (looser than C3 so
    # we can show the actual top regardless), then rank by cofit desc per gene.
    print(f"[{time.time()-t0:5.1f}s] Pulling top cofit partners per gene with annotations...")
    partners = spark.sql(f"""
        WITH ranked AS (
          SELECT c.orgId, c.locusId, c.hitId,
                 CAST(c.cofit AS DOUBLE) AS cofit,
                 CAST(c.rank  AS INT)    AS partner_rank,
                 ROW_NUMBER() OVER (PARTITION BY c.orgId, c.locusId
                                     ORDER BY CAST(c.cofit AS DOUBLE) DESC) AS rk
          FROM kescience_fitnessbrowser.cofit c
          WHERE c.orgId IN ('{org_list}')
            AND CAST(c.cofit AS DOUBLE) >= 0.5
        )
        SELECT r.orgId, r.locusId, r.hitId,
               r.cofit, r.partner_rank,
               g.gene  AS partner_gene_symbol,
               g.desc  AS partner_gene_desc
        FROM ranked r
        LEFT JOIN kescience_fitnessbrowser.gene g
          ON r.orgId = g.orgId AND r.hitId = g.locusId
        WHERE r.rk <= {TOP_COFIT_PARTNERS}
    """).toPandas()
    partners.attrs = {}
    print(f"  {len(partners):,} (gene, partner) rows | "
          f"{partners.groupby(['orgId','locusId']).ngroups:,} distinct genes covered")

    partners.to_parquet(PARTNERS_OUT, index=False)
    print(f"  Wrote {PARTNERS_OUT}  ({PARTNERS_OUT.stat().st_size/1e6:.1f} MB)")

    # 2. Gene neighborhood — within ±NEIGHBOR_RADIUS positions on same scaffold
    # We need a position index (row_number ordered by begin) to compute
    # neighbors. Cast begin to int.
    print(f"[{time.time()-t0:5.1f}s] Computing gene neighborhood (±{NEIGHBOR_RADIUS} positions)...")
    neighbors = spark.sql(f"""
        WITH g AS (
          SELECT orgId, scaffoldId, locusId, gene, desc,
                 CAST(begin AS BIGINT) AS begin_pos,
                 CAST(end   AS BIGINT) AS end_pos,
                 strand,
                 ROW_NUMBER() OVER (PARTITION BY orgId, scaffoldId
                                     ORDER BY CAST(begin AS BIGINT)) AS pos_idx
          FROM kescience_fitnessbrowser.gene
          WHERE orgId IN ('{org_list}')
            AND begin IS NOT NULL AND begin != ''
        )
        SELECT
          a.orgId, a.locusId,
          a.scaffoldId, a.pos_idx     AS gene_pos_idx,
          b.locusId  AS neighbor_locusId,
          b.gene     AS neighbor_gene_symbol,
          b.desc     AS neighbor_gene_desc,
          b.strand   AS neighbor_strand,
          b.pos_idx  AS neighbor_pos_idx,
          (b.pos_idx - a.pos_idx) AS offset
        FROM g a
        JOIN g b
          ON a.orgId = b.orgId
         AND a.scaffoldId = b.scaffoldId
         AND b.pos_idx BETWEEN a.pos_idx - {NEIGHBOR_RADIUS} AND a.pos_idx + {NEIGHBOR_RADIUS}
         AND a.locusId != b.locusId
    """).toPandas()
    neighbors.attrs = {}
    print(f"  {len(neighbors):,} neighbor rows | "
          f"{neighbors.groupby(['orgId','locusId']).ngroups:,} distinct genes covered")

    neighbors.to_parquet(NEIGHBORS_OUT, index=False)
    print(f"  Wrote {NEIGHBORS_OUT}  ({NEIGHBORS_OUT.stat().st_size/1e6:.1f} MB)")

    # Spot-check a sample
    print("\nSample partner rows:")
    sample = partners[partners.cofit >= 0.85].head(8)
    print(sample[["orgId", "locusId", "hitId", "cofit", "partner_gene_desc"]].to_string(index=False))
    print("\nSample neighborhood rows:")
    s2 = neighbors.head(8)
    print(s2[["orgId", "locusId", "neighbor_locusId", "offset", "neighbor_gene_desc"]].to_string(index=False))


if __name__ == "__main__":
    main()

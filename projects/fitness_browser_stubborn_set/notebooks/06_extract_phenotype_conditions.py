"""
Extract per-gene phenotype-with-condition records — the actual experiments
where each FB gene shows a strong or specific phenotype, with the experiment
metadata (carbon source, nitrogen source, stress type, etc.) attached.

This is what curators actually reason over: "specifically sick on D-mannose"
or "important under cisplatin stress at 20 uM". Without this, the dossier
has only fit-magnitude aggregates and no semantic content about the
phenotype.

Pulls two record types per gene in the 35 curated orgs:
  - All `specificphenotype` rows + condition metadata + (fit, t) values
  - Up to 10 strongest phenotypes (|fit|>=2 AND |t|>=5) by |fit|

Output: data/phenotype_conditions.parquet — one row per
(orgId, locusId, expName) with `record_type` ∈ {specific, strong}.

Run:
    python projects/fitness_browser_stubborn_set/notebooks/06_extract_phenotype_conditions.py
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
OUT_PATH = PROJECT_DATA / "phenotype_conditions.parquet"

TOP_STRONG_PER_GENE = 10  # cap on # strong-phenotype rows per gene


def main() -> None:
    t0 = time.time()
    feats = pd.read_parquet(FEATURES_PATH)
    curated_orgs = sorted(feats.loc[feats.is_reannotated == 1, "orgId"].unique())
    print(f"Curated organisms: {len(curated_orgs)}")

    spark = get_spark_session()
    print(f"[{time.time()-t0:5.1f}s] Spark session OK")
    org_list = "', '".join(curated_orgs)

    # 1. All specific-phenotype rows + condition + (fit, t)
    print(f"[{time.time()-t0:5.1f}s] Pulling specific-phenotype rows with conditions...")
    specific = spark.sql(f"""
        SELECT
          sp.orgId, sp.locusId, sp.expName,
          'specific' AS record_type,
          CAST(gf.fit AS DOUBLE) AS fit,
          CAST(gf.t   AS DOUBLE) AS t,
          e.expGroup, e.expDesc, e.expDescLong,
          e.condition_1, e.units_1, e.concentration_1,
          e.condition_2, e.condition_3, e.condition_4,
          e.media, e.temperature, e.pH, e.aerobic
        FROM kescience_fitnessbrowser.specificphenotype sp
        JOIN kescience_fitnessbrowser.experiment e
          ON sp.orgId = e.orgId AND sp.expName = e.expName
        LEFT JOIN kescience_fitnessbrowser.genefitness gf
          ON sp.orgId = gf.orgId AND sp.locusId = gf.locusId AND sp.expName = gf.expName
        WHERE sp.orgId IN ('{org_list}')
    """).toPandas()
    specific.attrs = {}
    print(f"  {len(specific):,} specific-phenotype rows")

    # 2. Top-N strong phenotypes per gene by |fit|, with conditions
    # (limited to TOP_STRONG_PER_GENE per gene via ROW_NUMBER window)
    print(f"[{time.time()-t0:5.1f}s] Pulling top-{TOP_STRONG_PER_GENE} strong-phenotype rows per gene...")
    strong = spark.sql(f"""
        WITH gf AS (
          SELECT orgId, locusId, expName,
                 CAST(fit AS DOUBLE) AS fit,
                 CAST(t   AS DOUBLE) AS t
          FROM kescience_fitnessbrowser.genefitness
          WHERE orgId IN ('{org_list}')
            AND ABS(CAST(fit AS DOUBLE)) >= 2.0
            AND ABS(CAST(t   AS DOUBLE)) >= 5.0
        ),
        ranked AS (
          SELECT *, ROW_NUMBER() OVER (PARTITION BY orgId, locusId ORDER BY ABS(fit) DESC) AS rk
          FROM gf
        )
        SELECT
          r.orgId, r.locusId, r.expName,
          'strong' AS record_type,
          r.fit, r.t,
          e.expGroup, e.expDesc, e.expDescLong,
          e.condition_1, e.units_1, e.concentration_1,
          e.condition_2, e.condition_3, e.condition_4,
          e.media, e.temperature, e.pH, e.aerobic
        FROM ranked r
        JOIN kescience_fitnessbrowser.experiment e
          ON r.orgId = e.orgId AND r.expName = e.expName
        WHERE r.rk <= {TOP_STRONG_PER_GENE}
    """).toPandas()
    strong.attrs = {}
    print(f"  {len(strong):,} strong-phenotype rows")

    # Combine (some rows will appear in both — dedupe on the key, prefer 'specific' tag)
    combined = pd.concat([specific, strong], ignore_index=True)
    combined = combined.sort_values(
        ["orgId", "locusId", "expName", "record_type"],
        # prefer 'specific' over 'strong' on duplicate
    )
    combined = combined.drop_duplicates(subset=["orgId", "locusId", "expName"], keep="first")

    print(f"[{time.time()-t0:5.1f}s] Combined: {len(combined):,} rows | "
          f"{combined.groupby(['orgId','locusId']).ngroups:,} distinct genes")
    print(f"  records by type:\n{combined['record_type'].value_counts().to_string()}")

    combined.to_parquet(OUT_PATH, index=False)
    print(f"[{time.time()-t0:5.1f}s] Wrote {OUT_PATH}  "
          f"({OUT_PATH.stat().st_size/1e6:.1f} MB)")

    # Quick spot-check: show one gene's records
    print("\nSample — one gene's phenotype-with-condition rows:")
    sample_gene = (combined
                   .groupby(['orgId','locusId'])
                   .size().sort_values(ascending=False).head(1)
                   .reset_index().iloc[0])
    sg = combined[(combined.orgId == sample_gene.orgId) & (combined.locusId == sample_gene.locusId)]
    print(sg[["expGroup", "condition_1", "fit", "t", "record_type"]].head(10).to_string(index=False))


if __name__ == "__main__":
    main()

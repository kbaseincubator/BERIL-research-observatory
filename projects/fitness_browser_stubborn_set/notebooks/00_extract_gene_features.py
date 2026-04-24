"""
Extract per-gene evidence features for every Fitness Browser gene, plus the
reannotation flag. Runs Spark Connect via the local .venv-berdl + proxy chain
and saves a single pandas Parquet file to projects/.../data/.

This step is kept out of the Jupyter notebook because Spark Connect's
PlanMetrics output is not JSON-serializable and breaks nbconvert saves.
Keep notebooks pandas-only; do Spark extraction here.

Run from the repo root with .venv-berdl active:
    source .venv-berdl/bin/activate
    python projects/fitness_browser_stubborn_set/notebooks/00_extract_gene_features.py
"""

import os
import sys
import time
from pathlib import Path

os.environ.setdefault("SPARK_CONNECT_PROGRESS_BAR_ENABLED", "false")

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from get_spark_session import get_spark_session  # noqa: E402

PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"
PROJECT_DATA.mkdir(parents=True, exist_ok=True)

OUT_PATH = PROJECT_DATA / "gene_evidence_features.parquet"


def main() -> None:
    t0 = time.time()
    spark = get_spark_session()
    print(f"[{time.time()-t0:5.1f}s] Spark session OK: {spark.version}")

    # Per-gene fitness summary (one pass over genefitness, 27M rows)
    gf = spark.sql(
        """
        SELECT
          orgId,
          locusId,
          MAX(ABS(CAST(fit AS DOUBLE))) AS max_abs_fit,
          MAX(ABS(CAST(t   AS DOUBLE))) AS max_abs_t,
          SUM(CASE WHEN ABS(CAST(fit AS DOUBLE)) >= 2.0
                    AND ABS(CAST(t   AS DOUBLE)) >= 5.0 THEN 1 ELSE 0 END) AS n_strong_experiments,
          SUM(CASE WHEN ABS(CAST(fit AS DOUBLE)) >= 1.0
                    AND ABS(CAST(t   AS DOUBLE)) >= 5.0 THEN 1 ELSE 0 END) AS n_moderate_experiments
        FROM kescience_fitnessbrowser.genefitness
        GROUP BY orgId, locusId
        """
    )

    sp_flags = spark.sql(
        """
        SELECT DISTINCT orgId, locusId, 1 AS in_specificphenotype
        FROM kescience_fitnessbrowser.specificphenotype
        """
    )

    cofit_stats = spark.sql(
        """
        SELECT orgId, locusId, MAX(CAST(cofit AS DOUBLE)) AS max_cofit
        FROM kescience_fitnessbrowser.cofit
        GROUP BY orgId, locusId
        """
    )

    reann = spark.sql(
        """
        SELECT DISTINCT orgId, locusId, 1 AS is_reannotated
        FROM kescience_fitnessbrowser.reannotation
        """
    )

    # Gene table: existing description + symbol for annotation-category analysis
    gene_desc = spark.sql(
        """
        SELECT orgId, locusId, gene AS gene_symbol, desc AS gene_desc
        FROM kescience_fitnessbrowser.gene
        """
    )

    joined = (
        gf
        .join(sp_flags, on=["orgId", "locusId"], how="left")
        .join(cofit_stats, on=["orgId", "locusId"], how="left")
        .join(reann, on=["orgId", "locusId"], how="left")
        .join(gene_desc, on=["orgId", "locusId"], how="left")
        .fillna({"in_specificphenotype": 0, "max_cofit": 0.0, "is_reannotated": 0,
                 "gene_symbol": "", "gene_desc": ""})
    )

    print(f"[{time.time()-t0:5.1f}s] Pulling results to driver (pandas)...")
    pdf = joined.toPandas()
    # Spark Connect attaches non-JSON-serializable PlanMetrics to df.attrs;
    # pandas.to_parquet serializes attrs into parquet metadata and crashes.
    pdf.attrs = {}
    print(f"[{time.time()-t0:5.1f}s] Got {len(pdf):,} rows, {len(pdf.columns)} columns")
    print(pdf.head())

    pdf.to_parquet(OUT_PATH, index=False)
    print(f"[{time.time()-t0:5.1f}s] Wrote {OUT_PATH}  ({OUT_PATH.stat().st_size/1e6:.1f} MB)")

    # Quick summary stats for sanity
    n_reann = int(pdf["is_reannotated"].sum())
    n_sp = int(pdf["in_specificphenotype"].sum())
    n_strong = int((pdf["n_strong_experiments"] >= 1).sum())
    n_cofit = int((pdf["max_cofit"] >= 0.75).sum())
    print(f"\nSanity check:")
    print(f"  reannotated (with fitness data): {n_reann}")
    print(f"  in specificphenotype:            {n_sp}")
    print(f"  with strong phenotype:           {n_strong}")
    print(f"  with max_cofit >= 0.75:          {n_cofit}")


if __name__ == "__main__":
    main()

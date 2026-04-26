"""
Pull the kescience_fitnessbrowser.reannotation table from BERDL into a
local parquet. Captures the curator's annotation, comment, and the
pre-curation gene description — the latter is critical for the
contamination-controlled dossier build.

Output: data/reannotation_set.parquet
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"
OUT_PATH = PROJECT_DATA / "reannotation_set.parquet"


def main() -> None:
    # Lazy import — requires .venv-berdl to be active
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from get_spark_session import get_spark_session  # type: ignore

    spark = get_spark_session()
    # The BERDL reannotation table has only 4 columns (verified 2026-04-26):
    # orgId, locusId, new_annotation, comment. We join `gene.desc` from the
    # gene table and also derive original_description from the local 456-gene
    # FEBA file in 22_prepare_reann_batches.py.
    df = spark.sql(
        """
        SELECT
            r.orgId,
            r.locusId,
            r.new_annotation,
            r.comment,
            g.desc AS current_gene_desc_in_berdl,
            g.gene AS current_gene_symbol_in_berdl
        FROM kescience_fitnessbrowser.reannotation r
        LEFT JOIN kescience_fitnessbrowser.gene g
          ON r.orgId = g.orgId AND r.locusId = g.locusId
        """
    )
    pdf = df.toPandas()
    pdf.attrs = {}
    print(f"Pulled {len(pdf):,} reannotation rows", file=sys.stderr)
    print(f"Columns: {list(pdf.columns)}", file=sys.stderr)
    print(f"Distinct orgId: {pdf['orgId'].nunique()}", file=sys.stderr)
    print(f"Has new_annotation: {pdf['new_annotation'].notna().sum()}", file=sys.stderr)
    print(f"Has comment: {pdf['comment'].notna().sum()}", file=sys.stderr)
    print(f"Has current gene_desc: {pdf['current_gene_desc_in_berdl'].notna().sum()}", file=sys.stderr)

    # Quick contamination read: how often is BERDL's current gene.desc identical
    # to the curator's new_annotation (case-insensitive, trimmed)?
    a = pdf["current_gene_desc_in_berdl"].fillna("").str.strip().str.lower()
    b = pdf["new_annotation"].fillna("").str.strip().str.lower()
    n_eq = int((a == b).sum())
    print(f"\nContamination check: gene.desc == new_annotation in {n_eq}/{len(pdf)} rows "
          f"({100*n_eq/len(pdf):.1f}%)", file=sys.stderr)

    pdf.to_parquet(OUT_PATH, index=False)
    print(f"Wrote {OUT_PATH}", file=sys.stderr)


if __name__ == "__main__":
    main()

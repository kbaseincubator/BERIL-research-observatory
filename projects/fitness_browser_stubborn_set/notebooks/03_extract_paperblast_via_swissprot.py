"""
Stage 1 of PaperBLAST integration: ID-based join from FB's pre-computed
SwissProt hits (kescience_fitnessbrowser.besthitswissprot, RAPSearch2 at
>=80% coverage / >=30% identity) to PaperBLAST entries (kescience_paperblast.
gene + genepaper + snippet).

Output: per-FB-gene PaperBLAST evidence (papers count, top paper, top
snippet, the matched SwissProt accession + identity). This covers the ~18%
of SwissProt-hit FB genes whose accession is also a PaperBLAST geneId
directly. The remaining ~82% will be covered by Stage 2 (DIAMOND).

Run:
    source .venv-berdl/bin/activate
    python projects/fitness_browser_stubborn_set/notebooks/03_extract_paperblast_via_swissprot.py
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
OUT_PATH = PROJECT_DATA / "paperblast_via_swissprot.parquet"

FEATURES_PATH = PROJECT_DATA / "gene_evidence_features.parquet"


def main() -> None:
    t0 = time.time()
    feats = pd.read_parquet(FEATURES_PATH)
    curated_orgs = sorted(feats.loc[feats.is_reannotated == 1, "orgId"].unique())
    print(f"Curated organisms: {len(curated_orgs)}")

    spark = get_spark_session()
    print(f"[{time.time()-t0:5.1f}s] Spark session OK")
    org_list = "', '".join(curated_orgs)

    # Per FB gene: SwissProt accession + identity, then number of PaperBLAST
    # papers via geneId or sprotId match.
    pb = spark.sql(f"""
        WITH fb_swiss AS (
          SELECT
            orgId, locusId,
            sprotAccession,
            sprotId,
            CAST(identity AS DOUBLE) AS identity
          FROM kescience_fitnessbrowser.besthitswissprot
          WHERE orgId IN ('{org_list}')
        ),
        pb_keys AS (
          -- (sprotAccession, geneId) and (sprotId, geneId) candidate pairs
          SELECT fs.orgId, fs.locusId, fs.sprotAccession, fs.sprotId, fs.identity, pg.geneId, pg.organism AS pb_organism, pg.desc AS pb_desc
          FROM fb_swiss fs
          JOIN kescience_paperblast.gene pg ON pg.geneId = fs.sprotAccession
          UNION
          SELECT fs.orgId, fs.locusId, fs.sprotAccession, fs.sprotId, fs.identity, pg.geneId, pg.organism, pg.desc
          FROM fb_swiss fs
          JOIN kescience_paperblast.gene pg ON pg.geneId = fs.sprotId
          UNION
          -- via seqtoduplicate
          SELECT fs.orgId, fs.locusId, fs.sprotAccession, fs.sprotId, fs.identity, sd.sequence_id AS geneId, NULL AS pb_organism, NULL AS pb_desc
          FROM fb_swiss fs
          JOIN kescience_paperblast.seqtoduplicate sd ON sd.duplicate_id = fs.sprotAccession
        ),
        paper_counts AS (
          SELECT pk.orgId, pk.locusId, pk.sprotAccession, pk.sprotId, pk.identity,
                 ANY_VALUE(pk.pb_organism) AS pb_organism,
                 ANY_VALUE(pk.pb_desc)     AS pb_desc,
                 COUNT(DISTINCT gp.pmId)   AS n_papers,
                 MIN(gp.pmId)              AS top_pmid,
                 ANY_VALUE(gp.title)       AS top_title
          FROM pb_keys pk
          LEFT JOIN kescience_paperblast.genepaper gp ON gp.geneId = pk.geneId
          GROUP BY pk.orgId, pk.locusId, pk.sprotAccession, pk.sprotId, pk.identity
        )
        SELECT * FROM paper_counts
        WHERE n_papers > 0
    """)

    print(f"[{time.time()-t0:5.1f}s] Pulling PaperBLAST evidence to driver...")
    pdf = pb.toPandas()
    pdf.attrs = {}

    print(f"[{time.time()-t0:5.1f}s] Got {len(pdf):,} FB genes with PaperBLAST papers")
    if len(pdf) > 0:
        print(pdf[["orgId", "locusId", "sprotAccession", "identity", "n_papers", "pb_desc"]].head(8).to_string(index=False))
        print(f"\nIdentity distribution: median={pdf.identity.median():.1f}%, p25={pdf.identity.quantile(0.25):.1f}%, p75={pdf.identity.quantile(0.75):.1f}%")
        print(f"Papers per gene:       median={pdf.n_papers.median():.0f}, p75={pdf.n_papers.quantile(0.75):.0f}, max={pdf.n_papers.max()}")

    pdf.to_parquet(OUT_PATH, index=False)
    print(f"[{time.time()-t0:5.1f}s] Wrote {OUT_PATH}  ({OUT_PATH.stat().st_size/1e6:.2f} MB)")


if __name__ == "__main__":
    main()

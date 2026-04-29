"""
Extract InterPro annotations for the training-set FB genes.

Pipeline:
  FB (orgId, locusId)
    ↓ via kescience_fitnessbrowser.locusxref (xrefDb='uniprot')
  UniProt accession
    ↓ via kescience_interpro.protein2ipr
  InterPro entry (ipr_id) with start/stop, source_acc (Pfam/etc.)
    ↓ via kescience_interpro.entry
  IPR entry_type, entry_name
    ↓ via kescience_interpro.go_mapping
  GO terms (id + name)

Output:
  data/target_gene_interpro.tsv     — one row per (FB gene, InterPro entry)
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from get_spark_session import get_spark_session  # noqa: E402

OUT_PATH = PROJECT_DATA / "target_gene_interpro.tsv"

# 36 training-set orgIds
ORGS = [
    "ANA3", "BFirm", "Btheta", "Burk376", "Caulo", "Cola", "Cup4G11", "Dino",
    "DvH", "Dyella79", "HerbieS", "Kang", "Keio", "Korea", "Koxy", "MR1",
    "Marino", "Miya", "PS", "PV4", "Pedo557", "Phaeo", "Ponti", "Putida",
    "SB2B", "Smeli", "SynE", "WCS417", "acidovorax_3H11", "azobra", "psRCH2",
    "pseudo13_GW456_L13", "pseudo1_N1B4", "pseudo3_N2E3", "pseudo5_N2C3_1",
    "pseudo6_N2E2",
]


def main() -> None:
    t0 = time.time()
    spark = get_spark_session()
    print(f"[{time.time()-t0:5.1f}s] Spark connected", file=sys.stderr)

    org_list = ",".join([f"'{o}'" for o in ORGS])

    # Single big query: FB → uniprot → InterPro → entry metadata → GO terms aggregate
    q = f"""
        WITH fb_uniprot AS (
          SELECT orgId, locusId, xrefId AS uniprot_acc
          FROM kescience_fitnessbrowser.locusxref
          WHERE xrefDb = 'uniprot'
            AND orgId IN ({org_list})
        ),
        ipr_go_agg AS (
          SELECT ipr_id,
                 array_join(collect_set(concat(go_id, ':', coalesce(go_name, ''))), '; ') AS go_terms
          FROM kescience_interpro.go_mapping
          GROUP BY ipr_id
        )
        SELECT
          fu.orgId,
          fu.locusId,
          fu.uniprot_acc,
          p.ipr_id,
          p.ipr_desc,
          e.entry_type,
          e.entry_name,
          p.source_acc,
          p.start,
          p.stop,
          gm.go_terms
        FROM fb_uniprot fu
        JOIN kescience_interpro.protein2ipr p ON fu.uniprot_acc = p.uniprot_acc
        LEFT JOIN kescience_interpro.entry e ON p.ipr_id = e.ipr_id
        LEFT JOIN ipr_go_agg gm ON p.ipr_id = gm.ipr_id
    """
    print(f"[{time.time()-t0:5.1f}s] Running query (this will be heavy)...", file=sys.stderr)
    df = spark.sql(q).toPandas()
    print(f"[{time.time()-t0:5.1f}s] Got {len(df):,} rows, {df['orgId'].nunique()} orgs, "
          f"{df['locusId'].nunique():,} unique locusIds, "
          f"{df['ipr_id'].nunique():,} unique IPR entries",
          file=sys.stderr)

    df.attrs = {}
    df.to_csv(OUT_PATH, sep="\t", index=False)
    print(f"[{time.time()-t0:5.1f}s] Wrote {OUT_PATH}  ({OUT_PATH.stat().st_size/1e6:.1f} MB)",
          file=sys.stderr)


if __name__ == "__main__":
    main()

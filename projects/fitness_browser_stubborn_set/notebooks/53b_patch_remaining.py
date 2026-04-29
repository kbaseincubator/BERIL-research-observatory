"""
Continuation of 53_patch_missing_33.py — fixes the steps that failed
(wrong column names) and fills the remaining evidence layers for the 33
missing reannotation-set genes.

Already done (per audit after 53 first-pass run):
  ✓ gene_evidence_features.parquet  (33/33)
  ✓ gene_neighborhood.parquet       (33/33)

Still need:
  - swissprot_hits          (21/33 already; query with sprotAccession not hitId)
  - domain_hits             (32/33 already)
  - kegg_hits               (24/33 already; needs two-hop join via keggOrg+keggId)
  - seed_hits               (32/33 already; trivial query)
  - cofit_partners_top10    (0/33; many genes have no cofit at all)
  - gene_secondary_evidence (0/33; derive from above)
  - phenotype_conditions    (0/33; expected — weak-fitness genes)
"""
from __future__ import annotations

import csv
import sys
import time
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from get_spark_session import get_spark_session  # noqa: E402

PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"


def load_keys() -> list[tuple[str, str]]:
    keys = []
    with open("/tmp/missing_33_genes.tsv") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            keys.append((r["orgId"], r["locusId"]))
    return keys


def keys_in_clause(keys, prefix=""):
    parts = []
    p = (prefix + ".") if prefix else ""
    for org, loc in keys:
        org_e = org.replace("'", "''")
        loc_e = loc.replace("'", "''")
        parts.append(f"({p}orgId='{org_e}' AND {p}locusId='{loc_e}')")
    return " OR ".join(parts)


def append_parquet(path: Path, new_df: pd.DataFrame, dedup_cols: list[str]) -> tuple[int, int]:
    if path.exists():
        existing = pd.read_parquet(path)
        before = len(existing)
        if all(c in existing.columns for c in dedup_cols) and len(new_df) > 0:
            keys_set = set(zip(*[new_df[c] for c in dedup_cols]))
            mask = existing.apply(lambda r: tuple(r[c] for c in dedup_cols) in keys_set, axis=1)
            existing = existing[~mask]
        combined = pd.concat([existing, new_df], ignore_index=True) if len(new_df) else existing
    else:
        before = 0
        combined = new_df
    combined.attrs = {}
    combined.to_parquet(path, index=False)
    return (len(combined) - before, len(combined))


def main() -> None:
    keys = load_keys()
    print(f"patching {len(keys)} genes", file=sys.stderr)
    where = keys_in_clause(keys)

    spark = get_spark_session()
    print("Spark connected", file=sys.stderr)

    # === SwissProt ===
    print("[swissprot]...", file=sys.stderr)
    sw_q = f"""
        SELECT b.orgId, b.locusId, b.sprotAccession, b.sprotId,
               CAST(b.identity AS DOUBLE) AS identity,
               s.geneName AS sprot_gene, s.desc AS sprot_desc, s.organism AS sprot_organism
        FROM kescience_fitnessbrowser.besthitswissprot b
        LEFT JOIN kescience_fitnessbrowser.swissprotdesc s ON b.sprotAccession = s.sprotAccession
        WHERE ({keys_in_clause(keys, 'b')})
    """
    sw = spark.sql(sw_q).toPandas()
    print(f"  swissprot rows pulled: {len(sw)}", file=sys.stderr)
    if len(sw):
        a, t = append_parquet(PROJECT_DATA / "swissprot_hits.parquet", sw, ["orgId","locusId"])
        print(f"  +{a}; total {t}", file=sys.stderr)

    # === Domain hits ===
    print("[domain]...", file=sys.stderr)
    dom_q = f"""
        SELECT orgId, locusId, domainDb, domainId, domainName, definition,
               ec, geneSymbol,
               CAST(score AS DOUBLE) AS score,
               CAST(evalue AS DOUBLE) AS evalue
        FROM kescience_fitnessbrowser.genedomain
        WHERE ({where})
    """
    dom = spark.sql(dom_q).toPandas()
    print(f"  domain rows pulled: {len(dom)}", file=sys.stderr)
    if len(dom):
        a, t = append_parquet(PROJECT_DATA / "domain_hits.parquet", dom, ["orgId","locusId","domainName"])
        print(f"  +{a}; total {t}", file=sys.stderr)

    # === KEGG ===
    print("[kegg]...", file=sys.stderr)
    kg_q = f"""
        SELECT b.orgId, b.locusId, km.kgroup,
               kd.desc AS ko_desc,
               ke.ecnum AS ko_ecnum,
               CAST(b.identity AS DOUBLE) AS identity
        FROM kescience_fitnessbrowser.besthitkegg b
        JOIN kescience_fitnessbrowser.keggmember km
          ON b.keggOrg = km.keggOrg AND b.keggId = km.keggId
        LEFT JOIN kescience_fitnessbrowser.kgroupdesc kd ON km.kgroup = kd.kgroup
        LEFT JOIN kescience_fitnessbrowser.kgroupec ke ON km.kgroup = ke.kgroup
        WHERE ({keys_in_clause(keys, 'b')})
    """
    kg = spark.sql(kg_q).toPandas()
    print(f"  kegg rows pulled: {len(kg)}", file=sys.stderr)
    if len(kg):
        a, t = append_parquet(PROJECT_DATA / "kegg_hits.parquet", kg, ["orgId","locusId"])
        print(f"  +{a}; total {t}", file=sys.stderr)

    # === SEED ===
    print("[seed]...", file=sys.stderr)
    sd = spark.sql(f"SELECT orgId, locusId, seed_desc FROM kescience_fitnessbrowser.seedannotation WHERE ({where})").toPandas()
    print(f"  seed rows pulled: {len(sd)}", file=sys.stderr)
    if len(sd):
        a, t = append_parquet(PROJECT_DATA / "seed_hits.parquet", sd, ["orgId","locusId"])
        print(f"  +{a}; total {t}", file=sys.stderr)

    # === Cofit partners (top 10) ===
    print("[cofit_partners]...", file=sys.stderr)
    cf_q = f"""
        WITH ranked AS (
          SELECT c.orgId, c.locusId, c.hitId, CAST(c.cofit AS DOUBLE) AS cofit,
                 g.gene AS partner_gene_symbol, g.desc AS partner_gene_desc,
                 ROW_NUMBER() OVER (PARTITION BY c.orgId, c.locusId
                                    ORDER BY ABS(CAST(c.cofit AS DOUBLE)) DESC) AS partner_rank
          FROM kescience_fitnessbrowser.cofit c
          LEFT JOIN kescience_fitnessbrowser.gene g
            ON c.orgId = g.orgId AND c.hitId = g.locusId
          WHERE ({keys_in_clause(keys, 'c')})
        )
        SELECT orgId, locusId, hitId, cofit, partner_rank, partner_gene_symbol, partner_gene_desc
        FROM ranked WHERE partner_rank <= 10
    """
    cf = spark.sql(cf_q).toPandas()
    print(f"  cofit rows pulled: {len(cf)}", file=sys.stderr)
    if len(cf):
        a, t = append_parquet(PROJECT_DATA / "cofit_partners_top10.parquet", cf, ["orgId","locusId","hitId"])
        print(f"  +{a}; total {t}", file=sys.stderr)
    else:
        print("  (none of these 33 genes have any cofit data)", file=sys.stderr)

    # === Secondary evidence flags — derive from above + check informative_kegg_ec ===
    print("[secondary_evidence]...", file=sys.stderr)
    sec = pd.DataFrame(keys, columns=["orgId","locusId"])
    if len(dom):
        dom_inf = dom[
            ((dom["ec"].notna()) & (dom["ec"] != "") & (dom["ec"] != "-")) |
            (~dom["definition"].fillna("").str.lower().str.contains("domain of unknown function|uncharacterized", regex=True))
            & (~dom["domainName"].fillna("").str.lower().str.contains("^duf|^upf", regex=True))
            & (dom["definition"].fillna("") != "")
        ]
        dom_keys = set(zip(dom_inf["orgId"], dom_inf["locusId"]))
    else:
        dom_keys = set()

    if len(kg):
        kg_ko = kg[kg["ko_desc"].notna() & (kg["ko_desc"] != "") &
                   ~kg["ko_desc"].fillna("").str.lower().str.contains("uncharacterized|hypothetical|unknown function", regex=True)]
        kg_ec = kg[kg["ko_ecnum"].notna() & (kg["ko_ecnum"] != "")]
        kg_ko_keys = set(zip(kg_ko["orgId"], kg_ko["locusId"]))
        kg_ec_keys = set(zip(kg_ec["orgId"], kg_ec["locusId"]))
    else:
        kg_ko_keys = set()
        kg_ec_keys = set()

    if len(sd):
        sd_inf = sd[sd["seed_desc"].notna() & ~sd["seed_desc"].fillna("").str.lower().str.contains("hypothetical")]
        sd_keys = set(zip(sd_inf["orgId"], sd_inf["locusId"]))
    else:
        sd_keys = set()

    sec["informative_domain"] = sec.apply(lambda r: int((r["orgId"], r["locusId"]) in dom_keys), axis=1)
    sec["informative_kegg_ko"] = sec.apply(lambda r: int((r["orgId"], r["locusId"]) in kg_ko_keys), axis=1)
    sec["informative_kegg_ec"] = sec.apply(lambda r: int((r["orgId"], r["locusId"]) in kg_ec_keys), axis=1)
    sec["informative_seed"] = sec.apply(lambda r: int((r["orgId"], r["locusId"]) in sd_keys), axis=1)
    sec["conserved_spec_phenotype"] = 0
    sec["conserved_cofit"] = 0
    a, t = append_parquet(PROJECT_DATA / "gene_secondary_evidence.parquet", sec, ["orgId","locusId"])
    print(f"  +{a}; total {t}", file=sys.stderr)

    print("\nAll patches written. Now rebuild dossier_md for these 33 genes.", file=sys.stderr)


if __name__ == "__main__":
    main()

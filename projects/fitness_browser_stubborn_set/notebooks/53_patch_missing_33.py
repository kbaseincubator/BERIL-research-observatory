"""
Patch the 33 reannotation-set genes that are missing from
gene_evidence_features.parquet (and downstream evidence parquets) by
querying BERDL directly for just those (orgId, locusId) pairs and
appending the rows to each parquet.

Most of these genes are likely missing because they have no rows in
`genefitness` (the inner anchor of 00_extract_gene_features.py). They may
still have data in the gene table, neighborhood, sequence-based hit
tables, etc. — we want all of that.

Required: BERDL Spark Connect available (SSH tunnels + pproxy + JupyterHub
session active).

After patching, run notebook 54 (or re-run the dossier build for
these 33 genes) and update human_validated.jsonl + llm_vs_human_disagreements.jsonl.
"""
from __future__ import annotations

import csv
import sys
import time
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from get_spark_session import get_spark_session  # type: ignore  # noqa: E402

PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"
KEYS_FILE = Path("/tmp/missing_33_genes.tsv")


def load_keys() -> list[tuple[str, str]]:
    if KEYS_FILE.exists():
        out = []
        with open(KEYS_FILE) as fh:
            for r in csv.DictReader(fh, delimiter="\t"):
                out.append((r["orgId"], r["locusId"]))
        return out
    # Recompute from training_set
    import json
    feat = pd.read_parquet(PROJECT_DATA / "gene_evidence_features.parquet")
    feat_keys = set(zip(feat["orgId"], feat["locusId"]))
    out = []
    with open(PROJECT_DATA / "training_set" / "human_validated.jsonl") as fh:
        for line in fh:
            r = json.loads(line)
            k = (r["orgId"], r["locusId"])
            if k not in feat_keys:
                out.append(k)
    return out


def keys_in_clause(keys: list[tuple[str, str]]) -> str:
    """Build a SQL `(orgId, locusId) IN (('o1','l1'), ...)` clause-style filter
    using OR (Spark Connect doesn't always like tuple IN)."""
    parts = []
    for org, loc in keys:
        # Escape single quotes in case (rare)
        org_e = org.replace("'", "''")
        loc_e = loc.replace("'", "''")
        parts.append(f"(orgId='{org_e}' AND locusId='{loc_e}')")
    return " OR ".join(parts)


def append_parquet(path: Path, new_df: pd.DataFrame, dedup_cols: list[str]) -> tuple[int, int]:
    """Append new_df to existing parquet, dedup by dedup_cols. Returns (added, total)."""
    if path.exists():
        existing = pd.read_parquet(path)
        before = len(existing)
        # Drop existing rows with these keys (so the new ones replace them, idempotent)
        if all(c in existing.columns for c in dedup_cols):
            keys_set = set(zip(*[new_df[c] for c in dedup_cols]))
            mask = existing.apply(lambda r: tuple(r[c] for c in dedup_cols) in keys_set, axis=1)
            existing = existing[~mask]
        combined = pd.concat([existing, new_df], ignore_index=True)
    else:
        before = 0
        combined = new_df
    combined.attrs = {}
    combined.to_parquet(path, index=False)
    return (len(combined) - before, len(combined))


def main() -> None:
    keys = load_keys()
    print(f"Patching {len(keys)} missing genes", file=sys.stderr)
    where = keys_in_clause(keys)

    t0 = time.time()
    spark = get_spark_session()
    print(f"[{time.time()-t0:5.1f}s] Spark connected", file=sys.stderr)

    # 1. gene_evidence_features.parquet — same logic as 00, but anchored on gene table
    print("[1/8] gene_evidence_features...", file=sys.stderr)
    gf = spark.sql(f"""
        SELECT orgId, locusId,
          MAX(ABS(CAST(fit AS DOUBLE))) AS max_abs_fit,
          MAX(ABS(CAST(t   AS DOUBLE))) AS max_abs_t,
          SUM(CASE WHEN ABS(CAST(fit AS DOUBLE))>=2.0 AND ABS(CAST(t AS DOUBLE))>=5.0 THEN 1 ELSE 0 END) AS n_strong_experiments,
          SUM(CASE WHEN ABS(CAST(fit AS DOUBLE))>=1.0 AND ABS(CAST(t AS DOUBLE))>=5.0 THEN 1 ELSE 0 END) AS n_moderate_experiments
        FROM kescience_fitnessbrowser.genefitness WHERE ({where}) GROUP BY orgId, locusId
    """).toPandas()
    sp = spark.sql(f"SELECT DISTINCT orgId, locusId, 1 AS in_specificphenotype FROM kescience_fitnessbrowser.specificphenotype WHERE ({where})").toPandas()
    cf = spark.sql(f"SELECT orgId, locusId, MAX(CAST(cofit AS DOUBLE)) AS max_cofit FROM kescience_fitnessbrowser.cofit WHERE ({where}) GROUP BY orgId, locusId").toPandas()
    gd = spark.sql(f"SELECT orgId, locusId, gene AS gene_symbol, desc AS gene_desc FROM kescience_fitnessbrowser.gene WHERE ({where})").toPandas()
    base = pd.DataFrame(keys, columns=["orgId", "locusId"])
    feat = (base.merge(gd, on=["orgId","locusId"], how="left")
                .merge(gf, on=["orgId","locusId"], how="left")
                .merge(sp, on=["orgId","locusId"], how="left")
                .merge(cf, on=["orgId","locusId"], how="left"))
    feat["is_reannotated"] = 1
    feat = feat.fillna({"max_abs_fit":0.0, "max_abs_t":0.0, "n_strong_experiments":0,
                        "n_moderate_experiments":0, "in_specificphenotype":0, "max_cofit":0.0,
                        "gene_symbol":"", "gene_desc":""})
    a, t = append_parquet(PROJECT_DATA / "gene_evidence_features.parquet", feat, ["orgId","locusId"])
    print(f"  +{a} rows; total {t}", file=sys.stderr)

    # 2. ranked_genes.parquet — same fields, just adds rank. Mark new rows with rank=NaN.
    if (PROJECT_DATA / "ranked_genes.parquet").exists():
        ranked_new = feat.copy()
        ranked_new["rank"] = pd.NA
        ranked_new["score"] = 0.0
        ranked_new["chunk_index"] = 0
        ranked_new["annotation_category"] = ""
        a, t = append_parquet(PROJECT_DATA / "ranked_genes.parquet", ranked_new, ["orgId","locusId"])
        print(f"[2/8] ranked_genes  +{a}; total {t}", file=sys.stderr)

    # 3. phenotype_conditions.parquet — strict thresholds may exclude these
    print("[3/8] phenotype_conditions (Price strong/specific only)...", file=sys.stderr)
    ph = spark.sql(f"""
        SELECT gf.orgId, gf.locusId, gf.expName,
               CASE WHEN ABS(CAST(gf.fit AS DOUBLE))>=2.0 AND ABS(CAST(gf.t AS DOUBLE))>=5.0 THEN 'strong'
                    WHEN ABS(CAST(gf.fit AS DOUBLE))>=1.0 AND ABS(CAST(gf.t AS DOUBLE))>=5.0 THEN 'specific' END AS record_type,
               CAST(gf.fit AS DOUBLE) AS fit, CAST(gf.t AS DOUBLE) AS t,
               e.expGroup, e.expDesc, e.expDescLong, e.condition_1, e.units_1, e.concentration_1,
               e.condition_2, e.condition_3, e.condition_4, e.media, e.temperature, e.pH, e.aerobic
        FROM kescience_fitnessbrowser.genefitness gf
        LEFT JOIN kescience_fitnessbrowser.experiment e
          ON gf.orgId = e.orgId AND gf.expName = e.expName
        WHERE ({where.replace('orgId','gf.orgId').replace('locusId','gf.locusId')})
          AND ABS(CAST(gf.fit AS DOUBLE))>=1.0 AND ABS(CAST(gf.t AS DOUBLE))>=5.0
    """).toPandas()
    if len(ph) > 0:
        a, t = append_parquet(PROJECT_DATA / "phenotype_conditions.parquet", ph, ["orgId","locusId","expName"])
        print(f"  +{a} rows; total {t}", file=sys.stderr)
    else:
        print(f"  (no rows passed Price thresholds — these genes have weak fitness)", file=sys.stderr)

    # 4. cofit_partners_top10.parquet
    print("[4/8] cofit_partners_top10...", file=sys.stderr)
    cf_top = spark.sql(f"""
        WITH ranked AS (
          SELECT c.orgId, c.locusId, c.hitId, CAST(c.cofit AS DOUBLE) AS cofit,
                 g.gene AS partner_gene_symbol, g.desc AS partner_gene_desc,
                 ROW_NUMBER() OVER (PARTITION BY c.orgId, c.locusId
                                    ORDER BY ABS(CAST(c.cofit AS DOUBLE)) DESC) AS rn
          FROM kescience_fitnessbrowser.cofit c
          LEFT JOIN kescience_fitnessbrowser.gene g
            ON c.orgId = g.orgId AND c.hitId = g.locusId
          WHERE ({where.replace('orgId','c.orgId').replace('locusId','c.locusId')})
        )
        SELECT orgId, locusId, hitId, cofit, partner_gene_symbol, partner_gene_desc
        FROM ranked WHERE rn <= 10
    """).toPandas()
    if len(cf_top) > 0:
        a, t = append_parquet(PROJECT_DATA / "cofit_partners_top10.parquet", cf_top, ["orgId","locusId","hitId"])
        print(f"  +{a} rows; total {t}", file=sys.stderr)

    # 5. gene_neighborhood.parquet (±5 positions on same scaffold)
    print("[5/8] gene_neighborhood...", file=sys.stderr)
    nb = spark.sql(f"""
        WITH self AS (
          SELECT orgId, locusId, scaffoldId,
                 CAST(begin AS BIGINT) AS begin, strand
          FROM kescience_fitnessbrowser.gene WHERE ({where})
        ),
        same_scaff AS (
          SELECT s.orgId AS center_org, s.locusId AS center_loc, s.begin AS center_begin,
                 g.locusId AS neighbor_loc, g.gene AS neighbor_gene_symbol,
                 g.desc AS neighbor_gene_desc, g.strand AS neighbor_strand,
                 CAST(g.begin AS BIGINT) AS neighbor_begin,
                 ROW_NUMBER() OVER (PARTITION BY s.orgId, s.locusId
                                    ORDER BY ABS(CAST(g.begin AS BIGINT) - s.begin)) AS rn
          FROM self s
          JOIN kescience_fitnessbrowser.gene g
            ON s.orgId = g.orgId AND s.scaffoldId = g.scaffoldId
        )
        SELECT center_org AS orgId, center_loc AS locusId, neighbor_loc, neighbor_gene_symbol,
               neighbor_gene_desc, neighbor_strand,
               CAST(neighbor_begin - center_begin AS INT) AS offset_bp,
               CAST(rn - 1 AS INT) AS offset
        FROM same_scaff WHERE rn <= 11
    """).toPandas()
    if len(nb) > 0:
        # offset ranges -5..+5 by position along scaffold; we keep all 11 (self + ±5)
        # Map row position to relative offset based on order in this gene's window
        # For simplicity, just store as offset (we'll compute relative offset in dossier)
        # Match existing parquet schema if it exists
        existing_cols = pd.read_parquet(PROJECT_DATA / "gene_neighborhood.parquet").columns.tolist() \
            if (PROJECT_DATA / "gene_neighborhood.parquet").exists() else nb.columns.tolist()
        nb = nb[[c for c in existing_cols if c in nb.columns]]
        a, t = append_parquet(PROJECT_DATA / "gene_neighborhood.parquet", nb, ["orgId","locusId","neighbor_loc"])
        print(f"  +{a} rows; total {t}", file=sys.stderr)

    # 6. swissprot_hits.parquet
    print("[6/8] swissprot_hits...", file=sys.stderr)
    sw = spark.sql(f"""
        SELECT b.orgId, b.locusId, b.hitId AS sprotAccession, CAST(b.identity AS DOUBLE) AS identity,
               s.desc AS sprot_desc, s.organism AS sprot_organism
        FROM kescience_fitnessbrowser.besthitswissprot b
        LEFT JOIN kescience_fitnessbrowser.swissprotdesc s ON b.hitId = s.sprotAccession
        WHERE ({where.replace('orgId','b.orgId').replace('locusId','b.locusId')})
    """).toPandas()
    if len(sw) > 0:
        existing_cols = pd.read_parquet(PROJECT_DATA / "swissprot_hits.parquet").columns.tolist() \
            if (PROJECT_DATA / "swissprot_hits.parquet").exists() else sw.columns.tolist()
        sw = sw.reindex(columns=existing_cols, fill_value=None)
        a, t = append_parquet(PROJECT_DATA / "swissprot_hits.parquet", sw, ["orgId","locusId"])
        print(f"  +{a} rows; total {t}", file=sys.stderr)

    # 7. domain_hits.parquet
    print("[7/8] domain_hits...", file=sys.stderr)
    dom = spark.sql(f"""
        SELECT orgId, locusId, domainDb, domainName, definition, ec, score
        FROM kescience_fitnessbrowser.genedomain
        WHERE ({where})
    """).toPandas()
    if len(dom) > 0:
        existing_cols = pd.read_parquet(PROJECT_DATA / "domain_hits.parquet").columns.tolist() \
            if (PROJECT_DATA / "domain_hits.parquet").exists() else dom.columns.tolist()
        dom = dom.reindex(columns=existing_cols, fill_value=None)
        a, t = append_parquet(PROJECT_DATA / "domain_hits.parquet", dom, ["orgId","locusId","domainName"])
        print(f"  +{a} rows; total {t}", file=sys.stderr)

    # 8. kegg_hits + seed_hits + secondary_evidence — bundle
    print("[8/8] kegg_hits + seed_hits + secondary_evidence...", file=sys.stderr)
    kg = spark.sql(f"""
        SELECT bk.orgId, bk.locusId, km.kgroup, kd.desc AS kegg_desc, ke.ecnum AS kegg_ec,
               CAST(bk.identity AS DOUBLE) AS kegg_identity
        FROM kescience_fitnessbrowser.besthitkegg bk
        JOIN kescience_fitnessbrowser.keggmember km ON bk.hitId = km.geneId
        LEFT JOIN kescience_fitnessbrowser.kgroupdesc kd ON km.kgroup = kd.kgroup
        LEFT JOIN kescience_fitnessbrowser.kgroupec ke ON km.kgroup = ke.kgroup
        WHERE ({where.replace('orgId','bk.orgId').replace('locusId','bk.locusId')})
    """).toPandas()
    if len(kg) > 0:
        existing_cols = pd.read_parquet(PROJECT_DATA / "kegg_hits.parquet").columns.tolist() \
            if (PROJECT_DATA / "kegg_hits.parquet").exists() else kg.columns.tolist()
        kg = kg.reindex(columns=existing_cols, fill_value=None)
        a, t = append_parquet(PROJECT_DATA / "kegg_hits.parquet", kg, ["orgId","locusId"])
        print(f"  kegg +{a}; total {t}", file=sys.stderr)

    sd = spark.sql(f"""
        SELECT orgId, locusId, seed_desc
        FROM kescience_fitnessbrowser.seedannotation
        WHERE ({where})
    """).toPandas()
    if len(sd) > 0:
        existing_cols = pd.read_parquet(PROJECT_DATA / "seed_hits.parquet").columns.tolist() \
            if (PROJECT_DATA / "seed_hits.parquet").exists() else sd.columns.tolist()
        sd = sd.reindex(columns=existing_cols, fill_value=None)
        a, t = append_parquet(PROJECT_DATA / "seed_hits.parquet", sd, ["orgId","locusId"])
        print(f"  seed +{a}; total {t}", file=sys.stderr)

    # Secondary evidence flags — derive from what we just collected
    sec = pd.DataFrame(keys, columns=["orgId","locusId"])
    sec["informative_domain"] = sec.apply(
        lambda r: int(((dom["orgId"]==r["orgId"]) & (dom["locusId"]==r["locusId"]) & (dom["ec"].notna() | dom["definition"].fillna("").str.lower().apply(lambda d: "domain of unknown function" not in d if d else True))).any()) if len(dom) else 0, axis=1)
    sec["informative_kegg_ko"] = sec.apply(
        lambda r: int(((kg["orgId"]==r["orgId"]) & (kg["locusId"]==r["locusId"]) & (~kg["kegg_desc"].fillna("").str.lower().str.contains("uncharacterized"))).any()) if len(kg) else 0, axis=1)
    sec["informative_kegg_ec"] = sec.apply(
        lambda r: int(((kg["orgId"]==r["orgId"]) & (kg["locusId"]==r["locusId"]) & kg["kegg_ec"].notna()).any()) if len(kg) else 0, axis=1)
    sec["informative_seed"] = sec.apply(
        lambda r: int(((sd["orgId"]==r["orgId"]) & (sd["locusId"]==r["locusId"]) & (~sd["seed_desc"].fillna("").str.lower().str.contains("hypothetical"))).any()) if len(sd) else 0, axis=1)
    sec["conserved_spec_phenotype"] = 0  # need specog/ortholog joins; default 0
    sec["conserved_cofit"] = 0  # ditto
    if (PROJECT_DATA / "gene_secondary_evidence.parquet").exists():
        existing_cols = pd.read_parquet(PROJECT_DATA / "gene_secondary_evidence.parquet").columns.tolist()
        sec = sec.reindex(columns=existing_cols, fill_value=0)
    a, t = append_parquet(PROJECT_DATA / "gene_secondary_evidence.parquet", sec, ["orgId","locusId"])
    print(f"  secondary_evidence +{a}; total {t}", file=sys.stderr)

    print(f"\n[{time.time()-t0:5.1f}s] All patches written", file=sys.stderr)


if __name__ == "__main__":
    main()

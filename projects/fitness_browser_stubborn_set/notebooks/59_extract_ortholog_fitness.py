"""
Build target_gene_ortholog_fitness.tsv: for each target gene in the
training set, every FB BBH ortholog with that ortholog's own fitness
profile + organism-level taxonomic distance.

Why this exists
---------------
The dossier currently only carries two binary "conservation" bits
(`conserved_cofit`, `conserved_specific_phenotype`) derived from the
ortholog graph. The actual fitness profile of an ortholog --- which
conditions it was strong in, how strong --- never reaches the agent.
For a target gene with weak signal, the strongest reasoning move is
"but its ortholog in WCS417 shows phenotype on xylose"; that
information is in BERDL, just not surfaced.

Two distance signals are exposed so the agent can weight orthologs:
  - bbh_ratio: BBH score ratio from ortholog.ratio (gene-level)
  - shared_taxonomic_ranks: 0..7 ranks shared in GTDB lineage between
    the target organism and the ortholog organism (organism-level)

Inputs
------
  kescience_fitnessbrowser.ortholog        BBH pairs (symmetric)
  kescience_fitnessbrowser.gene            descriptions
  kescience_fitnessbrowser.genefitness     27M-row fitness × experiment
  kescience_fitnessbrowser.specificphenotype  Price-thresholded specific
  data/fb_pangenome_link.tsv               FB orgId/locusId -> gtdb genome
  kbase_ke_pangenome.gtdb_taxonomy_r214v1  full GTDB lineage by genome_id

Outputs
-------
  data/training_set/fb_organism_gtdb_lineage.tsv
    36 rows; columns: orgId, genome_id, domain, phylum, class, order,
    family, genus, species

  data/training_set/target_gene_ortholog_fitness.tsv
    one row per (target_orgId, target_locusId, ortholog_orgId,
                 ortholog_locusId)
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"
TS = PROJECT_DATA / "training_set"
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from get_spark_session import get_spark_session  # noqa: E402

LINK_TSV = PROJECT_DATA / "fb_pangenome_link.tsv"
LINEAGE_OUT = TS / "fb_organism_gtdb_lineage.tsv"
ORTHO_OUT = TS / "target_gene_ortholog_fitness.tsv"

RANKS = ["domain", "phylum", "class", "order", "family", "genus", "species"]


def load_training_keys() -> pd.DataFrame:
    keys: set[tuple[str, str]] = set()
    for fn in ("negatives.jsonl", "positives.jsonl", "human_validated.jsonl"):
        p = TS / fn
        with open(p) as fh:
            for line in fh:
                r = json.loads(line)
                keys.add((r["orgId"], r["locusId"]))
    df = pd.DataFrame(list(keys), columns=["orgId", "locusId"])
    print(f"training keys: {len(df):,} ({df['orgId'].nunique()} orgs)", file=sys.stderr)
    return df


def build_orgid_lineage(spark, all_fb_orgs: list[str]) -> pd.DataFrame:
    """One row per FB orgId with the best-available lineage.

    Strategy:
      1. From fb_pangenome_link.tsv, take majority gtdb_species_clade_id per
         orgId, parse out the genome accession (after `--`).
      2. Look up full lineage in kbase_ke_pangenome.gtdb_taxonomy_r214v1.
      3. For orgs without a link entry (e.g. Cola/Kang/SB2B), fall back to
         kescience_fitnessbrowser.organism (always has genus + species).
         FB-fallback rows have empty domain..family but populated
         genus/species so cross-org genus matches still count.

    GTDB strings carry their `g__`/`s__` prefixes; FB-fallback rows are
    prefixed identically so shared-rank counting works across both.
    """
    link = pd.read_csv(LINK_TSV, sep="\t",
                       usecols=["orgId", "gtdb_species_clade_id"],
                       dtype=str, keep_default_na=False)
    link = link[link["gtdb_species_clade_id"].astype(bool)]
    counts = (link.groupby(["orgId", "gtdb_species_clade_id"]).size()
                  .reset_index(name="n")
                  .sort_values(["orgId", "n"], ascending=[True, False])
                  .drop_duplicates("orgId", keep="first"))
    counts["genome_id"] = counts["gtdb_species_clade_id"].str.split("--", n=1).str[1]
    counts = counts[["orgId", "genome_id"]]

    genome_ids = sorted(counts["genome_id"].dropna().unique())
    in_list = ",".join(f"'{g}'" for g in genome_ids)
    tax = spark.sql(f"""
        SELECT genome_id, domain, phylum, class, `order` AS order_, family,
               genus, species
        FROM kbase_ke_pangenome.gtdb_taxonomy_r214v1
        WHERE genome_id IN ({in_list})
    """).toPandas().rename(columns={"order_": "order"})

    primary = counts.merge(tax, on="genome_id", how="left")

    # Find orgs needing fallback
    have = set(primary["orgId"].dropna()) & set(all_fb_orgs)
    missing = [o for o in all_fb_orgs if o not in have or
               primary.loc[primary["orgId"] == o, "domain"].isna().all()]
    if missing:
        org_in = ",".join(f"'{o}'" for o in missing)
        fb_org = spark.sql(f"""
            SELECT orgId, division, genus, species
            FROM kescience_fitnessbrowser.organism
            WHERE orgId IN ({org_in})
        """).toPandas()
        # FB.division is mixed (sometimes phylum-level, sometimes class-level).
        # Don't try to slot it; just keep genus + species (with prefixes).
        fb_org["genome_id"] = ""
        fb_org["domain"]    = "d__Bacteria"  # all FB orgs are bacterial/archaeal — FB doesn't carry this; assume bacteria
        for r in ["phylum", "class", "order", "family"]:
            fb_org[r] = ""
        fb_org["genus"]   = fb_org["genus"].apply(lambda v: f"g__{v}" if v else "")
        fb_org["species"] = fb_org.apply(
            lambda r: f"s__{r['genus'][3:]} {r['species']}" if r["genus"] and r["species"] else "",
            axis=1,
        )
        fb_org = fb_org[["orgId", "genome_id"] + RANKS]
        primary = pd.concat([primary[~primary["orgId"].isin(missing)], fb_org],
                            ignore_index=True)

    primary = (primary[primary["orgId"].isin(all_fb_orgs)]
                  .drop_duplicates("orgId", keep="first")
                  .sort_values("orgId").reset_index(drop=True))
    return primary[["orgId", "genome_id"] + RANKS]


def shared_ranks(a: pd.Series, b: pd.Series) -> pd.Series:
    """Count of consecutive matching GTDB ranks from domain down."""
    n = pd.Series(0, index=a.index)
    matched = pd.Series(True, index=a.index)
    for r in RANKS:
        eq = matched & (a[r].fillna("") == b[r].fillna("")) & a[r].fillna("").astype(bool)
        n += eq.astype(int)
        matched = eq
    return n


def main() -> None:
    t0 = time.time()
    keys = load_training_keys()
    training_orgs = sorted(keys["orgId"].unique())

    spark = get_spark_session()
    print(f"[{time.time()-t0:5.1f}s] Spark connected", file=sys.stderr)

    # All orgIds present in the FB ortholog table (48 orgs)
    fb_orgs = [r["orgId1"] for r in spark.sql(
        "SELECT DISTINCT orgId1 FROM kescience_fitnessbrowser.ortholog"
    ).collect()]
    print(f"  FB orgs in ortholog table: {len(fb_orgs)}", file=sys.stderr)

    # ---- 1. orgId -> lineage (GTDB primary, FB.organism fallback) ----
    lineage = build_orgid_lineage(spark, fb_orgs)
    # Output: only training orgs in the per-organism file, but keep the full
    # 48-org lineage in memory so ortholog-side joins always have a value.
    lineage_train = lineage[lineage["orgId"].isin(training_orgs)].reset_index(drop=True)
    lineage_train.to_csv(LINEAGE_OUT, sep="\t", index=False)
    n_full = (lineage_train["domain"].astype(bool) & lineage_train["phylum"].astype(bool)
              & lineage_train["class"].astype(bool) & lineage_train["family"].astype(bool)).sum()
    print(f"[{time.time()-t0:5.1f}s] wrote {LINEAGE_OUT.name} "
          f"({len(lineage_train)} orgs, {n_full} with full GTDB lineage, "
          f"{len(lineage_train)-n_full} with FB-fallback genus/species only)",
          file=sys.stderr)

    # ---- 2. Pull all orthologs where the target side is a training org ----
    org_in = ",".join(f"'{o}'" for o in training_orgs)
    ortho_all = spark.sql(f"""
        SELECT orgId1 AS target_orgId, locusId1 AS target_locusId,
               orgId2 AS ortholog_orgId, locusId2 AS ortholog_locusId,
               try_cast(ratio AS DOUBLE) AS bbh_ratio
        FROM kescience_fitnessbrowser.ortholog
        WHERE orgId1 IN ({org_in})
    """).toPandas()
    print(f"[{time.time()-t0:5.1f}s] all orthologs from training orgs: {len(ortho_all):,}",
          file=sys.stderr)

    # Filter to (orgId, locusId) pairs in the training set
    train_set = set(zip(keys["orgId"], keys["locusId"]))
    mask = list(zip(ortho_all["target_orgId"], ortho_all["target_locusId"]))
    ortho = ortho_all[[k in train_set for k in mask]].reset_index(drop=True)
    print(f"  filtered to training-key target side: {len(ortho):,} pairs", file=sys.stderr)

    if len(ortho) == 0:
        print("no orthologs found, exiting", file=sys.stderr)
        return

    ortho_keys = (ortho[["ortholog_orgId", "ortholog_locusId"]]
                  .drop_duplicates())
    ortho_orgs = sorted(ortho_keys["ortholog_orgId"].unique())
    ortho_set  = set(zip(ortho_keys["ortholog_orgId"], ortho_keys["ortholog_locusId"]))
    print(f"  unique ortholog-side genes: {len(ortho_keys):,} across {len(ortho_orgs)} orgs",
          file=sys.stderr)

    # All ortholog-side aggregations are computed globally for the orgs that
    # contain ortholog-side keys (typically all 48 FB orgs), then filtered
    # to ortho_set in pandas.  Volumes are bounded: ~137k FB genes total.
    org_in_o = ",".join(f"'{o}'" for o in ortho_orgs)

    def _filter_to_ortho(df: pd.DataFrame) -> pd.DataFrame:
        keys = list(zip(df["orgId"], df["locusId"]))
        return df[[k in ortho_set for k in keys]].reset_index(drop=True)

    # ---- 3. Ortholog gene descriptions ----
    desc = spark.sql(f"""
        SELECT orgId, locusId, desc AS ortholog_gene_desc,
               gene AS ortholog_symbol
        FROM kescience_fitnessbrowser.gene
        WHERE orgId IN ({org_in_o})
    """).toPandas()
    desc = _filter_to_ortho(desc)
    print(f"[{time.time()-t0:5.1f}s] ortholog gene descriptions: {len(desc):,}",
          file=sys.stderr)

    # ---- 4. Per-ortholog fitness summary ----
    fit_sum = spark.sql(f"""
        SELECT orgId, locusId,
               MAX(ABS(try_cast(fit AS DOUBLE))) AS ortholog_max_abs_fit,
               MAX(ABS(try_cast(t   AS DOUBLE))) AS ortholog_max_abs_t,
               SUM(CASE WHEN ABS(try_cast(fit AS DOUBLE)) >= 1
                         AND ABS(try_cast(t   AS DOUBLE)) >= 4 THEN 1 ELSE 0 END)
                 AS ortholog_n_strong
        FROM kescience_fitnessbrowser.genefitness
        WHERE orgId IN ({org_in_o})
        GROUP BY orgId, locusId
    """).toPandas()
    fit_sum = _filter_to_ortho(fit_sum)
    print(f"[{time.time()-t0:5.1f}s] ortholog fitness summary: {len(fit_sum):,}",
          file=sys.stderr)

    # ---- 5. Top-3 conditions per ortholog by |fit| ----
    top_cond = spark.sql(f"""
        WITH ranked AS (
          SELECT f.orgId, f.locusId,
                 try_cast(f.fit AS DOUBLE) AS fit_signed,
                 try_cast(f.t   AS DOUBLE) AS t_val,
                 e.expDescLong AS condition,
                 ROW_NUMBER() OVER (
                   PARTITION BY f.orgId, f.locusId
                   ORDER BY ABS(try_cast(f.fit AS DOUBLE)) DESC NULLS LAST
                 ) AS rn
          FROM kescience_fitnessbrowser.genefitness f
          JOIN kescience_fitnessbrowser.experiment e
            ON f.orgId = e.orgId AND f.expName = e.expName
          WHERE f.orgId IN ({org_in_o})
        )
        SELECT orgId, locusId,
               array_join(
                 collect_list(
                   concat('fit=', round(fit_signed,2), ' t=', round(t_val,1),
                          ' cond=', condition)
                 ),
                 ' | '
               ) AS ortholog_top_conditions
        FROM ranked
        WHERE rn <= 3
        GROUP BY orgId, locusId
    """).toPandas()
    top_cond = _filter_to_ortho(top_cond)
    print(f"[{time.time()-t0:5.1f}s] ortholog top conditions: {len(top_cond):,}",
          file=sys.stderr)

    # ---- 6. Specific phenotype counts per ortholog ----
    spec = spark.sql(f"""
        SELECT orgId, locusId, COUNT(*) AS ortholog_n_specific_phenotype
        FROM kescience_fitnessbrowser.specificphenotype
        WHERE orgId IN ({org_in_o})
        GROUP BY orgId, locusId
    """).toPandas()
    spec = _filter_to_ortho(spec)
    print(f"[{time.time()-t0:5.1f}s] ortholog specific-phenotype counts: {len(spec):,}",
          file=sys.stderr)

    # ---- 8. Assemble: ortho ⨝ desc ⨝ fit_sum ⨝ top_cond ⨝ spec ----
    df = ortho.merge(
            desc.rename(columns={"orgId": "ortholog_orgId", "locusId": "ortholog_locusId"}),
            on=["ortholog_orgId", "ortholog_locusId"], how="left"
        ).merge(
            fit_sum.rename(columns={"orgId": "ortholog_orgId", "locusId": "ortholog_locusId"}),
            on=["ortholog_orgId", "ortholog_locusId"], how="left"
        ).merge(
            top_cond.rename(columns={"orgId": "ortholog_orgId", "locusId": "ortholog_locusId"}),
            on=["ortholog_orgId", "ortholog_locusId"], how="left"
        ).merge(
            spec.rename(columns={"orgId": "ortholog_orgId", "locusId": "ortholog_locusId"}),
            on=["ortholog_orgId", "ortholog_locusId"], how="left"
        )

    # ---- 9. Add organism-level taxonomic distance (shared rank count) ----
    # Use the full 48-org lineage so the ortholog side always has a row
    lin_target = lineage.rename(columns={c: f"target_{c}" for c in RANKS} | {"orgId": "target_orgId"})
    lin_ortho  = lineage.rename(columns={c: f"ortholog_{c}" for c in RANKS} | {"orgId": "ortholog_orgId"})
    df = df.merge(lin_target[["target_orgId"] + [f"target_{r}" for r in RANKS]],
                  on="target_orgId", how="left")
    df = df.merge(lin_ortho[["ortholog_orgId"] + [f"ortholog_{r}" for r in RANKS]],
                  on="ortholog_orgId", how="left")

    a = df[[f"target_{r}"   for r in RANKS]].rename(columns=lambda c: c.replace("target_",""))
    b = df[[f"ortholog_{r}" for r in RANKS]].rename(columns=lambda c: c.replace("ortholog_",""))
    df["shared_taxonomic_ranks"] = shared_ranks(a, b)

    # Tidy: keep just the lineage strings as compact joined columns rather than 14 columns
    df["target_gtdb_lineage"]   = df[[f"target_{r}"   for r in RANKS]].fillna("").agg(";".join, axis=1)
    df["ortholog_gtdb_lineage"] = df[[f"ortholog_{r}" for r in RANKS]].fillna("").agg(";".join, axis=1)
    df = df.drop(columns=[f"target_{r}"   for r in RANKS] +
                          [f"ortholog_{r}" for r in RANKS])

    # ---- 10. Order columns and emit ----
    cols = [
        "target_orgId", "target_locusId",
        "ortholog_orgId", "ortholog_locusId",
        "bbh_ratio", "shared_taxonomic_ranks",
        "ortholog_symbol", "ortholog_gene_desc",
        "ortholog_max_abs_fit", "ortholog_max_abs_t", "ortholog_n_strong",
        "ortholog_n_specific_phenotype",
        "ortholog_top_conditions",
        "target_gtdb_lineage", "ortholog_gtdb_lineage",
    ]
    df = df[cols].sort_values(
        ["target_orgId", "target_locusId", "bbh_ratio"],
        ascending=[True, True, False],
    )
    df.to_csv(ORTHO_OUT, sep="\t", index=False)
    size_mb = ORTHO_OUT.stat().st_size / 1e6
    print(f"\n[{time.time()-t0:5.1f}s] wrote {ORTHO_OUT.name}  "
          f"({size_mb:.1f} MB, {len(df):,} rows)", file=sys.stderr)

    # ---- summary stats ----
    n_targets = df[["target_orgId", "target_locusId"]].drop_duplicates().shape[0]
    print(f"  target genes with >= 1 ortholog: {n_targets:,}", file=sys.stderr)
    print(f"  ortholog rows with fitness data : "
          f"{df['ortholog_max_abs_fit'].notna().sum():,}", file=sys.stderr)
    print(f"  shared-rank distribution:", file=sys.stderr)
    print(df["shared_taxonomic_ranks"].value_counts().sort_index().to_string(),
          file=sys.stderr)
    print(f"  bbh_ratio quartiles:", file=sys.stderr)
    print(df["bbh_ratio"].describe()[["min","25%","50%","75%","max"]].to_string(),
          file=sys.stderr)


if __name__ == "__main__":
    main()

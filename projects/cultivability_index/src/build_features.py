"""
NB01 feature-matrix construction, scripted for runtime validation.
Builds per-genome GapMind pathway completeness matrix + metadata covariates
for HQ-filtered (CheckM >= 95, contam <= 5) BERDL genomes.

Outputs:
  data/features.parquet        — wide matrix: genome_id × 80 pathways + covariates + label
  data/cohort_summary.tsv      — n by label × phylum
  data/family_overlap.tsv      — per-family n_isolate / n_mag
"""
from pathlib import Path
import time

import pandas as pd
from berdl_notebook_utils.setup_spark_session import get_spark_session

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

spark = get_spark_session()
print(f"Spark {spark.version}")

# ---------------------------------------------------------------------------
# Step 1: labeled cohort with quality gate and taxonomy
# ---------------------------------------------------------------------------
t0 = time.time()
print("\n[1/4] Labeled cohort (CheckM >= 95, contam <= 5)...")

cohort_sql = """
SELECT
  REGEXP_REPLACE(m.accession, '^(RS_|GB_)', '') AS genome_id,
  CASE WHEN m.ncbi_genome_category = 'none' THEN 1 ELSE 0 END AS is_isolate,
  m.ncbi_genome_category AS raw_category,
  CAST(m.checkm_completeness AS DOUBLE) AS checkm_comp,
  CAST(m.checkm_contamination AS DOUBLE) AS checkm_contam,
  CAST(m.genome_size AS DOUBLE) AS genome_size,
  CAST(m.gc_percentage AS DOUBLE) AS gc_pct,
  CAST(m.contig_count AS INT) AS contig_count,
  CAST(m.n50_contigs AS INT) AS n50_contigs,
  t.phylum, t.class, t.`order`, t.family, t.genus, t.species
FROM kbase_ke_pangenome.gtdb_metadata m
JOIN kbase_ke_pangenome.gtdb_taxonomy_r214v1 t
  ON REGEXP_REPLACE(m.accession, '^(RS_|GB_)', '')
   = REGEXP_REPLACE(t.genome_id, '^(RS_|GB_)', '')
WHERE CAST(m.checkm_completeness AS DOUBLE) >= 95
  AND CAST(m.checkm_contamination AS DOUBLE) <= 5
  AND m.ncbi_genome_category IN (
    'none',
    'derived from metagenome',
    'derived from environmental sample',
    'derived from single cell'
  )
"""
cohort = spark.sql(cohort_sql)
cohort.createOrReplaceTempView("cohort")
n_cohort = cohort.count()
print(f"   HQ labeled cohort: {n_cohort:,} genomes ({time.time()-t0:.1f}s)")

# ---------------------------------------------------------------------------
# Step 2: per-genome × per-pathway binary completeness matrix
# ---------------------------------------------------------------------------
t1 = time.time()
print("\n[2/4] GapMind aggregation (MAX score_simplified per pathway)...")

gp_sql = """
SELECT
  gp.genome_id,
  gp.metabolic_category,
  gp.pathway,
  MAX(CAST(gp.score_simplified AS DOUBLE)) AS complete
FROM kbase_ke_pangenome.gapmind_pathways gp
JOIN cohort c ON gp.genome_id = c.genome_id
WHERE gp.sequence_scope = 'all'
GROUP BY gp.genome_id, gp.metabolic_category, gp.pathway
"""
print("   Pulling long-form to pandas for pivot...")
long_pd = spark.sql(gp_sql).toPandas()
print(f"   Long-form rows: {len(long_pd):,} ({time.time()-t1:.1f}s)")

wide_pd = (
    long_pd.assign(path_col=lambda d: d["metabolic_category"] + "__" + d["pathway"])
    .pivot_table(index="genome_id", columns="path_col", values="complete", aggfunc="max", fill_value=0)
    .reset_index()
)
print(f"   Wide matrix: {wide_pd.shape[0]:,} genomes × {wide_pd.shape[1]-1} pathway columns")

# ---------------------------------------------------------------------------
# Step 3: join cohort metadata + pathway matrix
# ---------------------------------------------------------------------------
t2 = time.time()
print("\n[3/4] Joining cohort metadata + pathway matrix...")
cohort_pd = cohort.toPandas()
features = cohort_pd.merge(wide_pd, on="genome_id", how="inner")
print(f"   Joined feature matrix: {features.shape[0]:,} genomes × {features.shape[1]} cols ({time.time()-t2:.1f}s)")
print(f"   Label balance: isolate={features['is_isolate'].sum():,}, mag={(1-features['is_isolate']).sum():,}")

# ---------------------------------------------------------------------------
# Step 4: write outputs
# ---------------------------------------------------------------------------
t3 = time.time()
print("\n[4/4] Writing outputs...")
features.to_parquet(DATA_DIR / "features.parquet", index=False)
print(f"   data/features.parquet written ({(DATA_DIR / 'features.parquet').stat().st_size/1e6:.1f} MB)")

# Cohort summary by label × phylum
summary = (
    features.groupby(["phylum", "is_isolate"]).size().unstack(fill_value=0).reset_index()
    .rename(columns={0: "mag", 1: "isolate"})
)
summary["total"] = summary["mag"] + summary["isolate"]
summary["frac_isolate"] = (summary["isolate"] / summary["total"]).round(3)
summary = summary.sort_values("total", ascending=False)
summary.to_csv(DATA_DIR / "cohort_summary.tsv", sep="\t", index=False)
print(f"   data/cohort_summary.tsv: {len(summary)} phyla")

# Family overlap
fam = (
    features.groupby("family")["is_isolate"]
    .agg(n_iso="sum", n_total="size")
    .reset_index()
)
fam["n_mag"] = fam["n_total"] - fam["n_iso"]
fam["both"] = ((fam["n_iso"] >= 5) & (fam["n_mag"] >= 5)).astype(int)
fam = fam.sort_values("n_total", ascending=False)
fam.to_csv(DATA_DIR / "family_overlap.tsv", sep="\t", index=False)
print(f"   data/family_overlap.tsv: {len(fam)} families, {fam['both'].sum()} with >=5 of both labels")

print(f"\nTotal runtime: {time.time()-t0:.1f}s")

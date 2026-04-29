"""NB22e — audit the pangenome-internal environment tables I missed.

Two tables in kbase_ke_pangenome that map genomes to environment data, that I should
have audited before recommending P4-D1 scope:

  - sample (293,059 rows, 1:1 with genomes): genome_id → ncbi_biosample_accession_id
  - ncbi_env (4.1M rows, EAV): biosample → harmonized_name → content
  - alphaearth_embeddings_all_years (83,287 rows, 28.4%): geospatial 64-dim embeddings

And a quick check of what's in kescience_mgnify (no schema doc exists, so we list).
"""
import json
import pandas as pd
from pyspark.sql import functions as F
from berdl_notebook_utils.setup_spark_session import get_spark_session

spark = get_spark_session()
species = pd.read_csv("/home/aparkin/BERIL-research-observatory/projects/gene_function_ecological_agora/data/p1b_full_species.tsv", sep="\t")
our_species = set(species["gtdb_species_clade_id"].unique())
our_genomes = set(species["representative_genome_id"].unique())
print(f"P1B species reps: {len(species):,}", flush=True)

# --- 1. sample table — 1:1 with genome ---
print("\n--- 1. sample table coverage ---", flush=True)
sample = spark.table("kbase_ke_pangenome.sample")
print(f"  total rows: {sample.count():,}", flush=True)
species_sdf = spark.createDataFrame(species[["representative_genome_id", "gtdb_species_clade_id"]])
sample_join = species_sdf.join(F.broadcast(sample), species_sdf["representative_genome_id"] == sample["genome_id"], "left")
biosample_stats = sample_join.agg(
    F.count("*").alias("total"),
    F.sum(F.when(F.col("ncbi_biosample_accession_id").isNotNull(), 1).otherwise(0)).alias("with_biosample"),
    F.countDistinct("ncbi_biosample_accession_id").alias("distinct_biosamples"),
).collect()[0].asDict()
print(f"  P1B species: {biosample_stats}", flush=True)

# --- 2. ncbi_env coverage ---
print("\n--- 2. ncbi_env (EAV) coverage ---", flush=True)
env = spark.table("kbase_ke_pangenome.ncbi_env")
print(f"  total rows: {env.count():,}", flush=True)
print(f"  schema:")
env.printSchema()

# Top harmonized_names
print(f"\n  top 30 harmonized_names by row count:")
top_hnames = env.groupBy("harmonized_name").count().orderBy(F.desc("count")).limit(30).toPandas()
print(top_hnames.to_string(index=False), flush=True)

# Get distinct biosamples for our species
our_biosamples = sample_join.filter(F.col("ncbi_biosample_accession_id").isNotNull()).select("ncbi_biosample_accession_id").distinct()
n_our_biosamples = our_biosamples.count()
print(f"\n  our P1B biosamples: {n_our_biosamples:,}", flush=True)

# Per-attribute coverage on our species' biosamples
KEY_ATTRS = ["env_broad_scale", "env_local_scale", "env_medium", "isolation_source",
             "geo_loc_name", "lat_lon", "host", "ph", "temp", "salinity", "depth", "biome"]
print(f"\n  Coverage of key environment attributes on P1B biosamples:")
attr_cov = {}
for attr in KEY_ATTRS:
    n = (env.filter(F.col("harmonized_name") == attr)
            .join(F.broadcast(our_biosamples), env["accession"] == our_biosamples["ncbi_biosample_accession_id"])
            .select("accession").distinct().count())
    pct = 100 * n / n_our_biosamples if n_our_biosamples > 0 else 0
    print(f"    {attr}: {n:,} biosamples ({pct:.1f}% of our P1B biosamples)", flush=True)
    attr_cov[attr] = {"n": n, "pct": round(pct, 1)}

# --- 3. alphaearth_embeddings ---
print("\n--- 3. alphaearth_embeddings coverage ---", flush=True)
ae = spark.table("kbase_ke_pangenome.alphaearth_embeddings_all_years")
print(f"  total rows: {ae.count():,}", flush=True)
ae_join = species_sdf.join(F.broadcast(ae.select("genome_id", "cleaned_lat", "cleaned_lon", "cleaned_year")),
                            species_sdf["representative_genome_id"] == ae["genome_id"], "left")
ae_stats = ae_join.agg(
    F.count("*").alias("total"),
    F.sum(F.when(F.col("cleaned_lat").isNotNull(), 1).otherwise(0)).alias("with_alphaearth"),
).collect()[0].asDict()
ae_pct = 100 * ae_stats["with_alphaearth"] / 18989
print(f"  AlphaEarth coverage on P1B: {ae_stats['with_alphaearth']:,} of 18,989 ({ae_pct:.1f}%)", flush=True)

# --- 4. kescience_mgnify catalog ---
print("\n--- 4. kescience_mgnify table inventory ---", flush=True)
try:
    tables = spark.sql("SHOW TABLES IN kescience_mgnify").toPandas()
    print(f"  {len(tables)} tables in kescience_mgnify:", flush=True)
    print(tables.to_string(index=False), flush=True)
except Exception as e:
    print(f"  failed: {e}", flush=True)

# --- 5. Update audit ---
audit_path = "/home/aparkin/BERIL-research-observatory/projects/gene_function_ecological_agora/data/p4d1_feasibility_audit.json"
with open(audit_path) as f:
    audit = json.load(f)
audit["pangenome_internal_env"] = {
    "sample_table_biosample_coverage": biosample_stats,
    "ncbi_env_attribute_coverage": attr_cov,
    "alphaearth_embeddings_pct": round(ae_pct, 1),
    "alphaearth_embeddings_count": int(ae_stats["with_alphaearth"]),
}
with open(audit_path, "w") as f:
    json.dump(audit, f, indent=2, default=str)
print(f"\nUpdated audit JSON.", flush=True)

"""NB22 / P4-D1 feasibility audit — substrate coverage for phenotype/ecology grounding.

Before committing 1-2 weeks to P4-D1, check substrate coverage of our 18,989 P1B
species reps against four candidate substrates:

  1. GTDB metadata (kbase_ke_pangenome.gtdb_metadata) — ncbi_isolation_source per genome
  2. BacDive (kescience_bacdive.sequence_info) — phenotype data via GCA accession
  3. Fitness Browser (local fb_pangenome_link.tsv) — DIAMOND BBH overlap with ~30 organisms
  4. NMDC (nmdc_arkin.taxonomy_features) — sample-level taxa coverage of our species

Decision criteria:
  - GTDB isolation_source coverage ≥ 50% of our species → P4-D1 environment grounding viable
  - BacDive phenotype coverage ≥ 20% of our species → phenotype anchoring viable
  - Fitness Browser 30 organism BBH → already known ~30 species; minimal cross-clade signal
  - NMDC: count distinct GTDB species observed across the 6,365 sample taxonomy_features

Outputs:
  data/p4d1_feasibility_audit.json — per-substrate coverage stats + go/no-go decision
"""
import json, time
from pathlib import Path
import pandas as pd
from pyspark.sql import functions as F
from berdl_notebook_utils.setup_spark_session import get_spark_session

PROJECT_ROOT = Path("/home/aparkin/BERIL-research-observatory/projects/gene_function_ecological_agora")
DATA_DIR = PROJECT_ROOT / "data"

t0 = time.time()
print("=== NB22 / P4-D1 feasibility audit ===", flush=True)

# Load our species reps (local)
species = pd.read_csv(DATA_DIR / "p1b_full_species.tsv", sep="\t")
print(f"P1B species reps: {len(species):,}", flush=True)
our_species_clade_ids = set(species["gtdb_species_clade_id"].unique())
our_genomes = set(species["representative_genome_id"].unique())
print(f"  distinct gtdb_species_clade_ids: {len(our_species_clade_ids):,}", flush=True)
print(f"  distinct representative_genome_ids: {len(our_genomes):,}", flush=True)

# Sample of our genome IDs to understand format
print(f"  sample genome_ids: {list(our_genomes)[:5]}", flush=True)

# Stage 1: Fitness Browser overlap (local, no Spark)
print("\n--- Stage 1: Fitness Browser BBH overlap ---", flush=True)
fb_link = pd.read_csv("/home/aparkin/BERIL-research-observatory/projects/conservation_vs_fitness/data/fb_pangenome_link.tsv", sep="\t")
fb_species = set(fb_link["gtdb_species_clade_id"].unique())
fb_orgs = set(fb_link["orgId"].unique())
fb_overlap = fb_species & our_species_clade_ids
print(f"FB orgIds: {len(fb_orgs)}", flush=True)
print(f"FB-linked species (any project): {len(fb_species)}", flush=True)
print(f"FB-linked species in OUR P1B set: {len(fb_overlap)} of 18,989 ({100*len(fb_overlap)/len(our_species_clade_ids):.2f}%)", flush=True)

# Stage 2: Spark — GTDB metadata isolation_source coverage
print("\n--- Stage 2: GTDB metadata isolation_source coverage ---", flush=True)
spark = get_spark_session()

# Read gtdb_metadata, filter to our representative genomes
species_sdf = spark.createDataFrame(pd.DataFrame({"representative_genome_id": list(our_genomes)}))

gtdb_meta = (spark.table("kbase_ke_pangenome.gtdb_metadata")
    .select("accession", "ncbi_isolation_source", "ncbi_country", "ncbi_genome_category", "ncbi_assembly_level"))
print(f"  gtdb_metadata total rows: {gtdb_meta.count():,}", flush=True)

joined = species_sdf.join(F.broadcast(gtdb_meta), species_sdf["representative_genome_id"] == gtdb_meta["accession"], "left")
print(f"  joined to our species (with broadcast): computing coverage...", flush=True)

cov_stats = joined.agg(
    F.count("*").alias("total"),
    F.sum(F.when(F.col("accession").isNotNull(), 1).otherwise(0)).alias("matched"),
    F.sum(F.when(F.col("ncbi_isolation_source").isNotNull() & (F.col("ncbi_isolation_source") != ""), 1).otherwise(0)).alias("with_isolation_source"),
    F.sum(F.when(F.col("ncbi_country").isNotNull() & (F.col("ncbi_country") != ""), 1).otherwise(0)).alias("with_country"),
    F.sum(F.when(F.col("ncbi_genome_category") == "isolate", 1).otherwise(0)).alias("isolates"),
    F.sum(F.when(F.col("ncbi_genome_category") == "MAG", 1).otherwise(0)).alias("mags"),
    F.sum(F.when(F.col("ncbi_genome_category") == "SAG", 1).otherwise(0)).alias("sags"),
).collect()[0].asDict()
print(f"  GTDB meta coverage: {cov_stats}", flush=True)

# Top 20 isolation sources for context
print("\n  Top 20 isolation sources for our species:")
top_iso = (joined.filter(F.col("ncbi_isolation_source").isNotNull() & (F.col("ncbi_isolation_source") != ""))
    .groupBy("ncbi_isolation_source").count()
    .orderBy(F.desc("count"))
    .limit(20)
    .toPandas())
print(top_iso.to_string(index=False), flush=True)

# Stage 3: BacDive coverage
print("\n--- Stage 3: BacDive sequence_info coverage ---", flush=True)
try:
    bacdive_seq = spark.table("kescience_bacdive.sequence_info").select("accession", "species_name").filter(F.col("accession").startswith("GCA"))
    print(f"  bacdive sequence_info rows (GCA): {bacdive_seq.count():,}", flush=True)

    # Our genome IDs are like GB_GCA_xxx or RS_GCF_xxx — need to strip prefix
    species_for_bd = species[["representative_genome_id", "gtdb_species_clade_id"]].copy()
    species_for_bd["clean_acc"] = species_for_bd["representative_genome_id"].str.replace(r"^(GB_|RS_)", "", regex=True)
    print(f"  sample cleaned accessions: {species_for_bd['clean_acc'].head(3).tolist()}", flush=True)
    n_gca = species_for_bd["clean_acc"].str.startswith("GCA").sum()
    n_gcf = species_for_bd["clean_acc"].str.startswith("GCF").sum()
    print(f"  our species: {n_gca} GCA, {n_gcf} GCF", flush=True)

    species_clean_sdf = spark.createDataFrame(species_for_bd[["clean_acc", "gtdb_species_clade_id"]])
    bd_join = species_clean_sdf.join(F.broadcast(bacdive_seq), species_clean_sdf["clean_acc"] == bacdive_seq["accession"], "left")
    bd_stats = bd_join.agg(
        F.count("*").alias("total"),
        F.sum(F.when(F.col("species_name").isNotNull(), 1).otherwise(0)).alias("matched"),
        F.countDistinct(F.when(F.col("species_name").isNotNull(), F.col("gtdb_species_clade_id"))).alias("distinct_species_matched"),
    ).collect()[0].asDict()
    print(f"  BacDive coverage: {bd_stats}", flush=True)
except Exception as e:
    print(f"  BacDive query failed: {e}", flush=True)
    bd_stats = {"error": str(e)}

# Stage 4: NMDC taxonomy_features — does any of our species appear in NMDC samples?
print("\n--- Stage 4: NMDC taxonomy_features coverage ---", flush=True)
try:
    # Look at the schema first to understand what taxa look like
    nmdc_tax = spark.table("nmdc_arkin.taxonomy_features")
    print(f"  nmdc_arkin.taxonomy_features columns: {nmdc_tax.columns}", flush=True)
    print(f"  total rows: {nmdc_tax.count():,}", flush=True)
    print(f"  sample rows:")
    nmdc_tax.show(3, truncate=False)
except Exception as e:
    print(f"  NMDC taxonomy_features query failed: {e}", flush=True)

# Decision
print("\n--- DECISION ---", flush=True)
gtdb_cov_pct = 100 * cov_stats["with_isolation_source"] / cov_stats["total"]
bd_cov_pct = 100 * bd_stats.get("distinct_species_matched", 0) / len(our_species_clade_ids) if "distinct_species_matched" in bd_stats else None
fb_cov_pct = 100 * len(fb_overlap) / len(our_species_clade_ids)

print(f"GTDB isolation_source coverage: {gtdb_cov_pct:.1f}%", flush=True)
print(f"BacDive species-level coverage: {bd_cov_pct:.1f}%" if bd_cov_pct is not None else "BacDive: query failed", flush=True)
print(f"Fitness Browser BBH coverage: {fb_cov_pct:.2f}% (39 of 18,989)", flush=True)

decision = {
    "phase": "4", "deliverable": "P4-D1 feasibility",
    "n_species_p1b": len(our_species_clade_ids),
    "gtdb_metadata_coverage": cov_stats,
    "gtdb_isolation_source_pct": round(gtdb_cov_pct, 2),
    "top_isolation_sources": top_iso.to_dict(orient="records"),
    "bacdive_coverage": bd_stats,
    "bacdive_species_pct": round(bd_cov_pct, 2) if bd_cov_pct is not None else None,
    "fitnessbrowser_overlap_count": len(fb_overlap),
    "fitnessbrowser_pct": round(fb_cov_pct, 4),
    "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}
with open(DATA_DIR / "p4d1_feasibility_audit.json", "w") as f:
    json.dump(decision, f, indent=2, default=str)
print(f"\nWrote p4d1_feasibility_audit.json", flush=True)
print(f"=== DONE in {time.time()-t0:.1f}s ===", flush=True)

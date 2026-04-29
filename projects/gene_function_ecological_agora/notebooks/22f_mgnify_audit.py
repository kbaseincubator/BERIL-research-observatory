"""NB22f — MGnify catalog quick audit.

The kescience_mgnify catalog has 18 tables including biome, species, genome —
likely a parallel pangenome database with biome linkage. Audit:
  - what does the biome table look like?
  - how does species link to biome?
  - what fraction of our P1B species have a MGnify match (via GTDB taxonomy)?
"""
import json
import pandas as pd
from pyspark.sql import functions as F
from berdl_notebook_utils.setup_spark_session import get_spark_session

spark = get_spark_session()
species = pd.read_csv("/home/aparkin/BERIL-research-observatory/projects/gene_function_ecological_agora/data/p1b_full_species.tsv", sep="\t")
print(f"P1B species reps: {len(species):,}", flush=True)

for tab in ["biome", "species", "genome", "pangenome_stats"]:
    print(f"\n--- kescience_mgnify.{tab} ---", flush=True)
    t = spark.table(f"kescience_mgnify.{tab}")
    print(f"  rows: {t.count():,}")
    t.printSchema()
    print(f"  sample:")
    t.show(5, truncate=80)

# How does species link to biome?
print("\n--- Cross-walk: MGnify species → biome ---", flush=True)
mg_species = spark.table("kescience_mgnify.species")
mg_genome = spark.table("kescience_mgnify.genome")
print(f"  mgnify.species columns: {mg_species.columns}")
print(f"  mgnify.genome columns: {mg_genome.columns}")

# Overlap with our species
print("\n--- Species name overlap with our P1B (using GTDB species name) ---", flush=True)
our_gtdb_species = set(species["GTDB_species"].dropna().unique())
print(f"  our distinct GTDB species names: {len(our_gtdb_species):,}")
mg_sp_names = mg_species.select(*mg_species.columns).limit(5).toPandas()
print(f"  sample MGnify species rows:")
print(mg_sp_names.to_string(index=False, max_colwidth=80))

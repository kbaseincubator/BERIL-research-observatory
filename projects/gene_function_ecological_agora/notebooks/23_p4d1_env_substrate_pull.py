"""NB23 / P4-D1 — substrate pull for environment grounding.

Per the corrected audit (NB22e + NB22f), pull three pangenome-internal env substrates
for our 18,989 P1B species reps:

  - kbase_ke_pangenome.sample → biosample mapping (100% coverage)
  - kbase_ke_pangenome.ncbi_env (EAV) → harmonized_name in {isolation_source,
    env_broad_scale, env_local_scale, env_medium, geo_loc_name, lat_lon, host} on biosamples
  - kbase_ke_pangenome.alphaearth_embeddings_all_years → 64-dim env vectors (27.2%)
  - kescience_mgnify.species → biome_id assignment (28.4%)

Output: data/p4d1_env_per_species.parquet — per-species joined env table

Compute time: ~5-10 min Spark + local join.
"""
import time
import pandas as pd
from pathlib import Path
from pyspark.sql import functions as F
from berdl_notebook_utils.setup_spark_session import get_spark_session

PROJECT_ROOT = Path("/home/aparkin/BERIL-research-observatory/projects/gene_function_ecological_agora")
DATA_DIR = PROJECT_ROOT / "data"

t0 = time.time()
print("=== NB23 / P4-D1 — environment substrate pull ===", flush=True)

species = pd.read_csv(DATA_DIR / "p1b_full_species.tsv", sep="\t")
print(f"P1B species reps: {len(species):,}", flush=True)

spark = get_spark_session()
species_sdf = spark.createDataFrame(species[["representative_genome_id", "gtdb_species_clade_id", "GTDB_species", "genus", "family", "order", "class", "phylum"]])

# --- Stage 1: sample table ---
print("\nStage 1: sample → biosample for our reps", flush=True)
sample = spark.table("kbase_ke_pangenome.sample").select("genome_id", "ncbi_biosample_accession_id", "ncbi_bioproject_accession_id")
sp_with_biosample = species_sdf.join(F.broadcast(sample),
    species_sdf["representative_genome_id"] == sample["genome_id"], "left")
print(f"  joined; converting to pandas...", flush=True)
sp_with_biosample_pd = sp_with_biosample.select(
    "representative_genome_id", "gtdb_species_clade_id", "GTDB_species",
    "genus", "family", "order", "class", "phylum",
    "ncbi_biosample_accession_id", "ncbi_bioproject_accession_id"
).toPandas()
print(f"  rows: {len(sp_with_biosample_pd):,}, with biosample: {sp_with_biosample_pd['ncbi_biosample_accession_id'].notna().sum():,}", flush=True)

# --- Stage 2: ncbi_env EAV → pivot to per-biosample columns ---
print("\nStage 2: ncbi_env EAV pull (filtered to relevant harmonized_names)", flush=True)
ENV_ATTRS = ["isolation_source", "env_broad_scale", "env_local_scale", "env_medium",
             "geo_loc_name", "lat_lon", "host", "depth", "temp", "ph", "salinity",
             "host_disease", "sample_type", "metagenome_source"]

our_biosamples_set = set(sp_with_biosample_pd["ncbi_biosample_accession_id"].dropna().unique())
print(f"  distinct biosamples: {len(our_biosamples_set):,}", flush=True)
biosample_sdf = spark.createDataFrame(pd.DataFrame({"accession": list(our_biosamples_set)}))

env = spark.table("kbase_ke_pangenome.ncbi_env").filter(F.col("harmonized_name").isin(ENV_ATTRS))
env_for_us = (env.join(F.broadcast(biosample_sdf), env["accession"] == biosample_sdf["accession"])
    .select(env["accession"], "harmonized_name", "content"))
print(f"  filtered + joined; converting to pandas...", flush=True)
env_pd = env_for_us.toPandas()
print(f"  ncbi_env rows for our biosamples: {len(env_pd):,}", flush=True)

# Pivot EAV → wide
env_wide = env_pd.pivot_table(index="accession", columns="harmonized_name", values="content",
                                aggfunc=lambda v: ";".join(sorted(set(str(x) for x in v if pd.notna(x)))))
env_wide = env_wide.reset_index().rename(columns={"accession": "ncbi_biosample_accession_id"})
print(f"  pivoted to {len(env_wide):,} biosamples × {env_wide.shape[1]} cols", flush=True)

# --- Stage 3: AlphaEarth ---
print("\nStage 3: AlphaEarth embeddings", flush=True)
ae = spark.table("kbase_ke_pangenome.alphaearth_embeddings_all_years")
ae_cols = ["genome_id", "cleaned_lat", "cleaned_lon", "cleaned_year"] + [f"A{n:02d}" for n in range(64)]
ae_filtered = ae.select(*ae_cols).join(
    F.broadcast(species_sdf.select("representative_genome_id")),
    ae["genome_id"] == species_sdf["representative_genome_id"]
)
ae_pd = ae_filtered.toPandas()
print(f"  AlphaEarth rows for our reps: {len(ae_pd):,}", flush=True)

# --- Stage 4: MGnify biome ---
print("\nStage 4: MGnify biome assignment", flush=True)
def to_mgnify(s):
    if not isinstance(s, str): return None
    s = s[3:] if s.startswith("s__") else s
    if "_" in s: return s.replace("_", " ", 1)
    return s
sp_with_biosample_pd["mgnify_form"] = sp_with_biosample_pd["GTDB_species"].apply(to_mgnify)

mg_sp = spark.table("kescience_mgnify.species").select("gtdb_species", "biome_id", "country", "continent").toPandas()
print(f"  MGnify species rows: {len(mg_sp):,}", flush=True)

# Group by gtdb_species (multi-biome possible) and aggregate
mg_sp_grouped = (mg_sp.groupby("gtdb_species")
    .agg(mgnify_biomes=("biome_id", lambda v: ";".join(sorted(set(v.dropna())))),
         mgnify_n_biomes=("biome_id", "nunique"),
         mgnify_countries=("country", lambda v: ";".join(sorted(set(v.dropna())))[:200]),
         mgnify_continents=("continent", lambda v: ";".join(sorted(set(v.dropna())))))
    .reset_index()
    .rename(columns={"gtdb_species": "mgnify_form"}))

# --- Stage 5: Join everything ---
print("\nStage 5: join all substrates per species", flush=True)
out = sp_with_biosample_pd.merge(env_wide, on="ncbi_biosample_accession_id", how="left")
out = out.merge(mg_sp_grouped, on="mgnify_form", how="left")
out = out.merge(ae_pd, left_on="representative_genome_id", right_on="genome_id", how="left").drop(columns=["genome_id"])

# Coverage report
print(f"\nCoverage on 18,989 species:", flush=True)
for col in ["isolation_source", "env_broad_scale", "env_local_scale", "env_medium",
             "geo_loc_name", "lat_lon", "host", "mgnify_biomes", "cleaned_lat"]:
    if col in out.columns:
        n = out[col].notna().sum()
        pct = 100*n/len(out)
        print(f"  {col}: {n:,} ({pct:.1f}%)", flush=True)

# Save
out.to_parquet(DATA_DIR / "p4d1_env_per_species.parquet", index=False)
print(f"\nWrote p4d1_env_per_species.parquet ({len(out):,} rows × {out.shape[1]} cols)", flush=True)
print(f"=== DONE in {time.time()-t0:.1f}s ===", flush=True)

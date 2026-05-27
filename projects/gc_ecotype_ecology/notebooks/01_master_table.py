"""
Notebook 01: Master Table Construction

Goal: Build genome_gc_env.parquet — one row per genome with
  - genome_id, gtdb_species_clade_id, ncbi_biosample_id
  - gc_pct (CAST from string), genome_size, checkm_completeness, checkm_contamination
  - Pivoted ncbi_env fields: isolation_source, host, env_broad_scale, env_local_scale, env_medium, lat_lon, geo_loc_name
  - has_alphaearth flag

Outputs:
  - projects/gc_ecotype_ecology/data/genome_gc_env.parquet
  - figures/01_gc_distribution_overall.png
  - figures/01_field_coverage.png
"""

import os
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pyspark.sql import functions as F
from berdl_notebook_utils.setup_spark_session import get_spark_session

PROJECT_DIR = "/home/justaddcoffee/BERIL-research-observatory/projects/gc_ecotype_ecology"
DATA_DIR = os.path.join(PROJECT_DIR, "data")
FIG_DIR = os.path.join(PROJECT_DIR, "figures")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(FIG_DIR, exist_ok=True)

spark = get_spark_session()

# -----------------------------------------------------------------------------
# Step 1: Build core genome table with GC, size, quality
# -----------------------------------------------------------------------------
print("Step 1: Building core genome table...")
core = spark.sql("""
    SELECT
      g.genome_id,
      g.gtdb_species_clade_id,
      g.ncbi_biosample_id,
      CAST(m.gc_percentage      AS DOUBLE) AS gc_pct,
      CAST(m.genome_size        AS BIGINT) AS genome_size,
      CAST(m.checkm_completeness AS DOUBLE) AS checkm_completeness,
      CAST(m.checkm_contamination AS DOUBLE) AS checkm_contamination
    FROM kbase_ke_pangenome.genome g
    LEFT JOIN kbase_ke_pangenome.gtdb_metadata m
      ON m.accession = g.genome_id
""")
core.cache()
n_total = core.count()
n_with_gc = core.where(F.col("gc_pct").isNotNull()).count()
print(f"  Total genomes: {n_total:,}")
print(f"  With GC: {n_with_gc:,} ({100*n_with_gc/n_total:.1f}%)")

# -----------------------------------------------------------------------------
# Step 2: Pivot ncbi_env to wide form on the fields we care about
# -----------------------------------------------------------------------------
print("\nStep 2: Pivoting ncbi_env...")
TARGET_FIELDS = [
    "isolation_source",
    "host",
    "env_broad_scale",
    "env_local_scale",
    "env_medium",
    "lat_lon",
    "geo_loc_name",
    "sample_type",
    "host_disease",
]
env_long = spark.sql(f"""
    SELECT accession, harmonized_name, content
    FROM kbase_ke_pangenome.ncbi_env
    WHERE harmonized_name IN ({",".join(repr(f) for f in TARGET_FIELDS)})
      AND content IS NOT NULL
      AND content != ''
""")
env_wide = (
    env_long.groupBy("accession")
    .pivot("harmonized_name", TARGET_FIELDS)
    .agg(F.first("content"))
)
print(f"  Distinct biosamples with at least one env field: {env_wide.count():,}")

# -----------------------------------------------------------------------------
# Step 3: AlphaEarth presence flag
# -----------------------------------------------------------------------------
print("\nStep 3: AlphaEarth presence flag...")
ae = spark.sql("""
    SELECT DISTINCT genome_id, 1 AS has_alphaearth
    FROM kbase_ke_pangenome.alphaearth_embeddings_all_years
""")
print(f"  Genomes with AlphaEarth: {ae.count():,}")

# -----------------------------------------------------------------------------
# Step 4: Join everything
# -----------------------------------------------------------------------------
print("\nStep 4: Joining...")
master = (
    core
    .join(env_wide, core.ncbi_biosample_id == env_wide.accession, "left")
    .drop("accession")
    .join(ae, "genome_id", "left")
    .fillna(0, subset=["has_alphaearth"])
)

# Apply quality filter: keep all rows for now, flag quality so we can subset later
master = master.withColumn(
    "passes_quality",
    (F.col("checkm_completeness") >= 90) & (F.col("checkm_contamination") <= 5)
)

# -----------------------------------------------------------------------------
# Step 5: Collect to pandas (small — 293K rows × ~15 cols) and save
# -----------------------------------------------------------------------------
print("\nStep 5: Collecting to pandas and saving parquet...")
df_raw = master.toPandas()
# Clean copy to drop Spark Connect plan metadata that breaks pyarrow serialization
df = pd.DataFrame({c: df_raw[c].to_numpy() for c in df_raw.columns})
del df_raw
print(f"  Rows: {len(df):,}, cols: {len(df.columns)}")
print(f"  Columns: {list(df.columns)}")
out_path = os.path.join(DATA_DIR, "genome_gc_env.parquet")
df.to_parquet(out_path, index=False)
print(f"  Wrote {out_path}")

# -----------------------------------------------------------------------------
# Step 6: Summary statistics
# -----------------------------------------------------------------------------
print("\n=== Coverage summary ===")
summary = pd.DataFrame({
    "field": ["gc_pct", "genome_size", "checkm_completeness",
              "isolation_source", "host", "env_broad_scale",
              "env_local_scale", "env_medium", "lat_lon",
              "geo_loc_name", "host_disease", "has_alphaearth", "passes_quality"],
})
summary["n_nonnull"] = summary["field"].apply(
    lambda f: int(df[f].notna().sum()) if f != "has_alphaearth"
              else int((df[f] == 1).sum())
)
summary["pct"] = (100 * summary["n_nonnull"] / len(df)).round(1)
print(summary.to_string(index=False))
summary.to_csv(os.path.join(DATA_DIR, "01_field_coverage.csv"), index=False)

# Species with most genomes
print("\n=== Top 20 species by genome count (quality-filtered) ===")
top_species = (
    df[df["passes_quality"] & df["gc_pct"].notna()]
    .groupby("gtdb_species_clade_id")
    .size()
    .sort_values(ascending=False)
    .head(20)
)
print(top_species.to_string())
top_species.to_csv(os.path.join(DATA_DIR, "01_top_species.csv"))

# -----------------------------------------------------------------------------
# Step 7: Figures
# -----------------------------------------------------------------------------
print("\nStep 7: Figures...")
qual = df[df["passes_quality"] & df["gc_pct"].notna()]

fig, ax = plt.subplots(figsize=(8, 5))
ax.hist(qual["gc_pct"], bins=80, color="#4c72b0", edgecolor="white")
ax.set_xlabel("GC content (%)")
ax.set_ylabel("Number of genomes")
ax.set_title(f"GC content distribution across {len(qual):,} quality-filtered bacterial genomes")
ax.axvline(qual["gc_pct"].mean(), color="black", linestyle="--", linewidth=1,
           label=f"mean = {qual['gc_pct'].mean():.1f}%")
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "01_gc_distribution_overall.png"), dpi=150)
plt.close()

fig, ax = plt.subplots(figsize=(9, 5))
summary_plot = summary.set_index("field")["pct"].sort_values(ascending=True)
ax.barh(summary_plot.index, summary_plot.values, color="#55a868")
ax.set_xlabel("% of genomes with this field populated")
ax.set_title("Field coverage in the master genome table (n={:,})".format(len(df)))
for i, v in enumerate(summary_plot.values):
    ax.text(v + 0.5, i, f"{v:.1f}%", va="center", fontsize=9)
ax.set_xlim(0, 105)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "01_field_coverage.png"), dpi=150)
plt.close()

print("\nNotebook 01 complete.")
print(f"Outputs:")
print(f"  {out_path}")
print(f"  {os.path.join(DATA_DIR, '01_field_coverage.csv')}")
print(f"  {os.path.join(DATA_DIR, '01_top_species.csv')}")
print(f"  {os.path.join(FIG_DIR, '01_gc_distribution_overall.png')}")
print(f"  {os.path.join(FIG_DIR, '01_field_coverage.png')}")

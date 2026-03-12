#!/usr/bin/env python3
"""Explore MGnify Phase 1 metadata: row counts, taxonomy, overlap with BERDL pangenome."""

import pandas as pd
import os
from pathlib import Path

METADATA_DIR = Path("/home/psdehal/pangenome_science/BERIL-research-observatory/data/mgnify_ingest/metadata")
GENOME_CAT_DIR = METADATA_DIR / "genome_catalogues"

# ---- 1. Biome counts from protein DB ----
print("=" * 70)
print("MGnify Protein Database - Biome Counts")
print("=" * 70)
biome_counts = pd.read_csv(
    METADATA_DIR / "protein_db" / "mgy_biome_counts.tsv.gz",
    sep="\t", header=None, names=["count", "biome"]
)
# Show top-level biomes only
top_level = biome_counts[biome_counts["biome"].str.count(":") <= 1].copy()
top_level = top_level[top_level["count"] > 0].sort_values("count", ascending=False)
print(f"\nTop-level biomes with proteins:")
for _, row in top_level.iterrows():
    print(f"  {row['count']:>15,}  {row['biome']}")
print(f"\nTotal proteins: {biome_counts[biome_counts['biome'] == 'root']['count'].values[0]:,}")

# ---- 2. Genome catalogue summary ----
print("\n" + "=" * 70)
print("MGnify Genome Catalogues - Summary")
print("=" * 70)

all_species_reps = []
summary_rows = []

for biome_dir in sorted(GENOME_CAT_DIR.iterdir()):
    if not biome_dir.is_dir():
        continue
    meta_file = biome_dir / "genomes-all_metadata.tsv"
    if not meta_file.exists():
        continue

    df = pd.read_csv(meta_file, sep="\t")
    species_reps = df[df["Species_rep"] == df["Genome"]]

    summary_rows.append({
        "biome": biome_dir.name,
        "total_genomes": len(df),
        "species_reps": len(species_reps),
        "isolates": (df["Genome_type"] == "Isolate").sum(),
        "mags": (df["Genome_type"] == "MAG").sum(),
        "median_completeness": df["Completeness"].median(),
        "median_contamination": df["Contamination"].median(),
    })

    # Collect species reps with taxonomy for overlap analysis
    species_reps = species_reps.copy()
    species_reps["biome"] = biome_dir.name
    all_species_reps.append(species_reps[["Genome", "Lineage", "biome"]])

summary = pd.DataFrame(summary_rows).sort_values("species_reps", ascending=False)
print(f"\n{'Biome':<25} {'Genomes':>10} {'Species Reps':>12} {'Isolates':>10} {'MAGs':>8} {'Med.Comp':>8} {'Med.Cont':>8}")
print("-" * 90)
for _, row in summary.iterrows():
    print(f"{row['biome']:<25} {row['total_genomes']:>10,} {row['species_reps']:>12,} "
          f"{row['isolates']:>10,} {row['mags']:>8,} {row['median_completeness']:>8.1f} {row['median_contamination']:>8.2f}")
print("-" * 90)
print(f"{'TOTAL':<25} {summary['total_genomes'].sum():>10,} {summary['species_reps'].sum():>12,}")

# ---- 3. Taxonomy analysis ----
print("\n" + "=" * 70)
print("Taxonomy Analysis (GTDB) - All Species Reps")
print("=" * 70)

all_reps = pd.concat(all_species_reps, ignore_index=True)

# Parse taxonomy levels
for level, prefix in [("domain", "d__"), ("phylum", "p__"), ("class", "c__"),
                      ("order", "o__"), ("family", "f__"), ("genus", "g__"), ("species", "s__")]:
    all_reps[level] = all_reps["Lineage"].str.extract(f"({prefix}[^;]+)")

print(f"\nDomain distribution:")
print(all_reps["domain"].value_counts().to_string())

print(f"\nTop 15 phyla:")
print(all_reps["phylum"].value_counts().head(15).to_string())

print(f"\nTop 15 genera:")
print(all_reps["genus"].value_counts().head(15).to_string())

# ---- 4. Species-level overlap check with BERDL pangenome ----
print("\n" + "=" * 70)
print("Overlap Check: MGnify species vs BERDL Pangenome Species")
print("=" * 70)

try:
    from berdl_notebook_utils.setup_spark_session import get_spark_session
    spark = get_spark_session()

    # Get BERDL pangenome species names (GTDB taxonomy)
    berdl_species = spark.sql("""
        SELECT DISTINCT species_name
        FROM kbase_ke_pangenome.species
        WHERE species_name IS NOT NULL
    """).toPandas()

    berdl_species_set = set(berdl_species["species_name"].str.strip())

    # Extract species names from MGnify (strip "s__" prefix)
    mgnify_species = set(all_reps["species"].dropna().str.replace("s__", "", regex=False).str.strip())

    overlap = berdl_species_set & mgnify_species
    mgnify_only = mgnify_species - berdl_species_set
    berdl_only = berdl_species_set - mgnify_species

    print(f"\n  BERDL pangenome species: {len(berdl_species_set):,}")
    print(f"  MGnify species reps:     {len(mgnify_species):,}")
    print(f"  Overlap:                 {len(overlap):,} ({len(overlap)/len(mgnify_species)*100:.1f}% of MGnify)")
    print(f"  MGnify-only:             {len(mgnify_only):,}")
    print(f"  BERDL-only:              {len(berdl_only):,}")

    if overlap:
        print(f"\n  Sample overlapping species:")
        for s in sorted(overlap)[:10]:
            print(f"    {s}")

    spark.stop()

except Exception as e:
    print(f"\n  Could not connect to BERDL Spark: {e}")
    print("  Run this script in the JupyterHub environment to check overlap.")

print("\n" + "=" * 70)
print("Phase 1 metadata exploration complete.")
print("=" * 70)

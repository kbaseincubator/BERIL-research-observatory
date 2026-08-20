#!/usr/bin/env python3
"""
build_usgs_metal_concentrations.py

Surveys all 94 elements in the USGS NGDB soil+sediment samples, checks spatial
coverage against the 634 MicrobeAtlas USA sample locations, and builds a wide-format
concentration table for all elements with >= MIN_COVERAGE_FRAC coverage.

Convention: negative qualified_value = below detection limit (USGS encoding).
  - positive: detected measurement, use as-is
  - negative: below detection; set to abs(value)/2 (half detection limit)
  - qualifier 'L': estimated below detection; same treatment
All units are ppm in the NGDB for soil/sediment elements.

Outputs:
  data/usa_cwm/usgs_species_coverage.csv    -- all 94 species × coverage stats
  data/usa_cwm/usgs_concentrations_634.csv  -- wide-format, one row per sample
"""

import sys
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import pyarrow.compute as pc
import pyarrow as pa
from pathlib import Path
from scipy.spatial import cKDTree

GEOCHEM_DIR  = Path.home() / "data/envdbs/usgs_geochem"
DATA         = Path("/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/data/usa_cwm")
COV_PATH     = DATA / "covariate_matrix_634.csv"

RADIUS_DEG         = 0.45   # match spatial thinning resolution (50 km / 0.45°)
MIN_COVERAGE_FRAC  = 0.50   # ≥50% of 634 samples must have ≥1 detected value
MIN_N_MEASURE      = 200    # skip species with fewer than this many soil+sed measurements

print("=" * 70)
print("build_usgs_metal_concentrations.py")
print("=" * 70)

# ── 1. Load 634 MicrobeAtlas sample locations ─────────────────────────────────
print("\n[1] Loading covariate matrix...")
cov = pd.read_csv(COV_PATH, usecols=["sample_id", "lat", "lon"])
sample_coords = cov[["lat", "lon"]].values
N = len(cov)
print(f"  Samples: {N}")

# ── 2. Load USGS geochem metadata (soil + sediment only) ─────────────────────
print("\n[2] Loading USGS geochem metadata (soil+sediment)...")
geo = pd.read_parquet(GEOCHEM_DIR / "usgs_geochem.parquet",
                      columns=["lab_id", "latitude", "longitude", "primary_class"])
soil_sed = geo[geo["primary_class"].isin(["soil", "sediment"])].copy()
soil_sed = soil_sed.dropna(subset=["latitude", "longitude"]).reset_index(drop=True)
soil_sed_ids = set(soil_sed["lab_id"].values)
print(f"  Soil+sediment samples: {len(soil_sed):,}")

# ── 3. Load soil+sediment chemistry (pyarrow filter) ─────────────────────────
print("\n[3] Loading soil+sediment chemistry from usgs_geochem_joined...")
table = pq.read_table(
    GEOCHEM_DIR / "usgs_geochem_joined.parquet",
    columns=["lab_id", "species", "qualified_value", "qualifier"]
)
print(f"  Full table rows: {len(table):,}")
mask = pc.is_in(table["lab_id"], value_set=pa.array(list(soil_sed_ids)))
chem = table.filter(mask).to_pandas()
del table
print(f"  Soil+sediment chem rows: {len(chem):,}")
print(f"  Unique species: {chem['species'].nunique()}")

# ── 4. Parse values ────────────────────────────────────────────────────────────
# USGS encoding: negative qualified_value = below detection limit.
# Set below-detection to abs(value)/2 (half detection limit convention).
print("\n[4] Parsing values (below-detection → abs(v)/2)...")
chem["value"] = chem["qualified_value"].copy()
below_det = chem["value"] < 0
chem.loc[below_det, "value"] = chem.loc[below_det, "value"].abs() / 2.0

# Drop qualifier 'H' (highly suspect) or '>10000' outliers per species (handled below)
# Keep all other qualifiers including 'L' (estimated)
n_neg = below_det.sum()
print(f"  Below-detection rows: {n_neg:,} ({n_neg/len(chem)*100:.1f}%); set to half-limit")

# ── 5. Merge lat/lon from soil_sed ────────────────────────────────────────────
print("\n[5] Merging lat/lon...")
chem = chem.merge(
    soil_sed[["lab_id", "latitude", "longitude"]].drop_duplicates("lab_id"),
    on="lab_id", how="inner"
)
print(f"  Rows after lat/lon merge: {len(chem):,}")

# ── 6. Spatial join: for each chem point, which sample locations are within radius?
print("\n[6] Building spatial index over USGS chem points...")
chem_coords = chem[["latitude", "longitude"]].values
chem_tree = cKDTree(chem_coords)
sample_tree = cKDTree(sample_coords)

print(f"  query_ball_tree (USGS pts → MA sample locations, r={RADIUS_DEG}°)...")
# For each of 634 sample locations, find all chem rows within radius
sample_to_chem = sample_tree.query_ball_tree(chem_tree, RADIUS_DEG)

n_covered_per_sample = [len(idx) for idx in sample_to_chem]
print(f"  Samples with ≥1 USGS chem point nearby: {sum(c>0 for c in n_covered_per_sample)}/{N}")
print(f"  Median USGS pts per sample: {np.median([c for c in n_covered_per_sample if c>0]):.0f}")

# ── 7. Explode to (sample_idx, chem_idx) pairs ──────────────────────────────
print("\n[7] Exploding to sample×chem pairs...")
pair_sample_idx = []
pair_chem_idx   = []
for s_idx, chem_idx_list in enumerate(sample_to_chem):
    if chem_idx_list:
        pair_sample_idx.extend([s_idx] * len(chem_idx_list))
        pair_chem_idx.extend(chem_idx_list)

pair_sample_idx = np.array(pair_sample_idx, dtype=np.int32)
pair_chem_idx   = np.array(pair_chem_idx,   dtype=np.int32)
print(f"  Total (sample, chem-row) pairs: {len(pair_sample_idx):,}")

pairs = pd.DataFrame({
    "sample_idx": pair_sample_idx,
    "sample_id":  cov["sample_id"].values[pair_sample_idx],
    "species":    chem["species"].values[pair_chem_idx],
    "value":      chem["value"].values[pair_chem_idx],
})
print(f"  Pairs DataFrame shape: {pairs.shape}")

# ── 8. Coverage survey ────────────────────────────────────────────────────────
print("\n[8] Species coverage survey...")

species_counts = chem["species"].value_counts()
candidate_species = species_counts[species_counts >= MIN_N_MEASURE].index.tolist()
print(f"  Species with ≥{MIN_N_MEASURE} soil+sed measurements: {len(candidate_species)}")

coverage_rows = []
for sp in candidate_species:
    sp_pairs = pairs[pairs["species"] == sp]
    n_with_pos = sp_pairs[sp_pairs["value"] > 0].groupby("sample_idx").size()
    n_covered = len(n_with_pos)  # samples with ≥1 detected value
    n_total   = len(sp_pairs["sample_idx"].unique())  # any measurement (incl below-det)
    median_val = sp_pairs[sp_pairs["value"] > 0]["value"].median()
    coverage_rows.append({
        "species":              sp,
        "n_soil_sed_measurements": species_counts[sp],
        "n_samples_any":        n_total,
        "n_samples_detected":   n_covered,
        "coverage_frac":        n_covered / N,
        "median_ppm_detected":  median_val,
    })

coverage_df = pd.DataFrame(coverage_rows).sort_values("coverage_frac", ascending=False)
cov_path = DATA / "usgs_species_coverage.csv"
coverage_df.to_csv(cov_path, index=False)
print(f"  Saved: {cov_path}")
print()
print("All species coverage:")
print(coverage_df.to_string(index=False))

good_species = coverage_df[coverage_df["coverage_frac"] >= MIN_COVERAGE_FRAC]["species"].tolist()
print(f"\n  Species with ≥{MIN_COVERAGE_FRAC*100:.0f}% coverage: {len(good_species)}")
print(f"  → {good_species}")

# ── 9. Build wide-format concentration table ───────────────────────────────────
print("\n[9] Building wide-format concentration table...")

# For each (sample, species): take median of detected (positive) values
pairs_pos = pairs[pairs["value"] > 0].copy()
medians   = (pairs_pos[pairs_pos["species"].isin(good_species)]
             .groupby(["sample_id", "species"])["value"].median()
             .unstack("species")
             .reset_index())

# Rename columns to element_ppm
medians.columns.name = None
new_cols = {sp: f"{sp}_ppm" for sp in medians.columns if sp != "sample_id"}
medians = medians.rename(columns=new_cols)

# Merge onto full sample list (left join — keep all 634 samples, NaN for missing)
result = cov[["sample_id"]].merge(medians, on="sample_id", how="left")
print(f"  Result shape: {result.shape}")

# Per-element coverage
for sp in good_species:
    col = f"{sp}_ppm"
    n_cov = result[col].notna().sum()
    print(f"  {sp}: {n_cov}/{N} ({n_cov/N*100:.1f}%) median={result[col].median():.2f} ppm")

out_path = DATA / "usgs_concentrations_634.csv"
result.to_csv(out_path, index=False)
print(f"\nSaved: {out_path}")
print(f"Columns ({len(result.columns)}): {list(result.columns)}")
print("\nDone.")

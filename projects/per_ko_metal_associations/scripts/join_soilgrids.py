"""Fetch SoilGrids covariates (pH, OC, clay) for all MAGs in both KO matrices.

Deduplicates by lat/lon to minimise API calls, then fans out results to all MAGs.
Output: data/mag_soilgrids_covariates.csv  [genome_id, ph_h2o, organic_carbon_density, clay_content]
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJ_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = PROJ_DIR.parent
MET_ENV_SCRIPTS = REPO_ROOT / "metagenomic_environment_prediction" / "scripts"
MET_ENV_DATA = REPO_ROOT / "metagenomic_environment_prediction" / "data"

sys.path.insert(0, str(MET_ENV_SCRIPTS))
from soilgrids_api import SoilGridsClient  # noqa: E402

DATA_DIR = PROJ_DIR / "data"
CACHE_PATH = MET_ENV_DATA / "soilgrids_cache.json"

COVARIATE_COLS = ["ph_h2o", "organic_carbon_density", "clay_content"]


def main() -> None:
    print("Loading KO matrices ...")
    mg = pd.read_parquet(DATA_DIR / "mgnify_all_ko_matrix.parquet")
    sp = pd.read_parquet(DATA_DIR / "spire_all_ko_matrix.parquet")

    mg_mags = mg[["genome_id", "latitude", "longitude"]].drop_duplicates("genome_id")
    sp_mags = sp[["genome_id", "latitude", "longitude"]].drop_duplicates("genome_id")
    all_mags = (
        pd.concat([mg_mags, sp_mags])
        .drop_duplicates("genome_id")
        .reset_index(drop=True)
    )
    print(f"  MGnify MAGs : {len(mg_mags):,}")
    print(f"  SPIRE MAGs  : {len(sp_mags):,}")
    print(f"  Total unique: {len(all_mags):,}")

    # Deduplicate by location — one API call per unique (lat, lon)
    unique_locs = (
        all_mags[["latitude", "longitude"]]
        .drop_duplicates()
        .reset_index(drop=True)
        .copy()
    )
    print(f"  Unique lat/lon locations: {len(unique_locs):,}")

    client = SoilGridsClient(
        cache_path=str(CACHE_PATH),
        depth="0-5cm",
        timeout_s=30,
        retry_n=3,
        rate_limit_delay=0.3,
        max_workers=4,
    )
    print(f"  Cache before: {client.cache_stats()['cached']:,} entries")

    print("Fetching SoilGrids data ...")
    sg_df = client.batch_query(unique_locs, lat_col="latitude", lon_col="longitude")

    # Rename clay_pct → clay_content to match SOILGRIDS_COLS convention
    sg_df = sg_df.rename(columns={"clay_pct": "clay_content"})

    # Keep only the three covariates we care about, plus coordinates for joining
    keep = ["ph_h2o", "organic_carbon_density", "clay_content"]
    available = [c for c in keep if c in sg_df.columns]
    loc_sg = pd.concat([unique_locs, sg_df[available]], axis=1)

    coverage = loc_sg["ph_h2o"].notna().sum()
    print(f"  SoilGrids location coverage: {coverage:,}/{len(loc_sg):,} ({100*coverage/len(loc_sg):.1f}%)")
    print(f"  Cache after : {client.cache_stats()['cached']:,} entries")

    # Fan out from unique locations back to all MAGs
    result = all_mags.merge(loc_sg, on=["latitude", "longitude"], how="left")

    mag_coverage = result["ph_h2o"].notna().sum()
    print(f"  MAG-level coverage: {mag_coverage:,}/{len(result):,} ({100*mag_coverage/len(result):.1f}%)")

    # Dataset-level breakdown
    for label, mags in [("MGnify", mg_mags), ("SPIRE", sp_mags)]:
        sub = result[result.genome_id.isin(mags.genome_id)]
        n = sub["ph_h2o"].notna().sum()
        print(f"    {label}: {n:,}/{len(sub):,} ({100*n/len(sub):.1f}%)")

    out = DATA_DIR / "mag_soilgrids_covariates.csv"
    result[["genome_id"] + available].to_csv(out, index=False)
    print(f"Saved: {out}  ({len(result):,} rows)")


if __name__ == "__main__":
    main()

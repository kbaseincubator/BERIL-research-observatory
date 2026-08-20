"""Build MAG × KO matrices from Spark eggnog annotation tables.

Supports two datasets:
  - MGnify: kescience_mgnify.genome + kescience_mgnify.gene_eggnog
  - SPIRE:  refdata.spire.genome_metadata + arkinlab.spire.eggnog_annotations_spire

Output is long-format (genome_id, ko_id, count, present) Parquet.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd


QUAL_FILTER = dict(completeness=70.0, contamination=10.0)

_KO_PATTERN = r'(K\d{5})'


def _apply_quality_filter(df: pd.DataFrame, require_bacteria: bool = True) -> pd.DataFrame:
    """Filter MAGs: completeness ≥70%, contamination ≤10%, optionally Bacteria."""
    mask = (
        (df['completeness'] >= QUAL_FILTER['completeness']) &
        (df['contamination'] <= QUAL_FILTER['contamination'])
    )
    if require_bacteria and 'domain' in df.columns:
        mask &= df['domain'].str.lower() == 'bacteria'
    n_before = len(df)
    df = df[mask].copy()
    print(f"Quality filter: {n_before:,} → {len(df):,} MAGs "
          f"(completeness ≥{QUAL_FILTER['completeness']}%, "
          f"contamination ≤{QUAL_FILTER['contamination']}%"
          + (", domain=Bacteria" if require_bacteria and 'domain' in df.columns else "") + ")")
    return df


def _apply_prevalence_filter(ko_df: pd.DataFrame, n_mags: int) -> pd.DataFrame:
    """Retain KOs present in ≥ max(10, floor(0.01 × n_mags)) MAGs."""
    threshold = max(10, int(0.01 * n_mags))
    ko_counts = ko_df.groupby('ko_id')['genome_id'].nunique()
    keep = ko_counts[ko_counts >= threshold].index
    n_before = ko_df['ko_id'].nunique()
    ko_df = ko_df[ko_df['ko_id'].isin(keep)].copy()
    n_after = ko_df['ko_id'].nunique()
    print(f"Prevalence filter (threshold={threshold} MAGs): "
          f"{n_before:,} → {n_after:,} KOs retained")
    return ko_df


def build_mgnify_ko_matrix(
    spark,
    coords_path: Path,
    csu_grid: pd.DataFrame,
    output_path: Path,
    batch_csu_join_fn,
    max_mags: Optional[int] = None,
) -> pd.DataFrame:
    """Build MAG × KO long-format table for MGnify.

    Args:
        spark: active SparkSession
        coords_path: path to final_mags_geospatial_traits.csv (lat/lon)
        csu_grid: CSU metal mobility grid DataFrame (cols: lat, lon, PF1_*)
        output_path: where to write the output Parquet
        batch_csu_join_fn: env_utils.batch_csu_join callable
        max_mags: cap for testing (None = all)

    Returns:
        Long-format DataFrame (genome_id, ko_id, count, present, lat, lon, PF1_*)
    """
    # kescience_mgnify.genome: genome_id, length, completeness, contamination only.
    # genus/phylum/domain come from final_mags_geospatial_traits.csv (merged below).
    print("Pulling MGnify MAG metadata from Spark...")
    mag_meta = spark.sql("""
        SELECT
            g.genome_id,
            g.completeness,
            g.contamination,
            g.length AS genome_size
        FROM kescience_mgnify.genome g
        WHERE g.length IS NOT NULL
    """).toPandas()
    mag_meta.attrs = {}

    # Apply completeness/contamination filter (domain filter happens after CSV merge)
    mag_meta = _apply_quality_filter(mag_meta, require_bacteria=False)

    if max_mags:
        mag_meta = mag_meta.head(max_mags)
        print(f"Test cap: {max_mags} MAGs")

    # Load coordinates + taxonomy from CSV (has lat, lon, domain, phylum, genus)
    coords_df = pd.read_csv(
        coords_path,
        usecols=['genome_id', 'lat', 'lon', 'domain', 'phylum', 'genus'],
    )
    coords_df = coords_df.rename(columns={'lat': 'latitude', 'lon': 'longitude'})
    mag_meta = mag_meta.merge(coords_df, on='genome_id', how='inner')
    mag_meta = mag_meta.dropna(subset=['latitude', 'longitude'])

    # Apply domain filter now that domain column is available
    n_before = len(mag_meta)
    mag_meta = mag_meta[mag_meta['domain'].str.lower() == 'bacteria'].copy()
    print(f"Domain filter (Bacteria): {n_before:,} → {len(mag_meta):,} MAGs")
    print(f"MAGs with coordinates: {len(mag_meta):,}")

    # Spatial join to CSU metal mobility grid
    csu_grid_renamed = csu_grid.rename(columns={'lat': 'latitude', 'lon': 'longitude'})
    mag_meta = batch_csu_join_fn(mag_meta, csu_grid_renamed)
    n_with_csu = mag_meta['PF1_Cu'].notna().sum()
    print(f"MAGs with CSU data: {n_with_csu:,}")

    # Pull eggnog KO annotations from Spark (kegg_ko column; partitioned by biome_id)
    mag_ids_sql = "', '".join(mag_meta['genome_id'].tolist())
    print("Pulling MGnify eggnog KO annotations from Spark...")
    annot = spark.sql(f"""
        SELECT
            e.genome_id,
            e.kegg_ko
        FROM kescience_mgnify.gene_eggnog e
        WHERE e.genome_id IN ('{mag_ids_sql}')
          AND e.kegg_ko IS NOT NULL
          AND e.kegg_ko != '-'
    """).toPandas()
    annot.attrs = {}

    # Explode comma-separated KO values; extract K##### pattern (handles 'ko:K00001' prefix)
    annot['kegg_ko'] = annot['kegg_ko'].str.split(',')
    annot = annot.explode('kegg_ko')
    annot['ko_id'] = annot['kegg_ko'].str.extract(_KO_PATTERN)
    annot = annot.dropna(subset=['ko_id'])[['genome_id', 'ko_id']].copy()

    # Aggregate: count per (genome_id, ko_id)
    ko_counts = (
        annot.groupby(['genome_id', 'ko_id'])
        .size()
        .reset_index(name='count')
    )
    ko_counts['present'] = 1

    n_mags = mag_meta['genome_id'].nunique()
    ko_counts = _apply_prevalence_filter(ko_counts, n_mags)

    # Merge metadata (lat, lon, PF1_*, genome_size, genus, phylum)
    meta_cols = ['genome_id', 'latitude', 'longitude', 'genome_size',
                 'genus', 'phylum', 'domain'] + \
                [c for c in mag_meta.columns if c.startswith('PF1_')]
    ko_matrix = ko_counts.merge(mag_meta[meta_cols], on='genome_id', how='left')

    output_path.parent.mkdir(parents=True, exist_ok=True)
    ko_matrix.to_parquet(output_path, index=False)
    print(f"Saved MGnify KO matrix: {len(ko_matrix):,} rows "
          f"({ko_matrix['genome_id'].nunique():,} MAGs × "
          f"{ko_matrix['ko_id'].nunique():,} KOs) → {output_path}")
    return ko_matrix


def build_spire_ko_matrix(
    spark,
    csu_grid: pd.DataFrame,
    output_path: Path,
    batch_csu_join_fn,
) -> pd.DataFrame:
    """Build MAG × KO long-format table for SPIRE using internal eggnog table.

    Filters: Bacteria domain, QC (completeness ≥70%, contamination ≤10%),
    non-host/non-marine (see NOT EXISTS clause). Adds SoilGrids pH, SOC, clay
    covariates via 0.25-deg spatial join (arkinlab.envdbs.soilgrids_master).

    Note: arkinlab.spire.eggnog_annotations_spire covers ~6,270 MAGs — a small
    subset of all SPIRE MAGs. Coverage should be checked and reported.
    """
    import gc as _gc
    import numpy as np

    print("Pulling SPIRE MAG metadata from Spark...")
    mag_meta = spark.sql("""
        SELECT DISTINCT
            mc.mag_id AS genome_id,
            mc.latitude,
            mc.longitude,
            gm.genome_size,
            gm.completeness,
            gm.contamination,
            gm.genus,
            gm.domain
        FROM refdata.spire.mag_coordinates mc
        JOIN refdata.spire.genome_metadata gm ON mc.mag_id = gm.genome_id
        WHERE mc.latitude IS NOT NULL
          AND mc.longitude IS NOT NULL
          AND gm.domain = 'Bacteria'
          AND NOT EXISTS (
            SELECT 1 FROM refdata.spire.sample_microntology sm
            WHERE sm.sample_id = mc.sample_id
              AND (sm.environment_term LIKE '%host%'
                OR sm.environment_term LIKE '%gut%'
                OR sm.environment_term LIKE '%clinical%'
                OR sm.environment_term LIKE '%marine%'
                OR sm.environment_term LIKE '%ocean%'
                OR sm.environment_term LIKE '%freshwater%'
                OR sm.environment_term LIKE '%wastewater%')
          )
    """).toPandas()

    mag_meta['phylum'] = None  # SPIRE table may not have phylum; fill with None
    mag_meta = _apply_quality_filter(mag_meta)
    print(f"SPIRE MAGs with coords (soil/env, bacterial, QC): {len(mag_meta):,}")

    # SoilGrids join at 0.25-deg resolution (adds sg_pH, sg_SOC, sg_clay)
    _SG_COLS = {
        'sg_pH':  'pH_0cm',
        'sg_SOC': 'soil_organic_carbon_0cm',
        'sg_clay': 'clay_0cm',
    }
    sg_exprs = ['CAST(lat AS DOUBLE) AS lat', 'CAST(lon AS DOUBLE) AS lon']
    for alias, raw in _SG_COLS.items():
        sg_exprs.append(f'TRY_CAST(`{raw}` AS DOUBLE) AS {alias}')

    print("Pulling SoilGrids covariates from Spark...")
    sg_df = spark.sql(
        f"SELECT {', '.join(sg_exprs)} "
        f"FROM arkinlab.envdbs.soilgrids_master "
        f"WHERE lat IS NOT NULL AND lon IS NOT NULL"
    ).toPandas()
    sg_df.attrs = {}

    def _round025(x):
        return np.round(np.round(x.astype(float), 2) * 4, 0) / 4

    sg_df['lat_025'] = _round025(sg_df['lat'])
    sg_df['lon_025'] = _round025(sg_df['lon'])
    sg_df = sg_df.drop(columns=['lat', 'lon']).drop_duplicates(['lat_025', 'lon_025'])

    mag_meta['lat_025'] = _round025(mag_meta['latitude'])
    mag_meta['lon_025'] = _round025(mag_meta['longitude'])
    mag_meta = mag_meta.merge(sg_df, on=['lat_025', 'lon_025'], how='left')
    mag_meta = mag_meta.drop(columns=['lat_025', 'lon_025'])

    n_sg = mag_meta['sg_pH'].notna().sum()
    print(f"SPIRE MAGs with SoilGrids pH: {n_sg:,} / {len(mag_meta):,} "
          f"({100*n_sg/len(mag_meta):.1f}%)")

    # Spatial join to CSU metal mobility grid
    csu_grid_renamed = csu_grid.rename(columns={'lat': 'latitude', 'lon': 'longitude'})
    mag_meta = batch_csu_join_fn(mag_meta, csu_grid_renamed)
    n_with_csu = mag_meta['PF1_Cu'].notna().sum()
    print(f"SPIRE MAGs with CSU data: {n_with_csu:,}")

    if n_with_csu < 500:
        print(f"WARNING: only {n_with_csu} SPIRE MAGs have CSU data — "
              f"SPIRE will be underpowered for replication. "
              f"Proceeding with available data.")

    # Pull eggnog annotations via temp view JOIN (avoids huge IN clause)
    spire_ids = mag_meta[['genome_id']].drop_duplicates()
    spark.createDataFrame(spire_ids).createOrReplaceTempView('spire_valid_genomes')
    n_valid = len(spire_ids)
    del spire_ids
    # arkinlab.spire.eggnog_annotations_spire uses KEGG_ko column (comma-sep KO IDs)
    print(f"Pulling SPIRE eggnog KO annotations from Spark ({n_valid:,} valid MAGs)...")
    ko_agg = spark.sql("""
        WITH ko_parsed AS (
            SELECT e.mag_id AS genome_id,
                   regexp_extract(ko_part, 'K[0-9]{5}', 0) AS ko_id
            FROM arkinlab.spire.eggnog_annotations_spire e
            JOIN spire_valid_genomes v ON e.mag_id = v.genome_id
            LATERAL VIEW OUTER EXPLODE(SPLIT(e.KEGG_ko, ',')) ko_tbl AS ko_part
            WHERE e.KEGG_ko IS NOT NULL AND e.KEGG_ko != '-'
        )
        SELECT genome_id, ko_id, COUNT(*) AS count
        FROM ko_parsed
        WHERE ko_id != ''
        GROUP BY genome_id, ko_id
    """).toPandas()
    spark.catalog.dropTempView('spire_valid_genomes')
    ko_agg.attrs = {}
    print(f"Annotation rows: {len(ko_agg):,}  MAGs annotated: {ko_agg['genome_id'].nunique():,}")

    ko_agg['present'] = 1
    ko_counts = ko_agg
    n_mags = ko_agg['genome_id'].nunique()
    del ko_agg
    _gc.collect()
    ko_counts = _apply_prevalence_filter(ko_counts, n_mags)

    sg_cols_out = [c for c in mag_meta.columns if c.startswith('sg_')]
    meta_cols = ['genome_id', 'latitude', 'longitude', 'genome_size',
                 'genus', 'phylum', 'domain'] + \
                [c for c in mag_meta.columns if c.startswith('PF1_')] + \
                sg_cols_out
    ko_matrix = ko_counts.merge(mag_meta[meta_cols], on='genome_id', how='left')

    output_path.parent.mkdir(parents=True, exist_ok=True)
    ko_matrix.to_parquet(output_path, index=False)
    print(f"Saved SPIRE KO matrix: {len(ko_matrix):,} rows "
          f"({ko_matrix['genome_id'].nunique():,} MAGs × "
          f"{ko_matrix['ko_id'].nunique():,} KOs) → {output_path}")
    return ko_matrix

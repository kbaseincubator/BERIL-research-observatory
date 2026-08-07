"""
berdl_utils.py
==============
BERDL Spark session management and common queries for the comprehensive
metal ecology project.

Provides:
- get_spark_session()      — works in both JupyterHub and standalone execution
- mgnify_genus_traits()    — metal-gene KO density per MAG genus
- ngsa_geochemistry()      — NGSA soil geochemistry by sample
- ausmicrobiome_samples()  — AusMicrobiome sample metadata with coordinates
- berdl_genus_latlon()     — spatial aggregate of genus lat/lon centroids

All returned DataFrames have snake_case column names.

Usage
-----
>>> from scripts.berdl_utils import get_spark_session, mgnify_genus_traits
>>> spark = get_spark_session()
>>> traits = mgnify_genus_traits(spark, ko_ids=["K00001", "K00002"])
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import pandas as pd


# ---------------------------------------------------------------------------
# Spark session helpers
# ---------------------------------------------------------------------------

def get_spark_session(app_name: str = "comprehensive_metal_ecology"):
    """Return a Spark session, handling JupyterHub vs standalone environments.

    In JupyterHub (BERDL), ``get_spark_session`` is injected into the
    namespace and requires no arguments.  In standalone execution (e.g.
    running a script locally), we fall back to building a local-mode session.

    Returns
    -------
    pyspark.sql.SparkSession
    """
    try:
        # JupyterHub path: berdl_notebook_utils injects get_spark_session
        from berdl_notebook_utils import get_spark_session as _hub_gs
        spark = _hub_gs()
        print(f"[berdl_utils] JupyterHub SparkSession acquired: {spark.version}")
        return spark
    except ImportError:
        pass

    # Standalone / CI path: build a local SparkSession
    try:
        from pyspark.sql import SparkSession
        spark = (
            SparkSession.builder
            .appName(app_name)
            .master("local[*]")
            .config("spark.driver.memory", "4g")
            .getOrCreate()
        )
        spark.sparkContext.setLogLevel("WARN")
        print(f"[berdl_utils] Standalone SparkSession: {spark.version}")
        return spark
    except ImportError as exc:
        raise RuntimeError(
            "PySpark is not available.  Either run inside BERDL JupyterHub or "
            "`pip install pyspark`."
        ) from exc


def _spark_to_pandas(sdf) -> pd.DataFrame:
    """Convert Spark DataFrame to pandas, renaming columns to snake_case."""
    pdf = sdf.toPandas()
    pdf.columns = [c.lower().replace(" ", "_") for c in pdf.columns]
    return pdf


# ---------------------------------------------------------------------------
# MGnify MAG tables
# ---------------------------------------------------------------------------

# Default BERDL table paths — update if namespaces change
_MGNIFY_MAG_TRAITS = "mgnify.mag_metal_traits"
_MGNIFY_MAG_KO_DENSITY = "mgnify.mag_ko_density"
_MGNIFY_GENUS_GEO_NICHE = "mgnify.genus_geo_niche"
_MGNIFY_PGLS_INPUT = "mgnify.pgls_input"


def mgnify_genus_traits(
    spark,
    ko_ids: Optional[Sequence[str]] = None,
    table: str = _MGNIFY_MAG_TRAITS,
) -> pd.DataFrame:
    """Load MGnify MAG genus-level trait table.

    Parameters
    ----------
    spark:
        Active SparkSession.
    ko_ids:
        If provided, restrict to rows where the KO column is in *ko_ids*.
    table:
        Hive/Spark table name (override for alternative namespaces).

    Returns
    -------
    pd.DataFrame with columns including: genus, ko_id, ko_density_per_mb,
    n_mags, mean_genome_size_mb, lat, lon (where available).
    """
    if ko_ids is not None:
        quoted = ", ".join(f"'{k}'" for k in ko_ids)
        query = f"SELECT * FROM {table} WHERE ko_id IN ({quoted})"
    else:
        query = f"SELECT * FROM {table}"
    return _spark_to_pandas(spark.sql(query))


def mgnify_mag_ko_density(
    spark,
    ko_ids: Sequence[str],
    table: str = _MGNIFY_MAG_KO_DENSITY,
) -> pd.DataFrame:
    """Load per-MAG KO density for a list of KOs.

    Parameters
    ----------
    spark:
        Active SparkSession.
    ko_ids:
        KO identifiers (e.g. ["K00001", "K07511"]).
    table:
        Override table name.

    Returns
    -------
    pd.DataFrame with columns: mag_id, genus, ko_id, ko_count, genome_size_bp.
    """
    quoted = ", ".join(f"'{k}'" for k in ko_ids)
    query = f"SELECT * FROM {table} WHERE ko_id IN ({quoted})"
    return _spark_to_pandas(spark.sql(query))


def mgnify_pgls_input(
    spark,
    table: str = _MGNIFY_PGLS_INPUT,
) -> pd.DataFrame:
    """Load the pre-computed PGLS input table (genus × trait × geo).

    This table is the primary input for Notebooks 01 and 02.  Columns include:
    genus, genus_lower, ko_per_mb (all), mean_levins_B, mean_levins_B_std,
    lat_centroid, lon_centroid, n_samples, plus soil geochemistry columns.
    """
    return _spark_to_pandas(spark.sql(f"SELECT * FROM {table}"))


def mgnify_genus_geo_niche(
    spark,
    table: str = _MGNIFY_GENUS_GEO_NICHE,
) -> pd.DataFrame:
    """Load genus-level geographic niche table.

    Columns: genus, n_samples, mean_lat, mean_lon, sd_lat, sd_lon,
    levins_B, levins_B_std, dominant_biome.
    """
    return _spark_to_pandas(spark.sql(f"SELECT * FROM {table}"))


# ---------------------------------------------------------------------------
# NGSA geochemistry
# ---------------------------------------------------------------------------

_NGSA_GEO = "ngsa.geochemistry"


def ngsa_geochemistry(
    spark,
    metals: Optional[Sequence[str]] = None,
    table: str = _NGSA_GEO,
) -> pd.DataFrame:
    """Load NGSA soil geochemistry sample data.

    Parameters
    ----------
    spark:
        Active SparkSession.
    metals:
        If provided, restrict to these element columns (plus always-included
        lat, lon, sample_id, landuse, depth).
    table:
        Override table name.

    Returns
    -------
    pd.DataFrame with one row per sample, columns for each measured element.
    """
    base_cols = ["sample_id", "lat", "lon", "landuse", "depth"]
    if metals:
        all_cols = base_cols + list(metals)
        col_str = ", ".join(all_cols)
        query = f"SELECT {col_str} FROM {table}"
    else:
        query = f"SELECT * FROM {table}"
    return _spark_to_pandas(spark.sql(query))


# ---------------------------------------------------------------------------
# AusMicrobiome
# ---------------------------------------------------------------------------

_AUSMICROBIOME_SAMPLES = "ausmicrobiome.samples"
_AUSMICROBIOME_OTU = "ausmicrobiome.otu_table"


def ausmicrobiome_samples(
    spark,
    table: str = _AUSMICROBIOME_SAMPLES,
) -> pd.DataFrame:
    """Load AusMicrobiome sample metadata.

    Columns include: sample_id, lat, lon, biome, depth, ph, ec, collection_date,
    and any available geochemistry measurements.
    """
    return _spark_to_pandas(spark.sql(f"SELECT * FROM {table}"))


def ausmicrobiome_otu(
    spark,
    sample_ids: Optional[Sequence[str]] = None,
    table: str = _AUSMICROBIOME_OTU,
) -> pd.DataFrame:
    """Load AusMicrobiome OTU/genus abundance table.

    Parameters
    ----------
    spark:
        Active SparkSession.
    sample_ids:
        If provided, filter to these samples only.
    table:
        Override table name.

    Returns
    -------
    Long-format DataFrame: sample_id, genus, abundance.
    """
    if sample_ids:
        quoted = ", ".join(f"'{s}'" for s in sample_ids)
        query = f"SELECT * FROM {table} WHERE sample_id IN ({quoted})"
    else:
        query = f"SELECT * FROM {table}"
    return _spark_to_pandas(spark.sql(query))


# ---------------------------------------------------------------------------
# Listing available tables in a namespace
# ---------------------------------------------------------------------------

def list_tables(spark, namespace: str) -> List[str]:
    """Return list of table names in *namespace* (e.g. 'mgnify', 'ngsa').

    Useful for confounder discovery.
    """
    df = _spark_to_pandas(spark.sql(f"SHOW TABLES IN {namespace}"))
    name_col = [c for c in df.columns if "table" in c or "name" in c]
    if name_col:
        return df[name_col[0]].tolist()
    return df.iloc[:, 1].tolist()   # fallback: second column


def list_namespaces(spark) -> List[str]:
    """Return all Spark/Hive databases (namespaces) visible from this session."""
    df = _spark_to_pandas(spark.sql("SHOW DATABASES"))
    col = df.columns[0]
    return df[col].tolist()


def sample_table(spark, full_table_name: str, n: int = 5) -> pd.DataFrame:
    """Return first *n* rows of a Hive table for quick inspection."""
    return _spark_to_pandas(spark.sql(f"SELECT * FROM {full_table_name} LIMIT {n}"))


def describe_table(spark, full_table_name: str) -> pd.DataFrame:
    """Return schema info for a Hive table."""
    return _spark_to_pandas(spark.sql(f"DESCRIBE {full_table_name}"))


# ---------------------------------------------------------------------------
# Local CSV fallback loader (for offline / non-BERDL use)
# ---------------------------------------------------------------------------

_DATA = Path(__file__).parent.parent / "data"


def load_local_pgls_input() -> pd.DataFrame:
    """Load pre-extracted PGLS input CSV (data/mgnify_pgls_input.csv)."""
    p = _DATA / "mgnify_pgls_input.csv"
    if not p.exists():
        raise FileNotFoundError(
            f"Local PGLS input not found at {p}.  "
            "Run from JupyterHub with Spark to query the BERDL tables."
        )
    return pd.read_csv(p)


def load_local_ngsa() -> pd.DataFrame:
    """Load pre-extracted NGSA geochemistry CSV (data/ngsa_geochemistry.csv)."""
    p = _DATA / "ngsa_geochemistry.csv"
    if not p.exists():
        raise FileNotFoundError(f"Local NGSA data not found at {p}.")
    return pd.read_csv(p)

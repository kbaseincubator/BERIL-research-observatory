"""Compute per-Mb metal-gene KO density from eggNOG annotations.

Primary input is a DataFrame with one row per gene containing at least:
    mag_id      : str
    KEGG_ko     : str  (may be comma-separated; may carry 'ko:' prefix; may be '-')

The 140-KO primary set and subcategory labels are loaded from the
comprehensive_metal_ecology project's curated_mrg_ko_ids_v2.csv.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

KO_LIST_PATH = Path(__file__).parents[2] / "comprehensive_metal_ecology" / "data" / "curated_mrg_ko_ids_v2.csv"

# Evidence tiers that constitute the primary (Tier 1+2) set
# CSV evidence_tier values: "Tier 1", "Tier 2", "Tier 2-Fitness"
TIER_PRIMARY = {"Tier 1", "Tier 2", "Tier 2-Fitness"}

_KO_DF: Optional[pd.DataFrame] = None


def _load_ko_list() -> pd.DataFrame:
    global _KO_DF
    if _KO_DF is None:
        _KO_DF = pd.read_csv(KO_LIST_PATH)
    return _KO_DF


def get_primary_ko_set() -> frozenset[str]:
    """Return the Tier 1+2 primary set as a frozenset of KO IDs."""
    df = _load_ko_list()
    primary = df[df["evidence_tier"].isin(TIER_PRIMARY)]["KO"]
    return frozenset(primary.str.upper().str.strip())


def get_subcategory_ko_sets() -> dict[str, frozenset[str]]:
    """Return {subcategory_label: frozenset(ko_ids)} for primary KOs."""
    df = _load_ko_list()
    primary = df[df["evidence_tier"].isin(TIER_PRIMARY)].copy()
    result = {}
    for cat, grp in primary.groupby("primary_category"):
        result[cat] = frozenset(grp["KO"].str.upper().str.strip())
    return result


def normalise_ko_ids(raw: str) -> list[str]:
    """Parse a KEGG_ko field value into a list of canonical KO IDs.

    Handles:
        'ko:K00001'            -> ['K00001']
        'K00001,ko:K00002'     -> ['K00001', 'K00002']
        '-'  or  ''  or  nan   -> []
    """
    if not isinstance(raw, str) or raw.strip() in ("", "-"):
        return []
    return [re.sub(r"(?i)^ko:", "", tok.strip()).upper()
            for tok in raw.split(",")
            if tok.strip() not in ("", "-")]


def compute_mag_density(
    gene_ko_series: pd.Series,
    genome_size_bp: float,
    ko_set: frozenset[str],
) -> float:
    """Count distinct KOs from ko_set present in gene_ko_series; divide by Mb.

    Parameters
    ----------
    gene_ko_series : pd.Series of str
        KEGG_ko values for all genes of one MAG.
    genome_size_bp : float
        Total assembly length in base pairs.
    ko_set : frozenset[str]
        Set of target KO IDs (e.g. primary 140-KO set).

    Returns
    -------
    float
        KO density per megabase, or NaN if genome_size_bp <= 0.
    """
    if genome_size_bp <= 0:
        return np.nan
    detected: set[str] = set()
    for raw in gene_ko_series.dropna():
        detected.update(k for k in normalise_ko_ids(raw) if k in ko_set)
    return len(detected) / (genome_size_bp / 1e6)


def batch_compute_densities(
    annotations: pd.DataFrame,
    genome_meta: pd.DataFrame,
    mag_id_col: str = "mag_id",
    ko_col: str = "KEGG_ko",
    size_col: str = "genome_size_bp",
) -> pd.DataFrame:
    """Compute per-Mb density for every MAG in *annotations*.

    Parameters
    ----------
    annotations : DataFrame
        One row per gene; must contain mag_id_col and ko_col.
    genome_meta : DataFrame
        One row per MAG; must contain mag_id_col and size_col.
        Also used to filter to complete/clean MAGs before this call.
    mag_id_col, ko_col, size_col : str
        Column names in their respective DataFrames.

    Returns
    -------
    DataFrame
        One row per MAG with columns:
        mag_id, n_primary_KOs, ko_per_mb_primary, plus one column
        per subcategory (n_<cat>_KOs, ko_per_mb_<cat>).
    """
    primary_set = get_primary_ko_set()
    subcat_sets = get_subcategory_ko_sets()

    size_map: dict[str, float] = (
        genome_meta.set_index(mag_id_col)[size_col].to_dict()
    )

    records = []
    for mag_id, grp in annotations.groupby(mag_id_col):
        genome_size = size_map.get(mag_id, np.nan)
        if np.isnan(genome_size) or genome_size <= 0:
            continue
        row: dict = {"mag_id": mag_id, "genome_size_bp": genome_size}

        # Primary set
        detected_primary: set[str] = set()
        for raw in grp[ko_col].dropna():
            detected_primary.update(
                k for k in normalise_ko_ids(raw) if k in primary_set
            )
        row["n_primary_KOs"] = len(detected_primary)
        row["ko_per_mb_primary"] = len(detected_primary) / (genome_size / 1e6)

        # Subcategories
        for cat, kos in subcat_sets.items():
            detected_cat: set[str] = set()
            for raw in grp[ko_col].dropna():
                detected_cat.update(
                    k for k in normalise_ko_ids(raw) if k in kos
                )
            col_base = cat.lower().replace(" ", "_").replace("/", "_")
            row[f"n_{col_base}_KOs"] = len(detected_cat)
            row[f"ko_per_mb_{col_base}"] = (
                len(detected_cat) / (genome_size / 1e6)
            )

        records.append(row)

    return pd.DataFrame(records)


def filter_mag_metadata(
    genome_meta: pd.DataFrame,
    min_completeness: float = 70.0,
    max_contamination: float = 10.0,
    kingdom_col: str = "kingdom",
    completeness_col: str = "completeness",
    contamination_col: str = "contamination",
) -> pd.DataFrame:
    """Restrict to Bacteria passing quality thresholds."""
    mask = pd.Series(True, index=genome_meta.index)
    if kingdom_col in genome_meta.columns:
        mask &= genome_meta[kingdom_col].str.lower().str.startswith("bact")
    if completeness_col in genome_meta.columns:
        mask &= genome_meta[completeness_col] >= min_completeness
    if contamination_col in genome_meta.columns:
        mask &= genome_meta[contamination_col] <= max_contamination
    return genome_meta[mask].copy()

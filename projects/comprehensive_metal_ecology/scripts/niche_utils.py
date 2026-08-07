"""
niche_utils.py
==============
Compute ecological niche breadth metrics from OTU/genus abundance tables.

Primary metric: Levins' Standardised Niche Breadth (B_std), which quantifies
how broadly a genus is distributed across environments relative to its expected
breadth if samples were equally occupied.

B = 1 / sum(p_ij^2)            # Levins' B (raw)
B_std = (B - 1) / (n - 1)      # Standardised to [0,1]: 0=specialist, 1=generalist

where p_ij = relative abundance of genus i in sample j (row-normalised).

Usage
-----
>>> from scripts.niche_utils import levins_b_std, genus_niche_summary
>>> df = levins_b_std(otu, sample_col=None)      # returns Series, index=genus
>>> summary = genus_niche_summary(otu)
"""

from __future__ import annotations

from typing import List, Optional, Sequence

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Core Levins' B calculation
# ---------------------------------------------------------------------------

def levins_b_std(
    otu: pd.DataFrame,
    genus_col: Optional[str] = None,
    min_samples: int = 5,
) -> pd.Series:
    """Compute Levins' standardised niche breadth for each genus.

    Parameters
    ----------
    otu:
        OTU/abundance table.  Either:
        - Wide format: index = genus labels, columns = samples, values = counts/TPM/reads.
        - Long format with *genus_col* specified: columns genus_col, sample_id, abundance.
    genus_col:
        If *otu* is in long format, name of the genus column.  If None, *otu*
        is treated as wide (index = genera, columns = samples).
    min_samples:
        Genera observed in fewer than *min_samples* samples are returned as NaN.

    Returns
    -------
    pd.Series indexed by genus label, values = B_std ∈ [0, 1].
    """
    if genus_col is not None:
        # Long → wide
        cols = [c for c in otu.columns if c != genus_col]
        if len(cols) < 2:
            raise ValueError("Long-format otu must have genus_col + sample_id + abundance columns")
        # Assume first non-genus col is sample id, second is abundance
        sample_id_col, abund_col = cols[0], cols[1]
        wide = otu.pivot_table(index=genus_col, columns=sample_id_col,
                               values=abund_col, fill_value=0.0)
    else:
        wide = otu.copy().fillna(0.0)

    wide = wide.astype(float)

    # Row-normalise: p_ij = count / rowsum (proportional occurrence)
    row_sums = wide.sum(axis=1)
    row_sums[row_sums == 0] = np.nan
    p = wide.div(row_sums, axis=0)

    n_samples = wide.shape[1]

    # Levins' B = 1 / Σ p_ij²
    sum_p2 = (p ** 2).sum(axis=1)
    B_raw = 1.0 / sum_p2

    # Standardise to [0, 1]
    B_std = (B_raw - 1) / (n_samples - 1)
    B_std = B_std.clip(0.0, 1.0)

    # Mask genera with too few occupied samples
    n_occupied = (wide > 0).sum(axis=1)
    B_std[n_occupied < min_samples] = np.nan

    B_std.name = "levins_B_std"
    return B_std


# ---------------------------------------------------------------------------
# Summary table
# ---------------------------------------------------------------------------

def genus_niche_summary(
    otu: pd.DataFrame,
    genus_col: Optional[str] = None,
    min_samples: int = 5,
) -> pd.DataFrame:
    """Return a per-genus niche summary DataFrame.

    Columns:
        genus, n_samples_present, mean_abundance, levins_B, levins_B_std.

    Parameters
    ----------
    otu, genus_col, min_samples:
        Same as :func:`levins_b_std`.

    Returns
    -------
    pd.DataFrame sorted by levins_B_std descending.
    """
    if genus_col is not None:
        cols = [c for c in otu.columns if c != genus_col]
        sample_id_col, abund_col = cols[0], cols[1]
        wide = otu.pivot_table(index=genus_col, columns=sample_id_col,
                               values=abund_col, fill_value=0.0)
    else:
        wide = otu.copy().fillna(0.0)

    wide = wide.astype(float)
    n_samples = wide.shape[1]

    row_sums = wide.sum(axis=1)
    row_sums_safe = row_sums.replace(0, np.nan)
    p = wide.div(row_sums_safe, axis=0).fillna(0.0)

    sum_p2 = (p ** 2).sum(axis=1)
    B_raw = 1.0 / sum_p2.replace(0, np.nan)
    B_std = ((B_raw - 1) / (n_samples - 1)).clip(0.0, 1.0)

    n_occupied = (wide > 0).sum(axis=1)
    B_std[n_occupied < min_samples] = np.nan

    mean_abund = wide.mean(axis=1)

    summary = pd.DataFrame({
        "genus": wide.index,
        "n_samples_present": n_occupied.values,
        "mean_abundance": mean_abund.values,
        "levins_B": B_raw.values,
        "levins_B_std": B_std.values,
    })
    return summary.sort_values("levins_B_std", ascending=False, na_position="last")


# ---------------------------------------------------------------------------
# Metal-trait weighted niche breadth
# ---------------------------------------------------------------------------

def community_weighted_niche(
    niche: pd.Series,
    trait: pd.Series,
    genus_col: str = "genus",
) -> pd.DataFrame:
    """Compute community-weighted mean niche breadth stratified by a trait.

    Parameters
    ----------
    niche:
        Series of levins_B_std values, indexed by genus (from :func:`levins_b_std`).
    trait:
        Series indexed by genus; typically KO density or metal gene investment.
    genus_col:
        Not used (legacy parameter); both series must share the same index.

    Returns
    -------
    pd.DataFrame with columns: genus, levins_B_std, trait, product.
    """
    common = niche.index.intersection(trait.index)
    merged = pd.DataFrame({
        "levins_B_std": niche.loc[common],
        "trait": trait.loc[common],
    })
    merged = merged.dropna()
    merged["product"] = merged["levins_B_std"] * merged["trait"]
    return merged


# ---------------------------------------------------------------------------
# Per-metal niche calculation
# ---------------------------------------------------------------------------

def metal_ko_density(
    genus_ko_counts: pd.DataFrame,
    ko_list: Sequence[str],
    genome_size_col: str = "genome_size_bp",
    genus_col: str = "genus",
) -> pd.Series:
    """Compute KO density (count / genome size in Mb) for a set of KOs.

    Parameters
    ----------
    genus_ko_counts:
        Wide DataFrame: index or column = genus, other columns = KO IDs with
        counts (how many copies each genus carries on average).
    ko_list:
        KOs to include in the density calculation.
    genome_size_col:
        Column with genome size in base pairs.
    genus_col:
        Column with genus labels (if genus is not the index).

    Returns
    -------
    pd.Series of KO-density values, indexed by genus.
    """
    df = genus_ko_counts.copy()
    if genus_col in df.columns:
        df = df.set_index(genus_col)

    present_kos = [k for k in ko_list if k in df.columns]
    if not present_kos:
        raise ValueError("None of the provided KOs found in genus_ko_counts columns.")

    ko_sum = df[present_kos].sum(axis=1)

    if genome_size_col in df.columns:
        genome_mb = df[genome_size_col] / 1e6
        genome_mb = genome_mb.replace(0, np.nan)
        density = ko_sum / genome_mb
    else:
        # Fallback: raw count
        density = ko_sum.astype(float)

    density.name = "ko_density_per_mb"
    return density

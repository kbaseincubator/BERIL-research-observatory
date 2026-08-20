"""Cross-dataset comparison of KO-metal association results.

Merges MGnify and SPIRE results, checks directional consistency,
computes Spearman ρ between effect sizes.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def merge_associations(
    mgnify_df: pd.DataFrame,
    spire_df: pd.DataFrame,
    beta_col: str = 'beta',
    q_col: str = 'q_value',
    q_threshold: float = 0.05,
) -> pd.DataFrame:
    """Merge MGnify and SPIRE association results on (ko_id, metal).

    Args:
        mgnify_df: association results from NB01 for MGnify
        spire_df: association results from NB01 for SPIRE
        beta_col: name of the effect-size column
        q_col: name of the FDR q-value column
        q_threshold: significance threshold

    Returns:
        Merged DataFrame with _mgnify / _spire suffixes, directional flags,
        and joint significance flags.
    """
    left = mgnify_df[['ko_id', 'metal', beta_col, q_col, 'spearman_rho',
                       'n_present', 'n_total']].copy()
    right = spire_df[['ko_id', 'metal', beta_col, q_col, 'spearman_rho',
                       'n_present', 'n_total']].copy()

    merged = left.merge(right, on=['ko_id', 'metal'],
                        suffixes=('_mgnify', '_spire'))

    # Directional consistency: same sign of beta in both datasets
    merged['direction_consistent'] = (
        np.sign(merged[f'{beta_col}_mgnify']) ==
        np.sign(merged[f'{beta_col}_spire'])
    )

    # Significance flags
    merged['sig_mgnify'] = merged[f'{q_col}_mgnify'] < q_threshold
    merged['sig_spire'] = merged[f'{q_col}_spire'] < q_threshold
    merged['sig_both'] = merged['sig_mgnify'] & merged['sig_spire']

    return merged


def compute_beta_correlation(
    merged: pd.DataFrame,
    beta_col_m: str = 'beta_mgnify',
    beta_col_s: str = 'beta_spire',
) -> dict:
    """Compute Spearman ρ between MGnify and SPIRE beta estimates.

    Args:
        merged: output of merge_associations()
        beta_col_m, beta_col_s: beta column names for each dataset

    Returns:
        dict with rho, p_value, n_pairs, h2_supported
    """
    valid = merged[[beta_col_m, beta_col_s]].dropna()
    if len(valid) < 10:
        return {'rho': np.nan, 'p_value': np.nan,
                'n_pairs': len(valid), 'h2_supported': False}

    rho, p = stats.spearmanr(valid[beta_col_m], valid[beta_col_s])
    return {
        'rho': float(rho),
        'p_value': float(p),
        'n_pairs': len(valid),
        'h2_supported': bool(rho > 0.2),
    }


def enrichment_test(
    results_df: pd.DataFrame,
    curated_ko_set: set[str],
    q_col: str = 'q_value',
    q_threshold: float = 0.05,
) -> dict:
    """Fisher's exact test: are curated KOs enriched among FDR-significant associations?

    Args:
        results_df: association results (one row per ko_id × metal)
        curated_ko_set: set of KO IDs in the curated metal-interacting list
        q_col: FDR q-value column name
        q_threshold: significance cutoff

    Returns:
        dict with odds_ratio, p_value, n_curated_sig, n_curated_nonsig,
        n_other_sig, n_other_nonsig, h3_supported
    """
    from scipy.stats import fisher_exact

    # Use one row per KO (aggregate over metals: KO is 'significant' if sig for any metal)
    ko_sig = results_df.groupby('ko_id')[q_col].min().reset_index()
    ko_sig['is_sig'] = ko_sig[q_col] < q_threshold
    ko_sig['is_curated'] = ko_sig['ko_id'].isin(curated_ko_set)

    a = int((ko_sig['is_curated'] & ko_sig['is_sig']).sum())
    b = int((ko_sig['is_curated'] & ~ko_sig['is_sig']).sum())
    c = int((~ko_sig['is_curated'] & ko_sig['is_sig']).sum())
    d = int((~ko_sig['is_curated'] & ~ko_sig['is_sig']).sum())

    or_val, p = fisher_exact([[a, b], [c, d]], alternative='greater')

    return {
        'odds_ratio': float(or_val),
        'p_value': float(p),
        'n_curated_sig': a,
        'n_curated_nonsig': b,
        'n_other_sig': c,
        'n_other_nonsig': d,
        'h3_supported': bool(p < 0.05),
    }

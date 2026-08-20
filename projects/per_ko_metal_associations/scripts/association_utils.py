"""Per-KO association tests: logistic regression, GAM, Spearman, FDR correction.

All analyses in this project are exploratory.
"""

from __future__ import annotations

import warnings
from typing import Optional

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.formula.api import logit


def _logistic_one_ko(
    ko_df: pd.DataFrame,
    metal_col: str,
    ko_id: str,
    all_mags_df: pd.DataFrame,
    covariate_cols: Optional[list] = None,
    tax_priority: tuple = ('phylum', 'genus'),
) -> dict:
    """Run logistic regression for one KO × metal pair.

    Model: KO_present ~ PF1_metal + log_genome_size [+ C(tax_col)] [+ covariates]
    Taxonomic control level is selected from tax_priority (first column found in data).
    Returns dict with beta, SE, p_value, odds_ratio (for PF1_metal coefficient).
    """
    present_ids = set(ko_df[ko_df['ko_id'] == ko_id]['genome_id'])

    # Pick best available taxonomic column per priority order
    tax_col = None
    for col in tax_priority:
        if col in all_mags_df.columns and all_mags_df[col].notna().any():
            tax_col = col
            break

    base_cols = [metal_col, 'log_genome_size', 'genome_id']
    if tax_col:
        base_cols.append(tax_col)
    if covariate_cols:
        base_cols.extend([c for c in covariate_cols if c in all_mags_df.columns])
    df = all_mags_df[base_cols].dropna().copy()
    df['present'] = df['genome_id'].isin(present_ids).astype(int)

    n_present = df['present'].sum()
    n_absent = (df['present'] == 0).sum()
    if n_present < 5 or n_absent < 5:
        return {
            'ko_id': ko_id, 'metal': metal_col,
            'beta': np.nan, 'se': np.nan, 'p_value': np.nan,
            'odds_ratio': np.nan, 'n_present': int(n_present),
            'n_total': len(df), 'converged': False,
        }

    if tax_col:
        # Keep only groups with ≥2 MAGs AND at least one present AND one absent
        # (prevents perfect separation which causes singular matrix)
        grp = df.groupby(tax_col)['present'].agg(['sum', 'count'])
        valid_groups = grp[(grp['sum'] >= 1) & (grp['count'] - grp['sum'] >= 1) & (grp['count'] >= 2)].index
        df = df[df[tax_col].isin(valid_groups)].copy()
        if len(df) < 20:
            return {
                'ko_id': ko_id, 'metal': metal_col,
                'beta': np.nan, 'se': np.nan, 'p_value': np.nan,
                'odds_ratio': np.nan, 'n_present': int(n_present),
                'n_total': len(df), 'converged': False,
            }
        formula = f'present ~ {metal_col} + log_genome_size + C({tax_col})'
    else:
        formula = f'present ~ {metal_col} + log_genome_size'

    if covariate_cols:
        for cov in covariate_cols:
            if cov in df.columns:
                formula += f' + {cov}'

    try:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            model = logit(formula, data=df).fit(disp=False, maxiter=200)
        beta = model.params[metal_col]
        se = model.bse[metal_col]
        p = model.pvalues[metal_col]
        return {
            'ko_id': ko_id, 'metal': metal_col,
            'beta': float(beta), 'se': float(se), 'p_value': float(p),
            'odds_ratio': float(np.exp(beta)),
            'n_present': int(n_present), 'n_total': len(df),
            'converged': bool(model.mle_retvals.get('converged', True)),
        }
    except Exception:
        return {
            'ko_id': ko_id, 'metal': metal_col,
            'beta': np.nan, 'se': np.nan, 'p_value': np.nan,
            'odds_ratio': np.nan, 'n_present': int(n_present),
            'n_total': len(df), 'converged': False,
        }


def _spearman_one_ko(
    ko_df: pd.DataFrame,
    metal_col: str,
    ko_id: str,
    all_mags_df: pd.DataFrame,
) -> dict:
    """Spearman ρ between KO copy number and PF1_metal.

    MAGs where KO is absent contribute count=0.
    """
    counts = ko_df[ko_df['ko_id'] == ko_id][['genome_id', 'count']].copy()
    merged = all_mags_df[['genome_id', metal_col]].dropna().merge(
        counts, on='genome_id', how='left'
    )
    merged['count'] = merged['count'].fillna(0)

    if merged[metal_col].std() == 0 or merged['count'].std() == 0:
        return {'ko_id': ko_id, 'metal': metal_col,
                'spearman_rho': np.nan, 'spearman_p': np.nan}

    rho, p = stats.spearmanr(merged[metal_col], merged['count'])
    return {
        'ko_id': ko_id, 'metal': metal_col,
        'spearman_rho': float(rho), 'spearman_p': float(p),
    }


def fdr_correct(p_values: pd.Series) -> pd.Series:
    """Benjamini-Hochberg FDR correction. Returns q-values aligned to input index."""
    from statsmodels.stats.multitest import multipletests
    valid_mask = p_values.notna()
    q_values = pd.Series(np.nan, index=p_values.index)
    if valid_mask.sum() == 0:
        return q_values
    _, q_valid, _, _ = multipletests(p_values[valid_mask], method='fdr_bh')
    q_values[valid_mask] = q_valid
    return q_values


# Module-level globals used by multiprocessing pool workers (set via initializer)
_WORKER_KO_MATRIX: Optional[pd.DataFrame] = None
_WORKER_ALL_MAGS: Optional[pd.DataFrame] = None
_WORKER_METAL_COLS: Optional[list] = None
_WORKER_COVARIATE_COLS: Optional[list] = None
_WORKER_TAX_PRIORITY: tuple = ('phylum', 'genus')


def _pool_init(
    ko_matrix: pd.DataFrame,
    all_mags: pd.DataFrame,
    metal_cols: list,
    covariate_cols: Optional[list] = None,
    tax_priority: tuple = ('phylum', 'genus'),
) -> None:
    global _WORKER_KO_MATRIX, _WORKER_ALL_MAGS, _WORKER_METAL_COLS, _WORKER_COVARIATE_COLS, _WORKER_TAX_PRIORITY
    _WORKER_KO_MATRIX = ko_matrix
    _WORKER_ALL_MAGS = all_mags
    _WORKER_METAL_COLS = metal_cols
    _WORKER_COVARIATE_COLS = covariate_cols
    _WORKER_TAX_PRIORITY = tax_priority


def _pool_worker(ko_id: str) -> list[dict]:
    """Process all metals for one KO (called in worker process)."""
    rows = []
    for metal in _WORKER_METAL_COLS:
        if metal not in _WORKER_ALL_MAGS.columns:
            continue
        logit_row = _logistic_one_ko(
            _WORKER_KO_MATRIX, metal, ko_id, _WORKER_ALL_MAGS,
            _WORKER_COVARIATE_COLS, _WORKER_TAX_PRIORITY,
        )
        spear_row = _spearman_one_ko(_WORKER_KO_MATRIX, metal, ko_id, _WORKER_ALL_MAGS)
        rows.append({**logit_row,
                     'spearman_rho': spear_row['spearman_rho'],
                     'spearman_p': spear_row['spearman_p']})
    return rows


def run_all_ko_associations(
    ko_matrix: pd.DataFrame,
    metal_cols: list[str],
    n_workers: int = 1,
    verbose_interval: int = 500,
    checkpoint_path=None,
    checkpoint_interval: int = 50,
    covariate_cols: Optional[list] = None,
    tax_priority: tuple = ('phylum', 'genus'),
) -> pd.DataFrame:
    """Run logistic regression + Spearman for every KO × metal pair.

    Args:
        ko_matrix: long-format (genome_id, ko_id, count, present, PF1_*, genome_size, phylum)
        metal_cols: list of PF1_* column names to test
        n_workers: parallelism via multiprocessing.Pool (safe on Linux via fork + COW)
        verbose_interval: print progress every N KOs
        checkpoint_path: if given, save raw results (no q_value) here every
            checkpoint_interval KOs; on restart, resume from this file
        checkpoint_interval: flush checkpoint every N completed KOs
        tax_priority: ordered tuple of taxonomy column names to try; first found wins.
            Default ('phylum', 'genus') matches prior behaviour. Use ('class', 'phylum', 'genus')
            for class-level control, or () for no discrete taxonomy (use with phylo-PC covariates).

    Returns:
        DataFrame with one row per (ko_id, metal): beta, se, p_value, q_value,
        odds_ratio, spearman_rho, spearman_p, n_present, n_total, converged
    """
    import multiprocessing
    from pathlib import Path as _Path

    # Load checkpoint if it exists
    checkpoint_path = _Path(checkpoint_path) if checkpoint_path else None
    checkpoint_rows: list[dict] = []
    done_kos: set[str] = set()

    if checkpoint_path and checkpoint_path.exists():
        ckpt_df = pd.read_csv(checkpoint_path)
        # Drop q_value if present — will be recomputed over full set at end
        ckpt_df = ckpt_df.drop(columns=['q_value'], errors='ignore')
        checkpoint_rows = ckpt_df.to_dict('records')
        metal_set = set(metal_cols)
        ko_metal_done = ckpt_df.groupby('ko_id')['metal'].apply(set)
        done_kos = {ko for ko, metals in ko_metal_done.items() if metals >= metal_set}
        print(f"Resuming from checkpoint: {len(done_kos):,} KOs already done "
              f"({len(checkpoint_rows):,} rows loaded)", flush=True)

    # Build per-MAG metadata table (one row per genome_id)
    tax_candidates = [c for c in tax_priority if c in ko_matrix.columns]
    cov_candidates = [c for c in (covariate_cols or []) if c in ko_matrix.columns]
    mag_cols = ['genome_id', 'genome_size'] + tax_candidates + cov_candidates + \
               [c for c in ko_matrix.columns if c.startswith('PF1_')]
    all_mags = ko_matrix[mag_cols].drop_duplicates('genome_id').copy()
    all_mags['log_genome_size'] = np.log(all_mags['genome_size'].clip(lower=1e4))

    all_ko_ids = ko_matrix['ko_id'].unique().tolist()
    ko_ids = [k for k in all_ko_ids if k not in done_kos]
    skip_msg = f" ({len(done_kos):,} skipped from checkpoint)" if done_kos else ""
    print(f"Running {len(ko_ids):,} KOs × {len(metal_cols)} metals = "
          f"{len(ko_ids) * len(metal_cols):,} tests{skip_msg}", flush=True)

    rows: list[dict] = list(checkpoint_rows)

    def _save_checkpoint(current_rows: list[dict]) -> None:
        if checkpoint_path:
            pd.DataFrame(current_rows).to_csv(checkpoint_path, index=False)

    if n_workers > 1:
        ctx = multiprocessing.get_context('fork')
        with ctx.Pool(
            processes=n_workers,
            initializer=_pool_init,
            initargs=(ko_matrix, all_mags, metal_cols, covariate_cols, tax_priority),
        ) as pool:
            for i, ko_rows in enumerate(pool.imap_unordered(_pool_worker, ko_ids, chunksize=20)):
                rows.extend(ko_rows)
                if (i + 1) % verbose_interval == 0:
                    print(f"  {i+1}/{len(ko_ids)} KOs processed", flush=True)
                if checkpoint_path and (i + 1) % checkpoint_interval == 0:
                    _save_checkpoint(rows)
                    print(f"  [checkpoint: {i+1} KOs]", flush=True)
    else:
        for i, ko_id in enumerate(ko_ids):
            for metal in metal_cols:
                if metal not in all_mags.columns:
                    continue
                logit_row = _logistic_one_ko(ko_matrix, metal, ko_id, all_mags, covariate_cols, tax_priority)
                spear_row = _spearman_one_ko(ko_matrix, metal, ko_id, all_mags)
                rows.append({**logit_row,
                             'spearman_rho': spear_row['spearman_rho'],
                             'spearman_p': spear_row['spearman_p']})
            if (i + 1) % verbose_interval == 0:
                print(f"  {i+1}/{len(ko_ids)} KOs processed", flush=True)
            if checkpoint_path and (i + 1) % checkpoint_interval == 0:
                _save_checkpoint(rows)
                print(f"  [checkpoint: {i+1} KOs]", flush=True)

    # Final checkpoint flush
    _save_checkpoint(rows)

    results = pd.DataFrame(rows)

    # FDR correction per metal (across all KOs for that metal)
    results['q_value'] = np.nan
    for metal in metal_cols:
        mask = results['metal'] == metal
        results.loc[mask, 'q_value'] = fdr_correct(results.loc[mask, 'p_value']).values

    return results


def gam_delta_aic(
    ko_matrix: pd.DataFrame,
    metal_col: str,
    ko_id: str,
    all_mags_df: pd.DataFrame,
) -> float:
    """Return ΔAIC (GAM − linear logit) for one KO × metal pair.

    Positive ΔAIC means GAM fits better. Requires pygam.
    Returns nan if pygam is unavailable or fit fails.
    """
    try:
        from pygam import LogisticGAM, s, f
    except ImportError:
        return np.nan

    present_ids = set(ko_matrix[ko_matrix['ko_id'] == ko_id]['genome_id'])
    df = all_mags_df[[metal_col, 'log_genome_size', 'genome_id']].dropna().copy()
    df['present'] = df['genome_id'].isin(present_ids).astype(int)
    if len(df) < 30 or df['present'].sum() < 5:
        return np.nan

    X_linear = df[[metal_col, 'log_genome_size']].values
    X_gam = df[[metal_col, 'log_genome_size']].values
    y = df['present'].values

    try:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            logit_m = logit(
                f'present ~ {metal_col} + log_genome_size',
                data=df
            ).fit(disp=False)
            gam_m = LogisticGAM(s(0) + s(1)).fit(X_gam, y)
        aic_linear = logit_m.aic
        aic_gam = gam_m.statistics_['AIC']
        return float(aic_linear - aic_gam)
    except Exception:
        return np.nan

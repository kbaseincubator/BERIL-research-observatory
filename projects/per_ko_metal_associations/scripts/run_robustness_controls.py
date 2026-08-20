"""Phase 2 and Phase 4 robustness controls for per_ko_metal_associations.

Phase 2 — Multi-metal controls:
  For each of the 219 H1-sig and 138 latitude-adjusted pairs, add the most-correlated
  metal as a covariate.  Model: KO_present ~ PF1_target + PF1_correlate + log_genome_size + C(phylum)
  Output: data/h1_multi_metal_adjusted.csv

Phase 4 — Class-level taxonomic control (targeted, 219 pairs only):
  Model: KO_present ~ PF1_target + log_genome_size + C(tax_class) + latitude
  Uses 'class' column from final_mags_geospatial_traits.csv (renamed to tax_class to avoid
  Python reserved-word conflict in patsy formula parsing).
  Output: data/h1_fine_taxonomy_adjusted.csv

Both phases run single-threaded (fast — 219 pairs only).
"""

from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.formula.api import logit
from statsmodels.stats.multitest import multipletests

SCRIPT_DIR  = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR    = PROJECT_DIR / 'data'
GEO_PATH    = PROJECT_DIR.parent / 'microbeatlas_metal_ecology' / 'data' / 'final_mags_geospatial_traits.csv'

METAL_COLS = ['PF1_As', 'PF1_Cd', 'PF1_Cr', 'PF1_Cu', 'PF1_Hg', 'PF1_Pb']

# Most correlated metal for each target (from Phase 1a Spearman matrix)
METAL_CORRELATE = {
    'PF1_As': ('PF1_Cr', 0.684),
    'PF1_Cd': ('PF1_Cr', -0.478),
    'PF1_Cr': ('PF1_Cu', 0.710),
    'PF1_Cu': ('PF1_Cr', 0.710),
    'PF1_Hg': ('PF1_As', 0.551),
    'PF1_Pb': ('PF1_Cd', 0.167),
}


def load_mags(ko_matrix: pd.DataFrame, extra_cols: list[str] | None = None) -> pd.DataFrame:
    """Extract one-row-per-MAG metadata from the KO matrix, joining extra cols from GEO."""
    base_cols = (['genome_id', 'genome_size', 'phylum', 'genus', 'latitude']
                 + METAL_COLS)
    mags = ko_matrix[base_cols].drop_duplicates('genome_id').copy()
    mags['log_genome_size'] = np.log(mags['genome_size'].clip(lower=1e4))

    if extra_cols:
        geo = pd.read_csv(GEO_PATH, usecols=['genome_id'] + extra_cols)
        rename = {c: f'tax_{c}' for c in extra_cols if c in ('class', 'lambda', 'for', 'in')}
        geo = geo.rename(columns=rename)
        mags = mags.merge(geo, on='genome_id', how='left')

    return mags


def run_one_logit(
    ko_matrix: pd.DataFrame,
    mags_df: pd.DataFrame,
    ko_id: str,
    metal_col: str,
    formula_suffix: str,
    base_cols: list[str],
) -> dict:
    """Run logistic regression for one KO × metal, return dict with results."""
    present_ids = set(ko_matrix[ko_matrix['ko_id'] == ko_id]['genome_id'])
    df = mags_df[base_cols + [metal_col, 'log_genome_size', 'genome_id']].dropna().copy()
    df['present'] = df['genome_id'].isin(present_ids).astype(int)

    formula = f'present ~ {metal_col} + log_genome_size{formula_suffix}'

    try:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            m = logit(formula, data=df).fit(disp=False, maxiter=200)
        beta = m.params[metal_col]
        p    = m.pvalues[metal_col]
        return {
            'ko_id': ko_id, 'metal': metal_col,
            'beta': float(beta), 'p_value': float(p),
            'n_total': len(df), 'converged': bool(m.mle_retvals.get('converged', True)),
        }
    except Exception as exc:
        return {
            'ko_id': ko_id, 'metal': metal_col,
            'beta': np.nan, 'p_value': np.nan,
            'n_total': len(df), 'converged': False,
        }


# ─────────────────────────────────────────────────────────
# Phase 2 — multi-metal control
# ─────────────────────────────────────────────────────────

def run_phase2(ko_matrix: pd.DataFrame, mags: pd.DataFrame) -> pd.DataFrame:
    print('\n=== Phase 2 — Multi-metal controls ===', flush=True)

    # H1-sig pairs
    unadj = pd.read_csv(DATA_DIR / 'mgnify_all_ko_associations.csv')
    h1_sig = unadj[unadj['q_value'] < 0.05][['ko_id', 'metal', 'beta', 'q_value']].copy()
    h1_sig = h1_sig.rename(columns={'beta': 'beta_unadjusted', 'q_value': 'q_unadjusted'})
    print(f'H1-sig pairs: {len(h1_sig):,}')

    rows = []
    for i, row in enumerate(h1_sig.itertuples()):
        ko_id = row.ko_id
        metal = row.metal
        correlate, corr_rho = METAL_CORRELATE[metal]

        # Separation filter on phylum
        present_ids = set(ko_matrix[ko_matrix['ko_id'] == ko_id]['genome_id'])
        df = mags[['genome_id', metal, correlate, 'log_genome_size', 'phylum']].dropna().copy()
        df['present'] = df['genome_id'].isin(present_ids).astype(int)

        grp = df.groupby('phylum')['present'].agg(['sum', 'count'])
        valid = grp[(grp['sum'] >= 1) & (grp['count'] - grp['sum'] >= 1) & (grp['count'] >= 2)].index
        df = df[df['phylum'].isin(valid)]

        formula = f'present ~ {metal} + {correlate} + log_genome_size + C(phylum)'
        try:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                m = logit(formula, data=df).fit(disp=False, maxiter=200)
            beta_adj = float(m.params[metal])
            p_adj    = float(m.pvalues[metal])
            conv     = bool(m.mle_retvals.get('converged', True))
        except Exception:
            beta_adj, p_adj, conv = np.nan, np.nan, False

        rows.append({
            'ko_id': ko_id,
            'metal_target': metal,
            'metal_correlate': correlate,
            'corr_rho': corr_rho,
            'beta_unadjusted': row.beta_unadjusted,
            'beta_adjusted': beta_adj,
            'p_adjusted': p_adj,
            'n_total': len(df),
            'converged': conv,
        })
        if (i + 1) % 50 == 0:
            print(f'  Phase 2: {i+1}/{len(h1_sig)} pairs', flush=True)

    df_out = pd.DataFrame(rows)
    # FDR per metal
    df_out['q_adjusted'] = np.nan
    for metal in METAL_COLS:
        mask = df_out['metal_target'] == metal
        if mask.sum() > 0:
            pvals = df_out.loc[mask, 'p_adjusted']
            if pvals.notna().sum() > 0:
                _, q, _, _ = multipletests(
                    pvals.fillna(1.0), method='fdr_bh'
                )
                df_out.loc[mask, 'q_adjusted'] = np.where(pvals.notna(), q, np.nan)

    df_out['survives'] = df_out['q_adjusted'] < 0.05

    n_sig = df_out['survives'].sum()
    n_valid = df_out['p_adjusted'].notna().sum()
    print(f'\nPhase 2 results: {n_sig}/{n_valid} pairs survive multi-metal adjustment '
          f'({n_sig/max(n_valid,1)*100:.0f}%)')
    for metal in METAL_COLS:
        sub = df_out[df_out['metal_target'] == metal]
        print(f'  {metal}: {sub["survives"].sum()}/{len(sub)} survive')

    # ── Supplementary: H1-sig pairs that also survive latitude adjustment ──
    # These are the 138 pairs in the intersection of H1-sig and H4-sig (lat-adjusted)
    print('\n  Supplementary (H1∩H4-sig pairs):', flush=True)
    adj = pd.read_csv(DATA_DIR / 'mgnify_adj_ko_associations.csv')
    # Pre-index beta lookup for speed
    adj_idx = adj.set_index(['ko_id', 'metal'])['beta'].to_dict()
    # Only pairs that are in BOTH H1-sig AND lat-adjusted-sig
    adj_sig = adj[adj['q_value'] < 0.05][['ko_id', 'metal']].drop_duplicates()
    h4_sig = h1_sig[['ko_id', 'metal']].merge(adj_sig, on=['ko_id', 'metal'])
    print(f'  H1∩H4-sig pairs: {len(h4_sig)} (= pairs surviving both screens)', flush=True)

    supp_rows = []
    for si, row in enumerate(h4_sig.itertuples()):
        ko_id = str(row.ko_id)
        metal = str(row.metal)
        correlate, corr_rho = METAL_CORRELATE[metal]

        present_ids = set(ko_matrix[ko_matrix['ko_id'] == ko_id]['genome_id'])
        df = mags[['genome_id', metal, correlate, 'log_genome_size', 'phylum', 'latitude']].dropna().copy()
        df['present'] = df['genome_id'].isin(present_ids).astype(int)
        grp = df.groupby('phylum')['present'].agg(['sum', 'count'])
        valid = grp[(grp['sum'] >= 1) & (grp['count'] - grp['sum'] >= 1) & (grp['count'] >= 2)].index
        df = df[df['phylum'].isin(valid)]

        formula = f'present ~ {metal} + {correlate} + log_genome_size + latitude + C(phylum)'
        try:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                m = logit(formula, data=df).fit(disp=False, maxiter=200)
            beta_adj = float(m.params[metal])
            p_adj    = float(m.pvalues[metal])
            conv     = bool(m.mle_retvals.get('converged', True))
        except Exception:
            beta_adj, p_adj, conv = np.nan, np.nan, False

        supp_rows.append({
            'ko_id': ko_id,
            'metal_target': metal,
            'metal_correlate': correlate,
            'corr_rho': corr_rho,
            'beta_lat_adj': adj_idx.get((ko_id, metal), np.nan),
            'beta_multimetal_adj': beta_adj,
            'p_multimetal_adj': p_adj,
            'converged': conv,
        })
        if (si + 1) % 30 == 0:
            print(f'  Supplementary: {si+1}/{len(h4_sig)}', flush=True)

    supp_df = pd.DataFrame(supp_rows)
    _, supp_q, _, _ = multipletests(supp_df['p_multimetal_adj'].fillna(1.0), method='fdr_bh')
    supp_df['q_multimetal_adj'] = np.where(supp_df['p_multimetal_adj'].notna(), supp_q, np.nan)
    supp_df['survives'] = supp_df['q_multimetal_adj'] < 0.05
    n_supp = supp_df['survives'].sum()
    print(f'  {n_supp}/{len(supp_df)} lat-adjusted pairs survive combined lat+multi-metal control')

    # Merge supplementary into output
    df_out = df_out.merge(
        supp_df[['ko_id', 'metal_target', 'beta_lat_adj', 'beta_multimetal_adj',
                  'p_multimetal_adj', 'q_multimetal_adj', 'survives']].rename(
            columns={'metal_target': 'metal', 'survives': 'survives_suppl'}
        ),
        left_on=['ko_id', 'metal_target'], right_on=['ko_id', 'metal'], how='left'
    ).drop(columns='metal', errors='ignore')

    return df_out


# ─────────────────────────────────────────────────────────
# Phase 4 — class-level targeted control (219 pairs)
# ─────────────────────────────────────────────────────────

def run_phase4(ko_matrix: pd.DataFrame, mags_with_class: pd.DataFrame) -> pd.DataFrame:
    print('\n=== Phase 4 — Class-level targeted control ===', flush=True)

    unadj = pd.read_csv(DATA_DIR / 'mgnify_all_ko_associations.csv')
    h1_sig = unadj[unadj['q_value'] < 0.05][['ko_id', 'metal', 'beta']].copy()
    h1_sig = h1_sig.rename(columns={'beta': 'beta_phylum'})
    print(f'H1-sig pairs: {len(h1_sig):,}', flush=True)

    rows = []
    for i, row in enumerate(h1_sig.itertuples()):
        ko_id = row.ko_id
        metal = row.metal

        present_ids = set(ko_matrix[ko_matrix['ko_id'] == ko_id]['genome_id'])
        df = mags_with_class[['genome_id', metal, 'log_genome_size', 'tax_class', 'latitude']].dropna().copy()
        df['present'] = df['genome_id'].isin(present_ids).astype(int)

        # Separation filter at class level
        grp = df.groupby('tax_class')['present'].agg(['sum', 'count'])
        valid = grp[(grp['sum'] >= 1) & (grp['count'] - grp['sum'] >= 1) & (grp['count'] >= 2)].index
        df = df[df['tax_class'].isin(valid)]

        if len(df) < 20:
            rows.append({
                'ko_id': ko_id, 'metal': metal,
                'beta_phylum': row.beta_phylum,
                'beta_class': np.nan, 'p_class': np.nan,
                'n_total': len(df), 'converged': False,
            })
            continue

        formula = f'present ~ {metal} + log_genome_size + C(tax_class) + latitude'
        try:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                m = logit(formula, data=df).fit(disp=False, maxiter=200)
            rows.append({
                'ko_id': ko_id, 'metal': metal,
                'beta_phylum': row.beta_phylum,
                'beta_class': float(m.params[metal]),
                'p_class': float(m.pvalues[metal]),
                'n_total': len(df),
                'converged': bool(m.mle_retvals.get('converged', True)),
            })
        except Exception:
            rows.append({
                'ko_id': ko_id, 'metal': metal,
                'beta_phylum': row.beta_phylum,
                'beta_class': np.nan, 'p_class': np.nan,
                'n_total': len(df), 'converged': False,
            })

        if (i + 1) % 50 == 0:
            print(f'  Phase 4: {i+1}/{len(h1_sig)} pairs', flush=True)

    df_out = pd.DataFrame(rows)

    # FDR per metal
    df_out['q_class'] = np.nan
    for metal in METAL_COLS:
        mask = df_out['metal'] == metal
        pvals = df_out.loc[mask, 'p_class']
        if pvals.notna().sum() > 0:
            _, q, _, _ = multipletests(pvals.fillna(1.0), method='fdr_bh')
            df_out.loc[mask, 'q_class'] = np.where(pvals.notna(), q, np.nan)

    df_out['survives'] = df_out['q_class'] < 0.05
    n_sig = df_out['survives'].sum()
    n_valid = df_out['p_class'].notna().sum()
    print(f'\nPhase 4 results: {n_sig}/{n_valid} pairs survive class-level control '
          f'({n_sig/max(n_valid,1)*100:.0f}%)')

    # Beta stability: phylum vs class
    comp = df_out.dropna(subset=['beta_phylum', 'beta_class'])
    if len(comp) >= 5:
        from scipy import stats as scipy_stats
        rho, p = scipy_stats.spearmanr(comp['beta_phylum'], comp['beta_class'])
        print(f'Beta stability (phylum vs class): ρ = {rho:.3f} (p={p:.2e}, n={len(comp)})')

    for metal in METAL_COLS:
        sub = df_out[df_out['metal'] == metal]
        print(f'  {metal}: {sub["survives"].sum()}/{len(sub)} survive')

    return df_out


# ─────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────

def main() -> None:
    print('Loading KO matrix...', flush=True)
    ko = pd.read_parquet(DATA_DIR / 'mgnify_all_ko_matrix.parquet')
    print(f'  {ko["genome_id"].nunique():,} MAGs, {ko["ko_id"].nunique():,} KOs')

    mags = load_mags(ko)
    mags_with_class = load_mags(ko, extra_cols=['class'])

    # Phase 2
    phase2_df = run_phase2(ko, mags)
    phase2_df.to_csv(DATA_DIR / 'h1_multi_metal_adjusted.csv', index=False)
    print(f'Saved: data/h1_multi_metal_adjusted.csv ({len(phase2_df)} rows)')

    # Phase 4
    phase4_df = run_phase4(ko, mags_with_class)
    phase4_df.to_csv(DATA_DIR / 'h1_fine_taxonomy_adjusted.csv', index=False)
    print(f'Saved: data/h1_fine_taxonomy_adjusted.csv ({len(phase4_df)} rows)')

    print('\nAll robustness controls complete.', flush=True)


if __name__ == '__main__':
    main()

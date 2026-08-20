"""Phase 3 robustness control: MAG quality (completeness + contamination).

Three analyses:
  (A) Full model — add completeness + contamination as covariates to the H1 model
      for all 219 H1-significant pairs.
      Model: KO_present ~ PF1_target + log_genome_size + C(phylum) + completeness + contamination
  (B) Moderate restriction — re-run H1 baseline on MAGs with completeness ≥ 95%
      AND contamination ≤ 2%.
      Same model as H1 baseline: KO_present ~ PF1_target + log_genome_size + C(phylum)
  (C) Stringent restriction — re-run H1 baseline on MAGs with completeness ≥ 97%
      AND contamination ≤ 1%.

NOTE: All 8,585 MAGs in the dataset pass the ≥90%/≤5% filter used during NB00
construction. Thresholds here are tightened so that Phase 3B/3C create meaningful
subsets. Mean completeness = 95.8%, mean contamination = 1.66%.

Outputs:
  data/mgnify_mag_quality.csv              -- genome_id, completeness, contamination
  data/h1_mag_quality_adjusted.csv         -- 219 rows; Phase 3A covariate results
  data/h1_mag_quality_sensitivity_95.csv   -- 219 rows; Phase 3B ≥95%/≤2% subset
  data/h1_mag_quality_sensitivity_97.csv   -- 219 rows; Phase 3C ≥97%/≤1% subset
"""

from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.formula.api import logit
from statsmodels.stats.multitest import multipletests

SCRIPT_DIR  = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR    = PROJECT_DIR / 'data'

METAL_COLS = ['PF1_As', 'PF1_Cd', 'PF1_Cr', 'PF1_Cu', 'PF1_Hg', 'PF1_Pb']

# Two sensitivity thresholds (all MAGs already pass ≥90%/≤5% from NB00 construction)
THRESHOLDS = [
    (95.0, 2.0, '95'),   # moderate
    (97.0, 1.0, '97'),   # stringent
]


# ─────────────────────────────────────────────────────────
# Step 1: fetch MAG quality from Spark
# ─────────────────────────────────────────────────────────

def fetch_mag_quality(genome_ids: list[str]) -> pd.DataFrame:
    """Query kescience_mgnify.genome for completeness + contamination."""
    print('Connecting to Spark...', flush=True)
    try:
        from berdl_notebook_utils.setup_spark_session import get_spark_session
        spark = get_spark_session()
    except ImportError:
        from get_spark_session import get_spark_session
        spark = get_spark_session()

    print(f'  Querying genome quality for {len(genome_ids):,} MAGs...', flush=True)

    # Pull all mgnify genome quality metadata and filter in pandas
    sdf = spark.sql("""
        SELECT genome_id, completeness, contamination
        FROM kescience_mgnify.genome
    """)
    qual = sdf.toPandas()
    print(f'  Fetched {len(qual):,} rows from kescience_mgnify.genome', flush=True)

    # Filter to the MAGs in our matrix
    qual = qual[qual['genome_id'].isin(set(genome_ids))].copy()
    print(f'  {len(qual):,} rows match our {len(genome_ids):,} matrix MAGs', flush=True)
    return qual


# ─────────────────────────────────────────────────────────
# Step 2: run one logistic regression
# ─────────────────────────────────────────────────────────

def run_one_logit(
    ko_matrix: pd.DataFrame,
    mags_df: pd.DataFrame,
    ko_id: str,
    metal: str,
    extra_covariates: str = '',
) -> dict:
    """Logistic regression for one KO × metal pair."""
    present_ids = set(ko_matrix[ko_matrix['ko_id'] == ko_id]['genome_id'])
    df = mags_df.dropna().copy()
    df['present'] = df['genome_id'].isin(present_ids).astype(int)

    # Separation filter on phylum
    grp = df.groupby('phylum')['present'].agg(['sum', 'count'])
    valid = grp[(grp['sum'] >= 1) & (grp['count'] - grp['sum'] >= 1) & (grp['count'] >= 2)].index
    df = df[df['phylum'].isin(valid)]

    if len(df) < 20:
        return {'ko_id': ko_id, 'metal': metal, 'beta': np.nan, 'p_value': np.nan,
                'n_total': len(df), 'converged': False}

    formula = f'present ~ {metal} + log_genome_size + C(phylum){extra_covariates}'
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            m = logit(formula, data=df).fit(disp=False, maxiter=200)
        return {
            'ko_id': ko_id, 'metal': metal,
            'beta': float(m.params[metal]),
            'p_value': float(m.pvalues[metal]),
            'n_total': len(df),
            'converged': bool(m.mle_retvals.get('converged', True)),
        }
    except Exception:
        return {'ko_id': ko_id, 'metal': metal, 'beta': np.nan, 'p_value': np.nan,
                'n_total': len(df), 'converged': False}


# ─────────────────────────────────────────────────────────
# Phase 3A — full model with quality covariates
# ─────────────────────────────────────────────────────────

def run_phase3a(ko_matrix, mags_full, h1_sig):
    print('\n=== Phase 3A — Quality covariates (completeness + contamination) ===', flush=True)

    rows = []
    for i, row in enumerate(h1_sig.itertuples()):
        ko_id, metal = row.ko_id, row.metal
        result = run_one_logit(
            ko_matrix, mags_full, ko_id, metal,
            extra_covariates=' + completeness + contamination'
        )
        rows.append(result)
        if (i + 1) % 50 == 0:
            print(f'  Phase 3A: {i+1}/{len(h1_sig)} pairs', flush=True)

    df_out = pd.DataFrame(rows)

    # FDR per metal
    df_out['q_value'] = np.nan
    for metal in METAL_COLS:
        mask = df_out['metal'] == metal
        pvals = df_out.loc[mask, 'p_value']
        if pvals.notna().sum() > 0:
            _, q, _, _ = multipletests(pvals.fillna(1.0), method='fdr_bh')
            df_out.loc[mask, 'q_value'] = np.where(pvals.notna(), q, np.nan)

    df_out['survives'] = df_out['q_value'] < 0.05

    n_sig = df_out['survives'].sum()
    n_valid = df_out['p_value'].notna().sum()
    print(f'\nPhase 3A results: {n_sig}/{n_valid} pairs survive quality covariate control '
          f'({n_sig/max(n_valid, 1)*100:.0f}%)')
    for metal in METAL_COLS:
        sub = df_out[df_out['metal'] == metal]
        print(f'  {metal}: {sub["survives"].sum()}/{len(sub)} survive')

    return df_out


# ─────────────────────────────────────────────────────────
# Phase 3B/3C — restricted to high-quality MAG subsets
# ─────────────────────────────────────────────────────────

def run_restricted_sensitivity(ko_matrix, mags_base, h1_sig, min_completeness, max_contamination, label):
    print(f'\n=== Phase 3{label} — Restricted sensitivity '
          f'(completeness ≥{min_completeness}%, contamination ≤{max_contamination}%) ===',
          flush=True)

    hq = mags_base[
        (mags_base['completeness'] >= min_completeness) &
        (mags_base['contamination'] <= max_contamination)
    ].copy()
    n_hq = hq['genome_id'].nunique()
    print(f'  MAGs passing filter: {n_hq:,} / {mags_base["genome_id"].nunique():,} '
          f'({n_hq/mags_base["genome_id"].nunique()*100:.1f}%)', flush=True)

    ko_hq = ko_matrix[ko_matrix['genome_id'].isin(hq['genome_id'])]

    rows = []
    for i, row in enumerate(h1_sig.itertuples()):
        ko_id, metal = row.ko_id, row.metal
        result = run_one_logit(ko_hq, hq, ko_id, metal)
        rows.append(result)
        if (i + 1) % 50 == 0:
            print(f'  Phase 3{label}: {i+1}/{len(h1_sig)} pairs', flush=True)

    df_out = pd.DataFrame(rows)

    df_out['q_value'] = np.nan
    for metal in METAL_COLS:
        mask = df_out['metal'] == metal
        pvals = df_out.loc[mask, 'p_value']
        if pvals.notna().sum() > 0:
            _, q, _, _ = multipletests(pvals.fillna(1.0), method='fdr_bh')
            df_out.loc[mask, 'q_value'] = np.where(pvals.notna(), q, np.nan)

    df_out['survives'] = df_out['q_value'] < 0.05

    n_sig = df_out['survives'].sum()
    n_valid = df_out['p_value'].notna().sum()
    print(f'\nPhase 3{label} results: {n_sig}/{n_valid} pairs survive '
          f'({n_sig/max(n_valid, 1)*100:.0f}%) on {n_hq:,} MAGs')
    for metal in METAL_COLS:
        sub = df_out[df_out['metal'] == metal]
        print(f'  {metal}: {sub["survives"].sum()}/{len(sub)} survive')

    return df_out, n_hq


# ─────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────

def main() -> None:
    print('Loading KO matrix...', flush=True)
    ko = pd.read_parquet(DATA_DIR / 'mgnify_all_ko_matrix.parquet')
    genome_ids = ko['genome_id'].unique().tolist()
    print(f'  {len(genome_ids):,} unique MAGs', flush=True)

    # Step 1: fetch quality if not already saved
    qual_path = DATA_DIR / 'mgnify_mag_quality.csv'
    if qual_path.exists():
        print(f'Loading cached quality data from {qual_path}', flush=True)
        qual = pd.read_csv(qual_path)
    else:
        qual = fetch_mag_quality(genome_ids)
        qual.to_csv(qual_path, index=False)
        print(f'Saved: data/mgnify_mag_quality.csv ({len(qual):,} rows)', flush=True)

    print(f'\nQuality statistics:')
    print(f'  completeness: mean={qual["completeness"].mean():.1f}%, '
          f'median={qual["completeness"].median():.1f}%')
    print(f'  contamination: mean={qual["contamination"].mean():.2f}%, '
          f'median={qual["contamination"].median():.2f}%')
    for min_c, max_cont, tag in THRESHOLDS:
        n = ((qual['completeness'] >= min_c) & (qual['contamination'] <= max_cont)).sum()
        print(f'  completeness≥{min_c}% AND contamination≤{max_cont}%: '
              f'{n:,}/{len(qual):,} ({n/len(qual)*100:.1f}%)')

    # H1-sig pairs
    unadj = pd.read_csv(DATA_DIR / 'mgnify_all_ko_associations.csv')
    h1_sig = unadj[unadj['q_value'] < 0.05][['ko_id', 'metal', 'beta', 'q_value']].copy()
    h1_sig = h1_sig.rename(columns={'beta': 'beta_h1', 'q_value': 'q_h1'})
    print(f'\nH1-sig pairs: {len(h1_sig):,}', flush=True)

    # Build one-row-per-MAG metadata
    mags_base = (
        ko[['genome_id', 'genome_size', 'phylum', 'latitude'] + METAL_COLS]
        .drop_duplicates('genome_id')
        .copy()
    )
    mags_base['log_genome_size'] = np.log(mags_base['genome_size'].clip(lower=1e4))
    mags_base = mags_base.merge(qual[['genome_id', 'completeness', 'contamination']],
                                 on='genome_id', how='left')
    n_matched = mags_base['completeness'].notna().sum()
    print(f'Quality data matched: {n_matched:,}/{len(mags_base):,} MAGs', flush=True)

    # Phase 3A — full model with quality covariates, all MAGs
    mags_full = mags_base.dropna(subset=['completeness', 'contamination'])
    phase3a = run_phase3a(ko, mags_full, h1_sig)
    phase3a_out = h1_sig.merge(
        phase3a.rename(columns={'beta': 'beta_p3a', 'p_value': 'p_p3a',
                                'q_value': 'q_p3a', 'survives': 'survives_p3a',
                                'n_total': 'n_p3a', 'converged': 'converged_p3a'}),
        on=['ko_id', 'metal']
    )
    phase3a_out.to_csv(DATA_DIR / 'h1_mag_quality_adjusted.csv', index=False)
    print(f'Saved: data/h1_mag_quality_adjusted.csv ({len(phase3a_out)} rows)')

    # Phases 3B and 3C — restricted-subset sensitivity, two thresholds
    sens_dfs = {}
    for min_c, max_cont, tag in THRESHOLDS:
        phase_label = 'B' if tag == '95' else 'C'
        df_sens, n_hq = run_restricted_sensitivity(
            ko, mags_base, h1_sig, min_c, max_cont, phase_label
        )
        out_path = DATA_DIR / f'h1_mag_quality_sensitivity_{tag}.csv'
        out = h1_sig.merge(
            df_sens.rename(columns={
                'beta': f'beta_p3{phase_label.lower()}',
                'p_value': f'p_p3{phase_label.lower()}',
                'q_value': f'q_p3{phase_label.lower()}',
                'survives': f'survives_p3{phase_label.lower()}',
                'n_total': f'n_p3{phase_label.lower()}',
                'converged': f'converged_p3{phase_label.lower()}',
            }),
            on=['ko_id', 'metal']
        )
        out.to_csv(out_path, index=False)
        print(f'Saved: data/h1_mag_quality_sensitivity_{tag}.csv ({len(out)} rows)')
        sens_dfs[tag] = (df_sens, n_hq, out)

    # Update h1_robustness_summary.csv with Phase 3 columns
    robust = pd.read_csv(DATA_DIR / 'h1_robustness_summary.csv')
    robust = robust.merge(
        phase3a_out[['ko_id', 'metal', 'beta_p3a', 'q_p3a', 'survives_p3a']],
        on=['ko_id', 'metal'], how='left'
    )
    for min_c, max_cont, tag in THRESHOLDS:
        phase_label = 'B' if tag == '95' else 'C'
        pl = phase_label.lower()
        _, _, out = sens_dfs[tag]
        robust = robust.merge(
            out[['ko_id', 'metal', f'survives_p3{pl}', f'n_p3{pl}']],
            on=['ko_id', 'metal'], how='left'
        )

    # All-controls survival: P2 + P3A + P4 + H7 (class-level)
    robust['survives_all_controls_with_p3'] = (
        robust['survives_all_controls'] & robust['survives_p3a'].fillna(False)
    )
    n_all = robust['survives_all_controls_with_p3'].sum()
    robust.to_csv(DATA_DIR / 'h1_robustness_summary.csv', index=False)
    print(f'Updated: data/h1_robustness_summary.csv — {n_all}/219 survive all 4 controls')

    print('\nPhase 3 complete.', flush=True)
    print('Summary:')
    print(f'  Phase 3A (quality covariates, all MAGs): '
          f'{phase3a["survives"].sum()}/{phase3a["p_value"].notna().sum()} survive')
    for min_c, max_cont, tag in THRESHOLDS:
        phase_label = 'B' if tag == '95' else 'C'
        df_s, n_hq, _ = sens_dfs[tag]
        print(f'  Phase 3{phase_label} (≥{min_c}%/≤{max_cont}%, {n_hq:,} MAGs): '
              f'{df_s["survives"].sum()}/{df_s["p_value"].notna().sum()} survive')


if __name__ == '__main__':
    main()


import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.stats.multitest import multipletests

def cultivation_bias_diagnostic(
    cultured_ko: pd.DataFrame,
    mag_ko: pd.DataFrame,
    markers: dict = None,
    fdr_threshold: float = 0.05,
    pseudocount: float = 0.001
) -> dict:
    """
    Compute per-KO cultivation coverage comparing cultured genomes vs MAGs.

    Parameters
    ----------
    cultured_ko : DataFrame with columns [genome_id, ko_id]
    mag_ko : DataFrame with columns [genome_id, ko_id]
    markers : dict mapping category name -> list of KO IDs (optional)
    fdr_threshold : significance cutoff after BH correction
    pseudocount : added to prevalence fractions before log2 ratio

    Returns
    -------
    dict with keys: 'coverage' (full DataFrame), 'markers' (marker summary),
                    'summary' (dict of counts)
    """
    n_cult = cultured_ko['genome_id'].nunique()
    n_mag = mag_ko['genome_id'].nunique()

    cult_prev = cultured_ko.groupby('ko_id')['genome_id'].nunique().rename('n_cult')
    mag_prev = mag_ko.groupby('ko_id')['genome_id'].nunique().rename('n_mag')

    all_kos = sorted(set(cult_prev.index) | set(mag_prev.index))
    cov = pd.DataFrame(index=all_kos)
    cov['n_cult'] = cult_prev.reindex(cov.index).fillna(0).astype(int)
    cov['n_mag'] = mag_prev.reindex(cov.index).fillna(0).astype(int)
    cov['frac_cult'] = cov['n_cult'] / n_cult
    cov['frac_mag'] = cov['n_mag'] / n_mag
    cov['log2_ratio'] = np.log2(
        (cov['frac_cult'] + pseudocount) / (cov['frac_mag'] + pseudocount)
    )

    pvals = []
    for ko_id in cov.index:
        a = cov.loc[ko_id, 'n_cult']
        b = n_cult - a
        c = cov.loc[ko_id, 'n_mag']
        d = n_mag - c
        _, p = stats.fisher_exact([[a, b], [c, d]])
        pvals.append(p)

    cov['pval'] = pvals
    reject, qvals, _, _ = multipletests(cov['pval'], method='fdr_bh')
    cov['qval'] = qvals
    cov['significant'] = reject

    sig = cov[cov['significant']]
    summary = {
        'n_cultured_genomes': n_cult,
        'n_mag_genomes': n_mag,
        'n_kos_total': len(cov),
        'n_significant': len(sig),
        'n_enriched_cultured': len(sig[sig['log2_ratio'] > 0]),
        'n_depleted_cultured': len(sig[sig['log2_ratio'] < 0]),
        'n_cultured_only': (cov['n_mag'] == 0).sum(),
        'n_mag_only': (cov['n_cult'] == 0).sum(),
    }

    result = {'coverage': cov, 'summary': summary}

    if markers:
        marker_rows = []
        for cat, kos in markers.items():
            for ko in kos:
                if ko in cov.index:
                    row = cov.loc[ko]
                    marker_rows.append({
                        'category': cat, 'ko_id': ko,
                        'frac_cult': row['frac_cult'], 'frac_mag': row['frac_mag'],
                        'log2_ratio': row['log2_ratio'], 'qval': row['qval'],
                        'significant': row['significant']
                    })
        result['markers'] = pd.DataFrame(marker_rows)

    return result

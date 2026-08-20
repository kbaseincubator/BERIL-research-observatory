"""Operon-level aggregation for MWAS sensitivity analysis.

Tests whether operon members show correlated presence/absence patterns
and whether operon-level associations differ substantially from individual KO results.

Known metal resistance/response operons tested:
- kdp: K01546 (kdpA), K01547 (kdpC), K01548 (kdpB) — K⁺-transporting ATPase
- mer: K16306 (merA), K16307 (merC), K14658 (merR), K00526 (merE) — mercury resistance
- czc: K15725 (czcA), K15727 (czcC), K16264 (czcB) — heavy metal RND transporter
- ars: K03756 (arsA), K01551 (arsB), K00537 (arsC) — arsenic resistance ABC transporter
- pst: K02036, K02037, K02038, K02040 — phosphate ABC transporter

Strategy:
1. Load SPIRE KO matrix (long format: genome_id, ko_id, presence flags, metal PF1, environmental covariates)
2. For each operon × metal:
   - Compute operon presence = union (ANY member KO present) or intersection (ALL members present)
   - Run logistic regression: operon_present ~ PF1_metal + latitude + sg_pH + C(phylum)
   - Compare operon β to individual member βs from prior analysis
3. Save results and document findings in REPORT.md

This is a scaffold script — full execution requires the parquet matrix on disk.
Results are interpretable without formal operon aggregation: the kdp operon shows
internally inconsistent member-level signals (kdpC survives pH control, kdpB does not),
consistent with C-subunit being the ecologically informative element.
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.formula.api import logit

# Operons: KEGG KO IDs
OPERONS = {
    'kdp': ['K01546', 'K01547', 'K01548'],  # kdpA, kdpC, kdpB
    'mer': ['K16306', 'K16307', 'K14658', 'K00526'],  # merA, merC, merR, merE
    'czc': ['K15725', 'K15727', 'K16264'],  # czcA, czcC, czcB
    'ars': ['K03756', 'K01551', 'K00537'],  # arsA, arsB, arsC
    'pst': ['K02036', 'K02037', 'K02038', 'K02040'],  # phosphate ABC
}

METALS = ['PF1_As', 'PF1_Cd', 'PF1_Cr', 'PF1_Cu', 'PF1_Hg', 'PF1_Pb']

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / 'data'


def load_spire_ko_matrix() -> pd.DataFrame:
    """Load SPIRE KO matrix in long format."""
    ko_matrix = pd.read_parquet(DATA_DIR / 'spire_all_ko_matrix.parquet')
    print(f"Loaded SPIRE KO matrix: {ko_matrix.shape}")
    return ko_matrix


def compute_operon_presence(
    ko_matrix: pd.DataFrame,
    operon_kos: list[str],
    method: str = 'union',
) -> pd.DataFrame:
    """Compute operon presence per MAG.

    Args:
        ko_matrix: long-format KO matrix (genome_id, ko_id, present, ...)
        operon_kos: list of KO IDs in the operon
        method: 'union' (ANY member present) or 'intersection' (ALL members present)

    Returns:
        DataFrame with columns [genome_id, operon_present, ...]
    """
    operon_data = ko_matrix[ko_matrix['ko_id'].isin(operon_kos)].copy()

    if method == 'union':
        # Operon present if ANY member is present
        operon_by_mag = (
            operon_data.groupby('genome_id')['present'].sum() >= 1
        ).astype(int)
    elif method == 'intersection':
        # Operon present if ALL members are present
        member_count = len(operon_kos)
        operon_by_mag = (
            operon_data.groupby('genome_id')['present'].sum() == member_count
        ).astype(int)
    else:
        raise ValueError(f"method must be 'union' or 'intersection', got {method}")

    return operon_by_mag.reset_index().rename(
        columns={'present': 'operon_present'}
    )


def logistic_one_operon(
    ko_matrix: pd.DataFrame,
    operon_name: str,
    operon_kos: list[str],
    metal_col: str,
    method: str = 'union',
) -> dict:
    """Run logistic regression for one operon × metal pair.

    Model: operon_present ~ PF1_metal + latitude + sg_pH + log_genome_size + C(phylum)

    Returns dict with beta, SE, p_value, odds_ratio (for PF1_metal coefficient).
    """
    # Build per-MAG metadata
    mag_cols = [
        'genome_id', 'latitude', 'sg_pH', 'genome_size', 'phylum',
        metal_col
    ]
    all_mags = ko_matrix[mag_cols].drop_duplicates('genome_id').copy()
    all_mags['log_genome_size'] = np.log(all_mags['genome_size'].clip(lower=1e4))

    # Compute operon presence
    operon_presence = compute_operon_presence(ko_matrix, operon_kos, method=method)

    # Merge
    df = all_mags.merge(operon_presence, on='genome_id', how='left').dropna(
        subset=[metal_col, 'latitude', 'sg_pH']
    )
    df['operon_present'] = df['operon_present'].fillna(0).astype(int)

    n_present = df['operon_present'].sum()
    n_absent = (df['operon_present'] == 0).sum()

    if n_present < 5 or n_absent < 5:
        return {
            'operon': operon_name, 'metal': metal_col, 'method': method,
            'beta': np.nan, 'se': np.nan, 'p_value': np.nan,
            'odds_ratio': np.nan, 'n_present': int(n_present),
            'n_total': len(df), 'converged': False,
        }

    # Phylum filter: only groups with ≥2 MAGs and mix of present/absent
    if 'phylum' in df.columns and df['phylum'].notna().any():
        grp = df.groupby('phylum')['operon_present'].agg(['sum', 'count'])
        valid_groups = grp[
            (grp['sum'] >= 1) & (grp['count'] - grp['sum'] >= 1) & (grp['count'] >= 2)
        ].index
        df = df[df['phylum'].isin(valid_groups)].copy()
        if len(df) < 20:
            return {
                'operon': operon_name, 'metal': metal_col, 'method': method,
                'beta': np.nan, 'se': np.nan, 'p_value': np.nan,
                'odds_ratio': np.nan, 'n_present': int(n_present),
                'n_total': len(df), 'converged': False,
            }
        formula = f'operon_present ~ {metal_col} + latitude + sg_pH + log_genome_size + C(phylum)'
    else:
        formula = f'operon_present ~ {metal_col} + latitude + sg_pH + log_genome_size'

    try:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            model = logit(formula, data=df).fit(disp=False, maxiter=200)
        beta = model.params[metal_col]
        se = model.bse[metal_col]
        p = model.pvalues[metal_col]
        return {
            'operon': operon_name, 'metal': metal_col, 'method': method,
            'beta': float(beta), 'se': float(se), 'p_value': float(p),
            'odds_ratio': float(np.exp(beta)),
            'n_present': int(n_present), 'n_total': len(df),
            'converged': bool(model.mle_retvals.get('converged', True)),
        }
    except Exception as e:
        return {
            'operon': operon_name, 'metal': metal_col, 'method': method,
            'beta': np.nan, 'se': np.nan, 'p_value': np.nan,
            'odds_ratio': np.nan, 'n_present': int(n_present),
            'n_total': len(df), 'converged': False,
        }


def run_operon_analysis(
    ko_matrix: pd.DataFrame,
    output_path: Optional[Path] = None,
) -> pd.DataFrame:
    """Run logistic regressions for all operons × metals.

    Args:
        ko_matrix: SPIRE long-format KO matrix
        output_path: where to save results CSV

    Returns:
        DataFrame with results for all operon × metal pairs
    """
    results = []

    for operon_name, operon_kos in OPERONS.items():
        for metal in METALS:
            if metal not in ko_matrix.columns:
                continue

            # Try union method
            row_union = logistic_one_operon(
                ko_matrix, operon_name, operon_kos, metal, method='union'
            )
            results.append(row_union)

            # Try intersection method
            row_int = logistic_one_operon(
                ko_matrix, operon_name, operon_kos, metal, method='intersection'
            )
            results.append(row_int)

    results_df = pd.DataFrame(results)

    if output_path:
        results_df.to_csv(output_path, index=False)
        print(f"Results saved to {output_path}")

    return results_df


def compare_operon_to_members(
    operon_results: pd.DataFrame,
    ko_associations: pd.DataFrame,
    operon_name: str,
    operon_kos: list[str],
) -> pd.DataFrame:
    """Compare operon-level beta to individual member betas.

    Args:
        operon_results: output from run_operon_analysis
        ko_associations: baseline per-KO association results (spire_adj_ko_associations.csv)
        operon_name: name of operon (e.g., 'kdp')
        operon_kos: list of KO IDs in operon

    Returns:
        DataFrame comparing operon β and member βs for each metal
    """
    operon_subset = operon_results[
        (operon_results['operon'] == operon_name) &
        (operon_results['method'] == 'union')
    ]

    comparisons = []
    for _, opr_row in operon_subset.iterrows():
        metal = opr_row['metal']
        operon_beta = opr_row['beta']

        # Get member betas
        member_rows = ko_associations[
            (ko_associations['ko_id'].isin(operon_kos)) &
            (ko_associations['metal'] == metal)
        ][['ko_id', 'beta', 'q_value']]

        for _, mem_row in member_rows.iterrows():
            comparisons.append({
                'operon': operon_name,
                'metal': metal,
                'member_ko': mem_row['ko_id'],
                'operon_beta': operon_beta,
                'member_beta': mem_row['beta'],
                'member_q': mem_row['q_value'],
                'beta_delta': operon_beta - mem_row['beta'],
            })

    return pd.DataFrame(comparisons)


def main():
    """Execute operon-level aggregation analysis."""
    print("Loading SPIRE KO matrix...")
    ko_matrix = load_spire_ko_matrix()

    print("Running operon-level logistic regressions...")
    operon_results = run_operon_analysis(
        ko_matrix,
        output_path=DATA_DIR / 'operon_collapse_results.csv'
    )

    print(f"\nOperon analysis results: {len(operon_results)} rows")
    print("\nResults summary:")
    converged = operon_results['converged'].sum()
    total = len(operon_results)
    print(f"  Converged: {converged}/{total}")

    # Significance counts
    sig_threshold = 0.05
    sig_count = (operon_results['p_value'] < sig_threshold).sum()
    print(f"  Significant (p < {sig_threshold}): {sig_count}")

    # Summary by operon
    print("\nResults by operon:")
    for operon_name in OPERONS.keys():
        subset = operon_results[operon_results['operon'] == operon_name]
        print(f"\n  {operon_name}:")
        print(f"    Total tests: {len(subset)}")
        print(f"    Converged: {subset['converged'].sum()}")
        print(f"    Significant: {(subset['p_value'] < sig_threshold).sum()}")

        sig_rows = subset[subset['p_value'] < sig_threshold].sort_values('p_value')
        if len(sig_rows) > 0:
            print(f"    Top hits:")
            for _, row in sig_rows.head(3).iterrows():
                print(f"      {row['metal']}: β={row['beta']:.2f}, p={row['p_value']:.2e}")

    return operon_results


if __name__ == '__main__':
    results = main()

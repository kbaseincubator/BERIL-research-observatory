"""
robustness_rho_nmin.py
======================
Robustness check for ρ(λ, D) across minimum genome-count thresholds.

The manuscript reports Spearman ρ = -0.041 (p = 0.49) between Pagel's λ (genus-level)
and Fritz & Purvis D (genome-level) for 275 metal KOs. This script re-estimates λ at
thresholds n_min in [2, 5, 10, 20] to test whether the near-zero correlation reflects
estimation noise from sparse-genome genera.

Workflow:
1. Load λ and D per KO.
2. Load per-genus genome counts from genus_ko_presence and density files.
3. For each threshold, filter genera with ≥ n_min total genomes.
4. Re-estimate λ for each KO using only genera meeting the threshold.
5. Compute Spearman ρ(λ_threshold, D) and track classification changes.
"""

import os
os.environ['OMP_NUM_THREADS'] = '1'

import sys
import numpy as np
import pandas as pd
from scipy import stats
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))
from pgls_utils import load_tree, build_vcv, _optimise_lambda

# Paths
DATA_DIR = Path(__file__).parent.parent / "data"
SCRIPTS_DIR = Path(__file__).parent
RESULTS_DIR = Path(__file__).parent.parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

TREE_PATH = DATA_DIR / "gtdb_bac_genus_pruned.tree"
PHYLO_D_PATH = DATA_DIR / "fritz_purvis_D_genome.csv"
LAMBDA_PATH = DATA_DIR / "phylo_d_all_ko.csv"
PRESENCE_PATH = DATA_DIR / "genus_ko_presence_all_metal_275_kos.csv"  # Complete genus × KO matrix (241/275 KOs)
DENSITY_PATH = DATA_DIR / "01_genus_ko_density_spark.csv"

def load_and_prepare_data():
    """Load all required data files."""
    print("Loading data files...")

    # Load original lambda and D values
    lambda_df = pd.read_csv(LAMBDA_PATH)
    phylo_d = pd.read_csv(PHYLO_D_PATH)

    # Merge to get both lambda and D per KO
    ko_data = lambda_df.merge(phylo_d[['ko_id', 'D']], on='ko_id', how='inner')
    print(f"  KOs with both λ and D: {len(ko_data)}")

    # Load per-genus genome counts
    density = pd.read_csv(DENSITY_PATH)
    genus_genomes = density[['genus_lower', 'n_genomes']].drop_duplicates()
    print(f"  Unique genera in density file: {len(genus_genomes)}")

    # Load KO presence data (genus × KO) — using CSV which has correct genus naming
    print(f"  Loading presence matrix from {PRESENCE_PATH}...")
    presence = pd.read_csv(PRESENCE_PATH)  # CSV file (Tier 1+2 KOs with correct naming)
    print(f"  KO presence records: {len(presence)}")

    # Find overlap: which KOs have both lambda/D estimates AND presence data
    ko_in_data = set(ko_data['ko_id'].unique())
    ko_in_presence = set(presence['ko'].unique())
    overlap_kos = ko_in_data & ko_in_presence
    print(f"  KOs with presence data AND lambda/D estimates: {len(overlap_kos)}/{len(ko_in_data)}")

    # Filter ko_data to only include KOs we can re-estimate
    ko_data = ko_data[ko_data['ko_id'].isin(overlap_kos)].copy()

    missing_kos = ko_in_data - ko_in_presence
    if missing_kos:
        print(f"  Missing from presence (not in mgnify/SPIRE): {len(missing_kos)}")

    # Merge presence with total genome counts per genus
    presence = presence.merge(density[['genus_lower', 'n_genomes']], on='genus_lower', how='left')
    print(f"  Presence data merged with genome counts")

    return ko_data, genus_genomes, presence

def get_genus_ko_presence_fractions(ko_id, presence_df, genus_subset_set):
    """
    Get per-genus KO presence fractions for a given KO, filtered to genus_subset_set.

    Parameters:
    - ko_id: KEGG KO identifier
    - presence_df: dataframe with columns [genus_lower, ko, n_genomes_with_ko, n_genomes]
    - genus_subset_set: set of genus_lower values to include

    Returns:
        dict {genus_lower: fraction_with_ko}, or empty if KO has no data for subset
    """
    ko_data = presence_df[presence_df['ko'] == ko_id].copy()
    if len(ko_data) == 0:
        return {}

    ko_data = ko_data[ko_data['genus_lower'].isin(genus_subset_set)]
    if len(ko_data) == 0:
        return {}

    # Compute fractions (n_genomes already merged in from density file)
    ko_data['fraction'] = ko_data['n_genomes_with_ko'] / ko_data['n_genomes']

    return dict(zip(ko_data['genus_lower'], ko_data['fraction']))

def estimate_lambda_for_ko(ko_id, presence_df, filtered_genera_set, tree):
    """
    Re-estimate Pagel's λ for a KO using only genera in filtered_genera_set.

    Parameters:
    - ko_id: KEGG KO identifier
    - presence_df: dataframe with columns [genus_lower, ko, n_genomes_with_ko, n_genomes]
    - filtered_genera_set: set of genus_lower values to include
    - tree: dendropy Tree object

    Returns:
        float: lambda estimate, or np.nan if insufficient data
    """
    fractions = get_genus_ko_presence_fractions(ko_id, presence_df, filtered_genera_set)

    if len(fractions) < 10:  # Need at least 10 genera for reasonable PGLS
        return np.nan

    # Prepare taxa list and check which ones are in the tree
    taxa_list = list(fractions.keys())
    tree_labels = {t.label.replace(" ", "_").lower() for t in tree.taxon_namespace}
    normalised_taxa = [t.replace(" ", "_").lower() for t in taxa_list]

    # Filter to only taxa in the tree
    in_tree_idx = [i for i, t in enumerate(normalised_taxa) if t in tree_labels]

    if len(in_tree_idx) < 10:  # Need at least 10 genera after tree filtering
        return np.nan

    # Build lists of y values and taxa that are in the tree
    filtered_taxa = [taxa_list[i] for i in in_tree_idx]
    y = np.array([fractions[t] for t in filtered_taxa])

    # Dummy X: just an intercept (we're estimating λ via univariate PGLS)
    X = np.ones((len(y), 1))

    # Build VCV for filtered taxa
    try:
        V = build_vcv(tree, filtered_taxa)
    except Exception as e:
        # Should not happen after we've already filtered to tree membership
        return np.nan

    # Optimize lambda
    try:
        lam, ll = _optimise_lambda(y, X, V)
        return float(lam)
    except Exception as e:
        return np.nan

def main():
    """Run robustness check."""
    print("=" * 70)
    print("Robustness check: ρ(λ, D) across minimum genome-count thresholds")
    print("=" * 70)

    # Load data
    ko_data, genus_genomes, presence = load_and_prepare_data()

    # Load tree once
    print(f"\nLoading tree from {TREE_PATH}...")
    tree = load_tree(TREE_PATH)
    print(f"  Tree loaded with {len(tree.taxon_namespace)} taxa")

    # Thresholds to test
    thresholds = [2, 5, 10, 20]
    results = []

    for n_min in thresholds:
        print(f"\n{'='*70}")
        print(f"Threshold: n_min = {n_min}")
        print(f"{'='*70}")

        # Filter genera with >= n_min genomes
        filtered_genera = genus_genomes[genus_genomes['n_genomes'] >= n_min].copy()
        filtered_genera_set = set(filtered_genera['genus_lower'].values)
        n_genera_retained = len(filtered_genera)
        print(f"Genera with ≥ {n_min} genomes: {n_genera_retained}")

        # Re-estimate λ for each KO
        print(f"Re-estimating λ for {len(ko_data)} KOs...")
        lambda_threshold = []
        valid_kos = []

        for idx, row in ko_data.iterrows():
            ko_id = row['ko_id']

            lam_new = estimate_lambda_for_ko(ko_id, presence, filtered_genera_set, tree)
            if not np.isnan(lam_new):
                lambda_threshold.append(lam_new)
                valid_kos.append(ko_id)

            if (idx + 1) % 50 == 0:
                print(f"  Processed {idx + 1}/{len(ko_data)} KOs ({len(valid_kos)} valid)")

        print(f"  Valid KOs with ≥10 genera: {len(valid_kos)}")

        if len(valid_kos) < 10:
            print(f"  WARNING: Only {len(valid_kos)} valid KOs; skipping this threshold")
            continue

        # Get corresponding D values (in same order as lambda_threshold)
        ko_data_valid = ko_data[ko_data['ko_id'].isin(valid_kos)].set_index('ko_id')
        d_values = np.array([ko_data_valid.loc[ko_id, 'D'] for ko_id in valid_kos])
        lambda_values = np.array(lambda_threshold)

        # Compute Spearman ρ
        rho, p_value = stats.spearmanr(lambda_values, d_values)
        print(f"\nSpearman ρ(λ_threshold, D): {rho:.4f} (p = {p_value:.4f})")

        # Track classification changes
        # "Double signal" typically defined as λ < 0.3 AND D < 0.3
        original_double_signal = np.array(
            [ko_data_valid.loc[ko_id, 'lambda'] < 0.3 and ko_data_valid.loc[ko_id, 'D'] < 0.3
             for ko_id in valid_kos]
        )
        threshold_double_signal = (lambda_values < 0.3) & (d_values < 0.3)
        n_classification_changes = np.sum(original_double_signal != threshold_double_signal)
        print(f"KOs changing double-signal classification (λ < 0.3): {n_classification_changes}")

        # Store result
        results.append({
            'n_min': n_min,
            'n_genera_retained': n_genera_retained,
            'n_kos_with_data': len(valid_kos),
            'rho': round(rho, 4),
            'p_value': round(p_value, 4),
            'n_classification_changes': n_classification_changes,
        })

    # Create results dataframe and save
    if results:
        results_df = pd.DataFrame(results)
        output_path = RESULTS_DIR / "robustness_rho_nmin.csv"
        results_df.to_csv(output_path, index=False)

        print(f"\n{'='*70}")
        print("RESULTS SUMMARY")
        print(f"{'='*70}")
        print(results_df.to_string(index=False))
        print(f"\nResults saved to: {output_path}")

        # Assess stability
        rho_values = results_df['rho'].values
        rho_range = rho_values.max() - rho_values.min()
        print(f"\nρ range across thresholds: {rho_range:.4f}")
        if rho_range < 0.05:
            stability = "STABLE"
        elif rho_range < 0.1:
            stability = "MODERATELY STABLE"
        else:
            stability = "UNSTABLE"
        print(f"Stability assessment: {stability}")

        print(f"\nSM13 summary: ρ(λ_genus, D_genome) remained {stability} across minimum genome-count")
        print(f"thresholds (ρ_range = {rho_range:.4f}), with ρ ranging from {rho_values.min():.4f} to {rho_values.max():.4f}.")
    else:
        print("\nNo valid results to report.")

if __name__ == "__main__":
    main()

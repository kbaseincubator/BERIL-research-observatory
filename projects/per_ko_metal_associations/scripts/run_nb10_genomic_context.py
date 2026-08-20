"""NB10 — Genomic context of field vs lab KOs.

Tests:
  Q1-proxy: Prevalence as proxy for core/accessory genome partitioning.
             Fritz & Purvis' D for the small intersection with phylo_d data.
  Q2: Co-occurrence partners — what KOs most frequently co-occur with field
      vs lab KOs? Are field partners more vs less prevalent?
  Q3: HGT marker co-occurrence — do field or lab KOs show higher Jaccard
      similarity with known transposase/integrase KOs?

All analyses use the 8,585-MAG MGnify binary KO matrix.

Usage:
    python scripts/run_nb10_genomic_context.py
"""

from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / 'data'

# ── HGT marker KOs (transposases/integrases with <50% MAG prevalence) ────────
# High-prevalence "integrases" like XerC (K03733, 93%) are housekeeping;
# excluded here. Integron intI (K01356, 86%) is also too universal to be an
# HGT marker in this dataset. We use the clearly mobile-element-associated KOs.
HGT_KORE_SET = {
    'K07477',  # transposase Tn3/MuA family        (3.6%)
    'K07480',  # transposase TnpA (Tn7)            (8.8%)
    'K07482',  # transposase IS30                  (5.9%)
    'K07483',  # transposase IS3 family            (42.2%)
    'K07484',  # transposase IS4 family            (26.5%)
    'K07485',  # transposase IS1                   (5.6%)
    'K07487',  # transposase IS256/IS630           (9.5%)
    'K07491',  # transposase IS5                   (43.5%)
    'K07741',  # phage integrase                   (2.4%)
    'K07742',  # resolvase (site-specific)         (26.9%)
    'K06400',  # serine recombinase (integrase)    (23.1%)
}

# Constitutive housekeeping proxy: KOs with prevalence > 85% of MAGs.
# These are the "essential core" in this dataset.
CORE_PREVALENCE_THRESHOLD = 0.85


def load_binary_matrix(path: Path) -> tuple[np.ndarray, list, list]:
    """Load MGnify KO matrix and return (binary ndarray, MAG list, KO list)."""
    print("Loading MGnify matrix ...")
    mat = pd.read_parquet(path, columns=['genome_id', 'ko_id'])
    mags = sorted(mat['genome_id'].unique())
    kos = sorted(mat['ko_id'].unique())
    mag_idx = {m: i for i, m in enumerate(mags)}
    ko_idx  = {k: i for i, k in enumerate(kos)}

    rows = [mag_idx[m] for m in mat['genome_id']]
    cols = [ko_idx[k] for k in mat['ko_id']]
    B = np.zeros((len(mags), len(kos)), dtype=np.bool_)
    B[rows, cols] = True
    print(f"Binary matrix: {B.shape[0]:,} MAGs × {B.shape[1]:,} KOs  "
          f"({B.sum():,} presences, {100*B.mean():.1f}% fill)")
    return B, mags, kos


def jaccard_one_vs_all(focal_vec: np.ndarray, B: np.ndarray) -> np.ndarray:
    """Jaccard of one focal binary vector (shape: n_mags,) against every KO column."""
    inter = (focal_vec[:, None] & B).sum(axis=0)          # shape: n_kos
    union = (focal_vec[:, None] | B).sum(axis=0)
    with np.errstate(invalid='ignore'):
        J = np.where(union == 0, 0.0, inter / union)
    return J


def jaccard_group_vs_all(focal_cols: np.ndarray, B: np.ndarray,
                          focal_ko_indices: set) -> pd.Series:
    """Mean Jaccard of a group of focal KOs against every KO column.

    focal_cols: B[:, focal_ko_indices] — only the focal columns.
    Returns a Series indexed by position in B's column axis.
    """
    n_kos = B.shape[1]
    J_sum = np.zeros(n_kos, dtype=np.float64)
    for col in focal_cols.T:
        J_sum += jaccard_one_vs_all(col, B)
    J_mean = J_sum / focal_cols.shape[1]
    return J_mean


def main():
    # ── Load data ────────────────────────────────────────────────────────────
    B, mags, kos = load_binary_matrix(DATA_DIR / 'mgnify_all_ko_matrix.parquet')
    ko_to_idx = {k: i for i, k in enumerate(kos)}
    n_mags = len(mags)

    # Prevalence for every KO
    prev = B.sum(axis=0)  # shape: n_kos

    robust = pd.read_csv(DATA_DIR / 'h1_robustness_summary.csv')
    lab_df = pd.read_csv(DATA_DIR / 'top_lab_ko_arc4_prevalence.csv')

    field_kos = set(robust[robust['survives_all_controls']]['ko_id'].unique())
    lab_kos   = set(lab_df['ko_id'].unique())

    # Filter to KOs present in MGnify matrix
    field_kos = field_kos & set(kos)
    lab_kos   = lab_kos   & set(kos)
    print(f"Field KOs in matrix: {len(field_kos)}")
    print(f"Lab KOs in matrix:   {len(lab_kos)}")

    field_idx = [ko_to_idx[k] for k in sorted(field_kos)]
    lab_idx   = [ko_to_idx[k] for k in sorted(lab_kos)]

    # ── Q1-proxy: Prevalence as core/accessory proxy ─────────────────────────
    print("\n=== Q1-proxy: Prevalence ===")
    field_prev = prev[field_idx]
    lab_prev   = prev[lab_idx]
    all_prev   = prev

    print(f"Field KOs:  mean {field_prev.mean():.0f} ({100*field_prev.mean()/n_mags:.1f}%)  "
          f"median {np.median(field_prev):.0f} ({100*np.median(field_prev)/n_mags:.1f}%)")
    print(f"Lab KOs:    mean {lab_prev.mean():.0f} ({100*lab_prev.mean()/n_mags:.1f}%)  "
          f"median {np.median(lab_prev):.0f} ({100*np.median(lab_prev)/n_mags:.1f}%)")
    print(f"All KOs:    mean {all_prev.mean():.0f} ({100*all_prev.mean()/n_mags:.1f}%)")

    u, p = stats.mannwhitneyu(field_prev, lab_prev, alternative='two-sided')
    print(f"Mann-Whitney U (field vs lab prevalence): U={u:.0f}, p={p:.2e}")

    # Field KOs with phylo-D data
    phylo_d = pd.read_csv(
        '/home/hmacgregor/BERIL-research-observatory/projects/'
        'comprehensive_metal_ecology/data/phylo_d_all_ko.csv'
    )
    field_d = phylo_d[phylo_d['ko_id'].isin(field_kos)]
    lab_d   = phylo_d[phylo_d['ko_id'].isin(lab_kos)]
    print(f"\nField KOs with phylo-D data: {len(field_d)}")
    if len(field_d):
        print(field_d[['ko_id','gene_name','lambda','n_genera']].to_string(index=False))
    print(f"\nLab KOs with phylo-D data: {len(lab_d)}")
    if len(lab_d):
        print(lab_d[['ko_id','gene_name','lambda','n_genera']].to_string(index=False))

    # ── Q2: Co-occurrence partners ────────────────────────────────────────────
    print("\n=== Q2: Co-occurrence partners ===")
    print("Computing mean Jaccard for field KOs vs all KOs ...")
    field_B = B[:, field_idx]
    J_field = jaccard_group_vs_all(field_B, B, set(field_idx))

    print("Computing mean Jaccard for lab KOs vs all KOs ...")
    lab_B = B[:, lab_idx]
    J_lab = jaccard_group_vs_all(lab_B, B, set(lab_idx))

    # Exclude focal KOs from partner ranking
    all_ko_arr = np.array(kos)
    field_mask = np.array([i not in set(field_idx) for i in range(len(kos))])
    lab_mask   = np.array([i not in set(lab_idx)   for i in range(len(kos))])

    # Top 20 partners for field KOs
    J_field_ext = J_field.copy(); J_field_ext[~field_mask] = -1
    top_field_idx = np.argsort(J_field_ext)[::-1][:30]
    top_field = pd.DataFrame({
        'ko_id': all_ko_arr[top_field_idx],
        'mean_J_field': J_field[top_field_idx],
        'prevalence': prev[top_field_idx],
        'prev_pct': 100 * prev[top_field_idx] / n_mags,
        'is_hgt_marker': [all_ko_arr[i] in HGT_KORE_SET for i in top_field_idx],
        'is_core': [prev[i] >= CORE_PREVALENCE_THRESHOLD * n_mags for i in top_field_idx],
    })
    print("\nTop 30 Jaccard partners for FIELD KOs:")
    print(top_field.to_string(index=False))

    # Top 20 partners for lab KOs
    J_lab_ext = J_lab.copy(); J_lab_ext[~lab_mask] = -1
    top_lab_idx = np.argsort(J_lab_ext)[::-1][:30]
    top_lab = pd.DataFrame({
        'ko_id': all_ko_arr[top_lab_idx],
        'mean_J_lab': J_lab[top_lab_idx],
        'prevalence': prev[top_lab_idx],
        'prev_pct': 100 * prev[top_lab_idx] / n_mags,
        'is_hgt_marker': [all_ko_arr[i] in HGT_KORE_SET for i in top_lab_idx],
        'is_core': [prev[i] >= CORE_PREVALENCE_THRESHOLD * n_mags for i in top_lab_idx],
    })
    print("\nTop 30 Jaccard partners for LAB KOs:")
    print(top_lab.to_string(index=False))

    # Prevalence of top partners — does field prefer low-prev partners (accessory)?
    print(f"\nField top-30 partner prevalence: mean={top_field['prev_pct'].mean():.1f}%  "
          f"core: {top_field['is_core'].sum()}/30")
    print(f"Lab top-30 partner prevalence: mean={top_lab['prev_pct'].mean():.1f}%  "
          f"core: {top_lab['is_core'].sum()}/30")

    # ── Q3: HGT marker co-occurrence ─────────────────────────────────────────
    print("\n=== Q3: HGT marker co-occurrence ===")
    hgt_in_matrix = [k for k in HGT_KORE_SET if k in ko_to_idx]
    print(f"HGT markers in matrix: {len(hgt_in_matrix)}")

    hgt_rows = []
    for hgt_ko in sorted(hgt_in_matrix):
        hgt_vec = B[:, ko_to_idx[hgt_ko]]
        hgt_prev = hgt_vec.sum()

        # Jaccard of this HGT marker with each field / lab KO
        J_field_ko = np.array([
            jaccard_one_vs_all(hgt_vec, B[:, [i]])[0]
            for i in field_idx
        ])
        J_lab_ko = np.array([
            jaccard_one_vs_all(hgt_vec, B[:, [i]])[0]
            for i in lab_idx
        ])
        hgt_rows.append({
            'hgt_ko': hgt_ko,
            'hgt_prev': hgt_prev,
            'hgt_prev_pct': 100 * hgt_prev / n_mags,
            'J_field_mean': J_field_ko.mean(),
            'J_field_median': np.median(J_field_ko),
            'J_lab_mean': J_lab_ko.mean(),
            'J_lab_median': np.median(J_lab_ko),
            'ratio_field_lab': J_field_ko.mean() / max(J_lab_ko.mean(), 1e-9),
        })

    hgt_df = pd.DataFrame(hgt_rows).sort_values('ratio_field_lab', ascending=False)
    print("\nHGT marker Jaccard (field vs lab KOs):")
    print(hgt_df.to_string(index=False))

    # Summary comparison
    field_mean = hgt_df['J_field_mean'].mean()
    lab_mean = hgt_df['J_lab_mean'].mean()
    print(f"\nMean J(HGT markers, field KOs): {field_mean:.4f}")
    print(f"Mean J(HGT markers, lab KOs):   {lab_mean:.4f}")
    print(f"Ratio field/lab: {field_mean/lab_mean:.2f}x")

    # Save outputs
    top_field.to_csv(DATA_DIR / 'nb10_field_ko_top_partners.csv', index=False)
    top_lab.to_csv(DATA_DIR / 'nb10_lab_ko_top_partners.csv', index=False)
    hgt_df.to_csv(DATA_DIR / 'nb10_hgt_marker_jaccard.csv', index=False)

    # Also save full J_field and J_lab for all KOs
    jaccard_all = pd.DataFrame({
        'ko_id': kos,
        'prevalence': prev,
        'prev_pct': 100 * prev / n_mags,
        'J_field_mean': J_field,
        'J_lab_mean': J_lab,
        'is_field_focal': [k in field_kos for k in kos],
        'is_lab_focal': [k in lab_kos for k in kos],
        'is_hgt_marker': [k in HGT_KORE_SET for k in kos],
        'is_core': [prev[i] >= CORE_PREVALENCE_THRESHOLD * n_mags for i, k in enumerate(kos)],
    })
    jaccard_all.to_parquet(DATA_DIR / 'nb10_jaccard_all_kos.parquet', index=False)
    print(f"\nSaved: nb10_field_ko_top_partners.csv, nb10_lab_ko_top_partners.csv, "
          f"nb10_hgt_marker_jaccard.csv, nb10_jaccard_all_kos.parquet")


if __name__ == '__main__':
    main()

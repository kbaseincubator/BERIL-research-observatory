"""NB10 expanded — HGT O/E and co-occurrence partner analysis across KO set thresholds.

Runs the same Q2/Q3 analyses as NB10 but for all field and lab KO threshold levels:

Field sets:
  - all-4-controls (84 unique KOs)
  - class-robust   (100 unique KOs)
  - lat-adj        (122 unique KOs)
  - all-H1-sig     (169 unique KOs)

Lab sets:
  - top-96         (96 KOs from Arc2)
  - strong-fit     (191 KOs, min_t < -4)
  - any-hit        (197 KOs, mean_t < -2)

Usage:
    python scripts/run_nb10_expanded.py > data/nb10_expanded_output.txt 2>&1
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / 'data'

HGT_KO_SET = {
    'K07477', 'K07480', 'K07482', 'K07483', 'K07484',
    'K07485', 'K07487', 'K07491', 'K07741', 'K07742', 'K06400',
}
CORE_THRESHOLD = 0.85
N_TOP_PARTNERS = 30


def load_binary_matrix(path: Path):
    print("Loading MGnify binary matrix ...", flush=True)
    mat = pd.read_parquet(path, columns=['genome_id', 'ko_id'])
    mags = sorted(mat['genome_id'].unique())
    kos  = sorted(mat['ko_id'].unique())
    mag_idx = {m: i for i, m in enumerate(mags)}
    ko_idx  = {k: i for i, k in enumerate(kos)}
    rows = [mag_idx[m] for m in mat['genome_id']]
    cols = [ko_idx[k]  for k in mat['ko_id']]
    B = np.zeros((len(mags), len(kos)), dtype=np.bool_)
    B[rows, cols] = True
    print(f"  {B.shape[0]:,} MAGs × {B.shape[1]:,} KOs  ({B.sum():,} presences)", flush=True)
    return B, mags, kos


def jaccard_one_vs_all(focal: np.ndarray, B: np.ndarray) -> np.ndarray:
    inter = (focal[:, None] & B).sum(axis=0)
    union = (focal[:, None] | B).sum(axis=0)
    with np.errstate(invalid='ignore'):
        return np.where(union == 0, 0.0, inter / union)


def mean_jaccard_group(focal_idx: list, B: np.ndarray) -> np.ndarray:
    J = np.zeros(B.shape[1], dtype=np.float64)
    for i in focal_idx:
        J += jaccard_one_vs_all(B[:, i], B)
    return J / max(len(focal_idx), 1)


def hgt_oe(focal_idx: list, hgt_idx: list, B: np.ndarray, n_mags: int,
           prev: np.ndarray) -> tuple[float, float]:
    """Return (mean_J_obs, mean_OE) of focal set vs all HGT markers."""
    if not focal_idx or not hgt_idx:
        return np.nan, np.nan
    focal_prevs = prev[focal_idx] / n_mags
    J_obs_list, OE_list = [], []
    for hi in hgt_idx:
        p_hgt = prev[hi] / n_mags
        J_per_focal = jaccard_one_vs_all(B[:, hi], B[:, focal_idx])  # shape: n_focal
        J_obs = J_per_focal.mean()
        E_per_focal = (p_hgt * focal_prevs) / (p_hgt + focal_prevs - p_hgt * focal_prevs)
        J_exp = E_per_focal.mean()
        J_obs_list.append(J_obs)
        OE_list.append(J_obs / J_exp if J_exp > 0 else np.nan)
    return np.mean(J_obs_list), np.nanmean(OE_list)


def partner_prevalence(focal_idx: list, B: np.ndarray, prev: np.ndarray,
                       n_mags: int, exclude_idx: set) -> dict:
    """Return stats on top-N Jaccard partners (excluding focal set itself)."""
    J_mean = mean_jaccard_group(focal_idx, B)
    J_ext = J_mean.copy()
    for i in exclude_idx:
        J_ext[i] = -1
    top_idx = np.argsort(J_ext)[::-1][:N_TOP_PARTNERS]
    top_prev_pct = prev[top_idx] / n_mags * 100
    core_mask = prev[top_idx] >= CORE_THRESHOLD * n_mags
    return {
        'partner_mean_prev_pct': top_prev_pct.mean(),
        'partner_median_prev_pct': np.median(top_prev_pct),
        'core_fraction': core_mask.mean(),
        'n_core': core_mask.sum(),
    }


def main():
    B, mags, kos = load_binary_matrix(DATA_DIR / 'mgnify_all_ko_matrix.parquet')
    ko_to_idx = {k: i for i, k in enumerate(kos)}
    kos_set = set(kos)
    n_mags = len(mags)
    prev = B.sum(axis=0)

    # HGT marker indices
    hgt_idx = [ko_to_idx[k] for k in HGT_KO_SET if k in ko_to_idx]
    print(f"HGT markers in matrix: {len(hgt_idx)}", flush=True)

    # ── Define field KO sets ─────────────────────────────────────────────────
    rob = pd.read_csv(DATA_DIR / 'h1_robustness_summary.csv')
    field_sets = {
        'all-4-controls': set(rob[rob['survives_all_controls']]['ko_id'].unique()) & kos_set,
        'class-robust':   set(rob[rob['survives_p4_class']]['ko_id'].unique()) & kos_set,
        'lat-adj':        set(rob[rob['survives_h4_latitude']]['ko_id'].unique()) & kos_set,
        'all-H1-sig':     set(rob['ko_id'].unique()) & kos_set,
    }

    # ── Define lab KO sets ───────────────────────────────────────────────────
    top_lab = pd.read_csv(DATA_DIR / 'top_lab_ko_arc4_prevalence.csv')
    hits    = pd.read_csv(DATA_DIR / 'all_ko_fitness_hits.csv')
    lab_sets = {
        'top-96':      set(top_lab['ko_id'].unique()) & kos_set,
        'strong-fit':  set(hits[hits['is_strong_hit']]['ko_id'].unique()) & kos_set,
        'any-hit':     set(hits['ko_id'].unique()) & kos_set,
    }

    # ── Collect results ──────────────────────────────────────────────────────
    records = []

    for fl, fkos in field_sets.items():
        fidx = [ko_to_idx[k] for k in fkos]
        fset = set(fidx)
        f_prev = prev[fidx] / n_mags * 100
        print(f"\n--- Field: {fl} (n={len(fkos)}) ---", flush=True)

        # HGT O/E for field
        f_j_obs, f_oe = hgt_oe(fidx, hgt_idx, B, n_mags, prev)
        print(f"  HGT J_obs={f_j_obs:.4f}  O/E={f_oe:.3f}", flush=True)

        # Partner prevalence for field
        fpart = partner_prevalence(fidx, B, prev, n_mags, fset)
        print(f"  Partners: mean_prev={fpart['partner_mean_prev_pct']:.1f}%  core={fpart['n_core']}/{N_TOP_PARTNERS}", flush=True)

        for ll, lkos in lab_sets.items():
            lidx = [ko_to_idx[k] for k in lkos]
            lset = set(lidx)
            l_prev = prev[lidx] / n_mags * 100

            # Prevalence comparison
            _, p_prev = stats.mannwhitneyu(f_prev, l_prev, alternative='two-sided')

            # HGT O/E for lab
            l_j_obs, l_oe = hgt_oe(lidx, hgt_idx, B, n_mags, prev)

            # Partner prevalence for lab
            lpart = partner_prevalence(lidx, B, prev, n_mags, lset)

            records.append({
                'field_set': fl,
                'n_field': len(fkos),
                'lab_set': ll,
                'n_lab': len(lkos),
                'field_prev_mean': f_prev.mean(),
                'field_prev_median': np.median(f_prev),
                'lab_prev_mean': l_prev.mean(),
                'lab_prev_median': np.median(l_prev),
                'p_prev_mw': p_prev,
                'field_hgt_J': f_j_obs,
                'field_hgt_OE': f_oe,
                'lab_hgt_J': l_j_obs,
                'lab_hgt_OE': l_oe,
                'field_partner_prev': fpart['partner_mean_prev_pct'],
                'field_partner_core_n': fpart['n_core'],
                'lab_partner_prev': lpart['partner_mean_prev_pct'],
                'lab_partner_core_n': lpart['n_core'],
            })
            print(f"  vs {ll} (n={len(lkos)}): p_prev={p_prev:.2e}  lab HGT J={l_j_obs:.4f} O/E={l_oe:.3f}", flush=True)

    df = pd.DataFrame(records)
    out = DATA_DIR / 'nb10_expanded_results.csv'
    df.to_csv(out, index=False)
    print(f"\n\n{'='*70}")
    print("SUMMARY TABLE")
    print('='*70)
    print(df[['field_set','n_field','lab_set','n_lab',
              'field_prev_median','lab_prev_median','p_prev_mw',
              'field_hgt_OE','lab_hgt_OE',
              'field_partner_prev','field_partner_core_n',
              'lab_partner_prev','lab_partner_core_n']].to_string(index=False))
    print(f"\nSaved: {out}")


if __name__ == '__main__':
    main()

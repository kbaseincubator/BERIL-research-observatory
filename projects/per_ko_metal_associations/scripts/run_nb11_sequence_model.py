"""NB11 — Sequence-feature model: do field KOs look like metal-fitness genes?

Arc 6 showed amino acid composition predicts metal fitness (AUC 0.56–0.77).
This notebook trains a Random Forest classifier on RB-TnSeq fitness data
(label = metal fitness hit) using protein sequence features, then applies
it to field-identified KOs.

Hypothesis: field KOs will have lower predicted metal-fitness probability
than lab fitness genes. Alternative: field KOs have high predicted fitness
(matching lab-fitness sequence features) but fail in lab conditions —
suggesting a context-dependence rather than a sequence-level mismatch.

Key confound: lab genes are near-core (65% prevalence); field KOs are rare
(5%). KEGG representative sequences may be from model organisms (E. coli,
B. subtilis) rather than soil specialists. Both effects are flagged.

Usage:
    python scripts/run_nb11_sequence_model.py > data/nb11_output.txt 2>&1
"""
from __future__ import annotations
import sys
import time
import json
import pickle
import warnings
from pathlib import Path
from collections import Counter

import numpy as np
import pandas as pd
from scipy import stats
import requests

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR    = PROJECT_DIR / 'data'
CACHE_FILE  = DATA_DIR / 'nb11_kegg_seq_cache.json'

# ── KEGG sequence cache (avoid re-fetching) ──────────────────────────────────
def load_cache() -> dict:
    if CACHE_FILE.exists():
        with open(CACHE_FILE) as f:
            return json.load(f)
    return {}


def save_cache(cache: dict) -> None:
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f)


def fetch_kegg_sequence(ko_id: str, cache: dict, delay: float = 0.35) -> str | None:
    """Return a representative protein sequence for a KO via two-step KEGG REST.

    Step 1: GET /link/genes/{ko_id}  → resolve KO to one or more gene IDs.
    Step 2: GET /get/{gene_id}/aaseq → fetch amino acid sequence for first gene.

    Direct /get/{ko_id}/aaseq returns nothing for KO-level IDs.
    Result is cached to avoid redundant API calls.
    """
    if ko_id in cache:
        return cache[ko_id]

    # Step 1 — resolve KO → gene IDs
    try:
        r1 = requests.get(f'https://rest.kegg.jp/link/genes/{ko_id}', timeout=20)
        time.sleep(delay)
        if r1.status_code != 200 or not r1.text.strip():
            cache[ko_id] = None
            return None
        genes = [ln.split('\t')[1] for ln in r1.text.strip().split('\n')
                 if '\t' in ln]
        if not genes:
            cache[ko_id] = None
            return None
    except Exception:
        cache[ko_id] = None
        return None

    # Prefer model-organism genes (Proteobacteria / Firmicutes) for consistency
    # with the lab fitness data (mostly gram-negative soil organisms).
    # Fallback: just take the first gene.
    preferred = [g for g in genes if g.split(':')[0] in
                 {'eco', 'sce', 'bsu', 'pae', 'cgl', 'dvu', 'cau', 'hpy'}]
    gene_id = preferred[0] if preferred else genes[0]

    # Step 2 — fetch amino acid sequence for chosen gene
    try:
        r2 = requests.get(f'https://rest.kegg.jp/get/{gene_id}/aaseq', timeout=20)
        time.sleep(delay)
        if r2.status_code != 200 or not r2.text.strip():
            cache[ko_id] = None
            return None
        seq = ''
        for line in r2.text.strip().split('\n'):
            if line.startswith('>'):
                if seq:
                    break
            else:
                seq += line.strip().upper()
        result = seq if len(seq) >= 10 else None
    except Exception:
        result = None

    cache[ko_id] = result
    return result


# ── Sequence features ────────────────────────────────────────────────────────
AMINO_ACIDS = list('ACDEFGHIKLMNPQRSTVWY')

# Kyte-Doolittle hydrophobicity scale (for GRAVY)
KD_SCALE = {
    'A':  1.8, 'R': -4.5, 'N': -3.5, 'D': -3.5, 'C':  2.5,
    'Q': -3.5, 'E': -3.5, 'G': -0.4, 'H': -3.2, 'I':  4.5,
    'L':  3.8, 'K': -3.9, 'M':  1.9, 'F':  2.8, 'P': -1.6,
    'S': -0.8, 'T': -0.7, 'W': -0.9, 'Y': -1.3, 'V':  4.2,
}

# Charge at pH 7: R, K, H(partial) positive; D, E negative; C, Y partial
CHARGE_SCALE = {
    'R':  1.0, 'K':  1.0, 'H':  0.1,
    'D': -1.0, 'E': -1.0,
    'C': -0.05, 'Y': -0.05,
}

def compute_features(seq: str) -> dict | None:
    if not seq or len(seq) < 10:
        return None
    seq = seq.upper()
    n = len(seq)
    counts = Counter(seq)
    total_std = sum(counts.get(aa, 0) for aa in AMINO_ACIDS)
    if total_std == 0:
        return None

    feats = {}
    for aa in AMINO_ACIDS:
        feats[f'aa_{aa}'] = counts.get(aa, 0) / n

    feats['length_log'] = np.log1p(n)
    feats['gravy'] = sum(KD_SCALE.get(aa, 0) * counts.get(aa, 0) for aa in AMINO_ACIDS) / n
    feats['net_charge'] = sum(CHARGE_SCALE.get(aa, 0) * counts.get(aa, 0) for aa in AMINO_ACIDS) / n
    feats['cys_frac'] = counts.get('C', 0) / n
    feats['aromatic_frac'] = (counts.get('F', 0) + counts.get('W', 0) + counts.get('Y', 0)) / n
    feats['polar_frac'] = sum(counts.get(aa, 0) for aa in 'STNQ') / n
    feats['charged_frac'] = sum(counts.get(aa, 0) for aa in 'RKHDE') / n
    feats['small_frac'] = sum(counts.get(aa, 0) for aa in 'GASP') / n
    return feats


FEATURE_COLS = (
    [f'aa_{aa}' for aa in AMINO_ACIDS]
    + ['length_log', 'gravy', 'net_charge', 'cys_frac',
       'aromatic_frac', 'polar_frac', 'charged_frac', 'small_frac']
)


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import StratifiedKFold, cross_val_predict
    from sklearn.pipeline import Pipeline
    from sklearn.calibration import CalibratedClassifierCV

    # ── Load KO sets ─────────────────────────────────────────────────────────
    hits    = pd.read_csv(DATA_DIR / 'all_ko_fitness_hits.csv')
    rob     = pd.read_csv(DATA_DIR / 'h1_robustness_summary.csv')
    top_lab = pd.read_csv(DATA_DIR / 'top_lab_ko_arc4_prevalence.csv')
    jac     = pd.read_parquet(DATA_DIR / 'nb10_jaccard_all_kos.parquet')

    prev_map = dict(zip(jac['ko_id'], jac['prevalence'] / 8585 * 100))

    # Positive training set: strong metal-fitness hits (min_t < -4)
    pos_kos = set(hits[hits['is_strong_hit']]['ko_id'].unique())
    # Negative training set: all tested KOs (in raw parquet) that are NOT hits
    # and have per-KO mean |t| < 1 (clearly neutral across all conditions tested)
    raw = pd.read_parquet(DATA_DIR / 'all_ko_fitness_raw.parquet')
    ko_mean_t = raw.groupby('ko_id')['t_stat'].mean()
    all_tested_kos = set(raw['ko_id'].unique())
    neg_kos = {k for k in all_tested_kos if k not in pos_kos and abs(ko_mean_t.get(k, 0)) < 1.0}

    # Field KO sets (multiple levels)
    field_strict = set(rob[rob['survives_all_controls']]['ko_id'].unique())
    field_loose  = set(rob['ko_id'].unique())

    # Lab top-96 (Arc2 strict)
    lab_top96 = set(top_lab['ko_id'].unique())

    print(f"Positive (strong lab hits): {len(pos_kos)}")
    print(f"Negative (neutral, mean_t>-0.5): {len(neg_kos)}")
    print(f"Field strict (all-4-controls): {len(field_strict)}")
    print(f"Field loose (all-H1-sig): {len(field_loose)}")
    print(f"Lab top-96: {len(lab_top96)}", flush=True)

    # All KOs to fetch sequences for
    all_kos = pos_kos | neg_kos | field_strict | field_loose | lab_top96
    print(f"\nTotal unique KOs needing sequences: {len(all_kos)}", flush=True)

    # ── Fetch KEGG sequences ─────────────────────────────────────────────────
    cache = load_cache()
    already_cached = sum(1 for k in all_kos if k in cache)
    to_fetch = [k for k in sorted(all_kos) if k not in cache]
    print(f"Cached: {already_cached}  To fetch: {len(to_fetch)}", flush=True)

    for i, ko in enumerate(to_fetch):
        fetch_kegg_sequence(ko, cache)
        if (i + 1) % 50 == 0:
            save_cache(cache)
            print(f"  Fetched {i+1}/{len(to_fetch)} ... ({len(to_fetch)-i-1} remaining)", flush=True)

    save_cache(cache)
    print("All sequences fetched.", flush=True)

    # ── Compute features ─────────────────────────────────────────────────────
    ko_feats = {}
    for ko in all_kos:
        seq = cache.get(ko)
        feats = compute_features(seq) if seq else None
        if feats is not None:
            ko_feats[ko] = feats

    print(f"\nKOs with valid features: {len(ko_feats)} / {len(all_kos)}", flush=True)

    # ── Build training DataFrame ─────────────────────────────────────────────
    train_rows = []
    for ko in pos_kos:
        if ko in ko_feats:
            train_rows.append({'ko_id': ko, 'label': 1, **ko_feats[ko]})
    for ko in neg_kos:
        if ko in ko_feats:
            train_rows.append({'ko_id': ko, 'label': 0, **ko_feats[ko]})

    train_df = pd.DataFrame(train_rows).dropna()
    print(f"Training set: {(train_df['label']==1).sum()} positives, "
          f"{(train_df['label']==0).sum()} negatives", flush=True)

    X = train_df[FEATURE_COLS].values
    y = train_df['label'].values

    # ── Cross-validated AUC ──────────────────────────────────────────────────
    print("\nCross-validation (5-fold stratified) ...", flush=True)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    results = {}
    for name, clf in [
        ('Logistic (L2)',   Pipeline([('sc', StandardScaler()),
                                      ('clf', LogisticRegression(C=1.0, max_iter=1000, random_state=42))])),
        ('Random Forest',   RandomForestClassifier(n_estimators=300, max_depth=5,
                                                   min_samples_leaf=5, random_state=42)),
    ]:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            probs = cross_val_predict(clf, X, y, cv=cv, method='predict_proba')[:, 1]
        auc = roc_auc_score(y, probs)
        results[name] = {'auc': auc, 'probs': probs}
        print(f"  {name}: AUC = {auc:.3f}", flush=True)

    # ── Train final model (Random Forest, best AUC) ──────────────────────────
    best_name = max(results, key=lambda k: results[k]['auc'])
    print(f"\nTraining final model: {best_name} ...", flush=True)

    if best_name == 'Random Forest':
        final_clf = RandomForestClassifier(n_estimators=500, max_depth=5,
                                           min_samples_leaf=5, random_state=42)
    else:
        final_clf = Pipeline([('sc', StandardScaler()),
                              ('clf', LogisticRegression(C=1.0, max_iter=1000, random_state=42))])

    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        final_clf.fit(X, y)

    # ── Feature importances ───────────────────────────────────────────────────
    if isinstance(final_clf, RandomForestClassifier):
        fi = pd.Series(final_clf.feature_importances_, index=FEATURE_COLS).sort_values(ascending=False)
        print("\nTop-15 feature importances:")
        print(fi.head(15).to_string())

    # ── Apply to all KO sets ─────────────────────────────────────────────────
    def predict_set(kos: set, label: str) -> pd.DataFrame:
        rows = []
        for ko in kos:
            if ko in ko_feats:
                rows.append({'ko_id': ko, **ko_feats[ko]})
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows).dropna(subset=FEATURE_COLS)
        X_pred = df[FEATURE_COLS].values
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            probs = final_clf.predict_proba(X_pred)[:, 1]
        df['pred_prob'] = probs
        df['prev_pct'] = df['ko_id'].map(prev_map)
        df['group'] = label
        return df[['ko_id', 'group', 'pred_prob', 'prev_pct']]

    sets = {
        'field-strict': field_strict,
        'field-loose':  field_loose,
        'lab-top96':    lab_top96,
        'lab-hits':     pos_kos,
        'neutral':      neg_kos,
    }

    all_preds = pd.concat([predict_set(kos, label) for label, kos in sets.items()],
                          ignore_index=True)

    # ── Statistical comparisons ───────────────────────────────────────────────
    print("\n=== Predicted metal-fitness probability by group ===")
    print(f"{'Group':<20} {'n':>5} {'mean':>7} {'median':>7} {'≥0.5':>6}")
    for grp in ['field-strict', 'field-loose', 'lab-top96', 'lab-hits', 'neutral']:
        sub = all_preds[all_preds['group'] == grp]['pred_prob']
        if len(sub) == 0:
            print(f"  {grp:<20} {'—':>5}")
            continue
        print(f"  {grp:<20} {len(sub):>5} {sub.mean():>7.3f} {sub.median():>7.3f} {(sub>=0.5).sum():>6}")

    print("\n=== Mann-Whitney: field vs lab ===")
    for fl in ['field-strict', 'field-loose']:
        fp = all_preds[all_preds['group'] == fl]['pred_prob'].values
        for ll in ['lab-top96', 'lab-hits']:
            lp = all_preds[all_preds['group'] == ll]['pred_prob'].values
            if len(fp) == 0 or len(lp) == 0:
                continue
            u, p = stats.mannwhitneyu(fp, lp, alternative='less')
            print(f"  {fl} < {ll}: U={u:.0f}, p={p:.4f}")

    print("\n=== Mann-Whitney: field vs neutral (are field KOs different from random?) ===")
    for fl in ['field-strict', 'field-loose']:
        fp = all_preds[all_preds['group'] == fl]['pred_prob'].values
        np_ = all_preds[all_preds['group'] == 'neutral']['pred_prob'].values
        if len(fp) == 0: continue
        u, p_less = stats.mannwhitneyu(fp, np_, alternative='less')
        u2, p_two = stats.mannwhitneyu(fp, np_, alternative='two-sided')
        print(f"  {fl} vs neutral: p(field<neutral)={p_less:.4f}  p(two-sided)={p_two:.4f}")

    # ── Prevalence-stratified check ───────────────────────────────────────────
    print("\n=== Prevalence-stratified: within 0–10% prev bucket ===")
    low_prev = all_preds[all_preds['prev_pct'] <= 10]
    for grp in ['field-strict', 'field-loose', 'neutral']:
        sub = low_prev[low_prev['group'] == grp]['pred_prob']
        if len(sub) < 3:
            print(f"  {grp:<20} n={len(sub)} (too few)")
            continue
        print(f"  {grp:<20} n={len(sub):>4}  mean={sub.mean():.3f}  median={sub.median():.3f}")

    # ── Save ─────────────────────────────────────────────────────────────────
    all_preds.to_csv(DATA_DIR / 'nb11_predicted_fitness_probs.csv', index=False)
    print(f"\nSaved: nb11_predicted_fitness_probs.csv")
    print(f"Model AUC: {results[best_name]['auc']:.3f} ({best_name})")


if __name__ == '__main__':
    main()

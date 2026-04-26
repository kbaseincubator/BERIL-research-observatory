"""Build NB04e_option_A_viability.ipynb — cell-count + pilot DA for within-ecotype × within-substudy CD-vs-nonIBD.

Tests whether Pillar 2 E1 can be rescued under the confound-free design (Option A from NB04d §6)
by stratifying the within-IBD-substudy CD-vs-nonIBD contrast by ecotype.
"""
from pathlib import Path
import nbformat as nbf

NB_PATH = Path(__file__).parent / "NB04e_option_A_viability.ipynb"
nb = nbf.v4.new_notebook()
cells = []

cells.append(nbf.v4.new_markdown_cell("""# NB04e — Option A Viability: Within-Ecotype × Within-Substudy CD-vs-nonIBD

**Project**: `ibd_phage_targeting` — E1 Pillar 2 rescue attempt
**Depends on**: NB04c (substudy map, wide matrix, ecotype assignments)

## Purpose

NB04d blocked Pillar 2 for E1. The recommended rescue is Option A: stratify the within-IBD-substudy CD-vs-nonIBD contrast (NB04c's confound-free analysis) by ecotype, so CD-vs-nonIBD is computed within a single (substudy, ecotype) cell. This breaks feature leakage because ecotype and DA are no longer testing the same samples on the same features — the within-substudy constraint supplies the independent evidence stream.

**This notebook tests whether Option A is viable** by:

1. Counting (ecotype × substudy × diagnosis) cells in the 4 IBD substudies (HallAB_2017, LiJ_2014, IjazUZ_2017, NielsenHB_2014).
2. Identifying eligible cells (≥ 10 CD AND ≥ 10 nonIBD).
3. Running per-cell CLR-Δ DA on NB04c's candidate battery.
4. Per-ecotype inverse-variance weighted meta-analysis across eligible substudies.
5. Deciding: is Option A viable per ecotype? If yes, what is the new per-ecotype Tier-A?

**Decision rule**:

- **Option A viable for ecotype K** if ≥ 2 substudies have ≥ 10 CD and ≥ 10 nonIBD samples in that ecotype, enabling meta-analysis.
- **Option A partially viable** if 1 substudy qualifies (single-study evidence, no meta — report but flag).
- **Option A not viable** if 0 substudies qualify — E1 needs Option B (pathway ecotypes) or Option C (cohort-level).
"""))

cells.append(nbf.v4.new_code_cell("""import warnings; warnings.filterwarnings('ignore')
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.stats import t as t_dist
from statsmodels.stats.multitest import multipletests

DATA_MART = Path.home() / 'data' / 'CrohnsPhage'
DATA_OUT = Path('../data')

# Rebuild the wide matrix + ecotype + substudy_map (same pipeline as NB04c)
syn = pd.read_csv(DATA_OUT / 'species_synonymy.tsv', sep='\\t')
lookup = dict(zip(syn.alias, syn.canonical))
ta = pd.read_parquet(DATA_MART / 'fact_taxon_abundance.snappy.parquet')
ta = ta[(ta.classification_method == 'metaphlan3') & (ta.study_id.isin(['CMD_HEALTHY','CMD_IBD']))].copy()

def normalize_format(name):
    if not isinstance(name, str): return None
    if '|' in name:
        parts = [p for p in name.split('|') if p.startswith('s__')]
        return parts[0][3:].replace('_', ' ').strip() if parts else None
    return name.replace('[','').replace(']','').strip()

def resolve(name):
    if not isinstance(name, str): return None
    if name in lookup: return lookup[name]
    fn = normalize_format(name)
    return lookup.get(fn, fn) if fn else None

ta['species'] = ta['taxon_name_original'].map(resolve)
ta = ta.dropna(subset=['species']).copy()
wide = ta.pivot_table(index='species', columns='sample_id', values='relative_abundance',
                     aggfunc='sum', fill_value=0.0)

eco = pd.read_csv(DATA_OUT / 'ecotype_assignments.tsv', sep='\\t')
eco_map = dict(zip(eco.sample_id, eco.consensus_ecotype))
diag_map = dict(zip(eco.sample_id, eco.diagnosis))
cols_keep = [c for c in wide.columns if c in eco_map]
wide = wide[cols_keep]
keep = pd.concat([
    (wide[[c for c in wide.columns if diag_map.get(c) == d]] > 0).mean(axis=1)
    for d in ['HC','CD','UC'] if any(diag_map.get(c) == d for c in wide.columns)
], axis=1).max(axis=1) >= 0.05
w = wide.loc[keep].copy()

dim_samples = pd.read_parquet(DATA_MART / 'dim_samples.snappy.parquet')
def resolve_substudy(row):
    ext = row['external_ids']
    if isinstance(ext, str):
        try:
            d = json.loads(ext)
            if isinstance(d.get('study'), str): return d['study']
        except Exception: pass
    pid = row['participant_id']
    if isinstance(pid, str):
        parts = pid.split(':')
        if len(parts) >= 3 and parts[0] in ('CMD', 'HMP2'): return parts[1]
    return None
dim_samples['substudy'] = dim_samples.apply(resolve_substudy, axis=1)
substudy_map = dict(zip(dim_samples.sample_id, dim_samples.substudy))

def clr(M):
    M = M.astype(float).copy()
    col_min_nz = np.where(M > 0, M, np.nan)
    col_min_nz = np.nanmin(col_min_nz, axis=0)
    col_min_nz = np.where(np.isnan(col_min_nz), 1e-6, col_min_nz / 2)
    M = np.where(M > 0, M, col_min_nz[None, :])
    logM = np.log(M)
    return logM - logM.mean(axis=0, keepdims=True)

print(f'Wide matrix: {w.shape[0]:,} species × {w.shape[1]:,} samples')
"""))

cells.append(nbf.v4.new_markdown_cell("""## §1. Count (ecotype × substudy × diagnosis) cells"""))

cells.append(nbf.v4.new_code_cell("""sample_meta = pd.DataFrame({
    'sample_id': w.columns,
    'substudy': [substudy_map.get(s) for s in w.columns],
    'diagnosis': [diag_map.get(s) for s in w.columns],
    'ecotype': [eco_map.get(s) for s in w.columns],
})
sample_meta = sample_meta[sample_meta.substudy.notna()]

# 4 IBD substudies with both CD and nonIBD
IBD_STUDIES = ['HallAB_2017', 'LiJ_2014', 'IjazUZ_2017', 'NielsenHB_2014']
sm_ibd = sample_meta[sample_meta.substudy.isin(IBD_STUDIES)]

# (ecotype × substudy × diagnosis) counts
cells_tbl = sm_ibd.groupby(['ecotype','substudy','diagnosis']).size().unstack(fill_value=0)
cells_tbl = cells_tbl[['CD', 'nonIBD'] + [c for c in cells_tbl.columns if c not in ('CD','nonIBD')]]
print('Cell counts per (ecotype × substudy) — within the 4 IBD studies:')
print(cells_tbl.to_string())

# Eligibility: n_CD >= 10 AND n_nonIBD >= 10 per (ecotype, substudy)
eligible_cells = []
for (k, st), row in cells_tbl.iterrows():
    cd_n = int(row.get('CD', 0)); ni_n = int(row.get('nonIBD', 0))
    if cd_n >= 10 and ni_n >= 10:
        eligible_cells.append({'ecotype': k, 'substudy': st, 'n_CD': cd_n, 'n_nonIBD': ni_n})
eligible_df = pd.DataFrame(eligible_cells)

print()
print(f'Eligible cells (n_CD >= 10 AND n_nonIBD >= 10): {len(eligible_df)}')
if len(eligible_df):
    print(eligible_df.to_string(index=False))

# Per-ecotype substudy count
per_eco_substudies = eligible_df.groupby('ecotype').substudy.nunique() if len(eligible_df) else pd.Series(dtype=int)
print()
print('Substudies eligible PER ECOTYPE:')
for k in [0, 1, 2, 3]:
    n = int(per_eco_substudies.get(k, 0))
    verdict = 'meta-viable' if n >= 2 else 'single-study only' if n == 1 else 'NOT VIABLE'
    print(f'  E{k}: {n} eligible substudies  →  Option A {verdict}')
"""))

cells.append(nbf.v4.new_markdown_cell("""## §2. Per-cell within-ecotype within-substudy CD-vs-nonIBD

Only cells with n_CD ≥ 10 AND n_nonIBD ≥ 10. CLR-Δ per species with bootstrap SE."""))

cells.append(nbf.v4.new_code_cell("""def cell_effect(w, sp_list, cd_ids, ni_ids, n_boot=300, rng_seed=42):
    cd_ = [c for c in cd_ids if c in w.columns]
    ni_ = [c for c in ni_ids if c in w.columns]
    if min(len(cd_), len(ni_)) < 10: return None
    cols = cd_ + ni_
    full = clr(w[cols].values)
    n_a = len(cd_)
    rng = np.random.default_rng(rng_seed)
    results = []
    for sp in sp_list:
        if sp not in w.index: continue
        idx = list(w.index).index(sp)
        a = full[idx, :n_a]; b = full[idx, n_a:]
        point = a.mean() - b.mean()
        deltas = np.empty(n_boot)
        for i in range(n_boot):
            ai = rng.integers(0, len(a), len(a))
            bi = rng.integers(0, len(b), len(b))
            deltas[i] = a[ai].mean() - b[bi].mean()
        se = deltas.std()
        results.append({'species': sp, 'point': point, 'se': se,
                        'ci_lo': np.percentile(deltas, 2.5),
                        'ci_hi': np.percentile(deltas, 97.5)})
    return pd.DataFrame(results)

# Test the full 335-species matrix per eligible cell (so we can detect new Tier-A, not just re-score battery)
per_cell_results = []
for _, row in eligible_df.iterrows():
    k, st = row.ecotype, row.substudy
    cd_ids = sm_ibd[(sm_ibd.ecotype == k) & (sm_ibd.substudy == st) & (sm_ibd.diagnosis == 'CD')].sample_id.tolist()
    ni_ids = sm_ibd[(sm_ibd.ecotype == k) & (sm_ibd.substudy == st) & (sm_ibd.diagnosis == 'nonIBD')].sample_id.tolist()
    res = cell_effect(w, w.index.tolist(), cd_ids, ni_ids)
    if res is None: continue
    res['ecotype'] = k; res['substudy'] = st
    res['n_CD'] = len(cd_ids); res['n_nonIBD'] = len(ni_ids)
    per_cell_results.append(res)

if per_cell_results:
    per_cell = pd.concat(per_cell_results, ignore_index=True)
    per_cell.to_csv(DATA_OUT / 'nb04e_per_cell_DA.tsv', sep='\\t', index=False)
    print(f'Per-cell DA rows: {len(per_cell):,} (species × eligible cells)')
    print()
    print('Eligible cells by ecotype × substudy:')
    print(per_cell.groupby(['ecotype','substudy']).size().to_string())
else:
    per_cell = pd.DataFrame()
    print('No eligible cells — Option A not viable for any ecotype.')
"""))

cells.append(nbf.v4.new_markdown_cell("""## §3. Per-ecotype meta-analysis across eligible substudies"""))

cells.append(nbf.v4.new_code_cell("""# For each (ecotype, species) pair, combine across eligible substudies via IVW
meta_rows = []
if len(per_cell):
    for (k, sp), grp in per_cell.groupby(['ecotype', 'species']):
        if len(grp) < 1: continue
        # IVW
        wts = 1.0 / (grp['se'].values ** 2 + 1e-9)
        pooled = (grp['point'].values * wts).sum() / wts.sum()
        pooled_se = np.sqrt(1.0 / wts.sum())
        concord = (np.sign(grp['point'].values) == np.sign(pooled)).mean() if len(grp) > 1 else 1.0
        meta_rows.append({
            'ecotype': int(k),
            'species': sp,
            'n_substudies': len(grp),
            'n_CD_total': int(grp['n_CD'].sum()),
            'n_nonIBD_total': int(grp['n_nonIBD'].sum()),
            'pooled_effect': pooled,
            'pooled_se': pooled_se,
            'concordant_sign_frac': concord,
        })
meta_df = pd.DataFrame(meta_rows)
if len(meta_df):
    meta_df['z'] = meta_df.pooled_effect / meta_df.pooled_se
    meta_df['p'] = 2 * (1 - t_dist.cdf(meta_df.z.abs(), df=40))
    # FDR per ecotype
    meta_df['fdr'] = np.nan
    for k, grp in meta_df.groupby('ecotype'):
        meta_df.loc[grp.index, 'fdr'] = multipletests(grp.p.fillna(1), method='fdr_bh')[1]
    meta_df = meta_df.sort_values(['ecotype','pooled_effect'], ascending=[True, False])
    meta_df.to_csv(DATA_OUT / 'nb04e_within_ecotype_meta.tsv', sep='\\t', index=False)

    print(f'Meta rows: {len(meta_df):,}')
    print()
    # Per-ecotype top CD↑ (pooled_effect > 0.5, fdr < 0.10, concord >= 0.66)
    for k in sorted(meta_df.ecotype.unique()):
        sub = meta_df[(meta_df.ecotype == k) & (meta_df.pooled_effect > 0.5) &
                      (meta_df.fdr < 0.10) & (meta_df.concordant_sign_frac >= 0.66)]
        print(f'E{k} — Tier-A candidates (pooled CD↑ > 0.5 CLR, FDR < 0.10, sign-concord >= 0.66): {len(sub)}')
        if len(sub):
            cols = ['species','pooled_effect','fdr','concordant_sign_frac','n_substudies','n_CD_total','n_nonIBD_total']
            print(sub[cols].head(20).to_string(index=False))
        print()
else:
    print('No meta-analysis produced — no eligible cells.')
"""))

cells.append(nbf.v4.new_markdown_cell("""## §4. Option A viability verdict"""))

cells.append(nbf.v4.new_code_cell("""viability = {}
per_eco_viable = {}
if len(eligible_df):
    for k in [0, 1, 2, 3]:
        n_substudies = int(eligible_df[eligible_df.ecotype == k].substudy.nunique())
        if n_substudies >= 2:
            per_eco_viable[k] = 'meta-viable'
        elif n_substudies == 1:
            per_eco_viable[k] = 'single-study-only'
        else:
            per_eco_viable[k] = 'not-viable'

# Per-ecotype Tier-A size under Option A
tier_a_sizes = {}
if len(meta_df):
    for k in sorted(meta_df.ecotype.unique()):
        n = len(meta_df[(meta_df.ecotype == k) & (meta_df.pooled_effect > 0.5) &
                        (meta_df.fdr < 0.10) & (meta_df.concordant_sign_frac >= 0.66)])
        tier_a_sizes[int(k)] = n

viability = {
    'date': '2026-04-24',
    'design': 'within-ecotype × within-substudy CD-vs-nonIBD meta-analysis',
    'per_ecotype_viability': per_eco_viable,
    'per_ecotype_tier_a_size': tier_a_sizes,
    'eligible_cells_by_ecotype_substudy': eligible_df.to_dict(orient='records') if len(eligible_df) else [],
    'conclusion': None,
    'recommendation': None,
}

print('=' * 70)
print('OPTION A VIABILITY VERDICT')
print('=' * 70)
for k in [0, 1, 2, 3]:
    viab = per_eco_viable.get(k, 'not-viable')
    sz = tier_a_sizes.get(k, 0)
    print(f'E{k}: {viab}  Tier-A size: {sz}')
print()

# Focus on E1: the blocked ecotype
e1_viab = per_eco_viable.get(1, 'not-viable')
e1_ta = tier_a_sizes.get(1, 0)
if e1_viab == 'meta-viable' and e1_ta >= 3:
    viability['conclusion'] = f'Option A rescues Pillar 2 E1 (Tier-A = {e1_ta})'
    viability['recommendation'] = 'Proceed to NB05 for E1 using Option A Tier-A list; retain NB04d E3 Tier-A for E3.'
elif e1_viab == 'meta-viable' and e1_ta > 0:
    viability['conclusion'] = f'Option A is statistically viable for E1 but yields only {e1_ta} candidates — marginal rescue'
    viability['recommendation'] = 'Pair Option A E1 Tier-A with Option C (cohort-level engraftment) for NB05. Flag small E1 Tier-A as a Pillar 2 limitation in REPORT.'
elif e1_viab == 'single-study-only' and e1_ta > 0:
    viability['conclusion'] = f'Only 1 substudy contributes E1 CD + nonIBD cells; {e1_ta} Tier-A from single-study evidence'
    viability['recommendation'] = 'Pillar 2 E1 under Option A has weak support. Prefer Option C (cohort-level) as primary; use Option A single-study evidence as confirmation.'
else:
    viability['conclusion'] = 'Option A not viable for E1 — insufficient (substudy × ecotype × diagnosis) cells'
    viability['recommendation'] = 'Pillar 2 E1 requires Option B (pathway ecotypes) or Option C (cohort-level Tier-A).'

print(f'Conclusion: {viability[\"conclusion\"]}')
print(f'Recommendation: {viability[\"recommendation\"]}')

with open(DATA_OUT / 'nb04e_option_A_viability.json', 'w') as f:
    json.dump(viability, f, indent=2, default=str)
"""))

nb['cells'] = cells
nb.metadata.kernelspec = {"display_name": "Python 3", "language": "python", "name": "python3"}
nb.metadata.language_info = {"name": "python", "version": "3.10"}

with open(NB_PATH, 'w') as f:
    nbf.write(nb, f)
print(f'Wrote {NB_PATH}')

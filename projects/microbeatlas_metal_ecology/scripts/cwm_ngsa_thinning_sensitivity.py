"""
CWM × NGSA thinning sensitivity.

Replicates NB19 CWM computation exactly, then applies 50 km (0.45° grid)
spatial thinning to test whether the Spearman signal survives independence control.
"""

import sys, numpy as np, pandas as pd
from scipy import stats
from scipy.stats import rankdata

BASE = '/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology'

METALS       = ['As', 'Cd', 'Co', 'Cr', 'Cu', 'Hg', 'Ni', 'Pb', 'Zn']
NGSA_COLS    = {m: f'ngsa_{m}_ppm' for m in METALS}
NGSA_DIST_KM = 200
THINNING_DEG = 0.45   # ~50 km

# ── Load NGSA data ─────────────────────────────────────────────────────────────
ngsa = pd.read_csv(f'{BASE}/data/aus_microbiome/aus_sample_ngsa.csv')
ngsa['Sample_ID'] = ngsa['Sample_ID'].astype(str).str.split('/').str[-1]
ngsa_filt = ngsa[ngsa['ngsa_dist_km'] <= NGSA_DIST_KM].copy()
ngsa_filt = ngsa_filt.set_index('Sample_ID')
print(f"NGSA-filtered samples: {len(ngsa_filt)}")

# ── Load OTU table and taxonomy ─────────────────────────────────────────────────
print("Loading OTU table...")
otu = pd.read_csv(f'{BASE}/data/aus_microbiome/BASE_16S_OTU.csv.gz', index_col=0)
otu.index   = otu.index.astype(str)
otu.columns = otu.columns.astype(str)
print(f"OTU table: {otu.shape[0]} OTUs x {otu.shape[1]} samples")

tax = pd.read_csv(f'{BASE}/data/aus_microbiome/BASE_16S_taxonomy.csv')
tax['OTUId']       = tax['OTUId'].astype(str)
tax['genus_lower'] = (tax['genus']
                      .str.replace(r'^g__', '', regex=True)
                      .str.strip()
                      .replace({'unclassified': np.nan, '': np.nan})
                      .str.lower())
tax = tax.dropna(subset=['genus_lower'])
genus_map = tax.set_index('OTUId')['genus_lower']

# ── Shared samples ──────────────────────────────────────────────────────────────
otu_g  = otu[otu.index.isin(tax['OTUId'])]
shared = sorted(set(otu.columns) & set(ngsa_filt.index))
print(f"OTUs with genus: {len(otu_g):,}  |  Shared samples: {len(shared)}")

otu_sub = otu_g[shared]
ng_sub  = ngsa_filt.loc[shared]

# ── Relative abundance per sample ───────────────────────────────────────────────
col_sums      = otu_sub.sum(axis=0)
otu_rel       = otu_sub.div(col_sums, axis='columns')
otu_rel.index = otu_rel.index.map(genus_map)
otu_rel       = otu_rel[~otu_rel.index.isna()]
g_ra          = otu_rel.groupby(level=0).sum()

# ── MAG KO density, aggregate to genus ─────────────────────────────────────────
print("Loading MAG KO density...")
mag_ko = pd.read_csv(f'{BASE}/data/mgnify_mag_ko_density.csv')
if mag_ko['genus'].str.startswith('g__').any():
    mag_ko['genus_lower'] = mag_ko['genus'].str[3:].str.lower()
else:
    mag_ko['genus_lower'] = mag_ko['genus'].str.lower()

genus_ko = mag_ko.groupby('genus_lower')[
    ['ko_per_mb_total', 'ko_per_mb_tier1', 'ko_per_mb_tier2']
].mean()
print(f"Genus-level KO density: {len(genus_ko)} genera")

# ── Compute CWM per sample ──────────────────────────────────────────────────────
common = g_ra.index.intersection(genus_ko.index)
print(f"Common genera: {len(common)}")
ra_c = g_ra.loc[common]
ko_c = genus_ko.loc[common]

cwm_records = []
for samp in shared:
    w  = ra_c[samp].values
    ws = w.sum()
    if ws == 0:
        cwm_records.append({'Sample_ID': samp, 'CWM_total': np.nan,
                             'CWM_tier1': np.nan, 'CWM_tier2': np.nan})
    else:
        cwm_records.append({
            'Sample_ID': samp,
            'CWM_total': np.dot(w, ko_c['ko_per_mb_total'].values) / ws,
            'CWM_tier1': np.dot(w, ko_c['ko_per_mb_tier1'].values) / ws,
            'CWM_tier2': np.dot(w, ko_c['ko_per_mb_tier2'].values) / ws,
        })

cwm_df = pd.DataFrame(cwm_records).set_index('Sample_ID')
cwm_df = cwm_df.join(ng_sub[[NGSA_COLS[m] for m in METALS if NGSA_COLS[m] in ng_sub.columns]],
                     how='inner')

# Attach coordinates for thinning
cwm_df = cwm_df.join(ng_sub[['latitude', 'longitude']], how='inner')
print(f"CWM computed for {len(cwm_df)} samples")

# ── Spearman on unthinned data (baseline, should match NB19) ───────────────────
def spearman_sweep(df, label):
    rows = []
    for metal in METALS:
        col = NGSA_COLS[metal]
        if col not in df.columns:
            continue
        for cwm_type in ['CWM_total', 'CWM_tier1', 'CWM_tier2']:
            v = df[[cwm_type, col]].dropna()
            if len(v) < 30:
                continue
            rho, p = stats.spearmanr(v[col], v[cwm_type])
            rows.append({'metal': metal, 'cwm_type': cwm_type,
                         'rho': rho, 'p': p, 'n_samples': len(v)})
    if not rows:
        return pd.DataFrame()
    res = pd.DataFrame(rows)
    m = len(res)
    ranks = rankdata(res['p'])
    res['q_BH'] = np.minimum(res['p'] * m / ranks, 1.0)
    res = res.sort_values('q_BH').reset_index(drop=True)
    sig = (res['q_BH'] < 0.05).sum()
    print(f"\n{label}: n_tests={m}, FDR<0.05: {sig}/{m}")
    print(res[['metal', 'cwm_type', 'rho', 'p', 'q_BH', 'n_samples']].head(10).to_string())
    return res

res_full = spearman_sweep(cwm_df, "Unthinned (baseline)")

# ── 50 km thinning (0.45° grid) ────────────────────────────────────────────────
rng = np.random.default_rng(42)

def thin_50km(df, deg=THINNING_DEG):
    """One sample per 0.45° grid cell (random draw)."""
    df = df.dropna(subset=['latitude', 'longitude']).copy()
    df['cell_lat'] = (df['latitude']  / deg).apply(np.floor)
    df['cell_lon'] = (df['longitude'] / deg).apply(np.floor)
    cells = df.groupby(['cell_lat', 'cell_lon'])
    kept = []
    for _, grp in cells:
        idx = rng.choice(grp.index)
        kept.append(idx)
    return df.loc[kept].drop(columns=['cell_lat', 'cell_lon'])

cwm_thin = thin_50km(cwm_df)
print(f"\nAfter 50 km thinning: {len(cwm_thin)} samples (from {len(cwm_df)})")

res_thin = spearman_sweep(cwm_thin, "50 km thinned")

# ── Save results ────────────────────────────────────────────────────────────────
out_dir = f'{BASE}/data'

res_full['thinning'] = 'none'
res_thin['thinning'] = '50km'
combined = pd.concat([res_full, res_thin], ignore_index=True)
combined.to_csv(f'{out_dir}/cwm_ngsa_thinning_sensitivity.csv', index=False)
print(f"\nSaved: {out_dir}/cwm_ngsa_thinning_sensitivity.csv")

# ── Summary comparison ──────────────────────────────────────────────────────────
print("\n=== SUMMARY ===")
for label, res in [("Unthinned", res_full), ("50km-thinned", res_thin)]:
    n = res['n_samples'].iloc[0] if len(res) else 0
    sig = (res['q_BH'] < 0.05).sum() if len(res) else 0
    total = len(res)
    print(f"  {label}: n≈{n}, FDR<0.05 = {sig}/{total}")
    if len(res):
        print(f"    rho range: {res['rho'].min():.3f} – {res['rho'].max():.3f}")
        sig_rows = res[res['q_BH'] < 0.05][['metal', 'cwm_type', 'rho', 'q_BH']]
        if len(sig_rows):
            print(sig_rows.to_string(index=False))

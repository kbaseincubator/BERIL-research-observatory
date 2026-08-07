"""
NB27 optimised — tier-specific coreness-matched permutation test.

Uses ONE batched Spark query then pure-pandas permutations (Pearson r as
test statistic, valid because λ≈0.804 is constant across all permutations).
"""
import os, random, sys
from pathlib import Path

os.environ['OMP_NUM_THREADS'] = '1'

import numpy as np
import pandas as pd
from scipy.stats import pearsonr

PROJECT = Path('/home/hmacgregor/BERIL-research-observatory/projects/comprehensive_metal_ecology')
DATA    = PROJECT / 'data'
FIGS    = PROJECT / 'figures'

sys.path.insert(0, str(PROJECT / 'scripts'))
sys.path.insert(0, '/home/hmacgregor/BERIL-research-observatory/tools')
from figure_style import apply_style, save, PALETTE, FIGW, ROW_H
apply_style()

# ── Load base data ────────────────────────────────────────────────────────────
bac_base  = pd.read_csv(DATA / '01_pgls_input_bacteria.csv')
trait_df  = bac_base[['genus_lower', 'mean_levins_B_std']].copy()

gene_df   = pd.read_csv(DATA / 'curated_mrg_ko_ids_v2.csv')
coreness_df = pd.read_csv(DATA / 'ko_coreness_pangenome.csv')
coreness_df['coreness'] = coreness_df['coreness'].astype(float)

primary_df = gene_df[gene_df['evidence_tier'].isin(['Tier 1', 'Tier 2'])]
primary_kos = set(primary_df['KO'])
cofactor_kos = list(primary_df[primary_df['primary_category'] == 'Cofactor Biosynthesis']['KO'])
resistance_kos = list(primary_df[primary_df['primary_category'] == 'Resistance/Detoxification']['KO'])

ALL_KO_CORE = coreness_df.set_index('ko')['coreness']
decile_bins = np.percentile(ALL_KO_CORE, np.linspace(0, 100, 11))
decile_bins[0] = -np.inf;  decile_bins[-1] = np.inf

def assign_decile(val):
    return int(np.searchsorted(decile_bins[1:-1], val))

ko_decile = ALL_KO_CORE.apply(assign_decile)

print(f"Base data: {len(bac_base)} genera")
print(f"Cofactor KOs ({len(cofactor_kos)}): {cofactor_kos}")
print(f"Resistance KOs ({len(resistance_kos)}): {resistance_kos[:5]}...")

# ── Build per-tier decile pools ───────────────────────────────────────────────
def get_tier_info(ko_list):
    tier_core = pd.Series({k: ALL_KO_CORE.get(k, np.nan) for k in ko_list}).dropna()
    tier_deciles = tier_core.apply(assign_decile)
    decile_counts = tier_deciles.value_counts().to_dict()
    pool_by_decile = {}
    for d in range(10):
        pool = ALL_KO_CORE[(ko_decile == d) & (~ALL_KO_CORE.index.isin(primary_kos))]
        pool_by_decile[d] = list(pool.index)
    return {'n_kos': len(ko_list), 'decile_counts': decile_counts,
            'pool_by_decile': pool_by_decile}

def sample_matched_set(tier_info):
    sampled = []
    for d, n in tier_info['decile_counts'].items():
        pool = tier_info['pool_by_decile'].get(d, [])
        if len(pool) < n:
            sampled.extend(random.choices(pool, k=n) if pool else [])
        else:
            sampled.extend(random.sample(pool, n))
    return list(set(sampled))

tiers = {'Cofactor Biosynthesis': cofactor_kos, 'Resistance/Detoxification': resistance_kos}
tier_infos = {name: get_tier_info(kos) for name, kos in tiers.items()}

for name, info in tier_infos.items():
    print(f"\n{name}: n_kos={info['n_kos']}, decile_counts={info['decile_counts']}")

# ── Pre-generate all permuted sets ────────────────────────────────────────────
N_PERM = 1000
random.seed(42)
perm_sets = {name: [sample_matched_set(info) for _ in range(N_PERM)]
             for name, info in tier_infos.items()}

all_needed_kos = set(cofactor_kos) | set(resistance_kos)
for sets in perm_sets.values():
    for s in sets:
        all_needed_kos.update(s)
print(f"\nTotal unique KOs for Spark query: {len(all_needed_kos)}")

# ── Single batched Spark query ────────────────────────────────────────────────
try:
    from berdl_utils import get_spark_session
    _spark = get_spark_session()
    print("Spark OK")
except Exception as e:
    print(f"Spark unavailable: {e}")
    sys.exit(1)

ko_list = list(all_needed_kos)
batch_size = 400
batches = [ko_list[i:i+batch_size] for i in range(0, len(ko_list), batch_size)]
print(f"Running {len(batches)} Spark batches of ≤{batch_size} KOs each...")

dfs = []
for i, batch in enumerate(batches):
    # gene_eggnog uses 'ko:K02225' prefix; strip it in the SELECT
    quoted = ', '.join(f"'ko:{k}'" for k in batch)
    sql = f"""
        SELECT REGEXP_REPLACE(koid.ko, '^ko:', '') AS ko,
               LOWER(TRIM(regexp_extract(gm.lineage, 'g__([^;]+)', 1))) AS genus_lower,
               SUM(1.0 / (gm.length / 1e6)) AS sum_inv_gl_mb,
               COUNT(DISTINCT gm.genome_id) AS n_genomes_with_ko
        FROM kescience_mgnify.genome gm
        JOIN (
            SELECT genome_id, explode(split(kegg_ko, ',')) AS ko
            FROM kescience_mgnify.gene_eggnog
            WHERE kegg_ko IS NOT NULL AND kegg_ko != '-'
        ) koid USING (genome_id)
        WHERE koid.ko IN ({quoted})
        GROUP BY koid.ko, genus_lower
    """
    df = _spark.sql(sql).toPandas()
    df.attrs = {}
    dfs.append(df)
    print(f"  Batch {i+1}/{len(batches)}: {len(df)} rows")

ko_genus_raw = pd.concat(dfs, ignore_index=True)
print(f"Total rows: {len(ko_genus_raw)}")

# (No per-genus total needed — using per-KO conditional density instead)
print("Skipping genus totals query (not needed for conditional density metric)")

# Compute per-KO per-genus conditional density (mean 1/genome_length_mb over
# genomes that HAVE the KO) — matches the run_density_pgls metric exactly.
# For a set S: density_S ≈ sum_{ko in S} cond_density[ko, genus]
# (separable approximation; exact for single-KO case; minor error for multi-KO
# from double-counting of genomes with multiple S-KOs, acceptable for ranking).
ko_genus_raw['cond_density'] = ko_genus_raw['sum_inv_gl_mb'] / ko_genus_raw['n_genomes_with_ko']
ko_genus_raw = ko_genus_raw.dropna(subset=['cond_density', 'genus_lower'])
print(f"Valid (ko, genus) pairs: {len(ko_genus_raw)}")

# ── Helper: compute genus density for a KO set ───────────────────────────────
def genus_density(ko_set):
    """Sum per-KO conditional densities across the set → genus density vector."""
    sub = ko_genus_raw[ko_genus_raw['ko'].isin(ko_set)]
    dens = sub.groupby('genus_lower')['cond_density'].sum().reset_index()
    dens.columns = ['genus_lower', 'density']
    merged = trait_df.merge(dens, on='genus_lower', how='inner')
    return merged

def pearson_r(df):
    if len(df) < 30:
        return np.nan
    r, _ = pearsonr(df['density'], df['mean_levins_B_std'])
    return r

# ── Observed test statistics ─────────────────────────────────────────────────
print("\nComputing observed Pearson r per tier...")
obs_r = {}
obs_n = {}
for name, kos in tiers.items():
    df = genus_density(kos)
    r = pearson_r(df)
    obs_r[name] = r
    obs_n[name] = len(df)
    print(f"  {name}: r={r:.4f}, n_genera={len(df)}")

# ── Permutation loop (pure pandas, ~ms per iteration) ────────────────────────
print("\nRunning permutations...")
perm_r_by_tier = {}

for name, sets in perm_sets.items():
    rs = []
    for i, kos in enumerate(sets):
        df = genus_density(kos)
        r = pearson_r(df)
        if not np.isnan(r):
            rs.append(r)
        if (i + 1) % 200 == 0:
            valid = [x for x in rs if not np.isnan(x)]
            print(f"  {name}: {i+1}/{N_PERM} done, valid={len(valid)}, "
                  f"r range [{min(valid):.4f}, {max(valid):.4f}]")
    perm_r_by_tier[name] = np.array(rs)
    print(f"  {name}: {len(rs)} valid permutations")

# ── Empirical p-values ───────────────────────────────────────────────────────
print("\n" + "="*65)
print("TIER-SPECIFIC CORENESS PERMUTATION TEST — RESULTS")
print("="*65)

results_rows = []
for name in tiers:
    obs = obs_r[name]
    perm = perm_r_by_tier[name]
    emp_p = (perm <= obs).mean()
    survives = emp_p < 0.05
    print(f"\n{name}:")
    print(f"  Observed Pearson r: {obs:.4f}  (n_genera={obs_n[name]})")
    print(f"  Permutation r: median={np.median(perm):.4f}, SD={perm.std():.4f}")
    print(f"  Empirical p (r ≤ obs): {emp_p:.4g} ({(perm<=obs).sum()}/{len(perm)})")
    print(f"  SURVIVES permutation (p<0.05): {'YES' if survives else 'NO'}")
    results_rows.append({
        'tier': name,
        'n_kos': tier_infos[name]['n_kos'],
        'n_genera_observed': obs_n[name],
        'observed_r': obs,
        'perm_median_r': float(np.median(perm)),
        'perm_sd_r': float(perm.std()),
        'emp_p': float(emp_p),
        'n_valid_perms': len(perm),
        'survives': survives,
    })

results_df = pd.DataFrame(results_rows)
results_df.to_csv(DATA / 'tier_coreness_permutation_v2.csv', index=False)
print(f"\nSaved: data/tier_coreness_permutation_v2.csv")

# ── Figure ───────────────────────────────────────────────────────────────────
import matplotlib.pyplot as plt

GRAY = '#999999'
tier_colors = {
    'Cofactor Biosynthesis': '#E69F00',
    'Resistance/Detoxification': '#D55E00',
}

fig, axs = plt.subplots(1, 2, figsize=(FIGW['2col'], ROW_H))

for idx, row in enumerate(results_df.itertuples()):
    ax = axs[idx]
    perm = perm_r_by_tier[row.tier]
    col  = tier_colors[row.tier]

    ax.hist(perm, bins=40, color=GRAY, alpha=0.75, edgecolor='white', lw=0.4)
    ax.axvline(row.observed_r, color=col, lw=2.2,
               label=f'Observed r = {row.observed_r:+.3f}\nemp p = {row.emp_p:.3g}')
    ax.set_xlabel('Permuted Pearson r', fontsize=9)
    ax.set_ylabel('Count', fontsize=9)
    tier_short = 'Cofactor\nBiosynthesis' if 'Cofactor' in row.tier else 'Resistance/\nDetoxification'
    ax.set_title(f'{tier_short}\n(n={row.n_kos} KOs, {row.n_valid_perms} perms)', fontsize=9)
    ax.legend(fontsize=8, framealpha=0.95, loc='upper right')
    ax.axvline(0, color='gray', lw=0.8, ls='--')

plt.tight_layout()
save(fig, FIGS / 'tier_coreness_permutation')
print("Saved: figures/tier_coreness_permutation.pdf")

print("\nDone.")

"""
soil_niche_extensions.py

Three additional PGLS models with soil-sample niche breadth (levins_B_soil_std):
  M11  expanded essential biosynthetic set (cofactor_vit + aa + nucleotide + lipid)
  M12  joint essential vs. accessory (resistance) — two β values
  M13  double-signal aggregate density
  M14  high-λ aggregate density
"""
import os, sys
import numpy as np
import pandas as pd
from pathlib import Path

os.environ.setdefault('OMP_NUM_THREADS', '1')
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
os.environ.setdefault('MKL_NUM_THREADS', '1')

DATA    = Path('data')
SCRIPTS = Path('scripts')
TREE    = str(DATA / 'gtdb_bac_genus_pruned.tree')
MIN_N   = 30
RESPONSE = 'levins_B_soil_std'

sys.path.insert(0, str(SCRIPTS))
from pgls_utils import run_pgls


def _z(s):
    v = s.dropna()
    if len(v) < 5 or v.std() == 0:
        return pd.Series(np.nan, index=s.index)
    return (s - v.mean()) / v.std()


def _extract(res, focal):
    if res is None:
        return np.nan, np.nan, np.nan, np.nan
    if 'betas' in res and isinstance(res['betas'], dict):
        beta = res['betas'].get(focal, np.nan)
        SE   = res['SEs'].get(focal, np.nan)
        p    = res['p_values'].get(focal, np.nan)
    else:
        beta = res.get('beta', np.nan)
        SE   = res.get('SE', np.nan)
        p    = res.get('p_value', np.nan)
    lam = res.get('lambda_est', np.nan)
    return beta, SE, p, lam


def run_model(df, label, predictors, focal=None):
    if focal is None:
        focal = predictors[0]
    cols = [RESPONSE] + predictors + ['genus_lower']
    valid = df[cols].dropna()
    n = len(valid)
    if n < MIN_N:
        print(f"  SKIP {label}: n={n}")
        return None
    res = run_pgls(valid, TREE, response=RESPONSE, predictors=predictors,
                   taxon_col='genus_lower', label=label, min_n=MIN_N)
    beta, SE, p, lam = _extract(res, focal)
    n_actual = res.get('n', n)
    ps = ('***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05
          else '†' if p < 0.10 else 'NS')
    print(f"  {label}: n={n_actual}  β={beta:+.6f}  SE={SE:.6f}  p={p:.4g}{ps}  λ={lam:.3f}")
    return {'label': label, 'response': RESPONSE, 'focal': focal,
            'n': n_actual, 'beta': beta, 'SE': SE, 'p_value': p, 'lambda_est': lam}


# ── Load base data ──────────────────────────────────────────────────────────
df = pd.read_csv(DATA / 'soil_sample_pgls_dataset.csv')
density = pd.read_csv(DATA / '01_genus_ko_density_spark.csv')
nb25 = pd.read_parquet(DATA / 'nb25_ko_presence_matrix.parquet')
nb25['genus_lower'] = nb25['genus_lower'].str.replace(r'^g__', '', regex=True)

lipid = pd.read_csv(DATA / 'landscape_lipid_metab_density.csv')[['genus_lower','ko_per_mb']]
lipid = lipid.rename(columns={'ko_per_mb': 'lipid_per_mb'})
df = df.merge(lipid, on='genus_lower', how='left')

print(f"Dataset n={len(df)}, levins_B_soil_std notna={df[RESPONSE].notna().sum()}")
print(f"lipid_per_mb notna={df['lipid_per_mb'].notna().sum()}")


# ── M11: expanded essential biosynthetic set ────────────────────────────────
# cofactor_vitamin + aa_metab + nucleotide + lipid (sum of per-Mb densities)
ess_cols = ['cofactor_vitamin_per_mb', 'aa_metab_per_mb', 'nucleotide_per_mb', 'lipid_per_mb']
df['expanded_essential_per_mb'] = df[ess_cols].sum(axis=1, skipna=False)
# NaN if any component missing
df.loc[df[ess_cols].isna().any(axis=1), 'expanded_essential_per_mb'] = np.nan
df['expanded_essential_z'] = _z(df['expanded_essential_per_mb'])
df['gsize_z']              = _z(df['mean_genome_mb'])

print(f"\nexpanded_essential_per_mb notna={df['expanded_essential_per_mb'].notna().sum()}")
print(f"  mean={df['expanded_essential_per_mb'].mean():.4f}, "
      f"SD={df['expanded_essential_per_mb'].std():.4f}")

# ── M12: accessory = resistance_per_mb ─────────────────────────────────────
df['resistance_z'] = _z(df['resistance_per_mb'])

# ── M13/M14: double-signal and high-λ aggregates from nb25 ─────────────────
DS_KOS  = ['K03897','K05908','K07785','K08170','K08356','K14974','K15585',
           'K19057','K19059','K19592','K19594','K19595','K25119']
HIL_KOS = ['K18146','K07807','K18307','K22041','K08355','K02230','K09883',
           'K07796','K21572','K08167']

density_aug = density[['genus_lower','n_genomes','mean_genome_mb']].drop_duplicates()

def compute_agg_density(nb25_df, ko_list, density_df, colname):
    sub = nb25_df[nb25_df['ko'].isin(ko_list)].copy()
    sub = sub.merge(density_df, on='genus_lower', how='left')
    sub['pres'] = sub['n_genomes_with_ko'] / sub['n_genomes'].clip(lower=1)
    grp = sub.groupby('genus_lower').agg(
        total_pres=('pres', 'sum'),
        mean_mb=('mean_genome_mb', 'first')
    ).reset_index()
    grp[colname] = grp['total_pres'] / grp['mean_mb'].clip(lower=0.01)
    return grp[['genus_lower', colname]]

ds_agg  = compute_agg_density(nb25, DS_KOS,  density_aug, 'ds_agg_per_mb')
hil_agg = compute_agg_density(nb25, HIL_KOS, density_aug, 'hil_agg_per_mb')

df = df.merge(ds_agg,  on='genus_lower', how='left')
df = df.merge(hil_agg, on='genus_lower', how='left')
df['ds_agg_z']  = _z(df['ds_agg_per_mb'])
df['hil_agg_z'] = _z(df['hil_agg_per_mb'])

print(f"ds_agg_per_mb notna={df['ds_agg_per_mb'].notna().sum()}")
print(f"hil_agg_per_mb notna={df['hil_agg_per_mb'].notna().sum()}")


# ── Run models ──────────────────────────────────────────────────────────────
results = []

print("\n── M11: expanded_essential ~ soil niche ──")
r = run_model(df, 'M11_expanded_essential', ['expanded_essential_z', 'gsize_z'])
if r: results.append(r)

print("\n── M12: joint essential + accessory ~ soil niche ──")
r = run_model(df, 'M12_joint_essential', ['expanded_essential_z', 'resistance_z', 'gsize_z'],
              focal='expanded_essential_z')
if r: results.append(r)
r = run_model(df, 'M12_joint_accessory', ['expanded_essential_z', 'resistance_z', 'gsize_z'],
              focal='resistance_z')
if r: results.append(r)

print("\n── M13: double-signal aggregate ~ soil niche ──")
r = run_model(df, 'M13_double_signal_agg', ['ds_agg_z', 'gsize_z'])
if r: results.append(r)

print("\n── M14: high-λ aggregate ~ soil niche ──")
r = run_model(df, 'M14_high_lambda_agg', ['hil_agg_z', 'gsize_z'])
if r: results.append(r)


# ── Append to existing results ──────────────────────────────────────────────
existing = pd.read_csv(DATA / 'soil_sample_pgls_results.csv')
new_rows = pd.DataFrame(results)
combined = pd.concat([existing, new_rows], ignore_index=True)
combined.to_csv(DATA / 'soil_sample_pgls_results.csv', index=False)
print(f"\nAppended {len(results)} rows → soil_sample_pgls_results.csv ({len(combined)} total)")


# ── Print summary table ─────────────────────────────────────────────────────
print("\n── New results summary ──")
print(f"{'Label':<30} {'β':>10} {'SE':>10} {'p':>10} {'λ':>7} {'n':>6}")
print('-' * 75)
for r in results:
    ps = ('***' if r['p_value'] < 0.001 else '**' if r['p_value'] < 0.01
          else '*' if r['p_value'] < 0.05 else '†' if r['p_value'] < 0.10 else 'NS')
    print(f"{r['label']:<30} {r['beta']:>+10.6f} {r['SE']:>10.6f} "
          f"{r['p_value']:>9.4g}{ps:<2} {r['lambda_est']:>7.3f} {r['n']:>6.0f}")

print("\n── All soil PGLS results ──")
full = pd.read_csv(DATA / 'soil_sample_pgls_results.csv')
print(full[['label','beta','SE','p_value','lambda_est','n']].to_string())

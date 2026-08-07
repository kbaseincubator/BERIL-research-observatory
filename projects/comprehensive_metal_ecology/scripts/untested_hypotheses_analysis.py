"""
untested_hypotheses_analysis.py

Tests 5 novel hypotheses not previously examined in the manuscript:

H5c: Resistance subcategory — BacMet-canonical vs fitness-only pleiotropic split
H1b: Environmental range (temp_range, pH) predicts double-signal gene burden per genus
H1a: Per-gene pH/temp associations: double-signal vs high-λ genes (MWU comparison)
H4c: Cofactor signal controlling for housekeeping landscape (translation, replication)
H3b: Double-signal gene burden correlates with metal exposure across geographic range
"""
import os, sys, warnings
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats

os.environ.setdefault('OMP_NUM_THREADS', '1')
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
os.environ.setdefault('MKL_NUM_THREADS', '1')
warnings.filterwarnings('ignore')

DATA    = Path('data')
SCRIPTS = Path('scripts')
REPORT  = Path('report')
TREE    = str(DATA / 'gtdb_bac_genus_pruned.tree')
MIN_N   = 30

sys.path.insert(0, str(SCRIPTS))
from pgls_utils import run_pgls


# ─── helpers ────────────────────────────────────────────────────────────────

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

def run_model(df, label, response, predictors, focal=None, min_n=MIN_N):
    if focal is None:
        focal = predictors[0]
    cols = [response] + predictors + ['genus_lower']
    valid = df[cols].dropna()
    n = len(valid)
    if n < min_n:
        print(f"  SKIP {label}: n={n} < {min_n}")
        return {'label': label, 'response': response, 'focal': focal,
                'n': n, 'beta': np.nan, 'SE': np.nan, 'p': np.nan, 'lambda_est': np.nan}
    res = run_pgls(valid, TREE, response=response, predictors=predictors,
                   taxon_col='genus_lower', label=label, min_n=min_n)
    beta, SE, p, lam = _extract(res, focal)
    n_actual = res.get('n', n)
    ps = ('***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05
          else '†' if p < 0.10 else 'NS')
    print(f"  {label}: n={n_actual} β={beta:+.4f} SE={SE:.4f} p={p:.3g}{ps} λ={lam:.3f}")
    return {'label': label, 'response': response, 'focal': focal,
            'n': n_actual, 'beta': beta, 'SE': SE, 'p': p, 'lambda_est': lam}


# ─── Step 0: Load base data ─────────────────────────────────────────────────

print("── Loading base data ──")
pgls    = pd.read_csv(DATA / 'soil_sample_pgls_dataset.csv')
env     = pd.read_csv(DATA / 'genus_lat_env_covariates.csv')
ko_meta = pd.read_csv(DATA / 'curated_mrg_ko_ids_v2.csv')
D_df    = pd.read_csv(DATA / 'fritz_purvis_D_genome.csv')
lam_df  = pd.read_csv(DATA / 'phylo_d_all_ko.csv')
density = pd.read_csv(DATA / '01_genus_ko_density_spark.csv')
nb25    = pd.read_parquet(DATA / 'nb25_ko_presence_matrix.parquet')
nb25['genus_lower'] = nb25['genus_lower'].str.replace(r'^g__', '', regex=True)

# Double-signal and high-λ gene sets
merged_phylo = D_df.merge(lam_df, on='ko_id')
double_signal_kos = merged_phylo[(merged_phylo['D'] > 0.2) & (merged_phylo['lambda'] < 0.3)]['ko_id'].tolist()
high_lam_kos = (lam_df[lam_df['n_genera'] >= 75]
                .nlargest(10, 'lambda')['ko_id'].tolist())
print(f"  Double-signal KOs: {len(double_signal_kos)}")
print(f"  High-λ KOs: {len(high_lam_kos)}")

# Merge env covariates into pgls
env_sub = env[['genus_lower', 'median_temp_range_C', 'median_soil_ph',
               'georoc_Cu_log', 'georoc_Ni_log', 'georoc_Cr_log',
               'georoc_Zn_log', 'georoc_Pb_log', 'median_georoc_metal_index']].copy()
df = pgls.merge(env_sub, on='genus_lower', how='left')
df = df.merge(density[['genus_lower', 'n_genomes']].drop_duplicates(), on='genus_lower', how='left')

# z-score all variables
for col in ['median_temp_range_C', 'median_soil_ph', 'georoc_Cu_log', 'georoc_Ni_log',
            'georoc_Cr_log', 'georoc_Zn_log', 'georoc_Pb_log',
            'median_georoc_metal_index', 'mean_genome_mb',
            'translation_per_mb', 'replication_repair_per_mb',
            'cofactor_per_mb', 'resistance_per_mb']:
    if col in df.columns:
        df[f'{col}_z'] = _z(df[col])

df['ko_per_mb_z'] = _z(df['ko_per_mb_primary'])
df['gsize_z'] = _z(df['mean_genome_mb'])

print(f"  Main dataset n={len(df)}")
print()

all_results = []


# ═══════════════════════════════════════════════════════════════════════════
# H5c: BacMet-canonical vs fitness-only resistance subcategory split
# ═══════════════════════════════════════════════════════════════════════════

print("══ H5c: BacMet canonical vs fitness-only resistance split ══")

# Identify BacMet-sourced and fitness-only resistance KOs (Tier 1+2)
res_kos = ko_meta[(ko_meta['is_resistance'] == True)].copy()
# Tier filter: keep Tier 1, 2, 2-Fitness
res_kos = res_kos[res_kos['evidence_tier'].isin(['Tier 1', 'Tier 2', 'Tier 2-Fitness'])]
bacmet_kos   = res_kos[res_kos['source_bacmet'].notna()]['KO'].tolist()
fitness_only = res_kos[(res_kos['source_bacmet'].isna()) &
                       (res_kos['source_fitness'].notna())]['KO'].tolist()
both_kos     = res_kos[(res_kos['source_bacmet'].notna()) &
                       (res_kos['source_fitness'].notna())]['KO'].tolist()

print(f"  BacMet-annotated resistance KOs: {len(bacmet_kos)}")
print(f"  Fitness-only resistance KOs: {len(fitness_only)}")
print(f"  Both sources: {len(both_kos)}")

# Compute per-genus density for each subgroup using nb25
def compute_density(nb25_df, ko_list, density_df, col_name):
    """Compute per-genus mean KO density (KOs per Mb) for a KO subgroup."""
    sub = nb25_df[nb25_df['ko'].isin(ko_list)].copy()
    if len(sub) == 0:
        return pd.DataFrame(columns=['genus_lower', col_name])
    # n_genomes_with_ko -> merge with total n_genomes per genus
    sub = sub.merge(density_df[['genus_lower', 'n_genomes', 'mean_genome_mb']].drop_duplicates(),
                    on='genus_lower', how='left')
    sub['presence_frac'] = sub['n_genomes_with_ko'] / sub['n_genomes'].clip(lower=1)
    # Sum presence fractions across KOs in subgroup, divide by genome size
    grp = sub.groupby('genus_lower').agg(
        total_presence=('presence_frac', 'sum'),
        n_kos=('ko', 'count'),
        mean_genome_mb=('mean_genome_mb', 'first')
    ).reset_index()
    grp[col_name] = grp['total_presence'] / grp['mean_genome_mb'].clip(lower=0.01)
    return grp[['genus_lower', col_name]]

density_aug = density[['genus_lower', 'n_genomes', 'mean_genome_mb']].drop_duplicates()
bacmet_dens  = compute_density(nb25, bacmet_kos,  density_aug, 'bacmet_res_density')
fitonly_dens = compute_density(nb25, fitness_only, density_aug, 'fitonly_res_density')

df = df.merge(bacmet_dens,  on='genus_lower', how='left')
df = df.merge(fitonly_dens, on='genus_lower', how='left')
df['bacmet_res_z']  = _z(df['bacmet_res_density'])
df['fitonly_res_z'] = _z(df['fitonly_res_density'])

print(f"\n  BacMet resistance density n_nonzero={df['bacmet_res_density'].gt(0).sum()}")
print(f"  Fitness-only resistance density n_nonzero={df['fitonly_res_density'].gt(0).sum()}")

print("\n  Reference: all resistance KOs (already computed)")
all_results.append(run_model(df, 'H5c_REF resistance_per_mb ~ B_std',
    'mean_levins_B_std', ['resistance_per_mb_z', 'gsize_z'], focal='resistance_per_mb_z'))

print("  BacMet-canonical resistance ~ niche breadth")
all_results.append(run_model(df, 'H5c_BacMet resistance density ~ B_std',
    'mean_levins_B_std', ['bacmet_res_z', 'gsize_z'], focal='bacmet_res_z'))

print("  Fitness-only (pleiotropic) resistance ~ niche breadth")
all_results.append(run_model(df, 'H5c_FitOnly resistance density ~ B_std',
    'mean_levins_B_std', ['fitonly_res_z', 'gsize_z'], focal='fitonly_res_z'))

# Joint model: bacmet + fitonly
print("  Joint model: B_std ~ bacmet_res_z + fitonly_res_z + gsize_z")
all_results.append(run_model(df, 'H5c_joint BacMet coeff',
    'mean_levins_B_std', ['bacmet_res_z', 'fitonly_res_z', 'gsize_z'], focal='bacmet_res_z'))
all_results.append(run_model(df, 'H5c_joint FitOnly coeff',
    'mean_levins_B_std', ['bacmet_res_z', 'fitonly_res_z', 'gsize_z'], focal='fitonly_res_z'))

# Cofactor reference model
print("  REFERENCE: cofactor density ~ B_std")
all_results.append(run_model(df, 'H5c_REF cofactor_per_mb ~ B_std',
    'mean_levins_B_std', ['cofactor_per_mb_z', 'gsize_z'], focal='cofactor_per_mb_z'))

# Check if BacMet or FitOnly resistance correlates with cofactor
r_bacmet_cofactor, p_bc = stats.spearmanr(
    df['bacmet_res_density'].dropna(),
    df.loc[df['bacmet_res_density'].notna(), 'cofactor_per_mb'].fillna(0))
r_fitonly_cofactor, p_fc = stats.spearmanr(
    df['fitonly_res_density'].dropna(),
    df.loc[df['fitonly_res_density'].notna(), 'cofactor_per_mb'].fillna(0))
print(f"\n  ρ(bacmet_res, cofactor_per_mb) = {r_bacmet_cofactor:.3f} (p={p_bc:.3g})")
print(f"  ρ(fitonly_res, cofactor_per_mb) = {r_fitonly_cofactor:.3f} (p={p_fc:.3g})")

h5c_summary = {
    'bacmet_kos': bacmet_kos,
    'fitness_only_kos': fitness_only,
    'r_bacmet_cofactor': r_bacmet_cofactor,
    'r_fitonly_cofactor': r_fitonly_cofactor,
}


# ═══════════════════════════════════════════════════════════════════════════
# H1b: Environmental range × double-signal gene burden
# ═══════════════════════════════════════════════════════════════════════════

print("\n══ H1b: Environmental range × double-signal gene burden ══")

# Compute per-genus double-signal gene presence count from nb25
def compute_presence_fraction(nb25_df, ko_list, density_df):
    """Compute per-genus mean presence fraction and burden for a KO set."""
    sub = nb25_df[nb25_df['ko'].isin(ko_list)].copy()
    sub = sub.merge(density_df[['genus_lower', 'n_genomes']].drop_duplicates(),
                    on='genus_lower', how='left')
    sub['presence_frac'] = sub['n_genomes_with_ko'] / sub['n_genomes'].clip(lower=1)
    grp = sub.groupby('genus_lower').agg(
        n_kos_present_50=('presence_frac', lambda x: (x > 0.5).sum()),
        mean_presence_frac=('presence_frac', 'mean'),
        n_kos_any=('presence_frac', lambda x: (x > 0).sum()),
    ).reset_index()
    return grp

ds_presence   = compute_presence_fraction(nb25, double_signal_kos, density_aug)
hiL_presence  = compute_presence_fraction(nb25, high_lam_kos, density_aug)

ds_presence.columns  = ['genus_lower', 'ds_n_kos_50', 'ds_mean_pres', 'ds_n_kos_any']
hiL_presence.columns = ['genus_lower', 'hiL_n_kos_50', 'hiL_mean_pres', 'hiL_n_kos_any']

df = df.merge(ds_presence,  on='genus_lower', how='left')
df = df.merge(hiL_presence, on='genus_lower', how='left')

for c in ['ds_n_kos_50', 'ds_mean_pres', 'ds_n_kos_any', 'hiL_n_kos_50', 'hiL_mean_pres', 'hiL_n_kos_any']:
    df[f'{c}_z'] = _z(df[c])

df['temp_range_z'] = _z(df['median_temp_range_C'])
df['pH_z']         = _z(df['median_soil_ph'])
df['Cu_log_z']     = _z(df['georoc_Cu_log'])
df['Cr_log_z']     = _z(df['georoc_Cr_log'])
df['metal_idx_z']  = _z(df['median_georoc_metal_index'])

n_ds  = df['ds_n_kos_50'].notna().sum()
n_hiL = df['hiL_n_kos_50'].notna().sum()
print(f"  Double-signal: n_genera with ≥1 KO present at >50%: {df['ds_n_kos_50'].gt(0).sum()}")
print(f"  High-λ:        n_genera with ≥1 KO present at >50%: {df['hiL_n_kos_50'].gt(0).sum()}")

print("\n  [H1b-1] ds_n_kos_50 ~ temp_range_z + gsize_z")
all_results.append(run_model(df, 'H1b_ds_burden ~ temp_range + gsize',
    'ds_n_kos_50', ['temp_range_z', 'gsize_z'], focal='temp_range_z'))

print("  [H1b-2] ds_n_kos_50 ~ pH_z + gsize_z")
all_results.append(run_model(df, 'H1b_ds_burden ~ pH + gsize',
    'ds_n_kos_50', ['pH_z', 'gsize_z'], focal='pH_z'))

print("  [H1b-3] ds_n_kos_50 ~ Cu_log_z + gsize_z")
all_results.append(run_model(df, 'H1b_ds_burden ~ Cu_log + gsize',
    'ds_n_kos_50', ['Cu_log_z', 'gsize_z'], focal='Cu_log_z'))

print("  [H1b-4] ds_n_kos_50 ~ Cr_log_z + gsize_z")
all_results.append(run_model(df, 'H1b_ds_burden ~ Cr_log + gsize',
    'ds_n_kos_50', ['Cr_log_z', 'gsize_z'], focal='Cr_log_z'))

print("  [H1b-5] ds_n_kos_50 ~ metal_idx_z + gsize_z")
all_results.append(run_model(df, 'H1b_ds_burden ~ metal_index + gsize',
    'ds_n_kos_50', ['metal_idx_z', 'gsize_z'], focal='metal_idx_z'))

print("  [H1b-6] ds_n_kos_50 ~ temp_range_z + pH_z + Cu_log_z + gsize_z  (joint)")
all_results.append(run_model(df, 'H1b_joint ds_burden ~ temp_range (focal)',
    'ds_n_kos_50', ['temp_range_z', 'pH_z', 'Cu_log_z', 'gsize_z'], focal='temp_range_z'))
all_results.append(run_model(df, 'H1b_joint ds_burden ~ pH (focal)',
    'ds_n_kos_50', ['temp_range_z', 'pH_z', 'Cu_log_z', 'gsize_z'], focal='pH_z'))
all_results.append(run_model(df, 'H1b_joint ds_burden ~ Cu_log (focal)',
    'ds_n_kos_50', ['temp_range_z', 'pH_z', 'Cu_log_z', 'gsize_z'], focal='Cu_log_z'))

print("  [H1b-7] high-λ burden ~ temp_range_z + gsize_z")
all_results.append(run_model(df, 'H1b_hiL_burden ~ temp_range + gsize',
    'hiL_n_kos_50', ['temp_range_z', 'gsize_z'], focal='temp_range_z'))

# Also: does double-signal burden predict niche breadth independently?
print("\n  [H1b-8] B_std ~ ds_n_kos_50_z + gsize_z")
all_results.append(run_model(df, 'H1b_B_std ~ ds_burden + gsize',
    'mean_levins_B_std', ['ds_n_kos_50_z', 'gsize_z'], focal='ds_n_kos_50_z'))


# ═══════════════════════════════════════════════════════════════════════════
# H1a: Per-gene env associations — double-signal vs high-λ (pH, temp_range)
# ═══════════════════════════════════════════════════════════════════════════

print("\n══ H1a: Per-gene PGLS: pH/temp associations for double-signal vs high-λ ══")

# For each gene in each set, compute per-genus presence fraction, then PGLS
# presence_frac ~ pH_z + temp_range_z + gsize_z

# Build genus-level presence fraction matrix for all target KOs
all_target_kos = double_signal_kos + high_lam_kos
nb25_target = nb25[nb25['ko'].isin(all_target_kos)].copy()
nb25_target = nb25_target.merge(density_aug[['genus_lower', 'n_genomes']], on='genus_lower', how='left')
nb25_target['presence_frac'] = nb25_target['n_genomes_with_ko'] / nb25_target['n_genomes'].clip(lower=1)

# Build per-genus base df with env covariates
base_df = df[['genus_lower', 'mean_genome_mb', 'gsize_z',
              'temp_range_z', 'pH_z', 'Cu_log_z', 'Cr_log_z']].dropna(
    subset=['temp_range_z', 'pH_z', 'gsize_z'])

per_gene_results = []
for ko_id in all_target_kos:
    ko_sub = nb25_target[nb25_target['ko'] == ko_id][['genus_lower', 'presence_frac']].copy()
    merged = base_df.merge(ko_sub, on='genus_lower', how='left')
    merged['presence_frac'] = merged['presence_frac'].fillna(0)
    n_nonzero = (merged['presence_frac'] > 0).sum()
    n = len(merged)
    gene_meta = merged_phylo[merged_phylo['ko_id'] == ko_id]
    gene_name = gene_meta['gene_name_x'].iloc[0] if len(gene_meta) > 0 else ko_id
    gene_type = 'double_signal' if ko_id in double_signal_kos else 'high_lambda'

    if n_nonzero < 30:
        per_gene_results.append({'ko_id': ko_id, 'gene_name': gene_name, 'gene_type': gene_type,
                                  'n': n, 'n_nonzero': n_nonzero,
                                  'beta_pH': np.nan, 'p_pH': np.nan,
                                  'beta_temp': np.nan, 'p_temp': np.nan,
                                  'beta_Cu': np.nan, 'p_Cu': np.nan})
        print(f"  SKIP {ko_id} ({gene_name}): n_nonzero={n_nonzero} < 30")
        continue

    print(f"  {ko_id} ({gene_name}, {gene_type}):", end='')
    valid = merged.dropna(subset=['presence_frac', 'temp_range_z', 'pH_z', 'gsize_z', 'Cu_log_z'])
    n_valid = len(valid)

    # Run PGLS: presence_frac ~ pH_z + temp_range_z + Cu_log_z + gsize_z
    if n_valid >= MIN_N:
        res = run_pgls(valid, TREE, response='presence_frac',
                       predictors=['pH_z', 'temp_range_z', 'Cu_log_z', 'gsize_z'],
                       taxon_col='genus_lower', label=f'{ko_id}_env', min_n=MIN_N)
        b_pH, _, p_pH, _ = _extract(res, 'pH_z')
        b_temp, _, p_temp, _ = _extract(res, 'temp_range_z')
        b_Cu, _, p_Cu, _ = _extract(res, 'Cu_log_z')
        print(f" pH β={b_pH:+.4f} p={p_pH:.3g} | temp β={b_temp:+.4f} p={p_temp:.3g} | Cu β={b_Cu:+.4f} p={p_Cu:.3g}")
    else:
        b_pH = b_temp = b_Cu = p_pH = p_temp = p_Cu = np.nan
        print(f" n_valid={n_valid} too small")

    per_gene_results.append({'ko_id': ko_id, 'gene_name': gene_name, 'gene_type': gene_type,
                              'n': n_valid, 'n_nonzero': n_nonzero,
                              'beta_pH': b_pH, 'p_pH': p_pH,
                              'beta_temp': b_temp, 'p_temp': p_temp,
                              'beta_Cu': b_Cu, 'p_Cu': p_Cu})

pg_df = pd.DataFrame(per_gene_results)
pg_df.to_csv(DATA / 'per_gene_env_pgls.csv', index=False)

# Compare β distributions between gene types
for met in ['pH', 'temp', 'Cu']:
    ds_betas  = pg_df[(pg_df['gene_type'] == 'double_signal') & pg_df[f'beta_{met}'].notna()][f'beta_{met}']
    hiL_betas = pg_df[(pg_df['gene_type'] == 'high_lambda')  & pg_df[f'beta_{met}'].notna()][f'beta_{met}']
    if len(ds_betas) >= 3 and len(hiL_betas) >= 3:
        stat, p_mwu = stats.mannwhitneyu(ds_betas, hiL_betas, alternative='two-sided')
        print(f"\n  {met}: DS mean_β={ds_betas.mean():+.4f} (n={len(ds_betas)}) | "
              f"HiL mean_β={hiL_betas.mean():+.4f} (n={len(hiL_betas)}) | "
              f"MWU p={p_mwu:.3g}")
    else:
        print(f"\n  {met}: insufficient data (DS n={len(ds_betas)}, HiL n={len(hiL_betas)})")

pg_summary = pg_df


# ═══════════════════════════════════════════════════════════════════════════
# H4c: Cofactor signal controlling for housekeeping landscape
# ═══════════════════════════════════════════════════════════════════════════

print("\n══ H4c: Cofactor signal controlling for housekeeping landscape ══")

print("  Reference: B_std ~ cofactor_z + gsize_z")
all_results.append(run_model(df, 'H4c_REF cofactor ~ B_std',
    'mean_levins_B_std', ['cofactor_per_mb_z', 'gsize_z'], focal='cofactor_per_mb_z'))

print("  [H4c-1] B_std ~ cofactor_z + translation_z + gsize_z")
all_results.append(run_model(df, 'H4c_1 cofactor + translation (cofactor)',
    'mean_levins_B_std', ['cofactor_per_mb_z', 'translation_per_mb_z', 'gsize_z'],
    focal='cofactor_per_mb_z'))
all_results.append(run_model(df, 'H4c_1 cofactor + translation (translation)',
    'mean_levins_B_std', ['cofactor_per_mb_z', 'translation_per_mb_z', 'gsize_z'],
    focal='translation_per_mb_z'))

print("  [H4c-2] B_std ~ cofactor_z + replication_repair_z + gsize_z")
all_results.append(run_model(df, 'H4c_2 cofactor + replication (cofactor)',
    'mean_levins_B_std', ['cofactor_per_mb_z', 'replication_repair_per_mb_z', 'gsize_z'],
    focal='cofactor_per_mb_z'))
all_results.append(run_model(df, 'H4c_2 cofactor + replication (replication)',
    'mean_levins_B_std', ['cofactor_per_mb_z', 'replication_repair_per_mb_z', 'gsize_z'],
    focal='replication_repair_per_mb_z'))

print("  [H4c-3] Full joint: cofactor + translation + replication + gsize")
all_results.append(run_model(df, 'H4c_3 joint (cofactor)',
    'mean_levins_B_std',
    ['cofactor_per_mb_z', 'translation_per_mb_z', 'replication_repair_per_mb_z', 'gsize_z'],
    focal='cofactor_per_mb_z'))
all_results.append(run_model(df, 'H4c_3 joint (translation)',
    'mean_levins_B_std',
    ['cofactor_per_mb_z', 'translation_per_mb_z', 'replication_repair_per_mb_z', 'gsize_z'],
    focal='translation_per_mb_z'))
all_results.append(run_model(df, 'H4c_3 joint (replication)',
    'mean_levins_B_std',
    ['cofactor_per_mb_z', 'translation_per_mb_z', 'replication_repair_per_mb_z', 'gsize_z'],
    focal='replication_repair_per_mb_z'))

# Spearman correlations between cofactor and housekeeping
for hk in ['translation_per_mb', 'replication_repair_per_mb']:
    if hk in df.columns:
        r, p = stats.spearmanr(df['cofactor_per_mb'].dropna(),
                               df.loc[df['cofactor_per_mb'].notna(), hk].fillna(0))
        print(f"  ρ(cofactor, {hk.replace('_per_mb','')}) = {r:.3f} (p={p:.3g})")


# ═══════════════════════════════════════════════════════════════════════════
# H3b: Double-signal burden × metal exposure across geographic range
# ═══════════════════════════════════════════════════════════════════════════

print("\n══ H3b: Double-signal burden × metal exposure ══")

# Prediction: genera carrying more double-signal genes occupy geochemically
# richer environments (higher Cu, Cr, composite metal index)

print("  [H3b-1] ds_burden ~ Cu_log_z + gsize_z")
all_results.append(run_model(df, 'H3b_1 ds_burden ~ Cu_log + gsize',
    'ds_n_kos_50', ['Cu_log_z', 'gsize_z'], focal='Cu_log_z'))

print("  [H3b-2] ds_burden ~ Cr_log_z + gsize_z")
all_results.append(run_model(df, 'H3b_2 ds_burden ~ Cr_log + gsize',
    'ds_n_kos_50', ['Cr_log_z', 'gsize_z'], focal='Cr_log_z'))

print("  [H3b-3] ds_burden ~ metal_idx_z + pH_z + gsize_z")
all_results.append(run_model(df, 'H3b_3 ds_burden ~ metal_index + pH (metal_idx)',
    'ds_n_kos_50', ['metal_idx_z', 'pH_z', 'gsize_z'], focal='metal_idx_z'))
all_results.append(run_model(df, 'H3b_3 ds_burden ~ metal_index + pH (pH)',
    'ds_n_kos_50', ['metal_idx_z', 'pH_z', 'gsize_z'], focal='pH_z'))

print("  [H3b-4] high-λ_burden ~ Cu_log_z + gsize_z (control)")
all_results.append(run_model(df, 'H3b_4 hiL_burden ~ Cu_log + gsize (control)',
    'hiL_n_kos_50', ['Cu_log_z', 'gsize_z'], focal='Cu_log_z'))

print("  [H3b-5] high-λ_burden ~ metal_idx_z + gsize_z (control)")
all_results.append(run_model(df, 'H3b_5 hiL_burden ~ metal_index + gsize (control)',
    'hiL_n_kos_50', ['metal_idx_z', 'gsize_z'], focal='metal_idx_z'))

# Spearman as non-phylogenetic check
for col in ['Cu_log_z', 'Cr_log_z', 'metal_idx_z', 'pH_z']:
    if col in df.columns:
        r, p = stats.spearmanr(df['ds_n_kos_50'].dropna(),
                               df.loc[df['ds_n_kos_50'].notna(), col])
        print(f"  ρ(ds_burden, {col}) = {r:+.3f} (p={p:.3g})")

# Test: does ds_burden predict niche breadth controlling for metal exposure?
print("\n  [H3b-6] B_std ~ ds_burden_z + metal_idx_z + gsize_z  (mediation check)")
all_results.append(run_model(df, 'H3b_6 B_std ~ ds_burden + metal_idx (ds_burden)',
    'mean_levins_B_std', ['ds_n_kos_50_z', 'metal_idx_z', 'gsize_z'], focal='ds_n_kos_50_z'))
all_results.append(run_model(df, 'H3b_6 B_std ~ ds_burden + metal_idx (metal_idx)',
    'mean_levins_B_std', ['ds_n_kos_50_z', 'metal_idx_z', 'gsize_z'], focal='metal_idx_z'))


# ─── Save PGLS results ──────────────────────────────────────────────────────

res_df = pd.DataFrame(all_results)
res_df.to_csv(DATA / 'untested_hypotheses_results.csv', index=False)
print(f"\n  Saved: data/untested_hypotheses_results.csv ({len(res_df)} rows)")


# ─── Generate report ─────────────────────────────────────────────────────────

print("\n── Generating report ──")

# Helper to retrieve result row
def _r(label):
    row = res_df[res_df['label'].str.startswith(label)]
    return row.iloc[0] if len(row) > 0 else None

def _fmtr(r, default='n/a'):
    if r is None or pd.isna(r['beta']): return default
    ps = ('***' if r['p'] < 0.001 else '**' if r['p'] < 0.01 else '*' if r['p'] < 0.05
          else '†' if r['p'] < 0.10 else 'NS')
    return f"β={r['beta']:+.4f} SE={r['SE']:.4f} p={r['p']:.3g}{ps} n={r['n']:.0f}"

def sig(r):
    if r is None or pd.isna(r['p']): return 'n/a'
    if r['p'] < 0.001: return '***'
    if r['p'] < 0.01: return '**'
    if r['p'] < 0.05: return '*'
    if r['p'] < 0.10: return '†'
    return 'NS'

# Per-gene results table
pg_ds  = pg_df[pg_df['gene_type'] == 'double_signal'].sort_values('p_pH')
pg_hiL = pg_df[pg_df['gene_type'] == 'high_lambda'].sort_values('p_pH')

# Compute MWU p-values for summary
mwu_results = {}
for met in ['pH', 'temp', 'Cu']:
    ds_b  = pg_df[(pg_df['gene_type'] == 'double_signal') & pg_df[f'beta_{met}'].notna()][f'beta_{met}']
    hiL_b = pg_df[(pg_df['gene_type'] == 'high_lambda')   & pg_df[f'beta_{met}'].notna()][f'beta_{met}']
    if len(ds_b) >= 3 and len(hiL_b) >= 3:
        _, p_mwu = stats.mannwhitneyu(ds_b, hiL_b, alternative='two-sided')
        mwu_results[met] = {'ds_mean': ds_b.mean(), 'hiL_mean': hiL_b.mean(),
                            'ds_n': len(ds_b), 'hiL_n': len(hiL_b), 'p_mwu': p_mwu}
    else:
        mwu_results[met] = None

# Build per-gene table
pg_rows = []
for _, row in pg_df.iterrows():
    ds = merged_phylo[merged_phylo['ko_id'] == row['ko_id']]
    D_val  = f"{ds['D'].iloc[0]:.3f}" if len(ds) > 0 else 'n/a'
    lam_val = f"{ds['lambda'].iloc[0]:.3f}" if len(ds) > 0 else 'n/a'
    def fmtb(b, p):
        if pd.isna(b): return 'NA'
        ps = ('***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05
              else '†' if p < 0.10 else 'NS')
        return f"{b:+.4f} ({ps})"
    pg_rows.append(
        f"| {row['ko_id']} | {row['gene_name']} | {row['gene_type'].replace('_',' ')} | "
        f"{D_val} | {lam_val} | {fmtb(row['beta_pH'], row['p_pH'])} | "
        f"{fmtb(row['beta_temp'], row['p_temp'])} | {fmtb(row['beta_Cu'], row['p_Cu'])} | {row['n']:.0f} |"
    )

# Build full PGLS table
pgls_rows = []
for _, row in res_df.iterrows():
    if pd.isna(row['beta']): continue
    ps = ('***' if row['p'] < 0.001 else '**' if row['p'] < 0.01 else '*' if row['p'] < 0.05
          else '†' if row['p'] < 0.10 else 'NS')
    pgls_rows.append(
        f"| {row['label'][:60]:<60} | {row['beta']:+.4f} | {row['SE']:.4f} | "
        f"{row['p']:.3g}{ps} | {row['n']:.0f} |"
    )


report = f"""# Untested Hypotheses — Analysis Report

**Date:** 2026-07-13
**Dataset:** n = {len(df)} genera (soil_sample_pgls_dataset.csv + env covariates)
**Tree:** GTDB r214 bacteria (genus-pruned). Pagel's λ optimised by ML.

This report documents 5 novel hypotheses not previously tested in the manuscript,
along with statistical results and manuscript recommendations.

---

## Hypothesis H5c — BacMet-canonical vs fitness-only resistance subcategory split

**Question:** Is the resistance-null (resistance genes do not predict niche breadth)
uniform across all resistance KOs, or does it mask heterogeneity between canonical
metal resistance (BacMet-annotated) and pleiotropic fitness-detected genes?

**Rationale:** The 23 Tier 1+2 resistance KOs include classical metal-efflux genes
(cusA, czcA, merR — BacMet-annotated, mechanistically characterised) and genes
detected only by fitness assays as pleiotropic stress responders (fadJ, galE, rpoE,
manA, hisA — no BacMet entry). If only one subgroup drives the null result, the
other may be biologically distinct.

**Gene sets:**
- BacMet-canonical (n = {len(bacmet_kos)} KOs): {', '.join(ko_meta[ko_meta['KO'].isin(bacmet_kos)]['gene_name'].tolist())}
- Fitness-only pleiotropic (n = {len(fitness_only)} KOs): {', '.join(ko_meta[ko_meta['KO'].isin(fitness_only)]['gene_name'].tolist())}

**PGLS results (all models: response = mean_levins_B_std):**

| Model | β | SE | p | n |
|---|---|---|---|---|
| REF all resistance | {_fmtr(_r('H5c_REF resistance_per_mb'))} |
| BacMet canonical | {_fmtr(_r('H5c_BacMet resistance'))} |
| Fitness-only pleiotropic | {_fmtr(_r('H5c_FitOnly resistance'))} |
| Joint (BacMet coeff) | {_fmtr(_r('H5c_joint BacMet'))} |
| Joint (FitOnly coeff) | {_fmtr(_r('H5c_joint FitOnly'))} |
| REF cofactor | {_fmtr(_r('H5c_REF cofactor'))} |

**Correlations:**
- ρ(BacMet resistance density, cofactor density) = {h5c_summary['r_bacmet_cofactor']:.3f}
- ρ(fitness-only resistance density, cofactor density) = {h5c_summary['r_fitonly_cofactor']:.3f}

**Interpretation and result:**
"""

# Determine H5c verdict
r_bacmet_res = _r('H5c_BacMet resistance')
r_fitonly_res = _r('H5c_FitOnly resistance')
bacmet_sig = r_bacmet_res is not None and not pd.isna(r_bacmet_res['p']) and r_bacmet_res['p'] < 0.05
fitonly_sig = r_fitonly_res is not None and not pd.isna(r_fitonly_res['p']) and r_fitonly_res['p'] < 0.05

if not bacmet_sig and not fitonly_sig:
    report += """Both subcategories are null: neither BacMet-canonical nor fitness-only
resistance genes predict niche breadth. The resistance null is robust across
mechanistically distinct resistance KO types. **HYPOTHESIS NOT SUPPORTED** —
the null is not a subgroup artefact.

**Manuscript recommendation:** Confirm and strengthen the resistance-null result
with the sentence: "The resistance null holds in both BacMet-annotated canonical
resistance genes (p = NS) and fitness-detected pleiotropic resistance genes
(p = NS), ruling out subgroup cancellation effects."
"""
elif bacmet_sig and not fitonly_sig:
    report += """BacMet-canonical genes are significant, fitness-only genes are null.
**HYPOTHESIS PARTIALLY SUPPORTED** — canonical metal resistance does predict niche
breadth, while pleiotropic fitness-detected genes do not.

**Manuscript recommendation:** Split the resistance category and report each subgroup.
"""
elif not bacmet_sig and fitonly_sig:
    report += """BacMet-canonical genes are null, fitness-only genes are significant.
**HYPOTHESIS PARTIALLY SUPPORTED** — the "resistance" signal is driven entirely by
pleiotropic fitness-detected genes, not by canonical metal resistance mechanisms.

**Manuscript recommendation:** This is a major finding — the apparent resistance
signal comes from pleiotropic metabolism, not metal-specific resistance per se.
"""
else:
    report += """Both subcategories significant. **HYPOTHESIS NOT SUPPORTED** in its
original form — both types predict niche breadth.
"""

report += f"""
---

## Hypothesis H1b — Environmental range × double-signal gene burden

**Question:** Do genera carrying more double-signal (HGT-prone) metal resistance genes
tend to occupy environments with greater temperature or metal variability (higher
temp_range, higher GeoROC Cu/Cr exposure)?

**Rationale:** HGT-prone resistance genes should accumulate preferentially in
genera exposed to fluctuating metal stress — environments where horizontal acquisition
confers fitness advantage. Temperature range proxies habitat heterogeneity.

**Double-signal gene burden** = number of double-signal KOs with presence fraction > 50%
in a genus (range 0–{int(df['ds_n_kos_50'].max())} per genus; {df['ds_n_kos_50'].gt(0).sum()} genera carry ≥1).

| Model | focal β | p | n |
|---|---|---|---|
| ds_burden ~ temp_range_z | {_fmtr(_r('H1b_ds_burden ~ temp_range'))} |
| ds_burden ~ pH_z | {_fmtr(_r('H1b_ds_burden ~ pH'))} |
| ds_burden ~ Cu_log_z | {_fmtr(_r('H1b_ds_burden ~ Cu_log'))} |
| ds_burden ~ Cr_log_z | {_fmtr(_r('H1b_ds_burden ~ Cr_log'))} |
| ds_burden ~ metal_index_z | {_fmtr(_r('H1b_ds_burden ~ metal_index'))} |
| Joint: temp_range focal | {_fmtr(_r('H1b_joint ds_burden ~ temp_range'))} |
| Joint: pH focal | {_fmtr(_r('H1b_joint ds_burden ~ pH'))} |
| Joint: Cu_log focal | {_fmtr(_r('H1b_joint ds_burden ~ Cu_log'))} |
| hiL_burden ~ temp_range_z (control) | {_fmtr(_r('H1b_hiL_burden ~ temp_range'))} |
| B_std ~ ds_burden_z | {_fmtr(_r('H1b_B_std ~ ds_burden'))} |

**Interpretation:**
"""

r_ds_temp = _r('H1b_ds_burden ~ temp_range')
r_ds_Cu   = _r('H1b_ds_burden ~ Cu_log')
r_ds_ph   = _r('H1b_ds_burden ~ pH')
r_ds_Bstd = _r('H1b_B_std ~ ds_burden')

sig_temp = r_ds_temp is not None and not pd.isna(r_ds_temp['p']) and r_ds_temp['p'] < 0.05
sig_Cu   = r_ds_Cu   is not None and not pd.isna(r_ds_Cu['p'])   and r_ds_Cu['p']   < 0.05
sig_ph   = r_ds_ph   is not None and not pd.isna(r_ds_ph['p'])   and r_ds_ph['p']   < 0.05
sig_Bstd = r_ds_Bstd is not None and not pd.isna(r_ds_Bstd['p']) and r_ds_Bstd['p'] < 0.05

report += f"""Double-signal gene burden {"does" if (sig_temp or sig_Cu or sig_ph) else "does NOT"}
significantly predict environmental variables. The double-signal burden {"predicts" if sig_Bstd else "does not predict"}
niche breadth.

**Manuscript recommendation:**
"""
if sig_temp or sig_Cu:
    report += "Report as a novel finding supporting the environmental selection hypothesis for HGT-prone metal resistance genes.\n"
else:
    report += ("The null result indicates HGT-prone gene burden is not driven by measurable "
               "environmental metal/temperature gradients at the genus level. This is a meaningful "
               "null — the double-signal classification reflects phylogenetic properties (D, λ), "
               "not environmental exposure per se. Report as a limitation of the HGT framework.\n")

report += f"""
---

## Hypothesis H1a — Per-gene pH/temperature associations: double-signal vs high-λ

**Question:** Do double-signal (HGT-prone, D>0.2 AND λ<0.3) genes show stronger
associations with pH and temperature range than high-λ (vertically inherited) genes?
This would indicate that double-signal genes are environmentally filtered differently.

**Method:** For each gene in both sets, PGLS of presence_fraction ~
pH_z + temp_range_z + Cu_log_z + genome_size_z. Compare β distributions between
gene types using Mann–Whitney U test.

**Per-gene results:**

| KO | Gene | Type | D | λ | β_pH | β_temp | β_Cu | n |
|---|---|---|---|---|---|---|---|---|
{chr(10).join(pg_rows)}

**Mann–Whitney U comparison (double-signal vs high-λ):**

| Env variable | DS mean β | HiL mean β | DS n | HiL n | p_MWU |
|---|---|---|---|---|---|
"""
for met, label in [('pH', 'Soil pH'), ('temp', 'Temp range'), ('Cu', 'GeoROC Cu')]:
    r = mwu_results.get(met)
    if r:
        report += (f"| {label} | {r['ds_mean']:+.4f} | {r['hiL_mean']:+.4f} | "
                   f"{r['ds_n']} | {r['hiL_n']} | {r['p_mwu']:.3g} |\n")
    else:
        report += f"| {label} | NA | NA | NA | NA | NA |\n"

report += """
**Interpretation:** If double-signal genes have significantly different environmental
β values than high-λ genes, this would support the idea that they respond to different
ecological filters (environmental variability vs phylogenetic ancestry).

**Manuscript recommendation:** Include as Supplementary Table if significant. The
per-gene PGLS approach provides mechanistic granularity for the double-signal framework.

---

## Hypothesis H4c — Cofactor signal controlling for housekeeping landscape

**Question:** Does the cofactor biosynthesis signal survive when translation (the
strongest housekeeping predictor) and replication/repair are included as co-predictors?
This tests whether cofactor is acting as a proxy for overall metabolic complexity.

**Context:** Translation density is the 2nd-strongest KEGG category predictor
(stronger than metal genes; from the functional landscape analysis). If cofactor and
translation are collinear, the cofactor signal may just reflect metabolic richness.

| Model | focal | β | p | n |
|---|---|---|---|---|
| REF: B_std ~ cofactor_z | cofactor | {_fmtr(_r('H4c_REF cofactor'))} |
| B_std ~ cofactor_z + translation_z | cofactor | {_fmtr(_r('H4c_1 cofactor + translation (cofactor)'))} |
| B_std ~ cofactor_z + translation_z | translation | {_fmtr(_r('H4c_1 cofactor + translation (translation)'))} |
| B_std ~ cofactor_z + replication_z | cofactor | {_fmtr(_r('H4c_2 cofactor + replication (cofactor)'))} |
| B_std ~ cofactor_z + replication_z | replication | {_fmtr(_r('H4c_2 cofactor + replication (replication)'))} |
| Full joint (cofactor) | cofactor | {_fmtr(_r('H4c_3 joint (cofactor)'))} |
| Full joint (translation) | translation | {_fmtr(_r('H4c_3 joint (translation)'))} |
| Full joint (replication) | replication | {_fmtr(_r('H4c_3 joint (replication)'))} |

**Interpretation:**
"""

r_cof_trans  = _r('H4c_1 cofactor + translation (cofactor)')
r_cof_rep    = _r('H4c_2 cofactor + replication (cofactor)')
r_cof_joint  = _r('H4c_3 joint (cofactor)')

cof_trans_sig  = r_cof_trans  is not None and not pd.isna(r_cof_trans['p'])  and r_cof_trans['p']  < 0.05
cof_rep_sig    = r_cof_rep    is not None and not pd.isna(r_cof_rep['p'])    and r_cof_rep['p']    < 0.05
cof_joint_sig  = r_cof_joint  is not None and not pd.isna(r_cof_joint['p']) and r_cof_joint['p'] < 0.05

if cof_trans_sig and cof_rep_sig and cof_joint_sig:
    report += """Cofactor signal survives all controls. The cofactor–niche breadth association
is independent of translation and replication/repair density. **HYPOTHESIS REJECTED** —
the cofactor signal is not a housekeeping confound.

**Manuscript recommendation:** Add this as a robustness check. State that "the cofactor
biosynthesis association with niche breadth is independent of translation (β = NS) and
replication/repair density (β = NS) when included jointly."
"""
elif cof_trans_sig and not cof_joint_sig:
    report += """Cofactor survives controlling for replication but is attenuated in the
full joint model with translation. Partial confounding. **HYPOTHESIS PARTIALLY SUPPORTED.**
"""
else:
    report += """Cofactor signal {("attenuated to NS" if not cof_trans_sig else "survives")}
when controlling for translation. **REVIEW SPECIFIC VALUES ABOVE.**
"""

report += f"""
---

## Hypothesis H3b — Double-signal gene burden × metal exposure

**Question:** Do genera carrying more double-signal HGT-prone metal resistance genes
tend to occur in geochemically richer environments (higher bedrock Cu, Cr, or composite
metal index)? This would confirm that environmental metal selection drives HGT of these
specific resistance genes.

**Method:** PGLS of ds_burden ~ metal_exposure + gsize. Compare to high-λ genes
as a control (they should show NO metal exposure association if vertical inheritance
decouples gene content from environment).

| Model | focal β | p | n |
|---|---|---|---|
| ds_burden ~ Cu_log_z | {_fmtr(_r('H3b_1 ds_burden ~ Cu_log'))} |
| ds_burden ~ Cr_log_z | {_fmtr(_r('H3b_2 ds_burden ~ Cr_log'))} |
| ds_burden ~ metal_idx + pH (metal_idx) | {_fmtr(_r('H3b_3 ds_burden ~ metal_index + pH (metal_idx)'))} |
| ds_burden ~ metal_idx + pH (pH) | {_fmtr(_r('H3b_3 ds_burden ~ metal_index + pH (pH)'))} |
| hiL_burden ~ Cu_log_z (control) | {_fmtr(_r('H3b_4 hiL_burden ~ Cu_log'))} |
| hiL_burden ~ metal_idx (control) | {_fmtr(_r('H3b_5 hiL_burden ~ metal_index'))} |
| B_std ~ ds_burden + metal_idx (ds) | {_fmtr(_r('H3b_6 B_std ~ ds_burden + metal_idx (ds_burden)'))} |
| B_std ~ ds_burden + metal_idx (metal) | {_fmtr(_r('H3b_6 B_std ~ ds_burden + metal_idx (metal_idx)'))} |

**Interpretation:**
"""

r_ds_Cu_h3 = _r('H3b_1 ds_burden ~ Cu_log')
r_hiL_Cu_h3 = _r('H3b_4 hiL_burden ~ Cu_log')
ds_Cu_sig   = r_ds_Cu_h3   is not None and not pd.isna(r_ds_Cu_h3['p'])  and r_ds_Cu_h3['p']  < 0.05
hiL_Cu_sig  = r_hiL_Cu_h3  is not None and not pd.isna(r_hiL_Cu_h3['p']) and r_hiL_Cu_h3['p'] < 0.05

if ds_Cu_sig and not hiL_Cu_sig:
    report += """Double-signal gene burden is significantly associated with metal exposure,
while high-λ genes show no such association. **HYPOTHESIS SUPPORTED** — HGT-prone
metal resistance genes accumulate preferentially in genera occupying high-metal environments,
consistent with environmental selection driving horizontal transfer.

**Manuscript recommendation:** Include as a key mechanistic finding: "The burden of
double-signal HGT-candidate genes was positively associated with bedrock Cu exposure
across genera (β = [value], p < 0.05), while vertically inherited high-λ genes showed
no such association (p = NS), suggesting that environmental metal selection drives
acquisition of HGT-prone resistance genes."
"""
elif not ds_Cu_sig and not hiL_Cu_sig:
    report += """Neither gene type shows significant metal exposure association. **HYPOTHESIS
NOT SUPPORTED.** Environmental metal exposure (as measured by GeoROC bedrock metals) does
not predict double-signal gene burden at the genus level. This is consistent with the
mobile metal null result (CSU PF1 analysis) — genus-level metal gene content is not
driven by measurable environmental metal gradients in either direction.

**Manuscript recommendation:** Report as supporting the "phylogenetic history not
environment" interpretation — HGT-prone gene classification reflects evolutionary
dynamics (D, λ values) not ecological metal exposure.
"""
else:
    report += "Both gene types or only high-λ show association — unexpected. Review specific β values above.\n"

report += f"""
---

## Summary table

| Hypothesis | Model | n | β | p | Result |
|---|---|---|---|---|---|
"""

# Build summary table
summary_rows = [
    ('H5c', 'All resistance ~ B_std', _r('H5c_REF resistance_per_mb')),
    ('H5c', 'BacMet resistance ~ B_std', _r('H5c_BacMet resistance')),
    ('H5c', 'Fitness-only resistance ~ B_std', _r('H5c_FitOnly resistance')),
    ('H5c', 'REF cofactor ~ B_std', _r('H5c_REF cofactor')),
    ('H1b', 'ds_burden ~ temp_range', _r('H1b_ds_burden ~ temp_range')),
    ('H1b', 'ds_burden ~ pH', _r('H1b_ds_burden ~ pH')),
    ('H1b', 'ds_burden ~ Cu_log', _r('H1b_ds_burden ~ Cu_log')),
    ('H1b', 'B_std ~ ds_burden', _r('H1b_B_std ~ ds_burden')),
    ('H4c', 'cofactor ~ B_std (REF)', _r('H4c_REF cofactor')),
    ('H4c', '+ translation (cofactor)', _r('H4c_1 cofactor + translation (cofactor)')),
    ('H4c', '+ translation (translation)', _r('H4c_1 cofactor + translation (translation)')),
    ('H4c', 'joint all (cofactor)', _r('H4c_3 joint (cofactor)')),
    ('H3b', 'ds_burden ~ Cu_log', _r('H3b_1 ds_burden ~ Cu_log')),
    ('H3b', 'ds_burden ~ Cr_log', _r('H3b_2 ds_burden ~ Cr_log')),
    ('H3b', 'hiL_burden ~ Cu_log (control)', _r('H3b_4 hiL_burden ~ Cu_log')),
    ('H3b', 'B_std ~ ds_burden + metal_idx (ds)', _r('H3b_6 B_std ~ ds_burden + metal_idx (ds_burden)')),
]

for hyp, label, r in summary_rows:
    if r is None or pd.isna(r.get('beta', np.nan)):
        report += f"| {hyp} | {label} | NA | NA | NA | n/a |\n"
    else:
        ps = ('***' if r['p'] < 0.001 else '**' if r['p'] < 0.01 else '*' if r['p'] < 0.05
              else '†' if r['p'] < 0.10 else 'NS')
        verdict = ('SUPPORTED' if (r['p'] < 0.05) else 'MARGINAL' if r['p'] < 0.10 else 'NULL')
        report += (f"| {hyp} | {label} | {r['n']:.0f} | {r['beta']:+.4f} | "
                   f"{r['p']:.3g}{ps} | {verdict} |\n")

report += """
H1a results see per-gene table above.

---

## Analyses not run (data limitations)

| Hypothesis | Reason |
|---|---|
| H2a: dN/dS | No pre-computed dN/dS data available in project directory |
| H2b: Resistance gene proximity to transposases | No genome neighbourhood / gene position data available |
| H2c: KO phylogenetic age | No phylostratigraphy data or KO MRCA estimation available |
| H4a: Double-signal gene co-occurrence with AMR | Would require genome-level co-occurrence network; complex |
| H4b: Transposase density in double-signal genera | No transposase KOs in nb25 (343 KOs are all Tier 1–3 metal genes) |
| H1c: Geographic hotspots for double-signal genes | Would require sample-level presence maps; complex visualisation |
| H3b extended: Hg/As exposure | No genus-level Hg or As bedrock data in genus_lat_env_covariates.csv |
| H6b: Independent transcriptomic validation | Requires external literature search, not computationally automatable |
"""

(REPORT / 'UNTESTED_HYPOTHESES_REPORT.md').write_text(report)
print(f"  Saved: report/UNTESTED_HYPOTHESES_REPORT.md")
print("\n═══════════════════════════════════════════════════")
print("COMPLETE")
print("  data/untested_hypotheses_results.csv")
print("  data/per_gene_env_pgls.csv")
print("  report/UNTESTED_HYPOTHESES_REPORT.md")
print("═══════════════════════════════════════════════════")

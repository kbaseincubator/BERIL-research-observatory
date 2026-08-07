#!/usr/bin/env python3
"""
Pathway completeness PGLS: test whether module completeness for 8+ biosynthetic
pathways predicts cross-biome niche breadth, using the same framework as the
cobalamin completeness analysis.

Output: data/pathway_completeness_pgls.csv
"""

import sys, os, json, time, urllib.request, re
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats as sp_stats

os.environ['OMP_NUM_THREADS'] = '1'

ROOT = Path('/home/hmacgregor/BERIL-research-observatory/projects/comprehensive_metal_ecology')
DATA = ROOT / 'data'
SCRIPTS = ROOT / 'scripts'
TREE = str(DATA / 'gtdb_bac_genus_pruned.tree')

sys.path.insert(0, str(SCRIPTS))
from pgls_utils import run_pgls

# ═══════════════════════════════════════════════════════════════════════════════
# 1. KEGG module KO fetching (cached)
# ═══════════════════════════════════════════════════════════════════════════════

CACHE_DIR = DATA / 'confound_results'

def fetch_module_kos(mod_id):
    cache = CACHE_DIR / f'kegg_module_{mod_id}.json'
    if cache.exists():
        return json.loads(cache.read_text())
    url = f"https://rest.kegg.jp/link/ko/{mod_id}"
    try:
        data = urllib.request.urlopen(url, timeout=30).read().decode()
        kos = []
        for line in data.strip().split('\n'):
            parts = line.split('\t')
            if len(parts) >= 2:
                ko = parts[1].replace('ko:', '')
                kos.append(ko)
        result = sorted(set(kos))
        cache.write_text(json.dumps(result))
        time.sleep(0.35)
        return result
    except Exception:
        return []

def fetch_kegg_pathway_modules(category_keyword):
    """Fetch all KEGG modules matching a category keyword from the module list."""
    cache = CACHE_DIR / 'kegg_module_list.json'
    if cache.exists():
        modules = json.loads(cache.read_text())
    else:
        url = "https://rest.kegg.jp/list/module"
        data = urllib.request.urlopen(url, timeout=30).read().decode()
        modules = {}
        for line in data.strip().split('\n'):
            parts = line.split('\t')
            if len(parts) >= 2:
                mod_id = parts[0].replace('md:', '')
                modules[mod_id] = parts[1]
        cache.write_text(json.dumps(modules))
    matching = {k: v for k, v in modules.items()
                if category_keyword.lower() in v.lower()}
    return matching

# ═══════════════════════════════════════════════════════════════════════════════
# 2. Define pathway groups
# ═══════════════════════════════════════════════════════════════════════════════

print("Step 1: Defining pathway groups and fetching KO lists...")

NAMED_PATHWAYS = {
    'Cobalamin (M00122+M00924)': ['M00122', 'M00924'],
    'Heme (M00121+M00926)': ['M00121', 'M00926'],
    'Molybdopterin (M00880)': ['M00880'],
    'Fe-S cluster (M00175+M00176)': ['M00175', 'M00176'],
    'Riboflavin B2 (M00125)': ['M00125'],
    'Thiamine B1 (M00127)': ['M00127'],
    'Biotin B7 (M00123)': ['M00123'],
}

pathway_kos = {}
for name, mod_ids in NAMED_PATHWAYS.items():
    all_kos = set()
    for mid in mod_ids:
        kos = fetch_module_kos(mid)
        all_kos.update(kos)
    pathway_kos[name] = sorted(all_kos)
    print(f"  {name}: {len(pathway_kos[name])} KOs from {len(mod_ids)} module(s)")

# Amino acid biosynthesis modules
aa_modules = fetch_kegg_pathway_modules('biosynthesis')
aa_biosyn_mods = {k: v for k, v in aa_modules.items()
                  if any(aa in v.lower() for aa in [
                      'valine', 'leucine', 'isoleucine', 'lysine', 'threonine',
                      'methionine', 'cysteine', 'arginine', 'proline', 'histidine',
                      'tryptophan', 'phenylalanine', 'tyrosine', 'serine', 'glycine',
                      'alanine', 'aspartate', 'glutamate', 'asparagine', 'glutamine',
                      'ornithine', 'chorismate', 'shikimate',
                  ])}
aa_kos = set()
for mid in aa_biosyn_mods:
    kos = fetch_module_kos(mid)
    aa_kos.update(kos)
if aa_kos:
    pathway_kos['Amino acid biosynthesis'] = sorted(aa_kos)
    print(f"  Amino acid biosynthesis: {len(aa_kos)} KOs from {len(aa_biosyn_mods)} modules")
    print(f"    Modules: {', '.join(sorted(aa_biosyn_mods.keys())[:10])}{'...' if len(aa_biosyn_mods) > 10 else ''}")

# Nucleotide biosynthesis modules
nuc_modules = fetch_kegg_pathway_modules('biosynthesis')
nuc_biosyn_mods = {k: v for k, v in nuc_modules.items()
                   if any(n in v.lower() for n in [
                       'purine', 'pyrimidine', 'imp ', 'ump ', 'gmp ', 'cmp ',
                       'inosine', 'guanine', 'adenine', 'cytidine', 'uridine',
                       'de novo biosynthesis of purine', 'de novo biosynthesis of pyrimidine',
                   ])}
nuc_kos = set()
for mid in nuc_biosyn_mods:
    kos = fetch_module_kos(mid)
    nuc_kos.update(kos)
if nuc_kos:
    pathway_kos['Nucleotide biosynthesis'] = sorted(nuc_kos)
    print(f"  Nucleotide biosynthesis: {len(nuc_kos)} KOs from {len(nuc_biosyn_mods)} modules")
    print(f"    Modules: {', '.join(sorted(nuc_biosyn_mods.keys())[:10])}{'...' if len(nuc_biosyn_mods) > 10 else ''}")

all_needed_kos = set()
for kos in pathway_kos.values():
    all_needed_kos.update(kos)
print(f"\nTotal unique KOs needed: {len(all_needed_kos)}")

# ═══════════════════════════════════════════════════════════════════════════════
# 3. Query Spark for genus-level KO presence
# ═══════════════════════════════════════════════════════════════════════════════

GENUS_KO_CACHE = DATA / 'genus_ko_presence_all.parquet'

if GENUS_KO_CACHE.exists():
    print(f"\nStep 2: Loading cached genus KO presence from {GENUS_KO_CACHE.name}...")
    genus_ko_df = pd.read_parquet(GENUS_KO_CACHE)
    print(f"  Loaded: {genus_ko_df.genus_lower.nunique()} genera, {genus_ko_df.ko.nunique()} KOs")
else:
    print("\nStep 2: Querying Spark for genus-level KO presence...")
    try:
        from berdl_notebook_utils import get_spark_session
        spark = get_spark_session()
    except ImportError:
        from pyspark.sql import SparkSession
        spark = (SparkSession.builder
                 .appName("pathway_completeness")
                 .master("local[*]")
                 .config("spark.driver.memory", "8g")
                 .getOrCreate())

    ko_list_sql = ", ".join(f"'{k}'" for k in sorted(all_needed_kos))

    query = f'''
    WITH ko_exploded AS (
        SELECT
            g.genome_id,
            UPPER(TRIM(REGEXP_EXTRACT(ko_raw, 'K[0-9]+', 0))) AS ko_id
        FROM kbase.ke_pangenome.gene g
        JOIN kbase.ke_pangenome.bakta_annotations ba
            ON g.gene_id = ba.gene_cluster_id
        LATERAL VIEW EXPLODE(SPLIT(ba.kegg_orthology_id, ',')) t AS ko_raw
        WHERE TRIM(ko_raw) != ''
          AND REGEXP_EXTRACT(ko_raw, 'K[0-9]+', 0) IS NOT NULL
    ),
    genus_map AS (
        SELECT
            accession AS genome_id,
            LOWER(REGEXP_EXTRACT(gtdb_taxonomy, 'g__([^;]+)', 1)) AS genus_lower
        FROM kbase.ke_pangenome.gtdb_metadata
        WHERE REGEXP_EXTRACT(gtdb_taxonomy, 'g__([^;]+)', 1) IS NOT NULL
          AND TRIM(REGEXP_EXTRACT(gtdb_taxonomy, 'g__([^;]+)', 1)) != ''
    )
    SELECT
        gm.genus_lower,
        ke.ko_id AS ko,
        COUNT(DISTINCT ke.genome_id) AS n_genomes_with_ko
    FROM ko_exploded ke
    JOIN genus_map gm ON ke.genome_id = gm.genome_id
    WHERE ke.ko_id IN ({ko_list_sql})
    GROUP BY gm.genus_lower, ke.ko_id
    '''

    print("  Running query...")
    sdf = spark.sql(query)
    genus_ko_df = sdf.toPandas()
    genus_ko_df.attrs = {}
    genus_ko_df.to_parquet(GENUS_KO_CACHE, index=False)
    print(f"  Result: {genus_ko_df.genus_lower.nunique()} genera, {genus_ko_df.ko.nunique()} KOs")
    print(f"  Cached to {GENUS_KO_CACHE.name}")

# Build genus → set of KOs present
genus_ko_sets = genus_ko_df.groupby('genus_lower')['ko'].apply(set).to_dict()

# Also build genus → total genomes for genome-count info
genus_genome_counts = (genus_ko_df.groupby('genus_lower')['n_genomes_with_ko']
                       .max().to_dict())

# ═══════════════════════════════════════════════════════════════════════════════
# 4. Load PGLS input data
# ═══════════════════════════════════════════════════════════════════════════════

print("\nStep 3: Loading PGLS input data...")
pgls_input = pd.read_csv(DATA / '01_pgls_input_bacteria.csv')
print(f"  PGLS genera: {len(pgls_input)}")

# Strip g__ prefix from genus_ko_sets keys if present
genus_ko_sets_clean = {}
for g, kos in genus_ko_sets.items():
    g_clean = re.sub(r'^g__', '', g)
    genus_ko_sets_clean[g_clean] = kos
genus_ko_sets = genus_ko_sets_clean

overlap = set(pgls_input.genus_lower) & set(genus_ko_sets.keys())
print(f"  Genera in both PGLS input and KO data: {len(overlap)}")

# ═══════════════════════════════════════════════════════════════════════════════
# 5. Compute completeness per pathway per genus
# ═══════════════════════════════════════════════════════════════════════════════

print("\nStep 4: Computing pathway completeness per genus...")

completeness_data = {}
for pw_name, pw_kos in pathway_kos.items():
    completeness = {}
    for genus in pgls_input.genus_lower:
        gkos = genus_ko_sets.get(genus, set())
        n_present = sum(1 for k in pw_kos if k in gkos)
        completeness[genus] = n_present / len(pw_kos) if pw_kos else 0.0
    completeness_data[pw_name] = completeness
    vals = list(completeness.values())
    nonzero = sum(1 for v in vals if v > 0)
    print(f"  {pw_name}: mean={np.mean(vals):.3f}, "
          f"median={np.median(vals):.3f}, "
          f"nonzero={nonzero}/{len(vals)} genera")

# ═══════════════════════════════════════════════════════════════════════════════
# 6. Run PGLS for each pathway
# ═══════════════════════════════════════════════════════════════════════════════

print("\nStep 5: Running PGLS models...")
print("=" * 70)

results = []

for pw_name, pw_kos in pathway_kos.items():
    print(f"\n--- {pw_name} ({len(pw_kos)} KOs) ---")

    # Build analysis dataframe
    df = pgls_input.copy()
    df['completeness'] = df['genus_lower'].map(completeness_data[pw_name])

    # Filter to genera with ≥1 KO present (analogous to cobalamin analysis)
    df_with = df[df['completeness'] > 0].copy()
    n_with = len(df_with)
    print(f"  Genera with ≥1 KO: {n_with}")

    if n_with < 50:
        print(f"  SKIP: too few genera ({n_with} < 50)")
        results.append({
            'pathway': pw_name,
            'n_kos': len(pw_kos),
            'n_genera': n_with,
            'note': f'skipped: n={n_with} < 50',
        })
        continue

    # z-score completeness and genome size within this subset
    df_with['completeness_z'] = (
        (df_with['completeness'] - df_with['completeness'].mean())
        / df_with['completeness'].std()
    )
    df_with['gsize_z'] = (
        (df_with['mean_genome_mb'] - df_with['mean_genome_mb'].mean())
        / df_with['mean_genome_mb'].std()
    )

    # Model 1: uncontrolled (completeness only)
    try:
        res_unc = run_pgls(
            df_with, TREE,
            response='mean_levins_B_std',
            predictors=['completeness_z'],
            label=f'{pw_name}_uncontrolled',
        )
        beta_unc = res_unc['beta']
        se_unc = res_unc['SE']
        p_unc = res_unc['p_value']
        lam_unc = res_unc['lambda_est']
        print(f"  Uncontrolled: β={beta_unc:.4f}, SE={se_unc:.4f}, "
              f"p={p_unc:.4e}, λ={lam_unc:.3f}")
    except Exception as e:
        print(f"  Uncontrolled FAILED: {e}")
        beta_unc = se_unc = p_unc = lam_unc = float('nan')

    # Model 2: genome-size controlled
    try:
        res_ctrl = run_pgls(
            df_with, TREE,
            response='mean_levins_B_std',
            predictors=['completeness_z', 'gsize_z'],
            label=f'{pw_name}_controlled',
        )
        beta_ctrl = res_ctrl['betas']['completeness_z']
        se_ctrl = res_ctrl['SEs']['completeness_z']
        p_ctrl = res_ctrl['p_values']['completeness_z']
        lam_ctrl = res_ctrl['lambda_est']
        beta_gsize = res_ctrl['betas']['gsize_z']
        p_gsize = res_ctrl['p_values']['gsize_z']
        print(f"  Controlled:   β={beta_ctrl:.4f}, SE={se_ctrl:.4f}, "
              f"p={p_ctrl:.4e}, λ={lam_ctrl:.3f}")
        print(f"  Genome size:  β={beta_gsize:.4f}, p={p_gsize:.4e}")
    except Exception as e:
        print(f"  Controlled FAILED: {e}")
        beta_ctrl = se_ctrl = p_ctrl = lam_ctrl = float('nan')
        beta_gsize = p_gsize = float('nan')

    # Detect suppression: signal strengthens (gets more negative) after gsize control
    suppression = False
    if not np.isnan(beta_unc) and not np.isnan(beta_ctrl):
        suppression = (beta_ctrl < beta_unc) and (beta_ctrl < 0)

    results.append({
        'pathway': pw_name,
        'n_kos': len(pw_kos),
        'n_genera': n_with,
        'beta_uncontrolled': beta_unc,
        'se_uncontrolled': se_unc,
        'p_uncontrolled': p_unc,
        'lambda_uncontrolled': lam_unc,
        'beta_controlled': beta_ctrl,
        'se_controlled': se_ctrl,
        'p_controlled': p_ctrl,
        'lambda_controlled': lam_ctrl,
        'beta_gsize': beta_gsize,
        'p_gsize': p_gsize,
        'suppression_effect': suppression,
        'significant_controlled': p_ctrl < 0.05 if not np.isnan(p_ctrl) else False,
    })

    if suppression:
        print(f"  *** SUPPRESSION: β goes from {beta_unc:.4f} → {beta_ctrl:.4f} after gsize control")

# ═══════════════════════════════════════════════════════════════════════════════
# 7. Joint models (significant pathways vs cobalamin)
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("Step 6: Joint models (pathway + cobalamin + genome size)")
print("=" * 70)

sig_pathways = [r for r in results
                if r.get('significant_controlled') and r['pathway'] != 'Cobalamin (M00122+M00924)']

if not sig_pathways:
    print("  No non-cobalamin pathway is individually significant. Skipping joint models.")
else:
    cob_name = 'Cobalamin (M00122+M00924)'
    for r in sig_pathways:
        pw_name = r['pathway']
        print(f"\n--- Joint: {pw_name} + Cobalamin ---")

        df = pgls_input.copy()
        df['cob_comp'] = df['genus_lower'].map(completeness_data[cob_name])
        df['pw_comp'] = df['genus_lower'].map(completeness_data[pw_name])

        # Require both pathways to have ≥1 KO
        df_joint = df[(df['cob_comp'] > 0) & (df['pw_comp'] > 0)].copy()
        print(f"  Genera with both pathways: {len(df_joint)}")

        if len(df_joint) < 50:
            print(f"  SKIP: too few genera ({len(df_joint)} < 50)")
            r['joint_n'] = len(df_joint)
            r['joint_note'] = 'skipped: n < 50'
            continue

        for col in ['cob_comp', 'pw_comp', 'mean_genome_mb']:
            df_joint[f'{col}_z'] = (
                (df_joint[col] - df_joint[col].mean()) / df_joint[col].std()
            )

        try:
            res_joint = run_pgls(
                df_joint, TREE,
                response='mean_levins_B_std',
                predictors=['cob_comp_z', 'pw_comp_z', 'mean_genome_mb_z'],
                label=f'joint_{pw_name}',
            )
            r['joint_n'] = res_joint['n']
            r['joint_beta_cobalamin'] = res_joint['betas']['cob_comp_z']
            r['joint_p_cobalamin'] = res_joint['p_values']['cob_comp_z']
            r['joint_beta_pathway'] = res_joint['betas']['pw_comp_z']
            r['joint_p_pathway'] = res_joint['p_values']['pw_comp_z']
            r['joint_lambda'] = res_joint['lambda_est']

            print(f"  Cobalamin: β={r['joint_beta_cobalamin']:.4f}, p={r['joint_p_cobalamin']:.4e}")
            print(f"  {pw_name}: β={r['joint_beta_pathway']:.4f}, p={r['joint_p_pathway']:.4e}")

            if r['joint_p_pathway'] < 0.05:
                print(f"  → {pw_name} SURVIVES joint model with cobalamin")
            else:
                print(f"  → {pw_name} absorbed by cobalamin (or shared signal)")

        except Exception as e:
            print(f"  Joint FAILED: {e}")
            r['joint_note'] = f'failed: {e}'

# ═══════════════════════════════════════════════════════════════════════════════
# 8. Binary completeness test (≥50% threshold) for significant pathways
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("Step 7: Binary completeness (≥50%) for significant pathways")
print("=" * 70)

for r in results:
    if not r.get('significant_controlled'):
        continue
    pw_name = r['pathway']
    print(f"\n--- {pw_name} binary ≥50% ---")

    df = pgls_input.copy()
    df['completeness'] = df['genus_lower'].map(completeness_data[pw_name])
    df_with = df[df['completeness'] > 0].copy()

    n_high = (df_with['completeness'] >= 0.5).sum()
    n_low = (df_with['completeness'] < 0.5).sum()
    print(f"  ≥50%: {n_high}, <50%: {n_low}")

    if n_high < 10 or n_low < 10:
        print(f"  SKIP: imbalanced groups")
        r['binary_note'] = f'skipped: ≥50%={n_high}, <50%={n_low}'
        continue

    df_with['binary_z'] = (
        (df_with['completeness'] >= 0.5).astype(float)
    )
    df_with['binary_z'] = (
        (df_with['binary_z'] - df_with['binary_z'].mean()) / df_with['binary_z'].std()
    )
    df_with['gsize_z'] = (
        (df_with['mean_genome_mb'] - df_with['mean_genome_mb'].mean())
        / df_with['mean_genome_mb'].std()
    )

    try:
        res_bin = run_pgls(
            df_with, TREE,
            response='mean_levins_B_std',
            predictors=['binary_z', 'gsize_z'],
            label=f'{pw_name}_binary',
        )
        r['binary_beta'] = res_bin['betas']['binary_z']
        r['binary_p'] = res_bin['p_values']['binary_z']
        print(f"  Binary: β={r['binary_beta']:.4f}, p={r['binary_p']:.4e}")
    except Exception as e:
        print(f"  Binary FAILED: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# 9. Save results and print summary
# ═══════════════════════════════════════════════════════════════════════════════

res_df = pd.DataFrame(results)
out_path = DATA / 'pathway_completeness_pgls.csv'
res_df.to_csv(out_path, index=False)
print(f"\nResults saved to {out_path}")

# ─── Summary table ─────────────────────────────────────────────────────────

print("\n" + "=" * 70)
print("SUMMARY: Pathway Completeness PGLS Results")
print("=" * 70)

cols = ['pathway', 'n_kos', 'n_genera',
        'beta_uncontrolled', 'p_uncontrolled',
        'beta_controlled', 'p_controlled',
        'suppression_effect', 'significant_controlled']

print(f"\n{'Pathway':<35} {'KOs':>4} {'n':>5} "
      f"{'β_unc':>8} {'p_unc':>10} "
      f"{'β_ctrl':>8} {'p_ctrl':>10} "
      f"{'Supp':>5} {'Sig':>4}")
print("-" * 100)

for _, r in res_df.iterrows():
    if 'note' in r and pd.notna(r.get('note', None)):
        print(f"{r['pathway']:<35} {r['n_kos']:>4} {r['n_genera']:>5}  {r.get('note', '')}")
        continue
    supp = '  Y' if r.get('suppression_effect') else '  N'
    sig = '  *' if r.get('significant_controlled') else '   '
    beta_u = r.get('beta_uncontrolled', float('nan'))
    p_u = r.get('p_uncontrolled', float('nan'))
    beta_c = r.get('beta_controlled', float('nan'))
    p_c = r.get('p_controlled', float('nan'))
    print(f"{r['pathway']:<35} {r['n_kos']:>4} {r['n_genera']:>5} "
          f"{beta_u:>8.4f} {p_u:>10.4e} "
          f"{beta_c:>8.4f} {p_c:>10.4e} "
          f"{supp:>5} {sig:>4}")

# ─── Interpretation ────────────────────────────────────────────────────────

print("\n" + "=" * 70)
print("INTERPRETATION")
print("=" * 70)

n_sig = sum(1 for r in results if r.get('significant_controlled'))
n_supp = sum(1 for r in results if r.get('suppression_effect'))
n_total = len([r for r in results if 'note' not in r or pd.isna(r.get('note'))])

print(f"\n  Pathways tested: {n_total}")
print(f"  Significant (p<0.05, gsize-controlled): {n_sig}")
print(f"  Showing suppression effect: {n_supp}")

sig_names = [r['pathway'] for r in results if r.get('significant_controlled')]
supp_names = [r['pathway'] for r in results if r.get('suppression_effect')]

if sig_names:
    print(f"\n  Significant pathways: {', '.join(sig_names)}")
if supp_names:
    print(f"  Suppression pathways: {', '.join(supp_names)}")

# Check if cobalamin is unique
cob_sig = any(r.get('significant_controlled') and 'Cobalamin' in r['pathway'] for r in results)
others_sig = [r['pathway'] for r in results
              if r.get('significant_controlled') and 'Cobalamin' not in r['pathway']]

if cob_sig and not others_sig:
    print("\n  CONCLUSION: Cobalamin is the ONLY biosynthetic pathway whose completeness")
    print("  independently predicts cross-biome niche specialisation after genome-size control.")
    print("  This is NOT a general property of essential biosynthetic modules.")
elif cob_sig and others_sig:
    print(f"\n  CONCLUSION: {len(others_sig) + 1} pathways show significant completeness-niche")
    print(f"  associations after genome-size control: Cobalamin + {', '.join(others_sig)}.")
    print("  The signal may be a general property of essential biosynthetic modules,")
    print("  not cobalamin-specific.")

    # Check joint model results
    joint_survivors = [r['pathway'] for r in results
                       if r.get('joint_p_pathway') is not None
                       and r.get('joint_p_pathway', 1.0) < 0.05]
    if joint_survivors:
        print(f"  Pathways surviving joint model with cobalamin: {', '.join(joint_survivors)}")
    else:
        print("  No pathway survives joint model with cobalamin — signals are shared.")
elif not cob_sig:
    print("\n  NOTE: Cobalamin completeness did NOT reach significance in this run.")
    print("  Check n_genera and compare to the manuscript's 1,543-genera result.")

print("\nDONE")

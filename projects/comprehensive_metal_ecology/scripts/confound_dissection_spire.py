#!/usr/bin/env python3
"""
Confound dissection for SPIRE genome database.
Same analysis as MGnify: raw → +GS → +ENV → kitchen sink, soil-only, biome control.
"""
import os
for var in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ.setdefault(var, '1')

import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats
from scipy.spatial import cKDTree
from statsmodels.stats.multitest import multipletests
import warnings
warnings.filterwarnings('ignore')

DATA = Path('/home/hmacgregor/BERIL-research-observatory/projects/per_ko_metal_associations/data')
CME = Path('/home/hmacgregor/BERIL-research-observatory/projects/comprehensive_metal_ecology/data')

MIN_GENOMES_PER_GENUS = 8
MIN_GENERA = 5  # Lower than MGnify since SPIRE has fewer genomes
METALS = ['PF1_Hg', 'PF1_As', 'PF1_Cu', 'PF1_Cr', 'PF1_Cd', 'PF1_Pb']

TARGET_KOS = {
    'K01546': 'kdpA', 'K01547': 'kdpB', 'K01548': 'kdpC',
    'K07646': 'kdpD', 'K07667': 'kdpE',
    'K04651': 'hypA', 'K04652': 'hypB', 'K04653': 'hypC',
    'K04654': 'hypD', 'K04655': 'hypE', 'K04656': 'hypF',
    'K06188': 'aqpZ', 'K01531': 'mgtA', 'K07241': 'hoxN/nixA',
    'K08364': 'merP', 'K01535': 'PMA1/PMA2', 'K01114': 'plc',
    'K05275': 'pdxDH', 'K06215': 'pdxS/pdx1',
    'K07497': 'IS_transposase1', 'K07486': 'IS_transposase2',
    'K07481': 'IS5_transposase',
    'K15461': 'mnmC', 'K06213': 'mgtE', 'K02863': 'rplA', 'K03498': 'trkH',
}

# ── Load SPIRE ─────────────────────────────────────────────────────────
print("Loading SPIRE data...", flush=True)
sp = pd.read_parquet(DATA / 'spire_all_ko_matrix.parquet')
sp_target = sp[sp.ko_id.isin(TARGET_KOS)].copy()

genome_meta = sp_target.groupby('genome_id').first()[
    ['genus', 'phylum', 'genome_size', 'latitude', 'longitude'] + METALS
].reset_index()
ko_wide = sp_target.pivot_table(index='genome_id', columns='ko_id',
                                values='present', fill_value=0).reset_index()
genome_df = genome_meta.merge(ko_wide, on='genome_id')

print(f"  SPIRE genomes: {len(genome_df):,}", flush=True)
print(f"  Unique genera: {genome_df.genus.nunique()}", flush=True)
genus_cts = genome_df.genus.value_counts()
usable = genus_cts[genus_cts >= MIN_GENOMES_PER_GENUS]
print(f"  Usable genera (≥{MIN_GENOMES_PER_GENUS}): {len(usable)}", flush=True)

# ── Biome from SPIRE sample_environment ────────────────────────────────
# SPIRE has its own biome info — check
print("\nChecking for SPIRE biome data...", flush=True)
try:
    from berdl_notebook_utils import get_spark_session
    spark = get_spark_session()
    biome_df = spark.sql("""
        SELECT DISTINCT se.sample_id, se.biome, se.feature, se.material,
               mc.mag_id, mc.latitude, mc.longitude
        FROM kbase.spire.sample_environment se
        JOIN kbase.spire.mag_coordinates mc ON se.sample_id = mc.sample_id
        WHERE mc.latitude IS NOT NULL
    """).toPandas()
    spark.stop()
    print(f"  SPIRE biome records: {len(biome_df):,}")
    biome_df = biome_df.rename(columns={'mag_id': 'genome_id'})
    genome_df = genome_df.merge(biome_df[['genome_id', 'biome', 'feature', 'material']],
                                 on='genome_id', how='left')
    genome_df['biome_broad'] = genome_df.biome.fillna('Unknown').apply(
        lambda x: 'Soil' if 'soil' in x.lower() else
                  'Marine' if 'marine' in x.lower() or 'ocean' in x.lower() else
                  'Freshwater' if 'freshwater' in x.lower() or 'lake' in x.lower() or 'river' in x.lower() else
                  'Sediment' if 'sediment' in x.lower() else
                  'Host' if 'host' in x.lower() or 'animal' in x.lower() else 'Other')
    genome_df['is_soil'] = genome_df.biome_broad == 'Soil'
except Exception as e:
    print(f"  Spark biome fetch failed: {e}")
    genome_df['biome_broad'] = 'Unknown'
    genome_df['is_soil'] = False

print("\nBiome distribution:")
print(genome_df.biome_broad.value_counts().to_string())

# ── Load env covariates via KD-tree from cached grids ─────────────────
print("\nJoining env covariates from cached grids...", flush=True)
env_cache = CME / 'env_cache'
env_cols_joined = []
locs = genome_df[['latitude', 'longitude']].values


def kdtree_join(grid_df, lat_col, lon_col, value_cols, max_dist_deg, label):
    grid_df = grid_df.dropna(subset=[lat_col, lon_col])
    if len(grid_df) == 0:
        return
    tree = cKDTree(grid_df[[lat_col, lon_col]].values)
    dd, ii = tree.query(locs, k=1)
    for c in value_cols:
        vals = pd.to_numeric(grid_df[c], errors='coerce').values
        genome_df[c] = vals[ii]
        genome_df.loc[dd > max_dist_deg, c] = np.nan
    env_cols_joined.extend(value_cols)
    n_matched = (dd <= max_dist_deg).sum()
    print(f"  {label}: {len(value_cols)} cols, {n_matched} matched (of {len(genome_df)})")


# Science 2025 HQ
sci = pd.read_csv(env_cache / 'science2025_grid.csv')
sci_cols = [c for c in sci.columns if c.startswith('sci_')]
kdtree_join(sci, 'lat', 'lon', sci_cols, 0.5, 'Science 2025 HQ')

# GeoROC
georoc = pd.read_csv(env_cache / 'georoc_grid.csv')
georoc_cols = [c for c in georoc.columns if c.startswith('georoc_')]
kdtree_join(georoc, 'lat', 'lon', georoc_cols, 2.0, 'GeoROC')

# GEMAS
gemas = pd.read_csv(env_cache / 'gemas.csv')
gemas_cols = [c for c in gemas.columns if c.startswith('gemas_')]
kdtree_join(gemas, 'lat', 'lon', gemas_cols, 1.0, 'GEMAS')

# Elevation
elev = pd.read_csv(env_cache / 'etopo1_grid.csv')
kdtree_join(elev, 'lat', 'lon', ['elevation_m'], 0.5, 'Elevation')

# Lithology (encode mafic score from name)
litho = pd.read_csv(env_cache / 'ecotapestry.csv')
mafic_map = {'Mafic': 1.0, 'Ultramafic': 1.0, 'Intermediate': 0.5, 'Felsic': 0.0}
litho['litho_mafic_score'] = litho.get('lithology_name', pd.Series()).map(mafic_map)
litho = litho.dropna(subset=['litho_mafic_score'])
if len(litho) > 0:
    kdtree_join(litho, 'lat', 'lon', ['litho_mafic_score'], 0.5, 'Lithology')

# EPA TRI (compute facility count within 50km)
tri_raw = pd.read_csv(env_cache / 'epa_tri.csv')
if len(tri_raw) > 0:
    tri_tree = cKDTree(tri_raw[['lat', 'lon']].values)
    counts_50 = tri_tree.query_ball_point(locs, r=0.5)  # ~50km at mid-latitudes
    genome_df['tri_facility_count_50km'] = [len(c) for c in counts_50]
    env_cols_joined.append('tri_facility_count_50km')
    print(f"  EPA TRI: 1 col, {(genome_df.tri_facility_count_50km > 0).sum()} with facilities nearby")

# Mining ops (compute min distance)
mines = pd.read_csv(env_cache / 'mining_ops.csv')
if len(mines) > 0:
    mine_tree = cKDTree(mines[['lat', 'lon']].values)
    dd, _ = mine_tree.query(locs, k=1)
    genome_df['mine_min_dist_km'] = dd * 111.0
    genome_df['mine_count_50km'] = [len(c) for c in mine_tree.query_ball_point(locs, r=0.5)]
    env_cols_joined.extend(['mine_min_dist_km', 'mine_count_50km'])
    print(f"  Mines: 2 cols")

# CMMI ores (min distance)
cmmi = pd.read_csv(env_cache / 'cmmi_ores.csv')
cmmi_metal_cols = [c for c in cmmi.columns if c.startswith('cmmi_')]
if len(cmmi) > 0:
    cmmi_tree = cKDTree(cmmi[['lat', 'lon']].values)
    dd, _ = cmmi_tree.query(locs, k=1)
    genome_df['cmmi_min_dist_km'] = dd * 111.0
    env_cols_joined.append('cmmi_min_dist_km')
    print(f"  CMMI: 1 col")

# Soil chemistry from the MGnify env covariates (use KD-tree)
env_full = pd.read_csv(CME / 'genome_env_covariates_full.csv')
soil_chem_cols = ['ph_h2o', 'organic_carbon_density', 'clay_pct',
                  'mean_annual_temp_C', 'mean_annual_precip_mm']
# These are already in the per-genome file — KD-tree match SPIRE to nearest MGnify loc
env_locs = env_full[['latitude', 'longitude']].dropna()
if len(env_locs) > 0:
    env_tree = cKDTree(env_locs.values)
    dd, ii = env_tree.query(locs, k=1)
    for c in soil_chem_cols:
        genome_df[c] = env_full[c].values[ii]
        genome_df.loc[dd > 0.5, c] = np.nan
    env_cols_joined.extend(soil_chem_cols)
    print(f"  Soil chemistry (from MGnify grid): {len(soil_chem_cols)} cols, {(dd <= 0.5).sum()} matched")

print(f"\n  Total env columns joined: {len(env_cols_joined)}")


# ── Run meta-analysis ─────────────────────────────────────────────────
def run_meta(df, ko_id, metal_pf1, covariates=None, min_genera=MIN_GENERA):
    genus_cts = df.genus.value_counts()
    genera = genus_cts[genus_cts >= MIN_GENOMES_PER_GENUS].index
    effects = []

    for genus in genera:
        gdf = df[df.genus == genus]
        if ko_id not in gdf.columns:
            continue
        ko = gdf[ko_id].values
        met = gdf[metal_pf1].values
        if ko.std() == 0 or np.isnan(met).all():
            continue
        prev = ko.mean()
        if prev < 0.05 or prev > 0.95:
            continue
        mask = np.isfinite(met)

        if covariates:
            avail = []
            for c in covariates:
                if c in gdf.columns:
                    cv = pd.to_numeric(gdf[c], errors='coerce').values
                    cm = np.isfinite(cv)
                    if cm[mask].sum() >= mask.sum() * 0.5:
                        avail.append(c)
                        mask &= cm
            if mask.sum() < MIN_GENOMES_PER_GENUS:
                continue
            ko_sub = ko[mask]
            if ko_sub.std() == 0:
                continue
            if len(avail) > 0:
                X = np.column_stack([pd.to_numeric(gdf[c], errors='coerce').values[mask]
                                    for c in avail])
                keep = [i for i in range(X.shape[1]) if X[:, i].std() > 0]
                if len(keep) > 0:
                    X = X[:, keep]
                    try:
                        Xf = np.column_stack([np.ones(X.shape[0]), X])
                        b, _, _, _ = np.linalg.lstsq(Xf, met[mask], rcond=None)
                        resid = met[mask] - Xf @ b
                        rho, _ = stats.pointbiserialr(ko_sub, resid)
                        if np.isfinite(rho):
                            effects.append((mask.sum(), rho))
                        continue
                    except:
                        continue
            try:
                rho, _ = stats.pointbiserialr(ko_sub, met[mask])
                if np.isfinite(rho):
                    effects.append((mask.sum(), rho))
            except:
                pass
            continue

        if mask.sum() < MIN_GENOMES_PER_GENUS:
            continue
        ko_sub = ko[mask]
        if ko_sub.std() == 0:
            continue
        try:
            rho, _ = stats.pointbiserialr(ko_sub, met[mask])
            if np.isfinite(rho):
                effects.append((mask.sum(), rho))
        except:
            continue

    if len(effects) < min_genera:
        return None
    ns = np.array([e[0] for e in effects])
    rhos = np.array([e[1] for e in effects])
    w = (ns - 3).clip(min=1)
    z = np.arctanh(np.clip(rhos, -0.999, 0.999))
    mz = np.average(z, weights=w)
    se = 1.0 / np.sqrt(w.sum())
    zs = mz / se
    p = 2 * stats.norm.sf(abs(zs))
    return {'meta_rho': np.tanh(mz), 'meta_p': p, 'n_genera': len(effects)}


# ── Phase 1: Raw scan all target KOs × metals ─────────────────────────
print(f"\n{'='*100}", flush=True)
print("PHASE 1: RAW SCAN — TARGET KOs × METALS (SPIRE)", flush=True)
print(f"{'='*100}\n", flush=True)

raw_results = []
for ko_id, gene_name in TARGET_KOS.items():
    if ko_id not in genome_df.columns:
        continue
    for metal in METALS:
        res = run_meta(genome_df, ko_id, metal)
        if res:
            raw_results.append({
                'ko_id': ko_id, 'gene_name': gene_name,
                'metal': metal.replace('PF1_', ''),
                **res
            })

raw_df = pd.DataFrame(raw_results)
if len(raw_df) > 0:
    _, q_vals, _, _ = multipletests(raw_df.meta_p.values, method='fdr_bh')
    raw_df['q_fdr'] = q_vals
    sig = raw_df[raw_df.q_fdr < 0.05]
    print(f"Tested: {len(raw_df)}, Significant (FDR<0.05): {len(sig)}")
    if len(sig) > 0:
        print("\nSignificant pairs:")
        for _, r in sig.sort_values('meta_p').iterrows():
            print(f"  {r.gene_name:18s} × {r.metal:3s}: ρ={r.meta_rho:+.4f}, "
                  f"p={r.meta_p:.2e}, q={r.q_fdr:.4f} ({r.n_genera} genera)")
else:
    print("No testable pairs!")
    sig = pd.DataFrame()


# ── Phase 2: Covariate ablation on significant pairs ──────────────────
if len(sig) > 0:
    print(f"\n{'='*100}", flush=True)
    print("PHASE 2: COVARIATE ABLATION (SPIRE)", flush=True)
    print(f"{'='*100}\n", flush=True)

    covariate_sets = {
        'Raw': [],
        'GS only': ['genome_size'],
        'GS + ENV': ['genome_size', 'ph_h2o', 'organic_carbon_density', 'clay_pct',
                     'mean_annual_temp_C', 'mean_annual_precip_mm',
                     'elevation_m', 'litho_mafic_score'],
        'GS + ENV + metals': ['genome_size', 'ph_h2o', 'organic_carbon_density', 'clay_pct',
                               'mean_annual_temp_C', 'mean_annual_precip_mm',
                               'elevation_m', 'litho_mafic_score',
                               'sci_hq_As', 'sci_hq_Cd', 'sci_hq_Co', 'sci_hq_Cr',
                               'sci_hq_Cu', 'sci_hq_Ni', 'sci_hq_Pb',
                               'georoc_Cu', 'georoc_Ni', 'georoc_Zn', 'georoc_Co', 'georoc_Cr',
                               'georoc_Pb', 'georoc_As', 'georoc_Cd', 'georoc_U',
                               'gemas_Cu', 'gemas_Pb', 'gemas_Ni', 'gemas_Cr', 'gemas_Co',
                               'gemas_Zn', 'gemas_As', 'gemas_Cd', 'gemas_Hg'],
        'Kitchen sink': ['genome_size', 'ph_h2o', 'organic_carbon_density', 'clay_pct',
                          'mean_annual_temp_C', 'mean_annual_precip_mm',
                          'elevation_m', 'litho_mafic_score',
                          'sci_hq_As', 'sci_hq_Cd', 'sci_hq_Co', 'sci_hq_Cr',
                          'sci_hq_Cu', 'sci_hq_Ni', 'sci_hq_Pb',
                          'georoc_Cu', 'georoc_Ni', 'georoc_Zn', 'georoc_Co', 'georoc_Cr',
                          'georoc_Pb', 'georoc_As', 'georoc_Cd', 'georoc_U',
                          'gemas_Cu', 'gemas_Pb', 'gemas_Ni', 'gemas_Cr', 'gemas_Co',
                          'gemas_Zn', 'gemas_As', 'gemas_Cd', 'gemas_Hg',
                          'tri_facility_count_50km', 'mine_min_dist_km',
                          'cmmi_min_dist_km', 'mine_count_50km'],
    }

    print(f"{'Model':35s} {'Tested':>6s} {'Survive':>7s} {'Mean att':>9s}")
    print('-' * 60)
    for name, covs in covariate_sets.items():
        covs_avail = [c for c in covs if c in genome_df.columns] if covs else None
        results = []
        for _, row in sig.iterrows():
            res = run_meta(genome_df, row.ko_id, 'PF1_' + row.metal, covs_avail)
            if res:
                atten = 1.0 - abs(res['meta_rho']) / max(abs(row.meta_rho), 1e-6)
                results.append({'rho': res['meta_rho'], 'p': res['meta_p'], 'atten': atten})
        if results:
            rdf = pd.DataFrame(results)
            _, q_vals, _, _ = multipletests(rdf.p.values, method='fdr_bh')
            rdf['q'] = q_vals
            n_surv = (rdf.q < 0.05).sum()
            print(f"  {name:35s} {len(rdf):6d} {n_surv:7d} {rdf.atten.mean():+8.0%}")


# ── Phase 3: Genome-wide raw scan for all KOs ─────────────────────────
print(f"\n{'='*100}", flush=True)
print("PHASE 3: GENOME-WIDE RAW SCAN (SPIRE)", flush=True)
print(f"{'='*100}\n", flush=True)

print("Loading full SPIRE KO matrix...", flush=True)
sp_full = pd.read_parquet(DATA / 'spire_all_ko_matrix.parquet')
n_genomes = sp_full.genome_id.nunique()

# KO prevalence
ko_counts = sp_full.groupby('ko_id')['genome_id'].nunique()
ko_prev = ko_counts / n_genomes
variable_kos = ko_prev[(ko_prev >= 0.05) & (ko_prev <= 0.95)]
print(f"  Variable KOs (5-95%): {len(variable_kos)}")

# Build presence matrix
sp_var = sp_full[sp_full.ko_id.isin(variable_kos.index)]
ko_wide_full = sp_var.pivot_table(index='genome_id', columns='ko_id',
                                   values='present', fill_value=0)

genome_full = sp_full.drop_duplicates('genome_id')[
    ['genome_id', 'genus', 'genome_size', 'latitude', 'longitude'] + METALS
].set_index('genome_id')
gw_df = genome_full.join(ko_wide_full, how='left').fillna(0).reset_index()

genus_cts_gw = gw_df.genus.value_counts()
genera_gw = genus_cts_gw[genus_cts_gw >= MIN_GENOMES_PER_GENUS].index
genus_idx = {g: gw_df.index[gw_df.genus == g].values for g in genera_gw}
print(f"  Usable genera: {len(genera_gw)}")

gw_raw = []
ko_list = sorted(variable_kos.index)
for i, ko_id in enumerate(ko_list):
    if (i + 1) % 500 == 0:
        print(f"    KO {i+1}/{len(ko_list)}...", flush=True)
    if ko_id not in gw_df.columns:
        continue
    ko_vals = gw_df[ko_id].values
    for metal in METALS:
        met_vals = gw_df[metal].values
        effects = []
        for genus, idx in genus_idx.items():
            ko = ko_vals[idx]
            met = met_vals[idx]
            mask = np.isfinite(met)
            if mask.sum() < MIN_GENOMES_PER_GENUS:
                continue
            ko_m = ko[mask]
            if ko_m.std() == 0:
                continue
            prev = ko_m.mean()
            if prev < 0.05 or prev > 0.95:
                continue
            try:
                rho, _ = stats.pointbiserialr(ko_m, met[mask])
                if np.isfinite(rho):
                    effects.append((mask.sum(), rho))
            except:
                continue
        if len(effects) < MIN_GENERA:
            continue
        ns = np.array([e[0] for e in effects])
        rhos = np.array([e[1] for e in effects])
        w = (ns - 3).clip(min=1)
        z = np.arctanh(np.clip(rhos, -0.999, 0.999))
        mz = np.average(z, weights=w)
        se = 1.0 / np.sqrt(w.sum())
        zs = mz / se
        p = 2 * stats.norm.sf(abs(zs))
        gw_raw.append({
            'ko_id': ko_id, 'metal': metal.replace('PF1_', ''),
            'is_metal_gene': ko_id in TARGET_KOS,
            'meta_rho': np.tanh(mz), 'meta_p': p, 'n_genera': len(effects)
        })

gw_scan = pd.DataFrame(gw_raw)
if len(gw_scan) > 0:
    _, q_vals, _, _ = multipletests(gw_scan.meta_p.values, method='fdr_bh')
    gw_scan['q'] = q_vals
    n_sig = (gw_scan.q < 0.05).sum()
    n_total = len(gw_scan)
    print(f"\n  SPIRE genome-wide raw: {n_sig}/{n_total} significant ({n_sig/n_total:.1%})")

    # Metal gene enrichment
    metal_gene_ids = set(TARGET_KOS.keys())
    mg_sig = gw_scan[(gw_scan.q < 0.05) & (gw_scan.is_metal_gene)]
    mg_ns = gw_scan[(gw_scan.q >= 0.05) & (gw_scan.is_metal_gene)]
    nm_sig = gw_scan[(gw_scan.q < 0.05) & (~gw_scan.is_metal_gene)]
    nm_ns = gw_scan[(gw_scan.q >= 0.05) & (~gw_scan.is_metal_gene)]
    table = np.array([[len(mg_sig), len(mg_ns)], [len(nm_sig), len(nm_ns)]])
    if table.min() > 0:
        oddsratio = (table[0, 0] * table[1, 1]) / (table[0, 1] * table[1, 0])
        _, fisher_p = stats.fisher_exact(table)
        print(f"  Metal gene enrichment: OR={oddsratio:.1f}, Fisher p={fisher_p:.2e}")
    else:
        print(f"  Metal gene enrichment: table={table}")

    # Per-metal breakdown
    print(f"\n  Per-metal significance:")
    for ms in ['Hg', 'As', 'Cu', 'Cr', 'Cd', 'Pb']:
        sub = gw_scan[gw_scan.metal == ms]
        ns = (sub.q < 0.05).sum()
        print(f"    {ms}: {ns}/{len(sub)} ({ns/max(len(sub),1):.1%})")

    gw_scan.to_csv(CME / 'spire_genomewide_raw_scan.csv', index=False)

    # ── Compare to MGnify ─────────────────────────────────────────────
    print(f"\n{'='*100}", flush=True)
    print("COMPARISON: MGnify vs SPIRE", flush=True)
    print(f"{'='*100}\n", flush=True)

    mg_raw = pd.read_csv(CME / 'genomewide_raw_scan.csv')
    mg_sig_n = (mg_raw.raw_q < 0.05).sum() if 'raw_q' in mg_raw.columns else 0
    sp_sig_n = (gw_scan.q < 0.05).sum()

    print(f"  {'Metric':30s} {'MGnify':>10s} {'SPIRE':>10s}")
    print(f"  {'Genomes':30s} {'8,585':>10s} {f'{n_genomes:,}':>10s}")
    print(f"  {'Variable KOs':30s} {'4,417':>10s} {f'{len(variable_kos):,}':>10s}")
    print(f"  {'Testable pairs':30s} {f'{len(mg_raw):,}':>10s} {f'{len(gw_scan):,}':>10s}")
    print(f"  {'Significant (FDR<0.05)':30s} {f'{mg_sig_n:,}':>10s} {f'{sp_sig_n:,}':>10s}")
    print(f"  {'Significance rate':30s} {mg_sig_n/max(len(mg_raw),1):.1%}{'':>5s} "
          f"{sp_sig_n/max(len(gw_scan),1):.1%}")

    # Look for pairs significant in BOTH databases
    if 'raw_q' in mg_raw.columns:
        mg_sig_pairs = set(mg_raw[mg_raw.raw_q < 0.05].apply(
            lambda r: f"{r.ko_id}_{r.metal}", axis=1))
        sp_sig_pairs = set(gw_scan[gw_scan.q < 0.05].apply(
            lambda r: f"{r.ko_id}_{r.metal}", axis=1))
        both = mg_sig_pairs & sp_sig_pairs
        print(f"\n  Significant in BOTH databases: {len(both)}")
        if len(both) > 0:
            # Concordance direction
            n_conc = 0
            for pair in sorted(both):
                ko, met = pair.rsplit('_', 1)
                mg_rho = mg_raw[(mg_raw.ko_id == ko) & (mg_raw.metal == met)].iloc[0].get('raw_rho', 0)
                sp_rho = gw_scan[(gw_scan.ko_id == ko) & (gw_scan.metal == met)].iloc[0].meta_rho
                if mg_rho * sp_rho > 0:
                    n_conc += 1
            print(f"  Direction concordance: {n_conc}/{len(both)} ({n_conc/len(both):.0%})")

raw_df.to_csv(CME / 'spire_target_ko_results.csv', index=False)
print("\nDONE.")

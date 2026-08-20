#!/usr/bin/env python3
"""
MicrobeAtlas OTU linkage analysis.

Instead of MWAS (test KO presence vs metal directly), spatially link genomes
to nearby MicrobeAtlas 16S amplicon samples and use community composition
as covariates. If KO×metal associations survive after controlling for
community composition, the genomic signal is not an artifact of community
structure.

Strategy:
1. Spatial join: each genome → nearest MicrobeAtlas sample (within 0.5°)
2. Pull OTU abundances for matched samples, aggregate to genus level
3. PCA on genus-level community composition → first K axes
4. Add community PCA axes as covariates in within-genus meta-analysis
5. Compare: raw KO×metal vs community-controlled KO×metal
"""
import sys
sys.stdout.reconfigure(line_buffering=True)

import os
for var in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ.setdefault(var, '1')

import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats
from scipy.spatial import cKDTree
from sklearn.decomposition import PCA
from statsmodels.stats.multitest import multipletests
import warnings
warnings.filterwarnings('ignore')

DATA = Path('/home/hmacgregor/BERIL-research-observatory/projects/per_ko_metal_associations/data')
CME = Path('/home/hmacgregor/BERIL-research-observatory/projects/comprehensive_metal_ecology/data')
OUTDIR = CME / 'confound_results'
PROJECTS = Path('/home/hmacgregor/BERIL-research-observatory/projects')

MIN_GENOMES_PER_GENUS = 8
MIN_GENERA = 10
METALS = ['PF1_Hg', 'PF1_As', 'PF1_Cu', 'PF1_Cr', 'PF1_Cd', 'PF1_Pb']
ENV_COLS = ['ph_h2o', 'organic_carbon_density', 'clay_pct',
            'mean_annual_temp_C', 'mean_annual_precip_mm',
            'elevation_m', 'litho_mafic_score']
N_COMMUNITY_PCS = 10

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

# ── Step 1: Load MGnify genome data ─────────────────────────────────
print("Step 1: Loading MGnify genomes and KO matrix...")
mg = pd.read_parquet(DATA / 'mgnify_all_ko_matrix.parquet',
                     columns=['genome_id', 'ko_id', 'present', 'genus',
                              'genome_size', 'latitude', 'longitude'] + METALS)

genome_meta = mg.drop_duplicates('genome_id')[
    ['genome_id', 'genus', 'genome_size', 'latitude', 'longitude'] + METALS
].copy()

env_full = pd.read_csv(CME / 'genome_env_covariates_full.csv')
env_cols = [c for c in env_full.columns if c not in ('latitude', 'longitude', 'genome_id')]
genome_meta = genome_meta.merge(env_full[['genome_id'] + env_cols], on='genome_id', how='left')

ko_counts = mg.groupby('ko_id')['genome_id'].nunique()
n_genomes = mg.genome_id.nunique()
ko_prev = ko_counts / n_genomes
variable_kos = ko_prev[(ko_prev >= 0.05) & (ko_prev <= 0.95)].index.tolist()
print(f"  Genomes: {len(genome_meta):,}, variable KOs: {len(variable_kos):,}")

ko_wide = mg[mg.ko_id.isin(variable_kos)].pivot_table(
    index='genome_id', columns='ko_id', values='present', fill_value=0)
genome_df = genome_meta.set_index('genome_id').join(ko_wide, how='left').fillna(0).reset_index()
del mg, ko_wide
import gc; gc.collect()

# ── Step 2: Spatial join to MicrobeAtlas ─────────────────────────────
print("\nStep 2: Spatial join to MicrobeAtlas...")
from berdl_notebook_utils import get_spark_session
spark = get_spark_session()

mba_samples = spark.sql("""
    SELECT sample_id,
           TRY_CAST(LatitudeParsed AS DOUBLE) AS latitude,
           TRY_CAST(LongitudeParsed AS DOUBLE) AS longitude,
           Env_Level_1
    FROM arkinlab_microbeatlas.sample_metadata
    WHERE TRY_CAST(LatitudeParsed AS DOUBLE) IS NOT NULL
      AND TRY_CAST(LongitudeParsed AS DOUBLE) IS NOT NULL
""").toPandas()
print(f"  MicrobeAtlas samples with coords: {len(mba_samples):,}")

mba_tree = cKDTree(mba_samples[['latitude', 'longitude']].values)
valid = genome_df.latitude.notna() & genome_df.longitude.notna()
genome_coords = genome_df.loc[valid, ['latitude', 'longitude']].values

dd, ii = mba_tree.query(genome_coords, k=1)
genome_df.loc[valid, 'mba_sample_id'] = mba_samples.sample_id.values[ii]
genome_df.loc[valid, 'mba_dist_deg'] = dd

within_05 = genome_df.mba_dist_deg < 0.5
print(f"  Genomes matched within 0.5°: {within_05.sum():,}/{len(genome_df):,}")

matched_sample_ids = genome_df.loc[within_05, 'mba_sample_id'].unique().tolist()
print(f"  Unique matched MicrobeAtlas samples: {len(matched_sample_ids):,}")

# ── Step 3: Pull OTU data and build community matrix ────────────────
print("\nStep 3: Pulling OTU abundances from Spark...")

# Pull OTU taxonomy — genus is in the Tax column (semicolon-delimited)
# Format: Kingdom;Phylum;Class;Order;Family;Genus
otu_tax = spark.sql("""
    SELECT otu_id, Tax
    FROM arkinlab_microbeatlas.otu_metadata
    WHERE Tax IS NOT NULL AND Tax != '' AND Tax != 'Unassigned'
""").toPandas()
# Parse genus (last field of semicolon-delimited Tax string)
otu_tax['Genus'] = otu_tax.Tax.str.split(';').str[-1].str.strip()
otu_tax['Family'] = otu_tax.Tax.str.split(';').apply(lambda x: x[-2].strip() if len(x) >= 2 else '')
otu_tax = otu_tax[otu_tax.Genus.notna() & (otu_tax.Genus != '') & (otu_tax.Genus != 'Unassigned')]
print(f"  OTUs with genus annotation: {len(otu_tax):,}")

# Pull OTU counts for matched samples in batches
batch_size = 200
all_otu_data = []
for i in range(0, len(matched_sample_ids), batch_size):
    batch = matched_sample_ids[i:i+batch_size]
    ids_str = "','".join(batch)
    batch_data = spark.sql(f"""
        SELECT sample_id, otu_id, count
        FROM arkinlab_microbeatlas.otu_counts_long
        WHERE sample_id IN ('{ids_str}')
    """).toPandas()
    all_otu_data.append(batch_data)
    print(f"  Batch {i//batch_size + 1}/{(len(matched_sample_ids)+batch_size-1)//batch_size}: "
          f"{len(batch_data):,} rows")

spark.stop()

otu_data = pd.concat(all_otu_data, ignore_index=True)
print(f"  Total OTU count rows: {len(otu_data):,}")

# Merge with taxonomy for genus-level aggregation
otu_data = otu_data.merge(otu_tax[['otu_id', 'Genus']], on='otu_id', how='inner')

# Aggregate to genus level and compute relative abundance
genus_counts = otu_data.groupby(['sample_id', 'Genus'])['count'].sum().reset_index()
sample_totals = genus_counts.groupby('sample_id')['count'].sum().rename('total')
genus_counts = genus_counts.merge(sample_totals, on='sample_id')
genus_counts['rel_abund'] = genus_counts['count'] / genus_counts['total']

# Pivot to wide: samples × genera
print("  Building genus-level community matrix...")
comm_wide = genus_counts.pivot_table(
    index='sample_id', columns='Genus', values='rel_abund', fill_value=0)
print(f"  Community matrix: {comm_wide.shape[0]} samples × {comm_wide.shape[1]} genera")

# Filter to genera present in ≥10% of samples
genus_prev = (comm_wide > 0).mean()
common_genera = genus_prev[genus_prev >= 0.10].index.tolist()
comm_filtered = comm_wide[common_genera]
print(f"  Common genera (≥10% prevalence): {len(common_genera)}")

# ── Step 4: PCA on community composition ────────────────────────────
print(f"\nStep 4: PCA on community composition ({N_COMMUNITY_PCS} PCs)...")
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
comm_scaled = scaler.fit_transform(comm_filtered)
pca = PCA(n_components=min(N_COMMUNITY_PCS, comm_filtered.shape[1], comm_filtered.shape[0]))
comm_pcs = pca.fit_transform(comm_scaled)
var_explained = pca.explained_variance_ratio_

print(f"  Variance explained: {', '.join(f'PC{i+1}={v:.1%}' for i, v in enumerate(var_explained))}")
print(f"  Total variance (first {pca.n_components_} PCs): {var_explained.sum():.1%}")

# Create DataFrame of PCs
pc_df = pd.DataFrame(
    comm_pcs,
    index=comm_filtered.index,
    columns=[f'comm_PC{i+1}' for i in range(pca.n_components_)]
)
pc_cols = list(pc_df.columns)

# Map PCs to genomes via spatial join
genome_df = genome_df.merge(
    pc_df.reset_index().rename(columns={'sample_id': 'mba_sample_id'}),
    on='mba_sample_id', how='left'
)
has_pcs = genome_df[pc_cols[0]].notna()
print(f"  Genomes with community PCs: {has_pcs.sum():,}")

# ── Step 5: Check if community PCs correlate with metals ────────────
print(f"\nStep 5: Do community PCs predict metal concentrations?")
for metal in METALS:
    m_name = metal.replace('PF1_', '')
    valid = genome_df[metal].notna() & has_pcs
    if valid.sum() < 50:
        continue
    X = genome_df.loc[valid, pc_cols].values
    y = genome_df.loc[valid, metal].values
    from sklearn.linear_model import LinearRegression
    reg = LinearRegression().fit(X, y)
    r2 = reg.score(X, y)
    print(f"  {m_name}: R²={r2:.3f} (community PCs → metal)")

# ── Step 6: Meta-analysis with community covariates ─────────────────
print(f"\nStep 6: Within-genus meta-analysis...")

genus_cts = genome_df.genus.value_counts()
usable_genera = genus_cts[genus_cts >= MIN_GENOMES_PER_GENUS]
genus_idx = {g: genome_df.index[genome_df.genus == g].values for g in usable_genera.index}
print(f"  Usable genera: {len(usable_genera)}")

# Run three covariate sets for each KO × metal
cov_sets = {
    'raw': None,
    'kitchen_sink': ['genome_size'] + ENV_COLS,
    'kitchen_sink_plus_community': ['genome_size'] + ENV_COLS + pc_cols,
}

all_results = {k: [] for k in cov_sets}

for i, ko_id in enumerate(variable_kos):
    if (i + 1) % 500 == 0:
        print(f"  KO {i+1}/{len(variable_kos)}...")
    if ko_id not in genome_df.columns:
        continue
    ko_vals = genome_df[ko_id].values

    for metal in METALS:
        met_vals = genome_df[metal].values

        for cov_name, covariates in cov_sets.items():
            effects = []
            for genus, idx in genus_idx.items():
                ko = ko_vals[idx]
                met = met_vals[idx]
                mask = np.isfinite(met)

                if covariates:
                    for c in covariates:
                        if c in genome_df.columns:
                            cv = pd.to_numeric(genome_df[c], errors='coerce').values[idx]
                            cm = np.isfinite(cv)
                            if cm[mask].sum() >= mask.sum() * 0.5:
                                mask &= cm

                if mask.sum() < MIN_GENOMES_PER_GENUS:
                    continue
                ko_m = ko[mask]
                if ko_m.std() == 0:
                    continue
                prev = ko_m.mean()
                if prev < 0.05 or prev > 0.95:
                    continue

                if covariates:
                    avail_cols = []
                    for c in covariates:
                        if c in genome_df.columns:
                            cv = pd.to_numeric(genome_df[c], errors='coerce').values[idx][mask]
                            if np.isfinite(cv).all() and cv.std() > 0:
                                avail_cols.append(cv)
                    if avail_cols:
                        X = np.column_stack(avail_cols)
                        try:
                            Xf = np.column_stack([np.ones(X.shape[0]), X])
                            b, _, _, _ = np.linalg.lstsq(Xf, met[mask], rcond=None)
                            resid = met[mask] - Xf @ b
                            rho, _ = stats.pointbiserialr(ko_m, resid)
                            if np.isfinite(rho):
                                effects.append((mask.sum(), rho))
                            continue
                        except:
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
            all_results[cov_name].append({
                'ko_id': ko_id, 'metal': metal.replace('PF1_', ''),
                'is_target': ko_id in TARGET_KOS,
                'meta_rho': np.tanh(mz), 'meta_p': p, 'n_genera': len(effects),
            })

# ── Results ──────────────────────────────────────────────────────────
print(f"\n{'='*70}")
print("RESULTS: MicrobeAtlas OTU Linkage Analysis")
print(f"{'='*70}\n")

for cov_name, results in all_results.items():
    if not results:
        print(f"  {cov_name}: no results")
        continue
    rdf = pd.DataFrame(results)
    _, q_vals, _, _ = multipletests(rdf.meta_p.values, method='fdr_bh')
    rdf['q_fdr'] = q_vals
    n_sig = (rdf.q_fdr < 0.05).sum()
    rdf.to_csv(OUTDIR / f'mba_otu_{cov_name}.csv', index=False)
    print(f"  {cov_name:40s}: {n_sig:>5d}/{len(rdf)} significant (FDR<0.05)")

    if cov_name == 'kitchen_sink_plus_community':
        print(f"\n    Per-metal (community-controlled):")
        for m in ['Hg', 'As', 'Cu', 'Cr', 'Cd', 'Pb']:
            sub = rdf[rdf.metal == m]
            n = (sub.q_fdr < 0.05).sum()
            print(f"      {m}: {n}/{len(sub)}")

        if n_sig > 0:
            print(f"\n    Top 20 hits surviving community control:")
            for _, r in rdf[rdf.q_fdr < 0.05].nsmallest(20, 'meta_p').iterrows():
                gene = TARGET_KOS.get(r.ko_id, r.ko_id)
                tag = '*' if r.is_target else ' '
                print(f"      {tag} {gene:18s} × {r.metal:3s}: ρ={r.meta_rho:+.4f} "
                      f"q={r.q_fdr:.4f} ({r.n_genera}g)")

# Compare: what fraction of raw hits survive each control level?
print(f"\n{'='*70}")
print("COMPARISON: Signal attenuation by covariate set")
print(f"{'='*70}\n")

raw_df = pd.DataFrame(all_results['raw'])
if len(raw_df) > 0:
    _, raw_q, _, _ = multipletests(raw_df.meta_p.values, method='fdr_bh')
    raw_df['q_fdr'] = raw_q
    raw_sig_pairs = set(raw_df[raw_df.q_fdr < 0.05].apply(
        lambda r: f"{r.ko_id}×{r.metal}", axis=1))

    for cov_name in ['kitchen_sink', 'kitchen_sink_plus_community']:
        if not all_results[cov_name]:
            continue
        cdf = pd.DataFrame(all_results[cov_name])
        _, cq, _, _ = multipletests(cdf.meta_p.values, method='fdr_bh')
        cdf['q_fdr'] = cq
        cov_sig_pairs = set(cdf[cdf.q_fdr < 0.05].apply(
            lambda r: f"{r.ko_id}×{r.metal}", axis=1))
        survived = raw_sig_pairs & cov_sig_pairs
        print(f"  Raw significant: {len(raw_sig_pairs)}")
        print(f"  → {cov_name}: {len(cov_sig_pairs)} sig, "
              f"{len(survived)} of raw hits survive ({len(survived)/max(len(raw_sig_pairs),1):.0%})")

print("\nDONE")

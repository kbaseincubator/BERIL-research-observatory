#!/usr/bin/env python3
"""
Clean first-pass survey: which KOs vary with environmental metals?

Data: per_ko_metal_associations project
- 6,451 KOs × 6 metals (Cu, Pb, Cr, As, Cd, Hg)
- 8,553 MGnify soil metagenomes with CSU-derived soil metal concentrations
- Latitude-adjusted logistic regression (where converged) + Spearman ρ

Controls applied:
1. Latitude adjustment (geographic confounding)
2. FDR correction (multiple testing across all KO × metal pairs)
3. Cross-dataset replication (MGnify vs SPIRE, n=299)
4. Direction consistency check
5. KEGG pathway annotation for biological interpretation

NOT controlled here (flag for follow-up):
- Genome size
- Phylogenetic non-independence
- Metal co-correlation
"""
import os
for var in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ.setdefault(var, '1')

import pandas as pd
import numpy as np
from statsmodels.stats.multitest import multipletests
from pathlib import Path
from collections import Counter

PKA = Path('/home/hmacgregor/BERIL-research-observatory/projects/per_ko_metal_associations/data')
CME = Path('/home/hmacgregor/BERIL-research-observatory/projects/comprehensive_metal_ecology/data')
KEGG_LIST = Path('/home/hmacgregor/BERIL-research-observatory/projects/final_draft/data/kegg_ko_list.csv')
OUT = CME / 'clean_ko_metal_survey_results.csv'

# ── 1. Load latitude-adjusted MGnify results ────────────────────────────────
mg = pd.read_csv(PKA / 'mgnify_adj_ko_associations.csv')
print(f"MGnify latitude-adjusted: {mg.shape}")
print(f"  Unique KOs: {mg.ko_id.nunique()}, Metals: {sorted(mg.metal.unique())}")
print(f"  Converged logistic: {mg.converged.sum()}/{len(mg)}")

# Use Spearman as primary (available for all); logistic beta as secondary
# Spearman columns
spearman_cols = [c for c in mg.columns if 'spearman' in c.lower()]
print(f"  Spearman columns: {spearman_cols}")

# ── 2. FDR on Spearman p-values ─────────────────────────────────────────────
mg = mg.rename(columns={'spearman_rho': 'rho', 'spearman_p': 'sp_p'})
mask = mg['sp_p'].notna() & np.isfinite(mg['sp_p'])
print(f"  Valid Spearman p-values: {mask.sum()}/{len(mg)}")

q = np.full(len(mg), np.nan)
reject, q_vals, _, _ = multipletests(mg.loc[mask, 'sp_p'].values, method='fdr_bh')
q[mask.values] = q_vals
mg['q_spearman'] = q

for threshold in [0.001, 0.01, 0.05, 0.10]:
    n = (mg.q_spearman < threshold).sum()
    print(f"  q < {threshold}: {n} KO-metal pairs ({n/len(mg)*100:.1f}%)")

# ── 3. Load SPIRE latitude-adjusted for replication ──────────────────────────
sp = pd.read_csv(PKA / 'spire_adj_ko_associations.csv')
sp = sp.rename(columns={'spearman_rho': 'rho_spire', 'spearman_p': 'sp_p_spire'})
print(f"\nSPIRE latitude-adjusted: {sp.shape}")
print(f"  Unique KOs: {sp.ko_id.nunique()}")

# ── 4. Merge MGnify × SPIRE ─────────────────────────────────────────────────
merged = mg.merge(
    sp[['ko_id', 'metal', 'rho_spire', 'sp_p_spire']],
    on=['ko_id', 'metal'], how='left', suffixes=('', '_sp')
)
merged['direction_consistent'] = (np.sign(merged['rho']) == np.sign(merged['rho_spire']))
merged['spire_sig'] = merged['sp_p_spire'] < 0.05
merged['both_sig'] = (merged['q_spearman'] < 0.05) & merged['spire_sig']
merged['replicated'] = merged['both_sig'] & merged['direction_consistent']

print(f"\nCross-dataset replication (MGnify q<0.05 + SPIRE p<0.05 + same direction):")
print(f"  Replicated: {merged.replicated.sum()}")
print(f"  Both sig but opposite: {(merged.both_sig & ~merged.direction_consistent).sum()}")

# ── 5. KEGG annotations ─────────────────────────────────────────────────────
kegg = pd.read_csv(KEGG_LIST)
kegg.columns = ['ko_id', 'description']
merged = merged.merge(kegg, on='ko_id', how='left')

# Also flag curated metal genes
curated = pd.read_csv(CME / 'curated_mrg_ko_ids_v2.csv')
curated_set = set(curated['KO'].values)
merged['is_curated_metal'] = merged.ko_id.isin(curated_set)

# ── 6. Tier the results ─────────────────────────────────────────────────────
# Tier 1: Replicated (FDR + SPIRE + direction)
# Tier 2: FDR significant but NOT replicated
# Tier 3: Nominally significant but not FDR

merged['tier'] = 'NS'
merged.loc[merged.q_spearman < 0.05, 'tier'] = 'FDR_only'
merged.loc[merged.replicated, 'tier'] = 'REPLICATED'

print(f"\n=== TIER BREAKDOWN ===")
print(merged.tier.value_counts().to_string())
print()

# ── 7. Show Tier 1: Replicated results ───────────────────────────────────────
rep = merged[merged.tier == 'REPLICATED'].sort_values('q_spearman')
print(f"=== TIER 1: REPLICATED ({len(rep)} KO-metal pairs) ===")
print(f"  Unique KOs: {rep.ko_id.nunique()}")
print(f"  Metal breakdown:")
print(f"  {rep.metal.value_counts().to_string()}")
print()

for _, r in rep.iterrows():
    metal_label = r.metal.replace('PF1_', '')
    curated_flag = ' [CURATED METAL GENE]' if r.is_curated_metal else ''
    desc = str(r.description)[:70] if pd.notna(r.description) else 'unknown'
    print(f"  {r.ko_id:10s} × {metal_label:3s}  ρ={r.rho:+.4f} q={r.q_spearman:.2e}  "
          f"SPIRE ρ={r.rho_spire:+.4f} p={r.sp_p_spire:.3f}  "
          f"{desc}{curated_flag}")

# ── 8. Show Tier 2: FDR-only (top 30) ───────────────────────────────────────
fdr = merged[(merged.tier == 'FDR_only')].sort_values('q_spearman')
print(f"\n=== TIER 2: FDR SIGNIFICANT, NOT REPLICATED (top 30 of {len(fdr)}) ===")
for _, r in fdr.head(30).iterrows():
    metal_label = r.metal.replace('PF1_', '')
    curated_flag = ' [CURATED]' if r.is_curated_metal else ''
    spire_info = f"SPIRE ρ={r.rho_spire:+.4f}" if pd.notna(r.rho_spire) else "no SPIRE"
    desc = str(r.description)[:55] if pd.notna(r.description) else 'unknown'
    print(f"  {r.ko_id:10s} × {metal_label:3s}  ρ={r.rho:+.4f} q={r.q_spearman:.2e}  "
          f"{spire_info}  {desc}{curated_flag}")

# ── 9. Pathway-level aggregation ─────────────────────────────────────────────
# For FDR survivors, what KEGG pathways are enriched?
fdr_all = merged[merged.q_spearman < 0.05].copy()
print(f"\n=== PATHWAY / FUNCTIONAL ANALYSIS of FDR survivors ===")
print(f"Total FDR survivors: {len(fdr_all)}, unique KOs: {fdr_all.ko_id.nunique()}")

# Parse KEGG descriptions to extract gene names and broad categories
def extract_gene_and_category(desc):
    if pd.isna(desc):
        return 'unknown', 'Unknown'
    parts = str(desc).split(';')
    gene = parts[0].strip().split(',')[0].strip() if parts else 'unknown'
    # Crude category from description keywords
    d = str(desc).lower()
    if any(x in d for x in ['transport', 'permease', 'abc', 'porin', 'channel']):
        return gene, 'Transport'
    elif any(x in d for x in ['regulat', 'transcription', 'sensor', 'response regulator', 'kinase']):
        return gene, 'Regulation'
    elif any(x in d for x in ['reductase', 'oxidase', 'dehydrogenase', 'synthase', 'synthetase', 'transferase', 'lyase', 'isomerase', 'ligase', 'hydrolase', 'mutase']):
        return gene, 'Enzyme'
    elif any(x in d for x in ['ribosom', 'translat', 'trna', 'rrna']):
        return gene, 'Translation'
    elif any(x in d for x in ['flagell', 'pilus', 'motil', 'chemotax']):
        return gene, 'Motility'
    elif any(x in d for x in ['resist', 'efflux', 'pump', 'multidrug', 'beta-lactam']):
        return gene, 'Resistance/Efflux'
    elif any(x in d for x in ['secretion', 'type i', 'type ii', 'type iii', 'type iv', 'type vi']):
        return gene, 'Secretion'
    elif any(x in d for x in ['dna', 'repair', 'recomb', 'replica', 'topoisom', 'gyrase']):
        return gene, 'DNA/Repair'
    elif any(x in d for x in ['phage', 'toxin', 'antitoxin', 'crispr', 'restriction']):
        return gene, 'Defense/MGE'
    else:
        return gene, 'Other/Metabolism'

fdr_all[['gene_short', 'func_category']] = fdr_all['description'].apply(
    lambda x: pd.Series(extract_gene_and_category(x)))

print(f"\nFunctional category breakdown:")
cat_counts = fdr_all.func_category.value_counts()
for cat, n in cat_counts.items():
    n_curated = fdr_all[fdr_all.func_category == cat].is_curated_metal.sum()
    print(f"  {cat:25s}: {n:4d} ({n_curated} curated metal genes)")

# ── 10. Direction analysis ───────────────────────────────────────────────────
print(f"\n=== DIRECTION: positive vs negative associations ===")
for metal in sorted(fdr_all.metal.unique()):
    pos = fdr_all[(fdr_all.metal == metal) & (fdr_all.rho > 0)]
    neg = fdr_all[(fdr_all.metal == metal) & (fdr_all.rho < 0)]
    print(f"  {metal.replace('PF1_',''):3s}: +{len(pos):4d} (KO MORE prevalent at higher metal)  "
          f"-{len(neg):4d} (KO LESS prevalent at higher metal)")

# ── 11. Effect sizes ─────────────────────────────────────────────────────────
print(f"\n=== EFFECT SIZE DISTRIBUTION (FDR survivors) ===")
print(f"  |ρ| quartiles: {fdr_all.rho.abs().quantile([0.25, 0.5, 0.75]).to_dict()}")
print(f"  |ρ| > 0.1: {(fdr_all.rho.abs() > 0.1).sum()}")
print(f"  |ρ| > 0.2: {(fdr_all.rho.abs() > 0.2).sum()}")
print(f"  |ρ| > 0.3: {(fdr_all.rho.abs() > 0.3).sum()}")

# Top effect sizes
print(f"\nLargest effect sizes (|ρ| > 0.15):")
big = fdr_all[fdr_all.rho.abs() > 0.15].sort_values('rho', key=abs, ascending=False)
for _, r in big.head(20).iterrows():
    metal_label = r.metal.replace('PF1_', '')
    curated_flag = ' [CURATED]' if r.is_curated_metal else ''
    spire = f"SPIRE={r.rho_spire:+.3f}" if pd.notna(r.rho_spire) else ""
    print(f"  {r.ko_id:10s} × {metal_label:3s}  ρ={r.rho:+.4f} q={r.q_spearman:.2e}  {spire:20s}  {r.gene_short:15s} ({r.func_category}){curated_flag}")

# ── 12. Surprising results: non-metal genes with strong metal associations ──
print(f"\n=== SURPRISING: Non-curated KOs with strong metal associations ===")
surprising = fdr_all[(~fdr_all.is_curated_metal) & (fdr_all.rho.abs() > 0.05)].sort_values('q_spearman')
cat_surprise = surprising.func_category.value_counts()
print(f"Categories of surprising associations:")
for cat, n in cat_surprise.items():
    print(f"  {cat:25s}: {n:4d}")

print(f"\nTop 30 surprising (non-metal, |ρ|>0.05):")
for _, r in surprising.head(30).iterrows():
    metal_label = r.metal.replace('PF1_', '')
    desc = str(r.description)[:60] if pd.notna(r.description) else 'unknown'
    print(f"  {r.ko_id:10s} × {metal_label:3s}  ρ={r.rho:+.4f} q={r.q_spearman:.2e}  {desc}")

# ── 13. Metal-specific gene signatures ───────────────────────────────────────
print(f"\n=== METAL-SPECIFIC vs SHARED signatures ===")
fdr_kos = fdr_all.groupby('ko_id')['metal'].apply(set).reset_index()
fdr_kos['n_metals'] = fdr_kos.metal.apply(len)
fdr_kos_single = fdr_kos[fdr_kos.n_metals == 1]
fdr_kos_multi = fdr_kos[fdr_kos.n_metals > 1]
print(f"  KOs associated with exactly 1 metal: {len(fdr_kos_single)}")
print(f"  KOs associated with 2+ metals: {len(fdr_kos_multi)}")
for _, r in fdr_kos_multi.sort_values('n_metals', ascending=False).head(10).iterrows():
    metals = ', '.join(sorted(m.replace('PF1_','') for m in r.metal))
    desc_row = merged[merged.ko_id == r.ko_id].iloc[0]
    desc = str(desc_row.description)[:50] if pd.notna(desc_row.description) else '?'
    print(f"  {r.ko_id:10s} ({r.n_metals} metals: {metals:30s})  {desc}")

# ── 14. Save full results ────────────────────────────────────────────────────
cols_out = ['ko_id', 'metal', 'rho', 'sp_p', 'q_spearman', 'rho_spire', 'sp_p_spire',
            'direction_consistent', 'replicated', 'tier', 'description', 'is_curated_metal',
            'n_present', 'n_total']
cols_out = [c for c in cols_out if c in merged.columns]
merged[cols_out].to_csv(OUT, index=False)
print(f"\nSaved {len(merged)} rows to {OUT}")

print("\nDONE.")

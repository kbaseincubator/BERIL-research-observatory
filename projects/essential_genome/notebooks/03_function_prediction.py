#!/usr/bin/env python3
"""
NB03: Predict function for hypothetical essential genes using module context.

For each hypothetical essential gene with orthologs:
  - Find non-essential orthologs in other organisms
  - Check if any non-essential ortholog is in an ICA fitness module
  - Transfer the module's enrichment labels and family annotations

Runs locally using cached data.
"""

import pandas as pd
import numpy as np
from pathlib import Path

# ============================================================================
# Setup
# ============================================================================
PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / 'data'
FIG_DIR = PROJECT_DIR / 'figures'

FM_DIR = PROJECT_DIR.parent / 'fitness_modules' / 'data'
MODULE_DIR = FM_DIR / 'modules'
FAMILY_DIR = FM_DIR / 'module_families'

print("Loading data...")
essential = pd.read_csv(DATA_DIR / 'all_essential_genes.tsv', sep='\t', low_memory=False)
essential['is_essential'] = essential['is_essential'].astype(str).str.strip().str.lower() == 'true'
essential['locusId'] = essential['locusId'].astype(str)

og_df = pd.read_csv(DATA_DIR / 'all_ortholog_groups.csv')
og_df['locusId'] = og_df['locusId'].astype(str)

# ============================================================================
# 1. Build lookup dictionaries (fast)
# ============================================================================
print("\n=== BUILDING LOOKUPS ===")

# Essential status lookup
ess_lookup = {}
for _, r in essential.iterrows():
    ess_lookup[(r['orgId'], r['locusId'])] = r['is_essential']
print(f"Essential status lookup: {len(ess_lookup):,} genes")

# Gene → OG lookup
gene_to_og = {}
for _, r in og_df.iterrows():
    gene_to_og[(r['orgId'], r['locusId'])] = r['OG_id']

# OG → members lookup
og_members = og_df.groupby('OG_id').apply(
    lambda g: list(zip(g['orgId'], g['locusId']))
).to_dict()

# Module membership: (orgId, locusId) → [modules]
gene_to_modules = {}
module_orgs = []
for f in sorted(MODULE_DIR.glob('*_gene_membership.csv')):
    org = f.stem.replace('_gene_membership', '')
    module_orgs.append(org)
    membership = pd.read_csv(f, index_col=0)
    for mod in membership.columns:
        mod_genes = membership.index[membership[mod] == 1]
        for gene in mod_genes:
            key = (org, str(gene))
            gene_to_modules.setdefault(key, []).append(mod)
print(f"Module membership: {len(gene_to_modules):,} genes in {len(module_orgs)} organisms")

# Module annotations: (orgId, module) → best annotation
module_best_ann = {}
for org in module_orgs:
    ann_file = MODULE_DIR / f'{org}_module_annotations.csv'
    if not ann_file.exists() or ann_file.stat().st_size < 10:
        continue
    ann = pd.read_csv(ann_file)
    sig = ann[ann['significant'] == True]
    for mod, grp in sig.groupby('module'):
        best = grp.loc[grp['fdr'].idxmin()]
        module_best_ann[(org, mod)] = {
            'term': best['term'], 'db': best['database'], 'fdr': best['fdr']
        }
print(f"Annotated modules: {len(module_best_ann):,}")

# Module families
mod_to_family = {}
for _, r in pd.read_csv(FAMILY_DIR / 'module_families.csv').iterrows():
    mod_to_family[(r['orgId'], r['module'])] = r['familyId']

fam_ann = {}
for _, r in pd.read_csv(FAMILY_DIR / 'family_annotations.csv').iterrows():
    fam_ann[r['familyId']] = {
        'consensus_term': r['consensus_term'],
        'consensus_db': r.get('consensus_db', ''),
        'n_organisms': r['n_organisms'],
    }

# ============================================================================
# 2. Identify hypothetical essential genes with orthologs
# ============================================================================
print("\n=== IDENTIFYING TARGETS ===")

hyp_patterns = ['hypothetical', 'uncharacterized', 'unknown function', 'DUF']
ess_genes = essential[essential['is_essential']].copy()
ess_genes['is_hypothetical'] = ess_genes['desc'].apply(
    lambda d: any(p.lower() in str(d).lower() for p in hyp_patterns)
    if pd.notna(d) else True
)

# Use merge instead of row-wise apply (performance pitfall)
og_lookup = og_df[['orgId', 'locusId', 'OG_id']].drop_duplicates()
ess_genes = ess_genes.merge(og_lookup, on=['orgId', 'locusId'], how='left')
ess_genes.rename(columns={'OG_id': 'og_id'}, inplace=True)

targets = ess_genes[ess_genes['is_hypothetical'] & ess_genes['og_id'].notna()]
print(f"Hypothetical essential genes: {ess_genes['is_hypothetical'].sum():,}")
print(f"  With orthologs (targets): {len(targets):,}")

# ============================================================================
# 3. Predict function via ortholog-module transfer
# ============================================================================
print("\n=== PREDICTING FUNCTION ===")

predictions = []
n_checked = 0

for _, gene in targets.iterrows():
    org = gene['orgId']
    locus = gene['locusId']
    og_id = gene['og_id']

    members = og_members.get(og_id, [])

    best_pred = None
    best_conf = -1

    for m_org, m_locus in members:
        if m_org == org and m_locus == locus:
            continue

        # Skip if also essential
        if ess_lookup.get((m_org, m_locus), True):
            continue

        # Check if in module
        mods = gene_to_modules.get((m_org, m_locus), [])
        for mod in mods:
            ann = module_best_ann.get((m_org, mod))
            if ann is None:
                continue

            fam_id = mod_to_family.get((m_org, mod), '')
            fam_info = fam_ann.get(fam_id, {})

            conf = -np.log10(max(ann['fdr'], 1e-20))
            if fam_id and fam_info.get('n_organisms', 0) > 1:
                conf += np.log10(fam_info['n_organisms'])

            if conf > best_conf:
                best_conf = conf
                best_pred = {
                    'target_orgId': org,
                    'target_locusId': locus,
                    'target_desc': gene['desc'],
                    'OG_id': og_id,
                    'source_orgId': m_org,
                    'source_locusId': m_locus,
                    'source_module': mod,
                    'predicted_term': ann['term'],
                    'predicted_db': ann['db'],
                    'enrichment_fdr': ann['fdr'],
                    'familyId': fam_id,
                    'family_n_organisms': fam_info.get('n_organisms', 0),
                    'family_consensus': fam_info.get('consensus_term', ''),
                    'confidence': conf,
                }

    if best_pred:
        predictions.append(best_pred)

    n_checked += 1
    if n_checked % 1000 == 0:
        print(f"  Checked {n_checked:,}/{len(targets):,} genes, "
              f"{len(predictions):,} predictions so far")

pred_df = pd.DataFrame(predictions)
print(f"\nTotal predictions: {len(pred_df):,} / {len(targets):,} targets "
      f"({len(pred_df)/len(targets)*100:.1f}%)")

if len(pred_df) > 0:
    pred_df = pred_df.sort_values('confidence', ascending=False)
    pred_df.to_csv(DATA_DIR / 'essential_predictions.tsv', sep='\t', index=False)
    print(f"Saved: data/essential_predictions.tsv")

    n_fam = (pred_df['familyId'] != '').sum()
    print(f"  Family-backed: {n_fam:,}")
    print(f"  Module-only: {len(pred_df) - n_fam:,}")

    # Top predictions
    print(f"\nTop 25 predictions:")
    print(f"{'organism':<12} {'locusId':<14} {'predicted':<18} {'db':<6} "
          f"{'FDR':<11} {'family':<7} {'conf':>6}")
    print("-" * 80)
    for _, r in pred_df.head(25).iterrows():
        print(f"{r['target_orgId']:<12} {str(r['target_locusId']):<14} "
              f"{str(r['predicted_term'])[:16]:<18} "
              f"{str(r['predicted_db'])[:5]:<6} "
              f"{r['enrichment_fdr']:<11.2e} "
              f"{str(r['familyId'])[:6]:<7} "
              f"{r['confidence']:>6.1f}")

    # Per organism
    print(f"\nPredictions per organism:")
    for org, cnt in pred_df.groupby('target_orgId').size().sort_values(ascending=False).items():
        print(f"  {org}: {cnt}")

# ============================================================================
# Summary
# ============================================================================
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
n_ess = essential['is_essential'].sum()
n_hyp = ess_genes['is_hypothetical'].sum()
n_hyp_og = len(targets)
n_hyp_orphan = n_hyp - n_hyp_og
print(f"Essential genes: {n_ess:,}")
print(f"Hypothetical essentials: {n_hyp:,} ({n_hyp/n_ess*100:.1f}%)")
print(f"  With orthologs: {n_hyp_og:,} (predictable)")
print(f"  Orphans: {n_hyp_orphan:,} (not predictable by this method)")
if len(pred_df) > 0:
    print(f"Predictions: {len(pred_df):,} ({len(pred_df)/n_hyp_og*100:.1f}% of predictable)")

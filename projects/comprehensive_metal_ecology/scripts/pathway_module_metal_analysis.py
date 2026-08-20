#!/usr/bin/env python3
"""
Pathway/module-level metal association analysis.

Aggregates KO-level metal associations to functional categories and tests:
1. KEGG main-category enrichment among FDR-significant KOs
2. Curated metal-gene category enrichment (resistance vs transport vs cofactor etc.)
3. Within-category direction coherence (do all KOs in a pathway go the same way?)
4. Per-metal pathway signatures
5. Cross-reference with within-genus survivors

Data sources:
- clean_ko_metal_survey_results.csv (6,451 KOs × 6 metals, FDR-corrected)
- within_genus_ko_metal_results.csv (25 target KOs × 6 metals)
- curated_mrg_ko_ids_v2.csv (730 curated metal-related KOs with categories)
- kegg_ko_hierarchy.csv (KEGG main category annotations)
"""
import os
for var in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ.setdefault(var, '1')

import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats
from statsmodels.stats.multitest import multipletests
from collections import Counter

CME = Path('/home/hmacgregor/BERIL-research-observatory/projects/comprehensive_metal_ecology/data')
KEGG = Path('/home/hmacgregor/BERIL-research-observatory/projects/final_draft/data')

# ── 1. Load data ───────────────────────────────────────────────────────────────
survey = pd.read_csv(CME / 'clean_ko_metal_survey_results.csv')
curated = pd.read_csv(CME / 'curated_mrg_ko_ids_v2.csv')
kegg_h = pd.read_csv(KEGG / 'kegg_ko_hierarchy.csv')
kegg_list = pd.read_csv(KEGG / 'kegg_ko_list.csv', names=['ko_id', 'description'])

print(f"Survey: {survey.shape[0]:,} KO-metal pairs, {survey.ko_id.nunique()} unique KOs")
print(f"Curated metal genes: {len(curated)}")
print(f"KEGG hierarchy entries: {len(kegg_h)}")

# Clean metal names
survey['metal_short'] = survey.metal.str.replace('PF1_', '')
METALS = sorted(survey.metal_short.unique())
print(f"Metals: {METALS}")

# FDR status
n_fdr = (survey.q_spearman < 0.05).sum()
n_rep = survey.replicated.sum()
print(f"FDR < 0.05: {n_fdr:,} ({n_fdr/len(survey)*100:.1f}%)")
print(f"Replicated: {n_rep:,}")

# ── 2. KEGG main-category enrichment ──────────────────────────────────────────
print(f"\n{'='*90}")
print("KEGG MAIN-CATEGORY ENRICHMENT AMONG FDR-SIGNIFICANT KOs")
print(f"{'='*90}")

# Map KOs to main categories (take first match to avoid duplicates)
kegg_map = kegg_h.drop_duplicates(subset='id')[['id', 'main_category']].rename(
    columns={'id': 'ko_id'})
# Only keep meaningful prokaryotic categories
keep_cats = ['Metabolism', 'Genetic Information Processing',
             'Environmental Information Processing', 'Cellular Processes']
kegg_map = kegg_map[kegg_map.main_category.isin(keep_cats)]

survey_kegg = survey.merge(kegg_map, on='ko_id', how='left')
survey_kegg['has_category'] = survey_kegg.main_category.notna()
survey_kegg['is_fdr'] = survey_kegg.q_spearman < 0.05

# Per-category Fisher test: is this category overrepresented among FDR-sig KOs?
all_kos = survey_kegg.ko_id.unique()
fdr_kos = survey_kegg[survey_kegg.is_fdr].ko_id.unique()

# Need KO-level (not KO×metal level) for enrichment
ko_cat = survey_kegg.drop_duplicates('ko_id')[['ko_id', 'main_category']]
ko_fdr_any = set(fdr_kos)

print(f"\nKOs with KEGG category: {ko_cat.main_category.notna().sum()}/{len(ko_cat)}")
print(f"KOs with ≥1 FDR hit: {len(ko_fdr_any)}")

enrichment_results = []
for cat in keep_cats:
    cat_kos = set(ko_cat[ko_cat.main_category == cat].ko_id)
    other_kos = set(ko_cat[ko_cat.main_category.notna()].ko_id) - cat_kos

    a = len(cat_kos & ko_fdr_any)     # in category, FDR sig
    b = len(cat_kos - ko_fdr_any)     # in category, not sig
    c = len(other_kos & ko_fdr_any)   # not in category, sig
    d = len(other_kos - ko_fdr_any)   # not in category, not sig

    odds, p = stats.fisher_exact([[a, b], [c, d]])
    enrichment_results.append({
        'category': cat,
        'n_in_cat': len(cat_kos),
        'n_sig': a,
        'pct_sig': a/len(cat_kos)*100 if len(cat_kos) > 0 else 0,
        'odds_ratio': odds,
        'p_fisher': p
    })

enr_df = pd.DataFrame(enrichment_results).sort_values('p_fisher')
_, enr_df['q_fdr'], _, _ = multipletests(enr_df.p_fisher, method='fdr_bh')

print(f"\n{'Category':45s} {'n_KOs':>6s} {'n_sig':>6s} {'%sig':>6s} {'OR':>7s} {'p':>10s} {'q':>10s}")
print('-' * 90)
for _, r in enr_df.iterrows():
    sig = '***' if r.q_fdr < 0.001 else '**' if r.q_fdr < 0.01 else '*' if r.q_fdr < 0.05 else ''
    print(f"{r.category:45s} {r.n_in_cat:6.0f} {r.n_sig:6.0f} {r.pct_sig:5.1f}% "
          f"{r.odds_ratio:7.2f} {r.p_fisher:10.2e} {r.q_fdr:10.4f} {sig}")

# ── 3. Curated metal-gene category enrichment ────────────────────────────────
print(f"\n{'='*90}")
print("CURATED METAL-GENE CATEGORY ENRICHMENT")
print(f"{'='*90}")

curated_map = curated[['KO', 'primary_category']].rename(columns={'KO': 'ko_id'})
curated_cats = curated_map.primary_category.value_counts()
print(f"\nCurated categories:")
for cat, n in curated_cats.items():
    print(f"  {cat:40s}: {n:4d} KOs")

# For each curated category, test enrichment among FDR-sig KOs
curated_set = set(curated_map.ko_id)
all_tested_kos = set(survey.ko_id.unique())

cat_enrichment = []
for cat in curated_cats.index:
    cat_kos = set(curated_map[curated_map.primary_category == cat].ko_id) & all_tested_kos
    non_cat_kos = all_tested_kos - cat_kos

    a = len(cat_kos & ko_fdr_any)
    b = len(cat_kos - ko_fdr_any)
    c = len(non_cat_kos & ko_fdr_any)
    d = len(non_cat_kos - ko_fdr_any)

    if a + b == 0:
        continue
    odds, p = stats.fisher_exact([[a, b], [c, d]])

    # Direction: what fraction of FDR-sig hits from this category are positive?
    cat_fdr = survey[(survey.ko_id.isin(cat_kos)) & (survey.q_spearman < 0.05)]
    frac_pos = (cat_fdr.rho > 0).mean() if len(cat_fdr) > 0 else np.nan

    # Metal specificity: which metals dominate for this category?
    metal_counts = cat_fdr.metal_short.value_counts().to_dict() if len(cat_fdr) > 0 else {}

    cat_enrichment.append({
        'category': cat,
        'n_tested': len(cat_kos),
        'n_sig': a,
        'pct_sig': a / len(cat_kos) * 100,
        'odds_ratio': odds,
        'p_fisher': p,
        'frac_positive': frac_pos,
        'top_metal': max(metal_counts, key=metal_counts.get) if metal_counts else '',
        'n_fdr_pairs': len(cat_fdr),
    })

cat_df = pd.DataFrame(cat_enrichment).sort_values('p_fisher')
if len(cat_df) > 0:
    _, cat_df['q_fdr'], _, _ = multipletests(cat_df.p_fisher, method='fdr_bh')
else:
    cat_df['q_fdr'] = np.nan

print(f"\n{'Category':40s} {'n_test':>6s} {'n_sig':>5s} {'%sig':>6s} {'OR':>7s} {'p':>10s} {'q':>10s} {'%pos':>5s} {'top_metal':>8s}")
print('-' * 100)
for _, r in cat_df.iterrows():
    sig = '***' if r.q_fdr < 0.001 else '**' if r.q_fdr < 0.01 else '*' if r.q_fdr < 0.05 else ''
    print(f"{r.category:40s} {r.n_tested:6.0f} {r.n_sig:5.0f} {r.pct_sig:5.1f}% "
          f"{r.odds_ratio:7.2f} {r.p_fisher:10.2e} {r.q_fdr:10.4f} "
          f"{r.frac_positive:5.1%} {r.top_metal:>8s} {sig}")

# ── 4. Per-metal × per-category: direction coherence ─────────────────────────
print(f"\n{'='*90}")
print("PER-METAL × PER-CATEGORY DIRECTION COHERENCE")
print(f"{'='*90}")
print("(Do all KOs in a category go the same direction for a given metal?)")

# Use curated categories (more biologically meaningful)
survey_curated = survey.merge(curated_map, on='ko_id', how='left')
fdr_curated = survey_curated[survey_curated.q_spearman < 0.05].copy()

print(f"\n{'Category':35s} {'Metal':>4s} {'n_sig':>5s} {'%pos':>6s} {'mean_ρ':>8s} {'sign_p':>10s}")
print('-' * 80)

coherence_results = []
for cat in ['Resistance/Detoxification', 'Transport/Homeostasis',
            'Cofactor Biosynthesis', 'Sensing/Regulation',
            'Metal-dependent Metabolism']:
    for metal in METALS:
        subset = fdr_curated[(fdr_curated.primary_category == cat) &
                             (fdr_curated.metal_short == metal)]
        if len(subset) < 3:
            continue
        frac_pos = (subset.rho > 0).mean()
        mean_rho = subset.rho.mean()
        n_pos = (subset.rho > 0).sum()
        sign_p = stats.binomtest(n_pos, len(subset), 0.5).pvalue

        sig = '***' if sign_p < 0.001 else '**' if sign_p < 0.01 else '*' if sign_p < 0.05 else ''
        print(f"{cat:35s} {metal:>4s} {len(subset):5d} {frac_pos:5.1%} {mean_rho:+8.4f} {sign_p:10.4f} {sig}")

        coherence_results.append({
            'category': cat, 'metal': metal, 'n_sig': len(subset),
            'frac_positive': frac_pos, 'mean_rho': mean_rho, 'sign_test_p': sign_p
        })

# ── 5. Oxidative-stress vs non-redox metal split ────────────────────────────
print(f"\n{'='*90}")
print("OXIDATIVE-STRESS METALS (Hg/As/Cu/Cr) vs NON-REDOX METALS (Cd/Pb)")
print(f"{'='*90}")
print("Testing whether the SAME KOs show OPPOSITE directions for the two metal groups")

oxidative = ['Hg', 'As', 'Cu', 'Cr']
non_redox = ['Cd', 'Pb']

fdr_survey = survey[survey.q_spearman < 0.05].copy()

# For each KO, compute mean ρ across oxidative metals and non-redox metals
ko_ox = fdr_survey[fdr_survey.metal_short.isin(oxidative)].groupby('ko_id')['rho'].mean()
ko_nr = fdr_survey[fdr_survey.metal_short.isin(non_redox)].groupby('ko_id')['rho'].mean()

both = pd.DataFrame({'rho_oxidative': ko_ox, 'rho_nonredox': ko_nr}).dropna()
print(f"\nKOs with FDR hits in BOTH groups: {len(both)}")

if len(both) > 0:
    n_same = ((both.rho_oxidative > 0) == (both.rho_nonredox > 0)).sum()
    n_opp = len(both) - n_same
    print(f"  Same direction in both: {n_same} ({n_same/len(both)*100:.1f}%)")
    print(f"  OPPOSITE direction: {n_opp} ({n_opp/len(both)*100:.1f}%)")

    corr, p = stats.spearmanr(both.rho_oxidative, both.rho_nonredox)
    print(f"  Correlation between oxidative ρ and non-redox ρ: {corr:+.3f}, p={p:.2e}")

    # Show top opposite-direction KOs
    both['diff'] = (both.rho_oxidative - both.rho_nonredox).abs()
    both['is_opposite'] = (both.rho_oxidative > 0) != (both.rho_nonredox > 0)
    opposite = both[both.is_opposite].sort_values('diff', ascending=False)

    if len(opposite) > 0:
        opposite = opposite.merge(kegg_list, left_index=True, right_on='ko_id', how='left')
        opposite = opposite.merge(curated_map, on='ko_id', how='left')

        print(f"\nTop 20 OPPOSITE-direction KOs:")
        print(f"{'KO':10s} {'ρ_ox':>7s} {'ρ_nr':>7s} {'curated_cat':>30s} {'description':>50s}")
        print('-' * 110)
        for _, r in opposite.head(20).iterrows():
            cat = str(r.primary_category) if pd.notna(r.get('primary_category')) else ''
            desc = str(r.description)[:50] if pd.notna(r.get('description')) else ''
            curated_flag = ' [CURATED]' if cat else ''
            print(f"{r.ko_id:10s} {r.rho_oxidative:+7.4f} {r.rho_nonredox:+7.4f} "
                  f"{cat:>30s} {desc}{curated_flag}")

# ── 6. KOs with the MOST metal associations (pan-metal genes) ────────────────
print(f"\n{'='*90}")
print("PAN-METAL GENES: KOs significant for 4+ metals")
print(f"{'='*90}")

ko_metal_count = fdr_survey.groupby('ko_id').agg(
    n_metals=('metal_short', 'nunique'),
    metals=('metal_short', lambda x: ','.join(sorted(x.unique()))),
    mean_rho=('rho', 'mean'),
    mean_abs_rho=('rho', lambda x: x.abs().mean()),
).reset_index()

pan = ko_metal_count[ko_metal_count.n_metals >= 4].sort_values('mean_abs_rho', ascending=False)
pan = pan.merge(kegg_list, on='ko_id', how='left')
pan = pan.merge(curated_map, on='ko_id', how='left')

print(f"\nKOs significant for 4+ metals: {len(pan)}")
print(f"  Of which curated metal genes: {pan.primary_category.notna().sum()}")
print(f"\n{'KO':10s} {'n':>2s} {'mean_ρ':>7s} {'|ρ|':>5s} {'metals':>25s} {'cat':>25s} {'description':>45s}")
print('-' * 130)
for _, r in pan.head(30).iterrows():
    cat = str(r.primary_category)[:25] if pd.notna(r.primary_category) else ''
    desc = str(r.description)[:45] if pd.notna(r.description) else ''
    print(f"{r.ko_id:10s} {r.n_metals:2d} {r.mean_rho:+7.4f} {r.mean_abs_rho:5.3f} "
          f"{r.metals:>25s} {cat:>25s} {desc}")

# How many of these pan-metal genes are NOT curated metal genes?
pan_non_curated = pan[pan.primary_category.isna()]
print(f"\nNon-curated pan-metal genes (4+ metals): {len(pan_non_curated)}")
print(f"  These are surprising: not in our metal gene list but vary with 4+ metals")

for _, r in pan_non_curated.head(20).iterrows():
    desc = str(r.description)[:60] if pd.notna(r.description) else ''
    print(f"  {r.ko_id:10s} {r.n_metals} metals ({r.metals:>25s}) mean_ρ={r.mean_rho:+.4f}  {desc}")

# ── 7. Metal-specific pathway enrichment (Fisher per metal × category) ───────
print(f"\n{'='*90}")
print("METAL-SPECIFIC KEGG CATEGORY ENRICHMENT")
print(f"{'='*90}")

metal_cat_results = []
for metal in METALS:
    fdr_metal = set(survey[(survey.q_spearman < 0.05) & (survey.metal_short == metal)].ko_id)
    ns_metal = set(survey[(survey.q_spearman >= 0.05) & (survey.metal_short == metal)].ko_id)

    for cat in keep_cats:
        cat_kos = set(ko_cat[ko_cat.main_category == cat].ko_id)
        other_kos = set(ko_cat[ko_cat.main_category.notna()].ko_id) - cat_kos

        a = len(cat_kos & fdr_metal)
        b = len(cat_kos & ns_metal)
        c = len(other_kos & fdr_metal)
        d = len(other_kos & ns_metal)

        if a + b == 0 or c + d == 0:
            continue
        odds, p = stats.fisher_exact([[a, b], [c, d]])
        metal_cat_results.append({
            'metal': metal, 'category': cat,
            'n_sig': a, 'n_total': a+b,
            'pct_sig': a/(a+b)*100, 'odds_ratio': odds, 'p_fisher': p
        })

mc_df = pd.DataFrame(metal_cat_results)
if len(mc_df) > 0:
    _, mc_df['q_fdr'], _, _ = multipletests(mc_df.p_fisher, method='fdr_bh')

    print(f"\n{'Metal':>4s} {'Category':>45s} {'n_sig':>5s} {'n_tot':>5s} {'%sig':>6s} {'OR':>7s} {'q':>10s}")
    print('-' * 90)
    for _, r in mc_df[mc_df.q_fdr < 0.10].sort_values(['metal', 'q_fdr']).iterrows():
        sig = '***' if r.q_fdr < 0.001 else '**' if r.q_fdr < 0.01 else '*' if r.q_fdr < 0.05 else '†'
        print(f"{r.metal:>4s} {r.category:>45s} {r.n_sig:5.0f} {r.n_total:5.0f} {r.pct_sig:5.1f}% "
              f"{r.odds_ratio:7.2f} {r.q_fdr:10.4f} {sig}")

# ── 8. Within-genus survivors by functional category ─────────────────────────
print(f"\n{'='*90}")
print("WITHIN-GENUS SURVIVORS: FUNCTIONAL BREAKDOWN")
print(f"{'='*90}")

within = pd.read_csv(CME / 'within_genus_ko_metal_results.csv')
within_sig = within[(within.status == 'tested') & (within.q_fdr < 0.05)].copy()

within_sig = within_sig.merge(curated[['KO', 'primary_category', 'is_resistance',
                                        'is_transport', 'is_cofactor']].rename(
    columns={'KO': 'ko_id'}), on='ko_id', how='left')

print(f"\nWithin-genus FDR < 0.05: {len(within_sig)} KO-metal pairs")
print(f"\nBy gene:")
for _, r in within_sig.sort_values('meta_p').iterrows():
    cat = str(r.primary_category)[:25] if pd.notna(r.primary_category) else 'NOT_CURATED'
    print(f"  {r.ko_id:10s} ({r.gene_name:12s}) × {r.metal:3s}: "
          f"meta_ρ={r.meta_rho:+.4f}, q={r.q_fdr:.2e}, {r.n_genera} genera  [{cat}]")

# Summary: what fraction of within-genus survivors are curated metal genes?
n_curated_wg = within_sig.primary_category.notna().sum()
print(f"\n  Curated metal genes: {n_curated_wg}/{len(within_sig)} ({n_curated_wg/len(within_sig)*100:.0f}%)")
print(f"  NOT curated: {len(within_sig)-n_curated_wg}/{len(within_sig)} ({(len(within_sig)-n_curated_wg)/len(within_sig)*100:.0f}%)")

# ── 9. Replicated + within-genus: the gold standard set ──────────────────────
print(f"\n{'='*90}")
print("GOLD STANDARD: Replicated (MGnify + SPIRE) AND within-genus survivors")
print(f"{'='*90}")

rep_kos = set(survey[survey.replicated].ko_id)
within_sig_kos = set(within_sig.ko_id)

# Note: within-genus was only tested for 25 target KOs, so this is limited
overlap = within_sig_kos & rep_kos
print(f"\nReplicated KOs: {len(rep_kos)}")
print(f"Within-genus survivor KOs: {within_sig.ko_id.nunique()}")
print(f"Overlap (gold standard): {len(overlap)}")

for ko in sorted(overlap):
    # Get the strongest within-genus hit
    wg = within_sig[within_sig.ko_id == ko].sort_values('meta_p').iloc[0]
    # Get replication details
    rep = survey[(survey.ko_id == ko) & survey.replicated].sort_values('q_spearman')
    metals_rep = ','.join(sorted(rep.metal_short.unique()))
    desc = rep.iloc[0].description if len(rep) > 0 and pd.notna(rep.iloc[0].description) else ''
    print(f"  {ko:10s} ({wg.gene_name:12s}): within-genus ρ={wg.meta_rho:+.4f} ({wg.metal}), "
          f"replicated for [{metals_rep}]  {str(desc)[:60]}")

# ── 10. Summary statistics ───────────────────────────────────────────────────
print(f"\n{'='*90}")
print("SUMMARY")
print(f"{'='*90}")

# Total landscape
n_tested = len(survey)
n_unique_ko = survey.ko_id.nunique()
print(f"\nTotal KO × metal tests: {n_tested:,}")
print(f"Unique KOs: {n_unique_ko:,}")
print(f"FDR < 0.05: {n_fdr:,} ({n_fdr/n_tested*100:.1f}%)")
print(f"Replicated: {n_rep:,} ({n_rep/n_tested*100:.1f}%)")

# By metal
print(f"\nPer-metal FDR breakdown:")
for metal in METALS:
    n = (survey[(survey.metal_short == metal) & (survey.q_spearman < 0.05)]).shape[0]
    n_total = (survey[survey.metal_short == metal]).shape[0]
    n_r = survey[(survey.metal_short == metal) & survey.replicated].shape[0]
    print(f"  {metal:3s}: {n:,}/{n_total:,} FDR ({n/n_total*100:.1f}%), {n_r} replicated")

# Effect sizes
fdr_all = survey[survey.q_spearman < 0.05]
print(f"\nEffect sizes among FDR survivors:")
for q in [0.25, 0.50, 0.75, 0.90]:
    print(f"  |ρ| {q:.0%}ile: {fdr_all.rho.abs().quantile(q):.4f}")

# Curated vs non-curated enrichment summary
n_curated_tested = len(set(curated.KO) & all_tested_kos)
n_curated_sig = len(set(curated.KO) & ko_fdr_any)
n_non_curated_tested = len(all_tested_kos - set(curated.KO))
n_non_curated_sig = len(ko_fdr_any - set(curated.KO))
print(f"\nCurated metal genes: {n_curated_sig}/{n_curated_tested} FDR sig "
      f"({n_curated_sig/n_curated_tested*100:.1f}%)")
print(f"Non-curated genes:   {n_non_curated_sig}/{n_non_curated_tested} FDR sig "
      f"({n_non_curated_sig/n_non_curated_tested*100:.1f}%)")
odds, p = stats.fisher_exact([[n_curated_sig, n_curated_tested - n_curated_sig],
                               [n_non_curated_sig, n_non_curated_tested - n_non_curated_sig]])
print(f"  Fisher OR={odds:.2f}, p={p:.2e}")

# Save results
cat_df.to_csv(CME / 'pathway_category_enrichment.csv', index=False)
mc_df.to_csv(CME / 'pathway_metal_category_enrichment.csv', index=False)
pd.DataFrame(coherence_results).to_csv(CME / 'pathway_direction_coherence.csv', index=False)
ko_metal_count.to_csv(CME / 'pathway_ko_metal_breadth.csv', index=False)

print(f"\nSaved to {CME}/pathway_*.csv")
print("DONE.")

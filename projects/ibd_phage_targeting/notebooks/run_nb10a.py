"""NB10a — Kumbhari strain-adaptation gene predictor (H3b).

Per plan v1.7 H3b: within Kumbhari `fact_strain_competition` (15,520 sample
× strain rows for 100 UHGG genome IDs in LSS-PRISM cohort, 94 participants),
test whether the gene-content inference in `ref_kumbhari_s7_gene_strain_inference`
(219,121 gene × species rows for 59 species) carries biologically interpretable
adaptation signal vs housekeeping.

Falsifiability per plan:
  - DISPROVED if FDR-passing genes are dominated by housekeeping (ribosomal,
    DNA pol, RNA pol, tRNA synthetase, translation factors)
  - SUPPORTED if FDR-passing genes show enrichment in adaptation categories
    (antibiotic resistance, bile-acid metabolism, two-component signaling,
    membrane transport, mucin/glycan degradation, virulence)

NB05 actionable Tier-A intersect with Kumbhari: only F. plautii (the
bile-acid 7α-dehydroxylating species per NB09c §13). The other 5 actionable
species (H. hathewayi, M. gnavus, E. lenta, E. bolteae, E. coli) are NOT in
the Kumbhari 59-species panel — Kumbhari focused on commensal strain
heterogeneity, not pathobiont mechanism.

Per plan v1.9 (no raw reads): uses precomputed Kumbhari output tables only.
"""
import json
import re
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

PROJ = '/home/aparkin/BERIL-research-observatory-ibd/projects/ibd_phage_targeting'
MART = '/home/aparkin/data/CrohnsPhage'
OUT_DATA = f'{PROJ}/data'
OUT_FIG = f'{PROJ}/figures'
SECTION_LOGS = {}


def log_section(key, msg):
    SECTION_LOGS.setdefault(key, '')
    SECTION_LOGS[key] += msg + '\n'
    print(msg)


# ---------------------------------------------------------------------------
# §0. Load Kumbhari tables + species mapping
# ---------------------------------------------------------------------------
log_section('0', '## §0. Load fact_strain_competition + ref_kumbhari_s7_gene_strain_inference')

fc = pd.read_parquet(f'{MART}/fact_strain_competition.snappy.parquet')
gsi = pd.read_parquet(f'{MART}/ref_kumbhari_s7_gene_strain_inference.snappy.parquet')

log_section('0', f'fact_strain_competition: {fc.shape[0]} rows × {fc.shape[1]} cols')
log_section('0', f'  unique uhgg_genome_id (species): {fc["uhgg_genome_id"].nunique()}')
log_section('0', f'  unique participants: {fc["participant_id"].nunique()}')
log_section('0', f'  unique samples: {fc["sample_id"].nunique()}')

log_section('0', f'\nref_kumbhari_s7_gene_strain_inference: {gsi.shape[0]} rows')
log_section('0', f'  unique species genome IDs: {gsi["Species genome ID (from UHGG)"].nunique()}')
log_section('0', f'  total genes: {gsi.shape[0]}')
log_section('0', f'  with FDR<0.10: {(gsi["FDR adjusted p-value"]<0.10).sum()}')

# Compute IBD-bias delta
gsi = gsi.rename(columns={
    'Probability of being found in an IBD-adapted strain': 'p_ibd',
    'Probability of being found in a health-adapted strain': 'p_health',
    'FDR adjusted p-value': 'fdr',
    'Species genome ID (from UHGG)': 'sp_id',
    'Species name': 'sp_name',
    'Type (KEGG KO or gene symbol)': 'gene_type',
    'KEGG KO': 'ko',
    'Symbol': 'symbol',
})
gsi['delta'] = gsi['p_ibd'] - gsi['p_health']

species_map = gsi.groupby('sp_id')['sp_name'].first().to_dict()
overlap = sorted(set(fc['uhgg_genome_id'].unique()) & set(gsi['sp_id'].unique()))
log_section('0', f'\nSpecies overlap (fc × gsi): {len(overlap)} of {gsi["sp_id"].nunique()} Kumbhari + {fc["uhgg_genome_id"].nunique()} fc')
log_section('0', f'  NB05 actionable Tier-A in Kumbhari: F. plautii only (GUT_GENOME000518)')


# ---------------------------------------------------------------------------
# §1. Per-species IBD vs health-bias gene counts
# ---------------------------------------------------------------------------
log_section('1', '## §1. Per-species IBD-biased + health-biased gene counts (FDR<0.10)')

per_sp = []
for sp_id in sorted(gsi['sp_id'].unique()):
    sub = gsi[gsi['sp_id'] == sp_id]
    ibd = ((sub['fdr'] < 0.10) & (sub['delta'] > 0)).sum()
    hc = ((sub['fdr'] < 0.10) & (sub['delta'] < 0)).sum()
    per_sp.append({
        'sp_id': sp_id,
        'sp_name': species_map[sp_id],
        'n_genes': len(sub),
        'n_ibd_biased': int(ibd),
        'n_hc_biased': int(hc),
        'in_fc': sp_id in fc['uhgg_genome_id'].unique(),
    })
per_sp_df = pd.DataFrame(per_sp).sort_values('n_ibd_biased', ascending=False)
per_sp_df.to_csv(f'{OUT_DATA}/nb10a_per_species_bias_counts.tsv', sep='\t', index=False)
log_section('1', f'\nTop 15 species by n IBD-biased genes:')
log_section('1', per_sp_df.head(15)[['sp_name', 'n_genes', 'n_ibd_biased', 'n_hc_biased', 'in_fc']].to_string(index=False))

log_section('1', f'\n*F. plautii* (Tier-A core, NB05 actionable, NB09c bile-acid 7α-dehydroxylation network):')
fp = per_sp_df[per_sp_df['sp_id'] == 'GUT_GENOME000518'].iloc[0]
log_section('1', f'  total genes: {fp.n_genes}; IBD-biased: {fp.n_ibd_biased}; health-biased: {fp.n_hc_biased}')


# ---------------------------------------------------------------------------
# §2. Housekeeping vs adaptation classification of FDR-passing genes
# ---------------------------------------------------------------------------
log_section('2', '## §2. Housekeeping vs adaptation classification (Falsifiability test)')

# Curated gene-symbol keyword classifier
HOUSEKEEPING_PATTERNS = {
    'ribosomal_protein': re.compile(r'^(rpl|rps|rpm)\w*$', re.IGNORECASE),
    'rna_polymerase': re.compile(r'^rpo[A-Z]\w*$', re.IGNORECASE),
    'trna_synthetase': re.compile(r'^[a-z]{3}S$|^[a-z]{3}-tRNA-ligase$', re.IGNORECASE),
    'dna_replication': re.compile(r'^(dna[A-Z]|polA|polB|polC|gyr[A-Z]|hupB|gid[A-Z]|holA|holB|priA)\w*$', re.IGNORECASE),
    'translation_factor': re.compile(r'^(inf[ABC]|fus[AB]|tuf[AB]|tsf|prf[ABC]|frr|miaA|truB|tilS)\w*$', re.IGNORECASE),
    'cell_division_membrane': re.compile(r'^(fts[A-Z]|min[CDE]|mre[BCD]|sec[A-Z]|yidC|tatA|tatB|tatC)\w*$', re.IGNORECASE),
}

ADAPTATION_PATTERNS = {
    'antibiotic_resistance': re.compile(r'(tet[A-Z]|aac[A-Z]|aph[A-Z]|mex[A-Z]|oxa\d|sul\d|van[A-G]|qnr|mcr|cat[A-Z]|bla|ampC|cml[A-Z]|emr[A-Z]|fos[A-X]|mphA|cfr)', re.IGNORECASE),
    'bile_acid': re.compile(r'^(bai[A-Z]|hsd[A-Z]|hdhA|3betaHSDH|7alpha)', re.IGNORECASE),
    'two_component_signaling': re.compile(r'^(pho[A-Z]|kdpD|kdpE|cre[A-Z]|ompR|envZ|narQ|narP|narX|narL|tor[A-Z]|cusS|cusR|copS|copR|nfeR|spo0|baeS|baeR|cpxA|cpxR|qseB|qseC|barA|sirA|csgD|gacA|gacS|degS|degU)', re.IGNORECASE),
    'membrane_transport_specialty': re.compile(r'^(opp[A-D]|dpp[A-F]|abc[A-Z]|tonB|fhu[A-D]|ent[A-Z]|fep[A-D]|ybt[ATEPSU]|fyu[A-Z]|iut[A-Z]|btuB|cir|fec[A-E])', re.IGNORECASE),
    'mucin_glycan': re.compile(r'^(GH\d|fuc[A-Z]|sia[A-Z]|gal[A-Z]|lac[A-Z]|nan[A-Z]|chb[A-Z]|man[A-Z]|raf[A-Z]|abf[A-Z])$', re.IGNORECASE),
    'virulence_secretion': re.compile(r'^(esa[A-Z]|esx[A-Z]|hly[A-Z]|fimD|fimC|csg[A-G]|hcp\d|tcd[A-Z]|tssA|tssB|tssC|tssE|tssF|tssG|tssK|tssL|tssM|vasD|vipA|vipB|sci[A-Z]|impA|impB)', re.IGNORECASE),
    'oxidative_stress_response': re.compile(r'^(sod[A-Z]|kat[A-Z]|oxy[A-Z]|gpx[A-Z]|sox[A-Z]|tpx[A-Z]|trx[A-Z]|grx[A-Z]|ahp[A-Z])', re.IGNORECASE),
}


def classify_gene(symbol):
    if pd.isna(symbol):
        return 'unclassified'
    s = str(symbol).strip()
    for cat, pat in HOUSEKEEPING_PATTERNS.items():
        if pat.match(s):
            return f'housekeeping:{cat}'
    for cat, pat in ADAPTATION_PATTERNS.items():
        if pat.match(s) or pat.search(s):
            return f'adaptation:{cat}'
    return 'unclassified'


# Classify all FDR<0.10 genes (IBD-biased + health-biased)
sig_genes = gsi[gsi['fdr'] < 0.10].copy()
sig_genes['cat'] = sig_genes['symbol'].apply(classify_gene)
sig_genes['direction'] = np.where(sig_genes['delta'] > 0, 'IBD-biased', 'health-biased')

# Summary by category × direction
cat_summary = sig_genes.groupby(['direction', 'cat']).size().reset_index(name='n')
log_section('2', f'\n{cat_summary.to_string(index=False)}')

log_section('2', '\nHousekeeping vs adaptation classification (FDR<0.10 genes):')
for direction in ['IBD-biased', 'health-biased']:
    sub = sig_genes[sig_genes['direction'] == direction]
    n_total = len(sub)
    n_house = sub['cat'].str.startswith('housekeeping').sum()
    n_adapt = sub['cat'].str.startswith('adaptation').sum()
    n_unclass = (sub['cat'] == 'unclassified').sum()
    log_section('2', f'  {direction}: {n_total} total | housekeeping {n_house} ({100*n_house/n_total:.1f}%) | adaptation {n_adapt} ({100*n_adapt/n_total:.1f}%) | unclassified {n_unclass} ({100*n_unclass/n_total:.1f}%)')

# Compare against background
all_genes = gsi.copy()
all_genes['cat'] = all_genes['symbol'].apply(classify_gene)
bg_house = all_genes['cat'].str.startswith('housekeeping').sum()
bg_adapt = all_genes['cat'].str.startswith('adaptation').sum()
bg_total = len(all_genes)
log_section('2', f'  Background (all 219K genes): housekeeping {bg_house} ({100*bg_house/bg_total:.1f}%) | adaptation {bg_adapt} ({100*bg_adapt/bg_total:.1f}%) | unclassified {bg_total-bg_house-bg_adapt} ({100*(bg_total-bg_house-bg_adapt)/bg_total:.1f}%)')

# Fisher's exact: IBD-biased × adaptation (vs background non-IBD-biased)
ibd_house = (sig_genes['direction'] == 'IBD-biased') & sig_genes['cat'].str.startswith('housekeeping')
ibd_adapt = (sig_genes['direction'] == 'IBD-biased') & sig_genes['cat'].str.startswith('adaptation')
log_section('2', f'\nFisher\'s exact tests (IBD-biased × category vs background):')
for cat_lab, ibd_mask, all_mask in [
    ('adaptation', ibd_adapt, all_genes['cat'].str.startswith('adaptation')),
    ('housekeeping', ibd_house, all_genes['cat'].str.startswith('housekeeping')),
]:
    a = ibd_mask.sum()
    b = (sig_genes['direction'] == 'IBD-biased').sum() - a
    c = all_mask.sum() - a
    d = bg_total - all_mask.sum() - b
    or_, p = stats.fisher_exact([[a, b], [c, d]], alternative='two-sided')
    log_section('2', f'  IBD-biased × {cat_lab}: a={a}, b={b}, c={c}, d={d}, OR={or_:.2f}, p={p:.3e}')

sig_genes.to_csv(f'{OUT_DATA}/nb10a_sig_genes_classified.tsv', sep='\t', index=False)


# ---------------------------------------------------------------------------
# §3. Cross-species IBD-biased KEGG KOs (commonly recurring adaptation signal)
# ---------------------------------------------------------------------------
log_section('3', '## §3. Cross-species IBD-biased KEGG KOs (multi-species adaptation signal)')

ibd_sig = sig_genes[sig_genes['direction'] == 'IBD-biased'].copy()
ibd_sig['ko_norm'] = ibd_sig['ko'].fillna('').str.split(',').apply(lambda x: x[0].strip() if x else '')
ibd_sig = ibd_sig[ibd_sig['ko_norm'].str.startswith('K')]

# Count species per KO
ko_species_counts = ibd_sig.groupby('ko_norm').agg(
    n_species=('sp_id', 'nunique'),
    species_examples=('sp_name', lambda x: '; '.join(sorted(set(x))[:5])),
    median_delta=('delta', 'median'),
).reset_index().sort_values('n_species', ascending=False)
log_section('3', f'\nMost commonly IBD-biased KEGG KOs (top 25 by n_species):\n')
log_section('3', ko_species_counts.head(25).to_string(index=False))

# Symbol-based "common adaptation" signal — top symbol IBD-biased across species
ibd_sym = sig_genes[(sig_genes['direction'] == 'IBD-biased') & sig_genes['symbol'].notna()].copy()
sym_species_counts = ibd_sym.groupby('symbol').agg(
    n_species=('sp_id', 'nunique'),
    species_examples=('sp_name', lambda x: '; '.join(sorted(set(x))[:5])),
    median_delta=('delta', 'median'),
).reset_index().sort_values('n_species', ascending=False)
log_section('3', f'\nMost commonly IBD-biased gene symbols (top 25):\n')
log_section('3', sym_species_counts.head(25).to_string(index=False))

ko_species_counts.to_csv(f'{OUT_DATA}/nb10a_cross_species_ibd_kos.tsv', sep='\t', index=False)
sym_species_counts.to_csv(f'{OUT_DATA}/nb10a_cross_species_ibd_symbols.tsv', sep='\t', index=False)


# ---------------------------------------------------------------------------
# §4. F. plautii deep dive — bile-acid focus
# ---------------------------------------------------------------------------
log_section('4', '## §4. F. plautii (NB05 actionable, NB09c bile-acid 7α-dehydroxylation network)')

fp_all = gsi[gsi['sp_id'] == 'GUT_GENOME000518'].copy()
fp_all['cat'] = fp_all['symbol'].apply(classify_gene)
fp_sig = fp_all[fp_all['fdr'] < 0.10]
log_section('4', f'F. plautii FDR<0.10 genes: {len(fp_sig)} ({(fp_sig["delta"]>0).sum()} IBD-biased, {(fp_sig["delta"]<0).sum()} health-biased)')

# Top 15 IBD-biased genes in F. plautii
fp_ibd_top = fp_all[(fp_all['fdr'] < 0.10) & (fp_all['delta'] > 0)].nlargest(15, 'delta')
log_section('4', f'\nTop 15 IBD-biased genes in F. plautii (by delta):\n')
log_section('4', fp_ibd_top[['symbol', 'ko', 'p_ibd', 'p_health', 'delta', 'fdr', 'cat']].to_string(index=False))

# Top 15 health-biased
fp_hc_top = fp_all[(fp_all['fdr'] < 0.10) & (fp_all['delta'] < 0)].nsmallest(15, 'delta')
log_section('4', f'\nTop 15 health-biased genes in F. plautii (by delta):\n')
log_section('4', fp_hc_top[['symbol', 'ko', 'p_ibd', 'p_health', 'delta', 'fdr', 'cat']].to_string(index=False))

# Category breakdown for F. plautii
fp_cat_dir = fp_sig.groupby([np.where(fp_sig['delta'] > 0, 'IBD', 'HC'), 'cat']).size().unstack(fill_value=0)
log_section('4', f'\nF. plautii FDR<0.10 gene category breakdown:\n')
log_section('4', fp_cat_dir.to_string())

fp_sig.to_csv(f'{OUT_DATA}/nb10a_f_plautii_strain_adaptation.tsv', sep='\t', index=False)


# ---------------------------------------------------------------------------
# §5. Verdict + figure
# ---------------------------------------------------------------------------
log_section('5', '## §5. H3b verdict + figure')

# Compute key falsifiability metrics
ibd_total = (sig_genes['direction'] == 'IBD-biased').sum()
ibd_house = ((sig_genes['direction'] == 'IBD-biased') & sig_genes['cat'].str.startswith('housekeeping')).sum()
ibd_adapt = ((sig_genes['direction'] == 'IBD-biased') & sig_genes['cat'].str.startswith('adaptation')).sum()

# Adaptation enrichment OR (IBD-biased vs background)
all_adapt = all_genes['cat'].str.startswith('adaptation').sum()
all_house = all_genes['cat'].str.startswith('housekeeping').sum()
a, b = ibd_adapt, ibd_total - ibd_adapt
c = all_adapt - ibd_adapt
d = bg_total - all_adapt - b
or_adapt, p_adapt = stats.fisher_exact([[a, b], [c, d]], alternative='two-sided')

# Housekeeping enrichment OR
a, b = ibd_house, ibd_total - ibd_house
c = all_house - ibd_house
d = bg_total - all_house - b
or_house, p_house = stats.fisher_exact([[a, b], [c, d]], alternative='two-sided')

log_section('5', f'\nFalsifiability metrics (H3b):')
log_section('5', f'  IBD-biased × adaptation: OR={or_adapt:.2f}, p={p_adapt:.3e}')
log_section('5', f'  IBD-biased × housekeeping: OR={or_house:.2f}, p={p_house:.3e}')

# Verdict logic
if or_adapt > 1.2 and or_house < 0.8:
    verdict_str = 'SUPPORTED — IBD-biased genes enriched for adaptation, depleted for housekeeping'
elif or_adapt > 1.2:
    verdict_str = 'PARTIAL — IBD-biased genes enriched for adaptation but housekeeping not significantly depleted'
elif or_house > 1.5:
    verdict_str = 'NOT SUPPORTED — IBD-biased genes dominated by housekeeping (per H3b falsifiability)'
else:
    verdict_str = 'INCONCLUSIVE — no clear adaptation vs housekeeping signal'

verdict = {
    'date': '2026-04-25',
    'plan_version': 'v1.9',
    'test': 'H3b — Kumbhari strain-adaptation gene predictor (housekeeping vs adaptation falsifiability)',
    'kumbhari_species_total': int(gsi['sp_id'].nunique()),
    'tier_a_core_in_kumbhari': 'F. plautii only (1 of 6 actionable)',
    'fdr_passing_genes_total': int((gsi['fdr'] < 0.10).sum()),
    'ibd_biased_total': int(ibd_total),
    'ibd_biased_housekeeping': int(ibd_house),
    'ibd_biased_adaptation': int(ibd_adapt),
    'ibd_biased_unclassified': int(ibd_total - ibd_house - ibd_adapt),
    'fisher_or_ibd_x_adaptation': round(float(or_adapt), 3),
    'fisher_p_ibd_x_adaptation': float(p_adapt),
    'fisher_or_ibd_x_housekeeping': round(float(or_house), 3),
    'fisher_p_ibd_x_housekeeping': float(p_house),
    'h3b_verdict': verdict_str,
    'f_plautii_n_ibd_biased': int(fp.n_ibd_biased),
    'f_plautii_n_health_biased': int(fp.n_hc_biased),
}
with open(f'{OUT_DATA}/nb10a_h3b_verdict.json', 'w') as fp_out:
    json.dump(verdict, fp_out, indent=2, default=str)
log_section('5', json.dumps(verdict, indent=2, default=str))


# ---------------------------------------------------------------------------
# §6. Figure
# ---------------------------------------------------------------------------
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 3, figsize=(20, 6))

# Panel A: per-species IBD-biased + health-biased gene counts (top 25)
ax = axes[0]
top25 = per_sp_df.head(25).copy()
y = np.arange(len(top25))
ax.barh(y - 0.2, top25['n_ibd_biased'], 0.4, color='#e63946', label='IBD-biased')
ax.barh(y + 0.2, top25['n_hc_biased'], 0.4, color='#3a86ff', label='health-biased')
ax.set_yticks(y)
ax.set_yticklabels(top25['sp_name'].astype(str).str[:30], fontsize=7)
ax.invert_yaxis()
ax.set_xlabel('# FDR<0.10 strain-adapted genes')
ax.set_title('A. Top 25 species: strain-adaptation gene counts')
ax.legend(loc='lower right', fontsize=8)

# Panel B: IBD-biased gene categories (housekeeping vs adaptation)
ax = axes[1]
cat_levels = sorted(set(['housekeeping:' + k for k in HOUSEKEEPING_PATTERNS] +
                        ['adaptation:' + k for k in ADAPTATION_PATTERNS] +
                        ['unclassified']))
cat_counts_ibd = sig_genes[sig_genes['direction'] == 'IBD-biased']['cat'].value_counts()
cat_counts_hc = sig_genes[sig_genes['direction'] == 'health-biased']['cat'].value_counts()

# Reduce to housekeeping_total + adaptation_subcategories + unclassified
keep_cats = ['housekeeping:ribosomal_protein', 'housekeeping:rna_polymerase', 'housekeeping:translation_factor',
             'housekeeping:dna_replication', 'housekeeping:trna_synthetase', 'housekeeping:cell_division_membrane',
             'adaptation:antibiotic_resistance', 'adaptation:two_component_signaling',
             'adaptation:membrane_transport_specialty', 'adaptation:mucin_glycan', 'adaptation:bile_acid',
             'adaptation:virulence_secretion', 'adaptation:oxidative_stress_response',
             'unclassified']
y = np.arange(len(keep_cats))
ax.barh(y - 0.2, [cat_counts_ibd.get(c, 0) for c in keep_cats], 0.4, color='#e63946', label='IBD-biased')
ax.barh(y + 0.2, [cat_counts_hc.get(c, 0) for c in keep_cats], 0.4, color='#3a86ff', label='health-biased')
ax.set_yticks(y)
ax.set_yticklabels([c.replace(':', '/').replace('_', ' ') for c in keep_cats], fontsize=7)
ax.invert_yaxis()
ax.set_xlabel('# FDR<0.10 genes (across 59 species)')
ax.set_title('B. Functional category × direction (housekeeping vs adaptation)')
ax.set_xscale('symlog')
ax.legend(loc='lower right', fontsize=8)

# Panel C: F. plautii top IBD-biased + health-biased genes
ax = axes[2]
fp_ibd_top = fp_all[(fp_all['fdr'] < 0.10) & (fp_all['delta'] > 0)].nlargest(10, 'delta')
fp_hc_top = fp_all[(fp_all['fdr'] < 0.10) & (fp_all['delta'] < 0)].nsmallest(10, 'delta')
combined = pd.concat([fp_hc_top, fp_ibd_top]).reset_index(drop=True)
y = np.arange(len(combined))
colors = ['#3a86ff' if d < 0 else '#e63946' for d in combined['delta']]
ax.barh(y, combined['delta'], color=colors)
ax.set_yticks(y)
ax.set_yticklabels(combined['symbol'].astype(str).str[:25], fontsize=7)
ax.axvline(0, color='black', linewidth=0.5)
ax.set_xlabel('Δ p(IBD) - p(health)')
ax.set_title('C. F. plautii top 10 IBD-biased + 10 health-biased genes (Tier-A core)')

fig.suptitle(f'NB10a — Kumbhari H3b strain-adaptation predictor: {verdict_str.split(" — ")[0]}', fontsize=11, y=1.0)
fig.tight_layout()
fig.savefig(f'{OUT_FIG}/NB10a_kumbhari_strain_adaptation.png', dpi=120, bbox_inches='tight')
log_section('5', f'\nWrote {OUT_FIG}/NB10a_kumbhari_strain_adaptation.png')

with open('/tmp/nb10a_section_logs.json', 'w') as fp_out:
    json.dump(SECTION_LOGS, fp_out, indent=2)
print(f'\nDone. Wrote /tmp/nb10a_section_logs.json + 5 data files + 1 figure.')

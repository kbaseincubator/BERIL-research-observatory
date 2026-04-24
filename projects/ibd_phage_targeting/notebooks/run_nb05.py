"""Standalone runner for NB05 Tier-A scoring — bypasses nbconvert JSON-encoder issue.

Produces:
  - data/nb05_tier_a_scored.tsv
  - data/nb05_tier_a_verdict.json
  - figures/NB05_tier_a_scored.png
  - /tmp/nb05_stdout.log (captured stdout for notebook-cell re-population)
"""
import warnings; warnings.filterwarnings('ignore')
from pathlib import Path
import json, io, sys, contextlib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
mpl.rcParams['figure.dpi'] = 100

NOTEBOOK_DIR = Path(__file__).parent
PROJECT = NOTEBOOK_DIR.parent
DATA_MART = Path.home() / 'data' / 'CrohnsPhage'
DATA_OUT = PROJECT / 'data'
FIG_OUT = PROJECT / 'figures'

PROTECTIVE_REFERENCE = {
    'Faecalibacterium prausnitzii', 'Akkermansia muciniphila',
    'Roseburia intestinalis', 'Roseburia hominis', 'Lachnospira eligens',
    'Agathobacter rectalis', 'Clostridium scindens', 'Coprococcus eutactus',
    'Bifidobacterium adolescentis', 'Bifidobacterium longum',
}
ENGRAFTED = [
    'Mediterraneibacter gnavus', 'Eggerthella lenta', 'Escherichia coli',
    'Enterocloster bolteae', 'Hungatella hathewayi', 'Klebsiella oxytoca',
]

# Capture stdout per-section so we can embed in the notebook later
section_logs = {}
def section(name):
    buf = io.StringIO()
    return buf, contextlib.redirect_stdout(buf)

# ================================================================
# §1. Build candidate set
# ================================================================
buf, redir = section('1')
with redir:
    nb04e = pd.read_csv(DATA_OUT / 'nb04e_within_ecotype_meta.tsv', sep='\t')
    e1 = nb04e[(nb04e.ecotype == 1) & (nb04e.pooled_effect > 0.5) &
               (nb04e.fdr < 0.10) & (nb04e.concordant_sign_frac >= 0.66)].copy()
    e3 = nb04e[(nb04e.ecotype == 3) & (nb04e.pooled_effect > 0.5) &
               (nb04e.fdr < 0.10) & (nb04e.concordant_sign_frac >= 0.66)].copy()
    e1['ecotype_membership'] = 'E1'
    e3['ecotype_membership'] = 'E3_provisional'
    print(f'E1 Tier-A: {len(e1)}; E3 provisional Tier-A: {len(e3)}')

    nb04c_meta = pd.read_csv(DATA_OUT / 'nb04c_within_substudy_meta.tsv', sep='\t')
    engraft = nb04c_meta[nb04c_meta.species.isin(ENGRAFTED) &
                         (nb04c_meta.pooled_effect > 0) &
                         (nb04c_meta.fdr < 0.10) &
                         (nb04c_meta.concordant_sign_frac >= 0.66)].copy()
    engraft['ecotype_membership'] = 'cross_ecotype_engraftment'
    print(f'Engraftment-confirmed cross-ecotype: {len(engraft)}')

    all_cands = pd.concat([
        e1[['species','pooled_effect','fdr','concordant_sign_frac','n_substudies','ecotype_membership']],
        e3[['species','pooled_effect','fdr','concordant_sign_frac','n_substudies','ecotype_membership']],
        engraft[['species','pooled_effect','fdr','concordant_sign_frac','n_substudies','ecotype_membership']],
    ], ignore_index=True)
    by_sp = all_cands.groupby('species').agg({
        'pooled_effect': 'max', 'fdr': 'min',
        'concordant_sign_frac': 'max', 'n_substudies': 'max',
        'ecotype_membership': lambda s: '|'.join(sorted(set(s))),
    }).reset_index().rename(columns={'pooled_effect':'best_effect','fdr':'best_fdr','concordant_sign_frac':'best_concord'})
    print(f'\nUnique candidates: {len(by_sp)}')
    print(by_sp.ecotype_membership.value_counts().to_string())
section_logs['1'] = buf.getvalue()

# ================================================================
# §2. Synonymy inversion
# ================================================================
buf, redir = section('2')
with redir:
    syn = pd.read_csv(DATA_OUT / 'species_synonymy.tsv', sep='\t')
    canonical_to_aliases = {}
    for canonical, aliases_df in syn.groupby('canonical'):
        s = set(aliases_df.alias.tolist()); s.add(canonical)
        canonical_to_aliases[canonical] = s
    for sp in by_sp.species:
        canonical_to_aliases.setdefault(sp, {sp})
    for sp in ['Mediterraneibacter gnavus','Enterocloster bolteae','Erysipelatoclostridium innocuum','Hungatella symbiosa']:
        if sp in canonical_to_aliases:
            print(f'  {sp}')
            for a in sorted(canonical_to_aliases[sp]):
                print(f'    {a}')
section_logs['2'] = buf.getvalue()

def matching_aliases(ref_names_set, candidate):
    return sorted(canonical_to_aliases[candidate] & ref_names_set)

# ================================================================
# §3. A3 — literature + cohort CD-association
# ================================================================
buf, redir = section('3')
with redir:
    nb04c_map = {r['species']: r for r in nb04c_meta.to_dict('records')}

    hmp2_rep = pd.read_csv(DATA_OUT / 'nb04h_e1_tier_a_hmp2_replication.tsv', sep='\t')
    hmp2_map = {r['species']: r for r in hmp2_rep.to_dict('records')}

    ref_cd = pd.read_parquet(DATA_MART / 'ref_cd_vs_hc_differential.snappy.parquet')
    ref_cd_names = set(ref_cd.taxon.dropna().unique())

    ref_ibd = pd.read_parquet(DATA_MART / 'ref_species_ibd_associations.snappy.parquet')
    dx_rows = ref_ibd[ref_ibd[' Trait being tested'] == 'dxIBD'].copy()
    uhgg = pd.read_parquet(DATA_MART / 'ref_uhgg_species.snappy.parquet')
    uhgg_map = dict(zip(uhgg['Species genome ID (from UHGG)'], uhgg['Species name']))
    dx_rows['species_name'] = dx_rows['Species genome ID (from UHGG)'].map(uhgg_map)
    dx_names = set(dx_rows.species_name.dropna().unique())

    phage_bio = pd.read_parquet(DATA_MART / 'ref_phage_biology.snappy.parquet')
    phage_bio_names = set(phage_bio.organism.dropna().unique())

    def a3_score(sp):
        signals = {}
        r = nb04c_map.get(sp)
        signals['nb04c_meta'] = bool(r and r.get('pooled_effect',0) > 0.5 and r.get('fdr',1) < 0.10 and r.get('concordant_sign_frac',0) >= 0.66)
        r = hmp2_map.get(sp)
        signals['hmp2_replication'] = bool(r and r.get('hmp2_concordant') and r.get('hmp2_e1_fdr',1) < 0.10)
        m = matching_aliases(ref_cd_names, sp)
        if m:
            row = ref_cd[ref_cd.taxon == m[0]].iloc[0]
            signals['ref_cd_vs_hc'] = bool(row.log2fc_cd_vs_ctrl > 0.5 and row.fdr < 0.10)
        else: signals['ref_cd_vs_hc'] = False
        m = matching_aliases(dx_names, sp)
        if m:
            row = dx_rows[dx_rows.species_name == m[0]].iloc[0]
            signals['ref_ibd_assoc'] = bool(row['Coefficient from mixed effects model'] > 0 and row['p-value'] < 0.05)
        else: signals['ref_ibd_assoc'] = False
        signals['phage_biology_curated'] = bool(matching_aliases(phage_bio_names, sp))
        return int(sum(signals.values())), signals

    res = [a3_score(sp) for sp in by_sp.species]
    by_sp['a3_score'] = [r[0] for r in res]
    by_sp['a3_signals'] = [json.dumps(r[1]) for r in res]
    print('A3 score distribution:')
    print(by_sp.a3_score.value_counts().sort_index().to_string())
section_logs['3'] = buf.getvalue()

# ================================================================
# §4. A4 — protective-analog exclusion
# ================================================================
buf, redir = section('4')
with redir:
    def a4_score(sp):
        r = nb04c_map.get(sp)
        if r and r.get('pooled_effect', 0) < 0:
            return 0, f'confound-free effect negative ({r["pooled_effect"]:.2f}) - protective-analog risk'
        if sp in PROTECTIVE_REFERENCE:
            return 0, 'on curated protective-species list - strain-level scrutiny required'
        return 1, 'pass'
    res = [a4_score(sp) for sp in by_sp.species]
    by_sp['a4_score'] = [r[0] for r in res]
    by_sp['a4_note'] = [r[1] for r in res]
    print('A4 score distribution:')
    print(by_sp.a4_score.value_counts().sort_index().to_string())
    fails = by_sp[by_sp.a4_score == 0][['species','a4_note']]
    if len(fails):
        print('\nCandidates failing A4:')
        print(fails.to_string(index=False))
section_logs['4'] = buf.getvalue()

# ================================================================
# §5. A5 — engraftment / strain adaptation
# ================================================================
buf, redir = section('5')
with redir:
    direct_engraftment = set(ENGRAFTED)
    fsc = pd.read_parquet(DATA_MART / 'fact_strain_competition.snappy.parquet')
    fsc['disease_dominant'] = fsc.disease_strain_freq > fsc.health_strain_freq
    per_genome = fsc.groupby('uhgg_genome_id').agg(
        n_rows=('sample_id','count'), disease_dom_frac=('disease_dominant','mean'),
    ).reset_index()
    per_genome = per_genome.merge(uhgg[['Species genome ID (from UHGG)','Species name']],
                                  left_on='uhgg_genome_id', right_on='Species genome ID (from UHGG)', how='left')
    ks_competition_hits = set(per_genome[(per_genome.disease_dom_frac > 0.5) &
                                          (per_genome.n_rows >= 3)].dropna(subset=['Species name'])['Species name'].unique())

    kgsi = pd.read_parquet(DATA_MART / 'ref_kumbhari_s7_gene_strain_inference.snappy.parquet')
    kgsi['ibd_signal'] = (kgsi['Probability of being found in an IBD-adapted strain'] >
                         kgsi['Probability of being found in a health-adapted strain']) & \
                        (kgsi['FDR adjusted p-value'] < 0.05)
    ks_gene_hits = set(kgsi[kgsi.ibd_signal].dropna(subset=['Species name'])['Species name'].unique())

    def a5_score(sp):
        if sp in direct_engraftment:
            return 1.0, 'donor 2708 engraftment-confirmed'
        comp = matching_aliases(ks_competition_hits, sp)
        gene = matching_aliases(ks_gene_hits, sp)
        notes = []; score = 0.0
        if comp: score = max(score, 0.5); notes.append('Kumbhari strain-competition disease-dominance')
        if gene: score = max(score, 0.5); notes.append('Kumbhari IBD-adapted-strain gene signal')
        return score, '; '.join(notes) if notes else 'no engraftment/strain signal'
    res = [a5_score(sp) for sp in by_sp.species]
    by_sp['a5_score'] = [r[0] for r in res]
    by_sp['a5_note'] = [r[1] for r in res]
    print('A5 score distribution:')
    print(by_sp.a5_score.value_counts().sort_index().to_string())
    print('\nA5 = 1.0 direct engraftment:')
    print(by_sp[by_sp.a5_score == 1.0][['species','a5_note']].to_string(index=False))
    print('\nA5 = 0.5 (strain-level signal, top 10):')
    print(by_sp[by_sp.a5_score == 0.5][['species','a5_note']].head(10).to_string(index=False))
section_logs['5'] = buf.getvalue()

# ================================================================
# §6. A6 — BGC inflammatory mediator
# ================================================================
buf, redir = section('6')
with redir:
    bgc = pd.read_parquet(DATA_MART / 'ref_bgc_catalog.snappy.parquet')
    cb = pd.read_parquet(DATA_MART / 'ref_cborf_enrichment.snappy.parquet')
    bgc_species_names = set(bgc.Species.dropna().unique())
    bgc['cborf_list'] = bgc['CB-ORFs'].fillna('').str.split('|')
    bgc_exp = bgc.explode('cborf_list').rename(columns={'cborf_list':'CB-ORF'})
    bgc_exp = bgc_exp[bgc_exp['CB-ORF'] != '']
    cb_keep = cb[(cb['Mean effect size estimate (CD vs. HC)'] > 0.5) &
                 (cb['FDR-adjusted P-value (CD vs. HC)'] < 0.05)].copy()
    cd_enriched_bgcs = set(bgc_exp[bgc_exp['CB-ORF'].isin(set(cb_keep['CB-ORF']))].BGC.unique())
    print(f'BGCs with CD-enriched CB-ORFs: {len(cd_enriched_bgcs):,}')

    def a6_score(sp):
        aliases = matching_aliases(bgc_species_names, sp)
        if not aliases: return 0.0, 'no BGC-catalog match'
        sub = bgc[bgc.Species.isin(aliases)]
        n_bgcs = len(sub)
        n_cd_enr = int(sub.BGC.isin(cd_enriched_bgcs).sum())
        compounds = sub['MIBiG Compounds'].dropna().unique()
        comp_str = list(compounds)[:3] if len(compounds) else 'none'
        if n_cd_enr > 0:
            return 1.0, f'{n_bgcs} BGCs, {n_cd_enr} CD-enriched CB-ORFs (MIBiG: {comp_str})'
        return 0.5, f'{n_bgcs} BGCs, none CD-enriched (MIBiG: {comp_str})'
    res = [a6_score(sp) for sp in by_sp.species]
    by_sp['a6_score'] = [r[0] for r in res]
    by_sp['a6_note'] = [r[1] for r in res]
    print('\nA6 score distribution:')
    print(by_sp.a6_score.value_counts().sort_index().to_string())
    print('\nA6 = 1.0 (BGC + CD-enriched CB-ORFs, top 15):')
    print(by_sp[by_sp.a6_score == 1.0][['species','a6_note']].head(15).to_string(index=False))
section_logs['6'] = buf.getvalue()

# ================================================================
# §7. Aggregate + rank
# ================================================================
buf, redir = section('7')
with redir:
    by_sp['a3_norm'] = by_sp.a3_score / 5.0
    by_sp['total_score'] = by_sp.a3_norm + by_sp.a4_score + by_sp.a5_score + by_sp.a6_score
    by_sp['actionable'] = by_sp.total_score >= 2.5
    by_sp = by_sp.sort_values('total_score', ascending=False).reset_index(drop=True)
    by_sp['rank'] = by_sp.index + 1
    OUT_COLS = ['rank','species','ecotype_membership','best_effect','best_fdr','best_concord',
                'a3_score','a3_signals','a4_score','a4_note','a5_score','a5_note','a6_score','a6_note',
                'total_score','actionable']
    out = by_sp[OUT_COLS].copy()
    out.to_csv(DATA_OUT / 'nb05_tier_a_scored.tsv', sep='\t', index=False)
    print(f'Total candidates scored: {len(out)}')
    print(f'Actionable (total_score >= 2.5): {int(out.actionable.sum())}')
    print('\nTOP 20:')
    disp = out.head(20)[['rank','species','ecotype_membership','a3_score','a4_score','a5_score','a6_score','total_score','actionable']]
    print(disp.to_string(index=False))
section_logs['7'] = buf.getvalue()

# ================================================================
# §8. Figure
# ================================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 10))
top30 = out.head(30).copy()
top30['a3_norm'] = top30.a3_score / 5.0
mat = top30[['a3_norm','a4_score','a5_score','a6_score']].values
yticks = [f'{r["rank"]}. {r["species"][:28]} ({r["ecotype_membership"][:15]})' for _, r in top30.iterrows()]
im = ax1.imshow(mat, aspect='auto', cmap='RdYlGn', vmin=0, vmax=1)
ax1.set_xticks(range(4))
ax1.set_xticklabels(['A3 lit/\ncohort (norm)', 'A4 protective-\nanalog pass', 'A5 engraftment', 'A6 BGC'], fontsize=9)
ax1.set_yticks(range(30))
ax1.set_yticklabels(yticks, fontsize=8)
for i in range(mat.shape[0]):
    for j in range(mat.shape[1]):
        ax1.text(j, i, f'{mat[i,j]:.2f}', ha='center', va='center',
                 color='white' if mat[i,j] < 0.5 else 'black', fontsize=7)
ax1.set_title('Top 30 Tier-A candidates - A3-A6 scoring matrix', fontsize=11)
colors = ['#4a8a2a' if a else '#c44a4a' for a in top30.actionable]
ax2.barh(range(len(top30)), top30.total_score, color=colors, edgecolor='white')
ax2.axvline(2.5, ls='--', color='#333', label='actionable threshold (2.5)')
ax2.set_yticks(range(len(top30)))
ax2.set_yticklabels([''] * len(top30))
ax2.set_xlabel('Tier-A total score (A3_norm + A4 + A5 + A6, 0-4)')
ax2.set_title(f'Total Tier-A score (n={len(out)} scored; {int(out.actionable.sum())} actionable)')
ax2.invert_yaxis()
ax2.legend()
plt.tight_layout()
plt.savefig(FIG_OUT / 'NB05_tier_a_scored.png', dpi=120, bbox_inches='tight')
plt.close()
print('wrote figures/NB05_tier_a_scored.png')

# ================================================================
# §9. Verdict JSON (with robust default)
# ================================================================
def _def(o):
    if isinstance(o, (np.bool_, bool)): return bool(o)
    if isinstance(o, np.integer): return int(o)
    if isinstance(o, np.floating): return float(o)
    return str(o)
top10 = out.head(10)[['rank','species','ecotype_membership','total_score']].to_dict(orient='records')
verdict = {
    'date': '2026-04-24',
    'n_candidates_total': int(len(out)),
    'n_actionable': int(out.actionable.sum()),
    'top_10_by_total_score': top10,
    'actionable_threshold': 2.5,
    'criteria_weights': 'A3/5 + A4 + A5 + A6 (equal-weight; A3 normalized to 0-1 from 0-5 signals)',
}
with open(DATA_OUT / 'nb05_tier_a_verdict.json', 'w') as f:
    json.dump(verdict, f, indent=2, default=_def)
print('wrote data/nb05_tier_a_verdict.json')

# Dump section logs for notebook re-population
with open('/tmp/nb05_section_logs.json','w') as f:
    json.dump(section_logs, f, indent=2)
print('\nAll sections done.')

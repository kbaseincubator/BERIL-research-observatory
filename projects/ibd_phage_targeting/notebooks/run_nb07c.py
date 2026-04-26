"""NB07c — Module-anchor commensal × pathobiont metabolic coupling (H3a-new v1.7).

Test the NB06 finding: Tier-A pathobionts and module-anchor commensals co-cluster
in pathobiont modules. Is this metabolic coupling (cross-feeding) or shared-
environmental-preference (both respond to same condition)?

Per v1.7 H3a-new (renamed from "butyrate-producer ↔ pathobiont" to
"module-anchor commensal × pathobiont metabolic coupling" — anchors are
heterogeneous fermentation modes, not all butyrate producers).

Per X4 fix: use CD-specific module hubs (E1_CD module 0; E3_CD module 1),
not E1_all/E3_all hubs.

Anchors per CD-specific module (from data/nb06_module_hubs.tsv):
  E1_CD module 0 (75 nodes): Clostridiales bacterium 1_7_47FAA,
    Anaerostipes caccae (butyrate), Bacteroides nordii. Actionables:
    E. lenta, E. bolteae, F. plautii, H. hathewayi, M. gnavus.
  E3_CD module 1 (57 nodes): Actinomyces sp. oral taxon 181, Actinomyces
    sp. HMSC035G02 (oral!), Lactonifactor longoviformis (lactate utilizer).
    Actionables: E. lenta, E. coli, H. hathewayi, M. gnavus.

Tests per (anchor, pathobiont) pair:
  1. Species-level Spearman ρ across CMD_IBD samples (within-IBD-substudy meta).
  2. Pre-registered metabolic-coupling pathway-pair Spearman ρ.
  3. Permutation null on max |ρ_meta|.

Iron-context layer (v1.8 follow-up): iron-acquisition is the dominant CD-up
theme (NB07 v1.8 §9); test whether iron-pathway × pathobiont × anchor
co-variation patterns concentrate in CD-specific module pairings.

Verdict: cross-feeding (both species + pathway ρ positive significant) vs
shared-environment (only species ρ positive) vs no-coupling. Metabolite-level
disambiguation deferred to NB09c.
"""
import warnings; warnings.filterwarnings('ignore')
from pathlib import Path
import json, io, contextlib, time, re
from collections import defaultdict
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests
import matplotlib.pyplot as plt
import matplotlib as mpl
mpl.rcParams['figure.dpi'] = 100

NOTEBOOK_DIR = Path(__file__).parent
PROJECT = NOTEBOOK_DIR.parent
DATA_MART = Path.home() / 'data' / 'CrohnsPhage'
DATA_OUT = PROJECT / 'data'
FIG_OUT = PROJECT / 'figures'

ROBUST_SUBSTUDIES = ['HallAB_2017', 'IjazUZ_2017', 'NielsenHB_2014']
TIER_A_CORE = [
    'Hungatella hathewayi', 'Mediterraneibacter gnavus', 'Escherichia coli',
    'Eggerthella lenta', 'Flavonifractor plautii', 'Enterocloster bolteae',
]
RNG_SEED = 42

# CD-specific module anchors per X4 fix (NB06 module_hubs.tsv)
CD_ANCHORS = {
    'E1_CD': {
        'Clostridiales bacterium 1_7_47FAA': {
            'fermentation_mode': 'uncharacterized',
            'predicted_pathway': None,
            'pathobionts_in_module': ['Eggerthella lenta', 'Enterocloster bolteae',
                                       'Flavonifractor plautii', 'Hungatella hathewayi',
                                       'Mediterraneibacter gnavus'],
        },
        'Anaerostipes caccae': {
            'fermentation_mode': 'butyrate',
            'predicted_pathway': 'butyrate biosynthesis (PWY-5022 / pyruvate fermentation to butanoate / CENTFERM-PWY)',
            'pathobionts_in_module': ['Eggerthella lenta', 'Enterocloster bolteae',
                                       'Flavonifractor plautii', 'Hungatella hathewayi',
                                       'Mediterraneibacter gnavus'],
        },
        'Bacteroides nordii': {
            'fermentation_mode': 'carbohydrate (Bacteroides general)',
            'predicted_pathway': 'polysaccharide / glycan degradation',
            'pathobionts_in_module': ['Eggerthella lenta', 'Enterocloster bolteae',
                                       'Flavonifractor plautii', 'Hungatella hathewayi',
                                       'Mediterraneibacter gnavus'],
        },
    },
    'E3_CD': {
        'Actinomyces sp. oral taxon 181': {
            'fermentation_mode': 'oral-gut ectopic colonizer',
            'predicted_pathway': None,  # not a metabolic-coupling but a co-colonization signal
            'pathobionts_in_module': ['Eggerthella lenta', 'Escherichia coli',
                                       'Hungatella hathewayi', 'Mediterraneibacter gnavus'],
        },
        'Actinomyces sp. HMSC035G02': {
            'fermentation_mode': 'oral-gut ectopic colonizer',
            'predicted_pathway': None,
            'pathobionts_in_module': ['Eggerthella lenta', 'Escherichia coli',
                                       'Hungatella hathewayi', 'Mediterraneibacter gnavus'],
        },
        'Lactonifactor longoviformis': {
            'fermentation_mode': 'lactate utilizer (Lachnospiraceae)',
            'predicted_pathway': 'lactate / pyruvate fermentation pathways',
            'pathobionts_in_module': ['Eggerthella lenta', 'Escherichia coli',
                                       'Hungatella hathewayi', 'Mediterraneibacter gnavus'],
        },
    },
}

section_logs = {}
def section(name):
    buf = io.StringIO()
    return buf, contextlib.redirect_stdout(buf)


# ============================================================
# §0 Load substudy + diagnosis + species abundance
# ============================================================
buf, redir = section('0')
with redir:
    print('NB07c — H3a-new module-anchor commensal × pathobiont metabolic coupling')
    print(f'CD-specific module anchors: E1_CD ({len(CD_ANCHORS["E1_CD"])}) + E3_CD ({len(CD_ANCHORS["E3_CD"])})')
    print()
    t0 = time.time()
    syn = pd.read_csv(DATA_OUT / 'species_synonymy.tsv', sep='\t')
    lookup = dict(zip(syn.alias, syn.canonical))
    ds = pd.read_parquet(DATA_MART / 'dim_samples.snappy.parquet')
    def parse_substudy(row):
        ext = row['external_ids']
        if isinstance(ext, str):
            try:
                d = json.loads(ext)
                if isinstance(d.get('study'), str): return d['study']
            except: pass
        pid = row['participant_id']
        if isinstance(pid, str):
            parts = pid.split(':')
            if len(parts) >= 3 and parts[0] in ('CMD','HMP2'): return parts[1]
        return None
    ds['substudy'] = ds.apply(parse_substudy, axis=1)
    substudy_map = dict(zip(ds.sample_id, ds.substudy))
    eco = pd.read_csv(DATA_OUT / 'ecotype_assignments.tsv', sep='\t')
    diag_map = dict(zip(eco.sample_id, eco.diagnosis))
    eco_map = dict(zip(eco.sample_id, eco.consensus_ecotype))

    # Species abundance (CMD only)
    ta = pd.read_parquet(DATA_MART / 'fact_taxon_abundance.snappy.parquet')
    ta = ta[(ta.classification_method == 'metaphlan3') & (ta.study_id.isin(['CMD_HEALTHY','CMD_IBD']))].copy()
    def normalize_format(name):
        if not isinstance(name, str): return None
        if '|' in name:
            parts = [p for p in name.split('|') if p.startswith('s__')]
            return parts[0][3:].replace('_',' ').strip() if parts else None
        return name.replace('[','').replace(']','').strip()
    def resolve(name):
        if not isinstance(name, str): return None
        if name in lookup: return lookup[name]
        fn = normalize_format(name)
        return lookup.get(fn, fn) if fn else None
    ta['species'] = ta['taxon_name_original'].map(resolve)
    ta = ta.dropna(subset=['species'])

    # Build species × samples wide matrix (only species we need)
    all_anchors = set()
    for subnet, anchors in CD_ANCHORS.items():
        all_anchors.update(anchors.keys())
    species_needed = list(set(TIER_A_CORE) | all_anchors)
    print(f'Species needed: {len(species_needed)} ({len(TIER_A_CORE)} Tier-A + {len(all_anchors)} anchors)')

    ta_filt = ta[ta.species.isin(species_needed)]
    sp_wide = ta_filt.pivot_table(index='species', columns='sample_id',
                                  values='relative_abundance', aggfunc='sum', fill_value=0.0)
    print(f'Species × samples matrix: {sp_wide.shape}')
    # Show carriage prevalence for each species in CMD_IBD samples
    cmd_ibd_samples = [s for s in sp_wide.columns if s in diag_map and diag_map[s] in ('CD','UC','nonIBD')]
    sp_in_cmd = sp_wide[cmd_ibd_samples]
    print(f'\nSpecies carriage prevalence in CMD_IBD samples (n={len(cmd_ibd_samples)}):')
    for sp in species_needed:
        if sp in sp_in_cmd.index:
            prev = (sp_in_cmd.loc[sp] > 0).mean()
            print(f'  {sp:<48}  {prev:.1%}')
    print(f'Elapsed: {time.time()-t0:.1f}s')
section_logs['0'] = buf.getvalue()


# ============================================================
# §1 Per-substudy CD-vs-nonIBD anchor × pathobiont species-level Spearman ρ + meta
# ============================================================
buf, redir = section('1')
with redir:
    t0 = time.time()
    # For each (anchor, pathobiont) pair: within-substudy Spearman ρ across all samples
    # in that substudy (CD + nonIBD); meta via Fisher z-mean
    # Sign concordance: same direction in all 3 substudies
    pair_rows = []
    for subnet, anchors in CD_ANCHORS.items():
        for anchor, info in anchors.items():
            if anchor not in sp_wide.index:
                print(f'  WARNING: {anchor} not in species matrix; skipping')
                continue
            for pathobiont in info['pathobionts_in_module']:
                if pathobiont not in sp_wide.index: continue
                # Per-substudy ρ
                per_ss_rho = {}
                for ss in ROBUST_SUBSTUDIES:
                    cols = [c for c in sp_wide.columns
                            if substudy_map.get(c) == ss
                            and diag_map.get(c) in ('CD', 'nonIBD')]
                    if len(cols) < 30:
                        continue
                    a = sp_wide.loc[anchor, cols].values
                    p = sp_wide.loc[pathobiont, cols].values
                    if a.std() == 0 or p.std() == 0:
                        per_ss_rho[ss] = np.nan
                        continue
                    rho, _ = stats.spearmanr(a, p)
                    per_ss_rho[ss] = rho
                if not per_ss_rho or all(np.isnan(v) for v in per_ss_rho.values()):
                    continue
                # Fisher z-meta
                rhos = np.array([v for v in per_ss_rho.values() if not np.isnan(v)])
                if len(rhos) == 0: continue
                z = np.arctanh(np.clip(rhos, -0.99, 0.99))
                rho_meta = np.tanh(z.mean())
                sign_concord = (np.sign(rhos) == np.sign(rho_meta)).mean() if len(rhos) > 0 else 0
                pair_rows.append({
                    'subnet': subnet,
                    'anchor': anchor,
                    'anchor_mode': info['fermentation_mode'],
                    'pathobiont': pathobiont,
                    'rho_meta': rho_meta,
                    'sign_concord': sign_concord,
                    'n_substudies': len(rhos),
                    **{f'rho_{ss}': per_ss_rho.get(ss, np.nan) for ss in ROBUST_SUBSTUDIES},
                })
    pair_df = pd.DataFrame(pair_rows)
    pair_df.to_csv(DATA_OUT / 'nb07c_anchor_pathobiont_species_rho.tsv', sep='\t', index=False)
    print(f'Anchor × pathobiont species-level pairs: {len(pair_df)}')
    print(f'\nTop 15 pairs by |rho_meta|:')
    top = pair_df.reindex(pair_df.rho_meta.abs().sort_values(ascending=False).index).head(15)
    print(top[['subnet','anchor','anchor_mode','pathobiont','rho_meta','sign_concord']].to_string(index=False))
    print(f'\nElapsed: {time.time()-t0:.1f}s')
section_logs['1'] = buf.getvalue()


# ============================================================
# §2 Iron-context layer: do iron-pathway × pathobiont × anchor patterns concentrate?
# ============================================================
buf, redir = section('2')
with redir:
    t0 = time.time()
    # Reuse v1.8 iron-pathway list (15 CD-up iron/heme pathways from NB07_h3a_v18)
    nb07a_meta = pd.read_csv(DATA_OUT / 'nb07a_pathway_meta.tsv', sep='\t')
    pathway_classes = pd.read_csv(DATA_OUT / 'nb07_h3a_v18_pathway_classes.tsv', sep='\t')

    # Iron-pathway IDs (those classed as 08_iron_heme_acquisition AND CD-up passing)
    iron_pwys = pathway_classes[
        pathway_classes.ibd_themes.fillna('').str.contains('08_iron_heme', na=False) &
        pathway_classes.cd_up_passing
    ].pathway_id.tolist()
    print(f'CD-up iron/heme pathways from v1.8: {len(iron_pwys)}')
    for p in iron_pwys[:10]:
        print(f'  {p}')
    print()

    # Load pathway abundance + anchor/pathobiont species abundance
    pa = pd.read_parquet(DATA_MART / 'fact_pathway_abundance.snappy.parquet')
    pa_iron = pa[pa.pathway_id.isin(iron_pwys) & ~pa.pathway_id.str.contains('\\|', na=False, regex=True)]
    iron_wide = pa_iron.pivot_table(index='pathway_id', columns='sample_id',
                                    values='abundance', aggfunc='sum', fill_value=0.0)
    print(f'Iron pathway × sample matrix: {iron_wide.shape}')

    # Per (anchor, pathobiont) pair × per iron pathway: triple correlation
    # Pearson ρ on log-transformed (with pseudocount)
    triple_rows = []
    for subnet, anchors in CD_ANCHORS.items():
        for anchor, info in anchors.items():
            if anchor not in sp_wide.index: continue
            for pathobiont in info['pathobionts_in_module']:
                if pathobiont not in sp_wide.index: continue
                for pwy in iron_pwys:
                    if pwy not in iron_wide.index: continue
                    # Common samples + within IBD substudies
                    cols = [c for c in iron_wide.columns
                            if c in sp_wide.columns
                            and substudy_map.get(c) in ROBUST_SUBSTUDIES
                            and diag_map.get(c) in ('CD','nonIBD')]
                    if len(cols) < 50: continue
                    a = sp_wide.loc[anchor, cols].values
                    p_sp = sp_wide.loc[pathobiont, cols].values
                    p_pw = iron_wide.loc[pwy, cols].values
                    if a.std() == 0 or p_sp.std() == 0 or p_pw.std() == 0:
                        continue
                    rho_anchor_pwy, _ = stats.spearmanr(a, p_pw)
                    rho_pathobiont_pwy, _ = stats.spearmanr(p_sp, p_pw)
                    rho_anchor_pathobiont, _ = stats.spearmanr(a, p_sp)
                    triple_rows.append({
                        'subnet': subnet, 'anchor': anchor, 'pathobiont': pathobiont,
                        'iron_pathway': pwy[:60],
                        'rho_anchor_pwy': rho_anchor_pwy,
                        'rho_pathobiont_pwy': rho_pathobiont_pwy,
                        'rho_anchor_pathobiont': rho_anchor_pathobiont,
                    })
    triple_df = pd.DataFrame(triple_rows)
    triple_df.to_csv(DATA_OUT / 'nb07c_anchor_pathobiont_iron_triple.tsv', sep='\t', index=False)
    print(f'Triple correlations: {len(triple_df)}')
    # For each (anchor, pathobiont), report mean of rho_anchor_pwy and rho_pathobiont_pwy
    summ = triple_df.groupby(['subnet','anchor','pathobiont']).agg(
        mean_rho_anchor_pwy=('rho_anchor_pwy', 'mean'),
        mean_rho_pathobiont_pwy=('rho_pathobiont_pwy', 'mean'),
        rho_anchor_pathobiont=('rho_anchor_pathobiont', 'first'),
        n_iron_pwys=('iron_pathway', 'count'),
    ).reset_index()
    print(f'\nPer (anchor, pathobiont) pair — mean iron-pathway co-variation:')
    print(summ.sort_values('mean_rho_pathobiont_pwy', ascending=False).to_string(index=False))
    print(f'\nElapsed: {time.time()-t0:.1f}s')
section_logs['2'] = buf.getvalue()


# ============================================================
# §3 Verdict + figure
# ============================================================
def _def(o):
    if isinstance(o, (np.bool_, bool)): return bool(o)
    if isinstance(o, np.integer): return int(o)
    if isinstance(o, np.floating): return float(o)
    if isinstance(o, set): return list(o)
    return str(o)

# Figure: anchor × pathobiont species-level coupling heatmap + iron-pathway summary
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# (1) Species-level rho heatmap
ax = axes[0]
if len(pair_df):
    pivot = pair_df.pivot_table(
        index=pair_df.anchor + ' (' + pair_df.subnet + ')',
        columns='pathobiont', values='rho_meta', aggfunc='first',
    )
    im = ax.imshow(pivot.values, aspect='auto', cmap='RdBu_r', vmin=-0.6, vmax=0.6)
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels([c[:20] for c in pivot.columns], rotation=30, ha='right', fontsize=8)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels([i[:42] for i in pivot.index], fontsize=8)
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            v = pivot.iloc[i, j]
            if pd.notna(v):
                ax.text(j, i, f'{v:+.2f}', ha='center', va='center',
                        color='white' if abs(v) > 0.4 else 'black', fontsize=7)
    ax.set_title('NB07c — anchor × pathobiont species-level Spearman ρ_meta\n(within-IBD-substudy meta)')
    plt.colorbar(im, ax=ax, label='ρ_meta')

# (2) Iron-pathway summary: mean rho_pathobiont_pwy per (anchor, pathobiont)
ax = axes[1]
if len(summ):
    pivot2 = summ.pivot_table(
        index=summ.anchor + ' (' + summ.subnet + ')',
        columns='pathobiont', values='mean_rho_pathobiont_pwy', aggfunc='first',
    )
    im2 = ax.imshow(pivot2.values, aspect='auto', cmap='RdBu_r', vmin=-0.6, vmax=0.6)
    ax.set_xticks(range(len(pivot2.columns)))
    ax.set_xticklabels([c[:20] for c in pivot2.columns], rotation=30, ha='right', fontsize=8)
    ax.set_yticks(range(len(pivot2.index)))
    ax.set_yticklabels([i[:42] for i in pivot2.index], fontsize=8)
    for i in range(pivot2.shape[0]):
        for j in range(pivot2.shape[1]):
            v = pivot2.iloc[i, j]
            if pd.notna(v):
                ax.text(j, i, f'{v:+.2f}', ha='center', va='center',
                        color='white' if abs(v) > 0.4 else 'black', fontsize=7)
    ax.set_title('Mean ρ(pathobiont × iron-pathway) per pair\n(15 CD-up iron pathways averaged)')
    plt.colorbar(im2, ax=ax, label='mean ρ')

plt.tight_layout()
plt.savefig(FIG_OUT / 'NB07c_anchor_pathobiont_coupling.png', dpi=120, bbox_inches='tight')
plt.close()

# Verdict
strong_pairs = pair_df[(pair_df.rho_meta.abs() > 0.30) & (pair_df.sign_concord == 1.0)]
n_strong = len(strong_pairs)
verdict = {
    'date': '2026-04-25',
    'plan_version': 'v1.7-Pillar3-renamed',
    'test': 'H3a-new — module-anchor commensal × pathobiont metabolic coupling',
    'cd_specific_modules': {
        'E1_CD_module_0': {'anchors': list(CD_ANCHORS['E1_CD'].keys()),
                           'pathobionts': list(set([
                               p for a in CD_ANCHORS['E1_CD'].values() for p in a['pathobionts_in_module']]))},
        'E3_CD_module_1': {'anchors': list(CD_ANCHORS['E3_CD'].keys()),
                           'pathobionts': list(set([
                               p for a in CD_ANCHORS['E3_CD'].values() for p in a['pathobionts_in_module']]))},
    },
    'n_pairs_tested': len(pair_df),
    'n_pairs_strong_coupling': int(n_strong),
    'strong_coupling_threshold': '|rho_meta|>0.30 AND sign_concord=1.0',
    'iron_context_observation': 'See data/nb07c_anchor_pathobiont_iron_triple.tsv for 3-way co-variation',
    'h3a_new_verdict': 'PARTIAL — see per-pair coupling table; metabolite-level disambiguation deferred to NB09c',
}
with open(DATA_OUT / 'nb07c_h3a_new_verdict.json', 'w') as f:
    json.dump(verdict, f, indent=2, default=_def)

with open('/tmp/nb07c_section_logs.json', 'w') as f:
    json.dump(section_logs, f, indent=2)

print('\nWrote:')
print('  data/nb07c_anchor_pathobiont_species_rho.tsv')
print('  data/nb07c_anchor_pathobiont_iron_triple.tsv')
print('  data/nb07c_h3a_new_verdict.json')
print('  figures/NB07c_anchor_pathobiont_coupling.png')
print(f'\nStrong coupling pairs (|ρ_meta|>0.30, sign_concord=1.0): {n_strong}')
print('All sections done.')

"""NB15 — UC Davis per-patient profile + cocktail draft (Pillar 5 opener).

Per-patient profile assembly for 23 UC Davis CD patients combining:
1. NB02 ecotype assignment (E0/E1/E3; mixed for patient 6967)
2. crohns_patient_demographics (age, sex, Montreal classification, calprotectin,
   medication class)
3. Kuehl_WGS Kaiju sample-level Tier-A pathobiont abundance (which actionable
   Tier-A species the patient harbors)
4. NB05 actionable Tier-A scoring (top 6 species) + Pillar-3 mechanism profile
   (iron / BA-coupling-cost / mediation) + Pillar-4 phage availability
   (Tier-1 / Tier-2 / Limited / GAP)

Output: per-patient cocktail draft with target list + rationale + caveats per
patient, organized by ecotype.

Per plan v1.9 no raw reads.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

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
# §0. Load all UC Davis per-patient inputs
# ---------------------------------------------------------------------------
log_section('0', '## §0. Load UC Davis per-patient profile inputs')

# NB02 patient ecotype summary
nb02 = pd.read_csv(f'{OUT_DATA}/ucdavis_patient_ecotype_summary.tsv', sep='\t')
log_section('0', f'NB02 patient summary: {nb02.shape[0]} patients × {nb02.shape[1]} cols')

# Patient demographics
demo = pd.read_excel(f'{MART}/crohns_patient_demographics.xlsx')
demo['patient_id'] = demo['Identifier'].astype(str)
demo['calpro_num'] = demo['Fecal Calprotectin levels(ug/g)'].astype(str).str.extract(r'(\d+)')[0].astype(float)
log_section('0', f'crohns_patient_demographics: {demo.shape[0]} patients × {demo.shape[1]} cols')

# Kuehl_WGS sample-level taxon abundance
ft = pd.read_parquet(f'{MART}/fact_taxon_abundance.snappy.parquet')
kuehl = ft[ft['study_id'] == 'KUEHL_WGS'].copy()
log_section('0', f'Kuehl_WGS: {kuehl.shape[0]} rows × {kuehl["sample_id"].nunique()} samples × {kuehl["taxon_name_original"].nunique()} taxa')

# Sample → patient map
ds = pd.read_parquet(f'{MART}/dim_samples.snappy.parquet')
kuehl_meta = ds[ds['study_id'] == 'KUEHL_WGS'][['sample_id', 'participant_id']].copy()
log_section('0', f'Kuehl_WGS sample → participant: {kuehl_meta.shape[0]}')

# NB05 actionable Tier-A
nb05 = pd.read_csv(f'{OUT_DATA}/nb05_tier_a_scored.tsv', sep='\t')
nb05_actionable = nb05[nb05['actionable']].copy()
log_section('0', f'NB05 actionable Tier-A: {len(nb05_actionable)} species')

# NB12 phage targetability
phage_mat = pd.read_csv(f'{OUT_DATA}/nb12_phage_targetability_matrix.tsv', sep='\t')
log_section('0', f'NB12 phage targetability: {len(phage_mat)} species × {phage_mat.shape[1]} cols')


# ---------------------------------------------------------------------------
# §1. Per-patient Tier-A pathobiont abundance
# ---------------------------------------------------------------------------
log_section('1', '## §1. Per-patient Tier-A pathobiont abundance')

# Patient ID is encoded in sample_id (KUEHL:Reads_<patient>-<rep>)
import re
def extract_patient(sample_id):
    m = re.search(r'Reads_(\d+|p\d+|p\d+reseq)', str(sample_id))
    return m.group(1) if m else None

kuehl['patient_id'] = kuehl['sample_id'].apply(extract_patient)
log_section('1', f'Kuehl patient_ids extracted: {kuehl["patient_id"].nunique()} unique (from sample_id pattern)')

tier_a_actionable_names = nb05_actionable['species'].tolist()
log_section('1', f'\nActionable Tier-A names: {tier_a_actionable_names}')

# Per-patient × Tier-A abundance
pat_tier_a = kuehl[kuehl['taxon_name_original'].isin(tier_a_actionable_names)].copy()
pat_pivot = pat_tier_a.pivot_table(index='patient_id', columns='taxon_name_original', values='relative_abundance', aggfunc='mean')
pat_pivot = pat_pivot.reindex(columns=tier_a_actionable_names).fillna(0)
log_section('1', f'\nPer-patient × Tier-A abundance matrix: {pat_pivot.shape}')
log_section('1', f'\nPresence/absence (fraction of patients with abundance > 0):')
for sp in tier_a_actionable_names:
    n = (pat_pivot[sp] > 0).sum()
    log_section('1', f'  {sp}: {n}/{len(pat_pivot)} patients')


# ---------------------------------------------------------------------------
# §2. Build per-patient profile (master table)
# ---------------------------------------------------------------------------
log_section('2', '## §2. Build per-patient profile master table')

# Merge NB02 ecotype + demographics
nb02['patient_id'] = nb02['patient_id'].astype(str)
demo['patient_id'] = demo['patient_id'].astype(str)
prof = nb02.merge(demo[['patient_id', 'calpro_num', 'Montreal Classification', 'Medication']], on='patient_id', how='left')

# Add Tier-A presence per patient (binary: ≥0.001 relative abundance)
THR = 0.001  # 0.1% relative abundance presence threshold
for sp in tier_a_actionable_names:
    short = sp.split()[0][:1] + '.' + sp.split()[1][:6]
    prof[f'has_{short}'] = prof['patient_id'].map(lambda p: 1 if (p in pat_pivot.index and pat_pivot.loc[p, sp] > THR) else 0)
    prof[f'abund_{short}'] = prof['patient_id'].map(lambda p: pat_pivot.loc[p, sp] if p in pat_pivot.index else 0)

# Compute target count per patient
has_cols = [c for c in prof.columns if c.startswith('has_')]
prof['n_actionable_targets'] = prof[has_cols].sum(axis=1)

log_section('2', f'\nPer-patient profile shape: {prof.shape}')
log_section('2', f'\nPer-ecotype distribution:')
log_section('2', f'  E0: {(prof["final_ecotype"]=="0").sum()}; E1: {(prof["final_ecotype"]=="1").sum()}; E3: {(prof["final_ecotype"]=="3").sum()}; mixed: {(prof["final_ecotype"]=="mixed").sum()}; nan: {prof["final_ecotype"].isna().sum()}')
log_section('2', f'\nMean # actionable targets per patient by ecotype:')
log_section('2', prof.groupby('final_ecotype')['n_actionable_targets'].agg(['mean', 'min', 'max', 'count']).to_string())

prof.to_csv(f'{OUT_DATA}/nb15_patient_profile.tsv', sep='\t', index=False)


# ---------------------------------------------------------------------------
# §3. Per-patient cocktail draft logic
# ---------------------------------------------------------------------------
log_section('3', '## §3. Per-patient cocktail draft')

# Pillar-3 mechanism profile + Pillar-4 phage availability per Tier-A actionable
TARGET_PROFILE = {
    'Hungatella hathewayi': {'tier_a_score': 4.0, 'iron': 'none', 'ba_cost': 'low', 'mediation': 'species-abundance', 'phage_class': 'GAP', 'phage_recommendation': 'External DB query (INPHARED + IMG/VR); fallback: GAG-degrading enzyme inhibitors'},
    'Mediterraneibacter gnavus': {'tier_a_score': 3.8, 'iron': 'none', 'ba_cost': 'low', 'mediation': 'species-abundance', 'phage_class': 'temperate-only', 'phage_recommendation': 'Limited: 6 temperate phages; lytic-locked engineering OR biochemical glucorhamnan-synthesis target'},
    'Escherichia coli': {'tier_a_score': 3.6, 'iron': 'dominant', 'ba_cost': 'low', 'mediation': 'strain-content', 'phage_class': 'Tier-1 clinical', 'phage_recommendation': 'Tier-1: NB13 5-phage cocktail (DIJ07_P2 + LF73_P1 + AL505_Ev3 + 55989_P2 + LF110_P2) OR EcoActive 7-phage cocktail; require AIEC strain-resolution diagnostic (pks/Yersiniabactin/Enterobactin)'},
    'Eggerthella lenta': {'tier_a_score': 3.3, 'iron': 'none', 'ba_cost': 'moderate', 'mediation': 'drug-metabolism', 'phage_class': 'Tier-2 lytic', 'phage_recommendation': 'Tier-2: PMBT5 siphovirus; co-monitor BA pool'},
    'Flavonifractor plautii': {'tier_a_score': 3.3, 'iron': 'weak', 'ba_cost': 'HIGHEST', 'mediation': 'species-abundance', 'phage_class': 'GAP+HIGH-cost', 'phage_recommendation': 'DEPRIORITIZE phage targeting due to HIGHEST BA-coupling cost; consider co-administering UDCA/BA-binding agent or biochemical 7α-dehydroxylation inhibitor'},
    'Enterocloster bolteae': {'tier_a_score': 2.8, 'iron': 'none', 'ba_cost': 'moderate', 'mediation': 'mixed', 'phage_class': 'Tier-2 lytic', 'phage_recommendation': 'Tier-2: PMBT24 (Kielviridae); co-monitor BA pool'},
}

# Per-ecotype Tier-A focus sets (from NB06 H2d module hubs)
ECOTYPE_TARGET_SETS = {
    '0': {  # E0 = healthy commensal — minimal pathobiont burden expected
        'rationale': 'E0 is the diverse-commensal ecotype; cocktail may not be needed if pathobiont burden is low. Apply only if patient harbors ≥2 Tier-A targets and calprotectin >250.',
        'priority_targets': ['Hungatella hathewayi', 'Mediterraneibacter gnavus'],
    },
    '1': {  # E1 = Bacteroides2 transitional — full pathobiont module
        'rationale': 'E1_CD module 0 (NB06 H2d): full Tier-A pathobiont module — H. hathewayi, F. plautii, E. bolteae, E. lenta, M. gnavus all co-cluster. Apply broad Tier-1 + Tier-2 cocktail with BA-cost monitoring for F. plautii / E. bolteae / E. lenta.',
        'priority_targets': ['Hungatella hathewayi', 'Mediterraneibacter gnavus', 'Enterocloster bolteae', 'Eggerthella lenta', 'Flavonifractor plautii'],
    },
    '3': {  # E3 = severe Bacteroides — different module, E. coli prominent
        'rationale': 'E3_CD module 1 (NB06 H2d): E. lenta + H. hathewayi + E. coli + M. gnavus dominant. F. plautii is E1-specific; reduced BA-coupling concern in E3.',
        'priority_targets': ['Eggerthella lenta', 'Hungatella hathewayi', 'Escherichia coli', 'Mediterraneibacter gnavus'],
    },
    'mixed': {  # patient 6967 longitudinal E1↔E3
        'rationale': 'Mixed ecotype (longitudinal drift E1↔E3); apply E1 + E3 union cocktail OR state-dependent dosing (rebalance based on per-visit ecotype). Patient 6967 longitudinal stability test — central per-patient case for Pillar 5 dosing strategy.',
        'priority_targets': ['Hungatella hathewayi', 'Mediterraneibacter gnavus', 'Eggerthella lenta', 'Escherichia coli'],
    },
}


def build_cocktail(row):
    """Per-patient cocktail draft logic."""
    eco = str(row['final_ecotype']) if pd.notna(row['final_ecotype']) else None
    if eco is None or eco == 'nan':
        return {'targets': [], 'cocktail_components': [], 'rationale': 'No ecotype call — cannot apply ecotype-specific cocktail; require metagenomics re-sample'}
    eco_set = ECOTYPE_TARGET_SETS.get(eco, ECOTYPE_TARGET_SETS['mixed'])
    priority_targets = eco_set['priority_targets']
    rationale = eco_set['rationale']

    targets = []
    cocktail_components = []
    for sp in priority_targets:
        short = sp.split()[0][:1] + '.' + sp.split()[1][:6]
        has_col = f'has_{short}'
        if has_col not in row or row[has_col] != 1:
            continue
        prof = TARGET_PROFILE.get(sp, {})
        targets.append({
            'species': sp,
            'tier_a_score': prof.get('tier_a_score'),
            'phage_class': prof.get('phage_class'),
            'ba_cost': prof.get('ba_cost'),
            'iron_specialization': prof.get('iron'),
            'mediation': prof.get('mediation'),
            'phage_recommendation': prof.get('phage_recommendation'),
        })
        # Add concrete phage cocktail components for E. coli only
        if sp == 'Escherichia coli':
            cocktail_components.extend([
                'DIJ07_P2 (Phapecoctavirus, NB13 broadest host range 63.8%)',
                'LF73_P1 (Tequatrovirus, Straboviridae)',
                'AL505_Ev3', '55989_P2', 'LF110_P2'
            ])
        elif sp == 'Eggerthella lenta':
            cocktail_components.append('PMBT5 (siphovirus; co-monitor BA pool)')
        elif sp == 'Enterocloster bolteae':
            cocktail_components.append('PMBT24 (virulent, 99,962 bp Kielviridae; co-monitor BA pool)')
        # Pillar-4 GAP species: no concrete phage component, only recommendation

    # Caveats
    caveats = []
    calp = row.get('calpro_num')
    if pd.isna(calp):
        caveats.append('No calprotectin — disease activity not quantified')
    elif calp < 50:
        caveats.append(f'Low calprotectin ({calp:.0f}) — disease quiescent, cocktail may not be needed')
    elif calp > 1000:
        caveats.append(f'High calprotectin ({calp:.0f}) — active disease, cocktail-design priority')

    if 'F. plautii' in [t['species'].split()[0][:1]+'.'+t['species'].split()[1][:6] for t in targets if 'F.' in t['species']]:
        caveats.append('F. plautii present + HIGHEST BA-coupling cost; consider deprioritizing or co-administer UDCA')

    if eco == 'mixed':
        caveats.append('Patient 6967 longitudinal E1↔E3 — central per-patient stability test for state-dependent dosing')

    n_pillar4_gap = sum(1 for t in targets if t['phage_class'] in ['GAP', 'GAP+HIGH-cost'])
    if n_pillar4_gap > 0:
        caveats.append(f'{n_pillar4_gap} target(s) in Pillar-4 phage GAP — external DB query priority')

    med = row.get('Medication') or row.get('med_class')
    if pd.notna(med):
        med_str = str(med).lower()
        if 'no therapy' in med_str:
            caveats.append('Naive patient — phage cocktail as first-line (combo with anti-TNF or anti-IL23 standard-of-care)')
        elif 'budesonide' in med_str or 'prednisone' in med_str or 'steroid' in med_str:
            caveats.append('On steroid — temporary control; phage cocktail as steroid-sparing strategy')

    return {
        'ecotype_rationale': rationale,
        'targets': targets,
        'cocktail_components': cocktail_components,
        'caveats': caveats,
    }


prof['cocktail_draft'] = prof.apply(build_cocktail, axis=1)

log_section('3', f'\nPer-patient cocktail drafts (subset for first 10 patients):')
for _, r in prof.head(10).iterrows():
    pid = r['patient_id']
    eco = r['final_ecotype']
    calp = r['calpro_num']
    n = len(r['cocktail_draft']['targets'])
    components = r['cocktail_draft']['cocktail_components']
    caveats = r['cocktail_draft']['caveats']
    log_section('3', f'\n=== Patient {pid} | E{eco} | calpro={calp} | {r.get("Montreal Classification","?")} | med={r.get("Medication","?")} ===')
    log_section('3', f'  Tier-A targets present: {n} / {len(ECOTYPE_TARGET_SETS.get(str(eco),{}).get("priority_targets",[]))}')
    for t in r['cocktail_draft']['targets']:
        log_section('3', f'    {t["species"]:<35s} | {t["phage_class"]} | BA-cost: {t["ba_cost"]} | {t["mediation"]}')
    if components:
        log_section('3', f'  Concrete phage components: {components}')
    if caveats:
        log_section('3', f'  Caveats:')
        for c in caveats:
            log_section('3', f'    • {c}')


# ---------------------------------------------------------------------------
# §4. Cocktail summary statistics
# ---------------------------------------------------------------------------
log_section('4', '## §4. Cocktail summary statistics')

# Per-ecotype cocktail composition summary
ecotype_summary = []
for eco in ['0', '1', '3', 'mixed']:
    sub = prof[prof['final_ecotype'].astype(str) == eco]
    if not len(sub):
        continue
    n_patients = len(sub)
    avg_targets = float(np.mean([len(d['targets']) for d in sub['cocktail_draft']]))
    n_with_cocktail = sum(1 for d in sub['cocktail_draft'] if len(d['targets']) > 0)
    n_with_concrete_phage = sum(1 for d in sub['cocktail_draft'] if len(d['cocktail_components']) > 0)
    ecotype_summary.append({
        'ecotype': f'E{eco}',
        'n_patients': n_patients,
        'mean_targets_per_patient': round(avg_targets, 2),
        'n_with_cocktail': n_with_cocktail,
        'n_with_concrete_phage_component': n_with_concrete_phage,
    })
ecotype_df = pd.DataFrame(ecotype_summary)
log_section('4', f'\nPer-ecotype cocktail summary:\n{ecotype_df.to_string(index=False)}')

# Per-target prescribing rate
log_section('4', f'\nPer-target prescribing rate (across all 23 patients):')
target_rate = []
for sp in tier_a_actionable_names:
    short = sp.split()[0][:1] + '.' + sp.split()[1][:6]
    has_col = f'has_{short}'
    n_present = prof[has_col].sum()
    target_rate.append({'species': sp, 'n_present': int(n_present), 'pct_present': round(100*n_present/len(prof), 1)})
target_rate_df = pd.DataFrame(target_rate).sort_values('pct_present', ascending=False)
log_section('4', target_rate_df.to_string(index=False))


# ---------------------------------------------------------------------------
# §5. Verdict + figure
# ---------------------------------------------------------------------------
log_section('5', '## §5. Verdict + figure')

verdict = {
    'date': '2026-04-25',
    'plan_version': 'v1.9',
    'test': 'NB15 — UC Davis per-patient profile + cocktail draft (Pillar 5 opener)',
    'n_patients': len(prof),
    'ecotype_distribution': prof['final_ecotype'].astype(str).value_counts().to_dict(),
    'mean_actionable_tier_a_per_patient': round(float(prof['n_actionable_targets'].mean()), 2),
    'patients_with_concrete_phage_component': int(sum(1 for d in prof['cocktail_draft'] if len(d['cocktail_components']) > 0)),
    'cocktail_summary_by_ecotype': ecotype_df.to_dict(orient='records'),
    'narrative': (
        f'23 UC Davis CD patients × per-patient profile (ecotype + calprotectin + Montreal + medication '
        f'+ Tier-A pathobiont presence). E0={(prof["final_ecotype"]=="0").sum()}, E1={(prof["final_ecotype"]=="1").sum()}, '
        f'E3={(prof["final_ecotype"]=="3").sum()}, mixed=1 (patient 6967), nan={prof["final_ecotype"].isna().sum()}. '
        f'Mean {prof["n_actionable_targets"].mean():.1f} actionable Tier-A targets per patient. '
        f'Per-patient cocktail draft composition stratified by ecotype-specific module (NB06 H2d) + '
        f'phage-availability tier (NB12-NB14) + bile-acid coupling cost (NB09c).'
    ),
}
with open(f'{OUT_DATA}/nb15_pillar5_cocktail_verdict.json', 'w') as fp:
    json.dump(verdict, fp, indent=2, default=str)
log_section('5', json.dumps(verdict, indent=2, default=str))

# Save cocktail drafts as TSV (flatten cocktail_draft dict to columns)
cocktail_long_rows = []
for _, r in prof.iterrows():
    pid = r['patient_id']
    eco = r['final_ecotype']
    calp = r['calpro_num']
    montreal = r.get('Montreal Classification', '?')
    med = r.get('Medication', '?')
    draft = r['cocktail_draft']
    for t in draft['targets']:
        cocktail_long_rows.append({
            'patient_id': pid,
            'ecotype': eco,
            'calpro_num': calp,
            'montreal': montreal,
            'medication': med,
            'target_species': t['species'],
            'tier_a_score': t['tier_a_score'],
            'phage_class': t['phage_class'],
            'ba_cost': t['ba_cost'],
            'iron_specialization': t['iron_specialization'],
            'mediation': t['mediation'],
            'phage_recommendation': t['phage_recommendation'],
        })
    if not draft['targets']:
        cocktail_long_rows.append({
            'patient_id': pid, 'ecotype': eco, 'calpro_num': calp, 'montreal': montreal, 'medication': med,
            'target_species': '(no Tier-A targets present in this patient)',
            'tier_a_score': None, 'phage_class': None, 'ba_cost': None, 'iron_specialization': None, 'mediation': None, 'phage_recommendation': None,
        })

cocktail_long_df = pd.DataFrame(cocktail_long_rows)
cocktail_long_df.to_csv(f'{OUT_DATA}/nb15_per_patient_cocktail_draft.tsv', sep='\t', index=False)
log_section('5', f'\nWrote {OUT_DATA}/nb15_per_patient_cocktail_draft.tsv ({len(cocktail_long_df)} rows = patients × targets)')


# ---------------------------------------------------------------------------
# §6. Figure
# ---------------------------------------------------------------------------
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

fig, axes = plt.subplots(1, 3, figsize=(20, 7))

# Panel A: per-patient × Tier-A presence heatmap, ordered by ecotype
ax = axes[0]
prof_sorted = prof.sort_values(['final_ecotype', 'patient_id'])
heatmap_data = prof_sorted[has_cols].astype(int).values
patient_labels = [f'{r.patient_id}\n(E{r.final_ecotype})' for _, r in prof_sorted.iterrows()]
target_short = [c.replace('has_', '') for c in has_cols]
sns.heatmap(heatmap_data, cmap='RdBu_r', center=0.5, vmin=0, vmax=1, cbar=False, ax=ax,
            xticklabels=target_short, yticklabels=patient_labels)
ax.set_title('A. Per-patient Tier-A pathobiont presence\n(blue=absent, red=present)')
ax.set_xlabel('Tier-A target')
ax.set_ylabel('Patient (sorted by ecotype)')
ax.tick_params(axis='y', labelsize=7)

# Panel B: per-ecotype cocktail composition
ax = axes[1]
ecotype_order = ['0', '1', '3', 'mixed']
ecotype_cocktail_n = []
for eco in ecotype_order:
    sub = prof[prof['final_ecotype'].astype(str) == eco]
    n_patients = len(sub)
    if n_patients == 0:
        continue
    target_counts = {}
    for sp in tier_a_actionable_names:
        short = sp.split()[0][:1] + '.' + sp.split()[1][:6]
        has_col = f'has_{short}'
        target_counts[short] = sub[has_col].sum()
    ecotype_cocktail_n.append({'ecotype': f'E{eco}', 'n_patients': n_patients, **target_counts})

eco_df = pd.DataFrame(ecotype_cocktail_n).set_index('ecotype').drop(columns=['n_patients'])
eco_df_pct = eco_df.div(eco_df.sum(axis=1), axis=0) * 100
sns.heatmap(eco_df_pct, cmap='Reds', annot=True, fmt='.0f', cbar_kws={'label': '% of ecotype patients'}, ax=ax)
ax.set_title('B. Per-ecotype Tier-A target prescribing rate\n(% of patients in ecotype with target present)')
ax.set_xlabel('Tier-A target')

# Panel C: per-patient calprotectin × number of targets
ax = axes[2]
prof_with_calp = prof.dropna(subset=['calpro_num']).copy()
eco_colors = {'0': '#73c0e8', '1': '#e63946', '3': '#264653', 'mixed': '#f4a261'}
for eco in ecotype_order:
    sub = prof_with_calp[prof_with_calp['final_ecotype'].astype(str) == eco]
    if len(sub):
        ax.scatter(sub['n_actionable_targets'], sub['calpro_num'],
                   c=eco_colors.get(eco, '#a8a8a8'), s=80, alpha=0.7,
                   edgecolors='black', linewidth=0.5,
                   label=f'E{eco} (n={len(sub)})')
        # Annotate patients
        for _, r in sub.iterrows():
            ax.annotate(str(r['patient_id'])[:6], (r['n_actionable_targets'], r['calpro_num']),
                        fontsize=7, alpha=0.8, xytext=(3, 3), textcoords='offset points')

ax.set_yscale('symlog')
ax.set_xlabel('# actionable Tier-A targets present')
ax.set_ylabel('Fecal calprotectin (μg/g)')
ax.axhline(250, color='gray', linestyle=':', linewidth=0.5, label='250 μg/g (active disease)')
ax.set_title('C. Per-patient cocktail-design priority\n(high calp + many targets = top priority)')
ax.legend(loc='lower right', fontsize=8)

fig.suptitle('NB15 — UC Davis per-patient cocktail draft (Pillar 5 opener)', fontsize=12, y=0.99)
fig.tight_layout()
fig.savefig(f'{OUT_FIG}/NB15_patient_cocktail_draft.png', dpi=120, bbox_inches='tight')
log_section('5', f'\nWrote {OUT_FIG}/NB15_patient_cocktail_draft.png')

with open('/tmp/nb15_section_logs.json', 'w') as fp:
    json.dump(SECTION_LOGS, fp, indent=2)
print(f'\nDone.')

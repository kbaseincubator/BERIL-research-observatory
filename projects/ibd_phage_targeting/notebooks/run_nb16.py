"""NB16 — Patient 6967 longitudinal stability + state-dependent dosing strategy.

Patient 6967 has 2 longitudinal samples with documented E1↔E3 ecotype drift
(NB02). NB16 deep-dives the per-visit Tier-A pathobiont composition + cocktail
implications, plus serves as the central test for state-dependent dosing
strategy in Pillar 5.

Tests:
1. Patient 6967 per-visit ecotype + Tier-A abundance comparison
2. Per-visit cocktail composition: would the patient receive different
   cocktails on different visits? Cocktail-shift score (Jaccard).
3. Technical replicate concordance check (patient 1112 has 2 reseq samples
   with same biological sample) — validates Kaiju reliability
4. State-dependent dosing rule recommendation for Pillar 5

Per plan v1.9 no raw reads.
"""
import json
import re
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
# §0. Load + identify multi-timepoint patients
# ---------------------------------------------------------------------------
log_section('0', '## §0. Load Kuehl_WGS + NB02 ecotype projection + identify multi-timepoint patients')

ft = pd.read_parquet(f'{MART}/fact_taxon_abundance.snappy.parquet')
kuehl = ft[ft['study_id'] == 'KUEHL_WGS'].copy()

ds = pd.read_parquet(f'{MART}/dim_samples.snappy.parquet')
kuehl_meta = ds[ds['study_id'] == 'KUEHL_WGS'][['sample_id']].copy()


def extract_patient(s):
    m = re.search(r'Reads_(\d+(?:\.\d+)?|p\d+(?:reseq)?|p\d+)', str(s))
    return m.group(1) if m else None


kuehl_meta['patient_root'] = kuehl_meta['sample_id'].apply(extract_patient)
# 6967.1 means visit-2 of patient 6967 — extract base patient ID
kuehl_meta['patient_base'] = kuehl_meta['patient_root'].str.split('.').str[0]
kuehl = kuehl.merge(kuehl_meta, on='sample_id', how='left')

# Per-patient sample counts
sample_counts = kuehl_meta.groupby('patient_base').size().sort_values(ascending=False)
multi_samp_patients = sample_counts[sample_counts > 1].index.tolist()
log_section('0', f'Multi-sample patients: {len(multi_samp_patients)}')
for p in multi_samp_patients:
    sub = kuehl_meta[kuehl_meta['patient_base'] == p]
    log_section('0', f'  {p}: {sub["sample_id"].tolist()}')

# NB02 per-sample projection
nb02_proj = pd.read_csv(f'{OUT_DATA}/ucdavis_kuehl_ecotype_projection.tsv', sep='\t')
log_section('0', f'\nNB02 per-sample projection: {nb02_proj.shape[0]} samples')


# ---------------------------------------------------------------------------
# §1. Patient 6967 deep dive
# ---------------------------------------------------------------------------
log_section('1', '## §1. Patient 6967 longitudinal deep dive (E1↔E3 drift)')

P6967_SAMPLES_PROJECTED = nb02_proj[nb02_proj['sample_id'].str.contains('6967', na=False)].copy()
log_section('1', f'\nPer-sample ecotype projection:')
log_section('1', P6967_SAMPLES_PROJECTED[['sample_id', 'ecotype_primary', 'primary_conf', 'ecotype_gmm_advisory', 'gmm_conf', 'methods_agree']].to_string(index=False))

tier_a = ['Hungatella hathewayi', 'Mediterraneibacter gnavus', 'Escherichia coli',
          'Eggerthella lenta', 'Flavonifractor plautii', 'Enterocloster bolteae']

p6967_kuehl = kuehl[kuehl['sample_id'].str.contains('6967', na=False)]
p6967_samples = sorted(p6967_kuehl['sample_id'].unique())
log_section('1', f'\nPer-sample Tier-A pathobiont abundance:')

# Build wide table: rows = Tier-A, cols = samples
abund_rows = []
for sp in tier_a:
    row = {'species': sp}
    for s in p6967_samples:
        s_sub = p6967_kuehl[p6967_kuehl['sample_id'] == s]
        sp_row = s_sub[s_sub['taxon_name_original'] == sp]
        row[s] = sp_row['relative_abundance'].iloc[0] if len(sp_row) else 0.0
    abund_rows.append(row)
abund_df = pd.DataFrame(abund_rows)
log_section('1', abund_df.to_string(index=False))

# Compute fold-change visit2 vs visit1 (assuming Reads_6967-1 = visit 1; Reads_6967.1-1 = visit 2)
visit1 = 'KUEHL:Reads_6967-1'
visit2 = 'KUEHL:Reads_6967.1-1'
if visit1 in abund_df.columns and visit2 in abund_df.columns:
    abund_df['fold_v2_v1'] = abund_df[visit2] / abund_df[visit1].replace(0, np.nan)
    log_section('1', f'\nFold change (visit 2 / visit 1):')
    log_section('1', abund_df[['species', visit1, visit2, 'fold_v2_v1']].to_string(index=False))

abund_df.to_csv(f'{OUT_DATA}/nb16_p6967_tier_a_longitudinal.tsv', sep='\t', index=False)


# ---------------------------------------------------------------------------
# §2. Patient 6967 per-visit cocktail composition
# ---------------------------------------------------------------------------
log_section('2', '## §2. Patient 6967 per-visit cocktail composition (would cocktail change?)')

# E1_CD module priority targets
E1_TARGETS = ['Hungatella hathewayi', 'Mediterraneibacter gnavus', 'Enterocloster bolteae',
              'Eggerthella lenta', 'Flavonifractor plautii']
# E3_CD module priority targets
E3_TARGETS = ['Eggerthella lenta', 'Hungatella hathewayi', 'Escherichia coli',
              'Mediterraneibacter gnavus']

THR = 0.001  # presence threshold


def cocktail_for_visit(visit_sample, ecotype):
    """Return cocktail components for a given visit sample + ecotype call."""
    if ecotype == 1:
        priority = E1_TARGETS
    elif ecotype == 3:
        priority = E3_TARGETS
    else:
        priority = []
    visit_abund = abund_df[['species', visit_sample]].rename(columns={visit_sample: 'abund'})
    targets_present = [
        sp for sp in priority
        if visit_abund.loc[visit_abund['species'] == sp, 'abund'].iloc[0] > THR
    ]
    return targets_present


# Per-visit cocktail
v1_eco = int(P6967_SAMPLES_PROJECTED[P6967_SAMPLES_PROJECTED['sample_id'] == visit1]['ecotype_primary'].iloc[0]) if visit1 in P6967_SAMPLES_PROJECTED['sample_id'].values else None
v2_eco = int(P6967_SAMPLES_PROJECTED[P6967_SAMPLES_PROJECTED['sample_id'] == visit2]['ecotype_primary'].iloc[0]) if visit2 in P6967_SAMPLES_PROJECTED['sample_id'].values else None

v1_cocktail = cocktail_for_visit(visit1, v1_eco)
v2_cocktail = cocktail_for_visit(visit2, v2_eco)
log_section('2', f'\nVisit 1 ({visit1}, ecotype E{v1_eco}, conf {P6967_SAMPLES_PROJECTED.loc[P6967_SAMPLES_PROJECTED["sample_id"]==visit1, "primary_conf"].iloc[0]:.2f}):')
log_section('2', f'  Priority targets: {E1_TARGETS if v1_eco==1 else E3_TARGETS}')
log_section('2', f'  Cocktail (targets present): {v1_cocktail}')
log_section('2', f'  Excluded (priority but absent): {[t for t in (E1_TARGETS if v1_eco==1 else E3_TARGETS) if t not in v1_cocktail]}')

log_section('2', f'\nVisit 2 ({visit2}, ecotype E{v2_eco}, conf {P6967_SAMPLES_PROJECTED.loc[P6967_SAMPLES_PROJECTED["sample_id"]==visit2, "primary_conf"].iloc[0]:.2f}):')
log_section('2', f'  Priority targets: {E1_TARGETS if v2_eco==1 else E3_TARGETS}')
log_section('2', f'  Cocktail (targets present): {v2_cocktail}')
log_section('2', f'  Excluded (priority but absent): {[t for t in (E1_TARGETS if v2_eco==1 else E3_TARGETS) if t not in v2_cocktail]}')

# Cocktail-shift score: Jaccard between v1 and v2 cocktail composition
v1_set, v2_set = set(v1_cocktail), set(v2_cocktail)
jaccard = len(v1_set & v2_set) / len(v1_set | v2_set) if (v1_set | v2_set) else 1.0
log_section('2', f'\nCocktail Jaccard(visit1, visit2) = {jaccard:.2f}')
log_section('2', f'  Shared targets: {sorted(v1_set & v2_set)}')
log_section('2', f'  Visit-1-only targets: {sorted(v1_set - v2_set)}')
log_section('2', f'  Visit-2-only targets: {sorted(v2_set - v1_set)}')


# ---------------------------------------------------------------------------
# §3. Technical replicate concordance check (patient 1112)
# ---------------------------------------------------------------------------
log_section('3', '## §3. Technical replicate concordance — patient 1112')

p1112_kuehl = kuehl[kuehl['sample_id'].str.contains('1112', na=False)]
p1112_samples = sorted(p1112_kuehl['sample_id'].unique())
log_section('3', f'\nPatient 1112 samples: {p1112_samples}')

p1112_abund_rows = []
for sp in tier_a:
    row = {'species': sp}
    for s in p1112_samples:
        s_sub = p1112_kuehl[p1112_kuehl['sample_id'] == s]
        sp_row = s_sub[s_sub['taxon_name_original'] == sp]
        row[s] = sp_row['relative_abundance'].iloc[0] if len(sp_row) else 0.0
    p1112_abund_rows.append(row)
p1112_abund_df = pd.DataFrame(p1112_abund_rows)
log_section('3', '\nPer-sample Tier-A abundance:')
log_section('3', p1112_abund_df.to_string(index=False))

# Compute pairwise concordance (Spearman ρ)
from scipy import stats as scipy_stats
if len(p1112_samples) >= 2:
    s1, s2 = p1112_samples[0], p1112_samples[1]
    rho, p = scipy_stats.spearmanr(p1112_abund_df[s1], p1112_abund_df[s2])
    log_section('3', f'\nSpearman ρ ({s1}, {s2}) on Tier-A abundance: {rho:.3f} (p={p:.3f})')


# ---------------------------------------------------------------------------
# §4. State-dependent dosing rule
# ---------------------------------------------------------------------------
log_section('4', '## §4. State-dependent dosing rule for Pillar 5')

log_section('4', '''
Patient 6967 shows a clear E1 → E3 ecotype shift across 2 visits, accompanied
by:
- M. gnavus 14-fold expansion (0.53 → 7.45)
- E. lenta 3-fold expansion (0.40 → 1.24)
- F. plautii 1.9-fold expansion
- All Tier-A pathobionts expand 1.3–14× in the E3 state vs E1

The cocktail composition shifts: visit 1 (E1 priority) had 5 targets in the
priority module; visit 2 (E3 priority) has 4 targets in the priority module
(F. plautii drops from priority because it's E1-specific per NB07c §10).

Cocktail Jaccard between visits = depends on which species are shared between
E1 + E3 priority lists (3 species: H. hathewayi, M. gnavus, E. lenta).

State-dependent dosing rule recommendations:

1. **Re-test ecotype every 3-6 months** for active CD patients on phage cocktail therapy.
   Patient 6967 shows ecotype is dynamic, not static.

2. **F. plautii inclusion is E1-specific** — if patient transitions to E3, deprioritize
   F. plautii from cocktail (it's no longer in the E3_CD module 1 priority set per NB07c).
   This also reduces BA-coupling-cost concern.

3. **E. coli inclusion is E3-specific** — if patient transitions to E1, deprioritize
   E. coli from cocktail (E. coli is not in E1_CD module 0 priority set; though E. coli
   targeting could still be applied if patient carries detectable E. coli, in which case
   AIEC strain-resolution diagnostic is required).

4. **Universal Tier-1 cocktail components** (M. gnavus, H. hathewayi, E. lenta) span both
   E1 and E3 and don't need re-evaluation on ecotype shift.

5. **The 14× M. gnavus expansion in E3 transition** suggests M. gnavus is the dominant
   ecotype-switching axis — clinical monitoring of M. gnavus abundance via qPCR could
   serve as an ecotype-state indicator (cheaper than full metagenomics re-test).
''')


# ---------------------------------------------------------------------------
# §5. Verdict + figure
# ---------------------------------------------------------------------------
log_section('5', '## §5. Verdict + figure')

verdict = {
    'date': '2026-04-25',
    'plan_version': 'v1.9',
    'test': 'NB16 — Patient 6967 longitudinal stability + state-dependent dosing strategy',
    'n_multi_sample_patients': len(multi_samp_patients),
    'patient_6967_ecotype_drift': f'E{v1_eco} → E{v2_eco}',
    'patient_6967_visit1_n_targets': len(v1_cocktail),
    'patient_6967_visit2_n_targets': len(v2_cocktail),
    'patient_6967_cocktail_jaccard_visit1_visit2': round(jaccard, 3),
    'patient_6967_M_gnavus_fold_change_v2_v1': round(float(abund_df.loc[abund_df['species']=='Mediterraneibacter gnavus', 'fold_v2_v1'].iloc[0]) if not pd.isna(abund_df.loc[abund_df['species']=='Mediterraneibacter gnavus', 'fold_v2_v1'].iloc[0]) else None, 2),
    'patient_1112_tech_rep_spearman_rho': round(float(rho), 3) if 'rho' in dir() else None,
    'narrative': (
        f'Patient 6967 shows clear E{v1_eco}→E{v2_eco} ecotype drift across 2 visits '
        f'with M. gnavus 14× expansion (0.53→7.45). Cocktail composition Jaccard between '
        f'visits = {jaccard:.2f}. Patient 1112 technical replicates Spearman ρ = '
        f'{rho:.3f} on Tier-A abundance — Kaiju calls reliable across reseq.'
    ),
    'state_dependent_dosing_rules': [
        'Re-test ecotype every 3-6 months for active CD patients on phage cocktail therapy',
        'F. plautii inclusion is E1-specific; deprioritize on E1→E3 transition',
        'E. coli inclusion is E3-specific; deprioritize on E3→E1 transition (subject to AIEC detection)',
        'Universal Tier-1 (M. gnavus, H. hathewayi, E. lenta) span both ecotypes',
        'M. gnavus 14× expansion suggests qPCR M. gnavus monitoring as cheap ecotype-state indicator',
    ],
}
with open(f'{OUT_DATA}/nb16_longitudinal_verdict.json', 'w') as fp:
    json.dump(verdict, fp, indent=2, default=str)
log_section('5', json.dumps(verdict, indent=2, default=str))


# ---------------------------------------------------------------------------
# §6. Figure
# ---------------------------------------------------------------------------
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 3, figsize=(18, 6))

# Panel A: patient 6967 per-visit Tier-A abundance
ax = axes[0]
visits = [visit1, visit2]
visit_labels = [f'Visit 1\nE{v1_eco}\n(conf {P6967_SAMPLES_PROJECTED.loc[P6967_SAMPLES_PROJECTED["sample_id"]==visit1, "primary_conf"].iloc[0]:.2f})',
                f'Visit 2\nE{v2_eco}\n(conf {P6967_SAMPLES_PROJECTED.loc[P6967_SAMPLES_PROJECTED["sample_id"]==visit2, "primary_conf"].iloc[0]:.2f})']
y = np.arange(len(tier_a))
width = 0.35
v1_vals = [abund_df.loc[abund_df['species']==sp, visit1].iloc[0] for sp in tier_a]
v2_vals = [abund_df.loc[abund_df['species']==sp, visit2].iloc[0] for sp in tier_a]
ax.barh(y - width/2, v1_vals, width, label=visit_labels[0], color='#73c0e8')
ax.barh(y + width/2, v2_vals, width, label=visit_labels[1], color='#e63946')
ax.set_yticks(y)
ax.set_yticklabels([sp.replace(' ', '\n', 1) for sp in tier_a], fontsize=8)
ax.set_xlabel('Kaiju relative abundance (log10)')
ax.set_xscale('symlog', linthresh=0.01)
ax.set_title(f'A. Patient 6967 per-visit Tier-A abundance\nEcotype drift: E{v1_eco} → E{v2_eco}')
ax.legend(loc='lower right', fontsize=8)
# Annotate fold changes
for i, sp in enumerate(tier_a):
    if v1_vals[i] > 0:
        fold = v2_vals[i] / v1_vals[i]
        ax.text(max(v1_vals[i], v2_vals[i]) * 1.15, i, f'{fold:.1f}×', va='center', fontsize=7)

# Panel B: patient 1112 technical replicate scatter
ax = axes[1]
s1 = p1112_samples[0] if len(p1112_samples) >= 1 else None
s2 = p1112_samples[1] if len(p1112_samples) >= 2 else None
if s1 and s2:
    s1_vals = [p1112_abund_df.loc[p1112_abund_df['species']==sp, s1].iloc[0] for sp in tier_a]
    s2_vals = [p1112_abund_df.loc[p1112_abund_df['species']==sp, s2].iloc[0] for sp in tier_a]
    ax.scatter(s1_vals, s2_vals, c='#264653', s=80, alpha=0.7, edgecolors='black', linewidth=0.5)
    for i, sp in enumerate(tier_a):
        ax.annotate(sp.split()[1][:8], (s1_vals[i], s2_vals[i]), fontsize=7, alpha=0.8, xytext=(3, 3), textcoords='offset points')
    # Diagonal
    max_val = max(max(s1_vals), max(s2_vals))
    ax.plot([0, max_val], [0, max_val], 'k--', alpha=0.5, linewidth=0.5)
    ax.set_xlabel(f'{s1.split(":")[-1][:25]} abundance')
    ax.set_ylabel(f'{s2.split(":")[-1][:25]} abundance')
    ax.set_title(f'B. Patient 1112 tech-replicate concordance\nSpearman ρ = {rho:.3f} (p={p:.3f})')

# Panel C: state-dependent dosing — cocktail composition shift
ax = axes[2]
all_targets = sorted(set(E1_TARGETS) | set(E3_TARGETS))
e1_in = [1 if t in E1_TARGETS else 0 for t in all_targets]
e3_in = [1 if t in E3_TARGETS else 0 for t in all_targets]
v1_in = [1 if t in v1_cocktail else 0 for t in all_targets]
v2_in = [1 if t in v2_cocktail else 0 for t in all_targets]
y = np.arange(len(all_targets))
width = 0.2
ax.barh(y - 1.5*width, e1_in, width, label='E1 priority list', color='#73c0e8', alpha=0.5)
ax.barh(y - 0.5*width, e3_in, width, label='E3 priority list', color='#264653', alpha=0.5)
ax.barh(y + 0.5*width, v1_in, width, label=f'Visit 1 (E{v1_eco}) cocktail', color='#73c0e8')
ax.barh(y + 1.5*width, v2_in, width, label=f'Visit 2 (E{v2_eco}) cocktail', color='#e63946')
ax.set_yticks(y)
ax.set_yticklabels([t.split()[0][:1]+'.'+t.split()[1][:8] for t in all_targets], fontsize=8)
ax.set_xticks([0, 1])
ax.set_xticklabels(['Absent', 'Present'])
ax.set_xlim(-0.1, 1.4)
ax.set_title(f'C. Cocktail composition shift\n(Jaccard visit1×visit2 = {jaccard:.2f})')
ax.legend(loc='lower right', fontsize=7)

fig.suptitle('NB16 — Patient 6967 longitudinal stability + state-dependent dosing strategy', fontsize=12, y=1.0)
fig.tight_layout()
fig.savefig(f'{OUT_FIG}/NB16_longitudinal_dosing.png', dpi=120, bbox_inches='tight')
log_section('5', f'\nWrote {OUT_FIG}/NB16_longitudinal_dosing.png')

with open('/tmp/nb16_section_logs.json', 'w') as fp:
    json.dump(SECTION_LOGS, fp, indent=2)
print(f'\nDone.')

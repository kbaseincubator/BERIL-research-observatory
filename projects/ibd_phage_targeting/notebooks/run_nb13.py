"""NB13 — PhageFoundry quantitative E. coli phage-cocktail design.

96 phages × 188 E. coli strains × 17,672 experimentally-tested susceptibility
pairs from PhageFoundry strain_modelling (Gaborieau 2025-10-02 phage-prediction
experiment, AUC=0.88).

Tests:
1. Per-phage host range (% of 188 E. coli strains susceptible)
2. Per-strain phage susceptibility (% of 96 phages that lyse the strain)
3. Broad-host-range phage candidates (≥30% strain coverage) for cocktail seeding
4. Phage-resistant strains (susceptible to <10% of phages) — escape candidates
5. Minimum-set-cover cocktail: smallest phage cocktail that lyses ≥95% of strains
6. Cross-reference with HMP2 viromics in-vivo observations
7. Phage host-phylogroup distribution (phages with phylogroup-A bias may miss
   AIEC strains which are predominantly phylogroup B2 / D)

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
# §0. Load PhageFoundry strain_modelling tables
# ---------------------------------------------------------------------------
log_section('0', '## §0. Load PhageFoundry strain_modelling — 96 phages × 188 strains')

import os
os.environ['KBASE_AUTH_TOKEN'] = open('/home/aparkin/.env').read().split('KBASE_AUTH_TOKEN=')[1].strip().split()[0]
from berdl_notebook_utils.setup_spark_session import get_spark_session
spark = get_spark_session()
db = 'phagefoundry_strain_modelling'

orgs = spark.sql(f'SELECT id, name, full_name FROM {db}.strainmodelling_organism').toPandas()
inter = spark.sql(f'SELECT id, organism1_id, organism2_id, value, experiment_id FROM {db}.strainmodelling_interaction').toPandas()
om_meta = spark.sql(f'SELECT param, value, organism_id FROM {db}.strainmodelling_organism_metadata').toPandas()

# Identify phages vs strains
PHAGE_PATTERN = 'phage|phi |Phi |[Pp]hage'
orgs['is_phage'] = orgs['full_name'].str.contains(PHAGE_PATTERN, case=False, na=False, regex=True)
phage_ids = set(orgs.loc[orgs['is_phage'], 'id'])
strain_ids = set(orgs.loc[~orgs['is_phage'], 'id'])
n_phages = len(phage_ids)
n_strains = len(strain_ids)
log_section('0', f'Phages: {n_phages}; E. coli strains: {n_strains}; total interactions: {len(inter)}')

# Identify phage × strain interactions
inter['is_phage_host'] = inter.apply(lambda r: (r['organism1_id'] in phage_ids) != (r['organism2_id'] in phage_ids), axis=1)
ph = inter[inter['is_phage_host']].copy()
# Normalize: phage_id, strain_id
ph['phage_id'] = ph.apply(lambda r: r['organism1_id'] if r['organism1_id'] in phage_ids else r['organism2_id'], axis=1)
ph['strain_id'] = ph.apply(lambda r: r['organism2_id'] if r['organism1_id'] in phage_ids else r['organism1_id'], axis=1)
log_section('0', f'Phage × strain interactions: {len(ph)} ({ph["value"].sum()} susceptible / {(ph["value"]==0).sum()} resistant)')

# Susceptibility matrix: 96 phages (rows) × 188 strains (cols)
mat = ph.pivot_table(index='phage_id', columns='strain_id', values='value', aggfunc='first', fill_value=np.nan)
log_section('0', f'Susceptibility matrix: {mat.shape}')

# Phage metadata wide
om_wide = om_meta.pivot(index='organism_id', columns='param', values='value').reset_index()
log_section('0', f'Phage metadata: {om_wide.shape} ({om_wide.columns.tolist()})')


# ---------------------------------------------------------------------------
# §1. Per-phage host range
# ---------------------------------------------------------------------------
log_section('1', '## §1. Per-phage host range (% of 188 E. coli strains lysed)')

phage_range = []
for pid in mat.index:
    row = mat.loc[pid].dropna()
    n_tested = len(row)
    n_lysed = int(row.sum())
    pct = n_lysed / n_tested if n_tested else 0
    phage_name = orgs.loc[orgs['id'] == pid, 'full_name'].iloc[0]
    phage_range.append({
        'phage_id': pid,
        'phage_name': phage_name,
        'n_strains_tested': n_tested,
        'n_strains_lysed': n_lysed,
        'host_range_pct': round(100 * pct, 1),
    })

# Add phage metadata
phage_range_df = pd.DataFrame(phage_range)
phage_range_df = phage_range_df.merge(om_wide.rename(columns={'organism_id': 'phage_id'}), on='phage_id', how='left')
phage_range_df = phage_range_df.sort_values('host_range_pct', ascending=False)
phage_range_df.to_csv(f'{OUT_DATA}/nb13_phage_host_range.tsv', sep='\t', index=False)

log_section('1', f'\nHost-range distribution:')
log_section('1', f'  median: {phage_range_df["host_range_pct"].median():.1f}%')
log_section('1', f'  mean: {phage_range_df["host_range_pct"].mean():.1f}%')
log_section('1', f'  range: [{phage_range_df["host_range_pct"].min():.1f}%, {phage_range_df["host_range_pct"].max():.1f}%]')
log_section('1', f'  ≥30 % host range (broad): {(phage_range_df["host_range_pct"] >= 30).sum()} phages')
log_section('1', f'  ≥50 % host range (very broad): {(phage_range_df["host_range_pct"] >= 50).sum()} phages')

log_section('1', f'\nTop 15 broadest-host-range phages:')
log_section('1', phage_range_df.head(15)[['phage_name', 'host_range_pct', 'Family', 'Genus', 'Phage_host_phylo']].to_string(index=False))


# ---------------------------------------------------------------------------
# §2. Per-strain phage susceptibility
# ---------------------------------------------------------------------------
log_section('2', '## §2. Per-strain phage susceptibility (% of 96 phages that lyse the strain)')

strain_susc = []
for sid in mat.columns:
    col = mat[sid].dropna()
    n_tested = len(col)
    n_lysed = int(col.sum())
    pct = n_lysed / n_tested if n_tested else 0
    strain_name = orgs.loc[orgs['id'] == sid, 'full_name'].iloc[0]
    strain_susc.append({
        'strain_id': sid,
        'strain_name': strain_name,
        'n_phages_tested': n_tested,
        'n_phages_lysed': n_lysed,
        'phage_susceptibility_pct': round(100 * pct, 1),
    })
strain_susc_df = pd.DataFrame(strain_susc).sort_values('phage_susceptibility_pct', ascending=False)
strain_susc_df.to_csv(f'{OUT_DATA}/nb13_strain_phage_susceptibility.tsv', sep='\t', index=False)

log_section('2', f'\nStrain-susceptibility distribution:')
log_section('2', f'  median: {strain_susc_df["phage_susceptibility_pct"].median():.1f}%')
log_section('2', f'  range: [{strain_susc_df["phage_susceptibility_pct"].min():.1f}%, {strain_susc_df["phage_susceptibility_pct"].max():.1f}%]')
log_section('2', f'  ≤5 % susceptibility (resistant): {(strain_susc_df["phage_susceptibility_pct"] <= 5).sum()} strains')
log_section('2', f'  ≥50 % susceptibility (broadly susceptible): {(strain_susc_df["phage_susceptibility_pct"] >= 50).sum()} strains')

log_section('2', f'\nMost phage-resistant strains (top 10 by lowest susceptibility):')
log_section('2', strain_susc_df.tail(10)[['strain_name', 'phage_susceptibility_pct', 'n_phages_lysed', 'n_phages_tested']].to_string(index=False))
log_section('2', f'\nMost phage-susceptible strains (top 10):')
log_section('2', strain_susc_df.head(10)[['strain_name', 'phage_susceptibility_pct', 'n_phages_lysed', 'n_phages_tested']].to_string(index=False))


# ---------------------------------------------------------------------------
# §3. Minimum-set-cover cocktail design (greedy)
# ---------------------------------------------------------------------------
log_section('3', '## §3. Minimum-set-cover cocktail (greedy approximation)')

# Goal: find smallest set of phages that lyses ≥X% of 188 strains
# Greedy algorithm: at each step, add the phage that lyses the most still-uncovered strains

def greedy_cover(mat, target_coverage=0.95):
    """Greedy minimum-set-cover. mat is phages × strains susceptibility (1=susceptible, 0=resistant, NaN=untested).
    Treat NaN as 0 (conservative — assume resistant unless tested susceptible)."""
    M = mat.fillna(0).astype(int).values  # phages × strains
    n_phages, n_strains = M.shape
    target_strains = int(target_coverage * n_strains)
    covered = np.zeros(n_strains, dtype=bool)
    cocktail = []
    while covered.sum() < target_strains:
        # For each phage, count still-uncovered strains it would cover
        coverage_gain = M[:, ~covered].sum(axis=1)
        # If multiple phages tied, pick first
        if coverage_gain.max() == 0:
            break
        best_phage_idx = int(coverage_gain.argmax())
        cocktail.append(best_phage_idx)
        # Mark covered
        covered |= (M[best_phage_idx] == 1)
        if len(cocktail) > 96:
            break  # safety
    return cocktail, int(covered.sum()), n_strains


cocktails = {}
for tc in [0.50, 0.75, 0.90, 0.95, 0.99]:
    cock, n_cov, n_total = greedy_cover(mat, target_coverage=tc)
    cock_phage_ids = [mat.index[i] for i in cock]
    cock_names = [orgs.loc[orgs['id'] == p, 'full_name'].iloc[0] for p in cock_phage_ids]
    cocktails[f'{int(tc*100)}pct'] = {'n_phages': len(cock), 'phages': cock_names, 'coverage_pct': round(100*n_cov/n_total, 1)}
    log_section('3', f'\n≥{int(tc*100)}% strain coverage: {len(cock)} phages cover {n_cov}/{n_total} ({100*n_cov/n_total:.1f}%) strains')
    log_section('3', f'  cocktail: {cock_names[:8]}{"..." if len(cock_names) > 8 else ""}')


# ---------------------------------------------------------------------------
# §4. Cross-reference with HMP2 viromics
# ---------------------------------------------------------------------------
log_section('4', '## §4. Cross-reference: PhageFoundry phages vs HMP2 patient-stool observations')

fv = pd.read_parquet(f'{MART}/fact_viromics.snappy.parquet')
ecoli_fv = fv[fv['virus_name'].astype(str).str.contains('Escherichia phage', case=False, na=False)].copy()
hmp2_phages = sorted(ecoli_fv['virus_name'].dropna().unique())
log_section('4', f'\nUnique E. coli phages observed in HMP2 fact_viromics: {len(hmp2_phages)}')
log_section('4', f'  (each may appear in multiple samples)')
log_section('4', f'  HMP2 phage list: {hmp2_phages}')

# String-overlap match between PhageFoundry phage names and HMP2 phages
pf_phages = phage_range_df['phage_name'].tolist()
overlap = []
for hmp2_p in hmp2_phages:
    # Exact name match
    matches = [pf for pf in pf_phages if hmp2_p == pf or hmp2_p.split()[-1] in pf or pf.split()[-1] in hmp2_p]
    if matches:
        overlap.append({'hmp2_phage': hmp2_p, 'phagefoundry_match': matches[0]})

log_section('4', f'\nName-overlap matches (PhageFoundry × HMP2): {len(overlap)}')
for r in overlap:
    log_section('4', f'  HMP2: {r["hmp2_phage"]} ↔ PhageFoundry: {r["phagefoundry_match"]}')


# ---------------------------------------------------------------------------
# §5. Phage host-phylogroup distribution
# ---------------------------------------------------------------------------
log_section('5', '## §5. Phage host-phylogroup distribution')

phylo_counts = phage_range_df.groupby('Phage_host_phylo').agg(
    n_phages=('phage_id', 'count'),
    median_host_range=('host_range_pct', 'median'),
    max_host_range=('host_range_pct', 'max'),
).reset_index().sort_values('n_phages', ascending=False)
log_section('5', f'\nPhage host-phylogroup distribution:\n{phylo_counts.to_string(index=False)}')

# AIEC associations: AIEC is predominantly phylogroup B2 (~80% of AIEC isolates) and D (~20%) per Dogan 2014, Dubinsky 2022.
# Phylogroup A and B1 are mostly commensal E. coli.
log_section('5', f'\n**AIEC-relevant phages**: AIEC strains are predominantly phylogroup B2 (~80%) and D (~20%) per Dogan 2014/Dubinsky 2022.')
b2_d_phages = phage_range_df[phage_range_df['Phage_host_phylo'].isin(['B2', 'D'])]
log_section('5', f'  Phages isolated against B2 or D phylogroup hosts: {len(b2_d_phages)} of {len(phage_range_df)} ({100*len(b2_d_phages)/len(phage_range_df):.0f}%)')
log_section('5', f'  Top 10 broadest-host-range B2/D phages (potential AIEC-active):')
log_section('5', b2_d_phages.head(10)[['phage_name', 'host_range_pct', 'Family', 'Genus']].to_string(index=False))


# ---------------------------------------------------------------------------
# §6. Verdict + figure
# ---------------------------------------------------------------------------
log_section('6', '## §6. Verdict + figure')

verdict = {
    'date': '2026-04-25',
    'plan_version': 'v1.9',
    'test': 'NB13 — PhageFoundry quantitative E. coli phage-cocktail design',
    'n_phages': n_phages,
    'n_strains': n_strains,
    'n_interactions_tested': int(len(ph)),
    'n_susceptible': int(ph['value'].sum()),
    'n_resistant': int((ph['value']==0).sum()),
    'mean_host_range_pct': round(float(phage_range_df['host_range_pct'].mean()), 1),
    'median_host_range_pct': round(float(phage_range_df['host_range_pct'].median()), 1),
    'max_host_range_pct': round(float(phage_range_df['host_range_pct'].max()), 1),
    'n_broad_host_range_phages': int((phage_range_df['host_range_pct'] >= 30).sum()),
    'n_resistant_strains_le_5pct': int((strain_susc_df['phage_susceptibility_pct'] <= 5).sum()),
    'cocktail_designs': cocktails,
    'n_b2_d_phylogroup_phages': int(len(b2_d_phages)),
    'n_phages_observed_in_hmp2_viromics': len(overlap),
    'hmp2_phagefoundry_overlaps': overlap,
    'narrative': (
        f'PhageFoundry has 17,672 experimentally-tested phage × E. coli strain pairs ({int(ph["value"].sum())}/{len(ph)} = '
        f'{100*ph["value"].sum()/len(ph):.0f}% susceptibility). Mean host range per phage: '
        f'{phage_range_df["host_range_pct"].mean():.1f}%; max {phage_range_df["host_range_pct"].max():.1f}%. '
        f'Greedy minimum-set-cover gives a {cocktails["95pct"]["n_phages"]}-phage cocktail covering ≥95% of 188 strains. '
        f'{len(b2_d_phages)} of {len(phage_range_df)} phages were isolated against B2/D phylogroup hosts (AIEC-relevant '
        f'per Dogan 2014/Dubinsky 2022).'
    ),
}
with open(f'{OUT_DATA}/nb13_phagefoundry_cocktail_verdict.json', 'w') as fp:
    json.dump(verdict, fp, indent=2, default=str)
log_section('6', json.dumps(verdict, indent=2, default=str)[:3000])


# ---------------------------------------------------------------------------
# §7. Figure
# ---------------------------------------------------------------------------
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

fig, axes = plt.subplots(1, 3, figsize=(20, 6))

# Panel A: phage host-range distribution histogram + broad-host-range threshold
ax = axes[0]
ax.hist(phage_range_df['host_range_pct'], bins=20, color='#2a9d8f', edgecolor='black')
ax.axvline(30, color='red', linestyle='--', linewidth=1, label='30% (broad)')
ax.axvline(50, color='darkred', linestyle='--', linewidth=1, label='50% (very broad)')
ax.set_xlabel('Host range (% of 188 E. coli strains lysed)')
ax.set_ylabel('# phages')
ax.set_title(f'A. Per-phage host-range distribution (n=96 phages)\nmean={phage_range_df["host_range_pct"].mean():.0f}%, max={phage_range_df["host_range_pct"].max():.0f}%')
ax.legend()

# Panel B: per-strain susceptibility distribution
ax = axes[1]
ax.hist(strain_susc_df['phage_susceptibility_pct'], bins=20, color='#e76f51', edgecolor='black')
ax.axvline(5, color='red', linestyle='--', linewidth=1, label='5% (resistant)')
ax.set_xlabel('Phage susceptibility (% of 96 phages that lyse)')
ax.set_ylabel('# strains')
ax.set_title(f'B. Per-strain susceptibility distribution (n=188 strains)\nmedian={strain_susc_df["phage_susceptibility_pct"].median():.0f}%, # resistant ≤5%: {(strain_susc_df["phage_susceptibility_pct"]<=5).sum()}')
ax.legend()

# Panel C: cocktail size vs coverage curve
ax = axes[2]
M = mat.fillna(0).astype(int).values
n_phages_full, n_strains_full = M.shape
covered = np.zeros(n_strains_full, dtype=bool)
coverage_curve = [0.0]
sizes = [0]
M_remaining = M.copy()
selected = set()
for _ in range(min(50, n_phages_full)):
    coverage_gain = M_remaining[:, ~covered].sum(axis=1)
    # Set already-selected phages to 0
    for s in selected:
        coverage_gain[s] = 0
    if coverage_gain.max() == 0:
        break
    best = int(coverage_gain.argmax())
    selected.add(best)
    covered |= (M[best] == 1)
    coverage_curve.append(100 * covered.sum() / n_strains_full)
    sizes.append(len(selected))
ax.plot(sizes, coverage_curve, '-o', color='#264653', markersize=4)
for thr in [50, 75, 90, 95, 99]:
    n_needed = next((s for s, c in zip(sizes, coverage_curve) if c >= thr), None)
    if n_needed:
        ax.axvline(n_needed, color='gray', linestyle=':', linewidth=0.5)
        ax.text(n_needed + 0.3, thr - 5, f'≥{thr}%: {n_needed} phages', fontsize=8)
ax.set_xlabel('# phages in cocktail (greedy minimum-set-cover)')
ax.set_ylabel('% of 188 E. coli strains covered')
ax.set_title('C. Cocktail size × coverage curve')
ax.set_ylim(0, 102)
ax.grid(True, alpha=0.3)

fig.suptitle(f'NB13 — PhageFoundry quantitative E. coli phage-cocktail design ({n_phages} phages × {n_strains} strains × {len(ph):,} interactions)', fontsize=12, y=1.0)
fig.tight_layout()
fig.savefig(f'{OUT_FIG}/NB13_phagefoundry_cocktail.png', dpi=120, bbox_inches='tight')
log_section('6', f'\nWrote {OUT_FIG}/NB13_phagefoundry_cocktail.png')

with open('/tmp/nb13_section_logs.json', 'w') as fp:
    json.dump(SECTION_LOGS, fp, indent=2)
print(f'\nDone.')

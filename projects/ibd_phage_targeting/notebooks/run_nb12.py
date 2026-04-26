"""NB12 — Pathobiont × phage targetability matrix (Pillar 4 opener).

Build a per-pathobiont phage-targetability profile combining:
1. ref_phage_biology curated literature synthesis (12 organisms; from
   indicator_taxa_literature_review)
2. NB05 actionable Tier-A scoring (6 species)
3. Pillar 3 per-target mechanism profile (iron / bile-acid / mediation)

Output:
- Per-target Tier-B (phage availability) score: 0=no known phages, 1=temperate
  only, 2=lytic literature mentions, 3=clinical trial / commercial cocktail
- Per-target combined Tier-A × Tier-B × bile-acid-coupling-cost score
- Coverage gap analysis: which actionable Tier-A core have NO phage options?

External phage DB queries (PhageFoundry, INPHARED, IMG/VR, NCBI Phage RefSeq,
PhagesDB) flagged for follow-up — BERDL Spark auth currently blocks
PhageFoundry direct query; ref_phage_biology + external-DB literature
references are the operational data scope for this notebook.

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
# §0. Load inputs
# ---------------------------------------------------------------------------
log_section('0', '## §0. Load ref_phage_biology + NB05 Tier-A scoring + Pillar-3 mechanism profile')

pb = pd.read_parquet(f'{MART}/ref_phage_biology.snappy.parquet')
log_section('0', f'ref_phage_biology: {pb.shape[0]} organisms × {pb.shape[1]} columns')
log_section('0', f'  Tier breakdown: {pb["tier"].value_counts().to_dict()}')

nb05 = pd.read_csv(f'{OUT_DATA}/nb05_tier_a_scored.tsv', sep='\t')
nb05_actionable = nb05[nb05['actionable']]
log_section('0', f'\nNB05 actionable Tier-A core: {len(nb05_actionable)} species')
for _, r in nb05_actionable.iterrows():
    log_section('0', f'  {r["species"]}: total_score={r["total_score"]}')

# Tier-B candidates (Tier-A scored but not actionable, top-scoring)
nb05_tierb = nb05[(~nb05['actionable']) & (nb05['total_score'] >= 2.2)].head(9)
log_section('0', f'\nNB05 Tier-B candidates (score 2.2-2.4):')
for _, r in nb05_tierb.iterrows():
    log_section('0', f'  {r["species"]}: total_score={r["total_score"]}')


# ---------------------------------------------------------------------------
# §1. Per-pathobiont phage-availability scoring
# ---------------------------------------------------------------------------
log_section('1', '## §1. Per-pathobiont phage-availability score')

# Curated synonymy: NB05 actionable Tier-A → ref_phage_biology organism column
SYNONYMY = {
    'Hungatella hathewayi': 'Hungatella hathewayi',
    'Mediterraneibacter gnavus': 'Ruminococcus gnavus',
    'Escherichia coli': 'Escherichia coli (AIEC)',
    'Eggerthella lenta': 'Eggerthella lenta',
    'Flavonifractor plautii': None,  # NOT in ref_phage_biology
    'Enterocloster bolteae': 'Enterocloster bolteae',
}

# Phage-availability score logic:
# 0 = no known phages OR only historical phage-like particles
# 1 = temperate / prophage only, or limited characterization
# 2 = lytic phage(s) characterized in literature, but not in clinical trials
# 3 = clinical trial / commercial cocktail OR published efficacy data
PHAGE_SCORES = {
    # Tier 1
    'Ruminococcus gnavus': (1, 'temperate', '6 temperate siphovirus phages (36.5–37.8 kb); co-exist with host in vivo. Phage therapy LIMITED by temperate lifecycle.'),
    'Enterocloster bolteae': (2, 'lytic', 'PMBT24 phage (virulent; 99,962 bp dsDNA; Kielviridae); inovirus prophages. Lytic phage available; not yet in clinical trials.'),
    'Escherichia coli (AIEC)': (3, 'lytic_clinical', 'EcoActive cocktail (7 lytic phages, clinical trials); vB_EcoA_PHZVL (Autographiviridae); HER259 (attenuates virulence). Most advanced phage-therapy candidate.'),
    '[Clostridium] innocuum': (1, 'temperate_only', 'Phage protein gp37 and holin genes in core genome; no isolated lytic phages.'),
    'Eggerthella lenta': (2, 'lytic', 'PMBT5 siphovirus (30,930 bp; 44 ORFs); extensive prophage diversity (5.8% of pangenome; 10+ clades).'),
    '[Clostridium] scindens': (1, 'lysin_only', 'Phage phiMMP01 endolysin (CWH) can lyse some strains. PRESERVE — not target.'),
    # Tier 2
    'Enterocloster asparagiformis': (1, 'temperate_only', 'Inovirus genes in 6/7 Enterocloster strains; 15 prophages (4 intact); no isolated lytic.'),
    'Klebsiella oxytoca': (2, 'lytic', 'vB_Kox_ZX8 (Przondovirus; burst 74 PFU; pH 3-11 stable; 100% survival in bacteremia model); vB8388 (synergistic with gentamicin).'),
    'Clostridioides difficile': (1, 'temperate_only_in_dev', 'ALL known phages are temperate (lysogenic); CRISPR-Cas3 antimicrobials in development.'),
    'Ruminococcus torques': (1, 'limited', 'Phage 1706 (genome homology); minimal phage characterization.'),
    'Hungatella hathewayi': (0, 'none', 'No specific phages identified; historical phage-like particles but no plaques. CRITICAL COVERAGE GAP.'),
    '[Clostridium] symbiosum': (0, 'none', 'Historical phage-like particles; modern phage literature minimal. CRITICAL COVERAGE GAP.'),
}

phage_rows = []
for _, r in nb05.iterrows():
    species = r['species']
    nb05_score = r['total_score']
    actionable = r['actionable']
    pb_organism = SYNONYMY.get(species)
    if pb_organism and pb_organism in PHAGE_SCORES:
        phage_score, lifestyle, phage_notes = PHAGE_SCORES[pb_organism]
    elif species in PHAGE_SCORES:
        phage_score, lifestyle, phage_notes = PHAGE_SCORES[species]
    else:
        # Not in ref_phage_biology — assume no curated phage info (score 0; needs literature follow-up)
        phage_score, lifestyle, phage_notes = (np.nan, 'unknown_not_in_ref_phage_biology', 'NOT IN ref_phage_biology — requires external phage DB query (INPHARED / IMG/VR / NCBI Phage RefSeq / PhagesDB)')
    phage_rows.append({
        'species': species,
        'tier_a_score_nb05': nb05_score,
        'actionable_tier_a': actionable,
        'phage_score_tier_b': phage_score,
        'lifestyle_dominant': lifestyle,
        'phage_notes': phage_notes,
        'in_ref_phage_biology': pb_organism is not None and pb_organism in PHAGE_SCORES,
    })

# Sort by tier_a_score, then by actionable flag
phage_df = pd.DataFrame(phage_rows).sort_values(['actionable_tier_a', 'tier_a_score_nb05'], ascending=[False, False])

log_section('1', f'\nPhage-availability scoring (top 20 by Tier-A score):')
log_section('1', phage_df.head(20)[['species', 'tier_a_score_nb05', 'actionable_tier_a', 'phage_score_tier_b', 'lifestyle_dominant']].to_string(index=False))


# ---------------------------------------------------------------------------
# §2. Combined Tier-A × Tier-B × Pillar-3 mechanism profile (per-target priority)
# ---------------------------------------------------------------------------
log_section('2', '## §2. Combined per-target priority for Pillar-5 cocktail design')

# Pillar-3 per-target mechanism profile (from REPORT §closure cocktail-design table)
PILLAR3_PROFILE = {
    'Hungatella hathewayi': {
        'iron_specialization': 'none',
        'ba_coupling_cost': 'low',
        'mediation': 'species-abundance + within-carrier-metabolic-shift',
        'pillar5_class': 'Tier-1 phage target (highest NB05 score; low BA cost)',
    },
    'Mediterraneibacter gnavus': {
        'iron_specialization': 'none',
        'ba_coupling_cost': 'low',
        'mediation': 'species-abundance (mucin-glucorhamnan; Henke 2019)',
        'pillar5_class': 'Tier-1 phage target (low BA cost; mucin mechanism)',
    },
    'Escherichia coli': {
        'iron_specialization': 'dominant (Yersiniabactin/Enterobactin/Colibactin)',
        'ba_coupling_cost': 'low',
        'mediation': 'strain-content (AIEC subset specific)',
        'pillar5_class': 'Tier-1 phage target with strain-resolution requirement',
    },
    'Flavonifractor plautii': {
        'iron_specialization': 'weak',
        'ba_coupling_cost': 'HIGHEST (active 7α-dehydroxylator)',
        'mediation': 'species-abundance (NB10a F. plautii informative null)',
        'pillar5_class': 'Tier-2 phage target with HIGHEST BA-coupling cost — depletion shifts BA pool toward primary tauro-conjugated forms; consider co-administering UDCA / BA-binding agent',
    },
    'Enterocloster bolteae': {
        'iron_specialization': 'none',
        'ba_coupling_cost': 'moderate (active 7α-dehydroxylator, NB09c × deoxycholate=+0.17)',
        'mediation': 'mixed',
        'pillar5_class': 'Tier-2 phage target (moderate BA cost)',
    },
    'Eggerthella lenta': {
        'iron_specialization': 'none',
        'ba_coupling_cost': 'moderate (partial 7α-dehydroxylator)',
        'mediation': 'drug-metabolism (Koppel 2018 Cgr2)',
        'pillar5_class': 'Tier-2 phage target (moderate BA cost; non-BGC drug-metabolism mechanism)',
    },
}


def combined_priority(row):
    """Combine NB05 Tier-A score + phage availability + Pillar-3 BA-cost into a per-target priority class."""
    species = row['species']
    score_a = row['tier_a_score_nb05']
    score_b = row['phage_score_tier_b']
    actionable = row['actionable_tier_a']
    if pd.isna(score_b):
        return 'GAP — needs external DB query'
    if not actionable:
        return f'Tier-B sub-threshold (NB05 {score_a:.1f}; phage {score_b})'
    profile = PILLAR3_PROFILE.get(species, {})
    cls = profile.get('pillar5_class', 'unclassified')
    return f'{cls} | phage_score={score_b}'


phage_df['pillar5_class_combined'] = phage_df.apply(combined_priority, axis=1)

actionable_combined = phage_df[phage_df['actionable_tier_a']].copy()
log_section('2', f'\nCombined per-actionable-target priority (NB05 actionable Tier-A only):')
for _, r in actionable_combined.iterrows():
    log_section('2', f'  {r["species"]:<35s} | NB05={r["tier_a_score_nb05"]:.1f} | phage={int(r["phage_score_tier_b"]) if pd.notna(r["phage_score_tier_b"]) else "?"} | {r["lifestyle_dominant"]}')
    profile = PILLAR3_PROFILE.get(r['species'], {})
    if profile:
        log_section('2', f'    iron: {profile["iron_specialization"]}; BA-cost: {profile["ba_coupling_cost"]}; mediation: {profile["mediation"]}')
        log_section('2', f'    Pillar-5 class: {profile["pillar5_class"]}')
    log_section('2', '')


# ---------------------------------------------------------------------------
# §3. Coverage gap analysis
# ---------------------------------------------------------------------------
log_section('3', '## §3. Coverage gap analysis')

gaps = phage_df[(phage_df['phage_score_tier_b'] == 0) | phage_df['phage_score_tier_b'].isna()]
log_section('3', f'\nPathobionts with phage_score = 0 or unknown (no actionable phage options in current scope):')
for _, r in gaps.iterrows():
    actionable_tag = ' [ACTIONABLE]' if r['actionable_tier_a'] else ''
    log_section('3', f'  {r["species"]:<35s}{actionable_tag} (NB05={r["tier_a_score_nb05"]:.1f})')

n_actionable_gap = ((phage_df['actionable_tier_a']) & ((phage_df['phage_score_tier_b'] == 0) | phage_df['phage_score_tier_b'].isna())).sum()
log_section('3', f'\n# actionable Tier-A core with phage coverage gap: {n_actionable_gap}')

# Specific gap analysis
log_section('3', '\n### Specific gaps in actionable Tier-A core:')
log_section('3', '\n- ***F. plautii***: NOT in ref_phage_biology curated set; literature search required (INPHARED / IMG/VR / NCBI Phage RefSeq / PhagesDB). Tier-2 priority for Pillar-5 cocktail design due to HIGH BA-coupling cost; the bile-acid-cost annotation is more important than phage availability for this species — first decision is whether to target F. plautii at all (BA pool consequence) before phage selection.')
log_section('3', '\n- ***H. hathewayi***: ref_phage_biology entry says "No specific phages identified; historical phage-like particles but no plaques" — CRITICAL COVERAGE GAP for the highest-NB05-scored Tier-A. External DB query required: search INPHARED / IMG/VR for any Hungatella-host phages. Also possible: target the GAG-degrading enzyme directly (per ref_phage_biology therapeutic_targets) rather than via phage.')
log_section('3', '\n- ***M. gnavus*** (= R. gnavus): all 6 known phages are TEMPERATE — phage therapy is structurally limited because temperate phages can confer host fitness benefits (lysogeny) rather than reliably lyse. Therapeutic strategies: (a) engineer lytic-locked variants of the temperate phages; (b) target glucorhamnan synthesis biochemically (per ref_phage_biology therapeutic_targets) rather than via phage.')


# ---------------------------------------------------------------------------
# §4. External phage DB references for follow-up
# ---------------------------------------------------------------------------
log_section('4', '## §4. External phage DB references (out-of-BERDL — Pillar 4 follow-up)')

EXTERNAL_DBS = [
    {
        'name': 'PhageFoundry (BERDL)',
        'access': 'BERDL Spark Connect — phagefoundry_strain_modelling, phagefoundry_ecoliphages_genomedepot, phagefoundry_klebsiella_*, phagefoundry_acinetobacter_*, phagefoundry_paeruginosa_*, phagefoundry_pviridiflava_*',
        'coverage_to_tier_a': 'E. coli direct (phagefoundry_ecoliphages_genomedepot); K. oxytoca direct (phagefoundry_klebsiella_*). Other Tier-A core (gut commensal hosts) not directly covered by current PhageFoundry collections.',
        'status': 'BLOCKED at NB12 execution: BERDL auth token in .env stale (KBASE_AUTH_TOKEN reports invalid). Refresh token + re-query as Pillar-4 follow-up.',
    },
    {
        'name': 'Millard lab INPHARED',
        'access': 'http://millardlab.org/phages/inphared/ (downloadable phage genome annotations + host predictions)',
        'coverage_to_tier_a': 'Comprehensive — ~25K phage genomes with GenBank-quality annotations. Host predictions via BLAST + phylogenetic placement. Best single source for phage availability across all Tier-A pathobionts.',
        'status': 'Out-of-BERDL — manual download + parse required. Promote to NB12-followup for the 3 actionable Tier-A coverage gaps (F. plautii, H. hathewayi, R. gnavus lytic alternatives).',
    },
    {
        'name': 'IMG/VR v4',
        'access': 'https://genome.jgi.doe.gov/portal/IMG_VR/IMG_VR.home.html (~3M uncultivated viral genomes from metagenomes, with host predictions via CRISPR spacer matches and BLAST)',
        'coverage_to_tier_a': 'Strongest for uncultivated phages of gut-anaerobe hosts where culturing-based isolation has failed (H. hathewayi, F. plautii). UViGs in IMG/VR may include phages with CRISPR-spacer-derived host predictions.',
        'status': 'Out-of-BERDL — JGI Portal API or direct download. Promote to NB12-followup.',
    },
    {
        'name': 'NCBI Phage Virus RefSeq',
        'access': 'NCBI Virus / RefSeq Viral; ~5K curated phage reference genomes',
        'coverage_to_tier_a': 'Curated subset — covers well-studied phages (E. coli, Klebsiella, Salmonella, Pseudomonas) but limited gut-anaerobe coverage.',
        'status': 'Out-of-BERDL — straightforward NCBI E-utils query.',
    },
    {
        'name': 'PhagesDB',
        'access': 'https://phagesdb.org/ (Mycobacterium-phage focused; ~25K isolated phages)',
        'coverage_to_tier_a': 'Mostly mycobacteriophages; not directly relevant for IBD pathobionts.',
        'status': 'Low priority for this project.',
    },
]

for d in EXTERNAL_DBS:
    log_section('4', f'\n- **{d["name"]}**')
    log_section('4', f'  Access: {d["access"]}')
    log_section('4', f'  Coverage: {d["coverage_to_tier_a"]}')
    log_section('4', f'  Status: {d["status"]}')


# ---------------------------------------------------------------------------
# §5. Save outputs + verdict
# ---------------------------------------------------------------------------
log_section('5', '## §5. Save outputs + verdict')

phage_df.to_csv(f'{OUT_DATA}/nb12_phage_targetability_matrix.tsv', sep='\t', index=False)

# Verdict
n_actionable = len(actionable_combined)
n_phage_score_3 = (actionable_combined['phage_score_tier_b'] == 3).sum()
n_phage_score_2 = (actionable_combined['phage_score_tier_b'] == 2).sum()
n_phage_score_1 = (actionable_combined['phage_score_tier_b'] == 1).sum()
n_phage_score_0 = (actionable_combined['phage_score_tier_b'] == 0).sum()

verdict = {
    'date': '2026-04-25',
    'plan_version': 'v1.9',
    'test': 'NB12 — Pathobiont × phage targetability matrix (Pillar 4 opener)',
    'n_actionable_tier_a': int(n_actionable),
    'n_phage_score_3_clinical': int(n_phage_score_3),
    'n_phage_score_2_lytic_literature': int(n_phage_score_2),
    'n_phage_score_1_temperate_or_limited': int(n_phage_score_1),
    'n_phage_score_0_gap': int(n_phage_score_0),
    'phage_clinical_tier_a': sorted(actionable_combined.loc[actionable_combined['phage_score_tier_b']==3, 'species'].tolist()),
    'phage_lytic_literature_tier_a': sorted(actionable_combined.loc[actionable_combined['phage_score_tier_b']==2, 'species'].tolist()),
    'phage_limited_tier_a': sorted(actionable_combined.loc[actionable_combined['phage_score_tier_b']==1, 'species'].tolist()),
    'phage_gap_tier_a': sorted(actionable_combined.loc[(actionable_combined['phage_score_tier_b']==0) | actionable_combined['phage_score_tier_b'].isna(), 'species'].tolist()),
    'pillar4_pillar5_handoff_note': (
        'Phage availability stratifies the 6 actionable Tier-A core into 4 classes: clinical-trial-stage (E. coli AIEC); '
        'lytic-literature (E. lenta, E. bolteae); temperate-limited (M. gnavus); coverage-gap (H. hathewayi, F. plautii). '
        'The 2 coverage-gap targets are the highest-NB05-scored species and require external phage DB queries (INPHARED + IMG/VR) '
        'as Pillar-4 follow-up. F. plautii additionally carries the highest BA-coupling cost — phage targeting may be deprioritized '
        'in favor of bile-acid-pool monitoring or biochemical-target alternatives. M. gnavus temperate-only constraint may require '
        'either lytic-locked phage engineering or biochemical glucorhamnan-synthesis targeting.'
    ),
    'limitations': [
        'BERDL Spark auth blocked at NB12 execution (KBASE_AUTH_TOKEN stale); PhageFoundry collections not directly queried. Refresh token + cross-check ref_phage_biology curated synthesis as a Pillar-4 follow-up.',
        'External phage DB queries (INPHARED / IMG/VR / NCBI Phage RefSeq) are out-of-BERDL and not run in NB12. Coverage gaps for F. plautii / H. hathewayi specifically require these queries.',
        'ref_phage_biology has 12 organisms — F. plautii is NOT in the curated set (only 5 of 6 actionable Tier-A core covered).',
        'Phage-availability scoring is qualitative (0-3 ordinal scale based on lifestyle + clinical status) — quantitative coverage metrics (n_phages, host-range CDS, receptor-binding-domain diversity) require PhageFoundry / INPHARED genomic data.',
    ],
}
with open(f'{OUT_DATA}/nb12_phage_targetability_verdict.json', 'w') as fp:
    json.dump(verdict, fp, indent=2, default=str)
log_section('5', json.dumps(verdict, indent=2, default=str))


# ---------------------------------------------------------------------------
# §6. Figure
# ---------------------------------------------------------------------------
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 2, figsize=(15, 7))

# Panel A: NB05 Tier-A score vs phage-availability score (per-actionable + per-Tier-B)
ax = axes[0]
to_plot = phage_df.dropna(subset=['phage_score_tier_b']).copy()
to_plot['size'] = to_plot['actionable_tier_a'].map({True: 200, False: 80})
to_plot['color'] = to_plot['actionable_tier_a'].map({True: '#e63946', False: '#73c0e8'})
ax.scatter(to_plot['tier_a_score_nb05'], to_plot['phage_score_tier_b'],
           c=to_plot['color'], s=to_plot['size'], alpha=0.7, edgecolors='black', linewidth=0.5)
# Annotate actionable Tier-A core
for _, r in to_plot[to_plot['actionable_tier_a']].iterrows():
    nm = r['species']
    short = nm.split()[1][:8] + ' ' + nm.split()[0][:1] + '.'
    ax.annotate(short, (r['tier_a_score_nb05'], r['phage_score_tier_b']),
                fontsize=8, alpha=0.9, xytext=(5, 5), textcoords='offset points', fontweight='bold')
ax.set_xlabel('NB05 Tier-A score (criteria A3-A6)')
ax.set_ylabel('Phage-availability score (Tier-B)\n0=no phages, 1=temperate, 2=lytic literature, 3=clinical trial')
ax.set_title('A. Per-pathobiont Tier-A × Tier-B phage targetability')
ax.set_yticks([0, 1, 2, 3])
ax.set_yticklabels(['0: no phages', '1: temperate / limited', '2: lytic literature', '3: clinical trial'])
ax.grid(True, alpha=0.3)
ax.axhline(2, color='gray', linestyle=':', linewidth=0.5, label='lytic threshold')
ax.axvline(2.5, color='gray', linestyle=':', linewidth=0.5, label='actionable threshold')

# Panel B: Pillar-5 cocktail-design priority class — categorical view
ax = axes[1]
labels = []
heights = []
colors = []
for _, r in actionable_combined.sort_values('tier_a_score_nb05', ascending=True).iterrows():
    species = r['species']
    score_b = int(r['phage_score_tier_b']) if pd.notna(r['phage_score_tier_b']) else 0
    profile = PILLAR3_PROFILE.get(species, {})
    short = species.split()[1][:8] + ' ' + species.split()[0][:1] + '.'
    labels.append(f'{short}\n(NB05={r["tier_a_score_nb05"]:.1f}; phage={score_b})\nBA={profile.get("ba_coupling_cost", "?")[:8]}')
    heights.append(r['tier_a_score_nb05'])
    # Color by phage_score
    color_map = {0: '#e63946', 1: '#f4a261', 2: '#e9c46a', 3: '#2a9d8f'}
    colors.append(color_map.get(score_b, '#a8a8a8'))

y = np.arange(len(labels))
ax.barh(y, heights, color=colors)
ax.set_yticks(y)
ax.set_yticklabels(labels, fontsize=8)
ax.set_xlabel('NB05 Tier-A score')
ax.set_title('B. Per-actionable-Tier-A Pillar-5 priority\n(color = phage-availability score)')

# Legend
from matplotlib.patches import Patch
legend_elems = [
    Patch(facecolor='#2a9d8f', label='3: clinical trial (E. coli AIEC EcoActive)'),
    Patch(facecolor='#e9c46a', label='2: lytic literature (E. bolteae PMBT24, E. lenta PMBT5)'),
    Patch(facecolor='#f4a261', label='1: temperate / limited (M. gnavus 6 temperate phages)'),
    Patch(facecolor='#e63946', label='0: GAP (H. hathewayi: no phages; F. plautii: not in ref)'),
]
ax.legend(handles=legend_elems, loc='lower right', fontsize=7)

fig.suptitle('NB12 — Pillar-4 opener: pathobiont × phage targetability matrix', fontsize=12, y=1.0)
fig.tight_layout()
fig.savefig(f'{OUT_FIG}/NB12_phage_targetability.png', dpi=120, bbox_inches='tight')
log_section('5', f'\nWrote {OUT_FIG}/NB12_phage_targetability.png')

with open('/tmp/nb12_section_logs.json', 'w') as fp:
    json.dump(SECTION_LOGS, fp, indent=2)
print(f'\nDone.')

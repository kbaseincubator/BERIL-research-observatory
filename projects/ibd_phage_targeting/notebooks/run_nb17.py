"""NB17 — Cross-cutting synthesis + clinical-translation roadmap (Pillar 5 closure capstone).

Three deliverables:
  1. Per-patient master table — one row per UC Davis patient with all per-pillar attributes
  2. Target decision matrix — 6 actionable Tier-A × 5 attributes → final cocktail-design priority class
  3. Synthesis figure — clinical-translation timeline + decision matrix heatmap + per-patient design-category distribution

Per plan v1.9 no-raw-reads. All inputs are precomputed mart artifacts.
"""
import json
import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJ = Path(__file__).parent.parent
DATA = PROJ / 'data'
FIG = PROJ / 'figures'

SECTION_LOGS: dict[str, str] = {}


def log(section: str, msg: str) -> None:
    print(msg)
    SECTION_LOGS[section] = SECTION_LOGS.get(section, '') + msg + '\n'


# ============================================================
# §1. Load upstream per-pillar artifacts
# ============================================================
log('1', '## §1. Load upstream per-pillar artifacts\n')

patient_profile = pd.read_csv(DATA / 'nb15_patient_profile.tsv', sep='\t')
log('1', f'  NB15 patient profile: {len(patient_profile)} patients × {patient_profile.shape[1]} attributes')

cocktail_draft = pd.read_csv(DATA / 'nb15_per_patient_cocktail_draft.tsv', sep='\t')
log('1', f'  NB15 cocktail draft (long): {len(cocktail_draft)} patient×target rows')

phage_matrix = pd.read_csv(DATA / 'nb12_phage_targetability_matrix.tsv', sep='\t')
log('1', f'  NB12 phage matrix: {len(phage_matrix)} species × {phage_matrix.shape[1]} attributes')

p6967_long = pd.read_csv(DATA / 'nb16_p6967_tier_a_longitudinal.tsv', sep='\t')
log('1', f'  NB16 patient 6967 longitudinal: {len(p6967_long)} Tier-A rows × 2 visits')

with open(DATA / 'nb16_longitudinal_verdict.json') as f:
    nb16_verdict = json.load(f)
log('1', f'  NB16 verdict: jaccard {nb16_verdict["patient_6967_cocktail_jaccard_visit1_visit2"]}; '
         f'M.gnavus FC {nb16_verdict["patient_6967_M_gnavus_fold_change_v2_v1"]}×; '
         f'1112 reseq ρ {nb16_verdict["patient_1112_tech_rep_spearman_rho"]}\n')


# ============================================================
# §2. Per-patient master table
# ============================================================
log('2', '## §2. Per-patient master table\n')

ACTIONABLE = ['H.hathew', 'M.gnavus', 'E.coli', 'E.lenta', 'F.plauti', 'E.boltea']
TIER_A_FULL = {'H.hathew': 'H. hathewayi', 'M.gnavus': 'M. gnavus', 'E.coli': 'E. coli',
               'E.lenta': 'E. lenta', 'F.plauti': 'F. plautii', 'E.boltea': 'E. bolteae'}


def design_category(row: pd.Series) -> str:
    """4-category Pillar 5 stratification per NB15 §3."""
    eco = str(row['final_ecotype'])  # stored as str: '0','1','3','mixed'
    calp = row.get('calpro_num')
    n_targets = int(row.get('n_actionable_targets') or 0)
    longitudinal = str(row['patient_id']) == '6967'
    if longitudinal or eco == 'mixed':
        return 'D_mixed_longitudinal'
    if pd.notna(calp) and calp >= 250:
        return 'A_active_many_targets' if n_targets >= 4 else 'B_active_few_targets'
    return 'C_quiescent'


def cocktail_strategy(row: pd.Series) -> str:
    """Map design-category × ecotype to recommended cocktail strategy (concrete)."""
    cat = row['design_category']
    eco = str(row['final_ecotype'])
    has_ecoli = bool(row.get('has_E.coli', 0))
    if cat == 'D_mixed_longitudinal':
        return 'state_dependent_dosing'
    if cat == 'C_quiescent':
        return 'reserve_for_flare'
    if eco == '0':
        return 'limited_E0_priority_targets_GAP'
    if eco == '1':
        return 'hybrid_3strategy_E1_full' if has_ecoli else 'hybrid_3strategy_E1_no_ecoli'
    if eco == '3':
        return 'focused_E3_with_ecoli' if has_ecoli else 'focused_E3_no_ecoli'
    return 'other'


master = patient_profile.copy()
master['design_category'] = master.apply(design_category, axis=1)
master['cocktail_strategy'] = master.apply(cocktail_strategy, axis=1)
master['longitudinal_status'] = master['patient_id'].astype(str).map(
    lambda p: 'E1->E3 drift; M.gnavus 14x; jaccard 0.60' if p == '6967'
    else 'reseq tech rep ρ=1.000' if p == '1112'
    else 'single timepoint'
)

# Concrete phage cocktail = E1 or E3 patient with at least one actionable Tier-A
# (E0 patients get "limited"/non-concrete; mixed-longitudinal goes to state-dependent dosing)
has_concrete = (master['final_ecotype'].astype(str).isin(['1', '3'])) & (master['n_actionable_targets'] >= 1)
master['concrete_phage_cocktail'] = has_concrete

cols = ['patient_id', 'final_ecotype', 'median_primary_conf', 'calpro_num', 'Montreal Classification',
        'Medication', 'n_actionable_targets', 'has_H.hathew', 'has_M.gnavus', 'has_E.coli',
        'has_E.lenta', 'has_F.plauti', 'has_E.boltea',
        'design_category', 'cocktail_strategy', 'longitudinal_status', 'concrete_phage_cocktail']
master_out = master[cols].copy()

master_out.to_csv(DATA / 'nb17_patient_master_table.tsv', sep='\t', index=False)
log('2', f'  Per-patient master table written: {DATA / "nb17_patient_master_table.tsv"}')

cat_counts = master['design_category'].value_counts().to_dict()
log('2', f'  Design-category distribution: {cat_counts}')

strat_counts = master['cocktail_strategy'].value_counts().to_dict()
log('2', f'  Cocktail-strategy distribution: {strat_counts}')

n_concrete = int(master['concrete_phage_cocktail'].sum())
log('2', f'  Patients with concrete phage cocktail draft: {n_concrete}/{len(master)}\n')


# ============================================================
# §3. Target decision matrix (6 actionable × 5 attributes)
# ============================================================
log('3', '## §3. Target decision matrix\n')

# Hard-code the multi-attribute profile from upstream notebooks (NB05 + NB06 + NB09c + NB10a + NB12)
# as specified in REPORT.md "Pillar 4 → Pillar 5 hand-off" table.
TARGET_PROFILE = {
    'H. hathewayi': dict(
        nb05_score=4.0,
        ecotype_module='E1+E3 (both)',
        ba_coupling_cost='none',
        mediation='species-abundance + within-carrier metabolic shift',
        phage_tier='GAP',
        prevalence_pct=83,
        priority_class='Tier-1 phage GAP — INPHARED/IMG-VR query priority',
    ),
    'M. gnavus': dict(
        nb05_score=3.8,
        ecotype_module='E1+E3 (both)',
        ba_coupling_cost='none',
        mediation='species-abundance (mucin-glucorhamnan; Henke 2019)',
        phage_tier='temperate-only',
        prevalence_pct=91,
        priority_class='Tier-1 limited — lytic-locked engineering OR biochemical glucorhamnan target',
    ),
    'E. coli': dict(
        nb05_score=3.6,
        ecotype_module='E3-specific',
        ba_coupling_cost='none',
        mediation='strain-content (AIEC subset; pks/Yersiniabactin/Enterobactin)',
        phage_tier='clinical-trial',
        prevalence_pct=35,
        priority_class='Tier-1 phage with strain-resolution — NB13 5-phage cocktail; AIEC diagnostic required',
    ),
    'E. lenta': dict(
        nb05_score=3.3,
        ecotype_module='E1+E3 (both; universal Tier-1)',
        ba_coupling_cost='moderate (partial 7α-dehydroxylator)',
        mediation='drug-metabolism (Koppel 2018 Cgr2)',
        phage_tier='lytic-literature (PMBT5)',
        prevalence_pct=70,
        priority_class='Tier-2 phage — PMBT5 with BA monitoring',
    ),
    'F. plautii': dict(
        nb05_score=3.3,
        ecotype_module='E1-specific',
        ba_coupling_cost='HIGHEST (active 7α-dehydroxylator; F420)',
        mediation='species-abundance (F. plautii informative null in Kumbhari)',
        phage_tier='GAP',
        prevalence_pct=78,
        priority_class='Tier-2 deprioritize — triple penalty (GAP + highest BA-cost + E1-only); UDCA/BA-binding co-therapy',
    ),
    'E. bolteae': dict(
        nb05_score=2.8,
        ecotype_module='E1+E3 (both)',
        ba_coupling_cost='moderate (active 7α-dehydroxylator)',
        mediation='mixed',
        phage_tier='lytic-literature (PMBT24)',
        prevalence_pct=83,
        priority_class='Tier-2 phage — PMBT24 with BA monitoring',
    ),
}

decision = pd.DataFrame.from_dict(TARGET_PROFILE, orient='index').reset_index().rename(
    columns={'index': 'species'})
decision.to_csv(DATA / 'nb17_target_decision_matrix.tsv', sep='\t', index=False)
log('3', f'  Target decision matrix written: {DATA / "nb17_target_decision_matrix.tsv"}')
log('3', f'  Decision matrix:\n{decision[["species","nb05_score","phage_tier","ba_coupling_cost","priority_class"]].to_string(index=False)}\n')


# ============================================================
# §4. Final per-pillar verdict + Novel Contributions one-line index
# ============================================================
log('4', '## §4. Final per-pillar verdict + Novel Contributions\n')

PILLAR_VERDICTS = {
    'Pillar 1 — Patient stratification': {
        'verdict': 'CLOSED',
        'key_finding': 'Four reproducible IBD ecotypes (E0/E1/E2/E3) on 8.5K cMD samples; HMP2 external-replication χ² p=0.016; UC Davis distributes E0 27% / E1 42% / E3 31% / E2 0% (χ² p=0.019)',
        'notebooks': 'NB00, NB01, NB01b, NB02, NB03',
    },
    'Pillar 2 — Pathobiont identification': {
        'verdict': 'CLOSED',
        'key_finding': 'Within-ecotype × within-substudy meta-analysis yields 51 E1 + 40 E3 Tier-A candidates; NB05 6 actionable Tier-A core; NB06 H2d 5/6 actionable in single per-subnet pathobiont module; HMP2 88.2% E1 sign-concordance external replication',
        'notebooks': 'NB04, NB04b, NB04c, NB04d, NB04e, NB04f, NB04g, NB04h, NB05, NB06',
    },
    'Pillar 3 — Functional drivers': {
        'verdict': 'CLOSED',
        'key_finding': '8 H3 sub-hypotheses tested (5 SUPPORTED + 1 PARTIALLY + 2 PARTIAL + 1 NOT); 2 cross-corroborated 6-line mechanism narratives (iron + bile-acid); NB07d CC1 r=0.96 collapses all narratives into single joint axis (cliff δ=+0.50, p=4e-4)',
        'notebooks': 'NB07a, NB07b, NB07_v18, NB07c, NB07d, NB08a, NB09a, NB09b, NB09c, NB09d, NB10a, NB11',
    },
    'Pillar 4 — Phage targetability': {
        'verdict': 'CLOSED',
        'key_finding': '3-layer phage-evidence convergence (literature + experimental + in-vivo); 5-phage E. coli AIEC cocktail at 94.7% strain coverage (PhageFoundry 17,672 pairs); H. hathewayi + F. plautii GAP confirmed across all 3 layers',
        'notebooks': 'NB12, NB13, NB14',
    },
    'Pillar 5 — UC Davis per-patient cocktail design': {
        'verdict': 'SUBSTANTIALLY CLOSED',
        'key_finding': '14 of 23 patients (61%) with concrete cocktail drafts; pure phage cocktail structurally infeasible for E1 (3-strategy hybrid required); F. plautii BA-cost dominant E1 design constraint; patient 6967 E1→E3 drift validates state-dependent dosing rule (M. gnavus 14× expansion); patient 1112 reseq ρ=1.000 validates Kaiju reliability; 5 dosing rules + clinical-translation workflow',
        'notebooks': 'NB15, NB16, NB17',
    },
}

NC_INDEX = [
    (1, 'Cross-method ARI as K-selection criterion when per-method fit is monotonic', 'NB01b'),
    (2, 'OvR-AUC vs per-patient agreement gap as classifier-utility diagnostic', 'NB03'),
    (3, 'Kaiju ↔ MetaPhlAn3 projection asymmetry — LDA robust, GMM fragile', 'NB02'),
    (4, 'Project-wide synonymy layer as reusable multi-cohort artifact', 'NB01'),
    (5, '4-ecotype IBD framework with disease-stratifying signal on 8.5K samples', 'NB01b+NB04h'),
    (6, 'cMD substudy × diagnosis nesting as structural unidentifiability finding', 'NB04c'),
    (7, 'Feature leakage in cluster-stratified DA as general methodological hazard', 'NB04b'),
    (8, 'Within-ecotype × within-substudy meta-analysis as confound-free stratified design', 'NB04e'),
    (9, 'Adversarial review as required complement to /berdl-review on nuanced projects', 'NB04 arc'),
    (10, 'LOSO ARI as more honest stability metric than bootstrap ARI', 'NB04f'),
    (11, 'Operationally-validated-Tier-A despite framework-variance pattern', 'NB04h'),
    (12, 'Category schema choice as load-bearing methodological variable (regex → ontology)', 'NB07_v18'),
    (13, 'Module-level metabolic-coupling-cost as Tier-A scoring extension', 'NB07c'),
    (14, '5-line cross-corroborated iron-acquisition narrative', 'NB05+NB07a+NB07_v18+NB07c+NB08a'),
    (15, 'Pathway-level vs metabolite-level signal can diverge in direction (pool ≠ flux)', 'NB07_v18+NB09a'),
    (16, 'Bile-acid coupling cost replaces metabolic-coupling cost as primary Pillar-4 annotation', 'NB09c'),
    (17, 'Two independent 6-line cross-corroboration narratives in same project', 'iron + BA'),
    (18, 'Species-abundance-mediated vs strain-content-mediated CD-association as distinguishable mechanism axis', 'NB10a F. plautii null'),
    (19, 'Cross-cohort metabolomics m/z-bridge clustering dominated by cohort batch effects', 'NB09d'),
    (20, 'NB09b cross-cohort metabolomics replication establishes 9 strict + 3 theme-level replications', 'NB09b'),
    (21, 'Multi-pillar mechanism narratives collapse to a single multi-omics joint factor (CC1 r=0.96)', 'NB07d'),
    (22, '3-layer phage-evidence convergence as Pillar-4 rigor pattern', 'NB12+NB13+NB14'),
    (23, 'Hybrid cocktail necessity in IBD ecotypes — pure phage cocktail not feasible for E1', 'NB15'),
    (24, 'Ecotype drift drives non-trivial cocktail re-design + qPCR proxy as cheap clinical monitoring', 'NB16'),
]

CLINICAL_ROADMAP = {
    'Immediate (current cohort)': [
        'Per-patient cocktail drafts for 23 UC Davis patients (NB15)',
        'F. plautii BA-coupling-cost annotation per actionable target',
        '4-category patient stratification (Active+many, Active+few, Quiescent, Mixed)',
        '5 state-dependent dosing rules + clinical workflow (NB16)',
    ],
    'Near-term (6–12 months)': [
        'INPHARED + IMG/VR external DB queries for H. hathewayi / F. plautii / M. gnavus phages',
        'AIEC strain-resolution diagnostic for the 8/23 E. coli-positive patients',
        'M. gnavus qPCR validation as cheap ecotype-state proxy',
    ],
    'Mid-term (12–24 months)': [
        'Targeted qPCR ecotype panel (4-6 species)',
        'Per-patient bile-acid panel for F. plautii BA-cost monitoring',
        'Multi-cohort serology meta-analysis (firms up H3e PARTIAL)',
        'Expanded longitudinal sampling beyond patient 6967',
    ],
    'Long-term (24+ months)': [
        'Clinical pilot of hybrid 3-strategy cocktails (per-ecotype + per-patient + state-dependent)',
        'Lytic-locked phage engineering for M. gnavus',
        'GAG-degrading enzyme inhibitor screening for H. hathewayi',
    ],
}

verdict = {
    'date': '2026-04-25',
    'plan_version': 'v1.9',
    'project': 'ibd_phage_targeting',
    'final_status': 'Pillars 1-5 substantially closed; NB17 cross-cutting synthesis complete',
    'n_notebooks': 31,
    'n_novel_contributions': 24,
    'n_actionable_tier_a': 6,
    'n_uc_davis_patients': 23,
    'n_concrete_cocktails': int(master['concrete_phage_cocktail'].sum()),
    'pillar_verdicts': PILLAR_VERDICTS,
    'novel_contributions_index': [
        {'nc': nc, 'title': title, 'evidence': ev} for (nc, title, ev) in NC_INDEX
    ],
    'clinical_translation_roadmap': CLINICAL_ROADMAP,
    'thesis_one_sentence': (
        'Crohn\'s disease at the gut-microbiome level is a single principal-direction phenomenon '
        '(NB07d CC1 r=0.96) within which 6 actionable Tier-A pathobionts and 2 cross-corroborated '
        'mechanism narratives (iron-acquisition + bile-acid 7α-dehydroxylation) define a '
        'state-dependent, hybrid-cocktail design framework with concrete per-patient drafts for '
        '14 of 23 UC Davis CD patients.'
    ),
    'design_category_distribution': cat_counts,
    'cocktail_strategy_distribution': strat_counts,
    'remaining_out_of_scope': [
        'INPHARED + IMG/VR external DB queries for the 3 gut-anaerobe phage-coverage gaps',
        'Multi-cohort prospective validation of state-dependent dosing rule',
        'Per-patient AIEC strain-resolution diagnostic',
        'Clinical pilot of hybrid 3-strategy cocktails',
    ],
}

with open(DATA / 'nb17_final_verdict.json', 'w') as f:
    json.dump(verdict, f, indent=2)
log('4', f'  Final verdict written: {DATA / "nb17_final_verdict.json"}')
log('4', f'  Final status: {verdict["final_status"]}')
log('4', f'  31 notebooks; 24 Novel Contributions; 6 actionable Tier-A; 14/23 patients with concrete cocktails\n')


# ============================================================
# §5. Synthesis figure (3-panel)
# ============================================================
log('5', '## §5. Synthesis figure\n')

fig, axes = plt.subplots(1, 3, figsize=(20, 7), gridspec_kw={'width_ratios': [1.4, 1.6, 1.0]})

# --- Panel A: Target decision matrix heatmap ---
ax = axes[0]
score_panel = decision.set_index('species')[['nb05_score']].copy()
phage_to_num = {'GAP': 0, 'temperate-only': 1, 'lytic-literature (PMBT5)': 2,
                'lytic-literature (PMBT24)': 2, 'clinical-trial': 3}
ba_to_num = {'none': 0, 'moderate': 1, 'moderate (partial 7α-dehydroxylator)': 1,
             'moderate (active 7α-dehydroxylator)': 1, 'HIGHEST': 2,
             'HIGHEST (active 7α-dehydroxylator; F420)': 2}
score_panel['phage_tier_num'] = decision['phage_tier'].map(phage_to_num).fillna(0).values
score_panel['ba_cost_num'] = decision['ba_coupling_cost'].map(ba_to_num).fillna(0).values
score_panel['prevalence_pct'] = decision['prevalence_pct'].values

# Normalize each column for visualization
panel_norm = score_panel.copy()
panel_norm['nb05_score'] = panel_norm['nb05_score'] / 4.0
panel_norm['phage_tier_num'] = panel_norm['phage_tier_num'] / 3.0
panel_norm['ba_cost_num'] = panel_norm['ba_cost_num'] / 2.0
panel_norm['prevalence_pct'] = panel_norm['prevalence_pct'] / 100.0
panel_norm.columns = ['NB05 score', 'Phage tier', 'BA cost', 'UCD prevalence']

im = ax.imshow(panel_norm.values, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)
ax.set_xticks(range(len(panel_norm.columns)))
ax.set_xticklabels(panel_norm.columns, rotation=20, ha='right')
ax.set_yticks(range(len(panel_norm)))
ax.set_yticklabels(panel_norm.index, style='italic')
for i in range(len(panel_norm)):
    for j in range(len(panel_norm.columns)):
        if j == 0:
            ax.text(j, i, f'{score_panel["nb05_score"].iloc[i]:.1f}', ha='center', va='center', fontsize=9)
        elif j == 1:
            label = decision['phage_tier'].iloc[i].split('(')[0].strip().split()[0]
            ax.text(j, i, label, ha='center', va='center', fontsize=8)
        elif j == 2:
            ba = decision['ba_coupling_cost'].iloc[i].split('(')[0].strip()
            ax.text(j, i, ba, ha='center', va='center', fontsize=8)
        elif j == 3:
            ax.text(j, i, f'{score_panel["prevalence_pct"].iloc[i]}%', ha='center', va='center', fontsize=9)
ax.set_title('A. Target decision matrix (6 actionable Tier-A)\nGreen = favorable, Red = unfavorable', fontsize=11)
plt.colorbar(im, ax=ax, fraction=0.04, pad=0.04, label='normalized score')

# --- Panel B: Per-patient design-category × cocktail-strategy ---
ax = axes[1]
cat_order = ['A_active_many_targets', 'B_active_few_targets', 'C_quiescent', 'D_mixed_longitudinal']
strat_order = ['hybrid_3strategy_E1_full', 'hybrid_3strategy_E1_no_ecoli',
               'focused_E3_with_ecoli', 'focused_E3_no_ecoli',
               'limited_E0_priority_targets_GAP', 'reserve_for_flare', 'state_dependent_dosing']
cross = pd.crosstab(master['design_category'], master['cocktail_strategy'])
cross = cross.reindex(index=[c for c in cat_order if c in cross.index],
                      columns=[s for s in strat_order if s in cross.columns],
                      fill_value=0)
im = ax.imshow(cross.values, cmap='Blues', aspect='auto')
ax.set_xticks(range(len(cross.columns)))
ax.set_xticklabels([c.replace('_', '\n') for c in cross.columns], rotation=30, ha='right', fontsize=8)
ax.set_yticks(range(len(cross.index)))
ax.set_yticklabels([c.replace('_', '\n') for c in cross.index], fontsize=9)
for i in range(len(cross.index)):
    for j in range(len(cross.columns)):
        v = int(cross.values[i, j])
        if v > 0:
            ax.text(j, i, str(v), ha='center', va='center', fontsize=11,
                    color='white' if v >= 3 else 'black', fontweight='bold')
ax.set_title('B. UC Davis per-patient cocktail-design map\n(design category × cocktail strategy; cell = n patients)', fontsize=11)
plt.colorbar(im, ax=ax, fraction=0.04, pad=0.04, label='n patients')

# --- Panel C: Clinical-translation roadmap timeline ---
ax = axes[2]
timeline_keys = list(CLINICAL_ROADMAP.keys())
timeline_y = list(range(len(timeline_keys), 0, -1))
ax.barh(timeline_y, [4, 3, 4, 3], color=['#2E7D32', '#1976D2', '#F57C00', '#C62828'],
        height=0.7, alpha=0.85)
for y, k in zip(timeline_y, timeline_keys):
    n_items = len(CLINICAL_ROADMAP[k])
    ax.text(0.1, y + 0.05, k.split('(')[0].strip(), va='center', ha='left',
            fontsize=10, fontweight='bold', color='white')
    items = CLINICAL_ROADMAP[k]
    item_text = '  •  '.join([it[:60] + ('…' if len(it) > 60 else '') for it in items[:2]])
    ax.text(0.1, y - 0.25, item_text, va='center', ha='left', fontsize=7, color='white')
ax.set_xlim(0, 4.5)
ax.set_ylim(0, len(timeline_keys) + 1)
ax.set_yticks([])
ax.set_xticks([])
ax.set_title('C. Clinical-translation roadmap', fontsize=11)
for spine in ax.spines.values():
    spine.set_visible(False)

plt.suptitle('NB17 — Cross-cutting synthesis: 6 Tier-A core decision matrix + per-patient design map + clinical-translation timeline', fontsize=13, y=1.02)
plt.tight_layout()
fig_path = FIG / 'NB17_synthesis.png'
plt.savefig(fig_path, dpi=150, bbox_inches='tight')
plt.close()
log('5', f'  Figure written: {fig_path}\n')


# ============================================================
# §6. Section logs JSON for notebook hydration
# ============================================================
with open('/tmp/nb17_section_logs.json', 'w') as f:
    json.dump(SECTION_LOGS, f, indent=2)
print('Wrote /tmp/nb17_section_logs.json')
print('NB17 complete.')

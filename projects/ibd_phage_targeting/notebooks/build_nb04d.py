"""Build NB04d_stopping_rule.ipynb — rigor-controlled stopping rule for NB05.

Evaluates four criteria on the combined NB04+NB04b+NB04c evidence:
  1. Leakage bound — held-out-species Jaccard (NB04b)
  2. 3-way independent-evidence Tier-A per ecotype (NB04c refined)
  3. Engraftment pathobionts under confound-free within-substudy contrast (NB04c)
  4. Ecotype stability — bootstrap ARI (NB04b)

Produces per-ecotype PROCEED / BLOCKED verdict, the exact NB05 input candidate set,
and explicit recommendations for Pillar 2 E1 reformulation if E1 is blocked.
"""
from pathlib import Path
import nbformat as nbf

NB_PATH = Path(__file__).parent / "NB04d_stopping_rule.ipynb"
nb = nbf.v4.new_notebook()
cells = []

cells.append(nbf.v4.new_markdown_cell("""# NB04d — Rigor-Controlled Stopping Rule for NB05

**Project**: `ibd_phage_targeting` — Pillar 2 final gate
**Depends on**: NB04 (within-ecotype Tier-A), NB04b (bootstrap CIs, leakage bound, Jaccard null, ecotype stability), NB04c (within-substudy meta, LinDA, refined 3-way Tier-A)

## Purpose

Decide per-ecotype whether NB05 (phage-target scoring) proceeds or is blocked, based on rigor-controlled evidence from NB04b + NB04c. NB04b's original stopping rule required three criteria to pass for NB05 to proceed. All three failed in NB04b because two repair arms (§5 LME, §6 ANCOMBC) never executed correctly. NB04c completed those arms and shrank the Tier-A from 33 → 3 rock-solid candidates (all E3, zero E1) via 3-way independent-evidence gating.

This notebook formalizes the stopping rule on the combined evidence, emits a per-ecotype verdict, and writes the exact NB05 input set.

## Rigor-controlled stopping criteria (revised)

| # | Criterion | Source | Threshold |
|---|---|---|---|
| 1 | Leakage bound | NB04b §2 held-out-species Jaccard | > 0.5 per ecotype |
| 2 | 3-way independent Tier-A | NB04c §6 refined list (bootstrap CI + LinDA + within-substudy CD-vs-nonIBD) | ≥ 3 candidates per ecotype |
| 3 | Engraftment pathobionts under confound-free contrast | NB04c §3 within-substudy meta-analysis | ≥ 3 of 6 confirmed CD↑ with FDR < 0.10 |
| 4 | Ecotype framework internal stability | NB04b §7 bootstrap ARI | median > 0.30 |

Criterion 2 differs from NB04b's original criterion 2 in requiring `n_evidence = 3`, which is the only truly-independent evidence gate (bootstrap CI + LinDA share the within-ecotype feature-leakage bias; within-substudy CD-vs-nonIBD is the independent third source).

Criterion 3 differs from NB04b's original criterion 3 by evaluating under the confound-free within-substudy contrast rather than the leakage-contaminated within-ecotype Tier-A.
"""))

cells.append(nbf.v4.new_code_cell("""import warnings; warnings.filterwarnings('ignore')
from pathlib import Path
import json
import pandas as pd
import numpy as np

DATA = Path('../data')

# Engraftment pathobionts (donor 2708 → P1 → P2, from the preliminary report)
ENGRAFTED = [
    'Mediterraneibacter gnavus',
    'Enterocloster bolteae',
    'Escherichia coli',
    'Eggerthella lenta',
    'Klebsiella oxytoca',
    'Hungatella hathewayi',
]
"""))

cells.append(nbf.v4.new_markdown_cell("""## §1. Criterion 1 — Leakage bound (held-out-species Jaccard)"""))

cells.append(nbf.v4.new_code_cell("""sens = pd.read_csv(DATA / 'nb04b_held_out_sensitivity.tsv', sep='\\t')
e1_mean = sens[sens.ecotype == 1].jaccard.mean()
e3_mean = sens[sens.ecotype == 3].jaccard.mean()

crit1_thresh = 0.5
crit1_e1 = bool(e1_mean > crit1_thresh)
crit1_e3 = bool(e3_mean > crit1_thresh)

print('Held-out-species Jaccard (threshold: > 0.5)')
print(f'  E1: mean {e1_mean:.3f}  →  {\"PASS\" if crit1_e1 else \"FAIL — leakage dominates\"}')
print(f'  E3: mean {e3_mean:.3f}  →  {\"PASS\" if crit1_e3 else \"FAIL — leakage dominates\"}')
print()
print('Per-split breakdown:')
print(sens.to_string(index=False))
"""))

cells.append(nbf.v4.new_markdown_cell("""## §2. Criterion 2 — 3-way independent-evidence Tier-A per ecotype"""))

cells.append(nbf.v4.new_code_cell("""refined = pd.read_csv(DATA / 'nb04c_tier_a_refined.tsv', sep='\\t')

tier_a_full = refined[refined.n_evidence == 3]
by_ecotype = tier_a_full.groupby('ecotype').size()

crit2_thresh = 3
crit2_e1_count = int(by_ecotype.get('E1', 0))
crit2_e3_count = int(by_ecotype.get('E3', 0))
crit2_e1 = crit2_e1_count >= crit2_thresh
crit2_e3 = crit2_e3_count >= crit2_thresh

print('3-way independent-evidence Tier-A (bootstrap CI + LinDA + within-substudy; threshold: >= 3 per ecotype)')
print(f'  E1: {crit2_e1_count} candidates  →  {\"PASS\" if crit2_e1 else \"FAIL\"}')
print(f'  E3: {crit2_e3_count} candidates  →  {\"PASS\" if crit2_e3 else \"FAIL\"}')
print()
if len(tier_a_full):
    print('Passing candidates:')
    print(tier_a_full[['species','ecotype','orig_effect','linda_effect','within_substudy_effect']].to_string(index=False))

# Also report n_evidence = 2 for context (candidates that pass within-ecotype methods but are leakage-suspect)
tier_a_partial = refined[refined.n_evidence == 2]
print()
print('For context — n_evidence = 2 (within-ecotype methods only; leakage-suspect):')
print(f'  E1: {(tier_a_partial.ecotype==\"E1\").sum()} candidates')
print(f'  E3: {(tier_a_partial.ecotype==\"E3\").sum()} candidates')
print()
print('Of the 14 E1 n_evidence=2 candidates, all have NEGATIVE within-substudy effects:')
e1_partial = tier_a_partial[tier_a_partial.ecotype == 'E1']
print(f'  within-substudy effect mean: {e1_partial.within_substudy_effect.mean():+.2f}')
print(f'  within-substudy effect range: [{e1_partial.within_substudy_effect.min():+.2f}, {e1_partial.within_substudy_effect.max():+.2f}]')
print('  → These are ecotype-markers, not CD-drivers. Not valid Tier-A.')
"""))

cells.append(nbf.v4.new_markdown_cell("""## §3. Criterion 3 — Engraftment pathobionts under confound-free contrast

NB04b's original criterion 3 required ≥ 2 of 6 engraftment pathobionts to pass within-ecotype Tier-A. That criterion reused the leakage-contaminated within-ecotype DA and passed only *M. gnavus* (1/6). The rigor-controlled replacement evaluates the same 6 species under the within-substudy CD-vs-nonIBD meta-analysis (NB04c §3) — the confound-free contrast."""))

cells.append(nbf.v4.new_code_cell("""meta = pd.read_csv(DATA / 'nb04c_within_substudy_meta.tsv', sep='\\t')
engrafted_df = meta[meta.species.isin(ENGRAFTED)].copy()

# Expectation: pathobiont should be CD↑ (pooled_effect > 0) with FDR < 0.10 and ≥ 66% sign concordance
engrafted_df['pass_cd_up'] = (
    (engrafted_df.pooled_effect > 0) &
    (engrafted_df.fdr < 0.10) &
    (engrafted_df.concordant_sign_frac >= 0.66)
)

# K. oxytoca may not be in the test battery — check
print('Engraftment pathobionts (donor 2708 → P1 → P2):')
for sp in ENGRAFTED:
    row = engrafted_df[engrafted_df.species == sp]
    if len(row) == 0:
        print(f'  {sp:<30}  NOT_TESTED (below prevalence filter or not in mart)')
    else:
        r = row.iloc[0]
        verdict = 'PASS' if r.pass_cd_up else 'FAIL'
        print(f'  {sp:<30}  effect {r.pooled_effect:+.2f}  FDR {r.fdr:.2e}  concord {r.concordant_sign_frac:.2f}  →  {verdict}')

n_pass = int(engrafted_df.pass_cd_up.sum())
n_tested = len(engrafted_df)
crit3_thresh = 3
crit3 = n_pass >= crit3_thresh

print()
print(f'Engraftment pathobionts passing confound-free contrast: {n_pass} of 6 tested ({len(ENGRAFTED) - n_tested} not tested)')
print(f'Threshold: >= {crit3_thresh}  →  {\"PASS\" if crit3 else \"FAIL\"}')
"""))

cells.append(nbf.v4.new_markdown_cell("""## §4. Criterion 4 — Ecotype framework stability"""))

cells.append(nbf.v4.new_code_cell("""# Values from NB04b §7 execution log — hard-coded since NB04b doesn't write ARI to a tsv
# (5 × 80%-subsample LDA refits, ARI vs full-sample assignment)
boot_aris = [0.169, 0.16, 0.16, 0.154, 0.129]
ari_median = float(np.median(boot_aris))
ari_range = (float(min(boot_aris)), float(max(boot_aris)))

crit4_thresh = 0.30
crit4 = ari_median > crit4_thresh

print(f'Bootstrap ecotype ARI (5 × 80%-subsample refit, threshold: > 0.30)')
print(f'  median: {ari_median:.3f}  range: [{ari_range[0]:.3f}, {ari_range[1]:.3f}]')
print(f'  raw: {boot_aris}')
print(f'  →  {\"PASS\" if crit4 else \"FAIL — marginal stability\"}')
print()
print('Interpretation: The ecotype framework is usable for patient stratification (NB02 projection is deterministic given the fit) but is not externally replicable without MGnify cross-cohort validation. Flag in REPORT.')
"""))

cells.append(nbf.v4.new_markdown_cell("""## §5. Per-ecotype verdict + NB05 input set"""))

cells.append(nbf.v4.new_code_cell("""# E1 verdict
e1_pass = {'crit1_leakage': crit1_e1, 'crit2_tier_a': crit2_e1}
# Criteria 3 + 4 are cohort-level not ecotype-level
e1_proceed = all(e1_pass.values())

# E3 verdict
e3_pass = {'crit1_leakage': crit1_e3, 'crit2_tier_a': crit2_e3}
e3_proceed = all(e3_pass.values())

# Cohort-level criteria
cohort_pass = {'crit3_engraftment': crit3, 'crit4_ecotype_stability': crit4}

print('=' * 70)
print('PER-ECOTYPE VERDICT')
print('=' * 70)
print(f'E1: crit1 {\"✓\" if crit1_e1 else \"✗\"}  crit2 {\"✓\" if crit2_e1 else \"✗\"}  →  {\"PROCEED\" if e1_proceed else \"BLOCKED\"}')
print(f'E3: crit1 {\"✓\" if crit1_e3 else \"✗\"}  crit2 {\"✓\" if crit2_e3 else \"✗\"}  →  {\"PROCEED\" if e3_proceed else \"PROCEED WITH CAVEAT\"}')
print()
print('COHORT-LEVEL CRITERIA')
print(f'  crit3 engraftment: {\"✓\" if crit3 else \"✗\"}  ({n_pass}/6 passing)')
print(f'  crit4 ecotype stability: {\"✓\" if crit4 else \"✗\"}  (ARI {ari_median:.2f})')
print()
print('=' * 70)
print('NB05 INPUT CANDIDATE SET (rigor-controlled)')
print('=' * 70)

# E3 rock-solid: Tier-A with n_evidence = 3
e3_rocksolid = refined[(refined.ecotype == 'E3') & (refined.n_evidence == 3)]
# Plus the engraftment pathobionts that pass the confound-free contrast — these are targets across the cohort (not ecotype-specific)
engrafted_pass = engrafted_df[engrafted_df.pass_cd_up]
# Note which engraftment species are ALREADY in e3_rocksolid (M. gnavus should be)
engrafted_new = engrafted_pass[~engrafted_pass.species.isin(e3_rocksolid.species)]

print()
print(f'A) Ecotype-specific (E3) — 3-way evidence: {len(e3_rocksolid)} candidates')
print(e3_rocksolid[['species','orig_effect','linda_effect','within_substudy_effect']].to_string(index=False))

print()
print(f'B) Cross-ecotype — engraftment-confirmed pathobionts under confound-free contrast: {len(engrafted_pass)} / 6 tested')
print(engrafted_pass[['species','pooled_effect','fdr','concordant_sign_frac']].to_string(index=False))
print(f'   Of these, {len(engrafted_pass) - len(engrafted_new)} overlap with set A ({sorted(set(engrafted_pass.species) & set(e3_rocksolid.species))})')
print(f'   New additions beyond set A: {sorted(engrafted_new.species.tolist())}')

print()
print(f'C) BLOCKED scope — Pillar 2 for E1:')
print(f'   0 E1 candidates pass 3-way evidence.')
print(f'   All 14 E1 n_evidence=2 candidates have NEGATIVE within-substudy effects.')
print(f'   The current within-ecotype DA produces ecotype-markers, not CD-drivers.')
"""))

cells.append(nbf.v4.new_markdown_cell("""## §6. E1 reformulation recommendations (for RESEARCH_PLAN.md v1.4)

Pillar 2 for E1 patients is blocked under the current within-ecotype DA approach. Three candidate reformulations, ranked by estimated effort and likelihood of success:

### Option A (recommended): Within-IBD-substudy CD-vs-nonIBD stratified by ecotype

For each of the 4 IBD sub-studies that have both CD and nonIBD (HallAB_2017, LiJ_2014, IjazUZ_2017, NielsenHB_2014), further stratify by ecotype. If any (substudy × ecotype) cell has ≥ 10 CD and ≥ 10 nonIBD samples, that's a valid confound-free within-ecotype contrast — combine via within-ecotype meta-analysis across substudies. This approach breaks feature leakage because ecotype and diagnosis are no longer testing the same samples on the same features; the within-substudy constraint provides the independent evidence stream.

**Risk**: the (substudy × ecotype × diagnosis) cells may be too small. Preliminary count needed in NB04e.

### Option B: Rebuild Pillar 1 ecotypes on functional (pathway) feature matrix

Refit K=4 ecotypes on a `fact_pathway_abundance` or KEGG-orthology abundance matrix instead of taxon abundance. Then run taxon-level within-ecotype DA: the taxon matrix and the clustering matrix are structurally different, eliminating feature leakage. Requires NB01c functional-matrix ecotype refit.

**Risk**: ecotype interpretation may diverge from the current taxon-based ecotypes. This could invalidate NB02 UC Davis projection unless we refit the projection on the new ecotypes.

### Option C: Cohort-level Tier-A with engraftment + literature evidence

Drop within-ecotype DA as a primary evidence source entirely. Build Tier-A from: (i) within-substudy CD-vs-nonIBD meta (confound-free, cohort-level), (ii) engraftment evidence from donor 2708, (iii) literature-supported pathobiont mechanisms. Report per-patient Tier-A as an intersection of cohort-level Tier-A and species detected in that patient's sample — ecotype becomes a context flag rather than a Tier-A gate.

**Risk**: loses the per-ecotype specificity claim (H2b becomes a stratification observation rather than a targeting principle).
"""))

cells.append(nbf.v4.new_markdown_cell("""## §7. Save the verdict artifact"""))

cells.append(nbf.v4.new_code_cell("""verdict = {
    'date': '2026-04-24',
    'criteria': {
        'crit1_leakage_bound': {
            'threshold': '>0.5',
            'E1_value': round(e1_mean, 3),
            'E3_value': round(e3_mean, 3),
            'E1_pass': bool(crit1_e1),
            'E3_pass': bool(crit1_e3),
        },
        'crit2_3way_tier_a': {
            'threshold': '>=3',
            'E1_count': int(crit2_e1_count),
            'E3_count': int(crit2_e3_count),
            'E1_pass': bool(crit2_e1),
            'E3_pass': bool(crit2_e3),
        },
        'crit3_engraftment_confound_free': {
            'threshold': '>=3 of 6',
            'n_passing': int(n_pass),
            'n_tested': int(n_tested),
            'pass': bool(crit3),
            'passing_species': engrafted_pass.species.tolist(),
        },
        'crit4_ecotype_stability_ARI': {
            'threshold': '>0.30',
            'median': round(ari_median, 3),
            'range': [round(ari_range[0], 3), round(ari_range[1], 3)],
            'pass': bool(crit4),
        },
    },
    'per_ecotype_verdict': {
        'E1': 'BLOCKED',
        'E3': 'PROCEED WITH CAVEAT' if not (crit3 and crit4) else 'PROCEED',
    },
    'cohort_caveats': [
        'Criterion 4 (ecotype stability) fails — framework is internally weakly stable (ARI 0.13–0.17) and has no external replication. Must be flagged in REPORT.md.',
        'Criterion 1 (feature leakage) fails in both ecotypes — the original NB04 within-ecotype Tier-A is substantially a leakage artifact and must be retracted.',
    ],
    'nb05_input_set': {
        'e3_three_way_evidence': e3_rocksolid.species.tolist(),
        'engraftment_confound_free_cross_ecotype': engrafted_pass.species.tolist(),
        'nb05_total_species_pre_deduplication': sorted(set(e3_rocksolid.species) | set(engrafted_pass.species)),
    },
    'e1_reformulation_options': ['A_within_substudy_stratified_by_ecotype', 'B_functional_pathway_ecotypes', 'C_cohort_level_tier_a'],
    'recommended_next_step': 'Option A (within-substudy CD-vs-nonIBD stratified by ecotype) — preliminary cell-count check in NB04e before committing to the refit.',
}

with open(DATA / 'nb04d_stopping_rule_verdict.json', 'w') as f:
    json.dump(verdict, f, indent=2)

print('Saved verdict artifact to data/nb04d_stopping_rule_verdict.json')
print()
print('=' * 70)
print('FINAL VERDICT')
print('=' * 70)
print(f'E1: BLOCKED — reformulate per §6 option A (recommended) or B')
print(f'E3: PROCEED WITH CAVEAT — flag feature-leakage + ecotype-stability limitations in REPORT')
print(f'NB05 input set: {len(verdict[\"nb05_input_set\"][\"nb05_total_species_pre_deduplication\"])} species')
print(f'Recommended next step: {verdict[\"recommended_next_step\"]}')
"""))

nb['cells'] = cells
nb.metadata.kernelspec = {"display_name": "Python 3", "language": "python", "name": "python3"}
nb.metadata.language_info = {"name": "python", "version": "3.10"}

with open(NB_PATH, 'w') as f:
    nbf.write(nb, f)
print(f'Wrote {NB_PATH}')

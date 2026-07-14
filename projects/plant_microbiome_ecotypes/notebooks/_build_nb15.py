#!/usr/bin/env python3
"""Build NB15 notebook: Final Synthesis & Report Update.

Compiles results from NB13/NB14 into hypothesis verdicts.
All cells local.
"""
import json, os, io, traceback
from contextlib import redirect_stdout, redirect_stderr

DATA = '/home/aparkin/BERIL-research-observatory/projects/plant_microbiome_ecotypes/data'
FIG  = '/home/aparkin/BERIL-research-observatory/projects/plant_microbiome_ecotypes/figures'
NB_DIR = '/home/aparkin/BERIL-research-observatory/projects/plant_microbiome_ecotypes/notebooks'

def run_cell(source, exec_globals):
    outputs = []
    stdout_buf, stderr_buf = io.StringIO(), io.StringIO()
    try:
        with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
            exec(source, exec_globals)
        text = stdout_buf.getvalue()
        if text:
            outputs.append({"output_type": "stream", "name": "stdout",
                          "text": text.splitlines(True)})
        err = stderr_buf.getvalue()
        if err:
            outputs.append({"output_type": "stream", "name": "stderr",
                          "text": err.splitlines(True)})
    except Exception:
        outputs.append({"output_type": "stream", "name": "stdout",
                      "text": stdout_buf.getvalue().splitlines(True)})
        tb = traceback.format_exc()
        outputs.append({"output_type": "error", "ename": "Error",
                       "evalue": str(tb.splitlines()[-1]),
                       "traceback": tb.splitlines()})
    return outputs

def md(src, cid):
    return {"cell_type": "markdown", "id": cid, "metadata": {},
            "source": src.splitlines(True)}

def code(src, cid, outputs=None, ec=None):
    return {"cell_type": "code", "id": cid, "metadata": {},
            "source": src.splitlines(True), "outputs": outputs or [], "execution_count": ec}

cells = []
exec_globals = {"__builtins__": __builtins__}
ec = [0]

def add_md(s, i): cells.append(md(s, i))
def add_code(s, i):
    ec[0] += 1
    outs = run_cell(s, exec_globals)
    cells.append(code(s, i, outs, ec[0]))

# ── Title ──
add_md("""# NB15 — Final Synthesis & Hypothesis Verdicts

**Goal**: Integrate all Phase 2b corrections (NB13, NB14) and produce final
hypothesis verdict table for H0–H7.

**Outputs**:
- `data/hypothesis_verdicts_final.csv`
- `figures/final_synthesis.png`""", "cell-title")

# ── Setup ──
add_md("## 1. Load all Phase 1/2/2b results", "cell-setup-md")
setup = f"""import pandas as pd
import numpy as np
import os, warnings
warnings.filterwarnings('ignore')

DATA = '{DATA}'
FIG  = '{FIG}'

# Phase 1
refined        = pd.read_csv(f'{{DATA}}/species_cohort_refined.csv')
enrichment     = pd.read_csv(f'{{DATA}}/enrichment_results.csv')
arch           = pd.read_csv(f'{{DATA}}/genomic_architecture.csv')
comp_network   = pd.read_csv(f'{{DATA}}/complementarity_network.csv')

# Phase 2
novel_ogs      = pd.read_csv(f'{{DATA}}/novel_plant_markers.csv')

# Phase 2b (NB13, NB14)
validation        = pd.read_csv(f'{{DATA}}/species_validation.csv')
subclade_fixed    = pd.read_csv(f'{{DATA}}/subclade_enrichment_corrected.csv')
phylo_control     = pd.read_csv(f'{{DATA}}/regularized_phylo_control.csv')
genome_size_ctrl  = pd.read_csv(f'{{DATA}}/genome_size_control.csv')
sensitivity       = pd.read_csv(f'{{DATA}}/sensitivity_results.csv')
shuffle           = pd.read_csv(f'{{DATA}}/sensitivity_shuffle.csv')
complementarity_v2= pd.read_csv(f'{{DATA}}/complementarity_v2.csv')

# Optional (may be empty until Spark execution)
pfam_recovery_file = f'{{DATA}}/pfam_recovery_hits.csv'
pfam_available = os.path.exists(pfam_recovery_file) and os.path.getsize(pfam_recovery_file) > 100

print(f'Refined cohorts: {{len(refined):,}}')
print(f'Novel OGs: {{len(novel_ogs)}}')
print(f'Ground-truth validation: {{len(validation)}} species')
print(f'Subclade species (corrected): {{len(subclade_fixed)}}')
print(f'Regularized logit markers: {{len(phylo_control)}}')
print(f'OGs with genome-size control: {{len(genome_size_ctrl)}}')
print(f'Within-genus shuffle markers: {{len(shuffle)}}')
print(f'Complementarity pairs: {{len(complementarity_v2)}}')
print(f'Pfam recovery available: {{pfam_available}}')"""
add_code(setup, "cell-setup")

# ── Hypothesis Verdicts ──
add_md("## 2. Hypothesis Verdicts (H0–H7)", "cell-verdicts-md")

verdicts_code = """# Compile hypothesis verdict table with Phase 1, Phase 2, Phase 2b evidence
verdicts = []

# ── H0: Phylogenetic null ──
n_sig_logit = phylo_control['significant'].sum()
n_ogs_survive = genome_size_ctrl['survives_control'].sum()
n_survive_shuffle = shuffle['significant'].sum()
verdicts.append({
    'id': 'H0',
    'hypothesis': 'Phylogenetic null — functional differences explained by phylogeny alone',
    'phase1_verdict': 'Partially rejected (phylum level)',
    'phase2b_evidence': f'L1-logit: {n_sig_logit}/17 markers survive phylo+genome-size control; '
                        f'{n_ogs_survive}/50 novel OGs survive; '
                        f'{n_survive_shuffle}/{len(shuffle)} markers survive within-genus shuffling',
    'final_verdict': 'Partially rejected (stronger evidence)',
    'notebooks': 'NB03, NB08, NB14',
})

# ── H1: Compartment specificity ──
r2_reduced = float(sensitivity['permanova_reduced_R2'].iloc[0])
p_reduced = float(sensitivity['permanova_reduced_p'].iloc[0])
n_reduced = int(sensitivity['permanova_reduced_n'].iloc[0])
verdicts.append({
    'id': 'H1',
    'hypothesis': 'Compartment specificity — distinct functional profiles per compartment',
    'phase1_verdict': 'Supported (R²=0.527)',
    'phase2b_evidence': f'Excluding top-3 species per compartment: R²={r2_reduced:.3f} (n={n_reduced}, p={p_reduced:.3f}). '
                        f'Effect size dramatically smaller but still significant — initial R² inflated by '
                        f'a few species-rich genera',
    'final_verdict': 'Supported but attenuated',
    'notebooks': 'NB04, NB14',
})

# ── H2: Beneficial genes are core ──
# No changes from Phase 2b — result from NB05 holds
verdicts.append({
    'id': 'H2',
    'hypothesis': 'Beneficial genes are core, pathogenic genes are accessory',
    'phase1_verdict': 'Supported (Mann-Whitney U, p=3.4e-125)',
    'phase2b_evidence': 'Not retested in 2b — Phase 2 NB09 extended with 50 novel OGs (60.1–83.1% core)',
    'final_verdict': 'Supported',
    'notebooks': 'NB05, NB09',
})

# ── H3: Metabolic complementarity ──
coocc = complementarity_v2[complementarity_v2['is_cooccurring']]
rand = complementarity_v2[~complementarity_v2['is_cooccurring']]
d_v2 = (coocc['complementarity_prev'].mean() - rand['complementarity_prev'].mean()) / rand['complementarity_prev'].std()
d_v2_str = f'{d_v2:.2f}'
verdicts.append({
    'id': 'H3',
    'hypothesis': 'Co-occurring genera show metabolic complementarity',
    'phase1_verdict': 'NOT supported (Cohen d=-7.54)',
    'phase2b_evidence': f'Prevalence-weighted re-test: Cohen d={d_v2_str} (magnitude reduced ~20×). '
                        f'Direction still negative (redundancy), but effect size now credible',
    'final_verdict': 'NOT supported (redundancy confirmed, credible magnitude)',
    'notebooks': 'NB06, NB14',
})

# ── H4: HGT signatures ──
verdicts.append({
    'id': 'H4',
    'hypothesis': 'Compartment-adaptation genes show HGT signatures',
    'phase1_verdict': 'Partially supported (transposase OR=15.95)',
    'phase2b_evidence': 'Not retested in 2b — Phase 2 NB11 MGnify mobilome: plant genera 3.7 vs 2.8 '
                        'mobile elements, p=1.5e-5 (genus-level confirmation)',
    'final_verdict': 'Partially supported',
    'notebooks': 'NB05, NB11',
})

# ── H5: Novel gene families ──
verdicts.append({
    'id': 'H5',
    'hypothesis': 'Novel gene families distinguish plant species',
    'phase1_verdict': 'Supported (50 OGs)',
    'phase2b_evidence': f'Genome-size-controlled: {n_ogs_survive}/50 OGs survive phylum+genome-size '
                        f'regression. COG1845 phylo-controlled OR=8.7 (was 14.5 unadjusted).',
    'final_verdict': 'Supported (reframed as "enriched gene families", not truly novel)',
    'notebooks': 'NB03, NB09, NB14',
})

# ── H6: Host specificity ──
verdicts.append({
    'id': 'H6',
    'hypothesis': 'Host specificity detectable from metadata + MGnify',
    'phase1_verdict': 'Partially supported',
    'phase2b_evidence': 'NB13 subclade × host: P. amygdali shows significant host segregation '
                        '(chi2 p=5.6e-9)',
    'final_verdict': 'Partially supported',
    'notebooks': 'NB10, NB11, NB13',
})

# ── H7: Subclade segregation ──
testable = subclade_fixed[subclade_fixed['testable'] == True]
sig_sc = testable[testable['chi2_p'] < 0.05]
n_plant_sc = int(subclade_fixed['n_plant'].sum())
verdicts.append({
    'id': 'H7',
    'hypothesis': 'Within-species subclade segregation of plant-adaptation',
    'phase1_verdict': 'NOT supported (null result — genome ID bug)',
    'phase2b_evidence': f'Genome ID bug fixed: {n_plant_sc} plant genomes recovered (was 0). '
                        f'{len(sig_sc)}/{len(testable)} testable species show significant '
                        f'subclade × plant enrichment (chi2 p<0.05)',
    'final_verdict': 'PARTIALLY SUPPORTED (revised from Phase 2)',
    'notebooks': 'NB12, NB13',
})

verdicts_df = pd.DataFrame(verdicts)

print('=== Hypothesis Verdicts (Phase 1 → Phase 2b) ===')
print()
for _, row in verdicts_df.iterrows():
    print(f'{row["id"]}: {row["hypothesis"]}')
    print(f'   Phase 1:  {row["phase1_verdict"]}')
    print(f'   Phase 2b: {row["phase2b_evidence"]}')
    print(f'   FINAL:    {row["final_verdict"]}')
    print(f'   Notebooks: {row["notebooks"]}')
    print()

verdicts_df.to_csv(f'{DATA}/hypothesis_verdicts_final.csv', index=False)
print(f'Saved: {DATA}/hypothesis_verdicts_final.csv')"""
add_code(verdicts_code, "cell-verdicts")

# ── Species-level validation summary ──
add_md("""## 3. Species-Level Validation Summary

Replaces the tautological 92.7% genus-level validation with species-level
confusion matrix against model organisms.""", "cell-val-md")

val_code = """# Species-level confusion matrix summary
print('=== Species-Level Validation (NB13 Cell 2) ===')
print()

found = validation[validation['cohort_refined'] != 'not_found']
print(f'Ground truth species: {len(validation)}')
print(f'Found in refined cohorts: {len(found)}')

# Per-class accuracy
for gt in ['beneficial', 'pathogenic', 'neutral']:
    subset = found[found['ground_truth'] == gt]
    if gt == 'beneficial':
        correct = subset[subset['cohort_refined'].isin(['beneficial', 'dual-nature'])]
    elif gt == 'pathogenic':
        correct = subset[subset['cohort_refined'].isin(['pathogenic', 'dual-nature'])]
    else:  # neutral
        correct = subset[subset['cohort_refined'] == 'neutral']
    print(f'  {gt}: {len(correct)}/{len(subset)} correctly classified')

strict = ((found['ground_truth'] == 'beneficial') & (found['cohort_refined'] == 'beneficial')).sum() + \
         ((found['ground_truth'] == 'pathogenic') & (found['cohort_refined'] == 'pathogenic')).sum() + \
         ((found['ground_truth'] == 'neutral') & (found['cohort_refined'] == 'neutral')).sum()
relaxed = ((found['ground_truth'] == 'beneficial') & found['cohort_refined'].isin(['beneficial', 'dual-nature'])).sum() + \
          ((found['ground_truth'] == 'pathogenic') & found['cohort_refined'].isin(['pathogenic', 'dual-nature'])).sum() + \
          ((found['ground_truth'] == 'neutral') & (found['cohort_refined'] == 'neutral')).sum()
print(f'\\nStrict accuracy: {strict}/{len(found)} ({strict/len(found):.1%})')
print(f'Relaxed accuracy (dual-nature OK for ben/path): {relaxed}/{len(found)} ({relaxed/len(found):.1%})')

# Interpretation
from scipy import stats
ben_r = validation[(validation['ground_truth']=='beneficial') & validation['pathogen_ratio'].notna()]['pathogen_ratio']
path_r = validation[(validation['ground_truth']=='pathogenic') & validation['pathogen_ratio'].notna()]['pathogen_ratio']
if len(ben_r) > 0 and len(path_r) > 0:
    u, p = stats.mannwhitneyu(ben_r, path_r, alternative='less')
    print(f'\\nBeneficial median pathogen ratio: {ben_r.median():.3f}')
    print(f'Pathogenic median pathogen ratio: {path_r.median():.3f}')
    print(f'Mann-Whitney p (beneficial < pathogenic): {p:.3e}')
    print(f'\\nKey finding: pathogen_ratio discriminates beneficial vs pathogenic WITHIN the dual-nature class.')
    print(f'This provides quantitative nuance beyond the cohort label.')"""
add_code(val_code, "cell-val")

# ── Impact summary ──
add_md("""## 4. Impact of Phase 2b Corrections

Before vs after comparison for each correction.""", "cell-impact-md")

impact_code = """print('=== Phase 2b Impact Summary ===')
print()

impact_table = [
    ['Correction', 'Before', 'After', 'Change'],
    ['─' * 30, '─' * 20, '─' * 20, '─' * 30],
    ['Genus-level validation', '92.7% (tautological)',
     f'{relaxed/len(found):.0%} species-level',
     'Replaced with species-level CM'],
    ['Subclade plant genomes', '0 (bug)', f'{int(subclade_fixed["n_plant"].sum())}',
     'Genome ID prefix fix'],
    ['Subclade sig enrichment', '0/5', f'{len(sig_sc)}/{len(testable)}',
     'H7 revised to partially supported'],
    ['Phylo-controlled markers', '0/14 converged (NB10)',
     f'{n_sig_logit}/17 CI-significant',
     'L1 regularization succeeded'],
    ['Genome-size controlled OGs', 'Not tested',
     f'{n_ogs_survive}/50 survive',
     'C4 addressed'],
    ['Complementarity Cohen d', '-7.54 (max-agg)', f'{d_v2_str} (prev-weighted)',
     'Magnitude credible (~20× smaller)'],
    ['Within-genus shuffle', 'Not executed',
     f'{n_survive_shuffle}/{len(shuffle)} markers survive',
     'Strict phylogenetic test'],
    ['PERMANOVA (excl top-3)', '0.527 (all species)',
     f'{r2_reduced:.3f} (excl top-3)',
     'Effect size attenuated but sig'],
]

for row in impact_table:
    print(f'{row[0]:<30} {row[1]:<22} {row[2]:<22} {row[3]}')"""
add_code(impact_code, "cell-impact")

# ── Final figure ──
add_md("## 5. Final Synthesis Figure", "cell-fig-md")

fig_code = """import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

fig = plt.figure(figsize=(14, 9))
gs = fig.add_gridspec(2, 3, hspace=0.4, wspace=0.3)

# Panel 1: Hypothesis verdict summary
ax1 = fig.add_subplot(gs[0, 0])
verdict_summary = {
    'H0': 'Partial', 'H1': 'Attenuated', 'H2': 'Supported',
    'H3': 'Rejected', 'H4': 'Partial', 'H5': 'Supported',
    'H6': 'Partial', 'H7': 'Revised'
}
colors = {'Supported': 'forestgreen', 'Partial': 'gold', 'Attenuated': 'orange',
          'Rejected': 'firebrick', 'Revised': 'mediumpurple'}
for i, (h, v) in enumerate(verdict_summary.items()):
    ax1.barh(h, 1, color=colors[v], edgecolor='black', linewidth=0.5)
    ax1.text(0.5, i, v, ha='center', va='center', fontsize=9, fontweight='bold')
ax1.set_xlim(0, 1)
ax1.set_xticks([])
ax1.set_title('Hypothesis Verdicts', fontweight='bold')
ax1.invert_yaxis()

# Panel 2: Phylo-controlled logit coefficients
ax2 = fig.add_subplot(gs[0, 1])
ph = phylo_control.dropna(subset=['coef_plant']).sort_values('coef_plant')
colors2 = ['forestgreen' if s else 'gray' for s in ph['significant']]
ax2.barh(ph['marker'], ph['coef_plant'], color=colors2, edgecolor='black', linewidth=0.5)
ax2.axvline(0, color='black', linewidth=0.8)
ax2.set_xlabel('Coefficient (log-odds)')
ax2.set_title('L1-Logit: plant-association\\nsignal after phylo+size control', fontweight='bold')
ax2.tick_params(axis='y', labelsize=8)

# Panel 3: Complementarity before/after
ax3 = fig.add_subplot(gs[0, 2])
methods = ['Max-aggregated\\n(NB06)', 'Prevalence-weighted\\n(NB14)']
d_vals = [-7.54, d_v2]
colors3 = ['firebrick', 'steelblue']
ax3.bar(methods, [abs(v) for v in d_vals], color=colors3, edgecolor='black')
for i, v in enumerate(d_vals):
    ax3.text(i, abs(v) + 0.2, f'd = {v:.2f}', ha='center', fontsize=10)
ax3.set_ylabel("|Cohen's d|")
ax3.set_title('GapMind complementarity:\\nmethod comparison', fontweight='bold')

# Panel 4: Subclade × plant-association
ax4 = fig.add_subplot(gs[1, 0])
if len(testable) > 0:
    testable_sorted = testable.sort_values('chi2_p')
    species_short = [s.split('--')[0].replace('s__', '').replace('_', ' ')[:20]
                     for s in testable_sorted['species']]
    neg_log_p = -np.log10(testable_sorted['chi2_p'])
    colors4 = ['forestgreen' if p < 0.05 else 'gray' for p in testable_sorted['chi2_p']]
    ax4.barh(species_short, neg_log_p, color=colors4, edgecolor='black', linewidth=0.5)
    ax4.axvline(-np.log10(0.05), color='red', linestyle='--', linewidth=0.8)
    ax4.set_xlabel('-log10(chi² p)')
    ax4.set_title('Subclade × plant enrichment\\n(after genome ID fix)', fontweight='bold')
    ax4.tick_params(axis='y', labelsize=9)

# Panel 5: Species validation
ax5 = fig.add_subplot(gs[1, 1])
classes = ['beneficial', 'pathogenic', 'neutral']
class_colors = {'beneficial': 'forestgreen', 'pathogenic': 'firebrick', 'neutral': 'gray'}
for c in classes:
    subset = validation[(validation['ground_truth'] == c) & validation['pathogen_ratio'].notna()]
    if len(subset) > 0:
        x = [list(classes).index(c)] * len(subset) + np.random.uniform(-0.1, 0.1, len(subset))
        ax5.scatter(x, subset['pathogen_ratio'], c=class_colors[c], s=60, alpha=0.7,
                    edgecolors='black', linewidth=0.5)
ax5.axhline(0.5, color='black', linestyle='--', alpha=0.3)
ax5.set_xticks(range(len(classes)))
ax5.set_xticklabels(classes)
ax5.set_ylim(-0.05, 1.05)
ax5.set_ylabel('Net pathogenicity ratio')
ax5.set_title('Species-level validation\\n(18 model organisms)', fontweight='bold')

# Panel 6: Within-genus shuffle
ax6 = fig.add_subplot(gs[1, 2])
sh = shuffle.sort_values('perm_p')
sh_names = sh['marker']
colors6 = ['forestgreen' if s else 'gray' for s in sh['significant']]
ax6.barh(sh_names, -np.log10(sh['perm_p'].clip(lower=1e-4)), color=colors6, edgecolor='black', linewidth=0.5)
ax6.axvline(-np.log10(0.05), color='red', linestyle='--', linewidth=0.8)
ax6.set_xlabel('-log10(perm p)')
ax6.set_title('Within-genus shuffle test\\n(strict phylo control)', fontweight='bold')
ax6.tick_params(axis='y', labelsize=8)

plt.suptitle('Phase 2b Final Synthesis: Hypothesis Verdicts After Corrections',
             fontsize=13, fontweight='bold', y=0.995)
plt.savefig(f'{FIG}/final_synthesis.png', dpi=150, bbox_inches='tight')
plt.close()
print(f'Saved: {FIG}/final_synthesis.png')"""
add_code(fig_code, "cell-fig")

# ── Summary ──
add_md("## 6. Summary", "cell-summary-md")

summary = """print('=' * 80)
print('NB15 FINAL SYNTHESIS SUMMARY')
print('=' * 80)
print()
print('Phase 2b successfully addressed 7 of 11 adversarial review issues:')
print('  C1 (phylo control): PARTIAL FIX via L1-regularized logit (9/17 markers)')
print('  C3 (circular validation): FIXED via species-level confusion matrix (77.8%)')
print('  C4 (genome size): FIXED — all 50 OGs survive phylum+gsize control')
print('  I1 (max-aggregation complementarity): FIXED — d: -7.54 → -0.39')
print('  I2 (novel OGs): REFRAMED as "enriched gene families" (all characterized)')
print('  I6 (subclade bug): FIXED — 599 plant genomes recovered, 2/5 species sig')
print('  I7 (genus validation): REPLACED with species-level validation')
print()
print('Documented limitations (remaining):')
print('  C2: PERMANOVA dispersion — documented as upper bound')
print('  I3: T3SS dual interpretation — context-dependent')
print('  I4: Scale-dependent mobilome signals — discussed')
print('  I5: NMDC genus loss — sensitivity future work')
print()
print('Key hypothesis revisions:')
print('  H1: Supported (R²=0.527) → Supported but attenuated (excl top-3: R²=0.072)')
print('  H3: NOT supported (|d|=7.54) → NOT supported (credible magnitude |d|=0.39)')
print('  H7: NOT supported → PARTIALLY SUPPORTED (2/5 species significant)')
print()
print('Outputs:')
for f in ['hypothesis_verdicts_final.csv']:
    path = f'{DATA}/{f}'
    exists = '✓' if os.path.exists(path) else '○'
    print(f'  {exists} data/{f}')
for f in ['final_synthesis.png']:
    path = f'{FIG}/{f}'
    exists = '✓' if os.path.exists(path) else '○'
    print(f'  {exists} figures/{f}')"""
add_code(summary, "cell-summary")

# ── Write notebook ──
nb = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3 (ipykernel)", "language": "python", "name": "python3"},
        "language_info": {"codemirror_mode": {"name": "ipython", "version": 3},
                          "file_extension": ".py", "mimetype": "text/x-python",
                          "name": "python", "nbconvert_exporter": "python",
                          "pygments_lexer": "ipython3", "version": "3.13.9"}
    },
    "nbformat": 4, "nbformat_minor": 5
}

outpath = os.path.join(NB_DIR, '15_final_synthesis.ipynb')
with open(outpath, 'w') as f:
    json.dump(nb, f, indent=1)

# Fix paths to relative
with open(outpath) as f:
    nb = json.load(f)
for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        src = ''.join(cell['source'])
        src = src.replace(DATA, '../data')
        src = src.replace(FIG, '../figures')
        cell['source'] = src.splitlines(True)
        for out in cell.get('outputs', []):
            if out.get('text'):
                out['text'] = [line.replace(DATA, '../data').replace(FIG, '../figures')
                              for line in out['text']]
with open(outpath, 'w') as f:
    json.dump(nb, f, indent=1)

print(f'Wrote: {outpath}')
print(f'Cells: {len(cells)}')

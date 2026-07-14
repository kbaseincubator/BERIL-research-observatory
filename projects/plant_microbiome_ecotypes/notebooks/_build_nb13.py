#!/usr/bin/env python3
"""Build NB13 notebook: Validation, Pfam Recovery & Subclade Fix.

Run the local-only cells and save as .ipynb with outputs.
Spark cells use cache-first pattern.
"""
import json, os, sys, io, traceback
from contextlib import redirect_stdout, redirect_stderr

DATA = '/home/aparkin/BERIL-research-observatory/projects/plant_microbiome_ecotypes/data'
FIG  = '/home/aparkin/BERIL-research-observatory/projects/plant_microbiome_ecotypes/figures'
NB_DIR = '/home/aparkin/BERIL-research-observatory/projects/plant_microbiome_ecotypes/notebooks'

# ── Helper to execute a code cell and capture output ──
def run_cell(source, exec_globals):
    """Execute cell code, return list of notebook output dicts."""
    outputs = []
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    try:
        with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
            exec(source, exec_globals)
        text = stdout_buf.getvalue()
        if text:
            outputs.append({
                "output_type": "stream",
                "name": "stdout",
                "text": text.splitlines(True)
            })
        err = stderr_buf.getvalue()
        if err:
            outputs.append({
                "output_type": "stream",
                "name": "stderr",
                "text": err.splitlines(True)
            })
    except Exception:
        outputs.append({
            "output_type": "stream",
            "name": "stdout",
            "text": stdout_buf.getvalue().splitlines(True)
        })
        tb = traceback.format_exc()
        outputs.append({
            "output_type": "error",
            "ename": "Error",
            "evalue": str(tb.splitlines()[-1]),
            "traceback": tb.splitlines()
        })
    # Check for saved PNG figures
    return outputs

def make_md_cell(source, cell_id):
    return {
        "cell_type": "markdown",
        "id": cell_id,
        "metadata": {},
        "source": source.splitlines(True)
    }

def make_code_cell(source, cell_id, outputs=None, execution_count=None):
    return {
        "cell_type": "code",
        "id": cell_id,
        "metadata": {},
        "source": source.splitlines(True),
        "outputs": outputs or [],
        "execution_count": execution_count
    }

# ── Build cells ──
cells = []
exec_globals = {"__builtins__": __builtins__}
exec_count = [0]

def add_md(source, cell_id):
    cells.append(make_md_cell(source, cell_id))

def add_code(source, cell_id, execute=True):
    exec_count[0] += 1
    if execute:
        outputs = run_cell(source, exec_globals)
        cells.append(make_code_cell(source, cell_id, outputs, exec_count[0]))
    else:
        cells.append(make_code_cell(source, cell_id, [], exec_count[0]))

# ═══════════════════════════════════════════════════════════════════
# CELL 0: Title
# ═══════════════════════════════════════════════════════════════════
add_md("""# NB13 — Validation, Pfam Recovery & Subclade Fix

**Goal**: Address three immediately-fixable adversarial review findings:
- **C3**: Replace tautological genus-level validation with species-level confusion matrix
- **Pfam gap**: Recover Pfam domain hits using LIKE query on versioned IDs
- **I6/NB12 bug**: Fix genome ID prefix mismatch in subclade analysis

**Outputs**:
- `data/species_validation.csv` — Ground-truth validation table
- `data/pfam_recovery_hits.csv` — Recovered Pfam domain hits
- `data/pfam_recovery_impact.csv` — Impact on cohort assignments
- `data/subclade_enrichment_corrected.csv` — Corrected subclade × plant enrichment
- `data/subclade_host_corrected.csv` — Corrected subclade × host mapping
- `figures/species_validation.png`
- `figures/subclade_corrected.png`""", "cell-title")

# ═══════════════════════════════════════════════════════════════════
# CELL 1: Setup
# ═══════════════════════════════════════════════════════════════════
add_md("""## 1. Setup & Data Loading""", "cell-setup-md")

setup_code = f"""import pandas as pd
import numpy as np
import os, warnings
from scipy import stats
from statsmodels.stats.multitest import multipletests

warnings.filterwarnings('ignore')

DATA = '{DATA}'
FIG  = '{FIG}'
os.makedirs(DATA, exist_ok=True)
os.makedirs(FIG, exist_ok=True)

# Load Phase 1/2 data
refined = pd.read_csv(f'{{DATA}}/species_cohort_refined.csv')
markers_v2 = pd.read_csv(f'{{DATA}}/species_marker_matrix_v2.csv')
ge = pd.read_csv(f'{{DATA}}/genome_environment.csv')
sp_comp = pd.read_csv(f'{{DATA}}/species_compartment.csv')
subclades = pd.read_csv(f'{{DATA}}/species_subclade_definitions.csv')

print(f'Refined cohorts: {{len(refined):,}} species')
print(f'Marker matrix v2: {{len(markers_v2):,}} species × {{markers_v2.shape[1]-3}} markers')
print(f'Genomes: {{len(ge):,}}')
print(f'Subclade assignments: {{len(subclades):,}} genomes')
print(f'Subclade species: {{subclades["gtdb_species_clade_id"].nunique()}}')"""

add_code(setup_code, "cell-setup")

# ═══════════════════════════════════════════════════════════════════
# CELL 2: Species-Level Validation (fixes C3)
# ═══════════════════════════════════════════════════════════════════
add_md("""## 2. Species-Level Validation (fixes C3)

Build a curated ground-truth table of ~20 species with experimentally confirmed
phenotypes. Compare against our refined cohort assignments to produce a species-level
confusion matrix, replacing the tautological genus-level validation from NB07.

**Ground truth categories**:
- **Beneficial**: ISR inducers, biocontrol agents, N-fixers (7 species)
- **Pathogenic**: T3SS effector injectors, wilt/rot agents (7 species)
- **Neutral/Non-plant**: Environmental extremophiles, human pathogens (4–6 species)""", "cell-val-md")

validation_code = """# Ground-truth species with experimentally confirmed phenotypes
# Format: (search term for GTDB species name, ground_truth_class, evidence)
ground_truth = [
    # Known Beneficial
    ('Pseudomonas_E simiae', 'beneficial', 'ISR inducer (WCS417)'),
    ('Pseudomonas_E protegens', 'beneficial', 'Biocontrol DAPG/HCN (CHA0)'),
    ('Bacillus velezensis', 'beneficial', 'Biocontrol (FZB42)'),
    ('Azospirillum brasilense', 'beneficial', 'N-fix / IAA (Sp245)'),
    ('Rhizobium leguminosarum', 'beneficial', 'N-fixation'),
    ('Paraburkholderia phytofirmans', 'beneficial', 'ISR (PsJN)'),
    ('Sinorhizobium meliloti', 'beneficial', 'N-fixation'),

    # Known Pathogenic
    ('Pseudomonas_E syringae', 'pathogenic', 'T3SS effectors'),
    ('Ralstonia solanacearum', 'pathogenic', 'Bacterial wilt'),
    ('Xanthomonas campestris', 'pathogenic', 'Black rot'),
    ('Agrobacterium tumefaciens', 'pathogenic', 'Crown gall'),
    ('Erwinia amylovora', 'pathogenic', 'Fire blight'),
    ('Pectobacterium carotovorum', 'pathogenic', 'Soft rot'),
    ('Clavibacter michiganensis', 'pathogenic', 'Bacterial canker'),

    # Known Neutral / Non-plant
    ('Deinococcus radiodurans', 'neutral', 'Radiation-resistant extremophile'),
    ('Thermus thermophilus', 'neutral', 'Thermophile'),
    ('Escherichia coli', 'neutral', 'Lab/gut commensal (K-12)'),
    ('Mycobacterium tuberculosis', 'neutral', 'Human pathogen'),
]

# Look up each species in refined cohort data
results = []
for search_term, gt_class, evidence in ground_truth:
    # Search by partial match on GTDB species name
    # GTDB format: s__Genus_species--RS_GCF_...
    mask = refined['gtdb_species_clade_id'].str.contains(
        search_term.replace(' ', '_'), case=False, na=False)
    matches = refined[mask]

    if len(matches) == 0:
        results.append({
            'search_term': search_term,
            'ground_truth': gt_class,
            'evidence': evidence,
            'n_species_matched': 0,
            'cohort_refined': 'not_found',
            'n_pgp_refined': np.nan,
            'n_pathogen_refined': np.nan,
            'pathogen_ratio': np.nan,
        })
        continue

    # For multi-species matches (e.g., P. syringae has many pathovars),
    # report the most common cohort and aggregate stats
    for _, row in matches.iterrows():
        n_pgp = row['n_pgp_refined']
        n_path = row['n_pathogen_refined']
        total = n_pgp + n_path
        pathogen_ratio = n_path / total if total > 0 else 0.0

        results.append({
            'search_term': search_term,
            'gtdb_species': row['gtdb_species_clade_id'][:60],
            'ground_truth': gt_class,
            'evidence': evidence,
            'cohort_refined': row['cohort_refined'],
            'n_pgp_refined': n_pgp,
            'n_pathogen_refined': n_path,
            'pathogen_ratio': pathogen_ratio,
        })

val_df = pd.DataFrame(results)

# Summarize: one row per ground-truth entry (use first match)
val_summary = val_df.groupby('search_term').first().reset_index()
val_summary = val_summary.sort_values('ground_truth')

print('=== Species-Level Validation Results ===')
print(f'{"Species":<30} {"GT":<12} {"Cohort":<14} {"PGP":>4} {"Path":>4} {"Ratio":>6}')
print('-' * 75)
for _, row in val_summary.iterrows():
    sp = row['search_term'][:29]
    gt = row['ground_truth']
    cohort = row['cohort_refined']
    # Highlight mismatches
    match_flag = ''
    if gt == 'beneficial' and cohort in ('beneficial', 'dual-nature'):
        match_flag = '  ✓'
    elif gt == 'pathogenic' and cohort in ('pathogenic', 'dual-nature'):
        match_flag = '  ✓'
    elif gt == 'neutral' and cohort == 'neutral':
        match_flag = '  ✓'
    elif cohort == 'not_found':
        match_flag = '  ?'
    else:
        match_flag = '  ✗'

    pgp = f"{row['n_pgp_refined']:.0f}" if not np.isnan(row['n_pgp_refined']) else '-'
    path = f"{row['n_pathogen_refined']:.0f}" if not np.isnan(row['n_pathogen_refined']) else '-'
    ratio = f"{row['pathogen_ratio']:.2f}" if not np.isnan(row['pathogen_ratio']) else '-'
    print(f'{sp:<30} {gt:<12} {cohort:<14} {pgp:>4} {path:>4} {ratio:>6}{match_flag}')

# Mann-Whitney U: beneficial vs pathogenic pathogen ratio
ben_ratios = val_summary[val_summary['ground_truth'] == 'beneficial']['pathogen_ratio'].dropna()
path_ratios = val_summary[val_summary['ground_truth'] == 'pathogenic']['pathogen_ratio'].dropna()

if len(ben_ratios) > 0 and len(path_ratios) > 0:
    u_stat, u_p = stats.mannwhitneyu(ben_ratios, path_ratios, alternative='less')
    print(f'\\nMann-Whitney U (beneficial < pathogenic pathogen ratio):')
    print(f'  Beneficial median ratio: {ben_ratios.median():.3f} (n={len(ben_ratios)})')
    print(f'  Pathogenic median ratio: {path_ratios.median():.3f} (n={len(path_ratios)})')
    print(f'  U={u_stat:.0f}, p={u_p:.2e}')

# Confusion matrix
print('\\n=== Confusion Matrix ===')
print('Ground truth vs refined cohort assignment:')

# For confusion matrix, define "correct" classification
# beneficial → beneficial or dual-nature is OK (dual-nature means PGP present)
# pathogenic → pathogenic or dual-nature is OK (dual-nature means pathogen present)
# neutral → neutral is correct; anything else is false positive

# Stricter view: exact match only
found = val_summary[val_summary['cohort_refined'] != 'not_found'].copy()
if len(found) > 0:
    strict_cm = pd.crosstab(found['ground_truth'], found['cohort_refined'],
                             margins=True, margins_name='Total')
    print(strict_cm)

    # Accuracy metrics
    n_correct_strict = sum(
        (found['ground_truth'] == 'beneficial') & (found['cohort_refined'] == 'beneficial') |
        (found['ground_truth'] == 'pathogenic') & (found['cohort_refined'] == 'pathogenic') |
        (found['ground_truth'] == 'neutral') & (found['cohort_refined'] == 'neutral')
    )
    n_correct_relaxed = sum(
        (found['ground_truth'] == 'beneficial') & (found['cohort_refined'].isin(['beneficial', 'dual-nature'])) |
        (found['ground_truth'] == 'pathogenic') & (found['cohort_refined'].isin(['pathogenic', 'dual-nature'])) |
        (found['ground_truth'] == 'neutral') & (found['cohort_refined'] == 'neutral')
    )
    print(f'\\nStrict accuracy (exact match): {n_correct_strict}/{len(found)} = {n_correct_strict/len(found):.1%}')
    print(f'Relaxed accuracy (dual-nature OK for ben/path): {n_correct_relaxed}/{len(found)} = {n_correct_relaxed/len(found):.1%}')

# Save validation results
val_summary.to_csv(f'{DATA}/species_validation.csv', index=False)
print(f'\\nSaved: {DATA}/species_validation.csv')

# Figure: dot plot of pathogen ratio by ground-truth class
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

fig, ax = plt.subplots(1, 1, figsize=(8, 5))

colors = {'beneficial': 'forestgreen', 'pathogenic': 'firebrick', 'neutral': 'gray'}
for gt_class in ['beneficial', 'pathogenic', 'neutral']:
    subset = val_summary[val_summary['ground_truth'] == gt_class]
    subset_valid = subset[subset['pathogen_ratio'].notna()]
    if len(subset_valid) > 0:
        jitter = np.random.uniform(-0.1, 0.1, len(subset_valid))
        x_pos = {'beneficial': 0, 'pathogenic': 1, 'neutral': 2}[gt_class]
        ax.scatter(x_pos + jitter, subset_valid['pathogen_ratio'],
                  c=colors[gt_class], s=80, alpha=0.7, edgecolors='black', linewidth=0.5,
                  label=f'{gt_class} (n={len(subset_valid)})', zorder=3)

ax.set_xticks([0, 1, 2])
ax.set_xticklabels(['Beneficial\\n(known PGPB)', 'Pathogenic\\n(known pathogens)',
                     'Neutral\\n(non-plant)'])
ax.set_ylabel('Net Pathogenicity Ratio\\n(n_pathogen / (n_pgp + n_pathogen))')
ax.set_title('Species-Level Validation: Pathogen Ratio by Ground-Truth Class')
ax.legend(loc='upper left')
ax.set_ylim(-0.05, 1.05)
ax.axhline(0.5, color='gray', linestyle='--', alpha=0.3)
ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig(f'{FIG}/species_validation.png', dpi=150, bbox_inches='tight')
plt.close()
print(f'Saved: {FIG}/species_validation.png')"""

add_code(validation_code, "cell-validation")

# ═══════════════════════════════════════════════════════════════════
# CELL 3: Pfam Recovery (needs Spark or cache)
# ═══════════════════════════════════════════════════════════════════
add_md("""## 3. Pfam Recovery via LIKE Query (fixes Pfam gap)

NB02 queried `bakta_pfam_domains` with bare Pfam accessions (e.g., `PF00771`)
but the table stores versioned IDs (e.g., `PF00771.22`), yielding 0 hits.

**Fix**: Use `LIKE` patterns to match versioned IDs. Query 10 key marker Pfam IDs
covering T3SS, T4SS, T6SS, CWDEs, and nitrogenase.

**Note**: This cell requires Spark. If running locally, it loads from cache.""", "cell-pfam-md")

pfam_code = f"""CACHE_PFAM = f'{{DATA}}/pfam_recovery_hits.csv'

if os.path.exists(CACHE_PFAM) and os.path.getsize(CACHE_PFAM) > 100:
    pfam_hits = pd.read_csv(CACHE_PFAM)
    print(f'Loaded cached Pfam recovery: {{len(pfam_hits):,}} hits')
else:
    # ── Requires Spark session ──
    try:
        spark = get_spark_session()
    except NameError:
        print('ERROR: Spark not available. Run this cell on the BERDL JupyterHub.')
        print('Skipping Pfam recovery — will be empty until executed on cluster.')
        pfam_hits = pd.DataFrame(columns=[
            'gene_cluster_id', 'pfam_id', 'gtdb_species_clade_id', 'is_core'])
        pfam_hits.to_csv(CACHE_PFAM, index=False)
        spark = None

    if spark is not None:
        pfam_hits = spark.sql(\"\"\"
        SELECT bpf.gene_cluster_id, bpf.pfam_id,
               gc.gtdb_species_clade_id, gc.is_core
        FROM kbase_ke_pangenome.bakta_pfam_domains bpf
        JOIN kbase_ke_pangenome.gene_cluster gc
             ON bpf.gene_cluster_id = gc.gene_cluster_id
        WHERE bpf.pfam_id LIKE 'PF00771%'   -- T3SS inner rod (PrgJ)
           OR bpf.pfam_id LIKE 'PF01313%'   -- T3SS PrgH
           OR bpf.pfam_id LIKE 'PF01514%'   -- Secretin (T2SS/T3SS)
           OR bpf.pfam_id LIKE 'PF03135%'   -- VirB8 (T4SS)
           OR bpf.pfam_id LIKE 'PF05936%'   -- Hcp (T6SS tube)
           OR bpf.pfam_id LIKE 'PF05943%'   -- VgrG (T6SS spike)
           OR bpf.pfam_id LIKE 'PF00544%'   -- Pectate lyase
           OR bpf.pfam_id LIKE 'PF12708%'   -- Pectate lyase 3
           OR bpf.pfam_id LIKE 'PF00150%'   -- Cellulase GH5
           OR bpf.pfam_id LIKE 'PF00142%'   -- Nitrogenase NifH
        \"\"\").toPandas()

        pfam_hits.to_csv(CACHE_PFAM, index=False)
        print(f'Saved: {{CACHE_PFAM}} ({{len(pfam_hits):,}} hits)')

# Summarize by Pfam ID
if len(pfam_hits) > 0:
    pfam_bare = pfam_hits['pfam_id'].str.extract(r'(PF\\d+)', expand=False)
    pfam_hits['pfam_bare'] = pfam_bare

    pfam_labels = {{
        'PF00771': 'T3SS inner rod (PrgJ)',
        'PF01313': 'T3SS PrgH',
        'PF01514': 'Secretin (T2SS/T3SS)',
        'PF03135': 'VirB8 (T4SS)',
        'PF05936': 'Hcp (T6SS tube)',
        'PF05943': 'VgrG (T6SS spike)',
        'PF00544': 'Pectate lyase',
        'PF12708': 'Pectate lyase 3',
        'PF00150': 'Cellulase GH5',
        'PF00142': 'Nitrogenase NifH',
    }}

    print('\\n=== Pfam Recovery Results ===')
    print(f'{{"Pfam ID":<12}} {{"Description":<25}} {{"Hits":>8}} {{"Species":>8}} {{"Core %":>7}}')
    for pfam_id, desc in pfam_labels.items():
        subset = pfam_hits[pfam_hits['pfam_bare'] == pfam_id]
        if len(subset) > 0:
            n_species = subset['gtdb_species_clade_id'].nunique()
            core_frac = subset['is_core'].mean() * 100
            print(f'{{pfam_id:<12}} {{desc:<25}} {{len(subset):>8,}} {{n_species:>8,}} {{core_frac:>6.1f}}%')
        else:
            print(f'{{pfam_id:<12}} {{desc:<25}} {{0:>8}} {{0:>8}}     -')

    print(f'\\nTotal: {{len(pfam_hits):,}} domain hits across '
          f'{{pfam_hits["gtdb_species_clade_id"].nunique():,}} species')

    # Impact assessment: how many species gain markers?
    pfam_species = pfam_hits.groupby('gtdb_species_clade_id')['pfam_bare'].apply(set).reset_index()
    pfam_species.columns = ['gtdb_species_clade_id', 'pfam_ids']

    # Map to marker categories
    pfam_to_marker = {{
        'PF00771': 't3ss', 'PF01313': 't3ss', 'PF01514': 't3ss',
        'PF03135': 't4ss',
        'PF05936': 't6ss', 'PF05943': 't6ss',
        'PF00544': 'cwde_pectinase', 'PF12708': 'cwde_pectinase',
        'PF00150': 'cwde_cellulase',
        'PF00142': 'nitrogen_fixation',
    }}

    impact = pfam_species.merge(
        markers_v2[['gtdb_species_clade_id', 't3ss_present', 't4ss_present',
                     'cwde_cellulase_present', 'cwde_pectinase_present',
                     'nitrogen_fixation_present']],
        on='gtdb_species_clade_id', how='left')

    # Count species that would gain new markers from Pfam recovery
    def check_new_markers(row):
        new = set()
        pfams = row['pfam_ids']
        for pfam_id in pfams:
            marker = pfam_to_marker.get(pfam_id, '')
            if marker == 't3ss' and row.get('t3ss_present', 0) == 0:
                new.add('t3ss')
            elif marker == 't4ss' and row.get('t4ss_present', 0) == 0:
                new.add('t4ss')
            elif marker == 'cwde_cellulase' and row.get('cwde_cellulase_present', 0) == 0:
                new.add('cwde_cellulase')
            elif marker == 'cwde_pectinase' and row.get('cwde_pectinase_present', 0) == 0:
                new.add('cwde_pectinase')
            elif marker == 'nitrogen_fixation' and row.get('nitrogen_fixation_present', 0) == 0:
                new.add('nitrogen_fixation')
        return new

    impact['new_markers'] = impact.apply(check_new_markers, axis=1)
    impact['n_new_markers'] = impact['new_markers'].apply(len)
    gained = impact[impact['n_new_markers'] > 0]

    print(f'\\n=== Impact on Cohort Assignments ===')
    print(f'Species with Pfam hits: {{len(impact):,}}')
    print(f'Species gaining NEW markers from Pfam recovery: {{len(gained):,}}')
    if len(gained) > 0:
        for marker in ['t3ss', 't4ss', 'cwde_cellulase', 'cwde_pectinase', 'nitrogen_fixation']:
            n = sum(gained['new_markers'].apply(lambda s: marker in s))
            if n > 0:
                print(f'  Gaining {{marker}}: {{n}} species')

    # Save impact
    impact_out = impact[['gtdb_species_clade_id', 'n_new_markers']].copy()
    impact_out['new_markers_list'] = impact['new_markers'].apply(lambda s: ','.join(sorted(s)))
    impact_out.to_csv(f'{{DATA}}/pfam_recovery_impact.csv', index=False)
    print(f'\\nSaved: {{DATA}}/pfam_recovery_impact.csv')
else:
    print('No Pfam hits found (run on cluster to execute Spark query)')"""

add_code(pfam_code, "cell-pfam")

# ═══════════════════════════════════════════════════════════════════
# CELL 4: Subclade Genome ID Fix (fixes NB12 bug)
# ═══════════════════════════════════════════════════════════════════
add_md("""## 4. Subclade Genome ID Fix (fixes NB12 bug / I6)

NB12 found 0 plant-associated genomes in subclades because genome IDs from
`phylogenetic_tree_distance_pairs` use bare NCBI accessions (e.g., `GCA_005059785.1`)
while `genome_environment.csv` uses GTDB-prefixed IDs (e.g., `GB_GCA_005059785.1`
or `RS_GCF_...`).

**Fix**: Add `GB_` prefix for `GCA_` IDs and `RS_` prefix for `GCF_` IDs, then re-merge.""", "cell-subclade-md")

subclade_code = """# Load subclade definitions
subclades = pd.read_csv(f'{DATA}/species_subclade_definitions.csv')
print(f'Subclade assignments: {len(subclades):,} genomes')
print(f'Species: {subclades["gtdb_species_clade_id"].nunique()}')

# Show the genome ID format mismatch
print(f'\\nSubclade genome ID examples:')
for gid in subclades['genome_id'].head(3):
    print(f'  {gid}')
print(f'\\nGenome environment ID examples:')
for gid in ge['genome_id'].head(3):
    print(f'  {gid}')

# Fix: map bare NCBI accessions to GTDB-prefixed IDs
def fix_genome_id(gid):
    if gid.startswith('GCA_'):
        return 'GB_' + gid
    elif gid.startswith('GCF_'):
        return 'RS_' + gid
    return gid

subclades['genome_id_fixed'] = subclades['genome_id'].apply(fix_genome_id)

# Verify fix by checking overlap
original_overlap = subclades['genome_id'].isin(ge['genome_id']).sum()
fixed_overlap = subclades['genome_id_fixed'].isin(ge['genome_id']).sum()
print(f'\\nGenome ID overlap with environment data:')
print(f'  Before fix: {original_overlap}/{len(subclades)} ({original_overlap/len(subclades):.1%})')
print(f'  After fix:  {fixed_overlap}/{len(subclades)} ({fixed_overlap/len(subclades):.1%})')

# Re-merge with environment data
subclades_fixed = subclades.drop(columns=['is_plant_associated', 'compartment', 'host_species'],
                                  errors='ignore')
subclades_fixed = subclades_fixed.merge(
    ge[['genome_id', 'is_plant_associated', 'compartment']],
    left_on='genome_id_fixed', right_on='genome_id',
    how='left', suffixes=('_orig', ''))

# Also merge host data
host_genomes = pd.read_csv(f'{DATA}/genome_host_species.csv')
subclades_fixed = subclades_fixed.merge(
    host_genomes[['genome_id', 'host_species']].drop_duplicates(),
    left_on='genome_id_fixed', right_on='genome_id',
    how='left', suffixes=('', '_host'))

# Report corrected plant-association status
print(f'\\n=== Corrected Subclade Plant-Association ===')
for sp_id in subclades_fixed['gtdb_species_clade_id'].unique():
    sp_data = subclades_fixed[subclades_fixed['gtdb_species_clade_id'] == sp_id]
    n_plant = (sp_data['is_plant_associated'] == 1).sum()
    n_total = len(sp_data)
    sp_short = sp_id.split('--')[0].replace('s__', '')
    print(f'  {sp_short:<40} {n_total:>4} genomes, {n_plant:>4} plant ({n_plant/n_total:.0%})')

# Re-run Fisher's exact test for subclade × plant-association enrichment
print(f'\\n=== Subclade × Plant-Association Enrichment (Corrected) ===')
enrichment_results = []

for sp_id in subclades_fixed['gtdb_species_clade_id'].unique():
    sp_data = subclades_fixed[subclades_fixed['gtdb_species_clade_id'] == sp_id]
    n_subclades = sp_data['subclade'].nunique()

    # Plant-associated count
    sp_data = sp_data.copy()
    sp_data['is_plant'] = (sp_data['is_plant_associated'] == 1)
    total_plant = sp_data['is_plant'].sum()
    total_nonplant = len(sp_data) - total_plant

    if n_subclades < 2 or total_plant < 3 or total_nonplant < 3:
        enrichment_results.append({
            'species': sp_id,
            'n_genomes': len(sp_data),
            'n_subclades': n_subclades,
            'n_plant': total_plant,
            'n_nonplant': total_nonplant,
            'best_subclade': -1,
            'best_plant_frac': np.nan,
            'fisher_p': np.nan,
            'chi2_p': np.nan,
            'testable': total_plant >= 3 and total_nonplant >= 3,
        })
        continue

    # Chi-square test
    contingency = pd.crosstab(sp_data['subclade'], sp_data['is_plant'])
    if contingency.shape[1] < 2:
        enrichment_results.append({
            'species': sp_id,
            'n_genomes': len(sp_data),
            'n_subclades': n_subclades,
            'n_plant': total_plant,
            'n_nonplant': total_nonplant,
            'best_subclade': -1,
            'best_plant_frac': np.nan,
            'fisher_p': np.nan,
            'chi2_p': np.nan,
            'testable': False,
        })
        continue

    chi2, chi2_p, _, _ = stats.chi2_contingency(contingency)

    # Find most plant-enriched subclade
    subclade_stats = []
    for sc in sp_data['subclade'].unique():
        sub = sp_data[sp_data['subclade'] == sc]
        n_sc_plant = sub['is_plant'].sum()
        frac = n_sc_plant / len(sub) if len(sub) > 0 else 0
        subclade_stats.append((sc, len(sub), n_sc_plant, frac))

    best_sc = max(subclade_stats, key=lambda x: x[3])

    # Fisher's exact for most enriched subclade vs rest
    a = best_sc[2]
    b = best_sc[1] - best_sc[2]
    c = total_plant - a
    d = total_nonplant - b
    _, fisher_p = stats.fisher_exact([[a, b], [c, d]])

    enrichment_results.append({
        'species': sp_id,
        'n_genomes': len(sp_data),
        'n_subclades': n_subclades,
        'n_plant': total_plant,
        'n_nonplant': total_nonplant,
        'best_subclade': best_sc[0],
        'best_plant_frac': best_sc[3],
        'fisher_p': fisher_p,
        'chi2_p': chi2_p,
        'testable': True,
    })

enrichment_df = pd.DataFrame(enrichment_results)

print(f'{"Species":<45} {"N":>4} {"SC":>3} {"Plant":>5} {"NonP":>5} {"Best%":>6} {"Fisher":>10} {"Chi2":>10}')
print('-' * 100)
for _, row in enrichment_df.iterrows():
    sp_short = row['species'].split('--')[0].replace('s__', '')[:44]
    best_pct = f"{row['best_plant_frac']:.0%}" if not np.isnan(row.get('best_plant_frac', np.nan)) else '-'
    fisher = f"{row['fisher_p']:.2e}" if not np.isnan(row.get('fisher_p', np.nan)) else '-'
    chi2 = f"{row['chi2_p']:.2e}" if not np.isnan(row.get('chi2_p', np.nan)) else '-'
    print(f'{sp_short:<45} {row["n_genomes"]:>4} {row["n_subclades"]:>3} '
          f'{row["n_plant"]:>5.0f} {row["n_nonplant"]:>5.0f} {best_pct:>6} {fisher:>10} {chi2:>10}')

testable = enrichment_df[enrichment_df['testable']]
sig = testable[testable['chi2_p'] < 0.05] if len(testable) > 0 else pd.DataFrame()
print(f'\\nTestable species (≥3 plant + ≥3 non-plant): {len(testable)}')
print(f'Significant subclade × plant enrichment (chi2 p<0.05): {len(sig)}')

enrichment_df.to_csv(f'{DATA}/subclade_enrichment_corrected.csv', index=False)
print(f'\\nSaved: {DATA}/subclade_enrichment_corrected.csv')

# Host × subclade mapping (corrected)
host_results = []
for sp_id in subclades_fixed['gtdb_species_clade_id'].unique():
    sp_data = subclades_fixed[subclades_fixed['gtdb_species_clade_id'] == sp_id]
    with_host = sp_data[sp_data['host_species'].notna()]

    if len(with_host) < 5 or with_host['host_species'].nunique() < 2:
        continue

    ct = pd.crosstab(with_host['subclade'], with_host['host_species'])
    if ct.shape[0] >= 2 and ct.shape[1] >= 2:
        chi2, p, _, _ = stats.chi2_contingency(ct)
        host_results.append({
            'species': sp_id,
            'n_with_host': len(with_host),
            'n_hosts': with_host['host_species'].nunique(),
            'chi2_p': p,
        })

host_df = pd.DataFrame(host_results)
if len(host_df) > 0:
    print(f'\\n=== Subclade × Host Associations (Corrected) ===')
    for _, row in host_df.sort_values('chi2_p').iterrows():
        sig_mark = '*' if row['chi2_p'] < 0.05 else ''
        sp_short = row['species'].split('--')[0].replace('s__', '')
        print(f'  {sp_short}: {row["n_with_host"]} genomes, {row["n_hosts"]} hosts, '
              f'chi2 p={row["chi2_p"]:.3e} {sig_mark}')
    host_df.to_csv(f'{DATA}/subclade_host_corrected.csv', index=False)
    print(f'Saved: {DATA}/subclade_host_corrected.csv')
else:
    print(f'\\nNo species had sufficient host data for subclade × host analysis')
    pd.DataFrame().to_csv(f'{DATA}/subclade_host_corrected.csv', index=False)

# Visualization: MDS colored by corrected plant-association status
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

species_list = subclades_fixed['gtdb_species_clade_id'].unique()
n_species = len(species_list)

fig, axes = plt.subplots(1, n_species, figsize=(5 * n_species, 5))
if n_species == 1:
    axes = [axes]

for i, sp_id in enumerate(species_list):
    sp_data = subclades_fixed[subclades_fixed['gtdb_species_clade_id'] == sp_id]

    for sc in sorted(sp_data['subclade'].unique()):
        sc_data = sp_data[sp_data['subclade'] == sc]
        plant = sc_data[sc_data['is_plant_associated'] == 1]
        nonplant = sc_data[sc_data['is_plant_associated'] != 1]

        marker_shapes = ['o', 's', '^', 'D', 'v']
        m = marker_shapes[sc % 5]

        if len(plant) > 0:
            axes[i].scatter(plant['mds1'], plant['mds2'],
                           marker=m, c='forestgreen', alpha=0.6, s=30, zorder=3)
        if len(nonplant) > 0:
            axes[i].scatter(nonplant['mds1'], nonplant['mds2'],
                           marker=m, c='gray', alpha=0.4, s=30, zorder=2)

    sp_short = sp_id.split('--')[0].replace('s__', '').replace('_', ' ')
    n_plant = (sp_data['is_plant_associated'] == 1).sum()
    axes[i].set_title(f'{sp_short}\\n{len(sp_data)} genomes ({n_plant} plant)', fontsize=9)
    axes[i].set_xlabel('MDS1')
    if i == 0:
        axes[i].set_ylabel('MDS2')

legend_elements = [
    Line2D([0], [0], marker='o', color='w', markerfacecolor='forestgreen', markersize=8, label='Plant'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='gray', markersize=8, label='Non-plant'),
]
axes[-1].legend(handles=legend_elements, loc='lower right', fontsize=8)

plt.suptitle('Subclade Analysis — Corrected Genome ID Mapping', fontsize=12, y=1.02)
plt.tight_layout()
plt.savefig(f'{FIG}/subclade_corrected.png', dpi=150, bbox_inches='tight')
plt.close()
print(f'\\nSaved: {FIG}/subclade_corrected.png')"""

add_code(subclade_code, "cell-subclade")

# ═══════════════════════════════════════════════════════════════════
# CELL 5: Summary
# ═══════════════════════════════════════════════════════════════════
add_md("""## 5. Summary & Impact Assessment""", "cell-summary-md")

summary_code = """print('=' * 80)
print('NB13 SUMMARY: Validation, Pfam Recovery & Subclade Fix')
print('=' * 80)

# C3: Species-level validation
val = pd.read_csv(f'{DATA}/species_validation.csv')
n_found = (val['cohort_refined'] != 'not_found').sum()
n_total = len(val)
print(f'\\n1. Species-Level Validation (C3 fix)')
print(f'   Ground-truth species: {n_total}')
print(f'   Found in refined cohorts: {n_found}')
ben = val[val['ground_truth'] == 'beneficial']
path = val[val['ground_truth'] == 'pathogenic']
neut = val[val['ground_truth'] == 'neutral']
ben_correct = ben[ben['cohort_refined'].isin(['beneficial', 'dual-nature'])]
path_correct = path[path['cohort_refined'].isin(['pathogenic', 'dual-nature'])]
neut_correct = neut[neut['cohort_refined'] == 'neutral']
print(f'   Beneficial correctly classified: {len(ben_correct)}/{len(ben)}')
print(f'   Pathogenic correctly classified: {len(path_correct)}/{len(path)}')
print(f'   Neutral correctly classified: {len(neut_correct)}/{len(neut)}')

# Pfam recovery
pfam_file = f'{DATA}/pfam_recovery_hits.csv'
if os.path.exists(pfam_file) and os.path.getsize(pfam_file) > 100:
    pfam = pd.read_csv(pfam_file)
    print(f'\\n2. Pfam Recovery')
    print(f'   Domain hits recovered: {len(pfam):,}')
    print(f'   Species with hits: {pfam["gtdb_species_clade_id"].nunique():,}')
else:
    print(f'\\n2. Pfam Recovery: PENDING (requires Spark execution)')

# Subclade fix
enr = pd.read_csv(f'{DATA}/subclade_enrichment_corrected.csv')
testable = enr[enr['testable'] == True]
sig = testable[testable['chi2_p'] < 0.05] if len(testable) > 0 else pd.DataFrame()
total_plant = enr['n_plant'].sum()
print(f'\\n3. Subclade Fix (I6)')
print(f'   Plant-associated genomes in subclades: {total_plant:.0f} (was 0 before fix)')
print(f'   Testable species: {len(testable)}')
print(f'   Significant enrichments: {len(sig)}')
if len(sig) > 0:
    print(f'   → H7 revision: subclade segregation detected')
else:
    if len(testable) > 0:
        print(f'   → H7 still NOT supported: plant genomes distributed across subclades')
    else:
        print(f'   → H7 untestable: insufficient plant/non-plant balance')

print(f'\\nOutputs:')
for f in ['species_validation.csv', 'pfam_recovery_hits.csv', 'pfam_recovery_impact.csv',
          'subclade_enrichment_corrected.csv', 'subclade_host_corrected.csv']:
    path = f'{DATA}/{f}'
    exists = '✓' if os.path.exists(path) and os.path.getsize(path) > 0 else '○'
    print(f'  {exists} data/{f}')
for f in ['species_validation.png', 'subclade_corrected.png']:
    path = f'{FIG}/{f}'
    exists = '✓' if os.path.exists(path) else '○'
    print(f'  {exists} figures/{f}')"""

add_code(summary_code, "cell-summary")

# ═══════════════════════════════════════════════════════════════════
# Build notebook JSON
# ═══════════════════════════════════════════════════════════════════
notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3 (ipykernel)",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "codemirror_mode": {"name": "ipython", "version": 3},
            "file_extension": ".py",
            "mimetype": "text/x-python",
            "name": "python",
            "nbconvert_exporter": "python",
            "pygments_lexer": "ipython3",
            "version": "3.13.9"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 5
}

outpath = os.path.join(NB_DIR, '13_validation_pfam_subclade.ipynb')
with open(outpath, 'w') as f:
    json.dump(notebook, f, indent=1)
print(f'Wrote: {outpath}')
print(f'Cells: {len(cells)} ({sum(1 for c in cells if c["cell_type"]=="code")} code, '
      f'{sum(1 for c in cells if c["cell_type"]=="markdown")} markdown)')

#!/usr/bin/env python3
"""Build the 3 analysis notebooks as .ipynb files with markdown narrative."""

import nbformat as nbf
from pathlib import Path

NB_DIR = Path(__file__).resolve().parent.parent / 'notebooks'

def md(text):
    """Create a markdown cell."""
    return nbf.v4.new_markdown_cell(text.strip())

def code(text):
    """Create a code cell."""
    return nbf.v4.new_code_cell(text.strip())

# ============================================================================
# NB02: Essential Gene Families
# ============================================================================
nb02 = nbf.v4.new_notebook()
nb02.metadata['kernelspec'] = {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'}
nb02.cells = [
    md("""# NB02: Essential Gene Families

Classify ortholog families by essentiality pattern across 48 Fitness Browser organisms.

**Input**: `data/all_essential_genes.tsv`, `data/all_ortholog_groups.csv` (from `src/extract_data.py`)
**Output**: `data/essential_families.tsv`, figures"""),

    code("""import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

DATA_DIR = Path('../data')
FIG_DIR = Path('../figures')
FIG_DIR.mkdir(parents=True, exist_ok=True)

essential = pd.read_csv(DATA_DIR / 'all_essential_genes.tsv', sep='\\t', low_memory=False)
essential['is_essential'] = essential['is_essential'].astype(str).str.strip().str.lower() == 'true'
essential['locusId'] = essential['locusId'].astype(str)

og_df = pd.read_csv(DATA_DIR / 'all_ortholog_groups.csv')
og_df['locusId'] = og_df['locusId'].astype(str)

seed_ann = pd.read_csv(DATA_DIR / 'all_seed_annotations.tsv', sep='\\t')

# SEED hierarchy from upstream project
seed_hier_path = Path('../../conservation_vs_fitness/data/seed_hierarchy.tsv')
seed_hier = pd.read_csv(seed_hier_path, sep='\\t') if seed_hier_path.exists() else None

print(f"Genes: {len(essential):,} ({essential['is_essential'].sum():,} essential, {essential['is_essential'].mean()*100:.1f}%)")
print(f"Ortholog groups: {og_df['OG_id'].nunique():,}")
print(f"Organisms: {essential['orgId'].nunique()}")"""),

    md("## Merge essentiality with ortholog groups"),

    code("""# Merge OG membership into essential gene table
merged = og_df.merge(
    essential[['orgId', 'locusId', 'is_essential', 'gene', 'desc', 'gene_length']],
    on=['orgId', 'locusId'], how='left'
)

# Tag genes that have orthologs
og_keys = og_df[['orgId', 'locusId']].drop_duplicates()
og_keys['in_og'] = True
essential = essential.merge(og_keys, on=['orgId', 'locusId'], how='left')
essential['in_og'] = essential['in_og'].fillna(False).astype(bool)

assert essential['in_og'].sum() > 30000, f"in_og merge failed: only {essential['in_og'].sum()} matches"
assert len(essential) == 221005, f"Merge created duplicates: {len(essential)}"

ess_in_og = essential[essential['is_essential'] & essential['in_og']]
ess_not_in_og = essential[essential['is_essential'] & ~essential['in_og']]

print(f"Genes with orthologs: {essential['in_og'].sum():,} / {len(essential):,}")
print(f"Essential with orthologs: {len(ess_in_og):,}")
print(f"Essential orphans (no orthologs): {len(ess_not_in_og):,}")"""),

    md("""## Classify ortholog families

For each ortholog group, determine:
- How many organisms have essential members vs non-essential
- **Universally essential**: essential in ALL organisms where family has members
- **Variably essential**: essential in some, non-essential in others
- **Never essential**: no essential members"""),

    code("""family_stats = []
for og_id, group in merged.groupby('OG_id'):
    with_status = group[group['is_essential'].notna()].copy()
    if len(with_status) == 0:
        continue
    with_status['is_essential'] = with_status['is_essential'].astype(bool)

    n_organisms = with_status['orgId'].nunique()
    n_essential = with_status[with_status['is_essential'] == True]['orgId'].nunique()
    n_nonessential = with_status[with_status['is_essential'] == False]['orgId'].nunique()
    n_genes = len(with_status)
    n_ess_genes = (with_status['is_essential'] == True).sum()

    descs = with_status['desc'].dropna().unique()
    non_hyp = [d for d in descs if 'hypothetical' not in str(d).lower()]
    rep_desc = non_hyp[0] if non_hyp else (descs[0] if len(descs) > 0 else 'unknown')
    gene_names = [g for g in with_status['gene'].dropna().unique() if g and str(g) != 'nan']
    rep_gene = gene_names[0] if gene_names else ''

    if n_essential == n_organisms:
        ess_class = 'universally_essential'
    elif n_essential > 0:
        ess_class = 'variably_essential'
    else:
        ess_class = 'never_essential'

    ess_orgs = sorted(with_status[with_status['is_essential'] == True]['orgId'].unique())
    noness_orgs = sorted(with_status[with_status['is_essential'] == False]['orgId'].unique())

    family_stats.append({
        'OG_id': og_id, 'n_organisms': n_organisms,
        'n_essential_organisms': n_essential, 'n_nonessential_organisms': n_nonessential,
        'n_genes': n_genes, 'n_essential_genes': int(n_ess_genes),
        'frac_essential': n_essential / n_organisms,
        'essentiality_class': ess_class, 'rep_gene': rep_gene, 'rep_desc': rep_desc,
        'essential_organisms': ';'.join(ess_orgs),
        'nonessential_organisms': ';'.join(noness_orgs),
    })

families = pd.DataFrame(family_stats)
families['copy_ratio'] = families['n_genes'] / families['n_organisms']
families['is_single_copy'] = (families['copy_ratio'] <= 1.5) & (families['n_nonessential_organisms'] == 0)

families.to_csv(DATA_DIR / 'essential_families.tsv', sep='\\t', index=False)
print(f"Classified {len(families):,} ortholog families")"""),

    md("## Family classification summary"),

    code("""class_counts = families['essentiality_class'].value_counts()
for cls, count in class_counts.items():
    print(f"  {cls}: {count:,} ({count/len(families)*100:.1f}%)")

univ = families[families['essentiality_class'] == 'universally_essential']
print(f"\\nUniversally essential: {len(univ)} total")
print(f"  Single-copy (strict): {univ['is_single_copy'].sum()}")
print(f"  Multi-copy/paralog: {len(univ) - univ['is_single_copy'].sum()}")
print(f"  Essential in ALL 48 organisms: {(univ['n_organisms'] == 48).sum()}")"""),

    md("## Top 30 universally essential families"),

    code("""top = univ.sort_values('n_organisms', ascending=False).head(30)
display_df = top[['OG_id', 'n_organisms', 'rep_gene', 'rep_desc', 'copy_ratio']].copy()
display_df.columns = ['OG', 'Organisms', 'Gene', 'Description', 'Copy ratio']
display_df['Description'] = display_df['Description'].str[:55]
display_df"""),

    md("## Variably essential families"),

    code("""var_ess = families[families['essentiality_class'] == 'variably_essential']
print(f"Variably essential: {len(var_ess):,}")
print(f"  Spanning 10+ organisms: {(var_ess['n_organisms'] >= 10).sum():,}")
print(f"  Spanning 20+ organisms: {(var_ess['n_organisms'] >= 20).sum():,}")
print(f"\\nEssentiality penetrance:")
print(f"  Mean: {var_ess['frac_essential'].mean():.3f}")
print(f"  Median: {var_ess['frac_essential'].median():.3f}")
print(f"  >50% essential: {(var_ess['frac_essential'] > 0.5).sum():,}")
print(f"  <10% essential: {(var_ess['frac_essential'] < 0.1).sum():,}")"""),

    md("## Functional characterization"),

    code("""# Hypothetical fraction by class
gene_family_class = merged.merge(families[['OG_id', 'essentiality_class']], on='OG_id', how='left')

for cls in ['universally_essential', 'variably_essential', 'never_essential']:
    subset = gene_family_class[gene_family_class['essentiality_class'] == cls]
    n_hyp = subset['desc'].str.contains('hypothetical', case=False, na=False).sum()
    print(f"{cls}: {len(subset):,} genes, {n_hyp/len(subset)*100:.1f}% hypothetical")

n_hyp_orphan = ess_not_in_og['desc'].str.contains('hypothetical', case=False, na=False).sum()
print(f"orphan_essential: {len(ess_not_in_og):,} genes, {n_hyp_orphan/len(ess_not_in_og)*100:.1f}% hypothetical")"""),

    md("## Gene length by essentiality"),

    code("""print(f"Essential median length: {essential[essential['is_essential']]['gene_length'].median():.0f} bp")
print(f"Non-essential median length: {essential[~essential['is_essential']]['gene_length'].median():.0f} bp")
short_ess = (essential['is_essential'] & (essential['gene_length'] < 300)).sum()
print(f"Essential genes <300 bp: {short_ess:,} ({short_ess/essential['is_essential'].sum()*100:.1f}%)")"""),

    md("## Figure 1: Family classification overview"),

    code("""fig, axes = plt.subplots(2, 2, figsize=(14, 11))

class_order = ['universally_essential', 'variably_essential', 'never_essential']
class_labels = ['Universally\\nessential', 'Variably\\nessential', 'Never\\nessential']
class_colors = ['#D32F2F', '#FF9800', '#4CAF50']

# Panel A
ax = axes[0, 0]
counts = [class_counts.get(c, 0) for c in class_order]
bars = ax.bar(class_labels, counts, color=class_colors, edgecolor='black', linewidth=0.5)
for bar, count in zip(bars, counts):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50,
            f'{count:,}', ha='center', va='bottom', fontsize=10)
ax.set_ylabel('Number of ortholog families')
ax.set_title('A. Essentiality Classification')
ax.set_ylim(0, max(counts) * 1.15)

# Panel B
ax = axes[0, 1]
for cls, color, label in zip(class_order, class_colors,
                              ['Universally essential', 'Variably essential', 'Never essential']):
    subset = families[families['essentiality_class'] == cls]
    ax.hist(subset['n_organisms'], bins=range(2, 50), alpha=0.6,
            color=color, label=f'{label} (n={len(subset):,})', edgecolor='black', linewidth=0.3)
ax.set_xlabel('Number of organisms in family')
ax.set_ylabel('Number of families')
ax.set_title('B. Family Size Distribution')
ax.legend(fontsize=8)

# Panel C
ax = axes[1, 0]
ax.hist(var_ess['frac_essential'], bins=20, color='#FF9800', edgecolor='black', linewidth=0.5)
ax.set_xlabel('Fraction of organisms where essential')
ax.set_ylabel('Number of families')
ax.set_title('C. Essentiality Penetrance (Variably Essential)')
ax.axvline(0.5, color='black', linestyle='--', alpha=0.5, label='50%')
ax.legend()

# Panel D
ax = axes[1, 1]
hyp_data = []
for cls, label in zip(class_order + ['orphan'], class_labels + ['Orphan\\nessential']):
    if cls == 'orphan':
        subset = ess_not_in_og
    else:
        subset = gene_family_class[gene_family_class['essentiality_class'] == cls]
    n_hyp = subset['desc'].str.contains('hypothetical', case=False, na=False).sum()
    hyp_data.append({'class': label, 'pct_hyp': n_hyp / len(subset) * 100, 'n': len(subset)})
hyp_df = pd.DataFrame(hyp_data)
bars = ax.bar(hyp_df['class'], hyp_df['pct_hyp'],
              color=['#D32F2F', '#FF9800', '#4CAF50', '#9E9E9E'], edgecolor='black', linewidth=0.5)
for bar, row in zip(bars, hyp_df.itertuples()):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
            f'n={row.n:,}', ha='center', va='bottom', fontsize=8)
ax.set_ylabel('% hypothetical proteins')
ax.set_title('D. Annotation Status by Essentiality Class')
ax.set_ylim(0, hyp_df['pct_hyp'].max() * 1.2)

plt.tight_layout()
plt.savefig(FIG_DIR / 'essential_families_overview.png', dpi=150, bbox_inches='tight')
plt.show()"""),

    md("## Figure 2: Top 40 universally essential families heatmap"),

    code("""top_univ = univ.sort_values('n_organisms', ascending=False).head(40)
all_orgs_sorted = sorted(essential['orgId'].unique())

fig, ax = plt.subplots(figsize=(16, 10))
heatmap_data = np.full((len(top_univ), len(all_orgs_sorted)), np.nan)
family_labels_list = []

for i, (_, fam) in enumerate(top_univ.iterrows()):
    fam_genes = merged[merged['OG_id'] == fam['OG_id']]
    for _, gene in fam_genes.iterrows():
        if gene['orgId'] in all_orgs_sorted:
            j = all_orgs_sorted.index(gene['orgId'])
            ess_val = gene.get('is_essential', None)
            if pd.notna(ess_val):
                heatmap_data[i, j] = 1 if bool(ess_val) else 0
    gene_name = str(fam['rep_gene'])[:8] if fam['rep_gene'] else ''
    desc_short = str(fam['rep_desc'])[:35]
    family_labels_list.append(f"{gene_name} - {desc_short}" if gene_name else desc_short)

from matplotlib.patches import Patch
cmap = plt.cm.colors.ListedColormap(['#4CAF50', '#D32F2F', '#E0E0E0'])
bounds = [-0.5, 0.5, 1.5, 2.5]
norm = plt.cm.colors.BoundaryNorm(bounds, cmap.N)
heatmap_display = np.where(np.isnan(heatmap_data), 2, heatmap_data)

ax.imshow(heatmap_display, aspect='auto', cmap=cmap, norm=norm, interpolation='none')
ax.set_yticks(range(len(family_labels_list)))
ax.set_yticklabels(family_labels_list, fontsize=7)
ax.set_xticks(range(len(all_orgs_sorted)))
ax.set_xticklabels(all_orgs_sorted, rotation=90, fontsize=6)
ax.set_xlabel('Organism')
ax.set_title(f'Top {len(top_univ)} Universally Essential Gene Families')
ax.legend(handles=[Patch(facecolor='#D32F2F', label='Essential'),
                   Patch(facecolor='#4CAF50', label='Non-essential'),
                   Patch(facecolor='#E0E0E0', label='Not present')], loc='lower right', fontsize=8)
plt.tight_layout()
plt.savefig(FIG_DIR / 'essential_families_heatmap.png', dpi=150, bbox_inches='tight')
plt.show()"""),
]

# ============================================================================
# NB03: Function Prediction
# ============================================================================
nb03 = nbf.v4.new_notebook()
nb03.metadata['kernelspec'] = {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'}
nb03.cells = [
    md("""# NB03: Function Prediction for Hypothetical Essential Genes

For each hypothetical essential gene with orthologs:
1. Find non-essential orthologs in other organisms
2. Check if any non-essential ortholog is in an ICA fitness module
3. Transfer the module's enrichment label as a function prediction

**Input**: Essential genes, ortholog groups, ICA module data from `fitness_modules` project
**Output**: `data/essential_predictions.tsv`"""),

    code("""import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path('../data')
FM_DIR = Path('../../fitness_modules/data')
MODULE_DIR = FM_DIR / 'modules'
FAMILY_DIR = FM_DIR / 'module_families'

essential = pd.read_csv(DATA_DIR / 'all_essential_genes.tsv', sep='\\t', low_memory=False)
essential['is_essential'] = essential['is_essential'].astype(str).str.strip().str.lower() == 'true'
essential['locusId'] = essential['locusId'].astype(str)

og_df = pd.read_csv(DATA_DIR / 'all_ortholog_groups.csv')
og_df['locusId'] = og_df['locusId'].astype(str)

print(f"Genes: {len(essential):,} ({essential['is_essential'].sum():,} essential)")
print(f"Ortholog groups: {og_df['OG_id'].nunique():,}")"""),

    md("## Build lookup dictionaries"),

    code("""# Essential status lookup
ess_lookup = {}
for _, r in essential.iterrows():
    ess_lookup[(r['orgId'], r['locusId'])] = r['is_essential']

# Gene -> OG
gene_to_og = {}
for _, r in og_df.iterrows():
    gene_to_og[(r['orgId'], r['locusId'])] = r['OG_id']

# OG -> members
og_members = og_df.groupby('OG_id').apply(
    lambda g: list(zip(g['orgId'], g['locusId']))
).to_dict()

# Module membership
gene_to_modules = {}
module_orgs = []
for f in sorted(MODULE_DIR.glob('*_gene_membership.csv')):
    org = f.stem.replace('_gene_membership', '')
    module_orgs.append(org)
    membership = pd.read_csv(f, index_col=0)
    for mod in membership.columns:
        for gene in membership.index[membership[mod] == 1]:
            gene_to_modules.setdefault((org, str(gene)), []).append(mod)

# Module annotations
module_best_ann = {}
for org in module_orgs:
    ann_file = MODULE_DIR / f'{org}_module_annotations.csv'
    if not ann_file.exists() or ann_file.stat().st_size < 10:
        continue
    ann = pd.read_csv(ann_file)
    sig = ann[ann['significant'] == True]
    for mod, grp in sig.groupby('module'):
        best = grp.loc[grp['fdr'].idxmin()]
        module_best_ann[(org, mod)] = {'term': best['term'], 'db': best['database'], 'fdr': best['fdr']}

# Module families
mod_to_family = {}
for _, r in pd.read_csv(FAMILY_DIR / 'module_families.csv').iterrows():
    mod_to_family[(r['orgId'], r['module'])] = r['familyId']
fam_ann = {}
for _, r in pd.read_csv(FAMILY_DIR / 'family_annotations.csv').iterrows():
    fam_ann[r['familyId']] = {'consensus_term': r['consensus_term'], 'n_organisms': r['n_organisms']}

print(f"Module organisms: {len(module_orgs)}")
print(f"Genes in modules: {len(gene_to_modules):,}")
print(f"Annotated modules: {len(module_best_ann):,}")"""),

    md("## Identify hypothetical essential genes"),

    code("""hyp_patterns = ['hypothetical', 'uncharacterized', 'unknown function', 'DUF']
ess_genes = essential[essential['is_essential']].copy()
ess_genes['is_hypothetical'] = ess_genes['desc'].apply(
    lambda d: any(p.lower() in str(d).lower() for p in hyp_patterns) if pd.notna(d) else True
)

og_lookup = og_df[['orgId', 'locusId', 'OG_id']].drop_duplicates()
ess_genes = ess_genes.merge(og_lookup, on=['orgId', 'locusId'], how='left')
ess_genes.rename(columns={'OG_id': 'og_id'}, inplace=True)

targets = ess_genes[ess_genes['is_hypothetical'] & ess_genes['og_id'].notna()]
print(f"Hypothetical essential genes: {ess_genes['is_hypothetical'].sum():,}")
print(f"  With orthologs (predictable): {len(targets):,}")
print(f"  Without orthologs (orphans): {ess_genes['is_hypothetical'].sum() - len(targets):,}")"""),

    md("""## Predict function via ortholog-module transfer

For each hypothetical essential gene, find non-essential orthologs in ICA modules.
Transfer the module's best enrichment annotation. Score by -log10(FDR) + log10(family breadth)."""),

    code("""predictions = []
for i, (_, gene) in enumerate(targets.iterrows()):
    org, locus, og_id = gene['orgId'], gene['locusId'], gene['og_id']
    best_pred, best_conf = None, -1

    for m_org, m_locus in og_members.get(og_id, []):
        if m_org == org and m_locus == locus:
            continue
        if ess_lookup.get((m_org, m_locus), True):
            continue  # also essential — skip
        for mod in gene_to_modules.get((m_org, m_locus), []):
            ann = module_best_ann.get((m_org, mod))
            if ann is None:
                continue
            fam_id = mod_to_family.get((m_org, mod), '')
            fam_info = fam_ann.get(fam_id, {})
            conf = -np.log10(max(ann['fdr'], 1e-20))
            if fam_id and fam_info.get('n_organisms', 0) > 1:
                conf += np.log10(fam_info['n_organisms'])
            if conf > best_conf:
                best_conf = conf
                best_pred = {
                    'target_orgId': org, 'target_locusId': locus,
                    'target_desc': gene['desc'], 'OG_id': og_id,
                    'source_orgId': m_org, 'source_locusId': m_locus,
                    'source_module': mod, 'predicted_term': ann['term'],
                    'predicted_db': ann['db'], 'enrichment_fdr': ann['fdr'],
                    'familyId': fam_id,
                    'family_n_organisms': fam_info.get('n_organisms', 0),
                    'family_consensus': fam_info.get('consensus_term', ''),
                    'confidence': conf,
                }
    if best_pred:
        predictions.append(best_pred)

pred_df = pd.DataFrame(predictions).sort_values('confidence', ascending=False)
pred_df.to_csv(DATA_DIR / 'essential_predictions.tsv', sep='\\t', index=False)
n_fam = (pred_df['familyId'] != '').sum()
print(f"Predictions: {len(pred_df):,} / {len(targets):,} targets ({len(pred_df)/len(targets)*100:.1f}%)")
print(f"  Family-backed: {n_fam:,}")
print(f"  Module-only: {len(pred_df) - n_fam:,}")"""),

    md("## Top 25 predictions"),

    code("""pred_df[['target_orgId', 'target_locusId', 'target_desc', 'predicted_term',
         'predicted_db', 'enrichment_fdr', 'familyId', 'confidence']].head(25)"""),

    md("## Predictions per organism"),

    code("""pred_df.groupby('target_orgId').size().sort_values(ascending=False)"""),

    md("## Summary"),

    code("""n_ess = essential['is_essential'].sum()
n_hyp = ess_genes['is_hypothetical'].sum()
print(f"Essential genes: {n_ess:,}")
print(f"Hypothetical essentials: {n_hyp:,} ({n_hyp/n_ess*100:.1f}%)")
print(f"  Predictable (have orthologs): {len(targets):,}")
print(f"  Orphans (no orthologs): {n_hyp - len(targets):,}")
print(f"Predictions made: {len(pred_df):,} ({len(pred_df)/len(targets)*100:.1f}% of predictable)")"""),
]

# ============================================================================
# NB04: Conservation Architecture
# ============================================================================
nb04 = nbf.v4.new_notebook()
nb04.metadata['kernelspec'] = {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'}
nb04.cells = [
    md("""# NB04: Conservation Architecture

Connect essential gene families to pangenome conservation status (core/accessory/singleton).

**Input**: Essential genes, ortholog groups, families from NB02, pangenome link table from `conservation_vs_fitness`
**Output**: `data/family_conservation.tsv`, figures"""),

    code("""import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from pathlib import Path

DATA_DIR = Path('../data')
FIG_DIR = Path('../figures')
CV_DIR = Path('../../conservation_vs_fitness/data')

essential = pd.read_csv(DATA_DIR / 'all_essential_genes.tsv', sep='\\t', low_memory=False)
essential['is_essential'] = essential['is_essential'].astype(str).str.strip().str.lower() == 'true'
essential['locusId'] = essential['locusId'].astype(str)

og_df = pd.read_csv(DATA_DIR / 'all_ortholog_groups.csv')
og_df['locusId'] = og_df['locusId'].astype(str)

families = pd.read_csv(DATA_DIR / 'essential_families.tsv', sep='\\t')

link = pd.read_csv(CV_DIR / 'fb_pangenome_link.tsv', sep='\\t')
link['locusId'] = link['locusId'].astype(str)

pg_meta = pd.read_csv(CV_DIR / 'pangenome_metadata.tsv', sep='\\t')
org_mapping = pd.read_csv(CV_DIR / 'organism_mapping.tsv', sep='\\t')

print(f"Link table: {len(link):,} gene-cluster links, {link['orgId'].nunique()} organisms")"""),

    md("## Core genome fraction by essentiality"),

    code("""ess_conservation = essential.merge(
    link[['orgId', 'locusId', 'is_core', 'is_auxiliary', 'is_singleton']],
    on=['orgId', 'locusId'], how='inner'
)

ess_core = ess_conservation[ess_conservation['is_essential']]
noness_core = ess_conservation[~ess_conservation['is_essential']]

print(f"Essential genes: {ess_core['is_core'].mean()*100:.1f}% core (n={len(ess_core):,})")
print(f"Non-essential: {noness_core['is_core'].mean()*100:.1f}% core (n={len(noness_core):,})")"""),

    md("## Conservation by essentiality class"),

    code("""# Add OG and class
ess_conservation = ess_conservation.merge(og_df[['orgId', 'locusId', 'OG_id']], on=['orgId', 'locusId'], how='left')
ess_conservation = ess_conservation.merge(families[['OG_id', 'essentiality_class']], on='OG_id', how='left')

ess_conservation.loc[
    ess_conservation['essentiality_class'].isna() & ess_conservation['is_essential'],
    'essentiality_class'] = 'orphan_essential'
ess_conservation.loc[
    ess_conservation['essentiality_class'].isna() & ~ess_conservation['is_essential'],
    'essentiality_class'] = 'no_og'

for cls in ['universally_essential', 'variably_essential', 'never_essential', 'orphan_essential']:
    s = ess_conservation[ess_conservation['essentiality_class'] == cls]
    if len(s) > 0:
        print(f"{cls}: {s['is_core'].mean()*100:.1f}% core (n={len(s):,})")"""),

    md("## Per-family conservation"),

    code("""family_conservation = []
for og_id, group in ess_conservation[ess_conservation['OG_id'].notna()].groupby('OG_id'):
    fam_info = families[families['OG_id'] == og_id]
    if len(fam_info) == 0:
        continue
    fam = fam_info.iloc[0]
    family_conservation.append({
        'OG_id': og_id, 'essentiality_class': fam['essentiality_class'],
        'pct_core': group['is_core'].mean() * 100, 'n_genes': len(group),
        'n_organisms': group['orgId'].nunique(),
        'n_essential_organisms': fam['n_essential_organisms'],
        'frac_essential': fam['frac_essential'],
        'rep_gene': fam['rep_gene'], 'rep_desc': fam['rep_desc'],
    })

fam_cons = pd.DataFrame(family_conservation)
fam_cons.to_csv(DATA_DIR / 'family_conservation.tsv', sep='\\t', index=False)

for cls in ['universally_essential', 'variably_essential', 'never_essential']:
    s = fam_cons[fam_cons['essentiality_class'] == cls]
    print(f"{cls}: median {s['pct_core'].median():.1f}% core (n={len(s):,})")

univ_fams = fam_cons[fam_cons['essentiality_class'] == 'universally_essential']
n100 = (univ_fams['pct_core'] == 100).sum()
n90 = (univ_fams['pct_core'] >= 90).sum()
print(f"\\nUniversally essential: {n100}/{len(univ_fams)} 100% core, {n90}/{len(univ_fams)} >=90% core")"""),

    md("## Penetrance vs conservation correlation"),

    code("""var_with_core = fam_cons[fam_cons['essentiality_class'] == 'variably_essential']
rho, p = stats.spearmanr(var_with_core['frac_essential'], var_with_core['pct_core'])
print(f"Penetrance vs conservation: rho={rho:.4f}, p={p:.2e}")

high_pen = var_with_core[var_with_core['frac_essential'] > 0.8]['pct_core'].median()
low_pen = var_with_core[var_with_core['frac_essential'] < 0.2]['pct_core'].median()
print(f"  >80% penetrance: {high_pen:.1f}% core")
print(f"  <20% penetrance: {low_pen:.1f}% core")"""),

    md("## Clade size vs essentiality rate"),

    code("""org_ess_stats = essential.groupby('orgId').agg(
    n_genes=('locusId', 'count'), n_essential=('is_essential', 'sum')).reset_index()
org_ess_stats['pct_essential'] = org_ess_stats['n_essential'] / org_ess_stats['n_genes'] * 100

org_meta = org_mapping.merge(pg_meta, on='gtdb_species_clade_id', how='inner')
org_ess_stats = org_ess_stats.merge(
    org_meta[['orgId', 'no_genomes', 'no_core', 'no_gene_clusters']], on='orgId', how='left')

has_pg = org_ess_stats.dropna(subset=['no_genomes'])
rho_g, p_g = stats.spearmanr(has_pg['no_genomes'], has_pg['pct_essential'])
print(f"Clade size vs % essential: rho={rho_g:.3f}, p={p_g:.3e}")"""),

    md("## Figure: Conservation architecture"),

    code("""noness_pct_core = noness_core['is_core'].mean() * 100
fig, axes = plt.subplots(2, 2, figsize=(14, 11))

# Panel A
ax = axes[0, 0]
plot_classes = ['universally_essential', 'variably_essential', 'never_essential', 'orphan_essential']
plot_labels = ['Universally\\nessential', 'Variably\\nessential', 'Never\\nessential', 'Orphan\\nessential']
colors = ['#D32F2F', '#FF9800', '#4CAF50', '#9E9E9E']
core_pcts, ns = [], []
for cls in plot_classes:
    s = ess_conservation[ess_conservation['essentiality_class'] == cls]
    core_pcts.append(s['is_core'].mean() * 100 if len(s) > 0 else 0)
    ns.append(len(s))
bars = ax.bar(plot_labels, core_pcts, color=colors, edgecolor='black', linewidth=0.5)
for bar, n in zip(bars, ns):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
            f'n={n:,}', ha='center', va='bottom', fontsize=8)
ax.set_ylabel('% core genome')
ax.set_title('A. Core Genome Fraction by Essentiality Class')
ax.set_ylim(0, 105)
ax.axhline(noness_pct_core, color='gray', linestyle='--', alpha=0.5,
           label=f'Non-essential baseline ({noness_pct_core:.1f}%)')
ax.legend(fontsize=8)

# Panel B
ax = axes[0, 1]
for cls, color, label in zip(
    ['universally_essential', 'variably_essential', 'never_essential'],
    ['#D32F2F', '#FF9800', '#4CAF50'],
    ['Universally essential', 'Variably essential', 'Never essential']):
    s = fam_cons[fam_cons['essentiality_class'] == cls]
    if len(s) > 0:
        ax.hist(s['pct_core'], bins=20, alpha=0.6, color=color,
                label=f'{label} (n={len(s):,})', edgecolor='black', linewidth=0.3)
ax.set_xlabel('% core genes in family')
ax.set_ylabel('Number of families')
ax.set_title('B. Family-Level Core Fraction')
ax.legend(fontsize=8)

# Panel C
ax = axes[1, 0]
ax.scatter(var_with_core['frac_essential'], var_with_core['pct_core'],
           alpha=0.3, s=10, color='#FF9800')
ax.set_xlabel('Fraction of organisms where essential')
ax.set_ylabel('% core genes in family')
ax.set_title(f'C. Penetrance vs Conservation (rho={rho:.3f}, p={p:.2e})')

# Panel D
ax = axes[1, 1]
if len(has_pg) > 0:
    ax.scatter(has_pg['no_genomes'], has_pg['pct_essential'],
               alpha=0.6, s=30, color='#2196F3', edgecolor='black', linewidth=0.3)
    for _, r in has_pg.iterrows():
        if r['no_genomes'] > 1000 or r['pct_essential'] > 25:
            ax.annotate(r['orgId'], (r['no_genomes'], r['pct_essential']), fontsize=6, alpha=0.7)
    ax.set_xlabel('Number of genomes in species clade')
    ax.set_ylabel('% genes called essential')
    ax.set_title(f'D. Clade Size vs Essentiality Rate (rho={rho_g:.3f}, p={p_g:.3e})')
    ax.set_xscale('log')

plt.tight_layout()
plt.savefig(FIG_DIR / 'conservation_architecture.png', dpi=150, bbox_inches='tight')
plt.show()"""),
]

# Write all notebooks
for nb, name in [(nb02, '02_essential_families'), (nb03, '03_function_prediction'),
                 (nb04, '04_conservation_architecture')]:
    path = NB_DIR / f'{name}.ipynb'
    with open(path, 'w') as f:
        nbf.write(nb, f)
    print(f"Created: {path}")

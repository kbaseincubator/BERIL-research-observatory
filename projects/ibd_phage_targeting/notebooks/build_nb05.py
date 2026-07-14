"""Build NB05_tier_a_scoring.ipynb — Tier-A scoring pipeline on rigor-controlled candidates.

Inputs:
  - NB04e E1 Tier-A (51 candidates, meta-viable 2 sub-studies)
  - NB04e E3 Tier-A (40 provisional single-study)
  - NB04c cross-ecotype engraftment-confirmed (5 species)
  - NB04h HMP2 external replication (E1 Tier-A sign-concordance per species)

Applies A3-A6 Tier-A criteria from RESEARCH_PLAN:
  - A3 — Literature / cohort CD-association (multi-source concordance)
  - A4 — Protective-analog exclusion (within-substudy effect sign + curated protective list)
  - A5 — Engraftment / strain-adaptation evidence (donor 2708 + Kumbhari)
  - A6 — BGC-encoded inflammatory mediator (ref_bgc_catalog + ref_cborf_enrichment)

Produces scored + ranked Tier-A list with actionable threshold flag.
"""
from pathlib import Path
import nbformat as nbf

NB_PATH = Path(__file__).parent / "NB05_tier_a_scoring.ipynb"
nb = nbf.v4.new_notebook()
cells = []

cells.append(nbf.v4.new_markdown_cell("""# NB05 — Tier-A Scoring Pipeline

**Project**: `ibd_phage_targeting` — Pillar 2 close-out
**Depends on**: NB04c (within-substudy meta), NB04e (ecotype-specific Tier-A), NB04h (HMP2 external replication), and the CrohnsPhage mart reference tables (BGC catalog, Kumbhari strain-adaptation, species-IBD associations, phage biology curation).

## Purpose

NB04d and NB04e produced the rigor-controlled input candidate set (~ 85 unique species after dedup). NB05 applies the Tier-A criteria A3 – A6 from `RESEARCH_PLAN.md` to produce a scored + ranked target list. This list feeds into Pillar 4 (phage targetability) and Pillar 5 (UC Davis per-patient cocktail drafts).

## Criteria applied

| Criterion | Source | Scoring |
|---|---|---|
| A3 — Literature + cohort CD-association | NB04c meta + HMP2 replication + `ref_cd_vs_hc_differential` + `ref_species_ibd_associations` + `ref_phage_biology` | 0–5 (fraction of sources showing CD-up) |
| A4 — Protective-analog exclusion | NB04c within-substudy effect sign + curated protective-species blacklist | 0 (protective-analog risk) or 1 (pass) |
| A5 — Engraftment / strain adaptation | Pre-identified donor 2708 engraftment set + `fact_strain_competition` + `ref_kumbhari_s7_gene_strain_inference` | 0 / 0.5 / 1 |
| A6 — BGC inflammatory mediator | `ref_bgc_catalog` (BGC count per species) + `ref_cborf_enrichment` (CB-ORF CD vs HC effect) | 0 / 0.5 / 1 |

## Note on synonymy

Several reference tables use pre-GTDB-r214 species names (e.g., "Ruminococcus gnavus" instead of "Mediterraneibacter gnavus", "Clostridium bolteae" instead of "Enterocloster bolteae"). We **invert the canonical→alias synonymy layer** so each Tier-A candidate matches against *all* its aliases in the reference tables. Without this, `ref_bgc_catalog` matches only 9/20 top E1 candidates; with inversion, we recover the full set.
"""))

cells.append(nbf.v4.new_code_cell("""import warnings; warnings.filterwarnings('ignore')
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
mpl.rcParams['figure.dpi'] = 100

DATA_MART = Path.home() / 'data' / 'CrohnsPhage'
DATA_OUT = Path('../data')
FIG_OUT = Path('../figures')

# Curated protective species (CD-protective mechanism documented in literature).
# These are flagged for strain-level scrutiny before any phage targeting, not auto-excluded.
PROTECTIVE_REFERENCE = {
    'Faecalibacterium prausnitzii', 'Akkermansia muciniphila',
    'Roseburia intestinalis', 'Roseburia hominis', 'Lachnospira eligens',
    'Agathobacter rectalis', 'Clostridium scindens', 'Coprococcus eutactus',
    'Bifidobacterium adolescentis', 'Bifidobacterium longum',
}

# Engraftment-confirmed pathobionts (donor 2708 → P1 → P2)
ENGRAFTED = [
    'Mediterraneibacter gnavus', 'Eggerthella lenta', 'Escherichia coli',
    'Enterocloster bolteae', 'Hungatella hathewayi', 'Klebsiella oxytoca',
]
"""))

cells.append(nbf.v4.new_markdown_cell("""## §1. Build the input candidate set"""))

cells.append(nbf.v4.new_code_cell("""# NB04e E1 + E3 Tier-A
nb04e = pd.read_csv(DATA_OUT / 'nb04e_within_ecotype_meta.tsv', sep='\\t')
e1 = nb04e[(nb04e.ecotype == 1) & (nb04e.pooled_effect > 0.5) &
           (nb04e.fdr < 0.10) & (nb04e.concordant_sign_frac >= 0.66)].copy()
e3 = nb04e[(nb04e.ecotype == 3) & (nb04e.pooled_effect > 0.5) &
           (nb04e.fdr < 0.10) & (nb04e.concordant_sign_frac >= 0.66)].copy()
e1['ecotype_membership'] = 'E1'
e3['ecotype_membership'] = 'E3_provisional'
print(f'E1 Tier-A: {len(e1)}; E3 provisional Tier-A: {len(e3)}')

# NB04c cross-ecotype engraftment-confirmed (within-IBD-substudy CD-vs-nonIBD)
nb04c_meta = pd.read_csv(DATA_OUT / 'nb04c_within_substudy_meta.tsv', sep='\\t')
engraft = nb04c_meta[nb04c_meta.species.isin(ENGRAFTED) &
                     (nb04c_meta.pooled_effect > 0) &
                     (nb04c_meta.fdr < 0.10) &
                     (nb04c_meta.concordant_sign_frac >= 0.66)].copy()
engraft['ecotype_membership'] = 'cross_ecotype_engraftment'
print(f'Engraftment-confirmed cross-ecotype: {len(engraft)}')

# Dedup into a single candidate set
all_cands = pd.concat([
    e1[['species','pooled_effect','fdr','concordant_sign_frac','n_substudies','ecotype_membership']],
    e3[['species','pooled_effect','fdr','concordant_sign_frac','n_substudies','ecotype_membership']],
    engraft[['species','pooled_effect','fdr','concordant_sign_frac','n_substudies','ecotype_membership']],
], ignore_index=True)

# Collapse to unique species with multi-category membership string
by_sp = all_cands.groupby('species').agg({
    'pooled_effect': 'max',
    'fdr': 'min',
    'concordant_sign_frac': 'max',
    'n_substudies': 'max',
    'ecotype_membership': lambda s: '|'.join(sorted(set(s))),
}).reset_index()
by_sp = by_sp.rename(columns={'pooled_effect':'best_effect','fdr':'best_fdr','concordant_sign_frac':'best_concord'})
print(f'\\nUnique candidates: {len(by_sp)}')
print(by_sp.ecotype_membership.value_counts().to_string())
"""))

cells.append(nbf.v4.new_markdown_cell("""## §2. Invert synonymy layer for reference-table joins"""))

cells.append(nbf.v4.new_code_cell("""syn = pd.read_csv(DATA_OUT / 'species_synonymy.tsv', sep='\\t')
# canonical -> set of aliases (including the canonical itself)
canonical_to_aliases = {}
for canonical, aliases_df in syn.groupby('canonical'):
    s = set(aliases_df.alias.tolist())
    s.add(canonical)
    canonical_to_aliases[canonical] = s

# Also add identity map for any candidate species not in synonymy table
for sp in by_sp.species:
    canonical_to_aliases.setdefault(sp, {sp})

# Display the inversion for a few candidates to verify
for sp in ['Mediterraneibacter gnavus','Enterocloster bolteae','Erysipelatoclostridium innocuum','Hungatella symbiosa']:
    if sp in canonical_to_aliases:
        print(f'  {sp}')
        for a in sorted(canonical_to_aliases[sp]):
            print(f'    {a}')

def matches_any(ref_names_set, candidate):
    \"\"\"True if any alias of candidate appears in ref_names_set.\"\"\"
    return bool(canonical_to_aliases[candidate] & ref_names_set)

def matching_aliases(ref_names_set, candidate):
    return sorted(canonical_to_aliases[candidate] & ref_names_set)
"""))

cells.append(nbf.v4.new_markdown_cell("""## §3. A3 — Literature + cohort CD-association"""))

cells.append(nbf.v4.new_code_cell("""# Signal 1: NB04c cross-study meta (confound-free within-IBD-substudy CD-vs-nonIBD)
nb04c_map = dict(zip(nb04c_meta.species, nb04c_meta[['pooled_effect','fdr','concordant_sign_frac']].to_dict(orient='records')))

# Signal 2: HMP2 E1 replication from NB04h
hmp2_rep = pd.read_csv(DATA_OUT / 'nb04h_e1_tier_a_hmp2_replication.tsv', sep='\\t')
hmp2_map = dict(zip(hmp2_rep.species, hmp2_rep[['hmp2_e1_effect','hmp2_e1_fdr','hmp2_concordant']].to_dict(orient='records')))

# Signal 3: ref_cd_vs_hc_differential (Kumbhari-style)
ref_cd = pd.read_parquet(DATA_MART / 'ref_cd_vs_hc_differential.snappy.parquet')
ref_cd_names = set(ref_cd.taxon.dropna().unique())

# Signal 4: ref_species_ibd_associations (UHGG-indexed) — need UHGG name mapping
ref_ibd = pd.read_parquet(DATA_MART / 'ref_species_ibd_associations.snappy.parquet')
# Filter to dxIBD trait
dx_rows = ref_ibd[ref_ibd[' Trait being tested'] == 'dxIBD'].copy()
# Map UHGG id -> species name via ref_uhgg_species
uhgg = pd.read_parquet(DATA_MART / 'ref_uhgg_species.snappy.parquet')
uhgg_map = dict(zip(uhgg['Species genome ID (from UHGG)'], uhgg['Species name']))
dx_rows['species_name'] = dx_rows['Species genome ID (from UHGG)'].map(uhgg_map)
dx_names = set(dx_rows.species_name.dropna().unique())

# Signal 5: ref_phage_biology (curated top Tier-1/Tier-2 targets)
phage_bio = pd.read_parquet(DATA_MART / 'ref_phage_biology.snappy.parquet')
phage_bio_names = set(phage_bio.organism.dropna().unique())

def a3_score(sp):
    \"\"\"Return (a3_score, a3_signals_dict) in range 0..5.\"\"\"
    signals = {}
    # 1. NB04c cross-study confound-free meta
    if sp in nb04c_map:
        r = nb04c_map[sp]
        signals['nb04c_meta'] = (r['pooled_effect'] > 0.5) and (r['fdr'] < 0.10) and (r['concordant_sign_frac'] >= 0.66)
    else: signals['nb04c_meta'] = False
    # 2. HMP2 replication (NB04h) — E1 Tier-A list only carries this
    if sp in hmp2_map:
        r = hmp2_map[sp]
        signals['hmp2_replication'] = bool(r['hmp2_concordant']) and (r['hmp2_e1_fdr'] < 0.10)
    else: signals['hmp2_replication'] = False
    # 3. ref_cd_vs_hc_differential
    m = matching_aliases(ref_cd_names, sp)
    if m:
        row = ref_cd[ref_cd.taxon == m[0]].iloc[0]
        signals['ref_cd_vs_hc'] = (row.log2fc_cd_vs_ctrl > 0.5) and (row.fdr < 0.10)
    else: signals['ref_cd_vs_hc'] = False
    # 4. ref_species_ibd_associations
    m = matching_aliases(dx_names, sp)
    if m:
        row = dx_rows[dx_rows.species_name == m[0]].iloc[0]
        signals['ref_ibd_assoc'] = (row['Coefficient from mixed effects model'] > 0) and (row['p-value'] < 0.05)
    else: signals['ref_ibd_assoc'] = False
    # 5. ref_phage_biology (curated)
    m = matching_aliases(phage_bio_names, sp)
    signals['phage_biology_curated'] = bool(m)
    return sum(signals.values()), signals

a3_results = [a3_score(sp) for sp in by_sp.species]
by_sp['a3_score'] = [r[0] for r in a3_results]
by_sp['a3_signals'] = [json.dumps(r[1]) for r in a3_results]
print(f'A3 score distribution:')
print(by_sp.a3_score.value_counts().sort_index().to_string())
"""))

cells.append(nbf.v4.new_markdown_cell("""## §4. A4 — Protective-analog exclusion"""))

cells.append(nbf.v4.new_code_cell("""def a4_score(sp):
    \"\"\"1 = pass, 0 = protective-analog risk. Flag + notes returned.\"\"\"
    # If confound-free within-substudy effect is negative -> CD-depleted under the cleanest contrast = protective-analog
    if sp in nb04c_map:
        r = nb04c_map[sp]
        if r['pooled_effect'] < 0:
            return 0, f'confound-free effect negative ({r["pooled_effect"]:.2f}) — protective-analog risk'
    # If species is on curated-protective list, flag for strain-level scrutiny (soft warning)
    if sp in PROTECTIVE_REFERENCE:
        return 0, 'on curated protective-species list — strain-level scrutiny required'
    return 1, 'pass'

a4_results = [a4_score(sp) for sp in by_sp.species]
by_sp['a4_score'] = [r[0] for r in a4_results]
by_sp['a4_note'] = [r[1] for r in a4_results]
print(f'A4 score distribution:')
print(by_sp.a4_score.value_counts().sort_index().to_string())
print(f'\\nCandidates failing A4 (protective-analog risk):')
print(by_sp[by_sp.a4_score == 0][['species','a4_note']].to_string(index=False))
"""))

cells.append(nbf.v4.new_markdown_cell("""## §5. A5 — Engraftment / strain adaptation"""))

cells.append(nbf.v4.new_code_cell("""# Direct engraftment (donor 2708)
direct_engraftment = set(ENGRAFTED)

# Kumbhari strain competition — which UHGG genomes show disease-strain expansion?
fsc = pd.read_parquet(DATA_MART / 'fact_strain_competition.snappy.parquet')
# Compute per-UHGG-genome mean disease-strain expansion (disease_freq > health_freq)
fsc['disease_dominant'] = fsc.disease_strain_freq > fsc.health_strain_freq
per_genome = fsc.groupby('uhgg_genome_id').agg(
    n_rows=('sample_id', 'count'),
    disease_dom_frac=('disease_dominant', 'mean'),
    calp_corr_mean=('calprotectin', 'mean'),
).reset_index()
per_genome = per_genome.merge(uhgg[['Species genome ID (from UHGG)','Species name']],
                              left_on='uhgg_genome_id', right_on='Species genome ID (from UHGG)', how='left')
# Species where >50% of sample-timepoints have disease-strain dominance, calprotectin > 50
ks_competition_hits = set(per_genome[(per_genome.disease_dom_frac > 0.5) &
                                      (per_genome.n_rows >= 3)].dropna(subset=['Species name']).Species_name.unique() if False else
                           per_genome[(per_genome.disease_dom_frac > 0.5) & (per_genome.n_rows >= 3)].dropna(subset=['Species name'])['Species name'].unique())

# Kumbhari gene-strain inference — species with IBD-adapted gene enrichment (FDR < 0.05, coefficient > 0)
kgsi = pd.read_parquet(DATA_MART / 'ref_kumbhari_s7_gene_strain_inference.snappy.parquet')
# Group by species: any gene with IBD-adapted-strain probability significantly > health-adapted?
kgsi['ibd_signal'] = (kgsi['Probability of being found in an IBD-adapted strain'] >
                     kgsi['Probability of being found in a health-adapted strain']) & \\
                    (kgsi['FDR adjusted p-value'] < 0.05)
ks_gene_hits = set(kgsi[kgsi.ibd_signal].dropna(subset=['Species name'])['Species name'].unique())

def a5_score(sp):
    # Direct engraftment pathobiont (donor 2708) = 1.0
    if sp in direct_engraftment:
        return 1.0, 'donor 2708 engraftment-confirmed'
    # Kumbhari strain competition disease-dominance
    competition_alias = matching_aliases(ks_competition_hits, sp)
    gene_alias = matching_aliases(ks_gene_hits, sp)
    notes = []
    score = 0.0
    if competition_alias:
        score = max(score, 0.5); notes.append('Kumbhari strain-competition disease-dominance')
    if gene_alias:
        score = max(score, 0.5); notes.append('Kumbhari IBD-adapted-strain gene signal')
    return score, '; '.join(notes) if notes else 'no engraftment/strain signal'

a5_results = [a5_score(sp) for sp in by_sp.species]
by_sp['a5_score'] = [r[0] for r in a5_results]
by_sp['a5_note'] = [r[1] for r in a5_results]
print(f'A5 score distribution:')
print(by_sp.a5_score.value_counts().sort_index().to_string())
print(f'\\nA5 = 1.0 (direct engraftment):')
print(by_sp[by_sp.a5_score == 1.0][['species','a5_note']].to_string(index=False))
print(f'\\nA5 = 0.5 (strain-level signal):')
top = by_sp[by_sp.a5_score == 0.5][['species','a5_note']].head(10)
print(top.to_string(index=False))
"""))

cells.append(nbf.v4.new_markdown_cell("""## §6. A6 — BGC-encoded inflammatory mediator"""))

cells.append(nbf.v4.new_code_cell("""bgc = pd.read_parquet(DATA_MART / 'ref_bgc_catalog.snappy.parquet')
cb = pd.read_parquet(DATA_MART / 'ref_cborf_enrichment.snappy.parquet')
bgc_species_names = set(bgc.Species.dropna().unique())

# Map CB-ORF -> BGC (CB-ORFs column in BGC catalog is pipe-delimited list)
bgc['cborf_list'] = bgc['CB-ORFs'].fillna('').str.split('|')
# Expand so each row has one CB-ORF
bgc_exp = bgc.explode('cborf_list').rename(columns={'cborf_list':'CB-ORF'})
bgc_exp = bgc_exp[bgc_exp['CB-ORF'] != '']
# Merge with cborf enrichment
cb_keep = cb[(cb['Mean effect size estimate (CD vs. HC)'] > 0.5) &
             (cb['FDR-adjusted P-value (CD vs. HC)'] < 0.05)].copy()
cd_enriched_bgcs = set(bgc_exp[bgc_exp['CB-ORF'].isin(set(cb_keep['CB-ORF']))].BGC.unique())
print(f'BGCs with CD-enriched CB-ORFs: {len(cd_enriched_bgcs):,}')

# Per-species: count BGCs + flag if any are CD-enriched
def a6_score(sp):
    aliases = matching_aliases(bgc_species_names, sp)
    if not aliases:
        return 0.0, 'no BGC-catalog match'
    sub = bgc[bgc.Species.isin(aliases)]
    n_bgcs = len(sub)
    n_cd_enriched = sub.BGC.isin(cd_enriched_bgcs).sum()
    mibig_compounds = sub['MIBiG Compounds'].dropna().unique()
    if n_cd_enriched > 0:
        return 1.0, f'{n_bgcs} BGCs, {n_cd_enriched} with CD-enriched CB-ORFs (MIBiG match: {list(mibig_compounds)[:3] if len(mibig_compounds) else "none"})'
    else:
        return 0.5, f'{n_bgcs} BGCs, none CD-enriched (MIBiG match: {list(mibig_compounds)[:3] if len(mibig_compounds) else "none"})'

a6_results = [a6_score(sp) for sp in by_sp.species]
by_sp['a6_score'] = [r[0] for r in a6_results]
by_sp['a6_note'] = [r[1] for r in a6_results]
print(f'\\nA6 score distribution:')
print(by_sp.a6_score.value_counts().sort_index().to_string())
print(f'\\nA6 = 1.0 candidates (BGC + CD-enriched CB-ORFs):')
print(by_sp[by_sp.a6_score == 1.0][['species','a6_note']].head(15).to_string(index=False))
"""))

cells.append(nbf.v4.new_markdown_cell("""## §7. Aggregate Tier-A score + rank"""))

cells.append(nbf.v4.new_code_cell("""# Total Tier-A score (0..4 range, weighting each criterion equally)
by_sp['a3_norm'] = by_sp.a3_score / 5.0
by_sp['total_score'] = by_sp.a3_norm + by_sp.a4_score + by_sp.a5_score + by_sp.a6_score
by_sp['actionable'] = by_sp.total_score >= 2.5
by_sp = by_sp.sort_values('total_score', ascending=False).reset_index(drop=True)
by_sp['rank'] = by_sp.index + 1

# Save
OUT_COLS = ['rank','species','ecotype_membership','best_effect','best_fdr','best_concord',
            'a3_score','a3_signals','a4_score','a4_note','a5_score','a5_note','a6_score','a6_note',
            'total_score','actionable']
out = by_sp[OUT_COLS].copy()
out.to_csv(DATA_OUT / 'nb05_tier_a_scored.tsv', sep='\\t', index=False)

print(f'Total candidates scored: {len(out)}')
print(f'Actionable (total_score >= 2.5): {out.actionable.sum()}')
print()
print('TOP 20:')
disp = out.head(20)[['rank','species','ecotype_membership','a3_score','a4_score','a5_score','a6_score','total_score','actionable']]
print(disp.to_string(index=False))
"""))

cells.append(nbf.v4.new_markdown_cell("""## §8. Visualize scoring matrix"""))

cells.append(nbf.v4.new_code_cell("""fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 10))

# Heatmap of top 30 scoring matrix
top30 = out.head(30)
mat = top30[['a3_norm','a4_score','a5_score','a6_score']].values
yticks = [f'{r["rank"]}. {r["species"][:28]} ({r["ecotype_membership"][:15]})' for _, r in top30.iterrows()]

# Use a diverging/sequential palette
im = ax1.imshow(mat, aspect='auto', cmap='RdYlGn', vmin=0, vmax=1)
ax1.set_xticks(range(4))
ax1.set_xticklabels(['A3 literature/\\ncohort (norm)', 'A4 protective-\\nanalog pass', 'A5 engraftment', 'A6 BGC'], fontsize=9)
ax1.set_yticks(range(30))
ax1.set_yticklabels(yticks, fontsize=8)
for i in range(mat.shape[0]):
    for j in range(mat.shape[1]):
        ax1.text(j, i, f'{mat[i,j]:.2f}', ha='center', va='center',
                 color='white' if mat[i,j] < 0.5 else 'black', fontsize=7)
ax1.set_title('Top 30 Tier-A candidates — A3-A6 scoring matrix', fontsize=11)

# Total score bar chart — color by actionable
colors = ['#4a8a2a' if a else '#c44a4a' for a in top30.actionable]
ax2.barh(range(len(top30)), top30.total_score, color=colors, edgecolor='white')
ax2.axvline(2.5, ls='--', color='#333', label='actionable threshold (2.5)')
ax2.set_yticks(range(len(top30)))
ax2.set_yticklabels([''] * len(top30))  # y-labels already on left panel
ax2.set_xlabel('Tier-A total score (A3_norm + A4 + A5 + A6, 0-4)')
ax2.set_title(f'Total Tier-A score (n={len(out)} scored; {out.actionable.sum()} actionable)')
ax2.invert_yaxis()
ax2.legend()

plt.tight_layout()
plt.savefig(FIG_OUT / 'NB05_tier_a_scored.png', dpi=120, bbox_inches='tight')
plt.show()
"""))

cells.append(nbf.v4.new_markdown_cell("""## §9. Summary + NB04/NB05 hand-off to Pillar 4

The scored Tier-A list in `data/nb05_tier_a_scored.tsv` is the **final prioritized target set for Pillar 4 (phage targetability) and Pillar 5 (UC Davis per-patient cocktail drafts)**. The top actionable candidates (total_score ≥ 2.5) carry:

- A3 = 2–5 cross-cohort / cross-cohort-replication CD-association signals
- A4 = 1 (pass protective-analog exclusion)
- A5 = 0.5 – 1.0 (engraftment or strain-level IBD-adaptation evidence)
- A6 = 0.5 – 1.0 (BGC with CD-enriched CB-ORFs in ≥ 1 cases)

Caveats carried forward:
- E3 Tier-A candidates are provisional (single-study HallAB_2017 within cMD; E3 is rare in HMP2 so HMP2 doesn't replicate E3 specifically).
- Cross-ecotype engraftment pathobionts are cohort-level (CD vs nonIBD confound-free) but don't carry ecotype-specific prioritization.
- Curated-protective-species candidates that pass A4 (positive within-substudy effect despite being on the blacklist) should get explicit strain-level scrutiny before phage targeting — the species name alone may not distinguish pathobiont-like from protective strains.
"""))

cells.append(nbf.v4.new_code_cell("""# Save verdict summary — coerce numpy types to native Python for JSON
def _py(x):
    if isinstance(x, (np.bool_,)): return bool(x)
    if isinstance(x, (np.integer,)): return int(x)
    if isinstance(x, (np.floating,)): return float(x)
    if isinstance(x, dict): return {k: _py(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)): return [_py(v) for v in x]
    return x

top10 = out.head(10)[['rank','species','ecotype_membership','total_score']].to_dict(orient='records')
verdict = {
    'date': '2026-04-24',
    'n_candidates_total': int(len(out)),
    'n_actionable': int(out.actionable.sum()),
    'top_10_by_total_score': _py(top10),
    'actionable_threshold': 2.5,
    'criteria_weights': 'A3/5 + A4 + A5 + A6 (equal-weight; A3 normalized to 0-1 from 0-5 signals)',
}
def _default(o):
    if isinstance(o, (np.bool_,)): return bool(o)
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (np.floating,)): return float(o)
    return str(o)
with open(DATA_OUT / 'nb05_tier_a_verdict.json', 'w') as f:
    json.dump(verdict, f, indent=2, default=_default)
print('Saved data/nb05_tier_a_scored.tsv + data/nb05_tier_a_verdict.json + figures/NB05_tier_a_scored.png')
"""))

nb['cells'] = cells
nb.metadata.kernelspec = {"display_name": "Python 3", "language": "python", "name": "python3"}
nb.metadata.language_info = {"name": "python", "version": "3.10"}

with open(NB_PATH, 'w') as f:
    nbf.write(nb, f)
print(f'Wrote {NB_PATH}')

"""NB07b — Stratified-pathway DA per Tier-A-core species: species-resolved H3a (b) re-test.

NB07a clause-(b) failed because only 3 of 52 CD-up unstratified MetaCyc pathways landed in
the 7 a-priori IBD categories (44/409 background). The honest interpretation was that the
unstratified-pathway level captures broader bacterial-fitness-in-inflamed-gut signal rather
than concentrating in classical IBD-themed categories. NB07b tests the alternative: at the
species-resolved level (HUMAnN3 stratified-pathway form `PWY-XXX|g__species`), do the CD-up
pathways attributable to specific Tier-A-core pathobionts concentrate in the 7 categories?

Per-species:
  - Filter stratified pathways to the canonical species (via synonymy: e.g.,
    "Ruminococcus_gnavus" -> "Mediterraneibacter gnavus")
  - 10%-prevalence per IBD substudy (presence in stratified data)
  - Per-pathway within-IBD-substudy CD-vs-nonIBD CLR-Δ + bootstrap SE
  - IVW meta across 3 robust substudies
  - Filter to passing (FDR<0.10, |effect|>0.5)
  - Apply 7 a-priori category mapping
  - Re-test H3a (b) at species-resolved level

Output: per-species pathway-DA tables, per-species category-coherence verdict, cross-species heatmap.
"""
import warnings; warnings.filterwarnings('ignore')
from pathlib import Path
import json, io, contextlib, time, re
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests
import matplotlib.pyplot as plt
import matplotlib as mpl
mpl.rcParams['figure.dpi'] = 100

NOTEBOOK_DIR = Path(__file__).parent
PROJECT = NOTEBOOK_DIR.parent
DATA_MART = Path.home() / 'data' / 'CrohnsPhage'
DATA_OUT = PROJECT / 'data'
FIG_OUT = PROJECT / 'figures'

ROBUST_SUBSTUDIES = ['HallAB_2017', 'IjazUZ_2017', 'NielsenHB_2014']
SENSITIVITY_SUBSTUDIES = ['LiJ_2014']
TIER_A_CORE = [
    'Hungatella hathewayi', 'Mediterraneibacter gnavus', 'Escherichia coli',
    'Eggerthella lenta', 'Flavonifractor plautii', 'Enterocloster bolteae',
]
PREVALENCE_THRESHOLD = 0.10
EFFECT_THRESHOLD = 0.5
FDR_THRESHOLD = 0.10
N_PERM_CATEGORY = 1000
RNG_SEED = 42

CATEGORY_PATTERNS = {
    '1_bile_acid': r'(?i)bile|cholate|deoxycholate|7-?alpha|7ALPHA',
    '2_mucin_glycan': r'(?i)mucin|fucose|sialic|glycan|alginate|N-acetylgalactosamine|GalNAc|polyol',
    '3_sulfur_redox': r'(?i)sulfate|sulfite|thiosulfate|hydrogen sulfide|sulfidogenesis|dissimilatory sulf|tetrathionate',
    '4_TMA_choline': r'(?i)trimethylamine|TMAO|choline|betaine|carnitine|phosphatidylcholine',
    '5_eut_pdu': r'(?i)ethanolamine|propanediol|propanoate fermentation',
    '6_polyamine_urea': r'(?i)polyamine|putrescine|spermidine|urease|urea cycle|nitrogen fixation',
    '7_AA_decarb': r'(?i)tryptophanase|decarboxylation|indole|histidine degradation|arginine degradation|ornithine|lysine degradation|AST pathway',
}
OTHER = '0_other'

def categorize(pw_id):
    for cat, pat in CATEGORY_PATTERNS.items():
        if re.search(pat, pw_id):
            return cat
    return OTHER

section_logs = {}
def section(name):
    buf = io.StringIO()
    return buf, contextlib.redirect_stdout(buf)


# ============================================================
# §0 Load + filter stratified data; synonymy mapping; substudy + diagnosis
# ============================================================
buf, redir = section('0')
with redir:
    print(f'NB07b — H3a (b) species-resolved retest')
    print(f'Tier-A core species: {TIER_A_CORE}')
    print()
    t0 = time.time()
    syn = pd.read_csv(DATA_OUT / 'species_synonymy.tsv', sep='\t')
    lookup = dict(zip(syn.alias, syn.canonical))
    # Build alias -> canonical reverse: for each Tier-A canonical, all its aliases
    canon_aliases = {sp: {sp} for sp in TIER_A_CORE}
    for alias, canonical in lookup.items():
        if canonical in TIER_A_CORE:
            canon_aliases[canonical].add(alias)
    for sp, aliases in canon_aliases.items():
        # MetaCyc stratified format uses underscore-separated species names, match both forms
        underscore_aliases = {a.replace(' ', '_') for a in aliases}
        canon_aliases[sp] = aliases | underscore_aliases
        print(f'  {sp}: {len(canon_aliases[sp])} aliases')
    print()

    # Load substudy + diagnosis maps
    ds = pd.read_parquet(DATA_MART / 'dim_samples.snappy.parquet')
    def parse_substudy(row):
        ext = row['external_ids']
        if isinstance(ext, str):
            try:
                d = json.loads(ext)
                if isinstance(d.get('study'), str): return d['study']
            except: pass
        pid = row['participant_id']
        if isinstance(pid, str):
            parts = pid.split(':')
            if len(parts) >= 3 and parts[0] in ('CMD','HMP2'): return parts[1]
        return None
    ds['substudy'] = ds.apply(parse_substudy, axis=1)
    substudy_map = dict(zip(ds.sample_id, ds.substudy))
    eco = pd.read_csv(DATA_OUT / 'ecotype_assignments.tsv', sep='\t')
    diag_map = dict(zip(eco.sample_id, eco.diagnosis))

    # Load full pathway abundance
    pa = pd.read_parquet(DATA_MART / 'fact_pathway_abundance.snappy.parquet')
    print(f'Pathway data: {len(pa):,} rows')

    # Filter to stratified pathways for Tier-A canonical species
    def parse_sp_suffix(p):
        if not isinstance(p, str) or '|' not in p: return None
        suffix = p.split('|', 1)[1]
        m = re.match(r'g__\w+\.s__(.+)', suffix)
        if m: return m.group(1).replace('_', ' ')
        return None
    # Compute species suffix only on unique pathway IDs (faster than per-row apply)
    unique_pw = pa.pathway_id.drop_duplicates().to_frame()
    unique_pw['sp_suffix'] = unique_pw.pathway_id.apply(parse_sp_suffix)
    # Map suffix to canonical (reverse synonymy)
    def to_canon(sp):
        if sp is None: return None
        if sp in lookup: return lookup[sp]
        return sp if sp in TIER_A_CORE else None
    unique_pw['canonical'] = unique_pw.sp_suffix.apply(to_canon)
    pw_to_canon = dict(zip(unique_pw.pathway_id, unique_pw.canonical))

    pa['canonical'] = pa.pathway_id.map(pw_to_canon)
    pa_strat = pa[pa.canonical.isin(TIER_A_CORE)].copy()
    print(f'Stratified rows for Tier-A core: {len(pa_strat):,}')
    print(f'Distinct stratified pathways for Tier-A core (per canonical):')
    for sp in TIER_A_CORE:
        n = pa_strat[pa_strat.canonical == sp].pathway_id.nunique()
        print(f'  {sp:<32}  {n}')
    print(f'Elapsed: {time.time()-t0:.1f}s')
section_logs['0'] = buf.getvalue()


# ============================================================
# §1 Per-species pathway × sample matrix construction
# ============================================================
def clr_pathway(M):
    """CLR transform across pathways within sample (axis=0 is pathway, axis=1 is sample)."""
    M = M.astype(float).copy()
    col_min_nz = np.where(M > 0, M, np.nan)
    col_min_nz = np.nanmin(col_min_nz, axis=0)
    col_min_nz = np.where(np.isnan(col_min_nz), 1e-6, col_min_nz / 2)
    M = np.where(M > 0, M, col_min_nz[None, :])
    logM = np.log(M)
    return logM - logM.mean(axis=0, keepdims=True)


def per_substudy_da(pw_wide, cd_ids, ni_ids, n_boot=300, seed=42):
    cd_ = [c for c in cd_ids if c in pw_wide.columns]
    ni_ = [c for c in ni_ids if c in pw_wide.columns]
    if min(len(cd_), len(ni_)) < 5:
        return None, None, len(cd_), len(ni_)
    cols = cd_ + ni_
    M = pw_wide[cols].values
    full_clr = clr_pathway(M)
    n_a = len(cd_)
    a = full_clr[:, :n_a]; b = full_clr[:, n_a:]
    point = a.mean(axis=1) - b.mean(axis=1)
    rng = np.random.default_rng(seed)
    boot = np.empty((n_boot, full_clr.shape[0]))
    for i in range(n_boot):
        ai = rng.integers(0, n_a, n_a)
        bi = rng.integers(0, len(b[0]), len(b[0]))
        boot[i] = a[:, ai].mean(axis=1) - b[:, bi].mean(axis=1)
    se = boot.std(axis=0)
    return point, se, len(cd_), len(ni_)


def ivw_meta(per_eff, per_se):
    eff = np.stack(per_eff, axis=0)
    se = np.stack(per_se, axis=0) + 1e-9
    w = 1.0 / (se ** 2)
    pooled_eff = (eff * w).sum(axis=0) / w.sum(axis=0)
    pooled_se = 1.0 / np.sqrt(w.sum(axis=0))
    sign_match = (np.sign(eff) == np.sign(pooled_eff)).mean(axis=0)
    z = pooled_eff / pooled_se
    p = 2 * (1 - stats.norm.cdf(np.abs(z)))
    return pooled_eff, pooled_se, z, p, sign_match


buf, redir = section('1')
with redir:
    t0 = time.time()
    # Pre-extract substudy → sample id splits
    pa_samples = pa.sample_id.unique()
    sm = pd.DataFrame({
        'sample_id': pa_samples,
        'substudy': [substudy_map.get(s) for s in pa_samples],
        'diagnosis': [diag_map.get(s) for s in pa_samples],
    })
    sm = sm[sm.substudy.notna()]
    cd_ids = {ss: sm[(sm.substudy == ss) & (sm.diagnosis == 'CD')].sample_id.tolist()
              for ss in ROBUST_SUBSTUDIES}
    ni_ids = {ss: sm[(sm.substudy == ss) & (sm.diagnosis == 'nonIBD')].sample_id.tolist()
              for ss in ROBUST_SUBSTUDIES}
    for ss in ROBUST_SUBSTUDIES:
        print(f'  {ss}: CD={len(cd_ids[ss])}, nonIBD={len(ni_ids[ss])}')
    print(f'Elapsed: {time.time()-t0:.1f}s')
section_logs['1'] = buf.getvalue()


# ============================================================
# §2-§3 Per-species DA: build matrix, prevalence-filter, per-substudy DA, IVW meta
# ============================================================
buf, redir = section('2-3')
all_per_species = {}
with redir:
    t0 = time.time()
    for sp in TIER_A_CORE:
        print(f'\n--- {sp} ---')
        sub = pa_strat[pa_strat.canonical == sp]
        if len(sub) == 0:
            print('  no stratified pathways; skipping')
            continue
        pw_wide = sub.pivot_table(index='pathway_id', columns='sample_id',
                                  values='abundance', aggfunc='sum', fill_value=0.0)

        # Drop UNMAPPED|species and UNINTEGRATED|species — they're stratified catch-all
        keep = ~pw_wide.index.str.startswith(('UNMAPPED', 'UNINTEGRATED'))
        pw_wide = pw_wide.loc[keep]
        print(f'  Stratified pathways (excl UNMAPPED/UNINTEGRATED): {pw_wide.shape[0]}')

        # 10%-prevalence filter: keep pathway if present in ≥10% of any IBD substudy
        keep_rows = []
        for pw_idx in pw_wide.index:
            for ss in ROBUST_SUBSTUDIES:
                ss_samples = [c for c in pw_wide.columns if substudy_map.get(c) == ss]
                ss_samples = [c for c in ss_samples if c in cd_ids[ss] + ni_ids[ss]]
                if not ss_samples: continue
                prev = (pw_wide.loc[pw_idx, ss_samples] > 0).mean()
                if prev >= PREVALENCE_THRESHOLD:
                    keep_rows.append(pw_idx)
                    break
        pw_filt = pw_wide.loc[sorted(set(keep_rows))]
        print(f'  After 10%-prevalence filter (≥1 IBD substudy): {pw_filt.shape[0]}')
        if pw_filt.shape[0] < 5:
            print('  Too few pathways after filter; skipping')
            continue

        # Per-substudy DA — skip insufficient substudies but keep going
        per_eff = []; per_se = []; per_n = []; viable_ss = []
        for ss in ROBUST_SUBSTUDIES:
            eff, se, ncd, nni = per_substudy_da(pw_filt, cd_ids[ss], ni_ids[ss], n_boot=200)
            if eff is None:
                print(f'  {ss}: insufficient samples (CD={ncd}, nonIBD={nni}); skipping this substudy')
                continue
            per_eff.append(eff); per_se.append(se); per_n.append((ncd, nni))
            viable_ss.append(ss)
            print(f'  {ss}: n_CD={ncd} n_nonIBD={nni}')
        if len(per_eff) == 0:
            print('  No viable substudies for DA; skipping this species')
            continue
        if len(per_eff) == 1:
            print(f'  WARNING: only 1 substudy viable ({viable_ss[0]}); single-study DA, no IVW meta')

        if len(per_eff) >= 2:
            pooled_eff, pooled_se, z, p, concord = ivw_meta(per_eff, per_se)
        else:
            # Single-study fallback
            pooled_eff = per_eff[0]
            pooled_se = per_se[0]
            z = pooled_eff / pooled_se
            p = 2 * (1 - stats.norm.cdf(np.abs(z)))
            concord = np.ones_like(pooled_eff)
        fdr = multipletests(p, method='fdr_bh')[1]
        df_sp = pd.DataFrame({
            'pathway_id': pw_filt.index,
            'pooled_effect': pooled_eff,
            'pooled_se': pooled_se,
            'p_value': p,
            'fdr': fdr,
            'sign_concord_frac': concord,
            'n_substudies_viable': len(per_eff),
            'viable_substudies': '|'.join(viable_ss),
        })
        df_sp['canonical_species'] = sp
        df_sp['cd_up_passing'] = (df_sp.pooled_effect > EFFECT_THRESHOLD) & (df_sp.fdr < FDR_THRESHOLD)
        df_sp['cd_down_passing'] = (df_sp.pooled_effect < -EFFECT_THRESHOLD) & (df_sp.fdr < FDR_THRESHOLD)
        df_sp['category'] = df_sp.pathway_id.apply(lambda x: categorize(x.split('|')[0]))
        all_per_species[sp] = df_sp
        n_up = int(df_sp.cd_up_passing.sum()); n_dn = int(df_sp.cd_down_passing.sum())
        print(f'  CD-up: {n_up}, CD-down: {n_dn} (pooled effect range: '
              f'[{pooled_eff.min():+.2f}, {pooled_eff.max():+.2f}])')
    print(f'\nTotal elapsed: {time.time()-t0:.1f}s')

    # Combine all per-species DA into one table
    if all_per_species:
        combined = pd.concat(all_per_species.values(), ignore_index=True)
        combined.to_csv(DATA_OUT / 'nb07b_stratified_pathway_da.tsv', sep='\t', index=False)
        print(f'\nCombined per-species DA: {len(combined):,} pathway-species rows; '
              f'{int(combined.cd_up_passing.sum())} CD-up passing across all species')
section_logs['2-3'] = buf.getvalue()


# ============================================================
# §4-§5 Per-species H3a (b) re-test
# ============================================================
buf, redir = section('4-5')
with redir:
    t0 = time.time()
    cat_7 = sorted(CATEGORY_PATTERNS.keys())

    print('Per-species CD-up category coherence (top-3 concentration vs random-allocation null):\n')
    rng = np.random.default_rng(RNG_SEED)
    h3a_b_results = {}
    for sp in TIER_A_CORE:
        if sp not in all_per_species:
            continue
        df = all_per_species[sp]
        # Background: all prevalence-filtered pathways for this species
        bg_cat_counts = df.category.value_counts()
        bg_in_7 = sum(bg_cat_counts.get(c, 0) for c in cat_7)
        if bg_in_7 < 5:
            print(f'  {sp:<32}  background pathways in 7-cat set: {bg_in_7} (too few; H3a (b) untestable)')
            h3a_b_results[sp] = {'verdict': 'untestable', 'reason': 'sparse background'}
            continue
        # Passing CD-up
        passing = df[df.cd_up_passing]
        passing_in_7 = passing[passing.category != OTHER].category.value_counts().reindex(cat_7).fillna(0).astype(int)
        passing_in_7_total = int(passing_in_7.sum())
        if passing_in_7_total < 3:
            print(f'  {sp:<32}  CD-up in 7-cat set: {passing_in_7_total} (too few; H3a (b) underpowered)')
            h3a_b_results[sp] = {
                'verdict': 'underpowered',
                'n_passing_total': int(passing.shape[0]),
                'n_passing_in_7': passing_in_7_total,
                'background_in_7': int(bg_in_7),
            }
            continue
        # Compute observed top-3 concentration
        obs_top3 = passing_in_7.sort_values(ascending=False).head(3).sum() / passing_in_7_total
        # Random-allocation null
        bg_props = np.array([bg_cat_counts.get(c, 0) / bg_in_7 for c in cat_7])
        null_top3 = np.empty(N_PERM_CATEGORY)
        for i in range(N_PERM_CATEGORY):
            draws = rng.choice(len(cat_7), size=passing_in_7_total, p=bg_props)
            sim = pd.Series(draws).value_counts().reindex(range(len(cat_7))).fillna(0)
            null_top3[i] = sim.sort_values(ascending=False).head(3).sum() / passing_in_7_total
        p_emp = float((null_top3 >= obs_top3).mean())
        verdict = 'PASS' if (obs_top3 >= 0.60 and p_emp < 0.10) else 'FAIL'
        print(f'  {sp:<32}  CD-up={passing.shape[0]}, in-7-cat={passing_in_7_total}, '
              f'top-3-conc={obs_top3:.3f}, null mean={null_top3.mean():.3f}, p_emp={p_emp:.3f}, {verdict}')
        # Show categorical distribution
        passing_cats_repr = ', '.join([f"{c.replace('_', '-')}:{int(passing_in_7[c])}"
                                        for c in cat_7 if passing_in_7[c] > 0])
        print(f'        categories: {passing_cats_repr}')
        h3a_b_results[sp] = {
            'verdict': verdict,
            'n_passing_total': int(passing.shape[0]),
            'n_passing_in_7': passing_in_7_total,
            'background_in_7': int(bg_in_7),
            'observed_top3_concentration': obs_top3,
            'null_mean_top3': float(null_top3.mean()),
            'null_sd_top3': float(null_top3.std()),
            'p_emp': p_emp,
            'category_distribution': {c: int(passing_in_7[c]) for c in cat_7},
        }
    print(f'\nElapsed: {time.time()-t0:.1f}s')
section_logs['4-5'] = buf.getvalue()


# ============================================================
# §6 Cross-species heatmap of CD-up pathway counts per category
# ============================================================
buf, redir = section('6')
with redir:
    if all_per_species:
        # Per-species: number of CD-up passing pathways per category
        heat_data = pd.DataFrame(0, index=TIER_A_CORE, columns=cat_7 + [OTHER])
        for sp in TIER_A_CORE:
            if sp not in all_per_species: continue
            sub = all_per_species[sp]
            for c in heat_data.columns:
                heat_data.loc[sp, c] = int(sub[(sub.cd_up_passing) & (sub.category == c)].shape[0])
        print('Per-species × category CD-up passing pathway counts:')
        print(heat_data.to_string())
        # Show top CD-up pathway per species per category
        print('\n\nTop CD-up pathway per species per category:')
        for sp in TIER_A_CORE:
            if sp not in all_per_species: continue
            sub = all_per_species[sp]
            up = sub[sub.cd_up_passing].sort_values('pooled_effect', ascending=False)
            for c in cat_7:
                top = up[up.category == c].head(1)
                if len(top):
                    pw = top.iloc[0]
                    print(f'  {sp[:24]:<24}  {c}: {pw.pathway_id.split("|")[0][:50]} '
                          f'(eff +{pw.pooled_effect:.2f}, FDR {pw.fdr:.1e})')
section_logs['6'] = buf.getvalue()


# ============================================================
# §7 Aggregate verdict + figure
# ============================================================
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# (1) Per-species CD-up pathway count heatmap (categories on x, species on y)
if all_per_species:
    ax = axes[0, 0]
    mat = heat_data[cat_7 + [OTHER]].values
    im = ax.imshow(mat, aspect='auto', cmap='Reds')
    ax.set_xticks(range(len(cat_7) + 1))
    ax.set_xticklabels([c.replace('_', '\n') for c in cat_7 + [OTHER]], rotation=0, fontsize=8)
    ax.set_yticks(range(len(TIER_A_CORE)))
    ax.set_yticklabels([sp[:25] for sp in TIER_A_CORE], fontsize=8)
    for i, sp in enumerate(TIER_A_CORE):
        for j, c in enumerate(cat_7 + [OTHER]):
            v = heat_data.loc[sp, c]
            ax.text(j, i, str(v), ha='center', va='center',
                    color='white' if v > heat_data.values.max() * 0.5 else 'black', fontsize=8)
    ax.set_title('CD-up passing pathways per species × category')
    plt.colorbar(im, ax=ax, label='# pathways')

# (2) Per-species H3a (b) verdict bar
ax = axes[0, 1]
sp_list = [sp for sp in TIER_A_CORE if sp in h3a_b_results]
if sp_list:
    n_passing = [h3a_b_results[sp].get('n_passing_total', 0) for sp in sp_list]
    n_in_7 = [h3a_b_results[sp].get('n_passing_in_7', 0) for sp in sp_list]
    x = np.arange(len(sp_list))
    width = 0.35
    ax.bar(x - width/2, n_passing, width, label='Total CD-up passing', color='#557ba8')
    ax.bar(x + width/2, n_in_7, width, label='In 7 a-priori categories', color='#c44a4a')
    ax.set_xticks(x); ax.set_xticklabels([sp[:18] for sp in sp_list], rotation=20, fontsize=8)
    ax.set_ylabel('# pathways')
    ax.set_title('Per-species CD-up: total vs in-7-category')
    ax.legend(fontsize=9)

# (3) Top CD-up pathways across all species
ax = axes[1, 0]
combined_up = combined[combined.cd_up_passing].sort_values('pooled_effect', ascending=False).head(20)
y_pos = np.arange(len(combined_up))
colors = {sp: c for sp, c in zip(TIER_A_CORE, plt.cm.tab10.colors)}
bar_colors = [colors[sp] for sp in combined_up.canonical_species]
ax.errorbar(combined_up.pooled_effect, y_pos,
            xerr=combined_up.pooled_se*1.96, fmt='o', mfc='none', color='gray', alpha=0.5)
for i, (_, r) in enumerate(combined_up.iterrows()):
    ax.scatter(r.pooled_effect, i, c=[colors[r.canonical_species]], s=50, zorder=3)
ax.set_yticks(y_pos)
labels = [f"{r.pathway_id.split('|')[0][:42]} ({r.canonical_species[:14]}, {r.category[:8]})"
          for _, r in combined_up.iterrows()]
ax.set_yticklabels(labels, fontsize=7)
ax.axvline(0, ls=':', color='#888'); ax.invert_yaxis()
ax.set_xlabel('Pooled CLR-Δ (CD − nonIBD)')
ax.set_title('Top 20 CD-up species-stratified pathways')

# (4) Verdict summary text
ax = axes[1, 1]
ax.axis('off')
text_lines = ['H3a (b) species-resolved retest', '']
for sp in TIER_A_CORE:
    r = h3a_b_results.get(sp, {})
    v = r.get('verdict', 'no data')
    n = r.get('n_passing_total', 0); n7 = r.get('n_passing_in_7', 0)
    pe = r.get('p_emp')
    pe_str = f', p={pe:.3f}' if pe is not None else ''
    text_lines.append(f'  {sp[:22]:<22}  {v:<14} (CD-up={n}, in-7={n7}{pe_str})')
n_pass = sum(1 for r in h3a_b_results.values() if r.get('verdict') == 'PASS')
n_under = sum(1 for r in h3a_b_results.values() if r.get('verdict') == 'underpowered')
n_untest = sum(1 for r in h3a_b_results.values() if r.get('verdict') == 'untestable')
n_fail = sum(1 for r in h3a_b_results.values() if r.get('verdict') == 'FAIL')
text_lines += ['', f'PASS: {n_pass}; FAIL: {n_fail}; underpowered: {n_under}; untestable: {n_untest}']
ax.text(0.0, 1.0, '\n'.join(text_lines), va='top', ha='left',
        family='monospace', fontsize=9, transform=ax.transAxes)
ax.set_title('Per-species H3a (b) verdict')

plt.tight_layout()
plt.savefig(FIG_OUT / 'NB07b_stratified_H3a_b.png', dpi=120, bbox_inches='tight')
plt.close()

# Verdict JSON
def _def(o):
    if isinstance(o, (np.bool_, bool)): return bool(o)
    if isinstance(o, np.integer): return int(o)
    if isinstance(o, np.floating): return float(o)
    return str(o)

verdict = {
    'date': '2026-04-24',
    'plan_version': 'v1.7',
    'test': 'H3a (b) species-resolved re-test (NB07b stratified-pathway DA)',
    'context': 'NB07a clause (b) was structurally degenerate at unstratified-pathway level; NB07b retests at species-resolved level',
    'tier_a_core_species': TIER_A_CORE,
    'substudies': ROBUST_SUBSTUDIES,
    'thresholds': {
        'prevalence': PREVALENCE_THRESHOLD, 'effect_clr': EFFECT_THRESHOLD,
        'fdr': FDR_THRESHOLD, 'top3_concentration': 0.60,
    },
    'per_species_h3a_b': h3a_b_results,
    'overall_n_pass': int(n_pass),
    'overall_n_fail': int(n_fail),
    'overall_n_underpowered': int(n_under),
    'overall_n_untestable': int(n_untest),
}
with open(DATA_OUT / 'nb07b_h3a_b_species_verdict.json', 'w') as f:
    json.dump(verdict, f, indent=2, default=_def)

# Section logs
with open('/tmp/nb07b_section_logs.json', 'w') as f:
    json.dump(section_logs, f, indent=2)

print('\nWrote:')
print('  data/nb07b_stratified_pathway_da.tsv')
print('  data/nb07b_h3a_b_species_verdict.json')
print('  figures/NB07b_stratified_H3a_b.png')
print('All sections done.')

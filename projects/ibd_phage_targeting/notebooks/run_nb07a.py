"""NB07a — Within-IBD-substudy CD-vs-nonIBD pathway DA + H3a v1.7 three-clause falsifiability.

Per RESEARCH_PLAN.md v1.7 §NB07a + §H3a:

§0 Substudy × diagnosis crosstab on fact_pathway_abundance (verify v1.7 plan claims).
   - Robust: HallAB_2017 (88/72), IjazUZ_2017 (56/38), NielsenHB_2014 (21/248)
   - Boundary: LiJ_2014 (76/10) — sensitivity test only
   - Excluded: VilaAV_2018 (216/0), IaniroG_2022 (0 nonIBD; 88 CDI etc., not CD vs nonIBD)

§1 Pathway wide matrix construction:
   - Unstratified MetaCyc pathways only (drop "|species" suffix forms)
   - Drop UNMAPPED + UNINTEGRATED catch-all categories
   - 10%-prevalence filter per-substudy (keep if ≥ 10% in at least one IBD substudy)

§2 Per-substudy CLR-Δ CD-vs-nonIBD with bootstrap SE.

§3 Inverse-variance-weighted meta across the 3 robust substudies; LiJ_2014 sensitivity sidecar.

§4-§5 H3a (a) — pathway count under permutation null:
   - 1000 permutations of diagnosis labels within each substudy
   - Recount pathways passing FDR < 0.10 with pooled-effect > 0.5
   - Empirical p = fraction of permutations with count ≥ observed

§6 MetaCyc category mapping via descriptive-name string patterns (7 a-priori categories).

§7-§8 H3a (b) — category concentration under random-allocation null:
   - 1000 random allocations of N passing pathways to 7 categories proportional to background
   - Compute fraction in top-3 categories per draw
   - Empirical p for observed concentration

§9 Pathway × Tier-A-core species Spearman ρ; per-substudy + meta.

§10 H3a (c) — pathway-pathobiont attribution under permutation null:
   - 200 permutations of pathway abundance across samples within substudy
   - Max |ρ| per pair against null

§11 Verdict aggregation per H3a v1.7 falsifiability.
§12 Figures + outputs.
"""
import warnings; warnings.filterwarnings('ignore')
from pathlib import Path
import json, io, sys, contextlib, time
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

# v1.7 anchors per plan
ROBUST_SUBSTUDIES = ['HallAB_2017', 'IjazUZ_2017', 'NielsenHB_2014']
SENSITIVITY_SUBSTUDIES = ['LiJ_2014']
TIER_A_CORE = [
    'Hungatella hathewayi', 'Mediterraneibacter gnavus', 'Escherichia coli',
    'Eggerthella lenta', 'Flavonifractor plautii', 'Enterocloster bolteae',
]
RNG_SEED = 42
N_PERM_COUNT = 1000        # H3a (a) permutation null
N_PERM_CATEGORY = 1000     # H3a (b) random-allocation null
N_PERM_ATTRIBUTION = 200   # H3a (c) permutation null
PREVALENCE_THRESHOLD = 0.10
EFFECT_THRESHOLD = 0.5
FDR_THRESHOLD = 0.10
RHO_THRESHOLD = 0.4

section_logs = {}
def section(name):
    buf = io.StringIO()
    return buf, contextlib.redirect_stdout(buf)

# ============================================================
# §0 Substudy verification + load samples
# ============================================================
buf, redir = section('0')
with redir:
    print(f'NB07a — H3a v1.7 falsifiability test')
    print(f'Robust substudies (primary meta): {ROBUST_SUBSTUDIES}')
    print(f'Sensitivity substudy: {SENSITIVITY_SUBSTUDIES}')
    print(f'Tier-A core species: {TIER_A_CORE}')
    print()
    t0 = time.time()
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
    eco_map = dict(zip(eco.sample_id, eco.consensus_ecotype))

    pa = pd.read_parquet(DATA_MART / 'fact_pathway_abundance.snappy.parquet')
    print(f'Pathway raw rows: {len(pa):,}; samples: {pa.sample_id.nunique():,}; pathways: {pa.pathway_id.nunique():,}')

    # Verified crosstab
    pa_samples = pa.sample_id.unique()
    sm = pd.DataFrame({
        'sample_id': pa_samples,
        'substudy': [substudy_map.get(s) for s in pa_samples],
        'diagnosis': [diag_map.get(s) for s in pa_samples],
    })
    sm = sm[sm.substudy.notna()]
    tbl = sm.groupby('substudy').diagnosis.value_counts().unstack(fill_value=0).fillna(0).astype(int)
    print(f'\nPathway-modality substudy × diagnosis (CD/nonIBD-relevant rows):')
    cols = [c for c in ['CD', 'nonIBD'] if c in tbl.columns]
    print(tbl[cols].sort_values('CD', ascending=False).to_string())
    print(f'\nElapsed: {time.time()-t0:.1f}s')
section_logs['0'] = buf.getvalue()

# ============================================================
# §1 Wide matrix construction (unstratified, drop catch-all, prevalence filter)
# ============================================================
buf, redir = section('1')
with redir:
    t0 = time.time()
    # Unstratified pathways only (no "|" suffix) and drop UNMAPPED/UNINTEGRATED
    is_unstrat = ~pa.pathway_id.str.contains('\\|', na=False, regex=True)
    is_informative = ~pa.pathway_id.str.startswith(('UNMAPPED', 'UNINTEGRATED'))
    pa_u = pa[is_unstrat & is_informative].copy()
    print(f'Unstratified informative pathway rows: {len(pa_u):,} ({pa_u.pathway_id.nunique():,} pathways)')

    # Pivot
    pw_wide = pa_u.pivot_table(index='pathway_id', columns='sample_id',
                               values='abundance', aggfunc='sum', fill_value=0.0)
    print(f'Wide matrix: {pw_wide.shape[0]:,} pathways × {pw_wide.shape[1]:,} samples')

    # 10%-prevalence filter: keep pathway if present in ≥10% of samples in at least one IBD substudy
    sample_substudy = pd.Series({s: substudy_map.get(s) for s in pw_wide.columns})
    keep_pathways = []
    for pw in pw_wide.index:
        for ss in ROBUST_SUBSTUDIES + SENSITIVITY_SUBSTUDIES:
            cols = sample_substudy[sample_substudy == ss].index.tolist()
            cols = [c for c in cols if c in pw_wide.columns]
            if not cols: continue
            prev = (pw_wide.loc[pw, cols] > 0).mean()
            if prev >= PREVALENCE_THRESHOLD:
                keep_pathways.append(pw)
                break
    pw_filt = pw_wide.loc[sorted(set(keep_pathways))]
    print(f'After 10%-prevalence filter (≥1 IBD substudy): {pw_filt.shape[0]:,} pathways')
    print(f'Elapsed: {time.time()-t0:.1f}s')

    # Per-substudy CD/nonIBD sample id splits
    cd_ids = {}; ni_ids = {}
    for ss in ROBUST_SUBSTUDIES + SENSITIVITY_SUBSTUDIES:
        cd_ids[ss] = sm[(sm.substudy == ss) & (sm.diagnosis == 'CD')].sample_id.tolist()
        ni_ids[ss] = sm[(sm.substudy == ss) & (sm.diagnosis == 'nonIBD')].sample_id.tolist()
        print(f'  {ss}: CD={len(cd_ids[ss])}, nonIBD={len(ni_ids[ss])}')
section_logs['1'] = buf.getvalue()


# ============================================================
# §2-§3 Per-substudy CLR-Δ + bootstrap SE; IVW meta
# ============================================================
def clr(M):
    """CLR transform on species/pathway × samples matrix."""
    M = M.astype(float).copy()
    col_min_nz = np.where(M > 0, M, np.nan)
    col_min_nz = np.nanmin(col_min_nz, axis=0)
    col_min_nz = np.where(np.isnan(col_min_nz), 1e-6, col_min_nz / 2)
    M = np.where(M > 0, M, col_min_nz[None, :])
    logM = np.log(M)
    return logM - logM.mean(axis=0, keepdims=True)


def per_substudy_da(pw_wide_sub, cd_ids, ni_ids, n_boot=300, seed=42):
    """Per-pathway CLR-Δ (mean CLR_CD − mean CLR_nonIBD) with bootstrap SE.
    Returns (effect_vec, se_vec) of length n_pathways."""
    cd_ = [c for c in cd_ids if c in pw_wide_sub.columns]
    ni_ = [c for c in ni_ids if c in pw_wide_sub.columns]
    if min(len(cd_), len(ni_)) < 5:
        return None, None, len(cd_), len(ni_)
    cols = cd_ + ni_
    full_clr = clr(pw_wide_sub[cols].values)  # pathways × samples
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


def ivw_meta(per_study_effects, per_study_ses):
    """Inverse-variance-weighted meta. Returns pooled_effect, pooled_se, z, p, sign_concord_frac."""
    eff = np.stack(per_study_effects, axis=0)   # K × P
    se = np.stack(per_study_ses, axis=0) + 1e-9
    w = 1.0 / (se ** 2)
    pooled_eff = (eff * w).sum(axis=0) / w.sum(axis=0)
    pooled_se = 1.0 / np.sqrt(w.sum(axis=0))
    # Sign concordance
    sign_match = (np.sign(eff) == np.sign(pooled_eff)).mean(axis=0)
    z = pooled_eff / pooled_se
    p = 2 * (1 - stats.norm.cdf(np.abs(z)))
    return pooled_eff, pooled_se, z, p, sign_match


buf, redir = section('2-3')
with redir:
    t0 = time.time()
    per_study = {}
    for ss in ROBUST_SUBSTUDIES + SENSITIVITY_SUBSTUDIES:
        eff, se, n_cd, n_ni = per_substudy_da(pw_filt, cd_ids[ss], ni_ids[ss], n_boot=300)
        per_study[ss] = (eff, se, n_cd, n_ni)
        print(f'{ss}: n_CD={n_cd} n_nonIBD={n_ni} eff_range=[{eff.min():.2f}, {eff.max():.2f}] mean_se={se.mean():.3f}')
    # Primary meta (3 robust substudies)
    primary_eff, primary_se, primary_z, primary_p, primary_concord = ivw_meta(
        [per_study[s][0] for s in ROBUST_SUBSTUDIES],
        [per_study[s][1] for s in ROBUST_SUBSTUDIES],
    )
    primary_fdr = multipletests(primary_p, method='fdr_bh')[1]
    print(f'\nPrimary meta (3 substudies):')
    print(f'  pooled effect: range=[{primary_eff.min():.2f}, {primary_eff.max():.2f}], '
          f'median={np.median(primary_eff):.3f}')
    print(f'  pooled SE: mean={primary_se.mean():.3f}')
    print(f'  passing |effect|>{EFFECT_THRESHOLD} AND FDR<{FDR_THRESHOLD}: '
          f'{((np.abs(primary_eff) > EFFECT_THRESHOLD) & (primary_fdr < FDR_THRESHOLD)).sum()} '
          f'(of which CD-up: {((primary_eff > EFFECT_THRESHOLD) & (primary_fdr < FDR_THRESHOLD)).sum()})')
    print(f'Elapsed: {time.time()-t0:.1f}s')

    # Sensitivity meta (3 robust + LiJ)
    sens_eff, sens_se, sens_z, sens_p, sens_concord = ivw_meta(
        [per_study[s][0] for s in ROBUST_SUBSTUDIES + SENSITIVITY_SUBSTUDIES],
        [per_study[s][1] for s in ROBUST_SUBSTUDIES + SENSITIVITY_SUBSTUDIES],
    )
    sens_fdr = multipletests(sens_p, method='fdr_bh')[1]
    print(f'Sensitivity meta (4 substudies, including LiJ_2014 boundary):')
    print(f'  passing |effect|>{EFFECT_THRESHOLD} AND FDR<{FDR_THRESHOLD}: '
          f'{((np.abs(sens_eff) > EFFECT_THRESHOLD) & (sens_fdr < FDR_THRESHOLD)).sum()}')

    # Save the meta DataFrame
    meta_df = pd.DataFrame({
        'pathway_id': pw_filt.index,
        'pooled_effect': primary_eff,
        'pooled_se': primary_se,
        'z': primary_z,
        'p_value': primary_p,
        'fdr': primary_fdr,
        'sign_concord_frac': primary_concord,
        'sensitivity_effect': sens_eff,
        'sensitivity_fdr': sens_fdr,
    })
    meta_df['cd_up_passing'] = (meta_df.pooled_effect > EFFECT_THRESHOLD) & (meta_df.fdr < FDR_THRESHOLD)
    meta_df['cd_down_passing'] = (meta_df.pooled_effect < -EFFECT_THRESHOLD) & (meta_df.fdr < FDR_THRESHOLD)
    meta_df.to_csv(DATA_OUT / 'nb07a_pathway_meta.tsv', sep='\t', index=False)
section_logs['2-3'] = buf.getvalue()


# ============================================================
# §4-§5 H3a clause (a) — observed pathway count + permutation null
# ============================================================
buf, redir = section('4-5')
with redir:
    t0 = time.time()
    observed_count = int(meta_df.cd_up_passing.sum())
    observed_count_dn = int(meta_df.cd_down_passing.sum())
    observed_count_either = int(((np.abs(primary_eff) > EFFECT_THRESHOLD) & (primary_fdr < FDR_THRESHOLD)).sum())
    print(f'Observed (CD-up): {observed_count} pathways pass |effect|>{EFFECT_THRESHOLD} + FDR<{FDR_THRESHOLD}')
    print(f'Observed (CD-down): {observed_count_dn}')
    print(f'Observed (either dir): {observed_count_either}')

    # Permutation null: shuffle diagnosis labels within each substudy, recompute meta + count
    print(f'\nRunning {N_PERM_COUNT}-permutation null on pathway count...')
    rng = np.random.default_rng(RNG_SEED)
    perm_counts_up = np.empty(N_PERM_COUNT, dtype=int)
    perm_counts_dn = np.empty(N_PERM_COUNT, dtype=int)
    perm_counts_either = np.empty(N_PERM_COUNT, dtype=int)

    # Pre-extract per-substudy CLR matrices to avoid recomputing
    substudy_clrs = {}
    substudy_n_cds = {}
    for ss in ROBUST_SUBSTUDIES:
        cd_ = [c for c in cd_ids[ss] if c in pw_filt.columns]
        ni_ = [c for c in ni_ids[ss] if c in pw_filt.columns]
        cols = cd_ + ni_
        substudy_clrs[ss] = clr(pw_filt[cols].values)
        substudy_n_cds[ss] = len(cd_)

    P = pw_filt.shape[0]
    for perm_i in range(N_PERM_COUNT):
        # Per-substudy: permute diagnosis labels (shuffle CD/nonIBD assignment), recompute effect
        per_perm_eff = []
        per_perm_se = []
        for ss in ROBUST_SUBSTUDIES:
            X = substudy_clrs[ss]  # P × N
            n_cd = substudy_n_cds[ss]
            n_total = X.shape[1]
            # Shuffle labels: randomly select n_cd indices for "CD"
            idx = rng.permutation(n_total)
            cd_idx = idx[:n_cd]; ni_idx = idx[n_cd:]
            eff = X[:, cd_idx].mean(axis=1) - X[:, ni_idx].mean(axis=1)
            # Approximate SE via per-substudy CLR variance (much faster than bootstrap per perm)
            # Use pooled-variance: var(diff) = var(X)/n_cd + var(X)/n_ni
            var_p = X.var(axis=1)
            se = np.sqrt(var_p / n_cd + var_p / (n_total - n_cd))
            per_perm_eff.append(eff)
            per_perm_se.append(se)
        # Meta
        eff_stack = np.stack(per_perm_eff)
        se_stack = np.stack(per_perm_se) + 1e-9
        w = 1.0 / (se_stack ** 2)
        pooled_eff_perm = (eff_stack * w).sum(axis=0) / w.sum(axis=0)
        pooled_se_perm = 1.0 / np.sqrt(w.sum(axis=0))
        z_perm = pooled_eff_perm / pooled_se_perm
        p_perm = 2 * (1 - stats.norm.cdf(np.abs(z_perm)))
        fdr_perm = multipletests(p_perm, method='fdr_bh')[1]
        perm_counts_up[perm_i] = ((pooled_eff_perm > EFFECT_THRESHOLD) & (fdr_perm < FDR_THRESHOLD)).sum()
        perm_counts_dn[perm_i] = ((pooled_eff_perm < -EFFECT_THRESHOLD) & (fdr_perm < FDR_THRESHOLD)).sum()
        perm_counts_either[perm_i] = ((np.abs(pooled_eff_perm) > EFFECT_THRESHOLD) & (fdr_perm < FDR_THRESHOLD)).sum()

    p_emp_up = (perm_counts_up >= observed_count).mean()
    p_emp_either = (perm_counts_either >= observed_count_either).mean()
    print(f'Permutation null:')
    print(f'  CD-up count: observed {observed_count}, null mean {perm_counts_up.mean():.1f} ± {perm_counts_up.std():.1f}, '
          f'p_emp = {p_emp_up:.4f}')
    print(f'  Either-direction count: observed {observed_count_either}, '
          f'null mean {perm_counts_either.mean():.1f} ± {perm_counts_either.std():.1f}, p_emp = {p_emp_either:.4f}')
    h3a_a_pass = (observed_count >= 10) and (p_emp_up < 0.10)
    print(f'\nH3a (a) verdict: {"PASS" if h3a_a_pass else "FAIL"} (≥10 pathways AND p_emp < 0.10)')
    print(f'Elapsed: {time.time()-t0:.1f}s')
section_logs['4-5'] = buf.getvalue()


# ============================================================
# §6 MetaCyc category mapping
# ============================================================
buf, redir = section('6')
with redir:
    # 7 a-priori categories per RESEARCH_PLAN.md §Expected outcomes (v1.7 H3a)
    CATEGORY_PATTERNS = {
        '1_bile_acid': r'(?i)bile|cholate|deoxycholate|7-?alpha|7ALPHA',
        '2_mucin_glycan': r'(?i)mucin|fucose|N-acetyl|sialic|GlcNAc|galactosamine|glycan|polyol|alginate',
        '3_sulfur_redox': r'(?i)sulfate|sulfite|thiosulfate|hydrogen sulfide|sulfidogenesis|dissimilatory sulf|tetrathionate',
        '4_TMA_choline': r'(?i)trimethylamine|TMAO|choline|betaine|carnitine',
        '5_eut_pdu': r'(?i)ethanolamine|propanediol|propanoate fermentation',
        '6_polyamine_urea': r'(?i)polyamine|putrescine|spermidine|urease|urea cycle|nitrogen fixation',
        '7_AA_decarb': r'(?i)tryptophanase|decarboxylation|indole|histidine degradation|arginine degradation|ornithine|lysine degradation',
    }
    OTHER = '0_other'

    def categorize(pw_id):
        for cat, pat in CATEGORY_PATTERNS.items():
            if pd.Series([pw_id]).str.contains(pat, regex=True, na=False).iloc[0]:
                return cat
        return OTHER

    meta_df['category'] = meta_df.pathway_id.map(categorize)
    cat_dist = meta_df.category.value_counts().sort_index()
    print(f'Background category distribution (all {len(meta_df)} prevalence-filtered pathways):')
    print(cat_dist.to_string())
    print()
    print(f'Passing-pathway category distribution (CD-up, {observed_count} pathways):')
    passing_cat_dist = meta_df[meta_df.cd_up_passing].category.value_counts().sort_index()
    print(passing_cat_dist.to_string())

    # Show actual passing pathways per category (for inspection)
    print(f'\nTop pathway in each category among passing:')
    for cat in sorted(meta_df.category.unique()):
        sub = meta_df[meta_df.cd_up_passing & (meta_df.category == cat)].sort_values('pooled_effect', ascending=False)
        if len(sub):
            top = sub.iloc[0]
            print(f'  {cat}: {top.pathway_id[:90]} (effect {top.pooled_effect:+.2f}, FDR {top.fdr:.2e})')
section_logs['6'] = buf.getvalue()


# ============================================================
# §7-§8 H3a clause (b) — category coherence under random-allocation null
# ============================================================
buf, redir = section('7-8')
with redir:
    t0 = time.time()
    n_passing = observed_count  # CD-up passing pathways
    if n_passing < 1:
        print('No CD-up passing pathways to test category coherence.')
        h3a_b_pass = False
    else:
        # Background category proportions (over all prevalence-filtered pathways)
        cat_counts = meta_df.category.value_counts()
        # Drop OTHER for the "concentrate in ≤ 3 of 7 categories" framing
        cat_7 = sorted([c for c in cat_counts.index if c != OTHER])
        bg_in_7 = sum(cat_counts.get(c, 0) for c in cat_7)
        bg_props = np.array([cat_counts.get(c, 0) / bg_in_7 if bg_in_7 else 0 for c in cat_7])
        print(f'Background props in 7 a-priori categories (excludes "{OTHER}"):')
        for c, p in zip(cat_7, bg_props):
            print(f'  {c}: {p:.3f} ({int(cat_counts.get(c, 0))} pathways)')

        # Observed concentration: fraction of passing pathways (excluding OTHER) in top-3 categories
        passing_in_7 = passing_cat_dist.reindex(cat_7).fillna(0).astype(int)
        passing_in_7_total = int(passing_in_7.sum())
        if passing_in_7_total < 1:
            print('\nAll passing pathways in OTHER category; H3a (b) trivially fails (no coherence).')
            h3a_b_pass = False
            obs_top3 = 0
            null_top3_p = 1.0
        else:
            obs_top3 = passing_in_7.sort_values(ascending=False).head(3).sum() / passing_in_7_total
            print(f'\nObserved: {passing_in_7_total} CD-up pathways in 7-category set; '
                  f'top-3-cat concentration = {obs_top3:.3f}')

            # Random-allocation null: draw N_passing samples from background distribution proportional to bg_props
            rng2 = np.random.default_rng(RNG_SEED)
            null_top3 = np.empty(N_PERM_CATEGORY)
            for i in range(N_PERM_CATEGORY):
                # Sample N_passing pathways from background, proportional to bg_props
                draws = rng2.choice(len(cat_7), size=passing_in_7_total, p=bg_props)
                cat_counts_sim = pd.Series(draws).value_counts().reindex(range(len(cat_7))).fillna(0)
                null_top3[i] = cat_counts_sim.sort_values(ascending=False).head(3).sum() / passing_in_7_total
            null_top3_p = (null_top3 >= obs_top3).mean()
            print(f'Random-allocation null: {null_top3.mean():.3f} ± {null_top3.std():.3f}; '
                  f'p_emp = {null_top3_p:.4f} for observed concentration')
            h3a_b_pass = (obs_top3 >= 0.60) and (null_top3_p < 0.10)
    print(f'\nH3a (b) verdict: {"PASS" if h3a_b_pass else "FAIL"} '
          f'(≥60% in top-3 categories AND p_emp < 0.10)')
    print(f'Elapsed: {time.time()-t0:.1f}s')
section_logs['7-8'] = buf.getvalue()


# ============================================================
# §9 Pathway × Tier-A-core species Spearman ρ (per-substudy + meta)
# ============================================================
buf, redir = section('9')
with redir:
    t0 = time.time()
    # Load species abundance + synonymy
    syn = pd.read_csv(DATA_OUT / 'species_synonymy.tsv', sep='\t')
    lookup = dict(zip(syn.alias, syn.canonical))
    ta = pd.read_parquet(DATA_MART / 'fact_taxon_abundance.snappy.parquet')
    ta = ta[(ta.classification_method == 'metaphlan3') & (ta.study_id.isin(['CMD_HEALTHY','CMD_IBD']))].copy()
    def normalize_format(name):
        if not isinstance(name, str): return None
        if '|' in name:
            parts = [p for p in name.split('|') if p.startswith('s__')]
            return parts[0][3:].replace('_',' ').strip() if parts else None
        return name.replace('[','').replace(']','').strip()
    def resolve(name):
        if not isinstance(name, str): return None
        if name in lookup: return lookup[name]
        fn = normalize_format(name)
        return lookup.get(fn, fn) if fn else None
    ta['species'] = ta['taxon_name_original'].map(resolve)
    ta = ta.dropna(subset=['species'])
    ta_tier_a = ta[ta.species.isin(TIER_A_CORE)]
    print(f'Tier-A-core species rows: {len(ta_tier_a):,}; samples covered: {ta_tier_a.sample_id.nunique():,}')

    # Pivot: species × samples
    sp_wide = ta_tier_a.pivot_table(index='species', columns='sample_id',
                                    values='relative_abundance', aggfunc='sum', fill_value=0.0)

    # For each substudy: compute Spearman ρ per (pathway × Tier-A-species) pair
    common_samples_per_substudy = {}
    for ss in ROBUST_SUBSTUDIES:
        common = [s for s in pw_filt.columns
                  if s in sp_wide.columns and substudy_map.get(s) == ss
                  and (s in cd_ids[ss] or s in ni_ids[ss])]
        common_samples_per_substudy[ss] = common
        print(f'  {ss}: {len(common)} samples with both pathway + species data')

    # Per-substudy Spearman ρ (vectorized via ranks)
    per_ss_rhos = {}  # ss -> (pathways × species) ρ matrix
    n_perm_pairs = {}
    for ss in ROBUST_SUBSTUDIES:
        cols = common_samples_per_substudy[ss]
        if len(cols) < 30:
            print(f'  {ss}: <30 samples, skipping')
            continue
        pw_sub = pw_filt[cols].values  # P × N
        sp_sub = sp_wide.reindex(TIER_A_CORE)[cols].values  # 6 × N
        # Rank-transform each row
        pw_ranks = np.apply_along_axis(lambda x: pd.Series(x).rank(method='average').values, 1, pw_sub)
        sp_ranks = np.apply_along_axis(lambda x: pd.Series(x).rank(method='average').values, 1, sp_sub)
        # Pearson on ranks = Spearman
        pw_c = pw_ranks - pw_ranks.mean(axis=1, keepdims=True)
        pw_n = pw_c / np.sqrt((pw_c ** 2).sum(axis=1, keepdims=True) + 1e-12)
        sp_c = sp_ranks - sp_ranks.mean(axis=1, keepdims=True)
        sp_n = sp_c / np.sqrt((sp_c ** 2).sum(axis=1, keepdims=True) + 1e-12)
        rho = pw_n @ sp_n.T  # P × 6
        per_ss_rhos[ss] = rho

    # Meta: Fisher z-mean across substudies
    rhos_stack = np.stack([per_ss_rhos[ss] for ss in ROBUST_SUBSTUDIES if ss in per_ss_rhos], axis=0)
    z_stack = np.arctanh(np.clip(rhos_stack, -0.999, 0.999))
    z_mean = z_stack.mean(axis=0)
    rho_meta = np.tanh(z_mean)  # P × 6

    # Sign concordance per pair
    sign_concord = (np.sign(rhos_stack) == np.sign(rho_meta)[None, :, :]).mean(axis=0)

    # Tabulate top pathway-species pairs by |ρ_meta|
    pair_rows = []
    for sp_idx, sp_name in enumerate(TIER_A_CORE):
        for pw_idx, pw_id in enumerate(pw_filt.index):
            pair_rows.append({
                'pathway_id': pw_id,
                'species': sp_name,
                'rho_meta': rho_meta[pw_idx, sp_idx],
                'sign_concord_frac': sign_concord[pw_idx, sp_idx],
                'rho_HallAB_2017': per_ss_rhos.get('HallAB_2017', np.full((len(pw_filt), 6), np.nan))[pw_idx, sp_idx] if 'HallAB_2017' in per_ss_rhos else np.nan,
                'rho_IjazUZ_2017': per_ss_rhos.get('IjazUZ_2017', np.full((len(pw_filt), 6), np.nan))[pw_idx, sp_idx] if 'IjazUZ_2017' in per_ss_rhos else np.nan,
                'rho_NielsenHB_2014': per_ss_rhos.get('NielsenHB_2014', np.full((len(pw_filt), 6), np.nan))[pw_idx, sp_idx] if 'NielsenHB_2014' in per_ss_rhos else np.nan,
            })
    pair_df = pd.DataFrame(pair_rows)
    pair_df['abs_rho'] = pair_df.rho_meta.abs()
    pair_df = pair_df.sort_values('abs_rho', ascending=False)
    pair_df.to_csv(DATA_OUT / 'nb07a_pathway_pathobiont_pairs.tsv', sep='\t', index=False)
    print(f'\nTotal pairs: {len(pair_df):,}')
    print(f'Pairs with |rho_meta|>{RHO_THRESHOLD}: {(pair_df.abs_rho > RHO_THRESHOLD).sum()}')
    print(f'\nTop 15 by |rho_meta|:')
    print(pair_df.head(15)[['pathway_id','species','rho_meta','sign_concord_frac']].to_string(index=False))
    print(f'Elapsed: {time.time()-t0:.1f}s')
section_logs['9'] = buf.getvalue()


# ============================================================
# §10 H3a clause (c) — permutation null on max |ρ_meta|
# ============================================================
buf, redir = section('10')
with redir:
    t0 = time.time()
    obs_max_rho = pair_df.abs_rho.iloc[0]
    obs_n_passing = int((pair_df.abs_rho > RHO_THRESHOLD).sum())
    print(f'Observed max |rho_meta|: {obs_max_rho:.3f}')
    print(f'Observed pairs with |rho_meta|>{RHO_THRESHOLD}: {obs_n_passing}')
    print(f'\nRunning {N_PERM_ATTRIBUTION} permutations of pathway abundance within substudy...')

    rng3 = np.random.default_rng(RNG_SEED)
    null_max_rhos = np.empty(N_PERM_ATTRIBUTION)
    null_n_passing = np.empty(N_PERM_ATTRIBUTION, dtype=int)
    for perm_i in range(N_PERM_ATTRIBUTION):
        per_ss_rhos_perm = {}
        for ss in ROBUST_SUBSTUDIES:
            if ss not in per_ss_rhos: continue
            cols = common_samples_per_substudy[ss]
            pw_sub = pw_filt[cols].values
            sp_sub = sp_wide.reindex(TIER_A_CORE)[cols].values
            # Permute pathway abundance ACROSS samples (within substudy)
            perm_idx = rng3.permutation(pw_sub.shape[1])
            pw_sub_perm = pw_sub[:, perm_idx]
            pw_ranks = np.apply_along_axis(lambda x: pd.Series(x).rank(method='average').values, 1, pw_sub_perm)
            sp_ranks = np.apply_along_axis(lambda x: pd.Series(x).rank(method='average').values, 1, sp_sub)
            pw_c = pw_ranks - pw_ranks.mean(axis=1, keepdims=True)
            pw_n = pw_c / np.sqrt((pw_c ** 2).sum(axis=1, keepdims=True) + 1e-12)
            sp_c = sp_ranks - sp_ranks.mean(axis=1, keepdims=True)
            sp_n = sp_c / np.sqrt((sp_c ** 2).sum(axis=1, keepdims=True) + 1e-12)
            per_ss_rhos_perm[ss] = pw_n @ sp_n.T
        rhos_stack_p = np.stack([per_ss_rhos_perm[ss] for ss in ROBUST_SUBSTUDIES if ss in per_ss_rhos_perm], axis=0)
        z_stack_p = np.arctanh(np.clip(rhos_stack_p, -0.999, 0.999))
        rho_meta_p = np.tanh(z_stack_p.mean(axis=0))
        null_max_rhos[perm_i] = np.abs(rho_meta_p).max()
        null_n_passing[perm_i] = (np.abs(rho_meta_p) > RHO_THRESHOLD).sum()
        if (perm_i + 1) % 50 == 0:
            print(f'  {perm_i+1}/{N_PERM_ATTRIBUTION}: null max |rho| range so far = '
                  f'[{null_max_rhos[:perm_i+1].min():.3f}, {null_max_rhos[:perm_i+1].max():.3f}]')

    p_max = (null_max_rhos >= obs_max_rho).mean()
    p_count = (null_n_passing >= obs_n_passing).mean()
    print(f'\nPermutation null:')
    print(f'  max |rho_meta|: observed {obs_max_rho:.3f}, null {null_max_rhos.mean():.3f} ± {null_max_rhos.std():.3f}, p_emp = {p_max:.4f}')
    print(f'  count passing |rho|>{RHO_THRESHOLD}: observed {obs_n_passing}, '
          f'null {null_n_passing.mean():.1f} ± {null_n_passing.std():.1f}, p_emp = {p_count:.4f}')

    # Verdict: ≥1 pair has |rho|>0.4 with permutation p<0.05
    h3a_c_pass = (obs_n_passing >= 1) and (p_max < 0.05)
    print(f'\nH3a (c) verdict: {"PASS" if h3a_c_pass else "FAIL"} '
          f'(≥1 pair |rho|>{RHO_THRESHOLD} AND permutation p<0.05)')
    print(f'Elapsed: {time.time()-t0:.1f}s')
section_logs['10'] = buf.getvalue()


# ============================================================
# §11 H3a verdict aggregation
# ============================================================
buf, redir = section('11')
with redir:
    print('='*70)
    print('H3a v1.7 — three-clause falsifiability verdict')
    print('='*70)
    print(f'\n(a) Pathway count under permutation null (≥10 pathways AND p_emp<0.10)')
    print(f'    Observed CD-up: {observed_count}; null mean {perm_counts_up.mean():.1f}±{perm_counts_up.std():.1f}; p_emp = {p_emp_up:.4f}')
    print(f'    Verdict: {"PASS" if h3a_a_pass else "FAIL"}')
    print(f'\n(b) Category coherence under random-allocation null (≥60% in top-3 categories AND p_emp<0.10)')
    if observed_count >= 1:
        print(f'    Observed top-3 concentration: {obs_top3:.3f}; null mean {null_top3.mean():.3f}±{null_top3.std():.3f}; p_emp = {null_top3_p:.4f}')
    print(f'    Verdict: {"PASS" if h3a_b_pass else "FAIL"}')
    print(f'\n(c) Pathway-pathobiont attribution under permutation null (≥1 pair |rho|>{RHO_THRESHOLD} AND p<0.05)')
    print(f'    Observed pairs |rho|>{RHO_THRESHOLD}: {obs_n_passing}; max |rho| {obs_max_rho:.3f}')
    print(f'    Null max-|rho|: {null_max_rhos.mean():.3f}±{null_max_rhos.std():.3f}; p_emp = {p_max:.4f}')
    print(f'    Verdict: {"PASS" if h3a_c_pass else "FAIL"}')
    print()
    overall = h3a_a_pass and h3a_b_pass and h3a_c_pass
    print(f'OVERALL H3a v1.7: {"SUPPORTED" if overall else "NOT SUPPORTED"}')
    print(f'  (a) {h3a_a_pass}, (b) {h3a_b_pass}, (c) {h3a_c_pass}')
section_logs['11'] = buf.getvalue()


# ============================================================
# §12 Figures + verdict JSON
# ============================================================
fig, axes = plt.subplots(2, 2, figsize=(15, 10))

# (1) Forest plot of top-15 CD-up pathways across substudies
top15 = meta_df[meta_df.cd_up_passing].sort_values('pooled_effect', ascending=False).head(15)
ax = axes[0, 0]
y_pos = np.arange(len(top15))
ax.errorbar(top15.pooled_effect, y_pos, xerr=top15.pooled_se*1.96, fmt='o', color='#c44a4a', label='Pooled (95% CI)')
ax.axvline(0, ls=':', color='#888')
ax.axvline(EFFECT_THRESHOLD, ls='--', color='#444', alpha=0.5, label=f'effect threshold {EFFECT_THRESHOLD}')
ax.set_yticks(y_pos)
ax.set_yticklabels([p[:60] for p in top15.pathway_id], fontsize=7)
ax.set_xlabel('Pooled CLR-Δ (CD − nonIBD)')
ax.set_title(f'Top 15 CD-up pathways (of {observed_count} passing)')
ax.legend(fontsize=8); ax.invert_yaxis()

# (2) Permutation null for pathway count
ax = axes[0, 1]
ax.hist(perm_counts_up, bins=30, color='#557ba8', edgecolor='white', alpha=0.7)
ax.axvline(observed_count, ls='--', color='#c44a4a', linewidth=2, label=f'Observed = {observed_count}\n(null p_emp = {p_emp_up:.3f})')
ax.set_xlabel('CD-up pathway count under permuted diagnosis labels')
ax.set_ylabel('# permutations')
ax.set_title(f'H3a (a): pathway count null (n={N_PERM_COUNT} perms)')
ax.legend(fontsize=8)

# (3) Category enrichment — passing vs background proportions
ax = axes[1, 0]
if observed_count >= 1:
    cat_7 = sorted([c for c in CATEGORY_PATTERNS])
    bg_props = np.array([(meta_df.category == c).mean() for c in cat_7])
    fg_props = np.array([(meta_df[meta_df.cd_up_passing].category == c).mean() if observed_count else 0 for c in cat_7])
    x = np.arange(len(cat_7))
    width = 0.35
    ax.bar(x - width/2, bg_props, width, label=f'Background (n={len(meta_df)})', color='#aaaaaa')
    ax.bar(x + width/2, fg_props, width, label=f'Passing (n={observed_count})', color='#c44a4a')
    ax.set_xticks(x); ax.set_xticklabels([c.replace('_', '\n') for c in cat_7], fontsize=7, rotation=0)
    ax.set_ylabel('Proportion')
    ax.set_title(f'H3a (b): MetaCyc category enrichment\ntop-3 concentration = {obs_top3:.2f} (null p_emp = {null_top3_p:.3f})')
    ax.legend(fontsize=8)
else:
    ax.text(0.5, 0.5, 'No passing pathways', ha='center', va='center', fontsize=12); ax.axis('off')

# (4) Pathway-pathobiont pair |ρ| permutation null
ax = axes[1, 1]
ax.hist(null_max_rhos, bins=30, color='#557ba8', edgecolor='white', alpha=0.7)
ax.axvline(obs_max_rho, ls='--', color='#c44a4a', linewidth=2, label=f'Observed max |rho| = {obs_max_rho:.3f}\n(null p_emp = {p_max:.3f})')
ax.set_xlabel('max |rho_meta(pathway × Tier-A species)| under permuted pathway abundance')
ax.set_ylabel('# permutations')
ax.set_title(f'H3a (c): pathway-pathobiont attribution null (n={N_PERM_ATTRIBUTION} perms)')
ax.legend(fontsize=8)

plt.tight_layout()
plt.savefig(FIG_OUT / 'NB07a_H3a_falsifiability.png', dpi=120, bbox_inches='tight')
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
    'test': 'H3a v1.7 — pathway DA within-IBD-substudy CD-vs-nonIBD meta + 3-clause falsifiability',
    'substudies_primary': ROBUST_SUBSTUDIES,
    'substudies_sensitivity': SENSITIVITY_SUBSTUDIES,
    'tier_a_core_species': TIER_A_CORE,
    'n_pathways_after_prevalence_filter': int(pw_filt.shape[0]),
    'thresholds': {
        'prevalence': PREVALENCE_THRESHOLD, 'effect_clr': EFFECT_THRESHOLD,
        'fdr': FDR_THRESHOLD, 'rho_meta': RHO_THRESHOLD,
    },
    'clause_a_pathway_count': {
        'observed_cd_up': int(observed_count),
        'observed_cd_down': int(observed_count_dn),
        'observed_either': int(observed_count_either),
        'null_mean_up': float(perm_counts_up.mean()),
        'null_sd_up': float(perm_counts_up.std()),
        'p_emp_up': float(p_emp_up),
        'verdict': bool(h3a_a_pass),
    },
    'clause_b_category_coherence': {
        'observed_top3_concentration': float(obs_top3) if observed_count >= 1 else None,
        'null_mean': float(null_top3.mean()) if observed_count >= 1 else None,
        'null_sd': float(null_top3.std()) if observed_count >= 1 else None,
        'p_emp': float(null_top3_p) if observed_count >= 1 else None,
        'verdict': bool(h3a_b_pass),
    },
    'clause_c_pathway_pathobiont_attribution': {
        'observed_max_rho_meta': float(obs_max_rho),
        'observed_n_passing': int(obs_n_passing),
        'null_mean_max_rho': float(null_max_rhos.mean()),
        'null_sd_max_rho': float(null_max_rhos.std()),
        'p_emp_max_rho': float(p_max),
        'verdict': bool(h3a_c_pass),
    },
    'overall_h3a_supported': bool(h3a_a_pass and h3a_b_pass and h3a_c_pass),
}
with open(DATA_OUT / 'nb07a_h3a_verdict.json', 'w') as f:
    json.dump(verdict, f, indent=2, default=_def)

# Save section logs
with open('/tmp/nb07a_section_logs.json', 'w') as f:
    json.dump(section_logs, f, indent=2)

print('\nWrote:')
print('  data/nb07a_pathway_meta.tsv')
print('  data/nb07a_pathway_pathobiont_pairs.tsv')
print('  data/nb07a_h3a_verdict.json')
print('  figures/NB07a_H3a_falsifiability.png')
print('All sections done.')

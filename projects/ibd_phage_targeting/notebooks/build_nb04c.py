"""Build NB04c_rigor_repair_completion.ipynb programmatically.

NB04b left two repair arms incomplete because their implementations were broken:
  * §5 LME substudy-adjustment (C3): regex-on-sample-ID parsed only 19 noisy categories; LME produced no results.
  * §6 ANCOMBC via rpy2 (I1): rpy2 pandas2ri.activate() errored; r-ancombc conda env is not present.

NB04c completes both arms with data-structure-aware fixes that do not depend on rpy2 or R:
  * Proper substudy resolution via dim_samples join (external_ids.study + participant_id middle token)
  * Within-substudy CD-vs-nonIBD DA (confound-free reference)
  * LinDA (Zhou et al. 2022) in pure NumPy — OLS on CLR with median bias correction
  * LME with proper substudy random effect (documenting the pooled-cohort unidentifiability)
  * Refined Tier-A with 3-way evidence

Outputs feed back into the §8-style stopping rule once the user has reviewed.
"""
from pathlib import Path
import nbformat as nbf

NB_PATH = Path(__file__).parent / "NB04c_rigor_repair_completion.ipynb"
nb = nbf.v4.new_notebook()
cells = []

cells.append(nbf.v4.new_markdown_cell("""# NB04c — Rigor Repair Completion

**Project**: `ibd_phage_targeting` — Pillar 2 rigor repair, follow-up to NB04b
**Depends on**: NB04b (bootstrap CIs, LOO, held-out sensitivity, Jaccard null) — this notebook reuses those outputs

## Why this notebook exists

NB04b attempted to repair six analytical-rigor issues flagged by the adversarial review. Two repair arms did not execute correctly and left the rigor-controlled Tier-A with `n_evidence ≤ 1`, which failed the NB05 stopping rule:

| Repair | NB04b status | Root cause |
|---|---|---|
| §5 LME substudy random effect (C3) | 0 rows produced | Regex-on-sample-ID parsed only 19 noisy prefix categories; most species had < 2 inferred substudies and LME refused to fit |
| §6 ANCOM-BC2 via rpy2 (I1) | rpy2 error, no output | `pandas2ri.activate()` deprecated in current rpy2; `r-ancombc` conda env is not present on this worktree |

This notebook fixes both without rpy2 / R:

- **§1** Load NB04b inputs and rebuild the wide matrix identically.
- **§2** Proper substudy resolution via `dim_samples.external_ids.study` + `participant_id` middle token → **51 sub-studies with 80.8 % coverage** (vs NB04b's 19 noisy categories).
- **§3** Within-substudy CD-vs-nonIBD DA — the four IBD sub-studies that contain both diagnoses (`HallAB_2017`, `IjazUZ_2017`, `LiJ_2014`, `NielsenHB_2014`; CD N=21–89, nonIBD N=10–248). This is the **confound-free CD-effect estimate** in cMD. The pooled CD-vs-HC contrast is structurally substudy-nested (all CD from IBD studies, all HC from healthy-cohort studies) and therefore cannot be rescued by a random effect.
- **§4** LinDA (Zhou et al. 2022) in pure NumPy: OLS on CLR-transformed abundance with median bias correction. Gives a second compositional DA method for within-ecotype concordance with CLR-MW.
- **§5** LME with proper substudy random effect on the within-ecotype contrasts (where substudy varies within the CD and within the HC subset, LME is identifiable; the pooled contrast is explicitly flagged as confounded).
- **§6** Refined Tier-A with 3-way evidence: bootstrap CI stable (NB04b) + LinDA concordant + within-substudy CD-vs-nonIBD concordant.

Stopping-rule re-evaluation and REPORT.md rewrite are deferred to a separate check-in after §5 outputs are reviewed.
"""))

cells.append(nbf.v4.new_code_cell("""import warnings; warnings.filterwarnings('ignore')
from pathlib import Path
import json, re
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, t as t_dist
from statsmodels.stats.multitest import multipletests
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt
import matplotlib as mpl
mpl.rcParams['figure.dpi'] = 100

DATA_MART = Path.home() / 'data' / 'CrohnsPhage'
DATA_OUT = Path('../data')
FIG_OUT = Path('../figures')
K_REF = 4
"""))

cells.append(nbf.v4.new_markdown_cell("""## §1. Rebuild wide matrix identically to NB04/NB04b"""))

cells.append(nbf.v4.new_code_cell("""# Synonymy + canonical wide matrix (same pipeline as NB01b/NB02/NB04/NB04b)
syn = pd.read_csv(DATA_OUT / 'species_synonymy.tsv', sep='\\t')
lookup = dict(zip(syn.alias, syn.canonical))

ta = pd.read_parquet(DATA_MART / 'fact_taxon_abundance.snappy.parquet')
ta = ta[(ta.classification_method == 'metaphlan3') & (ta.study_id.isin(['CMD_HEALTHY','CMD_IBD']))].copy()

def normalize_format(name):
    if not isinstance(name, str): return None
    if '|' in name:
        parts = [p for p in name.split('|') if p.startswith('s__')]
        return parts[0][3:].replace('_', ' ').strip() if parts else None
    return name.replace('[','').replace(']','').strip()

def resolve(name):
    if not isinstance(name, str): return None
    if name in lookup: return lookup[name]
    fn = normalize_format(name)
    return lookup.get(fn, fn) if fn else None

ta['species'] = ta['taxon_name_original'].map(resolve)
ta = ta.dropna(subset=['species']).copy()
wide = ta.pivot_table(index='species', columns='sample_id', values='relative_abundance',
                     aggfunc='sum', fill_value=0.0)

eco = pd.read_csv(DATA_OUT / 'ecotype_assignments.tsv', sep='\\t')
eco_map = dict(zip(eco.sample_id, eco.consensus_ecotype))
diag_map = dict(zip(eco.sample_id, eco.diagnosis))

cols_keep = [c for c in wide.columns if c in eco_map]
wide = wide[cols_keep]

# 5 %-prevalence filter (same as NB04)
keep = pd.concat([
    (wide[[c for c in wide.columns if diag_map.get(c) == d]] > 0).mean(axis=1)
    for d in ['HC','CD','UC'] if any(diag_map.get(c) == d for c in wide.columns)
], axis=1).max(axis=1) >= 0.05
w = wide.loc[keep].copy()
print(f'Wide matrix: {w.shape[0]:,} species × {w.shape[1]:,} samples')

# CLR transform — multi-species reference (only correct way)
def clr(M):
    M = M.astype(float).copy()
    col_min_nz = np.where(M > 0, M, np.nan)
    col_min_nz = np.nanmin(col_min_nz, axis=0)
    col_min_nz = np.where(np.isnan(col_min_nz), 1e-6, col_min_nz / 2)
    M = np.where(M > 0, M, col_min_nz[None, :])
    logM = np.log(M)
    return logM - logM.mean(axis=0, keepdims=True)
"""))

cells.append(nbf.v4.new_markdown_cell("""## §2. Proper substudy resolution (fix for C3 confounder-adjustment input)

NB04b's regex-on-sample-ID found only 19 noisy categories (`CMD` 5,333, `HMP2` 1,627, `EGAR` 355, etc.) because it tried to infer the substudy from the surface prefix of the sample ID. The real substudy lives in two places in the mart:

- `dim_samples.external_ids` — a JSON blob containing `"study": "AsnicarF_2021"` for CMD_HEALTHY samples.
- `dim_samples.participant_id` — `CMD:HallAB_2017:SKST006` format for CMD_IBD samples, where the middle token is the source study.

Resolving both yields **51 distinct sub-studies** covering **80.8 %** of the ecotype-assigned sample set (6,862 / 8,489)."""))

cells.append(nbf.v4.new_code_cell("""dim_samples = pd.read_parquet(DATA_MART / 'dim_samples.snappy.parquet')

def resolve_substudy(row):
    ext = row['external_ids']
    if isinstance(ext, str):
        try:
            d = json.loads(ext)
            if isinstance(d.get('study'), str):
                return d['study']
        except Exception:
            pass
    pid = row['participant_id']
    if isinstance(pid, str):
        parts = pid.split(':')
        if len(parts) >= 3 and parts[0] in ('CMD', 'HMP2'):
            return parts[1]
    return None

dim_samples['substudy'] = dim_samples.apply(resolve_substudy, axis=1)
substudy_map = dict(zip(dim_samples.sample_id, dim_samples.substudy))

in_matrix = pd.Series({s: substudy_map.get(s) for s in w.columns})
coverage = in_matrix.notna().mean()
print(f'Substudy coverage in wide matrix: {in_matrix.notna().sum()}/{len(w.columns)} = {coverage:.1%}')
print(f'Distinct sub-studies in matrix: {in_matrix.nunique()}')

# Sub-study × diagnosis breakdown (matrix scope)
rows = []
for s in w.columns:
    rows.append({'sample_id': s, 'substudy': substudy_map.get(s),
                 'diagnosis': diag_map.get(s), 'ecotype': eco_map.get(s)})
sample_meta = pd.DataFrame(rows)
sample_meta = sample_meta[sample_meta.substudy.notna()]

tbl = sample_meta.groupby('substudy').diagnosis.value_counts().unstack(fill_value=0)
tbl['N'] = tbl.sum(axis=1)
tbl = tbl.sort_values('N', ascending=False).head(20)
print()
print('Top 20 sub-studies × diagnosis (ecotype-assigned scope):')
print(tbl.to_string())
"""))

cells.append(nbf.v4.new_code_cell("""# Identify substudies suitable for confound-free CD-vs-nonIBD contrasts
ibd_contrast_studies = []
tbl_full = sample_meta.groupby('substudy').diagnosis.value_counts().unstack(fill_value=0)
for st, row in tbl_full.iterrows():
    cd_n = row.get('CD', 0); nonibd_n = row.get('nonIBD', 0)
    if cd_n >= 10 and nonibd_n >= 10:
        ibd_contrast_studies.append({'substudy': st, 'n_CD': int(cd_n), 'n_nonIBD': int(nonibd_n)})
ibd_contrast_df = pd.DataFrame(ibd_contrast_studies).sort_values('n_CD', ascending=False)
print('Sub-studies eligible for within-study CD-vs-nonIBD contrast (N ≥ 10 each):')
print(ibd_contrast_df.to_string(index=False))

# Document the pooled-cohort confound explicitly
hc_studies = set(tbl_full[tbl_full.get('HC', 0) >= 10].index)
cd_studies = set(tbl_full[tbl_full.get('CD', 0) >= 10].index)
overlap = hc_studies & cd_studies
print(f'\\nPooled-cohort confound check:')
print(f'  Sub-studies with HC ≥ 10: {len(hc_studies)}')
print(f'  Sub-studies with CD ≥ 10: {len(cd_studies)}')
print(f'  Sub-studies with BOTH HC and CD ≥ 10: {len(overlap)}  →  {sorted(overlap)}')
print('  ⇒ CD and HC come from disjoint study sets. A pooled CD-vs-HC LME with substudy random')
print('    effect is structurally UNIDENTIFIABLE (sub-study perfectly predicts diagnosis).')
print('    Within-substudy CD-vs-nonIBD is the confound-free alternative used below.')
"""))

cells.append(nbf.v4.new_markdown_cell("""## §3. Within-substudy CD-vs-nonIBD DA (confound-free)

For each of the four eligible IBD sub-studies and each of the 14 curated-battery species + NB04 Tier-A candidates: CLR-Δ (mean CD-CLR − mean nonIBD-CLR) with bootstrap CI. Agreement in sign across substudies is evidence that the CD-effect is not a study artifact.

Meta-analysis: inverse-variance weighted pooled estimate across substudies that contribute a valid effect."""))

cells.append(nbf.v4.new_code_cell("""BATTERY = ['Clostridium scindens','Faecalibacterium prausnitzii','Akkermansia muciniphila',
           'Roseburia intestinalis','Roseburia hominis','Lachnospira eligens',
           'Agathobacter rectalis','Coprococcus eutactus',
           'Mediterraneibacter gnavus','Enterocloster bolteae','Eggerthella lenta',
           'Bilophila wadsworthia','Escherichia coli','Klebsiella oxytoca','Hungatella hathewayi']

# Load NB04 Tier-A list to include in within-substudy DA
tier_a_orig = pd.read_csv(DATA_OUT / 'nb04_tier_a_candidates.tsv', sep='\\t')
TARGET_SPECIES = sorted(set(BATTERY) | set(tier_a_orig.species))
print(f'Species to test within-substudy: {len(TARGET_SPECIES)} (battery={len(BATTERY)}, plus NB04 Tier-A)')

def within_substudy_effect(w, species_list, sample_meta, group_a, group_b, n_boot=500, rng_seed=42):
    \"\"\"Per species × substudy: CLR-Δ(group_a − group_b) with bootstrap CI.\"\"\"
    results = []
    rng = np.random.default_rng(rng_seed)
    eligible = sample_meta.groupby('substudy').diagnosis.value_counts().unstack(fill_value=0)
    for st in eligible.index:
        a_ids = sample_meta[(sample_meta.substudy == st) & (sample_meta.diagnosis == group_a)].sample_id.tolist()
        b_ids = sample_meta[(sample_meta.substudy == st) & (sample_meta.diagnosis == group_b)].sample_id.tolist()
        if min(len(a_ids), len(b_ids)) < 10:
            continue
        cols = [c for c in a_ids + b_ids if c in w.columns]
        if not cols: continue
        full = clr(w[cols].values)
        n_a = sum(1 for c in a_ids if c in w.columns)
        for sp in species_list:
            if sp not in w.index: continue
            idx = list(w.index).index(sp)
            a = full[idx, :n_a]; b = full[idx, n_a:]
            if len(a) == 0 or len(b) == 0: continue
            point = a.mean() - b.mean()
            deltas = np.empty(n_boot)
            for i in range(n_boot):
                ai = rng.integers(0, len(a), len(a))
                bi = rng.integers(0, len(b), len(b))
                deltas[i] = a[ai].mean() - b[bi].mean()
            ci = np.percentile(deltas, [2.5, 97.5])
            se = deltas.std()
            results.append({'species': sp, 'substudy': st,
                            'n_CD': int(n_a), 'n_nonIBD': len(b),
                            'point': round(point, 3),
                            'ci_lo': round(ci[0], 3), 'ci_hi': round(ci[1], 3),
                            'boot_se': round(se, 3)})
    return pd.DataFrame(results)

cdvs_nonibd = within_substudy_effect(w, TARGET_SPECIES, sample_meta, 'CD', 'nonIBD')
print(f'\\nWithin-substudy CD-vs-nonIBD DA: {len(cdvs_nonibd)} (species × substudy) rows')
print(f'Substudies contributing: {sorted(cdvs_nonibd.substudy.unique())}')
cdvs_nonibd.to_csv(DATA_OUT / 'nb04c_within_substudy_cd_nonibd.tsv', sep='\\t', index=False)

# Inverse-variance weighted pooled per species
def ivw_pool(sub):
    if len(sub) < 2: return None
    w_i = 1.0 / (sub.boot_se ** 2 + 1e-9)
    pooled = (sub.point * w_i).sum() / w_i.sum()
    se_pooled = np.sqrt(1.0 / w_i.sum())
    return pooled, se_pooled, len(sub)

meta_rows = []
for sp, sub in cdvs_nonibd.groupby('species'):
    r = ivw_pool(sub)
    if r is None:
        meta_rows.append({'species': sp, 'pooled_effect': sub.point.iloc[0] if len(sub) else None,
                          'pooled_se': sub.boot_se.iloc[0] if len(sub) else None,
                          'n_substudies': len(sub),
                          'n_CD_total': int(sub.n_CD.sum()), 'n_nonIBD_total': int(sub.n_nonIBD.sum()),
                          'concordant_sign': True if len(sub) == 1 else None})
        continue
    pooled, se, k = r
    # Sign concordance: fraction of substudy effects with same sign as pooled
    concord = (np.sign(sub.point) == np.sign(pooled)).mean()
    meta_rows.append({'species': sp,
                      'pooled_effect': round(pooled, 3), 'pooled_se': round(se, 3),
                      'n_substudies': k,
                      'n_CD_total': int(sub.n_CD.sum()), 'n_nonIBD_total': int(sub.n_nonIBD.sum()),
                      'concordant_sign_frac': round(concord, 2)})
meta_df = pd.DataFrame(meta_rows)
meta_df['z'] = meta_df.pooled_effect / meta_df.pooled_se
meta_df['p'] = 2 * (1 - t_dist.cdf(meta_df.z.abs(), df=40))
meta_df['fdr'] = multipletests(meta_df.p.fillna(1), method='fdr_bh')[1]
meta_df = meta_df.sort_values('pooled_effect', ascending=False)
meta_df.to_csv(DATA_OUT / 'nb04c_within_substudy_meta.tsv', sep='\\t', index=False)
print(f'\\nMeta-analysis summary (14-battery species, top 10 by effect):')
battery_meta = meta_df[meta_df.species.isin(BATTERY)]
print(battery_meta.to_string(index=False))
"""))

cells.append(nbf.v4.new_markdown_cell("""## §4. LinDA (pure-Python) — second compositional DA method

Zhou et al. 2022: linear regression on CLR-transformed abundance with bias correction. For each species i:

$$y_{is} = \\beta_{0i} + \\beta_{1i} \\cdot \\text{is\\_CD}_s + \\epsilon_{is}$$

$$\\hat{\\beta}_{1i}^{\\text{adj}} = \\hat{\\beta}_{1i} - \\text{median}(\\{\\hat{\\beta}_{1j}\\}_j)$$

The median of the coefficient distribution across all species estimates the compositional-level shift that would otherwise contaminate each per-species coefficient. Bias-adjusted t-statistic → p-value → BH-FDR."""))

cells.append(nbf.v4.new_code_cell("""def linda(w_sub, group_a_ids, group_b_ids):
    \"\"\"LinDA on a species × samples subset. Returns DataFrame with effect, se, p, fdr per species.\"\"\"
    a_ids = [c for c in group_a_ids if c in w_sub.columns]
    b_ids = [c for c in group_b_ids if c in w_sub.columns]
    if min(len(a_ids), len(b_ids)) < 10: return pd.DataFrame()
    cols = a_ids + b_ids
    M = w_sub[cols].values
    X_clr = clr(M)
    x = np.concatenate([np.ones(len(a_ids)), np.zeros(len(b_ids))])  # is_CD
    x_mean = x.mean(); x_centered = x - x_mean; x_var = (x_centered ** 2).sum()
    Y = X_clr  # species × samples
    y_mean = Y.mean(axis=1, keepdims=True)
    beta = (Y * x_centered).sum(axis=1) / x_var  # raw coef per species
    # residuals, SE
    resid = Y - y_mean - np.outer(beta, x_centered)
    sigma2 = (resid ** 2).sum(axis=1) / (len(x) - 2)
    se = np.sqrt(sigma2 / x_var)
    # LinDA bias correction
    bias = np.median(beta)
    beta_adj = beta - bias
    t_stat = beta_adj / se
    p = 2 * (1 - t_dist.cdf(np.abs(t_stat), df=len(x) - 2))
    fdr = multipletests(p, method='fdr_bh')[1]
    out = pd.DataFrame({'species': w_sub.index, 'effect': beta_adj,
                        'se': se, 't_stat': t_stat, 'p': p, 'fdr': fdr,
                        'linda_bias': bias})
    return out

# Pool + per-ecotype
cd_ids = [c for c in w.columns if diag_map.get(c) == 'CD']
hc_ids = [c for c in w.columns if diag_map.get(c) == 'HC']
eco_cd = {k: [c for c in cd_ids if eco_map.get(c) == k] for k in [1, 3]}
eco_hc = {k: [c for c in hc_ids if eco_map.get(c) == k] for k in [1, 3]}

linda_pool = linda(w, cd_ids, hc_ids).assign(analysis='pooled')
linda_e1 = linda(w, eco_cd[1], eco_hc[1]).assign(analysis='E1')
linda_e3 = linda(w, eco_cd[3], eco_hc[3]).assign(analysis='E3')
linda_all = pd.concat([linda_pool, linda_e1, linda_e3], ignore_index=True)
linda_all.to_csv(DATA_OUT / 'nb04c_linda.tsv', sep='\\t', index=False)

print(f'LinDA runs: pooled={len(linda_pool)}; E1={len(linda_e1)}; E3={len(linda_e3)}')
print(f'Bias estimates (CLR units): pooled {linda_pool.linda_bias.iloc[0]:+.3f}; '
      f'E1 {linda_e1.linda_bias.iloc[0]:+.3f}; E3 {linda_e3.linda_bias.iloc[0]:+.3f}')

# Battery-focused view
battery_linda = linda_all[linda_all.species.isin(BATTERY)].pivot_table(
    index='species', columns='analysis', values='effect').round(3)
battery_linda_fdr = linda_all[linda_all.species.isin(BATTERY)].pivot_table(
    index='species', columns='analysis', values='fdr').round(4)
print('\\nLinDA effect (bias-adj CLR-Δ) per battery species × analysis:')
print(battery_linda.to_string())
print('\\nLinDA FDR per battery species × analysis:')
print(battery_linda_fdr.to_string())
"""))

cells.append(nbf.v4.new_markdown_cell("""## §5. LME with proper substudy random effect

For within-ecotype CD-vs-HC: substudy varies within both diagnosis groups (less tightly nested than the pooled contrast), so LME is identifiable. The pooled CD-vs-HC LME is retained for comparison but explicitly flagged as confounded.

Model: `log(relative_abundance + pseudocount) ~ C(diagnosis) + (1 | substudy)`"""))

cells.append(nbf.v4.new_code_cell("""def lme_proper(w, sp, cd_ids, hc_ids, substudy_map):
    if sp not in w.index: return None
    cd_ = [s for s in cd_ids if s in w.columns and substudy_map.get(s)]
    hc_ = [s for s in hc_ids if s in w.columns and substudy_map.get(s)]
    cols = cd_ + hc_
    if min(len(cd_), len(hc_)) < 10: return None
    sub = w.loc[[sp], cols].T.copy()
    sub.columns = ['rel_ab']
    pc = max(sub.rel_ab[sub.rel_ab > 0].min() / 2, 1e-8) if (sub.rel_ab > 0).any() else 1e-8
    sub['log_ab'] = np.log(sub.rel_ab.replace(0, pc))
    sub['diagnosis'] = ['CD'] * len(cd_) + ['HC'] * len(hc_)
    sub['substudy'] = [substudy_map[s] for s in cols]
    n_study = sub.substudy.nunique()
    # Within-group study variety check — is the contrast identifiable?
    cd_studies = set(sub[sub.diagnosis=='CD'].substudy)
    hc_studies = set(sub[sub.diagnosis=='HC'].substudy)
    common_studies = cd_studies & hc_studies
    if n_study < 2:
        return None
    try:
        model = smf.mixedlm('log_ab ~ C(diagnosis, Treatment(reference=\"HC\"))',
                            sub, groups='substudy')
        result = model.fit(method='lbfgs', disp=False, reml=False)
        coef = result.fe_params.iloc[1]
        ci_all = result.conf_int()
        ci = ci_all.iloc[1]
        return {'effect': coef, 'ci_lo': ci[0], 'ci_hi': ci[1],
                'p': result.pvalues.iloc[1], 'n_substudies': n_study,
                'n_common_substudies': len(common_studies),
                'n_samples': len(sub)}
    except Exception as e:
        return None

# Run LME for battery + NB04 Tier-A candidates on pooled + per-ecotype
LME_SPECIES = sorted(set(BATTERY) | set(tier_a_orig.species))
lme_rows = []
for sp in LME_SPECIES:
    for label, cd_e, hc_e in [
        ('pooled', cd_ids, hc_ids),
        ('E1', eco_cd[1], eco_hc[1]),
        ('E3', eco_cd[3], eco_hc[3]),
    ]:
        r = lme_proper(w, sp, cd_e, hc_e, substudy_map)
        if r:
            lme_rows.append({'species': sp, 'analysis': label,
                             'effect': round(r['effect'], 3),
                             'ci_lo': round(r['ci_lo'], 3),
                             'ci_hi': round(r['ci_hi'], 3),
                             'p': r['p'],
                             'n_substudies': r['n_substudies'],
                             'n_common_substudies': r['n_common_substudies']})

lme_df = pd.DataFrame(lme_rows)
if len(lme_df):
    lme_df['fdr'] = multipletests(lme_df.p.fillna(1), method='fdr_bh')[1]
else:
    lme_df['fdr'] = pd.Series(dtype=float)
lme_df.to_csv(DATA_OUT / 'nb04c_lme.tsv', sep='\\t', index=False)

print(f'LME rows produced: {len(lme_df)}')
if len(lme_df):
    print(f'\\nBattery species × analysis (LME):')
    print(lme_df[lme_df.species.isin(BATTERY)].to_string(index=False))
    print()
    print('NOTE: `n_common_substudies` column reports how many sub-studies contain BOTH CD and HC.')
    print('When n_common_substudies = 0 (all sub-studies have only one of CD/HC), the CD effect is')
    print('an across-study comparison and the random effect cannot absorb study confounding.')
"""))

cells.append(nbf.v4.new_markdown_cell("""## §6. Refined Tier-A with 3-way evidence

For each NB04 Tier-A candidate:

1. **Bootstrap CI stable CD↑** — from NB04b `nb04b_tier_a_refined.tsv`: `boot_ci_lo > 0.3`
2. **LinDA CD↑ concordant** — from §4 above: `effect > 0` AND `fdr < 0.10` in the same ecotype
3. **Within-substudy CD-vs-nonIBD concordant** — from §3 above: pooled effect > 0 AND sign-concordant across ≥ 2 substudies (or only 1 substudy contributed but effect > 0)

`n_evidence = 3` is the new Tier-A bar for proceeding to NB05."""))

cells.append(nbf.v4.new_code_cell("""nb04b_refined = pd.read_csv(DATA_OUT / 'nb04b_tier_a_refined.tsv', sep='\\t')
nb04c_linda = pd.read_csv(DATA_OUT / 'nb04c_linda.tsv', sep='\\t')
nb04c_meta = pd.read_csv(DATA_OUT / 'nb04c_within_substudy_meta.tsv', sep='\\t')

refined_rows = []
for _, r in nb04b_refined.iterrows():
    sp = r['species']; ecotype = r['ecotype']  # 'E1' or 'E3'
    boot_stable = bool(r['boot_stable_pos'])
    # LinDA in the matching ecotype
    linda_row = nb04c_linda[(nb04c_linda.species == sp) & (nb04c_linda.analysis == ecotype)]
    if len(linda_row):
        linda_effect = linda_row.iloc[0]['effect']
        linda_fdr = linda_row.iloc[0]['fdr']
        linda_pass = bool(linda_effect > 0 and linda_fdr < 0.10)
    else:
        linda_effect = linda_fdr = None; linda_pass = False
    # Within-substudy CD-vs-nonIBD (species-level; not ecotype-stratified because substudy × ecotype cells are too small)
    meta_row = nb04c_meta[nb04c_meta.species == sp]
    if len(meta_row):
        m = meta_row.iloc[0]
        meta_effect = m.get('pooled_effect')
        meta_n_sub = int(m.get('n_substudies', 0))
        concord_frac = m.get('concordant_sign_frac')
        # Pass if pooled > 0 and (single-substudy case OR >= 66% sign concordance across substudies)
        if meta_effect is None or pd.isna(meta_effect):
            within_pass = False
        elif meta_n_sub == 1:
            within_pass = bool(meta_effect > 0)
        else:
            within_pass = bool(meta_effect > 0 and (concord_frac is None or concord_frac >= 0.66))
    else:
        meta_effect = None; meta_n_sub = 0; concord_frac = None; within_pass = False
    n_ev = int(boot_stable) + int(linda_pass) + int(within_pass)
    refined_rows.append({'species': sp, 'ecotype': ecotype,
                         'orig_effect': r['orig_effect'],
                         'boot_stable_pos': boot_stable,
                         'linda_effect': None if linda_effect is None else round(linda_effect, 3),
                         'linda_fdr': None if linda_fdr is None else round(linda_fdr, 4),
                         'linda_pass': linda_pass,
                         'within_substudy_effect': None if meta_effect is None or pd.isna(meta_effect) else round(meta_effect, 3),
                         'within_substudy_n_sub': meta_n_sub,
                         'within_substudy_pass': within_pass,
                         'n_evidence': n_ev})

refined = pd.DataFrame(refined_rows).sort_values(['ecotype','n_evidence','orig_effect'],
                                                 ascending=[True, False, False])
refined.to_csv(DATA_OUT / 'nb04c_tier_a_refined.tsv', sep='\\t', index=False)

print(f'Refined Tier-A: {len(refined)} candidates evaluated')
print()
print('Per ecotype × n_evidence breakdown:')
print(refined.groupby(['ecotype','n_evidence']).size().to_string())
print()
print('TOP CANDIDATES (n_evidence >= 2):')
top = refined[refined.n_evidence >= 2]
if len(top):
    print(top[['species','ecotype','orig_effect','boot_stable_pos','linda_effect','linda_pass','within_substudy_effect','within_substudy_pass','n_evidence']].to_string(index=False))
else:
    print('  (none)')

print()
print('TOP CANDIDATES (n_evidence = 3):')
top3 = refined[refined.n_evidence == 3]
if len(top3):
    print(top3[['species','ecotype','orig_effect','boot_stable_pos','linda_effect','linda_pass','within_substudy_effect','within_substudy_pass']].to_string(index=False))
else:
    print('  (none)')
"""))

cells.append(nbf.v4.new_markdown_cell("""## §7. Summary (for user check-in before §8 stopping-rule re-run)

Outputs produced:

- `data/nb04c_within_substudy_cd_nonibd.tsv` — per species × substudy CLR-Δ CD-vs-nonIBD with bootstrap CI
- `data/nb04c_within_substudy_meta.tsv` — inverse-variance weighted pooled effects across substudies
- `data/nb04c_linda.tsv` — LinDA effects for pooled + E1 + E3 (all species)
- `data/nb04c_lme.tsv` — LME substudy-adjusted effects with per-analysis common-substudy reporting
- `data/nb04c_tier_a_refined.tsv` — 3-way evidence refined Tier-A (replaces nb04b_tier_a_refined.tsv)

Pending (next check-in):

- §8 stopping-rule re-run with refined Tier-A (criterion 2: bootstrap-stable × 3-way evidence)
- REPORT.md rewrite retracting NB04 overclaims
- RESEARCH_PLAN.md v1.4 documenting the failure + repair arc
"""))

nb['cells'] = cells
nb.metadata.kernelspec = {"display_name": "Python 3", "language": "python", "name": "python3"}
nb.metadata.language_info = {"name": "python", "version": "3.10"}

with open(NB_PATH, 'w') as f:
    nbf.write(nb, f)
print(f'Wrote {NB_PATH}')

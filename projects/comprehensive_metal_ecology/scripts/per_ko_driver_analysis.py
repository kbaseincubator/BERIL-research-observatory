#!/usr/bin/env python3
"""
Per-KO driver analysis: which resistance KOs drive the signal for which metals?
For each of 22 significant environmental niche breadth responses (tier1 PGLS):
  PGLS: env_response ~ ko_freq_z + genome_mb_z (Pagel λ, GTDB r214)
  predictor: per-KO frequency (n_genomes_with_ko / n_genomes), z-scored

Outputs:
  results/ko_drivers_results.csv     — all 198 PGLS models
  results/ko_drivers_heatmap.pdf     — Figure A: β heatmap (22 × 9)
  results/ko_drivers_metal_bars.pdf  — Figure B: per-metal t-stat bars (Cr/Cd/Ni/Cu/Hg)
  results/ko_drivers_metal_match.pdf — Figure C: metal-match scatter
  results/ko_drivers_report.md

Note: 9 of 15 TIER1_KOs are in the pangenome database (kbase.ke_pangenome via nb25).
Missing: K07798 (cusB), K08365 (merR), K15725 (czcC), K15727 (czcB), K16264 (czcD), K19591 (cueR).
"""
import os
os.environ['OMP_NUM_THREADS'] = '1'
import subprocess
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.colorbar import ColorbarBase
import warnings
warnings.filterwarnings('ignore')

BASE    = "/home/hmacgregor/BERIL-research-observatory/projects/comprehensive_metal_ecology"
DATA    = f"{BASE}/data"
RES     = f"{BASE}/results"
TREE    = "/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/data/gtdb_bac_genus_pruned.tree"
RSCRIPT = "/home/hmacgregor/r_env/bin/Rscript"

# ── KO definitions ─────────────────────────────────────────────────────────────
TIER1_KOS = [
    'K03325', 'K03446', 'K07665', 'K07785', 'K07787', 'K07798',
    'K08365', 'K15725', 'K15726', 'K15727', 'K16264', 'K17686',
    'K19591', 'K19594', 'K19595'
]
AVAILABLE_KOS = [  # in nb25_ko_presence_matrix
    'K03325', 'K03446', 'K07665', 'K07785', 'K07787',
    'K15726', 'K17686', 'K19594', 'K19595'
]
KO_META = {
    'K03325': {'gene': 'ACR3',  'metals': ['As', 'Tl']},
    'K03446': {'gene': 'emrB',  'metals': ['Cu', 'Tl']},
    'K07665': {'gene': 'cusR',  'metals': ['Cu', 'Ni']},
    'K07785': {'gene': 'nrsD',  'metals': ['Ni']},
    'K07787': {'gene': 'cusA',  'metals': ['Cu', 'Ag']},
    'K07798': {'gene': 'cusB',  'metals': ['Cu', 'Ag', 'Zn']},
    'K08365': {'gene': 'merR',  'metals': ['Hg', 'Cu', 'Zn']},
    'K15725': {'gene': 'czcC',  'metals': ['Ni', 'Zn', 'Co', 'Cd']},
    'K15726': {'gene': 'czcA',  'metals': ['Co', 'Ni', 'Zn', 'Cd']},
    'K15727': {'gene': 'czcB',  'metals': ['Co', 'Ni', 'Zn', 'Cd']},
    'K16264': {'gene': 'czcD',  'metals': ['Cd', 'Co', 'Zn', 'Tl']},
    'K17686': {'gene': 'copA',  'metals': ['Cu']},
    'K19591': {'gene': 'cueR',  'metals': ['Cu', 'Co', 'Ni', 'Zn']},
    'K19594': {'gene': 'gesB',  'metals': ['Cu', 'Au']},
    'K19595': {'gene': 'gesA',  'metals': ['Cu', 'Au']},
}

# 22 significant responses and readable labels
SIG22 = [
    'pH_sd', 'temp_sd', 'georoc_Ni_sd', 'georoc_Co_sd', 'georoc_Cr_sd',
    'georoc_Pb_sd', 'georoc_Cd_sd', 'georoc_Hg_sd', 'PF1_As_sd', 'PF1_Cd_sd',
    'PF1_Hg_sd', 'Ni_ICP_MS_mg_kg_0_5_sd', 'Zn_ICP_MS_mg_kg_0_9_sd',
    'As_ICP_MS_mg_kg_0_4_sd', 'Cr_ICP_MS_mg_kg_0_5_sd', 'Hg_AR_mg_kg_0_01_sd',
    'Cu_MMI_ME_mg_kg_0_01_sd', 'Ni_MMI_ME_mg_kg_0_005_sd',
    'Zn_MMI_ME_mg_kg_0_02_sd', 'As_MMI_ME_mg_kg_0_01_sd',
    'Cr_MMI_ME_mg_kg_0_001_sd', 'Hg_MMI_ME_mg_kg_0_001_sd',
]
RESP_LABEL = {
    'pH_sd': 'pH (GeoROC)', 'temp_sd': 'Temperature', 'georoc_Ni_sd': 'Ni (GeoROC)',
    'georoc_Co_sd': 'Co (GeoROC)', 'georoc_Cr_sd': 'Cr (GeoROC)',
    'georoc_Pb_sd': 'Pb (GeoROC)', 'georoc_Cd_sd': 'Cd (GeoROC)',
    'georoc_Hg_sd': 'Hg (GeoROC)', 'PF1_As_sd': 'As (CSU)',
    'PF1_Cd_sd': 'Cd (CSU)', 'PF1_Hg_sd': 'Hg (CSU)',
    'Ni_ICP_MS_mg_kg_0_5_sd': 'Ni (NGSA-ICP)', 'Zn_ICP_MS_mg_kg_0_9_sd': 'Zn (NGSA-ICP)',
    'As_ICP_MS_mg_kg_0_4_sd': 'As (NGSA-ICP)', 'Cr_ICP_MS_mg_kg_0_5_sd': 'Cr (NGSA-ICP)',
    'Hg_AR_mg_kg_0_01_sd': 'Hg (NGSA-AR)', 'Cu_MMI_ME_mg_kg_0_01_sd': 'Cu (NGSA-MMI)',
    'Ni_MMI_ME_mg_kg_0_005_sd': 'Ni (NGSA-MMI)', 'Zn_MMI_ME_mg_kg_0_02_sd': 'Zn (NGSA-MMI)',
    'As_MMI_ME_mg_kg_0_01_sd': 'As (NGSA-MMI)', 'Cr_MMI_ME_mg_kg_0_001_sd': 'Cr (NGSA-MMI)',
    'Hg_MMI_ME_mg_kg_0_001_sd': 'Hg (NGSA-MMI)',
}
# Which metals are in each response (for metal-match)
RESP_METAL = {
    'georoc_Ni_sd': 'Ni', 'georoc_Co_sd': 'Co', 'georoc_Cr_sd': 'Cr',
    'georoc_Pb_sd': 'Pb', 'georoc_Cd_sd': 'Cd', 'georoc_Hg_sd': 'Hg',
    'PF1_As_sd': 'As', 'PF1_Cd_sd': 'Cd', 'PF1_Hg_sd': 'Hg',
    'Ni_ICP_MS_mg_kg_0_5_sd': 'Ni', 'Zn_ICP_MS_mg_kg_0_9_sd': 'Zn',
    'As_ICP_MS_mg_kg_0_4_sd': 'As', 'Cr_ICP_MS_mg_kg_0_5_sd': 'Cr',
    'Hg_AR_mg_kg_0_01_sd': 'Hg', 'Cu_MMI_ME_mg_kg_0_01_sd': 'Cu',
    'Ni_MMI_ME_mg_kg_0_005_sd': 'Ni', 'Zn_MMI_ME_mg_kg_0_02_sd': 'Zn',
    'As_MMI_ME_mg_kg_0_01_sd': 'As', 'Cr_MMI_ME_mg_kg_0_001_sd': 'Cr',
    'Hg_MMI_ME_mg_kg_0_001_sd': 'Hg',
}

print("=" * 60)
print("Per-KO driver analysis")
print(f"  {len(AVAILABLE_KOS)}/15 TIER1 KOs available in pangenome db")
print(f"  {len(SIG22)} significant env responses")
print(f"  {len(AVAILABLE_KOS) * len(SIG22)} PGLS models")
print("=" * 60)

# ── Step 1: Build per-KO frequency matrix ─────────────────────────────────────
print("\nStep 1: Building per-KO frequency matrix...")
nb25 = pd.read_parquet(f"{DATA}/nb25_ko_presence_matrix.parquet")
# Strip GTDB g__ prefix (nb25 uses 'g__rhodococcus', PGLS uses 'rhodococcus')
nb25['genus_lower'] = nb25['genus_lower'].str.replace('^g__', '', regex=True)
nb25_t1 = nb25[nb25.ko.isin(AVAILABLE_KOS)].copy()

# Get n_genomes per genus from primary data
genus_meta = pd.read_csv(f"{DATA}/01_genus_ko_density_spark.csv")[['genus_lower','n_genomes']]
nb25_t1 = nb25_t1.merge(genus_meta, on='genus_lower', how='inner')
nb25_t1['ko_freq'] = nb25_t1['n_genomes_with_ko'] / nb25_t1['n_genomes']
nb25_t1['ko_freq'] = nb25_t1['ko_freq'].clip(0, 1)

# Pivot to wide
ko_wide = nb25_t1.pivot_table(
    index='genus_lower', columns='ko', values='ko_freq', fill_value=0)
ko_wide.columns = [f"ko_freq_{c}" for c in ko_wide.columns]
ko_wide = ko_wide.reset_index()
print(f"  KO freq matrix: {ko_wide.shape}")

# Z-score each KO
for col in ko_wide.columns[1:]:
    mn, sd = ko_wide[col].mean(), ko_wide[col].std()
    ko_wide[col + '_z'] = (ko_wide[col] - mn) / (sd + 1e-10)
z_cols = [c for c in ko_wide.columns if c.endswith('_z')]
print(f"  Z-scored cols: {z_cols}")

# ── Step 2: Merge with env niche breadth + PGLS predictors ────────────────────
print("\nStep 2: Merging with env niche breadth data...")
pgls_base = pd.read_csv(f"{DATA}/01_pgls_input_bacteria.csv")[
    ['genus_lower','genome_mb_z']].copy()

env_global = pd.read_csv(f"{DATA}/env_niche_global_spark.csv")
env_csu    = pd.read_csv(f"{DATA}/env_niche_csu_spark.csv")
env_ngsa   = pd.read_csv(f"{DATA}/env_niche_ngsa_spark.csv")

global_cols = [c for c in SIG22 if c in env_global.columns]
csu_cols    = [c for c in SIG22 if c in env_csu.columns]
ngsa_cols   = [c for c in SIG22 if c in env_ngsa.columns]

merged = pgls_base.merge(ko_wide, on='genus_lower', how='inner')
merged = merged.merge(env_global[['genus_lower'] + global_cols], on='genus_lower', how='left')
merged = merged.merge(env_csu[['genus_lower'] + csu_cols], on='genus_lower', how='left')
merged = merged.merge(env_ngsa[['genus_lower'] + ngsa_cols], on='genus_lower', how='left')
print(f"  Merged: {len(merged)} genera, {len(merged.columns)} columns")

merged_csv = f'/tmp/ko_driver_pgls_input.csv'
merged.to_csv(merged_csv, index=False)

# ── Step 3: PGLS in R (all 198 models) ────────────────────────────────────────
print("\nStep 3: Running PGLS in R (all models)...")
r_pgls = f"""
suppressPackageStartupMessages({{library(ape); library(nlme)}})
df_full <- read.csv("{merged_csv}", stringsAsFactors=FALSE)
tree_full <- read.tree("{TREE}")

responses <- c({','.join(f'"{r}"' for r in SIG22)})
ko_cols   <- c({','.join(f'"ko_freq_{k}_z"' for k in AVAILABLE_KOS)})
ko_names  <- c({','.join(f'"{k}"' for k in AVAILABLE_KOS)})

df_full$genus_tree <- df_full$genus_lower
shared <- intersect(df_full$genus_tree, tree_full$tip.label)
tree_p <- drop.tip(tree_full, setdiff(tree_full$tip.label, shared))
df_full <- df_full[df_full$genus_tree %in% shared, ]
df_full <- df_full[match(tree_p$tip.label, df_full$genus_tree), ]
rownames(df_full) <- df_full$genus_tree
cat(sprintf("n=%d genera in tree\\n", nrow(df_full)))

all_rows <- list()
for (resp in responses) {{
  df_r <- df_full[!is.na(df_full[[resp]]) & is.finite(df_full[[resp]]), ]
  if (nrow(df_r) < 30) {{ cat(sprintf("SKIP %s n=%d\\n", resp, nrow(df_r))); next }}
  tp_r <- drop.tip(tree_p, setdiff(tree_p$tip.label, df_r$genus_tree))
  df_r <- df_r[match(tp_r$tip.label, df_r$genus_tree), ]
  cat(sprintf("\\n%s (n=%d)\\n", resp, nrow(df_r)))
  for (ki in seq_along(ko_cols)) {{
    ko_col <- ko_cols[ki]
    ko_name <- ko_names[ki]
    if (!ko_col %in% names(df_r)) next
    df_k <- df_r[!is.na(df_r[[ko_col]]), ]
    if (nrow(df_k) < 30) next
    tp_k <- drop.tip(tp_r, setdiff(tp_r$tip.label, df_k$genus_tree))
    df_k <- df_k[match(tp_k$tip.label, df_k$genus_tree), ]
    fml <- as.formula(sprintf("%s ~ %s + genome_mb_z", resp, ko_col))
    tryCatch({{
      mod <- gls(fml, data=df_k,
                 correlation=corPagel(value=1, phy=tp_k, fixed=FALSE, form=~genus_tree),
                 method="ML", na.action=na.omit)
      co  <- summary(mod)$tTable
      lam <- as.numeric(mod$modelStruct$corStruct)
      n_fit <- length(mod$residuals)
      pn <- ko_col
      row <- data.frame(
        response=resp, ko=ko_name, gene=NA, predictor=pn,
        n=n_fit, lambda=lam,
        beta=co[pn,1], SE=co[pn,2], t=co[pn,3], p=co[pn,4],
        stringsAsFactors=FALSE)
      all_rows[[length(all_rows)+1]] <- row
      cat(sprintf("  %s: b=%.3f t=%.2f p=%.4f\\n", ko_name, co[pn,1], co[pn,3], co[pn,4]))
    }}, error=function(e) {{
      cat(sprintf("  ERROR %s/%s: %s\\n", ko_name, resp, conditionMessage(e)))
    }})
  }}
}}
out <- do.call(rbind, all_rows)
write.csv(out, "{RES}/ko_drivers_results.csv", row.names=FALSE)
cat(sprintf("\\nSaved %d models\\n", nrow(out)))
"""
r_file = '/tmp/ko_driver_pgls.R'
with open(r_file, 'w') as f:
    f.write(r_pgls)

res = subprocess.run([RSCRIPT, r_file], capture_output=True, text=True, timeout=7200)
print(res.stdout[-3000:] if len(res.stdout) > 3000 else res.stdout)
if res.returncode != 0:
    print(f"R error: {res.stderr[-600:]}")

# ── Step 4: Load results and add metadata ─────────────────────────────────────
print("\nStep 4: Processing results...")
try:
    results = pd.read_csv(f"{RES}/ko_drivers_results.csv")
    print(f"  Loaded {len(results)} models")
except Exception as e:
    print(f"  ERROR loading results: {e}")
    raise

# Add gene names, primary metals
results['gene'] = results.ko.map(lambda k: KO_META[k]['gene'])
results['ko_metals'] = results.ko.map(lambda k: ','.join(KO_META[k]['metals']))
results['resp_metal'] = results.response.map(RESP_METAL).fillna('')
results['metal_match'] = results.apply(
    lambda r: any(m in KO_META[r.ko]['metals'] for m in [r.resp_metal] if m), axis=1)

# FDR correction within each response
from statsmodels.stats.multitest import multipletests
rows = []
for resp, grp in results.groupby('response'):
    _, fdr, _, _ = multipletests(grp.p, method='fdr_bh')
    grp = grp.copy()
    grp['fdr_q'] = fdr
    rows.append(grp)
results = pd.concat(rows, ignore_index=True)
results.to_csv(f"{RES}/ko_drivers_results.csv", index=False)
print(f"  FDR corrected (within response)")
n_sig = (results.p < 0.05).sum()
n_fdr = (results.fdr_q < 0.1).sum()
print(f"  p<0.05: {n_sig}/{len(results)}, FDR q<0.1: {n_fdr}/{len(results)}")

# ── Step 5: Figures ────────────────────────────────────────────────────────────
print("\nStep 5: Generating figures...")
KO_LABELS = [f"{KO_META[k]['gene']}\n({k})" for k in AVAILABLE_KOS]
RESP_LABELS = [RESP_LABEL[r] for r in SIG22]

# Pivot t-statistic to matrix
t_mat = results.pivot_table(index='response', columns='ko', values='t', aggfunc='first')
t_mat = t_mat.reindex(index=SIG22, columns=AVAILABLE_KOS)
b_mat = results.pivot_table(index='response', columns='ko', values='beta', aggfunc='first')
b_mat = b_mat.reindex(index=SIG22, columns=AVAILABLE_KOS)
p_mat = results.pivot_table(index='response', columns='ko', values='p', aggfunc='first')
p_mat = p_mat.reindex(index=SIG22, columns=AVAILABLE_KOS)

# ── Figure A: β heatmap ────────────────────────────────────────────────────────
fig_a, ax = plt.subplots(figsize=(11, 9))
vmax = max(abs(b_mat.values[~np.isnan(b_mat.values)].max()),
           abs(b_mat.values[~np.isnan(b_mat.values)].min()))
vmax = min(vmax, 3.0)   # cap at 3 for readability
cmap = plt.cm.RdBu_r
im = ax.imshow(b_mat.values, aspect='auto', cmap=cmap,
               vmin=-vmax, vmax=vmax, interpolation='none')
ax.set_xticks(range(len(AVAILABLE_KOS)))
ax.set_xticklabels([KO_META[k]['gene'] for k in AVAILABLE_KOS], rotation=45, ha='right', fontsize=9)
ax.set_yticks(range(len(SIG22)))
ax.set_yticklabels(RESP_LABELS, fontsize=8)
# Mark significance
for i, resp in enumerate(SIG22):
    for j, ko in enumerate(AVAILABLE_KOS):
        p_val = p_mat.iloc[i, j]
        if pd.isna(p_val): continue
        marker = '***' if p_val < 0.001 else '**' if p_val < 0.01 else '*' if p_val < 0.05 else ''
        if marker:
            ax.text(j, i, marker, ha='center', va='center', fontsize=7, color='white',
                    fontweight='bold')
plt.colorbar(im, ax=ax, label='β (PGLS coefficient)', shrink=0.7)
ax.set_title("Per-KO PGLS: environmental niche breadth ~ KO frequency + genome size",
             fontsize=11, pad=10)
ax.set_xlabel("Resistance KO (gene name)", fontsize=10)
ax.set_ylabel("Environmental response (SD niche breadth)", fontsize=10)
ax.spines[['top','right','left','bottom']].set_visible(False)
fig_a.tight_layout()
fig_a.savefig(f"{RES}/ko_drivers_heatmap.pdf", dpi=150, bbox_inches='tight')
plt.close(fig_a)
print("  Saved ko_drivers_heatmap.pdf")

# ── Figure B: Per-metal t-stat bars (Cr, Cd, Ni, Cu, Hg) ─────────────────────
FOCUS_METALS = ['Cr', 'Cd', 'Ni', 'Cu', 'Hg']
metal_sub = results[results.resp_metal.isin(FOCUS_METALS)].copy()

if not metal_sub.empty:
    fig_b, axes = plt.subplots(1, len(FOCUS_METALS), figsize=(14, 5), sharey=False)
    colors_pos = '#2a78d6'
    colors_neg = '#e34948'
    for ax, metal in zip(axes, FOCUS_METALS):
        sub = metal_sub[metal_sub.resp_metal == metal].copy()
        # Average t-stats across responses with this metal
        mean_t = sub.groupby('ko')['t'].mean().reindex(AVAILABLE_KOS)
        genes = [KO_META[k]['gene'] for k in AVAILABLE_KOS]
        colors = [colors_pos if v >= 0 else colors_neg
                  for v in mean_t.values]
        bars = ax.barh(range(len(AVAILABLE_KOS)), mean_t.values,
                       color=colors, alpha=0.85, height=0.7)
        # Highlight KOs that target this metal
        for j, ko in enumerate(AVAILABLE_KOS):
            if metal in KO_META[ko]['metals']:
                ax.barh(j, mean_t.values[j], color=colors[j], alpha=1.0,
                        height=0.7, linewidth=2,
                        edgecolor='black')
        ax.axvline(0, color='#898781', lw=1)
        ax.axvline(1.96, color='#898781', lw=0.7, ls='--')
        ax.axvline(-1.96, color='#898781', lw=0.7, ls='--')
        ax.set_yticks(range(len(AVAILABLE_KOS)))
        ax.set_yticklabels(genes, fontsize=8)
        ax.set_title(f'{metal}', fontsize=11)
        ax.set_xlabel('Mean t-stat', fontsize=8)
        ax.spines[['top','right']].set_visible(False)
    fig_b.suptitle("Mean PGLS t-statistics by metal (outlined bar = KO targets that metal)",
                   fontsize=10)
    fig_b.tight_layout()
    fig_b.savefig(f"{RES}/ko_drivers_metal_bars.pdf", dpi=150, bbox_inches='tight')
    plt.close(fig_b)
    print("  Saved ko_drivers_metal_bars.pdf")
else:
    print("  Skipping Figure B — no metal-matched responses")

# ── Figure C: Metal-match scatter ─────────────────────────────────────────────
metal_resp_sub = results[results.resp_metal != ''].copy()
if not metal_resp_sub.empty:
    fig_c, ax = plt.subplots(figsize=(7, 5))
    match_t   = metal_resp_sub[metal_resp_sub.metal_match == True].t
    nomatch_t = metal_resp_sub[metal_resp_sub.metal_match == False].t

    ax.hist(nomatch_t.dropna(), bins=30, alpha=0.5, color='#898781',
            label=f'KO–metal mismatch (n={len(nomatch_t.dropna())})', density=True)
    ax.hist(match_t.dropna(), bins=30, alpha=0.7, color='#2a78d6',
            label=f'KO–metal match (n={len(match_t.dropna())})', density=True)
    ax.axvline(1.96, color='#e34948', lw=1, ls='--', label='|t|=1.96')
    ax.axvline(-1.96, color='#e34948', lw=1, ls='--')
    ax.set_xlabel('t-statistic (PGLS)', fontsize=11)
    ax.set_ylabel('Density', fontsize=11)
    ax.set_title('KO–metal specificity: matched vs mismatched responses', fontsize=11)
    ax.legend(fontsize=9)
    ax.spines[['top','right']].set_visible(False)
    # Mann-Whitney U test
    from scipy.stats import mannwhitneyu
    stat, pval = mannwhitneyu(match_t.dropna(), nomatch_t.dropna(), alternative='greater')
    ax.text(0.98, 0.95, f'Mann–Whitney U: p={pval:.3f}',
            transform=ax.transAxes, ha='right', va='top', fontsize=9)
    fig_c.tight_layout()
    fig_c.savefig(f"{RES}/ko_drivers_metal_match.pdf", dpi=150, bbox_inches='tight')
    plt.close(fig_c)
    print("  Saved ko_drivers_metal_match.pdf")
else:
    print("  Skipping Figure C — no metal-matched data")

# ── Step 6: Markdown report ────────────────────────────────────────────────────
print("\nStep 6: Writing report...")

def fmt_p(p):
    if p < 0.001: return f"{p:.2e}***"
    elif p < 0.01: return f"{p:.3f}**"
    elif p < 0.05: return f"{p:.3f}*"
    return f"{p:.3f}"

top5 = results[results.p < 0.05].sort_values('t', ascending=False).head(10)

lines = [
    "# Per-KO Driver Analysis Report",
    "",
    "*Generated by `scripts/per_ko_driver_analysis.py`*",
    "",
    "---",
    "",
    "## Methods",
    "",
    f"For each of {len(SIG22)} environmental niche breadth responses significantly predicted by",
    "TIER1 KO density (tier split PGLS, FDR < 5%, β > 0), we ran PGLS for each individual",
    "resistance KO:",
    "",
    "```",
    "env_response_sd ~ ko_freq_z + genome_mb_z",
    "```",
    "",
    f"**Predictor:** KO frequency = n_genomes_with_KO / n_genomes per genus (z-scored).",
    "**Tree:** GTDB r214 genus-level tree (2,283 tips). **λ:** estimated (Pagel 1999).",
    f"**Total models:** {len(AVAILABLE_KOS)} KOs × {len(SIG22)} responses = {len(AVAILABLE_KOS)*len(SIG22)}",
    "",
    f"**Note:** 9 of 15 TIER1 KOs are present in the pangenome database (kbase.ke_pangenome).",
    "Missing KOs (insufficient pangenome coverage): K07798 (cusB), K08365 (merR),",
    "K15725 (czcC), K15727 (czcB), K16264 (czcD), K19591 (cueR).",
    "",
    "---",
    "",
    "## Results",
    "",
    f"- Total models run: {len(results)}/{len(AVAILABLE_KOS)*len(SIG22)}",
    f"- Significant (p < 0.05): {n_sig} ({n_sig*100/max(len(results),1):.1f}%)",
    f"- Significant (FDR q < 0.1): {n_fdr}",
    "",
    "### Top associations (p < 0.05, by t-statistic)",
    "",
    "| Response | KO | Gene | β | SE | t | p | Metal match? |",
    "|----------|-----|------|---|----|----|---|---|",
]
for _, row in top5.iterrows():
    match_str = "✓" if row.metal_match else ""
    lines.append(
        f"| {RESP_LABEL.get(row.response, row.response)} | {row.ko} | {row.gene} | "
        f"{row.beta:.4f} | {row.SE:.4f} | {row.t:.3f} | {fmt_p(row.p)} | {match_str} |")

# Summary by KO
ko_summary = results.groupby('ko').agg(
    n_sig_05=('p', lambda x: (x < 0.05).sum()),
    mean_t=('t', 'mean'),
    max_t=('t', 'max'),
).reset_index()
ko_summary['gene'] = ko_summary.ko.map(lambda k: KO_META[k]['gene'])
ko_summary['metals'] = ko_summary.ko.map(lambda k: ','.join(KO_META[k]['metals']))
ko_summary = ko_summary.sort_values('n_sig_05', ascending=False)

lines += [
    "",
    "### Summary by KO",
    "",
    "| KO | Gene | Primary metals | Sig responses (p<0.05) | Mean t | Max t |",
    "|-----|------|---------------|------------------------|--------|-------|",
]
for _, row in ko_summary.iterrows():
    lines.append(f"| {row.ko} | {row.gene} | {row.metals} | {int(row.n_sig_05)} | "
                 f"{row.mean_t:.3f} | {row.max_t:.3f} |")

# Metal-match analysis
if not metal_resp_sub.empty:
    match_m = match_t.dropna().mean()
    no_m = nomatch_t.dropna().mean()
    lines += [
        "",
        "### Metal-match analysis",
        "",
        f"Mean t-stat for KO–metal matched pairs: {match_m:.3f}",
        f"Mean t-stat for KO–metal mismatched pairs: {no_m:.3f}",
        f"Mann–Whitney U test (matched > mismatched): p={pval:.3f}",
        "",
        "See `results/ko_drivers_metal_match.pdf` for distribution.",
    ]

lines += [
    "",
    "---",
    "",
    "## Figures",
    "",
    "- **Figure A** (`ko_drivers_heatmap.pdf`): β heatmap (22 responses × 9 KOs); asterisks indicate p<0.05.",
    "- **Figure B** (`ko_drivers_metal_bars.pdf`): mean t-statistic bars per metal (Cr/Cd/Ni/Cu/Hg); outlined = KO targets that metal.",
    "- **Figure C** (`ko_drivers_metal_match.pdf`): distribution of t-statistics for KO–metal matched vs mismatched pairs.",
]

with open(f"{RES}/ko_drivers_report.md", 'w') as f:
    f.write('\n'.join(lines))

print(f"\nReport: results/ko_drivers_report.md")
print("\n=== Per-KO driver analysis complete ===")

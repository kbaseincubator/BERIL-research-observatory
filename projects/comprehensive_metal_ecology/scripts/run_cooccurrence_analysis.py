#!/usr/bin/env python3
"""
Co-occurrence analysis: Parts A, B, C + PGLS — three strata
  1. all      — all MicrobeAtlas samples
  2. env      — environmental only (exclude plant/flower/leaf host-associated)
  3. soil     — soil only (soil, agricultural, farm, paddy, field, forest, shrub, peatland, desert)

Inputs:
  /tmp/cooc_genus_sample_long.parquet  — full binary matrix (genus × sample pairs)
  /tmp/cooc_sample_env.parquet         — sample_id → Env_Level_1
  /tmp/cooc_cophenetic.npy             — GTDB genus cophenetic distance matrix
  /tmp/cooc_cop_taxa.npy               — taxa labels for cophenetic matrix
  data/01_pgls_input_bacteria.csv      — genus predictor data for PGLS

Part A: Hypergeometric null (Veech 2013, fixed-fixed). FDR 5% BH.
Part B: Phi-coefficient network (weighted degree, betweenness k=500, clustering).
Part C: Partner MPD / SES (999 null draws, fully in Python/numpy).
PGLS:   7 co-occurrence metrics ~ ko_per_mb_z + genome_mb_z, Pagel λ (R).
"""
import os
os.environ['OMP_NUM_THREADS'] = '1'
import sys, time, subprocess, json
import numpy as np
import pandas as pd
import scipy.sparse as sp
from scipy.stats import hypergeom, t as t_dist
from statsmodels.stats.multitest import multipletests
import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE    = "/home/hmacgregor/BERIL-research-observatory/projects/comprehensive_metal_ecology"
DATA    = f"{BASE}/data"
RES     = f"{BASE}/results"
TREE    = "/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/data/gtdb_bac_genus_pruned.tree"
MATRIX  = "/tmp/cooc_genus_sample_long.parquet"
ENV_MAP = "/tmp/cooc_sample_env.parquet"
COPHEN  = "/tmp/cooc_cophenetic.npy"
COPHEN_TAXA = "/tmp/cooc_cop_taxa.npy"
RSCRIPT = "/home/hmacgregor/r_env/bin/Rscript"
FDR_ALPHA = 0.05
N_PERM    = 999

SOIL_ENVS = {'soil', 'agricultural', 'farm', 'paddy', 'field', 'forest', 'shrub', 'peatland', 'desert'}
HOST_ENVS = {'plant', 'flower', 'leaf'}   # excluded from environmental stratum

print("=" * 60)
print("Co-occurrence analysis — three strata")
print("=" * 60)

# ─────────────────────────────────────────────────────────────────
# Load data
# ─────────────────────────────────────────────────────────────────
print("\nLoading inputs...")
t0 = time.time()
sg_all = pd.read_parquet(MATRIX)
print(f"  Binary matrix: {len(sg_all):,} sample-genus pairs  ({time.time()-t0:.1f}s)")

env_map = None
if os.path.exists(ENV_MAP):
    env_map = pd.read_parquet(ENV_MAP)
    env_map['Env_Level_1'] = env_map['Env_Level_1'].str.lower().str.strip()
    print(f"  Env map: {len(env_map):,} samples, {env_map.Env_Level_1.nunique()} categories")
    print(f"    {dict(env_map.Env_Level_1.value_counts())}")
else:
    print("  WARNING: Env map not found — running 'all' stratum only")

pred = pd.read_csv(f"{DATA}/01_pgls_input_bacteria.csv")
pgls_genera_set = set(pred['genus_lower'].tolist())
print(f"  PGLS genera: {len(pgls_genera_set)}")

# Load cophenetic distance matrix (precomputed)
print(f"  Loading cophenetic matrix...")
t_c = time.time()
cop     = np.load(COPHEN)            # shape (n_tips, n_tips), float32
cop_taxa = np.load(COPHEN_TAXA, allow_pickle=True).tolist()  # list of genus names
cop_tax_idx = {g: i for i, g in enumerate(cop_taxa)}
n_tips = len(cop_taxa)
print(f"  Cophenetic: {n_tips} × {n_tips} ({cop.nbytes/1e6:.0f} MB)  ({time.time()-t_c:.1f}s)")

rng = np.random.default_rng(42)


# ─────────────────────────────────────────────────────────────────
# Part C helper — MPD + SES in Python/numpy
# ─────────────────────────────────────────────────────────────────
def compute_mpd_ses(partner_data_dict, all_genera_list, sig_pos_mat_local, g_idx_local):
    """
    For each focal genus in pgls_genera_set, compute:
      - MPD_obs: mean pairwise cophenetic distance among sig-positive-partner set
      - MPD_ses: standardized effect size vs N_PERM null draws
    Returns DataFrame with genus_lower, n_tree_partners, MPD_obs, MPD_ses
    """
    G_local = len(all_genera_list)
    focal = [g for g in all_genera_list if g in pgls_genera_set]
    rows = []
    for g in focal:
        g_i = g_idx_local[g]
        partners = [all_genera_list[k] for k in np.where(sig_pos_mat_local[g_i] == 1)[0]]
        focal_set = [g] + partners
        # Map to tree indices
        tree_idx = np.array([cop_tax_idx[x] for x in focal_set if x in cop_tax_idx])
        k = len(tree_idx)
        if k < 2:
            rows.append({'genus_lower': g, 'n_tree_partners': k - 1,
                          'MPD_obs': np.nan, 'MPD_ses': np.nan})
            continue
        # MPD_obs
        sub = cop[np.ix_(tree_idx, tree_idx)]
        triu = np.triu_indices(k, k=1)
        MPD_obs = float(sub[triu].mean())
        # Null distribution
        null_mpds = np.empty(N_PERM, dtype=np.float64)
        for pi in range(N_PERM):
            ri = rng.choice(n_tips, k, replace=False)
            d = cop[np.ix_(ri, ri)]
            null_mpds[pi] = d[triu].mean()
        sd_null = null_mpds.std()
        MPD_ses = (MPD_obs - null_mpds.mean()) / (sd_null + 1e-10)
        rows.append({'genus_lower': g, 'n_tree_partners': k - 1,
                      'MPD_obs': MPD_obs, 'MPD_ses': MPD_ses})
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────
# Per-stratum analysis function
# ─────────────────────────────────────────────────────────────────
def run_stratum(name, sg_pd, skip_network_metrics=False):
    """Run Parts A, B, C + PGLS for one sample-genus long table.
    skip_network_metrics: skip clustering, betweenness, and MPD/SES (for very dense strata).
    """
    print(f"\n{'='*60}")
    print(f"STRATUM: {name.upper()}  ({sg_pd.accession_id.nunique():,} samples, "
          f"{sg_pd.genus_lower.nunique():,} genera)")
    print('='*60)

    all_genera  = sorted(sg_pd['genus_lower'].unique())
    all_samples = sorted(sg_pd['accession_id'].unique())
    g_idx = {g: i for i, g in enumerate(all_genera)}
    s_idx = {s: i for i, s in enumerate(all_samples)}
    G, S = len(all_genera), len(all_samples)

    row_idx  = sg_pd['genus_lower'].map(g_idx).values
    col_idx  = sg_pd['accession_id'].map(s_idx).values
    M = sp.csr_matrix((np.ones(len(sg_pd), dtype=np.uint8), (row_idx, col_idx)),
                      shape=(G, S), dtype=np.uint8)
    row_sums = np.asarray(M.sum(axis=1)).ravel()
    print(f"  Matrix: {G} genera × {S} samples, prev median={int(np.median(row_sums))}")

    triu_i, triu_j = np.triu_indices(G, k=1)
    N_PAIRS = len(triu_i)

    # ── Part A: Hypergeometric ──────────────────────────────────
    print(f"  Part A: hypergeometric ({N_PAIRS:,} pairs)...")
    t1 = time.time()
    coo_counts = (M.astype(np.int32) @ M.T.astype(np.int32)).toarray()
    np.fill_diagonal(coo_counts, 0)
    K_obs = coo_counts[triu_i, triu_j]
    N_i   = row_sums[triu_i]
    N_j   = row_sums[triu_j]

    p_pos = np.zeros(N_PAIRS, dtype=np.float64)
    p_neg = np.zeros(N_PAIRS, dtype=np.float64)
    CHUNK = 1_000_000
    for start in range(0, N_PAIRS, CHUNK):
        end = min(start + CHUNK, N_PAIRS)
        p_pos[start:end] = hypergeom.sf(K_obs[start:end] - 1, S, N_i[start:end], N_j[start:end])
        p_neg[start:end] = hypergeom.cdf(K_obs[start:end],     S, N_i[start:end], N_j[start:end])

    _, p_pos_fdr, _, _ = multipletests(p_pos, method='fdr_bh')
    _, p_neg_fdr, _, _ = multipletests(p_neg, method='fdr_bh')
    sig_pos_mask = p_pos_fdr < FDR_ALPHA
    sig_neg_mask = p_neg_fdr < FDR_ALPHA

    sig_pos_mat = np.zeros((G, G), dtype=np.int8)
    sig_neg_mat = np.zeros((G, G), dtype=np.int8)
    sig_pos_mat[triu_i[sig_pos_mask], triu_j[sig_pos_mask]] = 1
    sig_pos_mat[triu_j[sig_pos_mask], triu_i[sig_pos_mask]] = 1
    sig_neg_mat[triu_i[sig_neg_mask], triu_j[sig_neg_mask]] = 1
    sig_neg_mat[triu_j[sig_neg_mask], triu_i[sig_neg_mask]] = 1

    sig_pos_per = sig_pos_mat.sum(axis=1)
    sig_neg_per = sig_neg_mat.sum(axis=1)
    print(f"    Sig+ pairs: {sig_pos_mask.sum():,} ({sig_pos_mask.sum()*100/N_PAIRS:.2f}%) | "
          f"Sig− pairs: {sig_neg_mask.sum():,} ({sig_neg_mask.sum()*100/N_PAIRS:.2f}%)  "
          f"({time.time()-t1:.0f}s)")

    part_a = pd.DataFrame({
        'genus_lower': all_genera,
        'prevalence': row_sums,
        'sig_pos_partners': sig_pos_per,
        'sig_neg_partners': sig_neg_per,
    })

    # ── Part B: Phi network ─────────────────────────────────────
    print(f"  Part B: phi network...")
    t2 = time.time()
    phi = (K_obs.astype(np.float64) * S - N_i.astype(np.float64) * N_j.astype(np.float64)) / np.sqrt(
        N_i.astype(np.float64) * (S - N_i.astype(np.float64)) *
        N_j.astype(np.float64) * (S - N_j.astype(np.float64)) + 1e-300)
    phi = np.clip(phi, -1, 1)
    t_stat = phi * np.sqrt(S - 2) / np.sqrt(1 - phi**2 + 1e-300)
    p_phi = 2 * t_dist.sf(np.abs(t_stat), df=S - 2)
    _, p_phi_fdr, _, _ = multipletests(p_phi, method='fdr_bh')
    sig_phi_mask = (p_phi_fdr < FDR_ALPHA) & (phi > 0)

    G_net = nx.Graph()
    G_net.add_nodes_from(all_genera)
    for ii, jj, w in zip(triu_i[sig_phi_mask], triu_j[sig_phi_mask], phi[sig_phi_mask]):
        G_net.add_edge(all_genera[ii], all_genera[jj], weight=float(w))
    print(f"    Network: {G_net.number_of_nodes()} nodes, {G_net.number_of_edges()} edges")

    degree_dict = dict(G_net.degree(weight='weight'))
    # Skip clustering+betweenness when network is too dense or explicitly requested.
    # At 42% co-occurrence (2.5M edges), O(N*k²) clustering is intractable and near-constant.
    if skip_network_metrics or G_net.number_of_edges() > 500_000:
        clustering_dict  = {}
        betweenness_dict = {}
        print(f"    Clustering+betweenness: SKIPPED (edges={G_net.number_of_edges():,}, too dense)")
    else:
        clustering_dict  = nx.clustering(G_net, weight='weight')
        k_btw = min(100, max(2, G_net.number_of_nodes() - 1))
        betweenness_dict = nx.betweenness_centrality(G_net, normalized=True, k=k_btw, seed=42) \
            if G_net.number_of_nodes() > 2 else {}
        print(f"    Clustering+betweenness done ({time.time()-t2:.0f}s)")

    part_b = pd.DataFrame({
        'genus_lower': all_genera,
        'degree':      [degree_dict.get(g, 0) for g in all_genera],
        'clustering':  [clustering_dict.get(g, 0) for g in all_genera],
        'betweenness': [betweenness_dict.get(g, 0) for g in all_genera],
    })

    # ── Part C: Partner MPD/SES (Python/numpy) ──────────────────
    avg_k = sig_pos_mat.sum(axis=1).mean()
    if skip_network_metrics or avg_k > 500:
        # With avg k>500 partners, 999 permutations × 1,574 genera takes >1 hour.
        # MPD/SES is biologically uninterpretable at near-complete co-occurrence.
        part_c = pd.DataFrame({'genus_lower': all_genera,
                               'n_tree_partners': np.nan,
                               'MPD_obs': np.nan, 'MPD_ses': np.nan})
        print(f"  Part C: SKIPPED (avg sig+ partners={avg_k:.0f}, too dense for SES)")
    else:
        print(f"  Part C: MPD/SES ({N_PERM} permutations, Python/numpy)...")
        t3 = time.time()
        part_c = compute_mpd_ses({}, all_genera, sig_pos_mat, g_idx)
        print(f"    MPD non-null: {part_c.MPD_obs.notna().sum()}  ({time.time()-t3:.0f}s)")

    # ── Merge for PGLS ──────────────────────────────────────────
    pgls_in = pred[['genus_lower','predictor_z','genome_mb_z','mean_levins_B_std']].copy()
    pgls_in = pgls_in.merge(
        part_a[['genus_lower','sig_pos_partners','sig_neg_partners','prevalence']],
        on='genus_lower', how='left')
    pgls_in = pgls_in.merge(
        part_b[['genus_lower','degree','clustering','betweenness']], on='genus_lower', how='left')
    pgls_in = pgls_in.merge(
        part_c[['genus_lower','n_tree_partners','MPD_obs','MPD_ses']], on='genus_lower', how='left')

    pgls_csv = f'/tmp/cooc_pgls_input_{name}.csv'
    pgls_in.to_csv(pgls_csv, index=False)
    print(f"  PGLS merge: {len(pgls_in)} genera, "
          f"sig_pos non-null={pgls_in.sig_pos_partners.notna().sum()}, "
          f"MPD non-null={pgls_in.MPD_obs.notna().sum()}")

    # ── PGLS in R ───────────────────────────────────────────────
    pgls_out = f'/tmp/cooc_pgls_results_{name}.csv'
    r_pgls = f"""
suppressPackageStartupMessages({{library(ape); library(nlme)}})
df <- read.csv("{pgls_csv}", stringsAsFactors=FALSE)
tree <- read.tree("{TREE}")
df$genus_tree <- df$genus_lower
shared <- intersect(df$genus_tree, tree$tip.label)
tree_p <- drop.tip(tree, setdiff(tree$tip.label, shared))
df <- df[df$genus_tree %in% shared, ]
df <- df[match(tree_p$tip.label, df$genus_tree), ]
rownames(df) <- df$genus_tree
cat(sprintf("PGLS n=%d (stratum: {name})\\n", nrow(df)))
run_model <- function(response_col) {{
  df_s <- df[!is.na(df[[response_col]]) & is.finite(df[[response_col]]), ]
  tp <- drop.tip(tree_p, setdiff(tree_p$tip.label, df_s$genus_tree))
  df_s <- df_s[match(tp$tip.label, df_s$genus_tree), ]
  if (nrow(df_s) < 30) {{
    cat(sprintf("  %s: n=%d too small\\n", response_col, nrow(df_s))); return(NULL)
  }}
  fml <- as.formula(sprintf("%s ~ predictor_z + genome_mb_z", response_col))
  tryCatch({{
    mod <- gls(fml, data=df_s,
               correlation=corPagel(value=1, phy=tp, fixed=FALSE, form=~genus_tree),
               method="ML", na.action=na.omit)
    co <- summary(mod)$tTable
    lam <- as.numeric(mod$modelStruct$corStruct)
    n_fit <- length(mod$residuals)
    cat(sprintf("  %s: n=%d lambda=%.3f\\n", response_col, n_fit, lam))
    rows <- list()
    for (pn in rownames(co)) {{
      if (pn == "(Intercept)") next
      rows[[length(rows)+1]] <- data.frame(
        response=response_col, stratum="{name}", predictor=pn,
        n=n_fit, lambda=lam,
        beta=co[pn,1], SE=co[pn,2], t=co[pn,3], p=co[pn,4],
        stringsAsFactors=FALSE)
    }}
    rows
  }}, error=function(e) {{
    cat(sprintf("  ERROR %s: %s\\n", response_col, conditionMessage(e))); NULL
  }})
}}
responses <- c("sig_pos_partners","sig_neg_partners","degree",
               "betweenness","clustering","MPD_obs","MPD_ses")
rows_all <- Filter(Negate(is.null),
                   unlist(lapply(responses, run_model), recursive=FALSE))
out <- do.call(rbind, rows_all)
write.csv(out, "{pgls_out}", row.names=FALSE)
cat("PGLS saved.\\n")
"""
    r_file = f'/tmp/cooc_pgls_{name}.R'
    with open(r_file, 'w') as f:
        f.write(r_pgls)
    res_p = subprocess.run([RSCRIPT, r_file], capture_output=True, text=True, timeout=3600)
    print(res_p.stdout[-2000:] if len(res_p.stdout) > 2000 else res_p.stdout)
    if res_p.returncode != 0:
        print(f"  PGLS R error: {res_p.stderr[-400:]}")
    try:
        pgls_res = pd.read_csv(pgls_out)
    except Exception:
        pgls_res = pd.DataFrame()

    # ── Spearman correlations ────────────────────────────────────
    from scipy.stats import spearmanr
    corr_rows = []
    for cc in ['sig_pos_partners','sig_neg_partners','degree','betweenness',
               'clustering','MPD_obs','MPD_ses']:
        sub = pgls_in[[cc,'mean_levins_B_std']].dropna()
        if len(sub) < 20: continue
        rho, pval = spearmanr(sub[cc], sub['mean_levins_B_std'])
        corr_rows.append({'stratum': name, 'metric': cc, 'n': len(sub),
                          'rho_vs_Bstd': rho, 'p_vs_Bstd': pval})

    # ── Scatter plot ─────────────────────────────────────────────
    pdat = pgls_in[['predictor_z','sig_pos_partners','mean_levins_B_std']].dropna()
    b_med = pdat.mean_levins_B_std.median()
    fig, ax = plt.subplots(figsize=(7, 5))
    for lbl, clr in [('Generalist', '#2a78d6'), ('Specialist', '#e34948')]:
        sub = pdat[pdat.mean_levins_B_std > b_med] if lbl == 'Generalist' else \
              pdat[pdat.mean_levins_B_std <= b_med]
        ax.scatter(sub.predictor_z, sub.sig_pos_partners, c=clr, alpha=0.35,
                   s=15, label=lbl, rasterized=True)
    ax.set_xlabel('Metal-gene KO density (z-score)', fontsize=11)
    ax.set_ylabel('Significant positive partners\n(hypergeometric FDR < 5%)', fontsize=11)
    ax.set_title(f'Co-occurrence vs metal-gene investment [{name}]', fontsize=12)
    ax.legend(title='Cross-biome niche breadth', fontsize=9)
    ax.spines[['top','right']].set_visible(False)
    fig.tight_layout()
    scatter_pdf = f"{RES}/cooccurrence_scatter_{name}.pdf"
    fig.savefig(scatter_pdf, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  Scatter: {scatter_pdf}")

    return {
        'name': name, 'G': G, 'S': S, 'N_PAIRS': N_PAIRS,
        'n_sig_pos': int(sig_pos_mask.sum()), 'n_sig_neg': int(sig_neg_mask.sum()),
        'n_sig_phi': int(sig_phi_mask.sum()),
        'part_a': part_a, 'part_b': part_b, 'part_c': part_c,
        'pgls_in': pgls_in, 'pgls_results': pgls_res,
        'corr_rows': corr_rows,
    }


# ─────────────────────────────────────────────────────────────────
# Build per-stratum sample sets and run
# ─────────────────────────────────────────────────────────────────
strata_results = {}
strata_results['all'] = run_stratum('all', sg_all, skip_network_metrics=True)

if env_map is not None:
    # Environmental: exclude host-associated (plant, flower, leaf)
    env_acc = set(env_map[~env_map['Env_Level_1'].isin(HOST_ENVS)]['accession_id'])
    sg_env  = sg_all[sg_all['accession_id'].isin(env_acc)].copy()
    prev_e  = sg_env.groupby('genus_lower')['accession_id'].nunique()
    sg_env  = sg_env[sg_env['genus_lower'].isin(prev_e[prev_e >= 10].index)].copy()
    strata_results['env'] = run_stratum('env', sg_env)

    # Soil only
    soil_acc = set(env_map[env_map['Env_Level_1'].isin(SOIL_ENVS)]['accession_id'])
    sg_soil  = sg_all[sg_all['accession_id'].isin(soil_acc)].copy()
    prev_s   = sg_soil.groupby('genus_lower')['accession_id'].nunique()
    sg_soil  = sg_soil[sg_soil['genus_lower'].isin(prev_s[prev_s >= 10].index)].copy()
    strata_results['soil'] = run_stratum('soil', sg_soil)


# ─────────────────────────────────────────────────────────────────
# Collate and save outputs
# ─────────────────────────────────────────────────────────────────
print("\n=== Collating results ===")
all_pgls = pd.concat([r['pgls_results'] for r in strata_results.values()
                       if not r['pgls_results'].empty], ignore_index=True)
all_corr = pd.concat([pd.DataFrame(r['corr_rows']) for r in strata_results.values()
                       if r['corr_rows']], ignore_index=True)
all_pgls.to_csv(f"{RES}/cooccurrence_pgls_results.csv", index=False)
all_corr.to_csv(f"{RES}/cooccurrence_correlations.csv", index=False)
print(f"  cooccurrence_pgls_results.csv ({len(all_pgls)} rows)")
print(f"  cooccurrence_correlations.csv ({len(all_corr)} rows)")


# ─────────────────────────────────────────────────────────────────
# Markdown report
# ─────────────────────────────────────────────────────────────────
def fmt_p(p):
    if p < 0.001: return f"{p:.2e}***"
    elif p < 0.01: return f"{p:.3f}**"
    elif p < 0.05: return f"{p:.3f}*"
    return f"{p:.3f}"

lines = [
    "# Co-occurrence Analysis Report",
    "",
    "*Generated by `scripts/run_cooccurrence_analysis.py`*",
    "",
    "---",
    "",
    "## Methods",
    "",
    "**Data:** MicrobeAtlas (arkinlab_microbeatlas). Three strata:",
    "- **all**: all genera present in ≥10 samples, all sample types",
    "- **env**: environmental only — exclude plant/flower/leaf host-associated samples",
    "- **soil**: soil environments only (soil, agricultural, farm, paddy, field, forest, shrub, peatland, desert)",
    "",
    "**Genus prevalence filter:** ≥10 samples within stratum.",
    "",
    "**Part A — Hypergeometric null (Veech 2013):** Fixed-fixed analytical test.",
    "P_pos = P(X≥K | S, N_i, N_j); P_neg = P(X≤K | S, N_i, N_j). BH FDR 5%.",
    "",
    "**Part B — Phi-coefficient network:** φ = (K·S − N_i·N_j) / √(N_i(S−N_i)·N_j(S−N_j)).",
    "t-approximation p-values, BH FDR. Network of significant positive φ edges.",
    "Weighted degree reported for all strata. Clustering (Watts-Strogatz, weighted) and betweenness",
    "centrality (k=100 pivot approximation) computed for 'env' and 'soil' strata only;",
    "skipped for 'all' (2.5M edges, 42% co-occurrence → near-complete graph, metrics degenerate).",
    "",
    "**Part C — Partner MPD/SES:** For each focal genus (in PGLS dataset), compute mean pairwise",
    "phylogenetic distance (MPD) of its significant positive-partner set within GTDB cophenetic space.",
    f"SES = (MPD_obs − mean(MPD_null)) / SD(MPD_null), {N_PERM} random sets sampled from precomputed",
    "cophenetic distance matrix (dendropy + numpy; GTDB r214 2,283 genus tips).",
    "Computed for 'env' and 'soil' strata; skipped for 'all' (avg partner set >500 → SES near-degenerate).",
    "",
    "**PGLS:** `metric ~ ko_per_mb_z + genome_mb_z`, Pagel's λ, GTDB r214 genus tree.",
    "",
    "---",
    "",
    "## Summary across strata",
    "",
    "| Stratum | Genera | Samples | Sig+ pairs (FDR<5%) | Sig− pairs | Phi-net edges |",
    "|---------|--------|---------|---------------------|------------|---------------|",
]
for name, r in strata_results.items():
    lines.append(
        f"| {name} | {r['G']:,} | {r['S']:,} | "
        f"{r['n_sig_pos']:,} ({r['n_sig_pos']*100/r['N_PAIRS']:.2f}%) | "
        f"{r['n_sig_neg']:,} ({r['n_sig_neg']*100/r['N_PAIRS']:.2f}%) | "
        f"{r['n_sig_phi']:,} |")

lines += ["", "---", "", "## Per-stratum results", ""]

for name, r in strata_results.items():
    pa_ = r['part_a']
    pb_ = r['part_b']
    pc_ = r['part_c']
    lines += [
        f"### Stratum: {name.upper()}  ({r['G']:,} genera, {r['S']:,} samples)",
        "",
        "**Part A — hypergeometric partner counts (all genera):**",
        "",
        "| Metric | Mean | Median | Max |",
        "|--------|------|--------|-----|",
        f"| sig_pos_partners | {pa_.sig_pos_partners.mean():.1f} | {int(pa_.sig_pos_partners.median())} | {pa_.sig_pos_partners.max()} |",
        f"| sig_neg_partners | {pa_.sig_neg_partners.mean():.1f} | {int(pa_.sig_neg_partners.median())} | {pa_.sig_neg_partners.max()} |",
        "",
        "**Part B — phi-coefficient network:**",
        "",
        "| Metric | Mean | Max |",
        "|--------|------|-----|",
        f"| Degree (weighted) | {pb_.degree.mean():.3f} | {pb_.degree.max():.3f} |",
        f"| Betweenness | {pb_.betweenness.mean():.5f} | {pb_.betweenness.max():.5f} |",
        f"| Clustering | {pb_.clustering.mean():.4f} | {pb_.clustering.max():.4f} |",
        "",
        "**Part C — partner phylogenetic diversity (PGLS genera only):**",
        "",
        "| Metric | n valid | Mean | SD |",
        "|--------|---------|------|----|",
        f"| MPD_obs | {pc_.MPD_obs.notna().sum()} | {pc_.MPD_obs.mean():.3f} | {pc_.MPD_obs.std():.3f} |",
        f"| SES_MPD | {pc_.MPD_ses.notna().sum()} | {pc_.MPD_ses.mean():.3f} | {pc_.MPD_ses.std():.3f} |",
        "",
        f"Mean SES_MPD = {pc_.MPD_ses.mean():.3f} — "
        + ("phylogenetically clustered (SES < 0)" if pc_.MPD_ses.mean() < 0 else "overdispersed (SES > 0)"),
        "",
    ]
    if not r['pgls_results'].empty:
        ko_rows = r['pgls_results'][r['pgls_results'].predictor == 'predictor_z']
        lines += [
            "**PGLS — ko_per_mb_z predictor:**",
            "",
            "| Response | n | λ | β | SE | t | p |",
            "|----------|---|---|---|----|---|---|",
        ]
        for _, row in ko_rows.iterrows():
            sig = ' ***' if row.p < 0.001 else ' **' if row.p < 0.01 else ' *' if row.p < 0.05 else ''
            lines.append(
                f"| {row.response} | {int(row.n)} | {row['lambda']:.3f} | "
                f"{row.beta:.4f} | {row.SE:.4f} | {row.t:.3f} | {fmt_p(row.p)}{sig} |")
        lines.append("")
    lines.append("---\n")

if not all_corr.empty:
    lines += ["## Spearman correlations with B_std (cross-biome niche breadth)", ""]
    for strat in strata_results:
        sub = all_corr[all_corr.stratum == strat].sort_values('p_vs_Bstd')
        if sub.empty: continue
        lines.append(f"**{strat.upper()}:**\n")
        lines += ["| Metric | n | ρ vs B_std | p |",
                  "|--------|---|-----------|---|"]
        for _, row in sub.iterrows():
            sig = ' ***' if row.p_vs_Bstd < 0.001 else ' **' if row.p_vs_Bstd < 0.01 \
                  else ' *' if row.p_vs_Bstd < 0.05 else ''
            lines.append(f"| {row.metric} | {int(row.n)} | {row.rho_vs_Bstd:.3f} | "
                         f"{fmt_p(row.p_vs_Bstd)}{sig} |")
        lines.append("")

with open(f"{RES}/cooccurrence_analysis_report.md", 'w') as f:
    f.write('\n'.join(lines))

print(f"\nReport: results/cooccurrence_analysis_report.md")
print("\n=== Co-occurrence analysis complete ===")

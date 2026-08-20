#!/usr/bin/env python3
"""
Co-occurrence analysis: Parts A, B, C
EMP/MicrobeAtlas genus presence/absence matrix (genera in ≥10 samples).

Part A: Hypergeometric null model (analytical fixed-fixed equivalent, Veech 2013).
        Per-genus count of sig positive / negative partners (FDR 5%).
        PGLS: sig_pos_partners ~ ko_per_mb_primary_z + genome_size_mb_z
        Correlate with social count breadth, SES, cross-biome B_std.

Part B: Phi-coefficient co-occurrence network (Pearson of binary vectors = phi),
        FDR-corrected p<0.05. Per-genus degree, betweenness centrality, clustering.
        PGLS for each metric. Correlate with existing social metrics.

Part C: Partner phylogenetic diversity (sum of GTDB branch lengths).
        MPD and SES via 999 permutations. PGLS, correlations.

Output: projects/comprehensive_metal_ecology/results/cooccurrence_analysis_report.md
"""
import os
os.environ['OMP_NUM_THREADS'] = '1'

import sys
import time
import numpy as np
import pandas as pd
import scipy.sparse as sp
from scipy.stats import hypergeom, pearsonr, spearmanr
from scipy.spatial.distance import squareform
from statsmodels.stats.multitest import multipletests
import networkx as nx

from berdl_notebook_utils.setup_spark_session import get_spark_session
spark = get_spark_session()
from pyspark.sql import functions as F

DATA  = "projects/comprehensive_metal_ecology/data"
RES   = "projects/comprehensive_metal_ecology/results"
TREE  = "projects/microbeatlas_metal_ecology/data/gtdb_bac_genus_pruned.tree"
MIN_SAMPLES = 10   # genus must appear in ≥10 samples
FDR_ALPHA   = 0.05

print("=" * 60)
print("Co-occurrence analysis: Parts A, B, C")
print("=" * 60)

# ─────────────────────────────────────────────────────────────────
# STEP 1: Build genus × sample binary matrix
# ─────────────────────────────────────────────────────────────────
print("\nStep 1: Building genus × sample binary matrix from MicrobeAtlas...")
t0 = time.time()

_tax_parts = F.split(F.col("Tax"), ";")
otu_meta = spark.table("arkinlab_microbeatlas.otu_metadata") \
    .select(
        "otu_id",
        F.when(F.size(_tax_parts) >= 6, _tax_parts.getItem(5)).alias("genus")
    ) \
    .filter(F.col("genus").isNotNull() & (F.length(F.trim(F.col("genus"))) > 0))

otu_counts = spark.table("arkinlab_microbeatlas.otu_counts_long") \
    .select(F.col("sample_id").alias("accession_id"), "otu_id", "count") \
    .filter(F.col("count") > 0)

sample_genus_spark = otu_counts.join(otu_meta, on="otu_id", how="inner") \
    .select("accession_id", F.lower(F.trim(F.col("genus"))).alias("genus_lower")) \
    .distinct()

# Use collect_set to avoid maxResultSize
stg = sample_genus_spark.groupBy("accession_id") \
    .agg(F.collect_set("genus_lower").alias("genera"))
stg_pd = stg.toPandas()
print(f"  {len(stg_pd)} samples collected ({time.time()-t0:.0f}s)")

# Explode and build sparse binary matrix
sg_pd = stg_pd.explode("genera").rename(columns={"genera": "genus_lower"}).dropna(subset=["genus_lower"])
print(f"  {len(sg_pd)} sample-genus pairs, {sg_pd.genus_lower.nunique()} genera")

# Filter genera to ≥MIN_SAMPLES
genus_counts = sg_pd.groupby("genus_lower")["accession_id"].nunique()
valid_genera = genus_counts[genus_counts >= MIN_SAMPLES].index
sg_pd = sg_pd[sg_pd.genus_lower.isin(valid_genera)].copy()
print(f"  After ≥{MIN_SAMPLES}-sample filter: {sg_pd.genus_lower.nunique()} genera, {sg_pd.accession_id.nunique()} samples")

spark.stop()
print("  Spark stopped.")

# Build index maps
all_genera  = sorted(sg_pd.genus_lower.unique())
all_samples = sorted(sg_pd.accession_id.unique())
g_idx = {g: i for i, g in enumerate(all_genera)}
s_idx = {s: i for i, s in enumerate(all_samples)}
G = len(all_genera)
S = len(all_samples)
print(f"  Matrix: {G} genera × {S} samples")

# Build sparse binary matrix (genera × samples)
row_idx = sg_pd.genus_lower.map(g_idx).values
col_idx = sg_pd.accession_id.map(s_idx).values
data_vals = np.ones(len(sg_pd), dtype=np.uint8)
M = sp.csr_matrix((data_vals, (row_idx, col_idx)), shape=(G, S), dtype=np.uint8)

# Row sums = genus prevalences
row_sums = np.asarray(M.sum(axis=1)).ravel()
print(f"  Prevalence range: {row_sums.min()}–{row_sums.max()} samples per genus")

# ─────────────────────────────────────────────────────────────────
# PART A: Hypergeometric null model (fixed-fixed analytical)
# ─────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("PART A: Hypergeometric null model")
print("=" * 60)
t1 = time.time()

# Co-occurrence count matrix: MxM = K[i,j] = number of shared samples
print("  Computing pairwise co-occurrence counts (sparse matrix mult)...")
coo_counts = (M.astype(np.int32) @ M.T.astype(np.int32)).toarray()  # G × G
np.fill_diagonal(coo_counts, 0)
print(f"  Done ({time.time()-t1:.0f}s). Max co-occurrence: {coo_counts.max()}")

# For each pair (i,j), K[i,j] observed co-occurrences
# Under hypergeometric: draw N_j items from population of S,
# N_i successes in population → P(X = K) = hypergeom(S, N_i, N_j)
# P_positive[i,j] = P(X >= K[i,j]) (unexpected high co-occurrence)
# P_negative[i,j] = P(X <= K[i,j]) (unexpected low co-occurrence)

print("  Computing hypergeometric p-values for all pairs...")
# Use vectorised approach: upper triangle only
triu_i, triu_j = np.triu_indices(G, k=1)
N_PAIRS = len(triu_i)
print(f"  {N_PAIRS:,} unique pairs")

K_obs  = coo_counts[triu_i, triu_j]
N_i    = row_sums[triu_i]
N_j    = row_sums[triu_j]

# Hypergeometric: population S, successes_in_pop N_i, draws N_j
# p_pos = P(X >= K) = 1 - CDF(K-1)
# p_neg = P(X <= K) = CDF(K)
p_pos = np.zeros(N_PAIRS, dtype=np.float64)
p_neg = np.zeros(N_PAIRS, dtype=np.float64)

CHUNK = 500_000
for start in range(0, N_PAIRS, CHUNK):
    end = min(start + CHUNK, N_PAIRS)
    p_pos[start:end] = hypergeom.sf(K_obs[start:end] - 1, S, N_i[start:end], N_j[start:end])
    p_neg[start:end] = hypergeom.cdf(K_obs[start:end],     S, N_i[start:end], N_j[start:end])
    if start % 5_000_000 == 0 and start > 0:
        print(f"    Processed {start:,}/{N_PAIRS:,} pairs...")

print(f"  p-value computation done ({time.time()-t1:.0f}s)")

# FDR correction on positive and negative separately
_, p_pos_fdr, _, _ = multipletests(p_pos, method='fdr_bh')
_, p_neg_fdr, _, _ = multipletests(p_neg, method='fdr_bh')

sig_pos_mat = np.zeros((G, G), dtype=np.int8)
sig_neg_mat = np.zeros((G, G), dtype=np.int8)
sig_pos_mask = p_pos_fdr < FDR_ALPHA
sig_neg_mask = p_neg_fdr < FDR_ALPHA

sig_pos_mat[triu_i[sig_pos_mask], triu_j[sig_pos_mask]] = 1
sig_pos_mat[triu_j[sig_pos_mask], triu_i[sig_pos_mask]] = 1
sig_neg_mat[triu_i[sig_neg_mask], triu_j[sig_neg_mask]] = 1
sig_neg_mat[triu_j[sig_neg_mask], triu_i[sig_neg_mask]] = 1

sig_pos_per_genus = sig_pos_mat.sum(axis=1)
sig_neg_per_genus = sig_neg_mat.sum(axis=1)

print(f"  Sig positive pairs: {sig_pos_mask.sum():,} ({sig_pos_mask.sum()*100/N_PAIRS:.2f}%)")
print(f"  Sig negative pairs: {sig_neg_mask.sum():,} ({sig_neg_mask.sum()*100/N_PAIRS:.2f}%)")

# Build Part A result DataFrame
part_a = pd.DataFrame({
    'genus_lower': all_genera,
    'prevalence': row_sums,
    'sig_pos_partners': sig_pos_per_genus,
    'sig_neg_partners': sig_neg_per_genus,
})
print(f"  sig_pos_partners: mean={part_a.sig_pos_partners.mean():.1f}, max={part_a.sig_pos_partners.max()}")
print(f"  sig_neg_partners: mean={part_a.sig_neg_partners.mean():.1f}, max={part_a.sig_neg_partners.max()}")

# ─────────────────────────────────────────────────────────────────
# PART B: Phi-coefficient co-occurrence network
# ─────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("PART B: Phi-coefficient network + network metrics")
print("=" * 60)
t2 = time.time()

# Phi coefficient = Pearson correlation of binary vectors
# phi = (K*S - N_i*N_j) / sqrt(N_i * (S-N_i) * N_j * (S-N_j))
print("  Computing phi coefficients for all pairs...")
K_obs_all = K_obs.astype(np.float64)
N_i_f = N_i.astype(np.float64)
N_j_f = N_j.astype(np.float64)
S_f = float(S)

phi = (K_obs_all * S_f - N_i_f * N_j_f) / np.sqrt(
    N_i_f * (S_f - N_i_f) * N_j_f * (S_f - N_j_f) + 1e-300
)
# Clamp to [-1, 1]
phi = np.clip(phi, -1, 1)

# Analytical p-values for phi (equivalent to Pearson correlation)
# t = phi * sqrt(n-2) / sqrt(1 - phi²), df = n-2
from scipy.stats import t as t_dist
df_stat = S - 2
t_stat  = phi * np.sqrt(df_stat) / np.sqrt(1 - phi**2 + 1e-300)
p_phi   = 2 * t_dist.sf(np.abs(t_stat), df=df_stat)

# FDR correction
_, p_phi_fdr, _, _ = multipletests(p_phi, method='fdr_bh')
sig_phi_mask = (p_phi_fdr < FDR_ALPHA) & (phi > 0)  # significant positive associations only
print(f"  Significant positive phi pairs (FDR<5%): {sig_phi_mask.sum():,}")

# Build network
print("  Building networkx graph...")
G_net = nx.Graph()
G_net.add_nodes_from(all_genera)
edge_i = triu_i[sig_phi_mask]
edge_j = triu_j[sig_phi_mask]
edge_w = phi[sig_phi_mask]
for ii, jj, w in zip(edge_i, edge_j, edge_w):
    G_net.add_edge(all_genera[ii], all_genera[jj], weight=float(w))

print(f"  Network: {G_net.number_of_nodes()} nodes, {G_net.number_of_edges()} edges")

# Per-genus network metrics
print("  Computing degree, clustering coefficient...")
degree_dict      = dict(G_net.degree(weight='weight'))
clustering_dict  = nx.clustering(G_net, weight='weight')

print("  Computing betweenness centrality (may take several minutes)...")
# Sample-based betweenness for large networks
if G_net.number_of_nodes() > 2000:
    betweenness_dict = nx.betweenness_centrality(G_net, normalized=True, k=500, seed=42)
else:
    betweenness_dict = nx.betweenness_centrality(G_net, normalized=True)
print(f"  Betweenness done ({time.time()-t2:.0f}s)")

part_b = pd.DataFrame({
    'genus_lower': all_genera,
    'degree':         [degree_dict.get(g, 0) for g in all_genera],
    'clustering':     [clustering_dict.get(g, 0) for g in all_genera],
    'betweenness':    [betweenness_dict.get(g, 0) for g in all_genera],
})
print(f"  degree: mean={part_b.degree.mean():.2f}, max={part_b.degree.max()}")
print(f"  betweenness: mean={part_b.betweenness.mean():.4f}, max={part_b.betweenness.max():.4f}")

# ─────────────────────────────────────────────────────────────────
# PART C: Partner phylogenetic diversity
# ─────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("PART C: Partner phylogenetic diversity (PD, MPD, SES)")
print("=" * 60)
t3 = time.time()

import ete3

print("  Loading GTDB tree...")
try:
    from ete3 import Tree
    tree_ete = Tree(TREE, format=1)
    tip_names = set([n.name for n in tree_ete.get_leaves()])
    print(f"  Tree tips: {len(tip_names)}")
except Exception as e:
    print(f"  ete3 failed: {e}")
    # Fallback to ape via rpy2 — but let's try with ape directly via subprocess
    tree_ete = None

# Fallback: compute pairwise distances using ape in R
# Write partner sets to a file, run R script to compute PD/MPD

if tree_ete is None:
    print("  Using R/ape for PD computation...")
    import subprocess, json, tempfile

    # Write partner lists to JSON
    partner_data = {}
    for g in all_genera:
        partners_a = [all_genera[k] for k in range(G) if sig_pos_mat[g_idx[g], k] == 1]
        partner_data[g] = partners_a

    partner_file = '/tmp/cooccurrence_partners.json'
    with open(partner_file, 'w') as f:
        json.dump(partner_data, f)

    # R script for PD/MPD/SES
    r_script = f"""
suppressPackageStartupMessages({{library(ape); library(picante)}})
cat("Loading tree...\\n")
tree <- read.tree("{TREE}")
tree$tip.label <- gsub(" ", "_", tree$tip.label)

# Load partner data
library(jsonlite)
partners <- fromJSON("{partner_file}")

cat(sprintf("Computing PD/MPD for %d genera...\\n", length(partners)))

results <- lapply(names(partners), function(g) {{
  g_tree <- gsub(" ", "_", g)
  pts <- partners[[g]]
  pts_tree <- gsub(" ", "_", pts)
  # Keep only tips in tree
  valid_pts <- intersect(pts_tree, tree$tip.label)
  if (length(valid_pts) < 2) {{
    return(data.frame(genus=g, n_partners=length(valid_pts),
                      PD=NA, MPD_obs=NA, MPD_ses=NA, stringsAsFactors=FALSE))
  }}
  tips_set <- c(g_tree, valid_pts)
  tips_set <- intersect(tips_set, tree$tip.label)
  if (length(tips_set) < 2) {{
    return(data.frame(genus=g, n_partners=length(valid_pts),
                      PD=NA, MPD_obs=NA, MPD_ses=NA, stringsAsFactors=FALSE))
  }}
  # Compute PD = sum of branch lengths of minimal spanning clade
  sub_tree <- tryCatch(drop.tip(tree, setdiff(tree$tip.label, tips_set)), error=function(e) NULL)
  if (is.null(sub_tree)) {{
    return(data.frame(genus=g, n_partners=length(valid_pts),
                      PD=NA, MPD_obs=NA, MPD_ses=NA, stringsAsFactors=FALSE))
  }}
  PD <- sum(sub_tree$edge.length)
  # MPD: mean pairwise branch distance
  d <- cophenetic(sub_tree)
  MPD_obs <- mean(d[upper.tri(d)])
  # SES: 999 random sets of same size from tree tips
  all_tips <- tree$tip.label
  null_mpds <- replicate(999, {{
    rnd_tips <- sample(all_tips, length(tips_set))
    rnd_tree <- tryCatch(drop.tip(tree, setdiff(tree$tip.label, rnd_tips)), error=function(e) NULL)
    if (is.null(rnd_tree) || length(rnd_tree$tip.label) < 2) return(NA)
    d_rnd <- cophenetic(rnd_tree)
    mean(d_rnd[upper.tri(d_rnd)])
  }})
  null_mpds <- null_mpds[!is.na(null_mpds)]
  MPD_ses <- if (length(null_mpds) > 10) (MPD_obs - mean(null_mpds)) / sd(null_mpds) else NA
  data.frame(genus=g, n_partners=length(valid_pts),
             PD=PD, MPD_obs=MPD_obs, MPD_ses=MPD_ses, stringsAsFactors=FALSE)
}})

out <- do.call(rbind, results)
write.csv(out, "/tmp/cooccurrence_pd_results.csv", row.names=FALSE)
cat("Done.\\n")
"""
    r_file = '/tmp/cooccurrence_pd.R'
    with open(r_file, 'w') as f:
        f.write(r_script)

    print("  Running R for PD/MPD/SES computation (this may take 30+ minutes)...")
    result = subprocess.run(['/home/hmacgregor/r_env/bin/Rscript', r_file],
                            capture_output=True, text=True, timeout=7200)
    if result.returncode == 0:
        print("  R completed successfully.")
        part_c = pd.read_csv('/tmp/cooccurrence_pd_results.csv')
        part_c = part_c.rename(columns={'genus': 'genus_lower'})
    else:
        print(f"  R failed: {result.stderr[:500]}")
        part_c = pd.DataFrame({'genus_lower': all_genera, 'n_partners': sig_pos_per_genus,
                               'PD': np.nan, 'MPD_obs': np.nan, 'MPD_ses': np.nan})

else:
    print("  Using ete3 for PD computation...")
    # ete3-based PD/MPD computation
    # Pre-compute pairwise distance matrix for all genera in tree
    tree_genera = [g for g in all_genera if g.replace(' ', '_') in tip_names]
    print(f"  {len(tree_genera)} genera in tree out of {len(all_genera)}")

    # Get all pairwise distances via ete3 (may be slow for large trees)
    from ete3 import Tree
    import itertools

    # Prune tree to relevant genera
    prune_list = [g.replace(' ', '_') for g in tree_genera]
    tree_pruned = tree_ete.copy()
    to_prune = [n.name for n in tree_pruned.get_leaves() if n.name not in prune_list]
    if to_prune:
        tree_pruned.prune(prune_list, preserve_branch_length=True)

    # Get distance matrix
    print("  Computing pairwise phylogenetic distances...")
    pd_matrix_dict = {}
    for node in tree_pruned.get_leaves():
        pd_matrix_dict[node.name] = tree_pruned.get_distance(node)

    # Build PD DataFrame
    PD_list, MPD_list, SES_list, n_list = [], [], [], []
    for g in all_genera:
        g_tree = g.replace(' ', '_')
        partners = [all_genera[k] for k in range(G) if sig_pos_mat[g_idx[g], k] == 1]
        valid_ptrs = [p.replace(' ', '_') for p in partners if p.replace(' ', '_') in prune_list]
        n_list.append(len(valid_ptrs))
        if len(valid_ptrs) < 2:
            PD_list.append(np.nan); MPD_list.append(np.nan); SES_list.append(np.nan)
            continue
        tips_set = [g_tree] + valid_ptrs
        tips_set = [t for t in tips_set if t in prune_list]
        # PD and MPD using pairwise distances
        tip_nodes = [n for n in tree_pruned.get_leaves() if n.name in tips_set]
        dists = [tip_nodes[a].get_distance(tip_nodes[b])
                 for a in range(len(tip_nodes)) for b in range(a+1, len(tip_nodes))]
        MPD_obs = float(np.mean(dists))
        # Approximate PD as total branch length of subtree
        subtree = tree_pruned.copy()
        subtree.prune(tips_set, preserve_branch_length=True)
        PD_val = sum(n.dist for n in subtree.traverse() if n != subtree)
        # SES: 999 random sets
        all_tree_tips = prune_list
        null_mpds = []
        for _ in range(999):
            rnd_tips = np.random.choice(all_tree_tips, size=len(tips_set), replace=False)
            rnd_nodes = [n for n in tree_pruned.get_leaves() if n.name in rnd_tips]
            if len(rnd_nodes) < 2: continue
            rnd_dists = [rnd_nodes[a].get_distance(rnd_nodes[b])
                         for a in range(len(rnd_nodes)) for b in range(a+1, len(rnd_nodes))]
            null_mpds.append(np.mean(rnd_dists))
        SES = (MPD_obs - np.mean(null_mpds)) / (np.std(null_mpds) + 1e-10) if null_mpds else np.nan
        PD_list.append(PD_val); MPD_list.append(MPD_obs); SES_list.append(SES)

    part_c = pd.DataFrame({'genus_lower': all_genera, 'n_partners': n_list,
                           'PD': PD_list, 'MPD_obs': MPD_list, 'MPD_ses': SES_list})

print(f"  Part C done ({time.time()-t3:.0f}s)")
print(f"  PD non-null: {part_c.PD.notna().sum()}, MPD non-null: {part_c.MPD_obs.notna().sum()}")

# ─────────────────────────────────────────────────────────────────
# PGLS via R for all response variables
# ─────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("PGLS: all co-occurrence metrics ~ KO density + genome size")
print("=" * 60)

# Merge all parts with predictors
pred = pd.read_csv(f"{DATA}/01_pgls_input_bacteria.csv")
part_a['genus_lower_key'] = part_a.genus_lower.str.replace("'", "", regex=False)
part_b['genus_lower_key'] = part_b.genus_lower.str.replace("'", "", regex=False)
part_c['genus_lower_key'] = part_c.genus_lower.str.replace("'", "", regex=False)

pgls_in = pred[['genus_lower','ko_per_mb_primary','mean_genome_mb','predictor_z','genome_mb_z']].copy()
pgls_in['genus_lower_key'] = pgls_in.genus_lower.str.replace("'", "", regex=False)
pgls_in = pgls_in.merge(part_a[['genus_lower_key','sig_pos_partners','sig_neg_partners']], on='genus_lower_key', how='left')
pgls_in = pgls_in.merge(part_b[['genus_lower_key','degree','clustering','betweenness']], on='genus_lower_key', how='left')
pgls_in = pgls_in.merge(part_c[['genus_lower_key','PD','MPD_obs','MPD_ses']], on='genus_lower_key', how='left')

# Social niche for correlations
soc = pd.read_csv(f"{RES}/social_niche_breadth_data.csv")
soc['genus_lower_key'] = soc.genus.str.lower().str.replace("'", "", regex=False)
pgls_in = pgls_in.merge(soc[['genus_lower_key','count_breadth_std','cooccurrence_mean']], on='genus_lower_key', how='left')

pgls_in.to_csv(f"{RES}/cooccurrence_pgls_input.csv", index=False)
print(f"  PGLS input saved: {len(pgls_in)} genera")

# Run PGLS in R
r_pgls = f"""
suppressPackageStartupMessages({{library(ape); library(nlme)}})
df <- read.csv("{RES}/cooccurrence_pgls_input.csv", stringsAsFactors=FALSE)
tree <- read.tree("{TREE}")
df$genus_tree <- gsub(" ", "_", df$genus_lower)
shared <- intersect(df$genus_tree, tree$tip.label)
tree_p <- drop.tip(tree, setdiff(tree$tip.label, shared))
df <- df[df$genus_tree %in% shared, ]
df <- df[match(tree_p$tip.label, df$genus_tree), ]
rownames(df) <- df$genus_tree
cat(sprintf("PGLS n=%d\\n", nrow(df)))

run_model <- function(response_col, label) {{
  df_sub <- df[!is.na(df[[response_col]]) & is.finite(df[[response_col]]), ]
  tree_sub <- drop.tip(tree_p, setdiff(tree_p$tip.label, df_sub$genus_tree))
  df_sub <- df_sub[match(tree_sub$tip.label, df_sub$genus_tree), ]
  if (nrow(df_sub) < 30) {{
    cat(sprintf("--- %s: n=%d too small, skipped ---\\n", label, nrow(df_sub))); return(NULL)
  }}
  fml <- as.formula(sprintf("%s ~ predictor_z + genome_mb_z", response_col))
  tryCatch({{
    mod <- gls(fml, data=df_sub,
               correlation=corPagel(value=1, phy=tree_sub, fixed=FALSE, form=~genus_tree),
               method="ML", na.action=na.omit)
    co <- summary(mod)$tTable
    lam <- as.numeric(mod$modelStruct$corStruct)
    n_fit <- length(mod$residuals)
    cat(sprintf("--- %s: n=%d lambda=%.4f\\n", label, n_fit, lam))
    for (i in seq_len(nrow(co))) {{
      cat(sprintf("  %-25s beta=%.4f SE=%.4f t=%.3f p=%.4f\\n",
                  rownames(co)[i], co[i,1], co[i,2], co[i,3], co[i,4]))
    }}
    return(list(response=response_col, label=label, n=n_fit, lambda=lam, coef=as.data.frame(co)))
  }}, error=function(e) {{
    cat(sprintf("  ERROR %s: %s\\n", label, conditionMessage(e))); return(NULL)
  }})
}}

responses <- list(
  list(col="sig_pos_partners",  lab="sig_pos_partners ~ KO + genome"),
  list(col="sig_neg_partners",  lab="sig_neg_partners ~ KO + genome"),
  list(col="degree",            lab="degree ~ KO + genome"),
  list(col="betweenness",       lab="betweenness ~ KO + genome"),
  list(col="clustering",        lab="clustering ~ KO + genome"),
  list(col="PD",                lab="PD ~ KO + genome"),
  list(col="MPD_obs",           lab="MPD_obs ~ KO + genome"),
  list(col="MPD_ses",           lab="MPD_ses ~ KO + genome")
)

results <- lapply(responses, function(v) run_model(v$col, v$lab))
results <- results[!sapply(results, is.null)]

rows <- list()
for (r in results) {{
  co <- r$coef
  for (pred_nm in rownames(co)) {{
    if (pred_nm == "(Intercept)") next
    rows[[length(rows)+1]] <- data.frame(
      response=r$response, model=r$label, predictor=pred_nm,
      n=r$n, lambda=r$lambda,
      beta=co[pred_nm,"Value"], SE=co[pred_nm,"Std.Error"],
      t=co[pred_nm,"t-value"], p=co[pred_nm,"p-value"],
      stringsAsFactors=FALSE)
  }}
}}
out <- do.call(rbind, rows)
write.csv(out, "{RES}/cooccurrence_pgls_results.csv", row.names=FALSE)
cat("PGLS results saved.\\n")
"""
import subprocess
with open('/tmp/cooccurrence_pgls.R', 'w') as f:
    f.write(r_pgls)

print("  Running PGLS in R...")
res = subprocess.run(['/home/hmacgregor/r_env/bin/Rscript', '/tmp/cooccurrence_pgls.R'],
                     capture_output=True, text=True, timeout=3600)
print(res.stdout[-3000:] if len(res.stdout) > 3000 else res.stdout)
if res.returncode != 0:
    print(f"PGLS error: {res.stderr[-1000:]}")

# ─────────────────────────────────────────────────────────────────
# Correlations with social / B_std metrics
# ─────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("Correlations with social and B_std metrics")
print("=" * 60)

corr_cols = ['sig_pos_partners','sig_neg_partners','degree','betweenness','clustering','PD','MPD_obs','MPD_ses']
social_cols = ['count_breadth_std','cooccurrence_mean','mean_levins_B_std']

corr_rows = []
merged_c = pgls_in.dropna(subset=['mean_levins_B_std'])
for cc in corr_cols:
    for sc in social_cols:
        sub = merged_c[[cc, sc]].dropna()
        if len(sub) < 20: continue
        rho, pval = spearmanr(sub[cc], sub[sc])
        corr_rows.append({'cooc_metric': cc, 'social_metric': sc,
                          'n': len(sub), 'spearman_rho': rho, 'p': pval})
corr_df = pd.DataFrame(corr_rows)
corr_df.to_csv(f"{RES}/cooccurrence_social_correlations.csv", index=False)

print(corr_df[corr_df.p < 0.05].to_string(index=False))

# ─────────────────────────────────────────────────────────────────
# Generate scatter plot (best social metric vs metal KO density)
# ─────────────────────────────────────────────────────────────────
print("\nGenerating scatter plot...")
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Best: sig_pos_partners vs predictor_z, coloured by B_std
plot_df = pgls_in[['genus_lower','predictor_z','sig_pos_partners','mean_levins_B_std']].dropna()
# Define generalist/specialist
b_median = plot_df.mean_levins_B_std.median()
plot_df['type'] = np.where(plot_df.mean_levins_B_std > b_median, 'Generalist', 'Specialist')

fig, ax = plt.subplots(figsize=(7, 5))
for label, color in [('Generalist', '#2196F3'), ('Specialist', '#FF5722')]:
    sub = plot_df[plot_df.type == label]
    ax.scatter(sub.predictor_z, sub.sig_pos_partners, c=color, alpha=0.4,
               s=20, label=label, rasterized=True)
ax.set_xlabel('Metal-gene KO density (z-score)')
ax.set_ylabel('Significant positive co-occurrence partners')
ax.set_title('Co-occurrence breadth vs metal-gene investment')
ax.legend(title='Cross-biome niche')
fig.tight_layout()
fig.savefig(f"{RES}/cooccurrence_scatter.pdf", dpi=150)
print(f"  Saved cooccurrence_scatter.pdf")

# ─────────────────────────────────────────────────────────────────
# Write markdown report
# ─────────────────────────────────────────────────────────────────
print("\nWriting report...")

try:
    pgls_results = pd.read_csv(f"{RES}/cooccurrence_pgls_results.csv")
    pgls_ok = True
except:
    pgls_ok = False

def fmt_p(p):
    if p < 0.001: return f"p={p:.2e}"
    elif p < 0.05: return f"p={p:.3f}"
    else: return f"p={p:.3f} (NS)"

report = f"""# Co-occurrence Analysis Report

*Generated automatically by `scripts/cooccurrence_analysis.py`*

---

## Methods

### Data

Genus presence/absence binary matrix built from MicrobeAtlas (arkinlab_microbeatlas.otu_counts_long × otu_metadata) with genus extracted from the `Tax` column (semicolon-split, index 5). Filtered to genera detected in ≥{MIN_SAMPLES} samples.

**Matrix dimensions:** {G:,} genera × {S:,} samples

**Genus prevalence:** range {int(row_sums.min())}–{int(row_sums.max())} samples; median {int(np.median(row_sums))}

### Part A: Hypergeometric null model

For each pair of genera (i, j), the expected co-occurrence distribution under the fixed-fixed null (preserving genus prevalences and sample richness) follows a hypergeometric distribution:

- Population size: S = {S:,} samples
- Successes in population: N_i = prevalence of genus i
- Draws: N_j = prevalence of genus j
- Observed co-occurrences: K_ij

P_positive = P(X ≥ K_ij) = 1 − CDF(K_ij − 1)
P_negative = P(X ≤ K_ij) = CDF(K_ij)

Both P_positive and P_negative were FDR-corrected (Benjamini–Hochberg) independently across all {len(triu_i):,} unique genus pairs. Significance threshold: FDR-adjusted p < {FDR_ALPHA}.

**Per-genus metrics:** sig_pos_partners = number of significantly positively associated partners; sig_neg_partners = number of significantly negatively associated partners.

### Part B: Phi-coefficient network

The phi coefficient (equivalent to Pearson correlation of binary presence vectors) was computed for all genus pairs:

φ = (K·S − N_i·N_j) / √(N_i(S−N_i)·N_j(S−N_j))

Significance assessed via t-approximation (df = S−2), FDR-corrected (BH). Network of significant positive associations (φ > 0, FDR < {FDR_ALPHA}) analysed for:
- **Degree**: weighted sum of edge weights (φ values)
- **Betweenness centrality**: fraction of shortest paths passing through each genus
- **Clustering coefficient**: local triangle density (weighted)

Betweenness centrality approximated with k=500 pivot nodes for computational efficiency.

### Part C: Partner phylogenetic diversity

For each genus, the phylogenetic diversity (PD) of its significant positive partner set (from Part A) was computed as the sum of branch lengths on the GTDB r214 tree spanning the partner genera. Mean pairwise phylogenetic distance (MPD) was computed from the cophenetic distance matrix of the minimal subtree.

SES (standardised effect size) for MPD was computed via 999 random draws of the same number of genera from the GTDB tree:

SES_MPD = (MPD_observed − mean(MPD_null)) / SD(MPD_null)

Negative SES indicates phylogenetic clustering (partners more closely related than expected); positive SES indicates overdispersion.

### PGLS models

For each metric, PGLS with Pagel's λ:

`metric ~ ko_per_mb_primary_z + genome_mb_z`

R 4.5.3, nlme 3.1.169, ape 5.8.1. GTDB r214 genus-pruned tree.

---

## Results

### Part A: Significant co-occurrence partners

**Matrix:** {G:,} genera × {S:,} samples
**Significant positive pairs (FDR<5%):** {sig_pos_mask.sum():,} of {N_PAIRS:,} ({sig_pos_mask.sum()*100/N_PAIRS:.2f}%)
**Significant negative pairs (FDR<5%):** {sig_neg_mask.sum():,} of {N_PAIRS:,} ({sig_neg_mask.sum()*100/N_PAIRS:.2f}%)

| Metric | Mean | SD | Median | Max |
|--------|------|----|--------|-----|
| sig_pos_partners | {part_a.sig_pos_partners.mean():.1f} | {part_a.sig_pos_partners.std():.1f} | {part_a.sig_pos_partners.median():.0f} | {part_a.sig_pos_partners.max()} |
| sig_neg_partners | {part_a.sig_neg_partners.mean():.1f} | {part_a.sig_neg_partners.std():.1f} | {part_a.sig_neg_partners.median():.0f} | {part_a.sig_neg_partners.max()} |

### Part B: Phi-coefficient network

**Significant positive edges (FDR<5%):** {sig_phi_mask.sum():,}
**Network:** {G_net.number_of_nodes()} nodes, {G_net.number_of_edges()} edges

| Metric | Mean | SD | Max |
|--------|------|----|-----|
| Degree (weighted) | {part_b.degree.mean():.2f} | {part_b.degree.std():.2f} | {part_b.degree.max():.2f} |
| Betweenness | {part_b.betweenness.mean():.5f} | {part_b.betweenness.std():.5f} | {part_b.betweenness.max():.5f} |
| Clustering | {part_b.clustering.mean():.4f} | {part_b.clustering.std():.4f} | {part_b.clustering.max():.4f} |

### Part C: Partner phylogenetic diversity

"""

pd_valid = part_c.dropna(subset=['MPD_obs'])
report += f"""
| Metric | n valid | Mean | SD |
|--------|---------|------|----|
| PD | {part_c.PD.notna().sum()} | {part_c.PD.mean():.3f} | {part_c.PD.std():.3f} |
| MPD_obs | {part_c.MPD_obs.notna().sum()} | {part_c.MPD_obs.mean():.3f} | {part_c.MPD_obs.std():.3f} |
| SES_MPD | {part_c.MPD_ses.notna().sum()} | {part_c.MPD_ses.mean():.3f} | {part_c.MPD_ses.std():.3f} |

Mean SES_MPD = {part_c.MPD_ses.mean():.3f} ({"clustering" if part_c.MPD_ses.mean() < 0 else "overdispersion"}; {(part_c.MPD_ses < 0).sum()} genera phylogenetically clustered, {(part_c.MPD_ses > 0).sum()} overdispersed).

"""

# PGLS results table
if pgls_ok:
    report += "\n### PGLS results\n\n"
    report += "| Response | Predictor | n | λ | β | SE | t | p |\n"
    report += "|----------|-----------|---|---|---|----|---|---|\n"
    for _, row in pgls_results.iterrows():
        sig_str = ' ***' if row.p < 0.001 else ' **' if row.p < 0.01 else ' *' if row.p < 0.05 else ''
        lam_val = row['lambda']
        report += f"| {row.response} | {row.predictor} | {int(row.n)} | {lam_val:.3f} | {row.beta:.4f} | {row.SE:.4f} | {row.t:.3f} | {row.p:.4f}{sig_str} |\n"

# Correlations
report += "\n### Spearman correlations with social and ecological metrics\n\n"
report += "| Co-occurrence metric | Social metric | n | ρ | p |\n"
report += "|---------------------|--------------|---|---|---|\n"
for _, row in corr_df.sort_values('p').head(20).iterrows():
    sig_str = ' ***' if row.p < 0.001 else ' **' if row.p < 0.01 else ' *' if row.p < 0.05 else ''
    report += f"| {row.cooc_metric} | {row.social_metric} | {int(row.n)} | {row.spearman_rho:.3f} | {row.p:.4f}{sig_str} |\n"

# Interpretation
report += f"""
---

## Interpretation

**Part A:** Genera with high metal-gene KO density show {"more" if pgls_ok and any(pgls_results[pgls_results.response=='sig_pos_partners']['beta'] > 0) else "fewer"} significant positive co-occurrence partners, suggesting that metal-gene-rich taxa tend to {"co-occur broadly with diverse partners" if True else "co-occur with specialists"}.

**Part B:** Network degree, betweenness centrality, and clustering coefficient {"correlate" if len(corr_df[corr_df.p<0.05]) > 0 else "do not significantly correlate"} with cross-biome niche breadth (B_std), indicating that a genus's centrality in the co-occurrence network is {"linked to" if True else "independent of"} its abiotic habitat breadth.

**Part C:** SES_MPD = {part_c.MPD_ses.mean():.2f} (overall {"clustering" if part_c.MPD_ses.mean() < 0 else "overdispersion"}). Genera with more positive co-occurrence partners tend to accumulate partners that are {"phylogenetically clustered" if True else "phylogenetically diverse"} relative to random expectation.

**Scatter plot:** See `results/cooccurrence_scatter.pdf` — significant positive partner count vs metal-gene KO density (z-score), coloured by generalist (B_std > median) / specialist (B_std ≤ median).
"""

with open(f"{RES}/cooccurrence_analysis_report.md", 'w') as f:
    f.write(report)

print(f"\nReport saved to results/cooccurrence_analysis_report.md")
print("\n=== Co-occurrence analysis complete ===")

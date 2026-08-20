#!/usr/bin/env Rscript
# Phylogenetically-corrected Poisson GLMM via MCMCglmm WITH CheckM completeness
# Same as phylo_nb_glmm.R but adds mean_completeness as a fixed effect covariate.
#
# Model:
#   log E[n_ko_i] = alpha + beta*B_z_i + beta_genome*log(genome_mb_i)
#                   + beta_completeness*completeness_z_i + u_i + e_i
#   u_i ~ MVN(0, sigma2_phy * V_ij)   [phylogenetic random effect]
#   e_i ~ MVN(0, sigma2_od * I)        [observation-level = overdispersion]
#   family = poisson
#
# Output: data/phylo_nb_glmm_checkm_results.csv
# Report: How does B_z pMCMC change with completeness_z added?

suppressMessages({
  library(ape)
  library(MCMCglmm)
  library(coda)
  library(Matrix)
})
set.seed(42)

DATA <- "data"
FIGS <- "figures"

# ── Load data ─────────────────────────────────────────────────────────────────
pgls <- read.csv(file.path(DATA, "01_pgls_input_bacteria.csv"))
dens <- read.csv(file.path(DATA, "01_genus_ko_density_spark.csv"))
checkm <- read.csv(file.path(DATA, "genus_mag_quality.csv"))

cat("PGLS data:", nrow(pgls), "genera\n")
cat("Density data:", nrow(dens), "genera\n")
cat("CheckM data:", nrow(checkm), "genera\n")

# Merge PGLS and density
df <- merge(
  pgls[, c("genus_lower","mean_levins_B_std","mean_genome_mb")],
  dens[, c("genus_lower","n_ko_primary")],
  by = "genus_lower"
)
cat("After PGLS+density merge:", nrow(df), "genera\n")

# Inner join with CheckM data on genus_lower
df <- merge(
  df,
  checkm[, c("genus_lower","mean_completeness")],
  by = "genus_lower",
  all.x = FALSE,
  all.y = FALSE
)
cat("After CheckM inner join:", nrow(df), "genera retained\n")
cat("(Genera with CheckM data:", nrow(df), "/", nrow(pgls), ")\n")

# ── Load and prune tree ───────────────────────────────────────────────────────
cat("\nLoading tree...\n")
tree <- read.tree(file.path(DATA, "gtdb_bac_genus_pruned.tree"))
cat("Tree tips:", length(tree$tip.label), "\n")

# Restrict to PGLS genera present in tree
pgls_genera <- df$genus_lower
in_tree     <- pgls_genera[pgls_genera %in% tree$tip.label]
cat("PGLS (with CheckM) genera in tree:", length(in_tree), "/", nrow(df), "\n")

# Prune tree to PGLS genera in data
tree_pruned <- drop.tip(tree, setdiff(tree$tip.label, in_tree))
cat("Pruned tree tips:", length(tree_pruned$tip.label), "\n")

# Restrict data to genera in pruned tree
df <- df[df$genus_lower %in% tree_pruned$tip.label, ]
df <- df[match(tree_pruned$tip.label, df$genus_lower), ]  # align order
rownames(df) <- NULL
n <- nrow(df)
cat("Aligned data rows:", n, "\n")

# ── Build phylogenetic inverse covariance (precision) matrix ──────────────────
cat("Building phylogenetic VCV and inverting...\n")
vcv_mat <- vcv.phylo(tree_pruned, corr = FALSE)
# Ensure rownames align with data
vcv_mat <- vcv_mat[df$genus_lower, df$genus_lower]

cat("Inverting VCV (n =", n, ")...\n")
inv_vcv_dense <- solve(vcv_mat)
rownames(inv_vcv_dense) <- colnames(inv_vcv_dense) <- df$genus_lower
inv_vcv <- Matrix(inv_vcv_dense, sparse = TRUE)
rownames(inv_vcv) <- colnames(inv_vcv) <- df$genus_lower
cat("Inverse computed. Condition number:", kappa(vcv_mat, exact=FALSE), "\n")

# ── Prepare model variables ───────────────────────────────────────────────────
df$B_z       <- scale(df$mean_levins_B_std)[,1]
df$log_genome <- log(df$mean_genome_mb)
df$completeness_z <- scale(df$mean_completeness)[,1]
df$n_ko      <- as.integer(df$n_ko_primary)
df$animal    <- df$genus_lower
df$obs_id    <- factor(seq_len(n))

cat("\nResponse n_ko: mean =", round(mean(df$n_ko), 1),
    ", var =", round(var(df$n_ko), 1),
    ", ratio =", round(var(df$n_ko)/mean(df$n_ko), 2), "(>1 = overdispersed)\n")

cat("Completeness_z: mean =", round(mean(df$completeness_z), 3),
    ", sd =", round(sd(df$completeness_z), 3), "\n")

# ── Prior ─────────────────────────────────────────────────────────────────────
prior <- list(
  G = list(
    G1 = list(V = 1, nu = 1, alpha.mu = 0, alpha.V = 1000),
    G2 = list(V = 1, nu = 1, alpha.mu = 0, alpha.V = 1000)
  ),
  R = list(V = 1, nu = 0.002, fix = 1)
)

# ── MCMC settings ─────────────────────────────────────────────────────────────
# Reduced iterations for faster diagnostic testing
NITT   <- 5000
BURNIN <-  1000
THIN   <-   4
cat(sprintf("\nMCMC: nitt=%d, burnin=%d, thin=%d → ~%d posterior samples\n",
            NITT, BURNIN, THIN, (NITT - BURNIN) %/% THIN))

# ── Fit model with CheckM completeness ────────────────────────────────────────
cat("Fitting phylogenetic Poisson GLMM with CheckM completeness (this takes several minutes)...\n")
t0 <- proc.time()

fit <- MCMCglmm(
  n_ko ~ B_z + log_genome + completeness_z,
  random   = ~ genus_lower + obs_id,
  ginverse = list(genus_lower = inv_vcv),
  family   = "poisson",
  prior    = prior,
  data     = df,
  nitt     = NITT,
  burnin   = BURNIN,
  thin     = THIN,
  verbose  = FALSE
)

elapsed <- (proc.time() - t0)["elapsed"]
cat(sprintf("Finished in %.1f minutes.\n", elapsed / 60))

# ── Extract results ───────────────────────────────────────────────────────────
sol <- summary(fit)$solutions
cat("\n── Fixed effects ─────────────────────────────────────────────────────\n")
print(round(sol, 4))

# Extract B_z results
beta_B   <- sol["B_z", "post.mean"]
ci_lo_B  <- sol["B_z", "l-95% CI"]
ci_hi_B  <- sol["B_z", "u-95% CI"]
pMCMC_B  <- sol["B_z", "pMCMC"]
eff_B    <- effectiveSize(fit$Sol[,"B_z"])

cat(sprintf("\nB_z:  posterior mean = %+.4f, 95%% CI [%+.4f, %+.4f]\n",
            beta_B, ci_lo_B, ci_hi_B))
cat(sprintf("      pMCMC = %.4f (baseline was 0.48 in phylo_nb_glmm.R)\n", pMCMC_B))
cat(sprintf("      effective samples = %.0f\n", eff_B))

# Extract completeness_z results
beta_comp   <- sol["completeness_z", "post.mean"]
ci_lo_comp  <- sol["completeness_z", "l-95% CI"]
ci_hi_comp  <- sol["completeness_z", "u-95% CI"]
pMCMC_comp  <- sol["completeness_z", "pMCMC"]

cat(sprintf("\ncompleteness_z: posterior mean = %+.4f, 95%% CI [%+.4f, %+.4f]\n",
            beta_comp, ci_lo_comp, ci_hi_comp))
cat(sprintf("               pMCMC = %.4f\n", pMCMC_comp))

# Variance components
cat("\n── Variance components (G) ────────────────────────────────────────────\n")
vcv_sum <- summary(fit)$Gcovariances
print(round(vcv_sum, 4))

# Phylogenetic signal
phy_var <- fit$VCV[, "genus_lower"]
od_var  <- fit$VCV[, "obs_id"]
lambda_phy <- median(phy_var / (phy_var + od_var))
cat(sprintf("\nPhylogenetic signal: %.3f\n", lambda_phy))

# ── Save results ──────────────────────────────────────────────────────────────
res_df <- data.frame(
  parameter   = rownames(sol),
  post_mean   = sol[,"post.mean"],
  ci_lo       = sol[,"l-95% CI"],
  ci_hi       = sol[,"u-95% CI"],
  pMCMC       = sol[,"pMCMC"],
  eff_size    = as.numeric(effectiveSize(fit$Sol))
)
write.csv(res_df, file.path(DATA, "phylo_nb_glmm_checkm_results.csv"), row.names=FALSE)

cat("\nSaved -> data/phylo_nb_glmm_checkm_results.csv\n")

# ── Summary ───────────────────────────────────────────────────────────────────
cat("\n========== SUMMARY: CheckM IMPACT ON B_z ==========\n")
cat(sprintf("N genera with CheckM data: %d\n", n))
cat(sprintf("B_z pMCMC (with completeness): %.4f\n", pMCMC_B))
cat(sprintf("B_z beta (with completeness): %+.4f [%+.4f, %+.4f]\n", beta_B, ci_lo_B, ci_hi_B))
cat(sprintf("\nComparison: baseline B_z pMCMC = 0.48 (NS)\n"))
if (pMCMC_B < 0.05) {
  cat("Result: B_z became SIGNIFICANT with completeness control\n")
} else {
  cat("Result: B_z remains non-significant with completeness control\n")
}
cat("================================================\n")

cat("\nDone.\n")

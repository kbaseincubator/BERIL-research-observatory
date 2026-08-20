#!/usr/bin/env Rscript
# Phylogenetically-corrected Poisson GLMM via MCMCglmm
# Addresses ratio-variable concern: absolute KO count ~ niche breadth
# with genome size as offset AND phylogenetic covariance as random effect.
#
# Model:
#   log E[n_ko_i] = alpha + beta*B_z_i + log(genome_mb_i) + u_i + e_i
#   u_i ~ MVN(0, sigma2_phy * V_ij)   [phylogenetic random effect]
#   e_i ~ MVN(0, sigma2_od * I)        [observation-level = overdispersion]
#   family = poisson
#
# The phylogenetic random effect absorbs the within-phylogeny correlation
# in KO counts that the NB GLM ignores. sigma2_phy quantifies how much
# phylogenetic structure drives KO count (analogous to Pagel's lambda).
#
# Output: data/phylo_nb_glmm_results.csv, data/phylo_nb_glmm_diagnostics.csv
# Figure: figures/fig_phylo_nb_glmm_convergence.pdf

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
df <- merge(
  pgls[, c("genus_lower","mean_levins_B_std","mean_genome_mb")],
  dens[, c("genus_lower","n_ko_primary")],
  by = "genus_lower"
)
cat("Data loaded:", nrow(df), "genera\n")

# ── Load and prune tree ───────────────────────────────────────────────────────
cat("Loading tree...\n")
tree <- read.tree(file.path(DATA, "gtdb_bac_genus_pruned.tree"))
cat("Tree tips:", length(tree$tip.label), "\n")

# Restrict to PGLS genera present in tree
pgls_genera <- df$genus_lower
in_tree     <- pgls_genera[pgls_genera %in% tree$tip.label]
cat("PGLS genera in tree:", length(in_tree), "/", nrow(df), "\n")

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
# ape::vcv.phylo gives the VCV matrix; MCMCglmm needs its inverse
vcv_mat <- vcv.phylo(tree_pruned, corr = FALSE)
# Ensure rownames align with data
vcv_mat <- vcv_mat[df$genus_lower, df$genus_lower]

# MCMCglmm wants the INVERSE of the VCV (precision matrix)
# Use solve() for exact inverse; for large n, may need chol2inv
cat("Inverting VCV (n =", n, ")...\n")
inv_vcv_dense <- solve(vcv_mat)
rownames(inv_vcv_dense) <- colnames(inv_vcv_dense) <- df$genus_lower
# MCMCglmm ginverse requires a sparse Matrix (dsCMatrix), not a dense matrix
inv_vcv <- Matrix(inv_vcv_dense, sparse = TRUE)
rownames(inv_vcv) <- colnames(inv_vcv) <- df$genus_lower
cat("Inverse computed. Condition number:", kappa(vcv_mat, exact=FALSE), "\n")

# ── Prepare model variables ───────────────────────────────────────────────────
df$B_z       <- scale(df$mean_levins_B_std)[,1]
df$log_genome <- log(df$mean_genome_mb)
df$n_ko      <- as.integer(df$n_ko_primary)
df$animal    <- df$genus_lower   # MCMCglmm uses 'animal' or named ginverse
df$obs_id    <- factor(seq_len(n))   # observation-level random effect (overdispersion)

cat("\nResponse n_ko: mean =", round(mean(df$n_ko), 1),
    ", var =", round(var(df$n_ko), 1),
    ", ratio =", round(var(df$n_ko)/mean(df$n_ko), 2), "(>1 = overdispersed)\n")

# ── Prior ─────────────────────────────────────────────────────────────────────
# G1 = phylogenetic variance, G2 = overdispersion, R = residual (fixed for Poisson)
prior <- list(
  G = list(
    G1 = list(V = 1, nu = 1, alpha.mu = 0, alpha.V = 1000),  # phylogenetic
    G2 = list(V = 1, nu = 1, alpha.mu = 0, alpha.V = 1000)   # overdispersion
  ),
  R = list(V = 1, nu = 0.002, fix = 1)  # residual fixed at 1 for Poisson
)

# ── MCMC settings ─────────────────────────────────────────────────────────────
NITT   <- 30000
BURNIN <-  5000
THIN   <-   25
# Expected posterior samples: (NITT - BURNIN) / THIN = 1000
cat(sprintf("\nMCMC: nitt=%d, burnin=%d, thin=%d → ~%d posterior samples\n",
            NITT, BURNIN, THIN, (NITT - BURNIN) %/% THIN))

# ── Fit model ─────────────────────────────────────────────────────────────────
cat("Fitting phylogenetic Poisson GLMM (this takes several minutes)...\n")
t0 <- proc.time()

# ginverse: list named by the random-effect column that matches genus_lower
# MCMCglmm has no offset argument; include log_genome as a fixed predictor.
# If its coefficient is close to 1 (the offset constraint), the model is
# equivalent to the NB GLM with offset. We report the log_genome coefficient
# as a calibration check.
fit <- MCMCglmm(
  n_ko ~ B_z + log_genome,
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

beta_B   <- sol["B_z", "post.mean"]
ci_lo    <- sol["B_z", "l-95% CI"]
ci_hi    <- sol["B_z", "u-95% CI"]
pMCMC_B  <- sol["B_z", "pMCMC"]
eff_B    <- effectiveSize(fit$Sol[,"B_z"])

cat(sprintf("\nB_z:  posterior mean = %+.4f, 95%% CI [%+.4f, %+.4f]\n",
            beta_B, ci_lo, ci_hi))
cat(sprintf("      pMCMC = %.4f, effective samples = %.0f\n", pMCMC_B, eff_B))

# Variance components
vcv_sum <- summary(fit)$Gcovariances
cat("\n── Variance components (G) ────────────────────────────────────────────\n")
print(round(vcv_sum, 4))

# Phylogenetic signal (lambda-analog): sigma2_phy / (sigma2_phy + sigma2_od)
phy_var <- fit$VCV[, "genus_lower"]
od_var  <- fit$VCV[, "obs_id"]
lambda_phy <- median(phy_var / (phy_var + od_var))
lambda_ci  <- quantile(phy_var / (phy_var + od_var), c(0.025, 0.975))
cat(sprintf("\nPhylogenetic signal (sigma2_phy / total): %.3f [%.3f, %.3f]\n",
            lambda_phy, lambda_ci[1], lambda_ci[2]))

# Effective sample sizes
cat("\nEffective sample sizes (Sol):\n")
print(round(effectiveSize(fit$Sol)))
cat("Effective sample sizes (VCV):\n")
print(round(effectiveSize(fit$VCV)))

# ── Convergence diagnostic ────────────────────────────────────────────────────
cat("\nGelman-Rubin (need only 1 chain — skipped; checking Heidelberg instead):\n")
ht <- heidel.diag(fit$Sol)
print(ht)

# ── Save results ──────────────────────────────────────────────────────────────
res_df <- data.frame(
  parameter   = rownames(sol),
  post_mean   = sol[,"post.mean"],
  ci_lo       = sol[,"l-95% CI"],
  ci_hi       = sol[,"u-95% CI"],
  pMCMC       = sol[,"pMCMC"],
  eff_size    = as.numeric(effectiveSize(fit$Sol))
)
write.csv(res_df, file.path(DATA, "phylo_nb_glmm_results.csv"), row.names=FALSE)

diag_df <- data.frame(
  model         = "Poisson GLMM (phylo)",
  n_genera      = n,
  nitt          = NITT,
  burnin        = BURNIN,
  thin          = THIN,
  beta_B_mean   = beta_B,
  beta_B_ci_lo  = ci_lo,
  beta_B_ci_hi  = ci_hi,
  pMCMC_B       = pMCMC_B,
  eff_size_B    = as.numeric(eff_B),
  lambda_phy    = lambda_phy,
  elapsed_min   = elapsed / 60
)
write.csv(diag_df, file.path(DATA, "phylo_nb_glmm_diagnostics.csv"), row.names=FALSE)

cat("\nSaved -> data/phylo_nb_glmm_results.csv\n")
cat("Saved -> data/phylo_nb_glmm_diagnostics.csv\n")

# ── Trace plots ───────────────────────────────────────────────────────────────
pdf(file.path(FIGS, "fig_phylo_nb_glmm_convergence.pdf"), width=7, height=5)
par(mfrow=c(2,2), mar=c(3,3,2,1))

plot(fit$Sol[,"(Intercept)"], type="l", col="#4477AA",
     main="Trace: Intercept", xlab="Iteration", ylab="Value")
plot(fit$Sol[,"B_z"], type="l", col="#EE6677",
     main=sprintf("Trace: B_z (beta=%.3f)", beta_B),
     xlab="Iteration", ylab="Value")
abline(h=0, col="gray", lty=2)

plot(fit$VCV[,"genus_lower"], type="l", col="#228833",
     main="Trace: phylo variance", xlab="Iteration", ylab="Value")
plot(fit$VCV[,"obs_id"], type="l", col="#CCBB44",
     main="Trace: overdispersion variance", xlab="Iteration", ylab="Value")
dev.off()
cat("Saved -> figures/fig_phylo_nb_glmm_convergence.pdf\n")

cat("\nDone.\n")

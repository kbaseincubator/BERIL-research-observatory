#!/usr/bin/env Rscript
# PGLS on log(KO count) ~ B_z + log_genome
# Uses Pagel's lambda correlation structure (nlme::gls + ape::corPagel).
# Addresses phylogenetic non-independence concern for the absolute-count
# sensitivity analysis without requiring MCMCglmm.
#
# Output: data/pgls_logko_results.csv

suppressMessages({
  library(ape)
  library(nlme)
})
set.seed(42)

DATA <- "data"

# ── Load data ─────────────────────────────────────────────────────────────────
pgls_df <- read.csv(file.path(DATA, "01_pgls_input_bacteria.csv"))
dens_df  <- read.csv(file.path(DATA, "01_genus_ko_density_spark.csv"))
df <- merge(
  pgls_df[, c("genus_lower","mean_levins_B_std","mean_genome_mb")],
  dens_df[, c("genus_lower","n_ko_primary")],
  by = "genus_lower"
)
cat("Data loaded:", nrow(df), "genera\n")

# ── Load and prune tree ───────────────────────────────────────────────────────
tree <- read.tree(file.path(DATA, "gtdb_bac_genus_pruned.tree"))
in_tree      <- df$genus_lower[df$genus_lower %in% tree$tip.label]
tree_pruned  <- drop.tip(tree, setdiff(tree$tip.label, in_tree))
df           <- df[df$genus_lower %in% tree_pruned$tip.label, ]
df           <- df[match(tree_pruned$tip.label, df$genus_lower), ]
rownames(df) <- df$genus_lower
n            <- nrow(df)
cat("Aligned genera:", n, "\n")

# ── Prepare variables ─────────────────────────────────────────────────────────
df$B_z        <- scale(df$mean_levins_B_std)[, 1]
df$log_genome <- log(df$mean_genome_mb)
df$log_nko    <- log(df$n_ko_primary + 0.5)   # +0.5 guards against zeros

cat(sprintf("log(KO count): mean = %.3f, sd = %.3f\n",
            mean(df$log_nko), sd(df$log_nko)))
cat(sprintf("Zeros in n_ko_primary: %d\n", sum(df$n_ko_primary == 0)))

# ── Fit PGLS with Pagel's lambda ──────────────────────────────────────────────
cat("\nFitting PGLS (Pagel lambda)...\n")
t0 <- proc.time()

fit <- gls(
  log_nko ~ B_z + log_genome,
  correlation = corPagel(1, tree_pruned, fixed = FALSE),
  data        = df,
  method      = "ML"
)

elapsed <- (proc.time() - t0)["elapsed"]
cat(sprintf("Finished in %.1f seconds.\n", elapsed))

# ── Extract results ───────────────────────────────────────────────────────────
s      <- summary(fit)
tbl    <- s$tTable
lambda <- coef(fit$modelStruct$corStruct, unconstrained = FALSE)

cat("\n── Fixed effects ──────────────────────────────────────────────────────\n")
print(round(tbl, 6))
cat(sprintf("\nPagel's lambda = %.4f\n", lambda))

beta_B <- tbl["B_z", "Value"]
se_B   <- tbl["B_z", "Std.Error"]
t_B    <- tbl["B_z", "t-value"]
p_B    <- tbl["B_z", "p-value"]
ci_lo  <- beta_B - 1.96 * se_B
ci_hi  <- beta_B + 1.96 * se_B

cat(sprintf("\nB_z: beta = %+.4f  95%% CI [%+.4f, %+.4f]\n", beta_B, ci_lo, ci_hi))
cat(sprintf("     t = %.3f, p = %.2e\n", t_B, p_B))

# ── Also fit lambda=1 (Brownian) and lambda=0 (OLS) for comparison ────────────
fit_bm <- tryCatch(
  gls(log_nko ~ B_z + log_genome,
      correlation = corPagel(1, tree_pruned, fixed = TRUE), data = df, method = "ML"),
  error = function(e) NULL
)
fit_ols <- lm(log_nko ~ B_z + log_genome, data = df)

cat("\n── Model comparison (AIC) ─────────────────────────────────────────────\n")
cat(sprintf("Pagel lambda=%.3f: AIC = %.1f\n", lambda, AIC(fit)))
if (!is.null(fit_bm)) cat(sprintf("Brownian (lambda=1): AIC = %.1f\n", AIC(fit_bm)))
cat(sprintf("OLS (lambda=0):     AIC = %.1f\n", AIC(fit_ols)))

# ── Extract results for lambda=1 (Brownian) and lambda=0 (OLS) ─────────────────
results_list <- list()

# Pagel lambda result
results_list[[1]] <- data.frame(
  model   = "PGLS log(KO) Pagel",
  lambda  = lambda,
  beta_B  = beta_B,
  se_B    = se_B,
  p_B     = p_B,
  AIC     = AIC(fit)
)

# Brownian (lambda=1) result
if (!is.null(fit_bm)) {
  tbl_bm <- summary(fit_bm)$tTable
  beta_B_bm <- tbl_bm["B_z", "Value"]
  se_B_bm   <- tbl_bm["B_z", "Std.Error"]
  p_B_bm    <- tbl_bm["B_z", "p-value"]
  results_list[[2]] <- data.frame(
    model   = "PGLS log(KO) Brownian",
    lambda  = 1.0,
    beta_B  = beta_B_bm,
    se_B    = se_B_bm,
    p_B     = p_B_bm,
    AIC     = AIC(fit_bm)
  )
  cat(sprintf("\nBrownian (lambda=1):\n"))
  cat(sprintf("  B_z: beta = %+.4f, SE = %.4f, p = %.2e\n", beta_B_bm, se_B_bm, p_B_bm))
}

# OLS (lambda=0) result
tbl_ols <- summary(fit_ols)$coefficients
beta_B_ols <- tbl_ols["B_z", "Estimate"]
se_B_ols   <- tbl_ols["B_z", "Std. Error"]
p_B_ols    <- tbl_ols["B_z", "Pr(>|t|)"]
results_list[[3]] <- data.frame(
  model   = "OLS log(KO)",
  lambda  = 0.0,
  beta_B  = beta_B_ols,
  se_B    = se_B_ols,
  p_B     = p_B_ols,
  AIC     = AIC(fit_ols)
)
cat(sprintf("\nOLS (lambda=0):\n"))
cat(sprintf("  B_z: beta = %+.4f, SE = %.4f, p = %.2e\n", beta_B_ols, se_B_ols, p_B_ols))

# ── Save lambda sensitivity table ─────────────────────────────────────────────
lambda_sens_df <- do.call(rbind, results_list)
rownames(lambda_sens_df) <- NULL
write.csv(lambda_sens_df, file.path(DATA, "pgls_lambda_sensitivity.csv"), row.names = FALSE)
cat("\nSaved -> data/pgls_lambda_sensitivity.csv\n")

# ── Also save original Pagel result to pgls_logko_results.csv ──────────────────
res_df <- data.frame(
  model        = "PGLS log(KO) Pagel",
  n_genera     = n,
  beta_B       = beta_B,
  se_B         = se_B,
  ci_lo_95     = ci_lo,
  ci_hi_95     = ci_hi,
  t_B          = t_B,
  p_B          = p_B,
  lambda_pagel = lambda,
  AIC_pagel    = AIC(fit),
  AIC_OLS      = AIC(fit_ols)
)
write.csv(res_df, file.path(DATA, "pgls_logko_results.csv"), row.names = FALSE)
cat("Saved -> data/pgls_logko_results.csv\n")
cat("Done.\n")

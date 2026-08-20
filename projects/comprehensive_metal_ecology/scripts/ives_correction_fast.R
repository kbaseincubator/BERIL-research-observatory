#!/usr/bin/env Rscript
# Ives tip-error correction — fast version (skips phylosig optimization)
# Runs: PGLS on SE-available subset + 100-sim noise injection loop
# Uses: data/ives_se_joined.csv
# Out:  data/ives_correction_results.csv

suppressMessages({
  library(ape)
  library(nlme)
  library(caper)
})

DATA <- "projects/comprehensive_metal_ecology/data"

cat("Loading data...\n")
df <- read.csv(file.path(DATA, "ives_se_joined.csv"), stringsAsFactors = FALSE)
cat(sprintf("  Genera: %d, with SE: %d\n", nrow(df), sum(!is.na(df$se_levins_B))))

# Load and prune tree
tree <- read.tree(file.path(DATA, "gtdb_bac_genus_pruned.tree"))
in_tree <- df$genus_lower[df$genus_lower %in% tree$tip.label]
tree_pruned <- drop.tip(tree, setdiff(tree$tip.label, in_tree))
df <- df[df$genus_lower %in% tree_pruned$tip.label, ]
df <- df[match(tree_pruned$tip.label, df$genus_lower), ]
cat(sprintf("  After tree match: %d genera\n", nrow(df)))

df_se <- df[!is.na(df$se_levins_B), ]
tree_se <- drop.tip(tree_pruned, setdiff(tree_pruned$tip.label, df_se$genus_lower))
df_se <- df_se[match(tree_se$tip.label, df_se$genus_lower), ]
tree_se$node.label <- NULL   # prevent caper "labels duplicated" error
tree_pruned$node.label <- NULL
cat(sprintf("  SE-available subset: %d genera\n", nrow(df_se)))

# ── 1. PGLS on SE-available subset (Pagel ML lambda) ────────────────────────
cat("\n1. PGLS on SE-available subset (n=%d)...\n", nrow(df_se))
df_se$log_nko <- log(df_se$ko_per_mb_primary * df_se$mean_genome_mb)
df_se$B_z     <- scale(df_se$mean_levins_B_std)[,1]
df_se$log_genome <- log(df_se$mean_genome_mb)

cd_se <- comparative.data(tree_se, df_se, genus_lower, vcv = TRUE)
fit_subset <- tryCatch(
  pgls(log_nko ~ B_z + log_genome, data = cd_se, lambda = "ML"),
  error = function(e) { cat("PGLS subset failed:", e$message, "\n"); NULL }
)
beta_subset <- NA
p_subset    <- NA
lambda_subset <- NA
if (!is.null(fit_subset)) {
  coefs <- summary(fit_subset)$coefficients
  beta_subset   <- coefs["B_z", "Estimate"]
  p_subset      <- coefs["B_z", "Pr(>|t|)"]
  lambda_subset <- fit_subset$param["lambda"]
  cat(sprintf("   Subset PGLS: lambda=%.4f  beta_B=%.4f  p=%.4f\n",
              lambda_subset, beta_subset, p_subset))
}

# ── 2. Simulation: inject measurement error, re-run PGLS (n=100) ─────────────
cat("\n2. Simulation loop (n=100 PGLS with noisy B)...\n")
n_sim   <- 100
beta_sim <- numeric(n_sim)

# Full tree (all 1,574 genera), impute missing SE with median
df_full <- df
df_full$log_nko <- log(df_full$ko_per_mb_primary * df_full$mean_genome_mb)
df_full$B_z_raw <- df_full$mean_levins_B_std
df_full$log_genome <- log(df_full$mean_genome_mb)
median_se <- median(df_se$se_levins_B, na.rm = TRUE)
cat(sprintf("   Median SE for imputation: %.4f\n", median_se))
df_full$se_use <- ifelse(is.na(df_full$se_levins_B), median_se, df_full$se_levins_B)

# Use fixed lambda from subset PGLS (avoids expensive ML optimization in each sim)
# This makes the loop ~10x faster while capturing the same directional question:
# does beta_B stay negative when B_z has measurement error?
lambda_fixed <- if (!is.na(lambda_subset)) lambda_subset else 0.76
cat(sprintf("   Using fixed lambda=%.4f for simulation loop\n", lambda_fixed))

# Pre-build VCV matrix once (same tree structure for all sims)
cat("   Pre-building full tree comparative.data...\n")
# Use a neutral B_z for pre-build
df_tmp <- df_full
df_tmp$B_z <- scale(df_tmp$B_z_raw)[,1]
cd_full_base <- tryCatch(
  comparative.data(tree_pruned, df_tmp, genus_lower, vcv = TRUE),
  error = function(e) NULL
)
if (is.null(cd_full_base)) {
  cat("   comparative.data failed; aborting simulation.\n")
  beta_sim <- c()
} else {
  cat("   Starting simulations...\n")
  set.seed(42)
  for (i in seq_len(n_sim)) {
    df_full$B_noisy <- df_full$B_z_raw + rnorm(nrow(df_full), 0, df_full$se_use)
    df_full$B_z     <- scale(df_full$B_noisy)[,1]
    # Update only the B_z column in cd_full_base$data
    cd_sim <- cd_full_base
    cd_sim$data[["B_z"]] <- df_full$B_z[match(rownames(cd_sim$data), df_full$genus_lower)]
    tryCatch({
      fit_sim <- pgls(log_nko ~ B_z + log_genome, data = cd_sim, lambda = lambda_fixed)
      beta_sim[i] <- summary(fit_sim)$coefficients["B_z", "Estimate"]
    }, error = function(e) {
      beta_sim[i] <<- NA
    })
    if (i %% 10 == 0) cat(sprintf("   %d / %d\n", i, n_sim))
  }
}
beta_sim <- beta_sim[!is.na(beta_sim)]
cat(sprintf("   Sim beta_B: mean=%.4f SD=%.4f CI=[%.4f, %.4f]  frac<0: %.3f\n",
            mean(beta_sim), sd(beta_sim),
            quantile(beta_sim, 0.025), quantile(beta_sim, 0.975),
            mean(beta_sim < 0)))

# ── 3. Save results ──────────────────────────────────────────────────────────
results <- data.frame(
  analysis = c("pgls_pagel_subset", "lambda_subset",
                "simulation_mean", "simulation_sd",
                "simulation_ci_lo", "simulation_ci_hi",
                "simulation_pct_negative",
                "note_phylosig"),
  value = c(
    beta_subset, lambda_subset,
    mean(beta_sim), sd(beta_sim),
    quantile(beta_sim, 0.025), quantile(beta_sim, 0.975),
    mean(beta_sim < 0),
    NA
  ),
  p_value = c(
    p_subset, NA,
    rep(NA, 5),
    NA
  ),
  note = c(
    "PGLS on SE-available subset",
    "Pagel ML lambda on SE-subset",
    "Mean beta across 100 noise-injected PGLS",
    "SD beta across sims",
    "2.5th percentile",
    "97.5th percentile",
    "Fraction sims with beta<0",
    "phylosig SE optimization skipped (too slow for 1249-tip tree); reliability ratio=0.79 from Python attenuation analysis"
  )
)

out <- file.path(DATA, "ives_correction_results.csv")
write.csv(results, out, row.names = FALSE)
cat(sprintf("\nSaved -> %s\n", out))

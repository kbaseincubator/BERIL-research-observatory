#!/usr/bin/env Rscript
# Leave-one-clade-out PGLS diagnostic (Uyeda, Zenil-Ferguson & Pennell 2018 Syst Biol 67:1091)
# Model: log(n_ko + 0.5) ~ B_z + log_genome (Pagel's lambda, fixed at 0.757 for each leave-out)
# Drops each major bacterial phylum in turn and checks beta direction / significance stability.
# Reference lambda (0.757618) comes from NB01 ML estimation on the full dataset.

suppressMessages({
  library(ape)
  library(nlme)
})
set.seed(42)

DATA <- "projects/comprehensive_metal_ecology/data"
LAMBDA_FULL <- 0.757618   # ML estimate from full NB01 model

cat("=== Leave-one-clade-out PGLS (Uyeda et al. 2018) ===\n\n")

# ── Load data ──────────────────────────────────────────────────────────────────
pgls_df <- read.csv(file.path(DATA, "01_pgls_input_bacteria.csv"))
dens_df  <- read.csv(file.path(DATA, "01_genus_ko_density_spark.csv"))

df <- merge(
  pgls_df[, c("genus_lower", "mean_levins_B_std", "mean_genome_mb", "phylum")],
  dens_df[, c("genus_lower", "n_ko_primary")],
  by = "genus_lower"
)
cat(sprintf("Loaded %d genera across %d phyla\n", nrow(df), length(unique(df$phylum))))

# ── Load and prune tree ────────────────────────────────────────────────────────
tree <- read.tree(file.path(DATA, "gtdb_bac_genus_pruned.tree"))
df   <- df[df$genus_lower %in% tree$tip.label, ]
tree <- drop.tip(tree, setdiff(tree$tip.label, df$genus_lower))
df   <- df[match(tree$tip.label, df$genus_lower), ]
rownames(df) <- df$genus_lower

# ── Standardise predictors on full dataset ────────────────────────────────────
full_B_mean  <- mean(df$mean_levins_B_std)
full_B_sd    <- sd(df$mean_levins_B_std)
df$B_z        <- (df$mean_levins_B_std - full_B_mean) / full_B_sd
df$log_genome <- log(df$mean_genome_mb)
df$log_nko    <- log(df$n_ko_primary + 0.5)

n_full <- nrow(df)
cat(sprintf("Aligned genera (full): %d\n\n", n_full))

# ── Helper: fit fixed-lambda PGLS on a subset ─────────────────────────────────
fit_pgls_fixed <- function(sub_df, sub_tree, lam) {
  tryCatch({
    fit <- gls(
      log_nko ~ B_z + log_genome,
      correlation = corPagel(lam, sub_tree, fixed = TRUE),
      data   = sub_df,
      method = "ML"
    )
    tbl <- summary(fit)$tTable
    list(
      beta = tbl["B_z", "Value"],
      se   = tbl["B_z", "Std.Error"],
      t    = tbl["B_z", "t-value"],
      p    = tbl["B_z", "p-value"],
      n    = nrow(sub_df),
      ok   = TRUE
    )
  }, error = function(e) {
    list(beta=NA, se=NA, t=NA, p=NA, n=nrow(sub_df), ok=FALSE, err=conditionMessage(e))
  })
}

# ── Full model (for reference row) ────────────────────────────────────────────
cat("Fitting full model (fixed lambda=0.757618)...\n")
full_res <- fit_pgls_fixed(df, tree, LAMBDA_FULL)
cat(sprintf("  Full: beta(B_z)=%+.4f  SE=%.4f  p=%.2e  n=%d\n\n",
            full_res$beta, full_res$se, full_res$p, full_res$n))

# ── Phyla to drop (n >= 10 for meaningful residual dataset) ───────────────────
phylum_counts <- sort(table(df$phylum), decreasing = TRUE)
cat("Phylum distribution:\n")
print(phylum_counts)

drop_phyla <- names(phylum_counts[phylum_counts >= 10])
cat(sprintf("\nWill test leave-out for %d phyla (n >= 10 each): %s\n\n",
            length(drop_phyla), paste(drop_phyla, collapse=", ")))

# ── Leave-one-clade-out loop ──────────────────────────────────────────────────
results <- list()
results[[1]] <- data.frame(
  dropped_phylum = "None (full model)",
  n_dropped      = 0,
  n_remaining    = full_res$n,
  beta_Bz        = round(full_res$beta, 5),
  se_Bz          = round(full_res$se,   5),
  t_Bz           = round(full_res$t,    3),
  p_Bz           = signif(full_res$p,   4),
  same_direction = TRUE,
  stringsAsFactors = FALSE
)

for (phy in drop_phyla) {
  n_phy  <- sum(df$phylum == phy)
  sub_df <- df[df$phylum != phy, ]

  # Prune tree to remaining genera
  keep_tips  <- sub_df$genus_lower
  sub_tree   <- drop.tip(tree, setdiff(tree$tip.label, keep_tips))
  sub_df     <- sub_df[sub_df$genus_lower %in% sub_tree$tip.label, ]
  sub_df     <- sub_df[match(sub_tree$tip.label, sub_df$genus_lower), ]
  rownames(sub_df) <- sub_df$genus_lower

  cat(sprintf("Dropping %-30s (n=%3d) -> %d genera remaining ... ",
              phy, n_phy, nrow(sub_df)))

  res <- fit_pgls_fixed(sub_df, sub_tree, LAMBDA_FULL)

  if (res$ok) {
    same_dir <- !is.na(res$beta) && (sign(res$beta) == sign(full_res$beta))
    cat(sprintf("beta=%+.4f  SE=%.4f  p=%.2e  %s\n",
                res$beta, res$se, res$p,
                if (same_dir) "DIR_STABLE" else "DIR_FLIP!"))
    results[[length(results) + 1]] <- data.frame(
      dropped_phylum = phy,
      n_dropped      = n_phy,
      n_remaining    = res$n,
      beta_Bz        = round(res$beta, 5),
      se_Bz          = round(res$se,   5),
      t_Bz           = round(res$t,    3),
      p_Bz           = signif(res$p,   4),
      same_direction = same_dir,
      stringsAsFactors = FALSE
    )
  } else {
    cat(sprintf("FAILED: %s\n", res$err))
    results[[length(results) + 1]] <- data.frame(
      dropped_phylum = phy, n_dropped = n_phy, n_remaining = res$n,
      beta_Bz=NA, se_Bz=NA, t_Bz=NA, p_Bz=NA, same_direction=NA,
      stringsAsFactors = FALSE
    )
  }
}

# ── Summary ───────────────────────────────────────────────────────────────────
out <- do.call(rbind, results)
rownames(out) <- NULL

cat("\n=== LEAVE-ONE-CLADE-OUT SUMMARY ===\n")
print(out[, c("dropped_phylum","n_dropped","n_remaining","beta_Bz","se_Bz","p_Bz","same_direction")],
      row.names=FALSE)

n_stable  <- sum(out$same_direction, na.rm=TRUE) - 1L  # subtract full-model row
n_tested  <- nrow(out) - 1L
cat(sprintf("\nDirection stable in %d/%d leave-one-phylum-out fits\n", n_stable, n_tested))

# ── Save ──────────────────────────────────────────────────────────────────────
out_file <- file.path(DATA, "clade_leave_one_out_pgls.csv")
write.csv(out, out_file, row.names = FALSE)
cat(sprintf("Saved -> %s\n", out_file))

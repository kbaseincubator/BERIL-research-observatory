#!/usr/bin/env Rscript
# pgls_sensitivity.R
# Sensitivity analyses addressing reviewer-level methodological concerns:
#   1. Leave-one-metal-out: test if any single metal drives the metal-type result
#   2. Leave-one-environment-out: test if any single env category drives B_std
#   3. Within-genus variance in metal types as additional covariate
#   4. log(n_species) PGLS covariate (explicitly log-transformed, extends R1)
#
# Usage: Rscript pgls_sensitivity.R [data_dir]

suppressPackageStartupMessages({
  library(ape)
  library(nlme)
})

args     <- commandArgs(trailingOnly = TRUE)
data_dir <- if (length(args) >= 1) args[1] else "data"

cat("=== PGLS Sensitivity Analyses ===\n")
cat("Data dir:", data_dir, "\n\n")

# ── Load data ──────────────────────────────────────────────────────────────
pgls_sub    <- read.csv(file.path(data_dir, "pgls_subset.csv"),
                        stringsAsFactors = FALSE)
amr_species <- read.csv(file.path(data_dir, "species_metal_amr.csv"),
                        stringsAsFactors = FALSE)
prev_wide   <- read.csv(file.path(data_dir, "otu_env_prevalence_wide.csv"),
                        stringsAsFactors = FALSE, row.names = 1)
otu_nb      <- read.csv(file.path(data_dir, "otu_niche_breadth.csv"),
                        stringsAsFactors = FALSE)
bac_tree    <- read.tree(file.path(data_dir, "gtdb_bac_genus_pruned.tree"))

METALS <- c("Hg", "As", "Cu", "Zn", "Cd", "Cr", "Ni")
ENVS   <- colnames(prev_wide)
cat("Metals:      ", paste(METALS, collapse = ", "), "\n")
cat("Environments:", paste(ENVS,   collapse = ", "), "\n")
cat("PGLS subset n:", nrow(pgls_sub), "\n\n")

# ── Helper: run one PGLS model ─────────────────────────────────────────────
run_pgls <- function(sub, tree, response_col, predictor_cols, label = "") {
  keep     <- sub$genus_lower %in% tree$tip.label
  sub      <- sub[keep, ]
  tree_sub <- keep.tip(tree, sub$genus_lower)
  rownames(sub) <- sub$genus_lower
  sub      <- sub[tree_sub$tip.label, ]  # CRITICAL: sort to tree order
  n        <- nrow(sub)

  formula_obj <- as.formula(
    paste(response_col, "~", paste(predictor_cols, collapse = " + "))
  )
  cor_struct <- corPagel(0.5, phy = tree_sub, fixed = FALSE)

  tryCatch({
    fit   <- gls(formula_obj, data = sub,
                 correlation = cor_struct, method = "ML")
    coefs <- summary(fit)$tTable
    lam   <- coef(fit$modelStruct$corStruct, unconstrained = FALSE)

    data.frame(
      model     = label,
      n_taxa    = n,
      lambda    = lam,
      predictor = rownames(coefs)[-1],
      beta      = coefs[-1, "Value"],
      SE        = coefs[-1, "Std.Error"],
      t_stat    = coefs[-1, "t-value"],
      p_value   = coefs[-1, "p-value"],
      row.names = NULL
    )
  }, error = function(e) {
    cat("  [ERROR in", label, "]", conditionMessage(e), "\n")
    NULL
  })
}

# ── Analysis 1: Leave-one-metal-out ───────────────────────────────────────
cat("=== Analysis 1: Leave-one-metal-out ===\n")

# Build per-species presence indicators for each metal
amr_species$genus_lower <- tolower(amr_species$gtdb_genus)
# Filter to PGLS genera
amr_in <- amr_species[amr_species$genus_lower %in% pgls_sub$genus_lower, ]

# Metal count columns in species-level AMR data
metal_cols <- paste0("n_", METALS)

lomo_results <- list()

for (excl_metal in METALS) {
  remaining <- METALS[METALS != excl_metal]
  remain_cols <- paste0("n_", remaining)

  # Compute n_types_excl per species
  amr_in$n_types_excl <- rowSums(amr_in[, remain_cols, drop = FALSE] > 0)

  # Aggregate to genus
  genus_means <- aggregate(n_types_excl ~ genus_lower, data = amr_in, FUN = mean)
  names(genus_means)[2] <- "mean_n_types_excl"

  # Merge with niche breadth
  sub2 <- merge(
    pgls_sub[, c("genus_lower", "mean_levins_B_std")],
    genus_means,
    by = "genus_lower"
  )
  sub2$pred_z <- as.numeric(scale(sub2$mean_n_types_excl))

  r <- run_pgls(sub2, bac_tree, "mean_levins_B_std", "pred_z",
                label = paste0("excl_", excl_metal))
  if (!is.null(r)) {
    lomo_results[[excl_metal]] <- r
    cat(sprintf("  Excl %-2s  (n=%d  λ=%.3f)  β=%+.4f  SE=%.4f  p=%.4g\n",
                excl_metal, r$n_taxa[1], r$lambda[1],
                r$beta[1], r$SE[1], r$p_value[1]))
  }
}

lomo_df <- do.call(rbind, lomo_results)

# ── Analysis 2: Leave-one-environment-out ─────────────────────────────────
cat("\n=== Analysis 2: Leave-one-environment-out ===\n")

# Merge OTU prevalences with genus info from otu_nb
otu_genus <- otu_nb[!is.na(otu_nb$genus) & otu_nb$genus != "", c("otu_id", "genus")]
otu_genus$genus_lower <- tolower(otu_genus$genus)

# Subset prev_wide to OTUs with genus info and that are in PGLS genera
keep_otus <- otu_genus$otu_id[otu_genus$genus_lower %in% pgls_sub$genus_lower]
# Only keep otus present in prev_wide rownames
keep_otus <- keep_otus[keep_otus %in% rownames(prev_wide)]
prev_sub  <- prev_wide[keep_otus, ]
otu_genus_sub <- otu_genus[match(keep_otus, otu_genus$otu_id), ]

cat(sprintf("  OTUs with genus in PGLS subset and in prev_wide: %d\n", nrow(prev_sub)))

# Function to compute B_std from a prevalence matrix (rows=OTUs, cols=envs)
compute_B_std <- function(pmat) {
  # pmat: numeric matrix of raw prevalence values
  # Row-normalize to get proportions
  row_sums <- rowSums(pmat, na.rm = TRUE)
  # Exclude OTUs with zero total prevalence
  valid <- row_sums > 0
  pmat  <- pmat[valid, , drop = FALSE]
  row_sums <- row_sums[valid]

  p <- sweep(pmat, 1, row_sums, "/")  # proportions
  B <- 1 / rowSums(p^2)               # Levins' B
  J <- ncol(pmat)
  B_std <- (B - 1) / (J - 1)

  data.frame(otu_id = rownames(pmat), B_std = B_std)
}

loeo_results <- list()

for (excl_env in ENVS) {
  remaining_envs <- ENVS[ENVS != excl_env]
  pmat <- as.matrix(prev_sub[, remaining_envs, drop = FALSE])

  b_df <- compute_B_std(pmat)
  b_df$genus_lower <- otu_genus_sub$genus_lower[match(b_df$otu_id,
                                                       rownames(prev_sub))]
  b_df <- b_df[!is.na(b_df$genus_lower), ]

  # Aggregate to genus (mean)
  genus_b <- aggregate(B_std ~ genus_lower, data = b_df, FUN = mean)
  names(genus_b)[2] <- "mean_levins_B_std_excl"

  # Merge with AMR predictor
  sub3 <- merge(
    pgls_sub[, c("genus_lower", "mean_n_metal_types")],
    genus_b,
    by = "genus_lower"
  )
  sub3$pred_z <- as.numeric(scale(sub3$mean_n_metal_types))
  names(sub3)[names(sub3) == "mean_levins_B_std_excl"] <- "mean_levins_B_std"

  r <- run_pgls(sub3, bac_tree, "mean_levins_B_std", "pred_z",
                label = paste0("excl_env_", excl_env))
  if (!is.null(r)) {
    loeo_results[[excl_env]] <- r
    cat(sprintf("  Excl env=%-14s  (n=%d  λ=%.3f)  β=%+.4f  SE=%.4f  p=%.4g\n",
                excl_env, r$n_taxa[1], r$lambda[1],
                r$beta[1], r$SE[1], r$p_value[1]))
  }
}

loeo_df <- do.call(rbind, loeo_results)

# ── Analysis 3: Within-genus variance in metal types ──────────────────────
cat("\n=== Analysis 3: Within-genus SD of metal types as covariate ===\n")

amr_in$n_types <- rowSums(amr_in[, metal_cols, drop = FALSE] > 0)
genus_sd <- aggregate(n_types ~ genus_lower, data = amr_in,
                      FUN = function(x) if (length(x) > 1) sd(x) else 0)
names(genus_sd)[2] <- "sd_n_metal_types"

sub4 <- merge(pgls_sub, genus_sd, by = "genus_lower", all.x = TRUE)
sub4$sd_n_metal_types[is.na(sub4$sd_n_metal_types)] <- 0
sub4$sd_metal_z <- as.numeric(scale(sub4$sd_n_metal_types))

r3 <- run_pgls(sub4, bac_tree, "mean_levins_B_std",
               c("mean_n_metal_types_z", "sd_metal_z"),
               label = "B_std~types_z+sd_types_z")
if (!is.null(r3)) {
  cat(sprintf("  B_std ~ metal_types_z + sd_metal_types_z  (n=%d  λ=%.3f)\n",
              r3$n_taxa[1], r3$lambda[1]))
  for (i in seq_len(nrow(r3))) {
    cat(sprintf("    %-30s  β=%+.4f  SE=%.4f  p=%.4g\n",
                r3$predictor[i], r3$beta[i], r3$SE[i], r3$p_value[i]))
  }
}

# ── Analysis 4: log(n_species) as PGLS covariate ──────────────────────────
cat("\n=== Analysis 4: log(n_species_with_amr) as PGLS covariate ===\n")

sub5 <- pgls_sub
sub5$log_n_species_z <- as.numeric(scale(log1p(sub5$n_species_with_amr)))

r4 <- run_pgls(sub5, bac_tree, "mean_levins_B_std",
               c("mean_n_metal_types_z", "log_n_species_z"),
               label = "B_std~types_z+log_n_species_z")
if (!is.null(r4)) {
  cat(sprintf("  B_std ~ metal_types_z + log(n_species_z)  (n=%d  λ=%.3f)\n",
              r4$n_taxa[1], r4$lambda[1]))
  for (i in seq_len(nrow(r4))) {
    cat(sprintf("    %-30s  β=%+.4f  SE=%.4f  p=%.4g\n",
                r4$predictor[i], r4$beta[i], r4$SE[i], r4$p_value[i]))
  }
}

# ── Save results ───────────────────────────────────────────────────────────
cat("\n=== Saving results ===\n")

rows_out <- list()
if (!is.null(lomo_df))   rows_out[["lomo"]]  <- lomo_df
if (!is.null(loeo_df))   rows_out[["loeo"]]  <- loeo_df
if (!is.null(r3))        rows_out[["within_genus_var"]] <- r3
if (!is.null(r4))        rows_out[["log_n_spp"]]        <- r4

if (length(rows_out) > 0) {
  combined <- do.call(rbind, rows_out)
  out_path <- file.path(data_dir, "pgls_sensitivity_results.csv")
  write.csv(combined, out_path, row.names = FALSE)
  cat("Saved:", out_path, "(", nrow(combined), "rows)\n")
}

cat("\nDone.\n")

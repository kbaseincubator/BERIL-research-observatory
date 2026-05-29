#!/usr/bin/env Rscript
# pgls_robustness.R
# Three robustness analyses to address caveats in the main PGLS (NB05):
#   1. Add n_species_with_amr as a covariate to control for pangenome sampling depth
#   2. Pangenome rarefaction: sample 1 species per genus, 200 iterations
#   3. Archaeal PGLS (n = 48 genera; low-power, exploratory)
#
# Usage: Rscript pgls_robustness.R [data_dir]

suppressPackageStartupMessages({
  library(ape)
  library(nlme)
})

args     <- commandArgs(trailingOnly = TRUE)
data_dir <- if (length(args) >= 1) args[1] else "data"

cat("=== PGLS Robustness Analyses ===\n")
cat("Data dir:", data_dir, "\n\n")

# ── Load data ────────────────────────────────────────────────────────────────
traits      <- read.csv(file.path(data_dir, "genus_trait_table.csv"),
                        stringsAsFactors = FALSE)
amr_species <- read.csv(file.path(data_dir, "species_metal_amr.csv"),
                        stringsAsFactors = FALSE)
pgls_sub    <- read.csv(file.path(data_dir, "pgls_subset.csv"),
                        stringsAsFactors = FALSE)

bac_tree <- read.tree(file.path(data_dir, "gtdb_bac_genus_pruned.tree"))
arc_tree <- read.tree(file.path(data_dir, "gtdb_arc_genus_pruned.tree"))

cat("Bacterial PGLS subset:", nrow(pgls_sub), "genera\n")
cat("Archaeal tree tips:   ", length(arc_tree$tip.label), "\n\n")

# ── Helper: fit one PGLS model ───────────────────────────────────────────────
run_pgls <- function(sub, tree, response_col, predictor_cols, label = "") {
  keep     <- sub$genus_lower %in% tree$tip.label
  sub      <- sub[keep, ]
  tree_sub <- keep.tip(tree, sub$genus_lower)
  rownames(sub) <- sub$genus_lower
  sub      <- sub[tree_sub$tip.label, ]     # CRITICAL: sort to tree order
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

    out <- data.frame(
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
    out
  }, error = function(e) {
    cat("  [ERROR]", conditionMessage(e), "\n")
    NULL
  })
}

# ── Analysis 1: n_species_with_amr as covariate ──────────────────────────────
cat("=== Analysis 1: PGLS with n_species_with_amr as covariate ===\n")

sub1 <- pgls_sub
sub1$n_species_with_amr_z <- as.numeric(scale(sub1$n_species_with_amr))

# 1a: B_std ~ metal_types_z + n_species_with_amr_z
r1a <- run_pgls(sub1, bac_tree, "mean_levins_B_std",
                c("mean_n_metal_types_z", "n_species_with_amr_z"),
                label = "B_std~types+n_species")

if (!is.null(r1a)) {
  cat(sprintf("  B_std ~ metal_types_z + n_species_with_amr_z  (n=%d  λ=%.3f)\n",
              r1a$n_taxa[1], r1a$lambda[1]))
  for (i in seq_len(nrow(r1a))) {
    cat(sprintf("    %-35s  β=%+.4f  SE=%.4f  p=%.4g\n",
                r1a$predictor[i], r1a$beta[i], r1a$SE[i], r1a$p_value[i]))
  }
}

# 1b: B_std ~ all 3 AMR + n_species_with_amr_z (extend the multi-predictor model)
r1b <- run_pgls(sub1, bac_tree, "mean_levins_B_std",
                c("mean_n_metal_types_z", "mean_n_metal_amr_clusters_z",
                  "mean_metal_core_fraction_z", "n_species_with_amr_z"),
                label = "B_std~all3+n_species")

if (!is.null(r1b)) {
  cat(sprintf("\n  B_std ~ all 3 AMR + n_species_with_amr_z  (n=%d  λ=%.3f)\n",
              r1b$n_taxa[1], r1b$lambda[1]))
  for (i in seq_len(nrow(r1b))) {
    cat(sprintf("    %-35s  β=%+.4f  SE=%.4f  p=%.4g\n",
                r1b$predictor[i], r1b$beta[i], r1b$SE[i], r1b$p_value[i]))
  }
}

# ── Analysis 2: Rarefied PGLS (1 species per genus, 200 iterations) ──────────
cat("\n=== Analysis 2: Rarefied PGLS (1 species per genus, 200 iterations) ===\n")

amr_species$gtdb_genus_lower <- tolower(amr_species$gtdb_genus)
pgls_genera <- unique(pgls_sub$genus_lower)
amr_match   <- amr_species[amr_species$gtdb_genus_lower %in% pgls_genera, ]

n_multi <- sum(table(amr_match$gtdb_genus_lower) > 1)
cat(sprintf("  Genera with >1 species in AMR db: %d of %d in PGLS subset\n",
            n_multi, length(pgls_genera)))
cat("  Running 200 rarefied PGLS iterations...\n")

set.seed(42)
rar_betas <- numeric(200)
rar_ps    <- numeric(200)
rar_ns    <- integer(200)
rar_lams  <- numeric(200)
n_ok      <- 0L

for (iter in seq_len(200)) {
  # Sample 1 species per genus (base R)
  samp <- do.call(rbind, lapply(
    split(amr_match, amr_match$gtdb_genus_lower),
    function(g) g[sample(nrow(g), 1), ]
  ))

  # Build sub: niche breadth from pgls_sub + rarefied AMR
  sub_r <- merge(
    pgls_sub[, c("genus_lower", "mean_levins_B_std")],
    samp[, c("gtdb_genus_lower", "n_metal_types",
             "n_metal_amr_clusters", "metal_core_fraction")],
    by.x = "genus_lower", by.y = "gtdb_genus_lower"
  )
  names(sub_r)[names(sub_r) == "n_metal_types"]        <- "mean_n_metal_types"
  names(sub_r)[names(sub_r) == "n_metal_amr_clusters"] <- "mean_n_metal_amr_clusters"
  names(sub_r)[names(sub_r) == "metal_core_fraction"]  <- "mean_metal_core_fraction"

  # Z-score predictors
  sub_r$mean_n_metal_types_z <- as.numeric(scale(sub_r$mean_n_metal_types))

  res_r <- run_pgls(sub_r, bac_tree, "mean_levins_B_std",
                    "mean_n_metal_types_z")
  if (!is.null(res_r) && nrow(res_r) > 0) {
    n_ok <- n_ok + 1L
    row  <- res_r[res_r$predictor == "mean_n_metal_types_z", ]
    rar_betas[n_ok] <- row$beta
    rar_ps[n_ok]    <- row$p_value
    rar_ns[n_ok]    <- row$n_taxa
    rar_lams[n_ok]  <- row$lambda
  }
}

cat(sprintf("  Successful iterations: %d / 200\n", n_ok))

if (n_ok > 0) {
  b  <- rar_betas[seq_len(n_ok)]
  p  <- rar_ps[seq_len(n_ok)]
  ns <- rar_ns[seq_len(n_ok)]
  ll <- rar_lams[seq_len(n_ok)]

  cat(sprintf("\n  B_std ~ metal_types_z (rarefied 1 species/genus):\n"))
  cat(sprintf("    Median β  = %+.4f  (IQR: %+.4f – %+.4f)\n",
              median(b), quantile(b, 0.25), quantile(b, 0.75)))
  cat(sprintf("    Median p  = %.4g\n", median(p)))
  cat(sprintf("    Frac p < 0.05        = %.1f%%\n", 100 * mean(p < 0.05)))
  cat(sprintf("    Frac p < 0.0083 (Bonf) = %.1f%%\n", 100 * mean(p < 0.0083)))
  cat(sprintf("    Median λ = %.3f\n",  median(ll)))
  cat(sprintf("    Median n taxa = %d\n", as.integer(median(ns))))

  rar_summary <- data.frame(
    model          = "rarefied_1species",
    response       = "mean_levins_B_std",
    predictor      = "mean_n_metal_types_z",
    n_iterations   = n_ok,
    median_n_taxa  = as.integer(median(ns)),
    median_lambda  = median(ll),
    median_beta    = median(b),
    q25_beta       = as.numeric(quantile(b, 0.25)),
    q75_beta       = as.numeric(quantile(b, 0.75)),
    median_p       = median(p),
    frac_p_lt_0.05 = mean(p < 0.05),
    frac_bonf_sig  = mean(p < 0.0083)
  )
  write.csv(rar_summary,
            file.path(data_dir, "pgls_rarefied_summary.csv"),
            row.names = FALSE)
  cat("\nSaved: pgls_rarefied_summary.csv\n")
}

# ── Analysis 3: Archaeal PGLS ────────────────────────────────────────────────
cat("\n=== Analysis 3: Archaeal PGLS (n ≈ 48, exploratory) ===\n")

traits$genus_lower <- tolower(traits$otu_genus)
arc_mask <- (
  traits$kingdom == "Archaea" &
  !is.na(traits$mean_n_metal_types) &
  !is.na(traits$mean_levins_B_std)
)
arc_sub <- traits[arc_mask, ]
arc_sub  <- arc_sub[arc_sub$genus_lower %in% arc_tree$tip.label, ]
cat(sprintf("  Archaeal genera with AMR + B_std + in tree: %d\n", nrow(arc_sub)))

if (nrow(arc_sub) >= 10) {
  arc_sub$mean_n_metal_types_z        <- as.numeric(scale(arc_sub$mean_n_metal_types))
  arc_sub$mean_n_metal_amr_clusters_z <- as.numeric(scale(arc_sub$mean_n_metal_amr_clusters))
  arc_sub$mean_metal_core_fraction_z  <- as.numeric(scale(arc_sub$mean_metal_core_fraction))

  arc_results <- list()
  for (pred_z in c("mean_n_metal_types_z",
                   "mean_n_metal_amr_clusters_z",
                   "mean_metal_core_fraction_z")) {
    r <- run_pgls(arc_sub, arc_tree, "mean_levins_B_std", pred_z,
                  label = paste0("arc_B_std~", pred_z))
    if (!is.null(r)) {
      arc_results[[pred_z]] <- r
      cat(sprintf("  arc B_std ~ %-35s  β=%+.4f  SE=%.4f  p=%.4g  λ=%.3f  n=%d\n",
                  pred_z, r$beta[1], r$SE[1], r$p_value[1],
                  r$lambda[1], r$n_taxa[1]))
    }
  }
  arc_df <- do.call(rbind, arc_results)
} else {
  cat("  Too few archaea (<10); skipping PGLS.\n")
  arc_df <- NULL
}

# ── Save combined results ────────────────────────────────────────────────────
cat("\n=== Saving combined results ===\n")

rows <- list()
if (!is.null(r1a))  rows[["cov_simple"]] <- r1a
if (!is.null(r1b))  rows[["cov_full"]]   <- r1b
if (!is.null(arc_df)) rows[["archaea"]]  <- arc_df

if (length(rows) > 0) {
  combined <- do.call(rbind, rows)
  out_path <- file.path(data_dir, "pgls_robustness_results.csv")
  write.csv(combined, out_path, row.names = FALSE)
  cat("Saved:", out_path, "(", nrow(combined), "rows)\n")
}

cat("\nDone.\n")

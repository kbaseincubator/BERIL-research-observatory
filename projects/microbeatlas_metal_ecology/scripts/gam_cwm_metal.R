#!/usr/bin/env Rscript
# gam_cwm_metal.R — Fit GAM models (base + full) for CWM × metal pairs.
#
# Usage:
#   Rscript gam_cwm_metal.R <cwm_csv> <covariate_csv> <output_csv>
#
# Input:
#   cwm_csv       : CSV with columns [sample_id, ko_id, cwm]
#   covariate_csv : CSV with columns [sample_id, As, Cd, Cr, Cu, Hg, Pb,
#                   ph_soilgrids, ph_ssurgo, drainage_class, organic_matter,
#                   clay_pct, cec, lith_class, usgs_mine_distance,
#                   epa_tri_releases, tectonic_boundary_dist, shannon,
#                   phylum_* columns]
#
# Output:
#   output_csv : CSV with per-KO × metal GAM results

suppressPackageStartupMessages({
  library(mgcv)
  library(parallel)
})

METALS   <- c("As", "Cd", "Cr", "Cu", "Hg", "Pb")
MIN_N    <- 30    # minimum observations per model
K_MET    <- 4    # spline knots for metal smoother
K_PH     <- 4    # spline knots for pH
K_MINE   <- 3    # spline knots for mine distance
K_CEC    <- 3    # spline knots for CEC
N_CORES  <- 16   # parallel cores for KO loop

# ── Parse arguments ────────────────────────────────────────────────────────────
args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 3) {
  stop("Usage: Rscript gam_cwm_metal.R <cwm_csv> <covariate_csv> <output_csv>")
}
cwm_path  <- args[1]
cov_path  <- args[2]
out_path  <- args[3]

cat(sprintf("GAM analysis starting\n"))
cat(sprintf("  CWM:        %s\n", cwm_path))
cat(sprintf("  Covariates: %s\n", cov_path))
cat(sprintf("  Output:     %s\n", out_path))

# ── Load data ──────────────────────────────────────────────────────────────────
cat("Loading CWM data...\n")
cwm <- read.csv(cwm_path, stringsAsFactors = FALSE)
cat(sprintf("  CWM: %d rows, %d unique KOs, %d unique samples\n",
            nrow(cwm), length(unique(cwm$ko_id)), length(unique(cwm$sample_id))))

cat("Loading covariate matrix...\n")
cov <- read.csv(cov_path, stringsAsFactors = FALSE)
cat(sprintf("  Covariates: %d rows, %d columns\n", nrow(cov), ncol(cov)))

# Identify phylum and land-cover columns
phylum_cols <- grep("^phylum_", names(cov), value = TRUE)
lc_cols     <- grep("^lc_", names(cov), value = TRUE)
cat(sprintf("  Phylum columns: %s\n", paste(phylum_cols, collapse = ", ")))
cat(sprintf("  Land cover columns: %s\n", paste(lc_cols, collapse = ", ")))

# Factor columns
if ("drainage_class" %in% names(cov)) {
  cov$drainage_class <- as.factor(cov$drainage_class)
}
if ("lith_class" %in% names(cov)) {
  cov$lith_class <- as.factor(cov$lith_class)
}

# ── GAM helper ─────────────────────────────────────────────────────────────────
fit_gam_pair <- function(df_pair, metal) {
  # df_pair: rows for one KO, merged with covariates
  # Returns: list with base and full model results

  # Log-transform exposure
  df_pair$log10_metal <- log10(pmax(df_pair[[metal]], 1e-6))
  df_pair$log10_mine  <- log10(pmax(df_pair$usgs_mine_distance, 0.1) + 1)

  # Base covariate set: metal + pH (always available from SoilGrids)
  # Use ph_soilgrids if available, fall back to ph_ssurgo
  if ("ph_soilgrids" %in% names(df_pair) && sum(!is.na(df_pair$ph_soilgrids)) > MIN_N) {
    df_pair$ph_use <- df_pair$ph_soilgrids
  } else if ("ph_ssurgo" %in% names(df_pair)) {
    df_pair$ph_use <- df_pair$ph_ssurgo
  } else {
    df_pair$ph_use <- NA_real_
  }

  # Complete cases for base model
  base_vars <- c("cwm", "log10_metal", "ph_use")
  df_base <- df_pair[complete.cases(df_pair[, base_vars, drop = FALSE]), ]

  result <- list(
    ko_id          = NA_character_,
    metal          = metal,
    n              = nrow(df_base),
    p_metal_base   = NA_real_,
    p_metal_full   = NA_real_,
    devexpl_base   = NA_real_,
    devexpl_full   = NA_real_,
    aic_base       = NA_real_,
    aic_full       = NA_real_,
    attenuation_ratio = NA_real_,
    converged_base = FALSE,
    converged_full = FALSE,
    error_msg      = NA_character_
  )

  if (nrow(df_base) < MIN_N) {
    result$error_msg <- sprintf("n=%d < %d", nrow(df_base), MIN_N)
    return(result)
  }
  if (var(df_base$cwm) < 1e-20) {
    result$error_msg <- "cwm constant"
    return(result)
  }

  result$n <- nrow(df_base)

  # ── Base model: cwm ~ s(log10_metal, k=4) + s(ph, k=4) ────────────────────
  tryCatch({
    # Adjust k if n is small
    k_met_adj <- min(K_MET, floor(nrow(df_base) / 5))
    k_ph_adj  <- if (!all(is.na(df_base$ph_use))) min(K_PH, floor(nrow(df_base) / 5)) else 1

    if (k_ph_adj >= 3 && !all(is.na(df_base$ph_use))) {
      m_base <- bam(cwm ~ s(log10_metal, k = k_met_adj) + s(ph_use, k = k_ph_adj),
                    data = df_base, method = "fREML", discrete = TRUE)
    } else {
      m_base <- bam(cwm ~ s(log10_metal, k = k_met_adj),
                    data = df_base, method = "fREML", discrete = TRUE)
    }
    sm_base <- summary(m_base)
    result$p_metal_base   <- sm_base$s.table["s(log10_metal)", "p-value"]
    result$devexpl_base   <- sm_base$dev.expl
    result$aic_base       <- AIC(m_base)
    result$converged_base <- m_base$converged
  }, error = function(e) {
    result$error_msg <<- paste("base:", conditionMessage(e))
  })

  # ── Full model: adds mine, soil props, community ─────────────────────────────
  # Select full-model covariates available in this dataset
  full_extra <- c()
  if ("log10_mine" %in% names(df_pair) &&
      sum(!is.na(df_pair$log10_mine)) > MIN_N) {
    full_extra <- c(full_extra, "log10_mine")
  }
  if ("cec" %in% names(df_pair) && sum(!is.na(df_pair$cec)) > MIN_N/2) {
    full_extra <- c(full_extra, "cec")
  }
  if ("clay_pct" %in% names(df_pair) && sum(!is.na(df_pair$clay_pct)) > MIN_N/2) {
    full_extra <- c(full_extra, "clay_pct")
  }
  if ("organic_matter" %in% names(df_pair) && sum(!is.na(df_pair$organic_matter)) > MIN_N/2) {
    full_extra <- c(full_extra, "organic_matter")
  }
  if ("drainage_class" %in% names(df_pair) && sum(!is.na(df_pair$drainage_class)) > MIN_N/2) {
    full_extra <- c(full_extra, "drainage_class")
  }
  if ("lith_class" %in% names(df_pair) && sum(!is.na(df_pair$lith_class)) > MIN_N/2) {
    full_extra <- c(full_extra, "lith_class")
  }
  if ("epa_tri_releases" %in% names(df_pair) && sum(!is.na(df_pair$epa_tri_releases)) > MIN_N/2) {
    full_extra <- c(full_extra, "epa_tri_releases")
  }
  if ("shannon" %in% names(df_pair) && sum(!is.na(df_pair$shannon)) > MIN_N/2) {
    full_extra <- c(full_extra, "shannon")
  }
  # Add phylum columns with reasonable coverage
  for (pc in phylum_cols) {
    if (pc %in% names(df_pair) && sum(!is.na(df_pair[[pc]])) > MIN_N/2) {
      full_extra <- c(full_extra, pc)
    }
  }
  # Add land cover columns
  for (lc in lc_cols) {
    if (lc %in% names(df_pair) && sum(!is.na(df_pair[[lc]])) > MIN_N/2) {
      full_extra <- c(full_extra, lc)
    }
  }

  if (length(full_extra) > 0) {
    full_vars <- c(base_vars, full_extra)
    df_full <- df_pair[complete.cases(df_pair[, intersect(full_vars, names(df_pair)),
                                               drop = FALSE]), ]

    if (nrow(df_full) >= MIN_N) {
      tryCatch({
        k_met_adj <- min(K_MET, floor(nrow(df_full) / 5))
        k_ph_adj  <- if (!all(is.na(df_full$ph_use))) min(K_PH, floor(nrow(df_full) / 5)) else 1
        k_mine_adj <- min(K_MINE, floor(nrow(df_full) / 5))
        k_cec_adj  <- min(K_CEC, floor(nrow(df_full) / 5))

        # Build formula dynamically
        terms <- c(sprintf("s(log10_metal, k=%d)", k_met_adj))
        if (!all(is.na(df_full$ph_use)) && k_ph_adj >= 3) {
          terms <- c(terms, sprintf("s(ph_use, k=%d)", k_ph_adj))
        }
        if ("log10_mine" %in% full_extra) {
          terms <- c(terms, sprintf("s(log10_mine, k=%d)", k_mine_adj))
        }
        if ("cec" %in% full_extra && k_cec_adj >= 3) {
          terms <- c(terms, sprintf("s(cec, k=%d)", k_cec_adj))
        }
        # Linear terms for categoricals and bounded-range continuous vars
        lin_terms <- intersect(full_extra, c("clay_pct", "organic_matter",
                                              "drainage_class", "lith_class",
                                              "epa_tri_releases", "shannon"))
        lin_terms <- c(lin_terms, intersect(full_extra, phylum_cols))
        lin_terms <- c(lin_terms, intersect(full_extra, lc_cols))
        if (length(lin_terms) > 0) {
          terms <- c(terms, lin_terms)
        }

        fmla <- as.formula(paste("cwm ~", paste(terms, collapse = " + ")))
        m_full <- bam(fmla, data = df_full, method = "fREML", discrete = TRUE)
        sm_full <- summary(m_full)
        result$p_metal_full   <- sm_full$s.table["s(log10_metal)", "p-value"]
        result$devexpl_full   <- sm_full$dev.expl
        result$aic_full       <- AIC(m_full)
        result$converged_full <- m_full$converged

        # Attenuation: how much does full model change metal deviance explained?
        if (!is.na(result$devexpl_base) && result$devexpl_base > 0) {
          result$attenuation_ratio <- 1 - (result$devexpl_full / result$devexpl_base)
        }
      }, error = function(e) {
        result$error_msg <<- paste(result$error_msg, "| full:", conditionMessage(e))
      })
    }
  }

  return(result)
}

# ── Main loop ─────────────────────────────────────────────────────────────────
cat("Starting GAM loop over all KO × metal pairs...\n")

all_kos <- unique(cwm$ko_id)
n_kos   <- length(all_kos)
n_metals <- length(METALS)
cat(sprintf("  %d KOs × %d metals = up to %d models\n", n_kos, n_metals, n_kos * n_metals))

# Pre-merge covariates onto CWM once, then split by ko_id for O(n) iteration.
# Avoid repeated cwm[cwm$ko_id == ko, ] on 2.79M rows (O(n²) total).
cat("Pre-merging covariates...\n")
cwm_cov <- merge(cwm, cov, by = "sample_id", all.x = FALSE)
cat(sprintf("  Merged dataset: %d rows\n", nrow(cwm_cov)))

cat("Splitting by KO (one-time O(n) pre-pass)...\n")
ko_list <- split(cwm_cov, cwm_cov$ko_id)
rm(cwm_cov)   # free memory
gc()
cat(sprintf("  Split into %d KO groups.\n", length(ko_list)))

cat(sprintf("Parallelising over KOs with %d cores...\n", N_CORES))
t_start <- proc.time()

process_ko <- function(ko) {
  df_ko <- ko_list[[ko]]
  if (is.null(df_ko)) return(NULL)
  results_ko <- vector("list", length(METALS))
  for (j in seq_along(METALS)) {
    metal <- METALS[j]
    if (!(metal %in% names(df_ko))) next
    df_pair <- df_ko[!is.na(df_ko[[metal]]), ]
    res <- fit_gam_pair(df_pair, metal)
    res$ko_id <- ko
    results_ko[[j]] <- as.data.frame(res)
  }
  results_ko[!sapply(results_ko, is.null)]
}

all_results_nested <- mclapply(all_kos, process_ko, mc.cores = N_CORES)
elapsed <- (proc.time() - t_start)[["elapsed"]]
cat(sprintf("  Loop complete: %.1f min\n", elapsed / 60))

results <- unlist(all_results_nested, recursive = FALSE)

# Combine and save
results_clean <- results[!sapply(results, is.null)]
out_df <- do.call(rbind, results_clean)

cat(sprintf("\nFitting complete: %d total results\n", nrow(out_df)))
cat(sprintf("  Models with n >= %d: %d\n", MIN_N, sum(out_df$n >= MIN_N, na.rm = TRUE)))
cat(sprintf("  Converged (base): %d\n", sum(out_df$converged_base, na.rm = TRUE)))

write.csv(out_df, out_path, row.names = FALSE)
cat(sprintf("\nSaved: %s\n", out_path))

# Quick BH-FDR summary (R side)
valid <- out_df[!is.na(out_df$p_metal_base) & out_df$n >= MIN_N, ]
if (nrow(valid) > 0) {
  valid$q_BH <- p.adjust(valid$p_metal_base, method = "BH")
  n_sig <- sum(valid$q_BH < 0.05)
  cat(sprintf("\nBH-FDR summary (base model, n >= %d):\n", MIN_N))
  cat(sprintf("  Tests: %d | FDR<0.05: %d\n", nrow(valid), n_sig))
  if (n_sig > 0) {
    top <- valid[order(valid$q_BH), ][seq_len(min(10, n_sig)), ]
    cat("  Top significant pairs:\n")
    print(top[, c("ko_id", "metal", "n", "p_metal_base", "q_BH",
                   "devexpl_base", "devexpl_full")])
  } else {
    top <- valid[order(valid$p_metal_base), ][seq_len(min(10, nrow(valid))), ]
    cat("  Top 10 (all q > 0.05):\n")
    print(top[, c("ko_id", "metal", "n", "p_metal_base", "q_BH", "devexpl_base")])
  }
}

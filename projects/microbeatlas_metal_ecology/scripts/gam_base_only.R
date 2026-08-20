#!/usr/bin/env Rscript
# gam_base_only.R — Base model only: cwm ~ s(log10_metal, k=4) + s(ph_use, k=4)
# Writes to a SEPARATE file from gam_results_raw.csv (full model run).
suppressPackageStartupMessages({
  library(mgcv)
  library(parallel)
})

METALS  <- c("As", "Cd", "Cr", "Cu", "Hg", "Pb")
MIN_N   <- 30
K_MET   <- 4
K_PH    <- 4
N_CORES <- 16

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 3) stop("Usage: Rscript gam_base_only.R <cwm_csv> <cov_csv> <out_csv>")
cwm_path <- args[1]; cov_path <- args[2]; out_path <- args[3]

cat(sprintf("Base-model GAM\n  CWM: %s\n  Cov: %s\n  Out: %s\n", cwm_path, cov_path, out_path))

cwm <- read.csv(cwm_path, stringsAsFactors = FALSE)
cov <- read.csv(cov_path, stringsAsFactors = FALSE)
cat(sprintf("CWM: %d rows, %d KOs, %d samples\n",
            nrow(cwm), length(unique(cwm$ko_id)), length(unique(cwm$sample_id))))

if ("drainage_class" %in% names(cov)) cov$drainage_class <- as.factor(cov$drainage_class)
if ("lith_class"     %in% names(cov)) cov$lith_class     <- as.factor(cov$lith_class)

fit_base <- function(df_pair, metal, ko) {
  df_pair$log10_metal <- log10(pmax(df_pair[[metal]], 1e-6))
  df_pair$ph_use <- if ("ph_soilgrids" %in% names(df_pair) &&
                         sum(!is.na(df_pair$ph_soilgrids)) > MIN_N) {
    df_pair$ph_soilgrids
  } else if ("ph_ssurgo" %in% names(df_pair)) {
    df_pair$ph_ssurgo
  } else NA_real_

  base_vars <- c("cwm", "log10_metal", "ph_use")
  df <- df_pair[complete.cases(df_pair[, base_vars, drop = FALSE]), ]

  out <- data.frame(ko_id = ko, metal = metal, n = nrow(df),
                    p_metal = NA_real_, devexpl = NA_real_,
                    aic = NA_real_, converged = FALSE,
                    error_msg = NA_character_, stringsAsFactors = FALSE)

  if (nrow(df) < MIN_N)           { out$error_msg <- sprintf("n=%d<30", nrow(df)); return(out) }
  if (var(df$cwm) < 1e-20)        { out$error_msg <- "cwm constant";               return(out) }

  k_met <- min(K_MET, floor(nrow(df) / 5))
  k_ph  <- min(K_PH,  floor(nrow(df) / 5))
  use_ph <- k_ph >= 3 && !all(is.na(df$ph_use))

  tryCatch({
    m <- if (use_ph) {
      bam(cwm ~ s(log10_metal, k = k_met) + s(ph_use, k = k_ph),
          data = df, method = "fREML", discrete = TRUE)
    } else {
      bam(cwm ~ s(log10_metal, k = k_met),
          data = df, method = "fREML", discrete = TRUE)
    }
    sm <- summary(m)
    out$p_metal   <- sm$s.table["s(log10_metal)", "p-value"]
    out$devexpl   <- sm$dev.expl
    out$aic       <- AIC(m)
    out$converged <- m$converged
  }, error = function(e) {
    out$error_msg <<- conditionMessage(e)
  })
  out
}

cat("Merging and splitting by KO...\n")
cwm_cov <- merge(cwm, cov, by = "sample_id", all.x = FALSE)
ko_list <- split(cwm_cov, cwm_cov$ko_id)
rm(cwm_cov); gc()
all_kos <- names(ko_list)
cat(sprintf("Split into %d KO groups. Launching %d cores.\n", length(all_kos), N_CORES))

t0 <- proc.time()
results_nested <- mclapply(all_kos, function(ko) {
  df_ko <- ko_list[[ko]]
  lapply(METALS, function(metal) {
    if (!(metal %in% names(df_ko))) return(NULL)
    df_pair <- df_ko[!is.na(df_ko[[metal]]), ]
    fit_base(df_pair, metal, ko)
  })
}, mc.cores = N_CORES)

elapsed <- (proc.time() - t0)[["elapsed"]]
cat(sprintf("Loop done: %.1f min\n", elapsed / 60))

results <- Filter(Negate(is.null), unlist(results_nested, recursive = FALSE))
out_df  <- do.call(rbind, results)
cat(sprintf("Total results: %d rows\n", nrow(out_df)))

valid <- out_df[!is.na(out_df$p_metal) & out_df$n >= MIN_N, ]
cat(sprintf("Testable pairs (n>=30, converged): %d\n", nrow(valid)))
valid$q_BH <- p.adjust(valid$p_metal, method = "BH")
n_sig <- sum(valid$q_BH < 0.05, na.rm = TRUE)
cat(sprintf("BH FDR<0.05: %d / %d\n", n_sig, nrow(valid)))
if (n_sig > 0) {
  top <- valid[order(valid$q_BH), ][seq_len(min(10, n_sig)), ]
  print(top[, c("ko_id","metal","n","p_metal","q_BH","devexpl")])
} else {
  top10 <- valid[order(valid$p_metal), ][seq_len(min(10, nrow(valid))), ]
  cat("Top 10 by p (all q>0.05):\n")
  print(top10[, c("ko_id","metal","n","p_metal","q_BH","devexpl")])
}

write.csv(out_df, out_path, row.names = FALSE)
cat(sprintf("Saved: %s\n", out_path))

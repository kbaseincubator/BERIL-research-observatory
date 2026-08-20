#!/usr/bin/env Rscript
# lm_ns_base.R — Fast base model: cwm ~ ns(log10_metal,3) + ns(ph_use,3)
# Uses natural splines (fixed df=3) via lm() instead of GAM REML.
# ~0.01 sec/fit vs ~2 sec/fit for gam(). Suitable for screening 38,592 pairs.
# Metal p-value from F-test: anova(m_null, m_full, test="F")$Pr[2]
suppressPackageStartupMessages({
  library(splines)
  library(parallel)
})

METALS  <- c("As", "Cd", "Cr", "Cu", "Hg", "Pb")
MIN_N   <- 30
NS_DF   <- 3      # effective df for natural splines (k=4 equivalent)
N_CORES <- 1   # Serial: avoid fork-copy OOM on large ko_list (2.4GB). 6.5 min at 0.01s/fit.

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 3) stop("Usage: Rscript lm_ns_base.R <cwm_csv> <cov_csv> <out_csv>")
cwm_path <- args[1]; cov_path <- args[2]; out_path <- args[3]
cat(sprintf("lm+ns base model\n  CWM: %s\n  Cov: %s\n  Out: %s\n",
            cwm_path, cov_path, out_path))

cwm <- read.csv(cwm_path, stringsAsFactors = FALSE)
cov <- read.csv(cov_path, stringsAsFactors = FALSE)
cat(sprintf("CWM: %d rows, %d KOs, %d samples\n",
            nrow(cwm), length(unique(cwm$ko_id)), length(unique(cwm$sample_id))))

fit_pair <- function(df_pair, metal, ko) {
  df_pair$log10_metal <- log10(pmax(df_pair[[metal]], 1e-6))
  df_pair$ph_use <- if ("ph_soilgrids" %in% names(df_pair) &&
                         sum(!is.na(df_pair$ph_soilgrids)) > MIN_N) {
    df_pair$ph_soilgrids
  } else if ("ph_ssurgo" %in% names(df_pair)) {
    df_pair$ph_ssurgo
  } else NA_real_

  df <- df_pair[complete.cases(df_pair[, c("cwm","log10_metal","ph_use")]), ]

  out <- data.frame(ko_id=ko, metal=metal, n=nrow(df),
                    p_metal=NA_real_, r2_full=NA_real_, r2_null=NA_real_,
                    delta_r2=NA_real_, error_msg=NA_character_,
                    stringsAsFactors=FALSE)

  if (nrow(df) < MIN_N)     { out$error_msg <- sprintf("n=%d<30", nrow(df)); return(out) }
  if (var(df$cwm) < 1e-20)  { out$error_msg <- "cwm constant";               return(out) }

  tryCatch({
    # Null model (pH only); full model adds metal spline
    use_ph <- !all(is.na(df$ph_use)) && length(unique(df$ph_use)) >= 4
    if (use_ph) {
      m_null <- lm(cwm ~ ns(ph_use, df = NS_DF), data = df)
      m_full <- lm(cwm ~ ns(log10_metal, df = NS_DF) + ns(ph_use, df = NS_DF), data = df)
    } else {
      m_null <- lm(cwm ~ 1, data = df)
      m_full <- lm(cwm ~ ns(log10_metal, df = NS_DF), data = df)
    }
    av  <- anova(m_null, m_full, test = "F")
    out$p_metal  <- av$`Pr(>F)`[2]
    out$r2_full  <- summary(m_full)$r.squared
    out$r2_null  <- summary(m_null)$r.squared
    out$delta_r2 <- out$r2_full - out$r2_null
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
results_nested <- lapply(all_kos, function(ko) {
  df_ko <- ko_list[[ko]]
  lapply(METALS, function(metal) {
    if (!(metal %in% names(df_ko))) return(NULL)
    df_pair <- df_ko[!is.na(df_ko[[metal]]), ]
    fit_pair(df_pair, metal, ko)
  })
})

elapsed <- (proc.time() - t0)[["elapsed"]]
cat(sprintf("Loop done: %.1f sec\n", elapsed))

results <- Filter(Negate(is.null), unlist(results_nested, recursive = FALSE))
out_df  <- do.call(rbind, results)
cat(sprintf("Total rows: %d\n", nrow(out_df)))

valid <- out_df[!is.na(out_df$p_metal) & out_df$n >= MIN_N, ]
cat(sprintf("Testable pairs (n>=30): %d\n", nrow(valid)))
valid$q_BH <- p.adjust(valid$p_metal, method = "BH")
n_sig <- sum(valid$q_BH < 0.05, na.rm = TRUE)
cat(sprintf("\n=== BH FDR<0.05: %d / %d ===\n", n_sig, nrow(valid)))
if (n_sig > 0) {
  top <- valid[order(valid$q_BH), ][seq_len(min(20, n_sig)), ]
  print(top[, c("ko_id","metal","n","p_metal","q_BH","delta_r2")])
} else {
  top10 <- valid[order(valid$p_metal), ][seq_len(min(10, nrow(valid))), ]
  cat("Top 10 by p (all q>0.05):\n")
  print(top10[, c("ko_id","metal","n","p_metal","q_BH","delta_r2")])
}

write.csv(out_df, out_path, row.names = FALSE)
cat(sprintf("Saved: %s\n", out_path))

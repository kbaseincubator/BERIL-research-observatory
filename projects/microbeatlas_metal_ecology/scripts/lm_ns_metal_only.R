#!/usr/bin/env Rscript
# lm_ns_metal_only.R — Metal-only model: cwm ~ ns(metal,3) vs intercept
# No pH, no confounders. Tests raw metal-CWM association.
suppressPackageStartupMessages(library(splines))

MIN_N <- 30
NS_DF <- 3

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 3) stop("Usage: Rscript lm_ns_metal_only.R <input_csv> <metal> <out_csv>")
in_path <- args[1]; metal <- args[2]; out_path <- args[3]
cat(sprintf("Metal-only model | Metal: %s\n  Input: %s\n  Output: %s\n", metal, in_path, out_path))

d <- read.csv(in_path, stringsAsFactors = FALSE)
cat(sprintf("Rows: %d, KOs: %d, samples: %d\n",
            nrow(d), length(unique(d$ko_id)), length(unique(d$sample_id))))

fit_one_ko <- function(df_ko) {
  ko <- df_ko$ko_id[1]
  df <- df_ko[complete.cases(df_ko[, c("cwm", "log10_metal")]), ]

  out <- data.frame(ko_id=ko, metal=metal, n=nrow(df),
                    p_metal_noph=NA_real_, r2_noph=NA_real_,
                    delta_r2_noph=NA_real_, delta_cwm_iqr=NA_real_,
                    beta_sign=NA_integer_, error_msg=NA_character_,
                    stringsAsFactors=FALSE)
  if (nrow(df) < MIN_N)    { out$error_msg <- sprintf("n=%d<30", nrow(df)); return(out) }
  if (var(df$cwm) < 1e-20) { out$error_msg <- "cwm constant";               return(out) }

  tryCatch({
    m_null <- lm(cwm ~ 1,                             data = df)
    m_full <- lm(cwm ~ ns(log10_metal, df = NS_DF),   data = df)
    av     <- anova(m_null, m_full, test = "F")
    out$p_metal_noph  <- av$`Pr(>F)`[2]
    out$r2_noph       <- summary(m_full)$r.squared
    out$delta_r2_noph <- out$r2_noph  # vs intercept null

    q25_m <- quantile(df$log10_metal, 0.25, na.rm = TRUE)
    q75_m <- quantile(df$log10_metal, 0.75, na.rm = TRUE)
    pred_lo <- df[1, , drop = FALSE]; pred_lo$log10_metal <- q25_m
    pred_hi <- df[1, , drop = FALSE]; pred_hi$log10_metal <- q75_m
    cwm_iqr <- tryCatch(
      predict(m_full, newdata = pred_hi)[1] - predict(m_full, newdata = pred_lo)[1],
      error = function(e2) NA_real_
    )
    out$delta_cwm_iqr <- cwm_iqr
    out$beta_sign     <- if (is.na(cwm_iqr)) NA_integer_ else as.integer(sign(cwm_iqr))
  }, error = function(e) {
    out$error_msg <<- conditionMessage(e)
  })
  out
}

t0 <- proc.time()
ko_list <- split(d, d$ko_id)
rm(d); gc()
cat(sprintf("KO groups: %d\n", length(ko_list)))

results <- lapply(ko_list, fit_one_ko)
elapsed <- (proc.time() - t0)[["elapsed"]]
cat(sprintf("Loop: %.1f sec\n", elapsed))

out_df <- do.call(rbind, results)
cat(sprintf("Rows: %d\n", nrow(out_df)))
write.csv(out_df, out_path, row.names = FALSE)
cat(sprintf("Saved: %s\n", out_path))

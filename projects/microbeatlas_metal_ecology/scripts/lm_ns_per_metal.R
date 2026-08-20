#!/usr/bin/env Rscript
# lm_ns_per_metal.R — Fit lm(cwm ~ ns(log10_metal,3) + ns(ph,3)) for one metal.
# Called once per metal; input CSV has all KOs for that metal pre-merged.
# Low memory: only one metal's data in RAM (~400K rows instead of 2.79M).
suppressPackageStartupMessages(library(splines))

MIN_N <- 30
NS_DF <- 3

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 3) stop("Usage: Rscript lm_ns_per_metal.R <input_csv> <metal_name> <out_csv>")
in_path <- args[1]; metal <- args[2]; out_path <- args[3]
cat(sprintf("Metal: %s | Input: %s\n", metal, in_path))

d <- read.csv(in_path, stringsAsFactors = FALSE)
cat(sprintf("Rows: %d, KOs: %d, samples: %d\n",
            nrow(d), length(unique(d$ko_id)), length(unique(d$sample_id))))

# Choose pH source: prefer soilgrids, fall back to ssurgo
if ("ph_soilgrids" %in% names(d) && sum(!is.na(d$ph_soilgrids)) > MIN_N) {
  d$ph_use <- d$ph_soilgrids
} else if ("ph_ssurgo" %in% names(d)) {
  d$ph_use <- d$ph_ssurgo
} else {
  d$ph_use <- NA_real_
}

fit_one_ko <- function(df_ko) {
  ko <- df_ko$ko_id[1]
  df <- df_ko[complete.cases(df_ko[, c("cwm", "log10_metal", "ph_use")]), ]
  out <- data.frame(ko_id=ko, metal=metal, n=nrow(df),
                    p_metal=NA_real_, r2_full=NA_real_, r2_null=NA_real_,
                    delta_r2=NA_real_, error_msg=NA_character_,
                    stringsAsFactors=FALSE)
  if (nrow(df) < MIN_N)    { out$error_msg <- sprintf("n=%d<30", nrow(df)); return(out) }
  if (var(df$cwm) < 1e-20) { out$error_msg <- "cwm constant";               return(out) }
  tryCatch({
    use_ph <- !all(is.na(df$ph_use)) && length(unique(na.omit(df$ph_use))) >= 4
    if (use_ph) {
      m_null <- lm(cwm ~ ns(ph_use,     df = NS_DF), data = df)
      m_full <- lm(cwm ~ ns(log10_metal, df = NS_DF) + ns(ph_use, df = NS_DF), data = df)
    } else {
      m_null <- lm(cwm ~ 1, data = df)
      m_full <- lm(cwm ~ ns(log10_metal, df = NS_DF), data = df)
    }
    av <- anova(m_null, m_full, test = "F")
    out$p_metal  <- av$`Pr(>F)`[2]
    out$r2_full  <- summary(m_full)$r.squared
    out$r2_null  <- summary(m_null)$r.squared
    out$delta_r2 <- out$r2_full - out$r2_null
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

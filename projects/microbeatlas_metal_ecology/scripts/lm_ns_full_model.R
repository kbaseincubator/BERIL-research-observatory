#!/usr/bin/env Rscript
# lm_ns_full_model.R — Full model: cwm ~ ns(metal,3) + ns(pH,3) + confounders
# F-test vs null (pH + same confounders). Per-metal input CSV already has all covariates.
# Confounders added to BOTH null and full models; F-test isolates metal contribution.
suppressPackageStartupMessages(library(splines))
suppressPackageStartupMessages(library(parallel))

MIN_N    <- 30
NS_DF    <- 3
THRESH   <- 15   # min non-NA to include a covariate
MC_CORES <- as.integer(Sys.getenv("MC_CORES", unset = "8"))
Sys.setenv(OMP_NUM_THREADS = "1")   # prevent BLAS thread explosion under mclapply

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 3) stop("Usage: Rscript lm_ns_full_model.R <input_csv> <metal> <out_csv> [covariate_csv]")
in_path <- args[1]; metal <- args[2]; out_path <- args[3]
covariate_csv <- if (length(args) >= 4) args[4] else NULL
cat(sprintf("Full model | Metal: %s\n  Input: %s\n  Output: %s\n", metal, in_path, out_path))
if (!is.null(covariate_csv)) cat(sprintf("  Covariate override: %s\n", covariate_csv))

d <- read.csv(in_path, stringsAsFactors = FALSE)
cat(sprintf("Rows: %d, KOs: %d, samples: %d\n",
            nrow(d), length(unique(d$ko_id)), length(unique(d$sample_id))))

# Merge organic TRI releases if available (avoids regenerating large per-metal CSVs)
organic_patch <- file.path(dirname(in_path), "organic_by_sample.csv")
if (file.exists(organic_patch) && !"epa_tri_organic_releases" %in% names(d)) {
  cat(sprintf("Merging organic TRI patch: %s\n", organic_patch))
  org <- read.csv(organic_patch, stringsAsFactors = FALSE)
  d <- merge(d, org, by = "sample_id", all.x = TRUE)
  cat(sprintf("  epa_tri_organic_releases: %d non-NA\n",
              sum(!is.na(d$epa_tri_organic_releases))))
}

# Optional covariate override: adds/replaces per-sample columns from v2 covariate matrix.
# Drops tectonic_boundary_dist; imputes epa_tri_releases=0 for NA; adds climate/soil vars.
if (!is.null(covariate_csv) && file.exists(covariate_csv)) {
  cat(sprintf("Merging covariate override: %s\n", covariate_csv))
  cov_new <- read.csv(covariate_csv, stringsAsFactors = FALSE)
  # Columns to pull from v2 (exclude identifiers and metal concentration cols)
  skip_cols <- c("sample_id", "lat", "lon",
                 "As","Cd","Cr","Cu","Hg","Pb",  # original 6 metals
                 "ph_soilgrids","ph_ssurgo","drainage_class","organic_matter","clay_pct","cec",
                 "lith_class","usgs_mine_distance","lc_forest_pct","lc_cultivated_pct",
                 "lc_urban_pct","lc_barren_pct","shannon",
                 grep("^phylum_", names(cov_new), value=TRUE))
  new_cols <- setdiff(names(cov_new), skip_cols)
  cov_patch <- cov_new[, c("sample_id", new_cols), drop=FALSE]
  # Drop obsolete columns from d before merging
  d <- d[, setdiff(names(d), c("tectonic_boundary_dist", new_cols)), drop=FALSE]
  d <- merge(d, cov_patch, by="sample_id", all.x=TRUE)
  # Impute epa_tri_releases=0 where NA (samples with no nearby TRI facility)
  if ("epa_tri_releases" %in% names(d))
    d$epa_tri_releases[is.na(d$epa_tri_releases)] <- 0
  cat(sprintf("  New columns merged: %s\n", paste(new_cols, collapse=", ")))
  cat(sprintf("  Rows after merge: %d\n", nrow(d)))
}

# ── pH: SSURGO primary, calibrated SoilGrids imputation ───────────────────────
# SSURGO is in-situ measured (preferred); SoilGrids is a global spatial model.
# Where SSURGO is missing (~14% of samples), impute using a calibration regression
# fit on samples with both measurements.
have_ssurgo   <- "ph_ssurgo"   %in% names(d) && sum(!is.na(d$ph_ssurgo))   >= THRESH
have_soilgrids <- "ph_soilgrids" %in% names(d) && sum(!is.na(d$ph_soilgrids)) >= THRESH

if (have_ssurgo && have_soilgrids) {
  both_mask <- !is.na(d$ph_ssurgo) & !is.na(d$ph_soilgrids)
  if (sum(both_mask) >= 20) {
    cal <- lm(ph_ssurgo ~ ph_soilgrids, data = d[both_mask, ])
    cal_r2 <- summary(cal)$r.squared
    cal_slope <- coef(cal)[["ph_soilgrids"]]
    cat(sprintf("pH calibration (SoilGrids→SSURGO): n=%d, R²=%.3f, slope=%.3f, intercept=%.3f\n",
                sum(both_mask), cal_r2, cal_slope, coef(cal)[["(Intercept)"]]))
    ph_sg_cal <- predict(cal, newdata = data.frame(ph_soilgrids = d$ph_soilgrids))
  } else {
    cat("  Too few overlap samples for calibration; using SoilGrids directly\n")
    ph_sg_cal <- d$ph_soilgrids
  }
  d$ph_use <- ifelse(!is.na(d$ph_ssurgo), d$ph_ssurgo,
                     ifelse(!is.na(d$ph_soilgrids), ph_sg_cal, NA_real_))
} else if (have_ssurgo) {
  cat("pH source: SSURGO only\n")
  d$ph_use <- d$ph_ssurgo
} else if (have_soilgrids) {
  cat("pH source: SoilGrids only (SSURGO unavailable)\n")
  d$ph_use <- d$ph_soilgrids
} else {
  d$ph_use <- NA_real_
}
cat(sprintf("ph_use: %d non-NA (%.1f%%)\n", sum(!is.na(d$ph_use)), 100*mean(!is.na(d$ph_use))))

if ("usgs_mine_distance" %in% names(d))
  d$log10_mine <- log10(pmax(d$usgs_mine_distance, 0.1) + 1)
if ("epa_tri_releases" %in% names(d))
  d$log10_epa  <- log10(pmax(d$epa_tri_releases, 0) + 1)
if ("epa_tri_organic_releases" %in% names(d))
  d$log10_epa_organic <- log10(pmax(d$epa_tri_organic_releases, 0) + 1)

# Factors
for (fc in c("drainage_class", "lith_class", "hydrologic_group", "flood_freq")) {
  if (fc %in% names(d)) d[[fc]] <- as.factor(d[[fc]])
}

# ── Select confounders at metal level (fixed for all KOs) ─────────────────────
# Continuous smooth terms (already have ns for metal/pH)
smooth_candidates <- c()  # could add cec as s() if desired — use linear instead
# Linear continuous candidates
linear_candidates <- c("clay_pct", "organic_matter", "cec",
                        "log10_mine", "log10_epa", "log10_epa_organic",
                        "lc_forest_pct", "lc_cultivated_pct", "lc_urban_pct", "lc_barren_pct",
                        "shannon",
                        grep("^phylum_", names(d), value = TRUE),
                        # v2 additions: climate
                        "mat_c", "map_mm", "temp_seasonality", "precip_seasonality",
                        "temp_annual_range_c",
                        # v2 additions: soil texture / structure
                        "sand_0cm", "silt_0cm", "bulk_density_0cm", "nitrogen_0cm",
                        # v2 additions: elevation
                        "elevation_m",
                        # v2 additions: gNATSGO
                        "slope_pct", "awc_0_25cm",
                        "hydric_pct", "ponding_pct", "land_cap_class",
                        # spatial sensitivity: sp_* columns auto-detected
                        grep("^sp_", names(d), value = TRUE))
# Categorical candidates
factor_candidates <- c("drainage_class", "lith_class",
                        # v2 additions: gNATSGO
                        "hydrologic_group", "flood_freq")

available_linear  <- linear_candidates[
  sapply(linear_candidates, function(v) v %in% names(d) && sum(!is.na(d[[v]])) >= THRESH)
]
available_factors <- factor_candidates[
  sapply(factor_candidates, function(v) v %in% names(d) && sum(!is.na(d[[v]])) >= THRESH)
]

# Drop covariates with near-zero variance (constants)
available_linear <- available_linear[sapply(available_linear, function(v) {
  x <- d[[v]][!is.na(d[[v]])]
  length(unique(x)) >= 3
})]

cat(sprintf("Confounders selected: %s\n",
    paste(c(available_linear, available_factors), collapse = ", ")))

# ── Formulas (fixed) ──────────────────────────────────────────────────────────
conf_terms <- c(available_linear, available_factors)
use_ph <- sum(!is.na(d$ph_use)) >= THRESH && length(unique(na.omit(d$ph_use))) >= 4

# All variables needed for complete-case selection per KO
# ph_use excluded when use_ph=FALSE: all-NA pH included in complete.cases drops all rows
all_vars <- c("cwm", "log10_metal", if (use_ph) "ph_use", available_linear, available_factors)

null_terms <- if (use_ph) c(sprintf("ns(ph_use, df=%d)", NS_DF), conf_terms) else conf_terms
full_terms  <- c(sprintf("ns(log10_metal, df=%d)", NS_DF), null_terms)

# Intercept-only null if no terms at all
if (length(null_terms) == 0) null_terms <- "1"

f_null <- as.formula(paste("cwm ~", paste(null_terms, collapse = " + ")))
f_full <- as.formula(paste("cwm ~", paste(full_terms, collapse = " + ")))
cat(sprintf("Null:  %s\nFull:  %s\n",
    paste(deparse(f_null), collapse = " "),
    paste(deparse(f_full), collapse = " ")))

# ── Per-KO fitting ─────────────────────────────────────────────────────────────
fit_one_ko <- function(df_ko) {
  ko <- df_ko$ko_id[1]
  # Complete cases on all required variables
  avail_vars <- intersect(all_vars, names(df_ko))
  df <- df_ko[complete.cases(df_ko[, avail_vars, drop = FALSE]), ]

  out <- data.frame(ko_id=ko, metal=metal, n=nrow(df), n_conf=length(conf_terms),
                    p_metal_full=NA_real_, p_metal_base=NA_real_,
                    r2_full=NA_real_, r2_base=NA_real_,
                    delta_r2_full=NA_real_, delta_r2_base=NA_real_,
                    delta_cwm_iqr=NA_real_, beta_sign=NA_integer_,
                    error_msg=NA_character_, stringsAsFactors=FALSE)
  if (nrow(df) < MIN_N)    { out$error_msg <- sprintf("n=%d<30", nrow(df)); return(out) }
  if (var(df$cwm) < 1e-20) { out$error_msg <- "cwm constant";               return(out) }

  # Check factor levels — need ≥2 levels to include as predictor
  ok_factors <- sapply(available_factors, function(v) {
    v %in% names(df) && length(unique(na.omit(df[[v]]))) >= 2
  })
  # Drop factors with <2 levels from this KO's subset
  drop_f <- available_factors[!ok_factors]
  if (length(drop_f) > 0) {
    f_null_ko <- update(f_null, as.formula(
      paste(". ~ . -", paste(drop_f, collapse = " - "))))
    f_full_ko <- update(f_full, as.formula(
      paste(". ~ . -", paste(drop_f, collapse = " - "))))
  } else {
    f_null_ko <- f_null
    f_full_ko <- f_full
  }

  tryCatch({
    m_null <- lm(f_null_ko, data = df)
    m_full <- lm(f_full_ko, data = df)
    av_full <- anova(m_null, m_full, test = "F")
    out$p_metal_full  <- av_full$`Pr(>F)`[2]
    out$r2_full       <- summary(m_full)$r.squared
    out$r2_base       <- summary(m_null)$r.squared
    out$delta_r2_full <- out$r2_full - out$r2_base

    # Also run base model (pH only) for attenuation comparison
    f_ph_null <- if (use_ph) as.formula(sprintf("cwm ~ ns(ph_use, df=%d)", NS_DF)) else as.formula("cwm ~ 1")
    f_ph_full <- if (use_ph) as.formula(sprintf("cwm ~ ns(log10_metal, df=%d) + ns(ph_use, df=%d)", NS_DF, NS_DF)) else as.formula(sprintf("cwm ~ ns(log10_metal, df=%d)", NS_DF))
    m_ph_null <- lm(f_ph_null, data = df)
    m_ph_full <- lm(f_ph_full, data = df)
    av_base <- anova(m_ph_null, m_ph_full, test = "F")
    out$p_metal_base  <- av_base$`Pr(>F)`[2]
    out$delta_r2_base <- summary(m_ph_full)$r.squared - summary(m_ph_null)$r.squared

    # Sign of association: CWM at Q75 vs Q25 of log10_metal (confounders held at first
    # complete-case row). Gives direction: +1 = more metal → higher CWM; -1 = inverse.
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

    # Per-covariate partial R² via Type II SS (drop1, base R only)
    # partial_r2_X = SS_X / (SS_X + SS_residual); SS_X = RSS_reduced - RSS_full
    tryCatch({
      d1 <- drop1(m_full)
      rss_full <- deviance(m_full)
      clean_term <- function(nm) {
        nm <- gsub("ns\\(log10_metal[^)]*\\)", "metal", nm)
        nm <- gsub("ns\\(ph_use[^)]*\\)",      "ph_use", nm)
        nm <- gsub("[^a-zA-Z0-9_]", "_", nm)
        nm <- gsub("_{2,}", "_", nm)
        nm <- sub("_$", "", tolower(nm))
        paste0("pr2_", nm)
      }
      for (nm in rownames(d1)[rownames(d1) != "<none>"]) {
        ss_t <- d1[nm, "RSS"] - rss_full
        out[[clean_term(nm)]] <- if (is.na(ss_t) || ss_t <= 0) 0 else ss_t / (ss_t + rss_full)
      }
    }, error = function(e3) {
      out$error_drop1 <<- conditionMessage(e3)
    })
  }, error = function(e) {
    out$error_msg <<- conditionMessage(e)
  })
  out
}

t0 <- proc.time()
ko_list <- split(d, d$ko_id)
rm(d); gc()
cat(sprintf("KO groups: %d  mc.cores: %d\n", length(ko_list), MC_CORES))

results <- mclapply(ko_list, fit_one_ko, mc.cores = MC_CORES)
# mclapply returns try-error for crashed workers — drop and warn
bad <- sapply(results, inherits, "try-error")
if (any(bad)) cat(sprintf("WARNING: %d workers crashed (try-error), dropping\n", sum(bad)))
results <- results[!bad]
elapsed <- (proc.time() - t0)[["elapsed"]]
cat(sprintf("Loop: %.1f sec\n", elapsed))

# Flexible rbind: some rows may have extra pr2_* or error_drop1 columns
all_cols <- unique(unlist(lapply(results, names)))
out_df <- do.call(rbind, lapply(results, function(x) {
  for (mc in setdiff(all_cols, names(x))) x[[mc]] <- NA
  x[, all_cols, drop = FALSE]
}))
cat(sprintf("Rows: %d\n", nrow(out_df)))
write.csv(out_df, out_path, row.names = FALSE)
cat(sprintf("Saved: %s\n", out_path))

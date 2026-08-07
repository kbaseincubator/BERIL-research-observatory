#!/usr/bin/env Rscript
# NB GLM with genome-size offset — see nb_glm_genome_size_offset.py for rationale
library(MASS)

DATA <- "data"
pgls <- read.csv(file.path(DATA, "01_pgls_input_bacteria.csv"))
dens <- read.csv(file.path(DATA, "01_genus_ko_density_spark.csv"))

df <- merge(pgls[, c("genus_lower","mean_levins_B_std","mean_genome_mb","predictor_z")],
            dens[, c("genus_lower","n_ko_primary")],
            by = "genus_lower")
cat("n genera:", nrow(df), "\n")

# Predictor: z-scored niche breadth (Levins B_std)
# NOTE: predictor_z in the PGLS file is z-scored ko_per_mb (the PGLS predictor),
# NOT z-scored niche breadth. We need to z-score levins_B_std for the NB GLM.
B_z      <- scale(df$mean_levins_B_std)[,1]
y        <- as.integer(df$n_ko_primary)
genome   <- df$mean_genome_mb
log_g    <- log(genome)
genome_z <- scale(genome)[,1]
ko_rate  <- df$n_ko_primary / genome

# ── M0: NB, no genome correction ─────────────────────────────────────────────
m0 <- glm.nb(y ~ B_z)
s0 <- summary(m0)

# ── M1: NB + offset(log genome) — key model ──────────────────────────────────
m1 <- glm.nb(y ~ B_z + offset(log_g))
s1 <- summary(m1)

# ── M2: NB + offset + genome_z as covariate (double control) ─────────────────
m2 <- glm.nb(y ~ B_z + genome_z + offset(log_g))
s2 <- summary(m2)

# ── M3: OLS ko_rate ~ B_z (reference; no phylogeny) ─────────────────────────
m3 <- lm(ko_rate ~ B_z)
s3 <- summary(m3)

# ── Print results ─────────────────────────────────────────────────────────────
get_row <- function(s, name, model_type="nb") {
  if (model_type == "nb") {
    cf <- coef(s)
    b  <- cf["B_z", "Estimate"]
    se <- cf["B_z", "Std. Error"]
    z  <- cf["B_z", "z value"]
    p  <- cf["B_z", "Pr(>|z|)"]
    th <- s$theta
  } else {
    cf <- coef(s)
    b  <- cf["B_z", "Estimate"]
    se <- cf["B_z", "Std. Error"]
    z  <- cf["B_z", "t value"]
    p  <- cf["B_z", "Pr(>|t|)"]
    th <- NA
  }
  list(model=name, beta=b, se=se, z=z, p=p, theta=th)
}

rows <- list(
  get_row(s0, "M0: NB (no genome)"),
  get_row(s1, "M1: NB + offset(log_genome)"),
  get_row(s2, "M2: NB + offset + genome_cov"),
  get_row(s3, "M3: OLS ko_per_mb", model_type="ols")
)

cat("\n── Model comparison ──────────────────────────────────────────────\n")
cat(sprintf("%-35s %8s %7s %12s %10s\n", "Model", "beta_B", "SE", "p", "theta_NB"))
cat(paste(rep("-",76), collapse=""), "\n")
for (r in rows) {
  sig <- ifelse(r$p < 0.001, "***", ifelse(r$p < 0.01, "**", ifelse(r$p < 0.05, "*", "ns")))
  th_str <- if (is.na(r$theta)) "     OLS" else sprintf("%8.2f", r$theta)
  cat(sprintf("%-35s %+8.4f %7.4f %12.4e %s  %s\n",
              r$model, r$beta, r$se, r$p, sig, th_str))
}

cat("\nFor comparison: PGLS beta = -0.021, p = 2.1e-8 (phylogenetically corrected)\n")

# M1 interpretation
b1 <- coef(s1)["B_z","Estimate"]
mean_rate <- mean(ko_rate)
rr <- exp(b1)
delta_pct <- (rr - 1) * 100
cat(sprintf("\nM1: exp(beta=%.4f) = %.4f\n", b1, rr))
cat(sprintf("  -> %.1f%% change in KO rate per SD of niche breadth\n", delta_pct))
cat(sprintf("  -> at mean rate %.2f KO/Mb: delta ~%.3f KO/Mb per SD B_std\n",
            mean_rate, mean_rate * (rr - 1)))

# AIC comparison
cat("\nAIC:\n")
cat(sprintf("  M0: %.1f\n  M1: %.1f\n  M2: %.1f\n  M3: %.1f (OLS)\n",
            AIC(m0), AIC(m1), AIC(m2), AIC(m3)))

# ── Save CSV ──────────────────────────────────────────────────────────────────
out <- data.frame(
  model  = sapply(rows, `[[`, "model"),
  beta_B = sapply(rows, `[[`, "beta"),
  se_B   = sapply(rows, `[[`, "se"),
  z_B    = sapply(rows, `[[`, "z"),
  p_B    = sapply(rows, `[[`, "p"),
  theta  = sapply(rows, function(r) ifelse(is.null(r$theta), NA, r$theta))
)
write.csv(out, file.path(DATA, "nb_glm_results.csv"), row.names=FALSE)
cat("\nSaved -> data/nb_glm_results.csv\n")

# ── Export per-genus predictions for Python figure ────────────────────────────
pred_df <- data.frame(
  genus_lower       = df$genus_lower,
  levins_B_std      = df$mean_levins_B_std,
  B_z               = as.numeric(B_z),
  n_ko_primary      = y,
  mean_genome_mb    = genome,
  ko_rate_obs       = ko_rate,
  ko_rate_pred_m1   = fitted(m1) / genome,   # predicted rate from M1
  ko_rate_pred_m0   = fitted(m0) / genome    # predicted rate from M0 (uncorrected)
)
write.csv(pred_df, file.path(DATA, "nb_glm_predictions.csv"), row.names=FALSE)
cat("Saved -> data/nb_glm_predictions.csv\n")

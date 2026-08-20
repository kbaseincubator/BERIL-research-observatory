#!/usr/bin/env Rscript
# Random-effects meta-regression of Pagel's lambda across KEGG functional subcategories
# Reference: Hadfield & Nakagawa 2010 J Evol Biol 23:494-508
#
# Model: lambda_i ~ subcategory (fixed moderator) + u_i (random study effect)
# Sampling variance: vi = 1 / (n_genera - 3)  [approximation treating lambda like
#   a partial correlation; exact sampling variance requires bootstrap from caper::pgls]
# Method: REML (restricted maximum likelihood)
#
# Excludes subcategory == "Unknown" (uninformative moderator level; 121 KOs)

suppressMessages(library(metafor))

DATA  <- "projects/comprehensive_metal_ecology/data"
FIGS  <- "projects/comprehensive_metal_ecology/figures"

# ── Load data ──────────────────────────────────────────────────────────────────
df <- read.csv(file.path(DATA, "phylo_d_all_ko.csv"), stringsAsFactors = FALSE)
cat(sprintf("Loaded %d metal KOs\n", nrow(df)))
cat(sprintf("Subcategory distribution:\n"))
print(table(df$subcategory))

# ── Exclude Unknown subcategory ────────────────────────────────────────────────
df_known <- df[df$subcategory != "Unknown", ]
cat(sprintf("\nAfter excluding Unknown: %d KOs\n", nrow(df_known)))

# ── Sampling variance approximation ───────────────────────────────────────────
# vi = 1 / (n - 3): analogous to Fisher-Z sampling variance for correlations.
# Lambda ~ Pearson r^2 of trait evolution, so this is conservative (slightly
# inflated vi for most KOs).
df_known$vi <- 1 / pmax(df_known$n_genera - 3, 1)

# ── Relevel: Cofactor Biosynthesis as reference (biological anchor) ──────────
df_known$subcategory <- factor(
  df_known$subcategory,
  levels = c("Cofactor Biosynthesis", "Metal-dependent Metabolism",
             "Resistance/Detoxification", "Sensing/Regulation",
             "Transport/Homeostasis")
)

# ── Model 1: Intercept-only random effects (overall mean lambda) ──────────────
cat("\n=== Model 1: Overall mean lambda (intercept-only) ===\n")
m0 <- rma(yi = lambda, vi = vi, data = df_known, method = "REML")
print(m0)

# ── Model 2: Subcategory as moderator ─────────────────────────────────────────
cat("\n=== Model 2: Subcategory moderator ===\n")
m1 <- rma(yi = lambda, vi = vi, mods = ~ subcategory, data = df_known, method = "REML")
print(m1)

# ── Likelihood ratio test: does subcategory improve fit? ──────────────────────
cat("\n=== LRT: M1 vs M0 ===\n")
lrt <- anova(m1, m0)
print(lrt)

# ── Per-subcategory predicted means with 95% CI ───────────────────────────────
cat("\n=== Per-subcategory predicted lambda (from M2) ===\n")
cats   <- levels(df_known$subcategory)
X_pred <- model.matrix(~ subcategory,
                        data = data.frame(subcategory = factor(cats, levels = cats)))
preds  <- predict(m1, newmods = X_pred[, -1, drop = FALSE])  # drop intercept col
pred_df <- data.frame(
  subcategory = cats,
  pred_lambda = round(preds$pred, 4),
  ci_lo       = round(preds$ci.lb, 4),
  ci_hi       = round(preds$ci.ub, 4),
  n_ko        = as.integer(table(df_known$subcategory))
)
print(pred_df)

# ── Save results ───────────────────────────────────────────────────────────────
out <- data.frame(
  model          = c("intercept_only", "subcategory_moderator"),
  QM             = c(NA, round(m1$QM, 3)),
  QM_df          = c(NA, m1$p - 1L),
  QMp            = c(NA, round(m1$QMp, 4)),
  tau2           = c(round(m0$tau2, 4), round(m1$tau2, 4)),
  I2             = c(round(m0$I2, 1), round(m1$I2, 1)),
  R2             = c(NA, round(m1$R2, 3)),
  LRT_Q          = c(NA, round(lrt$LRT, 3)),
  LRT_df         = c(NA, lrt$p.diff),
  LRT_p          = c(NA, round(lrt$pval, 4)),
  n_KO           = c(nrow(df_known), nrow(df_known)),
  n_KO_unknown   = c(sum(df$subcategory == "Unknown"), sum(df$subcategory == "Unknown"))
)
write.csv(out, file.path(DATA, "subcategory_meta_analysis.csv"), row.names = FALSE)

write.csv(pred_df, file.path(DATA, "subcategory_predicted_lambda.csv"), row.names = FALSE)

cat(sprintf("\nSaved -> %s/subcategory_meta_analysis.csv\n", DATA))
cat(sprintf("Saved -> %s/subcategory_predicted_lambda.csv\n", DATA))

# ── Summary for REPORT ────────────────────────────────────────────────────────
cat("\n=== REPORT SUMMARY ===\n")
cat(sprintf("Overall mean lambda (intercept-only): %.3f [%.3f, %.3f]\n",
            m0$beta[1], m0$ci.lb, m0$ci.ub))
cat(sprintf("tau2 = %.4f, I2 = %.1f%%\n", m0$tau2, m0$I2))
cat(sprintf("\nSubcategory moderator test: QM(%d) = %.2f, p = %.4f\n",
            m1$p - 1L, m1$QM, m1$QMp))
cat(sprintf("R2 (variance explained by subcategory): %.1f%%\n", m1$R2))
cat(sprintf("\nOriginal KW test: H=8.71, p=0.1212 (unweighted, ignored sampling variances)\n"))

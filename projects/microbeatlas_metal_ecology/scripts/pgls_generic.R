#!/usr/bin/env Rscript
# pgls_generic.R — Generic PGLS runner for sensitivity analyses
#
# Usage:
#   Rscript scripts/pgls_generic.R \
#       --input  data/sensitivity_emp_pgls_input.csv \
#       --tree   data/gtdb_bac_genus_pruned.tree \
#       --response mean_levins_B_std \
#       --predictor metal_per_Mb_z \
#       --output data/sensitivity_emp_niche_pgls.csv \
#       --label "EMP niche breadth sensitivity"
#
# Input CSV must have columns: genus_lower, <response>, <predictor>
# Predictor should be pre-z-scored (or will be z-scored here if not).

suppressPackageStartupMessages({ library(ape); library(nlme) })

# ── Parse args ────────────────────────────────────────────────────────────────
args <- commandArgs(trailingOnly = TRUE)
get_arg <- function(flag, default = NULL) {
    i <- which(args == flag)
    if (length(i) == 0) return(default)
    if (i >= length(args)) stop(paste("Flag", flag, "missing value"))
    args[i + 1]
}

input_file  <- get_arg("--input")
tree_file   <- get_arg("--tree",   "data/gtdb_bac_genus_pruned.tree")
response    <- get_arg("--response",  "mean_levins_B_std")
predictor   <- get_arg("--predictor")
covariate   <- get_arg("--covariate")   # optional; z-scored covariate to control for
output_file <- get_arg("--output")
label       <- get_arg("--label", "sensitivity")

if (is.null(input_file))  stop("--input is required")
if (is.null(predictor))   stop("--predictor is required")
if (is.null(output_file)) stop("--output is required")

cat(sprintf("\n=== PGLS Generic: %s ===\n", label))
cat(sprintf("Input:      %s\n", input_file))
cat(sprintf("Tree:       %s\n", tree_file))
cat(sprintf("Response:   %s\n", response))
cat(sprintf("Predictor:  %s\n", predictor))
if (!is.null(covariate)) cat(sprintf("Covariate:  %s\n", covariate))
cat(sprintf("Output:     %s\n", output_file))

# ── Load data ─────────────────────────────────────────────────────────────────
tree <- read.tree(tree_file)
df   <- read.csv(input_file, stringsAsFactors = FALSE)
cat(sprintf("\nInput rows: %d | Tree tips: %d\n", nrow(df), length(tree$tip.label)))

if (!response  %in% names(df)) stop(paste("Response column not found:", response))
if (!predictor %in% names(df)) stop(paste("Predictor column not found:", predictor))
if (!"genus_lower" %in% names(df)) stop("genus_lower column required")
if (!is.null(covariate) && !covariate %in% names(df))
    stop(paste("Covariate column not found:", covariate))

# ── Filter to tree overlap ────────────────────────────────────────────────────
keep <- df$genus_lower %in% tree$tip.label &
        !is.na(df[[response]]) &
        !is.na(df[[predictor]])
if (!is.null(covariate)) keep <- keep & !is.na(df[[covariate]])
sub <- df[keep, ]
cat(sprintf("After tree overlap + NA filter: %d genera\n", nrow(sub)))
if (nrow(sub) < 30) stop("Fewer than 30 genera after filtering — check taxonomy matching.")

# ── Z-score predictor (and covariate) if needed ───────────────────────────────
pred_vals <- sub[[predictor]]
if (abs(sd(pred_vals, na.rm = TRUE) - 1) > 0.05 || abs(mean(pred_vals, na.rm = TRUE)) > 0.05) {
    cat("Z-scoring predictor...\n")
    sub[[predictor]] <- as.numeric(scale(pred_vals))
}
if (!is.null(covariate)) {
    cov_vals <- sub[[covariate]]
    if (abs(sd(cov_vals, na.rm = TRUE) - 1) > 0.05 || abs(mean(cov_vals, na.rm = TRUE)) > 0.05) {
        cat("Z-scoring covariate...\n")
        sub[[covariate]] <- as.numeric(scale(cov_vals))
    }
}

# ── Prune tree ────────────────────────────────────────────────────────────────
tree_pruned <- drop.tip(tree, tree$tip.label[!tree$tip.label %in% sub$genus_lower])
sub <- sub[sub$genus_lower %in% tree_pruned$tip.label, ]
sub <- sub[match(tree_pruned$tip.label, sub$genus_lower), ]
rownames(sub) <- sub$genus_lower
cat(sprintf("After tree pruning: %d genera\n", nrow(sub)))

# ── Fit models ────────────────────────────────────────────────────────────────
fit_pgls <- function(dat, tree, resp_col, pred_col, cov_col = NULL) {
    rhs_full  <- if (is.null(cov_col)) pred_col else paste(pred_col, "+", cov_col)
    rhs_null  <- if (is.null(cov_col)) "1" else cov_col
    form_full <- as.formula(paste(resp_col, "~", rhs_full))
    form_null <- as.formula(paste(resp_col, "~", rhs_null))
    cor_struct <- corPagel(1, phy = tree, fixed = FALSE)
    fit_full  <- gls(form_full, data = dat, correlation = cor_struct, method = "ML")
    fit_null  <- gls(form_null, data = dat, correlation = cor_struct, method = "ML")
    coef_row  <- summary(fit_full)$tTable[pred_col, ]
    list(
        n      = nrow(dat),
        lambda = coef(fit_full$modelStruct$corStruct, unconstrained = FALSE),
        beta   = coef_row[["Value"]],
        SE     = coef_row[["Std.Error"]],
        t_stat = coef_row[["t-value"]],
        p_val  = coef_row[["p-value"]],
        AIC_full = AIC(fit_full),
        AIC_null = AIC(fit_null),
        delta_AIC = AIC(fit_full) - AIC(fit_null)
    )
}

cat("Fitting PGLS...\n")
result <- tryCatch(
    fit_pgls(sub, tree_pruned, response, predictor, covariate),
    error = function(e) { cat("PGLS error:", conditionMessage(e), "\n"); NULL }
)

if (is.null(result)) stop("PGLS fitting failed.")

out <- data.frame(
    label     = label,
    response  = response,
    predictor = predictor,
    n         = result$n,
    lambda    = result$lambda,
    beta      = result$beta,
    SE        = result$SE,
    t_stat    = result$t_stat,
    p_value   = result$p_val,
    AIC_full  = result$AIC_full,
    AIC_null  = result$AIC_null,
    delta_AIC = result$delta_AIC,
    stringsAsFactors = FALSE
)

write.csv(out, output_file, row.names = FALSE)

cat(sprintf("\n=== RESULT ===\n"))
cat(sprintf("n=%d  λ=%.3f  β=%+.4f  SE=%.4f  t=%+.3f  p=%.4g  ΔAIC=%.1f\n",
    result$n, result$lambda, result$beta, result$SE,
    result$t_stat, result$p_val, result$delta_AIC))
cat(sprintf("Saved: %s\n\n", output_file))
